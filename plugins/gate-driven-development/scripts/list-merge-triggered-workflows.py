#!/usr/bin/env python3
"""マージで起動する workflow の一覧を出す。

Usage:
  python3 list-merge-triggered-workflows.py [--repo <dir>] [--base <ref>] [--head <ref>]
                                            [--merge-with <ref>] [--default-branch <name>]

`git diff --name-only --no-renames -z <base>...<head>` の変更ファイルと、workflow
（`.github/workflows/*.yml`・`*.yaml`）の `on` を突き合わせ、既定ブランチへのマージで
起動するかを workflow ごとに 1 行で出す。<head> の既定は `HEAD`。マージの後は
`--base <push の前の既定ブランチ> --head <merge commit>` で、マージが起こす push の差分を見る
（merge commit と squash では `<merge commit>^1`、rebase では `<merge commit>~<PR の commit 数>`）。
workflow は <head> から読む。マージの前は `--merge-with <既定ブランチ>` を渡すと、マージの結果の
workflow をファイルごとに選んで読む（<head> 側だけが変えたものは <head>、ほかは既定ブランチから。
両方が変えたものは `起動しうる`）。既定ブランチに後から足された workflow も読む。

出力（タブ区切り、workflow のパス順）:
  <判定>\t<workflow のパス>\t<理由>
判定は `起動する`・`起動しうる`・`起動しない` のどれか。

`on.push` は filter（`branches`・`branches-ignore`・`tags`・`tags-ignore`・`paths`・
`paths-ignore`）で判定する。glob は GitHub Actions の filter pattern に合わせる。`*` は `/` を
またがず、`**` はまたぐ。`?`・`+` は直前の 1 文字にかかり、`[]` は英数字の範囲だけ、`!` は
先頭で直前までの一致を打ち消す（順に評価して後勝ち）。

push 以外の event は、マージでは起動しないと分かっているもの（`NOT_ON_MERGE`、`types` に
`closed` を含まない `pull_request`・`pull_request_target`・`issues`）だけを `起動しない` にし、
ほか（`workflow_run`・`release`・`merge_group`・`closed` を含む `pull_request` など）は
`起動しうる` にする。`issues` は `types` が無ければ全種類（`closed` を含む）で起動するので
`起動しうる`（PR 本文の `Closes #<n>` で、マージが issue を閉じる）。

判定できない形は `起動しうる` に倒す。読めない YAML（anchor・flow mapping・値の途中の引用符・
複数行の値など）、UTF-8 で読めないファイル、`on` が無い、`paths` と `paths-ignore`（または
`branches` と `branches-ignore`）の併用（GitHub は受け付けない）、`paths-ignore`・
`branches-ignore` の `!`、`!` だけの `paths`・`branches`、既定ブランチが分からないときの
`branches`・`branches-ignore`、差分が空のとき、差分が 3,000 ファイルを超えるときの
`paths`・`paths-ignore`（GitHub の Workflow syntax の `on.<push|pull_request>.paths` の節:
差分が 3,000 ファイルを超え、当たるファイルが先頭の 3,000 件に無いと起動しない）。

見ないもの: job の `if:`、push で起動した workflow が API（`gh workflow run`・
`repository_dispatch`）や tag・release を通して間接に起こす起動。

既定ブランチは `--default-branch`、無ければ `git symbolic-ref refs/remotes/origin/HEAD` で決める。
base の既定は `origin/<既定ブランチ>`（分からなければ `origin/main`）。git が失敗するなど一覧を
作れないときは exit 2 で、stdout には何も出さない。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

RUNS = "起動する"
MAY = "起動しうる"
NO = "起動しない"

ON_LINE = re.compile(r"""^(?:on|"on"|'on'|true)[ \t]*:(?:[ \t](.*))?$""")
FILTER_KEYS = {"branches", "branches-ignore", "tags", "tags-ignore", "paths", "paths-ignore"}
NOT_ON_MERGE = {
    "workflow_dispatch", "workflow_call", "schedule",
    "pull_request_review", "pull_request_review_comment", "issue_comment",
    "discussion", "discussion_comment", "label", "milestone", "watch", "fork", "gollum",
}
# types で closed を選べる event と、types が無いときに closed を含むか
CLOSED_TYPE_EVENTS = {"pull_request": False, "pull_request_target": False, "issues": True}
DIFF_LIMIT = 3000


class Unsupported(Exception):
    """この script の YAML の部分集合・filter の解釈で読めない形。"""


# --- YAML の部分集合（`on:` の節だけを読む） ---------------------------------


def _walk(text: str) -> Iterator[tuple[int, str]]:
    """引用の外の文字を (位置, 文字) で返す。引用符は値の先頭でだけ引用を始める。"""
    quote, i = "", 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                if quote == "'" and text[i + 1 : i + 2] == "'":
                    i += 2
                    continue
                quote = ""
        elif ch in "'\"":
            if i and text[i - 1] not in " [,":
                raise Unsupported(f"quote inside value: {text!r}")
            quote = ch
        else:
            yield i, ch
        i += 1
    if quote:
        raise Unsupported(f"unclosed quote: {text!r}")


def _strip_comment(line: str) -> str:
    for i, ch in _walk(line):
        if ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def _scalar(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] == "'":
        return text[1:-1].replace("''", "'")
    if len(text) >= 2 and text[0] == text[-1] == '"':
        if "\\" in text:
            raise Unsupported(f"escape in {text}")
        return text[1:-1]
    if not text or text[0] in "&*!|>{[%@`'\"":
        raise Unsupported(f"scalar {text!r}")
    return text


def _split_flow(body: str) -> list[str]:
    items, start = [], 0
    for i, ch in _walk(body):
        if ch in "[]{}":
            raise Unsupported("nested flow collection")
        if ch == ",":
            items.append(body[start:i])
            start = i + 1
    items.append(body[start:])
    return [_scalar(item) for item in items if item.strip()]


def _inline(text: str) -> object:
    if text.startswith("["):
        if not text.endswith("]"):
            raise Unsupported("multi-line flow sequence")
        return _split_flow(text[1:-1])
    if text == "{}":
        return {}
    if text in ("~", "null"):
        return None
    return _scalar(text)


def _split_key(content: str) -> tuple[str, str]:
    for i, ch in _walk(content):
        if ch == ":" and (i + 1 == len(content) or content[i + 1] == " "):
            return _scalar(content[:i]), content[i + 1 :].strip()
    raise Unsupported(f"not a mapping: {content!r}")


Lines = list[tuple[int, str]]


def _children(lines: Lines, indent: int) -> dict[str, tuple[str, Lines]]:
    """indent の mapping を、key → (同じ行の値, 子の行) に分ける。子の行はまだ読まない。"""
    out: dict[str, tuple[str, Lines]] = {}
    i = 0
    while i < len(lines):
        if lines[i][0] != indent or lines[i][1].startswith("-"):
            raise Unsupported("unexpected indentation")
        key, rest = _split_key(_strip_comment(lines[i][1]))
        if key in out:
            raise Unsupported(f"duplicate key {key}")
        j = i + 1
        while j < len(lines) and (
            lines[j][0] > indent or (lines[j][0] == indent and lines[j][1].startswith("-"))
        ):
            j += 1
        out[key] = (rest, lines[i + 1 : j])
        i = j
    return out


def _value(rest: str, child: Lines) -> object:
    if rest:
        if child:
            raise Unsupported("value and block together")
        return _inline(rest)
    if not child:
        return None
    if child[0][1].startswith("-"):
        seq = []
        for indent, content in child:
            item = _strip_comment(content)[1:].strip()
            if indent != child[0][0] or not content.startswith("- ") or not item:
                raise Unsupported("nested sequence item")
            value = _inline(item)
            if not isinstance(value, str):
                raise Unsupported("non-scalar sequence item")
            seq.append(value)
        return seq
    return {
        key: _value(sub_rest, sub_child)
        for key, (sub_rest, sub_child) in _children(child, child[0][0]).items()
    }


def read_on(text: str) -> object:
    """top-level の `on` を、文字列・list か、event 名 → (同じ行の値, 子の行) で返す。"""
    raw = text.splitlines()
    for n, line in enumerate(raw):
        found = ON_LINE.match(line.rstrip())
        if not found:
            continue
        rest = _strip_comment(found.group(1) or "").strip()
        if rest:
            return _inline(rest)
        lines: Lines = []
        for body in raw[n + 1 :]:
            if body and body[0] not in " \t#":
                break
            stripped = body.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lead = body[: len(body) - len(body.lstrip())]
            if "\t" in lead:
                raise Unsupported("tab indentation")
            lines.append((len(lead), stripped))
        if not lines:
            raise Unsupported("empty on")
        if lines[0][1].startswith("-"):
            return _value("", lines)
        return _children(lines, lines[0][0])
    raise Unsupported("no on key")


# --- filter pattern -----------------------------------------------------------


def _pattern(glob: str) -> re.Pattern[str]:
    atoms: list[str] = []
    i = 0
    while i < len(glob):
        ch = glob[i]
        if glob.startswith("**", i):
            i += 2
            if glob.startswith("/", i):
                atoms.append("(?:.*/)?")
                i += 1
            else:
                atoms.append(".*")
            continue
        if ch == "*":
            atoms.append("[^/]*")
        elif ch in "?+":
            if not atoms:
                raise Unsupported(f"{ch} without preceding character")
            atoms[-1] = f"(?:{atoms[-1]}){ch}"
        elif ch == "[":
            end = glob.find("]", i + 1)
            body = glob[i + 1 : end]
            if end < 0 or not re.fullmatch(r"(?:[a-zA-Z0-9](?:-[a-zA-Z0-9])?)+", body):
                raise Unsupported(f"bracket in {glob}")
            atoms.append(f"[{body}]")
            i = end
        elif ch == "\\":
            if i + 1 >= len(glob):
                raise Unsupported(f"trailing escape in {glob}")
            i += 1
            atoms.append(re.escape(glob[i]))
        else:
            atoms.append(re.escape(ch))
        i += 1
    try:
        return re.compile("".join(atoms), re.DOTALL)
    except re.error as exc:
        raise Unsupported(f"pattern {glob}: {exc}") from exc


def matches(patterns: list[str], path: str) -> bool:
    """順に評価して後勝ち。`!` で始まる pattern は、それまでの一致を打ち消す。"""
    hit = False
    for pattern in patterns:
        negative = pattern.startswith("!")
        if _pattern(pattern[1:] if negative else pattern).fullmatch(path):
            hit = not negative
    return hit


# --- 判定 --------------------------------------------------------------------


def _filters(push: object) -> dict[str, list[str]]:
    if push is None:
        return {}
    if not isinstance(push, dict):
        raise Unsupported("push is not a mapping")
    result: dict[str, list[str]] = {}
    for key, value in push.items():
        if key not in FILTER_KEYS:
            raise Unsupported(f"unknown key push.{key}")
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or not value:
            raise Unsupported(f"push.{key} is not a list")
        result[key] = value
    return result


def _list(files: list[str]) -> str:
    shown = ", ".join(re.sub(r"[\t\r\n]", "?", path) for path in files[:3])
    return shown + (f" ほか {len(files) - 3} 件" if len(files) > 3 else "")


def judge_push(push: object, files: list[str], default_branch: str | None) -> tuple[str, str]:
    f = _filters(push)
    for a, b in (("paths", "paths-ignore"), ("branches", "branches-ignore")):
        if a in f and b in f:
            return MAY, f"{a} と {b} の併用（GitHub は受け付けない）"
    for key in ("paths-ignore", "branches-ignore"):
        if any(p.startswith("!") for p in f.get(key, [])):
            return MAY, f"{key} の ! は判定しない"
    for key in ("paths", "branches"):
        if key in f and all(p.startswith("!") for p in f[key]):
            return MAY, f"{key} が ! だけ"
    has_branch_filter = "branches" in f or "branches-ignore" in f
    if not has_branch_filter and ("tags" in f or "tags-ignore" in f):
        return NO, "tags の filter だけ（branch の push では起動しない）"
    uncertain = []
    if has_branch_filter and default_branch is None:
        uncertain.append("既定ブランチが分からない")
    elif "branches" in f and not matches(f["branches"], default_branch or ""):
        return NO, f"branches が {default_branch} に当たらない"
    elif "branches-ignore" in f and matches(f["branches-ignore"], default_branch or ""):
        return NO, f"branches-ignore が {default_branch} に当たる"
    if not files:
        return MAY, "差分が空（base と head を確かめる）"
    has_paths_filter = "paths" in f or "paths-ignore" in f
    if "paths" in f:
        hits = [p for p in files if matches(f["paths"], p)]
        reason = f"paths に当たる: {_list(hits)}"
    elif "paths-ignore" in f:
        hits = [p for p in files if not matches(f["paths-ignore"], p)]
        reason = f"paths-ignore に当たらない: {_list(hits)}"
    else:
        hits, reason = files, "paths の filter なし"
    if not hits:
        return NO, "変更ファイルが paths の filter に当たらない"
    if has_paths_filter and len(files) > DIFF_LIMIT:
        uncertain.append(f"差分が {DIFF_LIMIT} ファイルを超える")
    if uncertain:
        return MAY, f"{reason}（{'・'.join(uncertain)}）"
    return RUNS, reason


def _judge_event(name: str, value: object, files: list[str], default_branch: str | None) -> tuple[str, str]:
    if name == "push":
        return judge_push(value, files, default_branch)
    if name in CLOSED_TYPE_EVENTS:
        types = value.get("types") if isinstance(value, dict) else None
        if value is not None and not isinstance(value, dict):
            raise Unsupported(f"{name} is not a mapping")
        if isinstance(types, str):
            types = [types]
        if types is not None and not isinstance(types, list):
            raise Unsupported(f"{name}.types is not a list")
        if types == []:
            raise Unsupported(f"{name}.types is empty")
        if types is None and CLOSED_TYPE_EVENTS[name]:
            return MAY, f"{name} の types が無い（closed を含む全種類で起動しうる）"
        if types and "closed" in types:
            return MAY, f"{name} の types に closed がある（マージで起動しうる）"
        return NO, f"{name}（closed を含まない）"
    return MAY, f"{name} はマージで起動しうる（判定しない event）"


def judge(text: str, files: list[str], default_branch: str | None) -> tuple[str, str]:
    try:
        on = read_on(text)
        if isinstance(on, str):
            events: dict[str, tuple[str, Lines]] = {on: ("", [])}
        elif isinstance(on, list):
            events = {name: ("", []) for name in on}
        elif isinstance(on, dict):
            events = on  # type: ignore[assignment]
        else:
            raise Unsupported("on is empty")
        results = []
        for name, (rest, child) in events.items():
            if name in NOT_ON_MERGE:  # 中身は読まない（読めない inputs で判定を落とさない）
                results.append((NO, name))
                continue
            try:
                results.append(_judge_event(name, _value(rest, child), files, default_branch))
            except Unsupported as exc:
                results.append((MAY, f"{name}: 判定できない形: {exc}"))
    except Unsupported as exc:
        return MAY, f"判定できない形: {exc}"
    for status in (RUNS, MAY):
        reasons = [reason for s, reason in results if s == status]
        if reasons:
            return status, " / ".join(reasons)
    if "push" not in events:
        return NO, "on.push なし（" + ", ".join(events) + "）"
    return NO, " / ".join(reason for _, reason in results)


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def _names(output: bytes) -> list[str]:
    return [name for name in output.decode("utf-8", "surrogateescape").split("\0") if name]


def _text(output: bytes) -> str:
    return output.decode("utf-8", "surrogateescape").strip()


def _default_branch(repo: Path) -> str | None:
    try:
        ref = _text(_git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"))
    except subprocess.CalledProcessError:
        return None
    return ref.removeprefix("refs/remotes/origin/") or None


def _workflows(repo: Path, ref: str) -> set[str]:
    tree = _names(_git(repo, "ls-tree", "-z", "--name-only", ref, ".github/workflows/"))
    return {p for p in tree if p.endswith((".yml", ".yaml")) and p.count("/") == 2}


def _sources(repo: Path, head: str, merge_with: str | None) -> dict[str, str | None]:
    """workflow のパス → 読む ref。None は両方が変えたもの（読まずに `起動しうる`）。"""
    ours = _workflows(repo, head)
    if merge_with is None:
        return {path: head for path in ours}
    theirs = _workflows(repo, merge_with)
    ours_changed = set(_names(_git(repo, "diff", "--name-only", "--no-renames", "-z", f"{merge_with}...{head}")))
    theirs_changed = set(_names(_git(repo, "diff", "--name-only", "--no-renames", "-z", f"{head}...{merge_with}")))
    sources: dict[str, str | None] = {}
    for path in ours | theirs:
        if path in ours_changed and path in theirs_changed:
            sources[path] = None
        elif path in ours_changed:
            if path in ours:  # PR が消したものは読まない
                sources[path] = head
        elif path in theirs:  # 既定ブランチが消したものは読まない
            sources[path] = merge_with
    return sources


def _judge_file(repo: Path, ref: str | None, path: str, files: list[str], default_branch: str | None) -> tuple[str, str]:
    if ref is None:
        return MAY, "PR と既定ブランチの両方が変えた（マージの結果を読まない）"
    try:
        text = _git(repo, "show", f"{ref}:{path}").decode("utf-8")
        return judge(text, files, default_branch)
    except Exception as exc:  # 1 つの workflow の失敗で一覧全体を落とさない
        return MAY, f"判定できない形: {type(exc).__name__}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--merge-with")
    parser.add_argument("--default-branch")
    args = parser.parse_args(argv)
    try:
        repo = Path(_text(_git(Path(args.repo), "rev-parse", "--show-toplevel")))
        default_branch = args.default_branch or _default_branch(repo)
        base = args.base or f"origin/{default_branch or 'main'}"
        files = _names(_git(repo, "diff", "--name-only", "--no-renames", "-z", f"{base}...{args.head}"))
        if args.merge_with == "":
            raise OSError("--merge-with が空")
        sources = _sources(repo, args.head, args.merge_with)
    except (subprocess.CalledProcessError, OSError) as exc:
        detail = exc.stderr.decode(errors="replace") if isinstance(exc, subprocess.CalledProcessError) else exc
        print(f"一覧を作れない: {detail}", file=sys.stderr)
        return 2
    lines = [
        f"{status}\t{path}\t{reason}"
        for path in sorted(sources)
        for status, reason in [_judge_file(repo, sources[path], path, files, default_branch)]
    ]
    if lines:  # パスは surrogateescape で読んだので、stdout の encoding によらず bytes で書く
        sys.stdout.flush()
        sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8", "surrogateescape"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
