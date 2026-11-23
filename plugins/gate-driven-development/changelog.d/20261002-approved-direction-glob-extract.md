---
type: patch
---

#### Summary

- `scripts/lint-approved-direction.py` が、正本の書式（`## Approved Direction` の見出しの節）の state.md から glob を読むようになった。読むのは `含むディレクトリ / モジュール glob:` の欄（と続きの箇条）の path らしい語だけで、`自走範囲` の自由文・`承認後の到達点`・`事前スキャン対象 glob` などは読まない。これまでは colon の形（`Approved Direction:`）しか読めず、正本の書式の state.md では単一ファイル固定 glob も全域 glob × security-sensitive の交差も検査されていなかった

#### Changed

- `scripts/lint-approved-direction.py`：見出しの節の `含むディレクトリ / モジュール glob:` の欄の値と、欄より深く字下げした続きの箇条を、カンマ・空白で区切って検査する。`/`・`*` を含むか、よく使う拡張子で終わる語だけを glob とみなす（`repo 全体` のような値は glob にせず、`INFO: no Approved Direction patterns found` になる）。節は、同じ階層以上の次の見出しで終わる。値が `<` で始まるもの（テンプレートの記入例のまま）は読まない。見出しの節があるときは colon の形の読み方を走らせない。colon の形だけの state.md の読み方は変えていない（未リリースの `20261002-pre-answer-followup` の「lint は `## Approved Direction` の見出しの形を読めない」を置き換える）
- `skills/gdd-systematic-debugging/SKILL.md` Step 3c：`INFO: global glob` だけが出たときは自走可（security-sensitive path に触れる変更は `human_recheck_required` に昇格する）と分岐を足した。`INFO: no Approved Direction patterns found` は、見出しの形でも glob の欄が無いときに出るとした（合格に数えず、自走範囲を手で照らす扱いは変えていない）
- `references/rollback-patterns.md` § Approved Direction glob 粒度 guard：lint が読む欄と、`INFO: no Approved Direction patterns found` を合格に数えないことを書いた
- `references/requirements-template.md` の Approved Direction テンプレート：glob の欄の記入例から、単一ファイル固定の `src/http/cookie.ts` を外した（`src/http/**` にした）
- `commands/gdd-dev.md` #10：承認の後に `Approved Direction` を記録するとき、自走範囲を glob の欄（テンプレートの `含むディレクトリ / モジュール glob`）に書くと指した

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/requirements-template.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/tests/test_lint_approved_direction_extract.py`（新規）
- `plugins/gate-driven-development/tests/test_pre_answer_contract.py`

#### User Action Required

- 正本の書式の state.md で `含むディレクトリ / モジュール glob:` の欄に単一ファイル固定の値（例：`src/http/cookie.ts`）を書いていると、steering の書き込み hook の advisory に ERROR が出るようになる（書き込みは止めない）。`gdd-systematic-debugging` Step 3c では exit=1 になり、ディレクトリ単位の glob に直すまで design_detail_only に進まない

#### Validation / Eval Impact

- 新規 `tests/test_lint_approved_direction_extract.py`：見出しの形の glob の欄の単一ファイル固定で exit 1、全域 glob × security で WARN、ディレクトリ glob は無出力、自由文の欄・記入例・次の見出しの後は読まないこと、glob でない値は INFO に落ちること、続きの箇条を読むこと、見出しでない `#` の行と深い見出しでは節を閉じないこと、見出しの節があれば colon の読み方を走らせないこと、colon の形は従来どおり読むこと、lint が読む欄名とテンプレートの欄名の一致、steering の書き込み hook の入口から ERROR が systemMessage に届くこと
- `tests/test_pre_answer_contract.py`：hook 入口のテストで `GDD_STEERING_SIZE_DENY` を外し、ほかの hook テストと揃えた
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
