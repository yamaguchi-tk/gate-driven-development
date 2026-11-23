"""pre-push gate（`hooks/scripts/run-pre-push-gate-hook.sh`）の契約テスト。

候補 root の解決（`git -C`・`--work-tree`・コマンド内の `cd`）、steering の解決から証跡の照合まで
（step 7〜13）、block reason の許可文法（AC-18）、`hooks.json` の配線を置く。起動の短絡と
active GDD の判定（step 1〜6）は `test_pre_push_gate_activation_contract.py`、opt-out（AC-4）
とその記録は `test_pre_push_gate_optout_contract.py`、独立レビュー証跡（step 13b）は
`test_pre_push_independent_review_contract.py` にある。fixture は
`_pre_push_gate_support.PrePushGateFixtureMixin`。
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import _block_reason_support as support


from _paths import PLUGIN_ROOT
from _pre_push_gate_support import (
    AC18_ALLOWED_TOKENS,
    AC18_SHA_RE,
    AC18_TOKEN_RE,
    DEFAULT_STEERING_SLUG,
    HOOK,
    PrePushGateFixtureMixin,
)

HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"
HOOK_SCRIPT_NAME = HOOK.name
# 実 push 経路の平均の所要時間は 1 秒に近い。1 秒に縮めると遅い環境で timeout により
# fail-open しうるため、余裕込みの下限を契約として固定する。
MIN_HOOK_TIMEOUT_SECONDS = 10
_NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen",
)


class PrePushGateContractTests(PrePushGateFixtureMixin, unittest.TestCase):
    def _assert_block_reason_has_required_three_elements(self, reason: str) -> None:
        """design.md § block reason に必ず含める 3 要素（復旧可能性）。

        要素 1・2（記録先 / 必要 key の全列挙 + 正本パス）は全 hook 共通なので
        `_block_reason_support` の 1 本を使う。本 hook が上乗せするのは要素 3
        （escape hatch）だけ — `GDD_SKIP_PRE_PUSH_GATE` は AC-4 により pre-push gate
        限定の受理面であり、pre-PR gate 側には存在しない。
        """
        self.assertEqual(
            support.missing_recovery_elements(reason), [], f"復旧要素が欠落: {reason}"
        )
        self.assertIn("GDD_SKIP_PRE_PUSH_GATE=1 git push", reason)

    # ---- T-9 (step 7〜14): steering resolver / refspec tip / Task Size /
    # 証跡 parse・sha 一致・dry 判定 ------------------------------------------
    #
    # T-8 の時点ではファイルは「step 6 まで判定し、それ以降は該当しない限り恒久的に
    # exit 0」で終わっていた。以下は現時点でまだ存在しない step 7〜14 のロジックに
    # 対する RED で、design.md § pre-push gate の判定順（確定版）99〜106 行を正本と
    # する。`gdd_pre_push_resolve_steering` / `gdd_parse_self_review_field` 自体の
    # 内部分岐は T-6 の `tests/test_self_review_evidence.sh`（T6-1〜T6-9）で単体
    # 検証済みのため、ここでは「hook 本体がそれらを正しく呼び出し、結果に応じて
    # 不足の通知 / 通知なし を選ぶ」配線の契約に絞る（重複させない）。

    # -- step 7: steering resolver（AC-25）--------------------------------

    def test_step7_no_steering_dir_logs_unresolved_no_candidate_and_exits(self) -> None:
        """`.steering/` が無い（trivial 相当）場合は exit 0 かつ `unresolved-steering`
        / `no-candidate` を 1 行残す（design.md 99 行 + § opt-out ログの Why）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo, "git push origin main", extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)}
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            lines = [
                line
                for line in (state_dir / "pre-push-optout.log").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(lines), 1, lines)
            self.assertIn("event: unresolved-steering", lines[0])
            self.assertIn("reason: no-candidate", lines[0])

    def test_step7_multiple_active_candidates_blocks_steering_multiple(self) -> None:
        """候補 2 件（design.md § テスト方針の必須 fixture）は、検査する steering を
        1 件に決められないので不足として通知する（reason code: steering-multiple）。

        以前は `unresolved-steering` のログだけ残して exit 0 していた。pre-PR gate は
        同じ primary の multiple を不足として通知しており、pre-push もそろえる
        （review-log/20260924-steering-terminal-pipe-head.md の C1・方針メモ-1）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            self._write_steering(
                repo,
                slug="20260817-a",
                resume_from="gdd-implementation-gating",
                next_action="gdd-implementation-gating",
            )
            self._write_steering(
                repo,
                slug="20260817-b",
                resume_from="gdd-design-gating",
                next_action="gdd-design-gating",
            )
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo, "git push origin main", extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)}
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("steering-multiple", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("GDD_SKIP_PRE_PUSH_GATE=1", payload["hookSpecificOutput"]["additionalContext"])

    def test_step7_next_action_non_done_active_steering_blocks_missing_evidence_ac25(self) -> None:
        """AC-25 の中心claim: `Next Action` が `done` 以外でも gate が発火し、証跡
        なし push が不足として通知される。`Resume From` も非 done にして done 限定
        resolver への逆戻りを判別できるようにする。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            self._write_steering(
                repo,
                resume_from="gdd-implementation-gating",
                next_action="gdd-implementation-gating",
                task_size="standard",
                evidence=None,
            )

            result = self._run_hook(
                repo,
                "git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])

    def test_step7_resume_from_blocked_active_steering_blocks_missing_evidence(self) -> None:
        """`Resume From: blocked` は両経路で gate 対象に統一する（design.md 156
        行 / ADR-2）。design.md § テスト方針が明示する必須 fixture。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            self._write_steering(
                repo,
                resume_from="blocked",
                next_action="gdd-implementation-gating",
                task_size="standard",
                evidence=None,
            )

            result = self._run_hook(
                repo,
                "git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])

    def test_step7_registry_binding_resolves_and_blocks_missing_evidence(self) -> None:
        """design.md § テスト方針が明示する「registry binding 登録済み fixture」。

        `gdd_task_binding.py upsert-from-state` で登録した binding を
        `gdd_detect_active_steering` の primary 経路が解決し、`Next Action` が
        非 done でも gate が発火することを、fallback 経路とは独立に固定する
        （fallback だけで通ってしまう実装は、実運用で常用される registry 経路の
        バグを見逃す）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            steering = self._write_steering(
                repo,
                slug="20260817-registry",
                resume_from="gdd-implementation-gating",
                next_action="gdd-implementation-gating",
                task_size="standard",
                evidence=None,
                task_id="20260817-registry",
                worktree=repo,
                branch="main",
            )
            self._register_binding(repo, steering / "state.md")

            result = self._run_hook(
                repo,
                "git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])

    # -- step 8: refspec tip 解決（AC-16）----------------------------------

    def test_step8_ambiguous_refspec_forms_block(self) -> None:
        """`--all` / `--mirror` / 複数 refspec は tip を一意解決できないため不足として
        通知する（design.md 100 行・415 行）。証跡は意図的に有効なものを置き、
        refspec 判定が証跡 parse より先に効くことも併せて固定する。
        """
        for label, suffix in (
            ("all-flag", "--all"),
            ("mirror-flag", "--mirror"),
            ("two-refspecs", "main develop"),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                head = self._head_sha(repo)
                self._write_steering(
                    repo,
                    task_size="standard",
                    evidence=self._evidence_line(sha=head),
                )

                result = self._run_hook(
                    repo,
                    f"git push origin {suffix}",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("refspec-ambiguous", payload["hookSpecificOutput"]["additionalContext"])

    def test_step8_unresolvable_explicit_ref_blocks(self) -> None:
        """`git push origin feature-x:main` で `feature-x` が存在しなければ tip を
        解決できず不足として通知する（design.md 415 行の対テストの片側）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            head = self._head_sha(repo)
            self._write_steering(
                repo, task_size="standard", evidence=self._evidence_line(sha=head)
            )

            result = self._run_hook(
                repo,
                "git push origin feature-x:main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("refspec-ambiguous", payload["hookSpecificOutput"]["additionalContext"])

    # -- step 9 / 13: Task Size 正規化・dry 要求分岐（AC-20 / AC-5）--------

    def test_step9_task_size_case_and_unknown_values_normalize_to_standard_ac20(self) -> None:
        """design.md 132 行「4 値に加えて大文字混じり・未知値の 2 ケース」。
        いずれも `standard` へ正規化され dry を要求する（fail-closed 側）ことを、
        `dry: no` の証跡が `dry-not-reached` で不足として通知されることで観測する。
        """
        for label, raw_task_size in (
            ("uppercase-with-whitespace", "  STANDARD  "),
            ("unknown-falls-back", "banana"),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                head = self._head_sha(repo)
                self._write_steering(
                    repo,
                    task_size=raw_task_size,
                    evidence=self._evidence_line(sha=head, dry="no", consecutive_clean="0"),
                )

                result = self._run_hook(
                    repo,
                    "git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("dry-not-reached", payload["hookSpecificOutput"]["additionalContext"])
                self.assertIn("Task Size: standard", payload["hookSpecificOutput"]["additionalContext"])

    def test_step9_quick_express_does_not_require_dry_passes(self) -> None:
        """`quick (express)` は発火表どおり dry を要求しない（requirements.md
        107〜108 行）。証跡は有効かつ sha 一致・`dry: no` のまま素通りする。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            head = self._head_sha(repo)
            self._write_steering(
                repo,
                task_size="quick (express)",
                evidence=self._evidence_line(sha=head, dry="no", consecutive_clean="0", rounds="1"),
            )

            result = self._run_hook(
                repo,
                "git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_step9_quick_standard_does_not_require_dry_passes(self) -> None:
        """`quick (standard)` は 2026-09-06 緩和で dry を要求しない（発火表）。
        `dry: no` の証跡でも sha 一致なら素通りする。文字列部分一致で `standard` に誤分岐しない
        ことも、4 値それぞれが個別 case 分岐を通ることの間接確認になる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            head = self._head_sha(repo)
            self._write_steering(
                repo,
                task_size="quick (standard)",
                evidence=self._evidence_line(sha=head, dry="no", consecutive_clean="0", rounds="1"),
            )

            result = self._run_hook(
                repo,
                "git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_step9_trivial_bypasses_unconditionally_regardless_of_evidence_state_ac20(
        self,
    ) -> None:
        """design.md § 発火表 / AC-20: `Task Size: trivial` は証跡の状態に関わらず
        無条件で通す（rc==0・stdout 空・ログ副作用なし）。

        `if [[ "$TASK_SIZE" == "trivial" ]]; then exit 0; fi` の比較文字列を
        `__never__` 等へ変異させると、trivial タスクが step 10〜13（証跡 parse /
        sha 一致 / dry 判定）まで進んでしまい、証跡なし・sha 不一致・dry 未到達の
        いずれの状態でも本来は起きないはずの不足の通知が出る（誤爆方向：
        本来 gate が働いてはいけない trivial タスクで gate が働いてしまう）。
        `rc == 0` だけでは不足の通知の経路も `exit 0` するため判別できず、
        `stdout == ""` と opt-out ログ不在まで見て初めてこの変異を検出できる。
        """
        for label in ("no-evidence", "sha-mismatch", "dry-not-reached"):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                head = self._head_sha(repo)
                if label == "no-evidence":
                    evidence = None
                elif label == "sha-mismatch":
                    evidence = self._evidence_line(
                        sha="0123456789abcdef0123456789abcdef01234567"
                    )
                else:  # dry-not-reached
                    evidence = self._evidence_line(sha=head, dry="no", consecutive_clean="0")
                self._write_steering(repo, task_size="trivial", evidence=evidence)
                state_dir = Path(tmp) / "hookstate"

                result = self._run_hook(
                    repo,
                    "git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "", f"{label}: {result.stdout}")
                self.assertFalse(
                    (state_dir / "pre-push-optout.log").exists(),
                    f"{label}: unexpected log side effect",
                )

    # -- step 10: 証跡 parse（AC-18）----------------------------------------

    def test_step10_missing_pre_push_self_review_field_blocks_missing_evidence(self) -> None:
        """`Pre-Push Self Review` 自体が無ければ `missing-evidence` で不足として通知する
        （AC-1 の primary owner は本テストを持ち込んだ T-9。missing-evidence の通知の
        コードと契約テストを最初に固定したタスクを primary とする ADR-8 の規律に従う。
        T-8 の `unresolvable-root` と同型の切り分け）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            self._write_steering(repo, task_size="standard", evidence=None)

            result = self._run_hook(
                repo,
                "git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])

    # -- step 11: sha 一致（AC-3）-------------------------------------------

    def test_step11_sha_mismatch_blocks_when_evidence_sha_is_stale(self) -> None:
        """証跡 sha より新しいコミットを積んだ状態の push は不足として通知する（AC-3）。
        再レビュー後に証跡 sha を HEAD に更新すれば通ることも対で固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            stale_sha = self._head_sha(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)
            self._write_steering(
                repo, task_size="standard", evidence=self._evidence_line(sha=stale_sha)
            )

            result = self._run_hook(
                repo,
                "git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("sha-mismatch", payload["hookSpecificOutput"]["additionalContext"])

    # -- step 12: dry/consecutive_clean 自己矛盾（AC-5）---------------------

    def test_step12_dry_yes_with_consecutive_clean_zero_blocks_as_contradiction(self) -> None:
        """`dry: yes` かつ `consecutive_clean: 0` は自己矛盾した証跡として
        `gdd_parse_self_review_field` 内で invalid になり、hook 側は他の invalid
        原因と同じ `missing-evidence` 分岐へ合流する。

        2026-09-06 改訂で閾値は `< 2` から `== 0` へ緩んだ（「2 連続」要件の撤廃。
        正本: references/self-review-lanes.md）。`consecutive_clean: 1` が通る側は
        `tests/test_pre_push_independent_review_contract.py` が固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            head = self._head_sha(repo)
            self._write_steering(
                repo,
                task_size="standard",
                evidence=self._evidence_line(sha=head, dry="yes", consecutive_clean="0"),
            )

            result = self._run_hook(
                repo,
                "git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])

    # -- step 14: 成功経路（AC-25 / AC-16 / AC-3 の統合）--------------------

    def test_full_flow_registry_bound_non_done_steering_with_valid_evidence_passes(self) -> None:
        """AC-25 の肯定側: registry 経路で解決した非 done steering でも、証跡 sha
        が push 対象 ref の tip と一致し `dry: yes` / `consecutive_clean: 2` なら
        通す（不足として通知しない）。step 7〜14 全体の黄金経路。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            head = self._head_sha(repo)
            steering = self._write_steering(
                repo,
                slug="20260817-golden",
                resume_from="gdd-implementation-gating",
                next_action="gdd-implementation-gating",
                task_size="standard",
                evidence=self._evidence_line(sha=head, dry="yes", consecutive_clean="2"),
                task_id="20260817-golden",
                worktree=repo,
                branch="main",
            )
            self._register_binding(repo, steering / "state.md")

            result = self._run_hook(
                repo,
                "git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    # -- 出力形式（formatting / output schema path・AC-18）-----------------

    def test_step7_to_13_block_reasons_include_required_three_elements_and_no_slug_leak(
        self,
    ) -> None:
        """不足の通知を出す全ケースの reason に「記録先 <steering-dir>/state.md」「不足 key
        名」「escape hatch 1 行」の 3 要素が含まれ（design.md 219〜221 行）、かつ
        `.steering/<slug>` の実 slug（案件名を含みうる）が漏れないこと（209 行）を、
        step 7〜13 が新たに導入する 4 種の reason code すべてで固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            secret_slug = "20260817-project-secret"
            head = self._head_sha(repo)

            cases: list[tuple[str, str, str]] = [
                ("refspec-ambiguous", "git push origin --all", self._evidence_line(sha=head)),
                ("missing-evidence", "git push -u origin main", None),
                (
                    "sha-mismatch",
                    "git push -u origin main",
                    self._evidence_line(sha="0123456789abcdef0123456789abcdef01234567"),
                ),
                (
                    "dry-not-reached",
                    "git push -u origin main",
                    self._evidence_line(sha=head, dry="no", consecutive_clean="0"),
                ),
            ]

            for reason_code, command, evidence in cases:
                with self.subTest(reason_code=reason_code), tempfile.TemporaryDirectory() as state_tmp:
                    self._write_steering(
                        repo, slug=secret_slug, task_size="standard", evidence=evidence
                    )

                    result = self._run_hook(
                        repo, command, extra_env={"GDD_HOOK_STATE_DIR": state_tmp}
                    )

                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                    reason = payload["hookSpecificOutput"]["additionalContext"]
                    self.assertIn(reason_code, reason)
                    self._assert_block_reason_has_required_three_elements(reason)
                    self.assertNotIn(secret_slug, reason)
                    self.assertNotIn(str(repo), reason)

    # -- H-1 remediation: 値の上書き型変異に対する回帰ガード -----------------
    #
    # impl-gate Attempt 1 の SURVIVOR は「正しく解決した中間結果を後段で別の値へ
    # 上書きする」型（resolve-then-discard）だった。分岐を消す型の変異は既存
    # test 群が殺せるが、`TIP_SHA` を `$HEAD_SHA` で、`PROJECT_ROOT` を
    # `$PROCESS_CWD` で上書きする型は「解決結果と代替値が一致する fixture」しか
    # 無いと素通りする。以下は代替値と解決結果が必ず食い違う fixture を作って
    # その差を観測する対テスト。

    def _commit_extra(self, repo: Path, name: str) -> str:
        """`repo` に 1 コミット足し、そのコミットの sha を返す。"""
        (repo / name).write_text(f"{name}\n", encoding="utf-8")
        subprocess.run(["git", "add", name], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", f"add {name}"], cwd=repo, check=True)
        return self._head_sha(repo)

    def _repo_with_diverged_branch(self, tmp: Path) -> tuple[Path, str, str]:
        """`feature-x` の tip が HEAD（`main`）より 1 コミット進んだ repo を作る。

        戻り値は `(repo, main の HEAD sha, feature-x の tip sha)` で、両者は必ず
        異なる。AC-16（fail-open 経路 5）の判別には「tip != HEAD」が必須。
        """
        repo = tmp / "repo"
        repo.mkdir()
        self._init_repo(repo)
        subprocess.run(["git", "checkout", "-q", "-b", "feature-x"], cwd=repo, check=True)
        feature_tip = self._commit_extra(repo, "feature.py")
        subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
        head = self._head_sha(repo)
        self.assertNotEqual(head, feature_tip)
        self._write_local_state(repo, active=True)
        return repo, head, feature_tip

    def test_step8_cross_ref_push_compares_explicit_ref_tip_not_head_ac16(self) -> None:
        """否定側: `git push origin feature-x:main` の照合対象は HEAD ではなく
        **explicit ref の tip**（requirements.md 273 行 fail-open 経路 5 / AC-16）。

        証跡 sha = HEAD（= レビュー済みの `main`）でも、publish されるのは
        `feature-x` の tip なので `sha-mismatch` で不足として通知されなければならない。
        `TIP_SHA` を解決直後に `$HEAD_SHA` で上書きする値置換型の変異は、この
        fixture でのみ観測できる（tip == HEAD の fixture では判別力がゼロ）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo, head, _feature_tip = self._repo_with_diverged_branch(Path(tmp))
            self._write_steering(
                repo, task_size="standard", evidence=self._evidence_line(sha=head)
            )

            result = self._run_hook(
                repo,
                "git push origin feature-x:main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("sha-mismatch", payload["hookSpecificOutput"]["additionalContext"])

    def test_step8_cross_ref_push_passes_when_evidence_matches_explicit_ref_tip_ac16(
        self,
    ) -> None:
        """肯定側: 同じ fixture で証跡 sha を `feature-x` の tip に更新すれば通す。

        否定側だけだと「常に不足として通知する」変異でも緑になるため、対で固定する
        （design.md § block reason テストは両方向 の規律）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo, _head, feature_tip = self._repo_with_diverged_branch(Path(tmp))
            self._write_steering(
                repo, task_size="standard", evidence=self._evidence_line(sha=feature_tip)
            )

            result = self._run_hook(
                repo,
                "git push origin feature-x:main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_step7_to_11_resolve_against_active_root_not_process_cwd_ac17(self) -> None:
        """`git -C <active repo> push` を **非 GDD ディレクトリから** 実行しても、
        steering / tip / 証跡はすべて active root 基準で解決する（AC-17）。

        `PROJECT_ROOT` / `ACTIVE_ROOT` を `$PROCESS_CWD` で上書きする値置換型の
        変異は、プロセス cwd と active root が同じ fixture では観測できない。
        否定側（stale 証跡 → 不足として通知）と肯定側（一致 → 通す）を対で固定する。
        """
        for label, use_stale_evidence in (("stale-evidence", True), ("fresh-evidence", False)):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                outside = Path(tmp) / "outside"
                outside.mkdir()
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                stale_sha = self._head_sha(repo)
                head = self._commit_extra(repo, "feature.py")
                self._write_steering(
                    repo,
                    task_size="standard",
                    evidence=self._evidence_line(sha=stale_sha if use_stale_evidence else head),
                )

                result = self._run_hook(
                    outside,
                    f"git -C {repo} push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                if use_stale_evidence:
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                    self.assertIn("sha-mismatch", payload["hookSpecificOutput"]["additionalContext"])
                else:
                    self.assertEqual(result.stdout, "")

    # -- M-1 remediation: 短縮 sha 契約の一本化（lib の 7〜40 桁が正本）------

    def test_step11_short_evidence_sha_is_normalized_and_accepted_ac3(self) -> None:
        """`lib/self-review-evidence.sh` は証跡 sha を 7〜40 桁の hex で valid と
        するので、hook 側も比較前に full sha へ正規化する（M-1）。

        書式検証を通った短縮 sha が恒久 `sha-mismatch` になると、AC-3 の
        「証跡 sha を更新すれば通る」が成立せず復旧不能になる。
        """
        for label, width in (("short-7", 7), ("short-12", 12)):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                head = self._head_sha(repo)
                self._write_steering(
                    repo, task_size="standard", evidence=self._evidence_line(sha=head[:width])
                )

                result = self._run_hook(
                    repo,
                    "git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_step11_unresolvable_or_stale_short_sha_still_blocks(self) -> None:
        """正規化は fail-closed 側を緩めない（M-1 の否定側）。

        - repo 上で解決できない短縮 sha → 空文字に落ちて `sha-mismatch`
        - 解決はできるが tip ではない古いコミットの短縮 sha → `sha-mismatch`

        「両辺を tip へ正規化して常に一致させる」型の変異はここで殺される。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            stale_sha = self._head_sha(repo)
            self._commit_extra(repo, "feature.py")

            for label, evidence_sha in (
                ("unresolvable-short", "0000000"),
                ("stale-short", stale_sha[:12]),
            ):
                with self.subTest(case=label):
                    self._write_steering(
                        repo, task_size="standard", evidence=self._evidence_line(sha=evidence_sha)
                    )

                    result = self._run_hook(
                        repo,
                        "git push -u origin main",
                        extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                    )

                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                    self.assertIn("sha-mismatch", payload["hookSpecificOutput"]["additionalContext"])

    # -- Carry Forward A-4 / A-7（opt-out 受理面の明示）+ advisory L-1 -------

    def test_block_reasons_have_single_punctuation_and_state_optout_placement(self) -> None:
        """L-1: reason code の閉じ括弧の直後が `）。。` にならない（T-8 が出す
        2 種は単一句点で、T-9 の 4 種だけ二重になっていた非対称の解消）。

        A-4 / A-7: `bash -c` / `eval` 越しの opt-out が受理されないことは
        `missing-evidence` の reason に固定文言で明示する（design.md 128 行の
        「`git` の直前に置いてください」を補う。許可トークン集合の項目 1
        「固定メッセージカタログの文言」に収まる）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            head = self._head_sha(repo)

            cases: list[tuple[str, str, str | None]] = [
                ("refspec-ambiguous", "git push origin --all", self._evidence_line(sha=head)),
                ("missing-evidence", "git push -u origin main", None),
                (
                    "sha-mismatch",
                    "git push -u origin main",
                    self._evidence_line(sha="0123456789abcdef0123456789abcdef01234567"),
                ),
                (
                    "dry-not-reached",
                    "git push -u origin main",
                    self._evidence_line(sha=head, dry="no", consecutive_clean="0"),
                ),
            ]

            for reason_code, command, evidence in cases:
                with self.subTest(reason_code=reason_code):
                    self._write_steering(repo, task_size="standard", evidence=evidence)

                    result = self._run_hook(
                        repo,
                        command,
                        extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                    )

                    self.assertEqual(result.returncode, 0, result.stderr)
                    reason = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                    self.assertIn(f"reason code: {reason_code}）。書き込み先", reason)
                    self.assertNotIn("）。。", reason)
                    if reason_code == "missing-evidence":
                        self.assertIn("bash -c / eval 経由の opt-out は受理されません", reason)

    def test_logged_head_field_is_the_resolved_head_sha_ac19(self) -> None:
        """AC-19 のログ `head` は **解決した HEAD sha** そのものであること
        （design.md 187 行「`head` は呼び出し側が渡す HEAD sha」）。

        既存の opt-out / unresolved-steering の test は `event:` と `via:` /
        `reason:` しか見ておらず、解決済み `HEAD_SHA` を定数 `unknown` で
        上書きする値置換型の変異が生き残っていた（本 remediation の V10）。
        fail-open の母数を記録する唯一の行の中身なので、値まで固定する。
        """
        for label, extra_env_key in (("optout", "GDD_SKIP_PRE_PUSH_GATE"), ("unresolved", None)):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                head = self._head_sha(repo)
                state_dir = Path(tmp) / "hookstate"
                env = {"GDD_HOOK_STATE_DIR": str(state_dir)}
                if extra_env_key:
                    env[extra_env_key] = "1"

                result = self._run_hook(repo, "git push origin main", extra_env=env)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                log = (state_dir / "pre-push-optout.log").read_text(encoding="utf-8")
                expected_event = "event: optout" if extra_env_key else "event: unresolved-steering"
                self.assertIn(expected_event, log)
                self.assertIn(f"head: {head}", log)
                self.assertNotIn("head: unknown", log)

    # ---- T-13: Step 0 で未充足と確定した AC-17 の cwd surface（ADR-8）--------

    def test_cd_in_command_resolves_candidate_root_ac17(self) -> None:
        """AC-17 の優先順第 2 位「コマンド内 `cd`」経由の候補 root 解決。

        既存 `test_step7_to_11_resolve_against_active_root_not_process_cwd_ac17` は
        `git -C` 形だけを覆う。`resolve_candidate_roots` の
        `primary_root = dash_c_root or cd_root or payload_cwd or process_cwd` から
        `cd_root` の項を落とす変異は、`-C` 形の既存 test では観測できない
        （プロセス cwd を GDD 外にした状態で `cd` 経由でのみ active root へ到達する、
        この形でしか判別できない）。stale → 不足として通知 / fresh → 素通りの対で固定し、
        「常に不足として通知」「常に pass」への退行も同時に排除する。
        """
        for label, use_stale_evidence in (
            ("stale-evidence", True),
            ("fresh-evidence", False),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                outside = Path(tmp) / "outside"
                outside.mkdir()
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                stale_sha = self._head_sha(repo)
                head = self._commit_extra(repo, "feature.py")
                self._write_steering(
                    repo,
                    task_size="standard",
                    evidence=self._evidence_line(
                        sha=stale_sha if use_stale_evidence else head
                    ),
                )

                result = self._run_hook(
                    outside,
                    f"cd {repo} && git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                if use_stale_evidence:
                    self.assertEqual(self._decision(result), "notice")
                    self.assertIn("sha-mismatch", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])
                else:
                    self.assertIsNone(self._decision(result), result.stdout)

    def test_work_tree_flag_blocks_even_when_process_cwd_is_outside_gdd_ac17(self) -> None:
        """`--work-tree` を伴う push を、プロセス cwd が GDD 外の状態で実行しても
        不足として通知する（design.md § テスト方針が `--git-dir` と併記で名指し / AC-17 後段）。

        既存 `test_git_dir_flag_makes_root_unresolvable_and_blocks_when_active` は
        `--git-dir` 単独 + プロセス cwd が active repo 内。design.md が名指す**併記形**
        （`combined` subTest）だけでは `resolve_candidate_roots` の
        `token.startswith(("--git-dir", "--work-tree"))` から `--work-tree` だけを
        落とす変異を検出できない（`--git-dir` 側が単独で `unresolvable=True` と
        `extra_roots` への追加を担ってしまい、`--work-tree` の扱いが変わっても
        不足の通知への到達経路にも reason 文字列にも差が出ない — 隔離コピーでの実測で確認済み）。
        **`work-tree-only`** subTest で `--work-tree` を `--git-dir` から切り離し、
        「タプルに `--work-tree` が含まれているか」という判別を独立に固定する。
        """
        for label, command in (
            (
                "combined",
                "git --git-dir={repo}/.git --work-tree={repo} push -u origin main",
            ),
            ("work-tree-only", "git --work-tree={repo} push -u origin main"),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                outside = Path(tmp) / "outside"
                outside.mkdir()
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)

                result = self._run_hook(
                    outside,
                    command.format(repo=repo),
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self._decision(result), "notice", f"{label}: {result.stdout!r}")
                reason = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("unresolvable-root", reason)
                self._assert_block_reason_has_required_three_elements(reason)
                self.assertNotIn(str(repo), reason)

    # ---- T-14: Step 0 で未充足と確定した resolver / block reason surface（ADR-8）--

    def test_done_steering_still_blocks_missing_evidence_ac25(self) -> None:
        """`Next Action=done` の steering でも hook が不足の通知へ落ちる**配線層**（AC-25）。

        `gdd_pre_push_resolve_steering` の union 分岐（`Resume From == done ||
        Next Action == done`）は lib 単体テスト `tests/test_self_review_evidence.sh` の
        T6-2 / T6-3 で固定済みだが、**hook がその lib 結果を受けて不足の通知まで到達する
        配線**は既存のテストに 1 件も無い（`next_action` は `gdd-implementation-gating` /
        `gdd-design-gating` のみ）。post-completion PR flow（`Next Action=done` 確定後の
        push）は実運用で最頻の経路であり、ここが fail-open すると AC-1 の中心価値が
        経路依存で失われる。hook 側で done 系候補を捨てる変異（union の第 2 項を落とす／
        `Next Action == done` を非 active とみなして早期 exit する）は、この 2 fixture
        でしか観測できない。
        """
        for label, resume_from, next_action in (
            ("next-action-done-only", "gdd-implementation-gating", "done"),
            ("post-completion-shape", "done", "done"),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                self._write_steering(
                    repo,
                    resume_from=resume_from,
                    next_action=next_action,
                    task_size="standard",
                    evidence=None,
                )

                result = self._run_hook(
                    repo,
                    "git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self._decision(result), "notice", f"{label}: {result.stdout}")
                self.assertIn("missing-evidence", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def _hook_block_reason_codes(self) -> frozenset[str]:
        """block reason code 集合を hook ソースから**機械導出**する（AC-18）。

        テスト側に reason code の literal 一覧・件数を持たせない。実装へ新しい
        reason code が足されたら、その code を踏む fixture が `_block_reasons_by_code`
        に無い限り `test_every_ascii_token_in_block_reason_matches_allow_list_ac18`
        が落ちる（fail-closed）。`len(observed) == 5` のような件数 literal は
        6 種目の欠落を構造的に検出できず、実際に `optout-log-write-failed` への
        漏洩が全 suite を素通りした（T-14 Attempt 1 の M-1）。

        導出そのものは `_block_reason_support` が `hooks/scripts/*.sh` を全走査して
        行い、ここは **本 hook のぶんだけ** を取り出す。走査を 1 本の hook に閉じて
        いたことが、pre-PR gate の 2 code をどの機械検査にも掛けないまま通した
        原因だった（T-15 Attempt 1 の M-1）。hook 横断の充足は
        `tests/test_hook_block_reason_recovery_contract.py` が担う。
        """
        return support.reason_codes_by_hook()[HOOK]

    def _block_reasons_by_code(self) -> list[support.BlockReasonSample]:
        """到達可能な block reason を reason code ごとに 1 本ずつ集める（AC-18 用）。

        `state_dir` は `"dir"`（正常な hook state ディレクトリ）と `"file"`（既存
        ファイルへ向けて `mkdir -p` を失敗させ opt-out ログ追記を失敗させる）の
        2 種。後者が `optout-log-write-failed` の唯一の到達経路。

        hook 横断 contract（`test_hook_block_reason_recovery_contract.py`）から
        provider として呼ばれるため、否定側検査用の実測値（一時 repo の絶対パスと
        steering slug）も一緒に返す。
        """
        reasons: list[support.BlockReasonSample] = []
        for label, evidence_kind, state_dir_kind, command in (
            ("unresolvable-root", "none", "dir", "git --git-dir={repo}/.git push origin main"),
            ("refspec-ambiguous", "fresh", "dir", "git push --all origin"),
            ("missing-evidence", "none", "dir", "git push -u origin main"),
            ("sha-mismatch", "stale", "dir", "git push -u origin main"),
            ("dry-not-reached", "dry-no", "dir", "git push -u origin main"),
            ("independent-review-missing", "ir-none", "dir", "git push -u origin main"),
            ("independent-review-stale", "ir-stale", "dir", "git push -u origin main"),
            ("independent-review-high", "ir-high", "dir", "git push -u origin main"),
            ("steering-multiple", "multi-terminal", "dir", "git push -u origin main"),
            ("steering-unreadable", "symlink-entry", "dir", "git push -u origin main"),
            (
                "optout-log-write-failed",
                "fresh",
                "file",
                "GDD_SKIP_PRE_PUSH_GATE=1 git push -u origin main",
            ),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                stale = self._head_sha(repo)
                head = self._commit_extra(repo, "feature.py")
                evidence = {
                    "none": None,
                    "fresh": self._evidence_line(sha=head),
                    "stale": self._evidence_line(sha=stale),
                    "dry-no": self._evidence_line(sha=head, dry="no", consecutive_clean="0"),
                }.get(evidence_kind, self._evidence_line(sha=head))
                # step 13b の 3 code は、self-review 証跡が step 13 まで通った
                # うえで `Independent Review` 行だけが壊れているときに到達する。
                ir_kwargs: dict[str, object] = {
                    "ir-none": {"auto_independent_review": False},
                    "ir-stale": {"independent_review": self._independent_review_line(sha=stale)},
                    "ir-high": {
                        "independent_review": self._independent_review_line(sha=head, high="3")
                    },
                }.get(evidence_kind, {})
                self._write_steering(
                    repo, task_size="standard", evidence=evidence, **ir_kwargs  # type: ignore[arg-type]
                )
                # 終端の steering が 2 件で 1 つに決まらない形（step 7 の不足の通知）。
                if evidence_kind == "multi-terminal":
                    for slug in (DEFAULT_STEERING_SLUG, "20260816-other"):
                        self._write_steering(repo, slug=slug, resume_from="done", next_action="done")
                # steering の列挙から落ちる symlink の entry がある形（step 7 の不足の通知）。
                if evidence_kind == "symlink-entry":
                    (repo / ".steering" / "20260816-link").symlink_to(
                        repo / ".steering" / DEFAULT_STEERING_SLUG
                    )

                state_dir = Path(tmp) / "hookstate"
                if state_dir_kind == "file":
                    state_dir.write_text("occupied", encoding="utf-8")

                result = self._run_hook(
                    repo,
                    command.format(repo=repo),
                    extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
                )
                self.assertEqual(self._decision(result), "notice", f"{label}: {result.stdout}")
                reason = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn(label, reason, f"{label} を踏めていない: {reason}")
                reasons.append(
                    support.BlockReasonSample(
                        code=label,
                        reason=reason,
                        forbidden=(str(repo), DEFAULT_STEERING_SLUG),
                    )
                )
        return reasons

    def test_every_ascii_token_in_block_reason_matches_allow_list_ac18(self) -> None:
        """AC-18: reason を token 化し、全 token が許可文法に一致することの機械検証。

        既存 `test_step7_to_13_block_reasons_include_required_three_elements_and_no_slug_leak`
        は「3 要素が在る」（肯定側）と「slug / 絶対パスが無い」（否定側の**列挙**）まで。
        列挙していない漏洩 — remote 名（`origin`）/ branch 名（`main`）/ refspec /
        URL（`https`）/ 絶対パス片（`Users` / `tmp`）を reason へ補間する変異 — は
        否定リスト方式では生き残る。allow-list は列挙漏れが fail-closed 側に倒れる。

        **`allowed` を後から緩めない**: 実装側が新しい語を reason に足したら、まず
        design.md § block reason の許可トークン集合 1〜6 のどれに属するかを判定し、
        属さないなら**実装側を直す**。テストの集合へ無条件に追記するのは AC-18 の空洞化。
        """
        allowed, sha_re, token_re = AC18_ALLOWED_TOKENS, AC18_SHA_RE, AC18_TOKEN_RE

        derived = self._hook_block_reason_codes()
        # reason code は allow-list 集合 2 そのもの。実装へ code を足して allow-list を
        # 更新し忘れた場合も fail-closed にする。
        self.assertEqual(
            sorted(derived - allowed), [], f"allow-list に無い reason code: {derived - allowed}"
        )

        observed = set()
        for sample in self._block_reasons_by_code():
            label, reason = sample.code, sample.reason
            observed.add(label)
            # 肯定側（3 要素が在る）と否定側（許可外 token が無い）を**同じ集合の上で**
            # 閉じる。従来は肯定側が別 test 2 本に分散し、`optout-log-write-failed` は
            # どちらにも入っていなかった。
            self._assert_block_reason_has_required_three_elements(reason)
            unknown = [
                token
                for token in token_re.findall(reason)
                if token not in allowed and not sha_re.match(token)
            ]
            self.assertEqual(unknown, [], f"{label}: 許可外 token {unknown} / reason={reason}")
        # hook ソースから導出した reason code 集合と完全一致すること。fixture が 1 経路へ
        # 縮退する退行も、実装に足された新 code の fixture 漏れも、ここで落ちる。
        self.assertEqual(
            observed,
            set(derived),
            f"fixture 未到達の reason code: {set(derived) - observed} / "
            f"実装に無い label: {observed - set(derived)}",
        )


class PrePushGateWiringContractTests(unittest.TestCase):
    """`hooks/hooks.json` の配線面そのものを固定する回帰ガード（T-10 remediation）。

    本ファイルの他の test はすべて hook script を直接叩くため、`hooks.json` を
    一度も開かず、**配線面に対する判別力が構造的にゼロ**だった。
    `tests/checks/hooks-wiring-lint.sh` も全 event / 全 matcher を平坦走査して
    script 名の出現有無しか見ないため、「lint 上は wired だが `Bash` tool 呼び出しで
    一度も起動しない」状態（event 移設 / matcher 差し替え / 大小文字ずれ）を
    素通しする。それは T-10 が閉じるべき残差そのもの（AC-1 / AC-25 が本番で
    無言のまま fail-open する形）なので、ここで assert する。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))

    def _pre_tool_use_entries(self) -> list[dict]:
        return self.config["hooks"]["PreToolUse"]

    def _wired_hooks(self) -> list[tuple[str, object, dict]]:
        """`(event, matcher, hook)` の形で配線箇所を全列挙する。"""
        found = []
        for event, entries in self.config["hooks"].items():
            for entry in entries:
                for hook in entry.get("hooks", []):
                    if HOOK_SCRIPT_NAME in hook.get("command", ""):
                        found.append((event, entry.get("matcher"), hook))
        return found

    def test_wired_exactly_once_into_pre_tool_use_bash_matcher(self) -> None:
        """`PreToolUse` の `matcher == "Bash"` エントリに 1 度だけ収録されること。

        `Bash` 以外の matcher（`Skill` 等）・別 event（`SessionStart` 等）・
        大小文字違い（`bash`）への移設は、いずれも `git push` 経路で hook が
        起動しなくなるため fail させる。
        """
        wired = self._wired_hooks()
        self.assertEqual(
            [(event, matcher) for event, matcher, _ in wired],
            [("PreToolUse", "Bash")],
            f"{HOOK_SCRIPT_NAME} は PreToolUse の matcher='Bash' エントリに"
            f" 1 度だけ配線されている必要がある: {[(e, m) for e, m, _ in wired]}",
        )

    def test_wired_timeout_has_headroom(self) -> None:
        """`timeout` を縮めると遅い環境で fail-open するため下限を固定する。"""
        wired = self._wired_hooks()
        self.assertTrue(wired, f"{HOOK_SCRIPT_NAME} が hooks.json から参照されていない")
        for event, matcher, hook in wired:
            with self.subTest(event=event, matcher=matcher):
                self.assertGreaterEqual(
                    hook.get("timeout", 0),
                    MIN_HOOK_TIMEOUT_SECONDS,
                    f"timeout は {MIN_HOOK_TIMEOUT_SECONDS} 秒以上（実 push 経路の平均に対する余裕）",
                )

    def test_description_hook_count_matches_actual_pre_tool_use_wiring(self) -> None:
        """`description` の hook 本数記述と実際の配線本数の自己整合。

        本数は `hooks.json` から機械導出し、テスト側に literal を持たない。
        """
        count = sum(len(entry.get("hooks", [])) for entry in self._pre_tool_use_entries())
        description = self.config["description"]
        self.assertIn(
            f"PreToolUse has {_NUMBER_WORDS[count]} hooks",
            description,
            f"description の hook 本数が実際の PreToolUse 配線数 {count} と不整合",
        )
        self.assertEqual(
            sorted(int(n) for n in re.findall(r"\((\d+)\)", description)),
            list(range(1, count + 1)),
            f"description の列挙 (1)〜({count}) に欠番・余剰がある",
        )


def _collect_pre_push_block_reason_samples() -> list[support.BlockReasonSample]:
    """hook 横断 contract 用の fixture provider（`_block_reasons_by_code` の再利用）。

    fixture を provider 側へ複製すると、本ファイルの allow-list 検査と hook 横断検査で
    2 つの正本ができる。TestCase を 1 個作って既存 helper をそのまま呼ぶ。
    """
    case = PrePushGateContractTests("test_every_ascii_token_in_block_reason_matches_allow_list_ac18")
    return case._block_reasons_by_code()


support.register_block_reason_provider(HOOK, _collect_pre_push_block_reason_samples)


if __name__ == "__main__":
    unittest.main()
