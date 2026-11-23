---
type: patch
---

#### Summary

- `scripts/lint-approved-direction.py` の colon の形（`Approved Direction:`）で、`自走範囲（S-1）: main.go` や `自走範囲 = main.go` のように欄名に注記や `=` を付けた行も `自走範囲` の行として読み、英字で始まる拡張子の単一ファイルを ERROR にするようになった

#### Changed

- `scripts/lint-approved-direction.py`：colon の形の `自走範囲` の行の判定で、欄名の後ろの括弧の注記（`（S-1）`・`(S-1)`。括弧の中身は問わないので、`自走範囲（補足）:` も `自走範囲` の行になる）と、区切りの `=` を許す。`自走範囲外:`・`自走範囲の補足:` は、今までどおり `自走範囲` の行にしない。`自走範囲` の行は、欄名を外した値だけを語に分ける（`自走範囲=**/auth/**` のように欄名と値の間に空白が無くても、`**/auth/**` の WARN が出る）（未リリースの `20261003-colon-dotted-word` の「`自走範囲:` の行」は、注記と `=` の付いた欄名を含む）

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/tests/test_lint_approved_direction_extract.py`

#### User Action Required

- colon の形の state.md で、`自走範囲（S-1）:`・`自走範囲 =` の行（と続きの行）に単一ファイルを書いていると、ERROR が出るようになる（steering の書き込み hook の advisory にも出る。書き込みは止めない）。`gdd-systematic-debugging` Step 3c では exit=1 になるので、`src/foo/**` のようなディレクトリ単位に直す

#### Validation / Eval Impact

- `tests/test_lint_approved_direction_extract.py`：`自走範囲（S-1）:`・`自走範囲 (S-1) :`・`自走範囲 =`・`自走範囲（S-1）=`・`- 自走範囲（S-1）：` の行の `main.go` を ERROR にすること、注記と `=` の欄名の続きの行も読むこと、欄名と値の間に空白が無くても値だけを読むこと、`自走範囲（補足）:` は `自走範囲` の行にし、`自走範囲（外）の補足:` はしないこと
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
