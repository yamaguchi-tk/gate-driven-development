---
type: patch
---

#### Summary

- human check で、人が選べる案が実質無いのに止まり直すのを減らす規定を `references/human-check-template.md` § 止まり直さないもの に足した。次の 4 つでは、判断ポイントにせず、確認を出し直さない
  - 案が実質 1 つの判断（ほかの案が依頼を満たさない・決まったことに反する・結果が推奨と同じ）。AI が推奨で決め、`現在地` か artifact に 1 行書く。判断ポイントが 0 件になったら、OK の範囲を 1 つの判断ポイントにする
  - 相談役 2 本の推奨が、表示した推奨と同じとき。全文を出し直さず、マーカーの無い 1 行だけを書く。1 本目だけが返ったターンでは何も出し直さない
  - 本人が答えた判断を、AC への書き写しや言い直しの確認のために聞き直すこと。`commands/gdd-dev.md` #10 STEP 1 の「明確な承認」に、「推奨で」と、点の番号と案名の組で全点に答えた返答（「1 は B、2 は推奨で」。点が 1 つの確認なら案名だけ）を入れ、修正指示より先に判定する。選んだ案を書き写し、再提示せずに承認へ進む（差が `なし` の点だけ）。点が 2 つ以上の確認で点の番号の無い名指し（「B で」）は、どの点を何にするかを 1 行で聞き返す。承認の語や名指しのほかに変更・条件が付いた返答は修正指示にし、名指しした点は決定済みとして残す。変更でない文（質問など）が付いたら、答えてから承認するかを聞き返す。推奨でない案で AC の意味か express の範囲・Files・Implementation Policy が変わるときは、今までどおり修正指示として扱う。答えていない点が残るときは、答えた点を 1 行と `依頼との差:` で残し、答えていない点だけを判断ポイントにして出し直す
  - 表示済みの確認についての質問への回答・状況報告に、中身の変わらない確認を再掲すること
- 判断ポイントが 0 件になった要件の承認と、Round 上限の一括提示は、今までどおり止まる（Round 上限で現実の案が「修正」だけでも、再入してよいかを 1 つの判断ポイントにして止まる）
- 一次表示の原則 7、§ 判断の書き方 8、却下した代替案の行、Planning Interrupt Decision Menu 2 と、その写し（`requirements-gating-steps.md`・`subagent-dispatch.md`・`rollback-patterns.md`）と `brainstorming-steps.md` の Options Exploration、表示の前に `scripts/lint-hitl-decision-fields.py` を当てる手順を、この節に合わせた

#### Affected Files

- `commands/gdd-dev.md`・`skills/gdd-brainstorming/SKILL.md`・`skills/gdd-requirements-gating/SKILL.md`
- `references/human-check-template.md`・`references/requirements-gating-steps.md`・`references/subagent-dispatch.md`・`references/rollback-patterns.md`・`references/brainstorming-steps.md`
- `tests/checks/skill-body-budget.sh`・`tests/checks/lint-scripts-functional.sh`（express の読み込み量の上限を 30141 から 30208 に上げた）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 2026-11-09〜13 の main の `human-check-waiting` の停止 111 件（fork の重複を除く）のうち、選べる案が実質無かった 48 件を分類した。規定を変えたのは 35 件で、承認の hook の拒否による出し直し 12 件には表示の前の lint の手順だけを足し、AI が決められる処置を聞いた 1 件は既存の規定の違反のまま
