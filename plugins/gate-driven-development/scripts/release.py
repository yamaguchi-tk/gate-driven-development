#!/usr/bin/env python3
"""`changelog.d/` の断片から次の版を作る（リリースのときだけ実行する）。

通常の PR は版数系のファイル（3 manifest・`CHANGELOG.md` の版見出し・`docs/VERSIONING.md` の現状）に
触れず、`changelog.d/<YYYYMMDD>-<slug>.md` に断片を 1 つ足す。このスクリプトは断片の種別の最大値
（breaking > minor > patch）から次の版数を決め、次の 4 つをまとめて行う:

1. 3 manifest の version を上げる
2. `docs/VERSIONING.md` § 現状 の「現行バージョン」を更新する
3. 断片を `CHANGELOG.md` の新しい版の節に集める
4. 断片ファイルを削除する

既定は dry-run（何も書かない）。書き込むのは `--apply` のときだけで、commit と tag は行わない。
断片が 0 件なら何もしない。正本: `docs/VERSIONING.md` § リリース手順
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT_DIR = "changelog.d"
MANIFESTS = (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json", ".codex-plugin/plugin.json")
KINDS = ("patch", "minor", "breaking")  # 小さい順
NAME_RE = re.compile(r"\d{8}-[a-z0-9][a-z0-9-]*\.md")
FRONTMATTER_RE = re.compile(r"---\ntype: (\S*)\n---\n")
HEADING_RE = re.compile(r"(#{1,4}) (.+)")
SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
# CHANGELOG § Entry Template の節の順。ここに無い節（Known limitations 等）は Affected Files の直前に置く
SECTION_ORDER = (
    "Summary",
    "Added",
    "Changed",
    "Fixed",
    "Breaking Contract Changes",
    "Affected Files",
    "User Action Required",
    "Validation / Eval Impact",
)
REQUIRED_SECTIONS = ("Summary", "Affected Files", "User Action Required", "Validation / Eval Impact")
CURRENT_VERSION_RE = re.compile(r"(\*\*現行バージョン\*\*: v)(\d+\.\d+\.\d+)")
RELEASED_HEADING_RE = re.compile(r"^### \[(\d+\.\d+\.\d+)\] - ", re.M)
RELEASE_NOTES_ANCHOR = "## Current Release Notes\n\n"
ARCHIVE_ROTATION_LINES = 1200  # CHANGELOG.md § Archive の回転トリガ


@dataclass
class Fragment:
    path: Path
    kind: str
    sections: list[tuple[str, str]]  # (見出し, 本文)


def parse_fragment(path: Path) -> tuple[Fragment | None, list[str]]:
    name = path.name
    errors = []
    if not NAME_RE.fullmatch(name):
        errors.append(f"{name}: file name must be <YYYYMMDD>-<slug>.md (slug: a-z, 0-9, -)")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return None, [*errors, f"{name}: cannot read: {error}"]
    matched = FRONTMATTER_RE.match(text)
    if not matched:
        return None, [*errors, f"{name}: must start with the frontmatter '---' / 'type: <{'|'.join(KINDS)}>' / '---'"]
    kind = matched.group(1)
    if kind not in KINDS:
        errors.append(f"{name}: type must be one of {', '.join(KINDS)} (got {kind!r})")

    sections: list[tuple[str, list[str]]] = []
    in_fence = False
    for line in text[matched.end():].splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        heading = None if in_fence else HEADING_RE.fullmatch(line)
        if heading and len(heading.group(1)) == 4:
            sections.append((heading.group(2).strip(), []))
        elif heading:
            errors.append(f"{name}: only '#### ' headings are allowed (got {line!r})")
        elif sections:
            sections[-1][1].append(line)
        elif line.strip():
            errors.append(f"{name}: text before the first '#### ' section ({line!r})")
            break

    bodies = {heading: "\n".join(lines).strip("\n") for heading, lines in sections}
    for required in REQUIRED_SECTIONS:
        if not bodies.get(required, "").strip():
            errors.append(f"{name}: missing or empty section '#### {required}'")
    if kind == "breaking" and not bodies.get("Breaking Contract Changes", "").strip():
        errors.append(f"{name}: type 'breaking' needs a '#### Breaking Contract Changes' section")
    if errors:
        return None, errors
    return Fragment(path, kind, [(heading, "\n".join(lines).strip("\n")) for heading, lines in sections]), []


def load_fragments(root: Path) -> tuple[list[Fragment], list[str]]:
    """断片をファイル名の順に読む。ドットファイル（.DS_Store 等）は無視する。"""
    directory = root / FRAGMENT_DIR
    if not directory.is_dir():
        return [], []
    fragments, errors = [], []
    for path in sorted(directory.iterdir()):
        if path.name.startswith(".") or not path.is_file():
            continue
        fragment, problems = parse_fragment(path)
        errors.extend(problems)
        if fragment:
            fragments.append(fragment)
    return fragments, errors


def next_version(current: str, kinds) -> str:
    """種別の最大値で上げる。v0.x の breaking は minor を上げる（docs/VERSIONING.md § バージョン体系）。"""
    major, minor, patch = (int(part) for part in SEMVER_RE.fullmatch(current).groups())
    top = max(kinds, key=KINDS.index)
    if top == "breaking" and major >= 1:
        return f"{major + 1}.0.0"
    if top == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return f"{major}.{minor + 1}.0"


def render_section(version: str, date: str, fragments: list[Fragment]) -> str:
    merged: dict[str, list[str]] = {}
    for fragment in fragments:
        for heading, body in fragment.sections:
            if body.strip():
                merged.setdefault(heading, []).append(body)
    split = SECTION_ORDER.index("Affected Files")
    extras = [heading for heading in merged if heading not in SECTION_ORDER]
    parts = [f"### [{version}] - {date}"]
    for heading in (*SECTION_ORDER[:split], *extras, *SECTION_ORDER[split:]):
        if heading in merged:
            parts += [f"#### {heading}", "\n\n".join(merged[heading])]
    return "\n\n".join(parts) + "\n\n"


def read_current_version(root: Path) -> tuple[str, list[str]]:
    versions, errors = {}, []
    for rel in MANIFESTS:
        try:
            version = json.loads((root / rel).read_text(encoding="utf-8")).get("version")
        except (OSError, ValueError, AttributeError) as error:
            errors.append(f"cannot read the version of {rel}: {error}")
            continue
        if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
            errors.append(f"{rel}: version is not semver: {version!r}")
            continue
        versions[rel] = version
    if not errors and len(set(versions.values())) != 1:
        errors.append(f"the 3 manifests disagree on the version: {versions}")
    return (next(iter(versions.values())) if not errors else ""), errors


def plan_writes(root: Path, current: str, new: str, section: str) -> tuple[dict[Path, str], list[str]]:
    """書き込む内容を先に全部作る。1 つでも作れなければ何も書かない。"""
    writes, errors = {}, []
    for rel in MANIFESTS:
        text = (root / rel).read_text(encoding="utf-8")
        updated, count = re.subn(rf'("version"\s*:\s*"){re.escape(current)}"', rf'\g<1>{new}"', text)
        if count != 1:
            errors.append(f"{rel}: expected exactly one \"version\": \"{current}\" (found {count})")
        writes[root / rel] = updated

    versioning = root / "docs" / "VERSIONING.md"
    text = versioning.read_text(encoding="utf-8")
    found = CURRENT_VERSION_RE.findall(text)
    if len(found) != 1 or found[0][1] != current:
        errors.append(f"docs/VERSIONING.md: expected one '**現行バージョン**: v{current}' line (found {found})")
    writes[versioning] = CURRENT_VERSION_RE.sub(rf"\g<1>{new}", text)

    changelog = root / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    released = RELEASED_HEADING_RE.findall(text)
    if text.count(RELEASE_NOTES_ANCHOR) != 1:
        errors.append("CHANGELOG.md: expected exactly one '## Current Release Notes' heading")
    elif not released or released[0] != current:
        errors.append(f"CHANGELOG.md: the top released heading is {released[:1]} but the manifests are v{current}")
    writes[changelog] = text.replace(RELEASE_NOTES_ANCHOR, RELEASE_NOTES_ANCHOR + section, 1)
    return writes, errors


def apply_writes(writes: dict[Path, str], fragments: list[Path]) -> None:
    """`--apply` の全ての変更を 1 つの操作として行う。
    (1) 新しい内容を一時ファイルへ書く (2) 書き込み対象を全てバックアップへ退避する
    (3) 一時ファイルを本体へ置換する (4) 断片を削除する。
    (1)〜(4) のどこで失敗しても、退避したバックアップと読み込んでおいた断片の中身を使って
    手順開始前の状態へ戻してから例外を送出する（部分的な置換・断片の消し残りを残さない）。
    全て終わったら、もう不要になった書き込み対象のバックアップを削除する
    （これが失敗しても新しい内容自体は確定済みで正しいので、ベストエフォートでよい）。"""
    pid = os.getpid()
    news: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    fragment_backup: dict[Path, bytes] = {}
    try:
        for path, text in writes.items():
            temp = path.with_name(f".{path.name}.new{pid}")
            temp.write_text(text, encoding="utf-8")
            news[path] = temp

        for path in writes:
            backup = path.with_name(f".{path.name}.bak{pid}")
            os.replace(path, backup)
            backups[path] = backup

        for path, temp in news.items():
            os.replace(temp, path)

        for fragment in fragments:
            fragment_backup[fragment] = fragment.read_bytes()
            fragment.unlink()
    except OSError:
        for fragment, data in fragment_backup.items():
            if not fragment.exists():
                fragment.write_bytes(data)
        for path, backup in backups.items():
            if backup.exists():
                os.replace(backup, path)
        raise
    finally:
        for temp in news.values():
            if temp.exists():
                temp.unlink()

    for backup in backups.values():
        try:
            backup.unlink()
        except OSError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--apply", action="store_true", help="write the changes (default: dry-run)")
    parser.add_argument("--date", type=datetime.date.fromisoformat, default=datetime.date.today(), help="YYYY-MM-DD")
    args = parser.parse_args(argv)

    fragments, errors = load_fragments(ROOT)
    if not fragments and not errors:
        print(f"nothing to release: {FRAGMENT_DIR}/ has no fragments")
        return 0
    current, version_errors = read_current_version(ROOT)
    errors += version_errors
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    new = next_version(current, [fragment.kind for fragment in fragments])
    section = render_section(new, args.date.isoformat(), fragments)
    writes, errors = plan_writes(ROOT, current, new, section)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    top = max((fragment.kind for fragment in fragments), key=KINDS.index)
    print(f"{'release' if args.apply else 'dry-run: would release'} v{new} (current v{current}; largest fragment type: {top})")
    for fragment in fragments:
        print(f"  {FRAGMENT_DIR}/{fragment.path.name} ({fragment.kind})")
    print(f"\n--- CHANGELOG.md ---\n{section}--- end ---")
    if not args.apply:
        print("dry-run: nothing written. Run again with --apply to write these changes.")
        return 0

    try:
        apply_writes(writes, [fragment.path for fragment in fragments])
    except OSError as error:
        print(f"ERROR: failed to write release files, nothing changed: {error}", file=sys.stderr)
        return 1
    print(f"updated {', '.join(MANIFESTS)}, docs/VERSIONING.md, CHANGELOG.md; deleted {len(fragments)} fragment(s).")
    lines = writes[ROOT / "CHANGELOG.md"].count("\n")
    if lines >= ARCHIVE_ROTATION_LINES:
        print(f"NOTE: CHANGELOG.md is {lines} lines (>= {ARCHIVE_ROTATION_LINES}). Rotate it per CHANGELOG.md § Archive.")
    print("Next: run the checks in docs/VERSIONING.md § リリース手順, then commit and tag (this script does neither).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
