---
type: minor
---

#### Summary

- PR 本文の型を `references/japanese-writing-norm.md` § PR 本文 に置いた。PR テンプレートがあればその見出しに従い、テンプレートに無い見出しを足さない。テンプレートが無ければ、なぜ・挙動の変化・確認したこと・やっていないこと・見てほしい箇所の順に、項目名を見出しにせず書く。「実装内容」にもファイルの一覧ではなく挙動の変化を書き、工程の記録（gate の経緯、どの巡で何が出たか）は書かない。型の出典は plain-writing の `writing-for-readers` § PR description で、plain-writing の skill は呼ばない
- PR Body WHY Check は、独立した `## Why` / `## なぜ` の見出しを求めなくなった。WHY は、テンプレートの目的・背景を書く欄（背景・目的・要件・概要など）の冒頭、そういう欄が無ければ最初の欄の冒頭、テンプレートが無ければ本文の最初の段落に書く。WHY が読めなければ High で PR 作成を止めるのは今までどおり
- advisory findings（impl-gate・completion-check が記録した medium / low）と Pre-PR loop で受け入れた medium / low は、`## Advisory Findings` や `## Known limitations` の節ではなく、本文の残した問題の欄に 1 件 1 行で全件書く。各行は `指摘止まり（<severity>）:` で始める。silent drop の確認は、見出しの有無ではなく、この行の数と state.md の記録・受け入れた件数の和の一致で行う
- 残した問題の欄には、指摘止まりの行のほかは、マージの後も残る不利益とまだ決まっていないこと（返事待ちの問い、人間に戻した箇所）だけを、変更の性質として書く。決着した確認は決めたことを 1 文で書く
- 自律で判断した箇所は `## 自律で判断した箇所` の節ではなく、`自律で判断したこと:` のラベルの下に 1 件 1 行で書く。人間に戻した箇所は残した問題の欄に書く
- 影響範囲の節がテンプレートに無いとき、`## 影響範囲` の見出しを足すのは 3 行を超えるときだけにした

#### Changed

- `references/post-completion-pr-flow.md`（Option 1 の PR 作成手順 4 と、その下の WHY・Boundary / Follow-up・Merge-Triggered Workflows・Autonomy Decisions・Advisory Findings の各 Check。残した問題の欄の項を足した）
- `references/japanese-writing-norm.md`（§ PR 本文 を足した）
- `skills/gdd-pr-review/references/pr-review.md`（WHY Check と Boundary / Follow-up Check の写しを同じ内容にした）
- `references/state-field-tiers.md`・`references/phase-progression.md`（advisory findings の搬送先の書き方）

#### Affected Files

- `references/post-completion-pr-flow.md`
- `references/japanese-writing-norm.md`
- `skills/gdd-pr-review/references/pr-review.md`
- `references/state-field-tiers.md`
- `references/phase-progression.md`

#### User Action Required

- 動いているセッションは、開き直すまで古い規定で PR 本文を書く
- `skills/gdd-pr-review/references/pr-review.md` を上流の pr-review plugin と同期し直すときは、WHY Check と Boundary / Follow-up Check のこの変更を当て直す

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
