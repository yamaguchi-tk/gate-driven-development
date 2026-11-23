---
lane: L1
pr: 旧#250
follow_up_of: 249
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fed9423afe834dd50786fc03b538f4ce69b54187 | 0 | 0 | 0 | 2026-09-30T15:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus（reviewer が review-log/ を除かない Grep を 1 回実行し、一致した語だけが表示されたと報告。判断には使っていないとの申告） | 939bed68bb0dd18812c6dfe07e5892888baeea44 | 0 | 0 | 0 | 2026-09-30T16:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | test-power | fixed | from_agent の not model の側を固定するテストが無く、明示した model の起動に「model を省略したこの agent」と出る変異が通った。明示した model の案内を確かめるテストを足した。commit: 1a3ec5e4 |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | sonnet の worker への案内が、自分で参照する手順 3 と食い違い、Worktree・Plugin Root も伝えていなかった。先に Next Action を確かめるよう促し、この工程のまま起動するなら heavy（Gate Rounds 2 以上は remediation）と受け渡しを伝える。commit: 8b0c9d1c |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 実装の工程の案内のテストが ## Worktree を固定していなかった。assert を足した。commit: 1a3ec5e4 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | gdd-model-routing の「4 段階で扱う」と 5 つ目の max が同じ行で食い違った。通常は 4 段階、max は用途を限る、にした。commit: 8b0c9d1c |
| F5 | 独立-1 | low | no | inherited | doc-claim | fixed | Review Set が指す Step 3 と、正本の reviewer-selection.md § Gate Rules の列挙が一致しない。Review Set と fixed-models の security-sensitive を、両方を指す（どちらかに当たれば selected）形にした。commit: 8b0c9d1c |
| F6 | 独立-1 | advisory | no | inherited | doc-claim | accepted | gdd-systematic-debugging § Fixed Model と subagent-dispatch.md:48 の remediation worker の要約に Worktree・Plugin Root が無い（worker は無ければ NEEDS_CONTEXT で返す） |
| F7 | 独立-1 | advisory | no | inherited | doc-claim | accepted | task-breakdown の雛形の Depends on: Task ... / なし が、正準形（none、Task ID のリスト）と違う |
| F8 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 既存テストの assertNotIn('model="sonnet" を明示') が、案内の言い回し（間に「か "opus"」が入る）の偶然で通っている |
| F9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | sonnet の worker への案内の「先に Next Action を確かめて」が、Resume From で工程が決まった場合（planning 中の起動）には工程を決めなかった欄を指す |
| F10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | hook の案内で heavy は prefix 付き、remediation worker は prefix なしの名前で、そのまま subagent_type に使うと解決されるか未確認 |
| F11 | 独立-2 | low | no | inherited | doc-claim | accepted | post-completion-learning.md:90 が security reviewer の条件を Step 3 の列挙だけで書き写し、§ Gate Rules にだけある条件が抜けている |
| F12 | 独立-2 | low | no | inherited | doc-claim | accepted | 正本と宣言した reviewer-selection.md § Gate Rules に、Step 3 にだけある「LLM 呼び出し・エージェント実装」が無い |
| F13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 旧#249 の未リリース断片が、security-sensitive を Step 3 だけに揃えた古い定義のまま（リリース時に版の節で揃える） |
| F14 | 独立-2 | advisory | no | self-inflicted | style | accepted | gdd-model-routing:112 の「通常 4 段階を使い」が頻度の文に読め、:113 の「xhigh は限定使用」と並ぶ |
