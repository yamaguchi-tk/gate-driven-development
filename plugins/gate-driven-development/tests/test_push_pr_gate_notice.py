"""pre-push gate と pre-PR gate が止めずに通し、実行後の通知と would-block の記録を残すかのテスト。

2 つの gate は不足を見つけても `{"decision": "block"}` を返さない。代わりに、同じ文を
`systemMessage` と `hookSpecificOutput.additionalContext` に入れて返し、state dir の
gate ごとのログに `would-block:<code>` を 1 行書く。code は呼び出し側が引数で渡す
（本文から切り出さない）。
"""
from __future__ import annotations

import re
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_pre_pr_gate_contract as _pr
from _paths import PLUGIN_ROOT
from _pre_push_gate_support import PrePushGateFixtureMixin

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
GATES = {
    "pre-push": SCRIPTS / "run-pre-push-gate-hook.sh",
    "pre-PR": SCRIPTS / "run-pre-pr-gate-hook.sh",
}


def _notice(test: unittest.TestCase, stdout: str, gate: str) -> str:
    """通知の JSON を 1 本だけ返していることを確かめ、通知の文を返す。"""
    lines = [line for line in stdout.splitlines() if line.strip()]
    test.assertEqual(len(lines), 1, stdout)
    payload = json.loads(lines[0])
    test.assertNotIn("decision", payload)
    specific = payload["hookSpecificOutput"]
    test.assertEqual(specific["hookEventName"], "PreToolUse")
    text = specific["additionalContext"]
    test.assertEqual(payload["systemMessage"], text)
    test.assertTrue(text.startswith(f"実行後の通知: {gate} gate は止めずに通した。"), text)
    return text


def _logged_codes(state_dir: Path, name: str) -> list[str]:
    log = state_dir / name
    if not log.exists():
        return []
    # 1 回の通知の code は、merge gate と同じくカンマでつないで 1 行に書く
    return [code
            for line in re.findall(r"\| event: would-block:([a-z0-9,-]+) \|", log.read_text(encoding="utf-8"))
            for code in line.split(",")]


class GateSourceTests(unittest.TestCase):
    def test_gates_never_return_a_block_decision(self):
        for gate, path in GATES.items():
            with self.subTest(gate=gate):
                self.assertNotIn('"decision": "block"', path.read_text(encoding="utf-8"))

    def test_every_notice_call_passes_a_code_literal(self):
        # 本文から code を切り出さないので、呼び出しごとに code を宣言して渡す
        call = re.compile(r"^\s*block\s+(\S+)\s")
        for gate, path in GATES.items():
            calls = [m.group(1) for line in path.read_text(encoding="utf-8").splitlines()
                     if (m := call.match(line))]
            with self.subTest(gate=gate):
                self.assertGreater(len(calls), 10)
                bad = [c for c in calls if not re.fullmatch(r"[a-z][a-z0-9-]*", c)]
                self.assertEqual(bad, [])


