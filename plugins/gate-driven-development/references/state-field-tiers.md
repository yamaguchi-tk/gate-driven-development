# State Field Tiers

> **所有**: `state.md` / `tasklist.md` の各 field を **Tier 別に分類**し、phase ごとの必須最小集合を明確化する正本
> **上位正本**: `gate-status-schema.md`（許容値・更新フォーマット）、`state-machine.md`（状態遷移）
> **参照元**: 各 skill の `Phase Gate Pre-check` セクション、SessionStart / PreToolUse hook

`state.md` には 13+ field があり、すべてを常時揃える運用は重い。実際には field によって「いつ必要か」が異なる。この reference は field を **3 Tier** に分類し、phase ごとの **Minimum Required Set** を提示する。

**重要**: この分類は運用ガイドラインで、**既存 hook の必須 field 制約は変更しない**。Hooks は引き続き Core Tier の不在で fail-closed する。

## Lightweight State Policy

`state.md` は **routing source** であり、長い監査ログではない。phase 再開に必要な Tier 1 と、その phase に入るために必要な Tier 2 だけを優先して読む。Reviewer Lineage、Fix Attempts、Handoff Summary の履歴、長い判断理由、scenario / eval の詳細は `worklog.md`、`adr.md`、または dedicated appendix に移す。

- routing source: `Resume From` / `Next Action` / `Human Check Status` / `Route In Progress`
- context source: `Approved Direction` / `Stage Continuity` / `Last Handoff Summary`
- audit source: `worklog.md` / `adr.md` / appendix（state.md からは参照リンクだけでよい）
- サイズ上限で `worklog.md` へ移すとき: field の現在値の行（上の routing source と、gate が読む `Task Size`・`ADR distilled`・Self Review・`Independent Review` など）は全部残し、置き換わった古い値と、上の段落で移すとした履歴（Reviewer Lineage・Fix Attempts など）の行だけを、書き換えずにそのまま移す（追記のみ。要約しない）。`tasklist.md` の `Next Action` と、完了タスクごとの見出し・AC の対応・`Reviewed by:`・結論も残す。移す前と後に `scripts/check-gate-ledger.sh --steering <その steering>` を走らせて出力を比べ、移す前の ok の行が移した後に無いか、移した後にだけ missing / invalid / n/a の行が現れたら、移した行をそのまま戻す（移す前から欠けていた行を直す手順ではない。ここまでの正本の文言: `hooks/scripts/lib/steering_size.py` の `SIZE_DENY_SUFFIX`）。完了タスクの `Reviewed by:` を落とす `tasklist.md` の書き込み（丸ごと消す・要約で見出しを崩す・`## Current Task`・`## Pending Tasks` 以外の節へ移す場合を含む）は、steering write guard が書き込みの時点で止める（category `completed_reviewed_by`）。止めるのは Write・Edit・MultiEdit だけで、ApplyPatch と Bash の書き込みは見ず、3 回続けて止められると警告付きで通る。この guard があっても、移す前と後の検算は省かない
- **廃止した hook の印（Tier 分類の対象外）**: `Status` / `CompactSessionId` / `CompactSource` / `AutoCycleCount` / `PausedAt` / `CompactTranscriptOffset` — compact 自動復帰（2026-09-28 に廃止）の印。hook は書きも読みもしない。既存の state.md に残っていても害は無く、消してもよい。skill / LLM は書かない。正本は `gate-status-schema.md` § `Status`

禁止:
- Tier 3 の audit field を全 phase の必須条件にしない
- `Approved Direction` や `Last Handoff Summary` を `Resume From` / `Next Action` の代わりに routing source として扱わない
- state を短くするために audit data を捨てない。移動先 artifact を明示する

## Tier 1: Core（active steering の必須最小集合）

active steering である限り、phase に関わらず**常に**揃える。Hook（PreToolUse `validate-steering-write.py` / SessionStart / UserPromptSubmit `detect-steering.sh`）がこれらの不在を検出した時点で fail-closed する。

検査箇所は行番号でなく関数名で示す（行番号はドリフトするため）。

