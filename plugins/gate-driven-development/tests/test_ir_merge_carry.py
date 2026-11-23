"""`Independent Review Carry`（main を取り込むだけの merge commit への独立レビューの引き継ぎ）のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_ir_merge_carry.py -q`

正本: `references/self-review-lanes.md` § Independent Review の引き継ぎ。レビュー済みの tip に
default branch を merge した commit で、gate が git から次を確かめられたときだけ、旧 sha の
`Independent Review` を merge commit のものとして扱う。

- 第 1 親が `Independent Review` の sha（= Carry の `from`）、第 2 親が default branch の祖先
- 条件の番号は正本の (1)〜(7)。依頼の (a) は (4)、(b) は (5)、(c) は (7) に当たる

pre-PR gate・pre-push gate・検算スクリプト（`scripts/check-gate-ledger.sh`）の 3 つが同じ判定を
するかを、`test_check_gate_ledger.py` の fixture で 1 回に確かめる。
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from _merge_gate_support import HANG_GUARD
from test_check_gate_ledger import GateLedgerFixture, _git, _status

CARRY_AT = "2026-10-13T00:00:00Z"
# PR #1328 の形: 両側が索引に 1 行ずつ足し、両方を残して解消する
RESOLVED_README = "test\n- feature\n- main\n"


class MergeCarryFixture(GateLedgerFixture):
    """feature（レビュー済みの tip）に main を merge し、Carry 行を書いた steering を作る。"""

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        # hook は shell の起動からの経過（bash の SECONDS）で持ち時間を測る。bash は環境変数の
        # SECONDS を起動時の値として取り込むので、負の値で、混んだマシンで前段にかかる時間を
        # 差し引く（引き継ぎの判定そのものの上限 5 秒は残る）
        self.extra_env["SECONDS"] = "-120"
        # feature 側: 索引（README.md）に 1 行足す。ここまでがレビュー済み
        (self.repo / "README.md").write_text("test\n- feature\n", encoding="utf-8")
        _git(self.repo, "commit", "-q", "-am", "feature index")
        self.reviewed = _git(self.repo, "rev-parse", "HEAD")
        self.state["Independent Review"] = (
            f"{self.reviewed} | reviewer: light-lane-independent-reviewer | context: diff-only "
            "| high: 0 | medium: 0 | blocking: 0 | at: 2026-10-02T00:00:00Z"
        )

    def advance_main(self, *, conflict: bool = True) -> None:
        _git(self.repo, "switch", "-q", "main")
        (self.repo / "main.txt").write_text("main\n", encoding="utf-8")
        _git(self.repo, "add", "main.txt")
        if conflict:
            (self.repo / "README.md").write_text("test\n- main\n", encoding="utf-8")
            _git(self.repo, "add", "README.md")
        _git(self.repo, "commit", "-q", "-m", "main moves")
        # 審査済みの default branch は remote-tracking の ref で見る（local の main は見ない）
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "main")
        _git(self.repo, "switch", "-q", "feature")

    def merge(
        self,
        source: str = "main",
        *,
        resolution: str = RESOLVED_README,
        extra: dict[str, str] | None = None,
    ) -> str:
        """`source` を feature に merge する。衝突したら README.md を `resolution` で解消する。

        `extra` は merge commit に混ぜる追加の変更（ファイル名 → 内容）。
        """
        subprocess.run(
            ["git", "-C", str(self.repo), "merge", "-q", "--no-ff", "--no-commit", source],
            capture_output=True, text=True, check=False,
        )
        conflicted = _git(self.repo, "diff", "--name-only", "--diff-filter=U")
        if "README.md" in conflicted.split():
            (self.repo / "README.md").write_text(resolution, encoding="utf-8")
            _git(self.repo, "add", "README.md")
        for name, body in (extra or {}).items():
            (self.repo / name).write_text(body, encoding="utf-8")
            _git(self.repo, "add", name)
        _git(self.repo, "commit", "-q", "--no-edit")
        merge = _git(self.repo, "rev-parse", "HEAD")
        self.set_tip(merge)
        return merge

    def add_base_file(self, name: str, body: str) -> None:
        """default branch に `name` を足して feature に取り込み、その後の feature の変更を待つ。"""
        _git(self.repo, "switch", "-q", "main")
        (self.repo / name).write_text(body, encoding="utf-8")
        _git(self.repo, "add", name)
        _git(self.repo, "commit", "-q", "-m", f"add {name}")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "main")
        _git(self.repo, "switch", "-q", "feature")
        _git(self.repo, "merge", "-q", "--no-edit", "main")

    def review_here(self) -> None:
        """今の feature の HEAD をレビュー済みにする。"""
        self.reviewed = _git(self.repo, "rev-parse", "HEAD")
        self.state["Independent Review"] = self.state["Independent Review"].replace(
            self.state["Independent Review"].split(" | ", 1)[0], self.reviewed
        )

    def main_edits(self, name: str, body: str) -> None:
        _git(self.repo, "switch", "-q", "main")
        (self.repo / name).write_text(body, encoding="utf-8")
        _git(self.repo, "commit", "-q", "-am", f"main edits {name}")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "main")
        _git(self.repo, "switch", "-q", "feature")

    def merge_resolving(self, name: str, body: str) -> str:
        subprocess.run(
            ["git", "-C", str(self.repo), "merge", "-q", "--no-ff", "--no-commit", "main"],
            capture_output=True, text=True, check=False,
        )
        if body is None:
            _git(self.repo, "rm", "-q", name)
        else:
            (self.repo / name).write_text(body, encoding="utf-8")
            _git(self.repo, "add", name)
        _git(self.repo, "commit", "-q", "--no-edit")
        merge = _git(self.repo, "rev-parse", "HEAD")
        self.set_tip(merge)
        return merge

    def set_tip(self, sha: str, *, carry_from: str | None = None, verified: str = "diff-equal") -> None:
        """Self Review は tip の sha で書き直し、Independent Review は旧 sha のまま Carry 行を足す。"""
        self.head = sha
        self.state["Pre-PR Self Review"] = self.state["Pre-PR Self Review"].replace(
            self.state["Pre-PR Self Review"].split(" | ", 1)[0], sha
        )
        self.state["Pre-Push Self Review"] = self.state["Pre-PR Self Review"]
        self.state["Independent Review Carry"] = (
            f"{sha} | from: {carry_from or self.reviewed} | verified: {verified} | at: {CARRY_AT}"
        )


class IndependentReviewCarryTests(unittest.TestCase):
    def _run(self, build):
        with tempfile.TemporaryDirectory() as tmp:
            fx = MergeCarryFixture(Path(tmp))
            build(fx)
            fx.write()
            code, rows = fx.ledger()
            return fx.pre_pr_blocks(), fx.pre_push_blocks(), code, rows

    def assert_carried(self, build) -> None:
        pr_blocks, push_blocks, code, rows = self._run(build)
        self.assertFalse(pr_blocks, rows)
        self.assertFalse(push_blocks, rows)
        self.assertEqual(_status(rows, "independent-review"), ["ok"], rows)
        self.assertEqual(code, 0, rows)

    def assert_not_carried(self, build) -> None:
        pr_blocks, push_blocks, code, rows = self._run(build)
        self.assertTrue(pr_blocks, rows)
        self.assertTrue(push_blocks, rows)
        self.assertEqual(_status(rows, "independent-review"), ["invalid"], rows)
        self.assertEqual(code, 1, rows)

    # ---- 引き継ぐ側 ----

    def test_clean_merge_is_carried(self) -> None:
        def build(fx):
            fx.advance_main(conflict=False)
            fx.merge()
        self.assert_carried(build)

    def test_one_line_index_conflict_is_carried(self) -> None:
        """PR #1328 の形（索引の 1 行の衝突を、両方の行を残して解消）。"""
        def build(fx):
            fx.advance_main()
            fx.merge()
        self.assert_carried(build)

    def test_resolution_at_threshold_is_carried(self) -> None:
        """解消で足した行が閾値（5 行）ちょうどなら引き継ぐ。"""
        extra = "".join(f"- extra {i}\n" for i in range(5))
        def build(fx):
            fx.advance_main()
            fx.merge(resolution=RESOLVED_README + extra)
        self.assert_carried(build)

    # ---- 引き継がない側（今までどおり取り直しを求める）----

    def test_without_carry_line_stays_stale(self) -> None:
        def build(fx):
            fx.advance_main()
            fx.merge()
            fx.state["Independent Review Carry"] = None
        self.assert_not_carried(build)

    def test_resolution_over_threshold_is_not_carried(self) -> None:
        extra = "".join(f"- extra {i}\n" for i in range(6))
        def build(fx):
            fx.advance_main()
            fx.merge(resolution=RESOLVED_README + extra)
        self.assert_not_carried(build)

    def test_conflict_markers_left_are_not_carried(self) -> None:
        markers = "test\n<<<<<<< HEAD\n- feature\n=======\n- main\n>>>>>>> main\n"
        def build(fx):
            fx.advance_main()
            fx.merge(resolution=markers)
        self.assert_not_carried(build)

    def test_separator_line_left_is_not_carried(self) -> None:
        """`<<<<<<<` と `>>>>>>>` だけを消し、区切りの `=======` を残した解消は引き継がない。"""
        def build(fx):
            fx.advance_main()
            fx.merge(resolution="test\n- feature\n=======\n- main\n")
        self.assert_not_carried(build)

    def test_quote_line_added_in_resolution_is_carried(self) -> None:
        """解消で足した行が引用（`> `）でも、マーカーの形でなければ余分な 1 行として引き継ぐ。"""
        def build(fx):
            fx.advance_main()
            fx.merge(resolution="test\n- feature\n> note\n- main\n")
        self.assert_carried(build)

    def test_extra_change_in_clean_file_is_not_carried(self) -> None:
        """衝突していないファイルを merge commit で変えた（evil merge）。"""
        def build(fx):
            fx.advance_main()
            fx.merge(extra={"file.txt": "2\nsneaked\n"})
        self.assert_not_carried(build)

    def test_extra_new_file_in_clean_merge_is_not_carried(self) -> None:
        def build(fx):
            fx.advance_main(conflict=False)
            fx.merge(extra={"new.txt": "new\n"})
        self.assert_not_carried(build)

    def test_dropping_reviewed_lines_in_conflict_is_not_carried(self) -> None:
        """解消で PR の行を落とし、main 側だけを残した（`--theirs` の形）。"""
        def build(fx):
            fx.advance_main()
            fx.merge(resolution="test\n- main\n")
        self.assert_not_carried(build)

    def test_dropping_main_lines_in_conflict_is_not_carried(self) -> None:
        """解消で main の行を落とし、PR 側だけを残した（`--ours` の形）。default branch 側の行が残らないので止まる。"""
        def build(fx):
            fx.advance_main()
            fx.merge(resolution="test\n- feature\n")
        self.assert_not_carried(build)

    def test_moving_reviewed_line_in_clean_file_is_not_carried(self) -> None:
        """衝突していないファイルで、PR が足した行を merge commit で別の位置へ動かした。

        `-U0` の変更行は両側で `+X` の 1 行になり、差分の比較だけでは一致する。自動 merge の
        tree との比較で止める。
        """
        def build(fx):
            _git(fx.repo, "switch", "-q", "main")
            (fx.repo / "list.txt").write_text("a\nb\nc\nd\ne\nf\n", encoding="utf-8")
            _git(fx.repo, "add", "list.txt")
            _git(fx.repo, "commit", "-q", "-m", "list")
            _git(fx.repo, "switch", "-q", "feature")
            _git(fx.repo, "merge", "-q", "--no-edit", "main")
            (fx.repo / "list.txt").write_text("a\nb\nX\nc\nd\ne\nf\n", encoding="utf-8")
            _git(fx.repo, "commit", "-q", "-am", "insert X")
            fx.reviewed = _git(fx.repo, "rev-parse", "HEAD")
            fx.state["Independent Review"] = fx.state["Independent Review"].replace(
                fx.state["Independent Review"].split(" | ", 1)[0], fx.reviewed
            )
            fx.advance_main()
            fx.merge(extra={"list.txt": "a\nb\nc\nd\ne\nX\nf\n"})
        self.assert_not_carried(build)

    def test_second_parent_not_on_default_branch_is_not_carried(self) -> None:
        def build(fx):
            _git(fx.repo, "update-ref", "refs/remotes/origin/main", "main")
            _git(fx.repo, "switch", "-q", "-c", "side", "main")
            (fx.repo / "side.txt").write_text("side\n", encoding="utf-8")
            _git(fx.repo, "add", "side.txt")
            _git(fx.repo, "commit", "-q", "-m", "side")
            _git(fx.repo, "switch", "-q", "feature")
            fx.merge("side")
        self.assert_not_carried(build)

    def test_first_parent_not_reviewed_sha_is_not_carried(self) -> None:
        """Independent Review の sha が第 1 親より古い（レビュー後に commit を積んでから merge）。"""
        def build(fx):
            old_review = fx.reviewed
            (fx.repo / "file.txt").write_text("3\n", encoding="utf-8")
            _git(fx.repo, "commit", "-q", "-am", "after review")
            fx.advance_main()
            fx.merge()
            fx.set_tip(fx.head, carry_from=old_review)
        self.assert_not_carried(build)

    def test_carry_from_differs_from_independent_review_sha_is_not_carried(self) -> None:
        def build(fx):
            fx.advance_main()
            fx.merge()
            fx.set_tip(fx.head, carry_from=fx.old)
        self.assert_not_carried(build)

    def test_carry_sha_not_tip_is_not_carried(self) -> None:
        def build(fx):
            fx.advance_main()
            merge = fx.merge()
            (fx.repo / "file.txt").write_text("after merge\n", encoding="utf-8")
            _git(fx.repo, "commit", "-q", "-am", "after merge")
            tip = _git(fx.repo, "rev-parse", "HEAD")
            fx.set_tip(tip)
            fx.state["Independent Review Carry"] = fx.state["Independent Review Carry"].replace(tip, merge)
        self.assert_not_carried(build)

    def test_carry_names_other_sha_than_tip_is_not_carried(self) -> None:
        """tip は引き継げる merge だが、Carry 行が別の sha を名指ししている。"""
        def build(fx):
            fx.advance_main()
            merge = fx.merge()
            fx.state["Independent Review Carry"] = fx.state["Independent Review Carry"].replace(
                merge, fx.reviewed, 1
            )
        self.assert_not_carried(build)

    def test_non_merge_tip_is_not_carried(self) -> None:
        def build(fx):
            (fx.repo / "file.txt").write_text("after review\n", encoding="utf-8")
            _git(fx.repo, "commit", "-q", "-am", "after review")
            fx.set_tip(_git(fx.repo, "rev-parse", "HEAD"))
        self.assert_not_carried(build)

    def test_chained_merge_is_not_carried(self) -> None:
        """2 回目の main の merge は、第 1 親が Independent Review の sha ではない。"""
        def build(fx):
            fx.advance_main()
            fx.merge()
            _git(fx.repo, "switch", "-q", "main")
            (fx.repo / "main2.txt").write_text("main2\n", encoding="utf-8")
            _git(fx.repo, "add", "main2.txt")
            _git(fx.repo, "commit", "-q", "-m", "main again")
            _git(fx.repo, "switch", "-q", "feature")
            fx.merge()
        self.assert_not_carried(build)

    def test_criss_cross_merge_is_not_carried(self) -> None:
        """merge-base が 2 つある（main が feature の古い commit を取り込んでいた）。"""
        def build(fx):
            fx.advance_main(conflict=False)
            main_one = _git(fx.repo, "rev-parse", "main")
            _git(fx.repo, "switch", "-q", "main")
            _git(fx.repo, "merge", "-q", "--no-edit", fx.old)
            _git(fx.repo, "update-ref", "refs/remotes/origin/main", "main")
            _git(fx.repo, "switch", "-q", "feature")
            _git(fx.repo, "merge", "-q", "--no-edit", main_one)
            fx.reviewed = _git(fx.repo, "rev-parse", "HEAD")
            fx.state["Independent Review"] = fx.state["Independent Review"].replace(
                fx.state["Independent Review"].split(" | ", 1)[0], fx.reviewed
            )
            fx.merge()
        self.assert_not_carried(build)

    def test_verified_other_value_is_not_carried(self) -> None:
        def build(fx):
            fx.advance_main()
            fx.merge()
            fx.set_tip(fx.head, verified="by-eye")
        self.assert_not_carried(build)

    def test_carry_does_not_hide_high(self) -> None:
        def build(fx):
            fx.advance_main()
            fx.merge()
            fx.state["Independent Review"] = fx.state["Independent Review"].replace("high: 0", "high: 1")
        self.assert_not_carried(build)

    def test_moving_reviewed_line_inside_conflicted_file_is_not_carried(self) -> None:
        """衝突したファイルの中で、衝突していない位置にあった PR の行を別の位置へ動かした。"""
        def build(fx):
            fx.add_base_file("doc.txt", "a\nb\nc\n")
            (fx.repo / "doc.txt").write_text("a\nX\nb\nc1\n", encoding="utf-8")
            _git(fx.repo, "commit", "-q", "-am", "pr edits doc")
            fx.review_here()
            fx.main_edits("doc.txt", "a\nb\nc2\n")
            fx.merge_resolving("doc.txt", "a\nb\nX\nc1\nc2\n")
        self.assert_not_carried(build)

    def test_keeping_both_sides_inside_conflicted_file_is_carried(self) -> None:
        """同じ形で、PR の行を元の位置に残し、衝突した行を両方残した解消は引き継ぐ。"""
        def build(fx):
            fx.add_base_file("doc.txt", "a\nb\nc\n")
            (fx.repo / "doc.txt").write_text("a\nX\nb\nc1\n", encoding="utf-8")
            _git(fx.repo, "commit", "-q", "-am", "pr edits doc")
            fx.review_here()
            fx.main_edits("doc.txt", "a\nb\nc2\n")
            fx.merge_resolving("doc.txt", "a\nX\nb\nc1\nc2\n")
        self.assert_carried(build)

    def test_binary_attribute_text_conflict_is_not_carried(self) -> None:
        """`.gitattributes` で diff を切ったテキストの衝突を、片側に寄せて解消した。"""
        def build(fx):
            info = fx.repo / ".git" / "info"
            info.mkdir(exist_ok=True)
            (info / "attributes").write_text("README.md -diff\n", encoding="utf-8")
            fx.advance_main()
            fx.merge(resolution="test\n- main\n")
        self.assert_not_carried(build)

    def test_conflicted_file_deleted_in_merge_is_not_carried(self) -> None:
        def build(fx):
            fx.advance_main()
            fx.merge_resolving("README.md", None)
        self.assert_not_carried(build)

    def test_binary_conflict_is_not_carried(self) -> None:
        def build(fx):
            fx.add_base_file("blob.bin", "a\0b\n")
            (fx.repo / "blob.bin").write_bytes(b"a\0pr\n")
            _git(fx.repo, "commit", "-q", "-am", "pr edits blob")
            fx.review_here()
            fx.main_edits("blob.bin", "a\0main\n")
            fx.merge_resolving("blob.bin", "a\0pr\n")
        self.assert_not_carried(build)

    def test_line_added_at_head_of_conflicted_file_is_not_carried(self) -> None:
        """衝突したファイルの、衝突の外（先頭）に行を足した。"""
        def build(fx):
            fx.advance_main()
            fx.merge(resolution="sneaked\n" + RESOLVED_README)
        self.assert_not_carried(build)

    def test_line_added_at_tail_of_conflicted_file_is_not_carried(self) -> None:
        """衝突したファイルの末尾が衝突の外にあるときに、その後ろへ行を足した。"""
        def build(fx):
            fx.add_base_file("doc.txt", "a\nb\nc\nd\n")
            (fx.repo / "doc.txt").write_text("a\nb1\nc\nd\n", encoding="utf-8")
            _git(fx.repo, "commit", "-q", "-am", "pr edits doc")
            fx.review_here()
            fx.main_edits("doc.txt", "a\nb2\nc\nd\n")
            fx.merge_resolving("doc.txt", "a\nb1\nb2\nc\nd\nsneaked\n")
        self.assert_not_carried(build)

    def test_zdiff3_conflict_style_is_carried(self) -> None:
        """repo の merge.conflictStyle が zdiff3 でも、判定は 2 方向のマーカーで読む。"""
        def build(fx):
            _git(fx.repo, "config", "merge.conflictStyle", "zdiff3")
            fx.advance_main()
            fx.merge()
        self.assert_carried(build)

    # ---- 判定できないときに通さない（安全策 2）----

    def test_git_failure_is_not_carried(self) -> None:
        """`git merge-tree` が失敗する git では引き継がない（例外で通さない）。"""
        def build(fx):
            fx.advance_main()
            fx.merge()
            shim = fx.root / "shim"
            shim.mkdir()
            real_git = subprocess.run(
                ["/bin/sh", "-c", "command -v git"], capture_output=True, text=True, check=True
            ).stdout.strip()
            script = shim / "git"
            script.write_text(
                "#!/bin/sh\n"
                'for a in "$@"; do [ "$a" = merge-tree ] && exit 128; done\n'
                f'exec "{real_git}" "$@"\n',
                encoding="utf-8",
            )
            script.chmod(script.stat().st_mode | stat.S_IXUSR)
            fx.extra_env["PATH"] = f"{shim}{os.pathsep}{os.environ['PATH']}"
        self.assert_not_carried(build)

    def test_hook_out_of_time_is_not_carried(self) -> None:
        """hook の持ち時間（timeout 10 秒の手前）を使い切っていたら、判定せずに止める。"""
        def build(fx):
            fx.advance_main()
            fx.merge()
            fx.extra_env["SECONDS"] = "9"
        pr_blocks, push_blocks, _code, rows = self._run(build)
        self.assertTrue(pr_blocks, rows)
        self.assertTrue(push_blocks, rows)

    def test_local_default_branch_only_is_not_carried(self) -> None:
        """remote-tracking の default branch が無く、local の main しか無い repo では引き継がない。"""
        def build(fx):
            fx.advance_main()
            fx.merge()
            _git(fx.repo, "update-ref", "-d", "refs/remotes/origin/main")
        self.assert_not_carried(build)


