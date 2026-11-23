"""`ApplyPatch` の patch 本文を path 単位にスコープ化するヘルパ。

`validate-steering-write.py`（PR #31 レビュー是正、コード健全性の目安である
1500 行を超過したため分離）から
抽出。1 回の `ApplyPatch` は複数ファイルを同時に更新できるため、patch 全体を
1 本の文字列として扱うと「別ファイルへ書いた行」を対象ファイルの変更と誤認する
（PR #31 レビュー Finding P / Q / T）。ここに置く関数群は、削除行・追加行・
ファイル削除・move のいずれも、`_scan()`（Codex の apply_patch と同じ規則の走査）の
結果から作る。関数ごとに走査を持つと、受け取る行の集合が食い違う。`extract_added_lines()`
だけは path を問わない全体の追加行で、`_scan()` を使わない。
"""

from __future__ import annotations


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


# `ApplyPatch` の file section header。**削除も収集対象に含める**（PR #31 レビュー
# Finding P）。Add / Update だけを集めると `*** Delete File: <...>/state.md` が
# steering_targets に入らず、main() が早期 allow して write-once の `Origin Session`
# ごとファイルを消せる。
_PATCH_FILE_HEADERS = ("*** Add File: ", "*** Update File: ", "*** Delete File: ")
_PATCH_DELETE_HEADER = "*** Delete File: "
_PATCH_UPDATE_HEADER = "*** Update File: "
# `*** Update File: <old>` の直後（diff hunk より前）に置かれる rename 指示。
# 認識しないと `*** Move to:` 行が汎用の `*** ` catch-all に落ちて section が
# 閉じ、旧 path の削除にも新 path 宛の書込みにも判定が及ばない（PR #31 レビュー
# Finding Y）。
_PATCH_MOVE_HEADER = "*** Move to: "


def _patch_header_path(line: str, headers: tuple[str, ...] = _PATCH_FILE_HEADERS) -> str | None:
    """patch の file section header 行から対象 path を取り出す（header でなければ None）。"""
    for header in headers:
        if line.startswith(header):
            return line[len(header) :].strip()
    return None


def patch_text_of(tool_name: str, tool_input: object) -> str | None:
    """payload から patch 本文を取り出す（patch 形式でなければ None）。

    `extract_target_paths` / `extract_content_chunks` / path スコープ化系の
    ヘルパが同じ規約で patch を認識するよう、取り出しはここ 1 箇所に置く。
    """
    if isinstance(tool_input, dict):
        if tool_name != "ApplyPatch":
            return None
        patch_text = tool_input.get("patch") or tool_input.get("text")
        return patch_text if isinstance(patch_text, str) else None
    if isinstance(tool_input, str):
        if tool_name == "ApplyPatch" or "*** Begin Patch" in tool_input:
            return tool_input
    return None


_END_PATCH = "*** End Patch"


class _Hunk:
    """`*** Add/Update/Delete File:` の 1 つ。`lines` は header より後ろの行（`+`/`-`/` ` の接頭辞つき）。

    kind が `stray` の hunk は、Update の外に置かれた `*** Move to:` の移動先で、target として
    拾うためだけにある（行も move も持たない）。
    """

    __slots__ = ("kind", "path", "move_paths", "lines")

    def __init__(self, kind: str, path: str) -> None:
        self.kind = kind
        self.path = path
        self.move_paths: list[str] = []
        self.lines: list[str] = []


def _scan(patch_text: str) -> list[_Hunk]:
    """patch を hunk の列にする。規則は Codex の apply_patch（codex-rs/apply-patch/src/streaming_parser.rs）に合わせる。

    - header（Add/Update/Delete File・End Patch）は、Update の hunk の中では行末の空白だけを
      落として判定し、それ以外では前後の空白を落として判定する（Update の中の先頭に空白の
      ある行は context 行）
    - `*** End of File` は hunk を閉じない（後ろの `@@` は同じファイルの次の chunk）
    - `*** End Patch` は hunk を閉じるだけで、走査は続ける（後ろを読む harness がありうるので、
      後ろの header は target として拾う。次の header までの `+` 行はどの hunk にも入らない）
    - `*** Move to:` は Update の hunk の中なら位置を問わず、何本でも移動先として受ける（前に
      置かれた行も移動先に属す）。Update の外のものも target として拾う（`stray`）
    - 行は `\n` だけで割り、行末の `\r` を 1 つ落とす（`str.splitlines()` は `\u2028` などでも
      割るので、header の path が途中で切れて target から漏れる）
    """
    hunks: list[_Hunk] = []
    current: _Hunk | None = None
    for line in patch_text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        probe = line.rstrip() if current is not None and current.kind == "update" else line.strip()
        if probe == _END_PATCH:
            current = None
            continue
        for kind, header in (("add", "*** Add File: "), ("update", _PATCH_UPDATE_HEADER), ("delete", _PATCH_DELETE_HEADER)):
            path = _patch_header_path(probe, (header,))
            if path:
                current = _Hunk(kind, path)
                hunks.append(current)
                break
        else:
            move_path = _patch_header_path(probe, (_PATCH_MOVE_HEADER,))
            if move_path and current is not None and current.kind == "update":
                current.move_paths.append(move_path)
                continue
            if move_path:
                hunks.append(_Hunk("stray", move_path))
            if current is None or current.kind == "delete":
                continue
            current.lines.append(line)
    return hunks


def parse_patch_paths(patch_text: str) -> list[str]:
    """patch が触る全 path（`*** Move to:` の移動先を含む）を返す。

    移動先を含めないと、別ファイルを `state.md` へ move するケースで移動先が
    `steering_targets` に入らず、write-once 検査が一切走らない（PR #31 レビュー
    Finding Y）。
    """
    paths: list[str] = []
    for hunk in _scan(patch_text):
        paths.append(hunk.path)
        paths.extend(hunk.move_paths)
    return paths


