---
lane: L1+
pr: 433
follow_up_of: 246
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | d99fcea5 | 0 | 2 | 0 | 2026-10-11 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f640a22c | 5 | 0 | 5 | 2026-10-11 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 2a97e4d0 | 0 | 0 | 0 | 2026-10-12 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 730c5626 | 2 | 1 | 2 | 2026-10-12 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | 140137bf | 0 | 0 | 0 | 2026-10-12 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 3136adac | 2 | 0 | 2 | 2026-10-12 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 85fa0e6e | 4 | 1 | 4 | 2026-10-12 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | c631743b | 0 | 0 | 0 | 2026-10-12 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | c631743b | 4 | 2 | 4 | 2026-10-12 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | b1165899 | 2 | 0 | 2 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | medium | no | self-inflicted | design | fixed | lib/pr_create_parse.py に移すと約 280 行が全差分の変更行になり、既存の穴が self-inflicted として出直す。module は作らず、hook の中の python から字句解析の関数を消して gh_command_parse を import する。commit: なし（方針） |
| P2 | 方針メモ | medium | no | self-inflicted | design | fixed | 寄せる先が依頼の文（git_command_parse）と違い、挙動も 4 件変わり、2 本目の中身も変わる。ユーザーに確かめ、回答を依頼の原文に足した。commit: なし（方針） |
| P3 | 方針メモ | low | no | self-inflicted | parse-exception | accepted | import の失敗は今の例外と同じく hook の exit 1（non-blocking）で通す、parsed の標識は足さない、とした。独立-1 の F1 を直すときにこの決定を覆し、merge gate と同じく parsed の標識を足して active GDD の中では止めるようにした（F1 の行） |
| P4 | 方針メモ | low | no | self-inflicted | test-power | fixed | InlineCopyMatchesLibTests は写しが消えると落ちるので消す。代わりに入口から import の失敗（module の削除・構文エラー）を再現するテストを足す。commit: なし（方針） |
| P5 | 方針メモ | low | no | inherited | line-continuation | accepted | 閉じない引用符の縮退（前段に当たる 29,905 件中 15 件）、引用符の中の本文の fd 番号の除去、両方が見落とす 11 形は、限界に書く |
| F1 | 独立-1 | high | yes | self-inflicted | parse-exception | accepted | lib を import できない・解析が例外で終わると hook が exit 1 で終わり、PR 作成を検査せずに通す（merge gate は止める）。止める block を 41bad978 で足したが、依頼の範囲外で cd 先も解けないため方針メモ-2 で外した（140137bf）。解析の例外は transcript の前段 29,960 件で 0 件。限界の節の先頭に書く
| F2 | 独立-1 | high | yes | self-inflicted | fd-strip | fixed | 列挙: lib の fd 番号の除去が引用符の中にもかかり、本文の `123456789012<br>` から数字が消えて 12 桁数字の検査が外れる。ユーザーが「この PR の lib 側で直す」を選んだ。fd 番号の除去を引用符の退避の後にかけた（merge gate の 30,283 件で解析結果の違い 0）。commit: 01143c19 |
| F3 | 独立-1 | high | yes | inherited | heredoc | accepted | 列挙: 1 語の here-string（`cat <<<word`）と算術の `<<` を heredoc と読み、後ろの行を捨てる。旧の写しも同じ regex。transcript で当たる PR 作成 0 件なので方針メモ-1 で (b)。限界の節の先頭に書く |
| F4 | 独立-1 | high | yes | self-inflicted | heredoc | accepted | 列挙: 実行される heredoc の本文を全行の後ろに足すので、heredoc より後ろの cd を本文の中の gh の cd 先と読む（旧はこの形を PR 作成と読まなかった）。transcript で 0 件なので方針メモ-1 で (b)。限界の節の先頭に書く |
| F5 | 独立-1 | high | yes | inherited | multi-create | accepted | 最初の PR 作成だけを検査し、同じ Bash の 2 本目の本文・作成先を見ない（main と同じ）。止める block を 41bad978 で足したが、依頼の範囲外で、5 件中 4 件は作成ごとに変数入りの cd があり hook では解けないため方針メモ-2 で外した（140137bf）。限界の節の先頭に書く
| F6 | 独立-1 | low | no | self-inflicted | heredoc | accepted | `bash script.sh <<EOF` のように script へ渡すだけの heredoc の本文も実行されるものとして読む（過検出）。入力が開いていて列挙で閉じないので限界に書く |
| F7 | 独立-1 | low | no | self-inflicted | product | fixed | heredoc の経路は dash・ksh を読むが、`-c`・eval の経路は bash・sh・zsh だけ。PR 本文の限界の節に書いた。commit: なし（PR 本文） |
| F8 | 独立-1 | low | no | self-inflicted | test-power | fixed | `echo fix#12; ls` は python に届かず、引用符の中の `&&` の扱いを固定するテストが無い。payload に new を含め、`--title "&&"` で本文の機密検査に届くテストを足した。commit: ae451c39 |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | ユーザーに示した母数（29,905）と PR 本文の母数が違い、測り方が無い。PR 本文で最新の母数と測り方を書く |
| F10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 旧い写しを前提にした記述が設計記録（ADR など 4 か所）に残る。日付つきの記録なので直さず PR 本文に書く |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 変更断片の検証の欄が hook を流すほかのテストを挙げていない。関係するテストのスクリプトの形にした。commit: 2a97e4d0 |
| R1 | 方針メモ-1 | - | - | - | - | - | なし |
| G1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 解析の失敗と複数の PR 作成の 2 つの block が依頼（挙動を変えずに）の外で、ユーザーの承認が無い。方針メモ-2 で 2 つとも外した。commit: 140137bf |
| G2 | 独立-2 | high | yes | self-inflicted | multi-create | fixed | 複数の PR 作成の block が 1 つ目の作成の cd 先だけで active GDD を決め、2 本目が別の GDD worktree なら通る。block を外した（F5 の行の限界に戻る）。commit: 140137bf |
| G3 | 独立-2 | high | yes | self-inflicted | parse-exception | fixed | 解析に失敗すると payload の cwd・workdir と cd 先が空になり、active GDD の worktree での PR 作成が通る。block を外した（F1 の行の限界に戻る）。commit: 140137bf |
| G4 | 独立-2 | low | no | self-inflicted | multi-create | fixed | 引用符の無い eval の引数に引用した複数語があると PR 作成を 2 件と数え、複数作成の block で止まる。block を外したので数えの誤りは判定に効かない。commit: 140137bf |
| G5 | 独立-2 | low | no | self-inflicted | test-power | fixed | 引用符の無い eval を 1 件と数えるテストが無い。数えを使う block を外した。commit: 140137bf |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | SECURITY.md:126 の「pre-PR gate は解析できないと通す」が古い。block を外したので記述が事実に戻った。commit: 140137bf |
| G7 | 独立-2 | low | no | self-inflicted | style | fixed | kill switch の案内文を merge gate と別のリテラルで書き写している。使っていた block ごと外した。commit: 140137bf |
| G8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 止める理由の文が「コマンド」と書くが前段は payload 全体に当てる。文ごと外した。commit: 140137bf |
| G9 | 独立-2 | advisory | no | self-inflicted | fd-strip | accepted | fd 番号の除去を退避の後にかけたので、FD_PREFIX_RE の `\s` が退避先の制御文字に当たりうる（U+0001〜U+0008 を 2 つ以上含むときだけ）。PR 本文に書く |
| G10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 複数作成の block（新しい発火条件）の件数のコマンドと止まる分が PR 本文に無い。block を外した。commit: 140137bf |
| R2 | 方針メモ-2 | - | - | - | - | - | なし |
| H1 | 独立-3 | high | yes | self-inflicted | parse-exception | accepted | lib を読めない・解析や本文ファイルの読み込みが例外で終わると hook が exit 1（non-blocking）で終わり、active GDD の中でも PR 作成を通す。merge gate は同じ故障で止める。ユーザーが C（block を外す）を選んだ。巡の上限の 3 巡目なので、限界の節の先頭に書く |
| H2 | 独立-3 | high | yes | inherited | multi-create | accepted | 1 回の Bash に PR 作成が 2 つ以上あると、2 本目以降の本文と作成先を検査しない（main と同じ）。ユーザーが C を選んだ。巡の上限の 3 巡目なので、限界の節の先頭に書く |
| H3 | 独立-3 | low | no | self-inflicted | bookkeeping | fixed | 依頼の原文で「C で進めて」が指す選択肢の文が引用されていない。assistant の文として引用を足した。commit: なし（review-log） |
| H4 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 実測の数値をどの commit の hook で取ったかが PR 本文に無い。PR 本文に測った commit を書く |
| I1 | 独立-4 | high | yes | self-inflicted | fd-strip | fixed | 引用符の外で `<`・`>` が続く 12 桁の数字（`--body 123456789012>out.txt`）を fd 番号として本文から消し、12 桁数字の検査が外れる。fd 番号の除去を 1 桁の数字だけにした（transcript の候補 89 件で解析結果の違い 0）。commit: c631743b |
| I2 | 独立-4 | high | yes | self-inflicted | parse-exception | accepted | lib を import できない・lib が例外を投げると pre-PR gate が検査せずに通す（merge gate は止める）。ユーザーが C（block を外す）を選んだので、限界の節の先頭に書く。lib の docstring の「壊れる」は「検査せずに通す」に直した（c631743b） |
| I3 | 独立-4 | high | yes | inherited | fd-strip | fixed | zsh は 1 桁だけを fd 番号に読むので、`gh pr merge 12>/tmp/log` の 12 を消すと merge gate が state.md の PR の承認で PR 旧#12 のマージを通す。I1 と同じ修正。commit: c631743b |
| I4 | 独立-4 | high | yes | self-inflicted | heredoc | accepted | 列挙: `_strip_heredoc_bodies` が heredoc の開始ごとに行全体を走査し直す（開始の数 × 行の長さ）。1 行に 1,000 個で約 9.8 秒、3,000 個で約 66 秒（hook の timeout 10 秒）。transcript 56,816 件で 1 行あたり最大 5 個（0.0 秒）。方針メモ-3 で (b)。限界の節の先頭に書く |
| I5 | 独立-4 | medium | no | self-inflicted | request-drift | fixed | 引用符の中の演算子だけの語を区切りにしない変化（止める側から通す側）が、ユーザーに示した変化の一覧に無い。区切りの判定を変更の前の語の集合に戻した。commit: c631743b |
| I6 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 変更断片と hook のコメントが、pre-PR gate に新しくかかる fd 番号の除去と、追加したテストの名前を書いていない。commit: c631743b |
| I7 | 独立-4 | low | no | self-inflicted | test-power | fixed | `_Helpers` が契約テストを継承し、unittest で実行すると約 70 本を二重に走らせる。継承をやめ、インスタンスを 1 つ作るだけにした。commit: 73cd7880 |
| I8 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 実測の件数が依頼の問いの件数と違い、数え方と時点が無い。PR 本文に書く |
| I9 | 独立-4 | advisory | no | inherited | doc-claim | accepted | 決定の記録（ADR など）が、pre-PR gate は独自の字句解析を持つと書いたまま。日付つきの記録なので直さない |
| R3 | 方針メモ-3 | - | - | - | - | - | なし |
| J1 | 独立-5 | high | yes | self-inflicted | fd-strip | fixed | fd 番号の除去を 1 桁にしたので、bash が fd 番号に読む `gh 12>/dev/null pr merge 7` を merge gate が merge と読まずに通し、`gh pr merge 12>/tmp/log` を PR 旧#12 と読む。merge gate は桁数を問わない規則に戻し、1 桁は pre-PR gate の本文の読みだけにした。commit: b1165899 |
| J2 | 独立-5 | high | yes | self-inflicted | request-drift | fixed | merge gate の読みを変える範囲が依頼（pre-PR gate の本文の数字）の外。J1 と同じ修正で merge gate の読みを戻した。commit: b1165899 |
| J3 | 独立-5 | medium | no | self-inflicted | doc-claim | fixed | 「2 桁以上は止める側」のコメント・本文に反例がある。コメントと変更断片を gate ごとの規則に直した。commit: b1165899 |
| J4 | 独立-5 | medium | no | self-inflicted | test-power | fixed | テストが bash で fail-open になる読み（pr_number 12）を固定している。merge gate は桁数を問わず消すことを固定するテストに替えた。commit: b1165899 |
| J5 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 変更断片が merge gate の読みの変化を書いていない。merge gate は変わらないと直した。commit: b1165899 |
| J6 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | `_strip_fd_prefixes` の docstring が規則を書いていない。commit: b1165899 |
| J7 | 独立-5 | low | no | self-inflicted | product | fixed | pre-push gate・worktree guard は桁数を問わず fd 番号に読み、gh_command_parse だけが 1 桁になった。merge gate を戻し、pre-PR gate の本文の読みだけの差であることを注記した。commit: b1165899 |
| J8 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界が「python3 が無いとき」だけで、lib を import できないときを書いていない。PR 本文の限界に書く |
| J9 | 独立-5 | high | yes | inherited | gh-subcommand | accepted | pre-PR gate は `pr` の直後の `create` しか見ないので、`gh 2>/dev/null pr create` と `gh pr -R o/r create` を PR 作成と読まない（merge gate の `_find_sub_command` は読む）。字句解析の外の既存の穴。方針メモ-3 の打ち切りに従い限界の節の先頭に書く |
| J10 | 独立-5 | high | yes | inherited | shell-c-operand | accepted | 列挙: merge gate の `_shell_c_operand` は `bash 2>/dev/null -c '…'` と `bash +e -c '…'` の本体を割らず、merge と読まない。字句解析の外の既存の穴。限界の節の先頭に書く |
| J11 | 独立-5 | advisory | no | self-inflicted | product | accepted | hook に残る判定（区切りの語の集合・global flag・入れ子の展開）と lib との差を、PR 本文の限界に書く |
| J12 | 独立-5 | advisory | no | self-inflicted | style | fixed | `_Helpers` が関係の無いテスト名で TestCase を作る。名前を `_helpers` にし、`run` で作るようにした。commit: e85d53be |
| K1 | 独立-6 | high | yes | self-inflicted | fd-strip | accepted | merge gate は桁数を問わず fd 番号を消すので、zsh の `gh pr merge 12>/tmp/x`（zsh は 12 を PR 番号として渡す）を引数省略形と読み、state.md の PR の承認で PR 旧#12 のマージを通す（origin/main と同じ読み）。1 桁にすると bash の `gh 12>/dev/null pr merge 7` が外れる。無効化後の差分巡の 2 回目なので、限界の節の先頭に書く |
| K2 | 独立-6 | high | yes | inherited | gh-subcommand | accepted | pre-PR gate は `gh` と `pr create` の間、`--body` と値の間のリダイレクトを読み飛ばさず、PR 作成と本文の検査が外れる（J9 と同じ穴の別の形）。限界の節の先頭に書く |
| K3 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | `SINGLE_DIGIT_FD_PREFIX_RE` の注記「本文の検査が過検出に倒れる」は当たらず、値を取る flag の直後では値を取り違える。follow_up_of のある PR なので直さない |
| K4 | 独立-6 | low | no | self-inflicted | test-power | accepted | 縮退経路で fd_prefix_re を渡すことを固定するテストが無い。直さない |
| K5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | module の docstring が、pre-PR gate が依存する `SINGLE_DIGIT_FD_PREFIX_RE` と `fd_prefix_re` 引数を挙げていない。直さない |
| K6 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 「pre-PR gate の本文の読みでは 1 桁だけ」は、実際には pre-PR gate の字句解析全体にかかる。直さない |
| K7 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | 実測を取った hook の sha が PR 本文に無い。PR 本文に書く |
| K8 | 独立-6 | advisory | no | self-inflicted | product | accepted | 共有の字句解析に gate ごとの fd 番号の規則（引数）を足した |
| K9 | 独立-6 | advisory | no | self-inflicted | style | accepted | 1,500 行を超えている gh_command_parse.py に正味 3 行を足した |
