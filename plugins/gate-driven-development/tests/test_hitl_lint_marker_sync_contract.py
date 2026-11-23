"""Cross-cutting contract tests for HITL lint marker synchronization.

導入時のタスクの完了条件,
AC-V-1 / AC-V-2 / AC-V-3 をそれぞれ独立した test 関数で検査する（task-breakdown
T-2〜T-20 で逐次追加）。

モジュールの読み込みは `sys.path` 経由ではなく明示パスで行う。この plugin には
`scripts/lib/` と `hooks/scripts/lib/` の 2 つの `lib` パッケージがあり、
`tests/_stop_hook_test_base.py` が先に `hooks/scripts` を `sys.path` へ入れて
`lib` を import するため、後から `scripts` を差し込んでも `sys.modules["lib"]`
は hooks 側のまま解決される。単体実行では通り full suite では落ちる、という
silent failure になるので load_plugin_module() で file location から直接読む。

ただし load_plugin_module() が使えるのは、import 時に `from lib.X import ...` を
実行しないモジュールだけ。`scripts/lint-*.py` の多くは `lib.lint_base` に依存する
ため in-process では読めず、subprocess 実行か ast 走査で検査する。適用範囲の正本は
worklog.md の T-2 実装記録「tests から scripts 配下を読む方式の判断基準」。
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import PLUGIN_ROOT, load_plugin_module  # noqa: E402


def _resolve_constant_expr(node: ast.expr, known: dict[str, object]) -> object:
    """`ast.literal_eval` が扱えない、既知定数への `ast.Name` 参照だけを解決する。

    `ALLOWED_FIELD_VALUES = (FIELD_VALUE_NONE, FIELD_VALUE_FILLED)` のように
    他の定数名を要素に持つタプル/リストは、要素が全てリテラルではないため
    `ast.literal_eval` が `ValueError` を送出し、`load_lint_constants` の
    旧実装ではこの定数自体が読めなかった（PR後-6 実測: 値語彙の同期テストが
    `FIELD_VALUE_NONE`/`FIELD_VALUE_FILLED` だけを見ており、実際に判定が
    参照する `ALLOWED_FIELD_VALUES` タプル自体に第三の値を直接追加する
    widening は検出できなかった）。定義順に処理される `known`（それまでに
    解決済みの定数）だけを使って `ast.Name` を解決することで、この種の
    「他の定数を並べただけ」の集約定数も読めるようにする。
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in known:
            return known[node.id]
        raise ValueError(f"unresolved name: {node.id}")
    if isinstance(node, (ast.Tuple, ast.List)):
        values = [_resolve_constant_expr(elt, known) for elt in node.elts]
        return tuple(values) if isinstance(node, ast.Tuple) else values
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def load_lint_constants(script_name: str) -> dict[str, object]:
    """scripts/<script_name>.py のモジュール級リテラル定数を ast で読む。

    lint-*.py は import 時に `from lib.lint_base import ...` を実行するため
    in-process import できない（正本: worklog.md § T-2 実装記録の判断基準）。

    `ast.Assign`（`NAME = ...`）と `ast.AnnAssign`（`NAME: <型注釈> = ...`）
    の両方を対象にする。型注釈付き定数（例:
    `FIELD_SECTIONS: tuple[tuple[str, str], ...] = (...)`）だけを対象外に
    すると、その定数を検査するテストが `KeyError` で気付かれずに失敗する
    のではなく、呼び出し側が `.get()` 等で握りつぶした場合に**定数が
    存在しないまま黙って検査を素通りする**経路になりうる（PR後-4 実測:
    `FIELD_SECTIONS` は型注釈付きのため旧実装では読めていなかった）。

    `ast.literal_eval` が失敗した場合は `_resolve_constant_expr` で
    他の既知定数への参照だけを解決するフォールバックを試す（PR後-6対応）。
    """
    source = (PLUGIN_ROOT / "scripts" / f"{script_name}.py").read_text(encoding="utf-8")
    constants: dict[str, object] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                continue
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
            if value is None:
                continue
        else:
            continue
        if not isinstance(target, ast.Name):
            continue
        try:
            constants[target.id] = ast.literal_eval(value)
            continue
        except (ValueError, TypeError, SyntaxError):
            pass
        try:
            constants[target.id] = _resolve_constant_expr(value, constants)
        except (ValueError, TypeError):
            continue
    return constants


