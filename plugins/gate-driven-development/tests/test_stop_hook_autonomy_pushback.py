"""Stop hook が、宣言された自律の範囲の中で止まったときに 1 回だけ押し返す（lib/autonomy_pushback.py）。

- A: bind 済み steering の worklog.md に `事前回答:` 行があるのに human-check-waiting で止まった
- B: `.claude/gdd-merge-intent.json`（マージ待ちの宣言）があるのに、PR が OPEN のまま止まった
- C: 宣言が無いのに、最後の発言が「CI が通ったらマージします」の形で止まった

どれも、読めない・判定できないときは押し返さない（今までどおり止まる側に倒す）。
"""
from __future__ import annotations

import json
import os
import re
import importlib
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"))

from _stop_hook_test_base import (
    _make_transcript_jsonl,
    _run_hook,
    _write_binding,
    _write_state_file,
    _write_steering,
)
from _timing_budget import hang_guard_seconds, hook_timeout_seconds, timing_budget

STOP_HOOK_TIMEOUT = hook_timeout_seconds("run-gdd-stop-hook.sh")
STOP_HANG_GUARD = hang_guard_seconds("run-gdd-stop-hook.sh")

SLUG = "20261003-sample"
HITL_STOP = (
    "## 🔍 確認をお願いします\n承認ポイント: ...\n"
    '<gdd-stop reason="human-check-waiting">\n\n## 👤 次にすること\nOKで承認してください'
)
PRE_ANSWER = (
    "事前回答: 2026-10-03T01:00+09:00 / 対象: この steering / 自走上限: マージまで / "
    "委任先: fable / 人に戻す条件: なし / 原文: 「Fable に相談しながら進めて。マージして良い」"
)


def _blocked(out: str) -> dict | None:
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("{"):
            payload = json.loads(line)
            if payload.get("decision") == "block":
                return payload
    return None


def _fake_gh(bindir: Path, payload: dict | None, rc: int = 0) -> dict[str, str]:
    """PATH の先頭に置く偽の gh。`gh pr view` に payload を返し、引数を gh-args に残す。"""
    bindir.mkdir(parents=True, exist_ok=True)
    out = bindir / "gh-out.json"
    out.write_text(json.dumps(payload) if payload is not None else "", encoding="utf-8")
    script = bindir / "gh"
    script.write_text(
        f"#!/bin/sh\necho \"$@\" >> '{bindir}/gh-args'\ncat '{out}'\nexit {rc}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"}


def _pr(state: str = "OPEN", head: str = "abc123", checks: list[dict] | None = None) -> dict:
    return {"state": state, "headRefOid": head, "statusCheckRollup": checks or []}


PENDING = [{"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": ""}]
SUCCESS = [{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"}]
FAILURE = [{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "FAILURE"}]


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name).resolve()
        self.transcript = self.ws / "transcript.jsonl"
        self.env = _fake_gh(self.ws / "bin", None, rc=1)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _gdd_active(self) -> None:
        _write_state_file(self.ws, {"active": "true", "session_id": "test-session", "iteration": "1"})

    def _steering(self, worklog: str | None) -> Path:
        steering = _write_steering(self.ws, SLUG, "# Tasklist\n")
        _write_binding(self.ws, SLUG)
        if worklog is not None:
            (steering / "worklog.md").write_text(worklog, encoding="utf-8")
        return steering

    def _stop(self, text: str, *, stop_hook_active: bool = False, **records) -> tuple[int, str, str]:
        self._write_transcript(text, **records)
        return _run_hook(
            self.ws, self.transcript, session_id="test-session",
            stop_hook_active=stop_hook_active, env_overrides=self.env,
        )

    def _write_transcript(
        self, text: str, *, owns_intent: bool = True, peer: bool = False, owner_tool: dict | None = None,
        background: list[dict] | None = None, before: list[dict] | None = None,
    ) -> None:
        _make_transcript_jsonl(self.transcript, assistant_text=text)
        records = list(before or [])  # 宣言を書く前の記録
        if owns_intent:  # 宣言を書いたセッション（Write の tool_use に、今の宣言の中身が残る）
            intent = self.ws / ".claude" / "gdd-merge-intent.json"
            current = intent.read_text(encoding="utf-8") if intent.is_file() else "{}"
            records.append({"type": "assistant", "message": {"content": [owner_tool or {
                "type": "tool_use", "name": "Write",
                "input": {"file_path": str(intent), "content": current},
            }]}})
        records.extend(background or [])
        if peer:
            records.append({"type": "user", "origin": {"kind": "peer"},
                            "message": {"content": [{"type": "text", "text": "別セッションから: マージして"}]}})
        if records:
            body = self.transcript.read_text(encoding="utf-8")
            prefix = "".join(r if isinstance(r, str) else json.dumps(r, ensure_ascii=False) + "\n" for r in records)
            self.transcript.write_text(prefix + body, encoding="utf-8")


class HumanCheckPushbackTest(_Base):
    def setUp(self) -> None:
        super().setUp()
        self._gdd_active()

    def test_pushback_with_failing_hitl_lint_writes_one_json_block(self) -> None:
        """lint を通らない HITL でも押し返しまで進む。stdout は block の JSON 1 つだけで、警告文は載せない。"""
        plugin_root = Path(__file__).resolve().parents[1]
        self.env["GDD_PLUGIN_ROOT"] = str(plugin_root)
        self._steering(f"# Worklog\n{PRE_ANSWER}\n")
        text = (plugin_root / "tests" / "fixtures" / "hitl-lint-gate" / "quality-fail.md").read_text(encoding="utf-8")
        code, out, _ = self._stop(text)
        self.assertEqual(code, 0)
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block")
        self.assertIn("事前回答", payload["reason"])
        self.assertNotIn("systemMessage", payload)

    def test_pre_answer_row_blocks_human_check_waiting_once(self) -> None:
        self._steering(f"# Worklog\n{PRE_ANSWER}\n")
        code, out, _ = self._stop(HITL_STOP)
        self.assertEqual(code, 0)
        payload = _blocked(out)
        self.assertIsNotNone(payload, out)
        self.assertIn("事前回答", payload["reason"])
        self.assertIn("委任先", payload["reason"])
        # 同じ記録のまま 2 回目に止まったら通す（無限に押し返さない）
        code, out, _ = self._stop(HITL_STOP, stop_hook_active=True)
        self.assertIsNone(_blocked(out), out)
        self.assertTrue((self.ws / ".claude" / "gdd-dev.local.md").exists())

    def test_fires_even_when_stop_hook_active_is_true(self) -> None:
        # GDD は継続の block を連鎖させるので、HITL に着く停止は通常 true で届く
        self._steering(f"{PRE_ANSWER}\n")
        _, out, _ = self._stop(HITL_STOP, stop_hook_active=True)
        self.assertIsNotNone(_blocked(out), out)

    def test_new_decision_row_rearms_pushback(self) -> None:
        steering = self._steering(f"{PRE_ANSWER}\n")
        self.assertIsNotNone(_blocked(self._stop(HITL_STOP)[1]))
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))
        with (steering / "worklog.md").open("a", encoding="utf-8") as fh:
            fh.write(
                "事前回答の適用: human-check / 対象: 2 / 採った案: 承認 / 委任先の推奨: 承認 / model: fable\n"
            )
        self.assertIsNotNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_parallel_delegate_blocks_and_names_it(self) -> None:
        """委任先が `並行`（`gdd-opus-advisor` に 2 本並行で相談）でも押し返し、文面にその値を出す。"""
        self._steering(PRE_ANSWER.replace("委任先: fable", "委任先: 並行") + "\n")
        payload = _blocked(self._stop(HITL_STOP)[1])
        self.assertIsNotNone(payload)
        self.assertIn("委任先: 並行", payload["reason"])

    def test_none_delegate_blocks(self) -> None:
        self._steering(PRE_ANSWER.replace("委任先: fable", "委任先: なし") + "\n")
        self.assertIsNotNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_unknown_delegate_allows_stop(self) -> None:
        """宣言した集合の外の委任先（大文字・別の model・空）では押し返さない（止まる側に倒す）。"""
        for value in ("Fable", "gpt", "fable（相談役）", ""):
            with self.subTest(value=value):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self._steering(PRE_ANSWER.replace("委任先: fable", f"委任先: {value}") + "\n")
                self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_missing_delegate_field_allows_stop(self) -> None:
        """委任先の欄が無い・重複する行でも例外で落ちず、押し返さない。"""
        rows = (
            PRE_ANSWER.replace("委任先: fable / ", ""),
            PRE_ANSWER.replace("委任先: fable / ", "委任先: fable / 委任先: opus / "),
        )
        for row in rows:
            with self.subTest(row=row):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self._steering(row + "\n")
                code, out, _ = self._stop(HITL_STOP)
                self.assertEqual(code, 0)
                self.assertIsNone(_blocked(out), out)

    def test_latest_pre_answer_decides(self) -> None:
        """事前回答の行が複数あるときは最後の行の委任先で決める。最後が読めなければ押し返さない。"""
        self._steering(PRE_ANSWER + "\n" + PRE_ANSWER.replace("委任先: fable", "委任先: claude") + "\n")
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_no_pre_answer_row_allows_stop(self) -> None:
        self._steering("# Worklog\n- 実装した\n")
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_last_decision_stop_to_human_allows_stop(self) -> None:
        self._steering(
            f"{PRE_ANSWER}\n"
            "事前回答の適用: human-check / 対象: 3 / 採った案: 人間に止める / 委任先の推奨: 人間に止める / model: fable\n"
        )
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_last_decision_not_applied_allows_stop(self) -> None:
        self._steering(
            f"{PRE_ANSWER}\n"
            "事前回答の適用: human-check / 対象: 1 / 採った案: 適用しない（原文を確かめられない） / 委任先の推奨: なし / model: なし\n"
        )
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_pre_answer_inside_code_fence_is_ignored(self) -> None:
        self._steering(f"```\n{PRE_ANSWER}\n```\n")
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_unreadable_worklog_allows_stop(self) -> None:
        steering = self._steering(None)
        (steering / "worklog.md").write_bytes(PRE_ANSWER.encode("utf-8") + b"\n\xff\xfe\n")
        code, out, _ = self._stop(HITL_STOP)
        self.assertEqual(code, 0)
        self.assertIsNone(_blocked(out), out)

    def test_decision_after_unclosed_fence_is_seen(self) -> None:
        # fence の判定は strip_fenced_blocks（正本）に合わせる。閉じ忘れの fence の後の行も読む
        self._steering(
            f"{PRE_ANSWER}\n```\n記入例\n"
            "事前回答の適用: human-check / 対象: 3 / 採った案: 人間に止める / 委任先の推奨: 人間に止める / model: fable\n"
        )
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_unbound_steering_is_not_read(self) -> None:
        steering = _write_steering(self.ws, SLUG, "# Tasklist\n")
        (steering / "worklog.md").write_text(f"{PRE_ANSWER}\n", encoding="utf-8")
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_corrupt_sidecar_allows_stop(self) -> None:
        self._steering(f"{PRE_ANSWER}\n")
        (self.ws / ".claude" / "gdd-autonomy-pushback.json").write_text("{not json", encoding="utf-8")
        code, out, _ = self._stop(HITL_STOP)
        self.assertEqual(code, 0)
        self.assertIsNone(_blocked(out), out)

    def test_pushback_survives_slow_hitl_lint(self) -> None:
        # HITL lint（前処理）に 3 秒以上かかっても、human check の押し返しは判定まで届く
        # plugin root の scripts/ は本物を指し、HITL lint の 4 本だけを 1 秒寝るものに差し替える
        # （bind の解決も plugin root の scripts/ を読むため）
        real = Path(__file__).resolve().parents[1] / "scripts"
        plugin = self.ws / "plugin"
        (plugin / "scripts").mkdir(parents=True)
        slow = {f"{name}.py" for name in ("lint-hitl-display-integrity", "lint-human-check-language",
                                          "lint-hitl-complexity", "lint-hitl-required-fields")}
        for entry in real.iterdir():
            target = plugin / "scripts" / entry.name
            if entry.name in slow:
                target.write_text("import time\ntime.sleep(1.0)\n", encoding="utf-8")
            else:
                target.symlink_to(entry, target_is_directory=entry.is_dir())
        self.env = {**self.env, "GDD_PLUGIN_ROOT": str(plugin)}
        self._steering(f"{PRE_ANSWER}\n")
        payload = _blocked(self._stop(HITL_STOP)[1])
        self.assertIsNotNone(payload)
        self.assertIn("事前回答", payload["reason"])

    def test_other_stop_reasons_are_not_pushed_back(self) -> None:
        self._steering(f"{PRE_ANSWER}\n")
        text = '<gdd-stop reason="clarification-needed">\n\n## 👤 次にすること\n答えてください'
        self.assertIsNone(_blocked(self._stop(text)[1]))


