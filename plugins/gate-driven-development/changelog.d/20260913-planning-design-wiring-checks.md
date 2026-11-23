---
type: minor
---

#### Summary

内部 gate（planning-reviewer / implementation-gating / completion-check）を全て通過した後に、別系統レビュー（Codex・Copilot・レビュー bot・人間）が初めて発見していた「配線の欠陥」（新設要素の書く側・読む側・到達経路が繋がっていない）と「開いた入力の扱いの明記漏れ」を、PR 前に検出できるようにした。要件フェーズに「開いた入力の扱い」の1行明記を追加し、設計フェーズに新設要素の配線表を必須化してその整合を `gdd-planning-reviewer` が grep で突き合わせ、実装フェーズに新設要素ごとの到達テスト要求と未参照シンボル検出（report-only）を追加し、PR 前に別系統モデル（Codex）での配線レビューを1回加えた。

#### Added

- `agents/gdd-planning-reviewer.md`: 「開いた入力の扱いチェック」節（requirements phase 専用）と「配線表整合チェック」節（design phase 専用、Desk Trace が対象外にする新設シンボルを対象に配線表を実コードと突き合わせる）
- `skills/gdd-design-gating/SKILL.md` Step 5c: design.md の配線表（要素 / 書く側 / 読む側 / 入口からの到達経路 / 同じ入力を読む既存実装 / 検証テスト名）
- `scripts/lint-unused-new-symbols.py`（新規）: diff で追加された Python の module-level 関数・定数のうちテスト以外から参照0件のものを列挙する report-only スクリプト（block しない。exit code は常に 0）
- `skills/gdd-pr-review/SKILL.md` 3g: 別系統モデル（Codex）による配線レビュー（新設要素ごとの書く側・読む側・到達経路 / 同じ入力を読む別実装との受理集合の一致）。使えない host では skip 理由を記録する

#### Changed

- `references/requirements-template.md`: 受入条件セクションに「開いた入力の扱い」記入欄、lightweight design.md skeleton に配線表項目を追加
- `references/requirements-template-express.md`: Acceptance Criteria に「開いた入力の扱い」記入欄を追加
- `references/human-check-template.md`: 含めるべき情報の写像に「AC の開いた入力の扱い」行を追加
- `skills/gdd-implementation-gating/SKILL.md` Stage A: 新設要素の配線確認（design.md が無い Express はここで代替確認）と、新設要素ごとの到達テスト要求を追加
- `skills/gdd-completion-check/SKILL.md` 4c-3: `lint-unused-new-symbols.py` の実行を追加（report-only）

#### Breaking Contract Changes

なし（既存の schema・field 名・pre-push gate の sha 一致検査は変更していない。新設した確認項目は既存 gate の severity 体系・route hint に従う）

#### Affected Files

- `agents/gdd-planning-reviewer.md`
- `references/requirements-template.md`
- `references/requirements-template-express.md`
- `references/human-check-template.md`
- `skills/gdd-design-gating/SKILL.md`
- `skills/gdd-implementation-gating/SKILL.md`
- `skills/gdd-completion-check/SKILL.md`
- `skills/gdd-pr-review/SKILL.md`
- `scripts/lint-unused-new-symbols.py`（新規）
- `tests/checks/pr-review-anticipation-tokens.sh`
- `tests/test_planning_reviewer_open_input_handling_contract.py`（新規）
- `tests/test_open_input_handling_template_contract.py`（新規）
- `tests/test_planning_reviewer_wiring_table_contract.py`（新規）
- `tests/test_wiring_table_authoring_contract.py`（新規）
- `tests/test_lint_unused_new_symbols.py`（新規）
- `tests/test_completion_check_unused_symbol_scan_contract.py`（新規）
- `tests/test_pr_review_wiring_cross_model_review_contract.py`（新規）

#### User Action Required

なし。進行中の `.steering/` は次回 gate 再入時から新チェックの対象になる（既存 requirements.md / design.md の書式変更は不要。新設要素が無いタスクでは配線表・開いた入力の扱い行を省略できる）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` full suite（2680 passed, 4 skipped）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` 全 BLOCK OK
- 追加 contract test: 上記 Affected Files の `tests/test_*.py`（新規）7 本
- 独立レビュー（read-only / diff-only / 実装文脈なし、観点レーン (a)〜(h)）を1回実施し、`scripts/lint-unused-new-symbols.py` に対する high 1 件（`--repo-root` 不正時の未捕捉例外による exit 1）・medium 2 件（git diff 失敗の黙殺 fail-open、定義行除外ロジックの受理集合非対称による誤検知）を検出、RED 再現テストを追加してから修正し high: 0 / blocking: 0 を確認した。low 1 件（非 ASCII ファイルパスの git quotepath 未対応）はスクリプト docstring に限界として開示し、follow-up とした
- Codex レビュー: unavailable（codex CLI バイナリ未検出、`ENOENT`。`codex-companion.mjs setup --json` で確認）
- PR レビュー指摘への対応（RED 再現テストを追加してから修正）:
  - `references/requirements-template-express.md`: 「開いた入力の扱い」記入欄を AC 行とは別の共有 1 行にしていたため、AC が複数あるとどの AC の扱いか紐付かなかった。`gdd-planning-reviewer` の Open Input Handling Check の手順（「AC 内に」明記）に合わせ、各 `- AC-N:` 行の中に紐付けるよう修正
  - `scripts/lint-unused-new-symbols.py::count_references`: 正規表現の単語境界一致で実参照数を数えていたため、`API_URL = os.getenv("API_URL")` の文字列リテラル内の自己参照やコメント中の言及まで実参照として誤カウントしていた（本来は参照 0 件のシンボルを見逃す false negative）。`tokenize` の `NAME` トークンのみを対象にする方式へ変更し、`STRING` / `COMMENT` トークンの中身が誤って参照としてカウントされないようにした（定義行除外ロジック自体は変更なし）
