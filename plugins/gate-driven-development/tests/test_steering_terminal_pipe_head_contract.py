"""hook の steering 検出で、pipe 注記つきの terminal 値を terminal と認識する契約。

state field の文法（references/state-machine.md § state field のフォーマット検証）は
`<value> | <key>: <detail>` で、先頭セグメントを trim して完全一致で比べる。hook は
`gdd_extract_doc_field` の戻り値（`|` で切らない）をそのまま `== "done"` 等で比べて
いたため、`Next Action: done | evidence: x` を terminal と認識しなかった。

その結果、active な steering と注記つき terminal の steering が同じ worktree に
あると候補 2 件の `multiple` になり、pre-push gate が `unresolved-steering` で
exit 0 していた（PR #164 独立-31 AI1。fail-open）。pre-push は、検査する steering を
1 件に決められない `multiple` を、active・終端を問わず不足として通知する。

区切りは ASCII `|` だけにする（先頭セグメントの切り出しは lint の `field_head` と同じ）。全角の
`｜`・`（` は文法外なので切らず、今までどおり active 扱い（gate が見る側）に残す。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _merge_gate_support import _init_repo as _mg_init_repo
from _merge_gate_support import _run_hook as _mg_run_hook
from _merge_gate_support import _write_marker_only
from _paths import PLUGIN_ROOT
from _stop_hook_test_base import _make_transcript_jsonl, _write_state_file
from _stop_hook_test_base import _run_hook as _stop_run_hook

LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
PRE_PUSH_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-push-gate-hook.sh"
PRE_PR_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-pr-gate-hook.sh"
LINT = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"

HEAD_INPUTS = (
    "done",
    "done | evidence: x",
    "done|x",
    "done   |   x",
    "cancelled | x",
    "blocked | reason: y",
    "| x",
    "   |",
    "|",
    "done-check | x",
    "done（x）",
    "done｜x",
    "gdd-implementation-gating",
    "https://github.com/acme/widgets/pull/7",
)


def _value_head(value: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", 'set -euo pipefail; source "$1"; gdd_value_head "$2"', "_", str(LIB), value],
        capture_output=True,
        text=True,
        check=False,
    )


def _lint_field_heads(values: tuple[str, ...]) -> list[str]:
    """lint の `field_head` を別プロセスで呼ぶ。

    lint は `from lib.lint_base import ...` で scripts/lib を import する。同じ
    pytest プロセスで hooks/scripts/lib が先に `lib` として読まれていると衝突する。
    """
    code = (
        "import importlib.util, json, sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "spec = importlib.util.spec_from_file_location('lint_resume_integrity', sys.argv[2])\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "values = json.loads(sys.stdin.read())\n"
        "print(json.dumps([m.field_head(f'- Next Action: {v}\\n', 'Next Action').strip() for v in values]))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(LINT.parent), str(LINT)],
        input=json.dumps(list(values)),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


class ValueHeadHelperTests(unittest.TestCase):
    def test_head_is_ascii_pipe_prefix_trimmed(self) -> None:
        for value in HEAD_INPUTS:
            with self.subTest(value=value):
                result = _value_head(value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, value.split("|", 1)[0].strip())

    def test_head_matches_lint_field_head(self) -> None:
        """(h) 先頭セグメントの切り出しが lint の `field_head` と同じ値を返す（ASCII の入力で固定）。"""
        for value, expected in zip(HEAD_INPUTS, _lint_field_heads(HEAD_INPUTS)):
            with self.subTest(value=value):
                self.assertEqual(_value_head(value).stdout, expected)

    def test_empty_value_does_not_abort_under_strict_mode(self) -> None:
        """安全策 2 (2): 空・pipe なし・pipe だけでも set -euo pipefail の下で落ちない。"""
        for value in ("", "done", "|"):
            with self.subTest(value=value):
                self.assertEqual(_value_head(value).returncode, 0)


class _PrePushFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        init_repo(self.repo, branch="main")
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "gdd-dev.local.md").write_text(
            "---\nactive: true\nsession_id: test-session\n---\n", encoding="utf-8"
        )

    def _write_steering(self, slug: str, *, resume_from: str, next_action: str) -> None:
        steering = self.repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        (steering / "state.md").write_text(
            f"- Resume From: {resume_from}\n"
            "- Human Check Status: approved\n"
            "- Route In Progress: none\n"
            f"- Next Action: {next_action}\n"
            "- Task Size: standard\n"
            "- Started At: 2026-09-24T00:00:00Z\n",
            encoding="utf-8",
        )

    def _write_active(self) -> None:
        self._write_steering(
            "20260924-active",
            resume_from="gdd-implementation-gating",
            next_action="gdd-implementation-gating",
        )

    def _push(self) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                "CLAUDE_CODE_SESSION_ID": "test-session",
                "GDD_HOOK_STATE_DIR": str(self.tmp / "hookstate"),
            }
        )
        payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}}
        result = subprocess.run(
            ["bash", str(PRE_PUSH_HOOK)],
            cwd=self.repo,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _assert_blocks_missing_evidence(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertTrue(result.stdout, "gate が走らずに通った（fail-open）")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])


class PrePushTerminalHeadTests(_PrePushFixture):
    def test_active_with_annotated_terminal_sibling_gates_active(self) -> None:
        """安全策 2 (1): 注記つき terminal が隣にあっても、active な steering を gate する。"""
        for label, resume_from, next_action in (
            ("next-done", "gdd-completion-check", "done | evidence: x"),
            ("resume-done", "done | updated_by: x", "gdd-completion-check"),
            ("resume-cancelled", "cancelled | reason: x", "gdd-completion-check"),
            ("next-blocked", "gdd-completion-check", "blocked | reason: x"),
        ):
            with self.subTest(case=label):
                self.setUp()
                self._write_active()
                self._write_steering("20260923-finished", resume_from=resume_from, next_action=next_action)
                self._assert_blocks_missing_evidence(self._push())

    def test_single_annotated_done_is_still_gated(self) -> None:
        """primary が none を返しても、union が done 候補として拾って gate する。

        primary だけを直した実装はここで exit 0（fail-open）になる。
        """
        self._write_steering(
            "20260923-finished", resume_from="gdd-completion-check", next_action="done | evidence: x"
        )
        self._assert_blocks_missing_evidence(self._push())

    def test_full_width_annotation_stays_active(self) -> None:
        """全角の区切りは文法外。切らずに active 扱い（gate が見る側）に残す。

        active な steering と並べて、候補 2 件の steering-multiple で不足として通知されることを見る。
        全角でも切る実装だと terminal になり、active 側 1 件の found で missing-evidence
        になる（reason code で見分ける）。
        """
        for value in ("done｜理由: x", "done（PR マージ済み）"):
            with self.subTest(value=value):
                self.setUp()
                self._write_active()
                self._write_steering("20260923-finished", resume_from="gdd-completion-check", next_action=value)
                payload = json.loads(self._push().stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("steering-multiple", payload["hookSpecificOutput"]["additionalContext"])
                self.assertNotIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])

    def test_empty_head_is_not_terminal(self) -> None:
        """安全策 2 (3): 先頭セグメントが空の値を terminal とみなさない。"""
        for value in ("| evidence: x", "   |"):
            with self.subTest(value=value):
                self.setUp()
                self._write_active()
                self._write_steering("20260923-other", resume_from=value, next_action=value)
                # 空 head の steering は active 候補に残るので、候補 2 件で multiple になり
                # steering-multiple で不足として通知される。terminal と誤認すると active 側 1 件の found に
                # なり、missing-evidence で不足として通知される（reason code で見分ける）。
                payload = json.loads(self._push().stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("steering-multiple", payload["hookSpecificOutput"]["additionalContext"])
                self.assertNotIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])

    def test_multiple_terminal_steerings_block(self) -> None:
        """終端の steering が 2 件以上で 1 つに決まらないときは、通さずに不足として通知する。

        pre-push は push がどのタスクのものかを決める材料を持たない。以前は `multiple`
        として exit 0 していたため、素の done と注記つき done が並ぶだけで検査が外れた。
        """
        for label, first, second in (
            ("done-and-annotated", ("done", "done"), ("gdd-completion-check", "done | evidence: x")),
            ("done-and-done", ("done", "done"), ("done", "done")),
            ("blocked-and-done", ("gdd-completion-check", "blocked | reason: x"), ("done", "done")),
        ):
            with self.subTest(case=label):
                self.setUp()
                self._write_steering("20260922-a", resume_from=first[0], next_action=first[1])
                self._write_steering("20260923-b", resume_from=second[0], next_action=second[1])
                result = self._push()
                self.assertTrue(result.stdout, "検査されずに通った（fail-open）")
                payload = json.loads(result.stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("steering-multiple", payload["hookSpecificOutput"]["additionalContext"])
                self.assertIn("GDD_SKIP_PRE_PUSH_GATE=1", payload["hookSpecificOutput"]["additionalContext"])

    def test_single_blocked_next_action_is_gated(self) -> None:
        """`Next Action: blocked` の steering も union の候補にする（素の値・注記つきとも）。"""
        for next_action in ("blocked", "blocked | reason: x"):
            with self.subTest(next_action=next_action):
                self.setUp()
                self._write_steering("20260923-b", resume_from="gdd-completion-check", next_action=next_action)
                self._assert_blocks_missing_evidence(self._push())

    def test_annotated_stale_brainstorming_is_dropped_like_plain(self) -> None:
        """古い brainstorming の steering は、注記つきでも素の値と同じく候補から外す。

        外さないと active な隣と 2 件で multiple になり、push が検査されずに通る。
        """
        steering = self.repo / ".steering" / "20260901-stale"
        steering.mkdir(parents=True)
        (steering / "state.md").write_text(
            "- Resume From: gdd-brainstorming | updated_by: x\n"
            "- Next Action: gdd-brainstorming\n"
            "- Started At: 2026-01-01T00:00:00Z\n",
            encoding="utf-8",
        )
        self._write_active()
        self._assert_blocks_missing_evidence(self._push())

    def test_annotated_terminal_behaves_like_plain_value(self) -> None:
        """`cancelled | x`・`blocked | x` は素の値と同じ挙動になる。"""
        for label, resume_from, annotated_next, plain_next in (
            ("cancelled", "gdd-completion-check", "cancelled | reason: x", "cancelled"),
            ("blocked", "gdd-completion-check", "blocked | reason: x", "blocked"),
        ):
            with self.subTest(case=label):
                outcomes = []
                for next_action in (annotated_next, plain_next):
                    self.setUp()
                    self._write_steering("20260923-finished", resume_from=resume_from, next_action=next_action)
                    outcomes.append(self._push().stdout)
                self.assertEqual(outcomes[0], outcomes[1])


class PrePrTerminalHeadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        init_repo(self.repo, branch="main")
        subprocess.run(["git", "switch", "-q", "-c", "feature"], cwd=self.repo, check=True)
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "gdd-dev.local.md").write_text(
            "---\nactive: true\nsession_id: test-session\n---\n", encoding="utf-8"
        )

    def _write_steering(self, *, tasklist_next: str, state_next: str | None = None) -> None:
        steering = self.repo / ".steering" / "20260924-pre-pr"
        steering.mkdir(parents=True)
        state_next_line = f"Next Action: {state_next}\n" if state_next is not None else ""
        (steering / "state.md").write_text(
            "Resume From: gdd-completion-check\n"
            "Human Check Status: approved\n"
            "Route In Progress: none\n"
            f"{state_next_line}"
            "Task Size: quick (express)\n"
            "ADR distilled: not_applicable\n"
            "ADR distillation reason: quick express / 重要判断なし\n"
            "Started At: 2026-09-24T00:00:00Z\n",
            encoding="utf-8",
        )
        (steering / "tasklist.md").write_text(
            "# Task List\n\n## Current Task\n- なし\n\n## Pending Tasks\n- なし\n\n"
            f"## Completed Tasks\n- done\n\nNext Action={tasklist_next}\n",
            encoding="utf-8",
        )

    def _create_pr(self) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                "CLAUDE_CODE_SESSION_ID": "test-session",
                "GDD_HOOK_STATE_DIR": tempfile.mkdtemp(dir=self._tmp.name),
            }
        )
        payload = {"tool_name": "Bash", "tool_input": {"command": "gh pr create --title t --body b"}}
        result = subprocess.run(
            ["bash", str(PRE_PR_HOOK)],
            cwd=self.repo,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_annotated_done_passes_completion_guard(self) -> None:
        self._write_steering(tasklist_next="done | evidence: completion-check pass")
        self.assertEqual(self._create_pr().stdout, "")

    def test_empty_head_does_not_fall_back_to_state(self) -> None:
        """tasklist の空 head から state.md の done へ読み直して通る経路を作らない。"""
        self._write_steering(tasklist_next="| evidence: x", state_next="done")
        payload = json.loads(self._create_pr().stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def _write_pair(self, resume_from: str, next_action: str) -> None:
        for slug in ("20260923-a", "20260924-b"):
            steering = self.repo / ".steering" / slug
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                f"Resume From: {resume_from}\nHuman Check Status: approved\n"
                f"Route In Progress: none\nNext Action: {next_action}\n",
                encoding="utf-8",
            )

    def test_multiple_steerings_guide_cancelling_unused_steering(self) -> None:
        """steering が 2 件で 1 つに決まらないときの通知は、pre-push と同じ解き方を案内する。

        作業中が 2 件なら、片方を completion-check で done にしても残りの作業中の steering で
        同じ gate に不足として通知される。done が 2 件なら、completion-check をやり直しても 2 件のまま。
        どちらも「completion-check を通してから」では解けない。
        """
        for label, resume_from, next_action in (
            ("active", "gdd-implementation-gating", "gdd-implementation-gating"),
            ("done", "gdd-completion-check", "done"),
        ):
            with self.subTest(case=label):
                self.setUp()
                self._write_pair(resume_from, next_action)
                payload = json.loads(self._create_pr().stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("Resume From と Next Action をどちらも cancelled", payload["hookSpecificOutput"]["additionalContext"])
                self.assertNotIn("completion-check を通してから", payload["hookSpecificOutput"]["additionalContext"])

    def test_no_completed_steering_still_guides_completion_check(self) -> None:
        """steering が 1 件も解決できない（done も無い）ときは、今までどおり completion-check を案内する。"""
        (self.repo / ".steering").mkdir()
        payload = json.loads(self._create_pr().stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("completion-check を通してから", payload["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("cancelled", payload["hookSpecificOutput"]["additionalContext"])


class MergeGateTargetRematchTests(unittest.TestCase):
    """primary が active の steering を返しても、対象 PR を記録した steering を gate する。

    以前は候補 2 件の `multiple` で PR URL 照合（`_mg_match_steering_by_target`）に
    入っていた。注記つき terminal を terminal と認識すると primary が active 側を
    found で返すので、照合し直さないと対象 PR の merge が検査されずに通る。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _mg_init_repo(self.tmp)
        _write_marker_only(self.repo, active=False, session_id="test-session")

    def _write(self, slug: str, body: str) -> None:
        steering = self.repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        (steering / "state.md").write_text("## Gate Status\n" + body, encoding="utf-8")

    def _merge(self, pr: int) -> str:
        result = _mg_run_hook({"tool_input": {"command": f"gh pr merge {pr}"}}, self.repo, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def _write_active(self, pr_url_line: str) -> None:
        self._write(
            "20260924-active",
            "- Resume From: gdd-implementation-gating\n- Next Action: gdd-implementation-gating\n"
            + pr_url_line,
        )

    def test_target_steering_is_gated_when_primary_returns_other_active(self) -> None:
        """対象 PR の steering の証跡で判定する。

        active 側には evidence の key が無い Merge Approval を置く。active 側で判定すると
        evidence-unparsable、対象側（Merge Approval なし）で判定すると approval-missing になる。
        """
        for label, next_action in (("annotated", "done | evidence: x"), ("plain", "done")):
            for active_url in ("- PR URL: https://github.com/acme/widgets/pull/9\n", ""):
                with self.subTest(target=label, active_has_url=bool(active_url)):
                    self.setUp()
                    self._write_active(active_url + "- Merge Approval: PR #7 / head 0000000\n")
                    self._write(
                        "20260923-target",
                        f"- Resume From: gdd-completion-check\n- Next Action: {next_action}\n"
                        "- PR URL: https://github.com/acme/widgets/pull/7\n",
                    )
                    out = self._merge(7)
                    self.assertIn('"hookEventName": "PreToolUse"', out, "対象 PR の steering が検査されずに通った")
                    self.assertIn("reason code: approval-missing", out)
                    self.assertNotIn("evidence-unparsable", out)
                    self.assertNotIn("pr-url-unrecorded", out)

    def test_many_target_steerings_block_as_ambiguous(self) -> None:
        """対象 PR を記録した steering が 2 件なら、multiple 経路と同じく不足として通知する。"""
        for next_action in ("done | evidence: x", "done"):
            with self.subTest(next_action=next_action):
                self.setUp()
                self._write_active("- PR URL: https://github.com/acme/widgets/pull/9\n")
                for slug in ("20260923-t1", "20260923-t2"):
                    self._write(
                        slug,
                        f"- Resume From: gdd-completion-check\n- Next Action: {next_action}\n"
                        "- PR URL: https://github.com/acme/widgets/pull/7\n",
                    )
                out = self._merge(7)
                self.assertIn('"hookEventName": "PreToolUse"', out)
                self.assertIn("steering-ambiguous", out)

    def test_unrecorded_url_among_candidates_blocks(self) -> None:
        """対象 PR を記録した steering が無く、URL 未記録の steering があれば不足として通知する。

        multiple 経路（判定材料の欠落は `pr-url-unrecorded`）と同じ扱いにする。
        """
        for next_action in ("done | evidence: x", "done"):
            with self.subTest(next_action=next_action):
                self.setUp()
                self._write_active("- PR URL: https://github.com/acme/widgets/pull/9\n")
                self._write(
                    "20260923-unrecorded",
                    f"- Resume From: gdd-completion-check\n- Next Action: {next_action}\n",
                )
                out = self._merge(7)
                self.assertIn('"hookEventName": "PreToolUse"', out)
                self.assertIn("pr-url-unrecorded", out)

    def test_no_steering_records_target_passes_through(self) -> None:
        """全候補が別 PR を記録しているときは、今までどおり素通り（対象外）。"""
        self._write_active("- PR URL: https://github.com/acme/widgets/pull/9\n")
        self._write(
            "20260923-other",
            "- Resume From: done\n- Next Action: done | evidence: x\n"
            "- PR URL: https://github.com/acme/widgets/pull/8\n",
        )
        self.assertNotIn('"hookEventName"', self._merge(7))


class SessionStartMultipleGuidanceTests(unittest.TestCase):
    """session-start の multiple 警告は、pre-push の steering-multiple と同じ解き方を案内する。

    以前は「worktree ごと削除するか、tasklist.md の Next Action=cancelled」を案内していた。
    検出は current worktree の state.md しか読まないので、tasklist.md を変えても解けず、
    worktree の削除は作業中の checkout ごと消す。
    """

    def test_warning_guides_cancelling_unused_steering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(os.path.realpath(tmp))
            home = root / "home"
            home.mkdir()
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            for slug in ("20260923-a", "20260924-b"):
                steering = repo / ".steering" / slug
                steering.mkdir(parents=True)
                (steering / "state.md").write_text(
                    "- Resume From: gdd-implementation-gating\n- Human Check Status: approved\n"
                    "- Route In Progress: none\n- Next Action: gdd-implementation-gating\n",
                    encoding="utf-8",
                )
            env = os.environ.copy()
            env.update({"HOME": str(home), "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)})
            for leaked in ("GDD_STEERING_DIR", "GDD_HOOK_STATE_DIR", "CLAUDE_CODE_SESSION_ID", "GDD_WORKTREES_ROOT"):
                env.pop(leaked, None)
            result = subprocess.run(
                ["bash", str(PLUGIN_ROOT / "hooks" / "scripts" / "run-session-start-hook.sh")],
                cwd=repo, input="", capture_output=True, text=True, env=env, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            additional = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("[gdd:warning]", additional)
            self.assertIn("Resume From と Next Action をどちらも cancelled", additional)
            self.assertNotIn("別の場所へ移", additional)
            self.assertNotIn("worktree ごと削除", additional)
            self.assertNotIn("tasklist.md の Next Action=cancelled", additional)


class StopHookHumanCheckFallbackTests(unittest.TestCase):
    """done guard の markerless fallback も `Resume From` を先頭セグメントで比べる。"""

    def test_annotated_human_check_waiting_enters_fallback(self) -> None:
        for resume_from in ("human-check-waiting", "human-check-waiting | updated_by: x"):
            with self.subTest(resume_from=resume_from), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
                steering = ws / ".steering" / "20260924-task"
                steering.mkdir(parents=True)
                (steering / "state.md").write_text(
                    f"# State\n\n## Gate Status\n- Resume From: {resume_from}\n", encoding="utf-8"
                )
                transcript = ws / "transcript.jsonl"
                _make_transcript_jsonl(transcript, assistant_text="承認をお願いします。", user_text="")
                code, _, err = _stop_run_hook(ws, transcript, session_id="test-session")
                self.assertEqual(code, 0)
                self.assertIn("markerless state fallback suppressed", err)


if __name__ == "__main__":
    unittest.main()