# 導入時の完了条件が宣言した検証手段。`test_hitl_budget_is_single_source` は Python 側の定数しか
# 見ないため、テンプレート本文へ旧値を書き戻しても全 test / 全 check が緑のまま通る
# （行数を変えない書き戻しで、全 test と validate が通ることを確かめた）。
# 「数値の正本は hitl_budget.py だけ」を成立させるには、テンプレート側に数値が
# 残っていないことを本文から検査する必要がある。
BUDGET_TEMPLATES = (
    "references/human-check-template.md",
    "references/human-check-template-compact.md",
)
BUDGET_POINTER = "scripts/lib/hitl_budget.py"
# 検査対象の数値は `hitl_budget.py` から機械導出する（ハードコードすると値変更に
# 追従できない）。加えて、過去に stale だった 30 / 140 を歴史的値として足す。
# `承認サマリ` の「5 行以内」は hitl_budget の管理対象ではないので集合に入らない。
STALE_BUDGET_NUMBERS = (30, 140)


def _forbidden_budget_pattern() -> "re.Pattern[str]":
    """`45 行` と `45行` の両方を捕まえる。空白の有無で検査をすり抜けさせない。"""
    hitl_budget = load_plugin_module("scripts/lib/hitl_budget.py")
    numbers = sorted(
        set(hitl_budget.PRIMARY_SURFACE_MAX_LINES.values())
        | {hitl_budget.HITL_SAMPLE_MAX_LINES}
        | set(STALE_BUDGET_NUMBERS)
    )
    return re.compile(r"(?:" + "|".join(str(n) for n in numbers) + r")\s*行")


def test_decision_section_markers_follow_the_any_of_groups() -> None:
    """空欄検査の綴り集合が、必須マーカー / any-of 群と同期している。

    `DECISION_SECTION_MARKERS` は「欄はあるが中身が空」を見る検査で、
    `lint-hitl-decision-quality.py` の中でしか使われない（消費者は lint 本体のみ）。
    そのため flat な必須語を any-of 群へ移したとき、空欄検査側への追従が漏れても
    全 test と全 check が緑のまま通る（実測: `この OK で許可すること` を空欄検査から
    外すと、full 正本どおりに書いた HITL は承認範囲欄が空でも rc=0 になるが、
    全 test が通った）。事例ではなく型を固定する。
    """
    consts = load_lint_constants("lint-hitl-decision-quality")
    groups = consts["REQUIRED_DECISION_MARKER_GROUPS"]
    flat = set(consts["REQUIRED_DECISION_MARKERS"])
    grouped = {value for group in groups for value in group}
    section = set(consts["DECISION_SECTION_MARKERS"])

    orphan = section - (flat | grouped)
    assert not orphan, (
        "DECISION_SECTION_MARKERS の語が REQUIRED_DECISION_MARKERS にも "
        f"REQUIRED_DECISION_MARKER_GROUPS にも無い -> {sorted(orphan)}。"
        "リテラル再掲すると片方だけ改名したとき検査が黙って無効化される"
    )

    for group in groups:
        covered = [value for value in group if value in section]
        if not covered:
            continue
        missing = [value for value in group if value not in section]
        assert not missing, (
            f"any-of 群 {group} のうち {covered} だけが空欄検査に入っていて "
            f"{missing} が漏れている。どちらの綴りで書いても同じ検査が効くこと"
        )


