---
lane: L1
pr: 282
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5eb85cf2efd1dd031fb4258d7c1bfb26caf26b37 | 0 | 3 | 0 | 2026-10-02T11:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 81d101015ea7c01d7fa726f0f3d8d66e123b1893 | 0 | 0 | 0 | 2026-10-02T12:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 5d74497bf8b87d8e00c0deae9202fe4388a4d104 | 0 | 0 | 0 | 2026-10-02T13:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| R1 | 独立-1 | medium | no | self-inflicted | rule-sync | fixed | brainstorming の Gap Scan ⑤ が「HCQ 3 件未満」を未解決とし、新しい「方向性を除いて 2 個以内」と逆を向く。⑤ を新しい目安に揃えた commit: 81d10101 |
| R2 | 独立-1 | medium | no | self-inflicted | lint-scope | fixed | 規定と lint が、スコープの原文の完了条件（AC への写しの照合元）と Express Minimal Trace まで `AC-n 参照` に書き換えさせる。規定に例外を書き、lint はその節を見ない commit: 81d10101 |
| R3 | 独立-1 | medium | no | self-inflicted | rule-sync | fixed | 承認ポイントに AC の値を書くかどうかで、requirements-template・human-check-template・compact・断片が食い違う。requirements.md の中は `AC-n` を引き、HITL の一次表示は値に `AC-n` を添える、に分けた commit: 81d10101 |
| R4 | 独立-1 | low | no | self-inflicted | rule-sync | fixed | human-check-template の express と判断ポイントの件数が古い（1-3 件）。新しい目安に揃えた commit: 81d10101 |
| R5 | 独立-1 | low | no | self-inflicted | lint-scope | fixed | lint が Planned Follow-up Stage Lane を見て、テンプレートの例外と逆の指示を出す。その節を見ない commit: 81d10101 |
| R6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary・User Action Required が Lane の値も `AC-n 参照` にする節に入れている。例外を書いた commit: 81d10101 |
| R7 | 独立-1 | low | no | self-inflicted | test-power | fixed | AC と重なる語が 1 つ・行の語が 2 つの場合をテストが固定していない。テストを直した commit: faa7cd07 |
| R8 | 独立-1 | low | no | self-inflicted | test-power | fixed | AC の下の行の語を AC に数える仕様をテストが固定していない。テストを足した commit: faa7cd07 |
| R9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「token 予算は相殺した」が express の runtime profile に当てはまらない。実測値を PR 本文に書いた commit: なし（PR 本文） |
| R10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 限界に「AC 側の改名で、今の AC と共有する語が 1 つ以下になった古い列挙は出ない」が無い。PR 本文の限界に書いた commit: なし（PR 本文） |
| R11 | 独立-1 | low | no | self-inflicted | product | fixed | write のたびに WARN が上限なしで全件出る。先頭の 5 件と残りの件数だけにした commit: 81d10101 |
| R12 | 独立-1 | low | no | self-inflicted | style | fixed | express テンプレートの方向性の番号が「2.」固定で、判断を 2 件書くと重なる。「N.」にした commit: 81d10101 |
| R13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | guard の import block に `lib.advisory_lint` の import を足した。(g)(h)・security で fail-open の経路は無し。PR 本文に記録 |
| R14 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | hook 経由のテストが requirements.md の write と Advisory 2 の `continue` との順序を固定していない |
| R15 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | size deny 中に advisory lint を起動しないことを見るテストの probe に、新しい lint が入っていない |
| R16 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | hook 経由のテストが `CLAUDE_PLUGIN_ROOT` を環境から引き継ぐ |
| R17 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 「終了コードは常に 0」が言い過ぎ（例外は 1）。docstring と断片を直した commit: 81d10101 |
| R18 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PreToolUse のため最後の write が検査されないことがあり、WARN の行番号が write 前のもの。限界の文言と WARN の文を直した commit: 81d10101 |
| S1 | 独立-2 | medium | no | self-inflicted | lint-scope | next-pr | lint が express の `## Scope` を照合元として外しているが、express の Scope は `AC-1 参照` と書かせる欄で照合元ではない。`Scope` を除外から外し、テストと断片・PR 本文の並びを直す |
| S2 | 独立-2 | low | no | self-inflicted | lint-scope | next-pr | 節の除外が見出しの完全一致で、すぐ下の節にしか効かない（`###` の小見出し・見出しの揺れ・フェンス内の `#` 行）。Stop hook の Lane の読み方（次の `##` まで）とずれる |
| S3 | 独立-2 | low | no | self-inflicted | rule-sync | next-pr | human-check-template.md:101・:189 の「判断すること 1-3 件」が新しい目安（方向性を除き 2 件以内）と揃っていない |
| S4 | 独立-2 | low | no | self-inflicted | rule-sync | next-pr | express だけ方向性以外の承認ポイントに下限 1 件が付き、standard（0 件を許す）より厳しい |
| S5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「（write 前の内容）」の注記を lint 本体に固定しており、CLI 実行や write 対象でないファイルにも付く |
| S6 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 否定側のテスト 2 本が終了コードを見ていない |
| S7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「昇格必須」の語が、サイズの昇格と独立承認ポイントへの昇格のどちらかを書いていない |
| S8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片が、compact template に無い規定（requirements.md の承認ポイント・express の件数）を compact の変更としても書いている |
| S9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文のテンプレートの説明に照合元の例外が無い。PR 本文で直す |
| S10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の standard profile の値が上限ちょうど。tip で測り直した値を PR 本文に書く |

| T1 | 独立-3 | low | no | self-inflicted | ci-cause | fixed | CI の失敗の原因は待ち時間ではなく、CLAUDE_PLUGIN_ROOT の無い hook が cwd（リポジトリ直下）から lint を探したこと。リポジトリ直下から実行して再現した。環境変数の変更を取り消し、テストで CLAUDE_PLUGIN_ROOT を固定した commit: f490ff2f |
| T2 | 独立-3 | low | no | self-inflicted | product | fixed | `GDD_ADVISORY_LINT_TIMEOUT` に inf・巨大値を渡すと OverflowError が抜ける。変更ごと取り消した commit: 214391cd |
| T3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 「延ばせる」と書いたが短くもできる。変更ごと取り消した commit: 214391cd |
| T4 | 独立-3 | low | no | self-inflicted | product | fixed | hook の時間予算のコメント（lint 2 秒固定）と合わない。変更ごと取り消した commit: 214391cd |
| T5 | 独立-3 | low | no | self-inflicted | test-power | fixed | 既定値・読めない値のテストが例外を飲んだ場合と区別できない。テストごと取り消した commit: f490ff2f |
| T6 | 独立-3 | low | no | self-inflicted | test-power | fixed | 環境変数の効果を本番の呼び出し経路で確かめていない。テストごと取り消した commit: f490ff2f |
| T7 | 独立-3 | low | no | self-inflicted | test-power | fixed | テストが os.environ を書き換えたまま戻さない。テストごと取り消した commit: f490ff2f |
| T8 | 独立-3 | low | no | inherited | test-power | out-of-diff | case38b にも 2 秒の問題がある、という指摘。前提（待ち時間が原因）が誤りだったので該当なし |
| T9 | 独立-3 | low | no | inherited | product | next-pr | `_resolve_plugin_root()` は CLAUDE_PLUGIN_ROOT が未設定・空のとき docstring と違って cwd を返す（本番は wrapper が設定するので当たらない） |
| T10 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Validation が待ち時間のテストを挙げていない。変更ごと取り消した commit: 214391cd |
| T11 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | config-defaults.md に新しい環境変数が無い。変更ごと取り消した commit: 214391cd |
