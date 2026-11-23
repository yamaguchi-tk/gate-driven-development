"""`scripts/check-gate-ledger.sh`（push・PR の前の帳簿の検算）のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_check_gate_ledger.py -q`

帳簿（state.md・tasklist.md）に変異を入れ、pre-PR gate・pre-push gate の hook の
不足の通知 / 通過と、検算スクリプトの行の状態を突き合わせる。検算スクリプトが hook と
違う判定をすると、「検算は通ったのに hook に不足として通知される」（またはその逆）になる。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _git_fixture import init_repo
from _locale_support import euc_jp_locale_env

SCRIPT = PLUGIN_ROOT / "scripts" / "check-gate-ledger.sh"
PRE_PR_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-pr-gate-hook.sh"
PRE_PUSH_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-push-gate-hook.sh"
SLUG = "20261002-ledger"
NOT_OK = {"missing", "invalid"}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _self_review(sha: str, *, dry: str = "yes", clean: str = "1") -> str:
    return (
        f"{sha} | rounds: 2 | consecutive_clean: {clean} | dry: {dry} "
        "| lanes: internal=2,grounding=not_applicable(no-external-dep),adversarial=1 "
        "| at: 2026-10-02T00:00:00Z"
    )


def _independent_review(sha: str, *, high: str = "0", blocking: str = "0") -> str:
    return (
        f"{sha} | reviewer: light-lane-independent-reviewer | context: diff-only "
        f"| high: {high} | medium: 0 | blocking: {blocking} | at: 2026-10-02T00:00:00Z"
    )


class GateLedgerFixture:
    """全行がそろった standard の steering を作り、変異を入れて hook とスクリプトを走らせる。"""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = root / "repo"
        self.repo.mkdir()
        init_repo(self.repo, branch="main")
        _git(self.repo, "switch", "-q", "-c", "feature")
        (self.repo / "file.txt").write_text("1\n", encoding="utf-8")
        _git(self.repo, "add", "file.txt")
        _git(self.repo, "commit", "-q", "-m", "one")
        self.old = _git(self.repo, "rev-parse", "HEAD")
        (self.repo / "file.txt").write_text("2\n", encoding="utf-8")
        _git(self.repo, "commit", "-q", "-am", "two")
        self.head = _git(self.repo, "rev-parse", "HEAD")
        claude = self.repo / ".claude"
        claude.mkdir()
        (claude / "gdd-dev.local.md").write_text(
            "---\nactive: true\nsession_id: test-session\n---\n", encoding="utf-8"
        )
        self.steering = self.repo / ".steering" / SLUG
        self.steering.mkdir(parents=True)
        self.state = {
            "Resume From": "done",
            "Human Check Status": "approved",
            "Route In Progress": "none",
            "Task Size": "standard",
            "ADR distilled": "not_applicable",
            "ADR distillation reason": "重要判断なし",
            "Pre-PR Self Review": _self_review(self.head),
            "Pre-Push Self Review": _self_review(self.head),
            "Independent Review": _independent_review(self.head),
        }
        self.next_action = "done"
        self.reviewed_by = "- Reviewed by: gdd-implementation-reviewer"
        self.extra_env: dict[str, str] = {}
        # Independent Review 行と同じ sha の、指摘 0 件の IR 節（references/finding-dispositions.md）
        self.review_findings = True

    def write(self) -> None:
        self.steering.joinpath("state.md").write_text(
            "".join(f"{k}: {v}\n" for k, v in self.state.items() if v is not None),
            encoding="utf-8",
        )
        ir = self.state.get("Independent Review")
        if ir and self.review_findings:
            self.steering.joinpath("review-findings.md").write_text(
                f"# Review Findings\n\n## IR1 | sha: {ir.split('|', 1)[0].strip()} | findings: 0\n\n"
                "| id | severity | category | file:line | 行き先 | 検証 | 根拠 |\n|---|---|---|---|---|---|---|\n",
                encoding="utf-8",
            )
        reviewed = f"{self.reviewed_by}\n" if self.reviewed_by else ""
        self.steering.joinpath("tasklist.md").write_text(
            f"# Task List\n\nNext Action: {self.next_action}\n\n"
            "## Current Task\n\n- なし\n\n## Pending Tasks\n\n- なし\n\n"
            "## Completed Tasks\n\n### Task 1: 一つ目\n\n- Commit: x\n"
            f"{reviewed}\n## Verification\n",
            encoding="utf-8",
        )

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(self.extra_env)
        env.update({
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
            "GDD_HOOK_STATE_DIR": str(self.root / "hookstate"),
        })
        return env

    def _hook_blocks(self, hook: Path, command: str) -> bool:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        result = subprocess.run(
            ["bash", str(hook)], cwd=self.repo, input=json.dumps(payload),
            capture_output=True, text=True, env=self._env(), check=False,
        )
        assert result.returncode == 0, result.stderr
        return '"hookEventName": "PreToolUse"' in result.stdout

    def pre_pr_blocks(self) -> bool:
        return self._hook_blocks(PRE_PR_HOOK, "gh pr create --title t --body x")

    def pre_push_blocks(self) -> bool:
        return self._hook_blocks(PRE_PUSH_HOOK, "git push -u origin feature")

    def ledger(self, *args: str, cwd: Path | None = None) -> tuple[int, list[tuple[str, str, str, str]]]:
        result = subprocess.run(
            ["bash", str(SCRIPT), *args], cwd=cwd or self.repo,
            capture_output=True, text=True, env=self._env(), check=False,
        )
        rows = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            assert len(parts) == 4, line
            rows.append((parts[0], parts[1], parts[2], parts[3]))
        assert rows, result.stdout + result.stderr
        return result.returncode, rows


def _status(rows, requirement: str) -> list[str]:
    return [status for status, req, _gate, _detail in rows if req == requirement]


def _gate_fails(rows, gate: str) -> bool:
    return any(status in NOT_OK and gate in gates.split(",") for status, _req, gates, _d in rows)


class CheckGateLedgerTests(unittest.TestCase):
    def _run(self, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            mutate(fx)
            fx.write()
            code, rows = fx.ledger()
            return fx.pre_pr_blocks(), fx.pre_push_blocks(), code, rows

    def assert_case(self, mutate, *, requirement, status, pre_pr, pre_push):
        pr_blocks, push_blocks, code, rows = self._run(mutate)
        self.assertEqual(pr_blocks, pre_pr, rows)
        self.assertEqual(push_blocks, pre_push, rows)
        # hook とスクリプトの判定が一致する（gate ごとに、ok でない行がある ⇔ hook が不足として通知する）
        self.assertEqual(_gate_fails(rows, "pre-PR"), pre_pr, rows)
        self.assertEqual(_gate_fails(rows, "pre-push"), pre_push, rows)
        if requirement is not None:
            self.assertIn(status, _status(rows, requirement), rows)
        self.assertEqual(code, 0 if all(s not in NOT_OK for s, *_ in rows) else 1, rows)
        return rows

    def test_all_present(self):
        pr_blocks, push_blocks, code, rows = self._run(lambda fx: None)
        self.assertEqual((pr_blocks, push_blocks, code), (False, False, 0), rows)
        self.assertEqual({s for s, *_ in rows} - {"ok", "n/a"}, set(), rows)
        for req in ("steering", "raw-steering", "next-action-done", "adr-distilled", "task-size",
                    "pre-pr-self-review", "pre-push-self-review", "independent-review",
                    "reviewed-by"):
            self.assertIn("ok", _status(rows, req), (req, rows))
        self.assertNotIn("steering-multiple", [d for _s, r, _g, d in rows if r == "steering"][0], rows)

    def test_reviewed_by_removed(self):
        def mutate(fx):
            fx.reviewed_by = ""
        self.assert_case(mutate, requirement="reviewed-by", status="missing",
                         pre_pr=False, pre_push=False)

    def test_reviewed_by_without_implementation_reviewer(self):
        def mutate(fx):
            fx.reviewed_by = "- Reviewed by: gdd-security-reviewer"
        self.assert_case(mutate, requirement="reviewed-by", status="invalid",
                         pre_pr=False, pre_push=False)

    def test_reviewed_by_skipped_with_the_declaration(self):
        # impl-gating が review を外した task（正本: references/task-breakdown-steps.md § Judgment Change）
        def mutate(fx):
            fx.reviewed_by = "- Judgment Change: no\n- Reviewed by: none (Judgment Change: no)"
        rows = self.assert_case(mutate, requirement="reviewed-by", status="ok", pre_pr=False, pre_push=False)
        self.assertEqual(_status(rows, "reviewed-by"), ["ok"], rows)

    def test_reviewed_by_skipped_without_the_declaration(self):
        def mutate(fx):
            fx.reviewed_by = "- Reviewed by: none (Judgment Change: no)"
        self.assert_case(mutate, requirement="reviewed-by", status="invalid",
                         pre_pr=False, pre_push=False)

    def test_independent_review_removed(self):
        def mutate(fx):
            fx.state["Independent Review"] = None
        self.assert_case(mutate, requirement="independent-review", status="missing",
                         pre_pr=True, pre_push=True)

    def test_independent_review_sha_is_old(self):
        def mutate(fx):
            fx.state["Independent Review"] = _independent_review(fx.old)
        self.assert_case(mutate, requirement="independent-review", status="invalid",
                         pre_pr=True, pre_push=True)

    def test_independent_review_sha_unresolvable(self):
        def mutate(fx):
            fx.state["Independent Review"] = _independent_review("deadbee")
        self.assert_case(mutate, requirement="independent-review", status="invalid",
                         pre_pr=True, pre_push=True)

    def test_independent_review_short_sha_of_head(self):
        def mutate(fx):
            fx.state["Independent Review"] = _independent_review(fx.head[:7])
        self.assert_case(mutate, requirement="independent-review", status="ok",
                         pre_pr=False, pre_push=False)

    def test_independent_review_high(self):
        for high, blocking in (("1", "0"), ("0", "1"), ("00", "0")):
            with self.subTest(high=high, blocking=blocking):
                def mutate(fx, high=high, blocking=blocking):
                    fx.state["Independent Review"] = _independent_review(
                        fx.head, high=high, blocking=blocking)
                self.assert_case(mutate, requirement="independent-review", status="invalid",
                                 pre_pr=True, pre_push=True)

    def test_pre_push_self_review_removed(self):
        def mutate(fx):
            fx.state["Pre-Push Self Review"] = None
        self.assert_case(mutate, requirement="pre-push-self-review", status="missing",
                         pre_pr=False, pre_push=True)

    def test_pre_push_self_review_sha_is_old(self):
        def mutate(fx):
            fx.state["Pre-Push Self Review"] = _self_review(fx.old)
        self.assert_case(mutate, requirement="pre-push-self-review", status="invalid",
                         pre_pr=False, pre_push=True)

    def test_sha_mismatch_row_shares_the_recovery_of_missing_row(self):
        """sha がずれた行の「それ以外は、」の後ろは、行が無いときの回復の文と同じ本文にする。"""
        def detail(mutate):
            with tempfile.TemporaryDirectory() as tmp:
                fx = GateLedgerFixture(Path(tmp))
                mutate(fx)
                fx.write()
                rows = fx.ledger()[1]
            return [d for _s, r, _g, d in rows if r == "pre-push-self-review"][0]
        missing = detail(lambda fx: fx.state.__setitem__("Pre-Push Self Review", None))
        stale = detail(lambda fx: fx.state.__setitem__("Pre-Push Self Review", _self_review(fx.old)))
        core = missing.split("証跡を直すときは、", 1)[1]
        self.assertIn("それ以外は、" + core, stale)

    def test_pre_pr_self_review_dry_no(self):
        def mutate(fx):
            fx.state["Pre-PR Self Review"] = _self_review(fx.head, dry="no")
        self.assert_case(mutate, requirement="pre-pr-self-review", status="invalid",
                         pre_pr=True, pre_push=False)

    def test_pre_pr_self_review_removed(self):
        def mutate(fx):
            fx.state["Pre-PR Self Review"] = None
        self.assert_case(mutate, requirement="pre-pr-self-review", status="missing",
                         pre_pr=True, pre_push=False)

    def test_next_action_not_done(self):
        def mutate(fx):
            fx.next_action = "gdd-completion-check"
        self.assert_case(mutate, requirement="next-action-done", status="invalid",
                         pre_pr=True, pre_push=False)

    def test_adr_distilled_removed(self):
        def mutate(fx):
            fx.state["ADR distilled"] = None
        self.assert_case(mutate, requirement="adr-distilled", status="missing",
                         pre_pr=True, pre_push=False)

    def test_adr_distilled_yes_without_adr_in_diff(self):
        def mutate(fx):
            fx.state["ADR distilled"] = "yes"
        self.assert_case(mutate, requirement="adr-distilled", status="invalid",
                         pre_pr=True, pre_push=False)

    def test_decision_handoff_rejects_adr_not_applicable(self):
        def mutate(fx):
            fx.state["- Decision Handoff"] = "issue: #12 | at: 2026-10-14T00:00:00Z"
        self.assert_case(mutate, requirement="adr-distilled", status="invalid",
                         pre_pr=True, pre_push=False)

    def test_decision_handoff_rejects_adr_not_applicable_in_quick_express(self):
        def mutate(fx):
            fx.state["Task Size"] = "quick (express)"
            fx.state["Pre-PR Self Review"] = None
            fx.state["Independent Review"] = None
            fx.state["Decision Handoff"] = ""
        self.assert_case(mutate, requirement="adr-distilled", status="invalid",
                         pre_pr=True, pre_push=False)

    def test_quick_express_does_not_require_dry_rows(self):
        def mutate(fx):
            fx.state["Task Size"] = "quick (express)"
            fx.state["Pre-PR Self Review"] = None
            fx.state["Independent Review"] = None
            fx.reviewed_by = ""
        self.assert_case(mutate, requirement="independent-review", status="n/a",
                         pre_pr=False, pre_push=False)

    def test_unknown_task_size_is_standard(self):
        def mutate(fx):
            fx.state["Task Size"] = "huge"
            fx.state["Independent Review"] = None
        self.assert_case(mutate, requirement="independent-review", status="missing",
                         pre_pr=True, pre_push=True)

    def test_tip_option_compares_pre_push_rows_with_tip(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            code, rows = fx.ledger("--tip", fx.old)
            self.assertEqual(code, 1, rows)
            self.assertIn("invalid", _status(rows, "pre-push-self-review"), rows)
            self.assertIn("invalid", _status(rows, "independent-review"), rows)

    def test_tip_option_marks_only_the_failing_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            _code, rows = fx.ledger("--tip", fx.old)
            gates = [g for s, r, g, _d in rows if r == "independent-review"]
            self.assertEqual(gates, ["pre-push"], rows)

    def test_steering_option_matching_resolution_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            # 相対パスは呼び出した cwd から解く。tmp の symlink（macOS の /var）を通るパスも同じ steering
            code, rows = fx.ledger("--steering", SLUG, cwd=fx.repo / ".steering")
            self.assertEqual((code, _status(rows, "steering")), (0, ["ok"]), rows)
            code, rows = fx.ledger("--steering", str(fx.steering))
            self.assertEqual((code, _status(rows, "steering")), (0, ["ok"]), rows)

    def test_base_option_is_resolved_like_the_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            out = fx.root / "written.txt"
            code, rows = fx.ledger("--base", f"--output={out}")
            self.assertFalse(out.exists())
            self.assertIn("invalid", _status(rows, "raw-steering"), rows)
            code, rows = fx.ledger("--base", "main")
            self.assertEqual((code, _status(rows, "raw-steering")), (0, ["ok"]), rows)
            # 短い名前は hook と同じく origin/ の側を先に解く
            _git(fx.repo, "update-ref", "refs/remotes/origin/main", "main")
            _code, rows = fx.ledger("--base", "main")
            details = [d for s, r, g, d in rows if r == "raw-steering"]
            self.assertTrue(details[0].startswith("origin/main...HEAD"), rows)

    def test_independent_review_malformed_names_the_reason(self):
        def mutate(fx):
            fx.state["Independent Review"] = fx.state["Independent Review"].replace("diff-only", "full")
        rows = self.assert_case(mutate, requirement="independent-review", status="invalid",
                                pre_pr=True, pre_push=True)
        detail = [d for s, r, g, d in rows if r == "independent-review"][0]
        self.assertIn("理由: malformed", detail)
        self.assertIn("context は diff-only 固定", detail)

    def test_no_completed_tasks_is_not_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            text = (fx.steering / "tasklist.md").read_text(encoding="utf-8")
            text = text.replace("### Task 1: 一つ目\n\n- Commit: x\n- Reviewed by: gdd-implementation-reviewer\n", "")
            (fx.steering / "tasklist.md").write_text(text, encoding="utf-8")
            code, rows = fx.ledger()
            # completion-check の Step 2a を通る Task Size で完了タスクが 0 件なのは、丸ごと移した・見出しが崩れた形
            self.assertEqual((code, _status(rows, "reviewed-by")), (1, ["missing"]), rows)

    def test_steering_option_not_matching_resolution_stays_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            other = fx.repo / ".steering" / "20261001-other"
            other.mkdir()
            (other / "state.md").write_text(
                "Resume From: gdd-test-driven-development\nNext Action: gdd-test-driven-development\n",
                encoding="utf-8",
            )
            (other / "tasklist.md").write_text(
                "Next Action: gdd-test-driven-development\n", encoding="utf-8")
            code, rows = fx.ledger("--steering", str(fx.steering))
            self.assertTrue(fx.pre_pr_blocks())
            self.assertEqual(code, 1, rows)
            self.assertIn("invalid", _status(rows, "steering"), rows)
            # 指定した steering の行は検算を続ける
            self.assertIn("ok", _status(rows, "independent-review"), rows)

    def test_steering_option_through_symlink_is_ok(self):
        # --steering は実体のパスにそろえて比べる（macOS の /var だけでなく、どの OS の symlink でも）
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            link = fx.root / "link"
            link.symlink_to(fx.repo)
            code, rows = fx.ledger("--steering", str(link / ".steering" / SLUG))
            self.assertEqual((code, _status(rows, "steering")), (0, ["ok"]), rows)

    def test_steering_gate_column_names_only_the_failing_gate(self):
        # 別の done の steering があると pre-PR の解決は multiple になり不足として通知されるが、pre-push は tip の証跡で選んで通す
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            other = fx.repo / ".steering" / "20261001-other"
            other.mkdir()
            (other / "state.md").write_text("Resume From: done\nNext Action: done\n", encoding="utf-8")
            (other / "tasklist.md").write_text("Next Action: done\n", encoding="utf-8")
            self.assertEqual((fx.pre_pr_blocks(), fx.pre_push_blocks()), (True, False))
            _code, rows = fx.ledger("--steering", str(fx.steering))
            self.assertEqual([(s, g) for s, r, g, _d in rows if r == "steering"], [("invalid", "pre-PR")], rows)
            self.assertEqual((_gate_fails(rows, "pre-PR"), _gate_fails(rows, "pre-push")), (True, False), rows)
            # pre-push の multiple は tip の証跡で選ぶ（hook の step 8b）。検算は判定しないことを詳細で知らせる
            detail = [d for _s, r, _g, d in rows if r == "steering"][0]
            self.assertIn("steering-multiple", detail, rows)
            # 注記は pre-PR の食い違いの説明の後ろ（詳細の最後）に置き、1 件に決まらないときの出口を挙げる
            self.assertGreater(detail.index("steering-multiple"), detail.index("--steering"), rows)
            self.assertIn("使わないステアリングの終え方", detail, rows)
            self.assertIn("ユーザーに確認", detail, rows)
            # 比べる向きは hook の step 8b と同じ（証跡の sha が tip の sha の先頭と一致する）
            self.assertIn("tip の sha の先頭と一致", detail, rows)

    def test_steering_row_is_ok_with_the_note_when_only_pre_push_is_multiple(self):
        # blocked の steering は pre-PR の解決からは外れ、pre-push の解決には入る（pre-push だけが multiple）
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            other = fx.repo / ".steering" / "20261001-other"
            other.mkdir()
            (other / "state.md").write_text("Resume From: blocked\nNext Action: blocked\n", encoding="utf-8")
            (other / "tasklist.md").write_text("Next Action: blocked\n", encoding="utf-8")
            self.assertFalse(fx.pre_push_blocks())
            _code, rows = fx.ledger()
            steering = [(s, g, d) for s, r, g, d in rows if r == "steering"]
            self.assertEqual([(s, g) for s, g, _d in steering], [("ok", "pre-PR,pre-push")], rows)
            detail = steering[0][2]
            self.assertGreater(detail.index("steering-multiple"), detail.index("pre-push=multiple"), rows)

    def test_steering_gate_column_skips_pre_push_when_it_resolves_none(self):
        # 終えた steering は pre-PR・pre-push のどちらの解決にも入らない。pre-push の hook は検査せずに通す
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.state["Resume From"] = "cancelled"
            fx.next_action = "cancelled"
            fx.write()
            self.assertFalse(fx.pre_push_blocks())
            _code, rows = fx.ledger("--steering", str(fx.steering))
            self.assertEqual([(s, g) for s, r, g, _d in rows if r == "steering"], [("invalid", "pre-PR")], rows)
            self.assertNotIn("steering-multiple", [d for _s, r, _g, d in rows if r == "steering"][0], rows)

    def test_moving_one_completed_task_drops_its_ok_row(self):
        # 戻す規則は「移す前の ok の行が移した後に無い」で決める。1 タスクのブロックを移すと、その ok 行が消える
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            path = fx.steering / "tasklist.md"
            text = path.read_text(encoding="utf-8")
            two = text.replace(
                "## Verification", "### Task 2: 二つ目\n\n- Reviewed by: gdd-implementation-reviewer\n\n## Verification")
            path.write_text(two, encoding="utf-8")
            _code, before = fx.ledger()
            path.write_text(text, encoding="utf-8")
            code, after = fx.ledger()
            self.assertEqual(code, 0, after)
            dropped = [r for r in set(before) - set(after) if r[1] == "reviewed-by"]
            self.assertEqual([r[0] for r in dropped], ["ok"], before)
            self.assertIn("二つ目", dropped[0][3])

    def test_rows_are_utf8_under_euc_jp_locale(self):
        # 利用者のロケールが UTF-8 でなくても、hook と同じく UTF-8 で読み書きする
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.extra_env = euc_jp_locale_env(self, Path(tmp))
            fx.write()
            code, rows = fx.ledger()
            self.assertEqual(code, 0, rows)
            self.assertIn("一つ目", " ".join(d for s, r, g, d in rows if r == "reviewed-by"), rows)

    def test_reviewed_by_has_a_row_per_task(self):
        # 既に 1 タスク欠けていても、別のタスクの行を落とすと、移した後にだけ現れる行が出る
        def tasklist(first: str, second: str) -> str:
            return (
                "# Task List\n\nNext Action: done\n\n## Completed Tasks\n\n"
                f"### Task 1: 一つ目\n\n{first}\n### Task 2: 二つ目\n\n{second}\n## Verification\n"
            )
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            path = fx.steering / "tasklist.md"
            path.write_text(tasklist("- Reviewed by: gdd-implementation-reviewer\n", ""), encoding="utf-8")
            _code, before = fx.ledger()
            self.assertEqual(_status(before, "reviewed-by"), ["ok", "missing"], before)
            path.write_text(tasklist("", ""), encoding="utf-8")
            _code, after = fx.ledger()
            appeared = [r for r in set(after) - set(before) if r[1] == "reviewed-by"]
            self.assertEqual([r[0] for r in appeared], ["missing"], after)
            self.assertIn("一つ目", appeared[0][3])

    def test_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = GateLedgerFixture(Path(tmp))
            fx.write()
            before = {p: p.read_bytes() for p in fx.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
            fx.ledger()
            after = {p: p.read_bytes() for p in fx.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
            self.assertEqual(before, after)
            self.assertFalse((fx.root / "hookstate").exists())


class SizeDenyNamesLedgerFieldsTests(unittest.TestCase):
    """サイズ上限の deny 文言は、検算スクリプトが state.md から読む field を全部「移さない行」に挙げる。

    検算スクリプトに field を足したのに文言に足さないと、その行を worklog へ移してよいと読める。
    """

    def test_every_state_field_the_ledger_reads_is_named(self):
        import re
        import sys
        sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))
        import steering_size

        script = SCRIPT.read_text(encoding="utf-8")
        fields = set(re.findall(r'gdd_extract_doc_field "\$STATE" "([^"]+)"', script))
        fields |= set(re.findall(r'check_self_review \S+ \S+ "([^"]+)"', script))
        fields |= set(re.findall(r'gdd_parse_merge_gate_field "\$STATE" "([^"]+)"', script))
        fields = {f for f in fields if not f.startswith("$")}
        self.assertGreaterEqual(fields, {"Task Size", "ADR distilled", "Independent Review",
                                         "Pre-PR Self Review", "Pre-Push Self Review"})
        for field in sorted(fields | {"Next Action", "Reviewed by", "Judgment Change"}):
            with self.subTest(field=field):
                self.assertIn(field, steering_size.SIZE_DENY_SUFFIX)


if __name__ == "__main__":
    unittest.main()
