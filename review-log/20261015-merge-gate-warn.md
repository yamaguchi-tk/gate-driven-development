---
lane: L1+
pr: 514
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-15 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 847746a7 | 0 | 5 | 0 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e50da31e | 0 | 0 | 0 | 2026-10-15 |
| 独立-3 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | f6c32c0e | 0 | 2 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | product | fixed | 案 W（3 gate とも止めない形）を推す。merge gate は警告が merge の後に届くので「止めるのをやめて記録を残す」と書き、通知を条件法の前置きにし、would-block を記録し、通知の読み手と文書を直す。PR 1 は merge gate、PR 2 は pre-push・pre-PR（旧#507 の後）。ユーザーへの確認は返事を待たずに本文に書き、推奨の案で進めた。commit: なし（方針） |
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | 通知の前置き（成功した場合は書き足さない）と、後ろに続く merge の前の手順の文（承認を記録して再実行する）が食い違う。前置きを、成功した場合と失敗した場合（失敗した場合だけ次の手順で直す）に分けた commit: e50da31e |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | would-block の記録が先頭の code だけで、ADR の測り直し（approval 系の行だけを数える）が 0 件に寄る。不足条件の全 code を 1 行に記録し、ADR の測り方を全行と transcript の突き合わせにした commit: e50da31e |
| I1-3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | ADR の「merge gate だけを変える PR は L1」が、root CLAUDE.md のレーンの表（merge gate を L1+ に挙げる）と食い違う。ADR を「L1 にするには表を直す必要があり、この時点では直していない」にした。表を直すのは次の PR commit: e50da31e |
| I1-4 | 独立-1 | medium | no | self-inflicted | product | accepted | 依頼の第 1 手（merge gate に続けて pre-push・pre-PR gate）のうち、pre-push・pre-PR を後の PR に回した。ユーザーが「PR を分けてOK」と答え、request.md に足した。2 つの gate は次の PR |
| I1-5 | 独立-1 | medium | no | self-inflicted | test-power | fixed | test_gates_toplevel_cwd の merge gate の 2 件が decision の不在だけを見ていて常に真になる。returncode 0・stdout が空・would-block の記録が空を見る assert に直した commit: dda2b2b4 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | merge gate が止める前提の記述が、ほかの文書（SECURITY.md:109、self-review-lanes.md、state-machine.md など）と Stop hook の押し返しの文に残る |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | env-s ADR に付けた置き換えの印が、pre-push gate と Stop hook が共有する parser の文まで外している |
| I1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | 全 code を通るテストが returncode を見ない。書けない state dir のテストは記録の guard を固定しない（集約の経路で全 code を 1 行に記録するテストは dda2b2b4 で足した） |
| I1-9 | 独立-1 | low | no | self-inflicted | product | accepted | 止めなくなった通知が、全 hook を外す kill switch を案内し続ける |
| I1-10 | 独立-1 | low | no | self-inflicted | product | accepted | merge の前に確かめると書いたが、記録を書かずに確かめる道具が無い |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の「would-block の行を数える」が、merge でないコマンドの行と先頭の code だけの記録に合わない。断片を記録の形に合わせた commit: e50da31e |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR の根拠の数値に、期間・抽出の手順・記録の場所が添えられていない |
| I1-13 | 独立-1 | advisory | no | self-inflicted | product | accepted | 確認 1（merge gate に判定を足す PR の凍結が、止めない形にする変更にも当たるか）の答えが記録に無かった。ユーザーが「確認1は当たらない」と答え、request.md に足した |
| I2-1 | 独立-2 | low | no | inherited | product | re-reported | pre-push・pre-PR gate を別の PR に分けたことの確認が依頼の原文に無い（I1-4 と同じ） |
| I2-2 | 独立-2 | low | no | self-inflicted | product | accepted | 通知の前置きの成功・失敗の 2 つの分岐が、merge でないコマンド（parse-error の行）と gh pr merge --auto の場合を覆わない |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 失敗の分岐（直して再実行）が、post-merge-qa.md と followup skill の「通知が出たら報告して止まる」と割れる |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 記録の形式 would-block:<code> が SECURITY.md・hook の冒頭のコメント・テストの説明で古いまま |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | reason code: の側の分岐を通る code の記録を確かめるテストが無く、既存の assert も区切りを含まない部分一致 |
| I2-6 | 独立-2 | low | no | inherited | doc-claim | re-reported | merge gate が止める前提の references の記述が残る（I1-6 と同じ） |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | ADR の「承認の無い merge の多くは approval 系でない行に入る」は実測ではなく推論 |
| I2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片が、通知の前置きの成功・失敗の分岐を書いていない |
| I3-1 | 独立-3 | medium | no | self-inflicted | product | accepted | merge の前に確かめる手順（gdd-pr-review-followup SKILL.md:143、post-merge-qa.md:27）に、確かめる道具（hook の判定を merge なしで走らせる入口）も、待ちの起点・長さ・条件の正本への参照も無い |
| I3-2 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | 利用者向けの記述（hooks.json の (10)、README.md:489、SECURITY.md:109）が今も merge gate は merge を止めると書く |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | agent 向けの規定・テストの注記・ADR（self-review-lanes.md:121-122、independent-review.md:19、post-completion-pr-flow.md:87、TROUBLESHOOTING.md:240-242 など）が止める前提のまま |
| I3-4 | 独立-3 | low | no | self-inflicted | product | accepted | 通知の文（失敗したら直して再実行）と手順（通知が出たら報告して止まる）が食い違う |
| I3-5 | 独立-3 | low | no | self-inflicted | product | accepted | 通知の前置きが成功・失敗の 2 通りだけで、merge でないコマンドの解析失敗・--auto の予約・--disable-auto に合わない |
| I3-6 | 独立-3 | low | no | self-inflicted | test-power | accepted | reason code の側から code を取り出す分岐（不足条件を含まない 7 つの code）を確かめるテストが無い |
| I3-7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | env-s ADR の置き換えの印が、merge gate に関係しない制約（pre-push gate の非対称・共有部品）まで外している |
| I3-8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 新しい ADR の Context の数（54 回の内訳、415 件と 357 件の母数）と数え方が書かれていない |
| I3-9 | 独立-3 | low | no | self-inflicted | product | accepted | would-block の行を repo の hash で transcript と突き合わせる手順が、binding で切り替えた worktree の行に当たらない |
| I3-10 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md:99 が systemMessage を出力に挙げず、:274 と hook の :19 が記録の形の [,<code>…] と merge でない行を落としている |
| I3-11 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片が、記録を必ず残すように読め、Affected Files に ADR の 3 ファイルを挙げていない |
| I3-12 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | Stop hook の説明（state-machine.md:51 など）が、もう起きない merge gate の拒否を扱っている |
| I3-13 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | suppression ログの書式を固定する正規表現が would-block の行を受け付けず、would-block の行に書式の検査が当たっていない |
