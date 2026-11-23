---
type: minor
---

#### Summary

- compaction の後の自動復帰（SessionStart が `/gdd-dev resume` を案内する注入）をやめた。compaction の hook は main と subagent を見分けられず、subagent にも復帰の案内が入っていたため
- compaction の直後の SessionStart は何も出さない（`[gdd:reboot]`・`[gdd:paused]` も出さない）。PreCompact は state.md に書かず、`state.md` の場所・`Resume From`・`Next Action` の事実だけを要約器に渡す

#### Changed

- `hooks/scripts/run-session-start-hook.sh`: payload の `source` が `compact` なら何も出さずに終わる。直前の turn の失敗の記録は消費せず、次の起動に残す。payload はロケールに依らず UTF-8 で読む。`source` が読めない（payload が無い・JSON が壊れている・python3 が無い）ときは通常の流れ
- `hooks/scripts/run-pre-compact-hook.sh`: state.md への印（`Status: paused`・`CompactSessionId`・`CompactSource`・`AutoCycleCount`・`PausedAt`・`CompactTranscriptOffset`）の書き込みと `.gdd_is_running` の削除をやめた。`Resume From`・`Next Action` を 4 つの行の形（`X:`・`- X:`・`X=`・`- X=`）で読み（以前は `Resume From:` の 1 形だけ）、state.md の場所と合わせて事実の文だけを `systemMessage` で出す。hook が固定で足す文に、委譲・再開の指示は入れない（state.md の値は skill 名でもそのまま渡す）
  - `Next Action` は、build 中（3 つの承認が揃った tasklist.md）は tasklist.md を先に読み、無ければ state.md。`|` 以降は落とす（tasklist.md に値があれば SessionStart と同じ値。UserPromptSubmit は最初の空白でも切る）
  - 場所と値は、不正な UTF-8 を捨て、制御文字を除き、文字単位で切り詰める（値は 128 字）。出力の JSON は非 ASCII をエスケープせず UTF-8 で出す
- `hooks/scripts/lib/compact-resume.sh` を削除した。`GDD_MAX_AUTO_CYCLES` は読まれなくなった
- `references/reviewer-common.md` の常時 High (b) を「Safe Resume の発火判定と、compaction の直後の SessionStart が案内を出さない判定」にした。(a) の routing field から `Status`・`CompactSource` を外した
- `references/state-field-tiers.md`・`references/gate-status-schema.md`・`references/state-schema.json`: 上の 6 つの印を「廃止した hook の印」（`retired_hook_fields`）にした。既存の state.md に残っていても hook は読まない

#### Affected Files

- `hooks/scripts/run-session-start-hook.sh`・`hooks/scripts/run-pre-compact-hook.sh`・`hooks/scripts/lib/compact-resume.sh`（削除）・`hooks/scripts/lib/detect-steering.sh`・`hooks/scripts/validate-steering-write.py`（Core field の欠落の理由文から自動復帰の記述を外した）
- `references/reviewer-common.md`・`references/state-field-tiers.md`・`references/gate-status-schema.md`・`references/state-schema.json`・`references/phase-gate-prechecks.md`・`README.md`
- `hooks/scripts/run-user-prompt-submit-hook.sh`・`hooks/scripts/run-pre-tool-use-plan-reread-hook.sh`（コメントと、Last Handoff Summary が未記入のときの注入文から、compaction の後の復帰の記述を外した）

#### User Action Required

- compaction の後に作業を続けるには、要約に残った状態から続けるか、`/gdd-dev resume` を自分で実行する
- `GDD_MAX_AUTO_CYCLES` を設定していたら、外してよい（読まれない）

#### Validation / Eval Impact

- 追加: `tests/test_compact_without_auto_resume.py`（入口の SessionStart(compact)・PreCompact から、出力と state.md の不変、payload の形、stdin が開いたままの起動、tasklist.md の Next Action、場所の sanitize を確かめる）
- 削除: 自動復帰の書き込み・判定を検査していたテスト 4 本（`test_pre_compact_transcript_offset.py`・`test_compact_resume_writer_and_source.py`・`test_session_start_hook_compact_resume.py`・`test_compact_state_form_invariants.py`）。SessionStart の payload の形と既定ブランチの判定の検査は、上の新しいテストと既存のテストへ移した
- 関係するテスト: 変更したファイル名を参照するテスト
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
