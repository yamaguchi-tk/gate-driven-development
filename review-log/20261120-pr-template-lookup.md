---
lane: L1
pr: 719
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4e60380d | 0 | 2 | 0 | 2026-11-20 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| 独立-1-1 | 独立-1 | medium | no | self-inflicted | coverage | accepted | GDD 側の探し方は bundled の pr-review.md（上流 pr-review が無いときのフォールバックで、上流と同期する対象）にしか入らず、上流を入れた環境と次の同期で効かない |
| 独立-1-2 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | git ls-files はカレントディレクトリより下しか列挙せず、cwd がサブディレクトリだと root のテンプレートを見落とす |
| 独立-1-3 | 独立-1 | low | no | self-inflicted | coverage | accepted | 列挙: subshell・pipeline の左側でのグロブの失敗は終了コード 0 で終わりうり、PostToolUseFailure の hook が出ない |
| 独立-1-4 | 独立-1 | low | no | self-inflicted | coverage | accepted | 列挙: hook は debug-and-review を入れて更新したセッションでだけ効く。version は据え置き |
| 独立-1-5 | 独立-1 | low | no | self-inflicted | coverage | accepted | 列挙: 普通の会話で PR を作る plain-writing の rules.md には探し方が入っていない |
| 独立-1-6 | 独立-1 | low | no | self-inflicted | test-power | accepted | テストが hooks.json の command を shell で実行せず、python3 を落としても通る |
| 独立-1-7 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | テストの名前が assert の中身より広い |
| 独立-1-8 | 独立-1 | advisory | no | self-inflicted | product | accepted | 正規表現が行番号の無い zsh のエラーの形を拾わない |
| 独立-1-9 | 独立-1 | advisory | no | self-inflicted | product | accepted | hook の起動に -X utf8 を付けていない |
| 独立-1-10 | 独立-1 | advisory | no | self-inflicted | product | accepted | コマンド由来のパターンを切り詰めずに additionalContext に入れている |
| 独立-1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | manifest と marketplace の description に hook が書かれていない |
| 独立-1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の件数と依頼の件数で数えた範囲の違いが書かれていない |
| 独立-1-13 | 独立-1 | advisory | no | self-inflicted | product | accepted | 探し方が org の既定テンプレートを拾わず、GitHub が使わない置き場にも一致する |
