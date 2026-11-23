"""依頼との差の表示（human check の Stop）の E2E。

hook の入口（run-request-diff-hook.sh）を subprocess で起動し、偽の `claude` を PATH に置いて確かめる。
"""
from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

from _paths import PLUGIN_ROOT  # noqa: E402

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib import request_diff  # noqa: E402

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-request-diff-hook.sh"
MARKER = '<gdd-stop reason="human-check-waiting">'
TAG = '<gdd-hitl-fields request-diff="none">'
PRESENTATION = f"## 確認\n推奨: 案 B で設計に進みます。\n- 依頼との差: なし\n{TAG}\n{MARKER}\n## 👤 次にすること\nOK と返信してください"
BROKEN = PRESENTATION.replace("- 依頼との差: なし", "- 依頼との差: なし | 全項目を検出したい")
MISSING = PRESENTATION.replace(TAG + "\n", "")
DIFFERS = PRESENTATION.replace(": なし", ": あり: 全項目を検出したい").replace('"none"', '"differs"')


def human(text: str) -> dict:
    return {"type": "user", "origin": {"kind": "human"}, "timestamp": "2026-11-09T00:00:00Z", "message": {"content": text}}


def assistant(text: str) -> dict:
    return {"type": "assistant", "timestamp": "2026-11-09T00:01:00Z", "message": {"content": [{"type": "text", "text": text}]}}


def feedback(reason: str) -> dict:
    """host が Stop hook の block の理由を transcript に書く形（isMeta の user の行）。"""
    return {"type": "user", "isMeta": True, "message": {"role": "user", "content": "Stop hook feedback:\n" + reason}}


TOOL_RESULT = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}
NOTIFICATION = {"type": "user", "origin": {"kind": "task-notification"}, "message": {"content": "相談役の報告の文"}}


def item(kind: str = "変わる", user: str = "全項目を検出したい", rec: str = "推奨: 案 B", alt: str = "なし") -> dict:
    return {"kind": kind, "user": user, "rec": rec, "alt": alt}


FLAGGED = {
    "result": json.dumps({"flag": True, "items": [item()]}, ensure_ascii=False),
    "total_cost_usd": 0.05,
}


