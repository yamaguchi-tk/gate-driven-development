# Reviewer Lineage（Cross-Steering Reviewer 履歴）

> **所有**: 同一 root feature の steering 系統（supersede / hotfix / amendment 関係）における reviewer selection と判定結果の累積記録
> **上位正本**: `reviewer-selection.md`（selection rule 本体）、`state-field-tiers.md`（state field の Tier 分類）
> **参照元**: `gdd-brainstorming`（lineage 抽出）、`gdd-design-gating` / `gdd-implementation-gating`（reviewer 再選定の参考）

## 背景

GDD は 1 steering 内で `Planning Reviewer Selection` / `Implementation Reviewer Selection` を canonical に記録するが、**cross-steering（同 root feature の hotfix 系統や supersede 系統）での reviewer 履歴は今まで保持していなかった**。結果として:

- 同じ feature 上の連続した hotfix で reviewer が context をリセットして毎回ゼロから判定する
- 「前回 security-reviewer で見たので今回は waived でいい」のような judgement を artifact に残せない
- reviewer fatigue / 同じ false positive の繰り返し / 同じ true positive の見落とし

これらを軽減するため、optional な **Reviewer Lineage** field を追加する。

## 設計原則

1. **自動継承禁止**: lineage 情報は judgment の **参考** にとどめる。次 steering で同じ reviewer を自動的に再 selected にはしない。human / brainstorming が明示的に判断する
2. **Tier 3 (Audit) field**: state.md の Tier 1 / 2 には入れず、optional な lineage section として記録。不在でも fail-closed にならない
3. **lineage は append-only**: 新 steering 開始時に parent から copy し、現 steering で追記する。過去の判定を上書きしない
4. **scope: same-feature steering chain**: 無関係な過去 steering の reviewer 情報は混入させない（feature の root を anchor にする）

## Lineage が成立する関係

以下のいずれかで 2 つの steering が「同一 root feature 系統」と判定される:

| 関係 | 検出元 | 例 |
|---|---|---|
| **Supersede** | `state.md` の `Superseded By` / `Superseded Steerings` | 旧 planning が放棄されて新 steering で再着手 |
| **Hotfix Of** | `state.md` の `Origin Steering` / `Hotfix Of` | merge 後の bug fix steering |
| **Amendment** | `gdd-requirements-amendment` 経由で作成 | done 済み feature への追加要件 |
| **同名 slug 接頭辞** | `.steering/YYYYMMDD-<feature-name>-*` で `<feature-name>` 一致 | 弱い heuristic、明示 anchor がない場合のフォールバック |

## state.md への記録形式

新 steering 開始時に parent から lineage を抽出して以下のセクションを `state.md` に追加する（optional / Tier 3）:

```markdown
## Reviewer Lineage（同一 root feature 系統の reviewer 履歴）

- root_feature: 20260315-feed-rdf-strictness
- chain:
  - steering: 20260315-feed-rdf-strictness | relation: root | planning_reviewer=approved | security_reviewer=waived(no-untrusted-input) | implementation_reviewer=approved | outcome: done | merged_at: 2026-03-20
  - steering: 20260420-feed-rdf-hotfix-encoding | relation: hotfix_of=20260315-feed-rdf-strictness | planning_reviewer=approved | security_reviewer=waived(no-untrusted-input) | implementation_reviewer=changes_requested(1 round) | outcome: done | merged_at: 2026-04-22
  - steering: 20260510-feed-rdf-additional-fields | relation: amendment_of=20260315-feed-rdf-strictness | current=true
```

## brainstorming での lineage 抽出手順

`gdd-brainstorming` の `amendment` / `supersede` / `hotfix` 関係検出時に以下を実行:

1. `gdd-using-git-worktrees` の active steering 候補列挙ロジックで全 worktree の `.steering/*/state.md` を grep
2. parent steering を 1 つに特定する（複数候補ある場合は fail-closed → human に確認）
3. parent の `state.md` から以下を抽出:
   - `Planning Reviewer Selection`
   - `Implementation Reviewer Selection`（tasklist.md 側）
   - `Resume From=done` または `Next Action=done` の最終遷移時刻
4. parent に既に `Reviewer Lineage` section があれば、それを copy + 自分の steering を `current=true` で追加
5. 無ければ新規作成

## design-gating / implementation-gating での参照

各 gate skill の reviewer selection step で以下を「参考情報」として確認する:

- lineage の最新 1-2 steering の reviewer 判定
- false positive / changes_requested の繰り返し
- 同一 root feature で security-reviewer が一貫して `waived` ならば、本 steering でも同様の判断材料となる（ただし自動 waive ではない）

明示的な記載例:

```markdown
# 例: gdd-design-gating Step 7（reviewer selection）

7. `references/reviewer-selection.md` に従って applicable reviewer を選び、state.md に記録する。
   - `references/reviewer-lineage.md` § Lineage に同一 root feature の過去判定があれば参考にする
   - 自動継承はしない（lineage は judgment 材料）
```

## 自動化 lint

`scripts/lint-reviewer-lineage.py` が以下の anti-pattern を機械的に検出する:

1. **Bias warning（一貫した waived）**: 同じ root feature で同じ reviewer が **3 連続**（default、`--threshold-consecutive-waived` で調整可）`waived` のとき、true positive 見落としの可能性を WARN として出力
2. **Repeated changes_requested**: 同じ reviewer が **3 連続**で `changes_requested` を返している場合、reviewer instruction の調整 or rotation 検討を WARN として提案
3. **Long chain without rotation**: chain が **5+ steerings** に達しても reviewer set が完全に同じなら、新観点 / 別 reviewer の追加検討を WARN として提案

呼び出し例:

```sh
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-reviewer-lineage.py --steering-dir .steering/<task>/
```

実行タイミング:

- **brainstorming で supersede / hotfix / amendment 関係を検出し lineage を抽出した直後**: 新 steering 開始時に過去 chain の bias を確認する
- **gdd-design-gating / gdd-implementation-gating の reviewer selection step**: 選定判断の参考情報として lineage warnings を考慮

WARN は **fail-closed ではない**。selection の最終判断は人間 / brainstorming が行う。lint は判断材料の提供にとどめる。

### 将来候補（未実装）

- **False positive learning**: 同じ reviewer から同じ false positive が連続している場合、severity を 1 段階下げる提案。reviewer Calibration の lineage 連携が必要
- **Rotation suggestion (auto)**: 単一 reviewer pattern が長期間続く場合、reviewer agent rotation を自動提案。reviewer pool infrastructure 前提

## 後方互換性

- lineage section が無い既存 steering は影響を受けない（field 欠落で fail-closed にしない）
- hooks は lineage を解釈しない（Tier 3 / Audit として無視）
- lineage は append-only で過去判定を変更しない

## Why

- 同 feature の hotfix chain で reviewer judgement が arbitrary に揺れる事故を軽減する
- false positive の繰り返しを human が判定できる材料を artifact に残す
- 真の reviewer rotation（複数 agent の round-robin）は別 infrastructure 改修が必要だが、lineage の枠組みは先行して整備できる
