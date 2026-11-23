---
lane: L1+
pr: 336
follow_up_of: 315
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#315 の受け入れた限界を直すユーザーの指示について、`review-log/20261003-deny-count-once-per-path.md` の方針メモと同じ相談。Opus は F3 を前と後の両方で救済読みにする、G1 は差し引きを Completed から消えた件数に限る、共有の counter（G2）と guard の中身を 2 本に分ける、と指摘し、main の案の欠陥の指摘として全部採った。この PR は G2 以外（F2・F3・G1・F10 と文言・テスト）。前に閉じていない fence が無いときは fence を追う読み方の比較も足し、閉じていない fence を足して完了タスクを隠す書き込みを今までどおり止める） | - | 0 | 0 | 0 | 2026-10-03T03:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 16472601 | 2 | 0 | 2 | 2026-10-03T05:30+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（C2 の `閉じ方: 列挙`。Opus は、厳密な UTF-8 の読みを、正しい UTF-8 だけを受け付ける許可リストとして (a) に当たるとし、F10 の取り消しに賛成した。拒否する語〔BOM・NUL〕を足す案は拒否リストの併用で閉じない。実測: transcript に hook の `could not check (UnicodeDecodeError)` の deny は 0 件で、誤 block は 0 件。main の案と一致したので Fable は呼ばなかった） | - | 0 | 0 | 0 | 2026-10-03T05:45+09:00 |
| 独立-2 | light-lane-independent-reviewer, 全差分, model: opus | da4a2822 | 1 | 0 | 1 | 2026-10-03T06:20+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + user（安全策 4 の発火。同じクラスタ「completed_reviewed_by の fail-open」の high を含む巡が 2 回。実測: tasklist.md 241 本の最終状態で、完了タスクの名前と Current・Pending の名前の重なり 0、Completed 内の同名 0、入力者は未測。Opus は「止める」を推奨（docstring に前から書いた設計上のトレードオフの再報告で、増えた分だけ差し引く案は WHY 文言の 2 回の手順を止め、同名の新タスクを同時に足す形が残って閉じない）。信号 ② で Fable にも相談し、同じく「止める」を推奨（測っても行き先は変わらない、限界に「入力者: 未測」を書く）。ユーザーは Fable の意見を確かめた上で「止める」を選んだ） | - | 0 | 0 | 0 | 2026-10-03T06:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 方針メモ | - | - | - | - | - | なし |
| C1 | 独立-1 | high | yes | self-inflicted | completed_reviewed_by の fail-open | fixed | 閉じていない fence を除くたびに全体を読み直すので、閉じない開き fence を数千行並べると hook の timeout に届き、書き込みが検査されずに通る。読み直しの回数に上限を置き、超えたら判定できないとして止める。commit: b877d395 |
| C2 | 独立-1 | high | yes | self-inflicted | completed_reviewed_by の fail-open | fixed | 列挙: 書き込みの前を `errors="replace"` で読むと、構造の行が読めなくなる tasklist.md（UTF-16 など）への Write が通る。方針メモ-1 で (a)。置き換えて読むのをやめ、UTF-8 で読めなければ止める（F10 は限界に戻す）。commit: eca35ff8 |
| C3 | 独立-1 | medium | no | inherited | 文言 | next-pr | gdd-task-breakdown の作り直しと refactor の abort の手順（skills/gdd-task-breakdown/SKILL.md:64、references/task-breakdown-steps.md:12、skills/gdd-refactor-planning/SKILL.md:226）が、guard と WHY 文言の「先に Pending へ移す」と食い違う。ユーザーが選んだ 3 本の分け方の ③（F6・G6）で直す |
| C4 | 独立-1 | low | no | self-inflicted | completed_reviewed_by の fail-open | fixed | 前から閉じていない fence があると fence を追う比較を飛ばし、前は止めていた隠す書き込みが通る。比較を常に両方で行う。commit: b877d395 |
| C5 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 「Completed に残ったまま ok でなくなった分は返す」が、同じ書き込みで同名の ok でない完了タスクを消すと成り立たない。docstring・断片・PR 本文に限定を付けた。commit: b877d395, da4a2822 |
| C6 | 独立-1 | low | no | self-inflicted | テスト | fixed | 足したテストが、fence を繰り返し除く処理と degraded の 2 つの項を固定していない。3 本を足した。commit: 7f92adcc |
| C7 | 独立-1 | low | no | self-inflicted | 文言 | fixed | `elif lost - degraded > reopened` の引き算が常に 0。commit: b877d395 |
| C8 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | Edit の改行の扱いの混在の形を、実際のツールで試した記録が差分に無い |
| D1 | 方針メモ-1 | - | - | - | - | - | なし |
| E1 | 独立-2 | high | yes | self-inflicted | completed_reviewed_by の fail-open | accepted | 列挙: 再オープンの差し引き `reopened = open_task_names(after)` が書き込みの前からある同名タスク（閉じていない fence の中の記入例を含む）も数えるので、同名タスクが前から Current・Pending にあると、完了タスクを消す・Reviewed by を落とす書き込みが通る（origin: pre-existing）。方針メモ-2 で止める |
| E2 | 独立-2 | low | no | self-inflicted | completed_reviewed_by の誤 deny | accepted | 書き込みの前の閉じていない fence の中に行頭のタスク行と Reviewed by 行があると、その fence を閉じる書き込みが removed で止まる |
| E3 | 独立-2 | low | no | self-inflicted | 文言 | accepted | Completed に残ったまま Reviewed by を失い、同名の ok でない完了タスクを同時に消すと、deny の理由が removed になる |
| E4 | 独立-2 | low | no | inherited | 文言 | re-reported | gdd-task-breakdown と gdd-refactor-planning の手順が、guard が止める 1 回の削除のまま（C3 の再掲） |
| E5 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 変更断片の Validation 欄が、テストの名前でなく件数で書かれている |
| E6 | 独立-2 | low | no | self-inflicted | テスト | accepted | 閉じていない fence の上限 10 がテストで固定されていない（50 本で確かめている） |
| E7 | 独立-2 | advisory | no | self-inflicted | 文言 | accepted | 閉じていない fence の上限を超えたときの deny が、原因と直し方を示さない |
| E8 | 独立-2 | advisory | no | inherited | 性能 | accepted | `strip_fenced_lines_marked` は閉じた fence の数 × 行数に比例し、比較の呼び出しが 1 回の書き込みで 3 回から 6 回に増えた（未測） |
| D2 | 方針メモ-2 | - | - | - | - | - | なし |
