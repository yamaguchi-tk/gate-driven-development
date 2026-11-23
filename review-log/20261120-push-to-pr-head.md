---
lane: L1
pr: 720
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4f12d1f4 | 0 | 3 | 1 | 2026-11-20 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 8041b03f | 0 | 1 | 1 | 2026-11-20 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | dc7f8683 | 0 | 0 | 0 | 2026-11-20 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| 独立-1-1 | 独立-1 | medium | yes | self-inflicted | trust-boundary | fixed | 設計: 変える（push の出力の文で判定する）。出力の文（PR コメントなど信頼できない文）を hook の文として文脈に入れていた。判定を push の後の手元の git の状態にし、文には手元の branch 名・upstream 名・remote 名だけを入れる。再現テストを先に書いた。commit: 81f3389e |
| 独立-1-2 | 独立-1 | medium | no | self-inflicted | coverage | fixed | GitHub の remote の文に頼り、出力を tail で切った push を知らせない。手元の状態の判定で閉じた。commit: 81f3389e |
| 独立-1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 意図した別名の push と、別の PR のブランチから切った branch で誤って知らせ、別の PR への push を勧める。手元の branch 名のリモートブランチがあるときだけ知らせ、文を確かめる手順にした。commit: 81f3389e |
| 独立-1-4 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 観点 0。事例の場面（軽いレーンの push）に何が効くかが書かれていない。debug-and-review は ~/.claude/settings.json で有効で、root checkout への symlink で入っていることを PR 本文に書いた。commit: なし（PR 本文） |
| 独立-1-5 | 独立-1 | low | no | self-inflicted | rule-conflict | accepted | gdd-pr-review-followup の手順 9 の push と直し方が、push 先の規定とそろっていない |
| 独立-1-6 | 独立-1 | low | no | self-inflicted | test-power | fixed | remote の HEAD（develop）の除外にテストが無い。develop のケースを足した。commit: 81f3389e |
| 独立-1-7 | 独立-1 | low | no | self-inflicted | coverage | accepted | 列挙: `git -C` の push の cwd のずれと、失敗で終わった複合コマンド（PostToolUseFailure）では起動しない |
| 独立-1-8 | 独立-1 | low | no | self-inflicted | product | fixed | hook の文の remote が origin 固定。upstream の remote を使うようにした（skill の文の origin 固定は残る）。commit: 81f3389e |
| 独立-1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 新しい発火条件の件数を、この型だけで測っていない。PR 本文の限界に未測と書く |
| 独立-1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストの docstring に既定のブランチの場合が無い。書き直した。commit: 81f3389e |
| 独立-1-11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | copy-sources.tsv の commit が据え置き |
| 独立-1-12 | 独立-1 | advisory | no | self-inflicted | product | accepted | 成功した Bash のたびに python3 を起動する。README に書いた |
| 独立-2-1 | 独立-2 | medium | no | self-inflicted | product | accepted | 列挙: 正しく push し直した後も、手元の branch 名のリモートブランチが残る間は同じ文を出し続ける |
| 独立-2-2 | 独立-2 | low | yes | self-inflicted | trust-boundary | fixed | 設計: 変える（名前を拒否する文字ではなく許す文字で閉じる）。branch 名・upstream 名を検査せずにコマンドの雛形に埋めていた。英数字・. _ / - に合う名前で、upstream が refs/heads/ のときだけ知らせる。再現テストを先に書いた。commit: 88ef45a9 |
| 独立-2-3 | 独立-2 | low | no | self-inflicted | coverage | accepted | 列挙: `git -C`・`cd` の先への push でも、状態は payload の cwd で読む |
| 独立-2-4 | 独立-2 | low | no | self-inflicted | product | accepted | 列挙: `git stash push` など push でないコマンドでも引き金になる |
| 独立-2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | 引き金の正規表現・remote の読み方・stderr の文・remote の HEAD がある場合の upstream 無しを、テストが固定していない |
| 独立-2-6 | 独立-2 | low | no | self-inflicted | test-power | accepted | テストの git commit が開発者の global の git 設定を読む |
| 独立-2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | hooks.json の説明と docstring の 1 行目が「作ったとき」のまま |
| 独立-2-8 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 観点 0。upstream を PR の head にしていない branch を確認なしに限界にしていた。軽いレーンの PR 作成後の push 先を root CLAUDE.md 手順 7 に足した。commit: 3ea90a2f |
| 独立-2-9 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 観点 0。本物の Claude Code で文が届くかを確かめていない。headless の claude が週の上限（11-22 解除）で動かず、PR 本文の限界に書く |
| 独立-2-10 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 未測のまま足す発火条件へのユーザーの確認が、依頼の原文に無い |
| 独立-3-1 | 独立-3 | low | no | self-inflicted | coverage | accepted | 許可リストに合わない名前（`#`・`@`・日本語など）の branch では、何も知らせない |
| 独立-3-2 | 独立-3 | low | no | self-inflicted | test-power | accepted | 許可リストのテストが upstream だけを外し、branch・remote・先頭の文字・`.`・`_` を固定していない |
| 独立-3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | README の行に、許可リスト外と refs/heads/ の外のときに黙ることが無い |
| 独立-3-4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | テストと hook の docstring に、足した黙る条件と先頭が英数字であることが無い |
| 独立-3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | CLAUDE.md の `HEAD:<head>` が、skill の `HEAD:<headRefName>` と取り方の書き方とそろっていない |
| 独立-3-6 | 独立-3 | low | no | inherited | rule-conflict | accepted | gdd-pr-review-followup の手順 9 の直し方が `git push origin <正しいブランチ名>` のまま |
| 独立-3-7 | 独立-3 | advisory | no | self-inflicted | trust-boundary | accepted | 英数字とハイフンだけの指示文の名前は許可リストを通る |
| 独立-3-8 | 独立-3 | advisory | no | inherited | product | accepted | 数字だけの upstream 名は gh pr view で PR 番号として解決される |
| 独立-3-9 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | CLAUDE.md の足した量と消した量の差は約 9 字 |
| 独立-3-10 | 独立-3 | advisory | no | inherited | bookkeeping | accepted | 未測のまま足す発火条件へのユーザーの確認が依頼の原文に無い |
| 独立-3-11 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の挙動に、upstream が refs/heads/ の外のとき黙ることが無い |
| 独立-3-12 | 独立-3 | advisory | no | inherited | coverage | accepted | 状態は payload の cwd の repo から読む |
