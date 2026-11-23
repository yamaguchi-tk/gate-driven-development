---
lane: L1
pr: 旧#509
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 755e5b1ab63e9754c6adf40f8f96c5bc25d9b260 | 0 | 1 | 0 | 2026-10-15T13:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 0ac8cf7aab901bf9accaa5fcda9b3d8898343d49 | 0 | 0 | 0 | 2026-10-15T13:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 判定の関数を直接呼ぶテストだけで、SupersedingAdrContractTests の setUp の配線を壊しても通る commit: 0ac8cf7aab901bf9accaa5fcda9b3d8898343d49 |
| r1-2 | 独立-1 | low | no | self-inflicted | style | accepted | repository_identity.py の読み込みを、共有ローダ load_plugin_module() を使わずに手で書いている |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | repository_identity.py と test_repository_identity.py の docstring が、呼び出し元を 2 本の check スクリプトだけと書く（plugin の scripts/ は判定のコードなので、この PR では触らない） |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の、同期先で確かめたという記述に、コマンドと sha と結果が無い commit: なし（PR 本文） |
| r1-5 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の grep の結果と同期先で確かめた記述は、実装の経緯で、差分が変える挙動ではない |
| r1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | このテストは先に配置の一致を見るので、check スクリプトと「同じ判定」とまでは言えない。配置の検査が要る理由が docstring から消えた |
| r1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | import の時点で repository_identity.py を読むので、読めないとファイル内の全部のテストが収集で error になる |
| r1-8 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | "gate-driven-development" を関数に直書きしており、check スクリプトの MARKETPLACE_NAME との一致を確かめるテストが無い |
| r1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 同期先で skip になる条件（manifest が無いか name が別）と、落ちる・error になる条件が PR 本文の限界に無い |
| r1-10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片と対になる review-log がまだ無く、validate-plugin.sh が review-log-present で落ちる |
| r1-11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | skip の条件を広げるので、近道（全差分巡 1 回）を使えるかは main の判断になる |
| r2-1 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文がテストを 5 本と書くが、setUp を通す 3 本を足して 8 本になった commit: なし（PR 本文） |
| r2-2 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 断片の Validation 欄にテストの件数を書いており、CHANGELOG.md § Policy の「件数を書かない」に反する |
| r2-3 | 独立-2 | low | no | self-inflicted | test-power | accepted | setUp を通すテストが skip・error の件数だけを見て、理由（RuntimeError・skip の文言）を固定しない |
