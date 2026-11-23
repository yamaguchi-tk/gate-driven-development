---
lane: L1+
pr: 626
follow_up_of: 620
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 96bf0b53 | 0 | 10 | 2 | 2026-10-31T14:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | bc77b7f2 | 0 | 6 | 0 | 2026-10-31T16:20+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 867e4ace | 1 | 2 | 1 | 2026-10-31T17:00+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | c26c81bd | 0 | 1 | 1 | 2026-10-31T17:50+09:00 |
| 方針メモ-1 | Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) + user | c26c81bd | 0 | 0 | 0 | 2026-10-31T18:20+09:00 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 3586d567 | 0 | 2 | 0 | 2026-10-31T19:00+09:00 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 122d46e5 | 0 | 2 | 0 | 2026-10-31T19:40+09:00 |
| 方針メモ-2 | Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) + user | 864a23f7 | 0 | 0 | 0 | 2026-10-31T21:00+09:00 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | b5b7b860 | 0 | 1 | 0 | 2026-10-31T21:40+09:00 |
| 方針メモ-3 | Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) | b5b7b860 | 0 | 0 | 0 | 2026-10-31T22:00+09:00 |
| 独立-8 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | c83ada0f | 0 | 1 | 1 | 2026-10-31T23:00+09:00 |
| 方針メモ-4 | 再設計, Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) | c83ada0f | 0 | 0 | 0 | 2026-10-31T23:50+09:00 |
| 独立-9 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b7075363 | 1 | 3 | 1 | 2026-11-01T00:40+09:00 |
| 独立-10 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d60989f4 | 0 | 2 | 1 | 2026-11-01T01:40+09:00 |
| 独立-11 | light-lane-independent-reviewer-xhigh, 差分, model: opus | ce227941 | 1 | 3 | 1 | 2026-11-01T02:10+09:00 |
| 独立-12 | light-lane-independent-reviewer-xhigh, 差分, model: opus | aac63ff6 | 0 | 0 | 0 | 2026-11-01T03:10+09:00 |
| 独立-13 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | d50f0712 | 0 | 1 | 0 | 2026-11-01T04:10+09:00 |
| 方針メモ-5 | 再設計, Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) | d60989f4 | 0 | 0 | 0 | 2026-11-01T02:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼から外れた: 範囲の終わりが突き合わせの起動になり、/gdd-dev の後の発言まで入っていた。範囲の終わりを transcript の最後の /gdd-dev の起動（打ったコマンドか main の Skill）にした（新しい state を足さずに transcript で決める）。commit: 366bdbc2 |
| r1-2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 設計: 変える（写しを控えて戻す仕組みをやめた。依頼は新しい記録の仕組みを足さないとしていた）。hook の state に節の控えを期限なしで残していた。commit: 366bdbc2 |
| r1-3 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼から外れた: main が /gdd-dev に渡した文と runner が引数から写した行を request.md の中に見出しつきで残していた（依頼は別のファイル）。どちらも request-notes.md に書くようにした。commit: 366bdbc2 |
| r1-4 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 列挙: 依頼から外れた: 前のタスクの終わりを done だけにしていた。cancelled も終わりにした。commit: 366bdbc2 |
| r1-5 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 依頼から外れた: 直前の assistant の文を最後の text 1 つだけにしていた。前の発言の後の main の文をすべて添えるようにした。commit: 366bdbc2 |
| r1-6 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 突き合わせ agent と完了前の reviewer の原文の定義が、節の外に足した発言を数えるか読み分けられない（修正の commit で定義の文は直したが、指摘としては受け入れ） |
| r1-7 | 独立-1 | medium | no | self-inflicted | product | accepted | 回し直しの突き合わせ（昇格など）で、節が無い古いタスクの request.md に今の session の発言で節ができる |
| r1-8 | 独立-1 | medium | yes | self-inflicted | data-loss | fixed | 設計: 変える（控えと戻しをやめ、節があれば何もしない）。控えが無く節がある request.md で、既存の節を別 session の発言で置き換えていた。再現テストを足した。commit: 366bdbc2 |
| r1-9 | 独立-1 | medium | yes | self-inflicted | security-boundary | fixed | 設計: 変える（控えと戻しをやめた）。人が節から秘密を消しても、控えから戻していた。再現テストを足した。commit: 366bdbc2 |
| r1-10 | 独立-1 | medium | no | self-inflicted | product | accepted | request.md を相対パスで渡すと写さない（文書には絶対パスで渡すと書いた） |
| r1-11 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | SECURITY.md の hook ごとの読む範囲と書き込み先の表に、新しい hook の行が無い |
| r1-12 | 独立-1 | low | no | self-inflicted | acceptance-set | accepted | 伏せ字が検査の止めるものを全部は覆わない（Worktree の行、LF 以外の改行） |
| r1-13 | 独立-1 | low | no | self-inflicted | acceptance-set | accepted | 列挙: origin を書かない版の host への逃げ道が無い |
| r1-14 | 独立-1 | low | no | self-inflicted | acceptance-set | accepted | 列挙: origin の無い <command-name> の行を受け入れる（model が起動したコマンドに host がこの行を書くかは未確認） |
| r1-15 | 独立-1 | low | no | self-inflicted | fail-open | accepted | dict でない message・lone surrogate で写すこと全体が止まり、ログも残らない |
| r1-16 | 独立-1 | low | no | self-inflicted | product | accepted | 発言に節の終わりの marker の文字列があると、読み手が節の終わりを取り違える |
| r1-17 | 独立-1 | low | no | self-inflicted | product | fixed | 控えの場所が GDD_HOOK_STATE_DIR を読まない（控えをやめたので無くなった）。commit: 366bdbc2 |
| r1-18 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | hooks.json の (16) が「the same hook」の前に入り、戻す条件も書いていなかった。SessionStart の文の後ろに移し、条件を書いた。commit: 366bdbc2 |
| r1-19 | 独立-1 | low | no | self-inflicted | test-power | accepted | 見出しを入れ替える変異でもテストが通る |
| r1-20 | 独立-1 | low | no | self-inflicted | product | accepted | 列挙: 範囲が広く、関係の無い頼みごとも原文の正本に入る |
| r1-21 | 独立-1 | advisory | no | self-inflicted | approval-path | accepted | 写す発言が 0 件のとき、先に書かれた BEGIN〜END の塊が残る |
| r1-22 | 独立-1 | advisory | no | self-inflicted | request-drift | accepted | system-reminder を queued の発言とコマンドの引数から取り除いていない |
| r1-23 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの見本の秘密の値を連結で組み立てていない |
| r1-24 | 独立-1 | advisory | no | self-inflicted | product | accepted | atomic な書き込みで request.md の mode が 0600 になり inode も変わる |
| r2-1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 依頼から外れた: runner が引数から写した行まで request.md から出していた（依頼が分けると言ったのは main の注記だけ）。節の下の見出しの下に残し、hook の節が無いときは今までどおり原文として書く規定にした。commit: d7f69694 |
| r2-2 | 独立-2 | medium | no | self-inflicted | product | accepted | /gdd-dev の起動から突き合わせまでのユーザーの発言（Clarification Loop の答え）がどこにも写されない |
| r2-3 | 独立-2 | medium | no | self-inflicted | acceptance-set | accepted | 列挙: BEGIN の文字列がどこかにあるだけで節を作らない |
| r2-4 | 独立-2 | medium | no | self-inflicted | product | accepted | 列挙: 節が消えたときに戻さない（追記だけにする規定か、写し直す条件の案） |
| r2-5 | 独立-2 | medium | no | self-inflicted | request-drift | accepted | 確認済み（2026-11-01 ユーザーが推奨で OK）: 写す時機を「/gdd-dev の起動時」から「突き合わせの起動時」に替えたことを、ユーザーに確かめていない。PR 本文の限界の節に問いを書いた |
| r2-6 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 依頼から外れた: PR 本文が人の確認への返事を main が足すことを「依頼より狭い」と書いていた。対策 B の範囲は /gdd-dev までなので縮小ではなく、種類を直した。commit: なし（PR 本文） |
| r2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 入口の script のコメントに、控えから戻す記述が残っている |
| r2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | human-check-template・変更断片・PR 本文の原文の定義が、節の下に足した発言を数えない |
| r2-9 | 独立-2 | low | no | self-inflicted | test-power | accepted | 列挙: 起動 2 回・既存の request-notes.md・notes の伏せ字をテストが固定していない |
| r2-10 | 独立-2 | low | no | self-inflicted | fail-open | accepted | request-notes.md の書き込みが失敗すると、main の引数が二度と写らない |
| r2-11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 人の発言が無い session では main の引数も request-notes.md に書かないことを、本文と断片が書いていない |
| r2-12 | 独立-2 | low | no | self-inflicted | product | accepted | 範囲に /gdd-dev の起動が無いと今までの発言を全部写す |
| r2-13 | 独立-2 | low | no | self-inflicted | acceptance-set | accepted | タスクの終わりの判定（done・cancelled、行頭だけ）が Stop hook と食い違う |
| r2-14 | 独立-2 | low | no | self-inflicted | acceptance-set | accepted | LF 以外の行区切りを置き換えず、後の書き直しが steering の検査で止まる |
| r2-15 | 独立-2 | low | no | self-inflicted | request-drift | accepted | 確認済み（2026-11-01 ユーザーが推奨で OK）: tool を断ったときの理由を写さない判断を、ユーザーに確かめていない。PR 本文の限界の節に問いを書いた |
| r2-16 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の hook の表に request-notes.md の読み書きが無い |
| r2-17 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の節の大きさを今の規則で測り直したかが確かめられない |
| r3-1 | 独立-3 | high | yes | self-inflicted | approval-path | fixed | 設計: 変える（runner の写しの置き場を文書の順序に任せず、hook が節を入れるときに request.md の中身を request-notes.md に機械で移す）。Skill 経由の起動で、runner が写した main の要約が見出しの無いまま節の下に残り、原文・承認として読まれえた。再現テストを足した。commit: 7a066acf |
| r3-2 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | 依頼から外れた: runner の写し（Skill 経由では main の要約）を request.md に置いていた（依頼は main の文を別のファイルに分ける）。hook が request-notes.md に移す。commit: 7a066acf |
| r3-3 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | 読む側 4 箇所が runner の見出しを知らない（request.md に runner の行が残らなくなったので、読む側が見分ける場面は無くなった） |
| r3-4 | 独立-3 | low | no | self-inflicted | product | accepted | 列挙: 足す発言が runner の見出しの下に入りうる（request.md に runner の見出しが無くなった） |
| r3-5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文が runner の写しの置き場を正しく書いていない。commit: なし（PR 本文） |
| r3-6 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 変更断片が runner の行の置き場を書いていない。commit: 7a066acf |
| r3-7 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | Skill の引数のテストの名前ほどの性質を固定していない |
| r4-1 | 独立-4 | medium | yes | self-inflicted | approval-path | fixed | 設計: 変える（原文を request.md の自由文から見分けず、transcript から作り直す）。節を入れる前の request.md にある、main が時刻つきで足したユーザーの発言（返事など）や再開前の元の依頼まで「原文ではない」として request-notes.md に移す。commit: 3586d567 |
| r4-2 | 独立-4 | low | no | self-inflicted | product | accepted | 打ったコマンドだけ（/model opus など）の session でも節ができ、元の依頼を移して request.md に依頼が残らない |
| r4-3 | 独立-4 | low | no | self-inflicted | product | accepted | 移した中身の見出しがそのまま入り、構造が「原文ではない」の外に出る |
| r4-4 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | README・docstring・hooks.json・断片の「先頭に写す」が作り直しの挙動と合わない |
| r4-5 | 独立-4 | low | no | self-inflicted | request-drift | accepted | 確認済み（2026-11-01 ユーザーが推奨で OK）: 写す時機を突き合わせの起動時に替えたことをユーザーに確かめていない（r2-5 と同じ問い） |
| r4-6 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 移す中身は置き換えずに書くのに、SECURITY.md は写すときに置き換えると書く |
| m1-1 | 方針メモ-1 | advisory | no | self-inflicted | approval-path | fixed | 安全策 4 の発火（高か blocking の巡が 3 回）。相談役 2 本が割れた（案 D: 移す塊の「原文ではない」を外し候補として読む／案 A': 再開の起動では何もせず、起動の後の発言を transcript から節の下に写す）。main は A' を採った（自由文の見分けをやめ宣言フィールドから作り直す。読む側の文書は既に「節の下に時刻つきで足した発言」を原文としている）。1 回目の発火なので推奨で進め、ユーザーの返事待ち。commit: 3586d567 |
| r5-1 | 独立-5 | medium | no | self-inflicted | product | fixed | 設計: 変える（再開を引数の語で見分けず、state.md の Started At 以前で最後の起動を steering を作った起動とする）。hook と gdd-dev の再開の判定が一致せず、「続きから」や引数なしの再開を新規として扱う。commit: 122d46e5 |
| r5-2 | 独立-5 | medium | no | self-inflicted | request-drift | fixed | 設計: 変える（同上）。同じ transcript で再開したとき、元の依頼が範囲内にあるのに節を作らない（依頼の範囲を確認なしに外す）。commit: 122d46e5 |
| r5-3 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | human-check-template.md:49 の原文の引き方が、節の下に足した発言を含まない（他の 2 か所と食い違う） |
| r5-4 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が、移す中身を runner の写しとしか書かない。commit: 122d46e5 |
| r5-5 | 独立-5 | low | no | self-inflicted | test-power | fixed | 再開の語の判定の変異をテストが落とさない（語の判定をやめたので消えた）。commit: 122d46e5 |
| r5-6 | 独立-5 | low | no | self-inflicted | bookkeeping | fixed | 新しい分岐の当たる件数を書いていない（Started At の設計で測り直し、notes に書いた）。commit: なし（PR 本文） |
| r5-7 | 独立-5 | low | no | self-inflicted | request-drift | accepted | 確認済み（2026-11-01 ユーザーが推奨で OK）: 写す時機を突き合わせの起動に替えたことをユーザーに確かめていない（r2-5 と同じ問い） |
| r5-8 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | README.md:543 が節の下に写すことと移すことを書いていない |
| r5-9 | 独立-5 | advisory | no | self-inflicted | product | accepted | Skill の名前の取り出しが main_model_gate と違う（name キー・空白） |
| r5-10 | 独立-5 | advisory | no | self-inflicted | product | accepted | 型の違う record が 1 行あると写す処理全体が止まる |
| r5-11 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の 13 session・節の大きさの数え方が notes に無い |
| r6-1 | 独立-6 | medium | no | self-inflicted | product | fixed | 設計: 変える（state.md に Created In Session を足し、payload の session_id と一致するときだけ写す。ユーザーが 10-31 に直すと決めた）。commit: b5b7b860。列挙: Started At 以前で最後の起動が、本当にこの steering を作った起動かを確かめない。別の session で作ったタスクを、前に別タスクの起動がある session で再開すると、別タスクの依頼が原文になる（文書の「何もしない」が成り立たない） |
| r6-2 | 独立-6 | medium | no | self-inflicted | test-power | accepted | 人の発言が無いときに節を作らない分岐を通るテストが無くなった（Skill の起動だけの形） |
| r6-3 | 独立-6 | low | no | self-inflicted | product | accepted | Started At は LLM が書く値で、実時刻との差（丸め・時差の書き違い）で選ぶ起動がずれる |
| r6-4 | 独立-6 | low | no | self-inflicted | product | fixed | Started At の読み方が state_fields の canonical reader と受け付ける形が違う（backtick・fence・字下げ） |
| r6-5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 時刻の読めない起動は飛ばして前の起動を選ぶのに、文書は「読めないと何もしない」と書く |
| r6-6 | 独立-6 | low | no | self-inflicted | test-power | accepted | 同じ transcript の再開のテストが、範囲の終わりが作った起動であることを固定しない |
| r6-7 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の「読めないと写さない」に Started At と作った起動の条件が無い |
| r6-8 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | PR 本文の節の大きさ（35 session）が今の選び方で測った値ではない |
| r6-9 | 独立-6 | low | no | self-inflicted | request-drift | accepted | 確認済み（2026-11-01 ユーザーが推奨で OK）: 写す時機を突き合わせの起動に替えたこと（r2-5 と同じ問い） |
| m2-1 | 方針メモ-2 | advisory | no | self-inflicted | product | fixed | ユーザーが「取り違えは直す」と決めた（依頼の「新しい記録の仕組みは足しません」とぶつかることを示したうえで）。相談役 2 本とも案 A（state.md に Created In Session を runner が書き、hook が payload の session_id と照合。必須にせず block guard は触らない。欄が無い・違うときは写さない）。subagent の Bash の CLAUDE_CODE_SESSION_ID が main と同じことを実測した。既存の Origin Session・runtime_session_id は意味が違うので使わない |
| r7-1 | 独立-7 | medium | no | self-inflicted | request-drift | fixed | 設計: 変える（写さなかったときは request.md の先頭に理由の節を別の marker で入れ、systemMessage でも出す。後で写せたら消す）。commit: 8fc6fc1c。列挙: 照合の値を LLM の runner が書くので、書き漏れると何も知らせずに写さず、runner の写しが原文として読まれる |
| r7-2 | 独立-7 | low | no | self-inflicted | product | accepted | Claude Code から開いた Codex・Cursor は CLAUDE_CODE_SESSION_ID を継ぐので、親の session で再開すると照合が通り、取り違えが残りうる（文書は「取れない」と書く） |
| r7-3 | 独立-7 | low | no | self-inflicted | bookkeeping | accepted | 照合で止める取り違えの件数と、写さなくなる件数が PR 本文に無い（未測の記載も無い） |
| r7-4 | 独立-7 | low | no | self-inflicted | doc-claim | fixed | module の docstring に「新しい記録の仕組みは足さない」が残る。commit: 8fc6fc1c |
| r7-5 | 独立-7 | low | no | self-inflicted | test-power | fixed | payload の session_id が空・欠落のときに写さない分岐を通るテストが無い。commit: 6d00f36e |
| r7-6 | 独立-7 | advisory | no | self-inflicted | product | accepted | runner の Bash の env と hook の payload が同じになる根拠（subagent・/clear・--resume の後）を示していない |
| r7-7 | 独立-7 | advisory | no | self-inflicted | product | accepted | Started At の後ろに文が続く行は、canonical reader では読めず写さない（実データの件数は未確認） |
| r7-8 | 独立-7 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Validation に、雛形を読む test_express_planning_review.py が無い |
| m3-1 | 方針メモ-3 | advisory | no | self-inflicted | product | fixed | r7-1 の閉じ方を相談役 2 本に聞き、2 本とも案 D（写さなかった理由の節を request.md の先頭に入れ、systemMessage でも出す）。10 月の 62 steering で state.md を最初に書いたのは Write 24・Edit 24・Bash 10・見つからない 4 で、hook が作成時に欄を書く案は作成を全部は捉えないので採らない。ユーザーの承認（作った session を記録して照合する）の範囲内なので確認は出さない。commit: 8fc6fc1c |
| r8-1 | 独立-8 | medium | no | self-inflicted | product | fixed | 設計: 変える（再設計: request.md は hook だけが作る。写せないときの request.md の下に runner の写しが無い）。commit: 028f3864。写さなかった理由の節がある状態の読み方が、突き合わせ agent・完了前の reviewer・human check に無く、runner の写しが今までどおり原文として読まれる |
| r8-2 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 設計: 変える（再設計で 9 (1) を書き直した）。commit: 028f3864。brainstorming-steps.md 9 (1) で、理由の節の規定の次の「hook の節が無いときは runner の行を原文として読む」が食い違う |
| r8-3 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 設計: 変える（再設計で条件を文書にそろえた）。commit: 028f3864。理由の節を入れる条件が、コード（5 つ）と SECURITY.md・hooks.json・断片・docstring で合わない |
| r8-4 | 独立-8 | low | no | self-inflicted | test-power | fixed | 設計: 変えない（fixture の漏れ）。commit: 21a01f13。session_id 空・欠落と Started At が読めないテストの fixture に Created In Session が無く、狙った分岐に届かない |
| r8-5 | 独立-8 | low | no | self-inflicted | test-power | fixed | 設計: 変えない（assert の不足）。commit: 21a01f13。理由の節を先頭に入れることと、写せたときに何も出さないことをテストが固定しない |
| r8-6 | 独立-8 | low | no | self-inflicted | style | fixed | 設計: 変えない（名前の追随漏れ）。commit: 21a01f13。テスト名 ..._leaves_request_md_unchanged が、節を入れる今の挙動と逆 |
| r8-7 | 独立-8 | low | no | self-inflicted | product | fixed | 設計: 変える（再設計: 例外では request.md を作らず、requirements-gating の前提で止まる）。commit: 028f3864。例外・タイムアウトで落ちると、理由の節も systemMessage も出ず、runner の写しが印なしで読まれる |
| r8-8 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 設計: 変える（再設計: 写していない旨の request.md の下は main が足した発言だけ）。commit: 028f3864。理由の節の「この下は runner の写し」が、main が足した本物の発言まで原文ではないと言う |
| r8-9 | 独立-8 | low | yes | self-inflicted | data-loss | fixed | 再設計: 設計: 変える（hook が書くのは、まだ無い request.md を link で作るときだけ。既にある中身を消す・動かす・見分けるコードを消した）。commit: 028f3864。理由の節を消す正規表現がファイル全体に掛かり、runner の写しに 2 つの marker が入るとその間の文を消す |
| m4-1 | 方針メモ-4 | advisory | no | self-inflicted | product | fixed | 再設計: 安全策 4 の条件（high か blocking を含む巡が 独立-1・3・4・8）に当たった。これまでの high・blocking（r1-8・r1-9・r3-1・r4-1・r8-9）はどれも「runner・main・人が書いた request.md に hook が後から手を入れる」決定から出ていた。相談役 2 本とも、Claude Code では hook だけが request.md を新しく作り、既にあれば触らない案（runner の写しは request-notes.md）。割れたのは写せなかったときで、1 本は何も作らない、1 本は写していない旨だけの request.md を hook が作る。後者を採った（理由つきのファイルを LLM の手順なしに作れる。hook が落ちたときはどちらもファイルが無く止まる側）。commit: 028f3864 |
| r9-1 | 独立-9 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（写していない旨の request.md を「依頼の原文なし」の宣言した状態にし、突き合わせ agent・human check・完了前の reviewer・PR 前の 3a が止める側に倒す）。commit: 7a92ae3a。写していない旨の request.md を読む側に規定が無く、Request Drift が比べる原文の無いまま通る |
| r9-2 | 独立-9 | medium | no | self-inflicted | doc-claim | fixed | 設計: 変えない（r9-1 と同じ文を書き換えるので一緒に直した）。commit: 7a92ae3a。hook が書かなかったとき「要件の gate で止まる」「作るのは hook だけ」と書くが、runner が作るので止まらず、突き合わせを unavailable にする規定も無い |
| r9-3 | 独立-9 | medium | no | self-inflicted | request-drift | fixed | 設計: 変えない（runner の条件を env の有無にし、hook は Created In Session の無い既存の request.md を systemMessage で知らせる）。commit: 7a92ae3a。runner が Created In Session を書き漏らすと、runner の写し（main の要約）が何も知らせずに原文になる |
| r9-4 | 独立-9 | medium | no | self-inflicted | request-drift | fixed | 設計: 変えない（起動の後の発言を、写していない旨の下に写す）。commit: 7a92ae3a。起動より前に人の発言が無いと、起動の後のユーザーの発言も捨てる |
| r9-5 | 独立-9 | low | no | self-inflicted | test-power | accepted | 例外のテストが mkstemp より前で落ち、一時ファイルの後片付けと link の失敗を通らない |
| r9-6 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md・hooks.json の「写せないときに作る」条件が、例外で何も作らない場合と分かれていない |
| r9-7 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | gdd-brainstorming SKILL.md:185 が「request.md と request-crosscheck.md を作る」のまま |
| r9-8 | 独立-9 | low | no | inherited | request-drift | re-reported | 確認済み（2026-11-01 ユーザーが推奨で OK）: 写す時機を突き合わせの起動に替えたこと（r2-5・r6-9 と同じ問い） |
| r9-9 | 独立-9 | low | no | self-inflicted | product | accepted | hard link を作れないファイルシステムでは os.link が毎回失敗し、何も作らず知らせもしない |
| r9-10 | 独立-9 | advisory | no | self-inflicted | product | accepted | timeout で kill されると .tmp- の一時ファイルが残りうる |
| r9-11 | 独立-9 | advisory | no | self-inflicted | test-power | accepted | test_existing_request_md_is_never_read_or_rewritten の「never read」をテストで確かめていない |
| r10-1 | 独立-10 | medium | yes | self-inflicted | approval-path | fixed | 再設計: 設計: 変える（原文が無いことの扱いを読み手の LLM の解消条件から risk_tier の機械の判定に移し、完了前の reviewer の「下に発言が無ければ High」を消した）。commit: 804b1e9a。写していない旨の request.md の「依頼の原文なし」の High の解消条件「下にユーザーの発言がある」が、hook が下に写した起動の後の発言や、その行を示していない human check への返事で満たされる |
| r10-2 | 独立-10 | medium | no | self-inflicted | product | fixed | 設計: 変える（risk_tier が Created In Session のある steering で hook の節で始まらない request.md を原文なしとして高にする）。commit: 804b1e9a。runner が規則に反して request.md を書いた形（Created In Session あり）は何も出ず、読み手が runner の行を原文として読む |
| r10-3 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 理由の「（起動の後の発言は下に写した）」が、下に何も無くても付く |
| r10-4 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 既にある request.md の通知の「runner が作ったもの」は確かめられず、hooks.json に session_id の条件が無い |
| r10-5 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 文書は、写していないすべての理由で起動の後の発言を下に写すと読めるが、コードは起動より前の発言が無いときだけ写す |
| r10-6 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 「依頼の原文: なし」の行が、§ ズレ確認 の定義と compact テンプレートに無い |
| r10-7 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | hook が request.md を作らなかったときの unavailable の経路に、human check の「既存とぶつかる」に載せる文が無い |
| r10-8 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の理由の一覧に「起動より前に写す発言が無い」が無く、JSON でない payload が request.md を作る側に並ぶ |
| r10-9 | 独立-10 | low | no | self-inflicted | product | fixed | 設計: 変える（risk_tier が request.md を読む）。commit: 804b1e9a。「依頼の原文なし → 高」が agent の指示だけで決まり、risk_tier の guard は request.md を読まない |
| r10-10 | 独立-10 | low | no | inherited | request-drift | re-reported | 写す時機を突き合わせの起動に替えたこと（2026-11-01 にユーザーが推奨で OK と決めた） |
| r10-11 | 独立-10 | advisory | no | self-inflicted | doc-claim | accepted | state-field-tiers.md・state-machine.md の Created In Session の読み手に、新しい使い方が無い |
| r10-12 | 独立-10 | advisory | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が「なし」なのに、開き直すまで写らないと書く |
| r11-1 | 独立-11 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（2026-11-01 にユーザーが A を選んだ。原文は通常のファイルで hook の節で始まる request.md だけにし、state.md の欄では決めない）。commit: 2beb8aa8。Created In Session が無いと _has_original_request が原文ありに倒れ、runner の書き漏らしや欄の削除で main の要約が原文として通る（hook とは判定が割れる） |
| r11-2 | 独立-11 | medium | no | self-inflicted | doc-claim | accepted | gdd-pr-review の 3a が、写していない旨の request.md を今も High として扱い、完了前の reviewer の 9 と食い違う |
| r11-3 | 独立-11 | medium | no | self-inflicted | product | accepted | risk_tier が原文なしとする形（欄あり・hook の節で始まらない）を、LLM 側の読み手は原文として読み、hook も欄がある場合は通知しない |
| r11-4 | 独立-11 | medium | no | self-inflicted | product | accepted | 完了前の reviewer から外した High の代わりの human check での確認が、compact の一次表示と事前回答の経路では届かない |
| r11-5 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | state-field-tiers.md・state-machine.md の Created In Session の読み手に、risk_tier の新しい使い方が無い |
| r11-6 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | gate-status-schema.md:42 の記述が新しい扱いと合わない |
| r11-7 | 独立-11 | low | no | inherited | doc-claim | accepted | 突き合わせ agent の 43 行目の risk-low の記述（既存） |
| r11-8 | 独立-11 | low | no | self-inflicted | test-power | accepted | request.md がディレクトリのときのテストが無い |
| r11-9 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | 新しい block の条件の件数か未測が PR 本文に無い |
| r11-10 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | 断片の文言 |
| r11-11 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | UNPROJECTABLE_REASON の文言 |
| r12-1 | 独立-12 | low | no | self-inflicted | approval-path | accepted | 突き合わせ agent は印の無い request.md を原文として段を低と記録しうるので、human check に見える段と guard の段（高）が食い違う |
| r12-2 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | UNPROJECTABLE_REASON が、依頼の原文が無いことで段が高になる場合を書いていない |
| r12-3 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | 文書が「hook が作った request.md」と言い切るが、実装は先頭の印だけを見て作り手を確かめない |
| r12-4 | 独立-12 | low | no | inherited | test-power | accepted | risk_tier の CAPTURE_BEGIN と request_capture の BEGIN の一致を確かめるテストが無い |
| r12-5 | 独立-12 | low | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files に、書き換えた既存テスト 3 本が無い |
| r12-6 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | 断片に、Codex・Cursor・既存の steering で state.md の一部の Edit が止まる影響と User Action Required が無い |
| r12-7 | 独立-12 | advisory | no | inherited | product | accepted | steering のディレクトリが symlink のとき、hook は作らないが読み手は原文に数える |
| r12-8 | 独立-12 | advisory | no | self-inflicted | doc-claim | accepted | 誤 block の件数を未測としたが、どの入力が記録に無いかを書いていない（測れる見込みがある） |
| r12-9 | 独立-12 | advisory | no | inherited | product | accepted | 原文かどうかを先頭の印だけで決め、作り手を確かめない（risk-low を使う手順を入れる前に決める） |
| r13-1 | 独立-13 | medium | no | self-inflicted | doc-claim | accepted | 写していない旨の request.md で、起動の後の発言を下に写すのは起動より前の発言が無いときだけで、5 つの文書の「写す」と合わない |
| r13-2 | 独立-13 | low | no | self-inflicted | request-drift | accepted | 確認済み（2026-11-01 ユーザーが形式でよいと決めた）: 案 A の「hook が書いた節で始まる request.md」を、実装は先頭の印だけで判定し作り手を確かめない（形式とも作り手とも読める） |
| r13-3 | 独立-13 | low | no | self-inflicted | product | accepted | 起動の選び方が runner の書く Started At の正確さに頼り、時計から取る指示が無い |
| r13-4 | 独立-13 | low | no | self-inflicted | product | accepted | 写す範囲の始まりを transcript 全体の最後の done から取るので、作った起動より後の done で起動を見失う |
| r13-5 | 独立-13 | low | no | self-inflicted | product | accepted | 人の発言の判定に、transcript.py が除く hook の注入の接頭辞の除外が無い |
| r13-6 | 独立-13 | low | no | self-inflicted | product | accepted | 完了前の reviewer の起動元が request-notes.md を渡さない |
| r13-7 | 独立-13 | low | no | self-inflicted | doc-claim | accepted | compact の human check テンプレートに「依頼の原文: なし」の行が無い |
| r13-8 | 独立-13 | low | no | self-inflicted | doc-claim | re-reported | UNPROJECTABLE_REASON と表示の段が依頼の原文の条件を反映していない（r12-2・r12-1 と同じ） |
| r13-9 | 独立-13 | low | no | self-inflicted | bookkeeping | re-reported | 変更断片の Affected Files・Changed が差分と合わない（r12-5・r12-6 と同じ） |
| r13-10 | 独立-13 | low | no | self-inflicted | product | accepted | Claude Code かどうかを環境変数だけで決め、Claude Code から開いた Cursor を取り違える |
| r13-11 | 独立-13 | low | no | self-inflicted | test-power | accepted | resume のテストが、最後の起動まで写す退行を検出しない |
| r13-12 | 独立-13 | low | no | inherited | doc-claim | accepted | README の matcher の数が hooks.json と合わない |
| r13-13 | 独立-13 | advisory | no | self-inflicted | test-power | accepted | Skill の起動の transcript の行の形を実データで確かめていない |
| r13-14 | 独立-13 | advisory | no | self-inflicted | product | accepted | lone surrogate があると request.md を作れない（止める側に倒れる） |
| r13-15 | 独立-13 | advisory | no | self-inflicted | doc-claim | accepted | SECURITY.md の列挙に、例外の経路が写していない旨の側に混ざっている |
| r13-16 | 独立-13 | advisory | no | self-inflicted | bookkeeping | accepted | 追加が約 1,004 行で +1,000 行を少し超えた（分割の相談の記録が無い） |
| m5-1 | 方針メモ-5 | advisory | no | self-inflicted | product | fixed | 再設計: 再設計の後の 2 巡（独立-9・10）で high・blocking が残った。穴を生んだ決定は、原文があるかと原文なしが解けたかを、3 者が書く request.md の印から読み手の LLM 4 か所が決めていたこと。相談役 2 本とも、risk_tier が原文の無い steering を高にし（人の承認を必須にする）、解ける High を確認の歯止めに使わない案。割れたのは runner が書いた request.md の扱いで、1 本は risk_tier の判定（Created In Session があるのに hook の節で始まらなければ原文なし）、1 本は hook が突き合わせの起動を止める（deny）。前者を採った（指摘を直すための deny の分岐は、当たる件数を先に測る規定で、この状態は記録に無く測れない。risk_tier だけで同じ形を高に倒せる）。commit: 804b1e9a |
