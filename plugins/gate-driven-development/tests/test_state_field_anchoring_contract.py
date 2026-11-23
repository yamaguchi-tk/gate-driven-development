"""state.md の field 存在判定を行頭アンカーで行う契約テスト。

背景（PR #191 Copilot レビュー指摘）:
`validate-steering-write.py:has_state_field` は `f"{field}:" in text` の単純な
部分文字列検索だった。そのため本文の散文に `Next Action:` という文字列が
含まれるだけで「field が存在する」と誤判定し、write hook の deny が fail-open で抜けた。

同ファイルの `state_field_value` は既に行頭アンカー付き正規表現を使っており、
同一ファイル内で読み取り規約が割れていた。存在判定を値取得と同じアンカー方式に揃える。

`has_started_at` も同型の部分文字列検索なので同じ規約に揃える。
`state_requires_started_at`（検査の trigger）も揃える必要がある。
trigger だけ緩いままだと「散文で trigger され、アンカー済み検査で欠落と判定される」
非対称が生まれ、正常な書き込みが誤って deny される。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

from _paths import PLUGIN_ROOT
SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"

CORE_FIELDS = (
    "Resume From: gdd-test-driven-development\n"
    "Human Check Status: approved\n"
    "Route In Progress: none\n"
    "Started At: 2026-07-30T09:00:00Z\n"
)


@pytest.fixture()
def module(tmp_path, monkeypatch):
    """deny counter がユーザー環境を汚さないよう state dir を tmp に向けて読み込む"""
    monkeypatch.setenv("GDD_HOOK_STATE_DIR", str(tmp_path / "hook-state"))
    spec = importlib.util.spec_from_file_location("validate_steering_write_anchor", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_steering_write_anchor"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run(module, payload: dict) -> tuple[int, str]:
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        with contextlib.redirect_stdout(io.StringIO()):
            original = sys.stdin
            sys.stdin = io.StringIO(json.dumps(payload))
            try:
                code = module.main()
            finally:
                sys.stdin = original
    return code, stderr.getvalue()


# --- unit: has_state_field の読み取り規約 -------------------------------------

def test_prose_mention_is_not_a_field(module):
    """散文中の `Next Action:` は field の存在として数えない

    これが fail-open の実体。`state_field_value` は同じ入力で空文字を返しており、
    存在判定と値取得で読み取り規約が割れていた。
    """
    prose = "## Last Handoff Summary\n次のターンでは Next Action: を必ず記録すること。\n"
    assert module.has_state_field(prose, "Next Action") is False
    assert module.state_field_value(prose, "Next Action") == ""


def test_field_forms_in_real_state_md_are_recognized(module):
    """実データに存在する field 表記はすべて認識する（規約を狭めすぎていないこと）"""
    for line in (
        "Next Action: gdd-implementation-gating",
        "Next Action=gdd-implementation-gating",
        "- Next Action: gdd-implementation-gating",
        "- `Next Action`: gdd-implementation-gating",
        "Next Action : gdd-implementation-gating",
        "Next Action=gdd-implementation-gating | evidence: x",
    ):
        assert module.has_state_field(line + "\n", "Next Action") is True, line


def test_indented_lines_are_not_fields(module):
    """インデント行は field ではない（2026-08-30 改訂）。

    元の表は `  Next Action : ...` を「実データに存在する形」として present 側に
    置いていたが、実データの state.md / tasklist.md を実測したところ canonical field を
    インデントして書く file は無かった。一方でインデント行を field と数える規約は、
    入れ子 bullet の履歴メモ（`  - `Next Action=gdd-implementation-gating`（Attempt #2
    へ再入場）`）を canonical と誤認する経路そのもので、実際に `gh pr create` が
    `Next Action=gdd-implementation-gating` で block される事故を起こした。

    読み手（`gdd_extract_doc_field`）と同じ「行頭 + bullet marker 1 個まで」へ揃える。
    規約の正本は `tests/test_canonical_field_line_anchoring_contract.py`。
    """
    for line in (
        "  Next Action : gdd-implementation-gating",
        "  Next Action: gdd-implementation-gating",
        "  - Next Action: gdd-implementation-gating",
        "    - `Next Action=gdd-implementation-gating`（Attempt #2 へ再入場）",
        "\t- Next Action: gdd-implementation-gating",
    ):
        assert module.has_state_field(line + "\n", "Next Action") is False, line
        assert module.has_state_field_line(line + "\n", "Next Action") is False, line
        assert module.state_field_value(line + "\n", "Next Action") == "", line


def test_has_state_field_agrees_with_state_field_value(module):
    """存在判定と値取得は同じ読み取り規約であること（同一ファイル内の割れを塞ぐ）"""
    for text in (
        "Route In Progress: none\n",
        "本文で Route In Progress: について触れるだけの行\n",
        "## Route In Progress の運用\n",
        "Route In Progress:\n",
        "Route In Progress:   \n",
        "Route In Progress: | evidence: x\n",
    ):
        assert module.has_state_field(text, "Route In Progress") == bool(
            module.state_field_value(text, "Route In Progress")
        ), text


def test_blank_value_counts_as_missing(module):
    """値のない field 行は「存在する」と数えない

    read 側 `detect-steering.sh:gdd_validate_active_state_fields` は
    `[[ -z "${_value// /}" ]]` で空値・空白のみの値を missing 扱いする。
    write 側が prefix の有無だけで present と判定すると、値が空でも Tier 1 が
    充足したことになり deny が抜ける（読み手が厳格・書き手が緩いの再発）。
    """
    for text in ("Resume From:\n", "Resume From:   \n", "- `Resume From`=\n"):
        assert module.has_state_field(text, "Resume From") is False, text
        assert module.state_field_value(text, "Resume From") == "", text


def test_value_is_not_pulled_from_the_following_line(module):
    """値なし field の直後の行を値として拾わない

    区切り文字の後を `\\s*` で読むと改行も食うため、`Resume From:` の値として
    次行の内容が返る。値の有無で判定するようにすると、この取り違えがそのまま
    「空値なのに present」の抜け道になる。
    """
    text = "Resume From:\nNext Action: gdd-implementation-gating\n"
    assert module.state_field_value(text, "Resume From") == ""
    assert module.has_state_field(text, "Resume From") is False
    # 直後の行は自分自身の field としては正しく読める
    assert module.state_field_value(text, "Next Action") == "gdd-implementation-gating"


def test_has_started_at_uses_the_same_convention(module):
    """`has_started_at` も同型の部分文字列検索だったので同じ規約に揃える"""
    assert module.has_started_at("Started At: 2026-07-30T09:00:00Z\n") is True
    assert module.has_started_at("- `Started At`= 2026-07-30T09:00:00Z\n") is True
    assert module.has_started_at("state.md には Started At: を書く必要がある\n") is False


def test_state_requires_started_at_anchors_but_ignores_the_value(module):
    """検査の trigger は行頭アンカーで読むが、値の有無は問わない

    trigger と充足検査で必要な条件が違う:

    - trigger（`state_requires_started_at`）は「routing field に触ったか」。
      部分文字列のままだと散文で trigger され、アンカー済みの充足検査で欠落と
      判定されて正常な書き込みを誤 deny する
    - 充足検査（`has_state_field`）は「値が入っているか」

    trigger まで値必須にすると、routing field を**空値に更新する**書き込みが
    trigger をすり抜け、Tier 1 検査が走らないまま通る（fail-open）。
    """
    assert module.state_requires_started_at("Resume From: gdd-task-breakdown\n") is True
    # 値なしでも「触った」ので trigger する（充足検査はこの後で欠落と判定する）
    assert module.state_requires_started_at("Route In Progress:\n") is True
    assert module.state_requires_started_at("- `Human Check Status`=\n") is True
    # 散文は trigger しない
    assert module.state_requires_started_at("Resume From については後で決める\n") is False


# --- integration: deny が fail-open で抜けないこと -----------------------------

def _state_path(tmp_path: Path) -> Path:
    p = tmp_path / ".steering" / "20260730-anchor" / "state.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def test_denies_write_that_only_blanks_a_routing_field(module, tmp_path):
    """routing field を空値にするだけの書き込みも検査対象になる

    trigger を値必須にすると、この chunk は「routing field に触っていない」と
    見なされて Tier 1 検査自体が走らず、空値のまま通ってしまう。
    """
    path = _state_path(tmp_path)
    code, stderr = _run(
        module,
        {"tool_name": "Write", "tool_input": {"file_path": str(path),
                                              "content": "Route In Progress:\n"}},
    )
    assert code == 2, f"blanking a routing field must be checked, got exit={code}"
    assert "Route In Progress" in stderr


def test_denies_when_tier1_field_has_a_blank_value(module, tmp_path):
    """Tier 1 field が値なしで書かれている書き込みは deny される

    read 側は空値を missing 扱いするので、write 側が通すと
    「書けたのに読み取り側で invalid」という非対称が残る。
    """
    path = _state_path(tmp_path)
    content = (
        "Resume From: gdd-test-driven-development\n"
        "Human Check Status: approved\n"
        "Route In Progress:\n"
        "Started At: 2026-07-30T09:00:00Z\n"
    )
    code, stderr = _run(
        module,
        {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}},
    )
    assert code == 2, f"blank Route In Progress must not satisfy Tier 1, got exit={code}"
    assert "Route In Progress" in stderr


def test_denies_when_tier1_field_only_appears_in_prose(module, tmp_path):
    """Tier 1 field が散文にしか無い書き込みは deny される（旧実装は allow していた）"""
    path = _state_path(tmp_path)
    content = (
        "Resume From: gdd-test-driven-development\n"
        "Human Check Status: approved\n"
        "Started At: 2026-07-30T09:00:00Z\n"
        "\n## メモ\n差し戻し時は Route In Progress: を更新する運用にしている。\n"
    )
    code, stderr = _run(
        module,
        {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}},
    )
    assert code == 2, f"prose-only Route In Progress must not satisfy Tier 1, got exit={code}"
    assert "Route In Progress" in stderr


def test_denies_when_next_action_only_appears_in_prose(module, tmp_path):
    """canonical tasklist phase で Next Action が散文にしか無い場合も deny される"""
    path = _state_path(tmp_path)
    path.parent.joinpath("tasklist.md").write_text("## Current Task\n", encoding="utf-8")
    content = (
        CORE_FIELDS
        + "Requirements Review Status: approved\n"
        + "Design Review Status: approved\n"
        + "\n## Last Handoff Summary\n次のターンでは Next Action: を必ず記録すること。\n"
    )
    code, stderr = _run(
        module,
        {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}},
    )
    assert code == 2, f"prose-only Next Action must not satisfy the gate, got exit={code}"
    assert "Next Action" in stderr


def test_allows_when_next_action_is_a_real_field(module, tmp_path):
    """canonical field として書かれていれば通る（アンカー化で正常系を壊していないこと）"""
    path = _state_path(tmp_path)
    path.parent.joinpath("tasklist.md").write_text("## Current Task\n", encoding="utf-8")
    content = (
        CORE_FIELDS
        + "Requirements Review Status: approved\n"
        + "Design Review Status: approved\n"
        + "Next Action: gdd-implementation-gating\n"
    )
    code, stderr = _run(
        module,
        {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}},
    )
    assert code == 0, f"canonical Next Action must be allowed: {stderr}"
