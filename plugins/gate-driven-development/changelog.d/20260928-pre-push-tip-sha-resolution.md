---
type: patch
---

#### Summary

pre-push gate は、検査する steering を 1 件に決められない（候補が 2 件以上の）とき、`steering-multiple` で止めていた。同じ checkout に古い steering が残るだけで、証跡を書いた本人の push も止まっていた。候補が 2 件以上のときは、`.steering/` の全 `state.md` のうち、valid な `Pre-Push Self Review` の sha（full sha に正規化）が push 対象の tip と一致するものを探し、ちょうど 1 件なら、その steering の証跡で以降の検査（dry・Independent Review）を行うようにした。このとき Task Size は読まず、standard として検査する（trivial・quick の steering に tip の証跡を書いて検査を緩めることはできない）。

証跡が valid でない・sha を commit に解決できない・`state.md` が読めない steering は一致に数えない。一致が 0 件・2 件以上なら、今どおり `steering-multiple` で止める。候補を探すときは、tip の sha の先頭 7 桁を含む `state.md` だけを先に絞り込み、steering の件数で hook の時間を増やさない。pre-PR gate には同じ材料が無いので、複数 steering のままでは今どおり止まる。

#### Changed

- `hooks/scripts/run-pre-push-gate-hook.sh`: `multiple` を push 対象の tip の証跡で解く。Task Size の読み取りを関数にまとめ、読めない `state.md` で hook ごと落ちないようにした（読めなければ standard）
- `references/self-review-lanes.md`・`docs/TROUBLESHOOTING.md`: pre-push が止まる条件の記述を合わせた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`
- `plugins/gate-driven-development/tests/test_pre_push_tip_sha_resolution_contract.py`（新規）

#### User Action Required

- なし。複数 steering で pre-push が止まったときは、push 対象の tip で Pre-Push Self Review を記録すれば、その steering で（standard として）検査される。pre-PR gate で止まったときは、今どおり使わない steering を `cancelled` にする

#### Validation / Eval Impact

- `tests/test_pre_push_tip_sha_resolution_contract.py`: 一致 1 件で検査して通ること（短い sha・終端だけの候補・明示した ref の tip を含む）、選んだ steering で Independent Review まで検査すること、一致 2 件・証跡なし・古い commit・存在しない sha・tree の sha・書式が不正な証跡・読めない `state.md` で `steering-multiple` のまま止まること、選んだ steering の Task Size（trivial・quick、cancelled を含む）で検査が緩まないこと、一致しない証跡を持つ steering が 200 件あっても解決の時間が増えないこと
- 変更したファイルを参照するテスト、`bash plugins/gate-driven-development/tests/validate-plugin.sh`