def patch_move_destinations(patch_text: str) -> list[str]:
    """`*** Move to:` の移動先（Update の外の `stray` を含む）。移動元はたどらない。"""
    return [path for hunk in _scan(patch_text) for path in (hunk.move_paths or [hunk.path] * (hunk.kind == "stray"))]


def parse_patch_sections(patch_text: str) -> dict[str, list[str]]:
    """patch を file section 単位に分け、`normalize_path` 済み path -> 本文行 を返す。

    move の行は**移動先の section だけ**に積み、移動元の section は消す。移動元に
    それまで積んだ行（同じ path の前の hunk）も移動先へ引き継ぐ。両方に同じ内容を
    紐付けると、move で「値は変わっていない」ように見える diff（旧値を削除し同じ値を
    新 path へ追加）が旧 path 自体の削除として検出できなくなる（Finding Y）。
    """
    sections: dict[str, list[str]] = {}
    for hunk in _scan(patch_text):
        if hunk.kind == "stray":
            continue
        key = normalize_path(hunk.path)
        if hunk.move_paths:
            carried = sections.pop(key, []) + hunk.lines
            for move_path in hunk.move_paths:
                sections.setdefault(normalize_path(move_path), []).extend(carried)
        else:
            sections.setdefault(key, []).extend(hunk.lines)
    return sections


def _patch_section_lines(patch_text: str, path: str, sign: str) -> str:
    """`path` 宛の section から `sign`（`+` / `-`）の行だけを取り出す。

    section の中の `+++` / `---` は unified diff の header ではなく、`++` / `--` で始まる内容
    （Codex の apply_patch は先頭の 1 文字だけを外す）。
    """
    body = parse_patch_sections(patch_text).get(normalize_path(path), [])
    return "\n".join(line[1:] for line in body if line.startswith(sign))


def patch_added_lines(patch_text: str, path: str) -> str:
    return _patch_section_lines(patch_text, path, "+")


def patch_added_lines_by_path(patch_text: str | None) -> list[str]:
    """hunk ごとの追加行。fence のように行をまたぐ状態を持つ検査が、別の hunk の行と対にしないために使う。

    section（move で引き継いだ行を含む）ではなく hunk で分ける。move で引き継いだ前の hunk の
    ``` と対になると、値が fence の中として免除される。
    """
    if patch_text is None:
        return []
    return [
        "\n".join(line[1:] for line in hunk.lines if line.startswith("+"))
        for hunk in _scan(patch_text)
        if hunk.lines
    ]


def patch_added_lines_by_section(patch_text: str | None) -> list[str]:
    """section（ファイル）ごとの追加行。hunk ごとと併せて使い、同じファイルの別の hunk との fence の対も見る。"""
    if patch_text is None:
        return []
    return ["\n".join(line[1:] for line in body if line.startswith("+")) for body in parse_patch_sections(patch_text).values()]


def extract_added_lines(patch_text: str) -> str:
    """patch 全体の追加行（path スコープなし）。

    表現検査（`collect_violations` 等）に渡す全体の chunk。行をまたぐ状態（fence）を持つ
    検査は、別ファイルの行と対にしないよう `patch_added_lines_by_path()` も併せて使う。
    **書込み後の field 値**で判定する security boundary からは使わない
    （`path_scoped_chunks()` を使う）。
    """
    added: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("*** ") or line.startswith("@@") or line.startswith("+++ "):
            continue
        if line.startswith("+"):
            added.append(line[1:])
    return "\n".join(added)


def path_scoped_chunks(
    tool_name: str, tool_input: object, chunks: list[str], path: str
) -> list[str]:
    """`path` 宛の追加文字列だけを返す。

    `Write` / `Edit` / `MultiEdit` は 1 回の呼び出しが単一ファイル宛なので chunk を
    そのまま返す。`ApplyPatch` だけが複数ファイルを 1 度に更新でき、
    `extract_content_chunks()` はその追加行を 1 本に集約するため、そのまま
    security boundary の判定に使うと別ファイルへ書いた行を対象ファイルの新しい値と
    誤認する（PR #31 レビュー Finding T）。
    """
    patch_text = patch_text_of(tool_name, tool_input)
    if patch_text is None:
        return chunks
    added = patch_added_lines(patch_text, path)
    return [added] if added else []


def patch_inflow_sources(patch_text: str, path: str) -> list[str]:
    """`path` へ move で流れ込む移動元を、推移的にたどって生のパスで返す（見つけた順）。

    a → b → `path` のような連鎖も拾う。hunk の順序は見ない（実際より広い集合になる側）。
    返すのは header に書かれたままのパスで、読むときにそのまま使う（`normalize_path()` は比べるためだけ）。
    移動先から移動元への表を 1 回作ってたどるので、1 回の呼び出しの時間は hunk の数に比例する
    （呼び出しは target ごとなので、target が多い patch では全体で hunk の数の 2 乗に比例する）。
    """
    by_dest: dict[str, list[str]] = {}
    for hunk in _scan(patch_text):
        if hunk.kind == "update":
            for dest in hunk.move_paths:
                by_dest.setdefault(normalize_path(dest), []).append(hunk.path)
    reached = {normalize_path(path)}
    queue = [normalize_path(path)]
    seen: set[str] = set()
    sources: list[str] = []
    while queue:
        for raw in by_dest.get(queue.pop(), []):
            if raw in seen:
                continue
            seen.add(raw)
            sources.append(raw)
            key = normalize_path(raw)
            if key not in reached:
                reached.add(key)
                queue.append(key)
    return sources
