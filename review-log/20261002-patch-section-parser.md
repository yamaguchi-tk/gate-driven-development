---
lane: L1+
pr: 323
follow_up_of: 305
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#305 の限界の常時 High を閉じる次の PR。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた。Opus は「要る・閉じる」とし、header の先頭の空白は実データ 0 件でも 1 文字で guard 全体を素通りできる穴だと再現して、Codex と同じ状態を持つ走査を 1 本にし、6 つの関数をすべてその結果から作る広い側を推した。End Patch は止めずに区切りを閉じるだけにすること、Move to は Update の中なら位置を問わず受けることも足した。main は広い側の既定に従って採った。Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-02T20:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 79aaac0ac96e3c7217e035a0418f77a4f1b92bb0 | 6 | 1 | 6 | 2026-10-03T10:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 18cc23b7904d9e3e02d5029d804c6ca8c2b77c78 | 3 | 0 | 3 | 2026-10-03T11:00+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user（安全策 4 の発火〔high を含む巡が 2 回、クラスタ origin-final-state・patch-fence-scope・patch-line-split の high が独立-1・独立-2 の 2 巡〕。Opus は、3 件とも 1 巡目の修正が base より緩めた退行なので、deny を足すだけの和集合で直して 3 巡目を最後にする (A) を推した。信号 ② で呼んだ Fable も賛成し、Q3 は parser の割り方の和ではなく「改行に似た文字と `.steering` を含む書き込みは早期 allow しない」で閉じること、3 巡目に high が残ったら往復せずに止めることを足した。ユーザーが (A) と Fable の補足を選んだ） | - | 0 | 0 | 0 | 2026-10-03T11:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 8975e7e7cf97d36ca41ae39147a5631f7ffcefeb | 3 | 0 | 3 | 2026-10-03T13:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| P1 | 独立-1 | high | yes | inherited | patch-line-split | fixed | `splitlines()` が `\u2028` などでも行を割り、header の path が切れて steering の target から漏れ、main() が早期 allow する。`\n` だけで割る commit: 24996fb8 |
| P2 | 独立-1 | high | yes | self-inflicted | patch-fence-scope | fixed | move で引き継いだ前の hunk の ``` と by_path で対になり、値が fence の中として免除される。hunk ごとに分ける commit: 24996fb8 |
| P3 | 独立-1 | high | yes | self-inflicted | origin-final-state | fixed | End of File が hunk を閉じなくなり、同じ値の Origin Session 行と Delete File の組が通る。削除を追加行より先に判定する commit: 24996fb8 |
| P4 | 独立-1 | high | yes | inherited | origin-final-state | fixed | `_origin_session_new_values` が削除・move・Add File の上書きより先に追加行の値を返す。削除を先に判定し、Add File は全文として読む commit: 24996fb8 |
| P5 | 独立-1 | high | yes | inherited | fence-fragment | accepted | fence の免除をファイル全体ではなく断片（Edit・Update の hunk）の中で判定し、既存の fence と組んで外に出る値を通す。ユーザーの判断で限界に書き、次の PR へ |
| P6 | 独立-1 | high | yes | inherited | removal-fuzzy | accepted | 先頭に空白・Unicode のダッシュを持つ削除行を field の削除と認めない（Codex の曖昧一致の規則は未確認）。ユーザーの判断で限界に書き、次の PR へ |
| P7 | 独立-1 | medium | no | self-inflicted | patch-move | fixed | Move to の target が前より狭い（Update の中の最後の 1 本だけ、Update の外は落とす）。全部を移動先・target にする commit: 24996fb8 |
| P8 | 独立-1 | low | no | self-inflicted | dead-code | fixed | `patch_move_sources` に本番の呼び出し元が無く、docstring も古い。削除する commit: 24996fb8 |
| P9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「1 回だけ走査」「全部 _scan から」が強すぎる（関数ごとに _scan を呼ぶ、extract_added_lines は別）。言い換える commit: 24996fb8 |
| P10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「End Patch の後ろはどのファイルにも属さない」が強すぎる。「次の header まで」にする commit: 24996fb8 |
| P11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 実データの件数に、測ったコマンドが無い。PR 本文に書く |
| P12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に載っていない変更がある。PR 本文に列挙 |
| P13 | 独立-1 | advisory | no | self-inflicted | style | accepted | 空行 3 つ・長い行・`_PATCH_ADD_HEADER` が無い。PR 本文に列挙 |
| Q1 | 独立-2 | high | yes | self-inflicted | origin-final-state | fixed | 削除の判定を先に返し、Add File の分岐が移動元の値を見ないので、既存値の無い state.md で消して作り直す・Add と move を重ねる patch の追加値が判定から外れ、peer turn の初回書込みと複数値の deny が外れる。書込み後に残りうる値の和で判定する commit: 6e58254d |
| Q2 | 独立-2 | high | yes | self-inflicted | patch-fence-scope | fixed | by_path を section ごとから hunk ごとに置き換えたので、同じファイルの別の hunk との fence の対が見られず、base で止まっていた値が通る。hunk ごととファイルごとの両方で見る commit: 6e58254d |
| Q3 | 独立-2 | high | yes | self-inflicted | patch-line-split | fixed | `split("\n")` にしたので、`splitlines()` なら割る文字の後ろの header を target に拾わず、その文字で割る harness では main() が早期 allow する。改行に似た文字と `.steering` を含む書き込みは早期 allow しない commit: 6e58254d |
| Q4 | 独立-2 | low | no | self-inflicted | test-power | accepted | Unicode 改行のテストが終了コード 2 だけを見ている。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| Q5 | 独立-2 | low | no | self-inflicted | test-power | accepted | 同じ path への move のテストが、削除の判定の順序の変更を固定していない。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| Q6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `collect_line_break_violations` の docstring が古い割り方を書いている。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| Q7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 「削除の 4 形」の数が Add File の追加で合わない。docstring を書き直す commit: 6e58254d |
| Q8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `parse_patch_sections()` の docstring の `patch_move_sources_for()` の役割が違う。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| Q9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の実測に再現の手順と比べた範囲が無い。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| Q10 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | ヘルパの列挙コメントに `patch_adds_file` が無い。列挙をやめて import 部を参照する commit: 6e58254d |
| R1 | 独立-3 | high | yes | inherited | origin-final-state | accepted | 和を取ると「書込み後に値が無い」結果（`[]`）が消え、Add File の置き換えと同じ値の move を重ねる形・同じ値を足す hunk と field の無いファイルの move を重ねる形で write-once の削除が通る（main の aa0f99d0 でも 2 形とも allow を実測）。方針メモ-2 の決定（3 巡目に high が残ったら往復せずに止める）に従い直さず、PR 本文の限界の節の先頭に書く |
| R2 | 独立-3 | high | yes | inherited | origin-final-state | accepted | 移動先の section に Origin Session の削除行が 1 本でもあると move 元の値が全部落ち、peer turn の初回値・複数値の deny が外れる。方針メモ-2 の決定（3 巡目に high が残ったら往復せずに止める）に従い直さず、PR 本文の限界の節の先頭に書く |
| R3 | 独立-3 | high | yes | inherited | peer-turn-move | accepted | peer turn の記録の検査が ApplyPatch の move で運ばれる move 元の内容を見ず、承認の記録を書ける。方針メモ-2 の決定（3 巡目に high が残ったら往復せずに止める）に従い直さず、PR 本文の限界の節の先頭に書く |
| R4 | 独立-3 | low | no | self-inflicted | product | accepted | 既存値の無い state.md を消して値つきで作り直す非 peer の初回書込みが、複数値の文言で止まる。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R5 | 独立-3 | low | no | self-inflicted | style | accepted | `patch_added_lines_by_path`（hunk ごと）と `patch_added_lines_by_section`（ファイルごと）の名前が逆に読める。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R6 | 独立-3 | low | no | self-inflicted | test-power | accepted | `.steering` を含み改行に似た文字の無い steering 外への書き込みが allow になるテストが無い。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R7 | 独立-3 | low | no | inherited | doc-claim | accepted | `collect_line_break_violations()` の docstring が `str.splitlines()` で割る前提のまま。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R8 | 独立-3 | advisory | no | self-inflicted | product | accepted | 新しい早期 deny の本文が、steering 外への書き込みにも「steering への書き込み」と言う。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R9 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | `_origin_session_new_values()` の docstring から行ごと消す Edit の名指しが抜け、正本として指す側と合わない。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R10 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | 既存値のある state.md を消して同じ値で作り直す形を止めることを固定するテストが無い。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R11 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実データの比較にコマンドと sha が無い。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R12 | 独立-3 | advisory | no | inherited | doc-claim | accepted | fence はどの切り方でも追加行だけで判定し、既存の行との組み合わせを見ないことが限界に無い。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
| R13 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | review-log の commit の件名に巡の ID が入り、欄の外から経緯が届いた。履歴は書き換えない。follow_up_of のある PR の 2 巡目以降の low・advisory なので直さず、PR 本文に書く |
