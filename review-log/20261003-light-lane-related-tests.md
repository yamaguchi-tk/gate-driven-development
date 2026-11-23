---
lane: L1
pr: 304
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4950f4325007e73b776c454981f9ab333b29e26a | 0 | 1 | 0 | 2026-10-03T19:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 07b6fbaf0d0d8d25dfd849e84773a1d80e13f929 | 0 | 0 | 0 | 2026-10-03T20:25+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| J1 | 独立-1 | medium | no | self-inflicted | product | fixed | 手順 3 の `$tests` は zsh では改行で分かれず、2 本以上のテストを pytest に渡せない。`--run` でスクリプトが pytest を起動する形にした commit: 07b6fbaf |
| J2 | 独立-1 | low | no | self-inflicted | product | fixed | git の失敗が「関係するテストなし」と同じ exit 1 になる。git の失敗は 2 にした commit: 07b6fbaf |
| J3 | 独立-1 | low | no | self-inflicted | product | fixed | 改名の元の名前で引かない。`--no-renames` にした commit: 07b6fbaf |
| J4 | 独立-1 | low | no | self-inflicted | product | fixed | `.` で始まる名前が空になって捨てられる。先頭の `.` を除いてから切る commit: 07b6fbaf |
| J5 | 独立-1 | low | no | inherited | product | fixed | marketplace.json と japanese-reply-guard の変更で、japanese-reply-guard のテストが出ない。GDD 以外の plugin を変えたらその plugin のテストを出す commit: 07b6fbaf |
| J6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「手で組み立てない」と「全部入れる・広げる」がぶつかる。`-- <テストのパス…>` で足せると書いた commit: 07b6fbaf |
| J7 | 独立-1 | low | no | self-inflicted | test-power | fixed | テストの名前（staged・helpers）と確かめる範囲がずれ、exit 1 を固定していない。テストを足した commit: 07b6fbaf |
| J8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Affected Files にスクリプトと root CLAUDE.md が無い commit: 07b6fbaf |
| J9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring の出す範囲と名前の切り方がコードと合っていない commit: 07b6fbaf |
| J10 | 独立-1 | advisory | no | self-inflicted | product | fixed | git の出力を `-z` なしで読む。`-z` にした commit: 07b6fbaf |
| J11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文に手順 3 のコマンドの形が無い commit: なし（PR 本文） |
| K1 | 独立-2 | medium | no | self-inflicted | product | next-pr | `--` で足したテストが、列挙 0 件のときと `--run` なしのときに捨てられる |
| K2 | 独立-2 | medium | no | inherited | product | next-pr | helper（`tests/_*.py`）経由でだけ部品を名指しするテストを拾わない（root-branch guard で 6 本、merge gate で 17 本） |
| K3 | 独立-2 | low | no | self-inflicted | product | next-pr | `--run` の終了コード 1・2 が pytest の終了コードと重なる |
| K4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | aws-investigate の `tests/` は validate-plugin.sh だけで、規則の文面とスクリプトが合わない |
| K5 | 独立-2 | low | no | self-inflicted | product | next-pr | ほかの plugin のテストが残す `__pycache__` を untracked の変更と数える |
| K6 | 独立-2 | low | no | inherited | product | next-pr | repo root に subdirectory を渡すと黙って「関係するテストなし」になる |
| K7 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | fixture の `.gitignore` の中身 `x` が `skills/x/` を無視させる。PR 本文に書く |
| K8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | テスト名が assert の範囲より広い。PR 本文に書く |
| K9 | 独立-2 | advisory | no | self-inflicted | product | accepted | `--run` で選んだテストの一覧が出ない。PR 本文に書く |
| K10 | 独立-2 | advisory | no | inherited | doc-claim | accepted | よくある名前（CLAUDE など）で多く選ぶことが限界の節に無い。PR 本文に書く |
| K11 | 独立-2 | advisory | no | inherited | doc-claim | next-pr | CLAUDE.md:96 と copilot-instructions の CI の説明に japanese-reply-guard の pytest が無い |
