"""fence 規約を「手で列挙した形の表」ではなく **生成した文書** で固定する契約テスト。

## なぜこの形が要るか

`state.md` / `tasklist.md` から canonical field を読む規約は、独立実装 3 本
（`detect-steering.sh` の awk / `lib/tasklist_parse.py` / `setup-gdd-loop.sh` の
埋め込み Python）に分かれている。これまでの回帰はすべて「**誰も列挙していない形**」で
起きた（実測）:

- fence のインデントを半角スペースだけに狭め、TAB fence が素通り（A-4 の再発）
- 閉じ忘れ時に本文を丸ごと返し、それ以前の閉じた記入例まで復活
- 開き fence の info string に ` を含む行を fence 扱いし、直後の field を飲む

いずれも既存の契約表（`test_canonical_field_line_anchoring_contract.py`）が
5 実装を拘束していたにもかかわらず通り抜けた。**表に無い形は検査されない**からで、
形を足し続ける限りこの失敗モードは消えない。

そこで本 module は形を列挙せず、fence の構成要素（記号種別・長さ・インデント・
info string・閉じる / 閉じない）から文書を**組み立てる**。組み立て側は
「payload 行を閉じた fence の中に置いたか否か」を**構成として知っている**ので、
実装を参照しない独立した正解を持つ。実装間の差分テストと違い、
**3 実装が揃って間違っている場合も落ちる**。

## 何を固定するか

1. 閉じた fence の中（区切り行を含む）に置いた canonical field は読まれない
2. fence の外、および**閉じ忘れ** fence の中に置いた canonical field は読まれる
   （閉じ忘れで以降を全部落とすと canonical field が 1 つも見えなくなるため、
   救済は「未閉鎖の開き fence 以降を残す」。正本は `strip_fenced_blocks`）
3. backtick fence の info string に ` を含む行は fence ではない（CommonMark）
4. 上記を独立実装 3 本すべてが同じ結論で満たす
"""
from __future__ import annotations

import random
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

# 読んだ直後に path を戻す。`hooks/scripts/lib` を常設すると、同一プロセスの
# 他 module の解決順を変える（この repo が実測付きで禁じている形）。
_LIB_DIR = str(PLUGIN_ROOT / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from tasklist_parse import strip_fenced_blocks  # noqa: E402
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)

DETECT_STEERING_LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
LOOP_SCRIPT = PLUGIN_ROOT / "scripts" / "setup-gdd-loop.sh"
TASKLIST_PARSE = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "tasklist_parse.py"

BACKTICK = chr(96)

#: payload は全実装が受理する形だけを使う（受理形の差は本 module の対象外）。
PAYLOAD = "- Next Action: done"
PAYLOAD_VALUE = "done"

#: fence の構成要素。回帰が起きた次元をすべて含む。
FENCE_CHARS = (BACKTICK, "~")
FENCE_LENGTHS = (3, 4, 5)
FENCE_INDENTS = ("", " ", "  ", "   ", "\t", " \t")
#: fence として成立する info string。
FENCE_INFOS = ("", "markdown", "json", "  ")
#: backtick fence を**無効化する** info string（` を含む）。`~~~` では無効化しない。
#: 先頭に ` を置くと marker の貪欲マッチに吸われて「1 つ長い fence」になるだけなので、
#: 必ず非 ` 文字で始める（生成器自身の罠。実測で踏んだ）。
NON_FENCE_INFOS = (
    " " + BACKTICK + "x" + BACKTICK,
    "で" + BACKTICK + "囲む" + BACKTICK,
    " use " + BACKTICK + " here",
)
#: fence にも canonical field にもならない行。
FILLER_LINES = ("prose", "# heading", "- some bullet", "", "  indented note")


def _opener(char: str, length: int, indent: str, info: str) -> str:
    return f"{indent}{char * length}{info}"


def _closer(char: str, length: int, indent: str) -> str:
    # 閉じ条件: 同じ記号・同じ長さ以上・情報文字列なし。
    return f"{indent}{char * length}"


