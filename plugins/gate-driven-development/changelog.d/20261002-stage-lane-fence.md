---
type: patch
---

#### Summary

Stop hook は、requirements.md の `## Planned Follow-up Stage Lane` に未完の Stage があるのに出力に `### 次の計画` が無い done を止める。post-merge continuation も、同じ判定で停止を止めるか、continuation の marker を消して通すかを決める。この判定は `- [ ]` の行だけを未完として探していたので、テンプレート（`references/requirements-template.md`）どおりに表で書いた Lane、`*` や番号付きの項目、コードフェンスの中の `## ` 行で切れた Lane、2 つ目の Lane などを読まず、止めるべき停止を通していた。

今後は既定を反転する。Lane の中（コードフェンスの中を除く）が、`- [x]` の項目・表の先頭のヘッダーの行と `|` を含む区切りの行・空行だけなら完了とし、それ以外の行（見出しを含む）が 1 行でもあれば未完とする。表のデータ行も未完に数える（表には完了を示す列が無いので、行が残る限り `### 次の計画` を求める）。

#### Fixed

- `hooks/scripts/lib/next_plan_check.py` の `has_incomplete_follow_up_stages`
  - Lane の中の行を、完了の形（`- [x]` の項目・表の先頭のヘッダーの行〔上が空行か節の先頭で、下が区切りの行〕・`|` を含む区切りの行・空行）だけなら完了、ほかの行（`- [ ]`・`*`・`+`・番号付きの項目、`###` 以下の見出し、表のデータ行、`---` などのパイプの無い行、地の文、入れ子の補足など）があれば未完とする
  - `lib/tasklist_parse.strip_fenced_blocks` を通した本文から Lane を読む。フェンスの中の行（記入例）は数えない。閉じないフェンスは、開きの行から後を読む
  - Lane の見出しは前方一致で読み（行末の文字を問わない）、Lane が 2 つ以上あれば全部を見る。Lane の終わりは、次の `#` か `##` の見出し（後ろに半角空白・タブ・行末が続く行）。`###` の小見出しや、`#` の後に全角空白が続く行では終えない
- `hooks/scripts/gdd_stop_hook.py` と `hooks/scripts/lib/post_merge_continuation.py` は、requirements.md に UTF-8 として読めないバイトがあっても、置き換えて読む（今までは読まずに停止を通し、post-merge では marker を消していた）
  - Lane の見出しの語があり、本文に LF・CR 以外の行区切り文字（U+2028・U+0085・`\x0c` など）があれば、読み方が決まらないので未完とする
- `scripts/lint-requirements-duplication.py` のフェンスの開きを `lib/tasklist_parse.py` と同じ規則にした（字下げは半角空白とタブだけ。backtick のフェンスの info string に backtick を含む行は開きにしない）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/next_plan_check.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/lib/post_merge_continuation.py`
- `plugins/gate-driven-development/scripts/lint-requirements-duplication.py`
- `plugins/gate-driven-development/tests/test_next_plan_check_fence.py`
- `plugins/gate-driven-development/tests/test_stop_hook_e2e_block_content.py`
- `plugins/gate-driven-development/tests/test_lint_requirements_duplication.py`

#### User Action Required

- 表で書いた Lane や、`- [x]` 以外の行（見出し・補足・地の文など）を残した Lane を持つタスクでは、done と post-merge の停止のたびに、出力に `### 次の計画` の見出しが要る（終わった Stage の行と補足を消すか、`### 次の計画` を書く）

#### Validation / Eval Impact

- `tests/test_next_plan_check_fence.py` を足した。フェンス（`## ` 行・Lane の記入例・フェンスの中だけの項目・閉じないフェンス）、Lane の終わり（`# ` の見出し・`###` の小見出し・`#` の後の全角空白や NBSP・`#` だけの行）、見出しの行末の全角空白、2 つ目の Lane、LF 以外の行区切り文字 8 種、表（データ行・ヘッダーだけ・先頭のセルが空・両端の `|` が無い・ヘッダーの無い 1 行・フェンスの中・Lane の外・崩れた行）、`*`・`+`・番号付きの項目（未完・済み）、`###` の見出し、表の途中の区切りの形の行、パイプの無い区切りの形の行、地の文と入れ子の補足、完了の形だけの Lane、Lane の無い本文の行区切り文字を見る
- `tests/test_stop_hook_e2e_block_content.py` に、Lane の中のフェンスに `## ` 行があるとき・表で書いた Lane のとき・requirements.md に UTF-8 として読めないバイトがあるときに、done と post-merge の停止を止めるテストを足した
- `tests/test_lint_requirements_duplication.py` に、フェンスの開きの規則のテストを足した
- 実データの requirements.md で、修正の前後の戻り値を比べた（PR 本文に結果）
