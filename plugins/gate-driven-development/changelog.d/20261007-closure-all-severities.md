---
type: patch
---

#### Summary

reviewer の出力に、修正案が閉じるかを書かせるようにした。全 reviewer の `concrete fix` に `閉じ方: 有限集合 | 構造 | 列挙` を添え、`列挙` なら修正後に残る形を 1 行書く。出力の冒頭（Requirements / Design 段階の出力形式では Handoff summary の 1 行目）には `設計の閉じ方: 閉じている | 開いている` を書く。この差分や計画が新しく足す仕組みそのものへの指摘が `列挙` なら `開いている` とし、直す前に、その仕組みが要るか・機械で閉じる設計に変えるか・限界として開示するかを決めるよう添える。gate の判定と route は変えない。

#### Affected Files

- `plugins/gate-driven-development/references/reviewer-common.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
