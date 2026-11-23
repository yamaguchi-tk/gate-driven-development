---
lane: L1+
pr: 305
follow_up_of: 286
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#286 の限界に書いた次の PR。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた。Opus は「要る・小さく閉じる」とし、除外節の状態を fence の外の行だけで更新すること、transcript の Edit での新旧の判定差の測定、緩む方向の変化と chunk 単位の誤対応を限界に書くことを足すよう推した。main の案と食い違わず、Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-02T15:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8f13ffe61c2f56a10c4e691aedc41eca82df0b68 | 1 | 0 | 1 | 2026-10-02T16:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 8765d99c68158d5d057f08f2e3392ba8bf230c35 | 2 | 0 | 2 | 2026-10-02T17:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 06626d722bb53d4e7744d320b85d36028a0301f5 | 1 | 1 | 1 | 2026-10-02T18:00+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user（安全策 4 の発火〔high を含む巡が 3 回、クラスタ patch-line-set の high が独立-2・独立-3 の 2 巡〕。Opus は「止める」を推し〔独立-3 の high は pre-existing・実データ 0 件・parser の統一は別の課題〕、信号 ② で呼んだ Fable も賛成し、2 つの parser の受理集合の食い違い 3 つを次の PR の範囲にするよう補った。ユーザーが「止める」を選んだ。以後の指摘は直さず限界に書く） | - | 0 | 0 | 0 | 2026-10-02T18:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| L1 | 独立-1 | high | yes | inherited | fail-open | fixed | `#### Attempts`・`#### 試行記録` の見出し行が全部の検出器を飛ばし、secret marker・値・ID を通す。見出し行も検出器にかける commit: 11fb531a |
| L2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 緩む方向の変化（閉じの条件を満たさない行・fence の中の `#` で節が終わらない）が限界と断片に無い commit: 11fb531a |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「CommonMark どおり」は閉じ忘れ・インデントで実装と違う。`_scan_fences` の規則と書く commit: 11fb531a |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 区切り行を検査するようになった変化が断片に無い commit: 11fb531a |
| L5 | 独立-1 | low | no | self-inflicted | test-power | fixed | deny のテストが exit だけを見て、内部エラーの exit 2 と区別できない commit: bd1a8dd1 |
| L6 | 独立-1 | low | no | self-inflicted | test-power | fixed | 区切り行を検査することを固定するテストが無い commit: bd1a8dd1 |
| L7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | common-guardrails.md の除外の記述が古い commit: 11fb531a |
| L8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | fence 走査の正本を述べるコメントが 2 か所で食い違う commit: 11fb531a |
| L9 | 独立-1 | advisory | no | inherited | test-power | accepted | 単一正本の契約テストが `_scan_fences(` の呼び出しを見ていない。PR 本文に列挙 |
| L10 | 独立-1 | advisory | no | inherited | doc-claim | accepted | SECURITY.md に、fence の中では値・ID・placeholder を検査しないことが無い。PR 本文に列挙 |
| L11 | 独立-1 | low | no | inherited | product | fixed | ApplyPatch で別ファイルの ``` と対になり、値が fence の中として免除される。ファイルごとの追加行でも検査する commit: 11fb531a |
| L12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 実データの件数に、測ったコマンドと材料の範囲が無い。PR 本文に書く |
| L13 | 独立-1 | advisory | no | self-inflicted | product | accepted | 閉じていない fence で deny したとき、本文に原因の手がかりが無い。PR 本文に列挙 |
| L14 | 独立-1 | low | no | self-inflicted | style | fixed | 1500 行を超えたファイルの行数が増えた。コメントを縮めて 1708 行に戻す commit: 11fb531a |
| L15 | 独立-1 | advisory | no | inherited | style | accepted | `startswith(("#", "##", ...))` は `startswith("#")` と同じ。PR 本文に列挙 |
| L16 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの値をリテラルで置くと外部の secret scanning が拾うおそれ。PR 本文に列挙 |
| L17 | 独立-1 | advisory | no | inherited | style | accepted | import の `strip_fenced_blocks` を使っていない。PR 本文に列挙 |
| L18 | 独立-1 | low | no | self-inflicted | test-power | fixed | info_with_backtick の入力が info に ` を含まず、規則を固定していない commit: bd1a8dd1 |
| M1 | 独立-2 | high | yes | self-inflicted | patch-line-set | fixed | ファイルごとの追加行が `+++` で始まる行を落とし、ファイルをまたぐ fence の免除が残る。section の `+` 行を全部積む 1 パスの builder にする commit: 048bd0d0 |
| M2 | 独立-2 | high | yes | inherited | patch-line-set | fixed | 内容が `++ ` で始まる patch の追加行がどの chunk にも入らず、全部の検出器を素通りする。ファイルごとの追加行を chunk の有無に関係なく検査する commit: 048bd0d0 |
| M3 | 独立-2 | low | no | self-inflicted | product | fixed | ファイルごとの追加行が section ごとに patch を読み直し、計算量が section 数 × 行数になる。1 パスにする commit: 048bd0d0 |
| M4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 閉じていない開き行の値を検査することを固定するテストが無い。PR 本文の限界に書く |
| M5 | 独立-2 | low | no | self-inflicted | style | accepted | `_advance_section_state` の読み飛ばしの戻り値が常に False。PR 本文の限界に書く |
| M6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「すべての検査」は Attempts 節の中では placeholder・省略記号を除く。PR 本文の限界に書く |
| M7 | 独立-2 | low | no | inherited | doc-claim | accepted | common-guardrails の除外の行に `#### 試行記録` が無い。PR 本文の限界に書く |
| M8 | 独立-2 | low | no | inherited | doc-claim | accepted | `extract_added_lines` の docstring の前提が古い。PR 本文の限界に書く |
| M9 | 独立-2 | low | no | inherited | doc-claim | accepted | secret_scanning.py のコメントの除外の規定が実装と合わない。PR 本文の限界に書く |
| M10 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | Write の空の content のケースを消した。PR 本文に列挙 |
| M11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 実測の母集団に ApplyPatch が無く、測ったコードの sha も無い。PR 本文に書く |
| M12 | 独立-2 | advisory | no | inherited | product | accepted | 閉じた fence の開き行の info は値・ID の検査を免除される。PR 本文の限界に書く |
| M13 | 独立-2 | advisory | no | inherited | doc-claim | accepted | SECURITY.md の deny の一覧に fence の中の免除が無い。PR 本文に列挙 |
| M14 | 独立-2 | advisory | no | inherited | style | accepted | テストが PATH の python3 を起動する。PR 本文に列挙 |
| N1 | 独立-3 | high | yes | inherited | patch-line-set | accepted | `parse_patch_sections()` が `*** End of File` で section を閉じ、その後ろの hunk の Origin Session の書き換え・削除を見ない。HITL で「止める」を選び、限界の先頭に書く |
| N2 | 独立-3 | medium | no | self-inflicted | test-power | accepted | `*** End of File` の後ろの行をファイルごとの chunk に入れる挙動を固定するテストが無い。HITL で「止める」を選び、PR 本文の限界に書く |
| N3 | 独立-3 | low | no | self-inflicted | test-power | accepted | 計算量が行数に比例することを固定するテストが無い。HITL で「止める」を選び、PR 本文の限界に書く |
| N4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | `+++` で始まる追加行の新しい deny が断片に無い。HITL で「止める」を選び、PR 本文の限界に書く |
| N5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | docstring の「file header でだけ切り替え」が Move to と合わない。HITL で「止める」を選び、PR 本文の限界に書く |
| N6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | section の切り方と `+++` 行の扱いの規定がモジュールの中で逆。HITL で「止める」を選び、PR 本文の限界に書く |
| N7 | 独立-3 | low | no | self-inflicted | product | accepted | `*** End Patch` の後ろの `+` 行が最後のファイルの chunk に入る。HITL で「止める」を選び、PR 本文の限界に書く |
| N8 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 実測が ApplyPatch の経路を含まない。HITL で「止める」を選び、PR 本文の限界に書く |
