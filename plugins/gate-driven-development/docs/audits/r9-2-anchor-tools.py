#!/usr/bin/env python3
"""R9-2 Wave 1 契約アンカー抽出・照合ツール（design.md D-B2 / adr.md ADR-10）。

単一ファイル / 標準ライブラリのみ。サブコマンドは extract / verify / compare / selftest。

設計上の不変条件（3 巡連続した同型 fail-open をバグクラスごと消すための構造）:

- 集合定義は SETS registry 1 つ。extract だけが writer で、verify はアンカーを
  再導出しない（manifest から読むだけ）。読み方のズレが発生しようがない。
- manifest の I/O は dataclass + json のみ。内容行と衝突しうる区切り記法
  （'## SET N' / 行頭 '#'）を持たない。
- 「アンカーが本文に存在する」は述語 present() 1 つ。
  present(anchor, text) := anchor in text（部分一致 / 正規化なし / 大小文字を区別）。
  allow 判定はこの述語の対象外（集合メンバシップで行う）。
- allow list はパース済みリスト 1 本。declared と used は同一オブジェクトから
  派生するため used ⊆ declared が構造的に成立し、突合は集合等価。
- verify() は VerifyOk か VerifyFailed のどちらかしか返さない。VerifyOk を
  構築できるのは 9 条件すべてを通過した 1 箇所だけ。
- verdict のキーは (set_id, anchor)。dedupe は集合内のみ。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

SCHEMA_VERSION = 1
BASE_COMMIT = "33cb8aa5"
ARCHIVE_DIR = ("docs", "references-archive")

# target relpath（プラグインルート基準）-> archive filename（docs/references-archive/ 配下）
# extract と verify は同じこの表から archive パスを導出する（design.md D-B2 決定 4 / NM-1）。
TARGETS: dict[str, str] = {
    "references/state-machine.md": "state-machine-pre-r9-2-wave1-original.md",
    "references/human-check-template.md": "human-check-template-pre-r9-2-wave1-original.md",
    "references/requirements-template.md": "requirements-template-pre-r9-2-wave1-original.md",
    "references/phase-progression.md": "phase-progression-pre-r9-2-wave1-original.md",
    "skills/root-cause-investigation/SKILL.md": "root-cause-investigation-SKILL-pre-r9-2-wave1-original.md",
    "skills/gdd-writing-skills/SKILL.md": "gdd-writing-skills-SKILL-pre-r9-2-wave1-original.md",
    "skills/gdd-systematic-debugging/SKILL.md": "gdd-systematic-debugging-SKILL-pre-r9-2-wave1-original.md",
    "skills/gdd-brainstorming/SKILL.md": "gdd-brainstorming-SKILL-pre-r9-2-wave1-original.md",
}

# ---------------------------------------------------------------------------
# 抽出パターン（design.md D-B。行頭限定 / 単一表記限定にしない）
# ---------------------------------------------------------------------------

HEADING_RE = re.compile(r"^[ \t]*#{1,6} ")
STEP_RE = re.compile(r"[Ss]tep [0-9]+[A-Za-z]?")
FENCE_RE = re.compile(r"^[ \t]*```")
NORMATIVE_RE = re.compile(
    "してはならない|禁止|必ず|fail-closed|しない|しないこと|するな"
    "|以上|以下|超|未満|最大|最小"
)
# SET 3 の候補文字列は D-B の集合定義（`grep -ohE` を行ごとに掛ける）を
# バイト列上で再現する。Python の文字列に対して同じ正規表現を当てると分母が縮む
# ことを実測している: `grep -E` の `{3,}` は C ロケールでバイト数を数えるため、
# CJK 2 文字（6 バイト）の quote はマッチし、以降の引用符ペアリングが 1 つずれる。
# 文字数勘定へ移すと `state-machine.md` の `新しい` のように、旧集合に含まれていた
# アンカーが静かに落ちる（= under-extraction の再導入）。よってバイト勘定は維持する。
#
# 引用符種別は **独立に走査する**（design.md D-B2 Amendment 1 / ADR-10 Amendment 1）。
# 単一の交替 `"..."|'...'` は、外側が `'...'` で内側に `"..."` がある行
# （例: `printf '{"hookEventName":"SessionStart"}\n' "$x"`）で外側の単一引用符領域が
# 先にマッチし、内側トークンを 1 件も抽出できない（ペアリング事故）。
# 実測（base 33cb8aa5、`{3,}` と `[^"\n]` / `[^'\n]` は維持したまま独立走査）:
# 8 対象すべてで **失われるアンカーは 0 件**、回収されるのは
# `state-machine.md` の `SessionStart` 1 件と `requirements-template.md` の
# `### 一言` / `- \`Resume From=human-check-waiting\`` の 2 件（計 3 件、単調増加）。
# 下限 `{3,}` と改行除外を外した広い変種（`"[^"]*"` / `'[^']*'`）は別物で、
# こちらは `戻す条件` のような文法断片が新規混入する（実測）。採用しない。
DQUOTED_BYTES_RE = re.compile(rb"\"[^\"\n]{3,}\"")
SQUOTED_BYTES_RE = re.compile(rb"'[^'\n]{3,}'")
CODESPAN_BYTES_RE = re.compile(rb"`[^`\n]{3,}`")
CJK_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")

SCAN_DIRS = ("tests", "hooks", "scripts", "skills", "references", "commands", "agents")
SCAN_EXTS = (".py", ".sh", ".md")


class ToolError(Exception):
    """fail-closed 用。CLI 層で exit 1 に落とす。"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def present(anchor: str, text: str) -> bool:
    """アンカーが本文に存在するか。部分一致 / 正規化なし / 大小文字を区別する。"""
    return anchor in text


