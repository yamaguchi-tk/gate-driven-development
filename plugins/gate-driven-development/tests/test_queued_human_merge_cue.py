"""turn の途中に queued で届いた人間の「マージした」を、マージ後の確認の合図として読むかのテスト。

Claude Code は、main が動いている間に届いた人間の発話を type:user の行ではなく、
attachment（type: queued_command、origin.kind: human）にだけ残すことがある。合図の判定は、
last_user_text と、その後に queued で届いた人間の本文のどちらかで一致すれば合図とみなす。
last_user_text（継続判定が読む）は変えない。
"""
from __future__ import annotations

import sys
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F401,F403
from lib.transcript import parse_transcript

_MISSING = object()
_PR_URL = "https://github.com/org/repo/pull/125"


def _user(text: str, ts: str | None = None) -> dict:
    record = {"type": "user", "origin": {"kind": "human"}, "message": {"content": [{"type": "text", "text": text}]}}
    if ts is not None:
        record["timestamp"] = ts
    return record


# host が注入する、人間の発話でない type:user 行（skill 起動の前置き。isMeta: true、origin なし）
SKILL_PREAMBLE = {"type": "user", "isMeta": True, "message": {"content": [
    {"type": "text", "text": "Base directory for this skill: /x/skills/gdd-using-git-worktrees\n\n# Worktrees"}]}}
CI_EVENT = {"type": "user", "message": {"content": [{"type": "text", "text": "<ci-monitor-event>CI failed</ci-monitor-event>"}]}}


def _assistant(text: str = "作業を続けます") -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def _queued(prompt: object, origin: object = _MISSING, ts: str | None = None) -> dict:
    attachment = {"type": "queued_command", "prompt": prompt}
    attachment["origin"] = {"kind": "human"} if origin is _MISSING else origin
    if origin is None:
        del attachment["origin"]
    record = {"type": "attachment", "isSidechain": False, "attachment": attachment}
    if ts is not None:
        record["timestamp"] = ts
    return record


def _texts(tv) -> list[str]:
    return [t for t, _ in tv.human_utterances]


PEER = {"type": "user", "origin": {"kind": "peer"}, "message": {"content": [
    {"type": "text", "text": "Another Claude session sent a message:\nhi"}]}}


def _parse(items: list[dict]):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "t.jsonl"
        p.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
        return parse_transcript(p)


class _MarkerRun:
    def _run(self, items: list[dict], created_at: object = _MISSING) -> dict | None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / ".claude").mkdir()
            marker = {"session_id": "test-session", "tasklist_path": "", "pr_url": _PR_URL,
                      "status": "pending_manual_merge"}
            if created_at is not _MISSING:
                marker["created_at_epoch"] = created_at
            (ws / ".claude" / "gdd-post-merge-continuation.json").write_text(json.dumps(marker), encoding="utf-8")
            transcript = ws / "transcript.jsonl"
            transcript.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
            code, out, err = _run_hook(ws, transcript)
            self.assertEqual(code, 0, err)
            return json.loads(out) if out.strip().startswith("{") else None

    def _assert_pending_block(self, payload: dict | None) -> None:
        self.assertIsNotNone(payload)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("Manual merge continuation が pending", payload["reason"])