class DelegationFieldPushbackTest(_Base):
    """state.md の Approved Direction の `判断の委任` の欄（references/human-check-template.md § 自走上限の置換値）で決める。"""

    def setUp(self) -> None:
        super().setUp()
        self._gdd_active()

    def _with_state(self, state: str | None, worklog: str | None = "# Worklog\n") -> None:
        steering = self._steering(worklog)
        if state is not None:
            (steering / "state.md").write_text(state, encoding="utf-8")

    def _reset(self) -> None:
        (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)

    def test_field_delegate_blocks_without_pre_answer_row(self) -> None:
        """既定の fable は事前回答の行を書かないので、欄だけで押し返す。"""
        for value in ("fable", "opus", "並行"):
            with self.subTest(value=value):
                self._reset()
                self._with_state(f"## Approved Direction\n- 自走上限: PR 作成まで\n- 判断の委任: {value}\n")
                payload = _blocked(self._stop(HITL_STOP)[1])
                self.assertIsNotNone(payload)
                self.assertIn(f"判断の委任: {value}", payload["reason"])

    def test_field_human_stop_overrides_pre_answer_row(self) -> None:
        """欄が `人に止める` なら、fable の事前回答の行があっても押し返さない（後から人に止めるへ戻した形）。"""
        self._with_state("## Approved Direction\n- 判断の委任: 人に止める\n", PRE_ANSWER + "\n")
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_field_wins_over_pre_answer_row(self) -> None:
        """欄が委任の値なら、事前回答の行の委任先が集合の外でも欄で押し返す。"""
        self._with_state("## Approved Direction\n- 判断の委任: fable\n", PRE_ANSWER.replace("委任先: fable", "委任先: claude") + "\n")
        self.assertIsNotNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_unreadable_or_ambiguous_field_allows_stop(self) -> None:
        """読めない値・欄が 2 つ・空の値では押し返さない（止まる側）。事前回答の行があっても欄を優先し、押し返さない。"""
        states = (
            "## Approved Direction\n- 判断の委任: Fable\n",
            "## Approved Direction\n- 判断の委任: fable\n- 判断の委任: 人に止める\n",
            "## Approved Direction\n- 判断の委任: \n",
        )
        for state in states:
            with self.subTest(state=state):
                self._reset()
                self._with_state(state, PRE_ANSWER + "\n")
                self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_field_inside_code_fence_is_ignored(self) -> None:
        self._with_state("## Approved Direction\n```\n- 判断の委任: fable\n```\n")
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_stopped_row_after_field_allows_stop(self) -> None:
        """人に戻す条件に当たって `採った案: 人間に止める` を書いた後は押し返さない。"""
        row = "事前回答の適用: human-check / 対象: 1 / 採った案: 人間に止める / 委任先の推奨: なし / model: なし"
        self._with_state("## Approved Direction\n- 判断の委任: fable\n", "# Worklog\n" + row + "\n")
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_second_stop_with_same_state_passes(self) -> None:
        self._with_state("## Approved Direction\n- 判断の委任: fable\n")
        self.assertIsNotNone(_blocked(self._stop(HITL_STOP)[1]))
        self.assertIsNone(_blocked(self._stop(HITL_STOP)[1]))

    def test_unreadable_state_falls_back_to_rows(self) -> None:
        """state.md が読めない（ディレクトリ）ときは例外で落ちず、事前回答の行で今までどおり決める。"""
        steering = self._steering(PRE_ANSWER + "\n")
        (steering / "state.md").mkdir()
        code, out, _ = self._stop(HITL_STOP)
        self.assertEqual(code, 0)
        self.assertIsNotNone(_blocked(out))


