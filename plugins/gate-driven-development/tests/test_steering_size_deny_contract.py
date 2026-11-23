"""steering artifact の size 通知の契約テスト（以前の size deny を、止めずに通知する形に変えたもの）。

固定する契約:
1. 「超過」= post-write サイズ > 上限 かつ post-write サイズ > 既存サイズ（算出は上界推定のまま）
2. 超過で、ほかの category の違反が無い書き込みは exit 0。deny は出さず、
   `hookSpecificOutput.additionalContext` と `systemMessage` の両方に通知の文を載せる
3. 通知の文は `[steering size] <name> is <post> bytes after this write, over the <limit> byte limit. `
   + `SIZE_DENY_SUFFIX`。<name> はファイル名だけ（S-5。生パス・ディレクトリ部を含まない）
4. ほかの category の違反と同時の超過は、ほかの category の理由で deny。deny 本文に通知の文が付き、
   size は deny の理由にならない
5. ほかの category が 3 回続いて降格する回の警告にも通知の文が付く。size のための deny counter は無い
6. 超過でない書き込み（上限以下・ちょうど上限・サイズ不変・減る・算出不能）では通知を出さない
7. kill switch `GDD_STEERING_SIZE_DENY` は無い。"0" でも通知は出て、無効化告知は出ない
8. 旧 advisory の "[artifact size]" は出ない
9. 例外は top-level guard で fail-closed（変えない）

ケース番号は旧 `design.md` § テスト方針の番号を引き継ぐ。hook は subprocess で起動し、
stdin に PreToolUse payload を渡して stdout / stderr の JSON を assert する。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
STATE_LIMIT = 20_000
TASKLIST_LIMIT = 80_000
DESIGN_LIMIT = 60_000
NON_EXAMPLE_EMAIL = "real.person" + "@" + "gmail.com"


class SteeringSizeNoticeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        # macOS の /var -> /private/var symlink 下でも target の resolve 結果が揃うよう resolve する。
        self._tmp = str(Path(tempfile.mkdtemp()).resolve())
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def _steering_file(self, name: str) -> Path:
        p = Path(self._tmp) / ".steering" / "20260904-w36-test" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _run(self, payload: object, *, extra_env: dict | None = None) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )

    def _deny_json(self, result: subprocess.CompletedProcess[str]) -> dict:
        return json.loads(result.stdout or result.stderr)

    def _counter_files(self) -> list[Path]:
        return sorted(Path(self._state_dir).glob("*.json"))

    # --- 通知の確かめ用の helper ---
    def _assert_notice_text(self, text: str, name: str | None, post: int, limit: int) -> None:
        """通知の文（契約 3）が `text` にある。`name` が None ならファイル名は固定しない。"""
        self.assertIn("[steering size]", text)
        if name is None:
            self.assertRegex(text, rf"\S+ is {post} bytes after this write")
        else:
            self.assertIn(f"{name} is {post} bytes after this write", text)
        self.assertIn(f"over the {limit} byte limit", text)
        self.assertIn("worklog.md", text)

    def _assert_common_absent(self, result: subprocess.CompletedProcess[str]) -> None:
        """契約 7・8: kill switch の告知と旧 advisory はどの書き込みでも出ない。"""
        out = result.stdout + result.stderr
        self.assertNotIn("[artifact size]", out)
        self.assertNotIn("GDD_STEERING_SIZE_DENY", out)

    def _assert_size_notice(
        self, result: subprocess.CompletedProcess[str], name: str | None, post: int, limit: int
    ) -> dict:
        """契約 2: exit 0、deny 無し、additionalContext と systemMessage の両方に通知。"""
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        hso = data.get("hookSpecificOutput", {})
        self.assertNotEqual(hso.get("permissionDecision"), "deny", data)
        self._assert_notice_text(hso.get("additionalContext", ""), name, post, limit)
        self._assert_notice_text(data.get("systemMessage", ""), name, post, limit)
        self._assert_common_absent(result)
        return data

    def _assert_no_size_notice(self, result: subprocess.CompletedProcess[str]) -> None:
        """契約 6: 出力のどこにも通知が無い。"""
        self.assertNotIn("[steering size]", result.stdout + result.stderr)
        self._assert_common_absent(result)

    def _assert_deny_with_notice(
        self, result: subprocess.CompletedProcess[str], name: str, post: int, limit: int
    ) -> str:
        """契約 4: ほかの category の理由で deny し、本文に通知が付く。size は理由にならない。"""
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        data = self._deny_json(result)
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")
        body = data["systemMessage"]
        self._assert_notice_text(body, name, post, limit)
        self.assertNotIn("would become", body)
        self.assertNotIn("exceeding the", body)
        self._assert_common_absent(result)
        return body

    # --- Case 1: Write で上限超過 → exit 0 + 通知 ---
    def test_case1_write_over_limit_notifies(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * (STATE_LIMIT + 1)},
        }
        self._assert_size_notice(self._run(payload), "state.md", STATE_LIMIT + 1, STATE_LIMIT)

    # --- Case 2: Edit で増加して上限超過 → 通知（本番経路） ---
    def test_case2_edit_increase_over_limit_notifies(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT - 10), encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(state_path),
                "old_string": "x" * 5,
                "new_string": "y" * 1000,
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 20_985, STATE_LIMIT)

    # --- Case 3: 上限超過ファイルへの縮小 Edit → 通知なし ---
    def test_case3_shrinking_edit_on_oversized_file_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT + 500), encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(state_path),
                "old_string": "x" * 1000,
                "new_string": "y" * 10,
            },
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 4: post-write が上限以下 → 通知なし ---
    def test_case4_under_limit_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "ok"},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 5: 超過の書き込みを 3 回続けても毎回通知、size の counter は作られない ---
    def test_case5_repeated_oversize_writes_notify_each_time_without_counter(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT - 10), encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(state_path),
                "old_string": "x" * 5,
                "new_string": "y" * 1000,
            },
        }
        for attempt in range(3):
            with self.subTest(attempt=attempt):
                self._assert_size_notice(self._run(payload), "state.md", 20_985, STATE_LIMIT)
        # ほかの category の違反が無いので、counter ファイルは 1 件も無い（size の counter は無い）
        self.assertEqual(self._counter_files(), [])

    # --- Case 6: ApplyPatch → 算出不能なので通知なし ---
    def test_case6_apply_patch_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        patch = (
            f"*** Begin Patch\n*** Update File: {state_path}\n"
            + "+" + ("z" * (STATE_LIMIT + 1000)) + "\n*** End Patch\n"
        )
        payload = {"tool_name": "ApplyPatch", "tool_input": {"patch": patch}}
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 7: Edit + replace_all=true → 既存内容の出現回数で算出し、超過なら通知 ---
    def test_case7_replace_all_edit_over_limit_notifies(self) -> None:
        """`a` × 19,990 に `a` → `b`×1000 を replace_all すると post size は 19,990,000B。

        出現回数で算出する（1 回分に丸めると 20,989B と表示される）。
        """
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * (STATE_LIMIT - 10), encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(state_path),
                "old_string": "a",
                "new_string": "b" * 1000,
                "replace_all": True,
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 19_990_000, STATE_LIMIT)

    def test_case7b_replace_all_edit_within_limit_has_no_notice(self) -> None:
        """replace_all でも出現回数分を足して上限内なら通知しない。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 100 + "x" * 1_000, encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "a", "new_string": "bb", "replace_all": True},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 8: MultiEdit で Σ が上限超過 → 通知 ---
    def test_case8_multi_edit_sum_over_limit_notifies(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 10 + "b" * 10 + ("x" * (STATE_LIMIT - 30)), encoding="utf-8")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(state_path),
                "edits": [
                    {"old_string": "a" * 10, "new_string": "A" * 3000},
                    {"old_string": "b" * 10, "new_string": "B" * 3000},
                ],
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 25_970, STATE_LIMIT)

    # --- Case 9: 通知の文に size 専用の退避手順が付き、email / path 向けの DENY_SUFFIX は混ざらない ---
    def test_case9_notice_has_size_suffix_only(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * (STATE_LIMIT + 1)},
        }
        data = self._assert_size_notice(self._run(payload), "state.md", STATE_LIMIT + 1, STATE_LIMIT)
        for text in (data["systemMessage"], data["hookSpecificOutput"]["additionalContext"]):
            # size 専用 suffix（SIZE_DENY_SUFFIX）が渡っていること
            self.assertIn("check-gate-ledger.sh", text)
            self.assertIn("does not repeat this notice", text)
            # 既定 DENY_SUFFIX（email / path 向け）は混ざらない
            self.assertNotIn("example@example.com", text)

    # --- Case 10: kill switch は無い。GDD_STEERING_SIZE_DENY=0 でも通知が出て、無効化告知は出ない ---
    def test_case10_removed_kill_switch_has_no_effect(self) -> None:
        state_path = self._steering_file("state.md")
        off = {"GDD_STEERING_SIZE_DENY": "0"}
        oversize = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * (STATE_LIMIT + 1)},
        }
        self._assert_size_notice(self._run(oversize, extra_env=off), "state.md", STATE_LIMIT + 1, STATE_LIMIT)

        # ほかの category と同時の超過も、env によらず email の理由で deny + 通知
        content = "x" * (STATE_LIMIT + 1) + f"\ncontact: {NON_EXAMPLE_EMAIL}\n"
        both = {"tool_name": "Write", "tool_input": {"file_path": str(state_path), "content": content}}
        body = self._assert_deny_with_notice(
            self._run(both, extra_env=off), "state.md", len(content.encode()), STATE_LIMIT
        )
        self.assertIn("example.com", body)

        # 上限内の書き込みでは、無効化告知も通知も出ない
        small = {"tool_name": "Write", "tool_input": {"file_path": str(state_path), "content": "ok"}}
        result = self._run(small, extra_env=off)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 12: 超過の通知が続いた後でも、初出 email は email として deny（通知付き） ---
    def test_case12_prior_notices_do_not_affect_other_category_deny(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT - 10), encoding="utf-8")
        grow_payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "x" * 5, "new_string": "y" * 1000},
        }
        for _ in range(2):
            self._assert_size_notice(self._run(grow_payload), "state.md", 20_985, STATE_LIMIT)
        new_string = f"contact: {NON_EXAMPLE_EMAIL}"
        email_payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "x" * 5, "new_string": new_string},
        }
        post = STATE_LIMIT - 10 - 5 + len(new_string.encode())
        body = self._assert_deny_with_notice(self._run(email_payload), "state.md", post, STATE_LIMIT)
        self.assertIn("example.com", body)

    # --- Case 13: 上限超過ファイルへの縮小 Edit に初出 secret_marker を混ぜる → deny（通知なし） ---
    def test_case13_shrinking_edit_with_secret_marker_still_denies(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT + 500), encoding="utf-8")
        # 実 key と同じ形（scanner 誤検知回避のため連結で組み立てる。
        # 既存 test_distribution_readiness_contract.py の token fixture と同じ作法）
        secret_value = "AKIA" + "IOSFODNN7EXAMPLE"
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(state_path),
                "old_string": "x" * 1000,
                "new_string": secret_value,
            },
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 2, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 14: UTF-8 バイト境界。日本語のみで文字数判定なら通知が出ない ---
    def test_case14_utf8_byte_boundary_not_char_count(self) -> None:
        state_path = self._steering_file("state.md")
        # 日本語 1 文字は UTF-8 で 3 バイト。文字数なら上限未満だがバイト数なら超過する数を作る。
        char_count = (STATE_LIMIT // 3) + 10
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "あ" * char_count},
        }
        self._assert_size_notice(self._run(payload), "state.md", char_count * 3, STATE_LIMIT)

    # --- Case 16: 存在しないファイルへの Edit → 算出不能なので通知なし、落ちない（S-4） ---
    def test_case16_nonexistent_file_edit_does_not_crash(self) -> None:
        missing = self._steering_file("state.md")  # write しない
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(missing), "old_string": "a", "new_string": "b" * (STATE_LIMIT + 1)},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 17: 通知に payload の path 文字列が含まれない（S-5） ---
    def test_case17_notice_excludes_raw_path(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * (STATE_LIMIT + 1)},
        }
        data = self._assert_size_notice(self._run(payload), "state.md", STATE_LIMIT + 1, STATE_LIMIT)
        for text in (data["systemMessage"], data["hookSpecificOutput"]["additionalContext"]):
            self.assertNotIn(str(state_path), text)
            self.assertNotIn("20260904-w36-test", text)

    # --- Case 19: 内容の無い縮小 Edit（new_string=""）は通知なし、その後の増加 write は通知 ---
    def test_case19_empty_new_string_shrink_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT - 10) + "TAIL_BLOCK", encoding="utf-8")
        # 縮小 Edit: new_string を空にして退避する（content_chunks が空になる経路）
        shrink_payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "TAIL_BLOCK", "new_string": ""},
        }
        shrink_result = self._run(shrink_payload)
        self.assertEqual(shrink_result.returncode, 0, shrink_result.stderr)
        self._assert_no_size_notice(shrink_result)
        grow_payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "x" * 5, "new_string": "y" * 1000},
        }
        self._assert_size_notice(self._run(grow_payload), "state.md", STATE_LIMIT + 995, STATE_LIMIT)

    # --- Case 21: post-write == 上限（ちょうど）→ 通知なし（境界値） ---
    def test_case21_exact_limit_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * STATE_LIMIT},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 22: post-write == existing（据え置き）→ 通知なし ---
    def test_case22_unchanged_size_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT + 100), encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "x", "new_string": "y"},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 23: worklog.md への上限超過 write → 通知なし（size 対象外。退避先） ---
    def test_case23_worklog_write_has_no_notice(self) -> None:
        worklog_path = self._steering_file("worklog.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(worklog_path), "content": "x" * (STATE_LIMIT * 10)},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 24: steering target 複数 → 全 target を判定し、超過した target を通知する ---
    def test_case24_multiple_targets_notify_when_any_exceeds(self) -> None:
        # 件数を増やすだけで size 判定を迂回できないよう、target ごとに判定する。
        # size が算出可能な Write payload に steering target を 2 件持たせる。
        state_path = self._steering_file("state.md")
        design_path = self._steering_file("design.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(state_path),
                "path": str(design_path),
                "content": "x" * (STATE_LIMIT + 1),  # state.md のみ超過（design.md は上限内）
            },
        }
        data = self._assert_size_notice(self._run(payload), "state.md", STATE_LIMIT + 1, STATE_LIMIT)
        self.assertNotIn("design.md is", data["systemMessage"])

    # --- Case 24c: 複数 target のいずれも上限内 → 通知なし（Case 24 の対照） ---
    def test_case24c_multiple_targets_all_within_limit_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        design_path = self._steering_file("design.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "path": str(design_path), "content": "ok"},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 24d: 複数 target の両方が超過 → 通知（どの名前を載せるかは固定しない） ---
    def test_case24d_multiple_targets_all_exceeding_notifies(self) -> None:
        state_path = self._steering_file("state.md")
        tasklist_path = self._steering_file("tasklist.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(state_path),
                "path": str(tasklist_path),
                "content": "x" * (TASKLIST_LIMIT + 1),  # state.md / tasklist.md とも超過
            },
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertNotEqual(data.get("hookSpecificOutput", {}).get("permissionDecision"), "deny")
        self.assertIn("[steering size]", data.get("systemMessage", ""))
        self.assertIn("[steering size]", data.get("hookSpecificOutput", {}).get("additionalContext", ""))
        self._assert_common_absent(result)

    # --- Case 24e: 後段 target だけが超過 → 通知（先頭 target で打ち切らない） ---
    def test_case24e_only_later_target_exceeding_notifies(self) -> None:
        design_path = self._steering_file("design.md")
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(design_path),  # 上限 60,000 なので非超過
                "path": str(state_path),  # 上限 20,000 を超過
                "content": "x" * (STATE_LIMIT + 1),
            },
        }
        data = self._assert_size_notice(self._run(payload), "state.md", STATE_LIMIT + 1, STATE_LIMIT)
        self.assertNotIn("design.md is", data["systemMessage"])

    # --- Case 24b: ApplyPatch の複数 target → 算出不能なので通知なし ---
    def test_case24b_apply_patch_multiple_targets_has_no_notice(self) -> None:
        state_path = self._steering_file("state.md")
        design_path = self._steering_file("design.md")
        patch = (
            f"*** Begin Patch\n*** Update File: {state_path}\n+" + ("a" * (STATE_LIMIT + 1)) + "\n"
            f"*** Update File: {design_path}\n+ok\n*** End Patch\n"
        )
        payload = {"tool_name": "ApplyPatch", "tool_input": {"patch": patch}}
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 39: email と超過が同時 → email の理由で deny + 通知、3 回目は email が降格して警告 + 通知 ---
    def test_case39_other_category_deny_and_hatch_carry_notice(self) -> None:
        state_path = self._steering_file("state.md")
        content = "x" * (STATE_LIMIT + 1) + f"\ncontact: {NON_EXAMPLE_EMAIL}\n"
        post = len(content.encode())
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(state_path), "content": content}}
        for attempt in range(2):
            with self.subTest(attempt=attempt):
                body = self._assert_deny_with_notice(self._run(payload), "state.md", post, STATE_LIMIT)
                self.assertIn("example.com", body)  # email の DENY_SUFFIX
        third = self._run(payload)
        # size は降格の判定に関わらないので、email の 3 回目で allow に降格する（契約 5）
        self.assertEqual(third.returncode, 0, third.stdout + third.stderr)
        message = json.loads(third.stdout).get("systemMessage", "")
        self.assertIn("HUMAN REVIEW REQUIRED", message)
        self.assertIn("email address", message)
        self._assert_notice_text(message, "state.md", post, STATE_LIMIT)
        self.assertNotIn("would become", message)
        self._assert_common_absent(third)

    # --- Case 40: size は降格の周期に乗らない。email の 3 回周期だけで降格し、size の counter は無い ---
    def test_case40_size_does_not_change_the_demotion_cycle(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(state_path),
                "content": "x" * (STATE_LIMIT + 1) + f"\ncontact: {NON_EXAMPLE_EMAIL}\n",
            },
        }
        codes = [self._run(payload).returncode for _ in range(6)]
        self.assertEqual(codes, [2, 2, 0, 2, 2, 0], codes)
        # 2 回 deny した直後なので、残る counter は email の 1 件だけ（steering_size の counter は無い）
        self._run(payload)
        self._run(payload)
        self.assertEqual(len(self._counter_files()), 1, [f.name for f in self._counter_files()])

    # --- Case 41: 既存違反のみ（サイズ内）は従来どおり 3 回目で降格、通知なし ---
    def test_case41_existing_violation_within_size_limit_still_demotes(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": f"contact: {NON_EXAMPLE_EMAIL}"},
        }
        results = [self._run(payload) for _ in range(3)]
        self.assertEqual([r.returncode for r in results], [2, 2, 0])
        for r in results:
            self._assert_no_size_notice(r)

    # --- Case 42: `..` 正規化後に .steering 配下でなければ size 非対象 ---
    def test_case42_dotdot_escape_is_not_a_size_target(self) -> None:
        steering_dir = Path(self._tmp) / ".steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        escaped = steering_dir / ".." / "state.md"
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(escaped), "content": "x" * 30_000},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)
        # 既存 deny 判定（is_steering_path ベース）は変えない
        with_email = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(escaped), "content": f"contact: {NON_EXAMPLE_EMAIL}"},
        }
        self.assertEqual(self._run(with_email).returncode, 2)

    # --- Case 42b: 相対パスは size 非対象（cwd 依存の誤判定を防ぐ） ---
    def test_case42b_relative_path_is_not_a_size_target(self) -> None:
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * 30_000, encoding="utf-8")
        rel = os.path.relpath(str(state_path), self._tmp)
        payload = {"tool_name": "Write", "tool_input": {"file_path": rel, "content": "x" * 25_000}}
        result = self._run(payload)  # hook の cwd は repo 側。相対パスは resolve 先がずれる
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 47: 同一ファイルの二重指定でも size 判定を迂回できない ---
    def test_case47_duplicate_target_keys_still_notify(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "path": str(state_path), "content": "x" * 30_000},
        }
        self._assert_size_notice(self._run(payload), "state.md", 30_000, STATE_LIMIT)

    def test_case47_spelling_variant_duplicate_targets_still_notify(self) -> None:
        """綴り違いの二重指定（`t/state.md` と `t/./state.md`）でも size 判定が外れない。"""
        state_path = self._steering_file("state.md")
        variant = f"{state_path.parent}/./{state_path.name}"
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "path": variant, "content": "x" * 30_000},
        }
        self._assert_size_notice(self._run(payload), "state.md", 30_000, STATE_LIMIT)

    def test_case47_case_variant_duplicate_targets_still_notify(self) -> None:
        """大小文字違いの二重指定（`state.md` と `State.MD`）でも通知が出る（どちらの名前かは固定しない）。"""
        state_path = self._steering_file("state.md")
        variant = state_path.parent / "State.MD"
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "path": str(variant), "content": "x" * 30_000},
        }
        self._assert_size_notice(self._run(payload), None, 30_000, STATE_LIMIT)

    # --- Case 51: 単独 target の casing 違いでも size 判定が外れない ---
    def test_case51_single_case_variant_target_notifies_state(self) -> None:
        """`State.MD` を単独 target で渡しても上限が引ける（case-insensitive FS で同一 inode）。"""
        variant = self._steering_file("State.MD")
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(variant), "content": "x" * 30_000}}
        self._assert_size_notice(self._run(payload), "State.MD", 30_000, STATE_LIMIT)

    def test_case51_single_case_variant_target_notifies_tasklist(self) -> None:
        variant = self._steering_file("Tasklist.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(variant), "content": "x" * (TASKLIST_LIMIT + 1_000)},
        }
        self._assert_size_notice(self._run(payload), "Tasklist.md", TASKLIST_LIMIT + 1_000, TASKLIST_LIMIT)

    def test_case51_uppercase_steering_dir_notifies(self) -> None:
        """`.STEERING/` 配下でも size 判定の対象になる（`is_steering_path` と同じ大小無視）。"""
        p = Path(self._tmp) / ".STEERING" / "20260904-w36-test" / "state.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(p), "content": "x" * 30_000}}
        self._assert_size_notice(self._run(payload), "state.md", 30_000, STATE_LIMIT)

    # --- Case 52: MultiEdit の要素 decoy で size 判定を諦めない ---
    def test_case52_multiedit_non_dict_element_does_not_hide_growth(self) -> None:
        """`edits` に非 dict 要素を 1 つ混ぜても、残りの edit の増分で算出する。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * 19_000, encoding="utf-8")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(state_path),
                "edits": [{"old_string": "x", "new_string": "y" * 30_000}, "junk"],
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 48_999, STATE_LIMIT)

    def test_case52_multiedit_replace_all_decoy_does_not_hide_growth(self) -> None:
        """`replace_all: true` の edit を 1 つ混ぜても、他の edit の増分で算出する。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * 19_000, encoding="utf-8")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(state_path),
                "edits": [
                    {"old_string": "x", "new_string": "y" * 30_000},
                    {"old_string": "x", "new_string": "x", "replace_all": True},
                ],
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 48_999, STATE_LIMIT)

    def test_case52_replace_all_counts_occurrences_in_existing_content(self) -> None:
        """`replace_all` は既存内容の出現回数で増分を計上する（1 回分に過小評価しない）。

        existing 19,000B で `a`（1,000 回出現）→ `aaaaa`（+4B × 1,000 = +4,000B）で 23,000B。
        1 回分（+4B）しか数えないと上限内に倒れて通知が出ない。
        """
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 1_000 + "x" * 18_000, encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "a", "new_string": "aaaaa", "replace_all": True},
        }
        self._assert_size_notice(self._run(payload), "state.md", 23_000, STATE_LIMIT)

    # --- Case 53: size 判定は上界推定 ---
    def test_case53_multiedit_shrink_cannot_offset_growth(self) -> None:
        """縮小 edit（負の delta）は計上しない。増分 edit の上限超過を縮小で相殺できない。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 19_000, encoding="utf-8")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(state_path),
                "edits": [
                    {"old_string": "a" * 18_000, "new_string": "y" * 30_000},
                    {"old_string": "a", "new_string": "", "replace_all": True},
                ],
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 31_000, STATE_LIMIT)

    def test_case53b_alias_asymmetric_shrink_cannot_offset_growth(self) -> None:
        """old の別名（実在しない `old_string` + 多出する `oldText`）で縮小だけを水増しできない。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 19_000, encoding="utf-8")
        # old_string が無い Edit は、リスクの段が低でない steering では risk_tier が先に止めるので、段を低にし、依頼の原文（hook の節で始まる request.md）を置く
        self._steering_file("request-crosscheck.md").write_text("### リスクの段\n\nリスクの段: 低\n", encoding="utf-8")
        self._steering_file("request.md").write_text("<!-- gdd-request-capture:begin -->\n", encoding="utf-8")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(state_path),
                "edits": [
                    {"old_string": "a", "new_string": "y" * 19_000},
                    {"old_string": "Q" * 10, "oldText": "a", "new_string": "", "replace_all": True},
                ],
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 37_999, STATE_LIMIT)

    def test_case53c_empty_old_replace_all_counts_insertions(self) -> None:
        """`old_string: ""` + replace_all は文字数 + 1 箇所へ挿入される（`str.replace` の仕様）。1 回分に丸めない。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("z" * 19_000, encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "", "new_string": "y", "replace_all": True},
        }
        self._assert_size_notice(self._run(payload), "state.md", 38_001, STATE_LIMIT)

    def test_case53d_edits_dict_is_treated_as_single_edit(self) -> None:
        """`edits` が list でなく dict でも 1 要素として算出する（容器の型ゆらぎで諦めない）。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * 19_000, encoding="utf-8")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {"file_path": str(state_path), "edits": {"old_string": "x", "new_string": "y" * 30_000}},
        }
        self._assert_size_notice(self._run(payload), "state.md", 48_999, STATE_LIMIT)

    def test_case53e_non_str_old_is_treated_as_pure_growth(self) -> None:
        """old が非 str / 欠落なら 0 バイト扱い（純増）で算出する（old 側だけ不明で諦めない）。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * 19_000, encoding="utf-8")
        for old in (123, None, ["x"]):
            with self.subTest(old=type(old).__name__):
                tool_input = {"file_path": str(state_path), "new_string": "y" * 30_000}
                if old is not None:
                    tool_input["old_string"] = old
                result = self._run({"tool_name": "Edit", "tool_input": tool_input})
                self._assert_size_notice(result, "state.md", 49_000, STATE_LIMIT)

    def test_case53f_replace_all_with_absent_old_counts_at_least_once(self) -> None:
        """old が既存に無くても replace_all の増分は 1 回分を下限に計上する（hits=0 を 0 倍にしない）。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("z" * 19_000, encoding="utf-8")
        # old_string が無い Edit は、リスクの段が低でない steering では risk_tier が先に止めるので、段を低にし、依頼の原文（hook の節で始まる request.md）を置く
        self._steering_file("request-crosscheck.md").write_text("### リスクの段\n\nリスクの段: 低\n", encoding="utf-8")
        self._steering_file("request.md").write_text("<!-- gdd-request-capture:begin -->\n", encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "q", "new_string": "y" * 2_000, "replace_all": True},
        }
        self._assert_size_notice(self._run(payload), "state.md", 20_999, STATE_LIMIT)

    def test_case53g_shrink_only_replace_all_over_limit_has_no_notice(self) -> None:
        """上限超過中でも縮小だけの replace_all は通知しない（超過は「増える」書き込みだけ）。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 25_000, encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "a", "new_string": "", "replace_all": True},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 54: 上界推定の適用漏れと受理集合の非対称 ---
    def test_case54_prior_edit_cannot_amplify_replace_all(self) -> None:
        """先行 edit が後続 replace_all の対象を増やす形でも上界で算出する。

        haystack を「元の内容 + 全 edit の new 文字列」にして、逐次適用で作られうる出現の上界を採る
        （元の内容だけで数えると hits=0 → 1 回分に丸められる）。
        """
        state_path = self._steering_file("state.md")
        state_path.write_text("HEADER\n" + "b" * 18_990, encoding="utf-8")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(state_path),
                "edits": [
                    {"old_string": "HEADER", "new_string": "Q" * 500},
                    {"old_string": "Q", "new_string": "Q" + "y" * 100, "replace_all": True},
                ],
            },
        }
        self._assert_size_notice(self._run(payload), "state.md", 69_591, STATE_LIMIT)

    def test_case54b_edits_dict_does_not_bypass_secret_detection(self) -> None:
        """`edits` が dict でも secret / email 等の detector に届く（size 側と受理集合を揃える）。"""
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(state_path),
                "edits": {"old_string": "x", "new_string": f"contact: {NON_EXAMPLE_EMAIL}"},
            },
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("email address", self._deny_json(result)["systemMessage"])

    def test_case54c_replace_all_growth_over_read_limit_still_notifies(self) -> None:
        """1MB 超のファイルは既存内容を読まないが、replace_all の増分は 1 回分下限で算出する。"""
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 1_000_001, encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "a", "new_string": "ab", "replace_all": True},
        }
        self._assert_size_notice(self._run(payload), "state.md", 1_000_002, STATE_LIMIT)

    def test_case54d_replace_all_at_read_limit_counts_occurrences(self) -> None:
        """ちょうど 1MB のファイルは読んで出現回数を掛ける（境界値の off-by-one 固定）。

        出現回数（1,000,000）× +1B が計上される（1 回分下限なら 1000001 と表示される）。
        """
        state_path = self._steering_file("state.md")
        state_path.write_text("a" * 1_000_000, encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "a", "new_string": "ab", "replace_all": True},
        }
        self._assert_size_notice(self._run(payload), "state.md", 2_000_000, STATE_LIMIT)

    # --- Case 46: tasklist.md（最大の超過対象）の通知と、縮小 Write の通知なし ---
    def test_case46_tasklist_oversize_write_notifies_and_shrink_write_does_not(self) -> None:
        tasklist_path = self._steering_file("tasklist.md")
        tasklist_path.write_text("x" * (TASKLIST_LIMIT + 5_000), encoding="utf-8")
        grow = {"tool_name": "Write", "tool_input": {"file_path": str(tasklist_path), "content": "x" * (TASKLIST_LIMIT + 6_000)}}
        self._assert_size_notice(self._run(grow), "tasklist.md", TASKLIST_LIMIT + 6_000, TASKLIST_LIMIT)
        # 縮小 Write（Edit だけでなく Write 経路も）は上限超過中でも通知しない
        shrink = {"tool_name": "Write", "tool_input": {"file_path": str(tasklist_path), "content": "x" * (TASKLIST_LIMIT + 1_000)}}
        result2 = self._run(shrink)
        self.assertEqual(result2.returncode, 0, result2.stderr)
        self._assert_no_size_notice(result2)

    # --- Case 45: lone surrogate で hook が落ちて既存 deny が fail-open しない ---
    def test_case45_lone_surrogate_does_not_crash_hook_or_bypass_existing_deny(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": f"contact: {NON_EXAMPLE_EMAIL} \ud800"},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 2, result.stderr)  # email deny は生きている（rc=1 の traceback にならない）
        self.assertNotIn("Traceback", result.stderr)
        # 超過 + surrogate: surrogatepass で算出を継続し通知を出す（surrogate は 3 バイトで数える）
        oversize = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * 30_000 + "\ud800"},
        }
        result2 = self._run(oversize)
        self.assertNotIn("Traceback", result2.stderr)
        self._assert_size_notice(result2, "state.md", 30_003, STATE_LIMIT)
        # 上限内 + surrogate: 算出は継続するが超過しないので通知なし
        within = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * 1_000 + "\ud800"},
        }
        result3 = self._run(within)
        self.assertEqual(result3.returncode, 0, result3.stderr)
        self.assertNotIn("Traceback", result3.stderr)
        self._assert_no_size_notice(result3)

    # --- Case 45e: 上限超過中のファイルへの小さい書き込み（surrogate 入り）→ 落ちず、通知も旧 advisory も出ない ---
    def test_case45e_surrogate_small_write_on_oversized_file_has_no_notice(self) -> None:
        """別名 key（`newText`）に surrogate を入れても落ちない。

        post size は 8 バイトで既存サイズより小さいので超過ではない（契約 6）。
        旧 advisory の "[artifact size]" は on-disk サイズで出ていたが、無くなった（契約 8）。
        """
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT + 5_000), encoding="utf-8")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "newText": "note \ud800"},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 45f: 証跡行に surrogate があっても本来の判定が出る ---
    def test_case45f_surrogate_in_self_review_line_keeps_real_verdict(self) -> None:
        """`parse_self_review_line` の tempfile write が surrogate で落ちて guard 固定文に化けない。"""
        state_path = self._steering_file("state.md")
        invalid = (
            "- Pre-Push Self Review: abc1234 | rounds: 3 | dry: yes | "
            "lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z \ud800\n"
        )
        result = self._run(
            {"tool_name": "Write", "tool_input": {"file_path": str(state_path), "content": invalid}}
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        message = self._deny_json(result)["systemMessage"]
        self.assertNotIn("internal error", message)
        self.assertIn("Pre-Push Self Review", message)

    # --- Case 45b: path 側 directory segment の lone surrogate でも既存 deny が走る ---
    def test_case45b_surrogate_in_path_segment_keeps_existing_deny(self) -> None:
        bad_dir = Path(self._tmp) / ".steering" / "seg\ud800dir" / "state.md"
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(bad_dir), "content": f"contact: {NON_EXAMPLE_EMAIL}"},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        # 内部エラーの fail-closed ではなく、本来の email deny が出ていること
        self.assertIn("email address", self._deny_json(result)["systemMessage"])

    # --- Case 45c: 2 つ目の target key（`path`）側の lone surrogate ---
    def test_case45c_surrogate_in_second_target_key_keeps_existing_deny(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(state_path),
                "path": str(Path(self._tmp) / ".steering" / "other\ud800" / "state.md"),
                "content": f"contact: {NON_EXAMPLE_EMAIL}",
            },
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("email address", self._deny_json(result)["systemMessage"])

    # --- Case 45d: ApplyPatch の `*** Update File:` header 側の lone surrogate ---
    def test_case45d_surrogate_in_applypatch_header_keeps_existing_deny(self) -> None:
        target = Path(self._tmp) / ".steering" / "patch\ud800" / "state.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {target}\n"
            f"+contact: {NON_EXAMPLE_EMAIL}\n"
            "*** End Patch\n"
        )
        result = self._run({"tool_name": "ApplyPatch", "tool_input": {"patch": patch}})
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("email address", self._deny_json(result)["systemMessage"])

    # --- Case 48: main() の未捕捉例外は deny（exit 2）へ倒れる ---
    def test_case48_internal_error_fails_closed_without_traceback(self) -> None:
        state_path = self._steering_file("state.md")
        # payload が dict でない（JSON 配列）。`payload.get` が AttributeError を投げ、
        # top-level guard が無いと exit 1 = PreToolUse 非 block になる。
        result = self._run([{"tool_name": "Write"}])
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        message = self._deny_json(result)["systemMessage"]
        self.assertIn("the guard hit an internal error and fails closed", message)
        self.assertIn("AttributeError", message)  # 型名のみ（メッセージ・path は載せない）
        self.assertNotIn(str(state_path), message)

    # --- Case 48b: 非 str の transcript_path は guard ではなく「未指定」扱い ---
    def test_case48b_non_str_transcript_path_is_treated_as_absent(self) -> None:
        """型ゆらぎ 1 つで全 `.steering` write が恒久 deny にならない（自動 escape hatch が無い経路）。"""
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "ok"},
            "transcript_path": {"not": "a string"},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn("internal error", result.stdout + result.stderr)

    # --- Case 48c: transcript_path の**値**に surrogate → peer 扱い ---
    def test_case48c_surrogate_transcript_path_falls_back_to_peer_turn(self) -> None:
        """値軸の surrogate は guard 固定文ではなく本来の判定（peer 扱い = fail-closed）にする。

        `lib/transcript.py` の `except OSError` は filename encode の
        `UnicodeEncodeError`（= `ValueError`）を拾わないため、そのままだと
        同一 session の全 `.steering` write が自動回復なしで恒久 deny になる。
        """
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(state_path),
                "content": "Human Check Status: approved\n",
            },
            "transcript_path": str(Path(self._tmp) / "tr\ud800.jsonl"),
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        message = self._deny_json(result)["systemMessage"]
        self.assertNotIn("internal error", message)
        self.assertIn("別セッションからのメッセージ", message)

    # --- Case 48d: surrogate な transcript_path でも無関係な write は通る ---
    def test_case48d_surrogate_transcript_path_does_not_deny_ordinary_write(self) -> None:
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "ok\n"},
            "transcript_path": str(Path(self._tmp) / "tr\ud800.jsonl"),
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("internal error", result.stdout + result.stderr)

    # --- Case 49: Write の別名 content key でも size が算出される ---
    def test_case49_write_alias_content_key_over_limit_notifies(self) -> None:
        """受理集合の正本は `NEW_STRING_KEYS`。`Write` 分岐の別リテラルが穴だった。"""
        for key in ("newText", "new_string", "replacement", "contents"):
            with self.subTest(key=key):
                state_path = self._steering_file("state.md")
                payload = {
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(state_path), key: "x" * (STATE_LIMIT + 1)},
                }
                self._assert_size_notice(self._run(payload), "state.md", STATE_LIMIT + 1, STATE_LIMIT)

    # --- Case 49b: decoy 別名を同居させても実サイズが隠せない ---
    def test_case49b_write_decoy_alias_does_not_hide_real_size(self) -> None:
        """`NEW_STRING_KEYS` の走査順に依存せず、str 値を持つ全 key の最大バイト長で算出する。"""
        cases = [
            ("content-over_new_string-decoy", {"content": "x" * (STATE_LIMIT + 1), "new_string": "y"}),
            ("newText-over_content-decoy", {"newText": "x" * (STATE_LIMIT + 1), "content": "y"}),
        ]
        for label, extra in cases:
            with self.subTest(case=label):
                state_path = self._steering_file("state.md")
                payload = {
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(state_path), **extra},
                }
                self._assert_size_notice(self._run(payload), "state.md", STATE_LIMIT + 1, STATE_LIMIT)

    # --- Case 49c: Edit / MultiEdit の decoy 別名でも最大 delta を採る ---
    def test_case49c_edit_decoy_alias_does_not_shrink_delta(self) -> None:
        """new 側は最大・old 側は最小を採るので、decoy を足しても delta を縮められない。"""
        for tool in ("Edit", "MultiEdit"):
            with self.subTest(tool=tool):
                state_path = self._steering_file("state.md")
                state_path.write_text("a" * 100, encoding="utf-8")
                edit = {
                    "old_string": "a",
                    "oldText": "a" * 50,  # decoy: 大きい old で delta を縮めようとする
                    "new_string": "b",  # decoy: 小さい new で post size を隠そうとする
                    "newText": "b" * (STATE_LIMIT + 1),
                }
                tool_input = (
                    {"file_path": str(state_path), **edit}
                    if tool == "Edit"
                    else {"file_path": str(state_path), "edits": [edit]}
                )
                result = self._run({"tool_name": tool, "tool_input": tool_input})
                # 100 + (20,001 − 1) = 20,100（decoy の new / old を採ると上限内に倒れる）
                self._assert_size_notice(result, "state.md", 20_100, STATE_LIMIT)

    # --- Case 50: 壊れた counter state file は「0 回」扱いで deny を維持 ---
    def test_case50_corrupt_deny_counter_state_does_not_become_guard_failure(self) -> None:
        """counter が読めないだけで (path, category) が恒久 deny で固まらない。

        guard 追加前は静かな fail-open だった経路が、guard 追加で「全 write 恒久
        deny」へ反転していた。
        """
        state_path = self._steering_file("state.md")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": f"contact: {NON_EXAMPLE_EMAIL}"},
        }
        # 1 回目の deny で counter state file を作る
        first = self._run(payload)
        self.assertEqual(first.returncode, 2, first.stderr)
        counter_files = self._counter_files()
        self.assertTrue(counter_files, "deny counter state file が作られていない")

        corruptions: list[bytes] = [
            b'["not", "a", "dict"]',  # 妥当な JSON だが非 dict -> AttributeError
            b'{"count": "three", "ts": "yesterday"}',  # count / ts が非数値 -> TypeError/ValueError
            b"\xff\xfe\x00\x01",  # 不正バイト -> UnicodeDecodeError
        ]
        for corrupt in corruptions:
            with self.subTest(corrupt=corrupt[:12]):
                for f in counter_files:
                    f.write_bytes(corrupt)
                result = self._run(payload)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                message = self._deny_json(result)["systemMessage"]
                self.assertNotIn("internal error", message)
                self.assertIn("email address", message)

    # --- Case 34: tool_input が str の payload でも既存 deny が失われない ---
    def test_case34_str_tool_input_keeps_existing_denies(self) -> None:
        state_path = self._steering_file("state.md")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {state_path}\n"
            f"+contact: {NON_EXAMPLE_EMAIL}\n"
            "*** End Patch\n"
        )
        # ApplyPatch の str payload。size 算出は不能だが hook は落ちてはいけない。
        result = self._run({"tool_name": "Write", "tool_input": patch})
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    # --- Case 35: resolve() 不能なパスでも既存 deny が走る ---
    def test_case35_unresolvable_path_keeps_existing_denies(self) -> None:
        state_path = self._steering_file("state.md")
        secret_value = "AKIA" + "IOSFODNN7EXAMPLE"
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(state_path) + "\x00truncated",
                "content": f"key: {secret_value}",
            },
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    # --- Case 36 (ADR-3): stat() が失敗する対象は tool_name によらず算出不能 → 通知なし ---
    def test_case36_stat_failure_is_uncomputable_for_write_too(self) -> None:
        # 親ディレクトリを実行不可にして stat を失敗させる。
        state_path = self._steering_file("state.md")
        state_path.write_text("x" * (STATE_LIMIT + 500), encoding="utf-8")
        parent = state_path.parent
        original_mode = parent.stat().st_mode
        os.chmod(parent, 0o000)
        self.addCleanup(os.chmod, parent, original_mode)
        if os.access(parent, os.X_OK):
            self.skipTest("stat() を失敗させられない環境（root 等）")
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(state_path), "content": "x" * (STATE_LIMIT + 1)},
        }
        result = self._run(payload)
        # 算出不能 (d) なので超過にならない（Write でも baseline=0 に落とさない）
        self.assertEqual(result.returncode, 0, result.stderr)
        self._assert_no_size_notice(result)

    # --- Case 37: newText / replacement / contents 別名でも size が算出される ---
    def test_case37_edit_aliases_are_measured(self) -> None:
        for new_key in ("new_string", "newText", "replacement", "contents"):
            with self.subTest(new_key=new_key):
                state_path = self._steering_file("state.md")
                state_path.write_text("x" * (STATE_LIMIT - 10), encoding="utf-8")
                payload = {
                    "tool_name": "Edit",
                    "tool_input": {
                        "file_path": str(state_path),
                        "old_string": "x" * 5,
                        new_key: "y" * 1000,
                    },
                }
                self._assert_size_notice(self._run(payload), "state.md", 20_985, STATE_LIMIT)

    # --- Case 37b: Write の `contents` / edits 内 `content` も測る ---
    def test_case37b_write_and_edit_content_aliases_are_measured(self) -> None:
        cases = [
            (
                "Write/contents",
                {"tool_name": "Write", "tool_input": {"file_path": None, "contents": "y" * (STATE_LIMIT + 5)}},
                0,
                STATE_LIMIT + 5,
            ),
            (
                "MultiEdit/content",
                {
                    "tool_name": "MultiEdit",
                    "tool_input": {
                        "file_path": None,
                        "edits": [{"old_string": "x" * 5, "content": "y" * 1000}],
                    },
                },
                STATE_LIMIT - 10,
                20_985,
            ),
            (
                "Edit/content",
                {
                    "tool_name": "Edit",
                    "tool_input": {"file_path": None, "old_string": "x" * 5, "content": "y" * 1000},
                },
                STATE_LIMIT - 10,
                20_985,
            ),
            (
                "MultiEdit/contents",
                {
                    "tool_name": "MultiEdit",
                    "tool_input": {
                        "file_path": None,
                        "edits": [{"old_string": "x" * 5, "contents": "y" * 1000}],
                    },
                },
                STATE_LIMIT - 10,
                20_985,
            ),
        ]
        for label, payload, existing, post in cases:
            with self.subTest(label=label):
                state_path = self._steering_file("state.md")
                state_path.write_text("x" * existing, encoding="utf-8")
                payload["tool_input"]["file_path"] = str(state_path)
                self._assert_size_notice(self._run(payload), "state.md", post, STATE_LIMIT)

    # --- Case 38b: 非超過の state.md write では advisory lint が起動する ---
    def test_case38b_allowed_write_still_runs_advisory_lints(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        marker = root / "lint-was-invoked"
        (root / "scripts").mkdir()
        probe = "from pathlib import Path\n" f"Path({str(marker)!r}).write_text('1')\n"
        for name in ("lint-approved-direction.py", "lint-ac.py"):
            (root / "scripts" / name).write_text(probe, encoding="utf-8")
        state_path = self._steering_file("state.md")
        state_path.write_text("ok", encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state_path), "old_string": "ok", "new_string": "fine"},
        }
        allowed = self._run(payload, extra_env={"CLAUDE_PLUGIN_ROOT": str(root)})
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertTrue(marker.exists(), "advisory lint が起動していない")


if __name__ == "__main__":
    unittest.main()
