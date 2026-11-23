---
lane: L1+
pr: 332
follow_up_of: 315
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#315 の受け入れた限界を直すユーザーの指示について。main の案は G2・F2・F3・G1・F10 と文言を 1 PR にまとめ、F3 は書き込みの前だけ救済読みにするものだった。実測: `_record_existing_denies` の呼び出し元は `_emit_with_violations` だけ、size の counter は別経路。Opus は、F3 を前だけにすると閉じていない fence のある tasklist への書き込みが全部 deny される、G1 の件数の式は ok と not-ok の同名で閉じない、G2 は生の path でなく `_state_key` で畳む、旧#315 で安全策 4 が発火したクラスタなので共有の counter（G2）と guard の中身を 2 本に分ける、と指摘した。main の案の欠陥の指摘として全部採ったので、判断の食い違いとして Fable は呼ばなかった。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた。この PR は G2 だけ） | - | 0 | 0 | 0 | 2026-10-03T03:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 18051e30 | 0 | 0 | 0 | 2026-10-03T04:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | d8d7ce77 | 0 | 0 | 0 | 2026-10-03T04:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| A1 | 独立-1 | low | no | inherited | doc-claim | fixed | 断片と PR 本文が、綴り違いの旧挙動と path の正規化を実態（`\` と `/` だけを同じとみなす）より広く書いていた。commit: d8d7ce77 |
| A2 | 独立-1 | low | no | inherited | test-power | fixed | 足したテストの綴り違い（`./`）は `_state_key` でまとまらず、key を素の文字列に戻しても通る。`\` と `/` だけが違う 2 key のテストを足した。commit: d8d7ce77 |
| A3 | 独立-1 | low | no | inherited | doc-claim | fixed | collector のコメントが、reason の件数だけ counter が進む旧い数え方を前提にしていた。commit: d8d7ce77 |
| A4 | 独立-1 | low | no | inherited | doc-claim | next-pr | SECURITY.md:106 が挙げる降格しない category が `NON_DEMOTABLE_CATEGORIES` より少ない（pre-existing、無関係。②-B の文言修正で直す） |
| A5 | 独立-1 | advisory | no | inherited | style | accepted | 同じファイルを 2 つの key で指す書き込みで、deny と警告の本文が重複する（pre-existing） |
| B1 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 断片の Summary に、変更ではない「今までどおり」の綴り違いの限界の文が入った（PR 本文の限界の節と重なる） |
| B2 | 独立-2 | low | no | self-inflicted | test-power | accepted | 区切り文字のテストは、`_state_key` から `normalize_path` を外しても通り、counter の共有そのものは確かめていない |
| B3 | 独立-2 | advisory | no | inherited | product | accepted | POSIX で `\` の綴りの key が来ると、存在しない path として `completed_reviewed_by` の共有 counter を clear し、降格が来ない（止める側） |
| B4 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 降格時の警告文「no longer block … until the counter resets」が、降格直後の clear と bounce-log-schema.md:41 に食い違う |
