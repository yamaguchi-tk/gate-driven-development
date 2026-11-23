"""往復（remediation loop）発生時の model routing を Opus 5 + max に昇格する契約。

実測根拠（2026-09-02 の dogfooding）: ある task は Opus 5 subagent で
implementation-gating を何度往復しても収束せず、方式転換で撤回した。
ほかの task は少ない gate で収束した。往復が始まった時点（同一 Current Task で
`changes_requested` が累計 2 回目 = `tasklist.md` の `Gate Rounds` ≥ 2。route 非依存）で
「なぜ収束しないか」の判断と修正の質を上げるため、往復に関わる 3 工程を昇格する:

1. route 判断（gdd-systematic-debugging subagent）
2. 再レビュー（gdd-implementation-gating の gate subagent 自体と escalation 先 reviewer を
   `model="opus"` で起動。inline review でも subagent になる）
3. remediation 実装（worker subagent の dispatch 必須、inline 修正不可）

昇格先は当初 Fable + high だった（ユーザー判断 2026-09-02）。2026-09-08 のユーザー指示
「Fable はよっぽど難解なとき以外は使わない」と、2026-09-05 の比較実験で Fable high が
Opus max より検出が少なかったことから、Opus 5 + max に戻した。

正本は `references/fixed-models.md` の tier 表（`remediation_loop` tier）。本ファイルは、
resolver の値と、その表の `remediation_loop` の行（Claude Code 列）を突き合わせる。
開始条件（`Gate Rounds` の数値）は本ファイルに機械検査なし。
"""

import importlib.util
import json
import subprocess
import sys
import unittest

from _paths import PLUGIN_ROOT as ROOT
RESOLVER = ROOT / "scripts" / "resolve-gdd-model.py"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _resolve(*args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(RESOLVER), *args, "--json"],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def _load_resolver():
    spec = importlib.util.spec_from_file_location("gdd_resolver_remediation_loop", RESOLVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fixed_models_row(tier: str) -> list[str]:
    for line in read("references/fixed-models.md").splitlines():
        if line.startswith(f"| `{tier}` |"):
            return [cell.strip() for cell in line.strip().strip("|").split("|")]
    raise AssertionError(f"fixed-models.md に {tier} の行が無い")


class RemediationLoopModelRoutingTests(unittest.TestCase):
    def test_resolver_resolves_remediation_loop_for_every_runtime(self) -> None:
        # Cursor / Codex は worker runner 経由でしか model が適用されないので、
        # --complexity remediation_loop で tier を明示指定できることが契約
        expected = {
            "claude_code": ("opus", "xhigh"),
            "cursor": ("grok-4.6", "high"),
            "codex": ("gpt-5.6-sol", "high"),
        }
        for runtime, (model, effort) in expected.items():
            resolved = _resolve(
                "--runtime", runtime,
                "--phase", "gdd-systematic-debugging",
                "--complexity", "remediation_loop",
            )
            self.assertEqual(resolved["tier"], "remediation_loop", runtime)
            self.assertEqual(resolved["model"], model, runtime)
            self.assertEqual(resolved["effort"], effort, runtime)

    def test_fixed_models_row_matches_resolver(self) -> None:
        # references/fixed-models.md の remediation_loop の行（Claude Code 列）を、resolver の値と突き合わせる
        resolver = _load_resolver()
        model = resolver.TIER_TO_MODEL["claude_code"]["remediation_loop"]
        effort = resolver.resolve_effort("claude_code", "remediation_loop", None, {})
        column = _fixed_models_row("remediation_loop")[1]
        self.assertIn(f"`{model}`", column)
        self.assertIn(f"effort={effort}`", column)

    def test_worker_runner_forwards_complexity(self) -> None:
        runner = read("scripts/run-gdd-worker.py")
        self.assertIn('"remediation_loop"', runner)
        self.assertIn('cmd.extend(["--complexity", complexity])', runner)


if __name__ == "__main__":
    unittest.main()
