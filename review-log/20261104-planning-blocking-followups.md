---
lane: L1
pr: 635
amends: 20261104-planning-blocking-rule.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f5ef41b11092586cc269518dfb8a3b4d90d5b96c | 0 | 3 | 1 | 2026-11-04 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d19d92313bb1a5d80edc506b09e9048a7b262265 | 0 | 1 | 0 | 2026-11-04 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 設計: 変える（安全境界の指摘を HCQ に移せるようにしたのに、移した項目を事前回答の人に戻す条件に入れていなかった）。委任先なしの事前回答では AI の仮決定で安全境界の blocking が閉じた。安全境界の項目を移した human check を § 事前回答 3 の人に戻す条件に足し、正本から指す。commit: d19d92313bb1a5d80edc506b09e9048a7b262265 |
| I1-2 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の 3（下げてよい場合と同じ正本の別の規則の食い違い）が、(b) を 3 つの規則で閉じたため、欄の浅さ・文言・failure scenario の無い指摘の規則で残っていた。(b) を規則の置き場所で書いた。commit: d19d92313bb1a5d80edc506b09e9048a7b262265 |
| I1-3 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の 2（迷った指摘が no で通る）を直す規則を Uncertainty Rule にだけ書いたので、正本と reviewer に渡す 1 枚に届かなかった。迷ったときの扱いを正本に書き、Uncertainty Rule は正本を指す。commit: d19d92313bb1a5d80edc506b09e9048a7b262265 |
| I1-4 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の対象の I1-6（旧#634）が、正本と 旧#634 の断片で「implementation 段階の数え方」のまま残っていた。「requirements / design 段階を除く」に揃えた。commit: d19d92313bb1a5d80edc506b09e9048a7b262265 |
| I1-5 | 独立-1 | low | no | self-inflicted | rule-copy | accepted | planning reviewer の :374 が、requirements-gating から design の観点で起動した reviewer にも開いた述語を Low と指示し、表と逆になる |
| I1-6 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | HCQ に移した解除の記録を reviews.md に書く規定と欄が無い |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 旧#634 の断片の (b) の説明が「など」で開いた形だった。正本の置き場所の書き方に揃えた。commit: d19d92313bb1a5d80edc506b09e9048a7b262265 |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 新しい断片の Summary に `is_blocking` の「単独正本」の文の変更が無かった。commit: d19d92313bb1a5d80edc506b09e9048a7b262265 |
| I1-9 | 独立-1 | low | no | self-inflicted | rule-copy | accepted | phase-progression の E2E Discovery Loop の「human check に戻す条件」に、policy-level の blocking を足していない |
| I1-10 | 独立-1 | low | no | inherited | bookkeeping | accepted | design-gating 手順 9 が advisory の書き先を design.md・worklog.md とし、正本の reviews.md への注記と分かれる |
| I1-11 | 独立-1 | advisory | no | self-inflicted | budget | accepted | design-gating SKILL の字数が増えた。token 予算は validate-plugin.sh で確かめる |
| I1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 旧#634 の断片をこの PR の後の状態に書き換え、新しい断片はリリースされていない中間の状態からの変化として書いている |
| I1-13 | 独立-1 | advisory | no | self-inflicted | style | accepted | 正本の「§ 常時 High の 4 型」にファイル名が無い。欄が無いときの文が HCQ の箇条の中に入った |
| I2-1 | 独立-2 | medium | no | self-inflicted | safety-exemption | accepted | 列挙: (b) の置き場所に「この節」全体を入れたので、文言・精度の規則や迷ったときの規則を根拠に、gate が安全境界の `blocking: yes` も advisory に下げられ、人の目に触れない。安全境界と design の policy-level は下げずに人に見せる案 |
| I2-2 | 独立-2 | low | no | self-inflicted | rule-copy | accepted | 列挙: requirements-gating SKILL の AC Quality Check（HCQ が 2 個を超えるなど）の advisory の規則が、(b) の置き場所の外にある |
| I2-3 | 独立-2 | low | no | self-inflicted | approval-path-scope | accepted | § 事前回答 3 の新しい条件が、どの human check かを限っておらず、後の human-recheck などでも人に止まる（止まる側） |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 正本の「当たるかで迷ったとき」が何に当たるかを書かず、迷った安全境界の failure scenario に「何が壊れる・漏れるか」が落ちている |
| I2-5 | 独立-2 | advisory | no | inherited | doc-claim | accepted | :13 の「適用範囲の 4 型」と :14 の「4 型」が揃っていない |
| I2-6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 旧#634 の断片を最終の形に書き換えたので、同じ変更が 2 つの断片に重なる |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「事前回答（委任）があっても」の括弧が、委任先なしの事前回答を外すように読める |
| I2-8 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | HCQ に移した項目の印が自由文で、main が移した安全境界の項目だと見分けられないことがある |
