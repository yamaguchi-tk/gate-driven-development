---
lane: L1+
pr: 484
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-14T13:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f7e487d5 | 0 | 1 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 90807e1e | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | low | no | self-inflicted | design | fixed | 変えるのは _ended_notifications だけで、`<result>`・`<event>` より前の区間に「This agent stopped with background work of its own still running」で始まる note があれば終わりに数えない（task-id の読み取り範囲は広げない）。正常に終わった通知にも note は付く（24,951 件）ので、note の有無ではなく接頭辞で狭く照合する。閉じタグの欠けた note も途中に倒す（待つ側。期限は wait watchdog が見る）。読む側は inflight_dispatch_ids・finished_task_ids（any_background_running・wait watchdog・state を消す停止の押し返し）・git_pre_push_review の _reviewer_outcomes（running になる）で、TaskStop の経路は変えない。限界は host の文言への依存と、途中のまま再開しない担当役が期限まで待ちに残ること。2026-10-13 に Opus と main の案が一致し、2026-10-14 にユーザーが計画を承認した commit: 05af5ac2 |
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | main が従う規則（subagent-dispatch.md の Typed Agent Resolution 手順 2・3 と時間上限）と background_dispatch_gate の deny の文が、途中の通知も返りとして timer を止めるよう読め、hook と食い違う。途中の通知の定義を手順 2 に 1 か所置き、ほかはそこを指した commit: c784126a |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 読む側の列挙にマージ待ちの押し返し（any_background_running → merge_wait_reason）が無く、新しく出る block（期限 watchdog・停止の押し返し）も書いていない。PR 本文に足した commit: なし（PR 本文） |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | コメント・断片が「もう一度通知が来る」と言い切っている。限界の「期限の上限まで」は LIMITS の 5 種にだけ当たり、ほかの type は TaskStop まで残る（PR 本文の限界は直した） |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | transcript.py の 3 つのコメント（:24・:37-40・:377-379）が、終わりを status だけで決めると書いたまま |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 分岐は status を問わず途中の note で終わりから外すが、断片・PR 本文は completed として書き、テストも completed だけ |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の数え方が hook の読み方（text block と queued の行。tool_result は読まない）と違い、新しい述語を当てた件数が無い。PR 本文に数え方の違いと、note が result より前にあることへの依存を書いた commit: なし（PR 本文） |
| I1-7 | 独立-1 | low | no | self-inflicted | product | fixed | 依頼の「実際の transcript から作ったテスト用のデータ」に対し、テストは組み立てた通知だけだった。実際の途中・終わりの通知を伏せて写した fixture を足し、解析と hook の入口のテストに使った commit: c784126a |
| I1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | LIMITS の dispatch に途中の通知だけが来たとき overdue_reason が block することを固定するテストが無い |
| I1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files にテストのファイルが無い |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 計画の「32 回分は未測」と PR 本文の「10 件以上」の関係が書かれていない。PR 本文に書いた commit: なし（PR 本文） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | L1+ 安全策 2 の「例外で guard 全体が落ちる」のテストが無い（例外の経路は無い） |
| I1-12 | 独立-1 | advisory | no | self-inflicted | product | fixed | 途中の通知の後に TaskStop した reviewer は、push 前のレビューの確認で ok から failed になる。PR 本文に書いた commit: なし（PR 本文） |
| I1-13 | 独立-1 | advisory | no | inherited | product | accepted | 途中の通知の result に、開始タグから丸ごと引用した終わりの通知があると、引用を 1 つの通知として読む（既存の限界） |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片が、規則の文書（subagent-dispatch.md の手順 2 と時間上限の節）と deny の文の変更、実際の通知の写しを使うテストを挙げていない |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | stop-hook-structured-markers.md:25 の「完了通知も TaskStop もまだのもの」に、途中の通知を除く注記が無い（挙動は hook のとおり） |
| I2-3 | 独立-2 | low | no | self-inflicted | product | accepted | 規則の文書は途中の通知を note の場所で限らず、hook は `<result>` より前の note だけを見る。result に note を引用した終わりの通知を、main が途中と読みうる |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | 断片とテストの docstring が「もう一度通知が来る」と言い切っている（I1-3 と同じ） |
| I2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | fixture の summary は伏せておらず、「summary は伏せた」の記述と合わない。PR 本文からは「summary」を外した |
| I2-6 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | final.txt は interim.txt と別の agent の通知で、同じ task の途中→終わりの組を写したものではない |
