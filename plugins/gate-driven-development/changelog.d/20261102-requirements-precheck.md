---
type: minor
---

#### Summary

- requirements-gating で、reviewer を起動する前に提出前の照合を 1 回行うようにした（quick (express) では requirements.md だけを照合する）。新しい agent `gdd-requirements-precheck`（Sonnet・high・read-only）が、初稿の requirements.md と design.md の文を、決まったチェック表（既存の挙動・テスト・一緒に変えるもの・合否の計測・既存の止めとの比較・後ろの段・文書の中の数と名前）で既存のコードに当てる。gate runner は `ng` を確かめてから初稿に反映し、照合の表は `.steering/<task>/review-input/precheck-round-<N>.md` に残す。reviewer には渡さない
- 再入の Round では、前回の blocking の処置が核を解いているか・直しが届いているか・処置が新しい食い違いを作っていないか（項目 0）も確かめる。再入で反映した `ng` は、最新 Round の処置に `照合-<n>` の項目として追記するので、再入の reviewer が見る範囲に入る
- worklog.md に `照合: Round <N> ng <n>・反映 <n>・不採用 <n>` の 1 行を書く。照合の agent が使えないときは `照合: unavailable（理由）` と書いて reviewer に進む
- brainstorming の Step 17 の「整合は再確認しない」を、照合は requirements-gating の提出前の照合が行う、に直した
- reviewer の blocking の線、Round 上限、Round の数え方は変えていない

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-requirements-precheck.md`（新規）
- `plugins/gate-driven-development/references/requirements-gating-steps.md`（Step 4a、Express の Step 4）
- `plugins/gate-driven-development/skills/gdd-requirements-gating/SKILL.md`
- `plugins/gate-driven-development/references/brainstorming-steps.md`（Step 17）
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`（model の検査の対象外に足した）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
