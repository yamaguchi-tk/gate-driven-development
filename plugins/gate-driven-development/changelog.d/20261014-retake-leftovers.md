---
type: patch
---

#### Summary

`references/independent-review.md` の (3-f) の取り直しと申し送りについて、関係する手順の記述を足した。gate の挙動は変えない。

- `pr-review-followup` の証跡の `Decision Retake` の欄は、GDD の `state.md` § Gate Status の `Decision Retake` の行も読む。初回の iteration で行も前の値も無ければ `not_used` にする
- `gdd-pr-review-followup` の checkpoint の強制発火に `(3-f) 取り直し後の残り` を書いた。`Decision Retake` の行がある状態で独立レビューに high または blocking が残ったときで、(1)〜(3) を選ばずに人に戻し、`<選択>` は `人に戻す` と書く
- (3-f) で後続の test の要件を申し送った Decision があるときは、Task Size によらず `ADR distilled: not_applicable` にせず repo ADR へ蒸留すると、`references/adr-vs-design.md` § Distill 対象・`references/post-completion-pr-flow.md` の Raw Steering Exclusion Check・`references/post-completion-learning.md` に書いた。pre-PR gate と `check-gate-ledger.sh` はこれを検査しない
- `references/phase-progression.md` の Post-Completion PR Flow の停止と、PR Flow 中の finding の節を、High だけでなく blocking の finding にも当てた。(3-f) の取り直しの後も high または blocking が残ったときに昇格処理の順序 3 に進む

#### Affected Files

- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/references/adr-vs-design.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/post-completion-learning.md`
- `plugins/gate-driven-development/references/phase-progression.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
