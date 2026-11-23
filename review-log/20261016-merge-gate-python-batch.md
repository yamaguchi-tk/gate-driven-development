---
lane: L1+
pr: 530
follow_up_of: 527
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | a9e7bae0 | 0 | 2 | 0 | 2026-10-16 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 6239d7229d8267ceb48ebf1a61eabaf8d00343e9 | 2 | 1 | 2 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2a0d71b8d5200b715429bc38d4233a31e0ddf3ae | 0 | 2 | 0 | 2026-10-16 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 82ea3f9f74ee50ce4a89b420a47203ed5b77d104 | 0 | 0 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| m-1 | 方針メモ | medium | no | self-inflicted | design | accepted | 2026-10-16 にユーザーが「A　今の形」と答えた。時刻の覚え書きの表をやめ、parser が検証で作った epoch を出力の変数で返して使い回す形にする（Opus・Fable とも）。_mg_elapsed_seconds も date -u +%s との引き算に替える。commit: なし（方針メモ） |
| m-2 | 方針メモ | medium | no | self-inflicted | request-scope | fixed | 2026-10-16 にユーザーが「B　Fable案」と答え、書き方を 8 進の \0NNN に替えた。cwd の抽出を解析の python にまとめる案を落とさない（Opus・Fable とも）。書き方は \xHH（Opus）と 8 進（Fable）で割れ、bash 3.2 で両方とも戻ることを確かめて \xHH を採った。commit: 82ea3f9f |
| r1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | gh_command_parse を import できないと tool_input の cwd・workdir が bash に届かず、プロセスの cwd が marker の無い repo なら merge が素通りする（この差分が別の python3 の抽出を消した退行）。再現テストを先に書き、変更前の hook では止まることも確かめた。commit: 2a0d71b8 |
| r1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 最上位の cwd も、解析の import か例外で落ちると届かない（前からある穴。同じ埋め込みの python の中）。hook_cwd の emit を gh_command_parse の import より前に移した。commit: 2a0d71b8 |
| r1-3 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 2026-10-16 にユーザーが「止めて良い」と答えた。依頼の「python3 の呼び出しをまとめて」に対し、field ごとの時刻の変換（約 990 回）と steering の解決（約 1,030 回）の python3 が残るのに、依頼より狭い範囲として書いていない。PR 本文の限界に場所と回数を書き、この範囲で止めた（推奨は止める。Fable は止める、Opus は時刻の変換もまとめる） |
| r1-4 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の原文が、返事の指す PR 旧#527 の問い 1〜3 と推奨の案の文を写していない。PR 旧#527 本文から引いて添えた。commit: e2814bb1 |
| r1-5 | 独立-1 | low | no | self-inflicted | test-power | accepted | python3 の起動回数を上限（5 以下）で見ており、経過の分の assert が理由の code・key に結び付いていない |
| r1-6 | 独立-1 | low | no | self-inflicted | test-power | accepted | 待機の経過を計る epoch が Last Review Push At のものか Bot Review Received のものかを、どのテストも区別しない（既存のテストは両方に同じ時刻を置く） |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd_mg_within_minutes のコメントが、hook から呼ばれなくなった後も鮮度判定に使うと書いている（今はテストだけが呼ぶ） |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の「判定は変えていない」が、秒未満の時刻での最大 1 秒の境界のずれと合わない |
| r1-9 | 独立-1 | low | no | self-inflicted | test-power | accepted | 列挙: cwd の受け渡しのテストが、read ループの見出しと起動の環境を写しで持ち、bash 3.2 の printf -v の挙動は bash 3.2 の手元でしか踏まない（CI は bash 5） |
| r1-10 | 独立-1 | advisory | no | self-inflicted | product | accepted | cwd の受け渡しのテストが、payload ごとに bash と python3 を 1 組ずつ起こす |
| r1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 起動回数と時間の、変更の前後の数が PR 本文と断片に無い。PR 本文に python3 の起動回数の前後を書いた。commit: なし（PR 本文） |
| r1-12 | 独立-1 | advisory | no | inherited | product | accepted | 同じ tool_input の cwd を、pre-PR gate（文字列だけ・~ と $VAR を展開）と merge gate（str にしてそのまま）が違う規則で受ける（前からある非対称） |
| r2-1 | 独立-2 | medium | no | self-inflicted | fail-open | accepted | hook_cwd の import 失敗だけを内側の try で握りつぶすので、lib の故障の扱いが 2 通りに割れる（gh_command_parse の故障は parse-error で止まり、hook_cwd の故障はプロセスの cwd で判定を続ける）。block から allow に変わるのは、root checkout に marker と新しい証跡がある通常でない構成だけ |
| r2-2 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | PR 本文の目的「判定は変えない」が、lib の故障と解析の例外のときに最上位の cwd の repo で止めるようになった挙動と合わない。目的を、変わる範囲を書いた形に直した。commit: なし（PR 本文） |
| r2-3 | 独立-2 | medium | no | self-inflicted | request-scope | re-reported | r1-3 の再報告（残る python3 を依頼より狭い範囲として残す。ユーザーが止めてよいと答えた） |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「判定は変えていない」が、lib の故障のときの判定の変化を書いていない |
| r2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の件数を測った sha が書かれていない。sha を書いた。commit: なし（PR 本文） |
| r2-6 | 独立-2 | advisory | no | self-inflicted | style | accepted | hook のファイルが、この巡の差分で 1,498 行から 1,503 行になり、1,500 行の目安を超える（main の 1,506 行からは減っている） |
| r2-7 | 独立-2 | advisory | no | self-inflicted | product | accepted | 足したテストが、subTest ごとに git repo を 2 つ作り、hooks/ を写している |
| r3-1 | 独立-3 | advisory | no | self-inflicted | product | accepted | 要約: なし |
