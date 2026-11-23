"""scripts/confirmed-text.py: human check で承認した確定文面の取り出し・digest・照合。

照合は「含まれるか」ではなく、base の版に宣言した置き換えを当てた期待値とファイル全体を
バイト単位で比べる。検出力は変異注入（隣に文を足す・1 文字変える・block を消す）で確かめる。
終了コードは 0 = 一致、1 = 不一致、2 = 入力の誤り。
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _paths import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "confirmed-text.py"

FENCE = "```"

DESIGN = f"""# design

## 変更点の要約

{FENCE}markdown
## 確定文面（フェンスの中の見出しは節にならない）
{FENCE}

## 確定文面（human check 2 回目で見せる文）

比較元は本節の写しと digest。

### D-1 新 ADR（`docs/adr/NNNN-x.md`）

Decision（比較の対象）:

{FENCE}markdown
## Decision

- (1) ADR-NNNN の決定を書く
{FENCE}

### D-2 計画の直す文

(i) 段落を置き換える:

{FENCE}markdown
新しい段落。ADR-NNNN を見る。
{FENCE}

(ii) 行の次に足す:

````markdown
- 足す行（中に {FENCE} を含む）
````

### D-3 比較の対象外

{FENCE}text noverify
比べない文
{FENCE}

## advisory の扱い

- 節の外
"""

PLAN_BASE = "# 計画\n\n古い段落。\n\n- 既存の行\n- 最後の行\n"
ADR_ACTUAL = (
    "# ADR-0192\n\n## Status\n\nAccepted\n\n## Decision\n\n- (1) ADR-0192 の決定を書く\n\n"
    "## Rejected Alternatives\n\n- なし\n"
)


def _section_digest(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    start = lines.index("## 確定文面（human check 2 回目で見せる文）")
    end = lines.index("## advisory の扱い")
    body = "\n".join(lines[start:end]) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest(), end - start


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60
    )


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


class _Fixture(unittest.TestCase):
    """base の commit に計画を置き、HEAD で確定文面を当てた repo を作る。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        init_repo(self.repo)
        (self.repo / "docs" / "adr").mkdir(parents=True)
        self.plan = self.repo / "docs" / "plan.md"
        self.plan.write_bytes(PLAN_BASE.encode("utf-8"))
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base = _git(self.repo, "rev-parse", "HEAD")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", self.base)
        # 確定文面を当てた実物（期待値と同じもの）
        self.plan.write_bytes(
            (
                "# 計画\n\n新しい段落。ADR-0192 を見る。\n\n- 既存の行\n"
                f"- 足す行（中に {FENCE} を含む）\n- 最後の行。直した\n"
            ).encode("utf-8")
        )
        self.adr = self.repo / "docs" / "adr" / "0192-x.md"
        self.adr.write_bytes(ADR_ACTUAL.encode("utf-8"))
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "apply")
        self.design = self.root / "design.md"
        self.design.write_bytes(DESIGN.encode("utf-8"))
        self.manifest_data = {
            "digest": _section_digest(DESIGN)[0],
            "substitutions": {"NNNN": "0192"},
            "files": [
                {
                    "path": "docs/plan.md",
                    "edits": [
                        {"old": "古い段落。", "new": "{{D-2#1}}"},
                        {"old": "- 既存の行\n", "new": "- 既存の行\n{{D-2#2}}\n"},
                        {"old": "- 最後の行\n", "new": "- 最後の行。直した\n", "reason": "承認済みの確定文面の外の直し"},
                    ],
                },
                {
                    "path": "docs/adr/0192-x.md",
                    "sections": [
                        {"start": "## Decision\n", "end": "\n## Rejected Alternatives", "text": "{{D-1#1}}\n"}
                    ],
                },
            ],
        }
        self.manifest = self.root / "confirmed-text.json"
        self._write_manifest()

    def _write_manifest(self) -> None:
        self.manifest.write_text(json.dumps(self.manifest_data, ensure_ascii=False), encoding="utf-8")

    def verify(self, *extra: str) -> subprocess.CompletedProcess:
        return _run(
            "verify", "--design", str(self.design), "--manifest", str(self.manifest),
            "--repo", str(self.repo), *extra,
        )


