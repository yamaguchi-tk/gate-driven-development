---
type: patch
---

#### Summary

- 利用者から見える変更なし。未リリースの main のモデルの通知（`main_model_gate`）を、リリースの前に直した
  - SessionStart は payload の model だけで判定し、`ANTHROPIC_MODEL` と settings の `model` の既定と、再開時の transcript を使わない。再開時の transcript の最後の信号は再開の前のモデルである。Desktop はセッションごとにモデルを選ぶので、既定は実際のモデルと食い違い、main が Opus のセッションにも「main は Sonnet」と出ていた
  - 相談の段の通知を、UserPromptSubmit から返事の後の Stop に移した。返事の前の transcript の最後の信号は前のターンのモデルで、画面での切り替えが記録に残らないと、前のモデルで知らせていた
  - `/gdd-dev` を止める判定は変わらない

#### Affected Files

- `hooks/scripts/lib/main_model_gate.py`
- `hooks/hooks.json`
- `hooks/scripts/run-main-model-gate-hook.sh`
- `README.md`
- `changelog.d/20261030-main-model-gate.md`（`amends:`。登録先と判定の記述を直した）
- `tests/test_main_model_gate.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
