---
lane: L1+
pr: 579
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 3c60fd151f62cef91870287a5c834c1890653f10 | 0 | 0 | 0 | 2026-10-24T17:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2cbf6ae8071e023d1bd4c88b27fcfcc98304b5d0 | 2 | 4 | 2 | 2026-10-24T19:10+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 2cbf6ae8071e023d1bd4c88b27fcfcc98304b5d0 | 0 | 0 | 0 | 2026-10-24T19:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 451ded199e63daa8361b09cb6d8149d4687d0237 | 0 | 0 | 0 | 2026-10-26T10:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| m1-1 | 方針メモ-1 | low | no | self-inflicted | design | fixed | 2 本とも、宣言と CODEOWNERS は既定ブランチの側だけを読む（PR が設定を変えれば組み込みの集合に当たるので、head の側を読んでも広がらない）と推奨。採った（commit: 80b02563） |
| m1-2 | 方針メモ-1 | low | no | self-inflicted | design | fixed | 2 本とも、git check-ignore は repo の .gitignore・info/exclude・global の設定を混ぜるので、空の一時 repo で一致の出どころを確かめるよう推奨。CODEOWNERS の `!`・`[`・`\` の行は exit 2。採った（commit: 80b02563） |
| m1-3 | 方針メモ-1 | low | no | self-inflicted | design | fixed | 組み込みに `.claude/settings.json` を入れるかで割れた（Opus は入れる・Fable は入れない）。agent の権限と hook を決めるファイルで `.gdd-config.md` と同じ種類、当たるのは 213 件中 1 件なので、広い側の入れる案を採った（commit: 80b02563） |
| m1-4 | 方針メモ-1 | low | no | self-inflicted | design | fixed | Fable の推奨で、1 問の先頭に `必ず人が見るファイル: <n> 件` の行を置き、効果を後から数えられるようにした。Opus の推奨で、想定しない例外も exit 2 にした（commit: 80b02563） |
| m1-5 | 方針メモ-1 | low | no | self-inflicted | scope | accepted | human check の時点（変更予定ファイルが集合に触れるとき）の表示は入れない。2 本とも、依頼に無く、マージの時点の判定で人に回ることは閉じるので、黙った縮小ではないと答えた。PR 本文の限界に書く |
| r1-1 | 独立-1 | high | yes | self-inflicted | declaration-values | fixed | 列挙: 設計: 変える（宣言だけ別の方言〔Deploy Paths の GitHub の glob〕で照合していた。CODEOWNERS と同じ gitignore の照合器に一本化し、値は許可リストで閉じた。方針メモ-2 の (a)）宣言の値を拒否リストでしか確かめず、空白区切り（`terraform/ infra/`）・末尾の `/`・バッククォート・波括弧・`#` の値が何にも当たらないまま exit 0 になる（list-human-review-files.py:133）。方針メモ-2 で (a)〜(c) を決める。commit: 451ded19 |
| r1-2 | 独立-1 | high | yes | self-inflicted | head-binding | fixed | 設計: 変える（判定とマージの head を定めていなかった。headRefOid に固定し、自走・人に問う経路とも --match-head-commit でマージし、--head を必須にした）判定に渡す head とマージする head が結び付いていない。push の後に別の commit が積まれると、ローカルの HEAD で exit 0 のまま GitHub の新しい head をマージする（post-merge-qa.md:19,27）。commit: 451ded19 |
| r1-3 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | autonomy.md:9 の「止める側に倒す」が、キーの綴り・大文字小文字の違う行まで含むように読めるが、script はキーの部分文字列が無ければ宣言なしにする |
| r1-4 | 独立-1 | medium | no | self-inflicted | test-power | accepted | .gitignore の隔離のテストは、無視されたファイルが commit されず差分が空なので、実装によらず通る。.gitignore が CODEOWNERS の当たりを隠す向きのテストも無い |
| r1-5 | 独立-1 | medium | no | self-inflicted | product | accepted | 確認済み（2026-10-26、推奨の案）: 依頼の原文は「repo ごとに宣言する」で、宣言の無い repo にも効く組み込みの集合と CODEOWNERS を足した範囲の拡大をユーザーが確かめた記録が無い。request.md に「9・10」の指す文の引用も無い |
| r1-6 | 独立-1 | medium | no | self-inflicted | product | accepted | 確認済み（2026-10-26、推奨の案）: human check の時点で「触れたらマージは人に問う」を出さない縮小を、ユーザーが確かめた記録が無い |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 手順 2 の「このときだけ `Merge Approval` を問わない」の前に 2 文を挟み、「このとき」が人の承認の後を指すようにも読める |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文が、exit 2 のときも件数と当たったファイルを並べると書いている（post-merge-qa は `判定できない` と理由） |
| r1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | operation-levels.md:63 の、既定ブランチから読む宣言の一覧に `GDD Human Review Paths` が無い |
| r1-10 | 独立-1 | low | no | self-inflicted | product | accepted | 組み込みの集合が `.claude/hooks/**` と、`.github/actions` の外のローカル action を守らない。PR 本文の件数は hooks を数えていない |
| r1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 説明の文にキーの名前を書くと 2 行と数えて exit 2 になり、理由に気づきにくい |
| r1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 損失 0 件のまま発火条件を足す理由（依頼による）が、目的の節に書かれていない |
| m2-1 | 方針メモ-2 | low | no | self-inflicted | declaration-values | accepted | r1-1 は (a)。入力者はユーザーで、隣のキー `GDD Push Review Exempt Paths: review-log/ plugins/*/changelog.d/` が指摘の形（空白区切り・`dir/`）で書かれている（1 件）。2 本とも、宣言の値を CODEOWNERS と同じ gitignore の規則で照合し、区切りはカンマか空白、値は許可リストで閉じる案を推した。許可リストに実データ（既存の 2 値）を当てて誤 block 0 件。木に当たらない値を止める案は、まだ無いパスを先に守る宣言を止めるので採らない |
| m2-2 | 方針メモ-2 | low | no | self-inflicted | head-binding | accepted | r1-2 は、head を `gh pr view --json headRefOid` に固定し、自走・人に問う経路とも `--match-head-commit` でマージする。Opus は `--head` の必須化、Fable はローカルの HEAD と違えば止めることを足し、両方採った |
| m2-3 | 方針メモ-2 | low | no | self-inflicted | product | accepted | r1-5 は 2 本ともこのまま（表の行 9 が CODEOWNERS と CI の workflow を名指ししている）。request.md に行 9・10 の引用を足した。r1-6 は割れた（Opus は足さない、Fable は human-check-template.md:507 に 1 文足す）。旧#576 が同じ段落を触っているので足さずに進め、ユーザーに確かめる |
| r2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | post-merge-qa.md:27 で、足した 2 文（headRefOid と --match-head-commit）が「exit 0」の文と「1 か 2 なら」の間に入り、「1 か 2」が script の終了コードを指すと読みにくい |
| r2-2 | 独立-2 | low | no | self-inflicted | declaration-values | accepted | 空白を区切りにしたので、`docs/My Docs/` のような空白を含むパスの宣言は 2 つに分かれ、何にも当たらず exit 0 になる（list-human-review-files.py:128）。区切りをカンマだけにすれば exit 2 になる |
| r2-3 | 独立-2 | low | no | self-inflicted | test-power | accepted | 出どころの欄（CODEOWNERS／宣言）を固めるテストが無く、CODEOWNERS と宣言を同時に置くテストも無い（list-human-review-files.py:115、test_list_human_review_files.py:62） |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | post-merge-qa.md:19 と変更断片は「CODEOWNERS と同じ書き方」とだけ書き、許可リスト（英数字と `._*-`）が狭いことを書いていない。`?` や ASCII でない名前は exit 2 になる |
| r2-5 | 独立-2 | low | no | self-inflicted | product | accepted | 確認済み（2026-10-26、推奨の案）: 人に問う経路（followup の Merge Approval）のマージ全部に head の固定（headRefOid・--match-head-commit）を広げたのは、依頼の範囲より広く、ユーザーの確認が無い（gdd-pr-review-followup/SKILL.md:237） |
| r2-6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | post-merge-qa.md:27 と SKILL.md:237 の `gh pr merge <PR> --match-head-commit <sha>` にマージ方式の引数が無く、TTY の無い Bash ではそのままでは失敗する |
| r2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文に「ローカルの HEAD と違えば止まる」「断られたら Collect に戻る」の一部が書かれていない |
| r2-8 | 独立-2 | advisory | no | inherited | head-binding | accepted | 同じ手順の list-merge-triggered-workflows.py:458 は `--head` が今も HEAD に倒れる。手順がローカルの HEAD と PR の head の一致を求めるので、今は実害が無い |
| r2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 両方に当たるファイルの出どころの表示が、CODEOWNERS から宣言に変わった（後勝ち）。docstring と PR 本文に書いていない（list-human-review-files.py:140-144） |
| r2-10 | 独立-2 | advisory | no | self-inflicted | declaration-values | accepted | 末尾が `/` のパターンは submodule（gitlink）のパスそのものに当たらない。GitHub の CODEOWNERS と挙動はおそらく同じ |
| r2-11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | post-merge-qa.md:37 の、main の手順だけで守る条件の並びに head の固定（--match-head-commit）が無い |
| r2-12 | 独立-2 | advisory | no | self-inflicted | product | accepted | 確認済み（2026-10-26、推奨の案）: root CLAUDE.md:219 は損失 0 件の発火条件を足さないとし、例外は未測をユーザーが確かめたときだけ。PR 本文の「依頼による例外」を、損失 0 件と知ったうえでユーザーが確かめた記録が無い |
