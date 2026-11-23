"""`scripts/list-merge-triggered-workflows.py`（マージで起動する workflow の一覧）のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_list_merge_triggered_workflows.py -q`

git の fixture に workflow と変更を置き、script を subprocess で起動して、
workflow ごとの判定（起動する・起動しうる・起動しない）を突き合わせる。
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _git_fixture import init_repo
from _plugin_module_loader import load_plugin_module

SCRIPT = PLUGIN_ROOT / "scripts" / "list-merge-triggered-workflows.py"

RUNS = "起動する"
MAY = "起動しうる"
NO = "起動しない"

DEPLOY = """\
name: agentcore-deploy
on:
  push:
    branches: [main]
    paths:
      - 'src/review-bot/**'
  workflow_dispatch:
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "on: push"
"""


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _write(repo: Path, files: dict[str, str | bytes]) -> None:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")


def _parse(stdout: str) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for line in stdout.splitlines():
        status, path, reason = line.split("\t")
        result[Path(path).name] = (status, reason)
    return result


def _run(
    workflows: dict[str, str | bytes],
    changed: list[str],
    *,
    default_branch: str | None = "main",
) -> tuple[dict[str, tuple[str, str]], subprocess.CompletedProcess[str]]:
    """workflow を main に置き、`changed` を変えた branch で script を起動する。

    戻り値の dict は workflow のファイル名 → (判定, 理由)。
    """
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        init_repo(repo, branch="main")
        _write(repo, {f".github/workflows/{name}": text for name, text in workflows.items()})
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "workflows")
        _git(repo, "switch", "-q", "-c", "feature")
        _write(repo, {rel: "changed\n" for rel in changed})
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "--allow-empty", "-m", "change")
        args = ["python3", str(SCRIPT), "--repo", str(repo), "--base", "main"]
        if default_branch is not None:
            args += ["--default-branch", default_branch]
        proc = subprocess.run(args, capture_output=True, text=True)
    return _parse(proc.stdout), proc


def _status(workflow: str, changed: list[str], **kwargs: object) -> str:
    result, proc = _run({"w.yml": workflow}, changed, **kwargs)  # type: ignore[arg-type]
    assert proc.returncode == 0, proc.stderr
    return result["w.yml"][0]


class PathsOnlyTest(unittest.TestCase):
    def test_file_under_paths_triggers(self) -> None:
        result, proc = _run(
            {"agentcore-deploy.yaml": DEPLOY},
            ["docs/readme.md", "src/review-bot/guardrails.md"],
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        status, reason = result["agentcore-deploy.yaml"]
        self.assertEqual(status, RUNS)
        self.assertIn("src/review-bot/guardrails.md", reason)

    def test_file_outside_paths_does_not_trigger(self) -> None:
        result, _ = _run({"agentcore-deploy.yaml": DEPLOY}, ["docs/readme.md"])
        self.assertEqual(result["agentcore-deploy.yaml"][0], NO)

    def test_single_star_does_not_cross_slash(self) -> None:
        wf = "on:\n  push:\n    paths: ['*.md']\n"
        self.assertEqual(_status(wf, ["docs/a.md"]), NO)
        self.assertEqual(_status(wf, ["a.md"]), RUNS)

    def test_double_star_prefix_matches_root(self) -> None:
        wf = "on:\n  push:\n    paths:\n    - '**/docs/**'\n"
        self.assertEqual(_status(wf, ["docs/a.md"]), RUNS)
        self.assertEqual(_status(wf, ["x/docs/y/a.md"]), RUNS)
        self.assertEqual(_status(wf, ["xdocs/a.md"]), NO)

    def test_question_mark_makes_preceding_char_optional(self) -> None:
        wf = "on:\n  push:\n    paths: ['*.jsx?']\n"
        self.assertEqual(_status(wf, ["a.js"]), RUNS)
        self.assertEqual(_status(wf, ["a.jsx"]), RUNS)
        self.assertEqual(_status(wf, ["a.ts"]), NO)


class PathsIgnoreOnlyTest(unittest.TestCase):
    WF = "on:\n  push:\n    branches: [main]\n    paths-ignore:\n      - 'docs/**'\n      - '**.md'\n"

    def test_all_files_ignored_does_not_trigger(self) -> None:
        self.assertEqual(_status(self.WF, ["docs/a.txt", "README.md"]), NO)

    def test_one_file_not_ignored_triggers(self) -> None:
        self.assertEqual(_status(self.WF, ["docs/a.txt", "src/app.py"]), RUNS)


class NegationTest(unittest.TestCase):
    def test_later_negation_excludes(self) -> None:
        wf = "on:\n  push:\n    paths:\n      - '**.md'\n      - '!README.md'\n"
        self.assertEqual(_status(wf, ["README.md"]), NO)
        self.assertEqual(_status(wf, ["docs/a.md"]), RUNS)

    def test_later_positive_reincludes(self) -> None:
        wf = "on:\n  push:\n    paths:\n      - '**.md'\n      - '!README.md'\n      - 'README*'\n"
        self.assertEqual(_status(wf, ["README.md"]), RUNS)

    def test_only_negative_patterns_may_trigger(self) -> None:
        wf = "on:\n  push:\n    paths: ['!docs/**']\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_negation_in_paths_ignore_may_trigger(self) -> None:
        wf = "on:\n  push:\n    paths-ignore: ['docs/**', '!docs/keep.md']\n"
        self.assertEqual(_status(wf, ["docs/a.md"]), MAY)


class EventShapeTest(unittest.TestCase):
    def test_workflow_dispatch_only_does_not_trigger(self) -> None:
        wf = "on:\n  workflow_dispatch:\n    inputs:\n      env:\n        type: string\n"
        self.assertEqual(_status(wf, ["src/a.py"]), NO)

    def test_pull_request_only_does_not_trigger(self) -> None:
        wf = "on:\n  pull_request:\n    paths: ['**']\n"
        self.assertEqual(_status(wf, ["src/a.py"]), NO)

    def test_scalar_push_triggers(self) -> None:
        self.assertEqual(_status("on: push\n", ["src/a.py"]), RUNS)

    def test_list_with_push_triggers(self) -> None:
        self.assertEqual(_status("on: [push, pull_request]\n", ["src/a.py"]), RUNS)

    def test_push_without_filters_triggers(self) -> None:
        self.assertEqual(_status("on:\n  push:\n  pull_request:\n", ["src/a.py"]), RUNS)

    def test_quoted_on_key(self) -> None:
        wf = '"on":\n  push:\n    paths: [\'src/**\']  # deploy\n'
        self.assertEqual(_status(wf, ["src/a.py"]), RUNS)
        self.assertEqual(_status(wf, ["docs/a.md"]), NO)

    def test_yaml_and_yml_extensions_are_both_read(self) -> None:
        result, proc = _run({"a.yml": "on: push\n", "b.yaml": "on: push\n"}, ["x"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(result["a.yml"][0], RUNS)
        self.assertEqual(result["b.yaml"][0], RUNS)


class BranchFilterTest(unittest.TestCase):
    def test_other_branch_does_not_trigger(self) -> None:
        wf = "on:\n  push:\n    branches: [develop]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), NO)

    def test_branch_glob_matches_default(self) -> None:
        wf = "on:\n  push:\n    branches: ['ma*']\n"
        self.assertEqual(_status(wf, ["src/a.py"]), RUNS)

    def test_branches_ignore_default_does_not_trigger(self) -> None:
        wf = "on:\n  push:\n    branches-ignore: [main]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), NO)

    def test_tags_only_does_not_trigger(self) -> None:
        wf = "on:\n  push:\n    tags: ['v*']\n"
        self.assertEqual(_status(wf, ["src/a.py"]), NO)

    def test_unknown_default_branch_may_trigger(self) -> None:
        wf = "on:\n  push:\n    branches: [main]\n"
        self.assertEqual(_status(wf, ["src/a.py"], default_branch=None), MAY)


class UndecidableTest(unittest.TestCase):
    def test_paths_and_paths_ignore_together_may_trigger(self) -> None:
        wf = "on:\n  push:\n    paths: ['src/**']\n    paths-ignore: ['docs/**']\n"
        self.assertEqual(_status(wf, ["docs/a.md"]), MAY)

    def test_branches_and_branches_ignore_together_may_trigger(self) -> None:
        wf = "on:\n  push:\n    branches: [main]\n    branches-ignore: [dev]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_flow_mapping_may_trigger(self) -> None:
        wf = "on: {push: {paths: ['src/**']}}\n"
        self.assertEqual(_status(wf, ["docs/a.md"]), MAY)

    def test_anchor_may_trigger(self) -> None:
        wf = "on:\n  push:\n    paths: &p\n      - 'src/**'\n"
        self.assertEqual(_status(wf, ["docs/a.md"]), MAY)

    def test_missing_on_may_trigger(self) -> None:
        self.assertEqual(_status("name: x\njobs: {}\n", ["docs/a.md"]), MAY)

    def test_bad_base_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo, branch="main")
            proc = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo), "--base", "no-such-ref"],
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")



class PatternTest(unittest.TestCase):
    def test_plus_and_bracket(self) -> None:
        wf = "on:\n  push:\n    paths: ['v[12].[0-9]+.md']\n"
        self.assertEqual(_status(wf, ["v1.42.md"]), RUNS)
        self.assertEqual(_status(wf, ["v3.4.md"]), NO)
        self.assertEqual(_status(wf, ["v1..md"]), NO)

    def test_backslash_escapes_star(self) -> None:
        wf = "on:\n  push:\n    paths: ['a\\*b']\n"
        self.assertEqual(_status(wf, ["a*b"]), RUNS)
        self.assertEqual(_status(wf, ["axb"]), NO)

    def test_reversed_bracket_range_may_trigger(self) -> None:
        wf = "on:\n  push:\n    paths: ['v[9-0]']\n"
        self.assertEqual(_status(wf, ["v1"]), MAY)

    def test_non_ascii_path_triggers(self) -> None:
        wf = "on:\n  push:\n    paths: ['agent-runtime/**']\n"
        self.assertEqual(_status(wf, ["agent-runtime/ガードレール.md"]), RUNS)

    def test_quote_inside_unquoted_value_may_trigger(self) -> None:
        wf = "on:\n  push:\n    paths: [it's/**, src/**]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_branches_ignore_negation_may_trigger(self) -> None:
        wf = "on:\n  push:\n    branches-ignore: ['release/**', '!release/x']\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_only_negative_branches_may_trigger(self) -> None:
        wf = "on:\n  push:\n    branches: ['!release/**']\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_diff_over_limit_may_trigger(self) -> None:
        module = load_plugin_module("scripts/list-merge-triggered-workflows.py")
        wf = "on:\n  push:\n    paths: ['src/**']\n"
        files = [f"src/{n}.py" for n in range(3001)]
        self.assertEqual(module.judge(wf, files, "main")[0], MAY)
        self.assertEqual(module.judge(wf, files[:3000], "main")[0], RUNS)


class OtherEventTest(unittest.TestCase):
    def test_pull_request_closed_may_trigger(self) -> None:
        wf = "on:\n  pull_request:\n    types: [closed]\n    branches: [main]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_workflow_run_may_trigger(self) -> None:
        wf = "on:\n  workflow_run:\n    workflows: [ci]\n    types: [completed]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_schedule_and_dispatch_do_not_trigger(self) -> None:
        wf = "on:\n  schedule:\n    - cron: '0 0 * * *'\n  workflow_dispatch:\n"
        self.assertEqual(_status(wf, ["src/a.py"]), NO)

    def test_unreadable_non_push_section_does_not_hide_push_absence(self) -> None:
        wf = (
            "on:\n  workflow_dispatch:\n    inputs:\n      env:\n"
            "        description: |\n          it's the target\n          # not a comment\n"
        )
        self.assertEqual(_status(wf, ["src/a.py"]), NO)

    def test_push_wins_over_undecidable_event(self) -> None:
        wf = "on:\n  push:\n  workflow_run:\n    workflows: [ci]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), RUNS)


class InputTest(unittest.TestCase):
    def test_empty_diff_may_trigger(self) -> None:
        self.assertEqual(_status("on: push\n", []), MAY)

    def test_non_utf8_workflow_may_trigger(self) -> None:
        result, proc = _run({"bad.yml": b"on: push\nname: \xff\n", "ok.yml": "on: push\n"}, ["x"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(result["bad.yml"][0], MAY)
        self.assertEqual(result["ok.yml"][0], RUNS)

    def test_head_merge_commit_reads_its_diff_and_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo, branch="main")
            _git(repo, "switch", "-q", "-c", "feature")
            _write(repo, {
                ".github/workflows/deploy.yml": DEPLOY,
                "src/review-bot/guardrails.md": "x\n",
            })
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "change")
            _git(repo, "switch", "-q", "main")
            _git(repo, "merge", "-q", "--no-ff", "-m", "merge", "feature")
            merge = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            # 作業ツリーは merge 前の main に戻す。head の commit から読むことを確かめる
            _git(repo, "switch", "-q", "--detach", f"{merge}^1")
            proc = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo), "--base", f"{merge}^1",
                 "--head", merge, "--default-branch", "main"],
                capture_output=True, text=True,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_parse(proc.stdout)["deploy.yml"][0], RUNS)


class FollowupTest(unittest.TestCase):
    def test_issues_closed_may_trigger(self) -> None:
        self.assertEqual(_status("on:\n  issues:\n    types: [closed]\n", ["a"]), MAY)

    def test_issues_without_types_may_trigger(self) -> None:
        self.assertEqual(_status("on:\n  issues:\n", ["a"]), MAY)

    def test_issues_without_closed_does_not_trigger(self) -> None:
        self.assertEqual(_status("on:\n  issues:\n    types: [opened, labeled]\n", ["a"]), NO)

    def test_merge_group_may_trigger(self) -> None:
        self.assertEqual(_status("on:\n  merge_group:\n", ["a"]), MAY)

    def test_two_mid_value_quotes_may_trigger(self) -> None:
        wf = "on:\n  push:\n    paths: [it's/**, src/**, x's/**]\n"
        self.assertEqual(_status(wf, ["src/a.py"]), MAY)

    def test_paths_ignore_over_limit_may_trigger(self) -> None:
        module = load_plugin_module("scripts/list-merge-triggered-workflows.py")
        wf = "on:\n  push:\n    paths-ignore: ['docs/**']\n"
        files = [f"src/{n}.py" for n in range(3001)]
        self.assertEqual(module.judge(wf, files, "main")[0], MAY)

    def test_branches_ignore_with_unknown_default_may_trigger(self) -> None:
        module = load_plugin_module("scripts/list-merge-triggered-workflows.py")
        wf = "on:\n  push:\n    branches-ignore: [dev]\n"
        self.assertEqual(module.judge(wf, ["src/a.py"], None)[0], MAY)

    def test_non_utf8_path_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo, branch="main")
            _write(repo, {".github/workflows/w.yml": "on:\n  push:\n    paths: ['**']\n"})
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "workflows")
            _git(repo, "switch", "-q", "-c", "feature")
            oid = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "-w", "--stdin"],
                input=b"x\n", check=True, capture_output=True,
            ).stdout.decode().strip()
            subprocess.run(
                [b"git", b"-C", str(repo).encode(), b"update-index", b"--add",
                 b"--cacheinfo", f"100644,{oid},".encode() + b"bad\xff.md"],
                check=True, capture_output=True,
            )
            _git(repo, "commit", "-q", "-m", "bad name")
            proc = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo), "--base", "main", "--default-branch", "main"],
                capture_output=True,
                env={**os.environ, "PYTHONIOENCODING": "utf-8:strict"},
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("起動する\t.github/workflows/w.yml\t".encode()))

    def test_non_utf8_workflow_path_is_written_as_original_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo, branch="main")
            oid = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "-w", "--stdin"],
                input=b"on:\n  push:\n    paths: ['**']\n", check=True, capture_output=True,
            ).stdout.decode().strip()
            subprocess.run(
                [b"git", b"-C", str(repo).encode(), b"update-index", b"--add",
                 b"--cacheinfo", f"100644,{oid},".encode() + b".github/workflows/bad\xff.yml"],
                check=True, capture_output=True,
            )
            _git(repo, "commit", "-q", "-m", "workflows")
            # 作業ツリーに無いファイルなので add -A を使わない（削除として stage される）
            _git(repo, "commit", "-q", "--allow-empty", "-m", "change")
            proc = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo), "--base", "HEAD^", "--default-branch", "main"],
                capture_output=True,
                env={**os.environ, "PYTHONIOENCODING": "utf-8:strict"},
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(b"\t.github/workflows/bad\xff.yml\t", proc.stdout)

    def test_issues_without_types_reason_does_not_claim_closed_in_types(self) -> None:
        module = load_plugin_module("scripts/list-merge-triggered-workflows.py")
        status, reason = module.judge("on:\n  issues:\n", ["a"], "main")
        self.assertEqual(status, MAY)
        self.assertNotIn("types に closed がある", reason)

    def test_empty_types_may_trigger(self) -> None:
        self.assertEqual(_status("on:\n  issues:\n    types: []\n", ["a"]), MAY)
        self.assertEqual(_status("on:\n  pull_request:\n    types: []\n", ["a"]), MAY)


def _merge_with_repo(tmp: str, *, main_files: dict[str, str], feature_files: dict[str, str],
                     main_rm: list[str] = (), feature_rm: list[str] = (),
                     start: dict[str, str] | None = None) -> Path:
    """main と feature が分かれた repo を作り、feature を checkout した状態で返す。"""
    repo = Path(tmp)
    init_repo(repo, branch="main")
    if start:
        _write(repo, start)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "start")
    _git(repo, "switch", "-q", "-c", "feature")
    _write(repo, feature_files)
    for rel in feature_rm:
        _git(repo, "rm", "-q", rel)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "feature")
    _git(repo, "switch", "-q", "main")
    _write(repo, main_files)
    for rel in main_rm:
        _git(repo, "rm", "-q", rel)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "main")
    _git(repo, "switch", "-q", "feature")
    return repo


def _merge_with(repo: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), "--repo", str(repo), "--base", "main", "--default-branch", "main", *extra],
        capture_output=True, text=True,
    )


class MergeWithTest(unittest.TestCase):
    GUARD = {"src/review-bot/guardrails.md": "x\n"}

    def test_reads_workflows_added_on_default_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _merge_with_repo(tmp, main_files={".github/workflows/deploy.yml": DEPLOY},
                                    feature_files=self.GUARD)
            without = _merge_with(repo)
            merged = _merge_with(repo, "--merge-with", "main")
        self.assertEqual(without.returncode, 0, without.stderr)
        self.assertNotIn("deploy.yml", without.stdout)
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(_parse(merged.stdout)["deploy.yml"][0], RUNS)

    def test_reads_workflow_changed_only_by_the_pr_from_head(self) -> None:
        wide = DEPLOY.replace("'src/review-bot/**'", "'**'")
        with tempfile.TemporaryDirectory() as tmp:
            repo = _merge_with_repo(tmp, start={".github/workflows/deploy.yml": DEPLOY},
                                    main_files={"other.md": "x\n"},
                                    feature_files={".github/workflows/deploy.yml": wide, "docs/a.md": "x\n"})
            proc = _merge_with(repo, "--merge-with", "main")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_parse(proc.stdout)["deploy.yml"][0], RUNS)

    def test_reads_workflow_changed_only_on_default_branch_from_it(self) -> None:
        narrow = DEPLOY.replace("'src/review-bot/**'", "'src/**'")
        with tempfile.TemporaryDirectory() as tmp:
            repo = _merge_with_repo(tmp, start={".github/workflows/deploy.yml": narrow},
                                    main_files={".github/workflows/deploy.yml": DEPLOY},
                                    feature_files=self.GUARD)
            proc = _merge_with(repo, "--merge-with", "main")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_parse(proc.stdout)["deploy.yml"][0], RUNS)

    def test_workflow_changed_on_both_sides_may_trigger(self) -> None:
        narrow = DEPLOY.replace("'src/review-bot/**'", "'src/**'")
        other = DEPLOY.replace("'src/review-bot/**'", "'lib/**'")
        with tempfile.TemporaryDirectory() as tmp:
            repo = _merge_with_repo(tmp, start={".github/workflows/deploy.yml": DEPLOY},
                                    main_files={".github/workflows/deploy.yml": narrow},
                                    feature_files={".github/workflows/deploy.yml": other})
            proc = _merge_with(repo, "--merge-with", "main")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_parse(proc.stdout)["deploy.yml"][0], MAY)

    def test_workflow_deleted_on_either_side_is_not_listed(self) -> None:
        start = {".github/workflows/a.yml": DEPLOY, ".github/workflows/b.yml": DEPLOY}
        with tempfile.TemporaryDirectory() as tmp:
            repo = _merge_with_repo(tmp, start=start, main_files={}, feature_files=self.GUARD,
                                    main_rm=[".github/workflows/a.yml"],
                                    feature_rm=[".github/workflows/b.yml"])
            proc = _merge_with(repo, "--merge-with", "main")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_unresolvable_merge_with_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _merge_with_repo(tmp, main_files={}, feature_files=self.GUARD)
            for ref in ("no-such-ref", ""):
                proc = _merge_with(repo, "--merge-with", ref)
                self.assertEqual(proc.returncode, 2, ref)
                self.assertEqual(proc.stdout, "", ref)

if __name__ == "__main__":
    unittest.main()