class MergeIntentPushbackTest(_Base):
    def _intent(self, body: object) -> None:
        d = self.ws / ".claude"
        d.mkdir(parents=True, exist_ok=True)
        text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, separators=(", ", ": "))
        (d / "gdd-merge-intent.json").write_text(text, encoding="utf-8")

    def test_open_pr_with_pending_ci_blocks_once_without_gdd_state(self) -> None:
        self._intent({"pr": 42, "then": "S-2 に進む"})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        payload = _blocked(self._stop("CI を待っています。")[1])
        self.assertIsNotNone(payload)
        self.assertIn("#42", payload["reason"])
        self.assertIn("pending", payload["reason"])
        self.assertIn("S-2 に進む", payload["reason"])
        self.assertIn("pr view 42", (self.ws / "bin" / "gh-args").read_text(encoding="utf-8"))
        # CI の状態が変わらないまま止まったら通す（待機を起動した後の停止）
        self.assertIsNone(_blocked(self._stop("待機を起動しました。")[1]))

    def test_ci_state_change_rearms_pushback(self) -> None:
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        self.assertIsNotNone(_blocked(self._stop("待ちます")[1]))
        self.env = _fake_gh(self.ws / "bin", _pr(checks=SUCCESS))
        payload = _blocked(self._stop("CI が通りました。")[1])
        self.assertIsNotNone(payload)
        self.assertIn("success", payload["reason"])

    def test_pending_reason_points_to_the_wait_script(self) -> None:
        # 待ち方の例は、上限と条件の終了コードを持つ wait-until.py にする（--watch は pending が続くと終わらない）。
        # Bash では ${CLAUDE_PLUGIN_ROOT} が未定義なので、そのまま実行できる絶対パスで示す
        self._intent({"pr": 42, "repo": "o/r"})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        reason = _blocked(self._stop("待ちます")[1])["reason"]
        self.assertNotIn("--watch", reason)
        match = re.search(r"python3 (\S+/wait-until\.py) --timeout \d+ --pr-checks 42 -R o/r", reason)
        self.assertIsNotNone(match, reason)
        script = Path(match.group(1))
        self.assertTrue(script.is_absolute() and script.is_file(), script)

    def test_failure_is_reported(self) -> None:
        self._intent({"pr": 7})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=FAILURE))
        payload = _blocked(self._stop("止まります")[1])
        self.assertIsNotNone(payload)
        self.assertIn("failure", payload["reason"])

    def test_reason_leaves_merge_permission_to_the_declaration(self) -> None:
        # hook は required の check も宣言の原文も読まないので、どの CI の状態でもマージの許可を足さない
        for checks in (FAILURE, [], PENDING, SUCCESS):
            with self.subTest(checks=checks):
                self._intent({"pr": 42})
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.env = _fake_gh(self.ws / "bin", _pr(checks=checks))
                reason = _blocked(self._stop("待ちます")[1])["reason"]
                self.assertIn("宣言の原文", reason)
                self.assertNotIn("マージしてよい", reason)
                self.assertNotIn("checks の無い repo ならほかのマージの条件を確かめてマージする", reason)

    def test_repo_is_passed_to_gh(self) -> None:
        self._intent({"pr": 42, "repo": "owner/name"})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        self._stop("待ちます")
        self.assertIn("-R owner/name", (self.ws / "bin" / "gh-args").read_text(encoding="utf-8"))

    def test_merged_pr_allows_stop(self) -> None:
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", _pr(state="MERGED", checks=SUCCESS))
        self.assertIsNone(_blocked(self._stop("マージしました")[1]))

    def test_gh_failure_allows_stop(self) -> None:
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", None, rc=1)
        code, out, _ = self._stop("待ちます")
        self.assertEqual(code, 0)
        self.assertIsNone(_blocked(out), out)

    def test_invalid_intent_allows_stop(self) -> None:
        bodies = (
            "{broken",
            json.dumps({"pr": "42; rm -rf /"}),
            json.dumps([42]),
            json.dumps({"pr": 0}),
            json.dumps({"pr": True}),
            json.dumps({"pr": 42, "repo": "-R evil"}),
            json.dumps({"pr": 42, "repo": False}),
            json.dumps({"pr": 42, "then": 0}),
        )
        for body in bodies:
            with self.subTest(body=body):
                self._intent(body)
                self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
                code, out, _ = self._stop("待ちます")
                self.assertEqual(code, 0)
                self.assertIsNone(_blocked(out), out)

    def test_empty_rollup_is_reported_as_no_checks(self) -> None:
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=[]))
        payload = _blocked(self._stop("待ちます")[1])
        self.assertIsNotNone(payload)
        self.assertIn("CI: no-checks", payload["reason"])

    def test_other_session_is_not_pushed_back(self) -> None:
        # 宣言を書いていないセッション（同じ worktree の別セッション）には届けない
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        self.assertIsNone(_blocked(self._stop("別の作業を終えました", owns_intent=False)[1]))
        self.assertIsNotNone(_blocked(self._stop("待ちます")[1]))

    def test_only_write_edit_of_this_declaration_counts_as_owner(self) -> None:
        intent = str(self.ws / ".claude" / "gdd-merge-intent.json")
        others = (
            {"type": "tool_use", "name": "Read", "input": {"file_path": intent}},
            {"type": "tool_use", "name": "Bash", "input": {"command": f"cat {intent}"}},
            {"type": "tool_use", "name": "Write",
             "input": {"file_path": "/elsewhere/.claude/gdd-merge-intent.json", "content": '{"pr": 42}'}},
            {"type": "tool_use", "name": "Write",
             "input": {"file_path": ".claude/gdd-merge-intent.json", "content": '{"pr": 42}'}},
            # 前に書いた宣言を、別のセッションが書き直した（今の中身はこのセッションが書いたものではない）
            {"type": "tool_use", "name": "Write", "input": {"file_path": intent, "content": '{"pr": 7}'}},
        )
        for tool in others:
            with self.subTest(tool=tool["name"]):
                self._intent({"pr": 42})
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
                self.assertIsNone(_blocked(self._stop("待ちます", owner_tool=tool)[1]))
        link = self.ws / "link"
        link.symlink_to(self.ws, target_is_directory=True)
        owners = (
            {"type": "tool_use", "name": "Edit",
             "input": {"file_path": intent, "old_string": "7", "new_string": '"pr": 42'}},
            {"type": "tool_use", "name": "MultiEdit",
             "input": {"file_path": intent, "edits": [{"old_string": "7", "new_string": '"pr": 42'}]}},
            {"type": "tool_use", "name": "Write",
             "input": {"file_path": str(link / ".claude" / "gdd-merge-intent.json"), "content": '{"pr": 42}'}},
        )
        for tool in owners:
            with self.subTest(owner=tool["name"]):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.assertIsNotNone(_blocked(self._stop("待ちます", owner_tool=tool)[1]))

    def test_null_repo_and_then_mean_omitted(self) -> None:
        self._intent({"pr": 42, "repo": None, "then": None})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        payload = _blocked(self._stop("待ちます")[1])
        self.assertIsNotNone(payload)
        self.assertNotIn("-R", (self.ws / "bin" / "gh-args").read_text(encoding="utf-8"))

    def test_peer_last_turn_is_not_pushed_back(self) -> None:
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        self.assertIsNone(_blocked(self._stop("了解しました", peer=True)[1]))

    def test_unsafe_then_invalidates_intent(self) -> None:
        for then in ("\ud800", "\x1b[2K消す", "a\u2028b"):
            with self.subTest(then=then):
                (self.ws / ".claude").mkdir(parents=True, exist_ok=True)
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                (self.ws / ".claude" / "gdd-merge-intent.json").write_text(
                    '{"pr": 42, "then": ' + json.dumps(then) + "}", encoding="utf-8")
                self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
                code, out, _ = self._stop("待ちます")
                self.assertEqual(code, 0)
                out.encode("utf-8")
                self.assertIsNone(_blocked(out), out)

    def test_non_hex_head_is_not_echoed(self) -> None:
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", _pr(head="\x1b[2Kevil", checks=PENDING))
        payload = _blocked(self._stop("待ちます")[1])
        self.assertIsNotNone(payload)
        self.assertNotIn("\x1b", payload["reason"])

    def test_gdd_done_stop_is_pushed_back_while_pr_open(self) -> None:
        self._gdd_active()
        self._intent({"pr": 42})
        self.env = _fake_gh(self.ws / "bin", _pr(checks=SUCCESS))
        payload = _blocked(self._stop('<gdd-stop reason="done">\n\n## 👤 次にすること\nなし')[1])
        self.assertIsNotNone(payload)
        self.assertIn("#42", payload["reason"])


def _ago(seconds: float) -> str:
    return datetime.fromtimestamp(time.time() - seconds, timezone.utc).isoformat().replace("+00:00", "Z")


def _bg_bash(n: str, *, background: bool = True, error: bool = False, ack: bool = True,
             at: object = "now") -> list[dict]:
    """background の Bash の起動と、host の起動応答。`at` は起動の record の timestamp（"now" は今）。"""
    content = (f"Command running in background with ID: bash_{n}. Output is being written to: /tmp/x"
               if ack else "done")
    result = {"type": "tool_result", "tool_use_id": f"toolu_bg_{n}", "content": content}
    if error:
        result["is_error"] = True
    launch = {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"toolu_bg_{n}", "name": "Bash",
                                                            "input": {"command": "python3 wait-until.py",
                                                                      "run_in_background": background}}]}}
    if at is not None:
        launch["timestamp"] = _ago(0) if at == "now" else at
    return [launch, {"type": "user", "message": {"content": [result]}}]


