---
lane: L1+
pr: 160
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user | - | 0 | 0 | 0 | 2026-09-20T09:55+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 97f145fe1034c0351668cec980e2999dc9384fd9 | 0 | 0 | 0 | 2026-09-20T10:05+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | 方針メモ 3 の「env 側は対象外」は理由が無い。両側 trim は、空白だけの現在 id で block から allow へ反転する fail-open を新設するので採らない、と理由つきに書く（`gdd_session_continuity_ok` と `setup-gdd-loop.sh:137` も片側 trim）。CLAUDE.md の「既定は広い側」に対する説明責任として、狭める理由を書いた |
| P2 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | 方針メモ 4 の対称性テストは、現在の id が空の行で Safe Resume の連鎖と `gdd_session_continuity_ok` が元から一致しないため、そのままでは書けない。範囲を現在の id が非空の入力に限り、空の行は限界として開示した |
| P3 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | 変異が 1 方向（末尾除去の削除）だけだと、全空白を消す過剰な除去を検出できない。値の途中の空白を保持するケースを足した |
| P4 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | 入力の列挙に「ファイル全体が CRLF」が無かった。動機のシナリオ（改行コードを変換した local state）なので、全行 CRLF と単一 CR を別のケースにした |
| P5 | 方針メモ | advisory | no | self-inflicted | memo-wording | accepted | 方針メモ 7 の読み手は 3 つではなく 4 つ（`setup-gdd-loop.sh` 120-137 行のロック検査も、`#` 以降を剥がす別の受理集合）。共有 helper 化は見送るので、4 実装が散在したまま残ることを限界として書いた |
| P6 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | open の PR 旧#156 が同じ if ブロックの別の行（既定ブランチ判定）を変える。マージ後に行番号がずれるので、changelog と review-log は行番号ではなく `STORED_SESSION_ID=` の pipeline のテキストで指す |
| R1 | 独立-1 | low | no | self-inflicted | doc-claim-scope | accepted | 「現在の id が非空なら Safe Resume と `gdd_session_continuity_ok` の結論は一致する」は、`.claude/gdd-dev.local.md` が存在しない入力では成り立たない（前者は Candidate Mode、後者は通す）。表は常にファイルを書くので検知しない。向きは過抑制で実害は無い。限界の条件を「ファイルが存在する入力」に狭めるのは後続 |
| R2 | 独立-1 | advisory | no | self-inflicted | doc-claim-scope | accepted | `session_id` を読む実装は 4 つではなく 5 つ。`scripts/gdd_task_binding.py` の `_frontmatter()`（`---\n` と `---` の行が完全一致）は、CRLF の local state の frontmatter 全体を読み落とす。影響は警告（`invalid_empty_local_session_id`）だけで、block / allow には届かない |
| R3 | 独立-1 | advisory | no | self-inflicted | doc-claim-scope | accepted | 同じ本文で読み手の数が「3 つ（末尾の扱いを比べた実装）」と「4 つ（散在）」に割れている。語で書き分ける |
| R4 | 独立-1 | advisory | no | self-inflicted | doc-claim-scope | accepted | 「Safe Resume を通す側（fail-open）には倒れない」は全称の断定。stored が「現在 id ＋末尾の空白・CR」だと、別 session の state でも通る。runtime はそのような id を作らず、11 箇所の block gate は既に同じ受理集合なので実害は無い。条件付きの文に直すのは後続 |
| R5 | 独立-1 | advisory | no | self-inflicted | doc-claim-scope | accepted | 「この tip で全量が通っている」は差分の中に証跡が無い。実行した sha と結果行は PR 本文に書く |
