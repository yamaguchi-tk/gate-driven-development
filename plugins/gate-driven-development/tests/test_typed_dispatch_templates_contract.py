"""`references/subagent-dispatch.md` の各 Agent Template は、
phase の tier に合う `subagent_type` と `model` を持つ（読む対象の欄は本ファイルに機械検査なし）。

根拠（2026-09-20 実測、GDD を使う別の repo の GDD セッション）:
- Agent 呼び出しの約半分が `subagent_type` 未指定で、prompt はどれも
  「skills/<phase>/SKILL.md を読んで phase を実行」だった。費用の大きな割合がこの未指定の subagent だった。
- `Agent` ツールは `effort` を引数で受けない。effort を固定できるのは agent 定義の
  frontmatter だけなので、Template の `effort="medium"` は効いていなかった。

検査は閉じた文法だけで行う（自由文の意味判定はしない）: フェンス内の `Agent(` ブロック、
`subagent_type=` / `model=` の行、`## Phase` の値。
"""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DISPATCH = (ROOT / "references" / "subagent-dispatch.md").read_text(encoding="utf-8")

# Template の description（既存テストが同じ文字列で Template を探している）→ 主となる phase
TEMPLATE_PHASES = {
    "GDD planning: brainstorming + requirements-gating": "gdd-brainstorming",
    "GDD design-gating": "gdd-design-gating",
    "GDD task-breakdown": "gdd-task-breakdown",
    "GDD TDD: RED preparation": "gdd-test-driven-development",
    "GDD implementation-gating": "gdd-implementation-gating",
    "GDD completion-check": "gdd-completion-check",
}

# tier → (subagent_type, agent 定義ファイル名, model の別名, effort)
# resolve-gdd-model.py の値との突き合わせ（コードが読む値との照合）:
# - Template の model と TIER_TO_MODEL: test_subagent_type_and_model_follow_the_phase_tier
# - agent 定義の frontmatter の effort と resolve_effort: test_agent_frontmatter_pins_model_and_effort_per_tier
# - references/fixed-models.md の tier の行と TIER_TO_MODEL・resolve_effort: test_fixed_models_row_matches_resolver
AGENT_BY_TIER = {
    "formal_gate": (
        "gate-driven-development:gdd-formal-gate-runner",
        "gdd-formal-gate-runner",
        "opus",
        "high",
    ),
    "light_task": (
        "gate-driven-development:gdd-light-task-runner",
        "gdd-light-task-runner",
        "sonnet",
        "medium",
    ),
}


