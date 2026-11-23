"""Reference integrity tests for GDD plugin docs, agents, commands, and skills."""
from __future__ import annotations

import re
import unittest


from _paths import PLUGIN_ROOT


class ReferenceIntegrityContractTests(unittest.TestCase):
    def test_root_references_from_runtime_docs_exist(self) -> None:
        """`references/foo.md` should resolve to plugin-root references/foo.md.

        Skill-local references must use `./references/foo.md`; those are validated
        separately by validate-plugin.sh. This test catches the class of drift where
        an agent or command mentions a root reference that was never added.
        """

        checked_roots = [
            "agents",
            "commands",
            "docs",
            "skills",
            "README.md",
        ]
        reference_pattern = re.compile(r"(?<![\w./-])references/([A-Za-z0-9_.-]+\.md)")
        missing: list[str] = []

        for root_name in checked_roots:
            root_path = PLUGIN_ROOT / root_name
            paths = [root_path] if root_path.is_file() else sorted(root_path.rglob("*.md"))
            for path in paths:
                text = path.read_text(encoding="utf-8")
                for match in reference_pattern.finditer(text):
                    ref = PLUGIN_ROOT / "references" / match.group(1)
                    if not ref.exists():
                        rel_path = path.relative_to(PLUGIN_ROOT)
                        missing.append(f"{rel_path}: references/{match.group(1)}")

        self.assertEqual(missing, [])

    def test_compact_templates_exist_and_stay_small(self) -> None:
        express = PLUGIN_ROOT / "references" / "requirements-template-express.md"
        compact_hitl = PLUGIN_ROOT / "references" / "human-check-template-compact.md"
        full_requirements = (PLUGIN_ROOT / "references" / "requirements-template.md").read_text(encoding="utf-8")
        full_hitl = (PLUGIN_ROOT / "references" / "human-check-template.md").read_text(encoding="utf-8")

        self.assertTrue(express.exists())
        self.assertTrue(compact_hitl.exists())
        self.assertLessEqual(len(express.read_text(encoding="utf-8").splitlines()), 150)
        compact_text = compact_hitl.read_text(encoding="utf-8")
        self.assertLessEqual(len(compact_text.splitlines()), 112)  # 導入時の実測終端値。express template 上限（skill-body-budget.sh が正本）の従属変数で、実測終端も 112 で下げ余地なし
        self.assertNotIn("| 既存 repo 標準 |", compact_text)
        self.assertNotIn("| 業界標準 / vendor official |", compact_text)
        self.assertNotIn("| 最小の自前実装 |", compact_text)
        self.assertIn("条件付き詳細", compact_text)

        self.assertIn("Size-Specific Template Dispatch", full_requirements)
        self.assertIn("references/requirements-template-express.md", full_requirements)
        self.assertIn("Compact First", full_hitl)
        self.assertIn("references/human-check-template-compact.md", full_hitl)


if __name__ == "__main__":
    unittest.main()