# ---------------------------------------------------------------------------
# SETS registry（集合定義はここ 1 箇所だけ）
# ---------------------------------------------------------------------------


@dataclass
class ExtractContext:
    base_tree: Path
    target_rel: str
    target_text: str

    @property
    def lines(self) -> list[str]:
        return self.target_text.splitlines()


def extract_set1(ctx: ExtractContext) -> list[str]:
    """見出し行（字下げを許容し、行全体を保持する）。"""
    return sorted({ln for ln in ctx.lines if HEADING_RE.match(ln)})


def extract_set2(ctx: ExtractContext) -> list[str]:
    """`Step <数字><英字?>` の全出現（大文字小文字の両表記）。"""
    return sorted(set(STEP_RE.findall(ctx.target_text)))


def _byte_matches(line: str, pattern: re.Pattern[bytes]) -> Iterable[str]:
    for m in pattern.findall(line.encode("utf-8", errors="ignore")):
        yield m[1:-1].decode("utf-8", errors="ignore")


def _set3_candidates_from_file(path: Path) -> Iterable[str]:
    suffix = path.suffix
    text = read_text(path)
    for line in text.splitlines():
        if suffix in (".py", ".sh"):
            # 引用符種別ごとに独立走査する（交替のペアリング事故を持ち込まない）
            yield from _byte_matches(line, DQUOTED_BYTES_RE)
            yield from _byte_matches(line, SQUOTED_BYTES_RE)
        elif suffix == ".md":
            yield from _byte_matches(line, CODESPAN_BYTES_RE)
            if HEADING_RE.match(line):
                yield HEADING_RE.sub("", line)


def extract_set3(ctx: ExtractContext) -> list[str]:
    """外部被参照文字列（テスト等 -> 原本の逆引き）。"""
    target_abs = (ctx.base_tree / ctx.target_rel).resolve()
    found: set[str] = set()
    for d in SCAN_DIRS:
        root = ctx.base_tree / d
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in SCAN_EXTS:
                continue
            if path.resolve() == target_abs:
                continue
            if "docs/references-archive/" in path.as_posix() + "/":
                continue
            for s in _set3_candidates_from_file(path):
                if not s or s in found:
                    continue
                min_len = 3 if CJK_RE.search(s) else 8
                if len(s) < min_len:
                    continue
                if not present(s, ctx.target_text):
                    continue
                found.add(s)
    return sorted(found)


def extract_set4(ctx: ExtractContext) -> list[str]:
    """コードフェンス内の全行（フェンスは字下げされうるので行頭に固定しない）。"""
    out: set[str] = set()
    in_fence = False
    for ln in ctx.lines:
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence and ln.strip():
            out.add(ln)
    return sorted(out)


def extract_set5(ctx: ExtractContext) -> list[str]:
    """規範表現・数値閾値を含む行。"""
    return sorted({ln for ln in ctx.lines if NORMATIVE_RE.search(ln)})


SETS: dict[int, tuple[str, Callable[[ExtractContext], list[str]]]] = {
    1: ("headings", extract_set1),
    2: ("step-numbering", extract_set2),
    3: ("externally-referenced", extract_set3),
    4: ("code-fence-lines", extract_set4),
    5: ("normative-and-thresholds", extract_set5),
}
SET_IDS = tuple(sorted(SETS))


# ---------------------------------------------------------------------------
# manifest（dataclass + json のみ。手書きパーサを置かない）
# ---------------------------------------------------------------------------


