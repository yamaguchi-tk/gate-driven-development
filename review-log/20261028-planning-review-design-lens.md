---
lane: L1+
pr: 601
follow_up_of: 576
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 09024021 | 0 | 0 | 0 | 2026-10-28 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 09024021 | 0 | 0 | 0 | 2026-10-28 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 546c3d7d | 0 | 4 | 0 | 2026-10-28 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8a36eb36 | 0 | 1 | 0 | 2026-10-28 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2ae04a96 | 0 | 1 | 0 | 2026-10-28 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | 進め方 | accepted | 設計: 変える（記録と hash で design-gating の reviewer を省く仕組みを作らない）。2 本とも、PR-4・B-7 は作らない（低 0/15 は規則でなくタスクの性質と定義による）、PR-5 は数値（3/14 が上がり、下がるもの 0）を添えてユーザーに決め直してもらう、文章・テストだけの PR は 0 件なので作らない、で一致。PR-2・PR-6 は、requirements-gating のレビューを広げてから design-gating を外す形に組み直す点で一致した。割れたのは 6'b の前に測るか（Fable: 測る、Opus: 1 本で、+1,000 行を超えるなら分ける） |
| M2-1 | 方針メモ-2 | advisory | no | self-inflicted | 時間上限 | accepted | 設計: 変える（1 体の reviewer に両方を見させない）。測定で、2 つの planning の 1 巡目の合計は中央値 47 分、13/13 本が 30 分の上限を超える。2 本とも案 Z（requirements-gating の同じ Round で、design phase の文脈の planning と条件の security を並行に起動）を推した。Opus は 6'a・6'b の 2 段を残し、6'a の後 5 本で design-gating の新しい指摘を human check の前からあった内容と後で足した内容に分けて数える案、Fable は足すと外すを 1 本にする案。外す側の仕組みで 旧#583 が fail-open の high を 3 回出したので、何も外さない 6'a を先にする Opus の案を採った |
| I1-1 | 独立-1 | medium | no | self-inflicted | 依頼の範囲 | accepted | 確認待ち: 依頼の原文から外れた（観点 0）: PR-2 の記録と hash、PR-6（design-gating を外す・approved と Cumulative Diff Base を書く）をこの PR に入れていない。PR-2 と PR-6 の見積もりの合計が +900〜1,700 行で +1,000 行を超えうること（手順 6 の (c)）と、外す側の仕組みが 旧#583 で fail-open の high を 3 回出したことから、2 段に分ける推奨の案で進め、PR 本文の限界の節に問いと戻す範囲を書いた |
| I1-2 | 独立-1 | medium | no | self-inflicted | design の観点の範囲 | fixed | design の観点が、旧#576 で human check の前に書く決まりになった配線表と影響範囲の grep の記録の欠けも指摘しない（gdd-planning-reviewer.md の追加段落）。指摘しない対象を template が求めていない記録（5d）に限る修正案。commit: 8a36eb36 |
| I1-3 | 独立-1 | medium | no | self-inflicted | 再入の範囲 | fixed | 再入で起動する reviewer の文に requirements-gating の限定が無く、design-gating の再入で security を回さない読み方ができる（requirements-gating-steps.md:39）。commit: 8a36eb36 |
| I1-4 | 独立-1 | medium | no | self-inflicted | 時間上限 | fixed | 追加した reviewer が時間超過したときの Round の判定が決まっていない。gate runner の中では reviewer ごとの timer を置けない。commit: 8a36eb36 |
| I1-5 | 独立-1 | low | no | self-inflicted | 記録の形 | accepted | Planning Reviewer Selection の新しい key と値 not_applicable が、gate-status-schema・state-machine・completion-check の分担と合わない |
| I1-6 | 独立-1 | low | no | self-inflicted | 同じ規定の別箇所 | accepted | どの gate がどの reviewer を起動するかを書いた別の箇所（Responsibility Matrix、gdd-dev.md:233、security reviewer の description、gate-status-schema、phase-progression）が前のまま |
| I1-7 | 独立-1 | low | no | self-inflicted | 起動の条件 | accepted | task-sizing の行に除外が無く、条件 (1) が運用レベルの上書きを見ない |
| I1-8 | 独立-1 | low | no | self-inflicted | Phase の行 | accepted | Phase の行をどこにあっても受け付け、requirements の観点の 1 枚にこの行が写ると design phase で読まれる |
| I1-9 | 独立-1 | low | no | self-inflicted | 1 枚の名前 | accepted | security reviewer に渡す 1 枚が決まっていない。security の定義に入力の範囲の文が無い |
| I1-10 | 独立-1 | low | no | self-inflicted | 測定 | accepted | 次の判断（design-gating を外すか）を数える欄と閾値が無い |
| I1-11 | 独立-1 | low | no | self-inflicted | design の観点の範囲 | accepted | design phase の節が承認済みの requirements を前提にしたまま。human check の前に何と比べるかが無い |
| I1-12 | 独立-1 | low | no | self-inflicted | 変更断片 | accepted | 断片の type が minor で、requirements gate の reviewer set の変更を breaking 候補とする Policy と合わない |
| I1-13 | 独立-1 | low | no | self-inflicted | PR 本文 | accepted | 挙動の変化に、Selection の行が増えることと、タスク分解の質チェックをしないことが無い |
| I1-14 | 独立-1 | low | no | self-inflicted | PR 本文 | accepted | 15 本から 13 本へ母数が説明なく変わる |
| I1-15 | 独立-1 | advisory | no | self-inflicted | 変更断片 | accepted | Changed に Quick Selection Table が無い。方針の文が断片にある |
| I1-16 | 独立-1 | advisory | no | self-inflicted | design の観点の範囲 | accepted | 2 本の planning reviewer の受け持ちが重なり、同じ開いた述語を Medium と Low で二重に出す |
| I2-1 | 独立-2 | medium | no | self-inflicted | 依頼の範囲 | re-reported | I1-1 の再掲。PR-2 の記録・hash と PR-6 を後回しにしたことへのユーザーの同意が依頼の原文に無い |
| I2-2 | 独立-2 | medium | no | self-inflicted | 時間上限 | fixed | design の観点の組の時間超過の例外が、正本の subagent-dispatch.md「超過・無応答のとき」に無く、gate runner が Round 全体の timeout・blocked とも読める（subagent-dispatch.md:64）。ユーザーが直すよう頼んだ I1-4 の範囲として直す。commit: 2ae04a96 |
| I2-3 | 独立-2 | low | no | self-inflicted | 時間上限 | accepted | SKILL.md の Guardrails「planning reviewer を飛ばして human check に進めない（時間超過の一括提示を除く）」が、design の観点の組の時間超過の例外と字面で合わない |
| I2-4 | 独立-2 | low | no | self-inflicted | 時間上限 | accepted | requirements の観点の reviewer だけが返らず、design・security が blocking を出したときの記録先が決まっていない |
| I2-5 | 独立-2 | low | no | self-inflicted | design の観点の範囲 | accepted | 5d も skeleton の同じ根拠に当たるのに指摘の対象から外したまま |
| I2-6 | 独立-2 | low | no | self-inflicted | design の観点の範囲 | accepted | grep の記録・配線表を条件（規定を変えるとき・新設要素があるとき）なしで指摘する書き方になっている。断片も同じ |
| I2-7 | 独立-2 | low | no | self-inflicted | 時間上限 | accepted | 時間超過の例外は design-gating が後で見ることが前提で、design-gating を外す次の PR で fail-open になる。次の PR で規則を替える必要がある |
| I2-8 | 独立-2 | low | no | self-inflicted | 再入の範囲 | accepted | 処置で design.md を変えても、前回 blocking を出していない security reviewer は再入で起動しない |
| I2-9 | 独立-2 | advisory | no | self-inflicted | design の観点の範囲 | accepted | light の quick (standard) の除外は通常当たらず、1 枚に運用レベルが無いので reviewer が判定できない |
| I3-1 | 独立-3 | medium | no | self-inflicted | 時間上限 | accepted | gate runner の中の reviewer には期限を置かないので、時間超過の例外は reviewer がエラーで返ったときだけ当たる。時間超過は runner の 60 分の停止で Round 全体が timeout になる。PR 本文の限界と断片に書く |
| I3-2 | 独立-3 | medium | no | self-inflicted | 依頼の範囲 | re-reported | I1-1 の再掲。PR-2・PR-6 の残りを条件つきで次の PR に回したことへのユーザーの確認が依頼の原文に無い |
| I3-3 | 独立-3 | low | no | self-inflicted | 時間上限 | accepted | SKILL.md:181 の Guardrails の例外に、design の観点の組だけが返らないときが無い（I2-3 と同じ箇所） |
| I3-4 | 独立-3 | low | no | self-inflicted | 時間上限 | accepted | 但し書きの「組だけが返らない」が組の全体とも読め、reviewer ごとに扱う Step 5 より狭い |
| I3-5 | 独立-3 | low | no | self-inflicted | 時間上限 | accepted | 断片の Changed に、時間超過の正本の変更が載っていない |
| I3-6 | 独立-3 | advisory | no | self-inflicted | 時間上限 | accepted | 但し書きに design-gating がある経路に限る前提が書かれていない（I2-7 と同じ前提） |
| I3-7 | 独立-3 | advisory | no | self-inflicted | 依頼の範囲 | out-of-diff | PR 本文の 15 本と 13/13 本の分母の食い違い |
