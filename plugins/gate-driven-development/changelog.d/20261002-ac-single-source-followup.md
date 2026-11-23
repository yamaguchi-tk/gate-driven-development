---
type: patch
---

#### Summary

AC の欄名の列挙の書き直しを出す advisory lint（`[duplication lint]`）と、承認ポイントの件数の規定を直した。`## Scope` の節を（Task Size を問わず）検査するようにし、検査から外す節（`スコープ`・`Express Minimal Trace`・`Planned Follow-up Stage Lane`）は、その下の小見出しも含めて外す。承認ポイントの件数は、express も「方向性承認と、ほかに 2 件以内」にそろえた。

#### Fixed

- `scripts/lint-requirements-duplication.py`
  - `## Scope` の節を検査から外していたのをやめた（express の Scope は `AC-1 参照` と書かせる欄で、照合元ではない。照合元は `スコープ` と `Express Minimal Trace`）
  - 外す節は、見出しから同じか上の階層の次の見出しまでとした（`###` の小見出しも外す）。コードフェンスの中の `#` 行は見出しとして扱わない。フェンスは開きと同じ文字で長さが同じか長く、info string の無い行で閉じ、文末まで閉じないフェンスは、開きの行から後の `#` 行を見出しとして数える（それより前の閉じたフェンスはそのまま）
  - WARN の文に「（照合元と Lane の値は除く）」を足した
- `hooks/scripts/validate-steering-write.py`: `CLAUDE_PLUGIN_ROOT` が空のとき、cwd ではなく hook の位置から plugin root を求める
- `references/human-check-template.md` の 承認サマリ・まず見るところ の判断の件数を「1-3 件」から「自走上限（方向性）と、ほかに 2 件以内」にした
- express の承認ポイントの下限をなくした（方向性承認と、ほかに 2 件以内。無ければ方向性だけ）。`references/requirements-template-express.md`・`references/requirements-template.md`・`references/human-check-template.md`・`references/task-sizing.md` をそろえた

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-requirements-duplication.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/requirements-template-express.md`
- `plugins/gate-driven-development/references/requirements-template.md`
- `plugins/gate-driven-development/references/task-sizing.md`
- `plugins/gate-driven-development/tests/test_lint_requirements_duplication.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_lint_requirements_duplication.py` に、express の `## Scope` の書き直しで WARN、外した節の小見出し・フェンスの中の `#` 行は見ず同じ階層の次の見出しで検査に戻る、WARN の文に例外が書かれる、`CLAUDE_PLUGIN_ROOT` が空で cwd が plugin の外でも advisory が出る、上の階層の見出しで検査に戻る、`~~~` のフェンス、info string 付きの行でフェンスを閉じない、閉じないフェンス、閉じないフェンスより前の閉じたフェンスの中の行（requirements.md・design.md）、design.md のフェンスの中の行、のテストを足した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