class DigestTest(_Fixture):
    def test_digest_covers_heading_to_next_h2_outside_fences(self) -> None:
        want, lines = _section_digest(DESIGN)
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"sha256={want}", r.stdout)
        self.assertIn(f"lines={lines}", r.stdout)
        self.assertIn("end: ", r.stdout)
        self.assertIn("## advisory の扱い", r.stdout)

    def test_one_char_inside_section_changes_digest_outside_does_not(self) -> None:
        base = _run("digest", "--design", str(self.design)).stdout
        self.design.write_text(DESIGN.replace("- 節の外", "- 節の外です"), encoding="utf-8")
        self.assertEqual(_run("digest", "--design", str(self.design)).stdout, base)
        self.design.write_text(DESIGN.replace("比べない文", "比べない分"), encoding="utf-8")
        self.assertNotEqual(_run("digest", "--design", str(self.design)).stdout, base)

    def test_until_extends_section_past_inner_h2(self) -> None:
        # 節の中に `##` があっても、終わりの見出しを宣言すればそこまでを承認の範囲にする
        design = DESIGN.replace("### D-3 比較の対象外\n", "## 節の中の見出し\n\n### D-3 比較の対象外\n")
        self.design.write_text(design, encoding="utf-8")
        want, lines = _section_digest(design)
        r = _run("digest", "--design", str(self.design), "--until", "## advisory の扱い")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"sha256={want}", r.stdout)
        self.assertIn(f"lines={lines}", r.stdout)
        r = _run("extract", "--design", str(self.design), "--until", "## advisory の扱い", "--block", "D-3#1")
        self.assertEqual((r.returncode, r.stdout), (0, "比べない文"), r.stderr)
        # 宣言なしでは、節の後ろに `### D-n` が残るので止める
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("--until", r.stderr)

    def test_h2_inside_section_without_block_after_is_allowed(self) -> None:
        # 節の後ろに `### D-n` が無ければ、既定どおり内側の `##` で終わる
        # （`### D-n` でない `###` は止めない）
        design = DESIGN.replace("## advisory の扱い", "## 後ろの節\n\n### 補足")
        self.design.write_text(design, encoding="utf-8")
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("## 後ろの節", r.stdout)

    def test_empty_until_is_input_error(self) -> None:
        r = _run("digest", "--design", str(self.design), "--until", "")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("confirmed-text: ERROR:", r.stderr)

    def test_digest_lists_blocks_with_verify_flag(self) -> None:
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertIn("照合する block: D-1#1 D-2#1 D-2#2", lines)
        self.assertIn("照合しない block（noverify）: D-3#1", lines)

    def test_block_lists_are_in_numeric_order(self) -> None:
        design = DESIGN.replace("### D-1 ", "### D-9 ").replace("### D-2 ", "### D-10 ")
        self.design.write_text(design, encoding="utf-8")
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("照合する block: D-9#1 D-10#1 D-10#2", r.stdout.splitlines())

    def test_noverify_fence_outside_block_heading_is_allowed(self) -> None:
        design = DESIGN.replace(
            "比較元は本節の写しと digest。", f"比較元は本節の写しと digest。\n\n{FENCE}text noverify\n例\n{FENCE}"
        )
        self.design.write_text(design, encoding="utf-8")
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("照合しない block（noverify）: D-3#1\n", r.stdout)

    def test_until_not_found_is_input_error(self) -> None:
        r = _run("digest", "--design", str(self.design), "--until", "## 無い見出し")
        self.assertEqual(r.returncode, 2)
        self.assertIn("confirmed-text: ERROR:", r.stderr)

    def test_fence_outside_valid_block_heading_is_input_error(self) -> None:
        for heading in ("### D-1（ADR の決定）", "### 題だけ"):
            with self.subTest(heading=heading):
                self.design.write_text(DESIGN.replace("### D-1 新 ADR（`docs/adr/NNNN-x.md`）", heading), encoding="utf-8")
                r = _run("digest", "--design", str(self.design))
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertIn("confirmed-text: ERROR:", r.stderr)

    def test_missing_section_is_input_error(self) -> None:
        self.design.write_text(DESIGN.replace("## 確定文面（human", "## 文面（human"), encoding="utf-8")
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 2)
        self.assertIn("confirmed-text: ERROR:", r.stderr)

    def test_unclosed_fence_is_input_error(self) -> None:
        self.design.write_text(DESIGN.replace("比べない文\n```\n", "比べない文\n"), encoding="utf-8")
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 2)
        self.assertIn("confirmed-text: ERROR:", r.stderr)


