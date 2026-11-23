# Gate Checklists

> **所有**: `gdd-completion-check` で実行される checklist 系 step（AC Drift Check / Stub Detection / External Dependency Completeness / Skill Document Quality）の手順と判定基準
> **上位正本**: `verification-before-completion.md`（Fresh Verification / Iron Law）、`adr-vs-design.md`（artifact 更新の書き分け）
> **参照元**: `gdd-completion-check` Part B Steps 5a / 9b / 9c / 9d、将来的に `gdd-pr-review` の Spec Drift Check

complition gate で実行する個別 checklist は内容が大きく独立性が高い。本 reference に切り出し、completion-check 本体は手順への pointer と判定後の routing に集中する。

## Checklist A: AC Drift Check（reverse direction 検査）

### 適用

`Verification.status=pass` を付ける前に必ず実行する。`gdd-ac-verification` の forward direction（AC → 実装）と組み合わせ、**双方向で drift 無し**を保証する。

### 方向性の違い

- **forward direction** (`gdd-ac-verification` 担当): AC を満たす実装があるか
- **reverse direction** (本 checklist 担当): 実装の挙動が全て artifact に記載されているか

両方向を通って初めて drift 無しと判定できる。

### 手順

1. `git diff <default-branch>...HEAD --name-only` で変更ファイル一覧を取得（default branch は `gdd-using-git-worktrees` で判定済み）
2. 実装 diff の中で**外部観測可能な挙動**の追加を確認:
   - 新規エンドポイント / 新規 HTTP method / 新規レスポンス field
   - 新規 CLI オプション / 新規環境変数
   - 新規 UI 要素 / 新規エラーメッセージ / 新規ログ形式
   - AC に書かれた境界値 / エラーハンドリングと異なる実装
3. 実装にあるが `requirements.md`（AC）・`design.md`・`adr.md` のいずれにも対応記載がない挙動を列挙

### 該当時の routing

| 該当パターン | 対応 |
|---|---|
| 軽微な追加で scope 内（AC の追記で閉じる） | `requirements.md` の AC を更新し、実装との対応を確認してから pass |
| 設計判断として記録すべき（AC には載せないが Why を残したい） | `adr.md` に Context / Decision / Why / Consequences を追記してから pass |
| AC の根本追加 / 削除 / 意味変更を伴う | `human_recheck_required` に昇格（silent に pass にしない） |
| scope 外の無関係な変更 | scope guard として `Next Action=gdd-systematic-debugging` + `implementation_fix_only` で差し戻し |

artifact 更新を伴う場合、updated_by / updated_at を記録して Part B を再実行する。

### Why

`Verification.status=pass` は「AC に対応する検証コマンドが通った」ことだけを保証し、「実装にある挙動すべてが AC で定義されている」ことは保証しない。AC が古いまま実装だけが進んだケース（E2E で追加 fix / subagent の silent な判断変更等）を最終 gate で検出する。

## Checklist B: Stub Detection（Existence ≠ Implementation）

### 適用

AC が pass であっても実装コードがスタブ状態でないかを確認する。

### grep 対象パターン

変更された実装ファイル（テストファイルを除く）に対して以下を grep:

- `return null` / `return None` / `return []` / `return {}` がメインロジックに残っていないか
- `raise NotImplementedError` / `throw new Error("not implemented")` が未削除でないか
- `TODO` / `FIXME` コメントが実装箇所に残っていないか
- 空の関数本体（`pass` のみ / `{}` のみ）が意図せず残っていないか

### 除外

テストファイル・mock ファイル・fixture ファイル内のパターンは除外（意図的なスタブ）。

### 該当時の判定

検出された場合は `status=fail` として扱い、実装の完成を要求する。

「コードが存在する」≠「機能が実装されている」を判定原則とする。

## Checklist C: External Dependency Completeness Check

### 適用

新規スキルやコマンドを追加するタスクで、requirements / SKILL.md に宣言された外部依存が全て実装に反映されているかを確認する。

### 確認対象

- **環境変数**: SKILL.md または requirements.md に記載された env var が実行環境の env 定義（設定ファイル・Terraform の変数・IaC）に追加されているか
- **IAM 権限**: requirements.md に記載された IAM 権限（`sts:AssumeRole`、`secretsmanager:GetSecretValue` 等）が Terraform の IAM policy statement に追加されているか
- **cross-account ロール**: cross-account AssumeRole を使う場合、AssumeRole 先の role ARN が環境変数に設定されており、対象アカウントへ配る IaC のテンプレートが存在するか

### 確認手順（2 段階）

