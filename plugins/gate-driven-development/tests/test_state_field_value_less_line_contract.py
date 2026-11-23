"""state.md canonical field の「値の無い行は現在値ではない」規則（R-1）を
実装横断で固定する契約テスト。

背景（2026-09-04 実機再現 / requirements.md § 判断材料）: `- Resume From:`
（空値）→ `- Resume From: gdd-tdd`（値付き）の順に並ぶ state.md に対し、
`gdd_validate_active_state_fields` は rc=1 / missing=`Resume From` を返して
いた。原因は `gdd_extract_doc_field`（awk）が最初に一致した field 行で
`exit` し、その行の値が空でもそのまま返すこと。

母集団は数ではなく規則で定義する（round 3 の枠組み是正、正本は
`requirements.md` § 判断材料「母集団の規則と除外記録」/ `adr.md` ADR-1）:
「(i) hook / skill / command が runtime で呼ぶ経路にあり、(ii) state.md の
canonical field を読み、(iii) 共通受理形 `- <Field>: <値>` / `<Field>: <値>`
を共有する reader」。現時点で該当する 6 実装は
`tests/test_state_field_value_less_line_contract.py::ValueLessLineCrossImplementationTests`
の docstring に列挙する（本ファイルの他クラスから段階的に追記される）。

除外（見つかったものの記録。完全性は主張しない）: bare 形限定 reader
（`run-session-start-hook.sh` の QUICK_REBOOT Task Size 抽出）、runtime
非使用の 3 lint + `find-stale-steerings.sh:extract_field`、行頭アンカーを持たない
`lib/handoff_summary.py:_is_terminal_tasklist` 内の `Next Action=` 部分文字列 reader と
`collect-gdd-telemetry.py:parse_task_metrics`（`Task Size` の直接 re.search） の `Task Size` reader。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _plugin_module_loader import PLUGIN_ROOT, load_plugin_module
from _git_fixture import init_repo
DETECT_STEERING_LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
SELF_REVIEW_EVIDENCE = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "self-review-evidence.sh"
MERGE_GATE_EVIDENCE = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "merge-gate-evidence.sh"
TASK_BINDING = PLUGIN_ROOT / "scripts" / "gdd_task_binding.py"
LOOP_SCRIPT = PLUGIN_ROOT / "scripts" / "setup-gdd-loop.sh"
VALIDATE_WRITE = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
TELEMETRY_SCRIPT = PLUGIN_ROOT / "scripts" / "collect-gdd-telemetry.py"

FENCE = "```"


class ValueLessLinePresenceCheckTests(unittest.TestCase):
    """`gdd_validate_active_state_fields` が Resume From / Human Check Status /
    Next Action の値の無い canonical 行を「欠落」と誤判定しないこと
    （AC-1 / AC-2）。fail-closed が緩んでいないこと（AC-3 (a)(b)(c)）も同居
    させる。`tests/test_route_in_progress_reader_contract.py::RouteInProgressPresenceCheckTests`
    と同型。
    """

    def _write_state(self, tmp: Path, body: str) -> Path:
        steering = tmp / ".steering" / "20260904-example"
        steering.mkdir(parents=True)
        (steering / "state.md").write_text(body, encoding="utf-8")
        return steering

    def _validate(self, steering_dir: Path, tasklist_canonical: str = "false") -> tuple[int, str]:
        script = (
            f'source "{DETECT_STEERING_LIB}"; '
            f'GDD_STEERING_DIR="{steering_dir}"; GDD_TASKLIST_CANONICAL="{tasklist_canonical}"; '
            'gdd_validate_active_state_fields; '
            'printf "%s\\n" "$?" "$GDD_ACTIVE_STATE_MISSING"'
        )
        proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        lines = proc.stdout.splitlines() + ["", ""]
        return int(lines[0] or 1), lines[1]

    def test_resume_from_value_less_line_does_not_hide_the_canonical_line(self) -> None:
        """AC-1: 空値行が先、値付き行が後。値部が空白/タブのみの形でも同じ結果。"""
        for value_less in ("- Resume From:", "- Resume From:   ", "- Resume From:\t"):
            body = (
                "## Gate Status\n"
                f"{value_less}\n"
                "- Resume From: gdd-test-driven-development\n"
                "- Human Check Status: approved\n"
                "- Route In Progress: none\n"
            )
            with tempfile.TemporaryDirectory() as d:
                steering = self._write_state(Path(d), body)
                rc, missing = self._validate(steering)
            self.assertEqual((rc, missing), (0, ""), value_less)

    def test_human_check_status_value_less_line_does_not_hide_the_canonical_line(self) -> None:
        """AC-2 (Human Check Status)。"""
        body = (
            "## Gate Status\n"
            "- Resume From: gdd-test-driven-development\n"
            "- Human Check Status:   \n"
            "- Human Check Status: approved\n"
            "- Route In Progress: none\n"
        )
        with tempfile.TemporaryDirectory() as d:
            steering = self._write_state(Path(d), body)
            rc, missing = self._validate(steering)
        self.assertEqual((rc, missing), (0, ""))

    def test_next_action_value_less_line_does_not_hide_the_canonical_line(self) -> None:
        """AC-2 (Next Action)。canonical tasklist phase（3 gate approved）を模して
        GDD_TASKLIST_CANONICAL=true を直接与える（RouteInProgressPresenceCheckTests
        と同じ手法。gdd_check_3field_gate 自体は T-1 の別テストクラスで拘束する）。
        """
        state_body = (
            "## Gate Status\n"
            "- Resume From: gdd-test-driven-development\n"
            "- Human Check Status: approved\n"
            "- Route In Progress: none\n"
            "- Next Action:\n"
            "- Next Action: gdd-test-driven-development\n"
        )
        with tempfile.TemporaryDirectory() as d:
            steering = self._write_state(Path(d), state_body)
            (steering / "tasklist.md").write_text("# Tasklist\n", encoding="utf-8")
            rc, missing = self._validate(steering, tasklist_canonical="true")
        self.assertEqual((rc, missing), (0, ""))

    def test_field_with_no_canonical_line_is_still_reported(self) -> None:
        """AC-3(a): 行が1本も無ければ従来どおり missing（回帰ガード）。"""
        body = "## Gate Status\n- Human Check Status: approved\n- Route In Progress: none\n"
        with tempfile.TemporaryDirectory() as d:
            steering = self._write_state(Path(d), body)
            rc, missing = self._validate(steering)
        self.assertEqual(rc, 1)
        self.assertIn("Resume From", missing)

    def test_field_only_inside_a_closed_fence_is_still_reported(self) -> None:
        """AC-3(b): 閉じた fence の中にしか値付き行が無ければ従来どおり missing。"""
        body = (
            "## Gate Status\n"
            "- Human Check Status: approved\n"
            "- Route In Progress: none\n"
            f"{FENCE}\n- Resume From: gdd-test-driven-development\n{FENCE}\n"
        )
        with tempfile.TemporaryDirectory() as d:
            steering = self._write_state(Path(d), body)
            rc, missing = self._validate(steering)
        self.assertEqual(rc, 1)
        self.assertIn("Resume From", missing)

    def test_field_with_only_a_value_less_line_is_still_reported(self) -> None:
        """AC-3(c): 空値行のみで値付き行が1本も無ければ従来どおり missing
        （走査継続ロジックが最後の空値行を返したり fail-closed を抜けたりしない）。
        """
        body = (
            "## Gate Status\n"
            "- Resume From:\n"
            "- Human Check Status: approved\n"
            "- Route In Progress: none\n"
        )
        with tempfile.TemporaryDirectory() as d:
            steering = self._write_state(Path(d), body)
            rc, missing = self._validate(steering)
        self.assertEqual(rc, 1)
        self.assertIn("Resume From", missing)


class ValueLessLineUnclosedFenceTests(unittest.TestCase):
    """AC-3-d（DM-2）: 未閉鎖 fence 以降にのみ値付き行がある形は present に転じる
    （R-1 が持ち込む意図的な挙動変化）。閉じた fence の中にしか値付き行が無い
    場合は AC-3(b) と非矛盾で従来どおり missing。2 本を対で固定する。
    """

    def _extract(self, text: str, field: str) -> str:
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "doc.md"
            target.write_text(text, encoding="utf-8")
            script = f'source "{DETECT_STEERING_LIB}"; gdd_extract_doc_field "{target}" "{field}"'
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        return proc.stdout.strip()

    def test_unclosed_fence_transitions_missing_to_present(self) -> None:
        text = f"- Resume From:\n{FENCE}\n- Resume From: gdd-test-driven-development\n"
        self.assertEqual(self._extract(text, "Resume From"), "gdd-test-driven-development")

    def test_closed_fence_stays_missing_consistent_with_ac_3_b(self) -> None:
        text = f"- Resume From:\n{FENCE}\n- Resume From: gdd-test-driven-development\n{FENCE}\n"
        self.assertEqual(self._extract(text, "Resume From"), "")


class ValueLessLineThreeFieldGateTests(unittest.TestCase):
    """AC-17 / DM-1: `gdd_check_3field_gate` の 3 gate 値（Requirements Review
    Status / Design Review Status / Human Check Status）にも AC-3 同型の境界を
    固定する。GATE_FILE は state.md 優先、無ければ design.md（SA3-2）。
    positive 方向（3 field すべて空値行 + 後続 approved）と `=` 区切り形も
    固定する。pipe のみの先行行は R-1 の対象外（DA3-3）。
    """

    def _gate(self, tmp: Path, gate_filename: str, gate_body: str) -> tuple[str, str]:
        steering = tmp / ".steering" / "20260904-example"
        steering.mkdir(parents=True)
        (steering / "tasklist.md").write_text("# Tasklist\n", encoding="utf-8")
        (steering / gate_filename).write_text(gate_body, encoding="utf-8")
        script = (
            f'source "{DETECT_STEERING_LIB}"; '
            f'GDD_STEERING_DIR="{steering}"; '
            'gdd_check_3field_gate; '
            'printf "%s\\n%s\\n" "$GDD_TASKLIST_CANONICAL" "$GDD_GATE_FILE"'
        )
        proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        lines = proc.stdout.splitlines() + ["", ""]
        return lines[0], lines[1]

    def _three_fields(self, req: str, des: str, hum: str) -> str:
        return f"- Requirements Review Status: {req}\n- Design Review Status: {des}\n- Human Check Status: {hum}\n"

    def test_a_missing_gate_field_line_keeps_canonical_false(self) -> None:
        """AC-17(a): いずれかの行が1本も無ければ false。"""
        with tempfile.TemporaryDirectory() as d:
            body = "- Requirements Review Status: approved\n- Design Review Status: approved\n"
            canonical, _ = self._gate(Path(d), "state.md", body)
        self.assertEqual(canonical, "false")

    def test_a_closed_fenced_gate_field_keeps_canonical_false(self) -> None:
        """AC-17(b)。"""
        with tempfile.TemporaryDirectory() as d:
            body = self._three_fields("approved", "approved", "") + f"{FENCE}\n- Human Check Status: approved\n{FENCE}\n"
            canonical, _ = self._gate(Path(d), "state.md", body)
        self.assertEqual(canonical, "false")

    def test_a_value_less_only_gate_field_keeps_canonical_false(self) -> None:
        """AC-17(c): 空値行のみで値付き行が1本も無ければ false。"""
        with tempfile.TemporaryDirectory() as d:
            body = "- Requirements Review Status: approved\n- Design Review Status: approved\n- Human Check Status:\n"
            canonical, _ = self._gate(Path(d), "state.md", body)
        self.assertEqual(canonical, "false")

    def test_value_less_line_before_approved_line_becomes_canonical_true(self) -> None:
        """positive 方向: 3 field すべてが「空値行 + 後続 approved」でも true。"""
        with tempfile.TemporaryDirectory() as d:
            body = (
                "- Requirements Review Status:\n- Requirements Review Status: approved\n"
                "- Design Review Status:\n- Design Review Status: approved\n"
                "- Human Check Status:\n- Human Check Status: approved\n"
            )
            canonical, _ = self._gate(Path(d), "state.md", body)
        self.assertEqual(canonical, "true")

    def test_equals_delimiter_form_is_accepted(self) -> None:
        """`=` 区切りの形を最低1本含める（gdd_check_3field_gate は `=` を正式に受理）。"""
        with tempfile.TemporaryDirectory() as d:
            body = (
                "- Requirements Review Status=\n- Requirements Review Status=approved\n"
                "- Design Review Status=approved\n- Human Check Status=approved\n"
            )
            canonical, _ = self._gate(Path(d), "state.md", body)
        self.assertEqual(canonical, "true")

    def test_design_md_is_used_as_gate_file_when_state_md_is_absent(self) -> None:
        """SA3-2: state.md 不在時は design.md が GATE_FILE になる。managed worktree
        の design.md の一部が canonical gate status 行を持ち、空値行も実在する。
        """
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            steering = tmp / ".steering" / "20260904-example"
            steering.mkdir(parents=True)
            (steering / "tasklist.md").write_text("# Tasklist\n", encoding="utf-8")
            (steering / "design.md").write_text(
                "- Design Review Status:\n- Design Review Status: approved\n"
                "- Requirements Review Status: approved\n- Human Check Status: approved\n",
                encoding="utf-8",
            )
            script = (
                f'source "{DETECT_STEERING_LIB}"; '
                f'GDD_STEERING_DIR="{steering}"; '
                'gdd_check_3field_gate; '
                'printf "%s\\n%s\\n" "$GDD_TASKLIST_CANONICAL" "$GDD_GATE_FILE"'
            )
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
            lines = proc.stdout.splitlines() + ["", ""]
        self.assertEqual(lines[0], "true")
        self.assertTrue(lines[1].endswith("design.md"))

    def test_pipe_only_leading_line_is_not_treated_as_value_less(self) -> None:
        """DA3-3: `gdd_check_3field_gate` は値を `sed 's/[[:space:]|].*//'` で切る
        ため、`- Human Check Status: | evidence: x` が先行する形は R-1 適用後も
        **その行が選ばれて空扱い**になり、後続の approved は遮蔽されたままである
        （pipe 分割は R-1 の空判定に含めない設計、design.md § R-1 の線引き）。
        """
        with tempfile.TemporaryDirectory() as d:
            body = (
                "- Requirements Review Status: approved\n- Design Review Status: approved\n"
                "- Human Check Status: | evidence: x\n- Human Check Status: approved\n"
            )
            canonical, _ = self._gate(Path(d), "state.md", body)
        self.assertEqual(canonical, "false")


class ValueLessLineEvidenceGateTests(unittest.TestCase):
    """AC-6: `self-review-evidence.sh:gdd_parse_self_review_field` / `merge-gate-evidence.sh:gdd_parse_merge_gate_field` は
    `gdd_extract_doc_field` の空文字を missing に変換して block する。
    (a) 値付き行がある場合は present、(b) 空値行のみの場合は従来どおり
    missing で block、を最低1 form ずつ固定する。
    """

    def _self_review_missing(self, body: str) -> str:
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_text(body, encoding="utf-8")
            script = (
                f'source "{DETECT_STEERING_LIB}"; source "{SELF_REVIEW_EVIDENCE}"; '
                f'gdd_parse_self_review_field "{target}" "Self Review"; '
                'printf "%s" "$GDD_SR_MISSING_KEYS"'
            )
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        return proc.stdout

    def _merge_gate_reason(self, body: str, field: str) -> str:
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_text(body, encoding="utf-8")
            script = (
                f'source "{DETECT_STEERING_LIB}"; source "{MERGE_GATE_EVIDENCE}"; '
                f'gdd_parse_merge_gate_field "{target}" "{field}"; '
                'printf "%s" "$GDD_MG_REASON"'
            )
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        return proc.stdout

    #: `self-review-evidence.sh` の `GDD_SR_REQUIRED_TOP_KEYS` を全て満たす値。
    #: 先頭 segment は key を持たない位置指定の sha（同ファイル冒頭の書式コメント）。
    VALID_SELF_REVIEW = (
        "abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes"
        " | lanes: internal=2,grounding=1,adversarial=0 | at: 2026-08-17T00:00:00Z"
    )
    #: `Merge Approval` は他 4 種と書式が違い、先頭 segment が `PR #<n> / head <sha>`、
    #: 時刻 key が `at` ではなく `approved_at`（`merge-gate-evidence.sh:gdd_parse_merge_gate_field の Merge Approval 分岐`）。
    VALID_MERGE_APPROVAL = (
        "PR #7 / head abc1234 | evidence: reviews.md | approved_at: 2026-08-17T00:00:00Z"
    )

    def test_self_review_value_less_line_no_longer_hides_the_value(self) -> None:
        body = f"- Self Review:\n- Self Review: {self.VALID_SELF_REVIEW}\n"
        self.assertEqual(self._self_review_missing(body), "")

    def test_self_review_value_less_line_only_is_still_missing(self) -> None:
        body = "- Self Review:\n"
        self.assertEqual(self._self_review_missing(body), "Self Review")

    def test_merge_approval_value_less_line_no_longer_hides_the_value(self) -> None:
        body = f"- Merge Approval:\n- Merge Approval: {self.VALID_MERGE_APPROVAL}\n"
        self.assertEqual(self._merge_gate_reason(body, "Merge Approval"), "")

    def test_merge_approval_value_less_line_only_is_still_missing(self) -> None:
        body = "- Merge Approval:\n"
        self.assertEqual(self._merge_gate_reason(body, "Merge Approval"), "missing")


class ValueLessLineCrossImplementationTests(unittest.TestCase):
    """AC-5: 母集団の規則に該当し本タスクが揃えた6実装が、同一の入力表に対して
    同じ「値の無い行は現在値ではない」判定を返す。

    規則（正本: requirements.md § 判断材料「母集団の規則と除外記録」/ adr.md
    ADR-1）: 「(i) hook / skill / command が runtime で呼ぶ経路にあり、
    (ii) state.md の canonical field を読み、(iii) 共通受理形
    `- <Field>: <値>` / `<Field>: <値>` を共有する reader」。

    現時点で該当する6実装:
      1. hooks/scripts/lib/detect-steering.sh:gdd_extract_doc_field（awk）
      2. scripts/gdd_task_binding.py:_field
      3. scripts/setup-gdd-loop.sh:parse_field
      4. hooks/scripts/validate-steering-write.py:state_field_value
      5. scripts/collect-gdd-telemetry.py:extract_field
      6. hooks/scripts/gdd_stop_hook.py:resume_from_value（Resume From 固定）

    横断表は共通受理形に限定する。field 名は `Resume From` に固定する
    （6本目が Resume From 専用で任意 field を取れないため）。

    横断表から除外する入力形と理由（AC-5 の除外注記。完全性は主張しない）:
      - `<Field>=<値>`: collect-gdd-telemetry.py:extract_field が `=` を受理しない
      - 大文字小文字の揺れ: setup-gdd-loop.sh:parse_field だけ case-insensitive
      - `Resume From` 以外の field: gdd_stop_hook.py の reader は Resume From 固定
      - bare 形限定 reader `run-session-start-hook.sh` の QUICK_REBOOT Task Size 抽出:
        受理形が異なる。残る非対称は表示の欠落のみで gate ではない
      - runtime 非使用 / 別規約: scripts/lint-resume-integrity.py:FIELD_PATTERNS /
        lint-worktree-provenance.py:FIELD_PATTERNS / lint-state-tasklist-continuity.py:FIELD_PATTERNS /
        find-stale-steerings.sh:extract_field（論点B、人間承認 2026-09-04T14:20:00+09:00）
      - 行頭アンカーを持たない別規約: lib/handoff_summary.py:_is_terminal_tasklist（Next Action= 部分
        文字列）/ collect-gdd-telemetry.py:parse_task_metrics（Task Size を requirements.md から re.search）
      - 「注記のみ行」（値部が pipe から始まる形）: pipe tail の解釈統一は非スコープ
        （requirements.md § 非スコープ）。R-1 適用後も6実装で返り値が割れたまま
        残る（gdd_extract_doc_field / _field / parse_field / resume_from_value は
        注記部分を含めて返し、state_field_value は空文字、extract_field は None を返す）

    この表は現時点で見つかった除外の記録であり、同型 reader の完全な数え上げ
    ではない（round 3 の枠組み是正）。AC-5 は揃えた実装が同一の一致だけを要求する。
    """

    VALUE_LESS_SUFFIXES = ("", "   ", "\t", " ``")

    @classmethod
    def setUpClass(cls) -> None:
        cls.task_binding = _load_module(TASK_BINDING, "gdd_task_binding_cross_impl")
        # staticmethod でラップしないと `self.parse_field(...)` がクラス属性の
        # 関数を記述子として束縛し、暗黙の `self` が第1引数に混入して
        # TypeError になる（T-2 の advisory と同じ落とし穴）。
        cls.parse_field = staticmethod(_load_loop_parse_field())
        cls.validate_write = _load_module(VALIDATE_WRITE, "validate_steering_write_cross_impl")
        cls.telemetry = _load_module(TELEMETRY_SCRIPT, "collect_gdd_telemetry_cross_impl")
        # gdd_stop_hook.py は `from lib.constants import ...` のような相対 import を
        # 持つため、hooks/scripts を sys.path に通す（ValueLessLineStopHookResumeTests
        # と同じパターン。このクラス単独実行時は他クラスの setUpClass に依存できない）。
        scripts_dir = str(PLUGIN_ROOT / "hooks" / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        cls.stop_hook = _load_module(STOP_HOOK, "gdd_stop_hook_cross_impl")

    def _extract_doc_field(self, text: str, field: str, tmp: Path) -> str:
        target = tmp / "doc.md"
        target.write_text(text, encoding="utf-8")
        script = f'source "{DETECT_STEERING_LIB}"; gdd_extract_doc_field "{target}" "{field}"'
        proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        return proc.stdout.strip()

    def test_all_six_implementations_agree_on_every_value_less_form(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            for sep in (":",):  # 横断表は `:` に限定（`=` は extract_field が非受理）
                for suffix in self.VALUE_LESS_SUFFIXES:
                    text = f"- Resume From{sep}{suffix}\n- Resume From: gdd-tdd\n"
                    with self.subTest(sep=sep, suffix=repr(suffix)):
                        self.assertEqual(self._extract_doc_field(text, "Resume From", tmp), "gdd-tdd")
                        self.assertEqual(self.task_binding._field(text, "Resume From"), "gdd-tdd")
                        self.assertEqual(self.parse_field(text, ["Resume From"]), "gdd-tdd")
                        self.assertEqual(self.validate_write.state_field_value(text, "Resume From"), "gdd-tdd")
                        self.assertEqual(self.telemetry.extract_field(text, "Resume From"), "gdd-tdd")
                        self.assertEqual(self.stop_hook.resume_from_value(text), "gdd-tdd")

    def test_first_value_bearing_line_wins_across_all_six_implementations(self) -> None:
        """AC-4（DM3-3）: 値付き行が2本ある fixture で「最初の値付き一致」が
        最終行採択に変わる変異を KILL できることを、6実装すべてで固定する。
        """
        text = "- Resume From: first\n- Resume From: second\n"
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self.assertEqual(self._extract_doc_field(text, "Resume From", tmp), "first")
        self.assertEqual(self.task_binding._field(text, "Resume From"), "first")
        self.assertEqual(self.parse_field(text, ["Resume From"]), "first")
        self.assertEqual(self.validate_write.state_field_value(text, "Resume From"), "first")
        self.assertEqual(self.telemetry.extract_field(text, "Resume From"), "first")
        self.assertEqual(self.stop_hook.resume_from_value(text), "first")

    def test_note_only_line_splits_the_readers_three_ways(self) -> None:
        """DA3-2（注記のみ行 / pipe tail）の**実挙動**を characterization として固定する。

        以前はこのテストが class docstring の文字列有無だけを見ており、実装を
        変えても落ちない hollow test だった（PR #35 独立セルフレビューの M15 が
        SURVIVED）。非スコープであることと「テストしない」ことは別なので、
        3 通りに割れる現状の返り値をそのまま固定する。揃えるのは別タスク。

        入力: `- Human Check Status: | evidence: x` が先、`- ...: approved` が後。
        """
        body = (
            "- Human Check Status: | evidence: x\n"
            "- Human Check Status: approved\n"
        )
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_text(body, encoding="utf-8")
            script = (
                f'source "{DETECT_STEERING_LIB}"; '
                f'gdd_extract_doc_field "{target}" "Human Check Status"'
            )
            awk_out = subprocess.run(["bash", "-c", script], capture_output=True, text=True).stdout.strip()

        # (1) awk と task binding は pipe tail 込みの文字列をそのまま返す
        self.assertEqual(awk_out, "| evidence: x")
        self.assertEqual(self.task_binding._field(body, "Human Check Status"), "| evidence: x")
        # (2) validate-steering-write は判定に pipe tail 込み、返り値は pipe 前 → 空文字
        self.assertEqual(self.validate_write.state_field_value(body, "Human Check Status"), "")
        # (3) telemetry は normalize_field_value が pipe 前を取り空になるため None
        self.assertIsNone(self.telemetry.extract_field(body, "Human Check Status"))


def _load_module(path: Path, name: str):
    """共有ローダ `tests/_plugin_module_loader.load_plugin_module` へ委譲する。

    独自の明示パス loader を書き写すと `sys.modules` 登録のような「必要だと
    記録されている手順」が写し落ちる —— 共有ローダの docstring が明示的に
    禁じている形。呼び出し側の互換のため `(path, name)` 形の signature は
    残すが、`name` は共有ローダが `gdd_contract_<stem>` を採るため使わない
    （同一ファイルを別名で重複ロードしない副次効果もある）。
    """
    return load_plugin_module(str(path.relative_to(PLUGIN_ROOT)))


def _load_loop_parse_field():
    """`setup-gdd-loop.sh` の heredoc から parse_field 系の定義だけを取り出す。
    抽出方法は `tests/test_canonical_field_line_anchoring_contract.py::_load_loop_parse_field`
    と同じ（この script は plugin 外からも単体実行されるため import できない）。
    """
    source = LOOP_SCRIPT.read_text(encoding="utf-8")
    blocks = []
    backtick = re.search(r"^BACKTICK = .*$", source, re.MULTILINE)
    assert backtick, f"BACKTICK definition not found in {LOOP_SCRIPT}"
    blocks.append(backtick.group(0))
    for name in ("normalize_line", "strip_fenced_blocks", "parse_field"):
        match = re.search(
            rf"^def {name}\(.*?(?=^def |\n^[a-zA-Z@#])", source, re.MULTILINE | re.DOTALL
        )
        assert match, f"{name} definition not found in {LOOP_SCRIPT}"
        blocks.append(match.group(0))
    namespace: dict = {}
    exec("\n".join(blocks), namespace)  # noqa: S102 - shipped source を直接検証するため
    return namespace["parse_field"]


class SimpleFieldReaderValueLessLineTests(unittest.TestCase):
    """`gdd_task_binding.py:_field` と `setup-gdd-loop.sh:parse_field` の
    空値行スキップ（Option C の 2 実装分）。8 入力（空/空白/タブ/バッククォート2個 の
    それぞれについて `:` / `=` の2形）を「空値行が先・値付き行が後」の2行構成で与える。
    """

    VALUE_LESS_SUFFIXES = ("", "   ", "\t", " ``")

    @classmethod
    def setUpClass(cls) -> None:
        cls.task_binding = _load_module(TASK_BINDING, "gdd_task_binding_under_test")
        # staticmethod でラップしないと `self.parse_field(...)` がクラス属性の
        # 関数を記述子として束縛し、暗黙の `self` が第1引数に混入して
        # TypeError（本来の RED 対象ではない test harness の不具合）になる。
        cls.parse_field = staticmethod(_load_loop_parse_field())

    def test_task_binding_field_skips_value_less_line(self) -> None:
        for sep in (":", "="):
            for suffix in self.VALUE_LESS_SUFFIXES:
                text = (
                    f"- Resume From{sep}{suffix}\n"
                    "- Resume From: gdd-test-driven-development\n"
                )
                with self.subTest(sep=sep, suffix=repr(suffix)):
                    self.assertEqual(
                        self.task_binding._field(text, "Resume From"),
                        "gdd-test-driven-development",
                    )

    def test_task_binding_field_returns_empty_when_no_value_bearing_line_exists(self) -> None:
        self.assertEqual(self.task_binding._field("- Resume From:\n", "Resume From"), "")

    def test_loop_parse_field_skips_value_less_line(self) -> None:
        for sep in (":", "="):
            for suffix in self.VALUE_LESS_SUFFIXES:
                text = (
                    f"- Resume From{sep}{suffix}\n"
                    "- Resume From: gdd-test-driven-development\n"
                )
                with self.subTest(sep=sep, suffix=repr(suffix)):
                    self.assertEqual(
                        self.parse_field(text, ["Resume From"]),
                        "gdd-test-driven-development",
                    )

    def test_loop_parse_field_returns_empty_when_no_value_bearing_line_exists(self) -> None:
        self.assertEqual(self.parse_field("- Resume From:\n", ["Resume From"]), "")


class RegexFieldReaderValueLessLineTests(unittest.TestCase):
    """`validate-steering-write.py:state_field_value` と
    `collect-gdd-telemetry.py:extract_field` の空値行スキップ。
    """

    VALUE_LESS_SUFFIXES = ("", "   ", "\t", " ``")

    @classmethod
    def setUpClass(cls) -> None:
        cls.validate_write = _load_module(VALIDATE_WRITE, "validate_steering_write_under_test")
        cls.telemetry = _load_module(TELEMETRY_SCRIPT, "collect_gdd_telemetry_under_test")

    def test_state_field_value_skips_value_less_line(self) -> None:
        for sep in (":", "="):
            for suffix in self.VALUE_LESS_SUFFIXES:
                text = f"- Resume From{sep}{suffix}\n- Resume From: gdd-test-driven-development\n"
                with self.subTest(sep=sep, suffix=repr(suffix)):
                    self.assertEqual(
                        self.validate_write.state_field_value(text, "Resume From"),
                        "gdd-test-driven-development",
                    )

    def test_state_field_value_returns_empty_when_no_value_bearing_line_exists(self) -> None:
        self.assertEqual(self.validate_write.state_field_value("- Resume From:\n", "Resume From"), "")

    def test_extract_field_returns_none_when_no_value_bearing_line_exists(self) -> None:
        self.assertIsNone(self.telemetry.extract_field("- Resume From:\n", "Resume From"))


STOP_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "gdd_stop_hook.py"
TASKLIST_PARSE = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "tasklist_parse.py"


class ValueLessLineStopHookResumeTests(unittest.TestCase):
    """AC-8-2 / DH-1: `gdd_stop_hook.py` の Resume From reader。module 直下へ
    引き上げた `latest_steering_resume_from()` を import し、実 state.md
    fixture（`.steering/<task>/state.md`）に対して呼ぶ（DM3-2 の shipped 経路）。
    `resume_from_value()` 単体も横断表側の入力で拘束する。
    """

    VALUE_LESS_SUFFIXES = ("", "   ", "\t", " ``")

    @classmethod
    def setUpClass(cls) -> None:
        # gdd_stop_hook.py は `from lib.constants import ...` のような相対 import を
        # 持つため、hooks/scripts を sys.path に通す（_stop_hook_test_base.py と同じパターン）。
        scripts_dir = str(PLUGIN_ROOT / "hooks" / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        cls.stop_hook = _load_module(STOP_HOOK, "gdd_stop_hook_under_test")

    def test_resume_from_value_returns_empty_when_no_value_bearing_line_exists(self) -> None:
        self.assertEqual(self.stop_hook.resume_from_value("- Resume From:\n"), "")

    def test_latest_steering_resume_from_reads_the_shipped_state_file(self) -> None:
        """DM3-2: `latest_steering_resume_from()` が実 state.md fixture を読む
        shipped 経路であること（`_check_steering_fallback` のテスト側複製を
        経由しない）。git repo は共有 fixture `_git_fixture.init_repo` で作る。
        """
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "repo"
            repo.mkdir()
            init_repo(repo)
            steering = repo / ".steering" / "20260904-example"
            steering.mkdir(parents=True)
            (steering / "tasklist.md").write_text("# Tasklist\n", encoding="utf-8")
            (steering / "state.md").write_text(
                "- Resume From:   \n- Resume From: human-check-waiting\n", encoding="utf-8"
            )
            result = self.stop_hook.latest_steering_resume_from(repo)
        self.assertEqual(result, "human-check-waiting")


class ValueLessLineStopHookCallSiteContractTests(unittest.TestCase):
    """`RESUME_FROM_PATTERN` を適用する箇所が `resume_from_value()` の1箇所のみ
    であることを機械検査する（`RouteInProgressCallSiteContractTests` と同型）。
    定義行（`RESUME_FROM_PATTERN = re.compile(...)`）は検査対象から除く（DA3-4）。

    定義と適用は `lib/tasklist_parse.py` にある。`gdd_stop_hook.py` は import で
    再エクスポートするだけ（同 hook が行数上限 1500 に対して余裕を持たないため、
    健全性ゲートを自分で塞がないよう reader を lib へ寄せた）。**hook 側に適用箇所が
    生えていないこと**も同時に検査し、2 箇所で走査する形へ戻る退行を止める。
    """

    def test_resume_from_pattern_is_applied_in_exactly_one_place(self) -> None:
        apply_pattern = re.compile(r"RESUME_FROM_PATTERN\.(match|search)\(")
        lib_offenders = apply_pattern.findall(TASKLIST_PARSE.read_text(encoding="utf-8"))
        self.assertEqual(
            len(lib_offenders), 1, f"lib 側の適用箇所が {len(lib_offenders)} 件ある: {lib_offenders}"
        )
        hook_offenders = apply_pattern.findall(STOP_HOOK.read_text(encoding="utf-8"))
        self.assertEqual(
            len(hook_offenders), 0, f"hook 側に適用箇所が生えている: {hook_offenders}"
        )


class StopHookResumeFromLineAnchoringTests(unittest.TestCase):
    """R-M1: `gdd_stop_hook.py` の `Resume From` reader も、他 5 実装と同じ
    行頭アンカー規約に従うこと。

    正本は `references/state-schema.json` の `canonical_line_form`:
    `allowed_line_prefix` = `["", "- "]` / `indented_lines_are_not_fields` = true。
    `RESUME_FROM_PATTERN` は `^[-*]?\\s*` で `*` bullet とインデント行を受理して
    おり、この 1 実装だけが規約から外れていた（`test_canonical_field_line_anchoring_contract.py`
    の対象外だったため見落とされていた）。

    R-1（空値行スキップ）はこの穴の到達性を広げる: 値がバッククォートだけの行
    （`- Resume From: ``）は R-1 で「値なし」と判定されて飛ばされるため、
    後続のインデント履歴メモが現在値の候補に昇格し、**偽の human check 停止**が
    起きうる（`rf_val == "human-check-waiting"` が真になる）。
    """

    @classmethod
    def setUpClass(cls) -> None:
        hooks_scripts = PLUGIN_ROOT / "hooks" / "scripts"
        if str(hooks_scripts) not in sys.path:
            sys.path.insert(0, str(hooks_scripts))
        cls.stop_hook = _load_module(hooks_scripts / "gdd_stop_hook.py", "gdd_stop_hook_anchoring")

    def test_indented_line_is_not_a_canonical_field(self) -> None:
        """入れ子 bullet の履歴メモは現在値ではない（indented_lines_are_not_fields）。"""
        for indented in (
            "  Resume From: human-check-waiting（履歴メモ）",
            "  - Resume From: human-check-waiting（履歴メモ）",
            "\tResume From: human-check-waiting（履歴メモ）",
        ):
            with self.subTest(indented=indented):
                self.assertEqual(self.stop_hook.resume_from_value(indented + "\n"), "")

    def test_star_bullet_is_not_a_canonical_field(self) -> None:
        """`allowed_line_prefix` は `""` と `"- "` のみ。`*` bullet は受理しない。"""
        self.assertEqual(
            self.stop_hook.resume_from_value("* Resume From: human-check-waiting\n"), ""
        )

    def test_accepted_prefixes_still_work(self) -> None:
        """回帰ガード: 受理形（bare / `- ` / バッククォート装飾）は従来どおり読める。"""
        for line in (
            "Resume From: human-check-waiting",
            "- Resume From: human-check-waiting",
            "- `Resume From: human-check-waiting`",
            "- Resume From: `human-check-waiting`",
            "- Resume From=human-check-waiting",
        ):
            with self.subTest(line=line):
                self.assertEqual(
                    self.stop_hook.resume_from_value(line + "\n"), "human-check-waiting"
                )

    def test_value_less_line_then_indented_memo_does_not_fake_a_human_check_stop(self) -> None:
        """R-M1 の再現形: バッククォートのみの値行 + インデント履歴メモ。

        アンカー修正前は `human-check-waiting（Attempt #2 の履歴メモ）` を返し、
        `latest_steering_resume_from()` 経由で偽の human check 停止を引き起こす。
        """
        body = (
            "- Resume From: ``\n"
            "  Resume From: human-check-waiting（Attempt #2 の履歴メモ）\n"
        )
        self.assertEqual(self.stop_hook.resume_from_value(body), "")

    def test_agrees_with_the_other_readers_on_the_same_input(self) -> None:
        """同じ入力に対し `gdd_extract_doc_field` と一致すること（横断表と同じ観点）。"""
        body = "- Resume From: ``\n  Resume From: human-check-waiting（履歴メモ）\n"
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_text(body, encoding="utf-8")
            script = f'source "{DETECT_STEERING_LIB}"; gdd_extract_doc_field "{target}" "Resume From"'
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        self.assertEqual(self.stop_hook.resume_from_value(body), proc.stdout.strip())


class TelemetryFieldExtractionBehaviorTests(unittest.TestCase):
    """PR #35 review (Copilot): `parse_task_metrics` の helper 抽出が
    「一致なし」と「一致したが正規化後に空」を潰していた退行を固定する。

    旧実装は `if size_match: m.task_size = ...rstrip(".")` で、`Task Size: .`
    のように正規化後が空になる入力でも **空文字を代入**していた。helper 抽出時に
    `_first_group(...) or m.task_size` と書いたため既定値 `"unknown"` が残り、
    telemetry の `by_size` 集計バケットが変わっていた（挙動不変のはずの
    リファクタが挙動を変えていた）。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.telemetry = _load_module(TELEMETRY_SCRIPT, "collect_gdd_telemetry_behavior")

    def test_first_group_returns_none_when_there_is_no_match(self) -> None:
        self.assertIsNone(self.telemetry._first_group(r"Task Size\s*[:：]\s*([^\n]+)", "no field here"))

    def test_first_group_returns_the_value_when_matched(self) -> None:
        self.assertEqual(
            self.telemetry._first_group(r"Task Size\s*[:：]\s*([^\n]+)", "Task Size: standard"),
            "standard",
        )

    def test_matched_but_empty_after_normalization_is_not_the_default(self) -> None:
        """`Task Size: .` は `rstrip(".")` で空になる。旧実装どおり空文字を採る
        （既定値 `unknown` へ落とさない）。
        """
        with tempfile.TemporaryDirectory() as d:
            steering = Path(d) / ".steering" / "20260904-example"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text("- Resume From: gdd-test-driven-development\n", encoding="utf-8")
            (steering / "requirements.md").write_text("Task Size: .\n", encoding="utf-8")
            (steering / "tasklist.md").write_text("# Tasklist\n", encoding="utf-8")
            metrics = self.telemetry.parse_task_metrics(steering, "wt")
        self.assertEqual(metrics.task_size, "")

    def test_absent_field_keeps_the_unknown_default(self) -> None:
        """一致が無い場合は従来どおり既定値 `unknown` のまま（対の回帰ガード）。"""
        with tempfile.TemporaryDirectory() as d:
            steering = Path(d) / ".steering" / "20260904-example"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text("- Resume From: gdd-test-driven-development\n", encoding="utf-8")
            (steering / "requirements.md").write_text("no size field\n", encoding="utf-8")
            (steering / "tasklist.md").write_text("# Tasklist\n", encoding="utf-8")
            metrics = self.telemetry.parse_task_metrics(steering, "wt")
        self.assertEqual(metrics.task_size, "unknown")


