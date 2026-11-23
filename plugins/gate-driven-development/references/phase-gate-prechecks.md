# Phase Gate Pre-check Templates

> **所有**: 各 gate skill が開始前に実行する Phase Gate Pre-check の標準テンプレート
> **上位正本**: `state-machine.md`（field の意味）、`state-field-tiers.md`（field の Tier 分類）、`task-sizing.md`（Task Size の判定）
> **参照元**: `gdd-implementation-gating` / `gdd-completion-check` 他、Pre-check を要する skill

formal gate skill は開始前に「active steering が正しい phase に到達しているか」を verify する。各 skill が同じ check を inline で繰り返さないよう、本 reference を pointer 参照する。

Machine-readable constraints are synchronized with `references/state-schema.json`. Express paths also enter build phase with `Human Check Status=approved`; never write a non-schema status.

機械可読な最小条件は `references/state-schema.json` § `prechecks.build_phase` と同期する。文書を更新したら schema と contract test も更新する。

## Common Pre-check Procedure

すべての gate skill で共通する 4 step:

1. **state.md の存在確認**: `.steering/<task>/state.md` が存在しなければ fail-closed で停止し、`/gdd-dev` 経由での正規フロー開始を案内する
2. **Task Size の取得**: `state.md` から `Task Size` フィールドを読み、後続の condition 分岐に使う（先頭セグメントの切り出し・trim・完全一致は `references/state-machine.md` § state field のフォーマット検証に従うが、列挙外の値は Template A/B のとおり standard 扱いにフォールバックし、同節の fail-closed 停止の対象ではない。`quick (express → standard)` は `quick (express)` と別値であり、`commands/gdd-dev.md` STEP 2 の Template 分岐は前者を後者と部分一致させない。各 commands・skill・reference が散文で書く「Express パス」「Express」は、この完全一致判定に従い `quick (express)` だけを指す。`quick (express → standard)` を含まない）
3. **Last Handoff Summary の更新**: phase を抜けるとき、`state.md` の `Last Handoff Summary` に「どこまで進み、次に何をするか」を 1 行で上書きする
4. **Model Tier の照合**（advisory・fail-closed にしない）: formal gate skill では、現在の実行モデルを `references/fixed-models.md` の該当 tier 推奨と照合する。推奨より軽いモデル（例: formal gate をセッションモデル `sonnet` のまま実行）の場合、乖離と影響（レビュー・判断の検出力低下）を明示して 1 回だけユーザー確認を取り、選択結果を `Last Handoff Summary` に 1 語（例: `model-ack:sonnet`）含める。既に `model-ack:` が記録済みの workflow では再確認しない。背景: 2026-08-22 の実測で、formal 工程一式がユーザーのセッションモデル指定（Sonnet）のまま進行し、乖離がどこにも表面化しなかった

`/gdd-dev` 経由でなく直接起動された場合でも Pre-check は省略しない。

### なぜ Last Handoff Summary を毎 phase 書くか

hook が会話に戻せるのは `state.md` の routing field と context field だけで、会話内容は戻せない（hook は会話にアクセスできない）。compaction の直後に hook は何も注入せず、PreCompact が要約器に渡すのは state.md の場所と `Resume From`・`Next Action` だけである。context field は、次のユーザー入力で UserPromptSubmit が注入する。PreCompact と UserPromptSubmit は、local state の session が現在の session と違う（または空）ときは何も渡さず、local state が無いときと、現在の session id が取れない runtime では照合せずに渡す。SessionStart は、local state の session が現在の session と一致したとき、または現在の session id が取れず、local state に session が無いか `human-check-waiting` のときに、Quick Reboot に `Last Handoff Summary` を入れる（local state が無いときと、ブランチが steering と合わないときは入れない）。`Last Handoff Summary` は「何をしていたか」を戻せる唯一の context source であり、これが空だと compaction や別セッションの後に phase だけ正しく作業内容が失われる。

Tier 3 field なので**不在でも fail-closed しない**。ただし build 中は plan-reread hook（PreToolUse）が未記入を検出して注入文で促す。

