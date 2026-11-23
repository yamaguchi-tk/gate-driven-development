---
lane: L1+
pr: 365
follow_up_of: 359
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (opus-advisor, model: opus)（旧#359 の next-pr〔review-log/20261003-gate-runner-background.md の F17〜F20・F23〜F25・F31〜F36・F39〕を直す後続 PR。F38〔マージ済みの未リリース断片の Affected Files〕はリリースの dry-run で直す。実測 2026-10-04、直近 30 日の transcript 3,203 本: Agent・Task の tool_result の起動応答 3,515 件はすべて本文の先頭。`run_in_background: true` を付けない Agent・Task 6,285 件のうち 1,829 件が起動応答を受けていた〔host が background で動かす〕ので、独立-4 の F33 の修正案〔run_in_background を条件に足す〕は本物の background を取りこぼす。parser と同じ text の取り方で全 tool_result を測ると、今の正規表現で 3,524 件、先頭に固定すると 3,515 件で、外れる 9 件はすべて引用〔fixture を読んだ Bash の出力 8 件、同期の相談役の回答 1 件〕。main の案は、F33 を parser の先頭固定で、F24 を try_stop_with_done_guard の先頭で昇格を済ませて押し返しを 1 か所で先に呼ぶ形で直すもの。Opus も同じ形を推し、限界〔host が起動応答の前に何かを付けると通す側に倒れる〕・計測の取り方の確認・background Bash の起動応答を先頭に固定しない理由〔読む側が Bash と run_in_background を確かめる〕を書くよう足した。採った。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-04T23:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 58f5a4783f6b29ed757eddd2ba1af88e1f5ed889 | 0 | 0 | 0 | 2026-10-05T00:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | b7ebb2c3310ba7f6513263787064741764543b66 | 0 | 0 | 0 | 2026-10-05T01:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨〔parser の先頭固定、押し返しを先頭へ、限界の追記〕を採用） |
| F1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストの docstring 2 か所が「state を消す直前で押し返す」の古い順序のまま commit: 33c17bb9 |
| F2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 末尾改行のテストの _blocked が hook を問わず block と deny のどちらも止めたとみなし、既存の hook の assert を緩めていた。hook ごとに止める形を持たせた commit: 33c17bb9 |
| F3 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 変更断片の Validation に時点に依存する件数がある。PR 本文へ移した commit: 40698ff2 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片が Bash の出力の引用も判定を変えていたと書き、読み手から期限 watchdog が抜けている commit: 40698ff2 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片が、README にも background の返りを拾わないことを書いたと読める。README に足し、断片を書き分けた commit: 40698ff2 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | stop-hook-structured-markers.md・state-machine.md が「最初に押し返す」と書くが、マージ待ちの押し返しと期限 watchdog が先に走り、押し返しを飛ばす条件もある commit: 40698ff2 |
| F7 | 独立-1 | low | no | inherited | doc-claim | fixed | state-machine.md の判定順序の規則 1 が「subagent の tool_result」のままで、実装は tool を問わず最後の tool result を読む commit: 40698ff2 |
| F8 | 独立-1 | low | no | inherited | doc-claim | fixed | stop-hook-structured-markers.md の Marker Sources と Fallback 表が「Agent tool result」に限っている commit: 40698ff2 |
| F9 | 独立-1 | low | no | inherited | doc-claim | fixed | state-machine.md の判定順序に期限 watchdog が無い commit: 40698ff2 |
| F10 | 独立-1 | low | no | inherited | doc-claim | fixed | stop-hook-structured-markers.md の許可 reason の一覧が 5 つだけ commit: 40698ff2 |
| F11 | 独立-1 | low | no | inherited | doc-claim | fixed | 継続契約の TaskStop の規定に staging-verification-blocked が無い commit: 40698ff2 |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | state-machine.md の待ちの節の期限 watchdog の参照先が § Typed Agent Resolution だけ commit: 40698ff2 |
| F13 | 独立-1 | low | no | self-inflicted | test-power | fixed | 「前提を満たさない done」のケースは binding が無く done guard に届かない。名前を直し、bind 済みで tasklist の検証が通らない done のケースを足した commit: 33c17bb9 |
| F14 | 独立-1 | low | no | self-inflicted | test-power | fixed | 昇格した reason を見出しの要求も使うことを固定するテストが無い commit: 33c17bb9 |
| F15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | general-purpose で起動し直すときの run_in_background の規定は散文だけで、deny も期限 watchdog も当たらない。PR 本文に書く |
| F16 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 実測値に再現するコマンドと sha が無い。PR 本文に書く commit: なし（PR 本文） |
| F17 | 独立-1 | advisory | no | inherited | product | accepted | content が list のときは最後の text block だけを読むので、host が起動応答の後ろに別の block を足すと background を同期と読む（差分の前からの読み方）。PR 本文に書く |
| F18 | 独立-2 | low | no | inherited | doc-claim | accepted | state-machine.md の § Autonomous Continuation が許可 reason を 7 種類だけと書く（hook は 8 つを受理する）。PR 本文の限界に書く |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「最後の tool result」は実際には本文が空でない最後の tool result。本文が空の tool を呼んでも前の marker は消えない。PR 本文の限界に書く |
| F20 | 独立-2 | low | no | self-inflicted | test-power | accepted | 末尾改行のテストの対照（inactive）が、宣言と違う形の出力を見ない（出力が空なことは別のテストが見る。plan-mode hook を除く）。PR 本文の限界に書く |
| F21 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が、README の「marker は本文に書く」と継続契約の staging-verification-blocked の追記を書いていない commit: なし（PR 本文） |
| F22 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 継続契約の停止 marker の一覧が 4 つのまま。PR 本文に書く |
| F23 | 独立-2 | advisory | no | inherited | doc-claim | fixed | PR 本文の限界が、起動応答の書式が変わったときに待つ間に継続を促されることを書いていない commit: なし（PR 本文） |
| F24 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の実測に前後の件数・sha・計測の範囲が無い commit: なし（PR 本文） |
| F25 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 前の未リリース断片が古い押し返しの順序を書く。リリースで新しい断片に寄せる |
| F26 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「HITL lint より先」は、HITL lint が human-check-waiting だけを見るので競う場面がない（誤りではない） |
