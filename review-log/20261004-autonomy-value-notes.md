---
lane: L1+
pr: 348
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable (general-purpose, model: fable、信号 ①: main の deny 案と Opus の案が食い違った) | - | 0 | 0 | 0 | 2026-10-04T00:40+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 350f18027b3c3adc8f5bafc94e9746dff7f1c574 | 0 | 4 | 0 | 2026-10-04T01:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 699ea0c0ca3243c9ddc81abd92d17825b20d72a1 | 0 | 0 | 0 | 2026-10-04T02:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | fixed | Opus: deny は足さない。注記の警告は systemMessage だけで main に届かず、書き込み前の内容を読む。deny は注記（範囲を狭める条件）を消す方向に誘導する。書き込み後の全文を state.md だけで読み、additionalContext で返す commit: なし（方針） |
| M2 | 方針メモ | advisory | no | inherited | none | fixed | Fable: Opus の案に賛成。旧文面「値は基底だけに」を置き換え、判別できないときは PR 作成まで に倒す。additionalContext は書き込みの後に届くので直すのは次の書き込み（限界）。マージ後に完全一致の件数と自走のマージの記録を数える commit: なし（方針） |
| R1 | 独立-1 | medium | no | self-inflicted | product | fixed | 読み手が退ける形（非正規の行の形・全角コロン・human: の後の空白・行が 2 行）で黙る。入口の形を許可リストで見て、欠けた条件を返すようにした commit: 699ea0c0 |
| R2 | 独立-1 | medium | no | self-inflicted | product | fixed | fence の判定を 2 つ目の実装として作り、4 連の fence と ~~~ で内外を取り違える。tasklist_parse.strip_fenced_blocks を使うようにした commit: 699ea0c0 |
| R3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 範囲を狭める注記の扱いが human-check-template.md の自走上限の置換値の節（別の行に書く）と食い違う。PR 作成まで にする規定に揃えた commit: 699ea0c0 |
| R4 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | main に human: の evidence を書き直させる案内が、evidence を本人のターンの外で書き換えない規定と食い違う。直すのはこの記録の続きの書き込みだけ、後から見つけた記録は書き換えない、と文面を直した（指摘の gate-status-schema.md:24 の規定は変えず、案内の側の autonomy_value.py を規定に合わせた） commit: 699ea0c0 |
| R5 | 独立-1 | low | no | self-inflicted | product | fixed | ApplyPatch では lint の警告も新しい注記も消える。lint の human-evidence を外すのを Write・Edit・MultiEdit に限り、事前回答の節に自分で確かめる文を戻した commit: 699ea0c0 |
| R6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | old_string が見つからない Edit は書き込み前の全文で注記を出すのに、テストと限界は出さないと書いている。テストを書き込み前の内容で知らせる形にした commit: 699ea0c0 |
| R7 | 独立-1 | low | no | self-inflicted | product | fixed | 行を消すだけの Edit で注記を計算しない。早期の allow でも返すようにした（size の空 chunk と降格の経路は限界） commit: 699ea0c0 |
| R8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 例外のテストの deny が無いことの assert が stdout だけを見て常に真。stderr が空で allow の応答であることを見るようにした commit: 699ea0c0 |
| R9 | 独立-1 | low | no | self-inflicted | test-power | fixed | 既存の hook 入口のテストが additionalContext を見ていない。空であることを足した commit: 699ea0c0 |
| R10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 不一致の注記が、自走上限の行が 2 行以上でも なし と言う。行数の注記を分け、不一致は 1 行のときだけにした commit: 699ea0c0 |
| R11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 未リリースの断片の古い記述を置き換えると書いていない。断片に置き換える 2 か所を書いた commit: 699ea0c0 |
| R12 | 独立-1 | advisory | no | self-inflicted | product | fixed | additionalContext にほかの書き手が書いた値をそのまま載せる。80 文字で切った commit: 699ea0c0 |
| R13 | 独立-1 | advisory | no | self-inflicted | style | fixed | allow_response の置き場所が module の説明と合わない。docstring に足した commit: 699ea0c0 |
| S1 | 独立-2 | medium | no | self-inflicted | product | next-pr | 書き込みが自走上限の行に触れなくても、書き込みのたびに同じ長い注記を返す。書き換えないよう案内した記録にも返り続ける。行の値と形が変わったときだけ返す |
| S2 | 独立-2 | low | no | self-inflicted | product | next-pr | _LINE の先頭グループが `**` を 2 通りに読み、`*` が長く続く行で後戻りが指数的に増え、hook の中で最大 10 秒止まりうる |
| S3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 注記の移し先が、文面では `事前回答:` の行、template では worklog.md と食い違う |
| S4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 断片の「ApplyPatch ではこれまでどおり」と置き換えの一覧が、merge 値で始まるときだけ見る lint の挙動と合わない |
| S5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | test_pre_answer_contract の docstring と lint の help が、merge 値で始まるときだけ・Write/Edit/MultiEdit のときだけ、を書いていない |
| S6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | template の「hook が見ない書き込み〔ApplyPatch・Bash〕」が、ApplyPatch で systemMessage を出す実装と違う |
| S7 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 形のテストが何か返ることしか見ず、注記の部分一致もほかの文面に当たる |
| S8 | 独立-2 | low | no | self-inflicted | test-power | next-pr | PROJECTABLE_TOOLS から Write か MultiEdit を外しても落ちるテストが無い |
| S9 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 早期 allow の経路は例外への備えが notes_for_write の中の 1 層だけで、テストも無い |
| S10 | 独立-2 | low | no | inherited | product | next-pr | state.md の判定が大文字小文字を区別し、hook のほかの判定と違う |
| S11 | 独立-2 | low | no | inherited | doc-claim | next-pr | docs/SECURITY.md の hook の表に、state.md の値を引用する additionalContext の出力が無い |
| S12 | 独立-2 | low | no | self-inflicted | style | next-pr | 1,500 行を超えたファイルの行数を差分巡で増やし、tool の集合を project_written_text と二重に持つ |
| S13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | テストの docstring「old_string が見つからない Edit は書き込まれない」が、ツールの照合で当たる場合を無視している |
| S14 | 独立-2 | advisory | no | self-inflicted | product | accepted | 閉じていないコードフェンスの扱いを、読み手の正本（post-merge-qa § 入口）が決めていない |
| S15 | 独立-2 | advisory | no | inherited | product | accepted | _LINE がラベルと括弧の間の空白などを数えず、読み手と数え方がずれる場合がある |
