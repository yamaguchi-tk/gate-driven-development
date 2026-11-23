---
type: patch
---

#### Summary

- README の「1 つのセッションで進めるタスクは 1 つ」の推奨に、タスクの数え方（`/gdd-dev <タスク>` で始める別の依頼。後続 Stage は同じチャットで続ける）と、別のタスクは別の checkout（worktree）のセッションで始める前提を書いた
- `/gdd-dev` のフォールバック（`setup-gdd-loop.sh` が使えないとき）を、スクリプトの実行そのものが拒否されたときに限った。別のセッションの loop が active で exit 1 になったときは、フォールバックせずに止まる

#### Affected Files

- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
