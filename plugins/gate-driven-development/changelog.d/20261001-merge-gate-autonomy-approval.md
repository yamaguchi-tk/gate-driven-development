---
type: minor
---

#### Summary

自走上限に「マージまで」「マージ・デプロイ・QA まで」を選んだタスクでは、利用者の例外（`~/.gdd/config.local.md` の `GDD Post-PR Autonomy Exception: on`）があれば、マージの前に `Merge Approval` を問わない。main がマージの直前に `Merge Approval: PR #<n> / head <sha> | evidence: post-pr-autonomy:<自走上限の値> | approved_at: <ISO 8601>` を書いてマージする。merge gate（hook）は変えていない。

#### Changed

- `references/post-merge-qa.md` § 宣言に、利用者の例外の行を足した。repo の外の `~/.gdd/config.local.md` だけを、`references/autonomy.md` § 宣言と同じ読み方（コードフェンス・HTML コメントなどの外）で読み、repo の中の CLAUDE.md・AGENTS.md は数えない。`Post-PR Autonomy Exception` を含む行が無い・2 行以上ある・形が違う・読めないときは例外が無いものとする。読んだ行は `worklog.md` に `Post-PR Autonomy 例外:` として書く
- `references/post-merge-qa.md` 手順 1・2: QA の書き込みを runner に任せる条件を上の例外の行にし、`Merge Approval` を問わない条件を手順 2 の「自走のマージの条件」（§ 入口・`worklog.md` の宣言と例外の記録・QA 計画レビューと Deploy Paths・`.gdd-config.md` を変えないこと）1 か所にまとめた。followup などの他の経路からのマージは、この条件を満たさなければ今までどおり問う。宣言の 2 回目の読み直しは手順 2 の前（`マージ・デプロイ・QA まで` では手順 1 の前）にした。手順 2 では、マージの直前に `worklog.md` に `マージ前:`（起動する workflow と環境、QA の書き込みの全件）を、成功したら `マージ:` を書く。例外が無ければ今までどおり 1 問で問う
- `references/post-merge-qa.md` 手順 2: merge gate の `review-wait-not-elapsed` は followup のとおり待つ。それ以外の merge gate の拒否、その他の hook の deny、auto mode classifier の拒否では、同じ操作を別の方法で試さずに報告して止まる
- `references/post-merge-qa.md` § 限界: merge gate が自走の承認と人間の承認を区別しないことと、本番しか無い repo ではマージが本番デプロイになることを書いた
- `references/autonomy.md`: 判断役が human check を承認するとき、自走上限に上の 2 値を選ぶ案は「止まる案」にした（自走上限の 2 値はユーザーが選ぶ）
- `references/human-check-template.md`: 承認サマリの「OK で許可される最大到達点」に、`マージまで` 以上ならマージで起動する workflow と環境を並べることを足した
- `references/self-review-lanes.md` § merge gate 証跡、`references/state-field-tiers.md`、`skills/gdd-pr-review-followup/SKILL.md`、`references/human-check-template.md` § 自走上限の置換値を、上の形に合わせた

#### Affected Files

- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_evidence_parsing.py`

#### User Action Required

- 自走のマージと QA の書き込みを使うには、自分の規則（グローバルの CLAUDE.md・AGENTS.md など）に例外を書いたうえで、`~/.gdd/config.local.md` に `GDD Post-PR Autonomy Exception: on` の 1 行を足す。足さなければ今までどおりマージの前に 1 問で問い、QA は書き込みをしない

#### Validation / Eval Impact

- `tests/test_merge_gate_hook_evidence_parsing.py`（`post-merge-qa.md` の `Merge Approval` のひな形を merge gate の parser に通す）
- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
