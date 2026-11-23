"""指摘の検証役の agent 定義（references/finding-dispositions.md § 検証役）。

model と effort は agent 定義の frontmatter で固定する。dispatch の gate は、model 省略の起動を
工程の検査から外し、`model` を明示した起動は判定する（Opus の相談役と同じ）。
"""
import tempfile
import unittest
from pathlib import Path

import test_agent_dispatch_model_gate_contract as gate_contract
from test_implementation_worker_agents import load_gate
from test_typed_dispatch_templates_contract import frontmatter

ROOT = Path(__file__).resolve().parents[1]
NAME = "gdd-finding-verifier"


def run_hook(subagent_type: str, model: str, **steering):
    case = gate_contract.HookScriptContractTests()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        case._init_repo(path)
        case._write_active_state(path)
        case._write_steering(path, **steering)
        return case._run_hook(path, subagent_type, model)


class TestFindingVerifierAgent(unittest.TestCase):
    def test_frontmatter_pins_model_effort_and_read_only_tools(self):
        fm = frontmatter(ROOT / "agents" / f"{NAME}.md")
        self.assertEqual(fm.get("name"), NAME)
        self.assertEqual(fm.get("model"), "opus")
        self.assertEqual(fm.get("effort"), "high")
        self.assertEqual({t.strip() for t in fm.get("tools", "").split(",")}, {"Read", "Grep", "Glob"})

    def test_gate_table_pins_opus_with_either_name(self):
        gate = load_gate()
        self.assertEqual(gate.fixed_model(NAME), "opus")
        self.assertEqual(gate.fixed_model(f"gate-driven-development:{NAME}"), "opus")

    def test_dispatch_without_model_is_not_flagged(self):
        # 実際の起動は impl-gating と独立レビューの中。opus を求める工程でも警告しない
        for resume_from in ("gdd-implementation-gating", "gdd-completion-check"):
            for subagent_type in (f"gate-driven-development:{NAME}", NAME):
                with self.subTest(resume_from=resume_from, subagent_type=subagent_type):
                    result = run_hook(subagent_type, "", resume_from=resume_from)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout.strip(), "")

    def test_explicit_downgrade_in_a_sonnet_phase_is_flagged_by_the_fixed_table(self):
        # sonnet の工程は sonnet を許すので、警告は固定表との照合からだけ出る
        result = run_hook(
            f"gate-driven-development:{NAME}",
            "sonnet",
            resume_from="human-check-waiting",
            next_action="gdd-subagent-driven-implementation",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("model を省略", result.stdout)


if __name__ == "__main__":
    unittest.main()
