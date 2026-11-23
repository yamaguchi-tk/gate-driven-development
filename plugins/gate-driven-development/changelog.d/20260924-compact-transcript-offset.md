---
type: minor
---

#### Summary

PreCompact hook が、state.md に `CompactTranscriptOffset`（その時点の main transcript のバイト長）を書くようになった。subagent の compaction でも PreCompact と SessionStart(compact) は走り、hook の入力には main と見分ける手がかり（`agent_id`）が無い（Claude Code 2.1.280）。main の compaction は main transcript（`<session>.jsonl`）に `compact_boundary` の行を足し、subagent の compaction は `<session>/subagents/` の下の transcript に足す。そこで、後の hook が「このバイト長より後ろに main transcript の境界の行があるか」で main の compaction かを確かめられるようにした。読む側の関数も足したが、compact 自動復帰の発火の判定にはまだつないでいない。state.md が既定の形（hook が書き換えられる形の行）なら、自動復帰の振る舞いは変わらない。

#### Added

- state.md の hook 所有の欄 `CompactTranscriptOffset`。値は 10 進の非負整数か `unknown`
  - PreCompact が書く
  - 次のときは `unknown` を書く: session id（`CLAUDE_CODE_SESSION_ID`）が取れない、stdin の payload が無い・壊れている、`transcript_path` が絶対パスでない、`/subagents/` を含む、ファイル名が `<CompactSessionId>.jsonl` でない、通常ファイルでない、python3 が無い
  - 同じ session の印（`CompactSource: pre-compact` と `CompactSessionId` の一致）が消費されずに残っていて、前の値が 10 進の数字なら、前の値を保つ
- `hooks/scripts/lib/compact-resume.sh` の関数
  - `gdd_pre_compact_transcript_offset`: PreCompact の payload からバイト長を返す
  - `gdd_compact_boundary_after_offset`: 指定のバイト長より後ろに `compact_boundary` の行があるかを答える
  - 2 つとも同じ述語で transcript を受け付ける
  - 境界は、行の JSON の `type` / `subtype` で判定する
  - 判定できないときは、境界が無い側（非 0）を返す

#### Changed

- PreCompact が `CompactTranscriptOffset` を書けないとき（state.md に書き換えられない形の行があるときなど）は、`CompactSource` を `pre-compact` に書き換えず、systemMessage で知らせる。ほかの印を書けないときと同じ扱いで、今回の compaction の印は立たない（前の印が `pre-compact` のまま残っていれば、それで発火しうる）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-compact-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/compact-resume.sh`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/state-schema.json`
- `plugins/gate-driven-development/tests/test_pre_compact_transcript_offset.py`（新規）
- `plugins/gate-driven-development/tests/test_always_high_scope_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 新規 contract test: `tests/test_pre_compact_transcript_offset.py`（実際の入口 `run-pre-compact-hook.sh` から、書いたバイト長で main の compaction の境界を見つけ、subagent の compaction では見つけないことを含む）
- `tests/test_always_high_scope_contract.py` の `HOOK_OWNED_OUTSIDE_RESUME_FIELDS` に `CompactTranscriptOffset` を足した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
