---
type: patch
---

#### Summary

- 要件を固める確認（brainstorming の 9）で 3 回聞いても聞いた行（既存とぶつかる行と、範囲を決める行）が決まらないとき、残った行を human check に回さず、一つ前の突き合わせに戻って見直すようにした。`worklog.md` に `要件確認: 見直し <時刻>` を書き、それまでの返事を足した `request.md` で `gdd-request-code-crosscheck` を起動し直し、`request-crosscheck.md` を上書きしてから確認をやり直す（`### リスクの段` も新しい判定に替わるが、前の段より下げない）。見直しの後の最初の問いは、残った行を細かく割らず、なぜ決まらないのか（依頼の目的・前提）を問う
- 見直しは 1 回まで。見直しの後も 3 回で決まらなければ、`要件確認: 未収束` を書き、依頼の目的から聞き直す 1 問で止まる（human check には回さない）。その返事の後に残った行は、範囲を決める行を全体を対象にした `具体化` に、`既存とぶつかる` の行を AI の仮決定にして、`requirements.md` の § ズレ確認 に書く。確認の中で答えが出た `既存とぶつかる` の行には回答を添えて書く。要件を固める確認で聞いて回答か仮決定を添えた `既存とぶつかる` は、human check の一次表示に載せなくなった（既存側がユーザーの決めた規則・方針の行と、確認を行わなかった経路の行は今までどおり載せる）
- `/gdd-dev` と subagent の返りの扱いで、最後の `要件確認:` 行が `未収束` のときも、`待ち` と同じく質問をそのまま出して止まるようにした

#### Affected Files

- `references/brainstorming-steps.md`・`references/human-check-template.md`・`references/human-check-template-compact.md`・`references/subagent-dispatch.md`・`commands/gdd-dev.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 文書だけの変更。`python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
