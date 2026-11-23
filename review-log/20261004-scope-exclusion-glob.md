---
lane: L1
pr: 345
follow_up_of: 325
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1f2af811465c81751f671f66bb3d16af623ef208 | 0 | 1 | 0 | 2026-10-04T01:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | e9ee7483df084ea6073158953484cce958ff2c09 | 0 | 2 | 0 | 2026-10-04T02:10+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | ba5f83ecdfbc4178899ec73ef6cc196d54d7be3f | 0 | 1 | 0 | 2026-10-04T03:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | product | fixed | 英語の除外（`** except src/legacy/**`）・先頭の `-` の語は SCOPE_WORD_RE に合い、検査した自走範囲に数えられて INFO が消える。各語を is_glob_shape にも通す commit: 6f82c3f4 |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | rollback-patterns の INFO の条件に、欄名つきの行の下の箇条を数えないことが無い commit: 58228e0c |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `read_state_patterns` とモジュールの docstring が、数えない集合と INFO の条件を古いまま書いている commit: 6f82c3f4 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片に、未リリースの断片の INFO の規則を置き換えた注記が無い commit: 58228e0c |
| F5 | 独立-1 | low | no | self-inflicted | product | fixed | `・`・`;`・縦棒・`／` で区切った glob の行で新しく INFO が出る（見出しの形と区切りが違う）。区切りをそろえた commit: 6f82c3f4 |
| F6 | 独立-1 | low | no | inherited | product | fixed | colon の形の語の区切りが `・` などで分けず、glob とつないだ単一ファイルが ERROR にならない commit: 6f82c3f4 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 正の欄名の下の箇条・glob の欄名の表記ゆれでも INFO が出ることが User Action Required に無い commit: 58228e0c |
| F8 | 独立-1 | low | no | inherited | product | fixed | 見出しの形は glob の欄の `!src/legacy/**` を glob の形として受け付ける（colon の形と非対称） commit: 6f82c3f4 |
| F9 | 独立-1 | low | no | self-inflicted | product | fixed | `label_indent` が節の始まりで戻らず、2 つ目の節の glob だけの行が数えられない commit: 6f82c3f4 |
| F10 | 独立-1 | low | no | self-inflicted | test-power | fixed | `* src/d/**` のケースが箇条の記号を外す処理を固定していない。F1 の修正で 1 文字の `*` が glob の形でなくなり固定される commit: 6f82c3f4 |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 「先頭の `!`」の書き方が、数えない語の集合より狭い commit: 58228e0c |
| F12 | 独立-1 | advisory | no | inherited | product | accepted | `CONTINUATION_LABEL_RE` が長い空白の行で 2 乗の時間がかかりうる（未実測。意図的に作らないと出ない形） |
| F13 | 独立-2 | medium | no | self-inflicted | test-power | fixed | 見出しの形で、`@`・括弧・`+`・全角の文字を含む正当なパス（`app/(auth)/**`）があると欄を読まず、同じ欄の単一ファイルの ERROR も出なくなる。ユーザーの指示で直した。見出しの形は `!`・`-` で始まる語だけを読まない語に足す commit: 4a1ea208 |
| F14 | 独立-2 | medium | no | self-inflicted | test-power | fixed | 先頭の `-` の規則と ASCII の括弧の規則を判別するテストが無い（`**` が glob の形でないことで INFO が出ている）。ユーザーの指示で直した。`src/**, -src/legacy/**`・`(src/legacy/**)` のテストを足した commit: d1ebc98e |
| F15 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | rollback-patterns の見出しの形の定義に文字の条件が無く、`!src/legacy/**` の例と食い違う |
| F16 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | Step 3c とモジュールの docstring の、欄を読まない条件の定義が古い |
| F17 | 独立-2 | low | no | self-inflicted | style | accepted | `WARN: glob field not read: non-glob words` の文言が、glob の形の語（`!src/legacy/**`）にも出る |
| F18 | 独立-2 | low | no | self-inflicted | test-power | accepted | 区切りが増えたので、`戻し条件: src/foo・main.go` が 1 語の ERROR から exit=0 に変わる |
| F19 | 独立-2 | low | no | self-inflicted | product | accepted | 番号つきの箇条・チェックボックスの箇条の glob は数えられず INFO が出る |
| F20 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 欄名つきの行と同じ字下げで続く箇条は数える。断片と正本の「下の箇条」はコードより広い |
| F21 | 独立-2 | low | no | inherited | test-power | accepted | 数える行が 1 行でもあれば、同じ節のほかの行の自由文（`リポジトリ全体`）は検査しない（見出しの形と非対称） |
| F22 | 独立-2 | low | no | inherited | product | out-of-diff | `**` だけの語は is_glob_shape で glob にならず、全域 glob の INFO に届かない |
| F23 | 独立-2 | low | no | inherited | test-power | accepted | 区切りの集合に全角の `；`・`｜` と空白なしの日本語の接続が無い |
| F24 | 独立-2 | low | no | inherited | doc-claim | accepted | rollback-patterns の「INFO で exit=0」は、数えない glob の単一ファイルで exit=1 になる場合を書いていない |
| F25 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「WARN と INFO を出す」は、`--quiet` で INFO が出ないことを書いていない |
| F26 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 断片に、未リリースの `20261003-glob-field-free-text` の条件を置き換えた注記が無い |
| F27 | 独立-2 | low | no | self-inflicted | test-power | accepted | 区切りのテストが `・` だけで、`;`・縦棒・`／` を token の区切りとして固定していない |
| F28 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | exit を変える入力があるので L1+ に当たる可能性（block しない advisory の lint なので L1 のまま） |
| F29 | 独立-3 | medium | no | self-inflicted | test-power | accepted | 見出しの形で、除外の言い方を空白なしで glob につないだ語（`リポジトリ全体（src/legacy/**を除く）`）を glob として数え、WARN・INFO が出ない（main と同じ挙動。colon の形では INFO が出る） |
| F30 | 独立-3 | low | no | inherited | test-power | accepted | 見出しの形で `!`・`-` の語が 1 つあると、同じ欄の単一ファイルの ERROR が出ない（WARN は出る） |
| F31 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | Step 3c の欄を読まない条件に `!`・`-` が無い |
| F32 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変えた行の直上のコメントと、モジュールの docstring・`SCOPE_WORD_RE`・`is_scope_word` の説明が、見出しの形の判定と合わない |
| F33 | 独立-3 | low | no | self-inflicted | style | accepted | WARN の文言が `!`・`-` の語を `non-glob words` と言い、除外の書き先を示さない |
| F34 | 独立-3 | low | no | self-inflicted | test-power | accepted | 先頭 `-` の見出しの形のテストが、欄を読まないこと（抽出が空・INFO）を固定していない |
| F35 | 独立-3 | advisory | no | inherited | doc-claim | accepted | colon の形では、記号・全角の文字を含む正当なパスだけの行でも INFO が出ることが限界に無い |
