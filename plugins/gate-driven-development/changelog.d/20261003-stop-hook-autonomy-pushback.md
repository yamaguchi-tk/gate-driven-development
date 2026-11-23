---
type: minor
---

#### Summary

宣言された自律の範囲の中で止まろうとしたときに、Stop hook が 1 回だけ押し返すようにした（`hooks/scripts/lib/autonomy_pushback.py`）。同じ状態のまま 2 回目に止まったら通す。読めない・判定できない・3 秒の締め切りを過ぎたときは押し返さない（後ろの done guard などは今までどおり走る）。

- 本人の事前回答（`worklog.md` の `事前回答:` 行）があるのに `human-check-waiting` で止まったとき：事前回答を適用して委任先（Fable・Opus）に相談して続けるか、`採った案: 人間に止める` を書いてから止まるよう求める
- マージ待ちの宣言（`.claude/gdd-merge-intent.json`）を書いたセッションが、PR が OPEN のまま止まったとき：`gh pr view` で PR と CI の状態を確かめ、success ならマージして次の作業へ、pending なら待つ仕組みを起動してから止まる、failure なら直す、のどれかを求める。GDD の steering が無いセッションでも効く
- 宣言が無いのに、最後の発言が「CI が通ったらマージします」の形で止まったとき：宣言を書いて待つか、マージしないと明言するかを求める（10 分に 1 回まで）

#### Added

- `hooks/scripts/lib/autonomy_pushback.py`
- `.claude/gdd-merge-intent.json`（マージ待ちの宣言）と `.claude/gdd-autonomy-pushback.json`（押し返しの判定の記録）

#### Changed

- `hooks/scripts/gdd_stop_hook.py`：上の押し返し（human check の入口とマージ待ちの入口の 2 つ）を組み込んだ。`external-review-waiting` のポーリング上限の判定を `lib/pr_review_followup_polling.py` に移した（挙動は同じ）
- `references/post-merge-qa.md` 手順 2：マージを待つときに宣言を書いて待つ仕組みを起動することを足した
- `references/autonomy.md` § 限界：Stop hook が押し返す場面を書いた
- `hooks/hooks.json` の description と `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` の導入時のチェックリストに、押し返しと 2 つのファイルを足した

#### Affected Files

- `hooks/hooks.json`
- `hooks/scripts/gdd_stop_hook.py`
- `hooks/scripts/lib/autonomy_pushback.py`
- `hooks/scripts/lib/pr_review_followup_polling.py`
- `references/post-merge-qa.md`
- `references/autonomy.md`
- `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`
- `tests/test_stop_hook_autonomy_pushback.py`

#### User Action Required

- `.claude/` を ignore していない repo では、`.claude/gdd-merge-intent.json` と `.claude/gdd-autonomy-pushback.json` を `.gitignore` に足す

#### Validation / Eval Impact

- `tests/test_stop_hook_autonomy_pushback.py`
- 関係する Stop hook のテスト（`scripts/light-lane-related-tests.py`）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
