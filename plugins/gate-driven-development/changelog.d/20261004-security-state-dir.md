---
type: patch
---

#### Summary

- `docs/SECURITY.md` の § 通信境界・§ 1・全体図に、hook が `gh pr view` で GitHub から PR の有無を読む例外を書いた（§ 4 と合わせた）
- § 4 に、hook が state dir（`~/.claude/.gdd-hook-state/`）に書くもの（GDD worktree の絶対パスを平文で持つ PR 台帳 `gdd-pr-roots`、ログ、キャッシュ、異常終了の記録）を書いた。Bash と SessionStart の行に、その読み書きを足した

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
