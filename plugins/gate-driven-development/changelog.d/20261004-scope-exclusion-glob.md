---
type: patch
---

#### Summary

- `scripts/lint-approved-direction.py` の colon の形（`Approved Direction:`）で、`自走範囲: リポジトリ全体、src/legacy/** は除く` のように、自走範囲の行に除外の言い方と並べて書いた glob では、自走範囲を検査していないことを示す INFO が出るようになった。英語の除外（`** except src/legacy/**`）と `!` の否定も同じ。見出しの形でも、`含むディレクトリ / モジュール glob:` の欄に `!src/legacy/**`・`-src/legacy/**` のように `!`・`-` で始まる語があれば、欄を読まずに WARN（と、`--quiet` でなければ INFO）を出す
- colon の形でも、見出しの形と同じく `・`・`;`・`|`・`／` で語に分ける。`src/b/**・src/foo.ts` の単一ファイルも ERROR になる

#### Changed

- `scripts/lint-approved-direction.py`：colon の形で `INFO: no Approved Direction patterns found` を消すのは、`自走範囲` の行の値・欄名の無い続きの行・`含むディレクトリ / モジュール glob:` の行のうち、語がすべて glob の形（`/` を含む glob か、拡張子つきの単一ファイル）で、英数字と `_ . * ? [ ] { } / -`（`-` は先頭以外）と末尾の `:行番号` だけでできている行の glob だけにする。自由文・英語の語（`except`）・全角の文字・`!`・括弧などの記号・先頭の `-` を含む語がある行と、欄名つきの続きの行（`明示的に除外する範囲:`・`対象:` など。glob の欄を除く）の下の箇条の glob は、今までどおり lint するが数えない（未リリースの `20261003-scope-annotation-content` の「`自走範囲` の行の値と、欄名の無い続きの行・`含むディレクトリ / モジュール glob:` の行の glob」を、「そのうち語がすべて上の形で、欄名つきの続きの行の下でない行の glob」に置き換える）
- `scripts/lint-approved-direction.py`：見出しの形の `含むディレクトリ / モジュール glob:` の欄は、glob の形でない語に加えて、`!`・`-` で始まる語（`!src/legacy/**` など）が 1 つでもあれば読まない。`app/(auth)/**`・`packages/@org/**`・`docs/設計/**` のような記号・全角の文字を含むパスは今までどおり読む（未リリースの `20261003-glob-field-free-text` の「glob の形でない語が 1 つでもあれば欄を読まず」を、「glob の形でない語か、`!`・`-` で始まる語が 1 つでもあれば欄を読まず」に置き換える）
- `scripts/lint-approved-direction.py`：colon の形の語の区切りを、見出しの形と同じ `,`・`、`・`，`・`;`・`|`・`／`・`・`・空白にする
- `references/rollback-patterns.md` § Approved Direction glob 粒度 guard：colon の形で INFO が出る条件を書き直した

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/tests/test_lint_approved_direction_extract.py`

#### User Action Required

- colon の形の state.md で次のように書いていると、INFO が出るようになる（exit code は、下の区切りの単一ファイルを除いて変わらない）。`gdd-systematic-debugging` Step 3c では自走範囲を手で照らすことになるので、glob を検査させたいときは、glob だけの行（`自走範囲: src/a/**`）にして、説明は別の行に書く
  - 自走範囲の行に glob と自由文・括弧の補足を並べている（`自走範囲: src/a/** の修正`、`自走範囲: src/** (S-1)`）
  - `src/foo` のような glob の形でない語や `/` だけの語を並べている（`自走範囲: src/a/** / src/b/**`）
  - 欄名つきの続きの行（`- 対象:`、表記のゆれた `- 含むディレクトリ・モジュール glob:` など）の下の箇条に glob を書いている。glob は `含むディレクトリ / モジュール glob:` の欄か、欄名の無い行に書く
- 見出しの形の `含むディレクトリ / モジュール glob:` の欄に `!src/legacy/**`・`-src/legacy/**` の否定を書いていると、欄を読まずに WARN（と、`--quiet` でなければ INFO）が出て、同じ欄の単一ファイルの ERROR も出ない。除外は `明示的に除外する範囲:` の欄に書く
- colon の形で、glob と単一ファイルを `・`・`;`・`|`・`／` でつないでいる（`src/b/**・src/foo.ts`）と、単一ファイルが ERROR になり、Step 3c では exit=1 になる。単一ファイルを外すか、ディレクトリ単位に直す

#### Validation / Eval Impact

- `tests/test_lint_approved_direction_extract.py`：自走範囲の値・欄名の無い続きの行に除外の言い方と並べた glob、先頭の `!`、欄名つきの続きの行の下の箇条では INFO が出ること、glob だけの行（注記つきの欄名・glob の欄の続きの箇条・`*` の箇条を含む）では INFO が出ないこと、除外の言い方と並べた単一ファイルは ERROR になること。英語の除外・先頭の `-`・2 つ目の節・`・` などの区切り・見出しの形の `!`・`-` の否定の扱い、見出しの形で `app/(auth)/**`・`packages/@org/ui/**`・`docs/設計/**` などのパスを読んで同じ欄の単一ファイルを ERROR にすること、colon の形で `-src/legacy/**`・`(src/legacy/**)` を数えないこと
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
