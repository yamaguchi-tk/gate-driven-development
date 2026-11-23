"""Stop hook の進捗件数・進捗表示・Resume From を bind 解決で読む契約テスト（AC-5 後半 / AC-7 / CT-4）。

進捗の件数が done guard と一致すること、受理面の差分検査、進捗表示と Resume From の
読み取りが bind 済み steering に限られることを固定する。
`test_stop_hook_bind_resolution_contract.py` から分けた。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_progress_bind_scope_contract.py -q
  python3 -m unittest tests.test_stop_hook_progress_bind_scope_contract
"""
from __future__ import annotations

import itertools
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import load_plugin_module  # noqa: E402
from _stop_hook_test_base import (  # noqa: E402
    _bind,
    _make_transcript_jsonl,
    _make_two_worktree_fixture,
    _run_hook,
    _write_state_file,
)


class ProgressCountTests(unittest.TestCase):
    """進捗表示（`_count_task_progress`）が done guard と同じ件数を出す。

    片方だけ fence / 行頭を扱うと、guard は未完了が多いと言うのに、
    進捗表示はほとんど完了と出る、という食い違いが出る（実測）。
    """

    def test_progress_ignores_fenced_and_indented_task_like_lines(self):
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        tasklist = textwrap.dedent(
            """\
            # Tasklist
            ## Current Task

            ### Task: T-3 実装中

            - 例:
                 - T1 | AC-01 | still open

            ```
            - T9 | AC-09 | fenced
            ### Task: T-98 fenced
            ```

            ## Pending Tasks

            ### Task: T-4 次

            ## Completed Tasks

            ### Task: T-1 済み
            ### Task: T-2 済み
            """
        )
        progress = module._count_task_progress(tasklist)
        self.assertIn("tasks: 2/4 done", progress)
        self.assertIn("T-3 実装中", progress)

    def test_progress_counts_tasks_with_trailing_whitespace(self):
        """**末尾**の空白でタスクを落とさない（guard 側の F-1 と同じ型）。

        行頭要求を `line != line.strip()` で書くと末尾も落ちるため、
        末尾に空白 1 つあるだけのタスクが数から漏れて進捗が過少になる。
        guard 側だけ pin しても進捗側は素通りする（変異注入で実測）。
        """
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        for label, suffix in (("space", " "), ("tab", "\t"), ("none", "")):
            with self.subTest(trailing=label):
                tasklist = (
                    "# Tasklist\n## Current Task\n"
                    f"### Task: T-3 実装中{suffix}\n\n"
                    "## Pending Tasks\n"
                    f"### Task: T-4 次{suffix}\n\n"
                    "## Completed Tasks\n"
                    f"### Task: T-1 済み{suffix}\n"
                    f"### Task: T-2 済み{suffix}\n"
                )
                progress = module._count_task_progress(tasklist)
                self.assertIn("tasks: 2/4 done", progress)


# ===========================================================================
# T-4: progress counter / progress text / resume-from を bind 解決へ差し替える
# （AC-5 後半「受理面の定義は共有関数 1 本に集約され、`gdd_stop_hook.py` 内に
#   重複定義が残らない」/ AC-7 / CT-4）
# ===========================================================================

_TASKLIST_PARSE = load_plugin_module("hooks/scripts/lib/tasklist_parse.py")


