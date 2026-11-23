---
type: patch
---

#### Summary

root branch を作るコマンドを止める guard（`validate-worktree-command.py`）は、repo の toplevel にある GDD の marker を見て、active なら deny する。ところが git の出力を text モードの `.strip()` で読んでいたので、名前が空白・改行・タブ・CR で終わる repo（`<repo> `）や、パスの途中に CR を含む repo では toplevel が別のパス（`<repo>`）になり、active な marker を見落として allow していた。今後は、git の出力を bytes で読み、最後の改行だけを落とす。

#### Fixed

- `hooks/scripts/validate-worktree-command.py` の `git_output` は、出力を bytes で読み、最後の改行 1 つだけを落とす。toplevel・`--git-dir`・`--git-common-dir` の読み取りが、名前の空白・改行・CR を保つ
- 対象の repo の marker だけを読むので、末尾を落とした同名の repo が active で、対象の repo が active でないときは、deny ではなく allow になる

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_trailing_whitespace.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_root_branch_guard_trailing_whitespace.py` を足した。名前が空白・改行・タブ・CR で終わる active な repo（末尾を落とした同名の repo がある形・無い形）と、途中に CR を含むディレクトリの下の active な repo で、root branch を作るコマンドが deny になる。名前が空白で終わる repo が active でなければ allow になる