| Field | Hook 検査箇所 | 検査モード |
|---|---|---|
| `Started At` | `validate-steering-write.py:state_requires_started_at` | **transitive**: 他の Tier 1 field が write chunk に含まれるときだけ deny する。active state.md には常に書く |
| `Resume From` | write: `validate-steering-write.py:collect_state_core_field_violations` / read: `detect-steering.sh:gdd_validate_active_state_fields` | **always required** |
| `Human Check Status` | 同上 | **always required** |
| `Route In Progress` | 同上 | **always required** |
| `Next Action` | `detect-steering.sh:gdd_validate_active_state_fields` | **conditional**: `Requirements / Design / Human Check Review Status` すべて `approved` になった canonical tasklist phase 以降で必須 |

write 側の検査は「既存ファイル内容 + 書き込み chunk」に対して行う。chunk だけを見ると、Edit で 1 field ずつ更新する通常運用では充足が検査される瞬間が来ないため。routing field をまったく含まない書き込み（別セクションの追記など）は対象外。

これらは **5 field** で、いずれも 1 行で表現できる。trivial / express task でもこの 5 field は揃える。

**Hook の field 名は `hooks/scripts/validate-steering-write.py:STATE_REQUIRED_FIELDS` と `hooks/scripts/lib/detect-steering.sh:gdd_validate_active_state_fields` の 2 箇所にハードコードされている**。本 reference を変更する場合は両方の hook 側も同期する。逆も同じ。

## Tier 2: Phase-Specific（その phase に入ったときに必須）

phase 遷移で初めて登場する。**遷移前は空 / 未設定でよい**。遷移と同時に正しい値を書き込む。

| Field | 必須になる phase | 不要になる timing |
|---|---|---|
| `Requirements Review Status` | `gdd-requirements-gating` 着手時 | task 完了後も保持（audit） |
| `Design Review Status` | `gdd-design-gating` 着手時 | task 完了後も保持（audit） |
| `Approved Direction` | human check `approved` 直後 | 上書きされるまで保持 |
| `Planning Reviewer Selection` | `gdd-requirements-gating` 着手時 | task 完了後も保持 |
| `Implementation Reviewer Selection` | `gdd-implementation-gating` 着手時 | next task 移行時にリセット |
| `Refactor Gate Status` | 全 task 完了 + standard path | Express path では使わない |
| `Operation Level` | brainstorming 確定時 | task 完了まで保持 |

**Express path** では `Refactor Gate Status` を使わない。`Requirements Review Status` / `Design Review Status` は使う（requirements-gating が書く。design.md が無いので Design は Requirements と同じ evidence で `approved`）。

## Tier 3: Audit / Context（条件付きで現れる）

特定条件下でのみ書き込む。**通常は不在でよい**。Hook も不在を許容する。

