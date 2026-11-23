---
type: patch
---

#### Summary

SessionStart hook の `[gdd:shadow-marker]` を撤去したことに合わせて、会話 routing の replay lint から `shadow_marker` の入力を扱う分岐を消した。あわせて、SessionStart hook の前回異常終了レポートのコメントが、全出力点が同じ 3 段 sanitize を通ると書いていた過大な断定を直した。配布物の hook の挙動は変わらない。

#### Changed

- `scripts/lint-conversation-routing-replay.py` は、fixture の `context.shadow_marker` を読まない。以前は `shadow_marker: true` のとき `gdd_status_required`（`gdd-status` への routing）を返していた。今は他の入力だけで routing を決める。`requires_status_or_resume` は、primary ではなく route が `gate-driven-development:gdd-status` を含むことを求めるようにした（以前は primary が `gdd` か `gdd_status_required` なら通り、`expected.primary` と同じことしか見ていなかった）
- `tests/fixtures/conversation-replay/` から shadow 用の fixture 2 件（`shadow-marker-temp-continue.json`・`shadow-marker-planning-amendment-followup.json`）を削除し、残りの fixture と `tests/checks/lint-scripts-functional.sh` の smoke fixture から `"shadow_marker": false` を外した
- `hooks/scripts/run-session-start-hook.sh` のコメントを、3 段 sanitize を通る出力点（compact 復帰・post-merge・active / 複数 steering の案内）と、通らない出力点（サイクル上限の警告はエスケープ 2 段、既定の案内は固定文）に分けて書き直した（コメントのみ）

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-conversation-routing-replay.py`
- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`（コメントのみ）
- `plugins/gate-driven-development/tests/fixtures/conversation-replay/*.json`
- `plugins/gate-driven-development/tests/checks/lint-scripts-functional.sh`
- `plugins/gate-driven-development/tests/test_conversation_replay_fixtures.py`
- `plugins/gate-driven-development/tests/test_p0_p1_operational_hardening_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 新規 contract test: `tests/test_conversation_replay_fixtures.py` の `ShadowMarkerInputIgnoredTests`（入口は replay lint の CLI。`shadow_marker: true` があっても、承認前の計画変更は `gdd-requirements-amendment` に、marker の無い「続けて」は `gdd-pre-workflow-brainstorming` に routing される。`requires_status_or_resume` は status 以外の route を落とす）
- `test_p0_p1_operational_hardening_contract.py` の登録確認で、`gdd_status_required` の代わりに `requires_status_or_resume` を見るようにした
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