class ExtractTest(_Fixture):
    def test_extract_block_with_substitution(self) -> None:
        r = _run("extract", "--design", str(self.design), "--block", "D-1#1", "--sub", "NNNN=0192")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "## Decision\n\n- (1) ADR-0192 の決定を書く")

    def test_extract_second_block_keeps_inner_fence_and_skips_prose(self) -> None:
        r = _run("extract", "--design", str(self.design), "--block", "D-2#2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, f"- 足す行（中に {FENCE} を含む）")

    def test_indented_fence_under_list_item_is_a_block(self) -> None:
        design = DESIGN.replace(
            "### D-3 比較の対象外\n",
            f"### D-3 比較の対象外\n\n- 決定:\n\n  {FENCE}markdown\n  ## 字下げの中の見出し\n    字下げした行\n  {FENCE}\n",
        )
        self.design.write_text(design, encoding="utf-8")
        r = _run("extract", "--design", str(self.design), "--block", "D-3#1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "## 字下げの中の見出し\n  字下げした行")

    def test_column0_h2_inside_indented_fence_does_not_end_section(self) -> None:
        design = DESIGN.replace(
            "### D-3 比較の対象外\n",
            f"### D-3 比較の対象外\n\n- 決定:\n\n  {FENCE}markdown\n## 行頭の見出し\n  {FENCE}\n",
        )
        self.design.write_text(design, encoding="utf-8")
        r = _run("digest", "--design", str(self.design))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("end: ", r.stdout)
        self.assertIn("## advisory の扱い", r.stdout)

    def test_backtick_in_info_is_not_a_fence(self) -> None:
        design = DESIGN.replace("比較元は本節の写しと digest。", "比較元は本節の写しと digest。\n```a`b")
        self.design.write_text(design, encoding="utf-8")
        r = _run("extract", "--design", str(self.design), "--block", "D-1#1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "## Decision\n\n- (1) ADR-NNNN の決定を書く")

    def test_unknown_block_is_input_error(self) -> None:
        r = _run("extract", "--design", str(self.design), "--block", "D-2#3")
        self.assertEqual(r.returncode, 2)
        self.assertIn("confirmed-text: ERROR:", r.stderr)


class VerifyTest(_Fixture):
    def test_same_when_actual_matches_expected(self) -> None:
        r = self.verify()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("RESULT: SAME", r.stdout)

    def test_explicit_base(self) -> None:
        # 既定の base（merge-base origin/main HEAD）では古い段落が無く、判定できない
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        r = self.verify()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r = self.verify("--base", self.base)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_reports_verified_and_skipped_blocks(self) -> None:
        r = self.verify()
        self.assertIn("照合した block: D-1#1 D-2#1 D-2#2", r.stdout)
        self.assertIn("照合しない block（noverify）: D-3#1", r.stdout)

    def test_block_missing_from_both_manifest_and_actual_is_different(self) -> None:
        del self.manifest_data["files"][0]["edits"][1]
        self._write_manifest()
        text = self.plan.read_bytes().decode("utf-8")
        self.plan.write_bytes(text.replace(f"- 足す行（中に {FENCE} を含む）\n", "").encode("utf-8"))
        r = self.verify()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("DIFFERENT D-2#2", r.stdout)

    # 変異注入: 実物の側
    def _assert_different(self, path: Path, old: str, new: str) -> None:
        text = path.read_bytes().decode("utf-8")
        self.assertEqual(text.count(old), 1, old)
        path.write_bytes(text.replace(old, new).encode("utf-8"))
        r = self.verify()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("RESULT: DIFFERENT", r.stdout)
        self.assertIn(f"DIFFERENT {path.relative_to(self.repo).as_posix()}", r.stdout)

    def test_mutation_sentence_appended_on_same_line(self) -> None:
        self._assert_different(self.plan, "ADR-0192 を見る。", "ADR-0192 を見る。例外も認める。")

    def test_mutation_line_added_next_to_block(self) -> None:
        self._assert_different(self.plan, "を含む）\n", "を含む）\n- 足した行\n")

    def test_mutation_one_char_changed(self) -> None:
        self._assert_different(self.plan, "新しい段落", "新しい段絡")

    def test_mutation_block_deleted(self) -> None:
        self._assert_different(self.plan, f"- 足す行（中に {FENCE} を含む）\n", "")

    def test_mutation_inside_section(self) -> None:
        self._assert_different(self.adr, "の決定を書く\n", "の決定を書く\n- (2) 足した決定\n")

    def test_mutation_crlf(self) -> None:
        self._assert_different(self.plan, "- 既存の行\n", "- 既存の行\r\n")
        self.assertIn("\\r", self.verify().stdout)

    def test_section_compare_does_not_see_outside_markers(self) -> None:
        # 区間比較の限界: 目印の外に足した文は見ない（reference に書いた限界）
        self.adr.write_bytes(ADR_ACTUAL.replace("- なし\n", "- なし\n- 足した\n").encode("utf-8"))
        self.assertEqual(self.verify().returncode, 0)

    # 変異注入: design.md の側
    def test_design_changed_after_approval_is_different(self) -> None:
        self.design.write_text(DESIGN.replace("ADR-NNNN の決定", "ADR-NNNN の決定と例外"), encoding="utf-8")
        r = self.verify()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("digest", r.stdout)

    def test_block_deleted_from_design_is_input_error_even_with_new_digest(self) -> None:
        mutated = DESIGN.replace(f"````markdown\n- 足す行（中に {FENCE} を含む）\n````\n", "")
        self.design.write_text(mutated, encoding="utf-8")
        self.manifest_data["digest"] = _section_digest(mutated)[0]
        self._write_manifest()
        r = self.verify()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("confirmed-text: ERROR:", r.stderr)
        self.assertIn("D-2#2", r.stdout + r.stderr)

    # 判定できないときに通さない
    def _assert_input_error(self) -> subprocess.CompletedProcess:
        self._write_manifest()
        r = self.verify()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("confirmed-text: ERROR:", r.stderr)
        self.assertNotIn("RESULT: SAME", r.stdout)
        return r

    def test_old_matching_twice_is_input_error(self) -> None:
        self.manifest_data["files"][0]["edits"][1]["old"] = "\n"
        self._assert_input_error()

    def test_old_not_found_is_input_error(self) -> None:
        self.manifest_data["files"][0]["edits"][0]["old"] = "無い段落。"
        self._assert_input_error()

    def test_missing_digest_is_input_error(self) -> None:
        del self.manifest_data["digest"]
        self._assert_input_error()

    def test_unknown_placeholder_is_input_error(self) -> None:
        self.manifest_data["files"][0]["edits"][0]["new"] = "{{D-9#1}}"
        self._assert_input_error()

    def test_section_marker_not_found_is_input_error(self) -> None:
        self.manifest_data["files"][1]["sections"][0]["end"] = "\n## Consequences"
        self._assert_input_error()

    def test_broken_json_is_input_error(self) -> None:
        self.manifest.write_text("{", encoding="utf-8")
        r = self.verify()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("confirmed-text: ERROR:", r.stderr)

    def test_missing_actual_file_is_different(self) -> None:
        for path in (self.adr, self.plan):
            with self.subTest(path=path.name):
                data = path.read_bytes()
                path.unlink()
                r = self.verify()
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("実物のファイルが無い", r.stdout)
                self.assertIn("RESULT: DIFFERENT", r.stdout)
                path.write_bytes(data)

    def test_overlapping_match_is_input_error(self) -> None:
        # "\n\n\n" に "\n\n" は重なって 2 回あたる（str.count では 1 回に見える）
        _git(self.repo, "checkout", "-q", "-b", "x", self.base)
        (self.repo / "docs" / "plan.md").write_bytes("# 計画\n\n\n古い段落。\n".encode("utf-8"))
        _git(self.repo, "commit", "-qam", "base2")
        self.base = _git(self.repo, "rev-parse", "HEAD")
        self.manifest_data["files"][0]["edits"] = [{"old": "\n\n", "new": "\n"}]
        self._write_manifest()
        r = self.verify("--base", self.base)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("2 回以上", r.stderr)

    def test_sections_for_file_present_at_base_is_input_error(self) -> None:
        self.manifest_data["files"][0] = {
            "path": "docs/plan.md",
            "sections": [{"start": "新しい段落", "end": "\n- 既存の行", "text": "{{D-2#1}}"}],
        }
        self._assert_input_error()

    def test_unknown_key_with_valid_edits_is_input_error(self) -> None:
        # repo はケースで変えないので組み直さず、manifest だけを毎回元に戻す
        original = copy.deepcopy(self.manifest_data)
        for where in ("file", "edit", "top"):
            with self.subTest(where=where):
                self.manifest_data = copy.deepcopy(original)
                target = {
                    "file": self.manifest_data["files"][0],
                    "edit": self.manifest_data["files"][0]["edits"][0],
                    "top": self.manifest_data,
                }[where]
                target["note"] = "x"
                self._assert_input_error()

    def test_wrong_types_are_input_error(self) -> None:
        # repo はケースで変えないので組み直さず、manifest だけを毎回元に戻す
        original = copy.deepcopy(self.manifest_data)
        cases = {
            "new": lambda d: d["files"][0]["edits"][0].__setitem__("new", 1),
            "subs": lambda d: d.__setitem__("substitutions", {"NNNN": 192}),
            "edits": lambda d: d["files"][0].__setitem__("edits", {}),
            "digest": lambda d: d.__setitem__("digest", None),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                self.manifest_data = copy.deepcopy(original)
                mutate(self.manifest_data)
                self._assert_input_error()

    def test_git_unavailable_is_input_error(self) -> None:
        empty = self.root / "empty-bin"
        empty.mkdir()
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "verify", "--design", str(self.design), "--manifest",
             str(self.manifest), "--repo", str(self.repo)],
            capture_output=True, text=True, timeout=60, env={"PATH": str(empty)},
        )
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("confirmed-text: ERROR:", r.stderr)

    def test_empty_section_end_is_input_error(self) -> None:
        self.manifest_data["section_end"] = ""
        self._assert_input_error()

    def test_unexpected_exception_is_input_error(self) -> None:
        self.manifest_data["files"][0]["path"] = "docs/\u0000x.md"
        self._assert_input_error()

    def test_path_spellings_are_input_error(self) -> None:
        # repo はケースで変えないので組み直さず、manifest だけを毎回元に戻す
        original = copy.deepcopy(self.manifest_data)
        # 実物は同じファイルに届く綴りでも、正規形でなければ照合しない（綴りの検査が無いと SAME になる）
        for path in ("<abs>", "docs/../docs/new.md", "./docs/new.md", "docs//new.md", "docs\\new.md", ""):
            with self.subTest(path=path):
                self.manifest_data = copy.deepcopy(original)
                new = self.repo / "docs" / "new.md"
                new.write_bytes(b"new\n")
                rel = str(new) if path == "<abs>" else path
                self.manifest_data["files"].append({"path": rel, "content": "new\n"})
                self.assertIn("正規形", self._assert_input_error().stderr)

    def test_case_variant_of_base_file_is_input_error(self) -> None:
        # base にある docs/adr/... を大文字違いで新しいファイルとして書き、弱い比較に逃がさない
        _git(self.repo, "checkout", "-q", "-b", "y", self.base)
        (self.repo / "docs" / "adr").mkdir(exist_ok=True)
        (self.repo / "docs" / "adr" / "0192-x.md").write_bytes(ADR_ACTUAL.encode("utf-8"))
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-qm", "adr at base")
        self.manifest_data["files"][1]["path"] = "Docs/adr/0192-x.md"
        self._write_manifest()
        r = self.verify("--base", _git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("confirmed-text: ERROR:", r.stderr)

    def test_duplicate_path_by_case_is_input_error(self) -> None:
        # 大文字小文字だけが違う同じファイルを 2 回宣言し、別々の比べ方に逃がさない
        self.manifest_data["files"].append({"path": "docs/adr/0192-X.md", "content": ADR_ACTUAL})
        self._assert_input_error()

    def test_referencing_noverify_block_is_input_error(self) -> None:
        self.manifest_data["files"][0]["edits"][2]["new"] = "- 最後の行。直した\n{{D-3#1}}\n"
        self._assert_input_error()

    def test_literal_braces_are_not_block_references(self) -> None:
        self.manifest_data["files"][1] = {
            "path": "docs/adr/0192-x.md",
            "content": ADR_ACTUAL.replace("## Decision\n\n- (1) ADR-0192 の決定を書く\n", "{{D-1#1}}\n")
            .replace("- なし\n", "- なし ${{ secrets.X }}\n"),
        }
        self._write_manifest()
        self.adr.write_bytes(ADR_ACTUAL.replace("- なし\n", "- なし ${{ secrets.X }}\n").encode("utf-8"))
        r = self.verify()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class ImportFailureTest(unittest.TestCase):
    def _run_copy(self, lib_source: str | None) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "scripts" / "confirmed-text.py"
            copy.parent.mkdir()
            copy.write_bytes(SCRIPT.read_bytes())
            if lib_source is not None:
                lib = Path(tmp) / "hooks" / "scripts" / "lib"
                lib.mkdir(parents=True)
                (lib / "tasklist_parse.py").write_text(lib_source, encoding="utf-8")
            env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            return subprocess.run(
                [sys.executable, str(copy), "digest", "--design", "x"], capture_output=True, text=True, env=env
            )

    def test_script_without_tasklist_parse_exits_2(self) -> None:
        r = self._run_copy(None)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("confirmed-text: ERROR: tasklist_parse", r.stderr)

    def test_broken_tasklist_parse_exits_2(self) -> None:
        r = self._run_copy("raise RuntimeError('boom')\n")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("confirmed-text: ERROR: tasklist_parse", r.stderr)


class FenceParityTest(unittest.TestCase):
    """フェンスの内外の判定が、design.md を読むほかの検査の正本（tasklist_parse）と一致する。"""

    DOCS = [
        f"a\n{FENCE}\nb\n{FENCE}\nc",
        f"- x\n\n  {FENCE}md\n## h\n  {FENCE}\nd",
        f"{FENCE}a`b\n## h\n{FENCE}\ne\n{FENCE}",
        f"~~~~\n{FENCE}\n~~~\n~~~~\nf",
        f"````md\n{FENCE}\n{FENCE} x\n````\ng",
        f"\t{FENCE}\n\t{FENCE}\nh",
        f"{FENCE}\n{FENCE} x\n{FENCE}\ny",
        f"{FENCE}\n````\nz",
    ]

    def test_outside_lines_match_scan_fences(self) -> None:
        import importlib.util

        sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))
        try:
            from tasklist_parse import _scan_fences
        finally:
            sys.path.pop(0)
        spec = importlib.util.spec_from_file_location("confirmed_text", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for doc in self.DOCS:
            with self.subTest(doc=doc):
                lines, closed, open_at, _ = _scan_fences(doc)
                inside = set(closed) | (set(range(open_at, len(lines))) if open_at >= 0 else set())
                want = [i not in inside for i in range(len(lines))]
                self.assertEqual(mod.outside_fences(doc.split("\n")), want)


class UntilManifestTest(_Fixture):
    def test_manifest_section_end_is_used_by_verify(self) -> None:
        design = DESIGN.replace("### D-3 比較の対象外\n", "## 節の中の見出し\n\n### D-3 比較の対象外\n")
        self.design.write_text(design, encoding="utf-8")
        self.manifest_data["digest"] = _section_digest(design)[0]
        self.manifest_data["section_end"] = "## advisory の扱い"
        self._write_manifest()
        r = self.verify()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("照合しない block（noverify）: D-3#1", r.stdout)


class NewFileTest(_Fixture):
    def test_content_entry_compares_whole_new_file(self) -> None:
        self.manifest_data["files"][1] = {
            "path": "docs/adr/0192-x.md",
            "content": ADR_ACTUAL.replace(
                "## Decision\n\n- (1) ADR-0192 の決定を書く\n", "{{D-1#1}}\n"
            ),
        }
        self._write_manifest()
        r = self.verify()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.adr.write_bytes(ADR_ACTUAL.replace("- なし\n", "- なし\n- 足した\n").encode("utf-8"))
        self.assertEqual(self.verify().returncode, 1)

    def test_content_entry_for_file_present_at_base_is_input_error(self) -> None:
        self.manifest_data["files"][0] = {"path": "docs/plan.md", "content": "x"}
        self._write_manifest()
        r = self.verify()
        self.assertEqual(r.returncode, 2)
        self.assertIn("confirmed-text: ERROR:", r.stderr)


if __name__ == "__main__":
    unittest.main()
