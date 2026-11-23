"""pre-push gate の escape hatch（opt-out, AC-4）と、その記録の契約テスト。

fixture は `_pre_push_gate_support.PrePushGateFixtureMixin` にある。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _pre_push_gate_support import PrePushGateFixtureMixin
from _timing_budget import hang_guard_seconds

PRE_PUSH_HANG_GUARD = hang_guard_seconds("run-pre-push-gate-hook.sh")


class PrePushGateOptoutContractTests(PrePushGateFixtureMixin, unittest.TestCase):
    # ---- AC-4: escape hatch（opt-out） ---------------------------------------

    def test_optout_via_process_env_accepted_logs_and_exits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
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
            log = (state_dir / "pre-push-optout.log").read_text(encoding="utf-8")
            self.assertIn("event: optout", log)
            self.assertIn("via: process-env", log)

    def test_optout_via_command_prefix_accepted_logs_and_exits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            log = (state_dir / "pre-push-optout.log").read_text(encoding="utf-8")
            self.assertIn("event: optout", log)
            self.assertIn("via: command-prefix", log)

    def test_optout_prefix_not_at_command_start_is_rejected(self) -> None:
        """design.md 120 行の非受理の例: `echo GDD_SKIP_PRE_PUSH_GATE=1 git push` は
        コマンド先頭でないため非受理。T-8 単体では他に不足の材料が無いため push 自体は
        通過してしまう（AC-1 の完成は T-9）が、optout ログに `event: optout` が
        誤って書かれないことは T-8 の責務として固定する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                "echo GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            logfile = state_dir / "pre-push-optout.log"
            if logfile.exists():
                self.assertNotIn("event: optout", logfile.read_text(encoding="utf-8"))

    def test_optout_via_nested_shell_with_leading_noop_is_rejected_a11(self) -> None:
        """A-11 決着の discriminating test（mutation で判別力を実測確認済み）。

        `find_optout` へ渡す opt-out 境界値を `tokenize_with_boundary` の
        raw_count（展開前の原文 token 数）ではなく `len(tokens)`（展開後の全長）に
        すると、`bash -c 'true; GDD_SKIP_PRE_PUSH_GATE=1 git push'` のような
        「nested shell の中で無害な先行コマンドの直後に opt-out を置く」形が
        誤って受理される（実測: boundary=len(tokens) だと accepted=True、
        boundary=raw_count だと accepted=False）。opt-out ログに `event: optout`
        が書かれないことを固定し、この回帰を機械的に検出する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                "bash -c 'true; GDD_SKIP_PRE_PUSH_GATE=1 git push origin main'",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            logfile = state_dir / "pre-push-optout.log"
            if logfile.exists():
                self.assertNotIn("event: optout", logfile.read_text(encoding="utf-8"))

    def test_optout_log_append_failure_blocks_ac4(self) -> None:
        """opt-out append 失敗時は受理せず不足として通知する（design.md 189 行 / AC-4 後半）。

        `GDD_HOOK_STATE_DIR` を（ディレクトリではなく）既存ファイルへ向けることで
        `mkdir -p` を失敗させ、append 失敗を再現する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            blocked_path = Path(tmp) / "not-a-directory"
            blocked_path.write_text("occupied", encoding="utf-8")

            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(blocked_path)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("optout-log-write-failed", payload["hookSpecificOutput"]["additionalContext"])

    def test_optout_log_blocks_when_home_unset(self) -> None:
        """`HOME` と `GDD_HOOK_STATE_DIR` の双方が未設定でも fail-closed で不足として通知する
        （requirements.md AC-1 / design.md § テスト方針）。

        修正前は `gdd_sr_log_event` が `${HOME}` の展開で `set -u` 即死し、hook は
        rc=1 / stdout 空のまま終わる（不足の通知を出せず無記録で通る）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)

            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
                drop_env=("HOME", "GDD_HOOK_STATE_DIR"),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("optout-log-write-failed", payload["hookSpecificOutput"]["additionalContext"])
            # stderr に `unbound variable` が出ないことは **ここでは検査しない**。
            # 呼び出し側（run-pre-push-gate-hook.sh:151）が `2>/dev/null` を持つため、
            # 仮に helper が即死しても stderr は握り潰され、assertion が構造上 RED に
            # ならない（= 常に成功する検証）。stderr 汚染の判別は `2>/dev/null` を
            # 持たない 118 / 163 行を踏む test_fail_open_paths_are_quiet_when_home_unset
            # （AC-4）が担う。

    def test_log_event_returns_one_for_optout_when_state_dir_unresolvable(self) -> None:
        """`gdd_sr_log_event` を `HOME` / `GDD_HOOK_STATE_DIR` 双方未設定・`set -u` 有効で
        直接呼ぶと、シェルを落とさず `optout` は戻り値 1 を返す（requirements.md AC-2 / design.md § AC-2 harness
        の必須規約。`set -u` を落とすと修正前でも通ってしまい判別力が消える）。
        """
        env = {k: v for k, v in os.environ.items() if k not in ("HOME", "GDD_HOOK_STATE_DIR")}
        lib_path = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "self-review-evidence.sh"
        script = (
            f'source "{lib_path}"\n'
            'if gdd_sr_log_event "optout" "-" "/tmp/x" "deadbeef" "process-env"; '
            'then echo "RC=0"; else echo "RC=$?"; fi\n'
        )
        result = subprocess.run(
            ["bash", "-uo", "pipefail", "-c", script],
            capture_output=True, text=True, env=env, timeout=PRE_PUSH_HANG_GUARD,
        )

        _diag = f"stdout={result.stdout!r} stderr={result.stderr!r}"
        self.assertEqual(result.returncode, 0, _diag)
        # 部分文字列一致だと `RC=127`（コマンド不在）等も `RC=1` を含んで通ってしまうため、
        # stdout 全体との完全一致で締める。失敗時は stdout / stderr 双方を message に載せる。
        self.assertEqual(result.stdout.strip(), "RC=1", _diag)
        self.assertNotIn("unbound variable", result.stderr)

    def test_log_event_returns_zero_for_non_optout_when_state_dir_unresolvable(self) -> None:
        """`optout` 以外の event（例: `hook-error`）は同条件で戻り値 0（best-effort）を
        返す。`lib/self-review-evidence.sh:511-515` の既存非対称契約が `HOME` 未設定時にも成立することを
        固定する（AC-2 後半）。
        """
        env = {k: v for k, v in os.environ.items() if k not in ("HOME", "GDD_HOOK_STATE_DIR")}
        lib_path = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "self-review-evidence.sh"
        script = (
            f'source "{lib_path}"\n'
            'if gdd_sr_log_event "hook-error" "-" "/tmp/x" "deadbeef" "-"; '
            'then echo "RC=0"; else echo "RC=$?"; fi\n'
        )
        result = subprocess.run(
            ["bash", "-uo", "pipefail", "-c", script],
            capture_output=True, text=True, env=env, timeout=PRE_PUSH_HANG_GUARD,
        )

        _diag = f"stdout={result.stdout!r} stderr={result.stderr!r}"
        self.assertEqual(result.returncode, 0, _diag)
        self.assertEqual(result.stdout.strip(), "RC=0", _diag)
        self.assertNotIn("unbound variable", result.stderr)

    def test_fail_open_paths_are_quiet_when_home_unset(self) -> None:
        """fail-open が意図された 2 経路（session-mismatch / unresolved-steering）は
        `HOME` 未設定でも rc=0 / stdout 空で通り、stderr に `unbound variable` を
        出さない（design.md § AC-4。118 行・163 行は `2>/dev/null` を持たないため、
        helper の即死がここでは stderr に直接現れる）。
        """
        with self.subTest(path="session-mismatch"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True, session_id="another-session")

                result = self._run_hook(
                    repo,
                    "git push origin main",
                    drop_env=("HOME", "GDD_HOOK_STATE_DIR"),
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("unbound variable", result.stderr)

        with self.subTest(path="unresolved-steering"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)

                result = self._run_hook(
                    repo,
                    "git push origin main",
                    drop_env=("HOME", "GDD_HOOK_STATE_DIR"),
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("unbound variable", result.stderr)

    def test_optout_log_format_unchanged_when_state_dir_writable(self) -> None:
        """`GDD_HOOK_STATE_DIR` が書き込み可能なとき、ログ書式は修正前後で変わらない
        （design.md § AC-3。非回帰の基準線）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            state_dir = Path(tmp) / "hookstate"
            head_sha = self._head_sha(repo)

            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            lines = [
                line
                for line in (state_dir / "pre-push-optout.log").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(lines), 1, lines)
            self.assertRegex(
                lines[0],
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \| event: optout \| "
                r"reason: - \| repo: [0-9a-f]{8} \| head: "
                + re.escape(head_sha)
                + r" \| via: command-prefix$",
            )

    def test_optout_log_written_under_home_when_state_dir_unset(self) -> None:
        """`GDD_HOOK_STATE_DIR` 未設定・`HOME` のみ設定（実運用の既定）では
        `${HOME}/.claude/.gdd-hook-state/pre-push-optout.log` に記録される
        （design.md § AC-8。Approach B が書き換える分岐そのもの）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            home_dir = Path(tmp) / "home"
            home_dir.mkdir()

            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
                extra_env={"HOME": str(home_dir)},
                drop_env=("GDD_HOOK_STATE_DIR",),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            logfile = home_dir / ".claude" / ".gdd-hook-state" / "pre-push-optout.log"
            lines = [
                line for line in logfile.read_text(encoding="utf-8").splitlines() if line.strip()
            ]
            self.assertEqual(len(lines), 1, lines)
            self.assertIn("event: optout", lines[0])

    # ---- T-12: Step 0 で未充足と確定した opt-out surface（ADR-8）------------

    def _active_repo_without_evidence(self, tmp: Path) -> Path:
        """active GDD かつ証跡なし = opt-out が効かなければ必ず不足として通知する足場。

        肯定側テストを「不足として通知されないこと」で観測できるようにするための fixture
        （証跡ありだと opt-out 判定を消しても素通りしてしまい、肯定側の assertion が
        判別力を失う）。
        """
        repo = tmp / "repo"
        repo.mkdir()
        self._init_repo(repo)
        self._write_local_state(repo, active=True)
        self._write_steering(repo, task_size="standard", evidence=None)
        return repo

    def test_optout_prefix_whose_adjacent_git_is_not_the_push_is_rejected_ac4(self) -> None:
        """代入列は**コマンド先頭**にあるが、直後の git が push を担っていない形。

        design.md §opt-out 受理面の機械定義 item 2 の中心。既存の否定側 2 test は
        `echo` 前置(コマンド先頭でない)と `bash -c` 展開(展開由来)だけを覆い、
        「先頭かつ展開由来でないが adjacency が偽」という分岐は未固定だった。
        `find_optout` の adjacency 判定を「代入列がどこかにあれば受理」へ緩める変異は、
        この形でしか観測できない。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._active_repo_without_evidence(Path(tmp))
            state_dir = Path(tmp) / "hookstate"

            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git rev-parse HEAD && git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self._decision(result), "notice")
            self.assertIn("missing-evidence", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])
            logfile = state_dir / "pre-push-optout.log"
            if logfile.exists():
                self.assertNotIn("event: optout", logfile.read_text(encoding="utf-8"))

    def test_optout_accepted_forms_named_by_design_ac4(self) -> None:
        """design.md § テスト方針 の opt-out 肯定側リストのうち、既存のテストが
        覆っていない 3 形（`env` 前置 / `git` の絶対パス / 行継続を挟んだ同形）。

        それぞれ別の分岐を叩く: `env` は `find_optout` の `token != "env"` スキップ、
        `/usr/bin/git` は `is_git_push` の `os.path.basename` 照合、行継続は `_lex` が
        `\\` + 改行を **token を残さず**除去する規約(ADR-5 / ADR-6)。行継続を
        `NEWLINE_TOKEN` に変える変異はコマンドの切れ目とみなされて受理されなくなるため、
        この 3 形は素の command-prefix 形と判別力が異なる。
        """
        for label, command in (
            ("env-prefix", "env GDD_SKIP_PRE_PUSH_GATE=1 git push -u origin main"),
            ("absolute-git", "GDD_SKIP_PRE_PUSH_GATE=1 /usr/bin/git push -u origin main"),
            ("line-continuation", "GDD_SKIP_PRE_PUSH_GATE=1 \\\n    git push -u origin main"),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = self._active_repo_without_evidence(Path(tmp))
                state_dir = Path(tmp) / "hookstate"

                result = self._run_hook(
                    repo, command, extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)}
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                # 証跡が無いので、opt-out が受理されなければ必ず不足として通知される
                self.assertIsNone(self._decision(result), f"{label}: {result.stdout}")
                log = (state_dir / "pre-push-optout.log").read_text(encoding="utf-8")
                self.assertIn("event: optout", log)
                self.assertIn("via: command-prefix", log)
                self.assertIn(f"head: {self._head_sha(repo)}", log)

    def test_optout_rejected_unless_value_and_var_name_match_exactly_ac4(self) -> None:
        """AC-4 本文が名指しする受理条件「`GDD_SKIP_PRE_PUSH_GATE` が **`1`**」の
        2 次元（値の厳密性 / 変数名の完全一致）を両経路で固定する。

        impl-gate の指摘: 既存のテストと、あとから足した 2 test はいずれも「代入列の
        位置・由来」と「受理されるべき形」だけを見ており、この 2 次元を壊す変異は
        **全 test を素通り**していた。代表例は (a) `token == f"{_OPTOUT_VAR}=1"`
        → `token.startswith(f"{_OPTOUT_VAR}=")`（`GDD_SKIP_PRE_PUSH_GATE=0 git push`
        でも opt-out 成立）(b) hook 側 `[[ "${GDD_SKIP_PRE_PUSH_GATE:-}" == "1" ]]`
        → `[[ -n ... ]]`（process-env 経路で任意の非空値が成立）。いずれも escape
        hatch の受理面が silent に広がる fail-open 方向で、`Human Recheck Boundary`
        が人間判断事項として名指しする境界に検知機構が無い状態だった。

        証跡なしの active repo を足場にしているので、誤って受理されると不足の通知が
        消えて `_decision` が `None` になり、この test だけが FAIL する。
        """
        cases = (
            # (label, command, process env に渡す値。None = 空文字で無効化)
            # --- 値の厳密性（command-prefix 経路）: `=1` 以外は不受理 ---
            ("prefix-value-zero", "GDD_SKIP_PRE_PUSH_GATE=0 git push -u origin main", None),
            ("prefix-value-true", "GDD_SKIP_PRE_PUSH_GATE=true git push -u origin main", None),
            ("prefix-value-ten", "GDD_SKIP_PRE_PUSH_GATE=10 git push -u origin main", None),
            ("prefix-value-empty", "GDD_SKIP_PRE_PUSH_GATE= git push -u origin main", None),
            ("prefix-value-absent", "GDD_SKIP_PRE_PUSH_GATE git push -u origin main", None),
            # --- 変数名の完全一致（command-prefix 経路）: 近傍名は不受理 ---
            ("prefix-var-suffixed", "GDD_SKIP_PRE_PUSH_GATE_X=1 git push -u origin main", None),
            ("prefix-var-prefixed", "MY_GDD_SKIP_PRE_PUSH_GATE=1 git push -u origin main", None),
            # --- 値の厳密性（process-env 経路）: `-n` 化を KILL する非空値を含む ---
            ("process-env-zero", "git push -u origin main", "0"),
            ("process-env-true", "git push -u origin main", "true"),
            ("process-env-ten", "git push -u origin main", "10"),
            ("process-env-empty", "git push -u origin main", ""),
        )
        for label, command, env_value in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                repo = self._active_repo_without_evidence(Path(tmp))
                state_dir = Path(tmp) / "hookstate"

                result = self._run_hook(
                    repo,
                    command,
                    extra_env={
                        "GDD_HOOK_STATE_DIR": str(state_dir),
                        # 呼び出し元シェルの汚染を排除する（値の厳密性を見る test のため、
                        # process-env 経路の値は常にこの test が決める）
                        "GDD_SKIP_PRE_PUSH_GATE": "" if env_value is None else env_value,
                    },
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    self._decision(result), "notice", f"{label}: {result.stdout!r}"
                )
                self.assertIn("missing-evidence", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])
                logfile = state_dir / "pre-push-optout.log"
                if logfile.exists():
                    self.assertNotIn(
                        "event: optout", logfile.read_text(encoding="utf-8"), label
                    )


if __name__ == "__main__":
    unittest.main()