def load_resolver():
    path = ROOT / "scripts" / "resolve-gdd-model.py"
    spec = importlib.util.spec_from_file_location("typed_dispatch_resolver", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RESOLVER = load_resolver()


def agent_blocks(text: str) -> list[str]:
    """フェンス内で `Agent(` から始まるブロックを、閉じ ``` の手前まで返す。"""
    blocks = []
    for match in re.finditer(r"^```\n(Agent\(\n.*?)^```$", text, flags=re.S | re.M):
        blocks.append(match.group(1))
    return blocks


def block_for(description: str) -> str:
    needle = f'description="{description}"'
    hits = [b for b in agent_blocks(DISPATCH) if needle in b]
    assert len(hits) == 1, f"{description}: Template が {len(hits)} 個ある"
    return hits[0]


def phase_of(block: str) -> str:
    """`## Phase` の次の 1 行全体（runner は行全体を skills/<Phase>/SKILL.md に展開する）。"""
    match = re.search(r"^\s*## Phase\n([^\n]*)\n", block, flags=re.M)
    assert match, "## Phase 欄が無い"
    return match.group(1).strip()


def fixed_models_row(tier: str) -> list[str]:
    """references/fixed-models.md の tier 表から、tier の行をセルに分けて返す。"""
    for line in (ROOT / "references" / "fixed-models.md").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| `{tier}` |"):
            return [cell.strip() for cell in line.strip().strip("|").split("|")]
    raise AssertionError(f"fixed-models.md に {tier} の行が無い")


def frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n"), f"{path.name}: frontmatter が無い"
    end = content.index("\n---\n", 4)
    data = {}
    for line in content[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
    return data


class TestEveryTemplateIsTyped(unittest.TestCase):
    def test_all_six_templates_are_found(self):
        self.assertEqual(len(agent_blocks(DISPATCH)), len(TEMPLATE_PHASES))

    def test_subagent_type_and_model_follow_the_phase_tier(self):
        for description, phase in TEMPLATE_PHASES.items():
            with self.subTest(template=description):
                block = block_for(description)
                tier = RESOLVER.PHASE_TO_TIER[phase]
                subagent_type, _, model, _ = AGENT_BY_TIER[tier]
                self.assertIn(f'subagent_type="{subagent_type}"', block)
                self.assertIn(f'model="{model}"', block)
                # hook（agent_dispatch_gate）が判定する model と、Template の model が一致する
                self.assertEqual(RESOLVER.TIER_TO_MODEL["claude_code"][tier], model)

    def test_phase_field_names_the_primary_phase_and_resolves_to_a_skill(self):
        for description, phase in TEMPLATE_PHASES.items():
            with self.subTest(template=description):
                block = block_for(description)
                self.assertEqual(phase_of(block), phase)
                self.assertTrue((ROOT / "skills" / phase / "SKILL.md").is_file())

    def test_runner_existence_check_passes_for_every_template_phase_value(self):
        # runner は `<Plugin Root>/skills/<Phase>/SKILL.md` が無いと state を更新せず停止する。
        # Template の `## Phase` の値（行全体）をその検査に通す（複合値・注釈付きの値は落ちる）。
        for description in TEMPLATE_PHASES:
            with self.subTest(template=description):
                phase = phase_of(block_for(description))
                self.assertRegex(phase, r"^gdd-[a-z-]+$", f"Phase は単一の phase 名だけにする: {phase!r}")
                self.assertTrue((ROOT / "skills" / phase / "SKILL.md").is_file(), phase)


class TestRunnerAgentDefinitions(unittest.TestCase):
    def test_agent_frontmatter_pins_model_and_effort_per_tier(self):
        for tier, (_, filename, model, effort) in AGENT_BY_TIER.items():
            with self.subTest(tier=tier):
                path = ROOT / "agents" / f"{filename}.md"
                self.assertTrue(path.is_file(), f"{path} が無い")
                fm = frontmatter(path)
                self.assertEqual(fm.get("name"), filename)
                self.assertEqual(fm.get("model"), model)
                self.assertEqual(fm.get("effort"), effort)
                self.assertEqual(RESOLVER.resolve_effort("claude_code", tier, None, {}), effort)

    def test_fixed_models_row_matches_resolver(self):
        # references/fixed-models.md の tier 表（Claude Code 列）を、resolver の値と突き合わせる
        for tier in AGENT_BY_TIER:
            with self.subTest(tier=tier):
                model = RESOLVER.TIER_TO_MODEL["claude_code"][tier]
                effort = RESOLVER.resolve_effort("claude_code", tier, None, {})
                column = fixed_models_row(tier)[1]
                self.assertIn(f"`{model}`", column)
                self.assertIn(f"effort={effort}`", column)

    def test_runner_agents_are_not_in_the_hook_exemption_set(self):
        # Template が model を明示するので、hook は通常どおり工程で判定する。免除集合には入れない。
        gate_path = ROOT / "hooks" / "scripts" / "lib" / "agent_dispatch_gate.py"
        spec = importlib.util.spec_from_file_location("typed_dispatch_gate", gate_path)
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        for tier, (subagent_type, _, model, _) in AGENT_BY_TIER.items():
            with self.subTest(tier=tier):
                self.assertNotIn(subagent_type, gate.MODEL_FIXED_SUBAGENT_TYPES)
                self.assertFalse(gate.is_exempt_from_phase_model_check(subagent_type, model))
                # model を省略しても免除されない（集合に入れた瞬間に落ちる。model が非空なら常に False になる上の行では守れない）
                self.assertFalse(gate.is_exempt_from_phase_model_check(subagent_type, ""))

    def test_hook_accepts_each_template_model_for_its_phase(self):
        gate_path = ROOT / "hooks" / "scripts" / "lib" / "agent_dispatch_gate.py"
        spec = importlib.util.spec_from_file_location("typed_dispatch_gate2", gate_path)
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        for description, phase in TEMPLATE_PHASES.items():
            with self.subTest(template=description):
                block = block_for(description)
                model = re.search(r'model="([^"]+)"', block).group(1)
                self.assertIsNone(gate.judge(phase, model))


def runner_body(filename: str) -> str:
    text = (ROOT / "agents" / f"{filename}.md").read_text(encoding="utf-8")
    return text[text.index("\n---\n", 4) + 5 :]


class TestIndependent3Findings(unittest.TestCase):
    """独立-3（最終・全差分）: 2 つの runner の本文が frontmatter 以外で同一であること。"""

    def test_l8_runner_bodies_are_identical_after_the_frontmatter(self):
        # 2 つの runner は frontmatter 以外が同一。片方だけ直す変更を落とす。
        self.assertEqual(runner_body("gdd-formal-gate-runner"), runner_body("gdd-light-task-runner"))


class TestPostPR1Findings(unittest.TestCase):
    """独立-15: setup-gdd-loop.sh の continuation prompt が dispatch 文言を複製していないこと
    （test_p5）と、`Resume From` の許容値集合が state-machine.md / gdd-status/SKILL.md の
    3 箇所で一致すること（test_p6）を固定する。"""

    def test_p5_setup_gdd_loop_continuation_prompt_does_not_duplicate_the_dispatch_logic(self):
        # 独立-15 finding 4: setup-gdd-loop.sh が Stop hook 経由で毎回注入する continuation
        # prompt に、requirements-gating-steps.md（独立-13 finding 1 で直した）と同型の
        # 「次の phase skill を invoke する」文言の複製が残っていた。runtime を問わず正本
        # （commands/gdd-dev.md instruction 10 STEP 2）を指す形に直した。
        text = (ROOT / "scripts" / "setup-gdd-loop.sh").read_text(encoding="utf-8")
        self.assertNotIn("invoke the next phase skill", text)
        self.assertIn("commands/gdd-dev.md", text)
        self.assertIn("instruction 10 STEP 2", text)

    def test_p6_resume_from_enum_agrees_across_state_machine_and_gdd_status(self):
        # 独立-15 finding 2・5(1): state-machine.md の `Resume From` 許容値集合（field 定義・
        # planning candidate 判定）と gdd-status/SKILL.md のチェック1 許容値が、express 専用の
        # gdd-test-driven-development を含めて 3 箇所とも同じ集合であることを固定する
        # （独立-14 finding 1 で state-machine.md 側だけ直し、gdd-status 側の追随漏れが
        # 独立-15 finding 2 で見つかった。同型の再発を防ぐ）。
        token_re = re.compile(r"`([a-z][a-z-]*)`")

        state_machine = (ROOT / "references" / "state-machine.md").read_text(encoding="utf-8")
        # 独立-16 finding 9: count で一意性を確かめてから index する（同形の行が
        # 先に増えると別の行を読んだまま緑になるのを防ぐ）。
        self.assertEqual(state_machine.count("- `Resume From`:\n"), 1)
        field_def_line = state_machine.splitlines()[
            state_machine[: state_machine.index("- `Resume From`:\n")].count("\n") + 1
        ]
        field_def_set = set(token_re.findall(field_def_line.split("（")[0]))

        candidate_line = [
            l for l in state_machine.splitlines()
            if l.lstrip().startswith("- `Resume From` が") and "のいずれか" in l
        ]
        self.assertEqual(len(candidate_line), 1)
        candidate_set = set(token_re.findall(candidate_line[0].split("のいずれか")[0]))

        gdd_status = (ROOT / "skills" / "gdd-status" / "SKILL.md").read_text(encoding="utf-8")
        status_line = [
            l for l in gdd_status.splitlines()
            if l.lstrip().startswith("- `Resume From` の許容値:")
        ]
        self.assertEqual(len(status_line), 1)
        status_set = set(token_re.findall(status_line[0].split("（")[0]))

        self.assertIn("gdd-test-driven-development", field_def_set)
        self.assertEqual(field_def_set, candidate_set)
        self.assertEqual(field_def_set, status_set)

        # 独立-15 finding 5(1): 許容値集合だけでなく、express 状態遷移表の実値
        # （`human check 承認（express）` 行の `Resume From` 列）も集合に含まれること。
        # enum を揃えても、実際にその値を書く行が値を出さなくなれば 3 箇所の一致は
        # 無意味になる。
        express_row = [
            l for l in state_machine.splitlines()
            if l.lstrip().startswith("| human check 承認（express）")
        ]
        self.assertEqual(len(express_row), 1)
        self.assertIn("gdd-test-driven-development", express_row[0])


if __name__ == "__main__":
    unittest.main()
