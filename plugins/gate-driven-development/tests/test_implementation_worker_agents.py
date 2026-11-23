"""実装 worker を task の複雑度で振り分ける agent 定義（2026-09-30）。

根拠（2026-09-20 実測、GDD を使う別の repo の subagent 全期間）:
- effort は opus・sonnet とも high がほぼ全部で、tier 表の `implementation=medium` は発火していなかった。
  効いていたのは agent 定義の frontmatter に書いた分だけだった（`Agent` ツールは effort を引数で受けない）。
- 実装の worker は opus が最も多く、sonnet より未指定が多くて、契約（sonnet + medium、risk のときだけ opus）と逆だった。

worker は `implementation`（`Complexity: standard`）・`general_heavy_risk`（`complex` か未宣言）・
`remediation_loop`（`Gate Rounds` ≥ 2）の 3 tier に 1 つずつ置く。frontmatter の model・effort を
`scripts/resolve-gdd-model.py` の値と突き合わせる。呼び出し側は model を省略して frontmatter に任せるので、
Agent の model を検査する hook が opus の worker を免除し、sonnet の worker を frontmatter の model で
工程に照らして判定することを、hook スクリプトの入口から確かめる。簡素化パス（gdd-code-simplifier）も sonnet に固定し、
同じく工程に照らして判定し、opus 必須の工程では簡素化パス向けの案内を出すことを確かめる。
"""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

import test_agent_dispatch_model_gate_contract as gate_contract
from test_typed_dispatch_templates_contract import RESOLVER, frontmatter

ROOT = Path(__file__).resolve().parents[1]

# tier → (agent 定義の名前, model の別名)
WORKER_BY_TIER = {
    "implementation": ("gdd-implementation-worker", "sonnet"),
    "general_heavy_risk": ("gdd-implementation-worker-heavy", "opus"),
    "remediation_loop": ("gdd-remediation-worker", "opus"),
}


