---
lane: L1
pr: 旧#165
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 88d81cc067d6f881ab455c1fb5b7863230f93ec4 | 0 | 1 | 0 | 2026-09-21T19:09+09:00 |
| PR後-1 | yamaguchi-tk（PR 上のレビュー） | 3e1e68dfb3c867705182d528a6ad6caac5da21be | 0 | 2 | 0 | 2026-09-21T19:46+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 8c5c72b24a1d5fc7c25f442d30eb3b592d95ff4c | 1 | 1 | 1 | 2026-09-21T19:55+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | c62ec340b0979665664bf76dc9c4840ad26b3f40 | 0 | 0 | 0 | 2026-09-21T20:18+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | shortcut-omits-test-weakening | fixed | 近道の条件（`CLAUDE.md:80`）が「判定のコードを含まない」だけで、L0 行（`:17`）・テスト削除等の例外文（`:56`）が言う「テストの削除・assert の緩和も含まない」を反映していない。テストを削る PR が近道 1 巡で通る経路が残る。PR後-1（ユーザーレビュー）で指摘され、この PR で直した |
| F2 | 独立-1 | medium | no | self-inflicted | next-pr-list-incomplete | next-pr | 無効化後の差分巡に足した `next-pr` の適用箇所（`:90`）が、`next-pr` を列挙する他の 3 箇所（`:62`・`:66`・`:176`〔全レーン共通の「近道と3巡目では」〕・`:183`）に反映されておらず、`next-pr` にした指摘が「次の PR」一覧の入口から漏れる。次の PR で「近道・3 巡目・無効化後の差分巡」に揃える |
| F3 | 独立-1 | low | no | self-inflicted | rationale-inconsistent-with-list | next-pr | パスの区分の根拠文（`:54`）「宣言だけを目的とするファイル」が、列挙済みの `VERSIONING.md`（手順文書、宣言は一部の節のみ）や、非判定コード扱いの `changelog.d/`・`review-log/`（同じ「中身を読んで検査する」根拠が当てはまる）と字義上一致しない。次の PR で根拠を検査が読む節に限定するか、列挙を正本と明記する |
| F4 | 独立-1 | low | no | self-inflicted | github-dir-default-open | next-pr | `.github/`（`workflows/` を除く）を規則の文書にしたことで、将来 `.github/actions/`・CI が呼ぶスクリプトが増えても既定で近道の対象になる（閉じる側でなく開く側がデフォルト）。次の PR で判定のコード側を「CI が実行するもの」の列挙にし、規則の文書側を `copilot-instructions.md`・`instructions/` の列挙にする |
| F5 | 独立-1 | low | no | self-inflicted | fragment-affected-files-mismatch | next-pr | 断片 `#### Changed` が「近道の終了文言」から言い切り表現を外したと書くが、実際に外したのは 3 巡目と無効化後の差分巡の文言で、近道の文言（`:81`）は変えていない。`#### Affected Files` も L0 行（`:17`）の変更が抜けている。次の PR で文言を直す |
| F6 | 独立-1 | advisory | no | self-inflicted | duplicate-rule-in-review-checklist | next-pr | 断片規則の正本を `CHANGELOG.md` § Policy に移した一方、`CONTRIBUTING.md:236` の PR レビュー観点表に同じ規則の再掲が残る。次の PR で pointer に短縮する |
| H1 | PR後-1 | medium | no | self-inflicted | codex-return-point-too-broad | fixed | 手順 5（Codex）の巡の終了時の参照（`CLAUDE.md:47`）が、常に「最終の全差分巡の後に commit を積んだとき」に送られる。Codex の主な入口である L1+ 安全策 4 は最終巡の前にも発火するため、途中の巡で直した commit まで無効化後の差分巡（最大 2 回）に押し込め、残りの通常の巡を飛ばしてしまう。この PR で、最終巡の後かそれより前かで参照先を分けた |
| H2 | PR後-1 | medium | no | self-inflicted | shortcut-omits-test-weakening | fixed | F1 の再確認（インラインコメントで再掲）。近道の資格判定（`CLAUDE.md:80`）にテスト削除・assert 緩和の除外が反映されておらず、断片の「両方で判定のコードと同じ扱いにする」という記述と実装が食い違っていた。この PR で `:80` に除外を足した |
| H3 | PR後-1 | low | no | self-inflicted | next-pr-list-incomplete | re-reported | F2 の再確認。記録済みの `next-pr` と同じ |
| H4 | PR後-1 | low | no | self-inflicted | github-dir-default-open | re-reported | F4 の再確認。記録済みの `next-pr` と同じ |
| H5 | PR後-1 | low | no | self-inflicted | changelog-policy-drops-midreview-exception | fixed | `CHANGELOG.md` § Policy（旧 `CONTRIBUTING.md`）に断片規則の正本を移した際、「レビューの修正が利用者から見える変更を変えたときだけ、その分を push の前の 1 回にまとめて直す」の例外文が落ちていた。この PR で § Policy に例外を書き戻した |
| H6 | PR後-1 | low | no | self-inflicted | fragment-affected-files-mismatch | re-reported | F5 の再確認。記録済みの `next-pr` と同じ |
| I1 | 独立-2 | high | no | self-inflicted | safety-net4-continue-conflict | fixed | H1 の修正で `CLAUDE.md:47` に足した「安全策 4 発火時も次の巡へ進む」分岐が、安全策 4 の「止める」規定（`:170`）と正面から矛盾していた。HITL で「止める」を選んだ後でも、手順 5 だけを読めば続ける指示が有効に読めた。この PR で、続行できるのは HITL で続行を選んだ後に限ると明記し、`:170` の優先規定に手順 5 も加えた |
| I2 | 独立-2 | medium | no | self-inflicted | codex-return-round-type-mismatch | fixed | `CLAUDE.md:47` に書いた具体的な巡の種類（差分巡 → 最終の全差分巡）が、同じ場面を扱う全レーン共通の規定（`:176`、巡の種類を名指ししない）より狭く、対になる 2 つの規定がずれていた。この PR で手順 5 からも巡の種類の名指しを外した |
| I3 | 独立-2 | low | no | self-inflicted | changelog-policy-summary-stale | fixed | `CHANGELOG.md` § Policy に例外を書き戻した一方、それを要約する `CLAUDE.md:37`・`CONTRIBUTING.md:136` が「巡ごとに書き足さない」と絶対形のまま例外を落としていた。この PR で要約を「確定の時機」に縮めた |
| I4 | 独立-2 | advisory | no | self-inflicted | duplicate-rule-in-review-checklist | re-reported | F6 の再確認（`CONTRIBUTING.md:236` の重複規則）。記録済みの `next-pr` と同じ |
| I5 | 独立-2 | advisory | no | self-inflicted | prompt-template-violation | out-of-diff | 呼び出し prompt の PR 本文欄に、レビュー工程の叙述（前回の巡の結果・指摘 ID）が含まれていた（テンプレート外）。差分の内容ではなく、今後のレビュー起動時の運用注意として記録するのみ。次の PR の対象にしない |
| J1 | 独立-3 | low | no | self-inflicted | pointer-direction-wrong | next-pr | I2 の修正で `CLAUDE.md:47` に足した「上の『巡は 2 種類ある』と近道の規定」の参照方向が誤り。両方とも手順 5 より下（`:57`・`:80`）にある。次の PR で「下の」に直す |
| J2 | 独立-3 | low | no | self-inflicted | safety-net4-proviso-scope-narrow | next-pr | I1 の修正で足した安全策 4 の但し書きが、「それより前」分岐の末尾にしか掛からず、「直して commit を積んだら」より後ろに置かれているため、HITL 待ちの範囲を狭く読める。次の PR で、但し書きを両分岐の前に 1 回だけ置く形に直す |
| J3 | 独立-3 | low | no | self-inflicted | fragment-affected-files-mismatch | next-pr | 断片の Affected Files（`changelog.d/20260921-light-lane-cycle-shorten-followup.md:25`）が「L1+ で足す安全策 4」（`CLAUDE.md:170`）の変更を含めていない。次の PR で範囲に加える |
| J4 | 独立-3 | low | no | self-inflicted | changelog-policy-confirm-timing-ambiguous | next-pr | `CHANGELOG.md:20` の例外文が「1 回で確定」と「1 回にまとめて直す」で「1 回」を 2 つの意味に使っており、レビュー後に断片を直す時機が確定しない。次の PR で時点ベースの書き方に直す |
| J5 | 独立-3 | low | no | self-inflicted | duplicate-enumeration-not-collapsed-to-pointer | next-pr | `CONTRIBUTING.md:136` の第 2 文が、`CHANGELOG.md:20` と同じ 4 項目の列挙をそのまま重複させたまま残っている（F6・I4 と同系統、別箇所）。次の PR で列挙を持たない形に直す |
| J6 | 独立-3 | advisory | no | self-inflicted | review-scope-field-nonstandard | out-of-diff | 呼び出し prompt の `範囲` 欄に `差分（無効化後）` を渡した。規定（`CLAUDE.md:84`）は欄自体を `差分` のまま渡し、区別は review-log の reviewer 列だけで表すとしている。差分の内容ではなく運用注意として記録するのみ |
| J7 | 独立-3 | advisory | no | self-inflicted | diff-hunk-header-mismatch | out-of-diff | prompt の差分欄の最終ハンクのヘッダ（`@@ -12,8 +12,8 @@`）と実際の行数が不一致（手貼り時に文脈行が重複）。実ファイルには重複が無く、変更行の判断には影響していない。運用注意として記録するのみ |
