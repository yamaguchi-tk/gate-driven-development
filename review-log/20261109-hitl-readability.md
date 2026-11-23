---
lane: L1
pr: 651
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承 | d26d55bdb51d003d4ea2c1877060196dc4ae54a8 | 0 | 6 | 0 | 2026-11-09 |
| 方針メモ-1 | Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) | d26d55bdb51d003d4ea2c1877060196dc4ae54a8 | 0 | 0 | 0 | 2026-11-09 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承 | 8d0d151f59586e8fe58e6d242c522f9f85152232 | 0 | 5 | 0 | 2026-11-09 |
| 独立-3 | general-purpose, 全差分（無効化後）, model: opus, effort 継承 | 3f10b5b4c0f033936b9a1d422ea9c251581cf258 | 0 | 5 | 1 | 2026-11-09 |
| 独立-4 | general-purpose, 差分（無効化後）, model: opus, effort 継承 | aa5eedbf222b360d4aef445edfad170b0f1eb1d1 | 0 | 0 | 0 | 2026-11-09 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | product | accepted | 判断に関係ない節として書かなくしたのは条件付きの 3 節だけで、段階実装・ズレ確認などの必須の見出しは残る。相談役の答えが割れたので、推奨の (A) で進め、PR 本文で問う |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | T-n・Stage ID・ADR 番号が記号のまま残り、線引きが PR 本文に無い commit: 8d0d151f5 |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 規定 5 が ズレ確認の # の固定行と同時に守れない commit: 8d0d151f5 |
| I1-4 | 独立-1 | medium | no | self-inflicted | product | accepted | 規定 7 で推奨案に書き込んだ追加を requirements.md・design.md に反映する定めが無く、AC を変える追加の振り分けも無い |
| I1-5 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 全文を出し直す規定 7 と、gdd-dev.md:189 の変更した点のみ再提示が食い違う |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | human-check-template.md:54 の、推奨は選択肢を変えないという文が規定 7 と食い違う |
| I1-7 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 判断ポイントを指す 1 行にする変更が断片と PR 本文に無く、ルール 17 との優先も書いていない。PR 本文に書いた。断片とルール 17 は直していない commit: なし（PR 本文） |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | subagent-dispatch.md:51・:135 に表示前の置き換えの括弧が無い |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | human-check-template.md:401 の lint の説明が 該当なし の明記のまま |
| I1-10 | 独立-1 | low | no | self-inflicted | product | accepted | 相談役が割れたときと判断ポイントが無いときは、OK を閉じる 1 文が書けない |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 規定 2 の最初の 1〜2 文に、閉じる 1 文が入るのかが読めない |
| I1-12 | 独立-1 | low | no | self-inflicted | product | accepted | 単一案の理由の置き場が requirements-template.md に無く、単一 PR の理由は行き先なしで消える |
| I1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 専用 agent を呼べず、prompt の冒頭に定義を読む文を足した（代わりの経路） |
| I1-14 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | notes の Skill RED-GREEN Evidence が tip に無い。この記録と同じ commit で足した commit: なし（review-log） |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | accepted | Stage ID の規定が Stage Continuity Brief の雛形（:190）と :61・:135・:425 に食い違う |
| I2-2 | 独立-2 | medium | no | self-inflicted | product | accepted | compact に 段階実装案 の表が無く、Stage ID の定義場所が無い |
| I2-3 | 独立-2 | medium | no | self-inflicted | product | accepted | ズレ確認の # を残すのは依頼の範囲より狭い。数えるのは人か main で、読むコードは無い。PR 本文で問う |
| I2-4 | 独立-2 | medium | no | self-inflicted | product | accepted | 確定文面に別の ADR の番号があると、表示で読んだ文と承認して文書に入る文が違ってしまう。PR 本文の限界に書く |
| I2-5 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | PR 本文に T-n・ADR・Stage ID・# の挙動が無い commit: なし（PR 本文） |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の列挙に T-n・ADR・Stage ID・# の扱いが無い |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | lint-hitl-stage-plan.py は hook の配線の対象外で、Stage ID を残す根拠として強く読める |
| I2-8 | 独立-2 | low | no | self-inflicted | product | accepted | 置き換える記号が列挙のままで、列挙の外の記号は読み手の判定になる |
| I2-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 項目 2 の原文の材料に # が残る |
| I2-10 | 独立-2 | low | no | self-inflicted | product | accepted | 既存とぶつかる の質問を そのまま載せる 規定と置き換えが当たる |
| M1-1 | 方針メモ-1 | low | no | self-inflicted | product | accepted | 要約: I1-1 の扱い。Opus 2 本は必須の見出しも省く (B) を推した。Fable は (A)。main は変換表の実測 2/10 を確かめて (A) |
| I3-1 | 独立-3 | medium | yes | self-inflicted | approval-path | fixed | 設計: 変えない（記号の置き換えは要るので、人が文そのものを承認する確定文面だけを外す）。確定文面の文まで表示の前に置き換えると、人が見た文と文書に入る文が違う commit: aa5eedbf2 |
| I3-2 | 独立-3 | medium | no | self-inflicted | product | accepted | 推奨案に書き込んだ相談役の追加が requirements.md・design.md に届かない（I1-4 と同じ）。PR 本文の限界に書く |
| I3-3 | 独立-3 | medium | no | self-inflicted | product | accepted | 番号を指す 1 行にする規定を文字どおり読むと、自走の節の必須行と段階実装案の表が消える |
| I3-4 | 独立-3 | medium | no | self-inflicted | product | accepted | AC-n・Stage ID・タグも記号のまま残るのに、問いが # だけ。PR 本文の問いを広げる |
| I3-5 | 独立-3 | medium | no | self-inflicted | product | accepted | 当たらない回にも段階実装・ズレ確認の行が残る（I1-1 と同じ）。2/10 は変換表の根拠で段階実装の根拠ではない。PR 本文で問う |
| I3-6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | output-format.md:41 と lint の案内が、内部用語を括弧で補足するのまま |
| I3-7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 単一 PR の本文に 後続 PR の語があると lint-hitl-decision-quality.py が節を求める。手動実行のときだけ |
| I3-8 | 独立-3 | low | no | self-inflicted | product | accepted | 単一案の理由の置き場が requirements-template.md に無い（I1-12 と同じ） |
| I3-9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 必須ルール 1 の lint の説明が 該当なし の明記のまま（I1-9 と同じ） |
| I3-10 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 一次表示の原則 7 と判断の書き方 8 が食い違う（I1-6 と同じ）。判断ポイントの上限を超えるときの扱いも無い |
| I3-11 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary に規定 4 の変更が無い |
| I3-12 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の規定 7 は取り込みの後は 8 commit: なし（PR 本文） |
| I3-13 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文にテストの結果が無い commit: なし（PR 本文） |
| I3-14 | 独立-3 | advisory | no | self-inflicted | style | accepted | compact の条件の指示が <...> の置換の形と混ざる |
| I3-15 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | 抜粋に巡の ID と結果が入っていた |
| I4-1 | 独立-4 | low | no | self-inflicted | product | fixed | 確定文面の除外が PR 本文に無い commit: なし（PR 本文） |
| I4-2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | そのまま出し が表示の必須か、行数の目安との優先が読み切れない |
| I4-3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 断片に確定文面の除外が無い |
| I4-4 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | 抜粋に確認したことの節が入っていた |
| I4-5 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | 専用 agent を呼べず、prompt に定義を読む文を足した（代わりの経路） |
| I4-6 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | D-n#i は除外の対象に入っていない |
| I4-7 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 比較の場面は確定文面を含まない |
| I4-8 | 独立-4 | advisory | no | inherited | doc-claim | accepted | 表示した block と design.md の一致を確かめる仕組みが無い |
