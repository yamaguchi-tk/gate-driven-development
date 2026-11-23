---
type: minor
---

#### Summary

外部の形式（API 応答・通知 payload・Webhook・ログ書式）の欄の位置や値の形に依存する AC を、実データを読み取り専用で取って fixture にしてから書く順序にした。brainstorming の 8a に実測の手順を足した。standard では、requirements-gating の Spec Self-Review Checklist が human check の前にその有無を見て、design-gating の Step 5d が、値を取り出す規則（正規表現・上限値・抽出位置）を fixture に当てて落ちた件数を記録する。quick (express) は requirements-gating と design-gating を通らないので、確認は brainstorming の 8a だけになる。

#### Added

- `references/brainstorming-steps.md` § 8a の「外部形式の実測」: 判定（この repo の外で作られるデータの欄の位置か値の形を、AC か design が前提にするか）と、AC を書く前に行う実測の手順
  - 読み取り専用の操作だけで取る。secret・認証情報・token を返す操作（`get-secret-value`・`--with-decryption` など）は使わず、鍵の配置は値を返さない操作かマスク済みの sample で得る
  - 取る範囲（期間・件数。producer や通知の種類ごとに 1 件以上）を決めて `findings.md` に書く
  - 生データは worktree の外に置く。構造・値の形・件数を保って値を合成値にした fixture を worktree の中（`.steering/<task>/` かテストの fixture 置き場）に作り、作ったら生データを消す
  - 実値をログ・`findings.md`・steering・commit に書かない
  - 取れないときは、AC に「未測」と理由を書き、取得手段を `Human Check Questions` に出す
- `references/requirements-gating-steps.md` § Spec Self-Review Checklist: 外部形式に依存する AC が fixture を根拠にしているか、未測ならそう出ているかの項目
- `skills/gdd-design-gating/SKILL.md` Step 5d「規則の実値検算」: 規則を fixture（値の形が足りなければ同じ扱いの実データ）に当て、`落ちた件数 / 総件数` と落ちた値の形を `design.md` に記録してから確定する。0 件でなければ規則を直すか落としてよい理由を書き、どちらも無ければ未測と理由を書いて `Open Questions` に出す。記録が無ければ Medium finding

#### Changed

- `skills/gdd-brainstorming/SKILL.md` の 8a: 応答の形・認証・レート制限・ページングの確認結果を `外部依存の確認結果` に、未解決の点を `Open Questions` に書く。外部形式の実測を AC より先に行うことを書き、手順は `references/brainstorming-steps.md` § 8a を指す。`references/brainstorming-steps.md` § 8a の記録先も同じにした
- `references/brainstorming-steps.md` § 9 の「外部依存コンポーネントの実動作調査」: 外部で作られるデータの形に依存するなら、コードを読むだけで終えず § 8a の実測をする
- `skills/gdd-test-driven-development/SKILL.md`: テストの fixture に、§ 8a で作った fixture があればそれを使う
- `skills/gdd-design-gating/SKILL.md` Step 6: Step 3 と重複していた採用技術・access method などの列挙を、Step 3 を指す 1 文にまとめた。Step 6 の扱いは Step 3 の列挙にそろい、official integration の採否も含む。Step 3 の列挙には、Step 6 にだけあった multi-tenant の境界を足した

#### Affected Files

- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/tests/checks/external-format-sampling-tokens.sh`
- `plugins/gate-driven-development/tests/checks/manifest.tsv`
- `plugins/gate-driven-development/tests/test_validate_plugin_check_inventory.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/checks/external-format-sampling-tokens.sh` を足した（`validate-plugin.sh` から BLOCK で呼ぶ）。brainstorming の 8a、requirements-gating の Spec Self-Review Checklist、design-gating の Step 5d に発火点があることを検査する。check の一覧の固定値（`tests/test_validate_plugin_check_inventory.py`）にも足した
