---
type: patch
---

#### Summary

- 配線レビュー（別系統モデル）の指摘を独立レビューの指摘とまとめるときに、同じ行の別の欠陥が直されずに閉じられないようにし、突き合わせる相手・比べる値・件数の記録を決めた

#### Changed

- `gdd-pr-review` の 3g（配線レビュー）の指摘のまとめ方を、依頼文・突き合わせる相手・数え方・重さ・閉じる条件の 5 つの箇条に分けた
- 依頼文: Codex への依頼文に `reviewer-common.md` § finding category の表の値と severity の尺度（high / medium / low / advisory）を書き写し、指摘ごとに `file:line`（repo からの相対パスと開始行）・category・severity を添えさせる。category が無い・表の外の指摘は blocking、severity が無い・尺度の外の指摘は high として扱う
- 突き合わせる相手: Codex に渡した diff の tip と同じ sha で走った独立レビューの指摘に限る。独立レビューが無いとき、または `file:line` の無い指摘は、突き合わせずに別の 1 件として数える。比べる前に両方の `file:line` をそろえる
- 数え方: 同じ `file:line` に独立レビューの指摘があれば、Codex の指摘は別に数えず、そのうち 1 件に本文を書き添える
- 重さ: 受け側の独立レビューの指摘と書き添えたすべての Codex の指摘のうち、最も重い severity と blocking を取る。PR 作成前に直す指摘を、high 相当に加えて blocking の指摘にも広げた
- 閉じる条件: 書き添えたすべての本文が直ったことを確かめてから閉じる。Codex の指摘をまとめたことを理由に `Independent Review` 行の件数を足し引きしない。`independent-review.md` の (3-c) の未解消分は、独立レビューの指摘の本体が直ったかで判定する
- SKILL 本文の合計行数の予算を 7068 から 7073 に上げた

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`
- `plugins/gate-driven-development/tests/checks/lint-scripts-functional.sh`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
