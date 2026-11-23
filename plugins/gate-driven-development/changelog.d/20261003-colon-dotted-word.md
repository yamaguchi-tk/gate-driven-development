---
type: patch
---

#### Summary

- `scripts/lint-approved-direction.py` の colon の形（`Approved Direction:`）の読み方で、`戻し条件` などの自由文の中の `db.internal:5432`・`api.example.com` のような host:port・ホスト名を、単一ファイル固定の glob として ERROR にしなくなった。`自走範囲` の行は、今までどおりどの拡張子の単一ファイルも ERROR にする

#### Changed

- `scripts/lint-approved-direction.py`：colon の形の `自走範囲` 以外の行（`自走範囲:` の行と、それより深く字下げした続きの行を除く）では、`/` の無い語を、`.ts`・`.js`・`.py`・`.tf`・`.md` で終わる（行番号が付いていてもよい）ときだけ単一ファイルとみなす。この拡張子で終わる自由文の語（`Node.js`・`requirements.md`）と、`/` を含む語（URL を含む）は、今までどおり拾う。見出しの形の glob の欄の読み方は変えていない（未リリースの `20261003-glob-field-free-text` の Changed の「どの拡張子でもよく」は、見出しの形の glob の欄と colon の形の `自走範囲` の行に当てはまる）
- 同じ script：colon の形の節は、見出しでも終わる。`- Approved Direction: <自由文>` のような箇条で始まる節は、同じ字下げ以下の、`Route In Progress:` のような英語の欄名の箇条でも終わる（`- 方向性:`・`- 自走範囲:` のような同じ字下げの箇条は節の中として読む）。これまでは後ろの行（`- Last Handoff Summary: SKILL.md を更新した` など）まで読み、ERROR にしていた

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/tests/test_lint_approved_direction_extract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_lint_approved_direction_extract.py`：colon の形の `戻し条件` の行で `db.internal:5432`・`api.example.com:443`・`api.example.com`・`main.go`・`cookie.tsx` を glob にせず、5 つの拡張子の単一ファイルは ERROR にすること、`自走範囲` の行では `package.json`・`main.go`・`cookie.ts:42` を ERROR にすること、`/` を含む語の ERROR・WARN が残ること、`自走範囲` の続きの行と `含むディレクトリ / モジュール glob:` の行の単一ファイルを ERROR にすること、`自走範囲外:` の行は自走範囲の行にしないこと、節が見出しと英語の欄名の兄弟の箇条で終わり、平らな箇条と深い箇条は読むこと
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