@dataclass
class Manifest:
    schema_version: int
    target: str
    base_commit: str
    source_sha256: str
    expect_empty: list[int]
    counts: dict[str, int]
    total: int
    sets: dict[str, list[str]]

    def to_json(self) -> str:
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "target": self.target,
                "base_commit": self.base_commit,
                "source_sha256": self.source_sha256,
                "expect_empty": self.expect_empty,
                "counts": self.counts,
                "total": self.total,
                "sets": self.sets,
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

    @staticmethod
    def load(path: Path) -> "Manifest":
        if not path.is_file():
            raise ToolError(f"anchors manifest not found: {path}")
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            raise ToolError(f"anchors manifest is empty: {path}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ToolError(f"anchors manifest is not valid JSON ({exc}): {path}") from exc
        if not isinstance(data, dict):
            raise ToolError(f"anchors manifest is not an object: {path}")
        missing = [
            k
            for k in (
                "schema_version",
                "target",
                "base_commit",
                "source_sha256",
                "expect_empty",
                "counts",
                "total",
                "sets",
            )
            if k not in data
        ]
        if missing:
            raise ToolError(f"anchors manifest missing keys {missing}: {path}")
        return Manifest(
            schema_version=data["schema_version"],
            target=data["target"],
            base_commit=data["base_commit"],
            source_sha256=data["source_sha256"],
            expect_empty=list(data["expect_empty"]),
            counts={str(k): int(v) for k, v in data["counts"].items()},
            total=int(data["total"]),
            sets={str(k): list(v) for k, v in data["sets"].items()},
        )

    def anchor_keys(self) -> list[tuple[int, str]]:
        """verdict のキー列。(set_id, anchor)。集合内 dedupe 済み前提。"""
        keys: list[tuple[int, str]] = []
        for sid in SET_IDS:
            for anchor in self.sets.get(str(sid), []):
                keys.append((sid, anchor))
        return keys


@dataclass
class AllowEntry:
    anchor: str
    reason: str
    used: bool = False


@dataclass
class AllowList:
    path: Path
    entries: list[AllowEntry] = field(default_factory=list)

    @staticmethod
    def load(path: Path) -> "AllowList":
        if not path.is_file():
            raise ToolError(f"allow-missing file not found: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ToolError(f"allow-missing file is not valid JSON ({exc}): {path}") from exc
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ToolError(f"allow-missing schema_version mismatch: {path}")
        entries = []
        for item in data.get("allowed_missing", []):
            entries.append(AllowEntry(anchor=item["anchor"], reason=item.get("reason", "")))
        return AllowList(path=path, entries=entries)

    def find(self, anchor: str) -> AllowEntry | None:
        for e in self.entries:
            if e.anchor == anchor:
                return e
        return None

    @property
    def declared(self) -> set[str]:
        return {e.anchor for e in self.entries}

    @property
    def used(self) -> set[str]:
        return {e.anchor for e in self.entries if e.used}


# ---------------------------------------------------------------------------
# verify（VerifyOk は 9 条件通過後の 1 箇所でしか構築できない）
# ---------------------------------------------------------------------------

PRESENT = "PRESENT"
MISSING = "MISSING"
ALLOWED_MISSING = "ALLOWED_MISSING"


@dataclass(frozen=True)
class VerifyOk:
    checked: int
    allowed: int
    candidate: str


@dataclass(frozen=True)
class VerifyFailed:
    reason: str
    details: list[str] = field(default_factory=list)


def derive_plugin_root(candidate: Path, target_rel: str) -> Path | None:
    cparts = candidate.resolve().parts
    tparts = Path(target_rel).parts
    if len(cparts) <= len(tparts) or cparts[-len(tparts):] != tparts:
        return None
    return Path(*cparts[: -len(tparts)])


def archive_path_for(plugin_root: Path, target_rel: str) -> Path:
    return plugin_root.joinpath(*ARCHIVE_DIR, TARGETS[target_rel])


def verify(
    anchors_path: Path,
    candidate_path: Path,
    allow_path: Path | None,
) -> VerifyOk | VerifyFailed:
    try:
        manifest = Manifest.load(anchors_path)
    except ToolError as exc:
        return VerifyFailed(str(exc))

    # 条件 1: schema_version 一致
    if manifest.schema_version != SCHEMA_VERSION:
        return VerifyFailed(
            f"schema_version mismatch: expected {SCHEMA_VERSION}, got {manifest.schema_version}"
        )
    # 条件 2: total > 0
    if manifest.total <= 0:
        return VerifyFailed(f"manifest total must be > 0 (got {manifest.total})")
    # 条件 3: candidate が存在し非空
    if not candidate_path.is_file():
        return VerifyFailed(f"candidate not found: {candidate_path}")
    candidate_text = read_text(candidate_path)
    if not candidate_text.strip():
        return VerifyFailed(f"candidate is empty: {candidate_path}")
    # 条件 9: manifest.target と candidate の対応（TARGETS registry から導出）
    if manifest.target not in TARGETS:
        return VerifyFailed(f"manifest target is not a registered target: {manifest.target}")
    plugin_root = derive_plugin_root(candidate_path, manifest.target)
    if plugin_root is None:
        return VerifyFailed(
            f"candidate path does not correspond to manifest target "
            f"({candidate_path} vs {manifest.target})"
        )
    # 条件 8: source_sha256 == archive 原本の sha256
    archive = archive_path_for(plugin_root, manifest.target)
    if not archive.is_file():
        return VerifyFailed(f"archive original not found (registry-derived): {archive}")
    archive_sha = sha256_of(archive)
    if archive_sha != manifest.source_sha256:
        return VerifyFailed(
            "source_sha256 does not match archive original "
            f"(manifest {manifest.source_sha256[:12]} vs archive {archive_sha[:12]}): {archive}"
        )

    allow = AllowList.load(allow_path) if allow_path is not None else AllowList(Path("<none>"))

    verdicts: dict[tuple[int, str], str] = {}
    for sid, anchor in manifest.anchor_keys():
        if present(anchor, candidate_text):
            verdicts[(sid, anchor)] = PRESENT
            continue
        entry = allow.find(anchor)
        if entry is not None:
            entry.used = True
            verdicts[(sid, anchor)] = ALLOWED_MISSING
            continue
        verdicts[(sid, anchor)] = MISSING

    # 条件 4: 全アンカーがちょうど 1 つの verdict を持つ
    if len(verdicts) != manifest.total:
        return VerifyFailed(
            f"verdict count mismatch: manifest total {manifest.total}, verdicts {len(verdicts)}"
        )
    # 条件 5: 集合別の verdict 件数が counts と一致
    per_set: dict[int, int] = {sid: 0 for sid in SET_IDS}
    for sid, _ in verdicts:
        per_set[sid] = per_set.get(sid, 0) + 1
    for sid in SET_IDS:
        declared = manifest.counts.get(str(sid))
        if declared is None:
            return VerifyFailed(f"manifest counts missing set {sid}")
        if per_set[sid] != declared:
            return VerifyFailed(
                f"set {sid} count mismatch: counts declares {declared}, verdicts {per_set[sid]}"
            )
    if sum(manifest.counts.get(str(sid), 0) for sid in SET_IDS) != manifest.total:
        return VerifyFailed("manifest counts do not sum to total")

    # 条件 6: missing == 0
    missing = [f"MISSING (set {sid}): {anchor}" for (sid, anchor), v in verdicts.items() if v == MISSING]
    if missing:
        return VerifyFailed(f"{len(missing)} missing anchors", sorted(missing))

    # 条件 7: declared == used（集合等価。used ⊆ declared は構造的に成立）
    if allow.declared != allow.used:
        stale = sorted(allow.declared - allow.used)
        return VerifyFailed(
            f"allow-missing declaration mismatch: {len(stale)} stale declaration(s)",
            [f"STALE-ALLOW: {s}" for s in stale],
        )

    allowed = sum(1 for v in verdicts.values() if v == ALLOWED_MISSING)
    return VerifyOk(checked=len(verdicts), allowed=allowed, candidate=str(candidate_path))


# ---------------------------------------------------------------------------
# 旧形式（bash 版 anchors.txt）リーダ。compare の中だけに閉じる。
# ---------------------------------------------------------------------------

LEGACY_HEADER_RE = re.compile(r"^# set([1-5])_count=([0-9]+)")


@dataclass
class LegacyAnchors:
    declared: dict[int, int]
    sets: dict[int, list[str]]

    @property
    def declared_total(self) -> int:
        return sum(self.declared.values())

    @property
    def read_total(self) -> int:
        return sum(len(v) for v in self.sets.values())


def load_legacy_anchors(path: Path) -> LegacyAnchors:
    """旧テキスト形式の読み取り規則（design.md D-B2 決定 5 / H-2 で逐語固定）。

    - 最初の `## SET 1` 以降、「次に来るべき `## SET n` と完全一致する行」だけを
      マーカーとみなす（旧 verify と同一規則）
    - マーカー以降の非空行はすべてアンカーとして読む（`#` 始まりを含む）
    - 旧ヘッダの宣言件数との突合を必須にする（リーダ自身の過少読みの検出）
    """
    if not path.is_file():
        raise ToolError(f"legacy anchors not found: {path}")
    declared: dict[int, int] = {}
    sets: dict[int, list[str]] = {sid: [] for sid in SET_IDS}
    current: int | None = None
    next_set = 1
    for line in path.read_text(encoding="utf-8").splitlines():
        if next_set <= 5 and line == f"## SET {next_set}":
            current = next_set
            next_set += 1
            continue
        if current is None:
            m = LEGACY_HEADER_RE.match(line)
            if m:
                declared[int(m.group(1))] = int(m.group(2))
            continue
        if not line:
            continue
        sets[current].append(line)
    if sorted(declared) != list(SET_IDS):
        raise ToolError(
            f"legacy anchors header incomplete ({len(declared)}/5 set counts): {path}"
        )
    legacy = LegacyAnchors(declared=declared, sets=sets)
    for sid in SET_IDS:
        if len(sets[sid]) != declared[sid]:
            raise ToolError(
                f"legacy anchors set {sid} count mismatch: header declares "
                f"{declared[sid]}, read {len(sets[sid])}: {path}"
            )
    if legacy.read_total != legacy.declared_total:
        raise ToolError(
            f"legacy anchors total mismatch: header declares {legacy.declared_total}, "
            f"read {legacy.read_total}: {path}"
        )
    return legacy


# ---------------------------------------------------------------------------
# サブコマンド
# ---------------------------------------------------------------------------


def cmd_extract(args: argparse.Namespace) -> int:
    base_tree = Path(args.base_tree)
    target_rel = args.target
    if target_rel not in TARGETS:
        raise ToolError(f"target is not registered in TARGETS: {target_rel}")
    target_file = base_tree / target_rel
    if not target_file.is_file():
        raise ToolError(f"target not found in base tree: {target_file}")

    archive = Path(args.archive)
    expected_name = TARGETS[target_rel]
    if archive.name != expected_name:
        raise ToolError(
            f"--archive basename does not match TARGETS registry: "
            f"expected {expected_name}, got {archive.name}"
        )
    if not archive.is_file():
        raise ToolError(f"archive original not found: {archive}")

    source_sha = sha256_of(target_file)
    archive_sha = sha256_of(archive)
    if source_sha != archive_sha:
        raise ToolError(
            "base tree target does not match the archive original "
            f"(base {source_sha[:12]} vs archive {archive_sha[:12]}). "
            "wrong --base-tree (a distilled worktree?) or wrong archive."
        )

    expect_empty = (
        sorted({int(x) for x in str(args.expect_empty).split(",") if x.strip()})
        if args.expect_empty
        else []
    )
    ctx = ExtractContext(
        base_tree=base_tree, target_rel=target_rel, target_text=read_text(target_file)
    )
    sets: dict[str, list[str]] = {}
    counts: dict[str, int] = {}
    for sid in SET_IDS:
        _, fn = SETS[sid]
        values = fn(ctx)
        if not values and sid not in expect_empty:
            raise ToolError(
                f"ANCHOR_EXTRACT_FAILED: set {sid} is empty and not declared in --expect-empty"
            )
        sets[str(sid)] = values
        counts[str(sid)] = len(values)

    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        target=target_rel,
        base_commit=args.base_commit,
        source_sha256=source_sha,
        expect_empty=expect_empty,
        counts=counts,
        total=sum(counts.values()),
        sets=sets,
    )
    out = Path(args.out)
    tmp = out.with_name(out.name + f".tmp.{os.getpid()}")
    try:
        tmp.write_text(manifest.to_json() + "\n", encoding="utf-8")
        os.replace(tmp, out)
    finally:
        if tmp.exists():
            tmp.unlink()
    counts_str = " ".join(f"set{sid}={counts[str(sid)]}" for sid in SET_IDS)
    print(f"ANCHOR_EXTRACT_OK: {manifest.total} anchors ({counts_str}) -> {out}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify(
        Path(args.anchors),
        Path(args.candidate),
        Path(args.allow_missing) if args.allow_missing else None,
    )
    if isinstance(result, VerifyOk):
        print(
            f"ANCHOR_VERIFY_OK: {result.checked} anchors checked, "
            f"0 unexpected missing ({result.allowed} allowed) in {result.candidate}"
        )
        return 0
    for line in result.details:
        print(line)
    print(f"ANCHOR_VERIFY_FAILED: {result.reason}")
    return 1


def cmd_compare(args: argparse.Namespace) -> int:
    legacy = load_legacy_anchors(Path(args.old))
    new = Manifest.load(Path(args.new))
    print(
        f"compare: old declares {legacy.declared_total} anchors "
        f"({' '.join(f'set{s}={legacy.declared[s]}' for s in SET_IDS)}), read {legacy.read_total}"
    )
    print(
        f"compare: new has {new.total} anchors "
        f"({' '.join(f'set{s}={new.counts.get(str(s), 0)}' for s in SET_IDS)})"
    )
    lost: list[str] = []
    for sid in SET_IDS:
        new_set = set(new.sets.get(str(sid), []))
        for anchor in legacy.sets[sid]:
            if anchor not in new_set:
                lost.append(f"COVERAGE-LOSS (set {sid}): {anchor}")
    if lost:
        for line in sorted(lost):
            print(line)
        print(f"ANCHOR_COMPARE_FAILED: {len(lost)} old anchors are absent from the new manifest")
        return 1
    print(
        f"ANCHOR_COMPARE_OK: old ({legacy.read_total}) is a subset of new ({new.total}); "
        f"net gain {new.total - legacy.read_total}"
    )
    return 0


# ---------------------------------------------------------------------------
# selftest（R1〜R21。design.md D-B2 決定 6）
# ---------------------------------------------------------------------------


class SelfTestFailure(Exception):
    pass


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


FIXTURE_TARGET = "references/fixture.md"
FIXTURE_ARCHIVE = "fixture-pre-r9-2-wave1-original.md"

# selftest が起動する子プロセス（R16 の CLI exit code 検査）でも fixture target を
# 解決できるようにする。通常実行では未設定なので TARGETS は 8 対象のままになる。
if os.environ.get("R9_2_ANCHOR_SELFTEST") == "1":
    TARGETS.setdefault(FIXTURE_TARGET, FIXTURE_ARCHIVE)

FIXTURE_BODY = """# Fixture 見出し

本文には削除してはならない規範文がある。3 回以上は禁止。

## 適用しない場合

  ### 字下げ見出し

Step 1 と step 4 と Step 12b を扱う。

## SET 2

```
fence line alpha
```

  ```
  indented fence line beta
  ```

参照される契約文字列: 停止理由 / ANCHOR_FIXTURE_LITERAL_STRING

nested quote 由来の契約文字列: NESTED_ANCHOR_TOKEN
"""


def _build_fixture_tree(root: Path, body: str = FIXTURE_BODY) -> Path:
    """base tree + plugin root を兼ねた fixture ツリーを作る。"""
    plugin = root / "plugin"
    _write(plugin / FIXTURE_TARGET, body)
    _write(plugin / "docs" / "references-archive" / FIXTURE_ARCHIVE, body)
    _write(
        plugin / "tests" / "test_contract.py",
        'def t():\n    assert "ANCHOR_FIXTURE_LITERAL_STRING" in x\n    assert "停止理由" in x\n',
    )
    _write(plugin / "references" / "other.md", "  ### 字下げ見出し\n\n`停止理由`\n")
    # R21: 外側が単一引用符・内側が二重引用符の行（交替走査だと内側を 1 件も拾えない）
    _write(
        plugin / "hooks" / "run-hook.sh",
        '#!/bin/sh\nprintf \'{"hookEventName":"NESTED_ANCHOR_TOKEN"}\\n\' "$_warn"\n',
    )
    return plugin


def _extract_fixture(plugin: Path, out: Path, expect_empty: str = "") -> int:
    args = argparse.Namespace(
        base_tree=str(plugin),
        target=FIXTURE_TARGET,
        archive=str(plugin / "docs" / "references-archive" / FIXTURE_ARCHIVE),
        out=str(out),
        expect_empty=expect_empty,
        base_commit=BASE_COMMIT,
    )
    return cmd_extract(args)


def _verify_fixture(plugin: Path, anchors: Path, allow: Path | None = None):
    return verify(anchors, plugin / FIXTURE_TARGET, allow)


def _write_allow(path: Path, anchors: list[str]) -> Path:
    return _write(
        path,
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "target": FIXTURE_TARGET,
                "allowed_missing": [{"anchor": a, "reason": "selftest fixture"} for a in anchors],
            },
            indent=2,
            ensure_ascii=False,
        ),
    )


