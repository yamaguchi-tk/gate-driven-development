---
type: patch
---

#### Summary

- Claude のモデル名を版数なしで書く規定（旧#176）の残りを揃えた。表の Claude Code 列を小文字の alias にし、Host Adapter 表の Cursor・Codex の行を他の文書に合わせ、過去の実測と実適用 model の記録の書き方を決めた

#### Changed

- 表の Claude Code 列（`fixed-models.md`・`gdd-model-routing` の tier 表・役割表、`dialectic-review.md` の Host Adapter 表の Claude Code の行）の `Sonnet`・`Haiku`・`Opus` を、小文字の alias（`sonnet`・`haiku`・`opus`）に揃えた。散文は版数なしの family 名で書いてよい
- `dialectic-review.md` の Host Adapter 表で、Cursor の Counter の Opus が版を書いた `dialectic_counter` 行を指すようにした。Codex の Counter から、Codex では使えない Opus を外した（別階層の GPT-5.6 high）
- 過去の実測は「当時の Opus」と日付で書くことにした。実適用 model の記録には、確かめられたら transcript の model ID を併記する
- `gdd-model-routing` の見直しの規定に、Cursor の Counter の版は `fixed-models.md` § モデル名の書き方の 2 行だけを直すことを足した

#### Affected Files

- `references/fixed-models.md`・`references/dialectic-review.md`
- `skills/gdd-model-routing/SKILL.md`・`skills/gdd-pr-review/SKILL.md`・`README.md`
- `tests/test_model_names_without_version_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 関係するテスト: `test_model_names_without_version_contract.py` ほか、変更したファイル名を参照するテスト
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