1. `git diff <default-branch>...HEAD -- <env 定義と IaC のパス>` で差分を確認
2. 差分にない場合でも「前のタスクで設定済み」の可能性があるため、宣言された依存が **現在のファイルに既存かどうか** を追加確認（env 定義のキーの有無、IaC での IAM statement の grep 等）

現在のファイルにも存在しない場合のみ `status=fail` とする。

### Why

「SKILL.md は完成したがスキルが実際に動かない」状態が発生した（20260502: ansible-ec2 に cross-account AssumeRole が未実装のまま Done 宣言）。完了宣言前に外部依存の充足を確認し「Done だが機能しない」を防ぐ。

## Checklist D: Skill / Document Quality Check

### 適用

タスクに SKILL.md / ドキュメントの追加・変更が含まれる場合（`git diff --name-only` に `SKILL.md` / `*.md` が含まれる場合）。

### 確認項目

| 観点 | 内容 |
|---|---|
| 記述の一貫性 | 追加した手順・ガードレール・例が、既存の同ファイル内の他セクションと矛盾していないか |
| 具体性 | 「適切に処理する」「必要に応じて確認する」等の曖昧な記述が残っていないか。具体的な条件・コマンド・期待出力に落とされているか |
| Why の記載 | 新規追加した guardrail / check / ルールに「なぜ必要か」が書かれているか（過去のインシデント・失敗事例が根拠になるとなおよい） |
| 重複・矛盾 | 同一ファイル内または関連ファイルに同内容が既にないか。既存ルールと逆のことを言っていないか |

### 該当時の判定

いずれかが不合格なら implementation に差し戻す（`status=fail`）。

### Why

GDD の completion-check PASS 後に bot review（PR 旧#132）で SKILL.md の記述品質について MEDIUM 指摘が出た。「実装 AC を満たすか」の視点だけでは文書品質は検出できず、PR 後のレビューサイクルで発見される。completion-check 内に品質チェックを入れることで、PR 作成前に文書品質問題を閉じられる。

## Checklist E: Completion Stale Classification

completion-check の stale 判定を 3 分類する（正本。数値と Round 契約自体は `references/state-machine.md` § Remediation Loop Safety）。

- **(i) evidence 鮮度**（`gdd-ac-verification` § Fresh Verification Rule へ pointer）: `Verification` の `method=ac:<id>` 行 と `method=security_evidence:<kind>` 行の evidence が前セッション由来である場合**のみ**。
- **(ii) 記録が実態より古いだけ**（自動更新 + advisory）: (a) gate status 行の `updated_by` / `updated_at` の陳腐化、(b) 非 human-approval route の `Route In Progress` 残存。**この 2 経路のみ**。
- **(ii) に分類してよい観測は 3 つに限定する**: `git log` / **本セッションで実行した検証コマンドの出力** / `Completed Tasks` の `Reviewed by:` 行の実在（`Reviewed by: none (Judgment Change: no)` は review の観測に数えない）。この 3 つのいずれかで「記録が古いだけ」を反証できた場合だけ (ii) に落とし、推測・過去セッションの記録・self-report を根拠にしない。human approval を完了条件に持つ route（`human_recheck_required` / `planning_rework_required` / `requirements_amendment`）は 3 観測で完了を証明できないため**常に (iii)**。**`Route In Progress=implementation_fix_only` の残存を (ii) に落とす場合は、`Reviewed by:` 行が当該修正コミット以降に記録されていることまで確認する**（`git log` の修正コミット日時と比較。`Reviewed by:` 行が修正コミットより古ければ、その修正は未レビューであることを意味し観測として使えず、impl-gate 再実行が必要な (iii) とする。`git log` / 検証コマンド出力の単独提示だけで route を自動クリアしない）。
- **(iii) 既定**: 上記以外のすべて。明示的に (iii) 固定として列挙するのは、Step 2 Reviewer Selection Audit / Step 2a Implementation Gate Evidence Check / Step 3 / 3b / Step 4b / 4c / 4c-2 / 4c-3 / 4d / **Step 5a AC Drift Check** / Step 9b / 9c / 9d / Step 11 / Step 13・14 / **`## AC Trace Ledger Gate`**（ただし `ac-ledger.md` か AC の行が無いとき、本セッションの Part B で pass した AC の行を gate が追記して回し直すのは、`skills/gdd-completion-check/SKILL.md` § AC Trace Ledger Gate の例外として同じ Round で続けてよい）/ **`## HITL Outcome Audit`（`unverified` を (ii) に読み替えない）** / **`### Part A-2` Output Consistency Evidence** / **Step 12a Dialectic Review Evidence Check**。
- **分類外**（`Completion Rounds` に数えない）: Step 10 / Part C Step 19 の外部前提不足のみの経路と、Step 13 の reviewer が時間超過・エラーで 2 回とも返らない経路（`references/subagent-dispatch.md` § Reviewer Input and Time Budget。blocker ではなくレビュー不成立として `blocked` で止める）。`Completion Rounds` を +1 するのは差し戻し（`Next Action=gdd-systematic-debugging`）のときだけで、それ以外の停止では数えない。Step 0 の行が `error` で止める経路も分類外。dispatch の前に main が Codebase Health の High で差し戻すとき（`references/subagent-dispatch.md` § Completion-Check の前の機械検査）も、gate と同じく +1 する。
- **Step 5a を (i) にしない理由**: 5a は AC Drift Check（実装 → artifact）で、evidence の再実行では解消しない。`gdd-completion-check` の「AC Drift Check の bypass 禁止」と衝突するため (iii) 固定。
- **カバレッジと表記**: 上記は completion-check 全 blocker 経路に対する割り当てで、将来 Step が増えても (iii) 既定が受け皿になる。行の anchor は Step 番号ではなく**節名 / Step 名**にし、番号 drift で腐らないようにする。

