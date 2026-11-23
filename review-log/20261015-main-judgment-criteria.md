---
lane: L1
pr: 511
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 214649c9 | 0 | 5 | 0 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | db54b1f9 | 0 | 4 | 0 | 2026-10-15 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 84eccd3f | 0 | 1 | 0 | 2026-10-15 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 82cd63ef | 0 | 2 | 0 | 2026-10-15 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 6c911d0f | 0 | 2 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 縮める判断の扱いが、依頼の 2 つの道（並行の相談か、依頼より狭いと書いた確認）から読み替わっていた。2 つの道をそのまま規定にした。commit: db54b1f9 |
| A2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 原文と言い換えた文を並べるが、main が申告した語の対に狭まっていた。整理した要件の各行に、request-crosscheck の要件の表の原文（express は request.md の引用）を並べる形にした。commit: db54b1f9 |
| A3 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 相談役の本文が正本を指すだけではなく、指す 1 文と写しと一致のテストになっている。ユーザーに返事を待たない確認として出した |
| A4 | 独立-1 | medium | no | self-inflicted | product | accepted | 依頼より狭い の開示先が、human check の一次表示（compact）に無い。確認は判断ポイントか問いに出す形にしたが、compact の固定の欄は足していない |
| A5 | 独立-1 | medium | no | self-inflicted | product | accepted | 同じ縮小の判断を定める既存の規定（requirements-template:117、brainstorming-steps 9a、requirements-gating の照合）が、前の弱い条件のまま残る |
| A6 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 合格基準のある AC を、ユーザーの合格基準を写した AC に読み替えていた。依頼の語に戻した。commit: db54b1f9 |
| A7 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 方式転換の 4 択の、再設計を先に比べる順序の扱いが無かった。4 択の推奨で再設計を先に比べる形にした。commit: db54b1f9 |
| A8 | 独立-1 | low | no | self-inflicted | product | accepted | Narrowed Acceptance は、列挙に縮める＋対象外 で避けられる |
| A9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 閉じ方 (a)(b) のみなしが、Structural Closure Skipped に当たるかが読めない |
| A10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 対象外の行の「上の 2 行に当たらない」が Vague Enumeration Boundary の行を除いていない |
| A11 | 独立-1 | low | no | self-inflicted | product | accepted | 基準 1 と human check の狭める根拠で、数値の意味の強さが違う |
| A12 | 独立-1 | low | no | self-inflicted | product | accepted | compact の他AC波及 の記入例と、full の記入例が規則の変更に追いついていない |
| A13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 2 つの skill が、改名前の節名 scope の勝手な拡大 で参照している |
| A14 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の「前者」が、文の並びでは違う規則を指す |
| A15 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に、基準 4 の言い換えが無い（PR 本文で直す） |
| A16 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の件数に、出典も数えたコマンドも無い（PR 本文で直す） |
| A17 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 一致のテストは番号付きの行だけを比べ、docstring にクラスと根拠が無い |
| A18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「食い違えば正本に従う」が、相談役は正本を読めないという前提と合わない |
| A19 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Affected Files に context-budget.md があるが、Summary に無い |
| A20 | 独立-1 | advisory | no | self-inflicted | product | accepted | root CLAUDE.md の方針メモの広い側・狭い側の規定が、締めた後の規定と食い違う（root CLAUDE.md を触る PR で合わせる） |
| A21 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 承認済みの除外に 依頼より狭い を付けている（PR 本文で直す） |
| A22 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が見えない（PR 本文に書く） |
| B1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 縮める判断の確認の道から「限界に」が落ち、相談役の道では縮めた記録が人に届かなかった。確認を限界に書く形に戻し、2 本が割れたら確認に進むこと、縮めたら次に人に示す出力の限界の先頭に書くことを足した（L1 と同じ箇所）。commit: 84eccd3f |
| B2 | 独立-2 | medium | no | self-inflicted | ac-closure | accepted | 「合格基準のある AC」に定義が無く、字どおり読むと全部の AC に当たる。語は依頼の原文のままで、読みはこの PR では決めない |
| B3 | 独立-2 | medium | no | self-inflicted | ac-closure | fixed | planning reviewer の表の対象外の行の「上の 2 行」が、足した 2 行を対象外にしうる。「上のどの行にも当たらない」にした。commit: 84eccd3f |
| B4 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | express には request.md が無いのに、原文の出典を request.md にしていた。会話の依頼の発言の引用にし、表に行が無いときの出典も足した（L2 と同じ箇所）。commit: 84eccd3f |
| B5 | 独立-2 | medium | no | self-inflicted | request-drift | re-reported | 相談役の本文が指すだけではなく写しとテストになっている（A3 の再掲） |
| B6 | 独立-2 | low | no | self-inflicted | request-drift | fixed | 確認の道から「限界に」が落ちた（B1 と同じ修正）。commit: 84eccd3f |
| B7 | 独立-2 | low | no | self-inflicted | request-drift | fixed | 要件の表に行が無いときの原文の出典が無い（B4 と同じ修正）。commit: 84eccd3f |
| B8 | 独立-2 | low | no | self-inflicted | stop-marker | accepted | 返事を求める問いの止まり方（gdd-stop の reason）を指していない |
| B9 | 独立-2 | low | no | self-inflicted | option-order | accepted | 4 択の推奨順に task 撤回の位置が書かれていない |
| B10 | 独立-2 | low | no | self-inflicted | changelog | fixed | 変更断片が修正後の規定（縮める判断の 2 つの道、原文: の行）に追随していない。commit: 84eccd3f |
| B11 | 独立-2 | low | no | self-inflicted | changelog | fixed | 変更断片に 4 択の推奨順と rollback-patterns.md が無い。commit: 84eccd3f |
| B12 | 独立-2 | advisory | no | inherited | option-order | accepted | Remediation Loop Safety と PR 後の方式転換の 3 択には推奨順が無い（依頼は 4 択だけを名指し） |
| B13 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文に Skill RED-GREEN Evidence を載せること |
| C1 | 独立-3 | medium | no | self-inflicted | request-drift | re-reported | 相談役の本文が指すだけではなく写しとテストになっている（A3 の再掲） |
| C2 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | express の human check を書く subagent は会話を持たないので、原文: 行がユーザーの原文にならない。express では表示の前に main が会話の依頼の発言を埋め、引けなければ未取得と書くようにした。commit: 82cd63ef |
| C3 | 独立-3 | low | no | self-inflicted | limit-record | accepted | 縮めた後の完了報告で、限界の先頭と output-format の § スコープ変更通知 の 2 つの規定が並ぶ |
| C4 | 独立-3 | low | no | self-inflicted | advisor-split | accepted | 相談役の片方が返らないときの扱いが無い |
| C5 | 独立-3 | low | no | self-inflicted | subagent-scope | accepted | 縮める判断をする subagent は相談役を呼べないので、確認の側に進むと書いていない |
| C6 | 独立-3 | low | no | inherited | doc-ref | accepted | task-breakdown と subagent-driven-implementation の SKILL が節を旧名（scope の勝手な拡大）で指す |
| C7 | 独立-3 | low | no | self-inflicted | changelog | fixed | 変更断片に、2 本が割れたら確認に進むことと、表に行が無いときの出典が無い。commit: 82cd63ef |
| C8 | 独立-3 | low | no | inherited | option-order | accepted | completion-check の SKILL の 4 択に推奨の順序が書かれていない（出力手順から rollback-patterns に届く） |
| C9 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文に Skill RED-GREEN Evidence を載せること |
| C10 | 独立-3 | advisory | no | inherited | doc-claim | accepted | 「相談役は plugin の references を読めない」は、読んだ例 0 件の観測より強い断定になっている |
| D1 | 独立-4 | medium | no | self-inflicted | wiring | fixed | express の原文: を main が埋める規定に、subagent が書くときのテンプレート（compact）が追随せず、書く側と埋める側が決まっていなかった。subagent は `原文: main 記入` と書き、main が置き換える形にした。commit: 6c911d0f |
| D2 | 独立-4 | medium | no | self-inflicted | wiring | fixed | background の返りの手順（subagent-dispatch の Typed Agent Resolution 4）が、埋める欄に express の原文: を含んでいなかった。commit: 6c911d0f |
| D3 | 独立-4 | medium | no | self-inflicted | request-drift | re-reported | 相談役の本文が指すだけではなく写しとテストになっている（A3 の再掲） |
| D4 | 独立-4 | low | no | self-inflicted | doc-ref | fixed | subagent-dispatch の Post-Return の行が、原文: の規定を原則 7 と指していた。commit: 6c911d0f |
| D5 | 独立-4 | low | no | self-inflicted | doc-ref | fixed | gdd-dev.md の行からファイル名が落ち、原則と項目の 2 語で呼んでいた。commit: 6c911d0f |
| D6 | 独立-4 | low | no | self-inflicted | changelog | fixed | 変更断片に `原文: 未取得（理由）` が無い。commit: 6c911d0f |
| D7 | 独立-4 | low | no | self-inflicted | limit-record | fixed | PR 本文の限界で、軽いレーンに届かない分が連鎖の除外とまとまり、19 件のうち届く件数が無かった。件数を分けて書いた。commit: なし（PR 本文） |
| D8 | 独立-4 | advisory | no | inherited | test-power | accepted | express の原文: の行の有無や引用の一致は lint で検査されない（PR 本文の限界に書いた） |
| D9 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文に Skill RED-GREEN Evidence を載せること |
| E1 | 独立-5 | medium | no | self-inflicted | wiring | accepted | express の原文: は表示の前にだけ置き換えるので、autonomy の判断役と事前回答の委任先、別セッションでの再表示には原文が届かない（PR 本文の限界に書く） |
| E2 | 独立-5 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 依頼は「効く範囲は 19 件」で plugin のファイルだけと承認されたが、届くのは正式 GDD の 10 件で、軽いレーン 6 件・GDD 不使用 3 件を除くことの承認は無い。返事を待たない確認として出した |
| E3 | 独立-5 | low | no | self-inflicted | doc-ref | accepted | main が埋める欄の呼び方（原則 7・項目 2・一次表示の 7）と、原文: の置き場所の書き方が 4 か所でそろっていない |
| E4 | 独立-5 | low | no | inherited | wiring | accepted | 相談役の推奨: は subagent が書かない、原文: は main 記入と書く、で main が埋める 2 欄の決まりが違う |
| E5 | 独立-5 | low | no | self-inflicted | request-drift | re-reported | 相談役の本文が指すだけではなく写しとテストになっている（A3 の再掲） |
| E6 | 独立-5 | advisory | no | self-inflicted | test-power | accepted | main 記入の置き換え忘れを機械で検出しない（残れば表示される） |
| E7 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | Codex の 503 の説明を短くした変更で扱いを変えていないことの確かめ方を書くとよい |