class PrePushNoticeTests(PrePushGateFixtureMixin, unittest.TestCase):
    def _push_without_evidence(self, tmp: Path, state_dir: Path):
        repo = tmp / "repo"
        repo.mkdir()
        self._init_repo(repo)
        self._write_local_state(repo, active=True)
        self._write_steering(repo, resume_from="gdd-implementation-gating",
                             next_action="gdd-implementation-gating", task_size="standard", evidence=None)
        return self._run_hook(repo, "git push origin main", extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)})

    def test_missing_evidence_is_a_notice_and_a_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "hookstate"
            result = self._push_without_evidence(Path(tmp), state_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("missing-evidence", _notice(self, result.stdout, "pre-push"))
            self.assertEqual(_logged_codes(state_dir, "pre-push-gate-suppressed.log"), ["missing-evidence"])

    def test_unwritable_record_still_returns_the_notice(self):
        # 記録先に書けなくても、通知を落とさない（黙って通さない）
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "hookstate"
            state_dir.write_text("not a directory", encoding="utf-8")
            result = self._push_without_evidence(Path(tmp), state_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("missing-evidence", _notice(self, result.stdout, "pre-push"))

    def test_unresolvable_root_is_a_notice_not_silence(self):
        # 判定できない push も、黙って通さずに通知する
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(repo, f"git --git-dir={repo}/.git push origin main",
                                    extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("unresolvable-root", _notice(self, result.stdout, "pre-push"))
            self.assertEqual(_logged_codes(state_dir, "pre-push-gate-suppressed.log"), ["unresolvable-root"])


class PrePrNoticeTests(unittest.TestCase):
    _init_repo = _pr.PrePrGateContractTests._init_repo
    _write_local_state = _pr.PrePrGateContractTests._write_local_state
    _write_steering = _pr.PrePrGateContractTests._write_steering
    _head_sha = _pr.PrePrGateContractTests._head_sha
    _independent_review_line = _pr.PrePrGateContractTests._independent_review_line
    _run_hook = _pr.PrePrGateContractTests._run_hook

    def _create(self, tmp: str, command: str, **steering):
        repo = Path(tmp) / "repo"
        repo.mkdir()
        self._init_repo(repo)
        self._write_local_state(repo)
        self._write_steering(repo, **steering)
        state_dir = Path(tmp) / "hookstate"
        return self._run_hook(repo, command, extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)}), state_dir

    def test_completion_check_not_passed_is_a_notice_and_a_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, state_dir = self._create(tmp, "gh pr create --title t --body ok",
                                             next_action="gdd-completion-check")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Next Action=gdd-completion-check", _notice(self, result.stdout, "pre-PR"))
            self.assertEqual(_logged_codes(state_dir, "pre-pr-gate-suppressed.log"), ["completion-check-missing"])

    def test_secret_candidate_asks_for_an_immediate_report(self):
        # 本文はもう GitHub に出ているので、直すだけでなく、すぐユーザーに報告させる
        with tempfile.TemporaryDirectory() as tmp:
            result, state_dir = self._create(tmp, "gh pr create --title t --body 'access_token=abcdefghijklmnop'")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = _notice(self, result.stdout, "pre-PR")
            self.assertIn("token/key/password", text)
            self.assertIn("ただちにユーザーに報告", text)
            self.assertEqual(_logged_codes(state_dir, "pre-pr-gate-suppressed.log"), ["body-secret-candidate"])

    def test_secret_candidate_is_reported_before_completion_check(self):
        # completion-check の前に PR を作っても、機密候補の通知を落とさない
        with tempfile.TemporaryDirectory() as tmp:
            result, state_dir = self._create(tmp, "gh pr create --title t --body 'access_token=abcdefghijklmnop'",
                                             next_action="gdd-completion-check")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = _notice(self, result.stdout, "pre-PR")
            self.assertIn("ただちにユーザーに報告", text)
            self.assertIn("Next Action=gdd-completion-check", text)
            self.assertEqual(_logged_codes(state_dir, "pre-pr-gate-suppressed.log"),
                             ["body-secret-candidate", "completion-check-missing"])

    def test_secret_candidate_is_reported_when_steering_is_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo)
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(repo, "gh pr create --title t --body 'access_token=abcdefghijklmnop'",
                                    extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ただちにユーザーに報告", _notice(self, result.stdout, "pre-PR"))
            self.assertEqual(_logged_codes(state_dir, "pre-pr-gate-suppressed.log"),
                             ["body-secret-candidate", "steering-unresolved"])

    def test_every_shortfall_is_in_one_notice(self):
        # pre-PR gate は PR 1 本につき 1 回しか走らないので、最初の不足だけで終えない
        with tempfile.TemporaryDirectory() as tmp:
            result, state_dir = self._create(tmp, "gh pr create --title t --body ok",
                                             next_action="gdd-completion-check", adr_distilled="")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = _notice(self, result.stdout, "pre-PR")
            self.assertEqual(text.count("実行後の通知"), 1)
            self.assertIn("Next Action=gdd-completion-check", text)
            self.assertIn("ADR蒸留状況を確認できません", text)
            self.assertEqual(_logged_codes(state_dir, "pre-pr-gate-suppressed.log"),
                             ["completion-check-missing", "adr-status-unknown"])

    def test_a_later_crash_keeps_the_earlier_notice(self):
        # 通知を最後にまとめて出すので、後段の 1 コマンドの失敗で前段の不足を消さない
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "scripts"
            shutil.copytree(SCRIPTS, scripts)
            (scripts / "lib" / "merge-gate-evidence.sh").write_text("return 1\n", encoding="utf-8")
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check", task_size="standard",
                                 adr_distilled="yes")
            state_dir = Path(tmp) / "hookstate"
            env = os.environ.copy()
            env.update({"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "GDD_PLUGIN_ROOT": str(PLUGIN_ROOT),
                        "CLAUDE_CODE_SESSION_ID": "test-session",
                        "GDD_HOOK_STATE_DIR": str(state_dir)})
            payload = {"tool_name": "Bash", "tool_input": {"command": "gh pr create --title t --body ok"}}
            result = subprocess.run(["bash", str(scripts / "run-pre-pr-gate-hook.sh")], cwd=repo,
                                    input=json.dumps(payload), capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Next Action=gdd-completion-check", _notice(self, result.stdout, "pre-PR"))
            self.assertEqual(_logged_codes(state_dir, "pre-pr-gate-suppressed.log"),
                             ["completion-check-missing", "adr-missing-in-diff", "missing-evidence"])


if __name__ == "__main__":
    unittest.main()
