"""`_merge_gate_input_classes` の前提（hook が payload を読む場所）と、組ごとの起動が実際の起動と同じ結果になること。"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from _merge_gate_input_classes import HOOK_SCRIPT, hook_input_class, once_per_input_class
from _merge_gate_support import _new_repo_with_marker_and_pr, _run_hook


class HookPayloadReadsTests(unittest.TestCase):
    def test_hook_reads_the_payload_only_where_the_input_class_looks(self):
        # 組の鍵は、この 2 か所（`merge` の粗い絞り込み・埋め込みの python）から作る。
        # hook が payload をほかの場所で読むようになったら、鍵に足すまで組ごとの起動は使えない。
        reads = [line.strip() for line in HOOK_SCRIPT.read_text(encoding="utf-8").splitlines()
                 if re.search(r'"\$PAYLOAD"|\$\{PAYLOAD[^_]', line)]
        self.assertEqual(reads, [
            'case "$PAYLOAD" in',
            "done < <(printf '%s' \"$PAYLOAD\" | python3 -c '",
        ])


class OncePerInputClassTests(unittest.TestCase):
    def test_results_match_a_hook_launch_for_every_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            (home / ".claude").mkdir(parents=True)
            repo = _new_repo_with_marker_and_pr(root, "widgets", pr=7)
            payloads = [{"tool_input": {"command": c}}
                        for c in ("gh pr merge 7", "gh pr merge 007", "gh pr merge 8")]
            # 7 と 007 は hook に同じ入力が渡り、8 は別の組になる
            keys = [hook_input_class(p, repo) for p in payloads]
            self.assertEqual(keys[0], keys[1])
            self.assertNotEqual(keys[0], keys[2])

            launches = []

            def run(payload):
                launches.append(payload)
                return _run_hook(payload, repo, home)

            once = once_per_input_class(run, repo)
            for payload in payloads:
                with self.subTest(payload=payload):
                    self.assertEqual(once(payload).stdout, _run_hook(payload, repo, home).stdout)
            self.assertEqual(len(launches), 2)
            self.assertIn('"hookEventName": "PreToolUse"', once(payloads[0]).stdout)
            self.assertEqual(once(payloads[2]).stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
