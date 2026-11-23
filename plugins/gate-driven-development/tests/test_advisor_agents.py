"""判断の相談役の agent 定義（references/autonomy.md 判断の手順、references/fixed-models.md の相談役の段落）。

`Agent` ツールは effort を引数で受けないので、相談役の model と effort は agent 定義の frontmatter で固定する。
dispatch の gate は、opus の相談役を model 省略のときだけ工程の検査から外し、`model` を明示した起動は判定する
（固定 reviewer と同じ。明示した model が定義より優先されるため）。fable の相談役は工程の tier に無いので、
model の値によらず外す。
"""
import unittest
from pathlib import Path

import test_agent_dispatch_model_gate_contract as gate_contract
from test_implementation_worker_agents import load_gate
from test_typed_dispatch_templates_contract import frontmatter

ROOT = Path(__file__).resolve().parents[1]

# 相談役の名前 → (model, effort)
ADVISORS = {
    "gdd-opus-advisor": ("opus", "high"),
    "gdd-opus-advisor-max": ("opus", "max"),
    "gdd-fable-advisor": ("fable", "medium"),
}


def criteria_items(path: Path) -> list[str]:
    """`## 選ぶときの基準` の節の、最初の段落（正本と写しで書き分ける前置き）より後の行を順に返す。

    基準の前に置く問い（箇条を含む）と、番号付きの基準（`0. ` など）の両方が入る。空行は除く。
    """
    items, inside, paragraphs = [], False, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside, paragraphs, in_paragraph = line == "## 選ぶときの基準", 0, False
        elif inside:
            if not line.strip():
                in_paragraph = False
            elif not in_paragraph:
                in_paragraph, paragraphs = True, paragraphs + 1
            if line.strip() and paragraphs > 1:
                items.append(line)
    return items


class TestAdvisorAgents(unittest.TestCase):
    def test_frontmatter_pins_model_and_effort(self):
        for name, (model, effort) in ADVISORS.items():
            with self.subTest(name=name):
                fm = frontmatter(ROOT / "agents" / f"{name}.md")
                self.assertEqual(fm.get("name"), name)
                self.assertEqual(fm.get("model"), model)
                self.assertEqual(fm.get("effort"), effort)

    def test_frontmatter_omits_claude_md(self):
        # 相談役は材料を場所で受けて自分で読むので、起動時の CLAUDE.md と memory の索引（最初の turn の
        # 約 30k token）を入れない。Claude Code の plugin agent の読み込みは "true" の文字列を真として読む
        for name in ADVISORS:
            with self.subTest(name=name):
                fm = frontmatter(ROOT / "agents" / f"{name}.md")
                self.assertEqual(fm.get("omitClaudeMd"), "true")

    def test_advisor_bodies_are_identical_after_the_frontmatter(self):
        # 3 本は model・effort と description だけが違う。本文の契約（出力の欄）は 1 つに保つ
        bodies = {
            (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8").split("\n---\n", 1)[1]
            for name in ADVISORS
        }
        self.assertEqual(len(bodies), 1)

    def test_advisor_criteria_copy_the_common_guardrails_section(self):
        # 正本は references/common-guardrails.md § 選ぶときの基準。相談役は利用する repo で動き、
        # plugin の references を読めないので、本文に同じ番号付きの文を写す
        canon = criteria_items(ROOT / "references" / "common-guardrails.md")
        self.assertTrue(canon)
        # 番号の基準の前に置く問いも写しに入る（番号の行だけを拾う抽出に戻ると、ここで落ちる）
        self.assertFalse(canon[0].startswith("0. "))
        self.assertTrue(any(line.startswith("0. ") for line in canon))
        for name in ADVISORS:
            with self.subTest(name=name):
                self.assertEqual(criteria_items(ROOT / "agents" / f"{name}.md"), canon)

    def test_gate_table_matches_the_opus_advisors(self):
        gate = load_gate()
        for name, (model, _) in ADVISORS.items():
            with self.subTest(name=name):
                expected = model if model == "opus" else ""
                self.assertEqual(gate.fixed_model(name), expected)
                self.assertEqual(gate.fixed_model(f"gate-driven-development:{name}"), expected)


class TestAdvisorExplicitModel(unittest.TestCase):
    def _run(self, subagent_type: str, model: str):
        import tempfile

        case = gate_contract.HookScriptContractTests()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            case._init_repo(path)
            case._write_active_state(path)
            case._write_steering(path, resume_from="gdd-requirements-gating")
            return case._run_hook(path, subagent_type, model)

    def test_opus_advisor_with_explicit_downgrade_is_flagged(self):
        for name in ("gdd-opus-advisor", "gdd-opus-advisor-max"):
            for subagent_type in (f"gate-driven-development:{name}", name):
                with self.subTest(subagent_type=subagent_type):
                    result = self._run(subagent_type, "sonnet")
                    self.assertEqual(result.returncode, 0)
                    self.assertIn("additionalContext", result.stdout)

    def _run_in_phase(self, next_action: str, subagent_type: str, model: str):
        import tempfile

        case = gate_contract.HookScriptContractTests()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            case._init_repo(path)
            case._write_active_state(path)
            case._write_steering(path, resume_from="human-check-waiting", next_action=next_action)
            return case._run_hook(path, subagent_type, model)

    def test_opus_fixed_agent_downgraded_in_a_sonnet_phase_is_flagged(self):
        # sonnet の工程は sonnet を許すが、opus に固定した agent を明示して下げるのは定義の上書きなので警告する。
        # 直し方は model の省略（明示した model は定義より優先される）
        for subagent_type in (
            "gate-driven-development:gdd-opus-advisor",
            "gdd-opus-advisor-max",
            "gate-driven-development:gdd-planning-reviewer",
        ):
            for model in ("sonnet", "claude-sonnet-5-5", "inherit"):
                with self.subTest(subagent_type=subagent_type, model=model):
                    result = self._run_in_phase("gdd-subagent-driven-implementation", subagent_type, model)
                    self.assertEqual(result.returncode, 0)
                    self.assertIn("additionalContext", result.stdout)
                    self.assertIn("model を省略", result.stdout)

    def test_opus_fixed_agent_with_explicit_opus_is_silent_in_a_sonnet_phase(self):
        for model in ("opus", "claude-opus-5-5"):
            with self.subTest(model=model):
                result = self._run_in_phase(
                    "gdd-subagent-driven-implementation", "gate-driven-development:gdd-opus-advisor", model
                )
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), "")

    def test_opus_fixed_agent_downgrade_message_asks_to_omit_model_in_an_opus_phase(self):
        result = self._run("gate-driven-development:gdd-opus-advisor", "sonnet")
        self.assertIn("model を省略", result.stdout)

    def test_fable_advisor_with_explicit_model_is_not_flagged(self):
        for subagent_type in ("gate-driven-development:gdd-fable-advisor", "gdd-fable-advisor"):
            with self.subTest(subagent_type=subagent_type):
                result = self._run(subagent_type, "fable")
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
