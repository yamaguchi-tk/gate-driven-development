---
lane: L1+
pr: 230
follow_up_of: 222
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。Opus は絶対化の置き場所を cd 後の `$PWD` から hook の python に移すよう推奨し、メインはその実測〔`-P` の root で cd が $HOME へ移る〕に合わせたので、食い違いは残らず Fable は呼んでいない） | - | 1 | 1 | 1 | 2026-09-29T01:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 18e3a488642d50faf8f13d1657e6c8908be9b448 | 2 | 1 | 2 | 2026-09-29T02:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 2e291d17a4d6800056aada6bb395d46d6fbb786a | 3 | 0 | 3 | 2026-09-29T02:45+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火〔root-resolution-miss の high が独立-1・独立-2〕。ユーザーの 2026-09-28 の決定で HITL は内部の相談で代えた。Opus は続行・G2 と G3 を直す・G1 を accepted にして次の PR を推し、メインの案と食い違わなかったので Fable は呼んでいない） | - | 0 | 1 | 0 | 2026-09-29T03:05+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | c1a8a0ea439b73880f6c2732ced9ba2718133a7a | 1 | 0 | 1 | 2026-09-29T03:35+09:00 |
| 方針メモ-3 | 方針メモ-2 で Opus と決めた出口の適用（安全策 4 の再発火〔parse-exception の high が独立-2・独立-3、high の巡が合計 3〕。独立-3 の high は main でも再現する既存の欠陥なので accepted にし、限界の節の先頭に書いて、直す次の PR を続けて出す。出口が事前に決まっているので Opus・Fable への再相談はしていない） | - | 0 | 0 | 0 | 2026-09-29T03:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | high | yes | self-inflicted | relative-project-root | fixed | 草案の `cd` 後の `PROJECT_ROOT="$PWD"` では、`git -C -P push` の `-P` が cd の option になって $HOME へ移り、not-a-git-repo の none で通る。候補 root を hook の python で展開・絶対化してから使う（`-` で始まる root も、絶対パスの cd は CDPATH も見ない） |
| P2 | 方針メモ | medium | no | self-inflicted | relative-project-root | fixed | 空の root（`--git-dir=` の空の値）を絶対化すると process の cwd に化け、`git -C /nongdd --git-dir= push` が通過から unresolvable-root に反転する。空は絶対化せずに飛ばす |
| P3 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | `--git-dir=~/…`・`--work-tree=$HOME/…` の extras も展開され、今は通るものが unresolvable-root で止まる（止める向き）。変更断片に書く。相対パスの root の found・multiple は、今の block から絶対パスと同じ判定に反転する |
| P4 | 方針メモ | advisory | no | inherited | root-resolution-limits | accepted | parser は変えないので残る形: `cd a && cd b`（最後の cd だけを見る）、`cd /abs && git -C rel`、引用符の中の `~`・`$HOME` を hook だけが展開する、hook の env で展開する（セッションの中で export した変数は見えない）、Bash tool のシェルの CDPATH、payload の cwd と hook の cwd の食い違い、`link/..` の字面の解決、nudge hook が展開しない非対称。PR 本文の限界の節に書く |
| F1 | 独立-1 | high | yes | inherited | root-resolution-miss | fixed | step 5 は候補 root の直下の marker しか見ず、`cd repo/sub && git push`・`git -C repo/sub push` を検査せずに通す（② だが § 常時 High）。toplevel と root 自身の marker を見る（12d1c9bf のテスト、fixed in 2e291d17） |
| F2 | 独立-1 | high | yes | inherited | root-resolution-miss | fixed | 先頭の root がディレクトリに解決できない（`cd "$(git rev-parse --show-toplevel)"`・存在しないパス・未定義の変数）と process の cwd を見ずに通す。process の cwd も候補に足す（fixed in 2e291d17） |
| F3 | 独立-1 | medium | no | self-inflicted | root-resolution-miss | fixed | 展開で例外になった root を相対パスのまま返し、except の経路をテストが通っていない。絶対パスにして返し、NUL を含む user 名のテストを足す（fixed in 2e291d17） |
| F4 | 独立-1 | low | no | self-inflicted | test-coverage | fixed | `unset CDPATH` の行を消しても落ちるテストが無い。相対パスで hook を起動するテストを足した（行を消すと落ちることを確認。fixed in 12d1c9bf） |
| F5 | 独立-1 | low | no | self-inflicted | changelog-wording | fixed | 変更断片の Summary が閉じていない形まで閉じたように書いている。閉じた形だけにし、残る形を足す（fixed in 2e291d17） |
| G1 | 独立-2 | high | yes | inherited | root-resolution-miss | accepted | gitdir の中の root（`git -C repo/.git push`・cwd が `repo/.git/hooks`）は `--show-toplevel` が失敗し、marker を見ずに通す。pre-PR gate・merge gate も同じ前提で、gitdir の形（`.git`・`.git/worktrees/<x>`・`--separate-git-dir`・`.git/modules/<sub>`）が開いているので、3 gate の toplevel 解決をまとめる次の PR で直す（方針メモ-2。PR 本文の限界の節の先頭に書く） |
| G2 | 独立-2 | high | yes | inherited | parse-exception | fixed | lone surrogate（`\ud800`）を含む root で python の出力が UnicodeEncodeError になり、root も fallback も出ずに通す。emit を surrogateescape で符号化し、失敗したときだけ backslashreplace にする（a13d4e71 のテスト、fixed in c1a8a0ea） |
| G3 | 独立-2 | high | yes | self-inflicted | root-resolution-miss | fixed | 解決できない cd の fallback が process の cwd だけで、payload の cwd（Codex の workdir）を見ない。優先順の残り（payload の cwd・process の cwd）を足す（a13d4e71 のテスト、fixed in c1a8a0ea） |
| G4 | 独立-2 | low | no | self-inflicted | changelog-wording | accepted | 「cd が失敗すると push は作業ディレクトリで走る」は `&&`・`$(git rev-parse --show-toplevel)` の例で成り立たない（コメント・変更断片・テストのコメント）。2 巡目の low で follow_up_of があるので accepted。G3 の修正で hook のコメントと変更断片の同じ行は書き直した（テストのコメントは触っていない） |
| G5 | 独立-2 | low | no | self-inflicted | test-docstring | accepted | テストの module docstring が、足したテスト（toplevel・fallback・展開の例外・CDPATH）に追随していない。2 巡目の low で follow_up_of があるので accepted |
| S2 | 方針メモ-2 | medium | no | self-inflicted | parse-exception | fixed | メインの G2 案の `sys.stdout.reconfigure(errors="backslashreplace")` は、UTF-8 でない byte のパス（`\udcXX`）を文字どおりに出し、python では isdir が真なので fallback が出ず bash の `-d` で落ちる（Linux）。surrogateescape を先に試し、失敗したときだけ backslashreplace にする（fixed in c1a8a0ea）。独立-3 で同じクラスタが再発したら、main でも再現するものは accepted、この PR が生んだものは revert する |
| H1 | 独立-3 | high | yes | inherited | parse-exception | accepted | pre-PR gate の本文の検査（`run-pre-pr-gate-hook.sh:629`）は、`--body` に lone surrogate があると python の出力が UnicodeEncodeError になって空の本文を見て通す。`--body-file` の値の lone surrogate は `except OSError` を抜けて hook ごと exit 1 になる。main でも同じ（この PR は pre-PR gate を変えていない）。次の PR で直す（方針メモ-3。PR 本文の限界の節の先頭に書く） |
| H2 | 独立-3 | low | no | self-inflicted | test-power | accepted | `emit()` の 1 段目の surrogateescape（UTF-8 でない byte のパス）を突くテストが無い。3 巡目の low で follow_up_of があるので accepted |
| H3 | 独立-3 | low | no | self-inflicted | pr-body-wording | fixed | PR 本文の挙動の変化の行が payload の cwd の fallback に追随していない。PR 本文を直した（差分のファイルではない） |
| S3 | 方針メモ-3 | - | - | - | - | - | なし |
