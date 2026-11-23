"""cross-session HITL 通知（送信/受信/取り込みタイミング）。

`Origin Session` の write-once 契約が hook（validate-steering-write.py）側で
機械強制されていることを検査する。
"""
import importlib.util
import unittest

from _paths import PLUGIN_ROOT as ROOT


HOOK = (ROOT / "hooks" / "scripts" / "validate-steering-write.py").read_text(encoding="utf-8")


class TestCrossSessionHITL(unittest.TestCase):
    def test_hook_required_fields_unchanged(self):
        """`Origin Session` は optional。hook の必須 field 集合を増やしていないこと。

        pr-review 是正で `Origin Session` の write-once を hook が機械強制するように
        なったため、旧実装の `assertNotIn("Origin Session", HOOK)`（本文の文字列
        検索）は「必須 field が増えていない」ではなく「hook が本 field を一切
        知らない」を測っていた。契約の意味は `STATE_REQUIRED_FIELDS` の中身なので、
        定数そのものを見る。
        """
        spec = importlib.util.spec_from_file_location(
            "validate_steering_write_cross_session",
            ROOT / "hooks" / "scripts" / "validate-steering-write.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertNotIn("Origin Session", module.STATE_REQUIRED_FIELDS)
        self.assertEqual(
            module.STATE_REQUIRED_FIELDS,
            ("Resume From", "Human Check Status", "Route In Progress"),
        )


if __name__ == "__main__":
    unittest.main()
