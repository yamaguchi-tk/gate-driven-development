---
lane: L1
pr: 527
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 9ba6d257ceef8c02068751d39afc5bf39e85a795 | 0 | 1 | 0 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 0fb99e6f591371804b3e6b294f3fa6f6ea985539 | 0 | 0 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 2026-10-16 にユーザーが推奨（別の PR）で OK と答えた。merge gate のテストを確認なしに後回しにしていた。hook のコードを変えずにできる分（コマンドの表で、hook に同じ入力が渡る行を 1 回だけ起動する形）はこの PR に入れた（commit: 4b0bfcd0・51ff6c45・ef054b82）。hook のコードを変える軽量化と、repo の状態で行が違う表は別の PR にする案で進め、ユーザーに確かめる |
| r1-2 | 独立-1 | low | no | self-inflicted | measurement | fixed | 全量への効果に数字が無い。変えたファイルの CPU 時間を変更の前後で測り、PR 本文に書いた。commit: なし（PR 本文） |
| r1-3 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 改行で終わる toplevel の 18 通りを、lib の関数を直接呼ぶ形ではなく、先頭の hook の起動で見ている |
| r1-4 | 独立-1 | low | no | self-inflicted | test-power | accepted | done guard の表は validate_done_preconditions を通らないので、その中の前処理の変化は各表の先頭 1 件でしか見えない。PR 本文の限界の書き方を直した |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | done guard のテストの module docstring と _run_verification の docstring が、古い測り方を説明している |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | _judge_in_process の docstring が、理由をつなぐのを hook の main と書いている（実際は validate_done_preconditions） |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が merge gate のテストに触っていないと書くが、2 本を変えている。commit: なし（PR 本文） |
| r1-8 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | PR 本文の限界に種類が無い。commit: なし（PR 本文） |
| r1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | PR 本文の秒数に、測ったコマンドと sha が無い。commit: なし（PR 本文） |
| r1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Summary が差分と合わず、Validation にコマンドが無い。commit: 0fb99e6f |
| r1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | test_confirmed_text の「repo はケースで変えない」のコメントが、綴りのテストには当たらない（毎回同じ docs/new.md を書く） |
| r1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 消したテストの名前が docs/design/2026-08-21-pr-w3-self-review-adr.md に残る（履歴の文書） |
| r1-13 | 独立-1 | advisory | no | self-inflicted | style | accepted | test_confirmed_text の _run_copy のローカル変数 copy が、足した import copy を隠す |
| r1-14 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 別ファイルのテストのクラスを名前で import して二重に集める型を止める仕組みが無い（今の件数は 0） |
| r2-1 | 独立-2 | medium | no | self-inflicted | request-scope | re-reported | r1-1 の再報告（repo の状態で行が違う merge gate の表を別の PR にする） |
| r2-2 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 2026-10-16 にユーザーが推奨（この形のまま）で OK と答えた。merge gate の表は、関数を直接呼ぶ形ではなく、hook に同じ入力が渡る行を 1 回だけ起動する形にした（手段を代えた） |
| r2-3 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 2026-10-16 にユーザーが推奨（止める）で OK と答えた。重複の判定を遅い上位 200 本で止めた |
| r2-4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 列挙: 組の鍵の前提を守るテストは、hook の "$PAYLOAD" の形しか拾わず、source する lib と鍵の写し（merge の語・cwd）の変化を拾わない。PR 本文の書き方を保証の範囲に合わせた |
| r2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | 列挙: cd_after_merge・gate_regressions・explicit_target は、組ごとの起動を _run に隠しており、途中で state を書くテストを足すと古い判定を返す（今は該当 0 件） |
| r2-6 | 独立-2 | low | no | self-inflicted | test-power | accepted | hook_input_class は pytest の env で走るので、手元で GH_REPO を export していると鍵が hook と違う（今の表には該当する行が無い） |
| r2-7 | 独立-2 | low | no | self-inflicted | product | accepted | 埋め込みの python の sys.path.insert が worker の中で積み重なる |
| r2-8 | 独立-2 | low | no | self-inflicted | style | accepted | HOOK_SCRIPT・LIB_DIR を _merge_gate_support と同じ値で定義し直している |
| r2-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文に、時間の数字と測り方が無い。PR 本文に CPU 時間の前後とコマンドを書いた（断片は直していない） |
| r2-10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片の「2 本を消した」と PR 本文の「上位 200 本で消せたのは 4 本」の内訳が読み手に分からない。PR 本文に内訳を書いた（断片は直していない） |
