---
lane: L1+
pr: 381
follow_up_of: 376
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（対象は 旧#376 の独立-2 で accepted にした P3〜P6。実測: queued の本文が list で tool_result block を含むものは 30 日の transcript で 0 件。main の草案は共有の _user_texts に flag を通す案だった。Opus は、queued の分岐で素の文字列と text block の許可リストに絞ってから渡し、type:user の経路を変えない案と、last_tool_result_text・all_tool_result_ids を変わらないものに足すこと、AC1 にも Stop hook の入口からのテストを置くことを推奨した。main はこれを採り、ユーザーが承認した。食い違いは残らないので max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-06T10:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 416691ff | 0 | 0 | 0 | 2026-10-06T11:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 37739d62 | 0 | 0 | 0 | 2026-10-06T11:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| A1 | 独立-1 | low | no | self-inflicted | 文言 | fixed | phase-progression.md:31 の「この行を読むのは steering write guard だけ」が、Stop hook が queued の本文を完了通知として読むことと食い違う。commit: 37739d62 |
| A2 | 独立-1 | low | no | self-inflicted | コード健全性 | fixed | 1500 行を超える validate-steering-write.py に docstring で 2 行足した。commit: 37739d62 |
| A3 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 変更断片の Validation で「Stop hook の入口から」が parse_transcript の単体テスト 2 本にも掛かって読める |
| A4 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 断片と抜粋が、queued の tool_result で dispatch_agent_ids・background_shell_ids も更新しなくなることを書いていない |
| A5 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | PR 本文の抜粋の「0 件」に数え方が書かれていない |
| A6 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | last_user_turn_is_peer の docstring の「既定では読まない」が、include_queued=True で本文も読むと取れる |
| B1 | 独立-2 | low | no | self-inflicted | 文言 | fixed | PR 本文の抜粋の「steering write guard だけが読む」が、Stop hook も queued の行を完了通知として読むことと食い違う。commit: なし（PR 本文） |
| B2 | 独立-2 | low | no | inherited | 文言 | accepted | transcript.py:412 と constants.py:191 が「queued の行にだけ残る」と断定し、ほかの記述の「残ることがある」と食い違う |
| B3 | 独立-2 | advisory | no | inherited | 信頼境界 | accepted | Stop hook は origin.kind=peer の queued の行の本文も完了通知として読み、steering write guard の扱いと非対称 |
| B4 | 独立-2 | advisory | no | self-inflicted | 文言 | accepted | 識別基準の段落で、queued の行に text prefix の fallback が効かないことが読み取りにくい |
