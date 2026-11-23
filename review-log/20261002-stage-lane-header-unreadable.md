---
lane: L1+
pr: 316
follow_up_of: 301
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#301 の限界に残した high 2 件。main は、表のヘッダーの判定をセルの数の照合で絞る案と、ヘッダーも未完にする案を並べた。Opus は後者をさらに進め、完了と読む行を空行と `- [x]` だけにするよう推した〔セルの数の照合は例外の行を細かくする案で、リストの印やコードスパンの中のパイプが次の入力として出る〕。読めない requirements.md は、合成テキストではなく読み込みと判定をまとめた関数で未完に倒すよう推した。main は Opus の案を採り、食い違いは残らず、Fable は呼んでいない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-02T17:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c84ceae616191c523a4079cff5674dc2cbb082c1 | 3 | 0 | 3 | 2026-10-02T17:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | ed8ecc280e9f77ad24f67a50e24ba3800fa0201c | 3 | 0 | 3 | 2026-10-02T22:40+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user（安全策 4 の発火〔クラスタ non-regular-file の high が独立-1・独立-2 の 2 巡〕。main は F1 を直し F3 も直す案だった。Opus は、F1 は足した越境の検査を外して base の挙動に戻し、F2・F3 は限界にする案を推した〔state.md を `is_file()` で読む読み手がほかに 6 か所あり、直すたびに隣の読み手が high になってきた〕。食い違いがあり信号 ①② で Fable を呼び、Fable も同じ案を推した。ユーザーは A を選んだ：F1 だけ直し、F2・F3 は限界にし、独立-3 を 1 回だけ回す。独立-3 で同じクラスタの high が出ても直さず限界にする。ただし F1 を外したことで生じた退行だけは直す） | - | 0 | 0 | 0 | 2026-10-02T23:15+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 1234f0bc826892da46d8e7f0baf2d4e3e395e196 | 1 | 0 | 1 | 2026-10-02T23:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし |
| Q1 | 独立-1 | high | yes | self-inflicted | non-regular-file | fixed | `requirements_lane_pending` が `is_file()` の確認を外したので、FIFO の requirements.md で読み込みが戻らず、post-merge の経路では hook が timeout まで止まる。非ブロッキングで開いて種類を確かめてから読む `read_regular_bytes` に替えた commit: 6e0e9bcb |
| Q2 | 独立-1 | high | yes | inherited | non-regular-file | fixed | done guard が `tasklist_path.is_file()` が偽なら検査対象なしとして通すので、ディレクトリ・FIFO・symlink のループ・権限のない tasklist.md で done が素通りする。無いパスだけを検査対象なしとし、ほかは done を止める commit: 6e0e9bcb |
| Q3 | 独立-1 | high | yes | inherited | non-regular-file | fixed | post-merge の marker が FIFO だと `_mentions_other_pr` と `_next_plan_block_payload` の読み込みが戻らない。marker を `read_regular_bytes` で 1 回だけ読み、読めないときは merge cue のある停止を止める commit: 6e0e9bcb |
| Q4 | 独立-1 | low | no | self-inflicted | test-gap | fixed | `file/requirements.md` のテストが `file` を作っておらず、NotADirectoryError の経路を通らない commit: 79e1aeca |
| Q5 | 独立-1 | low | no | inherited | doc-claim | fixed | `references/requirements-template.md` の Lane の節に、完了と読む形（`- [x]` と空行だけ）が書かれていない commit: f8ffc602 |
| Q6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `ClosedByDefaultTests` の docstring が、見出しと表のヘッダーを完了と読む古い規則のまま commit: 79e1aeca |
| Q7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `test_stop_hook_bind_resolution_contract.py` の docstring が改名前の関数名を書いている commit: 79e1aeca |
| Q8 | 独立-1 | low | no | inherited | doc-claim | fixed | `_require_next_plan_block` と `_next_plan_block_payload` の docstring が「内部エラーは fail-open」のままで、読めない requirements.md を未完にする挙動と食い違う commit: 6e0e9bcb |
| Q9 | 独立-1 | low | no | inherited | containment | accepted | requirements.md に symlink の越境の検査が無い。足した検査が Python 3.12 以前で例外を投げたので外し、読むだけの入力として受け入れる（方針メモ-2） |
| Q10 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 前の PR の断片（stage-lane-fence）が、表のヘッダーと区切りを完了と読むと書いていて、この PR の挙動と食い違う。未リリースの断片はリリースのときに直す |
| Q11 | 独立-1 | advisory | no | inherited | platform | accepted | `os.O_NONBLOCK` と FIFO の扱いは POSIX の前提で、Windows では確かめていない |
| Q12 | 独立-1 | advisory | no | self-inflicted | non-regular-file | accepted | 壊れた symlink（指す先が無い）は ENOENT になり、「無い」と扱う |
| R1 | 独立-2 | high | yes | self-inflicted | non-regular-file | fixed | `requirements_lane_pending` に足した `contained_file` が、Python 3.12 以前の symlink のループで RuntimeError を投げ、呼び出し元が握って done・post-merge の停止を通す。検査を外し、ループは `read_regular_bytes` の OSError で未完にする commit: 5d0bd789 |
| R2 | 独立-2 | high | yes | inherited | non-regular-file | accepted | post-merge の marker が symlink のループだと、`_post_merge_precheck` の `exists()` が先に弾き、読めない marker で止める分岐に届かない。marker は hook が通常のファイルとして書くので、限界として受け入れる（方針メモ-2）。断片からループの記述を外した |
| R3 | 独立-2 | high | yes | inherited | non-regular-file | accepted | done guard の Check 3 が state.md を `is_file()` で除外し、FIFO・ディレクトリ・ループで Route In Progress の検査を飛ばす。同じ state.md の読み手がほかにも残るので、限界として受け入れる（方針メモ-2） |
| R4 | 独立-2 | low | no | self-inflicted | product | accepted | tasklist.md を読めないときの回復ヒントが既定の「全タスクを完了し…」になり、`checked_path` を空で返すので bind できないときの案内も出ない |
| R5 | 独立-2 | low | no | self-inflicted | test-power | accepted | tasklist.md の非通常ファイルのテストの `assertIn("tasklist.md")` は、done guard のどの block でも真になる |
| R6 | 独立-2 | low | no | inherited | non-regular-file | accepted | `write_continuation` が FIFO の marker に書き込むと止まり、`_next_task_hint` も state.md を `exists()` と `read_text()` で読む |
| R7 | 独立-2 | low | no | inherited | non-regular-file | out-of-diff | `.claude/gdd-dev.local.md` が FIFO だと `parse_state` で hook が timeout まで止まる |
| R8 | 独立-2 | low | no | inherited | doc-claim | accepted | `skills/gdd-requirements-gating/SKILL.md` が Lane をチェックリスト形式に限っていて、テンプレートの表と食い違う |
| R9 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の「権限のないファイル」を「無い」として通していた、は不正確（mode 000 は base でも止まる） commit: 4fd9f022 |
| R10 | 独立-2 | advisory | no | self-inflicted | platform | accepted | `os.O_NONBLOCK` は Windows に無く AttributeError になる |
| R11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | `regular_file.py` の docstring の「壊れた symlink」「権限のないファイル」が不正確 |
| R12 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実データの比較の手順が再現できず、標本にヘッダーだけの表が無い |
| P2 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし |
| S1 | 独立-3 | high | yes | inherited | non-regular-file | accepted | post-merge の marker が symlink のループだと、`_post_merge_precheck` の `exists()` が「無い」と読み、読めない marker で止める分岐に届かない（R2 と同じ欠陥）。方針メモ-2 のユーザー決定（独立-3 で同じクラスタの high が出ても直さず限界にする）に従い受け入れ、断片の主節に例外を書いた |
| S2 | 独立-3 | low | no | inherited | doc-claim | accepted | `regular_file.py` の module docstring の列挙（壊れた symlink・権限のないファイル）が断片の列挙と合わない |
| S3 | 独立-3 | low | no | inherited | doc-claim | accepted | `test_stop_hook_non_regular_files.py` の module docstring が、marker の symlink のループも止めると書いている |
| S4 | 独立-3 | low | no | self-inflicted | containment | accepted | requirements.md が steering の外を指す symlink でも辿って読み、containment を掛ける tasklist.md と非対称（main と同じ挙動）。PR 本文の限界に書く |
| S5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の「symlink のループを『無い』として done を通していた」は Python 3.13 以降でだけ正しい commit: cda1aec8 |
| S6 | 独立-3 | advisory | no | self-inflicted | product | accepted | NUL・lone surrogate を含む marker の `tasklist_path` は `os.open` の ValueError が呼び出し元で握られ、「無い」側で終わる |
| S7 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 実データの比較で、PR 側をどの sha で測ったかが書かれていない |
| S8 | 独立-3 | advisory | no | inherited | product | out-of-diff | UserPromptSubmit hook は同じ marker を `-f` で確かめ、FIFO・ディレクトリ・ループでは post-merge の案内を出さない |
