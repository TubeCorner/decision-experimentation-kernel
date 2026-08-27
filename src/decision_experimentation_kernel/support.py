"""Support / opposition — domain-provided policy over evaluations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

SUPPORT_SIGNALS = (
    "supporting",
    "weak_supporting",
    "opposing",
    "inconclusive",
)

SupportPolicy = Callable[[dict[str, Any]], str]


def apply_support_policy(
    evaluation: dict[str, Any],
    policy: SupportPolicy,
) -> str:
    """Classify evaluation using a domain-owned policy.

    The policy is injected so domain criteria stay outside the kernel.
    """
    signal = policy(evaluation)
    if signal not in SUPPORT_SIGNALS:
        raise ValueError(
            f"Support policy returned '{signal}'. "
            f"Allowed: {', '.join(SUPPORT_SIGNALS)}."
        )
    return signal


def answer(evaluation: dict[str, Any], key: str) -> str | None:
    """Helper for domain policies: read normalized answer string."""
    item = evaluation.get(key)
    if isinstance(item, dict):
        return item.get("answer")
    return None
