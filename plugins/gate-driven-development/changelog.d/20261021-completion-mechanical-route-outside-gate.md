---
type: minor
---

#### Summary

- main は Completion-Check Template を dispatch する前に `scripts/check-completion-mechanical.py` を回し、機械で判定できる不備を gate runner を起動せずに差し戻す。出力の最初の `ok` 以外の行で、`reviewed-by` は `gdd-implementation-gating`（`Implementation Gate Bounce Log` に足す。閾値に達するなら gate を dispatch）、`remaining-tasks` は `gdd-test-driven-development`、`codebase-health` の High は `gdd-systematic-debugging`（`Completion Rounds` を +1）、`ac-ids` は `gdd-completion-check` のまま止める。`route-in-progress` は gate に任せる
- スクリプトは行を gate の Step の順（2a → 3 → 4 → 4c-3 → 5）に出し、検査の道具が判定できないとき（部品の例外、base を解決できない、子の出力を読めない、`lint-ac.py` の exit 2）は新しい状態 `error` を出す。`error` は記録の不備ではないので、main も gate も差し戻さずに外部前提不足で止める
- completion-check の Step 4c-3 の High の戻し先を `gdd-systematic-debugging` 1 つにした

#### Changed

- `scripts/check-completion-mechanical.py`（行の順、状態 `error`）
- `references/subagent-dispatch.md`（§ Completion-Check の前の機械検査に、行ごとに main が行うことを書いた。Template の事前確認は、ok でないとき行の詳細をそのまま報告する）
- `skills/gdd-completion-check/SKILL.md`（Step 0 の `error` の扱い、Step 4c-3 の戻し先）
- `references/gate-checklists.md`（§ Checklist E の分類外に `error` を足し、main の差し戻しでも `Completion Rounds` を +1 する）
- `references/state-machine.md`（遷移表に main の差し戻しの行を足した）

#### Affected Files

- `scripts/check-completion-mechanical.py`
- `references/subagent-dispatch.md`
- `skills/gdd-completion-check/SKILL.md`
- `references/gate-checklists.md`
- `references/state-machine.md`
- `tests/test_check_completion_mechanical.py`

#### User Action Required

- なし。動いているセッションの main は、root checkout を pull した後に読む references から新しい手順に従う

#### Validation / Eval Impact

- `tests/test_check_completion_mechanical.py`（行の順、`error` の 3 ケース）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
