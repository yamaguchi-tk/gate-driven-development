---
type: minor
---

#### Summary

自律モード（`GDD Autonomy: internal`）で判断役にする model を、`.gdd-config.md` の `GDD Autonomy Advisor: opus | fable` の行で選べるようにした。行が無ければ、これまでどおり Opus が判断役になる。

- `GDD Autonomy Advisor: fable` のときは、判断役そのものを Fable にする（Agent tool の `model: fable`）。Opus は呼ばず、食い違ったときに Fable に第二意見を求める手順も飛ばす
- 行が 2 つ以上ある、または値が `opus`・`fable` 以外のときは、判定できないものとして人間に止まる。Fable を起動できないときも、Opus に替えずに止まる
- 宣言と同じく、この行はユーザーが書く。エージェントは書かない。判断点ごとに読み直すので、書き換えれば次の判断点から効く
- worklog の `自律判断:` の行は、判断役が Fable のとき `Fable: 判断役` と書き、第二意見の回数（1 steering あたり 1 回）には数えない

#### Changed

- `references/autonomy.md` の § 宣言、§ 判断の手順 1・3・5、§ 限界

#### Affected Files

- `plugins/gate-driven-development/references/autonomy.md`

#### User Action Required

- Fable を判断役にしたいプロジェクトは、`.gdd-config.md` に `GDD Autonomy Advisor: fable` を書く（`GDD Autonomy: internal` がある場合だけ効く）

#### Validation / Eval Impact

- 文書だけの変更。`.gdd-config.md` に判断役の行がある状況で、判断役の起動・第二意見・不正な値・起動できないとき・worklog の欄の 5 問を、変更前後の文書で main 役に答えさせた
