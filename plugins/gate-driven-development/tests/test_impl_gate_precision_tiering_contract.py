"""implementation-gating への精度二層化の適用と artifact 肥大の抑制。

実測根拠（2026-09-02 の dogfooding）: v0.37.0 の精度二層化は planning 側では
機能したが、実装フェーズで 1 つの task が長時間 impl-gate を繰り返し、
同一箇所に finding が出続けて発散した。既存 Loop Safety
（3/3 soft・5/5 hard）が効かなかった構造は次の 4 点:

1. hard cap で人間に戻した後の再ループに上限がない（承認後も Attempt が続いた）
2. requirements § Honest Limitations に既載の限界（証跡は自己申告・偽装は防げない）
   にまで「安全境界 = blocking」が適用され、reviewer が諦めた領域の欠陥を要求し続けた
3. 同一箇所への連続 finding を「方式そのものの問題」として扱う規則がない
4. requirements だけ 300 行目安で抑えた結果、肥大が tasklist・design・
   adr・state へ移動した。gate や route 判断のたびに大きなファイルを
   読み書きするため、1 ステップが大きく遅くなった

固定する契約: artifact サイズの上限超過の通知（hook。止めずに additionalContext で知らせる）。
"""

import json
import os
import subprocess
import tempfile
import unittest

from _paths import PLUGIN_ROOT as ROOT
HOOK = ROOT / "hooks" / "scripts" / "validate-steering-write.py"


class ArtifactSizeContractTests(unittest.TestCase):

    def _run_hook(self, file_path: str, content: str, state_dir: str) -> tuple[int, dict, str]:
        payload = {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}}
        env = dict(os.environ, GDD_HOOK_STATE_DIR=state_dir)
        proc = subprocess.run(
            ["python3", str(HOOK)], input=json.dumps(payload),
            capture_output=True, text=True, timeout=30, env=env,
        )
        data = json.loads(proc.stdout) if proc.returncode == 0 and proc.stdout.strip() else {}
        return proc.returncode, data, proc.stdout + proc.stderr

    def test_hook_notifies_oversized_design_without_blocking(self) -> None:
        # 上限を超えて増える write は止めずに、main に届く additionalContext で通知する。
        # state.md は既存の canonical field 検査があるため、素の内容で通る design.md で検証する
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(f"{tmp}/.steering/t")
            target = f"{tmp}/.steering/t/design.md"
            big = "## Summary Brief\n" + ("- 変更点の要約: hook 配線と証跡パーサを追加する\n" * 1500)
            size = len(big.encode())
            self.assertGreater(size, 60_000)
            code, data, out = self._run_hook(target, big, f"{tmp}/hook-state")
            self.assertEqual(code, 0, out)
            self.assertNotIn("Blocked", out)
            self.assertNotIn("[artifact size]", out)
            context = data.get("hookSpecificOutput", {}).get("additionalContext", "")
            self.assertIn("[steering size]", context)
            self.assertIn(f"design.md is {size} bytes after this write", context)
            self.assertIn("over the 60000 byte limit", context)
            self.assertIn("worklog.md", context)

    def test_hook_stays_quiet_for_small_design(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(f"{tmp}/.steering/t")
            target = f"{tmp}/.steering/t/design.md"
            code, _, out = self._run_hook(target, "## Summary Brief\n- 変更点の要約: 1 行\n", f"{tmp}/hook-state")
            self.assertEqual(code, 0, out)
            self.assertNotIn("[steering size]", out)
            self.assertNotIn("[artifact size]", out)


if __name__ == "__main__":
    unittest.main()
