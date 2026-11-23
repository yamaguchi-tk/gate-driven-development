---
type: minor
---

#### Summary

- human check の提示のときに、推奨をユーザーの発言に別の読み手が照らし、推奨どおりに進めると依頼から変わるところ・満たせないところがあれば、`依頼との差（変わる）: <発言> → <推奨>` と `依頼との差（満たせない）: <発言>（別の案: なし）` の形で、種類ごとに 1 行（最大 2 行）人に見せる Stop hook を足した。提示は止めず、main に書き直させない。1 回の起動に数秒〜数十秒かかり、そのぶん停止の表示が遅れる
- 読み手は `claude -p`（Opus・medium・ツールなし・hook なし）で動く。起動ごとに費用がかかる（過去の 70 件で約 $0.03）
- transcript にユーザーの発言が無いセッション（依頼が親セッションから渡されたものなど）と、起動に失敗したときは何も出ない。理由は記録に残る

#### Affected Files

- `hooks/hooks.json`、`hooks/scripts/run-request-diff-hook.sh`、`hooks/scripts/lib/request_diff.py`
- `README.md`

#### User Action Required

- なし。使わないときは環境変数 `GDD_SKIP_REQUEST_DIFF=1` で切れる

#### Validation / Eval Impact

- 結果は `~/.claude/.gdd-hook-state/request-diff.log` に残る。ユーザーの発言の引用を含むので、共有しない
