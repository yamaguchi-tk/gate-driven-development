"""AC-4: 分割前後でチェック名一覧が一致することを保証する等価性テスト。

canonical リストは分割前の validate-plugin.sh から手動で確定した固定値であり、
実装（manifest）からの動的抽出ではない。これにより manifest 側の欠落/過剰の
両方を検出できる（fixture が manifest を鏡写しにして自己一致するだけの
false-pass を防ぐ）。
"""
from __future__ import annotations


from _paths import PLUGIN_ROOT
MANIFEST_PATH = PLUGIN_ROOT / "tests" / "checks" / "manifest.tsv"

# Fixed 2026-07-09 from validate-plugin.sh (3,937 lines, pre-split), plus
# broken-reference-lint added 2026-07-11 (PR-0b R8-A A-5), plus
# agent-effort-schema added 2026-07-16 (Task E-7 AC-E7-1), plus
# pr-review-followup-polling-tokens added 2026-07-18 (Task E-2), plus
# pr-review-auto-arm-tokens added 2026-08-07 (auto-arm AC-11), plus
# stage-continuation-tokens added 2026-08-07 (stage continuation AC-13), plus
# pr-review-anticipation-tokens added 2026-08-08 (3f anticipation AC-6), plus
# hitl-population-tokens added 2026-08-08 (evidence population AC-8), plus
# gdd-self-development-tokens added 2026-08-08 (self-development rules AC-4), plus
# self-review-lane-tokens added 2026-08-18 (T-26 self-review lane tokens, AC-9/AC-10/AC-23/AC-24), plus
# self-review-lane-provenance added 2026-08-19 (T-28 self-review lane provenance, AC-21), plus
# version-not-consumed added 2026-08-19 (T-29 integration-target version reuse, AC-15), plus
# command-frontmatter-parse added 2026-08-18 (frontmatter YAML parse), plus
# bounded-claim-evidence added 2026-08-19 (T-30 bounded-claim evidence pairing, 分類5 下位型), plus
# osascript-arg-lint added 2026-08-27 (T-23 osascript の -e 連結禁止と here-doc quoted の静的固定, AC-21 隣接), plus
# mcp-retry-token added 2026-08-27 (T-23 MCP 再試行 1 回の文言の存在固定, AC-21), plus
# review-log-present added 2026-09-14 (軽いレーンの指摘記録の強制), plus
# hitl-lint-gate-wiring added 2026-09-15 (HITL 品質 lint の Stop hook 配線契約), plus
# hitl-required-fields-lint added 2026-09-15 (条件付き節の該当なし明記 + Option軸必須、warn-only配線), plus
# external-format-sampling-tokens added 2026-10-02 (外部形式の実測を AC より先に置く発火点の固定).
# 26 BLOCK-marker checks (grep-extracted) + 3 preamble checks (manually
# enumerated, no BLOCK marker) + 19 post-split additions = 48.
# superpowers-benchmark-gate と skill-red-green-gate は 2026-11-09 に外した (環境変数を立てる箇所が無かった)。
# 上記の内訳は split 時点の導出根拠であり、実行時の BLOCK 出力数ではない
# (opt-in check は BLOCK を出さずに skip するため実行時の出力数は上記未満になる)。
# Order matches current execution order.
CANONICAL_CHECK_NAMES: list[str] = [
    "skill-count-budget",
    "osascript-arg-lint",
    "mcp-retry-token",
    "skill-body-budget",
    "codebase-health-smoke",
    "grade-evals",
    "classify-intent",
    "hooks",
    "agent-effort-schema",
    "skill-reference-drift",
    "docs-links-valid",
    "express-promotion-transition",
    "workflow-loop",
    "active-steering-required-fields",
    "active-steering-candidate-resolution",
    "external-verifier-smoke",
    "human-check-language-lint",
    "clarification-brief-lint",
    "hitl-outcome-audit-lint",
    "hitl-complexity-lint",
    "hitl-display-integrity-lint",
    "resume-integrity-lint",
    "pr-review-followup-state-lint",
    "worktree-provenance-lint",
    "state-tasklist-continuity-lint",
    "hitl-decision-quality-lint",
    "lint-scripts-syntax",
    "lint-scripts-functional",
    "hooks-wiring-lint",
    "broken-reference-lint",
    "pr-review-followup-polling-tokens",
    "pr-review-auto-arm-tokens",
    "stage-continuation-tokens",
    "pr-review-anticipation-tokens",
    "hitl-population-tokens",
    "gdd-self-development-tokens",
    "self-review-lane-tokens",
    "self-review-lane-provenance",
    "version-not-consumed",
    "bounded-claim-evidence",
    "command-frontmatter-parse",
    "review-log-present",
    "hitl-lint-gate-wiring",
    "hitl-required-fields-lint",
    "external-format-sampling-tokens",
]


def _read_manifest_names() -> list[str]:
    if not MANIFEST_PATH.exists():
        raise AssertionError(
            f"manifest not found: {MANIFEST_PATH} "
            "(expected after validate-plugin.sh split; before split this test "
            "must fail RED)"
        )
    names: list[str] = []
    for raw_line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        # validate-plugin.sh（bash `IFS=$'\t' read`）と同じ前提でパースする:
        # 行や列の前後空白を strip しない。空白混入は fail-closed で検出する。
        columns = raw_line.split("\t")
        if len(columns) != 3 or any(column != column.strip() for column in columns):
            raise AssertionError(f"malformed manifest.tsv row (expected 3 tab-separated columns, no extra whitespace): {raw_line!r}")
        name, _blocking, _script = columns
        names.append(name)
    return names


def test_manifest_preserves_execution_order() -> None:
    """manifest 行の順序が現行の実行順（canonical 順）と一致する。

    **リスト完全一致なので件数一致を含意する** —— かつて `test_canonical_count_is_42`
    という件数テストがあったが、`== 42` -> `== 44` に直したとき**テスト名の数値だけが
    取り残された**（T-23 Attempt 1 / M-8）。manifest から導出する形に直したところ
    今度は本テストに完全に包含され、**単独で落ちる入力が存在しなくなった**（同 Attempt 2 / CQ-M2）。
    件数リテラルの正本はヘッダーの算術コメント 1 箇所で、
    `test_canonical_header_comment_matches_canonical_list` が照合する。
    """
    manifest_names = _read_manifest_names()
    assert manifest_names == CANONICAL_CHECK_NAMES