def load_gate():
    path = ROOT / "hooks" / "scripts" / "lib" / "agent_dispatch_gate.py"
    spec = importlib.util.spec_from_file_location("implementation_worker_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestImplementationWorkerAgents(unittest.TestCase):
    def test_frontmatter_matches_the_resolver_for_each_tier(self):
        for tier, (name, model) in WORKER_BY_TIER.items():
            with self.subTest(tier=tier):
                path = ROOT / "agents" / f"{name}.md"
                self.assertTrue(path.is_file(), f"{path} が無い")
                fm = frontmatter(path)
                self.assertEqual(fm.get("name"), name)
                self.assertEqual(fm.get("model"), RESOLVER.TIER_TO_MODEL["claude_code"][tier])
                self.assertEqual(fm.get("model"), model)
                self.assertEqual(fm.get("effort"), RESOLVER.resolve_effort("claude_code", tier, None, {}))

    def test_hook_table_matches_the_agent_frontmatter(self):
        # hook は model 省略時に agent 定義の model で判定する。表の値を frontmatter と突き合わせる
        gate = load_gate()
        for subagent_type, model in gate.FIXED_MODEL_BY_SUBAGENT_TYPE.items():
            with self.subTest(subagent_type=subagent_type):
                name = subagent_type.split(":", 1)[1]
                self.assertEqual(frontmatter(ROOT / "agents" / f"{name}.md").get("model"), model)
        for name, _ in WORKER_BY_TIER.values():
            with self.subTest(worker=name):
                self.assertIn(f"gate-driven-development:{name}", gate.FIXED_MODEL_BY_SUBAGENT_TYPE)
                self.assertEqual(gate.fixed_model(name), gate.fixed_model(f"gate-driven-development:{name}"))

    def test_worker_names_in_the_docs_match_the_agents(self):
        # controller が読む選び方の正本（fixed-models.md）と手順 3 の worker 名が、agent 定義と一致する
        expected = {name for name, _ in WORKER_BY_TIER.values()}
        pattern = re.compile(r"gdd-(?:implementation|remediation)-worker(?:-heavy)?")
        fixed_models = (ROOT / "references" / "fixed-models.md").read_text(encoding="utf-8")
        paragraph = next(
            line for line in fixed_models.splitlines()
            if line.startswith("`gdd-subagent-driven-implementation` は `implementation` tier。")
        )
        skill = (ROOT / "skills" / "gdd-subagent-driven-implementation" / "SKILL.md").read_text(encoding="utf-8")
        step3 = next(line for line in skill.splitlines() if line.startswith("3. 実装は小さく分ける。"))
        for label, text in (("fixed-models", paragraph), ("step 3", step3)):
            with self.subTest(doc=label):
                self.assertEqual(set(pattern.findall(text)), expected)
                for name in expected:
                    self.assertIn(f"gate-driven-development:{name}", text)

    def test_opus_workers_are_exempt_and_the_sonnet_worker_is_judged(self):
        # opus はどの工程でも許されるので免除してよい。sonnet の worker は工程で判定する
        gate = load_gate()
        for tier, (name, model) in WORKER_BY_TIER.items():
            for subagent_type in (f"gate-driven-development:{name}", name):
                with self.subTest(subagent_type=subagent_type):
                    self.assertEqual(gate.is_exempt_from_phase_model_check(subagent_type, ""), model == "opus")

    def _run_in_phase(self, next_action, subagent_type, model=""):
        hook = gate_contract.HookScriptContractTests("test_hooks_json_registers_agent_matcher")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            hook._init_repo(path)
            hook._write_active_state(path)
            hook._write_steering(path, resume_from="human-check-waiting", next_action=next_action)
            return hook._run_hook(path, subagent_type, model)

    def test_hook_is_silent_when_a_worker_is_launched_without_model(self):
        # 入口（hook スクリプト）から: 実装の工程で model を省略して worker を起動しても、
        # 「model=\"sonnet\" を明示してください」を出さない（heavy・remediation が sonnet に下がるため）
        for tier, (name, _) in WORKER_BY_TIER.items():
            for subagent_type in (f"gate-driven-development:{name}", name):
                with self.subTest(tier=tier, subagent_type=subagent_type):
                    result = self._run_in_phase("gdd-subagent-driven-implementation", subagent_type)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout.strip(), "")

    def test_hook_warns_the_sonnet_worker_in_an_opus_phase(self):
        # model を省略しても、frontmatter の sonnet で opus 必須の工程を走らせるなら警告する
        for subagent_type in ("gate-driven-development:gdd-implementation-worker", "gdd-implementation-worker"):
            with self.subTest(subagent_type=subagent_type):
                result = self._run_in_phase("gdd-implementation-gating", subagent_type)
                self.assertEqual(result.returncode, 0)
                self.assertIn("additionalContext", result.stdout)
                self.assertIn("opus", result.stdout)

    def test_hook_names_the_agent_model_when_the_sonnet_worker_runs_an_opus_phase(self):
        # model を指定していない起動に「model=\"sonnet\" が指定されています」とは言わず、
        # この工程で使う worker（heavy・remediation）を model 省略で起動するよう案内する
        result = self._run_in_phase("gdd-implementation-gating", "gate-driven-development:gdd-implementation-worker")
        self.assertIn("additionalContext", result.stdout)
        self.assertNotIn("が指定されています", result.stdout)
        self.assertIn("agent 定義の model", result.stdout)
        for name in ("gdd-implementation-worker-heavy", "gdd-remediation-worker"):
            self.assertIn(name, result.stdout)
        # 設計どおりなら worker は実装の工程で起動する。先に Next Action を確かめるよう促し、受け渡しも伝える
        self.assertIn("Next Action", result.stdout)
        self.assertIn("## Worktree", result.stdout)
        self.assertIn("## Plugin Root", result.stdout)

    def test_hook_keeps_the_explicit_model_message_when_model_is_given(self):
        # model を明示した起動は、固定 model の agent でも「指定されています」の案内のまま
        result = self._run_in_phase(
            "gdd-implementation-gating", "gate-driven-development:gdd-implementation-worker", "sonnet"
        )
        self.assertIn("が指定されています", result.stdout)
        self.assertNotIn("agent 定義の model", result.stdout)

    def test_hook_tells_the_worker_contract_in_the_implementation_phase(self):
        # 実装の工程の案内は、worker を起動する場合に限って worker を勧め、Plugin Root の受け渡しまで伝える
        result = self._run_in_phase("gdd-subagent-driven-implementation", "general-purpose")
        self.assertIn("worker を起動するなら", result.stdout)
        self.assertIn("## Worktree", result.stdout)
        self.assertIn("## Plugin Root", result.stdout)
        self.assertIn("worker 以外", result.stdout)

    def test_hook_points_general_purpose_to_the_workers_in_the_implementation_phase(self):
        # 実装の工程で model 省略の general-purpose には、sonnet の明示ではなく typed worker を案内する
        result = self._run_in_phase("gdd-subagent-driven-implementation", "general-purpose")
        self.assertEqual(result.returncode, 0)
        self.assertIn("additionalContext", result.stdout)
        self.assertIn("gdd-implementation-worker", result.stdout)
        self.assertNotIn('model=\\"sonnet\\" を明示', result.stdout)

    def test_worker_bodies_are_identical_after_the_frontmatter(self):
        # 3 つの worker は model・effort と description だけが違う。本文の契約は 1 つに保つ
        bodies = set()
        for name, _ in WORKER_BY_TIER.values():
            text = (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8")
            bodies.add(text.split("\n---\n", 1)[1])
        self.assertEqual(len(bodies), 1)

    def test_simplifier_runs_on_sonnet_in_the_implementation_phase(self):
        # 入口（hook スクリプト）から: 簡素化パス（SKILL.md 14a）は実装の工程で model を省略して起動する。
        # sonnet に固定したので、実装の工程では黙り、opus 必須の工程では警告する
        gate = load_gate()
        for subagent_type in ("gate-driven-development:gdd-code-simplifier", "gdd-code-simplifier"):
            with self.subTest(subagent_type=subagent_type):
                self.assertEqual(gate.fixed_model(subagent_type), "sonnet")
                self.assertFalse(gate.is_exempt_from_phase_model_check(subagent_type, ""))
                quiet = self._run_in_phase("gdd-subagent-driven-implementation", subagent_type)
                self.assertEqual(quiet.returncode, 0)
                self.assertEqual(quiet.stdout.strip(), "")
                warned = self._run_in_phase("gdd-implementation-gating", subagent_type)
                self.assertEqual(warned.returncode, 0)
                self.assertIn("additionalContext", warned.stdout)
                self.assertIn("opus", warned.stdout)
                # 警告は簡素化パスの案内で、worker の起動の案内ではない
                context = json.loads(warned.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("gdd-subagent-driven-implementation", context)
                self.assertNotIn("gdd-implementation-worker-heavy", context)


if __name__ == "__main__":
    unittest.main()
