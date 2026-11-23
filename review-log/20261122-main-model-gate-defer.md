---
lane: L1+
pr: 733
follow_up_of: 731
amends: 20261030-main-model-gate.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) + user | 1217d9d1 | 0 | 0 | 0 | 2026-11-22 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ff7ba002 | 3 | 4 | 3 | 2026-11-22 |
| 方針メモ-1 | 再設計, Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | ff7ba002 | 0 | 0 | 0 | 2026-11-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 96e411d9 | 4 | 4 | 4 | 2026-11-22 |
| 方針メモ-2 | 再設計, Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | 96e411d9 | 0 | 0 | 0 | 2026-11-22 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 13dbdf9a | 2 | 2 | 0 | 2026-11-22 |
| 方針メモ-3 | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | 13dbdf9a | 0 | 0 | 0 | 2026-11-22 |
| 方針メモ-4 | 再設計, Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) + user | f7d69dd6 | 0 | 0 | 0 | 2026-11-22 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 015583cb | 2 | 1 | 2 | 2026-11-22 |
| 方針メモ-5 | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | 1d5fa0aa | 0 | 0 | 0 | 2026-11-22 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | c4558fd8 | 1 | 0 | 1 | 2026-11-22 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | ee06b4a8 | 0 | 1 | 0 | 2026-11-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M0-1 | 方針メモ | advisory | no | self-inflicted | design | fixed | 2 本とも、止める判定を返事の前の UserPromptExpansion から、その turn の main の最初の PreToolUse に移す案を推した（作らない案・止める文だけ直す案は推さない）。方針メモを本文でユーザーに示し、推奨で進めた。commit: 4998a1a3 |
| I1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（判定待ちの印を turn の寿命で持つ）。印を Stop で消すが、ほかの Stop hook が停止を block すると turn が続き、残りの Sonnet の道具が通る。方針メモ-1 で印を撤去し、GDD の入口で毎回判定する形にした。commit: 4d2b0c8f |
| I1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（同上）。展開を止めないので本文が context に残り、deny → Stop の後の「続けて」で setup-gdd-loop.sh が判定されずに通る。入口（setup-gdd-loop.sh の Bash を含む）で毎回判定するので閉じる。commit: 4d2b0c8f |
| I1-3 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（印を見る fast path）。set -u の下の ${HOME} で HOME 未設定だと exit 1 になり判定されない。印と fast path を撤去し、shell の前段は stdin の語だけで絞る。commit: 4d2b0c8f |
| I1-4 | 独立-1 | medium | no | self-inflicted | product | fixed | hooks.json の description の番号が PreToolUse の配線の本数と合わず、契約テストが落ちる。再設計で Skill の登録の matcher を広げ、本数を base と同じにした。commit: 4d2b0c8f |
| I1-5 | 独立-1 | medium | no | self-inflicted | product | fixed | command の引数 pending が command の書式の契約に反し、契約テストが落ちる。引数を撤去した。commit: 4d2b0c8f |
| I1-6 | 独立-1 | medium | no | self-inflicted | product | fixed | 前提（PreToolUse の時点で今の返事の行が transcript にある）が未検証なのに、逃げ道の案内文を外した。文書は transcript が非同期に書かれ遅れうると書く。今の返事の行が取れず前の信号で判定したときに限って案内文を残し、どの段で判定したかを log に書く。commit: 4d2b0c8f |
| I1-7 | 独立-1 | medium | no | self-inflicted | product | fixed | 印が API エラー・Esc の turn で残り、無関係の作業を誤って deny する。印を撤去した。commit: 4d2b0c8f |
| I1-8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 判定の移った先の opt-out・kill switch・知らせない分岐にテストが無い。入口ごとのテストに書き直した。commit: 4d2b0c8f |
| I1-9 | 独立-1 | low | no | self-inflicted | test-power | fixed | hooks.json の command から pending を落としても配線のテストが通る。配線のテストで command と matcher を固定した。commit: 4d2b0c8f |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | README の PreToolUse の hook 数が配線と合わない。本数を直した。commit: 4d2b0c8f |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docs/SECURITY.md の通す場合の一覧に、差分で増えた通す場合が無い。前の返事のモデルで判定したときに通す場合を足した。commit: 4d2b0c8f |
| I1-12 | 独立-1 | low | no | self-inflicted | product | fixed | どのセッションの印でも残れば全道具の呼び出しで python が起きる。印を撤去した。commit: 4d2b0c8f |
| I1-13 | 独立-1 | advisory | no | self-inflicted | design | accepted | 誤停止の実測 0 件の損失のために穴を入れる取引になっている。ユーザーが依頼に含めると答え、相談役 2 本も直す側を推したので、作り直して進める |
| PM1-1 | 方針メモ-1 | advisory | no | self-inflicted | design | fixed | 再設計: 前提: ずれる（返事の前に印を置けば、turn の最初の道具の呼び出しで今の返事のモデルを読める、という turn 単位の前提）。2 本とも、印をやめ、GDD の入口（gdd-dev・gdd-resume の Skill、setup-gdd-loop.sh を実行する Bash、.claude/gdd-dev.local.md への書き込み）で毎回、tool_use_id の行・今の turn の行・最後の信号の順で今の返事のモデルを取る案を推した。最後の信号に落ちたときに限って案内文を残し、段を log に書く。実データの入口の件数（main が Sonnet）: setup-gdd-loop.sh の Bash 533、gdd-dev.local.md の書き込み 132、Skill 222。commit: 4d2b0c8f |
| I2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 再設計: 設計: 変える（Bash の command の文字列から setup の実行を見分ける）。最初の語の basename の列挙で既定が allow なので、`/bin/bash X`・`bash -x X`・`if …; then X; fi` が通る。判定を setup-gdd-loop.sh の中へ移し、hook は Bash を判定しない。どう包んで実行しても script が動けば判定する。commit: 44588d5c |
| I2-2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 再設計: 設計: 変える（state ファイルへの書き込みを入口に数える）。`cp`・`sed -i`・`cd .claude && …` などが通る。書き込みの入口を外し、setup が止めたら手で進めないよう止める文で案内する。手で書く形は限界として開示する。commit: 44588d5c |
| I2-3 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（判定の結果を作る前にログを書く）。孤立サロゲートのモデル名で UnicodeEncodeError が起き deny が出ない。判定の結果を先に作り、ログの中身全体を except Exception で包む。再現テストを先に書いた。commit: 44588d5c |
| I2-4 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 再設計: 設計: 変える（読み直しごとに全体を走査する）。大きい transcript で hook の timeout を超えて通る。末尾 4 MiB だけを読み、合計 3 秒の期限で打ち切って最後の信号に落とす。commit: 44588d5c |
| I2-5 | 独立-2 | medium | no | self-inflicted | verification | accepted | 依頼の効果（画面で切り替えた直後に今の返事の行を読めるか）を実環境で確かめていない。週の上限が解けたら headless で log の段を測る。測れないうちは限界として開示する |
| I2-6 | 独立-2 | medium | no | self-inflicted | scope | fixed | 書き込みの入口は依頼より広い deny で、承認の記録が無い。書き込みの入口を外した。commit: 44588d5c |
| I2-7 | 独立-2 | medium | no | self-inflicted | product | fixed | `>` を含めば読み取りも止める。hook は Bash を判定せず、script が動いたときだけ判定するので、読むだけでは止めない。commit: 44588d5c |
| I2-8 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | SECURITY.md の state dir の一覧にログが無い。一覧に足し、0600・session のハッシュ・書けないときの扱いを書いた。commit: ec5acf3c |
| I2-9 | 独立-2 | low | no | self-inflicted | test-power | fixed | 次の turn でも毎回判定することのテストが、状態を持つ実装を落とさない。state を撤去し、setup を 2 回走らせて 2 回とも止まることを見るテストにした。commit: 6d364b26 |
| I2-10 | 独立-2 | low | no | self-inflicted | test-power | accepted | 読み直しのテストが起動の速さに依存する |
| I2-11 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 新しい deny の条件に当たる件数が PR 本文に無い。PR 本文の目的に実データの件数を書く。commit: なし（PR 本文） |
| I2-12 | 独立-2 | advisory | no | self-inflicted | product | accepted | 最後の信号に落ちるまでの待ち（今は最大 3 秒）が、テストと信号の無いセッションに乗る |
| I2-13 | 独立-2 | advisory | no | self-inflicted | design | accepted | subagent の呼び出しの扱いが決まっていない。今までどおり main の返事のモデルで判定し、Skill の呼び出しでテストを足した |
| PM2-1 | 方針メモ-2 | advisory | no | self-inflicted | design | fixed | 再設計: 前提: ずれる（GDD の始まりを、hook が見る道具の呼び出しの形から見分けられる）。入力者の実測（main が Sonnet・Haiku で setup-gdd-loop.sh を含む Bash 637 件）で事故で打つ形は 1 件以上あり、許可リスト v2 ならすり抜け 0 だが読むだけ 236 件のうち 105 件を誤って止める。2 本とも、判定を setup-gdd-loop.sh の中へ移し hook は Skill だけにする案を推した。Fable（信号①）は Write・Edit の file_path の入口を残し opt-out の語を含む Bash を止める案を推したが、どちらも件数が未測で依頼の外に広がるので採らず、限界として開示する。commit: 44588d5c |
| I3-1 | 独立-3 | high | no | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（setup の判定の入力を agent の Bash の環境から読む）。setup の判定の入力（opt-out・GDD_RUNTIME・CLAUDE_CODE_SESSION_ID・CLAUDE_CONFIG_DIR・HOME）を agent の Bash の環境から読むので、前に付ければ外せる。止める文が変数名を名指ししている。前に付けて外した実測は 0 件で (b) に当たるが、再設計は上限の 2 回に達したのでユーザーに戻す。推奨の方向: opt-out を settings のファイルの env から読み、runtime は process tree の判定を使う。ユーザーが推奨の方向を選んだので、そのとおりに直した。commit: a48eebcf |
| I3-2 | 独立-3 | high | no | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（書き込みの入口を外した）。setup が走らなかったときの commands/gdd-dev.md の手動の手順（.claude/gdd-dev.local.md を書いて進める）が、どこでも判定されない。Sonnet・Haiku の main が active: true を Write した 11 件は、手動の手順で始めたものと分けていない（入力者を測れない）。再設計の上限でユーザーに戻す。推奨の方向: 手順を Write ツールに決め、ファイルが無いか active でないところから始める Write・Edit・MultiEdit だけを hook で判定する。ユーザーが推奨の方向を選んだので、そのとおりに直した。commit: a48eebcf |
| I3-3 | 独立-3 | medium | no | self-inflicted | verification | accepted | 依頼の効果（Skill の hook・setup の実行の時点で今の返事の行があるか、setup がデスクトップアプリの transcript を見つけられるか）を実環境で確かめていない |
| I3-4 | 独立-3 | medium | no | self-inflicted | product | accepted | setup を実行するほかのテストと validate が、実 HOME の main-model-gate.log に行を書き、段の実測を汚す |
| I3-5 | 独立-3 | low | no | self-inflicted | test-power | accepted | 末尾読みのテストが、末尾読みも全体読みへの切り替えも固定していない |
| I3-6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | README の「7 matcher」が実体（6 種）と合わない |
| I3-7 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | ログにモデル名を伏せずに入れ、tab・改行で列がずれうる |
| I3-8 | 独立-3 | low | no | self-inflicted | product | accepted | 期限で走査を打ち切ったときも、途中までの値を current_turn として返す |
| I3-9 | 独立-3 | low | no | self-inflicted | product | accepted | setup からの python の起動に -X utf8 が無い |
| I3-10 | 独立-3 | low | no | self-inflicted | product | accepted | _scan の getsize が OSError しか捕まえず、通知とログの行が消える（判定は通すで変わらない） |
| I3-11 | 独立-3 | low | no | self-inflicted | product | accepted | ログは GDD_HOOK_STATE_DIR に従うが、通知の印は従わない |
| I3-12 | 独立-3 | low | no | inherited | product | accepted | Stop の通知が読む main_model() は transcript を毎回全部読む |
| I3-13 | 独立-3 | low | no | self-inflicted | style | accepted | テストの重複した assert・呼び出しと、合わなくなったテスト名 |
| I3-14 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の件数の数え方が差分にも本文にも無い |
| PM3-1 | 方針メモ-3 | advisory | no | self-inflicted | design | fixed | 2 本とも、I3-1・I3-2 は (a) の条件を満たさず（I3-1 は実測 0 件、I3-2 は入力者を測れない。deny の条件を足す修正は (a) に数えない）、再設計は上限の 2 回に達したので、ユーザーに戻すと推した。推奨の方向は、opt-out を settings のファイルの env から読むことと、手順を Write に決めて始める書き込みだけを hook で判定すること。commit: a48eebcf |
| PM4-1 | 方針メモ-4 | advisory | no | self-inflicted | design | fixed | 再設計: 前提: ずれる（setup の判定の入力と外し方を、agent の Bash のプロセスの環境から読んでよい）。ユーザーが方針メモ-3 の推奨（settings のファイルの env から外し方を読み、runtime は process tree で決め、手動の手順を Write に決めて run を始める書き込みを hook で判定する）を選んだので、そのとおりに作り直した。commit: a48eebcf |
| I4-1 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（書いた後の中身の active: true の行の形を読む）。`active: True` などの書き方で判定を通らずに run を始められる。ディスクのファイルが active でなければ書く内容を見ずに判定し、active かは Stop hook と同じ読み方（state_io.marker_state）で決める。再現テストを先に書いた。commit: 1d5fa0aa |
| I4-2 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変えない（ユーザーが realpath で直す案を選んだ）。対象ファイルの認識が file_path の末尾 2 要素の文字列だけで、`..` を挟む・大文字小文字の違う・symlink の別名が判定されない。手順どおりの書き込みは 141/141 件決まった形で、別名は 0 件なので (b) に当たるが、再設計は上限を超えたのでユーザーに戻す。cwd と結合して realpath で解決したパスと字面のどちらかを、大文字小文字を問わずに比べ、wrapper の絞り込みも大文字小文字を問わない形にした。再現テストを先に書いた。commit: ee06b4a8 |
| I4-3 | 独立-4 | low | no | self-inflicted | product | accepted | ディスクが active なら、別の session の持ち物でも書き換えを判定しない |
| I4-4 | 独立-4 | low | no | self-inflicted | test-power | accepted | setup のテストが、実行した環境の process tree と一時ディレクトリの祖先の settings で結果が変わる |
| I4-5 | 独立-4 | medium | no | self-inflicted | test-power | fixed | 読めないときは判定する分岐を固定するテストが無い。ディレクトリのパスと孤立サロゲートのパスで deny になることを assert した。commit: 1115bc7c |
| I4-6 | 独立-4 | low | no | self-inflicted | test-power | accepted | 外し方の「cwd から上」・CLAUDE_CONFIG_DIR・Write の入口の外し方を試すテストが無い |
| I4-7 | 独立-4 | low | no | self-inflicted | product | accepted | 外し方を受け取る集合が hook（プロセスの環境）と setup（settings のファイル）で食い違う |
| I4-8 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の止めない形の列挙と「前に付けた値では外れない」の断定が、実装より広い（PATH など） |
| I4-9 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | テストの docstring・README・変更断片・ログの入口の列が、書き込みの入口に追随していない |
| I4-10 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | PR 本文の実測が、新しく足した発火条件の件数になっていない |
| I4-11 | 独立-4 | low | no | self-inflicted | product | accepted | Path.cwd() の例外で、setup の判定が通る側に落ちる |
| I4-12 | 独立-4 | advisory | no | self-inflicted | product | accepted | 全 session の Write・Edit・MultiEdit で wrapper が起動する負荷を測っていない |
| PM5-1 | 方針メモ-5 | advisory | no | self-inflicted | design | accepted | 2 本とも、I4-2 は実測 0 件で (b) に当たり、再設計の上限を超えたのでユーザーに戻すと推した。戻すときの推奨は割れた（realpath と casefold で直す／限界として出す）。python を起こす前の語の絞り込みが名前の違う symlink を落とし、Bash の書き込みも開示済みの限界なので、main は限界として出す側を推す |
| I5-1 | 独立-5 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変えない（ユーザーが realpath で直す案を選んだ）。I4-2 と同じ。state ファイルを `..`・相対と cwd・大文字小文字・symlink の別の綴りのパスで書くと判定されない。I4-2 の返事に合わせて扱う。cwd と結合して realpath で解決したパスと字面のどちらかを、大文字小文字を問わずに比べ、wrapper の絞り込みも大文字小文字を問わない形にした。再現テストを先に書いた。commit: ee06b4a8 |
| I5-2 | 独立-5 | low | no | self-inflicted | product | accepted | 別の session の active な state と session_id が空の active な state への書き込みは判定しない |
| I5-3 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化が、書く内容を見ない判定になっていない。commit: なし（PR 本文） |
| I5-4 | 独立-5 | low | no | self-inflicted | test-power | accepted | import の失敗で判定する側に倒す分岐を、テストが固定していない |
| I5-5 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | active: が 2 行ある state では「Stop hook と同じ読み方」が成り立たない（止める側だけ） |
| I5-6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md とテストの docstring のログの入口の列挙が Write を欠く |
| I5-7 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | README の § モデル選択が MultiEdit を挙げていない |
| I6-1 | 独立-6 | medium | no | self-inflicted | test-power | accepted | realpath の例外で判定する側に倒す分岐を、テストが通らない。テストの環境の python3（3.9）は、孤立サロゲート・NUL のパスでも realpath が例外を出さずに字面で解決するので、入口から通す入力を作れなかった |
| I6-2 | 独立-6 | low | no | self-inflicted | product | accepted | wrapper の nocasematch が Skill・Stop・SessionStart の語にも効き、小文字の skill・stop を含む書き込みでも python を起こす（判定は変わらない） |
| I6-3 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 変更断片とテストの説明の「symlink を解決」が、名前の違う file symlink を除いていない。wrapper のコメントは判定のコードなので直していない。commit: f9991520 |
| I6-4 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | SECURITY.md の止めない形に、hardlink と名前の違う symlink を通した書き込みが無い。commit: f9991520 |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に、パスの解決と大文字小文字を問わない比較が無い。commit: なし（PR 本文） |
| I6-6 | 独立-6 | advisory | no | self-inflicted | product | accepted | 解決できないパスは、state ファイルと無関係でも判定する（止める側） |
| I6-7 | 独立-6 | advisory | no | self-inflicted | product | accepted | hardlink と名前の違う file symlink は、ユーザーが選んだ案の残りとして high に数えなかった |
| I6-8 | 独立-6 | advisory | no | self-inflicted | doc-claim | fixed | SECURITY.md のログの入口とテストの docstring が Write の入口を欠く。commit: f9991520 |