| Field | 書き込み条件 | クリア条件 |
|---|---|---|
| `Last Handoff Summary` | phase 遷移ごとに上書き | 上書きされるまで保持 |
| `Decision Retake`・`Decision Handoff` | `references/independent-review.md` の (3-f) で、取り直しを始めるとき（`Decision Retake`）と、後続の test の要件を Issue に写したとき（`Decision Handoff`）。書式は同項 | PR 単位で保持し、worklog へ移さない（`Decision Retake` の行があれば取り直しは使用済み。`Decision Handoff` の語があれば pre-PR gate は `ADR distilled: not_applicable` を実行後に通知する） |
| `Blocked Since` | `gdd-completion-check` が `blocked` 停止 | blocker 解消で削除 |
| `batch_paused_for_hotfix` | `batch_mixed` で Hotfix Lane 明示 | Hotfix 完了で `false` |
| `Bounce Log` | rollback pattern 適用時 | append-only |
| `Stacked Base` | Stage Continuation の stacked 継続時 | 先行 Stage ID / head branch / tip SHA / `baseRefName`。Pre-Flight と cleanup 判定が読むため落とさない |
| `Fix Attempts` | `gdd-systematic-debugging` で remediation | task 完了でリセット |
| `Gate Rounds` | `gdd-implementation-gating` が `changes_requested` を出すたびに +1（`remediation_loop` 判定。正本 `references/fixed-models.md`） | task `approved` で削除。`human_recheck_required` では reset しない（planning 差し戻し後の tasklist の作り直しでは、task と一緒に消える） |
| `Fix Findings`（保存先 `tasklist.md` の task のブロック） | 差し戻しのたびに、その回の finding で書き直す（前の行は残さない）。書くのは、completion-check の差し戻しでは `gdd-completion-check`（再オープン・作成した task のすべて。`Pending Tasks` に置いたものも含む）、それ以外（impl-gate・PR 後のレビューなど）では `gdd-systematic-debugging`（route によらない。ただし Hotfix Lane に回す route では元の steering に書かず、`worklog.md` の `## Hotfix Findings` と新しい steering の `## Origin Findings` を経て、新しい steering の `gdd-task-breakdown`（express では `gdd-test-driven-development` Step 1）が書く。`## Hotfix Findings` は `gdd-pr-review-followup` も書く。書く task が `Completed Tasks` にしか無ければ、同じ steering で直す route なら書く前に再オープンする。手順は `references/state-machine.md` § tasklist.md の canonical state）。形は `Fix Findings:` の下に 1 件 1 行で `- <出所（finding を出した gate・レビューの名前）> \| <severity> \| <file:line。無ければ なし（AC-<n> など、指摘の対象）> \| <要約>`。Gate Batch では finding の対象の task ごとに書き、対象の task を決められない finding は batch の全 task に書く。読むのは `gdd-test-driven-development` Step 1 だけ | task `approved` で削除（`gdd-implementation-gating` Step 11 で `Completed Tasks` に移すとき）。planning 差し戻しの作り直しでは消さず、作り直した task に写す（`references/state-machine.md` § planning 差し戻し後の tasklist.md リセット） |
| `Completion Rounds`（保存先 `tasklist.md`） | `gdd-completion-check` が blocker を出して差し戻すたびに +1（Round 上限は `references/state-machine.md` § Remediation Loop Safety が正本） | `Next Action=done` 到達時に削除 |
| `Completion Baseline`（保存先 `tasklist.md`） | `gdd-completion-check` の**初回** Round 開始時に `HEAD` を 1 度だけ記録（既に行があれば上書きしない）。以降は blocker を出して差し戻すたびに、その Round が使った `HEAD` へ更新する（手順は `references/gate-checklists.md` § Checklist E） | `Next Action=done` 到達時に削除 |
| `Completion Reviewed Through`（保存先 `tasklist.md`） | `gdd-completion-check` の Step 13 で `gdd-completion-reviewer` の出力が返った Round を差し戻すとき（Round 上限超過を含む）に、差し戻しの書き込みを終えた後に Step 13 で reviewer を起動する直前の `HEAD` で上書き（時間超過・エラーで返らないとき、書き込みを終える前に止まったときは書かない）。2 回目以降の Round の差分の起点（手順は `references/gate-checklists.md` § Checklist E） | `Next Action=done` 到達時に削除 |
| `Cumulative Changed Files` | implementation 進行中の audit | task 完了で保持 |
| `Parallel Investigation Rounds` | `parallel-failure-investigation` 実行時 | append-only |
| `Superseded By` / `Superseded Steerings` | supersede 検出時 | 上書きされない |
| `Reviewer Lineage` | brainstorming で supersede / hotfix / amendment 関係を検出時 | append-only（過去判定を変更しない、新 steering を追記） |
| `## Advisory Findings (Impl-Gate)`（見出しセクション） | impl-gate か completion-check が High・実害クラス以外の medium / low を検出した時（Task Size によらない。`gdd-implementation-gating` Step 13、`gdd-completion-check` 手順 13） | PR 本文の残した問題の欄（`指摘止まり（` で始まる行）へ搬送後も削除しない（audit）。`references/post-completion-pr-flow.md`（`gdd-completion-check` から参照）が読み出す唯一の搬送元。旧見出し `## Advisory Findings (Express Impl-Gate)` の節が残っていれば、それも合わせて読む（書き込みは新しい見出しだけ） |
| `Pre-PR Self Review` | `gh pr create` 前のセルフレビュー収束時（発火条件と Task Size 分岐は本 reference では定義しない。正本は `references/self-review-lanes.md`） | 上書きされるまで保持（監査） |
| `Pre-Push Self Review` | `git push` 前のセルフレビュー時（発火条件と Task Size 分岐は本 reference では定義しない。正本は `references/self-review-lanes.md`） | 上書きされるまで保持（監査） |
| `PR Review Follow-up Attempts` | `gdd-pr-review-followup` の polling 周回時（既存 field。Tier 表に未記載だったため本行で補記） | リセット契約なし（単調増加のカウンタ）。上限に達したとき、または state.md を通常のファイルとして読めないときは、stop hook が `blocked` を強制する。上限値の正本は `hooks/scripts/lib/constants.py` の `PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS` |
| `PR Review Rounds` | `gdd-pr-review-followup` の Step 1（新しい head sha のレビュー結果を収集するたびに +1。同一 sha の再レビュー・CI 再実行・polling wake では加算しない）。PR 作成時に 0 で初期化（初期化の時点と条件は followup SKILL の `PR Review Rounds` field 行） | PR 単位で生存し、リセットしない（checkpoint (1) を選んでも 0 に戻さない）。上限到達で checkpoint を強制発火（`blocked` にしない）。正本: `skills/gdd-pr-review-followup/SKILL.md` § Design Review Checkpoint、上限値は `hooks/scripts/lib/constants.py` の `PR_REVIEW_ROUNDS_MAX` |
| `PR URL` | `gh pr create` 後、merge gate（`gh pr merge`）の入力として必須（従来「推奨」からの格上げ） | 上書きされるまで保持（監査） |
| `Last Review Push At` / `Pre-Merge Review Recheck` / `Bot Review Received` / `Independent Review` | それぞれ: PR head を更新する push のたび（初回 push を含む） / マージ直前の再 fetch 直後 / Review Pending Loop の fresh 取得ごと / 独立レビュー lane（実装文脈を渡さない独立実行。手順の正本は `references/independent-review.md`、model は `references/fixed-models.md` の `independent_review` tier）の完了時 | 上書きされるまで保持 |
| `Medium Disposition` | `Independent Review` の `medium` が 1 件以上のとき、同じタイミングで記録する（書き手は `Independent Review` と同じ `gdd-pr-review-followup`。書式の正本: `references/self-review-lanes.md` § merge gate 証跡） | 上書きされるまで保持 |
| `Merge Approval` | 人間が明示ワードでマージを承認したターン（その場で記録。後追いでまとめて書かない）。自走のマージの条件（`references/post-merge-qa.md` 手順 2）で代えるときはマージの直前 | 上書きされるまで保持（監査） |
| `Origin Session`（write-once） | steering 作成時に一度だけ、起動元セッションが記録（GDD 自身は書かない。`references/phase-progression.md` § Cross-Session Messaging） | 書き換え禁止（`hooks/scripts/validate-steering-write.py` が、書込み後の値が既存値と変わる書込を deny。行の**削除**・空値化も含む。ApplyPatch は当てた後の値を推定せず、`state.md` を移動先にする patch と、patch・今の `state.md` のどちらかに field の語がある patch を、初回でも deny する。Bash の書き込みは見ない）。値が無い/変更が必要な場合は通知を skip する |
| `Created In Session` | brainstorming の手順 5 で `state.md` を作る書き込み（値は Bash の `printenv CLAUDE_CODE_SESSION_ID`。取れなければ書かない） | 書き換えない（再開では書かない）。`hooks/scripts/lib/request_capture.py` が payload の session_id と照合し、一致するときだけ依頼の原文を写す。guard では守らない |
| `Origin Notification` | `human-check-waiting` 到達時の起動元への通知送信結果。成功時 `sent (<HITL 到達の timestamp>)`、tool 不在・送信失敗時 `unavailable (<理由>)` | HITL 到達ごとに上書き（timestamp が到達を識別する。同じ timestamp なら再送せず、別の到達では新たに送る） |

