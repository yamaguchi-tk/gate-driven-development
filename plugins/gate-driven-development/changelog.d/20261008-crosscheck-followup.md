---
type: patch
---

#### Summary

着手前の突き合わせ（`gdd-request-code-crosscheck`）を、起動できないときと express からの昇格のときにも進められるようにした。定義が見つからないときは `general-purpose` を `model: opus` で起動し（Codex・Cursor では `fixed-models.md` の相談役の段落の経路）、それも起動できないとき（Codex で委譲の許可が無い、起動の失敗など）は `request-crosscheck.md` に `突き合わせ: unavailable（理由）` の 1 行を書いて human check に載せる。express から quick (standard) への昇格では、requirements-gating に戻る前に突き合わせを行う。そこで `既存とぶつかる` が 1 件以上出たか `unavailable` のときは、承認済みの `Human Check Status` を `pending` に戻し、req-gate の後の human check で聞く（`state-machine.md`・`phase-progression.md`・`faq.md`）。steering の書き込みの検査がパス・email を止めたときの deny 文と `faq.md`・`docs/SECURITY.md` は、置き換え先に `<redacted>` を勧めず、`（ローカルパス）` のような語を勧める。placeholder の記号は、その行のパスの検査を外してしまうため。秘密値の deny は今までどおり `<redacted>` を勧める。前の断片に書き漏れた点も補う: 突き合わせの agent の根拠はリポジトリからの相対パスで書き、Codex・Cursor では `general_heavy_risk` tier のモデルの read-only の別コンテキストに agent の本文を渡す。

#### Affected Files

- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/faq.md`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/tests/test_steering_deny_placeholder_guidance.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 足したテスト: `tests/test_steering_deny_placeholder_guidance.py`（パス・email の deny 文が `PATH_PLACEHOLDER_TOKENS` のどの語も勧めず、秘密値の deny は `<redacted>` を勧めること）
- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
