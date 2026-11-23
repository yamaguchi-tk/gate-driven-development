---
type: patch
---

#### Summary

実装の差し戻しの早期の方式判断（1 回目の差し戻しで high が 3 件以上のとき、Opus に route を聞く）を、次のように直した。

- 判断役は、`gdd-systematic-debugging` を起動する側（通常は main）が起動の前に呼び、推奨を材料として渡す。subagent の中から入れ子で起動することに頼らない。high は impl gate の handoff（`handoff/implementation_gating.md` の `## Round 1` の節。impl gate が `changes_requested` のときに finding ごとに書く）で数え、読めないときは行わない。Codex・Cursor での起動は `references/autonomy.md` 判断の手順 1 と同じ
- `gdd-systematic-debugging` は、Routing Decision Tree の 1 の ADR ≥ 2 の判定の後、テスト設計の判定の前に推奨を当てる（2/2・同一 root cause カテゴリ 3 回連続・ADR ≥ 2 の方式転換が先。TDD に戻る前に判断する）
- 1 つの steering で 1 回だけにした。起動する側が起動を試みた直後に（起動できなかったときも）`worklog.md` に `早期方式判断:` の行を書き、起動できなかった回も 1 回に数える。その行で数えるので、作り直しで tasklist の数えが途切れても、早期の方式判断が作り直しのたびに起動されることはない
- 判断役が `止めるべきか: yes` と答えた、または 4 つの route と TDD・root-cause-investigation のどれでもない案を推したときは、`human_recheck_required`（方式転換の選択肢の提示）として扱う。自律モードでも、止めるべきという答えは `references/autonomy.md` 判断の手順 4 のとおり人間に止まり、それ以外は一覧 2 に従う。`root-cause-investigation` が推されたら No Root Cause Routing に戻す
- 推奨が `design_detail_only` で自走範囲の中なら人間に戻さない。自走範囲の検査で外と分かれば、Decision Tree の 3b〜5 で判定する
- `worklog.md` の行の書式に task id・task ごとの high の件数・`止めるべきか:`・`model: なし` を足した。採った route はこの行に書かず、route の記録に書く
- Gate Batch では、batch の 1 回目の差し戻しで high が 3 件以上の task が 1 つでもあれば、1 回だけ起動して batch 全体の route を問う
- `phase-progression.md` の Escalation Decision Table に行を足し、相談役の起動点の列挙（`agents/gdd-opus-advisor.md`・`references/fixed-models.md`・`references/autonomy.md`）に足した

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（同じ steering で 2 回目の場面と、判断役が止めるべきと答えた場面）は PR 本文に書く
