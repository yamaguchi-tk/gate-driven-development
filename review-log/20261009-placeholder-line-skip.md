---
lane: L1+
pr: 418
follow_up_of: 415
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) | b8c51591 | 0 | 0 | 0 | 2026-10-09 |
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承, CLAUDE.md・memory 入り | b8668150 | 1 | 0 | 1 | 2026-10-09 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 45445acc | 0 | 0 | 0 | 2026-10-09 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | low | no | inherited | design | fixed | 案 C（placeholder の例外を外す）を推奨。main の案と一致。実測: steering 1,599 ファイルの placeholder を含む 230 行で新しく止まる行 0、transcript の steering への書き込み 45,373 回で placeholder と実パスが同じ行に並び素通りした行 2（2026-09-03）。ユーザーへの確認は、内部相談で進めてよいというユーザーの発言（2026-10-08）に従い、内部相談で代えた。commit: なし（方針の記録） |
| M2 | 方針メモ | low | no | inherited | design | fixed | `Active Worktree Path` の語を含む行も、行全体でパスの検出を飛ばす（同じ形の穴）。実測で該当 0 行（steering・transcript とも）。この PR の外。独立-1 の I1 で high として出たので、この PR で直した。commit: a9424ce5 |
| I1 | 独立-1 | high | yes | inherited | fail-open | fixed | `find_local_path` の `Active Worktree Path` の例外が部分文字列一致で、語を含む表の行・本文の行にある別の絶対パスも素通りする。欄の行（ラベルと値だけ）の fullmatch に限った。transcript の steering への書き込みでこの語を含む 51 行のうち、表の行に絶対パスを書いた 4 行が新しく止まる（止めるべき形）。commit: a9424ce5（テストは 72c8cef9） |
| I2 | 独立-1 | low | no | self-inflicted | test | fixed | deny 文の案内のテストの説明が、`${CLAUDE_PLUGIN_ROOT}` を勧める faq と噛み合わない。値の書き換えと plugin のファイルの指し方を分けて書いた。commit: 72c8cef9 |
| I3 | 独立-1 | low | no | self-inflicted | docs | fixed | 0.44.0 の後の断片 `20261008-crosscheck-followup.md` の placeholder の理由が、この変更の後は当たらない。この PR の断片の Summary に明記した。commit: a9424ce5 |
| I4 | 独立-1 | advisory | no | self-inflicted | test | fixed | テスト名 `…_instead_of_crashing` が実際の確かめより広い。`…_are_denied_too` に改名した。commit: 72c8cef9 |
| I5 | 独立-1 | advisory | no | inherited | process | accepted | 読み込みの照合で候補が 83 行（`wc -l` は 82）。候補ファイルの末尾に改行が無く、`wc -l` が最後の行を数えないためで、中身は同じ。次の巡から候補ファイルの末尾に改行を足す |
| I6 | 独立-2 | low | no | self-inflicted | product | accepted | `Active Worktree Path` の欄の行の例外が受理する形（`-` か箇条書きなし・`:` 区切り・1 語の値）は、同じ欄を読む lint（`*` の箇条書き・`=` 区切り・空白を含む値も読む）より狭い。止める側への非対称で、旧 metadata のその書き方は止まる |
| I7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `tests/test_stop_hook_validate.py:100` の docstring が、語を含む行全体が通るという変更前の挙動を説明したまま |
| I8 | 独立-2 | advisory | no | self-inflicted | request | fixed | 依頼の原文は placeholder の穴だけを挙げていて、`Active Worktree Path` の例外を欄の行に絞る変更と、`self-contained-contract.md` の security 契約の文の変更は依頼に無い範囲。ユーザーに確かめ、含めてよいとの回答を `.request.md` に足した。commit: なし（依頼の原文） |
