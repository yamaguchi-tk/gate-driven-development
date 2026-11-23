"""human check の判断ポイントの `依頼との差:` が `なし` でないか欠けているとき、承認の記録を止める。

判定は `hooks/scripts/lib/request_diff_approval.py` で、steering の Write・Edit の検査（`validate-steering-write.py`）
から呼ぶ。直前の提示は transcript の最後の、HITL のマーカーを含む assistant の発言とする。前の提示とは比べない。
Bash で承認を書くコマンド（`run-request-diff-approval-gate-hook.sh`）は、提示を読まずに Write・Edit へ付け替える。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from lib import request_diff_field as gate  # noqa: E402
from lib.hitl_lint_gate import HITL_MARKER  # noqa: E402

STEERING_WRITE = SCRIPTS / "validate-steering-write.py"
BASH_HOOK = SCRIPTS / "run-request-diff-approval-gate-hook.sh"

def state_text(status: str = "pending") -> str:
    lines = ["Started At: 2026-11-10T00:00:00Z", "- Resume From: gdd-requirements-gating",
             f"- Human Check Status: {status}"]
    return "\n".join(lines + ["- Route In Progress: none", ""])


PENDING_STATE = state_text()
APPROVED_STATE = PENDING_STATE.replace("pending", "approved | evidence: human:承認まで")


def tag(*values: str) -> str:
    return f'<gdd-hitl-fields options="none" request-diff="{",".join(values)}">'


def presentation(*fields: str, tag_values: tuple[str, ...] | None = None) -> str:
    """判断ポイントごとに欄を 1 行置き、マーカーの直前にタグを置く。タグの値は既定で欄から作る。"""
    lines = ["## 判断ポイント"]
    for i, value in enumerate(fields, 1):
        lines += [f"### ポイント {i}", "- 推奨: A", f"- 依頼との差: {value}", "- 無回答時のデフォルト: A"]
    if tag_values is None:
        tag_values = tuple("none" if v == "なし" else "differs" for v in fields)
    lines += ["", tag(*tag_values), HITL_MARKER]
    return "\n".join(lines)


_UUIDS = iter(range(1, 10**6))


def assistant(text: str, uuid: str | None = None) -> dict:
    record = {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}
    record["uuid"] = uuid or f"u{next(_UUIDS)}"
    return record


HUMAN = {"type": "user", "message": {"content": [{"type": "text", "text": "OK"}]}}


class FieldTest(unittest.TestCase):
    """欄は `<記号> 依頼との差: <値>` の 1 つの形だけ。ラベルを含む行は全部を見て、値はちょうど `なし` だけを通す。"""

    def test_all_none_with_matching_tag_passes(self) -> None:
        self.assertIsNone(gate.field_problem(presentation("なし", "なし")))

    def test_accepted_line_forms_are_read(self) -> None:
        for line in ("- 依頼との差: なし", "1. 依頼との差: なし", "* 依頼との差: なし", "依頼との差: なし",
                     "> - 依頼との差: なし", "   - __依頼との差__：なし", "- **依頼との差**: なし",
                     "- **依頼との差:** なし", "- 依頼との差: **なし**", "- 依頼との差: `なし`", "- 依頼との差　：　なし",
                     "- `依頼との差`: なし"):
            with self.subTest(line=line):
                text = f"{line}\n{tag('none')}\n{HITL_MARKER}"
                self.assertEqual(gate.field_values(text), ["なし"])
                self.assertIsNone(gate.field_problem(text))

    def test_declared_difference_is_a_problem_for_approval_but_readable(self) -> None:
        for value in ("あり: 全レーンに入れる", "あり：全レーンに入れる", "**あり**: 全レーン", "あり : 全レーン"):
            with self.subTest(value=value):
                text = presentation(value, tag_values=("differs",))
                self.assertEqual(gate.field_problem(text), "なし以外の点がある")
                self.assertIsNone(gate.format_problem(text))
                text = presentation(value, tag_values=("none",))
                self.assertEqual(gate.field_problem(text), "なし以外の点がある")

    def test_values_outside_the_two_forms_are_unreadable(self) -> None:
        """値は `なし` ちょうどか `あり: <項目>` の 2 形だけ。ほかは意味を読まずに読めない形にする。"""
        for value in ("全レーンに入れる", "なし（ユーザー「PR を分ける」）", "なし（狭めるが影響は小さい）",
                      "なし | <満たさない依頼の原文の項目>", "なし | 剥奪されたあと投稿する", "なしで進める", "なし。",
                      "ありません。", "案 1 ならありません。", "案 1′ はなし。", "読み替えあり。", "あり（前回は誤り）",
                      "あり:", "あり: ", "あります。 範囲を外す", ""):
            with self.subTest(value=value):
                text = presentation(value, tag_values=("none",))
                self.assertEqual(gate.field_problem(text), "欄の形が読めない")
                self.assertEqual(gate.format_problem(text), "欄の形が読めない")
                self.assertEqual(len(gate.unreadable_lines(text)), 1)

    def test_format_problem_matches_field_problem_except_for_points_that_differ(self) -> None:
        cases = (presentation("なし"), presentation("なし", "なし"), "- 推奨: A\n" + HITL_MARKER,
                 presentation("なし") + "\n### 依頼との差", presentation("なし").replace('request-diff="none"', 'request-diff="x"'))
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(gate.format_problem(text), gate.field_problem(text))
        self.assertIsNone(gate.format_problem(presentation("なし", tag_values=("differs",))))

    def test_every_line_with_the_label_must_be_the_one_form(self) -> None:
        for line in ("| 依頼との差 | なし |", "- 依頼との差（点 2）: 全レーン", "### 依頼との差",
                     "1. 案 — 変更後: A / 依頼との差: 全レーンに入れる", "1. 依頼との差の扱いについて",
                     "- **「OK」** → `依頼との差: なし` の点を承認します", "依頼との差 → 全レーン"):
            with self.subTest(line=line):
                text = line + "\n" + presentation("なし")
                self.assertEqual(gate.field_problem(text), "欄の形が読めない")
                self.assertIn(line.strip(), gate.unreadable_lines(text))

    def test_fenced_lines_are_read_too(self) -> None:
        text = "```\n| 依頼との差 | x |\n```\n" + presentation("なし")
        self.assertEqual(gate.field_problem(text), "欄の形が読めない")

    def test_body_field_is_not_required_when_the_tag_says_none(self) -> None:
        """通すかどうかはタグで決める。本文の欄は止める向きにだけ使い、欠けていても止めない。"""
        self.assertIsNone(gate.field_problem(f"- 推奨: A\n{tag('none')}\n{HITL_MARKER}"))

    def test_templates_as_written_pass(self) -> None:
        """テンプレートの判断ポイントの節とタグを、placeholder を埋めて通す（テンプレートを変えたときの退行を捕まえる）。"""
        compact = (PLUGIN_ROOT / "references" / "human-check-template-compact.md").read_text(encoding="utf-8")
        block = compact[compact.index("### 判断ポイント"):compact.index("### どこまで自走するか")]
        compact_tag = compact[compact.index("<gdd-hitl-fields"):compact.index(HITL_MARKER) + len(HITL_MARKER)]
        full = (PLUGIN_ROOT / "references" / "human-check-template.md").read_text(encoding="utf-8")
        start = full.index("### 承認ポイント\n")
        full_block = full[start:full.index("**N. 方向性**", start)]
        full_tag_at = full.index("<gdd-hitl-fields options=")
        full_tag = full[full_tag_at:full.index(">`", full_tag_at) + 1] + "\n" + HITL_MARKER
        for name, text, tag_text in (("compact", block, compact_tag), ("full", full_block, full_tag)):
            with self.subTest(template=name):
                filled = text.replace("<N>", "1").replace("なし | <", "なし <!-- ")
                filled = "\n".join(l.split(" <!-- ")[0] for l in filled.splitlines())
                count = len(gate.field_values(filled))
                filled_tag = re.sub(r'request-diff="[^"]*"', 'request-diff="' + ",".join(["none"] * count) + '"',
                                    re.sub(r'="none\|filled"', '="none"', tag_text))
                self.assertIn("request-diff=", tag_text)
                self.assertIsNone(gate.field_problem(filled + "\n" + filled_tag), gate.unreadable_lines(filled))


class RequestDiffTagTest(unittest.TestCase):
    """通すかどうかと件数は、各マーカーの直前のタグの `request-diff`（判断ポイントの順に `none`/`differs` をカンマで）
    だけで決める。本文の欄は止める向きにだけ使う（読めない行・なし 以外）。本文の欄の数は数えない。"""

    QUOTE = "**依頼**: 確認の承認ポイント数: 2 件までにしてほしい"

    def test_missing_tag_stops(self) -> None:
        text = presentation("なし").replace(tag("none") + "\n", "")
        self.assertEqual(gate.field_problem(text), "タグが無い")

    def test_tag_not_adjacent_to_the_marker_stops(self) -> None:
        text = presentation("なし").replace(HITL_MARKER, "本文の続き\n" + HITL_MARKER)
        self.assertEqual(gate.field_problem(text), "タグが無い")

    def test_tag_without_the_attribute_stops(self) -> None:
        text = presentation("なし").replace(' request-diff="none"', "")
        self.assertEqual(gate.field_problem(text), "タグの値が読めない")

    def test_unreadable_tag_values_stop(self) -> None:
        for value in ("", "None", "none,", ",none", "none, none", "none;none", "なし", "none|differs",
                      "<判断ポイントの順に none|differs をカンマで>", "none," * 5000):
            with self.subTest(value=value[:40]):
                text = presentation("なし").replace('request-diff="none"', f'request-diff="{value}"')
                self.assertEqual(gate.field_problem(text), "タグの値が読めない")

    def test_duplicated_attribute_stops(self) -> None:
        text = presentation("なし").replace('request-diff="none"', 'request-diff="differs" request-diff="none"')
        self.assertEqual(gate.field_problem(text), "タグの値が読めない")

    def test_differs_in_the_tag_stops_even_if_the_body_says_none(self) -> None:
        text = presentation("なし", "なし", tag_values=("none", "differs"))
        self.assertEqual(gate.field_problem(text), "なし以外の点がある")

    def test_body_field_count_is_not_compared(self) -> None:
        """引用・例示にある欄の形の行が、欠けた本物の欄の代わりに数えられることが無いよう、本文の欄は数えない。"""
        self.assertIsNone(gate.field_problem(presentation("なし", tag_values=("none", "none"))))
        quote = "**依頼**: 次のとおり\n> - 依頼との差: なし\n"
        self.assertIsNone(gate.field_problem(quote + presentation("なし", tag_values=("none", "none"))))
        self.assertEqual(gate.field_problem(quote + presentation("なし", tag_values=("none", "differs"))),
                         "なし以外の点がある")

    def test_count_words_in_the_body_are_not_read(self) -> None:
        """引用や書き換えた語（`承認ポイント数 3`・`判断ポイント数: 3`）は読まない。決めるのはタグの値だけ。"""
        for line in (self.QUOTE, "承認ポイント数 3", "判断ポイント数: 3", "承認ポイント数: 2（方向性を含む）", "承認ポイント数:"):
            with self.subTest(line=line):
                self.assertIsNone(gate.field_problem(line + "\n" + presentation("なし")))
                self.assertEqual(gate.field_problem(line + "\n" + presentation("なし", tag_values=("none", "differs"))),
                                 "なし以外の点がある")

    def test_every_marker_needs_its_own_tag(self) -> None:
        text = presentation("なし") + "\n追記\n" + HITL_MARKER
        self.assertEqual(gate.field_problem(text), "タグが無い")
        text = presentation("なし") + "\n" + tag("differs") + "\n" + HITL_MARKER
        self.assertEqual(gate.field_problem(text), "なし以外の点がある")
        text = presentation("なし") + "\n" + tag("none") + "\n" + HITL_MARKER
        self.assertIsNone(gate.field_problem(text))

    def test_text_without_marker_reads_the_tag_at_the_end(self) -> None:
        self.assertIsNone(gate.field_problem(f"- 依頼との差: なし\n{tag('none')}"))
        self.assertEqual(gate.field_problem("- 依頼との差: なし\n本文"), "タグが無い")

    def test_odd_tag_input_does_not_raise_and_stops(self) -> None:
        """タグの読み取りまで届く入力（欄は読める）で、例外を出さずに止める理由を返す。"""
        field = "- 依頼との差: なし\n"
        cases = {
            "<gdd-hitl-fields>\n" + HITL_MARKER: "タグの値が読めない",
            '<gdd-hitl-fields request-diff=">\n' + HITL_MARKER: "タグが無い",
            '<gdd-hitl-fields request-diff="\x00">\n' + HITL_MARKER: "タグの値が読めない",
            '<gdd-hitl-fields request-diff="none" request-diff="none">\n' + HITL_MARKER: "タグの値が読めない",
            "\x00\n" + HITL_MARKER: "タグが無い",
            '<gdd-hitl-fields ' + 'x="y" ' * 20000 + 'request-diff="none,">\n' + HITL_MARKER: "タグの値が読めない",
            HITL_MARKER * 3: "タグが無い",
        }
        for text, problem in cases.items():
            with self.subTest(text=text[:40]):
                self.assertEqual(gate.field_problem(field + text), problem)

    def test_reading_the_fields_takes_linear_time(self) -> None:
        """欄の読み取りは提示の長さに比例する時間で終わる（空白の長い行で二乗の時間がかかると、hook の上限
        10 秒を超えて guard 全体が走らずに書き込みが通る）。長い行も、形が合えば欄として読む。"""
        worst = ("- 依頼との差: あり: a" + " " * 100000 + "x", " " * 100000 + "x依頼との差", "> " + " " * 100000 + "x依頼との差",
                 "- 依頼との差: なし" + " " * 100000, "1." + " " * 100000 + "依頼との差",
                 ">" * 300000 + "依頼との差: なし", "> " * 150000 + "依頼との差: なし")
        many = "\n".join(["- 依頼との差: あり: a" + " " * 985 + "x"] * 3000)
        for text in worst + (many,):
            with self.subTest(text=text[:12]):
                started = time.monotonic()
                gate.field_problem(text + "\n" + tag("none") + "\n" + HITL_MARKER)
                self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual(gate.field_problem(worst[0] + "\n" + tag("none") + "\n" + HITL_MARKER), "なし以外の点がある")
        self.assertIsNone(gate.field_problem(worst[3] + "\n" + tag("none") + "\n" + HITL_MARKER))
        self.assertEqual(gate.field_problem(worst[1] + "\n" + tag("none") + "\n" + HITL_MARKER), "欄の形が読めない")

    def test_unreadable_or_empty_body_does_not_raise(self) -> None:
        self.assertIsNone(gate.field_problem(""  + tag("none")))
        self.assertEqual(gate.field_problem("依頼との差" * 10000), "欄の形が読めない")


class _Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state_dir = self.tmp / "hook-state"
        self.transcript = self.tmp / "transcript.jsonl"
        self.repo = self.tmp / "repo"
        self.state = self.repo / ".steering" / "20261110-x" / "state.md"
        self.state.parent.mkdir(parents=True)
        self.state.write_text(PENDING_STATE, encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def transcript_with(self, *records: dict) -> None:
        self.transcript.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8")

    def env(self) -> dict:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = str(self.state_dir)
        return env


class SteeringWriteEntryTest(_Fixture):
    """Write・Edit の入口（validate-steering-write.py の main）。"""

    def run_edit(self, old: str = "Human Check Status: pending",
                 new: str = "Human Check Status: approved | evidence: human:承認まで",
                 path: Path | None = None, session: str = "s1") -> subprocess.CompletedProcess:
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(path or self.state), "old_string": old, "new_string": new},
            "transcript_path": str(self.transcript),
            "cwd": str(self.repo),
            "session_id": session,
        }
        return subprocess.run(
            [sys.executable, str(STEERING_WRITE)], input=json.dumps(payload),
            env=self.env(), capture_output=True, text=True,
        )

    def message(self, result: subprocess.CompletedProcess) -> str:
        return json.loads(result.stderr)["systemMessage"]

    def test_approval_after_differing_point_is_denied(self) -> None:
        self.transcript_with(assistant(presentation("あり: 全レーンに入れる")), HUMAN)
        result = self.run_edit()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("gdd-requirements-amendment", self.message(result))

    def test_value_only_edit_to_approved_is_judged(self) -> None:
        self.transcript_with(assistant(presentation("あり: 全レーンに入れる")), HUMAN)
        self.assertEqual(self.run_edit(old="pending", new="approved | evidence: human:承認まで").returncode, 2)

    def test_approval_after_all_none_is_allowed(self) -> None:
        self.transcript_with(assistant(presentation("なし")), HUMAN)
        result = self.run_edit()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_allow_is_recorded_with_the_presentation(self) -> None:
        record = assistant(presentation("なし"), uuid="p1")
        self.transcript_with(record, HUMAN)
        self.assertEqual(self.run_edit().returncode, 0)
        line = json.loads((self.state_dir / "request-diff-approval.log").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((line["entry"], line["uuid"], line["session_id"]), ("allow", "p1", "s1"))
        self.assertEqual(line["steering"], os.path.realpath(self.state))
        self.assertEqual(len(line["sha"]), 64)

    def test_re_presentation_with_fewer_points_is_not_compared(self) -> None:
        self.transcript_with(assistant(presentation("なし", "あり: 全レーンに入れる")), HUMAN,
                             assistant(presentation("なし")), HUMAN)
        self.assertEqual(self.run_edit().returncode, 0)

    def test_allow_is_not_recorded_when_another_check_denies(self) -> None:
        self.transcript_with(assistant(presentation("なし")), HUMAN)
        result = self.run_edit(new="Human Check Status: approved | evidence: human:承認まで\n- Note: 以下省略...")
        self.assertEqual(result.returncode, 2, result.stderr)
        log = self.state_dir / "request-diff-approval.log"
        entries = [json.loads(l)["entry"] for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        self.assertNotIn("allow", entries)

    def test_quoted_count_in_preamble_does_not_change_the_judgement(self) -> None:
        text = RequestDiffTagTest.QUOTE + "\n" + presentation("なし", "なし")
        self.transcript_with(assistant(text), HUMAN)
        self.assertEqual(self.run_edit().returncode, 0)

    def test_approval_without_the_tag_is_denied_with_the_tag_form(self) -> None:
        self.transcript_with(assistant(presentation("なし").replace(tag("none") + "\n", "")), HUMAN)
        result = self.run_edit()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("タグが無い", self.message(result))
        self.assertIn('request-diff="', self.message(result))

    def test_approval_without_marker_presentation_is_allowed(self) -> None:
        self.transcript_with(assistant("方針を確かめます"), HUMAN)
        self.assertEqual(self.run_edit().returncode, 0)

    def test_latest_marker_presentation_is_judged(self) -> None:
        self.transcript_with(
            assistant(presentation("あり: 全レーンに入れる")), HUMAN,
            assistant(presentation("なし")), HUMAN, assistant("記録します"),
        )
        self.assertEqual(self.run_edit().returncode, 0)

    def test_unrelated_edit_to_already_approved_state_is_allowed(self) -> None:
        self.state.write_text(APPROVED_STATE, encoding="utf-8")
        self.transcript_with(assistant(presentation("あり: 全レーンに入れる")), HUMAN)
        result = self.run_edit(old="Route In Progress: none", new="Route In Progress: gdd-design-gating")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unreadable_transcript_denies(self) -> None:
        self.transcript.mkdir()
        self.assertEqual(self.run_edit().returncode, 2)

    def test_deny_names_the_reason_and_the_unreadable_line(self) -> None:
        self.transcript_with(assistant(presentation("なし") + "\n| 依頼との差 | 全部 |"), HUMAN)
        result = self.run_edit()
        self.assertEqual(result.returncode, 2)
        self.assertIn("欄の形が読めない", self.message(result))
        self.assertIn("| 依頼との差 | 全部 |", self.message(result))

    def test_each_deny_is_recorded_for_the_readout(self) -> None:
        self.transcript_with(assistant(presentation("あり: 全レーンに入れる")), HUMAN)
        self.run_edit()
        log = self.state_dir / "request-diff-approval.log"
        record = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(record["entry"], "steering-write")
        self.assertEqual(record["problem"], "なし以外の点がある")

    def test_edit_whose_old_string_misses_the_file_is_judged_as_approval(self) -> None:
        self.transcript_with(assistant(presentation("あり: 全レーンに入れる")), HUMAN)
        result = self.run_edit(old="- Human Check Status: pending ", new="- Human Check Status: approved")
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_decoy_line_before_the_real_approval_is_judged_by_the_gate_reader(self) -> None:
        self.transcript_with(assistant(presentation("あり: 全レーンに入れる")), HUMAN)
        content = PENDING_STATE.replace(
            "- Human Check Status: pending\n",
            "Human Check Status : pending\n- Human Check Status: approved\n",
        )
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(self.state), "content": content},
            "transcript_path": str(self.transcript),
            "cwd": str(self.repo),
        }
        result = subprocess.run([sys.executable, str(STEERING_WRITE)], input=json.dumps(payload),
                                env=self.env(), capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_malformed_transcript_records_do_not_fail_the_guard(self) -> None:
        self.transcript.write_text(
            "\n".join([
                "not json", json.dumps([1, 2]), json.dumps({"type": "assistant", "message": "x"}),
                json.dumps({"type": "attachment", "attachment": "text"}),
                json.dumps(assistant(presentation("なし")), ensure_ascii=False),
            ]),
            encoding="utf-8",
        )
        result = self.run_edit()
        self.assertEqual(result.returncode, 0, result.stderr)


def reply(text: str = "OK") -> dict:
    """人の発言（origin が human の user の行）。"""
    return {"type": "user", "origin": {"kind": "human"}, "message": {"content": [{"type": "text", "text": text}]}}


def correction(*values: str, decided: str | None = None, extra: str = "") -> dict:
    """人の返事の後に main が書く補正（欄とタグだけを直した版。問いではないのでマーカーを付けない）。"""
    attrs = f' decided="{decided}"' if decided is not None else ""
    return assistant(f"上の確認の欄とタグだけを直します。{extra}\n\n"
                     f'<gdd-hitl-fields correction request-diff="{",".join(values)}"{attrs}>')


class CorrectionTest(_Fixture):
    """欄かタグに問題のある確認に人が答えた後は、確認を出し直させず、補正を根拠に承認を通す
    （Stop の hook が動かなかった・記録を書けなかった・上限を使い切ったときに、人に答え直させない）。
    hook は狭める点かを分類しない。補正には常に、提示の後の人の返事の引用（`decided`）を求める。"""

    NO_TAG = presentation("なし").replace(tag("none") + "\n", "")
    run_edit = SteeringWriteEntryTest.run_edit
    message = SteeringWriteEntryTest.message

    def entries(self) -> list[dict]:
        log = self.state_dir / "request-diff-approval.log"
        return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []

    def test_problems_are_settled_by_a_correction_quoting_the_reply(self) -> None:
        for name, text in (
            ("タグが無い", self.NO_TAG),
            ("タグの値が読めない", presentation("なし", tag_values=("ok",))),
            ("欄に句点", presentation("なし").replace("依頼との差: なし", "依頼との差: なし。")),
            ("あり", presentation("あり: 全レーンに入れる")),
            ("読めないタグの differs", presentation("なし", tag_values=("none, differs",))),
            ("大文字の Differs", presentation("なし", tag_values=("Differs",))),
            ("タグだけ differs", presentation("なし", tag_values=("differs",))),
        ):
            with self.subTest(name=name):
                self.transcript_with(assistant(text), reply("この案で進めて"), correction("none", decided="この案で進めて"))
                result = self.run_edit()
                self.assertEqual(result.returncode, 0, result.stderr)
                last = self.entries()[-1]
                self.assertEqual((last["entry"], last["decided_chars"]), ("allow-corrected", len("この案で進めて")))
                self.assertNotIn("この案で進めて", json.dumps(last, ensure_ascii=False), "人の発言は記録に残さない")

    def test_a_correction_without_a_quote_is_denied_even_for_form_only_problems(self) -> None:
        for name, text in (
            ("タグが無い", self.NO_TAG),
            ("読めないタグの differs", presentation("なし", tag_values=("none, differs",))),
            ("属性が 2 つ", presentation("なし").replace(tag("none"), tag("none")[:-1] + ' request-diff="differs">')),
            ("あり", presentation("あり: 全レーンに入れる")),
        ):
            with self.subTest(name=name):
                self.transcript_with(assistant(text), reply(), correction("none"))
                self.assertEqual(self.run_edit().returncode, 2)

    def test_without_a_correction_the_deny_explains_how_to_write_one(self) -> None:
        self.transcript_with(assistant(self.NO_TAG), reply())
        result = self.run_edit()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("correction", self.message(result))
        self.assertIn("decided", self.message(result))

    def test_a_correction_needs_a_human_reply_before_it(self) -> None:
        for records in (
            (assistant(self.NO_TAG), correction("none", decided="OK")),
            (assistant(self.NO_TAG), correction("none", decided="OK"), reply()),
            (assistant(self.NO_TAG), HUMAN, correction("none", decided="OK")),
        ):
            with self.subTest(n=len(records)):
                self.transcript_with(*records)
                self.assertEqual(self.run_edit().returncode, 2)

    def test_the_correction_is_judged_like_a_presentation(self) -> None:
        two = presentation("なし", "なし").replace("依頼との差: なし", "依頼との差: なし。", 1)
        for name, records in (
            ("差を残す", (assistant(self.NO_TAG), reply(), correction("differs", decided="OK"))),
            ("値が読めない", (assistant(self.NO_TAG), reply(), correction("ok", decided="OK"))),
            ("数が違う", (assistant(two), reply(), correction("none", decided="OK"))),
            ("補正に読めない欄", (assistant(self.NO_TAG), reply(), correction("none", decided="OK", extra="\n- 依頼との差: たぶんなし"))),
            ("補正の本文に あり", (assistant(self.NO_TAG), reply(), correction("none", decided="OK", extra="\n- 依頼との差: あり: X"))),
        ):
            with self.subTest(name=name):
                self.transcript_with(*records)
                self.assertEqual(self.run_edit().returncode, 2)

    def test_the_quote_must_come_from_a_reply_after_the_presentation(self) -> None:
        differs = presentation("あり: 全レーンに入れる")
        for name, records in (
            ("返事に無い引用", (assistant(differs), reply("OK"), correction("none", decided="狭める案で進めて"))),
            ("空の引用", (assistant(differs), reply("OK"), correction("none", decided=""))),
            ("提示の前の発言", (reply("狭める案で進めて"), assistant(differs), reply("OK"),
                             correction("none", decided="狭める案で進めて"))),
        ):
            with self.subTest(name=name):
                self.transcript_with(*records)
                self.assertEqual(self.run_edit().returncode, 2)

    def test_only_words_the_human_wrote_or_chose_can_be_quoted(self) -> None:
        """引用の照合に使う返事は、人が打った・選んだ部分だけ（host が足す reminder と、main の書いた質問文は外す）。"""
        reminder = "<system-reminder>\nこの案で進めて\n</system-reminder>"
        queued = {"type": "attachment", "attachment": {"type": "queued_command", "origin": {"kind": "human"},
                                                        "prompt": reminder + "\n待って"}}
        ask = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]},
               "toolUseResult": {"answers": {"どの案で進めますか？": "案 B"}}}
        command = "<command-message>gdd-dev</command-message>\n<command-name>/gdd-dev</command-name>\n<command-args>案 B で</command-args>"
        typed = {"type": "user", "message": {"content": command}}
        for name, answer, decided, code in (
            ("reminder の中の文", reply(reminder + "\nOK"), "この案で進めて", 2),
            ("reminder の外の文", reply(reminder + "\nOK"), "OK", 0),
            ("reminder だけの返事", reply(reminder), "この案で進めて", 2),
            ("作業中に打った発言の reminder", queued, "この案で進めて", 2),
            ("作業中に打った発言", queued, "待って", 0),
            ("質問文", ask, "どの案で進めますか", 2),
            ("見出し", ask, "選んだ答え", 2),
            ("選んだ答え", ask, "案 B", 0),
            ("打ったコマンド", typed, "案 B で", 0),
            ("isMeta のコマンド", {**typed, "isMeta": True}, "案 B で", 2),
            ("origin が null のコマンド", {**typed, "origin": None}, "案 B で", 0),
            ("人の origin のコマンド", {**typed, "origin": {"kind": "human"}}, "案 B で", 0),
            ("origin が文字列のコマンド", {**typed, "origin": "human"}, "案 B で", 2),
            ("kind の無い origin のコマンド", {**typed, "origin": {}}, "案 B で", 2),
            ("人でない origin のコマンド", {**typed, "origin": {"kind": "task-notification"}}, "案 B で", 2),
            ("origin が null の選んだ答え", {**ask, "origin": None}, "案 B", 0),
            ("人の origin の選んだ答え", {**ask, "origin": {"kind": "human"}}, "案 B", 0),
            ("origin が文字列の選んだ答え", {**ask, "origin": "human"}, "案 B", 2),
            ("kind の無い origin の選んだ答え", {**ask, "origin": {}}, "案 B", 2),
            ("人でない origin の選んだ答え", {**ask, "origin": {"kind": "task-notification"}}, "案 B", 2),
        ):
            with self.subTest(name=name):
                self.transcript_with(assistant(self.NO_TAG), answer, correction("none", decided=decided))
                self.assertEqual(self.run_edit().returncode, code)

    def test_malformed_rows_after_the_presentation_do_not_fail_the_guard(self) -> None:
        odd = [{"type": "attachment", "attachment": "text"}, {"type": "user", "origin": "human", "message": "x"},
               {"type": "user", "origin": {"kind": "human"}, "message": {"content": [{"type": "text", "text": 3}]}}]
        self.transcript_with(assistant(self.NO_TAG), *odd, reply("OK"), correction("none", decided="OK"))
        result = self.run_edit()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_loading_the_approval_check_leaves_sys_path_alone(self) -> None:
        code = ("import sys; sys.path.insert(0, %r); before = list(sys.path); "
                "import lib.request_diff_approval; print(sys.path == before)") % str(SCRIPTS)
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), "True", result.stderr)

    def test_a_new_presentation_after_the_correction_is_judged_itself(self) -> None:
        self.transcript_with(assistant(self.NO_TAG), reply(), correction("none", decided="OK"), assistant(self.NO_TAG))
        self.assertEqual(self.run_edit().returncode, 2)


class SteeringWriteWrapperTest(_Fixture):
    """実際の入口（hooks.json の run-steering-write-hook.sh。`python3 -I` で起動する）。"""

    def run_wrapper(self) -> subprocess.CompletedProcess:
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(self.state), "old_string": "Human Check Status: pending",
                           "new_string": "Human Check Status: approved | evidence: human:承認まで"},
            "transcript_path": str(self.transcript),
            "cwd": str(self.repo),
        }
        env = self.env()
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        return subprocess.run(["bash", str(SCRIPTS / "run-steering-write-hook.sh")], input=json.dumps(payload),
                              env=env, capture_output=True, text=True)

    def test_all_none_approval_is_allowed_through_the_wrapper(self) -> None:
        self.transcript_with(assistant(presentation("なし")), HUMAN)
        result = self.run_wrapper()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_differing_point_is_denied_through_the_wrapper(self) -> None:
        self.transcript_with(assistant(presentation("あり: 全レーンに入れる")), HUMAN)
        result = self.run_wrapper()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("gdd-requirements-amendment", json.loads(result.stderr)["systemMessage"])

    def test_correction_after_the_reply_is_allowed_through_the_wrapper(self) -> None:
        """Stop の hook が動かずにタグの無い確認が人に届いても、返事の後の補正で承認を書ける。"""
        self.transcript_with(assistant(CorrectionTest.NO_TAG), reply(), correction("none", decided="OK"))
        result = self.run_wrapper()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class BashEntryTest(_Fixture):
    """Bash の入口。承認を書くコマンドは、提示を読まずに Write・Edit へ付け替える（python は起動しない）。"""

    APPROVE = "sed -i '' 's/^- Human Check Status: .*/- Human Check Status: approved/' .steering/20261110-x/state.md"

    def run_bash(self, command: str, script: Path = BASH_HOOK, env: dict | None = None) -> subprocess.CompletedProcess:
        payload = {"tool_name": "Bash", "tool_input": {"command": command, "description": "x"},
                   "transcript_path": str(self.transcript), "cwd": str(self.repo)}
        return subprocess.run(["bash", str(script)], input=json.dumps(payload, ensure_ascii=False),
                              env=env or self.env(), capture_output=True, text=True, cwd=str(self.repo))

    def decision(self, result: subprocess.CompletedProcess) -> str | None:
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]

    def test_approval_by_bash_is_always_redirected(self) -> None:
        self.transcript_with(assistant(presentation("なし")), HUMAN)
        result = self.run_bash(self.APPROVE)
        self.assertEqual(self.decision(result), "deny")
        reason = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Edit", reason)

    def test_command_without_both_words_is_allowed(self) -> None:
        self.assertIsNone(self.decision(self.run_bash("grep 'Human Check Status' state.md")))
        self.assertIsNone(self.decision(self.run_bash("git status")))

    def test_kill_switch_skips(self) -> None:
        home = self.tmp / "home"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        env = self.env()
        env["HOME"] = str(home)
        self.assertIsNone(self.decision(self.run_bash(self.APPROVE, env=env)))

    def test_missing_kill_switch_file_denies(self) -> None:
        broken = self.tmp / "broken" / "scripts"
        (broken / "lib").mkdir(parents=True)
        shutil.copy(BASH_HOOK, broken / BASH_HOOK.name)
        self.assertEqual(self.decision(self.run_bash(self.APPROVE, script=broken / BASH_HOOK.name)), "deny")

    def test_hook_does_not_start_python(self) -> None:
        env = self.env()
        env["PATH"] = "/usr/bin:/bin"
        fake = self.tmp / "nopython"
        fake.mkdir()
        (fake / "python3").write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
        (fake / "python3").chmod(0o755)
        env["PATH"] = f"{fake}:{env['PATH']}"
        self.assertEqual(self.decision(self.run_bash(self.APPROVE, env=env)), "deny")


class HooksJsonWiringTest(unittest.TestCase):
    def test_bash_pre_tool_use_runs_the_hook(self) -> None:
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        commands = [
            h["command"]
            for entry in hooks["hooks"]["PreToolUse"] if entry.get("matcher") == "Bash"
            for h in entry["hooks"]
        ]
        self.assertTrue(any(BASH_HOOK.name in c for c in commands))


if __name__ == "__main__":
    unittest.main()
