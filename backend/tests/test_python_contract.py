from __future__ import annotations

from pathlib import Path
import sys
import tomllib

from packaging.requirements import Requirement


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
REQUIRED_PYTHON = (3, 11, 7)


def _requirement_names(path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "-r ")):
            continue
        names.add(Requirement(line).name.lower())
    return names


def test_backend_runs_on_exact_required_python() -> None:
    assert sys.version_info[:3] == REQUIRED_PYTHON


def test_python_version_sources_are_synchronized() -> None:
    pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))

    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.11.7"
    assert pyproject["project"]["requires-python"] == "==3.11.7"


def test_requirement_files_match_project_metadata() -> None:
    pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_metadata = {
        Requirement(value).name.lower() for value in pyproject["project"]["dependencies"]
    }
    test_metadata = {
        Requirement(value).name.lower()
        for value in pyproject["project"]["optional-dependencies"]["test"]
    }

    assert _requirement_names(BACKEND / "requirements.txt") == runtime_metadata
    assert _requirement_names(BACKEND / "requirements-dev.txt") == test_metadata
