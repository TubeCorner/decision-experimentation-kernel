"""Evidence-first decision experimentation kernel.

A small Python library for experimenting with decisions, preserving
contradictory outcomes, analyzing failures, and producing scoped hypotheses.

Domain-specific acquisition, observation generation, decision ontologies,
execution, and evaluation criteria stay outside this package.
"""

from decision_experimentation_kernel.decision import build_decision
from decision_experimentation_kernel.evaluation import normalize_evaluation
from decision_experimentation_kernel.evidence import build_evidence_record
from decision_experimentation_kernel.experiment import build_experiment
from decision_experimentation_kernel.failure import normalize_failure_analysis
from decision_experimentation_kernel.generalization import (
    classify_applicability,
    compute_scoped_generalization,
)
from decision_experimentation_kernel.hypothesis import build_hypothesis
from decision_experimentation_kernel.lifecycle import run_case
from decision_experimentation_kernel.observation import build_observation
from decision_experimentation_kernel.support import (
    SUPPORT_SIGNALS,
    apply_support_policy,
)

__all__ = [
    "SUPPORT_SIGNALS",
    "apply_support_policy",
    "build_decision",
    "build_evidence_record",
    "build_experiment",
    "build_hypothesis",
    "build_observation",
    "classify_applicability",
    "compute_scoped_generalization",
    "normalize_evaluation",
    "normalize_failure_analysis",
    "run_case",
]

__version__ = "0.1.0"
