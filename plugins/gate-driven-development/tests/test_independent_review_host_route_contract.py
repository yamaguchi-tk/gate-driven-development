"""`independent_review` tier の、resolver の値と文書の表の照合テスト。

`scripts/resolve-gdd-model.py` の `TIER_TO_MODEL` と `resolve_effort` の runtime ごとの値を、
`references/fixed-models.md` の `independent_review` の行（3 runtime の列）と、
`references/cursor.md`・`references/codex.md` の tier 表の `independent_review` の行に突き合わせる。
Claude Code の独立レビューは `agents/gdd-independent-reviewer.md` で起動する（`Agent` ツールは effort を引数で
受けないので、effort を固定できるのは定義の frontmatter だけ）。その model・effort を resolver の値と、Agent の
model を検査する hook が使う固定 model の表に突き合わせる。
Claude Code 以外で独立レビューを起動する経路（agent 定義を直接起動しない等）は、本ファイルに機械検査なし。
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT
from test_typed_dispatch_templates_contract import frontmatter

AGENT = PLUGIN_ROOT / "agents" / "gdd-independent-reviewer.md"

EXPECTED = {
    "claude_code": ("opus", "xhigh", "opus"),
    "cursor": ("grok-4.6", "high", "Grok 4.6"),
    "codex": ("gpt-5.6-sol", "high", "gpt-5.6-sol"),
}


def _load_resolver():
    path = PLUGIN_ROOT / "scripts" / "resolve-gdd-model.py"
    spec = importlib.util.spec_from_file_location("gdd_resolver_independent_review", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _independent_review_row() -> list[str]:
    for line in _read(PLUGIN_ROOT / "references" / "fixed-models.md").splitlines():
        if line.startswith("| `independent_review` |"):
            return [cell.strip() for cell in line.strip().strip("|").split("|")]
    raise AssertionError("fixed-models.md に independent_review の行が無い")


def _host_reference_row(name: str) -> list[str]:
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in _read(PLUGIN_ROOT / "references" / name).splitlines()
        if line.startswith("| `independent_review` |")
    ]
    if len(rows) != 1:
        raise AssertionError(f"{name} に independent_review の行が {len(rows)} 行ある")
    return rows[0]


class ResolverMatchesFixedModelsTests(unittest.TestCase):
    def test_resolver_has_independent_review_for_every_runtime(self) -> None:
        resolver = _load_resolver()
        for runtime, (model, effort, _) in EXPECTED.items():
            self.assertEqual(resolver.TIER_TO_MODEL[runtime]["independent_review"], model, runtime)
            self.assertEqual(
                resolver.resolve_effort(runtime, "independent_review", None, {}), effort, runtime
            )

    def test_fixed_models_row_matches_resolver(self) -> None:
        row = _independent_review_row()
        columns = {"claude_code": row[1], "cursor": row[2], "codex": row[3]}
        for runtime, (_, effort, label) in EXPECTED.items():
            self.assertIn(f"`{label}`", columns[runtime], runtime)
            self.assertIn(f"effort={effort}`", columns[runtime], runtime)

    def test_host_reference_rows_match_resolver(self) -> None:
        # references/cursor.md・codex.md の tier 表の independent_review の行（model・effort）を、
        # resolver の値と突き合わせる。文書の model ラベル（`Grok 4.6`）は、小文字にして空白を
        # `-` に置き換えると resolver の値（`grok-4.6`）になる
        resolver = _load_resolver()
        for runtime, name in (("cursor", "cursor.md"), ("codex", "codex.md")):
            with self.subTest(runtime=runtime):
                row = _host_reference_row(name)
                label = row[1].strip("`").lower().replace(" ", "-")
                self.assertEqual(label, resolver.TIER_TO_MODEL[runtime]["independent_review"])
                effort = resolver.resolve_effort(runtime, "independent_review", None, {})
                self.assertEqual(row[2], f"`{effort}`")


class ClaudeCodeAgentDefinitionTests(unittest.TestCase):
    def test_agent_frontmatter_matches_resolver(self) -> None:
        resolver = _load_resolver()
        data = frontmatter(AGENT)
        self.assertEqual(data.get("model"), resolver.TIER_TO_MODEL["claude_code"]["independent_review"])
        self.assertEqual(
            data.get("effort"), resolver.resolve_effort("claude_code", "independent_review", None, {})
        )

    def test_dispatch_gate_uses_agent_model(self) -> None:
        # model を省略した Agent 起動を、hook が定義の model（opus）で判定する
        sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
        from lib.agent_dispatch_gate import fixed_model

        model = frontmatter(AGENT).get("model")
        for name in ("gate-driven-development:gdd-independent-reviewer", "gdd-independent-reviewer"):
            self.assertEqual(fixed_model(name), model, name)


if __name__ == "__main__":
    unittest.main()
