---
lane: L1
pr: 457
follow_up_of: 450
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 62c37a97 | 0 | 5 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9abff0cd | 0 | 2 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1-M1 | 独立-1 | medium | no | self-inflicted | product | fixed | merge-tree の失敗が $(…) と head -n 1 で隠れ、空の --workflows-ref で黙って head から読む。commit: 9abff0cd |
| F1-M2 | 独立-1 | medium | no | self-inflicted | product | fixed | rebase の判定の件名比較が、GitHub の messageHeadline の切り詰め（…）で外れ、^1 に戻る。commit: 9abff0cd |
| F1-M3 | 独立-1 | medium | no | self-inflicted | product | fixed | MMC1 で起動するの行の run が 600 秒現れないとき・待ちの条件の gh が失敗したときの扱いが無い。commit: 9abff0cd |
| F1-M4 | 独立-1 | medium | no | self-inflicted | product | fixed | run をマージ commit で探すので、pull_request closed の run が見つからない。script 失敗時の待ちが最初の 1 本で終わる。commit: 9abff0cd |
| F1-M5 | 独立-1 | medium | no | self-inflicted | product | fixed | gh も失敗した分岐の報告が POST_MERGE_DONE_RE に当たり、確認が済んでいないのに marker が消える。ユーザーの選択（D）で、決まった 1 行で未了を報告して止まり、限界の節に書く。commit: 9abff0cd |
| F1-L1 | 独立-1 | low | no | self-inflicted | product | fixed | merge-tree の無い git で既定ブランチに後から足された workflow が出ないことを、確認なしに限界にした。commit: 9abff0cd |
| F1-L2 | 独立-1 | low | no | self-inflicted | product | fixed | completion-check の 11 に fetch が無い。commit: 9abff0cd |
| F1-L3 | 独立-1 | low | no | self-inflicted | product | fixed | completion-check の 11 の括弧が HEAD の workflow から読むと書いたまま。commit: 9abff0cd |
| F1-L4 | 独立-1 | low | no | self-inflicted | product | fixed | script の docstring 冒頭が head の workflow を読むと書いたまま。commit: 9abff0cd |
| F1-L5 | 独立-1 | low | no | self-inflicted | product | fixed | issues の types が無いときも理由が types に closed があるになる。commit: 9abff0cd |
| F1-L6 | 独立-1 | low | no | self-inflicted | product | fixed | types が空の list のとき起動しないになる（push の空 list は起動しうる）。commit: 9abff0cd |
| F1-L7 | 独立-1 | low | no | self-inflicted | product | fixed | wait-until を前面で 600 秒待つと Bash の上限を超えうる。commit: 9abff0cd |
| F1-L8 | 独立-1 | low | no | self-inflicted | product | fixed | --workflows-ref のテストが tree の OID・空文字を通らず、UTF-8 でないパスのテストが bytes を固定しない。commit: 9abff0cd |
| F1-L9 | 独立-1 | low | no | self-inflicted | product | fixed | Merge Report Cleanup Trigger が一覧を作れなかったときを対象外と読める。commit: 9abff0cd |
| F1-L10 | 独立-1 | low | no | self-inflicted | product | fixed | 旧#450 の断片の ^1・止まるの記述と、この PR の断片が食い違う。commit: 9abff0cd |
| F1-L11 | 独立-1 | low | no | inherited | product | fixed | post-merge-qa の 5 の squash と rebase の見分け方が MMC1 の決め方を指していない。commit: 9abff0cd |
| F1-A1 | 独立-1 | advisory | no | self-inflicted | product | fixed | 断片の type は minor が妥当（新しい CLI オプション）。commit: 9abff0cd |
| F1-A2 | 独立-1 | advisory | no | self-inflicted | product | fixed | repo のパスと既定ブランチ名が UTF-8 でなくても落ちないことが PR 本文・断片に無い。commit: 9abff0cd |
| F2-M1 | 独立-2 | medium | no | self-inflicted | product | accepted | script が失敗したときの gh run list --created が workflow・commit で絞らず、他の PR の run まで拾い、引き直しに上限が無い |
| F2-M2 | 独立-2 | medium | no | self-inflicted | product | accepted | 理由の欄に event 名が出ず、push と pull_request closed の両方を持つ workflow が push の行として --commit だけで探される |
| F2-L1 | 独立-2 | low | no | self-inflicted | product | accepted | 起動しうるの行ごとに前面で 540 秒順に待ち、k 行で k×540 秒かかる |
| F2-L2 | 独立-2 | low | no | self-inflicted | product | accepted | wait-until の最悪の所要が 600 秒で Bash の上限と同じで余白が無い。Codex・Cursor での形が無い |
| F2-L3 | 独立-2 | low | no | self-inflicted | product | accepted | PR Body Merge-Triggered Workflows Check の deploy の確認が --commit に固定のまま |
| F2-L4 | 独立-2 | low | no | self-inflicted | product | accepted | phase-progression の監視の対象が一覧のままで、一覧を作れないときの run を含まない |
| F2-L5 | 独立-2 | low | no | self-inflicted | product | accepted | 断片と PR 本文に post-merge-qa の 3 の探し方の変更が無い |
| F2-L6 | 独立-2 | low | no | self-inflicted | product | accepted | 旧#450 の断片の置き換えの句で、版の節に古い記述と打ち消しが並ぶ。post-merge-qa の 3 は止まるまま |
| F2-L7 | 独立-2 | low | no | self-inflicted | product | accepted | 起動するの行が 124 のときに決まった報告の行（gh が失敗）が実態と合わない |
| F2-L8 | 独立-2 | low | no | self-inflicted | product | accepted | 足した route の分岐（rebase 判定・探し方の分け・失敗時の監視）の件数か未測が PR 本文に無い |
| F2-A1 | 独立-2 | advisory | no | self-inflicted | product | accepted | mergedAt の取り方が無く、--created が Z の日時を受けるかは未確認 |
| F2-A2 | 独立-2 | advisory | no | self-inflicted | product | accepted | docstring の判定できない形の列挙に空の types が無い |
| F2-A3 | 独立-2 | advisory | no | self-inflicted | product | accepted | 「どちらかが消したものは出さない」は modify/delete では起動しうるで出る |
| F2-A4 | 独立-2 | advisory | no | self-inflicted | product | accepted | wait-until の docstring に前面で起動する使い方が無い |
| F2-A5 | 独立-2 | advisory | no | self-inflicted | product | accepted | --merge-with が空の分岐はテストが固定していない（冗長な分岐） |
| F2-A6 | 独立-2 | advisory | no | self-inflicted | product | accepted | テストの既定値が list の型に tuple、if __name__ の前の空行が 1 行 |
| F2-A7 | 独立-2 | advisory | no | self-inflicted | product | accepted | 断片の Validation から validate-plugin.sh の行が消えた |
