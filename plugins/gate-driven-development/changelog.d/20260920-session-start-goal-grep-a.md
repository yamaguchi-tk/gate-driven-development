---
type: patch
---

#### Summary

SessionStart hook の reboot 案内で、Goal（requirements.md の `### 一言` の次の行）が Linux（GNU grep）の UTF-8 ロケールで誤って出ていた。requirements.md に不正な UTF-8 のバイト列があると、GNU grep はその行を binary として出力せず、Goal が `### 一言` になる。BSD grep（macOS）は出力するので、macOS では起きていなかった。GitHub Actions の CI（ubuntu-latest）を足したときに `test_invalid_utf8_in_state_value_does_not_abort_hook_under_utf8_locale` が落ちて見つかった。

#### Fixed

- `hooks/scripts/run-session-start-hook.sh`: Goal の抽出の `grep -A1` を `grep -aA1` にした。`-a` で出るようになった不正なバイトは、`iconv -c -f UTF-8 -t UTF-8` で抽出の時点で落とす。出力の直前の CONTEXT の sanitize（`gdd_truncate_chars`）は python3 が使えないと不正な UTF-8 を落とせないため、そこに頼らない。`iconv` が無いときは Goal が空になり、案内から外れる。BSD grep では、不正なバイトを含まない Goal の出力は変わらない

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/tests/test_session_start_context_json_control_chars.py`

#### User Action Required

- 利用者の操作は不要

#### Known limitations

- 同じ `grep -A1 '### 一言'` が `run-user-prompt-submit-hook.sh:218` と `run-pre-tool-use-plan-reread-hook.sh:37` にもあり、Linux では同じ入力で Goal が `### 一言` になる。直していない。この 2 つは Goal を JSON へそのまま `printf` していて、制御文字や不正なバイトを落とす処理が無い。`-a` だけを足すと、Linux でも macOS と同じく JSON が壊れうる経路が開く。sanitize と合わせて別に直す
- 同じ hook の `Task Size:` の抽出は、macOS でも不正なバイトを含む行で値が空になる。原因は BSD sed（`sed: RE error: illegal byte sequence`）で、`/usr/bin/grep` は行を出す。Linux 固有ではないため、この変更では扱わない
- この修正を守るのは Linux の実行だけである。macOS の BSD grep は `-a` が無くても不正なバイトの行を出すので、`-a` を外しても macOS の全量は通る。Linux の CI（`.github/workflows/plugin-lint.yml`）が入るまでは、`-a` の退行は検出されない。python3 不在時の不正バイトの除去（`iconv`）は macOS でも検出される

#### Validation / Eval Impact

- 再現: `test_invalid_utf8_in_state_value_does_not_abort_hook_under_utf8_locale` が、Linux（Debian trixie、`en_US.UTF-8`）と GitHub Actions の ubuntu-latest で失敗していた（修正前）。修正後は同じ Linux（Docker、2 vCPU 相当）で全量が通る（3338 passed, 6 skipped）
- 追加: `test_invalid_utf8_goal_stays_valid_json_when_python_is_unavailable`（python3 が壊れていて Goal に不正なバイトがあっても、出力が UTF-8 と JSON で読める）。修正前は macOS でも失敗する
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
