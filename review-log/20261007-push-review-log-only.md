---
lane: L1+
pr: 400
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（実測: 9/17 以降の main の transcript で、PR が OPEN の branch への push 214 件・62 セッションのうち、直前のレビューの後に commit が無いものは 14 件、GDD を使う別の repo では 70 件中 65 件がレビューしていない tip の push。push の 63% は commit と push を 1 コマンドにし、208 件中 120 件は push の前に編集・テストなどを置いていた。main の案は PostToolUse でレビューの記録を書く方式だった。Opus は、session の cwd と作業先の worktree が違う repo で記録を取り違えること、background の Agent の起動の ack で記録が立つことを挙げ、push の時点で transcript を読む方式を推奨した。ユーザーは push を単独のコマンドにさせることを受け入れなかったので、main は判定を git の pre-push hook に移す案を出し、Opus は差し込み方を SessionStart の CLAUDE_ENV_FILE に変える案を推奨した。main は実測（git 2.54 の設定による pre-push hook が GIT_CONFIG_* だけで動き、元の hook と husky も動き、exit 1 で push が止まる。CLAUDE_ENV_FILE の env は main・background・subagent の Bash に届く）の後にこれを採った。過去の push の再生では、tip が分かった 52 件のうち止める側が 46 件。ユーザーは、general-purpose のレビューを数えないこと、deny の理由文で再試行の規則に足りること、PR1 を log-only にして数日のログで確かめてから PR2 で止めることを選んだ。食い違いは残らないので max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-07T11:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2e79dace50f7b6ad49594e7248a4e72bd5ea4910 | 0 | 4 | 0 | 2026-10-07T15:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9a9c0a3a37af0015460581b5a4bd13019113ae17 | 0 | 1 | 0 | 2026-10-07T16:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| R1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | env file の hook のコマンドが、消えた script を指すと push を止める。script が無ければ何もしない形にした。commit: 9a9c0a3a |
| R1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | PR の無い branch が gh-unknown になる。gh pr list の open の件数で引く。commit: 9a9c0a3a |
| R1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 起動に失敗・中断した reviewer を完了と数える。成功で終わったものだけを数える。commit: 9a9c0a3a |
| R1-4 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | docs/SECURITY.md の hook の境界（外部通信の例外・SessionStart の書き込み先・state dir の一覧）が合わない。commit: 9a9c0a3a |
| R1-5 | 独立-1 | low | no | self-inflicted | product | fixed | 数字だけの branch 名を PR 番号として解決する。gh pr list --head で解消。commit: 9a9c0a3a |
| R1-6 | 独立-1 | low | no | self-inflicted | product | fixed | remote の URL を使わず gh の既定の repo に問い合わせる。github.com の remote から owner/repo を取り、それ以外は not-github。commit: 9a9c0a3a |
| R1-7 | 独立-1 | low | no | self-inflicted | product | fixed | gh を PATH で探す。絶対パスでなければ gh-unknown。commit: 9a9c0a3a |
| R1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | README の SessionStart の行が新しい hook に触れていない。commit: 9a9c0a3a |
| R1-9 | 独立-1 | low | no | self-inflicted | product | fixed | パスの許可リストに合わない session が何も記録されない。not-installed の 1 行を書く。commit: 9a9c0a3a |
| R1-10 | 独立-1 | low | no | self-inflicted | product | fixed | reviewer の判定が部分一致。許可リストの完全一致にした。commit: 9a9c0a3a |
| R1-11 | 独立-1 | low | no | self-inflicted | product | fixed | 同じ 1 秒の中の前後を取り違える。commit 時刻の次の秒から数える。commit: 9a9c0a3a |
| R1-12 | 独立-1 | low | no | self-inflicted | product | fixed | ログに判定の決め手が残らない。session・by・agents を足した。commit: 9a9c0a3a |
| R1-13 | 独立-1 | low | no | self-inflicted | test-power | fixed | main・background・subagent の Bash に効く証拠が無い。PR 本文に実測を書き、zsh で source するテストを足した。commit: 9a9c0a3a |
| R1-14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の記述が差分と合わない。commit: 9a9c0a3a |
| R1-15 | 独立-1 | low | no | self-inflicted | test-power | fixed | env file が無い場合のテストが何も確かめていない。commit: 9a9c0a3a |
| R1-16 | 独立-1 | low | no | self-inflicted | test-power | fixed | git が設定による hook を持たないとテストが黙って skip。CI では fail にし、SessionStart のテストを skip しないクラスに移した。commit: 9a9c0a3a |
| R1-17 | 独立-1 | low | no | self-inflicted | test-power | fixed | git の hook 側の kill switch と宣言の読み方の一部にテストが無い。commit: 9a9c0a3a |
| R1-18 | 独立-1 | low | no | self-inflicted | test-power | fixed | 元の pre-push hook に stdin が届くことを確かめていない。commit: 9a9c0a3a |
| R1-19 | 独立-1 | low | no | self-inflicted | product | fixed | 新しいログが state dir の権限の規定に従っていない。0600 にした。commit: 9a9c0a3a |
| R1-20 | 独立-1 | low | no | self-inflicted | product | fixed | ref ごとに gh と transcript の読み込みを繰り返す。transcript は 1 回、ref は 10 本まで。commit: 9a9c0a3a |
| R1-21 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | .gdd-config.md の説明が広すぎる。commit: 9a9c0a3a |
| R1-22 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 限界の「core.hooksPath を上書きすると hook が動かない」は誤り（実測で動く）。PR 本文の限界を直し、テストで固定した。commit: 9a9c0a3a |
| R1-23 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | GDD_PUSH_REVIEW_GH_BIN が書かれていない。docstring にテスト用と書いた。commit: 9a9c0a3a |
| R1-24 | 独立-1 | advisory | no | self-inflicted | product | fixed | 全体を除外する exempt の値が通る。英数字を含まない値を受け付けない。commit: 9a9c0a3a |
| R1-25 | 独立-1 | advisory | no | self-inflicted | product | accepted | 次の止める側の PR が、今動いている session にすぐ効く（env file の hook は plugin の script を毎回読む）。PR 本文に列挙 |
| R1-26 | 独立-1 | advisory | no | self-inflicted | product | accepted | タイムゾーンの無い時刻の読み方が、ほかの実装と違う。PR 本文に列挙 |
| R2-1 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「止める側の版は動いている session にもすぐ効く」が、版つきの cache のパスと矛盾する。限界の文を直した。commit: なし（PR 本文） |
| R2-2 | 独立-2 | medium | no | self-inflicted | product | next-pr | 起動応答が読めない background の reviewer が、通知の前に reviewed になる |
| R2-3 | 独立-2 | low | no | self-inflicted | product | next-pr | tip の後の reviewer が running・failed だと、exempt-only を見ずに would-deny になる |
| R2-4 | 独立-2 | low | no | self-inflicted | product | next-pr | GitHub の remote の判定が狭い（pushurl・insteadOf の別名・SSH の host の別名） |
| R2-5 | 独立-2 | low | no | self-inflicted | test-power | next-pr | reviewed_point の `- 1` を消してもテストが通る |
| R2-6 | 独立-2 | low | no | self-inflicted | test-power | next-pr | gh の stub が引数を見ないので、`--json number --jq length` を消してもテストが通る |
| R2-7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | hooks.json の description が許可リスト・成功・github.com に追随していない |
| R2-8 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | SECURITY.md:106 の state dir の作り方が新しい 0700 と食い違う |
| R2-9 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | skipped・not-installed の行の空の欄と、not-installed の行が SessionStart のたびに増える |
| R2-10 | 独立-2 | low | no | self-inflicted | product | next-pr | REVIEWERS に独立レビューでない reviewer が入っている |
| R2-11 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | .gdd-config.md の説明が、文書を外した理由を書いていない |
| R2-12 | 独立-2 | low | no | self-inflicted | product | next-pr | 宣言の行の解析が Markdown の構文の列挙で、行の途中の HTML コメントと 4 つのバッククォートを取りこぼす |
| R2-13 | 独立-2 | low | no | self-inflicted | product | next-pr | _judge の外の例外が error の行を残さない。isdigit が全角の数字を通す |
| R2-14 | 独立-2 | low | no | self-inflicted | product | next-pr | test_hooks_kill_switch の _run_hook が CLAUDE_ENV_FILE を落とさない |
| R2-A1 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文・断片に無い外から見える挙動（unsafe-hook-path、ログの欄、GDD_PUSH_REVIEW_GH_BIN）。PR 本文に列挙 |
| R2-A2 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | CLAUDE_ENV_FILE の実測の手順と結果が PR 本文に無い。PR 本文に列挙 |
| R2-A3 | 独立-2 | advisory | no | self-inflicted | product | accepted | nudge と PR の有無の問い合わせが違う（fork から upstream への PR）。PR 本文に列挙 |
| R2-A4 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | REVIEWERS の名前を agent 定義と突き合わせるテストが無い。PR 本文に列挙 |
| R2-A5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | SECURITY.md の表に git の hook の読み取り範囲が無い。PR 本文に列挙 |
| R2-A6 | 独立-2 | advisory | no | self-inflicted | product | accepted | ms が hook 全体の時間を含まない。repo の hash が worktree ごとに分かれる。PR 本文に列挙 |
| R2-A7 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | CI でないと、git の hook のテストが全部 skip しても緑になる。PR 本文に列挙 |
| R2-A8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片に git の版の目安が無い。PR 本文に列挙 |
| R2-A9 | 独立-2 | advisory | no | self-inflicted | product | accepted | kill-switch.sh の setlocale の警告が push の出力に出うる。PR 本文に列挙 |
