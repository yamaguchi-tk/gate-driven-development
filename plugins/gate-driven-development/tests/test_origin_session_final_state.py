"""ApplyPatch の `Origin Session` は、patch を当てた後の値を推定せずに判定する。

patch の当て方（Codex の緩い照合・fence・同じファイルの別の綴り・move の連鎖）を hook で写すと、
写しと実物のずれが開いた入力になる。値の推定はやめ、state.md に届く ApplyPatch は、ターンによらず、
patch・move で流れ込む移動元・既存の state.md のどこかに（バッククォートを除いて）field の語があれば止める。
apply_patch は行を新しく作らないので、当てた後の state.md の行はこの 3 か所のどれかから来る。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import PLUGIN_ROOT  # noqa: E402
from test_peer_turn_write_boundary_contract import PEER_RECORD, write_transcript  # noqa: E402

VALIDATE = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
INTERNAL_ERROR = "internal error and fails closed"
PATCH_MESSAGE = "does not estimate the value after an ApplyPatch"
MOVE_MESSAGE = "moves a file onto a `state.md`"

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
_spec = importlib.util.spec_from_file_location("validate_steering_write", VALIDATE)
validate_steering_write = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_steering_write)


def patch_of(*hunks: str) -> str:
    return "*** Begin Patch\n" + "".join(hunks) + "*** End Patch\n"


class _Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.dir = Path(self._tmp) / ".steering" / "20261003-x"
        self.dir.mkdir(parents=True)
        self.state = self.dir / "state.md"
        self.notes = self.dir / "notes.md"

    def write(self, state: str | None, notes: str | None = None) -> None:
        if state is not None:
            self.state.write_text(state, encoding="utf-8")
        if notes is not None:
            self.notes.write_text(notes, encoding="utf-8")


class HookEntryTest(_Fixture):
    """hook の入口（stdin の payload）から判定まで通す（非 peer turn）。"""

    peer_turn = False

    def run_patch(self, patch: str) -> tuple[int, str]:
        payload: dict = {"tool_name": "ApplyPatch", "tool_input": {"patch": patch}}
        if self.peer_turn:
            transcript = Path(self._tmp) / "transcript.jsonl"
            write_transcript(transcript, [PEER_RECORD])
            payload["transcript_path"] = str(transcript)
        with tempfile.TemporaryDirectory() as hook_state:
            result = subprocess.run(
                [sys.executable, str(VALIDATE)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                env=dict(os.environ, GDD_HOOK_STATE_DIR=hook_state),
                cwd=self._tmp,
                timeout=20,
            )
        return result.returncode, result.stderr

    def assertDenied(self, patch: str, message: str = "Origin Session") -> None:
        code, err = self.run_patch(patch)
        self.assertEqual(code, 2, err)
        text = json.loads(err)["systemMessage"]  # deny の本文は JSON の \u エスケープで出る
        self.assertIn(message, text)
        self.assertNotIn(INTERNAL_ERROR, text)

    def assertAllowed(self, patch: str) -> None:
        code, err = self.run_patch(patch)
        self.assertEqual(code, 0, err)

    def test_patch_on_a_state_md_with_a_value_is_denied_even_if_it_keeps_the_value(self) -> None:
        # 値を推定しない。既存値のある state.md への ApplyPatch は、値の行に触れなくても止める
        self.write("- Origin Session: X\nnote\n")
        for patch in (
            patch_of(f"*** Update File: {self.state}\n@@\n-note\n+note2\n"),
            patch_of(f"*** Update File: {self.state}\n@@\n-- Origin Session: X\n+- Origin Session: X\n"),
            patch_of(f"*** Update File: {self.state}\n@@\n+```\n - Origin Session: X\n+```\n"),
            patch_of(f"*** Update File: {self.state}\n@@\n-- Origin Session: X\n"),
            patch_of(f"*** Delete File: {self.state}\n", f"*** Add File: {self.state}\n+- Origin Session: X\n"),
            patch_of(f"*** Update File: {self.state}\n*** Move to: {self.notes}\n@@\n note\n"),
        ):
            with self.subTest(patch=patch):
                self.assertDenied(patch, PATCH_MESSAGE)

    def test_patch_on_another_spelling_of_a_state_md_with_a_value_is_denied(self) -> None:
        self.write("- Origin Session: X\nnote\n")
        (self.dir / "sub").mkdir()
        self.assertDenied(
            patch_of(f"*** Update File: {self.dir}/sub/../state.md\n@@\n-note\n+note2\n"), PATCH_MESSAGE
        )

    def test_patch_on_a_state_md_without_a_value_is_allowed(self) -> None:
        self.write("- Resume From: a\nnote\n", "x\n")
        for patch in (
            patch_of(f"*** Update File: {self.state}\n@@\n-note\n+note2\n"),
            patch_of(f"*** Update File: {self.state}\n@@\n note\n+```\n+example\n+```\n"),
        ):
            with self.subTest(patch=patch):
                self.assertAllowed(patch)

    def test_first_value_from_a_normal_turn_is_denied(self) -> None:
        # 初回の値も ApplyPatch では書かせない（Write・Edit で書く）
        self.assertDenied(patch_of(f"*** Add File: {self.state}\n+- Origin Session: a\n+note\n"), PATCH_MESSAGE)
        self.write("note\n")
        self.assertDenied(patch_of(f"*** Update File: {self.state}\n@@\n note\n+- Origin Session: a\n"), PATCH_MESSAGE)

    def test_field_name_split_by_a_backtick_is_denied(self) -> None:
        # reader はバッククォートを除いてから field 名を照合する
        self.write("note\n")
        self.assertDenied(patch_of(f"*** Update File: {self.state}\n@@\n note\n+- O`rigin Session: x\n"), PATCH_MESSAGE)

    def test_opening_a_fenced_example_in_the_file_is_denied(self) -> None:
        # patch に語が無くても、fence の開きを消すと既存の記入例が値になる
        self.write("note\n```text\n- Origin Session: x\n```\n")
        self.assertDenied(patch_of(f"*** Update File: {self.state}\n@@\n note\n-```text\n+memo\n"), PATCH_MESSAGE)

    def test_move_onto_a_state_md_is_denied_without_reading_the_source(self) -> None:
        # 移動元は読まない（巨大なファイル・FIFO で hook の timeout に届かない）。値の有無・ターンによらず止める
        fifo = self.dir / "fifo.md"
        os.mkfifo(fifo)
        for state in ("- Origin Session: X\n", "note\n"):
            with self.subTest(state=state):
                self.write(state, "x\n")
                self.assertDenied(patch_of(f"*** Update File: {fifo}\n*** Move to: {self.state}\n@@\n+y\n"), MOVE_MESSAGE)
                self.assertDenied(
                    patch_of(f"*** Update File: {self.notes}\n*** Move to: {self.state}\n@@\n-x\n+y\n"), MOVE_MESSAGE
                )

    def test_values_carried_by_a_move_are_denied(self) -> None:
        self.write("note\n", "- Origin Session: A\n- Origin Session: B\nfoo\n")
        self.assertDenied(
            patch_of(f"*** Update File: {self.notes}\n*** Move to: {self.state}\n@@\n-foo\n+bar\n"), MOVE_MESSAGE
        )

    def test_chain_of_moves_with_another_spelling_is_denied(self) -> None:
        # `./b.md` は `b.md` と綴りが違うので、移動元の連鎖をたどると a.md の値を見落とす
        self.write("note\n")
        relay_a = Path(self._tmp) / "a.md"
        relay_a.write_text("- Origin Session: Y\nkeep\n", encoding="utf-8")
        self.assertDenied(patch_of(
            f"*** Update File: {relay_a}\n*** Move to: {self._tmp}/b.md\n@@\n-keep\n+keep2\n",
            f"*** Update File: {self._tmp}/./b.md\n*** Move to: {self.state}\n@@\n-keep2\n+keep3\n",
        ), MOVE_MESSAGE)

    def test_stray_move_onto_a_state_md_is_denied(self) -> None:
        self.write("note\n", "x\n")
        self.assertDenied(patch_of(f"*** Add File: {self.notes}\n+x\n*** Move to: {self.state}\n"), MOVE_MESSAGE)

    def test_values_behind_a_fence_in_another_file_are_denied(self) -> None:
        self.write("note\n", "x\n")
        self.assertDenied(patch_of(
            f"*** Update File: {self.notes}\n@@\n x\n+```\n",
            f"*** Update File: {self.state}\n@@\n note\n+- Origin Session: a\n+- Origin Session: b\n+```\n",
        ), PATCH_MESSAGE)

    def test_patch_not_reaching_a_state_md_is_allowed(self) -> None:
        self.write("- Origin Session: X\n", "x\n")
        self.assertAllowed(patch_of(f"*** Update File: {self.notes}\n@@\n-x\n+- Origin Session: Y\n"))

class PeerTurnHookEntryTest(_Fixture):
    """peer turn の transcript を渡して、hook の入口から判定まで通す。"""

    peer_turn = True
    run_patch = HookEntryTest.run_patch
    assertDenied = HookEntryTest.assertDenied
    assertAllowed = HookEntryTest.assertAllowed

    def test_patch_naming_the_field_on_a_state_md_without_a_value_is_denied(self) -> None:
        self.write("note\n", "x\n")
        for patch in (
            patch_of(f"*** Update File: {self.state}\n@@\n note\n+- Origin Session: Y\n"),
            patch_of(f"*** Add File: {self.state}\n+- Origin Session: Y\n"),
            # 値の無い行・別のファイルの行でも、patch のどこかに語があれば止める（値を推定しない）
            patch_of(f"*** Update File: {self.state}\n@@\n note\n+- Origin Session:\n"),
            patch_of(
                f"*** Update File: {self.notes}\n@@\n-x\n+- Origin Session: Y\n",
                f"*** Update File: {self.state}\n@@\n note\n+memo\n",
            ),
        ):
            with self.subTest(patch=patch):
                self.assertDenied(patch, PATCH_MESSAGE)

    def test_value_carried_by_a_move_into_a_state_md_without_a_value_is_denied(self) -> None:
        self.write("note\n", "- Origin Session: Y\nfoo\n")
        self.assertDenied(
            patch_of(f"*** Update File: {self.notes}\n*** Move to: {self.state}\n@@\n-foo\n+bar\n"),
            MOVE_MESSAGE,
        )

    def test_move_from_fifo_into_a_state_md_without_a_value_is_denied_without_hanging(self) -> None:
        self.write("note\n")
        fifo = self.dir / "fifo.md"
        os.mkfifo(fifo)
        self.assertDenied(
            patch_of(f"*** Update File: {fifo}\n*** Move to: {self.state}\n@@\n+y\n"), MOVE_MESSAGE
        )

    def test_patch_without_the_field_on_a_state_md_without_a_value_is_allowed(self) -> None:
        self.write("note\n", "foo\n")
        self.assertAllowed(patch_of(f"*** Update File: {self.state}\n@@\n note\n+memo\n"))

    def test_approval_carried_by_a_chain_of_moves_is_denied(self) -> None:
        self.write("- Human Check Status: pending\n")
        relay_a = Path(self._tmp) / "a.md"
        relay_b = Path(self._tmp) / "b.md"
        relay_a.write_text("keep\n- Human Check Status: approved\n", encoding="utf-8")
        relay_b.write_text("keep\n", encoding="utf-8")
        self.assertDenied(patch_of(
            f"*** Update File: {relay_a}\n*** Move to: {relay_b}\n@@\n-keep\n+keep\n",
            f"*** Update File: {relay_b}\n*** Move to: {self.state}\n@@\n-keep\n+keep\n",
        ), MOVE_MESSAGE)

    def test_approval_moved_from_a_name_with_backslash_is_denied(self) -> None:
        self.write("- Human Check Status: pending\n")
        source = Path(self._tmp) / "x\\y.md"
        source.write_text("- Human Check Status: approved\nfoo\n", encoding="utf-8")
        self.assertDenied(patch_of(
            f"*** Update File: {source}\n*** Move to: {self.state}\n@@\n-foo\n+bar\n"
        ), MOVE_MESSAGE)

    def test_move_from_fifo_is_denied_without_hanging(self) -> None:
        self.write("- Human Check Status: pending\n")
        fifo = Path(self._tmp) / "fifo.md"
        os.mkfifo(fifo)
        self.assertDenied(patch_of(f"*** Update File: {fifo}\n*** Move to: {self.state}\n@@\n+y\n"), MOVE_MESSAGE)

    def test_move_without_records_onto_a_state_md_is_denied(self) -> None:
        self.write("- Human Check Status: pending\n", "foo\n")
        self.assertDenied(
            patch_of(f"*** Update File: {self.notes}\n*** Move to: {self.state}\n@@\n-foo\n+bar\n"), MOVE_MESSAGE
        )


class PeerTurnTest(_Fixture):
    """peer turn の判定（関数を直接呼ぶ）。"""

    def peer_record(self, patch: str) -> list:
        tool_input = {"patch": patch}
        chunks = validate_steering_write.extract_content_chunks("ApplyPatch", tool_input)
        return validate_steering_write.collect_peer_turn_state_write_violations(
            [str(self.state)], tool_input, chunks, True, "ApplyPatch"
        )

    def test_moved_record_of_approval_is_denied(self) -> None:
        self.write("- Human Check Status: pending\n", "- Human Check Status: approved\nfoo\n")
        patch = patch_of(f"*** Update File: {self.notes}\n*** Move to: {self.state}\n@@\n-foo\n+bar\n")
        self.assertTrue(self.peer_record(patch))

    def test_record_moved_out_of_steering_is_allowed(self) -> None:
        self.write("- Human Check Status: pending\n", "- Human Check Status: approved\nfoo\n")
        outside = Path(self._tmp) / "outside.md"
        patch = patch_of(f"*** Update File: {self.notes}\n*** Move to: {outside}\n@@\n-foo\n+bar\n")
        self.assertEqual(self.peer_record(patch), [])


class InflowSourcesTest(unittest.TestCase):
    def test_long_chain_of_moves_is_followed_in_linear_time(self) -> None:
        # hook の timeout（10 秒）で検査ごと通らないよう、連鎖の長さに比例する時間でたどる
        import time

        from lib.patch_scoping import patch_inflow_sources

        n = 3000
        patch = patch_of(*(f"*** Update File: a{i}.md\n*** Move to: a{i + 1}.md\n" for i in range(n)))
        started = time.monotonic()
        sources = patch_inflow_sources(patch, f"a{n}.md")
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual(sorted(sources), sorted(f"a{i}.md" for i in range(n)))


if __name__ == "__main__":
    unittest.main()
