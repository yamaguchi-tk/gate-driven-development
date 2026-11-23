---
type: patch
---

#### Summary

steering の書き込みの検査（`validate-steering-write.py`）は、`${CLAUDE_PLUGIN_ROOT}`・`<redacted>`・`***`・`/path/to/` などを 1 つでも含む行で、ローカルの絶対パスの検出を行全体で飛ばしていた。この例外を外し、placeholder を含む行でも、ローカルの絶対パスの形があれば止める。`/Users/<redacted>/...` のように一部だけを伏せた絶対パスも止まる。`Active Worktree Path` の例外も、語を含む行全体ではなく、欄の行（`- Active Worktree Path: <値>` のようにラベルと値だけの行）に限った。表の行や本文にこの語があっても、同じ行のローカルの絶対パスは止まる。`Worktree:` の欄の行の例外は変えない。止まった後に同じ書き込みが 3 回続くと警告付きで通る仕組みも、今までどおり。これに合わせて、`brainstorming-steps.md` § 9・`faq.md`・email の deny 文から、placeholder が検査を外すという但し書きを除いた。0.44.0 の後の断片 `20261008-crosscheck-followup.md` の「placeholder の記号は、その行のパスの検査を外してしまうため」は、この変更の後は当たらない。置き換え先に placeholder を勧めない理由は、一部だけを伏せても絶対パスの形が残り、同じ deny が繰り返されるためになる。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/secret_scanning.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/references/faq.md`
- `plugins/gate-driven-development/references/self-contained-contract.md`
- `plugins/gate-driven-development/tests/test_steering_path_placeholder_no_skip.py`
- `plugins/gate-driven-development/tests/test_steering_deny_placeholder_guidance.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 足したテスト: `tests/test_steering_path_placeholder_no_skip.py`（placeholder と実パスが同じ行にある Write・Edit・MultiEdit が deny になり、一部を伏せた絶対パスも deny になり、placeholder だけの行は通る。`Active Worktree Path` の語を含む表の行・本文の行は deny になり、欄の行だけは通る）
- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
