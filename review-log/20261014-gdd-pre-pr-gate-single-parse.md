---
lane: L1+
pr: 旧#507
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 1 | 0 | 2026-10-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 9e78a7281b9888d973e23244056533fb7091ffec | 2 | 0 | 2 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 7b426be3fff53be0f4957a237718b2bb953236fc | 2 | 0 | 2 | 2026-10-15 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-15 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 5dc8a657fe71495f339dd15c9173d26646976486 | 0 | 0 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| m-1 | 方針メモ | medium | no | self-inflicted | design | fixed | 草案（欄の取り出し専用の python3 を足す）は raw steering の検査を飛ばす経路を増やす。解析の python が merge gate と同じ key/value で直接出す案 C に変えた。ユーザーが案 C を承認。commit: なし（方針メモ） |
| r1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | here-string（done <<< "$PARSE_OUTPUT"）を一時ファイルで作れないと、bash 4 以上は set -e で出力なしの exit 1 になり、deny を全部飛ばす。読めなかったら PARSED=false にした。macOS の bash 3.2 はリダイレクトの失敗で終わらないので、再現テストは手元では変更前も通る（bash 4 以上で落ちる形）。commit: 5748b1e9 |
| r1-2 | 独立-1 | high | yes | inherited | fail-open | fixed | merge gate の origin 以外の remote の set-default を読むループ（done <<<"$_others"）が失敗すると、_repo が origin のまま miss で通る。読めなかったら _repo を空（特定できない）にした。再現テストは変更前に落ちることを確かめた。commit: 5748b1e9 |
| r1-3 | 独立-1 | low | no | self-inflicted | test-power | accepted | PR 作成の python3 の起動回数のテストは、途中の exit 0 で抜けても回数が減ったとして合格する |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Summary: --head の照合が飛んでいたのは --head の値に lone surrogate があるとき、空になったのは UTF-8 で書けない surrogate のときだけ、3 回→1 回は create・new・pulls を含む呼び出しのうち、タブ・改行が空白になる変化が無い |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文に、大きい本文（環境変数の上限を超えるもの）も検査するようになったこと、--base の lone surrogate・末尾の改行が解決できない base になることが無い。commit: なし（PR 本文） |
| r1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 800 組の一致に、比べたコマンドと sha が無い。差分が意図して変えた入力は transcript の実コマンドにほぼ入っていない。テストの外の速さに変更後の時間が無い |
| r1-7 | 独立-1 | advisory | no | self-inflicted | style | accepted | 解析中の例外のテストは、既存の test_pre_pr_gate_shared_lexer.py の renamed-functions と同じ経路を通る |
| r2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | merge gate の読めないときに _repo を空にする修正で、here-string を読めないと unknown になり、hit のときだけ止める git cwd の経路（828〜831 行）と出口（906〜910 行）で、今まで止めていた GDD の PR の merge が通る。主案はリダイレクトを使わない読み方。ユーザーが続行（A）を選び、here-string をやめてリダイレクトを使わない読み方にした（読めないときの分岐も消えた）。commit: 7f52b70a |
| r2-2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | pre-PR gate の here-string を読めないと PARSED=false になり、active GDD の外では raw steering の検査が飛ぶ（main は欄ごとの pipe で読むので飛ばない）。主案はリダイレクトを使わない読み方。ユーザーが続行（A）を選び、here-string をやめてリダイレクトを使わない読み方にした（読めないときの分岐も消えた）。commit: 7f52b70a |
| r2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文が merge gate の hit-only 経路の block → allow を書いていない |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片が merge gate の変更と新しいテストを載せていない。merge gate の変更と新しいテストを載せた。commit: 7f52b70a |
| r2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「判定は変えない」が here-string を読めないときを除いていない。800 組の比較は tip の hook ではない |
| r2-6 | 独立-2 | advisory | no | self-inflicted | product | accepted | merge gate の判定の変更は依頼と方針メモに無く、ユーザーの確認を経ていない |
| r2-7 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | pre-PR の here-string のテストは bash 4 以上でしか差分を戻したときに落ちない |
| r2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「bash 5.1 未満では一時ファイル」は狭い。5.1 以上でも pipe の容量を超えると一時ファイルを使う |
| r2-9 | 独立-2 | advisory | no | self-inflicted | style | accepted | merge gate の hook が 1,500 行の目安を超えたまま 1 行増えた |
| r2-10 | 独立-2 | advisory | no | inherited | product | accepted | scripts/check-gate-ledger.sh:319 の here-string にも読めないときの扱いが無い（開発者が回す検査） |
| hm-1 | 方針メモ-1 | low | no | self-inflicted | fail-open | fixed | 安全策 4 の発火（fail-open が独立-1・独立-2 で 2 回）。Opus の推奨は続行で、2 か所とも here-string をやめてリダイレクトを使わない読み方にし、読めないときの分岐も消す（pre-PR gate は配列を使わず set -f と改行の IFS の for、merge gate は同じファイルの _rest の形）。同じ型の差分の外の 4 か所は直さず限界に書く。ユーザーが続行（A）を選んだ。commit: なし（方針メモ） |
| r3-1 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の 800 組の照合は 9e78a728 の hook で、その後に書き直した解析結果のループを含まない。照合した sha と、tip のループはテストでだけ確かめていることを書き添えた。commit: なし（PR 本文） |
| r3-2 | 独立-3 | low | no | self-inflicted | test-power | accepted | merge gate の形のテストの assertIn('_repo=""') はループより前の行で満たされ、ループを固定していない（挙動は test_merge_gate_hook_non_gdd_merge.py の既存テストが固定） |
| r3-3 | 独立-3 | low | no | self-inflicted | test-power | accepted | 拒否する形のリスト（<<<・< <(・done <）は空白の無い形・here-doc・<& を拾わない |
| r3-4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | テストの docstring の 1 行目が gate の全ループを指すように読める（見るのは 2 か所だけ） |
| r3-5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 限界の節の、差分の外に残るループの一覧に pre-push gate・lib などが抜け、here-string とプロセス置換の失敗の条件を分けていない。grep の結果で列挙し、条件を分けた。commit: なし（PR 本文） |
| r3-6 | 独立-3 | low | no | self-inflicted | product | accepted | 空の解析出力のテストは test_pre_pr_gate_single_parse.py の既存テストと同じ状態を見ていて、修正を戻しても落ちない |
| r3-7 | 独立-3 | advisory | no | self-inflicted | style | accepted | テストのファイル名 test_here_string_read_failure.py が、here-string を使わないことを見る中身と合っていない |
