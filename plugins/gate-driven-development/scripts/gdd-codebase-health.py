#!/usr/bin/env python3
"""GDD-owned codebase health survey for early planning and completion gates."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


EXCLUDE_DIRS = {
    ".git",
    ".gdd",
    ".steering",
    ".worktrees",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".terraform",
    "build",
    "dist",
    "node_modules",
    "tmp",
    "vendor",
}

CODE_EXTENSIONS = {
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".tf",
    ".ts",
    ".tsx",
}

TEXT_EXTENSIONS = CODE_EXTENSIONS | {".json", ".md", ".toml", ".yaml", ".yml"}
PYTHON_FUNCTION_WARN_LIMIT = 40
PYTHON_FUNCTION_FAIL_LIMIT = 80
PYTHON_COMPLEXITY_LIMIT = 15
DEFAULT_BASELINE_FILE = "gdd-codebase-health-baseline.json"

LOCKFILES = {
    "package.json": ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"],
    "pyproject.toml": ["uv.lock", "poetry.lock", "pdm.lock"],
    "requirements.txt": ["requirements.lock", "requirements-dev.lock"],
    "Gemfile": ["Gemfile.lock"],
    "Cargo.toml": ["Cargo.lock"],
    "go.mod": ["go.sum"],
    "versions.tf": [".terraform.lock.hcl"],
}

LOCKFILE_NAMES = {name for names in LOCKFILES.values() for name in names}
LOCKFILE_NAMES.update({"bun.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock"})
LOCAL_LOCK_ONLY_MANIFESTS = {"go.mod"}

CI_FILE_NAMES = {
    ".buildkite/pipeline.yml",
    ".buildkite/pipeline.yaml",
    ".circleci/config.yml",
    ".circleci/config.yaml",
    ".drone.yml",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
    "bitbucket-pipelines.yml",
}


@dataclass
class Finding:
    category: str
    severity: str
    path: str
    evidence: str
    recommendation: str


@dataclass(frozen=True)
class LargeFileBaseline:
    path: str
    current_lines: int
    target_lines: int
    reduce_by: int
    expires_on: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class PythonComplexityBaseline:
    path: str
    function: str
    current_complexity: int
    target_complexity: int
    reduce_by: int
    expires_on: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class PythonFunctionCountBaseline:
    path: str
    current_count: int
    target_count: int
    reduce_by: int
    expires_on: str | None = None
    reason: str = ""


def run_git(repo: Path, args: list[str]) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return [line for line in completed.stdout.splitlines() if line.strip()]


def run_git_paths(repo: Path, args: list[str]) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return [item.decode("utf-8", errors="surrogateescape") for item in completed.stdout.split(b"\0") if item]


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def repo_files(repo: Path, names: Iterable[str], *, must_exist: bool = True) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        path = repo / name
        if (path.exists() or not must_exist) and not is_excluded(Path(name)):
            result.append(path)
    return result


def untracked_files(repo: Path) -> list[str]:
    return run_git_paths(repo, ["ls-files", "-z", "--others", "--exclude-standard"]) or []


def tracked_files(repo: Path) -> list[Path]:
    git_files = run_git_paths(repo, ["ls-files", "-z"])
    if git_files is not None:
        return repo_files(repo, [*git_files, *untracked_files(repo)])
    return [
        path
        for path in repo.rglob("*")
        if path.is_file() and not is_excluded(path.relative_to(repo))
    ]


def head_has_parent(repo: Path) -> bool:
    return run_git(repo, ["rev-parse", "--verify", "HEAD^"]) is not None


def resolve_changed_base(repo: Path, base_ref: str) -> tuple[str | None, bool]:
    head = run_git(repo, ["rev-parse", "--verify", "HEAD^{commit}"])
    head_oid = head[0] if head else None
    candidates = [base_ref, "origin/HEAD", "main", "master"]
    saw_head_candidate = False
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        candidate_oid = run_git(repo, ["rev-parse", "--verify", f"{candidate}^{{commit}}"])
        if candidate_oid is None:
            continue
        if candidate_oid[0] == head_oid:
            return None, True
        return candidate, saw_head_candidate
    return None, saw_head_candidate


def resolve_pre_pr_ref(repo: Path, base_ref: str) -> str | None:
    """Resolve the commit where this branch diverged from the target branch.

    Baseline entries must be measured against this ref, not the live working
    tree: a branch under repeated rebase can show a transient, inflated
    measurement that has nothing to do with the debt that actually predates
    the PR.
    """
    resolved_base, _ = resolve_changed_base(repo, base_ref)
    if resolved_base is None:
        return None
    merge_base = run_git(repo, ["merge-base", resolved_base, "HEAD"])
    return merge_base[0] if merge_base else None


def changed_files(repo: Path, base_ref: str) -> list[Path]:
    resolved_base, saw_head_candidate = resolve_changed_base(repo, base_ref)
    names: list[str] = []
    if resolved_base is not None:
        for range_expr in (f"{resolved_base}...HEAD", f"{resolved_base}..HEAD"):
            git_files = run_git_paths(repo, ["diff", "--relative", "--name-only", "-z", range_expr])
            if git_files is not None:
                names.extend(git_files)
                break
    for diff_args in (["diff", "--relative", "--name-only"], ["diff", "--relative", "--name-only", "--cached"]):
        git_files = run_git_paths(repo, [*diff_args, "-z"])
        if git_files is not None:
            names.extend(git_files)
    names.extend(untracked_files(repo))
    if resolved_base is None:
        if not head_has_parent(repo):
            return tracked_files(repo)
        if not saw_head_candidate:
            raise ValueError(
                f"changed mode base ref not found: {base_ref} "
                "(also tried origin/HEAD, main, master)"
            )
        if names:
            return repo_files(repo, names, must_exist=False)
        return []
    return repo_files(repo, names, must_exist=False)


def package_json_workspaces(manifest: Path) -> list[str]:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    workspaces = data.get("workspaces", [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages", [])
    if not isinstance(workspaces, list):
        return []
    return [item for item in workspaces if isinstance(item, str)]


def pnpm_workspace_packages(workspace_file: Path) -> list[str]:
    try:
        lines = workspace_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    packages: list[str] = []
    in_packages = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "packages:":
            in_packages = True
            continue
        if in_packages and not line.startswith((" ", "\t", "-")):
            break
        if in_packages and stripped.startswith("- "):
            packages.append(stripped[2:].strip().strip("'\""))
    return packages


def workspace_patterns(lock_dir: Path) -> list[str]:
    return [
        *package_json_workspaces(lock_dir / "package.json"),
        *pnpm_workspace_packages(lock_dir / "pnpm-workspace.yaml"),
    ]


def go_mod_required_modules(manifest: Path) -> set[str]:
    try:
        lines = manifest.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()
    modules: set[str] = set()
    in_require = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if stripped == "require (":
            in_require = True
            continue
        if in_require and stripped == ")":
            in_require = False
            continue
        if in_require:
            modules.add(stripped.split()[0])
            continue
        if stripped.startswith("require "):
            parts = stripped.split()
            if len(parts) >= 2:
                modules.add(parts[1])
    return modules


def go_mod_local_replacements(manifest: Path) -> set[str]:
    try:
        lines = manifest.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()
    modules: set[str] = set()
    in_replace = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if stripped == "replace (":
            in_replace = True
            continue
        if in_replace and stripped == ")":
            in_replace = False
            continue
        if in_replace or stripped.startswith("replace "):
            body = stripped.removeprefix("replace ").strip()
            if "=>" not in body:
                continue
            left, right = (part.strip() for part in body.split("=>", 1))
            replacement = right.split()[0] if right.split() else ""
            if replacement.startswith(("./", "../", "/")):
                modules.add(left.split()[0])
    return modules


def go_mod_requires_sum(manifest: Path) -> bool:
    required = go_mod_required_modules(manifest)
    if not required:
        return False
    return bool(required - go_mod_local_replacements(manifest))


def segment_glob_match(path: str, pattern: str) -> bool:
    path_parts = [part for part in path.split("/") if part]
    pattern_parts = [part for part in pattern.rstrip("/").split("/") if part]

    def matches(path_index: int, pattern_index: int) -> bool:
        if pattern_index == len(pattern_parts):
            return path_index == len(path_parts)
        pattern_part = pattern_parts[pattern_index]
        if pattern_part == "**":
            return any(matches(next_index, pattern_index + 1) for next_index in range(path_index, len(path_parts) + 1))
        if path_index >= len(path_parts):
            return False
        return fnmatch.fnmatchcase(path_parts[path_index], pattern_part) and matches(path_index + 1, pattern_index + 1)

    return matches(0, 0)


def ancestor_lock_covers_manifest(repo: Path, lock_dir: Path, manifest_path: Path) -> bool:
    try:
        nested_dir = manifest_path.parent.relative_to(lock_dir)
    except ValueError:
        return False
    nested = str(nested_dir)
    return any(segment_glob_match(nested, pattern) for pattern in workspace_patterns(lock_dir))


def count_lines(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def read_text_at_ref(repo: Path, ref: str, repo_relative_path: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "show", f"{ref}:{repo_relative_path}"],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return completed.stdout.decode("utf-8", errors="ignore")


def measure_lines_at_ref(repo: Path, ref: str, repo_relative_path: str) -> int | None:
    text = read_text_at_ref(repo, ref, repo_relative_path)
    return None if text is None else len(text.splitlines())


def measure_python_function_count_at_ref(repo: Path, ref: str, repo_relative_path: str) -> int | None:
    text = read_text_at_ref(repo, ref, repo_relative_path)
    if text is None:
        return None
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    return sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))


def measure_python_complexity_at_ref(repo: Path, ref: str, repo_relative_path: str, function_name: str) -> int | None:
    text = read_text_at_ref(repo, ref, repo_relative_path)
    if text is None:
        return None
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return python_function_complexity(node)
    return None


def rel(repo: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def looks_like_test(repo: Path, path: Path) -> bool:
    try:
        check_path = path.relative_to(repo)
    except ValueError:
        check_path = path
    parts = {part.lower() for part in check_path.parts}
    name = path.name.lower()
    return (
        "test" in parts
        or "tests" in parts
        or "__tests__" in parts
        or "spec" in parts
        or name.startswith("test_")
        or name.endswith(
            (
                "_test.go",
                "_test.js",
                "_test.py",
                "_test.rb",
                "_spec.rb",
                ".test.js",
                ".test.jsx",
                ".test.ts",
                ".test.tsx",
                ".spec.js",
                ".spec.jsx",
                ".spec.ts",
                ".spec.tsx",
            )
        )
    )


def load_large_file_baselines(
    repo: Path,
    baseline_file: str | None = DEFAULT_BASELINE_FILE,
    pre_pr_ref: str | None = None,
) -> tuple[dict[str, LargeFileBaseline], list[Finding]]:
    if not baseline_file:
        return {}, []
    path = repo / baseline_file
    if not path.exists():
        return {}, []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline_file,
                evidence=f"baseline file is unreadable: {exc}",
                recommendation="Fix or remove the codebase health baseline before relying on the gate.",
            )
        ]

    baselines: dict[str, LargeFileBaseline] = {}
    findings: list[Finding] = []
    for index, item in enumerate(raw.get("large_files", [])):
        entry_path = str(item.get("path", "")).strip()
        try:
            baseline = LargeFileBaseline(
                path=entry_path,
                current_lines=int(item["current_lines"]),
                target_lines=int(item["target_lines"]),
                reduce_by=int(item["reduce_by"]),
                expires_on=item.get("expires_on"),
                reason=str(item.get("reason", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=entry_path or f"{baseline_file}:large_files[{index}]",
                    evidence=f"invalid baseline entry: {exc}",
                    recommendation="Use path, current_lines, target_lines, reduce_by, and optional expires_on.",
                )
            )
            continue
        findings.extend(validate_large_file_baseline(baseline, repo, pre_pr_ref))
        baselines[baseline.path] = baseline
    return baselines, findings


def validate_large_file_baseline(
    baseline: LargeFileBaseline,
    repo: Path | None = None,
    pre_pr_ref: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not baseline.path:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path="<empty>",
                evidence="baseline path is empty",
                recommendation="Set a repository-relative path for each large file baseline.",
            )
        )
    if baseline.target_lines >= baseline.current_lines:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline.path or "<empty>",
                evidence=f"target_lines {baseline.target_lines} must be lower than current_lines {baseline.current_lines}",
                recommendation="Keep large file exceptions as a ratchet toward a smaller target.",
            )
        )
    if baseline.reduce_by <= 0:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline.path or "<empty>",
                evidence=f"reduce_by {baseline.reduce_by} must be positive",
                recommendation="Require a concrete reduction when a baseline file is touched.",
            )
        )
    if baseline.expires_on:
        try:
            expires_on = date.fromisoformat(baseline.expires_on)
        except ValueError:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=baseline.path or "<empty>",
                    evidence=f"expires_on is not YYYY-MM-DD: {baseline.expires_on}",
                    recommendation="Use an ISO date or remove expires_on.",
                )
            )
        else:
            if expires_on < date.today():
                findings.append(
                    Finding(
                        category="codebase_health_baseline",
                        severity="high",
                        path=baseline.path or "<empty>",
                        evidence=f"baseline expired on {baseline.expires_on}",
                        recommendation="Refresh the baseline only with a smaller current_lines target or split the file.",
                    )
                )
    if repo is not None and pre_pr_ref is not None and baseline.path:
        pre_pr_lines = measure_lines_at_ref(repo, pre_pr_ref, baseline.path)
        if pre_pr_lines is not None and baseline.current_lines > pre_pr_lines:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=baseline.path,
                    evidence=(
                        f"current_lines {baseline.current_lines} exceeds {pre_pr_lines} lines measured "
                        f"at pre-PR ref {pre_pr_ref}"
                    ),
                    recommendation=(
                        "Record current_lines from the pre-PR ref (merge-base with the base branch), "
                        "not a rebased working tree; a PR must not bake its own growth into the accepted baseline."
                    ),
                )
            )
    return findings


def large_file_finding_for_baseline(
    repo: Path,
    path: Path,
    lines: int,
    max_file_lines: int,
    baseline: LargeFileBaseline | None,
) -> Finding | None:
    path_name = rel(repo, path)
    if baseline is None:
        severity = "medium" if looks_like_test(repo, path) else "high"
        return Finding(
            category="large_file",
            severity=severity,
            path=path_name,
            evidence=f"{lines} lines > limit {max_file_lines}",
            recommendation="Do not add more behavior here without a split/refactor task or an explicit exception.",
        )
    if lines > baseline.current_lines:
        return Finding(
            category="large_file",
            severity="high" if not looks_like_test(repo, path) else "medium",
            path=path_name,
            evidence=f"{lines} lines > baseline current {baseline.current_lines}",
            recommendation="Reduce this file back to or below its accepted baseline before adding behavior.",
        )
    required_lines = max(baseline.target_lines, baseline.current_lines - baseline.reduce_by)
    if lines > required_lines:
        return Finding(
            category="large_file_baseline_reduction",
            severity="medium",
            path=path_name,
            evidence=f"{lines} lines; baseline expects <= {required_lines} lines this touch, target {baseline.target_lines}",
            recommendation="Prefer reducing this accepted legacy file before adding more behavior.",
        )
    return None


def collect_large_file_findings(
    repo: Path,
    files: Iterable[Path],
    max_file_lines: int,
    baselines: dict[str, LargeFileBaseline] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    baselines = baselines or {}
    for path in files:
        if path.suffix not in TEXT_EXTENSIONS or path.name in LOCKFILE_NAMES:
            continue
        lines = count_lines(path)
        if lines is None or lines <= max_file_lines:
            continue
        finding = large_file_finding_for_baseline(repo, path, lines, max_file_lines, baselines.get(rel(repo, path)))
        if finding is not None:
            findings.append(finding)
    return findings


def load_python_complexity_baselines(
    repo: Path,
    baseline_file: str | None = DEFAULT_BASELINE_FILE,
    pre_pr_ref: str | None = None,
) -> tuple[dict[tuple[str, str], PythonComplexityBaseline], list[Finding]]:
    if not baseline_file:
        return {}, []
    path = repo / baseline_file
    if not path.exists():
        return {}, []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline_file,
                evidence=f"baseline file is unreadable: {exc}",
                recommendation="Fix or remove the codebase health baseline before relying on the gate.",
            )
        ]

    baselines: dict[tuple[str, str], PythonComplexityBaseline] = {}
    findings: list[Finding] = []
    for index, item in enumerate(raw.get("python_complexity", [])):
        entry_path = str(item.get("path", "")).strip()
        entry_function = str(item.get("function", "")).strip()
        try:
            baseline = PythonComplexityBaseline(
                path=entry_path,
                function=entry_function,
                current_complexity=int(item["current_complexity"]),
                target_complexity=int(item["target_complexity"]),
                reduce_by=int(item["reduce_by"]),
                expires_on=item.get("expires_on"),
                reason=str(item.get("reason", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=entry_path or f"{baseline_file}:python_complexity[{index}]",
                    evidence=f"invalid baseline entry: {exc}",
                    recommendation="Use path, function, current_complexity, target_complexity, reduce_by, and optional expires_on.",
                )
            )
            continue
        findings.extend(validate_python_complexity_baseline(baseline, repo, pre_pr_ref))
        baselines[(baseline.path, baseline.function)] = baseline
    return baselines, findings


def validate_python_complexity_baseline(
    baseline: PythonComplexityBaseline,
    repo: Path | None = None,
    pre_pr_ref: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not baseline.path or not baseline.function:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline.path or "<empty>",
                evidence="baseline path or function is empty",
                recommendation="Set a repository-relative path and a function name for each complexity baseline.",
            )
        )
    if baseline.target_complexity >= baseline.current_complexity:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline.path or "<empty>",
                evidence=f"target_complexity {baseline.target_complexity} must be lower than current_complexity {baseline.current_complexity}",
                recommendation="Keep complexity exceptions as a ratchet toward a smaller target.",
            )
        )
    if baseline.reduce_by <= 0:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline.path or "<empty>",
                evidence=f"reduce_by {baseline.reduce_by} must be positive",
                recommendation="Require a concrete reduction when a baseline entry is touched.",
            )
        )
    if baseline.expires_on:
        try:
            expires_on = date.fromisoformat(baseline.expires_on)
        except ValueError:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=baseline.path or "<empty>",
                    evidence=f"expires_on is not YYYY-MM-DD: {baseline.expires_on}",
                    recommendation="Use an ISO date or remove expires_on.",
                )
            )
        else:
            if expires_on < date.today():
                findings.append(
                    Finding(
                        category="codebase_health_baseline",
                        severity="high",
                        path=baseline.path or "<empty>",
                        evidence=f"baseline expired on {baseline.expires_on}",
                        recommendation="Refresh the baseline only with a smaller current_complexity target, or split the function.",
                    )
                )
    if repo is not None and pre_pr_ref is not None and baseline.path and baseline.function:
        pre_pr_complexity = measure_python_complexity_at_ref(repo, pre_pr_ref, baseline.path, baseline.function)
        if pre_pr_complexity is not None and baseline.current_complexity > pre_pr_complexity:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=baseline.path,
                    evidence=(
                        f"{baseline.function} current_complexity {baseline.current_complexity} exceeds "
                        f"{pre_pr_complexity} measured at pre-PR ref {pre_pr_ref}"
                    ),
                    recommendation=(
                        "Record current_complexity from the pre-PR ref (merge-base with the base branch), "
                        "not a rebased working tree; a PR must not bake its own growth into the accepted baseline."
                    ),
                )
            )
    return findings


def python_complexity_finding_for_baseline(
    repo_path: str,
    function_name: str,
    complexity: int,
    is_test: bool,
    baseline: PythonComplexityBaseline | None,
) -> Finding | None:
    severity = "medium" if is_test else "high"
    if baseline is None:
        return Finding(
            category="python_cyclomatic_complexity",
            severity=severity,
            path=repo_path,
            evidence=f"{function_name} complexity {complexity} > limit {PYTHON_COMPLEXITY_LIMIT}",
            recommendation="Split branches or extract focused helpers before adding more behavior.",
        )
    if complexity > baseline.current_complexity:
        return Finding(
            category="python_cyclomatic_complexity",
            severity=severity,
            path=repo_path,
            evidence=f"{function_name} complexity {complexity} > baseline current {baseline.current_complexity}",
            recommendation="Reduce this function back to or below its accepted baseline before adding behavior.",
        )
    required_complexity = max(baseline.target_complexity, baseline.current_complexity - baseline.reduce_by)
    if complexity > required_complexity:
        return Finding(
            category="python_cyclomatic_complexity_baseline_reduction",
            severity="medium",
            path=repo_path,
            evidence=f"{function_name} complexity {complexity}; baseline expects <= {required_complexity} this touch, target {baseline.target_complexity}",
            recommendation="Prefer reducing this accepted legacy function before adding more behavior.",
        )
    return None


def load_python_function_count_baselines(
    repo: Path,
    baseline_file: str | None = DEFAULT_BASELINE_FILE,
    pre_pr_ref: str | None = None,
) -> tuple[dict[str, PythonFunctionCountBaseline], list[Finding]]:
    if not baseline_file:
        return {}, []
    path = repo / baseline_file
    if not path.exists():
        return {}, []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline_file,
                evidence=f"baseline file is unreadable: {exc}",
                recommendation="Fix or remove the codebase health baseline before relying on the gate.",
            )
        ]

    baselines: dict[str, PythonFunctionCountBaseline] = {}
    findings: list[Finding] = []
    for index, item in enumerate(raw.get("python_function_count", [])):
        entry_path = str(item.get("path", "")).strip()
        try:
            baseline = PythonFunctionCountBaseline(
                path=entry_path,
                current_count=int(item["current_count"]),
                target_count=int(item["target_count"]),
                reduce_by=int(item["reduce_by"]),
                expires_on=item.get("expires_on"),
                reason=str(item.get("reason", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=entry_path or f"{baseline_file}:python_function_count[{index}]",
                    evidence=f"invalid baseline entry: {exc}",
                    recommendation="Use path, current_count, target_count, reduce_by, and optional expires_on.",
                )
            )
            continue
        findings.extend(validate_python_function_count_baseline(baseline, repo, pre_pr_ref))
        baselines[baseline.path] = baseline
    return baselines, findings


def validate_python_function_count_baseline(
    baseline: PythonFunctionCountBaseline,
    repo: Path | None = None,
    pre_pr_ref: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not baseline.path:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path="<empty>",
                evidence="baseline path is empty",
                recommendation="Set a repository-relative path for each function count baseline.",
            )
        )
    if baseline.target_count >= baseline.current_count:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline.path or "<empty>",
                evidence=f"target_count {baseline.target_count} must be lower than current_count {baseline.current_count}",
                recommendation="Keep function count exceptions as a ratchet toward a smaller target.",
            )
        )
    if baseline.reduce_by <= 0:
        findings.append(
            Finding(
                category="codebase_health_baseline",
                severity="high",
                path=baseline.path or "<empty>",
                evidence=f"reduce_by {baseline.reduce_by} must be positive",
                recommendation="Require a concrete reduction when a baseline entry is touched.",
            )
        )
    if baseline.expires_on:
        try:
            expires_on = date.fromisoformat(baseline.expires_on)
        except ValueError:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=baseline.path or "<empty>",
                    evidence=f"expires_on is not YYYY-MM-DD: {baseline.expires_on}",
                    recommendation="Use an ISO date or remove expires_on.",
                )
            )
        else:
            if expires_on < date.today():
                findings.append(
                    Finding(
                        category="codebase_health_baseline",
                        severity="high",
                        path=baseline.path or "<empty>",
                        evidence=f"baseline expired on {baseline.expires_on}",
                        recommendation="Refresh the baseline only with a smaller current_count target, or split the file.",
                    )
                )
    if repo is not None and pre_pr_ref is not None and baseline.path:
        pre_pr_count = measure_python_function_count_at_ref(repo, pre_pr_ref, baseline.path)
        if pre_pr_count is not None and baseline.current_count > pre_pr_count:
            findings.append(
                Finding(
                    category="codebase_health_baseline",
                    severity="high",
                    path=baseline.path,
                    evidence=(
                        f"current_count {baseline.current_count} exceeds {pre_pr_count} functions measured "
                        f"at pre-PR ref {pre_pr_ref}"
                    ),
                    recommendation=(
                        "Record current_count from the pre-PR ref (merge-base with the base branch), "
                        "not a rebased working tree; a PR must not bake its own growth into the accepted baseline."
                    ),
                )
            )
    return findings


def python_function_count_finding_for_baseline(
    repo_path: str,
    function_count: int,
    is_test: bool,
    baseline: PythonFunctionCountBaseline | None,
) -> Finding | None:
    severity = "medium" if is_test else "high"
    if baseline is None:
        return Finding(
            category="python_function_count",
            severity=severity,
            path=repo_path,
            evidence=f"{function_count} functions > fail limit {PYTHON_FUNCTION_FAIL_LIMIT}",
            recommendation="Split responsibilities before adding more Python behavior to this file.",
        )
    if function_count > baseline.current_count:
        return Finding(
            category="python_function_count",
            severity=severity,
            path=repo_path,
            evidence=f"{function_count} functions > baseline current {baseline.current_count}",
            recommendation="Split responsibilities back to or below the accepted baseline before adding behavior.",
        )
    required_count = max(baseline.target_count, baseline.current_count - baseline.reduce_by)
    if function_count > required_count:
        return Finding(
            category="python_function_count_baseline_reduction",
            severity="medium",
            path=repo_path,
            evidence=f"{function_count} functions; baseline expects <= {required_count} this touch, target {baseline.target_count}",
            recommendation="Prefer reducing this accepted legacy module before adding more behavior.",
        )
    return None


def python_function_complexity(node: ast.AST) -> int:
    complexity = 1
    match_node = getattr(ast, "Match", None)
    nested_scope_nodes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

    def walk_current_scope(current: ast.AST):
        for child in ast.iter_child_nodes(current):
            if child is not node and isinstance(child, nested_scope_nodes):
                continue
            yield child
            yield from walk_current_scope(child)

    for child in walk_current_scope(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler)):
            complexity += 1
        elif match_node is not None and isinstance(child, match_node):
            complexity += len(getattr(child, "cases", []))
        elif isinstance(child, ast.BoolOp):
            complexity += max(0, len(child.values) - 1)
    return complexity


def collect_python_structure_findings(
    repo: Path,
    files: Iterable[Path],
    complexity_baselines: dict[tuple[str, str], PythonComplexityBaseline] | None = None,
    function_count_baselines: dict[str, PythonFunctionCountBaseline] | None = None,
) -> list[Finding]:
    complexity_baselines = complexity_baselines or {}
    function_count_baselines = function_count_baselines or {}
    findings: list[Finding] = []
    for path in files:
        if path.suffix != ".py" or path.name in LOCKFILE_NAMES or not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError):
            continue

        repo_path = rel(repo, path)
        is_test = looks_like_test(repo, path)
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        function_count = len(functions)
        if function_count > PYTHON_FUNCTION_FAIL_LIMIT:
            finding = python_function_count_finding_for_baseline(
                repo_path, function_count, is_test, function_count_baselines.get(repo_path)
            )
            if finding is not None:
                findings.append(finding)
        elif function_count > PYTHON_FUNCTION_WARN_LIMIT:
            findings.append(
                Finding(
                    category="python_function_count",
                    severity="medium",
                    path=repo_path,
                    evidence=f"{function_count} functions > warn limit {PYTHON_FUNCTION_WARN_LIMIT}",
                    recommendation="Watch for accretion and consider a focused split before this becomes blocking.",
                )
            )

        for function in functions:
            complexity = python_function_complexity(function)
            if complexity <= PYTHON_COMPLEXITY_LIMIT:
                continue
            finding = python_complexity_finding_for_baseline(
                repo_path,
                function.name,
                complexity,
                is_test,
                complexity_baselines.get((repo_path, function.name)),
            )
            if finding is not None:
                findings.append(finding)
    return findings


def names_by_directory(files: Iterable[Path]) -> dict[Path, set[str]]:
    result: dict[Path, set[str]] = {}
    for path in files:
        result.setdefault(path.parent, set()).add(path.name)
    return result


def dependency_manifest_for_path(path: Path, all_names_by_dir: dict[Path, set[str]]) -> tuple[Path, list[str]] | None:
    locks = LOCKFILES.get(path.name)
    if locks is not None:
        if not path.exists() or (path.name == "go.mod" and not go_mod_requires_sum(path)):
            return None
        return path, locks

    manifest_name = next(
        (
            manifest
            for manifest, lock_names in LOCKFILES.items()
            if path.name in lock_names and manifest in all_names_by_dir.get(path.parent, set())
        ),
        None,
    )
    if manifest_name is None:
        return None
    return path.parent / manifest_name, LOCKFILES[manifest_name]


def has_local_lock(manifest_path: Path, locks: list[str], all_names_by_dir: dict[Path, set[str]]) -> bool:
    return any(lock in all_names_by_dir.get(manifest_path.parent, set()) for lock in locks)


def has_covering_ancestor_lock(repo: Path, manifest_path: Path, locks: list[str], all_names_by_dir: dict[Path, set[str]]) -> bool:
    if manifest_path.name in LOCAL_LOCK_ONLY_MANIFESTS:
        return False
    return any(
        lock in all_names_by_dir.get(directory, set())
        for directory in manifest_path.parent.parents
        if (directory == repo or repo in directory.parents) and ancestor_lock_covers_manifest(repo, directory, manifest_path)
        for lock in locks
    )


def collect_dependency_findings(repo: Path, files: Iterable[Path] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    all_files = tracked_files(repo)
    scoped_files = list(files) if files is not None else all_files
    all_names_by_dir = names_by_directory(all_files)
    checked_manifests: set[Path] = set()
    for path in scoped_files:
        manifest = dependency_manifest_for_path(path, all_names_by_dir)
        if manifest is None:
            continue
        manifest_path, locks = manifest
        if manifest_path in checked_manifests:
            continue
        checked_manifests.add(manifest_path)
        if has_local_lock(manifest_path, locks, all_names_by_dir):
            continue
        if has_covering_ancestor_lock(repo, manifest_path, locks, all_names_by_dir):
            continue
        findings.append(
            Finding(
                category="missing_lockfile",
                severity="medium",
                path=rel(repo, manifest_path),
                evidence=f"{manifest_path.name} exists but none of {', '.join(locks)} exists in {rel(repo, manifest_path.parent)}",
                recommendation="Confirm the package/dependency management policy before adding dependencies.",
            )
        )
    return findings


def collect_repo_baseline_findings(repo: Path) -> list[Finding]:
    paths = [path.relative_to(repo) for path in tracked_files(repo)]
    path_names = {str(path) for path in paths}
    path_parts = {part.lower() for path in paths for part in path.parts}
    has_test_file = any(looks_like_test(repo, repo / path) for path in paths)
    findings: list[Finding] = []
    if not has_test_file and not ({"test", "tests", "spec", "__tests__"} & path_parts):
        findings.append(
            Finding(
                category="missing_tests_directory",
                severity="medium",
                path=".",
                evidence="No test/tests/spec/__tests__ path segment was found",
                recommendation="Identify the existing test convention or create a minimal test baseline before feature work.",
            )
        )
    has_ci = any(name.startswith(".github/workflows/") for name in path_names) or bool(path_names & CI_FILE_NAMES)
    if not has_ci:
        findings.append(
            Finding(
                category="missing_ci_workflow",
                severity="medium",
                path="ci",
                evidence="No common CI workflow file was found",
                recommendation="Confirm verification will run somewhere before treating PR checks as sufficient.",
            )
        )
    return findings


def build_report(
    repo: Path,
    mode: str,
    base_ref: str,
    max_file_lines: int,
    baseline_file: str | None = DEFAULT_BASELINE_FILE,
) -> dict:
    files = changed_files(repo, base_ref) if mode == "changed" else tracked_files(repo)
    pre_pr_ref = resolve_pre_pr_ref(repo, base_ref) if mode == "changed" else None
    large_file_baselines, baseline_findings = load_large_file_baselines(repo, baseline_file, pre_pr_ref)
    complexity_baselines, complexity_baseline_findings = load_python_complexity_baselines(repo, baseline_file, pre_pr_ref)
    function_count_baselines, function_count_baseline_findings = load_python_function_count_baselines(
        repo, baseline_file, pre_pr_ref
    )
    findings = [
        *baseline_findings,
        *complexity_baseline_findings,
        *function_count_baseline_findings,
        *collect_large_file_findings(repo, files, max_file_lines, large_file_baselines),
    ]
    findings.extend(collect_python_structure_findings(repo, files, complexity_baselines, function_count_baselines))
    findings.extend(collect_dependency_findings(repo, files if mode == "changed" else None))
    if mode == "survey":
        findings.extend(collect_repo_baseline_findings(repo))
    counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    recommended_tasks = []
    if any(f.category == "missing_lockfile" for f in findings):
        recommended_tasks.append("package/dependency management policy must be decided before dependency changes")
    if any(f.category == "large_file" and f.severity == "high" for f in findings):
        recommended_tasks.append("large touched modules need split/refactor guard before adding behavior")
    if any(f.category.startswith("python_") and f.severity == "high" for f in findings):
        recommended_tasks.append("Python accretion hotspots need split/refactor guard before adding behavior")
    if any(f.category.startswith("missing_") for f in findings):
        recommended_tasks.append("verification baseline must be explicit in requirements/design/HITL")
    return {
        "repo_root": str(repo),
        "mode": mode,
        "base_ref": base_ref if mode == "changed" else None,
        "max_file_lines": max_file_lines,
        "baseline_file": baseline_file,
        "summary": {"files_scanned": len(files), "finding_counts": counts},
        "findings": [asdict(finding) for finding in findings],
        "recommended_tasks": recommended_tasks,
    }


def render_markdown(report: dict) -> str:
    counts = report["summary"]["finding_counts"]
    lines = [
        "# GDD Codebase Health Survey",
        "",
        f"- Repo: `{report['repo_root']}`",
        f"- Mode: `{report['mode']}`",
        f"- Files scanned: {report['summary']['files_scanned']}",
        f"- Findings: high={counts.get('high', 0)}, medium={counts.get('medium', 0)}, low={counts.get('low', 0)}",
        "",
    ]
    if not report["findings"]:
        lines.append("No health findings.")
        return "\n".join(lines)
    lines.extend(["| Severity | Category | Path | Evidence | Recommendation |", "|---|---|---|---|---|"])
    for finding in report["findings"]:
        lines.append(
            "| {severity} | {category} | `{path}` | {evidence} | {recommendation} |".format(**finding)
        )
    if report["recommended_tasks"]:
        lines.extend(["", "## Recommended Planning Tasks"])
        lines.extend(f"- {task}" for task in report["recommended_tasks"])
    return "\n".join(lines)


def should_fail(report: dict, fail_on: str) -> bool:
    counts = report["summary"]["finding_counts"]
    if fail_on == "none":
        return False
    if fail_on == "high":
        return counts.get("high", 0) > 0
    return counts.get("high", 0) > 0 or counts.get("medium", 0) > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=os.getcwd(), help="Target repository/worktree root")
    parser.add_argument("--mode", choices=["survey", "changed"], default="survey")
    parser.add_argument("--base-ref", default="origin/main", help="Base ref for --mode changed")
    parser.add_argument("--max-file-lines", type=int, default=1500)
    parser.add_argument("--baseline-file", default=DEFAULT_BASELINE_FILE, help="Repo-relative JSON baseline file for accepted legacy large files")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--fail-on", choices=["none", "medium", "high"], default="none")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    if not repo.exists():
        print(f"repo root not found: {repo}", file=sys.stderr)
        return 2

    try:
        report = build_report(repo, args.mode, args.base_ref, args.max_file_lines, args.baseline_file)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))
    return 1 if should_fail(report, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
