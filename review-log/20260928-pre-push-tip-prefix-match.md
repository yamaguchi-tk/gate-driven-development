---
lane: L1+
pr: 219
follow_up_of: 211
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Fable 設計レビュー (general-purpose, model: fable) + user | 41b7816462aa73157f7a864434b520e1aa981386 | 0 | 0 | 0 | 2026-09-28T21:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1dfec222e433c777bfbb7edf10ffc86c206076a6 | 0 | 1 | 0 | 2026-09-28T22:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 066e837363b6c7a0b37cfe8ec127dca4148c017a | 1 | 0 | 1 | 2026-09-28T22:45+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 08bdf67b7f30fedd06a5862893bdbbac42b0766f | 2 | 0 | 2 | 2026-09-28T23:40+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) | 08bdf67b7f30fedd06a5862893bdbbac42b0766f | 0 | 0 | 0 | 2026-09-28T23:55+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | e818cfb6883099a9c178dd125da9afadace5ea76 | 2 | 0 | 2 | 2026-09-29T00:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) | e818cfb6883099a9c178dd125da9afadace5ea76 | 0 | 0 | 0 | 2026-09-29T00:50+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 2eda1acdbc1dfd9f8e566a7bb4226db077354cf4 | 1 | 1 | 1 | 2026-09-29T01:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（ユーザー指示で Opus の代わりに Fable に相談。推奨は「比較を先頭一致の 1 条件に置き換え rev-parse を外す・件数の検査は parser の awk の回数を数える・tip で選んだときの注記を入れる・断片の言い過ぎはリリース時に直す」で、そのまま採用。merge gate の URL の無い cancelled の件は作らない〔再開条件は PR 本文〕） |
| D1 | 独立-1 | medium | no | self-inflicted | guidance-scope | fixed | tip で選んだときの注記が、steering を終える案内の前提（ユーザーへの確認・PR が open のものを除く・手順の参照先）を持たず、選んだ steering が cancelled のときは約束も成り立たない（ea988e56、ebf2e360） |
| D2 | 独立-1 | low | no | self-inflicted | test-power | fixed | _PP_RECOVERY_SUFFIX への追記（dry-not-reached の経路）を検査するテストが無い（ea988e56） |
| D3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 注記を付ける block 文の列挙（dry・Independent Review）が実装（sha-mismatch・missing-evidence にも付く）と合わない（ebf2e360） |
| D4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストの module docstring に、外した「sha を解決できないときは止める」が残る（ea988e56） |
| D5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 同じ一致条件を書く未リリースの断片（旧#211）が古い条件のまま。リリース時に直す一覧に入れた |
| D6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「grep と比較で受理する集合が同じ」は、先頭 7 文字に backtick を挟んだ証跡で成り立たない（止める側）。PR 本文に列挙 |
| E1 | 独立-2 | high | yes | inherited | bound-terminal-fail-open | fixed | worktree の binding が終端（cancelled など）の steering を指すと、resolver が none/terminal-only を返し、binding の無い作業中の steering の push を検査せずに通す。pre-push で作業中の steering を数え直す（f3958bd4、8b5b0026） |
| E2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 注記の「作業中または完了済みのステアリングが一つになると」が resolver の規則（作業中が 1 件なら完了済みを数えない）と合わない（follow_up_of: 211 の後続 PR なので next-pr にせず accepted。PR 本文の限界に書く） |
| E3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | self-review-lanes.md:114 の tip の経路の案内と、:120 の参照元の列挙が注記に追随していない（follow_up_of: 211 の後続 PR なので next-pr にせず accepted。PR 本文の限界に書く） |
| E4 | 独立-2 | low | no | self-inflicted | test-power | accepted | tip の注記のテストが「ユーザーに確認」の部分一致だけで、否定形と「削除も移動もせず」の欠落を通す（follow_up_of: 211 の後続 PR なので next-pr にせず accepted。PR 本文の限界に書く） |
| E5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の注記の引用と実際のリテラルで括弧が違う。PR 本文を直す |
| F1 | 独立-3 | high | yes | inherited | bound-terminal-fail-open | fixed | step 7b は none/terminal-only のときしか走らず、binding が done を指す（または cancelled を指して done・blocked が 1 件ある）と union がその終端の steering を found にし、作業中の steering をその Task Size（trivial なら無検査）で検査する。resolver 側で数え直し、step 7b を消した（4f95e4d9、40efa0fb） |
| F2 | 独立-3 | high | yes | inherited | bound-terminal-fail-open | fixed | 同じ入力（binding が cancelled、作業中の steering あり）で merge gate が unresolved-steering-on-merge として承認の証跡なしに素通りする。resolver 側の数え直しで同時に閉じた（4f95e4d9、40efa0fb） |
| F3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 数え直しの全件走査の費用（timeout 10 秒で素通りしうる）が限界に書かれていない。PR 本文の限界に書いた |
| P1 | 方針メモ-1 | advisory | no | inherited | none | accepted | 要約: なし（安全策 4 が発火〔bound-terminal-fail-open の high が 独立-2・独立-3 の 2 巡〕。2026-09-28 のユーザー決定〔HITL は当初の機能が実装できない見込みのときだけ、設計変更は内部相談〕により Opus に相談。推奨は A〔resolver 側で直し step 7b を消す。merge gate も同時に閉じる〕で、main の案と食い違いが無いので Fable には聞かずに採用。binding が done の steering を指し、使っていない作業中の steering が残る checkout で止まる側の変化は限界として PR 本文に書く） |
| G1 | 独立-4 | high | yes | self-inflicted | bound-terminal-fail-open | fixed | 終端の binding の数え直しで作業中の steering だけを選ぶと、その Task Size（trivial）で、union が binding 先の done の steering を standard で止めていた push を無検査で通す。作業中の steering があるときは done・blocked の steering も候補に残して multiple にする（f53aa9e0、14727819） |
| G2 | 独立-4 | high | yes | inherited | bound-terminal-fail-open | accepted | pre-PR gate は binding が cancelled・stale な brainstorming の steering を指すと作業中の steering を数えず、done の steering が 1 件あればそれで completion-check を判定し、作業中の steering を検査せずに PR を作らせる。この PR は pre-PR gate を変えていない。限界の先頭に直していない常時 High・実害クラスとして書き、次の PR で直す |
| G3 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 断片の merge gate の止まり方と、done の binding で作業中が無いときの記述が実装より広い。数え直しの変更と合わせて書き直した（14727819） |
| P2 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし（安全策 4 の 2 回目の発火〔bound-terminal-fail-open の high が 独立-2〜独立-4〕。2026-09-28 のユーザー決定により Opus に相談。推奨は案 X′〔数え直しで作業中の steering があれば done・blocked の steering も候補に残す。新しい変数・reason・block 文は足さない〕で採用。G2 は pre-PR gate の resolver で、Post-Completion の PR 作成との両立が要るため次の PR にし、self-review-lanes.md と PR 本文の記述を実際の性質に直す。Fable はこの PR の方針メモで使ったので呼ばない） |
| H1 | 独立-5 | high | yes | inherited | bound-terminal-fail-open | accepted | binding 先の終端の判定が Resume From だけを見て、正規の完了の形（Next Action: done）を終端にしない。binding 先が Next Action: done・trivial なら found になり、作業中の steering があっても push を検査せずに通す（origin/main から同じ）。無効化後の差分巡が 2 回に達したので直さず、限界の先頭に書いて次の PR で直す |
| H2 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 数え直しで残す done・blocked の候補は stale な brainstorming を除いた後に集めるが、コメント・規定・限界は union と同じと書く。PR 本文の限界に書く |
| H3 | 独立-5 | medium | no | self-inflicted | test-power | accepted | 数え直しで残す done・blocked の述語のうち、Next Action だけが done の形と blocked の選言をテストが固定していない。follow_up_of の後続 PR なので accepted。PR 本文の限界に書く |
| H4 | 独立-5 | low | no | self-inflicted | test-power | accepted | 作業中の steering が trivial のテスト 2 本が、出力が空でないことしか確かめない（steering-multiple を固定しない）。PR 本文の限界に書く |
| H5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | テストの docstring・関数の見出しコメント・断片 :11・PR 本文のテストの行・pre-PR gate の記述（binding 先が done のとき）が、数え直しの挙動と合わない。PR 本文の限界に書く |
| H6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | self-review-evidence.sh のコメント 2 か所・テストの class docstring・merge gate のテストの docstring・断片の User Action Required が、done・blocked を候補に残すことに追いついていない。PR 本文の限界に書く |
