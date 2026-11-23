#!/usr/bin/env python3
"""軽いレーンの「関係するテスト」（root CLAUDE.md 手順 3）を列挙し、--run なら pytest で回す。

使い方: python3 scripts/light-lane-related-tests.py --run . origin/main [-- <足すテスト・pytest の引数…>]
（--run なしなら 1 行 1 パスで出すだけ。zsh は引用符なしの $tests を改行で分けないので、回すときは --run を使う。
--run では、選んだテストを stderr に出してから、`--` の後ろと一緒に 1 回の pytest に渡す）

変えたファイルは、merge-base（<base> と HEAD）から作業ツリーまでの差分（改名は元と先の両方）と、untracked の
ファイル。どちらからも `__pycache__`・`.pyc` は除く。<repo_root> が subdirectory でも、その repo の top-level を使う。
出すのは次の和集合（どれも tests/ 直下の test_*.py）。
- 変えたファイルの名前（先頭の `.` を除き、次の `.` より前）を本文に含む GDD のテスト。GDD の helper
  （tests/ 直下の _*.py）がその名前を含むなら、helper の名前を含むテストも（1 段だけたどる）
- 変えたテストそのもの（消したものは除く）
- GDD 以外の plugin を変えたら、その plugin のテスト全部。.claude-plugin/marketplace.json を変えたら、GDD 以外の全 plugin のテスト
- review-log/ か GDD の changelog.d/ を変えたら、記録の検査のテスト（test_review_log_present.py。名前の一致では選ばれない）
--run では、`--` の後ろの、`-` で始まらず repo にある（top-level から見た）パス（`::` の前）を足すテストとして、
選んだテストと一緒に位置引数でも渡す（option の値だけでは pytest が tree 全体を集めるため）。選んだテストが 0 件でも、
足すテストがあれば回す。0 件で、`--` の後ろに `-` で始まらず repo に無い引数があれば、EXIT_ERROR で止める。
GDD 以外の plugin の `tests/validate-plugin.sh`（pytest でない検査。CI も回さない）は、その plugin を変えたら
（marketplace.json なら全部）、手で回すものとして stderr に出す。
終了コード: 0 = 列挙できた（--run なら pytest の終了コード。pytest は 0〜5 を使う）、EXIT_NO_TESTS（65）= 関係するテストなし
（stdout は空。空の引数の pytest は repo 全体を集めるため、pytest は回さない）、EXIT_ERROR（64）= 使い方の誤り、
git の失敗、テストのファイルを読めない、`--` の後ろのパスが無い。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

GDD = "plugins/gate-driven-development"
EXIT_NO_TESTS = 65
EXIT_ERROR = 64
MARKETPLACE = ".claude-plugin/marketplace.json"
RECORD_CHECK = f"{GDD}/tests/test_review_log_present.py"
RECORD_DIRS = ("review-log/", f"{GDD}/changelog.d/")


def _tests_in(repo_root: Path, rel_dir: str) -> list[Path]:
    return sorted((repo_root / rel_dir).glob("test_*.py"))


def _plugin_of(path: str) -> str | None:
    parts = path.split("/")
    return parts[1] if len(parts) > 2 and parts[0] == "plugins" else None


def _mentions(path: Path, stems: set[str]) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(stem in text for stem in stems)


def related_tests(changed: list[str], repo_root: Path) -> list[str]:
    stems = {Path(path).name.lstrip(".").split(".", 1)[0] for path in changed}
    stems.discard("")
    helpers = sorted((repo_root / GDD / "tests").glob("_*.py"))
    stems |= {helper.stem for helper in helpers if stems and _mentions(helper, stems)}
    found: set[Path] = {test for test in _tests_in(repo_root, f"{GDD}/tests") if stems and _mentions(test, stems)}
    for path in changed:
        candidate = repo_root / path
        if candidate.parent.name == "tests" and candidate.name.startswith("test_") and candidate.suffix == ".py" and candidate.is_file():
            found.add(candidate)
    for plugin in _changed_plugins(changed, repo_root):
        found.update(_tests_in(repo_root, f"plugins/{plugin}/tests"))
    if any(path.startswith(RECORD_DIRS) for path in changed) and (repo_root / RECORD_CHECK).is_file():
        found.add(repo_root / RECORD_CHECK)
    return sorted(str(test.relative_to(repo_root)) for test in found)


def _changed_plugins(changed: list[str], repo_root: Path) -> set[str]:
    plugins = {_plugin_of(path) for path in changed}
    if MARKETPLACE in changed:
        plugins.update(p.name for p in (repo_root / "plugins").iterdir() if p.is_dir())
    return plugins - {None, GDD.split("/")[1]}


def changed_files(repo_root: Path, base: str) -> list[str]:
    def git(*args: str) -> list[str]:
        out = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, check=True).stdout
        return [p.decode(errors="replace") for p in out.split(b"\0") if p]

    merge_base = git("merge-base", base, "HEAD")[0].strip()
    tracked = git("diff", "-z", "--no-renames", "--name-only", merge_base)
    untracked = git("ls-files", "-z", "--others", "--exclude-standard", "--full-name")
    return sorted(p for p in set(tracked) | set(untracked) if "__pycache__" not in p.split("/") and not p.endswith(".pyc"))


def top_level(path: Path) -> Path:
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    return Path(out.stdout.strip()).resolve()


def main(argv: list[str]) -> int:
    args, extra = (argv[1:argv.index("--")], argv[argv.index("--") + 1:]) if "--" in argv else (argv[1:], None)
    run = "--run" in args
    args = [a for a in args if a != "--run"]
    if len(args) not in (1, 2) or (extra is not None and not run):
        print("usage: light-lane-related-tests.py [--run] <repo_root> [<base>（既定: origin/main）] [-- <pytest の引数…>（--run のときだけ）]", file=sys.stderr)
        return EXIT_ERROR
    extra = extra or []
    base = args[1] if len(args) == 2 else "origin/main"
    try:
        repo_root = top_level(Path(args[0]))
        changed = changed_files(repo_root, base)
    except (subprocess.CalledProcessError, OSError, IndexError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else exc
        detail = detail.decode(errors="replace") if isinstance(detail, bytes) else str(detail)
        print(f"変えたファイルを決められない（base: {base}）: {detail.strip()}", file=sys.stderr)
        return EXIT_ERROR
    try:
        tests = related_tests(changed, repo_root)
    except OSError as exc:
        print(f"テストのファイルを読めない: {exc}", file=sys.stderr)
        return EXIT_ERROR
    for plugin in sorted(_changed_plugins(changed, repo_root)):
        script = repo_root / "plugins" / plugin / "tests" / "validate-plugin.sh"
        if script.is_file():
            print(f"手で回す検査: {script.relative_to(repo_root)}", file=sys.stderr)
    positional = [a for a in extra if not a.startswith("-")]
    added = [a for a in positional if (repo_root / a.split("::", 1)[0]).exists()]
    if not tests and not added:
        missing = [a for a in positional if a not in added]
        if missing:
            print(f"`--` の後ろのパスが repo（top-level から見て）に無い: {' '.join(missing)}", file=sys.stderr)
            return EXIT_ERROR
        print("関係するテストなし", file=sys.stderr)
        return EXIT_NO_TESTS
    if not run:
        print("\n".join(tests))
        return 0
    print("選んだテスト:\n" + "\n".join(f"  {t}" for t in [*tests, *added]), file=sys.stderr)
    return subprocess.run([sys.executable, "-m", "pytest", *tests, *added, "-q", *extra], cwd=repo_root, check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
