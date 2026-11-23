---
type: minor
---

#### Summary

- human check の「判断の委任」の既定を `人に止める` から `Fable に任せる` に替えた。最初の human check（計画・要件の承認）は今までどおり人が見る。返事が `OK` だけなら、承認の後の human check は Fable の相談役が判断する
- 選んだ委任の値は、承認のときに `state.md` の `Approved Direction` の `- 判断の委任: <fable | opus | 並行 | 人に止める>` の欄に書く。「判断の委任」の行は最初の human check にだけ出し、後の human check の `OK` は欄を変えない。会話で「人に止めて」と言えば、欄はすぐ `人に止める` になる。後続 Stage の steering には欄の値を写す
- 委任したときに人に戻す条件を、承認した要件（依頼の原文・AC・信頼境界・承認した契約）を満たせない見込みになった、または満たさない方向に変える（AC・scope を削る・弱める・意味を変える、信頼境界を外す・緩める）ときと、止まる側に倒す仕組み（判定できない・起動できない・本人の新しい入力など）と、許可の境界（自走上限など）だけにした。依頼の範囲の中で AC・scope を足す・具体化する、技術スタック・設計を変える、確認に並んでいない案を採る、は委任先が決める。依頼より広げる案は採らずに止まらず進み、`範囲を広げる提案` として完了の報告と PR 本文で示す
- Stop hook は、bind 済み steering の `state.md` に `判断の委任` の欄がちょうど 1 つあり、値が `fable`・`opus`・`並行` なら、`事前回答:` 行が無くても human check での停止を 1 回押し返す。欄が `人に止める`・読めない値・2 つ以上なら押し返さない。欄の無い steering は、今までどおり最後の `事前回答:` 行で決める
- 最初の human check の「人間に戻す主な条件」のひな形と compact 版、`/gdd-dev` の Approved Direction の例を同じ原則にそろえた

#### Affected Files

- `hooks/scripts/lib/autonomy_pushback.py`
- `references/human-check-template.md`・`references/subagent-dispatch.md`・`references/rollback-patterns.md`・`skills/gdd-pr-review-followup/SKILL.md`・`references/human-check-template-compact.md`・`references/requirements-template.md`・`references/autonomy.md`・`references/state-machine.md`・`commands/gdd-dev.md`・`README.md`・`evals/evals.json`
- `tests/test_stop_hook_autonomy_pushback.py`

#### User Action Required

- 承認の後の判断を自分で見たいときは、最初の human check の「判断の委任」で `人に止める` を選ぶか、承認の後に会話で「人に止めて」と言う。`OK` だけでは Fable に任せる
- Fable の相談は 1 本 約 $3.6（作者の環境、2026-11-13 の 4 件の試し）で、利用枠を使う。Fable を起動できない環境では、今までどおり人に止まる
- 進行中の steering（欄が無いもの）は今までの `事前回答:` 行の扱いのままで、既定は変わらない

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_stop_hook_autonomy_pushback.py` に、欄による押し返し・`人に止める`・読めない欄・code fence の中の欄・欄の後の停止の行・`state.md` が読めないときの fallback のテストを足した
