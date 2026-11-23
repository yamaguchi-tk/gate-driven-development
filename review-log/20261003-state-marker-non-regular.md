---
lane: L1+
pr: 326
follow_up_of: 316
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user（旧#316 で受け入れた常時 High 2 件〔marker の symlink のループ、done guard の state.md〕を、ユーザーの指示で直す。main は 2 件を直し、隣の読み手は判定に届くものだけ揃える案だった。Opus は、block / allow に届く読み手〔`gdd-dev.local.md` の FIFO、bind が無いときの state.md の選び方、ポーリング上限〕まで揃える案 B を推した。表示・提案・書き込みの読み手は限界にする。`gdd-dev.local.md` は shell 側の `[[ -f ]]` と揃えて止めずに記録して通す。改行をそろえる `read_regular_text` を足す。食い違いは無く、Fable は呼んでいない。ユーザーは B1〔ポーリング上限で state.md を読めなければ blocked〕を選んだ） | - | 0 | 0 | 0 | 2026-10-03T00:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1f6b58f97144ea8813ddcd83b666ed5b90e8e3fc | 1 | 1 | 1 | 2026-10-03T00:45+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 8073b35bc9728bce587abeaa3fb57d4aac701d3f | 0 | 1 | 0 | 2026-10-03T01:23+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 53a73d89168e41a90b2bd9c4fa79ab717f18e6ea | 1 | 0 | 1 | 2026-10-03T17:35+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | f313f4ccab12b3794dcd6fc0ff448160d5fb852d | 2 | 0 | 2 | 2026-10-03T18:20+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user（安全策 4 の発火〔クラスタ unstatable の high が独立-3・独立-4 の 2 巡、high・blocking を含む巡が合計 3 回〕。main は止める案だった。Opus も止めるを推し、根拠は「事故から守る」ではなく「実データ 0/166 件で入力が開いている・差分（無効化後）の巡を使い切った」に置くべきとした。信号 ② で Fable を呼び、Fable も止めるを推し、D2 だけ直す案は架空のパスを理由に示すなど新しい指摘を生むと指摘した。ユーザーは止めるを選んだ：D1 を限界の節の先頭に直していない常時 High・実害クラスとして書き、D2 は安全側として限界に書く） | - | 0 | 0 | 0 | 2026-10-03T18:33+09:00 |
| 独立-5 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 0878c6b7fa1d5092cda43e4f8692e09ac6b241ff | 1 | 1 | 1 | 2026-10-03T19:13+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし |
| A1 | 独立-1 | high | yes | self-inflicted | platform | fixed | `read_regular_bytes` が `os.O_NONBLOCK` を直に参照し、Windows では AttributeError になる。`parse_state` が読むようになったので、例外が握られて stop hook の判定が丸ごと通る。無い環境ではフラグなしで開く commit: 7fc8d559 |
| A2 | 独立-1 | medium | no | inherited | non-regular-file | fixed | 指す先の無い symlink は ENOENT になり、tasklist.md・state.md・marker などを「無い」と読む。パスにも symlink にも何も無いときだけ None にする commit: 7fc8d559 |
| A3 | 独立-1 | low | no | self-inflicted | non-regular-file | fixed | ポーリング上限が bind を見ずに最新の steering の state.md を読み、無関係な新しい steering で blocked になる。resume-from と同じ `_steering_candidate` で選ぶ commit: 7fc8d559 |
| A4 | 独立-1 | low | no | inherited | non-regular-file | fixed | 最新の steering のディレクトリ自体が使えない（steering の外を指す symlink・ループ）と、古い steering へ飛ぶ commit: 7fc8d559 |
| A5 | 独立-1 | low | no | self-inflicted | observability | fixed | ポーリング上限で state.md を読めず blocked にしたときに記録が無く、`references/state-field-tiers.md` の行にも書かれていない commit: 7fc8d559 |
| A6 | 独立-1 | low | no | self-inflicted | product | fixed | state.md を読めないときの done の block が、パスを示さず、回復手順が既定の「全タスクを完了し…」になる commit: 7fc8d559 |
| A7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の記述（進捗表示・handoff の挙動）が実際と合わない commit: なし（PR 本文） |
| A8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Summary の記述が実際の挙動と合わない commit: 7fc8d559 |
| A9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `test_stop_hook_non_regular_files.py` の module docstring が、state.md・`gdd-dev.local.md` と記録して通す扱いを書いていない commit: 3f4f4f90 |
| A10 | 独立-1 | low | no | self-inflicted | test-gap | fixed | 最新の steering が steering の外を指す symlink のときのテストが無い commit: 3f4f4f90 |
| A11 | 独立-1 | low | no | self-inflicted | test-gap | fixed | ポーリング上限で最新の state.md が指す先の無い symlink のときのテストが無い commit: 3f4f4f90 |
| A12 | 独立-1 | low | no | self-inflicted | test-gap | fixed | ポーリング上限の FIFO のテストが同じプロセスで読み、止まるとテストごと戻らない commit: 3f4f4f90 |
| A13 | 独立-1 | advisory | no | inherited | containment | accepted | done guard の Check 3 は state.md に containment を掛けない |
| A14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文に実データの計測コマンドが無い |
| B1 | 独立-2 | medium | no | self-inflicted | product | fixed | 停止理由に関係なく `_steering_candidate` を先に評価するので、`.steering` を一覧できないと external-review-waiting 以外の停止でも hook が例外で落ち、pause が 1 回だけ強制継続になる。ユーザーの指示で直した commit: 4673a2fb |
| B2 | 独立-2 | low | no | self-inflicted | test-power | accepted | state.md の block のパスを見る assert（`20260620-task`）は、tasklist の検査対象の行でも満たされる |
| B3 | 独立-2 | low | no | self-inflicted | test-power | accepted | ポーリング上限を bind 済み steering で判定する経路のテストが無い |
| B4 | 独立-2 | low | no | inherited | product | accepted | 最新の task dir に x 権限が無いと `os.path.lexists` が偽になり、古い steering へ飛ぶ |
| B5 | 独立-2 | low | no | self-inflicted | platform | accepted | Windows では `O_BINARY` を付けずに開くので text mode で読む（未確認） |
| B6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片の「Windows で判定が丸ごと通っていた」は main の挙動と合わない |
| B7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 回復手順が原因を通常のファイルでない場合に断定し、権限エラーのときに合わない |
| B8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `references/state-field-tiers.md` の条件が、steering の外を指す state.md も blocked にするコードより狭い |
| B9 | 独立-2 | advisory | no | inherited | doc-claim | accepted | `gdd-pr-review-followup` の skill の「超えたら」がコードの「達したら」と 1 回ずれる |
| B10 | 独立-2 | advisory | no | self-inflicted | product | accepted | bind が無いと、steering でない symlink が最新の名前にあるだけで resume-from が読めず、external-review-waiting が毎回 blocked になる |
| B11 | 独立-2 | advisory | no | inherited | containment | accepted | Check 3 だけが steering の外を指す state.md を読む |
| B12 | 独立-2 | advisory | no | inherited | doc-claim | accepted | `_guard_tasklist` の docstring が実装（ちょうど 1 件の規則）と違う |
| C1 | 独立-3 | high | yes | self-inflicted | unstatable | fixed | `_steering_candidate` が `os.path.lexists`・`Path.is_dir()` で権限エラーも「無い」と読み、最新の task dir や `.steering` に x が無いと古い steering へ飛ぶ（ポーリング上限が古いタスクの回数で pause のまま、resume-from が古いタスクの `human-check-waiting` で停止を許す）。ENOENT・ENOTDIR だけを「無い」とし、ほかは使えないとする commit: 5fb4a0a5 |
| C2 | 独立-3 | low | no | self-inflicted | test-power | fixed | `.steering` を一覧できないときのテストが root では誤って落ち、検出力も無くなるのに skip が無い commit: 71c81241 |
| C3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | `references/state-field-tiers.md` の blocked の条件が、`.steering` を一覧できない・steering の外を指すときを含まない |
| C4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片の「ほかの停止理由は pause・終了する」が done（block）まで含めて読める |
| C5 | 独立-3 | low | no | inherited | doc-claim | next-pr | `skills/gdd-pr-review-followup/SKILL.md` の「上限を超えたら blocked」が、コードの「達したら」と 1 回ずれる |
| D1 | 独立-4 | high | yes | inherited | unstatable | accepted | done guard の tasklist の選び方（`resolve_guard_tasklist`）が `.steering` を `Path.is_dir()` で読み、権限で stat できない `.steering` を「無い」と扱って done を通す（bind 済みは Python 3.13 以降、bind が無いときは全版）。方針メモ-2 で止めるを選び、限界として受け入れた |
| D2 | 独立-4 | high | yes | inherited | unstatable | accepted | `_steering_candidate` が、`.steering` が在るのにディレクトリとして使えない（指す先の無い symlink・ループ・通常のファイル）と「無い」を返し、ポーリング上限を判定しない。方針メモ-2 で止めるを選び、限界として受け入れた |
| D3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Summary が、`.steering` に x が無いときの旧挙動を誤って書き、bind 済みの task dir の変化を書いていない |
| D4 | 独立-4 | low | no | self-inflicted | product | accepted | 権限で stat できないだけの state.md でも、hook-errors.log の理由が「通常のファイルでない」になる |
| D5 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | `Path.is_dir()` が EACCES を False にするのは Python 3.13 以降で、docstring の記述が 3.12 以前では成り立たない |
| D6 | 独立-4 | advisory | no | self-inflicted | test-power | accepted | import の時点で評価される `os.geteuid()` のため、Windows ではテストのモジュールごと読み込めない |
| D7 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | `_steering_candidate` の docstring に「stat できなければ使えない」が無い |
| P2 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし |
| E1 | 独立-5 | high | yes | inherited | unstatable | accepted | `.steering` 自体が在るのにディレクトリとして使えないと「無い」と読み、ポーリング上限を判定しない（D2 と同じ欠陥）。方針メモ-2 で止めるを選んだので直さず限界に書く |
| E2 | 独立-5 | medium | no | inherited | containment | accepted | done guard の Check 3 が steering の外を指す state.md を containment なしで読む（A13・B11 と同じ） |
| E3 | 独立-5 | low | no | self-inflicted | product | accepted | ファイルを指す symlink の entry を、使えない最新の steering と読む |
| E4 | 独立-5 | low | no | inherited | containment | accepted | bind が無いとき state.md の containment の基点が `.steering` なので、古い steering の state.md への symlink を使える |
| E5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 回復手順が読めない原因を 4 種類に言い切る（B7 と同じ） |
| E6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 変更断片が、ポーリング上限の判定を stop hook から「移した」と書く（main で先に lib に移っていた） |
| E7 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 変更断片が、`.steering` に x が無いときの旧挙動を取り違えている（D3 と同じ） |
| E8 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 変更断片が、Windows の旧挙動を「判定が丸ごと通っていた」と書く（B6 と同じ） |
| E9 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | merge の宣言と押し返しの記録が指す先の無い symlink のときに、押し返さなくなる変化を断片と PR 本文に書いていない |
| E10 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | marker と local state の存在の確認は `os.path.lexists` で、権限で辿れない `.claude` を「無い」と読む（shell 側の `-f` と同じ） |
| E11 | 独立-5 | advisory | no | inherited | doc-claim | accepted | `_guard_tasklist` の docstring が実装（ちょうど 1 件の規則）と違う（B12 と同じ） |
| E12 | 独立-5 | advisory | no | inherited | product | accepted | shell 側の `gdd_detect_active_steering` は通常のファイルでない state.md を飛ばし、stop hook と選ぶ steering が食い違いうる |
| E13 | 独立-5 | advisory | no | self-inflicted | platform | accepted | Windows では `O_BINARY` を付けないので text mode で開く（B5 と同じ） |
| E14 | 独立-5 | advisory | no | inherited | product | accepted | 最新の steering に state.md が無いときは、古い steering へ飛ぶまま |
| E15 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | `references/state-field-tiers.md` の blocked の条件が一部だけ（C3 と同じ） |
