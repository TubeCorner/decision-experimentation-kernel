"""Observations — contestable statements grounded in evidence refs."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_observation(
    *,
    statement: str,
    evidence_ids: list[str],
    kind: str | None = None,
    confidence: float | None = None,
    observation_id: str | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an observation linked to evidence.

    ``kind`` is free-form and domain-owned (not an editorial ontology).
    """
    text = (statement or "").strip()
    if not text:
        raise ValueError("statement is required.")
    if not evidence_ids:
        raise ValueError("At least one evidence_id is required.")
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1.")
    record = {
        "id": observation_id or str(uuid4()),
        "statement": text,
        "kind": (kind or "").strip() or None,
        "evidence_ids": list(dict.fromkeys(evidence_ids)),
        "confidence": confidence,
        "schema_version": "efdek.observation.0.1",
    }
    if extras:
        record["extras"] = dict(extras)
    return record
