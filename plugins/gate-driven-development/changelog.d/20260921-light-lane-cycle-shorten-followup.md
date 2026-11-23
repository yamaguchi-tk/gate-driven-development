---
type: patch
---

#### Summary

- root `CLAUDE.md` の軽いレーンの手順 6（独立レビュー）の記述の欠落・矛盾を、PR 旧#162 の「次の PR」項目（G1〜G4・D2〜D5・D7・C3・C5・C6）に沿って直した。plugin を開発する側の手順の精度を上げる変更で、利用者の実行時の挙動は変わらない

#### Changed

- パスの区分（判定のコード / 規則の文書）に 3 manifest（`.claude-plugin/`・`.cursor-plugin/`・`.codex-plugin/` の `plugin.json`）・`evals/`・`.github/workflows/` を足し、`.github/` 全体を判定のコードにしていたのを `workflows/` だけに狭めた（`.github/copilot-instructions.md`・`instructions/` は規則の文書側）。根拠を「版数・配布識別子の宣言だけを目的とするファイルを検査が読んで一致を確認する」に絞り、`CHANGELOG.md`（版の見出し行だけを読まれる）とは区別することを明記した
- テストを削除する、または assert を緩める commit は、巡の無効化・近道の資格判定の両方で判定のコードと同じ扱いにすると明記した
- 最終の全差分巡の後に行う差分巡の reviewer 列に「差分（無効化後）」の表記を足し、中間の差分巡と区別できるようにした（呼び出しテンプレートの `範囲` 欄自体は変えない）
- 近道の 1 巡目が、① の high・blocking と、②③ のうちこの PR で直すものを出さずに終わるときは、先行する差分巡なしにその 1 巡を最終の 1 回にできると明記した
- 手順 5（Codex）の巡の終了時の参照を、最終の全差分巡の後なら手順 7・全レーン共通と同じ「最終の全差分巡の後に commit を積んだとき」に、それより前なら巡の種類を名指しせず通常の巡の流れに戻るよう分けた。あわせて、安全策 4 が発火しているときにこの分岐へ進めるのはユーザーが続行を選んだ後に限ると明記し、安全策 4 の「止める」後の優先規定に手順 5 も含めた
- 変更断片の内容・書式の規則の正本を `CHANGELOG.md` § Policy に置き、`CLAUDE.md`・`CONTRIBUTING.md` の重複記述を pointer に差し替えた（レビューの修正で利用者から見える変更が変わったときだけ push 前の 1 回にまとめて直せる例外も、正本に明記した）。`CLAUDE.md`・`CONTRIBUTING.md` 側の要約が「巡ごとに書き足さない」と絶対形のまま例外を落としていたのを「確定の時機」に縮めた
- 近道の見出しを「判定のコードを含まない変更の近道」に直した（条件が差分の内容ではなく、レーン名でもないことを明確にした）
- 限界の節の見出し「直していない実害クラス」を「直していない常時 High・実害クラス」に直し、実害クラスに当たらない常時 High の残存もカバーした
- 全レーン共通の medium 取り込み規定を、最終の全差分巡より前に取り込んだ場合もカバーするように広げた
- 巡の上限・近道の終了文言から、CI 確認前に「merge-ready とする」と言い切る表現を外し、終了条件の 3 条件（手順 6）と整合させた
- 巡が無効になった後の差分巡に、3 巡目・近道と同じ `next-pr` の扱い（① の blocking でない medium・low）を足し、再試行回数（巡が無効になるたびに 2 回まで）の数え方を明記し、実害クラスが残ったときの限界の節の書き方も足した

#### Affected Files

- root `CLAUDE.md`（軽いレーンの手順 4・5・6、全レーン共通）
- `plugins/gate-driven-development/CONTRIBUTING.md`（項 1d）
- `plugins/gate-driven-development/CHANGELOG.md`（§ Policy）

#### User Action Required

- なし

#### Validation / Eval Impact

- 関係するテスト: `test_always_high_scope_contract.py`・`test_distribution_readiness_contract.py`・`test_independent_review_host_route_contract.py`・`test_light_lane_review_routing_contract.py`・`test_review_log_present.py`・`test_changelog_fragments.py`・`test_governance_contract.py`・`test_light_lane_review_candidates.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