def _bg_agent(n: str) -> list[dict]:
    return [
        {"type": "assistant", "timestamp": _ago(0),
         "message": {"content": [{"type": "tool_use", "id": f"toolu_ag_{n}", "name": "Agent",
                                                       "input": {"subagent_type": "general-purpose",
                                                                 "run_in_background": True, "prompt": "..."}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"toolu_ag_{n}",
                                                  "content": f"Async agent launched successfully.\nagentId: agent_{n} (internal ID)"}]}},
    ]


def _ended(task_id: str, tool_use_id: str, status: str = "completed") -> dict:
    text = (f"<task-notification>\n<task-id>{task_id}</task-id>\n<tool-use-id>{tool_use_id}</tool-use-id>\n"
            f"<status>{status}</status>\n<summary>done</summary>\n</task-notification>")
    return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}


def _task_stop(task_id: str) -> list[dict]:
    return [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"toolu_stop_{task_id}",
                                                       "name": "TaskStop", "input": {"task_id": task_id}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"toolu_stop_{task_id}",
                                                  "content": json.dumps({"message": "stopped", "task_id": task_id})}]}},
    ]


class MergeIntentWhileBackgroundRunsTest(_Base):
    """宣言があっても、まだ終わっていない background の処理があれば押し返さない（終われば通知で起きる）。"""

    def setUp(self) -> None:
        super().setUp()
        d = self.ws / ".claude"
        d.mkdir(parents=True, exist_ok=True)
        (d / "gdd-merge-intent.json").write_text(json.dumps({"pr": 42}), encoding="utf-8")
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))

    def test_running_background_bash_skips_pushback(self) -> None:
        self.assertIsNone(_blocked(self._stop("CI を待っています。", background=_bg_bash("1"))[1]))

    def test_running_background_agent_skips_pushback(self) -> None:
        self.assertIsNone(_blocked(self._stop("レビューを待っています。", background=_bg_agent("1"))[1]))

    def test_finished_background_is_pushed_back(self) -> None:
        for status in ("completed", "failed", "killed"):
            with self.subTest(status=status):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                records = _bg_bash("1") + [_ended("bash_1", "toolu_bg_1", status)]
                self.assertIsNotNone(_blocked(self._stop("待ちます", background=records)[1]))

    def test_stopped_background_is_pushed_back(self) -> None:
        records = _bg_bash("1") + _task_stop("bash_1")
        self.assertIsNotNone(_blocked(self._stop("待ちます", background=records)[1]))

    # block（押し返し）すべき入力が allow になる: 起動を確かめられない shell は数えない
    def test_unconfirmed_background_is_pushed_back(self) -> None:
        for name, records in (
            ("foreground の Bash の結果に起動応答の文", _bg_bash("1", background=False)),
            ("起動が is_error", _bg_bash("1", error=True)),
            ("起動応答が無い", _bg_bash("1", ack=False)),
            ("Read の結果に起動応答の文", [
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "toolu_r", "name": "Read",
                                                               "input": {"file_path": "/tmp/t.jsonl"}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_r",
                                                          "content": "Command running in background with ID: bash_9."}]}},
            ]),
        ):
            with self.subTest(name=name):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.assertIsNotNone(_blocked(self._stop("待ちます", background=records)[1]))

    def test_finished_or_stopped_background_agent_is_pushed_back(self) -> None:
        for name, records in (
            ("完了通知", _bg_agent("1") + [_ended("agent_1", "toolu_ag_1")]),
            ("TaskStop", _bg_agent("1") + _task_stop("agent_1")),
        ):
            with self.subTest(name=name):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.assertIsNotNone(_blocked(self._stop("待ちます", background=records)[1]))

    # block（押し返し）すべき入力が allow になる: 終わらない処理・通知の届かない shell で押し返しが止まり続けない
    def test_background_outside_window_is_pushed_back(self) -> None:
        for name, at in (
            ("2 時間 10 分より前の起動", _ago(7800 + 60)),
            ("未来の時刻", _ago(-3600)),
            ("時刻が無い", None),
            ("時刻が読めない", "yesterday"),
            ("時差の無い時刻", "2026-10-09T00:00:00"),
        ):
            with self.subTest(name=name):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.assertIsNotNone(_blocked(self._stop("待ちます", background=_bg_bash("1", at=at))[1]))

    def test_background_inside_window_skips_pushback(self) -> None:
        self.assertIsNone(_blocked(self._stop("待ちます", background=_bg_bash("1", at=_ago(7800 - 60)))[1]))

    def test_promise_path_is_unchanged_while_background_runs(self) -> None:
        (self.ws / ".claude" / "gdd-merge-intent.json").unlink()
        text = "CI の完了を裏で待っています。CI が通ったらマージします。"
        self.assertIsNotNone(_blocked(self._stop(text, owns_intent=False, background=_bg_bash("1"))[1]))


class BackgroundCheckFailureTest(unittest.TestCase):
    """background の判定が例外・読めないときは、動いていないとして扱う（押し返す側）。"""

    def setUp(self) -> None:
        from lib import autonomy_pushback
        self.mod = autonomy_pushback
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.transcript = Path(self._tmp.name) / "t.jsonl"

    def test_exception_means_not_running(self) -> None:
        self.transcript.write_text("", encoding="utf-8")
        with mock.patch.object(self.mod, "parse_transcript", side_effect=RuntimeError("boom")):
            self.assertFalse(self.mod._background_running(Path(self._tmp.name), self.transcript))


