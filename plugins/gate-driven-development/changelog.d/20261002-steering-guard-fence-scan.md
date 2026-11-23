---
type: patch
---

#### Summary

- `.steering/` への書き込みを検査する hook（validate-steering-write.py）が、コードブロックの内外を `lib/tasklist_parse._scan_fences` の規則（記号の種類・長さ・info の有無で閉じを判定する）で決めるようにした。これまでは ``` の行ごとに状態を反転するだけだったので、4 連の fence の中の ```、`~~~` の中の ```、info に `` ` `` を含む行（```` ```で`囲む` ```` など）の後ろで状態がずれ、fence の外の `password:` などの値・AWS アカウント ID・placeholder を見逃していた
- `#### Attempts`・`#### 試行記録` の見出し行が、すべての検出器を飛ばしていた。見出し行も検査する

#### Changed

- 値・ID・placeholder の検査を免除するのは、閉じた fence（```・````・`~~~`）の中だけにした。`~~~` の fence の中も免除の対象になった
- 開いている fence の中で、閉じの条件（同じ記号・同じ長さ以上・info なし）を満たさない行は fence を閉じない。4 連の fence の中の ``` の対の間や、開いている fence の中の ```` ```json ```` の後ろは、コードブロックの中として扱う
- 閉じていない fence の後ろは、コードブロックとして扱わず検査する。記入例の fence を Edit で書き換えるときは、開きと閉じを同じ編集に含める
- fence の区切り行も検査する。閉じた fence の区切り行には email・path・secret marker・省略記号の検査を、閉じていない開き行にはすべての検査をかける
- fence の中の行は、`#### Attempts` などの節の始まり・終わりとして読まない。fence の中の `#` の行では節が終わらない
- ApplyPatch の追加行は、ファイルごとにも検査する。別のファイルに足した ``` と対にして、値を fence の中として免除しない

#### Affected Files

- `hooks/scripts/validate-steering-write.py`
- `hooks/scripts/lib/patch_scoping.py`
- `references/common-guardrails.md`
- `tests/test_steering_write_fence_scan.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_steering_write_fence_scan.py`（hook の入口から: fence がずれる 3 つの入口 × 3 つの検出器、閉じた fence の記入例、閉じ忘れ、節の見出し行と節の境界、区切り行、ApplyPatch のファイルをまたぐ fence、例外で落ちない入力）
- `tests/validate-plugin.sh`
