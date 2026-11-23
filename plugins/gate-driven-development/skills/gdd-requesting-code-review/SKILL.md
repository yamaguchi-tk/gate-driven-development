---
name: gdd-requesting-code-review
version: 0.1.0
description: "Use when the user explicitly requests an out-of-band GDD companion, security, or final diff review."
---

# Workflow Requesting Code Review

明示的な companion review の dispatcher。formal gate である `gdd-implementation-gating` の代わりではなく、追加の advisory review を別レーンで起動するときだけ使う。

## Goal

Run an explicit advisory review without changing the formal gate model.

## Fixed Model

- `Claude Code`: `opus` + `effort=high`
- `Cursor`: `Grok 4.6` + `reasoning.effort=low` / `Codex`: `gpt-5.6-sol` + `reasoning.effort=low`
- 3 host とも general_heavy tier（`scripts/resolve-gdd-model.py` の割り当てと `skills/gdd-model-routing` の表に合わせる）。実レビュー本体は、起動した reviewer の agent 定義のモデルに従う

This skill exists for:

- PR 前の final diff review
- security-sensitive change の追加 review
- formal multi-reviewer gate とは別レーンでの second opinion

## Where It Is Used

- PR 作成前に、formal gate とは別で final diff をもう一度見たいとき
- security-sensitive な変更に対して、`gdd-security-reviewer` の追加確認を取りたいとき
- `gdd-implementation-gating` とは別に advisory な second opinion を取りたいとき

## What It Does

- 対象 diff と依頼理由を最小限だけ読む
- `gdd-implementation-reviewer`、`gdd-security-reviewer`、または両方を選ぶ
- companion review を起動して findings を集める
- actionable issue があれば `gdd-receiving-code-review` に渡す
- formal `Next Action` や formal `Review Status` は変えない

This skill does **not** replace:

- `gdd-implementation-gating`
- `gdd-implementation-reviewer`（formal gate）
- required external security evidence

## When To Use

Use this skill when the user explicitly asks for a **companion review** — an additional advisory review separate from the formal gate. Trigger phrases include:

- 「追加レビューして」「追加で見て」
- 「companion review して」
- 「セキュリティレビュー追加で」
- 「final diff を別レーンで見て」
- 「gdd-requesting-code-review で見て」
- "companion review", "additional review", "second opinion"

Do **not** use this skill for generic review requests:

- 「コードレビューして」→ `gdd-implementation-gating`
- 「実装レビューして」→ `gdd-implementation-gating`
- 「PRレビューして」→ `gdd-pr-review`
- 「差分チェックして」→ `gdd-pr-review`

If the user wants the companion lane but did not explicitly invoke it yet, first ask for or confirm `gdd-requesting-code-review` rather than auto-starting this lane.

## Inputs

Collect only the minimum context needed:

- approved `.steering/.../requirements.md`
- approved `.steering/.../design.md`
- current `.steering/.../tasklist.md` if it exists
- the current task or target diff
- why the companion review is being requested

## Reviewer Selection

- Use `gdd-implementation-reviewer` for:
  - final diff review
  - bugs, regressions, maintainability, workflow drift
- Use `gdd-security-reviewer` for:
  - auth
  - secrets
  - input validation
  - dependency risk
  - IaC exposure
- Use both when the request or diff clearly needs both viewpoints

## Checkpoint Review Triggers

superpowers `requesting-code-review` の checkpoint review 規律を GDD の companion lane に吸収する。これは formal gate の代替ではなく、自然な節目で advisory review を入れるための trigger 定義である。

### Early Lightweight Review Habit

Review early, review often。GDD では、レビューを最後の大きな gate だけに寄せず、task completion or natural checkpoint で軽量な advisory review を提案できる。ただしこれは proposal, not an automatic blocking gate であり、does not replace gdd-implementation-gating。

提案してよい自然な節目:

- after each completed task: task 単位の変更がまとまり、次 task に入る前
- natural checkpoint: API 境界、データ構造、権限境界、HITL 文面、テスト戦略など、後続作業に影響する判断が固まった時
- before merge: PR 作成後、merge 前に追加の second opinion が欲しい時
- stuck / uncertain: root cause や設計判断に迷いが残り、追加視点が価値を持つ時

依頼 context には base/head SHA を含める。最低限、`BASE_SHA` / `HEAD_SHA` / 何を見てほしいか / どの requirements・design・tasklist に基づくかを渡す。軽量レビューで指摘が出た場合も、そのまま実装変更せず `gdd-receiving-code-review` に渡して妥当性を評価する。

次のいずれかに該当する場合、ユーザー明示または GDD 内の計画で companion review を提案してよい:

- **major feature**: 複数 component / module / workflow にまたがる実装
- **security-sensitive**: auth / secrets / PII / permission / external egress / credential / untrusted input を扱う変更
- **IaC**: Terraform / CloudFormation / Kubernetes / runtime deploy config などの infra 変更
- irreversible / hard-to-rollback な変更
- prompt / skill / review policy / human-facing HITL 出力の変更
- **before-refactor-baseline**: `gdd-refactor-planning` が `Refactor Baseline Review Packet` を作り、large / shared / sensitive refactor の事前確認を求めた時

レビュー依頼には **Reviewer Lineage** を残す。最低限、以下を companion review context に含める:

```markdown
Reviewer Lineage:
- requested_by: <user|gdd-skill|checkpoint-trigger>
- reason: <major feature|security-sensitive|IaC|before-refactor-baseline|...>
- REASON=<final-diff | security-sensitive | before-refactor-baseline | stuck | other>
- BASE_SHA: <base sha>
- HEAD_SHA: <head sha>
- DESCRIPTION: <何を確認してほしいか>
- PLAN_OR_REQUIREMENTS: <requirements/design/tasklist path or Refactor Baseline Review Packet>
```

actionable issue が出た場合は、そのまま実装変更に入らず `gdd-receiving-code-review` に渡して妥当性・route・修正要否を評価する。

## Procedure

1. Confirm this is an explicit companion review request and not a generic `gdd-implementation-gating` request.
2. Read the minimum steering and diff context.
3. Choose `gdd-implementation-reviewer`, `gdd-security-reviewer`, or both.
4. Run the selected reviewer(s) and present the findings as advisory review.
5. If the review finds actionable issues, hand off to `gdd-receiving-code-review` to verify and route the fixes.
6. If no actionable issues are found, report that the companion review was clean and leave the main workflow state unchanged.

## Guardrails

- Do not change `Next Action`.
- Do not change formal `Review Status`.
- Do not auto-trigger this lane for generic review requests.
- Do not auto-trigger this lane from PR 前 review や security review の文脈だけで判断しない。`gdd-requesting-code-review` の明示実行を必須にする。
- Do not call generic reviewer names such as `code-reviewer` or `security-reviewer`.
- Treat `gdd-security-reviewer` as additional human-style review, not as a replacement for external security evidence or verifier hooks.
