---
type: patch
---

#### Summary

利用者から見える変更なし。このリポジトリの軽いレーン（root `CLAUDE.md` 手順 6、配布物ではない）で、軽いレーンが独立レビューの契約から外れる点を列挙する手順 6 の冒頭に、契約 1 を破った巡（reviewer が `テンプレート外の記述あり` を報告した巡）も有効な独立レビューに数えることを足した。テンプレート外の報告の扱いの行に書いた実測値（本数と、誘導・抑制に当たりうるものの件数）を直した。

#### Affected Files

- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_light_lane_review_routing_contract.py`：手順 6 の冒頭がこの扱いを挙げることを固定した。手順 7 の列挙の `unavailable` の行を、前後の区切りまで固定した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
