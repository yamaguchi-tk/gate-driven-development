---
type: patch
---

#### Summary

- 相談役（`gdd-opus-advisor`・`gdd-fable-advisor`・`gdd-opus-advisor-max`）の「そもそもどうあるべきか、どうするのがいいのか」の問いを、`references/common-guardrails.md` § 選ぶときの基準 の冒頭に移し、相談役 3 本の同じ節に同じ文で写した。`tests/test_advisor_agents.py` は、この問いも番号の基準と合わせて写しの一致を見る
- あるべき形が、ユーザーがすでに決めたこと（基準 0）と食い違うときは、その決定を覆す案を推奨にせず、食い違いと理由を書く。基準 0 の「1〜3 を、それを覆す理由に使わない」を「上の問いと 1〜3 を」にした
- あるべき形の一部が依頼の範囲の外にあるときは、範囲の中で一番近づく案を推奨にし、範囲の外の分は相談役の新しい欄 `範囲を広げる提案:` に分けて書く。基準 3 の「選択肢に無い案を推してよいとき」に、どの選択肢もあるべき形に届かないときを足した
- 相談役の `観点:` の `あるべき形` は、並んだ案に無い案を推したときだけ付ける。出力の節は、結論（`推奨:`）を先頭の `そもそもどうあるべきか:` の次に書くと書き分けた
- main が自分で案を推すときも、同じ問いを依頼の原文の目的から自分に問うと書いた

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/references/common-guardrails.md`
- `plugins/gate-driven-development/tests/test_advisor_agents.py`
- `plugins/gate-driven-development/changelog.d/20261104-advisor-how-it-should-be.md`（文の直し）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 過去の相談 19 件への当て直しの記録: repo root の `review-log/20261105-advisor-how-it-should-be-findings.notes.md` の `## Skill RED-GREEN Evidence`
