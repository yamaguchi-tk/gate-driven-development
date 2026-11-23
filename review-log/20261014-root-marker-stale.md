---
lane: L1+
pr: 496
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | e5df22e2 | 0 | 0 | 0 | 2026-10-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a9fa22d8 | 0 | 3 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 35e27f6e | 0 | 1 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | advisory | no | inherited | design | accepted | 採用: 案 1（ロックのメッセージに持ち主の最後の記録の時刻を出す。block/allow は変えない）。main の最初の案は案 1＋案 2（持ち主が 8 日以上動いていなければ外す）。Opus は案 2 を足さないと推奨（損失の主因の写しは C-1 で閉じ、root の 21 件中 18 件は 72h 未満、8 日で外れるのは 2 件）。追加の実測で 8 日以上空いた後の再開が 610 本中 22 回あり、main も案 2 をやめた。信号 ① で Fable に相談し、Fable も案 1。ユーザーが案 1 を選んだ |
| I1-1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | session_id の許可リストを消しても、パス・glob の文字の param がどれも unknown のまま通る。辿った先に実在するファイルを置く param（../-p/OLD-SESSION など）にし、時刻が出ないことも確かめた commit: b6db1bf2 |
| I1-2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 経過時間の値を確かめるテストが無い（"h ago" の部分一致だけ）。今から相対の時刻で、行全体を比べる形にした commit: b6db1bf2 |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 時刻を空白の無い "timestamp":"…" の正規表現で取り、入れ子の timestamp も最大値に入る。末尾の各行を JSON として読み、top-level の timestamp だけを使う形にした。直近 50 本の transcript で 50 本とも時刻が取れる commit: b6db1bf2 |
| I1-4 | 独立-1 | low | no | self-inflicted | test-power | accepted | 最大値ではなく最後に当たった値・最後に読んだ dir の値を採る実装でも、dir の並びによってはテストが通る |
| I1-5 | 独立-1 | low | no | self-inflicted | test-power | accepted | HOME と CLAUDE_CONFIG_DIR の両方を読んで最大値を採る実装でも通る |
| I1-6 | 独立-1 | low | no | self-inflicted | test-power | accepted | 先頭の 1 MiB を読む実装でもテストが通る（1 MiB を超える transcript のテストが無い） |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docs/TROUBLESHOOTING.md の復帰の手順が Existing session last active: の行に触れていない |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docs/SECURITY.md に、ロックの分岐で別の session の transcript の末尾を読むことが書かれていない |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「Cursor・Codex では unknown」が実際と違う（Codex と変数を受け継がない Cursor はロックが起きない。受け継いだ Cursor は親の時刻が出る） commit: なし（PR 本文） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | product | accepted | transcript が無いときに marker の started_at を下限として添えられる |
| I1-11 | 独立-1 | advisory | no | self-inflicted | product | accepted | 1 時間未満が全部 0h ago、時刻が UTC だけ、未来の時刻で -1h ago になる |
| I1-12 | 独立-1 | advisory | no | self-inflicted | product | accepted | 案内の行が、時刻の行をユーザーに見せることを求めていない |
| I1-13 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 既存のロックのテスト 2 本が HOME を差し替えず、実際の ~/.claude/projects を走査する |
| I1-14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | commands/gdd-dev.md の手動の手順で止まるときは、時刻を出す手順が無い |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | accepted | splitlines() が U+2028 などでも行を分け、その記録の timestamp を読み落として古い時刻が出うる。同じ入力を読む lib/transcript.py・autonomy_pushback.py は split("\n") |
| I2-2 | 独立-2 | low | no | self-inflicted | product | accepted | 日付として正しくない timestamp が 1 件でもあると、fromisoformat の ValueError で全体が unknown になる。\d が全角数字にも当たる |
| I2-3 | 独立-2 | low | no | self-inflicted | product | accepted | 秒で切り捨てて比べるので、同じ秒の中では最大値の文字列にならない |
| I2-4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 1 MiB を超える transcript のテストが無く、末尾へ seek する分岐を通らない |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | 入れ子の timestamp を top-level より後ろにしか置いておらず、行ごとに最初の値を採る実装でも通る |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の実測が、コードより広い条件で数えていた。スクリプトと同じ関数で数え直した（50/50） commit: なし（PR 本文） |
| I2-7 | 独立-2 | advisory | no | inherited | doc-claim | accepted | docs/TROUBLESHOOTING.md の復帰の節が Existing session last active: の行に触れていない |
| I2-8 | 独立-2 | advisory | no | inherited | doc-claim | fixed | transcript に記録が増えない間（返事待ち・timer・subagent の待ち）は、動いている session でも古い時刻が出ることを PR 本文の限界に書いた commit: なし（PR 本文） |
| I2-9 | 独立-2 | advisory | no | inherited | product | accepted | 未来の時刻で (-1h ago) と出る |
| I2-10 | 独立-2 | advisory | no | self-inflicted | style | accepted | テスト名の real_json_spacing が、空白入りの JSON を実際の形と読ませる |
