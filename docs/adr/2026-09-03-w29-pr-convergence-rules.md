# ADR: W10 / W-29 — finding category taxonomy と merge-gate 判定の刷新

- Status: Accepted（2026-09-04 design-gating、2026-09-06 completion-check Round 22 approved）
- 対象タスク: `20260903-w29-pr-convergence-rules`
- リリース: `plugins/gate-driven-development/CHANGELOG.md` § `[0.39.1]`（origin/main の別 PR が版数 `0.39.0` を先に消費していたため付け替え）
- **逐語アーカイブ（正本）**: `plugins/gate-driven-development/docs/design/2026-09-03-w29-pr-convergence-rules-adr.md`

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

本ファイルは repo 直下の ADR インデックスである。**個々の判断の本文・数値・実測はすべて上記の逐語アーカイブが正本**で、
ここには**転記しない**（同じ値を 2 箇所に置くと片方が黙って陳腐化するため）。

## Context

PR レビューの収束条件が「指摘 0 件」を機械強制していたため、帳簿・文書の不整合で production 欠陥ゼロのままマージできない、severity ラベルの揺れで実害のある medium が素通りする、PR 規模・巡数の上限が無いといった問題があった（実測: PR 旧#949 が 87 巡 / 40.7h、PR 旧#25 が 6 巡 / 13h、自傷率 95%）。

## Decisions

逐語アーカイブに ADR-1〜ADR-8 として記録した。主なものは次のとおり（詳細・根拠・却下案は各 ADR を参照）。

| ADR | 決定の要旨 |
|---|---|
| ADR-1 / ADR-2 | `category` 語彙 9 値の単一正本化（named alias 方式）と、契約テストの走査範囲（バッククォート付きトークン形のみ・`agents/` 除外） |
| ADR-3 | 旧書式（`blocking` key 欠落）の既定は requirements.md (c) 定義（warning 記録 + `high != 0` のみで block。当時の判定）を採る |
| ADR-4 | requirements の参照先ずれ 3 件を design 側で訂正 |
| ADR-5 | budget 方針の不確定・承認記録の食い違いにより Round 2 を `human_recheck_required` で一度差し戻し、4 論点をユーザー確定回答後に Round 3 で approved |
| ADR-6 | budget 上限 3 本すべてを等価交換のみで吸収し、既存 worked example は削除ではなく `docs/references-archive/` へ移送する |
| **ADR-7** | **`Medium Disposition` に HEAD sha と件数一致検査を持たせ、緩和分の唯一の統制が 1 行で恒久バイパスされる経路を閉じる** |
| ADR-8 | category 未付与 finding の impl-gate 側既定を `product` 相当（Round 消費・非 blocking、fail-closed）にする |

## Consequences

- merge gate（`hooks/scripts/run-merge-gate-hook.sh`）の block 判定が `medium != 0` から `high != 0 || blocking != 0` へ置換され、medium ≥ 1 の証跡は `Medium Disposition` の記録が必須になった
- `references/task-sizing.md` に PR 規模上限（production 差分 2,000 行 / 25 ファイル）が新設された
- `skills/gdd-implementation-gating/SKILL.md` の Round カウントが Round 消費 category に限定され、帳簿系 finding だけでは巡数が増えなくなった
- `references/*.md` line budget / SKILL body line budget / standard runtime profile token budget の 3 本すべてが base から不変のまま出荷される（等価交換の遵守）

## 統合作業に関する追記（ADR に昇格しない運用判断）

design 確定後、`origin/main`（34 commit 先行、`tests/test_merge_gate_hook.py` の 7 ファイル分割を含む）への統合作業で、`git rebase` の代わりに `git merge` を採用したこと、分割後ファイルへの本 PR 差分の再配置、`gdd-codebase-health-baseline.json` の閾値引き上げに対するユーザー承認取得の経緯は、逐語アーカイブ末尾「補遺」に記録した。

## 未処置として PR 本文へ送った論点

`GDD_MG_REQUIRE_BLOCKING_FIELD` の反転（W-28 着地後）、`references/self-review-lanes.md` の `Medium Disposition` valid 述語の追加検査（`gdd_extract_doc_field` の節非依存という既知の限界）ほか。**一覧と根拠は PR 本文および `.steering/20260903-w29-pr-convergence-rules/tasklist.md` § Verification**。
