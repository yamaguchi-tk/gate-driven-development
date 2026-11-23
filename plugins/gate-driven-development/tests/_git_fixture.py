"""テスト用の git リポジトリを作る共有 fixture。

`git init` → user 設定 → README.md の 1 commit までは、各テストが同じ手順を
書き写していた。1 箇所に置いて共有する。サイト固有の後続操作（`git switch -c` など）
は呼び出し側に残す。

同じ引数・同じ git の環境での 2 回目以降は、プロセスごとに 1 回だけ作った repo を複製し、
git の起動を 6 回から 1 回にする（2026-10-14 に測ると、全量のテストは git を非常に多く起動していて、
複製は `init_repo` より ずっと速かった）。
"""
from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# git init が読む環境（ホストの init.defaultBranch など）。値が違えば別の複製元を作る
_GIT_ENV_KEYS = ("HOME", "XDG_CONFIG_HOME", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM",
                 "GIT_CONFIG_SYSTEM", "GIT_TEMPLATE_DIR")
_templates: dict[tuple, Path] = {}
_template_root: Path | None = None


def init_repo(
    path: Path, *, branch: str | None = None, commit_date: str | None = None
) -> None:
    """`path` を git repo にして、README.md の commit を 1 つ積む。

    `branch` が None なら初期ブランチ名を指定しない（ホストの `init.defaultBranch`
    に従う）。名前を固定したいテストだけが渡す。

    `commit_date` を渡すと、commit の author date と committer date をその値にする。
    HEAD の committer date を読む検査（merge gate の A-1 pin など）のテストが使う。
    渡さないときは、複製しても commit の日時を呼んだ時刻にする。

    auto maintenance は切る。`git commit` は `git maintenance run --auto --detach`
    を起こし、その子プロセスが `.git/objects/maintenance.lock` を一瞬作る。直後に
    `.git` を `shutil.copytree` するテストが、コピー中に消えたファイルで落ちる。
    """
    if (path / ".git").exists() or (path / "README.md").exists():
        # 複製で上書きしてしまう形は、従来の手順で作る
        _build(path, branch=branch, commit_date=commit_date)
        return
    key = (branch, commit_date, tuple(os.environ.get(k) for k in _GIT_ENV_KEYS))
    template = _templates.get(key)
    if template is None:
        template = _new_template_dir()
        _build(template, branch=branch, commit_date=commit_date)
        _templates[key] = template
    shutil.copytree(template, path, symlinks=True, dirs_exist_ok=True)
    if commit_date is None:
        # 複製元を作った時刻ではなく、呼んだ時刻の commit にする
        _git(path, "commit", "-q", "--amend", "--no-edit", "--date=now")


def _build(path: Path, *, branch: str | None, commit_date: str | None) -> None:
    init_args = ["init", "-q"]
    if branch is not None:
        init_args += ["-b", branch]
    _git(path, *init_args)
    _git(path, "config", "maintenance.auto", "false")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test User")
    (path / "README.md").write_text("test\n", encoding="utf-8")
    _git(path, "add", "README.md")
    env = None
    if commit_date is not None:
        env = {**os.environ, "GIT_AUTHOR_DATE": commit_date, "GIT_COMMITTER_DATE": commit_date}
    _git(path, "commit", "-q", "-m", "init", env=env)


def _new_template_dir() -> Path:
    global _template_root
    if _template_root is None:
        _template_root = Path(tempfile.mkdtemp(prefix="gdd-git-fixture-"))
        atexit.register(shutil.rmtree, _template_root, True)
    path = _template_root / str(len(_templates))
    path.mkdir()
    return path


def _git(cwd: Path, *args: str, env: dict[str, str] | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, env=env)
