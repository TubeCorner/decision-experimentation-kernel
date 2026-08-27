"""Evaluation — domain-provided criteria; kernel only normalizes answers."""

from __future__ import annotations

from typing import Any


class EvaluationError(ValueError):
    pass


def normalize_evaluation(
    *,
    criteria: list[dict[str, Any]],
    answers: dict[str, Any] | None,
) -> dict[str, Any]:
    """Normalize answers against domain-supplied criteria.

    Criteria are injected by the caller. Domain metric ids are *not* kernel
    concepts — the kernel only validates answer shapes.

    Criterion shape::

        {"id": str, "prompt": str, "kind": "yes_no_unclear" | "choice" | "text",
         "choices": [...] }  # required for kind=choice
    """
    if not criteria:
        raise EvaluationError("At least one evaluation criterion is required.")
    source = answers or {}
    result: dict[str, Any] = {}
    for question in criteria:
        question_id = question.get("id")
        if not question_id:
            raise EvaluationError("Each criterion requires an id.")
        kind = question.get("kind") or "text"
        prompt = question.get("prompt") or question_id
        raw = source.get(question_id)

        if kind == "choice":
            allowed = {str(c).lower() for c in (question.get("choices") or [])}
            if not allowed:
                raise EvaluationError(f"Criterion '{question_id}' choice requires choices.")
            value = (raw or "unanswered").strip().lower() if isinstance(raw, str) else "unanswered"
            if value != "unanswered" and value not in allowed:
                raise EvaluationError(
                    f"{question_id} must be one of {sorted(allowed)} or unanswered."
                )
            result[question_id] = {"prompt": prompt, "answer": value, "kind": kind}

        elif kind == "yes_no_unclear":
            if isinstance(raw, dict):
                value = (raw.get("answer") or "unanswered").strip().lower()
                notes = (raw.get("notes") or "").strip() or None
            else:
                value = (raw or "unanswered").strip().lower() if isinstance(raw, str) else "unanswered"
                notes = None
            if value not in {"yes", "no", "unclear", "unanswered"}:
                raise EvaluationError(
                    f"{question_id} must be yes, no, unclear, or unanswered."
                )
            result[question_id] = {
                "prompt": prompt,
                "answer": value,
                "notes": notes,
                "kind": kind,
            }

        elif kind == "text":
            text = ""
            if isinstance(raw, dict):
                text = (raw.get("answer") or raw.get("text") or "").strip()
            elif isinstance(raw, str):
                text = raw.strip()
            result[question_id] = {
                "prompt": prompt,
                "answer": text or None,
                "kind": kind,
            }
        else:
            raise EvaluationError(f"Unsupported criterion kind '{kind}'.")
    return result
