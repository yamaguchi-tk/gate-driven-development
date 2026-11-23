---
lane: L1
pr: 344
follow_up_of: 337
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d726e5457db8ffecd9695be834b256e1ee7c8c8b | 0 | 1 | 0 | 2026-10-04T01:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 「ファイルは chmod 600」が steering の書き込み検査の counter に当たらない（umask のまま）。counter が書き込み先の絶対パスを平文で持つことも書いていない。限界に書いた |
| M2 | 独立-1 | low | no | inherited | product | accepted | counter のファイルだけが chmod せず絶対パスを持ち、同じ state dir の秘匿水準を下回る（実装側）。限界に書いた |
| M3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | last-turn-failure.json の中身（error_details・timestamp）と、消える条件（project が一致したときなど）が実装より狭く書かれている。限界に書いた |
| M4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 4 の箇条書きと表が食い違う（StopFailure の行が無い、Write/Edit の行に counter が無い、gdd-dev.local.md が Bash の行にだけある）。限界に書いた |
| M5 | 独立-1 | low | no | inherited | doc-claim | accepted | SessionStart の行に、TMPDIR の診断ログの書き込みと settings.json などの読み取りが無い。限界に書いた |
| M6 | 独立-1 | low | no | inherited | product | next-pr | SessionStart の診断ログが固定名で、TMPDIR の無い共有 Linux ホストでは利用者の間でぶつかる（実装側）。次の PR |
| M7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | GDD_HOOK_STATE_DIR を保存先としてだけ書き、台帳と counter が gate の判定にも使われることを書いていない。限界に書いた |
| M8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | gh pr view の照会がいつ走るか（active を問わず push のたび、許可より前）を書いていない。PR 本文に列挙 |
| M9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 案内の hook のログを「gate のログ」に含めている。PR 本文に列挙 |
| M10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の Summary が counter・主語の変更などを書き漏らしている。PR 本文に列挙 |
| M11 | 独立-1 | advisory | no | inherited | doc-claim | accepted | § 1 の「skill 自体は外部通信しない」と § 通信境界の「skill は gh を実行する」が食い違って見える。PR 本文に列挙 |
| M12 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 「ファイルシステム操作と stdout/stderr 出力のみ」に、StopFailure・Notification のデスクトップ通知が入っていない。PR 本文に列挙 |
| M13 | 独立-1 | advisory | no | inherited | doc-claim | accepted | § 監査証跡に、state dir のログと台帳（ローテーションなし）が無い。PR 本文に列挙 |
