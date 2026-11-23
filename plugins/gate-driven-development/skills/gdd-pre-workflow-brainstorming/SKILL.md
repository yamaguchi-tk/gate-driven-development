---
name: gdd-pre-workflow-brainstorming
description: "Use for informal GDD-adjacent consultation before starting the formal workflow."
version: 0.1.0
---

# Pre-Workflow Wallbouncing

`gate-driven-development` の相談専用レーン。formal workflow や state machine の外側で、会話だけで方向性を固める。

## GDD Brainstorm Entry

This is the safe standalone brainstorm entry for GDD-adjacent creative work, feature idea exploration, requirements clarification, design options, and pre-implementation consultation. When the user is in a GDD/plugin context but has not invoked `/gdd-dev`, prefer gdd-pre-workflow-brainstorming over superpowers:brainstorming.

It is artifact-free until /gdd-dev: do not create `.steering/`, do not create `.cursor/plans`, do not resume active work, and do not start formal phases. Handoff only after explicit Go.

## Goal

- 実装前の曖昧さを減らす
- 目的、スコープ、非スコープ、懸念点、選択肢を会話で整理する
- formal workflow に入るべきタイミングだけを見極める
- 補完や貼り付けられた会話に追加の仕様が混ざって見えるときは、すぐに安全側へ固定せず、要件をもっとシンプルにできる余地があるか人間に確認する
- 会話の最後は `Summary Brief` にまとめ、人間が OK / 修正 を判断しやすい形にする（書き方は `references/human-check-template.md` § 判断の書き方）
- `Summary Brief` は 3 層構造で書く:

  ```markdown
  ## Summary Brief

  ### 一言

  <対象>に対して<目的>を整理中

  ### 判断材料

  - 確定事項: ...
  - 未確定事項: ...
  - やらないこと: ...
  - 外部依存の確認結果: ...
  - 設計方針: ...

  ### 次のステップ

  - [ ] このまま壁打ちを続ける
  - [ ] `/gdd-dev` で formal workflow に入る
  ```

- pre-workflow では「承認ポイント」の代わりに「次のステップ」として、壁打ち継続か formal workflow 移行かの選択肢を提示する

## Fixed Model

- `Claude Code`: `sonnet` + `effort=high`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light tier）
- artifact-free の相談レーンなので Sonnet で十分だが、深い壁打ちのため `effort=high` を使う。Cursor / Codex は light tier に固定（cheap lane モデルでは取りこぼしが多いため）

## This Skill Owns

- 会話内の壁打ち
- 選択肢の整理と比較
- Open Questions の洗い出し
- 「まだ相談段階」か「もう formal workflow に入る段階」かの見極め

## This Skill Does Not Own

- `.steering/.../requirements.md`
- `.steering/.../design.md`
- `.steering/.../tasklist.md`
- `.cursor/plans/*.plan.md`
- `Resume From`
- `Next Action`
- `gdd-design-gating` / human check / `gdd-task-breakdown` / build phase

## Trigger Matrix

- この skill は host の skill discovery で相談レーンとして選ばれることを想定する。GDD state machine の `Next Action` auto-route ではない。
- Use this skill when:
  - ユーザーが「壁打ちしたい」「まだ実装しないけど整理したい」「方向性を詰めたい」と言っている
  - ユーザーが「要件から整理したい」「保存だけしたい」と言っているが、まだ formal workflow は始めていない
  - 例: 「複数ファイルにまたがる機能追加をしたい。まだ `/gdd-dev` は始めず、まず相談だけで要件から整理したい」
  - 要件、選択肢、スコープ、懸念点を軽く詰めたい
  - formal workflow に入る前に、まず会話で固めたい
- Do not use this skill when:
  - ユーザーが `/gdd-dev` を明示実行している
  - ユーザーが既存 steering の再開、`tasklist.md` の続き、実装レビュー以降の phase を明示している
  - ユーザーが既に「今から実装する」「formal workflow を始める」と明示している
- Ambiguous utterances:
  - 「進めて」「この方向で」「やって」だけでは handoff しない
  - まだ相談継続か、`/gdd-dev` に入る意思か不明なら確認する