class LinePrefixAsymmetryIsRecordedTests(unittest.TestCase):
    """PR #35 review (Copilot): 行頭 bullet の受理形が全実装で揃っていないこと、
    および揃っていない実装が `state-schema.json` に記録されていることを固定する。

    実測（本テストが検証する）: `* Resume From: x` を値 reader 4 本と
    `gdd_stop_hook.resume_from_value` は読まないが、`setup-gdd-loop.sh:normalize_line`
    は `-` / `*` / `+` を受理する。この非対称は PR #35 以前から存在し、
    `tests/test_canonical_field_line_anchoring_contract.py` が `* Next Action: done` を
    `loop_parse_field` の受理形として固定している。揃えるには同テストの期待値変更が
    必要なため PR #35 では触らず、`state-schema.json` の
    `canonical_line_form.line_prefix_exceptions` に記録した。
    """

    @classmethod
    def setUpClass(cls) -> None:
        hooks_scripts = PLUGIN_ROOT / "hooks" / "scripts"
        if str(hooks_scripts) not in sys.path:
            sys.path.insert(0, str(hooks_scripts))
        cls.stop_hook = _load_module(hooks_scripts / "gdd_stop_hook.py", "gdd_stop_hook_prefix")
        cls.binding = _load_module(TASK_BINDING, "gdd_task_binding_prefix")
        cls.parse_field = staticmethod(_load_loop_parse_field())

    def test_value_readers_and_stop_hook_reject_the_star_bullet(self) -> None:
        body = "* Resume From: gdd-test-driven-development\n"
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_text(body, encoding="utf-8")
            script = f'source "{DETECT_STEERING_LIB}"; gdd_extract_doc_field "{target}" "Resume From"'
            awk_out = subprocess.run(["bash", "-c", script], capture_output=True, text=True).stdout.strip()
        self.assertEqual(awk_out, "", "gdd_extract_doc_field")
        self.assertEqual(self.binding._field(body, "Resume From"), "", "gdd_task_binding._field")
        self.assertEqual(self.stop_hook.resume_from_value(body), "", "gdd_stop_hook.resume_from_value")

    def test_loop_reader_still_accepts_the_star_bullet(self) -> None:
        """既知の非対称（PR #35 以前から）。揃えるには既存契約テストの期待値変更が要る。"""
        self.assertEqual(
            self.parse_field("* Next Action: done\n", ["Next Action"]), "done"
        )


