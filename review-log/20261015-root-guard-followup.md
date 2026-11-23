---
lane: L1
follow_up_of: 505
amends: 20261014-root-branch-guard-session.md
pr: 517
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0003c887 | 1 | 3 | 1 | 2026-10-15 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 0003c887 | 0 | 0 | 0 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 277bf169 | 0 | 3 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | yes | inherited | fail-open | accepted | 列挙: bash 側の block gate（pre-push・pre-PR・plan mode・enter worktree・skill・dispatch など 10 の hook）が、通常のファイルでない・読めない state を [[ -f ]] で inactive と読んで通す。依頼の行から外れたまま。方針メモ-1 で (b) |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | deny の文の抜け方が、setup のロックの文と違い、先にユーザーに聞かずに active: false にさせる commit: eed5e48e |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 読めない state の抜け方（通常のファイルに戻す・権限を直す）が deny の文に無い commit: eed5e48e |
| I1-4 | 独立-1 | medium | no | inherited | product | accepted | 推奨で決定（2026-10-15 ユーザー「進めて」）: 検索権の無い .claude/ の下で state が無くても止める。r があれば os.listdir で無いことを確かめられる（緩める変更で、止める・通すの判定が変わる） |
| I1-5 | 独立-1 | low | no | inherited | product | fixed | 関数名 active_gdd_state_exists を変えずに限界に回した。root_state_blocks に改めた commit: 9b5aead8 |
| I1-6 | 独立-1 | low | no | inherited | parse-symmetry | accepted | 推奨で決定（2026-10-15 ユーザー「進めて」）: session_id を読む実装ごとに受け入れる形が違う（guard の側が厳しく bypass は無い） |
| I1-7 | 独立-1 | low | no | inherited | product | fixed | 誤 block 21 件のうち何件が通るかが無い。PR 本文に、環境変数と payload の id の一致の実測と、当時の state の持ち主が記録に残らず未測であることを書いた commit: なし（PR 本文） |
| I1-8 | 独立-1 | low | no | inherited | product | fixed | 件数を数えた方法が無い。PR 本文に数え方を書いた commit: なし（PR 本文） |
| I1-9 | 独立-1 | low | no | inherited | product | accepted | 推奨で決定（2026-10-15 ユーザー「進めて」）: regular_file.py の import に失敗すると git を含む全コマンドを止める（分けるとブランチ作成だけを止められるが、止める・通すの判定が変わる） |
| I1-10 | 独立-1 | low | no | self-inflicted | product | fixed | deny の文がどの理由で止めたかを示さない。戻り値は変えず、確かめ方（state の先頭の行を読む）と GDD 名のブランチは state によらず止めることを文に足した commit: eed5e48e |
| I1-11 | 独立-1 | low | no | self-inflicted | product | fixed | 文に並べた理由に、frontmatter の区切りが無いとき・payload の id の形が外れるときが無い commit: eed5e48e |
| I1-12 | 独立-1 | low | no | self-inflicted | test-power | fixed | 文のテストが理由の語・聞く順・読めない state を見ない commit: eed5e48e |
| I1-13 | 独立-1 | low | no | inherited | docs | fixed | session_owner のテストの冒頭が、読めない state を止めることと抜け方を書かない commit: eed5e48e |
| I1-14 | 独立-1 | low | no | self-inflicted | docs | fixed | fail_closed のテストの冒頭と docstring が regular_file.py の欠落を書かない commit: eed5e48e |
| I1-15 | 独立-1 | low | no | self-inflicted | changelog | fixed | 断片の User Action が、読めない state は中身によらず止まること・state が無くても止まる場合を伝えない commit: 9b5aead8 |
| I1-16 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の抜粋に review-log の amends: への言及がある（テンプレート外の記述あり）。抜粋から除いた commit: なし（PR 本文） |
| I1-17 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の書き換えに対になる review-log の amends: が無い commit: 05c9c8ab |
| I1-18 | 独立-1 | advisory | no | self-inflicted | product | accepted | deny の文が、どの root の state かを絶対パスで示さない |
| M1-1 | 方針メモ-1 | advisory | no | inherited | design | accepted | 列挙: I1-1 は (b)。入力者の実測: 全 project の transcript（subagent を含む 26,726 本）の Bash で、gdd-dev.local.md か .claude を対象にした chmod・mkfifo・ln -s・mkdir は 5 件で、どれも mktemp の一時 repo か scratchpad の確かめ（実際の作業の事故は 0 件）。旧#505 の時点の state も 0 件。Opus は (b) を推し、別の L1+ の PR は既定では提案しない（直すと 10 hook に「分からなければ止める」分岐が増え、全レーン共通の新しい発火条件の規定で、当たる件数 0 なら足さない側）。Fable も (b) で、別の PR は提案として書くと推した。依頼の原文の行（high は確認待ちにせず直す）と列挙の行（方針メモで決める）の優先順は規則に無く、ここでは列挙の行に従った。I1-4・I1-6・I1-9 は 2 本とも限界のまま確かめる、I1-10 は 2 本とも直す（Opus は文だけ、Fable は戻り値を理由にする形。文だけで直した） |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | re-reported | I1-4 の再報告（検索権の無い .claude/ の下で state が無くても止める。依頼 74 行） |
| I2-2 | 独立-2 | medium | no | self-inflicted | parse-symmetry | accepted | 推奨で決定（2026-10-15 ユーザー「進めて」）: 依頼 66 行（session_id を読む setup のロック・gdd_session_continuity_ok・guard の 3 実装で受け入れる形が違う）を差分も PR 本文も扱っていない。そろえると 13 本の hook の block/allow が変わる |
| I2-3 | 独立-2 | medium | no | self-inflicted | fail-open | accepted | 推奨で決定（2026-10-15 ユーザー「進めて」）: 依頼 67 行（bash 側の [[ -f ]] が、読めない state を inactive と読む）が PR 本文の抜粋に出てこない。中身は I1-1 と同じで、ユーザーへの確認はこれが初めて |
| I2-4 | 独立-2 | medium | no | self-inflicted | product | fixed | 依頼 64 行: 46 件・21 件を数えたコマンドが無い。PR 本文に抜き出しと重複除去、GDD を始めていないことの判定の仕方を書いた commit: なし（PR 本文） |
| I2-5 | 独立-2 | low | no | self-inflicted | product | fixed | 依頼 68 行: 21 件のうち通るようになる件数を確認なしに未測とした。setup が session_id を書くのは 2026-08-15 の最初の版からなので、手で書き換えた state を除いて上限 21 と PR 本文に書いた commit: なし（PR 本文） |
| I2-6 | 独立-2 | low | no | self-inflicted | product | accepted | deny の文の確かめ方（state の先頭の行を読む）では、payload 側の理由と例外の経路を見分けられない |
| I2-7 | 独立-2 | low | no | self-inflicted | product | accepted | state が今の session のものでも、抜け方の問いが「書いた session がまだ動いているか」で、答えが常に yes になる |
| I2-8 | 独立-2 | low | no | self-inflicted | parse-symmetry | accepted | guard は active: true を本文も含めた部分一致で読むので、依頼の文に active: true があると frontmatter を false にしても止まり続ける |
| I2-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | session_owner のテストの冒頭の「前は通していた」が、Python の版に限った話であることを書かない |
| I2-10 | 独立-2 | low | no | inherited | doc-claim | accepted | root_state_blocks の docstring が、検索権の無い .claude/ の下では state が無くても止めることを書かない |
| I2-11 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の実測の記述にコマンドと出力の形が無い。PR 本文に書いた commit: なし（PR 本文） |
| I2-12 | 独立-2 | advisory | no | self-inflicted | changelog | accepted | 断片の Summary に内部の関数名の変更を書いている |
| I2-13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Affected Files と PR 本文が、コメントを変えた test_root_branch_name_candidates.py を挙げない |
| I2-14 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | deny の文が理由によらず同じなので、chmod 0 のテストが読めない state の経路に結びつかない |
| I2-15 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | block gate の判定の行（main の呼び出し）を改名で書き換えたので、迷ったら L1+ に当たる |
