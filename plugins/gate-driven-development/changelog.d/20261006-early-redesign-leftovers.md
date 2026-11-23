---
type: patch
---

#### Summary

実装の差し戻しの早期の方式判断で、判断役の答えの扱いを単純にし、判定と記録の曖昧さを直した。

- 判断役の答えは、main が 1 つの route に写してから `gdd-systematic-debugging` に渡す。`推奨:` が既知の route で `止めるべきか: no` のときだけその route にし、それ以外（`止めるべきか: yes`、欄が無い・読めない、途中で切れた出力、route でない案）はすべて `human_recheck_required` にする。受ける側は写した route だけを見る。起動できないのは Agent tool の起動がエラーを返したときだけで、そのときは route を渡さず通常どおり判定する
- 判断役が止めるべきと答えたときに、自律モードや事前回答の適用中でも人間に止まり聞き直さない、という例外をやめた。`human_recheck_required` に写した後は、ほかの `human_recheck_required` と同じく Downstream Human Recheck Handoff に従う（自律モードは一覧 2 の判断役に、事前回答の適用中は委任先に、人間に止めるべきかを聞く。事前回答の委任先が `なし` なら main の仮決定で進みうる）。`references/autonomy.md` の止まる場面、§ 事前回答 3 の人に戻す条件、Downstream Human Recheck Handoff から、この例外の項目を除いた
- 早期の方式判断の問いに「人間に止めるべきか」を足し、`推奨:` と `止めるべきか:` の欄で答えるよう問いに書く（Codex・Cursor の経路でも欄が返るようにするため。返らなければ `human_recheck_required` に写す）。`早期方式判断:` の行に `写した route:` の欄と、`判断役の推奨:` の `読めない` の値を足した
- `gdd-implementation-gating` の Step 1・1d の出口でも、`Gate Rounds` の加算（Round 消費 category の finding があるときだけ +1）を Step 9 のとおりにする。2 回目の差し戻しで `## Round 1` の節が足されなくなる
- Implementation-Gating Template の State Update Contract の `approved` から Step 8a の出口を除いた。見出しの番号の説明に、足さなかったときの値（今の値、無ければ 0）を書いた
- `事前回答の適用:` の行の 1 欄目に `human-recheck`（Downstream Human Recheck Handoff で着いたとき。`対象:` は `Current Task` の id）を足した

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
