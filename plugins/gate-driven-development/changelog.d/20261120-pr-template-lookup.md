---
type: patch
---

#### Summary

- `gdd-pr-review` の PR 作成の手順で、PR テンプレートを `git ls-files | grep -i -E '(^|/)pull_request_template'` で探す。大文字・小文字と、`.github/`・`docs/`・root・`PULL_REQUEST_TEMPLATE/` の置き場を拾い、グロブでは探さない（zsh では一致しないグロブがコマンドごと失敗し、在るテンプレートを見落とした）

#### Affected Files

- `skills/gdd-pr-review/references/pr-review.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
