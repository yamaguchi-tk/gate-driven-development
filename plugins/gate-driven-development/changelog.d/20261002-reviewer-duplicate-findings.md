---
type: patch
---

#### Summary

- PR 前の配線レビュー（別系統モデル）の指摘を、同じ push に向けた独立レビューの指摘と突き合わせ、同じ箇所の指摘を二重に数えないようにした

#### Changed

- `gdd-pr-review` の 3g（配線レビュー）で、Codex に指摘ごとの `file:line` を添えさせるようにした
- 人に見せる前・直す前に、同じ push に向けた独立レビューの指摘と突き合わせ、`file:line` が同じものは独立レビューの id を添えて 1 件にまとめるようにした。扱いは独立レビュー側に従い、severity・blocking が食い違えば重い方を取る。行が違うものはまとめない

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
