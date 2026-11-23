---
type: patch
---

#### Summary

利用者から見える変更なし。このリポジトリの軽いレーンの独立レビューで、手順 7 が GitHub の PR 本文に書かせる節を、reviewer に渡す PR 本文の抜粋が抜く節（目的・変更内容・限界）と同じにした（配布物ではない root `CLAUDE.md` と `AGENTS.md` の変更）。限界の節からは、受け入れた指摘の記録を除く。`AGENTS.md` が依頼なしに reviewer へ送ってよい材料に、呼び出し元の候補と PR 本文の抜粋を足した。規定を固定する契約テストを、語だけでなく向きまで見るように強めた。

#### Affected Files

- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_light_lane_review_routing_contract.py`：手順 7 の PR 本文が抜粋の抜く節を持つこと、`AGENTS.md` が手順 6 の材料を挙げることのテストを足した。契約 1 を緩める向き・巡の sha と結果と受け入れた指摘を除く向き・reviewer が報告して判断に使わない向き・読み込みが合わないときに巡を無効にする扱いを、句で固定した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
