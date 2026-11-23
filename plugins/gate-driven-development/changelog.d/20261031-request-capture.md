---
type: minor
---

#### Summary

Claude Code で、依頼と既存コードの突き合わせ agent を起動するときに、main の transcript からユーザーの発言を写した節で `request.md` を作るようにした。これまで `request.md` を書く brainstorming の runner は `/gdd-dev` の引数しか見えず、main が Skill で起動すると main が書いた要約が「依頼の原文」になっていた（10 月の起動は Skill 経由が 411 回、ユーザーが打ったものが 207 回）。

#### Changed

- 新しい hook `hooks/scripts/run-request-capture-hook.sh`（実装は `hooks/scripts/lib/request_capture.py`）を PreToolUse（`Agent`）に登録した。起動は止めない
- 写す範囲は、main の最後の `<gdd-stop reason="done">` か `cancelled`（code の外の行頭にあるもの）より後から、この steering を作った `/gdd-dev` の起動（`state.md` の `Started At` 以前で最後の起動）まで。写すのは、人が打った発言（作業中に打ったものを含む）、打ったコマンド、AskUserQuestion の答え。各発言の前に、その前の発言の後の assistant の文を、文脈と分かる見出しで添える
- Claude Code では、runner は `request.md` を作らず、起動の引数の写し（main が Skill で起動したときは main が書いた文）を `request-notes.md` に書く。hook は既にある `request.md` を書き換えない（上書きせず、途中で落ちても中途半端なファイルを残さない）。`state.md` に `Created In Session` が無いまま `request.md` があるときは、systemMessage で知らせる
- `/gdd-dev` の起動の後から突き合わせまでのユーザーの発言は、節の下に時刻つきで写す
- `state.md` に新しい欄 `Created In Session`（steering を作った session の id。runner が作るときに書く。必須ではない）を足した。hook はこれが今の session の id と一致するときだけ写す。欄が無い・違うとき（別の session で始めたタスクの再開など）、steering を作った起動が transcript に無いとき、時刻が読めないときは、写していないことと理由の見出しの `request.md` を作り（起動の後の発言があれば下に写す）、systemMessage でも知らせる。hook が `request.md` を作らなかったとき（例外・kill switch・開き直していない session など）は、runner が同じ形で作り、突き合わせは unavailable（リスクの段 高）にする
- 写していない旨の `request.md` は「依頼の原文なし」として扱う。突き合わせ agent はリスクの段を高にし、human check は依頼をユーザーに確かめる。steering の書き込み検査（`risk_tier.py`）は、`request.md` が hook の節で始まる通常のファイルでないとき（この形、runner・main が書いたもの、無いとき。Codex・Cursor の steering も含む）、リスクの段の記録によらず `risk-low` の承認を止める（human check で本人の承認を待つ）
- steering の書き込み検査が止める値（email・ローカルの絶対パス・省略の記号・AWS アカウント ID・secret の目印・password などの値）は、語に置き換えて写す
- main と runner の注記（推奨・除外など）は `request.md` に書かず `request-notes.md` に書く。突き合わせ agent・完了前の reviewer・人の確認の「原文」は、この節のユーザーの発言を正本として読む

#### Affected Files

- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/hooks/scripts/run-request-capture-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/request_capture.py`
- `plugins/gate-driven-development/hooks/scripts/lib/risk_tier.py`
- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/gate-status-schema.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/agents/gdd-request-code-crosscheck.md`
- `plugins/gate-driven-development/agents/gdd-completion-reviewer.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/tests/test_request_capture.py`
- `plugins/gate-driven-development/tests/test_risk_tier_reader.py`
- `plugins/gate-driven-development/tests/test_risk_low_approval_guard.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`

#### User Action Required

- なし。長く動いているセッションは、開き直すまで hook が効かず、写していない旨の `request.md` になる

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_request_capture.py plugins/gate-driven-development/tests/test_risk_tier_reader.py plugins/gate-driven-development/tests/test_risk_low_approval_guard.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
