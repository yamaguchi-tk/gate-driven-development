#!/usr/bin/env python3
"""default branch を取り込むだけの merge commit に、旧 sha の `Independent Review` を引き継げるかを確かめる。

条件の正本: references/self-review-lanes.md § Independent Review の引き継ぎ。

    python3 ir_merge_carry.py <repo> <merge sha> <reviewed sha> <default branch ref> <残り秒>

引き継げるときだけ exit 0。引き継げないときは exit 1 で、理由を 1 行 stdout に出す。
git の失敗・時間切れ・想定外の例外も exit 1（引き継がない側。gate は今までどおり不足として通知する。
pre-push・pre-PR は independent-review-stale、merge gate は待機か独立レビューの要求）。`verified: diff-equal` の自己申告は読まず、条件は
すべて git から計算し直す。衝突したファイルの集合は、git が merge commit に記録を残さない
ので、`git merge-tree --write-tree --name-only` で 2 つの親から計算し直す。
"""
from __future__ import annotations

import re
import signal
import subprocess
import sys
import time

# 衝突ブロックの中で、両側のどちらの行でもない行の数の合計の上限（正本の (7)。依頼の (c)）。
# 2026-10-13 に GDD を使う別の repo の main の取り込みで測った最大 3 に余裕を足した値。
RESOLUTION_LINE_LIMIT = 5
# hook の timeout（hooks.json の 10 秒）を超えると、hook は無出力で終わり push を通す。
# 呼び出し側は hook の起動からの残り時間を `<残り秒>` で渡す。その残りとこの上限の
# 小さい方で、引き継がない側で終える。
TIME_BUDGET_SECONDS = 5.0
_MARKER_RE = re.compile(rb"^(?:<{7,}|>{7,}|\|{7,})", re.M)
# 衝突ブロックの位置で両側のどちらでもない行に残った、区切りを含む衝突マーカーの行
_EXTRA_MARKER_RE = re.compile(rb"^(?:<{7,}|={7,}|>{7,}|\|{7,})(?:[ \t]|\r?\n|$)")
_DIFF_ARGS = (
    "diff", "-U0", "--no-color", "--no-ext-diff", "--no-textconv",
    "--no-renames", "--binary", "--full-index",
)


class NotCarried(Exception):
    pass