def test_primary_surface_budget_numbers_live_only_in_hitl_budget() -> None:
    """テンプレート本文に一次表示バジェットの裸の数値が残っていない。

    数値を 2 箇所に置くと、片方だけ動かしたときに検査が黙って無効化される。
    テンプレートは `hitl_budget.py` へのポインタだけを持つこと。
    """
    for rel in BUDGET_TEMPLATES:
        text = (PLUGIN_ROOT / rel).read_text(encoding="utf-8")
        assert BUDGET_POINTER in text, (
            f"{rel}: 一次表示バジェットの正本ポインタ（{BUDGET_POINTER}）が無い"
        )
        found = sorted(set(_forbidden_budget_pattern().findall(text)))
        assert not found, (
            f"{rel}: 一次表示バジェットの数値が本文に再掲されている -> {found}。"
            f"数値は {BUDGET_POINTER} にのみ置き、テンプレートはポインタだけを書くこと"
        )


def test_complexity_default_uses_budget_and_overbudget_fixture_fails() -> None:
    hitl_budget = load_plugin_module("scripts/lib/hitl_budget.py")
    script = PLUGIN_ROOT / "scripts" / "lint-hitl-complexity.py"
    fixtures = PLUGIN_ROOT / "tests" / "fixtures" / "hitl"

    # --max-lines を渡さずに実行し、配線された既定値が budget と一致することを確認する
    proc_over = subprocess.run(
        [sys.executable, str(script), str(fixtures / "over-budget-default.md")],
        capture_output=True, text=True,
    )
    assert proc_over.returncode == 1, proc_over.stdout + proc_over.stderr
    assert (
        f"HITL行数 exceeds budget: 61 > {hitl_budget.HITL_SAMPLE_MAX_LINES}"
        in proc_over.stdout
    )

    proc_at = subprocess.run(
        [sys.executable, str(script), str(fixtures / "at-budget-60.md")],
        capture_output=True, text=True,
    )
    assert proc_at.returncode == 0, proc_at.stdout + proc_at.stderr


def test_display_integrity_markers_exist_in_canonical_sources() -> None:
    """marker が正本テンプレートに実在することを blocking check として固定する。

    check スクリプトの OK fixture は heredoc で手書きされるため、正本にまだ無い語を
    先取りして書くと lint も check も通ってしまい、「正本どおりに書いた HITL が lint に
    落ちる」状態がどの blocking check にも映らない（impl-gate #1 F-2）。この test は
    fixture を経由せず正本ファイルそのものを読むので、その silent failure を塞ぐ。
    """
    consts = load_lint_constants("lint-hitl-display-integrity")
    sources = {
        src: (PLUGIN_ROOT / src).read_text(encoding="utf-8")
        for src in consts["CANONICAL_SOURCES"]
    }
    for src, text in sources.items():
        assert text, f"canonical source is empty or missing: {src}"

    markers = list(consts["REQUIRED_MARKERS"])
    for group in consts["REQUIRED_MARKER_GROUPS"]:
        markers.extend(group)
    for marker in markers:
        assert any(marker in text for text in sources.values()), (
            f"marker not present in any CANONICAL_SOURCES: {marker!r}. "
            "正本テンプレートへ先に追加するか、marker の owner task へ移すこと"
        )


MARKER_CONST_RE = re.compile(r"^(REQUIRED|FINAL_HITL_REQUIRED)_.*(MARKERS|PHRASES)$")
# any-of 群（compact と full で綴りが違う表示要素）。flat な marker 定数と違い
# 名前が `_GROUPS` で終わるため MARKER_CONST_RE には一致しない。群化した語が
# 「正本に実在するか」の検査から丸ごと漏れると、flat から群へ移すだけで保護が
# 消えるので、ここで明示的に拾って同じ検査へ流す。
MARKER_GROUP_CONST_RE = re.compile(r"^(REQUIRED|FINAL_HITL_REQUIRED)_.*_GROUPS$")


