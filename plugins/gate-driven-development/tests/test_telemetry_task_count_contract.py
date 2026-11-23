"""T-6 契約テスト: telemetry の task カウントを共有受理面（`lib/tasklist_parse`）へ固定する。

対象は `scripts/collect-gdd-telemetry.py` の `parse_task_metrics()` が返す
`pending_tasks` / `completed_tasks`。現行実装は `^###\\s+Task:` の 2 行
（design.md § AC-6 棚卸し表の `collect-gdd-telemetry.py:178/188`）で数えており、
`### Task N:` を取りこぼす（done guard の見出しの取りこぼしと同型の silent failure）。

**測っている範囲**

- `parse_task_metrics()` に渡される 1 steering の `## Pending Tasks` / `## Completed Tasks`
  各節に **1 行だけ**置いた見出し候補の受理/不受理（`_HEADING_FORMS` に列挙した型空間）
- 同じ節に複数行置いたときに **件数として合算**されること（bool 化した実装を弾く）
- `- なし` 節・`tasklist.md` 不在時に 0 になること
- 出荷スクリプトを `--format=json` で subprocess 実行したときの値（unit と同じ結論が
  CLI 経路でも出ること）

**測っていない範囲（意図的。ここで結論を出さない）**

- fenced code block の扱い。`gdd_stop_hook.py` は `strip_fenced_lines()` で剥がすが
  telemetry は剥がしておらず、本 task の AC-6 / design も剥がすことを要求していない。
  実測（2026-08-24 / `~/.gdd/worktrees/**/.steering/*/tasklist.md` ＝
  **repo 外の可変 corpus**）では fence を剥がしても件数は変わらないため、
  本テストは fence について**何も固定しない**。処置は planning 側の判断。
- `"なし" in body` による節丸ごとの短絡（`### Task 3: ...なし...` で節が 0 になる）。
  現行挙動であり本 task の変更対象外。`- なし` の canonical 形だけ pin する。
- `## Task: x` 形式。節の区切り正規表現（`(?=\\n##\\s)`）と衝突して節自体を切るため、
  1 行 fixture の型空間から除外した。
- text / csv の描画。値の出所は同じ dataclass なので json 1 形式で代表させる。

**両側 pin**: 各形の期待値は表にリテラルで書き（対象側の pin）、同じ subtest 内で
共有 module（`classify_task_line`）から導いた参照値とも突き合わせる（検査側の pin）。
どちらか一方だけが動いた場合に落ちる。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# 共通規約 13: `python3 -m unittest tests.<module>` 起動では tests/ が sys.path に
# 載らず、sibling の `_plugin_module_loader` が解決できずに collection error になる。
# pytest / `unittest discover` だけで確認すると取りこぼす（実測済み）。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import PLUGIN_ROOT, load_plugin_module  # noqa: E402

_TELEMETRY = load_plugin_module("scripts/collect-gdd-telemetry.py")
_TASKLIST_PARSE = load_plugin_module("hooks/scripts/lib/tasklist_parse.py")

parse_task_metrics = _TELEMETRY.parse_task_metrics
classify_task_line = _TASKLIST_PARSE.classify_task_line

_TELEMETRY_SCRIPT = PLUGIN_ROOT / "scripts" / "collect-gdd-telemetry.py"

#: 受理面の型空間。`expected` は「その 1 行だけを節に置いたときの件数」。
#: 見出し形（`###` 始まり）だけを数える現行仕様は維持する（`- T-N |` 形式は
#: `classify_task_line` では task だが telemetry は数えない ＝ 表の 0 行）。
_HEADING_FORMS: tuple[tuple[str, int, str], ...] = (
    ("### Task: 説明", 1, "正準形（現行も受理）"),
    ("### Task 1: 説明", 1, "採番形。本 task が閉じる取りこぼし"),
    ("### Task 12: 説明", 1, "2 桁採番"),
    ("### Task : 説明", 1, "`Task` と `:` の間に空白。共有受理面は受理する"),
    ("###Task: 説明", 1, "`###` の直後に空白なし。共有受理面は受理する"),
    ("#### Task: 説明", 1, "h4 見出し。現行の `^###\\s+Task:` は受理しない"),
    ("### Task: 説明   ", 1, "末尾空白で落とさない（gdd_stop_hook が踏んだ退行の isolate 版）"),
    ("### Task:", 0, "名前が空。現行の正規表現は誤って受理する"),
    ("### Task:　", 0, "名前が全角空白のみ。現行の正規表現は誤って受理する"),
    ("### Task Size Distribution", 0, "`Task` の直後が `:` でない"),
    ("### Tasks: 一覧", 0, "`Tasks` は task 見出しではない"),
    ("### Task-1: 説明", 0, "`Task-N` は採番形ではない"),
    ("# Task: 説明", 0, "h1 は共有受理面の下限（`##`）外"),
    ("- Task: 説明", 0, "共有受理面では task だが見出しではない ＝ telemetry は数えない"),
    ("- T-1 | AC-01 | 説明", 0, "list-item 形式。同上（現行仕様を維持する）"),
    ("- T-helper | 説明", 0, "`T` の直後が数字でない ＝ task ではない"),
    ("  ### Task 1: 説明", 0, "インデント行は tasklist の構造ではない（design § 論点 2c）"),
    ("\t### Task 1: 説明", 0, "タブインデントも同じ"),
)


def _shared_surface_count(line: str) -> int:
    """共有 module から導いた参照値（検査側 pin）。

    - 行頭ぴったりであること（`gdd_stop_hook.py` の done guard / 進捗表示と同じ規約）
    - 共有 module が task と分類すること
    - かつ見出し形であること（telemetry は list-item を数えない現行仕様を維持）
    """
    if line != line.lstrip():
        return 0
    stripped = line.strip()
    if not stripped.startswith("###"):
        return 0
    return 1 if classify_task_line(stripped) == "task" else 0


def _write_steering(tmp: Path, *, pending: str, completed: str, tasklist: bool = True) -> Path:
    steering = tmp / ".steering" / "20260822-target"
    steering.mkdir(parents=True)
    (steering / "state.md").write_text(
        "Resume From: gdd-test-driven-development\nRoute In Progress: none\n",
        encoding="utf-8",
    )
    if tasklist:
        (steering / "tasklist.md").write_text(
            "# Tasklist\n\n## Current Task\n- なし\n\n"
            f"## Pending Tasks\n{pending}\n\n"
            f"## Completed Tasks\n{completed}\n\n"
            "## Status\nNext Action=gdd-test-driven-development\n",
            encoding="utf-8",
        )
    return steering


def _metrics(pending: str, completed: str, *, tasklist: bool = True):
    with tempfile.TemporaryDirectory() as tmp:
        steering = _write_steering(Path(tmp), pending=pending, completed=completed, tasklist=tasklist)
        return parse_task_metrics(steering, "wtA")


class TelemetryTaskCountTests(unittest.TestCase):
    """AC-6 / design § parser: `### Task N:` を含む steering で件数が正しいこと。"""

    def test_numbered_heading_is_counted(self):
        """success path。現行は `pending_tasks == 0` で落ちる（RED の主因）。"""
        m = _metrics(
            pending="### Task 1: 説明\n- AC: AC-1",
            completed="### Task 2: 説明\n- AC: AC-2",
        )
        self.assertEqual(m.pending_tasks, 1)
        self.assertEqual(m.completed_tasks, 1)

    def test_canonical_heading_stays_counted(self):
        """デグレ防止。正準形 `### Task:` の現行挙動を変えない。"""
        m = _metrics(
            pending="### Task: 説明\n- AC: AC-1",
            completed="### Task: 説明\n- AC: AC-2",
        )
        self.assertEqual(m.pending_tasks, 1)
        self.assertEqual(m.completed_tasks, 1)

    def test_headings_are_summed_not_flagged(self):
        """件数であって bool ではないこと（`any()` 化した実装を弾く）。

        混在させるのは、正準形と採番形が同じ節に同居する実データの形。
        """
        pending = textwrap.dedent(
            """\
            ### Task 1: 説明
            - AC: AC-1
            ### Task: 説明
            - AC: AC-2
            ### Task 12: 説明
            - AC: AC-3"""
        )
        completed = "### Task 3: 説明\n- AC: AC-4\n### Task 4: 説明\n- AC: AC-5"
        m = _metrics(pending=pending, completed=completed)
        self.assertEqual(m.pending_tasks, 3)
        self.assertEqual(m.completed_tasks, 2)

    def test_empty_marker_and_missing_tasklist_count_zero(self):
        """no-op / silent success path。"""
        with self.subTest(case="- なし"):
            m = _metrics(pending="- なし", completed="- なし")
            self.assertEqual((m.pending_tasks, m.completed_tasks), (0, 0))
        with self.subTest(case="tasklist.md 不在"):
            m = _metrics(pending="", completed="", tasklist=False)
            self.assertEqual((m.pending_tasks, m.completed_tasks), (0, 0))


class AcceptanceSurfaceEquivalenceTests(unittest.TestCase):
    """受理面の型空間を列挙し、telemetry と共有 module の同値を固定する。

    節ごとに別 fixture を作るのは、`completed_tasks` / `pending_tasks` が
    **別々の呼び出し箇所**で数えられているため（片方だけ直した実装を弾く）。
    """

    def test_form_table_matches_shared_surface(self):
        """検査側 pin。表のリテラル期待値が共有 module から導けること。"""
        for line, expected, why in _HEADING_FORMS:
            with self.subTest(line=line, why=why):
                self.assertEqual(_shared_surface_count(line), expected)

    def test_pending_section_accepts_exactly_the_shared_surface(self):
        for line, expected, why in _HEADING_FORMS:
            with self.subTest(line=line, why=why):
                m = _metrics(pending=line, completed="- なし")
                self.assertEqual(m.pending_tasks, expected)

    def test_completed_section_accepts_exactly_the_shared_surface(self):
        for line, expected, why in _HEADING_FORMS:
            with self.subTest(line=line, why=why):
                m = _metrics(pending="- なし", completed=line)
                self.assertEqual(m.completed_tasks, expected)


class TelemetryCliOutputTests(unittest.TestCase):
    """user-visible side effect path。出荷スクリプトそのものを subprocess で実行する。"""

    def test_json_output_reports_numbered_task_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_steering(
                Path(tmp),
                pending="### Task 1: 説明\n- AC: AC-1\n### Task 2: 説明\n- AC: AC-2",
                completed="### Task 3: 説明\n- AC: AC-3",
            )
            proc = subprocess.run(
                [sys.executable, str(_TELEMETRY_SCRIPT), "--root", tmp, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(len(payload["tasks"]), 1, payload["tasks"])
            task = payload["tasks"][0]
            self.assertEqual(task["pending_tasks"], 2)
            self.assertEqual(task["completed_tasks"], 1)


if __name__ == "__main__":
    unittest.main()
