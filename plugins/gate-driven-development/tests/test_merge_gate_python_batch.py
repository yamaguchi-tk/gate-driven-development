"""merge gate の hook が python3 を起こす回数を減らした形の契約。

- 時刻: `gdd_parse_merge_gate_field` が検証のときに作った epoch を `GDD_MG_AT_EPOCH`・
  `GDD_MG_APPROVED_AT_EPOCH` で返し、hook はそれを使い回す（経過は `date -u +%s` との引き算）
- cwd: `tool_input` の cwd は、コマンドの解析と同じ埋め込みの python が `payload_cwd` で出す
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _merge_gate_input_classes import _SOURCE as EMBEDDED_PARSER
from _merge_gate_support import (
    HANG_GUARD,
    HOOK_SCRIPT,
    LIB_DIR,
    PLUGIN_ROOT,
    _approval_line,
    _head_sha,
    _init_named_repo,
    _init_repo,
    _new_repo_with_marker_and_pr,
    _run_hook,
    _valid_evidence_lines,
    _write_state,
)

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.constants import (  # noqa: E402
    MERGE_GATE_APPROVAL_FRESHNESS_MINUTES,
    MERGE_GATE_RECHECK_FRESHNESS_MINUTES,
)

_PYTHON3 = shutil.which("python3")


def _epoch(iso: str) -> str:
    return str(int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()))


def _parse_fields(lines: list[tuple[str, str]], path_prefix: str = "") -> dict:
    """field を順に parse し、最後の parse の後の出力変数を返す（`set -u` で未定義なら落ちる）。"""
    script = f"""
set -euo pipefail
source '{LIB_DIR}/merge-gate-evidence.sh'
STATE_FILE="$(mktemp)"
printf '%s\\n' "$@" > "$STATE_FILE"
for _f in {" ".join(f"'{name}'" for name, _ in lines)}; do
  gdd_parse_merge_gate_field "$STATE_FILE" "$_f" "2026-01-01T00:00:00Z"
done
printf 'valid=%s\\nreason=%s\\nat_epoch=%s\\napproved_epoch=%s\\n' \\
  "$GDD_MG_VALID" "$GDD_MG_REASON" "$GDD_MG_AT_EPOCH" "$GDD_MG_APPROVED_AT_EPOCH"
"""
    env = dict(os.environ)
    if path_prefix:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"
    proc = subprocess.run(
        ["bash", "-c", script, "_", *[f"- {name}: {value}" for name, value in lines]],
        capture_output=True, text=True, timeout=HANG_GUARD, env=env,
    )
    if proc.returncode != 0:
        raise AssertionError(f"parse が落ちた: {proc.stderr}")
    return dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)


class EvidenceEpochTests(unittest.TestCase):
    AT = "2026-01-01T00:05:00Z"

    def test_parser_returns_the_epoch_of_the_validated_at(self):
        out = _parse_fields([("Pre-Merge Review Recheck", f"abc1234 | new_blocking: 0 | at: {self.AT}")])
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["at_epoch"], _epoch(self.AT))
        self.assertEqual(out["approved_epoch"], "")

    def test_parser_returns_the_epoch_of_the_validated_approved_at(self):
        at = "2026-01-01T09:05:00+09:00"
        out = _parse_fields([("Merge Approval", f"PR #7 / head abc1234 | evidence: x | approved_at: {at}")])
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["approved_epoch"], _epoch(at))

    def test_an_invalid_field_after_a_valid_one_leaves_no_epoch(self):
        # 前の parse の epoch が残ると、後の field の鮮度を前の時刻で判定してしまう
        out = _parse_fields([
            ("Merge Approval", f"PR #7 / head abc1234 | evidence: x | approved_at: {self.AT}"),
            ("Pre-Merge Review Recheck", f"abc1234 | new_blocking: 0 | at: {self.AT}"),
            ("Bot Review Received", "abc1234 | received: yes | at: 2026-01-01T00:05:00"),
        ])
        self.assertEqual((out["valid"], out["reason"]), ("false", "malformed"))
        self.assertEqual((out["at_epoch"], out["approved_epoch"]), ("", ""))

    def test_a_failing_time_conversion_is_malformed_not_valid(self):
        # 時刻を変換できない（python3 が落ちる）ときは、epoch の無いまま valid にしない
        shim = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, shim, True)
        (shim / "python3").write_text("#!/bin/sh\nexit 1\n")
        (shim / "python3").chmod(0o755)
        out = _parse_fields(
            [("Pre-Merge Review Recheck", f"abc1234 | new_blocking: 0 | at: {self.AT}")],
            path_prefix=str(shim))
        self.assertEqual((out["valid"], out["reason"], out["at_epoch"]), ("false", "malformed", ""))


def _decode_payload_cwd(payload_text: str) -> str:
    """埋め込みの python の出力を、hook の read ループの `payload_cwd` の行と同じ形で戻す（値が無ければ空）。"""
    arm = re.search(r"^\s*payload_cwd\) (.*;;)$", HOOK_SCRIPT.read_text(encoding="utf-8"), re.M)
    assert arm is not None, "hook の read ループに payload_cwd の行が無い"
    # hook と同じく `set -u` で回す（空の値で変数が消えると、hook ごと落ちて素通りになる）
    script = f"""
