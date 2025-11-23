"""Google GenAI SDK wrapper providing consistent request/response handling."""
from __future__ import annotations

import base64
import binascii
import os
import threading
from dataclasses import dataclass
from typing import Any, Iterable, List, Sequence

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

__all__ = [
    "GenAIClientError",
    "GenAIResponse",
    "GenAIPromptBlocked",
    "generate_content",
]

_DEFAULT_MODEL = os.getenv("GEMINI_MODEL_NAME", os.getenv("GOOGLE_GENAI_MODEL", "gemini-flash-latest"))
_DEFAULT_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "16384"))

_DEFAULT_GENERATION_CONFIG = {
    "temperature": 0.4,
    "top_k": 1,
    "top_p": 0.95,
    "max_output_tokens": _DEFAULT_MAX_OUTPUT_TOKENS,
}

_DEFAULT_SAFETY_SETTINGS: list[genai_types.SafetySetting] = [
    genai_types.SafetySetting(
        category=genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
    ),
    genai_types.SafetySetting(
        category=genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
    ),
    genai_types.SafetySetting(
        category=genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
    ),
    genai_types.SafetySetting(
        category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
    ),
]

_GENERATION_KEY_ALIASES = {
    "topK": "top_k",
    "top_p": "top_p",
    "topP": "top_p",
    "maxOutputTokens": "max_output_tokens",
    "max_output_tokens": "max_output_tokens",
    "candidateCount": "candidate_count",
    "responseMimeType": "response_mime_type",
}


@dataclass(frozen=True)
class GenAIResponse:
    """Normalised response payload returned by :func:`generate_content`."""

    text: str
    finish_reason: str | None
    raw_response: genai_types.GenerateContentResponse
    candidate: genai_types.Candidate


class GenAIClientError(RuntimeError):
    """Raised when the GenAI client fails to process a request."""


class GenAIPromptBlocked(GenAIClientError):
    """Raised when the model blocks a prompt for safety reasons."""

    def __init__(self, block_reason: str, safety_ratings: Sequence[genai_types.SafetyRating] | None):
        super().__init__(f"Prompt blocked: {block_reason}")
        self.block_reason = block_reason
        self.safety_ratings = list(safety_ratings or [])


_CLIENT_CACHE: dict[tuple[str, ...], genai.Client] = {}
_CLIENT_LOCK = threading.Lock()


def _coerce_enum(enum_cls, value: Any):
    if value is None:
        return None
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        normalised = value.strip()
        if not normalised:
            return None
        for candidate in enum_cls:
            if normalised.upper() == candidate.name:
                return candidate
            if normalised.upper() == candidate.value.upper():
                return candidate
        raise GenAIClientError(f"Unknown {enum_cls.__name__} value: {value}")
    raise GenAIClientError(f"Unsupported {enum_cls.__name__} value type: {type(value)!r}")


def _build_generation_config(override: Any | None) -> genai_types.GenerateContentConfig | None:
    if override is None:
        return genai_types.GenerateContentConfig(**_DEFAULT_GENERATION_CONFIG)

    if isinstance(override, genai_types.GenerateContentConfig):
        return override

    if not isinstance(override, dict):
        raise GenAIClientError("generation_config_override must be a dict or GenerateContentConfig instance")

    config_data = dict(_DEFAULT_GENERATION_CONFIG)
    for key, value in override.items():
        canonical_key = _GENERATION_KEY_ALIASES.get(key, key)
        config_data[canonical_key] = value

    return genai_types.GenerateContentConfig(**config_data)


def _build_safety_settings(settings: Sequence[Any] | None) -> list[genai_types.SafetySetting]:
    if settings is None:
        return list(_DEFAULT_SAFETY_SETTINGS)

    materialised: list[genai_types.SafetySetting] = []
    for item in settings:
        if isinstance(item, genai_types.SafetySetting):
            materialised.append(item)
            continue
        if not isinstance(item, dict):
            raise GenAIClientError("safety_settings_override must contain dict or SafetySetting entries")

        category = _coerce_enum(genai_types.HarmCategory, item.get("category"))
        threshold = _coerce_enum(genai_types.HarmBlockThreshold, item.get("threshold"))
        method = item.get("method")
        if method is not None:
            method = _coerce_enum(genai_types.HarmBlockMethod, method)
        materialised.append(
            genai_types.SafetySetting(category=category, threshold=threshold, method=method)
        )
    return materialised


def _decode_inline_data(part: dict[str, Any]) -> genai_types.Part:
    inline_data = part.get("inline_data")
    if not isinstance(inline_data, dict):
        raise GenAIClientError("inline_data part must be a dict with base64-encoded 'data'")
    raw_data = inline_data.get("data")
    if not raw_data:
        raise GenAIClientError("inline_data part missing 'data'")
    try:
        decoded = base64.b64decode(raw_data)
    except (binascii.Error, ValueError) as exc:  # pragma: no cover - defensive guard
        raise GenAIClientError("inline_data contains invalid base64") from exc
    mime_type = inline_data.get("mime_type") or "application/octet-stream"
    return genai_types.Part.from_bytes(data=decoded, mime_type=mime_type)


def _decode_file_data(part: dict[str, Any]) -> genai_types.Part:
    file_data = part.get("file_data")
    if not isinstance(file_data, dict):
        raise GenAIClientError("file_data part must be a dict with a 'file_uri'")
    file_uri = file_data.get("file_uri") or file_data.get("uri")
    if not file_uri:
        raise GenAIClientError("file_data part missing 'file_uri'")
    mime_type = file_data.get("mime_type")
    return genai_types.Part.from_uri(file_uri, mime_type=mime_type)


