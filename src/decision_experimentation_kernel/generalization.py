"""Scoped generalization over domain-provided conditions (not editorial categories)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

APPLICABILITY_CLASSES = (
    "insufficient_evidence",
    "universally_applicable",
    "context_dependent",
    "failed",
)


def classify_applicability(
    *,
    experiments_run: int,
    evaluated_n: int,
    success_rate: float | None,
    opposing_n: int,
    conditions_with_support: list[str],
    conditions_seen: list[str],
) -> dict[str, str]:
    """Classify applicability from experiment counts and condition labels.

    Condition labels are domain-provided free-form strings.
    """
    if evaluated_n < 2 or experiments_run < 2:
        return {
            "class": "insufficient_evidence",
            "rationale": "Fewer than two evaluated independent experiments.",
        }
    if success_rate is not None and success_rate < 0.34 and opposing_n >= 2:
        return {
            "class": "failed",
            "rationale": "Repeated opposing evaluations with low success rate.",
        }
    supported = [c for c in conditions_with_support if c and c != "unspecified"]
    seen = [c for c in conditions_seen if c and c != "unspecified"]
    if (
        success_rate is not None
        and success_rate >= 0.75
        and opposing_n == 0
        and len(supported) >= 2
    ):
        return {
            "class": "universally_applicable",
            "rationale": (
                "High success across multiple condition labels with no opposing evaluations."
            ),
        }
    if len(seen) >= 2 and len(supported) == 1:
        return {
            "class": "context_dependent",
            "rationale": "Support concentrated in a subset of observed conditions.",
        }
    if success_rate is not None and 0.34 <= success_rate < 0.75:
        return {
            "class": "context_dependent",
            "rationale": "Mixed outcomes suggest conditional applicability.",
        }
    if success_rate is not None and success_rate >= 0.75 and opposing_n == 0:
        return {
            "class": "context_dependent",
            "rationale": (
                "Strong success so far, but not yet observed across multiple conditions."
            ),
        }
    return {
        "class": "insufficient_evidence",
        "rationale": "Evidence pattern is inconclusive for applicability classification.",
    }


def _condition_label(conditions: dict[str, Any], key: str) -> str:
    value = conditions.get(key)
    if value is None or value == "":
        return "unspecified"
    return f"{key}={value}"


def compute_scoped_generalization(
    *,
    cases: list[dict[str, Any]],
    condition_key: str,
    decision_type: str | None = None,
) -> dict[str, Any]:
    """Descriptive scoped generalization.

    ``cases`` entries should include::

        {
          "experiment": {...},          # with conditions
          "support_signal": str|None,
          "failure_analysis": dict|None,
          "evaluation": dict|None,
          "decision": {...}|None,
        }

    Does not promote decisions. Does not invent universal rules.
    """
    if not (condition_key or "").strip():
        raise ValueError("condition_key is required for scoped generalization.")

    filtered = cases
    if decision_type:
        filtered = [
            c
            for c in cases
            if (c.get("decision") or {}).get("decision_type") == decision_type
            or (c.get("experiment") or {}).get("decision_type") == decision_type
        ]

    by_condition: dict[str, dict[str, int]] = defaultdict(
        lambda: {"experiments": 0, "supporting": 0, "opposing": 0, "inconclusive": 0}
    )
    experiment_ids_by_condition: dict[str, set[str]] = defaultdict(set)
    failures: list[dict[str, Any]] = []
    evaluated = []

    for case in filtered:
        experiment = case.get("experiment") or {}
        conditions = experiment.get("conditions") or {}
        label = _condition_label(conditions, condition_key)
        exp_id = experiment.get("id") or "unknown"
        experiment_ids_by_condition[label].add(exp_id)
        signal = case.get("support_signal")
        if signal:
            evaluated.append(case)
            if signal in {"supporting", "weak_supporting"}:
                by_condition[label]["supporting"] += 1
            elif signal == "opposing":
                by_condition[label]["opposing"] += 1
                failures.append(
                    {
                        "experiment_id": exp_id,
                        "condition": label,
                        "failure_analysis": case.get("failure_analysis"),
                        "evaluation": case.get("evaluation"),
                    }
                )
            else:
                by_condition[label]["inconclusive"] += 1

    for label, ids in experiment_ids_by_condition.items():
        by_condition[label]["experiments"] = len(ids)

    supporting_n = sum(
        1
        for c in evaluated
        if c.get("support_signal") in {"supporting", "weak_supporting"}
    )
    opposing_n = sum(1 for c in evaluated if c.get("support_signal") == "opposing")
    evaluated_n = len(evaluated)
    experiments_run = len(
        {
            (c.get("experiment") or {}).get("id")
            for c in filtered
            if (c.get("experiment") or {}).get("id")
        }
    )
    success_rate = (supporting_n / evaluated_n) if evaluated_n else None

    conditions_with_support = [
        label
        for label, stats in by_condition.items()
        if stats["supporting"] > 0 and stats["supporting"] >= stats["opposing"]
    ]
    applicability = classify_applicability(
        experiments_run=experiments_run,
        evaluated_n=evaluated_n,
        success_rate=success_rate,
        opposing_n=opposing_n,
        conditions_with_support=conditions_with_support,
        conditions_seen=list(by_condition.keys()),
    )

    scoped_findings: list[str] = []
    for label, stats in sorted(by_condition.items()):
        if stats["supporting"] > 0 and stats["opposing"] == 0 and stats["supporting"] >= 1:
            scoped_findings.append(
                f"Support observed under {label} "
                f"(supporting={stats['supporting']}, opposing={stats['opposing']})."
            )
        elif stats["opposing"] > 0 and stats["supporting"] == 0:
            scoped_findings.append(
                f"Unsupported / opposing under {label} "
                f"(supporting={stats['supporting']}, opposing={stats['opposing']})."
            )
        elif stats["supporting"] > 0 and stats["opposing"] > 0:
            scoped_findings.append(
                f"Mixed under {label} "
                f"(supporting={stats['supporting']}, opposing={stats['opposing']})."
            )

    return {
        "schema_version": "efdek.generalization.0.1",
        "descriptive_only": True,
        "condition_key": condition_key,
        "decision_type": decision_type,
        "experiments_run": experiments_run,
        "evaluations_recorded": evaluated_n,
        "success_rate": success_rate,
        "condition_breakdown": dict(by_condition),
        "known_failure_conditions": failures,
        "scoped_findings": scoped_findings,
        "applicability_class": applicability["class"],
        "applicability_rationale": applicability["rationale"],
        "note": (
            "Generalization summaries are research statistics. "
            "They do not automatically promote decisions or create universal rules."
        ),
    }
