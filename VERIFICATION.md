# Clean-clone verification

This note records how publication readiness was checked **without** depending on the Editorial Decision Lab working tree.

## Procedure

1. Copy `opensource/decision-experimentation-kernel/` to a temporary directory outside the EDL repository.
2. Create a fresh virtualenv in that directory.
3. `pip install -e ".[dev]"`
4. `pytest -q`
5. Run the three examples.

## Commands used (Windows PowerShell)

```powershell
$src = "<path-to>\opensource\decision-experimentation-kernel"
$dst = Join-Path $env:TEMP ("dek-verify-" + [guid]::NewGuid().ToString())
Copy-Item -Recurse $src $dst
Set-Location $dst
python -m venv .venv
.\.venv\Scripts\pip install -U pip
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python examples\editorial\run.py
.\.venv\Scripts\python examples\audit\run.py
.\.venv\Scripts\python examples\operations\run.py
```

## Expected

| Step | Expected |
| --- | --- |
| Install | Succeeds with no EDL packages required |
| Tests | All pass |
| Editorial | Prints JSON + `EDITORIAL_EXAMPLE: PASS` |
| Audit | Prints JSON + `AUDIT_EXAMPLE: PASS` |
| Operations | Prints JSON + `OPERATIONS_EXAMPLE: PASS` |

## Open Source M1 verification (2026-08-27)

Performed on Windows: copied this project to `%TEMP%\dek-verify-*`, created a fresh venv, installed with `pip install -e ".[dev]"`, ran `pytest -q` (**7 passed**), ran all three examples (**PASS**).

Independence check: package root had `HAS_APP=False` and `HAS_EDL_MARKER=False`.

See `OPEN_SOURCE_M1_REPORT.md`.
