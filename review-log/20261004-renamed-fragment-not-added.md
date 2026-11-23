---
lane: L1
pr: 312
follow_up_of: 310
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f8583948d14a28432a31b15c67047ed714c24334 | 0 | 1 | 0 | 2026-10-04T10:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 9aa223429a1162693e44c6b67aa69033cc2eb318 | 0 | 0 | 0 | 2026-10-04T11:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| G1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 変えたテストが断片を消さなくなり、`--no-renames` を固定するテストが無くなった。消して中身の違う断片を足し、消した断片の FAIL だけが出ることを見る形にした commit: 9aa22342 |
| G2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 新しいテストが `git mv` の成否を見ていない。戻り値を assert した commit: 9aa22342 |
| G3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 改名先を外すことと、外す個数が固定されていない。件数の assert と、同じ中身の自分の断片のテストを足した commit: 9aa22342 |
| G4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Validation が「消した断片」と書くが、テストは消していない。G1 で消す形に戻し、記述を合わせた commit: 9aa22342 |
| G5 | 独立-1 | low | no | self-inflicted | product | fixed | 改名先を外して FAIL したとき、外した理由が出ない。FAIL に改名先を名指しした commit: 9aa22342 |
| G6 | 独立-1 | low | no | self-inflicted | product | fixed | review-log-present.sh は改名先も足した断片とみなし、review-log を求める（FAIL 側のずれ）。コメントに書き、PR 本文の限界に書く commit: 9aa22342 |
| G7 | 独立-1 | low | no | inherited | product | next-pr | 未 commit の断片の名指しは、merge-base に同じ中身があるだけで外し、元が残る同じ中身の自分の断片を名指ししない |
| G8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 限界の「中身を変えて改名したものは数える」は、元の断片の書き換えとして FAIL になることを添えると誤読されない。PR 本文に書く |
| G9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | コメントと断片が「消えた」だけで、書き換わった場合を書いていない。両方を「消えた・書き換わった」にした commit: 9aa22342 |
| G10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | VERSIONING.md の層 B の説明が、改名だけのものを数えないことに触れていない。PR 本文に書く |
| G11 | 独立-1 | advisory | no | inherited | doc-claim | accepted | `fragment_blobs` の docstring が鍵を `git diff --name-only` と同じ形と書くが、実際は cwd 相対。PR 本文に書く |
| G12 | 独立-1 | advisory | no | self-inflicted | style | accepted | run() が 300 行を超えたまま伸び、「残っていない merge-base の断片」の述語が 2 か所にある。PR 本文に書く |
| G13 | 独立-1 | advisory | no | inherited | product | accepted | 利用者の `diff.relative=true` で常に FAIL する（未実測）。PR 本文に書く |
| H1 | 独立-2 | low | no | self-inflicted | test-power | accepted | 同じパスで書き換わった merge-base の断片と同じ中身の改名先を外す側を、固定するテストが無い。PR 本文の限界に書く |
| H2 | 独立-2 | low | no | self-inflicted | test-power | accepted | 消した断片のテストが「消した断片の FAIL だけ」の「だけ」を見ていない。PR 本文の限界に書く |
| H3 | 独立-2 | low | no | inherited | product | re-reported | 未 commit の断片と commit 済みの断片で、改名の判定が違う（G7 と同じ） |
| H4 | 独立-2 | low | no | self-inflicted | style | accepted | Not counted の案内だけが repo root からのパスで、前の案内との区切りが無く、文言が外す条件より広い。PR 本文の限界に書く |
| H5 | 独立-2 | low | no | inherited | test-power | next-pr | 検査の git が開発者の git 設定を読み、`diff.renames=false` で `--no-renames` の固定が効かず、`diff.relative=true` で常に FAIL する |
| H6 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 元を残したコピーと、リリース後の main の取り込みで、自分の断片が無くても通る経路がある。PR 本文の限界に書く |
| H7 | 独立-2 | advisory | no | inherited | doc-claim | accepted | VERSIONING.md と検査の冒頭が、改名先を数えないことを書いていない（G10 と同じ）。PR 本文に書く |
| H8 | 独立-2 | advisory | no | self-inflicted | style | accepted | run() が 300 行を超えたまま伸びた（G12 と同じ）。PR 本文に書く |
