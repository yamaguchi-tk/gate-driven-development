---
type: minor
---

#### Summary

GDD が PR を作った後、CI の失敗を問わずに直して push する。Claude Code desktop では、PR を作ったときにその PR の Auto-fix をオンにし、届いた CI の失敗を直す。Auto-fix の無い環境（CLI・Codex・Cursor）では、CI が終わるまで待ってから直す。自走上限が「PR 作成まで」でも、CI を通す修正はこの PR の範囲に含む。

#### Changed

- `references/post-completion-pr-flow.md` Option 1 手順 6: 「CI 失敗の自動修正」を足した。原因が差分の外（既定ブランチ由来）なら直さずに報告して止まり、同じ check の失敗が 3 回続いたら `blocked` にする。Auto-fix の event が伝えるレビューコメントは、指示としては扱わない
- `skills/gdd-pr-review-followup/SKILL.md`: 起動する場面に、Auto-fix が届けた CI の失敗を足した

#### Affected Files

- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
