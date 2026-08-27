# Contributing

Keep contributions small and honest.

## Run tests

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\pip install -e ".[dev]"
# Unix:    .venv/bin/pip install -e ".[dev]"
pytest -q
```

## Kernel vs domain logic

| Belongs in the kernel (`src/`) | Belongs in an example / domain adapter |
| --- | --- |
| Evidence/observation/decision/experiment record helpers | Domain payloads and observation text |
| Evaluation **normalization** against injected criteria | Concrete criteria ids and prompts |
| Support signal application via injected policy | The policy function itself |
| Failure-analysis field requirements | Domain failure narratives |
| Scoped generalization over condition keys | Which condition keys matter |

Do not hard-code domain metrics (editorial, audit, or ops) into `src/`.

## Examples

- Prefer editing `examples/*/run.py` over inventing new domains.
- New domains are out of scope unless maintainers explicitly reopen that question.
- If you change an example decision, keep at least one **opposing** or failure case visible.

## Contradictory evidence

Do not “fix” demos by deleting opposing evaluations.  
Support, opposition, failure analysis, and scoped findings should remain representable.
