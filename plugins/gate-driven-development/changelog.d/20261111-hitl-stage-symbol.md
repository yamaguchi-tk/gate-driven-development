---
type: patch
---

#### Summary

- human check で、段階が 1 つだけの回は段階実装の節（`段階実装サマリー`・`Stage Continuity Brief`・`段階実装案`）を書かないようにした。省いたことは `<gdd-hitl-fields>` の 5 つ目の属性 `stage="none"` で示す（複数段階・後続 PR 前の再承認などで節を書いたら `filled`）。`lint-hitl-required-fields.py` は `stage` の欠落・不正値を警告する。`lint-hitl-display-integrity.py`・`lint-human-check-language.py`・`lint-hitl-decision-quality.py` は、stop marker の直前のタグ（marker が複数なら全部）で `stage="none"` を宣言したときだけ段階実装の語を要求しない。タグが無い・`filled`・不正値のときは今までどおり要求する。ズレ確認の見出しと「なし」の 3 行は変えていない
- 一次表示で記号のまま残してよいものを決めた。人が返事で使う呼び名（`AC-n`・Stage ID は初出で意味を書く、案の名前）、機械が読む行（宣言タグと stop marker）、確定文面の block の中だけで、それ以外の内部の記号・番号は中身の言葉にする
- ズレ確認と整理した要件の原文の行に `request-crosscheck.md` の `#` を出さず、件数と言葉で書くようにした。`#` ごとの行き先の固定行は `worklog.md` に書く

#### Affected Files

- `references/human-check-template-compact.md`・`references/human-check-template.md`・`references/brainstorming-steps.md`・`references/task-breakdown-steps.md`・`skills/gdd-requirements-gating/SKILL.md`・`commands/gdd-resume.md`・`docs/DISTRIBUTION_READINESS.md`
- `scripts/lint-hitl-required-fields.py`・`scripts/lint-hitl-display-integrity.py`・`scripts/lint-human-check-language.py`・`scripts/lint-hitl-decision-quality.py`・`scripts/lib/hitl_fields.py`（新規。宣言タグを位置契約で読む部品）・`hooks/scripts/lib/hitl_lint_gate.py`（説明の文だけ）

#### User Action Required

- なし（stop hook の配線は変えておらず、どの lint も警告だけ）

#### Validation / Eval Impact

- `tests/test_lint_hitl_stage_conditional.py`（新規。3 本の lint の CLI と `hitl_lint_gate.run_hitl_lints` から通す）、`stage="none"` でも段階以外の必須語は求めることの検査、`tests/test_lint_hitl_required_fields.py` の `stage` の検査、`tests/checks/hitl-required-fields-lint.sh`・`tests/test_hitl_lint_gate_warn_wiring.py` のタグへの `stage` の追加
- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
