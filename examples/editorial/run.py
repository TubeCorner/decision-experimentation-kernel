"""Editorial domain example — trim_opening vs preserve_opening via extracted kernel.

Domain-owned editorial criteria and policy (not kernel concepts).
"""

from __future__ import annotations

import json
from decision_experimentation_kernel import (
    build_decision,
    build_evidence_record,
    build_experiment,
    build_hypothesis,
    build_observation,
    compute_scoped_generalization,
    run_case,
)
from decision_experimentation_kernel.support import answer

# Domain-owned editorial evaluation criteria (NOT kernel taxonomy).
EDITORIAL_CRITERIA = [
    {"id": "preferred_version", "prompt": "Which version is preferred?", "kind": "choice",
     "choices": ["a", "b", "tie"]},
    {"id": "meaning_preserved", "prompt": "Was meaning preserved?", "kind": "yes_no_unclear"},
    {"id": "clarity_improved", "prompt": "Did clarity improve?", "kind": "yes_no_unclear"},
    {"id": "pacing_improved", "prompt": "Did pacing improve?", "kind": "yes_no_unclear"},
    {"id": "introduced_regressions", "prompt": "Did the decision introduce regressions?",
     "kind": "yes_no_unclear"},
    {"id": "preference_why", "prompt": "Why?", "kind": "text"},
]


def editorial_support_policy(evaluation: dict) -> str:
    """Domain-owned support policy for editorial evaluations."""
    preferred = answer(evaluation, "preferred_version")
    meaning = answer(evaluation, "meaning_preserved")
    regressions = answer(evaluation, "introduced_regressions")
    if preferred == "b" and meaning in {"yes", "unclear"} and regressions in {
        "no",
        "unclear",
        "unanswered",
    }:
        if meaning == "yes" and regressions == "no":
            return "supporting"
        return "weak_supporting"
    if preferred == "a" or regressions == "yes" or meaning == "no":
        return "opposing"
    return "inconclusive"


def _case_trim_supported():
    evidence = build_evidence_record(
        domain="editorial",
        payload={
            "video_id": "demo-editorial-001",
            "opening_transcript": "uh so yeah welcome back to the show today we talk markets",
            "opening_window_ms": 8000,
        },
        source_refs=[{"section": "transcript", "start_ms": 0, "end_ms": 4500}],
    )
    obs = build_observation(
        statement="Opening contains soft filler before substantive topic language.",
        evidence_ids=[evidence["id"]],
        kind="opening_softness",
        confidence=0.8,
    )
    decision = build_decision(
        decision_type="trim_opening",
        choice="trim_opening",
        observation_ids=[obs["id"]],
        rationale="Soft open delays topic entry.",
        alternatives_considered=["preserve_opening"],
    )
    experiment = build_experiment(
        decision_id=decision["id"],
        conditions={"opening_type": "soft_filler", "content_form": "podcast_short"},
        procedure="Compare Version A (preserve) vs Version B (trim to first topic clause).",
        comparison={"version_a": "preserve_opening", "version_b": "trim_opening"},
        outcome={"rendered": "synthetic"},
    )
    return run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=experiment,
        evaluation_criteria=EDITORIAL_CRITERIA,
        evaluation_answers={
            "preferred_version": "b",
            "meaning_preserved": "yes",
            "clarity_improved": "yes",
            "pacing_improved": "yes",
            "introduced_regressions": "no",
            "preference_why": "Faster to substance without losing topic.",
        },
        support_policy=editorial_support_policy,
    )


