"""事前回答（`references/human-check-template.md` § 事前回答）を読むコードの契約。

- `scripts/lint-hitl-stage-plan.py`: 後続 Stage の承認範囲に `事前回答で後続PRも実施許可` を受ける
- `scripts/lint-approved-direction.py`: 自走上限か `human:` の evidence の値が、自走のマージを指しうる値か注記を付けた
  `PR マージ後検証 / 再学習まで` のとき、表の値でない値・行の数と形・両者の不一致を警告する。`human:` で始まらない evidence は、自走上限が自走のマージを指しうる値で、status が
  承認前（`pending`・`changes_requested`）でないときだけ警告する（`references/post-merge-qa.md`
  手順 2 の自走のマージは完全一致を求める）。
  steering の書き込み hook（`hooks/scripts/validate-steering-write.py`）が、自走上限の行に触れない書き込みでは返さないことも見る
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _plugin_module_loader import load_plugin_module

STAGE_LINT = PLUGIN_ROOT / "scripts" / "lint-hitl-stage-plan.py"
AD_LINT = PLUGIN_ROOT / "scripts" / "lint-approved-direction.py"
HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
TEMPLATE = PLUGIN_ROOT / "references" / "human-check-template.md"

PRE_ANSWER_SCOPE = "事前回答で後続PRも実施許可"

STAGE_TABLE = """### 段階実装案

| Stage | この段階でやること | このPR/後続 | このOKで承認する範囲 | 完了確認 | 次に進む条件 / 人間に戻す条件 | 後続の追跡先 | 見積もり diff 行数 |
|---|---|---|---|---|---|---|---|
| S-1 | 読み方とガードを足す | current-pr | このPRで実施許可 | pytest pass | AC 変更時に戻る | なし | 300〜500 行 |
| S-2 | 許可欄名を env に足す | {boundary} | {scope} | E2E pass | 事前回答の人に戻す条件 | Planned Follow-up Stage Lane | 10〜30 行 |
"""

# GDD を使う別の repo（2026-10-02）で手作りされた記録の形
HANDMADE_STATE = """# State

## Gate Status
- Human Check Status: approved | evidence: human:マージまで（2026-10-01 夜の人の事前回答。承認ポイント 1〜5 の個別判断は Fable が代行） | updated_by: gdd-design-gating | updated_at: 2026-10-02T09:16:12+09:00
- Route In Progress: none

## Approved Direction
- 何を作るか: 通知から欄を取る読み方
- 自走上限: マージまで（merge ごとの確認なし。Fable に相談）
- 人に戻す条件: 計画 §7
"""

CANONICAL_STATE = """# State

## Gate Status
- Human Check Status: approved | evidence: human:マージまで | updated_by: gdd-design-gating | updated_at: 2026-10-02T09:16:12+09:00