def _read_canonical_source(rel_path: str) -> str:
    """`CANONICAL_SOURCES` が宣言したパスを、宣言どおりに解決して読む。

    旧実装は basename をキーにした dict を引いていたため、(a) `skills/` /
    `commands/` を宣言しても `Path(src).name` が `SKILL.md` / `gdd-dev.md` になって
    キーに一致せず、正本を空文字として扱っていた（実測: 事前に読み込んでいた
    2 本はどちらも参照されない死んだ入力だった）。さらに (b) `SKILL.md` は
    skill ごとに存在する basename なので、将来 `skills/*/SKILL.md` を宣言すると
    別の skill の本文と衝突して**別ファイルを正本として読む** silent failure に
    なりうる。宣言されたパスをそのまま解決すれば、どちらの経路も消える。
    """
    path = PLUGIN_ROOT / rel_path
    assert path.is_file(), (
        f"CANONICAL_SOURCES が宣言したファイルが実在しない: {rel_path}。"
        "宣言はプラグインルートからの相対パスで書くこと"
    )
    return path.read_text(encoding="utf-8")


def test_bidirectional_marker_sync() -> None:
    canonical_compact = _read_canonical_source("references/human-check-template-compact.md")

    checked = 0
    hitl_markers: set[str] = set()  # 方向B で再利用する（HITL 系 3 lint のマーカー集合）
    # T-5 時点の確定版は 3 本。`lint-clarification-brief` は CANONICAL_SOURCES を
    # T-14 で宣言するため、T-14 側の 2 行差分として後から足す（Step 4 の注記）。
    for script_name in (
        "lint-hitl-display-integrity",
        "lint-hitl-decision-quality",
        "lint-human-check-language",
    ):
        consts = load_lint_constants(script_name)
        assert "CANONICAL_SOURCES" in consts, f"{script_name} missing CANONICAL_SOURCES"
        # 宣言の妥当性は marker 照合より前に全件確認する。照合側は any() で短絡するため、
        # 先頭の正本が一致すると後続の宣言（改名・typo で実在しなくなったもの）が
        # 一度も評価されず、壊れた宣言が緑のまま通る。
        canonical_texts = [
            _read_canonical_source(src) for src in consts["CANONICAL_SOURCES"]
        ]
        assert canonical_texts, f"{script_name}: CANONICAL_SOURCES が空"
        markers = {k: v for k, v in consts.items() if MARKER_CONST_RE.match(k)}
        assert markers, f"{script_name} has no REQUIRED_*_MARKERS/PHRASES tuple"
        # any-of 群は「群のどれか 1 語があれば OK」だが、`正本に実在するか` は
        # 群の全要素に対して個別に成り立つべき（実在しない語を群に混ぜても
        # 他の語が拾ってしまい黙って無効化されるため）。flat 側と同じ扱いにする。
        for group_var, groups in consts.items():
            if not MARKER_GROUP_CONST_RE.match(group_var):
                continue
            markers[group_var] = tuple(value for group in groups for value in group)
        for var_name, values in markers.items():
            for value in values:
                found_in_any = any(value in text for text in canonical_texts)
                assert found_in_any, f"{script_name}.{var_name} marker not in canonical source: {value!r}"
                checked += 1
            hitl_markers.update(values)
    assert checked > 0

    # 方向B: compact Template fence 内の表示要素見出しが、いずれかのマーカーに被覆されているか。
    # 事故は「正本にある表示要素を lint が守っていない」という逆方向で起きたため片側検査では防げない。
    for group in load_lint_constants("lint-hitl-display-integrity").get(
        "REQUIRED_MARKER_GROUPS", ()
    ):
        hitl_markers.update(group)
    fences = re.findall(r"```markdown\n(.*?)```", canonical_compact, flags=re.S)
    assert fences, "compact template fence not found"
    headings = [
        line.strip()
        for fence in fences
        for line in fence.splitlines()
        # container 見出し `## 確認` は表示要素ではなく、旧 `## 🔍 確認` は導入時の台帳で
        # 削除として手続き済み（代替検査は配下の `REQUIRED_MARKERS`）。必須に戻すと台帳と矛盾する。
        if line.strip().startswith("### ")
    ]
    conditional = ("選択肢の説明", "アーキテクチャ選択", "Multiple PR Strategy Options")
    targets = [h for h in headings if not any(w in h for w in conditional)]
    # 非 vacuous 下限（実測由来 / 2026-11-12: 一次表示を判断ポイントと OK の範囲だけにした後の
    # `### ` 見出し 7 件 − 条件付き 3 件 = 4 件）。抽出が壊れて 0 件になった場合に、ループが空回りして
    # pass するのを防ぐ。
    assert len(targets) >= 4, f"direction B extracted too few headings: {targets}"
    for heading in targets:
        assert any(marker in heading for marker in hitl_markers), (
            f"compact heading not covered by any lint marker: {heading!r}"
        )


