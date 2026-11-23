---
type: minor
---

#### Summary

GDD の 7 つの agent 定義（formal-gate-runner・light-task-runner・code-simplifier・reviewer 4 種）に `tools:` の許可リストを付けた。これまでは親の全ツールを受け取っていた。MCP やブラウザのツール定義を含めると、起動しただけで文脈が約 70k トークンになり、subagent が呼び出すたびに読み直されていた。許可リストは次のとおり。

- 共通: Read・Grep・Glob・Bash・Edit・Write・Monitor・TaskStop
- reviewer 4 種: 共通に WebFetch・WebSearch を足す
- formal-gate-runner: reviewer と同じものに、reviewer や評価者を入れ子で起動するための Agent を足す

subagent は MCP のツールを使えなくなる。reviewer・light-task-runner・code-simplifier は入れ子の起動もしなくなる。MCP でしか読めない URL（社内の wiki・チケット管理・Slack など）は、`/gdd-dev` の main が brainstorming の dispatch の前に MCP で読み、一時ファイルで渡す。runner は一時ファイルを渡された URL を WebFetch しない。WebFetch で本文が取れない URL では、推測で進めずに `clarification-needed` で止まる。completion-check の runner の中の `gdd-pr-review` は、Skill tool を持たないので同梱の `pr-review.md` で動く。

#### Changed

- `agents/*.md` の frontmatter に `tools:` を追加
- `commands/gdd-dev.md` の instruction 7（brainstorming の dispatch）に、MCP でしか読めない URL を main が読んで一時ファイルで渡す手順を追加
- `references/subagent-dispatch.md` の brainstorming Template の `読むファイル` と実行手順 0 に、一時ファイルの受け取り方と、本文が取れない URL で止まることを追加
- `references/subagent-dispatch.md` § Typed Agent Resolution の起動し直しの条件に、`tools:` の名前が解決できず起動に失敗したときを追加
- `skills/gdd-pr-review/SKILL.md` の手順 1 で、Skill tool が使えないときも同梱の `pr-review.md` を読む
- `CONTRIBUTING.md` の reviewer agent の節に、新しい agent は許可リストを決めることを追加

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-formal-gate-runner.md`
- `plugins/gate-driven-development/agents/gdd-light-task-runner.md`
- `plugins/gate-driven-development/agents/gdd-code-simplifier.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-implementation-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-security-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-completion-reviewer.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`

#### User Action Required

- agent 定義はセッションの開始時にしか読み込まれない。すでに動いているセッションには反映されない。新しいセッションから効く
- 公式ドキュメントでは、許可リストの名前が解決できない Claude Code で subagent の起動がエラーになる（未実測）。そのときは `references/subagent-dispatch.md` § Typed Agent Resolution の手順で、general-purpose で 1 回だけ起動し直す

#### Validation / Eval Impact

- `tests/test_agent_tool_allowlist_contract.py` を追加した。次を固定する
  - 各 agent の許可リスト
  - 名前が閉じた集合に入っていること
  - 入れ子で起動できるのは formal-gate-runner だけであること
  - Template から許可リストを持つ agent に届くこと
  - MCP の URL の渡し方（`/gdd-dev` の instruction 7 が `<URL> → <絶対パス>` の対で書き、Template の手順 0 が読む。本文が取れない URL で止まる）
  - Skill tool が無い runner の中での `gdd-pr-review` の手順 1 と、`tools:` の名前が解決できないときの起動し直し
