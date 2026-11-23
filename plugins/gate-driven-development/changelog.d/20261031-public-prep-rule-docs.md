---
type: patch
---

#### Summary

- 公開に向けて、規則の文書（root の `CLAUDE.md`、`.claude/agents/`、plugin の references・skills・agents）と `hooks/hooks.json`・`tests/checks/review-log-present.sh`・`hooks/scripts/run-agent-dispatch-model-gate-hook.sh` から、repo の外の計画書の項目番号（`X-NN`・`W-NN` など）、手元の文書へのパス（`~/work/...`）、根拠として書いた実測の値（ドル額・件数・時間・比率など）、過去のタスクの AC 番号・レビューの巡や指摘の番号・セッション ID・過去のタスクの steering の slug を外し、その計測や項目が示した意味の文に書き直した。規則の閾値・上限・既定値と PR 番号は変えていない
- 見出しの名前が変わった節がある（`reviewer-selection.md` の `## Security Reviewer 非該当リスト`・`### waived 記録時の reason 書式`、`workspace-policy.md` の `## 相談レーンの分類`、`phase-progression.md` の `### Steering Archive / Scrub / 機密削除の規約`。どれも括弧の中の番号やラベルを外しただけ）
- 利用者に見える文字列では、`review-log-present.sh` の review-log が無いときの案内が「`review-log/README.md` の書式で作る」になった。`gdd-opus-advisor-max` の description と、相談役 3 本の「advisor ツールを呼ばない」の理由から、1 回あたりの費用・時間の値を外した。`hooks.json` の description から計画書の項目番号を外した。model を書かずに Agent を起動したときの警告の文から、計画書の項目番号と実測の比率を外した
- review-log の書式の正本を、repo の中の `review-log/README.md`（強制は `tests/checks/review-log-present.sh`）と書くようにした

#### Affected Files

- root の `CLAUDE.md`、`.claude/agents/light-lane-independent-reviewer.md`・`light-lane-independent-reviewer-xhigh.md`
- `agents/`: `gdd-completion-reviewer.md`、`gdd-fable-advisor.md`、`gdd-formal-gate-runner.md`、`gdd-implementation-reviewer.md`、`gdd-light-task-runner.md`、`gdd-opus-advisor.md`、`gdd-opus-advisor-max.md`、`gdd-planning-reviewer.md`、`gdd-security-reviewer.md`
- `references/` の 28 本（`state-schema.json` を含む）、`skills/` の 13 本の SKILL.md
- `hooks/hooks.json`（description）、`tests/checks/review-log-present.sh`（コメントと案内の文）、`hooks/scripts/run-agent-dispatch-model-gate-hook.sh`（コメントと警告の文）

#### User Action Required

なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run`（変えたファイルを参照するテスト）、`bash tests/validate-plugin.sh`
