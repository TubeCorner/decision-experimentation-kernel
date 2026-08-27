"""Failure analysis — required research artifact fields."""

from __future__ import annotations

from typing import Any

FAILURE_ANALYSIS_FIELDS = (
    "why_failed",
    "missing_evidence",
    "unsupported_assumptions",
    "content_specific_limitations",
)


class FailureAnalysisError(ValueError):
    pass


def normalize_failure_analysis(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Require four failure-analysis fields; optional contradiction fields allowed.

    ``content_specific_limitations`` may hold any domain boundary notes
    (not limited to editorial content).
    """
    if not payload:
        raise FailureAnalysisError(
            "Failure analysis is required when recording opposing/poor outcomes."
        )
    result: dict[str, Any] = {}
    for field in FAILURE_ANALYSIS_FIELDS:
        value = (payload.get(field) or "").strip()
        if not value:
            raise FailureAnalysisError(f"Failure analysis field '{field}' is required.")
        result[field] = value
    for optional in (
        "opposing_evidence",
        "alternative_explanation",
        "boundary_condition",
        "confidence_note",
    ):
        text = (payload.get(optional) or "").strip()
        if text:
            result[optional] = text
    result["recorded_as"] = "first_class_research_artifact"
    return result
