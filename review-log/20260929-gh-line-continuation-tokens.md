---
lane: L1+
pr: 238
follow_up_of: 234
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。メインの草案〔git_command_parse.split_segments による行単位の第二の検出を和集合にする〕に対し、Opus は実データ 19,537 件で、草案が上乗せする merge 26 件は全部誤検知で本物 0 件、見落としの原因は shlex が行継続を次の語の先頭の改行にすることだけ、と実測して、両方の gate の tokenizer で token の先頭の改行を落とす案を推した。メインが同じ実測を再実行して確かめ、Opus の案に合わせたので食い違いは残らず、Fable は呼んでいない） | - | 1 | 1 | 1 | 2026-09-29T09:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 04f97e8d | 4 | 1 | 4 | 2026-09-29T10:14+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 594e7195 | 6 | 0 | 6 | 2026-09-29T10:45+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火〔nested-lex・prefilter の high が独立-1・独立-2 で続いた〕。ユーザーの 2026-09-28 の決定で、HITL は内部の相談で代えた。メインの案〔指摘 1 は入れ子の本体で commenters を空にする。指摘 2 は token の後処理をやめ、字句解析の前に行継続を空白 + 改行に置き換える。指摘 3〜6 は main でも見落とす既存の形で、実データの本物 0 件なので限界にする〕に対し、Opus は試作と実データ 19,537 件の計測で同じ方向を推し、無条件の置き換えは語の途中の `1\` + 改行 + `23` を PR 23 と読み違える退行を入れると実行で示して、語の途中は置き換えない条件を足した。方向の食い違いは無く、Fable は呼んでいない） | - | 1 | 0 | 1 | 2026-09-29T11:34+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | e01877a9 | 4 | 0 | 4 | 2026-09-29T13:08+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の 2 回目の発火〔独立-1・2・3 のすべてに high、直前の修正が次の high を生む型が 3 巡〕。ユーザーの 2026-09-28 の決定で、HITL は内部の相談で代えた。メインの案〔V1・V2 は直した。V3・V4 は main も同じ既存の形で実データ 0 件なので限界にし、差分巡 1 回で止める〕に対し、Opus は実データ 19,537 件と約 2 万通りの変形の fuzz で main との比較を測り、落とした 0 件を確かめて同じ方向を推した。違いは、pre-PR の埋め込み python を lib の import に寄せる案は fail-open の経路を増やすので入れず、複製の規則がずれないことを固定するテストだけを足す点。Fable は呼んでいない） | - | 0 | 1 | 0 | 2026-09-29T13:34+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分, model: opus | 9e342066 | 4 | 0 | 4 | 2026-09-29T15:02+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分, model: opus | 1ab69547 | 4 | 0 | 4 | 2026-09-29T15:37+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | high | yes | inherited | line-continuation | fixed | 行単位の第二の検出（草案）は、実データで誤検知 26 件・本物 0 件の上乗せで、cd の先を解かない・lib の import が main の検出を落としうる・再帰と heredoc の走査で例外や timeout になる経路を持ち込む。作らず、token の先頭の改行を落とす案にした。commit: 1aef8191 |
| P2 | 方針メモ | medium | no | inherited | pr-scope | accepted | 旧#234 の限界の形（K3・N3・N4・Q1〜Q4。実データ 19,537 件で 0 件）はこの PR では閉じない。PR 本文の限界に書く |
| R1 | 独立-1 | high | yes | self-inflicted | empty-token | fixed | merge gate の後処理が、先頭の改行を落とすと空になる token を捨てるので、空の値（`--body ""`・`-R ''`）が消えて flag が次の語を取り込み、PR 番号の読み違いと merge の見落としが起きる。token は消さず、空・演算子だけになるものは元のまま残す。commit: 70297971 |
| R2 | 独立-1 | high | yes | self-inflicted | empty-token | fixed | pre-PR gate も同じ原因で `gh --repo "" pr create` を PR 作成と判定せず、`--body "" --head other` の head を検証しない。R1 と対で直した。commit: 70297971 |
| R3 | 独立-1 | high | yes | inherited | prefilter | fixed | pre-PR gate の前段の照合が `pr create` の 2 語の字面で絞るので、空白 2 つ・引用符・TAB・行継続を挟んだ `gh pr create` が python に届かない。merge gate と同じく 1 語（`create`・`new`・`pulls`）で絞る。commit: 70297971 |
| R4 | 独立-1 | high | yes | inherited | nested-lex | fixed | pre-PR gate の `bash -c`・`eval` の本体を `punctuation_chars` なしで割るので、演算子に密着した `gh` を見落とし、`eval` は 1 語しか読まない。top-level と同じ字句解析にし、`eval` は区切りまでつなぐ。commit: 70297971 |
| R5 | 独立-1 | medium | no | self-inflicted | line-continuation | fixed | 行継続の扱いが pre-push gate（字句解析の前に文字列で除く）と別方式で、ADR の計画と食い違う。ADR に追補を足し、方式の理由と受理する入力の違いを書いた。commit: 70297971 |
| R6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 利用者から見える挙動の変化（flag と値の間の行継続）が断片に無い。改行だけの token を残すようにしたので、この変化は起きなくなった（main と同じ）。断片を今の挙動に合わせた。commit: 5389cc1a |
| R7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 実データの比較が検出の有無だけを見ている。pre-PR の COMMAND_INFO の全 key と merge gate の全 key に広げて比べ、両方で検出したもの（PR 作成 1,143 件・merge 863 件）の値の差は 0 件だった。PR 本文に書く。commit: なし（PR 本文） |
| R8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 「落ちない」テストが前段の照合を通らない入力で、判定を assert していない。末尾の行継続で block の reason・`is_merge`・`pr_number` を assert するテストにした。commit: a99fc89c |
| R9 | 独立-1 | low | no | self-inflicted | test-power | fixed | `eval` の本体への適用を戻しても落ちるテストが無い。`eval` の行継続の subTest を足した。commit: a99fc89c |
| R10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | tokenizer と素の shlex が一致するという不変条件が、後処理の後は一般には成り立たない。docstring に後処理を書き、テストの不変条件のコメントを改行を含まない入力に限った。commit: 70297971 |
| T1 | 独立-2 | high | yes | self-inflicted | nested-lex | fixed | pre-PR gate の入れ子の本体を shlex 既定の `#` 規則で割るようになり、`bash -c 'echo $#; gh pr create …'`・`eval 'n=${#a}; …'`・`a#b` の後ろの gh を見落とす（main・base は検出）。入れ子の本体では commenters を空にする。commit: 84f57c20 |
| T2 | 独立-2 | high | yes | self-inflicted | line-continuation | fixed | 改行だけの token を残したため、字下げ付きの行継続が gh と pr の間・pr と create/merge の間・`bash -c` と本体の間・flag と値の間に来ると、2 つの gate が見落とすか値を改行として読む。token の後処理をやめ、字句解析の前に行継続を空白 + 改行に置き換える（語の途中は置き換えない）。commit: 84f57c20 |
| T3 | 独立-2 | high | yes | inherited | nested-lex | accepted | pre-PR の `eval` の連結が引用符で書いた区切り（`eval "true" "&&" "gh pr create …"`）で止まり、後ろの gh を見落とす。main も見落とす。実データの本物 0 件。PR 本文の限界の先頭に書き、字句解析の lib への統合（旧#234 の載せ直し）で扱う |
| T4 | 独立-2 | high | yes | inherited | prefilter | accepted | pre-PR の前段の照合を、語の中の引用符・`\`（`cr''eate`・`cr\eate`・`ne''w`・`pu''lls`）で抜ける。main も抜ける。実データの本物 0 件（候補 7 件はすべて散文）。PR 本文の限界の先頭に書く |
| T5 | 独立-2 | high | yes | inherited | prefilter | accepted | merge gate の前段の照合も `mer''ge`・`mer\ge` で抜ける。main も抜ける（コードを読んで判断、実行では未確認）。PR 本文の限界の先頭に書く |
| T6 | 独立-2 | high | yes | inherited | nested-lex | accepted | pre-PR の入れ子の shell の認識が merge gate と違う（`bash --norc -c` の `--norc` を `-c` と読む、`dash`・`ksh` を展開しない）。main も見落とす。旧#234 の K3 と同じ形。PR 本文の限界の先頭に書く |
| T7 | 独立-2 | low | no | self-inflicted | performance | accepted | `eval` を区切りまでつないで割り直すので、`eval` を N 個並べると計算量が N の 2 乗になる（eval×2000・約 10KB で約 3.1 秒、hook の timeout は 10 秒）。PR 本文の限界に書く |
| T8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 前段の照合の説明が「コマンドの語」になっているが、実際は payload 全体の部分文字列で、cwd に new・create を含むと毎回 python が走る。コメントと断片を直した。commit: ee00795a |
| T9 | 独立-2 | low | no | self-inflicted | test-power | fixed | 改行だけの値のテストの `--title "\n"` は、捨てても解析がずれない位置で判別しない。`gh --repo "\n" pr create` にした。commit: c096d772 |
| T10 | 独立-2 | low | no | self-inflicted | test-power | fixed | 改行・行継続だけの入力で例外が出ないテストが消えていた。merge 側に `"\\\n"`・`"\n"` で is_merge が false になるテストを戻した。commit: c096d772 |
| T11 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files に `test_merge_gate_hook_quoted_operator.py` が無い。足した。commit: ee00795a |
| T12 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の実測に計測した sha と再現の手段が無い。PR 本文に書く。commit: なし（PR 本文） |
| U1 | 方針メモ-1 | high | yes | self-inflicted | line-continuation | fixed | 行継続を無条件に空白 + 改行へ置き換えると、`gh pr merge 1\` + 改行 + `23` を PR 23 と読み、別の PR の承認を借りる（main・base・head は PR を特定できないとして止める）。前後がどちらも語の文字なら置き換えない。commit: 84f57c20 |
| V1 | 独立-3 | high | yes | self-inflicted | line-continuation | fixed | 行継続の置き換えを 1 組ずつ判定したため、続く行継続（`1\` + 改行 + `\` + 改行 + `23`）で語が 2 つに割れ、merge gate が PR 23 と読んで、done 後は承認を見ずに通す（base は止めていた）。続く行継続を 1 まとまりで判定する。commit: dbe1ad67 |
| V2 | 独立-3 | high | yes | self-inflicted | nested-lex | fixed | pre-PR の入れ子の本体が語頭の `#` のコメントも読み、コメントの中の flag（`# -X GET`・`# --head …`）が後勝ちで効く（base は捨てていた）。語頭の `#` から行末までを捨てる規則を、merge gate と同じ内容で複製した。commit: dbe1ad67 |
| V3 | 独立-3 | high | yes | inherited | heredoc-continuation | accepted | heredoc の導入行が行継続で終わる形（`cat <<'EOF' && \` + 改行 + `gh …`）は、heredoc 本文の除去が物理行単位なので、次の行の gh を見落とす。main も同じ。実データの本物 0 件（誤一致 1 件）。PR 本文の限界の先頭に書く |
| V4 | 独立-3 | high | yes | inherited | body-scan | accepted | 二重引用符の中の行継続を bash のように取り除かないので、行継続で折った秘密が PR 本文の機密検査に当たらない。main も同じ。実データで本文に行継続が残る PR 作成 0 件（348 件中）。ADR の記述は実態に合わせた（commit: 7bc06d0f）。PR 本文の限界の先頭に書く |
| V5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | `_tokenize_checked` の docstring とテストの注記が、置き換えの後の文字列と素の shlex が一致するとしているが、語頭コメントと fd 番号の除去も通る。文言を直した。commit: dbe1ad67 |
| V6 | 独立-3 | low | no | self-inflicted | product | accepted | 置き換えの判定が生の文字を見るので、エスケープした区切り文字の直後（`echo a\;\` + 改行 + `gh pr merge 7`）や単引用符の中で過検出する。block の側に倒れるだけ。PR 本文の限界に書く |
| V7 | 独立-3 | low | no | self-inflicted | test-power | accepted | `group(1)`（エスケープした `\\` の直後）の行継続のテストが無い。続く行継続と pre-PR の語の途中は、今回テストを足した。残りは `follow_up_of` がある PR なので accepted |
| V8 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の実測に再現の手段が無い。PR 本文に計測のコマンド（`remeasure2.py`）と sha を書く。commit: なし（PR 本文） |
| W1 | 方針メモ-2 | medium | no | self-inflicted | duplicate-rule | fixed | pre-PR の埋め込み python が複製している行継続・語頭コメントの規則と `WORD_BOUNDARY_CHARS` が、lib とずれないことを固定するテストが無い。乱数の入力 2 万件で複製と lib を比べるテストを足した。commit: 979a7879 |
| X1 | 独立-4 | high | yes | self-inflicted | nested-lex | fixed | 行継続の置き換えが、直前の区切り文字がエスケープされているか（`a\ ` + 行継続 + `#x`）を見ず、次の行の `#` を語頭コメントとして捨てて、後ろの gh を見落とす（merge gate と pre-PR の入れ子の本体）。エスケープした区切り文字は語の文字として扱う。commit: 6b059f30 |
| X2 | 独立-4 | high | yes | self-inflicted | nested-lex | fixed | 語頭コメントの除去が `$'…'`（ANSI-C 引用）を知らず、中の `\'` で引用が閉じたとみなして、後ろの gh を捨てる。`$` の直後の単引用符の中では `\` を次の 1 文字のエスケープにする（lib と埋め込みの両方）。commit: 6b059f30 |
| X3 | 独立-4 | high | yes | inherited | eval-timeout | accepted | pre-PR gate の `eval` を N 個並べると割り直しが N の 2 乗になり、10 秒の timeout で block を返せない。main も同じ（推定、閾値は未計測）。独立-2 の T7 と同じ。PR 本文の限界に書く |
| X4 | 独立-4 | high | yes | inherited | eval-timeout | accepted | merge gate の `_scan_tokens` が、`eval` を n 個並べると n の 4 乗になり、timeout で block を返せない。main も同じ再帰（推定、閾値は未計測）。この差分の変更とは無関係。PR 本文の限界に書く |
| X5 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 変更断片の「bash と同じ」が、X1・X2 の形では成り立たなかった。X1・X2 を直し、断片の書き方を実装の保証に合わせた。commit: 6b059f30 |
| X6 | 独立-4 | advisory | no | self-inflicted | doc-claim | fixed | ADR 追補の「改行を残す理由」が、pre-PR の入れ子の本体の語頭コメントの除去に追いついていない。commit: 6b059f30 |
| X7 | 独立-4 | advisory | no | self-inflicted | doc-claim | fixed | 変更断片の Validation 欄が、足したテスト（続く行継続・入れ子の語頭の `#`・複製と lib の一致）を挙げていない。commit: 6b059f30 |
| X8 | 独立-4 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の実測が、どの時点のコードで測ったものか分からない。tip で測り直し、`at <sha>` を PR 本文に書く。commit: なし（PR 本文） |
| X9 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | reviewer が `advisory: テンプレート外の記述あり` を報告した。起動時の git status に載る最近の commit の件名（巡・実装順序を含むもの）が届いた。履歴は書き換えない。以後の commit の件名は変更の内容だけにする（この巡は有効のままにする。手順 6） |
| Y1 | 独立-5 | high | yes | self-inflicted | nested-lex | fixed | 語頭コメントの除去が `$$'…'` まで ANSI-C 引用と読み（`$$` は PID で、後ろの単引用符は通常の引用）、後ろの gh を捨てる（引用の数が釣り合う形）。`$` が続くときは 2 つ目を数えない。lib と埋め込みの両方。commit: 15f90618 |
| Y2 | 独立-5 | high | yes | inherited | nested-lex | fixed | `$` + 行継続 + `'…'` を ANSI-C 引用と読まない（bash は `$` の次の文字を読む前に行継続を消す）。エスケープ分岐で行継続なら `$` の直後の状態を保つ。commit: 15f90618 |
| Y3 | 独立-5 | high | yes | inherited | ansi-c-shlex | accepted | shlex と `_mask_quoted_operators` が ANSI-C 引用を読めず、引用の数が釣り合う形（`echo $'it\'s' ; gh pr merge 7 ; echo \'`）で gh が 1 つの token に飲まれる。main も同じで、CHANGELOG.md と ADR に既存の限界として開示済み。差分は悪化させていない。PR 本文の限界の先頭に書く |
| Y4 | 独立-5 | high | yes | inherited | ansi-c-shlex | accepted | pre-PR の top-level は語頭コメントの除去を通らず、ANSI-C 引用と語頭の `#` を読めない（`git commit -m $'fix: don\'t break #12' && gh pr create …`）。main も同じ。入れ子の本体との非対称が生まれた。PR 本文の限界の先頭に書く |
| Y5 | 独立-5 | low | no | self-inflicted | test-power | accepted | ANSI-C の新テストが 1 行の形で、shlex の縮退に頼っており、hook の判定（parse-error）を固定していない。引用の数が釣り合う形と `$$`・`$` + 行継続のテストは今回足した。`follow_up_of` がある PR なので accepted |
| Y6 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 断片の「bash と同じ」が実装の保証より広い。主語を語頭の判定に限り、読む形を列挙した。commit: 15f90618 |
| Y7 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 「語の途中」の定義（エスケープした区切り文字も語の文字）が lib の docstring にしか無かった。ADR・埋め込みのコメント・断片に足した。commit: 15f90618 |
| Y8 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | merge gate 自身の挙動の変化（`$'…\'…'` を含む入力が parse-error で止まる）が断片に無い。足した。限界の最終行の例外は PR 本文に書く。commit: 15f90618 |
| Y9 | 独立-5 | low | no | inherited | doc-claim | fixed | 実データの母数が ADR・テスト（19,537 件）と PR 本文（19,840 件）で食い違う。tip で測り直し（28・47 件は同じ）、3 箇所を 19,840 件に揃えた。commit: 15f90618 |
| Y10 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | 実データ比較の sha が書かれていない。PR 本文に sha と計測の手順を書く。commit: なし（PR 本文） |
| Y11 | 独立-5 | advisory | no | self-inflicted | style | fixed | PR 本文の抜粋で句点が落ちている。PR 本文では直す。commit: なし（PR 本文） |
