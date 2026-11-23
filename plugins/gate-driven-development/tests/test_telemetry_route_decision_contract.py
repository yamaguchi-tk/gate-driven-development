"""T-12 契約テスト: telemetry の Route Decision 計上を固定値で pin する（AC-8 / AC-9 / AC-10）。

対象は `scripts/collect-gdd-telemetry.py` が `.steering/<task>/worklog.md` から出す
`bounce_count` / `unparsed_route_sections` と、その `text` / `json` / `csv` 3 形式への露出。
受理面の正本は `references/phase-progression.md` § Bounce 計測の受理面。**本ファイルは
その正本の実装を測る側であって、受理面の定義ではない**。

**名前の衝突に注意（T-11 impl-gate advisory L-3）**: ここで扱う `bounce_count` は
telemetry の report-only 指標であり、`references/bounce-log-schema.md` の
**gate 別 Bounce Log の `bounce_count`（閾値 2 で escape hatch が発動する制御値）とは
同名の別概念**。取り違えると「テストが escape hatch を守っている」という誤読になる。

**期待値の正本はこのファイル 1 箇所**（AC-9）。fixture から件数を導出しない。fixture を
書き換えるときは同じ commit で下記の literal も更新する。

## 測っている範囲

- 凍結 fixture 2 本に対する計上件数の固定値（`_FIXTURE_EXPECTED`）。`text` / `json` / `csv`
  の 3 形式それぞれで同じ値が出ること（AC-8）
- `## Route Decision` 節に **1 行だけ**置いたときの行形ごとの受理/不受理（`_LINE_FORMS`）。
  F1 / F2（太字あり・なし）と、正本節が「計上対象外」と列挙した形の判別
- section 単位の形（`_SECTION_FORMS`）。`## Batch Route Decisions` / 見出しだけが route 値を
  持つ形が `unparsed_route_sections` に出ること
- 出荷 doc（`references/phase-progression.md` § Escalation Decision Table）の**複数境界記録例を
  そのまま worklog にした場合**に計上されないこと（`- Route:` と F1 の不一致 / owner T-12）
- fixture 側の**逐語形**（A-11 / A-15）。pr-w3 = `- **route 判定**:`（太字あり）/
  drift = `- route 判定:`（太字なし）。F2 は太字有無の両形を受理するため、fixture の太字が
  将来失われても・付いても件数は動かず、固定値 assert では気づけない。**2 種を交差表で pin する**
  （A-11 だけを見て pr-w3 側だけ pin すると drift 側の coverage が静かに空く）
- `text` の `unparsed_by_task`（AC-10 の所在）。件数 0 の task を除外すること / 件数降順・
  同数なら id 昇順に並ぶこと / 全 task が 0 なら節ごと出さないこと

## 測っていない範囲（意図的。ここで結論を出さない）

- **表セル `` route `x` `` 形と、indent された `  - ` sub-bullet で `route: ` を含む形は、
  最小化後の pr-w3 fixture には 1 件も無い**（実測: それぞれ 0 件 / 0 件。indent sub-bullet
  自体は 78 行あるが `route: ` を含む行は無い）。`design.md` § telemetry が
  「当該 worklog に 10 行実在」「節内に多数実在」と書いたのは**最小化前のソース worklog**に
  対する記述で、出荷 fixture には当てはまらない。よって両形の負の assert は
  `_LINE_FORMS` の**合成 1 行**でだけ測っており、fixture の固定値 assert は両形を覆っていない
- code fence の扱い。parser は fence を剥がさず、正本節も fence 規則を持たない
  （T-11 impl-gate advisory L-2 = 許容として記録）。本テストは fence について何も固定しない
- 行番号での所在。telemetry の出力粒度は `steering_id` / `worktree` までで行番号を持たない
- repo 外の可変 corpus（`~/.gdd/worktrees/**` 等）に対する集計。非決定なので入力は
  fixture と合成入力に限る
"""
from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# 共通規約 13: `python3 -m unittest tests.<module>` 起動では tests/ が sys.path に
# 載らず、sibling の `_plugin_module_loader` が解決できずに collection error になる。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import PLUGIN_ROOT  # noqa: E402

