---
lane: L1+
pr: 91
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | general-purpose subagent (advisory review, pre-commit diff, 経緯非共有相当)。本行は compaction 後の会話要約から再構成しており、指摘の severity/クラスタ分類は本 session が要約を根拠に再判定したもの（原文 transcript は未再確認） | - | 3 | 4 | 0 | 2026-09-15T20:00+09:00 |
| 独立-1 | general-purpose subagent (read-only, diff-only, 経緯非共有; git worktree add --detach での実行込み) | 04dddd5 | 0 | 1 | 0 | 2026-09-16T00:15+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#91 review, インラインコメント3件) | 5170e96 | 1 | 2 | 0 | 2026-09-16T10:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | high | yes | self-inflicted | next-action-routing-source | fixed | Next Action を tasklist.md からしか読んでおらず、実運用で多い state.md 側の記載を取りこぼしていた |
| pm-2 | 方針メモ | high | yes | self-inflicted | build-phases-coverage | fixed | BUILD_PHASES に gdd-subagent-driven-implementation 等 4 工程が抜けており、それらの起動では判定が働かなかった |
| pm-3 | 方針メモ | high | yes | self-inflicted | phase-materials-timing | deferred | brainstorming/requirements/design の初回 dispatch は steering 作成前か human-check-waiting 経由のため、Resume From も Next Action も読めず判定できない構造的な限界 |
| pm-4 | 方針メモ | medium | yes | self-inflicted | next-action-routing-source | fixed | 3 gate 未承認（draft）の tasklist.md に書かれた仮置きの Next Action を routing source として使ってしまっていた |
| pm-5 | 方針メモ | medium | yes | self-inflicted | next-action-normalization | fixed | Next Action の値に付く装飾（reason 付記等）を正規化せず、既存 hook と異なる読み方になっていた |
| pm-6 | 方針メモ | medium | yes | self-inflicted | subagent-type-symmetry | fixed | MODEL_FIXED_SUBAGENT_TYPES の判定が plugin prefix 付き名だけを受理し、bare 名（prefix 無し）で渡ってくるケースに非対称だった |
| pm-7 | 方針メモ | medium | yes | self-inflicted | phase-tier-scope | fixed | formal gate 中に Explore 等の読み取り専用調査 agent を model 未指定で dispatch すると誤って warn していた |
| pm-8 | 方針メモ | low | yes | self-inflicted | warn-only-error-handling | fixed | hook 末尾の python3 呼び出しに OR true 相当のフォールバックが無く、set -euo pipefail 下で失敗すると warn-only の設計に反して非 0 終了しうる余地があった |
| pm-9 | 方針メモ | low | no | self-inflicted | unspecified-vs-parse-failure | accepted | payload の JSON parse 失敗と model 未指定を区別しておらず、前者も「未指定」として扱われる。warn-only のため実害は小さいと判断し区別しない |
| pm-10 | 方針メモ | low | no | self-inflicted | changelog-fragment | fixed | changelog.d/ への断片追加自体がまだ行われていなかった |
| pm-11 | 方針メモ | low | no | self-inflicted | doc-line-citation-stability | accepted | 参照コメント中の CHANGELOG.md の行番号引用（例: `CHANGELOG.md:94-95`）が将来の編集で陳腐化しうる。本 PR のスコープでは対応しない |
| pm-12 | 方針メモ | low | no | self-inflicted | resolver-load-failure-handling | accepted | `_load_resolver()` が失敗すると例外が外側の OR true 相当のフォールバックで握りつぶされ無言の no-op になる。warn-only の設計方針とは整合しており、意図した挙動として受け入れる |
| ind1-1 | 独立-1 | medium | yes | self-inflicted | hook-timeout-budget | fixed | hooks.json の Agent matcher の timeout=5 が、1 回の起動で python3 を最大 4 回逐次 spawn する構成に対して実測でマージン不足（最大 5.33 秒で超過）だった |
| ind1-2 | 独立-1 | low | no | self-inflicted | planning-phases-coverage | accepted | PLANNING_PHASES が state-machine.md の Resume From 許容値表にある gdd-task-breakdown を含んでおらず非対称。ただし references/fixed-models.md に既知の限界として開示済みで実害は小さい |
| ind1-3 | 独立-1 | low | no | self-inflicted | fail-open-test-coverage | fixed | 不正 JSON・非 dict tool_input・非文字列 model 等の例外系入力を直接叩く統合テストが無く、fail-open 性を担保する回帰が無かった |
| pr1-1 | PR後-1 | high | yes | self-inflicted | fixed-reviewer-exemption-scope | fixed | 固定 reviewer subagent を subagent_type だけで免除しており、起動時に model を明示的にダウングレードされても判定していなかった。Claude Code の model 解決順は起動時 model が agent frontmatter より優先されるため、実測で model=sonnet 明示指定時に見逃していた |
| pr1-2 | PR後-1 | medium | yes | self-inflicted | model-id-normalization | fixed | 許容判定が opus/sonnet の alias としか比較しておらず、claude-opus-5 等の full ID を不適切な model と誤警告していた |
| pr1-3 | PR後-1 | medium | yes | self-inflicted | payload-extraction-transport | fixed | tool_input の抽出で payload 全体を argv 経由（sys.argv[1]）で渡しており、大きな prompt を含む起動で ARG_MAX を超えて抽出が失敗しうる（かつ prompt がプロセス一覧に露出しうる）構成だった |
