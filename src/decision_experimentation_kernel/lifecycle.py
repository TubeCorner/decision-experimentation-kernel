"""Minimal lifecycle runner — assemble one case through the shared stages."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from decision_experimentation_kernel.evaluation import normalize_evaluation
from decision_experimentation_kernel.failure import normalize_failure_analysis
from decision_experimentation_kernel.support import apply_support_policy


def run_case(
    *,
    evidence: dict[str, Any],
    observations: list[dict[str, Any]],
    decision: dict[str, Any],
    experiment: dict[str, Any],
    evaluation_criteria: list[dict[str, Any]],
    evaluation_answers: dict[str, Any],
    support_policy: Callable[[dict[str, Any]], str],
    failure_analysis: dict[str, Any] | None = None,
    require_failure_on_opposing: bool = True,
) -> dict[str, Any]:
    """Run Evaluation → Support/Opposition → optional Failure Analysis for one case.

    Evidence/observation/decision/experiment are accepted as already-built
    records (domains may synthesize them). This function does not acquire media
    or call EDL services.
    """
    evaluation = normalize_evaluation(
        criteria=evaluation_criteria, answers=evaluation_answers
    )
    support_signal = apply_support_policy(evaluation, support_policy)

    failure = None
    if support_signal == "opposing" and require_failure_on_opposing:
        failure = normalize_failure_analysis(failure_analysis)
    elif failure_analysis:
        failure = normalize_failure_analysis(failure_analysis)

    return {
        "evidence": evidence,
        "observations": observations,
        "decision": decision,
        "experiment": experiment,
        "evaluation": evaluation,
        "support_signal": support_signal,
        "failure_analysis": failure,
        "contradictory_record": {
            "supporting_signal": support_signal
            in {"supporting", "weak_supporting"},
            "opposing_signal": support_signal == "opposing",
            "alternative_explanation": (failure or {}).get("alternative_explanation"),
            "failure_reason": (failure or {}).get("why_failed"),
            "missing_evidence": (failure or {}).get("missing_evidence"),
            "boundary_condition": (failure or {}).get("boundary_condition")
            or (failure or {}).get("content_specific_limitations"),
            "confidence_or_uncertainty": (failure or {}).get("confidence_note"),
        },
        "schema_version": "efdek.case.0.1",
    }
