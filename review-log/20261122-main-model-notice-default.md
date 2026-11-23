---
lane: L1
pr: 731
amends: 20261030-main-model-gate.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8554a6d0 | 0 | 0 | 0 | 2026-11-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 68b1b169 | 0 | 0 | 0 | 2026-11-22 |
| 方針メモ-1 | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | 68b1b169 | 0 | 0 | 0 | 2026-11-22 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | e7a7ea95 | 1 | 2 | 0 | 2026-11-22 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | f2868b12 | 0 | 1 | 0 | 2026-11-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | request | fixed | 設計: 変えない（画面での切り替えは transcript に残らないことがあり、判定では見分けられない）。新しいセッションの通知が UserPromptSubmit に移り、画面での切り替えが記録に残らなかった直後に前のモデルで知らせうる。記録なしの切り替えは 30 日で 102 件。通知の文に、切り替えの直後は前のモデルを指すことがあると書いた。commit: 68b1b169 |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 原因を settings の既定と断定した測定の記録が無い。payload の model の有無は確かめていない。測定は review-log の notes に書いた |
| I1-3 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の Affected Files に、amends で書き換えた断片とテストが無い |
| I1-4 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 未リリースの挙動の変更を、利用者から見える変更として断片に書いている |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しいセッションの最初の発言が /gdd-dev なら、モデル名つきの通知は出ず「判定できませんでした」だけが出る。限界に書いていない |
| I1-6 | 独立-1 | advisory | no | self-inflicted | scope | accepted | 既定を外す範囲が Desktop だけでなく CLI にも及ぶ |
| I1-7 | 独立-1 | advisory | no | inherited | doc-claim | accepted | docs/SECURITY.md の hook の表に main-model-gate が無い（以前から） |
| I1-8 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 既定を使わないことのテストが、hook が落ちたときも通る（stderr を見ていない） |
| I2-1 | 独立-2 | low | no | self-inflicted | request | fixed | 設計: 変える（通知を返事の前の UserPromptSubmit で判定していた）。画面での切り替えの直後の誤った通知が残り、注記で代えていた。相談役 2 本の推奨どおり、通知を返事の後の Stop に移し、注記を戻した。commit: e7a7ea95 |
| I2-2 | 独立-2 | low | no | self-inflicted | style | fixed | 足した注記の主語が無く、main が前のモデルのままと読める。注記は通知を Stop に移したときに戻した。commit: e7a7ea95 |
| I2-3 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 変更断片に通知の文が変わったことが無い。Summary に足した。commit: df6179b7 |
| I2-4 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 足した注記を元に戻しても落ちるテストが無い |
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | design | fixed | 2 本とも、注記を足す案と transcript からの通知をやめる案のどちらでもなく、通知を返事の後の Stop に移す案を推した（返事の後なら最後の信号は今答えたモデル）。採った。commit: e7a7ea95 |
| I3-1 | 独立-3 | high | no | self-inflicted | wiring | fixed | 設計: 変えない（Stop の本数を固定するテストが、知らせだけの hook を名前で外す形で、足すたびに書き足す決まり）。Stop に通知の hook を足したのに、Stop の配線を固定するテストを直しておらず落ちる。知らせだけの hook として外す名前に足した。commit: 9a4f6709 |
| I3-2 | 独立-3 | medium | no | self-inflicted | request | fixed | 再開の SessionStart が再開の前のモデルで知らせうる経路を、確認なしに限界にしていた。再開でも transcript からは知らせず、最初の返事の後の Stop に任せた。/gdd-dev を止める文のずれは警告ではなく止める判定の側で、この依頼の外として限界に書いた。commit: f2868b12 |
| I3-3 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | Stop の時点で transcript に今の返事が書かれていることと、Desktop で Stop の systemMessage が出ることを実測しておらず、hooks.json の説明などが断定している。PR 本文の限界に未検証と書いた |
| I3-4 | 独立-3 | low | no | self-inflicted | test-power | accepted | 通知を出さないことだけを見る Stop のテスト 2 本は、Stop を扱わない元のコードでも通る（全体ではほかのテストで固定されている） |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | README と元の断片に「相談の段の発言で」が残り、README の Stop の行に通知が無い。再開の SessionStart の記述を直すときに合わせて直した。commit: f2868b12 |
| I3-6 | 独立-3 | low | no | self-inflicted | perf | accepted | Stop のたびに、印を見る前に transcript を全部読む |
| I3-7 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | decide() は止める判定と共有なので L1+ とも読める。(g)(h)・security で指摘なし |
| I3-8 | 独立-3 | advisory | no | self-inflicted | product | accepted | /model で切り替えたときも、通知が 1 ターン遅れる |
| I4-1 | 独立-4 | medium | no | self-inflicted | request | next-pr | 画面で切り替えた直後の /gdd-dev を止める文も「今の main は Sonnet」と誤る。ユーザーが依頼に含めると答えた（.request.md）。止める判定を変える L1+ の次の PR で直す |
| I4-2 | 独立-4 | medium | no | inherited | product | accepted | SessionStart の payload の model が Desktop で実際のモデルと合う証拠が無い。PR 本文の限界に未検証と書いた |
| I4-3 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の Affected Files に、Stop の配線のテストが無い |
| I4-4 | 独立-4 | advisory | no | self-inflicted | test-power | accepted | 再開のテストは、再開の後に別のモデルが答えた場面を通していない |
| I4-5 | 独立-4 | advisory | no | inherited | doc-claim | accepted | README の PreToolUse の hook 数が hooks.json と合わない（以前から） |
| I4-6 | 独立-4 | advisory | no | inherited | doc-claim | accepted | docs/SECURITY.md の state dir の一覧に通知の印が無い（以前から） |
| I4-7 | 独立-4 | advisory | no | self-inflicted | perf | accepted | Stop のたびに transcript を全行読む |