class TestQueuedHumanMergeCueFromHook(_MarkerRun, unittest.TestCase):
    """入口（gdd_stop_hook.py）から: queued の人間の合図で、マージ後の確認の前の停止を止める。"""

    def test_queued_merge_cue_blocks_stop(self):
        for name, prompt in {"文字列": "マージした", "list": [{"type": "text", "text": "#125 はマージした"}]}.items():
            with self.subTest(prompt=name):
                self._assert_pending_block(self._run([_user("PR を作って"), _assistant(), _queued(prompt), _assistant("了解")]))

    def test_queued_cue_for_other_pr_does_not_block(self):
        self.assertIsNone(self._run([_user("PR を作って"), _assistant(), _queued("#999 はマージした"), _assistant()]))

    def test_later_queued_text_does_not_hide_typed_merge_cue(self):
        """type:user の「マージした」の後に queued の割り込みが来ても、合図は消えない。"""
        self._assert_pending_block(self._run([_user("マージした"), _assistant(), _queued("ありがとう"), _assistant()]))

    def test_typed_human_turn_clears_queued_cue(self):
        """queued の合図の後に type:user の人間の発話があれば、その発話で判定する。"""
        self.assertIsNone(self._run([_user("PR を作って"), _queued("マージした"), _assistant(),
                                     _user("別の話をしよう"), _assistant()]))

    def test_queued_cue_after_peer_does_not_block(self):
        """peer の後の queued の人間の合図では、今までどおり確認を始めない（peer turn のまま）。"""
        self.assertIsNone(self._run([_user("PR を作って"), _assistant(), PEER, _queued("マージした"), _assistant()]))

    def test_queued_human_text_does_not_change_last_user_text(self):
        """継続判定が読む last_user_text は変えない。"""
        tv = _parse([_user("/gdd-dev 続けて"), _queued("マージした"), _assistant()])
        self.assertEqual(tv.last_user_text, "/gdd-dev 続けて")
        self.assertEqual(_texts(tv), ["/gdd-dev 続けて", "マージした"])

    def test_host_injected_user_rows_do_not_clear_merge_cue(self):
        """止めるべき並びを通さない: 合図の後の skill の前置き・ci-monitor-event の行で、合図を消さない。"""
        for name, cue in {"type:user の合図": [_user("マージした")], "queued の合図": [_user("PR を作って"), _queued("マージした")]}.items():
            for injected_name, injected in {"skill の前置き": SKILL_PREAMBLE, "ci-monitor-event": CI_EVENT}.items():
                with self.subTest(cue=name, injected=injected_name):
                    self._assert_pending_block(self._run(cue + [_assistant(), injected, _assistant()]))


