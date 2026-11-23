"""マージより後ろの `cd` は、マージの実行先を変えない。

`gh pr merge … && cd <dir> && git pull` のように、マージの後で別のディレクトリへ
移る形を、実行先を 1 つに決められない（`pr-target-unresolvable`）として止めていた。
マージを囲む構文（ループ・関数・波括弧・サブシェル・入れ子 shell）が無いときだけ、
マージを含む segment より後ろを実行先の判定から外す。
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from _timing_budget import timing_budget
from _merge_gate_input_classes import once_per_input_class
from _merge_gate_support import _init_named_repo, _run_hook, _write_marker_only
from _paths import PLUGIN_ROOT

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.gh_command_parse import (  # noqa: E402
    _extract_cd_target,
    _through_merge_segment,
    _tokenize,
    parse_gh_pr_merge,
)

MERGE = "gh pr merge https://github.com/acme/widgets/pull/7 --merge"
MERGE_BY_NUMBER = "gh pr merge 7 --merge"


class CdAfterMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.launch = _init_named_repo(self.tmp, "launch")
        _write_marker_only(self.launch, active=False)
        self.other = _init_named_repo(self.tmp, "other")
        # どのテストも repo の状態を途中で変えないので、hook に同じ入力が渡る行は 1 回だけ起動する
        self._hook = once_per_input_class(
            lambda payload: _run_hook(payload, self.launch, self.home), self.launch)

    def _run(self, command):
        return self._hook({"tool_input": {"command": command}})

    def _decision(self, command):
        result = self._run(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    # 対象を番号だけで指す merge で見る（URL で明示した merge は実行先を見ないので、切り出しが
    # 壊れても判定が変わらず、切り出しの退行を検出できない）。
    def test_cd_after_the_merge_does_not_change_the_decision(self):
        MERGE = MERGE_BY_NUMBER
        alone = self._decision(MERGE)
        self.assertNotIn('"hookEventName": "PreToolUse"', alone)
        for tail in (
            f" && cd {self.other} && git pull --ff-only",
            f"; cd {self.other}",
            f" || cd {self.other}",
            f" | cd {self.other}",
            f" && gh pr view 7 && cd {self.other} && git log --oneline -1",
            f" && pushd {self.other} && popd",
            f" 2>&1 | tail -2; cd {self.other} && git pull",
            f" && cd {self.other}\ngit pull",
            # 改行はコマンドの区切り（bash・zsh とも merge を実行してから cd する。`;` と同じ）。
            f"\ncd {self.other}",
            f" && cd {self.other} || cd {self.launch}",
            " && cd ~/other",
        ):
            with self.subTest(tail=tail):
                self.assertEqual(self._decision(MERGE + tail), alone)

    def test_cd_before_and_after_the_merge_is_judged_by_the_one_before(self):
        before = f"cd {self.launch} && {MERGE_BY_NUMBER}"
        alone = self._decision(before)
        self.assertNotIn('"hookEventName": "PreToolUse"', alone)
        self.assertEqual(self._decision(f"{before} && cd {self.other}"), alone)

    def test_constructs_that_can_rerun_the_merge_still_block(self):
        # マージを囲む構文があると、後ろの cd の後でマージがまた走りうる。今までどおり不足として通知する。
        # 対象を番号だけで指す merge で見る（URL・`-R owner/name` で明示した merge は、gh の対象が
        # 実行先に依存しないので、cd の位置によらず root の証跡で検査する。test_merge_gate_explicit_target）。
        MERGE = MERGE_BY_NUMBER
        for command in (
            f"for p in 1 2; do {MERGE}; cd {self.other}; done",
            f"while true; do {MERGE}; cd {self.other}; done",
            f"until false; do {MERGE}; cd {self.other}; done",
            f"select p in a; do {MERGE}; cd {self.other}; done",
            f"case x in x) {MERGE}; cd {self.other};; esac",
            f"f(){{ {MERGE}; }}; cd {self.other}; f",
            f"f () {{ {MERGE}; }}; cd {self.other}; f",
            f"function f {{ {MERGE}; }}; cd {self.other}; f",
            f"{{ {MERGE}; cd {self.other}; }}",
            f"( {MERGE} ); cd {self.other}",
            f"bash -c '{MERGE}; cd {self.other}'",
            f"{MERGE} & cd {self.other}",
            f"cd {self.other}; {MERGE}",
            # zsh の繰り返し構文（`repeat`・`foreach`）も、後ろの cd の後でマージを走らせる。
            f"repeat 2 {MERGE} && cd {self.other}",
            f"repeat 2; {MERGE} && cd {self.other}",
            f"foreach p (1 2); {MERGE}; cd {self.other}; end",
            f"cd {self.other} && {MERGE} && cd {self.launch}",
            f"{MERGE} && eval true && cd {self.other}",
            # 予約語が単独の token にならない形（縮退・バッククォート・語の途中の行継続）と、
            # 後で走るマージ（trap）。切り出してよいと言える形の外なので全体を見る。
            f":;while true;do {MERGE} && cd {self.other};done;git commit -m 'note <<E\nx'",
            f"`repeat 2 {MERGE} && cd {self.other}`",
            f"rep\\\neat 2 {MERGE} && cd {self.other}",
            f"trap '{MERGE}' EXIT; gh pr merge 8 && cd {self.other}",
            f"{MERGE} && X=$(pwd) && cd {self.other}",
            f"bash -c \"cd {self.other} && {MERGE}\"; cd {self.launch}",
            f"time {MERGE} && cd {self.other}",
            # zsh の括弧なしの `foreach` は位置パラメータで回る。
            f"set -- 1 2; foreach p; {MERGE}; cd {self.other}; end",
            # 同じ文字列の中の alias は eval を通したときだけ効く。eval は入れ子 shell として全体を見る。
            f"alias rr=rep'eat'; eval 'rr 2 {MERGE} && cd {self.other}'",
        ):
            with self.subTest(command=command):
                stdout = self._decision(command)
                self.assertIn('"hookEventName": "PreToolUse"', stdout)


class CdAfterMergeUnitTests(unittest.TestCase):
    def test_cd_after_the_merge_is_not_a_chdir_intent(self):
        self.assertFalse(parse_gh_pr_merge(f"{MERGE} && cd /x", "", "/repo")["cd_intent"])

    def test_extract_cd_target_ignores_the_cd_after_the_merge(self):
        # 本番経路（`parse_gh_pr_merge`）と同じく、マージより後ろの cd を見ない。
        tokens = _tokenize(f"cd /launch && {MERGE} && cd /other")
        self.assertEqual(_extract_cd_target(tokens), "/launch")

    def test_cut_needs_only_and_or_semicolon_before_the_merge(self):
        # マージより前にパイプ・`||` があると切らない（後ろの cd も数えて main と同じ判定）。
        for op in ("|", "||"):
            command = f"cd /Q {op} {MERGE} && cd /R"
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertIsNone(result["cd_target"])
                self.assertTrue(result["cd_intent"])

    def test_cd_before_an_or_still_names_the_target(self):
        # `cd X || exit 1` の cd は成功すれば cwd を変える。main と同じく X を実行先にする。
        self.assertEqual(
            parse_gh_pr_merge(f"cd /W || exit 1; {MERGE}", "", "/repo")["cd_target"], "/W"
        )

    def test_cd_followed_by_redirection_or_sequence_is_still_the_target(self):
        for command in (
            f"cd /Q && {MERGE}",
            f"cd /Q; {MERGE}",
            f"cd /Q >/dev/null && {MERGE}",
            f"cd /Q 2>&1 && {MERGE}",
            f"cd /Q\n{MERGE}",
            f"cd /Q && {MERGE} 2>&1 | tail -2",
        ):
            with self.subTest(command=command):
                self.assertEqual(parse_gh_pr_merge(command, "", "/repo")["cd_target"], "/Q")

    def test_many_segments_before_the_merge_are_read_in_linear_time(self):
        # segment ごとに token 列全体を写すと 2 乗になり、hook の timeout（10 秒）を超えて通る。
        # 解析全体は負荷で揺れるので、切り出しの CPU 時間だけを測る（2 乗なら閾値を超え、線形なら閾値よりずっと短い）。
        command = "a;" * 50_000 + MERGE + " && cd /x"
        tokens = _tokenize(command)
        with timing_budget() as timing:
            cut = _through_merge_segment(command, tokens, False)
        self.assertLess(timing.cpu_seconds, 1.0, f"wall {timing.wall_seconds:.2f}s")
        self.assertEqual(cut, tokens[:-3])
        self.assertTrue(parse_gh_pr_merge("a;" * 50_000 + MERGE, "", "/repo")["is_merge"])


if __name__ == "__main__":
    unittest.main()
