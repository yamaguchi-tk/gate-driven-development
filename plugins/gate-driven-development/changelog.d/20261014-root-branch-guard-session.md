---
type: patch
---

#### Summary

root-branch guard（`validate-worktree-command.py`）が、root の `active: true` の session state で止めるのを、state の持ち主の session だけにした。今の session id は hook の payload の `session_id` から取り、hook のプロセスの環境変数 `CLAUDE_CODE_SESSION_ID` と一致するとき（Claude Code の hook）だけ使う。環境変数を継いだ別の runtime では一致しないので、今までどおり止める。そのうえで、state の frontmatter の `session_id` 行（ちょうど 1 行。`lib/state_io.py` の parse_state と同じく、`\n` だけで行を分け、行を strip してキーを読む）と違うときは、state による deny をしない。どちらの値も英数字・`-`・`_` の形のときだけ使う。payload の `session_id` が無い・文字列でない・形が外れる（リモート呼び出しの `served:<id>` を含む）・環境変数と一致しないとき、state の `session_id` が空・無い・2 行以上・形が外れる・frontmatter の外にだけある・frontmatter の区切りか閉じの区切りが無いとき、照合の途中の例外のときは、今までどおり止める。state があるのに通常のファイルでない（ディレクトリ・壊れた symlink・FIFO）・読めない（検索権の無い `.claude/` の下を含む）ときも止める（今までは通していた。検索権の無い `.claude/` は、`Path.is_file()` が権限エラーを False に読む Python の版でだけ通していた）。検索権の無い `.claude/` の下では、state が無いときも止める。state は parse_state と同じ `lib/regular_file.py` の `read_regular_text` で読む。GDD 名のブランチの deny と、worktree の作り方の deny は変えない。持ち主が終わった後に残った state が、GDD を使っていない別の session の `git checkout -b` などを止めていた（全 project の transcript で、state による deny 46 件のうち、止められた session が一度も GDD を始めていないものが 21 件）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`（state による deny に session の照合を足す。読めない state で止める）
- `plugins/gate-driven-development/tests/test_root_branch_guard_session_owner.py`

#### User Action Required

- session_id が空・形が外れる古い state が root に `active: true` のまま残っているときは止まる。持ち主が動いていないことをユーザーに確かめてから `active: false` にする。読めない state があるとき（中身によらない）と、検索権の無い `.claude/` の下（state が無くても）でも止まる。通常のファイルに戻すか、`.claude/` と state の権限を直す

#### Validation / Eval Impact

- `tests/test_root_branch_guard_session_owner.py`（hook を入口にして、別の session の state では止めないこと、持ち主と照合できない各ケースでは止めること、照合の途中の例外で deny になること、読めない state で止めることを確かめる）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
