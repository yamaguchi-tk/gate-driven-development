---
type: patch
---

#### Summary

peer turn（直近の発言が別セッションからのメッセージ）の steering の書き込み guard は、`Next Action: cancelled` は止めていたが、`Resume From` を検査していなかった。peer turn で worktree の binding 先に `Resume From: cancelled`（または `done`）を書くと、binding 先が pre-push・merge・pre-PR gate の数え直しから外れ、push・merge を検査せずに通すことがあった。`state.md` の `Resume From` を cancelled・done にする書き込み（行ごとの Write・Edit、値だけを置換する Edit・MultiEdit）も、peer turn では止める。行の正規表現は、ほかの記録と同じく `.steering/` の中のどのファイルへの書き込みにも効く。

peer turn の記録（承認・マージ承認・中止・完了）の値の比較は、gate が読む reader（`gdd_extract_doc_field`）で読んだ値でも行うようにした。python 側の行の規則は、区切りの前の空白や `\v` を含む行も field として読むので、gate が読まない囮の行を先に足しておくと、本物の値を置換する 2 回目の Edit を見逃していた。`Human Check Status: approved later` のように gate が approved と読む値も止める。Write の全文と、`edits` が dict の MultiEdit も値で比べる。reader を起動できないとき、field ごとの読み取りに失敗したとき、書き込みに孤立サロゲートがあるときは、peer turn の書き込みを止める。

`.steering/` を触る書き込み（ApplyPatch の patch、Write の content、Edit・MultiEdit の old_string・new_string など）に LF・CRLF 以外の行区切り文字（`\v`・`\f`・U+2028・単独の CR など）があれば、ターンを問わず止める。guard は patch や既存ファイルをこれらでも行に割る（単独の CR は LF に変えて読む）が、gate の reader は割らないので、その後ろに置いた `Resume From: cancelled`・承認・`Origin Session` の書き換えが検査を外れていた。あわせて、Edit・MultiEdit の書き込み後のテキストを素の置換で射影できないとき（old_string が書き込み前のテキストに見つからないとき、または new_string が空で old_string が改行で終わらず、その後ろに改行が続くとき。Claude Code の Edit は後者で改行ごと消し、行がつながる）は、peer turn の state.md・tasklist.md への書き込みと、`Origin Session` のある state.md への書き込みを止める（guard の射影では「変化なし」に見えても、ツールの適用では記録が変わりうるため）。

merge gate が `.steering/` の外の候補（binding 先）で `steering-ambiguous` に止めるときの文から、binding 先のパスを外した。パスに制御文字があると出力の JSON が壊れて merge が通っていたのと、ほかの block 文と同じくパスを出さない規約に合わせるため。

`gdd_detect_active_steering` の数え直しでは、stale な brainstorming の binding 先も候補に残し、作業中の steering が無ければ binding 先で検査する（放置した brainstorming に bind したままでは、push・merge が検査されなかった）。数え直しで binding 先を候補から外すのは、`Resume From: cancelled`（完全一致）のときだけである。`Resume From: done`（完全一致）の binding 先は done として候補に残る（`.steering/` の外にあり作業中の steering が無いときだけ検査されない）。

#### Changed

