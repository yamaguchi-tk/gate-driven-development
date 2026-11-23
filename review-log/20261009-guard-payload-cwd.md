---
lane: L1+
pr: 423
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 1e5850c3 | 0 | 0 | 0 | 2026-10-09 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1d0cba88 | 2 | 4 | 2 | 2026-10-09 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 1d0cba88 | 0 | 0 | 0 | 2026-10-09 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | a2e68906 | 2 | 0 | 2 | 2026-10-10 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | a2e68906 | 0 | 0 | 0 | 2026-10-10 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 67115ce7 | 1 | 1 | 1 | 2026-10-10 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | f0e9b873 | 0 | 1 | 0 | 2026-10-10 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | medium | no | inherited | wiring | next-pr | 他の 4 hook（pre-push・merge・pre-PR gate、push 後の nudge）も tool_input の cwd とプロセスの cwd だけを読む。pre-push-optout.log の 10 月の session-mismatch 146 行は、root で判定して素通りした兆候。この PR は guard だけにし、gate は次の PR で測ってから直す |
| M2 | 方針メモ | low | no | inherited | scope | accepted | root にいるセッションが `cd <worktree> && git checkout -b` する 2 件の型は、cd の行き先より先に payload の cwd を判定するので残る。ユーザーが承認した推奨の 2 番目は「payload の cwd を読む」だけで、cd・-C の判定順は含まない |
| I1-1 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | 列挙: linked worktree の最上位の cwd で判定すると、root を守るのが実行先の列挙だけになる。(a) root が active でないときの `cd <root> &&`・`git -C <root>` の GDD 名のブランチ作成は、実行先にも cwd と同じ条件を当てて直した（入力者の実測: 9/25 以降の transcript で、root へのリテラルの cd・-C と gdd/ のブランチ作成が同じコマンドにあるもの 0 件、過剰 block になりうる形 0 件。commit: fc9cfcdb）。(b) `pushd <root>`・`if cd <root>; then`・`{ cd <root>; }`・変数の cd など、列挙が拾わない形は方針メモ-1 で (b) にした（desktop で root が active なときの block のうち root に届いたもの 0 件。CLI は未測） |
| I1-2 | 独立-1 | high | yes | inherited | fail-open | accepted | pre-push・pre-PR・merge gate は最上位の cwd を読まず、hook の cwd が root になるセッションでは worktree の GDD を検査せずに通す。この PR の依頼は guard だけで、方針メモ-1 で次の PR（M1）に回した。実害クラスなので数えから外さない |
| I1-3 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼の「15 件は消える」を確かめずに 13 件へ狭めた。ユーザーに確かめ（.request.md に追記）、先頭の `cd` が効いた形を cd の行き先で判定するようにした。commit: 75363b53 |
| I1-4 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 記録された block が消えるかを測っていない。記録された block を desktop の条件（hook の cwd を root）で旧版と新版に当て、PR 本文に数とコマンドを書いた。commit: なし（PR 本文） |
| I1-5 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 最上位の cwd の NUL・surrogate など、例外になりうる値のテストが無い。使えない値の一覧に足した。commit: fc9cfcdb |
| I1-6 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 使えない最上位の cwd のテストが、hook の cwd に戻ったことを固定していない。hook の cwd を root と worktree の両方にして判定が分かれることを見るようにした。commit: fc9cfcdb |
| I1-7 | 独立-1 | low | no | self-inflicted | product | fixed | 最上位の cwd の受け取り方が tool_input 側と揃っておらず、版によって使えない値で戻らない。`os.path.isdir` で受けるようにした。commit: fc9cfcdb |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 0.41.11 の「最上位の cwd は hook の cwd と同じ値」と食い違う。断片に CLI での実測と書き、未リリースの断片が当たらなくなることも書いた。commit: fc9cfcdb |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Affected Files・Validation が差分と合っていない。commit: fc9cfcdb |
| I1-10 | 独立-1 | low | no | self-inflicted | style | fixed | 新しいテストが hook の起動を共有の補助の外で持つ。`run_root_branch_guard_raw` に `process_cwd` を足して使った。commit: fc9cfcdb |
| I1-11 | 独立-1 | advisory | no | inherited | product | accepted | push の後の nudge も最上位の cwd を読まない。M1 の次の PR で扱う |
| I1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋が、依頼の 5 項目のどれを扱うかを書いていない。commit: なし（PR 本文） |
| M3 | 方針メモ-1 | - | - | - | - | - | なし |
| I2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | root のセッションで先頭の `cd <wt> &&` の後に、行き先を決められない移動（`cd -`・`cd $OLDPWD`・`cd ~-`・引数なしの `cd`・`env -C`・`<(cd …)`・`find -execdir`）があると、root へのブランチ作成を通す。範囲の検査が拒否する語のリストで、許可リストになっていない。閉じ方: 構造。入力者の実測: 9/25 以降の先頭 cd＋ブランチ作成 45 件のうち、cd の後に行き先不明の移動があるもの 0 件。方針メモ-2 でユーザーが A' を選び、範囲を git の fetch・checkout・switch・branch と記号を含まない語だけの許可リストにし、cd の引数を `/`・`~/`・`./`・`../` で始まるものに限った。commit: c1298d1e |
| I2-2 | 独立-2 | high | yes | inherited | fail-open | accepted | pre-push・pre-PR・merge gate が最上位の cwd を読まない（I1-2 と同じ。実害クラスなので re-reported にしない）。次の PR（M1） |
| I2-3 | 独立-2 | low | no | self-inflicted | product | fixed | 先頭の cd が効いた後でも、相対の `git -C` は payload の cwd を基点に解く（止める側に倒れる）。先頭の cd の部品を外したので、この形は無くなった。commit: f89dda51 |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 20261004 の断片と test_root_branch_guard_exec_target.py の「payload の cwd は候補に残したまま」が、先頭の cd の形では当たらない。先頭の cd の部品を外したので、記述は今の挙動と合う |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 最上位の cwd の `os.path.isabs` を固定するテストが無い |
| I2-6 | 独立-2 | low | no | self-inflicted | test-power | fixed | 範囲の引用符の規則を固定するテストが無い。先頭の cd の部品を外したので、この規則は無くなった。commit: f89dda51 |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の 15 件と記録 27 件の関係が書かれていない。commit: なし（PR 本文） |
| I2-8 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | replay の再現手順が PR 本文にコマンドとして無い。commit: なし（PR 本文） |
| I2-9 | 独立-2 | advisory | no | self-inflicted | product | fixed | 依頼の残りの項目（1・3・4・5 番）の行き先が PR 本文に無い。commit: なし（PR 本文） |
| M4 | 方針メモ-2 | - | - | - | - | - | なし |
| I3-1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 先頭の cd の引数を Python のパスの規則で解くので、シェルと解き方が違う形（`HOME=<root>; cd ~/ &&`、シンボリックリンクの後の `..`、引用符の中の `~`、glob・brace）が許可リストを通り、root へのブランチ作成を allow する。方針メモ-2 でユーザーが先に認めた出口のとおり、先頭の cd の部品（leading_cd_dir）を外し、root のセッションからの `cd <worktree> && git checkout -b`（旧#7・旧#8 の型）は今までどおり止める限界にした。commit: f89dda51 |
| I3-2 | 独立-3 | medium | no | self-inflicted | test-power | fixed | 区切りの条件を単独で固定するテストが無い。部品を外したので条件ごと無くなった。commit: f89dda51 |
| I3-3 | 独立-3 | low | no | self-inflicted | test-power | fixed | 入れ子のブランチ作成の数の条件に単独のテストが無い。部品を外したので条件ごと無くなった。commit: f89dda51 |
| I3-4 | 独立-3 | low | no | self-inflicted | test-power | fixed | `~/` の接頭辞を受けることを固定するテストが無い。部品を外したので無くなった。commit: f89dda51 |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | leading_cd のテストの docstring が受理条件に追いついていない。テストごと消した。commit: f89dda51 |
| I3-6 | 独立-3 | low | no | inherited | doc-claim | accepted | test_root_branch_guard_exec_target.py の「payload cwd が root なら、cd の先が worktree でも止まる」が、部品のある形では当たらない。部品を外したので、記述は今の挙動と合う |
| I3-7 | 独立-3 | low | no | self-inflicted | product | fixed | 依頼の「語は記号を含まないもの」を、シェルの特殊文字を含まないものに読み替えた。部品を外したので無くなった。commit: f89dda51 |
| I3-8 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の確かめ方に再現のコマンドが無い。commit: なし（PR 本文） |
| I4-1 | 独立-4 | medium | no | self-inflicted | test-power | fixed | 部品を外して戻した挙動（root のセッションからの `cd <worktree> && git checkout -b` を止める）を固定するテストが無い。I3-1 の実害の再現テストとして、test_payload_cwd_stays_a_candidate に 4 形を足した（部品のあった版では 3 件が落ちる）。テストだけの commit なので巡は無効にならない。commit: bc6d7bd2 |
| I4-2 | 独立-4 | low | no | self-inflicted | product | fixed | 限界の節に、ユーザーが選んだ「2 件も消す」を、先に決めた出口（この部品に fail-open の high が出たら外す）で外したことが書かれていない。commit: なし（PR 本文） |
| I4-3 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 限界の節の「コマンドの文だけからは閉じられない」が、挙げた例より広い断定になっている。commit: なし（PR 本文） |
| I4-4 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 「worktree に移ってから打てば止まらない」に裏付けが無い。commit: なし（PR 本文） |