class _Doc:
    """組み立てた文書と、payload が読まれるべきかどうかの正解を持つ。"""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.payload_visible: bool | None = None

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"


def _build_document(rng: random.Random) -> _Doc:
    """fence の構成要素から文書を組み立てる。正解は**構成として**決まる。

    payload 行はちょうど 1 つだけ置く（`Next Action` を含む他の行は置かない）。
    """
    doc = _Doc()
    # payload をどの構造に入れるか。正解はここで決まる。
    placement = rng.choice(
        ["outside", "closed_fence", "unclosed_fence", "after_non_fence_opener"]
    )
    doc.payload_visible = placement != "closed_fence"

    def emit_filler() -> None:
        for _ in range(rng.randint(0, 2)):
            doc.lines.append(rng.choice(FILLER_LINES))

    def emit_closed_fence(inner: list[str]) -> None:
        char = rng.choice(FENCE_CHARS)
        length = rng.choice(FENCE_LENGTHS)
        indent = rng.choice(FENCE_INDENTS)
        info = rng.choice(FENCE_INFOS)
        doc.lines.append(_opener(char, length, indent, info))
        doc.lines.extend(inner)
        # 閉じ側は「同種・同長以上・info なし」。長さは開き以上から選ぶ。
        doc.lines.append(
            _closer(char, rng.choice([n for n in FENCE_LENGTHS if n >= length]),
                    rng.choice(FENCE_INDENTS))
        )

    # 前置きとして、payload と無関係な閉じた fence を混ぜる（閉じ忘れ救済が
    # 「それ以前の閉じた fence まで復活させない」ことを踏むため）。
    emit_filler()
    if rng.random() < 0.5:
        emit_closed_fence([rng.choice(FILLER_LINES) or "sample"])
    emit_filler()

    if placement == "outside":
        doc.lines.append(PAYLOAD)
    elif placement == "closed_fence":
        emit_closed_fence([PAYLOAD])
    elif placement == "unclosed_fence":
        char = rng.choice(FENCE_CHARS)
        doc.lines.append(
            _opener(char, rng.choice(FENCE_LENGTHS), rng.choice(FENCE_INDENTS),
                    rng.choice(FENCE_INFOS))
        )
        doc.lines.append(PAYLOAD)
        # 閉じない。以降に閉じ記号を出さない。
        return doc
    else:  # after_non_fence_opener
        # backtick fence の info に ` を含む行は fence ではないので、
        # 直後の payload は読まれる。`~~~` はこの規約の対象外なので使わない。
        doc.lines.append(
            _opener(BACKTICK, rng.choice(FENCE_LENGTHS), rng.choice(FENCE_INDENTS),
                    rng.choice(NON_FENCE_INFOS))
        )
        doc.lines.append(PAYLOAD)

    emit_filler()
    if rng.random() < 0.4:
        emit_closed_fence(["trailing sample"])
    return doc


def _visible_via_canonical(text: str) -> bool:
    return any(line == PAYLOAD for line in strip_fenced_blocks(text).splitlines())


def _load_loop_strip_fenced_blocks():
    """`setup-gdd-loop.sh` の heredoc から `strip_fenced_blocks` だけを取り出す。"""
    source = LOOP_SCRIPT.read_text(encoding="utf-8")
    blocks = []
    backtick_def = re.search(r"^BACKTICK = .*$", source, re.MULTILINE)
    if backtick_def is None:
        raise AssertionError(f"BACKTICK definition not found in {LOOP_SCRIPT}")
    blocks.append(backtick_def.group(0))
    match = re.search(
        r"^def strip_fenced_blocks\(.*?(?=^def |\n^[a-zA-Z@#])",
        source, re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"strip_fenced_blocks not found in {LOOP_SCRIPT}")
    blocks.append(match.group(0))
    namespace: dict = {}
    exec("\n".join(blocks), namespace)  # noqa: S102 - shipped source を直接検証するため
    return namespace["strip_fenced_blocks"]


