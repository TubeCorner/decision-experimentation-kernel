"""Operations domain example — retry / escalate / ignore with opposing case preserved."""

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

OPS_CRITERIA = [
    {"id": "incident_resolved", "prompt": "Was the incident resolved?", "kind": "yes_no_unclear"},
    {"id": "regression_introduced", "prompt": "Did the action introduce a regression?",
     "kind": "yes_no_unclear"},
    {"id": "latency_acceptable", "prompt": "Was resulting latency acceptable?",
     "kind": "yes_no_unclear"},
    {"id": "preferred_action", "prompt": "Which action was appropriate?", "kind": "choice",
     "choices": ["retry", "escalate", "ignore"]},
    {"id": "notes", "prompt": "Operator notes", "kind": "text"},
]


def ops_support_policy(evaluation: dict) -> str:
    """Support the chosen action when resolved, no regression, latency ok."""
    resolved = answer(evaluation, "incident_resolved")
    regression = answer(evaluation, "regression_introduced")
    latency = answer(evaluation, "latency_acceptable")
    preferred = answer(evaluation, "preferred_action")

    # For this demo, experiments always chose "retry"; support means retry was appropriate.
    if preferred == "retry" and resolved == "yes" and regression == "no":
        if latency == "yes":
            return "supporting"
        return "weak_supporting"
    if preferred in {"escalate", "ignore"} or resolved == "no" or regression == "yes":
        return "opposing"
    return "inconclusive"


def _case_retry_transient():
    evidence = build_evidence_record(
        domain="operations",
        payload={
            "incident_id": "INC-501",
            "service": "payments-api",
            "error": "503 Service Unavailable",
            "error_code": "UPSTREAM_TIMEOUT",
            "occurred_at": "2026-08-06T10:01:00Z",
        },
        source_refs=[{"system": "pager", "incident_id": "INC-501"}],
    )
    obs = build_observation(
        statement="Single 503 with upstream timeout; no config change in deploy window.",
        evidence_ids=[evidence["id"]],
        kind="transient_upstream_signal",
        confidence=0.75,
    )
    decision = build_decision(
        decision_type="incident_response",
        choice="retry",
        observation_ids=[obs["id"]],
        rationale="Likely transient upstream failure.",
        alternatives_considered=["escalate", "ignore"],
    )
    experiment = build_experiment(
        decision_id=decision["id"],
        conditions={"failure_mode": "transient_upstream", "action": "retry"},
        procedure="Execute one controlled retry and compare to escalate baseline.",
        comparison={"challenger": "retry", "baseline": "escalate"},
        outcome={"retry_result": "success", "http_status": 200},
    )
    return run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=experiment,
        evaluation_criteria=OPS_CRITERIA,
        evaluation_answers={
            "incident_resolved": "yes",
            "regression_introduced": "no",
            "latency_acceptable": "yes",
            "preferred_action": "retry",
            "notes": "Retry succeeded; escalate unnecessary.",
        },
        support_policy=ops_support_policy,
    )