_SCRIPT = PLUGIN_ROOT / "scripts" / "collect-gdd-telemetry.py"
_FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
_PR_W3_FIXTURE = _FIXTURES / "route-decision-pr-w3-min.md"
_DRIFT_FIXTURE = _FIXTURES / "route-decision-drift-min.md"
_SURFACE_DOC = PLUGIN_ROOT / "references" / "phase-progression.md"

#: 凍結 fixture に対する期待値（AC-9）。**件数の literal はこの表 1 箇所だけ**。
#: pr-w3 = `## Route Decision` 節の F1 20 件 + 別節の F2 1 件 / 未パース 3 節。
#: drift = `## <date> Systematic Debugging Route Decision` 節の F2 1 件 / 未パース 0。
_FIXTURE_EXPECTED: tuple[tuple[Path, str, int, int], ...] = (
    (_PR_W3_FIXTURE, "20260817-pr-w3-self-review", 21, 3),
    (_DRIFT_FIXTURE, "20260407-example-allowlist", 1, 0),
)

#: `## Route Decision` 節に 1 行だけ置いたときの `(bounce_count, unparsed_route_sections)`。
#: 計上されない行しか無い節は、その節ごと `unparsed_route_sections` に 1 件出る。
_LINE_FORMS: tuple[tuple[str, tuple[int, int], str], ...] = (
    (
        "- 2026-01-01 | Current Task: **T-1** | route: `implementation_fix_only`",
        (1, 0),
        "F1 正本書式。新規記録はこれで書く",
    ),
    (
        "- **route 判定**: Routing Decision Tree Step 2 = Yes",
        (1, 0),
        "F2 太字あり（pr-w3 fixture の実在形）",
    ),
    (
        "- route 判定:",
        (1, 0),
        "F2 太字なし（drift fixture の実在形）",
    ),
    (
        "- **route 判断**: Routing Decision Tree Step 2 = Yes",
        (0, 1),
        "A-10。`判定` -> `判断` の 1 文字差で F2 に一致しない。正本節の列挙には無いが一般則で未パース行き",
    ),
    (
        "- Route: human_recheck_required",
        (0, 1),
        "§ Escalation Decision Table の記録例。F1 は `route: ` の部分一致なので大文字始まりは不一致",
    ),
    (
        "- **選んだ route**: `design_detail_only`",
        (0, 1),
        "正本節が列挙する計上対象外の形",
    ),
    (
        "- route判定: 空白なし",
        (0, 1),
        "F2 は `route 判定`（間に半角空白）始まり。空白を落とした形は受理しない",
    ),
    (
        "  - route: `nested`",
        (0, 1),
        "indent された sub-bullet は計上しない（トップレベル `- ` 行のみ）",
    ),
    (
        "| T-1 | route `implementation_fix_only` | build 継続 |",
        (0, 1),
        "表セル形。`- ` 始まりではないので計上しない",
    ),
    (
        "- route:`implementation_fix_only`",
        (0, 1),
        "F1 token は `route: `（末尾空白まで）。`:` の直後に値が来る形は受理しない",
    ),
)

#: section 単位の形。`worklog.md` 全文として渡す。
_SECTION_FORMS: tuple[tuple[str, tuple[int, int], str], ...] = (
    (
        "## Batch Route Decisions (2026-04-19T12:34:00Z)\n- T-1: implementation_fix_only\n",
        (0, 1),
        "1 turn の batch 内 per-task マップ。差し戻しイベント 1 回とは粒度が違うため計上対象外",
    ),
    (
        "## 2026-08-18 remediation（route `implementation_fix_only`）\n- 対象: M-1 / M-2\n",
        (0, 1),
        "見出しだけが route 値を持ち、本文に該当行が無い形",
    ),
    (
        "## Route Decision\n- 2026-01-01 | route: `x`\n\n## Route Decision\n- Route: none\n",
        (1, 1),
        "節境界で flush されること（片方だけ計上・片方だけ未パース）",
    ),
    (
        "## 実装メモ\n- 2026-01-01 | route: `implementation_fix_only`\n",
        (0, 0),
        "anchor に一致しない見出しの下は、F1 形でも計上しないし未パースにも出さない",
    ),
    (
        "##### Route Decision\n- 2026-01-01 | route: `implementation_fix_only`\n",
        (0, 0),
        "見出し level の上限外（正本は `^#{2,4} `）。見出しと見なさないので節が始まらない",
    ),
    (
        "# Route Decision\n- 2026-01-01 | route: `implementation_fix_only`\n",
        (0, 0),
        "見出し level の下限外。同上",
    ),
    (
        "## routes overview\n- 2026-01-01 | route: `implementation_fix_only`\n",
        (0, 0),
        "anchor の `route` は後ろに空白が要る。`routes` は route section ではない",
    ),
)

