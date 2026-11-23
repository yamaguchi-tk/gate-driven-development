---
type: minor
---

#### Summary

- リスクの段の読み手（`hooks/scripts/lib/risk_tier.py` の `read_risk_tier`）を足した。`.steering/<task>/request-crosscheck.md` の `### リスクの段` の直後の行が `リスクの段: 低` ちょうどのときだけ `低` と読み、記録が無い・読めない・`高`・`判定できない`・形が崩れている・見出しや `リスクの段:` の行が 2 つあるときは `高` と読む
- steering の書き込み hook は、state.md に触れる書き込みで、触れた state.md の steering のリスクの段が 1 つでも `低` と読めなければ、次のときに書き込みを止める。追加分のどこか（どのファイルの追加行かは問わない。ApplyPatch は `+` で始まる行をすべて。追加分をつないだものも見る）に `risk-low`（human check を待たない承認の evidence。大文字・`_`・空白・全角などの表記の揺れを含む）があるとき。既にある state.md への Edit・MultiEdit で、`old_string` が書き込み前のテキストにそのまま無いか、空の `new_string` で改行ごと消える形のとき（書き込み後の全文を確かめられないため。`risk-low` を書かない Edit も止まる）。Write・Edit・MultiEdit の書き込み後の state.md に、書き込み前に無かった `risk-low` の行が現れるとき（`risk` と `-low` を別の Edit に分けた形を含む）。欄名・status は問わない。3 回続けて止めても警告には落とさない。今は `risk-low:` を書く手順が無いので、この検査が止めるのは書き間違いだけである
- `hooks/scripts/validate-steering-write.py` の一部（path の判定、書き込み後の全文の再構成、`Origin Session` の検査）を lib に移した。挙動は変わらない

#### Added

- `hooks/scripts/lib/risk_tier.py`
- `hooks/scripts/lib/steering_paths.py`・`hooks/scripts/lib/state_write_projection.py`・`hooks/scripts/lib/origin_session_guard.py`（`validate-steering-write.py` から移した）
- `tests/test_risk_tier_reader.py`・`tests/test_risk_low_approval_guard.py`

#### Changed

- `hooks/scripts/validate-steering-write.py`（検査の呼び出し、降格しない category に `risk_low_approval` を足す、分割で 1,609 行から 1,326 行に）
- `references/gate-status-schema.md`（`risk-low:` を書ける steering）

#### Affected Files

- `hooks/scripts/validate-steering-write.py`
- `hooks/scripts/lib/risk_tier.py`
- `hooks/scripts/lib/steering_paths.py`
- `hooks/scripts/lib/state_write_projection.py`
- `hooks/scripts/lib/origin_session_guard.py`
- `references/gate-status-schema.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_risk_tier_reader.py plugins/gate-driven-development/tests/test_risk_low_approval_guard.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