# `<gdd-hitl-fields ...>` タグの「書く側」コピーは compact（fenced Template、著者が
# 実際に Read+埋める一次表示）と full（§ 必須ルール1、個別ルールの正本）の2箇所に
# ある（独立-7 実測: 値語彙同期テストが compact 側しか読まないため、
# `references/human-check-template.md:415` のタグだけを `na|done` 等に差し替えても
# 全量 test・validate-plugin.sh とも緑のまま通っていた）。両方を検査対象にする。
HITL_FIELDS_TAG_SOURCES = (
    "references/human-check-template-compact.md",
    "references/human-check-template.md",
)


# guard（`hooks/scripts/lib/request_diff_field.py` の `TAG_ATTR`）が読む属性。lint の `FIELD_SECTIONS` には
# 入らないので、属性名と値語彙の同期の検査からは、この属性だけを外す（同期は guard のテストが見る）。
_GUARD_ATTR = load_plugin_module("hooks/scripts/lib/request_diff_field.py").TAG_ATTR


def _extract_hitl_fields_tag(text: str, source: str) -> str:
    """`source`（`HITL_FIELDS_TAG_SOURCES` の相対パス）内の最初の `<gdd-hitl-fields ...>`
    を返す（独立-8 Low: 失敗メッセージがどのソースで見つからなかったかを言わないと、
    compact/full 2ソースを検査する現在の呼び出し側では原因の切り分けができない）。
    """
    match = re.search(r'<gdd-hitl-fields\s+((?:[^>"]|"[^"]*")*)>', text)
    assert match, f"{source}: <gdd-hitl-fields ...> タグが見つからない"
    body = match.group(1)
    assert f'{_GUARD_ATTR}="' in body, f"{source}: タグに {_GUARD_ATTR} が無い"
    return re.sub(rf'\s*{_GUARD_ATTR}="[^"]*"', "", body)


def test_hitl_required_fields_attrs_match_compact_template_tag() -> None:
    """`lint-hitl-required-fields.py` の `FIELD_SECTIONS` 属性名が、
    compact/full 両テンプレートの `<gdd-hitl-fields ...>` タグの属性名と
    一致することを検査する（PR後-4 Medium: 属性名1個のリネームが43本の
    suite を生き残っていた。書く側と読む側がずれると、その軸だけ常時 warn
    になるが、warn-only のためどの既存 test/check にも映らない。独立-7
    Medium: 検査対象が compact だけだったため、full 側だけがずれても
    検出できなかった）。
    """
    consts = load_lint_constants("lint-hitl-required-fields")
    field_sections = consts["FIELD_SECTIONS"]
    attr_names = {attr for attr, _ in field_sections}

    for rel in HITL_FIELDS_TAG_SOURCES:
        canonical = _read_canonical_source(rel)
        tag_body = _extract_hitl_fields_tag(canonical, rel)
        template_attrs = set(re.findall(r'([A-Za-z][A-Za-z0-9-]*)="', tag_body))

        assert attr_names == template_attrs, (
            f"lint 側 FIELD_SECTIONS の属性名 {sorted(attr_names)} と {rel} の "
            f"タグ属性名 {sorted(template_attrs)} が一致しない。"
            "書く側（テンプレート）と読む側（lint）の属性名は同期していること"
        )


