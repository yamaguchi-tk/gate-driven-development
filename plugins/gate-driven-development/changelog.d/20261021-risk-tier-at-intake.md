---
type: minor
---

#### Summary

- 着手の時点で、タスクのリスクの段（高・低）を判定して steering に記録するようにした（quick (standard)・standard。express から昇格したタスクは昇格のとき）。判定は `gdd-request-code-crosscheck` が行い、`.steering/<task>/request-crosscheck.md` の `### リスクの段` に `リスクの段: 高` か `リスクの段: 低` の 1 行と根拠を書く
- 段の定義は `agents/gdd-request-code-crosscheck.md` § リスクの段（正本）。高は、セキュリティのリスク・トレードオフ（選んだ案でセキュリティ・費用・利用者に見える挙動が変わるものだけ）・認証・権限・課金。低は、文章・テスト・社内ツールと、上に当たらないもの。判定できないとき（crosscheck を起動できず `突き合わせ: unavailable` になったときを含む）は高。trivial・quick (express) には記録が無い
- 今はどの gate・遷移もこの段を読まない。Task Size（Safety Surface を含む）と、人の確認・レビューの選び方は変わらない

#### Changed

- `agents/gdd-request-code-crosscheck.md`（手順 4、§ リスクの段（正本）、出力の `### リスクの段` の節）
- `references/brainstorming-steps.md` の 9（記録の場所を 1 句足した。crosscheck を起動できないときも `リスクの段: 高` を書く）

#### Affected Files

- `agents/gdd-request-code-crosscheck.md`
- `references/brainstorming-steps.md`

#### User Action Required

- 動いているセッションは、開き直すまで古い定義で動く

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
