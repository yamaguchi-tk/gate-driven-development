"""GDD の agent 定義は `tools:` の許可リストを持つ（2026-09-29）。

根拠（2026-09-29 実測）:
- `tools:` の無い agent は親の全ツール（MCP・ブラウザ等）を受け取る。起動直後の文脈は
  全ツールの agent が、Read・Grep・Glob だけの agent より大きく膨らんだ（GDD を使う別の repo）。
  この文脈は subagent の呼び出しのたびに読み直される（formal-gate-runner は呼び出しが多い）。
- reviewer が `mcp__ccd_session__spawn_task`・`mark_chapter`・`EnterWorktree` を呼んだ例がある。

公式ドキュメント（sub-agents・tools-reference）によると、許可リストに解決できない名前があると
subagent の起動がエラーになる（この版での実測はしていない）。名前は閉じた集合（KNOWN_TOOLS）から選ぶ。入れ子の起動（Agent）は formal-gate-runner だけが持つ。
"""
import unittest
from pathlib import Path

from test_typed_dispatch_templates_contract import DISPATCH, agent_blocks, frontmatter

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"

# Claude Code の組み込みツールのうち、GDD の agent に渡してよい名前（手書きの集合。Claude Code が
# 解決できるかはここでは確かめない。2026-09-29 の CLI 2.1.280 のセッションに全部あることは目で確かめた）
KNOWN_TOOLS = frozenset(
    {"Read", "Grep", "Glob", "Bash", "Edit", "Write", "Agent", "WebFetch", "WebSearch", "Monitor", "TaskStop"}
)

BASE = {"Read", "Grep", "Glob", "Bash", "Edit", "Write", "Monitor", "TaskStop"}
WEB = {"WebFetch", "WebSearch"}

EXPECTED = {
    # phase を実行し、reviewer・dialectic の評価者を入れ子で起動する
    "gdd-formal-gate-runner": BASE | WEB | {"Agent"},
    "gdd-light-task-runner": BASE,
    "gdd-code-simplifier": BASE,
    # 実装 worker は葉。入れ子の起動はしない
    "gdd-implementation-worker": BASE,
    "gdd-implementation-worker-heavy": BASE,
    "gdd-remediation-worker": BASE,
    # reviewer は葉。入れ子の起動はしない。grounding のために Web は読む
    "gdd-planning-reviewer": BASE | WEB,
    "gdd-implementation-reviewer": BASE | WEB,
    "gdd-security-reviewer": BASE | WEB,
    "gdd-completion-reviewer": BASE | WEB,
    # マージ後の QA は葉。repo の書き込みはせず、Bash で環境を確かめる（references/post-merge-qa.md）
    "gdd-qa-runner": {"Read", "Grep", "Glob", "Bash", "Monitor", "TaskStop"},
    # 相談役は葉で read-only。材料はファイルの場所で受けて読む（references/autonomy.md 判断の手順）
    "gdd-opus-advisor": {"Read", "Grep", "Glob"},
    "gdd-opus-advisor-max": {"Read", "Grep", "Glob"},
    "gdd-fable-advisor": {"Read", "Grep", "Glob"},
    # 依頼と既存コードの突き合わせは葉で read-only（references/brainstorming-steps.md の 9）
    "gdd-request-code-crosscheck": {"Read", "Grep", "Glob"},
    # 提出前の照合は葉で read-only（references/requirements-gating-steps.md Step 4a）
    "gdd-requirements-precheck": {"Read", "Grep", "Glob"},
    # 指摘の検証役は葉で read-only（references/finding-dispositions.md § 検証役）
    "gdd-finding-verifier": {"Read", "Grep", "Glob"},
    # 独立レビューは read-only（references/independent-review.md 契約 2）
    "gdd-independent-reviewer": {"Read", "Grep", "Glob"},
}


def tools_of(name: str) -> set[str]:
    value = frontmatter(AGENTS / f"{name}.md").get("tools")
    if value is None:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


class TestAgentToolAllowlist(unittest.TestCase):
    def test_every_agent_file_is_listed(self):
        # 新しい agent を足したら、ここに許可リストを決めて足す（黙って全ツールにしない）
        on_disk = {path.stem for path in AGENTS.glob("*.md")}
        self.assertEqual(on_disk, set(EXPECTED))

    def test_every_agent_has_the_expected_allowlist(self):
        for name, expected in EXPECTED.items():
            with self.subTest(agent=name):
                self.assertEqual(tools_of(name), expected)

    def test_allowlist_names_are_known_builtin_tools(self):
        for name in EXPECTED:
            with self.subTest(agent=name):
                unknown = tools_of(name) - KNOWN_TOOLS
                self.assertFalse(unknown, f"{name}: 解決できない名前 {sorted(unknown)}")

    def test_only_the_formal_gate_runner_can_nest(self):
        nesting = {name for name in EXPECTED if "Agent" in tools_of(name)}
        self.assertEqual(nesting, {"gdd-formal-gate-runner"})


class TestDispatchReachesAnAllowlistedAgent(unittest.TestCase):
    """入口（subagent-dispatch.md の Template）から、許可リストを持つ agent に届く。"""

    def test_every_template_subagent_type_has_an_allowlist(self):
        types = set()
        for block in agent_blocks(DISPATCH):
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("subagent_type="):
                    types.add(line.split("=", 1)[1].strip().strip('",'))
        gdd_types = {t.split(":", 1)[1] for t in types if t.startswith("gate-driven-development:")}
        self.assertTrue(gdd_types, "Template に GDD の subagent_type が無い")
        for name in gdd_types:
            with self.subTest(agent=name):
                self.assertTrue(tools_of(name), f"{name}: tools が無い（全ツールを受け取る）")

    def test_reviewer_escalation_runs_inside_a_runner_that_can_nest(self):
        # implementation-gating の reviewer escalation と design-gating の dialectic は、
        # formal-gate-runner の中から Agent で起動する
        for phase in ("gdd-implementation-gating", "gdd-design-gating", "gdd-completion-check"):
            with self.subTest(phase=phase):
                blocks = [b for b in agent_blocks(DISPATCH) if f"## Phase\n  {phase}" in b or f"## Phase\n{phase}" in b]
                self.assertTrue(blocks, f"{phase} の Template が無い")
                for block in blocks:
                    self.assertIn("gate-driven-development:gdd-formal-gate-runner", block)
        self.assertIn("Agent", tools_of("gdd-formal-gate-runner"))


if __name__ == "__main__":
    unittest.main()