class GuardSurvivesPushbackFailureTest(_Base):
    """押し返しが遅い・止まる・落ちるときも、既存の done guard が判定を出す。

    入口から起動する打ち切りは止まったときの保険（hooks.json の timeout の 6 倍）にする。
    並列の全量テストの負荷では、正しく返る hook の壁時計も timeout に届くため。
    本番の timeout に収まることは、押し返しの持ち時間の上限と hooks.json の timeout を比べて見る。
    遅い gh・FIFO は打ち切りが効かないと戻らないので、打ち切りの保険で TimeoutExpired になる。
    """

    UNVERIFIED_DONE = '<gdd-stop reason="done">\n\n## 👤 次にすること\nなし'

    def setUp(self) -> None:
        super().setUp()
        self._gdd_active()
        self._steering(None)
        (self.ws / ".steering" / SLUG / "tasklist.md").write_text(
            "# Tasklist\n- [ ] T-1 未完了\n", encoding="utf-8")

    def _run_stop(self, text: str, **records) -> tuple[int, str, str]:
        self._write_transcript(text, **records)
        return _run_hook(
            self.ws, self.transcript, session_id="test-session",
            stop_hook_active=True, env_overrides=self.env, timeout=STOP_HANG_GUARD,
        )

    def _assert_done_guard_blocks(self, *, background: list[dict] | None = None) -> None:
        code, out, _ = self._run_stop(self.UNVERIFIED_DONE, background=background)
        self.assertEqual(code, 0)
        payload = _blocked(out)
        self.assertIsNotNone(payload, out)
        self.assertNotIn("gdd-merge-intent", payload["reason"])

    def test_pushback_time_limit_fits_the_hook_timeout(self) -> None:
        # 押し返しは読み込みから HARD_LIMIT_SECONDS で手を引き、残りを done guard に回す
        from lib import autonomy_pushback
        self.assertLess(autonomy_pushback.HARD_LIMIT_SECONDS, STOP_HOOK_TIMEOUT)
        self.assertLessEqual(autonomy_pushback.DEADLINE_SECONDS, autonomy_pushback.HARD_LIMIT_SECONDS)

    def test_slow_gh_does_not_starve_done_guard(self) -> None:
        d = self.ws / ".claude"
        (d / "gdd-merge-intent.json").write_text(json.dumps({"pr": 42}), encoding="utf-8")
        bindir = self.ws / "bin"
        # exec にして、gh の打ち切りが sleep 本体に届くようにする（sh だけを止めると sleep が残る）
        (bindir / "gh").write_text("#!/bin/sh\nexec sleep 600\n", encoding="utf-8")
        self._assert_done_guard_blocks()

    def test_large_transcript_does_not_starve_done_guard(self) -> None:
        # background の判定は transcript 全体を読む。大きな transcript でも done guard が判定を出す
        (self.ws / ".claude" / "gdd-merge-intent.json").write_text(json.dumps({"pr": 42}), encoding="utf-8")
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        filler = {"type": "assistant", "timestamp": _ago(0),
                  "message": {"content": [{"type": "text", "text": "x" * 2000}]}}
        with timing_budget() as timing:
            self._assert_done_guard_blocks(background=_bg_agent("1") + [filler] * 15000)
        self.assertLess(timing.cpu_seconds, STOP_HOOK_TIMEOUT)

    def test_fifo_intent_does_not_starve_done_guard(self) -> None:
        os.mkfifo(self.ws / ".claude" / "gdd-merge-intent.json")
        self._assert_done_guard_blocks()

    def test_fifo_sidecar_does_not_starve_done_guard(self) -> None:
        os.mkfifo(self.ws / ".claude" / "gdd-autonomy-pushback.json")
        code, out, _ = self._run_stop("CI が通ったらマージします。" + self.UNVERIFIED_DONE)
        payload = _blocked(out)
        self.assertIsNotNone(payload, out)
        self.assertNotIn("gdd-merge-intent", payload["reason"])


class RunWithinDeadlineTest(unittest.TestCase):
    """押し返しの境界は例外を出さず、押し返しに使った時間の合計で締め切りを決め、締め切り後は記録を書かない。"""

    def setUp(self) -> None:
        import lib.autonomy_pushback as module
        self.mod = importlib.reload(module)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.commits: list[str] = []

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _pushback(self, name: str, *, sleep: float = 0.0):
        def fn():
            time.sleep(sleep)
            return self.mod.Pushback(name, lambda: self.commits.append(name) or True)
        return fn

    def _errors(self) -> str:
        path = self.root / ".gdd" / "hook-errors.log"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def test_thread_start_failure_returns_none_and_is_logged(self) -> None:
        fake = mock.Mock(side_effect=RuntimeError("can't start new thread"))
        with mock.patch.object(self.mod.threading.Thread, "start", fake):
            self.assertIsNone(self.mod.run_within_deadline(self._pushback("x"), self.root))
        self.assertIn("can't start new thread", self._errors())

    def test_exception_in_fn_is_caught_inside_the_thread_and_logged(self) -> None:
        with mock.patch.object(threading, "excepthook") as hook:
            self.assertIsNone(self.mod.run_within_deadline(lambda: 1 / 0, self.root))
        hook.assert_not_called()
        self.assertIn("ZeroDivisionError", self._errors())

    def test_reason_that_cannot_be_encoded_is_not_returned(self) -> None:
        # 本番の起動（kill-switch.sh の python3 関数の `-X utf8`）の stdout は surrogateescape で、U+DC80〜DCFF は
        # 生のバイトで出るが、それ以外の surrogate（U+D800 など）と、UTF-8 mode でない起動では出力で
        # UnicodeEncodeError になり、後ろの done guard ごと停止が通る。encode できない理由文は押し返さず、key も残さない
        for bad in ("wait /p/\udc80/wait-until.py", "wait /p/\ud800/wait-until.py"):
            with self.subTest(bad=bad):
                self.assertIsNone(self.mod.run_within_deadline(self._pushback(bad), self.root))
                self.assertEqual(self.commits, [])
                self.assertIn("UnicodeEncodeError", self._errors())

    def test_time_before_the_first_call_does_not_count(self) -> None:
        self.mod.DEADLINE_SECONDS = 0.3
        time.sleep(0.5)  # HITL lint などの前処理に相当
        self.assertEqual(self.mod.run_within_deadline(self._pushback("x"), self.root), "x")

    def test_budget_is_the_sum_of_calls(self) -> None:
        self.mod.DEADLINE_SECONDS = 0.5
        self.assertIsNone(self.mod.run_within_deadline(lambda: time.sleep(0.3), self.root))
        self.assertIsNone(self.mod.run_within_deadline(self._pushback("y", sleep=0.35), self.root))
        self.assertEqual(self.commits, [])
        self.assertIn("deadline", self._errors())

    def test_hard_limit_from_process_start(self) -> None:
        self.mod.HARD_LIMIT_SECONDS = 0.2
        time.sleep(0.3)
        self.assertIsNone(self.mod.run_within_deadline(self._pushback("x"), self.root))
        self.assertIn("no time left", self._errors())

    def test_late_result_is_not_committed(self) -> None:
        self.mod.DEADLINE_SECONDS = 0.2
        self.assertIsNone(self.mod.run_within_deadline(self._pushback("late", sleep=0.4), self.root))
        time.sleep(0.4)
        self.assertEqual(self.commits, [])

    def test_commit_failure_means_no_pushback(self) -> None:
        fn = lambda: self.mod.Pushback("x", lambda: False)  # noqa: E731
        self.assertIsNone(self.mod.run_within_deadline(fn, self.root))


class MergePromiseNudgeTest(_Base):
    def test_promise_without_intent_blocks_once(self) -> None:
        payload = _blocked(self._stop("PR #42 を作りました。CI が通ったらマージします。")[1])
        self.assertIsNotNone(payload)
        self.assertIn("gdd-merge-intent.json", payload["reason"])
        self.assertIn("Write", payload["reason"])
        # 直後にもう一度同じ形で止まっても、続けては押し返さない
        self.assertIsNone(_blocked(self._stop("CI が success になったらマージします。")[1]))

    def test_promise_variants(self) -> None:
        for text in (
            "Copilot のレビューと CI を待っていて、問題が無ければマージします。",
            "CI が success になったらマージし、次の PR に進みます。",
            "今は CI の完了を待っていて、通ったらマージして次の項目に進みます。",
            "I'll merge it once CI is green.",
        ):
            with self.subTest(text=text):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.assertIsNotNone(_blocked(self._stop(text)[1]))

    def test_no_promise_allows_stop(self) -> None:
        for text in (
            "PR を作りました。", "マージしました。", "CI が通りました。",
            "CI が通ったので PR #42 をマージしました。",
            "Merged PR #42 after CI passed.",
            "CI が通ったらマージしてください。",
        ):
            with self.subTest(text=text):
                (self.ws / ".claude" / "gdd-autonomy-pushback.json").unlink(missing_ok=True)
                self.assertIsNone(_blocked(self._stop(text)[1]))

    def test_promise_in_peer_turn_is_not_pushed_back(self) -> None:
        self.assertIsNone(_blocked(self._stop("CI が通ったらマージします。", peer=True)[1]))

    def test_intent_present_uses_intent_path(self) -> None:
        d = self.ws / ".claude"
        d.mkdir(parents=True, exist_ok=True)
        (d / "gdd-merge-intent.json").write_text(json.dumps({"pr": 42}), encoding="utf-8")
        self.env = _fake_gh(self.ws / "bin", _pr(state="MERGED"))
        self.assertIsNone(_blocked(self._stop("CI が通ったらマージします。")[1]))


