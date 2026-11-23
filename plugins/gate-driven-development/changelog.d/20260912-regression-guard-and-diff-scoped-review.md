---
type: minor
---

#### Summary

直前の修正が持ち込む退行を防ぎ、2 巡目以降のレビューを直前の修正箇所とその影響先に絞る。`implementation_fix_only` の復帰シーケンスに、実害クラス（`is_blocking` の finding category）または `High` の finding を対象とした RED 再現テスト必須化を追加し、`fix blast radius` の `unanalyzed` をその対象で禁止した。独立レビューと completion-check の再検証範囲を、同一 PR / 同一タスク内の 2 回目以降は前回証跡以降の差分と影響先に絞り、範囲外への新規指摘は advisory・前回証跡が解決不能なら全量に倒す（fail-closed）。Completion Baseline は「初回固定」から「差し戻し時点（修正前）で都度更新するローリングウィンドウ」に変更し、既存の回帰防止契約（2026-09-04 修正）を新方式へ置き換えた。

#### Added

- `references/rollback-patterns.md` § implementation_fix_only: RED 再現テスト必須化（実害クラス / High）と修正 commit 規律
- `references/independent-review.md` 契約 3: 同一 PR で 2 回目以降起動する場合の差分絞り込みと fail-closed。絞り込みは前回証跡の `high` / `blocking` が両方 0 のときだけ行い、そうでない場合は全量に倒す（diff 絞り込みによる fail-open を防ぐ）

#### Changed

- `references/reviewer-common.md` § Fix の影響範囲: 実害クラス / High の finding（文言・帳簿の指摘は除く）で `fix blast radius` の `unanalyzed` を禁止
- `skills/gdd-systematic-debugging/SKILL.md` Failure Routing: Standard / Express 双方の `implementation_fix_only` 復帰シーケンスに RED 再現テストの条件分岐を追加
- `references/gate-checklists.md` § Checklist E 手順 2/4/6、`references/state-machine.md` § Remediation Loop Safety、`references/state-field-tiers.md` Tier 3: Completion Baseline を「初回固定・以降上書きしない」から「差し戻し時点で都度更新・再検証時に diff が空なら全量再検証」に変更
- `skills/gdd-completion-check/SKILL.md`: Completion Baseline 更新契約の要約を新方式に同期

#### Breaking Contract Changes

- なし（`Completion Baseline` の更新契約・独立レビューの起動範囲はいずれも agent が prose を読んで実行する手順であり、`state.md` / `tasklist.md` の field 名・書式・pre-push gate の sha 一致検査は変えていない）

#### Affected Files

- `references/rollback-patterns.md`
- `references/reviewer-common.md`
- `references/independent-review.md`
- `references/gate-checklists.md`
- `references/state-machine.md`
- `references/state-field-tiers.md`
- `skills/gdd-systematic-debugging/SKILL.md`
- `skills/gdd-completion-check/SKILL.md`
- `tests/test_completion_check_loop_safety_contract.py`
- `tests/test_repro_test_and_blast_radius_contract.py`（新規）
- `tests/test_independent_review_differential_scope_contract.py`（新規）

#### User Action Required

- 進行中の `.steering/` がある場合、次回 `gdd-completion-check` 再入時から `Completion Baseline` が Round ごとに更新される（既存の `Completion Baseline` 行はそのまま使われ、migration 操作は不要）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` full suite
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` 全 BLOCK（`skill-body-budget` の references line budget を含む）
- 追加 contract test: `test_repro_test_and_blast_radius_contract.py` / `test_independent_review_differential_scope_contract.py`、更新: `test_completion_check_loop_safety_contract.py`
