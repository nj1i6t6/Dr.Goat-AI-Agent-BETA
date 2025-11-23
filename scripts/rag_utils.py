"""Shared helpers for preparing Retrieval-Augmented Generation inputs."""
from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_OCR_DPI = 300


def iter_source_files(source_dir: Path) -> List[Path]:
    """Return all supported files under the given directory, sorted by path."""
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    files = [
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def read_text(file_path: Path) -> str:
    """Read a supported text document as UTF-8 or extract text from PDF."""
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported extension: {file_path.suffix}."
            " Supported: .md, .txt, .pdf"
        )

    if suffix == ".pdf":
        return _extract_pdf_text(file_path)

    return file_path.read_text(encoding="utf-8")


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Split text into overlapping windows of roughly ``chunk_size`` characters."""
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    length = len(text)
    step = max(chunk_size - overlap, 1)

    while start < length:
        end = min(length, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def _extract_pdf_text(file_path: Path) -> str:
    """Extract textual content from a PDF file using text layer or OCR fallback."""
    try:
        PdfReader = importlib.import_module("pypdf").PdfReader  # type: ignore[attr-defined]
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency missing
        raise RuntimeError(
            "PDF support requires the 'pypdf' package. "
            "Please install backend dependencies (pip install -r backend/requirements.txt)."
        ) from exc

    text_segments: List[str] = []
    try:
        reader = PdfReader(str(file_path))
        for page_index, page in enumerate(reader.pages):
            try:
                page_text = (page.extract_text() or "").strip()
            except Exception as page_exc:  # pragma: no cover - defensive
                LOGGER.warning("Failed to extract text from %s page %s: %s", file_path, page_index + 1, page_exc)
                page_text = ""
            if page_text:
                text_segments.append(page_text)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Unable to read PDF %s via pypdf: %s", file_path, exc)

    combined_text = "\n\n".join(text_segments).strip()
    if combined_text:
        return combined_text

    LOGGER.info("PDF %s appears to lack an extractable text layer; falling back to OCR", file_path)

    try:
        convert_from_path = importlib.import_module("pdf2image").convert_from_path  # type: ignore[attr-defined]
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency missing
        raise RuntimeError(
            "OCR fallback requires the 'pdf2image' package. Install backend dependencies to enable PDF ingestion."
        ) from exc

    try:
        pytesseract = importlib.import_module("pytesseract")
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency missing
        raise RuntimeError(
            "OCR fallback requires the 'pytesseract' package. Install backend dependencies to enable PDF ingestion."
        ) from exc

    poppler_path = os.environ.get("POPPLER_PATH") or None
    try:
        images = convert_from_path(str(file_path), dpi=DEFAULT_OCR_DPI, poppler_path=poppler_path)
    except Exception as exc:
        raise RuntimeError(
            "Failed to rasterize PDF for OCR. Ensure Poppler utilities are installed and accessible."
        ) from exc

    ocr_segments: List[str] = []
    for page_number, image in enumerate(images, start=1):
        try:
            text = pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Tesseract OCR binary not found. Install 'tesseract-ocr' (and language packs) on the host system."
            ) from exc
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("OCR failed for %s page %s: %s", file_path, page_number, exc)
            text = ""
        text = text.strip()
        if text:
            ocr_segments.append(text)
        else:
            LOGGER.debug("OCR produced empty output for %s page %s", file_path, page_number)

    if not ocr_segments:
        LOGGER.warning("OCR fallback produced no text for PDF %s", file_path)
        return ""

    return "\n\n".join(ocr_segments).strip()
