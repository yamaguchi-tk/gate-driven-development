---
lane: L1+
pr: 262
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。Opus の推奨〔案 A: hook を変えず文書で自走の Merge Approval を定める〕はメインの案〔案 B: merge gate に basis: autonomy のときの追加検査を足す〕と食い違い、Opus の推奨を採った。Fable は呼んでいない） | - | 1 | 1 | 0 | 2026-10-01T03:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c65eedb213b7bb9b9944aafde8f21dec82b33aca | 1 | 4 | 4 | 2026-10-01T03:58+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 5c9e1ed181cedc765440d71b49ee39f6cc6a9c34 | 2 | 0 | 2 | 2026-10-01T10:20+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火〔approval-path の high を含む巡が 2 回〕。memory の 2026-09-28 の決定で、ユーザーへの確認は内部の相談で代えた。Opus の推奨〔A′: high 2 件を、経路ではなく worklog の記録で決める条件に変えて直し、3 巡目へ〕はメインの案と同じ。Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-01T10:40+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 6519c39ead4a95f92f3815f474516ef1ee75a103 | 1 | 1 | 1 | 2026-10-01T11:05+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の再発火〔approval-path の high を含む巡が 3 回〕。方針メモ-1 で Opus が「3 巡目でも approval-path の high が出たら止める」と推奨しており、memory の 2026-09-28 の決定で確認は内部の相談で代えて「止める」を採った。この機能は opt-in で宣言と例外の行は実データ 0 件のため、残りはマージ直後の次の PR で直す。Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-01T11:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | high | no | self-inflicted | product | fixed | 草案の Merge Approval の形（approved_at の後ろにコロンが無く、evidence も無い）は parser の必須 key（evidence:・approved_at:）を欠き、merge gate に unparsable で止められる。ひな形を evidence が autonomy:<自走上限の値> の形にし、parser に通すテストを足した。commit: 31e0033f |
| P2 | 方針メモ | medium | no | inherited | approval-path | fixed | `GDD Autonomy: internal` の repo では判断役が最初の human check を承認でき、自走上限の 2 値を AI だけで選べた。autonomy.md の止まる案に足した。commit: 31e0033f |
| P3 | 方針メモ | low | no | inherited | doc-claim | fixed | post-merge-qa.md § 限界 の「merge gate は人間の承認ターンで書いた Merge Approval を求める」は hook の挙動と違う（hook はターンを見ない）。commit: 31e0033f |
| G1 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | Merge Approval を問わない条件の「利用者の規則（CLAUDE.md・AGENTS.md）」に読む先の限定が無く、PR 自身が repo の CLAUDE.md に例外を足せば満たせた。repo の外の ~/.gdd/config.local.md の固定の 1 行だけで判定する形にした。commit: 5c9e1ed1 |
| G2 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 例外の判定に固定の形と判定できないときの扱いが無かった。固定の 1 行にし、無い・2 行以上・形が違う・読めないときは例外無しにした。commit: 5c9e1ed1 |
| G3 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 手順 2 の書き直しで「hook の deny で止まる」と「承認が含むのは並べた操作だけ」が消えた。戻した。commit: 5c9e1ed1 |
| G4 | 独立-1 | medium | yes | inherited | approval-path | fixed | 手順 1 の QA の書き込みを任せる条件にも G1 と同じ穴があった。同じ例外の行を条件にした。commit: 5c9e1ed1 |
| G5 | 独立-1 | medium | no | self-inflicted | product | fixed | reason code の拒否で止まる規定が followup SKILL の review-wait-not-elapsed の待機と逆だった。review-wait-not-elapsed は followup のとおり待つ形にした。commit: 5c9e1ed1 |
| G6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | followup SKILL の (2) スコープ縮小の行に「merge は人間の明示承認」が残り、自走のマージと食い違った。例外の参照を足した。commit: 5c9e1ed1 |
| G7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | § 限界 の括弧書きが merge gate がターンを見て止めるように読めた。steering の書き込み検査が止めると書いた。commit: 5c9e1ed1 |
| G8 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | evidence の接頭辞 autonomy: が判断役の承認の印と重なった。post-pr-autonomy: にし、approved_at が書いた時刻であることを書いた。commit: 5c9e1ed1 |
| G9 | 独立-1 | low | no | self-inflicted | test-power | fixed | テストの 2 値の繰り返しが判別力を足さず、approved_at を assert していなかった。1 値にして approved_at を assert した。commit: 5c9e1ed1 |
| G10 | 独立-1 | low | no | self-inflicted | product | fixed | マージ直前の worklog の記録に固定のラベルが無く、再開でマージ済みと読みえた。マージ前・マージの行に分け、再開時の確かめ方を書いた。commit: 5c9e1ed1 |
| G11 | 独立-1 | low | no | self-inflicted | product | fixed | マージで起動する CD を並べる欄が human check のひな形に無かった。承認サマリの最大到達点に足した。commit: 5c9e1ed1 |
| G12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の目的が、グローバルの規則に例外が書かれていると根拠なく言い切っていた。PR 本文を直した。commit: なし（PR 本文） |
| G13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの 旧#260 の断片（20261001-post-pr-autonomy-scope.md:18,46）が変更前の Merge Approval の挙動を書いたまま。リリースの dry-run で版の節を直す（memory release-time-stale-fragment-fixes） |
| H1 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | 利用者の例外の行の読み方が autonomy.md § 宣言とそろっておらず、on の行の下に off の行を足す、HTML コメント・フェンスの中に行を残す、などの止めたつもりの書き方でも例外ありと読めた。読み方を autonomy.md § 宣言にそろえ、読んだ行を worklog に記録する形にした。commit: fa21248f |
| H2 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | followup SKILL の問わない条件が post-merge-qa の § 入口・手順 2 の経路に限られず、followup の clean からのマージや Post-PR Scope Continuation からも QA 計画レビュー・Deploy Paths・.gdd-config.md の除外を通らずに問わずにマージできた。human-check-template の自走上限の置換値も同じ。条件を post-merge-qa の手順 2 の「自走のマージの条件」1 か所にまとめ、followup・human-check-template・state-field-tiers・self-review-lanes がそれを指す形にした。宣言の 2 回目の読み直しを手順 2 の前にした。commit: fa21248f |
| M3 | 独立-2 | medium | no | self-inflicted | doc-claim | next-pr | human-check-template-compact の最大到達点に、マージで起動する workflow と環境を並べる規定が無い |
| L4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 承認サマリの最大到達点に QA の書き込み先（Write Targets）が並ばない |
| L5 | 独立-2 | low | no | self-inflicted | product | next-pr | review-wait-not-elapsed が他の reason code と一緒に出たときも待つと読める。単独のときだけ待つ形にする |
| L6 | 独立-2 | low | no | self-inflicted | product | next-pr | マージの行の記録が例外の有無で分かれ、再開時の確かめで MERGED 以外（OPEN・CLOSED）の扱いが無い |
| L7 | 独立-2 | low | no | self-inflicted | product | next-pr | マージ前の行の起動先にアカウント ID を含む ARN が入りうるが、伏せる規定が無い |
| L8 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 利用者の規則と例外の行の食い違いを誰も確かめないことが限界に書かれていない |
| L9 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | operation-levels.md の Post-PR Autonomy の行が新しいキーに触れていない |
| A10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | § 宣言の見出し（ユーザーが書く・repo 単位）と、repo の外の利用者の行が同じ節にある |
| A11 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | テストの入力を 1 値にしたのはテストの削除に当たりうる |
| A12 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋に、再開時の確かめと approved_at の鮮度の扱いが無い |
| K1 | 方針メモ-1 | - | - | - | - | - | なし |
| N1 | 独立-3 | high | yes | self-inflicted | approval-path | accepted | 例外の記録の形が読んだ行をそのまま書くため判定の結果を残さず、on と off の 2 行があって例外無しと判定した入力でも、手順 2 は記録の行があるだけで Merge Approval を問わずにマージへ進めた。宣言の記録も同じ形。安全策 4 で止めたので直さず、PR 本文の限界の先頭に書き、次の PR で記録を判定の結果（on か なし）にする |
| N2 | 独立-3 | medium | no | self-inflicted | product | fixed | plugins/.DS_Store が commit に入っていた。外した。commit: 36c4856e |
| N3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | human-check-template の自走上限の括弧書きが、QA の書き込みを任せる条件を手順 1 と違う形で書いている |
| N4 | 独立-3 | low | no | self-inflicted | product | next-pr | 再開で読む記録の一覧に例外の記録が無い |
| N5 | 独立-3 | low | no | inherited | doc-claim | next-pr | operation-levels.md の設定の節に config.local.md から読む例外の行が無い |
| N6 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 断片の Summary が例外があれば問わないと条件を広く書いている |
| N7 | 独立-3 | low | no | self-inflicted | style | next-pr | self-review-lanes の括弧書きで同じ参照先を 2 回指している |
| N8 | 独立-3 | low | no | inherited | doc-claim | next-pr | post-merge-qa.md の参照元の一覧が、手順 2 が挙げる参照元と合わない |
| N9 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり（commit の件名に巡の ID が入り、起動時の git status から経緯が届いた）。以後の review-log の commit の件名に巡の ID を書かない |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
