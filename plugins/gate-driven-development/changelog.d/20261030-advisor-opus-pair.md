---
type: minor
---

#### Summary

相談役に並行で相談するとき（判断の委任の `並行`、human check の判断ポイントを表示する前の相談、scope を縮めるときの相談）に、Opus（`gdd-opus-advisor`）と Fable（`gdd-fable-advisor`）を 1 本ずつではなく、`gdd-opus-advisor` を 2 本起動するようにした。過去の相談 16 件の当て直しで、Opus high の 2 本は Opus high と Fable medium の組に劣らず、費用は半分以下だった（組の値は 2026-10-14 時点の定義で回したもの）。Fable は、委任先に `fable` を選んだとき、名指しで意見を求めたとき、利用する repo の規則が名指ししたときだけ起動する。

#### Changed

- `references/autonomy.md` 判断の手順 1：委任先 `並行` で `gdd-opus-advisor` を 2 本起動する。Codex・Cursor では、委任先 `並行` は Fable を起動できずに人間に止まっていたが、その host の `general_heavy_risk` tier のモデルで別コンテキストを 2 つ起動して判断するようになる（Codex で委譲の許可が無いときは、今までどおり人間に止まる）
- `references/human-check-template.md` 項目 7・§ 事前回答：表示前の相談を `gdd-opus-advisor` の 2 本にし、`相談役の推奨:` の行を `Opus-1 <案> / Opus-2 <案>` にした
- `references/human-check-template-compact.md`：`相談役に任せる` の説明と `相談役の推奨:` の欄
- `references/common-guardrails.md` § scope の勝手な拡大・縮小：並行の相談を `gdd-opus-advisor` の 2 本にした
- `references/fixed-models.md` 相談役の段落：起動の条件と根拠の実測
- `agents/gdd-fable-advisor.md` の description：起動の条件から `並行` と項目 7 を外した

#### Affected Files

- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/common-guardrails.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`

#### User Action Required

- なし。委任先の値（`fable`・`opus`・`並行`・`なし`）と、Stop hook の押し返しの条件は変わらない

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 根拠の実測は `review-log/20261030-advisor-opus-pair.notes.md`
