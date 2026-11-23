# ADR: pre-push gate の optout ログ失敗経路を「helper 明示ガード + 呼び出し側 subshell」の 2 段で fail-closed に戻す

- **日付**: 2026-09-07
- **状態**: 採用
- **対象タスク**: `20260907-pre-push-optout-fail-open`
- **リリース**: `plugins/gate-driven-development/CHANGELOG.md` `[0.41.7]`
- **関連**: `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh` の optout 分岐 / `hooks/scripts/lib/self-review-evidence.sh` の `gdd_sr_log_event`

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

## Context

`run-pre-push-gate-hook.sh` の optout 分岐は「escape hatch の使用を記録できないなら push を止める」と
**明示的に fail-closed 設計された唯一の位置**である。その実体である `gdd_sr_log_event` の

```bash
local _state_dir="${GDD_HOOK_STATE_DIR:-${HOME}/.claude/.gdd-hook-state}"
```

は `${HOME}` が未ガードで、`set -u` 下で `HOME` 未設定だとシェルごと即死する。
`if` は `set -e` を抑止するが `set -u` の即死は抑止しないため、`block` に到達せず
escape hatch が**無記録のまま素通り**する。

実測（修正前）:

| 条件 | 結果 |
|---|---|
| `HOME` あり・state dir が書き込み不可（対照群） | rc=0 / stdout に `{"decision": "block", ... optout-log-write-failed ...}` |
| `HOME`・`GDD_HOOK_STATE_DIR` 双方なし | rc=1 / stdout 空 / stderr に `HOME: unbound variable` |

この欠陥は PR 旧#55（v0.41.4、merge gate 側の同型欠陥修正）の独立セルフレビューが実測で発見し、
当該 PR の差分外だったため Known Limitations に記録して持ち越したものである。

既存の `tests/test_pre_push_gate_contract.py` は `_run_hook` が `os.environ.copy()` で必ず `HOME` を
持つため、この面を原理的に踏めなかった。merge gate 側は v0.41.0 で `_run_hook` に `drop_env` を
足してこの面を踏めるようにしてある。

## Decision

**Approach B = helper 明示ガード + 呼び出し側 subshell の 2 段**を採用する。

- **helper**: `_state_dir` の解決を「`GDD_HOOK_STATE_DIR` → `${HOME:-}`（あれば）→ 未解決（空）」の
  3 分岐にし、書き込み条件に `[[ -n "$_state_dir" ]] &&` を足して「記録先未解決」を既存の
  「書き込み失敗」経路へ合流させる
- **呼び出し側**: optout 記録の呼び出しを `if ( gdd_sr_log_event ... ) 2>/dev/null; then` にする
- **テスト**: merge gate 側と同等の `drop_env` を pre-push の `_run_hook` にも足し、`HOME` を落とした
  回帰テストを RED で固定してから修正する（TDD）

人間承認済み（`state.md` § Approved Direction、2026-09-07）。

## Why

- 「記録先が決まらない = 書き込み失敗」に合流させることで、`optout` のみ `return 1` / 他 event は
  `return 0` という既存の非対称戻り値契約（`tests/test_self_review_evidence.sh` の T7-7 / T7-8 が固定）を
  そのまま流用でき、分岐の意味を増やさない
- `/` の書き込み権限に依存しない。guardrail の挙動が実行ユーザーの権限で変わらない
- subshell は helper 実装が将来どう変わっても「失敗 = block」を構造で保つ保険になる（当時）

## Rejected Alternatives

- **Approach A（helper で `${HOME:-}` のみ）**: 1 文字差分で block も出る。却下理由は、`/` が書ける環境
  （root 実行 / 一部コンテナ）で黙って成功し `/.claude/.gdd-hook-state` にログを書いてしまう点。記録先が
  迷子になり、fail-closed の成否が実行ユーザーの権限に依存する。これは本件が直そうとしている
  「暗黙の fail-open」と同種の欠陥である
- **Approach C（呼び出し側 subshell のみ）**: 先行 PR（v0.41.0 / v0.41.4）と見た目が揃う。却下理由は
  (a) helper 本体の地雷が残り次の呼び出し者が同じ罠を踏む、(b) `session-mismatch` / `unresolved-steering` の
  fail-open 経路が `HOME` 未設定時に rc=1 + stderr の `unbound variable` を出し続ける、
  (c) `${HOME:-}` の安全形を helper 側に入れる案の検討という依頼を満たさない

## Consequences

- helper 修正は `gdd_sr_log_event` の production 4 呼び出しすべてに効く
- merge gate 側の `( _mg_log_suppressed ... ) 2>/dev/null || true`（記録して**継続**）と、本件の
  `if ( ... ) 2>/dev/null; then`（記録失敗なら**停止**）は**意図的に非対称**である（当時）。この非対称の理由は
  コード上のコメントと CHANGELOG に残した
- **2 段ガードは AC-1 に対して相互冗長**である。変異注入で実測した（下表）。呼び出し側 subshell は
  現時点では load-bearing ではないが、helper 内の未知の即死要因に対する構造的保険として意図的に残す。
  AC-1 の判別力は変異 (d) が担保する

  | 変異 | 実測結果 |
  |---|---|
  | (a) helper ガード除去 | AC-2 ×2 / AC-4 が RED / AC-1 は GREEN |
  | (b) 呼び出し側 subshell 除去 | AC-1 は GREEN（現時点では冗長） |
  | (c) `HOME` 既定分岐の記録先変更 | AC-8 が RED（判別力あり） |
  | (d) 両ガード同時除去 | AC-1 / AC-2 ×2 / AC-4 すべて RED |

- **`HOME` 未設定環境の復旧手順は「hook プロセス自身の環境変数」でなければならない**。記録先は helper が
  プロセス env から読むだけで、hook が command 文字列から解釈するのは `GDD_SKIP_PRE_PUSH_GATE` のみ。
  したがって `GDD_HOOK_STATE_DIR=... git push ...` のようにコマンド文字列の先頭へ置いても効かない
  （実測で block のまま・記録先も空）。セッション起動前の `export` が正しい。この事実は実装ゲートの
  独立レビューが実測で発見した
- **スコープ外の同種欠陥が 5 箇所残る**: `run-merge-gate-hook.sh` と `run-session-start-hook.sh` に未ガードの
  `${HOME}` が残っている（実測済み）。危険度が異なる（本件だけが fail-closed 判定そのものの消失）ため
  別 PR に送り、CHANGELOG の Known Limitations に対象パス・行番号を残した