### Completion Rounds / Completion Baseline の操作手順

`gdd-completion-check` が実行する。保存先は **`tasklist.md`**（Tier 3。field 定義は `references/state-field-tiers.md`）。上限値・fail-closed 条件・escalation 先は `references/state-machine.md` § Remediation Loop Safety が正本で、ここには再掲しない。

1. **Round 開始時**: `tasklist.md` に `Completion Baseline: <HEAD の commit sha>` を記録する（既に行があれば上書きしない）。`Completion Rounds` 行が無ければ `Completion Rounds: 0` を追加する。ただし `Completion Baseline` が既に存在する場合は初回ではないため `Completion Rounds: 0` を追加せず、手順 6 の fail-closed（上限超過と同じ扱い）に従う
2. **blocker を出して差し戻すとき**: `Completion Rounds` を **+1** して `tasklist.md` に書き戻す。同時に `Completion Baseline` を、この Round の再検証に使った `HEAD`（＝これから修正が入る直前の commit sha）へ更新する（上書きする）。上限超過時の書込 field は state-machine 側の規定に従い、方式転換の選択肢と 4 つ目を置ける条件は `references/rollback-patterns.md` § gdd-completion-check の Round 上限超過 に従う
3. **`Next Action=done` に到達したとき**: `Completion Rounds` / `Completion Baseline` / `Completion Reviewed Through` の 3 行を削除する。route reset / `human_recheck_required` と、planning 差し戻し後の tasklist の作り直しでは削除もリセットもしない
4. **2 回目以降の Round の再検証範囲**: Step 13 で `gdd-completion-reviewer` の出力（finding の一覧）が返った Round を差し戻すとき（`Next Action=gdd-systematic-debugging`。Round 上限超過で `human_recheck_required` を併せて書くときを含む）は、差し戻しの書き込み（`Completion Rounds` の +1・`Next Action`・handoff）を終えた後の最後に、Step 13 で reviewer を起動する直前の `HEAD`（`git rev-parse HEAD`）を `tasklist.md` の `Completion Reviewed Through: <sha>` に書く（行があれば上書きする）。差し戻し以外の出口（Step 19 の停止・Step 14 の `human_recheck_required` への戻し・done・cancelled）、reviewer が時間超過・エラーで返らないとき、Step 13 より前で止まった Round、書き込みを終える前に止まったときは書かない。次の Round は `git diff <Completion Reviewed Through>...HEAD`（＝Step 13 が最後に見た後の変更すべて）とその影響範囲だけを再検証する。この diff はコミット間の差分のみで staged/unstaged/untracked を含まないため、**再検証の直前に blocker 修正を commit すること**が前提（commit できない事情がある場合は手順 6 の全量再検証に倒す）。`Completion Reviewed Through` より前の**通過済み箇所への新規指摘は advisory** とし、新情報の根拠を示せる場合だけ blocking へ昇格する。**Why（起点を `Completion Baseline` にしない理由）**: Baseline は差し戻しのたびに進むので、Step 13 より前（Part A・B）で差し戻した Round の後は、Step 13 が一度も見ていない前の Round の修正が起点より前に入り、差分スコープで素通りする。起点を Step 13 が実際に見た `HEAD` に置けば、どこで差し戻しても、見ていない変更はすべて diff に入る。`Completion Baseline` は Round 数の fail-closed（手順 1・6）のためだけに使う
5. **毎ラウンド全量（差分スコープの例外 4 件）**: 前ラウンド未解消 blocker（diff 外でも blocking 維持）/ `## AC Trace Ledger Gate` / Step 2a Implementation Gate Evidence Check / Part B の required external security evidence 判定（Step 8 / Step 10）
6. **`Completion Reviewed Through` の欠落・解決不能 sha・`HEAD` の祖先でない（`git merge-base --is-ancestor <Completion Reviewed Through> HEAD` が偽。reset・rebase で commit が落ちたとき）、または再検証時に `git diff <Completion Reviewed Through>...HEAD` が空**: 差分を信頼せず**全量再検証**（fail-closed）。Step 13 がまだ判定を返していないとき（差し戻しがすべて Step 13 より前だった、Step 13 が時間超過で返らなかった、Step 10 で止まった）は欠落に当たり、`Completion Baseline` や `Completion Rounds` があっても差分スコープにしない。`Completion Baseline` があるのに `Completion Rounds` が読めない場合は「初回」と解釈しない（state-machine 側の fail-closed 規定）

