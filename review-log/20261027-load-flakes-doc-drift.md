---
lane: L1
pr: 591
amends: 20261027-parallel-suite-load-flakes.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 713c86da7bdeb62dd1059a2cc91529ba31a9e762 | 0 | 1 | 0 | 2026-10-27T18:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 0d54f27f7cf8807675a18b5f4d048c302cdce944 | 0 | 0 | 0 | 2026-10-27T18:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | docs/learned-patterns.md:17 の追記は、hook を起動するテスト全体が hang_guard_seconds を使い、本番の timeout に収まるかを CPU 時間と backstop で見ると読める。実際は literal の打ち切りのテストが残り、大半のテストは本番の timeout に収まるかを見ていない |
| r1-2 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-27 22:48、項目 1 全体と読む案で直した）: 依頼の「断片の本数」を本数だけと読み、同じ項目の nudge の要約のずれを確かめずに外した。Opus・Fable の推奨（項目 1 全体と読んで直す）で直した（commit: 0d54f27f7cf8807675a18b5f4d048c302cdce944） |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | test_timing_budget_contract.py:1 の括弧が関数を 2 つしか挙げず、同じ docstring の「3 関数」と食い違う |
| r1-4 | 独立-1 | low | no | inherited | doc-claim | accepted | docs/adr/2026-09-11-merge-gate-quoted-operator.md:69 と test_merge_gate_hook_quoted_operator.py:377-382 が、今も「本番と同じ 10 秒」と書く |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | learned-patterns:17 の更新の注記が項の末尾にあり、見出しは古い規定のまま（同じファイルの他の注記は見出しの直後） |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR X-37 Decision 5 の「末尾の Consequences を参照」は、Consequences が末尾の節でなく、指す行も最後の行でない |
| r1-7 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | PR 本文の限界の行に Honest Limitations の種類が無い。PR 本文で直す（commit: なし（PR 本文）） |
| r1-8 | 独立-1 | advisory | no | inherited | test-power | accepted | run_root_branch_guard_raw の打ち切りは、どのテストも固定していない |
| r1-9 | 独立-1 | advisory | no | inherited | test-power | accepted | hang_guard_seconds に既定値の逃げ道が無いことを、どのテストも固定していない |
| r2-1 | 独立-2 | low | no | self-inflicted | request-scope | re-reported | r1-2 の再掲。依頼の「断片の本数」を項目 1 全体と読んだ。返事が来るまで merge-ready と報告しない |
| r2-2 | 独立-2 | advisory | no | inherited | test-power | out-of-diff | nudge の hook を helper を通さずに起動する 2 か所（test_review_followup_nudge_hook.py:195・test_review_followup_nudge_hook_gh.py:208）に打ち切りが無い |
| r2-3 | 独立-2 | advisory | no | self-inflicted | doc-claim | re-reported | r1-5 の再掲。learned-patterns:17 の更新の注記が見出しの直後でなく項の末尾にある |