class BacktickPairThenValueAsymmetryTests(unittest.TestCase):
    """PR #35 独立セルフレビュー（correctness lane）: `` ` `` 対の**後ろに値が続く**形で
    `gdd_stop_hook.resume_from_value` が他 5 reader と割れることを固定する。

    `RESUME_FROM_PATTERN` の末尾 group `` (`.*)?$ `` は「最初のバッククォート以降」を
    丸ごと吸うため、`` - Resume From: `` human-check-waiting `` では `group(1)` が
    `` ` `` だけになる。R-1 の空判定（backtick 除去後に空）でこの行が飛ばされ、
    **後続行の値**が返る。他 5 reader は同じ行を `human-check-waiting` と読む。

    これは PR #35 が持ち込んだ退行ではない（旧実装はこの行を `` ` `` として返しており、
    やはり他 5 本と割れていた）。ただし `ValueLessLineCrossImplementationTests` の
    `VALUE_LESS_SUFFIXES` はこの形を含まないため、AC-5 の「揃えた実装が同一の一致を
    返す」という主張はこの形では成立しない。**非対称を隠さずテストで固定する**のが
    本クラスの目的で、揃えるには `RESUME_FROM_PATTERN` の backtick 扱いを
    他 5 本（値側だけ `strip("`")`）へ寄せる必要があり、本 PR のスコープ外。
    """

    #: 先頭が `` ` `` 対で、その後ろに値が続く行。`- Resume From: `` human-check-waiting`
    ASYMMETRIC_LINE = "- Resume From: `` human-check-waiting"
    FOLLOWING_LINE = "- Resume From: gdd-test-driven-development"

    @classmethod
    def setUpClass(cls) -> None:
        hooks_scripts = PLUGIN_ROOT / "hooks" / "scripts"
        if str(hooks_scripts) not in sys.path:
            sys.path.insert(0, str(hooks_scripts))
        cls.stop_hook = _load_module(hooks_scripts / "gdd_stop_hook.py", "gdd_stop_hook_backtick")
        cls.task_binding = _load_module(TASK_BINDING, "gdd_task_binding_backtick")

    def _body(self) -> str:
        return f"{self.ASYMMETRIC_LINE}\n{self.FOLLOWING_LINE}\n"

    def test_stop_hook_skips_the_line_and_returns_the_next_value(self) -> None:
        """stop hook は `` ` `` を「値なし」と見て飛ばし、**後続行**の値を返す。"""
        self.assertEqual(
            self.stop_hook.resume_from_value(self._body()), "gdd-test-driven-development"
        )

    def test_the_other_readers_read_the_line_itself(self) -> None:
        """他 reader は同じ行を `human-check-waiting` と読む（= stop hook と割れる）。"""
        body = self._body()
        self.assertEqual(self.task_binding._field(body, "Resume From"), "human-check-waiting")
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_text(body, encoding="utf-8")
            script = f'source "{DETECT_STEERING_LIB}"; gdd_extract_doc_field "{target}" "Resume From"'
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        self.assertEqual(proc.stdout.strip(), "human-check-waiting")