def _normalise_part(part: Any) -> genai_types.Part:
    if isinstance(part, genai_types.Part):
        return part
    if isinstance(part, str):
        return genai_types.Part(text=part)
    if isinstance(part, dict):
        if "text" in part:
            return genai_types.Part(text=str(part["text"]))
        if "inline_data" in part:
            return _decode_inline_data(part)
        if "file_data" in part:
            return _decode_file_data(part)
        if "function_call" in part:
            func_call = part["function_call"]
            return genai_types.Part.from_function_call(
                name=func_call.get("name", ""),
                args=func_call.get("args", {}),
            )
        if "function_response" in part:
            func_resp = part["function_response"]
            return genai_types.Part.from_function_response(
                name=func_resp.get("name", ""),
                response=func_resp.get("response", {}),
            )
    raise GenAIClientError("Unsupported content part format")


def _normalise_content(message: Any) -> genai_types.Content:
    if isinstance(message, genai_types.Content):
        return message
    if isinstance(message, str):
        return genai_types.Content(role="user", parts=[genai_types.Part(text=message)])
    if isinstance(message, dict):
        role = message.get("role") or "user"
        parts = message.get("parts")
        if not isinstance(parts, Iterable):
            raise GenAIClientError("content dictionary must include a 'parts' iterable")
        normalised_parts = [
            _normalise_part(part)
            for part in parts
        ]
        return genai_types.Content(role=role, parts=normalised_parts)
    raise GenAIClientError("Unsupported message format for contents")


def _normalise_contents(prompt: Any) -> list[genai_types.Content]:
    if isinstance(prompt, genai_types.Content):
        return [prompt]
    if isinstance(prompt, str):
        return [_normalise_content(prompt)]
    if isinstance(prompt, Sequence):
        contents: list[genai_types.Content] = []
        for item in prompt:
            contents.append(_normalise_content(item))
        return contents
    raise GenAIClientError("Prompt must be a string, Content, or sequence of content dictionaries")


def _is_vertex_mode() -> bool:
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() in {"1", "true", "yes"}


def _get_client(api_key: str | None) -> genai.Client:
    use_vertex = _is_vertex_mode()
    if use_vertex:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")
        if not project or not location:
            raise GenAIClientError("Vertex AI mode requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION")
        cache_key = ("vertex", project, location)
        with _CLIENT_LOCK:
            client = _CLIENT_CACHE.get(cache_key)
            if client is None:
                client = genai.Client(vertexai=True, project=project, location=location)
                _CLIENT_CACHE[cache_key] = client
            return client

    resolved_key = (api_key or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not resolved_key or resolved_key in {"your-gemini-api-key", "your-gemini-api-key-here"}:
        raise GenAIClientError("GOOGLE_API_KEY is not configured. Provide a valid key via header or environment.")
    cache_key = ("api_key", resolved_key)
    with _CLIENT_LOCK:
        client = _CLIENT_CACHE.get(cache_key)
        if client is None:
            client = genai.Client(api_key=resolved_key)
            _CLIENT_CACHE[cache_key] = client
        return client


def _stringify_finish_reason(finish_reason: Any) -> str | None:
    if finish_reason is None:
        return None
    if isinstance(finish_reason, str):
        return finish_reason
    if hasattr(finish_reason, "name"):
        return finish_reason.name
    return str(finish_reason)


def _extract_text(candidate: genai_types.Candidate) -> str:
    content = candidate.content
    if not content or not content.parts:
        return ""
    fragments: List[str] = []
    for part in content.parts:
        text = getattr(part, "text", None)
        if text:
            fragments.append(text)
    return "".join(fragments)


def _pick_candidate(candidates: Sequence[genai_types.Candidate] | None) -> genai_types.Candidate | None:
    if not candidates:
        return None
    return candidates[0]


def _format_api_error(exc: genai_errors.APIError) -> str:
    code = getattr(exc, "code", None)
    message = str(exc)
    return f"GenAI API error (code {code}): {message}" if code is not None else f"GenAI API error: {message}"


def generate_content(
    prompt: Any,
    *,
    api_key: str | None = None,
    generation_config_override: Any | None = None,
    safety_settings_override: Sequence[Any] | None = None,
    model: str | None = None,
) -> GenAIResponse:
    """Invoke the Google GenAI SDK with consistent defaults and error handling."""

    contents = _normalise_contents(prompt)
    generation_config = _build_generation_config(generation_config_override)
    safety_settings = _build_safety_settings(safety_settings_override)
    client = _get_client(api_key)

    if generation_config is None:
        generation_config = genai_types.GenerateContentConfig(**_DEFAULT_GENERATION_CONFIG)

    generation_config.safety_settings = safety_settings

    try:
        response = client.models.generate_content(
            model=model or _DEFAULT_MODEL,
            contents=contents,
            config=generation_config,
        )
    except genai_errors.APIError as exc:
        raise GenAIClientError(_format_api_error(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise GenAIClientError(f"Unexpected error invoking GenAI: {exc}") from exc

    feedback = response.prompt_feedback
    if feedback and feedback.block_reason:
        raise GenAIPromptBlocked(str(feedback.block_reason), feedback.safety_ratings)

    candidate = _pick_candidate(response.candidates)
    if candidate is None:
        raise GenAIClientError("GenAI response did not contain any candidates.")

    text = getattr(response, "text", None) or _extract_text(candidate)
    finish_reason = _stringify_finish_reason(candidate.finish_reason)
    return GenAIResponse(text=text or "", finish_reason=finish_reason, raw_response=response, candidate=candidate)
