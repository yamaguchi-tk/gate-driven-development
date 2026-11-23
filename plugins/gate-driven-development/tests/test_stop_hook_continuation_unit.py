"""Stop hook の継続の判定（`active: false` の早期終了・`looks_like_gdd_continuation()`・連続 block の上限の窓）の単体テスト。

`test_stop_hook_unit.py` から分けた。確かめる本体は `hooks/scripts/gdd_stop_hook.py`・`hooks/scripts/lib/guards.py`。
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F811
import sys
import time
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F403


# Default last_assistant for approval tests: a human-check pause surface.
# looks_like_gdd_continuation() only fires approval when last_assistant contains
# a human-check pause marker — without it, "OK" alone returns False (correct contract).
_HC = '<gdd-stop reason="human-check-waiting">'


class TestLooksLikeGddContinuation(unittest.TestCase):
    """Comprehensive tests for the continuation gating logic.

    Contract: returns True only when the current conversation clearly signals
    that an active GDD workflow should keep running. Returns False for
    unrelated inputs so stale gdd-dev.local.md files don't hijack other chats.
    """

    def _c(self, user_text, last_assistant=_HC):
        return looks_like_gdd_continuation(user_text, last_assistant)

    # --- Inputs that SHOULD trigger continuation ---

    def test_gdd_dev_slash_at_line_start_triggers(self):
        self.assertTrue(self._c("/gdd-dev 新しいタスク"))

    def test_gdd_status_slash_triggers(self):
        self.assertTrue(self._c("/gdd-status"))

    def test_gdd_slash_with_leading_space_triggers(self):
        self.assertTrue(self._c("  /gdd-dev resume"))

    def test_gdd_skill_name_in_text_triggers(self):
        self.assertTrue(self._c("gdd-brainstorming を実行して"))
        self.assertTrue(self._c("gdd-implementation-gating を再実行"))
        self.assertTrue(self._c("gdd-completion-check をスキップして"))

    def test_approval_english_triggers(self):
        self.assertTrue(self._c("OK"))
        self.assertTrue(self._c("ok"))
        self.assertTrue(self._c("Ok!"))
        self.assertTrue(self._c("yes"))
        self.assertTrue(self._c("YES"))
        self.assertTrue(self._c("y"))
        self.assertTrue(self._c("approved"))
        self.assertTrue(self._c("approve"))

    def test_approval_japanese_triggers(self):
        self.assertTrue(self._c("はい"))
        self.assertTrue(self._c("承認"))
        self.assertTrue(self._c("進めて"))
        self.assertTrue(self._c("続けて"))

    def test_approval_emoji_triggers(self):
        self.assertTrue(self._c("👍"))
        self.assertTrue(self._c("✅"))

    def test_approval_with_trailing_punctuation_triggers(self):
        self.assertTrue(self._c("OK!"))
        self.assertTrue(self._c("OK。"))
        self.assertTrue(self._c("はい、"))

    def test_phase_marker_in_last_assistant_triggers(self):
        """Phase mid-flight: continuation regardless of user text."""
        self.assertTrue(self._c(
            "別の話題",
            "<gdd-phase>gdd-task-breakdown</gdd-phase>\n実装中です。",
        ))

    def test_human_check_waiting_marker_in_last_assistant_triggers(self):
        self.assertTrue(self._c(
            "OK",
            '## 🔍 確認をお願いします\n承認ポイント\n<gdd-stop reason="human-check-waiting">',
        ))

    def test_human_check_japanese_marker_in_last_assistant_triggers(self):
        self.assertTrue(self._c("はい", "🔍 確認をお願いします"))

    def test_承認ポイント_keyword_in_last_assistant_triggers(self):
        self.assertTrue(self._c("OK", "以下の承認ポイントを確認してください。"))

    # --- Inputs that should NOT trigger continuation ---

    def test_unrelated_question_does_not_trigger(self):
        self.assertFalse(self._c("Pythonでファイルを読む方法を教えて"))

    def test_unrelated_short_replies_do_not_trigger(self):
        self.assertFalse(self._c("ありがとう"))
        self.assertFalse(self._c("なるほど"))
        self.assertFalse(self._c("わかりました"))

    def test_approval_followed_by_unrelated_text_does_not_trigger(self):
        """'OK but ...' is too long to match _APPROVAL_REPLY_RE (anchored ^ ... $)."""
        self.assertFalse(self._c("OK but I have a question about something else"))
        self.assertFalse(self._c("OKです、でも別のことも聞きたいのですが"))

    def test_empty_inputs_do_not_trigger(self):
        self.assertFalse(self._c("", ""))
        self.assertFalse(self._c("", None))

    def test_none_inputs_do_not_trigger(self):
        self.assertFalse(self._c(None, None))

    def test_gdd_skill_name_in_sentence_still_triggers(self):
        """_GDD_SKILL_REF_RE matches 'gdd-dev' anywhere in the text (word boundary only).
        Even mid-sentence mentions of a GDD skill name trigger continuation.
        The SLASH regex requires line-start but SKILL_REF does not."""
        self.assertTrue(self._c("I was using /gdd-dev before but need Python help"))
        # Pure non-GDD text (no skill name at all) → should not trigger
        self.assertFalse(self._c("I was asking about Python before but need help now"))

    def test_unrelated_multiline_no_gdd_marker_does_not_trigger(self):
        self.assertFalse(self._c(
            "別の話題について質問があります\nどう実装すればよいですか？",
            "こちらが通常の回答です。GDD に関係ありません。",
        ))

    def test_continue_go_triggers(self):
        """'continue' and 'go' are in the approval pattern."""
        self.assertTrue(self._c("continue"))
        self.assertTrue(self._c("go"))

    def test_done_as_approval_triggers(self):
        """'done' alone is a valid approval reply (user confirms task is done)."""
        self.assertTrue(self._c("done"))

    def test_done_with_extra_words_does_not_trigger(self):
        """'done with this, what's next?' is too long."""
        self.assertFalse(self._c("done with this, what's next?"))


