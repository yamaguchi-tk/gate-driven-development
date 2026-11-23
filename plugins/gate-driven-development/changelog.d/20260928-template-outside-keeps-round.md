---
type: patch
---

#### Summary

利用者から見える変更なし。このリポジトリの軽いレーンの独立レビュー（root `CLAUDE.md` 手順 6、配布物ではない）で、reviewer が `advisory: テンプレート外の記述あり` を報告した巡の扱いを定めた。巡は有効のままにして起動し直さず、見つかった指摘はほかの巡と同じく振り分け、報告された記述は次の巡の前に prompt と抜粋から除く。あわせて、終了条件の例外を「PR 本文に書かせる `unavailable` の行」に限り、手順 7 の PR 本文の列挙にもその行を入れた。

#### Affected Files

- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_light_lane_review_routing_contract.py`：テンプレート外の報告を受けた巡の扱い（有効のまま・起動し直さない・振り分ける・次の巡の前に除く）のテストを足した。終了条件の例外の句を「PR 本文に」と「巡の sha と結果とは別に」まで延ばし、「だけを書き（…）」の括弧の中にあることを固定した。手順 7 の列挙に `unavailable` の行があることを固定した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
