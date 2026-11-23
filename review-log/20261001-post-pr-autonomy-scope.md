---
lane: L1
pr: 旧#260
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | cdf37056fc3a38eb0efc5e9a5ab3c2d87f87e5e5 | 1 | 5 | 3 | 2026-10-01T01:06+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | e14edcec1a96fbf4cf3928a142378aa94f0669eb | 0 | 1 | 1 | 2026-10-01T01:34+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 0666ddfc67f974d3e9bfb330f7bd9f4f34242ac5 | 0 | 0 | 0 | 2026-10-01T01:49+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| H1 | 独立-1 | high | no | self-inflicted | wiring | fixed | 手順 7 は completion-check の runner の中で走り、done で戻った後に main が post-merge-qa.md の手順 2〜5 へ進む経路が無い commit: 571169e7 |
| M1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | マージと QA の書き込みを 1 回の承認に束ね、1 操作ごとの明示承認の規定と食い違う。承認の提示にデプロイが無い commit: 571169e7 |
| M2 | 独立-1 | medium | yes | self-inflicted | fail-open | fixed | 手順 5 の revert PR は active な steering の pre-push・pre-PR gate に止められ、書かれたとおりに作れない commit: 571169e7 |
| M3 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 新しい 2 値の「レビュー収束」が Auto-Arm の発火条件につながっていない commit: 571169e7 |
| M4 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 手順 2 の条件に merge gate の証跡が無く、拒否時に不完全な根拠でマージのコマンドを渡す commit: 571169e7 |
| M5 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | Option 1 の範囲と PR 作成後に done を出す条件を定める他の箇所が変わっていない commit: 571169e7 |
| L1 | 独立-1 | low | yes | self-inflicted | security-boundary | fixed | 宣言を読む時点が決まっておらず、マージ後に読むと PR 自身の .gdd-config.md の変更が効く commit: 571169e7 |
| L2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 新しい hook のテストの状態が、実際に QA を起動する時点（Next Action=done）と違う commit: 571169e7 |
| L3 | 独立-1 | low | no | self-inflicted | product | fixed | git revert -m 1 がマージ方式を前提にしている commit: 571169e7 |
| L4 | 独立-1 | low | no | self-inflicted | product | fixed | 手順 3 に run を待つ時間の決まりが無い commit: 571169e7 |
| L5 | 独立-1 | low | no | self-inflicted | product | fixed | subagent_type が prefix なしで、agent 定義が見つからないときの扱いが無い commit: 571169e7 |
| L6 | 独立-1 | low | no | self-inflicted | product | fixed | 「マージまで」の止めることにデプロイがあり、マージで走る CD と合わない commit: 571169e7 |
| L7 | 独立-1 | low | no | self-inflicted | product | fixed | Deploy Paths の判定が rename を見落とし、glob の意味も決まっていない commit: 571169e7 |
| L8 | 独立-1 | low | no | self-inflicted | product | fixed | Codex・Cursor で QA runner を起動するときの委譲の許可とツールの制約が無い commit: 571169e7 |
| L9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | fixed-models.md の model 省略の免除の列挙に gdd-qa-runner が無い commit: 571169e7 |
| L10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | brainstorming の自走上限の値の列挙が変わっていない commit: 571169e7 |
| L11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片に 2 つの削除とテストのファイルの書き漏れがある commit: 571169e7 |
| L12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に削除と承認の範囲の書き漏れがある commit: なし（PR 本文） |
| L13 | 独立-1 | low | no | self-inflicted | product | fixed | QA 計画のレビューの起動の型と effort の扱いが決まっていない commit: 571169e7 |
| A1 | 独立-1 | advisory | no | self-inflicted | product | fixed | qa-plan.md にアカウント ID を含む ARN や絶対パスを書くと steering の書き込み検査に止められる commit: 571169e7 |
| A2 | 独立-1 | advisory | no | self-inflicted | style | accepted | operation-levels.md の新しい見出しの直後に空行が無い |
| A3 | 独立-1 | advisory | no | self-inflicted | product | accepted | git fetch では既存の origin/HEAD が更新されず、既定ブランチの改名後に古い枝を読みうる |
| R2-1 | 独立-2 | medium | yes | self-inflicted | data-loss | fixed | 自走上限が 2 値のとき、優先の規定が Step 4 と completion-check まで広がり、ユーザーが明示した Post-PR Completion Scope を扱う場所が無くなる commit: 414687cd |
| R2-2 | 独立-2 | medium | no | self-inflicted | wiring | next-pr | post-merge-qa への入口が subagent からの復帰だけで、completion-check を main で動かす経路と中断後の再開から入れない |
| R2-3 | 独立-2 | medium | no | self-inflicted | product | next-pr | human check の一次表示（compact）が「OKでも許可されないこと: merge / deploy」を固定で持ち、2 値と食い違う |
| R2-4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | completion-check の「（と Auto-Arm の収束）」が 2 値では起きない |
| R2-5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 自走上限を読む場所が main（Approved Direction）と runner でそろっていない |
| R2-6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「QA を起動する時点では dispatch gate は判定しない」が、tasklist.md に前の工程が残る場合と general-purpose の経路を落としている |
| R2-7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | dispatch gate のテストの同じ関数に、起動元の古いコメントが残る |
| R2-8 | 独立-2 | low | no | self-inflicted | product | next-pr | 宣言を 1 回だけ読む時点が human check の読み取りと重なり、読み直して宣言が変わったときの扱いが無い |
| R2-9 | 独立-2 | low | no | self-inflicted | product | next-pr | QA 計画をレビューした head を、マージする head と照合しない |
| R2-10 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | Deploy Paths の比較コマンドの merge-base が決まっておらず、文末の文法が誤り |
| R2-11 | 独立-2 | low | no | self-inflicted | test-power | next-pr | references の行数の上限に、実測より 10 行の余裕が残る |
| R2-12 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 自走上限の値の列挙が human-check-template と requirements-template に残り、外部レビュー収束の値が表に無い |
| R2-13 | 独立-2 | low | no | self-inflicted | product | next-pr | QA 計画のレビューに Codex・Cursor の起動先と、起動できないときの扱いが無い |
| R2-14 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 外から見える挙動の一部（.gdd-config.md を変える PR、拒否時の扱い、revert を作らない場合など）が PR 本文と変更断片に無い |
| R2-15 | 独立-2 | low | no | self-inflicted | product | next-pr | 新しい分岐が、Option 1 で PR を作ったことを条件にしていない |
| R2-16 | 独立-2 | advisory | no | self-inflicted | product | accepted | QA 計画のレビュアーへの prompt に「計画のコマンドを実行しない」が無い |
| R3-1 | 独立-3 | medium | no | self-inflicted | wiring | next-pr | Post-PR Completion Scope がある場合の除外が、完了条件に「マージ」を含むと Scope を必須にする既存の規定と重なり、2 値を頼んでも新しい経路に入らない（従来の止まる経路に戻る） |
| R3-2 | 独立-3 | low | no | self-inflicted | product | next-pr | 「Post-PR Completion Scope が無い」の判定（none の扱い、見る場所）が決まっておらず、main と runner で分かれうる |
| R3-3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | post-completion-pr-flow.md 手順 7 の「…より優先する」が、条件を絞った後は意味を持たない |
| R3-4 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | Option 1 冒頭の 2 値の文に Post-PR Completion Scope の条件が無い |
| R3-5 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | post-merge-qa.md の入口の説明に、Post-PR Completion Scope があるときの除外が無い |
| R3-6 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 変更断片が Post-PR Completion Scope があるときの除外を書いていない |
| R3-7 | 独立-3 | low | no | inherited | product | next-pr | Completion-Check Post-Return Routing の「それ以外」の分岐は、Scope があって runner が blocked で止まったときも完了サマリーを出す |
| R3-8 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋の「（ユーザー承認）」） |
| R3-9 | 独立-3 | advisory | no | self-inflicted | doc-claim | re-reported | dispatch gate のテストの同じ関数に、起動元の古いコメントが残る（R2-7 の再報告） |
| R3-10 | 独立-3 | advisory | no | self-inflicted | doc-claim | re-reported | requirements-template の Approved Direction の自走上限の値の欄が表と合っていない（R2-12 の再報告） |
