"""reviewer-common.md § 常時 High の (a) の field 列挙と、再開経路の hook の突き合わせ（Issue #123）。

クラス D（2 箇所で持つ集合の一致）。(a) に列挙した再開用の field（RESUME_FIELDS）が、
state-field-tiers.md の routing source の宣言と、再開経路の hook が実際に読み書きする field に
一致すること、廃止した印（state-field-tiers.md の宣言）を hook が読み書きしないことを見る。
hook が新しい再開用の field を読み書きし始めたのに (a) に足さないと、
その field に届く欠陥が常時 High の適用範囲から黙って外れる。
"""
from __future__ import annotations

import re
import unittest

from _paths import PLUGIN_ROOT

CANONICAL = PLUGIN_ROOT / "references" / "reviewer-common.md"
HEADING = "### 常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）"


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    rest = text[start + len(heading):]
    m = re.search(r"^#{2,3} ", rest, flags=re.M)
    return rest[: m.start()] if m else rest


# 再開に使う canonical field（Issue #123）。block しない hook（SessionStart など）でも、
# これらの書き込み・削除に届く欠陥は適用範囲内にする。「resume に関わるもの全部」ではなく効果で列挙する。
# compact 自動復帰の印（`Status`・`CompactSource` など）は 2026-09-28 に廃した（state-field-tiers.md の「廃止した hook の印」の行。state-schema.json の retired_hook_fields）
RESUME_FIELDS = ("Resume From", "Next Action", "Route In Progress", "Human Check Status")
TIERS = PLUGIN_ROOT / "references" / "state-field-tiers.md"


def _retired_mark_pattern(field: str) -> str:
    r"""廃止した印を field 名として使う形。`Status` は `Human Check Status` などの一部にもなるので、
    前が英字・空白でない（ただし `Gate\s*Status` のような「英字＋`\s`＋量指定子」の直後は除く）か
    bullet の `- `、後ろが引用符・`:`・`=`・正規表現の `\s` のものだけを見る。"""
    return rf"(?:(?<![A-Za-z ])(?<![A-Za-z]\\s[*+?])|(?<=- )){re.escape(field)}(?=[\"':=]|\\s)"
SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
# 列挙した field を読む側と、そのファイルでの現れ方。ファイルごとに検査する
# （連結すると、1 ファイルを外しても他のファイルの出現で通る。独立-4）
RESUME_PATHS = [
    # SessionStart hook（Safe Resume）: gdd_extract_doc_field（読む側）の呼び出し。呼び出しごと固定する
    (SCRIPTS / "run-session-start-hook.sh", 'gdd_extract_doc_field "$GDD_STEERING_DIR/state.md" "{}"',
     ("Resume From",)),
    # active steering 判定
    (SCRIPTS / "lib" / "detect-steering.sh", '"{}"',
     ("Resume From", "Next Action", "Human Check Status", "Route In Progress")),
    # done guard（gdd_stop_hook.py は lib/tasklist_parse.py の正規表現に委ねる）
    (SCRIPTS / "lib" / "tasklist_parse.py", "`?{}", ("Resume From", "Route In Progress")),
]


