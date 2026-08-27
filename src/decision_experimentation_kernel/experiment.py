"""Experiments — structured comparison of a decision under conditions."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_experiment(
    *,
    decision_id: str,
    conditions: dict[str, Any],
    procedure: str,
    outcome: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
    experiment_id: str | None = None,
) -> dict[str, Any]:
    """Build an experiment record.

    ``conditions`` are domain-provided context keys used later for scoped
    generalization (not editorial content categories).
    """
    if not (decision_id or "").strip():
        raise ValueError("decision_id is required.")
    proc = (procedure or "").strip()
    if not proc:
        raise ValueError("procedure is required.")
    if not isinstance(conditions, dict):
        raise ValueError("conditions must be a dict.")
    return {
        "id": experiment_id or str(uuid4()),
        "decision_id": decision_id,
        "conditions": dict(conditions),
        "procedure": proc,
        "outcome": dict(outcome or {}),
        "comparison": dict(comparison or {}),
        "schema_version": "efdek.experiment.0.1",
    }
