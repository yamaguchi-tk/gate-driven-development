"""区切りで手動 /compact の 1 行を systemMessage で提案する契約。

提案は Stop hook の出力に `systemMessage` として足すだけで、`decision` / `reason` /
終了コードには触れない。区切りは次の 4 つに閉じる（これ以外では何も出さない）。

1. `Human Check Status=approved` かつ `Next Action=gdd-design-gating`（要件の承認）
2. 設計の承認後（`Design Review Status=approved` かつ `Human Check Status=approved`）に
   `Next Action` が task-breakdown / TDD / subagent-driven-implementation のいずれか
3. state.md に `PR URL`（`/pull/<番号>`）が記録されている
4. tasklist.md の `## Current Task` 節の `Gate Rounds` が 3（`## Execution Plan` の
   `- Gate Batch <N>: T-1, T-2, T-3` に入る task は、batch で 1 つの区切りにまとめる）

Stop hook 本体が active・runtime・session・transcript の guard を通った停止（本体が
`compact_suggestion.mark_eligible()` を呼んだ停止）でだけ判定し、同じ steering の同じ区切りは
1 回だけ出す。本体が guard で黙って抜ける停止（別セッション・別 runtime・transcript の無い停止）
には出さず、1 回分の記録も使わない。
PR マージ後の「新しいセッションで始めて」は対象外（state.md に merge を記録する field が無い）。
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _stop_hook_test_base import (  # noqa: E402
    _make_transcript_jsonl,
    _run_hook,
    _write_binding,
    _write_state_file,
    _write_steering,
)
from lib.compact_suggestion import detect, merge_into_output  # noqa: E402

SLUG = "20260912-compact-test"
RECORD = Path(".claude") / "gdd-compact-suggestions.json"
POST_MERGE_MARKER = Path(".claude") / "gdd-post-merge-continuation.json"

LINE_1 = (
    f"/compact 要件は承認済み。次は gdd-design-gating。正本は .steering/{SLUG}/ の "
    "requirements.md と state.md。残すもの：承認時にユーザーが示した判断・条件。"
    "要件を詰めた会話の経緯は捨ててよい"
)
LINE_2 = (
    "/compact 設計は承認済み。次は task-breakdown と実装。正本は design.md・tasklist.md・"
    "state.md。残すもの：Current Task、Next Action、承認時の条件。設計レビューの往復は捨ててよい"
)
LINE_3 = (
    "/compact PR #42 を作成済み。以後はレビュー対応だけ。残すもの：PR 番号、ブランチ、"
    "最後に通した回帰テストと独立レビューの SHA。実装の経緯は捨ててよい"
)
LINE_4 = (
    "/compact impl-gate Round 3 の途中。残すもの：未解決 finding の ID と場所"
    "（file:function）、試した修正とその結果、Gate Rounds。解決済み finding のやり取りは捨ててよい"
)


def _state(
    *,
    requirements: str = "approved",
    design: str = "pending",
    human_check: str = "approved",
    next_action: str = "gdd-design-gating",
    extra: str = "",
) -> str:
    return (
        "# State\n\n## Gate Status\n"
        f"- Requirements Review Status: {requirements} | evidence: r-1\n"
        f"- Design Review Status: {design} | evidence: d-1\n"
        f"- Human Check Status: {human_check} | evidence: hc-1\n"
        f"- Next Action: {next_action}\n"
        "- Route In Progress: none\n"
        f"{extra}"
    )


STATE_1 = _state()
STATE_NONE = _state(human_check="pending", next_action="human-check-waiting")
STATE_BUILD = _state(design="approved", next_action="gdd-implementation-gating")
STATE_3 = _state(
    design="approved",
    next_action="gdd-completion-check",
    extra="- PR URL: https://github.com/o/r/pull/42\n",
)


def _tasklist(*, next_action: str = "gdd-implementation-gating", current: str = "- なし\n") -> str:
    return (
        "# Tasklist\n\n## Current Task\n"
        f"{current}\n"
        "## Pending Tasks\n- なし\n\n"
        "## Completed Tasks\n- なし\n\n"
        "## Review Status\n"
        f"- Next Action: {next_action}\n"
    )


def _keys(state: str, tasklist: str = "") -> list[str]:
    return [key for key, _ in detect(state, tasklist, SLUG)]


class DetectTests(unittest.TestCase):
    """区切りの判定（純関数）。"""

    def test_boundary_1_requirements_approved(self):
        self.assertEqual(detect(STATE_1, "", SLUG), [("req_approved", LINE_1)])

    def test_boundary_1_requires_human_check_approved(self):
        self.assertEqual(_keys(_state(human_check="pending")), [])

    def test_boundary_2_each_implementation_phase(self):
        for next_action in (
            "gdd-task-breakdown",
            "gdd-test-driven-development",
            "gdd-subagent-driven-implementation",
        ):
            with self.subTest(next_action=next_action):
                state = _state(design="approved", next_action="gdd-design-gating")
                self.assertEqual(
                    detect(state, _tasklist(next_action=next_action), SLUG),
                    [("impl_started", LINE_2)],
                )

    def test_boundary_2_reads_state_before_tasklist_exists(self):
        state = _state(design="approved", next_action="gdd-task-breakdown")
        self.assertEqual(_keys(state), ["impl_started"])

    def test_boundary_2_requires_design_approved(self):
        state = _state(design="in_review", next_action="gdd-task-breakdown")
        self.assertEqual(_keys(state, _tasklist(next_action="gdd-task-breakdown")), [])

    def test_boundary_2_requires_requirements_approved(self):
        """設計承認後に要件を再オープンした状態（`gdd-requirements-amendment`）では、

        `Design Review Status` / `Human Check Status` が直前の `approved` のまま
        残っていても、`Requirements Review Status` が非承認なら routing source は
        まだ tasklist.md に移っていない（references/state-machine.md:204 の 3 条件）。
        この状態で tasklist.md に古い `Next Action=gdd-task-breakdown` が残っていても
        `impl_started` を出してはいけない。
        """
        state = _state(requirements="pending", design="approved", next_action="human-check-waiting")
        self.assertEqual(_keys(state, _tasklist(next_action="gdd-task-breakdown")), [])

    def test_boundary_2_requires_requirements_approved_when_state_has_no_next_action(self):
        """state.md に `Next Action` 行が無いと、`Next Action` を持たない設計承認直後の
        状態（要件は未承認のまま）でも、旧実装は tasklist.md の古い
        `Next Action=gdd-task-breakdown` へ fallback して誤発火していた。

        `references/state-machine.md:204` の 3 条件（Requirements / Design /
        Human Check がすべて approved）が揃うまで、tasklist.md は routing source
        にならない。state.md に `Next Action` が無い場合は「まだ揃っていない」の
        つもりであり、tasklist.md を見に行ってはいけない。
        """
        state = (
            "# State\n\n## Gate Status\n"
            "- Requirements Review Status: pending | evidence: r-1\n"
            "- Design Review Status: approved | evidence: d-1\n"
            "- Human Check Status: approved | evidence: hc-1\n"
            "- Route In Progress: none\n"
        )
        self.assertEqual(_keys(state, _tasklist(next_action="gdd-task-breakdown")), [])

    def test_boundary_2_not_after_implementation(self):
        self.assertEqual(_keys(STATE_BUILD, _tasklist()), [])

    def test_boundary_3_pr_url(self):
        self.assertEqual(detect(STATE_3, _tasklist(), SLUG), [("pr_created", LINE_3)])

    def test_boundary_3_requires_pull_number(self):
        state = _state(design="approved", next_action="done", extra="- PR URL: 未作成\n")
        self.assertEqual(_keys(state, _tasklist(next_action="done")), [])

    def test_boundary_4_gate_rounds_3(self):
        current = "- **T-8 版数を上げる**\n- Gate Rounds: 3（R1 / R2 / R3）\n"
        self.assertEqual(
            detect(STATE_BUILD, _tasklist(current=current), SLUG),
            [("gate_rounds_3:T-8", LINE_4)],
        )

    def test_boundary_4_other_round_counts(self):
        for rounds in ("1", "2", "4"):
            with self.subTest(rounds=rounds):
                current = f"- T-8 x\n- Gate Rounds: {rounds}\n"
                self.assertEqual(_keys(STATE_BUILD, _tasklist(current=current)), [])

    def test_boundary_4_only_in_current_task_section(self):
        tasklist = _tasklist() + "\n## Completed Tasks Notes\n- Gate Rounds: 3\n"
        self.assertEqual(_keys(STATE_BUILD, tasklist), [])

    def test_boundaries_3_and_4_both_reported_in_order(self):
        current = "- T-2 x\n- Gate Rounds: 3\n"
        self.assertEqual(
            _keys(STATE_3, _tasklist(current=current)), ["pr_created", "gate_rounds_3:T-2"]
        )

    def test_boundary_4_pairs_gate_rounds_with_its_own_task_in_parallel_batch(self):
        """並列 batch では `## Current Task` に複数 task が並ぶ（T-1 は Round 1、
        T-2 が Round 3）。節全体から最初の `Gate Rounds` だけを見ると T-1 の `1` で
        止まり、T-2 の Round 3 を取りこぼす。task ごとのブロックで見る必要がある。
        """
        current = "- T-1 a\n- Gate Rounds: 1\n- T-2 b\n- Gate Rounds: 3\n"
        self.assertEqual(_keys(STATE_BUILD, _tasklist(current=current)), ["gate_rounds_3:T-2"])

    def test_boundary_4_does_not_misattribute_gate_rounds_to_wrong_task(self):
        """T-1 に `Gate Rounds` が無く T-2 が Round 3 の場合、節全体から最初の
        Task ID だけを見ると T-1 に誤記録する（`gate_rounds_3:T-1`）。実際に
        Round 3 なのは T-2 なので、記録キーも T-2 でなければならない。
        """
        current = "- T-1 a\n- T-2 b\n- Gate Rounds: 3\n"
        self.assertEqual(_keys(STATE_BUILD, _tasklist(current=current)), ["gate_rounds_3:T-2"])

    def test_boundary_4_recognizes_canonical_task_heading(self):
        """task-breakdown-steps.md の正準見出しは `### Task: T-1 <name>`（箇条書き
        ではなく見出し）。この形式で書かれた単一 task も、互換の箇条書き形式と
        同じく Gate Rounds 3 で拾えなければならない。
        """
        current = "### Task: T-1 canonical task\n- Gate Rounds: 3\n"
        self.assertEqual(_keys(STATE_BUILD, _tasklist(current=current)), ["gate_rounds_3:T-1"])

    def test_boundary_4_pairs_gate_rounds_with_canonical_heading_in_parallel_batch(self):
        """正準見出しの並列 batch（T-1=Round1・T-2=Round3）でも、箇条書き形式と
        同じくブロック単位で対応付ける。節全体から最初の値だけを見ると T-1 の
        `1` で止まり、T-2 の Round 3 を取りこぼす。
        """
        current = "### Task: T-1 a\n- Gate Rounds: 1\n### Task: T-2 b\n- Gate Rounds: 3\n"
        self.assertEqual(_keys(STATE_BUILD, _tasklist(current=current)), ["gate_rounds_3:T-2"])

    def test_boundary_4_recognizes_shared_parser_compatible_headings(self):
        """tasklist_parse.task_name() が受理する既存形式でも区切り④を検出する。"""
        for heading in ("### Task 1: T-1 legacy heading", "- Task: T-1 legacy list"):
            with self.subTest(heading=heading):
                current = f"{heading}\n- Gate Rounds: 3\n"
                self.assertEqual(
                    _keys(STATE_BUILD, _tasklist(current=current)), ["gate_rounds_3:T-1"]
                )

    def test_boundary_4_pairs_shared_parser_headings_in_parallel_batch(self):
        """共有パーサーの既存形式でも Gate Rounds を同じ task の ID と組にする。"""
        for template in ("### Task {n}: T-{n} task", "- Task: T-{n} task"):
            with self.subTest(template=template):
                current = (
                    f"{template.format(n=1)}\n- Gate Rounds: 1\n"
                    f"{template.format(n=2)}\n- Gate Rounds: 3\n"
                )
                self.assertEqual(
                    _keys(STATE_BUILD, _tasklist(current=current)), ["gate_rounds_3:T-2"]
                )

    def test_boundary_4_is_one_key_per_gate_batch(self):
        """Gate Batch では batch の全 task に同じだけ `Gate Rounds` を足す
        （`skills/gdd-implementation-gating/SKILL.md` Step 9）。task ごとのキーだと、
        同じ Round 3 の区切りが task の数だけ出る。batch の task は 1 つのキーにまとめる。
        """
        current = "".join(f"### Task: T-{n} task\n- Gate Rounds: 3\n" for n in (2, 1, 3))
        tasklist = _tasklist(current=current).replace(
            "## Pending Tasks", "## Execution Plan\n- Mode: sequential\n- Gate Batch 1: T-1, T-2, T-3\n\n## Pending Tasks"
        )
        self.assertEqual(_keys(STATE_BUILD, tasklist), ["gate_rounds_3:gate-batch-1"])

    def test_boundary_4_keeps_task_keys_outside_gate_batch(self):
        """batch に入らない task と、fence の中の Gate Batch の例は、task ごとのキーのまま。"""
        current = "### Task: T-4 task\n- Gate Rounds: 3\n### Task: T-1 task\n- Gate Rounds: 3\n"
        tasklist = _tasklist(current=current).replace(
            "## Pending Tasks",
            "## Execution Plan\n- Mode: sequential\n```\n- Gate Batch 9: T-1, T-4\n```\n"
            "- Gate Batch 1: T-1, T-2, T-3\n\n## Pending Tasks",
        )
        self.assertEqual(
            _keys(STATE_BUILD, tasklist), ["gate_rounds_3:T-4", "gate_rounds_3:gate-batch-1"]
        )

    def test_boundary_4_reads_only_the_leading_task_id_of_each_gate_batch_item(self):
        """注記の中の task id（`(after T-3)`）を batch の一員に数えない。2 つの Gate Batch の
        行に出る id は、どちらの batch にも数えず task ごとのキーに戻す。
        """
        current = "".join(f"### Task: T-{n} task\n- Gate Rounds: 3\n" for n in (1, 2, 3))
        tasklist = _tasklist(current=current).replace(
            "## Pending Tasks",
            "## Execution Plan\n- Mode: sequential\n- Gate Batch 1: T-1, T-2, T-3\n"
            "- Gate Batch 2: T-4, T-5, T-6 (after T-3)\n- Gate Batch 3: T-2, T-7\n\n## Pending Tasks",
        )
        self.assertEqual(
            _keys(STATE_BUILD, tasklist), ["gate_rounds_3:gate-batch-1", "gate_rounds_3:T-2"]
        )

    def test_boundary_4_ignores_gate_batch_lines_outside_execution_plan(self):
        """`## Execution Plan` 節の外にある `- Gate Batch` の行は読まない。"""
        current = "### Task: T-4 task\n- Gate Rounds: 3\n"
        tasklist = _tasklist(current=current).replace(
            "## Completed Tasks\n- なし\n", "## Completed Tasks\n- なし\n- Gate Batch 9: T-1, T-4\n"
        )
        self.assertEqual(_keys(STATE_BUILD, tasklist), ["gate_rounds_3:T-4"])

    def test_fenced_examples_are_ignored(self):
        state = "# State\n```\n- Human Check Status: approved\n- Next Action: gdd-design-gating\n```\n"
        self.assertEqual(_keys(state), [])

    def test_other_states_emit_nothing(self):
        for next_action in (
            "gdd-requirements-gating",
            "human-check-waiting",
            "gdd-implementation-gating",
            "gdd-completion-check",
            "done",
        ):
            with self.subTest(next_action=next_action):
                state = _state(design="approved", next_action=next_action)
                self.assertEqual(_keys(state, _tasklist(next_action=next_action)), [])

    def test_empty_inputs_emit_nothing(self):
        self.assertEqual(detect("", "", SLUG), [])


class MergeIntoOutputTests(unittest.TestCase):
    """既存の出力へ systemMessage だけを足す。"""

    def test_empty_output_becomes_system_message_only(self):
        merged = merge_into_output("", "S")
        self.assertEqual(json.loads(merged), {"systemMessage": "S"})

    def test_block_payload_keeps_decision_and_reason(self):
        original = {"decision": "block", "reason": "R", "systemMessage": "M"}
        merged = json.loads(merge_into_output(json.dumps(original) + "\n", "S"))
        self.assertEqual(merged, {"decision": "block", "reason": "R", "systemMessage": "M\n\nS"})

    def test_payload_without_system_message(self):
        merged = json.loads(merge_into_output('{"continue": true}\n', "S"))
        self.assertEqual(merged, {"continue": True, "systemMessage": "S"})

    def test_unmergeable_output_is_left_alone(self):
        for output in ("not json\n", '{"a": 1}\n{"b": 2}\n', "[1]\n", '{"systemMessage": 1}\n'):
            with self.subTest(output=output):
                self.assertIsNone(merge_into_output(output, "S"))


class StopHookIntegrationTests(unittest.TestCase):
    """実際の Stop hook を subprocess で走らせ、既存の判定が変わらないことを確かめる。"""

    _NEXT_ACTION = "\n\n## 👤 次にすること\nOK で承認してください"

    def _workspace(self, tmp: str, state: str, tasklist: str = "# Tasklist\n", active: bool = True):
        ws = Path(tmp)
        if active:
            _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
        _write_steering(ws, SLUG, tasklist, state)
        _write_binding(ws, SLUG)
        return ws

    def _continue(self, ws: Path) -> tuple[int, dict]:
        transcript = ws / "transcript.jsonl"
        _make_transcript_jsonl(
            transcript,
            assistant_text="<gdd-phase>gdd-design-gating</gdd-phase>\n設計を進めます。",
            user_text="OK",
        )
        code, out, err = _run_hook(ws, transcript, session_id="test-session")
        self.assertTrue(out.strip(), f"continuation block must be printed. err={err}")
        return code, json.loads(out)

    def _pause(self, ws: Path) -> tuple[int, str]:
        transcript = ws / "transcript.jsonl"
        _make_transcript_jsonl(
            transcript,
            assistant_text='確認をお願いします。<gdd-stop reason="human-check-waiting">' + self._NEXT_ACTION,
        )
        code, out, _ = _run_hook(ws, transcript, session_id="test-session")
        return code, out

    def test_continuation_block_keeps_decision_and_reason(self):
        with tempfile.TemporaryDirectory() as base_tmp, tempfile.TemporaryDirectory() as tmp:
            _, baseline = self._continue(self._workspace(base_tmp, STATE_NONE))
            code, payload = self._continue(self._workspace(tmp, STATE_1))
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], baseline["decision"])
        self.assertEqual(payload["reason"], baseline["reason"])
        self.assertEqual(set(payload), set(baseline))
        self.assertNotIn("/compact", baseline["systemMessage"])
        self.assertTrue(payload["systemMessage"].startswith("[GDD #2]"))
        self.assertIn(LINE_1, payload["systemMessage"].splitlines())

    def test_same_boundary_is_suggested_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_1)
            _, first = self._continue(ws)
            _, second = self._continue(ws)
        self.assertIn(LINE_1, first["systemMessage"].splitlines())
        self.assertNotIn("/compact", second["systemMessage"])
        self.assertEqual(second["decision"], "block")

    def test_gate_batch_round_3_is_suggested_once_through_the_stop_hook(self):
        """Stop hook の入口から、Gate Batch の 3 task が同時に Round 3 になっても提案は 1 回。"""
        current = "".join(f"### Task: T-{n} task\n- Gate Rounds: 3\n" for n in (1, 2, 3))
        tasklist = _tasklist(current=current).replace(
            "## Pending Tasks", "## Execution Plan\n- Mode: sequential\n- Gate Batch 1: T-1, T-2, T-3\n\n## Pending Tasks"
        )
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_NONE, tasklist)
            messages = [self._continue(ws)[1]["systemMessage"] for _ in range(3)]
        self.assertEqual([LINE_4 in m.splitlines() for m in messages], [True, False, False])

    def test_record_is_kept_outside_the_steering(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_1)
            steering = ws / ".steering" / SLUG
            before = {p.name: p.read_bytes() for p in steering.iterdir()}
            self._continue(ws)
            after = {p.name: p.read_bytes() for p in steering.iterdir()}
            record = json.loads((ws / RECORD).read_text(encoding="utf-8"))
        self.assertEqual(before, after)
        self.assertEqual(list(record.values()), [["req_approved"]])

    def test_pause_path_gets_system_message_only(self):
        with tempfile.TemporaryDirectory() as base_tmp, tempfile.TemporaryDirectory() as tmp:
            base_code, base_out = self._pause(self._workspace(base_tmp, STATE_NONE))
            code, out = self._pause(self._workspace(tmp, STATE_3, _tasklist()))
        self.assertEqual((base_code, base_out), (0, ""))
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(set(payload), {"systemMessage"})
        self.assertIn(LINE_3, payload["systemMessage"].splitlines())

    def test_inactive_session_gets_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_1, active=False)
            code, out = self._pause(ws)
        self.assertEqual((code, out), (0, ""))

    def test_other_session_gets_nothing_and_keeps_the_record(self):
        """本体が黙って抜ける停止（別セッション）では提案せず、1 回分の記録も使わない。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_1)
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text="別の会話です。")
            code, out, _ = _run_hook(ws, transcript, session_id="other-session")
            record_left = (ws / RECORD).exists()
            _, owner = self._continue(ws)
        self.assertEqual((code, out), (0, ""))
        self.assertFalse(record_left)
        self.assertIn(LINE_1, owner["systemMessage"].splitlines())

    def test_other_runtime_gets_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_1)
            _write_state_file(
                ws,
                {"active": "true", "session_id": "test-session", "iteration": "1", "workflow_runtime": "cursor"},
            )
            code, out = self._pause(ws)
            record_left = (ws / RECORD).exists()
        self.assertEqual((code, out), (0, ""))
        self.assertFalse(record_left)

    def test_missing_transcript_gets_nothing(self):
        """references/stop-hook-structured-markers.md § Transcript Missing Suppression と揃える。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_1)
            code, out, _ = _run_hook(ws, None, session_id="test-session")
            record_left = (ws / RECORD).exists()
        self.assertEqual((code, out), (0, ""))
        self.assertFalse(record_left)

    def test_corrupted_record_is_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = self._workspace(tmp, STATE_1)
            (ws / RECORD).write_text("{broken", encoding="utf-8")
            _, payload = self._continue(ws)
            record = json.loads((ws / RECORD).read_text(encoding="utf-8"))
        self.assertIn(LINE_1, payload["systemMessage"].splitlines())
        self.assertEqual(list(record.values()), [["req_approved"]])

    def test_suggestion_failure_leaves_the_hook_output_unchanged(self):
        with tempfile.TemporaryDirectory() as base_tmp, tempfile.TemporaryDirectory() as tmp:
            _, baseline = self._continue(self._workspace(base_tmp, STATE_NONE))
            ws = self._workspace(tmp, STATE_1)
            (ws / RECORD).mkdir(parents=True)
            code, payload = self._continue(ws)
        self.assertEqual(code, 0)
        self.assertEqual(payload, baseline)

    def _post_merge(self, tmp: str, assistant_text: str) -> tuple[Path, int, str]:
        ws = Path(tmp)
        marker = ws / POST_MERGE_MARKER
        marker.parent.mkdir(parents=True)
        marker.write_text(
            json.dumps(
                {
                    "pr_url": "https://github.com/o/r/pull/42",
                    "tasklist_path": str(ws / ".steering" / SLUG / "tasklist.md"),
                    "status": "pending_manual_merge",
                }
            ),
            encoding="utf-8",
        )
        transcript = ws / "transcript.jsonl"
        _make_transcript_jsonl(transcript, assistant_text=assistant_text, user_text="mergeした")
        code, out, _ = _run_hook(ws, transcript, session_id="test-session")
        return ws, code, out

    def test_post_merge_verified_adds_nothing(self):
        """PR マージ後は区切りの対象外。post-merge 検証の完了時も何も足さない。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws, code, out = self._post_merge(
                tmp, "マージ後の確認: state.md と tasklist.md を再読込し、残タスクはありません。"
            )
            marker_left = (ws / POST_MERGE_MARKER).exists()
        self.assertFalse(marker_left)
        self.assertEqual((code, out), (0, ""))

    def test_post_merge_pending_block_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws, code, out = self._post_merge(tmp, "了解しました。")
            marker_left = (ws / POST_MERGE_MARKER).exists()
        self.assertTrue(marker_left)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["decision"], "block")
        self.assertNotIn("[gdd:compact]", payload["systemMessage"])


if __name__ == "__main__":
    unittest.main()
