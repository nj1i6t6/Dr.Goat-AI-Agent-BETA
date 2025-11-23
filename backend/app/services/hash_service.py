"""Utilities for generating verifiable hashes."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


class HashService:
    """Generate deterministic hashes for the append-only ledger."""

    @staticmethod
    def generate_hash(previous_hash: Optional[str], data: Dict[str, Any]) -> str:
        """Return a SHA-256 hash for the provided payload.

        The data payload must already be serialisable. We normalise the
        structure to ensure deterministic hashing across environments.
        """

        payload = {
            "previous_hash": previous_hash or "",
            "data": data,
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
