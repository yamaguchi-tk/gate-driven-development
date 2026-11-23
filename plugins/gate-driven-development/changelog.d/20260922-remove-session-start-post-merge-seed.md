---
type: minor
---

#### Summary

SessionStart hook から、post-merge continuation marker を読んで `[gdd:post-merge-auto-continue]`（`/gdd-dev resume`）を注入し marker を削除する経路を撤去した。この経路は `${HOME}/.claude/gdd-post-merge-continuation.json` を見ていたが、marker を書く `gdd_stop_hook.py` は `<project root>/.claude/` に書く。project root が `${HOME}` と一致する起動を除いて書き手の出力先と読み手のパスは一致せず、実データでの注入は 0 件だった。marker を読む経路は UserPromptSubmit の cue 注入と stop hook の post-merge block lane の 2 つに戻る。

#### Changed

- `hooks/scripts/run-session-start-hook.sh` から `_post_merge_seed_check` とその呼び出しを削除した。SessionStart の出力点は 6 箇所から 5 箇所になった。`GDD_POST_MERGE_SEED_FILE` 環境変数（テスト用の上書き）も無くなった
- 撤去して「パスを project root に合わせる」を選ばなかった理由は 2 つある。(1) SessionStart が marker を `rm -f` するため、marker の存在を入口にしている stop hook の block lane と UserPromptSubmit の cue 注入が、次のセッション開始で入口ごと消える。(2) marker は PR 作成時に `status: "pending_manual_merge"` として書かれ「マージ済みか」を持たないので、PR が open の間ずっと `/gdd-dev resume` を注入することになる
- compact 自動復帰・Safe Resume・`[gdd:reboot]`・`[gdd:paused]`・複数 steering の `[gdd:warning]`・既定の案内は変えていない

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/tests/test_session_start_no_post_merge_seed.py`（新規）
- `plugins/gate-driven-development/tests/test_session_start_hook_compact_resume.py`
- `plugins/gate-driven-development/tests/test_session_start_last_turn_failure_contract.py`
- `plugins/gate-driven-development/tests/test_p0_p1_operational_hardening_contract.py`
- `plugins/gate-driven-development/tests/test_safe_resume_session_id_trim.py`
- `plugins/gate-driven-development/tests/test_session_start_context_json_control_chars.py`
- `plugins/gate-driven-development/tests/test_session_start_no_shadow_marker.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`（コメントのみ）
- `plugins/gate-driven-development/tests/test_stop_hook_bind_resolution_contract.py`（docstring のみ）

#### User Action Required

- なし

#### Validation / Eval Impact

- 新規 contract test: `tests/test_session_start_no_post_merge_seed.py`
- 削除したテスト: `test_session_start_hook_compact_resume.py` の `_run_post_merge_seed`・`test_post_merge_seed_consumed_and_deleted`・`test_post_merge_seed_not_injected_when_absent`・`test_post_merge_seed_not_injected_when_next_task_hint_empty`・`test_post_merge_seed_is_hermetic_against_ambient_steering`・`test_post_merge_seed_does_not_touch_real_hook_state_dir`、`test_session_start_last_turn_failure_contract.py` の `test_post_merge_seed_path_prepends_marker`、`test_p0_p1_operational_hardening_contract.py` の `test_session_start_invalid_seed_json_noop`。hook state dir の隔離は `_run()` 側の `test_run_helper_does_not_touch_real_hook_state_dir` が引き続き担う
- 出力点の構造 pin（`test_every_shipped_output_point_is_wired`）を 6 → 5 に更新した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
