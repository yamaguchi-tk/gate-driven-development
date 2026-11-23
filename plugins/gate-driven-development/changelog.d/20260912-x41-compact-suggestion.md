---
type: minor
---

#### Summary

Stop hook に、GDD ワークフローの区切り（要件承認 / 実装開始 / PR 作成 / impl-gate Round 3）で手動 `/compact` に使える 1 行を `systemMessage` で提案する機能を追加した（X-41）。提案は `systemMessage` にしか触れず、`decision` / `reason` / 終了コードを変えない（`systemMessage` はユーザー表示専用でモデル文脈には入らないためトークンコストは 0）。同じ steering の同じ区切りは 1 回だけ提案する。

#### Added

- `hooks/scripts/lib/compact_suggestion.py`: 区切り判定（`detect`）と `systemMessage` への合流（`merge_into_output`）、Stop hook 本体をラップして呼ぶ `run`
- `tests/test_compact_suggestion_contract.py`: 4 区切りの判定・出力合流・Stop hook 経由の統合テスト

#### Changed

- `hooks/scripts/gdd_stop_hook.py`: `main()` の呼び出しを `compact_suggestion.run(main, _bound_steering_file)` でラップし、session・runtime・transcript の guard を通った直後に `compact_suggestion.mark_eligible()` を呼ぶ（既存の `decision` / `reason` / 終了コードは変更なし）。提案を出すのは本体がこれらの guard を通った停止だけで、別セッション・別 runtime・transcript の無い停止には出さず、1 回分の記録も使わない（`references/stop-hook-structured-markers.md` § Transcript Missing Suppression と揃える）。guard を通った後で本体が黙って抜ける停止（継続意図が見えない停止など）には出る。`session_id` が空の Cursor の state では、本体と同じく会話を区別しない
- `hooks/scripts/lib/compact_suggestion.py`（PR レビュー指摘対応）:
  - 区切り②（実装開始）の発火条件を `Human Check Status` / `Design Review Status` の 2 つから、`Requirements Review Status` を含む 3 つすべて（`all_approved`）に揃えた。あわせて、3 つが揃うまでは `Next Action` を state.md からしか読まないようにした（旧実装は state.md に `Next Action` が無いと tasklist.md の古い値へ fallback し、要件未承認のまま誤発火していた）
  - 区切り④（Gate Rounds = 3）の判定を、`## Current Task` 節全体から最初の値を拾う方式から、task 見出しごとのブロック単位に変えた。並列 batch で複数 task が同節に並ぶと、旧実装は Task ID と Gate Rounds を独立に取得しており、取りこぼし・誤記録（別 task の ID で記録）が起きていた
  - task 見出しのブロック境界に、正準形 `### Task: T-1 <name>`（`references/task-breakdown-steps.md` § 見出しの正準形）を追加した。互換の箇条書き形式（`- T-1 ...`）のみ認識していた旧実装は、正準形で書かれた通常の tasklist.md では区切り④が発火しなかった
  - task 見出しの判定を `lib/tasklist_parse.py` の共有受理面へ揃え、既存tasklistの `### Task 1: T-1 ...` / `- Task: T-1 ...` でも区切り④が発火するようにした。compact 提案が従来受理していた `- T-1 ...` / `- **T-1 ...**` も維持する

#### Affected Files

- `hooks/scripts/lib/compact_suggestion.py`（新規）
- `hooks/scripts/gdd_stop_hook.py`
- `tests/test_compact_suggestion_contract.py`（新規）

#### User Action Required

- なし。提案は systemMessage の追記のみで、既存の自動継続・done guard・block 判定は変わらない

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 追加 contract test: `test_compact_suggestion_contract.py`
