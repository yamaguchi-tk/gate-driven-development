"""`scripts/lint-approved-direction.py` が state.md の Approved Direction から glob を取り出す範囲の契約。

正本の書式（`references/requirements-template.md` § Approved Direction テンプレート）は `## Approved Direction`
の見出しの節で、glob は `含むディレクトリ / モジュール glob:` の欄に書く。自由文の欄（`自走範囲` の値、
`承認後の到達点`、`事前スキャン対象 glob` など）からは取り出さない。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _plugin_module_loader import load_plugin_module

AD_LINT = PLUGIN_ROOT / "scripts" / "lint-approved-direction.py"
TEMPLATE = PLUGIN_ROOT / "references" / "requirements-template.md"

GLOB_FIELD = "含むディレクトリ / モジュール glob"

HEADING_STATE = """# State

## Approved Direction
- 方向性: 通知から欄を取る
- 自走範囲:
  - 含むディレクトリ / モジュール glob: {globs}
  - 含む AC: [AC-1]
- 自走上限: PR 作成まで
- 承認後の到達点: PR 作成まで / deploy 手前まで
- 事前スキャン対象 glob: src/notify/handler.py
- 人間に戻す条件: 方向性自体の変更

## Gate Status
- Route In Progress: none
"""


def _extract(state_text: str) -> list[str]:
    lint = load_plugin_module("scripts/lint-approved-direction.py")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.md"
        path.write_text(state_text, encoding="utf-8")
        return lint.extract_patterns_from_state_md(path)


def _run(state_text: str, *extra: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.md"
        path.write_text(state_text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(AD_LINT), str(path), *extra], capture_output=True, text=True,
        )


class HeadingFormExtractionTests(unittest.TestCase):
    def test_single_file_glob_in_declared_field_fails(self) -> None:
        result = _run(HEADING_STATE.format(globs="src/auth/**, src/http/cookie.ts"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/http/cookie.ts'", result.stdout)
        self.assertNotIn("'src/auth/**'", result.stdout)

    def test_global_security_glob_in_declared_field_warns(self) -> None:
        result = _run(HEADING_STATE.format(globs="**/auth/**"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN: global glob '**/auth/**'", result.stdout)

    def test_directory_globs_pass_silently(self) -> None:
        state = HEADING_STATE.format(globs="src/notify/**, tests/notify/**")
        self.assertEqual(_extract(state), ["src/notify/**", "tests/notify/**"])
        result = _run(state)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout + result.stderr, "")

    def test_free_text_fields_are_not_extracted(self) -> None:
        """`承認後の到達点` の `/` や `事前スキャン対象 glob` の単一ファイルは読まない。"""
        self.assertEqual(_extract(HEADING_STATE.format(globs="src/notify/**")), ["src/notify/**"])

    def test_free_text_scope_value_is_not_extracted(self) -> None:
        state = HEADING_STATE.replace(
            "- 自走範囲:\n  - 含むディレクトリ / モジュール glob: {globs}\n",
            "- 自走範囲: S-1（SKILL.md 変更）+ S-2（scripts/foo.py 変更） / PR 作成まで\n",
        )
        self.assertNotIn(GLOB_FIELD, state)
        self.assertIn("scripts/foo.py", state)
        self.assertEqual(_extract(state), [])

    def test_non_path_value_is_not_a_pattern(self) -> None:
        """`repo 全体` のような glob でない値は pattern にせず、INFO（glob を検査していない）に落とす。"""
        state = HEADING_STATE.format(globs="repo 全体")
        self.assertEqual(_extract(state), [])
        result = _run(state)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_field_with_negated_glob_is_not_read(self) -> None:
        """`!src/legacy/**` のような否定の語があれば、欄を読まずに WARN と INFO を出す。"""
        result = _run(HEADING_STATE.format(globs="!src/legacy/**"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN: glob field not read", result.stdout)
        self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_field_with_leading_dash_glob_is_not_read(self) -> None:
        result = _run(HEADING_STATE.format(globs="src/**, -src/legacy/**"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN: glob field not read", result.stdout)

    def test_paths_with_symbols_or_wide_chars_are_read(self) -> None:
        """`@`・括弧・`+`・全角の文字を含む正当なパスでも欄を読み、同じ欄の単一ファイルを ERROR にする。"""
        for glob in ("app/(auth)/**", "packages/@org/ui/**", "src/routes/**/+page.svelte", "docs/設計/**"):
            with self.subTest(glob=glob):
                result = _run(HEADING_STATE.format(globs=f"{glob}, src/http/cookie.ts"))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("ERROR: single-file-fixed glob 'src/http/cookie.ts'", result.stdout)
                self.assertNotIn("glob field not read", result.stdout)

    def test_field_with_non_glob_word_is_not_read(self) -> None:
        """glob の形（glob meta を含む語か、拡張子つきの語）でない語が 1 つでもあれば、欄を読まずに INFO に落とす。"""
        for value in (
            "S-1/S-2", "/", "S-1/S-2/", "src/notify", "src/auth/**, PR 作成まで",
            "[TBD]", "未定?", "{TBD}", "**未定**", "src/auth/**, src/http/** etc.", "v1.2",
        ):
            with self.subTest(value=value):
                state = HEADING_STATE.format(globs=value)
                self.assertEqual(_extract(state), [])
                result = _run(state)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
                self.assertTrue(result.stdout.startswith("WARN: glob field not read: "), result.stdout)
                self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_field_not_read_is_warned_even_when_quiet(self) -> None:
        """欄を読まなかったことは、--quiet で呼ぶ hook にも届くよう WARN で出す（語を並べる）。"""
        result = _run(HEADING_STATE.format(globs="src/http/cookie.ts など"), "--quiet")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "WARN: glob field not read: non-glob words ['など'] in '含むディレクトリ / モジュール glob'。"
            "glob を検査していないので、自走範囲を手で照らしてください"
        ])

    def test_middle_dot_and_slash_separators_split_words(self) -> None:
        for sep in ("・", ";", "|", "／"):
            with self.subTest(sep=sep):
                state = HEADING_STATE.format(globs=f"src/auth/**{sep}src/http/cookie.ts")
                self.assertEqual(_extract(state), ["src/auth/**", "src/http/cookie.ts"])

    def test_single_file_with_line_suffix_fails(self) -> None:
        for suffix in (":42", ":10-20"):
            with self.subTest(suffix=suffix):
                result = _run(HEADING_STATE.format(globs=f"src/auth/**, src/foo.ts{suffix}"))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"ERROR: single-file-fixed glob 'src/foo.ts{suffix}'", result.stdout)
                self.assertNotIn("glob field not read", result.stdout)

    def test_single_file_with_any_extension_is_a_pattern(self) -> None:
        self.assertEqual(_extract(HEADING_STATE.format(globs="main.go, package.json")), ["main.go", "package.json"])

    def test_non_glob_continuation_line_drops_the_field(self) -> None:
        state = HEADING_STATE.format(globs="src/auth/**").replace(
            "  - 含む AC: [AC-1]\n", "    - S-1/S-2\n  - 含む AC: [AC-1]\n"
        )
        self.assertEqual(_extract(state), [])

    def test_continuation_lines_of_the_field_are_read(self) -> None:
        state = HEADING_STATE.format(globs="src/auth/**").replace(
            "  - 含む AC: [AC-1]\n", "    - src/http/cookie.ts\n  - 含む AC: [AC-1]\n"
        )
        self.assertEqual(_extract(state), ["src/auth/**", "src/http/cookie.ts"])

    def test_non_heading_hash_lines_and_deeper_headings_do_not_close_the_block(self) -> None:
        state = HEADING_STATE.format(globs="src/auth/**").replace(
            "- 自走範囲:\n", "#123 の対応\n### 補足\n- 自走範囲:\n"
        )
        self.assertEqual(_extract(state), ["src/auth/**"])

    def test_colon_reader_does_not_run_when_heading_block_exists(self) -> None:
        """見出しの節があるときは、colon の形の読み方（自由文から path らしい語を拾う）を走らせない。"""
        state = HEADING_STATE.format(globs="src/notify/**").replace(
            "- 方向性: 通知から欄を取る\n", "- 方向性: 通知から欄を取る\n- Approved Direction: 承認済み\n"
        )
        self.assertEqual(_extract(state), ["src/notify/**"])

    def test_placeholder_value_is_not_extracted(self) -> None:
        result = _run(HEADING_STATE.format(globs="<例: src/auth/**, src/http/cookie.ts>"), "--quiet")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("ERROR", result.stdout)

    def test_block_ends_at_next_heading(self) -> None:
        state = HEADING_STATE.format(globs="src/notify/**") + f"\n## Notes\n- {GLOB_FIELD}: src/other/x.ts\n"
        result = _run(state, "--quiet")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("x.ts", result.stdout)

    def test_template_declares_the_field_the_lint_reads(self) -> None:
        """lint が読む欄名は、正本のテンプレートの Approved Direction の欄名と一致する。"""
        lint = load_plugin_module("scripts/lint-approved-direction.py")
        self.assertEqual(lint.GLOB_FIELD_LABEL, GLOB_FIELD)
        self.assertIn(f"- {lint.GLOB_FIELD_LABEL}:", TEMPLATE.read_text(encoding="utf-8"))


class HookEntryTests(unittest.TestCase):
    """steering の書き込み hook の入口から、見出しの形の ERROR が advisory の systemMessage まで届く。"""

    def test_hook_advisory_reports_single_file_glob(self) -> None:
        import json
        import os
        import shutil

        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        state = tmp / ".steering" / "20261002-glob" / "state.md"
        state.parent.mkdir(parents=True)
        metadata = "## Gate Status\nStarted At: 2026-10-02T00:26:19+09:00\n- Resume From: gdd-task-breakdown\n- Next Action: gdd-task-breakdown\n- Human Check Status: approved | evidence: human:PR 作成まで\n- Route In Progress: none\n"
        text = HEADING_STATE.format(globs="src/auth/**, src/http/cookie.ts").replace(
            "## Gate Status\n- Route In Progress: none\n", metadata
        )
        state.write_text(text, encoding="utf-8")
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(state), "old_string": "- Route In Progress: none",
                           "new_string": "- Route In Progress: none "},
        }
        env = dict(os.environ, GDD_HOOK_STATE_DIR=str(tmp / "hookstate"), CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT))
        result = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload), env=env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        message = json.loads(result.stdout).get("systemMessage", "")
        self.assertIn("ERROR: single-file-fixed glob 'src/http/cookie.ts'", message)


class ColonFormExtractionTests(unittest.TestCase):
    def test_colon_form_still_extracts(self) -> None:
        result = _run("Approved Direction:\n  自走範囲: src/foo.ts, src/bar/**\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/foo.ts'", result.stdout)

    def test_colon_form_single_file_with_line_suffix_fails(self) -> None:
        result = _run("Approved Direction:\n  自走範囲: src/foo.ts:42, src/bar/**\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/foo.ts:42'", result.stdout)

    def test_colon_form_skips_dotted_words_outside_scope_line(self) -> None:
        """`自走範囲` 以外の行（`戻し条件` など）の自由文では、`/` の無いドット付きの語（host:port・ホスト名）を glob にしない。"""
        for word in ("db.internal:5432", "api.example.com:443", "api.example.com", "main.go", "cookie.tsx"):
            with self.subTest(word=word):
                result = _run(f"Approved Direction:\n  自走範囲: src/bar/**\n  戻し条件: {word} が変わったら戻す\n")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout + result.stderr, "")

    def test_colon_form_flags_known_extensions_outside_scope_line(self) -> None:
        for word in ("app.js", "setup.py", "main.tf", "NOTES.md", "cookie.ts", "cookie.ts:10-20"):
            with self.subTest(word=word):
                result = _run(f"Approved Direction:\n  自走範囲: src/bar/**\n  戻し条件: {word} が変わったら戻す\n")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"ERROR: single-file-fixed glob '{word}'", result.stdout)

    def test_colon_form_scope_line_flags_any_single_file(self) -> None:
        """`自走範囲` の行では、どの拡張子の単一ファイルも ERROR にする（block すべき入力が通らない）。"""
        for word in ("package.json", "main.go", "cookie.ts:42"):
            with self.subTest(word=word):
                result = _run(f"Approved Direction:\n  自走範囲: {word}, src/bar/**\n")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"ERROR: single-file-fixed glob '{word}'", result.stdout)

    def test_colon_form_slash_words_keep_their_checks(self) -> None:
        result = _run("Approved Direction:\n  自走範囲: src/bar/**\n  戻し条件: src/main.go か **/auth/** に触れたら戻す\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/main.go'", result.stdout)
        self.assertIn("WARN: global glob '**/auth/**'", result.stdout)

    def test_colon_form_bullet_block_ends_at_sibling_bullet_and_heading(self) -> None:
        """`- Approved Direction: <自由文>` の節は、同じ字下げ以下の次の箇条か見出しで終わる。"""
        state = (
            "## Gate Status\n- Approved Direction: 既存 hook を拡張する\n- Route In Progress: none\n"
            "- Last Handoff Summary: SKILL.md を更新した\n## Notes\n- 戻し条件: state.md\n"
        )
        result = _run(state)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")

    def test_colon_form_bullet_block_reads_deeper_items(self) -> None:
        result = _run("- Approved Direction:\n  - 方向性: hook を拡張する\n  - 自走範囲: src/a.go, src/b/**\n- Route In Progress: none\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/a.go'", result.stdout)

    def test_colon_form_bullet_block_reads_flat_scope_items(self) -> None:
        """正本テンプレートと同じく、`Approved Direction` と同じ字下げに `- 方向性:`・`- 自走範囲:` を並べても読む。"""
        state = "- Approved Direction: 既存 hook を拡張する\n- 方向性: hook を拡張する\n- 自走範囲: src/foo.ts, src/bar/**\n"
        result = _run(state)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/foo.ts'", result.stdout)

    def test_colon_form_scope_continuation_lines_flag_any_single_file(self) -> None:
        cases = (
            "Approved Direction:\n  自走範囲:\n    - main.go\n    - src/b/**\n",
            "- Approved Direction:\n  - 自走範囲:\n    - 含むディレクトリ / モジュール glob: package.json, src/b/**\n- Route In Progress: none\n",
        )
        for state, word in zip(cases, ("main.go", "package.json")):
            with self.subTest(word=word):
                result = _run(state)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"ERROR: single-file-fixed glob '{word}'", result.stdout)

    def test_colon_form_annotated_scope_label_is_a_scope_line(self) -> None:
        """欄名に注記（`（S-1）`・`(S-1)`）や `=` を付けた `自走範囲` の行も、どの拡張子の単一ファイルも ERROR にする。"""
        for label in ("自走範囲（S-1）:", "自走範囲 (S-1) :", "自走範囲 =", "自走範囲（S-1）=", "- 自走範囲（S-1）："):
            with self.subTest(label=label):
                result = _run(f"Approved Direction:\n  {label} main.go, src/bar/**\n")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(result.stdout.splitlines(), [
                    "ERROR: single-file-fixed glob 'main.go': rename/split で silent に過剰発動します。"
                    "最低限ディレクトリ単位 （例: 'src/foo/**'）にしてください"
                ])

    def test_colon_form_annotated_scope_label_reads_continuation_lines(self) -> None:
        for label in ("自走範囲（S-1）:", "自走範囲 ="):
            with self.subTest(label=label):
                result = _run(f"Approved Direction:\n  {label}\n    - main.go\n    - src/b/**\n")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
                self.assertIn("ERROR: single-file-fixed glob 'main.go'", result.stdout)

    def test_colon_form_scope_value_without_space_after_label(self) -> None:
        """欄名と値の間に空白が無くても、欄名を値から外して読む。"""
        result = _run("Approved Direction:\n  自走範囲=**/auth/**\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN: global glob '**/auth/**'", result.stdout)
        result = _run("Approved Direction:\n  自走範囲（S-1）：main.go\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'main.go'", result.stdout)

    def test_colon_form_single_file_in_scope_annotation_fails(self) -> None:
        """`自走範囲` の欄名の括弧の注記の中の単一ファイルも、値と同じく検査する。"""
        for label, word in (("自走範囲（scripts/foo.py の修正）:", "scripts/foo.py"), ("自走範囲(main.go のみ) =", "main.go")):
            with self.subTest(label=label):
                result = _run(f"Approved Direction:\n  {label} src/bar/**\n")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
                self.assertIn(f"ERROR: single-file-fixed glob '{word}'", result.stdout)

    def test_colon_form_non_glob_scope_annotation_is_ignored(self) -> None:
        for annotation in ("S-1・第1段階", "v1.2 対応"):
            with self.subTest(annotation=annotation):
                result = _run(f"Approved Direction:\n  自走範囲（{annotation}）: src/bar/**\n")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout + result.stderr, "")

    def test_colon_form_scope_annotation_reads_only_single_files(self) -> None:
        """注記のディレクトリ glob・全域 glob（除外の注記など）は pattern に数えない。"""
        for annotation in ("src/legacy/** を除く", "**/auth/** は人間に戻す"):
            with self.subTest(annotation=annotation):
                result = _run(f"Approved Direction:\n  自走範囲（{annotation}）: リポジトリ全体\n")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_colon_form_any_annotation_makes_a_scope_line(self) -> None:
        """括弧の注記の中身は問わない（`自走範囲（補足）:` も `自走範囲` の行にする）。"""
        result = _run("Approved Direction:\n  自走範囲: src/bar/**\n  自走範囲（補足）: api.example.com は触らない\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'api.example.com'", result.stdout)

    def test_colon_form_scope_prefix_lines_are_not_scope_lines(self) -> None:
        for line in ("自走範囲外: package.json", "自走範囲の補足: api.example.com は触らない", "自走範囲（外）の補足: package.json"):
            with self.subTest(line=line):
                result = _run(f"Approved Direction:\n  自走範囲: src/bar/**\n  {line}\n")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")

    def test_colon_form_block_ends_at_heading(self) -> None:
        for state in (
            "Approved Direction: 既存 hook を拡張する\n## Notes\n- SKILL.md を更新した\n",
            "- Approved Direction: 既存 hook を拡張する\n## Notes\nSKILL.md を更新した\n",
        ):
            with self.subTest(state=state):
                result = _run(state)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")

    def test_colon_form_globs_outside_scope_do_not_count_as_checked_scope(self) -> None:
        """`戻し条件`・`自走範囲外:`・除外の続きの行の glob は lint するが、自走範囲を検査したことには数えない（INFO を出す）。"""
        for rest in (
            "  自走範囲: リポジトリ全体\n  戻し条件: src/legacy/** に触れたら戻す\n",
            "  自走範囲: リポジトリ全体\n  自走範囲外: src/legacy/**\n",
            "  自走範囲:\n    - リポジトリ全体\n    - 明示的に除外する範囲: src/legacy/**\n",
        ):
            with self.subTest(rest=rest):
                result = _run("Approved Direction:\n" + rest)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_colon_form_out_of_scope_globs_are_still_linted(self) -> None:
        result = _run("Approved Direction:\n  自走範囲: リポジトリ全体\n  戻し条件: src/main.go か **/auth/** に触れたら戻す\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/main.go'", result.stdout)
        self.assertIn("WARN: global glob '**/auth/**'", result.stdout)
        self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_colon_form_scope_value_and_glob_field_count_as_checked_scope(self) -> None:
        for rest in (
            "  自走範囲: src/a/**\n  戻し条件: なし\n",
            "  自走範囲:\n    - 含むディレクトリ / モジュール glob: src/b/**\n",
            "  自走範囲:\n    - src/c/**\n",
        ):
            with self.subTest(rest=rest):
                result = _run("Approved Direction:\n" + rest)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout + result.stderr, "")

    def test_colon_form_exclusion_globs_in_scope_do_not_count_as_checked_scope(self) -> None:
        """自走範囲の値・欄名の無い続きの行に、glob の形でない語（除外の言い方）と並べて書いた glob は数えない。"""
        for rest in (
            "  自走範囲: リポジトリ全体、src/legacy/** は除く\n",
            "  自走範囲: リポジトリ全体（src/legacy/** を除く）\n",
            "  自走範囲:\n    - リポジトリ全体\n    - src/legacy/** は除く\n",
            "  自走範囲:\n    - リポジトリ全体\n    - （除外）src/legacy/**\n",
            "  自走範囲:\n    - リポジトリ全体\n    - !src/legacy/**\n",
            "  自走範囲:\n    - リポジトリ全体\n    - 明示的に除外する範囲:\n      - src/legacy/**\n",
            "  自走範囲: src/a/** など全体\n",
            "  自走範囲: ** except src/legacy/**\n",
            "  自走範囲:\n    - リポジトリ全体\n    - except src/legacy/**\n",
            "  自走範囲: src/** (except src/legacy/**)\n",
            "  自走範囲: **, -src/legacy/**\n",
            "  自走範囲: src/**, -src/legacy/**\n",
            "  自走範囲: (src/legacy/**)\n",
        ):
            with self.subTest(rest=rest):
                result = _run("Approved Direction:\n" + rest)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_colon_form_glob_only_scope_lines_count_as_checked_scope(self) -> None:
        """語がすべて glob の行は、注記つきの欄名・glob の欄の続きの箇条・欄名の無い行が欄名つきの行の後でも数える。"""
        for rest in (
            "  自走範囲: src/a/**, `src/b/**`\n",
            "  自走範囲（S-1）: src/a/**\n",
            "  自走範囲:\n    - 含むディレクトリ / モジュール glob:\n      - src/b/**\n",
            "  自走範囲:\n    - 明示的に除外する範囲: なし\n    - src/c/**\n",
            "  自走範囲:\n    * src/d/**\n",
            "  自走範囲: src/a/**・src/b/**; src/c/**\n",
            "  自走範囲:\n    - 除外:\n# 次の節\nApproved Direction:\n      自走範囲: src/a/**\n",
        ):
            with self.subTest(rest=rest):
                result = _run("Approved Direction:\n" + rest)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout + result.stderr, "")

    def test_colon_form_exclusion_single_file_in_scope_is_still_linted(self) -> None:
        result = _run("Approved Direction:\n  自走範囲: リポジトリ全体、src/main.go は除く\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/main.go'", result.stdout)
        self.assertIn("INFO: no Approved Direction patterns found", result.stderr)

    def test_colon_form_single_file_joined_by_separator_is_linted(self) -> None:
        """`・`・`;`・`|`・`／` でつないだ単一ファイルも、見出しの形と同じく語に分けて ERROR にする。"""
        result = _run("Approved Direction:\n  自走範囲:\n    - src/a/**\n    - src/b/**・src/foo.ts\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: single-file-fixed glob 'src/foo.ts'", result.stdout)

    def test_colon_form_skips_non_glob_words(self) -> None:
        """colon の形でも、`S-1/S-2` や `/` を glob とみなさない（語ごとに捨てる）。"""
        result = _run("Approved Direction:\n  自走範囲: S-1/S-2, PR 作成まで / deploy 手前まで\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("INFO: no Approved Direction patterns found", result.stderr)


if __name__ == "__main__":
    unittest.main()