class TestCeilingResetWindow(unittest.TestCase):
    """AC-E9-3: consecutive_stop_hook_blocks must not reset just because
    stop_hook_active=false — a background Agent's <task-notification> also
    arrives as a stop_hook_active=false turn, and resetting on every such
    notification would let a long completion wait restart the block burst
    forever. Reset is now gated on GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS."""

    def setUp(self):
        import gdd_stop_hook
        self.hook = gdd_stop_hook
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tmp.name) / "gdd-dev.local.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_stop_hook_active_true_always_increments(self):
        now = int(time.time())
        frontmatter = {
            "consecutive_stop_hook_blocks": "3",
            "consecutive_stop_hook_blocks_at": str(now - 999999),
        }
        self.hook.enforce_consecutive_block_ceiling(
            {"stop_hook_active": True}, frontmatter, "body", self.state_path,
        )
        self.assertEqual(frontmatter["consecutive_stop_hook_blocks"], "4")

    def test_false_within_window_continues_counting(self):
        now = int(time.time())
        frontmatter = {
            "consecutive_stop_hook_blocks": "3",
            "consecutive_stop_hook_blocks_at": str(now - 5),
        }
        self.hook.enforce_consecutive_block_ceiling(
            {"stop_hook_active": False}, frontmatter, "body", self.state_path,
        )
        self.assertEqual(
            frontmatter["consecutive_stop_hook_blocks"], "4",
            "a stop_hook_active=false call shortly after the previous block "
            "(e.g. a <task-notification> turn) must not reset the counter",
        )

    def test_false_outside_window_resets(self):
        now = int(time.time())
        window = self.hook.GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS
        frontmatter = {
            "consecutive_stop_hook_blocks": "5",
            "consecutive_stop_hook_blocks_at": str(now - window - 10),
        }
        self.hook.enforce_consecutive_block_ceiling(
            {"stop_hook_active": False}, frontmatter, "body", self.state_path,
        )
        self.assertEqual(
            frontmatter["consecutive_stop_hook_blocks"], "0",
            "a stop_hook_active=false call after the reset window has "
            "elapsed must be treated as a genuinely fresh turn and reset",
        )

    def test_missing_at_field_falls_back_safely(self):
        frontmatter = {"consecutive_stop_hook_blocks": "4"}
        self.hook.enforce_consecutive_block_ceiling(
            {"stop_hook_active": False}, frontmatter, "body", self.state_path,
        )
        self.assertEqual(
            frontmatter["consecutive_stop_hook_blocks"], "0",
            "missing consecutive_stop_hook_blocks_at must fail safe (reset) "
            "instead of assuming an in-window burst",
        )


if __name__ == "__main__":
    unittest.main()
