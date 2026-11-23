"""Stop hook の handoff・phase の検出・session start での抽出の単体テスト。

確かめる本体は `hooks/scripts/gdd_stop_hook.py`・`hooks/scripts/lib/constants.py`・`hooks/scripts/run-session-start-hook.sh`。
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F811
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F403

class TestHandoffPattern(unittest.TestCase):
    """HANDOFF_PATTERN regex correctness."""

    def test_matches_standard_handoff(self):
        text = textwrap.dedent("""\
            <!-- Context Handoff: design-gating → task-breakdown -->
            **Handoff:** REST API 採用 | 変更対象: src/api/users.ts | 注意: offset バリデーション

            ## Next section
        """)
        m = HANDOFF_PATTERN.search(text)
        self.assertIsNotNone(m)
        self.assertIn("REST API 採用", m.group(1))

    def test_matches_multiline_handoff(self):
        text = textwrap.dedent("""\
            <!-- Context Handoff: brainstorming → req-gate -->
            **Handoff:** 決定事項1
            - 変更対象: file1.ts
            - 注意: 特になし

            ## Gate Status
        """)
        m = HANDOFF_PATTERN.search(text)
        self.assertIsNotNone(m)
        self.assertIn("決定事項1", m.group(1))
        self.assertIn("file1.ts", m.group(1))

    def test_no_match_without_handoff_marker(self):
        text = "<!-- Context Handoff: a → b -->\nSome random text without Handoff bold marker\n\n"
        m = HANDOFF_PATTERN.search(text)
        self.assertIsNone(m)

    def test_no_match_on_unrelated_comment(self):
        text = "<!-- Some other comment -->\n**Handoff:** text\n\n"
        m = HANDOFF_PATTERN.search(text)
        self.assertIsNone(m)

    def test_stops_at_gdd_stop_tag(self):
        text = textwrap.dedent("""\
            <!-- Context Handoff: impl-gate → completion -->
            **Handoff:** 全タスク完了
            <gdd-stop reason="done">
        """)
        m = HANDOFF_PATTERN.search(text)
        self.assertIsNotNone(m)
        self.assertNotIn("gdd-stop", m.group(1))

    def test_stops_at_next_section(self):
        text = textwrap.dedent("""\
            <!-- Context Handoff: a → b -->
            **Handoff:** 要約

            ## Unrelated section
            This should not be captured.
        """)
        m = HANDOFF_PATTERN.search(text)
        self.assertIsNotNone(m)
        self.assertNotIn("Unrelated", m.group(1))


class TestPersistHandoffSummary(unittest.TestCase):
    """Smart Session Recovery: persist and recover Last Handoff Summary."""

    def test_inserts_after_route_in_progress(self):
        """Inserts after Route In Progress (first matching anchor)."""
        output = textwrap.dedent("""\
            <!-- Context Handoff: design-gating → task-breakdown -->
            **Handoff:** REST API 確定 | 変更: src/api/users.ts
        """)
        result = persist_handoff_summary_to_content(output, SAMPLE_STATE)
        self.assertIn("Last Handoff Summary=", result)
        self.assertIn("REST API 確定", result)
        rip_pos = result.index("Route In Progress=")
        lhs_pos = result.index("Last Handoff Summary=")
        self.assertGreater(lhs_pos, rip_pos)

    def test_updates_existing_handoff(self):
        state_with_existing = SAMPLE_STATE.replace(
            "Approved Direction=REST API でページネーション",
            "Approved Direction=REST API でページネーション\nLast Handoff Summary=古い要約",
        )
        output = textwrap.dedent("""\
            <!-- Context Handoff: impl-gate → completion -->
            **Handoff:** 新しい要約
        """)
        result = persist_handoff_summary_to_content(output, state_with_existing)
        self.assertIn("Last Handoff Summary=**Handoff:** 新しい要約", result)
        self.assertNotIn("古い要約", result)

    def test_no_change_without_handoff(self):
        output = "Some output without any handoff summary."
        result = persist_handoff_summary_to_content(output, SAMPLE_STATE)
        self.assertEqual(result, SAMPLE_STATE)

    def test_multiline_encoded_as_pipe(self):
        output = textwrap.dedent("""\
            <!-- Context Handoff: a → b -->
            **Handoff:** 行1
            行2
            行3

            ## Next
        """)
        result = persist_handoff_summary_to_content(output, SAMPLE_STATE)
        lhs_line = [l for l in result.splitlines() if "Last Handoff Summary=" in l][0]
        self.assertIn(" | ", lhs_line)
        value_part = lhs_line.split("Last Handoff Summary=", 1)[1]
        self.assertNotIn("\n", value_part)

    def test_truncates_at_10_lines(self):
        body_lines = "\n".join(f"- 行{i}" for i in range(15))
        output = f"<!-- Context Handoff: a → b -->\n**Handoff:** {body_lines}\n\n"
        result = persist_handoff_summary_to_content(output, SAMPLE_STATE)
        lhs_value = [
            l for l in result.splitlines() if "Last Handoff Summary=" in l
        ][0].split("Last Handoff Summary=", 1)[1]
        segments = lhs_value.split(" | ")
        self.assertLessEqual(len(segments), 10)


class TestPhaseTransitionDetection(unittest.TestCase):
    """Hook-enforced Context Budget: phase transition + warning."""

    def test_phase_marker_detected(self):
        output = "<gdd-phase>gdd-task-breakdown</gdd-phase>\nSome content"
        phase, _ = detect_phase_transition(output, "gdd-design-gating")
        self.assertEqual(phase, "gdd-task-breakdown")

    def test_warning_when_handoff_missing(self):
        output = "<gdd-phase>gdd-task-breakdown</gdd-phase>\nNo handoff here."
        _, warning = detect_phase_transition(output, "gdd-design-gating")
        self.assertIn("[context-budget]", warning)
        self.assertIn("gdd-design-gating", warning)
        self.assertIn("gdd-task-breakdown", warning)

    def test_no_warning_when_handoff_present(self):
        output = textwrap.dedent("""\
            <gdd-phase>gdd-task-breakdown</gdd-phase>
            <!-- Context Handoff: design-gating → task-breakdown -->
            **Handoff:** 設計確定
        """)
        _, warning = detect_phase_transition(output, "gdd-design-gating")
        self.assertEqual(warning, "")

    def test_no_warning_when_same_phase(self):
        output = "<gdd-phase>gdd-brainstorming</gdd-phase>"
        _, warning = detect_phase_transition(output, "gdd-brainstorming")
        self.assertEqual(warning, "")

    def test_no_warning_when_no_previous_phase(self):
        output = "<gdd-phase>gdd-brainstorming</gdd-phase>"
        _, warning = detect_phase_transition(output, "")
        self.assertEqual(warning, "")

    def test_fallback_heuristic_detection(self):
        output = "Moving to gdd-implementation-gating for review."
        phase, _ = detect_phase_transition(output, "gdd-subagent-driven-implementation")
        self.assertEqual(phase, "gdd-implementation-gating")

    def test_helpers_not_detected_as_phase(self):
        """Helper skills should not be in the phase candidate list."""
        helpers = [
            "gdd-model-routing",
            "gdd-using-git-worktrees",
            "gdd-requesting-code-review",
            "gdd-receiving-code-review",
            "gdd-refactor-planning",
            "gdd-test-failure-debug-pack",
        ]
        for helper in helpers:
            output = f"Using {helper} to assist."
            phase, _ = detect_phase_transition(output, "gdd-brainstorming")
            self.assertEqual(
                phase, "gdd-brainstorming",
                f"{helper} should not be detected as a phase",
            )


class TestDetectPhaseModelRoutingNormalization(unittest.TestCase):
    """`_detect_phase()`（model routing 専用、`detect_phase_transition` とは別関数）の
    `<gdd-phase>` marker 抽出が表記ゆれを正規化すること。

    独立レビュー round 4 High/blocking 指摘（F2）: `.strip()` だけで大文字小文字を
    正規化しないため、LLM 自身の出力の表記ゆれがそのまま `resolve-gdd-model.py
    --phase` へ渡り、`PHASE_TO_TIER` の完全一致に外れて permissive な既定
    （light_task）へ落ちていた。ユーザー判断により、marker 抽出時点で
    `.strip().lower()` に正規化する（`GDD_PHASE_MARKERS` は全て小文字のため
    正規化しても既知 phase の判定は変わらない）。
    """

    def setUp(self):
        from _plugin_module_loader import load_plugin_module
        self.module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")

    def test_marker_phase_is_lowercased(self):
        # PR #89 レビュー指摘（discussion_r4024909688 / test-power medium）:
        # 本文が "Some content" だけだと、`.strip().lower()` を外して marker
        # 正規表現が fullmatch に落ちても、heuristic フォールバックが
        # `last_output.lower()` 全体（marker 部分も含む）から同じ
        # "gdd-requirements-gating" を拾ってしまい、このテストは緑のまま
        # 退行を検知できなかった。heuristic と答えが分かれる fixture にする:
        # 本文に `GDD_PHASE_MARKERS` でこの marker 値より前に並ぶ別 candidate
        # （`gdd-design-gating`）を competing signal として置く。marker 側の
        # 正規化が効いていれば marker 経由で "gdd-requirements-gating" を返し、
        # 外れて heuristic に落ちれば先に一致する "gdd-design-gating" を返す
        # ため、`.strip().lower()` を外すとこのテストは落ちるようになる。
        output = "<gdd-phase>GDD-Requirements-Gating</gdd-phase>\nSee gdd-design-gating for background"
        phase = self.module._detect_phase({}, output)
        self.assertEqual(phase, "gdd-requirements-gating")

    def test_marker_phase_strips_surrounding_whitespace(self):
        # 上と同じ理由（discussion_r4024909688）で、heuristic と答えが分かれる
        # competing candidate を本文に置く。
        output = (
            "<gdd-phase> gdd-requirements-gating \n</gdd-phase>\n"
            "See gdd-design-gating for background"
        )
        phase = self.module._detect_phase({}, output)
        self.assertEqual(phase, "gdd-requirements-gating")

    def test_already_lowercase_marker_is_unaffected(self):
        # PR #89 レビュー指摘（discussion_r4025334822 / test-power medium）:
        # 本文が "Some content" だけだと、marker 抽出の分岐そのものを丸ごと
        # 削除しても heuristic フォールバックが `last_output.lower()`（marker
        # 部分も含む）から同じ "gdd-implementation-gating" を拾ってしまい、
        # このテストは marker 経由の判定に対して判別力ゼロだった（独立レビューが
        # 7 変異——正規化削除・marker 分岐死・regex 緩め等——のいずれでも
        # このテストを通過させたと報告）。上の 2 テストと同じ手当てで、
        # `GDD_PHASE_MARKERS` でこの marker 値より前に並ぶ競合 candidate
        # （`gdd-completion-check`）を本文に置く。
        output = "<gdd-phase>gdd-implementation-gating</gdd-phase>\nSee gdd-completion-check for background"
        phase = self.module._detect_phase({}, output)
        self.assertEqual(phase, "gdd-implementation-gating")

    def test_marker_value_with_embedded_newline_is_not_returned_verbatim(self):
        # 独立レビュー round 7 High/blocking 指摘（H-1）: `PHASE_MARKER` の
        # `[^<]+` は改行にもマッチするため、`<gdd-phase>` の中身に改行を混ぜた
        # 出力を与えると、`.strip().lower()` は前後の空白しか削らず改行入りの
        # 値がそのまま `_detect_phase()` の戻り値になっていた。この戻り値は
        # `frontmatter["detected_phase"]` へ入り `write_state()` で無検証に
        # 書き出されるため、`active: false` 等の frontmatter key を注入して
        # 次ターンの `_load_active_state()` の `active` チェックを書き換え、
        # Stop hook の guard 全体を無効化できた（round 4 で `.lower()` を足した
        # ことで、注入する key 名の大文字小文字を気にしなくてよくなり悪用条件が
        # 緩んでいた）。改行や `:` を含む値は marker として受理せず、
        # heuristic フォールバックへ落とす（fail-closed）。
        output = "<gdd-phase>GDD-Brainstorming\nactive: false</gdd-phase>\nSome content"
        phase = self.module._detect_phase({}, output)
        self.assertNotIn("\n", phase)
        self.assertNotIn(":", phase)
        # heuristic フォールバックが lower_output 中の正当な candidate
        # （"gdd-brainstorming"）を拾うため、注入は無効化されつつ検出自体は
        # 機能する。
        self.assertEqual(phase, "gdd-brainstorming")

    def test_marker_value_of_only_hyphens_is_rejected(self):
        # 独立レビュー round 9 指摘（H-1 の防御多層化）: `[a-z0-9-]+` は
        # `-`/`---` のようなハイフンのみの値も受理してしまい、`---` が
        # `parse_state()` の frontmatter 終端の部分文字列と衝突する
        # attacker-controlled 値になりえた（`state_io.py` 側の line-exact
        # 終端判定が本体の修正だが、marker 側でも受理集合を締めて多層防御する）。
        output = "<gdd-phase>---</gdd-phase>\nunrelated content"
        phase = self.module._detect_phase(
            {"detected_phase": "gdd-design-gating"}, output
        )
        self.assertNotEqual(phase, "---")

    def test_marker_value_with_invalid_characters_and_no_fallback_candidate_falls_back_to_current_phase(self):
        # 独立レビュー round 7 指摘（H-1 の裏側）: heuristic フォールバックにも
        # 正当な candidate が無い場合、注入値ではなく既存の `current_phase`
        # （frontmatter の既存値、正規化済み）へ安全に倒れること。
        output = "<gdd-phase>\nactive: false</gdd-phase>\nunrelated content"
        phase = self.module._detect_phase(
            {"detected_phase": "gdd-design-gating"}, output
        )
        self.assertEqual(phase, "gdd-design-gating")

    def test_frontmatter_fallback_phase_is_normalized_when_no_marker_or_text_match(self):
        # 独立レビュー round 5 指摘（F-5）: marker 抽出結果は正規化していたが、
        # marker もヒューリスティックなテキスト一致も無い場合に frontmatter の
        # 既存 `detected_phase` をそのまま返す fallback には及んでいなかった
        # （marker 未検出のターンで非正規化値がそのまま永続しうる）。
        output = "No phase marker and no heuristic keyword here."
        phase = self.module._detect_phase(
            {"detected_phase": "GDD-Requirements-Gating"}, output
        )
        self.assertEqual(phase, "gdd-requirements-gating")


class TestSessionStartInjection(unittest.TestCase):
    """Verify that Last Handoff persisted by stop hook can be extracted
    by the same grep pattern used in run-session-start-hook.sh."""

    def _make_active_steering(self, repo: Path, slug: str) -> None:
        steering = repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        (steering / "state.md").write_text(
            "# State\n\n"
            "## Metadata\n"
            "- Started At: 2026-06-01T00:00:00Z\n\n"
            "## Gate Status\n"
            "- Requirements Review Status=approved | evidence: req\n"
            "- Design Review Status=approved | evidence: des\n"
            "- Human Check Status=approved | evidence: hc\n"
            "- Resume From=gdd-test-driven-development\n"
            "- Route In Progress=none\n"
            "- Last Handoff Summary=直前の判断\n",
            encoding="utf-8",
        )
        (steering / "tasklist.md").write_text(
            "# Task List\n\n"
            "## Current Task\n"
            "### Task: T-1 | AC-01 | continue\n\n"
            "## Pending Tasks\n"
            "- なし\n\n"
            "## Completed Tasks\n"
            "- なし\n\n"
            "## Review Status\n"
            "- `Next Action=gdd-test-driven-development`\n",
            encoding="utf-8",
        )

    def _bind_active_steering(self, repo: Path, slug: str) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "gdd_task_binding.py"
        subprocess.run(
            [
                "python3",
                str(script),
                "upsert-from-state",
                "--repo-root",
                str(repo),
                "--state",
                str(repo / ".steering" / slug / "state.md"),
            ],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )

    def _run_session_start(self, repo: Path, env: dict[str, str] | None = None) -> str:
        hook = (
            Path(__file__).resolve().parents[1]
            / "hooks"
            / "scripts"
            / "run-session-start-hook.sh"
        )
        run_env = os.environ.copy()
        run_env.pop("CLAUDE_CODE_SESSION_ID", None)
        if env:
            run_env.update(env)
        result = subprocess.run(
            ["bash", str(hook)],
            cwd=repo,
            env=run_env,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        return payload["hookSpecificOutput"]["additionalContext"]

    def test_session_start_without_current_session_id_does_not_reboot_stale_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            stale_slug = "20260601-example-review-task"
            self._make_active_steering(repo, stale_slug)
            self._bind_active_steering(repo, stale_slug)
            state_dir = repo / ".claude"
            state_dir.mkdir(exist_ok=True)
            (state_dir / "gdd-dev.local.md").write_text(
                "---\n"
                "active: true\n"
                "session_id: old-session\n"
                "---\n",
                encoding="utf-8",
            )

            additional = self._run_session_start(repo)

            self.assertNotIn("[gdd:reboot]", additional)
            self.assertNotIn(stale_slug, additional)
            self.assertIn("gate-driven-development is available", additional)

    def test_session_start_with_mismatched_session_id_does_not_reboot_stale_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            stale_slug = "20260601-example-review-task"
            self._make_active_steering(repo, stale_slug)
            self._bind_active_steering(repo, stale_slug)
            state_dir = repo / ".claude"
            state_dir.mkdir(exist_ok=True)
            (state_dir / "gdd-dev.local.md").write_text(
                "---\n"
                "active: true\n"
                "session_id: old-session\n"
                "---\n",
                encoding="utf-8",
            )

            additional = self._run_session_start(
                repo,
                {"CLAUDE_CODE_SESSION_ID": "new-session"},
            )

            self.assertNotIn("[gdd:reboot]", additional)
            self.assertNotIn(stale_slug, additional)
            self.assertIn("[gdd:paused]", additional)

    def test_session_start_with_empty_stored_session_id_does_not_reboot_stale_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            stale_slug = "20260601-example-review-task"
            self._make_active_steering(repo, stale_slug)
            self._bind_active_steering(repo, stale_slug)
            state_dir = repo / ".claude"
            state_dir.mkdir(exist_ok=True)
            (state_dir / "gdd-dev.local.md").write_text(
                "---\n"
                "active: true\n"
                "session_id:\n"
                "---\n",
                encoding="utf-8",
            )

            additional = self._run_session_start(
                repo,
                {"CLAUDE_CODE_SESSION_ID": "new-session"},
            )

            self.assertNotIn("[gdd:reboot]", additional)
            self.assertNotIn(stale_slug, additional)
            self.assertIn("[gdd:paused]", additional)

    def test_session_start_without_local_state_file_does_not_reboot_stale_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            stale_slug = "20260601-example-review-task"
            self._make_active_steering(repo, stale_slug)
            self._bind_active_steering(repo, stale_slug)

            additional = self._run_session_start(
                repo,
                {"CLAUDE_CODE_SESSION_ID": "new-session"},
            )

            self.assertNotIn("[gdd:reboot]", additional)
            self.assertNotIn(stale_slug, additional)
            self.assertIn("[gdd:paused]", additional)

    def test_session_start_blocked_state_is_not_replaced_by_paused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            slug = "20260602-missing-canonical-field"
            self._make_active_steering(repo, slug)
            state_file = repo / ".steering" / slug / "state.md"
            state_file.write_text(
                "# State\n\n"
                "## Metadata\n"
                "- Started At: 2026-06-01T00:00:00Z\n\n"
                "## Gate Status\n"
                "- Requirements Review Status=approved | evidence: req\n"
                "- Design Review Status=approved | evidence: des\n"
                "- Resume From=gdd-test-driven-development\n"
                "- Route In Progress=none\n",
                encoding="utf-8",
            )
            self._bind_active_steering(repo, slug)

            additional = self._run_session_start(repo)

            self.assertIn("[gdd:blocked]", additional)
            self.assertIn("Human Check Status", additional)
            self.assertNotIn("[gdd:paused]", additional)

    def test_session_start_with_matching_session_id_can_reboot_active_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            slug = "20260602-llm-judge-secret-output-ban"
            self._make_active_steering(repo, slug)
            self._bind_active_steering(repo, slug)
            state_dir = repo / ".claude"
            state_dir.mkdir(exist_ok=True)
            (state_dir / "gdd-dev.local.md").write_text(
                "---\n"
                "active: true\n"
                "session_id: same-session\n"
                "---\n",
                encoding="utf-8",
            )

            additional = self._run_session_start(
                repo,
                {"CLAUDE_CODE_SESSION_ID": "same-session"},
            )

            self.assertIn("[gdd:reboot]", additional)
            self.assertIn(slug, additional)

    def test_round_trip_persist_then_extract(self):
        """Full round-trip: stop hook persists, session-start hook extracts."""
        output = textwrap.dedent("""\
            <!-- Context Handoff: design-gating → task-breakdown -->
            **Handoff:** カーソルベースAPI確定 | 変更: src/api/users.ts | 注意: offset上限
        """)
        updated = persist_handoff_summary_to_content(output, SAMPLE_STATE)

        # Extract like session-start hook
        value = ""
        for line in updated.splitlines():
            if "Last Handoff Summary=" in line:
                value = line.split("Last Handoff Summary=", 1)[1]
                break

        self.assertIn("カーソルベースAPI確定", value)
        self.assertIn("src/api/users.ts", value)


if __name__ == "__main__":
    unittest.main()
