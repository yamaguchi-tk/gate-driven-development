---
lane: L1+
pr: 485
amends: 20260915-x56-hitl-lint-gate-wiring.md, 20260915-x60-x57-hitl-required-fields.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-14T13:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2b05cbd9 | 0 | 4 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 68ed3b91 | 0 | 3 | 0 | 2026-10-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 90b0eaca | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | low | no | self-inflicted | design | fixed | 変えるのは enforce_hitl_lint_gate の結果の扱いだけで、lint の判定は変えない。通らなかったときは止めず、hook-errors.log に記録し、停止を許す _stop_for_non_done_reason で systemMessage を 1 回だけ出す（autonomy の押し返しで block するときは出さず、JSON が 2 つ並ばない）。差し戻しの予算・_emit_block・state の引数は使わなくなるので外す（戻すときは revert）。GDD_SKIP_HITL_LINT は警告を止める手段として残す。テンプレート 2 本に `## 👤 次にすること` を足す。限界は、HITL の不足を差し戻さなくなることと、警告を見ても AI は自分で直さないこと。2026-10-13 に Opus と main の案が一致し、2026-10-14 にユーザーが計画を承認した commit: 3cde8498 |
| I1-1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | safe_path のテストの ModuleNotFoundError の assert が、警告文が最初の行だけなので空回りする。Traceback が無いことを見る形にした commit: 555e48fa |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | lint の不通過が hook-errors.log を埋め、gdd-status の Hook Errors の窓から本物の故障を押し出す。不通過は .gdd/hitl-lint.log に分けた commit: 0dc5963b |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 警告文が lint の固定の見出し行しか載せず、何を直すかが伝わらない。詳細行を 3 行まで載せた commit: 0dc5963b |
| I1-4 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 押し返しの block と lint の警告が重なる経路（stdout が JSON 1 つ）を固定するテストが無い（gdd_stop_hook.py:734）。tests/test_stop_hook_autonomy_pushback.py に足した commit: 555e48fa |
| I1-5 | 独立-1 | low | no | self-inflicted | product | fixed | 依頼の「テンプレートに次にすることの見出しを足す」から、rollback-patterns.md の Downstream Human Recheck Handoff の型が漏れていた commit: 0dc5963b |
| I1-6 | 独立-1 | low | no | self-inflicted | test-power | fixed | 警告文と記録について lint の名前しか assert していない。lint を直接走らせた出力の最初の行・詳細行と、記録の全文を見るテストにした commit: 555e48fa |
| I1-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | warn_wiring のテストが警告文を捨て、記録だけの lint が警告文に載らないことを確かめていない |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「空行 2 行」が差分（1 行）と合わない commit: なし（PR 本文） |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「state_path も 3 つの関数から外した」「_emit_block は外した」が差分と合わない commit: なし（PR 本文） |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 未リリースのほかの断片（python-isolation・wait-loop-deny・x60-declared・x64）が差し戻し・予算の挙動をそのまま書いている |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 外した state のキー hitl_lint_blocks を、state_io.py と test_stop_hook_state_unit.py が今も読まれるキーの例として書いている |
| I1-12 | 独立-1 | low | no | self-inflicted | style | accepted | テスト名とコメントに block・予算の設計が残っている |
| I1-13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「マーカーを最後に置く」と書く規則の文書（subagent-dispatch.md など）が、テンプレートの順序（マーカー → 見出し）と食い違う |
| I1-14 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しい断片の User Action Required が「なし」で、type の根拠が見えない（Affected Files は関数名を足していない） |
| I1-15 | 独立-1 | advisory | no | self-inflicted | product | accepted | lint の例外による失敗と品質の不足が同じ記録に並ぶ |
| I1-16 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | HITL の出力契約を変えたので Skill RED-GREEN Evidence が要る。PR 本文に書いた commit: なし（PR 本文） |
| I1-17 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | compact テンプレートの終わり方を Stop hook が読む形と照らすテストが無い |
| I1-18 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 既存の断片 2 本の書き換えに amends: の宣言が要る（宣言済み） |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | accepted | 不通過を hitl-lint.log に分けたのは配線済みの 3 本だけで、記録だけの lint（required-fields）の不通過は今も hook-errors.log に入る |
| I2-2 | 独立-2 | medium | no | self-inflicted | product | accepted | lint が例外で落ちると exit 1 で不通過に数えられ、故障の記録（hook-errors.log）ではなく hitl-lint.log に入る |
| I2-3 | 独立-2 | medium | no | self-inflicted | product | accepted | 「マーカーを最後に置く」と書く gdd-dev.md・subagent-dispatch.md などが、テンプレートの「マーカーの後に見出し」と食い違う（I1-13 と同じ箇所で severity が上がった） |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | rollback-patterns.md が参照する節の名前に 👤 が無く、実際の見出しと合わない |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | docs/SECURITY.md の hook の表に、Stop hook の新しい書き込み先（hitl-lint.log・警告の systemMessage）が無い |
| I2-6 | 独立-2 | low | no | self-inflicted | product | accepted | append_hook_error の記録先の計算が try の外に出た（今の呼び出し元はすべて Path を渡すので届かない） |
| I2-7 | 独立-2 | low | no | self-inflicted | test-power | accepted | 押し返しのテストが、lint が実際に走ったことを確かめていない |
| I2-8 | 独立-2 | low | no | self-inflicted | style | accepted | テスト名の and_logs が、外した assert のまま |
| I2-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation に test_stop_hook_autonomy_pushback.py が無い |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 「詳細行（3 行まで）」が lint ごとかどうか読めない。PR 本文は直した commit: なし（PR 本文） |
| I2-11 | 独立-2 | low | no | inherited | product | accepted | 新しい記録先も hook-errors.log と同じく FIFO・symlink を避けずに開く |
| I2-12 | 独立-2 | advisory | no | inherited | product | accepted | hitl-lint.log に大きさの上限も session の識別子も無い |
| I3-1 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「出力に」は、Stop hook がマーカーを探す main の最後の text block より広い |
| I3-2 | 独立-3 | low | no | inherited | doc-claim | accepted | 同じ「末尾にマーカー」の規定が runtime で読まれるほかの 5 か所に残る（旧#489 で直している） |
| I3-3 | 独立-3 | advisory | no | inherited | doc-claim | accepted | compact テンプレートの説明文の「末尾のタグ」が、Template の並びと合わない |
| I3-4 | 独立-3 | advisory | no | inherited | doc-claim | accepted | lint-hitl-required-fields.py の docstring の「出力の末尾にある本物」が今のテンプレートと合わない |
| I3-5 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に、必須ルール 1 からマーカーを末尾に置くと読める語を外したことが無い commit: なし（PR 本文） |
| I3-6 | 独立-3 | advisory | no | inherited | doc-claim | out-of-diff | clarification-needed の停止の「末尾に」の文（旧#489 で直している） |
| I3-7 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が必須ルール 1 の変更を含むかを抜粋から確かめられない |