class _HookFixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.bin = self.dir / "bin"
        self.bin.mkdir()
        self.state = self.dir / "state"
        self.transcript = self.dir / "t.jsonl"
        self.calls = self.dir / "calls.jsonl"

    def write_transcript(self, records: list[dict]) -> None:
        self.transcript.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")

    def fake_claude(self, stdout: str, code: int = 0) -> None:
        path = self.bin / "claude"
        path.write_text(
            "#!/usr/bin/env python3\n"
            "import json,sys,os\n"
            f"open({str(self.calls)!r},'a').write(json.dumps({{'argv':sys.argv[1:],'stdin':sys.stdin.read(),"
            "'cwd':os.getcwd()},ensure_ascii=False)+'\\n')\n"
            f"sys.stdout.write({stdout!r})\n"
            f"sys.exit({code})\n",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def run_hook(self, env: dict | None = None, payload: str | None = None, path: str | None = None):
        real_python = str(Path(sys.executable).parent)
        full_env = {
            **os.environ,
            "HOME": str(self.dir),
            "GDD_HOOK_STATE_DIR": str(self.state),
            "PATH": path if path is not None else f"{self.bin}:{real_python}:/usr/bin:/bin",
            **(env or {}),
        }
        body = payload if payload is not None else json.dumps(
            {"session_id": "s1", "cwd": str(self.dir), "transcript_path": str(self.transcript)}
        )
        return subprocess.run(["bash", str(HOOK)], input=body, capture_output=True, text=True, env=full_env, check=False)

    def calls_made(self) -> list[dict]:
        if not self.calls.exists():
            return []
        return [json.loads(line) for line in self.calls.read_text(encoding="utf-8").splitlines()]

    def message(self, result) -> str:
        return json.loads(result.stdout)["systemMessage"] if result.stdout.strip() else ""

class RequestDiffHookTest(_HookFixture):
    def test_shows_one_line_per_kind_in_the_agreed_form(self):
        answer = {"result": json.dumps({"flag": True, "items": [
            item(), item(user="依頼の別の語", rec="別の推奨"), item(kind="満たせない", user="根本から直したい", rec="表示だけ足す", alt="あり"),
        ]}, ensure_ascii=False)}
        self.write_transcript([human("全項目を検出したい"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps(answer, ensure_ascii=False))
        self.assertEqual(self.message(self.run_hook()), "\n".join([
            "依頼との差（変わる）: 全項目を検出したい → 推奨: 案 B（ほか 1 件）",
            "依頼との差（満たせない）: 根本から直したい（別の案: あり）",
        ]))
        record = json.loads((self.state / "request-diff.log").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual([i["kind"] for i in record["items"]], ["変わる", "変わる", "満たせない"])
        self.assertEqual(record["items"][2]["alt"], "あり")

    def test_shows_the_difference_and_does_not_block_a_well_formed_presentation(self):
        self.write_transcript([human("全項目を検出したい"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        result = self.run_hook()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.message(result), "依頼との差（変わる）: 全項目を検出したい → 推奨: 案 B")
        self.assertNotIn("decision", json.loads(result.stdout))

    def test_nothing_is_shown_when_there_is_no_difference(self):
        self.write_transcript([human("依頼"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps({"result": '{"flag":false,"items":[]}'}))
        result = self.run_hook()
        self.assertEqual((result.returncode, result.stdout.strip()), (0, ""))
        self.assertEqual(len(self.calls_made()), 1)

    def test_only_human_words_and_the_presentation_reach_the_checker(self):
        self.write_transcript([
            human("人の依頼の文"),
            assistant("main の途中の分析の文"),
            {"type": "user", "origin": {"kind": "task-notification"}, "message": {"content": "相談役の報告の文"}},
            {"type": "user", "isSidechain": True, "origin": {"kind": "human"}, "message": {"content": "subagent 側の文"}},
            human("人の途中の決定の文"),
            assistant(PRESENTATION),
        ])
        self.fake_claude(json.dumps({"result": '{"flag":false,"items":[]}'}))
        self.run_hook()
        sent = self.calls_made()[0]["stdin"]
        for present in ("人の依頼の文", "人の途中の決定の文", "推奨: 案 B で設計に進みます"):
            self.assertIn(present, sent)
        for absent in ("main の途中の分析の文", "相談役の報告の文", "subagent 側の文"):
            self.assertNotIn(absent, sent)

    def test_words_before_the_previous_task_finished_still_reach_the_checker(self):
        self.write_transcript([
            human("前のタスクの依頼"),
            assistant('終わりました\n<gdd-stop reason="done">'),
            human("今のタスクの依頼"),
            assistant(PRESENTATION),
        ])
        self.fake_claude(json.dumps({"result": '{"flag":false,"items":[]}'}))
        self.run_hook()
        sent = self.calls_made()[0]["stdin"]
        self.assertIn("今のタスクの依頼", sent)
        self.assertIn("前のタスクの依頼", sent)

    def test_the_child_cannot_use_tools_or_start_hooks_and_runs_the_measured_model(self):
        self.write_transcript([human("依頼"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps({"result": '{"flag":false,"items":[]}'}))
        self.run_hook()
        argv = self.calls_made()[0]["argv"]
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(json.loads(argv[argv.index("--settings") + 1]), {"disableAllHooks": True})
        self.assertEqual(argv[argv.index("--model") + 1], "opus")
        self.assertEqual(argv[argv.index("--effort") + 1], "medium")
        self.assertIn("--no-session-persistence", argv)

    def test_stops_other_than_human_check_do_not_start_the_checker(self):
        self.write_transcript([human("依頼"), assistant('<gdd-stop reason="done">')])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        result = self.run_hook()
        self.assertEqual((result.returncode, result.stdout.strip(), self.calls_made()), (0, "", []))

    def test_the_same_presentation_is_checked_once(self):
        self.write_transcript([human("依頼"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        first = self.run_hook()
        second = self.run_hook()
        self.assertIn("依頼との差", self.message(first))
        self.assertEqual(second.stdout.strip(), "")
        self.assertEqual(len(self.calls_made()), 1)

    def test_a_changed_presentation_is_checked_again(self):
        self.write_transcript([human("依頼"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        self.run_hook()
        self.write_transcript([human("依頼"), assistant(PRESENTATION + "\n書き直した")])
        self.run_hook()
        self.assertEqual(len(self.calls_made()), 2)

    def test_result_is_kept_in_the_state_dir_for_reading_the_trial(self):
        self.write_transcript([human("全項目を検出したい"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        self.run_hook()
        record = json.loads((self.state / "request-diff.log").read_text(encoding="utf-8").splitlines()[-1])
        self.assertTrue(record["flag"])
        self.assertEqual(record["session_id"], "s1")
        self.assertEqual(record["items"][0]["user"], "全項目を検出したい")
        self.assertEqual(record["cost_usd"], 0.05)

    def test_the_request_diff_fields_are_kept_in_the_log(self):
        presentation = PRESENTATION.replace("- 依頼との差: なし", "- 依頼との差: なし\n- 依頼との差: あり: 全レーンに入れる").replace(
            '"none"', '"none,differs"')
        self.write_transcript([human("全項目を検出したい"), assistant(presentation)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        self.run_hook()
        record = json.loads((self.state / "request-diff.log").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(record["fields"], ["なし", "あり: 全レーンに入れる"])
        self.assertEqual(record["field_problem"], "なし以外の点がある")

    def test_not_run_stays_in_the_log_and_shows_nothing(self):
        cases = {
            "claude が無い": (None, 0),
            "終了コードが 0 でない": ("x", 1),
            "JSON でない": ("not json", 0),
            "is_error": (json.dumps({"is_error": True, "result": "limit"}), 0),
            "判定が JSON でない": (json.dumps({"result": "わかりません"}), 0),
            "flag なのに項目が無い": (json.dumps({"result": '{"flag":true,"items":[]}'}), 0),
            "項目の形が違う": (json.dumps({"result": '{"flag":true,"items":["x"]}'}), 0),
            "種類が読めない": (json.dumps({"result": json.dumps({"flag": True, "items": [item(kind="その他")]})}), 0),
            "別の案が読めない": (json.dumps({"result": json.dumps({"flag": True, "items": [item(alt="不明")]})}), 0),
        }
        for name, (stdout, code) in cases.items():
            with self.subTest(name):
                (self.bin / "claude").unlink(missing_ok=True)
                (self.state / "request-diff.log").unlink(missing_ok=True)
                self.write_transcript([human("依頼"), assistant(PRESENTATION)])
                if stdout is not None:
                    self.fake_claude(stdout, code)
                result = self.run_hook()
                self.assertEqual((result.returncode, result.stdout.strip()), (0, ""))
                record = json.loads((self.state / "request-diff.log").read_text(encoding="utf-8").splitlines()[-1])
                self.assertTrue(record["not_run"])

    def test_a_presentation_without_human_words_is_not_checked(self):
        self.write_transcript([assistant(PRESENTATION)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        result = self.run_hook()
        self.assertEqual(result.stdout.strip(), "")
        self.assertEqual(self.calls_made(), [])
        record = json.loads((self.state / "request-diff.log").read_text(encoding="utf-8").splitlines()[-1])
        self.assertTrue(record["not_run"])

    def test_a_broken_payload_or_transcript_stays_quiet_and_does_not_fail_the_stop(self):
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        for payload in ("not json", "{}", json.dumps({"transcript_path": str(self.dir / "none.jsonl")})):
            with self.subTest(payload):
                result = self.run_hook(payload=payload)
                self.assertEqual((result.returncode, result.stdout.strip()), (0, ""))
        self.assertEqual(self.calls_made(), [])

    def test_skip_env_and_kill_switch_turn_it_off(self):
        self.write_transcript([human("依頼"), assistant(PRESENTATION)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        self.assertEqual(self.run_hook(env={"GDD_SKIP_REQUEST_DIFF": "1"}).stdout.strip(), "")
        (self.dir / ".claude").mkdir()
        (self.dir / ".claude" / "gdd-hooks-disabled").write_text("")
        self.assertEqual(self.run_hook().stdout.strip(), "")
        self.assertEqual(self.calls_made(), [])

    def test_timeout_is_reported_as_not_run(self):
        with mock.patch.object(request_diff.subprocess, "run", side_effect=subprocess.TimeoutExpired("claude", 1)), \
                mock.patch.object(request_diff.shutil, "which", return_value="/x/claude"):
            verdict = request_diff.ask_checker("text")
        self.assertEqual(verdict.not_run, "時間切れ")

    def test_quotes_cannot_break_the_one_line_form(self):
        line = request_diff.render(item(user="a\nb" + "x" * 500, rec="c\rd"), others=0)
        self.assertNotIn("\n", line)
        self.assertLess(len(line), 300)

    def test_hook_timeout_is_longer_than_the_checker_timeout(self):
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entries = [h for g in hooks["hooks"]["Stop"] for h in g["hooks"] if "run-request-diff-hook.sh" in h["command"]]
        self.assertEqual(len(entries), 1)
        self.assertGreater(entries[0]["timeout"], request_diff.CHECKER_TIMEOUT_SECONDS)


class MalformedFieldBlockTest(_HookFixture):
    """承認の書き込みで止まる確認（欄の形が崩れた・なし以外の点がある）は、ユーザーが答える前に Stop で main に出し直させる
    （読み手は起動しない）。"""

    def payload(self, active: bool = False, session: str = "s1") -> str:
        return json.dumps({"session_id": session, "cwd": str(self.dir), "transcript_path": str(self.transcript),
                           "stop_hook_active": active})

    def decision(self, result) -> dict:
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def records(self) -> list[dict]:
        log = self.state / "request-diff.log"
        return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []

    def test_each_malformed_form_is_blocked_before_the_user_answers(self):
        cases = {
            "なし と項目を並べた": BROKEN,
            "タグが無い": MISSING,
            "タグの値が読めない": PRESENTATION.replace('"none"', '"none|differs"'),
            "説明の文に語を書いた": "止められたので、依頼との差の欄を直して出し直します。\n" + PRESENTATION,
            "ありません と書いた": PRESENTATION.replace(": なし", ": ありません。"),
        }
        for name, text in cases.items():
            with self.subTest(name):
                (self.state / "request-diff.log").unlink(missing_ok=True)
                self.write_transcript([human("全項目を検出したい"), assistant(text)])
                self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
                result = self.run_hook(payload=self.payload())
                self.assertEqual(result.returncode, 0)
                self.assertEqual(self.decision(result).get("decision"), "block", result.stdout)
        self.assertEqual(self.calls_made(), [], "出し直させる提示に読み手を起動しない")

    def test_block_reason_quotes_the_unreadable_line_and_asks_for_the_full_presentation_only(self):
        self.write_transcript([human("依頼"), assistant(BROKEN)])
        reason = self.decision(self.run_hook(payload=self.payload()))["reason"]
        self.assertIn("なし | 全項目を検出したい", reason)
        self.assertIn(MARKER, reason)

    def test_declared_difference_is_blocked_before_the_user_answers(self):
        """推奨が依頼より狭い確認は、ユーザーが OK しても承認の書き込みで止まり、同じ判断を答え直させる。表示の時点で
        出し直させ、狭める案は採用しない案として並べさせる（ユーザーが名指しで選べば、その返事で決まる）。"""
        self.write_transcript([human("全項目を検出したい"), assistant(DIFFERS)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        result = self.run_hook(payload=self.payload())
        decision = self.decision(result)
        self.assertEqual(decision.get("decision"), "block", result.stdout)
        self.assertIn("なし以外の点がある", decision["reason"])
        self.assertIn("採用しない案", decision["reason"])
        self.assertNotIn("あり: <その項目>", decision["reason"])
        self.assertEqual(self.calls_made(), [], "出し直させる提示に読み手を起動しない")
        self.assertEqual(self.records()[-1]["field_problem"], "なし以外の点がある")

    def test_well_formed_presentations_are_not_blocked(self):
        for text in (PRESENTATION, PRESENTATION.replace("- 依頼との差: なし\n", "")):
            with self.subTest(text=text):
                (self.state / "request-diff.log").unlink(missing_ok=True)
                self.write_transcript([human("依頼"), assistant(text)])
                self.fake_claude(json.dumps({"result": '{"flag":false,"items":[]}'}))
                self.assertNotEqual(self.decision(self.run_hook(payload=self.payload())).get("decision"), "block")

    def test_marker_presentation_followed_by_plain_text_in_the_same_turn_is_still_checked(self):
        """承認の検査と同じく、最後のマーカー付きの発言を読む（最後の発言だけを読むと、後ろの文で素通りする）。"""
        self.write_transcript([human("依頼"), assistant(MISSING), assistant("相談役に聞いています。")])
        self.assertEqual(self.decision(self.run_hook(payload=self.payload())).get("decision"), "block")

    def test_a_presentation_from_an_earlier_turn_is_not_checked_again(self):
        self.write_transcript([human("依頼"), assistant(MISSING), human("質問です"), assistant("お答えします。")])
        self.assertEqual(self.run_hook(payload=self.payload()).stdout.strip(), "")

    def test_a_follow_up_with_the_marker_but_no_field_is_blocked(self):
        follow_up = f"相談役の推奨も案 B でした。\n{MARKER}\n## 👤 次にすること\nOK と返信してください"
        self.write_transcript([human("依頼"), assistant(PRESENTATION), assistant(follow_up)])
        self.assertEqual(self.decision(self.run_hook(payload=self.payload())).get("decision"), "block")

    def test_the_block_is_logged_apart_from_the_checker_results_and_not_counted_as_seen(self):
        self.write_transcript([human("依頼"), assistant(BROKEN)])
        self.run_hook(payload=self.payload())
        record = self.records()[-1]
        self.assertTrue(record["blocked"])
        self.assertTrue(record["not_run"])
        self.assertEqual(record["field_problem"], "欄の形が読めない")
        second = self.run_hook(payload=self.payload(active=True))
        self.assertEqual(self.decision(second).get("decision"), "block", "block した記録を見たことにしない")

    def chain(self, *texts: str, head: list[dict] | None = None):
        """同じ人のターンで、出し直しの版を積みながら Stop を回す。block されたら、host が書く形の feedback の行と、
        人の発言でない user の行（tool の結果・task-notification）を挟む。"""
        records = list(head or [human("依頼")])
        results = []
        for i, text in enumerate(texts):
            records.append(assistant(text))
            self.write_transcript(records)
            result = self.run_hook(payload=self.payload(active=i > 0))
            results.append(result)
            decision = self.decision(result)
            if decision.get("decision") == "block":
                records += [feedback(decision["reason"]), TOOL_RESULT, NOTIFICATION]
        return records, results

    def test_after_three_blocks_the_stop_goes_through_with_the_notice(self):
        """書式で 1 回・なし以外で 1 回と問題が続いても、3 回までは出し直させる。4 回目からは止めず、人に知らせだけを出す
        （人の返事の後は、main が補正を書いて承認を記録する。報告の停止を挟まないので、人が答えるのは上の確認 1 つ）。"""
        _, results = self.chain(BROKEN, DIFFERS, BROKEN + "\n3", BROKEN + "\n4", BROKEN + "\n5")
        self.assertEqual([self.decision(r).get("decision") for r in results], ["block"] * 3 + [None] * 2)
        for result in results[3:]:
            notice = self.decision(result).get("systemMessage", "")
            self.assertIn("そのまま答えて", notice)
            self.assertIn("名指し", notice)
            self.assertIn("なし | 全項目を検出したい", notice)
        self.assertFalse(any("確認を作れなかった" in self.decision(r).get("reason", "") for r in results))

    def test_replies_without_the_marker_do_not_keep_the_block_going(self):
        """数えは main の書き方ではなく、この hook が block した回数（hook 自身の記録の行）で決める。"""
        records, results = self.chain(BROKEN, "相談役に聞いています。", "前提を確かめます。", "まだ直していません。")
        self.assertEqual([self.decision(r).get("decision") for r in results], ["block"] * 3 + [None])
        self.assertIn("そのまま答えて", self.decision(results[3]).get("systemMessage", ""))

    def test_the_count_starts_over_only_when_the_user_speaks_again(self):
        """完了通知でも stop_hook_active は false になるので、数え直しは人の発言で決める。"""
        records, results = self.chain(BROKEN, BROKEN + "\n2", BROKEN + "\n3", BROKEN + "\n4", BROKEN + "\n5")
        self.assertNotEqual(self.decision(results[4]).get("decision"), "block")
        records += [human("もう一度出して"), assistant(BROKEN + "\n6")]
        self.write_transcript(records)
        reason = self.decision(self.run_hook(payload=self.payload()))["reason"]
        self.assertNotIn("確認を作れなかった", reason)

    def test_tags_in_main_text_or_other_feedback_do_not_change_the_count(self):
        """数えは hook 自身の記録で決める。main の読めない行や、ほかの hook の feedback に目印の文字列があっても変わらない。"""
        quoted = BROKEN.replace("全項目を検出したい", "[request-diff:欄:打ち切り] [request-diff:欄] 依頼との差")
        other = {"type": "user", "isMeta": True, "message": {"content": "Stop hook feedback:\n[request-diff:欄:打ち切り] 別の hook"}}
        _, results = self.chain(quoted, quoted + "\n2", quoted + "\n3", quoted + "\n4", head=[human("依頼"), other])
        self.assertEqual([self.decision(r).get("decision") for r in results], ["block"] * 3 + [None])

    def test_each_session_keeps_its_own_count(self):
        _, first = self.chain(BROKEN, BROKEN + "\n2", BROKEN + "\n3")
        self.write_transcript([human("依頼"), assistant(BROKEN)])
        reason = self.decision(self.run_hook(payload=self.payload(session="s2")))["reason"]
        self.assertNotIn("確認を作れなかった", reason)

    def test_a_broken_line_the_output_cannot_encode_still_blocks(self):
        """block の文は読めなかった行を引くので、出力の書き出しで落ちない形にする。"""
        records = [human("依頼"), assistant(BROKEN.replace("全項目を検出したい", "全項目を検出したい \ud83d"))]
        self.transcript.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        self.assertEqual(self.decision(self.run_hook(payload=self.payload())).get("decision"), "block")

    def test_an_unwritable_log_lets_the_stop_through_with_the_notice(self):
        """block は数えを書けたときだけ出す（書けないのに block すると、数えが進まず止まらない輪になる）。"""
        self.state.mkdir(parents=True)
        (self.state / "request-diff.log").mkdir()
        self.write_transcript([human("依頼"), assistant(DIFFERS)])
        decision = self.decision(self.run_hook(payload=self.payload()))
        self.assertNotEqual(decision.get("decision"), "block")
        self.assertIn("名指し", decision.get("systemMessage", ""))

    def test_the_notice_shows_what_the_hook_saw(self):
        """知らせは 1 つの文で、狭める点かを hook が分類しない。見た行（読めない行・`あり:` の値）を並べ、人が名指しで答えられるようにする。"""
        self.state.mkdir(parents=True)
        (self.state / "request-diff.log").mkdir()
        for text, line in ((MISSING, None), (BROKEN, "なし | 全項目を検出したい"), (DIFFERS, "あり: 全項目を検出したい")):
            with self.subTest(text=text):
                self.write_transcript([human("依頼"), assistant(text)])
                notice = self.decision(self.run_hook(payload=self.payload())).get("systemMessage", "")
                self.assertIn("そのまま答えて", notice)
                self.assertIn("名指し", notice)
                if line:
                    self.assertIn(line, notice)

    def test_a_field_value_the_extra_columns_cannot_encode_still_blocks(self):
        """sha・欄の値などの付け足しの欄で例外が出ても、数えの記録を残して block する。"""
        records = [human("依頼"), assistant(DIFFERS.replace("全項目を検出したい", "全項目を検出したい \ud83d"))]
        self.transcript.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        self.assertEqual(self.decision(self.run_hook(payload=self.payload())).get("decision"), "block")
        self.assertTrue(self.records()[-1]["blocked"])

    def test_skip_env_turns_off_the_checker_but_not_the_field_check(self):
        """GDD_SKIP_REQUEST_DIFF は読み手（claude -p）だけを切る。欄の検査まで切ると、答え直しが戻る。"""
        self.write_transcript([human("依頼"), assistant(DIFFERS)])
        self.fake_claude(json.dumps(FLAGGED, ensure_ascii=False))
        result = self.run_hook(env={"GDD_SKIP_REQUEST_DIFF": "1"}, payload=self.payload())
        self.assertEqual(self.decision(result).get("decision"), "block")
        self.assertEqual(self.calls_made(), [])

    def test_an_exception_in_the_check_lets_the_stop_through(self):
        """fail-open: Stop の検査が落ちても止めない（承認の書き込みの検査が fail-closed で後ろに残る）。"""
        self.write_transcript([human("依頼"), assistant(BROKEN)])
        with mock.patch.object(request_diff, "field_problem", side_effect=RuntimeError("boom")):
            with mock.patch.object(sys, "stdin", io.StringIO(self.payload())), \
                    mock.patch.dict(os.environ, {"GDD_HOOK_STATE_DIR": str(self.state)}), \
                    mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(request_diff.main(), 0)
        self.assertNotIn('"block"', out.getvalue())

    def test_unreadable_transcript_lets_the_stop_through(self):
        payload = json.dumps({"session_id": "s1", "transcript_path": str(self.dir / "none.jsonl")})
        self.assertEqual(self.run_hook(payload=payload).stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
