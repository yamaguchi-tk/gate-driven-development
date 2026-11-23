"""hook が出す block reason の復旧要素を **hook 横断** で機械検査するための共有土台。

T-14 で `_hook_block_reason_codes` を機械導出化したが、その導出は
`run-pre-push-gate-hook.sh` 1 本しか読まない形だったため、T-15 が
`run-pre-pr-gate-hook.sh` へ足した 2 code（`missing-evidence` / `dry-not-reached`）は
**どの機械検査にも掛かっていなかった**（T-15 Attempt 1 の M-1: 3 要素のうち記録先・
key 一覧・正本パスを持たない reason が全 suite を素通りした）。

ここが閉じるのは「検査対象の集合をテスト側が列挙している」という構造そのもの:

1. reason code を出す hook を **glob で発見** する（ファイル名も件数も literal で持たない）
2. hook ごとの fixture provider を **登録制** にする
3. 発見された hook に provider が無ければ落とす（fail-closed）

これにより hook が増えても自動的に検査対象へ入る。provider を書く以外に
「検査対象へ追加する」操作は存在しない。
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path
from typing import Callable, NamedTuple

from _paths import PLUGIN_ROOT
TESTS_DIR = Path(__file__).resolve().parent
HOOK_SCRIPT_DIR = PLUGIN_ROOT / "hooks" / "scripts"

_REASON_CODE_RE = re.compile(r"reason code: ([a-z][a-z0-9-]*)")
# design.md § 主要フロー step 11 が要求する「短絡せず全件列挙」の集約 block() は、
# 個々の code を `reason code: <literal>` として直接ソースに書かず、共有配列へ
# `FAILURES+=("<code>")` で積んでから `${FAILURES[0]}` として動的に埋め込む
# （merge gate hook が唯一の採用者）。この形は `_REASON_CODE_RE` では発見できない
# ため、専用の第 2 パターンで拾う。
_FAILURES_APPEND_RE = re.compile(r'FAILURES\+=\("([a-z][a-z0-9-]*)"\)')
# 抽出そのものが壊れて空集合になると assert が空回りするため、実装から消える予定の
# ない 1 本をアンカーにして非空洞であることを固定する（T-14 と同じ規律）。
_ANCHOR_CODE = "missing-evidence"

# design.md § block reason の復旧要素（テスト基盤との接続）: provider には
# 「復旧要素そのもの」ではなく shell 側の正本定数名を返させ、テスト側が
# hooks/scripts/lib/*.sh から literal を抽出して照合する。provider が値そのもの
# を返すと「hook が出した文字列が、hook の作者が宣言した文字列を含むか」という
# 自己参照検査に退化するため。
_RECOVERY_CONSTANT_NAMES = ("GDD_SR_RECOVERY_CORE", "GDD_MG_RECOVERY_CORE", "GDD_IR_RECOVERY_CORE")
_LIB_DIR = PLUGIN_ROOT / "hooks" / "scripts" / "lib"


def _extract_shell_constant(name: str) -> str:
    """`NAME='...'` / `NAME="..."` の **行頭代入だけ** を拾って値を返す。

    行頭アンカーと「`=` 直後のクォート対」を必須にする。bash の代入は `=` の前後に
    空白を置けないので、これが実仕様どおりの受理面であり、同時に次の 2 つの誤ヒットを
    閉じる（緩和ではなく厳格化）:
    (1) 説明コメント中の `# ... NAME= ...` に当たり、直後の 1 文字をクォートと
        誤認して無関係な断片を返す
    (2) `NAME= '値'` のように `=` の直後が空白のとき、空白をクォートと誤認する
    """
    pattern = re.compile(rf"^{re.escape(name)}=(['\"])(.*?)\1", re.MULTILINE)
    for script in sorted(_LIB_DIR.glob("*.sh")):
        matched = pattern.search(script.read_text(encoding="utf-8"))
        if matched:
            return matched.group(2)
    raise AssertionError(f"shell 定数が見つからない: {name}")


def _recovery_elements() -> tuple[str, ...]:
    elements: list[str] = ["<steering-dir>/state.md"]
    for name in _RECOVERY_CONSTANT_NAMES:
        elements.append(_extract_shell_constant(name))
    return tuple(elements)


RECOVERY_ELEMENTS: tuple[str, ...] = _recovery_elements()


class BlockReasonSample(NamedTuple):
    """到達可能な block 1 本分の実測結果。

    `forbidden` には「その reason に出てはならない実測値」（一時 repo の絶対パス・
    steering slug 等）を入れる。否定側検査を fixture 側の実値で行うことで、
    列挙した禁止 token だけを見る形（実パスが変わると素通りする形）にしない。
    """

    code: str
    reason: str
    forbidden: tuple[str, ...]


_PROVIDERS: dict[Path, Callable[[], list[BlockReasonSample]]] = {}


def reason_codes_by_hook() -> dict[Path, frozenset[str]]:
    """`hooks/scripts/*.sh` を全走査し、reason code を出す hook だけを返す。

    走査対象を glob にすることで、新しい hook が reason code を出し始めた瞬間に
    検査対象へ入る。ここに hook 名の literal を書かないことが本モジュールの要点。
    """
    found: dict[Path, frozenset[str]] = {}
    for script in sorted(HOOK_SCRIPT_DIR.glob("*.sh")):
        text = script.read_text(encoding="utf-8")
        codes = frozenset(_REASON_CODE_RE.findall(text)) | frozenset(
            _FAILURES_APPEND_RE.findall(text)
        )
        if codes:
            found[script] = codes
    if not found:
        raise AssertionError(f"reason code を出す hook を 1 本も検出できない: {HOOK_SCRIPT_DIR}")
    if not any(_ANCHOR_CODE in codes for codes in found.values()):
        raise AssertionError(f"reason code の抽出に失敗（anchor 不在）: {found}")
    return found


def register_block_reason_provider(
    hook: Path, provider: Callable[[], list[BlockReasonSample]]
) -> None:
    """hook 1 本ぶんの fixture provider を登録する（各 contract test module が呼ぶ）。"""
    _PROVIDERS[hook.resolve()] = provider


def registered_providers() -> dict[Path, Callable[[], list[BlockReasonSample]]]:
    return dict(_PROVIDERS)


def import_provider_modules() -> None:
    """本モジュールを参照している `tests/test_*.py` を import して登録を集める。

    import する module 名を literal で持たない（持つと「登録されているはずの module」
    という第 2 の正本が生まれ、片方だけ増えるドリフトが再発する）。
    """
    if str(TESTS_DIR) not in sys.path:
        sys.path.insert(0, str(TESTS_DIR))
    marker = Path(__file__).stem
    for test_file in sorted(TESTS_DIR.glob("test_*.py")):
        if marker not in test_file.read_text(encoding="utf-8"):
            continue
        importlib.import_module(test_file.stem)


def missing_recovery_elements(reason: str) -> list[str]:
    """reason に欠けている復旧要素を返す（空リスト = 充足）。

    先頭要素（`<steering-dir>/state.md`）は全 hook 共通で必須。残りは hook ごとに
    異なる正本定数（`GDD_SR_RECOVERY_CORE` / `GDD_MG_RECOVERY_CORE`）の抽出値で、
    reason は **そのうちどれか 1 つ**を含んでいれば足りる。全部を同時に要求すると、
    1 個の正本定数しか埋め込まない hook の reason が構造的に常に「欠落」判定になる
    （self-review 系 hook は `GDD_SR_RECOVERY_CORE` だけ、merge gate hook は
    `GDD_MG_RECOVERY_CORE` だけを埋め込む。design.md が hook 横断で要求するのは
    「復旧要素を持つこと」であって「全 hook 共通の同一文字列」ではない）。
    """
    common, *per_hook_cores = RECOVERY_ELEMENTS
    missing: list[str] = []
    if common not in reason:
        missing.append(common)
    if per_hook_cores and not any(core in reason for core in per_hook_cores):
        missing.extend(per_hook_cores)
    return missing