MERGE_GATE_DENIAL = (
    "PreToolUse:Bash hook error: ⛔ merge gate（reason code: untrusted-root-unverified）: "
    "repo 内のディレクトリでセッションを起動して実行するか、対象 PR の承認証跡を steering に記録してから再実行してください。"
    "起動根拠: steering 未解決。書き込み先 <steering-dir>/state.md（正本: references/self-review-lanes.md）。"
)
WAIT_DENIAL = (
    "PreToolUse:Bash hook error: ⛔ merge gate（reason code: review-wait-not-elapsed）: HEAD で high 0 の独立レビューを"
    "記録するか、残り分だけ待ってください。不足条件: review-wait-not-elapsed。review-wait-not-elapsed → 残り 120 秒。"
)


def _merge_attempt(n: str, command: str, result: str, *, error: bool = True) -> list[dict]:
    """`gh pr merge` の Bash の試行と、その結果（hook・classifier の拒否は is_error の tool_result で届く）。"""
    tool_result = {"type": "tool_result", "tool_use_id": f"toolu_merge_{n}", "content": result}
    if error:
        tool_result["is_error"] = True
    return [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"toolu_merge_{n}", "name": "Bash",
                                                       "input": {"command": command}}]}},
        {"type": "user", "message": {"content": [tool_result]}},
    ]


class MergeIntentAfterMergeDenialTest(_Base):
    """宣言を書いた後、同じ PR のマージが auto mode classifier や他の hook に拒否されていたら押し返さない（2026-10-13、PR #1328）。

    merge gate は今は拒否せず実行後に通知するだけだが、transcript に残る merge gate の拒否の文面（当時の形）も、
    ほかの拒否と同じに扱う。拒否された操作は再試行しないので、人に戻して止まるのが正しい停止である。
    """

    def setUp(self) -> None:
        super().setUp()
        (self.ws / ".claude").mkdir(parents=True, exist_ok=True)
        (self.ws / ".claude" / "gdd-merge-intent.json").write_text(
            '{"pr": 1328, "repo": "o/r", "then": "次の作業"}', encoding="utf-8")
        self.env = _fake_gh(self.ws / "bin", _pr(checks=SUCCESS))

    def _errors(self) -> str:
        path = self.ws / ".gdd" / "hook-errors.log"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _decide(self, text: str, **records):
        """押し返しの判定を in-process で呼ぶ。gh の `subprocess.run` は差し替える。

        入口から起動すると、負荷の下では gh の打ち切り（2 秒）か押し返しの持ち時間（3 秒）に届き、
        止まる側に倒れる（判定が正しくても押し返さない）。判定の表はこちらで確かめ、入口からは 1 本ずつだけ見る。
        """
        from lib import autonomy_pushback
        (self.ws / ".gdd" / "hook-errors.log").unlink(missing_ok=True)
        self._write_transcript(text, **records)
        view = subprocess.CompletedProcess([], 0, stdout=json.dumps(_pr(head="a" * 40, checks=SUCCESS)), stderr="")
        with mock.patch.object(autonomy_pushback.subprocess, "run", return_value=view):
            return autonomy_pushback.merge_wait_reason(self.ws, self.transcript, lambda: False)

    def test_many_merge_attempts_fit_the_deadline(self) -> None:
        # マージの試行の多い長い transcript でも、締め切りの中で拒否を読む（押し返しが黙って飛ばない）
        many = [r for i in range(300) for r in _merge_attempt(
            f"x{i}", f"cd /repo && gh pr merge {i} -R o/r --merge", "Exit code 1\nnot mergeable")]
        filler = {"type": "assistant", "message": {"content": [{"type": "text", "text": "merge " * 300}]}}
        attempt = _merge_attempt("1", "gh pr merge 1328", MERGE_GATE_DENIAL)
        out = self._stop("止まります", background=[*many, *[filler] * 3000, *attempt])[1]
        self.assertIsNone(_blocked(out), out)
        self.assertNotIn("autonomy_pushback", self._errors())

    def test_errors_log_is_where_the_entry_writes(self) -> None:
        # 陽性対照：入口から走査が例外を出すと、このテストが読む記録に残る（記録が無いことの assert が空振りしない）
        self.transcript.unlink(missing_ok=True)
        self.transcript.mkdir()
        _run_hook(self.ws, self.transcript, session_id="test-session", env_overrides=self.env)
        self.assertIn("autonomy_pushback", self._errors())

    def test_merge_gate_denial_of_this_pr_allows_stop(self) -> None:
        # 事象の形：repo の root に cd して merge し、当時の merge gate が拒否した（transcript に残る文面）
        attempt = _merge_attempt("1", "cd /repo && gh pr merge 1328 -R o/r --merge && gh pr view 1328",
                                 MERGE_GATE_DENIAL)
        code, out, _ = self._stop("merge gate に拒否されたので、人に戻します。", background=attempt)
        self.assertEqual(code, 0)
        self.assertIsNone(_blocked(out), out)
        self.assertNotIn("autonomy_pushback", self._errors())  # 例外で押し返さなかったのではない

    def test_denial_variants_allow_stop(self) -> None:
        variants = {
            "旧形式の merge gate": ("gh pr merge 1328 --merge",
                                   "⛔ merge gate（reason code: session-mismatch）: 不足している検証を解消してください"),
            "auto mode classifier": ("gh pr merge 1328 -R o/r --merge",
                                     "Permission for this action was denied by the Claude Code auto mode classifier. "
                                     "Reason: Blocked by classifier."),
            "他の hook の deny": ("gh pr merge 1328 --merge", "PreToolUse:Bash hook error: 別の guard が止めました"),
            # 番号の無い形（branch から推定）は、対象 PR と区別できないので一致とみなす（止まる側）
            "番号なし": ("cd /gdd/worktree && gh pr merge --merge", MERGE_GATE_DENIAL),
            "URL の形": ("gh pr merge https://github.com/o/r/pull/1328 --merge", MERGE_GATE_DENIAL),
            "review-wait-not-elapsed とほかの不足": ("gh pr merge 1328", WAIT_DENIAL.replace(
                "不足条件: review-wait-not-elapsed。", "不足条件: review-wait-not-elapsed, approval-missing。")),
            # `Exit code` で始まらない is_error は、走る前に止められたとみなす（文言の変化は止まる側に倒れる）
            "未知の拒否の形": ("gh pr merge 1328", "<tool_use_error>denied by settings</tool_use_error>"),
            "branch 名の形": ("gh pr merge feature-x --merge", MERGE_GATE_DENIAL),
            # is_error で本文が空・text の無い形も、走る前に止められたとみなす（`Exit code` で始まらない）
            "is_error で本文が空": ("gh pr merge 1328", ""),
            "is_error で空のリスト": ("gh pr merge 1328", []),
            "is_error で text の無いリスト": ("gh pr merge 1328", [{"type": "image", "source": {}}]),
            "is_error で content が無い": ("gh pr merge 1328", None),
            # merge gate は待つ場面も含めて拒否せず、実行後に通知するだけになった。待つ場面の文が transcript に残っていても、ほかの拒否と同じく止まる側に倒す
            "review-wait-not-elapsed だけの文": ("gh pr merge 1328", WAIT_DENIAL),
            "リストの形の review-wait-not-elapsed だけの文": ("gh pr merge 1328", [{"type": "text", "text": WAIT_DENIAL}]),
        }
        for name, (command, result) in variants.items():
            with self.subTest(name):
                attempt = _merge_attempt("1", command, result)
                if result is None:
                    del attempt[1]["message"]["content"][0]["content"]
                self.assertIsNone(self._decide("拒否されたので止まります", background=attempt))
                self.assertNotIn("autonomy_pushback", self._errors())

    def test_cases_that_still_push_back(self) -> None:
        # block すべき入力が allow にならない：拒否ではない失敗・別の PR・宣言より前の拒否・拒否の後の再試行
        cases = {
            "実行して失敗": dict(background=_merge_attempt(
                "1", "gh pr merge 1328 --squash", "Exit code 1\nGraphQL: Squash merges are not allowed")),
            "別の PR の拒否": dict(background=_merge_attempt("1", "gh pr merge 7 --merge", MERGE_GATE_DENIAL)),
            "別の PR の URL の拒否": dict(background=_merge_attempt(
                "1", "gh pr merge https://github.com/o/r/pull/7", MERGE_GATE_DENIAL)),
            # 1 行目に merge gate の拒否の文面があっても、走って失敗した出力（gate のソースの grep など）は拒否ではない
            "Exit code の中の merge gate の文": dict(background=_merge_attempt(
                "1", "gh pr merge 1328", "Exit code 1\n" + MERGE_GATE_DENIAL)),
            "宣言より前の拒否": dict(before=_merge_attempt("1", "gh pr merge 1328", MERGE_GATE_DENIAL)),
            "拒否の後の再試行は拒否されていない": dict(background=[
                *_merge_attempt("1", "gh pr merge 1328", MERGE_GATE_DENIAL),
                *_merge_attempt("2", "gh pr merge 1328", "Exit code 1\nPull Request is not mergeable"),
            ]),
            "grep の中の文字列": dict(background=_merge_attempt(
                "1", 'grep -n "gh pr merge 1328" log', MERGE_GATE_DENIAL)),
            "is_error でない": dict(background=_merge_attempt(
                "1", "gh pr merge 1328", MERGE_GATE_DENIAL, error=False)),
            # content が text block のリストでも、連結した本文の先頭で読む
            "リストの形の Exit code": dict(background=_merge_attempt("1", "gh pr merge 1328", [
                {"type": "text", "text": "Exit code 1\n"}, {"type": "text", "text": MERGE_GATE_DENIAL}])),
        }
        for name, kwargs in cases.items():
            with self.subTest(name):
                pushback = self._decide("止まります", **kwargs)
                self.assertIsNotNone(pushback, self._errors())
                self.assertIn("#1328", pushback.reason)

    def test_broken_lines_do_not_hide_the_denial(self) -> None:
        # 例外で判定全体が落ちない：壊れた行・形の違う行が混ざっても拒否を読む
        attempt = _merge_attempt("1", "gh pr merge 1328", MERGE_GATE_DENIAL)
        noise = ["{broken toolu_merge_1\n", '"toolu_merge_1"\n',
                 {"type": "user", "message": {"content": "toolu_merge_1 の結果"}},
                 {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_merge_1",
                                                           "content": [{"type": "text", "text": "x"}, 3]}]}}]
        self.assertIsNone(self._decide("止まります", background=[attempt[0], *noise, attempt[1]]))
        self.assertNotIn("autonomy_pushback", self._errors())  # 例外で押し返さなかったのではない
        # 同じ雑音で、拒否でない試行なら押し返す
        failed = _merge_attempt("1", "gh pr merge 1328", "Exit code 1\nPull Request is not mergeable")
        self.assertIsNotNone(self._decide("止まります", background=[failed[0], *noise, failed[1]]), self._errors())
        self.assertNotIn("autonomy_pushback", self._errors())
        # content が block のリストの形でも読む
        listed = _merge_attempt("1", "gh pr merge 1328", "")
        listed[1]["message"]["content"][0]["content"] = [{"type": "text", "text": MERGE_GATE_DENIAL}]
        self.assertIsNone(self._decide("止まります", background=listed))
        self.assertNotIn("autonomy_pushback", self._errors())

    def test_reason_offers_stopping_after_a_denial(self) -> None:
        reason = _blocked(self._stop("止まります")[1])["reason"]
        self.assertIn("再試行せず", reason)