def _progress_line_product() -> list[str]:
    """進捗カウンタの受理面を測る境界の直積。

    次元は `tests/test_tasklist_parse_contract.py::BashReaderEquivalenceTests` の
    `_boundary_product()` と**同じ 4 次元**（空白の位置 / 空白の繰り返し数 / 採番の桁数 /
    末尾の形）に、`- T<n> | ...` 形の族（bullet / ID / 後続）を足したもの。
    見出し形だけだと `_count_task_progress` のもう 1 本の重複定義
    （`re.match(r'^- T-?\\d', ...) and "|" in ...`）を一切変異検出できない。

    **振っていない次元への変異は素通りする**（空白 3 個以上、5 桁採番、非 ASCII 空白）。
    受理面を変えるときはこの関数の次元定義自体を見直すこと。
    """
    bullets = ["#", "##", "###", "####", "#####", "-", "*", "+"]
    seps = ["", " ", "  ", "\t"]
    words = ["Task", "task", "TASK", "Tasks", "Task ID"]
    nums = ["", "1", "12", "007", "1234"]
    tails = ["", ":", ": x", ":  "]
    heading = {
        b + s1 + w + s2 + n + s3 + t
        for b, s1, w, s2, n, s3, t in itertools.product(
            bullets, seps, words, seps, nums, seps, tails
        )
    }
    item_bullets = ["-", "*", "+", "--", "- "]
    ids = ["T", "T1", "T-1", "T12", "t1", "T-helper", "T007"]
    rests = [" | AC-01 | desc", " |", "| x", " の作業を完了した", ""]
    items = {b + i + r for b, i, r in itertools.product(item_bullets, ids, rests)}
    return sorted(heading | items)


def _progress_verdict(module, line: str) -> tuple[bool, str]:
    """1 行だけの `## Current Task` に対する `_count_task_progress` の判定を返す。

    返り値は `(タスクとして数えたか, 表示された名前)`。この関数は集計しか返さないので、
    **1 行 = 1 呼び出し**にすることで行単位の differential にできる。
    """
    progress = module._count_task_progress("# Tasklist\n## Current Task\n" + line + "\n")
    if not progress:
        return False, ""
    if "current: " in progress:
        return True, progress.split("current: ", 1)[1]
    return True, ""


class ProgressAcceptanceSurfaceDifferentialTests(unittest.TestCase):
    """AC-5 / CT-4: 進捗カウンタの受理面 = `lib/tasklist_parse` の受理面。

    一点 pin を足す方式は本 PR で 3 attempt 続けて破られた（T-1 の
    `BashReaderEquivalenceTests` の経緯）。ここでも列挙をやめ、**境界の直積を
    `_count_task_progress` と共有関数の両方に通して突き合わせる**。
    片側だけ変異させれば（生成した形の範囲で）必ず落ちる = 両側 pin。
    """

    def test_progress_counter_matches_the_shared_acceptance_surface(self):
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        product = _progress_line_product()
        # `## ` で始まる行は **section の reset**（`## Completed Tasks` 等と同じ入口）で、
        # done guard 側も `line.startswith("## ")` で同じ扱いをする。受理面の話ではないので
        # 差分の対象から外す。外した側は次の test が両 reader で pin する。
        scope = [line for line in product if not line.startswith("## ")]

        # hollow check: 生成集合が空・片側だけになったら differential は何も測らずに緑になる。
        # 生成集合の件数は固定せず、両側があることだけを見る
        self.assertTrue(scope, "differential の母集合が空")
        self.assertGreater(len(product), len(scope), "`## ` の行（差分から外す族）が生成されていない")
        expected_tasks = [
            line for line in scope
            if _TASKLIST_PARSE.classify_task_line(line.strip()) == "task"
        ]
        self.assertEqual(len(expected_tasks), 1362, "共有受理面の受理数が変わった（意図した変更なら実測し直す）")
        self.assertGreater(len(scope), len(expected_tasks), "共有受理面が受理しない行が生成されていない")

        mismatches = []
        for line in scope:
            stripped = line.strip()
            expected = (
                _TASKLIST_PARSE.classify_task_line(stripped) == "task",
                _TASKLIST_PARSE.task_name(stripped),
            )
            actual = _progress_verdict(module, line)
            if expected != actual:
                mismatches.append((line, expected, actual))
        self.assertEqual(
            mismatches[:10], [], f"共有受理面と食い違う形 {len(mismatches)} 件"
        )

    def test_h2_task_headings_are_a_section_reset_in_both_readers(self):
        """差分から外した `## ` 族を、外した理由ごと両 reader で固定する。

        `## Task 3: 説明` は共有受理面では `task` だが、進捗カウンタも done guard も
        **section の切り替わり**として読む（`## ` で始まる行は既知の 3 見出し以外
        すべて section を抜ける）。片方だけ「タスク」に変えると、guard が数える件数と
        進捗表示の件数が再び割れる ―― T-3 が潰した非対称の作り直しになる。
        """
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        heading = "## Task 3: 説明"
        self.assertEqual(_TASKLIST_PARSE.classify_task_line(heading), "task")
        self.assertEqual(_progress_verdict(module, heading), (False, ""))

        tasklist = textwrap.dedent(
            """\
            # Tasklist
            ## Current Task
            ## Task 3: 説明

            ## Pending Tasks
            - なし

            ## Completed Tasks
            - なし

            ## Verification
            | method | status | evidence | notes |
            |---|---|---|---|
            | method=ac:AC-01 | pass | ok | - |
            """
        )
        # 維持: 本テストの主張は `## ` 見出しの section reset 判定であり
        # Verification 文法とは無関係。canonical 全 pass は allow のまま
        # （design.md § 5「不変」）なので canonical 化のみで RED が解消する
        # （Category A2）。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            steering = root / ".steering" / "20260822-target"
            steering.mkdir(parents=True)
            (steering / "tasklist.md").write_text(tasklist, encoding="utf-8")
            module._BIND_CACHE.clear()
            module._BIND_CACHE[str(module._worktree_toplevel(root))] = module.BindResult(
                status="resolved", steering_dir=steering, candidates=[]
            )
            try:
                is_valid, error_msg, _checked = module.validate_done_preconditions(root)
            finally:
                module._BIND_CACHE.clear()
        self.assertTrue(is_valid, f"done guard 側が `## ` を task として数えている: {error_msg}")

    def test_no_second_definition_of_the_acceptance_surface_remains(self):
        """CT-4: `gdd_stop_hook.py` に受理面の重複定義が残らない（機械検査）。

        測るのは**コメントを除いたソース**。コメントで受理面に言及するのは
        （lib への参照として）残ってよいが、判定そのものを持ち直すと
        「2 つの reader が見出しの形について食い違う」という本 PR が閉じている
        欠陥が復活する。現状の重複は 2 箇所（`startswith("### Task:")` と
        `replace("### Task:", "")`、いずれも `_count_task_progress` 内）。
        """
        source = (
            Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "gdd_stop_hook.py"
        ).read_text(encoding="utf-8")
        code = "\n".join(
            line for line in source.splitlines() if not line.lstrip().startswith("#")
        )
        for token in ('"### Task:"', "'### Task:'", "^- T-?", "^- T-\\?"):
            with self.subTest(token=token):
                hits = [
                    f"{n}: {line.strip()}"
                    for n, line in enumerate(code.splitlines(), 1)
                    if token in line
                ]
                self.assertEqual(
                    hits, [],
                    "受理面の重複定義が残っている（lib/tasklist_parse に集約すること）",
                )