## Template A: 3-Gate Approval Required（impl-gate 等の build phase 用）

`gdd-implementation-gating` / `gdd-task-breakdown` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` などが使う。

| Task Size | 必須フィールド |
|---|---|
| `standard` / `quick (standard)` / `quick (express → standard)` | `Requirements Review Status = approved` + `Design Review Status = approved` + `Human Check Status = approved`（列挙外の値も standard 扱いにフォールバックする。`state-schema.json` の `prechecks.build_phase_default`） |
| `quick (express)` | 上と同じ 3 つ（`Design Review Status` は requirements-gating が同じ evidence で `approved` にする。`references/requirements-gating-steps.md` § Express） |
| `trivial` | この skill に到達しないはず（routing 誤り） |

いずれかが未満の場合、戻るべき phase を提示して fail-closed 停止:

- `Human Check Status` 未承認 → `human-check-waiting` に戻る
- `Requirements Review Status` 未承認 → `gdd-requirements-gating` に戻る
- `Design Review Status` 未承認 → `gdd-design-gating` に戻る（express は `gdd-requirements-gating`）

### impl-gate 固有追加 check

`gdd-implementation-gating` のみ:

- `tasklist.md` の `Implementation Reviewer Selection` セクションが存在し、少なくとも `gdd-implementation-reviewer` が `selected` または `in_review` であること
- 欠落時は `gdd-task-breakdown` で初期枠が未作成 → task-breakdown からやり直す

### task-breakdown 固有追加 check

`gdd-task-breakdown` のみ:

- Express パスではこの skill に到達しない。`Task Size` が `quick (express)` の場合は fail-closed で停止し、Express フローの誤 routing として報告する
- standard / quick (standard) 系（`quick (express → standard)` を含む）のみ Template A の 3-gate approval check を適用する

## Template B: Task-Size Aware Skip（completion-check 用）

`gdd-completion-check` 用。Task Size に応じて skill 自体の実行可否が変わる:

- **`quick (express)`**: Express パスでは completion-check を実施しない（`impl-gate → done` で直行するため、この skill に到達すること自体が routing ミス）。`Next Action=done` に修正し、Post-Completion PR Flow だけを実行して `<gdd-stop reason="done">` で終了する。Part A 以降の Steps は実行しない
- **`standard` / `quick (standard)` / `quick (express → standard)`**: Template A の 3-gate approval check を通したうえで通常の Steps を実行する（列挙外の値も standard 扱いにフォールバックする）
- **`trivial`**: completion-check に到達しないはず

## 各 skill の SKILL.md での参照方法

各 gate skill の `## Phase Gate Pre-check` セクションは Template への pointer を 3-5 行で示す形にする:

```markdown
## Phase Gate Pre-check（必須）

`references/phase-gate-prechecks.md` § Template A を実行する（Task Size 別の必須フィールド検査 + 戻り先 phase 提示）。

**この skill 固有の追加 check**:
- `tasklist.md` の `Implementation Reviewer Selection` に `gdd-implementation-reviewer` が `selected` / `in_review` であること
```

skill 固有の差分（追加 check）だけを inline で残し、共通部分は本 reference を信頼する。

## Why（このパターンの根拠）

- 同じ 3-field gate check を 3+ skill が inline で記載しており、許容値 / 戻り先の更新時に複数箇所を同期する必要があった
- `state-field-tiers.md` で field の Tier 分類を切り出したのと同じ理由で、Pre-check 手順も SSOT 化する
- `state-field-tiers.md` が「field の Tier 表」、`gate-status-schema.md` が「許容値と更新フォーマット」、本 reference が「Pre-check の手順」と役割分担する（Template A/B の default フォールバックは precheck 側では新設だが、`hooks/scripts/run-pre-push-gate-hook.sh` / `run-pre-pr-gate-hook.sh` / `validate-steering-write.py` が既に未知の `Task Size` を standard 扱いにしている既存挙動に precheck 側を揃えたもの）
