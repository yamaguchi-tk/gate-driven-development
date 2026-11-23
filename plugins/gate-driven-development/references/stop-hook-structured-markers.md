# Stop Hook Structured Markers

> **所有**: Stop hook の停止判定、自然文 fallback の制限、fail-closed エラー処理
> **参照元**: `hooks/scripts/gdd_stop_hook.py`, `tests/test_stop_hook_unit.py`, `tests/test_stop_hook_state_unit.py`, `tests/test_stop_hook_continuation_unit.py`, `tests/test_stop_hook_stop_reason_unit.py`, `tests/test_stop_hook_e2e.py`, `tests/test_stop_hook_e2e_block_content.py`, `tests/test_stop_hook_validate.py`

GDD Stop hook は、自然文の雰囲気ではなく構造化マーカーを主信号にする。

## Primary Stop Signal

停止・一時停止・完了は必ず `<gdd-stop reason="...">` で表す。

許可 reason: `hooks/scripts/lib/constants.py` の `ALLOWED_STOP_REASONS`（一覧と意味は `references/output-format.md` § `<gdd-stop reason>` の許容値）

`done` は tasklist / verification / Route In Progress を検証してから許可する。検証できない場合は fail-closed で block する。

## Marker Sources

Stop hook が primary として読む場所:

1. 最後の assistant text 内の `<gdd-stop ...>`
2. 最後の tool result（tool の種類を問わない）内の `<gdd-stop ...>`

これ以外の自然文だけで、停止の reason を推定しない（`human-check-waiting` だけは下の Markerless State Fallback で読む）。

background で起動した dispatch の返りは完了通知（user text）で届き、tool result ではないので、2 の経路では拾わない。turn の途中に届いた完了通知は、queue-operation の remove の content か attachment（type: queued_command）の prompt にだけ残ることがあり、これも完了通知として読む（queue-operation の enqueue だけのものは配達待ちなので読まない）。background の dispatch（起動応答の agentId があり、完了通知も、host が動いていないと答えた `TaskStop` の結果〔本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`〕もまだのもの）が動いている間は、loop state を消す停止（`done`・`blocked`・`cancelled`・`staging-verification-blocked`）を、どちらの経路で決まっても、見出しの要求・HITL lint・done guard より先に押し返す（`lib/wait_watchdog.py` の `state_clear_guard`。押し返しは、連続 block の上限を超えたとき・直近の実会話ターンが peer のとき・判定の例外のとき・state に数を書けないときは飛ばす。マージ待ちの押し返しと期限 watchdog は、これより前に走る）。期限 watchdog（期限 timer の有無と上限）は `references/subagent-dispatch.md` § Reviewer Input and Time Budget。marker の無い停止でも、完了の信号がまだ無い subagent の dispatch か、直近 2 時間 10 分（マージ待ちの押し返しと同じ窓）に起動してまだ終わっていない待ちの background の Bash か、同じ窓に SendMessage で再開して、その後に完了通知も、host が動いていないと答えた `TaskStop` の結果もまだの agent があれば、`/gdd-dev` の継続を押し返さない（`gdd_stop_hook.py` の `_continuation_intent_guard`）。再開は、host が SendMessage の結果の行に書く `toolUseResult`（`success` が true で、`resumedAgentId` が空でない str）だけで読む（`lib/transcript.py` の `any_resumed_agent_running`）。待ちに数えるのは、期限 timer の単独の `sleep <秒>` と、`scripts/wait-until.py` を起動するコマンドだけである（`lib/transcript.py` の `_WAIT_COMMAND_RES`）。ほかの background の Bash（テストの実行、`until … sleep` の loop など）を待って止まると、押し返す。

## Fallback Labels

各 fallback には `permanent` / `transitional` のラベルと delete condition を付ける。

| fallback | label | delete condition |
|---|---|---|
| assistant text `<gdd-stop>` | permanent | なし。primary stop signal |
| 最後の tool result `<gdd-stop>`（tool を問わない） | permanent | subagent 出力が常に main assistant text へ echo される host 契約ができるまで維持 |
| markerless `Resume From=human-check-waiting` + human-check surface | transitional | 全 phase skill が main assistant text に `<gdd-stop reason="human-check-waiting">` を確実に出す contract test を持ったら削除 |
| user intent continuation guard | permanent | stale active state が unrelated 会話を hijack しないため維持 |
| phase-name heuristic text match | transitional | 全 phase transition が `<gdd-phase>` を出し、scenario evals で resume / model routing に不要と証明できたら削除 |

## Markerless State Fallback

`state.md` の `Resume From=human-check-waiting` は、subagent → main session の marker 伝播漏れを救うための fallback である。ただし state だけでは古い task を拾う危険があるため、以下をすべて満たす時だけ許可する。

- current worktree の `.steering/<task>/state.md` である
- `Resume From=human-check-waiting` である
- 直近 assistant text または tool result が human-check surface に見える
  - `<gdd-stop reason="human-check-waiting">`
  - `承認ポイント`
  - `判断ポイント`
  - `整理した要件`
  - `実装する方法・内容`
  - `検証する方法・内容`
  - `OKでも許可されないこと`
  - `人間に戻す条件`

単に「承認をお願いします」だけでは markerless state fallback を許可しない。

## Fail-Closed Error Handling

active GDD state があるのに Stop hook が必要情報を読めない場合、state を削除せず block する。

fail-closed 対象:

- `.claude/gdd-dev.local.md` の frontmatter 破損
- `iteration` が数値でない
- `done` guard が tasklist / verification を読めない

この場合は `.gdd/hook-errors.log` に JSONL で記録し、`gdd-status` の Hook Errors で見えるようにする。

### Transcript Missing Suppression

`transcript_path` が無い、または存在しない場合は **block payload を返さない**。`.gdd/hook-errors.log` に記録し、stderr に短い警告を出して silent exit する。

理由: `transcript_path` が無い状態では、直近ユーザー入力が GDD 継続意図か、副会話 / unrelated chat かを判定できない。ここで `GDD Stop hook integrity failure` を systemMessage として返すと、root や副会話に残った stale `.claude/gdd-dev.local.md` が毎ターン警告を出し続ける。状態は削除せず保持し、明示的な `/gdd-dev` で再開できるようにする。

### Transcript Read Errors

transcript の 1 block・1 行が例外で読めないときは、その block・行だけを読み飛ばし、ほかは読む。読み飛ばした数と最初の例外を `.gdd/hook-errors.log` に記録する（Stop のたびに 1 件）。直近の人間のターンが peer かを判定する処理が例外になったときは、block payload を返さず、peer のときと同じく自動継続を抑止し、例外を記録する。post-merge の事前判定が例外になったときも、記録して何もしない。

## Why

自然文 fallback はモデルの出力スタイル変更、日本語/英語混在、古い state の混線に弱い。構造化マーカーを主信号にし、markerless fallback を human-check recovery に限定することで、Stop hook の安全性と再開性を両立する。