class GeneratedDocumentsMatchTheFencePolicyTests(unittest.TestCase):
    """組み立てた正解に対し、Python 側 2 実装が一致すること。"""

    #: 固定 seed。失敗時に同じ文書を再現できるようにする。
    SEED = 20260903
    CASES = 3000

    def test_canonical_implementation_matches_construction(self) -> None:
        rng = random.Random(self.SEED)
        for i in range(self.CASES):
            doc = _build_document(rng)
            with self.subTest(case=i, text=doc.text()):
                self.assertEqual(_visible_via_canonical(doc.text()), doc.payload_visible)

    def test_loop_script_implementation_matches_construction(self) -> None:
        # class 属性に関数を置くと束縛メソッド化して self が渡るため、局所で持つ。
        loop_strip = _load_loop_strip_fenced_blocks()
        rng = random.Random(self.SEED + 1)
        for i in range(self.CASES):
            doc = _build_document(rng)
            visible = any(
                line == PAYLOAD for line in loop_strip(doc.text()).splitlines()
            )
            with self.subTest(case=i, text=doc.text()):
                self.assertEqual(visible, doc.payload_visible)

    def test_the_generator_reaches_every_placement(self) -> None:
        """生成器が全分岐を踏むこと（踏まない分岐は検査していないのと同じ）。"""
        rng = random.Random(self.SEED)
        seen = {"visible": 0, "hidden": 0}
        markers = {"tab_indent": 0, "tilde": 0, "long_fence": 0, "non_fence_info": 0}
        for _ in range(self.CASES):
            doc = _build_document(rng)
            seen["visible" if doc.payload_visible else "hidden"] += 1
            text = doc.text()
            if "\t" in text:
                markers["tab_indent"] += 1
            if "~~~" in text:
                markers["tilde"] += 1
            if BACKTICK * 4 in text:
                markers["long_fence"] += 1
            if any(info in text for info in NON_FENCE_INFOS):
                markers["non_fence_info"] += 1
        for key, count in {**seen, **markers}.items():
            with self.subTest(kind=key):
                self.assertGreater(count, 0, f"{key} を 1 度も生成していない")


