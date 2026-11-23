---
lane: L1+
pr: 542
amends: 20261004-autonomy-value-notes-followup.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | - | 0 | 1 | 0 | 2026-10-16 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 526b29f2d45949e04914d15fb2565a1b177fcd3d | 0 | 0 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| m-1 | 方針メモ | medium | no | self-inflicted | design | accepted | 確認済み（10-16 21:33 「よい」）: size の deny をやめ、上限を超えて増える write を allow にして、超過の文と退避の手順を additionalContext（subagent にも届くことを transcript で確かめた）と systemMessage に出す。ほかの category の deny と、降格した allow にも同じ通知を付ける。kill switch GDD_STEERING_SIZE_DENY・size の deny counter・降格の連動・DISABLED_NOTICE は消す（2 本とも）。今の advisory の _oversize_warning は消して通知に一本化する（Fable。Opus は ApplyPatch の分だけ既存サイズで残す案。30 日で ApplyPatch の steering write は 0 件なので Fable 案）。size の算出の例外は今の top-level guard のままで except を足さない（Opus。Fable は算出不能の通知を出す案。コード上到達せず実例 0 件なので Opus 案）。通知の文は実行後に届く形にする（2 本とも）。commit: なし（方針） |
| r1-1 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（10-16 21:33 「よい」）: 旧 advisory を消したので、算出できない書き込み（ApplyPatch・相対パス・stat の失敗・edits の型違い・dict でない tool_input）には合図が出なくなった。方針メモの確認（m-1）の問いに含めて返事を待つ。PR 本文の限界に全部の形を書いた |
| r1-2 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（10-16 21:33 「よい」）: kill switch を消したので、size の通知を止める手段が hook 全体の無効化だけになった。方針メモの確認（m-1）の問いに含まれる |
| r1-3 | 独立-1 | low | no | self-inflicted | product | accepted | 降格した allow では、size の通知が systemMessage にだけ付き、agent に届く additionalContext に出ない |
| r1-4 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の type が minor で、Breaking Contract Changes の節が無い（block 条件の変更と env の削除） |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR と設計文書の追記の参照先が、リリースで消える changelog.d の断片になっている |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 未リリースの断片 4 本（20261002 の 3 本と approved-direction-glob-extract）が、消えた deny の文言・警告文・WHY 行・env を記述したまま |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の hook の入出力の表に、size の通知が無い |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docs/learned-patterns.md:7 に「state.md を 20000 byte 以内に制限する」が残る |
| r1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文に、size の Why 行が消えたことと、上限を超える書き込みでも advisory lint が走るようになったことが無い。PR 本文に書いた。commit: なし（PR 本文） |
| r1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の消したテストの説明に、Why 行のテストと advisory lint を走らせないテストが入っていない。PR 本文に書いた。commit: なし（PR 本文） |
| r1-11 | 独立-1 | low | no | self-inflicted | test-power | accepted | size の通知と自走上限の注記が同時に出る形を、テストが通していない |
| r1-12 | 独立-1 | low | no | self-inflicted | product | accepted | post_size は上界推定なのに、通知は確定したサイズとして書く |
| r1-13 | 独立-1 | advisory | no | self-inflicted | product | accepted | 知らせるだけになった size の判定が try で守られず、想定外の例外で steering への書き込みが全部 deny になる（コード上は到達しない） |
| r1-14 | 独立-1 | advisory | no | self-inflicted | style | accepted | emit_allow_with_warning の docstring・steering_size.py:76・SIZE_DENY_SUFFIX の名前・test_check_gate_ledger.py のコメントが、deny の前提のまま |
| r1-15 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の件数と subagent への到達の確認に、測ったコマンドが無い。PR 本文に書いた。commit: なし（PR 本文） |
| r1-16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片と通知の文の「出さない」条件に、同じサイズの書き込みが無い |
