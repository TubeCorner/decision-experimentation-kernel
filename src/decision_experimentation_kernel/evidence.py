"""Evidence records — opaque domain payload + provenance refs."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_evidence_record(
    *,
    domain: str,
    payload: dict[str, Any],
    source_refs: list[dict[str, Any]] | None = None,
    notes: str | None = None,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    """Build a domain-agnostic evidence shell.

    The kernel does not interpret ``payload``. Callers own schema and meaning.
    """
    if not domain or not str(domain).strip():
        raise ValueError("domain is required.")
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict.")
    return {
        "id": evidence_id or str(uuid4()),
        "domain": domain.strip(),
        "payload": payload,
        "source_refs": list(source_refs or []),
        "notes": (notes or "").strip() or None,
        "schema_version": "efdek.evidence.0.1",
    }
