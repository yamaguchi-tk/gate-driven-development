"""ApplyPatch の section の切り方を 1 つの走査にし、Codex の apply_patch と同じ規則で読む。

Codex（openai/codex の codex-rs/apply-patch/src/streaming_parser.rs）の規則:
  - `*** End of File` の後ろの `@@` は、同じファイルの次の chunk になる
  - header は、ファイルの間・Add・Delete の状態では行の前後の空白を落として判定する。
    Update の状態では行末の空白だけを落とす（先頭に空白のある行は context 行）
  - section の中の `+++x` は `++x` の追加行（unified diff の header ではない）
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

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib import patch_scoping  # noqa: E402

VALIDATE = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
INTERNAL_ERROR = "internal error and fails closed"
LINE_BREAK = "U+000B"  # deny の本文は JSON の \u エスケープで出るので、ASCII の部分で見る

_spec = importlib.util.spec_from_file_location("validate_steering_write", VALIDATE)
validate_steering_write = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_steering_write)


class HookEntryTest(unittest.TestCase):
    """hook の入口（stdin の payload）から deny まで通す。"""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.state = Path(self._tmp) / ".steering" / "20261002-x" / "state.md"
        self.state.parent.mkdir(parents=True)
        self.state.write_text("- Origin Session: sess-origin\nnote\n", encoding="utf-8")
        self.notes = self.state.parent / "notes.md"
        self.notes.write_text("x\n", encoding="utf-8")

    def run_patch(self, patch: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as hook_state:
            env = dict(os.environ, GDD_HOOK_STATE_DIR=hook_state)
            result = subprocess.run(
                [sys.executable, str(VALIDATE)],
                input=json.dumps({"tool_name": "ApplyPatch", "tool_input": {"patch": patch}}),
                capture_output=True,
                text=True,
                env=env,
                cwd=self._tmp,
            )
        return result.returncode, result.stderr

    def assertDeniedBy(self, result: tuple[int, str], message: str) -> None:
        code, err = result
        self.assertEqual(code, 2, err)
        self.assertIn(message, err)
        self.assertNotIn(INTERNAL_ERROR, err)

    def test_rewrite_after_end_of_file_is_denied(self) -> None:
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state}\n"
            "@@\n note\n+more\n*** End of File\n"
            "@@\n-- Origin Session: sess-origin\n+- Origin Session: sess-attacker\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "Origin Session")

    def test_delete_after_end_of_file_is_denied(self) -> None:
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state}\n"
            "@@\n note\n+more\n*** End of File\n"
            "@@\n-- Origin Session: sess-origin\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "Origin Session")

    def test_indented_header_after_begin_patch_is_a_header(self) -> None:
        patch = (
            "*** Begin Patch\n"
            f" *** Update File: {self.state}\n"
            "@@\n-- Origin Session: sess-origin\n+- Origin Session: sess-attacker\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "Origin Session")

    def test_indented_header_inside_add_file_is_a_header(self) -> None:
        patch = (
            "*** Begin Patch\n"
            f"*** Add File: {self.state.parent / 'new.md'}\n+x\n"
            f"  *** Update File: {self.state}\n"
            "@@\n-- Origin Session: sess-origin\n+- Origin Session: sess-attacker\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "Origin Session")

    def test_fence_after_end_of_file_is_scoped_to_its_file(self) -> None:
        patch = (
            "*** Begin Patch\n"
            "*** Add File: docs/a.md\n+```\n"
            f"*** Update File: {self.notes}\n"
            "@@\n x\n+y\n*** End of File\n"
            "@@\n+password: " + "Zq8v" + "Lm2pXr\n+```\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "probable sensitive value")

    def test_header_path_after_unicode_line_break_is_a_target(self) -> None:
        # Codex は行を \n だけで割り、path の前後の空白（\u2028・\x85 を含む）を落とす
        for brk in ("\u2028", "\x85", "\x0b"):
            with self.subTest(brk=repr(brk)):
                patch = (
                    "*** Begin Patch\n"
                    f"*** Update File: {brk}{self.state}\n"
                    "@@\n-- Origin Session: sess-origin\n+- Origin Session: sess-attacker\n"
                    "*** End Patch\n"
                )
                self.assertEqual(self.run_patch(patch)[0], 2)

    def test_header_after_line_break_inside_a_line_is_denied(self) -> None:
        # `\n` 以外で行を割る harness なら header になる。parser の割り方に依らず止める
        for name, patch in {
            "u2028": (
                "*** Begin Patch\n*** Add File: docs/a.md\n+x\u2028"
                f"*** Update File: {self.state}\n"
                "@@\n-- Origin Session: sess-origin\n+- Origin Session: sess-attacker\n*** End Patch\n"
            ),
            "lone_cr": (
                f"*** Begin Patch\r*** Update File: {self.state}\r"
                "@@\r-- Origin Session: sess-origin\r+- Origin Session: sess-attacker\r*** End Patch\r"
            ),
        }.items():
            with self.subTest(case=name):
                self.assertDeniedBy(self.run_patch(patch), LINE_BREAK)

    def test_line_break_outside_steering_is_allowed(self) -> None:
        patch = "*** Begin Patch\n*** Add File: docs/a.md\n+x\u2028y\n*** End Patch\n"
        self.assertEqual(self.run_patch(patch)[0], 0)

    def test_fence_pairs_within_the_same_file_across_hunks(self) -> None:
        design = self.state.parent / "design.md"
        design.write_text("existing\nexisting2\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            "*** Add File: docs/a.md\n+```\n"
            f"*** Update File: {design}\n@@\n existing\n+```\n"
            f"*** Update File: {design}\n@@\n existing2\n+```\n+password: " + "Zq8v" + "Lm2pXr\n+```\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "probable sensitive value")

    def test_fence_does_not_pair_across_hunks_carried_by_move(self) -> None:
        design = self.state.parent / "design.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.notes}\n@@\n x\n+```\n"
            f"*** Update File: {self.notes}\n*** Move to: {design}\n"
            "@@\n+password: " + "Zq8v" + "Lm2pXr\n+```\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "probable sensitive value")

    def test_same_value_rewrite_then_delete_is_denied(self) -> None:
        rewrite = "@@\n-- Origin Session: sess-origin\n+- Origin Session: sess-origin\n"
        for name, middle in {"plain": "", "after_end_of_file": "*** End of File\n"}.items():
            with self.subTest(case=name):
                patch = (
                    "*** Begin Patch\n"
                    f"*** Update File: {self.state}\n" + rewrite + middle
                    + f"*** Delete File: {self.state}\n"
                    "*** End Patch\n"
                )
                self.assertDeniedBy(self.run_patch(patch), "Origin Session")

    def test_add_file_over_existing_state_without_field_is_denied(self) -> None:
        patch = "*** Begin Patch\n" f"*** Add File: {self.state}\n+note\n" "*** End Patch\n"
        self.assertDeniedBy(self.run_patch(patch), "Origin Session")

    def test_move_to_same_path_is_denied(self) -> None:
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state}\n*** Move to: {self.state}\n"
            "@@\n note\n+more\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(self.run_patch(patch), "Origin Session")


class OriginFinalStateTest(unittest.TestCase):
    """消す・作り直す・move を重ねた patch で、Origin Session を書く・運ぶものを止める（既存値の有無を問わない）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.state = Path(self._tmp) / ".steering" / "20261002-x" / "state.md"
        self.state.parent.mkdir(parents=True)
        self.state.write_text("note\n", encoding="utf-8")
        self.notes = self.state.parent / "notes.md"
        self.notes.write_text("- Origin Session: sess-attacker\n", encoding="utf-8")

    def collect(self, patch: str, is_peer_turn: bool) -> list:
        return validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state)], [], is_peer_turn, {"patch": patch}, "ApplyPatch"
        )

    def test_peer_turn_cannot_set_value_by_delete_then_add(self) -> None:
        patch = (
            f"*** Begin Patch\n*** Delete File: {self.state}\n"
            f"*** Add File: {self.state}\n+- Origin Session: sess-attacker\n*** End Patch\n"
        )
        self.assertTrue(self.collect(patch, True))

    def test_peer_turn_cannot_set_value_by_delete_and_move(self) -> None:
        patch = (
            f"*** Begin Patch\n*** Delete File: {self.state}\n"
            f"*** Update File: {self.notes}\n*** Move to: {self.state}\n@@\n+- Origin Session: sess-attacker\n"
            "*** End Patch\n"
        )
        self.assertTrue(self.collect(patch, True))

    def test_peer_turn_cannot_carry_value_by_add_and_move(self) -> None:
        patch = (
            f"*** Begin Patch\n*** Add File: {self.state}\n+note\n"
            f"*** Update File: {self.notes}\n*** Move to: {self.state}\n@@\n+x\n*** End Patch\n"
        )
        self.assertTrue(self.collect(patch, True))

    def test_two_values_after_delete_then_add_are_denied(self) -> None:
        patch = (
            f"*** Begin Patch\n*** Delete File: {self.state}\n*** Add File: {self.state}\n"
            "+- Origin Session: a\n+- Origin Session: b\n*** End Patch\n"
        )
        self.assertTrue(self.collect(patch, False))

    def test_same_value_update_is_denied(self) -> None:
        # 既存値のある state.md への ApplyPatch は、当てた後の値を推定せずに止める
        self.state.write_text("- Origin Session: sess-origin\n", encoding="utf-8")
        patch = (
            f"*** Begin Patch\n*** Update File: {self.state}\n"
            "@@\n-- Origin Session: sess-origin\n+- Origin Session: sess-origin\n*** End Patch\n"
        )
        self.assertTrue(self.collect(patch, False))

    def test_delete_without_existing_value_is_allowed(self) -> None:
        patch = f"*** Begin Patch\n*** Delete File: {self.state}\n*** End Patch\n"
        self.assertEqual(self.collect(patch, False), [])


