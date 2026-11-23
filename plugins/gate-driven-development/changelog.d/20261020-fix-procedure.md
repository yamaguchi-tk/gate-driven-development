---
type: patch
---

#### Summary

- レビューの指摘を直すときの順序を `references/self-review-lanes.md` § 直し方 に置いた。再現するテストを先に書く → 修正が受け入れる入力の形を列挙して境界ごとにテストを書く（判定を出すコードと、その判定に届く部品〔判定が使う解析・正規化などの共有部品〕と、block しない hook のうち `references/reviewer-common.md` § 常時 High の適用範囲の (a)(b) に届く部分では fail-open の 3 ケースも。判定を出すコードは warn-only の lint・hook と検査スクリプトを含み、当たるか決められないときは含める）→ 使う側と対を直す前に列挙する → 拒否リストに足す前に許可リストか既定の反転と比べる → 同じ部品の修正が 2 巡続いたら、その部品が要るか・共有の実装に寄せられるかを問う
- 修正の手順を持つ skill（`gdd-pr-review`・`gdd-pr-review-followup`・`pr-review-followup`・`gdd-subagent-driven-implementation`・`gdd-systematic-debugging`・`gdd-receiving-code-review`）と `references/rollback-patterns.md` § implementation_fix_only から、この節を指す
- 実害クラス・`High` でない、コードを変える修正にも、再現するテストを先に書く順序が当たるようになる（文言・帳簿だけの修正は対象外。skill・reference・prompt のように文書が挙動を決める修正は、`references/testing-anti-patterns.md` § テスト判定基準 と Skill RED-GREEN Evidence で確かめる）

#### Changed

- `references/self-review-lanes.md`（§ 修正時規律 に § 直し方 を追加。参照元に `gdd-systematic-debugging`・`gdd-receiving-code-review` を追加）
- `skills/gdd-pr-review/SKILL.md`（指摘を直す順序と 3g）
- `skills/gdd-pr-review-followup/SKILL.md`・`skills/pr-review-followup/SKILL.md`（Fix の ①直す）
- `skills/gdd-subagent-driven-implementation/SKILL.md`（差し戻しの修正）
- `skills/gdd-systematic-debugging/SKILL.md`（§ Failure Routing）
- `skills/gdd-receiving-code-review/SKILL.md`（IMPLEMENT）
- `references/rollback-patterns.md`（§ implementation_fix_only）

#### Affected Files

- `references/self-review-lanes.md`
- `references/rollback-patterns.md`
- `skills/gdd-pr-review/SKILL.md`
- `skills/gdd-pr-review-followup/SKILL.md`
- `skills/pr-review-followup/SKILL.md`
- `skills/gdd-subagent-driven-implementation/SKILL.md`
- `skills/gdd-systematic-debugging/SKILL.md`
- `skills/gdd-receiving-code-review/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
