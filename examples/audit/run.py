"""Audit domain example — flag vs do_not_flag via extracted kernel (synthetic)."""

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

AUDIT_CRITERIA = [
    {"id": "objection_valid", "prompt": "Is the audit objection valid?", "kind": "yes_no_unclear"},
    {"id": "false_positive", "prompt": "Is this a false positive?", "kind": "yes_no_unclear"},
    {"id": "material_impact", "prompt": "Is material impact present?", "kind": "yes_no_unclear"},
    {"id": "preferred_action", "prompt": "Preferred action after review?", "kind": "choice",
     "choices": ["flag", "do_not_flag", "escalate"]},
    {"id": "notes", "prompt": "Reviewer notes", "kind": "text"},
]


def audit_support_policy(evaluation: dict) -> str:
    """Domain policy: support flagging when objection valid, not false positive, material."""
    valid = answer(evaluation, "objection_valid")
    fp = answer(evaluation, "false_positive")
    material = answer(evaluation, "material_impact")
    preferred = answer(evaluation, "preferred_action")

    if preferred == "flag" and valid == "yes" and fp == "no" and material in {"yes", "unclear"}:
        if material == "yes":
            return "supporting"
        return "weak_supporting"
    if preferred == "do_not_flag" or fp == "yes" or valid == "no":
        return "opposing"
    return "inconclusive"


def _case_flag_duplicate_payment():
    evidence = build_evidence_record(
        domain="audit",
        payload={
            "record_id": "TX-1001",
            "vendor": "Acme Supplies",
            "amount": 12500.00,
            "invoice_ids": ["INV-88", "INV-88"],
            "payment_dates": ["2026-01-04", "2026-01-11"],
        },
        source_refs=[{"system": "ap_ledger", "record_id": "TX-1001"}],
    )
    obs = build_observation(
        statement="Same invoice_id paid twice within 7 days for identical amount.",
        evidence_ids=[evidence["id"]],
        kind="duplicate_payment_pattern",
        confidence=0.9,
    )
    decision = build_decision(
        decision_type="exception_disposition",
        choice="flag",
        observation_ids=[obs["id"]],
        rationale="Duplicate invoice payment pattern warrants exception.",
        alternatives_considered=["do_not_flag", "escalate"],
    )
    experiment = build_experiment(
        decision_id=decision["id"],
        conditions={"exception_class": "duplicate_payment", "control": "invoice_uniqueness"},
        procedure="Compare flag vs do_not_flag against senior reviewer adjudication.",
        comparison={"challenger": "flag", "baseline": "do_not_flag"},
        outcome={"adjudication": "confirmed_duplicate"},
    )
    return run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=experiment,
        evaluation_criteria=AUDIT_CRITERIA,
        evaluation_answers={
            "objection_valid": "yes",
            "false_positive": "no",
            "material_impact": "yes",
            "preferred_action": "flag",
            "notes": "Confirmed duplicate payment.",
        },
        support_policy=audit_support_policy,
    )