def test_hitl_required_fields_allowed_values_match_compact_template_tokens() -> None:
    """`lint-hitl-required-fields.py` の `ALLOWED_FIELD_VALUES`（判定が実際に
    参照する値語彙の正本）が、compact/full 両テンプレートの
    `<gdd-hitl-fields ...>` タグが著者に示す `none|filled` という二択表記の
    各トークンと一致することを検査する（PR後-5 Medium: 属性**名**の同期は
    `test_hitl_required_fields_attrs_match_compact_template_tag` で足した
    が、値**語彙**側（`none|filled` -> `na|filled` のような変更）は無防備
    で suite を生き残り得た。PR後-6 Medium: 一度は `FIELD_VALUE_NONE`/
    `FIELD_VALUE_FILLED` だけを見る形で直したが、判定が実際に参照するのは
    `ALLOWED_FIELD_VALUES = (FIELD_VALUE_NONE, FIELD_VALUE_FILLED)` の方
    であり、`ALLOWED_FIELD_VALUES` に直接第三の値（例: `"na"`）を追加する
    widening は `FIELD_VALUE_NONE`/`FIELD_VALUE_FILLED` 自体を変えないため
    検出できなかった。`load_lint_constants` が `ast.Name` 参照を解決できる
    ようになったため、`ALLOWED_FIELD_VALUES` を直接読んで比較する。独立-7
    Medium: 検査対象が compact だけだったため、full 側の値語彙がずれても
    検出できなかった）。
    """
    consts = load_lint_constants("lint-hitl-required-fields")
    allowed_values = set(consts["ALLOWED_FIELD_VALUES"])

    for rel in HITL_FIELDS_TAG_SOURCES:
        canonical = _read_canonical_source(rel)
        tag_body = _extract_hitl_fields_tag(canonical, rel)
        value_tokens: set[str] = set()
        for value in re.findall(r'="([^"]*)"', tag_body):
            value_tokens.update(value.split("|"))

        assert allowed_values == value_tokens, (
            f"lint 側の ALLOWED_FIELD_VALUES {sorted(allowed_values)} と {rel} の "
            f"タグが示す値語彙 {sorted(value_tokens)} が一致しない。"
            "書く側（テンプレート）と読む側（lint、判定が実際に参照する定数）の"
            "許容値は同期していること"
        )


def _uses_name(node: ast.AST, name: str) -> bool:
    return any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(node))


def test_hitl_required_fields_validation_predicate_is_not_widened() -> None:
    """`ALLOWED_FIELD_VALUES` を使った受理判定が、他の条件との `or`/`and` で
    widen されていないことを AST で固定する（独立-7 Medium 実測: 判定式を
    `if value in ALLOWED_FIELD_VALUES or value == "na":` のように変異させて
    も、値語彙の同期テスト2本は `ALLOWED_FIELD_VALUES` 定数自体の内容しか
    見ないため green のまま通り、全量 test・validate-plugin.sh とも
    exit 0 だった。定数の同期だけでは、判定式側で定数を経由せず受理集合を
    直接広げる widening は検出できない。判定式の「形」自体をピン留めする。
    独立-8 Medium 実測: 初版は比較の右辺（comparators）を検査しておらず、
    `if value in ALLOWED_FIELD_VALUES + ("na",):` のように右辺を式で widen
    しても、`_uses_name` が式の中の `ALLOWED_FIELD_VALUES` を見つけて
    「対象の比較」として扱ってしまうだけで、右辺が単純な参照かどうかは
    検査していなかったため green のまま通っていた。右辺が
    `ALLOWED_FIELD_VALUES` への単純な参照そのものであることも固定する）。
    """
    source = (PLUGIN_ROOT / "scripts" / "lint-hitl-required-fields.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    compare_nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare) and _uses_name(node, "ALLOWED_FIELD_VALUES")
    ]
    assert compare_nodes, "ALLOWED_FIELD_VALUES を使った比較が見つからない"
    for node in compare_nodes:
        assert isinstance(node.left, ast.Name) and node.left.id == "value", (
            f"ALLOWED_FIELD_VALUES を使った比較の左辺が value ではない: {ast.dump(node)}"
        )
        assert [type(op) for op in node.ops] == [ast.In], (
            f"ALLOWED_FIELD_VALUES を使った比較演算子が in ではない: {ast.dump(node)}"
        )
        comparator = node.comparators[0] if len(node.comparators) == 1 else None
        assert isinstance(comparator, ast.Name) and comparator.id == "ALLOWED_FIELD_VALUES", (
            "ALLOWED_FIELD_VALUES を使った比較の右辺が単純な参照ではない "
            f"（式で widen されている可能性がある）: {ast.dump(node)}"
        )

    for node in ast.walk(tree):
        if not isinstance(node, ast.BoolOp):
            continue
        assert not any(_uses_name(value, "ALLOWED_FIELD_VALUES") for value in node.values), (
            "ALLOWED_FIELD_VALUES を使った判定が他の条件と or/and で合成されている "
            f"（受理集合が定数を経由せず widen されうる）: {ast.dump(node)}"
        )


