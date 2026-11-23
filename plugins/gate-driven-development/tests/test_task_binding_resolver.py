from __future__ import annotations

import subprocess
import tempfile
import sys
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import load_plugin_module
from _git_fixture import init_repo



def load_module():
    return load_plugin_module("scripts/gdd_task_binding.py")


class TestTaskBindingResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_module()

    def _init_repo(self, root: Path) -> None:
        init_repo(root)

    def _make_worktree(self, repo: Path, path: Path, branch: str) -> None:
        subprocess.run(["git", "worktree", "add", "-q", "-b", branch, str(path)], cwd=repo, check=True)

    def _write_state(self, steering_dir: Path, task_id: str, goal: str, branch: str, worktree: Path) -> Path:
        steering = steering_dir / task_id
        steering.mkdir(parents=True, exist_ok=True)
        state = steering / "state.md"
        state.write_text(
            "\n".join(
                [
                    f"Task ID: {task_id}",
                    "Task Size: standard",
                    "Status: build",
                    "Started At: 2026-06-05T00:00:00Z",
                    f"Worktree: {worktree}",
                    f"Branch: {branch}",
                    "",
                    "## Approved Direction",
                    f"- 承認内容: {goal}",
                    "",
                    "## Gate Status",
                    "- Requirements Review Status: approved | evidence: fixture",
                    "- Design Review Status: approved | evidence: fixture",
                    "- Human Check Status: approved | evidence: fixture",
                    "- Route In Progress: none",
                    "- Resume From: gdd-test-driven-development",
                    "- Next Action: gdd-test-driven-development",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return state

    def test_natural_language_status_uses_registry_and_does_not_adopt_stale_root_steering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)

            metrics_wt = Path(tmp) / "metrics-worktree"
            self._make_worktree(repo, metrics_wt, "codex/20260605-example-upload-task")
            metrics_state = self._write_state(
                metrics_wt / ".steering",
                "20260605-example-upload-task",
                "メトリクス画像が貼り付けられない調査・修正",
                "codex/20260605-example-upload-task",
                metrics_wt,
            )

            stale_state = self._write_state(
                repo / ".steering",
                "20260601-example-review-task",
                "PRレビュー senior reading",
                "codex/20260601-example-review-task",
                Path(tmp) / "missing-pr-review-worktree",
            )

            self.mod.upsert_binding_from_state(repo, metrics_state)

            result = self.mod.resolve_task(
                repo_root=repo,
                cwd=metrics_wt,
                current_branch="codex/20260605-example-upload-task",
                latest_user_text="今の状況を確認したい",
            )

            self.assertEqual(result["status"], "resolved")
            self.assertEqual(result["task_id"], "20260605-example-upload-task")
            self.assertNotEqual(result["task_id"], "20260601-example-review-task")
            self.assertIn("legacy_root_steering_ignored", result["warnings"])
            self.assertIn(str(stale_state.parent), result["diagnostic_candidates"])

    def test_stale_local_state_does_not_override_matching_registry_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)

            metrics_wt = Path(tmp) / "metrics-worktree"
            self._make_worktree(repo, metrics_wt, "codex/20260605-example-upload-task")
            metrics_state = self._write_state(
                metrics_wt / ".steering",
                "20260605-example-upload-task",
                "メトリクス画像が貼り付けられない調査・修正",
                "codex/20260605-example-upload-task",
                metrics_wt,
            )
            self.mod.upsert_binding_from_state(repo, metrics_state)

            local_state = repo / ".claude" / "gdd-dev.local.md"
            local_state.parent.mkdir(parents=True, exist_ok=True)
            local_state.write_text(
                "---\n"
                "active: true\n"
                "task_id: 20260601-example-review-task\n"
                "branch: codex/20260601-example-review-task\n"
                "worktree: /tmp/missing-pr-review-worktree\n"
                "---\n",
                encoding="utf-8",
            )

            result = self.mod.resolve_task(
                repo_root=repo,
                cwd=metrics_wt,
                current_branch="codex/20260605-example-upload-task",
                local_state_path=local_state,
                latest_user_text="続きで再開して",
            )

            self.assertEqual(result["status"], "resolved")
            self.assertEqual(result["task_id"], "20260605-example-upload-task")
            self.assertIn("local_state_mismatch_ignored", result["warnings"])

    def test_branch_match_alone_is_not_enough_to_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            current = Path(tmp) / "current"
            self._make_worktree(repo, current, "codex/shared-branch")

            other_state = self._write_state(
                repo / ".steering",
                "20260601-example-review-task",
                "PRレビュー senior reading",
                "codex/shared-branch",
                Path(tmp) / "other-worktree",
            )
            self.mod.upsert_binding_from_state(repo, other_state)

            result = self.mod.resolve_task(
                repo_root=repo,
                cwd=current,
                current_branch="codex/shared-branch",
                latest_user_text="今どこ？",
            )

            self.assertEqual(result["status"], "conflict")
            self.assertIn("no_current_worktree_binding", result["warnings"])

    def test_conflict_reports_stale_binding_and_empty_local_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)

            stale_state = self._write_state(
                repo / ".steering",
                "20260614-merged-followup",
                "merged task with missing worktree",
                "gdd/20260614-merged-followup",
                Path(tmp) / "deleted-gdd-worktree",
            )
            self.mod.upsert_binding_from_state(repo, stale_state)

            local_state = repo / ".claude" / "gdd-dev.local.md"
            local_state.parent.mkdir(parents=True, exist_ok=True)
            local_state.write_text(
                "---\n"
                "active: true\n"
                "session_id:\n"
                "---\n",
                encoding="utf-8",
            )

            result = self.mod.resolve_task(
                repo_root=repo,
                cwd=repo,
                current_branch="main",
                local_state_path=local_state,
                latest_user_text="gdd-status",
            )

            self.assertEqual(result["status"], "conflict")
            self.assertIn("no_current_worktree_binding", result["warnings"])
            self.assertIn("stale_binding_missing_worktree", result["warnings"])
            self.assertIn("invalid_empty_local_session_id", result["warnings"])
            self.assertEqual(
                result["invalid_bindings"],
                [
                    {
                        "task_id": "20260614-merged-followup",
                        "reason": "missing_worktree_path",
                        "worktree_path": str((Path(tmp) / "deleted-gdd-worktree").resolve(strict=False)),
                    }
                ],
            )

    def test_frontmatter_value_of_three_hyphens_does_not_hide_empty_local_session_id_warning(self) -> None:
        # 独立レビュー round 9/10 で `hooks/scripts/lib/state_io.py::parse_state()` と
        # `scripts/resolve-gdd-model.py::extract_frontmatter_value()`/
        # `read_text_from_state()` に見つかった同型の fail-open（frontmatter 終端を
        # 部分文字列一致 `text.split("---\n", 2)` で判定しており、値がちょうど
        # `"---"` になる行があるとそこを終端と誤認してそれより後ろの key を丸ごと
        # 読み落とす）の第 3 の実装が `_frontmatter()` にも残っていた。`--local-state-path`
        # 経由で `skills/gdd-status/SKILL.md` から実際に到達する（`.claude/gdd-dev.local.md`
        # を渡す）ため、`active`/`session_id` より前にちょうど `"---"` で終わる
        # frontmatter 行があると、`active == "true"` かつ `session_id` が空という
        # 本来警告すべき状態が `local.get("active")` の欠落（None）で判定不能になり
        # `invalid_empty_local_session_id` 警告が出なくなる。DRY・一貫性のため
        # `state_io.py::parse_state()` と対称の line-exact 判定へこの PR で合わせて直す。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)

            local_state = repo / ".claude" / "gdd-dev.local.md"
            local_state.parent.mkdir(parents=True, exist_ok=True)
            local_state.write_text(
                "---\n"
                "some_legacy_field: ---\n"
                "active: true\n"
                "session_id:\n"
                "---\n",
                encoding="utf-8",
            )

            result = self.mod.resolve_task(
                repo_root=repo,
                cwd=repo,
                current_branch="main",
                local_state_path=local_state,
                latest_user_text="gdd-status",
            )

            self.assertIn("invalid_empty_local_session_id", result["warnings"])


