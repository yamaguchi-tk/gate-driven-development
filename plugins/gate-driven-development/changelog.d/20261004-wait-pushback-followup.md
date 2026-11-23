---
type: patch
---

#### Summary

Stop hook が background の dispatch の起動応答（`Async agent launched successfully. ... agentId:`）を、tool result の本文の先頭にあるものだけで読むようになった。これまでは、同期の subagent（Agent・Task）の回答の途中にある引用も起動応答とみなし、その dispatch を「動いている background」として、loop state を消す停止の押し返し・期限 watchdog・継続の判定に使っていた。

background の dispatch が動いている間に loop state を消す停止を押し返す判定を、Stop hook のほかの停止の検査（「👤 次にすること」見出しの要求・HITL lint・done guard）より先に行うようにした。待つつもりで止められたとき、最初の block が見出しの要求ではなく待ち方の案内になる。`external-review-waiting` のポーリング上限での `blocked` への昇格も、ほかの検査より先に行う（block の文面の reason が `blocked` になる）。

`references/stop-hook-structured-markers.md` と `references/state-machine.md` に、background の返りを tool result として拾わないこと、この押し返しと飛ばす条件、期限 watchdog の段、tool result の marker は tool の種類を問わず最後のものを読むことを書き、許可 reason の一覧を 8 つにそろえた。README の Stop の行に、目印なしの待ち・この押し返し・期限 watchdog を書いた。継続契約の「ONE assistant turn」に、background の dispatch を待つときは目印なしで turn を終えてよいことを足した。formal gate の Template を `general-purpose` で起動し直すときも、`run_in_background` と待ち方の手順を引き継ぐと書いた。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/lib/wait_watchdog.py`
- `plugins/gate-driven-development/hooks/scripts/run-background-dispatch-gate-hook.sh`
- `plugins/gate-driven-development/scripts/setup-gdd-loop.sh`
- `plugins/gate-driven-development/references/stop-hook-structured-markers.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/tests/test_wait_watchdog.py`
- `plugins/gate-driven-development/tests/test_hooks_toplevel_trailing_newline.py`
- `plugins/gate-driven-development/tests/test_background_dispatch_gate.py`

#### User Action Required

- なし（継続契約の追記は、この版の後に始めた `/gdd-dev` から届く）

#### Validation / Eval Impact

- `tests/test_wait_watchdog.py`: 引用された起動応答を background とみなさないこと、先頭の空白・list の content の起動応答は読むこと、見出しの無い停止と done guard に当たる done でも押し返しが先に出ること、昇格した reason を見出しの要求も使うこと、state を残す停止を押し返さないこと、押し返しを飛ばしたときに見出しの要求に落ちること、`overdue_reason` の type の空白の正規化
- `tests/test_hooks_toplevel_trailing_newline.py`: background-dispatch-gate を、toplevel が改行で終わる repo で止める側に倒す hook の一覧に入れ、hook ごとに止める形（block か deny）を見る
- 直近の transcript の tool result で、変更の前後の正規表現が起動応答とみなす件数を比べた（数値は PR 本文）
- `bash tests/validate-plugin.sh`
