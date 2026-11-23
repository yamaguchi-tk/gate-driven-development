"""Stop hook の state の parse・write と、`.steering/*/state.md` の Resume From への fallback の単体テスト。

`test_stop_hook_unit.py` から分けた。確かめる本体は `hooks/scripts/gdd_stop_hook.py`・`hooks/scripts/lib/state_io.py`・`hooks/scripts/lib/tasklist_parse.py`・`hooks/scripts/lib/constants.py`・`hooks/scripts/lib/errors.py`。
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F811
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F403
from lib.errors import hook_error_log_path

class TestParseWriteState(unittest.TestCase):
    """parse_state / write_state round-trip."""

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "gdd-dev.local.md"
            original = textwrap.dedent("""\
                ---
                active: true
                iteration: 3
                session_id: abc-123
                started_at: 2026-04-08T10:00:00Z
                detected_phase: gdd-brainstorming
                ---

                Resume the workflow.
            """)
            state_file.write_text(original, encoding="utf-8")
            fm, body = parse_state(state_file)
            self.assertEqual(fm["iteration"], "3")
            self.assertEqual(fm["session_id"], "abc-123")
            self.assertEqual(fm["detected_phase"], "gdd-brainstorming")
            self.assertIn("Resume the workflow", body)

            fm["iteration"] = "4"
            fm["detected_phase"] = "gdd-design-gating"
            write_state(state_file, fm, body)

            fm2, body2 = parse_state(state_file)
            self.assertEqual(fm2["iteration"], "4")
            self.assertEqual(fm2["detected_phase"], "gdd-design-gating")
            self.assertIn("Resume the workflow", body2)

    def test_write_state_neutralizes_embedded_newlines_in_values(self):
        # 独立レビュー round 7 High/blocking 指摘（H-1）: `write_state()` は値を
        # `f"{key}: {value}"` でそのまま書き出すため、値に改行が混ざっていると
        # 別の frontmatter 行として再パースされ、後勝ちで既存 key（`active` 等）
        # を上書きできた（guard bypass / fail-open）。`_detect_phase()` 側の
        # marker 検証（H-1 本体の修正）に加えて、`lib/handoff_summary.py` が
        # 既に行っている改行の中和（`"\n"` -> `" | "`）と対称に、
        # `write_state()` 自体でも値の改行を無害化し、他の書き込み経路からの
        # 同型再発を防ぐ（fail-closed の多層防御）。
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.md"
            fm = {
                "active": "true",
                "iteration": "1",
                "detected_phase": "gdd-brainstorming\nactive: false",
            }
            write_state(state_file, fm, "body")
            fm2, _ = parse_state(state_file)
            self.assertEqual(fm2["active"], "true")
            self.assertEqual(fm2["detected_phase"], "gdd-brainstorming | active: false")
            self.assertEqual(set(fm2), {"active", "iteration", "detected_phase"})

    def test_write_state_neutralizes_non_lf_line_separators_too(self):
        # 独立レビュー round 8 指摘（L-1）: `parse_state()` は `str.splitlines()`
        # で行分割するため `\n` 以外（`\r`・U+2028 等）でも行が割れるが、旧実装は
        # `value.replace("\n", ...)` で `\n` しか中和しておらず reader/writer の
        # 受理集合が非対称だった（round 7 H-1 と同型の注入が `\r` でも成立しうる）。
        # 独立レビュー round 9 指摘（L-1）: 本テストは `active` の非上書きしか
        # 検証しておらず、値が中和されず生の `\r` のまま書かれても
        # （`parse_state()` は `\n` 分割のみのため）このテストは偽陽性で
        # 通ってしまう。`test_write_state_neutralizes_embedded_newlines_in_values`
        # と対称に、中和後の値と key 集合も検証する。
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.md"
            fm = {
                "active": "true",
                "iteration": "1",
                "detected_phase": "gdd-brainstorming\ractive: false",
            }
            write_state(state_file, fm, "body")
            fm2, _ = parse_state(state_file)
            self.assertEqual(fm2["active"], "true")
            self.assertEqual(fm2["detected_phase"], "gdd-brainstorming | active: false")
            self.assertEqual(set(fm2), {"active", "iteration", "detected_phase"})

    def test_write_state_value_of_exactly_three_hyphens_does_not_truncate_frontmatter(self):
        # 独立レビュー round 9 High/blocking 指摘（H-1）: `parse_state()` は
        # frontmatter の終端を「行」ではなく部分文字列 `"---\n"` の出現位置で
        # 決めていた（`text.split("---\n", 2)`）。値が `"---"` になる
        # frontmatter 行（例: `detected_phase: ---`）を書くと、その行自体が
        # 部分文字列として `"---\n"` を含むため、本来の終端行より前でそこを
        # frontmatter 終端と誤認し、それより後ろの key（`recommended_model`・
        # `hitl_lint_blocks` 等、`enforce_consecutive_block_ceiling()` や HITL
        # lint 予算が読む key を含む）が丸ごと消えて body へ漏れていた
        # （round 7 H-1 と同じ入口。`_detect_phase()` の文字集合検証
        # `[a-z0-9-]+` は `-`/`---` 等ハイフンのみの値も受理してしまうため
        # 素通りする）。frontmatter の終端は「内容が厳密に `---` である行」で
        # 判定するよう `parse_state()` を修正する。
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.md"
            fm = {
                "active": "true",
                "iteration": "1",
                "detected_phase": "---",
                "recommended_model": "sonnet",
                "hitl_lint_blocks": "3",
            }
            write_state(state_file, fm, "body text")
            fm2, body2 = parse_state(state_file)
            self.assertEqual(fm2["recommended_model"], "sonnet")
            self.assertEqual(fm2["hitl_lint_blocks"], "3")
            self.assertNotIn("---", body2)

    def test_write_state_non_str_value_does_not_crash_sanitizer(self):
        # 独立レビュー round 9 指摘（L-2）: `_sanitize_frontmatter_value()` は
        # round 8（A-2）で non-str 値による `AttributeError`（guard クラッシュ
        # → fail-open）を防ぐため `str(value)` を挟んだが、それを固定する
        # テストが無く、以後の変更で退行しても検知できなかった。int 値でも
        # 例外にならず、文字列化されて書き戻せることをピン留めする。
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.md"
            fm = {"active": "true", "iteration": 3}
            write_state(state_file, fm, "body")
            fm2, _ = parse_state(state_file)
            self.assertEqual(fm2["iteration"], "3")

    def test_parse_invalid_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "bad.md"
            state_file.write_text("no frontmatter here", encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_state(state_file)

    def test_write_preserves_key_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.md"
            fm = {
                "detected_phase": "gdd-brainstorming",
                "active": "true",
                "session_id": "s1",
                "iteration": "1",
                "started_at": "2026-04-08",
            }
            write_state(state_file, fm, "body")
            lines = state_file.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[1], "active: true")
            self.assertEqual(lines[2], "iteration: 1")
            self.assertEqual(lines[3], "session_id: s1")
            self.assertEqual(lines[4], "started_at: 2026-04-08")

    def test_active_empty_session_id_is_invalid(self):
        self.assertTrue(is_invalid_active_local_session({"active": "true", "session_id": ""}))
        self.assertTrue(is_invalid_active_local_session({"active": "true"}))
        self.assertFalse(is_invalid_active_local_session({"active": "true", "session_id": "abc-123"}))
        self.assertFalse(is_invalid_active_local_session({"active": "false", "session_id": ""}))

    def test_round_trip_is_idempotent_across_repeated_cycles(self):
        """AC-E8-1: f(x) = parse_state(write_state(fm, body)) must satisfy
        f(f(x)) == f(x) (idempotent normalization, not raw identity)."""
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "gdd-dev.local.md"
            original = textwrap.dedent("""\
                ---
                active: true
                iteration: 1
                session_id: abc-123
                started_at: 2026-04-08T10:00:00Z
                ---

                Resume the workflow.
            """)
            state_file.write_text(original, encoding="utf-8")
            fm, body = parse_state(state_file)

            bodies = []
            for _ in range(3):
                write_state(state_file, fm, body)
                fm, body = parse_state(state_file)
                bodies.append(body)

            self.assertEqual(
                bodies[0], bodies[1],
                f"body must stabilize after the first write/parse cycle, got {bodies!r}",
            )
            self.assertEqual(bodies[1], bodies[2])
            self.assertFalse(
                bodies[-1].startswith("\n"),
                f"leading newline must not accumulate across cycles: {bodies[-1]!r}",
            )

    def test_pre_accumulated_leading_newlines_converge_after_one_write(self):
        """AC-E8-2: a .local.md with already-accumulated leading newlines in body
        converges to the canonical single-blank-line form after one write_state call."""
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "gdd-dev.local.md"
            accumulated = (
                "---\n"
                "active: true\n"
                "iteration: 5\n"
                "session_id: abc-123\n"
                "started_at: 2026-04-08T10:00:00Z\n"
                "---\n"
                + ("\n" * 5)
                + "Resume the workflow.\n"
            )
            state_file.write_text(accumulated, encoding="utf-8")

            fm, body = parse_state(state_file)
            self.assertFalse(
                body.startswith("\n"),
                f"parse_state must strip pre-accumulated leading newlines: {body!r}",
            )

            write_state(state_file, fm, body)
            raw_after = state_file.read_text(encoding="utf-8")
            content_after_frontmatter = raw_after.split("---\n", 2)[2]
            self.assertEqual(
                content_after_frontmatter,
                "\nResume the workflow.\n",
                f"on-disk body must converge to canonical single-blank-line form: {content_after_frontmatter!r}",
            )


class TestLocalStateParseFailOpen(unittest.TestCase):
    """AC-E8-3: a malformed .claude/gdd-dev.local.md (parse_state failure,
    e.g. missing frontmatter start) must not block Stop. It must suppress
    (allow stop) and log to .gdd/hook-errors.log instead."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".claude").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_malformed_state(self) -> Path:
        state_file = self.root / ".claude" / "gdd-dev.local.md"
        state_file.write_text(
            "active: true\nno frontmatter delimiter here\n", encoding="utf-8"
        )
        return state_file

    def test_malformed_local_state_does_not_block_stop(self):
        self._write_malformed_state()
        rc, stdout, stderr = _run_hook(self.root)
        self.assertEqual(rc, 0, f"malformed .local.md must allow stop, stderr={stderr!r}")
        self.assertNotIn(
            '"decision": "block"', stdout,
            f"malformed .local.md must not emit decision:block, stdout={stdout!r}",
        )
        self.assertIn(
            "parse_state", stderr,
            f"expected a stderr warning naming the parse_state source, stderr={stderr!r}",
        )

    def test_malformed_local_state_logs_to_hook_errors(self):
        self._write_malformed_state()
        log_path = hook_error_log_path(self.root)
        _run_hook(self.root)
        self.assertTrue(
            log_path.exists(),
            "suppress_hook_integrity_failure must append to .gdd/hook-errors.log",
        )
        entries = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(
            any(e.get("source") == "parse_state" for e in entries),
            f"expected a parse_state entry in hook-errors.log, got {entries!r}",
        )


