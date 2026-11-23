---
type: minor
---

#### Summary

PR がある branch への push が、レビューの済んだ tip かどうかをログに書くようにした（log-only。push は止めない）。

- SessionStart の hook が `$CLAUDE_ENV_FILE` に、git の設定による pre-push hook（`hook.gdd-push-review.*`）を `GIT_CONFIG_*` で書く。main・background・subagent の Bash の git push に効く。コマンドの文面と `core.hooksPath` は変えないので、repo の `.git/hooks` や husky の hook もそのまま動く。設定による hook に対応しない git では何も起きない。
- git の pre-push hook は、remote が github.com で、push 先の branch に open の PR があれば（`gh pr list`）、session の transcript を読んで判定する。
  - `reviewed`: push する tip の commit 時刻の次の秒以降に、reviewer の Agent が起動して成功で終わっている。reviewer に数えるのは、subagent_type（`:` より後ろ）が `light-lane-independent-reviewer`・`light-lane-independent-reviewer-xhigh`・`gdd-implementation-reviewer`・`gdd-completion-reviewer`・`gdd-security-reviewer`・`code-reviewer` のどれかのものだけ。background の起動は、`completed` の通知が来たものだけを数える。
  - `exempt-only`: 最後に成功した reviewer の起動の前の commit から tip までの変更が、その commit の `.gdd-config.md` の `GDD Push Review Exempt Paths:` に書いたパスだけ。
  - `would-deny`: どちらでもない。理由（`no-reviewer`・`reviewer-incomplete`・`reviewer-failed`・`changed-after-review`・`other-agent-only`）を付ける。
  - そのほか `not-github`・`no-pr`・`gh-unknown`・`no-transcript`・`error`。1 回の push の ref が 10 本を超えた分は `skipped` の 1 行にまとめる。
- ログは `~/.claude/.gdd-hook-state/push-review.log`（0600）に、ref ごとに 1 行で書く。欄は時刻・判定・理由・session・repo・branch・sha・時間（ms）の順で、session・repo・branch はハッシュで書く。`reviewed` には成功した reviewer（`by:`）、`other-agent-only` には起動した Agent（`agents:`、3 件まで）を足す。transcript のパスに安全でない文字があって差し込めなかった session は、`not-installed` の 1 行を書く。

#### Affected Files

- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/hooks/scripts/run-push-review-env-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/git-pre-push-review-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/git_pre_push_review.py`
- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/tests/test_push_review_log_only.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`

#### User Action Required

- 有効にするには、Claude Code の session を開き直す（SessionStart で書くため）。git は設定による hook（`hook.<name>.event`）に対応した版が要る。
- レビュー不要のパスを使う repo は、作業ツリー直下の `.gdd-config.md` に `GDD Push Review Exempt Paths: <パス> …` の行を 1 つ書く。値は git の pathspec で、末尾が `/` のものはディレクトリの中身すべてを指す。

#### Validation / Eval Impact

- `tests/test_push_review_log_only.py` を足した（SessionStart の hook が書いた env file を bash・zsh で source した shell で本物の `git push` を打ち、判定ごとのログと、push が止まらないこと、元の pre-push hook が同じ stdin で動くこと、既存の `GIT_CONFIG_*` を消さないこと、script が消えても push を止めないことを確かめる）
- `bash tests/validate-plugin.sh`
