"""toplevel の名前が空白・改行・CR で終わる repo でも、active な GDD の marker を見落とさない。

`git_output` が出力を `.strip()` で読むと、`<repo> ` の toplevel が `<repo>` になり、
別のパスの marker を見て root branch を作るコマンドを allow していた。text モードで
読むと、CR（`\\r`）も改行に置き換わる。
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import run_root_branch_guard

COMMAND = "git checkout -b feature/x"


def _repo(path: Path, *, active: bool | None) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    if active is not None:
        marker = path / ".claude" / "gdd-dev.local.md"
        marker.parent.mkdir()
        marker.write_text(f"active: {'true' if active else 'false'}\n", encoding="utf-8")
    return path


def _run(cwd: Path):
    return run_root_branch_guard(cwd, COMMAND)


class TrailingWhitespaceToplevelTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()

    def assertDenied(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        payload = json.loads(result.stderr.strip())
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_active_repo_whose_name_ends_with_whitespace_denies(self):
        # 末尾を落とした同名の repo（marker なし）がある形・無い形の両方。
        for suffix in (" ", "\n", "\t", "\r"):
            for twin in (False, True):
                with self.subTest(suffix=repr(suffix), twin=twin):
                    base = self.tmp / f"case-{len(list(self.tmp.iterdir()))}"
                    base.mkdir()
                    if twin:
                        _repo(base / "repo", active=None)
                    target = _repo(base / f"repo{suffix}", active=True)
                    self.assertDenied(_run(target))

    def test_active_repo_under_a_parent_with_a_carriage_return_denies(self):
        # パスの途中の CR も、改行に置き換えずに読む。
        parent = self.tmp / "x\ry"
        parent.mkdir()
        self.assertDenied(_run(_repo(parent / "repo", active=True)))

    def test_inactive_repo_whose_name_ends_with_whitespace_allows(self):
        # 対照: marker が active でなければ今までどおり通す。
        target = _repo(self.tmp / "repo ", active=False)
        result = _run(target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
