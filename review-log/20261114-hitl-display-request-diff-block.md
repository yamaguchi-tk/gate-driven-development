---
lane: L1+
pr: 674
follow_up_of: 669
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 8ad28df2b849b02ccf1d7e106bb291f846df37b4 | 0 | 0 | 0 | 2026-11-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | de2810bf73f232f333636c2e3b1078dfb097c655 | 0 | 2 | 0 | 2026-11-14 |
| 方針メモ-2 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 2563ae2a | 0 | 0 | 0 | 2026-11-14 |
| 方針メモ-3 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | 72d91d7abc0b766c4297bd5685464b9fd49f0e8a | 0 | 0 | 0 | 2026-11-14 |
| 独立-2 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | d47a5a2e5fe3f5552f7c8a50c5afec04f4578906 | 0 | 2 | 0 | 2026-11-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 6ce1c9161703ba6e19f9f9a921fe79e76144938e | 0 | 1 | 0 | 2026-11-14 |
| 方針メモ-4 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 7f1d86eb2c9549d439a3fc3f6c3905fd2caba379 | 0 | 0 | 0 | 2026-11-15 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | fd9eb8e2a75f7fca9034d7126fe5ad5dfa666c8d | 3 | 2 | 2 | 2026-11-15 |
| 方針メモ-5 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 2badcc04b0b129bff0e6054b544169ee5fcd8a32 | 0 | 0 | 0 | 2026-11-15 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 8817dfd115799cb62518d2909732217a97729f5b | 1 | 3 | 1 | 2026-11-15 |
| 方針メモ-6 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | c7a982721ed0899b99c175c7b7f7fa3d2b4eb467 | 0 | 0 | 0 | 2026-11-15 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分, model: fable | c7a982721ed0899b99c175c7b7f7fa3d2b4eb467 | 0 | 3 | 0 | 2026-11-15 |
| 方針メモ-7 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | a118988ace989ac991d394818dc9776f6e7e94dd | 0 | 0 | 0 | 2026-11-15 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分, model: fable | a118988ace989ac991d394818dc9776f6e7e94dd | 1 | 2 | 1 | 2026-11-15 |
| 方針メモ-8 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | e1537d7dabc5f929e7741242ba1cec3cc5b2cae6 | 0 | 0 | 0 | 2026-11-15 |
| 独立-8 | light-lane-independent-reviewer-xhigh, 差分, model: fable | e1537d7dabc5f929e7741242ba1cec3cc5b2cae6 | 0 | 1 | 0 | 2026-11-15 |
| 独立-9 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | e4877f8e3ee0a3a27d08e952cbd7d9e5ffa6351d | 1 | 3 | 1 | 2026-11-15 |
| 方針メモ-9 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 205836868b188428000f71d74b4d7bc0836a5018 | 0 | 0 | 0 | 2026-11-15 |
| 独立-10 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | af1b776272656945e84cb2f0296a79bef526a524 | 1 | 2 | 1 | 2026-11-15 |
| 独立-11 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 2a1f22e82c2fe8e3c5ce234d8474b100d831dc2b | 1 | 1 | 1 | 2026-11-16 |
| 独立-12 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | aee8f0740fc460e094ac4a0d3c536bdec4209361 | 0 | 0 | 0 | 2026-11-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | low | no | self-inflicted | design | accepted | 2 本とも、Stop hook で承認の hook と同じ field_problem の書式の 3 値だけを、人のターンごとに 1 回押し返し、新しい lib に置き、直し方の文を共有する案で一致。main の草案（提示の sha ごとに 1 回）は書き直すたびに sha が変わり上限にならないので改めた。割れたのは締め切り（Opus-1 は run_within_deadline、Opus-2 は不要）と「なし以外を止めない」を問うか。純関数で key を引数で渡すので締め切りは使わず、なし以外は PR 本文に根拠つきで書く |
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 「なし以外の点がある」を押し返さず、依頼の行（lint を止める側に）より狭い。ユーザーが「この PR で直す」と答えたので、なし以外も押し返す。旧#672 の hook にまとめ直した（ユーザーの「A で作り直す」）。commit: 7428abb2 |
| I1-2 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 押し返しを人のターンごとに 1 回に限っていた。旧#672 の hook の上限を 3 回にした。commit: 7428abb2 |
| I1-3 | 独立-1 | low | no | self-inflicted | pushback-count | accepted | 列挙: 人のターンの key では、相談役の後の出し直しと、同じ worktree の 2 セッションの交互の停止を見逃す・上書きする |
| I1-4 | 独立-1 | medium | no | self-inflicted | test-isolation | fixed | テストが本物の request-diff-approval.log に display-block を書く（GDD_HOOK_STATE_DIR を差し替えていない）。テストの記録を一時ディレクトリに書かせた。後の作り直しで、このテストごと撤去した（旧#672 の hook のテストは記録を一時ディレクトリに書く）。commit: 65bbf64b |
| I1-5 | 独立-1 | low | no | self-inflicted | observability | accepted | display-block に session_id が無く、判定の例外を hook-errors.log に残さない |
| I1-6 | 独立-1 | low | no | self-inflicted | input-symmetry | accepted | 押し返しは最後の text block を読み、承認の hook はマーカーを含む record の text block の連結を読む（PR 本文の限界に開示） |
| I1-7 | 独立-1 | low | no | self-inflicted | input-symmetry | accepted | 押し返す問題を返り値の許可リストで決めるので、field_problem に新しい書式の問題が足されると黙って見逃す |
| I1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | 同じ集合のテストの期待値が実装の定数を使う、本文を直に渡す、display-block の記録と origin の無い key を確かめていない |
| I1-9 | 独立-1 | low | no | self-inflicted | fail-open | accepted | key を書いた後で sha の計算が例外を出すと、そのターンの押し返しを使い切る。tmp の書き込みの ValueError を捕まえない |
| I1-10 | 独立-1 | low | no | self-inflicted | cost | accepted | 押し返される不良の版にも request-diff の checker が走る |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | references/autonomy.md:18 が、Stop hook の human check の押し返しを事前回答のときだけと書いたまま |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しい sidecar が PROJECT_CLAUDE_MD_TEMPLATE.md の .gitignore の案内と断片の User Action Required に無い |
| I1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | lint-hitl-decision-fields.py と hitl_lint_gate.py の docstring が新しい経路を指していない |
| I1-14 | 独立-1 | advisory | no | self-inflicted | request-scope | fixed | 依頼が名指しした lint ではなく、同じ判定を Stop hook の中で直に当てた。PR 本文に 1 文書いた。commit: なし（PR 本文） |
| I1-15 | 独立-1 | advisory | no | inherited | doc-claim | accepted | human-check-template.md:558 の 0 件の確認の説明が 旧#664 の後の判定（タグ）と合わない |
| I1-16 | 独立-1 | advisory | no | self-inflicted | operability | accepted | 押し返しだけを切る手段が無い（GDD_SKIP_HITL_LINT では切れない） |
| I1-17 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 旧#664 の後の表示の件数は測れる。測って 0 件だったので PR 本文に書いた。commit: なし（PR 本文） |
| M2-1 | 方針メモ-2 | low | no | self-inflicted | design | accepted | 2 本とも、なし以外を素通しする案と、hook が人の返事の文を読む案を退けた。割れたのは直し方: Opus-1 は表示の時点でなし以外も押し返し、狭める案を採用しない案として名指しで選ばせる（承認の hook はそのまま）。Opus-2 は承認の書き込みに点ごとの決定と人の発言の引用を宣言させて照合する。main は欄を増やさず既存の規則（狭い推奨を既定にしない）に沿う Opus-1 を採った。両者が足した「提示の後に人の発言があること」の検査は、allow 35 件中 0 件（全件で提示の後に人の発言があった）なので足さない |
| M3-1 | 方針メモ-3 | low | no | self-inflicted | design | accepted | main に入った 旧#672 が、書式の崩れの押し返しを別の Stop hook（lib/request_diff.py）に入れていた。2 本とも、旧#674 の押し返しを撤去して 旧#672 の hook の判定を field_problem に広げ、なし以外の文を分け、上限を 3 にし、`あり:` を案内する文書をそろえる案（A）で一致。ユーザーが「A で作り直す」と答えた。表示の前の lint も同じ入力を読むので、同じ判定にそろえた |
| I2-1 | 独立-2 | medium | no | self-inflicted | rule-consistency | accepted | 「狭める案を採用しない案に並べる」が § 止まり直さないもの 1（退けた案を採用しない案に並べて判断ポイントを作らない）と食い違い、main が狭める案を消すか判断ポイントを作るかが文書で決まらない（brainstorming-steps.md:80 の写しも） |
| I2-2 | 独立-2 | medium | no | self-inflicted | rule-consistency | accepted | 名指しの後の request.md・requirements-gating 1 Round の手順が gdd-dev.md #10 STEP 1 の経路に無く、approved を書く時機が決まっていない。gdd-dev.md:189 の例外は express の範囲・Files・Implementation Policy の変更も承認に入れる形に広がっている |
| I2-3 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 決定（ユーザー「上限の後も直す」）: 上限 3 回の後は、不良の確認が人に届き、承認の書き込みで拒否されて答え直す経路 2 が残る。ユーザーが選んだ案 A（上限 3）に含まれると読んだが、結ぶ発言が無いので PR 本文の限界で問う |
| I2-4 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 承認の書き込みの拒否の文（DENY_MESSAGE）に `あり: <その項目>` を書けという案内が残り、出し直しの文と逆を指す。案 A の「`あり:` を案内する箇所をそろえる」に合わせて文だけ直した。commit: ace5d21c |
| I2-5 | 独立-2 | low | no | self-inflicted | message | accepted | 形の崩れとなし以外が両方ある確認では形の文だけが出て、タグに `differs` を書いてよいと読める |
| I2-6 | 独立-2 | low | no | self-inflicted | test-power | accepted | 形の崩れの文から `あり:` の案内を外したことを固定するテストが無い |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | hooks.json の description が block の条件を形の崩れだけ、上限を 2 回と書いたまま |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | request_diff_field.py の docstring と run-request-diff-hook.sh のコメントが、format_problem を Stop と lint が使う形のまま |
| I2-9 | 独立-2 | low | no | self-inflicted | observability | accepted | not_run の値を改名したことが PR 本文・断片に無い（blocked・field_problem の列で数えれば分かれない）。偽の `なし` の数え方が読む時期の計画に無い |
| I2-10 | 独立-2 | advisory | no | self-inflicted | style | accepted | 「なし以外の点がある」の文字列を 2 ファイルに書いている |
| I2-11 | 独立-2 | advisory | no | self-inflicted | product | accepted | `あり:` の確認のたびに記録だけの lint の不通過が hook-errors.log に増える |
| I2-12 | 独立-2 | advisory | no | inherited | doc-claim | accepted | test_lint_hitl_decision_fields.py の docstring が、lint の呼び先を request_diff_approval.py と書いている |
| I3-1 | 独立-3 | medium | no | self-inflicted | request-scope | fixed | 上限の後と、Stop の hook が動かないときは、経路 2 だけでなく経路 1 も残るのに、PR 本文の限界は経路 2 だけを書いていた。I2-3 の問いと同じ限界の行に経路 1 と hook が動かないときを足した。commit: なし（PR 本文） |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 拒否の文の「出した Stop で出し直しになります」は、拒否が出る場面（上限の後・hook が動かない）では成り立たない |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 拒否の文の「この語」が、書き換えで `依頼との差` から遠くなった |
| I3-4 | 独立-3 | low | no | self-inflicted | test-power | accepted | 書き換えた拒否の文を固定するテストが無い |
| I3-5 | 独立-3 | low | no | inherited | doc-claim | accepted | hooks.json の description が古い条件と上限 2 回のまま（I2-7 と同じ） |
| I3-6 | 独立-3 | low | no | inherited | doc-claim | accepted | request_diff_field.py の docstring と run-request-diff-hook.sh のコメントが古い（I2-8 と同じ） |
| I3-7 | 独立-3 | low | no | inherited | doc-claim | accepted | 拒否の文の、ユーザーが狭めると決めた点の案内にタグの値（none）が無い |
| M4-1 | 方針メモ-4 | low | no | self-inflicted | design | accepted | 上限の後も答え直しを無くす（ユーザーの「上限の後も直す」）。2 本とも、承認の書き込みの検査は変えず、Stop の hook の側で閉じる案で一致。数えを記録ではなく transcript（最後の人の発言の後の、問題のあるマーカー付きの発言の数）にし、記録の書き込みの失敗で block を落とさない。4 回目は block で、マーカーを付けずに「確認を作れなかった」と原因を報告させ、人には systemMessage で「上の確認には答えず、次の報告に返事を」と知らせる。上限の後に最後の発言がマーカー無しなら通す。GDD_SKIP_REQUEST_DIFF は読み手だけを切る。退けた案: 承認の hook を緩める（X）、上限を無くす（Z、止まらない輪のおそれ） |
| I4-1 | 独立-4 | high | no | self-inflicted | field-cap | fixed | 列挙: 設計: 変える（上限を main の書き方から数えていた）。数えが問題のあるマーカー付きの発言の数なので、block された main がマーカー無しの文で返し続けると何度でも block する（止まらない輪）。方針メモ-5 のとおり、この hook が block した回数を host の feedback の行で数える形にした。commit: 2b33e3a4 |
| I4-2 | 独立-4 | high | yes | self-inflicted | field-cap | fixed | 列挙: 設計: 変える（give-up を出したかを最後の発言の形で推し量っていた）。上限の後に問題のある確認の後ろへ文が 1 つ付くと、give-up の block も知らせも出ずに通る。give-up を出したかを feedback の行の目印で決め、通すときは必ず知らせを出す形にした。commit: 2b33e3a4 |
| I4-3 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（記録を組み立ててから出す payload を決めていた）。記録の失敗で block を落とさないのは OSError だけで、sha の計算（surrogate）・_redact・_log_path の例外では block ごと落ちる。出す payload を先に決め、記録は最後にどの例外でも捨てる形にした。commit: 2badcc04 |
| I4-4 | 独立-4 | medium | no | self-inflicted | request-scope | fixed | 「上限の後も直す」が、問いの文にあった hook が動かないときの経路まで含むかが 2 通りに読める。ユーザーは「含めて直す」と答えた（2026-11-15）。返事の後は補正を根拠に承認を通す。commit: a118988a |
| I4-5 | 独立-4 | medium | no | self-inflicted | test-power | accepted | 数え直しのテストの transcript に、人以外の user の行（tool の結果・Stop hook feedback・task-notification）が挟まらない |
| I4-6 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 変更断片の User Action Required が、GDD_SKIP_REQUEST_DIFF で欄の検査が切れなくなったことを書いていない |
| I4-7 | 独立-4 | low | no | inherited | doc-claim | accepted | docs/SECURITY.md:130 が request-diff の hook を止める hook ではないと書いたまま |
| I4-8 | 独立-4 | low | no | self-inflicted | message | accepted | give-up の文が、GDD の Stop hook に継続を求められる場合の止まり方を言わない |
| I4-9 | 独立-4 | low | no | self-inflicted | message | accepted | give-up の文がマーカーの文字列を含み、報告に写されると報告が確認として数えられる |
| I4-10 | 独立-4 | low | no | self-inflicted | message | accepted | 5 回目の知らせが、来ない報告への返事を求める |
| I4-11 | 独立-4 | low | no | self-inflicted | test-power | accepted | 数え直しのテストの 2 つ目の assert が、通常の block と give-up を区別しない |
| I4-12 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | request_diff_field.py の docstring と run-request-diff-hook.sh のコメントが今の使い手と合わない |
| M5-1 | 方針メモ-5 | low | no | self-inflicted | field-cap | accepted | 列挙: I4-1・I4-2 の直し方。2 本とも、上限が数えるべきは main の書き方ではなくこの hook が今のターンで block した回数で、host が transcript に書く `Stop hook feedback:` の行（isMeta の user。実 transcript で形を確かめた）のうち、この hook の block の目印を含む行を数える案で一致。give-up を出したかも同じ行の目印で決める。main の案（本文のある発言の数＋記録の block 数）は、途中の文を数えて上限 3 を狭めるので退けた。割れたのは記録の block 数を max で残すか（Opus-1 は残す、Opus-2 は残さない）。数えの正本を 1 つにし、host が行を書かなくなっても host の連続 block の上限で止まるので、残さない側を採った。両者が足した、出力の print の ensure_ascii と give-up・知らせの文の直し（I4-8〜I4-10）も入れる |
| I5-1 | 独立-5 | high | yes | self-inflicted | field-cap | fixed | 列挙: 設計: 変える（block の回数を transcript の自由文の部分文字列で見分けていた）。give-up の目印を feedback の行の全体から探すので、block の文が引いた main の読めない行に目印があると、1 回目の block で give-up 済みになり、出し直しが 1 回で終わる。差分（無効化後）の 2 回目の後も残ったので再設計に進み、方針メモ-6 のとおり hook 自身の記録で数える形にした。commit: c7a98272 |
| I5-2 | 独立-5 | medium | no | self-inflicted | request-scope | fixed | 「上限の後も直す」が、問いの文にあった hook が動かないときの経路まで含むか（I4-4 と同じ問い）。ユーザーは「含めて直す」と答えた（2026-11-15）。返事の後は補正を根拠に承認を通す。commit: a118988a |
| I5-3 | 独立-5 | medium | no | self-inflicted | test-power | accepted | テストの feedback の行は content が文字列で、repo の fixture の list の形と `[<hook>]: ` の前置きを通らない（実 transcript で見た行は文字列で前置きなし） |
| I5-4 | 独立-5 | medium | no | self-inflicted | test-power | accepted | 記録を組み立てられない確認のテストが例外の経路を通らず、except Exception を固定していない |
| I5-5 | 独立-5 | low | no | self-inflicted | test-power | accepted | tool の結果のテストが isMeta と前置きの条件を固定していない |
| I5-6 | 独立-5 | low | no | self-inflicted | fail-open | accepted | _feedback_text が text の型違いで TypeError を出し、その Stop では止めない |
| I5-7 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | PR 本文が引く知らせの文が実際の文と違い、give-up の文の「出し直しても」が block の回数の数えと合わない |
| I5-8 | 独立-5 | low | no | inherited | observability | accepted | Stop の記録と承認の記録で sha の取り方が違い、同じ確認で一致しないことがある |
| I5-9 | 独立-5 | advisory | no | inherited | doc-claim | out-of-diff | run-request-diff-hook.sh と request_diff_field.py の説明が古い（I4-12 と同じ） |
| I5-10 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文の抜粋の限界の行に経緯の文（前に退けた・このまま進めている）があった。次の巡の前に抜粋から除く |
| I5-11 | 独立-5 | advisory | no | inherited | product | out-of-diff | host の連続 block の上限と、この hook の最大 4 回の合算は未確認 |
| M6-1 | 方針メモ-6 | low | no | self-inflicted | field-cap | accepted | 再設計: 前提: 合う。I4-1・I4-2・I4-3・I5-1 は、block の回数を main の書き方や transcript の自由文から推し量る設計の決定から出ていた。割れた: Opus-1 は feedback の各行の、前置きを外した先頭が hook の定数の文頭で始まるかで数え、give-up は回数から出す。Opus-2 は数えを hook 自身の記録（request-diff.log の同じ session・ターンの block の行）に移し、数えの行を書けたときだけ block し、書けない・読めないときは止めずに知らせる。実 transcript の feedback の行は `[<hook のコマンド>]: ` の前置きつき 2182 件・前置きなし 1306 件で形が一定でない。規則どおり作り直す側の Opus-2 を採った。M4-1 の「記録の書き込みの失敗で block を落とさない」は、書けないときは知らせにする形に替えた |
| I6-1 | 独立-6 | medium | no | self-inflicted | request-scope | fixed | 記録を読めない・書けない環境では、欄の検査は block せず知らせだけになり、問題のある確認が人に届く。「上限の後も直す」がこの経路まで含むかが 2 通りに読める（I5-2 と同じ問いに含めた）。ユーザーは「含めて直す」と答えた（2026-11-15）。返事の後は補正を根拠に承認を通す。commit: a118988a |
| I6-2 | 独立-6 | medium | no | self-inflicted | request-scope | fixed | hook が動かないときの経路を含めない側で進めている（I4-4・I5-2 と同じ問い）。ユーザーは「含めて直す」と答えた（2026-11-15）。返事の後は補正を根拠に承認を通す。commit: a118988a |
| I6-3 | 独立-6 | medium | no | self-inflicted | doc-claim | accepted | 変更断片の数えの説明が、main の挙動（もともと記録で数えていた）と合わず、途中の版の不具合を「今まで」と書いている |
| I6-4 | 独立-6 | low | no | self-inflicted | test-power | accepted | 記録を読めない側の分岐（_blocks_in_turn の例外）にテストが無い |
| I6-5 | 独立-6 | low | no | self-inflicted | observability | accepted | 知らせだけで通した Stop が記録に残らず、sha の突き合わせで取りこぼす |
| I6-6 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | test_replies_without_the_marker_do_not_keep_the_block_going の docstring が撤去した数え方（feedback の行）のまま |
| I6-7 | 独立-6 | low | no | inherited | doc-claim | accepted | docs/SECURITY.md:130 が request-diff の hook を止める hook ではないと書いたまま（I4-7 と同じ） |
| I6-8 | 独立-6 | advisory | no | self-inflicted | field-cap | accepted | 数えの key が人の発言の位置で、transcript の書き直しや hook の二重登録で数えがずれうる。記録に行を足すと block を止められる（敵対的な形） |
| I6-9 | 独立-6 | advisory | no | inherited | doc-claim | out-of-diff | run-request-diff-hook.sh のコメントが形の崩れだけを書いたまま（I4-12 と同じ） |
| M7-1 | 方針メモ-7 | low | no | self-inflicted | design | accepted | ユーザーの「含めて直す」（hook が動かない・記録を書けない経路）の直し方。2 本とも、Stop の側では hook が動かない経路を閉じられないので、承認の書き込みの検査で、人の返事の後に main が書く補正（欄とタグだけを直した版）を受ける案で一致し、案 Z（例外で知らせ）を退けた。割れた点: Opus-1 は狭める点を補正で消させず、記録を書けないときは stop_hook_active で 1 回 block する案を足した。Opus-2 は名指しした返事を decided に引けば狭める点も消せるとし、stop_hook_active は GDD の継続の block の連鎖で常に真になる（lib/autonomy_pushback.py:15）として退けた。main は事実を確かめ Opus-2 の側（広い側）を採った。知らせを形だけの問題と狭める点で分けるのは 2 本とも同じ |
| I7-1 | 独立-7 | high | yes | self-inflicted | correction | fixed | 設計: 変える（狭める点を狭める形の列挙で分類し、補正を提示と別の関数で検査した）。補正の経路が、読めないタグの differs と補正本文の `あり:` を「なし」として通す。分類（narrows）を撤去し、補正は field_problem で見て常に返事の引用を求めた。commit: e1537d7d |
| I7-2 | 独立-7 | medium | no | self-inflicted | request-scope | fixed | 上限の 4 回目で、人への知らせ（答えてよい）と main への give-up の指示（返事は承認ではない）が食い違い、答え直しが残る（依頼から外れる）。give-up の block を撤去し、上限の後は知らせだけにした。commit: e1537d7d |
| I7-3 | 独立-7 | medium | no | self-inflicted | correction | accepted | 列挙: decided は部分一致だけで、返事が「OK」でも decided="OK" で通る（自己申告。PR 本文の限界に開示） |
| I7-4 | 独立-7 | low | no | self-inflicted | request-scope | fixed | narrows が、語を含むが欄の形でない行も狭める点に数え、存在しない点を問い直す（定義の文書と合わない）。分類を撤去し、知らせに見た行を並べた。commit: e1537d7d |
| I7-5 | 独立-7 | low | no | self-inflicted | correction | accepted | 補正の後に別の文を書くと、補正が読まれず deny になる（止まる向き） |
| I7-6 | 独立-7 | low | no | self-inflicted | message | fixed | 補正の文に欄の名前を書くと deny になるのに、拒否の文が言わない。拒否の文に案内を足した（補正の読めない行は示さない）。commit: e1537d7d |
| I7-7 | 独立-7 | low | no | self-inflicted | fail-closed | accepted | 提示の後に形の崩れた行があると _human_entry が例外を出し、承認の書き込みが全部 deny になる（止まる向き） |
| I7-8 | 独立-7 | low | no | self-inflicted | test-power | fixed | タグだけが differs の枝にテストが無い。作り直しのテストに入れた。commit: adcf134d |
| I7-9 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | hooks.json の description が古い条件と上限のまま（request_diff.py の docstring は作り直しで直した） |
| I7-10 | 独立-7 | low | no | self-inflicted | import-hygiene | accepted | request_capture の import が、validate-steering-write.py の sys.path の後片付けを破る（本番の害は未確認） |
| I7-11 | 独立-7 | low | no | self-inflicted | product | accepted | 補正で通した確認は読み手（claude -p）が一度も照らしていない（PR 本文の限界に開示） |
| I7-12 | 独立-7 | advisory | no | self-inflicted | message | fixed | decided に `"` と改行を含められない。拒否の文に「1 行で `"` を含まない部分を引く」を足した。commit: e1537d7d |
| M8-1 | 方針メモ-8 | low | no | self-inflicted | correction | accepted | 再設計: 前提: 合う。再設計後の 2 巡目（独立-7）で high が残った。2 本が割れた: Opus-1 は狭める点の分類（narrows）を撤去し、補正は常に返事の引用を求め、補正を field_problem で見て、上限の後の give-up の block も撤去する案。Opus-2 は分類を許可リストに反転して残し、語の出現ごとに見る案。規則（割れたら作り直す側）で Opus-1 を採った。Fable は、この PR で 1 回使ったので呼ばなかった |
| I8-1 | 独立-8 | medium | no | self-inflicted | observability | accepted | 上限の後に人へ届いた確認が request-diff.log に残らず、承認側の記録と sha で突き合わない |
| I8-2 | 独立-8 | low | no | self-inflicted | request-scope | accepted | 決定（ユーザー「残す」）: 上限の後、狭める点のある確認に「OK」とだけ返すと、その点だけもう一度問われる。直すとユーザーの決定（案 A の「名指しの規則は残す」）と食い違うので、残してよいかを PR 本文の限界の節で問う |
| I8-3 | 独立-8 | low | no | self-inflicted | message | accepted | タグだけが differs・読めないとき、知らせに hook が見た行が出ない |
| I8-4 | 独立-8 | low | no | inherited | doc-claim | accepted | 拒否の文と requirements-gating-steps.md:156 が、返事の後の名指しの無い狭める点と書き忘れの行き先を 2 通りに書く |
| I8-5 | 独立-8 | low | no | inherited | correction | accepted | 補正は返事の後の最後のマーカー無し発言でなければ読まれない（I7-5 と同じ。止まる向き） |
| I8-6 | 独立-8 | low | no | inherited | correction | accepted | AskUserQuestion の質問文（main の文）が返事に入り、decided がそれに当たっても通る |
| I8-7 | 独立-8 | low | no | inherited | fail-closed | accepted | record_allow で surrogate の例外が出ると、承認の書き込みが deny になる（止まる向き） |
| I8-8 | 独立-8 | low | no | self-inflicted | test-power | accepted | 撤去した文言を見る assert が常に真で、2 本は KeyError でだけ block を見る |
| I8-9 | 独立-8 | low | no | self-inflicted | test-power | accepted | 補正の判定で例外が出たときの deny を入口から固定するテストが無い |
| I8-10 | 独立-8 | low | no | self-inflicted | doc-claim | accepted | 変更断片と docs/SECURITY.md に、承認の記録へ人の返事の引用を残すことが無い |
| I8-11 | 独立-8 | advisory | no | inherited | doc-claim | out-of-diff | hooks.json の description が古い上限と条件のまま（I7-9 と同じ） |
| I8-12 | 独立-8 | advisory | no | inherited | doc-claim | accepted | request_diff_field.py の docstring が、Stop と lint は format_problem を使うと書いたまま |
| I8-13 | 独立-8 | advisory | no | inherited | doc-claim | accepted | 出し直しの文の「承認を記録できず、OK を言い直させる」が補正の経路と合わない |
| I8-14 | 独立-8 | advisory | no | self-inflicted | product | accepted | 知らせに並べる行の数に上限が無い |
| I8-15 | 独立-8 | advisory | no | self-inflicted | product | accepted | correction_problem の [0] の IndexError（今は届かない）と、属性値の中の correction の語も読む |
| I9-1 | 独立-9 | high | yes | self-inflicted | approval-path | fixed | 列挙: 設計: 変える（sys.path の副作用を避けるため、人の発言の許可リストを承認の検査に写した）。写しが `<system-reminder>` の除去を落とし、reminder の文を decided に引くと承認が通る。許可リストを依存の無い lib/human_reply.py 1 つにまとめ、照合には人が打った・選んだ部分だけを使う。commit: 20583686 |
| I9-2 | 独立-9 | medium | no | self-inflicted | request-scope | fixed | 写しが打ったコマンドの返事を数えず、答え直しが残る（依頼から外れる）。正本を 1 つにして数えるようにした。commit: 20583686 |
| I9-3 | 独立-9 | medium | no | self-inflicted | test-power | fixed | 返事の判定の分岐（queued・isMeta・AskUserQuestion・コマンド・reminder）に fail-open 側のテストが無い。入口から足した。commit: c0a9285e |
| I9-4 | 独立-9 | medium | no | self-inflicted | request-scope | accepted | 決定（ユーザー「残す」）: 狭める点に「OK」とだけ答えると、その点をもう一度問う経路が、ユーザーの返事の無いまま残る（I8-2 と同じ問い。PR 本文の限界の節で問う） |
| I9-5 | 独立-9 | low | no | self-inflicted | observability | accepted | allow-corrected の行に提示の問題の種類が無く、短い引用が狭める点に当たるかを数えられない |
| I9-6 | 独立-9 | low | no | self-inflicted | test-power | fixed | import を戻しても落ちるテストが無い。承認の検査の読み込みが sys.path を変えないテストを足した。commit: c0a9285e |
| I9-7 | 独立-9 | low | no | self-inflicted | doc-claim | fixed | 写しの docstring の「同じ許可リスト」が実装と合わない。写しを消した。commit: 20583686 |
| I9-8 | 独立-9 | low | no | inherited | fail-closed | accepted | 対にならない surrogate を含む提示で、record_allow が例外を出し deny になる（I8-7 と同じ。止まる向き） |
| I9-9 | 独立-9 | low | no | inherited | product | accepted | origin を書かない host では補正の経路が使えない（止まる向き） |
| I9-10 | 独立-9 | advisory | no | inherited | approval-path | accepted | toolUseResult.answers を tool の名前を見ずに人の返事に数える（未検証） |
| I9-11 | 独立-9 | advisory | no | inherited | doc-claim | out-of-diff | docs/SECURITY.md の降格しない category の一覧が古い |
| M9-1 | 方針メモ-9 | low | no | self-inflicted | approval-path | accepted | 列挙: I9-1 の直し方。2 本とも (a) で、写しをやめ許可リストを依存の無い module 1 つに置く案で一致。main の案（AskUserQuestion は質問と答えのまま照らす）には 2 本とも反対し、照合用の出口を分けて人が打った・選んだ部分だけにする（I8-6 を開き直さない）、reminder の除去は全部の枝に当てる、形の崩れた行で例外を出さない、を足した。入力者は main（agent）で、取り違えの事故の形。transcript の件数は未測（補正の経路は未リリース） |
| I10-1 | 独立-10 | high | yes | self-inflicted | approval-path | fixed | 列挙: ユーザーが「方向を与えて続ける」（origin を 3 形に限る許可リスト）を選んだので直した。commit: 2a1f22e。元の記録: human_reply.py のコマンド行の枝が、origin が dict でない・kind の無い行を「origin 無し」と同じに扱い、人の返事として受ける（承認の検査では e4877f8e の写しより緩む）。差分巡（無効化後）の 2 回目の後も残り、再設計は 2 回使ったので、修正を止めてユーザーに戻す。reviewer の修正案は、受ける origin を「キーが無い・null・dict で kind が human」の 3 つに限る許可リスト |
| I10-2 | 独立-10 | medium | no | self-inflicted | request-scope | accepted | 決定（ユーザー「残す」）: 狭める点に「OK」とだけ答えると、その点をもう一度問う経路が残る（I8-2・I9-4 と同じ問い） |
| I10-3 | 独立-10 | medium | no | self-inflicted | test-power | accepted | 足したテストが、判定できない行を人の返事にしない向きを固定していない（崩れた行だけの後の補正で deny を見ていない） |
| I10-4 | 独立-10 | low | no | self-inflicted | approval-path | accepted | 列挙: 外すのは対になった `<system-reminder>` だけで、閉じていない reminder や host が足すほかの文は残る（引用は自己申告の限界の中） |
| I10-5 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 拒否の文と reference に、引けるのが人の打った文・選んだラベル・打ったコマンドの名前と引数だけだと書いていない |
| I10-6 | 独立-10 | low | no | self-inflicted | product | accepted | 空の発言を、Stop は人のターンに数え、承認の検査は返事に数えない |
| I10-7 | 独立-10 | low | no | inherited | product | accepted | queued の発言だけ、写しで reminder を外さない |
| I10-8 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 変更断片に、打ったコマンドを返事に数えることと足した検証が無い |
| I10-9 | 独立-10 | low | no | inherited | product | accepted | toolUseResult.answers のある行を tool の名前を見ずに人の答えとする（I9-10 と同じ） |
| I10-10 | 独立-10 | advisory | no | self-inflicted | doc-claim | accepted | request_diff.py の docstring と import が、許可リストの場所を request_capture と書いたまま |
| I11-1 | 独立-11 | high | yes | self-inflicted | approval-path | fixed | 列挙: 設計: 変えない（ユーザーの決めた 3 形の許可リストを、user の行の共通の条件にして AskUserQuestion の答えの分岐にも当てる）。実 transcript（30 日）で answers を持つ行 1268 件は全部 origin がキー無しで、正当な答えは落ちない。commit: aee8f07 |
| I11-2 | 独立-11 | medium | no | self-inflicted | request-scope | accepted | 決定（ユーザー「残す」）: 狭める点に「OK」とだけ答えると、その点をもう一度問う経路が残る（I10-2 と同じ問い） |
| I11-3 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | request_capture.py・request_diff.py の docstring が許可リストの中身と場所を古いまま書く |
| I11-4 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文に、origin の 3 形の規則と対応するテストが書かれていない |
| I11-5 | 独立-11 | advisory | no | inherited | doc-claim | out-of-diff | docs/SECURITY.md の降格しない category の列挙がコードの 7 個と合わない |
| I11-6 | 独立-11 | advisory | no | inherited | approval-path | accepted | main の Skill 起動を host が origin 無しのコマンド行で書く版があれば人の返事に数えられる（未測） |
| I11-7 | 独立-11 | advisory | no | self-inflicted | style | accepted | PR 本文の項目の番号の並びが順でない |
| I12-1 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | request_capture.py の docstring が許可リストの origin の条件を古いまま書く（I11-3 と同じ） |
| I12-2 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文に、origin の 3 形の規則が写しと Stop の検査にも効くことが書かれていない（I11-4 と同じ） |
| I12-3 | 独立-12 | advisory | no | self-inflicted | product | accepted | 答えの行の origin の実データの形が未確認（main が 30 日分で測り、1268 件すべてキー無し。notes に記録） |
| I12-4 | 独立-12 | advisory | no | inherited | product | accepted | origin の無い行は形だけで人の発言になり、tool_use の name と対にしていない |
| I12-5 | 独立-12 | advisory | no | inherited | product | accepted | REMINDER・COMMAND_ARGS の `[\s\S]*?` が閉じタグの無い大きな本文で遅くなりうる |
| I12-6 | 独立-12 | advisory | no | self-inflicted | style | accepted | PR 本文の項目の番号の並びが順でない（I11-7 と同じ） |
