"""steering write guard の fence の判定を lib/tasklist_parse._scan_fences に揃える。

``` の行ごとに反転するだけの判定は、4 連 fence の中の ```・`~~~` の中の ```・
info に ` を含む行で状態がずれ、fence の外の値（password: の値・AWS アカウント ID）を
見逃していた。hook の入口（stdin の payload）から判定までを通して見る。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import test_patch_section_scan as _patch_section_scan

VALIDATE = (Path(__file__).resolve().parent.parent / "hooks" / "scripts" / "validate-steering-write.py")

SECRETS = {
    "sensitive_value": "password: Zq8vLm2pXr",
    "aws_account_id": "AWS account: 210987654321",
}
# deny の本文に出る、検出器ごとの文言
MESSAGES = {
    "sensitive_value": "probable sensitive value",
    "aws_account_id": "probable AWS account ID",
}
# `#### Attempts` 節で免除される検出器（省略記法）の入力と文言
ELLIPSIS = "入力例: ...省略"
ELLIPSIS_MESSAGE = "omission marker"
TOKEN = "ghp_" + "abcdefghijklmnopqrstuvwxyz0123456789"

# fence の外に出た後の行を、旧判定は code block の中だと読み違えていた入口
DESYNC_PREFIXES = {
    "four_backtick_fence": "````\n```\n````\n",
    "tilde_fence": "~~~\n```\n~~~\n",
    # info に ` を含む行は fence にならない（CommonMark）。旧判定はここで反転した
    "info_with_backtick": "```で`囲む`例を下に書く\n",
}


def run_hook(tool_name: str, tool_input: dict) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as state:
        env = dict(os.environ, GDD_HOOK_STATE_DIR=state)
        result = subprocess.run(
            ["python3", str(VALIDATE)],
            input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
            capture_output=True,
            text=True,
            env=env,
        )
    return result.returncode, result.stderr


def write(content: str) -> tuple[int, str]:
    return run_hook("Write", {"file_path": ".steering/20261002-task/design.md", "content": content})


class FenceScanTest(unittest.TestCase):
    assertDeniedBy = _patch_section_scan.HookEntryTest.assertDeniedBy

    def assertAllowed(self, result: tuple[int, str]) -> None:
        code, err = result
        self.assertEqual(code, 0, err)

    def test_value_after_desynced_fence_is_denied(self) -> None:
        for prefix_name, prefix in DESYNC_PREFIXES.items():
            for secret_name, secret in SECRETS.items():
                with self.subTest(prefix=prefix_name, secret=secret_name):
                    self.assertDeniedBy(write(prefix + secret + "\n"), MESSAGES[secret_name])

    def test_value_inside_fence_opened_by_info_with_backtick_is_denied(self) -> None:
        # info に ` を含む行は開きではないので、続く ``` が開きになり、値は fence の外
        content = "```で`囲む`\n" + SECRETS["sensitive_value"] + "\n```\n"
        self.assertDeniedBy(write(content), MESSAGES["sensitive_value"])

    def test_value_after_desynced_fence_is_denied_on_edit(self) -> None:
        result = run_hook(
            "Edit",
            {
                "file_path": ".steering/20261002-task/design.md",
                "old_string": "x",
                "new_string": DESYNC_PREFIXES["tilde_fence"] + SECRETS["sensitive_value"] + "\n",
            },
        )
        self.assertDeniedBy(result, MESSAGES["sensitive_value"])

    def test_fence_does_not_pair_across_files_in_a_patch(self) -> None:
        # ApplyPatch の追加行を 1 本に連結すると、別ファイルの ``` と対になって値が fence の中に入る
        patch = (
            "*** Begin Patch\n"
            "*** Add File: docs/a.md\n+```\n"
            "*** Add File: .steering/20261002-task/design.md\n"
            "+" + SECRETS["sensitive_value"] + "\n+```\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(run_hook("ApplyPatch", {"patch": patch}), MESSAGES["sensitive_value"])

    def test_fence_does_not_pair_across_files_for_lines_starting_with_plus(self) -> None:
        # 内容が `++` で始まる行も、ファイルごとの追加行に入る
        patch = (
            "*** Begin Patch\n"
            "*** Add File: docs/a.md\n+```\n"
            "*** Add File: .steering/20261002-task/design.md\n"
            "+++" + SECRETS["sensitive_value"] + "\n+```\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(run_hook("ApplyPatch", {"patch": patch}), MESSAGES["sensitive_value"])

    def test_patch_line_starting_with_plus_plus_space_is_checked(self) -> None:
        # `*** ` の section の中の `+++ ` は unified diff の header ではなく、内容が `++ ` で始まる追加行
        patch = (
            "*** Begin Patch\n"
            "*** Add File: .steering/20261002-task/design.md\n"
            "+++ " + SECRETS["sensitive_value"] + "\n"
            "*** End Patch\n"
        )
        self.assertDeniedBy(run_hook("ApplyPatch", {"patch": patch}), MESSAGES["sensitive_value"])

    def test_examples_inside_closed_fence_are_allowed(self) -> None:
        body = "\n".join(SECRETS.values())
        for fence in ("```", "````", "~~~"):
            with self.subTest(fence=fence):
                self.assertAllowed(write(f"{fence}yaml\n{body}\n{fence}\n"))

    def test_value_after_unclosed_fence_is_denied(self) -> None:
        # 閉じ忘れの fence の後ろは記入例と本文を区別できないので、検査する側に倒す
        for secret_name, secret in SECRETS.items():
            with self.subTest(secret=secret_name):
                self.assertDeniedBy(write("```yaml\n" + secret + "\n"), MESSAGES[secret_name])

    def test_attempts_heading_inside_fence_does_not_open_exclude_section(self) -> None:
        # fence の中の記入例の見出しは構造ではない。外に出た後の省略記法を免除しない
        content = "```markdown\n#### Attempts\n```\n" + ELLIPSIS + "\n"
        self.assertDeniedBy(write(content), ELLIPSIS_MESSAGE)

    def test_comment_line_inside_fence_does_not_close_exclude_section(self) -> None:
        content = "#### Attempts\n```bash\n# 実行したコマンド\n```\n" + ELLIPSIS + "\n"
        self.assertAllowed(write(content))

    def test_attempts_heading_line_is_checked_for_secrets(self) -> None:
        # 節の見出し行は節に入るだけで、検出器を飛ばさない
        self.assertDeniedBy(write("#### Attempts " + TOKEN + "\n"), "probable secret marker")
        self.assertDeniedBy(write("#### 試行記録 " + SECRETS["sensitive_value"] + "\n"), MESSAGES["sensitive_value"])

    def test_attempts_heading_line_keeps_ellipsis_exemption(self) -> None:
        self.assertAllowed(write("#### Attempts（...省略）\n"))

    def test_closed_fence_delimiter_line_is_checked(self) -> None:
        self.assertDeniedBy(write("```sh " + TOKEN + "\nx\n```\n"), "probable secret marker")

    def test_unusual_inputs_do_not_crash_the_guard(self) -> None:
        # 例外は exit 2 に倒れるので、exit だけでなく検出器の文言と内部エラーの文言を見る
        for name, content in {
            "crlf": "```\r\nx\r\n```\r\n" + SECRETS["sensitive_value"] + "\r\n",
            "large": ("```\nx\n```\n" * 5000) + SECRETS["sensitive_value"] + "\n",
        }.items():
            with self.subTest(case=name):
                self.assertDeniedBy(write(content), MESSAGES["sensitive_value"])
        self.assertAllowed(write("```"))


if __name__ == "__main__":
    unittest.main()
