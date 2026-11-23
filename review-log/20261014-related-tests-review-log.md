---
lane: L1
pr: 500
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f1a51e8d | 0 | 1 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | PR 本文が 旧#476 をこの穴のせいにしていたが、旧#476 の行は 旧#454 自身の断片と対で、validate-plugin.sh の review-log-present.sh が既に見ていた。最後のローカルの確認の後に review-log だけの commit を積んだ経路で漏れた。PR 本文の目的と限界を直した。commit: なし（PR 本文） |
| F2 | 独立-1 | low | no | self-inflicted | test-power | accepted | RECORD_CHECK の実物を改名・移動すると、is_file() で黙って選ばなくなり、契約テストは fixture で通る |
| F3 | 独立-1 | low | no | self-inflicted | product | accepted | 列挙: changelog.d/ の分岐で足す test_review_log_present は実 repo の断片を読まず、断片を読む test_merge_approval_vocabulary_leak.py は選ばれない |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | テストの module docstring に新しい選び方が無い |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary・Changed が GDD の changelog.d/ に限ることを書いていない。「配布物は変えていない」はテストを変えたことと合わない |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | script の docstring の「名前の一致では選ばれない」は、README などの名前では選ばれるので言い切りが広い |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の発火の件数に数とコマンドが無い |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | root CLAUDE.md 手順 3 と CONTRIBUTING.md に新しい選び方が無い |
| A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | 選ばれるテストは全 review-log を検査するので時間がかかり、main 由来の壊れた記録でも落ちる |
| A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | GDD 以外の plugin に changelog.d/ は今は無い |
| A4 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの x.md という名前が部分一致で別のファイルに当たりうる |
