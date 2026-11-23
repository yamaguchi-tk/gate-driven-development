---
type: patch
---

#### Summary

PR がある branch への push のレビュー判定（log-only）の取りこぼしを直した。

- `run_in_background` の reviewer の起動応答が読めないときは、通知の `<tool-use-id>` で終わりを見る。completed の通知が来るまでは `reviewer-incomplete`、それ以外の終わりの通知なら `reviewer-failed` にする（前は、通知が来る前でも `reviewed` になっていた）。
- tip の後の reviewer が動いている・失敗したときも、その前に成功した reviewer からの変更が宣言のパスだけなら `exempt-only` にする。
- GitHub の remote かどうかを、remote の `pushurl`（無ければ `url`）、git が渡した URL の順に見る。git は pushurl があると url に push しないので、pushurl が GitHub でなければ url が GitHub でも `not-github` にする。
- `.gdd-config.md` にコードフェンス（バッククォート・チルダ 3 つ）か HTML コメントの開始があれば、宣言を読まない。宣言は行頭から書く。
- ログの空の欄（`skipped` の行の branch・sha など）は `-` と書く。判定の外で起きた例外（ref 名が UTF-8 でないなど。hook の script の読み込みの失敗は除く）も `error` の 1 行を書く。gh の出力は ASCII の数字だけを件数として読み、UTF-8 でない出力も `gh-unknown` にする。UTF-8 として読めない gh・git の出力は置換文字に直して読む（`.gdd-config.md` は、読めないバイトを含む行が宣言に当たらなくなるだけで、ほかの行の宣言は読む）。
- 差し込めなかった session の `not-installed` の行に session（transcript の名前のハッシュ）を書き、compact では繰り返さない。
- hooks.json の説明と `docs/SECURITY.md`（git の pre-push hook の読み取り範囲、state dir の権限、SessionStart が `not-installed` を書く条件）を今の挙動に合わせた。

#### Affected Files

- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/hooks/scripts/run-push-review-env-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/git_pre_push_review.py`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/references/operation-levels.md`
- `plugins/gate-driven-development/tests/test_push_review_log_only.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`

#### User Action Required

- `.gdd-config.md` にコードフェンスか HTML コメントを書いている repo は、それを消さないと `GDD Push Review Exempt Paths:` の宣言が読まれない。宣言の前に空白を付けた行も読まない。

#### Validation / Eval Impact

- `tests/test_push_review_log_only.py` に、上の各挙動のテストを足した。`tests/test_hooks_kill_switch.py` は、テストを回す session の `CLAUDE_ENV_FILE` に書き足さないようにした。
- `bash tests/validate-plugin.sh`