class DeclaredBehaviorChangeSm31Tests(unittest.TestCase):
    """PR #35 独立セルフレビュー（M-SM3-1）: CHANGELOG が「意図的な挙動変化」の
    **唯一の enforcement が消える方向**として開示した SM3-1 を固定する。

    他 5 件は「missing → present」方向で、いずれもテストがあった。SM3-1 だけは
    `active → none`（active steering の解決自体が消え `[gdd:blocked]` の context
    注入も止まる）という逆方向なのに、固定するテストが 1 本も無かった。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.binding = _load_module(TASK_BINDING, "gdd_task_binding_sm31")

    def test_value_less_line_then_terminal_value_is_now_terminal(self) -> None:
        """空値行 + 後続 `done` は terminal と判定される（R-1 が持ち込む変化）。

        R-1 適用前は空値行が遮蔽して非 terminal と判定され、当該 steering が
        active candidate に残っていた。適用後は terminal として除外される。
        """
        body = "- Resume From: gdd-test-driven-development\n- Next Action:\n- Next Action: done\n"
        self.assertTrue(self.binding._is_terminal_state(body))

    def test_value_less_line_then_non_terminal_value_stays_active(self) -> None:
        """対の回帰ガード: 後続が非 terminal なら active のまま（除外しすぎない）。"""
        body = (
            "- Resume From: gdd-test-driven-development\n"
            "- Next Action:\n- Next Action: gdd-implementation-gating\n"
        )
        self.assertFalse(self.binding._is_terminal_state(body))

    def test_value_less_line_only_is_not_terminal(self) -> None:
        """AC-3(c) 同型: 空値行しか無ければ terminal 判定に使える値が無い。"""
        body = "- Resume From: gdd-test-driven-development\n- Next Action:\n"
        self.assertFalse(self.binding._is_terminal_state(body))


class TelemetryErrorLogRowCountTests(unittest.TestCase):
    """PR #35 独立セルフレビュー（M10 SURVIVED）: `_count_error_log_entries` の
    header 減算（`len(rows) - 1`）に安全網が無く、off-by-one 変異が生き残っていた。

    helper 抽出そのものは挙動不変だったが、抽出した関数に直接のテストが無いため
    「複雑度を下げるためだけの、安全網なしのリファクタ」になっていた。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.telemetry = _load_module(TELEMETRY_SCRIPT, "collect_gdd_telemetry_errorlog")

    def test_header_row_is_subtracted(self) -> None:
        worklog = (
            "## Error Log\n"
            "| when | what |\n"
            "|---|---|\n"
            "| t1 | a |\n"
            "| t2 | b |\n"
        )
        self.assertEqual(self.telemetry._count_error_log_entries(worklog), 2)

    def test_header_only_table_counts_zero(self) -> None:
        worklog = "## Error Log\n| when | what |\n|---|---|\n"
        self.assertEqual(self.telemetry._count_error_log_entries(worklog), 0)

    def test_absent_section_counts_zero(self) -> None:
        self.assertEqual(self.telemetry._count_error_log_entries("## Other\n"), 0)


