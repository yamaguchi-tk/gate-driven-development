---
type: patch
---

#### Summary

- `references/common-guardrails.md` § scope の勝手な拡大・縮小 で、依頼より狭める案の出口を替えた。前は「限界に `依頼より狭い` と理由を書いた確認を出す」で狭い案を推奨にできた。今は、狭い案を出す前に、依頼のままでは届かない理由を前提か要件の問題として挙げ、前提を変えて依頼を満たす案を推奨にするか、確かめたい前提・要件を問いとして出す。狭める案は選択肢に並べてよいが、ユーザーが狭めると決めたとき以外は推奨・既定にしない
- 狭い案を既定にできた残りの道を外した
  - `references/human-check-template.md`・`human-check-template-compact.md` の承認ポイントから `既定範囲` と `狭める根拠` の欄を外した。前は `狭める根拠` に数値（実装コスト・誤検知実測・他AC波及）を書けば `狭い側` を既定にできた。今は `無回答時のデフォルト` の欄に、依頼より狭い案を既定にしないと書いてある
  - `scripts/lint-hitl-decision-quality.py` は、この 2 つの欄を求めず、値も検査しない
  - `common-guardrails.md` § 選ぶときの基準 の基準 1 と、相談役 3 本（`gdd-opus-advisor`・`gdd-opus-advisor-max`・`gdd-fable-advisor`）の写しを、狭い案を推奨・既定にしない文に替えた。前は「数値で示せたら狭い案を推してよく、そのときは `依頼より狭い` と書く」だった
  - 方式転換の選択肢（`state-machine.md`・`phase-progression.md`・`rollback-patterns.md`・`gdd-completion-check`・`gdd-pr-review-followup`）の「スコープ縮小」を「依頼の範囲を変えるかを人に問う」に替えた
  - Pre-PR loop の上限で事前回答の委任先が採れる案から「AC を削らないスコープ縮小」を外し、再設計だけにした（`post-completion-pr-flow.md`）。依頼の範囲を変えるかを人に問う案を推したら、人に止まる
  - 限界の `依頼より狭い` には、選んでもらう判断ポイントの番号か、ユーザーが狭めると決めた記録の場所を添える。どちらも無ければ、その狭めはしない（`common-guardrails.md` § Honest Limitations・§ scope、相談役 3 本の `残る限界:`）
  - 要件縮小の 1 回検討（`brainstorming-steps.md`）で、縮小版を採用案にできるのは、ユーザーが狭めると決めたときだけにした。前は基準 1 の数値の理由があれば採用案にできた

#### Affected Files

- `references/common-guardrails.md`
- `references/human-check-template.md`
- `references/human-check-template-compact.md`
- `scripts/lint-hitl-decision-quality.py`
- `agents/gdd-opus-advisor.md`・`agents/gdd-opus-advisor-max.md`・`agents/gdd-fable-advisor.md`
- `references/state-machine.md`・`references/phase-progression.md`・`references/rollback-patterns.md`・`references/brainstorming-steps.md`・`references/post-completion-pr-flow.md`
- `skills/gdd-completion-check/SKILL.md`・`skills/gdd-pr-review-followup/SKILL.md`

#### User Action Required

- 古い形（`- 既定範囲:`・`- 狭める根拠:` の行）で書いた human check も、lint は落とさない。行はそのまま残っても検査されない

#### Validation / Eval Impact

- `lint-hitl-decision-quality.py` の検査が 1 つ減る。再生での比べ方は PR 本文に書いた
