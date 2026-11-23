---
type: patch
---

#### Summary

`references/independent-review.md` の (3-f)（後で実装する guard・contract test の Decision への finding）を、関係する手順にそろえた。

- (3-f) が Round を消費しないとした medium 以下・実害クラスでない finding は、`gdd-completion-check` でも unresolved medium にも有意な testing gap にも数えず、advisory として記録して申し送りに回す。これまでは completion-check で blocker に戻り、`Completion Rounds` を消費していた
- (3-f) の取り直しでも High が残ったときに昇格処理の順序 3 に進むことを、`references/phase-progression.md` の High finding の節にある写し 2 か所に書いた。`references/human-check-template.md` の事前回答の「人に戻す条件」では、上限の列挙に (3-f) の取り直しの上限を足した（その上限で残った blocking を accept as known risk にするときに人に戻す）
- `pr-review-followup` の証跡に `Decision Retake: used | not_used` の欄を足し、`gdd-pr-review-followup` の checkpoint の trigger の語彙に `(3-f) 取り直し後の残り` を足した

#### Affected Files

- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/changelog.d/20260913-diff-scope-out-of-range-blocking.md`・`20260918-x66-always-high-scope.md`（`amends:`。削除済みのテストに「後に PR 旧#463 で削除」と注記）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