class MergeIntentLocationTest(_Base):
    """宣言の置き場所は Stop hook の cwd の toplevel の 1 か所。押し返しの文は、hook が読む絶対パスを示す。"""

    def test_intent_reason_shows_the_absolute_path(self) -> None:
        (self.ws / ".claude").mkdir(parents=True, exist_ok=True)
        (self.ws / ".claude" / "gdd-merge-intent.json").write_text('{"pr": 42}', encoding="utf-8")
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        reason = _blocked(self._stop("待ちます")[1])["reason"]
        self.assertIn(str(self.ws / ".claude" / "gdd-merge-intent.json"), reason)

    def test_promise_reason_shows_the_absolute_path(self) -> None:
        reason = _blocked(self._stop("CI が通ったらマージします。", owns_intent=False)[1])["reason"]
        self.assertIn(str(self.ws / ".claude" / "gdd-merge-intent.json"), reason)
        self.assertIn("GDD の worktree", reason)

    def test_declaration_in_another_worktree_is_not_read(self) -> None:
        # GDD の worktree など、hook の cwd の外に書いた宣言は読まない（約束の押し返しに進み、正しい場所を示す）
        other = self.ws / "gdd-worktree"
        (other / ".claude").mkdir(parents=True)
        (other / ".claude" / "gdd-merge-intent.json").write_text('{"pr": 42}', encoding="utf-8")
        self.env = _fake_gh(self.ws / "bin", _pr(checks=PENDING))
        tool = {"type": "tool_use", "name": "Write",
                "input": {"file_path": str(other / ".claude" / "gdd-merge-intent.json"), "content": '{"pr": 42}'}}
        reason = _blocked(self._stop("CI が通ったらマージします。", owner_tool=tool)[1])["reason"]
        self.assertIn("がありません", reason)  # 宣言ありの押し返しではなく、約束の押し返し
        self.assertNotIn("#42", reason)
        self.assertFalse((self.ws / "bin" / "gh-args").exists())  # 別の worktree の宣言で gh を呼ばない
        self.assertIn(str(self.ws / ".claude" / "gdd-merge-intent.json"), reason)


class PushbackTextSafetyTest(unittest.TestCase):
    """押し返しの文に載せるパス・コマンドを、shell に貼れて端末を乱さない形にする。"""

    def test_unsafe_wait_script_path_is_not_echoed(self) -> None:
        # 理由文に載せる待機スクリプトのパスも、制御文字・surrogate を含むなら置き換える（クォートした placeholder は出さない）
        from lib import autonomy_pushback
        for bad in ("/p/a\x1b[2Kb/wait-until.py", "/p/\udc80/wait-until.py", "/p/a\nb/wait-until.py"):
            with self.subTest(bad=bad):
                shown = autonomy_pushback._wait_command(Path(bad), 42, ["-R", "o/r"])
                self.assertEqual(shown, "python3 …/scripts/wait-until.py --timeout 3600 --pr-checks 42 -R o/r")
                shown.encode("utf-8")
        ok = autonomy_pushback._wait_command(Path("/p/my dir/wait-until.py"), 42, [])
        self.assertEqual(ok, "python3 '/p/my dir/wait-until.py' --timeout 3600 --pr-checks 42")

    def test_reason_replaces_an_unsafe_wait_script_path(self) -> None:
        # 理由文を組む入口（_intent_reason）でも、待機スクリプトのパスの置き換えが効く
        from lib import autonomy_pushback
        import subprocess
        view = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            {"state": "OPEN", "headRefOid": "a" * 40, "statusCheckRollup": []}), stderr="")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
                autonomy_pushback, "WAIT_SCRIPT", Path("/p/a\x1b[2Kb/wait-until.py")), mock.patch.object(
                autonomy_pushback.subprocess, "run", return_value=view):
            reason = autonomy_pushback._intent_reason(Path(tmp), (42, "o/r", "")).reason
        self.assertIn("python3 …/scripts/wait-until.py --timeout 3600 --pr-checks 42", reason)
        self.assertNotIn("\x1b", reason)
        reason.encode("utf-8")

    def test_unknown_head_is_not_a_shell_redirect(self) -> None:
        # head を読めないときの run の確かめ方も、shell に貼れる形にする（`<head>` はリダイレクトになる）
        from lib import autonomy_pushback
        import subprocess
        view = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            {"state": "OPEN", "headRefOid": "not-a-sha", "statusCheckRollup": []}), stderr="")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
                autonomy_pushback.subprocess, "run", return_value=view):
            reason = autonomy_pushback._intent_reason(Path(tmp), (42, "o/r", "")).reason
        self.assertNotIn("<head>", reason)
        self.assertIn('gh run list --commit "$(gh pr view 42 --json headRefOid -q .headRefOid -R o/r)" -R o/r', reason)

    def test_unsafe_toplevel_is_not_echoed(self) -> None:
        # 理由文に載せる宣言のパスは、制御文字・surrogate を含むなら相対の書き方にする
        from lib import autonomy_pushback
        self.assertEqual(autonomy_pushback._shown_intent_path(Path("/w/a\x1b[2Kb")), ".claude/gdd-merge-intent.json")
        self.assertEqual(autonomy_pushback._shown_intent_path(Path("/w/ok")), "/w/ok/.claude/gdd-merge-intent.json")