set -euo pipefail
PAYLOAD_CWD=""
while IFS=$'\\t' read -r _k _v; do
  case "$_k" in
    payload_cwd) {arm.group(1)}
  esac
done < <(printf '%s' "$1" | python3 -I -X utf8 -c "$2" '{LIB_DIR}' "$PWD" 2>/dev/null || true)
printf '%sx' "$PAYLOAD_CWD"
"""
    proc = subprocess.run(["bash", "-c", script, "_", payload_text, EMBEDDED_PARSER],
                          capture_output=True, timeout=HANG_GUARD)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout[:-1].decode("utf-8", "surrogateescape")


def _expected_cwd(payload_text: str) -> str | None:
    """以前の抽出（hook が別の python3 で読んでいた形）が bash に渡していた値。NUL は bash が落とす。"""
    try:
        d = json.loads(payload_text).get("tool_input", {})
        line = str(d.get("cwd") or d.get("workdir") or "")
    except Exception:
        return None
    try:
        data = line.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        data = line.encode("utf-8", "backslashreplace")
    return data.replace(b"\0", b"").decode("utf-8", "surrogateescape")


class PayloadCwdFromTheParserTests(unittest.TestCase):
    CWDS = [
        "/work/repo", "relative/dir", "", "/a/b\n", "/a\nb", "/a\tb", "/a\rb", "/a\\b",
        "/a\\x41", "/a\\c", "/a\\0101", "/a%b", "/a\0b", "/日本語", "/a\ud800", "/a\udc80",
        "/trailing ", " /leading", "/a\x1eb\x1f",
        # エスケープの直後に数字・16 進の文字が続く値（書き方の桁の境目で読み違えない）
        "/a\n1", "/a\n0123", "/a\\7", "/a\t012", "/a\rff", "/a\\x41\n7",
    ]

    def _payloads(self):
        for cwd in self.CWDS:
            yield {"tool_input": {"command": "gh pr merge 7", "cwd": cwd}}
        yield {"tool_input": {"command": "gh pr merge 7", "workdir": "/w\nd"}}
        yield {"tool_input": {"command": "gh pr merge 7", "cwd": "", "workdir": "/w"}}
        yield {"tool_input": {"command": "gh pr merge 7", "cwd": 123}}
        yield {"tool_input": {"command": "gh pr merge 7", "cwd": ["/x", "y"]}}
        yield {"tool_input": {"command": "gh pr merge 7"}}
        yield {"tool_input": "not a dict"}
        yield {"tool_input": {"command": 123, "cwd": "/still/read"}}
        yield ["not", "a", "dict"]

    def test_the_parser_passes_the_same_cwd_as_the_old_extraction(self):
        texts = [json.dumps(p) for p in self._payloads()] + ['{"tool_input": {"cwd": "/x"', ""]
        for text in texts:
            with self.subTest(payload=text):
                expected = _expected_cwd(text)
                got = _decode_payload_cwd(text)
                self.assertEqual(got or "", expected or "")

    def test_the_cwd_is_read_even_when_the_command_parse_fails(self):
        # 解析が例外で落ちても、cwd は今までどおり bash に届く（実行先の検査を素通りさせない）
        self.assertEqual(_decode_payload_cwd(json.dumps(
            {"tool_input": {"command": 123, "cwd": "/still/read"}})), "/still/read")


class HookLaunchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)
        self.shim = self.tmp / "shim"
        self.shim.mkdir()
        self.log = self.tmp / "python3.log"
        (self.shim / "python3").write_text(
            "#!/bin/bash\n"
            f"printf '%s\\0' \"$*\" >> '{self.log}'\n"
            f"exec '{_PYTHON3}' \"$@\"\n")
        (self.shim / "python3").chmod(0o755)

    def _run(self, payload):
        result = _run_hook(payload, self.repo, self.home,
                           extra_env={"PATH": f"{self.shim}:{os.environ['PATH']}"})
        calls = self.log.read_bytes().decode().split("\0")[:-1] if self.log.exists() else []
        return result, calls

    def _merge(self, **tool_input):
        return self._run({"tool_input": {"command": "gh pr merge 7", **tool_input}})

    def test_an_allowed_merge_reads_the_payload_and_each_time_once(self):
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        result, calls = self._merge()
        # hook が落ちても通知は出ないので、終了コードと空の出力で allow を確かめる
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(sum("tool_input" in c for c in calls), 1, "PAYLOAD を読む python3 は 1 回")
        self.assertEqual(sum("at_dt" in c for c in calls), 0, "経過の計算に python3 を起こさない")
        times = [c.rsplit(" ", 1)[-1] for c in calls if "fromisoformat" in c]
        # 承認・Recheck・Last Review Push At（＋ HEAD の committer date）・Bot Review Received で 1 回ずつ
        self.assertLessEqual(len(times), 5, times)

    def test_a_stale_approval_is_still_reported_with_the_elapsed_minutes(self):
        lines = _valid_evidence_lines(self.head)
        lines[0] = _approval_line(7, self.head, minutes_ago=MERGE_GATE_APPROVAL_FRESHNESS_MINUTES + 3)
        _write_state(self.repo, active=False, extra_lines=lines)
        result, _ = self._merge()
        self.assertIn("reason code: approval-stale", result.stdout)
        self.assertRegex(result.stdout, rf"経過 ({MERGE_GATE_APPROVAL_FRESHNESS_MINUTES + 2}|{MERGE_GATE_APPROVAL_FRESHNESS_MINUTES + 3}) 分")

    def _recheck_at(self, at: datetime):
        lines = _valid_evidence_lines(self.head)
        lines[1] = (f"- Pre-Merge Review Recheck: {self.head} | new_blocking: 0 | "
                    f"at: {at.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        _write_state(self.repo, active=False, extra_lines=lines)
        return self._merge()[0]

    def test_a_stale_or_future_recheck_is_still_reported(self):
        now = datetime.now(timezone.utc)
        for label, at, minutes in (
            ("stale", now - timedelta(minutes=MERGE_GATE_RECHECK_FRESHNESS_MINUTES + 2),
             rf"経過 {MERGE_GATE_RECHECK_FRESHNESS_MINUTES + 2} 分"),
            ("future", now + timedelta(minutes=5), r"経過 0 分"),
        ):
            with self.subTest(label):
                result = self._recheck_at(at)
                self.assertIn("recheck-stale", result.stdout)
                self.assertRegex(result.stdout, minutes)

    def test_an_unresolvable_payload_cwd_with_escapes_is_still_reported(self):
        # 改行・バックスラッシュ・tab を含む実行先が届いたのに解決できないときは、検査を素通りしない
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        for cwd in ("/no/such\\x41dir", "/no/such\ndir\n", "/no\tsuch"):
            with self.subTest(cwd=cwd):
                result, _ = self._merge(cwd=cwd)
                self.assertIn("reason code: pr-target-unresolvable", result.stdout)


class BrokenParserLibTests(unittest.TestCase):
    """`lib/gh_command_parse.py` を import できなくても、payload の cwd は届き、解析の失敗として知らせる。

    プロセスの cwd は marker の無い git repo にする（git でないと repo の解決で先に引っかかり、cwd の欠けを踏めない）。
    """

    def _run(self, payload, break_module):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            outside = _init_named_repo(root, "outside")
            target = _new_repo_with_marker_and_pr(root, "widgets", pr=7)
            hooks = root / "plugin" / "hooks"
            shutil.copytree(PLUGIN_ROOT / "hooks", hooks)
            break_module(hooks / "scripts" / "lib" / "gh_command_parse.py")
            payload = json.loads(json.dumps(payload).replace("@TARGET@", str(target)))
            env = {k: v for k, v in os.environ.items()
                   if k not in ("GH_HOST", "GH_REPO", "GDD_HOOK_STATE_DIR")}
            env.update(HOME=str(home), CLAUDE_PLUGIN_ROOT=str(root / "plugin"),
                       CLAUDE_CODE_SESSION_ID="test-session")
            return subprocess.run(
                ["bash", str(hooks / "scripts" / "run-merge-gate-hook.sh")],
                input=json.dumps(payload), capture_output=True, text=True,
                env=env, cwd=str(outside), timeout=HANG_GUARD)

    def test_the_payload_cwd_reaches_the_gate_when_the_parser_lib_is_broken(self):
        payloads = {
            "tool_cwd": {"tool_input": {"command": "gh pr merge 7", "cwd": "@TARGET@"}},
            "workdir": {"tool_input": {"command": "gh pr merge 7", "workdir": "@TARGET@"}},
            "top_cwd": {"cwd": "@TARGET@", "tool_input": {"command": "gh pr merge 7"}},
        }
        breakers = {
            "missing": lambda path: path.unlink(),
            "syntax-error": lambda path: path.write_text("def (:\n", encoding="utf-8"),
        }
        for via, payload in payloads.items():
            for label, breaker in breakers.items():
                with self.subTest(via=via, lib=label):
                    result = self._run(payload, breaker)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("reason code: parse-error", result.stdout)


if __name__ == "__main__":
    unittest.main()
