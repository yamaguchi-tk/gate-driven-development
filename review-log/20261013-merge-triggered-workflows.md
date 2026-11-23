---
lane: L1
pr: 450
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0f77b1e3 | 0 | 7 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | a400489e | 1 | 0 | 1 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 236f37fa | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1-M1 | 独立-1 | medium | no | self-inflicted | product | fixed | 非 ASCII を含むパスが quotePath で引用符つきになり、paths に当たらず起動しないになる。commit: a400489e |
| F1-M2 | 独立-1 | medium | no | self-inflicted | product | fixed | 差分が空だと filter の無い on: push まで起動しないになる。マージ後に PR の branch で実行すると差分が空になる。commit: a400489e |
| F1-M3 | 独立-1 | medium | no | self-inflicted | product | fixed | PR 本文の一覧は PR 作成前の 1 回だけで古くなるが、マージ後の手順がそれを使う。commit: a400489e |
| F1-M4 | 独立-1 | medium | no | self-inflicted | product | fixed | push 以外の event（pull_request の closed、workflow_run）でマージ時に起動する workflow を起動しないと断定する（依頼の「判定できない形は起動しうる」から外れる）。commit: a400489e |
| F1-M5 | 独立-1 | medium | no | self-inflicted | product | fixed | post-merge-qa の 3 で、起動しうるの行の run が現れないと blocked で止まる。commit: a400489e |
| F1-M6 | 独立-1 | medium | no | self-inflicted | product | fixed | gdd-pr-review の PR 本文チェックの列挙に新しいチェックが無い。commit: a400489e |
| F1-M7 | 独立-1 | medium | no | self-inflicted | product | fixed | post-merge-qa の 2 の 起動: と Merge Approval の問いが一覧につながっていない。commit: a400489e |
| F1-L1 | 独立-1 | low | no | self-inflicted | product | fixed | post-merge-qa の 3 がデプロイ系でない workflow の success も条件にする（依頼はデプロイ系の完了確認）。commit: a400489e |
| F1-L2 | 独立-1 | low | no | self-inflicted | product | fixed | DIFF_LIMIT 3000 に出典が無い（reviewer は 300 と推測。docs は 3,000 で、出典を docstring に書いた）。commit: a400489e |
| F1-L3 | 独立-1 | low | no | self-inflicted | product | fixed | git 以外の例外で exit 1 になり途中までの行だけ残る。手順は exit 2 しか扱わない。commit: a400489e |
| F1-L4 | 独立-1 | low | no | self-inflicted | product | fixed | 呼び出しが --default-branch を渡さず、origin/HEAD の無い clone で branches の filter が判定できない。commit: a400489e |
| F1-L5 | 独立-1 | low | no | self-inflicted | product | fixed | on の中の push と関係ない節が読めないと、push の無い workflow も起動しうるになる。commit: a400489e |
| F1-L6 | 独立-1 | low | no | self-inflicted | product | fixed | completion-check の 11 が条件付きに読める・express で走らない・未コミットの変更が漏れる。commit: a400489e |
| F1-L7 | 独立-1 | low | no | self-inflicted | product | fixed | 引用符の無い値の途中の ' を引用の始まりと数え、コメントや , を読み違える。commit: a400489e |
| F1-L8 | 独立-1 | low | no | self-inflicted | test-power | fixed | +・[]・\・上限・branches-ignore の ! を壊しても落ちるテストが無い。commit: a400489e |
| F1-L9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring と PR 本文の判定できない形の書き方が実装と合わない。commit: a400489e |
| F1-L10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に書いていない挙動がある。commit: なし（PR 本文） |
| F1-L11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片が新しく止まる条件を書いていない。commit: a400489e |
| F1-L12 | 独立-1 | low | no | self-inflicted | product | fixed | phase-progression の manual merge continuation が一覧を指していない。commit: a400489e |
| F1-A1 | 独立-1 | advisory | no | self-inflicted | product | fixed | ! だけの paths と ! だけの branches で扱いが違う。commit: a400489e |
| F1-A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | stacked の PR では base と branch の判定がマージ先と合わない |
| F1-A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | README の Scripts の表に新しい script が無い |
| F1-A4 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の新しい条件の件数の書き方が root CLAUDE.md の形になっていない。commit: なし（PR 本文） |
| F2-H1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | post-merge-qa の 3 がマージ commit を fetch せずに script を呼び、0 以外で終わったときの分岐が無い。確かめる run が 0 件のまま QA に進みうる。commit: 9e20ce9f |
| F2-M1 | 独立-2 | medium | no | self-inflicted | product | next-pr | rebase merge では <sha>^1...<sha> が PR の全 commit の差分にならない |
| F2-M2 | 独立-2 | medium | no | self-inflicted | product | next-pr | Manual Merge Continuation の 1 に run の出現を待つ手順が無く、直後に見て空なら監視から外れる |
| F2-M3 | 独立-2 | medium | no | self-inflicted | product | next-pr | PR 作成後の push で一覧を作り直す規定が、push する gdd-pr-review-followup に届いていない |
| F2-L1 | 独立-2 | low | no | self-inflicted | product | next-pr | issues の closed と merge_group はマージで起動しうるのに NOT_ON_MERGE に入っている |
| F2-L2 | 独立-2 | low | no | self-inflicted | product | next-pr | UTF-8 でないパスが理由の欄に入ると print が UnicodeEncodeError で exit 1 になる |
| F2-L3 | 独立-2 | low | no | self-inflicted | product | next-pr | マージ前の一覧は PR の head の workflow だけを読み、既定ブランチに後から足された workflow が出ない |
| F2-L4 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 値の途中の引用符のテストが閉じない引用符の検査でも通り、足した検査を固定していない |
| F2-L5 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 3,000 超の paths-ignore と既定ブランチ不明の branches-ignore を固定するテストが無い |
| F2-L6 | 独立-2 | low | no | self-inflicted | product | next-pr | gdd-using-git-worktrees の Merge Report Cleanup Trigger が確かめる workflow を一覧に結んでいない |
| F2-L7 | 独立-2 | low | no | self-inflicted | product | accepted | push 以外の event まで読み起動しうるにするのは、依頼の on.push より語の範囲が広い。依頼の原文から外れたという指摘なのでユーザーに確かめ、A（今のまま）が選ばれた。request.md に足した |
| F2-L8 | 独立-2 | low | no | self-inflicted | product | fixed | gdd-pr-review のチェックを手順 4 の全 Check にし、依頼に無い Advisory Findings Check まで広げた。新しいチェックだけを足す形に戻した。commit: 9e20ce9f |
| F2-A1 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 理由の欄の ` / ` のつなぎ方・on.push なしの形・パスの置き換えが PR 本文に無い |
| F2-A2 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | 未測の文を限界の節にも書く。commit: なし（PR 本文） |
| F3-M1 | 独立-3 | medium | no | self-inflicted | product | next-pr | Manual Merge Continuation の 1 の「止まる」が、manual merge continuation の Stop hook（報告文で marker が消える・監視を促す）とぶつかる |
| F3-M2 | 独立-3 | medium | no | self-inflicted | product | next-pr | post-merge-qa の 2 の 起動: だけ、script が 0 以外で終わったときの扱いと fetch が無い |
| F3-M3 | 独立-3 | medium | no | self-inflicted | product | re-reported | rebase merge では --base <merge commit>^1 が最後の 1 commit の差分しか見ない（F2-M1 と同じ） |
| F3-L1 | 独立-3 | low | no | self-inflicted | product | next-pr | gdd-pr-review の列挙に Advisory Findings Check が無く、この skill から直接作る PR では止まらない |
| F3-A1 | 独立-3 | advisory | no | self-inflicted | style | accepted | fetch の書き方が git fetch と git fetch origin --quiet でそろっていない |
