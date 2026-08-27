# Decision Experimentation Kernel

An evidence-first Python framework for experimenting with decisions, preserving contradictory outcomes, analyzing failures, and producing scoped hypotheses.

It is a small library. It is not a universal intelligence engine.

---

## The problem

A decision may work in one situation and fail in another.

A simple success rate or aggregate outcome can hide the conditions that explain those differences.

Illustrative scenario (not a new domain or runnable example):

```text
Case 1

Evidence:
temporary network failure

Decision:
retry

Outcome:
resolved


Case 2

Evidence:
invalid configuration

Decision:
retry

Outcome:
failed
```

An oversimplified summary might conclude:

```text
retry success rate: 50%
```

That number loses the more useful information:

```text
Under what conditions did retry work?

Under what conditions did retry fail?
```

The useful question is not only:

> Did this decision work?

It is:

> Under what conditions did it work, and under what conditions did it fail?

The Decision Experimentation Kernel exists to structure that investigation: preserve supporting outcomes, opposing outcomes, failure analysis, applicability conditions, and bounded/scoped hypotheses — instead of collapsing them into a single score.

You bring the domain. The kernel records the experiment structure and refuses to erase contradictory results.

---

## What this is

This project provides a reusable **decision experimentation** lifecycle for **evaluating decisions across cases** and **comparing alternative decisions** under domain-supplied criteria:

```text
Evidence
   ↓
Observation
   ↓
Decision
   ↓
Experiment / comparison
   ↓
Domain-specific evaluation
   ↓
Supporting + opposing evidence
   ↓
Failure analysis
   ↓
Applicability conditions
   ↓
Scoped hypothesis
```

It is a structured way to do **decision evaluation**: record experiments, keep **supporting and opposing evidence**, run **failure analysis**, note **applicability conditions**, and form **bounded / scoped hypotheses** — without collapsing contradictory outcomes into a single score.

---

## When might this be useful?

This library may be useful when you need to:

- evaluate a decision or rule across multiple cases
- compare alternative decisions or interventions
- preserve supporting and contradictory outcomes
- analyze why a decision failed
- identify conditions under which a decision appears to apply
- turn repeated experimental outcomes into a bounded hypothesis

It can help **structure** that investigation. It does not automate domain judgment, acquire evidence for you, or claim to fit every problem.

---

## What each stage means

| Stage | Role |
| --- | --- |
| **Evidence** | Opaque domain payload + provenance refs. The kernel does not acquire or interpret it. |
| **Observation** | A statement grounded in evidence ids. |
| **Decision** | A domain-owned decision type and choice (opaque strings). |
| **Experiment** | A procedure under domain-owned **conditions**, with optional comparison/outcome. |
| **Evaluation** | Answers to **caller-supplied** criteria (not a fixed metric taxonomy). |
| **Support / Opposition** | Classification via a **caller-supplied** policy. |
| **Failure analysis** | Required fields when outcomes oppose the decision; optional contradiction notes. |
| **Applicability / generalization** | Descriptive stats scoped by a condition key — not universal rules. |
| **Hypothesis** | A research artifact that requires alternatives, gaps, and falsifiability. |

---

## Three demonstrated domains

This repository currently demonstrates the lifecycle in **exactly three** domains:

1. **Editorial** — e.g. trim vs preserve an opening  
2. **Audit** — e.g. flag vs do not flag an exception  
3. **Operations** — e.g. retry vs escalate an incident  

These are demonstrations, **not** proof of universal applicability.

---

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python examples\editorial\run.py

# macOS / Linux
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python examples/editorial/run.py
```

Also:

```bash
python examples/audit/run.py
python examples/operations/run.py
```

---

## Examples

| Path | What it shows |
| --- | --- |
| `examples/editorial/run.py` | Editorial criteria (`meaning_preserved`, etc.) injected as **domain** policy; opposing hard-open case preserved |
| `examples/audit/run.py` | Audit criteria (`objection_valid`, `false_positive`, …); false-positive opposing case |
| `examples/operations/run.py` | Ops criteria; **retry succeeds for transient failures and fails for deterministic config errors** |

Editorial metric names appear only in the editorial example, not in the kernel.

---

## Contradictory evidence

**Contradictory outcomes** are preserved rather than discarded. Opposing evaluations are first-class (`support_signal=opposing`).

**Failure analysis** records why a decision failed, missing evidence, unsupported assumptions, limitations, and may include alternative explanations and boundary conditions.

Scoped generalization keeps **known failure conditions** and **applicability conditions**. The operations example intentionally preserves a failure case instead of hiding it.

---

## What this project does NOT do

This is **not**:

- an AI decision framework  
- a universal intelligence engine  
- a workflow automation platform  
- a generic agent framework  
- a SaaS platform  
- an LLM orchestration framework  
- a guarantee that findings generalize across domains  

Also outside the kernel (unless you provide them):

- evidence acquisition  
- observation generation  
- decision definitions / ontologies  
- execution (renders, remediations, ledger writes)  
- evaluation criteria and support policies  

---

## Current limitations

- Demonstrated in **three domains only**  
- Not independently validated by external users  
- No claim of universal applicability  
- Usefulness outside the demonstrated domains is **unproven**  
- Domain adapters still require domain knowledge  
- Does not acquire evidence automatically  
- Does not decide which decisions a domain should contain  
- In-memory dict records only — no database, UI, or API server  

---

## Install / test (summary)

```bash
pip install -e ".[dev]"
pytest -q
python examples/editorial/run.py
python examples/audit/run.py
python examples/operations/run.py
```

See `VERIFICATION.md` for clean-clone checks and `OPEN_SOURCE_M1_REPORT.md` for the publication readiness verdict.

---

## License

MIT — see `LICENSE`.
