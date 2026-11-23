---
type: patch
---

#### Summary

- `scripts/lint-approved-direction.py` は、見出しの形の `含むディレクトリ / モジュール glob:` の欄に glob の形でない語が 1 つでもあると、欄を読まずに `WARN: glob field not read`（と、`--quiet` でなければ `INFO: no Approved Direction patterns found`）を出すようになった。これまでは `S-1/S-2` や `/` のような語も path とみなし、何も出さずに合格にしていた

#### Changed

- `scripts/lint-approved-direction.py`：glob として検査する語を、`/` を含み glob meta（`*`・`?`・`[`・`]`・`{`）を含む語と、英字で始まる拡張子つきの単一ファイル（どの拡張子でもよく、`:42` のような行番号が付いていてもよい。ERROR になる）に置き換えた。`/` だけを含む語（`S-1/S-2`、`**` の無い `src/notify`）、meta だけの自由文（`[TBD]`・`**未定**`）、拡張子に見える語（`etc.`・`v1.2`）は glob とみなさない
  - 見出しの形の glob の欄（続きの箇条を含む）では、glob の形でない語が 1 つでもあれば欄を読まず、その語を並べた `WARN: glob field not read` を出す。`--quiet` で呼ぶ steering の書き込み hook の advisory にも出る。glob の形の語が混ざっていても、ERROR・WARN は出さない
  - 欄の語の区切りに `;`・`|`・`／`・`・` を足した
  - colon の形（`Approved Direction:`）でも、glob の形でない語を 1 つずつ捨てる
  - 未リリースの `20261002-approved-direction-glob-extract` の Summary の「path らしい語だけ」と、Changed の「`/`・`*` を含むか、よく使う拡張子で終わる語だけを glob とみなす」を置き換える。同じ断片の User Action Required の ERROR は、glob の欄に glob の形の語だけを書いたときに出る
- `skills/gdd-systematic-debugging/SKILL.md` Step 3c と `references/rollback-patterns.md` § Approved Direction glob 粒度 guard：欄を読まない条件と、`WARN: glob field not read` を合格に数えないことを書いた

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/tests/test_lint_approved_direction_extract.py`

#### User Action Required

- glob の欄には glob だけを書く。`**` 無しのディレクトリ（`src/notify`）や自由文を 1 語でも混ぜると、lint は欄を読まず（単一ファイル固定の ERROR も出さず）、`WARN: glob field not read` を出す。Step 3c では自走範囲を手で照らすことになる。ディレクトリは `src/notify/**` のように書く

#### Validation / Eval Impact

- `tests/test_lint_approved_direction_extract.py`：`S-1/S-2`・`/`・`S-1/S-2/`・`src/notify`・`[TBD]`・`未定?`・`{TBD}`・`**未定**`・`etc.`・`v1.2`・glob と自由文の混在で欄を読まずに WARN と INFO を出すこと、`--quiet` でも WARN が出ること、続きの箇条の `S-1/S-2` で欄を読まないこと、`・`・`;`・`|`・`／` で語を区切ること、どの拡張子の単一ファイルも pattern にすること、colon の形で `S-1/S-2`・`/` を捨てること
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
