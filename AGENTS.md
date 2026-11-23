# AGENTS.md

このリポジトリの開発ルールは、root の [`CLAUDE.md`](CLAUDE.md) に従う。作業を始める前に読むこと。

操作の承認境界（merge・デプロイ・force push・インフラ操作・機密情報の扱い）は、各エージェントのグローバル設定と、[`plugins/gate-driven-development/docs/PROJECT_CLAUDE_MD_TEMPLATE.md`](plugins/gate-driven-development/docs/PROJECT_CLAUDE_MD_TEMPLATE.md) の「2. Operational Safety」「3. Secrets 保護」「4. ブランチ・PR」に従う。このリポジトリで緩める規定は無い。加えて、デプロイ（本番以外も含む）と、次に挙げる操作を超える外部への投稿・送信は、1 操作ごとにユーザーの明示的な依頼を取る。依頼なしに行ってよいのは、`CLAUDE.md` の手順に沿った push、PR の作成と本文の更新、`CLAUDE.md` 手順 5 の条件で使うときの Codex レビューへの差分の送信、`CLAUDE.md` の L1+ 安全策 1・4 が求める Opus への相談と、手順 6 の独立レビューの reviewer への、手順が渡すよう求める材料（差分・呼び出し元の候補・実コード・変更案・方針メモの草案・PR 本文の抜粋（PR 作成前は草案）・依頼の原文（`review-log/<slug>.request.md` の写し）・review-log の場所）の送信（機密情報を含むファイルは送らない）、`CLAUDE.md` の全レーン共通が定める、後回し（`deferred`）にした指摘の Issue の作成、PR レビューのコメントへのインラインの返信、PR を閉じる依頼を受けたときの、`CLAUDE.md` の全レーン共通が定める行き先のコメントだけである。

Claude Code 以外のエージェント（Codex・Cursor など）向けの入口である。`CLAUDE.md` の本文はここに複製しない（正本は `CLAUDE.md` の 1 か所）。Claude Code 固有の手順（Agent の model 指定、agent 定義、memory の照合、Codex の呼び出し）の代わりは、下の「Claude Code 以外で読むとき」に従う。下の手順の番号は `CLAUDE.md` のものである。

## Claude Code 以外で読むとき

AGENTS.md 経由で Codex・Cursor などが読むと、Claude Code 固有の手順は実行できない。代わりは次のとおりにする。

- 手順 6 の独立レビュー：`plugins/gate-driven-development/references/fixed-models.md` の `independent_review` tier の、その runtime の列のモデル（Cursor は `Grok 4.6` + `reasoning.effort=high`、Codex は `gpt-5.6-sol` + `reasoning.effort=high`）で、会話を引き継がない read-only の別コンテキストを起動し、`.claude/agents/light-lane-independent-reviewer.md` の本文と埋めたテンプレートをそのまま渡す。merge-ready の条件の `model: opus` は、列のモデルと effort で走ったときに満たしたものとする
  - agent 定義を直接起動しない。frontmatter の `model: opus` は Cursor の Task では解決できずに起動が落ちる。Codex では agent 定義による起動を前提にしない（未実測）。別コンテキストは列のモデルと effort を明示して起動し、定義の本文（frontmatter を除く）と埋めたテンプレートを prompt に貼る。frontmatter を除くと `tools: Read, Grep, Glob` の制限が落ちるので、起動側で使えるツールを Read・Grep・Glob 相当に絞る（Cursor は Task の readonly 指定。指定の有無は未確認。Codex は read-only の sandbox）。絞れないときは、read-only が散文だけの規定になったことを記録する（reviewer 列に書く）
  - 明示できないときだけ inherit にし、main が列と同じモデル・effort であることを確かめる。reviewer 列にはモデルと effort の両方を書く。届かない、または確かめられないときは merge-ready とは言わず、PR 本文に `独立レビュー: unavailable（model 条件未達: <実際のモデル・effort>）` と書いてユーザーに渡す
  - Codex では、`plugins/gate-driven-development/references/codex.md` § Codex Subagent Delegation Permission の許可があるときだけ起動する。許可が無いときは inline で代替せず（実装文脈を渡さない契約を満たさない）、上と同じく `独立レビュー: unavailable（委譲許可なし）` にする
  - 起動に失敗しても、すぐに unavailable と書かない。先にこの経路を 1 回試す。それでも起動できなければ、上と同じく `独立レビュー: unavailable（理由）` にする
- 安全策 1 と手順 6 の再設計の Opus 設計レビュー：安全策 1 の「Opus を呼べないとき」に従う
- 方針メモの memory の照合（リポジトリの外の `~/.claude/projects/.../memory`）：読めなければ、方針メモのその項目に `memory 照合: unavailable（理由）` と書く
- 手順 5 の Codex：Codex 自身が実装しているときは別系統にならないので使わない
