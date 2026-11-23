# Abandon and Pause

> **所有**: ワークフロー途中での中断・一時停止・離脱の手順
> **参照元**: `gdd-status`

GDD ワークフローを途中で止めたい・やめたい・手動に切り替えたい場合の選択肢。

---

## 選択肢の一覧

| やりたいこと | 方法 | state の行先 | 復帰可能か |
|-------------|------|-------------|-----------|
| **一時停止**して後で再開 | session を閉じるだけ | 変化なし | Yes（SessionStart hook が Quick Reboot で復元） |
| **明示的に一時停止**を記録 | `state.md` に `Blocked Since=<now>` を手動記録 | blocked 扱い | Yes（blocker 解消後に再開） |
| **正式にキャンセル** | `/gdd-dev` で `gdd-completion-check` に到達 → cancelled | `Next Action=cancelled`（worktree の binding が指す steering は、これだけでは push・PR・merge の gate から外れない。外すには `Resume From: cancelled` も書く） | No（新規 steering で再開は可能） |
| **即座にキャンセル**（mid-build） | `state.md` の `Resume From` と `Next Action` をどちらも `cancelled` に手動設定 → cleanup | `Resume From: cancelled` / `Next Action: cancelled` | No |
| **新タスクに置き換え（supersede）** | 新タスクの brainstorming 中に旧 state.md へ `Status: superseded / Superseded By: <new-slug> / Resume From: cancelled` を記録 | `Resume From: cancelled`（resume 候補外） | No（audit trail として保持） |
| **GDD を離脱**して手動開発に戻る | session を閉じて `.steering/` を残したまま通常開発 | 変化なし | Yes（いつでも `/gdd-dev` で resume 可能） |

---

## 一時停止（Pause）

session を閉じるだけで十分。GDD の state は `.steering/` に永続化されており、次の session 開始時に SessionStart hook が Quick Reboot 情報を注入する。

### 明示的な一時停止を記録したい場合

外部の前提待ち（他チームの API 公開、環境構築待ち等）で長期間止まる場合は、`state.md` に `Blocked Since=<ISO 8601 timestamp>` を記録する。24 時間超で SessionStart hook が警告を表示する。

```
Blocked Since=2026-04-16T10:00:00+09:00
```

blocker が解消したら `Blocked Since` 行を削除して `/gdd-dev` で再開する。

---

## キャンセル（Cancel）

### 正規パス: gdd-completion-check 経由

`/gdd-dev` で再開し、「このタスクをキャンセルしたい」と伝える。`gdd-completion-check` に到達すると Step 21 で `Next Action=cancelled` が設定され、`gdd-using-git-worktrees` の Cancelled Cleanup（keep / archive / discard の 3 択）に進む。

### 短縮パス: mid-build からの即座キャンセル

`gdd-completion-check` に到達するまで待てない場合:

1. active worktree の `.steering/<slug>/state.md` を開き、`Resume From: cancelled` と `Next Action: cancelled` をどちらも書き、`Route In Progress` が `none` 以外なら `none` にする（pre-push・pre-PR・SessionStart の steering 検出は `state.md` を読む。pre-PR は `state.md` の `Next Action` が空のときだけ `tasklist.md` を読む。worktree の binding が指す steering については、`Resume From: cancelled` が無いと、pre-push・merge・pre-PR の gate は `Next Action`〔`tasklist.md` を含む〕だけの cancel の binding 先を候補に残す）
2. worktree を片付けるなら、`gdd-using-git-worktrees` の Cancelled Cleanup（keep / archive / discard）に従う（hook は `cancelled` を検出して誘導しない）

**注意**: 短縮パスでは completion-check の最終検証（AC Drift Check、Verification 確認）を skip する。キャンセル目的なので問題ないが、後で成果物を再利用する場合は検証が不完全であることを認識する。

---

## GDD 離脱（Manual Development に戻る）

GDD を使わず手動で開発を続けたい場合:

1. session を閉じる
2. `.steering/` ディレクトリはそのまま残す（削除不要）
3. 通常のブランチ操作・コミット・PR 作成を手動で行う
4. GDD に戻りたくなったら `/gdd-dev` で resume できる

**注意**: `.steering/` が残っていると、次の session 開始時に SessionStart hook が Quick Reboot 情報を表示する。気になる場合は `/gdd-dev` でキャンセルしてから離脱する。

---

## Gate のスキップについて

GDD では gate（requirements review / design review / human check / implementation review）を個別にスキップする機能は提供していない。これは意図的な設計判断:

- **trivial** タスク: 全 gate が自動スキップされる（そもそも gate を通らない）
- **quick (express)** タスク: requirements review / design review / completion check が自動スキップされる
- **quick (standard) / standard** タスク: sizing に応じた gate が必須

gate が過剰に感じる場合は、タスクの sizing が正しいかを確認する。sizing を変更するには `requirements.md` の `Task Size` を修正して `/gdd-dev` で再開する。

---

## Guardrails

- cancel / pause の操作は state 変更を伴うため、ユーザーの明示的な意思表示なしに実行しない
- `.steering/` ディレクトリの自動削除はしない（`gdd-using-git-worktrees` Cancelled Cleanup の選択肢を通す）
- cancel 後の remote branch 削除はユーザーに手動実行を案内する
