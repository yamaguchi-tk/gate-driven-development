# Contract Overview

> **所有**: 自己完結条件と fail-closed 条件の quick index
> **上位正本**: `self-contained-contract.md`
> **正本マップ**: `references/source-of-truth-map.md`

詳細ルール、Acceptance Criteria、検証契約は `self-contained-contract.md` が正本。この overview は要約だけを置き、優先順位を上書きしない。

## 境界

GDD は root 側ルールに依存せず、plugin 内の `commands/` / `skills/` / `agents/` / `references/` / `scripts/` / manifest で workflow 契約を自己完結させ、Claude Code / Cursor / Codex で同じ契約を再現する。

state.md は routing source と短い context source。state.md is not an audit dump。audit details は `worklog.md` / `adr.md` / `findings.md` / appendix に分離する。

## Fail-Closed

次は先へ進まない: git / worktree 不在、same-name asset 衝突、必須 file / manifest / reference 欠落、worktree candidate 複数、planning/build candidate 競合、worktree identity（path slug / steering slug / state task id / git branch / state active branch）と Worktree Identity Tuple 不一致（branch_slug_mismatch / active_branch_mismatch 等）、複数 non-terminal steering、mixed worktree bases、Route In Progress と Next Action の矛盾、state field 不正値。

## Blocked Response

停止時は `参照した正本` / `停止理由` / `次の1アクション` を返し、`<gdd-stop>` の後に `## 👤 次にすること` を付ける（`references/output-format.md` § 停止時の「👤 次にすること」マップ）。

## Pointers

- 詳細契約: `self-contained-contract.md`
- phase / state: `state-machine.md`
- field tier: `state-field-tiers.md`
- 正本マップ: `references/source-of-truth-map.md`
