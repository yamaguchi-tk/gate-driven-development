---
name: gdd-goal-driven-execution
version: 0.1.0
description: "Use when a GDD-adjacent task has a clear goal but the plan is uncertain, changing, or evidence-dependent. Triggers: 「Goal達成まで続けて」「うまくいくまで自律的に修正して」「不確実な中で計画を更新しながら進めて」「root cause を確度高く見つけるまで」. Responsibilities: goal contract + current-state readback + hypothesis-driven plan revision + execution/verification loop + cross-platform guidance for Claude Code, Cursor, and Codex."
---

# Goal-Driven Execution

GDD の Goal-Driven Execution は、固定された手順を順番に実行するための skill ではない。**Goal is stable; plan is revisable** を正本にし、不確実な状況で観測、仮説、計画修正、実行、検証を回しながら Goal に近づける。

Loop owner の正本は `references/state-machine.md` § Goal-Driven Loop Ownership。`gdd-goal-driven-execution` は outer loop を所有するが、`root-cause-investigation` / `gdd-subagent-driven-implementation` / Stop hook の inner loop や continuation guard を置き換えない。

Outer loop boundary: do not run root cause probes directly, and do not mark subagent DONE as verified_done. root cause の probe は `root-cause-investigation`、実装と task-level verification は `gdd-subagent-driven-implementation`、final completion claim は completion gate か outer loop の fresh evidence 確認に戻す。

## Goal

- Goal を明文化し、途中で計画が変わっても Goal を勝手に変えない
- `state.md / tasklist.md / worklog.md / PR / CI / git / test` から現在地を読み、事実と推測を分ける
- 1 サイクルごとに Working Hypothesis を立て、検証結果で plan を維持・修正・停止する
- Claude Code、Cursor、Codex のどれでも同じ実行契約に寄せる
- superpowers:executing-plans の「計画を順に実行する便利さ」は取り込むが、workflow owner は GDD に戻す

## When To Use

使う:

- Goal は明確だが、最短の計画や原因がまだ不確実
- 途中でレビュー、CI、scenario eval、root cause 調査、PR follow-up の結果に応じて計画を修正する必要がある
- 「計画通りに進める」より「Goal に向けて自律的にループする」ことが大事
- active GDD / post-completion GDD-adjacent / GDD plugin 改善の継続作業
- root cause が `confirmed` ではなく、追加証跡を取りながら Confirmed Gate の停止条件（進展なしが 3 回連続、または調査予算超過）まで確度を上げたい

使わない:

- `/gdd-dev` の初回要件整理。まず `gdd-brainstorming` / `gdd-requirements-gating`
- 単純な read-only status 確認。`gdd-status`
- レビュー指摘が明確で PR follow-up loop だけで閉じる。`gdd-pr-review-followup`
- Goal 自体を決める前の壁打ち。`gdd-pre-workflow-brainstorming`

## Goal Contract

開始時に以下を 5 行以内で固定する。

```markdown
Goal:
- <達成したい状態>

Done When:
- <観測可能な完了条件>

Not Changing Without Human:
- <勝手に変えない scope / safety / release / merge / deploy 境界>
```

Goal は途中で勝手に広げない。新しい事実で Goal 自体を変える必要が出た場合は、`human_recheck_required` または `gdd-requirements-amendment` に戻す。

## Current State

各サイクル開始時に、会話履歴ではなく事実 source を読む。

- GDD artifact: `state.md / tasklist.md / worklog.md / requirements.md / design.md`
- Git / PR / CI / test: `git status`, `gh pr view/checks`, 実行済み test / scenario eval
- 直近の人間入力: 最新発話を最優先し、古い reboot task や compact summary で上書きしない

出力では以下を分ける。

```markdown
Current State:
- Done: <確認済み>
- Missing: <Goal に足りないもの>
- Evidence: <参照した artifact / command / PR / CI>
- Uncertainty: <まだ推測のもの>
```

## Working Hypothesis

次の 1 サイクルで Goal に近づくための仮説を 1 つ書く。root cause なら原因仮説、PR follow-up なら解消すべき blocker、scenario eval なら落ちた契約の仮説になる。

```markdown
Working Hypothesis:
- If: <この仮説が正しければ>
- Then: <この実行で何が改善する>
- Disprove By: <何が観測されたら仮説を捨てる>
- Verification: <通す test / CI / scenario / review>
```

複数仮説が残り、独立に検証できる場合だけ subagent / parallel investigation を使う。仮説に依存関係がある場合は順番に検証する。

## Plan Revision Loop

