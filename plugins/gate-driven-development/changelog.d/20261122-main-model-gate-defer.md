---
type: patch
---

#### Summary

- 利用者から見える変更なし。未リリースの main のモデルの gate（`main_model_gate`）を、リリースの前に直した
  - 止める判定を、直接打った `/gdd-dev`（UserPromptExpansion）から、gdd-dev・gdd-resume の Skill の呼び出し、`setup-gdd-loop.sh` の中、手動の手順で run を始める `.claude/gdd-dev.local.md` への Write・Edit・MultiEdit に移し、毎回判定する。state ファイルのパスは、`..`・相対パス・大文字小文字・symlink（ディレクトリの symlink と、名前が同じ file symlink）を解決して比べる。`setup-gdd-loop.sh` の外し方は settings のファイルの env だけを読む。返事の前の transcript の最後の信号は前のターンのモデルで、画面での切り替えが記録に残らないと、Opus に切り替えた直後に止め、Sonnet に切り替えた直後に通していた
  - モデルは、Skill を呼んだ・script を実行した返事の行から取る。読めないときは今までの最後の信号で判定し、そのときだけ切り替えた直後の案内を出す

#### Affected Files

- `hooks/scripts/lib/main_model_gate.py`
- `hooks/scripts/run-main-model-gate-hook.sh`
- `hooks/hooks.json`
- `scripts/setup-gdd-loop.sh`
- `commands/gdd-dev.md`
- `README.md`
- `docs/SECURITY.md`
- `changelog.d/20261030-main-model-gate.md`（`amends:`。登録先と判定の場所、判定の仕方、切り替えの直後の案内を直した）
- `tests/test_main_model_gate.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
