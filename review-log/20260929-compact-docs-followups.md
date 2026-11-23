---
lane: L1+
pr: 232
follow_up_of: 208
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 207f9217058e0666cf998222c479234d8209c67e | 2 | 1 | 2 | 2026-09-29T00:06+09:00 |
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) | 207f9217058e0666cf998222c479234d8209c67e | 0 | 0 | 0 | 2026-09-29T00:22+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | e30b3d69007355b69d9ae5f376420a18d04bf898 | 1 | 0 | 1 | 2026-09-29T00:58+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) | e30b3d69007355b69d9ae5f376420a18d04bf898 | 0 | 0 | 0 | 2026-09-29T01:14+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | bc1c786ff593987f3f27d1e02019419d8671cff2 | 1 | 0 | 1 | 2026-09-29T01:43+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus) | bc1c786ff593987f3f27d1e02019419d8671cff2 | 0 | 0 | 0 | 2026-09-29T02:03+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | d3e13c9f1cbba73225898df6f1370d81cd5621b9 | 2 | 0 | 2 | 2026-09-29T02:33+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus) | d3e13c9f1cbba73225898df6f1370d81cd5621b9 | 0 | 0 | 0 | 2026-09-29T02:55+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | d0459f901ed23081cb4e26d46f76115e74ee7d7e | 4 | 0 | 4 | 2026-09-29T03:36+09:00 |
| 方針メモ-5 | Opus 設計レビュー (general-purpose, model: opus) | d0459f901ed23081cb4e26d46f76115e74ee7d7e | 0 | 0 | 0 | 2026-09-29T04:10+09:00 |
| 独立-6 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 1680e52482ad570fe06a6acfd06bcd41d713faec | 2 | 1 | 2 | 2026-09-29T04:34+09:00 |
| 独立-7 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 84ccfaf573af0ca6f6d0509704e971a270f1c001 | 1 | 1 | 1 | 2026-09-29T08:42+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | yes | inherited | cancelled-terminal-set | fixed | binding の経路の終端判定が `Resume From` だけを見て、中止の規定が書く `Next Action: cancelled` だけの steering を作業中として返す。pre-push が中止した steering の Task Size・証跡で作業中の steering の push を検査していた。binding の経路でも `Next Action` の cancelled を終端にした。commit: a293787d |
| I1-2 | 独立-1 | high | yes | inherited | cancelled-terminal-set | fixed | steering write guard の peer turn の境界が `Next Action: cancelled` だけを見て、`Resume From: cancelled` の書き込みを通していた。検出はこれだけで中止とみなす。パターンと field の両方に足した。commit: f9b9e333 |
| I1-3 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 足した discard のテストが skill の文書の語だけを assert していた（repo の CLAUDE.md § テストが書かないと定める形）。skill の行から値を取り出し、binding 先の終端の判定を pre-push の入口から見る形にした。commit: ea58d155 |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片とテストの docstring が挙げる、以前の discard が候補に残る経路が実装と合わなかった（残るのは binding の経路だけ）。断片を書き直した。commit: 1dd43ae6 |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PreCompact・UserPromptSubmit が local state が無いときに照合せずに渡すことが説明から抜けていた（SessionStart はこのとき入れない）。phase-gate-prechecks.md と README に足した。commit: 1dd43ae6 |
| I1-6 | 独立-1 | advisory | no | inherited | doc-claim | accepted | Exit Decision の discard は AI の判断だけでも発火し、両 field の cancelled で完全な中止になる。`abandon-and-pause.md` の「cancel はユーザーの明示なしに実行しない」と食い違う（以前も `Next Action: cancelled` を書いていた） |
| I1-7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | gdd-brainstorming の本文を変えたので、PR 本文に 1b・1c の証跡を書く |
| P1 | 方針メモ | medium | no | inherited | cancelled-terminal-set | next-pr | binding の経路は `Next Action: done` を終端にしない（`gdd-pr-review-followup` の external-review-waiting の間の暫定値）。`state-machine.md` の terminal の定義（どちらの field の done でも終端）・fallback・resolver と食い違う。done を足すと followup 中の steering が none になるので、この PR では cancelled だけにした（Opus の推奨。実データ: Next Action=done で Resume From が非終端のもの約 19 件、cancelled 側は 0 件） |
| I2-1 | 独立-2 | high | yes | self-inflicted | cancelled-terminal-set | fixed | binding 先が `Next Action: cancelled` だけで対象 PR を記録していると、終端になって候補 0 件の `none/terminal-only` に落ち、merge gate が承認の証跡を見ずに merge を通す（差分の前は approval-missing）。同じ素通りは `Resume From: cancelled`・binding なしの中止の steering で差分の前からあった。merge gate の候補 0 件の分岐で対象 PR を照合し、PR を記録した steering がある checkout で対象を省いた merge は止めた。commit: c32701e7 |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | phase-gate-prechecks.md の「local state が無いときは入れない」が、session id が取れない runtime では実装と逆（SessionStart は入れる）。follow_up_of の PR の 2 巡目の low なので限界として PR 本文に書く |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | peer turn の正規表現が 4 本になったが、同じリストを読む関数の docstring が「3 パターン」のまま（決定の種類としては 3）。限界として PR 本文に書く |
| I2-4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「対象のファイルは state.md」が、追加の形の層（steering 配下のどのファイルでも deny）より狭い。PR 本文を直す |
| I2-5 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり（commit の件名に巡の名前）。判断には使われていない |
| P2 | 方針メモ-2 | advisory | no | inherited | cancelled-terminal-set | accepted | 安全策 4 の発火（同じクラスタの high が 2 巡）。Opus の推奨（A+: merge gate の候補 0 件の分岐で対象 PR を照合し、対象を決められない merge は PR を記録した steering があれば止める）を採用。メインの案（A: 対象 PR があるときだけ照合）では引数なし・ブランチ名の merge が素通りのまま残ることを Opus が複製で実測した。新しく止まる入力の実データは 0 件。pre-PR gate は binding 先が中止のとき done の steering で判定する（`self-review-lanes.md` の規定どおり）ので限界に書く |
| I3-1 | 独立-3 | high | yes | inherited | pr-url-target-match | accepted | merge gate の対象 PR の照合が、URL の形では文字列全体の一致だけを見て、正準形でない PR URL（`<…>`・`縦棒 注記`・リンクの形）を記録した steering と照合できず、承認の証跡を見ずに通していた（番号の形は止まる）。found・multiple の経路は差分の前から、候補 0 件の経路はこの PR で同じ照合を通るようになった。URL の形も番号と owner/repo で比べる共通の判定にした。URL の形の照合を撤回したので未修正に戻った。main から残る欠陥として、gh の flag の文法と合わせて次の PR で直す |
| I3-2 | 独立-3 | low | no | self-inflicted | test-power | accepted | 候補 0 件の分岐の、通す側（PR を記録した steering が無い checkout の引数なしの merge）と many 側（同じ PR を記録した中止の steering 2 件）のテストが無い。読めない state.md のテストは新しい分岐を通らない。限界として PR 本文に書く |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片と self-review-lanes.md の「終端の steering だけが残るときも、対象 PR を省いた merge は止める」が、done・blocked の steering が残る checkout（union が found を返す）にも広げて読める。限界として PR 本文に書く |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が「なし」のまま（中止の steering の PR の merge と、対象 PR を省いた merge が新しく止まる）。限界として PR 本文に書く |
| I3-5 | 独立-3 | low | no | self-inflicted | product | accepted | 候補 0 件の分岐の `steering-ambiguous` の案内文（対象 PR の明示・完了済み steering の整理）が、中止の steering だけの checkout と many の状況に合わない。限界として PR 本文に書く |
| I3-6 | 独立-3 | low | no | self-inflicted | product | accepted | 対象 PR が無い merge でも、PR を記録した steering の有無を見るため全 state.md を開くようになった（multiple の経路の引数なしの merge を含む）。hook の timeout に件数で近づく既知の限界に寄る。限界として PR 本文に書く |
| I3-7 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 `20260928-pre-push-tip-prefix-match.md` の「作業中が無ければ今どおり通る」が、中止の steering が PR を記録していると古くなる。リリースの dry-run で直す |
| P3 | 方針メモ-3 | advisory | no | inherited | pr-url-target-match | accepted | 安全策 4 の再発火（high を含む巡が 3 回）。Opus は A（この PR で閉じる）を推奨し、複製で 3 経路 × 正準形でない 5 種の URL の形が素通りから block に変わり、既存のテストで反転するものが 0 本であることを実測した。メインの案も A。実データは PR URL を記録した 181 件中 1 件が正準形でない。3 巡目の後なので、確かめは無効化後の差分巡で行う |
| F1 | 独立-4 | high | yes | self-inflicted | pr-url-target-match | fixed | 値を取る短い flag を束ねた merge（`gh pr merge -st <URL> 7`）では URL と番号が両方残り、URL の形の照合が番号を見なくなったため、番号の PR を記録した steering の承認の証跡を見ずに通っていた。URL の形の照合を撤回し、番号でも照合する形に戻した。commit: 1ac8dfff |
| F2 | 独立-4 | high | yes | inherited | pr-url-target-match | fixed | 台帳の経路で、記録した PR URL から repo を取り出せないと、repo の比較が一致しないとして照合から外れ、承認の証跡を見ずに通っていた。取り出せないときは照合したものとして止める側に倒した。commit: 913c6f05 |
| F3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation に、候補 0 件の経路で対象 PR を照合するテストが挙がっていない。follow_up_of の PR の無効化後の巡の low なので限界として PR 本文に書く |
| P4 | 方針メモ-4 | advisory | no | inherited | pr-url-target-match | next-pr | 安全策 4 の再発火（high を含む巡が 4 回）。Opus は F1 をパーサで閉じる案（URL と番号が合わせて 2 つ以上なら unresolvable）と F2 の修正を推奨し、複製で既存のテストの反転が 0 本であることを実測した。メインの案も同じ。短い flag の束ね（`-st 7`・`-sRacme/other 7`）で値を位置引数に読む既存のパーサの限界と、marker の無い checkout の台帳の経路が照合できない対象を通す限界は、次の PR で直す |
| G1 | 独立-5 | high | yes | self-inflicted | pr-url-target-match | fixed | marker の無い git checkout の台帳の経路で、URL と番号が両方見える merge が unresolvable になり unknown として通る。差分前（main も同じ）は URL の番号で hit して止まっていた `gh pr merge -st 8 <URL#7>`・`-st 8 7` が通る。URL と番号が両方見える形を unresolvable にするパーサの扱いを撤回し、台帳の経路は URL の番号で照合する形に戻した。commit: 1ac8dfff |
| G2 | 独立-5 | high | yes | inherited | pr-url-target-match | accepted | 位置引数のブランチ名は数えないので、`gh pr merge -st 7 <branch>` は番号 7 で照合して外れ、found・multiple・候補 0 件のどの経路でも通る。main から残る欠陥（常時 High）。PR 本文の限界の節の先頭に書き、次の PR（gh の短い flag の文法）で直す |
| G3 | 独立-5 | high | yes | inherited | pr-url-target-match | accepted | パーサは短い flag を綴りで列挙し、束ねた形（`-st 7`）の値を位置引数に読み、値を密着させた `-R`（`-Racme/other 7`・`-R=…`・`-sR…`）は repo の上書きを落とす。main から残る欠陥（常時 High）。PR 本文の限界の節の先頭に書き、次の PR（gh の短い flag の文法）で直す |
| G4 | 独立-5 | high | yes | inherited | gh-command-grammar | accepted | sub-command の前に値を密着させた `-R`（`gh -Racme/w pr merge 7`）や、`pr` と `merge` の間の `-R` で、merge と判定しない。main から残る欠陥（常時 High）。PR 本文の限界の節の先頭に書き、次の PR（gh の短い flag の文法）で直す |
| G5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | `test_number_is_still_matched_when_a_url_is_also_given` の名前と docstring が実装（番号も URL も対象にしない）と逆で、止まった理由を assert していない。撤回で名前と docstring は実装と合った。止まった理由を assert しない点は、follow_up_of の PR の low として限界に書く |
| G6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | `_mg_ledger_verdict` の頭のコメント「番号だけでは照合しない」が、repo を取り出せない記録を番号だけで hit にする動作と食い違う。follow_up_of の PR の low。限界として PR 本文に書く |
| P5 | 方針メモ-5 | advisory | no | inherited | pr-url-target-match | accepted | 安全策 4 の再発火（high を含む巡が 5 回、巡の上限も使い切った）。Opus は URL の形の照合とパーサの扱いを撤回する案を推奨した。複製の 108 ケースで、main と比べて新しく通る形が撤回前は 7、撤回後は 0（新しく止まるのは候補 0 件の経路の 10 形）。merge gate は独立-3 で見た bc1c786f と、台帳の `_rrepo` の hunk だけが違う。メインの案も同じ。撤回を確かめる差分巡（新しい無効化）を 1 回回す。I3-1・G2〜G4 は main から残る常時 High として accepted にし、次の PR で直す |
| H1 | 独立-6 | high | yes | inherited | pr-url-target-match | accepted | URL の形の merge は文字列全体の一致で照合するので、正準形でない PR URL を記録した steering を通す（I3-1 と同じ。main と同じ挙動）。番号の形で止めたときの block 文が URL の形での打ち直しを案内する点も含め、方針メモ-5 のとおり次の PR（対象の読み取り）で直す。限界の節の先頭に書く |
| H2 | 独立-6 | high | yes | inherited | pr-url-target-match | accepted | 短い flag の束の値を位置引数に読み、`gh pr merge 7 -st 8`・`8 -sb <URL#7>`・`-R … -st <URL#8> 7` で本当の対象を検査しない（G3 と同じ。パーサは main と同一）。方針メモ-5 のとおり次の PR で直す。限界の節の先頭に書く |
| H3 | 独立-6 | medium | no | self-inflicted | doc-claim | accepted | 断片の「URL と番号が両方見える merge も台帳の PR として止める」「対象 PR を記録した steering を検査する」が、URL が台帳の PR でない向きと、正準形でない PR URL の URL の形の merge では成り立たない。follow_up_of の PR の medium なので限界として PR 本文に書く |
| J1 | 独立-7 | high | yes | inherited | pr-url-target-match | accepted | URL の形の merge は、正準形でない PR URL を記録した steering と照合せず通す（I3-1・H1 と同じ。main と同じ挙動で、この PR の候補 0 件の経路も同じ照合を使う）。台帳の経路は同じ入力を止めるので受理集合が割れている。方針メモ-5 のとおり次の PR で直す。限界の節の先頭に書く |
| J2 | 独立-7 | medium | no | self-inflicted | test-power | accepted | pre-push の「binding 先を判定できないとき」のテストは、作業中の steering に証跡が無いので binding 先の分類によらず止まり、判別力が無い。断片の Validation の主張も成り立たない。限界として PR 本文に書く |
| J3 | 独立-7 | low | no | self-inflicted | test-power | accepted | 数え直さない分岐に、読めない state.md・`Next Action` の欠落・大文字・tasklist.md だけの cancelled で found を返すテストが無い |
| J4 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | phase-gate-prechecks.md の「local state が無いときは入れない」は、session id が取れない runtime の SessionStart では成り立たない（I2-2 と同じ） |
| J5 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | `gdd_detect_active_steering` の冒頭コメントが、数え直さない呼び出しでも `Next Action: cancelled` を終端にすることを書いていない |
| J6 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | 断片と self-review-lanes.md の「PR を記録した steering がある checkout で対象を省いた merge は steering-ambiguous で止める」は候補 0 件のときだけ成り立つ（I3-3 と同じ） |
| J7 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | merge gate のテストクラスの docstring が、tip に無い素通りの挙動（数え直さない分岐の後の素通り）を書いている |
| J8 | 独立-7 | low | no | self-inflicted | test-power | accepted | 候補 0 件の経路の通す側（PR を記録した steering が無い・`.steering` が無い checkout の引数なしの merge）のテストが無い（I3-2 と同じ） |
| J9 | 独立-7 | low | no | self-inflicted | test-power | accepted | peer turn の不正な UTF-8 と値だけの Edit のテストが exit 2 だけを見て、deny の理由と人のターンの通過を見ていない |
| J10 | 独立-7 | low | no | self-inflicted | test-power | accepted | `NON_CANONICAL_PR_URLS` の 5 形のうち 4 形がどのテストにも使われていない |
| J11 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | 候補 0 件の block は untrusted root の検査より前に走り、中止の steering だけが残る untrusted root で reason code と許可の条件が変わるが、PR 本文と断片に書かれていない |
| J12 | 独立-7 | low | no | self-inflicted | product | accepted | `steering-ambiguous` の復旧文（完了済み steering の整理）が、候補 0 件の block では解除の手段にならない（I3-5 と同じ） |
| J13 | 独立-7 | advisory | no | self-inflicted | test-power | accepted | `_brainstorming_discard_values()` が skill の行を散文で探し、見つからないと import 時にモジュール全体が落ちる |
| J14 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | README と phase-gate-prechecks.md の session 照合の書き方（「または空」、UserPromptSubmit の「何も渡さず」）がそろっていない |
| J15 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に、self-review-lanes.md の追記と test_state_field_value_less_line_contract.py の docstring の変更が無い。PR 本文を直す |
