#!/usr/bin/env python3
"""steering の `review-findings.md`（reviewer の指摘の ID と行き先）を検査する。読むだけで、何も書かない。

使い方:
  python3 scripts/check-finding-dispositions.py --steering <dir> --task <Current Task> [--base <default-branch>]
    --steering  検査する steering（.steering/<slug>/）
    --task      今回の Round の task（Gate Batch は , 区切り）。どの task も、tasklist.md の Current Task にあり、
                その task を含む最後の IG 節の sha が HEAD で、round がその task の Gate Rounds（無ければ 0）でなければ invalid
    --base      根拠が absent@<sha> の行の path を分類する基準のブランチ。その行があるのに無ければ invalid

impl-gating Step 8 で、Round の判定を決める前に回す（正本: references/finding-dispositions.md）。
出力は 1 行 1 要求で `状態<TAB>要求<TAB>gate<TAB>詳細`（scripts/check-gate-ledger.sh と同じ形）。
状態は ok / missing（review-findings.md が無い）/ invalid（形・連番・値域・行き先の規則の誤り）/
error（読めない: 通常のファイルでない・UTF-8 でない）。ok 以外が 1 件でもあれば exit 1、引数の誤りは exit 2。
`Independent Review` 行の件数との突き合わせは check-gate-ledger.sh の `findings` 行が行う。
述語は hooks/scripts/lib/finding_dispositions.py にあり、ここに書き足さない。ここが持つのは、git と tasklist.md を
読む部分だけ（今回の Round の IG 節が HEAD の sha と Gate Rounds で書かれているかと、根拠が absent@<sha> の行の
`file:line` の分類。分類はどの IG 節の行もその sha で行い、その sha の時点で、path が merge-base にも sha にも、
branch の途中の commit にも無く、同じ basename の file も無い `never` だけを通す。sha が解けなければ invalid）。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.finding_dispositions import ABSENT_RE, location_path, parse, same_sha, structure_errors  # noqa: E402
from lib.regular_file import read_regular_text  # noqa: E402
from lib.tasklist_parse import strip_fenced_blocks, task_name  # noqa: E402

GATE = "impl-gating"
_CURRENT_TASK_RE = re.compile(r"^##[ \t]+Current Task\b[^\n]*\n(.*?)(?=^##[ \t]|\Z)", re.MULTILINE | re.DOTALL)
# `- **T-1 …**` の形（compact_suggestion が受け付ける形）も task の見出しに数える
_COMPAT_TASK_RE = re.compile(r"^-[ \t]+\*\*(T-?\d+\b[^*]*)\*\*")
_GATE_ROUNDS_RE = re.compile(r"^[ \t]*(?:[-*][ \t]+)?Gate Rounds[ \t]*:[ \t]*(\S*)")
_ROUND_VALUE_RE = re.compile(r"(0|[1-9][0-9]*)(?![0-9])")


class _Unclassifiable(Exception):
    pass


def _git(repo: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return r.returncode, r.stdout


def _must(repo: Path, *args: str) -> str:
    code, out = _git(repo, *args)
    if code != 0:
        raise _Unclassifiable(f"git {args[0]} が失敗した")
    return out


def _name_key(path: str) -> str:
    """basename の照合の鍵。表記の揺れ（NFC・NFD、大文字小文字）は同じ名前に倒す（never にしない側）。"""
    return unicodedata.normalize("NFC", Path(path).name).casefold()


def classify(repo: Path, base: str | None, sha: str, location: str) -> str:
    """present / removed / similar / never。分類できなければ _Unclassifiable。"""
    # path は許可リストの文字だけで読む。外れた形（行:桁、\、引用符など）は never にせず分類できないにする
    name = location_path(location)
    if name is None:
        raise _Unclassifiable("file:line の欄が 1 つの path:行 でない")
    if base is None:
        raise _Unclassifiable("--base が無い")
    sha = _must(repo, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}").strip()
    mb = _must(repo, "merge-base", base, sha).strip()
    at_head = sha == _must(repo, "rev-parse", "HEAD").strip()
    path = Path(name)
    rel: str | None = name
    if path.is_absolute():
        try:
            rel = path.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError:
            rel = None  # worktree の外の path は basename の照合だけに使う
    if rel is not None:
        if _git(repo, "cat-file", "-e", f"{sha}:{rel}")[0] == 0 or (at_head and (repo / rel).exists()):
            return "present"
        if _git(repo, "cat-file", "-e", f"{mb}:{rel}")[0] == 0 or _must(
                repo, "log", "--format=%H", f"{mb}..{sha}", "--", rel).strip():
            return "removed"
    # -z で取る（引用符つきの名前を作らない）。HEAD では staged・未 commit の file も入れる
    names = _must(repo, "ls-tree", "-r", "-z", "--name-only", sha) + _must(repo, "ls-tree", "-r", "-z", "--name-only", mb)
    names += _must(repo, "log", "-z", "--name-only", "--format=", f"{mb}..{sha}")
    if at_head:
        names += _must(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if _name_key(name) in {_name_key(n) for n in names.split("\0") if n.strip()}:
        return "similar"
    return "never"


def current_task_rounds(tasklist: str) -> list[tuple[str, str]]:
    """Current Task の task ごとに (見出しの名前, Gate Rounds)。行が無ければ "0"、値が読めなければ ""。"""
    m = _CURRENT_TASK_RE.search(strip_fenced_blocks(tasklist))
    blocks: list[list] = []
    for line in (m.group(1).splitlines() if m else []):
        compat = _COMPAT_TASK_RE.match(line.strip())
        name = task_name(line.strip()) or (compat.group(1) if compat else "")
        if name:
            blocks.append([" ".join(name.strip("*").split()), None])
            continue
        g = _GATE_ROUNDS_RE.match(line)
        if g and blocks and blocks[-1][1] is None:
            v = _ROUND_VALUE_RE.match(g[1])
            blocks[-1][1] = v[1] if v else ""
    return [(name, "0" if rounds is None else rounds) for name, rounds in blocks]


def _task_round(blocks: list[tuple[str, str]], task: str) -> str | None:
    """task の Gate Rounds。task は見出しの名前の先頭と照合する（`T-1` は `T-10 …` に当たらない）。"""
    pattern = re.compile(rf"\**{re.escape(task)}(?![\w-])")
    return next((rounds for name, rounds in blocks if pattern.match(name)), None)


def round_errors(text: str, repo: Path | None, steering: Path, task: str, base: str | None) -> list[str]:
    """--task の task ごとに、Current Task にあるかと、その task を含む最後の IG 節の sha・round が HEAD・Gate Rounds と
    同じかを見る。あわせて、どの IG 節の absent@ の行もその節の sha で分類する。"""
    if repo is None:
        return ["steering が git の worktree の中に無い（HEAD と突き合わせられない）"]
    code, out = _git(repo, "rev-parse", "--verify", "--quiet", "HEAD")
    if code != 0:
        return ["HEAD が解けない（今回の Round の節と突き合わせられない）"]
    head = out.strip()
    try:
        tasklist = read_regular_text(steering / "tasklist.md")
    except (OSError, UnicodeDecodeError):
        tasklist = None
    if tasklist is None:
        return ["tasklist.md を読めない（Current Task の Gate Rounds と突き合わせられない）"]
    blocks = current_task_rounds(tasklist)
    sections, _ = parse(text)
    errors: list[str] = []
    for t in (t.strip() for t in task.split(",")):
        rounds = _task_round(blocks, t)
        last = next((s for s in reversed(sections) if s.kind == "IG" and t in s.tasks), None)
        if rounds is None:
            errors.append(f"task {t} が tasklist.md の Current Task に無い")
        elif not rounds:
            errors.append(f"task {t} の Gate Rounds の値が読めない")
        elif last is None:
            errors.append(f"今回の Round（HEAD {head[:12]}）の IG 節に task {t} が無い")
        elif not same_sha(last.sha, head) or last.round != rounds:
            errors.append(f"task {t} の最後の IG 節 {last.name}（sha {last.sha}・round {last.round}）が、今回の Round"
                          f"（HEAD {head[:12]}・Gate Rounds {rounds}）の節でない")
    for row in (r for s in sections if s.kind == "IG" for r in s.rows if ABSENT_RE.match(r.evidence)):
        try:
            kind = classify(repo, base, row.evidence.removeprefix("absent@"), row.location)
        except _Unclassifiable as exc:
            kind = f"分類できない（{exc}）"
        if kind != "never":
            errors.append(f"{row.rid}: 根拠の path が {kind}。absent@ は、その sha の時点で merge-base・tip・branch の途中の commit・未 commit の file のどれにも無く、同じ basename の file も無い path だけ")
    return errors


def check(steering: Path, task: str, base: str | None = None) -> list[tuple[str, str]]:
    path = steering / "review-findings.md"
    if not path.exists() and not path.is_symlink():
        return [("missing", f"{path} が無い")]
    try:
        text = read_regular_text(path)
    except (OSError, UnicodeDecodeError) as exc:
        return [("error", f"{path} を読めない（{type(exc).__name__}）")]
    if text is None:
        return [("error", f"{path} が通常のファイルでない")]
    code, top = _git(steering, "rev-parse", "--show-toplevel") if steering.is_dir() else (1, "")
    repo = Path(top.strip()) if code == 0 else None
    errors = structure_errors(text) + round_errors(text, repo, steering, task, base)
    if errors:
        return [("invalid", e) for e in errors]
    return [("ok", "review-findings.md の形・連番・行き先に誤りが無い")]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--steering", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--base")
    args = parser.parse_args(argv)
    try:
        rows = check(Path(args.steering), args.task, args.base)
    except Exception as exc:  # 検査の道具が落ちても ok を出さない
        rows = [("error", f"検査が例外で止まった（{type(exc).__name__}）")]
    for status, detail in rows:
        print(f"{status}\tfindings\t{GATE}\t{detail}")
    return 0 if all(s == "ok" for s, _ in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
