---
lane: L1+
pr: 293
follow_up_of: 279
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（旧#279 の限界に書いた次の PR。main の草案は、語彙を足す・cd からマージまでの区切りで実行先を None にする・marker の無い経路で実行先を決められないときは miss だけ通す、の 3 つ。Opus は「修正して進める」を推した〔miss だけ通す形は transcript の 42 件を新たに止めるので、番号だけで台帳と照合する。`.`・`source`・`alias` はコマンド位置で判定する。区切りから `‖` を外す〕。草案と食い違ったので信号 ① で Fable を呼んだ。Fable は番号だけの照合を、marker の無い経路で実行先を決められない分岐に限って採るよう推し、背景化はコマンドの and-or リストの規則に置き換えるよう推した。main は今の台帳で番号だけの照合が当たる件数を測った〔実行先を決められない番号形 63 件中 0 件〕。1 PR 1 課題に従い、背景化〔共有部品 `_is_control_operator` の `&!` を含む〕は次の PR に分けた。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T11:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 46e087a940fc0efb9daadd9f0053bb7f3916eee2 | 4 | 1 | 4 | 2026-10-03T12:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 8b3bcb50914b70956e374e2e00ed96f69e33adf8 | 2 | 1 | 2 | 2026-10-03T13:10+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) + user（独立-1・独立-2 で fail-open の high が続き安全策 4 が発火。Fable は方針メモで使用済み。Opus は、読み込みの語の検査を外し `chdir` と番号だけの照合を残す案を推した〔過去のマージ 934 件で読み込みの語は 0 件。cd 先を捨てると退行、残すと穴で、今の signal では両方閉じない〕。ユーザーは「読み込みの語を外す」を選んだ） | - | 0 | 0 | 0 | 2026-10-03T13:40+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 7546278522f260501e3646d2fb86e2ebfa4e4c17 | 2 | 1 | 2 | 2026-10-03T14:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| B1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | token 列が改行を落とすので、改行の後の `source`・`.` と、`{`・`if`・`!`・`A=1` の後をコマンド位置と読まず、`git status` + 改行 + `source ./env.sh` + 改行 + マージを通す。`source`・`alias` はどこでも数え、`.` は前置きの語・代入を飛ばし、改行の後を元の文字列で見る commit: 28006eba。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| B2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | `cd /W && source ./env.sh && gh pr merge 7` で、読んだコードが cwd を変えうるのに `/W` を実行先に採る。別のコードを読む形では cd_target を採らない commit: 28006eba。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| B3 | 独立-1 | high | yes | inherited | fail-open | accepted | marker の無い経路で、番号も URL も無いマージ（branch 名・引数なし・`$pr`）は台帳と照合できず、実行先を決められない chdir の後でも通る。Opus の推奨で限界にした（照合のキーが無く、過去の 934 件で該当する 4 件はすべて正当なループで、止めると誤検知だけになる）。PR 本文の限界に書く |
| B4 | 独立-1 | high | yes | inherited | fail-open | accepted | pre-push gate（`push_command_parse.py` の `_find_cd_root`）と pre-PR gate が `cd` しか見ず、同じ言い換えで同じ穴がある。別の実装で判定の意味も違い、block gate 2 つの変更が 1 PR 1 課題を超えるので、Opus の推奨で次の PR に回す。PR 本文の限界と次の PR に書く |
| B5 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 断片の User Action Required が、GDD セッションで `source … && gh pr merge` が止まることと、git の外の cwd で `-R`・URL 形でも止まることを書いていない。断片に書き足した commit: 28006eba。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| B6 | 独立-1 | low | no | self-inflicted | product | fixed | block の文面が、`-R`・URL での明示と、読み込みを別のコマンドに分けることを案内しない。文面に足した commit: 28006eba |
| B7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `_has_chdir_intent` の docstring と hook のコメントの語の一覧が古い。一覧を直した commit: 28006eba |
| B8 | 独立-1 | low | no | self-inflicted | product | fixed | `_QuotedWord` の条件が常に真で意味が無い。条件を外し、`'source' x` のテストを足した commit: 28006eba。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| B9 | 独立-1 | low | no | self-inflicted | test-power | fixed | `builtin source`・`command .` の分岐のテストが無い。テストを足した commit: ffc19ed5。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| B10 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | リダイレクトのテストが既存のテストと重なる。PR 本文に書く |
| B11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実測（63 件中 0 件）に測り方が無い。PR 本文に測り方を書く |
| B12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の条件を「実行先の repo を決められない」と書くほうが正確。断片を直した commit: 28006eba |
| B13 | 独立-1 | advisory | no | self-inflicted | review-template | accepted | テンプレート外の記述（PR 本文の抜粋の、次の PR に分けた背景化の項目）。次の巡の抜粋から除く |
| C1 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | 読み込みの語で先頭の `cd` の行き先を捨てるので、marker の無い git の cwd から `cd <GDD の worktree> && source x && gh pr merge`（番号なし・台帳に無い番号）を打つと、worktree が候補に入らず gate が起動しないで通る。base では worktree の証跡を検査して止めていた。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| C2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | コマンド位置の `.` を列挙で判定するので、改行の後の `A=1 .`・リダイレクトが前に付く `.`・`case` のパターンの後・`time -p .`・`command -p .` を数え落とす。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| C3 | 独立-2 | medium | no | self-inflicted | test-power | fixed | `.` の前置きの語（`{`・`if`・`time`・`builtin` など）を消してもテストが落ちない。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| C4 | 独立-2 | low | no | self-inflicted | product | fixed | `repo-root-unresolvable` の文面が、読み込みの語で止まったときに効かない `-R`・URL を案内し、別のコマンドに分けることを案内しない。読み込みの語で止まる経路が無くなり、`-R`・URL の案内が効く形だけが残った commit: 75462785 |
| C5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の「引用符の中の `source` はならない」が、`'source' x` を数える実装・テストと合わない。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| C6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | hook のコメントの語の一覧と、cd_target を採らない理由の分類が実装と合わない。コメントの語の一覧を `chdir` だけに戻した commit: 75462785 |
| C7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | docstring の「止める側に倒す」が、marker の無い git の cwd の経路では逆になる（C1 と同じ根）。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| C8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に、git の外の cwd では `-R`・URL 形でも止まることが書かれていない。読み込みの語で止まる形が無くなり、抜粋に書く挙動が無くなった commit: なし（PR 本文） |
| C9 | 独立-2 | low | no | self-inflicted | product | fixed | `_strip_heredoc_bodies(command)` を 2 回計算している。読み込みの語の検査を撤回して部品ごと消えた commit: 75462785 |
| C10 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | `_extract_cd_target` が改行の後の `.` を見ず、本番の経路と答えが違う。PR 本文に書く |
| C11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実測がどの版のパーサで数えたか分からない。PR 本文に版と測り方を書く |
| K2 | 方針メモ-1 | - | - | - | - | - | なし |
| D1 | 独立-3 | high | yes | self-inflicted | approval-path | accepted | 読み込みの語（`source`・`.`・`alias`）の検査を外したので、GDD の worktree で `source ./x && gh pr merge 7` の `./x` が別 repo へ cd すると、worktree の承認の証跡で通る（main と同じ挙動）。方針メモ-1 でユーザーが外すことを選んだ。PR 本文の限界の先頭に書き、pre-push・pre-PR gate と合わせて次の PR で実行先の新しい signal として設計し直す |
| D2 | 独立-3 | high | yes | inherited | approval-path | accepted | marker の無い git の cwd から、実行先を決められない chdir（相対パスの cd・pushd・builtin cd）と番号なしのマージを組み合わせると、台帳の PR でも通る（B3 と同じ根）。巡の上限に達したので PR 本文の限界の先頭に書く |
| D3 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | 断片の User Action Required に、`chdir` とマージをつなぐと GDD セッションでは `pr-target-unresolvable`、git の外の cwd では `-R`・URL 形でも止まることが無い。PR 本文の限界に書く |
| D4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の「`chdir` を `cd` と同じく扱う」は広すぎる（`chdir` は `pushd` と同じく実行先を決められない側に回る）。PR 本文の限界に書く |
| D5 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | 断片の Validation 欄に、変わらない挙動（読み込みの語を見ない）を書いている。PR 本文の限界に書く |
| D6 | 独立-3 | low | no | self-inflicted | test-power | accepted | 新しい hook テストが reason を固定せず、改行の後の `.` の入力は位置引数 2 つの unresolvable の経路で止まる。PR 本文の限界に書く |
| D7 | 独立-3 | low | no | inherited | product | accepted | `repo-root-unresolvable` の文面に、`chdir` を別のコマンドに分ける案内が無い。PR 本文の限界に書く |
| D8 | 独立-3 | advisory | no | self-inflicted | review-template | accepted | テンプレート外の記述（起動時の git status に出る commit の件名の巡の ID）。判断には使っていない |
| D9 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「934 件中 0 件」の測り方が無い。PR 本文に測り方を書く |
