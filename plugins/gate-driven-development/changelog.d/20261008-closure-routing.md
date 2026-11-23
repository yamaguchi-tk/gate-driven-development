---
type: patch
---

#### Summary

`references/reviewer-common.md` § Fix の影響範囲 で、`設計の閉じ方:` を書く位置を出力形式ごとに書き分けた。Implementation 段階の出力形式では冒頭、Requirements / Design 段階の出力形式では末尾の Handoff summary の 1 行目である。

#### Affected Files

- `plugins/gate-driven-development/references/reviewer-common.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