- `hooks/scripts/validate-steering-write.py`: peer turn で止める記録に `Resume From` の cancelled・done を足した（行の正規表現と、`state.md` の値の比較）。値の比較を gate の reader で読んだ値でも行い、Write と dict の `edits` も比べ、reader を起動できなければ止める。止めたときの文面を「承認・マージ承認・中止・完了の記録には使えません」にした。`.steering/` を触る書き込みの中身に LF・CRLF 以外の行区切り文字があれば止める（降格しない）。射影できない Edit・MultiEdit（old_string が見つからない、または空の new_string で行がつながる）を、peer turn の state.md・tasklist.md と `Origin Session` のある state.md では止める
- `hooks/scripts/run-pre-push-gate-hook.sh`・`hooks/scripts/run-pre-pr-gate-hook.sh`・`hooks/scripts/run-merge-gate-hook.sh`: `missing-evidence`・completion-check・`pr-url-unrecorded` の文に、使わないステアリングの終え方への案内を足した
- `hooks/scripts/run-merge-gate-hook.sh`: `.steering/` の外の候補で止めるときの文から binding 先のパスを外した
- `hooks/scripts/lib/detect-steering.sh`: `--recount-terminal-binding` のとき、stale な brainstorming の binding 先も候補に残す。binding 先を候補から外す条件のコメントを直した
- `references/self-review-lanes.md`: stale な brainstorming の binding 先も数え直しで候補に残すことを書いた
- `references/phase-progression.md`: 権限境界の列挙に、完了（`Resume From: done`）と `Resume From` の cancelled を足した

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/detect-steering.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/tests/test_peer_turn_write_boundary_contract.py`
- `plugins/gate-driven-development/tests/test_peer_turn_write_boundary_e2e_contract.py`
- `plugins/gate-driven-development/tests/test_merge_gate_bound_terminal_steering.py`
- `plugins/gate-driven-development/tests/test_pre_push_tip_sha_resolution_contract.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_gate_activation.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`

#### User Action Required

- 別セッションから届いたメッセージの直後のターンでは、steering の `Resume From` を cancelled・done にできない（supersede で旧 `state.md` に `Resume From: cancelled` を書く操作も含む）。ユーザー本人のターンで行う
- 放置した brainstorming の steering に worktree が bind したままだと、push・PR 作成・merge は、その steering で検査される（作業中の steering もあれば「複数」で止まる）。使わない steering は `references/self-review-lanes.md` の「使わないステアリングの終え方」に従って終える。pre-push の `missing-evidence`、merge の `pr-url-unrecorded`、pre-PR の completion-check の文にも、この案内を足した
- `.steering/` への書き込み（ApplyPatch・Write・Edit・MultiEdit）に、LF・CRLF 以外の行区切り文字を入れない（止められたら、その文字を取り除いて書き直す。ファイルに既にある文字を消すときは、その文字を含まない全文を Write で書き直す）
- 別セッションのメッセージの直後のターンで state.md・tasklist.md を Edit するとき、および `Origin Session` のある state.md を Edit するときは、old_string をファイルと完全に一致させ、行を消すときは改行まで含める

#### Validation / Eval Impact

- `tests/test_peer_turn_write_boundary_contract.py`: peer turn で `Resume From: cancelled`・`Resume From=cancelled`・バッククォートと注記つき・`Resume From: done` の行を止め、`Resume From: Cancelled` と peer turn でない書き込みは通すこと
- `tests/test_peer_turn_write_boundary_e2e_contract.py`: peer turn で値だけを cancelled・注記つき cancelled・done に置換する Edit を止め、本人のターンなら通し、transcript のパスを開けない（NUL）ときは peer turn とみなして止めること。gate が読まない囮の行（区切りの前の空白・`\v`）を先に足した state.md で、本物の値を置換する Edit を止め、`approved later` と dict の `edits` の置換を止め、reader を起動できないときは止め、本人のターンなら通すこと。ApplyPatch で `\v`・`\f`・単独の CR・U+2028 の後ろに置いた記録を peer turn で止め、`Origin Session` の書き換え（偽の header を含む）を本人のターンでも止め、本人のターンの通常の patch（CRLF を含む）は通すこと。Edit・MultiEdit・Write の中身の `\v`・U+2028・`\f`・単独の CR を本人のターンでも止め、CRLF の Write は通すこと。old_string が見つからない Edit を、peer turn の state.md と、本人のターンでも `Origin Session` のある state.md で止めること。空の new_string で行をつなぐ Edit（2 手目の MultiEdit を含む）を、peer turn の approved・`Resume From` と本人のターンの `Origin Session` で止め、改行まで含めた行の削除は通すこと
- `tests/test_peer_turn_write_boundary_contract.py`（reader）: field ごとの読み取りの失敗と孤立サロゲートで `None` を返し、field が無いだけなら空の値を返すこと
- `tests/test_pre_push_tip_sha_resolution_contract.py`: binding 先が stale な brainstorming でも、作業中が無ければ binding 先で検査し、作業中の trivial の steering があれば `steering-multiple` で止まること。止める文が使わないステアリングの終え方を案内すること
- `tests/test_merge_gate_hook_gate_activation.py`・`tests/test_pre_pr_gate_contract.py`: `pr-url-unrecorded`・completion-check の文が使わないステアリングの終え方を案内すること
- `tests/test_merge_gate_bound_terminal_steering.py`: binding 先のディレクトリ名に制御文字があっても、止める出力が JSON として読め、reason にパスを出さないこと
- 変更したファイルを参照するテスト、`bash plugins/gate-driven-development/tests/validate-plugin.sh`