class TestQueuedHumanMergeCueFailOpen(_MarkerRun, unittest.TestCase):
    """L1+ 安全策 2 の fail-open の 3 ケース。"""

    def test_non_human_queued_lines_are_not_merge_cues(self):
        """人間の行でなければ合図にしない（peer・通知・origin の無い行・形の崩れた origin・remove の行）。"""
        cases = {
            "peer": _queued("マージした", {"kind": "peer"}),
            "task-notification": _queued("マージした", {"kind": "task-notification"}),
            "origin 無し": _queued("マージした", None),
            "kind が数値": _queued("マージした", {"kind": 3}),
            "origin が文字列": _queued("マージした", "human"),
            "remove の行": {"type": "queue-operation", "operation": "remove", "content": "マージした"},
            "hook の注入": _queued("Stop hook feedback: マージした"),
        }
        for name, record in cases.items():
            with self.subTest(case=name):
                self.assertIsNone(self._run([_user("PR を作って"), _assistant(), record, _assistant()]))

    def test_later_cue_for_other_pr_does_not_hide_earlier_cue(self):
        """止めるべき並びを通さない: 後から届いた別の PR の合図で、前の合図を打ち消さない。"""
        cases = {
            "type:user の合図 → queued の別の PR": [_user("マージした"), _assistant(), _queued("#999 もマージした")],
            "queued の別の PR → queued の合図": [_user("PR を作って"), _queued("#999 はマージした"), _queued("マージした")],
            "queued の合図 → queued の別の PR": [_user("PR を作って"), _queued("マージした"), _queued("別の PR もマージした")],
        }
        for name, items in cases.items():
            with self.subTest(case=name):
                self._assert_pending_block(self._run(items + [_assistant()]))

    def test_malformed_queued_human_lines_do_not_crash(self):
        """例外で落ちない: prompt が変な形でも skipped は空で、後ろの合図は読む。"""
        malformed = [_queued(None), _queued(3), _queued({"text": "マージした"}),
                     _queued([3, None, {"type": ["text"], "text": "x"}, {"type": "text", "text": None}])]
        tv = _parse([_user("PR を作って")] + malformed + [_queued("マージした")])
        self.assertEqual(tv.skipped, [])
        self.assertEqual(_texts(tv), ["PR を作って", "マージした"])
        self._assert_pending_block(self._run([_user("PR を作って")] + malformed + [_queued("マージした"), _assistant()]))

    def test_cue_before_marker_creation_does_not_block(self):
        """古い合図（PR の URL が初めて出た時刻より前）は数えない。その後の合図は数える。"""
        created = 1_768_464_000  # 2026-01-15T08:00:00Z
        before, after = "2026-01-15T07:00:00.000Z", "2026-01-15T09:00:00.000Z"
        pr_made = _assistant_at(f"{_PR_URL} を作りました", "2026-01-15T08:00:00.000Z")
        for name, items in {"type:user": [_user("マージした", before)],
                            "queued": [_user("PR を作って", before), _queued("マージした", ts=before)]}.items():
            with self.subTest(case=name, when="before"):
                self.assertIsNone(self._run(items + [pr_made, CI_EVENT, _assistant()], created_at=created))
        for name, items in {"type:user": [_user("マージした", after)],
                            "queued": [_user("PR を作って", before), _queued("マージした", ts=after)]}.items():
            with self.subTest(case=name, when="after"):
                self._assert_pending_block(self._run(items + [pr_made, CI_EVENT, _assistant()], created_at=created))

    def test_unreadable_times_count_the_cue(self):
        """判定できないときは止める側: 合図の時刻か marker の時刻が読めなければ、合図として数える。"""
        cases = {
            "合図の時刻が壊れている": ([_user("マージした", "not-a-time")], 1_800_000_000),
            "合図の時刻が無い": ([_user("マージした")], 1_800_000_000),
            "marker の時刻が文字列": ([_user("マージした", "2027-01-15T07:00:00Z")], "x"),
            "marker の時刻が無い": ([_user("マージした", "2027-01-15T07:00:00Z")], _MISSING),
        }
        for name, (items, created) in cases.items():
            with self.subTest(case=name):
                self._assert_pending_block(self._run(items + [_assistant(), CI_EVENT, _assistant()], created_at=created))

    def test_unreadable_marker_with_queued_cue_blocks(self):
        """判定できないときは止める側: marker が通常のファイルとして読めないとき、queued の合図でも block する。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / ".claude" / "gdd-post-merge-continuation.json").mkdir(parents=True)
            transcript = ws / "transcript.jsonl"
            transcript.write_text("\n".join(json.dumps(i) for i in [
                _user("PR を作って"), _queued("マージした"), _assistant()]) + "\n", encoding="utf-8")
            code, out, err = _run_hook(ws, transcript)
            self.assertEqual(code, 0, err)
            payload = json.loads(out)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("通常のファイルとして読めない", payload["reason"])


def _assistant_at(text: str, ts: str) -> dict:
    return {"type": "assistant", "timestamp": ts, "message": {"content": [{"type": "text", "text": text}]}}


# 合図の語を本文に含む、実物に近い skill の前置き（gdd-using-git-worktrees の Post-Merge Cleanup）
SKILL_PREAMBLE_WITH_CUE = {"type": "user", "isMeta": True, "message": {"content": [{"type": "text", "text": (
    "Base directory for this skill: /x/skills/gdd-using-git-worktrees\n\n"
    "ユーザーが「マージした」と報告したら、旧 worktree を整理する。")}]}}


class TestMergeCueOnlyFromHumanPastReport(_MarkerRun, unittest.TestCase):
    """合図は人間の発話の、マージを済ませた報告だけから取る。"""

    def test_host_injected_text_with_cue_word_is_not_a_cue(self):
        """止めない側: 人間の発話に origin.kind human が付く transcript では、注入の行の本文の語を合図にしない。"""
        for injected_name, injected in {"skill の前置き": SKILL_PREAMBLE_WITH_CUE,
                                        "compaction の要約": {"type": "user", "message": {"content": [{"type": "text", "text": (
                                            "This session is being continued from a previous conversation. ユーザーは「マージした」と報告した")}]}}}.items():
            with self.subTest(injected=injected_name):
                self.assertIsNone(self._run([_user("PR を作って"), _assistant(), injected, _assistant()]))

    def test_transcript_without_human_origin_keeps_reading_last_user_text(self):
        """origin を書かない版（人間の行に origin が無い transcript）は、今までどおり直近のユーザー入力を読む。"""
        plain = {"type": "user", "message": {"content": [{"type": "text", "text": "マージした"}]}}
        self._assert_pending_block(self._run([plain, _assistant()]))

    def test_not_yet_merged_utterances_are_not_cues(self):
        for text in ("マージしたら次に進んで", "セルフレビューでマージしたい", "このPRはマージした方が良い？",
                     "マージした？", "7月にマージしたPRを見て"):
            for name, items in {"type:user": [_user(text)], "queued": [_user("PR を作って"), _queued(text)]}.items():
                with self.subTest(text=text, form=name):
                    self.assertIsNone(self._run(items + [_assistant()]))

    def test_past_reports_are_cues(self):
        for text in ("マージした", "マージした。確認して", "#125 をマージしたので確認して", "312をマージしたがCIが通らない",
                     "merged", "Merged."):
            for name, items in {"type:user": [_user(text)], "queued": [_user("PR を作って"), _queued(text)]}.items():
                with self.subTest(text=text, form=name):
                    self._assert_pending_block(self._run(items + [_assistant()]))


class TestMergeCueTimeBoundary(_MarkerRun, unittest.TestCase):
    """合図の時刻の境界は、marker の PR の URL が assistant の本文に初めて出た時刻。"""

    T0, T1, T2, T3 = ("2026-01-15T07:00:00Z", "2026-01-15T08:00:00Z", "2026-01-15T08:30:00Z", "2026-01-15T09:00:00Z")
    T4, T5 = "2026-01-15T10:00:00Z", "2026-01-15T10:30:00Z"
    CREATED = 1_768_467_600  # 2026-01-15T09:00:00Z（done の Stop で marker を書いた時刻）

    def test_cue_between_pr_creation_and_marker_counts(self):
        """PR を作った後・marker を書く前に queued で届いた合図も数える。"""
        items = [_user("PR を作って", self.T0), _assistant_at(f"PR を作りました: {_PR_URL}", self.T1),
                 _queued("マージした", ts=self.T2), _assistant_at("CI を待ちます", self.T2), CI_EVENT, _assistant()]
        self._assert_pending_block(self._run(items, created_at=self.CREATED))

    def test_cue_before_pr_creation_does_not_count(self):
        """PR を作る前の古い合図は数えない。"""
        items = [_user("マージした", self.T0), _assistant_at("別の作業", self.T0), CI_EVENT,
                 _assistant_at(f"PR を作りました: {_PR_URL}", self.T1), CI_EVENT, _assistant()]
        self.assertIsNone(self._run(items, created_at=self.CREATED))

    def test_cue_in_another_session_before_url_counts(self):
        """PR を作った record の無い別の session: marker の後の合図は、その後に assistant が URL を書いても数える。"""
        items = [_user("マージした", self.T4), _assistant_at(f"{_PR_URL} のマージを確認します", self.T5),
                 CI_EVENT, _assistant()]
        self._assert_pending_block(self._run(items, created_at=self.CREATED))

    def test_cue_after_marker_without_url_counts_and_before_does_not(self):
        """URL が transcript に無ければ marker の時刻で区切る。"""
        after = [_user("マージした", self.T4), _assistant(), CI_EVENT, _assistant()]
        self._assert_pending_block(self._run(after, created_at=self.CREATED))
        before = [_user("マージした", self.T0), _assistant_at("別の作業", self.T0), CI_EVENT, _assistant()]
        self.assertIsNone(self._run(before, created_at=self.CREATED))

    def test_unreadable_url_time_counts_the_cue(self):
        """判定できないときは止める側: URL の record の時刻が読めなければ区切らない。"""
        items = [_user("PR を作って", self.T0), _assistant_at(f"PR を作りました: {_PR_URL}", "not-a-time"),
                 _queued("マージした", ts=self.T2), _assistant_at("CI を待ちます", self.T2), CI_EVENT, _assistant()]
        self._assert_pending_block(self._run(items, created_at=self.CREATED))

    def test_unusable_marker_time_with_url_counts_the_cue(self):
        """判定できないときは止める側: marker の時刻が使えなければ、URL があっても区切らない。"""
        for name, created in {"未来": 4_000_000_000, "文字列": "x", "無い": _MISSING}.items():
            with self.subTest(created=name):
                items = [_user("マージした", self.T0), _assistant_at("別の作業", self.T0), CI_EVENT,
                         _assistant_at(f"PR を作りました: {_PR_URL}", self.T1), CI_EVENT, _assistant()]
                self._assert_pending_block(self._run(items, created_at=created))

    def test_unusable_marker_time_counts_the_cue(self):
        """判定できないときは止める側: URL が transcript に無く、marker の時刻が使えない値なら合図に数える。"""
        for name, created in {"NaN": float("nan"), "Infinity": float("inf"), "ミリ秒": 1_800_000_000_000,
                              "未来": 4_000_000_000, "負": -1, "bool": True}.items():
            with self.subTest(created=name):
                self._assert_pending_block(self._run([_user("マージした", self.T0), _assistant(), CI_EVENT, _assistant()],
                                                     created_at=created))


if __name__ == "__main__":
    unittest.main()
