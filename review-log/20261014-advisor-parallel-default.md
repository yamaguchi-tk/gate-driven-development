---
lane: L1
pr: 510
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 094aad85 | 0 | 4 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 1477e164 | 0 | 6 | 0 | 2026-10-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 696a37b6 | 0 | 2 | 0 | 2026-10-14 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | d16a2906 | 0 | 3 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | request-drift | next-pr | 自律モードの判断役を並行にしていない。ユーザーに確かめ、判断役の仕組み自体を自走の範囲の選択肢として作り直したいとの回答だったので、別の課題として次の PR で扱う（.request.md に回答を写した） |
| A2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 限界の種類が相談役の出力にだけ入り、人が判断する面に届かない。common-guardrails の Honest Limitations に種類を置き、requirements テンプレート・Handoff の限界から書かせた。commit: 6412d10d |
| A3 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 選択肢に無い案を推す条件が、閉じる設計変更・撤去を推せない形に狭めていた。基準 2・4 の案が並んでいないときも推せるようにした。commit: 6412d10d |
| A4 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 基準 5 が、GDD の hook に限った決定を全 repo の全相談に広げていた。GDD 自身の hook・gate に限り、利用者の製品の信頼境界には当てないと書いた。commit: 6412d10d |
| A5 | 独立-1 | medium | no | self-inflicted | product | accepted | 試行の戻す条件（20 件・割れた件の選択）を数える記録の置き場が無い。transcript から手で数える。PR 本文の限界に書く |
| A6 | 独立-1 | low | no | self-inflicted | product | accepted | 基準 7 の「だけである」が、autonomy の止まる案・事前回答 3 の人に戻す一覧と食い違う。main が一覧を別に強制するので承認の経路は迂回されない |
| A7 | 独立-1 | low | no | self-inflicted | product | accepted | 項目 7 の「同じ材料で片方を済ませていれば」の例（autonomy の判断役・事前回答の委任先）は、材料と問いが項目 7 と違う |
| A8 | 独立-1 | low | no | self-inflicted | product | accepted | 戻す条件はユーザーの選択との一致を測り、並べる目的（片方だけが拾う点）を測っていない |
| A9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | fixed-models に足した数字の記録の場所と、測った版と出荷した文の違いが書かれていない |
| A10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「28〜30」の 30 がどの組の値か書かれていない（high＋Fable は 28） |
| A11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Handoff も 2 本を起動すること、片方だけ済ませたときの形、unavailable の書き方の変化が断片と PR 本文に無い |
| A12 | 独立-1 | low | no | self-inflicted | product | accepted | root CLAUDE.md の全レーン共通（Fable を Opus と並べない）が、項目 7 と反対のまま残る。ユーザーの回答で、旧#495 のマージ後にこの PR に足す |
| A13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の検証欄に、本文の一致を固定するテストと根拠の評価が書かれていない |
| A14 | 独立-1 | advisory | no | self-inflicted | product | accepted | Codex・Cursor では項目 7 の Fable が毎回 unavailable になる |
| A15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | fixed-models の起動する場面の括弧に項目 7 が無い |
| A16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Fable の description の役（ユーザーならどれを選ぶかの代わり）が、項目 7 に入れた理由（片方だけが拾う点）と向きが違う |
| A17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 狭める理由にしない語の一覧が、CLAUDE.md の方針メモの規定と違う |
| B1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 依頼は既定なのに、試行と自動で戻す条件を足した。試行と戻す条件を項目 7・fixed-models・CLAUDE.md・断片から消した。commit: 6ecadc53 |
| B2 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 既定を確認の前の相談だけに絞り、安全策 1・4 と方針メモ-N は Opus だけだった。CLAUDE.md の相談を Opus と Fable の並行に揃え、reviewer 列・Fable の信号 ① を合わせた。commit: 6ecadc53 |
| B3 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | CLAUDE.md:61 が全レーン共通の Opus への相談を指していた。並行の相談を指すようにした。commit: 6ecadc53 |
| B4 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | human check の まだ確認できないこと に限界の種類が届いていない。項目の書式と規定に種類を足した。commit: 6ecadc53 |
| B5 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | GDD の PR 本文の Known limitations と rollback の書式に種類の規定が無い。種類を書く規定を足した。commit: 6ecadc53 |
| B6 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 断片が自律モードの判断役を変えないと書くが、本文の基準は判断役にも当たる。起動の仕方は変えず、基準は当たると書いた。commit: 6ecadc53 |
| B7 | 独立-2 | low | no | self-inflicted | product | fixed | 試行の測り方が並べる理由を測っていない。試行と戻す条件を消したので測る対象が無くなった。commit: 6ecadc53 |
| B8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の同じ規定が 2 通りに書かれている |
| B9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | fixed-models の数字が、配布した基準の文を測った値に読める |
| B10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界の種類の付け方が定義と合わない（PR 本文で直す） |
| B11 | 独立-2 | low | no | self-inflicted | product | accepted | 同じ相談を 2 回呼ぶ経路があり、使い回しの規定が無い |
| B12 | 独立-2 | low | no | self-inflicted | product | accepted | 基準 5 の守る範囲が CLAUDE.md の規定と合わない |
| B13 | 独立-2 | low | no | self-inflicted | product | accepted | 基準 0 の受け入れた形が、何の記録を数えるかを決めていない |
| B14 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 限界の種類の定義が 2 系統あり、そろえる規定が無い |
| B15 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | requirements テンプレートの テストで担保できない部分 が common-guardrails と合わない |
| B16 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | Fable の役の文が、並べる理由と合わない |
| B17 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | fixed-models の段落の冒頭が、項目 7 での起動を挙げていない |
| B18 | 独立-2 | advisory | no | self-inflicted | product | accepted | 依頼の数値の出典が本文で明示されていない |
| B19 | 独立-2 | advisory | no | self-inflicted | product | accepted | Honest Limitations の 依頼より狭い は承認の記録にならない |
| B20 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | Skill RED-GREEN Evidence が抜粋に無い（PR 本文に書く） |
| B21 | 独立-2 | advisory | no | self-inflicted | product | accepted | runtime の token 上限を超えるおそれ（validate-plugin.sh の token 見積もりは通っている） |
| B22 | 独立-2 | advisory | no | self-inflicted | doc-claim | re-reported | 28〜30 の 30 がどの組の値か無い（A10 の再掲） |
| B23 | 独立-2 | advisory | no | self-inflicted | bookkeeping | re-reported | 断片の検証の欄が根拠の評価を挙げていない（A13 の再掲） |
| B24 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | compact の欄が書式を示さない |
| C1 | 独立-3 | medium | no | self-inflicted | doc-claim | fixed | 安全策 1 の手順 3 が Opus の推奨だけを載せる形のまま。2 本の推奨と割れた点を載せる形にした。commit: 0b895c17 |
| C2 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | 方針メモ-N に、依頼が既定に付けた条件（観点を前回の答えから作らない・割れた点の扱い）が無い。CLAUDE.md の方針メモ-N の項に足した。commit: 0b895c17 |
| C3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | Claude Code 以外で読むときの行が、消えた句「Opus を呼べないとき」を引いている |
| C4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 安全策 4 の Opus は材料を出すだけ・手順 5 の Opus の案と並べる、が Opus だけを名指ししている |
| C5 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | 方針メモで 2 本とも呼べなかったとき、Fable の unavailable が記録に残らない |
| C6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | AGENTS.md の依頼なしに行ってよい送信の列挙に、Fable への相談が無い |
| C7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | common-guardrails の種類の適用先の列挙に、PR 本文の Known limitations と Handoff の まだ確認できていないこと が無い |
| C8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の Affected Files と種類の適用先に post-completion-pr-flow が無い |
| C9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋の種類の適用先と、費用・unavailable の限界が安全策 1・4・方針メモ-N を挙げていない（PR 本文で直す） |
| C10 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | fixed-models の「人に表示する前の相談だけは」が、repo の規則が他の相談でも並べることと合わない |
| C11 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 10-03 の「安全策 4 の発火だけでは Fable を呼ばない」を、置き換えた記録なしに消した |
| C12 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | output-format の まだ確認できていないこと と、rollback の PR 本文の草案の限界に種類の指示が無い |
| C13 | 独立-3 | low | no | self-inflicted | product | accepted | 割れた件でユーザーがどちらを選んだかを決まった場所に残す規定が無くなった |
| C14 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 限界の未測の列挙に、HITL・Handoff・PR 本文に足した種類が無い（PR 本文で直す） |
| C15 | 独立-3 | advisory | no | self-inflicted | product | accepted | 自律モードの判断役を次の PR で扱う時機は、ユーザーの発言に無く main が決めた |
| C16 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋の限界に、確認の経緯を語る文） |
| D1 | 独立-4 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 自律モードの判断役の作り直しを次の PR に回した時機を、ユーザーに確かめていない。返事を待たない確認として出した |
| D2 | 独立-4 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 事前回答の委任先を、確認なしに並行の対象から外した。返事を待たない確認として出した |
| D3 | 独立-4 | medium | no | self-inflicted | advisor-split | accepted | 2 本が割れて main が決めきれないとき、返事を待たずに推奨で進む 2 か所（依頼の原文の確認、安全策 4 の 1 回目）で進む案が決まらない |
| D4 | 独立-4 | low | no | self-inflicted | changelog | accepted | 変更断片に post-completion-pr-flow.md と PR 本文の Known limitations が無い |
| D5 | 独立-4 | low | no | self-inflicted | changelog | accepted | 変更断片の、選択肢に無い案を推す条件と compact の書式の書き方が本文と合わない |
| D6 | 独立-4 | low | no | self-inflicted | doc-ref | accepted | Claude Code 以外で読むときの行が、消えた句「Opus を呼べないとき」を引き、Fable の側が無い |
| D7 | 独立-4 | low | no | self-inflicted | doc-ref | accepted | 手順 5 と安全策 4 の続行の行が Opus だけを名指ししたまま |
| D8 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | 方針メモ-N で 2 本とも呼べなかったとき、Fable の unavailable を書く規定が無い |
| D9 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | requirements テンプレートの「ユニットテストでは担保できない部分」が「テストで担保できない部分」に変わった |
| D10 | 独立-4 | low | no | self-inflicted | limit-kind | accepted | Honest Limitations に入る条件（できないと断定できるもの）と、足した限界の種類が合わない |
| D11 | 独立-4 | low | no | self-inflicted | limit-kind | accepted | 限界の種類を書かせる面の列挙が、実際の面（PR 本文の Known limitations、rollback の 4 つ目の案、output-format の停止本文）とずれる |
| D12 | 独立-4 | low | no | self-inflicted | criteria | accepted | 基準 7 が、autonomy.md の止まる案と事前回答 3 の一覧と逆を向いて読める（main は一覧を照らすので止まる） |
| D13 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に、root CLAUDE.md の文の削除と max の規定の書き換えが無い |
| D14 | 独立-4 | low | no | self-inflicted | limit-kind | accepted | PR 本文のリスクが低いの限界に、件数も未測も無い |
| D15 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | HITL 出力契約を変えた分の Skill RED-GREEN Evidence が抜粋から見えない（PR 本文の別の節にある） |
| D16 | 独立-4 | low | no | self-inflicted | doc-ref | accepted | AGENTS.md の、依頼なしに送ってよい相談の一覧に Fable が無い |
| D17 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 2026-10-14 の数値の記録が repo の外にしかない |
| D18 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | Fable の役は欠陥を先に見つけることではない、の文が並行の目的と食い違って読める |
| D19 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | 2 本が割れた件とユーザーの選択を残す規定が無い |
| D20 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | rationale の日付と、置き換えた旧文の扱いが読めない |
| D21 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | Claude Code の環境ごとに fable を受け付けるかは未測 |
| D22 | 独立-4 | advisory | no | self-inflicted | product | accepted | runtime の token 上限の余裕は reviewer が確かめられない（validate-plugin.sh は rc=0） |
