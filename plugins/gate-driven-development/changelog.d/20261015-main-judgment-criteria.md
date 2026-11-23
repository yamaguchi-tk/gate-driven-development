---
type: minor
---

#### Summary

main（実装している agent）が案・既定・推奨を作るときも、相談役と同じ「選ぶときの基準」に照らすようにした。依頼を黙って縮める判断を減らすため。

- `references/common-guardrails.md` に § 選ぶときの基準（0〜7）を置き、これを正本にした。相談役 3 本（`gdd-opus-advisor`・`-max`・`gdd-fable-advisor`）の本文は、正本を指す 1 文と同じ文の写しにした。相談役は利用する repo で動き、plugin の references を読めないため
- § scope の勝手な拡大 を § scope の勝手な拡大・縮小 にした。main は、次の 4 つを黙って決めない: 範囲の一部を対象外にする / 狭い側を既定・推奨にする / 合格条件・指標を替える / 後回しにする。当たるときは、進める前に、並行の相談役（`gdd-opus-advisor`・`gdd-fable-advisor`）に聞く（2 本が割れたら確認に進む）か、限界に `依頼より狭い` と理由を書いた確認を出す。縮めたら、次に人に示す出力の限界の先頭に `依頼より狭い` と理由を書く
- AC の「開いた入力の扱い」に `構造で閉じる`（設計を変え、範囲を保ったまま入力の形を閉じる）を足し、候補があれば既定にした。合格基準のある AC には `限界として開示する` を使わない。planning reviewer は、前者を `Narrowed Acceptance`（High）、候補があるのに構造で閉じなかったものを `Structural Closure Skipped`（Medium）として指摘する
- human check の既定範囲を狭い側にする根拠は、広い側を採ったときの費用・波及にし、他AC波及 には AC の番号を添える。狭い側にしたら `まだ確認できないこと` に `依頼より狭い` の行を書く
- human check の「整理した要件」の各行に、対応する依頼の原文を `原文: …` で並べる（quick (standard)・standard は `request-crosscheck.md` の表〔対応する行が無ければ `request.md`〕から引く。express は subagent が `原文: main 記入` と書き、表示の前に main が会話の依頼の発言で置き換える。引けなければ `原文: 未取得（理由）`）
- gate の上限を超えたときの方式転換 4 択の推奨は、再設計を先に比べる
- brainstorming の Scope Reduction Check の承認ポイントは、フル版を採用案にする（縮小版を採用案にするのは基準 1 の数値の理由があるときだけ）
- 基準 4 の「測っていない部品」を「測る前の部品」と言い換えた（意味は同じ）

#### Affected Files

- `plugins/gate-driven-development/references/common-guardrails.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/references/requirements-template.md`
- `plugins/gate-driven-development/references/requirements-template-express.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/references/context-budget.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_advisor_agents.py` が、共通の規定の節と相談役 3 本の基準の文の一致を固定する
