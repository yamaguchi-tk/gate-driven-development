---
type: patch
---

#### Summary

- compact 自動復帰は、subagent の compaction でも発火する。Claude Code 2.1.261 では PreCompact と SessionStart(compact) の入力に agent_id が無く、hook からは main と見分けられない。判定は変えず、SessionStart が注入する文の側で、subagent が従わないようにした

#### Changed

- `[gdd:compact-auto-resume]` の自動復帰の案内の先頭に、受け取った側を振り分ける固定文が付く。メインは以下に従い、subagent はその文を含め以下を無視する
- サイクル上限に達したときの警告は、「手動で /gdd-dev resume を実行してください」から「利用者が指示するまで、GDD のワークフローを再開しないこと」に変わる。main が警告に従って再開し、上限が効かなくなることを防ぐ
- `GDD_MAX_AUTO_CYCLES` が数字だけの 10 進整数でないとき（`1.5`・`40x`・`abc`・負の値・`+5`・前後の空白・`0x10` など）は 0 として扱い、自動復帰しない（警告に `GDD_MAX_AUTO_CYCLES=0` と出る）。これまでは `1.5`・`40x` で上限の比較が偽になって上限を飛ばすか、`abc` で hook が出力なしで終わっていた。設定し直すときは数字だけで書く。`AutoCycleCount` と `GDD_MAX_AUTO_CYCLES` の先頭の 0 は 10 進として読む（これまでは 8 進として扱われ、`010` は 8 になっていた）

#### Affected Files

- `hooks/scripts/lib/compact-resume.sh`
- `hooks/scripts/run-session-start-hook.sh`
- `tests/test_compact_resume_writer_and_source.py`
- `tests/test_compact_state_form_invariants.py`
- `tests/test_session_start_hook_compact_resume.py`

#### User Action Required

- subagent が `[gdd:compact-auto-resume]` の自動復帰の案内を受け取ることは、まだ起こりうる。固定文の subagent の節に従って無視してよい。サイクル上限の警告には固定文が付かない（誰に対しても再開しないよう伝える文である）
- サイクル上限に達したら、続けるかを判断してから `/gdd-dev resume` を手動で実行する。`AutoCycleCount` を戻す書き手は無いので、自動復帰を戻すには `GDD_MAX_AUTO_CYCLES` を上げるか、`AutoCycleCount` を手で戻す
- main の compaction 中に subagent が印を消費すると、その回の自動復帰は起きない。`/gdd-dev resume` を手動で実行する

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` と `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_compact_resume_writer_and_source.py` に追加: `test_real_entry_resume_context_tells_subagent_not_to_resume`・`test_cap_warning_tells_nobody_to_resume`・`test_notice_keeps_main_resume_firing_and_counting`・`test_notice_is_not_emitted_when_resume_does_not_fire`・`test_unreadable_max_cycles_stops_auto_resume`・`test_leading_zero_values_are_decimal`・`test_valid_max_cycles_above_count_still_fires`
- hook を起動する 3 つのテストの env から、host の `GDD_MAX_AUTO_CYCLES` を落とした
