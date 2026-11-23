---
type: patch
---

#### Summary

- 指摘の行き先（`review-findings.md`）の規定の文を、述語と CLI の実際の動きにそろえた。検査を回す時点、検証役を起動する条件、`absent@` の条件と path の形、独立レビューの `blocking` の数え方が、文書ごとに食い違っていた

#### Fixed

- `skills/gdd-implementation-gating/SKILL.md` Step 8: 検証役の判定が要るのは、`rejected:refuted` と、high・実害クラスの `advisory:calibration`・`advisory:unverified_file` だけと書いた（前は捨てる・下げる finding のすべてと読めた）。Step 1c の `absent@` の条件は正本を指す
- `skills/gdd-pr-review-followup/SKILL.md`: `Independent Review` 行の `blocking` は、`review-findings.md` の `IR` 節を `finding-dispositions.md` の数え方で数える（`rejected:duplicate` は数えない）
- `references/finding-dispositions.md`: 前の節を直してよいのは検査が誤りを示したときだけ、`absent@` の行は検証役を起動しない、path に使える文字（Unicode の文字・数字・`_`）、`rejected:refuted` にした行が再び出たら `Route In Progress` を `human_recheck_required` にする、を書いた
- `agents/gdd-finding-verifier.md`: 材料の欄は reviewer がその指摘に書いた欄すべて（欄の名前は reviewer ごとに違う）
- `references/subagent-dispatch.md`・`README.md`・`scripts/check-gate-ledger.sh` の冒頭の説明: 指す表、agents の一覧、`findings` 行の gate 列（`independent-review`）を直した

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/references/finding-dispositions.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/agents/gdd-finding-verifier.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/scripts/check-finding-dispositions.py`
- `plugins/gate-driven-development/hooks/scripts/lib/finding_dispositions.py`
- `plugins/gate-driven-development/tests/test_finding_dispositions.py`
- `plugins/gate-driven-development/tests/test_finding_verifier_agent.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_finding_dispositions.py`（実害クラスの calibration、同じ sha の節の引き継ぎ、`rejected:refuted` の medium・low の数え方、節の順序違い、ledger の読めない形、`git log` にだけ残る basename と NFD の名前を固定する）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
