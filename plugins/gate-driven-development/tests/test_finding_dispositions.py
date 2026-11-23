"""reviewer の指摘の行き先（steering の `review-findings.md`）の検査のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_finding_dispositions.py -q`

正本: `references/finding-dispositions.md`。述語は `hooks/scripts/lib/finding_dispositions.py` にあり、
入口は 2 つ: impl-gating Step 8 で Round の判定を決める前に回す `scripts/check-finding-dispositions.py` と、push・PR の前に回す
`scripts/check-gate-ledger.sh` の `findings` 行（`Independent Review` 行の件数と突き合わせる）。
どちらも入口から exit・行の状態が変わるまでを通す。
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _paths import PLUGIN_ROOT
from test_check_gate_ledger import GateLedgerFixture, _independent_review

CLI = PLUGIN_ROOT / "scripts" / "check-finding-dispositions.py"
REVIEWER_COMMON = PLUGIN_ROOT / "references" / "reviewer-common.md"
NOT_OK = {"missing", "invalid", "error"}
TABLE = "| id | severity | category | file:line | 行き先 | 検証 | 根拠 |\n|---|---|---|---|---|---|---|\n"

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib import finding_dispositions as fd  # noqa: E402


# IG 節の見出しの sha の既定値。CliTest は書き出すときに HEAD の sha に置き換える
IG_SHA = "abc1234"


def section(name: str, key: str, value: str, rows: list[str], n: int | None = None, sha: str = IG_SHA,
            round_: int = 0) -> str:
    count = n if n is not None else sum(1 for r in rows if re.match(rf"\| {name}-\d", r))
    head = f"task: {value} | sha: {sha} | round: {round_}" if key == "task" else f"{key}: {value}"
    return f"## {name} | {head} | findings: {count}\n\n{TABLE}" + "".join(r + "\n" for r in rows) + "\n"


def row(rid: str, severity: str = "medium", category: str = "product", dest: str = "advisory",
        evidence: str = "-", verify: str = "-", location: str = "a.py:1") -> str:
    return f"| {rid} | {severity} | {category} | {location} | {dest} | {verify} | {evidence} |"


def run_cli(steering: Path, *extra: str) -> tuple[int, list[list[str]]]:
    result = subprocess.run(
        [sys.executable, str(CLI), "--steering", str(steering), *extra], capture_output=True, text=True, check=False,
    )
    rows = [line.split("\t") for line in result.stdout.splitlines()]
    assert rows and all(len(r) == 4 for r in rows), result.stdout + result.stderr
    return result.returncode, rows


def write_tasklist(steering: Path, tasks: dict[str, int | None]) -> None:
    """tasklist.md の Current Task に task を並べる。値はその task の Gate Rounds（None なら行を書かない）。"""
    body = "".join(f"### Task: {t} 説明\n" + (f"- Gate Rounds: {n}\n" if n is not None else "") + "\n"
                   for t, n in tasks.items())
    (steering / "tasklist.md").write_text(f"# Tasklist\n\n## Current Task\n\n{body}## Pending Tasks\n",
                                          encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        repo = Path(self._tmp.name) / "repo"
        repo.mkdir()
        init_repo(repo)
        self.head = _git(repo, "rev-parse", "HEAD")
        self.steering = repo / ".steering" / "20261022-x"
        self.steering.mkdir(parents=True)
        write_tasklist(self.steering, {"T-1": None, "T-2": None})

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, body: str) -> None:
        # 今回の Round の IG 節は HEAD の sha で書く（CLI は --task の節の sha を HEAD と突き合わせる）
        text = "# Findings\n\n" + body.replace(IG_SHA, self.head)
        (self.steering / "review-findings.md").write_text(text, encoding="utf-8")

    def cli(self, *extra: str) -> tuple[int, list[list[str]]]:
        return run_cli(self.steering, "--task", "T-1", *extra)

    def assert_invalid(self, body: str, needle: str) -> None:
        self.write(body)
        code, rows = self.cli()
        self.assertEqual(code, 1, rows)
        bad = [r for r in rows if r[0] in NOT_OK]
        self.assertTrue(any(needle in r[3] for r in bad), rows)

    def test_valid_file_passes(self) -> None:
        self.write(
            section("IG1", "task", "T-1, T-2", [
                row("IG1-1", "high", "fail-open", "blocking"),
                row("IG1-2", "medium", "product", "advisory"),
                row("IG1-3", "high", "product", "rejected:refuted", "b.py:3", verify="refuted"),
                row("IG1-4", "medium", "style", "rejected:duplicate:IG1-2"),
            ])
            + section("IG2", "task", "T-1", [row("IG2-1", "high", "fail-open", "re-reported:IG1-1")])
            + section("IR1", "sha", "abc1234", [], n=0)
        )
        code, rows = self.cli()
        self.assertEqual(code, 0, rows)
        self.assertEqual([r[0] for r in rows], ["ok"])

    # --- 安全策 2 の 1: 止めるべき入力が通る ---

    def test_ir_high_cannot_be_advisory(self) -> None:
        self.assert_invalid(
            section("IR1", "sha", "abc1234", [row("IR1-1", "high", "product", "advisory:out_of_scope")]),
            "IR1-1",
        )

    def test_ir_blocking_category_cannot_be_advisory(self) -> None:
        self.assert_invalid(
            section("IR1", "sha", "abc1234", [row("IR1-1", "medium", "data-loss", "advisory")]),
            "IR1-1",
        )

    def test_ig_high_cannot_be_plain_advisory(self) -> None:
        self.assert_invalid(section("IG1", "task", "T-1", [row("IG1-1", "high", "product", "advisory")]), "IG1-1")

    def test_ig_high_cannot_be_insufficient_evidence(self) -> None:
        self.assert_invalid(
            section("IG1", "task", "T-1", [row("IG1-1", "high", "product", "advisory:insufficient_evidence")]),
            "IG1-1",
        )

    def test_ig_blocking_category_cannot_be_calibrated(self) -> None:
        # 検証役が refuted と判定しても、実害クラスは calibration で下げられない
        for severity in ("high", "medium"):
            with self.subTest(severity=severity):
                self.assert_invalid(
                    section("IG1", "task", "T-1", [
                        row("IG1-1", severity, "fail-open", "advisory:calibration", verify="refuted")]),
                    "calibration で advisory にできない",
                )

    def test_ig_high_downgrades_that_the_gate_allows(self) -> None:
        # out_of_scope は再入（同じ task の IG 節が前にある）ときだけ
        self.write(section("IG1", "task", "T-1", []) + section("IG2", "task", "T-1", [
            row("IG2-1", "high", "product", "advisory:calibration", "b.py:3", verify="refuted"),
            row("IG2-2", "high", "fail-open", "advisory:unverified_file", "b.py:4", verify="refuted"),
            row("IG2-3", "high", "fail-open", "advisory:out_of_scope"),
        ]))
        code, rows = self.cli()
        self.assertEqual(code, 0, rows)

    def test_refuted_needs_evidence(self) -> None:
        self.assert_invalid(
            section("IG1", "task", "T-1", [row("IG1-1", "medium", "product", "rejected:refuted", "-", verify="refuted")]), "IG1-1"
        )

    def test_section_numbers_run_through_the_steering_across_tasks(self) -> None:
        # 節の番号は task ごとの Gate Rounds ではなく、steering 通しの連番（IG と IR で別々）
        self.write(
            section("IG1", "task", "T-1", [row("IG1-1", "high", "fail-open", "blocking")])
            + section("IG2", "task", "T-1", [])
            + section("IR1", "sha", "abc1234", [])
            + section("IG3", "task", "T-2", [row("IG3-1")])
        )
        code, rows = self.cli()
        self.assertEqual(code, 0, rows)

    def test_section_numbers_must_start_at_1_in_file_order(self) -> None:
        self.assert_invalid(section("IG2", "task", "T-1", [row("IG2-1")]), "IG2")
        self.assert_invalid(
            section("IG1", "task", "T-1", []) + section("IG3", "task", "T-2", []), "IG3"
        )
        self.assert_invalid(section("IR2", "sha", "abc1234", []), "IR2")
        self.assert_invalid(
            section("IG2", "task", "T-1", []) + section("IG1", "task", "T-2", []), "IG2"
        )

    def test_gap_in_numbering(self) -> None:
        self.assert_invalid(
            section("IG1", "task", "T-1", [row("IG1-1"), row("IG1-3")], n=3), "IG1"
        )

    def test_count_line_larger_than_rows(self) -> None:
        self.assert_invalid(section("IG1", "task", "T-1", [row("IG1-1")], n=2), "IG1")

    def test_duplicate_must_point_to_same_round_kept_row(self) -> None:
        self.assert_invalid(
            section("IG1", "task", "T-1", [row("IG1-1")])
            + section("IG2", "task", "T-1", [row("IG2-1", dest="rejected:duplicate:IG1-1")]),
            "IG2-1",
        )
        self.assert_invalid(
            section("IG1", "task", "T-1", [
                row("IG1-1", dest="rejected:duplicate:IG1-2"), row("IG1-2", dest="rejected:duplicate:IG1-1"),
            ]),
            "IG1-",
        )

    def test_re_reported_must_point_to_earlier_round(self) -> None:
        self.assert_invalid(
            section("IG1", "task", "T-1", [row("IG1-1", dest="re-reported:IG2-1")])
            + section("IG2", "task", "T-1", [row("IG2-1")]),
            "IG1-1",
        )

    def test_main_carried_row_must_be_re_reported(self) -> None:
        self.assert_invalid(
            section("IR2", "sha", "abc1234", [row("IR2-m1", "high", "product", "blocking")], n=0), "IR2-m1"
        )

    # --- 検証役（agents/gdd-finding-verifier.md）を通さずに捨てる・下げる ---

    def test_refuted_requires_the_verifier_to_refute(self) -> None:
        for verify in ("-", "confirmed", "unverifiable"):
            with self.subTest(verify=verify):
                self.assert_invalid(section("IG1", "task", "T-1", [
                    row("IG1-1", "medium", "product", "rejected:refuted", "b.py:3", verify=verify),
                ]), "IG1-1")
        self.assert_invalid(section("IR1", "sha", "abc1234", [
            row("IR1-1", "low", "style", "rejected:refuted", "b.py:3"),
        ]), "IR1-1")

    def test_serious_downgrade_requires_the_verifier_to_refute(self) -> None:
        for dest in ("advisory:calibration", "advisory:unverified_file"):
            for verify in ("-", "confirmed", "unverifiable"):
                with self.subTest(dest=dest, verify=verify):
                    self.assert_invalid(section("IG1", "task", "T-1", [
                        row("IG1-1", "high", "product", dest, verify=verify),
                    ]), "IG1-1")

    def test_verifier_is_not_required_where_no_one_is_dropped(self) -> None:
        self.write(section("IG1", "task", "T-1", []) + section("IG2", "task", "T-1", [
            row("IG2-1", "high", "product", "advisory:out_of_scope"),
            row("IG2-2", "medium", "product", "advisory:calibration"),
            row("IG2-3", "high", "fail-open", "blocking", verify="confirmed"),
        ]))
        code, rows = self.cli()
        self.assertEqual(code, 0, rows)

    def test_verify_value_outside_the_domain(self) -> None:
        self.assert_invalid(section("IG1", "task", "T-1", [row("IG1-1", verify="yes")]), "IG1-1")

    def test_duplicate_cannot_point_to_a_lighter_row(self) -> None:
        for rows_ in (
            [row("IG1-1", "high", "product", "rejected:duplicate:IG1-2"), row("IG1-2", "low", "product")],
            [row("IG1-1", "medium", "fail-open", "rejected:duplicate:IG1-2"),
             row("IG1-2", "medium", "product", "blocking")],
        ):
            with self.subTest(rows=rows_):
                self.assert_invalid(section("IG1", "task", "T-1", rows_), "IG1-1")
        self.write(section("IG1", "task", "T-1", [
            row("IG1-1", "low", "product", "rejected:duplicate:IG1-2"),
            row("IG1-2", "high", "fail-open", "blocking"),
        ]))
        code, rows = self.cli()
        self.assertEqual(code, 0, rows)

    def test_values_outside_the_domain(self) -> None:
        for bad in (row("IG1-1", severity="critical"), row("IG1-1", category="security"),
                    row("IG1-1", dest="adopted"), row("IG1-1", dest="advisory:later"),
                    row("IG1-1", dest="rejected:wontfix")):
            with self.subTest(bad=bad):
                self.assert_invalid(section("IG1", "task", "T-1", [bad]), "IG1-1")

    # --- 安全策 2 の 3: 判定できない形が通る ---

    def test_unreadable_shapes_are_not_ok(self) -> None:
        for body in (
            "## IG1 | task: T-1\n\n" + TABLE,  # 件数の欄が無い
            "## IX1 | task: T-1 | findings: 0\n",  # 巡の名前が値域の外
            "## IR1 | task: T-1 | findings: 0\n",  # IR に sha が無い
            "## IR1 | sha: not-a-sha | findings: 0\n",
            section("IG1", "task", "T-1", []).replace("| 根拠 |", "| メモ |"),  # 表の見出しが違う
            section("IG1", "task", "T-1", [row("IG1-1")]) + "自由文の行\n",  # 表の外の行
            section("IG1", "task", "T-1", ["| IG1-1 | medium | product | advisory | - |"], n=1),  # 欄が足りない
            section("IG1", "task", "T-1", []) + section("IG1", "task", "T-1", []),  # 巡の重複
        ):
            with self.subTest(body=body[:40]):
                self.write(body)
                code, rows = self.cli()
                self.assertEqual(code, 1, rows)
                self.assertTrue(any(r[0] in NOT_OK for r in rows), rows)

    def test_missing_file_is_missing(self) -> None:
        code, rows = self.cli()
        self.assertEqual(code, 1)
        self.assertEqual(rows[0][0], "missing")

    # --- 安全策 2 の 2: 例外で検査全体が落ちる ---

    def test_undecodable_file_is_error_not_crash(self) -> None:
        (self.steering / "review-findings.md").write_bytes(b"# Findings\n\n\xff\xfe\n")
        code, rows = self.cli()
        self.assertEqual(code, 1)
        self.assertIn(rows[0][0], NOT_OK)

    def test_directory_in_place_of_file_is_not_ok(self) -> None:
        (self.steering / "review-findings.md").mkdir()
        code, rows = self.cli()
        self.assertEqual(code, 1)
        self.assertIn(rows[0][0], NOT_OK)

    # --- 今回の Round の節（--task と HEAD の sha） ---

    def test_task_section_at_head_is_required(self) -> None:
        old = "1234567"  # HEAD でない sha
        cases = {
            "IR だけ": section("IR1", "sha", IG_SHA, [], n=0),
            "別の task だけ": section("IG1", "task", "T-2", []),
            "前の sha の節だけ": section("IG1", "task", "T-1", [], sha=old),
        }
        for name, body in cases.items():
            with self.subTest(case=name):
                self.write(body)
                code, rows = self.cli()
                self.assertEqual(code, 1, rows)
                self.assertTrue(any(r[0] == "invalid" and "T-1" in r[3] for r in rows), rows)
        for body in (section("IG1", "task", "T-2, T-1", []),  # Gate Batch
                     section("IG1", "task", "T-1", [], sha=old) + section("IG2", "task", "T-1", []),
                     section("IG1", "task", "T-1", [], sha=self.head[:8])):  # 短い sha
            with self.subTest(body=body[:40]):
                self.write(body)
                code, rows = self.cli()
                self.assertEqual(code, 0, rows)

    def test_round_number_must_match_gate_rounds(self) -> None:
        # 同じ HEAD のまま再 gate しても、今回の Round（Gate Rounds）の節が無ければ前の節で通さない
        write_tasklist(self.steering, {"T-1": 1})
        first = section("IG1", "task", "T-1", [row("IG1-1", "high", "fail-open", "blocking")])
        self.assert_invalid(first, "Gate Rounds")
        self.write(first + section("IG2", "task", "T-1", [], round_=1))
        self.assertEqual(self.cli()[0], 0)
        # 最後の節で比べる（Gate Rounds を 0 に戻した後に書き落とすと、前の round 0 の節では通さない）
        write_tasklist(self.steering, {"T-1": None})
        self.assert_invalid(first + section("IG2", "task", "T-1", [], round_=1), "Gate Rounds")
        # Gate Rounds の値が読めない
        (self.steering / "tasklist.md").write_text(
            "## Current Task\n\n### Task: T-1 説明\n- Gate Rounds: たくさん\n", encoding="utf-8")
        self.assert_invalid(first, "Gate Rounds")

    def test_task_must_be_in_current_task(self) -> None:
        self.write(section("IG1", "task", "T-3", []))
        code, rows = run_cli(self.steering, "--task", "T-3")
        self.assertEqual(code, 1, rows)
        self.assertTrue(any("T-3" in r[3] and "Current Task" in r[3] for r in rows), rows)
        # 番号の形でない task id も、見出しの名前の先頭で照合する
        write_tasklist(self.steering, {"Fix 9258bb7d3": None, "R-1": 2})
        self.write(section("IG1", "task", "Fix 9258bb7d3", []) + section("IG2", "task", "R-1", [], round_=2))
        self.assertEqual(run_cli(self.steering, "--task", "Fix 9258bb7d3")[0], 0)
        self.assertEqual(run_cli(self.steering, "--task", "R-1")[0], 0)
        self.assertEqual(run_cli(self.steering, "--task", "Fix")[0], 1)  # 名前の一部だけでは照合しない

    def test_every_task_of_the_argument_needs_its_section(self) -> None:
        self.write(section("IG1", "task", "T-1", []))
        code, rows = run_cli(self.steering, "--task", "T-1, T-2")
        self.assertEqual(code, 1, rows)
        self.assertTrue(any("T-2" in r[3] for r in rows if r[0] == "invalid"), rows)
        self.write(section("IG1", "task", "T-1, T-2", []))
        self.assertEqual(run_cli(self.steering, "--task", "T-1, T-2")[0], 0)

    def test_tasklist_that_cannot_be_read_is_not_ok(self) -> None:
        self.write(section("IG1", "task", "T-1", []))
        (self.steering / "tasklist.md").unlink()
        code, rows = self.cli()
        self.assertEqual(code, 1, rows)
        (self.steering / "tasklist.md").mkdir()
        code, rows = self.cli()
        self.assertEqual(code, 1, rows)
        self.assertTrue(any("tasklist.md" in r[3] for r in rows), rows)

    def test_task_argument_is_required(self) -> None:
        self.write(section("IG1", "task", "T-1", []))
        result = subprocess.run([sys.executable, str(CLI), "--steering", str(self.steering)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_steering_outside_git_is_not_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            steering = Path(tmp) / ".steering" / "x"
            steering.mkdir(parents=True)
            (steering / "review-findings.md").write_text(
                "# Findings\n\n" + section("IG1", "task", "T-1", []), encoding="utf-8")
            code, rows = run_cli(steering, "--task", "T-1")
            self.assertEqual(code, 1, rows)
            self.assertTrue(all(r[0] in NOT_OK or r[0] == "ok" for r in rows), rows)
            self.assertTrue(any(r[0] in NOT_OK for r in rows), rows)

    def test_ig_section_header_needs_task_and_sha(self) -> None:
        for header in ("## IG1 | task: T-1 | round: 0 | findings: 0\n",  # sha が無い
                       "## IG1 | sha: abc1234 | round: 0 | findings: 0\n",  # task が無い
                       "## IG1 | task: T-1 | sha: abc1234 | findings: 0\n",  # round が無い
                       "## IR1 | task: T-1 | sha: abc1234 | findings: 0\n",  # IR に task
                       "## IR1 | sha: abc1234 | round: 0 | findings: 0\n",  # IR に round
                       "## IG1 | task: T-1 | sha: abc1234 | round: x | findings: 0\n",
                       "## IG1 | task: T-1 | sha: xyz1234 | round: 0 | findings: 0\n"):
            with self.subTest(header=header):
                self.assertNotEqual(fd.structure_errors("# F\n\n" + header + "\n" + TABLE), [])

    # --- 引き継ぎ・duplicate・out_of_scope・refuted の根拠 ---

    def test_re_reported_cannot_be_lighter_than_its_target(self) -> None:
        # 独立レビューの件数から high・実害クラスを隠さない。IR 節の re-reported だけを見る
        for later in (row("IR2-m1", "medium", "fail-open", "re-reported:IR1-1"),
                      row("IR2-m1", "high", "product", "re-reported:IR1-1")):
            with self.subTest(row=later):
                self.assert_invalid(
                    section("IG1", "task", "T-1", [])
                    + section("IR1", "sha", "1234567", [row("IR1-1", "high", "fail-open", "blocking")])
                    + section("IR2", "sha", "1234567", [later], n=0),
                    "IR2-m1",
                )
        # IG では、一部を直した後に reviewer が軽くして再報告した行を止めない
        self.write(section("IG1", "task", "T-1", [row("IG1-1", "medium", "test-power", "advisory")])
                   + section("IG2", "task", "T-1", [row("IG2-1", "low", "test-power", "re-reported:IG1-1")]))
        self.assertEqual(self.cli()[0], 0)

    def test_duplicate_cannot_point_to_a_dropped_row(self) -> None:
        targets = [
            row("IG1-2", "high", "product", "rejected:refuted", "b.py:3", verify="refuted"),
            row("IG1-2", "high", "product", "blocking", verify="refuted"),
            row("IG1-2", "high", "fail-open", "advisory:unverified_file", f"absent@{IG_SHA}",
                location="src/ghost.py:3"),
        ]
        for target in targets:
            with self.subTest(target=target):
                self.assert_invalid(
                    section("IG1", "task", "T-1", [row("IG1-1", "high", "product", "rejected:duplicate:IG1-2"),
                                                   target]),
                    "IG1-1",
                )

    def test_ig_out_of_scope_needs_an_earlier_section_of_every_task(self) -> None:
        oos = [row("IG2-1", "high", "fail-open", "advisory:out_of_scope")]
        for earlier, tasks in ((section("IG1", "task", "T-2", []), "T-1"),  # 別の task の節だけ
                               (section("IG1", "task", "T-1", []), "T-1, T-3")):  # Gate Batch の一部だけ
            with self.subTest(tasks=tasks):
                self.assert_invalid(earlier + section("IG2", "task", tasks, oos), "IG2-1")
        self.assert_invalid(section("IG1", "task", "T-1", [row("IG1-1", "high", "fail-open", "advisory:out_of_scope")]),
                            "IG1-1")

    def test_refuted_verdict_needs_a_location(self) -> None:
        for dest in ("blocking", "advisory", "advisory:calibration", "rejected:refuted"):
            for evidence in ("-", "b.py の 3 行目", "b.py"):
                with self.subTest(dest=dest, evidence=evidence):
                    self.assert_invalid(section("IG1", "task", "T-1", [
                        row("IG1-1", "medium", "product", dest, evidence, verify="refuted")]), "IG1-1")

    def test_absent_location_form_is_checked_by_the_predicate(self) -> None:
        r = row("IG1-1", "high", "fail-open", "advisory:unverified_file", f"absent@{IG_SHA}",
                location="src/kept.py:12:5")
        self.assertNotEqual(fd.structure_errors("# F\n\n" + section("IG1", "task", "T-1", [r])), [])


class AbsentPathTest(unittest.TestCase):
    """impl-gating Step 1c: 根拠の path が merge-base にも tip にも無い high を、検証役なしで下げる。

    CLI が `根拠` の `absent@<sha>` の行の `file:line` を git で分類し、`never` のときだけ通す。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        init_repo(self.repo, branch="main")
        # 開発者の global 設定によらず、git が名前を引用符つき・NFD のまま出す形で確かめる
        _git(self.repo, "config", "core.quotePath", "true")
        _git(self.repo, "config", "core.precomposeunicode", "false")
        for name in ("src/kept.py", "src/gone.py", "src/moved.py", "src/設計.py", "src/\u304c.py",
                     "src/\u306f\u309a.py"):  # 最後は NFD の名前（ぱ）
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / name).write_text("x = 1\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "base")
        _git(self.repo, "switch", "-q", "-c", "feature")
        _git(self.repo, "rm", "-q", "src/gone.py")
        _git(self.repo, "mv", "src/moved.py", "src/renamed.py")
        (self.repo / "mid.py").write_text("y = 1\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "change")
        _git(self.repo, "rm", "-q", "mid.py")
        _git(self.repo, "commit", "-q", "-m", "drop mid")
        (self.repo / "src" / "wip.py").write_text("z = 1\n", encoding="utf-8")  # 未 commit
        (self.repo / "src" / "staged.py").write_text("s = 1\n", encoding="utf-8")
        _git(self.repo, "add", "src/staged.py")  # staged だけの新しい file
        self.head = _git(self.repo, "rev-parse", "HEAD")
        self.steering = self.repo / ".steering" / "20261023-x"
        self.steering.mkdir(parents=True)
        write_tasklist(self.steering, {"T-1": None, "T-2": None})

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_with(self, location: str, *, evidence: str | None = None, dest: str = "advisory:unverified_file",
                 category: str = "fail-open", extra: tuple[str, ...] = ("--base", "main")) -> tuple[int, list]:
        ev = evidence if evidence is not None else f"absent@{self.head}"
        body = section("IG1", "task", "T-1", [row("IG1-1", "high", category, dest, ev, location=location)],
                       sha=self.head)
        (self.steering / "review-findings.md").write_text("# Findings\n\n" + body, encoding="utf-8")
        return run_cli(self.steering, "--task", "T-1", *extra)

    def test_path_never_in_history_passes(self) -> None:
        for location in ("src/ghost.py:3", "`src/ghost.py:3-5`", "/elsewhere/checkout/src/ghost.py:3"):
            with self.subTest(location=location):
                code, rows = self.run_with(location)
                self.assertEqual(code, 0, rows)

    def test_paths_that_exist_or_existed_are_invalid(self) -> None:
        cases = {
            "src/kept.py:1": "present",  # tip にある
            "src/wip.py:1": "present",  # 未 commit の新しい file
            "src/gone.py:1": "removed",  # diff が消した（消した検査を根拠にした本物の high）
            "src/moved.py:1": "removed",  # 改名の元
            "mid.py:1": "removed",  # branch の途中で足して消した
            "lib/kept.py:9": "similar",  # 同じ basename の file が tip にある
            "/elsewhere/checkout/src/renamed.py:2": "similar",  # worktree の外の絶対パス
            "lib/設計.py:1": "similar",  # git が引用符つきで出す非 ASCII の basename
            "lib/\u304b\u3099.py:1": "similar",  # NFC の名前を NFD で書いた
            "lib/KEPT.py:1": "similar",  # 大文字小文字だけが違う
            "lib/staged.py:1": "similar",  # staged だけの新しい file と同じ basename
            "lib/mid.py:1": "similar",  # branch の途中で足して消した file（git log にだけ残る）と同じ basename
            "lib/\u3071.py:1": "similar",  # NFD で commit した名前を NFC で書いた
        }
        for location, kind in cases.items():
            with self.subTest(location=location):
                code, rows = self.run_with(location)
                self.assertEqual(code, 1, rows)
                self.assertTrue(any("IG1-1" in r[3] and kind in r[3] for r in rows), rows)

    def test_locations_outside_the_allowed_form_are_invalid(self) -> None:
        # path は許可リストの文字だけで読む。外れた形は never にせず分類できないにする
        for location in ("src/kept.py:12:5", "src\\kept.py:1", '"src/ghost.py":3', "src/gh$ost.py:3",
                         "src/ghost.py:3:", "src/ghost.py:0"):
            with self.subTest(location=location):
                code, rows = self.run_with(location)
                self.assertEqual(code, 1, rows)
                self.assertTrue(any("IG1-1" in r[3] and "分類できない" in r[3] for r in rows), rows)

    def test_unclassifiable_rows_are_invalid(self) -> None:
        cases = [
            ("-", {}),  # 欄が path でない
            ("src/ghost.py", {}),  # 行番号が無い
            ("src/a.py:1, src/b.py:2", {}),  # path が 2 つ
            ("src/ghost.py:3", {"evidence": "absent@deadbeefdeadbeef"}),  # sha が解けない
            ("src/ghost.py:3", {"extra": ()}),  # --base が無い
            ("src/ghost.py:3", {"extra": ("--base", "no-such-branch")}),  # base が解けない
        ]
        for location, kw in cases:
            with self.subTest(location=location, kw=kw):
                code, rows = self.run_with(location, **kw)
                self.assertEqual(code, 1, rows)
                self.assertTrue(any("IG1-1" in r[3] for r in rows), rows)

    def test_absent_does_not_open_other_destinations(self) -> None:
        # calibration は検証役の refuted だけ。absent@ は unverified_file だけに効く
        code, rows = self.run_with("src/ghost.py:3", dest="advisory:calibration", category="product")
        self.assertEqual(code, 1, rows)
        code, rows = self.run_with("src/ghost.py:3", dest="advisory")
        self.assertEqual(code, 1, rows)

    def test_older_sections_are_classified_at_their_own_sha(self) -> None:
        self.assertEqual(self.run_with("src/ghost.py:3")[0], 0)
        # 後の task が同じ path の file を作っても、前の Round の節はその節の sha の時点の事実で分類する
        (self.repo / "src" / "ghost.py").write_text("g = 1\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "later")
        new_head = _git(self.repo, "rev-parse", "HEAD")
        path = self.steering / "review-findings.md"
        path.write_text(path.read_text(encoding="utf-8") + section("IG2", "task", "T-2", [], sha=new_head),
                        encoding="utf-8")
        code, rows = run_cli(self.steering, "--task", "T-2", "--base", "main")
        self.assertEqual(code, 0, rows)
        # 前の Round の task には、HEAD の節が無い
        code, rows = run_cli(self.steering, "--task", "T-1", "--base", "main")
        self.assertEqual(code, 1, rows)

    def test_older_sections_whose_path_existed_are_invalid(self) -> None:
        # HEAD でない節でも、その sha の時点で path があった absent@ の行は通さない
        old = _git(self.repo, "rev-parse", "main")
        body = (section("IG1", "task", "T-1", [row("IG1-1", "high", "fail-open", "advisory:unverified_file",
                                                   f"absent@{old}", location="src/gone.py:1")], sha=old)
                + section("IG2", "task", "T-1", [], sha=self.head))
        (self.steering / "review-findings.md").write_text("# Findings\n\n" + body, encoding="utf-8")
        code, rows = run_cli(self.steering, "--task", "T-1", "--base", "main")
        self.assertEqual(code, 1, rows)
        self.assertTrue(any("IG1-1" in r[3] and "present" in r[3] for r in rows), rows)

    def test_sections_whose_sha_is_gone_are_invalid(self) -> None:
        # 前の節の sha が解けなければ、その節の absent@ の行は分類できないので通さない
        gone = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
        body = (section("IG1", "task", "T-1", [row("IG1-1", "high", "fail-open", "advisory:unverified_file",
                                                   f"absent@{gone}", location="src/ghost.py:3")], sha=gone)
                + section("IG2", "task", "T-1", [], sha=self.head))
        (self.steering / "review-findings.md").write_text("# Findings\n\n" + body, encoding="utf-8")
        code, rows = run_cli(self.steering, "--task", "T-1", "--base", "main")
        self.assertEqual(code, 1, rows)
        self.assertTrue(any("IG1-1" in r[3] and "分類できない" in r[3] for r in rows), rows)

    def test_absent_sha_must_be_the_section_sha(self) -> None:
        # absent@ の sha は節の sha（その Round の HEAD）と同じ。古い sha で分類させない
        code, rows = self.run_with("src/ghost.py:3", evidence="absent@" + _git(self.repo, "rev-parse", "main"))
        self.assertEqual(code, 1, rows)
        self.assertTrue(any("IG1-1" in r[3] and "節の sha" in r[3] for r in rows), rows)
        self.assertEqual(self.run_with("src/ghost.py:3", evidence=f"absent@{self.head[:9]}")[0], 0)  # 短い sha も可

    def test_predicate_accepts_only_the_absent_form(self) -> None:
        def errs(evidence: str, section_name: str = "IG1") -> list[str]:
            key, value = ("task", "T-1") if section_name.startswith("IG") else ("sha", "abc1234")
            r = row(f"{section_name}-1", "high", "fail-open", "advisory:unverified_file", evidence,
                    location="src/ghost.py:3")
            return fd.structure_errors("# F\n\n" + section(section_name, key, value, [r]))
        self.assertEqual(errs("absent@abc1234"), [])
        for bad in ("absent@", "absent@xyz1234", "absent@abc1234 extra", "absent"):
            with self.subTest(evidence=bad):
                self.assertNotEqual(errs(bad), [])
        self.assertNotEqual(errs("absent@abc1234", "IR1"), [])  # 独立レビューの high は advisory にできない


class CategoryVocabularyTest(unittest.TestCase):
    """述語が持つ category の集合と実害クラスが、reviewer-common.md § finding category の表と同じ。"""

    def test_categories_match_reviewer_common(self) -> None:
        text = REVIEWER_COMMON.read_text(encoding="utf-8")
        table = text.split("### finding category", 1)[1].split("導出述語", 1)[0]
        rows = re.findall(r"^\| `([a-z-]+)` \|.*\| (yes|no) \|$", table, re.M)
        self.assertEqual(len(rows), 9, rows)
        self.assertEqual(set(fd.CATEGORIES), {c for c, _ in rows})
        self.assertEqual(set(fd.BLOCKING_CATEGORIES), {c for c, b in rows if b == "yes"})


class LedgerTest(unittest.TestCase):
    """check-gate-ledger.sh の `findings` 行。`Independent Review` 行の件数と sha で突き合わせる。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.f = GateLedgerFixture(Path(self._tmp.name))
        self.f.review_findings = False  # 各テストが自分で書く

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def findings_row(self) -> tuple[int, tuple[str, str, str, str]]:
        self.f.write()
        code, rows = self.f.ledger()
        found = [r for r in rows if r[1] == "findings"]
        self.assertEqual(len(found), 1, rows)
        return code, found[0]

    def write_findings(self, body: str) -> None:
        (self.f.steering / "review-findings.md").write_text("# Findings\n\n" + body, encoding="utf-8")

    def test_matching_section_is_ok(self) -> None:
        self.write_findings(section("IR1", "sha", self.f.head, [], n=0))
        code, found = self.findings_row()
        self.assertEqual(found[0], "ok", found)
        self.assertEqual(code, 0)
        self.assertEqual(found[2], "independent-review")

    def test_missing_file_is_missing(self) -> None:
        code, found = self.findings_row()
        self.assertEqual(found[0], "missing", found)
        self.assertEqual(code, 1)

    def test_section_for_another_sha_is_missing(self) -> None:
        self.write_findings(section("IR1", "sha", self.f.old, [], n=0))
        code, found = self.findings_row()
        self.assertEqual(found[0], "missing", found)

    def test_counts_must_match_independent_review_line(self) -> None:
        rows = [
            row("IR1-1", "high", "product", "rejected:refuted", "b.py:2", verify="refuted"),  # 棄却しても数える
            row("IR1-2", "medium", "fail-open", "blocking"),
            row("IR1-3", "low", "style", "advisory"),
            row("IR1-4", "medium", "doc-claim", "advisory:out_of_scope"),  # 範囲外は数えない
            row("IR1-5", "medium", "fail-open", "rejected:duplicate:IR1-2"),  # 重複は数えない（参照先は採った行）
            row("IR1-6", "medium", "fail-open", "rejected:refuted", "b.py:4", verify="refuted"),  # medium・実害も数える
            row("IR1-7", "low", "style", "rejected:refuted", "b.py:5", verify="refuted"),
        ]
        self.write_findings(section("IR1", "sha", self.f.head, rows))
        self.f.state["Independent Review"] = _independent_review(self.f.head, high="1", blocking="2").replace(
            "medium: 0", "medium: 4")
        _, found = self.findings_row()
        self.assertEqual(found[0], "ok", found)
        for high, medium, blocking in (("0", "4", "2"), ("1", "5", "2"), ("1", "4", "1"), ("1", "3", "2"),
                                       ("1", "2", "1")):
            with self.subTest(high=high, medium=medium, blocking=blocking):
                self.f.state["Independent Review"] = _independent_review(
                    self.f.head, high=high, blocking=blocking).replace("medium: 0", f"medium: {medium}")
                code, found = self.findings_row()
                self.assertEqual(found[0], "invalid", found)
                self.assertEqual(code, 1)

    def test_same_sha_twice_uses_the_last_section(self) -> None:
        # 同じ tip を 2 回レビューしたら、Independent Review 行は後の巡で上書きされる
        empty = section("IR1", "sha", self.f.head, [], n=0)
        high = section("IR2", "sha", self.f.head, [row("IR2-1", "high", "product", "blocking")])
        self.write_findings(high.replace("IR2", "IR1") + empty.replace("IR1", "IR2"))  # 後の節で high 0
        self.f.state["Independent Review"] = _independent_review(self.f.head, high="0")
        _, found = self.findings_row()
        self.assertEqual(found[0], "invalid", found)  # 同じ tip なので前の high は直っていない
        carried = section("IR2", "sha", self.f.head, [row("IR2-m1", "high", "product", "re-reported:IR1-1")], n=0)
        self.write_findings(high.replace("IR2", "IR1") + carried)
        self.f.state["Independent Review"] = _independent_review(self.f.head, high="1")
        _, found = self.findings_row()
        self.assertEqual(found[0], "ok", found)
        self.write_findings(empty + high)  # 前の節に high が無ければ、後の節と行だけを突き合わせる
        _, found = self.findings_row()
        self.assertEqual(found[0], "ok", found)
        self.f.state["Independent Review"] = _independent_review(self.f.head, high="0")
        code, found = self.findings_row()
        self.assertEqual(found[0], "invalid", found)
        self.assertEqual(code, 1)

    def test_carry_over_covers_every_serious_row_of_the_earlier_section(self) -> None:
        empty = section("IR2", "sha", self.f.head, [], n=0)
        cases = [
            # (前の節の行, 最後の節, Independent Review の high・blocking, 期待)
            ([row("IR1-1", "medium", "fail-open", "blocking")], empty, ("0", "0"), "invalid"),  # 実害クラス
            ([row("IR1-1", "high", "product", "rejected:refuted", "b.py:2", verify="refuted")], empty,
             ("0", "0"), "invalid"),  # 捨てた high も同じ tip では引き継ぐ
            ([row("IR1-1", "high", "product", "blocking"), row("IR1-2", "high", "product", "rejected:duplicate:IR1-1")],
             section("IR2", "sha", self.f.head, [row("IR2-m1", "high", "product", "re-reported:IR1-1")], n=0),
             ("1", "0"), "ok"),  # duplicate の行は引き継がなくてよい
            ([row("IR1-1", "low", "style", "advisory")], empty, ("0", "0"), "ok"),  # 重くない行は要らない
        ]
        for earlier, last, (high, blocking), expected in cases:
            with self.subTest(earlier=earlier):
                self.write_findings(section("IR1", "sha", self.f.head, earlier) + last)
                self.f.state["Independent Review"] = _independent_review(self.f.head, high=high, blocking=blocking)
                _, found = self.findings_row()
                self.assertEqual(found[0], expected, found)

    def test_unreadable_file_is_invalid_not_ok(self) -> None:
        path = self.f.steering / "review-findings.md"
        makers = {
            "directory": lambda: path.mkdir(),
            "not-utf8": lambda: path.write_bytes(b"# Findings\n\n\xff\xfe\n"),
            "dangling-symlink": lambda: path.symlink_to(self.f.steering / "no-such-file.md"),
        }
        for name, make in makers.items():
            with self.subTest(form=name):
                self.f.write()
                make()
                code, rows = self.f.ledger()
                found = [r for r in rows if r[1] == "findings"]
                self.assertEqual(len(found), 1, rows)
                self.assertEqual(found[0][0], "invalid", found)
                self.assertEqual(code, 1)
                if path.is_dir() and not path.is_symlink():
                    path.rmdir()
                else:
                    path.unlink()

    def test_absent_rows_in_ig_sections_pass_the_ledger(self) -> None:
        # ledger は git を呼ばず、absent@ の形だけを見る（判定は impl-gating の CLI が行った）
        ig = section("IG1", "task", "T-1", [row("IG1-1", "high", "fail-open", "advisory:unverified_file",
                                                 "absent@abc1234", location="src/ghost.py:3")])
        self.write_findings(ig + section("IR1", "sha", self.f.head, [], n=0))
        _, found = self.findings_row()
        self.assertEqual(found[0], "ok", found)

    def test_short_and_long_sha_match(self) -> None:
        for section_sha, line_sha in ((self.f.head[:7], self.f.head), (self.f.head, self.f.head[:7])):
            with self.subTest(section=section_sha, line=line_sha):
                self.write_findings(section("IR1", "sha", section_sha, [], n=0))
                self.f.state["Independent Review"] = _independent_review(line_sha)
                _, found = self.findings_row()
                self.assertEqual(found[0], "ok", found)

    def test_carry_over_reaches_every_earlier_section_of_the_same_sha(self) -> None:
        h = self.f.head
        ir1 = section("IR1", "sha", h[:7], [row("IR1-1", "high", "product", "blocking")])
        cases = [
            # 真ん中の節が引き継ぎ、最後の節が落とした（短い sha の節も同じ tip）
            (ir1 + section("IR2", "sha", h, [row("IR2-m1", "high", "product", "re-reported:IR1-1")], n=0)
             + section("IR3", "sha", h, [], n=0), ("0", "0"), "invalid"),
            # 真ん中の節で新しく出た high を、最後の節が落とした
            (ir1 + section("IR2", "sha", h, [row("IR2-1", "high", "product", "blocking"),
                                             row("IR2-m1", "high", "product", "re-reported:IR1-1")])
             + section("IR3", "sha", h, [row("IR3-m1", "high", "product", "re-reported:IR2-m1")], n=0),
             ("1", "0"), "invalid"),
            # 元の id を辿って引き継げば ok
            (ir1 + section("IR2", "sha", h, [row("IR2-m1", "high", "product", "re-reported:IR1-1")], n=0)
             + section("IR3", "sha", h, [row("IR3-m1", "high", "product", "re-reported:IR2-m1")], n=0),
             ("1", "0"), "ok"),
        ]
        for body, (high, blocking), expected in cases:
            with self.subTest(body=body[-60:]):
                self.write_findings(body)
                self.f.state["Independent Review"] = _independent_review(h, high=high, blocking=blocking)
                _, found = self.findings_row()
                self.assertEqual(found[0], expected, found)

    def test_absent_rows_with_a_bad_location_fail_the_ledger(self) -> None:
        ig = section("IG1", "task", "T-1", [row("IG1-1", "high", "fail-open", "advisory:unverified_file",
                                                 f"absent@{IG_SHA}", location="src/ghost.py:3:1")])
        self.write_findings(ig + section("IR1", "sha", self.f.head, [], n=0))
        _, found = self.findings_row()
        self.assertEqual(found[0], "invalid", found)

    def test_broken_file_is_invalid_even_if_counts_match(self) -> None:
        self.write_findings(section("IR1", "sha", self.f.head, [], n=0) + "自由文\n")
        _, found = self.findings_row()
        self.assertEqual(found[0], "invalid", found)

    def test_not_required_when_independent_review_is_not(self) -> None:
        self.f.state["Task Size"] = "trivial"
        _, found = self.findings_row()
        self.assertEqual(found[0], "n/a", found)


if __name__ == "__main__":
    unittest.main()
