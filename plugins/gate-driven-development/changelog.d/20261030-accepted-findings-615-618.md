---
type: patch
---

#### Summary

- quick (express) が要件レビューを通るようになった後も残っていた、古い記述と条件の食い違いを直した

#### Fixed

- `references/state-machine-overview.md` の Express Path に `gdd-requirements-gating` を入れた
- `references/onboarding.md` の express の所要時間を、README と同じ 15〜45 分の目安にした
- `agents/gdd-completion-reviewer.md` と `skills/gdd-pr-review/SKILL.md` で、`request.md` があるのは quick (standard)・standard だけ、という記述を「trivial には無い」にした
- `agents/gdd-planning-reviewer.md` の実装可能性の机上追跡の見出しと本文を、express の requirements にも当てる形にし、対象に `## Scope` の Files を足した
- human check の「ズレ確認」で、既存とぶつかる・原文だけでは決まらないを、express にも載せるようにした（`references/human-check-template.md`、`references/human-check-template-compact.md`）
- express の昇格条件（`references/task-sizing.md` § Express 昇格条件、`references/requirements-template-express.md` § Promotion Rules）のファイル数を、express の 4 条件と同じく実装コードで数えるようにした（テンプレートの `Files:` の欄と Human recheck trigger も同じ）。実装 2・テスト 1 の express は昇格しない
- express の要件レビューで security reviewer を起動する線を書いた。非 waivable 上書き条項に当たるときだけ起動する（`references/reviewer-selection.md`、`references/task-sizing.md`）
- express の human check の「一部変更」で範囲か Files が変わったときの再入を、返答の分類（`commands/gdd-dev.md` instruction 10 STEP 1）にも書き、Round の数え方・読む範囲・lint の `--entry` を書いた（`references/requirements-gating-steps.md` § Express）
- express の requirements の reviewer の入力の 1 枚に、机上追跡の対象の節を入れた（`references/subagent-dispatch.md`）
- `/gdd-dev` に `--auto-confirm` が渡されたら、無視して撤去を 1 行で伝えるようにした（`references/entry-intent.md`）
- README の所要時間の注記と、archive の例（`docs/references-archive/worked-examples.md`）の古い記述を直した

#### Affected Files

- `references/state-machine-overview.md`
- `references/onboarding.md`
- `references/human-check-template.md`
- `references/human-check-template-compact.md`
- `references/task-sizing.md`
- `references/requirements-template-express.md`
- `references/reviewer-selection.md`
- `references/requirements-gating-steps.md`
- `references/subagent-dispatch.md`
- `references/entry-intent.md`
- `agents/gdd-planning-reviewer.md`
- `agents/gdd-completion-reviewer.md`
- `skills/gdd-pr-review/SKILL.md`
- `commands/gdd-dev.md`
- `README.md`
- `docs/references-archive/worked-examples.md`
- `tests/checks/skill-body-budget.sh`（コメントだけ）
- `tests/test_express_planning_review.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_express_planning_review.py`（express で Design Review Status が approved でなければ build に進まない）
- `bash tests/validate-plugin.sh`