#: fixture 側の逐語形の交差表（A-11 / A-15）。行頭一致の件数。
#: F2 が太字有無の両形を受理するため、この 2 形は件数述語ではどちらも pin されない。
_VERBATIM_FORMS: tuple[str, ...] = ("- **route 判定**:", "- route 判定:")
_VERBATIM_EXPECTED: tuple[tuple[Path, tuple[int, ...], str], ...] = (
    (_PR_W3_FIXTURE, (1, 0), "A-11: 太字を剥がしても件数 (21, 3) は不変なので、逐語形で pin する"),
    (_DRIFT_FIXTURE, (0, 1), "A-15: 太字を付けても件数 (1, 0) は不変（A-11 の鏡像）"),
)

#: AC-10 の所在を測る合成 root。値は `(unparsed 節数, bounce 節数)`。
#: (a) unparsed 0 の task を含む / (b) id 昇順・件数降順・件数昇順が互いに異なる /
#: (c) 同数の組を含む —— の 3 条件を満たすように選んである。
_LOCATION_ROOT: tuple[tuple[str, int, int], ...] = (
    ("aaa-alpha", 1, 1),
    ("bbb-beta", 3, 0),
    ("ccc-gamma", 2, 0),
    ("ddd-delta", 2, 1),
    ("eee-epsilon", 0, 2),
)
_LOCATION_EXPECTED_TEXT = (
    "- total_bounce_count: 4\n"
    "- total_unparsed_route_sections: 8\n"
    "- unparsed_by_task:\n"
    "  - bbb-beta: 3\n"
    "  - ccc-gamma: 2\n"
    "  - ddd-delta: 2\n"
    "  - aaa-alpha: 1"
)

_UNPARSED_SECTION = "## Route Decision\n- Route: none\n\n"
_BOUNCE_SECTION = "## Route Decision\n- 2026-01-01 | route: `implementation_fix_only`\n\n"

_BOUNCE_HEADING = "### Bounce (Route Decision)"


def _write_steering(root: Path, slug: str, worklog_text: str) -> None:
    steering = root / ".steering" / slug
    steering.mkdir(parents=True)
    steering.joinpath("state.md").write_text(
        "Resume From: gdd-test-driven-development\nRoute In Progress: none\n", encoding="utf-8"
    )
    steering.joinpath("worklog.md").write_text(worklog_text, encoding="utf-8")


def _run(root: Path, fmt: str) -> str:
    """出荷スクリプトそのものを subprocess で実行する（user-visible side effect path）。"""
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(root), "--format", fmt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise AssertionError(f"telemetry exited {proc.returncode}: {proc.stderr}")
    return proc.stdout


