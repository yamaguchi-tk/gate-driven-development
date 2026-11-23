---
lane: L1
pr: 280
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user（GDD を使う別の repo の 20261001-investigation-credential-handoff で、completion の Round 上限を超えた後も pre-PR gate を満たせる案が無かった件から。main の草案は「受け入れた限界と完全一致する再報告を re-reported にする」。Opus は作らない〔Z〕を推し、草案の事実の誤り〔Round 3 の blocking 6 件のうち限界に当たるのは 3 件〕を指摘した。ユーザーの指示で Fable に聞き、Fable は gate の述語と (3-d) を変えずに方式転換へ「限界として開示して人に渡す」を足す案〔Y+〕を推した。ユーザーは Y+ を選んだ） | - | 0 | 0 | 0 | 2026-10-02T10:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 768e9ae3cf9bdfbf0cd203112f30e39a5e5d0e98 | 0 | 0 | 0 | 2026-10-02T11:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | - | - | - | - | - | なし |
| Q1 | 独立-1 | medium | no | self-inflicted | product | next-pr | 人の返答を処理する側（gdd-dev.md #10・human-check-template.md の共通の承認後処理）が、4 つ目の案の「state を変えずに止まる」につながっていない。返答を承認として処理すると元のループに戻る |
| Q2 | 独立-1 | medium | no | self-inflicted | doc-claim | next-pr | 各案の見込みを Independent Review の条件だけで書かせている。pre-PR gate は先に Next Action=done を要求し、Completion Rounds は human_recheck で戻らない |
| Q3 | 独立-1 | medium | no | self-inflicted | product | next-pr | 「人が承認した限界」の記録先に、agent が人の承認なしに書く adr.md と PR に入る ADR が入っている。承認の出典を求めていない |
| Q4 | 独立-1 | medium | no | self-inflicted | product | next-pr | 記録先に、正本の requirements.md § Honest Limitations（Human Check 承認時点）が入っていない。gdd-pr-review-followup の既知の限界の定義とそろっていない |
| Q5 | 独立-1 | medium | no | self-inflicted | doc-claim | next-pr | Round 上限の手順の正本 gate-checklists.md:135 に「方式転換 3 択」が残っている |
| Q6 | 独立-1 | medium | no | self-inflicted | product | next-pr | 人の端末で PR を作る経路では pre-PR gate の機密チェックなどが走らない。草案への 3d 相当のチェックと、走らない検査の開示が無い |
| Q7 | 独立-1 | low | no | self-inflicted | product | next-pr | 4 つ目の案の後、steering が human-check-waiting のまま残り、再開するたびに同じメニューが出る。終え方が無い |
| Q8 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | pre-push gate の block 文が案内する GDD_SKIP_PRE_PUSH_GATE=1 を使わない・案内しないと書いていない |
| Q9 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 草案の節の対象（常時 High・実害クラス）が、置ける条件の対象（残る high・blocking）より狭い |
| Q10 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | handoff/completion_check.md の「該当 Round の節」の見出しが定義されておらず、上書きで草案が消えうる |
| Q11 | 独立-1 | low | no | self-inflicted | product | next-pr | 残る high・blocking が 0 件でも、4 つ目を置ける条件が形式上満たされる |
| Q12 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の User Action Required が「なし」と書いたうえで利用者の作業を書いている |
| Q13 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の Validation / Eval Impact に検証の種類ではない主張があり、references/ を判定のコードと呼んでいる |
| Q14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に worklog.md への 1 行の記録と、限界を草案に書くことが無い。PR 本文に足した commit: なし（PR 本文） |
| Q15 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | skill 本文を変えたのに Skill RED-GREEN Evidence が抜粋で確認できない。PR 本文に載せた commit: なし（PR 本文） |
| Q16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | repo root の docs/learned-patterns.md:16 に「方式転換 3 択」と plugin に無い Human Waiver が残る。当時の記録。PR 本文に列挙 |
| Q17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | impl-gate 側・PR 後側の方式転換は 3 案のままで、見込みの記載も無い。PR 本文の限界に書いた |
