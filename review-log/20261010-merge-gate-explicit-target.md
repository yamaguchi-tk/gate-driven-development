---
lane: L1+
pr: 425
follow_up_of: 422
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) | dd593aba | 0 | 0 | 0 | 2026-10-10 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 96f514cb | 2 | 4 | 2 | 2026-10-10 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 96f514cb | 0 | 0 | 0 | 2026-10-10 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 95f8bae9 | 1 | 1 | 1 | 2026-10-10 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | 95f8bae9 | 0 | 0 | 0 | 2026-10-10 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8c14a73d | 2 | 2 | 2 | 2026-10-10 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | 8c14a73d | 0 | 0 | 0 | 2026-10-10 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | b78e4e05 | 0 | 0 | 0 | 2026-10-10 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | low | no | inherited | design | fixed | 対象を repo つきで明示した merge では、cd 先を決められなくても pr-target-unresolvable で止めず、プロセス cwd の root の証跡で検査する案を推奨。条件は 2 つ: この経路で block を飛ばしたら、素通りの exit で GDD の PR 台帳を引き miss だけ通す（cd 先の別の GDD worktree の PR を証跡なしで通さない）。URL の owner/repo にも文字の許可リストを当て、`-R` の形では番号を必須にする。実測: 10-01〜10-10 の pr-target-unresolvable は一意の merge 14 件で、うち 10 件が URL か `-R` で明示した形。ユーザーへの確認は、内部相談で進めてよいというユーザーの発言（2026-10-08）に従い、内部相談で代えた。commit: なし（方針の記録） |
| F1 | 独立-1 | high | yes | inherited | approval-path | fixed | 列挙: 台帳の照合が、`$`・`*` を含む `-R`・URL の owner/repo を特定できた repo として扱い、miss で通す。方針メモ-1 で (a) とし、owner/repo が許可リストの形でなければ番号だけで照合する（`_mg_ledger_pair`）。正規表現の定義を、使う関数より前へ移した（`set -u` で落ちて通る形を防ぐ）。commit: cb949231 |
| F2 | 独立-1 | high | yes | inherited | approval-path | accepted | 列挙: `_has_env_repo_prefix` が最初の `gh` で走査を打ち切るので、後ろの `GH_HOST=`・`GH_REPO=` の代入（と `.envrc` の読み込み）で別 host の同じ owner/repo/番号の PR を merge しうる。方針メモ-1 で (b)。merge 1,430 件の transcript で 0 件。PR 本文の限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| F3 | 独立-1 | medium | no | self-inflicted | test-power | fixed | `test_merge_gate_cd_after_merge.py` の 2 本が URL の merge のままで、merge の後ろの cd の切り出しの退行を検出できない。番号の形に替え、`MERGE && cd /x` の `cd_intent` が False の単体テストを足した。commit: cb949231 |
| F4 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 許可リストの正規表現が判定を分ける場面（root に対象 PR が無く台帳が決める）と、台帳を読めないときのテストが無い。3 形と台帳を読めない形のテストを足した。commit: cb949231 |
| F5 | 独立-1 | medium | no | self-inflicted | test-power | fixed | for ループ側の明示の分岐を通るテストが無い。cd 先が別 repo に解決する形・payload の cwd が別の形・台帳に当たる形のテストを足した。commit: cb949231 |
| F6 | 独立-1 | medium | no | self-inflicted | product | fixed | 依頼から狭めた: root を決められない経路（`repo-root-unresolvable`、cd の意図で止まる）の明示した merge が範囲外のまま。方針メモ-1 は 0 件のため限界とする案だったが、ユーザーが「この PR で直す」を選んだ（`.request.md` に追記）。この経路でも明示した merge は台帳だけで決める。commit: f9a7fa09 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary が cd 先が解決した別 repo・payload の cwd の形を書かず、「ほかの GDD worktree の PR なら止める」は台帳に載っているときだけ。Affected Files にテストが無い。commit: fd37e91b |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 同じ規定を書いたほかの箇所（20261001・20261002 の断片、hook の注釈、gdd-pr-roots.sh、テストの docstring）が古い。既存の断片は書き換えず、新しい断片に成り立たなくなった記述を書いた。commit: 2781590b |
| M2 | 方針メモ-1 | low | no | inherited | design | fixed | F1・F2 の `閉じ方: 列挙` を相談。F1 は `$` 入りの repo の merge が transcript に 1 件あるので (a) 許可リストで閉じる。F2 は 0 件なので (b) accepted。F6 も 0 件なので分岐を足さず限界とする。commit: なし（方針の記録） |
| G1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | root 未解決の経路の明示した merge の分岐が、git に頼らない marker の検査を飛ばし、git が無い・rev-parse が失敗した GDD worktree の台帳に無い PR を証跡なしで通す。決められる実行先の祖先に marker があれば止める（`_mg_explicit_outside_gdd_merge`）。commit: 98df501e |
| G2 | 独立-2 | medium | no | self-inflicted | product | accepted | 許可リストの形でない `-R`・URL は、台帳を引く経路で台帳に無い番号でも unknown になり新しく止まる。PR 本文・断片に書いていない。`follow_up_of:` のある PR なので PR 本文の限界の節に書く |
| G3 | 独立-2 | low | no | self-inflicted | test-power | accepted | `test_unlisted_repo_with_a_pr_of_another_gdd_worktree_blocks` は (a‴) で止まり台帳の照合に届かない |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の第 2 段落が、20261002 の「今までどおり block」のうち明示した merge で止まらなくなった形（囲む構文・入れ子 shell・`&` など）を一部しか挙げていない |
| G5 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files に、注釈だけを変えたテスト 2 本が無い |
| G6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 台帳の読み手を「marker が無いので通す経路」と呼ぶ注記が、明示した merge の経路と合わない |
| G7 | 独立-2 | advisory | no | self-inflicted | style | accepted | テストの書き方の不揃い（`MERGE = MERGE_BY_NUMBER` のローカルの隠し、`setUp` の二重定義） |
| G8 | 独立-2 | advisory | no | self-inflicted | product | accepted | 14 件のうち明示した形でない 4 件の内訳が PR 本文に無く、番号だけの複合コマンドを限界にしたことをユーザーに確かめた記録が無い |
| M3 | 方針メモ-2 | low | no | inherited | design | fixed | 番号だけで cd がある merge の (a)(b) をこの PR で直す（ユーザーの選択。`.request.md` に追記）。Opus は、単一引用符の span と `$?` を除いた前処理後の文字列が `_CUTTABLE_CHARS` に収まるときだけ、cd 先の採否 (g) と merge の後ろの切り出しを救済する案を推奨（今の検査に OR で足す・`$?` は両方に足す・禁止語と merge の語も同じ文字列に当てる）。実測: 本番の pr-target-unresolvable 20 行のうち番号だけの 4 行で、旧#409 は cd 先が決まり、旧#294・旧#406 は切り出せる。旧#264 は今の解析器で cd 先が決まる（当時の hook で止まった理由は未測）。commit: 7bed4bdf |
| H1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 列挙: 単一引用符の救済を切り出しの `_CUT_BLOCKERS`・merge の語の数にも当てたので、引用符やコメントの中の偽の heredoc の開始語で後続の関数定義を隠す形や、引用符の中の 2 つ目の merge をパイプで bash に渡す形が、止まる側から通る側へ変わる。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ） |
| H2 | 独立-3 | medium | no | self-inflicted | product | fixed | 依頼から狭めた: (a) を、見かけだけ決められなかった形を決められるようにして扱い、本当に決められない番号だけの merge は止めたまま。線引きをユーザーに確かめていない。本番の 14 件で変更後に通る件数を測っていない。ユーザーが「Cで」と答え、案 A（番号だけの形は文字列を推測せず止める）に決まった。`.request.md` に追記。commit: なし（依頼の記録） |
| H3 | 独立-3 | medium | no | self-inflicted | product | fixed | 列挙: 救済は二重引用符の中と引用符の外の文字を許可リストで見るので、日本語の句読点・`#`・`*` を含む commit message があると効かない。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ） |
| H4 | 独立-3 | high | yes | self-inflicted | fail-open | accepted | 列挙: `cd /a && trap 'cd /b' DEBUG && gh pr merge 7`・`alias gh='cd /b && command gh'` で cd_target が /a になる（base でも同じ。差分は単一引用符の中に `$` を含む変種だけを広げた） |
| H5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | hook の注釈と test の docstring に、root 未解決の明示 merge の marker の検査が書かれていない |
| H6 | 独立-3 | low | no | self-inflicted | test-power | fixed | ledger の worktree へ cd するテストが block しか見ず、救済を戻しても通る。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ）。テストごと削除 |
| H7 | 独立-3 | low | no | self-inflicted | test-power | fixed | 閉じない引用符のテストは degraded で先に決まり、救済の None を見ていない。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ）。テストごと削除 |
| H8 | 独立-3 | low | no | self-inflicted | test-power | fixed | 新しいテストに「例外で guard 全体が落ちる」ケースが無い。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ）。テストごと削除 |
| H9 | 独立-3 | low | no | self-inflicted | product | fixed | 前処理（heredoc の除去など）を 2 回実行し、開始語の多い入力で時間が倍になる（未測）。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ） |
| H10 | 独立-3 | advisory | no | self-inflicted | style | fixed | `gh_command_parse.py` が 1,500 行の目安を超えたまま 30 行増えた。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ）。行数は base に戻った |
| H11 | 独立-3 | advisory | no | self-inflicted | test-power | fixed | `$?` の 2 つ目の形は、どちらの検査が効いたかを区別できない。commit: 3c40629a（救済を外した。ユーザーが案 C を選んだ）。テストごと削除 |
| M4 | 方針メモ-3 | low | no | inherited | design | accepted | 安全策 4 の発火（high を含む巡が 3 回、fail-open が 2 回）。Opus は「止める」を推奨（H1・H4 は列挙で 0 件のため (b)）。ユーザーは「再設計含めて広く対応を検討したい」を選び、(a) の線引きも「再設計含めて広く検討したい」とした。修正は止め、再設計の検討に移る |
| K1 | 独立-4 | low | no | self-inflicted | test-power | accepted | 削除したテストのうち、コメント・heredoc の本文の `$`・行継続の 3 形で cd_target が決まることを見る assert は、救済と関係なく main の挙動を守るもので、ほかに同じ assert が無い |
| K2 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が、merge の後ろの cd を切り出せない番号だけの形（旧#294・旧#406）も止まったままであることを書いていない。commit: なし（PR 本文） |
| K3 | 独立-4 | low | no | self-inflicted | product | accepted | `pr-target-unresolvable` の案内に、cd と同じコマンドに `$` を含めないことと、URL か `-R` での書き直しが先に書かれていない |
| K4 | 独立-4 | advisory | no | self-inflicted | product | accepted | git が壊れた環境で、決められない cd 先の marker は見ない（台帳に無い GDD の PR は証跡を見ずに通る限界の範囲） |
