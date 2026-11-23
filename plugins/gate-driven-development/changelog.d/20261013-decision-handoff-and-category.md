---
type: patch
---

#### Summary

`references/independent-review.md` の (3-f)（後で実装する guard・contract test の Decision への finding）を 2 点直した。

- 後続の test の要件として Issue に写した申し送りがある Decision は、Task Size によらず repo ADR へ蒸留し、その Consequences に「この Decision の guard・contract test を実装するときは Issue #<N> の要件を満たす」と書く（蒸留の前なら steering の `adr.md` に書いて、蒸留で運ぶ）。guard・contract test を実装する作業は Decision を読むので、そこから Issue に届く。これまでは「task が無いときは着手時に main session が Issue を読む」としか書いておらず、別のセッションがその Issue を知る手段が無かった
- 承認済みの Decision の列挙の形への finding も、high でなければ経路 P 型と同じ category（テストの判別力不足の値。実害クラスを付けない）にする。これまでは category を決めておらず、reviewer が実害クラスを付けると、承認済みの Decision が差し戻されていた

#### Affected Files

- `plugins/gate-driven-development/references/independent-review.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
