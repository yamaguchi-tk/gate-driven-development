---
lane: L1
pr: 547
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 148898af | 0 | 1 | 0 | 2026-10-20 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2346ff4b | 0 | 3 | 0 | 2026-10-20 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 0ce9aa41 | 0 | 1 | 0 | 2026-10-20 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 確認済み（2026-10-21 ユーザー: 推奨のまま）: 依頼の「判定のコード」を § 常時 High の適用範囲に狭めて読んだ（検査スクリプトと warn-only の lint・hook が外れる）。Opus・Fable とも広げる案を推し、その案で直した。commit: 2346ff4b |
| F2 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 確認済み（2026-10-21 ユーザー: 推奨のまま）: 依頼に無い「文書だけの変更には 1・2 を当てない」を足し、述語が 2 つ並んでいた。推奨の案で、文書が挙動を決める変更は testing-anti-patterns.md § テスト判定基準 に向けた。commit: 2346ff4b |
| F3 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 確認済み（2026-10-21 ユーザー: 推奨のまま）: 依頼が名指しした gdd-receiving-code-review から指していなかった。Opus・Fable とも指す案を推し、IMPLEMENT から指した。commit: 2346ff4b |
| F4 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 確認済み（2026-10-21 ユーザー: 推奨のまま）: design-gating・requirements-gating-steps.md の文書の処置から指していない。Opus は指す、Fable は指さないを推した。planning 文書の処置は別の段なので指さない案で進め、限界に書く |
| F5 | 独立-1 | low | no | self-inflicted | wiring | accepted | subagent-driven-implementation の Prompt Contract の Constraints（:57）が § 直し方 を挙げず、worker の報告に 4・5 の記録の欄が無い |
| F6 | 独立-1 | low | no | self-inflicted | wiring | accepted | systematic-debugging の implementation_fix_only 以外の route（TDD に回すものなど）の復帰が § 直し方 を指していない |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | rollback-patterns.md:137 の「テストは変更しない」と § 直し方 2 の境界のテストの段がぶつかり、「従来どおり実装修正 → impl-gate」の列に再現テストの段が見えない |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 直し方 4・5 と common-guardrails.md § 選ぶときの基準 2・4、1 と root-cause-investigation の Phase 4 が互いを指さない。PR 本文の「無かった」の言い過ぎは本文で直した |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に、5 の既定の行動・4 の記録・1 のテストを残すことの広がりが無い。commit: なし（PR 本文） |
| F10 | 独立-1 | advisory | no | self-inflicted | measurement | accepted | 4・5 は発火条件だが、条件に当たる件数と、その条件で止まる損失を測っていない |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 参照元の pr-review-followup の注記と :6 の理由、gdd-pr-review-followup:19 の「規律A/B/C」が § 直し方 の追加に追随していない |
| F12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 根拠の 118 件が出た軽いレーンは root CLAUDE.md § 指摘を直すとき に従い、§ 直し方 を読まないことを限界に書いていない。commit: なし（PR 本文） |
| F13 | 独立-1 | advisory | no | inherited | doc-claim | accepted | self-review-lane-tokens.sh:69・:73 のコメントが「3 skill」のまま（検査は参照元の行から導くので挙動は正しい） |
| F14 | 独立-1 | advisory | no | self-inflicted | evidence | fixed | 抜粋に Skill RED-GREEN Evidence が無い。PR 本文の別の節に置いた。commit: なし（PR 本文） |
| F15 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | § 直し方 2 の範囲を「判定を出すコード」にしたため、§ 常時 High の適用範囲にある block しない hook の (a) 再開に使う state.md の field の書き込みが外れ、「より広い」の断定が成り立たない |
| F16 | 独立-2 | medium | no | self-inflicted | request-drift | accepted | 確認済み（2026-10-21 ユーザー: 推奨のまま）: design-gating 手順 12・gdd-requirements-amendment § レビュー指摘の処置から指していない（独立-1 の F4 と同じ問い。指さない案で進める） |
| F17 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 確認済み（2026-10-21 ユーザー: 推奨のまま）: gdd-pr-review の 3g・Pre-PR loop の修正から指していなかった。Opus・Fable とも指す案を推し、SYNC 対象の pr-review.md は書き換えずに SKILL.md から指した。commit: 0ce9aa41 |
| F18 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | § 直し方 冒頭の指摘の出所の列挙に、gdd-receiving-code-review が扱う companion・security review が入っていない |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | testing-anti-patterns.md § テスト判定基準 は正とする先を 3 つ挙げるのに括弧は CLAUDE.md だけで、文書の変更の確かめ方（Skill RED-GREEN Evidence）は gdd-writing-skills にある |
| F20 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary に、1・2 を当てない範囲と文書の変更の確かめ方の変更、「決められないときは含める」の既定が出ていない |
| F21 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容の 2 に「決められないときは含める」の既定が無い。commit: なし（PR 本文） |
| F22 | 独立-3 | medium | no | self-inflicted | wiring | accepted | gdd-pr-review の Pre-PR loop の medium・3f・3g の修正には、規律 C の 3 つの記録先のどれも当たらず、§ 直し方 4・5 の記録を書く先が無い |
| F23 | 独立-3 | medium | no | self-inflicted | request-drift | re-reported | planning 文書の処置（design-gating・requirements-gating-steps.md・gdd-requirements-amendment）から指していない（F16 の再報告） |
| F24 | 独立-3 | low | no | self-inflicted | request-drift | accepted | gdd-pr-review の 3a・3b でその場で直す分が「Pre-PR loop・3f・3g」の列挙に入っていない |
| F25 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 参照元の注記で、§ 直し方 を指す followup の 2 skill に「§ 直し方」が無く、:6 の理由の文も 3 skill だけを挙げる |
| F26 | 独立-3 | advisory | no | self-inflicted | style | accepted | 直す順序の文が「停止条件の上書き」の箇条の末尾にあり、見出しと合わない |
| F27 | 独立-3 | advisory | no | self-inflicted | evidence | accepted | Skill RED-GREEN Evidence が gdd-pr-review の変更まで含むか、抜粋からは確かめられない（evidence は pr-review-followup の経路で取った） |
| F28 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | followup の 2 skill の指す文が、§ 直し方 の手順の名前を括弧で 3 つ書き写している |
