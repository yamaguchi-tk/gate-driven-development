---
lane: L1
pr: 313
follow_up_of: 312
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | bf4bf99cfc9fb535c45a95afd6d0540488bac404 | 0 | 0 | 0 | 2026-10-04T12:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 1f7d29a34d6a6ed4c93f77360000aa21d7c3d785 | 0 | 0 | 0 | 2026-10-04T12:50+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| J1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「検査を起動するテストは HOME を外す」が、env を自分で組む GIT_DIR のテストに当てはまらず、断片にテスト内部の説明が入っている。そのテストにも HOME を外し、断片の文を削った commit: 1f7d29a3 |
| J2 | 独立-1 | low | no | inherited | doc-claim | fixed | `fragment_blobs` の docstring が `git diff --name-only` の出力を changelog.d/ 相対と書いている（実際は top-level から）。直した commit: 1f7d29a3 |
| J3 | 独立-1 | low | no | inherited | product | out-of-diff | `check-no-raw-task-steering.py` は `--root` に subdirectory を渡し、かつ `diff.relative=true` のとき top-level の `.steering/` を見落とす。呼び出し側はどれも top-level を渡しており、実データの該当なし |
| J4 | 独立-1 | advisory | no | inherited | test-power | accepted | `test_review_log_present.py` の `run_check` も開発者の `~/.gitconfig` を検査に通す。PR 本文に書く |
| J5 | 独立-1 | advisory | no | inherited | style | accepted | FAIL のヒントの中で、改名とみなした断片だけが top-level からのパスになる。PR 本文に書く |
| K1 | 独立-2 | low | no | inherited | doc-claim | accepted | `fragment_blobs` の docstring の「changelog.d/ 相対」が、同じ文の「cwd 相対」と同じ読み方をすると `<name>` だけに読め、「prefix」も定義していない。PR 本文の限界に書く |
| K2 | 独立-2 | low | no | inherited | test-power | accepted | `test_review_log_present.py` の検査の起動 3 か所が、開発者の git 設定を外していない（今日壊す設定は無い）。PR 本文の限界に書く |
| K3 | 独立-2 | advisory | no | self-inflicted | style | accepted | GIT_DIR のテストが `run_check` の env を手で書き写している。PR 本文に書く |
| K4 | 独立-2 | advisory | no | inherited | test-power | accepted | テスト側の `git add -A`・`git mv` の一部が GIT_ENV を通さず、開発者の設定を読む。PR 本文に書く |
