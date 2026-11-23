---
type: patch
---

#### Summary

- `references/phase-progression.md` の cancelled 化した trigger hotfix の引き取り契約が、`Trigger Hotfix` の定義を `state-machine.md` § Hotfix Lane スキーマと書いていたのを、実際に定義がある `state-machine.md` § 許容値 に直した

#### Affected Files

- `references/phase-progression.md`

#### User Action Required

なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run`（変えたファイルを参照するテスト）、`bash tests/validate-plugin.sh`
