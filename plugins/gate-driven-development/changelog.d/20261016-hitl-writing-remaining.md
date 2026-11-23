---
type: patch
---

#### Summary

- `references/human-check-template.md` § 判断の書き方 に、GDD のほかの文書（skill・reference・テンプレート）の行数や「短く」の指示は、判断の筋書きと選択肢ごとに残るものを削る理由にしない、と足した
- 次の長さの指示を外すか、判断に効く分を書く文に替えた: 承認サマリの「5 行以内」、Stage Continuity Brief の「3-5 行に圧縮」、既存実装の調査状況の「圧縮表示」、ベースライン検証の確認の「1 行で」、Top 3 Stop Conditions の「短い自然文」、簡易版テンプレートの選択肢・アーキテクチャ選択・PR 分割・ズレ確認の欄の「1〜3 行」、アーキテクチャ選択・PR 分割の選択肢の「1〜3 行に圧縮」（簡易版と `references/context-budget.md`）、`gdd-brainstorming` と `gdd-pre-workflow-brainstorming` の Summary Brief の「短い」「圧縮」「3〜5 点」、簡易版の WHY・要件・実装・検証の欄の「1〜2 行」「1〜3 行」、まず見るところの「1-2 行」「上位 2-3 件」、承認ポイント位置関係の「短い要約だけ」、推奨理由の「1-2 行」（`references/brainstorming-steps.md`）、`gdd-requirements-gating` の技術スタック・段階実装案の「短く」「短い表」と合理化表の「5 行で判断したい」、実装技術スタックの「短い表」、選択肢の概要の「1-2 行」（`references/brainstorming-steps.md`）、方式比較の「短い表」と調査の結論の「1〜2 行」（`references/requirements-template.md`）、採用方式と理由の「1〜2 行」（`references/brainstorming-steps.md`）、option の期待価値の「1 行で」（`gdd-brainstorming`）、`gdd-pre-workflow-brainstorming` の「簡潔に」「短い要約」「短く出す」。選択肢の案と option を書く行からも § 判断の書き方 を指した
- `lint-hitl-complexity` の警告文を、判断に効かない段落を外すか内部用語を説明する（判断の筋書きは削らない）処方に替えた。判定と閾値は変えていない
- full テンプレートの § 具体例を、30秒判断 → 判断ポイント → やること → 承認サマリ の並びに直し、判断ポイントを判断ごとの流れ（いまの状態・分かったこと・起こりうること・おすすめと残るもの）で書いた
- `gdd-requirements-gating` が予算超過のときに残す項目に、変更予定ファイル（WHERE）を足した（8 項目）
- `docs/TEAM_ROLLOUT.md` の HITL の読み方を、先に `30秒判断` と `判断ポイント` を読む案内に替えた

#### Affected Files

- `references/human-check-template.md`（§ Compact First、§ 承認サマリ、§ まず見るところ、必須ルール 13・15・16・20、§ HITL の役割、§ 判断の書き方、§ 承認ポイントの位置関係、§ 具体例）
- `references/human-check-template-compact.md`、`references/context-budget.md`、`references/brainstorming-steps.md`、`references/requirements-template.md`、`references/skill-responsibility-matrix.md`
- `skills/gdd-requirements-gating/SKILL.md`、`skills/gdd-brainstorming/SKILL.md`、`skills/gdd-pre-workflow-brainstorming/SKILL.md`
- `scripts/lint-hitl-complexity.py`（警告文だけ）
- `docs/TEAM_ROLLOUT.md`

#### User Action Required

なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