## Approved Direction
- 自走上限: マージまで
- 人に戻す条件: 事前回答の人に戻す条件
"""


def _run_stage_lint(boundary: str, scope: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "draft.md"
        path.write_text(STAGE_TABLE.format(boundary=boundary, scope=scope), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(STAGE_LINT), str(path), "--expected-stage", "S-1", "--expected-stage", "S-2"],
            capture_output=True, text=True,
        )


def _run_ad_lint(state_text: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.md"
        path.write_text(state_text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(AD_LINT), str(path), "--quiet"], capture_output=True, text=True,
        )


def _section(text: str, heading: str) -> str:
    after = text.split(heading, 1)[1]
    return re.split(r"^#{2,3} ", after, maxsplit=1, flags=re.MULTILINE)[0]


class StagePlanPreAnswerScopeTests(unittest.TestCase):
    def test_follow_up_stages_accept_pre_answer_scope(self) -> None:
        for boundary in ("follow-up-pr", "post-merge-verification"):
            with self.subTest(boundary=boundary):
                result = _run_stage_lint(boundary, PRE_ANSWER_SCOPE)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_current_pr_rejects_pre_answer_scope(self) -> None:
        result = _run_stage_lint("current-pr", PRE_ANSWER_SCOPE)
        self.assertEqual(result.returncode, 1)
        self.assertIn("approval scope does not match PR boundary", result.stderr)

    def test_template_scope_vocabulary_matches_lint(self) -> None:
        """template の段階実装案の表が示す承認範囲の語彙と、lint が受ける集合が一致する。"""
        lint = load_plugin_module("scripts/lint-hitl-stage-plan.py")
        section = _section(TEMPLATE.read_text(encoding="utf-8"), "### 段階実装案")
        rows = [line for line in section.splitlines() if line.startswith("|")]
        header = [c.strip() for c in rows[0].strip("|").split("|")]
        col = header.index("このOKで承認する範囲")
        for row in rows[2:]:
            cell = [c.strip() for c in row.strip("|").split("|")][col]
            with self.subTest(row=row[:20]):
                self.assertEqual(set(cell.strip("<>").split(" / ")), set(lint.APPROVAL_SCOPES))


class HumanEvidenceLintTests(unittest.TestCase):
    def test_handmade_parenthetical_warns(self) -> None:
        result = _run_ad_lint(HANDMADE_STATE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN: human-evidence", result.stdout)

    def test_canonical_record_is_silent(self) -> None:
        result = _run_ad_lint(CANONICAL_STATE)
        self.assertNotIn("WARN", result.stdout + result.stderr)

    def test_mismatched_limit_warns(self) -> None:
        state = CANONICAL_STATE.replace("- 自走上限: マージまで", "- 自走上限: PR 作成まで")
        result = _run_ad_lint(state)
        self.assertIn("WARN: human-evidence", result.stdout)

    def test_same_annotation_on_both_sides_warns_annotation_only(self) -> None:
        """両方に同じ補足を写した記録は一致するが、自走のマージの値ではないので補足の WARN を出す。"""
        for limit in ("マージまで", "マージ・デプロイ・QA まで"):
            annotated = f"{limit}（事前回答）"
            state = CANONICAL_STATE.replace("human:マージまで", f"human:{annotated}").replace(
                "- 自走上限: マージまで", f"- 自走上限: {annotated}"
            )
            with self.subTest(limit=limit):
                result = _run_ad_lint(state)
                self.assertIn(f"`{limit}` に注記が付いた形", result.stdout)
                self.assertNotIn("一致しません", result.stdout)

    def test_non_human_evidence_is_not_checked(self) -> None:
        state = CANONICAL_STATE.replace("human:マージまで", "autonomy:human-check").replace(
            "- 自走上限: マージまで", "- 自走上限: PR 作成まで"
        )
        result = _run_ad_lint(state)
        self.assertNotIn("WARN", result.stdout + result.stderr)

    def test_state_without_globs_is_silent(self) -> None:
        """glob pattern の無い state.md は usage error にせず、--quiet では何も出さない。"""
        result = _run_ad_lint(CANONICAL_STATE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout + result.stderr, "")

    def test_evidence_warn_comes_without_usage_noise(self) -> None:
        result = _run_ad_lint(HANDMADE_STATE)
        self.assertIn("WARN: human-evidence", result.stdout)
        self.assertNotIn("INFO:", result.stdout + result.stderr)
        self.assertNotIn("usage:", result.stdout + result.stderr)

    def test_missing_state_md_is_usage_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(AD_LINT), "/nonexistent/state.md", "--quiet"], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_merge_limits_are_template_values(self) -> None:
        """lint が完全一致を求める自走上限の値は、template の自走上限の置換値の表にある。"""
        lint = load_plugin_module("scripts/lint-approved-direction.py")
        section = _section(TEMPLATE.read_text(encoding="utf-8"), "### 自走上限の置換値")
        values = {
            line.strip("|").split("|")[0].strip() for line in section.splitlines() if line.startswith("|")
        }
        self.assertTrue(lint.MERGE_AUTONOMY_LIMITS)
        self.assertLessEqual(set(lint.MERGE_AUTONOMY_LIMITS), values)


    def test_delegates_match_template_record_format(self) -> None:
        """Stop hook が読む委任先の集合は、template の事前回答の記録の形の値と同じ。"""
        sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
        try:
            from lib import autonomy_pushback as pushback
        finally:
            sys.path.pop(0)
        section = _section(TEMPLATE.read_text(encoding="utf-8"), "## 事前回答")
        match = re.search(r"委任先: <([^>]+)>", section)
        self.assertIsNotNone(match)
        values = {value.strip() for value in match.group(1).split("|")}
        self.assertEqual(set(pushback.DELEGATES), values)

class HumanEvidenceHookEntryTests(unittest.TestCase):
    """steering の書き込み hook の入口で、自走上限の行に触れない書き込みには additionalContext を返さない（届くことは test_autonomy_value_notes.py が見る）。"""

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def _edit_state(self, text: str) -> subprocess.CompletedProcess:
        state = self._tmp / ".steering" / "20261002-pre-answer" / "state.md"
        state.parent.mkdir(parents=True)
        # 書き込み hook は state.md の Tier 1 field が欠けると deny するので、メタデータを足す
        metadata = "Started At: 2026-10-02T00:26:19+09:00\n- Resume From: gdd-task-breakdown\n- Next Action: gdd-task-breakdown\n"
        state.write_text(text.replace("## Gate Status\n", "## Gate Status\n" + metadata, 1), encoding="utf-8")
        # old_string が無い Edit は、リスクの段が低でない steering では risk_tier が先に止めるので、段を低にし、依頼の原文（hook の節で始まる request.md）を置く
        (state.parent / "request-crosscheck.md").write_text("### リスクの段\n\nリスクの段: 低\n", encoding="utf-8")
        (state.parent / "request.md").write_text("<!-- gdd-request-capture:begin -->\n", encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state), "old_string": "- Route In Progress: none",
                           "new_string": "- Route In Progress: none "},
        }
        # CLAUDE_PLUGIN_ROOT が空だと hook は cwd を plugin root とみなすので、明示する
        env = dict(os.environ, GDD_HOOK_STATE_DIR=self._state_dir, CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT))
        return subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), env=env, capture_output=True, text=True,
        )

    def test_hook_advisory_is_silent_for_canonical_state(self) -> None:
        result = self._edit_state(CANONICAL_STATE)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout) if result.stdout.strip() else {}
        self.assertNotIn("systemMessage", response)
        self.assertNotIn("additionalContext", response.get("hookSpecificOutput", {}))

    def test_hook_does_not_repeat_notes_for_lines_it_did_not_change(self) -> None:
        """注記の付いた既存の記録は書き換えないので、自走上限の行に触れない書き込みでは返さない。"""
        result = self._edit_state(HANDMADE_STATE)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout) if result.stdout.strip() else {}
        self.assertNotIn("additionalContext", response.get("hookSpecificOutput", {}))


if __name__ == "__main__":
    unittest.main()
