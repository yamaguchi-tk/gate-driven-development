---
lane: L1+
pr: 263
follow_up_of: 262
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（memory の 2026-09-28 の決定で、ユーザーへの確認は内部の相談で代えた。Opus の推奨〔記録を「1 行だけ」で判定する、Autonomy の生の行は判定に置き換える、選べる値の対応を明記する、再開で読めないときは止まる、ARN の規則は既存の検査に任せる〕を採った。Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-01T12:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5be4112992a8f067eebe70c3d5fcecc290a5dab4 | 0 | 4 | 1 | 2026-10-01T12:45+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 95ab8e18e28a4d5338b9e44f70bc8dcc0de7b815 | 1 | 4 | 1 | 2026-10-01T13:25+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 2705599e19de4e3c8bfa4939ba7cc920dcd5b093 | 0 | 1 | 0 | 2026-10-01T13:50+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| J1 | 方針メモ | - | - | - | - | - | なし |
| R1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 再開で MERGED のとき、マージまで のタスクでも手順 3〜5（デプロイの確認・QA・revert の PR）へ進んだ。自走上限で分け、手順 3〜5 は マージ・デプロイ・QA まで のときだけにした。commit: 4ba15db0 |
| R2 | 独立-1 | medium | no | self-inflicted | product | fixed | Write Targets の ARN を読んだまま記録させる規定が steering の書き込み検査と食い違った。Write Targets にアカウント ID を含む ARN と絶対パスを書かない形にした。commit: 4ba15db0 |
| R3 | 独立-1 | medium | no | self-inflicted | product | fixed | compact の最大到達点に、マージまで 以上の条件・本番なら本番・QA の書き込み先が無かった。足した（等価交換で重複する 1 文を削った）。commit: 4ba15db0 |
| R4 | 独立-1 | medium | no | self-inflicted | style | fixed | plugins/.DS_Store が差分に入っていた。外し、.gitignore に足した。commit: 4ba15db0 |
| R5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | full テンプレートの QA の書き込み先が マージまで にも掛かって読めた。マージ・デプロイ・QA まで に限った。commit: 4ba15db0 |
| R6 | 独立-1 | low | no | inherited | product | fixed | 再開で MERGED のとき、マージされた head を マージ前 の head と比べなかった。違えば止まる形にした。commit: 4ba15db0 |
| R7 | 独立-1 | low | no | inherited | product | fixed | 再開で OPEN のとき、古い記録だけで問わずにマージできた。OPEN では自走せず 1 問で問う形にした。commit: 4ba15db0 |
| R8 | 独立-1 | low | no | inherited | product | fixed | 再開に使うデプロイ・QA の記録の形が無く、QA や revert の PR を 2 回行いえた。デプロイ・QA 結果・revert PR の行を決めた。commit: 4ba15db0 |
| R9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が手順 1 にも 1 問で問うが当たるように書いていた。手順 1 と手順 2 を分けた。commit: 4ba15db0 |
| R10 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片に利用者から見えない参照元の整理が入っていた。削った。commit: 4ba15db0 |
| R11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片と PR 本文の gh pr view に PR の引数が無かった。足した。commit: 4ba15db0 |
| R12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの 旧#262 の断片が変更前の記録と待機の挙動を書いたまま。リリースの dry-run で版の節を直す（memory release-time-stale-fragment-fixes） |
| R13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | followup SKILL の待つ条件が この code だけのとき に限られていない。自走のマージでは 1 巡余分に待つだけで、PR 本文に書く |
| R14 | 独立-1 | advisory | no | self-inflicted | product | accepted | 1 行だけ の数え方が worklog 全体で、同じ steering での 2 回目の自走のマージは必ず問う。問う側に倒れるので PR 本文の限界に書く |
| R15 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 読んだまま記録する GDD QA の行が、読み方の規則で数える行に限られていなかった。限った。commit: 4ba15db0 |
| R16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | runtime の token 予算を確かめていなかった。validate-plugin.sh で確かめ、standard 45405 以内だった（直すものは無い） |
| S1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 再開が デプロイ の結論を見ず、失敗・承認待ちで止まったデプロイの後に QA へ進んだ。デプロイ の行は run がすべて success のときだけ書く形にした。commit: ac8e5745 |
| S2 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | QA 結果・revert PR を書く前の中断では、再開で QA や revert の PR を 2 回行いうる。断片の主張を、書いた後の中断に狭めた。PR 本文の限界に書く |
| S3 | 独立-2 | medium | no | self-inflicted | product | accepted | マージまで で マージ の行がある状態から再開すると、マージ後の read-only の確認を飛ばしうる。PR 本文の限界に書く |
| S4 | 独立-2 | medium | no | self-inflicted | product | accepted | Write Targets にアカウント ID を含む ARN が書かれていたときの扱いが無く、記録が止められるか伏せ字になる。PR 本文の限界に書く |
| S5 | 独立-2 | medium | no | inherited | product | fixed | QA 計画レビューで止まった後の再開が、止まった理由を出さずにマージの 1 問へ進んだ。high か blocking が 0 でない記録は記録の無いものとして扱う形にした。commit: ac8e5745 |
| S6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 絶対パスは止められるという理由が、検査が止める範囲（ホームディレクトリ）より広い。PR 本文の限界に書く |
| S7 | 独立-2 | low | no | self-inflicted | product | accepted | マージ前 の行が 2 つあるとき、比べる head が決まっていない（止まる側）。PR 本文の限界に書く |
| S8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文が手順 1 と手順 2 の条件を一括りで書いていた。PR 本文を直した。commit: なし（PR 本文） |
| S9 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の references の行数が実測と合わなかった。PR 本文を直した。commit: なし（PR 本文） |
| S10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 記録する GDD QA の行を絞った変更が断片に無かった。足した。commit: ac8e5745 |
| S11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | レビュー待機中に再開すると自走でなくなることが限界に無い。PR 本文の限界に書く |
| S12 | 独立-2 | advisory | no | self-inflicted | style | accepted | compact の略記が値の名前と揃っていない（token 予算のため） |
| T1 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | QA 計画レビューの行が複数あるとき、どの行で判定するかが決まっていない（手順の外の操作が要る）。PR 本文の限界に書く |
| T2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 手順 3 の それ以外は書かずに止まる が進行中の run も含んで読める（止まる側）。PR 本文の限界に書く |
| T3 | 独立-3 | low | no | inherited | product | accepted | run が 0 件や、デプロイの job が skip された run でも すべて success が真になる。PR 本文の限界に書く |
| T4 | 独立-3 | low | no | inherited | product | accepted | merge だけの宣言では 宣言 の記録が 0 行で、再開の起点がずれうる（止まる側）。PR 本文の限界に書く |
| T5 | 独立-3 | low | no | inherited | product | accepted | QA 計画レビューの記録が head にしか結びつかず、計画の中身に結びつかない。PR 本文の限界に書く |
| T6 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 時間の上限で止まった後の再開で、上限をどこから数えるかが決まっていない（止まる側） |
| T7 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 再開の側は デプロイ の結論を見ない（書く側の条件で守る） |
| T8 | 独立-3 | advisory | no | inherited | doc-claim | accepted | § 入口の括弧が手順 1 を挙げていない |
| T9 | 独立-3 | advisory | no | inherited | doc-claim | accepted | 旧#262 の断片が例外の記録に読んだ行を書くと書いたまま。リリースの dry-run で版の節を直す（memory release-time-stale-fragment-fixes） |
