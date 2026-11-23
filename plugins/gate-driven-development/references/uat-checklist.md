# UAT Checklist Template

> **所有**: `gdd-completion-check` Part D で提示する手動確認チェックリストのフォーマットと運用ルール
> **参照元**: `gdd-completion-check` Part D

`Next Action=done` 確定後、Post-Completion Learning の前に、ユーザー向け UAT（User Acceptance Testing）チェックリストを提示する。これはフォーマルな gate ではなく、人間が実際に動かして確認できる機会を提供するもの。

## いつ実行するか

- `Next Action=done` が確定した直後（completion-check Step 20 通過後）
- Post-Completion Learning や PR Flow の **前**
- `done` をブロックしない（オプション提示）

## 抽出ルール

1. `requirements.md` の AC から **ユーザーが手動で確認できる項目** を **3-5 件** に絞る
2. テストで自動確認済みの AC は **除外**（重複提示しない）
3. 内部実装の正確性（型 / 性能 / refactor）は UAT 対象外。**外部観測可能な挙動** のみ

## 提示フォーマット

```markdown
## 手動確認チェックリスト（任意）

AI の自動検証は完了していますが、実際に動かして確認したい場合は以下をお試しください:

- [ ] <AC から抽出したシナリオ 1>（確認方法: <具体的な操作>）
- [ ] <AC から抽出したシナリオ 2>
- [ ] <AC から抽出したシナリオ 3>

問題が見つかった場合は `/gdd-dev <問題の説明>` で続行できます。
```

## 運用ルール

1. **UAT は `done` をブロックしない**: ユーザーが応答せず次のターンに進んだ場合も `done` として扱う
2. **問題報告時の扱い**: ユーザーが問題を報告した場合は新しい GDD タスクとして `/gdd-dev` で受け付ける（現タスクは `done` のまま）。post-merge hotfix と同じ扱い
3. **UAT 提示後の flow**: `<gdd-stop>` を出す前に Post-Completion PR Flow に進む

## Why

GDD の completion-check は AI 主導の証跡確認で完結するが、「実際に動かした」確認がないと人間が不安になる。フォーマルな gate にせず提案として出すことで:

- GDD の自律完了契約を崩さない（done は AI 判定で確定）
- 人間の安心感を担保（実動作確認の機会を明示提供）
- 問題発見時は次の steering として独立処理（current task を re-open しない）