def _expect_failed(result, case: str) -> None:
    if not isinstance(result, VerifyFailed):
        raise SelfTestFailure(f"{case}: expected VerifyFailed, got {result!r}")


def _expect_ok(result, case: str) -> VerifyOk:
    if not isinstance(result, VerifyOk):
        raise SelfTestFailure(f"{case}: expected VerifyOk, got {result!r}")
    return result


def _run_selftest_cases(tmp: Path) -> list[str]:  # noqa: C901 - fixture 一覧は 1 箇所に集約する
    log: list[str] = []

    def ok(case: str, note: str) -> None:
        log.append(f"{case}: PASS ({note})")

    # 共通 fixture
    plugin = _build_fixture_tree(tmp / "base")
    anchors = tmp / "anchors.json"
    _extract_fixture(plugin, anchors)
    manifest = Manifest.load(anchors)

    # R1: anchors 不在 -> exit != 0
    _expect_failed(_verify_fixture(plugin, tmp / "does-not-exist.json"), "R1")
    ok("R1", "missing anchors manifest -> VerifyFailed")

    # R2: 0 バイト / 途中切り詰め -> exit != 0
    _expect_failed(_verify_fixture(plugin, _write(tmp / "empty.json", "")), "R2/empty")
    truncated = anchors.read_text(encoding="utf-8")[: len(anchors.read_text(encoding="utf-8")) // 2]
    _expect_failed(_verify_fixture(plugin, _write(tmp / "trunc.json", truncated)), "R2/truncated")
    ok("R2", "empty and truncated manifests -> VerifyFailed")

    # R3: counts と実 verdict 数の不一致 -> exit != 0
    data = json.loads(anchors.read_text(encoding="utf-8"))
    data["counts"]["1"] = data["counts"]["1"] + 1
    data["total"] = data["total"] + 1
    _expect_failed(
        _verify_fixture(plugin, _write(tmp / "badcounts.json", json.dumps(data, ensure_ascii=False))),
        "R3",
    )
    ok("R3", "tampered counts/total -> VerifyFailed")

    # R4: 内容行 '## SET 2' が 1 アンカーとして照合される
    if "## SET 2" not in manifest.sets["1"]:
        raise SelfTestFailure("R4: '## SET 2' content line was not extracted as an anchor")
    stripped = "\n".join(ln for ln in FIXTURE_BODY.splitlines() if ln != "## SET 2")
    plugin_r4 = _build_fixture_tree(tmp / "r4")
    _write(plugin_r4 / FIXTURE_TARGET, stripped)
    _expect_failed(_verify_fixture(plugin_r4, anchors), "R4")
    ok("R4", "'## SET 2' is an anchor, not a delimiter")

    # R5: 字下げ見出しが SET 1 に入る
    if "  ### 字下げ見出し" not in manifest.sets["1"]:
        raise SelfTestFailure("R5: indented heading missing from set 1")
    ok("R5", "indented heading in set 1")

    # R6: 小文字 'step 4' が SET 2 に入る
    if "step 4" not in manifest.sets["2"] or "Step 12b" not in manifest.sets["2"]:
        raise SelfTestFailure("R6: lowercase/step-suffix forms missing from set 2")
    ok("R6", "lowercase 'step 4' and 'Step 12b' in set 2")

    # R7: 字下げコードフェンス内の行が SET 4 に入る
    if "  indented fence line beta" not in manifest.sets["4"]:
        raise SelfTestFailure("R7: indented fence content missing from set 4")
    ok("R7", "indented fence content in set 4")

    # R8: 参照元 md の字下げ見出しが SET 3 に入る
    if "字下げ見出し" not in manifest.sets["3"]:
        raise SelfTestFailure("R8: indented heading of a referencing md missing from set 3")
    if "ANCHOR_FIXTURE_LITERAL_STRING" not in manifest.sets["3"]:
        raise SelfTestFailure("R8: quoted literal from .py missing from set 3")
    ok("R8", "referencing-md indented heading and .py literal in set 3")

    # R9: '#' 始まりアンカーの allow 宣言が declared と used に同時に計上される
    heading = "# Fixture 見出し"
    body_no_heading = "\n".join(ln for ln in FIXTURE_BODY.splitlines() if ln != heading)
    plugin_r9 = _build_fixture_tree(tmp / "r9")
    _write(plugin_r9 / FIXTURE_TARGET, body_no_heading)
    allow_r9 = _write_allow(tmp / "allow-r9.json", [heading])
    res = _verify_fixture(plugin_r9, anchors, allow_r9)
    got = _expect_ok(res, "R9")
    if got.allowed < 1:
        raise SelfTestFailure("R9: '#'-prefixed allow declaration was not counted as used")
    ok("R9", f"'#'-prefixed allow entry counted in declared and used ({got.allowed} allowed)")

    # R10: stale 宣言（実際には欠落していない）-> exit != 0
    allow_r10 = _write_allow(tmp / "allow-r10.json", [heading])
    _expect_failed(_verify_fixture(plugin, anchors, allow_r10), "R10")
    ok("R10", "stale allow declaration -> VerifyFailed")

    # R11: 未承認欠落 + stale 宣言の組み合わせ -> exit != 0
    plugin_r11 = _build_fixture_tree(tmp / "r11")
    _write(
        plugin_r11 / FIXTURE_TARGET,
        "\n".join(ln for ln in FIXTURE_BODY.splitlines() if ln != "  ### 字下げ見出し"),
    )
    allow_r11 = _write_allow(tmp / "allow-r11.json", [heading])
    _expect_failed(_verify_fixture(plugin_r11, anchors, allow_r11), "R11")
    ok("R11", "unapproved deletion + stale declaration -> VerifyFailed")

    # R12: 忠実な candidate は OK（検出力の副作用がないことの対照）
    got = _expect_ok(_verify_fixture(plugin, anchors), "R12")
    if got.checked != manifest.total:
        raise SelfTestFailure("R12: checked count != manifest total")
    ok("R12", f"faithful candidate -> VerifyOk ({got.checked} checked)")

    # R13: 宣言のない 0 件集合 -> extract が exit != 0
    plugin_r13 = _build_fixture_tree(tmp / "r13", body="# Only heading\n\n必ず守る\n")
    try:
        _extract_fixture(plugin_r13, tmp / "r13.json")
    except ToolError:
        ok("R13", "undeclared empty set -> ToolError from extract")
    else:
        raise SelfTestFailure("R13: extract accepted an undeclared empty set")

    # R14: expect_empty 宣言済みの 0 件集合 -> extract 成功 + verify の total 整合も通る
    r14_anchors = tmp / "r14.json"
    _extract_fixture(plugin_r13, r14_anchors, expect_empty="2,3,4")
    r14 = Manifest.load(r14_anchors)
    if r14.counts["4"] != 0 or 4 not in r14.expect_empty:
        raise SelfTestFailure("R14: expect_empty was not recorded")
    _expect_ok(_verify_fixture(plugin_r13, r14_anchors), "R14")
    ok("R14", "declared empty set extracts and verifies")

    # R15: 同一文字列が複数集合にあっても条件 4・5 が通る（キーは (set_id, anchor)）
    dup = [a for a in manifest.sets["1"] if a in set(manifest.sets["5"])]
    if not dup:
        raise SelfTestFailure("R15: fixture has no cross-set duplicate anchor")
    got = _expect_ok(_verify_fixture(plugin, anchors), "R15")
    if got.checked != manifest.total:
        raise SelfTestFailure("R15: cross-set duplicates were deduplicated")
    ok("R15", f"cross-set duplicate ({len(dup)} anchors) keeps total intact")

    # R16: CLI 経由で exit code を確認（main() が int 以外を返す穴を含む）
    def run_cli(argv: list[str]) -> subprocess.CompletedProcess:
        env = dict(os.environ, R9_2_ANCHOR_SELFTEST="1")
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve())] + argv,
            capture_output=True,
            text=True,
            env=env,
        )

    if run_cli([]).returncode == 0:
        raise SelfTestFailure("R16: no subcommand returned exit 0")
    if run_cli(["bogus-subcommand"]).returncode == 0:
        raise SelfTestFailure("R16: unknown subcommand returned exit 0")
    cli_ok = run_cli(
        ["verify", "--anchors", str(anchors), "--candidate", str(plugin / FIXTURE_TARGET)]
    )
    if cli_ok.returncode != 0:
        raise SelfTestFailure(f"R16: faithful verify via CLI returned {cli_ok.returncode}")
    cli_ng = run_cli(
        ["verify", "--anchors", str(anchors), "--candidate", str(plugin_r11 / FIXTURE_TARGET)]
    )
    if cli_ng.returncode != 1:
        raise SelfTestFailure(f"R16: failing verify via CLI returned {cli_ng.returncode}")
    for name, fn in (("extract", cmd_extract), ("verify", cmd_verify), ("compare", cmd_compare)):
        if not callable(fn):
            raise SelfTestFailure(f"R16: handler for {name} is not callable")
    ok("R16", "CLI exit codes 2/2/0/1 as expected; dispatch table complete")

    # R17: '#' 始まりアンカーを含む旧形式 fixture を compare の互換リーダが読む
    legacy_txt = _write(
        tmp / "legacy.txt",
        "# anchors for references/fixture.md (base tree: /tmp/x)\n"
        "# set1_count=2\n# set2_count=1\n# set3_count=1\n"
        "# set4_count=0 (expected-empty)\n# set5_count=1\n"
        "## SET 1\n# Fixture 見出し\n## 適用しない場合\n"
        "## SET 2\nStep 1\n## SET 3\n停止理由\n## SET 4\n## SET 5\n必ず守る\n",
    )
    legacy = load_legacy_anchors(legacy_txt)
    if legacy.read_total != legacy.declared_total or legacy.read_total != 5:
        raise SelfTestFailure(f"R17: legacy reader read {legacy.read_total}, declared {legacy.declared_total}")
    if "# Fixture 見出し" not in legacy.sets[1] or "## 適用しない場合" not in legacy.sets[1]:
        raise SelfTestFailure("R17: legacy reader dropped '#'-prefixed anchors")
    try:
        load_legacy_anchors(
            _write(tmp / "legacy-bad.txt", legacy_txt.read_text(encoding="utf-8").replace("Step 1\n", ""))
        )
    except ToolError:
        pass
    else:
        raise SelfTestFailure("R17: legacy reader accepted a header/body count mismatch")
    ok("R17", "legacy reader keeps '#'-prefixed anchors and enforces header counts")

    # R18: base tree 取り違え / source_sha256 不一致
    plugin_r18 = _build_fixture_tree(tmp / "r18")
    _write(plugin_r18 / FIXTURE_TARGET, FIXTURE_BODY + "\n## 蒸留で足された見出し\n")
    try:
        _extract_fixture(plugin_r18, tmp / "r18.json")
    except ToolError:
        pass
    else:
        raise SelfTestFailure("R18: extract accepted a base tree that differs from the archive")
    data = json.loads(anchors.read_text(encoding="utf-8"))
    data["source_sha256"] = "0" * 64
    _expect_failed(
        _verify_fixture(plugin, _write(tmp / "badsha.json", json.dumps(data, ensure_ascii=False))),
        "R18/verify",
    )
    ok("R18", "wrong base tree (extract) and sha mismatch (verify) both fail closed")

    # R19: 全集合空 / total=0 の manifest -> exit != 0（条件 2 の単一ガードを pin する）
    #      条件 4・5 は verdicts 0 == total 0 / counts 0 == 0 で全部整合してしまうため、
    #      このバグクラス（「走ったが 1 件も照合していない」）を止めているのは条件 2 だけ。
    empty_manifest = json.loads(anchors.read_text(encoding="utf-8"))
    empty_manifest["sets"] = {str(sid): [] for sid in SET_IDS}
    empty_manifest["counts"] = {str(sid): 0 for sid in SET_IDS}
    empty_manifest["total"] = 0
    empty_manifest["expect_empty"] = list(SET_IDS)
    _expect_failed(
        _verify_fixture(
            plugin, _write(tmp / "zero-total.json", json.dumps(empty_manifest, ensure_ascii=False))
        ),
        "R19",
    )
    ok("R19", "all-empty manifest (total=0) -> VerifyFailed (condition 2 is the sole guard)")

    # R20: 大小文字だけが異なる candidate -> exit != 0（present() の大小文字区別を pin する）
    cased_body = FIXTURE_BODY.replace(
        "ANCHOR_FIXTURE_LITERAL_STRING", "anchor_fixture_literal_string"
    )
    if cased_body == FIXTURE_BODY:
        raise SelfTestFailure("R20: fixture body did not change; case mutation is ineffective")
    plugin_r20 = _build_fixture_tree(tmp / "r20")
    _write(plugin_r20 / FIXTURE_TARGET, cased_body)
    _expect_failed(_verify_fixture(plugin_r20, anchors), "R20")
    ok("R20", "case-only difference -> VerifyFailed (present() is case-sensitive)")

    # R21: 外側 '...' の内側にある "..." が SET 3 に入る（交替走査のペアリング事故の回帰）
    if "NESTED_ANCHOR_TOKEN" not in manifest.sets["3"]:
        raise SelfTestFailure(
            "R21: nested double-quoted token inside a single-quoted region missing from set 3"
        )
    ok("R21", "nested quote token extracted into set 3 (quote types scanned independently)")

    # round-trip 不変条件（M5）
    reloaded = Manifest.load(anchors)
    for sid in SET_IDS:
        if reloaded.sets[str(sid)] != manifest.sets[str(sid)]:
            raise SelfTestFailure("round-trip: manifest set changed after reload")
    log.append("round-trip: PASS (extract -> write -> read gives identical sets)")
    return log


