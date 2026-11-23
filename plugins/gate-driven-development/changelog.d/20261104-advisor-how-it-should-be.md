---
type: patch
---

#### Summary

- 相談役（`gdd-opus-advisor`・`gdd-fable-advisor`・`gdd-opus-advisor-max`）は、並んだ案を比べる前に「そもそもどうあるべきか、どうするのがいいのか」を問うようにした。依頼の原文の目的と repo の規則・要件から、あるべき形（目標・指標・手法・方式そのものも、問い直す対象に入れる）と、症状を塞ぐより先に、その問題を生んだ原因（設計の決定・前提・工程）ごと直す進め方を先に考え、並んだ案がそこに届くかを比べる。どの案も届かないなら、あるべき形に向かう案を推す。問いの前提や案の並びに合わせて、推奨を狭めない。これまでの「並んだ案に無い案は、選ぶときの基準の 2・3・4 に当たるときに推す」の文は外した
- 相談役の出力の先頭に `そもそもどうあるべきか:` の欄を足した。`推奨:` はこの欄から導き、`観点:` の値に `あるべき形` を足した
- `references/common-guardrails.md` § 選ぶときの基準 に、番号の基準で照らす前に同じ問いを置くことを書いた（main も相談役も当てる）

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/references/common-guardrails.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 過去の相談 19 件への当て直しの記録: repo root の `review-log/20261104-advisor-how-it-should-be.notes.md` の `## Skill RED-GREEN Evidence`
