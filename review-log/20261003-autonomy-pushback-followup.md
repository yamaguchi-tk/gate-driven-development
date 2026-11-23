---
lane: L1+
pr: 350
follow_up_of: 342
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (Plan, model: opus) | - | 0 | 0 | 0 | 2026-10-03T10:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 028ec076cf8f1a34e36f8eee884ddf31b02dacef | 0 | 1 | 1 | 2026-10-03T15:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | f02778ce8768fedfc3f458222812fe0ee89aec84 | 0 | 1 | 0 | 2026-10-03T16:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | advisory | no | inherited | pushback-deadline | fixed | 締め切りの起点を使った時間の合計だけにすると全体の上限が無くなる。プロセスの開始からの上限 6 秒と小さいほうにした。記録の書き込みは呼び出し側の thread で、try の内側で行う。commit: (本 PR) |
| pm-2 | 方針メモ | advisory | no | inherited | merge-intent-session | fixed | 宣言を書いたセッションは、resolve したパスの一致で比べ、約束の理由文と post-merge-qa.md に Write で書くことを書く。human check の peer は設計上の理由だけを書いて揃えない。commit: (本 PR) |
| i1-1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | failure・no-checks の理由文が、宣言の原文より広いマージの許可を出す。4 状態とも宣言の原文と repo・タスクの手順で決めるよう書き、no-checks は待たせる。commit: a9bf1f39, e4f2f91b |
| i1-2 | 独立-1 | low | no | self-inflicted | merge-intent-parse | fixed | `repo`・`then` の偽の値（false・0）を null 以外も省略として受け付ける。null だけを省略にした。commit: a9bf1f39, e4f2f91b |
| i1-3 | 独立-1 | low | no | self-inflicted | merge-intent-session | fixed | 宣言のパスに一度書いたセッションが、別のセッションが書き直した宣言でも所有者になる。最後の書き込みの内容が今の宣言と一致するときだけにした。commit: a9bf1f39, e4f2f91b |
| i1-4 | 独立-1 | low | no | self-inflicted | test-power | fixed | 所有者の判定のテストに MultiEdit・相対パス・symlink が無い。subTest を足した。commit: e4f2f91b |
| i1-5 | 独立-1 | low | no | self-inflicted | pushback-deadline | fixed | 締め切りの新しい閾値に入口からのテストと「残り 0」の記録の検査が無い。遅い HITL lint の e2e と記録の assert を足した。commit: e4f2f91b |
| i1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | state-machine.md の判定順序に、rule 1 より前のマージ待ちの押し返しが無い。0. を足した。commit: a9bf1f39 |
| i1-7 | 独立-1 | low | no | self-inflicted | pushback-deadline | fixed | hooks.json の description・断片・docstring の締め切りの説明が実装とずれている。合計 3 秒とモジュールの読み込みから 6 秒に直した。commit: a9bf1f39 |
| i1-8 | 独立-1 | low | no | self-inflicted | merge-intent-session | fixed | 書き込みの tool の集合に ApplyPatch が無い。対象外であることを post-merge-qa.md と断片に書いた。commit: a9bf1f39 |
| i1-9 | 独立-1 | advisory | no | self-inflicted | hook-error-log | accepted | hook エラーの記録先が toplevel から hook の cwd に変わった。Stop hook のほかの記録と揃っているので変えない |
| i1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | subagent の tool_use が親 transcript に載るか、Write で `.claude/` に書けるかは未実測。PR 本文の限界に書く |
| i1-11 | 独立-1 | advisory | no | self-inflicted | pushback-deadline | accepted | 6 秒の上限のため、前処理が遅いと done guard の残り時間が約 4 秒まで減る。PR 本文の限界に書く |
| i1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 前の PR の未リリース断片に古い説明が残る。次のリリースの dry-run で版の節を直す |
| i1-13 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | RunWithinDeadlineTest が書き換えた定数を戻さない。今は in-process で後から呼ぶテストが無い |
| i2-1 | 独立-2 | medium | no | self-inflicted | merge-intent-session | accepted | 空の `new_string` か短い文字列の Edit が最後の書き込みだと、別のセッションが書き直した宣言でも押し返す。PR 本文の限界に書く |
| i2-2 | 独立-2 | low | no | self-inflicted | merge-intent-session | accepted | Write の中身を完全一致で比べるので、書いた後に整形されると押し返さない。PR 本文の限界に書く |
| i2-3 | 独立-2 | low | no | self-inflicted | pushback-deadline | accepted | 断片の「前処理が 6 秒未満なら届く」は、マージ待ちが 3 秒を使い切ったときと残りが短いときに成り立たない。PR 本文の限界に書く |
| i2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | state-machine.md の判定順序 0 に約束の押し返しと MultiEdit・今の宣言の条件が無い。hooks.json の description も同じ。PR 本文の限界に書く |
| i2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | 所有者の判定のテストに、Edit の不一致と、一致する Write の後の不一致の Write の負例が無い。PR 本文の限界に書く |
| i2-6 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 理由文のテストは古い文言 2 つが無いことしか見ていない |
| i2-7 | 独立-2 | advisory | no | self-inflicted | merge-intent-parse | accepted | 壊れた宣言で止まるたびに例外の repr（宣言の中身を含む）が記録される。`{}` の宣言は約束の押し返しを止める |
| i2-8 | 独立-2 | advisory | no | self-inflicted | merge-intent-session | accepted | transcript の 1 行の file_path に NUL などがあると、所有者の判定全体が例外で押し返さない側に倒れる |
| i2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 前の PR の未リリース断片に古い締め切りと理由文の説明が残る。リリースの dry-run で直す |
| i2-10 | 独立-2 | advisory | no | self-inflicted | style | accepted | テスト名 test_hard_limit_from_process_start が起点の変更と食い違う |
| i2-11 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 遅い HITL lint のテストは時間の余裕が約 2 秒で、負荷の高い runner で誤って落ちうる |