def _check_steering_fallback(project_root: Path) -> str | None:
    """Fallback 3 の判定。走査は **shipped 実装**へ委譲する。

    旧実装はここに `RESUME_FROM_PATTERN` の複製と独自の走査ループを持っていた。
    複製は merge-base では shipped と同一だったが、`Resume From` のアンカーを
    他 reader に揃えて狭めた時点で乖離し、この test 群が shipped コードを
    一切検証しなくなっていた（shipped が `*` bullet 受理へ退行しても緑のまま。
    独立レビュー medium-1）。テスト側に 2 つ目の実装を置かない。
    """
    import gdd_stop_hook

    steering_dir = project_root / ".steering"
    if not steering_dir.is_dir():
        return None
    for d in sorted(steering_dir.iterdir(), reverse=True):
        sf = d / "state.md"
        if sf.is_file():
            return gdd_stop_hook.resume_from_value(sf.read_text(encoding="utf-8")) or None
    return None


class TestSteeringStateFallback(unittest.TestCase):
    """Fallback 3: "Resume From: <stop-reason>" in .steering/*/state.md.

    The brainstorming skill always writes "Resume From: human-check-waiting"
    (colon-separated, markdown list item format) when it reaches the human-check gate.
    This fallback catches the case where neither <gdd-stop> in assistant text nor
    detected_phase in gdd-dev.local.md has been updated, but the steering state file
    clearly says the workflow has reached human-check-waiting.
    """

    def _make_steering(self, tmp: str, dirname: str, resume_from: str, fmt: str = "colon") -> Path:
        """fmt='colon'    writes '- Resume From: value'           (plain colon format).
           fmt='equals'   writes 'Resume From=value'              (old equals format).
           fmt='backtick' writes '- `Resume From=value`'          (actual state.md format written by requirements-gating)."""
        steering = Path(tmp) / ".steering" / dirname
        steering.mkdir(parents=True)
        state = steering / "state.md"
        if fmt == "equals":
            line = f"Resume From={resume_from}"
        elif fmt == "backtick":
            line = f"- `Resume From={resume_from}`"
        else:
            line = f"- Resume From: {resume_from}"
        state.write_text(
            f"# State\n\n## Gate Status\n{line}\n",
            encoding="utf-8",
        )
        return state

    def test_detects_human_check_waiting_colon_format(self):
        """'- Resume From: human-check-waiting' (real brainstorming output) triggers stop."""
        with tempfile.TemporaryDirectory() as tmp:
            self._make_steering(tmp, "20260410-mytask", "human-check-waiting", fmt="colon")
            rf = _check_steering_fallback(Path(tmp))
            self.assertIsNotNone(rf)
            self.assertIn(rf, ALLOWED_STOP_REASONS)

    def test_detects_human_check_waiting_equals_format(self):
        """'Resume From=human-check-waiting' (legacy equals format) also triggers stop."""
        with tempfile.TemporaryDirectory() as tmp:
            self._make_steering(tmp, "20260410-mytask", "human-check-waiting", fmt="equals")
            rf = _check_steering_fallback(Path(tmp))
            self.assertIsNotNone(rf)
            self.assertIn(rf, ALLOWED_STOP_REASONS)

    def test_detects_human_check_waiting_backtick_format(self):
        """'- `Resume From=human-check-waiting`' (actual format from gdd-requirements-gating) triggers stop."""
        with tempfile.TemporaryDirectory() as tmp:
            self._make_steering(tmp, "20260410-mytask", "human-check-waiting", fmt="backtick")
            rf = _check_steering_fallback(Path(tmp))
            self.assertIsNotNone(rf, "Backtick-wrapped Resume From should be detected")
            self.assertIn(rf, ALLOWED_STOP_REASONS)

    def test_detects_done_in_steering(self):
        """Resume From: done in steering state also triggers stop."""
        with tempfile.TemporaryDirectory() as tmp:
            self._make_steering(tmp, "20260410-mytask", "done")
            rf = _check_steering_fallback(Path(tmp))
            self.assertIsNotNone(rf)
            self.assertIn(rf, ALLOWED_STOP_REASONS)

    def test_does_not_trigger_for_non_stop_resume_from(self):
        """Resume From: gdd-design-gating should NOT trigger stop."""
        with tempfile.TemporaryDirectory() as tmp:
            self._make_steering(tmp, "20260410-mytask", "gdd-design-gating")
            rf = _check_steering_fallback(Path(tmp))
            self.assertIsNotNone(rf)
            self.assertNotIn(rf, ALLOWED_STOP_REASONS)

    def test_real_state_md_format(self):
        """Regression: match the exact format written by gdd-brainstorming skill (plain colon)."""
        with tempfile.TemporaryDirectory() as tmp:
            steering = Path(tmp) / ".steering" / "20260410-cve-task"
            steering.mkdir(parents=True)
            # Exact excerpt from a real state.md
            (steering / "state.md").write_text(
                textwrap.dedent("""\
                    # State

                    ## Gate Status

                    - Requirements Review Status: approved
                    - Human Check Status: pending
                    - Resume From: human-check-waiting
                    - Operation Level: standard
                """),
                encoding="utf-8",
            )
            rf = _check_steering_fallback(Path(tmp))
            self.assertIsNotNone(rf)
            self.assertIn(rf, ALLOWED_STOP_REASONS)

    def test_real_state_md_backtick_format(self):
        """Regression: match the backtick format actually written by gdd-requirements-gating skill.

        The actual format observed in production state.md:
          - `Resume From=human-check-waiting`
        """
        with tempfile.TemporaryDirectory() as tmp:
            steering = Path(tmp) / ".steering" / "20260411-example-remote-task"
            steering.mkdir(parents=True)
            # Exact excerpt from the real B-run state.md (2026-04-11)
            (steering / "state.md").write_text(
                textwrap.dedent("""\
                    # State: Remote MCP Server for AWS Resources

                    ## Gate Status

                    - `Requirements Review Status=approved | evidence: requirements-gating-20260411 | updated_by: gdd-requirements-gating | updated_at: 2026-04-11`
                    - `Planning Reviewer Selection=gdd-planning-reviewer: selected (reason: standardタスク、requirements phaseは常時必須) | updated_by: gdd-requirements-gating | updated_at: 2026-04-11`
                    - `Design Review Status=pending | evidence: none | updated_by: gdd-requirements-gating | updated_at: 2026-04-11`
                    - `Human Check Status=pending | evidence: none | updated_by: gdd-requirements-gating | updated_at: 2026-04-11`
                    - `Resume From=human-check-waiting`
                    - `Operation Level=standard`
                    - `Task Size=standard`
                """),
                encoding="utf-8",
            )
            rf = _check_steering_fallback(Path(tmp))
            self.assertIsNotNone(rf, "Backtick-wrapped Resume From in real state.md should be detected")
            self.assertIn(rf, ALLOWED_STOP_REASONS)


if __name__ == "__main__":
    unittest.main()
