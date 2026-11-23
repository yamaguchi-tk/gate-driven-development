---
lane: L1
pr: 325
follow_up_of: 317
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c363b9c5e9a85737dc897bdbaf93a3299b8db189 | 0 | 1 | 0 | 2026-10-03T21:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f14a5c98cf37e8bcc0a9ad0b134203d12b6cb6a | 0 | 1 | 0 | 2026-10-03T21:40+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | e792ef50d568aa93c6cd77905b97fd6f26b5f1b8 | 0 | 1 | 0 | 2026-10-03T23:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | product | fixed | 注記のディレクトリ glob・全域 glob も pattern に数え、除外の注記で INFO が消えて Step 3c の手照らしが抜ける。注記からは単一ファイルだけを拾う commit: dfb63fc2 |
| F2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 負のテストが注記の語の絞り込みを固定していない。`（v1.2 対応）` とディレクトリ glob・全域 glob の注記のテストを足した commit: 85d8c68f |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 書き込み hook の advisory にも ERROR が出ることが断片と PR 本文に無い commit: 3f14a5c9 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 前の断片を直す一文とコードのコメントが字義のうえで矛盾する。置き換えの形に書き直した commit: 3f14a5c9 |
| F5 | 独立-1 | low | no | inherited | product | accepted | 「」・。・・に接した単一ファイルは、語の区切りが列挙型のため検出しない。開いた入力なので限界に書く |
| F6 | 独立-1 | low | no | inherited | product | accepted | 欄名の注記は入れ子の無い丸括弧 1 つだけを読み、`【】`・太字・2 つの注記は `自走範囲` の行にならない。開いた入力なので限界に書く |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 正本の見出しの形では、欄名の注記を読まない（PR 本文の限界に書く） |
| F8 | 独立-2 | medium | no | inherited | product | fixed | `戻し条件`・`自走範囲外:`・続きの行の `明示的に除外する範囲:` に書いた glob は pattern に数えられ、自由文の自走範囲を検査していないのに INFO が消える。ユーザーの指示で直した。INFO は自走範囲の値・欄名の無い続きの行・glob の欄の glob だけで消す commit: 7e3e6dde |
| F9 | 独立-2 | low | no | self-inflicted | product | accepted | 注記に書いた全域 glob × security-sensitive（`（**/auth/** も含む）`）は WARN にならず、`戻し条件` の同じ glob と扱いが逆になる |
| F10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の、注記で検出する形の説明が実際の規則と合わない。PR 本文で直す commit: なし（PR 本文） |
| F11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `extract_patterns_from_state_md` の docstring が注記の扱いに触れていない |
| F12 | 独立-2 | low | no | self-inflicted | test-power | accepted | 注記の語からクォート・バッククォートを剥がす処理をテストが固定していない |
| F13 | 独立-2 | advisory | no | inherited | product | accepted | 波括弧の固定のファイル集合（`src/foo.{ts,js}`）がカンマで割れ、単一ファイル固定として検出されず INFO も消える |
| F14 | 独立-3 | medium | no | inherited | product | accepted | `自走範囲` の値や欄名の無い続きの行に書いた除外の glob（`リポジトリ全体、src/legacy/** は除く`）は検査した自走範囲に数えられ、INFO が消える。開いた入力なので限界に書く |
| F15 | 独立-3 | low | no | self-inflicted | test-power | accepted | `counts_as_scope` の `scope_line` 条件・注記の単一ファイルを数えないこと・欄名つきの行の lint をテストが固定していない。`GLOB_FIELD_RE` の節は効いていない |
| F16 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Affected Files に `references/rollback-patterns.md` が無い commit: ce8104b6 |
| F17 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片・rollback-patterns の「exit=0」は、`戻し条件` に単一ファイルがあると exit=1 と INFO が一緒に出る挙動より広い |
| F18 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の「欄名の括弧の注記の glob も今までどおり lint する」は、注記から単一ファイルだけを拾う挙動より広い |
| F19 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | ERROR・WARN と一緒に `INFO: no Approved Direction patterns found` が出て、文言が矛盾して見える |
| F20 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | モジュールの docstring の Exit code の説明が、新しい INFO の条件を表していない |
| F21 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 欄名つきの続きの行の glob（`- backend: src/api/**`）で新しく INFO が出ることが User Action Required に無い |
| F22 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | Step 3c の INFO の説明が見出しの形だけを書いている |
