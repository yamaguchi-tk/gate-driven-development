"""self-review evidence 検査 (AC-11 / AC-22 / AC-6) の回帰テスト。

`hooks/scripts/validate-steering-write.py` の `collect_self_review_evidence_violations` /
`collect_state_core_field_violations` を実 hook stdin 経路（subprocess）で検査する。
判定の正本は shipped parser `gdd_parse_self_review_field`
(`hooks/scripts/lib/self-review-evidence.sh`) に委譲されており、本ファイルは
独自の書式を発明せず、正本と同一の fixture 文字列だけを使う
（T-21 Verification（正本整合 / L-38 規律）参照）。

Carry Forward:
- T-19 impl-gate Attempt 2 advisory L-46（実装は正しいがテストで固定されていない 3 挙動）:
  test_self_review_empty_value_write_denies / test_self_review_pre_pr_side_invalid_denies /
  test_self_review_second_touched_field_invalid_denies_even_after_first_field_valid で固定する。
- advisory L-45（連結 chunk の順序依存）は `collect_self_review_evidence_violations` の
  docstring に既知の限界 (2) として **追記済み**（impl-gate Attempt 1 M-2 の remediation）。
  ただし Attempt 1 時点の「誤爆方向のみで fail-open にはならない」という記述は
  impl-gate Attempt 2 の実測で **偽**と判明した（M-1'）。実際は連結順で判定が決まり
  fail-open にも倒れ、発火は複数ファイル `ApplyPatch` に限らず単一 `Write` /
  `MultiEdit` でも起きる。「限定的な連言が要るので test 化は過剰」という Attempt 1 の
  判断根拠はこの実測で失効したため、docstring を実態へ訂正したうえで
  test_self_review_concatenated_chunk_order_decides_verdict が現状挙動を固定する
  （記述だけを直すと、同じ記述が次の編集でまた実態から外れる）。
- advisory L-43（chunk 境界をまたぐ部分 Edit は無検査）は
  `collect_self_review_evidence_violations` の docstring に既に明記済みのため
  本タスクでの追加対応なし。

命名規約: `Planned Verification` が `-k self_review` で本ファイルを絞り込む前提のため、
全 test method 名に `self_review` を含める（pytest -k はケース非依存だが区切り文字は
正規化しないため、クラス名 `SelfReviewEvidenceValidationTests` だけでは `self_review`
に部分一致しない）。
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

VALID_PRE_PUSH_LINE = (
    "Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 "
    "| dry: no | lanes: internal=1,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z\n"
)
VALID_PRE_PR_LINE = (
    "Pre-PR Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 "
    "| dry: no | lanes: internal=1,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z\n"
)
MALFORMED_PRE_PUSH_LINE = "Pre-Push Self Review: def5678 | rounds: 2\n"
# 独立レビューへの委譲記録形。受理面は Task Size 依存（standard のみ）。
DELEGATED_PRE_PUSH_LINE = (
    "Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 1 "
    "| dry: no | lanes: internal=2,grounding=not_applicable(independent-review),"
    "adversarial=not_applicable(independent-review) | at: 2026-08-17T00:00:00Z\n"
)
GROUNDING_DELEGATED_PRE_PUSH_LINE = (
    "Pre-Push Self Review: abc1234 | rounds: 1 | consecutive_clean: 0 "
    "| dry: no | lanes: internal=2,grounding=not_applicable(independent-review),"
    "adversarial=0 | at: 2026-08-17T00:00:00Z\n"
)
MALFORMED_PRE_PR_LINE = "Pre-PR Self Review: def5678 | rounds: 2\n"


class SelfReviewEvidenceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)

    def _run(self, payload: dict, *, extra_env: dict | None = None) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        if extra_env:
            env.update(extra_env)
        script = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
        return subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_self_review_edit_to_malformed_value_denies_even_with_prior_valid_line(self) -> None:
        """chunk 限定検査による false-pass 防止（既存に有効な行がある state.md への不正 Edit）"""
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / ".steering" / "20260817-x" / "state.md"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(VALID_PRE_PUSH_LINE, encoding="utf-8")
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(state_path),
                    "new_string": MALFORMED_PRE_PUSH_LINE,
                },
            }
            result = self._run(payload)
            self.assertEqual(result.returncode, 2)

    def test_self_review_mixed_category_four_consecutive_denies_stays_denied(self) -> None:
        """self_review_evidence は NON_DEMOTABLE_CATEGORIES なので escape hatch で降格しない。

        観測点は **4 回すべての returncode**。escape hatch は 3 回目に allow へ降格した
        直後に counter を clear するため（`validate-steering-write.py` の `main` 末尾）、
        4 回目は降格が有効でも deny に戻る。終状態だけを見ると降格の有無と独立な観測に
        なり test が vacuous になる（impl-gate Attempt 1 の M-1）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / ".steering" / "20260817-y" / "state.md"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("", encoding="utf-8")
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(state_path),
                    # 省略記法（降格できる ellipsis category）+ 不正な self-review evidence
                    "new_string": (
                        "...省略\n"
                        + MALFORMED_PRE_PUSH_LINE
                    ),
                },
            }
            codes = [self._run(payload).returncode for _ in range(4)]
            # baseline は [2, 2, 2, 2]。NON_DEMOTABLE_CATEGORIES を空集合化する変異
            # （= AC-22 が禁じた自動 allow 降格の復活）では 3 回目だけが 0 に転じ
            # [2, 2, 0, 2] になる。差は 3 回目にしか現れないので全回を assert する。
            self.assertEqual(
                codes,
                [2, 2, 2, 2],
                "non-demotable category は MAX_CONSECUTIVE_DENIES 回目でも降格して"
                f"はならない（3 回目の allow 降格が復活していないか）: {codes!r}",
            )

    def test_self_review_empty_value_write_denies(self) -> None:
        """advisory L-46 (1): 値を空にする書き込み（`Pre-Push Self Review:` のみ）が deny される。

        trigger は has_state_field_line（値不問）である選択の固定。has_state_field
        （値必須）へ trigger を差し替えると、空値の書き込みが検査自体をすり抜けて
        allow へ転じる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / ".steering" / "20260817-empty" / "state.md"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("", encoding="utf-8")
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(state_path),
                    "new_string": "Pre-Push Self Review:\n",
                },
            }
            result = self._run(payload)
            self.assertEqual(result.returncode, 2)

    def test_self_review_pre_pr_side_invalid_denies(self) -> None:
        """advisory L-46 (2): `Pre-PR Self Review` 側の不正証跡が deny される。

        AC-6 は `Pre-PR Self Review` を名指しするが、既存の 8 検査も上記の draft 2 test も
        `Pre-Push Self Review` しか通していなかった。`Pre-PR Self Review` だけを
        SELF_REVIEW_FIELDS から外す退行を検知する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / ".steering" / "20260817-prepr" / "state.md"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("", encoding="utf-8")
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(state_path),
                    "new_string": MALFORMED_PRE_PR_LINE,
                },
            }
            result = self._run(payload)
            self.assertEqual(result.returncode, 2)

    def test_self_review_second_touched_field_invalid_denies_even_after_first_field_valid(self) -> None:
        """advisory L-46 (3): 2 field が並び、touched 順で後の field だけ不正でも deny される。

        `SELF_REVIEW_FIELDS = ("Pre-PR Self Review", "Pre-Push Self Review")` の順で
        `touched` が構築されるため、`Pre-PR Self Review`（正常）を先に `continue` した後、
        `Pre-Push Self Review`（不正）まで検査が届くかを固定する。`for field in touched:` を
        先頭要素だけ見て打ち切る変異（例: `touched[:1]`）が入ると、この test だけが
        SURVIVOR から検知できなくなる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / ".steering" / "20260817-second" / "state.md"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("", encoding="utf-8")
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(state_path),
                    "new_string": VALID_PRE_PR_LINE + MALFORMED_PRE_PUSH_LINE,
                },
            }
            result = self._run(payload)
            self.assertEqual(result.returncode, 2)

    def _apply_patch_rc(self, tmp: str, entries: list[tuple[str, str]]) -> int:
        """`entries`（(ファイル名, added line) の並び）を 1 つの ApplyPatch として送る。"""
        parts = ["*** Begin Patch"]
        for name, line in entries:
            path = Path(tmp) / ".steering" / "20260818-order" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
            parts += [f"*** Update File: {path}", "@@", "+" + line.rstrip("\n")]
        parts.append("*** End Patch")
        payload = {"tool_name": "ApplyPatch", "tool_input": {"patch": "\n".join(parts)}}
        return self._run(payload).returncode

    def test_self_review_concatenated_chunk_order_decides_verdict(self) -> None:
        """既知の限界 (2): 連結 chunk では**最初の 1 行**だけが判定され、順序で結果が変わる。

        docstring 側の主張（誤爆・fail-open の両方向が起きる / 発火は複数ファイル
        ApplyPatch に限らない）を実行で裏づけて固定する。impl-gate Attempt 1 は
        「誤爆方向のみで fail-open にはならない」と**実測せずに**書き、Attempt 2 で
        偽と判明した（M-1'）。記述だけを直しても次の編集で再び実態から外れるため、
        限界の**内側と外側の両方**をここで観測する。

        期待値は現状挙動の固定であって、望ましい挙動の宣言ではない。挙動を直す
        （書き込み単位ごとに分割 / 全出現を検査）なら design 変更として本 test も
        書き換えること。
        """
        with tempfile.TemporaryDirectory() as tmp:
            # 対照: state.md 単独の不正行は deny される
            self.assertEqual(
                self._apply_patch_rc(tmp, [("state.md", MALFORMED_PRE_PUSH_LINE)]),
                2,
                "対照が deny でないと以降の比較が無意味になる",
            )
            # fail-open: 他ファイルの有効行が先に来ると、同じ不正行が allow に転じる
            self.assertEqual(
                self._apply_patch_rc(
                    tmp,
                    [("tasklist.md", VALID_PRE_PUSH_LINE), ("state.md", MALFORMED_PRE_PUSH_LINE)],
                ),
                0,
                "連結順に依存した fail-open が消えた（挙動を変えたなら docstring "
                "既知の限界 (2) も同時に更新すること）",
            )
            # 誤爆: 他ファイルの不正行が先に来ると、state.md が有効でも deny される
            self.assertEqual(
                self._apply_patch_rc(
                    tmp,
                    [("tasklist.md", MALFORMED_PRE_PUSH_LINE), ("state.md", VALID_PRE_PUSH_LINE)],
                ),
                2,
                "誤爆方向が消えた（同上）",
            )

    def test_self_review_single_file_write_also_order_dependent(self) -> None:
        """既知の限界 (2) の射程: 同じ順序依存は単一 `Write` でも起きる。

        「複数ファイル ApplyPatch という限定的な連言でのみ発火する」という Attempt 1 の
        受容根拠が成り立たないことの固定。限界の**外側が安全である**という主張を
        書くなら、その外側を実際に叩いて確かめる必要がある（M-1' の再発防止）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / ".steering" / "20260818-single" / "state.md"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("", encoding="utf-8")

            def rc(content: str) -> int:
                return self._run(
                    {"tool_name": "Write", "tool_input": {"file_path": str(state_path), "content": content}}
                ).returncode

            self.assertEqual(rc(VALID_PRE_PUSH_LINE + MALFORMED_PRE_PUSH_LINE), 0)
            self.assertEqual(rc(MALFORMED_PRE_PUSH_LINE + VALID_PRE_PUSH_LINE), 2)

            def rc_multi(*lines: str) -> int:
                return self._run(
                    {
                        "tool_name": "Edit",
                        "tool_input": {
                            "file_path": str(state_path),
                            "edits": [{"new_string": ln} for ln in lines],
                        },
                    }
                ).returncode

            # chunk が別々でも `chunk_text` へ連結されるため同じ順序依存になる
            self.assertEqual(rc_multi(VALID_PRE_PUSH_LINE, MALFORMED_PRE_PUSH_LINE), 0)
            self.assertEqual(rc_multi(MALFORMED_PRE_PUSH_LINE, VALID_PRE_PUSH_LINE), 2)


    def _rc_with_task_size(self, task_size: str, evidence_line: str, slug: str) -> int:
        """`Task Size` を持つ state.md へ証跡行を Edit したときの returncode を返す。"""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        state_path = Path(tmp) / ".steering" / f"20260907-{slug}" / "state.md"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(f"- Task Size: {task_size}\n", encoding="utf-8")
        return self._run(
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": str(state_path), "new_string": evidence_line},
            }
        ).returncode

    def test_self_review_delegation_token_write_is_task_size_dependent(self) -> None:
        """R4 #1: write 側も gate と同じ Task Size 依存の受理面にする。

        Task Size を渡さないと `quick (standard)` で「write は通るが pre-push gate は
        invalid にする」非対称に戻る（T-19 Attempt 1 の M-1 と同型）。
        """
        self.assertEqual(
            self._rc_with_task_size("quick (standard)", DELEGATED_PRE_PUSH_LINE, "quick"), 2
        )
        self.assertEqual(
            self._rc_with_task_size("quick (express)", DELEGATED_PRE_PUSH_LINE, "express"), 2
        )
        self.assertEqual(
            self._rc_with_task_size("standard", DELEGATED_PRE_PUSH_LINE, "standard"), 0
        )

    def test_self_review_grounding_delegation_token_write_is_task_size_dependent(self) -> None:
        """R4 #3: grounding 側の委譲 token も同じ受理面（adversarial だけの非対称にしない）"""
        self.assertEqual(
            self._rc_with_task_size(
                "quick (standard)", GROUNDING_DELEGATED_PRE_PUSH_LINE, "g-quick"
            ),
            2,
        )
        self.assertEqual(
            self._rc_with_task_size("standard", GROUNDING_DELEGATED_PRE_PUSH_LINE, "g-standard"),
            0,
        )

    def test_self_review_unknown_task_size_normalizes_to_standard(self) -> None:
        """未知値・欠落は pre-push gate と同じ規則で `standard` へ畳む（R4 #1 / #7）"""
        self.assertEqual(
            self._rc_with_task_size("bogus-size", DELEGATED_PRE_PUSH_LINE, "unknown"), 0
        )
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        state_path = Path(tmp) / ".steering" / "20260907-nosize" / "state.md"
        state_path.parent.mkdir(parents=True)
        state_path.write_text("", encoding="utf-8")
        rc = self._run(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(state_path),
                    "new_string": DELEGATED_PRE_PUSH_LINE,
                },
            }
        ).returncode
        self.assertEqual(rc, 0)

    def test_self_review_surrogate_path_does_not_crash_hook(self) -> None:
        """R5 #1: target path の lone surrogate で `read_text` が ValueError を投げても落ちない。

        `except OSError` だけだと `UnicodeEncodeError`（`ValueError` の subclass）が
        `main()` まで抜け、rc=1 で既存 deny category が 1 件も走らずに fail-open する。
        """
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        bad_path = f"{tmp}/.steering/20260907-sur\ud800rogate/state.md"
        proc = self._run(
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": bad_path, "new_string": DELEGATED_PRE_PUSH_LINE},
            }
        )
        self.assertNotIn("Traceback", proc.stderr)
        # 既存内容は読めない → Task Size 欠落 → `standard` へ畳む → 委譲記録形は受理
        self.assertEqual(proc.returncode, 0)

    def test_self_review_task_size_in_same_chunk_wins_over_existing(self) -> None:
        """R5 #2: 同じ write で `Task Size` を変える場合は chunk 側の新値が効く。

        `state_field_value` は最初の値付き出現を返すため、`existing + chunk` の順で
        連結すると既存値が常に勝ち、chunk 側の更新が無視される。
        """
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        state_path = Path(tmp) / ".steering" / "20260907-chunkwins" / "state.md"
        state_path.parent.mkdir(parents=True)
        state_path.write_text("- Task Size: standard\n", encoding="utf-8")
        rc = self._run(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(state_path),
                    "new_string": "- Task Size: quick (standard)\n" + DELEGATED_PRE_PUSH_LINE,
                },
            }
        ).returncode
        # chunk 側の `quick (standard)` が効けば委譲 token は invalid（既存値が勝つと 0）
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
