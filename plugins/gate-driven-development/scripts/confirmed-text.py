#!/usr/bin/env python3
"""human check で承認した確定文面の取り出し・digest・照合（正本: references/confirmed-text.md）。

  digest  --design <design.md> [--until <終わりの見出し>]
  extract --design <design.md> [--until <終わりの見出し>] --block D-1#1 [--sub NNNN=0192 ...]
  verify  --design <design.md> --manifest <confirmed-text.json> [--repo DIR] [--base REF] [--actual DIR]

verify は base の版に manifest の置き換えを当てた期待値と、実物をバイト単位で比べる（edits・content は
ファイル全体、sections は目印の間。「含まれるか」では比べない）。終了コード: 0 = 一致、1 = 不一致、2 = 入力の誤り（判定できない）。
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# フェンスの規則は design.md を読むほかの実装と同じ正本（tasklist_parse）に揃える。
# top-level module として読む（`lib` パッケージ名は scripts/lib と衝突する）。
_LIB_DIR = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from tasklist_parse import _FENCE_RE as FENCE_RE  # noqa: E402
except Exception as _exc:  # 読めない・壊れているときは判定できないので、不一致（1）ではなく 2 で止める
    print(f"confirmed-text: ERROR: tasklist_parse を読めない ({_exc})", file=sys.stderr)
    sys.exit(2)
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)

SECTION_RE = re.compile(r"^## 確定文面(?:$|[ （(])")
SECTION_END_RE = re.compile(r"^#{1,2} ")
HEADING_RE = re.compile(r"^#{1,3} ")
BLOCK_HEADING_RE = re.compile(r"^### (D-\d+)(?:$|\s)")
PLACEHOLDER_RE = re.compile(r"\{\{(D-\d+#[1-9]\d*)\}\}")
NOVERIFY = "noverify"
BLOCK_ID_RE = re.compile(r"^D-\d+#[1-9]\d*$")
FILE_KEYS = {"path", "edits", "content", "sections"}
EDIT_KEYS = {"old", "new", "reason"}
SECTION_KEYS = {"start", "end", "text"}
MANIFEST_KEYS = {"digest", "section_end", "substitutions", "files"}


class InputError(Exception):
    """入力が読めない・宣言どおりに当てられない。判定せずに exit 2 で止める。"""


def _decode(data: bytes, where: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"{where}: UTF-8 として読めない ({exc})") from exc


def _read(path: Path) -> str:
    try:
        return _decode(path.read_bytes(), str(path))
    except OSError as exc:
        raise InputError(f"{path}: 読めない ({exc})") from exc


def _fence_open(line: str) -> re.Match | None:
    """開きのフェンスなら match を返す（backtick のフェンスの info に ` を含む行は開きにしない）。"""
    m = FENCE_RE.match(line)
    if m and m.group("marker")[0] == "`" and "`" in m.group("info"):
        return None
    return m


def _fence_closes(line: str, marker: str) -> bool:
    m = FENCE_RE.match(line)
    return bool(
        m and m.group("marker")[0] == marker[0] and len(m.group("marker")) >= len(marker)
        and not m.group("info").strip()
    )


def _fence_toggle(line: str, fence: str | None) -> str | None:
    """フェンスの開閉を返す。開いていれば開いたフェンスの記号、閉じていれば None。"""
    if fence is None:
        m = _fence_open(line)
        return m.group("marker") if m else None
    return None if _fence_closes(line, fence) else fence


def _dedent(line: str, width: int) -> str:
    """開きのフェンスの字下げの分だけ、行頭の空白を外す。"""
    n = 0
    while n < width and n < len(line) and line[n] in " \t":
        n += 1
    return line[n:]


def _fence_scan(lines: list[str]) -> tuple[list[bool], bool]:
    """行ごとにフェンスの外か（区切りの行は中に数える）と、閉じていないフェンスがあるかを返す。"""
    outside: list[bool] = []
    fence: str | None = None
    for line in lines:
        outside.append(fence is None and _fence_open(line) is None)
        fence = _fence_toggle(line, fence)
    return outside, fence is not None


def outside_fences(lines: list[str]) -> list[bool]:
    """行ごとにフェンスの外かを返す（tasklist_parse の `_scan_fences` と同じ判定。テストが一致を固定する）。"""
    return _fence_scan(lines)[0]


def section_lines(design: str, until: str | None = None) -> tuple[list[str], str]:
    """`## 確定文面` の見出し行から、フェンスの外の次の `#`・`##` 見出しの前まで（無ければ末尾まで）。

    `until` を渡すと、間の見出しでは終えず、フェンスの外で `until` で始まる最初の行の前で終える
    （その行が無ければ判定しない）。宣言なしで終えた節の後ろに `### D-n` があれば止める（黙って範囲外に
    しない）。返り値は節の行と、節を終わらせた見出し（末尾までなら `EOF`）。"""
    if until is not None and not until:
        raise InputError("節の終わりの見出しが空")
    lines = design.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    outside, unclosed = _fence_scan(lines)
    if unclosed:
        raise InputError("design.md: 閉じていないコードフェンスがある")
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        if not outside[i]:
            continue
        if SECTION_RE.match(line):
            if start is not None:
                raise InputError(f"design.md:{i + 1}: `## 確定文面` の節が 2 つある")
            start = i
        elif start is not None and end is None and (
            line.startswith(until) if until else SECTION_END_RE.match(line)
        ):
            end = i
    if start is None:
        raise InputError("design.md: `## 確定文面` の節が無い")
    if until and end is None:
        raise InputError(f"design.md: 節の終わりの見出し {until!r} が節の後ろに無い")
    if not until and end is not None:
        after = [i for i in range(end, len(lines)) if outside[i] and BLOCK_HEADING_RE.match(lines[i])]
        if after:
            raise InputError(
                f"design.md:{after[0] + 1}: 節（{end + 1} 行目で終わる）の後ろに `{lines[after[0]]}` がある。"
                "節の中に `##` を置いたなら、または後ろの `### D-n` が確定文面でないなら、"
                "終わりの見出しを --until（manifest は section_end）で宣言する"
            )
    return lines[start:end], ("EOF" if end is None else f"{end + 1}: {lines[end]}")


def _bid_key(bid: str) -> tuple[int, int]:
    n, i = bid[2:].split("#")
    return int(n), int(i)


def digest(design: str, until: str | None = None) -> tuple[str, int, str, dict[str, tuple[str, bool]]]:
    found = blocks(design, until)  # 承認の前に、block にならないフェンスを見つけて止める
    lines, end = section_lines(design, until)
    body = "\n".join(lines) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest(), len(lines), end, found


def _block_lists(found: dict[str, tuple[str, bool]]) -> tuple[list[str], list[str]]:
    ids = sorted(found, key=_bid_key)
    return [b for b in ids if found[b][1]], [b for b in ids if not found[b][1]]


def blocks(design: str, until: str | None = None) -> dict[str, tuple[str, bool]]:
    """節の中の `### D-n` ごとのフェンスの中身を `D-n#i`（i は 1 から）で返す。

    値は (中身, 照合するか)。info に `noverify` の語があるフェンスは照合しない。
    `### D-n` の下にない照合するフェンスは、照合から黙って外れるので止める。"""
    out: dict[str, tuple[str, bool]] = {}
    seen: set[str] = set()
    current: str | None = None
    count = 0
    fence: str | None = None
    indent = 0
    check = True
    buf: list[str] = []
    for n, line in enumerate(section_lines(design, until)[0][1:], 2):
        if fence is None:
            m = BLOCK_HEADING_RE.match(line)
            if m:
                if m.group(1) in seen:
                    raise InputError(f"design.md: `### {m.group(1)}` が 2 つある")
                seen.add(m.group(1))
                current, count = m.group(1), 0
                continue
            if HEADING_RE.match(line):
                current = None
                continue
            m = _fence_open(line)
            if m is not None:
                fence, buf = m.group("marker"), []
                indent = len(line) - len(line.lstrip(" \t"))
                check = NOVERIFY not in m.group("info").split()
                if current is None and check:
                    raise InputError(
                        f"確定文面の {n} 行目: `### D-<n> <題>` の下にないフェンス（照合しないなら info に {NOVERIFY} を書く）"
                    )
            continue
        if _fence_closes(line, fence):
            fence = None
            if current is not None:
                count += 1
                out[f"{current}#{count}"] = ("\n".join(buf), check)
            continue
        buf.append(_dedent(line, indent))
    return out


def _substitute(text: str, subs: dict[str, str]) -> str:
    for key, value in subs.items():
        text = text.replace(key, value)
    return text


def _expand(
    text: str, found: dict[str, tuple[str, bool]], subs: dict[str, str], where: str, used: set[str] | None = None
) -> str:
    """`{{D-n#i}}` を block の中身（置換の後）に展開する。`used` を渡すと、展開した id を足す。"""
    def repl(m: re.Match) -> str:
        bid = m.group(1)
        if bid not in found:
            raise InputError(f"{where}: block {bid} が design.md の確定文面に無い")
        if not found[bid][1]:
            raise InputError(f"{where}: block {bid} は {NOVERIFY}（照合しない）なので参照できない")
        if used is not None:
            used.add(bid)
        return _substitute(found[bid][0], subs)

    return PLACEHOLDER_RE.sub(repl, text)


def _parse_subs(pairs: list[str]) -> dict[str, str]:
    subs: dict[str, str] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise InputError(f"--sub {pair!r}: KEY=VALUE の形でない")
        subs[key] = value
    return subs


def _require(obj: object, keys: set[str], required: set[str], where: str, strings: set[str]) -> dict:
    if not isinstance(obj, dict):
        raise InputError(f"{where}: object でない")
    unknown = set(obj) - keys
    if unknown:
        raise InputError(f"{where}: 知らない key {sorted(unknown)}")
    missing = required - set(obj)
    if missing:
        raise InputError(f"{where}: key {sorted(missing)} が無い")
    for key in strings & set(obj):
        if not isinstance(obj[key], str):
            raise InputError(f"{where}.{key}: 文字列でない")
    return obj


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(_read(path))
    except json.JSONDecodeError as exc:
        raise InputError(f"{path}: JSON として読めない ({exc})") from exc
    _require(data, MANIFEST_KEYS, {"digest", "files"}, "manifest", {"digest", "section_end"})
    subs = data.get("substitutions", {})
    if not isinstance(subs, dict) or not all(isinstance(k, str) and k and isinstance(v, str) for k, v in subs.items()):
        raise InputError("manifest.substitutions: 文字列から文字列への object でない")
    if not isinstance(data["files"], list) or not data["files"]:
        raise InputError("manifest.files: 空でない配列でない")
    paths: set[str] = set()
    for n, entry in enumerate(data["files"]):
        where = f"manifest.files[{n}]"
        _require(entry, FILE_KEYS, {"path"}, where, {"path", "content"})
        kinds = [k for k in ("edits", "content", "sections") if k in entry]
        if len(kinds) != 1:
            raise InputError(f"{where}: edits・content・sections のどれか 1 つだけを書く")
        rel = entry["path"]
        if not rel or rel.startswith("/") or "\\" in rel or any(s in ("", ".", "..") for s in rel.split("/")):
            raise InputError(f"{where}: path {rel!r} は repo からの相対の正規形で書く（先頭の /、.・..・空の段、\\ を使わない）")
        if rel.casefold() in paths:
            raise InputError(f"{where}: path {rel} が 2 回ある（大文字小文字の違いを含む）")
        paths.add(rel.casefold())
        for kind, keys, required in (("edits", EDIT_KEYS, {"old", "new"}), ("sections", SECTION_KEYS, {"start", "end", "text"})):
            if kind in entry:
                if not isinstance(entry[kind], list) or not entry[kind]:
                    raise InputError(f"{where}.{kind}: 空でない配列でない")
                for m, item in enumerate(entry[kind]):
                    _require(item, keys, required, f"{where}.{kind}[{m}]", keys)
    return data


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    except OSError as exc:
        raise InputError(f"git を起動できない ({exc})") from exc


def _base_files(repo: Path, base: str) -> set[str]:
    r = _git(repo, "ls-tree", "-r", "--name-only", "-z", base)
    if r.returncode != 0:
        raise InputError(f"git ls-tree {base[:12]} が失敗した ({r.stderr.decode(errors='replace').strip()})")
    return {p for p in r.stdout.decode("utf-8", errors="surrogateescape").split("\0") if p}


def _git_show(repo: Path, base: str, rel: str, base_files: set[str]) -> bytes | None:
    if rel not in base_files:
        folded = [p for p in base_files if p.casefold() == rel.casefold()]
        if folded:
            raise InputError(f"path {rel} は base の {folded[0]} と大文字小文字だけが違う（base の綴りで書く）")
        return None
    r = _git(repo, "show", f"{base}:{rel}")
    if r.returncode != 0:
        raise InputError(f"git show {base[:12]}:{rel} が失敗した ({r.stderr.decode(errors='replace').strip()})")
    return r.stdout


def _resolve_base(repo: Path, base: str | None) -> str:
    cmd = ["rev-parse", "--verify", f"{base}^{{commit}}"] if base else ["merge-base", "origin/main", "HEAD"]
    r = _git(repo, *cmd)
    out = r.stdout.decode(errors="replace").strip()
    if r.returncode != 0 or not out:
        raise InputError(f"base を決められない: git {' '.join(cmd)}: {r.stderr.decode(errors='replace').strip()}")
    return out


def _once(text: str, needle: str, where: str) -> int:
    if not needle:
        raise InputError(f"{where}: 空の文字列は場所を決められない")
    first = text.find(needle)
    if first < 0:
        raise InputError(f"{where}: 1 回もあたらない")
    if text.find(needle, first + 1) >= 0:  # 重なる出現も数える
        raise InputError(f"{where}: 2 回以上あたる（1 回だけあたる文にする）")
    return first


def _diff(want: str, got: str) -> list[str]:
    lines = list(difflib.unified_diff(want.splitlines(True), got.splitlines(True), "expected", "actual"))
    return [line.rstrip("\n").replace("\r", "\\r") for line in lines[:40]]


def verify(args: argparse.Namespace) -> int:
    design = _read(Path(args.design))
    manifest = load_manifest(Path(args.manifest))
    until = manifest.get("section_end")
    got_digest, nlines, _, found = digest(design, until)
    if got_digest != manifest["digest"]:
        print(f"DIFFERENT digest: design.md の確定文面 sha256={got_digest} lines={nlines}、manifest の承認時の digest={manifest['digest']}")
        print("RESULT: DIFFERENT")
        return 1
    used: set[str] = set()
    subs = manifest.get("substitutions", {})
    repo = Path(args.repo)
    actual_root = Path(args.actual) if args.actual else repo
    base = _resolve_base(repo, args.base)
    base_files = _base_files(repo, base)
    checks: list[tuple[str, str, bytes | None]] = []  # (表示名, 期待値, 実物)
    for n, entry in enumerate(manifest["files"]):
        rel = entry["path"]
        where = f"manifest.files[{n}] ({rel})"
        try:
            actual = (actual_root / rel).read_bytes()
        except FileNotFoundError:
            actual = None
        except OSError as exc:
            raise InputError(f"{where}: 実物を読めない ({exc})") from exc
        base_bytes = _git_show(repo, base, rel, base_files)
        if "content" in entry:
            if base_bytes is not None:
                raise InputError(f"{where}: content は base に無い新しいファイルにだけ使う（base {base[:12]} にある）")
            checks.append((rel, _expand(entry["content"], found, subs, where, used), actual))
        elif "edits" in entry:
            if base_bytes is None:
                raise InputError(f"{where}: base {base[:12]} に無い（新しいファイルは content か sections で書く）")
            text = _decode(base_bytes, f"{base[:12]}:{rel}")
            for m, edit in enumerate(entry["edits"]):
                w = f"{where}.edits[{m}]"
                old = _expand(edit["old"], found, subs, w)
                i = _once(text, old, w + ".old")
                text = text[:i] + _expand(edit["new"], found, subs, w, used) + text[i + len(old):]
            checks.append((rel, text, actual))
        else:
            if base_bytes is not None:
                raise InputError(f"{where}: sections は base に無い新しいファイルにだけ使う（base {base[:12]} にある。edits で書く）")
            got_text = _decode(actual, rel) if actual is not None else None
            for m, sec in enumerate(entry["sections"]):
                w = f"{where}.sections[{m}]"
                want = _expand(sec["text"], found, subs, w, used)
                if got_text is None:
                    checks.append((f"{rel} [sections[{m}]]", want, None))
                    continue
                s = _once(got_text, sec["start"], w + ".start")
                e = _once(got_text, sec["end"], w + ".end")
                if e < s:
                    raise InputError(f"{w}: end が start より前にある")
                checks.append((f"{rel} [sections[{m}]]", want, got_text[s:e].encode("utf-8")))
    ok = True
    for name, want, actual in checks:
        if actual is not None and want.encode("utf-8") == actual:
            print(f"SAME {name}")
            continue
        ok = False
        print(f"DIFFERENT {name}")
        if actual is None:
            print("  実物のファイルが無い")
        else:
            for line in _diff(want, _decode(actual, name)):
                print("  " + line)
    checked, skipped = _block_lists(found)
    for bid in (b for b in checked if b not in used):
        ok = False
        print(f"DIFFERENT {bid}: 照合する block を manifest の new・content・text のどれも参照していない")
    print(f"照合した block: {' '.join(sorted(used, key=_bid_key)) or 'なし'}")
    print(f"照合しない block（{NOVERIFY}）: {' '.join(skipped) or 'なし'}")
    print(f"base: {base}")
    print("RESULT: SAME" if ok else "RESULT: DIFFERENT")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("digest")
    p.add_argument("--design", required=True)
    p.add_argument("--until")
    p = sub.add_parser("extract")
    p.add_argument("--design", required=True)
    p.add_argument("--until")
    p.add_argument("--block", required=True)
    p.add_argument("--sub", action="append", default=[])
    p = sub.add_parser("verify")
    p.add_argument("--design", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--repo", default=".")
    p.add_argument("--base")
    p.add_argument("--actual")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "digest":
            value, nlines, end, found = digest(_read(Path(args.design)), args.until)
            checked, skipped = _block_lists(found)
            print(f"sha256={value} lines={nlines}")
            print(f"end: {end}")
            print(f"照合する block: {' '.join(checked) or 'なし'}")
            print(f"照合しない block（{NOVERIFY}）: {' '.join(skipped) or 'なし'}")
            return 0
        if args.cmd == "extract":
            if not BLOCK_ID_RE.match(args.block):
                raise InputError(f"--block {args.block!r}: D-n#i の形でない")
            found = blocks(_read(Path(args.design)), args.until)
            if args.block not in found:
                raise InputError(f"block {args.block} が design.md の確定文面に無い")
            sys.stdout.write(_substitute(found[args.block][0], _parse_subs(args.sub)))
            return 0
        return verify(args)
    except InputError as exc:
        print(f"confirmed-text: ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # 想定外の例外も「判定できない」にし、不一致（1）と取り違えさせない
        print(f"confirmed-text: ERROR: 想定外の例外 {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
