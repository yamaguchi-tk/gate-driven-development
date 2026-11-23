# Express Requirements Template

> **所有**: `quick (express)` の requirements.md 最小形
> **上位正本**: `references/requirements-template.md`
> **目的**: 実装コード 1〜2 ファイルの小変更で、standard 用の長い要求項目を読ませず、実装に必要な情報だけを残す

`quick (express)` ではこのテンプレートを使う。ここに無い情報が必要になった時点で `quick (standard)` 以上へ昇格する。事実は AC に 1 回だけ書き、ほかの欄は `AC-n` を引く。

## Template

```markdown
# Requirements: <task slug>

Task Size: quick (express)

## Summary Brief

### 一言
<何を直す / 追加するかを 1 行>

### 判断材料
- 確定: <AC-1 参照>
- 未確定: <無ければ `なし`>
- やらないこと: <今回触らない範囲>
- 外部依存: <無ければ `なし`>

### 承認ポイント
1. <方向性のほかに OK で承認してほしい判断を 2 件以内。無ければ方向性だけ> / 根拠: <AC と同じ>
N. **方向性**: <目的 1 行> / 自走範囲: <Files の内。実装コードが Files の外へ波及したら quick (standard) に昇格（テスト・ドキュメント・skill 設定の付随更新は数えない）> / 自走上限: <human-check-template § 自走上限の置換値> → OK / 自走範囲を制限したい

### ズレ確認

## Scope

- Change: <AC-1 参照>
- Files: <想定ファイル。実装コードは 1〜2 件（付随するテスト・ドキュメント・skill 設定は数えない）>
- Non-goals: <今回やらないこと>

## 受入条件

- AC-1: <テスト可能な完了条件>（開いた入力の扱い: <構造で閉じる / なし / 列挙に縮める / 限界として開示する のいずれか。候補があれば構造で閉じる。限界として開示するは合格基準のある AC に使わない。開いた入力を扱わないなら `なし（対象は<有限集合>）`>） / 根拠: <読むか測った `file:line`・コマンドと値、`未測（理由）`、`なし（理由）`> / 計測: <何を・どの母集団で・どの値なら合格か>

## Implementation Policy

- Existing pattern: <参照した既存実装 / N/A の理由>
- Approach: <どう直すか>
- Test plan: <RED / regression / smoke のどれで確認するか>

## Express Minimal Trace

| Field | Value |
|---|---|
| User-stated condition | <ユーザーの完了条件の要約> |
| Testable AC mapping | <AC-1 へどう変換したか> |
| Single-stage reason | <後続 stage が不要な理由> |
| Human recheck trigger | AC 追加 / 修正範囲拡大 / 実装コード 2 ファイル超 / security・route・schema 影響 |

## Implementation Sequence Plan

N/A - single-stage express（<根拠>）

## 既存実装の確認

- Checked: <関連ファイル / 類似実装 / テスト>
- Risk if wrong: <無ければ `低`>
```

## Promotion Rules

以下のいずれかが見えたら、このテンプレートでは続けない。

- 実装コードのファイルが 3 件以上になりそう（テスト・ドキュメント・skill 設定の付随更新は数えない）
- AC が 4 件以上に増える
- security / auth / route / DB schema / external API / prompt output contract に触れる
- 既存実装調査が `not_run`
- 段階実装や後続 PR が必要

昇格時は `references/requirements-template.md` の quick standard / standard template に戻る。
