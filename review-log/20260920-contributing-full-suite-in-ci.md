---
lane: L1
pr: 旧#163
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f7c2b4c95d64d243d09497a193e1ad704d504f68 | 0 | 2 | 0 | 2026-09-20T14:42+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus（prompt の差分に転記ミス 3 箇所: skills→skill、行末空白、末尾に実在しない文脈行 1 行。reviewer の指摘には影響なし） | ca61bd53d28f62751a91e1369c4a52ee20fd4655 | 0 | 1 | 0 | 2026-09-20T15:01+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus（prompt は差分・PR 本文とも保存した内容と機械的に一致。reviewer は Grep の結果に review-log の既存行が混ざって見えたと開示したが、指摘は差分と実コードから導いたと報告。F6・F7 は A3・A4 と同じ指摘） | 169877b54bba7e0151de9c1749cc120909cf401a | 0 | 0 | 0 | 2026-09-20T15:18+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分, model: opus（1 回目の起動は prompt の差分に転記ミス 2 箇所があり、TaskStop して起動し直した。起動し直した prompt は差分・PR 本文とも保存した内容と機械的に一致。reviewer は Grep の結果に review-log の行が混ざったが中身は読んでいないと開示） | 77407970c5f332a7fb300af5fa099e4377acf13c | 0 | 1 | 0 | 2026-09-20T15:35+09:00 |
| 独立-5 | light-lane-independent-reviewer, 全差分, model: opus（最終の全差分巡の 2 回目。prompt は差分・PR 本文とも保存した内容と機械的に一致） | 6e296aaf84524e610439f01b01d1cbd1a2cae04a | 0 | 0 | 0 | 2026-09-20T15:48+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | stale-note-after-followup | fixed | root `CLAUDE.md` 手順 3 に「CONTRIBUTING の項 1 は実行しない（追随は次の PR）」の注記が残り、この PR で追随したことと食い違う。注記を外し、「CONTRIBUTING の項 1 も同じ分担を書いている」に直した（差分との関係: 影響先） |
| A2 | 独立-1 | medium | no | self-inflicted | conflicting-pointer-target | fixed | 項 1 が残した正本のポインタ先 `references/gdd-self-development.md:20` が「フルスイートは completion-check と pre-PR の 2 回だけ」で、項 1 の新しい規定と逆だった。同 bullet を「フルは CI、手元は対応する契約テストだけ」に直した。あわせて、項 1 の一般規定（契約破れを先に直す）を「以下は全量を手元で回す手順」の見出しの外へ出した。「関係するテスト」の選び方を root CLAUDE.md へ指す案は、plugin の文書から root CLAUDE.md への依存を書かない規則（CONTRIBUTING「Root CLAUDE.md 独立性」）に反するので採らず、要点を CONTRIBUTING に自己完結で書いた（差分との関係: 変更箇所） |
| A3 | 独立-1 | low | no | inherited | stale-count-in-instructions | next-pr | `.github/instructions/gate-driven-development.instructions.md:13` の Skill count budget が 28 のまま（実数は 29）。Copilot が「上限超過」と誤指摘しうる。差分との関係: 無関係。次の PR で数値を直す |
| A4 | 独立-1 | advisory | no | self-inflicted | unobservable-check | accepted | Copilot が check run の状態を観測できない場合、「`gdd-plugin` が success か」の確認は常に不能になる。並記の「PR 本文に run の URL や結果があるか」は観測できるので指示は機能する。PR 本文に列挙 |
| A5 | 独立-1 | advisory | no | self-inflicted | trigger-wording | accepted | 「PR と main への push ごとに回す」は、PR が無いブランチへの push を含まない（trigger は pull_request と main への push だけ）。軽いレーンは push 直後に PR を作るので実害は無い。PR 本文に列挙 |
| B1 | 独立-2 | medium | no | self-inflicted | local-full-run-occasions | fixed | 手元で全量を回す機会の列挙（CONTRIBUTING 項 1「release 前と CI が使えないときだけ」）が、`gdd-self-development.md:19` の「hooks は local に入れる前に validate と全量を通す」を落としていた。CONTRIBUTING の列挙と root CLAUDE.md 手順 3 の許可の列挙に「hooks を local に入れる前」を足して揃えた（:19 は変えない。差分との関係: 影響先） |
| B2 | 独立-2 | low | no | self-inflicted | pointer-into-hidden-section | fixed | 項 1 に足した「round ごとの粒度は下の正本を参照」が、全量を手元で回すときの区画の中を指していた。`references/gdd-self-development.md` § 開発場所の使い分け を直接書いた（変更箇所） |
| B3 | 独立-2 | low | no | self-inflicted | ci-result-timing | fixed | `gdd-self-development.md:20` が挙げる completion-check・pre-PR は push 前で、その時点では CI のフルの結果が無い。「フルの結果は PR 作成後に `gdd-plugin` の success で確かめる」を足した（変更箇所） |
| B4 | 独立-2 | low | no | self-inflicted | fragment-list-drift | fixed | 断片の Validation が「2 ファイルの文言だけの変更」のまま（Affected Files は 4 ファイル）。「Affected Files の 4 ファイルの文言だけの変更」に直した（影響先） |
| B5 | 独立-2 | low | no | self-inflicted | relevant-test-set-narrow | fixed | 断片の grep の alternation に `CLAUDE` が無く、root CLAUDE.md を読む契約テスト 3 本が証拠集合から漏れていた。`CLAUDE` を足して回し直した（1224 passed。変更箇所） |
| B6 | 独立-2 | low | no | self-inflicted | rule-scope-overclaimed | fixed | 「Root CLAUDE.md 独立性」規則に従って指さない、の書き方が規則の適用範囲（README・commands・skills・agents・scripts）と合わない。「設計判断として指さない。規則は CONTRIBUTING 自身は対象外だが同じ趣旨に合わせた」に直した（断片。変更箇所） |
| B7 | 独立-2 | low | no | inherited | limitation-list-overbroad | fixed | 限界の列挙の `docs/VERSIONING.md` 47 行目は v1.0 昇格基準（CI 安定）で、手元で全量を回す前提ではない。対象外と分けて書いた。差分との関係は無関係だが、指摘の行がこの PR の変更行（断片）なので手順 6 の規定で ① にした |
| B8 | 独立-2 | low | no | inherited | stale-count-in-instructions | re-reported | `.github/instructions/gate-driven-development.instructions.md:13` の Skill count budget 28（実数 29）。独立-1 の A3（next-pr）と同じ指摘の再掲 |
| C1 | 独立-3 | low | no | self-inflicted | local-full-run-occasions | fixed | root `CLAUDE.md` 手順 3 の「ローカルで全量を回してよいのは…だけ」の列挙が、CONTRIBUTING 項 1 の 3 つ（release 前・hooks を local に入れる前・CI が使えないとき）より 1 つ少なかった。「release 前（CONTRIBUTING 項 0）」を足した（変更箇所） |
| C2 | 独立-3 | low | no | self-inflicted | duplicated-pointer | fixed | 「以下は全量を手元で回すときの手順」の内側に、「round ごとの検証は契約テストのみでよい」の 1 文が残り、項 1 先頭側の同じポインタと重複し、意図と逆に読めた。内側の 1 文を削った（変更箇所） |
| C3 | 独立-3 | low | no | self-inflicted | relevant-test-set-empty-for-new-file | fixed | 新規の skill は名前を参照するテストがまだ無く、「関係するテスト」が空集合になる。「skill を追加する」手順 6 に `plugin.json` を読むテスト（4 ファイル）を入れる指示を足した（変更箇所） |
| C4 | 独立-3 | low | no | self-inflicted | ci-trigger-wording | fixed | `gdd-self-development.md:20` の「CI は push の後に走る」は、PR の前の branch push では成り立たない（trigger は `pull_request` と main への push）。「PR を作った後の push（と main への push）で走る」に直した（変更箇所） |
| C5 | 独立-3 | low | no | inherited | hook-add-procedure-not-connected | fixed | 「hook を追加する」の手順が pytest を回す手順を持たず、項 1 の「hooks を local に入れる前は全量」に接続していなかった。関係するテストと、local に入れる前の全量の手順を足した（影響先。経路: 項 1 の列挙 → 同じ節の hook 追加の手順） |
| C6 | 独立-3 | low | no | inherited | stale-count-in-instructions | re-reported | `.github/instructions/gate-driven-development.instructions.md:13` の Skill count budget 28（実数 29）。独立-1 の A3（next-pr）の再掲 |
| C7 | 独立-3 | advisory | no | self-inflicted | unobservable-check | accepted | Copilot が check run の状態を読めるか未確認。PR 本文の run の URL・結果という代替が同じ文にある。独立-1 の A4 と同じ指摘（origin が this-diff なので再掲にはせず、advisory として PR 本文に列挙する） |
| D1 | 独立-4 | medium | no | self-inflicted | wrong-selector-for-new-skill | fixed | 独立-3 の C3 の修正で足した「`plugin.json` を読むテストも入れる」は、選ばれる 4 ファイルが manifest の version しか見ず、新規 skill を 1 つも検査しない。skill 数を固定する `test_superpowers_differentiation_contract.py`（29 の pin）と、skills 本文を走査する `test_finding_category_vocabulary_contract.py` を名前で指すように直した（変更箇所。自分の修正が生んだ指摘） |
| D2 | 独立-4 | low | no | self-inflicted | path-base-mismatch | fixed | 手順 6 に足した grep だけが repo root 基準で、同じ節の他の手順は plugin 基準。D1 の修正で grep をやめ、plugin 基準のテスト名（`tests/…`）にそろえた（変更箇所） |
| D3 | 独立-4 | low | no | self-inflicted | pr-body-omits-deletion | fixed | 項 1 から重複した 1 文を削ったことが、PR 本文の変更内容に無かった（断片にはあった）。PR 本文の草案に 1 句足した（変更箇所） |
| D4 | 独立-4 | low | no | inherited | step2-plugin-json-skills-array-absent | next-pr | 「skill を追加する」の手順 2「`plugin.json` の `skills` 配列に追加」は、3 つの manifest のどれにも skills の配列が無く、実行できない。この PR が触っていない行（`CONTRIBUTING.md:168`）で、D1 の修正で手順 6 は手順 2 に依存しなくなった。次の PR で直す |
| D5 | 独立-4 | low | no | inherited | stale-count-in-instructions | re-reported | `.github/instructions/gate-driven-development.instructions.md:13` の Skill count budget 28（実数 29）。独立-1 の A3（next-pr）の再掲 |
| E1 | 独立-5 | low | no | self-inflicted | ci-trigger-wording | next-pr | `gdd-self-development.md:20` に独立-3 の C4 の修正で足した「CI は PR を作った後の push（と main への push）で走る」は、workflow の trigger（`pull_request` の `opened`・`synchronize`・`reopened`）と食い違う。PR の作成そのものが run を起こす。「PR の作成・更新（と main への push）」に直し、`CONTRIBUTING.md:83` の「PR と main への push ごと」も揃える。最終の全差分巡の 2 回目に出た ① の low なので、手順 6 の規定で直さない（直すと巡が無効になる） |
| E2 | 独立-5 | low | no | self-inflicted | closed-list-of-skill-tests | next-pr | 「skill を追加する」手順 6 が挙げる 2 本のうち、新規 skill で必ず落ちるのは skill 数の pin だけ。skills 本文を走査する pytest は他にもある（`test_precision_tiering_contract.py`・`test_remediation_loop_model_routing_contract.py`）。列挙で閉じず、型で書く（skill 数を固定するテストと、skills 本文を走査するテスト）。CI が backstop になっている。手順 6 の規定で直さない |
| E3 | 独立-5 | low | no | inherited | stale-count-in-instructions | re-reported | `.github/instructions/gate-driven-development.instructions.md:13` の Skill count budget 28（実数 29）。独立-1 の A3（next-pr）の再掲 |
| E4 | 独立-5 | advisory | no | self-inflicted | unobservable-check | accepted | Copilot が check run を観測できるか未確認。PR 本文の run の URL・結果という代替が同じ文にある。独立-1 の A4、独立-3 の C7 と同じ指摘。PR 本文に列挙する |
| E5 | 独立-5 | advisory | no | self-inflicted | two-rules-one-pointer | accepted | 項 1 の「round ごとの粒度は `gdd-self-development.md` § 開発場所の使い分け」の先は、別の選び方（`tests/test_<対象>_contract.py`、`-k`）を書いていて、同じ規則の詳細に見える。PR 本文の限界の節に「別の目安で、統一していない」と開示済み。PR 本文に列挙する |
