"""merge gate: 対象 PR を gh と同じ文法で読み、URL の形も番号で照合する。

#232 の限界に残した、main 由来の 2 つの欠陥の再現と固定。

- gh（pflag）は短い flag を束ね（`-st`）、値を密着させ（`-t7`・`-Racme/x`・`-t=x`）、
  `--` の後を位置引数として読む。パーサは `-` で始まる token を一律に 1 token 飛ばして
  いたので、`-st 7 <branch>` の 7 を対象の PR と読み、束ねた値を取る flag の値を位置引数と
  読んでいた。`pr` と `merge` の間の flag（`gh pr -R x merge 7`）では merge を見失っていた
- 番号は gh と同じく ASCII の数字だけを番号とする。全角の `７` を番号と読むと照合に使えず
  素通りしていた
- URL の形の merge は、記録した PR URL と文字列全体で比べていたので、正準形でない
  記録（`<…>`・`| 注記`・リンクの形・`/files`・先頭の 0）の steering を通していた。
  番号の形と同じく番号で照合する（repo の違いは 3 組解決の (d) が不足として通知する）
- 台帳の経路は、対象を決められない merge（知らない flag・位置引数 2 つ以上・名指しできない URL）でも、
  読めた URL と番号が台帳の PR に当たれば不足として通知する（当たらなければ今どおり unknown）
- sub-command（`pr`・`merge`）は cobra の探索規則で見つける（知らない 2 文字の短い flag と
  `=` の無い長い flag は次の token を値として飛ばし、束ねと `=` の形は飛ばさない）。
  見つけた後は、`pr` と `merge` を除いた全 token を merge の表で読む
- 対象を決められない merge は、読めた番号が記録と違っても本体の経路で不足として通知する
- 番号・URL は gh が受ける形（`#7`・`+7`・先頭の 0・`http://`・`/pull/7/files`）も読む
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    PLUGIN_ROOT,
    _new_repo_with_marker_and_pr,
    _run_hook,
    _write_state,
    _write_two_done_steerings,
)
from _merge_gate_input_classes import once_per_input_class
from _timing_budget import hook_timeout_seconds, timing_budget
from test_merge_gate_bound_terminal_steering import _MergeGateBoundFixture
from test_merge_gate_hook_non_gdd_merge import _clone_like, _register

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

# 解析時間は CPU 時間で測り、壁時計は hook の timeout の半分を backstop にする（テスト時間の ADR の二本立て）。
WALL_BACKSTOP_SEC = hook_timeout_seconds("run-merge-gate-hook.sh") / 2

from lib.gh_command_parse import (  # noqa: E402
    _env_short_option_step,
    _read_merge_flag,
    parse_gh_pr_merge,
)

URL7 = "https://github.com/acme/widgets/pull/7"
URL8 = "https://github.com/acme/widgets/pull/8"

# 正準形でない PR URL の記録（state.md に実際に書かれうる形）。
NON_CANONICAL_7 = (
    f"<{URL7}>",
    f"{URL7} | 外部レビュー待ち",
    f"[#7]({URL7})",
    f"{URL7}/files",
    "https://github.com/acme/widgets/pull/007",
)


def _hook(command: str, cwd: Path, home: Path):
    return _run_hook({"tool_input": {"command": command}}, cwd, home,
                     drop_env=("GDD_HOOK_STATE_DIR",))


def _hook_once(cwd: Path, home: Path):
    """`_hook` と同じ起動を、hook の入力の組ごとに 1 回だけ行う（repo の状態を変えない表に使う）。"""
    run = once_per_input_class(
        lambda payload: _run_hook(payload, cwd, home, drop_env=("GDD_HOOK_STATE_DIR",)), cwd)
    return lambda command: run({"tool_input": {"command": command}})


def _is_block(result) -> bool:
    return result.returncode == 0 and '"hookEventName": "PreToolUse"' in result.stdout


def _is_pass(result) -> bool:
    return result.returncode == 0 and '"hookEventName"' not in result.stdout


def _parse(command: str) -> dict:
    return parse_gh_pr_merge(command, "", "/repo")


class ParserGrammarTests(unittest.TestCase):
    """gh が受け付ける形は、gh と同じ対象・repo に読む。"""

    def _assert_target(self, command, *, number=None, url=None, repo=None,
                       unresolvable=False, admin=False):
        result = _parse(command)
        self.assertTrue(result["is_merge"], command)
        self.assertEqual(
            (result["pr_number"], result["pr_url"], result["repo_flag"],
             result["unresolvable"], result["admin"]),
            (number, url, repo, unresolvable, admin),
            command,
        )

    def test_bundled_short_flags(self):
        cases = {
            # 値を取る flag が束ねの最後なら、次の token がその値。
            "gh pr merge -st 7": {},
            "gh pr merge -st 7 8": {"number": "8"},
            "gh pr merge 7 -st 8": {"number": "7"},
            f"gh pr merge 8 -sb {URL7}": {"number": "8"},
            f"gh pr merge -st 8 {URL7}": {"url": URL7},
            "gh pr merge -sd 7": {"number": "7"},
            "gh pr merge -dsm 7": {"number": "7"},
            # 値が密着する形。
            "gh pr merge -st7 8": {"number": "8"},
            "gh pr merge -t=x 8": {"number": "8"},
            "gh pr merge -st=x 8": {"number": "8"},
            "gh pr merge -b7 8": {"number": "8"},
            "gh pr merge -sA x@example.com 7": {"number": "7"},
            "gh pr merge -sF body.md 7": {"number": "7"},
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self._assert_target(command, **expected)

    def test_bundled_value_flag_before_a_branch_is_unresolvable(self):
        # `-st 7` の 7 は subject。対象は branch なので決められない。
        self._assert_target("gh pr merge -st 7 feature-x", unresolvable=True)

    def test_repo_flag_spellings(self):
        cases = {
            "gh pr merge -Racme/other 7": "acme/other",
            "gh pr merge -R=acme/other 7": "acme/other",
            "gh pr merge -sRacme/other 7": "acme/other",
            "gh pr merge -sR acme/other 7": "acme/other",
            "gh pr merge --repo=acme/other 7": "acme/other",
            "gh -Racme/other pr merge 7": "acme/other",
            "gh -R=acme/other pr merge 7": "acme/other",
            "gh pr -R acme/other merge 7": "acme/other",
            "gh pr -Racme/other merge 7": "acme/other",
            "gh pr --repo acme/other merge 7": "acme/other",
            "gh pr --repo=acme/other merge 7": "acme/other",
            # 後勝ち（pflag は同じ flag を上書きする）。
            "gh -R acme/first pr merge -R acme/other 7": "acme/other",
        }
        for command, repo in cases.items():
            with self.subTest(command=command):
                self._assert_target(command, number="7", repo=repo)

    def test_long_flags(self):
        cases = {
            "gh pr merge --subject=x 7": {"number": "7"},
            "gh pr merge --subject x 7": {"number": "7"},
            "gh pr merge --body-file b.md 7": {"number": "7"},
            "gh pr merge --match-head-commit abc 7": {"number": "7"},
            "gh pr merge --squash --delete-branch 7": {"number": "7"},
            "gh pr merge --squash=true 7": {"number": "7"},
            "gh pr merge --admin 7": {"number": "7", "admin": True},
            "gh pr merge --admin=true 7": {"number": "7", "admin": True},
            "gh pr merge --admin=false 7": {"number": "7"},
            "gh pr merge -h": {},
            "gh pr merge --help": {},
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self._assert_target(command, **expected)

    def test_double_dash_ends_the_flags(self):
        self._assert_target("gh pr merge -- 7", number="7")
        self._assert_target("gh pr merge -s -- 7", number="7")
        # `--` の後の `-t` は flag ではなく位置引数（branch）。
        self._assert_target("gh pr merge -- -t", unresolvable=True)

    def test_unknown_flags_are_unresolvable_but_keep_the_target(self):
        cases = {
            "gh pr merge --new-flag 7": {"number": "7"},
            "gh pr merge -x 7": {"number": "7"},
            "gh pr merge -sx 7": {"number": "7"},
            "gh pr merge 7 --new-flag": {"number": "7"},
            f"gh pr merge --new-flag {URL7}": {"url": URL7},
            "gh pr --new-flag merge 7": {"number": "7"},
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self._assert_target(command, unresolvable=True, **expected)

    def test_missing_flag_value_is_unresolvable(self):
        for command in ("gh pr merge 7 -t", "gh pr merge 7 -R", "gh pr merge 7 --subject", "gh pr merge 7 -st"):
            with self.subTest(command=command):
                self._assert_target(command, number="7", unresolvable=True)

    def test_two_positionals_are_unresolvable_but_keep_what_was_read(self):
        self._assert_target(f"gh pr merge 7 {URL8}", number="7", url=URL8, unresolvable=True)
        self._assert_target("gh pr merge 7 8", number="8", unresolvable=True)

    def test_only_ascii_digits_are_a_number(self):
        for command in ("gh pr merge ７", "gh pr merge ²", "gh pr merge ٧"):
            with self.subTest(command=command):
                result = _parse(command)
                self.assertTrue(result["is_merge"])
                self.assertIsNone(result["pr_number"])
                self.assertTrue(result["unresolvable"])

    def test_sub_command_is_found_the_way_cobra_finds_it(self):
        """gh が merge を実行する形を merge と読み、残りの token 全部を merge の表で読む。"""
        cases = {
            # 3 文字以上の束ねは値を取らない 1 token として扱われ、merge が見つかる。
            "gh pr -st merge fix 7": {"number": "7"},
            "gh pr -st merge fix": {},
            "gh -st pr merge fix": {},
            # 知らない 2 文字の短い flag・`=` の無い長い flag は次の token を飛ばす。
            # 値として飛ばされた `--` では探索は止まらない。
            "gh pr -s -- merge 7": {"number": "7"},
            "gh -s -- pr merge 7": {"number": "7"},
            "gh pr --admin -- merge 7": {"number": "7", "admin": True},
            "gh -s -t pr merge 7": {},
            # `gh` の後の `-R` は sub-command の前でも読む。
            "gh -R other/repo pr merge 7": {"number": "7", "repo": "other/repo"},
            "gh pr --help merge 7": {"number": "7"},
            # cobra は `-`・空の token を読み飛ばし、`=` を含む 2 文字の token（`-=`）は値を取らない。
            "gh pr -st - merge 7": {"number": "7"},
            "gh -st '' pr merge 7": {"number": "7"},
            "gh -st -= -R acme/widgets pr merge 7": {"number": "7", "repo": "acme/widgets"},
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self._assert_target(command, **expected)

    def test_an_empty_or_dash_token_before_merge_is_a_positional_and_unresolvable(self):
        for command in ("gh pr '' merge --squash", "gh '' pr merge --squash", "gh - pr merge 7"):
            with self.subTest(command=command):
                result = _parse(command)
                self.assertTrue(result["is_merge"], command)
                self.assertTrue(result["unresolvable"], command)

    def test_flags_gh_would_reject_after_the_sub_command_are_unresolvable(self):
        for command in ("gh --version pr merge 7", "gh --hostname github.com pr merge 7"):
            with self.subTest(command=command):
                self._assert_target(command, number="7", unresolvable=True)

    def test_a_value_flag_that_swallows_the_sub_command_name_is_unresolvable(self):
        """gh が別の版で bool として読む flag の後の sub-command も、見失わずに不足として通知する側へ倒す。"""
        for command in ("gh -h pr merge 7", "gh pr -s merge 7", "gh -s pr merge 7"):
            with self.subTest(command=command):
                self._assert_target(command, number="7", unresolvable=True)

    def test_number_forms_gh_accepts(self):
        """gh は `#` を落として `Atoi` で読む（`+7`・先頭の 0 も番号）。"""
        for command in ("gh pr merge 007", "gh pr merge +7", "gh pr merge '#7'", "gh pr merge '#+007'"):
            with self.subTest(command=command):
                self._assert_target(command, number="7")
        for command in ("gh pr merge -7", "gh pr merge '#'", "gh pr merge ++7"):
            with self.subTest(command=command):
                result = _parse(command)
                self.assertIsNone(result["pr_number"], command)

    def test_url_forms_gh_accepts_are_read_as_the_canonical_url(self):
        for token in (
            URL7, f"{URL7}/", f"{URL7}/files", f"{URL7}?a=1#b", "http://github.com/acme/widgets/pull/7",
            "HTTPS://GitHub.com/acme/widgets/pull/7", "https://github.com/acme/widgets/pull/007",
        ):
            with self.subTest(token=token):
                self._assert_target(f"gh pr merge {token}", url=URL7)

    def test_urls_gh_would_not_read_as_a_github_pr_are_a_branch(self):
        for token in (
            "https://github.com/acme/widgets/pulls/7", "https://github.com/acme/pull/7", "\x01https://github.com/acme/widgets/pull/7",
        ):
            with self.subTest(token=token):
                self._assert_target(f"gh pr merge {token}", unresolvable=True)

    def test_url_forms_gh_reads_but_the_gate_cannot_name_are_read_as_the_url_and_unresolvable(self):
        """gh は番号の後の続きを読まない（`/pull/7x` は #7）。URL は読んだうえで、対象を決められない形にする。"""
        for token in (
            f"{URL7}x", f"{URL7}.", f"{URL7}-x", "'https://github.com/acme/widgets/pull/7 '",
            "'https://github.com/acme/widgets/pull/7/files x'", "https://www.github.com/acme/widgets/pull/7",
            "https://github.com/acme/widgets/pull/%37", "https://github.com:443/acme/widgets/pull/7",
            "https://user@github.com/acme/widgets/pull/7", "https://api.github.com/acme/widgets/pull/7",
            "https://foo.bar.github.com/acme/widgets/pull/7", "https://example.com/acme/widgets/pull/7",
            "https://notgithub.com/acme/widgets/pull/7", "https:/acme/widgets/pull/7", "https:///acme/widgets/pull/7",
            "https://g\u0130thub.com/acme/widgets/pull/7", "https://a\uff0f.github.com/acme/widgets/pull/7",
            "https://a\uff03.github.com/acme/widgets/pull/7", "HTTP://[::1]/acme/widgets/pull/7",
        ):
            with self.subTest(token=token):
                self._assert_target(f"gh pr merge {token}", url=URL7, unresolvable=True)

    def test_hostile_url_tokens_never_raise(self):
        """例外で guard 全体が落ちない: 読めない URL は、読める範囲で URL に、それ以外は branch に倒す。"""
        for token in ("https://[", "https://\x00/a/b/pull/1", "http://" + "a" * 100_000, "https:", "https://a/b/c/pull/" + "9" * 5_000):
            with self.subTest(token=token[:30]):
                result = _parse(f"gh pr merge {token}")
                self.assertTrue(result["is_merge"])
                self.assertTrue(result["unresolvable"])

    # 解析時間の検査は、2 乗のとき数秒〜十数秒かかる大きさの入力を、線形なら数十 ms で終わる
    # ことを大きな余裕（1 秒）で確かめる。CPU 時間で測る（壁時計と比は、並列実行の負荷で揺れる）。
    # 壁時計は WALL_BACKSTOP_SEC を上限にし、CPU を使わずに止まる退行を拾う。
    SLOW_SECONDS = 1.0

    def _best_seconds(self, action, repeat=2):
        samples = []
        for _ in range(repeat):
            with timing_budget() as timing:
                action()
            self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
            samples.append(timing.cpu_seconds)
        return min(samples)

    def test_a_long_bundle_is_read_in_linear_time(self):
        """長い束ねが解析時間を 2 乗にして hook の timeout を超えさせない。"""
        token = "-" + "s" * 400_000
        self.assertLess(self._best_seconds(lambda: _read_merge_flag([token], 0, {})), self.SLOW_SECONDS)

    def test_many_gh_tokens_are_searched_in_linear_time(self):
        """gh の token が並んでも、sub-command の探索が token 数の 2 乗にならない。"""
        command = "gh -s " * 4_000 + "gh ; gh pr merge 7 --squash"
        results = []
        seconds = self._best_seconds(lambda: results.append(_parse(command)))
        self.assertTrue(all(result["is_merge"] for result in results))
        self.assertLess(seconds, self.SLOW_SECONDS)

    def test_a_long_env_option_bundle_is_read_in_linear_time(self):
        token = "-" + "v" * 400_000
        self.assertLess(self._best_seconds(lambda: _env_short_option_step(token, None)), self.SLOW_SECONDS)


