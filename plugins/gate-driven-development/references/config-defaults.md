# Config Defaults

> **所有**: 設定値・閾値・タイムアウト・リトライ回数・バッチサイズを設計段階でどう扱うか
> **参照元**: `agents/gdd-planning-reviewer.md`, `references/requirements-template.md`, `references/task-sizing.md`

GDD では、運用環境で変わり得る値を実装コードへ直接埋め込まない。planning / design review では、値そのものより **どこで変更できるか、未設定時にどう振る舞うか、検証できるか** を確認する。

## いつ設定化を求めるか

以下の値が要件・設計・実装方針に出てきた場合は、原則として設定化または named constant 化を検討する。

- タイムアウト秒数、polling interval、retry 回数
- バッチサイズ、page size、rate limit、concurrency limit
- スコア閾値、confidence threshold、分類境界
- retention 日数、TTL、再試行猶予時間
- 外部サービス endpoint、feature flag、rollout percentage
- LLM / Judge / eval の model id、effort、temperature、sample size

## 判断基準

| 判断 | 使ってよい条件 | 必須記録 |
|------|----------------|----------|
| named constant | 環境差は無いが、意味を名前で説明したい | constant 名、単位、理由 |
| config file / env | 環境・顧客・運用状況で変わる | 設定場所、未設定時 default、parse 失敗時挙動 |
| requirements.md に固定 | 業務仕様として固定値が正本 | 値、単位、変更時の承認者 |
| N/A | 値が今回の変更に存在しない | `N/A - no tunable values` |

## Fail-Closed Defaults

denylist / allowlist / security boundary / external posting / destructive operation に関わる設定は、未設定・空・parse 失敗時に fail-closed を基本にする。

- allowlist が無い: deny
- credential backend が不明: stop / human_recheck_required
- external posting destination が不明: no-post
- destructive operation approval が不明: stop

fail-open が必要な場合は、requirements.md の承認ポイントで人間に明示確認する。

## Review Questions

planning reviewer は、設定値が出てきたときに以下を確認する。

1. 値の単位と意味が明記されているか
2. default 値の根拠があるか
3. 未設定・空・parse 失敗時の挙動が定義されているか
4. 本番 / staging / local / CI で変わり得るか
5. テストで default と override の両方を確認できるか
6. security / destructive / external write に関わる値が fail-open になっていないか

## Minimal Artifact Shape

requirements.md または design.md には、必要に応じて以下のように短く残す（値が無い場合は表を省略し `N/A - no tunable values in this change.` の 1 行にする）。

```markdown
## Config Defaults

| Name | Default | Unit | Override Location | Invalid/Missing Behavior | Verification |
|------|---------|------|-------------------|--------------------------|--------------|
| REQUEST_TIMEOUT | 30 | seconds | env:REQUEST_TIMEOUT | fail with clear error | unit + config parse test |
```
## Merge Gate
| Name | Default | Unit |
|------|---------|------|
| Merge Gate Review Wait | 40 | minutes |
| Merge Gate Recheck Freshness | 10 | minutes |
| Merge Gate Approval Freshness | 120 | minutes |

この値は 3 箇所に写しがある。**実際に gate が読むのは `hooks/scripts/run-merge-gate-hook.sh` の shell literal（`MERGE_GATE_*_MINUTES` の代入）だけ**で、hook は `constants.py` を import しない。`hooks/scripts/lib/constants.py` の `MERGE_GATE_REVIEW_WAIT_MINUTES` / `MERGE_GATE_RECHECK_FRESHNESS_MINUTES` / `MERGE_GATE_APPROVAL_FRESHNESS_MINUTES` は python 側の参照用ミラーで、本表が人間向け正本。**値を変えるときは 3 箇所すべてを同じ commit で更新する**（本ファイルだけを編集しても gate の閾値は変わらない）。md↔code 同期は契約テスト（`tests/test_merge_gate_hook_contracts.py`）が `## Merge Gate` 見出し直下の最初の表から抽出した値と一致することを固定し、加えて `Merge Gate Approval Freshness` > `Merge Gate Review Wait` の大小関係も assert する（承認鮮度が待機値以下だと、正規手順の待機がそのまま承認を失効させてしまうための不変条件）。runtime の env override は無い。

