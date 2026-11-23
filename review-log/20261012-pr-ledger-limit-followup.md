---
lane: L1
pr: 436
follow_up_of: 432
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 274d25c0be5bc4b6225c47c91cd728803998853c | 1 | 0 | 1 | 2026-10-12T11:30+09:00 |
| 方針メモ-1 | user | - | 0 | 0 | 0 | 2026-10-12T11:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6845ed113e5f4b3d76d0ec98e479049de37ee69c | 1 | 1 | 1 | 2026-10-12T11:50+09:00 |
| 方針メモ-2 | user | - | 0 | 0 | 0 | 2026-10-12T11:50+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 7f6c591365e3ee5bc0575af896c39f10ff897441 | 0 | 0 | 0 | 2026-10-12T13:10+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | cb0d7c2ed8ecca24de327977c6b6ce1ae2d33074 | 0 | 1 | 0 | 2026-10-12T13:30+09:00 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | f1b92e80f48710957e031a94380235776b2d9027 | 0 | 1 | 0 | 2026-10-12T14:20+09:00 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | edd4262cde59d9a2b4455ecdaea1b51fee359b85 | 0 | 0 | 0 | 2026-10-12T14:35+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | yes | inherited | root-selection | accepted | 列挙: pre-PR gate・pre-push gate の root を cd 先 1 つで決めるので、`cd <marker の無い GDD worktree> && gh pr create`・`git push` を検査せずに通す（merge gate の候補の選び方とそろっていない）。常時 High なので再掲にできない。閉じ方: 列挙。方針メモ-1：事故で打つ形として transcript に 25 件・44 件あるので規定の既定は (a) だが、ユーザーが 2026-10-12 に同じ欠陥を直さず 旧#431 に足すと決めた（依頼の原文）のでそれに従い accepted。Opus 設計レビュー: 呼んでいない（同じ欠陥の扱いをユーザーが決定済みのため） |
| F2 | 独立-1 | low | no | self-inflicted | ledger-hit-deadend | fixed | 足した案内「marker のある場所から実行する」は、root に marker があって止まる出口（:887）では出口にならない。「台帳に載った GDD worktree に marker が無いと cd しても止まり続けるので人が merge する」にした。commit: 6845ed11 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 飛ばす検査を「全部挙げた」としていたが、state.md 読めない・base branch 解決不能の block が漏れていた。「marker の判定より後の検査すべて（…など）」にした。commit: 6845ed11 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「照合で外れた merge は marker の無いセッションからなら通る」が実装より狭く、lib のコメントと食い違う。条件を外し、止まる場合を括弧で添えて両方をそろえた。commit: 6845ed11 |
| F5 | 独立-1 | low | no | inherited | ledger-hit-deadend | fixed | 未リリースの断片 20260918-merge-gate-non-gdd-merge.md の User Action Required が「GDD の worktree で実行する」だけで、marker が無いと止まり続けることを書いていない。前の断片は変えず、この PR の断片の User Action Required に書いた。commit: 6845ed11 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary に § 制限事項の例外の変更（git push・pre-push gate の追加、「marker を見る検査をしない」）が無い。1 行足した。commit: 6845ed11 |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の「台帳で当たった PR を止めるときの案内」は、`repo-root-unresolvable` の全 block に出る文言である |
| F8 | 独立-1 | advisory | no | inherited | doc-claim | accepted | § 制限事項の例外に、merge gate が台帳で外れた PR を証跡を見ずに通すことを書いていない（§ 4 を読めば分かる） |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | lib のコメントの PR 本数の内訳に git push の件数が混ざる |
| F10 | 独立-1 | advisory | no | self-inflicted | style | accepted | lib のコメントと merge gate のコメントの折り返しがそろっていない |
| F11 | 方針メモ-1 | - | - | - | - | - | なし |
| F12 | 独立-2 | high | yes | inherited | root-selection | accepted | 列挙: 独立-1 の F1 と同じ欠陥（pre-PR gate・pre-push gate が `cd <marker の無い GDD worktree>` の形を検査せずに通す）。常時 High なので再掲にできない。閉じ方: 列挙。方針メモ-2：ユーザーが 2026-10-12 に直さず 旧#431 に足すと決めた（依頼の原文）のでそれに従い accepted。Opus 設計レビュー: 呼んでいない（同じ欠陥の扱いをユーザーが決定済みのため） |
| F13 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 足した括弧書き「止まるのは、root の steering が対象 PR を記録しているときと、自セッション所有の active な marker の下で steering を解決できるときだけ」が実装と合わない。marker の無い root では steering を読まずに通し、PR URL 未記録・steering の複数・読めないときなどでも止まる。ユーザーの指示（依頼の原文の追加分「直して」）で直した。止まる場合ではなく、証跡を見ずに通る 3 つの場合を書いた。commit: 7f6c5913 |
| F14 | 独立-2 | low | no | inherited | ledger-hit-deadend | accepted | `repo-root-unresolvable` の案内の先頭「repo 内のディレクトリで実行する」は、台帳で当たった block（repo 内で実行している）では行き止まり。PR 本文の限界に書く |
| F15 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary に、照合で外れた merge が通る条件を書き直したことが無い。F13 を直すときに Summary にも書いた。commit: 7f6c5913 |
| F16 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | :109・lib は「marker の判定より後の検査すべて」、:273・断片は「marker を見る検査をしない」で語がそろっていない。PR 本文の限界に書く |
| F17 | 方針メモ-2 | - | - | - | - | - | なし |
| F18 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 直した文の除外の例「複数ある」が実装と逆（steering が複数でも、どれも別の PR を記録していれば :1039 で通る）。ユーザーが直すよう求めた文の残りなので直し、例を `PR URL` の無い steering（:1157 で止まる）に替えた。commit: cb0d7c2e |
| F19 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 自セッションが所有する active な marker の下で steering が決まるときは証跡を検査するのに、文からはそれが読めない（穴を広く書く向き） |
| F20 | 独立-3 | low | no | inherited | doc-claim | accepted | 「照合で外れた」は、台帳が unknown・unreadable を返す場合や、解析しきれないときに通る経路を書いていない。PR 本文の限界に書く |
| F21 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 「root の steering に対象 PR があっても読まない」は、台帳に載った root では照合で読むので言い過ぎに読める |
| F22 | 独立-4 | medium | no | self-inflicted | doc-claim | fixed | 差し替えた除外の例「`PR URL` の無い steering がある」も、候補 0 件の経路（中止した steering だけが残る checkout）では止まらずに通る（:1050-1076。test_only_terminal_steerings_still_pass が固定）。ユーザーが直すよう求めた文の残りだが、ユーザーが再び「直して」と指示した（依頼の原文の追加分）ので、除外を止まるときの reason code で指す形にした。commit: f1b92e80 |
| F23 | 独立-4 | low | no | self-inflicted | style | accepted | gdd-pr-roots.sh:24 だけ前後のコメント行より長く、折り返しがそろっていない |
| F24 | 独立-4 | advisory | no | inherited | doc-claim | accepted | found の経路は中止した steering の PR URL 欠けで止めるのに、候補 0 件の経路は通す非対称（:1063-1076 と :1105-1122）。どちらにそろえるかは別 PR で設計を確かめてから |
| F25 | 独立-5 | medium | no | self-inflicted | doc-claim | fixed | 除外を 4 つの reason code に閉じたが、`pr-target-unresolvable` で止まる経路と、自セッションの active な marker の下で証跡を検査して止まる経路が漏れていた。依頼（直して）の残りなので直し、「など」で網羅を主張しない形にして、証跡を検査する場合も除外に足した。commit: edd4262c |
| F26 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | 2 つ目の除外句（active な marker の下で証跡を検査する場合）は実装では必ず止まるので、1 つ目の「理由つきで止まる場合」に含めてまとめられる。任意 |