class TestStateFieldParsing(unittest.TestCase):
    """`state.md` の書き手が使う表記ゆれを読み手が受け入れることを固定する。

    `.steering/` 配下への書き込みは PreToolUse hook がローカル絶対パス
    (`/Users/...`) を deny するため、state.md 側は `~` 表記になる。
    バッククォート囲みも Markdown として自然な書き方であり、
    どちらも parser 側で吸収しなければ silent failure になる。
    """

    def setUp(self) -> None:
        self.mod = load_module()

    def _upsert(self, tmp: Path, worktree_line: str, branch_line: str = "Branch: gdd/sample") -> dict:
        repo = tmp / "repo"
        steering = repo / ".steering" / "20260616-sample"
        steering.mkdir(parents=True, exist_ok=True)
        state = steering / "state.md"
        state.write_text(
            "\n".join(
                [
                    "Task ID: 20260616-sample",
                    worktree_line,
                    branch_line,
                    "",
                    "## Approved Direction",
                    "- 承認内容: sample",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return self.mod.upsert_binding_from_state(repo, state)

    def test_backticked_tilde_worktree_is_expanded_to_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = self._upsert(Path(tmp), "- Worktree: `~/gdd-wt/sample`")
        self.assertEqual(
            data["worktree_path"],
            str((Path.home() / "gdd-wt" / "sample").resolve(strict=False)),
        )

    def test_bare_tilde_worktree_is_expanded_to_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = self._upsert(Path(tmp), "- Worktree: ~/gdd-wt/sample")
        self.assertEqual(
            data["worktree_path"],
            str((Path.home() / "gdd-wt" / "sample").resolve(strict=False)),
        )

    def test_backticked_absolute_worktree_stays_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = self._upsert(Path(tmp), "- Worktree: `/abs/path/sample`")
        self.assertEqual(data["worktree_path"], "/abs/path/sample")

    def test_backticked_branch_value_drops_backticks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = self._upsert(
                Path(tmp),
                "- Worktree: `/abs/path/sample`",
                branch_line="- Branch: `gdd/20260616-sample`",
            )
        self.assertEqual(data["branch"], "gdd/20260616-sample")

    def test_field_strips_backticks_only_from_the_value(self) -> None:
        text = "- Worktree: `~/gdd-wt/sample`\n- Branch: `gdd/sample`\n"
        self.assertEqual(self.mod._field(text, "Worktree"), "~/gdd-wt/sample")
        self.assertEqual(self.mod._field(text, "Branch"), "gdd/sample")


if __name__ == "__main__":
    unittest.main()
