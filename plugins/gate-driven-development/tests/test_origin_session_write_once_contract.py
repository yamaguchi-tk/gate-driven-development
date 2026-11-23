"""`Origin Session` の write-once 境界（`validate-steering-write.py` の `collect_origin_session_rewrite_violations`）。

`test_peer_turn_write_boundary_contract.py` から分けた。peer turn の判定とは独立に、常時有効な検査である。
"""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
sys.path.insert(0, str(ROOT / "hooks" / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "validate_steering_write", ROOT / "hooks" / "scripts" / "validate-steering-write.py"
)
validate_steering_write = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_steering_write)


class TestOriginSessionWriteOnceBoundary(unittest.TestCase):
    """pr-review 是正: `Origin Session` の write-once を hook で機械強制する。

    design.md § Cross-Session Messaging（security M-4）と
    `references/state-field-tiers.md` Tier 3 は「書き換え禁止」を宣言していたが、
    強制していたのは文書契約だけで、write hook は本 field の変更を検査していなかった。
    既存値を別 ID へ書き換えられると、内容 allowlist（HITL 要約 + steering path）を
    通っても宛先が第三者セッションにすり替わる。

    適用条件は peer turn とは独立（常時有効）。design の禁止は「GDD 自身も受信
    メッセージも更新しない」という field 単位の規則で、peer 由来ターンに限定されない。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.state_path = Path(self._tmp) / ".steering" / "20260903-x" / "state.md"
        self.state_path.parent.mkdir(parents=True)

    def _write_existing(self, body: str) -> None:
        self.state_path.write_text(body, encoding="utf-8")

    def _collect(self, chunk: str, is_peer_turn: bool = False, tool_input=None, tool_name: str = "Edit"):
        return validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)], [chunk], is_peer_turn, tool_input, tool_name
        )

    def test_case_a2_first_write_on_peer_turn_is_denied(self) -> None:
        """pr-review 是正 (Finding D): 既存値が無い state.md に peer 由来のターンが
        最初の値を書けると、その値が write-once として固定され、以後の HITL 要約の
        送信先になる。正当な初回設定は起動元セッション（非 peer ターン）が行う。
        """
        self._write_existing("Started At: 2026-09-03T00:00:00Z\n")
        reasons = self._collect("- Origin Session: sess-attacker\n", is_peer_turn=True)
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_case_a3_same_value_rewrite_on_peer_turn_is_allowed(self) -> None:
        """全文 Write で state.md を書き直す通常運用（値は変えない）は peer turn でも通す。"""
        self._write_existing("- Origin Session: sess-origin\n")
        self.assertEqual(self._collect("- Origin Session: sess-origin\n", is_peer_turn=True), [])

    def test_case_a4_untouched_field_on_peer_turn_is_allowed(self) -> None:
        self._write_existing("- Origin Session: sess-origin\n")
        self.assertEqual(
            self._collect("- Resume From: gdd-implementation-gating\n", is_peer_turn=True), []
        )

    def test_value_only_edit_rewrite_is_denied(self) -> None:
        """Finding C と同型: 値だけを置換する Edit も書込み後テキストで判定する。"""
        self._write_existing("- Origin Session: sess-origin\n")
        reasons = self._collect(
            "sess-attacker",
            tool_input={"old_string": "sess-origin", "new_string": "sess-attacker"},
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_case_a_first_write_is_allowed(self) -> None:
        self._write_existing("Started At: 2026-09-03T00:00:00Z\n")
        self.assertEqual(
            self._collect("- Origin Session: sess-origin\n"),
            [],
            "既存値が無い初回書込み（起動元セッションの write-once そのもの）は妨げない",
        )

    def test_case_a5_new_file_creation_on_peer_turn_is_denied(self) -> None:
        """pr-review 是正 (Finding V): 新規 `state.md` の作成時は PreToolUse の段階で
        ファイルがまだ存在しない。`Path(path).read_text()` の `OSError` を `continue`
        すると検査全体を skip し、peer turn からの `Write` で `Origin Session` を
        初回設定できてしまう（Finding D の初回書込み deny が新規作成では効かない）。
        """
        new_path = Path(self._tmp) / ".steering" / "20260904-y" / "state.md"
        self.assertFalse(new_path.exists())
        content = "- Origin Session: sess-attacker\n"
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(new_path)],
            [content],
            True,
            {"file_path": str(new_path), "content": content},
            "Write",
        )
        self.assertTrue(reasons, "新規ファイル作成でも peer turn からの初回書込みは deny する")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_case_a6_new_file_creation_on_human_turn_is_allowed(self) -> None:
        """false positive ガード: 起動元セッション（非 peer ターン）による新規
        steering 作成は、初回の write-once そのものなので妨げない。
        """
        new_path = Path(self._tmp) / ".steering" / "20260904-y" / "state.md"
        content = "- Origin Session: sess-origin\n"
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(new_path)],
            [content],
            False,
            {"file_path": str(new_path), "content": content},
            "Write",
        )
        self.assertEqual(reasons, [])

    def test_case_b_rewrite_to_different_value_is_denied_without_peer_turn(self) -> None:
        self._write_existing("- Origin Session: sess-origin\n")
        reasons = self._collect("- Origin Session: sess-attacker\n")
        self.assertTrue(reasons, "既存値と異なる値への変更は deny されなければならない")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")
        self.assertIn("sess-attacker", reasons[0][1])

    def test_case_c_rewrite_to_same_value_is_allowed(self) -> None:
        self._write_existing("- Origin Session: sess-origin\n")
        self.assertEqual(
            self._collect("- Origin Session: sess-origin\n"),
            [],
            "同じ値の再書込み（全文 Write での書き直し）は通らなければならない",
        )

    def test_backtick_and_bare_forms_share_one_acceptance_rule(self) -> None:
        self._write_existing("`Origin Session`: sess-origin\n")
        self.assertTrue(
            self._collect("Origin Session = sess-attacker\n"),
            "gdd_extract_doc_field と同じ受理規則（バッククォート / `=` 区切り）で判定する",
        )

    def test_double_backtick_rewrite_is_denied(self) -> None:
        """独立レビュー是正 (Finding F-2): 旧パターンは field 名周りの単一任意
        backtick しか許容せず、二重 backtick は unmatched のまま field 行
        自体が未検出になっていた（読み取り側 `gdd_extract_doc_field()` は
        行内の backtick を全 `gsub` するため、値は書き換わってしまう）。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        reasons = self._collect("- ``Origin Session``: sess-attacker\n")
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_backtick_inside_field_name_rewrite_is_denied(self) -> None:
        """独立レビュー是正 (Finding F-2): field 名の内部に backtick を 1 個
        挟む形も旧パターンでは unmatched だった。"""
        self._write_existing("- Origin Session: sess-origin\n")
        reasons = self._collect("- Ori`gin Session: sess-attacker\n")
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_backtick_before_bullet_rewrite_is_denied(self) -> None:
        """独立レビュー是正 (Finding F-2): bullet marker の前に backtick を
        置く形も旧パターンでは unmatched だった。"""
        self._write_existing("- Origin Session: sess-origin\n")
        reasons = self._collect("`- Origin Session: sess-attacker\n")
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_clearing_the_value_is_denied(self) -> None:
        self._write_existing("- Origin Session: sess-origin\n")
        self.assertTrue(
            self._collect("- Origin Session:\n"),
            "空値化も write-once の書き換えなので fail-closed で deny する",
        )

    def test_line_deleting_edit_is_denied(self) -> None:
        """pr-review 是正 (Finding J): 行ごと消す Edit（`new_string=""`）も
        書込み後テキストで判定する。空値化と同じく write-once の破壊。
        """
        self._write_existing("- Origin Session: sess-origin\n- Resume From: x\n")
        reasons = self._collect(
            "",
            tool_input={"old_string": "- Origin Session: sess-origin\n", "new_string": ""},
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_full_write_dropping_the_line_is_denied(self) -> None:
        """pr-review 是正 (Finding K): 全文 `Write` で新本文から `Origin Session` 行を
        省く形も、既存値の削除として deny する。残すと write-once の宛先を消してから
        別 ID を「初回値」として設定できる。
        """
        self._write_existing("- Origin Session: sess-origin\n- Resume From: x\n")
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)],
            ["- Resume From: x\n"],
            False,
            {"file_path": str(self.state_path), "content": "- Resume From: x\n"},
            "Write",
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_full_write_dropping_the_line_via_path_key_is_denied(self) -> None:
        """独立レビュー是正 (Finding F-7): `project_written_text()` が `file_path`
        だけを見ていたときは、同じ `Write` 系ツールでも対象 path を `path` 等の
        別 key で示す harness（本 plugin は Cursor / Codex ともマルチ harness
        対応）で target が常に不一致になり、全文 Write が field 行を省く形
        （Finding K と同型の削除）を検出できなかった。`extract_target_paths()` と
        同じ key 集合（`file_path` / `path` / `target_file` / `target_notebook`）を
        見ることを確認する。
        """
        self._write_existing("- Origin Session: sess-origin\n- Resume From: x\n")
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)],
            ["- Resume From: x\n"],
            False,
            {"path": str(self.state_path), "content": "- Resume From: x\n"},
            "Write",
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_full_write_keeping_the_line_is_allowed(self) -> None:
        """false positive ガード: 値を保ったままの全文 Write（通常運用）は通す。"""
        self._write_existing("- Origin Session: sess-origin\n- Resume From: x\n")
        self.assertEqual(
            validate_steering_write.collect_origin_session_rewrite_violations(
                [str(self.state_path)],
                ["- Origin Session: sess-origin\n- Resume From: y\n"],
                False,
                {
                    "file_path": str(self.state_path),
                    "content": "- Origin Session: sess-origin\n- Resume From: y\n",
                },
                "Write",
            ),
            [],
        )

    def test_full_write_without_existing_value_is_allowed(self) -> None:
        """既存値が無い state.md への全文 Write（`Origin Session` を持たない本文）は
        削除ではないので通す。
        """
        self._write_existing("- Resume From: x\n")
        self.assertEqual(
            validate_steering_write.collect_origin_session_rewrite_violations(
                [str(self.state_path)],
                ["- Resume From: y\n"],
                False,
                {"file_path": str(self.state_path), "content": "- Resume From: y\n"},
                "Write",
            ),
            [],
        )

    def test_apply_patch_deleting_the_line_is_denied(self) -> None:
        """pr-review 是正 (Finding K): 削除のみの `ApplyPatch` は追加行が空なので
        chunk 判定にかからず、全文再構成もできない。削除行から検出する。
        """
        self._write_existing("- Origin Session: sess-origin\n- Resume From: x\n")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state_path}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            " - Resume From: x\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_deleting_the_line_with_inert_edit_pair_is_still_denied(self) -> None:
        """独立レビュー是正 (Finding F-3): `ApplyPatch` payload に、対象ファイルに
        存在しない文字列を対象とする無害な `old_string`/`new_string` を混ぜても、
        削除のみの patch を deny できることを確認する。`project_edited_text()` が
        tool_name を確認せず常時呼ばれていたときは、この無害な置換が生む
        「変化なし」の projected テキストが `elif projected is not None` を先に
        消費し、本物の patch 削除を見る `patch_removes_state_field()` に
        到達しなかった。
        """
        self._write_existing("- Origin Session: sess-origin\n- Resume From: x\n")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state_path}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            " - Resume From: x\n"
            "*** End Patch\n"
        )
        tool_input = {
            "patch": patch,
            "old_string": "zzz_never_matches_anything_zzz",
            "new_string": "irrelevant",
        }
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)], [], False, tool_input, "ApplyPatch"
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_keeping_the_value_on_a_state_md_with_a_value_is_denied(self) -> None:
        """既存値のある state.md を書く patch は、値の行を文脈行として残しても止める。"""
        self._write_existing("- Origin Session: sess-origin\n")
        worklog = self.state_path.parent / "worklog.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {worklog}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            f"*** Update File: {self.state_path}\n"
            "@@\n"
            " - Origin Session: sess-origin\n"
            "+- Resume From: gdd-completion-check\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)], ["- Resume From: gdd-completion-check"], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertEqual([reason[0] for reason in reasons], ["origin_session_rewrite"])

    def test_apply_patch_deleting_the_whole_file_is_denied(self) -> None:
        """pr-review 是正 (Finding P): `*** Delete File:` は追加行も削除行も持たない。
        ファイルごと消せば既存値も消えるので、削除の一形態として deny する。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        patch = f"*** Begin Patch\n*** Delete File: {self.state_path}\n*** End Patch\n"
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_delete_file_paths_are_collected_as_targets(self) -> None:
        """Finding P の入口: `*** Delete File:` を path 収集から落とすと
        `steering_targets` が空になり main() が検査前に allow する。
        """
        patch = f"*** Begin Patch\n*** Delete File: {self.state_path}\n*** End Patch\n"
        self.assertEqual(
            validate_steering_write.extract_target_paths("ApplyPatch", {"patch": patch}),
            [str(self.state_path)],
        )

    def test_apply_patch_deleting_a_state_md_without_origin_session_is_allowed(self) -> None:
        """false positive ガード: 本 category が守るのは `Origin Session` だけ。
        既存値を持たない state.md の削除まで止めない。
        """
        self._write_existing("- Resume From: x\n")
        patch = f"*** Begin Patch\n*** Delete File: {self.state_path}\n*** End Patch\n"
        self.assertEqual(
            validate_steering_write.collect_origin_session_rewrite_violations(
                [str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
            ),
            [],
        )

    def test_apply_patch_moving_state_md_away_is_denied(self) -> None:
        """pr-review 是正 (Finding Y): `*** Update File: <old>` の直後の
        `*** Move to: <new>` を認識しないと、`*** Move to:` 行が汎用の `*** `
        catch-all に落ちて section が閉じ、旧 path（`state.md`）からの削除にも
        判定が及ばない。move は既存値を消す一形態として deny する。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        moved_to = self.state_path.parent / "archived-state.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state_path}\n"
            f"*** Move to: {moved_to}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            "+- Origin Session: sess-origin\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path), str(moved_to)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons, "move による旧 path からの既存値削除は deny する")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_move_destination_path_is_collected_as_target(self) -> None:
        """Finding Y の入口: `*** Move to:` の移動先を path 収集から落とすと
        `steering_targets` に入らず、移動先が `state.md` でも検査が一切走らない。
        """
        moved_to = self.state_path.parent / "new-state.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state_path}\n"
            f"*** Move to: {moved_to}\n"
            "@@\n"
            "*** End Patch\n"
        )
        self.assertIn(
            str(moved_to),
            validate_steering_write.extract_target_paths("ApplyPatch", {"patch": patch}),
        )

    def test_apply_patch_moving_a_different_file_into_state_md_is_denied_on_peer_turn(
        self,
    ) -> None:
        """move で任意ファイルを `state.md` へ改名すると、移動先の内容として
        `Origin Session` を自由に設定できてしまう。移動先への書込みとして
        peer turn 中の初回設定も deny する。
        """
        other = self.state_path.parent / "notes.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            f"*** Move to: {self.state_path}\n"
            "@@\n"
            "-- some note\n"
            "+- Origin Session: sess-attacker\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], True, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_moving_a_different_file_into_state_md_without_origin_session_is_denied(
        self,
    ) -> None:
        """state.md を移動先にする patch は、移動元を読まずに止める（`Origin Session` が絡まなくても）。"""
        other = self.state_path.parent / "notes.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            f"*** Move to: {self.state_path}\n"
            "@@\n"
            "-old note\n"
            "+- Resume From: x\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertEqual([reason[0] for reason in reasons], ["origin_session_rewrite"])
        self.assertIn("moves a file onto a `state.md`", reasons[0][1])

    def test_apply_patch_pure_move_without_hunk_into_state_md_is_denied(self) -> None:
        """Copilot レビュー是正 (PR #31 review, commit d9a288a への指摘): `*** Update
        File: <old>` の直後に `*** Move to: <new>` だけが続き、間に diff hunk が
        無い**純粋 move**（ファイル名だけを変える move。内容は変えない）は、
        `parse_patch_sections()` が移動先の section を空リストのまま作る。空
        section は `patch_added_lines()` でも `project_written_text()`（ApplyPatch
        は常に `None`）でも「投影不能」扱いになり、削除でもファイルごとの削除でも
        ないため、移動先の書込み後内容が一切検査されずに素通りしていた。
        `.steering/` 外にあるこの hook の検査対象外ファイル（既に `Origin Session`
        を含む）を、hunk を付けずに `state.md` へ move するだけで write-once 検査を
        完全に迂回できていた。純粋 move は内容を変えないため、移動元の現在の
        ディスク内容を移動先の書込み後内容として判定することを確認する。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        other = self.state_path.parent / "notes.md"
        other.write_text("- Origin Session: sess-attacker\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            f"*** Move to: {self.state_path}\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons, "hunk 無し純粋 move による Origin Session 迂回は deny する")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_pure_move_without_hunk_and_without_origin_session_is_denied(self) -> None:
        """state.md を移動先にする純粋 move も、移動元を読まずに止める。"""
        other = self.state_path.parent / "notes.md"
        other.write_text("- Resume From: x\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            f"*** Move to: {self.state_path}\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertEqual([reason[0] for reason in reasons], ["origin_session_rewrite"])
        self.assertIn("moves a file onto a `state.md`", reasons[0][1])

    def test_apply_patch_move_with_unrelated_hunk_still_denies_origin_session_in_source(
        self,
    ) -> None:
        """独立レビュー再検証是正 (Copilot 是正 commit d9a288a への指摘の再検証):
        「診断行（diff hunk）が無い move だけ」を対象にした初版修正は、hunk が
        対象 field と無関係な行だけを変える、ごく通常の move+hunk には及ばな
        かった。`Origin Session` は hunk の追加行に一切現れない（移動元に元から
        あるだけ）ため `has_state_field_line` は False、section は非空（無関係な
        hunk がある）ため純粋 move 判定にも該当せず、`else: continue` で素通り
        していた。move である限り診断行の有無を問わず移動元の現在の内容を
        判定対象にすることを確認する。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        other = self.state_path.parent / "notes.md"
        other.write_text("# notes\n- Origin Session: sess-attacker\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            f"*** Move to: {self.state_path}\n"
            "@@\n"
            "-# notes\n"
            "+# notes v2\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons, "hunk が無関係な行だけを変える move でも移動元の Origin Session は検査する")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_two_pure_moves_to_same_destination_both_checked(self) -> None:
        """独立レビュー再検証是正: 初版の移動元収集は最初の 1 件で `return` していた
        ため、同一移動先へ複数の move がある patch では 2 件目以降の移動元が
        無検査だった（無害な移動元を先に置き、攻撃者の移動元を 2 件目にするだけで
        迂回できた）。全ての移動元を収集して判定することを確認する。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        benign = self.state_path.parent / "benign.md"
        benign.write_text("- Resume From: x\n", encoding="utf-8")
        attacker = self.state_path.parent / "notes.md"
        attacker.write_text("- Origin Session: sess-attacker\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {benign}\n"
            f"*** Move to: {self.state_path}\n"
            f"*** Update File: {attacker}\n"
            f"*** Move to: {self.state_path}\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(benign), str(attacker), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons, "2 件目以降の移動元も検査しなければならない")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_hunk_before_move_to_header_is_not_discarded(self) -> None:
        """独立レビュー再検証是正: `parse_patch_sections()` は `*** Move to:` 検出時に
        旧 key の section を `del` していたため、非正規な順序（`Update File:` の
        直後、`Move to:` より**前**に hunk が置かれる patch）では、hunk の内容が
        旧 key・新 key のどちらにも属さず完全に消えていた。hunk 自体が
        `Origin Session` を書き換えていても、この消失により無検査で通過していた。
        `Move to:` 検出時に旧 key の内容を新 key へ引き継ぐことを確認する。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        other = self.state_path.parent / "notes.md"
        other.write_text("- Origin Session: sess-origin\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            "+- Origin Session: sess-attacker\n"
            f"*** Move to: {self.state_path}\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons, "Move to: より前に置かれた hunk の内容を消失させてはいけない")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_move_source_with_malformed_byte_is_denied_not_crashed(self) -> None:
        """独立レビュー再検証是正 (Finding F-2): 移動元ファイルの読み取りが
        `except OSError` だけで保護されていたため、`UnicodeDecodeError`
        （`OSError` のサブクラスではない）が送出されると hook プロセスごと
        クラッシュし、この書込みに対する全検査（secrets / ellipsis 等含む）が
        無効化される（fail-open）問題があった。`errors="replace"` で読み、
        クラッシュせず fail-closed（deny）に倒れることを確認する。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        other = self.state_path.parent / "notes.md"
        other.write_bytes(b"- Origin Session: sess-attacker\n\xff\n")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            f"*** Move to: {self.state_path}\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons, "不正バイトを含む移動元の読み取りはクラッシュせず deny に倒す")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_apply_patch_move_onto_a_state_md_with_a_value_is_denied(self) -> None:
        """既存値のある state.md へ流れ込む move は、移動元の値が同じでも止める。ApplyPatch では
        当てた後の値を推定しない（`_origin_session_patch_reason()`）。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        other = self.state_path.parent / "notes.md"
        other.write_text("# notes\n- Origin Session: sess-origin\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            f"*** Move to: {self.state_path}\n"
            "@@\n"
            "-# notes\n"
            "+# notes v2\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertEqual([reason[0] for reason in reasons], ["origin_session_rewrite"])
        self.assertIn("moves a file onto a `state.md`", reasons[0][1])

    def test_apply_patch_move_removing_origin_session_field_is_denied_not_masked_by_source(
        self,
    ) -> None:
        """false positive ガードの反対側: hunk が移動元の `Origin Session` 行を
        明示的に削除している場合、移動元の**現在の**ディスク内容（削除前の値）を
        そのまま「維持され得る値」として使ってはいけない。削除は既存値を消して
        復元不能にする操作として扱い、移動元の現在値で上書きしない。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        other = self.state_path.parent / "notes.md"
        other.write_text("- Origin Session: sess-origin\n- Resume From: x\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {other}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            " - Resume From: x\n"
            f"*** Move to: {self.state_path}\n"
            "*** End Patch\n"
        )
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(other), str(self.state_path)], [], False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons, "hunk が明示的に削除した field を移動元の現在値で復元してはいけない")
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_duplicate_origin_session_lines_are_denied(self) -> None:
        """pr-review 是正 (Finding Q): 既存値を先頭に残したまま別の値の行を後ろへ
        足す形。下流パーサは最初の 1 行しか読まないため「値は変わっていない」と
        判定され、宛先 field だけが二重化する。全出現を見て deny する。
        """
        existing = "- Origin Session: sess-origin\n"
        self._write_existing(existing)
        content = existing + "- Origin Session: sess-attacker\n"
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)],
            [content],
            False,
            {"file_path": str(self.state_path), "content": content},
            "Write",
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")
        self.assertIn("sess-attacker", reasons[0][1])

    def test_duplicate_origin_session_lines_on_first_write_are_denied(self) -> None:
        """既存値が無くても、1 回の書込みで別々の値を 2 行書けば宛先は曖昧になる。"""
        self._write_existing("- Resume From: x\n")
        content = "- Origin Session: sess-a\n- Origin Session: sess-b\n"
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)],
            [content],
            False,
            {"file_path": str(self.state_path), "content": content},
            "Write",
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")

    def test_repeated_identical_lines_are_allowed(self) -> None:
        """false positive ガード: 同じ値が 2 行あっても宛先は 1 つに定まる。"""
        self._write_existing("- Origin Session: sess-origin\n")
        content = "- Origin Session: sess-origin\n- Origin Session: sess-origin\n"
        self.assertEqual(
            validate_steering_write.collect_origin_session_rewrite_violations(
                [str(self.state_path)],
                [content],
                False,
                {"file_path": str(self.state_path), "content": content},
                "Write",
            ),
            [],
        )

    def test_apply_patch_rewrite_beside_the_same_value_in_another_file_is_denied(self) -> None:
        """Finding T の形: 別ファイル（worklog.md）へ既存値と同じ行を足しても、state.md 側の宛先変更は止まる。
        ApplyPatch は値を推定せず、語のある patch を止める（`_origin_session_patch_reason()`）。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        worklog = self.state_path.parent / "worklog.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {worklog}\n"
            "@@\n"
            "+- Origin Session: sess-origin\n"
            f"*** Update File: {self.state_path}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            "+- Origin Session: sess-attacker\n"
            "*** End Patch\n"
        )
        chunks = validate_steering_write.extract_content_chunks("ApplyPatch", {"patch": patch})
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)], chunks, False, {"patch": patch}, "ApplyPatch"
        )
        self.assertTrue(reasons)
        self.assertEqual(reasons[0][0], "origin_session_rewrite")
        self.assertIn("sess-origin", reasons[0][1])

    def test_apply_patch_on_a_state_md_with_a_value_is_denied_even_if_the_field_is_in_another_file(self) -> None:
        """既存値のある state.md を書く patch は、値の行が別のファイルにしか無くても止める。"""
        self._write_existing("- Origin Session: sess-origin\n")
        worklog = self.state_path.parent / "worklog.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {worklog}\n"
            "@@\n"
            "+- Origin Session: sess-other\n"
            f"*** Update File: {self.state_path}\n"
            "@@\n"
            "+- Resume From: gdd-completion-check\n"
            "*** End Patch\n"
        )
        chunks = validate_steering_write.extract_content_chunks("ApplyPatch", {"patch": patch})
        reasons = validate_steering_write.collect_origin_session_rewrite_violations(
            [str(self.state_path)], chunks, False, {"patch": patch}, "ApplyPatch"
        )
        self.assertEqual([reason[0] for reason in reasons], ["origin_session_rewrite"])

    def test_write_content_for_another_path_is_not_applied_to_state_md(self) -> None:
        """false positive ガード: `Write` の `content` は `file_path` 宛の全文。
        別 key で列挙された無関係なパスの判定材料に使わない。
        """
        self._write_existing("- Origin Session: sess-origin\n")
        other = self.state_path.parent / "worklog.md"
        self.assertEqual(
            validate_steering_write.collect_origin_session_rewrite_violations(
                [str(self.state_path)],
                ["memo\n"],
                False,
                {"file_path": str(other), "content": "memo\n"},
                "Write",
            ),
            [],
        )

    def test_untouched_field_is_not_triggered(self) -> None:
        self._write_existing("- Origin Session: sess-origin\n")
        self.assertEqual(
            self._collect("- Resume From: gdd-implementation-gating\n"),
            [],
            "`Origin Session` 行に触れない書込みは trigger にかからない",
        )

    def test_non_state_md_path_is_out_of_scope(self) -> None:
        worklog = self.state_path.parent / "worklog.md"
        worklog.write_text("- Origin Session: sess-origin\n", encoding="utf-8")
        self.assertEqual(
            validate_steering_write.collect_origin_session_rewrite_violations(
                [str(worklog)], ["- Origin Session: sess-attacker\n"]
            ),
            [],
            "正本置き場は state.md。他 artifact の同名散文を deny 対象にしない",
        )

    def test_case_variant_state_md_path_is_recognized_as_in_scope(self) -> None:
        """独立レビュー是正 (Finding F-4): macOS(既定 APFS) / Windows は大文字小文字を
        区別しないファイルシステムで、`.STEERING/x/State.MD` は実ファイルとして
        `.steering/x/state.md` と同一を指す（実測）。casing を変えただけの path が
        `is_steering_path()` / `is_state_md_path()` をすり抜けると、`steering_targets`
        への採用自体が漏れ、この hook の全検査（peer-turn / write-once / secrets /
        ellipsis）を素通りしたまま実 file を書き換えられる。判定は純粋な文字列
        比較（大文字小文字を無視）であり、実行環境の FS 大文字小文字区別の有無には
        依存しないことを確認する。
        """
        case_variant_path = str(self.state_path).replace(".steering", ".STEERING").replace(
            "state.md", "State.MD"
        )
        self.assertTrue(validate_steering_write.is_steering_path(case_variant_path))
        self.assertTrue(validate_steering_write.is_state_md_path(case_variant_path))
        self.assertTrue(
            validate_steering_write.is_tasklist_md_path(
                case_variant_path.replace("State.MD", "TaskList.MD")
            )
        )

    def test_category_is_non_demotable(self) -> None:
        self.assertIn(
            "origin_session_rewrite", validate_steering_write.NON_DEMOTABLE_CATEGORIES
        )

    def test_why_explanation_registered(self) -> None:
        self.assertIn("origin_session_rewrite", validate_steering_write.WHY_EXPLANATIONS)


if __name__ == "__main__":
    unittest.main()