class CarryModuleFailClosedTests(unittest.TestCase):
    """判定の途中の想定外の例外は、引き継がない側（exit 1）に倒す。"""

    def test_unexpected_exception_is_not_carried(self) -> None:
        import importlib.util
        from _paths import PLUGIN_ROOT

        spec = importlib.util.spec_from_file_location(
            "ir_merge_carry", PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "ir_merge_carry.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def boom(*_args):
            raise RuntimeError("unexpected")

        module.verify = boom
        # 引数は CLI と同じ 6 個にする（数が違うと verify の前に返り、例外の経路を通らない）
        self.assertEqual(module.main(["x", "repo", "merge", "reviewed", "ref", "5"]), 1)

    def _module(self, name: str):
        import importlib.util
        from _paths import PLUGIN_ROOT

        spec = importlib.util.spec_from_file_location(
            name, PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "ir_merge_carry.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_shared_line_does_not_hide_extra_line(self) -> None:
        """両側が同じ行を持つとき、ブロックの中の余分な行を少なく数えない。"""
        m = self._module("ir_merge_carry_s")
        auto = b"x\n<<<<<<< ours\na\nb\n=======\na\nc\n>>>>>>> theirs\ny\n"
        merged = [b"x\n", b"a\n", b"b\n", b"Z\n", b"c\n", b"y\n"]
        self.assertEqual(m._resolution_lines(m._conflict_segments(auto), merged), 1)

    def test_dropped_side_raises_not_carried(self) -> None:
        """ブロックの片側の行が残らないときは、例外に頼らず NotCarried で止める。"""
        m = self._module("ir_merge_carry_d")
        auto = b"x\n<<<<<<< ours\na\n=======\nb\n>>>>>>> theirs\ny\n"
        for merged in ([b"x\n", b"b\n", b"y\n"], [b"x\n", b"a\n", b"y\n"]):
            with self.subTest(merged=merged):
                with self.assertRaises(m.NotCarried):
                    m._resolution_lines(m._conflict_segments(auto), merged)

    def test_changed_line_between_blocks_is_not_carried(self) -> None:
        """2 つのブロックの間にある衝突の外の行を変えた merge は引き継がない。"""
        m = self._module("ir_merge_carry_b")
        auto = (b"x\n<<<<<<< ours\na\n=======\nb\n>>>>>>> theirs\nmid\n"
                b"<<<<<<< ours\nc\n=======\nd\n>>>>>>> theirs\ny\n")
        segments = m._conflict_segments(auto)
        ok = [b"x\n", b"a\n", b"b\n", b"mid\n", b"c\n", b"d\n", b"y\n"]
        self.assertEqual(m._resolution_lines(segments, ok), 0)
        changed = [b"x\n", b"a\n", b"b\n", b"MID\n", b"c\n", b"d\n", b"y\n"]
        with self.assertRaises(m.NotCarried):
            m._resolution_lines(segments, changed)

    def test_blob_missing_or_nul_is_not_carried(self) -> None:
        """消えた blob と NUL を含む blob は、その理由で止める。"""
        m = self._module("ir_merge_carry_n")

        class FakeGit:
            def __init__(self, code, out):
                self.result = subprocess.CompletedProcess([], code, out, b"")

            def run(self, *_args, **_kwargs):
                return self.result

        with self.assertRaisesRegex(m.NotCarried, "消えている"):
            m._blob(FakeGit(128, b""), "t", "p", "消えている")
        with self.assertRaisesRegex(m.NotCarried, "バイナリ"):
            m._blob(FakeGit(0, b"a\0b\n"), "t", "p", "消えている")
        self.assertEqual(m._blob(FakeGit(0, b"a\n"), "t", "p", "消えている"), b"a\n")

    def test_slow_python_path_stops_within_budget(self) -> None:
        """git を呼ばない Python の計算が長くても、渡した残り時間で引き継がない側に終える。

        退行したときに止まらないので、子プロセスで走らせ、時間切れなら失敗にする。
        """
        import sys
        import time
        from _paths import PLUGIN_ROOT

        script = (
            "import importlib.util, sys\n"
            "spec = importlib.util.spec_from_file_location('m', sys.argv[1])\n"
            "m = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(m)\n"
            "def spin(*_a):\n"
            "    while True:\n"
            "        pass\n"
            "m.verify = spin\n"
            "sys.exit(m.main(['x', 'repo', 'merge', 'reviewed', 'ref', '0.5']))\n"
        )
        start = time.monotonic()
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-c", script,
                 str(PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "ir_merge_carry.py")],
                capture_output=True, text=True, timeout=HANG_GUARD,
            )
        except subprocess.TimeoutExpired:
            self.fail("Python の計算が残り時間を越えて走り続けた")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("時間内に確かめられない", result.stdout)
        # 渡した残り時間（0.5 秒）で切る。子プロセスの起動の分だけ余裕を置く
        self.assertLess(time.monotonic() - start, 3.0)

    def test_check_time_stops_after_deadline(self) -> None:
        """期限を過ぎたら、git を呼ぶ前に止める。"""
        m = self._module("ir_merge_carry_c")
        git = m._Git("repo", 0.01)
        git.deadline = 0
        with self.assertRaisesRegex(m.NotCarried, "時間内"):
            git.check_time()

    def test_malformed_markers_are_not_carried(self) -> None:
        """`=======` が 1 つのブロックに 2 本・閉じないブロック・ブロックが無い blob は読まない。"""
        m = self._module("ir_merge_carry_m")
        for auto in (
            b"<<<<<<< ours\na\n=======\nb\n=======\nc\n>>>>>>> theirs\n",
            b"<<<<<<< ours\na\n=======\nb\n",
            b"plain only\n",
            b"a\n>>>>>>> theirs\n",
        ):
            with self.subTest(auto=auto):
                with self.assertRaises(m.NotCarried):
                    m._conflict_segments(auto)

    def test_time_budget_from_caller_stops_slow_git(self) -> None:
        """呼び出し側が渡した残り時間を超える git は待たず、引き継がない。"""
        import importlib.util
        import io
        import contextlib
        from _paths import PLUGIN_ROOT

        spec = importlib.util.spec_from_file_location(
            "ir_merge_carry_t", PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "ir_merge_carry.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            shim = Path(tmp) / "git"
            shim.write_text("#!/bin/sh\nsleep 5\n", encoding="utf-8")
            shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
            old_path = os.environ["PATH"]
            os.environ["PATH"] = f"{tmp}{os.pathsep}{old_path}"
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out):
                    started = time.monotonic()
                    code = module.main(["x", tmp, "a" * 40, "b" * 40, "ref", "0.5"])
                    elapsed = time.monotonic() - started
            finally:
                os.environ["PATH"] = old_path
        self.assertEqual(code, 1)
        self.assertIn("時間内に確かめられない", out.getvalue())
        # 渡した残り時間（0.5 秒）で切る。上限 5 秒まで待たない
        self.assertLess(elapsed, 2.0)

    def test_no_time_left_is_not_carried(self) -> None:
        """引き継げる merge でも、残り時間が 0 以下なら引き継がない（対照: 残り 5 秒なら引き継ぐ）。"""
        import contextlib
        import io

        m = self._module("ir_merge_carry_t2")
        with tempfile.TemporaryDirectory() as tmp:
            fx = MergeCarryFixture(Path(tmp))
            fx.advance_main()
            merge = fx.merge()
            args = ["x", str(fx.repo), merge, fx.reviewed, "refs/remotes/origin/main"]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(m.main(args + ["0"]), 1)
            self.assertIn("時間内に確かめられない", out.getvalue())
            self.assertEqual(m.main(args + ["5"]), 0)

    def test_without_setitimer_reports_why(self) -> None:
        """時計を張れない環境（Windows など）では、その理由で引き継がない。"""
        import contextlib
        import io
        import types

        m = self._module("ir_merge_carry_w")
        m.signal = types.SimpleNamespace(SIGALRM=None, signal=lambda *_a: None)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(m.main(["x", "repo", "a" * 40, "b" * 40, "ref", "5"]), 1)
        self.assertIn("時間の上限を張れない", out.getvalue())

    def test_shell_subtracts_truncated_second(self) -> None:
        """bash の SECONDS は秒の切り捨てなので、残りが 1 秒でも判定を始めない（持ち時間 8 秒・経過 7 秒台）。"""
        from _paths import PLUGIN_ROOT

        lib = PLUGIN_ROOT / "hooks" / "scripts" / "lib"
        with tempfile.TemporaryDirectory() as tmp:
            fx = MergeCarryFixture(Path(tmp))
            fx.advance_main()
            merge = fx.merge()
            fx.write()
            script = (
                f'source "{lib}/detect-steering.sh"; source "{lib}/self-review-evidence.sh"; '
                f'source "{lib}/merge-gate-evidence.sh"; source "{lib}/gate-ledger.sh"; '
                f'gdd_ir_carry_matches "$1" "$2" "$3" "$4" 8 && echo carried || echo "no: $GDD_IR_CARRY_REASON"'
            )
            # 判定の python を呼んだかを印で見る（呼んだ側が時間切れで同じ文を出す形と分ける）
            stub = Path(tmp) / "bin"
            stub.mkdir()
            real = shutil.which("python3")
            (stub / "python3").write_text(
                f'#!/bin/bash\ncase "$*" in *ir_merge_carry.py*) echo called; exit 0;; esac\nexec "{real}" "$@"\n',
                encoding="utf-8",
            )
            (stub / "python3").chmod(0o755)
            state = str(fx.steering / "state.md")
            env = {**os.environ, "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}"}
            run = lambda seconds: subprocess.run(
                ["bash", "-c", script, "x", str(fx.repo), state, fx.reviewed, merge],
                capture_output=True, text=True, env={**env, "SECONDS": seconds},
            ).stdout
            self.assertIn("no: 時間内に確かめられない", run("7"))
            self.assertIn("carried", run("0"))

if __name__ == "__main__":
    unittest.main()