def _render_single(worklog_text: str, slug: str, fmt: str) -> str:
    """steering 1 本だけの root を作って出荷スクリプトを掛ける（単一 task の入力口）。"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_steering(root, slug, worklog_text)
        return _run(root, fmt)


def _render_fixture(fixture: Path, slug: str, fmt: str) -> str:
    """凍結 fixture 1 本を worklog として置いたときの出力。"""
    return _render_single(fixture.read_text(encoding="utf-8"), slug, fmt)


def _counts(worklog_text: str, slug: str = "20260101-synthetic") -> tuple[int, int]:
    """1 steering 分の `(bounce_count, unparsed_route_sections)` を json から取る。"""
    task = json.loads(_render_single(worklog_text, slug, "json"))["tasks"][0]
    return task["bounce_count"], task["unparsed_route_sections"]


def _bounce_block(text_output: str) -> str:
    """text 出力の `### Bounce (Route Decision)` 以降を取り出す。"""
    index = text_output.index(_BOUNCE_HEADING)
    return text_output[index + len(_BOUNCE_HEADING):].strip("\n")


def _recorded_example() -> str:
    """出荷 doc § Escalation Decision Table の複数境界記録例（fence 内）を取り出す。"""
    chunks = _SURFACE_DOC.read_text(encoding="utf-8").split("\n### ")
    section = next((c for c in chunks if c.startswith("Escalation Decision Table")), None)
    if section is None:
        raise AssertionError("§ Escalation Decision Table が references/phase-progression.md に無い")
    # ``` で割ると奇数番目が fence 内。fence 内の先頭行は info string なので落とす。
    blocks = [chunk.partition("\n")[2] for chunk in section.split("```")[1::2]]
    matched = [b for b in blocks if b.startswith("## Route Decision (")]
    if len(matched) != 1:
        raise AssertionError(f"記録例の fence が 1 個ではない: {len(matched)}")
    return matched[0]


class FixtureCountContractTests(unittest.TestCase):
    """AC-9 / AC-8: 凍結 fixture の計上件数を 3 形式すべてで固定値 assert する。"""

    def test_json_reports_fixture_counts(self):
        for fixture, slug, bounce, unparsed in _FIXTURE_EXPECTED:
            with self.subTest(fixture=fixture.name):
                payload = json.loads(_render_fixture(fixture, slug, "json"))
                self.assertEqual(len(payload["tasks"]), 1, payload["tasks"])
                task = payload["tasks"][0]
                self.assertEqual(task["steering_id"], slug)
                self.assertEqual(task["bounce_count"], bounce)
                self.assertEqual(task["unparsed_route_sections"], unparsed)
                self.assertEqual(payload["summary"]["bounce"]["total_bounce_count"], bounce)
                self.assertEqual(
                    payload["summary"]["bounce"]["total_unparsed_route_sections"], unparsed
                )

    def test_text_reports_fixture_counts(self):
        for fixture, slug, bounce, unparsed in _FIXTURE_EXPECTED:
            with self.subTest(fixture=fixture.name):
                block = _bounce_block(_render_fixture(fixture, slug, "text"))
                self.assertIn(f"- total_bounce_count: {bounce}", block)
                self.assertIn(f"- total_unparsed_route_sections: {unparsed}", block)

    def test_csv_reports_fixture_counts(self):
        for fixture, slug, bounce, unparsed in _FIXTURE_EXPECTED:
            with self.subTest(fixture=fixture.name):
                rows = list(csv.DictReader(io.StringIO(_render_fixture(fixture, slug, "csv"))))
                self.assertEqual(len(rows), 1, rows)
                self.assertEqual(rows[0]["bounce_count"], str(bounce))
                self.assertEqual(rows[0]["unparsed_route_sections"], str(unparsed))


class AcceptanceSurfaceFormTests(unittest.TestCase):
    """受理面の型空間を列挙して、計上する形としない形を 1 行単位で分離する。"""

    def test_line_forms_match_acceptance_surface(self):
        for line, expected, why in _LINE_FORMS:
            with self.subTest(line=line, why=why):
                self.assertEqual(_counts(f"## Route Decision\n{line}\n"), expected)

    def test_section_forms_match_acceptance_surface(self):
        for worklog, expected, why in _SECTION_FORMS:
            with self.subTest(why=why):
                self.assertEqual(_counts(worklog), expected)


class RecordedExampleContractTests(unittest.TestCase):
    """`- Route:` と F1 の不一致（owner T-12）を、出荷 doc の記録例そのもので固定する。"""

    def test_escalation_table_example_is_not_counted(self):
        example = _recorded_example()
        self.assertIn("\n- Route: ", "\n" + example, example)
        self.assertNotIn("- route: ", example, "記録例が F1 に寄せられたなら本テストの前提が変わる")
        self.assertEqual(_counts(example), (0, 1))


class FixtureVerbatimFormTests(unittest.TestCase):
    """A-11 / A-15: 件数述語が守らない 2 種の逐語形を、交差表で両側 pin する。"""

    def test_fixtures_keep_both_verbatim_forms(self):
        for fixture, expected, why in _VERBATIM_EXPECTED:
            lines = fixture.read_text(encoding="utf-8").splitlines()
            for form, count in zip(_VERBATIM_FORMS, expected):
                with self.subTest(fixture=fixture.name, form=form, why=why):
                    self.assertEqual(sum(1 for line in lines if line.startswith(form)), count)


class UnparsedLocationTests(unittest.TestCase):
    """AC-10: 未パース節の件数だけでなく所在（どの task か）が出ること。"""

    def _location_root(self, tmp: str) -> Path:
        root = Path(tmp)
        for slug, unparsed, bounce in _LOCATION_ROOT:
            _write_steering(root, slug, _UNPARSED_SECTION * unparsed + _BOUNCE_SECTION * bounce)
        return root

    def test_text_lists_unparsed_tasks_by_count_then_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = _run(self._location_root(tmp), "text")
        self.assertEqual(_bounce_block(out), _LOCATION_EXPECTED_TEXT)

    def test_json_keeps_zero_unparsed_tasks_as_rows(self):
        """所在の per-task 行は 0 件の task も残す（text の一覧だけが 0 を落とす）。"""
        with tempfile.TemporaryDirectory() as tmp:
            payload = json.loads(_run(self._location_root(tmp), "json"))
        actual = {t["steering_id"]: t["unparsed_route_sections"] for t in payload["tasks"]}
        self.assertEqual(actual, {slug: unparsed for slug, unparsed, _ in _LOCATION_ROOT})

    def test_text_omits_the_list_when_nothing_is_unparsed(self):
        """no-op / silent success path。未パース 0 なら一覧の節ごと出さない。"""
        fixture, slug, _, unparsed = _FIXTURE_EXPECTED[1]
        self.assertEqual(unparsed, 0, "drift fixture は未パース 0 の入力として使っている")
        out = _render_fixture(fixture, slug, "text")
        self.assertIn("- total_unparsed_route_sections: 0", out)
        self.assertNotIn("unparsed_by_task", out)


if __name__ == "__main__":
    unittest.main()


class RouteInProgressSharedSurfaceTests(unittest.TestCase):
    """collector が **done guard と同じ受理面**で `Route In Progress` を読む。

    2026-08-31 の独立最終レビューの指摘。`select_route_in_progress()` の共有化は
    「実データでの不一致が無くなる」ことを根拠に入れたのに、
    **退行検出器が 1 本も無かった**（改訂前の `extract_field(...) or "none"` に戻す変異が
    全 suite で SURVIVED した）。
    """

    def _route(self, state_body: str) -> str:
        """出荷 collector を **subprocess で** 実行して `route_in_progress` を得る。

        既存テストと同じ呼び出し方に揃える（module import ではなく実行可能性まで見る）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "wt" / ".steering" / "20260101-x"
            d.mkdir(parents=True)
            (d / "state.md").write_text(state_body, encoding="utf-8")
            (d / "tasklist.md").write_text("## Current Task\n\n- なし\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(_SCRIPT), "--root", str(Path(tmp) / "wt"), "--format", "json"],
                capture_output=True, text=True, check=True,
            )
            tasks = json.loads(proc.stdout)["tasks"]
            self.assertEqual(1, len(tasks), f"stdout={proc.stdout}")
            return tasks[0]["route_in_progress"]

    def test_annotated_none_is_not_a_live_route(self):
        """`none | reason: ...` / `none（注記）` / `**none**` / `None` は解除扱い。

        注記を値の一部として集計すると **1 件ごとに別バケット**になり、
        route 別集計が原理的に成立しない（`state.md` の注記が予告していた形）。
        """
        for val in (
            "none | reason: design-gating 通過 | updated_by: gdd-design-gating",
            "none（2026-08-21 / 人間による解除で T-30 を approved とした）",
            "**none**",
            "NONE",
        ):
            with self.subTest(val=val):
                self.assertEqual("none", self._route(f"- Route In Progress: {val}\n"), f"val={val}")

    def test_live_route_is_reported_as_the_bare_enum(self):
        """negative control: 非 none は**素の enum** で報告する（空洞にしない）。"""
        self.assertEqual(
            "implementation_fix_only",
            self._route("- Route In Progress: implementation_fix_only | reason: T-27 の remediation 中\n"),
        )

    def test_the_last_canonical_line_wins_in_the_collector_too(self):
        """解除の追記が無視されない（done guard と同じ last-wins）。"""
        self.assertEqual(
            "none",
            self._route("- Route In Progress: human_recheck_required\n- Route In Progress: none\n"),
        )
