"""Decisions — domain-owned decision type + options."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_decision(
    *,
    decision_type: str,
    choice: str,
    observation_ids: list[str],
    rationale: str | None = None,
    alternatives_considered: list[str] | None = None,
    decision_id: str | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a decision record.

    ``decision_type`` and ``choice`` are opaque strings owned by the domain.
    The kernel does not validate them against an ontology.
    """
    dtype = (decision_type or "").strip()
    chosen = (choice or "").strip()
    if not dtype:
        raise ValueError("decision_type is required.")
    if not chosen:
        raise ValueError("choice is required.")
    if not observation_ids:
        raise ValueError("At least one observation_id is required.")
    record = {
        "id": decision_id or str(uuid4()),
        "decision_type": dtype,
        "choice": chosen,
        "observation_ids": list(dict.fromkeys(observation_ids)),
        "rationale": (rationale or "").strip() or None,
        "alternatives_considered": [
            item.strip() for item in (alternatives_considered or []) if item and item.strip()
        ],
        "schema_version": "efdek.decision.0.1",
    }
    if extras:
        record["extras"] = dict(extras)
    return record