def _case_retry_opposed_config_error():
    evidence = build_evidence_record(
        domain="operations",
        payload={
            "incident_id": "INC-777",
            "service": "payments-api",
            "error": "500 Internal Server Error",
            "error_code": "MISSING_CONFIG_KEY",
            "message": "Required env STRIPE_WEBHOOK_SECRET not set",
            "occurred_at": "2026-08-06T11:22:00Z",
        },
        source_refs=[{"system": "pager", "incident_id": "INC-777"}],
    )
    obs = build_observation(
        statement="Error message indicates missing configuration key after deploy.",
        evidence_ids=[evidence["id"]],
        kind="deterministic_config_signal",
        confidence=0.95,
    )
    decision = build_decision(
        decision_type="incident_response",
        choice="retry",
        observation_ids=[obs["id"]],
        rationale="Operator retried despite config error signal.",
        alternatives_considered=["escalate", "ignore"],
    )
    experiment = build_experiment(
        decision_id=decision["id"],
        conditions={"failure_mode": "deterministic_config", "action": "retry"},
        procedure="Execute retry on deterministic config failure; compare to escalate.",
        comparison={"challenger": "retry", "baseline": "escalate"},
        outcome={"retry_result": "failed", "http_status": 500, "same_error": True},
    )
    return run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=experiment,
        evaluation_criteria=OPS_CRITERIA,
        evaluation_answers={
            "incident_resolved": "no",
            "regression_introduced": "no",
            "latency_acceptable": "no",
            "preferred_action": "escalate",
            "notes": "Retry looped the same MISSING_CONFIG_KEY error; escalate required.",
        },
        support_policy=ops_support_policy,
        failure_analysis={
            "why_failed": "Retry cannot fix missing configuration; error is deterministic.",
            "missing_evidence": "Deploy diff was not checked before choosing retry.",
            "unsupported_assumptions": "Assumed all 5xx are transient.",
            "content_specific_limitations": "Deterministic config failures need escalate/fix.",
            "opposing_evidence": "incident_resolved=no; preferred_action=escalate; same_error after retry.",
            "alternative_explanation": "Escalate-to-config-fix is the correct response class.",
            "boundary_condition": "failure_mode=deterministic_config",
            "confidence_note": "Strong single opposing case; do not hide it.",
        },
    )


def main() -> int:
    supporting = _case_retry_transient()
    opposing = _case_retry_opposed_config_error()
    cases = [supporting, opposing]

    assert supporting["support_signal"] == "supporting"
    assert opposing["support_signal"] == "opposing"
    assert opposing["failure_analysis"]["boundary_condition"] == (
        "failure_mode=deterministic_config"
    )

    summary = compute_scoped_generalization(
        cases=cases,
        condition_key="failure_mode",
        decision_type="incident_response",
    )

    assert any("transient" in f.lower() for f in summary["scoped_findings"])
    assert any(
        "deterministic" in f.lower() or "unsupported" in f.lower()
        for f in summary["scoped_findings"]
    )

    scoped_statement = (
        "Retry appears effective under transient failure conditions but is unsupported "
        "for deterministic configuration failures."
    )

    hypothesis = build_hypothesis(
        title="Retry is condition-scoped, not universal",
        research_question="When should operators retry vs escalate on payments-api incidents?",
        observed_pattern=scoped_statement + " | " + "; ".join(summary["scoped_findings"]),
        proposed_explanation=(
            "Retry helps transient upstream timeouts; deterministic missing-config errors "
            "require escalate/fix and oppose retry."
        ),
        alternative_explanations=[
            "Retry count was too low on the config case.",
            "Pager classification of MISSING_CONFIG_KEY was wrong.",
        ],
        evidence_gaps="Two synthetic incidents; no week-long on-call corpus.",
        falsifiability_criterion=(
            "If deterministic_config incidents resolve via retry without config change "
            "in ≥2 independent cases, the opposing claim is weakened."
        ),
        future_test_plan="Label next 30 incidents by failure_mode and A/B retry vs escalate.",
        related_experiment_ids=[c["experiment"]["id"] for c in cases],
        related_decision_ids=[c["decision"]["id"] for c in cases],
        confidence=0.5,
        status="active",
    )

    report = {
        "domain": "operations",
        "scoped_statement": scoped_statement,
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
            "alternatives_count": len(hypothesis["alternative_explanations"]),
        },
        # Prove editorial categories are absent from kernel generalization:
        "editorial_categories_in_breakdown": [
            k
            for k in summary["condition_breakdown"]
            if k.startswith("podcast") or "interview" in k or "vlog" in k
        ],
    }
    assert report["editorial_categories_in_breakdown"] == []
    print(json.dumps(report, indent=2))
    print("OPERATIONS_EXAMPLE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