### Step 4b: 複数 blocker 同時発生時の合成 Next Action ルール（優先順位）

1. **Reviewer Lineage 未反映** blocker がある → `Next Action=gdd-implementation-gating`（対象 task を該当 reviewer で再 gate にかける）。`Route In Progress=implementation_fix_only` を併記
2. **Reviewer Lineage は反映済みだが ADR 未起票** blocker のみ → `Next Action=gdd-completion-check` のまま停止し、`adr.md` への直接追記を要求
3. **Routing 提案との不整合**（`human-check-waiting` 提案だったが human check 未通過）→ `Next Action=human-check-waiting`、`Human Check Status=pending` に戻す
4. 複数該当する場合は **より上流の gate に戻す方を優先**（impl-gate ＞ completion-check ＞ human-check）。理由: 上流再 gate の過程で下流 blocker も同 reviewer 観点で自然に解消される順序になるため

**Why（合成ルールの必要性）**: blocker が単独発生時は SKILL.md の規定で `Next Action` が一意に決まるが、複数 blocker 同時発生時は合成判断が必要。「ADR 未起票」だけなら `gdd-completion-check` 停止で `adr.md` を書けば済むが、Reviewer Lineage も未反映なら先に impl-gate 再走を通さないと security reviewer の観点で ADR 内容が不足する。よって上流優先で合成する。

**Why（蓄積記録の確認自体）**: AC Drift Check は forward direction（artifact → 実装）と reverse direction（実装 → artifact）の双方向検査だが、build loop 中に発生した spec change がどこまで波及したかの「期待値」を持っていなかった。SMI / Impact Block は build loop 中に「これこれの変更があったので ADR を起票し Lineage を追加した」と宣言する記録であり、completion-check はその宣言と現実の整合を機械的に確認できる。superpowers の standalone completion とは異なり、build 履歴を state machine が追跡しているからこそ可能な検査。

## completion-check での実行順序

Part B 内で以下の順序で実行する（`Checklist E` は実行順序を持たない**分類 reference**兼操作手順であり、A〜D と違って以下の並びに位置を持たない）:

1. `Verification` から required evidence を読み取る（Step 5）
2. **Checklist A (AC Drift)** を実行（Step 5a）
3. AC 検証行を埋める（Steps 6-9）
4. **Checklist B (Stub Detection)** を実行（Step 9b）
5. **Checklist C (External Dependency)** を実行（Step 9c）
6. **Checklist D (Skill Quality)** を実行（Step 9d）
7. external security evidence 確認（Step 10-11）

各 checklist は独立しており、いずれかで `status=fail` が出たら早期 return せず最後まで実行して全件報告する。

## 各 skill の SKILL.md での参照方法

```markdown
# 例: completion-check 内
5a. **AC Drift Check**: `references/gate-checklists.md` § Checklist A を実行する。
    - reverse direction 検査として実装 → artifact 整合を確認
    - 該当時の routing は同 reference の routing 表に従う
```

inline で長文を再記載せず、reference を信頼する。

## Why（このパターンの根拠）

- completion-check の checklist 群（5a / 9b / 9c / 9d）はそれぞれが独立した手順・判定基準を持つ
- 同 skill 内で 100+ 行を占有しており、checklist 内容の更新時に completion-check の流れを見失いやすい
- reference 化により completion-check 本体は「checklist を実行 + routing 判断」に集中できる
- 将来的に `gdd-pr-review` の Spec Drift Check が同じ checklist を呼びたい場合の再利用基盤になる
