---
lane: L1+
pr: 501
follow_up_of: 490
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | e06cfce5 | 0 | 0 | 0 | 2026-10-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ce75e882 | 2 | 0 | 2 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 96ded940 | 2 | 2 | 2 | 2026-10-14 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 96ded940 | 0 | 0 | 0 | 2026-10-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 30174394 | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ-1 | advisory | no | inherited | binding-reach | fixed | 旧#490 の「次の PR」4 項目の扱い。main の案は項目 2 を書く側（gdd_task_binding.py:128）で steering_path.parent.parent に倒す案。Opus は書く側の fallback に反対（不正形 4 件は 08-08〜08-28 で 9 月以降 0 件、倒すと実在しない worktree の binding が root で有効になる）で、読む側（_select_worktree_matches が _norm("") をプロセスの cwd に解決して一致させる）を、実際に一致すると確かめたときだけ直す案。確かめた結果、GDD を使う別の repo は worktree_path の無い旧書式の binding.json 4 件を git に commit していて、292 個の registry に複製され、resolve は旧書式の task への resolved 263・conflict 29。項目 3（太字の PR URL、1/420 件、block gate と共有の gdd_extract_doc_field）と項目 4（PR URL 欄なし 143/274、hook で書く案は gdd-pr-roots.sh:32-33 で否決済み）は直さず限界に書く。項目 1 は分母を数え直して別の PR で決める。ユーザーは「上＋別の repo の 4 件も消す」を選んだ（GDD を使う別の repo の 4 件の削除は別 repo の PR） commit: なし（方針） |
| I1-1 | 独立-1 | high | yes | inherited | fail-open | fixed | resolve_task の known_steering_paths（gdd_task_binding.py:304）が steering_path を _norm に通すので、数値・NUL を含む steering_path の binding が 1 件あると resolver 全体が落ち、done guard は conflict で、steering が 2 つ以上なら warn だけで通る。binding ごとの正規化を _safe_norm で例外に強くした commit: 4a6fb7ad |
| I1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | _absolute_worktree_path は絶対パスでも NUL・孤立サロゲート（realpath の lstat が ValueError）や、Python 3.12 以前の Path.exists の EACCES で例外になる値を通し、resolver 全体が落ちる。正規化と exists の例外を binding ごとに閉じた commit: 4a6fb7ad |
| I1-3 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 依頼の項目 2（worktree_path が実在しない、PR 1099）の書き側を限界にしたことを、ユーザーが確かめた記録が無い。ユーザーに確かめ、「限界として書く」を request.md に足した commit: なし（依頼の原文） |
| I1-4 | 独立-1 | low | no | self-inflicted | product | fixed | 依頼が述べた効果（GDD を使う別の repo の done guard が binding を決められる）を修正後の実データで確かめていない。320 worktree で旧・新の resolver を比べ、conflict→本物の binding に resolved が 22、旧書式に resolved→conflict が 264（どちらでも done guard は conflict）、conflict のまま 7 を PR 本文に書いた commit: なし（PR 本文） |
| I1-5 | 独立-1 | low | no | self-inflicted | test-power | accepted | テストの「相対（名前）: wtB」は cwd/wtB/wtB に解決され、修正前でも一致しないので型を固定していない（「空」「.」は固定している） |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片・PR 本文・テスト docstring の「warn だけで通していた」「done guard・detect-steering から一致」「相対の値が一致」は、steering 2 つ以上・branch を渡さない done guard・cwd に解決される相対値のときだけ成り立つ |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文が項目 4 の根拠に挙げた gdd-pr-roots.sh:32-33 は、台帳に PR URL を書く案の否決で、state.md に書く案ではない |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 実在しない相対パス・~ の binding で missing_worktree_path と stale_binding_missing_worktree が出なくなる変化が PR 本文・断片に無い |
| I1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | テストの module docstring の列挙に ~ 始まりが無い |
| I1-10 | 独立-1 | advisory | no | self-inflicted | style | fixed | is_absolute の後の expanduser().exists() の expanduser が効かない。正規化済みの値で exists を見る形にした commit: 4a6fb7ad |
| I1-11 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | L1+ 安全策 2 の 3 ケースとテストの対応が PR 本文に無い。判定できないとき（本物の binding が無く steering 2 つ以上）は修正の前後で warn のまま（W-9 AC-2 の設計） |
| I1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の件数に数えたコマンドが無い |
| I1-13 | 独立-1 | advisory | no | inherited | doc-claim | accepted | _stop_hook_test_base.py:370-374 の利用ファイルの列挙が古い（差分の前から） |
| I2-1 | 独立-2 | high | yes | inherited | fail-open | fixed | load_bindings（gdd_task_binding.py:160）が binding.json 1 件ごとに OSError・ValueError だけを捕る。深い入れ子の JSON は RecursionError で resolve_task 全体が落ち、done guard は conflict。merge gate の binding lookup は 1 件ずつ except Exception で飛ばしていて受理集合も食い違う。except Exception にした commit: 32a0e475 |
| I2-2 | 独立-2 | high | yes | inherited | fail-open | fixed | resolve の CLI の print が ensure_ascii=False で、一致しない binding の task_id・worktree_path の孤立サロゲートで strict な UTF-8 の stdout に出せず exit 1、detect-steering.sh・gate-ledger.sh が fallback に倒れる。ensure_ascii=True にした commit: 32a0e475 |
| I2-3 | 独立-2 | medium | no | self-inflicted | test-power | accepted | test_task_binding_resolve_security_contract.py:739 の、wrapper の広い except を固定するテストが、この PR で resolve_task が落ちなくなって空洞になった（docstring と :159-162 のコメントの仕組みの説明も古い） |
| I2-4 | 独立-2 | medium | no | self-inflicted | test-power | accepted | EACCES のテストは Python 3.13 以降では修正前でも通り、CI（3.14）では try/except を消しても検出できない |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | _safe_norm の docstring の「孤立サロゲートは UnicodeEncodeError」は、surrogateescape で通る \udc80〜\udcff には当たらない |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の _absolute_worktree_path の返り値と、exists の例外の扱いの説明が実装と違う commit: なし（PR 本文） |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の 292・263・29 と表の 320・264 が合わない。前の数は登録された registry の数で数え方が違うので、表の数だけにした commit: なし（PR 本文） |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary に、正規化できない binding を 1 件ずつ飛ばす変更が無い。断片に足した commit: 9995280b |
| I2-9 | 独立-2 | advisory | no | inherited | product | accepted | known_steering_paths は steering_path に絶対パスを求めない（影響は diagnostic_candidates と legacy_root_steering_ignored の警告だけで、hook・gate は読まない） |
| P2 | 方針メモ-2 | advisory | no | inherited | fail-open | fixed | 安全策 4 の発火（fail-open の high を含む巡が独立-1・独立-2 の 2 回）。実測: ディスク上の binding.json 1,343 件で、JSON の深さ最大 2、文字列でない path 欄 0、サロゲート・制御文字 0（異常は欄の欠落 297 件だけ）。書き手は I2-1・I2-2 の形を作れない。Opus の推奨は B（続行。2 件とも閉じ方: 構造の 1 行で閉じ、独立-3 を最後の巡にする。入力者 0 件で限界にする規定は閉じ方: 列挙の場面に限る。独立-3 で同じクラスタの high が出たら止めて限界に書く）。main の案も B。memory（この repo では安全策 4 の続行・停止を Opus に相談して決めてよい、2026-10-08 ユーザー決定）により内部で B に決めた commit: なし（方針） |
| I3-1 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | resolve の出力の escape は、出力を直接読む gdd-status・/gdd-dev resume・gdd-next-plan にも届き、日本語のパスや発言が \uXXXX で見えるのに開示が無い。断片と PR 本文に書いた commit: 370f1baf |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の「その 1 件だけを飛ばす」は読めない binding.json だけに当たり、正規化できない欄は空、Path.exists の例外は missing_worktree_path として扱う。断片を直した commit: 370f1baf |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「strict な UTF-8 の stdout」は hook の環境（kill-switch.sh の LC_ALL=C.UTF-8・PYTHONUTF8=1 で surrogateescape）と合わず、落ちるのは U+DC80〜U+DCFF 以外の孤立サロゲートだけ。断片と PR 本文は直した。gdd_task_binding.py とテストのコメントは、巡を無効にしないために直していない |
| I3-4 | 独立-3 | low | no | self-inflicted | product | fixed | 依頼の効果に対し、conflict のまま残る 7 件の理由が無い。実測（319 worktree）で、conflict のまま残るのは自分の binding が無いもの（項目 1）と、自分の binding が 5 件ある 1 worktree（複数一致）だった。PR 本文に書いた commit: なし（PR 本文） |
| I3-5 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の worktree 数と表の合計が合わない。registry の無い 27 worktree の行を足した commit: なし（PR 本文） |
| I3-6 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | テストのコメントの「invalid_bindings・candidates として出力に載る」の candidates は conflict の出力にしか無い |
| I3-7 | 独立-3 | advisory | no | inherited | fail-open | accepted | _frontmatter（gdd_task_binding.py:169-172）が local state を try なしで読み、Python 3.12 以前の EACCES で CLI 全体が落ちる。done guard は local_state_path を渡さず、fallback は同じ worktree の steering を数え直すので allow に届く経路は見つかっていない |
| I3-8 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | request.md の見出しの括弧書きに巡の ID と前の巡の指摘への言及がある。この PR で足した 2 行を「AskUserQuestion」だけにした（34 行目は前の PR の request.md の写しなので変えない） commit: 370f1baf |