class MainPathUrlFormTests(unittest.TestCase):
    """本体の経路（marker のある checkout）で、URL の形の merge を番号で照合する。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)

    def test_url_form_matches_non_canonical_records_on_the_found_path(self):
        """不足として通知すべき入力: 正準形でない PR URL を記録した steering の PR を、URL の形で merge する。"""
        for recorded in NON_CANONICAL_7:
            with self.subTest(recorded=recorded):
                _write_state(self.repo, active=False, pr_url=recorded)
                result = _hook(f"gh pr merge {URL7}", self.repo, self.home)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("approval-missing", result.stdout)

    def test_url_form_matches_non_canonical_records_on_the_multiple_path(self):
        """不足として通知すべき入力: steering が 2 件で、対象の記録が正準形でない。"""
        _write_two_done_steerings(self.repo)
        state = self.repo / ".steering" / "20260101-demo" / "state.md"
        for recorded in NON_CANONICAL_7:
            with self.subTest(recorded=recorded):
                state.write_text(
                    "## Gate Status\n- Resume From: done\n- Next Action: done\n"
                    f"- PR URL: {recorded.replace('/7', '/1').replace('/007', '/001').replace('#7', '#1')}\n"
                )
                result = _hook("gh pr merge https://github.com/acme/widgets/pull/1", self.repo, self.home)
                self.assertTrue(_is_block(result), result.stdout)

    def test_other_pr_url_still_passes(self):
        """通知しすぎない: 記録と別の番号の URL は今どおり通す。"""
        for recorded in NON_CANONICAL_7:
            with self.subTest(recorded=recorded):
                _write_state(self.repo, active=False, pr_url=recorded)
                self.assertTrue(_is_pass(_hook(f"gh pr merge {URL8}", self.repo, self.home)))

    def test_same_number_in_another_repo_is_stopped_like_the_number_form(self):
        """受理集合の対称性: 別 repo の同じ番号は、URL の形でも `-R` の番号の形と同じく不足として通知する。"""
        hook = _hook_once(self.repo, self.home)
        for command in ("gh pr merge -R other/x 7", "gh pr merge https://github.com/other/x/pull/7"):
            with self.subTest(command=command):
                result = hook(command)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_grammar_forms_that_target_the_recorded_pr_are_gated(self):
        """不足として通知すべき入力: gh が記録の PR（#7）を merge する形。"""
        hook = _hook_once(self.repo, self.home)
        for command in (
            "gh pr merge -st 8 7",
            f"gh pr merge -st 8 {URL7}",
            "gh pr merge 7 -st 8",
            "gh pr merge -st7 7",
            "gh pr merge -- 7",
            "gh pr -R acme/widgets merge 7",
            "gh -Racme/widgets pr merge 7",
            "gh pr merge -Racme/widgets 7",
            "bash 2>/dev/null -c 'gh pr merge 7'",
            "bash +e -c 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = hook(command)
                self.assertTrue(_is_block(result), result.stdout)

    def test_grammar_forms_that_hide_the_target_are_unresolvable(self):
        """判定できないときは不足として通知する: 対象を決められない形（branch・全角の数字・知らない flag）。"""
        hook = _hook_once(self.repo, self.home)
        for command in (
            "gh pr merge -st 7 feature-x",
            "gh pr merge ７",
            "gh pr merge --new-flag 7",
            "gh pr merge 12>/tmp/x",
            "gh pr merge 7 12>/tmp/x",
        ):
            with self.subTest(command=command):
                result = hook(command)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_sub_command_forms_that_merge_the_recorded_pr_are_gated(self):
        """不足として通知すべき入力: gh は merge を実行するが、探索を誤ると merge と読まない形。"""
        hook = _hook_once(self.repo, self.home)
        for command in (
            "gh pr -st merge fix 7",
            "gh pr -s -- merge 7",
            "gh -s -- pr merge 7",
            "gh pr --admin -- merge 7",
            "gh -s -t pr merge 7",
            "gh -st pr merge fix",
            "gh pr -st - merge 7",
            "gh -st '' pr merge 7",
            "gh -st -= -R acme/widgets pr merge 7",
        ):
            with self.subTest(command=command):
                result = hook(command)
                self.assertTrue(_is_block(result), result.stdout)

    def test_number_and_url_forms_gh_accepts_are_matched_to_the_record(self):
        """番号が決まる形は、branch と読まずに記録の PR と照合する（承認の証跡がなければ approval-missing）。"""
        _write_state(self.repo, active=False, pr_url=URL7)
        hook = _hook_once(self.repo, self.home)
        for token in (
            "007", "+7", "'#7'", f"{URL7}/", f"{URL7}/files", "http://github.com/acme/widgets/pull/7",
        ):
            with self.subTest(token=token):
                result = hook(f"gh pr merge {token}")
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("approval-missing", result.stdout)

    def test_unresolvable_target_is_stopped_even_when_the_number_read_differs(self):
        """判定できないときは不足として通知する: 読めた番号が記録（#7）と違っても、対象を決められない merge は通さない。"""
        hook = _hook_once(self.repo, self.home)
        for command in (
            "gh pr merge --new-flag 8",
            "gh pr merge 8 9",
            f"gh pr merge 8 {URL8}",
        ):
            with self.subTest(command=command):
                result = hook(command)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_a_subject_that_looks_like_the_recorded_pr_does_not_hide_a_branch_target(self):
        """不足として通知すべき入力: 記録が #9 のとき、`-st 7 <branch>` の 7 は件名で、対象は branch（決められない）。"""
        _write_state(self.repo, active=False, pr_url="https://github.com/acme/widgets/pull/9")
        result = _hook("gh pr merge -st 7 feature-x", self.repo, self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_a_redirect_in_the_value_position_does_not_hide_the_target(self):
        """不足として通知すべき入力: リダイレクトは argv に入らないので、`-t` の値は `9`、対象は #7。"""
        result = _hook("gh pr merge 7 -t >/dev/null 9", self.repo, self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)
        self.assertTrue(_is_pass(_hook("gh pr merge 8 -t >/dev/null 9", self.repo, self.home)))

    def test_newline_ends_the_merge_command(self):
        """改行はコマンドの区切り（bash・zsh とも merge を実行してから sleep する）。次の行は対象に入らない。"""
        result = _hook("gh pr merge 7 --squash\nsleep 9", self.repo, self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)
        self.assertTrue(_is_pass(_hook("gh pr merge 8 --squash\nsleep 9", self.repo, self.home)))

    def test_unresolvable_target_is_stopped_on_the_multiple_path(self):
        _write_two_done_steerings(self.repo)
        for command in ("gh pr merge --new-flag 8",):
            with self.subTest(command=command):
                result = _hook(command, self.repo, self.home)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("steering-ambiguous", result.stdout)

    def test_grammar_forms_that_target_another_pr_pass(self):
        """通知しすぎない: 記録の URL を値に持つが、gh が別の PR（#8）を merge する形。"""
        hook = _hook_once(self.repo, self.home)
        for command in (f"gh pr merge 8 -sb {URL7}", "gh pr merge -st 7 8", f"gh pr merge --body {URL7} 8"):
            with self.subTest(command=command):
                self.assertTrue(_is_pass(hook(command)))


class TerminalOnlyUrlFormTests(_MergeGateBoundFixture):
    """候補 0 件の経路（終端の steering だけ）でも、URL の形を番号で照合する。"""

    def test_url_form_matches_non_canonical_records(self):
        """不足として通知すべき入力: 中止した steering が正準形でない URL で対象 PR を記録している。"""
        for recorded in NON_CANONICAL_7:
            with self.subTest(recorded=recorded):
                self.bound.write_text(
                    "Resume From: cancelled\nNext Action: cancelled\nTask Size: standard\n"
                    f"PR URL: {recorded}\n",
                    encoding="utf-8",
                )
                self.assertIn("approval-missing", self._merge(f"gh pr merge {URL7}"))

    def test_unresolvable_target_is_stopped_even_when_the_number_read_differs(self):
        """判定できないときは不足として通知する: 対象を決められない merge は、読めた番号が記録と違っても不足として通知する。"""
        self.bound.write_text(
            "Resume From: cancelled\nNext Action: cancelled\nTask Size: standard\n"
            f"PR URL: {URL7}\n",
            encoding="utf-8",
        )
        self.assertIn("steering-ambiguous", self._merge("gh pr merge --new-flag 8"))


class LedgerGrammarTests(unittest.TestCase):
    """台帳の経路（marker の無い checkout）: 台帳の PR に当たれば、対象を決められない形でも不足として通知する。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.gdd = _new_repo_with_marker_and_pr(self.tmp, "infra-gdd", pr=7, commit=False)
        self.checkout = _clone_like(self.tmp, "root-checkout", "https://github.com/acme/infra-gdd.git")
        _register(self.home, self.gdd)

    def _from_checkout(self, command):
        return _hook(command, self.checkout, self.home)

    def test_ledger_pr_is_stopped_through_every_spelling(self):
        """不足として通知すべき入力: 台帳の PR（#7）を、gh が受け付ける形・対象を決められない形で merge する。"""
        url7 = "https://github.com/acme/infra-gdd/pull/7"
        hook = _hook_once(self.checkout, self.home)
        for command in (
            "gh pr merge -st 8 7",
            f"gh pr merge -st 8 {url7}",
            "gh pr merge -- 7",
            "gh pr -R acme/infra-gdd merge 7",
            "gh pr merge -Racme/infra-gdd 7",
            "gh pr merge --new-flag 7",
            "gh pr merge 7 --new-flag",
            "gh pr --new-flag merge 7",
            f"gh pr merge 7 {url7}",
            f"gh pr merge 8 {url7}",
            # 2〜10 桁の fd 番号で対象を決められない形も、読めた番号で台帳と照合する。
            "gh pr merge 7 12>/tmp/x",
            "gh 12>/dev/null pr merge 7",
            "bash -c 'gh pr merge 7 12>/tmp/x'",
            # zsh は `07` を語（PR #7）、bash は fd 番号に読む。zsh の読みの番号も照合する。
            "gh pr merge 07>/tmp/x",
            "# don't wait\ngh pr merge 07>/tmp/x",
        ):
            with self.subTest(command=command):
                self.assertTrue(_is_block(hook(command)))

    def test_ledger_pr_is_stopped_through_the_forms_gh_accepts(self):
        """不足として通知すべき入力: gh が台帳の PR（#7）を merge する、番号・URL・sub-command の別の綴り。"""
        url7 = "https://github.com/acme/infra-gdd/pull/7"
        hook = _hook_once(self.checkout, self.home)
        for command in (
            "gh pr merge 007",
            "gh pr merge +7",
            "gh pr merge '#7'",
            f"gh pr merge {url7}/",
            f"gh pr merge {url7}/files",
            "gh pr merge http://github.com/acme/infra-gdd/pull/7",
            "gh pr -st merge fix 7",
            "gh -s -- pr merge 7",
            "gh pr --admin -- merge 7",
            "gh pr -st - merge 7",
            "gh -st '' pr merge 7",
        ):
            with self.subTest(command=command):
                self.assertTrue(_is_block(hook(command)))

    def test_ledger_pr_is_stopped_for_non_canonical_records(self):
        url7 = "https://github.com/acme/infra-gdd/pull/7"
        for recorded in (f"<{url7}>", f"{url7} | 注記", f"[#7]({url7})", f"{url7}/files"):
            with self.subTest(recorded=recorded):
                _write_state(self.gdd, active=False, pr_url=recorded)
                self.assertTrue(_is_block(self._from_checkout(f"gh pr merge {url7}")))

    def test_ledger_pr_is_stopped_when_the_url_has_a_tail_or_host_form_only_gh_reads(self):
        """不足として通知すべき入力: gh が台帳の PR（#7）として読む URL の、番号の後の続き・host（下位の host・host が空の形・Unicode の綴り）・% の綴り。

        別の host（example.com、GHES）の同じ owner/repo/番号は、gh は台帳の PR と読まないが、host を問わず path を読む設計の
        受け入れた通知しすぎとして、ここに固定する。
        """
        hook = _hook_once(self.checkout, self.home)
        for token in (
            "https://github.com/acme/infra-gdd/pull/7x", "https://github.com/acme/infra-gdd/pull/7.",
            "https://github.com/acme/infra-gdd/pull/7-x", "'https://github.com/acme/infra-gdd/pull/7 '",
            "'https://github.com/acme/infra-gdd/pull/7/files x'", "https://www.github.com/acme/infra-gdd/pull/7",
            "https://github.com/acme/infra-gdd/pull/%37", "https://github.com:443/acme/infra-gdd/pull/7",
            "https://api.github.com/acme/infra-gdd/pull/7", "https:/acme/infra-gdd/pull/7",
            "https:///acme/infra-gdd/pull/7", "https://g\u0130thub.com/acme/infra-gdd/pull/7",
            "https://a\uff0f.github.com/acme/infra-gdd/pull/7", "https://a\uff03.github.com/acme/infra-gdd/pull/7",
            "https://example.com/acme/infra-gdd/pull/7",
        ):
            with self.subTest(token=token):
                self.assertTrue(_is_block(hook(f"gh pr merge {token}")))

    def test_other_pr_still_passes(self):
        """通知しすぎない: 台帳に無い PR は、対象を決められない形でも今どおり通す（git-cwd の経路は unknown を通す）。"""
        hook = _hook_once(self.checkout, self.home)
        for command in (
            "gh pr merge -st 7 8",
            "gh pr merge 8",
            "gh pr merge --new-flag 8",
            "gh pr merge -st 7 feature-x",
            "gh pr merge https://github.com/acme/infra-gdd/pull/8x",
        ):
            with self.subTest(command=command):
                self.assertTrue(_is_pass(hook(command)))


if __name__ == "__main__":
    unittest.main()
