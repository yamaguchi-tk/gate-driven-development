---
lane: L1+
pr: 654
follow_up_of: 653
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-11-10 |
| 方針メモ-1 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-11-10 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ccb5183a0720c1405b108af1c632936d6c68c0c1 | 6 | 6 | 5 | 2026-11-10 |
| 方針メモ-2 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-11-10 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 33d5d79ce8a9bcb8ef90e20350c04c1c2490598d | 6 | 3 | 5 | 2026-11-10 |
| 方針メモ-3 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-11-10 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e1210696c7b030bed1e8f4b2b5e28ffa3bf1f319 | 3 | 4 | 3 | 2026-11-10 |
| 方針メモ-4 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-11-10 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 337f3a11d0624fd41899711ce5ae37d15d7dc82e | 2 | 1 | 2 | 2026-11-10 |
| 方針メモ-5 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-11-10 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 02a42087226c5d17508ccb10284ef9b836e760e5 | 2 | 1 | 0 | 2026-11-10 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 058e80087906e920e2a2392121f78ca1a2353f76 | 1 | 0 | 1 | 2026-11-11 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1-1 | 方針メモ | advisory | no | self-inflicted | trigger | fixed | 2 本とも、草案の警告の lint とテンプレートの文では「OK を承認にしない」が発火する場所が無いと指摘した（警告は systemMessage でユーザーにしか見えない）。Opus-2 の、承認の書き込みの PreToolUse で deny する形にした。ユーザーは「推奨どおり」。commit: なし（この PR の最初の commit） |
| M1-2 | 方針メモ | advisory | no | self-inflicted | scope | fixed | 対象の広さは 2 本と Fable が宣言のある提示だけを推したが、同じ入力空間なので広い側（全 human check の停止。簡易な確認は先頭に 1 行）にした。commit: なし（この PR の最初の commit） |
| M2-1 | 方針メモ-1 | advisory | no | self-inflicted | trigger | fixed | 承認の書き込み 203 回のうち 147 回（72%）は Bash で、Write・Edit の検査だけでは 28% にしか届かないと実測した。2 本の推奨（A）で、Bash の PreToolUse に固定の部分文字列だけを見る検査を足した。Stop で state.md を照らす B は足さず、限界に書く。commit: なし（この PR の最初の commit） |
| I1-1 | 独立-1 | high | no | self-inflicted | import | fixed | 設計: 変える（実行時の import をやめ、起動時の import の塊に入れ、欄の判定を依存なしの module に分けた）。validate-steering-write.py は起動時の import の後で lib を path から外すので、実行時の import が `-I` の wrapper で落ち、steering の書き込みが全部止まっていた。wrapper を通すテストを足した。commit: 8614456b |
| I1-2 | 独立-1 | high | yes | self-inflicted | presentation-window | fixed | 列挙: 設計: 変える（再提示は全部の点を載せると規定し、通った承認の区切りより後の提示で点の数が減ったら止める）。変えた点だけの再提示で、`なし` 以外の点が直前の提示から消えて承認が通っていた。方針メモ-2 の 2 本の推奨どおり、区切りは deny されていない承認か changes_requested の書き込みにし、数えるのは欄の行の数にした。commit: 95beae00 |
| I1-3 | 独立-1 | high | yes | self-inflicted | approval-detection | fixed | 設計: 変える（承認の書き込みの見分け方を peer turn の検査と同じ道具〔Edit の当て外れ・gate の reader〕にした）。old_string が当たらない Edit と、囮の行の後の本当の承認行で通っていた。commit: 3da46699 |
| I1-4 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（wrapper が python の失敗を deny の JSON に変える）。Bash の hook の python が 0 以外で終わると、Claude Code が通していた。commit: 3da46699 |
| I1-5 | 独立-1 | high | yes | self-inflicted | field-form | fixed | 列挙: 設計: 変える（候補を行頭のラベル・行の途中の区切りつきのラベル・表の行に広げ、受け付ける形を 1 つにし、合わない候補は読めないものとして止める）。番号つき・`*` などの書き方の欄を読まずに通していた。方針メモ-2 で 2 本が割れた候補の広さは、同じ入力空間なので広い側（インラインコードの外の出現）にした。deny の文に読めなかった行を入れる。commit: 95beae00 |
| I1-6 | 独立-1 | high | yes | self-inflicted | exemption | fixed | 設計: 変える（Bash の入口から承認済みの免除を外した）。別の steering が承認済みだと、新しい承認の書き込みも通っていた。commit: 3da46699 |
| I1-7 | 独立-1 | medium | no | self-inflicted | scope | accepted | 確認待ち: 依頼の 1 点目は強制の場所を Write・Edit の検査としていたが、Bash の入口を足して広げた（方針メモ-1 で承認の書き込みの 72% が Bash と実測）。Bash の入口を残す推奨で進め、PR 本文の限界の節で問う |
| I1-8 | 独立-1 | medium | no | self-inflicted | delivery | fixed | Downstream Human Recheck Handoff・full テンプレートの記入例・compact の必須語に欄が無く、依頼の 3 点目（全 human check の停止）に届いていなかった。commit: 3a6d3da6 |
| I1-9 | 独立-1 | medium | no | self-inflicted | delivery | fixed | gdd-dev.md・gdd-brainstorming・gdd-requirements-gating の承認の文が「OK は全承認」のままで、依頼の 5 点目と食い違っていた。commit: 3a6d3da6 |
| I1-10 | 独立-1 | medium | no | self-inflicted | test | fixed | Write・Edit の入口のテストが実際の wrapper を通っていなかった。commit: 2061f0b6 |
| I1-11 | 独立-1 | medium | no | self-inflicted | test | accepted | ApplyPatch・Write・MultiEdit の入口のテストが無い |
| I1-12 | 独立-1 | medium | no | self-inflicted | test | fixed | tip で warn の配線のテストが落ちていた（記入例に欄が無い）。commit: 8614456b |
| I1-13 | 独立-1 | low | no | self-inflicted | docs | accepted | SECURITY.md の hook の一覧に新しい hook が無い |
| I1-14 | 独立-1 | low | no | self-inflicted | scope | fixed | `なし（理由）` で理由を書けてしまい、依頼の 2 点目（理由を書く場所は作らない）から外れていた。括弧の中はユーザーの発言の引用だけを受け、transcript の発言と照らす。commit: afc2ad15 |
| I1-15 | 独立-1 | low | no | self-inflicted | measure | fixed | deny が記録に残らず、撤去の線（deny の後に案が変わった件）を数えられなかった。commit: afc2ad15 |
| I1-16 | 独立-1 | low | no | self-inflicted | measure | accepted | lint の失敗が hook-errors.log に書かれる |
| I1-17 | 独立-1 | low | no | inherited | docs | accepted | 「8 要素」の数が古い |
| I1-18 | 独立-1 | low | no | self-inflicted | pr-body | fixed | PR 本文の抜粋が ApplyPatch・MultiEdit も止めると読める。commit: なし（PR 本文） |
| I1-19 | 独立-1 | low | no | self-inflicted | docs | accepted | 変更断片の Validation にテストの名前が無い |
| I1-20 | 独立-1 | advisory | no | self-inflicted | docs | fixed | hook の注記が古い。commit: 3da46699 |
| I1-21 | 独立-1 | advisory | no | self-inflicted | template | accepted | テンプレート外の記述あり（PR 本文の抜粋の 29 行目の経緯）。次の巡の前に抜粋から除く |
| M3-1 | 方針メモ-2 | advisory | no | self-inflicted | field-form | fixed | 列挙: 2 本とも (a) 許可リストで閉じると推した。行の途中の出現を候補にすると、返答ガイドの `依頼との差: なし` の行で full の提示が全部止まると指摘した。候補をコードの外に限り、テンプレートを通すテストを足した。commit: 95beae00 |
| M3-2 | 方針メモ-2 | advisory | no | self-inflicted | presentation-window | fixed | 列挙: 2 本とも、区切りを deny された承認にすると穴になると指摘した。区切りは tool_result が error でないものに限り、比べる数は欄の行の数にした（Opus-2）。規定の書き換えは 7 か所にそろえた（Opus-2）。commit: 95beae00 |
| I2-1 | 独立-2 | high | yes | self-inflicted | quote-form | fixed | 再設計: 設計: 変える（値はちょうど `なし` だけを通し、引用の照合を撤去した）。`なし（…「…」…）` の括弧の中に、引用の外の理由を書けていた commit: af05df10 |
| I2-2 | 独立-2 | high | yes | self-inflicted | quote-trust | fixed | 再設計: 設計: 変える（引用の照合を撤去し、hook はユーザーの発言を読まない）。引用の照合先に AskUserQuestion の問いの文（assistant が書いた文）が入り、空白や 1〜2 文字の引用も通っていた commit: af05df10 |
| I2-3 | 独立-2 | high | yes | self-inflicted | field-form | fixed | 再設計: 設計: 変える（`依頼との差` を含む行は全部を候補にし、1 つの形だけを受け付ける）。欄の候補が区切り記号の列挙で、`` `依頼との差`: `` や全角空白・矢印の書き方を読み飛ばしていた commit: af05df10 |
| I2-4 | 独立-2 | high | yes | self-inflicted | presentation-window | fixed | 再設計: 設計: 変える（前の提示との比較を撤去し、点の数は state.md の `Human Check Points` と照らす）。区切りが tool の入力の 2 語だけで決まり、gate の手順 8 の書き込みで数え直しになっていた commit: af05df10 |
| I2-5 | 独立-2 | high | no | self-inflicted | handoff-delivery | fixed | 再設計: 設計: 変える（Handoff の欄は判断ポイントごとに、おすすめの案について 1 行にした）。Handoff の案ごとの欄で、4 択の後の承認が記録できなくなっていた commit: af05df10 |
| I2-6 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 再設計: 設計: 変える（Bash の wrapper は付け替えだけの純 bash にし、kill-switch.sh を読めないときも止める）。Bash の wrapper が kill-switch.sh を読めないと exit 1 で終わり、Bash が通っていた commit: af05df10 |
| I2-7 | 独立-2 | medium | no | self-inflicted | field-form | accepted | 太字の中にコロンを入れた書き方や `**なし**` で、`なし` と書いても止まる |
| I2-8 | 独立-2 | medium | no | self-inflicted | delivery | accepted | 受け付ける引用の形と止めた理由の種類が、テンプレートと deny の文で書き手に届かない |
| I2-9 | 独立-2 | medium | no | self-inflicted | test | accepted | 例外で止まることを確かめるテストが、差し替える関数を経路から外れたため何も確かめていない |
| I2-10 | 独立-2 | low | no | self-inflicted | docs | accepted | hooks.json の (17) の説明と docstring が、消した例外を残している |
| I2-11 | 独立-2 | low | no | self-inflicted | docs | accepted | README の hook の数とテンプレートの受理文法の節が追従していない |
| I2-12 | 独立-2 | low | no | self-inflicted | pr-body | fixed | PR 本文の抜粋が実装と合っていない。commit: なし（PR 本文） |
| I2-13 | 独立-2 | low | no | self-inflicted | docs | accepted | 変更断片が差分の挙動と合っていない |
| I2-14 | 独立-2 | low | no | self-inflicted | style | accepted | presentation_blocks_approval が本番のどこからも呼ばれない |
| I2-15 | 独立-2 | low | no | self-inflicted | docs | accepted | テストの docstring が、読む先を古い名前で書いている |
| I2-16 | 独立-2 | advisory | no | self-inflicted | measure | accepted | request-diff.log の欄の問題は引用の照合も点の数も見ないので、guard の判定と食い違う |
| I2-17 | 独立-2 | advisory | no | inherited | bookkeeping | out-of-diff | 依頼の原文に main の注記が入っている |
| M4-1 | 方針メモ-3 | advisory | no | self-inflicted | redesign | fixed | 再設計: 2 本とも、種類ごと消す設計の変更はあると答えた。high は全部、書き手の文・ユーザーの発言・過去の tool の入力から意味を推し量る部品から出ていた。欄を 1 つの形と値 `なし` に閉じ、引用の照合と前の提示との比較を撤去し、wrapper を止める側にした。割れた 2 点のうち、点の数は Opus-2 の state.md の欄（Opus-1 は撤去して限界）を、狭めた点の発言の置き場は Opus-1 の `根拠` の行（Opus-2 は request.md）を採った。Bash は Opus-2 の付け替えにした。commit: af05df10 |
| I3-1 | 独立-3 | high | yes | self-inflicted | points-baseline | fixed | 列挙: 承認を書く書き込みの中で `Human Check Points` を下げれば、点の数の照合をすり抜けた。deny の文がその道を案内していた。再設計: 設計: 変える（点の数の基準を書き手が書く state.md の欄に置いた）。commit: 337f3a11d0624fd41899711ce5ae37d15d7dc82e |
| I3-2 | 独立-3 | high | yes | self-inflicted | points-baseline | fixed | 列挙: `Human Check Points` の行を消す・数でない値を挟む・射影できない tool で、減少の検査を通った。再設計: 設計: 変える（同上。欄と減少の検査を撤去）。commit: 337f3a11d0624fd41899711ce5ae37d15d7dc82e |
| I3-3 | 独立-3 | high | yes | inherited | bash-approval | accepted | 確認待ち: 列挙: `Human Check Status` の語を含まない sed（`3s/pending/approved/`）で、Edit・Write の検査を通らずに承認が着地する。全レーン共通の新しい発火条件の規則で transcript を測ると、事故の実例は 0 件のため PostToolUse の hook は足さない。足すかは PR 本文で問う |
| I3-4 | 独立-3 | medium | no | self-inflicted | points-baseline | accepted | gate に入り直したときの手順 8 が、前の check の Points が残っていると減少として止まる |
| I3-5 | 独立-3 | medium | no | self-inflicted | measure | accepted | Bash の deny と Points の減少の deny が request-diff-approval.log に残らない |
| I3-6 | 独立-3 | medium | no | self-inflicted | delivery | accepted | 狭めた点の発言を引く `根拠` の行が、compact と Handoff に無い |
| I3-7 | 独立-3 | medium | no | self-inflicted | measure | accepted | 測れる発火の件数を未測とし、リスクが低いと書いている |
| I3-8 | 独立-3 | low | no | self-inflicted | docs | accepted | Bash の hook は payload 全体を照らすが、文書は「コマンドに」と書く |
| I3-9 | 独立-3 | low | no | self-inflicted | test | accepted | python を起動しないことのテストが、起動を見分けない |
| I3-10 | 独立-3 | low | no | self-inflicted | test | accepted | 壊れた transcript の行のテストが判別力を失った |
| I3-11 | 独立-3 | low | no | self-inflicted | docs | accepted | 新しい state の欄が state-field-tiers.md に無い |
| I3-12 | 独立-3 | low | no | self-inflicted | docs | accepted | 変更断片が Points を書く範囲と残る穴を実際と違えて書いている |
| I3-13 | 独立-3 | low | no | inherited | docs | accepted | README の PreToolUse の本数が古い |
| I3-14 | 独立-3 | low | no | self-inflicted | pr-body | fixed | 予算の問いが限界の節に無い。commit: なし（PR 本文） |
| I3-15 | 独立-3 | advisory | no | self-inflicted | measure | accepted | 正規化で、記録に残る欄の値が書かれた値と変わる |
| I3-16 | 独立-3 | advisory | no | self-inflicted | field-form | accepted | 依頼の原文に語が入っていると `原文:` の行で止まる |
| I3-17 | 独立-3 | advisory | no | inherited | scope | accepted | マーカーのある提示が transcript に無い承認は照合されない |
| I3-18 | 独立-3 | advisory | no | self-inflicted | docs | accepted | transcript を読めないときの deny の文が欄の問題と読める |
| I3-19 | 独立-3 | advisory | no | self-inflicted | style | accepted | Bash の hook が kill-switch.sh を照合の後で source する |
| I3-20 | 独立-3 | advisory | no | self-inflicted | test | accepted | wrapper のテストが HOME を隔離しない |
| M5-1 | 方針メモ-4 | advisory | no | self-inflicted | points-baseline | fixed | 列挙: 再設計: I3-1・I3-2 は 2 本とも (b)。Opus-1 は基準をユーザーが見た提示（transcript）に移し、区切りを guard が通した承認・changes_requested の記録にする作り直し、Opus-2 は比較を撤去して限界にする案。割れたので作り直す側（Opus-1）を採り、Opus-2 の案は PR 本文で問う |
| M5-2 | 方針メモ-4 | advisory | no | inherited | bash-approval | accepted | 列挙: 再設計: I3-3 は、Opus-2 が transcript を測り、語を含まない Bash の承認は事故の実例 0 件（レビュー役が作った形だけ）。Opus-1 は Bash の PostToolUse で、guard の記録が無い approved への変化を止める案。全レーン共通の規則（当たる件数が 0 なら発火条件を足さない）が先に当たるので足さず、I3-3 は確認待ちにして PR 本文で問う |
| I4-1 | 独立-4 | high | yes | self-inflicted | points-baseline | fixed | 列挙: 設計: 変えない（数える集合を欄の検査と同じにする。方針メモ-5）。前の提示の点を読める欄の行だけで数えるので、読めない形・欄の欠け・欄の無い前の提示の後に、変えた点だけの再提示が通る。commit: 02a42087226c5d17508ccb10284ef9b836e760e5 |
| I4-2 | 独立-4 | high | yes | self-inflicted | points-baseline | fixed | 設計: 変える（区切りを本文の sha から、同じ state.md の承認の位置に移す）。区切りを session の承認の提示の sha の集合で決め、steering も位置も見ないので、別の steering の承認や同じ本文の再出で区切りが動いて通る。commit: 02a42087226c5d17508ccb10284ef9b836e760e5 |
| I4-3 | 独立-4 | medium | no | self-inflicted | points-baseline | accepted | 全面見直しや取りやめた task の後の、新しい human check の承認を、前の大きい提示の点の数で止める |
| I4-4 | 独立-4 | low | no | self-inflicted | request-scope | accepted | 点の数の照合と Bash の付け替えは、依頼の「直前の提示」と強制の場所の外に足した手段。問い 2・3 の返事まで merge-ready にしない |
| I4-5 | 独立-4 | low | no | self-inflicted | guard-exception | accepted | 単独サロゲートを含む提示が transcript に残ると、その session の承認の書き込みが全部 internal error で止まる |
| I4-6 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の「通すたびに 1 行残す」と記録の中身が、実装と合わない |
| I4-7 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | requirements-gating-steps・human-check-template・gdd-dev の再提示の規定に、取り下げた点が無い |
| I4-8 | 独立-4 | low | no | self-inflicted | test-power | accepted | allow の記録の位置・降格の経路・session_id の照合を変えても落ちるテストが無い |
| I4-9 | 独立-4 | advisory | no | self-inflicted | security-boundary | accepted | 区切りの記録は agent が Bash で書ける場所にある |
| I4-10 | 独立-4 | advisory | no | self-inflicted | style | accepted | `_RDA_PENDING` が module の global で消されない |
| I4-11 | 独立-4 | advisory | no | self-inflicted | product | accepted | allow は PreToolUse の時点で残すので、Edit が失敗しても区切りが残る |
| M6-1 | 方針メモ-5 | advisory | no | self-inflicted | points-baseline | fixed | 列挙: I4-1・I4-2 は 2 本とも (a)。点の数を欄の候補の行（読めない行も含む）と宣言の大きい方で数え、区切りを同じ session・同じ state.md の最後に通した承認の提示の uuid の位置にする。見つからなければ区切らない。入力の実測は、同じ session の再提示で承認ポイント数が前より減った件が 21 件（marker のある 633 session・提示 2048 件）で、1 件以上なので (a) |
| I5-1 | 独立-5 | high | no | self-inflicted | points-baseline | accepted | ユーザーの選択（撤去する）で部品ごと撤去: 列挙: 前の提示の読めない行と宣言を点に数えるので、欄の外の語や多すぎる宣言を直した再提示が「点が減った」で止まり、降格もしない |
| I5-2 | 独立-5 | medium | no | self-inflicted | points-baseline | accepted | 区切りを直前の提示より前だけで探すので、同じ提示での承認のやり直しで transcript の全部を数えて止まる |
| I5-3 | 独立-5 | high | no | self-inflicted | points-baseline | accepted | ユーザーの選択（撤去する）で部品ごと撤去: 列挙: 区切りを state.md ごとにしたので、同じセッションで前の task を終えた後の新しい task の最初の承認が、前の task の点の数で止まる |
| I5-4 | 独立-5 | low | no | self-inflicted | test-power | accepted | 同じ本文の提示を区切りにしないテストが、uuid が transcript に無い経路で deny になり、本文で探す実装に戻しても落ちない |
| I5-5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | DROP_MESSAGE が点の数を「行」と書き、何をどの提示から数えたかを書かない |
| I5-6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | テストのモジュールの説明が、欄の数と session の区切りのまま |
| I5-7 | 独立-5 | low | no | self-inflicted | guard-exception | accepted | 4301 桁以上の承認ポイント数で、その steering の承認が内部エラーで止まり続ける |
| I5-8 | 独立-5 | advisory | no | self-inflicted | product | accepted | allow の記録に sha が無く、deny の記録に steering が無い |
| I5-9 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 問い 2 が、照合を残すと正当な承認が止まる場面を書いていない |
| I6-1 | 独立-6 | high | yes | self-inflicted | points-baseline | accepted | ユーザーが限界を選んだ（2026-11-11「撤去する（Fable）」）: 承認ポイントを減らした再提示で、なし以外の点が承認として通る。限界の節の先頭に、直していない常時 High・実害クラスとして書く |
| I6-2 | 独立-6 | low | no | self-inflicted | guard-exception | accepted | 提示の本文に単独サロゲートがあると、allow の記録の sha で例外になり正当な承認が止まる |
| I6-3 | 独立-6 | low | no | self-inflicted | test-power | accepted | allow の記録のテストが、sha と uuid の中身と、提示が無いときに残さないことを固定していない |
| I6-4 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | allow・deny の sha が request-diff.log の sha（strip した本文）と突き合わない |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | hooks.json の (17) の説明が、記録の条件を言い過ぎ、欄の無い提示と読めない transcript の deny を書いていない |
| I6-6 | 独立-6 | low | no | inherited | doc-claim | accepted | 変更断片の deny の条件に、transcript を読めないときと通す条件が無い |
| I6-7 | 独立-6 | low | no | inherited | doc-claim | accepted | README の PreToolUse の行が 16 hook のままで、Bash の付け替えを挙げていない |
| I6-8 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「発火の上限 21 件」は上限ではなく目安 |
| I6-9 | 独立-6 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋に撤去の経緯の文）。PR 本文から除く |
| I6-10 | 独立-6 | advisory | no | self-inflicted | test-power | accepted | 穴を期待どおりとして固定するテストを足している |
| I6-11 | 独立-6 | advisory | no | self-inflicted | style | accepted | テストの import 名・使わない引数・docstring の小さな食い違い |
| I6-12 | 独立-6 | advisory | no | inherited | doc-claim | accepted | lint のテストの docstring が呼び先を取り違えている |
| I6-13 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | agent が読むテンプレートに、通り抜けの形が書いてある |
