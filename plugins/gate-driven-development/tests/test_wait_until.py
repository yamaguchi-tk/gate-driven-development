"""scripts/wait-until.py: 処理待ち（CI・レビュー bot のレビュー・デプロイ）を上限つきで待つスクリプト。

条件コマンドの終了コードは 0 = 成立、1 = まだ、それ以外 = 条件が壊れている（待たずに exit 2）。
全体の期限を過ぎたら exit 124。`--pr-checks` は条件を書かせずに PR の CI を待つ。
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN / "scripts" / "wait-until.py"
FINAL_RE = re.compile(
    r"^wait-until: result=(?P<result>met|timeout|broken) elapsed=(?P<elapsed>\d+) checks=(?P<checks>\d+) "
    r"last_exit=(?P<last_exit>-?\d+|none) last_stdout=(?P<last_stdout>.*)$"
)


def _run(*args: str, env: dict[str, str] | None = None, timeout: float = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=timeout, env={**os.environ, **(env or {})},
    )


def _final(out: str) -> re.Match:
    last = out.rstrip("\n").splitlines()[-1]
    match = FINAL_RE.match(last)
    if match is None:
        raise AssertionError(f"最終行の形が違う: {last!r}")
    return match


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _wait_dead(pid: int, seconds: float = 5) -> bool:
    end = time.time() + seconds
    while time.time() < end:
        if not _pid_alive(pid):
            return True
        time.sleep(0.05)
    return False


class _Tmp(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()


class GenericConditionTest(_Tmp):
    def test_met_on_first_check(self) -> None:
        proc = _run("--timeout", "60", "--", "sh", "-c", "echo ok; exit 0")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        final = _final(proc.stdout)
        self.assertEqual(final["result"], "met")
        self.assertEqual(final["checks"], "1")
        self.assertEqual(final["last_exit"], "0")
        self.assertEqual(final["last_stdout"], "ok")

    def test_not_yet_then_met_records_each_observation(self) -> None:
        counter = self.ws / "n"
        cond = f"n=$(cat '{counter}' 2>/dev/null || echo 0); n=$((n+1)); echo $n > '{counter}'; echo n=$n; [ $n -ge 2 ]"
        proc = _run("--timeout", "2", "--interval", "10", "--", "sh", "-c", cond)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertRegex(proc.stdout, r"(?m)^wait-until: check=1 elapsed=\d+ exit=1 stdout=n=1$")
        final = _final(proc.stdout)
        self.assertEqual((final["result"], final["checks"], final["last_stdout"]), ("met", "2", "n=2"))

    def test_timeout_exits_124_with_last_observation(self) -> None:
        proc = _run("--timeout", "1", "--", "sh", "-c", "echo waiting; exit 1")
        self.assertEqual(proc.returncode, 124, proc.stdout + proc.stderr)
        final = _final(proc.stdout)
        self.assertEqual((final["result"], final["last_exit"], final["last_stdout"]), ("timeout", "1", "waiting"))

    def test_other_exit_code_is_broken_without_waiting(self) -> None:
        started = time.time()
        proc = _run("--timeout", "60", "--", "sh", "-c", "echo partial; echo 'gh: unknown flag' >&2; exit 3")
        self.assertLess(time.time() - started, 10)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        final = _final(proc.stdout)
        self.assertEqual((final["result"], final["last_exit"], final["checks"]), ("broken", "3", "1"))
        self.assertIn("wait-until: stderr=gh: unknown flag", proc.stdout)

    def test_killed_condition_is_broken(self) -> None:
        proc = _run("--timeout", "60", "--", "sh", "-c", "kill -9 $$")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(_final(proc.stdout)["result"], "broken")

    def test_missing_command_is_broken(self) -> None:
        proc = _run("--timeout", "60", "--", str(self.ws / "no-such-command"))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(_final(proc.stdout)["result"], "broken")

    def test_hanging_check_is_broken_and_its_group_is_killed(self) -> None:
        pidfile = self.ws / "grandchild"
        started = time.time()
        proc = _run("--timeout", "60", "--check-timeout", "1", "--",
                    "sh", "-c", f"sleep 30 & echo $! > '{pidfile}'; wait")
        self.assertLess(time.time() - started, 15)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(_final(proc.stdout)["result"], "broken")
        self.assertTrue(_wait_dead(int(pidfile.read_text().strip())), "孫のプロセスが残っている")

    def test_hanging_check_outside_its_group_still_ends(self) -> None:
        # 別のプロセスグループに移った子（set -m の job、GNU timeout など）が pipe を持ったまま残っても、上限で終わる
        pidfile = self.ws / "outside"
        started = time.time()
        proc = _run("--timeout", "60", "--check-timeout", "1", "--",
                    "bash", "-c", f"set -m; sleep 30 & echo $! $$ > '{pidfile}'; wait")
        pid, bash_pid = map(int, pidfile.read_text().split())
        try:
            self.assertLess(time.time() - started, 15)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(_final(proc.stdout)["result"], "broken")
            # 条件のグループを止めた後も生きている = 子は本当に別のグループにいた（このテストの前提）
            self.assertTrue(_pid_alive(pid), "子が条件のグループごと止まった（別グループの前提が成り立たない）")
            # 条件のグループの番号は、新しいセッションの先頭の bash の pid と同じ
            self.assertNotEqual(os.getpgid(pid), bash_pid)
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_condition_does_not_inherit_stdin(self) -> None:
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "--timeout", "60", "--check-timeout", "5", "--",
             "sh", "-c", 'read x; echo "got=$x"; exit 0'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            out, err = proc.communicate(timeout=4)  # stdin は閉じない（受け継いでいれば read が待つ）
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            self.fail("条件コマンドが stdin を受け継いで待った")
        self.assertEqual(proc.returncode, 0, out + err)
        self.assertEqual(_final(out)["last_stdout"], "got=")

    def test_observations_are_flushed_while_waiting(self) -> None:
        log = self.ws / "out.txt"
        with log.open("w") as fh:
            proc = subprocess.Popen([sys.executable, str(SCRIPT), "--timeout", "4", "--", "sh", "-c", "echo pending; exit 1"],
                                    stdout=fh, stderr=subprocess.STDOUT)
            try:
                time.sleep(1.5)
                self.assertIn("wait-until: check=1 ", log.read_text())
            finally:
                proc.wait(timeout=15)
        self.assertEqual(proc.returncode, 124)

    def test_sigterm_stops_the_running_check(self) -> None:
        pidfile = self.ws / "child"
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "--timeout", "60", "--check-timeout", "60", "--",
             "sh", "-c", f"echo $$ > '{pidfile}'; sleep 30"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        end = time.time() + 5
        while not pidfile.exists() and time.time() < end:
            time.sleep(0.05)
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=10)
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(_wait_dead(int(pidfile.read_text().strip())), "条件コマンドが残っている")


class ArgumentTest(_Tmp):
    """引数を読めないときは、条件を 1 回も実行せずに exit 2 で終わる。"""

    def _assert_rejected(self, *args: str) -> None:
        marker = self.ws / "ran"
        proc = _run(*args, "--", "sh", "-c", f"touch '{marker}'; exit 0")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertFalse(marker.exists(), "条件が実行された")

    def test_timeout_is_required(self) -> None:
        self._assert_rejected()

    def test_bad_values_are_rejected_not_clamped(self) -> None:
        cases = [
            ("--timeout", "0"), ("--timeout", "-5"), ("--timeout", "7201"), ("--timeout", "abc"), ("--timeout", "1.5"),
            ("--timeout", "60", "--interval", "9"), ("--timeout", "60", "--interval", "x"),
            ("--timeout", "60", "--check-timeout", "0"), ("--timeout", "60", "--check-timeout", "601"),
        ]
        for case in cases:
            with self.subTest(case=case):
                self._assert_rejected(*case)

    def test_pr_checks_and_command_are_exclusive(self) -> None:
        self._assert_rejected("--timeout", "60", "--pr-checks", "42")

    def test_needs_a_condition(self) -> None:
        proc = _run("--timeout", "60")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)

    def test_pr_number_must_be_positive_integer(self) -> None:
        env = _fake_gh(self.ws / "bin", _pr(SUCCESS))
        for value in ("0", "-1", "abc", "4.2"):
            with self.subTest(value=value):
                proc = _run("--timeout", "60", "--pr-checks", value, env=env)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertNotIn("wait-until: result=", proc.stdout)
                self.assertFalse((self.ws / "bin" / "gh-args").exists(), "gh が呼ばれた")

    def test_repo_without_pr_checks_is_rejected(self) -> None:
        self._assert_rejected("--timeout", "60", "-R", "o/r")


def _fake_gh(bindir: Path, payload: object, rc: int = 0) -> dict[str, str]:
    bindir.mkdir(parents=True, exist_ok=True)
    out = bindir / "gh-out.json"
    out.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
    script = bindir / "gh"
    script.write_text(f"#!/bin/sh\necho \"$@\" >> '{bindir}/gh-args'\ncat '{out}'\nexit {rc}\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"}


def _pr(checks: object, head: str = "abc123def4567890") -> dict:
    return {"state": "OPEN", "headRefOid": head, "statusCheckRollup": checks}


PENDING = [{"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": ""}]
SUCCESS = [{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"}]
FAILURE = [{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "FAILURE"}]


class PrChecksTest(_Tmp):
    def _run_pr(self, payload: object, *extra: str, rc: int = 0, timeout: str = "60") -> subprocess.CompletedProcess:
        env = _fake_gh(self.ws / "bin", payload, rc)
        return _run("--timeout", timeout, "--pr-checks", "42", *extra, env=env)

    def test_success_is_met(self) -> None:
        proc = self._run_pr(_pr(SUCCESS), "-R", "o/r")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        final = _final(proc.stdout)
        self.assertEqual((final["result"], final["last_stdout"]), ("met", "state=OPEN ci=success any_failure=no head=abc123def456"))
        args = (self.ws / "bin" / "gh-args").read_text(encoding="utf-8")
        self.assertIn("pr view 42 --json state,headRefOid,statusCheckRollup -R o/r", args)

    def test_failure_is_met_and_reported(self) -> None:
        # CI が終わったことが待つ条件。結果（failure）は最終行で返し、直すかは main が決める
        proc = self._run_pr(_pr(FAILURE))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_final(proc.stdout)["last_stdout"], "state=OPEN ci=failure any_failure=yes head=abc123def456")

    def test_pending_waits_until_timeout(self) -> None:
        proc = self._run_pr(_pr(PENDING), timeout="1")
        self.assertEqual(proc.returncode, 124, proc.stdout + proc.stderr)
        self.assertEqual(_final(proc.stdout)["last_stdout"], "state=OPEN ci=pending any_failure=no head=abc123def456")

    def test_failure_with_pending_checks_keeps_waiting(self) -> None:
        # 1 つが failure でも、ほかが pending の間は CI が終わっていないので待つ。出ている failure は観測に残す
        proc = self._run_pr(_pr(SUCCESS + FAILURE + PENDING), timeout="1")
        self.assertEqual(proc.returncode, 124, proc.stdout + proc.stderr)
        self.assertEqual(_final(proc.stdout)["last_stdout"], "state=OPEN ci=pending any_failure=yes head=abc123def456")

    def test_closed_or_merged_pr_ends_even_with_pending_checks(self) -> None:
        for state in ("MERGED", "CLOSED"):
            with self.subTest(state=state):
                proc = self._run_pr({**_pr(PENDING), "state": state})
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                final = _final(proc.stdout)
                self.assertEqual((final["result"], final["last_stdout"]), ("met", f"state={state} ci=pending any_failure=no head=abc123def456"))

    def test_head_with_control_characters_stays_on_one_line(self) -> None:
        proc = self._run_pr(_pr(SUCCESS, head="abc\nresult=met x"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(len(proc.stdout.splitlines()), 2, proc.stdout)
        self.assertNotIn("\n", _final(proc.stdout)["last_stdout"])

    def test_gh_error_is_broken(self) -> None:
        proc = self._run_pr("", rc=1)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(_final(proc.stdout)["result"], "broken")

    def test_unreadable_view_is_broken(self) -> None:
        for payload in ("not json", "[]", json.dumps({"state": "OPEN", "statusCheckRollup": "x"}),
                        json.dumps(_pr([1])), json.dumps({**_pr(SUCCESS), "state": None})):
            with self.subTest(payload=payload):
                proc = self._run_pr(payload)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertEqual(_final(proc.stdout)["result"], "broken")


def _load_module():
    spec = importlib.util.spec_from_file_location("wait_until_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UnexpectedErrorTest(_Tmp):
    """確認の中の予期しない例外も、traceback で落ちずに broken の最終行で終わる。"""

    def test_exception_in_check_is_broken_with_final_line(self) -> None:
        cases = (("_check_command", ["--timeout", "60", "--", "true"]),
                 ("_check_pr", ["--timeout", "60", "--pr-checks", "42"]))
        for target, argv in cases:
            for message in ("boom", "first\nlast"):
                with self.subTest(target=target, message=message):
                    module = _load_module()
                    buf = io.StringIO()
                    with mock.patch.object(module, target, side_effect=RuntimeError(message)), redirect_stdout(buf):
                        code = module.main(argv)
                    self.assertEqual(code, 2, buf.getvalue())
                    self.assertEqual(_final(buf.getvalue())["result"], "broken")
                    self.assertIn("wait-until: stderr=RuntimeError: ", buf.getvalue())

    def test_unkillable_check_does_not_block_past_the_drain(self) -> None:
        # グループを止められない（EPERM・D state など）とき、止めた確認の終わりを待ち続けない
        module = _load_module()
        pidfile = self.ws / "pids"
        buf = io.StringIO()
        started = time.time()
        try:
            with mock.patch.object(module, "_kill_group", lambda proc: None), redirect_stdout(buf):
                code = module.main(["--timeout", "60", "--check-timeout", "1", "--",
                                    "bash", "-c", f"echo $$ > '{pidfile}'; sleep 30 & echo $! >> '{pidfile}'; wait"])
            self.assertLess(time.time() - started, 15)
            self.assertEqual(code, 2, buf.getvalue())
            self.assertEqual(_final(buf.getvalue())["result"], "broken")
        finally:
            for line in pidfile.read_text().split():
                try:
                    os.kill(int(line), signal.SIGKILL)
                except ProcessLookupError:
                    pass


class NoChecksGraceTest(_Tmp):
    """checks が登録されない状態が続いたら、待つ条件が成立しえないものとして止める。"""

    def _main(self, grace: int, timeout: str) -> tuple[int, str]:
        module = _load_module()
        env = _fake_gh(self.ws / "bin", _pr([]))
        buf = io.StringIO()
        with mock.patch.dict(os.environ, env), mock.patch.object(module, "NO_CHECKS_GRACE_SECONDS", grace), \
                redirect_stdout(buf):
            code = module.main(["--timeout", timeout, "--pr-checks", "42"])
        return code, buf.getvalue()

    def test_no_checks_past_grace_is_broken(self) -> None:
        code, out = self._main(0, "60")
        self.assertEqual(code, 2, out)
        final = _final(out)
        self.assertEqual((final["result"], final["last_stdout"]), ("broken", "state=OPEN ci=no-checks any_failure=no head=abc123def456"))

    def test_no_checks_within_grace_keeps_waiting(self) -> None:
        code, out = self._main(600, "1")
        self.assertEqual(code, 124, out)


class CiStateSharedTest(unittest.TestCase):
    """CI の分類は Stop hook のマージ待ちの押し返しと同じ実装を使う（受理する集合をそろえる）。"""

    def test_script_and_pushback_use_the_same_function(self) -> None:
        sys.path.insert(0, str(PLUGIN / "hooks" / "scripts"))
        from lib import autonomy_pushback, ci_state  # noqa: PLC0415

        self.assertIs(autonomy_pushback._ci_state, ci_state.ci_state)
        script_impl = Path(_load_module().ci_state.__code__.co_filename).resolve()
        self.assertEqual(script_impl, Path(ci_state.__file__).resolve())

    def test_classification(self) -> None:
        sys.path.insert(0, str(PLUGIN / "hooks" / "scripts"))
        from lib.ci_state import ci_state  # noqa: PLC0415

        cases = [
            (SUCCESS, "success"), (FAILURE, "failure"), (PENDING, "pending"), ([], "no-checks"),
            (SUCCESS + PENDING, "pending"), (SUCCESS + FAILURE + PENDING, "failure"),
            ([{"state": "SUCCESS"}], "success"), ([{"state": "EXPECTED"}], "pending"), ([{"state": "ERROR"}], "failure"),
            ([{"status": "COMPLETED", "conclusion": "SKIPPED"}], "success"),
            ("x", None), ([1], None), (None, None),
        ]
        for rollup, expected in cases:
            with self.subTest(rollup=rollup):
                self.assertEqual(ci_state(rollup), expected)


if __name__ == "__main__":
    unittest.main()
