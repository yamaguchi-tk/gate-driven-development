---
type: patch
---

#### Summary

`/gdd-dev` の session state（`.claude/gdd-dev.local.md`）に、書いた checkout の git toplevel を `project_root:`（JSON 文字列）として残すようにした。`setup-gdd-loop.sh` は、別の session の `active: true` の state を見つけても、frontmatter の `project_root:` がちょうど 1 行の JSON 文字列で、その値が今の toplevel と別の実体（`st_dev`・`st_ino`）の実在するディレクトリを指す絶対パスであり、state が symlink を通らずに今の toplevel の下にあって hardlink でないときは、別の checkout から写された state としてロックにせず、旧 session と記録された `project_root` を stderr に出して上書きする。`project_root:` が無い・2 行以上ある・JSON 文字列でない・絶対パスでない・指す先が無いかディレクトリでないか今の checkout と同じ実体・frontmatter の区切りが無い・本文にだけある、git が無いか失敗する、toplevel が改行か CR を含む、state か `.claude/` が symlink、state が hardlink のときは、今までどおりロックにする。worktree を作るときに root の `.claude/` が写され、root に残った古い state が worktree の新しい session を止めていた（07-01〜10-14 の transcript で、ロック 67 件のうち 46 件）。

#### Affected Files

- `plugins/gate-driven-development/scripts/setup-gdd-loop.sh`（state に `project_root:` を書く。ロックの判定に、写された state の判定を足す）

#### User Action Required

- `project_root:` の無い今の state には効かない。止まっている session の state が `active: true` のまま残っているなら、持ち主の session が動いていないことを確かめて `active: false` にする

#### Validation / Eval Impact

- `tests/test_setup_gdd_loop_project_root.py`（git の linked worktree を作り、`setup-gdd-loop.sh` を入口にして、写された state を通すこと、止める側の各ケースでロックすることを確かめる）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