1. Goal Contract を読み直す
2. Current State を事実 source から読む
3. Working Hypothesis を 1 つ立てる
4. 次の最小アクションを決める
5. Execute and Verify を行う
6. 結果で分岐する

分岐:

- `progress`: Goal に近づいた。次サイクルへ
- `verified_done`: Done When を満たした。completion / PR / cleanup へ
- `hypothesis_rejected`: plan を修正し、別仮説へ
- `needs_design_rework`: `gdd-design-gating` または `gdd-requirements-amendment`
- `needs_human`: scope / safety / release / merge / deploy / AC 変更が必要
- `blocked`: 追加証跡が取れない、または同じ壁が 3 回続いた

## Execute and Verify

実行は小さく行い、証跡なしに前進扱いしない。

- コード変更: TDD / focused test / relevant regression を実行
- root cause: 仮説を棄却または確認できる probe を実行
- PR follow-up: 指摘修正、push、CI、必要なら再レビュー依頼
- scenario eval: fixture / scenario runner / contract test を実行し、改善前後を比較

検証が失敗したら「少し直して再実行」を無限にしない。失敗理由を Working Hypothesis の結果として記録し、plan を更新する。

## Stop Conditions

以下で停止または人間に戻す。

- Done When を満たした
- Goal 自体を変える必要がある
- AC / scope / security boundary / release boundary が変わる
- `merge` / `deploy` / `terraform apply` / AWS write / external posting など AGENTS.md 上の明示承認が必要
- 同じ hypothesis / same route が 3 回失敗した
- 追加証跡が取れず、`insufficient_evidence` 以上に進めない
- active GDD task / worktree / PR / branch が一意に解決できない

## Cross-Platform Contract

### Claude Code

- TodoWrite / subagent が使える場合は、Current State と Working Hypothesis を task ごとに分ける
- ただし subagent 結果は GDD artifact に戻し、subagent を workflow owner にしない

### Cursor

- Composer / Agent に渡す場合も、Goal Contract、Current State、Working Hypothesis、Verification を明示する
- 長い context に頼らず、GDD artifact と git / PR / CI の事実を再読する

### Codex

- Codex goal continuation がある場合も、`state.md / tasklist.md / worklog.md` と PR / branch / worktree で active task を解決する
- compact 後は会話履歴を参考情報、GDD artifact を正本、Git / PR / CI / test を事実として扱う
- `get_goal` / `create_goal` が使える環境でも、GDD の Goal Contract と矛盾させない

## Output Template

```markdown
## Goal-Driven Execution

### Goal Contract
- Goal:
- Done When:
- Not Changing Without Human:

### Current State
- Done:
- Missing:
- Evidence:
- Uncertainty:

### Working Hypothesis
- If:
- Then:
- Disprove By:
- Verification:

### Next Action
- <このサイクルで実行する最小アクション>

### Loop Result
- Executed:
- Observed:
- Decision: progress | verified_done | hypothesis_rejected | needs_design_rework | needs_human | blocked
- Plan Update:
```

## Relationship To Superpowers

`superpowers:executing-plans` は fixed written plan を順番に実行する standalone executor。Goal-Driven Execution は、Goal は維持し、Plan は更新する GDD owner の loop。active GDD / GDD-adjacent では superpowers を workflow owner にしない。必要な discipline だけを advisory reference とし、state.md / tasklist.md / worklog.md / PR evidence に戻す。

## Rationalization Check

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「計画があるから順番に進めればいい」 | 不確実な作業では計画より Goal が正本。観測結果で計画を更新する | [Plan Fixation] 最初の計画に固執して Goal から逸れる |
| 「あと 1 回だけ同じ修正を試す」 | 同じ壁が続くなら hypothesis を捨てる。3 回で停止または再設計 | [Sunk Cost Fallacy] 失敗した方針への投資を惜しむ |
| 「Goal 達成に近づいた気がする」 | 証跡なしの前進は前進ではない。Verification を通す | [Progress Theater] 作業量を成果と誤認する |
| 「superpowers の方が便利だからそちらに渡す」 | active GDD では GDD artifact が workflow owner。superpowers は advisory only | [Authority Substitution] 便利な primitive に state ownership を渡す |

## Guardrails

- Goal を勝手に変えない
- Done When を満たす前に完了宣言しない
- 証跡なしに `progress` にしない
- 同じ hypothesis を 3 回以上繰り返さない
- worktree / PR / branch / state Task ID が混線したら進めず `gdd-status` へ戻す
- 人間承認が必要な操作は AGENTS.md の承認境界に従う
