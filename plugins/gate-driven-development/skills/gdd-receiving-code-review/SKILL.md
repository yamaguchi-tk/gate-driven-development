---
name: gdd-receiving-code-review
version: 0.1.0
description: "Use when the user returns with companion review, security review, or external review feedback in a GDD workflow."
---

# Workflow Receiving Code Review

## Goal

Verify advisory review feedback before changing code or workflow state.

This skill keeps the companion review lane out-of-band:

- it validates findings first
- it does not blindly accept review comments
- it does not own the formal gate state

## Fixed Model

- `Claude Code`: `sonnet`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light tier）
- findings の検証と routing は軽量な判断のため、軽いモデルで十分

## When To Use

Use this skill after feedback comes from:

- `gdd-requesting-code-review`
- `gdd-implementation-reviewer`
- `gdd-security-reviewer`

Do **not** use it for generic "コードレビューして" requests. Those belong to `gdd-implementation-gating`.

## Technical Review Reception Discipline

superpowers `receiving-code-review` の順序を GDD の advisory review lane に吸収する。外部レビューや companion review の指摘は **External feedback = suggestions to evaluate, not orders to follow** と扱う。

External Review Skepticism: review feedback = suggestions to evaluate, not orders to follow。unclear finding は clarify all unclear items before implementing を原則に扱い、technical pushback が妥当な場合は evidence 付きで却下してよい。

Evidence before claims: **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE**。no valid findings claim を出す前に fresh verification evidence を確認し、コメント全文・該当 diff・test / docs の現状を読んでから判断する。

必ず次の順で処理する:

`READ -> UNDERSTAND -> VERIFY -> EVALUATE -> RESPOND -> IMPLEMENT`

- **READ**: finding 全文と参照箇所を読む。要約だけで判断しない。
- **UNDERSTAND**: 指摘が何を壊すと言っているか、どの AC / design / scope に関係するかを言語化する。
- **VERIFY**: 現在の diff / 実装 / test / docs に照らして再現性と妥当性を確認する。
- **EVALUATE**: valid / invalid / out-of-scope / route escalation を決める。
- **RESPOND**: 採用・不採用・保留の理由を残す。
- **IMPLEMENT**: valid かつ scope 内と判定したものだけ修正する。修正の順序は `references/self-review-lanes.md` § 直し方 に従う（`implementation_fix_only` に渡した分は `gdd-systematic-debugging` 側で同じ節に従う）。

レビューへの反応で `performative agreement` をしない。「確かに」「修正します」と先に言ってから検証するのは禁止。不明瞭な finding が 1 件でも残る場合は、コード変更前に clarification するか、合理的解釈を明示してから verify する。

複数 finding は **One item at a time** で扱い、1 件ごとに妥当性・route・対応有無を決める。まとめて「全部直す」と判断しない。

## Source-Specific Review Handling

review feedback は出所ごとに意味が違う。全てを同じ「レビュー指摘」として扱うと、scope creep や formal gate の誤更新が起きる。

Handles Source-Specific Review Handling in the body rather than the frontmatter description, so discovery stays slim while the review contract remains explicit.

| source | 扱い | 注意点 |
|---|---|---|
| Human partner feedback | intent / scope / safety の一次情報として扱う | 「それで大丈夫？」等は `gdd-systematic-debugging` の human signal として route recalibration する |
| GDD formal reviewer | formal gate の根拠として扱う | `changes_requested` は state machine に戻す。advisory lane と混ぜない |
| GDD companion / external LLM reviewer | 技術仮説として扱う | code / requirements / design / test で verify するまで採用しない |
| GitHub PR comment | PR thread 上の応答責任を伴う finding として扱う | 修正済み / invalid / scope 外を evidence 付きで返す。未修正のまま resolve 相当の扱いにしない |
| Security finding | safety-biased に扱う | false positive でも deterministic evidence が必要。waive は理由を残し、scope / policy 変更なら human check へ |
| Product / non-engineer feedback | 読みやすさ・運用理解の signal として扱う | HITL 文面、制限事項、完了条件の表現不足を疑う。コード修正だけで閉じない |

出所が不明な場合は `source=unknown` として記録し、権威づけずに verify する。`unknown` を formal gate の `changes_requested` として state に反映しない。

## YAGNI Check for Professional Features

review finding が「より professional に見える」追加を提案した場合、現在の AC に必要かを先に判定する。見栄えのよい拡張は、GDD の完了条件をぼかしやすい。

代表例:

