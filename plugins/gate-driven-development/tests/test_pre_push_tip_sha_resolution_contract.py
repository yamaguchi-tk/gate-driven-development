"""pre-push gate: steering が複数でも、push 対象の tip の証跡を持つ steering が 1 件なら検査する。

検査する steering を 1 件に決められない（`multiple`）とき、pre-push は `steering-multiple` で
不足として通知する。同じ checkout に古い steering が残るだけで、証跡を書いた本人の push も止まっていた。
候補の `Pre-Push Self Review` の sha（大文字小文字は区別しない）が push 対象の tip の sha の
先頭と一致する steering がちょうど 1 件なら、その steering で以降の検査（dry・Independent
Review。Task Size は読まず standard）を行う。0 件・2 件以上なら、今どおり `steering-multiple` で不足として通知する。
選んだ steering の sha を解決できなければ、step 11 が `sha-mismatch` で不足として通知する。
merge gate が対象 PR の URL で steering を探し直すのと同じ形。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _pre_push_gate_support import (
    AC18_ALLOWED_TOKENS,
    AC18_SHA_RE,
    AC18_TOKEN_RE,
    PrePushGateFixtureMixin,
)

TIP_REASON = "tip の Pre-Push Self Review"
# tip で選んだときだけ通知文に添える注記（standard として検査した理由と復旧）
TIP_NOTE = "push 対象の tip の証跡で選んだため"
# steering を終える案内は、ほかの 3 つの入口と同じ前提（ユーザーへの確認・手順の参照先）を持つ
USER_CONFIRM = "ユーザーに確認"
CANCEL_PROCEDURE = "references/self-review-lanes.md の「使わないステアリングの終え方」"


class PrePushTipShaResolutionTests(PrePushGateFixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self._init_repo(self.repo)
        self._write_local_state(self.repo)
        self.head = self._head_sha(self.repo)

    def _push(self, ref: str = "main") -> subprocess.CompletedProcess[str]:
        result = self._run_hook(self.repo, f"git push origin {ref}")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _reason(self, result: subprocess.CompletedProcess[str]) -> str:
        self.assertTrue(result.stdout.strip(), "検査されずに通った（fail-open）")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return payload["hookSpecificOutput"]["additionalContext"]

    def _assert_steering_multiple(self, result: subprocess.CompletedProcess[str]) -> None:
        reason = self._reason(result)
        self.assertIn("steering-multiple", reason)
        self.assertIn(TIP_REASON, reason)

    def _pair(self, evidence_a: str | None, evidence_b: str | None = None, **kwargs) -> None:
        self._write_steering(self.repo, slug="20260923-a", evidence=evidence_a, **kwargs)
        self._write_steering(self.repo, slug="20260924-b", evidence=evidence_b)

    # ---- 一致がちょうど 1 件なら、その steering で検査する ------------------------

    def test_single_steering_with_tip_evidence_is_gated_and_passes(self) -> None:
        self._pair(self._evidence_line(sha=self.head))
        self.assertIsNone(self._decision(self._push()))

    def test_short_sha_evidence_is_normalized(self) -> None:
        self._pair(self._evidence_line(sha=self.head[:12]))
        self.assertIsNone(self._decision(self._push()))

    def test_terminal_steerings_resolve_the_same_way(self) -> None:
        """終端（done）だけが並ぶ multiple でも同じ材料で解く。"""
        self._write_steering(
            self.repo, slug="20260923-a", resume_from="done", next_action="done",
            evidence=self._evidence_line(sha=self.head),
        )
        self._write_steering(self.repo, slug="20260924-b", resume_from="done", next_action="done")
        self.assertIsNone(self._decision(self._push()))

    def test_tip_note_is_added_only_when_resolved_by_tip(self) -> None:
        """tip で選んだときの通知文は、standard として検査した理由と復旧を示す（AC-18 の語だけで）。"""
        cases = (
            ("independent-review-missing", {"auto_independent_review": False}, None),
            ("dry-not-reached", {}, "no"),
        )
        for code, kwargs, dry in cases:
            extra = {"dry": dry, "consecutive_clean": "0"} if dry else {}
            with self.subTest(code=code, path="tip"):
                self.setUp()
                self._pair(self._evidence_line(sha=self.head, **extra), **kwargs)
                reason = self._reason(self._push())
                self.assertIn(code, reason)
                for expected in (TIP_NOTE, USER_CONFIRM, CANCEL_PROCEDURE):
                    self.assertIn(expected, reason)
                unknown = [
                    t for t in AC18_TOKEN_RE.findall(reason)
                    if t not in AC18_ALLOWED_TOKENS and not AC18_SHA_RE.match(t)
                ]
                self.assertEqual(unknown, [], reason)
            with self.subTest(code=code, path="single steering"):
                self.setUp()
                self._write_steering(
                    self.repo, slug="20260923-a",
                    evidence=self._evidence_line(sha=self.head, **extra), **kwargs,
                )
                reason = self._reason(self._push())
                self.assertIn(code, reason)
                self.assertNotIn(TIP_NOTE, reason)

    def test_explicit_ref_uses_that_ref_tip(self) -> None:
        subprocess.run(["git", "switch", "-q", "-c", "feature"], cwd=self.repo, check=True)
        (self.repo / "f.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "f.txt"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "f"], cwd=self.repo, check=True)
        feature_tip = self._head_sha(self.repo)
        subprocess.run(["git", "switch", "-q", "main"], cwd=self.repo, check=True)
        with self.subTest(evidence="feature tip"):
            self._pair(self._evidence_line(sha=feature_tip))
            self.assertIsNone(self._decision(self._push("feature")))
        with self.subTest(evidence="HEAD (not the pushed ref)"):
            self._pair(self._evidence_line(sha=self.head))
            self._assert_steering_multiple(self._push("feature"))

    def test_match_is_found_regardless_of_scan_order(self) -> None:
        """一致が走査の先頭でなくても、その steering を選ぶ（先頭を選ぶだけの実装を通さない）。"""
        self._pair(None, self._evidence_line(sha=self.head))
        self.assertIsNone(self._decision(self._push()))
        self._write_steering(
            self.repo, slug="20260924-b", evidence=self._evidence_line(sha=self.head),
            auto_independent_review=False,
        )
        self.assertIn("independent-review-missing", self._reason(self._push()))

    # ---- fail-open 側（安全策 2）: 1 件に決まらない・判定できないときは不足として通知する -----

    def test_selected_steering_task_size_does_not_weaken_the_checks(self) -> None:
        """不足として通知すべき入力: tip で選んだ steering の Task Size（trivial・quick）で検査を緩めない。

        候補の外（cancelled）でも候補の中でも、tip で解いたときは standard で検査する。
        """
        for size, state in (
            ("trivial", ("cancelled", "cancelled")),
            ("quick (express)", ("cancelled", "cancelled")),
            ("quick (standard)", ("gdd-implementation-gating", "gdd-implementation-gating")),
        ):
            with self.subTest(task_size=size, resume_from=state[0]):
                self.setUp()
                self._write_steering(self.repo, slug="20260923-a")
                self._write_steering(self.repo, slug="20260924-b")
                self._write_steering(
                    self.repo, slug="20260925-c", task_size=size,
                    resume_from=state[0], next_action=state[1],
                    evidence=self._evidence_line(sha=self.head), auto_independent_review=False,
                )
                self.assertIn("independent-review-missing", self._reason(self._push()))

    def test_tip_resolution_does_not_parse_every_steering(self) -> None:
        """判定できない（timeout で無出力のまま素通り）: 解決の費用を steering の件数で増やさない。

        hook の timeout を超えると、無出力のまま素通りになる。tip 以外の証跡を持つ steering が
        増えても、`Pre-Push Self Review` を読む回数は増えない（全件を parse しない）。state.md の
        field は awk で読むので、PATH の先頭に置いた awk が受け取った field 名を数える（時間では
        環境の揺れで判別できない）。
        """
        real_awk = shutil.which("awk")
        self.assertIsNotNone(real_awk)

        def evidence_reads(extra: int) -> int:
            self.setUp()
            for i in range(extra):
                self._write_steering(
                    self.repo, slug=f"20260801-{i:03d}", resume_from="cancelled",
                    next_action="cancelled", evidence=self._evidence_line(sha="0" * 40),
                )
            self._pair(self._evidence_line(sha=self.head))
            bindir = Path(self._tmp.name) / "bin"
            bindir.mkdir()
            log = Path(self._tmp.name) / "awk.log"
            shim = bindir / "awk"
            shim.write_text(f'#!/bin/sh\nprintf "%s\\n" "$2" >> "{log}"\nexec "{real_awk}" "$@"\n', encoding="utf-8")
            shim.chmod(0o755)
            result = self._run_hook(
                self.repo, "git push origin main",
                extra_env={"PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsNone(self._decision(result))
            lines = log.read_text(encoding="utf-8").splitlines()
            return lines.count("field=Pre-Push Self Review")

        baseline = evidence_reads(0)
        self.assertGreater(baseline, 0, "shim が parser の awk を捕まえていない")
        self.assertEqual(evidence_reads(50), baseline)

    def test_evidence_sha_must_be_a_prefix_of_the_tip(self) -> None:
        """不足として通知すべき入力: tip を指す tag の sha は一致に数えない（先に絞る grep と同じ集合）。

        tip の sha がファイルの別の行（Independent Review）にあって grep を通っても、証跡の
        sha が tip の先頭でなければ一致にしない。
        """
        subprocess.run(["git", "tag", "-a", "-m", "t", "v1"], cwd=self.repo, check=True)
        tag = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "v1"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self._write_steering(
            self.repo, slug="20260923-a", evidence=self._evidence_line(sha=tag),
            independent_review=self._independent_review_line(sha=self.head),
        )
        self._write_steering(self.repo, slug="20260924-b")
        self._assert_steering_multiple(self._push())

    def test_uppercase_evidence_sha_is_a_match(self) -> None:
        self._pair(self._evidence_line(sha=self.head.upper()))
        self.assertIsNone(self._decision(self._push()))

    def test_two_steerings_with_tip_evidence_block(self) -> None:
        """不足として通知すべき入力: 2 件とも tip の証跡を持つ → どちらを検査するか決めない。"""
        self._pair(self._evidence_line(sha=self.head), self._evidence_line(sha=self.head))
        self._assert_steering_multiple(self._push())

    def test_no_tip_evidence_blocks(self) -> None:
        with self.subTest(evidence="none"):
            self._pair(None)
            self._assert_steering_multiple(self._push())
        with self.subTest(evidence="old commit"):
            self.setUp()
            old = self._commit_parent()
            self._pair(self._evidence_line(sha=old))
            self._assert_steering_multiple(self._push())

    def test_unresolvable_evidence_sha_blocks(self) -> None:
        """判定できない: 存在しない sha・commit でない object（tree）の sha は一致としない。"""
        tree = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD^{tree}"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        for label, sha in (("missing", "0" * 40), ("tree", tree)):
            with self.subTest(sha=label):
                self.setUp()
                self._pair(self._evidence_line(sha=sha))
                self._assert_steering_multiple(self._push())

    def test_invalid_evidence_line_is_not_a_match(self) -> None:
        """証跡の書式が不正なら、sha が tip でも一致としない（parser が valid にしたものだけ）。"""
        self._pair(f"{self.head} | rounds: 2")
        self._assert_steering_multiple(self._push())

    def test_unreadable_state_does_not_abort_the_guard(self) -> None:
        """例外で guard が落ちない: 読めない state.md があっても不足の通知を出す。

        読めない state.md は、steering の解決の直後に `steering-unreadable` で不足として通知される
        （tip の証跡での選び直しまで進まない）。
        """
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        self._pair(self._evidence_line(sha=self.head))
        state = self.repo / ".steering" / "20260923-a" / "state.md"
        state.chmod(0)
        self.addCleanup(state.chmod, 0o644)
        self.assertIn("steering-unreadable", self._reason(self._push()))

    def _commit_parent(self) -> str:
        """HEAD より前の commit を作って、その sha を返す（HEAD は新しい commit に進む）。"""
        old = self._head_sha(self.repo)
        (self.repo / "g.txt").write_text("g\n", encoding="utf-8")
        subprocess.run(["git", "add", "g.txt"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "g"], cwd=self.repo, check=True)
        self.head = self._head_sha(self.repo)
        return old


class PrePushBoundTerminalSteeringTests(PrePushGateFixtureMixin, unittest.TestCase):
    """worktree の binding が終端の steering を指すとき、binding の無い作業中の steering を検査する。

    binding が done・cancelled（または stale な brainstorming）の steering を指すと、resolver は
    作業中の steering を数えなかった。cancelled なら `none/terminal-only` で検査せずに通し、done
    （または別の done・blocked の steering が 1 件ある）なら、その終端の steering の Task Size
    （trivial なら無検査）で検査していた。resolver が binding の無いときと同じ規則で作業中の
    steering を数え直し、1 件ならそれを、2 件以上なら tip の証跡で選んで検査する。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self._init_repo(self.repo)
        self._write_local_state(self.repo)
        self.head = self._head_sha(self.repo)
        bound = self._write_steering(
            self.repo, slug="20260901-bound", resume_from="cancelled", next_action="cancelled",
            task_id="20260901-bound", worktree=self.repo, branch="main",
        )
        self._register_binding(self.repo, bound / "state.md")

    def _push(self) -> subprocess.CompletedProcess[str]:
        result = self._run_hook(
            self.repo, "git push origin main",
            extra_env={"GDD_HOOK_STATE_DIR": str(Path(self._tmp.name) / "hookstate")},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    _reason = PrePushTipShaResolutionTests._reason

    def test_single_active_steering_is_gated(self) -> None:
        """不足として通知すべき入力: 作業中の steering が 1 件で証跡が無い → missing-evidence。"""
        self._write_steering(self.repo, slug="20260924-active")
        self.assertIn("missing-evidence", self._reason(self._push()))

    def test_single_active_steering_uses_its_own_evidence(self) -> None:
        self._write_steering(
            self.repo, slug="20260924-active", evidence=self._evidence_line(sha=self.head),
        )
        self.assertIsNone(self._decision(self._push()))

    def test_two_active_steerings_are_resolved_by_the_tip(self) -> None:
        with self.subTest(evidence="none"):
            self._write_steering(self.repo, slug="20260924-a")
            self._write_steering(self.repo, slug="20260925-b")
            self.assertIn("steering-multiple", self._reason(self._push()))
        with self.subTest(evidence="tip in b"):
            self._write_steering(
                self.repo, slug="20260925-b", evidence=self._evidence_line(sha=self.head),
                auto_independent_review=False,
            )
            self.assertIn("independent-review-missing", self._reason(self._push()))

    def test_unreadable_state_counts_as_active(self) -> None:
        """例外で guard が落ちない・判定できないときは不足として通知する: 読めない state.md は作業中に数える。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        steering = self._write_steering(self.repo, slug="20260924-active")
        state = steering / "state.md"
        state.chmod(0)
        self.addCleanup(state.chmod, 0o644)
        self.assertTrue(self._push().stdout.strip(), "検査されずに通った（fail-open）")

    def _bind_done(self, *, task_size: str = "standard", evidence: str | None = None) -> None:
        bound = self._write_steering(
            self.repo, slug="20260901-bound", resume_from="done", next_action="done",
            task_size=task_size, task_id="20260901-bound", worktree=self.repo, branch="main",
            evidence=evidence,
        )
        self._register_binding(self.repo, bound / "state.md")

    def test_binding_to_a_done_trivial_steering_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: binding が done・trivial の steering を指しても、作業中の steering があれば
        どちらかを決められず不足として通知する（binding 先の Task Size でも、作業中の steering の Task Size でも通さない）。"""
        self._bind_done(task_size="trivial")
        self._write_steering(self.repo, slug="20260924-active")
        self.assertIn("steering-multiple", self._reason(self._push()))

    def test_active_trivial_steering_does_not_loosen_a_done_binding(self) -> None:
        """不足として通知すべき入力: binding が done・standard・証跡なしの steering を指し、作業中の steering が
        trivial でも、trivial として通さない（binding が無いときの union は binding 先を standard で止めていた）。"""
        self._bind_done()
        self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
        self.assertTrue(self._push().stdout.strip(), "検査されずに通った（fail-open）")

    def test_done_binding_with_the_tip_evidence_is_chosen_over_a_stray_active_one(self) -> None:
        """binding 先の done の steering が tip の証跡を持てば、残っている作業中の steering より先に選ばれる。"""
        self._bind_done(evidence=self._evidence_line(sha=self.head))
        self._write_steering(self.repo, slug="20260924-active")
        self.assertIsNone(self._decision(self._push()))

    def test_done_binding_without_active_steerings_is_resolved_as_before(self) -> None:
        """作業中の steering が無ければ、binding 先の done の steering をその Task Size で検査する（今どおり）。"""
        self._bind_done()
        self.assertIn("missing-evidence", self._reason(self._push()))

    def test_another_done_trivial_steering_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: binding が cancelled で、別に done・trivial の steering が 1 件あっても、
        作業中の steering があればどちらかを決められず不足として通知する。"""
        self._write_steering(
            self.repo, slug="20260910-done", resume_from="done", next_action="done", task_size="trivial",
        )
        self._write_steering(self.repo, slug="20260924-active")
        self.assertIn("steering-multiple", self._reason(self._push()))

    def test_active_trivial_steering_does_not_loosen_another_done_one(self) -> None:
        """不足として通知すべき入力: binding が cancelled で、done・standard・証跡なしの steering と作業中・trivial の
        steering があるとき、trivial として通さない（binding が無いときの union は done の方を standard で止めていた）。"""
        self._write_steering(self.repo, slug="20260910-done", resume_from="done", next_action="done")
        self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
        self.assertTrue(self._push().stdout.strip(), "検査されずに通った（fail-open）")

    def test_single_active_trivial_steering_passes_as_without_the_binding(self) -> None:
        """限界の固定: binding が cancelled で、作業中・trivial の steering だけなら、binding が無いときと同じく通る。"""
        self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
        self.assertIsNone(self._decision(self._push()))

    def test_detect_without_the_option_still_ignores_a_terminal_binding(self) -> None:
        """他の呼び出し元（session-start など）が使う引数なしの呼び出しは、今どおり none を返す。"""
        self._write_steering(self.repo, slug="20260924-active")
        lib = PLUGIN_ROOT / "hooks" / "scripts" / "lib"
        result = subprocess.run(
            ["bash", "-c", 'source "$1/detect-steering.sh"; gdd_detect_active_steering || true; '
             'printf "%s" "$GDD_STEERING_STATUS"', "_", str(lib)],
            cwd=self.repo, capture_output=True, text=True, check=True,
            env={**os.environ, "GDD_PLUGIN_ROOT": str(PLUGIN_ROOT)},
        )
        self.assertEqual(result.stdout, "none", result.stderr)

    def test_only_terminal_or_stale_steerings_still_pass(self) -> None:
        """作業中が無い（終端・stale な brainstorming だけ）の checkout は、今どおり検査しない。"""
        self._write_steering(self.repo, slug="20260920-old", resume_from="cancelled", next_action="cancelled")
        stale = self.repo / ".steering" / "20260101-idea"
        stale.mkdir(parents=True)
        (stale / "state.md").write_text(
            "Resume From: gdd-brainstorming\nHuman Check Status: pending\nRoute In Progress: none\n"
            "Next Action: gdd-brainstorming\nTask Size: standard\nStarted At: 2026-01-01T00:00:00Z\n",
            encoding="utf-8",
        )
        self.assertIsNone(self._decision(self._push()))


def _brainstorming_discard_values() -> tuple[str, str]:
    """gdd-brainstorming の discard の手順が state.md に書かせる `Resume From`・`Next Action` の値。"""
    text = (PLUGIN_ROOT / "skills" / "gdd-brainstorming" / "SKILL.md").read_text(encoding="utf-8")
    line = next(line for line in text.splitlines() if "`state.md` を" in line and "`Next Action:" in line)
    values = dict(re.findall(r"`(Resume From|Next Action): ([^`]+)`", line))
    return values["Resume From"], values["Next Action"]


class PrePushBrainstormingDiscardBindingTests(PrePushBoundTerminalSteeringTests):
    """brainstorming の discard が書かせる値（skill の行から取り出す）も、binding 先の終端になる。

    binding 先を trivial（無検査で通る Task Size）にして、親クラスの全ケースを回す（tip の証跡は持たせない。
    `multiple` のときは tip の証跡を持つ steering を選ぶ設計なので）。
    """

    RESUME_FROM, NEXT_ACTION = _brainstorming_discard_values()

    def setUp(self) -> None:
        super().setUp()
        bound = self._write_steering(
            self.repo, slug="20260901-bound", resume_from=self.RESUME_FROM, next_action=self.NEXT_ACTION,
            task_size="trivial", task_id="20260901-bound", worktree=self.repo, branch="main",
        )
        self._register_binding(self.repo, bound / "state.md")


class DetectNextActionOnlyCancelledBindingTests(PrePushGateFixtureMixin, unittest.TestCase):
    """binding 先の中止が `Next Action: cancelled` だけ（中止の規定の形）のとき。

    数え直さない呼び出し元（session-start・PreCompact など）には、中止した steering を作業中として渡さない。
    数え直す gate は、binding 先を候補に残す（作業中が無ければ binding 先で検査する）。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self._init_repo(self.repo)
        self._write_local_state(self.repo)

    def _status(self, *args: str) -> str:
        lib = PLUGIN_ROOT / "hooks" / "scripts" / "lib"
        result = subprocess.run(
            ["bash", "-c", 'source "$1/detect-steering.sh"; shift; gdd_detect_active_steering "$@" || true; '
             'printf "%s" "$GDD_STEERING_STATUS"', "_", str(lib), *args],
            cwd=self.repo, capture_output=True, text=True, check=True,
            env={**os.environ, "GDD_PLUGIN_ROOT": str(PLUGIN_ROOT)},
        )
        return result.stdout

    def test_cancelled_binding_is_not_handed_to_callers_that_do_not_recount(self) -> None:
        for next_action in ("cancelled", "cancelled | superseded-by: 20260924-active"):
            with self.subTest(next_action=next_action):
                bound = self._write_steering(
                    self.repo, slug="20260901-bound", resume_from="human-check-waiting", next_action=next_action,
                    task_id="20260901-bound", worktree=self.repo, branch="main",
                )
                self._register_binding(self.repo, bound / "state.md")
                self.assertEqual(self._status(), "none")
                self.assertEqual(self._status("--recount-terminal-binding"), "found")

    def test_working_binding_is_still_found(self) -> None:
        """通知しすぎない: 中止していない binding 先は、今どおり作業中として渡す。"""
        bound = self._write_steering(
            self.repo, slug="20260901-bound", resume_from="human-check-waiting", next_action="human-check-waiting",
            task_id="20260901-bound", worktree=self.repo, branch="main",
        )
        self._register_binding(self.repo, bound / "state.md")
        self.assertEqual(self._status(), "found")


class PrePushBoundStateUnreadableOrUndecidedTests(PrePushGateFixtureMixin, unittest.TestCase):
    """binding 先の終端を判定できないときは、今どおり binding 先を作業中として検査する（通さない）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self._init_repo(self.repo)
        self._write_local_state(self.repo)
        self.head = self._head_sha(self.repo)
        self.bound = self._write_steering(
            self.repo, slug="20260901-bound", task_id="20260901-bound", worktree=self.repo, branch="main",
        )
        self._register_binding(self.repo, self.bound / "state.md")
        self._write_steering(self.repo, slug="20260924-active")

    def _pushed(self) -> str:
        result = self._run_hook(
            self.repo, "git push origin main",
            extra_env={"GDD_HOOK_STATE_DIR": str(Path(self._tmp.name) / "hookstate")},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_unreadable_bound_state_is_still_gated(self) -> None:
        """例外で guard が落ちない: binding 先の state.md が読めなくても、検査せずに通さない。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        state = self.bound / "state.md"
        state.chmod(0)
        self.addCleanup(state.chmod, 0o644)
        self.assertTrue(self._pushed(), "検査されずに通った（fail-open）")

    def test_bound_state_without_next_action_is_still_gated(self) -> None:
        """判定できないときは不足として通知する: binding 先に `Next Action` が無いときは、終端にしない。"""
        state = self.bound / "state.md"
        state.write_text(
            "".join(line for line in state.read_text(encoding="utf-8").splitlines(keepends=True)
                    if not line.startswith("Next Action:")),
            encoding="utf-8",
        )
        self.assertTrue(self._pushed(), "検査されずに通った（fail-open）")



class PrePushBoundNextActionTerminalTests(PrePushGateFixtureMixin, unittest.TestCase):
    """binding 先が正規の完了の形（Resume From は done 以外・Next Action: done）でも終端とみなす。

    completion-check は Next Action だけを done にする。binding 先の終端判定が Resume From だけを
    見ると、binding 先がこの形・trivial のとき found になり、binding の無い作業中の steering が
    あっても push を検査せずに通していた。数え直すとき（pre-push・merge gate・pre-PR）だけ、
    state.md か tasklist.md の Next Action の先頭が done・cancelled でも終端とみなす。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self._init_repo(self.repo)
        self._write_local_state(self.repo)
        self.head = self._head_sha(self.repo)

    def _bind(self, *, next_action: str = "done", resume_from: str = "gdd-completion-check",
              task_size: str = "trivial", evidence: str | None = None) -> Path:
        bound = self._write_steering(
            self.repo, slug="20260901-bound", resume_from=resume_from, next_action=next_action,
            task_size=task_size, task_id="20260901-bound", worktree=self.repo, branch="main",
            evidence=evidence,
        )
        self._register_binding(self.repo, bound / "state.md")
        return bound

    _push = PrePushBoundTerminalSteeringTests._push

    _reason = PrePushTipShaResolutionTests._reason

    def test_next_action_done_binding_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: binding 先が Next Action: done・trivial でも、作業中の steering を隠さない。"""
        for next_action in ("done", "done | evidence: x"):
            with self.subTest(next_action=next_action):
                self._bind(next_action=next_action)
                self._write_steering(self.repo, slug="20260924-active")
                self.assertIn("steering-multiple", self._reason(self._push()))

    def test_next_action_cancelled_binding_stays_a_candidate_beside_the_active_one(self) -> None:
        """不足として通知すべき入力: binding 先が Next Action: cancelled でも、作業中の steering と並べて候補に
        残す（peer turn の write guard が止めない綴りの cancel でも、binding 先を検査から外さない）。"""
        self._bind(next_action="cancelled")
        self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
        self.assertIn("steering-multiple", self._reason(self._push()))

    def test_cancel_binding_without_active_steerings_is_checked_as_before(self) -> None:
        """不足として通知すべき入力: Next Action だけが cancel の binding 先は、作業中が無ければ、別の done の
        steering（trivial）があっても、数え直す前と同じく binding 先の Task Size で検査する。"""
        for next_action in ("canceled", "Canceled"):
            with self.subTest(next_action=next_action):
                self.setUp()
                self._bind(next_action=next_action, task_size="standard")
                self._write_steering(self.repo, slug="20260910-done", resume_from="done",
                                     next_action="done", task_size="trivial")
                self.assertIn("missing-evidence", self._reason(self._push()))
        self.setUp()
        self._bind(next_action="canceled", task_size="standard")
        self.assertIn("missing-evidence", self._reason(self._push()))

    def test_tasklist_only_cancel_binding_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: tasklist.md にだけ cancelled がある binding 先も候補に残す。"""
        bound = self._bind(next_action="gdd-implementation-gating", task_size="standard")
        (bound / "tasklist.md").write_text("# Task List\n\nNext Action=cancelled\n", encoding="utf-8")
        self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
        self.assertIn("steering-multiple", self._reason(self._push()))

    def test_tasklist_only_done_binding_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: Next Action: done が tasklist.md にだけある binding 先も終端とみなす。"""
        bound = self._bind()
        state = bound / "state.md"
        state.write_text(
            "".join(l + "\n" for l in state.read_text(encoding="utf-8").splitlines()
                    if not l.startswith("Next Action")),
            encoding="utf-8",
        )
        (bound / "tasklist.md").write_text("# Task List\n\nNext Action=done\n", encoding="utf-8")
        self._write_steering(self.repo, slug="20260924-active")
        self.assertTrue(self._push().stdout.strip(), "検査されずに通った（fail-open）")

    def test_unreadable_binding_state_does_not_crash_the_gate(self) -> None:
        """例外で guard が落ちない: binding 先の state.md が読めなくても、不足として通知する側の判定を出す。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        bound = self._bind()
        self._write_steering(self.repo, slug="20260924-active")
        state = bound / "state.md"
        state.chmod(0)
        self.addCleanup(state.chmod, 0o644)
        self._reason(self._push())

    def test_followup_binding_without_active_steerings_is_resolved_as_before(self) -> None:
        """followup 中の形（Next Action: done・Resume From: external-review-waiting）で作業中が無ければ、
        今どおり binding 先をその証跡で検査する。"""
        self._bind(resume_from="external-review-waiting", task_size="standard",
                   evidence=self._evidence_line(sha=self.head))
        self.assertIsNone(self._decision(self._push()))

    def test_annotated_or_cased_terminal_binding_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: 注記つき・大文字・米国綴りの終端値の binding 先（trivial）も、作業中の
        steering を隠さない（先頭の英単語を小文字にして比べる）。"""
        cases = {
            "done（PR #1 マージ済み）": "steering-multiple",
            "done (merged)": "steering-multiple",
            "Done": "steering-multiple",
            "canceled": "steering-multiple",
            "Cancelled": "steering-multiple",
            "cancelled（superseded）": "steering-multiple",
        }
        for next_action, reason in cases.items():
            with self.subTest(next_action=next_action):
                self._bind(next_action=next_action)
                self._write_steering(self.repo, slug="20260924-active")
                self.assertIn(reason, self._reason(self._push()))

    def test_done_binding_without_active_steerings_is_checked_despite_another_done_one(self) -> None:
        """作業中の steering が無ければ、別の done の steering があっても binding 先をその Task Size で
        検査する（数え直す前と同じ）。"""
        self._bind(task_size="standard")
        self._write_steering(self.repo, slug="20260910-done", resume_from="done", next_action="done")
        self.assertIn("missing-evidence", self._reason(self._push()))

    def test_stale_brainstorming_binding_is_still_checked(self) -> None:
        """不足として通知すべき入力: binding 先が stale な brainstorming でも、数え直しでは候補に残す。作業中が
        無ければ binding 先で検査し、作業中の trivial の steering と並べて数える。"""
        self._bind(resume_from="gdd-brainstorming", next_action="gdd-brainstorming", task_size="standard")
        with self.subTest(active="none"):
            reason = self._reason(self._push())
            self.assertIn("missing-evidence", reason)
            self.assertIn("使わないステアリングの終え方", reason)
        self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
        with self.subTest(active="trivial"):
            self.assertIn("steering-multiple", self._reason(self._push()))

    def test_done_binding_outside_the_steering_dir_is_still_checked(self) -> None:
        """不足として通知すべき入力: binding 先の state.md が .steering/ の外にあっても、検査せずに通さない。"""
        outside = self.repo / "elsewhere"
        outside.mkdir()
        (outside / "state.md").write_text(
            "Task ID: 20260901-outside\nResume From: external-review-waiting\nHuman Check Status: approved\n"
            "Route In Progress: none\nNext Action: done\nTask Size: standard\n"
            f"Started At: 2026-08-17T00:00:00Z\nWorktree: {self.repo}\nBranch: main\n",
            encoding="utf-8",
        )
        self._register_binding(self.repo, outside / "state.md")
        self.assertTrue(self._push().stdout.strip(), "検査されずに通った（fail-open）")

    def test_unreadable_binding_tasklist_keeps_the_binding_checked(self) -> None:
        """例外で guard が落ちない: binding 先の tasklist.md が読めなくても、binding 先を今どおり検査する。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        bound = self._bind(next_action="gdd-implementation-gating", task_size="standard")
        tasklist = bound / "tasklist.md"
        tasklist.write_text("# Task List\n\nNext Action=done\n", encoding="utf-8")
        tasklist.chmod(0)
        self.addCleanup(tasklist.chmod, 0o644)
        self.assertIn("missing-evidence", self._reason(self._push()))

    def _unreadable_tasklist_binding(self, make_unreadable) -> None:
        bound = self._bind(next_action="gdd-implementation-gating", task_size="trivial")
        make_unreadable(bound / "tasklist.md")
        self._write_steering(self.repo, slug="20260924-active")
        self.assertIn("steering-multiple", self._reason(self._push()))

    def test_unreadable_trivial_binding_tasklist_does_not_hide_the_active_one(self) -> None:
        """判定できないときに通さない: binding 先（trivial）の tasklist.md が読めなければ、done かも
        しれないものとして数え直し、binding の無い作業中の steering を隠さない。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")

        def make_unreadable(tasklist: Path) -> None:
            tasklist.write_text("# Task List\n\nNext Action=done\n", encoding="utf-8")
            tasklist.chmod(0)
            self.addCleanup(tasklist.chmod, 0o644)

        self._unreadable_tasklist_binding(make_unreadable)

    def test_non_file_binding_tasklist_does_not_hide_the_active_one(self) -> None:
        """判定できないときに通さない: binding 先（trivial）の tasklist.md がファイルでなくても同じ。"""
        self._unreadable_tasklist_binding(lambda tasklist: tasklist.mkdir())

    def _outside_binding(self, *, resume_from: str, next_action: str = "done") -> None:
        outside = self.repo / "elsewhere"
        outside.mkdir(exist_ok=True)
        (outside / "state.md").write_text(
            f"Task ID: 20260901-outside\nResume From: {resume_from}\nHuman Check Status: approved\n"
            f"Route In Progress: none\nNext Action: {next_action}\nTask Size: standard\n"
            f"Started At: 2026-08-17T00:00:00Z\nWorktree: {self.repo}\nBranch: main\n",
            encoding="utf-8",
        )
        self._register_binding(self.repo, outside / "state.md")

    def test_cancel_binding_outside_the_steering_dir_is_not_loosened_by_a_trivial_active_one(self) -> None:
        """不足として通知すべき入力: .steering/ の外の Next Action: cancelled の binding 先も、作業中の trivial の
        steering と並べて数える。"""
        self._outside_binding(resume_from="external-review-waiting", next_action="cancelled")
        self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
        self.assertIn("steering-multiple", self._reason(self._push()))

    def test_done_binding_outside_the_steering_dir_is_not_loosened_by_a_trivial_active_one(self) -> None:
        """不足として通知すべき入力: .steering/ の外の done の binding 先も、作業中の trivial の steering と並べて
        数える（作業中の Task Size だけで検査を緩めない）。"""
        for resume_from in ("external-review-waiting", "done"):
            with self.subTest(resume_from=resume_from):
                self._outside_binding(resume_from=resume_from)
                self._write_steering(self.repo, slug="20260924-active", task_size="trivial")
                self.assertIn("steering-multiple", self._reason(self._push()))

    def test_non_canonical_done_binding_without_active_steerings_is_checked_as_before(self) -> None:
        """作業中が無ければ、非正規の綴りの done の binding 先も、別の done の steering があっても
        binding 先で検査する（binding 先を作業中に数えて multiple にしない）。"""
        self._bind(next_action="done (merged)", task_size="trivial")
        self._write_steering(self.repo, slug="20260910-done", resume_from="done", next_action="done")
        self.assertIsNone(self._decision(self._push()))


if __name__ == "__main__":
    unittest.main()
