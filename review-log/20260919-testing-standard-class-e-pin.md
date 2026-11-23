---
lane: L1
pr: 152
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1f3e3005e150310f8299c97434439b943fba6ca2 | 0 | 1 | 0 | 2026-09-19T21:10+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#152 review) | c5d236f7def98532488c899bd567a562f27efca3 | 0 | 2 | 0 | 2026-09-20T00:15+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 35ec3623d9a9b11126583bba8314f16fb9dd17ce | 0 | 1 | 0 | 2026-09-20T00:15+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | de058e71bcdde4b3ec334110244229410f9af801 | 0 | 1 | 0 | 2026-09-20T01:12+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | pr-body-claim | fixed | 「E のテストに削除を求めなくなる」の断定に証拠が無い（1c Skill RED-GREEN Evidence が未提出）。PR 本文に変更前後の pressure scenario を足した（commit なし） |
| L1 | 独立-1 | low | no | self-inflicted | testing-standard-test-power | accepted | 参照側の語の不在の検査は、別の言葉での写しを検出しない |
| A1 | 独立-1 | advisory | no | self-inflicted | pr-body-claim | accepted | TDD・inline checklist は正本の全項目（引用要件を含む）で判定するようになり、E 以外では従来より厳しくなる向きが書かれていない |
| A2 | 独立-1 | advisory | no | self-inflicted | testing-standard-doc | accepted | 除外は「文言」の pin だけで、リテラル・配置の pin との境界と (a)〜(c) との優先順位が文書に無い |
| P1 | PR後-1 | medium | no | self-inflicted | testing-standard-test-power | fixed | 契約テストの後半が 6 ファイル全文の語の不在を見ており、正本の「語の存在で見るものは消す」に当たる。判定行だけを見る形に直した |
| P2 | PR後-1 | medium | no | self-inflicted | pr-body-claim | fixed | 断片の Summary の「削除を求めなくなる」が全称。行と動詞まで含めて見るテストに限る書き方に直し、Known Limitations に残差を写した |
| P3 | PR後-1 | low | no | self-inflicted | testing-standard-doc | fixed | クラス表 E の「行と動詞まで含めて」と除外文の「行アンカーと動詞まで」で用語がずれる。除外文をクラス表にそろえた |
| P4 | PR後-1 | advisory | no | self-inflicted | pr-body-claim | fixed | 断片の「再測定していない」と PR 本文の Skill RED-GREEN Evidence が食い違う。断片に合わせて書き直した |
| M2 | 独立-2 | medium | no | self-inflicted | testing-standard-rule-conflict | fixed | 除外を固定値 pin 全体に広げたため、runtime 文書を丸ごと写す全文一致のテストが「行と動詞まで含めて見る」に読まれると残る側に倒れる。正本の除外文に「節・文書を丸ごと写すものは E に含めず、固定値 pin として判定する」を足し、契約テストで固定した（ユーザーの指示） |
| L2 | 独立-2 | low | no | self-inflicted | testing-standard-test-power | accepted | 写しの検査が 4 ファイルの判定行だけになり、planning reviewer と design gating が検査から外れた |
| L3 | 独立-2 | low | no | self-inflicted | testing-standard-test-power | accepted | 新しいテストの docstring が、テスト自身が検出しない別の言葉での写しを根拠にしている |
| L4 | 独立-2 | low | no | inherited | pr-body-claim | accepted | 断片の利用者向けの変更の列挙に completion check が無い |
| A3 | 独立-2 | advisory | no | inherited | testing-standard-doc | accepted | TDD の判定行に mock の条件の言い換え（false confidence の括弧）が残り、正本の assert_called_once_with の例外が無い |
| N1 | 独立-3 | medium | no | self-inflicted | testing-standard-rule-conflict | deferred | 追加した除外文「丸ごと写すもの」に判別条件が無く、クラス表 E の行と除外文で E の定義が 2 か所に分かれる。行アンカー付きの assertion を多数並べたテストが、除外文では固定値 pin と読まれうる。PR 本文の後続候補に記載 |
| N2 | 独立-3 | low | no | self-inflicted | pr-body-claim | accepted | 断片の利用者向けの記述（:8）と Known Limitations の未再測定の範囲が、この差分の追加に追随していない |
| N3 | 独立-3 | advisory | no | self-inflicted | testing-standard-doc | accepted | 全文の写しと SHA 固定で判定が逆の向きのまま残る。テストのコメントの根拠は、向きが入れ替わっただけで成立しない |
