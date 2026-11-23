---
type: patch
---

#### Summary

- PR 作成前の Codex 配線レビュー（`gdd-pr-review` の 3g）で、4 型に当たるかを判定できない指摘と、確かめた後に戻すときの扱いを、PR 作成後の Classify と同じにした

#### Changed

- `gdd-pr-review` の 3g の重さ: 4 型に当たるかを判定できない指摘と、確かめた後に戻すときの扱い（どの部品か・戻す条件・上限）は、`gdd-pr-review-followup` の手順 2 Classify に従う。戻し先は 3g の依頼文の規定で分けた severity（Codex が付けた値。無い・尺度の外なら high のまま）にし、Classify の読み替えはしない。確かめた根拠は PR コメントの代わりに PR 本文または worklog に残す

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`

#### User Action Required

- 操作は不要。PR 作成前に Codex が低い severity を付けた指摘でも、guard bypass などに当たるかを判定できなければ high として扱い、PR 作成前に直すか、確かめて戻すことになる

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
