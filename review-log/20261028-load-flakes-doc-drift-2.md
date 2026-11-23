---
lane: L1
pr: 598
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fa1e1717c35f7bef49debfc17d3126bef87ad537 | 0 | 1 | 0 | 2026-10-28T10:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 67994674f1b40386a70b6d78ae93388b45e61cf0 | 0 | 0 | 0 | 2026-10-28T11:10+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | fd2ac0c891b11158e77dec037f57f35583f345a5 | 0 | 1 | 0 | 2026-10-28T11:40+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 6c0662c4df9415b2cdb5bf3df8ef0cb5c55d4c94 | 0 | 0 | 0 | 2026-10-28T12:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 設計: 変えない（文書の 1 項の書き方の誤りで、穴の種類を生む設計の決定が無い）。learned-patterns:17 の注記が、pre-push gate・pre-PR gate の helper も hang_guard_seconds にしたと読め、依頼 1（実態より広い書き方を直す）が届いていない。替えた helper とテストを日付つきで書き、正本を 2 つの断片に向けた（Opus・Fable とも直す案。commit: 67994674f1b40386a70b6d78ae93388b45e61cf0） |
| r1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR merge-gate-quoted-operator:69 の括弧が、merge gate の hook を起動するテスト全部の打ち切りを HANG_GUARD と言い切る（test_merge_gate_ir_carry.py:100 は 30 秒）。「既定の」が抜けている |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary と PR 本文の「hook を起動するテストの打ち切りを hang_guard_seconds にした」が、依頼 1 と同じ型の広い書き方 |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の learned-patterns の行の説明が、注記に書いた中身より狭い（r1-1 の修正で書き直した。commit: 67994674f1b40386a70b6d78ae93388b45e61cf0） |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 注記の「X-37 の T は壁時計 backstop も見る」の「も」が、T も CPU 時間を timeout と比べると読める（r1-1 の修正で文ごと消えた） |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 注記が merge gate の変更を 2026-10-27 に入れ、ADR の 2026-10-26 と食い違う（r1-1 の修正で日付を分けた） |
| r1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | test_merge_gate_hook_quoted_operator.py の docstring の「渡す 60 秒と同じ値」は、merge gate の timeout が 10 秒のときだけ成り立つ |
| r2-1 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 設計: 変えない（注記の 1 文の書き漏れ）。依頼 2（見出しは古い規定のまま読める）について、書き直した注記が見出しの原則が今も有効かと今の規定の正本を書かなくなった。注記の頭に、原則を今どこに当てていないかと正本を書いた（commit: fd2ac0c891b11158e77dec037f57f35583f345a5） |
| r2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「打ち切りを延ばしたテストは、本番の timeout に収まるかを見なくなる」が全称の言い過ぎ。CPU 時間を timeout と比べるテストや backstop を持つテストが残る |
| r2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | pre-PR gate を _run_pre_pr の 20 秒だけで書き、契約テストの _run_hook の打ち切りなしと Stop hook の helper の 60 秒の literal を挙げていない |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 注記が全量として指す 2 つの断片の Summary が、注記より広く書いている |
| r2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 注記が指す changelog.d の断片のパスは、次のリリースで消える |
| r2-6 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | r1-2 の再掲。ADR merge-gate-quoted-operator:69 の括弧に「既定の」が無い |
| r2-7 | 独立-2 | advisory | no | self-inflicted | style | accepted | 注記の中のパスの基準（repo 直下と plugin から）が混ざっている |
| r3-1 | 独立-3 | medium | no | self-inflicted | request-scope | fixed | 設計: 変える（外れる helper を列挙する書き方をやめ、正本をコードにする。3 巡とも列挙の漏れの指摘だった）。注記の「見出しの原則は merge gate と root branch guard の helper の既定に当てていない」が外れる箇所を 2 つに限り、ほかの helper では見出しが今の規定に読める。原則が今の規定ではないことだけを書いた（commit: 6c0662c4df9415b2cdb5bf3df8ef0cb5c55d4c94） |
| r3-2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 注記が今の規定の正本とした ADR X-37 の節は root branch guard しか書かず、docstring とも範囲が違う（r3-1 の修正で正本をコードにした） |
| r3-3 | 独立-3 | low | no | self-inflicted | style | accepted | 1 つの注記に指す先の違う「以下は」が 2 回出る（r3-1 の修正で 1 回になった） |
| r3-4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 足した指し先 tests/_timing_budget.py が plugin からのパスで、repo 直下からたどれない（r3-1 の修正で repo 直下からのパスにした） |
| r4-1 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 注記の括弧が打ち切りの正本の置き場を 3 つに限り、呼び出し側が literal の timeout= を渡すテスト（test_stop_failure_hook_contract.py など）を覆わない |
