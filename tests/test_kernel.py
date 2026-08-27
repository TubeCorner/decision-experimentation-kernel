"""Kernel unit tests — no Editorial Decision Lab dependency."""

from __future__ import annotations

import pytest

from decision_experimentation_kernel import (
    apply_support_policy,
    build_decision,
    build_evidence_record,
    build_experiment,
    build_hypothesis,
    build_observation,
    compute_scoped_generalization,
    normalize_evaluation,
    normalize_failure_analysis,
    run_case,
)
from decision_experimentation_kernel.support import answer


def _policy(evaluation: dict) -> str:
    preferred = answer(evaluation, "preferred_action")
    ok = answer(evaluation, "outcome_ok")
    if preferred == "do" and ok == "yes":
        return "supporting"
    if preferred == "skip" or ok == "no":
        return "opposing"
    return "inconclusive"


CRITERIA = [
    {
        "id": "preferred_action",
        "prompt": "Preferred action?",
        "kind": "choice",
        "choices": ["do", "skip"],
    },
    {"id": "outcome_ok", "prompt": "Outcome ok?", "kind": "yes_no_unclear"},
]


def test_lifecycle_supporting_and_opposing_preserved():
    evidence = build_evidence_record(domain="demo", payload={"n": 1})
    obs = build_observation(
        statement="signal present", evidence_ids=[evidence["id"]], kind="signal"
    )
    decision = build_decision(
        decision_type="act",
        choice="do",
        observation_ids=[obs["id"]],
        alternatives_considered=["skip"],
    )
    supporting_exp = build_experiment(
        decision_id=decision["id"],
        conditions={"mode": "transient"},
        procedure="try once",
    )
    opposing_exp = build_experiment(
        decision_id=decision["id"],
        conditions={"mode": "deterministic"},
        procedure="try once",
    )

    supporting = run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=supporting_exp,
        evaluation_criteria=CRITERIA,
        evaluation_answers={"preferred_action": "do", "outcome_ok": "yes"},
        support_policy=_policy,
    )
    opposing = run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=opposing_exp,
        evaluation_criteria=CRITERIA,
        evaluation_answers={"preferred_action": "skip", "outcome_ok": "no"},
        support_policy=_policy,
        failure_analysis={
            "why_failed": "Deterministic failure.",
            "missing_evidence": "No config check.",
            "unsupported_assumptions": "Assumed transient.",
            "content_specific_limitations": "Deterministic mode is a boundary.",
            "opposing_evidence": "outcome_ok=no",
            "alternative_explanation": "Skip or fix config instead.",
            "boundary_condition": "mode=deterministic",
            "confidence_note": "Single opposing case.",
        },
    )

    assert supporting["support_signal"] == "supporting"
    assert opposing["support_signal"] == "opposing"
    assert opposing["failure_analysis"]["why_failed"]
    assert opposing["contradictory_record"]["opposing_signal"] is True
    assert opposing["contradictory_record"]["alternative_explanation"]

    summary = compute_scoped_generalization(
        cases=[supporting, opposing],
        condition_key="mode",
        decision_type="act",
    )
    assert summary["descriptive_only"] is True
    assert any("transient" in f for f in summary["scoped_findings"])
    assert any("deterministic" in f or "Unsupported" in f for f in summary["scoped_findings"])

    hyp = build_hypothesis(
        title="Do works under transient only",
        research_question="When should do be chosen?",
        observed_pattern="; ".join(summary["scoped_findings"]),
        proposed_explanation="Transient supports; deterministic opposes.",
        alternative_explanations=["Reviewer noise."],
        evidence_gaps="Synthetic.",
        falsifiability_criterion="Two deterministic successes via do refute this.",
        future_test_plan="Add more labeled cases.",
        related_experiment_ids=[supporting_exp["id"], opposing_exp["id"]],
        related_decision_ids=[decision["id"]],
        confidence=0.4,
    )
    assert len(hyp["alternative_explanations"]) >= 1


def test_domain_criteria_are_injected_not_hardcoded():
    criteria = [
        {"id": "objection_valid", "prompt": "Valid?", "kind": "yes_no_unclear"},
    ]
    evaluation = normalize_evaluation(criteria=criteria, answers={"objection_valid": "yes"})
    assert "objection_valid" in evaluation
    assert "meaning_preserved" not in evaluation


def test_failure_analysis_requires_fields():
    with pytest.raises(Exception):
        normalize_failure_analysis({"why_failed": "only one field"})


def test_support_policy_must_return_known_signal():
    with pytest.raises(ValueError):
        apply_support_policy({}, lambda _e: "maybe")


def test_kernel_modules_do_not_import_app():
    import decision_experimentation_kernel as dek
    import decision_experimentation_kernel.evaluation as evaluation
    import decision_experimentation_kernel.generalization as generalization
    import decision_experimentation_kernel.support as support

    for module in (dek, evaluation, generalization, support):
        assert "app" not in getattr(module, "__dict__", {})
        source = Path_read(module.__file__)
        assert "from app" not in source
        assert "import app" not in source


def Path_read(path: str) -> str:
    from pathlib import Path

    return Path(path).read_text(encoding="utf-8")
