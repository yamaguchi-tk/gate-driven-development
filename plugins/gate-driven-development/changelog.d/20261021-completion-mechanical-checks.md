---
type: minor
---

#### Summary

- completion-check の機械検査（完了タスクの `Reviewed by:` 行、`Current Task`・`Pending Tasks` の残り、`Route In Progress`、AC ID の整合、Codebase Health の High）を、1 本のスクリプト `scripts/check-completion-mechanical.py` で回すようにした。読むだけで、結果は `状態<TAB>要求<TAB>gate<TAB>詳細` の行と exit code（不備があれば 1）で返す。ローカルでも CI からでも、steering のパスを渡せば回せる
- completion-check の gate は Part A の Step 0 でこのスクリプトを回し、各 Step が自分の行を読んで判定する。差し戻し先（`Next Action`）は今までと同じ
- main は Completion-Check Template を dispatch する前に同じスクリプトを回し、worklog.md へ移しただけの記録を戻すなど、記録の書き漏れを gate の Round を使う前に直す
- `gdd-completion-reviewer` は、上の機械検査の項目を指摘しない。見るのは横断の整合性と AC の充足

#### Added

- `scripts/check-completion-mechanical.py`
- `hooks/scripts/lib/tasklist_structure.py`（Stop hook の done guard の Check 1 の前段〔行区切り文字・fence の閉じ忘れ・構造行〕。done guard とスクリプトが共有する。挙動は変えていない）

#### Changed

- `skills/gdd-completion-check/SKILL.md`（Part A に Step 0 を足し、Step 2a・3・4・4c-3・5 をその行で判定する）
- `references/subagent-dispatch.md`（§ Completion-Check の前の機械検査を足し、Template の事前確認をその行で確かめる）
- `agents/gdd-completion-reviewer.md`
- `scripts/check-gate-ledger.sh` の reviewed-by 行は、`hooks/scripts/lib/tasklist_parse.py` の `reviewed_by_rows` を呼ぶ（出力は変えていない）

#### Affected Files

- `scripts/check-completion-mechanical.py`
- `hooks/scripts/lib/tasklist_structure.py`
- `hooks/scripts/lib/tasklist_parse.py`
- `hooks/scripts/gdd_stop_hook.py`
- `scripts/check-gate-ledger.sh`
- `skills/gdd-completion-check/SKILL.md`
- `references/subagent-dispatch.md`
- `agents/gdd-completion-reviewer.md`

#### User Action Required

- なし。動いているセッションは、開き直すまで古い skill と agent 定義で動く

#### Validation / Eval Impact

- `tests/test_check_completion_mechanical.py`（行ごとの変異、check-gate-ledger.sh との一致、fail-open の 3 ケース）
- `tests/test_fence_policy_single_source_contract.py`（許可リストに `tasklist_structure.py` を足し、stale の検査を `strip_fenced_lines_marked(` の呼び出しにも当てる）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
