---
type: patch
---

#### Summary

実装の差し戻しの早期の方式判断（1 回目の差し戻しで high が 3 件以上のとき、Opus に route を聞く）の配線の欠けを直した。

- impl gate が `changes_requested` を返すとき、`handoff/implementation_gating.md` に `## Round <Gate Rounds>` の節を足し、finding ごとに severity・category・対象の task を書く手順を、`gdd-implementation-gating` の Step 9 と Implementation-Gating Template にも書いた。見出しの番号はこの gate が更新した後の `Gate Rounds`（足さなかったときは今の値、無ければ 0）で、gate が決める（呼び出し側は埋めない）。前の節は消さず、早期の方式判断は最後に足した節が `## Round 1` のときにその節で数える。これまでは handoff の例にしか無く、書かれないと早期の方式判断は行われなかった
- 自律モードで、早期の方式判断の判断役が止めるべきと答えた、または答えが読めないときに人間に止まることを、`references/autonomy.md` の止まる場面と `references/rollback-patterns.md` の Downstream Human Recheck Handoff にも書いた。これまでは `references/state-machine.md` の本文と `references/autonomy.md` の参照元の行にしか無く、Handoff から一覧 2 に入って進みうる

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/state-machine.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
