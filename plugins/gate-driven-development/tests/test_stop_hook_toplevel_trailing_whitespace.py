"""名前が空白・タブ・改行・CR で終わる worktree でも、done guard が検査対象を見失わない。

`_worktree_toplevel` が git の出力を text モードの `.strip()` で読むと、`<wt> ` の
toplevel が `<wt>` になる。bind も `.steering` も見つからず、未完了の tasklist の
まま done を通していた。タブ・改行・CR を含むパスは、正しく読めた後に containment
の検査が拒否する（tasklist の状態にかかわらず止める）。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _git_fixture import init_repo  # noqa: E402
from _stop_hook_test_base import (  # noqa: E402
    _CLEAN_TASKLIST,
    _UNFINISHED_TASKLIST,
    _bind,
    _git,
    _stop_done,
)

SLUG = "20260822-target"


class TrailingWhitespaceToplevelTests(unittest.TestCase):
    def _run(self, suffix: str, *, bound: bool, tasklist: str | None, others: int = 0):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp).resolve()
            main = tmp_path / "main"
            main.mkdir()
            init_repo(main)
            wt = tmp_path / f"wt{suffix}"
            _git("worktree", "add", "-b", "target-branch", str(wt), cwd=main)
            if tasklist is not None:
                steering = wt / ".steering" / SLUG
                steering.mkdir(parents=True)
                (steering / "tasklist.md").write_text(tasklist, encoding="utf-8")
            for i in range(others):
                other = wt / ".steering" / f"20260821-other{i}"
                other.mkdir(parents=True)
                (other / "tasklist.md").write_text(_UNFINISHED_TASKLIST, encoding="utf-8")
            if bound:
                _bind(wt, SLUG)
            _code, out, err = _stop_done(wt)
            return wt, out, f"out={out}\nerr={err}"

    def test_unfinished_tasklist_blocks_in_a_worktree_whose_name_ends_with_a_space(self):
        # "" は対照（fixture が空白の無い名前で同じ理由の block を出すこと）。
        for suffix in ("", " "):
            for bound in (True, False):
                with self.subTest(suffix=repr(suffix), bound=bound):
                    wt, out, msg = self._run(suffix, bound=bound, tasklist=_UNFINISHED_TASKLIST)
                    self.assertIn('"decision": "block"', out, msg)
                    self.assertIn("未完了タスクが 1 件残っています", out, msg)
                    self.assertIn(f"{wt}/.steering/{SLUG}/tasklist.md", out, msg)
                    if bound:
                        self.assertNotIn("[gdd:bind-unresolved]", out, msg)

    def test_clean_tasklist_allows_in_a_worktree_whose_name_ends_with_a_space(self):
        _wt, out, msg = self._run(" ", bound=True, tasklist=_CLEAN_TASKLIST)
        self.assertNotIn('"decision": "block"', out, msg)

    def test_control_characters_in_the_name_block_by_containment(self):
        # タブ・改行・CR は containment が拒否する。完了済みの tasklist でも止める。
        for suffix in ("\t", "\n", "\r"):
            for tasklist in (_UNFINISHED_TASKLIST, _CLEAN_TASKLIST):
                with self.subTest(suffix=repr(suffix), clean=tasklist is _CLEAN_TASKLIST):
                    _wt, out, msg = self._run(suffix, bound=True, tasklist=tasklist)
                    self.assertIn('"decision": "block"', out, msg)
                    self.assertIn("containment rejected", out, msg)

    def test_control_characters_block_with_several_steerings(self):
        # binding は拒否文字で捨てられる。steering が 2 つ以上でも、推測で通さずに止める。
        for suffix in ("\t", "\n", "\r"):
            for bound in (True, False):
                with self.subTest(suffix=repr(suffix), bound=bound):
                    _wt, out, msg = self._run(
                        suffix, bound=bound, tasklist=_UNFINISHED_TASKLIST, others=1
                    )
                    self.assertIn('"decision": "block"', out, msg)
                    self.assertIn("containment rejected", out, msg)

    def test_control_characters_without_steering_allow(self):
        # 対照: steering が無い worktree は今までどおり検査対象なしで通す。
        _wt, out, msg = self._run("\t", bound=False, tasklist=None)
        self.assertNotIn('"decision": "block"', out, msg)


if __name__ == "__main__":
    unittest.main()
