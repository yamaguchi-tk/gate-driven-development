import unittest


from _paths import PLUGIN_ROOT as ROOT


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class TestWorktreePollutionContract(unittest.TestCase):
    def test_pre_artifact_worktree_guard_is_scripted_and_required_before_writes(self):
        script = ROOT / "scripts" / "assert-worktree-ready.py"
        self.assertTrue(script.exists(), "pre-artifact worktree guard script is missing")

        script_text = script.read_text(encoding="utf-8")
        required_script_terms = [
            "repo-root",
            "worktree-path",
            "steering-slug",
            "Refusing to write GDD steering artifacts into repo root",
            "root_steering_duplicate",
            "legacy-migration",
        ]
        for term in required_script_terms:
            with self.subTest(term=term):
                self.assertIn(term, script_text)

        brainstorming_steps = read("references/brainstorming-steps.md")
        subagent_dispatch = read("references/subagent-dispatch.md")
        gdd_dev = read("commands/gdd-dev.md")

        required_contract_terms = [
            "scripts/assert-worktree-ready.py",
            "pre-artifact",
            "root に `.steering/` を作る前に失敗させる",
        ]
        combined = "\n".join([brainstorming_steps, subagent_dispatch, gdd_dev])
        for term in required_contract_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)


if __name__ == "__main__":
    unittest.main()
