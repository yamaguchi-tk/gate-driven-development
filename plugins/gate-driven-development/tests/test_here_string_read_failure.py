"""gate が値を 1 行ずつ読むループは、リダイレクトを使わない。

here-string（`<<<`）は一時ファイルで作られることがある（bash 5.1 未満、または pipe の容量を
超えるとき）。作れないとループは回らずに 1 を返し、bash 4 以上は set -e で出力なしのまま
終わる（Claude Code は止めない）。読めないときの分岐を足すと、その分岐が別の経路を通す。
リダイレクトの失敗は手元では起こせないので、ループの形を固定し、空の入力で止まる側に
なることを確かめる。
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
import test_pre_pr_gate_contract as pre_pr

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
REDIRECTS = ("<<<", "< <(", "done <")


def _between(path: Path, start: str, end: str) -> str:
    text = path.read_text(encoding="utf-8")
    i = text.index(start)
    return text[i:text.index(end, i)]


class LoopsDoNotRedirectTests(unittest.TestCase):
    def test_pre_pr_gate_reads_parse_output_without_redirect(self) -> None:
        loop = _between(SCRIPTS / "run-pre-pr-gate-hook.sh", '|| PARSE_OUTPUT=""', '[[ "$PARSED" == "true" ]]')
        self.assertIn("$PARSE_OUTPUT", loop)
        for redirect in REDIRECTS:
            self.assertNotIn(redirect, loop)

    def test_merge_gate_reads_other_remotes_without_redirect(self) -> None:
        loop = _between(SCRIPTS / "run-merge-gate-hook.sh", "_others=", '_exec_repo="')
        self.assertIn("_repo=\"\"", loop)
        for redirect in REDIRECTS:
            self.assertNotIn(redirect, loop)


class PrePrGateEmptyParseOutputTests(unittest.TestCase):
    def test_empty_parse_output_blocks_inside_active_gdd(self) -> None:
        # fail-open ケース「判定できないときに通ってしまう」: 解析の出力が空なら、解析に失敗した
        # ものとして active GDD の中で不足として通知する。
        h = pre_pr.PrePrGateContractTests("run")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            h._init_repo(repo)
            h._write_local_state(repo)
            h._write_steering(repo, next_action="gdd-completion-check")
            hooks = root / "plugin" / "hooks"
            shutil.copytree(PLUGIN_ROOT / "hooks", hooks)
            hook = hooks / "scripts" / "run-pre-pr-gate-hook.sh"
            text = hook.read_text(encoding="utf-8")
            anchor = '2>/dev/null)" || PARSE_OUTPUT=""\n'
            self.assertEqual(text.count(anchor), 1)
            hook.write_text(text.replace(anchor, anchor + 'PARSE_OUTPUT=""\n'), encoding="utf-8")
            original = pre_pr.HOOK
            pre_pr.HOOK = hook
            try:
                result = h._run_hook(repo, "gh pr create --title t --body ok")
            finally:
                pre_pr.HOOK = original
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)


if __name__ == "__main__":
    unittest.main()
