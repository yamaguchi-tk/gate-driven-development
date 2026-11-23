---
type: patch
---

#### Summary

自走上限に注記を付けた書き込み（`- 自走上限: マージまで（事前回答 …）`、`human:マージまで（…）`）が、main に知らされないまま残り、自走のマージに入れなかったのを直した。steering の書き込み hook が、Write・Edit・MultiEdit で書いた後の `state.md` を見て、`references/post-merge-qa.md` § 入口の形（`自走上限` と `Human Check Status` の行が 1 行ずつ、`- 自走上限: <値>` の形、evidence が `human:<値>` と完全一致、値が表の値）を満たさない理由を `additionalContext` で返す。書き込みは止めない。見るのは、自走上限か `human:` の evidence が `マージまで`・`マージ・デプロイ・QA まで` で始まるときだけである。注記の文面は、範囲を狭める条件なら値を `PR 作成まで` にし、出所・日付・委任先だけなら `worklog.md` に移す、と案内する。これまでの警告は、書き込み前の内容を読んで利用者の端末（`systemMessage`）にだけ出ていた。ApplyPatch ではこれまでどおり lint の警告を出す。

未リリースの `20261002-pre-answer-delegation.md` の「hook は書き込み前の state.md を lint するので、警告は次の state.md の書き込みで出て…」と、`20261002-pre-answer-followup.md` の「evidence の警告は hook の systemMessage で利用者の端末に出て main には届かない」を置き換える（Write・Edit・MultiEdit の書き込みについて）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_value.py`
- `plugins/gate-driven-development/hooks/scripts/lib/advisory_lint.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/references/human-check-template.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_autonomy_value_notes.py` を足した
- `tests/test_pre_answer_contract.py` の警告の文面と届く先を、新しい挙動に合わせた
- `bash tests/validate-plugin.sh`
