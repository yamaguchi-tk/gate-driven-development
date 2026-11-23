"""PR レビュー followup の Design Review Checkpoint の閾値の定数（AC-2）。

クラス A（指す先のシンボルの実在）。`skills/gdd-pr-review-followup/SKILL.md`・`references/state-field-tiers.md`・
`references/bounce-log-schema.md`・`references/state-machine.md` は、checkpoint の閾値をこの 5 つの定数名で指す。
コードからは使われていないので、改名や未使用シンボルの掃除で消えても、ほかのテストは落ちない。
"""
import unittest

from _paths import PLUGIN_ROOT as ROOT

CONSTANTS = (ROOT / "hooks/scripts/lib/constants.py").read_text(encoding="utf-8")


class ConstantsContractTest(unittest.TestCase):
    def test_five_checkpoint_constants_defined_once_each(self) -> None:  # AC-2
        names = (
            "PR_REVIEW_ROUNDS_MAX",
            "PR_CHECKPOINT_ROUNDS_THRESHOLD",
            "PR_CHECKPOINT_SELF_INFLICTED_RATIO",
            "PR_CHECKPOINT_CLUSTER_REPEAT_ROUNDS",
            "PR_CHECKPOINT_REVIEW_COMMIT_RATIO",
        )
        for name in names:
            self.assertEqual(CONSTANTS.count(f"{name} ="), 1, name)


if __name__ == "__main__":
    unittest.main()
