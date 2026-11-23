---
lane: L1
pr: 144
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 93bf25bf0a206316e496ed5caedb868a1a77917d | 0 | 1 | 0 | 2026-09-19T18:25+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#144 review) | 8d50539fdf15128527496964a072cb76182a9f90 | 0 | 1 | 0 | 2026-09-19T19:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | testing-standard-rule-conflict | deferred | クラス E（runtime が読む文書の行と動詞を見るテスト）が、同じ節の固定値 pin の規則では削除対象になる。参照側 3 か所が固定値 pin の条件を別の言葉で写し、受理集合が一致しない（旧#143） |
| L1 | 独立-1 | low | no | self-inflicted | testing-standard-wiring | accepted | Planned RED を書く task-breakdown が基準を参照せず、禁止された型の Planned RED が TDD で初めて落ちる |
| L2 | 独立-1 | low | no | self-inflicted | testing-standard-wiring | accepted | 継ぎ目（クラス A）の gap を見る項目が implementation reviewer にしか無く、impl gate の既定経路の inline checklist に無い |
| L3 | 独立-1 | low | no | self-inflicted | testing-standard-test-power | accepted | 契約テストが、動詞の入れ替えや行の Focus 外への移動では落ちない |
| L4 | 独立-1 | low | no | self-inflicted | testing-standard-doc | accepted | completion reviewer Focus 6 の削除と severity の規則が「網羅の要件ではない」一覧の中にある |
| L5 | 独立-1 | low | no | self-inflicted | fragment-policy | accepted | 変更断片の Validation 欄に件数と実測結果が入っている（CHANGELOG.md § Policy は PR 本文に書く決まり） |
| L6 | 独立-1 | low | no | self-inflicted | fragment-policy | accepted | 変更断片の中で「live file の SHA 凍結」と「本番ファイルの SHA 固定」の 2 つの呼び名が混在する |
| L7 | 独立-1 | low | no | self-inflicted | testing-standard-doc | accepted | 新しい契約テストの docstring 1 行目が根拠の PR 番号を引いていない（受入条件 1） |
| A1 | 独立-1 | advisory | no | self-inflicted | testing-standard-doc | accepted | 正本の「既存のテストなら消す」が限界「差分に入ったテストだけ」より広い。SHA 固定の 2 行が (1)(3) を両方欠く既存 pin で食い違う |
| A2 | 独立-1 | advisory | no | self-inflicted | testing-standard-doc | accepted | repo 固有基準の 3 つの探索先の優先順位・root 限定・節の見分け方が未定 |
| A3 | 独立-1 | advisory | no | self-inflicted | pr-body-claim | accepted | PR 本文の予算の値に at <sha> が無い |
| A4 | 独立-1 | advisory | no | self-inflicted | pr-body-claim | accepted | 1b の Superpowers Benchmark Summary と、1c の対象範囲が渡された範囲では判断できない（PR 本文に書く） |
| P1 | PR後-1 | medium | no | self-inflicted | testing-standard-rule-conflict | deferred | 独立-1 M1 と同じ（旧#143）。新規の指摘なし。SHA の条件の書き分けと契約テストの検出力は独立-1 の A1・L3 に合わせて Medium にしない |
