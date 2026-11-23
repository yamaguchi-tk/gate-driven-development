---
type: patch
---

#### Summary

Stop hook が、マージ後の確認を始める合図（`マージした`・`mergeした`・`merged`）を、turn の途中に届いた人間の発話からも読むようにした。この発話は transcript に `type: "user"` の行として残らず、`attachment`（type: `queued_command`、`attachment.origin.kind` が `human`）にだけ残ることがある。これまでは読まなかったので、作業中に「マージした」と送っても、マージ後の確認を済ませずに止まれた。合図は、直近の `type: "user"` の人間の発話と、その後に queued で届いた人間の発話のどれかが、この PR の合図（別の PR を指していないもの）なら合図とみなす。後から届いた別の発話（別の PR のマージの報告を含む）で、前の合図は消えない。合図は `origin.kind` が `human` の人間の発話だけから取る。skill の前置きや `<ci-monitor-event>` などの、host が注入する `type: "user"` の行の語は合図にせず、その行で合図を消さない（これまでは、`type: "user"` の合図もこれらの行で消えていた）。`origin` を書かない transcript だけ、今までどおり直近のユーザー入力も読む。合図にするのは、語の後が文末・空白・句読点・接続の語（`ので`・`から`・`が`・`よ`・`けど`・`です`）のマージ済みの報告だけにした。`マージしたら次に進んで`・`マージしたい`・`マージした？`・`マージしたPR` は合図にしない（これまでは合図にしていた）。marker を作った時刻（`created_at_epoch`）より前の発話は、合図に数えない。ただし marker の PR の URL がそれより前に assistant の本文に出ていれば、その時刻からの発話を数える（PR を作った後・marker を書く前に届いた合図）。`created_at_epoch` が使えない値（0 以上で今より後でない整数でないもの）のときと、URL の record の時刻が読めないときは区切らない。発話の時刻が読めないときと、`origin` を書かない transcript の直近のユーザー入力は、時刻で区切らない。

継続判定（`looks_like_gdd_continuation`）が読む直近のユーザー入力は変えていない。`type: "user"` で届いた peer のメッセージの後は、queued の人間の発話があっても今までどおり確認を始めない。queued の行のうち、origin の無い行・`human` 以外の kind の行と、`queue-operation` の `remove` の行は合図に数えない。

この変更で、マージ後の確認の marker（`.claude/gdd-post-merge-continuation.json`）があるときに turn の途中で「マージした」と送ると、確認の前の停止を block するようになる。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/constants.py`
- `plugins/gate-driven-development/hooks/scripts/lib/merge-gate-evidence.sh`（コメントだけ）
- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/lib/post_merge_continuation.py`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/tests/test_queued_human_merge_cue.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_queued_human_merge_cue.py` を足した（Stop hook の入口から、queued の人間の「マージした」で block すること、合図の後の skill の前置き・ci-monitor-event の行で合図が消えないこと、後から届いた別の PR の合図で前の合図が消えないこと、marker を作った時刻（それより前に PR の URL が出ていればその時刻）より前の合図を数えず、別の session で合図の後に URL を書いても合図を数えること、時刻が読めないとき・使えない created_at のときは数えること、注入の行の語と未マージの発話（`マージしたら` など）を合図にしないこと、別の PR の合図・peer の後・次の type:user の発話の後では block しないこと、type:user の合図の後の割り込みで合図が消えないこと、人間以外の queued の行を合図にしないこと、marker が読めないときは block すること。parse_transcript の単体で、last_user_text を変えないことと、形の崩れた prompt で落ちないこと）
- `bash tests/validate-plugin.sh`
