---
type: minor
---

#### Summary

planning reviewer（`gdd-planning-reviewer`）と implementation reviewer（`gdd-implementation-reviewer`）は、計画 doc の全文と plugin の reference を毎回読んでおり、時間の上限も無かった（2026-10-02 の実測では、requirements レビュー 1 回が約 115 分と約 320 分かかり、2 回目は 10 分無応答で stream watchdog に止められた）。今後は、gate から起動する reviewer の入力を「変更点・AC 表・blocking の定義」を中心にした 1 枚に絞り、計画 doc と plugin の reference はパスと節だけを渡す。blocking の指摘には具体的な失敗シナリオを必須にし、起動した側が再現を確かめてから受け入れる（§ 常時 High・実害クラス・security reviewer の指摘は、再現できなくても blocking のまま）。時間上限は planning 30 分・implementation 20 分で、超えたら入力を狭めて 1 回だけ再実行し、それでも返らなければその回を消費済みとして人間に渡す。AC ID の突合などの機械的な整合は、新しい script が行う。

#### Added

- `references/subagent-dispatch.md` § Reviewer Input and Time Budget: 入力の 1 枚（`.steering/<task>/review-input/<gate>-round-<N>.md`。gate ごとの中身、`Worktree:` の行、`機械検査:` の行）、パスだけ渡すもの、blocking の条件（`failure scenario` 必須・再現の確認と、その例外）、時間上限と Claude Code での監視手順（background 起動の reviewer と `sleep` の期限 timer の先着。`/loop` の dynamic mode では `ScheduleWakeup`）、所要時間の記録、超過・無応答のときの扱い、計れない経路での記録を定める正本
- `scripts/lint-plan-consistency.py`: requirements.md の `## 受入条件` に無い AC を Summary Brief・Implementation Sequence Plan・design.md が引用している、またはそこで AC を定義し直している、`## 受入条件` 節が無い、コード fence が閉じていない、を ERROR（exit 1）にする。AC ID を 1 つだけ含む引用行の数値（分・秒・時間・行・件・回・日・巡・%・MB・KB）が、その AC の定義の同じ単位の数値と食い違うときは WARN だけを出す。閉じたコード fence（開きと同じ記号・同じ長さ以上で、info string の無い行で閉じる）の中の行と、Implementation Sequence Plan の表の行の数値は見ない。`3 分割` などは分として数えない

#### Changed

- `agents/gdd-planning-reviewer.md`・`agents/gdd-implementation-reviewer.md`: gate から 1 枚を渡されたときは、計画 doc の全文と plugin の `references/` を通読せず、1 枚が名指しした節（reference はこの定義が名指しした節も）だけを読む。実コード・最新 Round の `reviews.md`（planning）・呼び出し側と対になる実装（implementation）は従来どおり読む。blocking の指摘に `failure scenario` を付け、付けられないものは advisory にする（§ 常時 High・実害クラスを除く）。1 枚を渡されない起動（`gdd-requesting-code-review` など）は従来どおり
- `references/reviewer-common.md`: 出力書式の impact に、blocking なら failure scenario を書くと足した
- `references/requirements-gating-steps.md`: reviews.md の `判定:` に `timeout` を足した
- `skills/gdd-requirements-gating/SKILL.md`・`skills/gdd-design-gating/SKILL.md`・`skills/gdd-implementation-gating/SKILL.md`（escalation のとき）・`references/requirements-gating-steps.md`: reviewer の起動を上の節に従わせる
- 行と token の予算に収めるため、内容を変えずに次をまとめた: `references/self-contained-contract.md`・`references/phase-progression.md` の重複していた reviewer selection の行と Plan mode の行、`skills/gdd-design-gating/SKILL.md` 冒頭の Goal と重複していた reviewer の文、`skills/gdd-requirements-gating/SKILL.md` の手順の概要のうち詳細手順と重複していた反映時機の文

#### Affected Files

- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/self-contained-contract.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-implementation-reviewer.md`
- `plugins/gate-driven-development/skills/gdd-requirements-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/scripts/lint-plan-consistency.py`
- `plugins/gate-driven-development/tests/test_lint_plan_consistency.py`
- `plugins/gate-driven-development/tests/checks/lint-scripts-syntax.sh`
- `plugins/gate-driven-development/tests/checks/lint-scripts-functional.sh`

#### User Action Required

- reviewer が時間上限を 2 回続けて超えると、requirements は一括提示の `human-check-waiting` で、design と implementation は `blocked` で止まるようになった。人間が選択肢に答えるか、原因を除いて `/gdd-dev resume` で再開する
- 動いているセッションは、agent 定義をセッションの開始時にしか読み込まないので、新しい入力の範囲は開き直した後のセッションから効く

#### Validation / Eval Impact

- `tests/test_lint_plan_consistency.py` を足した（引用先の欠落・再定義・受入条件の欠落の ERROR、数値の食い違いの WARN、AC を 2 つ含む行・単位が違う数値・`分割`・段階計画の表の行・コード fence の中の行・design.md が無いときの素通り、閉じ忘れの fence と、記号・長さの違う行では閉じない fence の後ろの ERROR）
- `tests/checks/lint-scripts-syntax.sh`・`tests/checks/lint-scripts-functional.sh` に `lint-plan-consistency.py` を足した
