---
name: gdd-resume
description: 通常導線ではなく復旧用。Continuation ID から GDD の次フェーズを新しいチャット・新しい worktree で復元する
argument-hint: "continuation-id（例: 20260611-foo-p2）"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-gdd-loop.sh:*)"]
---

# GDD Resume

`/gdd-resume <continuation-id>` は、PR merge 後や段階実装の切れ目で作成された Continuation Registry から次フェーズを復元する入口。通常導線は同じチャットで「次に進んで」であり、`/gdd-resume` はチャット破損・compaction 不安・明示的な新チャット開始時だけ使う復旧用。

## ツール境界

frontmatter の `allowed-tools` は Claude Code の slash command 実行時に最初に許可する bootstrap command を示す。実際の復旧 workflow では、repo root 解決と registry 読み取りで continuation を特定してから `setup-gdd-loop.sh` を bootstrap として実行し、その後に Git / PR / CI / test facts の read-only 確認と worktree 作成を GDD の通常権限・安全規則に従って行う。権限や環境の都合で実行できない場合は、作成済みや確認済みと主張せず、blocked reason と次の1アクションを出す。

## 使い方

```text
/gdd-resume <continuation-id>
```

## 情報源の優先順位

- **会話履歴は参考情報**: compaction や新チャットで欠落するため、会話だけで次計画を確定しない。
- **GDD artifact は正本**: `requirements.md / design.md / tasklist.md / state.md / worklog.md / continuation.json` を state と承認済み scope の正本にする。
- **Git / PR / CI / test は事実**: PR state、merge commit、CI、review、test result、diff を read-only で確認する。
- **Continuation ID は受け渡しキー**: 対象 repo root の `.claude/gdd-continuations/<continuation-id>.json` を読み、新チャットへ必要な情報を復元する。

## Registry

Continuation Registry の保存先は対象 repo root 配下:

```text
.claude/gdd-continuations/<continuation-id>.json
```

**安定場所の定義**: stable storage / 対象 repo root の安定場所とは、削除対象 worktree の外にある canonical repo root 配下の `.claude/gdd-continuations/<continuation-id>.json`、または merge 済み commit に含まれる同等の registry artifact を指す。削除予定の GDD worktree 内だけにある `.claude/gdd-continuations/` は安定場所ではない。

最低限読む field:

- `continuation_id`
- `origin_pr`
- `origin_branch`
- `origin_merge_commit`
- `origin_steering`
- `base_branch`
- `base_commit`
- `remaining_stage_ids`
- `phase_continuity_packet`
- `conversation_history=reference_only`
- `artifact_source=canonical`
- `fact_source=git_pr_ci_test`

## 手順

1. `<continuation-id>` を受け取り、対象 repo root の `.claude/gdd-continuations/<continuation-id>.json` を読む。repo root が複数候補になる場合は、次の固定順で解決する: (1) Task Binding Registry に continuation/task binding がある repo、(2) registry payload の `origin_pr` を `gh pr view` できる repo、(3) registry payload の `origin_branch` が存在する repo、(4) current cwd の repo、(5) `.claude/gdd-continuations/<id>.json` が見つかった repo。複数残る場合は候補を最大 3 件に絞り、解決できなければ新規計画を作らず候補と次の1アクションだけを出す。
2. registry が読めた repo root で `setup-gdd-loop.sh` を bootstrap として実行する。bootstrap はセッション状態の初期化であり、first workflow artifact action ではない。
3. `origin_pr` / `origin_merge_commit` / `base_branch` / `base_commit` を read-only で確認する。確認できない場合は未確認と明記し、会話履歴だけで補完しない。
4. registry が旧 worktree 内だけに存在する場合は、後続 worktree 作成や cleanup の前に対象 repo root の安定場所へコピーまたは再作成する。worktree remove で消える場所にしか registry が無い場合は `Continuation Registry created` とみなさず、cleanup も実装開始もしない。
5. 後続実装は必ず **latest default branch** から **新しい worktree** を作って開始する。古い worktree や merged branch を再利用しない。
   - まず `git fetch --prune origin` などの **git fetch** で remote default branch を更新する。
   - 起点は原則 `origin/<default-branch>`（例: `origin/main`）にする。
   - base_commit と latest default branch がずれている場合は、latest default branch を優先する。差分が大きい、前フェーズ成果が default branch に入っていない、または merge commit を確認できない場合は実装開始せず、post-merge verification blocker として止める。
   - root の作業中ブランチを汚さないため、ローカル main を無理に switch / pull しない。既存 root に branch を切らない。
   - worktree 作成後、current branch / worktree path / steering slug が continuation と一致することを確認する。
6. first workflow artifact action として `requirements.md / design.md / state.md` を作成する。`setup-gdd-loop.sh は bootstrap` として先に実行してよいが、worktree 作成だけでは planning 未完了。
7. `phase_continuity_packet` から以下を requirements / design に反映する。
   - 前フェーズで完了したこと
   - 今回のPRでやること
   - 後続PRに送ること
   - 最終到達点
   - 今回のスコープ / やらないこと
   - 検証方法
   - 自走上限
8. 実装へ入る前に **HITL before implementation** を出す。HITL には、整理した要件、実装する方法・内容、検証する方法・内容、どこまで自走するのか、判断ポイント、段階実装サマリー（複数段階か後続PR着手前の再承認があるとき）を出す。

順序は固定: registry 解決 → bootstrap → read-only facts 確認 → registry persistence 確認 → fetch / new worktree → requirements.md / design.md / state.md → HITL before implementation。PR / CI facts の確認前に worktree 作成へ進まない。

## 禁止

- 会話履歴や compact summary だけから次計画を確定する
- 人間に長文プロンプトの貼り付けを要求する
- `Phase Continuity Packet` なしで段階実装に入る
- `requirements.md / design.md / state.md` が無いまま実装する
- 旧 worktree / merged branch / repo root branch で後続実装を開始する

## 出力

復元できた場合:

```markdown
## GDD Resume

**Continuation ID**: <continuation-id>
**参照した正本**: <repo root>/.claude/gdd-continuations/<continuation-id>.json / <origin steering>
**確認した事実**: PR / merge commit / CI / test
**次の作業場所**: <new worktree path>

ここから `/gdd-dev` と同じ formal workflow に入り、requirements.md / design.md / state.md を作成して HITL before implementation を出します。
```

復元できない場合:

```markdown
## GDD Resume Blocked

**停止理由**: Continuation ID を解決できません
**参照した場所**: .claude/gdd-continuations/
**扱い**: 候補と次の1アクションだけを出し、新規計画や実装は開始しません
**候補**: <見つかった近い continuation id があれば最大 3 件。無ければ `なし`>
**次の1アクション**: continuation id が分かる場合は `/gdd-resume <正しい continuation-id>` を再入力してください。id が分からない場合は、merge 済み PR 番号を添えて `gdd-next-plan` を実行し、registry を作成してください
```