def _first_markdown_block_after(text: str, heading: str) -> str | None:
    """`heading` の行より後ろで最初の ```markdown ブロックの中身を返す（ブロック内の `## ` 見出しで切らない）。"""
    if f"\n{heading}\n" not in text:
        return None
    rest = text.split(f"\n{heading}\n", 1)[1]
    match = re.search(r"^```markdown\n(.*?)^```$", rest, flags=re.DOTALL | re.MULTILINE)
    return match.group(1) if match else None


_FULL_TEMPLATE_CHECK_MESSAGES = (
    "too many overlapping summary sections",
    "承認ポイント数の宣言",
    "missing decision marker: OKでも許可されないこと",
)


def _run_decision_quality(path: Path, text: str) -> subprocess.CompletedProcess[str]:
    path.write_text(text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"), str(path)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_full_template_check_messages_are_emitted_by_the_lint(tmp_path: Path) -> None:
    """下のテストが「出ない」ことを見る 3 つの文が、lint から実際に出ることを先に確かめる。"""
    bad = "\n".join(
        [
            "### 承認サマリ",
            "### まず見るところ",
            "### 判断ポイント",
            "1. <判断テーマ>",
            "- 無回答時のデフォルト: 案Aを既定採用する",
        ]
    )
    result = _run_decision_quality(tmp_path / "bad.md", bad)
    for message in _FULL_TEMPLATE_CHECK_MESSAGES:
        assert message in result.stdout, result.stdout


def test_full_template_approval_summary_has_the_lint_required_field_name() -> None:
    """lint の必須語 `OKでも許可されないこと` が、出力テンプレートの承認サマリの欄名にある。"""
    template = _read_canonical_source("references/human-check-template.md")
    block = _first_markdown_block_after(template, "## 出力テンプレート")
    assert block is not None
    summary = block.split("\n### 承認サマリ\n", 1)[1].split("\n### ", 1)[0]
    required = load_lint_constants("lint-hitl-decision-quality")["REQUIRED_DECISION_MARKERS"]
    assert "OKでも許可されないこと" in required
    assert "- **OKでも許可されないこと**:" in summary, summary


def test_full_template_output_and_example_pass_summary_and_point_count_checks(tmp_path: Path) -> None:
    """full の出力テンプレートと具体例を lint-hitl-decision-quality にかけ、重複した要約と

    承認ポイント数の宣言の検査と、`OKでも許可されないこと` の欄の検査に落ちないことを
    確かめる（ほかの検査の結果は見ない。骨組みは placeholder のまま、具体例は
    `PR検証後の次の導線` が無いことで落ちる）。
    """
    template = _read_canonical_source("references/human-check-template.md")
    blocks = [_first_markdown_block_after(template, heading) for heading in ("## 出力テンプレート", "## 具体例")]
    assert all(blocks), "出力テンプレートと具体例の markdown ブロックが見つからない"
    for index, block in enumerate(blocks):
        result = _run_decision_quality(tmp_path / f"block-{index}.md", block)
        assert "Traceback" not in result.stderr, result.stderr
        for message in _FULL_TEMPLATE_CHECK_MESSAGES:
            assert message not in result.stdout, result.stdout
