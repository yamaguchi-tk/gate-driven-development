"""pre-push gate の起動の短絡と active GDD の判定（step 1〜6、CT-1・AC-17・AC-19）の契約テスト。

kill-switch・payload の短絡・push の検出・候補 root の列挙・active の判定・session の
不一致を扱う。fixture は `_pre_push_gate_support.PrePushGateFixtureMixin` にある。
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _pre_push_gate_support import PrePushGateFixtureMixin


class PrePushGateActivationContractTests(PrePushGateFixtureMixin, unittest.TestCase):
    # ---- CT-1 / AC-2: GDD 外・非 push・kill-switch では無反応 ----------------

    def test_kill_switch_active_short_circuits_before_any_parsing(self) -> None:
        """kill-switch が有効なら push payload でも一切パースせず exit 0・無出力。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            home = Path(tmp) / "home"
            (home / ".claude").mkdir(parents=True)
            (home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")

            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
                extra_env={"HOME": str(home), "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            # kill-switch は「判定を一切走らせない」契約なので、副作用（ログ）も
            # 残ってはならない。rc/stdout だけを見ると `gdd_kill_switch_active && true`
            # のような無効化変異が opt-out ログを書きながら生存する。
            self.assertFalse((Path(tmp) / "hookstate" / "pre-push-optout.log").exists())

    def test_payload_without_push_keyword_short_circuits(self) -> None:
        """payload に `push` が含まれなければ token 化にすら進まず exit 0（最優先短絡）。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                "git status",
                extra_env={
                    "GDD_SKIP_PRE_PUSH_GATE": "1",
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertFalse((state_dir / "pre-push-optout.log").exists())

    def test_non_git_push_command_containing_push_word_exits_quietly(self) -> None:
        """`push` を含むが `is_git_push` が False のコマンドは exit 0・無出力・**無記録**。

        active repo かつ `GDD_SKIP_PRE_PUSH_GATE=1` が env にある形も併せて固定する。
        `is_push` を常時 true にする変異（= あらゆる `push` 語を含む Bash 呼び出しを
        gate 対象にする誤爆方向）は、この env 付きケースでのみ opt-out ログという
        観測可能な副作用として現れる。
        """
        for label, extra in (
            ("plain", {}),
            ("optout-env", {"GDD_SKIP_PRE_PUSH_GATE": "1"}),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                state_dir = Path(tmp) / "hookstate"
                env: dict[str, str] = {"GDD_HOOK_STATE_DIR": str(state_dir)}
                env.update(extra)

                result = self._run_hook(repo, "echo pushing artifact to s3", extra_env=env)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertFalse((state_dir / "pre-push-optout.log").exists())

    def test_no_active_steering_anywhere_exits_silently_ct1(self) -> None:
        """CT-1: どの候補 root にも active marker が無ければ exit 0・無出力・無記録。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            # .claude/gdd-dev.local.md を書かない = active marker なし
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo, "git push origin main", extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)}
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertFalse((state_dir / "pre-push-optout.log").exists())

    def test_active_marker_false_treated_as_non_active(self) -> None:
        """`active: false` の marker は非 active 扱い（exit 0・無出力）。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo, active=False)

            result = self._run_hook(
                repo,
                "git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    # ---- AC-19 / CT-1: 非 active では観測可能な副作用がゼロであること ----------
    #
    # T-8 の active 側で観測できる出力は「optout ログ」「session-mismatch ログ」
    # 「不足の通知（systemMessage・additionalContext）」の 3 つしかない。`rc == 0` + `stdout == ""` だけを見る assertion は
    # 「active 判定を消す」「active を過大マッチする」方向の変異を素通りさせるため、
    # 以下では **ログ不在**（= 副作用ゼロ）を第一級の契約として固定する。

    def test_non_active_repo_leaves_no_log_even_with_optout_ac19(self) -> None:
        """非 active repo では opt-out 付き push でも一切記録しない（AC-19）。

        `[[ "$ANY_ACTIVE" == "true" ]] || exit 0` を削除する変異、および
        `grep -q '^active: true'` を `grep -q 'active'` へ緩める変異は、いずれも
        「非 active なのに step 6 の opt-out ログを書く」形で現れる。marker 無しと
        `active: false` の 2 形の両方で観測可能な副作用ゼロを固定する。
        """
        for label, write_marker in (("no-marker", False), ("active-false", True)):
            with self.subTest(marker=label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                if write_marker:
                    self._write_local_state(repo, active=False)
                state_dir = Path(tmp) / "hookstate"

                result = self._run_hook(
                    repo,
                    "git push origin main",
                    extra_env={
                        "GDD_SKIP_PRE_PUSH_GATE": "1",
                        "GDD_HOOK_STATE_DIR": str(state_dir),
                    },
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertFalse((state_dir / "pre-push-optout.log").exists())

    def test_non_active_repo_git_dir_push_is_not_blocked_ct1(self) -> None:
        """非 active repo への `--git-dir` push は不足として通知しない（AC-2 / CT-1 の誤爆防止）。

        unresolvable-root の不足の通知を active 判定の**上**へ前倒しする変異は、GDD 外の
        repo に対する `--git-dir` push を不足として通知する = 誤爆方向の regression になる。
        design.md 90〜93 行の「非 active ならまず exit 0、active のときだけ不足として通知」
        という順序をここで固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            # marker を書かない = GDD 外の repo
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                f"git --git-dir={repo}/.git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertFalse((state_dir / "pre-push-optout.log").exists())

    def test_optout_does_not_rescue_unresolvable_root_when_active(self) -> None:
        """active repo では opt-out があっても unresolvable-root の不足の通知が優先される。

        step 6（escape hatch）を step 5 の不足の通知より上へ動かす変異は、opt-out を
        付けるだけで `--git-dir` push が通ってしまう fail-open を生む。design.md
        90〜93 行の step 5 → step 6 の順序を固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                f"GDD_SKIP_PRE_PUSH_GATE=1 git --git-dir={repo}/.git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("unresolvable-root", payload["hookSpecificOutput"]["additionalContext"])
            self.assertFalse((state_dir / "pre-push-optout.log").exists())

    def test_session_id_mismatch_passes_and_logs_once(self) -> None:
        """session continuity 不一致は通すが `event: session-mismatch` を 1 行残す。

        design.md 94 行「不足として通知しない。誤爆コストを増やさずに fail-open の母数を
        可視化する」の唯一の観測手段。ログ呼び出しを削除する変異は `rc == 0` +
        `stdout == ""` の assertion だけでは生存する（L-20）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True, session_id="another-session")
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                "git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            lines = [
                line
                for line in (state_dir / "pre-push-optout.log")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(len(lines), 1, lines)
            self.assertIn("event: session-mismatch", lines[0])
            # session 不一致は step 5 で抜けるため、opt-out 判定へは進まない
            self.assertNotIn("event: optout", lines[0])

    # ---- AC-17（コード上は T-8 draft に同居。design.md §判定順 step 4-5 前倒し）--

    def test_git_dir_flag_makes_root_unresolvable_and_blocks_when_active(self) -> None:
        """`--git-dir` を伴う push は候補 root に加えつつ「解釈不能」とし、
        いずれかの候補が active なら不足として通知する（design.md 90 行 / 旧 step 8 前倒し）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)

            result = self._run_hook(
                repo,
                f"git --git-dir={repo}/.git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("unresolvable-root", payload["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