## Brainstorm Flow

段階的に質問して要件を深掘りする。superpowers の brainstorm パターンに倣い、1問ずつ掘り下げて全体像を明確にする。全ステップを必ず踏む必要はなく、会話の中で十分な情報が出ていればスキップしてよい。

1. **What（何を）**: 何を達成したいか。ユーザーの言葉を目的・スコープ・受入条件に置き換えて確認する
2. **Why（なぜ）**: なぜそれが必要か。動機・背景・誰が困っているかを聞く。既に明らかなら省略可
3. **Who（誰が）**: 誰が使うか、誰が影響を受けるか。ユーザー自身のこともあれば、エンドユーザーやチームメンバーのこともある
4. **Constraints（制約）**: 技術的制約、期限、既存システムとの互換性、コスト上限。制約が見えると選択肢が絞れる
5. **Options（選択肢）**: 2〜3 の選択肢を提示し、違いと判断軸を整理する。ここで `findings.md` に記録する価値がある発見が出やすい
6. **Decision（判断）**: ユーザーの判断を確認し、Summary Brief にまとめる

段階的に質問する理由: 最初からすべてを聞くと情報過多になる。1 問ずつ掘り下げることで、ユーザーが自分の考えを整理しながら進められる。

### findings.md への記録

brainstorm で得た発見（比較結果、技術検証、却下した案とその理由）は、`/gdd-dev` への handoff 時に `.steering/.../findings.md` として引き継げる。ただし pre-workflow 中は artifact を作らないので、handoff 時に Summary Brief と一緒にまとめる。

## Steps

1. Brainstorm Flow の **What** から始める。ユーザーが固めたいものを短く言い換え、目的・スコープ・受入条件の言葉に置き換える。
2. **Why** / **Who** / **Constraints** を順に掘り下げる。既に会話から明らかな項目はスキップしてよい。
3. 十分な情報が揃ったら **Options** を提示する。2 つまでの選択肢を出し、違いと判断軸を整理する。
4. 壁打ち中は会話だけで進め、artifact は作らない。
5. ユーザーが保存を求めても、この lane では `.steering/...` や `.cursor/plans/*.plan.md` を作らない。
6. 「保存だけしたい」と言われた場合は、この lane が artifact を持たないことを伝え、そのまま壁打ちを続けるか、formal workflow に移るかを確認する。
7. ユーザーが明確に実装開始を指示したら、brainstorm で得た発見を Summary Brief にまとめて `/gdd-dev` に handoff する。

## Handoff Rules

- handoff は、ユーザーが明確に実装開始を指示したときだけ行う。
- handoff 後の formal workflow の開始点は常に `/gdd-dev` と同じで、最初の formal phase は `gdd-brainstorming` のままにする。
- active steering の解決、resume 判断、fail-closed 判定、artifact 作成はこの skill では行わない。すべて `/gdd-dev` と `gdd-brainstorming` に委譲する。
- 複数の解釈があり得る場合は handoff 前に確認する。

### 実装へ進む導線

相談の最後は、この出力だけで会話を終えない。必ず次の選択肢を出す:

- このまま壁打ちを続ける
- `/gdd-dev <Summary Brief の一言 + 採用案>` で formal workflow に入る
- 「GDDで実装計画を作って」と言えば、worktree を準備し、requirements.md を作成し、human check まで進む

次に出るもの:

- worktree
- requirements.md
- human check

### Formal Handoff Progress Note

ユーザーが正式に進める Go サインを出した直後は、重い setup の前に 1 文で次に出るものを伝える。例: `ここから formal GDD に入ります。次に worktree を確定し、requirements.md を作成して human check を出します。`

## Transition Rules（pre-workflow ⇄ formal の切り替え）

ユーザーが途中で意図を変える場合の切り替え手順。`references/skill-responsibility-matrix.md` § Pair 2 と整合させる。

### upgrade: pre-workflow → `gdd-brainstorming`（相談 → 正式）