class LoopReaderBulletSetMatchesTheSchemaRecordTests(unittest.TestCase):
    """PR #35 独立セルフレビュー（M14 SURVIVED）: `line_prefix_exceptions` が
    `accepts: ["-","*","+"]` と記録しているのに、実装を叩く姉妹テストが `*` だけで、
    `+` / `-` は記録と実装が乖離しても検出できなかった。

    記録された 3 種すべてを実装に対して検証する。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.parse_field = staticmethod(_load_loop_parse_field())

    def test_every_recorded_bullet_is_actually_accepted(self) -> None:
        import json

        schema = json.loads((PLUGIN_ROOT / "references" / "state-schema.json").read_text(encoding="utf-8"))
        entry = next(
            e for e in schema["canonical_line_form"]["line_prefix_exceptions"]
            if e["reader"] == "scripts/setup-gdd-loop.sh:normalize_line"
        )
        for bullet in entry["accepts"]:
            with self.subTest(bullet=bullet):
                self.assertEqual(
                    self.parse_field(f"{bullet} Next Action: done\n", ["Next Action"]),
                    "done",
                    f"schema は {bullet!r} を受理形として記録しているが実装が読まない",
                )


class Sm31MergeGateReachabilityTests(unittest.TestCase):
    """PR #35 独立セルフレビュー（security lane / high 1）: SM3-1 の帰結が
    **merge gate の起動可否**まで及ぶことを固定する。

    `lib/self-review-evidence.sh:gdd_pre_push_resolve_steering` の union フォールバックは
    `Resume From: done` / `Next Action: done` / `Resume From: blocked` / `Next Action: blocked`
    しか候補にしない。
    R-1 で terminal 値が読めるようになると、除外された値が `cancelled` の場合は
    union も救済せず `terminal-only` に落ち、`run-merge-gate-hook.sh` は、対象 PR を記録した
    steering が無ければ `unresolved-steering-on-merge` で素通りする。

    遮蔽行の無い正しい `Resume From: cancelled` は本変更の前から同じく素通りするので、
    R-1 が変えるのは「書きかけ行があると偶然 block されていた」ケースのみ。
    ここでは**どの値がどちらに落ちるか**を characterization として固定する。
    """

    SELF_REVIEW_LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "self-review-evidence.sh"

    def _resolve(self, resume_from: str) -> str:
        """遮蔽行 + `resume_from` を持つ state.md での解決結果 `status/reason`。"""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".steering" / "20260101-x").mkdir(parents=True)
            (root / ".steering" / "20260101-x" / "state.md").write_text(
                "- Started At: 2026-01-01T00:00:00Z\n"
                "- Human Check Status: approved\n"
                "- Route In Progress: none\n"
                "- Resume From:\n"
                f"- Resume From: {resume_from}\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q", "."], cwd=root, check=True, capture_output=True)
            script = (
                f'source "{DETECT_STEERING_LIB}"; source "{self.SELF_REVIEW_LIB}"; '
                f'gdd_pre_push_resolve_steering "{root}" >/dev/null 2>&1; '
                'printf "%s/%s" "$GDD_PP_STEERING_STATUS" "$GDD_PP_STEERING_REASON"'
            )
            proc = subprocess.run(
                ["bash", "-c", script], cwd=root, capture_output=True, text=True
            )
        return proc.stdout.strip()

    def test_done_is_rescued_by_the_union_fallback(self) -> None:
        """`done` は union が拾うので merge gate は起動する（素通りしない）。"""
        self.assertEqual(self._resolve("done"), "found/")

    def test_cancelled_falls_through_to_terminal_only(self) -> None:
        """`cancelled` は union の条件に無いため `terminal-only`（merge gate は対象 PR の照合だけ）。

        本変更が到達可能にする形。遮蔽行の無い同値の state.md は変更前から同じ結果。
        """
        self.assertEqual(self._resolve("cancelled"), "none/terminal-only")

    def test_blocked_resume_from_is_rescued(self) -> None:
        """`Resume From: blocked` は union が明示的に拾う（`Next Action: blocked` も同じく拾う）。"""
        self.assertEqual(self._resolve("blocked"), "found/")


class PythonReadersSurviveMalformedInputTests(unittest.TestCase):
    """PR #35 独立セルフレビュー round 2（H-1）: python 側の reader が不正 UTF-8 で
    落ちて **検査そのものを無効化**しないことを固定する。

    `UnicodeDecodeError` は `ValueError` 系で `except OSError` に捕まらない。
    `validate-steering-write.py` は hook として exit 1（non-blocking error）で落ち、
    Tier 1 field 検査が丸ごと効かなくなる = **不正な書き込みが通る**（PreToolUse の
    exit 2 だけが deny で、exit 1 は素通り）。`gdd_task_binding.py` は
    `references/state-machine.md` が「task identity の正本」と宣言する registry を
    沈黙のうちに機能停止させる。

    round 1 の CHANGELOG は「汎用 reader 側だけ無防備だった」と書いていたが、
    実際には python 側 2 本にも同じ穴があった（記述を是正済み）。
    """

    VALIDATE_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
    BAD_BYTES = b"\xc3\x28\n"

    def _steering_with_bad_bytes(self, root: Path) -> Path:
        steering = root / ".steering" / "20260101-a"
        steering.mkdir(parents=True)
        state = steering / "state.md"
        # `Started At` を**入れない**: 書き込み内容が canonical field を更新するのに
        # `Started At` が無い形は Tier 1 検査の deny 条件。既存ファイル側にあると
        # 推移的に満たされて allow になり、deny 経路を通らなくなる。
        state.write_bytes(
            b"- Resume From: gdd-test-driven-development\n"
            b"- Human Check Status: approved\n"
            b"- Route In Progress: none\n"
            b"- Note: " + self.BAD_BYTES
        )
        return state

    def test_task_binding_upsert_survives_malformed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state = self._steering_with_bad_bytes(root)
            proc = subprocess.run(
                [sys.executable, str(TASK_BINDING), "upsert-from-state",
                 "--repo-root", str(root), "--state", str(state)],
                capture_output=True, text=True,
            )
        self.assertEqual(proc.returncode, 0, f"stderr={proc.stderr[-400:]}")
        self.assertNotIn("UnicodeDecodeError", proc.stderr)

    def test_write_hook_still_denies_when_existing_file_has_bad_bytes(self) -> None:
        """既存 state.md に不正バイトがあっても書き込み検査が deny を返す。

        修正前は traceback で exit 1 になり、deny が出せず書き込みが通っていた。
        """
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state = self._steering_with_bad_bytes(root)
            payload = json.dumps({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": str(state),
                    # `Started At` を落とした書き込み = Tier 1 検査で deny されるべき形
                    "content": "- Resume From: gdd-test-driven-development\n",
                },
            })
            proc = subprocess.run(
                [sys.executable, str(self.VALIDATE_HOOK)],
                input=payload, capture_output=True, text=True,
            )
        self.assertNotIn("UnicodeDecodeError", proc.stderr)
        self.assertEqual(proc.returncode, 2, "PreToolUse の deny は exit 2")
        # deny payload は stderr に出る（Claude Code の PreToolUse 契約）。
        self.assertIn('"permissionDecision": "deny"', proc.stderr)


class ValueLessLineNonAppliedContractTests(unittest.TestCase):
    """R-1 を**適用しない**側（`state_field_values`）と、awk の `=` 分岐の trim を固定する。

    どちらも独立レビューの変異注入で SURVIVED した面（low-4 / low-5）。前者は
    「善意の一貫性リファクタ」で無音で反転し、write-once の security boundary
    （PR #31 Finding Q/J）が緩む。後者は `:` 分岐しか横断表が見ていないため、
    `=` 分岐固有の trim が落ちても気付けない。
    """

    def test_state_field_values_keeps_the_value_less_occurrence(self) -> None:
        """`state_field_values` は空値行も 1 出現として返す（R-1 非適用）。

        ここを R-1 適用に変えると `- Origin Session:`（宛先の削除）+
        `- Origin Session: A` が「1 値の書込み」に化け、削除してから別 ID を
        初回値として設定する迂回が通る。
        """
        # `state_fields.py` は同 lib の `tasklist_parse` を **top-level module** として
        # 読む（`from lib.X import` は `sys.modules["lib"]` を固定して scripts/lib を
        # 壊すため。正本: validate-steering-write.py の同名ブロック）。同じ path 前提で読む。
        lib_dir = str(PLUGIN_ROOT / "hooks" / "scripts" / "lib")
        sys.path.insert(0, lib_dir)
        try:
            mod = load_plugin_module("hooks/scripts/lib/state_fields.py")
        finally:
            if lib_dir in sys.path:
                sys.path.remove(lib_dir)
        self.assertEqual(
            mod.state_field_values("- Origin Session: \n- Origin Session: A\n", "Origin Session"),
            ["", "A"],
        )

    def test_awk_equals_branch_trims_before_the_empty_check(self) -> None:
        """awk の `=` 分岐でも「空白のみの値」は空値行として飛ばす。

        横断表（`ValueLessLineCrossImplementationTests`）は telemetry が `=` を
        受理しないため `:` 分岐しか見ておらず、`=` 分岐の trim は無防備だった。
        """
        with tempfile.TemporaryDirectory() as d:
            state = Path(d) / "state.md"
            state.write_text("- Resume From=   \n- Resume From= gdd-pr-review\n", encoding="utf-8")
            script = (
                f'source "{DETECT_STEERING_LIB}"; '
                f'printf "%s" "$(gdd_extract_doc_field "{state}" "Resume From")"'
            )
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        self.assertEqual(proc.stdout, "gdd-pr-review")