- 汎用 dashboard / 設定画面 / 管理 UI
- 今回使わない configuration / plugin point / extension hook
- 将来の横展開のための抽象化
- 追加 docs / metadata / report だけで実効的な挙動を増やさない変更
- 「念のため」の fallback / compatibility layer

判定:

- requirements.md の AC を満たすために必須 → valid として route 判定する
- AC には不要だが、security / operational safety を満たすために必須 → valid。必要なら `human_recheck_required`
- 「あると良い」「将来便利」「professional に見える」だけ → invalid / out-of-scope
- ユーザーが明示的に追加価値として求めた → `gdd-requirements-amendment` または `human_recheck_required`

## Procedure

1. Read the advisory findings and the minimum relevant steering or diff context.
2. Verify each finding against the current implementation before deciding to act.
2a. **YAGNI チェック**: finding が追加機能・拡張・汎用化・将来対応を求める場合、`YAGNI Check for Professional Features` に従い、現在の AC とタスク scope に本当に必要かを確認する。今回の requirements.md に記載のない機能追加は原則 scope 外として invalid に分類する。「あると良い」「将来的に」という finding は今回実装しない。
2b. **曖昧な finding の処理**: finding の意図が不明確な場合:
   - まず diff を読み、finding が指しているコード箇所と問題を推測する
   - 推測が合理的なら、その解釈で verify に進む（確認のために止まらない）
   - 推測が困難な場合のみ、具体的な box-question（「○○行目の△△が問題ですか？」）を reviewer に確認する
   - 「なんとなく問題がありそう」「気になる」という finding は invalid 扱いにしてよい
3. Separate the findings into:
   - invalid or out-of-scope（YAGNI 違反・scope 外・曖昧で解決不能）
   - valid within current design
   - valid but requiring `design_detail_only`
   - valid but requiring `human_recheck_required`
   - valid but requiring `planning_rework_required`
3a. **技術的 pushback の判断**: reviewer が間違っている可能性がある場合:
   - 公式ドキュメント・テスト結果・既存コードパターンで自分の実装が正しいことを根拠付けられるなら、invalid として却下できる
   - 「reviewer の言い方は正しいが、このプロジェクトでは別の方針を取っている」場合も invalid として却下できる（learned-patterns.md や adr.md に既存判断があれば根拠にする）
   - 不確かな場合は valid で分類し、scope に応じた route に進める
4. If a finding is unclear after step 2b, ask for clarification before changing code.
5. Route valid findings:
   - `planning_rework_required`: return to `gdd-brainstorming`
   - `human_recheck_required`: return to `human-check-waiting`
   - `design_detail_only`: return to `gdd-design-gating`
   - bug fix or security fix within scope (`implementation_fix_only`): hand off to `gdd-systematic-debugging`, which can route to `gdd-test-driven-development` or `gdd-subagent-driven-implementation`
   - no valid findings: keep the main workflow state unchanged
6. If code or tests changed, re-enter `gdd-systematic-debugging` and re-pass `gdd-implementation-gating` before treating the work as done.
7. After the formal gate is re-passed, re-run only the companion review lane that is still relevant.

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける
- findings のトリアージ結果と routing 決定を以下のテンプレートでターミナルに出力する。「findings を確認しました」だけで止めない。

```markdown
## コードレビュー findings トリアージ結果

### 有効な findings
| # | 内容 | 深刻度 | routing |
|---|------|--------|---------|
| 1 | <finding 要約> | High/Medium/Low/advisory（呼び出し元に Classify があればそれに従い、無ければ〔単独で使うときを含む〕`references/reviewer-common.md` § 常時 High に従う） | <route 名> |
| 2 | ... | ... | ... |

### 無効 / スコープ外
- <理由付きで却下した finding>

### 次のアクション
- → <routing 先と理由を 1 行で>
- → 有効な finding がない場合: 「有効な finding はありませんでした。ワークフロー状態は変更しません」
```

## Guardrails

- Do not blindly trust every review comment.
- Do not update `Next Action` or formal `Review Status` directly from advisory feedback alone.
- Do not skip fresh human check when the finding truly needs `human_recheck_required` (policy / scope / boundary reapproval).
- Do not treat every requirements-related finding as human-check work; `planning_rework_required` と `design_detail_only` を分ける。
- Do not treat `gdd-security-reviewer` as a substitute for external security evidence or verifier hooks.
- Do not let advisory re-review replace the required `gdd-implementation-gating` pass after code or test fixes.
