---
lane: L1+
pr: 429
follow_up_of: 423
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 1d962a3c | 0 | 1 | 0 | 2026-10-10 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1822446c | 1 | 0 | 1 | 2026-10-10 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 1822446c | 0 | 0 | 0 | 2026-10-10 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 99bc165a | 0 | 0 | 0 | 2026-10-10 |
| 独立-3 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 09988b6b | 0 | 2 | 1 | 2026-10-12 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 357ea2b5 | 0 | 0 | 0 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | medium | no | inherited | wiring | fixed | 草案の「PROCESS_CWD の値だけを差し替える」形では、pre-PR の相対の本文ファイル（os.getcwd 基準）、nudge の相対の root、merge の相対の cd 先・payload cwd が root から解かれたまま残る。プロセスの cwd を cd で移し、pre-PR の python も chdir する形にした commit: aec5e6a2 |
| I1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: merge gate で最上位の cwd を trusted にしたため、desktop の worktree のセッションで、別の PR を記録した marker のある worktree から、台帳に載った別の worktree の PR を cd なしで `gh pr merge 7` すると、root checkout での台帳の照合を通らずに通る（差分前は block）。方針メモ-1 で (A) に決めた: trusted root の「対象 PR を記録していない」3 つの出口でも台帳を照合し hit なら止める（CLI の既存の穴も閉じる）。unresolvable で空にする前の番号を退避して照合する commit: 070a15cd |
| I1-2 | 独立-1 | low | no | self-inflicted | product | fixed | 依頼の行は gate が見た root を transcript で確かめることと、pre-push-optout.log の session-mismatch を兆候に挙げていたが、PR 本文はコマンドの件数と nudge のログしか示していなかった。session-mismatch の 10 月 148 行のうち 147 行が root checkout の hash であることを測り、断片と PR 本文に足した。pre-PR・merge gate は見た root をログに残さないので推定であることを限界に書く commit: a9f0cd40 |
| I1-3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 受け入れの条件のテストが、タブ（実在しないパスで試していた）・CR・実行権の条件を固定していなかった。実在するディレクトリで試し、拒否を値で assert し、中に入れないときはプロセスの cwd に戻ることを確かめる形にした commit: 2b2ef456 |
| I1-4 | 独立-1 | low | no | self-inflicted | test-power | fixed | pre-push の相対の --git-dir のテストが、相対の解決ではなく最上位の cwd の marker で block していた。`--git-dir=../other/.git` を最上位の cwd から解いたときだけ active を指す形にした。merge の相対 cd のテストは名前と docstring を trusted の候補の移動に合わせた commit: 2b2ef456 |
| I1-5 | 独立-1 | low | no | self-inflicted | test-power | fixed | pre-PR の python の os.chdir を消しても新しいテストが通っていた。active な steering の fixture で、相対の --body-file を最上位の cwd から読むテストを足した（chdir を消すと落ちることを確かめた） commit: 2b2ef456 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc | fixed | merge gate のコメント・断片の「相対の cd 先もセッションの cwd から解く」「プロセスの cwd と出所が同じ」、テストの docstring の受け入れの条件、pre-push gate の cd のコメントが実態と合わない。言い換え、pre-push gate は bash の cd を外して python の基準だけにした commit: a9f0cd40 |
| I1-7 | 独立-1 | advisory | no | inherited | doc | accepted | 最上位の cwd を読むほかの実装に stop-failure-record.py もある（isabs とタブ等を見ない）。PR 本文の限界の一覧に足す |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc | fixed | 限界の「新しく止めうる件数は測っていない」は、入力が記録に残っているので測れないとは言えない。測っていない理由を PR 本文に書く commit: なし（PR 本文） |
| M2 | 方針メモ-1 | - | - | - | - | - | なし |
| I2-1 | 独立-2 | low | no | self-inflicted | doc | accepted | test_gates_toplevel_cwd.py の module docstring が、pre-push gate もプロセスの cwd を移すと書き、受け入れの条件を 2 回食い違って書いている |
| I2-2 | 独立-2 | low | no | self-inflicted | doc | accepted | lib/hook_cwd.py の docstring が、pre-push gate もプロセスの cwd を移すと書いている（pre-push gate は相対の root の基準にするだけ） |
| I2-3 | 独立-2 | low | no | self-inflicted | doc | accepted | test_merge_gate_hook_non_gdd_merge.py の docstring が、台帳の読み手を 3 経路のまま書いている（gdd-pr-roots.sh は 4 経路に直した） |
| I2-4 | 独立-2 | low | no | self-inflicted | doc | accepted | run-merge-gate-hook.sh の _mg_ledger_verdict の見出しが「marker が無いので通す経路で」のまま。marker のある trusted root の出口からも呼ぶ |
| I2-5 | 独立-2 | low | no | self-inflicted | doc | accepted | 変更断片で、CLI のセッションで新しく止まることと打ち直し方を Summary にだけ書き、User Action Required は「なし」。番号を解決できない merge も読めた番号で照合することが断片に無い |
| I2-6 | 独立-2 | low | no | self-inflicted | doc | accepted | run-pre-push-gate-hook.sh のコメントの「lib は cd の後に呼ぶ」は不正確。gdd_session_continuity_ok と gdd_sr_log_event は cd の前に絶対パスの引数で呼ぶ |
| I2-7 | 独立-2 | low | no | self-inflicted | test-power | accepted | 列挙: test_merge_gate_toplevel_ledger.py の使えない最上位の cwd のテストは、R の経路と W1 の出口が同じ block を出すので、誤って W1 に移っても落ちない。相対の w1 も R から見て存在しない |
| I2-8 | 独立-2 | low | no | inherited | product | accepted | 出口の台帳の照合は unknown・unreadable を通すので、GH_REPO を付けた merge で避けられる。共通ディレクトリの分岐は止めるので非対称（差分前の desktop の経路と同じ扱い） |
| I2-9 | 独立-2 | low | no | self-inflicted | product | fixed | 依頼の「desktop の worktree のセッションで gate が見た root を確かめる」に対し、根拠の件数が desktop と CLI を分けず、pre-PR・merge gate を推定に替えていた。entrypoint で分け（worktree の cd なしのコマンド 1,013 件はすべて desktop）、pre-PR・merge gate は見た root が記録に残らないので測れないことを PR 本文に書いた commit: なし（PR 本文） |
| I2-10 | 独立-2 | advisory | no | self-inflicted | product | accepted | 台帳の照合を出口に広げたことで CLI のセッションでも新しく止まる。依頼の原文にこの広がりを確認した行は無い（方針メモ-1 で決めた） |
| I2-11 | 独立-2 | low | no | self-inflicted | product | accepted | 出口の新しい停止は repo-root-unresolvable の文面を使い、repo の中にいる利用者には合わない。台帳の root が別の clone のときは、断片が案内する cd でも pr-target-unresolvable で止まる |
| I2-12 | 独立-2 | advisory | no | inherited | test-power | out-of-diff | nudge・merge・pre-PR の入口の fallback テストの相対値は、プロセスの cwd から見て存在しないので、入口では isabs を固定していない（共有関数のテストが固定している） |
| I3-1 | 独立-3 | medium | yes | self-inflicted | fail-open | fixed | merge gate の trusted の候補を最上位の cwd に移したが、最上位の cwd だけが前の Bash の cd に追従するなら、CLI で marker の無い入れ子の repo へ cd した後に台帳に無い PR を証跡なしで通す。headless の claude で実測し、CLI ではプロセスの cwd も同じ値で一緒に動く（4 回とも一致）ことを確かめ、前提と実測をコメント・断片・PR 本文に書いた commit: 932aab2b |
| I3-2 | 独立-3 | medium | no | self-inflicted | product | fixed | 出口の台帳の照合は依頼に無い deny の分岐で、desktop でも新しく止まるのに件数もユーザーの確認も無い。台帳の PR を merge した transcript の記録 3 件を数え、新しく止まるのは 0 件。ユーザーが「残す」を選び、依頼の原文に足した。断片と PR 本文に desktop でも止まることを書いた commit: 932aab2b |
| I3-3 | 独立-3 | low | no | self-inflicted | product | fixed | 依頼の「PR 作成で gate が見た root を確かめる」を、確認なしに測れないとして限界にしていた。gh pr create 301 件がすべて desktop で、desktop の hook のプロセスの cwd が root checkout であることからの推論として目的の節に書いた commit: なし（PR 本文） |
| I3-4 | 独立-3 | low | no | self-inflicted | product | re-reported | 出口の hit の案内文が repo-root-unresolvable の汎用の文面で、場面に合わない（I2-11） |
| I3-5 | 独立-3 | low | no | self-inflicted | fail-open | accepted | merge gate の hook_cwd の emit が解析の後にあり、解析が想定外の例外で落ちると最上位の cwd へ移らない（今わかっている失敗では差分前と同じ） |
| I3-6 | 独立-3 | low | no | self-inflicted | doc | re-reported | hook_cwd.py とテストの docstring が、pre-push gate もプロセスの cwd を移すと書く（I2-1・I2-2） |
| I3-7 | 独立-3 | low | no | self-inflicted | doc | re-reported | 断片の User Action Required が「なし」で、打ち直しの形を Summary にだけ書く（I2-5） |
| I3-8 | 独立-3 | low | no | self-inflicted | doc | accepted | docs/SECURITY.md の Bash の PreToolUse の行が最上位の cwd を挙げず、merge gate のコメント 2 か所が trusted の候補を「hook プロセス cwd」のまま書く |
| I3-9 | 独立-3 | low | no | self-inflicted | test-power | accepted | nudge・merge・pre-PR の入口の相対値のテストは、プロセスの cwd から見て存在しないので入口で isabs を固定していない |
| I3-10 | 独立-3 | low | no | inherited | product | accepted | Stop hook・compact の提案・StopFailure の記録は、相対やタブを含む最上位の cwd を受けるので、gate と判定する root が割れうる |
| I3-11 | 独立-3 | advisory | no | self-inflicted | product | accepted | root branch guard は受け入れの条件を hook_cwd から import せず書き写している |
| I3-12 | 独立-3 | advisory | no | self-inflicted | doc | accepted | root checkout に漏れた marker・root checkout が記録した台帳に無い PR は、最上位の cwd へ移ると止まらなくなる。限界は marker のある worktree の形しか書いていない |
| I3-13 | 独立-3 | advisory | no | self-inflicted | doc | accepted | merge gate でも相対の tool_input の cwd を解く基準が最上位の cwd に変わるが、断片と PR 本文はほかの 3 つの hook についてだけ書く |
| I3-14 | 独立-3 | advisory | no | inherited | product | accepted | nudge の相対の cd 先で ROOT が相対の文字列のままキャッシュのキーになり、別の repo の同じ相対パス・branch と 300 秒共有しうる |
| I4-1 | 独立-4 | low | no | self-inflicted | doc | accepted | 断片の「desktop でも新しく止まる」が、変更前に止まっていたものを戻す分（CLI で作った PR）と、更新後の pre-PR gate で作った PR だけが新しく止まる分を分けず、更新前に desktop で作った PR は止まらないことを書いていない |
| I4-2 | 独立-4 | low | no | self-inflicted | test-power | accepted | test_merge_gate_toplevel_ledger.py の CLI の runner は最上位の cwd の無い payload で、実際の CLI の形（最上位の cwd = プロセスの cwd）が出口の照合まで届くテストが無い |
| I4-3 | 独立-4 | low | no | self-inflicted | doc | accepted | コメントと断片が「最上位の cwd は cd に追従する」「CLI では一緒に動く」を、desktop と対話の CLI を測らずに断定している（headless の CLI だけで実測） |