def _module_constants() -> dict[str, float]:
    """lib/autonomy_pushback.py の module の定数を、ソースから読む。

    RunWithinDeadlineTest は module を reload して締め切りを書き換え、戻さないので、走る順によっては
    import した module の値が書き換わったままになる。ここでは書き換えの影響を受けないソースの値を見る。
    """
    import ast
    source = Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib" / "autonomy_pushback.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    return {
        node.targets[0].id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float))
    }


class GhTimeoutIsLoggedTest(_Base):
    """マージ待ちの宣言の PR を読む gh が打ち切られたら、hook-errors.log に残す（押し返さないのは今までどおり）。"""

    def setUp(self) -> None:
        super().setUp()
        (self.ws / ".claude").mkdir(parents=True, exist_ok=True)
        (self.ws / ".claude" / "gdd-merge-intent.json").write_text(json.dumps({"pr": 42}), encoding="utf-8")
        self.bindir = self.ws / "slow-bin"
        self.bindir.mkdir()
        self.called = self.ws / "gh-called"
        gh = self.bindir / "gh"
        gh.write_text(f"#!/bin/sh\necho called > '{self.called}'\nexec sleep 600\n", encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        self.slow_path = {"PATH": f"{self.bindir}{os.pathsep}{os.environ.get('PATH', '')}"}

    def _records(self) -> list[dict]:
        path = self.ws / ".gdd" / "hook-errors.log"
        if not path.exists():
            return []
        return [r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines())
                if r.get("source") == "autonomy_pushback"]

    def _messages(self) -> list[str]:
        return [str(r.get("message", "")) for r in self._records()]

    def _decide(self):
        from lib import autonomy_pushback
        self._write_transcript("止まります")
        with mock.patch.dict(os.environ, self.slow_path):
            return autonomy_pushback.merge_wait_reason(self.ws, self.transcript, lambda: False)

    def test_gh_timeout_is_logged_and_does_not_push_back(self) -> None:
        # 押し返しの締め切りを通さずに呼ぶので、締め切りとの競争は無く、gh の打ち切りの分岐だけを見る
        self.assertIsNone(self._decide())
        self.assertTrue(self.called.exists())
        gh_lines = [m for m in self._messages() if m.startswith("gh: timed out")]
        self.assertEqual(len(gh_lines), 1, self._messages())

    def test_gh_failure_other_than_timeout_is_not_logged(self) -> None:
        from lib import autonomy_pushback
        self._write_transcript("止まります")
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="not found")
        for outcome in (FileNotFoundError("gh"), failed):
            with self.subTest(outcome=type(outcome).__name__):
                kwargs = {"side_effect": outcome} if isinstance(outcome, BaseException) else {"return_value": outcome}
                with mock.patch.object(autonomy_pushback.subprocess, "run", **kwargs):
                    self.assertIsNone(autonomy_pushback.merge_wait_reason(self.ws, self.transcript, lambda: False))
        self.assertEqual(self._messages(), [])

    def test_failing_log_write_does_not_escape_the_pushback_boundary(self) -> None:
        # 記録の書き込みが例外を出しても（本物の append_hook_error は例外を握るので、防御の確認）、押し返しの境界が None を返す
        from lib import autonomy_pushback
        self._write_transcript("止まります")
        boom = mock.Mock(side_effect=RuntimeError("log write failed"))
        with mock.patch.dict(os.environ, self.slow_path), \
                mock.patch.object(autonomy_pushback, "append_hook_error", boom), \
                mock.patch.object(autonomy_pushback, "DEADLINE_SECONDS", 60), \
                mock.patch.object(autonomy_pushback, "HARD_LIMIT_SECONDS", 60), \
                mock.patch.object(autonomy_pushback, "_STARTED_AT", time.monotonic()), \
                mock.patch.object(autonomy_pushback, "_spent", 0.0), \
                mock.patch.object(threading, "excepthook"):
            result = autonomy_pushback.run_within_deadline(
                lambda: autonomy_pushback.merge_wait_reason(self.ws, self.transcript, lambda: False), self.ws)
        self.assertIsNone(result)
        self.assertTrue(self.called.exists())
        self.assertTrue(any("gh: timed out" in str(c.args) for c in boom.call_args_list), boom.call_args_list)

    def test_gh_timeout_is_shorter_than_the_pushback_deadline(self) -> None:
        # 逆だと締め切りが常に先に切り、gh の打ち切りの記録に届かない。必要条件で、十分条件ではない
        # （締め切りの残りは、gh の前の処理の時間と HARD_LIMIT_SECONDS でさらに縮む）
        constants = _module_constants()
        self.assertLess(constants["GH_TIMEOUT_SECONDS"], constants["DEADLINE_SECONDS"])

    def test_stop_hook_logs_gh_timeout_and_done_guard_still_blocks(self) -> None:
        # 入口から通す。負荷で締め切りが gh の打ち切りより先に来ると、gh の行は出ず deadline の行だけが出る。
        # そのときは確かめられなかったとして skip にする（通したことにしない）。どちらの行も無ければ失敗
        self._gdd_active()
        self._steering(None)
        (self.ws / ".steering" / SLUG / "tasklist.md").write_text("# Tasklist\n- [ ] T-1 未完了\n", encoding="utf-8")
        self.env = self.slow_path
        code, out, _ = self._stop(GuardSurvivesPushbackFailureTest.UNVERIFIED_DONE, stop_hook_active=True)
        self.assertEqual(code, 0)
        self.assertIsNotNone(_blocked(out), out)
        messages = self._messages()
        if any(m.startswith("gh: timed out") for m in messages):
            return
        if any(m.startswith("deadline:") for m in messages):
            self.skipTest(f"押し返しの締め切りが gh の打ち切りより先に来た（負荷）: {messages}")
        self.fail(f"gh の打ち切りの記録が無い: {messages}")

    def test_deadline_record_into_fifo_does_not_hang_the_main_thread(self) -> None:
        # 押し返しが締め切りに届かないとき、main の thread が書く deadline の記録も、FIFO で止まらない
        from lib import autonomy_pushback
        (self.ws / ".gdd").mkdir(exist_ok=True)
        os.mkfifo(self.ws / ".gdd" / "hook-errors.log")
        done = threading.Event()

        def call() -> None:
            autonomy_pushback.run_within_deadline(lambda: time.sleep(5), self.ws)
            done.set()

        with mock.patch.object(autonomy_pushback, "DEADLINE_SECONDS", 0.2), \
                mock.patch.object(autonomy_pushback, "HARD_LIMIT_SECONDS", 60), \
                mock.patch.object(autonomy_pushback, "_STARTED_AT", time.monotonic()), \
                mock.patch.object(autonomy_pushback, "_spent", 0.0):
            threading.Thread(target=call, daemon=True).start()
            self.assertTrue(done.wait(3), "deadline の記録の open で止まった")

    def test_fifo_error_log_does_not_starve_done_guard(self) -> None:
        # 記録先が読み手のいない FIFO でも、記録の open で止まらず、done guard が block を出す
        self._gdd_active()
        self._steering(None)
        (self.ws / ".steering" / SLUG / "tasklist.md").write_text("# Tasklist\n- [ ] T-1 未完了\n", encoding="utf-8")
        (self.ws / ".gdd").mkdir(exist_ok=True)
        os.mkfifo(self.ws / ".gdd" / "hook-errors.log")
        self.env = self.slow_path
        code, out, _ = self._stop(GuardSurvivesPushbackFailureTest.UNVERIFIED_DONE, stop_hook_active=True)
        self.assertEqual(code, 0)
        self.assertIsNotNone(_blocked(out), out)


if __name__ == "__main__":
    unittest.main()
