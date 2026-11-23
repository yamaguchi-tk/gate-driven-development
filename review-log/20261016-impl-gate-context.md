---
lane: L1
pr: 534
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1a577e49 | 0 | 7 | 0 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b58903bf | 0 | 1 | 0 | 2026-10-16 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 16b883e2 | 0 | 1 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | section-heading | fixed | script が節の見出しを完全一致で読み、done guard が同じ節と読む `## Pending Tasks（再オープン）` などを黙って落とす。前方一致にして一致した節を全部出し、task 名を open_task_names と突き合わせた。commit: b58903bf |
| F2 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | ユーザー確認済み（推奨のまま）: 依頼は節の見出しの判定に tasklist_parse を使うとしたが、公開の関数が無い。done guard と同じ前方一致を script に置き、open_task_names の検算で縛る案で進めた |
| F3 | 独立-1 | medium | no | self-inflicted | wrong-path | accepted | ユーザー確認済み（推奨のまま）: learned-patterns.md を steering 直下で探し、書く側の docs/ と違う。docs/ に揃えた直し（b58903bf）が依頼の「変えないもの」（Step 5 の入力）を変えたため 16b883e2 で戻し、置き場の揃えは関係する 6 箇所をまとめる次の PR にする案で進めている |
| F4 | 独立-1 | medium | no | self-inflicted | missing-section | fixed | Agentic Worker Header・Execution Plan を出さないのに、範囲だけを読む規定だった。全節の索引・冒頭・Execution Plan を出し、state.md・worklog.md の Edit 前の Read を規定の外にした。commit: b58903bf |
| F5 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼の必須の節 3 つのうち Implementation Reviewer Selection を任意にしていた。必須に戻した。commit: b58903bf |
| F6 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼のテスト（実データ形の見出し・was_valid=false だけ）が無かった。task 行の 3 形・節見出しの接尾辞・再オープンの節の fixture を足した。commit: b58903bf |
| F7 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | PR 本文の測り方に、動いてはいけない 3 つの指標が無かった。commit: なし（PR 本文） |
| F8 | 独立-1 | low | no | self-inflicted | request-drift | fixed | Calibration の entry を was_valid によらず全部出していた。was_valid: false の entry だけにした。commit: b58903bf |
| F9 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 前回の gate の出力から判定の行を出していなかった。fence の外の見出しと判定の行を出す。commit: b58903bf |
| F10 | 独立-1 | low | no | self-inflicted | fence | accepted | Refactor Gate Status を含む行と Completed Tasks の calibration・task 行を、fence の内外を見ずに出す |
| F11 | 独立-1 | low | no | self-inflicted | missing-writer | accepted | State Machine Impact を handoff/ に書く側が定まっておらず、script はほぼ常に「block が無い」と出す。最新のファイルを採る方式は別の task の block を拾いうる |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が「gate の判定は変えていない」と書くが入力の読み方は変わる。書き分けた。commit: b58903bf |
| F13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Template の State Update Contract 3 が tasklist の re-read のまま残る |
| F14 | 独立-1 | low | no | self-inflicted | exit-code | accepted | SKILL.md は exit 1 の扱いしか書かず、exit 2・127 の扱いが無い |
| F15 | 独立-1 | low | no | self-inflicted | stale-range | accepted | tasklist.md を書き換えた後に古い行番号の範囲を Read しうる |
| F16 | 独立-1 | low | no | self-inflicted | ordering | accepted | Phase Gate Pre-check が script より前に tasklist.md を読む |
| F17 | 独立-1 | low | no | self-inflicted | line-break | accepted | splitlines が LF 以外の 8 文字でも行を分け、行番号が Read とずれうる |
| F18 | 独立-1 | low | no | self-inflicted | test-power | accepted | 任意の節が無いとき・handoff の新しい方の選択・handoff/ が無いときを固定するテストが無い |
| F19 | 独立-1 | low | no | self-inflicted | test-power | fixed | SKILL.md の文字列の有無だけを見るテストだった。SKILL.md が名指す script を抜き出して実在を見る形にした。commit: b58903bf |
| F20 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring と PR 本文で tasklist.md の行数の上限が食い違っていた。commit: b58903bf |
| F21 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が出す節を実物より広く書いていた。実物どおりに書き直した。commit: b58903bf |
| A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文に Skill RED-GREEN Evidence があるかを確かめられない。PR 本文に載せる。commit: なし（PR 本文） |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | SKILL.md の段落の一覧に前回の gate の出力の見出しが無かった。commit: b58903bf |
| A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に Step 2 の書き換え・exit 2・節が無いときの出力が無かった。commit: なし（PR 本文） |
| F22 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | Step 5 の cross-task の読み先を docs/ に替え、依頼に無い形で severity の降格を有効にしうる。Step 5 の本文を base に戻し、script も Step 5 と同じ置き場を読む。commit: 16b883e2 |
| F23 | 独立-2 | low | no | self-inflicted | request-drift | fixed | PR 本文が依頼の「節の見出しの判定は tasklist_parse」を黙って言い換えた。限界に、節の判定は script 内の前方一致で、lib との突き合わせは Current Task・Pending Tasks だけと書く。commit: なし（PR 本文） |
| F24 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | _check_open_tasks は今の lib と同じ規則で必ず一致し、「食い違い 0 件」は証拠にならない。docstring は言い過ぎ（PR 本文の 0 件の記述は直す） |
| F25 | 独立-2 | low | no | inherited | fence | re-reported | Refactor Gate Status を含む行と Completed Tasks の出力が fence の中と字下げした行を除かない（F10 の再掲） |
| F26 | 独立-2 | low | no | self-inflicted | calibration-regex | accepted | was_valid: false の判定が書き方を並べた正規表現で、外れた書き方は印なしで落ちる |
| F27 | 独立-2 | low | no | self-inflicted | stale-range | re-reported | runner 自身の Edit の後に出力の行番号が古くなる（F15 の再掲） |
| F28 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | テストの docstring の必須の節が 2 つのまま |
| F29 | 独立-2 | low | no | inherited | wrong-path | accepted | learned-patterns.md の置き場の規定が別のファイルで古い（subagent-driven-implementation SKILL.md:72,218、collect-gdd-telemetry.py:312、SECURITY.md:52,92、cross-task-learning.md） |
| A4 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が材料から確かめられない。PR 本文に載せる。commit: なし（PR 本文） |
| A5 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 限界の「159 件で 152 件」に母集団と再現のコマンドが無い。commit: なし（PR 本文） |
| A6 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 再オープンのテストの 2 つ目の assert が索引の行だけで通る |
| A7 | 独立-2 | advisory | no | self-inflicted | wrong-path | accepted | _learned の置き場を resolve() で決めている（16b883e2 で resolve を使わなくなった） |
| A8 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 中身が空の Rejected Alternatives 節を「節が無い」と出す |
| A9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | script の docstring の Exit code 1 の説明が実際より狭い |
| A10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | SKILL の段落と変更断片では Refactor Gate Status が「節」としか書かれていない |
| F30 | 独立-3 | medium | no | self-inflicted | wrong-path | accepted | ユーザー確認済み（推奨のまま）: script と Step 5 が読む <Steering Dir>/learned-patterns.md には誰も書かず、Cross-task calibration の入力は空のまま（main と同じ）。docs/ に揃えると Step 5 の入力が変わる。置き場の揃えを次の PR にする案で進めている（F3 と同じ問い） |
| F31 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文と断片が「Step 5 と同じ置き場」とだけ書き、書く側とずれて入力が空になることを書いていない。「steering 直下」が 2 通りに読める。PR 本文の限界と断片を直した（script の docstring は直していない）。断片は commit: 1d02a594 |
| F32 | 独立-3 | low | no | inherited | wrong-path | accepted | collect-gdd-telemetry.py:312 が別の置き場（.steering/ 直下）を読み、読み先が 3 通りになった |
| F33 | 独立-3 | low | no | inherited | doc-claim | accepted | subagent-driven-implementation SKILL.md:72,218 と :180、SECURITY.md:52 と :258 で置き場が 2 通りに書かれている |
