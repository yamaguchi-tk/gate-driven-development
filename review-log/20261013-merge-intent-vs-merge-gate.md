---
lane: L1+
pr: 448
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | ecd389be | 0 | 0 | 0 | 2026-10-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | dd86a0ee | 0 | 3 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6f9e2b06 | 1 | 0 | 1 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6b7f9c14 | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | advisory | no | inherited | design | accepted | 採用: 拒否のマーカーは merge gate に加えて PreToolUse hook と auto mode classifier の拒否も数え、review-wait-not-elapsed だけの拒否は除く。宣言の書き込みより後の拒否だけを数え、PR 番号の無い gh pr merge は一致とみなし、gate と同じ parse_gh_pr_merge で読む。置き場所は Stop hook の cwd の toplevel の 1 か所 |
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | 拒否の判定が 3 つの接頭辞の列挙で、未知の拒否の形では押し返す。実データ 323 件で Exit code 以外の is_error は全部走る前の拒否だったので、Exit code で始まらない is_error を拒否とする形に変えた commit: ec1f0075 |
| I1-2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | merge gate の文を 200 文字以内で探していた。実データの拒否は全件 1 行目の先頭か 28 文字目で、200 を超えたのは Exit code の出力だけだったので、1 行目で探す形に変え、実際の拒否の文の形を fixture にした commit: ec1f0075 |
| I1-3 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 壊れた行のテストが、例外で押し返さない場合も通っていた。hook エラーの記録が無いことと、同じ雑音で拒否でない試行なら押し返すことを assert した commit: ec1f0075 |
| I1-4 | 独立-1 | low | no | self-inflicted | test-power | fixed | review-wait-not-elapsed だけかを FAILURES[0] の並びに頼って判定していた。送出の行の 不足条件 を読む形にし、書式を契約テストで固定した commit: ec1f0075 |
| I1-5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 別の worktree の宣言を読まないテストが、宣言ありの押し返しでも通っていた。約束の押し返しであることと gh を呼ばないことを assert した commit: ec1f0075 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | state-machine.md の Stop hook の判定順序に、押し返さない新しい条件が無かった commit: ec1f0075 |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 番号の無い gh pr merge の扱いが、断片・docstring では branch から推定する形だけと読めた。番号・URL で PR を特定できない形全般と書いた commit: ec1f0075 |
| I1-8 | 独立-1 | low | no | self-inflicted | product | fixed | merge を含む行を全部読み、同じ行を 2 回 json で読んでいた。Bash を含む行に絞り、1 行 1 回にし、試行の多い transcript の締め切りのテストを足した commit: ec1f0075 |
| I1-9 | 独立-1 | low | no | self-inflicted | product | fixed | 共有の解析器を module の読み込みで import しており、import の失敗で Stop hook ごと落ちうる。押し返しの thread の中で import する形にした commit: ec1f0075 |
| I1-10 | 独立-1 | low | no | self-inflicted | product | fixed | 理由文に載せる宣言の絶対パスに制御文字の検査が無かった。含むなら相対の書き方にした commit: ec1f0075 |
| I1-11 | 独立-1 | low | no | self-inflicted | test-power | fixed | 新しいテストが if __name__ == "__main__" の後ろにあり、直接実行では走らなかった commit: ec1f0075 |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文に走査のコマンドと、classifier・ほかの hook の拒否の後の押し返しの件数が無かった commit: なし（PR 本文） |
| I1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | セッションの cwd が GDD の worktree に残る構成では、hook は GDD の worktree の宣言を読む。文書の「GDD の worktree で作業していてもこちら」は通常の構成の話で、押し返しの文の絶対パスが正本 |
| I2-1 | 独立-2 | high | yes | inherited | fail-open | fixed | 理由文の待機スクリプトの絶対パスに surrogate が入ると、Stop hook の出力で UnicodeEncodeError になり、stop_hook_active の停止では done guard ごと通る。run_within_deadline で encode できない理由文を押し返さず key も残さない形にした commit: 39b9dbfe |
| I2-2 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | 押し返さない側のテスト（締め切り・variants）が、走査が例外で落ちた場合も通る。hook エラーの記録が無いことの assert が無い |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | hooks.json の description が、Exit code で始まらない is_error を全部拒否と読むことと、PR を特定できない形を対象とみなすことを書いていない |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | post-merge-qa.md の「上の拒否」が、コードの受理範囲（Exit code で始まらない is_error 全部）より狭く読める |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | docstring と post-merge-qa.md が、理由文に常に絶対パスを出すと書く（制御文字を含むパスは相対で出す） |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 変更断片も、絶対パスを示すと無条件に書いている |
| I2-7 | 独立-2 | low | no | self-inflicted | product | next-pr | is_error で本文が空の結果を拒否と読まず、押し返す |
| I2-8 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 契約テストが CODES の末尾の区切りを落とす行と、review-wait-not-elapsed を直接出す block の行を固定していない |
| I2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 不足条件を持たない旧形式の review-wait-not-elapsed だけの拒否も、拒否と読む（今の merge gate は必ず不足条件を出す） |
| I2-10 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 実測の根拠が、実行できるコマンドではなく散文で書かれている |
| I3-1 | 独立-3 | low | no | self-inflicted | product | next-pr | 本番は UTF-8 mode（surrogateescape）で動くので、理由文の surrogate は出力で例外にならず、encode の検査で押し返しが出なくなる。WAIT_SCRIPT を _has_unsafe_char で判定して置き換え、コメントを実際の仕組みに直す |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | encode できない理由文を押し返さないことと、宣言のパスを相対で出すことが、変更断片に無い |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | post-merge-qa.md の押し返さない条件の列挙に、理由文を UTF-8 に encode できないときが無い |
| I3-4 | 独立-3 | advisory | no | inherited | product | accepted | WAIT_SCRIPT の制御文字は encode を通り、理由文にそのまま載る（パスは plugin を置いた利用者が決める） |
| I3-5 | 独立-3 | advisory | no | inherited | product | accepted | done guard の payload など、ほかの block の出口も ensure_ascii=False の print で、範囲外の surrogate では例外になりうる（この PR で悪化はしていない） |
| I3-6 | 独立-3 | advisory | no | self-inflicted | product | accepted | encode の失敗では key を残さないので、Stop のたびに gh pr view と理由文の全文を含む hook エラーの記録が繰り返される |
| I3-7 | 独立-3 | advisory | no | inherited | doc-claim | fixed | PR 本文の、両方の文が GDD の worktree でもこちらに書くと書くように読める記述 commit: なし（PR 本文） |