def _case_trim_opposed_hard_open():
    evidence = build_evidence_record(
        domain="editorial",
        payload={
            "video_id": "demo-editorial-002",
            "opening_transcript": "The Fed just hiked fifty basis points — here is why it matters",
            "opening_window_ms": 8000,
        },
        source_refs=[{"section": "transcript", "start_ms": 0, "end_ms": 3000}],
    )
    obs = build_observation(
        statement="Opening already states the core claim in the first clause.",
        evidence_ids=[evidence["id"]],
        kind="hard_open_claim",
        confidence=0.85,
    )
    decision = build_decision(
        decision_type="trim_opening",
        choice="trim_opening",
        observation_ids=[obs["id"]],
        rationale="Attempted trim even though open is already hard.",
        alternatives_considered=["preserve_opening"],
    )
    experiment = build_experiment(
        decision_id=decision["id"],
        conditions={"opening_type": "hard_claim", "content_form": "podcast_short"},
        procedure="Compare preserve vs trim on a hard open.",
        comparison={"version_a": "preserve_opening", "version_b": "trim_opening"},
        outcome={"rendered": "synthetic"},
    )
    return run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=experiment,
        evaluation_criteria=EDITORIAL_CRITERIA,
        evaluation_answers={
            "preferred_version": "a",
            "meaning_preserved": "no",
            "clarity_improved": "no",
            "pacing_improved": "unclear",
            "introduced_regressions": "yes",
            "preference_why": "Trim cut the claim; preserve was clearer.",
        },
        support_policy=editorial_support_policy,
        failure_analysis={
            "why_failed": "Trim removed the opening claim that carried meaning.",
            "missing_evidence": "No reliable hard-boundary marker before trim point.",
            "unsupported_assumptions": "Assumed all opens are soft filler.",
            "content_specific_limitations": "Hard-claim opens are a boundary condition.",
            "opposing_evidence": "Reviewer preferred Version A; meaning_preserved=no.",
            "alternative_explanation": "Preserve opening may be correct when claim is front-loaded.",
            "boundary_condition": "opening_type=hard_claim",
            "confidence_note": "Single opposing case; confidence limited.",
        },
    )


def main() -> int:
    supporting = _case_trim_supported()
    opposing = _case_trim_opposed_hard_open()
    cases = [supporting, opposing]

    assert supporting["support_signal"] in {"supporting", "weak_supporting"}
    assert opposing["support_signal"] == "opposing"
    assert opposing["failure_analysis"] is not None
    assert opposing["contradictory_record"]["opposing_signal"] is True
    assert opposing["contradictory_record"]["alternative_explanation"]

    summary = compute_scoped_generalization(
        cases=cases,
        condition_key="opening_type",
        decision_type="trim_opening",
    )

    hypothesis = build_hypothesis(
        title="Trim opening helps soft filler but not hard claims",
        research_question=(
            "Under what opening conditions does trim_opening improve Shorts without "
            "harming meaning?"
        ),
        observed_pattern="; ".join(summary["scoped_findings"]),
        proposed_explanation=(
            "Trim opening is supported when the open is soft filler; opposing when the "
            "open already carries the core claim."
        ),
        alternative_explanations=[
            "Reviewer preference is aesthetic pacing, not meaning structure.",
            "Transcript OCR error misclassified hard claim as soft filler.",
        ],
        evidence_gaps="Only two synthetic cases; no replicated corpus breadth.",
        falsifiability_criterion=(
            "If hard-claim opens still prefer trim_opening with meaning preserved "
            "across ≥2 independent videos, this hypothesis is weakened."
        ),
        future_test_plan="Run targeted A/B on labeled soft vs hard opens.",
        related_experiment_ids=[
            supporting["experiment"]["id"],
            opposing["experiment"]["id"],
        ],
        related_decision_ids=[
            supporting["decision"]["id"],
            opposing["decision"]["id"],
        ],
        confidence=0.45,
        status="active",
    )

    report = {
        "domain": "editorial",
        "cases": [
            {
                "support_signal": c["support_signal"],
                "decision": c["decision"]["choice"],
                "conditions": c["experiment"]["conditions"],
                "contradictory_record": c["contradictory_record"],
            }
            for c in cases
        ],
        "scoped_generalization": summary,
        "hypothesis": {
            "title": hypothesis["title"],
            "observed_pattern": hypothesis["observed_pattern"],
            "alternatives": hypothesis["alternative_explanations"],
            "confidence": hypothesis["confidence"],
        },
    }
    print(json.dumps(report, indent=2))
    print("EDITORIAL_EXAMPLE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
