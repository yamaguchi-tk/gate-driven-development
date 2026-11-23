---
type: patch
---

#### Summary

`scripts/check-gate-ledger.sh` の steering 行で、pre-push の解決が multiple のときの注記を、hook の比べ方（valid な Pre-Push Self Review の sha〔大文字小文字は区別しない〕が tip の sha の先頭と一致するか）に合わせた。1 件に決まらないときの出口（どれを終えるかユーザーに確認したうえで、`references/self-review-lanes.md` の「使わないステアリングの終え方」に従う）も注記に書いた。

#### Affected Files

- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_check_gate_ledger.py` に、注記が pre-PR の食い違いの説明の後ろにあり、比べる向きと出口を書くこと（pre-PR も multiple の invalid 行）と、pre-push だけが multiple の ok 行にも注記が載ることのテストを足した