**契機**: ユーザーが「正式に進めたい」「これで進めて」「実装に入って」など、明確な Go サインを出した。

**手順**:

1. このターンまでに固まった内容を `Summary Brief`（3 層）にまとめる
2. `Summary Brief` を出力したうえで `/gdd-dev` に handoff する旨を 1 行で明示
3. `gdd-brainstorming` の `entry intent=new` として起動
4. `gdd-brainstorming` 側で `Summary Brief` を `requirements.md` の初期入力として使う
5. worktree 準備 / artifact 生成は `gdd-brainstorming` が所有

この skill 自身は artifact を作らない。upgrade 時点で `.steering/` 系を一切触らない。

### downgrade: `gdd-brainstorming` → pre-workflow（正式 → 相談）

**契機**: formal workflow 中にユーザーが「やっぱり相談だけに戻したい」「実装やめて整理しなおしたい」と明示した。

**auto-downgrade 禁止**: 既に `.steering/<slug>/` の artifact がある状態で勝手に pre-workflow に戻すと state が dirty になる。必ず人間に確認する。

**手順**:

1. **3 択をユーザーに提示**:
   - `discard`: artifact を削除して pre-workflow に戻る（やり直し前提のとき）
   - `archive`: `.steering/<slug>-archived-YYYYMMDD/` にリネームし、その `state.md` の `Resume From` と `Next Action` をどちらも `cancelled` にして pre-workflow に戻る（後で参照するかも）
   - `continue`: pre-workflow ではなく `gdd-brainstorming` の中で議論を続ける（state を残したまま）
2. ユーザー選択を待つ（auto-select しない）
3. `discard` / `archive` 選択時の worktree / branch 処理は `gdd-using-git-worktrees` § Cancelled Cleanup に委譲
4. `continue` 選択時は本 skill を起動せず、`gdd-brainstorming` の中で会話モードを継続する

この downgrade はユーザーが pre-workflow 名指しで指示した場合のみ受け付ける。曖昧な発言（「ちょっと待って」等）では実行しない。

### 同時並行の禁止

同じ slug / 同じ worktree で pre-workflow と `gdd-brainstorming` を並行起動しない。並行が疑われる場合は fail-closed で停止し、ユーザーにどちらか選んでもらう。判断材料は `references/entry-intent.md` と `references/skill-responsibility-matrix.md` § Pair 2。

## Output Style

- `/gdd-dev` への handoff 時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける
- 相談が続く応答では、冒頭または要約の直後に、このターンでは `/gdd-dev` に入らず artifact も作らないことを 1 文で明示する（既に明らかなら繰り返さない）。
- 相談中は要約、論点、選択肢、確認質問を中心に返す。
- ドキュメント風の長いテンプレートは作らない。
- 会話の締めでは `Summary Brief` を返し、`確定事項` / `未確定事項` / `やらないこと` を明示する。
- 「要件から整理したい」「まだ実装しない」だけなら、`gdd-pre-workflow-brainstorming` を先に明示し、`.steering/...` と `.cursor/plans/*.plan.md` はまだ作らないことを先に伝える。
- 「複数ファイルにまたがる機能追加をしたい。要件から整理したい」だけなら、この lane に留めて artifact を作らず、まだ `/gdd-dev` に handoff しない。
- 「まだ相談段階」なら `/gdd-dev` に handoff しないことを明示してよい。
- 「保存だけしたい」と言われたら、この lane は artifact-free であること、`.steering/...` や `.cursor/plans/*.plan.md` を作らないこと、formal workflow に移るか確認が必要なことを短く伝える。
- 実装 Go が出たら、いままで固まった要点をまとめてから `/gdd-dev` に handoff する。

## Guardrails

- `.steering/...` を作らない
- `.cursor/plans/*.plan.md` を作らない
- `gdd-brainstorming` 以降の formal phase を直接始めない
- 曖昧な Go サインで勝手に handoff しない
- 実装、テスト、レビュー、worktree 作成を始めない（相談レーン＝root。判断根拠は `references/workspace-policy.md` § 相談レーンの分類）