`## Advisory Findings (Impl-Gate)` の行フォーマット:

```
- `<task-id>`: <finding 要約> | severity: <medium|low> | evidence: <impl-gate review run id> | recorded_at: <ISO 8601 timestamp>
```

記録が 0 件の場合はこの節自体を state.md に書かない（存在しない = advisory findings なし、の意味）。これは既存の「advisory review lane」（`references/state-machine.md` の `gdd-requesting-code-review` companion review 用語）とは無関係の別概念。

## Phase 別 Minimum Required Set

phase ごとに「最低限揃っていれば routing できる」field の組み合わせを示す。Hook の fail-closed 判定はこの表を基準にする。

### `pre-brainstorming`（`/gdd-dev` 受付直後）
- `Started At` のみ
- 他の Tier 1 field は brainstorming 着手後に揃える

### `gdd-brainstorming` 進行中
- Core 5 のうち `Started At` / `Resume From` / `Route In Progress=none`
- `Human Check Status=pending` / `Next Action` は brainstorming 末尾で書き込む

### `gdd-requirements-gating` / `gdd-design-gating`（standard / quick standard）
- Core 5 すべて
- Tier 2: `Requirements Review Status` / `Design Review Status` / `Planning Reviewer Selection`
- Tier 3: 任意

### `human-check-waiting`
- Core 5 すべて
- Tier 2: `Requirements Review Status=approved` / `Design Review Status=approved`（standard / quick standard / express）
- `Approved Direction` は **不在**（approved 後に書き込まれる）

