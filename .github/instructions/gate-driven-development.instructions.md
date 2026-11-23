---
applyTo: "plugins/gate-driven-development/**"
---

# gate-driven-development プラグインのレビュー観点

詳細な必須チェックは
[plugins/gate-driven-development/CONTRIBUTING.md](../../plugins/gate-driven-development/CONTRIBUTING.md)
を正本とします。レビュー時は特に以下を確認してください。

- 加算式改修の禁止: 新しい reference や長い section を足すだけでなく、
  重複する記述を親文書から削除しているか
- Skill count budget（現在の上限 28）を超えていないか。超える場合は
  統合・削除による削減計画が PR に書かれているか
- `references/` の総行数が `validate-plugin.sh` の line budget を超えていないか
- hook や script（`hooks/scripts/*.py`, `*.sh`）の変更に対応するテスト
  （`tests/test_*.py`）が更新されているか
