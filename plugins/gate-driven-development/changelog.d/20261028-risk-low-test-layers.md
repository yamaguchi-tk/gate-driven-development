---
type: patch
---

#### Summary

- リスクの段が低でない steering で、改行が CRLF（または CR だけ）の state.md に、既に `risk-low` の行があると、関係の無い Edit も止まっていた。書き込みの前と後で改行の扱いが違い、既にある行を新しい行に数えていたため。比べる前に改行をそろえ、止まらないようにした
- 親ディレクトリに権限が無く、あるかを確かめられない state.md への Edit / MultiEdit を、この検査でも止めるようにした。今までは「無いファイル」とみなして、この検査を飛ばしていた（ツールも書けないので、通ってしまう事故にはなっていなかった）
- `risk_low_approval` の deny の Why に、書き込み後の state.md を確かめられない書き込みも止める理由として入れた。`old_string` がそのまま当たらない Edit にも、`risk-low` を読み違えて書いたという Why だけが付き、原因を読み違えうるため

#### Fixed

- `hooks/scripts/lib/risk_tier.py`（`_risk_low_lines` で `\r\n`・`\r` を `\n` にそろえる。既にあるかを `os.path.lexists` ではなく `lstat_or_none` で確かめ、確かめられなければ止める側にする）
- `hooks/scripts/validate-steering-write.py`（`risk_low_approval` の Why の文面）

#### Affected Files

- `hooks/scripts/lib/risk_tier.py`
- `hooks/scripts/lib/state_write_projection.py`
- `hooks/scripts/validate-steering-write.py`
- `tests/test_risk_low_approval_guard.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_risk_low_approval_guard.py`。`risk` と `-low` を別の edit に分けた形のうち、追加分をつないでも `risk-low` にならない順の 2 件を足した（今までの分けた形のテストは、追加分をつないだ層で先に止まっていた）。書き込み後の行の多重集合の比較を行数の比較に変えると、このうち入れ替わる形の 1 件が落ちる。CRLF・CR だけの state.md、権限の無い親、state.md への move のテストも足し、止めない側のテストは hook が通したこと（rc 0）も確かめる
