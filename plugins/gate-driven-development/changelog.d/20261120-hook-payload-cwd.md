---
type: patch
---

#### Summary

- steering と marker を読む hook（UserPromptSubmit・SessionStart・PreCompact・Stop、Plan mode・EnterWorktree・skill・Agent の gate など 11 本）は、入口でプロセスの cwd を payload の `cwd`（セッションの cwd）へ移してから判定する。desktop の worktree のセッションでは hook のプロセスの cwd が root checkout になり、root checkout に残った古い steering を読んで、worktree のセッションに毎ターン `[gdd:blocked]` を注入していた。入口が失敗しても（cwd が消えているなど）hook は落ちず、移さないだけになる
- block gate 5 本（Plan mode・EnterWorktree・skill・skill の展開・background dispatch）と、警告だけを出す agent-dispatch の gate は、移した先の repo と移す前の repo のすべてで「このセッションの active な marker が無い」と言い切れたときだけ通す。「無い」と読むのは、marker が無く親のディレクトリを検索できたとき、marker の `active` が false のとき、`active` が true でも session_id が空か別のセッションのもの（英数字・`.`・`_`・`:`・`-` だけで、今の id と違う）のときだけで、ほかは判定できないものとして止める側にする（cwd や移す前の cwd を取れない、toplevel が改行で終わる、`.claude` を検索できない、marker が宙に浮いた symlink・読めない、`active` の値が無い・読めない、session_id が許す文字の外、`active`・session_id が frontmatter に 2 行以上ある、marker があるのに python3 が無い）。skill・skill の展開・background dispatch の gate は、marker で通せなかった後に payload を読む python3 が 0 以外で終わった（無い・落ちた）ときも止める。marker の中身は、Stop hook と同じ Python のコード（frontmatter の行の分け方と、key と値の前後の空白の除き方）で読む。Stop の bash 側は、今までの判定を 2 つの repo の両方に当て、どちらかで止める側なら止める。移す前の repo だけを見ていた頃より止める範囲は狭くならない
- UserPromptSubmit の毎ターンの注入（`[gdd:blocked]`・複数 steering の警告を含む）と、Write・Edit の前の `[gdd:build]` の注入は、GDD の印（cwd の repo の `.claude/gdd-dev.local.md` が active で、このセッションのもの）があるときだけにした。印の無いセッションには、steering が残っていても注入しない。`CLAUDE_CODE_SESSION_ID` の無いランタイム（Codex など）では、Stop hook と同じく marker の session_id を payload の session_id と比べ、marker に session_id が無ければ active かだけを見る（そのため、別のセッションが残した session_id の無い active な marker は印として通る）。marker が active でなければ注入しないので、setup を省いて marker を作らずに進める GDD のセッションは、毎ターンの注入を受けない（`/gdd-dev` を打ち直せば marker ができる）

#### Affected Files

- `hooks/scripts/lib/payload-cwd.sh`（新規）・`hooks/scripts/lib/exact-path.sh`・`hooks/scripts/lib/detect-steering.sh`・`hooks/scripts/lib/gdd-active-check.sh`・`hooks/scripts/run-*.sh` の 11 本

#### User Action Required

- 長く動いているセッションは開き直す（hook の script が変わる）

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
