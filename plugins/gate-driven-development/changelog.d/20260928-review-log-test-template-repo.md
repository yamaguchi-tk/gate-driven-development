---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。`tests/test_review_log_present.py` の `test_every_review_log_on_this_checkout_passes` は、repo root の review-log を 1 本ずつ、一時 repo を作って検査する。review-log ごとに base の commit と feature branch を作り直していたので、その費用が本数分かかっていた。どの review-log でも同じ部分を 1 回だけ作り、review-log ごとに複製するようにした。1 本あたりの費用が下がるだけで、実行時間が本数に比例して伸びることは変わらない。検査の入力と assert は変えていない。複製の途中で auto maintenance の lock が消えないよう、base の repo では `maintenance.auto` を止めた。

#### Affected Files

- `plugins/gate-driven-development/tests/test_review_log_present.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 書式の誤った review-log を 1 本渡すと、複製した repo でも検査が失敗することを確かめた
- `python3 -m pytest plugins/gate-driven-development/tests/test_review_log_present.py -q`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