class ScanTest(unittest.TestCase):
    """走査の結果を関数ごとに見る（どの関数も同じ走査から作る）。"""

    def test_indented_header_inside_update_is_a_context_line(self) -> None:
        patch = (
            "*** Begin Patch\n"
            "*** Update File: notes.md\n"
            "@@\n *** Update File: .steering/x/state.md\n+- Origin Session: a\n"
            "*** End Patch\n"
        )
        self.assertEqual(patch_scoping.parse_patch_paths(patch), ["notes.md"])
        self.assertEqual(patch_scoping.patch_added_lines(patch, "notes.md"), "- Origin Session: a")
        self.assertEqual(patch_scoping.patch_added_lines(patch, ".steering/x/state.md"), "")

    def test_lines_after_end_patch_belong_to_no_section(self) -> None:
        patch = "*** Begin Patch\n*** Add File: a.md\n+```\n+x\n*** End Patch\n+```\n"
        self.assertEqual(patch_scoping.patch_added_lines_by_path(patch), ["```\nx"])

    def test_header_after_end_patch_is_still_a_target(self) -> None:
        # End Patch の後ろを読む harness がありうるので、target は広く拾う
        patch = "*** Begin Patch\n*** Add File: a.md\n+x\n*** End Patch\n*** Add File: .steering/x/b.md\n+y\n"
        self.assertEqual(patch_scoping.parse_patch_paths(patch), ["a.md", ".steering/x/b.md"])

    def test_plus_and_minus_triple_lines_are_content(self) -> None:
        patch = "*** Begin Patch\n*** Update File: a.md\n@@\n---x\n+++y\n*** End Patch\n"
        self.assertEqual(patch_scoping.patch_added_lines(patch, "a.md"), "++y")
        self.assertEqual(patch_scoping._scan(patch)[0].lines, ["@@", "---x", "+++y"])

    def test_move_carries_lines_and_by_path_agrees_with_sections(self) -> None:
        patch = (
            "*** Begin Patch\n*** Update File: old.md\n@@\n+a\n*** Move to: new.md\n@@\n+b\n*** End Patch\n"
        )
        self.assertEqual(patch_scoping.patch_added_lines(patch, "new.md"), "a\nb")
        self.assertEqual(patch_scoping.patch_added_lines(patch, "old.md"), "")
        self.assertEqual(patch_scoping.patch_added_lines_by_path(patch), ["a\nb"])
        self.assertEqual(patch_scoping.patch_inflow_sources(patch, "new.md"), ["old.md"])

    def test_by_path_keeps_hunks_apart_when_move_carries_lines(self) -> None:
        patch = (
            "*** Begin Patch\n*** Update File: old.md\n@@\n+```\n"
            "*** Update File: old.md\n*** Move to: new.md\n@@\n+b\n+```\n*** End Patch\n"
        )
        self.assertEqual(patch_scoping.patch_added_lines_by_path(patch), ["```", "b\n```"])

    def test_move_to_inside_add_file_is_not_a_move_but_still_a_target(self) -> None:
        patch = "*** Begin Patch\n*** Add File: a.md\n+x\n*** Move to: b.md\n+y\n*** End Patch\n"
        self.assertEqual([(hunk.kind, hunk.move_paths) for hunk in patch_scoping._scan(patch)], [("add", []), ("stray", [])])
        self.assertEqual(patch_scoping.patch_added_lines(patch, "a.md"), "x\ny")
        self.assertEqual(patch_scoping.parse_patch_paths(patch), ["a.md", "b.md"])

    def test_every_move_to_in_an_update_is_a_target(self) -> None:
        patch = "*** Begin Patch\n*** Update File: a.md\n*** Move to: b.md\n*** Move to: c.md\n*** End Patch\n"
        self.assertEqual(patch_scoping.parse_patch_paths(patch), ["a.md", "b.md", "c.md"])
        for dest in ("b.md", "c.md"):
            self.assertEqual(patch_scoping.patch_inflow_sources(patch, dest), ["a.md"])

    def test_lines_are_split_on_newline_only(self) -> None:
        patch = "*** Begin Patch\r\n*** Add File: a.md\r\n+x\u2028y\r\n*** End Patch\r\n"
        self.assertEqual(patch_scoping.patch_added_lines(patch, "a.md"), "x\u2028y")

    def test_delete_header_with_indent_is_detected(self) -> None:
        patch = "*** Begin Patch\n  *** Delete File: .steering/x/state.md\n*** End Patch\n"
        self.assertEqual([(hunk.kind, hunk.path) for hunk in patch_scoping._scan(patch)], [("delete", ".steering/x/state.md")])

    def test_unusual_inputs_do_not_raise(self) -> None:
        for patch in ("", "*** Begin Patch", "*** Move to: a.md\n+x", "\r\n*** Update File: a\r\n+b\r\n"):
            with self.subTest(patch=patch):
                patch_scoping.parse_patch_paths(patch)
                patch_scoping.parse_patch_sections(patch)
                patch_scoping.patch_added_lines_by_path(patch)
                patch_scoping.patch_inflow_sources(patch, "a")


if __name__ == "__main__":
    unittest.main()
