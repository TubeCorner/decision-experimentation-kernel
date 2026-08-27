"""Hypotheses — research artifacts with required alternatives (from EDL M5)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

HYPOTHESIS_STATUSES = ("draft", "active", "supported", "refuted")


class HypothesisError(ValueError):
    pass


def normalize_alternative_explanations(
    items: list[dict[str, Any]] | list[str] | None,
) -> list[dict[str, Any]]:
    """Require at least one alternative explanation."""
    if not items:
        raise HypothesisError(
            "At least one alternative explanation is required for disciplined reasoning."
        )
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if isinstance(item, str):
            label = chr(ord("A") + index) if index < 26 else str(index + 1)
            text = item.strip()
            notes = None
        else:
            label = (item.get("label") or chr(ord("A") + index)).strip()
            text = (item.get("explanation") or item.get("text") or "").strip()
            notes = (item.get("notes") or "").strip() or None
        if not text:
            raise HypothesisError(
                f"Alternative explanation {label} must include explanation text."
            )
        result.append({"label": label, "explanation": text, "notes": notes})
    return result


def build_hypothesis(
    *,
    title: str,
    research_question: str,
    observed_pattern: str,
    proposed_explanation: str,
    alternative_explanations: list[dict[str, Any]] | list[str] | None,
    evidence_gaps: str,
    falsifiability_criterion: str,
    future_test_plan: str,
    related_experiment_ids: list[str],
    related_decision_ids: list[str] | None = None,
    confidence: float | None = None,
    status: str = "draft",
    hypothesis_id: str | None = None,
) -> dict[str, Any]:
    """Build a hypothesis requiring alternatives, gaps, and falsifiability."""
    if status not in HYPOTHESIS_STATUSES:
        raise HypothesisError(
            f"Unsupported hypothesis status '{status}'. "
            f"Allowed: {', '.join(HYPOTHESIS_STATUSES)}."
        )
    for field_name, value in (
        ("title", title),
        ("research_question", research_question),
        ("observed_pattern", observed_pattern),
        ("proposed_explanation", proposed_explanation),
        ("evidence_gaps", evidence_gaps),
        ("falsifiability_criterion", falsifiability_criterion),
        ("future_test_plan", future_test_plan),
    ):
        if not (value or "").strip():
            raise HypothesisError(f"{field_name} is required.")
    if not related_experiment_ids:
        raise HypothesisError(
            "Every hypothesis must be traceable to at least one experiment."
        )
    if confidence is not None and not 0 <= confidence <= 1:
        raise HypothesisError("Confidence must be between 0 and 1.")

    return {
        "id": hypothesis_id or str(uuid4()),
        "title": title.strip(),
        "research_question": research_question.strip(),
        "related_decision_ids": list(dict.fromkeys(related_decision_ids or [])),
        "related_experiment_ids": list(dict.fromkeys(related_experiment_ids)),
        "observed_pattern": observed_pattern.strip(),
        "proposed_explanation": proposed_explanation.strip(),
        "alternative_explanations": normalize_alternative_explanations(
            alternative_explanations
        ),
        "evidence_gaps": evidence_gaps.strip(),
        "confidence": confidence,
        "status": status,
        "falsifiability_criterion": falsifiability_criterion.strip(),
        "future_test_plan": future_test_plan.strip(),
        "schema_version": "efdek.hypothesis.0.1",
        "epistemic_note": (
            "This is a research hypothesis artifact. It is not a production rule."
        ),
    }