### `gdd-task-breakdown` 〜 `gdd-implementation-gating`（build phase）
- Core 5 すべて
- Tier 2: 3 phase status すべて `approved`（express を含む） + `Approved Direction` + `Implementation Reviewer Selection`
- Tier 3: `Fix Attempts` / `Cumulative Changed Files` 等は remediation / audit 時に追記

### `gdd-completion-check`
- Core 5 すべて
- Tier 2: 全 phase status `approved`
- Tier 3: `Refactor Gate Status`（standard のみ）/ `Last Handoff Summary`

### `done` / `cancelled`

- Core 5 のうち `Resume From=done|cancelled` / `Next Action=done|cancelled`
- 他は保持（audit trail）

## Lightweight Template（Express / trivial 用）

express / trivial 開始時の最小 `state.md` は以下:

```markdown
---
Started At: <ISO 8601>
Created In Session: <printenv CLAUDE_CODE_SESSION_ID の値。取れなければ行ごと書かない>
Task Size: quick (express)
---

# State

Resume From: gdd-brainstorming
Requirements Review Status: pending
Design Review Status: pending
Human Check Status: pending
Route In Progress: none
Next Action: gdd-brainstorming
```

**Tier 1 + Task Size** と、express が requirements-gating で使う `Requirements Review Status` / `Design Review Status`。ほかの Tier 2 / Tier 3 は phase 遷移で必要になったときに追記する。trivial では Task Size を `trivial` に変え、この 2 行を書かない。

## Standard / quick standard Template

```markdown
---
Started At: <ISO 8601>
Created In Session: <printenv CLAUDE_CODE_SESSION_ID の値。取れなければ行ごと書かない>
Task Size: <quick (standard) | standard>
Operation Level: standard
---

# State

Resume From: gdd-brainstorming
Human Check Status: pending
Route In Progress: none
Next Action: gdd-brainstorming

Requirements Review Status: pending
Design Review Status: pending
Planning Reviewer Selection: pending
```

Tier 1 + Tier 2 の planning 着手前最小集合。`Approved Direction` / `Implementation Reviewer Selection` は phase 遷移で追記する。

## なぜ Tier 化するか（Why）

- 13+ field を **常時揃えようとすると**、phase ごとに不要な field が散乱し、state.md の drift / parse 失敗の原因になる
- 過去にも「`Last Handoff Summary` の空文字 vs field 欠落 vs sentinel」の挙動を区別する fail-safe 契約を導入した経緯がある（`state-machine.md` § Last Handoff Summary 参照）
- Tier 1 だけが Hook の fail-closed 対象。Tier 2 / 3 は phase が必要とした時点で着く
- 既存 hook の必須制約（`Started At` / `Resume From` / `Human Check Status` / `Route In Progress` / `Next Action`）はすべて Tier 1 に含まれており、**この分類は hook の挙動を変更しない**

## 移行ガイド（既存 steering に対する後方互換）

- 既存の active steering は変更不要。すべての field が揃っている状態は Tier 化後も valid
- 新規 steering（特に express / trivial）から Lightweight Template を採用してよい
- Hook 側は引き続き Tier 1 のみを fail-closed の判定対象とする。`Approved Direction` 等の Tier 2 field 不在で fail-closed しない
- Tier 2 / 3 を後から追記する skill 側は、追記時に `gate-status-schema.md` の更新フォーマット（status / evidence / updated_by / updated_at）を守る
