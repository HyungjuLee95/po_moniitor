from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ROOT = (
    "AGENTS.md",
    "PROJECT.md",
    "CURRENT_TASK.md",
    "ROADMAP.md",
    "README.md",
    "MANUAL.md",
    "ERROR.md",
    "SKILL.md",
    "CHANGELOG.md",
)
REQUIRED_AREA = ("README.md", "MANUAL.md", "ERROR.md", "SKILL.md")
REQUIRED_DOMAIN = ("README.md", "MANUAL.md", "ERROR.md", "SKILL.md", "API.md")
AREAS = (ROOT / "frontend", ROOT / "backend")
DOMAIN_ROOTS = (
    ROOT / "frontend" / "src" / "domains",
    ROOT / "backend" / "app" / "domains",
)
FORBIDDEN_ROOT_ALIASES = ("ERRORS.md", "SKILLS.md")
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "__pycache__",
    "offline",
}
LOCAL_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
URI_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_markdown(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"Markdown is not UTF-8: {relative(path)}")
    except OSError as exc:
        errors.append(f"Cannot read Markdown: {relative(path)} ({exc})")
    return ""


def check_required_files(errors: list[str]) -> None:
    for filename in REQUIRED_ROOT:
        if not (ROOT / filename).is_file():
            errors.append(f"Missing root document: {filename}")

    for alias in FORBIDDEN_ROOT_ALIASES:
        if (ROOT / alias).exists():
            errors.append(
                f"Duplicate source-of-truth document: {alias} "
                "(use singular ERROR.md or SKILL.md)"
            )

    for area in AREAS:
        if not area.is_dir():
            errors.append(f"Missing project area: {relative(area)}")
            continue
        for filename in REQUIRED_AREA:
            if not (area / filename).is_file():
                errors.append(f"Missing area document: {relative(area / filename)}")


def actual_domains(domain_root: Path) -> list[Path]:
    if not domain_root.is_dir():
        return []
    return sorted(
        path
        for path in domain_root.iterdir()
        if path.is_dir()
        and not path.name.startswith((".", "_"))
        and path.name not in EXCLUDED_DIRECTORY_NAMES
    )


def check_domains(errors: list[str]) -> None:
    project_path = ROOT / "PROJECT.md"
    skill_path = ROOT / "SKILL.md"
    if not project_path.is_file() or not skill_path.is_file():
        return

    project_text = read_markdown(project_path, errors)
    skill_text = read_markdown(skill_path, errors)

    for domain_root in DOMAIN_ROOTS:
        if not domain_root.is_dir():
            errors.append(f"Missing domain root: {relative(domain_root)}")
            continue

        for domain in actual_domains(domain_root):
            for filename in REQUIRED_DOMAIN:
                document = domain / filename
                if not document.is_file():
                    errors.append(f"Missing domain document: {relative(document)}")
                elif document.stat().st_size == 0:
                    errors.append(f"Empty domain document: {relative(document)}")

            marker = relative(domain / "README.md")
            if marker not in project_text:
                errors.append(f"Domain absent from PROJECT.md: {marker}")
            if marker not in skill_text:
                errors.append(f"Domain absent from SKILL.md: {marker}")


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for markdown in ROOT.rglob("*.md"):
        if any(part in EXCLUDED_DIRECTORY_NAMES for part in markdown.relative_to(ROOT).parts):
            continue
        files.append(markdown)
    return sorted(files)


def normalize_link_target(raw_target: str) -> str:
    target = raw_target.strip().strip("<>")
    if " \"" in target:
        target = target.split(" \"", 1)[0]
    if " '" in target:
        target = target.split(" '", 1)[0]
    return unquote(target.split("#", 1)[0].strip())


def check_local_links(errors: list[str]) -> None:
    root_resolved = ROOT.resolve()
    for markdown in markdown_files():
        text = read_markdown(markdown, errors)
        for raw_target in LOCAL_LINK_PATTERN.findall(text):
            stripped = raw_target.strip()
            if not stripped or stripped.startswith("#") or URI_SCHEME_PATTERN.match(stripped):
                continue

            target = normalize_link_target(stripped)
            if not target:
                continue

            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(root_resolved)
            except ValueError:
                errors.append(
                    f"Link escapes project root: {relative(markdown)} -> {target}"
                )
                continue
            if not resolved.exists():
                errors.append(f"Broken link: {relative(markdown)} -> {target}")


def tracked_files() -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    return [
        Path(item.decode("utf-8", errors="replace"))
        for item in completed.stdout.split(b"\0")
        if item
    ]


def check_sensitive_tracked_files(errors: list[str]) -> None:
    sensitive_names = {"id_rsa", "id_ed25519", "credentials.json"}
    sensitive_suffixes = {".pem", ".key", ".p12", ".pfx"}

    for path in tracked_files():
        name = path.name.lower()
        is_private_env = name.startswith(".env") and not name.endswith(".example")
        if is_private_env or name in sensitive_names or path.suffix.lower() in sensitive_suffixes:
            errors.append(f"Sensitive file is tracked by Git: {path.as_posix()}")


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_domains(errors)
    check_local_links(errors)
    check_sensitive_tracked_files(errors)

    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}")
        return 1

    domain_count = sum(len(actual_domains(root)) for root in DOMAIN_ROOTS)
    print(
        "Project documentation checks passed: "
        f"{domain_count} area domains, {len(markdown_files())} Markdown files."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
