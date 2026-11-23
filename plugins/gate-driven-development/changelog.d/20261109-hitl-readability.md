---
type: patch
---

#### Summary

- human check の一次表示で、当たらない条件付きの節（`選択肢の説明`・`アーキテクチャ選択`・`Multiple PR Strategy Options`）を書かないようにした。`選択肢なし`・`該当なし` の行は置かず、`<gdd-hitl-fields>` の `none` で示す。単一案の理由は `requirements.md` に残す
- 指摘の id・質問番号・run の名前・内部フィールド名を本文に残さず、中身の言葉に置き換えるようにした。main が subagent の下書きを表示する前の置き換えも認める。判断ポイント・選択肢・承認の境界は変えない
- 冒頭に、OK が何を決めるかを案の名前だけで閉じた 1 文を書くようにした。相談役の追加は main が取捨して推奨案の文に書き込み、`案 + 追加 N 点` の形で見せない

#### Affected Files

- `references/human-check-template-compact.md`・`references/human-check-template.md`
- `references/subagent-dispatch.md`・`commands/gdd-dev.md`・`skills/gdd-requirements-gating/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 検査の判定は変えていない。`lint-hitl-required-fields.py` はこれまでもタグだけを見るので、節を書かなくても通る
