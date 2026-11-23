---
type: patch
---

#### Summary

自走のマージ（`references/post-merge-qa.md`）で、`自走上限` と `Human Check Status` の行の数え方と値の読み方を § 入口に 1 か所だけ書いた。どちらも state.md 全体（コードフェンスの外）で、箇条の記号・`**`・括弧の注記・全角コロン・`=` の形も含めて数え、1 行だけのときに使う。値は state field の文法（`references/state-machine.md`）のとおり最初の ` | ` の前までで、括弧の補足などの注記を付けた値はどの値にも当たらない。`自走上限` の行が 2 行以上あると、自走ではマージせず 1 問で問う。あわせて、次の記述を実際の規定にそろえた。

- human check の承認の後処理（`commands/gdd-dev.md` STEP 2、`references/human-check-template.md` の共通の承認後処理）：判断役の承認なら evidence を `autonomy:<箇所>` にする（本人のターンの承認と事前回答の適用は `human:<自走上限の値>`）
- `references/gate-status-schema.md`：`approved`・`changes_requested` の evidence の例から `<approval-id>` を除き、review run の id か本人の差し戻しの approval id とした。`Human Check Status` の `approved` は `human:`・`autonomy:`・`auto-confirm:` のどれかと書いた
- `references/post-merge-qa.md` § 限界：`human:` の evidence を新しく書く場面と、書き直しでは元の evidence を写すことを書いた。steering の書き込み検査と peer turn の書き込み検査が止めるのは Edit・Write などのツールでの書き込みだけで、Bash での書き込みは止めないと書いた

#### Affected Files

- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/gate-status-schema.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