class ProgressTextBindScopeTests(unittest.TestCase):
    """AC-7: 進捗表示の根拠は bind 済み steering。他 worktree を漁らない。

    現行 `_find_tasklist_text_for_progress()` は `git worktree list --porcelain` を
    順に舐め、**最初に `.steering` を持つ worktree**（= 他人の wtA）の tasklist を
    そのまま読む。誤バインドの block は T-3 で塞いだが、**表示だけは他人の進捗**という
    状態が残っており、継続ターンの `[GDD #N]` に他タスクの件数と名前が載る。
    """

    _FOREIGN_TASKLIST = textwrap.dedent(
        """\
        # Tasklist
        ## Current Task
        ### Task: FOREIGN-A よその作業

        ## Pending Tasks
        - なし

        ## Completed Tasks
        - なし
        """
    )
    _TARGET_TASKLIST = textwrap.dedent(
        """\
        # Tasklist
        ## Current Task
        ### Task: TARGET-B 自分の作業

        ## Pending Tasks
        ### Task: TARGET-C 次

        ## Completed Tasks
        ### Task: TARGET-D 済み
        """
    )

    def _fixture(self, tmp: Path) -> tuple[Path, Path]:
        wtA, wtB = _make_two_worktree_fixture(tmp)
        (wtA / ".steering" / "20260101-foreign" / "tasklist.md").write_text(
            self._FOREIGN_TASKLIST, encoding="utf-8"
        )
        (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
            self._TARGET_TASKLIST, encoding="utf-8"
        )
        return wtA, wtB

    def _continuation(self, wtB: Path) -> tuple[int, str, str]:
        _write_state_file(
            wtB, {"active": "true", "session_id": "test-session", "iteration": "1"}
        )
        transcript = wtB / "transcript.jsonl"
        _make_transcript_jsonl(
            transcript,
            assistant_text="<gdd-phase>gdd-test-driven-development</gdd-phase>\n作業中。",
            user_text="続けて",
        )
        return _run_hook(wtB, transcript, session_id="test-session")

    def test_progress_text_comes_from_the_bound_steering(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = self._fixture(Path(tmp))
            _bind(wtB)
            _code, out, err = self._continuation(wtB)
            sys_msg = json.loads(out.strip())["systemMessage"]
            # **件数と名前の両方**を固定する。名前だけだと件数が他人由来のままでも通る。
            self.assertIn("tasks: 1/3 done", sys_msg, f"out={out}\nerr={err}")
            self.assertIn("current: TARGET-B 自分の作業", sys_msg)
            self.assertNotIn("FOREIGN", out + err)
            self.assertNotIn("20260101-foreign", out + err)

    def test_progress_text_never_reads_a_foreign_worktree_when_unbound(self):
        """bind 不能でも他 worktree は根拠にしない（自分の worktree の steering に留まる）。

        ここで「bind 不能なら進捗を出さない」にしないのは、出荷済みの
        `tests/test_stop_hook_e2e_block_content.py::...::test_continuation_block_includes_task_progress`
        が **binding.json の無い workspace** で `tasks: 1/3 done` を要求しているため。
        AC-7 が禁じているのは「他 worktree / 無関係 steering」であって、
        自分の worktree の steering ではない。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = self._fixture(Path(tmp))
            # binding.json を書かない
            _code, out, err = self._continuation(wtB)
            sys_msg = json.loads(out.strip())["systemMessage"]
            self.assertIn("tasks: 1/3 done", sys_msg, f"out={out}\nerr={err}")
            self.assertIn("current: TARGET-B 自分の作業", sys_msg)
            self.assertNotIn("FOREIGN", out + err)

    def test_find_tasklist_text_for_progress_ignores_other_worktrees(self):
        """関数単体でも両ケース（bind 済み / 不能）を固定する。"""
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = self._fixture(Path(tmp))
            module._BIND_CACHE.clear()
            try:
                unbound = module._find_tasklist_text_for_progress(wtB)
                self.assertIn("TARGET-B", unbound)
                self.assertNotIn("FOREIGN-A", unbound)
                _bind(wtB)
                module._BIND_CACHE.clear()
                bound = module._find_tasklist_text_for_progress(wtB)
                self.assertIn("TARGET-B", bound)
                self.assertNotIn("FOREIGN-A", bound)
            finally:
                module._BIND_CACHE.clear()


class ResumeFromBindScopeTests(unittest.TestCase):
    """AC-7: human-check fallback の `Resume From` も bind 済み steering から読む。

    現行 `latest_steering_resume_from()` は current worktree の `.steering` を
    **名前の降順で 1 件目**だけ見る。同じ worktree に別タスクの steering が
    後から増える（= 名前が新しい）と、bind 済みタスクではなく**無関係な steering**の
    `Resume From: human-check-waiting` で停止する。他 worktree は見ないので bind 限定で塞いだ
    誤 block ではないが、AC-7 の「無関係 steering を human-check fallback の
    根拠にしない」に該当する。
    """

    #: markerless fallback（`<gdd-stop>` 無し）で human-check surface と判定される形。
    #: `## 👤 次にすること` を含めるのは、含めないと fallback が発火した瞬間に
    #: **その手前の OT-F10 guard**（`👤 次にすること` ブロック必須）で block されてしまい、
    #: 「fallback が発火したか」ではなく「👤 ブロックが無いか」を測る test になるため。
    _HITL_SURFACE = (
        "## 確認\n### 判断ポイント\n1. Scope を確認してください。\n承認ポイント: ...\n\n"
        "## 👤 次にすること\n承認してください。\n"
    )
    _PAUSE_MARKER = "GDD session paused (reason=human-check-waiting)"

    def _fixture(self, tmp: Path, *, bound_resume: str) -> tuple[Path, Path]:
        """wtB に steering 2 つ。bind 対象は名前が**古い**方（降順走査で 2 番目）。"""
        wtA, wtB = _make_two_worktree_fixture(tmp)
        (wtB / ".steering" / "20260822-target" / "state.md").write_text(
            f"# State\n\n## Gate Status\n- Resume From: {bound_resume}\n", encoding="utf-8"
        )
        unrelated = wtB / ".steering" / "20260901-unrelated"
        unrelated.mkdir(parents=True)
        (unrelated / "state.md").write_text(
            "# State\n\n## Gate Status\n- Resume From: human-check-waiting\n",
            encoding="utf-8",
        )
        return wtA, wtB

    def _run(self, wtB: Path) -> tuple[int, str, str]:
        _write_state_file(
            wtB, {"active": "true", "session_id": "test-session", "iteration": "1"}
        )
        transcript = wtB / "transcript.jsonl"
        _make_transcript_jsonl(transcript, assistant_text=self._HITL_SURFACE)
        return _run_hook(wtB, transcript, session_id="test-session")

    def test_resume_from_uses_the_bound_steering_not_the_newest_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = self._fixture(Path(tmp), bound_resume="gdd-implementation-gating")
            _bind(wtB)
            _code, out, err = self._run(wtB)
            self.assertNotIn(
                self._PAUSE_MARKER, err,
                f"無関係 steering の human-check-waiting で停止している\nout={out}\nerr={err}",
            )
            self.assertNotIn("20260901-unrelated", out + err)

    def test_bound_steering_human_check_waiting_still_pauses(self):
        """positive control: bind 済み steering が human-check-waiting なら従来どおり止まる。

        これが無いと「fallback を丸ごと殺す」実装でも上の test が緑になる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = self._fixture(Path(tmp), bound_resume="human-check-waiting")
            _bind(wtB)
            _code, out, err = self._run(wtB)
            self.assertIn(self._PAUSE_MARKER, err, f"out={out}\nerr={err}")

    def test_fenced_resume_from_example_does_not_pause(self):
        """fenced code block の記入例で停止しないこと。

        `Resume From` を読む実装は複数あり、この 1 本だけが fence 非対応だと、
        同じ state.md に対して stop hook だけ別の値で routing する
        （読み手の正本規約は tests/test_canonical_field_line_anchoring_contract.py）。
        """
        fence = chr(96) * 3
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = self._fixture(Path(tmp), bound_resume="gdd-implementation-gating")
            (wtB / ".steering" / "20260822-target" / "state.md").write_text(
                "# State\n\n## Gate Status\n"
                f"記入例:\n{fence}\n- Resume From: human-check-waiting\n{fence}\n"
                "- Resume From: gdd-implementation-gating\n",
                encoding="utf-8",
            )
            _bind(wtB)
            _code, out, err = self._run(wtB)
            self.assertNotIn(
                self._PAUSE_MARKER, err,
                f"fence 内の記入例で停止している\nout={out}\nerr={err}",
            )

    def test_unbound_still_falls_back_to_the_own_worktree_steering(self):
        """positive control: bind 不能時の current-worktree fallback は残す。

        出荷済みの `tests/test_stop_hook_e2e.py::TestHookE2EFallback3SteeringResumeFrom`
        3 本が binding.json 無しでこの fallback を要求している。bind 済みだけを見る
        実装に倒すと、markerless recovery が無言で消える。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, wtB = _make_two_worktree_fixture(Path(tmp))
            (wtB / ".steering" / "20260822-target" / "state.md").write_text(
                "# State\n\n## Gate Status\n- Resume From: human-check-waiting\n",
                encoding="utf-8",
            )
            # binding.json を書かない
            _code, out, err = self._run(wtB)
            self.assertIn(self._PAUSE_MARKER, err, f"out={out}\nerr={err}")
            self.assertNotIn("20260101-foreign", out + err)


if __name__ == "__main__":
    unittest.main()
