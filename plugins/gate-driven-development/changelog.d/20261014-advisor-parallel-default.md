---
type: minor
---

#### Summary

人に human check を表示する前の相談を、Opus high と Fable medium の 2 本に並べた。また、相談役の本文に「選ぶときの基準」を足した。自律モードの判断役と、事前回答の委任先の起動の仕方は変えない（本文の基準は、同じ定義を使うのでこれらにも当たる）。

- `references/human-check-template.md` 項目 7: 表示の前に `gdd-opus-advisor` と `gdd-fable-advisor` を並行に 1 回ずつ起動し、同じ材料（steering のパス・判断ポイント・main の案）だけを渡す。相談ごとの観点や前回の推奨は足さない。2 本が割れた点は main が repo の事実を確かめて推す側を決め、決めきれなければ両方を載せる。行の書式は `相談役の推奨: Opus <案> / Fable <案> / 食い違い: <…>`（`human-check-template-compact.md` も同じ）
- `agents/gdd-opus-advisor.md`・`gdd-opus-advisor-max.md`・`gdd-fable-advisor.md` の本文に「選ぶときの基準」（0〜7）を足した。ユーザーがすでに決めたことを先に見る、依頼を縮めない、設計変更で完全に閉じるなら先に推す、同じ入力空間なら広い側、などである。選択肢に無い案を推すのは、基準 3 に当たるときだけにした
- 人に示す限界は、限界ごとに種類（`依頼より狭い`・`リスクが低い`・`費用に見合わない`・`その他`）を先頭に書く。縮めた要件と、気にしなくてよい限界を見分けられるようにするため。定義は `references/common-guardrails.md` § Honest Limitations に置き、`requirements.md` の Honest Limitations、human check の `まだ確認できないこと`、Handoff の限界、相談役の `残る限界:` が同じ種類を書く
- 選択肢に無い案を推すのは、どの選択肢も依頼を縮めるとき、または閉じる設計変更・撤去の案が並んでいないときにする
- 敵対的に作らないと出ない形を限界にしてよい基準は、GDD 自身の hook・gate だけに当てる
- `gdd-opus-advisor`・`gdd-fable-advisor` の description に、項目 7 の表示前の相談を起動の場面として足した
- `references/fixed-models.md` の相談役の段落に、2026-10-14 の再投入と、基準を入れた根拠の数字を足した

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/common-guardrails.md`
- `plugins/gate-driven-development/references/requirements-template.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`

#### User Action Required

- なし。人に表示する前の相談 1 回あたりの費用は、Opus high 単独より増える（金額は未測）

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
