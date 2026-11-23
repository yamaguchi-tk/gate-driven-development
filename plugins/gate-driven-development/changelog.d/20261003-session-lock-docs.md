---
type: patch
---

#### Summary

- `/gdd-dev` のフォールバックで、`.claude/gdd-dev.local.md` が別のセッションの `active: true` を持つときは、brainstorming を起動する前（手順 2）に止まるようにした。スクリプトが走って 0 以外で終わったときも、フォールバックせずに止まる
- README の「1 つのセッションで進めるタスクは 1 つ」の推奨で、同じ checkout の lock が止めるのは Claude Code だけで、セッション ID を渡さない runtime（Cursor など）では前の state を上書きすることを書いた。別のタスクは、どのタスクも使っていない checkout で始める
- `docs/TROUBLESHOOTING.md` に、`gdd loop is already active in another session.` で止まったときの復帰の仕方を足した
- `/gdd-dev` のフォールバックが作る `.claude/gdd-dev.local.md` の雛形を、`setup-gdd-loop.sh` と同じ `---` で囲んだ形にした。brainstorming の後は、その形でファイル全体を書き直す（書く直前に読み直し、別のセッションが active なら書き換えずに止まる）。これまでの `---` の無い形は stop hook が読めず、フォールバックで始めたセッションでは done guard と自動継続が走らなかった

#### Affected Files

- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
