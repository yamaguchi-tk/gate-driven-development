---
lane: L1+
pr: 355
follow_up_of: 323
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（旧#323 の限界の R1〜R3 を直す次の PR。ユーザーは、実データ 0 件でも直すことを選んだ。memory の 2026-09-28 の決定に従い、方針の確認は内部の相談で代えた。main の草案は、値の和に空値 "" を入れる案だった。Opus は試作で、この案には閉じない fail-open が 1 形〔Add で値を書いた後に Update で消す〕と新しい誤 deny が 3 形残ると示し、hunk を出現順に当てる値の層の仮想ファイルを推した〔Codex の lib.rs の順序を原典で確認〕。案が食い違ったので信号 ① で Fable を呼び、Fable は代案に賛成して、field に触れたかを値の無い行も含めて数えるよう補った。main は代案と補足を採った） | - | 0 | 0 | 0 | 2026-10-03T16:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a743255bdbb7897b20300dba5c6e75ed87a33a64 | 7 | 1 | 7 | 2026-10-03T17:00+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（独立-1 の high に閉じ方: 列挙 のものがあったので、直す前に振り分けを相談した。Opus は、S1・S6 を決められない値として止め、S3・S4 を連鎖した移動元を生のパスで読むことで閉じ、S5 は流れ込むファイルだけを通常のファイルとして読み、S9 は reader に合わせることを推した。S7・S8 は実データ 0 件の列挙で、次の PR に回すことを推した。main は推奨をそのまま採った。Fable は方針メモで 1 回使ったので呼ばない） | - | 0 | 0 | 0 | 2026-10-03T18:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c70e6a53badc58eb410d665ff54eeae79e0cdf06 | 6 | 0 | 6 | 2026-10-03T19:50+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus) + user（安全策 4 の発火: origin-final-state のクラスタの high が独立-1 と独立-2 の 2 回。Opus は部品を残し、この差分が入れた H1・H5 を直し、H2・H3 も決められない値の仕組みで閉じ、H4・H6 は事故では作られない列挙の形として限界に回すことを推した。試作で、7,851 件〔state.md 宛て 479 件〕の判定が tip と変わらないことを確かめた。main の案も同じで食い違いは無い。Fable はこの PR で使い切ったので呼ばない。ユーザーは C〔H1〜H3＋H5 を直す〕を選んだ） | - | 0 | 0 | 0 | 2026-10-03T20:40+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 5c1454a6a5e6929b786eab20106792eb94033add | 3 | 1 | 3 | 2026-10-03T22:10+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus) + user（安全策 4 の 2 回目の発火: high を含む巡が 3 回。3 件の high はどれも閉じ方: 列挙で、実データ 0 件〔transcript の patch 7,851 件、手元の state.md 203 本で fence・Origin の行 0〕。field の行に限ると、記号の後に空白を置く削除行は 0/1,141 本。Opus は 3 件を accepted にして限界の先頭に書き、この差分の退行 F4 だけを 1 行で直すことを推した〔Add の本文を Write の content として通した 11 ケースで判定の不一致 0〕。main の案も同じ。Fable はこの PR で使い切ったので呼ばない。ユーザーは B〔F4 だけ直す〕を選んだ） | - | 0 | 0 | 0 | 2026-10-04T10:00+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 23410d04e280e5e35b7c82cbb55b79606917d625 | 2 | 0 | 2 | 2026-10-04T11:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| S1 | 独立-1 | high | yes | self-inflicted | origin-final-state | fixed | 同じ patch の Delete・move で消えたファイルへの Update を空のファイルへの Update として当て、Delete→Update(+X) を通す。commit: 13ca8e98 |
| S2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | Delete→Update・Add→Delete のテストが exit code を見ず、deny を確かめていない。commit: a53196cd |
| S3 | 独立-1 | high | yes | self-inflicted | peer-turn-move | fixed | peer turn の記録の検査が直接の移動元しか読まず、連鎖した move で運ばれる承認の記録を見ない。commit: 13ca8e98 |
| S4 | 独立-1 | high | yes | self-inflicted | peer-turn-move | fixed | peer turn の検査は移動元を normalize_path 後のパスで読み、仮想ファイルは生のパスで読む。commit: 13ca8e98 |
| S5 | 独立-1 | high | yes | self-inflicted | guard-read | fixed | 仮想ファイルが patch 内の無関係なファイルまで FIFO の確認もサイズの上限もなく読み、hook の timeout で通る。commit: 13ca8e98 |
| S6 | 独立-1 | high | yes | inherited | origin-final-state | fixed | 前の hunk が消した値を後の hunk が消して足す、途中で当たらない patch を通す。commit: 13ca8e98 |
| S7 | 独立-1 | high | yes | inherited | fence-fragment | accepted | fence を書き込み後のファイルでなく hunk の +/- 行の断片で数え、fence の外に出る値を落とす。旧#323 の限界の残りで、実データで当たる形は 0 件（memory の 2026-10-02 の決定〔閉じ方: 列挙〕で方針メモ-2 の Opus に相談）。PR 本文の限界に書き、次の PR で直す |
| S8 | 独立-1 | high | yes | inherited | removal-fuzzy | accepted | 行頭の空白・Unicode のダッシュ・NBSP で書いた削除行を、値の削除として数えない。旧#323 の限界の残りで、実データで当たる形は 0 件（memory の 2026-10-02 の決定〔閉じ方: 列挙〕で方針メモ-2 の Opus に相談）。PR 本文の限界に書き、次の PR で直す |
| S9 | 独立-1 | low | no | self-inflicted | product | fixed | 値の無い行を数えるのが ApplyPatch だけで、Write・Edit と reader に合わない。commit: 13ca8e98 |
| S10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「Write・Edit の経路は変えない」と断片の「値の無い行も数える」が実装と合わない。commit: bb63f352 |
| S11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary が 3 つ目の patch も「削除を通していた」と書いている。commit: bb63f352 |
| S12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 消した関数を判定の担い手として名指す docstring が残っている。commit: 13ca8e98 |
| S13 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変えた関数の docstring が新しい挙動を書いていない。commit: 13ca8e98 |
| S14 | 独立-1 | low | no | self-inflicted | style | fixed | `patch_deletes_file()`・`patch_removed_lines()` が本番の呼び出し元を失った。commit: 13ca8e98 |
| S15 | 独立-1 | low | no | self-inflicted | test-power | fixed | `test_move_without_records_is_allowed` が何も判別しない。commit: a53196cd |
| S16 | 独立-1 | low | no | self-inflicted | test-power | fixed | peer turn の move の移動元の検査に、hook の入口から通すテストが無い。commit: a53196cd |
| S17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 実データの「判定が変わるものは 0 件」に再現手段と変えた経路の標本が無い。PR 本文に書く |
| TH1 | 独立-2 | high | yes | self-inflicted | origin-final-state | fixed | 値を決められない patch を、既存値が無く peer turn でもないと通す（move で A・B を運んだ後に消えた移動元を Update する patch）。commit: 13b50ca9 |
| TH2 | 独立-2 | high | yes | inherited | fence-fragment | fixed | hunk の +/- 行で fence を足して既存値を fence の中に隠す patch、閉じ fence を消して記入例の値を出す patch を、field に触れないとして通す。commit: 13b50ca9 |
| TH3 | 独立-2 | high | yes | inherited | origin-final-state | fixed | 同じ state.md を 2 つの節で Update し、後の節の context が前の節の結果に当たらず値の削除だけが残りうる patch を、値の上で当てて通す。commit: 13b50ca9 |
| TH4 | 独立-2 | high | yes | inherited | peer-turn-layer2 | accepted | peer turn の ApplyPatch に書き込み前後の値の比較が無く、pending の行を消して後ろの古い approved を出す patch を通す（main からの既知の限界。閉じ方: 列挙。事故では作られない形として、PR 本文の限界の先頭に書き、次の PR で直す） |
| TH5 | 独立-2 | high | yes | self-inflicted | guard-timeout | fixed | move の連鎖をたどる処理が target ごとに不動点ループで、敵対的に作った長い連鎖で hook の timeout に届く。commit: 13b50ca9 |
| TH6 | 独立-2 | high | yes | inherited | guard-read | accepted | 対象の state.md が FIFO だと既存値の読み込みで止まり、timeout で通る（main から。閉じ方: 列挙。事故では作られない形として、PR 本文の限界の先頭に書き、次の PR で直す） |
| TL1 | 独立-2 | low | no | self-inflicted | product | accepted | コロンの後が空白だけの `Origin Session: ` は空の値として数え、既存値の横に足すと止める（reader は読み飛ばす。止める側）。断片の記述は 0ac7f039 で実挙動に合わせた。PR 本文の限界に書く |
| TL2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | state_fields.py と test_state_field_value_less_line_contract.py の docstring が、空値行の数え方の実挙動と食い違う。PR 本文の限界に書く |
| TL3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | detect-steering.sh の peer turn の検査のコメントが、移動元の内容を見ることを書いていない。PR 本文の限界に書く |
| TL4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | peer turn の検査の docstring 層 1 に、移動元と読めない移動元の扱いが無い。commit: 13b50ca9 |
| TL5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | patch_inflow_sources の docstring の「出現順」が実装と合わない。commit: 13b50ca9 |
| TL6 | 独立-2 | low | no | self-inflicted | product | fixed | 読めない state.md に Origin に触れない Update を当てると、touched を決める前に決められないとして止める。commit: 13b50ca9 |
| TL7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の決められない条件に、Update の対象が読めないときが無い。commit: 0ac7f039 |
| TL8 | 独立-2 | low | no | self-inflicted | style | fixed | _origin_session_new_values の型注釈に UNDECIDABLE が無い。commit: 13b50ca9 |
| TL9 | 独立-2 | low | no | self-inflicted | test-power | fixed | FIFO の移動元のテストが決められない経路を固定せず、「読めない移動元」のテストの入力が存在しないファイル。commit: 89f37318 |
| TA1 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実データ比較に測った tip の sha が無く、母集団に move・Origin 行が 0 件で変えた経路への検出力が無い。PR 本文に書く |
| K3 | 方針メモ-3 | - | - | - | - | - | なし |
| U1 | 独立-3 | high | yes | self-inflicted | fence-fragment | accepted | 列挙: 削除行と追加行で field 行を既存の fence の内側へ入れ直す patch を、値の上は同じとして通す（書いた後は reader が読めない）。実データ 0 件。PR 本文の限界の先頭に書く |
| U2 | 独立-3 | high | yes | self-inflicted | removal-fuzzy | accepted | 列挙: Codex の緩い照合で当たる削除行（記号の後の空白、NBSP を前に置いた fence 行）で、field 行・閉じ fence を消す patch を通す（照合の規則は未確認）。実データ 0 件。PR 本文の限界の先頭に書く |
| U3 | 独立-3 | high | yes | self-inflicted | guard-timeout | accepted | 列挙: patch_inflow_sources を target ごとに呼ぶので、target が多い patch では全体で hunk の数の 2 乗になり、敵対的に作った patch で timeout に届く。docstring は 0e2c8d00 で実際に合わせた。PR 本文の限界の先頭に書く |
| U4 | 独立-3 | medium | no | self-inflicted | product | fixed | fence 行の規則が Add File にもかかり、fence を含む state.md の Add File を降格しない拒否で止める。commit: 0e2c8d00 |
| U5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文と断片の、決められない patch の規則の範囲が挙動と合わない。commit: 168c33b4 |
| U6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | collect_origin の docstring の許可する 3 形と references の要約に、ApplyPatch の決められないときの拒否が無い。PR 本文の限界に書く |
| U7 | 独立-3 | low | no | self-inflicted | test-power | fixed | 無い移動元のテストが既定 message で経路を固定しない。commit: 8fe7c479 |
| U8 | 独立-3 | low | no | self-inflicted | style | fixed | InflowSourcesTest が main ガードの後ろにある。commit: 8fe7c479 |
| U9 | 独立-3 | advisory | no | self-inflicted | style | fixed | `line[:1] in "+-"` が空行でも真になる。commit: 0e2c8d00 |
| U10 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実測に再実行できるコマンドが無い。PR 本文に書く |
| U11 | 独立-3 | advisory | no | inherited | bookkeeping | accepted | テンプレート外の記述あり（起動時の git status の commit 件名に対応と方針メモの経緯）。以後の commit の件名は変更の内容だけにする |
| K4 | 方針メモ-4 | - | - | - | - | - | なし |
| V1 | 独立-4 | high | yes | self-inflicted | fence-fragment | accepted | 列挙: Update の hunk で値の行を既存の fence の中へ動かす形（文脈行の fence、2 chunk、move）を、値の上は同じとして通す。方針メモ-4 でユーザーが選んだ B〔確かめの巡で high が出ても直さず限界に書く〕に従う。PR 本文の限界の先頭に書く |
| V2 | 独立-4 | high | yes | self-inflicted | guard-timeout | accepted | hook が 10 秒の timeout に届く入力（target の多い patch の 2 乗の走査、FIFO の state.md、上限の無い移動元の読み込み）で deny が出ない。どれも事故では作られない形。方針メモ-4 の B に従い、PR 本文の限界の先頭に書く |
| V3 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 断片の止める条件が、Add File・Delete File・move を常に触れたと数えるコードより狭い。commit: 5833da41 |
| V4 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 決められないときの理由文が、fence の条件を Update に限っていない。PR 本文の限界に書く |
| V5 | 独立-4 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Validation に、fence を含む Add File のテストが無い。commit: 5833da41 |
| V6 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | PR 本文の実データの文が壊れていて、比較の手段と変えた分岐の件数が無い。commit: なし（PR 本文） |
| V7 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | patch_inflow_sources の docstring の「hunk の数に比例」は実際は patch の行数に比例する。PR 本文に書く |
| V8 | 独立-4 | advisory | no | inherited | bookkeeping | accepted | テンプレート外の記述あり（起動時の git status の commit 件名）。以後の件名は変更の内容だけにする |
