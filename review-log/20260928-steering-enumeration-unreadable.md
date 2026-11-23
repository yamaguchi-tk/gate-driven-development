---
lane: L1+
pr: 222
follow_up_of: 218
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。Opus の推奨はメインの案を補う向きで食い違わず、Fable は呼んでいない） | - | 1 | 1 | 1 | 2026-09-28T20:45+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2efa43012442075bc2ad099975858913de4fe740 | 1 | 0 | 1 | 2026-09-28T21:25+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 9b914698862c7c63dcf36a9697df798033c09ff3 | 1 | 0 | 1 | 2026-09-28T21:50+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4。F1 を I1 と同じクラスタと数えるか迷ったので、発火したものとして扱った。ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。Opus は A〔続行〕を推奨し、クラスタは別と判断した。回帰テストを関数単位ではなく入口の resolve_bind から通す形にする点だけ食い違い、メインはそれに合わせたので、Fable は呼んでいない） | 9b914698862c7c63dcf36a9697df798033c09ff3 | 0 | 0 | 0 | 2026-09-28T22:05+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | e55945b7d7d38ef60621e1181a2ff09caee9d8a6 | 0 | 0 | 0 | 2026-09-28T22:30+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus（main a32ed827 の取り込みで独立-3 が無効になった。字義どおりの base〔e55945b7〕は main の変更で 10,640 行になるので、取り込み後の merge-base a32ed827 からの 694 行で回した。旧#208 の独立-6/7 と同じ） | 33d37df449d2ce8eab2700ad3bd3cbce82feadc6 | 1 | 0 | 1 | 2026-09-28T23:20+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火。high を含む巡が合計 3 回〔独立-1・2・4〕。ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。メインの案 C〔新しい判定だけ cwd で見る〕と Opus の推奨は一致した。Opus は、C で閉じない既存の 2 経路〔payload の cwd と hook の cwd の食い違い、CDPATH〕を限界と次の PR に足すことと、次の巡の base を独立-4 の sha にすることを足し、メインは合わせたので、Fable は呼んでいない） | 33d37df449d2ce8eab2700ad3bd3cbce82feadc6 | 0 | 0 | 0 | 2026-09-28T23:40+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | e474cc7e2f10d1224bd240b7f8f3870d116555a3 | 3 | 0 | 3 | 2026-09-29T00:10+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の再発火〔high を含む巡が合計 4 回、クラスタ relative-project-root が 2 巡〕と、無効化後の差分巡 2 回の上限。ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。メインの案〔止める〕と Opus の推奨は一致し、Fable は呼んでいない。3 件は origin/main a32ed827 でも同じ入力で同じ結果になることを実測とコードで確かめ、決定 5〔直す次の PR を続けて出すならマージしてよい〕を当てた。巡の上限で修正はもう禁じられているので、止める選択の追加の効果は、以後の発火を抑えることだけ） | e474cc7e2f10d1224bd240b7f8f3870d116555a3 | 0 | 0 | 0 | 2026-09-29T00:25+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| O1 | 方針メモ | high | yes | inherited | unreadable-steering-scan | fixed | 草案は pre-push gate の none の分岐だけを止めていた。found（作業中が 1 件で trivial）でも、読めない steering が別にあると検査せずに通り、件数で block と素通りが反転する。resolver の直後で、結果によらず判定する |
| O2 | 方針メモ | medium | no | self-inflicted | path-kind-semantics | fixed | 草案は `_mg_ledger_node` の意味（symlink を辿る）を変えて lib へ移すとしていた。台帳のファイル・その親・root でも使うので、symlink の台帳が読めなくなる。意味は変えずに名前だけ中立にして移し、symlink の判定は steering の判定の中だけに置く |
| O3 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | pre-push gate は `set -euo pipefail` で動く。判定は `if` の条件で呼び、local は値つきで初期化する |
| O4 | 方針メモ | advisory | no | self-inflicted | test-matrix | fixed | テストに足す形: `.steering` が通常ファイル・一覧できない（0000・0311・0600）・symlink、state.md の無い task dir と README だけの `.steering`（通す側）、symlink の台帳（従来どおり hit） |
| O5 | 方針メモ | advisory | no | inherited | scan-limits | accepted | binding が symlink の task dir を指す形、pre-PR gate の found と読めない steering の組、LF を含む名前、task dir でないものを指す symlink の entry の誤 block（実データ 0 件）は、この PR では扱わない。PR 本文の限界の節に書く |
| I1 | 独立-1 | high | yes | inherited | hang-on-open | fixed | 経路: 差分の pre-push の判定 → 直前の resolver → binding の resolver（python）の `_legacy_root_candidates` の `read_text`。state.md が FIFO（symlink の先が FIFO を含む）だと開いて待ち、hook が timeout して通る。merge gate も同じ。resolver は通常ファイルでない state.md を開かず、pre-push は判定を resolver の前に移した（テスト f2349867、修正 9b914698） |
| I2 | 独立-1 | low | no | self-inflicted | test-power | fixed | symlink の台帳のテストが root 未解決の経路（hit でも unreadable でも止める）で見ていて、読める／読めないを判別しない。hit だけ止める git cwd の経路で見る（f2349867） |
| I3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Affected Files に変えたテストが無い。`.steering` 自体の symlink が User Action Required に無い。Summary の「読めない判定では読める」は merge gate だけの話（9b914698） |
| I4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `references/self-review-lanes.md` の pre-push の steering 解決の規定に `steering-unreadable` が無い（9b914698） |
| I5 | 独立-1 | low | no | self-inflicted | product | fixed | merge gate の `state-unreadable` の案内が symlink の直し方を示さない。pre-push の文は state.md の symlink に合わない（9b914698） |
| I6 | 独立-1 | low | no | self-inflicted | style | fixed | `_gdd_pp_steering_result` の説明コメントが `gdd_path_kind` の上に取り残された（9b914698） |
| I7 | 独立-1 | advisory | no | self-inflicted | ledger-scan-limits | accepted | 台帳の照合は symlink を辿って読むので、symlink を読めない側に数えても見つけるものは増えず、一致しないときに miss が unreadable になるだけ（root 未解決の経路で無関係な merge も止まる）。実データの symlink は 0 件。PR 本文の advisory に書く |
| J1 | 独立-2 | high | yes | self-inflicted | exception-outside-try | fixed | 足した `state_path.is_file()` が既存の `try/except OSError` の外にある。Python 3.12 では r はあるが x の無い task dir の下の state.md で PermissionError を投げ、resolver が例外で抜けて Stop hook の done guard が warn に下がる（手元の 3.12 で再現）。確認を try の中へ移した（テスト 30e60e0f、修正 e55945b7。修正後に 3.12 で [] を確認） |
| J2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `test_pre_push_tip_sha_resolution_contract.py` の docstring が「解決の直後」のまま（判定は解決の前に移った）。TROUBLESHOOTING と self-review-lanes.md の列挙に FIFO が無い。follow_up_of の PR の 2 巡目の low なので直さず、PR 本文の限界の節に書く |
| J3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界の「binding が `.steering` の外の FIFO を指すと待つ」は実装に無い経路（読む側は `-f` で確かめる）。残るのは binding.json 自体が FIFO の形。PR 本文の限界の記述を書き直した（commit なし） |
| J4 | 独立-2 | advisory | no | self-inflicted | style | accepted | テストの `HOOK_TIMEOUT = 10` が `test_merge_gate_ledger_fail_closed.py` と重複。PR 本文の advisory に書く |
| Q1 | 方針メモ-2 | advisory | no | inherited | exception-outside-try | accepted | 同じファイルの差分の外に同じ型がある: `_invalid_bindings` の `Path(worktree_path).exists()`（3.12 で権限エラーを投げる。Stop hook の経路）、`_frontmatter` の try の無い read、`load_bindings` の binding.json（FIFO なら待つ）。is_file と open の間の差し替え（TOCTOU）も残る。PR 本文の限界の節に書き、「開いたまま待つ」型の次の PR で扱う |
| K1 | 独立-3 | low | no | inherited | exception-outside-try | accepted | 同じ入力（`.steering/*/state.md`）を try の外の `is_file()` で判定する実装が 2 か所残る（`hooks/scripts/lib/pr_review_followup_polling.py:41` の `find_active_steering_state`、`hooks/scripts/gdd_stop_hook.py:149`・`:163` の `_bound_steering_file`）。Python 3.12 の権限エラーで poll 上限の引き上げ・markerless の一時停止が効かない。done guard の判定には届かない。follow_up_of の PR の 3 巡目の low なので直さず、PR 本文の限界の節に書く |
| K2 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋ファイル内の限界の節の「手元の 3.12 で行った」は実行結果の断定）。reviewer は根拠に採用していない。PR 本文では実行したコマンドと版を添えて書く |
| K3 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | 差し替えた `is_file` が呼ばれたことを確かめていないので、将来 legacy の走査が state.md を拾わなくなると空振りのまま緑になる。PR 本文の advisory に書く |
| L1 | 独立-4 | high | yes | inherited | relative-project-root | fixed | pre-push gate は `cd repo && git push`・`git -C repo push` で PROJECT_ROOT を相対パスのまま入れて cd するので、新しい判定が cd 先から `repo/.steering` を見て「無い」になり、読めない steering があっても none で通る（実測で再現。絶対パスなら止まる）。判定には cwd を渡した（テスト 4a946eab、修正 bafc4732） |
| L2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | `test_pre_push_tip_sha_resolution_contract.py` の docstring が「解決の直後」のまま（J2 と同じ）。follow_up_of の PR の low なので直さず、PR 本文の限界の節に書く |
| L3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | TROUBLESHOOTING・断片が「README など task dir でないファイルは止めない」と書くが、symlink のファイルは止める。原因の列挙に `.steering` が通常ファイル・state.md が FIFO の形が無い。follow_up_of の PR の low なので直さず、PR 本文の限界の節に書く |
| L4 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation が、merge gate の一覧できない task dir のテストも新しいファイルにあるように読める（既存の `test_merge_gate_ledger_fail_closed.py` にある）。PR 本文の advisory に書く |
| R1 | 方針メモ-3 | advisory | no | inherited | relative-project-root | accepted | C で閉じない既存の経路: payload の cwd と hook の cwd が違うとき、相対パスの root は step 5 で active と判定されず通る（`push_command_parse.resolve_candidate_roots` が payload の cwd に連結しない）。CDPATH を export していると `cd repo` が別の場所へ移る。相対パスの root の found・multiple は誤って止まる（fail-closed）。main でも同じ挙動。PR 本文の限界と次の PR に書く |
| M1 | 独立-5 | high | yes | inherited | relative-project-root | accepted | 相対 root（`cd repo && git push`・`git -C repo push`）では、resolver の union（`lib/self-review-evidence.sh` の `find "$_project_root/.steering"`）も cd 先から相対パスで探し、done・blocked の steering を見つけずに none で通る。main でも同じ（実測）。巡の上限のため直さず、PR 本文の限界の節の先頭に書く。次の PR で PROJECT_ROOT を cd 直後に絶対化する |
| M2 | 独立-5 | high | yes | inherited | cdpath | accepted | pre-push gate に `unset CDPATH` が無く、CDPATH があると相対 root の `cd` が stdout に絶対パスを印字し、block の JSON が壊れて効かない（新しい `steering-unreadable` の block も含む）。main でも同じ（実測）。巡の上限のため直さず、PR 本文の限界の節の先頭に書く。次の PR で merge gate と同じく冒頭で unset する |
| M3 | 独立-5 | high | yes | inherited | relative-project-root | accepted | `cd ~/repo`・`$HOME` の root が展開されず、step 5 で active と判定されずに通る（merge gate は repo-root-unresolvable で止める）。main でも同じ（実測）。巡の上限のため直さず、PR 本文の限界の節の先頭に書く。次の PR で step 5 で `~`・`$HOME` を展開する |
| M4 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（起動時の git status に出た commit の件名に巡の ID がある）。reviewer は判断に使っていない |
| S1 | 方針メモ-4 | - | - | - | - | - | なし |
