---
type: patch
---

#### Summary

- `plugins/gate-driven-development/tests` の性能回帰テスト 5 本が `-n auto` 並列 + 外部 CPU 負荷下で flaky になっていた問題を修正した。判定を「CPU 時間（厳・現状閾値据え置き）＋ 壁時計 backstop（緩・hook timeout ÷ 2）」の二本立てに変更し、検出力を落とさずに安定させた（X-37）。

#### Changed

- `tests/_timing_budget.py`（新規）に CPU/壁時計計測の共有 contextmanager `timing_budget()` と、`hooks/hooks.json` から timeout 秒数を導出する `hook_timeout_seconds()` を追加した
- `tests/_root_branch_guard_support.py` の `run_root_branch_guard` に `timeout` キーワード引数（既定値はモジュール定数 `GUARD_HOOK_TIMEOUT_SEC`）を追加し、ハング退行時に回帰スイート全体を止めないようにした
- `test_root_branch_guard_contract.py` / `test_merge_gate_followup_findings.py` / `test_merge_gate_hook_command_parse.py` の計 5 本の性能回帰テストの判定を `timing_budget()` ベースの二本立てへ置換した。うち 2 本（`test_root_branch_guard_contract.py`）は入力長を 2 倍にし、mutation 実測で退行検出力の余裕が AC-8(b) の要求（閾値の 3 倍以上）を満たすことを確認した（実測値は PR 本文に `at <sha>` つきで記載する）

#### Fixed

- CPU 律速の性能退行に対する検出力（CPU 側閾値）は一切緩めていない。壁時計の単独上限のみを hook timeout の半分（5 秒）へ緩め、並列・高負荷環境由来の flaky を解消した

#### Affected Files

- `plugins/gate-driven-development/tests/_timing_budget.py`（新規）
- `plugins/gate-driven-development/tests/_root_branch_guard_support.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_contract.py`
- `plugins/gate-driven-development/tests/test_merge_gate_followup_findings.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_command_parse.py`（`import time` は origin/main が追加した既存テストが引き続き使用するため維持）
- `plugins/gate-driven-development/tests/test_timing_budget_contract.py`（新規。`_timing_budget.py` の fail-loud 分岐と、CPU 計測式の両項（`time.process_time()` による自プロセス CPU 捕捉 / `RUSAGE_CHILDREN` による孫プロセス CPU 捕捉）を mutation で固定する契約テスト）
- `docs/adr/2026-09-12-x37-test-timing-flakiness.md`（repo-root。新規。判断を ADR に蒸留した）
- `docs/learned-patterns.md`（repo-root。本タスクの学びを 4 件追記した）

#### User Action Required

- なし。テストのみの変更で、hook の実装本体・contract には影響しない

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` で全体回帰を実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` を実行した
- mutation 実測（production hook を一時的に退行実装へ差し替えて検証、直後に復元）で、対象 5 本すべてが退行を検出できることを確認した。検出 channel の内訳: 旧#1〜旧#3 は復元前の実行が hook の subprocess timeout（`TimeoutExpired`）に先に抵触して検出、旧#4 は直接計測（pytest 経由は乗算的な膨張が観測されたため直接測定で代替）、旧#5 のみ CPU アサーション（`AssertionError`）で直接検出。`seen` 重複排除除去形の退行は検出できるが、二重走査形の退行は依然未検出のまま（既知の限界として据え置き。ADR § Consequences）。`_timing_budget.py` の計測式（CPU 計測式の両項 — `time.process_time()` による自プロセス CPU 捕捉と `RUSAGE_CHILDREN` による孫プロセス CPU 捕捉 —、および CPU/壁時計の分離）自体も、項ごとに独立した mutation で固定した。実測は PR 本文に `at <sha>` つきで記載する
