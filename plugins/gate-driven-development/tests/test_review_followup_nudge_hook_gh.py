"""review-followup nudge hook の `gh` の呼び出し・結果の分類・cache の契約テスト。

`hooks/scripts/run-review-followup-nudge-hook.sh` が `gh pr view` の結果（OPEN・MERGED・
PR なし・エラー・timeout・想定外の出力）を分類すること、`gh` の解決と timeout・子プロセスの
後始末、PR の有無の cache（命中・権限・壊れた日付・未来の日付）を測る。
`test_review_followup_nudge_hook.py` から分けた。fixture は `_review_followup_nudge_support.py`
の `ReviewFollowupNudgeFixtureMixin` にある。
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _timing_budget import hook_timeout_seconds
from _review_followup_nudge_support import (
    _hash8,
    HANG_GUARD,
    HOOK,
    _write_stub_gh,
    ReviewFollowupNudgeFixtureMixin,
)


class ReviewFollowupNudgeGhTests(ReviewFollowupNudgeFixtureMixin, unittest.TestCase):
    def test_gh_error_is_recorded_as_undeterminable_not_no_pr(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="error")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            log_file = state_dir / "review-followup-nudge.log"
            self.assertTrue(log_file.exists())
            self.assertIn("event: undeterminable", log_file.read_text(encoding="utf-8"))

    def test_gh_timeout_is_recorded_as_undeterminable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="hang")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    "GDD_REVIEW_FOLLOWUP_GH_TIMEOUT": "1",
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            log_file = state_dir / "review-followup-nudge.log"
            self.assertIn("event: undeterminable", log_file.read_text(encoding="utf-8"))
            self.assertIn("gh-timeout", log_file.read_text(encoding="utf-8"))

    def test_cache_hit_does_not_reinvoke_gh(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            extra_env = {
                "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                "GDD_REVIEW_FOLLOWUP_PR_CACHE_TTL": "300",
            }
            r1 = self._run_hook(repo, "git push origin feature-x", extra_env=extra_env)
            r2 = self._run_hook(repo, "git push origin feature-x", extra_env=extra_env)
            self.assertEqual(r1.returncode, 0, r1.stderr)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertIn("additionalContext", r1.stdout)
            self.assertIn("additionalContext", r2.stdout)
            calls = counter.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(calls), 1, f"gh should only be invoked once, calls={calls}")

    def test_alternate_gh_no_pr_phrasing_is_not_misread_as_error(self) -> None:
        """gh の stderr 文言に軽く結合しすぎない: `no open pull requests found` の
        ような別表現でも「PR なし」に分類し、`undeterminable` に落とさない。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            gh_stub.write_text(
                "\n".join([
                    "#!/usr/bin/env bash",
                    "set -eu",
                    'echo "no open pull requests found for branch \\"x\\"" >&2',
                    "exit 1",
                ]) + "\n",
                encoding="utf-8",
            )
            gh_stub.chmod(gh_stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertNotIn("event: undeterminable", log_text)
            self.assertIn("no-pr", log_text)

    def test_gh_timeout_env_is_clamped_below_hook_timeout(self) -> None:
        """独立レビュー3巡目で検出: `GDD_REVIEW_FOLLOWUP_GH_TIMEOUT` を
        hooks.json 側の hook 自体の timeout（8 秒）以上に設定すると、python3/git
        の前処理より前に hook ごと外部から kill され、`undeterminable` すら
        記録されずに沈黙する。6 秒に頭打ちされることを、gh を待つ `sleep 1` の
        回数で確認する（壁時計は負荷で伸び、並列の全量テストでは 8 秒に届く）。"""
        hook_timeout = hook_timeout_seconds("run-review-followup-nudge-hook.sh")
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            # gh は本物の sleep で止まり、hook の待ちの sleep は回数を書いてすぐ返す
            gh_stub = Path(tmp) / "gh-stub.sh"
            gh_stub.write_text(f"#!/bin/sh\nexec {shutil.which('sleep')} 30\n", encoding="utf-8")
            gh_stub.chmod(0o755)
            bindir = Path(tmp) / "bin"
            bindir.mkdir()
            sleeps = Path(tmp) / "sleeps"
            (bindir / "sleep").write_text(f"#!/bin/sh\necho \"$1\" >> '{sleeps}'\n", encoding="utf-8")
            (bindir / "sleep").chmod(0o755)
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    # hook timeout(8秒)以上を指定しても 6 秒に頭打ちされるはず。
                    "GDD_REVIEW_FOLLOWUP_GH_TIMEOUT": "99",
                    "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            waited = sleeps.read_text(encoding="utf-8").split() if sleeps.exists() else []
            self.assertEqual(waited, ["1"] * 6, result.stderr)
            self.assertLess(len(waited), hook_timeout)
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertIn("gh-timeout", log_text)

    def test_hash8_pipefail_does_not_block_hook(self) -> None:
        """人間レビュー指摘 High-1: PATH 上の `shasum` が「無い」のではなく
        「非 0 終了する」場合、`set -euo pipefail` 下では _hash8 のパイプライン
        全体の失敗が hook 全体へ伝播しうる。PreToolUse で終了コード 2 は block
        扱いになるため、advisory のはずの hook が空の reason で push を deny
        しうる（`run-merge-gate-hook.sh` が既に同型を警告済み）。壊れた
        `shasum` を PATH 前方に置いても、hook が exit code 0 で完走し（block
        しない）、sha1sum へフォールバックして正しく注入できることを固定する。
        """
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            broken_bin = Path(tmp) / "broken-bin"
            broken_bin.mkdir()
            broken_shasum = broken_bin / "shasum"
            broken_shasum.write_text(
                "#!/usr/bin/env bash\nexit 1\n", encoding="utf-8"
            )
            broken_shasum.chmod(
                broken_shasum.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
            )
            env = os.environ.copy()
            env.update(
                {
                    "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "PATH": f"{broken_bin}:{env['PATH']}",
                }
            )
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "git push origin feature-x"},
            }
            result = subprocess.run(
                ["bash", str(HOOK)],
                cwd=repo,
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=HANG_GUARD,
            )
            self.assertEqual(
                result.returncode, 0, f"stderr={result.stderr!r} stdout={result.stdout!r}"
            )
            self.assertIn("additionalContext", result.stdout)

    def test_merged_pr_is_not_injected(self) -> None:
        """人間レビュー指摘 Medium: `gh pr view --json number,url` は MERGED /
        CLOSED でも exit 0 で "number" を返す。state を見ずに注入すると、
        マージ済み branch への push（多くは followup と無関係）にまで誤注入
        する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr-merged")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertIn("event: skipped", log_text)
            self.assertIn("no-pr", log_text)

    def test_gh_exit_zero_with_unexpected_state_is_undeterminable_not_no_pr(self) -> None:
        """PR #88 人間レビュー round 6 指摘 Medium: `gh pr view` が exit 0
        でも、state が OPEN/MERGED/CLOSED のいずれでもない場合（`--jq` の
        出力が壊れた・API 応答が想定外だった等）に「OPEN ではない」を
        「no-pr」と断定していた。fail-safe の契約「判定不能は
        undeterminable として記録し、no-pr と誤判定しない」は非 0 終了時
        にしか効いておらず、exit 0 かつ想定外の state はそのまま no-pr
        として 300 秒キャッシュされていた。既知の3値（OPEN/MERGED/CLOSED）
        以外は undeterminable に倒すことを固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="exit0-unexpected-state")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertIn("event: undeterminable", log_text)
            self.assertIn("gh-unexpected-state", log_text)
            self.assertNotIn(
                "event: skipped",
                log_text,
                "想定外の state を no-pr(skipped) として誤記録している",
            )

    def test_gh_state_output_with_extra_whitespace_is_still_recognized(self) -> None:
        """独立レビュー round 4 指摘 Medium: 旧実装は生 JSON を
        `grep -q '"state":"OPEN"'` で文字列一致させていたため、`gh` が
        （`CLICOLOR_FORCE=1` 等で）整形・色付き出力に切り替わる環境では
        一致が壊れ、OPEN な PR でも "no" と誤判定していた。`--json state
        --jq '.state'` へ切り替えた後は前後の空白があっても正しく認識できる
        ことを固定する（`--jq` は整形より前の生 API レスポンスに対して評価
        されるため、実運用でこの空白が付くのは主に本 stub のような境界値
        テストのみだが、`tr -d` での正規化自体の正しさを固定する）。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            gh_stub.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -eu",
                        'printf " OPEN \\n"',
                        "exit 0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            gh_stub.chmod(
                gh_stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
            )
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("additionalContext", result.stdout)

    def test_gh_process_is_not_orphaned_after_timeout(self) -> None:
        """人間レビュー指摘 Medium: `( cd ... && gh ...; echo $? > rc ) &` の
        ため `$!` は subshell の pid で、`gh` 本体はその子。timeout の
        `kill -9 "$_gh_pid"` は subshell だけを殺し、`gh` は init に引き取ら
        れて残り続ける。subshell の直接の子も辿って kill することを固定する。

        独立レビュー round 4 で指摘: `subprocess.run`（hook 完了まで blocking）
        の後で pid file の出現を確認すると、`-n auto` の並列負荷下でスケジュー
        リングが遅れ stub が最初の行（pid file 書き込み）に到達する前に
        timeout kill が先に走ることがあり、"stub never started" として誤って
        flaky に落ちる。`Popen` で起動し、hook がまだ timeout 待ちをしている
        間（GDD_REVIEW_FOLLOWUP_GH_TIMEOUT 秒の猶予がある間）に pid file の
        出現を確認することで、hook 完了を待たずに済ませる。timeout 自体も
        1 秒では負荷時の起動猶予が足りないため 3 秒にする。
        """
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            pid_file = Path(tmp) / "gh.pid"
            gh_stub.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -eu",
                        f'echo $$ > "{pid_file}"',
                        "sleep 30",
                        "exit 0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            gh_stub.chmod(
                gh_stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
            )
            state_dir = Path(tmp) / "hookstate"
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "git push origin feature-x"},
            }
            env = os.environ.copy()
            env.update(
                {
                    "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    "GDD_REVIEW_FOLLOWUP_GH_TIMEOUT": "3",
                }
            )
            proc = subprocess.Popen(
                ["bash", str(HOOK)],
                cwd=repo,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            assert proc.stdin is not None
            proc.stdin.write(json.dumps(payload))
            proc.stdin.close()
            # hook がまだ timeout 待ちをしている間に pid file の出現を確認する
            # （hook 完了まで待つと、負荷次第で「kill が先に走った」のか
            # 「stub がまだ起動していないだけ」なのかを区別できない）。
            for _ in range(100):
                if pid_file.exists():
                    break
                time.sleep(0.1)
            self.assertTrue(
                pid_file.exists(), "gh stub process never started within the timeout window"
            )
            gh_pid = int(pid_file.read_text(encoding="utf-8").strip())
            stdout, stderr = proc.communicate(timeout=20)
            self.assertEqual(proc.returncode, 0, stderr)
            for _ in range(40):
                try:
                    os.kill(gh_pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.1)
            else:
                self.fail(
                    f"gh stub process {gh_pid} is still alive after hook timeout (orphaned)"
                )

    def test_cache_file_and_dir_permissions_are_restricted(self) -> None:
        """人間レビュー指摘 Medium: cache の mkdir/write に chmod が無く、実測
        で directory 0755 / file 0644 になっていた。同じ state dir の近傍
        （log は 600 済み）と非対称だった。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            cache_dir = state_dir / "review-followup-pr-cache"
            self.assertTrue(cache_dir.is_dir())
            cache_files = list(cache_dir.iterdir())
            self.assertEqual(len(cache_files), 1)
            dir_mode = stat.S_IMODE(cache_dir.stat().st_mode)
            file_mode = stat.S_IMODE(cache_files[0].stat().st_mode)
            self.assertEqual(oct(dir_mode), oct(0o700))
            self.assertEqual(oct(file_mode), oct(0o600))

    def test_gh_binary_resolved_once_survives_relative_path_lookup_after_cd(self) -> None:
        """PR #88 人間レビュー round 5 指摘 Medium: `command -v "$GH_BIN"` は
        hook 自身の起動 cwd で解決するが、実行は `cd "$ROOT"` の後だった。
        `$GH_BIN` が相対名で PATH に `.`（カレントディレクトリ）を含む場合、
        存在確認した実体と実際に実行される実体が別物になりうる —
        untrusted な push 対象 repo（`$ROOT`）に `cd` した後に PATH 経由で
        `gh` を再解決すると、その repo 自身に置かれた偽の `gh` を拾ってしまう
        （新しく untrusted repo を cwd にして外部バイナリを呼ぶ形の攻撃面）。
        起動 cwd で一度だけ絶対パスへ解決し、以後はその絶対パスだけを実行
        することで、`cd` 後の PATH 再解決を発生させないことを固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            other_repo = Path(tmp) / "other-repo"
            other_repo.mkdir()
            self._init_repo(other_repo, branch="other-branch")

            malicious_marker = Path(tmp) / "malicious-called.log"
            malicious_gh = other_repo / "gh"
            malicious_gh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -eu",
                        f'printf "call\\n" >> "{malicious_marker}"',
                        'echo "OPEN"',
                        "exit 0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            malicious_gh.chmod(
                malicious_gh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
            )

            safe_dir = Path(tmp) / "safe-bin"
            safe_dir.mkdir()
            safe_gh = safe_dir / "gh"
            safe_counter = Path(tmp) / "safe-counter.log"
            _write_stub_gh(safe_gh, behavior="has-pr", counter_file=safe_counter)

            # "." を先頭にした PATH。旧実装（cd 後に "$GH_BIN" を再解決）だと
            # cd 後の cwd（other_repo）で "." が other_repo/gh を拾ってしまう。
            # 起動 cwd（repo、gh を置いていない）には該当が無いので、修正後は
            # "." をスキップして safe_dir/gh に解決される。
            env_path = f".:{safe_dir}:{os.environ.get('PATH', '')}"
            result = self._run_hook(
                repo,
                f"cd {other_repo} && git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "PATH": env_path,
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(
                malicious_marker.exists(),
                "cd 後の PATH 再解決で untrusted repo 内の偽 gh が実行されている",
            )
            self.assertTrue(
                safe_counter.exists(), "起動 cwd で解決した安全な gh が実行されていない"
            )

    def test_relative_gh_resolution_is_rejected_not_executed(self) -> None:
        """PR #88 人間レビュー round 3 指摘 High（round 5 修正の是正漏れ）:
        `command -v` は PATH 要素を前置するだけなので、PATH に `.` を含み、
        かつ**起動 cwd 自身**に `gh` という名前の実行可能ファイルがあると、
        `command -v` 自体が相対パス（`./gh`）を返す（実測確認済み）。round 5
        の「起動 cwd で一度だけ絶対パスへ解決する」修正は cd 後の再解決は
        防ぐが、この相対パス自体を実行してしまえば untrusted な push 対象
        repo 側のファイルが動く前提は変わらない。解決結果が絶対パスでない
        場合は「見つからない」と同じ fail-safe（`gh` を呼ばず判定不能）に
        倒すことを固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)

            repo_gh_marker = Path(tmp) / "repo-gh-called.log"
            repo_gh = repo / "gh"
            repo_gh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -eu",
                        f'printf "call\\n" >> "{repo_gh_marker}"',
                        'echo "OPEN"',
                        "exit 0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            repo_gh.chmod(
                repo_gh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
            )

            state_dir = Path(tmp) / "hookstate"
            # "." を PATH に含める。起動 cwd（= repo。command -v は cd 前の
            # ここで評価される）に `gh` があるため、`command -v gh` は
            # 絶対パスではなく相対パス `./gh` を返す。
            env_path = f".:{os.environ.get('PATH', '')}"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "PATH": env_path,
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.strip(), "",
                "相対パスに解決された gh を実行し、注入まで進んでいる",
            )
            self.assertFalse(
                repo_gh_marker.exists(),
                "相対パスのまま gh を実行している（fail-safe になっていない）",
            )
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertIn("gh-not-absolute", log_text)

    def test_broken_date_does_not_reuse_stale_cache_forever(self) -> None:
        """PR #88 人間レビュー round 3 指摘 Low（後続可、同じ push で吸収）:
        `date +%s` が失敗すると `NOW_EPOCH="0"`（既存の fallback）になる。
        これをそのまま TTL 比較に使うと `0 - _cached_epoch`（大きな負数）が
        常に `<= _ttl` を満たしてしまい、どれだけ古いキャッシュでも
        期限切れにならなくなる。`NOW_EPOCH="0"` のときはキャッシュ読みを
        無効化し、毎回 fresh に `gh` を呼ぶことを固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)

            fake_bin = Path(tmp) / "fake-bin"
            fake_bin.mkdir()
            (fake_bin / "date").write_text(
                "#!/usr/bin/env bash\nexit 1\n", encoding="utf-8"
            )
            (fake_bin / "date").chmod(0o755)

            state_dir = Path(tmp) / "hookstate"
            cache_dir = state_dir / "review-followup-pr-cache"
            cache_dir.mkdir(parents=True)
            root_hash = _hash8(str(repo.resolve()))
            # 古い（本来ならとっくに TTL 切れの）cache に、今回の fresh 判定
            # （gh stub は has-pr = "yes"）とは異なる "no" を仕込んでおく。
            # NOW_EPOCH=0 のバグが残っていれば、この古い "no" がそのまま
            # 再利用され、注入が起きない。
            (cache_dir / f"{root_hash}__{_hash8('feature-x')}").write_text(
                "1\nno\n", encoding="utf-8"
            )
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            env_path = f"{fake_bin}:{os.environ.get('PATH', '')}"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    "PATH": env_path,
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "additionalContext", result.stdout,
                "date 失敗時に古いキャッシュ(no)が再利用され、fresh 判定(yes)へ進んでいない",
            )

    def test_future_dated_cache_entry_is_not_reused(self) -> None:
        """独立レビュー指摘 Low（round 3 の `NOW_EPOCH="0"` 是正と同じ根本
        原因の別形）: TTL 比較 `now - cached_epoch <= ttl` は、cache の
        epoch が **未来**（システムクロックのずれ — RTC 復旧直後の
        VM/container 等）でも同じ理由で常に真になる。`date` 自体は正常に
        動いていても、未来日付の cache が無期限に再利用され続けることを
        固定するための regression test。`NOW_EPOCH < _cached_epoch` の
        cache は無効（未来日付＝壊れている）として扱う。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)

            state_dir = Path(tmp) / "hookstate"
            cache_dir = state_dir / "review-followup-pr-cache"
            cache_dir.mkdir(parents=True)
            root_hash = _hash8(str(repo.resolve()))
            future_epoch = int(time.time()) + 10_000_000
            # 未来日付の cache に、今回の fresh 判定（gh stub は has-pr =
            # "yes"）とは異なる "no" を仕込んでおく。未来日付ガードが無ければ
            # `now - future_epoch` は大きな負数になり、常に TTL 内と判定
            # されてこの古い "no" がそのまま再利用される。
            (cache_dir / f"{root_hash}__{_hash8('feature-x')}").write_text(
                f"{future_epoch}\nno\n", encoding="utf-8"
            )
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "additionalContext", result.stdout,
                "未来日付の古いキャッシュ(no)が再利用され、fresh 判定(yes)へ進んでいない",
            )


if __name__ == "__main__":
    unittest.main()
