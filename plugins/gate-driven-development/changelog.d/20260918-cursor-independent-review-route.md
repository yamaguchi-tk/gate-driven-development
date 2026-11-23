---
type: patch
---

#### Summary

- Cursor / Codex で独立レビューを起動する経路を書いた。agent 定義（frontmatter `model: opus`）を Cursor の Task でそのまま起動すると Opus に解決できずに落ちる（2026-09-18 実測。inherit なら起動できた）。この失敗から、PR に独立レビューを「unavailable」と誤記していた
- `independent_review` tier を `scripts/resolve-gdd-model.py` の `TIER_TO_MODEL` に足し、`references/fixed-models.md` の表の `independent_review` 行と実装を一致させた

#### Changed

- `references/cursor.md`・`references/codex.md`: tier 表に `independent_review` の行を足し、独立レビューの起動の箇条を足した（cursor.md は § 初稿とレビュー、codex.md は § 方針）。モデルは `fixed-models.md` の `independent_review` tier の host 列（Cursor: `Grok 4.6` + `reasoning.effort=high`、Codex: `gpt-5.6-sol` + `reasoning.effort=high`）を使う。agent 定義は直接起動せず、列のモデルと effort を明示して read-only の別コンテキストを起動し、定義の本文と埋めたテンプレートを prompt に貼る。frontmatter を除くと `tools: Read, Grep, Glob` の制限が落ちるので、起動側で使えるツールを Read・Grep・Glob 相当に絞り（Cursor は Task の readonly 指定、Codex は read-only の sandbox）、絞れないときは read-only が散文だけの規定になったことを記録する。明示できないときだけ inherit にし、main が列と同じモデル・effort であることを確かめる。記録にはモデルと effort の両方を書き、列に届かない・確かめられないときはモデル条件を満たしたとしない（unavailable（model 条件未達））。Codex では、独立レビューも § Codex Subagent Delegation Permission の許可があるときだけ起動し、許可が無ければ inline で代替せずに unavailable（委譲許可なし）と記録する。起動に失敗しても、この経路を 1 回試すまでは unavailable と記録しない（旧#131）
- GDD の `agents/*.md` の reviewer を Cursor / Codex で起動する経路を、既存のフォールバックと揃えた（旧#132）。Cursor は、定義のままで起動できなければ本文を貼る経路を試し、それも不可なら inline review にフォールバックする（`references/cursor.md`・`references/faq.md`・`references/cursor-guide.md`）。Codex は § Codex Subagent Delegation Permission の許可があるときだけ本文を貼る経路で起動し、許可が無ければ main session inline execution で実行する（`references/codex.md`、`references/subagent-dispatch.md` と同じ）。GDD の reviewer はツールと sandbox を定義どおりにし、read-only に絞らない（Read・Grep・Glob への制限は独立レビューだけ）
- `scripts/resolve-gdd-model.py`: `TIER_TO_MODEL` の 3 runtime と `resolve_effort` に `independent_review` を足した（Claude Code: `opus` + `max`、Cursor: `grok-4.6` + `high`、Codex: `gpt-5.6-sol` + `high`）
- plugin の外: root `CLAUDE.md`「Claude Code 以外で読むとき」の独立レビューを、「その runtime で使える最上位のモデル」から `fixed-models.md` の `independent_review` tier の参照に直し、同じ起動経路を書いた
- `references/cursor.md` § 初稿とレビュー の「GPT 系 / `effort=none` は使わない」を削った。§ 方針 の「使わないもの」と同じ内容で、references の行予算に収めるため

#### Added

- `tests/test_independent_review_host_route_contract.py`: resolver と `fixed-models.md` の `independent_review` 行の一致、cursor.md / codex.md の tier 行、root `CLAUDE.md` と両 reference の起動経路の記述を固定する契約テスト

#### Affected Files

- `references/cursor.md`
- `references/codex.md`
- `references/faq.md`
- `references/cursor-guide.md`
- `scripts/resolve-gdd-model.py`
- `tests/test_independent_review_host_route_contract.py`
- plugin の外: root `CLAUDE.md`

#### User Action Required

- 利用者の操作は不要。Cursor / Codex で独立レビューを起動するときは、agent 定義を直接起動せずに本文を prompt に貼る

#### Known Limitations

- `independent_review` のキーは `--complexity` の選択肢に無く、resolver の CLI・worker runner からは届かない（独立レビューは worker runner 経由で起動しないため）。表との同期のためのキーである
- Codex で agent 定義の起動が落ちることは未実測（Codex では agent 定義による起動を前提にせず、Anthropic のモデルも使えないため、同じ経路を書いた）
- inherit で起動したときに main のモデル・effort が列と同じかを確かめるのは、実行する agent の自己申告に依存する
- 起動経路は散文の規定で、Cursor / Codex での機械的な強制は無い
- Cursor の Task に readonly の指定があるかは未確認。指定できなければ、独立レビューの read-only は散文だけの規定になる

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
