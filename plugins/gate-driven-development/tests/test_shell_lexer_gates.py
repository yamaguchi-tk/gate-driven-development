"""共有の字句解析の芯（`lib/shell_lexer.py`）を通る 4 つの gate を、hook の入口から確かめる。

pre-push gate・root-branch guard（`validate-worktree-command.py`）・merge gate・pre-PR gate のそれぞれで、
fail-open の 3 ケース（block すべき入力が allow になる／例外で guard 全体が落ちる／判定できないときに
通る）を見る。期待値の正解は、偽の gh・git を PATH の先頭に置いて bash と zsh で実行した argv。

- 複数行の commit メッセージの閉じ側の行に `"` が 2 つあると、行ごとの字句解析は
  ` && git push … --body ` を 1 つの引用符の token と読み、push を見落としていた
- `gh pr merge N …` の後に改行して次のコマンドを書くと、次のコマンドを merge の引数と読み、
  対象を決められない側（block）に倒していた
- `$(…)#x` の `#` をコメントと読み、後ろの `gh pr merge`・`gh pr create` を見落としていた
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

from _merge_gate_support import HANG_GUARD, _new_repo_with_marker_and_pr, _run_hook as _run_merge_hook
from _paths import PLUGIN_ROOT
from _pre_push_gate_support import PrePushGateFixtureMixin
from _root_branch_guard_support import RootBranchGuardFixtureMixin
from _timing_budget import hook_timeout_seconds, timing_budget
import test_pre_pr_gate_contract as pre_pr_contract

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

import gh_command_parse  # noqa: E402
import git_command_parse as gcp  # noqa: E402
import push_command_parse as pcp  # noqa: E402
import shell_lexer  # noqa: E402

PRE_PUSH_HOOK_TIMEOUT = hook_timeout_seconds("run-pre-push-gate-hook.sh")
NL = "\n"
BS = "\\"

# 閉じ側の行に `"` が 2 つある、複数行の commit メッセージの後の push（実データに多い型）。
COMMIT_THEN_PUSH = (
    'git commit -m "fix: s' + NL + NL + 'Co-Authored-By: X <x@example.com>" && git push origin HEAD'
    ' && gh pr comment 1 --body "c' + NL + 'd"'
)
# 同じ型で branch を作る形。
COMMIT_THEN_SWITCH = (
    'git commit -m "a' + NL + 'b" && git switch -c codex/20261013-x && echo "c' + NL + 'd"'
)
# 引用した heredoc の本文に、引用符を対にするアポストロフィが 2 つある（本文は実行されない）。
HEREDOC_APOSTROPHES_THEN_PUSH = (
    "cat > f <<'EOF'" + NL + "it's" + NL + "EOF" + NL + "git push origin main" + NL
    + "cat > g <<'E2'" + NL + "don't" + NL + "E2"
)
# 引用した heredoc の本文の行末の `\`（行継続にならない。終端の行は EOF のまま）。
QUOTED_HEREDOC_BACKSLASH = "cat > f <<'EOF'" + NL + "a " + BS + NL + "EOF" + NL
# 二重引用符の中の `$(…)`・バッククォート・`${…}` の中の `"` は外の引用を閉じない。中の `#` は
# コメントではない（bash・zsh とも後ろの push を実行する）。
QUOTED_SUBSTITUTION_PREFIXES = (
    'git commit -m "$(printf "fix #12")" && ',
    "echo `echo a #b`; ",
    'echo "${x:-"a #b"}" && ',
)
# バッククォートの中の `$(…)`・サブシェルの `#`。bash は閉じる ` を先に探すので、`#` はコメントに
# ならず後ろのコマンドを実行する（zsh は何も実行しない。割れる形は止める側）。二重引用符の中の
# バッククォートの形は bash・zsh とも実行する。
BACKTICK_PAREN_PREFIXES = (
    "echo `echo $(echo a #b)`; ",
    "`(echo a #b)`; ",
    'echo `echo "$(echo a #b)"`; ',
    'echo "`echo "a #b"`" && ',
)
# バッククォートの区間は、エスケープされていない次の ` までで閉じる（bash の読み）。区間の中のコメントは
# 閉じの手前で終わり、中の `'`・`"` は外の引用にならない。下の形は、bash が後ろの push を今の repo で
# 実行する（1 つ目の `cd /tmp` はコメントの中。zsh は 1 つ目だけ何も実行しない。割れる形は止める側）。
BACKTICK_INTERVAL_PUSHES = (
    "echo `(echo a` && ( true # ; cd /tmp" + NL + "git push origin main )",
    "v=`git rev-parse HEAD # it's the tip`" + NL + "git push origin main # don't wait",
    'x="`echo a # it' + "'" + 's`"' + NL + "git push origin main # don't",
)
# 引用符の外の区間の中の引用は、トップレベルと同じく対にして読む（bash・zsh とも後ろの push を実行する）。
# 中の `"` を残したまま `'` だけを追うと `"` が外へ漏れ、中の引用を外すと引用した `;`・改行が外の区切りになる。
OUTER_INTERVAL_PUSHES = (
    "x=`echo 'a\"b'`; git push origin main; y=`echo 'c\"d'`",
    'echo `echo "; cd /tmp "`; git push origin main',
    'echo `echo "a' + NL + 'cd /tmp b"`; git push origin main',
    'echo `echo "; GDD_SKIP_PRE_PUSH_GATE=1 git push "`; git push origin main',
)
# 二重引用符の中の区間（`$(…)` の内側を含む）の中身は、外の二重引用符の中の 1 語として読む。
QUOTED_INTERVAL_PUSHES = (
    "x=\"$(echo `echo 'a\"b'`)\"; git push origin main; y=\"$(echo `echo 'c\"d'`)\"",
    'x="`echo "; cd /tmp"`"; git push origin main',
)
# 閉じないバッククォートの中に `(` が 40,000 個、後ろに ` #` が 40,000 個（bash・zsh は 1 行目の push を
# 実行しない〔構文エラー〕が、割れる形は止める側）。
DEEP_BACKTICK = "git push origin main" + NL + "(" * 40000 + "`" + " #" * 40000
# git・push・gh の側が区切りと読む集合の和（引用すると語になる）。
SEPARATOR_WORDS = (
    gcp.COMMAND_SEPARATOR_TOKENS
    | pcp._COMMAND_START_SEPARATORS
    | pcp.PUSH_DETECTION_COMMAND_START_SEPARATORS
    | pcp.PUSH_DETECTION_CD_SEPARATORS
    | {";", "|", "&", "&&", "||", ";;", "|&"}
)
# heredoc の本文に heredoc を 1,000 段入れ子にする（本文はデータで、最後の行の push は実行される）。
NESTED_HEREDOCS = NL.join(
    [f"cat <<E{i}" for i in range(1000)] + [f"E{i}" for i in reversed(range(1000))] + ["git push origin main"]
)


def _is_block(result: subprocess.CompletedProcess[str]) -> bool:
    """pre-push gate・pre-PR gate は止めず、止めていた入力では実行後の通知を出す。"""
    return result.returncode == 0 and '"hookEventName": "PreToolUse"' in result.stdout and '"decision"' not in result.stdout


def _is_pass(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode == 0 and '"hookEventName"' not in result.stdout


def _is_merge_notice(result: subprocess.CompletedProcess[str]) -> bool:
    """merge gate は止めず、止めていた入力では実行後の通知を出す。"""
    return result.returncode == 0 and '"hookEventName": "PreToolUse"' in result.stdout and '"decision"' not in result.stdout


def _is_merge_pass(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode == 0 and not result.stdout.strip()


def _copy_hooks_with_broken_lexer(root: Path) -> Path:
    """hooks を写し、`shell_lexer.py` を import の時点で例外を投げるものに替える。"""
    plugin = root / "plugin"
    shutil.copytree(PLUGIN_ROOT / "hooks", plugin / "hooks")
    (plugin / "hooks" / "scripts" / "lib" / "shell_lexer.py").write_text(
        "raise RuntimeError('broken')\n", encoding="utf-8"
    )
    return plugin


class PrePushGateTests(PrePushGateFixtureMixin, unittest.TestCase):
    def _run(self, command: str) -> subprocess.CompletedProcess[str]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / "repo"
        repo.mkdir()
        self._init_repo(repo)
        self._write_local_state(repo, active=True)
        self._write_steering(repo, task_size="standard")
        return self._run_hook(repo, command, extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp.name) / "s")})

    def test_push_after_multiline_commit_message_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも push を実行する。
        result = self._run(COMMIT_THEN_PUSH)
        self.assertTrue(_is_block(result), result.stdout + result.stderr)
        self.assertIn("missing-evidence", result.stdout)

    def test_push_after_heredoc_with_apostrophes_is_blocked(self) -> None:
        # block すべき入力が allow になる: 本文のアポストロフィで引用符を対にして push を飲まない。
        result = self._run(HEREDOC_APOSTROPHES_THEN_PUSH)
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_push_after_quoted_heredoc_backslash_is_blocked(self) -> None:
        # 引用した heredoc の行末の `\` で終端の行をつながない（bash・zsh とも push を実行する）。
        result = self._run(QUOTED_HEREDOC_BACKSLASH + "git push origin main")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_push_after_command_substitution_hash_is_blocked(self) -> None:
        result = self._run("echo $(date)#x; git push origin main")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_push_with_a_quote_left_open_is_blocked(self) -> None:
        # 判定できないときに通る: 引用符が末尾まで閉じないと、bash はその前の行の push を実行する
        # （zsh は何も実行しない）。割れる形は止める側。
        for command in ("git push origin main" + NL + 'echo "x', "echo 'x" + NL + "git push origin main"):
            with self.subTest(command=command):
                self.assertTrue(_is_block(self._run(command)))

    def test_hostile_inputs_do_not_take_the_guard_down(self) -> None:
        # 例外で guard 全体が落ちる: この hook は解析の例外で通す設計なので、芯が例外を投げない
        # ことを入口から確かめる（lone surrogate・NUL・閉じない `$'`・深い入れ子・長い入力）。
        for command in (
            "git push origin main \ud800 '" + NL + "x",
            "git push origin main \x00 $'",
            "bash -c " * 8 + "'git push origin main'",
            "echo " + "'a' " * 3000 + "; git push origin main",
            "cat <<EOF" + NL + "x" + NL + "git push origin main",
            NESTED_HEREDOCS,
        ):
            with self.subTest(command=command[:40]):
                self.assertTrue(_is_block(self._run(command)))

    def test_push_after_a_quoted_substitution_with_a_hash_is_blocked(self) -> None:
        # block すべき入力が allow になる: 中の `"` で外の引用を閉じたと読むと、`#` 以降をコメントとして
        # 落とし、push を見落とす。
        for prefix in QUOTED_SUBSTITUTION_PREFIXES:
            with self.subTest(prefix=prefix):
                result = self._run(prefix + "git push origin main")
                self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_push_after_a_backtick_with_a_hash_in_parens_is_blocked(self) -> None:
        # block すべき入力が allow になる。
        for prefix in BACKTICK_PAREN_PREFIXES:
            with self.subTest(prefix=prefix):
                result = self._run(prefix + "git push origin main")
                self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_push_after_a_backtick_interval_is_checked(self) -> None:
        # block すべき入力が allow になる: 区間の中の `(` が外の文脈に残ると、後ろの `#` をコメントと読まず
        # `cd /tmp` を実行先と読む。区間の中のアポストロフィが引用を開くと、push を見落とす。
        for command in BACKTICK_INTERVAL_PUSHES:
            with self.subTest(command=command):
                result = self._run(command)
                self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_quotes_inside_an_interval_pair_up_and_stay_inside(self) -> None:
        # block すべき入力が allow になる: push を見落とす、引用の中の `cd`・opt-out を受理する。
        for command in OUTER_INTERVAL_PUSHES + QUOTED_INTERVAL_PUSHES:
            with self.subTest(command=command):
                tokens, raw = pcp.tokenize_with_boundary(command)
                self.assertEqual(pcp._find_cd_root(tokens, pcp.is_git_push(tokens)[1]), "")
                self.assertFalse(pcp.find_optout(tokens, raw)["accepted"])
                result = self._run(command)
                self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_push_inside_an_interval_outside_quotes_is_checked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも区間の中の push を実行する。引用符の外の区間の
        # 中身を 1 語にすると（全部をエスケープすると）、中の `;` が区切りでなくなり push を見落とす。
        result = self._run('echo `echo "a"; git push origin main`')
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_push_before_an_unclosed_backtick_is_blocked(self) -> None:
        # 判定できないときに通る: 閉じないバッククォートの中のアポストロフィ（bash は 1 行目の push を
        # 実行し、zsh は何も実行しない）。
        result = self._run("git push origin main" + NL + "echo `x # it's")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_deep_backtick_finishes_within_the_hook_timeout(self) -> None:
        # 例外で guard 全体が落ちる: hook の timeout（10 秒）を超えると、gate は検査せずに通る。
        # CPU 時間を timeout と比べる（壁時計は負荷で伸び、並列の実行で落ちる）。hook の処理はほぼ直列なので、
        # CPU 時間だけで timeout を超えるなら、壁時計でも超える
        with timing_budget() as timing:
            result = self._run(DEEP_BACKTICK)
        self.assertTrue(_is_block(result), result.stdout + result.stderr)
        self.assertLess(timing.cpu_seconds, PRE_PUSH_HOOK_TIMEOUT, f"wall {timing.wall_seconds:.2f}s")

    def test_every_quoted_separator_is_a_word(self) -> None:
        # 引用した区切りは、どの集合の区切りとも読まない（例外も投げない）。
        for word in sorted(SEPARATOR_WORDS):
            for quoted in (f"'{word}'", f'"{word}"'):
                with self.subTest(quoted=quoted):
                    tokens, degraded = shell_lexer.lex(f"echo {quoted} x", NL, 1)
                    self.assertFalse(degraded)
                    self.assertEqual(tokens, ["echo", word, "x"])
                    self.assertIsInstance(tokens[1], shell_lexer.QuotedWord)

    def test_quoted_newline_does_not_start_an_opt_out_or_a_cd(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも、opt-out の代入と cd は echo の引数で、
        # 後ろの push は今の repo で opt-out なしに実行する。
        command = "echo '" + NL + "' GDD_SKIP_PRE_PUSH_GATE=1 git push a b; git push origin main"
        tokens, raw = pcp.tokenize_with_boundary(command)
        self.assertFalse(pcp.find_optout(tokens, raw)["accepted"])
        self.assertTrue(_is_block(self._run(command)))
        with tempfile.TemporaryDirectory() as other:
            command = "echo '" + NL + f"' cd {other} && git push origin main"
            tokens, _raw = pcp.tokenize_with_boundary(command)
            self.assertEqual(pcp._find_cd_root(tokens, pcp.is_git_push(tokens)[1]), "")
            result = self._run(command)
            self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_quoted_separator_in_the_refspecs_is_ambiguous(self) -> None:
        # bash・zsh とも git に `origin main & feature` を渡す（refspec が 2 つ）。対象を決められない側。
        command = "git push origin main '&' feature"
        tokens, _raw = pcp.tokenize_with_boundary(command)
        self.assertTrue(pcp.classify_refspec(tokens, pcp.is_git_push(tokens)[1])["ambiguous"])
        result = self._run(command)
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_quoted_separator_as_a_global_option_value_is_a_push(self) -> None:
        # block すべき入力が allow になる: git は `&` という dir で push する。
        result = self._run("git -C '&' push origin main")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_quoted_separator_before_dry_run_is_still_a_dry_run(self) -> None:
        # git は `;` を refspec、`--dry-run` を option と読む（remote を更新しない）。
        tokens, _raw = pcp.tokenize_with_boundary("git push origin ';' --dry-run")
        self.assertTrue(pcp.push_has_side_effect_excluded_flag(tokens, pcp.is_git_push(tokens)[1]))

    def test_push_before_an_unclosed_quoted_substitution_is_blocked(self) -> None:
        # 判定できないときに通る: bash は 1 行目の push を実行する（zsh は何も実行しない）。
        result = self._run("git push origin main" + NL + 'echo "$(echo "a #b"')
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_deeply_nested_heredocs_do_not_take_the_guard_down(self) -> None:
        # 例外で guard 全体が落ちる: 本文の再帰が深すぎても、行ごとの読みに倒して push を見る。
        tokens, _raw = pcp.tokenize_with_boundary(NESTED_HEREDOCS)
        self.assertTrue(pcp.is_git_push(tokens)[0])
        result = self._run(NESTED_HEREDOCS)
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_quoted_separator_does_not_start_an_opt_out(self) -> None:
        # block すべき入力が allow になる: 引用した `;` は区切りではない。bash・zsh とも opt-out の
        # 代入は echo の引数で、2 つ目の push は opt-out なしで実行する。
        command = "echo ';' GDD_SKIP_PRE_PUSH_GATE=1 git push a b; git push origin main"
        tokens, raw = pcp.tokenize_with_boundary(command)
        self.assertFalse(pcp.find_optout(tokens, raw)["accepted"])
        result = self._run(command)
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_quoted_separator_does_not_start_a_cd(self) -> None:
        # block すべき入力が allow になる: `cd` は echo の引数で、push は今の repo で実行する。
        with tempfile.TemporaryDirectory() as other:
            command = f"echo ';' cd {other} && git push origin main"
            tokens, _raw = pcp.tokenize_with_boundary(command)
            self.assertEqual(pcp._find_cd_root(tokens, pcp.is_git_push(tokens)[1]), "")
            result = self._run(command)
            self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_degraded_reading_keeps_the_line_reading_for_detection_only(self) -> None:
        # 縮退したら、新しい読みが push を見つければその読み、見つけなければ行ごとの読みを使う
        # （検出は 2 つの読みの和。bash・zsh は閉じない引用符の行を実行しない）。
        for command in (
            "echo 'x" + NL + "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
            'echo "x; GDD_SKIP_PRE_PUSH_GATE=1 git push origin main',
        ):
            with self.subTest(command=command):
                tokens, raw = pcp.tokenize_with_boundary(command)
                self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_union_finds_a_push_only_the_line_reading_sees(self) -> None:
        # bash・zsh とも何も実行しない（最後の行の `"` が閉じない）。新しい読みでは push は単引用符の
        # 中だが、縮退したので行ごとの読みとの和を取り、止める側に倒す。
        command = "echo 'a" + NL + "git push origin main" + NL + "y'" + NL + 'echo "b'
        tokens, degraded = shell_lexer.lex(command, NL, 1)
        self.assertTrue(degraded)
        self.assertNotIn("push", tokens)
        self.assertTrue(pcp.is_git_push(pcp.tokenize_with_boundary(command)[0])[0])


class RootBranchGuardTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self._init_repo(self.repo)
        self._write_active_state(self.repo)

    def test_branch_after_multiline_commit_message_is_denied(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも branch を作る。
        self.assertEqual(self._run_guard(self.repo, COMMIT_THEN_SWITCH).returncode, 2)

    def test_branch_after_quoted_heredoc_backslash_is_denied(self) -> None:
        result = self._run_guard(self.repo, QUOTED_HEREDOC_BACKSLASH + "git switch -c codex/20261013-y")
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_branch_with_a_quote_left_open_is_denied(self) -> None:
        # 判定できないときに通る: 閉じない引用符の前後の branch の作成。
        for command in ("git switch -c codex/20261013-z" + NL + "echo 'x", "echo 'x" + NL + "git switch -c codex/20261013-z"):
            with self.subTest(command=command):
                self.assertEqual(self._run_guard(self.repo, command).returncode, 2)

    def test_branch_inside_a_quote_before_an_unclosed_quote_is_denied(self) -> None:
        # 判定できないときに通る: 末尾の `"` が閉じない（bash・zsh は何も実行しない）。縮退したら
        # 行ごとの読みのセグメントも足し、単引用符の中に見える branch の作成で止める側に倒す。
        command = "echo 'a" + NL + "git switch -c codex/20261013-q" + NL + "y'" + NL + 'echo "b'
        self.assertEqual(self._run_guard(self.repo, command).returncode, 2)

    def test_multi_digit_fd_is_read_as_a_word_too(self) -> None:
        # bash は `12>x` を fd 12、zsh は語 `12`（root に branch 12 を作る）と読む。割れる形は止める側。
        self.assertEqual(self._run_guard(self.repo, "git branch 12>/dev/null").returncode, 2)

    def test_broken_lexer_denies(self) -> None:
        # 例外で guard 全体が落ちる: 芯を import できなければ、git を含むコマンドを止める。
        with tempfile.TemporaryDirectory() as tmp:
            plugin = _copy_hooks_with_broken_lexer(Path(tmp))
            payload = {"tool_name": "Bash", "tool_input": {"command": "git status", "cwd": str(self.repo)}}
            result = subprocess.run(
                ["python3", str(plugin / "hooks" / "scripts" / "validate-worktree-command.py")],
                input=json.dumps(payload), capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


class MergeGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)

    def _hook(self, command: str) -> subprocess.CompletedProcess[str]:
        return _run_merge_hook({"tool_input": {"command": command}}, self.repo, self.home)

    def test_command_on_the_next_line_is_not_a_merge_argument(self) -> None:
        # bash・zsh とも `gh pr merge 7 --merge` と `gh pr view 7 …` を別に実行する。
        parsed = gh_command_parse.parse_gh_pr_merge("gh pr merge 7 --merge 2>&1" + NL + "gh pr view 7 --json state", "", "/r")
        self.assertEqual((parsed["is_merge"], parsed["pr_number"], parsed["unresolvable"]), (True, "7", False))
        result = self._hook("gh pr merge 7 --merge 2>&1" + NL + "gh pr view 7 --json state")
        self.assertTrue(_is_merge_notice(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)
        self.assertTrue(_is_merge_pass(self._hook("gh pr merge 8 --merge 2>&1" + NL + "gh pr view 8 --json state")))

    def test_merge_after_command_substitution_hash_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも `gh pr merge 7` を実行する。
        result = self._hook("echo $(date)#x; gh pr merge 7")
        self.assertTrue(_is_merge_notice(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_merge_after_a_quoted_substitution_with_a_hash_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも `gh pr merge N` を実行する。
        parsed = gh_command_parse.parse_gh_pr_merge('echo "$(echo "a #b")" && gh pr merge 999', "", "/r")
        self.assertEqual((parsed["is_merge"], parsed["pr_number"]), (True, "999"))
        result = self._hook('echo "$(echo "a #b")" && gh pr merge 7')
        self.assertTrue(_is_merge_notice(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_merge_after_a_backtick_with_a_hash_in_parens_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash は `gh pr merge 7` を実行する（zsh は何も実行しない）。
        for prefix in BACKTICK_PAREN_PREFIXES:
            with self.subTest(prefix=prefix):
                result = self._hook(prefix + "gh pr merge 7")
                self.assertTrue(_is_merge_notice(result), result.stdout)

    def test_merge_after_a_backtick_interval_with_an_apostrophe_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも `gh pr merge 7 --squash` を実行する。
        result = self._hook("v=`git rev-parse HEAD # it's the tip`" + NL + "gh pr merge 7 --squash # don't")
        self.assertTrue(_is_merge_notice(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_merge_between_intervals_with_quotes_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも `gh pr merge 7 --squash` を実行する。
        result = self._hook('a=`echo "it' + "'" + 's"`; gh pr merge 7 --squash; b=`echo "don' + "'" + 't"`')
        self.assertTrue(_is_merge_notice(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_paired_quote_inside_an_interval_is_not_degraded(self) -> None:
        # 区間の中の `'"'` は対になった引用で、縮退（対象を決められない側の block）にしない。
        command = "T=`gh pr view 7 -q .title | tr -d '\"'`; gh pr merge 7 --squash"
        parsed = gh_command_parse.parse_gh_pr_merge(command, "", "/r")
        self.assertEqual((parsed["is_merge"], parsed["pr_number"], parsed["degraded"]), (True, "7", False))
        result = self._hook(command)
        self.assertTrue(_is_merge_notice(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_cd_after_leading_comment_lines_is_the_merge_location(self) -> None:
        # bash・zsh とも cd してから merge する。先頭のコメント行・空行は cd をコマンドの先頭から外さない
        # （外すと実行先を決められない側に倒れ、承認の有無を見ずに不足として通知する）。
        for prefix in ("", "# c" + NL + NL):
            with self.subTest(prefix=prefix):
                result = self._hook(f"{prefix}cd {self.repo} && gh pr merge 7")
                self.assertTrue(_is_merge_notice(result), result.stdout)
                self.assertIn("approval-missing", result.stdout)

    def test_continued_fd_number_is_unresolvable(self) -> None:
        # 判定できないときに通る: bash は fd 12（今のブランチの PR）、zsh は PR 12 を merge する。
        parsed = gh_command_parse.parse_gh_pr_merge("gh pr merge 1" + BS + NL + "2>/dev/null", "", "/r")
        self.assertTrue(parsed["is_merge"])
        self.assertTrue(parsed["unresolvable"])
        self.assertTrue(_is_merge_notice(self._hook("gh pr merge 1" + BS + NL + "2>/dev/null")))

    def test_broken_lexer_blocks_inside_active_gdd(self) -> None:
        # 例外で guard 全体が落ちる: 芯を import できなければ parse-error を不足として通知する。
        plugin = _copy_hooks_with_broken_lexer(self.tmp)
        env = {k: v for k, v in os.environ.items() if k not in ("GH_HOST", "GH_REPO", "GDD_HOOK_STATE_DIR")}
        env.update({"HOME": str(self.home), "CLAUDE_PLUGIN_ROOT": str(plugin), "CLAUDE_CODE_SESSION_ID": "test-session"})
        result = subprocess.run(
            ["bash", str(plugin / "hooks" / "scripts" / "run-merge-gate-hook.sh")],
            input=json.dumps({"tool_input": {"command": "gh pr merge 7"}}),
            capture_output=True, text=True, env=env, cwd=str(self.repo), timeout=HANG_GUARD,
        )
        self.assertTrue(_is_merge_notice(result), result.stdout + result.stderr)
        self.assertIn("parse-error", result.stdout)


class PrePrGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.h = pre_pr_contract.PrePrGateContractTests("run")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.h._init_repo(self.repo)
        self.h._write_local_state(self.repo)
        self.h._write_steering(self.repo, next_action="gdd-completion-check")

    def test_create_after_command_substitution_hash_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも `gh pr create` を実行する。
        result = self.h._run_hook(self.repo, "echo $(date)#x; gh pr create --title t --body ok")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)
        self.assertIn("Next Action=gdd-completion-check", result.stdout)

    def test_create_after_a_quoted_substitution_with_a_hash_is_blocked(self) -> None:
        # block すべき入力が allow になる: bash・zsh とも `gh pr create` を実行する。
        result = self.h._run_hook(self.repo, 'echo "$(echo "a #b")" && gh pr create --title t --body ok')
        self.assertTrue(_is_block(result), result.stdout + result.stderr)
        self.assertIn("Next Action=gdd-completion-check", result.stdout)

    def test_create_with_a_quote_left_open_is_blocked(self) -> None:
        # 判定できないときに通る。
        result = self.h._run_hook(self.repo, "gh pr create --title t --body ok" + NL + "echo 'x")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_single_quoted_body_keeps_its_line_continuation(self) -> None:
        # bash・zsh とも本文は `a \` + 改行 + `b`（単引用符の中の行継続は残る）。
        tokens = gh_command_parse._tokenize("gh pr create --body 'a " + BS + NL + "b'")
        self.assertEqual(tokens[-1], "a " + BS + NL + "b")

    def test_broken_lexer_blocks_inside_active_gdd(self) -> None:
        # 例外で guard 全体が落ちる。
        plugin = _copy_hooks_with_broken_lexer(self.root)
        original = pre_pr_contract.HOOK
        pre_pr_contract.HOOK = plugin / "hooks" / "scripts" / "run-pre-pr-gate-hook.sh"
        try:
            result = self.h._run_hook(self.repo, "gh pr create --title t --body ok")
        finally:
            pre_pr_contract.HOOK = original
        self.assertTrue(_is_block(result), result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