class _Git:
    def __init__(self, repo: str, budget: float) -> None:
        self.repo = repo
        self.deadline = time.monotonic() + min(TIME_BUDGET_SECONDS, budget)

    def check_time(self) -> None:
        if time.monotonic() >= self.deadline:
            raise NotCarried("時間内に確かめられない")

    def run(self, *args: str, ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[bytes]:
        self.check_time()
        remaining = self.deadline - time.monotonic()
        try:
            result = subprocess.run(
                # 衝突マーカーは 2 方向（<<<<<<< / ======= / >>>>>>>）に固定する（diff3・zdiff3 の
                # ||||||| の節を読まない）
                ["git", "-C", self.repo, "-c", "core.quotePath=true",
                 "-c", "merge.conflictStyle=merge", *args],
                capture_output=True, timeout=remaining, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise NotCarried("時間内に確かめられない") from exc
        if result.returncode not in ok:
            raise NotCarried(f"git {args[0]} が失敗した")
        return result

    def text(self, *args: str) -> str:
        return self.run(*args).stdout.decode("utf-8", "surrogateescape").strip()


def _split_patch(patch: bytes) -> dict[bytes, tuple[list[bytes], list[bytes]]]:
    """`git diff` の出力をファイルごとに分ける。値は (比べる行, 変更行)。

    key は `diff --git` の行（--no-renames なので両側で同じ path を指す）。比べる行からは
    `index` 行と `@@` 行を落とす。変更行は最初の `@@` より後ろの `+`/`-` の行。
    """
    files: dict[bytes, tuple[list[bytes], list[bytes]]] = {}
    current: bytes | None = None
    in_body = False
    for line in patch.split(b"\n"):
        if line.startswith(b"diff --git "):
            # 種類の変更（通常のファイル ↔ symlink）は同じ行の 2 件になる。上書きせず続ける
            current = line
            files.setdefault(current, ([], []))[0].append(line)
            in_body = False
            continue
        if current is None:
            continue
        if line.startswith(b"@@"):
            in_body = True
            continue
        if not in_body and line.startswith(b"index "):
            continue
        files[current][0].append(line)
        if in_body and line[:1] in (b"+", b"-"):
            files[current][1].append(line)
    return files


def verify(repo: str, merge: str, reviewed: str, default_ref: str, budget: float) -> None:
    git = _Git(repo, budget)
    merge = git.text("rev-parse", "--verify", f"{merge}^{{commit}}")
    reviewed = git.text("rev-parse", "--verify", f"{reviewed}^{{commit}}")
    parents = git.text("rev-list", "--parents", "-n", "1", merge).split()[1:]
    if len(parents) != 2:
        raise NotCarried("merge commit ではない（親が 2 つでない）")
    first, second = parents
    if first != reviewed:
        raise NotCarried("第 1 親が Independent Review の sha ではない")
    if git.run("merge-base", "--is-ancestor", second, default_ref, ok=(0, 1)).returncode != 0:
        raise NotCarried("第 2 親が default branch に無い")
    bases = git.text("merge-base", "--all", first, second).split()
    if len(bases) != 1:
        raise NotCarried("merge-base が 1 つに決まらない（criss-cross）")
    base = bases[0]

    tree = git.run(
        "merge-tree", "--write-tree", "--name-only", "--no-messages", "-z", first, second,
        ok=(0, 1),
    ).stdout
    names = tree.split(b"\0")
    auto_tree = names[0].decode("ascii", "replace").strip()
    conflicted = [n.decode("utf-8", "surrogateescape") for n in names[1:] if n]
    if not auto_tree:
        raise NotCarried("自動 merge の tree を得られない")

    # 衝突していないファイルは、git の自動 merge の結果と同じでなければならない
    changed = git.run(
        "diff-tree", "-r", "--name-only", "-z", "--no-renames", auto_tree, merge,
    ).stdout
    outside = {n.decode("utf-8", "surrogateescape") for n in changed.split(b"\0") if n}
    if outside - set(conflicted):
        raise NotCarried("衝突していないファイルが git の自動 merge の結果と違う")

    reviewed_files = _split_patch(git.run(*_DIFF_ARGS, base, first).stdout)
    merged_files = _split_patch(git.run(*_DIFF_ARGS, second, merge).stdout)
    git.check_time()

    resolution = 0
    conflict_headers: set[bytes] = set()
    for path in conflicted:
        merged = _blob(git, merge, path, "衝突したファイルが merge で消えている")
        auto = _blob(git, auto_tree, path, "衝突したファイルの自動 merge の結果が無い")
        if _MARKER_RE.search(merged):
            raise NotCarried("衝突したファイルに衝突マーカーが残っている")
        resolution += _resolution_lines(_conflict_segments(auto), merged.splitlines(keepends=True))
        for old, new in ((base, first), (second, merge)):
            conflict_headers.update(
                _split_patch(git.run(*_DIFF_ARGS, old, new, "--", f":(literal){path}").stdout)
            )
    if resolution > RESOLUTION_LINE_LIMIT:
        raise NotCarried(f"衝突の解消の行数 {resolution} が {RESOLUTION_LINE_LIMIT} を超える")

    for header in set(reviewed_files) | set(merged_files):
        if header in conflict_headers:
            continue
        if reviewed_files.get(header, ([], []))[0] != merged_files.get(header, ([], []))[0]:
            raise NotCarried("衝突していないファイルの差分が PR の差分と一致しない")
    git.check_time()


def _blob(git: _Git, tree: str, path: str, missing: str) -> bytes:
    """`<tree>:<path>` の中身。無ければ missing を理由に、NUL を含めばバイナリとして引き継がない。

    `.gitattributes` の binary・-diff 扱いによらず、中身を行として読む。
    """
    result = git.run("cat-file", "blob", f"{tree}:{path}", ok=(0, 128))
    if result.returncode != 0:
        raise NotCarried(missing)
    if b"\0" in result.stdout:
        raise NotCarried("衝突したファイルがバイナリ")
    return result.stdout


_OPEN = re.compile(rb"^<{7}(?: |\r?\n|$)")
_SEP = re.compile(rb"^={7}\r?\n?$")
_CLOSE = re.compile(rb"^>{7}(?: |\r?\n|$)")


def _conflict_segments(auto: bytes) -> list[tuple[list[bytes], list[bytes], list[bytes]]]:
    """自動 merge の blob を (衝突の前の行の塊, PR 側の行, default branch 側の行) の並びに分ける。

    最後の要素は (末尾の行の塊, [], [])。マーカーの並びが崩れている・`=======` が 1 つの
    ブロックに 1 本でない・ブロックが 1 つも無い（modify/delete などの衝突）ときは引き継がない。
    隣り合うブロック（間の行の塊が空）は、どこで分かれるかを merge 側から決められないので、
    1 つのブロックにまとめる。
    """
    segments: list[tuple[list[bytes], list[bytes], list[bytes]]] = []
    plain: list[bytes] = []
    ours: list[bytes] = []
    theirs: list[bytes] = []
    state = "plain"
    for line in auto.splitlines(keepends=True):
        if state == "plain":
            if _OPEN.match(line):
                state = "ours"
            elif _SEP.match(line) or _CLOSE.match(line) or line.startswith(b"|||||||"):
                raise NotCarried("衝突マーカーの並びを読めない")
            else:
                plain.append(line)
        elif state == "ours":
            if _SEP.match(line):
                state = "theirs"
            elif _OPEN.match(line) or _CLOSE.match(line) or line.startswith(b"|||||||"):
                raise NotCarried("衝突マーカーの並びを読めない")
            else:
                ours.append(line)
        else:
            if _CLOSE.match(line):
                if segments and not plain:
                    _prev_plain, prev_ours, prev_theirs = segments[-1]
                    segments[-1] = (_prev_plain, prev_ours + ours, prev_theirs + theirs)
                else:
                    segments.append((plain, ours, theirs))
                plain, ours, theirs = [], [], []
                state = "plain"
            elif _OPEN.match(line) or _SEP.match(line) or line.startswith(b"|||||||"):
                raise NotCarried("衝突マーカーの並びを読めない")
            else:
                theirs.append(line)
    if state != "plain" or not segments:
        raise NotCarried("衝突マーカーの並びを読めない")
    segments.append((plain, [], []))
    return segments


def _find(lines: list[bytes], chunk: list[bytes], start: int) -> int:
    """lines[start:] で chunk が連続して現れる最初の位置。無ければ -1。"""
    if not chunk:
        return start
    for i in range(start, len(lines) - len(chunk) + 1):
        if lines[i:i + len(chunk)] == chunk:
            return i
    return -1


def _subsequence(region: list[bytes], wanted: list[bytes]) -> set[int] | None:
    """wanted が region の中に順序を保って残る位置（先から貪欲に当てる）。残らなければ None。"""
    hits: set[int] = set()
    pos = 0
    for line in wanted:
        while pos < len(region) and region[pos] != line:
            pos += 1
        if pos == len(region):
            return None
        hits.add(pos)
        pos += 1
    return hits


def _resolution_lines(
    segments: list[tuple[list[bytes], list[bytes], list[bytes]]], merged: list[bytes]
) -> int:
    """merged が「衝突の外の行の塊は自動 merge のとおり、ブロックの中は両側の行を順序どおり含む」
    形かを確かめ、ブロックの中で両側のどちらにも当たらない行の数を返す。

    先頭の塊は merged の先頭、末尾の塊は merged の末尾に固定する。間の塊は前から順に、最初に
    連続で現れる位置に当てる（外れれば、後の塊やブロックの照合が崩れて引き継がない側に倒れる）。
    """
    head = segments[0][0]
    tail = segments[-1][0]
    if merged[:len(head)] != head:
        raise NotCarried("衝突したファイルで、衝突の外の行が自動 merge の結果と違う")
    end = len(merged) - len(tail)
    if end < len(head) or merged[end:] != tail:
        raise NotCarried("衝突したファイルで、衝突の外の行が自動 merge の結果と違う")
    extra = 0
    cursor = len(head)
    for index, (_plain, ours, theirs) in enumerate(segments[:-1]):
        following = segments[index + 1][0]
        if index + 1 == len(segments) - 1:
            stop = end
        else:
            stop = _find(merged[:end], following, cursor)
            if stop < 0:
                raise NotCarried("衝突したファイルで、衝突の外の行が自動 merge の結果と違う")
        region = merged[cursor:stop]
        kept_ours = _subsequence(region, ours)
        kept_theirs = _subsequence(region, theirs)
        if kept_ours is None:
            raise NotCarried("衝突したファイルで PR 側の行が merge に順序どおり残っていない")
        if kept_theirs is None:
            raise NotCarried("衝突したファイルで default branch 側の行が merge に順序どおり残っていない")
        kept = kept_ours | kept_theirs
        for pos, line in enumerate(region):
            if pos not in kept and _EXTRA_MARKER_RE.match(line):
                raise NotCarried("衝突したファイルに衝突マーカーが残っている")
        extra += len(region) - len(kept)
        cursor = stop + len(following)
    return extra


def _expire(_signum, _frame) -> None:
    raise NotCarried("時間内に確かめられない")


def main(argv: list[str]) -> int:
    if len(argv) != 6 or not all(argv[1:]):
        print("引数が足りない")
        return 1
    try:
        budget = float(argv[5])
        if not budget > 0:
            print("時間内に確かめられない")
            return 1
        # git の待ちと Python の計算の両方を、1 つの時計で切る。時計の無い環境（Windows）では引き継がない
        if not (hasattr(signal, "SIGALRM") and hasattr(signal, "setitimer")):
            print("この環境では時間の上限を張れない")
            return 1
        signal.signal(signal.SIGALRM, _expire)
        signal.setitimer(signal.ITIMER_REAL, min(TIME_BUDGET_SECONDS, budget))
        try:
            verify(argv[1], argv[2], argv[3], argv[4], budget)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    except NotCarried as exc:
        print(exc)
        return 1
    except Exception:  # noqa: BLE001 - 判定できないときは引き継がない側に倒す
        print("判定できない")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
