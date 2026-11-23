---
lane: L1
pr: 577
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 36809e6877ee134f216a07c3bad5e3fd6ccc49e2 | 0 | 5 | 0 | 2026-10-24T15:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d4dc3a93c1b2a85d4701523aed0e54e17c7f9c8b | 0 | 1 | 0 | 2026-10-26T10:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-26、推奨の案）: § 直し方の「設計に戻る」を 3 回差し戻したときだけにした。軽いレーンは high・blocking を直す前に毎回求める（依頼より狭い）。Opus・Fable の推奨（毎回求める）で § 直し方の 0 にした（commit: cc76cbce） |
| r1-2 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-26、推奨の案）: 依頼に無い Stop hook の通知を足した。今の書式の steering では当たる件数が 0 で、CLAUDE.md の発火条件の規則（0 件なら足さない・未測ならユーザーが確かめる）に合わない。Opus・Fable の推奨（外す）で通知とテストを外した（commit: cc76cbce） |
| r1-3 | 独立-1 | medium | no | self-inflicted | routing-consistency | accepted | `kept` が Routing Decision Tree 2b（Architecture Gate）・bounce-log-schema・合理化の表の「同じ route に戻さない」と食い違い、同じ場面に 2 つの手順がある |
| r1-4 | 独立-1 | medium | no | self-inflicted | routing-consistency | accepted | `kept` で 3 回目の implementation_fix_only を選んだ task を再開すると、state-machine の整合性検証 3（Fix Attempts ≥ 3 かつ implementation_fix_only は不整合）が止める |
| r1-5 | 独立-1 | medium | no | self-inflicted | record-persistence | accepted | `changed` の route は tasklist を作り直すので、Approach Rethink の行は消え、数えられるのは `kept` だけになる |
| r1-6 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-26、推奨の案）: 「3 巡目のレビュー」を impl-gate の差し戻しだけに限り、PR 後のレビューの 3 巡目を対象にしていない。Opus・Fable の推奨（PR 後も対象にし、既存の Design Review Checkpoint の checkpoint: 行を記録として指す）で直した（commit: cc76cbce） |
| r1-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | 通知に /compact の前置きが付かないこと、Next Action の読み順、Current Task の中の fence の `## ` 行を固定するテストが無い |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 直し方 5 の後半に主語が無く worker も当てうる。同節冒頭の「4・5 の記録先は規律 C」と食い違う |
| r1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しい欄 Approach Rethink が state-field-tiers.md と § 更新責任 に載っていない |
| r1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | compact の契約の「4 つに閉じる（これ以外では何も出さない）」が、通知を足した後は事実と合わない |
| r1-11 | 独立-1 | low | no | self-inflicted | changelog | accepted | 変更断片が `type: patch` だが、新しい通知・欄・手順を足すので minor に当たる |
| r1-12 | 独立-1 | low | no | self-inflicted | budget | accepted | 行数の予算を、既存の箇条への継ぎ足しで回避した。別の発火条件の規則が別の項に混ざる |
| r1-13 | 独立-1 | low | no | self-inflicted | notice-key | accepted | tasklist を作り直して同じ task id が再び 3 回差し戻されても、記録キーが同じなので通知が出ない |
| r1-14 | 独立-1 | low | no | inherited | parser-symmetry | accepted | Gate Rounds を読む compact_suggestion と check-finding-dispositions で、受け付ける書き方が違う（origin: pre-existing） |
| r1-15 | 独立-1 | advisory | no | self-inflicted | changelog | accepted | 変更断片の Summary が通知の条件を落としている |
| r1-16 | 独立-1 | advisory | no | self-inflicted | style | accepted | 通知の文が plugin の中の相対パスを指し、利用者の repo から辿れない。「か」の後に空白が無い |
| r2-1 | 独立-2 | medium | no | self-inflicted | record-persistence | accepted | `Approach Rethink: changed` の行と § 直し方 0 の `設計: 変える` の行は、planning 差し戻しで tasklist.md を作り直すと消え、残るのは変えない側だけになる |
| r2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | § 直し方 0 は 3 回差し戻された後の route 判断を `Approach Rethink` に書くとし、正本は最初の 1 回だけで書き換えを禁じるので、4 回目以降の `設計:` の記録先が決まらない |
| r2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 後の「3 巡目」を数字で書き、閾値を定数名（`PR_CHECKPOINT_ROUNDS_THRESHOLD`）で書く followup の規定と合わない |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `checkpoint:` の行には § 直し方 0 が求める決定・理由の欄が無く、(a) は発火の条件で見直しの中身は同節の再評価にある |
| r2-5 | 独立-2 | low | no | self-inflicted | request-scope | accepted | PR 後の例外の主語が skill を限らず、checkpoint を持たない pr-review-followup にも当たって読める |
| r2-6 | 独立-2 | low | no | inherited | doc-claim | accepted | self-review-lanes.md の参照元の一覧に、§ 直し方 0 を指す state-machine.md § Remediation Loop Safety が無い（origin: pre-existing） |
| r2-7 | 独立-2 | low | no | inherited | doc-claim | re-reported | state-field-tiers.md に `Approach Rethink` の欄が無い（r1-9 の再掲） |
| r2-8 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | § 直し方 0 が当たる件数と止めたい損失の数が PR 本文に無い。PR 本文の限界に未測として書く（commit: なし（PR 本文）） |
| r2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 同じ見直しの記録が `設計:`・`Approach Rethink:`・`checkpoint:` の 3 通りの語で書かれ、対応表が無い |
