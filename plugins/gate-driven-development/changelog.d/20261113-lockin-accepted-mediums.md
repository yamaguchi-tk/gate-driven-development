---
type: patch
---

#### Summary

- 要件を固める確認の見直しで、突き合わせの結果を上書きする前に、それまでの `request-crosscheck.md` を `request-crosscheck.before-revisit.md` に写すようにした。上書きの後、答えから足していた `原文だけでは決まらない` の行が新しい出力に無ければ足し直す。突き合わせを起動し直せないときは上書きせず、前の出力のまま `要件確認: 未収束` に進む
- 見直しの後も決まらなかった `既存とぶつかる` の行を AI が仮決定するとき、依頼の原文どおりになる側にし、依頼を既存に合わせて狭めないようにした
- requirements-gating の範囲の狭めの検査（Step 4c）で、仮決定を添えた `既存とぶつかる` の行も reviewer に写し、依頼を既存に合わせて狭めた仮決定を blocking にする

#### Affected Files

- `references/brainstorming-steps.md`・`references/requirements-gating-steps.md`・`references/subagent-dispatch.md`・`agents/gdd-planning-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 文書だけの変更。`python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