class AwkImplementationMatchesTheFencePolicyTests(unittest.TestCase):
    """awk 実装（merge gate が証跡を読む唯一の経路）も同じ正解を満たすこと。

    1 ケースごとに bash を起動するので件数は絞る。判別力は Python 側と同じ
    生成器から取るので、次元の網羅は落ちない。
    """

    SEED = 20260904
    CASES = 200

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _read(self, text: str) -> str:
        target = self.tmp / "doc.md"
        target.write_text(text, encoding="utf-8")
        proc = subprocess.run(
            ["bash", "-c",
             f'source "{DETECT_STEERING_LIB}"; gdd_extract_doc_field "{target}" "Next Action"'],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(f"gdd_extract_doc_field 失敗: {proc.stderr}")
        return proc.stdout.strip()

    def test_awk_matches_construction(self) -> None:
        rng = random.Random(self.SEED)
        for i in range(self.CASES):
            doc = _build_document(rng)
            expected = PAYLOAD_VALUE if doc.payload_visible else ""
            with self.subTest(case=i, text=doc.text()):
                self.assertEqual(self._read(doc.text()), expected)


class FenceVisibilityHasASingleSourceTests(unittest.TestCase):
    """「何が見えるか」を決めるのは `strip_fenced_blocks` だけであること。

    実測した退行: `select_route_in_progress()` が `strip_fenced_lines()` の
    第 2 戻り値から**自前で**可視性を決めており、閉じ忘れ救済の変更から取り残されて
    いた（正しく閉じた記入例が現在値に化け、done guard が素通りした）。
    可視性の決定が 2 箇所に増えたらここで落ちる。

    `strip_fenced_lines()` 自体は tasklist の task 行を数える経路が
    `(lines, unclosed)` の 2 値を必要とするため残すが、**呼び出してよい場所を
    許可制**にして、可視性の再導出が increment しないようにする。
    """

    #: `strip_fenced_lines()` を呼んでよい場所（file 名 → 理由）。
    #: 増やすときは「なぜ `strip_fenced_blocks` では足りないか」を書くこと。
    ALLOWED_STRIP_FENCED_LINES_CALLERS = {
        # tasklist の未完了 task を数える経路。閉じ忘れを fail-closed の材料に
        # 使うため、可視行だけでなく `unclosed` そのものが要る。
        "gdd_stop_hook.py",
        # done guard の Check 1 の組み立て（`tasklist_structure`）。gdd_stop_hook.py から
        # 切り出し、completion-check の機械検査と共有する。理由は gdd_stop_hook.py と同じ。
        "tasklist_structure.py",
        # 正本自身（`strip_fenced_blocks` が内部で使う）。
        "tasklist_parse.py",
        # done guard の drift 計測。hook 本体と**同じ**可視性判定を通さないと
        # 閉じ忘れ fence の扱いが変わり、CHANGELOG に載せる実測値が hook の
        # 実挙動とずれる（実測で差が出た）。可視性を自前で決めているのではなく、
        # 測定対象と同一の経路を使うための例外。
        "measure-done-guard-drift.py",
    }

    SCAN_DIRS = ("hooks", "scripts")

    def _sources(self):
        for directory in self.SCAN_DIRS:
            for path in sorted((PLUGIN_ROOT / directory).rglob("*")):
                if path.is_file() and path.suffix in (".py", ".sh"):
                    yield path

    #: `strip_fenced_lines()` / `strip_fenced_lines_marked()` のどちらの呼び出しも
    #: 拾う。新 API 名 `strip_fenced_lines_marked(` は `strip_fenced_lines(` の
    #: 部分文字列に一致しない（`lines` の直後が `_marked(` で `(` ではないため）ので、
    #: 単一パターンのままだと新 API が単一正本の走査対象から漏れる（design.md D4）。
    _STRIP_FENCED_LINES_CALL_RE = re.compile(
        r"strip_fenced_lines\(|strip_fenced_lines_marked\("
    )

    def test_only_allowed_callers_use_the_two_value_api(self) -> None:
        offenders = []
        for path in self._sources():
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if not self._STRIP_FENCED_LINES_CALL_RE.search(line):
                    continue
                if line.lstrip().startswith("#"):
                    continue
                if path.name in self.ALLOWED_STRIP_FENCED_LINES_CALLERS:
                    continue
                offenders.append(f"{path.relative_to(PLUGIN_ROOT)}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders, [],
            "可視性を `strip_fenced_lines` / `strip_fenced_lines_marked` から自前で"
            "決めている箇所がある。`strip_fenced_blocks` を使うか、理由を添えて"
            "allow-list に足すこと",
        )

    def test_select_route_in_progress_routes_through_the_single_source(self) -> None:
        """正本経由であることを、振る舞いで固定する（実測した退行の再発防止）。

        「正しく閉じた記入例」＋「後続の閉じ忘れ」で、記入例が現在値に化けない。
        """
        from tasklist_parse import select_route_in_progress

        state = "\n".join([
            "- Route In Progress: systematic_debugging | reason: r | updated_by: u",
            BACKTICK * 3,
            "- Route In Progress: none | reason: 記入例 | updated_by: human",
            BACKTICK * 3,
            BACKTICK * 3,
            "閉じ忘れ",
        ])
        self.assertEqual(select_route_in_progress(state), "systematic_debugging")

    def test_the_allow_list_is_not_stale(self) -> None:
        """allow-list に載っているのに実際は呼んでいない file を残さない。"""
        actual = set()
        for path in self._sources():
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if self._STRIP_FENCED_LINES_CALL_RE.search(line) and not line.lstrip().startswith("#"):
                    actual.add(path.name)
        self.assertEqual(
            self.ALLOWED_STRIP_FENCED_LINES_CALLERS - actual, set(),
            "allow-list に、実際には呼んでいない file が残っている",
        )


if __name__ == "__main__":
    unittest.main()
