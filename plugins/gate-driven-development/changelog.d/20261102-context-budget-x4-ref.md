---
type: patch
---

#### Summary

- `references/context-budget.md` の root stub のサイズ制御の節が、root stub を定める節を `state-machine.md` § X-4 と書いていたのを、実際に節がある `phase-progression.md` § X-4 に直した

#### Affected Files

- `references/context-budget.md`

#### User Action Required

なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run`（変えたファイルを参照するテスト）、`bash tests/validate-plugin.sh`
