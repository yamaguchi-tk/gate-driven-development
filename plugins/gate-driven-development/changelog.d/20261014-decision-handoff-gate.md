---
type: minor
---

#### Summary

`references/independent-review.md` の (3-f) で後続の test の要件を Issue に申し送った Decision を、pre-PR gate が `ADR distilled: not_applicable` のまま通さないようにした。

- `state.md` § Gate Status に Tier 3 の欄 `- Decision Handoff: issue: #<N>[, #<M>] | at: <ISO 8601>` を足した。main session が (3-f) の申し送りで Issue に写したときに 1 行書く（impl-gate・completion-check の手順 13 からも同項を指す）。申し送りが無ければ行を書かない
- `hooks/scripts/lib/gate-ledger.sh` の `gdd_adr_not_applicable_allowed` は 3 つ目の引数に `state.md` のパスを取る。ファイルに `decision handoff` の文字列があるとき（大文字小文字・fence・字下げ・値の有無を問わない）と、パスが無い・読めないときは、Task Size と理由によらず `not_applicable` を許さない。値の書式は検査しない
- pre-PR gate は `不足ガード=ADR not_applicable with Decision Handoff` で止め、`docs/adr/` へ蒸留して `ADR distilled: yes` にするよう案内する。`scripts/check-gate-ledger.sh` は `adr-distilled` の行を invalid にする
- 「gate はこれを検査しない」と書いていた `references/post-completion-pr-flow.md`・`references/post-completion-learning.md` を直し、`references/state-field-tiers.md` に欄を、`state.md` を短くするときに残す欄の案内（`steering_size.py`）に欄名を足した

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/steering_size.py`
- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/post-completion-learning.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`

#### User Action Required

- `state.md` に `decision handoff` の語（欄名）を、申し送りが無いのに書かない。書くと `ADR distilled: not_applicable` で PR を作れなくなる（出口は `docs/adr/` へ蒸留して `ADR distilled: yes`）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py plugins/gate-driven-development/tests/test_check_gate_ledger.py -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
