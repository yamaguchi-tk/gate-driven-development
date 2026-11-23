---
lane: L1
pr: 570
follow_up_of: 569
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4e719dab | 0 | 6 | 0 | 2026-10-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8c5cb798 | 0 | 5 | 0 | 2026-10-23 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9ed8ee76 | 0 | 3 | 1 | 2026-10-23 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 88551c44 | 0 | 2 | 0 | 2026-10-23 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーの指示で Fable の案。中継は残し、読めなければ PR から取り直して取れなければ止める）。PR 後のレビューの主な入口（gdd-pr-review-followup の Route・Auto-Arm・Escape Hatch）が human_recheck_required・planning_rework_required を選ぶとき systematic-debugging を通らず、Hotfix Findings を書く主体が動かない。systematic-debugging の復帰シーケンスも Hotfix Lane に回したときの戻り先を書いていない commit: 8c5cb798 |
| F2 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーの指示で Fable の案。中継は残し、読めなければ PR から取り直して取れなければ止める）。task-breakdown の Template と gdd-task-breakdown/SKILL.md の読む範囲に worklog.md が無く、runner が Origin Findings を読むかが決まらない commit: 8c5cb798 |
| F3 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーの指示で Fable の案。中継は残し、読めなければ PR から取り直して取れなければ止める）。quick (express) の hotfix は task-breakdown を通らず、TDD Step 1 が作る tasklist に Origin Findings を写す段が無い commit: 8c5cb798 |
| F4 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーの指示で Fable の案。中継は残し、読めなければ PR から取り直して取れなければ止める）。Hotfix Findings を書く done の steering の worklog.md は、マージ後の cleanup で worktree ごと消え、hotfix を起こすときには読めず黙って飛ばされる commit: 8c5cb798 |
| F5 | 独立-1 | medium | no | self-inflicted | wiring | accepted | Hotfix Findings・Origin Findings に書き方・写した印・消す時期が無く、2 本目の hotfix や作り直しで行が重なるか消える |
| F6 | 独立-1 | medium | no | self-inflicted | wiring | accepted | finding の AC ID が元の steering の番号のまま、新しい steering の AC の primary owner と Covers AC に当てられ、lint-ac で blocker になりうる |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd-using-git-worktrees の hotfix の手順と phase-progression の規約の列挙に、写す段が無い。PR 本文の「起票の手順が skill に無い」とも食い違う |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | state-field-tiers の Fix Findings の読み手が TDD Step 1 だけのままで、state-machine の更新責任も新しい書き込みを挙げていない |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の「これで TDD Step 1 が読む」が、届く範囲より広い |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 件数を未測とした理由が既存の記録（Error Log・followup の記録）と合わず、限界の節にもユーザーの確認にも回していない |
| F11 | 独立-1 | low | no | inherited | wiring | accepted | post-completion-pr-flow のマージ後着弾レビューは別の書式で新しい steering に渡すので、Fix Findings に届かない |
| F12 | 独立-1 | low | no | self-inflicted | wording | accepted | 「元の steering」と「差し戻しを受けた steering」の呼び方がそろっておらず、多段 hotfix で root に書かれうる |
| F13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 3 本が、同じ規定の途中の形を順に書いている |
| F14 | 独立-2 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーが選んだ Fable の案の中継のまま、書き手・取り直し・写す主体を決める）。PR から取り直すとき、Hotfix に回したことが PR に残らないので、Hotfix に回していない指摘も写り、resolve 済みの thread の行は落ちる。F4 の直しの残り commit: 9ed8ee76 |
| F15 | 独立-2 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーが選んだ Fable の案の中継のまま、書き手・取り直し・写す主体を決める）。書き手に Auto-Arm を含めているが、Auto-Arm は done マーカーの前にしか動かず、暫定の done を done と読ませる。F1 の直しの残り commit: 9ed8ee76 |
| F16 | 独立-2 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーが選んだ Fable の案の中継のまま、書き手・取り直し・写す主体を決める）。書き手の節の列挙から followup の Design Review Checkpoint が漏れている。F1 の直しの残り commit: 9ed8ee76 |
| F17 | 独立-2 | medium | no | self-inflicted | wiring | accepted | systematic-debugging の Hotfix route で、rollback-patterns の永続化に従うと done の steering を non-terminal に戻し、元 steering を done のまま残す規定とぶつかる |
| F18 | 独立-2 | medium | no | self-inflicted | wiring | fixed | 設計: 変えない（ユーザーが選んだ Fable の案の中継のまま、書き手・取り直し・写す主体を決める）。Hotfix Findings から Origin Findings に写す主体が無く、hotfix を作る手順（gdd-using-git-worktrees）の規約の列挙にも無い。F4 の直しの残り commit: 9ed8ee76 |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | express での写し先が、state-machine（下の規則）と TDD SKILL（1 タスク）で食い違う |
| F20 | 独立-2 | low | no | self-inflicted | wiring | accepted | 取れなければ human-check-waiting で止めた後の state と再開の仕方が決まっていない |
| F21 | 独立-2 | low | no | self-inflicted | wiring | re-reported | AC を名指す行を、新しい steering の同じ番号の AC の primary owner に写す |
| F22 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | gdd-task-breakdown/SKILL.md の Inputs に worklog.md が無く、Inputs を正とする起動では Origin Findings を読まない |
| F23 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 足した発火条件（PR から取り直す・取れなければ止める）の件数も未測の理由も、PR 本文に無い |
| F24 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界「gh が使えないときに followup が書けない」は、規定から生じない場合を書いている |
| F25 | 独立-2 | advisory | no | inherited | wiring | accepted | done の前に followup が human_recheck_required に決めた指摘は、同じ steering の Fix Findings にも書かれない |
| F26 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | systematic-debugging の新しい戻り先が、PR 本文と変更断片の Summary に無い |
| F27 | 独立-3 | medium | no | self-inflicted | wiring | accepted | 設計の変更（88551c44 で PR コメントの義務を外した）で前提が消えたので、systematic-debugging と state-machine は変えない。PR コメントの義務が systematic-debugging と state-machine に届かず、その経路では cleanup の後にどこからも取れない |
| F28 | 独立-3 | medium | yes | self-inflicted | security-boundary | fixed | 設計: 変える（取り直し元を、誰でも書ける専用の PR コメントにした決定をやめ、ユーザーが選んだコメントと review thread に戻し、起こした行は human check で承認されたものだけを写す）。`Hotfix Findings:` で始まる PR コメントなら書いた人を問わず検証なしに Origin Findings と Fix Findings に入る commit: 88551c44 |
| F29 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | 設計: 変える（取り直し元を、誰でも書ける専用の PR コメントにした決定をやめ、ユーザーが選んだコメントと review thread に戻し、起こした行は human check で承認されたものだけを写す）。ユーザーが選んだ「PR のレビューのスレッドから取り直す」を、確認なしに専用のコメントに替えた commit: 88551c44 |
| F30 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | state-field-tiers の Fix Findings の書き手の列挙が、phase-progression の「skill・節を問わず」とそろっていない |
| F31 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 設計: 変える（取り直し元を、誰でも書ける専用の PR コメントにした決定をやめ、ユーザーが選んだコメントと review thread に戻し、起こした行は human check で承認されたものだけを写す）。変更断片が systematic-debugging も PR コメントを残すと書くが、差分に無い commit: 88551c44 |
| F32 | 独立-3 | low | no | self-inflicted | wiring | fixed | 設計: 変える（取り直し元を、誰でも書ける専用の PR コメントにした決定をやめ、ユーザーが選んだコメントと review thread に戻し、起こした行は human check で承認されたものだけを写す）。followup の Route 行に PR コメントの接頭辞が無く、Escape Hatches から Route 行を指す文も無い commit: 88551c44 |
| F33 | 独立-3 | low | no | self-inflicted | wiring | accepted | cleanup 側（Persistence Gate・safe cleanup ready）に、Hotfix Findings を写す前に cleanup しない条件が無い |
| F34 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | phase-progression の Post-Merge Follow-up Worktree Policy の 4 の列挙に Origin Findings が無い |
| F35 | 独立-3 | low | no | self-inflicted | wiring | fixed | 設計: 変える（取り直し元を、誰でも書ける専用の PR コメントにした決定をやめ、ユーザーが選んだコメントと review thread に戻し、起こした行は human check で承認されたものだけを写す）。PR コメントを投稿できなかったときの扱いが無い commit: 88551c44 |
| F36 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | 足した仕組みの件数を測るか、未測と記録に残らない入力を PR 本文に書いていない |
| F37 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | phase-progression の「skill・節を問わず」とマージ後着弾の扱いが読み分けられない |
| F38 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | done マーカーと暫定の done の条件の言い方が、phase-progression と followup で違う |
| F39 | 独立-4 | medium | no | self-inflicted | wiring | accepted | route を Hotfix Lane に決めたことが PR に残らず、PR から取り直すときにどのクラスタを起こすかが推測になる。漏れた行は human check でも見えない |
| F40 | 独立-4 | medium | no | self-inflicted | wiring | accepted | PR から起こした行を承認まで置く場所、示す human check、承認後に Origin Findings へ書く主体が決まっていない |
| F41 | 独立-4 | low | no | self-inflicted | request-drift | accepted | 確認済み（2026-10-23 08:17、ユーザーが今の形を選んだ）: 取り直し元を「PR のコメントと review thread」に広げたことと、human check で承認された行だけを写す条件を足したことを、ユーザーに確かめていない |