def _case_flag_opposed_timing_difference():
    evidence = build_evidence_record(
        domain="audit",
        payload={
            "record_id": "TX-2044",
            "vendor": "Acme Supplies",
            "amount": 12500.00,
            "invoice_ids": ["INV-91", "INV-92"],
            "payment_dates": ["2026-02-01", "2026-02-03"],
            "memo": "Progress billing installment 1 and 2",
        },
        source_refs=[{"system": "ap_ledger", "record_id": "TX-2044"}],
    )
    obs = build_observation(
        statement="Two similar amounts to same vendor within 3 days.",
        evidence_ids=[evidence["id"]],
        kind="similar_amount_cluster",
        confidence=0.55,
    )
    decision = build_decision(
        decision_type="exception_disposition",
        choice="flag",
        observation_ids=[obs["id"]],
        rationale="Heuristic flagged similar amounts.",
        alternatives_considered=["do_not_flag"],
    )
    experiment = build_experiment(
        decision_id=decision["id"],
        conditions={
            "exception_class": "similar_amount_near_duplicate",
            "control": "invoice_uniqueness",
        },
        procedure="Adjudicate similar-amount heuristic flag.",
        comparison={"challenger": "flag", "baseline": "do_not_flag"},
        outcome={"adjudication": "legitimate_progress_billing"},
    )
    return run_case(
        evidence=evidence,
        observations=[obs],
        decision=decision,
        experiment=experiment,
        evaluation_criteria=AUDIT_CRITERIA,
        evaluation_answers={
            "objection_valid": "no",
            "false_positive": "yes",
            "material_impact": "no",
            "preferred_action": "do_not_flag",
            "notes": "Distinct invoices; progress billing.",
        },
        support_policy=audit_support_policy,
        failure_analysis={
            "why_failed": "Flag treated legitimate multi-invoice billing as duplicate.",
            "missing_evidence": "Invoice line-item narrative was not in the heuristic input.",
            "unsupported_assumptions": "Assumed similar amount + vendor + proximity implies duplicate.",
            "content_specific_limitations": "Progress billing creates near-duplicate amount patterns.",
            "opposing_evidence": "false_positive=yes; preferred_action=do_not_flag.",
            "alternative_explanation": "Need invoice_id equality, not amount proximity alone.",
            "boundary_condition": "exception_class=similar_amount_near_duplicate",
            "confidence_note": "One opposing adjudication; rule not rejected globally.",
        },
    )


def main() -> int:
    supporting = _case_flag_duplicate_payment()
    opposing = _case_flag_opposed_timing_difference()
    cases = [supporting, opposing]

    assert supporting["support_signal"] == "supporting"
    assert opposing["support_signal"] == "opposing"
    assert opposing["contradictory_record"]["missing_evidence"]
    assert opposing["contradictory_record"]["boundary_condition"]

    summary = compute_scoped_generalization(
        cases=cases,
        condition_key="exception_class",
        decision_type="exception_disposition",
    )

    hypothesis = build_hypothesis(
        title="Duplicate invoice_id flags hold; amount-proximity flags overfire",
        research_question=(
            "When should AP exceptions be flagged as duplicate payments?"
        ),
        observed_pattern="; ".join(summary["scoped_findings"]),
        proposed_explanation=(
            "Flagging is supported for identical invoice_id repeats; opposing for "
            "similar-amount clusters without invoice equality."
        ),
        alternative_explanations=[
            "Reviewer inconsistently applied materiality thresholds.",
            "Vendor naming collisions caused false similar-amount clusters.",
        ],
        evidence_gaps="Synthetic records only; no production ledger sample.",
        falsifiability_criterion=(
            "If identical invoice_id repeats are repeatedly adjudicated as false positives, "
            "the supporting claim is refuted."
        ),
        future_test_plan="Sample 50 AP clusters stratified by invoice equality vs amount proximity.",
        related_experiment_ids=[c["experiment"]["id"] for c in cases],
        related_decision_ids=[c["decision"]["id"] for c in cases],
        confidence=0.4,
        status="active",
    )

    report = {
        "domain": "audit",
        "cases": [
            {
                "support_signal": c["support_signal"],
                "decision": c["decision"]["choice"],
                "conditions": c["experiment"]["conditions"],
                "evaluation_keys": sorted(c["evaluation"].keys()),
                "contradictory_record": c["contradictory_record"],
            }
            for c in cases
        ],
        "scoped_generalization": summary,
        "hypothesis_title": hypothesis["title"],
        "hypothesis_alternatives": hypothesis["alternative_explanations"],
    }
    print(json.dumps(report, indent=2))
    # Prove editorial criteria are not required:
    for c in cases:
        assert "meaning_preserved" not in c["evaluation"]
        assert "objection_valid" in c["evaluation"]
    print("AUDIT_EXAMPLE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
