"""Smoke-import the three example modules (does not execute main unless asked)."""

from __future__ import annotations

import importlib.util
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    ROOT / "examples" / "editorial" / "run.py",
    ROOT / "examples" / "audit" / "run.py",
    ROOT / "examples" / "operations" / "run.py",
]


def test_examples_exist():
    for path in EXAMPLES:
        assert path.is_file(), path


def test_examples_run_as_scripts():
    for path in EXAMPLES:
        ns = runpy.run_path(str(path), run_name="__not_main__")
        assert "main" in ns
        assert ns["main"]() == 0
