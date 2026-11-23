---
lane: L1+
pr: 551
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | df8b6887 | 0 | 6 | 0 | 2026-10-21 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c36a1d8a | 1 | 6 | 1 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b725736f | 1 | 1 | 1 | 2026-10-21 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | b725736f | 0 | 0 | 0 | 2026-10-21 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b8b6da32 | 0 | 2 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | medium | no | self-inflicted | shared-predicate | fixed | done guard の Check 1 は `_scan_remaining_tasks` 単体ではなく、行区切り文字と fence の閉じ忘れの検査を先に組み合わせている。単体を呼ぶと fail-open になるので、組み立てを `lib/tasklist_structure.py` に切り出して hook とスクリプトの両方から呼ぶ（Opus）。commit: 9b4f9739 |
| pm-2 | 方針メモ | medium | no | self-inflicted | shared-predicate | fixed | reviewed-by 行を check-gate-ledger.sh の subprocess で拾うと、無関係な steering の解決の失敗で行が出ず誤って止まる。ledger の heredoc を `tasklist_parse.reviewed_by_rows` に移して両方から呼ぶ（Opus）。commit: 9b4f9739 |
| pm-3 | 方針メモ | medium | no | self-inflicted | fail-open | fixed | Codebase Health の base を既定値に倒すと、黙って違う範囲を見る。`--base` を必須にし、解決できなければ invalid にする（Opus・Fable）。commit: 9b4f9739 |
| pm-4 | 方針メモ | medium | no | self-inflicted | routing-order | fixed | Step 0 で全行を一度に Next Action へ写すと、2 行以上が fail したときに勝つ差し戻し先が変わる。Step 0 は回して写すだけにし、各 Step が自分の位置で行を読む（Opus）。commit: 9b4f9739 |
| pm-5 | 方針メモ | medium | no | self-inflicted | duplicate-precheck | fixed | dispatch 前の実行は新しい手順を足すだけでなく、既存の main 側の事前確認（Post-Return Routing 手順 3 と Template の事前確認）をその行で確かめる形に寄せる（Fable）。commit: 9b4f9739 |
| pm-6 | 方針メモ | medium | no | self-inflicted | request-drift | accepted | 確認待ち: Refactor Gate Status（Step 3b）と Planning Reviewer Selection（Step 2）を「文字列の有無だけ」の行でスクリプトに入れるか（Fable は入れる、Opus は入れない）。推奨（入れない。値の書式が宣言されておらず、有無だけでは Step 3b・2 の述語を代替しきれない）で進め、PR 本文の限界の節に問いを書いた |
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | Step 0 が、行の無い Step を通す。stdout が UTF-8 でないと print が途中で落ち、後ろの行（Codebase Health など）が消えて素通りする。stdout と子の lint を UTF-8 に固定し、例外の部品が受け持つ要求すべてに invalid 行を残し、終わりの行を出す。Step 0 は終わりの行が無い・行の無い Step を invalid にする。commit: b725736f |
| F2 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 機械検査の不備は今までどおり gate の Round を使う。依頼の「reviewer の gate から外す」を、gate の外（main）で Next Action に写す形にするか。推奨（今の形。遷移表を変えない）で進め、限界を「依頼より狭い」にした |
| F3 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: Step 3b・2 を入れない狭い側に、数値の理由が無い（pm-6 と同じ問い）。限界の節に問いを書いた |
| F4 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 観点 8・4c の Covers AC・4d の field・AC Trace Ledger の行など、機械で判定できる検査の列挙と、残す理由が PR 本文に無い。PR 本文に Step ごとの表を載せた。commit: なし（PR 本文） |
| F5 | 独立-1 | medium | no | self-inflicted | same-rule-drift | accepted | Checklist E (ii)(b) で Route In Progress を自動更新しても、Step 0 の行で止まり Round が 1 回増える |
| F6 | 独立-1 | medium | no | self-inflicted | wiring | accepted | dispatch 前の機械検査の節を、普通の経路（refactor-planning → completion-check、SKILL.md の冒頭、nudge hook）が指していない |
| F7 | 独立-1 | medium | no | self-inflicted | measurement | accepted | 「移しただけの記録を戻す」という新しい発火条件の件数を測っていない |
| F8 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 「CI から回せる形」を狭めたのに `その他` に分類している。PR 本文で「依頼より狭い」に直した。commit: なし（PR 本文） |
| F9 | 独立-1 | low | no | self-inflicted | test-power | accepted | test_line_separator は、行区切り文字の検査を消しても落ちない |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | reviewer の新しい段落が、観点 8 まで見ないと読める |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が、skill と agent 定義の切り替わりの時機を誤って書いている |
| F12 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files にテストが無い |
| F13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しく止める入力（非標準の行・state.md が無い・Route の行が読めない・lint-ac の exit 2）が PR 本文に無い |
| F14 | 独立-1 | low | no | self-inflicted | product | accepted | fence の閉じ忘れで 2a が task 名なしで impl-gate に戻す |
| F15 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Part A の見出しと番号付けルールに Step 0 が無い |
| F16 | 独立-1 | low | no | self-inflicted | same-rule-drift | accepted | commands/gdd-dev.md の実装漏れ防止 guard が追随していない |
| F17 | 独立-1 | low | no | self-inflicted | product | accepted | 2a の Reviewed by の有無が、task_name が受け付ける見出しの集合まで狭まった |
| F18 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が抜粋に無い（PR 本文の別の節に書く） |
| F19 | 独立-1 | advisory | no | self-inflicted | product | accepted | gate でない main が Reviewed by 行を書き戻せる。戻してよい形が書かれていない |
| F20 | 独立-1 | advisory | no | self-inflicted | product | accepted | 詳細の欄が tasklist の文を safe_for_output に通さずに出す |
| G1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | Step 0 の新しい文が「行が無いまま Step 1 へ進まない」を消し、exit 2 を invalid の規則の外に置いた。`${CLAUDE_PLUGIN_ROOT}` が空などで再実行しても exit 2 なら、行 0 行のまま各 Step が不備なしと読める。exit によらず、終わりの行が無ければ全 Step・行の無い Step はその Step を invalid にし、行が無いまま Step 1 に進まない（安全策 4 の 1 回目の発火。Opus・Fable とも続行を推し、通す条件を肯定形で書いて既定を反転する文にした。ユーザーの返事は未着で、推奨で進めた）。commit: b8b6da32 |
| G2 | 独立-2 | medium | no | self-inflicted | routing-order | accepted | 終わりの行が無い・exit が 0/1 以外・`_guarded` の行など、道具の故障を各 Step の差し戻し先（impl-gate・TDD など）へ送る。外部前提不足で止める形に分けるには行の status を分ける（閉じ方: 列挙。§ 常時 High の high・blocking ではないので方針メモにしない） |
| G3 | 独立-2 | medium | no | self-inflicted | request-drift | re-reported | F2 の再報告（gate の外で差し戻すか） |
| G4 | 独立-2 | medium | no | self-inflicted | request-drift | re-reported | F4 の再報告（4c・4d・AC Trace Ledger を機械で判定できるのに gate に残す） |
| G5 | 独立-2 | low | no | self-inflicted | request-drift | re-reported | F8 の再報告（CI から回せるのは steering を渡せる環境だけ） |
| G6 | 独立-2 | low | no | self-inflicted | wiring | accepted | 終わりの行の `rows=<n>` を読む側が無く、途中の行だけ落ちた形を検出できない |
| G7 | 独立-2 | low | no | self-inflicted | test-power | accepted | 親の decode の `encoding="utf-8"` と `errors="backslashreplace"` を戻してもテストが落ちない |
| G8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片が終わりの行・行の無い Step の読み方・UTF-8 出力を書いていない |
| G9 | 独立-2 | low | no | self-inflicted | product | accepted | `reconfigure` が `parse_args` の後にあり、非 UTF-8 の stdout で `--help` が落ちる |
| G10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「受け持つ要求のどれにも invalid 行」が unused-symbols に当たらない。exit 2 はスクリプトを開けないときも出る |
| G11 | 独立-2 | low | no | self-inflicted | style | accepted | tasklist の部品の (要求, gate) の組が 2 か所に別々に書かれている |
| G12 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（抜粋の相談役の推奨の 1 文）。次の巡の抜粋から除く |
| pm-7 | 方針メモ-1 | - | - | - | - | - | なし |
| H1 | 独立-3 | medium | no | self-inflicted | routing-order | accepted | スクリプトが完結しない（終わりの行が無い・exit が 0/1 以外が再実行後も続く）とき、Step 0 で止まるが Next Action が決まらないか、各 Step の差し戻し先（impl-gate・systematic-debugging）へ誤送する。外部前提不足として止める形に分ける（G2 と同じ型） |
| H2 | 独立-3 | medium | no | self-inflicted | same-rule-drift | accepted | Checklist E (ii)(b)（古いだけの Route In Progress を自動更新して advisory）と、Step 0 の「route-in-progress の行が ok 以外なら Step 4 の不備・読み直さない」が食い違う（F5 と同じ型） |
| H3 | 独立-3 | medium | no | self-inflicted | request-drift | re-reported | F2 の再報告（gate の外で差し戻すか） |
| H4 | 独立-3 | medium | no | self-inflicted | request-drift | re-reported | F4 の再報告（4c・4d・AC Trace Ledger・3b・2・観点 8 の扱い） |
| H5 | 独立-3 | low | no | self-inflicted | request-drift | re-reported | F8 の再報告（CI から回せるのは steering を渡せる環境だけ） |
| H6 | 独立-3 | low | no | self-inflicted | same-rule-drift | accepted | subagent-dispatch.md の事前確認は remaining-tasks 行だけを見て、exit と終わりの行を見ない |
| H7 | 独立-3 | low | no | self-inflicted | fail-open | accepted | 「引数を直して 1 回だけ実行し直す」で、直してよい範囲（`--steering`・`--root`・`--base` を Template から変えない）が書かれていない |
| H8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「行が無いまま Step 1 の判定に進まない」と exit 2 の原因が PR 本文の変更内容に無い。commit: なし（PR 本文） |
| H9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の「差し戻し先は今までと同じ」が実際と合わず、止める入力が増える点が断片に無い |
| H10 | 独立-3 | low | no | inherited | doc-claim | accepted | Part A の見出しと番号付けルールに Step 0 が無い（F15 と同じ） |
| H11 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | (c) が要求ごとではなく Step ごとの 1 行以上 |
| H12 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | (b) の最後の行が stdout のものか書かれていない |
| H13 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | Skill RED-GREEN Evidence が抜粋に無い（PR 本文の別の節に書く） |
| H14 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（抜粋の「独立レビューの残りが 1 巡」）。PR 本文から除く |
