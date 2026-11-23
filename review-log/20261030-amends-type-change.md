---
lane: L1+
pr: 622
amends: 20261030-simplifier-sonnet.md, 20261013-merge-intent-followup.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) + user | f4c00568 | 0 | 0 | 0 | 2026-10-30T17:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4d8edc35 | 0 | 0 | 0 | 2026-10-30T18:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1-1 | 方針メモ | advisory | no | self-inflicted | design | fixed | 採用: 案 W（amends: で宣言した断片の type 不変の条件を外す）。2 本とも W、main の案と同じ。type 不変の FAIL は transcript で 0 件、type を変える必要は 45 件中 1 件。ユーザーへの確認は返事を待たずに W で進める。commit: f4c00568 |
| M1-2 | 方針メモ | advisory | no | self-inflicted | wiring | fixed | 宣言の無い type の変更が FAIL になるテストを足し、type 不変のテストを両方向で通る形に反転する。commit: f4c00568 |
| M1-3 | 方針メモ | advisory | no | self-inflicted | doc-claim | fixed | 未リリースの 20261013-merge-intent-followup.md の「type: の変更は今までどおり FAIL」と、検査の docstring・VERSIONING.md の受理範囲も直す。commit: f4c00568 |
| M1-4 | 方針メモ | advisory | no | self-inflicted | doc-claim | fixed | VERSIONING.md の問いを、既にある gate の表・警告・reference を変えた model に合わせて直しただけのときに限ると書き、MINOR の境目とぶつけない。commit: f4c00568 |
| r1-1 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 決着（2026-10-30 ユーザー: 残す）: VERSIONING.md の問いの見出しから「だけ」を外し、既にある dispatch gate の表・警告・reference を直しただけのときも PATCH という今後の PR に効く規則を足した。依頼の「patch に直す」に規則として残すことまで含むかが 2 通りに読める。ユーザーが残すと決めた（VERSIONING.md:201, 203） |
| r1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「宣言の無い書き換え・削除・改名は FAIL」が、中身を変えない改名は通ることと食い違う（changelog.d/20261030-amends-type-change.md:11、version-not-consumed.sh:373, 518） |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary の「これまでは type を変える書き換えは FAIL だった」が、リリースされたことのない状態を基準にしている（changelog.d/20261030-amends-type-change.md:7, 11） |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が、breaking を下げると Breaking Contract Changes の節も外せること、版数の記述が v0.x の話であること、件数を書いていない。commit: なし（PR 本文） |
| r1-5 | 独立-1 | advisory | no | self-inflicted | product | accepted | 外した検査は HEAD を読んでいたが、層 A は作業ツリーを読む（version-not-consumed.sh:239） |
| r1-6 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | type 行の無い書き換えのテストが、層 A と層 B のどちらが拒んだかを区別しない（test_changelog_fragment_amends.py:104-107） |
| r1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation に tests/test_changelog_fragments.py が無い |
| r1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の transcript 0 件・45 件中 1 件の数を出したコマンドが記録に無い |
