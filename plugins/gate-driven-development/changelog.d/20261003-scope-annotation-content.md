---
type: patch
---

#### Summary

- `scripts/lint-approved-direction.py` の colon の形（`Approved Direction:`）で、`自走範囲（scripts/foo.py の修正）:` のように `自走範囲` の欄名の括弧の注記の中に書いた単一ファイルも、値と同じく ERROR にするようになった
- colon の形で、`戻し条件`・`自走範囲外:`・欄名つきの続きの行（`明示的に除外する範囲:` など）にだけ glob を書いた state.md でも、自走範囲を検査していないことを示す INFO が出るようになった

#### Changed

- `scripts/lint-approved-direction.py`：colon の形の `自走範囲` の行は、欄名を外した値に加えて、欄名の括弧の注記の中身もカンマ・空白で区切り、注記からは単一ファイルだけを拾う。注記のディレクトリ glob・全域 glob（`（src/legacy/** を除く）` などの除外の注記）と、glob の形でない語（`S-1` など）は拾わない（未リリースの `20261003-scope-label-annotation` の「欄名を外した値だけを語に分ける」を、「欄名を外した値と、欄名の括弧の注記の中の単一ファイルを語に分ける」に置き換える）
- `scripts/lint-approved-direction.py`：colon の形では、`戻し条件` の行・`自走範囲外:` の行・欄名の括弧の注記・欄名つきの続きの行の glob も今までどおり lint するが、`INFO: no Approved Direction patterns found` を消すのは、`自走範囲` の行の値と、欄名の無い続きの行・`含むディレクトリ / モジュール glob:` の行の glob だけにする

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/tests/test_lint_approved_direction_extract.py`

#### User Action Required

- colon の形の state.md で、`自走範囲` の欄名の括弧の注記に、カンマ・空白で区切って単一ファイルを書いていると、ERROR が出るようになる（`自走範囲（注: main.go は除く）:` のような除外の注記も同じ。steering の書き込み hook の advisory にも出る。書き込みは止めない）。`gdd-systematic-debugging` Step 3c では exit=1 になるので、注記から単一ファイルを外すか、`src/foo/**` のようなディレクトリ単位に直す
- colon の形で、自走範囲の値が自由文（`リポジトリ全体` など）のまま `戻し条件` などに glob を書いた state.md では、INFO が出るようになる（exit=0 のまま。glob を検査していないので合格に数えず、自走範囲を手で照らす）

#### Validation / Eval Impact

- `tests/test_lint_approved_direction_extract.py`：`自走範囲（scripts/foo.py の修正）:`・`自走範囲(main.go のみ) =` の注記の中の単一ファイルを ERROR にすること、glob の形でない注記（`（S-1・第1段階）`・`（v1.2 対応）`）は何も出さないこと、注記のディレクトリ glob・全域 glob は pattern に数えず INFO が出ること。colon の形で `戻し条件`・`自走範囲外:`・続きの行の `明示的に除外する範囲:` だけに書いた glob は lint するが INFO が出ること、`自走範囲` の値・glob の欄・欄名の無い続きの行の glob では INFO が出ないこと
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