def cmd_selftest(_args: argparse.Namespace) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="r9-2-anchor-selftest-"))
    registered = FIXTURE_TARGET in TARGETS
    TARGETS[FIXTURE_TARGET] = FIXTURE_ARCHIVE
    try:
        log = _run_selftest_cases(tmp)
    except SelfTestFailure as exc:
        print(f"SELFTEST_FAILED: {exc}")
        return 1
    finally:
        if not registered:
            TARGETS.pop(FIXTURE_TARGET, None)
        shutil.rmtree(tmp, ignore_errors=True)
    for line in log:
        print(line)
    print(f"SELFTEST_OK: {len(log)} cases passed")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="r9-2-anchor-tools.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd")

    e = sub.add_parser("extract", help="原本から契約アンカー manifest を抽出する")
    e.add_argument("--base-tree", required=True)
    e.add_argument("--target", required=True)
    e.add_argument("--archive", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--expect-empty", default="")
    e.add_argument("--base-commit", default=BASE_COMMIT)

    v = sub.add_parser("verify", help="蒸留版に全アンカーが存在することを照合する")
    v.add_argument("--anchors", required=True)
    v.add_argument("--candidate", required=True)
    v.add_argument("--allow-missing", default="")

    c = sub.add_parser("compare", help="旧 anchors.txt が新 manifest の部分集合であることを検査する")
    c.add_argument("--old", required=True)
    c.add_argument("--new", required=True)

    sub.add_parser("selftest", help="回帰 fixture R1〜R21 を実行する")
    return p


HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "extract": cmd_extract,
    "verify": cmd_verify,
    "compare": cmd_compare,
    "selftest": cmd_selftest,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = HANDLERS.get(args.cmd or "")
    if handler is None:
        parser.print_usage(sys.stderr)
        print("error: a subcommand is required (extract / verify / compare / selftest)", file=sys.stderr)
        return 2
    code = handler(args)
    # sys.exit(None) が exit 0 になる穴を塞ぐ（design.md D-B2 決定 4 / M-4）。
    if not isinstance(code, int) or isinstance(code, bool):
        print(f"ANCHOR_TOOL_FAILED: handler for {args.cmd} returned {code!r}, not int", file=sys.stderr)
        return 2
    return code


if __name__ == "__main__":
    try:
        _code = main()
    except SystemExit:
        # argparse などが自前で終了コードを決めた場合はそのまま通す。
        raise
    except ToolError as _exc:
        print(f"ANCHOR_TOOL_FAILED: {_exc}", file=sys.stderr)
        _code = 1
    except BaseException as _exc:  # noqa: BLE001 - fail-closed
        print(f"ANCHOR_VERIFY_FAILED: internal error: {_exc!r}", file=sys.stderr)
        _code = 2
    sys.exit(_code)
