---
lane: L1
pr: 638
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 619d93f4d0af9381a025d28abda09dbb19cc3300 | 0 | 1 | 0 | 2026-11-06 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | snapshot-fidelity | accepted | git の出力を text で読むので、CRLF が LF に変わったまま worktree.diff に書かれ、UTF-8 でないバイトでは meta.json（HEAD）ごと欠ける |
| I1-2 | 独立-1 | low | no | self-inflicted | snapshot-fidelity | accepted | git diff が利用者の設定（color・diff.external・noprefix・textconv）を読むので、当て直しに使えない形になりうる |
| I1-3 | 独立-1 | low | no | self-inflicted | error-log | accepted | 保存先が無いうちの失敗は errors.log に書けず消える。途中で落ちたディレクトリが完成品と同じ名前で残る |
| I1-4 | 独立-1 | low | no | self-inflicted | test-power | accepted | errors.log に書く経路を通るテストが無い |
| I1-5 | 独立-1 | low | no | self-inflicted | test-power | accepted | 新しい hook の kill switch が効くことを確かめるテストが無い（config の grep で先に抜ける） |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-copy | accepted | README の Hooks 表の PreToolUse の本数（16）と Agent matcher の列挙に新しい hook が無い |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-copy | accepted | docs/SECURITY.md の hook ごとの読む範囲・書き込み先に、新しい hook の分が無い |
| I1-8 | 独立-1 | low | no | self-inflicted | coverage | accepted | steering を 1 つに決められないとき（binding の worktree が cwd と違う配置など）や HOME が unset のとき、何も残さず理由も書かない |
| I1-9 | 独立-1 | low | no | self-inflicted | coverage | accepted | tool_input の prompt・model と plugin の版を保存しておらず、当て直しの材料が transcript の保持に依存する |
| I1-10 | 独立-1 | advisory | no | self-inflicted | request-scope | accepted | 既定 off なので、利用者が設定の行を足すまで計測が始まらないことが PR 本文から読み取りにくい |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の tool_use_id と transcript の結び付き、容量の見積もり（diff を含まない）に根拠が無い |
| I1-12 | 独立-1 | advisory | no | self-inflicted | config-read | accepted | 有効にする判定がコードフェンスや HTML コメントの中の行も on として読む |
| I1-13 | 独立-1 | advisory | no | self-inflicted | path-safety | accepted | tool_use_id をそのままディレクトリ名に使い、保存物は umask のまま作る |
