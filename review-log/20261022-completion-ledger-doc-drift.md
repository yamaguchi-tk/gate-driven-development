---
lane: L1
pr: 563
follow_up_of: 559
amends: 20261021-completion-mechanical-ac-coverage.md, 20261021-completion-ledger-ac-glyph.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 94d4940b | 0 | 0 | 0 | 2026-10-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | f410bd28 | 0 | 0 | 0 | 2026-10-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L-1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 注記の置き場所「Ledger の節の次の `##` 見出しの節」の行き先が決まっておらず、続く節によって done guard や 2 つ目の Ledger の節に当たる。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 正本にした § Append-Only Rule の置ける行に空行が無く、SKILL.md の「すべて当たる」が言い過ぎになる。散文の要約の扱いも無い。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 旧#559 の断片で、AC の有無によらず読み飛ばしていた fence の行が「AC を含まない」の列挙に入っている。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 旧#559 の断片に、定義の無い「AC の字形」が残っている。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 旧#556 の断片の「（`ac-ledger`）だけを出す」が、同じ行の ac-source の記述と合わない。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | スクリプト先頭の説明の ac-source の場合に PR Boundary が無い。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-7 | 独立-1 | low | no | inherited | style | fixed | 同じ helper で gate に返すことを確かめるテスト 3 本が `_is_invalid` の名前のまま。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | 「表が終わる」のテストの assert が、見出しの形の行で表を閉じる分岐を消しても通る |
| L-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストのコメントの「日本語に続く ID」が入力（ID の後に日本語）と逆。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| L-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の種類 `依頼より狭い` が定義と合わず、巡の由来で書いている。commit: なし（PR 本文） |
| A-1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋の review-log の amends: の記述） |
| A-2 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋の、前の PR で受け入れた指摘の一覧） |
| A-3 | 独立-1 | advisory | no | self-inflicted | style | fixed | テストのコメントが縦棒の逃がしを Python の文字列の書き方（バックスラッシュ 2 つ）で書き、Ledger に書く形と違う。設計: 変えない（文書の言い回しのずれ）。commit: f410bd28 |
| M-1 | 独立-2 | low | no | self-inflicted | product | accepted | `## Ledger Notes` を Ledger の節の直後に置くと、ファイルの末尾に足した Ledger の行が節の外に入り、読まれずに前の verified が残る。閉じ方: 列挙（文書では閉じず、節の外の Ledger の形の行を判定するコードでだけ閉じる） |
| M-2 | 独立-2 | low | no | inherited | product | accepted | 履歴の圧縮の許可と、置いてしまった読めない行は消えないことのどちらが勝つかが書かれていない |
| M-3 | 独立-2 | low | no | inherited | doc-claim | accepted | `###` の Ledger の節の範囲が文書に無く、「直後」の解釈で `## Completed Tasks` の中に `##` を足すとタスクが節の外に出る |
| M-4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「見出しに `AC Trace Ledger` を含めると読まれる」は実装（`AC Trace Ledger` で始まる見出し）より広い |
| M-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 圧縮の規定と説明の PR Boundary が断片に書かれていない。PR 本文の置き場所の「だけ」が散文の要約の置き場所と合わない（PR 本文は直す） |
| M-6 | 独立-2 | low | no | inherited | bookkeeping | accepted | この PR の断片の、未リリースの断片を直したという行は利用者から見えない変更 |
| M-7 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 旧#559 の断片の「これまで読み飛ばしていた」は未リリースの状態を指す |
| M-8 | 独立-2 | low | no | inherited | doc-claim | accepted | subagent-dispatch.md の (4a) と 旧#556 の断片の ac-source の条件が、正本（PR Boundary・Plan の行の欄の数）より狭い |
| M-9 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 文書が決めた注記の置き場所で ok になることを固定するテストが無い |
| M-10 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「lint-ac の文法（ASCII・大文字）」が、Unicode の数字にも当たる実装と合わない。commit: なし（PR 本文） |
