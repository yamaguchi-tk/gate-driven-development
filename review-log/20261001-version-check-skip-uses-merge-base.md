---
lane: L1+
pr: 273
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（Opus は比較を merge-base に置き換える案〔main と同じ〕を推し、merge-base が 2 件以上〔criss-cross〕なら SKIP にしない条件の追加も勧めた。main は追加しない案で食い違い、信号 ① で Fable を呼んだ。Fable は追加しない側を推した〔plugin に触れないブランチの criss-cross が誤 FAIL になる。criss-cross の中で plugin の変更を取り消す fail-open は作れるが、運用ではまれなので限界に書く〕。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-01T20:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 84a9d062376a4087d2067a3666633a227437ecd7 | 0 | 1 | 0 | 2026-10-01T20:50+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 59f42435fab1bebcdbc408147af5b9097e33d981 | 0 | 0 | 0 | 2026-10-01T21:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| L1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 層 B の実行条件の正本 docs/VERSIONING.md:127 が旧条件（統合先との差）のまま。merge-base からの変更と、求まらないときの FAIL に直した commit: 1a3dd40e |
| L2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 限界と断片の「plugin に触れないブランチは SKIP-B」は criss-cross では一意でない。断片に例外を書き、PR 本文の限界を直した commit: 1a3dd40e |
| L3 | 独立-1 | low | no | self-inflicted | product | fixed | merge-base が取れないときの FAIL が理由を示さず、shallow clone も同じ FAIL になる。案内を足し、断片に書いた commit: 1a3dd40e |
| L4 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 断片の Validation 欄にテストの件数を書いている。件数を外し、テストの名前を並べた commit: 1a3dd40e |
| L5 | 独立-1 | low | no | self-inflicted | test-power | fixed | SKIP を期待する 2 本が SKIP の理由を固定していない。理由の文言の assert を足した commit: 1a3dd40e |
| L6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋の変更内容に実行結果の断定（PR 旧#269 の実データで確かめた）がある（テンプレート外の記述あり）。次の巡の抜粋から除き、PR 本文にはコマンドと出力を at sha つきで書く |
| L7 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | SKIP-B の理由の文言の変更が PR 本文と断片に無い。断片と PR 本文に書いた commit: 1a3dd40e |
| L8 | 独立-1 | advisory | no | inherited | style | accepted | run() が 300 行の目安を超えたまま差分で 1 行増える（tests/checks/ が code-health の対象かは未決）。PR 本文に列挙 |
| M1 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 足した assert「cannot find the merge-base」は旧文言とも一致し、`git fetch --unshallow` の案内を戻しても落ちない |
| M2 | 独立-2 | low | no | self-inflicted | style | next-pr | 同じ merge-base の失敗を読む review-log-present.sh:268 だけ、案内の無い旧文言のまま |
| M3 | 独立-2 | low | no | inherited | doc-claim | next-pr | VERSIONING.md:127 の層 B の実行条件に、identity（marketplace.json の name）と work tree でないときの FAIL が無い |
| M4 | 独立-2 | advisory | no | self-inflicted | style | accepted | git merge-base の失敗（rc 128 を含む）をすべて「no common ancestor」と案内する。stderr も出るので判定は FAIL のまま。PR 本文に列挙 |
| M5 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「後者が常に FAIL になる」は言い過ぎ。「FAIL になりうる」に直した commit: なし（PR 本文） |
| M6 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の括弧書きに criss-cross の説明（限界の内容）が入っている。挙動の範囲を書くため残す。PR 本文に列挙 |
| M7 | 独立-2 | advisory | no | inherited | product | accepted | SKIP-B の判定は commit 同士の比較で、commit 前の作業ツリーの変更を見ない（以前から）。PR 本文に列挙 |
| M8 | 独立-2 | advisory | no | self-inflicted | process | accepted | reviewer が自分の Grep で本 PR の review-log の 3 行を読んだ（除外の glob の付け忘れ。根拠には使っていないと報告）。prompt と抜粋にテンプレート外の記述は無く、巡は有効とした |