class ResumeScopeTest(unittest.TestCase):
    """(a) の field 列挙と、tiers の宣言・再開経路の hook の突き合わせ（Issue #123）。"""

    def setUp(self) -> None:
        self.text = CANONICAL.read_text(encoding="utf-8")
        self.body = _section(self.text, HEADING)

    def test_resume_fields_are_in_scope(self) -> None:
        # (a) の括弧の中の列挙だけを取り、両方向の一致を見る（節のどこかにあるだけでは、
        # (a) から外して別の文に書いた field や、hook が読まない field を (a) に足した形を通す）
        # 括弧の入れ子は許さない。入れ子の後ろに足した field が比較から漏れるので、一致しなければ落とす
        match = re.search(r"\(a\)[^（]*（([^（）]*)）", self.body)
        self.assertIsNotNone(match, "(a) の field の列挙が見つからない")
        self.assertEqual(set(re.findall(r"`([^`]+)`", match.group(1))), set(RESUME_FIELDS))

    def test_routing_sources_match_state_field_tiers(self) -> None:
        # routing source の正本は state-field-tiers.md。そちらに field が増えたら列挙も追従させる
        tiers = TIERS.read_text(encoding="utf-8")
        line = next(l for l in tiers.splitlines() if l.startswith("- routing source:"))
        routing = re.findall(r"`([^`]+)`", line)
        self.assertTrue(routing)
        for field in routing:
            with self.subTest(field=field):
                self.assertIn(field, RESUME_FIELDS)

    def test_retired_marks_are_out_of_scope_and_unused(self) -> None:
        # 廃した印は (a) に入れず、hook のどこからも書き・読まない（読み手を残すと、印を見て発火する経路が
        # 戻る）。廃したことの代わり（compaction の直後に何も出さない）は test_compact_without_auto_resume.py
        tiers = TIERS.read_text(encoding="utf-8")
        line = next(l for l in tiers.splitlines() if "**廃止した hook の印（Tier 分類の対象外）**:" in l)
        retired = re.findall(r"`([^`]+)`", line.split("**:", 1)[1].split("—", 1)[0])
        self.assertIn("Status", retired)
        self.assertIn("CompactSource", retired)
        scripts = [
            p for root in (SCRIPTS, PLUGIN_ROOT / "scripts") for p in root.rglob("*")
            if p.is_file() and p.suffix in (".sh", ".py")
        ]
        self.assertTrue(scripts)
        for field in retired:
            with self.subTest(field=field):
                self.assertNotIn(field, RESUME_FIELDS)
                pattern = _retired_mark_pattern(field)
                for path in scripts:
                    self.assertNotRegex(path.read_text(encoding="utf-8"), pattern, path.name)

    def test_retired_mark_pattern_matches_field_usage_only(self) -> None:
        # 上の検査の正規表現そのものを固定する（狭めると、廃止した印の読み手が戻っても通る）
        for field, text in (
            ("Status", "grep -m1 '^- Status:'"), ("Status", r"'^\s*Status:'"), ("Status", "(?:- )?Status="),
            ("Status", "- Status: paused"), ("Status", r"'^Status\s*:'"), ("CompactSource", '"CompactSource"'),
        ):
            with self.subTest(match=text):
                self.assertRegex(text, _retired_mark_pattern(field))
        for text in (r'r"Gate\s*Status",', "Human Check Status:", "- Human Check Status:", r"Human\s+Check\s+Status\s*:"):
            with self.subTest(no_match=text):
                self.assertNotRegex(text, _retired_mark_pattern("Status"))

    def test_retired_mark_pattern_over_every_prefix_and_suffix(self) -> None:
        # 例を 1 件ずつ並べるのではなく、選んだ前の文脈 × 後ろの文脈のすべての組み合わせで期待を固定する。
        # 前: field 名として使う形か、`Human Check Status` のような別の名前の一部か
        prefixes = {
            "": True, "\n": True, "\t": True, "x\n": True, "'^": True, "\"": True, "- ": True, "grep -m1 '^- ": True, "(?:- )?": True, r"'^\s*": True,
            "Human Check ": False, "Human\\s+Check\\s+": False, "Gate": False, "Gate ": False, r"Gate\s*": False,
            r"Gate\s+": False, r"Gate\s?": False, "x": False, "Route ": False,
        }
        suffixes = {'"': True, "'": True, ":": True, "=": True, r"\s": True, r"\s*:": True,
                    "": False, " ": False, "_x": False, "x": False, ".": False, ",": False}
        for prefix, prefix_ok in prefixes.items():
            for suffix, suffix_ok in suffixes.items():
                text = f"{prefix}Status{suffix}"
                with self.subTest(text=text):
                    matched = re.search(_retired_mark_pattern("Status"), text) is not None
                    self.assertEqual(matched, prefix_ok and suffix_ok)

    def test_resume_fields_are_used_by_resume_paths(self) -> None:
        # 列挙した field が再開の経路で実際に書かれ・読まれていること（改名で列挙だけが残るのを防ぐ）
        covered: set[str] = set()
        for path, form, fields in RESUME_PATHS:
            text = path.read_text(encoding="utf-8")
            for field in fields:
                with self.subTest(path=path.name, field=field):
                    self.assertIn(form.format(field), text)
            covered.update(fields)
        self.assertEqual(covered, set(RESUME_FIELDS))
        # `select_route_in_progress` の呼び出しは、#145 で Check 3 ごと `lib/done_guard.py` へ移った
        stop_hook = (SCRIPTS / "gdd_stop_hook.py").read_text(encoding="utf-8")
        done_guard = (SCRIPTS / "lib" / "done_guard.py").read_text(encoding="utf-8")
        for source, reader in ((done_guard, "select_route_in_progress("), (stop_hook, "resume_from_value(")):
            with self.subTest(reader=reader):
                self.assertIn(reader, source)


if __name__ == "__main__":
    unittest.main()
