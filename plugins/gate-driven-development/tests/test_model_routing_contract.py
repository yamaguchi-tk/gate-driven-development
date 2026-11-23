"""Contract tests for GDD model / effort routing across hosts."""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest


from _paths import PLUGIN_ROOT
RESOLVER = PLUGIN_ROOT / "scripts" / "resolve-gdd-model.py"


def read_reference(name: str) -> str:
    return (PLUGIN_ROOT / "references" / name).read_text(encoding="utf-8")


def read_skill(name: str) -> str:
    return (PLUGIN_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def read_command(name: str) -> str:
    return (PLUGIN_ROOT / "commands" / name).read_text(encoding="utf-8")


def resolve(*args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(RESOLVER), *args, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def load_resolver():
    spec = importlib.util.spec_from_file_location("model_routing_resolver", RESOLVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def host_table_rows(text: str) -> dict[str, list[str]]:
    """`| tier | Claude Code | Cursor | Codex |` の表の行を、先頭のセルの tier 名で引く。"""
    rows: dict[str, list[str]] = {}
    in_table = False
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells == ["tier", "Claude Code", "Cursor", "Codex"]:
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        match = re.match(r"`([a-z_]+)`", cells[0])
        if match:
            rows[match.group(1)] = cells
    return rows


class ModelRoutingContractTests(unittest.TestCase):
    def test_claude_implementation_is_sonnet_until_risk_escalation(self) -> None:
        normal = resolve(
            "--runtime",
            "claude_code",
            "--phase",
            "gdd-subagent-driven-implementation",
            "--text",
            "bounded implementation for approved AC",
        )
        risky = resolve(
            "--runtime",
            "claude_code",
            "--phase",
            "gdd-subagent-driven-implementation",
            "--text",
            "security-sensitive implementation across many files",
        )

        self.assertEqual(normal["tier"], "implementation")
        self.assertEqual(normal["model"], "sonnet")
        self.assertEqual(normal["effort"], "medium")
        self.assertEqual(risky["tier"], "general_heavy_risk")
        self.assertEqual(risky["model"], "opus")
        self.assertEqual(risky["effort"], "high")

    def test_cursor_implementation_uses_composer_25(self) -> None:
        payload = resolve(
            "--runtime",
            "cursor",
            "--phase",
            "gdd-subagent-driven-implementation",
            "--text",
            "bounded implementation for approved AC",
        )

        self.assertEqual(payload["tier"], "implementation")
        self.assertEqual(payload["model"], "composer-2.5")
        self.assertEqual(payload["effort"], "n/a")

        for text in [
            read_skill("gdd-model-routing"),
            read_reference("cursor.md"),
            read_reference("fixed-models.md"),
            read_reference("subagent-dispatch.md"),
            read_command("gdd-dev.md"),
        ]:
            self.assertIn("Composer 2.5", text)
            self.assertIn("composer-2-fast", text)
            self.assertNotIn("Composer 2`", text)

    def test_pr_review_is_final_review_tier(self) -> None:
        """gdd-pr-review は最終 diff review であり light ではなく risk tier で固定する。

        根拠: 2026-08-22 に GDD を使う別の repo の PR で確かめると、gate 通過後の
        実害級欠陥を検出したのは Opus + effort=high の最終レビューだった。
        """
        claude = resolve(
            "--runtime",
            "claude_code",
            "--phase",
            "gdd-pr-review",
            "--text",
            "diff を確認する",
        )
        cursor = resolve(
            "--runtime",
            "cursor",
            "--phase",
            "gdd-pr-review",
            "--text",
            "diff を確認する",
        )

        self.assertEqual(claude["tier"], "general_heavy_risk")
        self.assertEqual(claude["model"], "opus")
        self.assertEqual(claude["effort"], "high")
        self.assertEqual(cursor["tier"], "general_heavy_risk")
        self.assertEqual(cursor["model"], "grok-4.6")
        self.assertEqual(cursor["effort"], "high")

    def test_entry_gate_hints_route_formal_gate_without_phase(self) -> None:
        """phase 未確定の entry で brainstorming / requirements 系の文言は formal_gate に解決する。

        旧実装では LIGHT_HINTS に "brainstorming" / "requirements" が含まれ、
        新規 workflow の入口（最初のフェーズはまさに brainstorming）が
        light_task=Sonnet に解決されていた。
        """
        payload = resolve(
            "--runtime",
            "claude_code",
            "--text",
            "新機能の brainstorming から始めたい",
        )

        self.assertEqual(payload["tier"], "formal_gate")
        self.assertEqual(payload["model"], "opus")
        self.assertEqual(payload["effort"], "high")

    def test_plain_light_hints_still_route_light_without_phase(self) -> None:
        payload = resolve(
            "--runtime",
            "claude_code",
            "--text",
            "変更内容の要約だけ作って",
        )

        self.assertEqual(payload["tier"], "light_task")
        self.assertEqual(payload["model"], "sonnet")

    def test_codex_implementation_and_mini_boundary(self) -> None:
        payload = resolve(
            "--runtime",
            "codex",
            "--phase",
            "gdd-subagent-driven-implementation",
            "--text",
            "bounded implementation for approved AC",
        )

        self.assertEqual(payload["tier"], "implementation")
        self.assertEqual(payload["model"], "gpt-5.6-terra")
        self.assertEqual(payload["effort"], "low")

        for text in [
            read_skill("gdd-model-routing"),
            read_reference("cursor.md"),
            read_reference("codex.md"),
            read_reference("fixed-models.md"),
        ]:
            self.assertIn("mini禁止境界", text)
            self.assertIn("HITL生成", text)
            self.assertIn("routing判断", text)
            self.assertIn("state更新", text)
            self.assertIn("completion判定", text)


    def test_model_routing_host_table_covers_every_resolver_tier(self) -> None:
        # skills/gdd-model-routing の host 写像表の Claude Code 列を、resolver の tier ごとの値と突き合わせる
        resolver = load_resolver()
        rows = host_table_rows(read_skill("gdd-model-routing"))
        for tier, model in resolver.TIER_TO_MODEL["claude_code"].items():
            with self.subTest(tier=tier):
                self.assertIn(tier, rows)
                effort = resolver.resolve_effort("claude_code", tier, None, {})
                self.assertIn(f"`{model}` + `effort={effort}`", rows[tier][1])

if __name__ == "__main__":
    unittest.main()
