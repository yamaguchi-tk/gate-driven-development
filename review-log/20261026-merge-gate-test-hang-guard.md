---
lane: L1
pr: 582
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0495135fc4a0b83fd8b796743c14c8629f4a615f | 0 | 2 | 0 | 2026-10-26T18:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 2faee86c67a0d055f4510842ebf96a7f0a37ae48 | 0 | 0 | 0 | 2026-10-26T19:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| c1-1 | 独立-1 | medium | no | self-inflicted | test-power | accepted | 共有 helper の既定を 60 秒にしたので、helper を通る起動から「hook が本番の timeout に収まる」の検査が消えた。helper の中で CPU 時間を見れば残せる |
| c1-2 | 独立-1 | medium | no | inherited | test-power | fixed | 列挙: merge gate hook を直接起動する test_shell_lexer_gates.py:467・test_merge_gate_python_batch.py:278 が literal の 10 秒のまま（origin: pre-existing）。ユーザーの指示（2026-10-26 18:40）でこの PR に入れた（commit: 2faee86c） |
| c1-3 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-27、推奨の案）: 依頼が名指ししたのは gate_activation だけだが、差分は followup の helper・直接の起動・FIFO の 3 本の打ち切りも広げた。推奨（Opus・Fable とも）は範囲を merge gate hook を起動するテストの打ち切りとすること |
| c1-4 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-27、推奨の案）: 依頼の「タイムアウトの偽の失敗」に、ADR X-37 の壁時計 backstop（timeout の半分）の assert が入るかを確かめずに限界に回した。推奨（Opus・Fable とも）はこの PR で変えないこと |
| c1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | コメントの「負荷で HOOK_TIMEOUT を超える」の根拠に最大 8.8 秒を挙げ、超えた観測（全量の 11 件）を書いていない |
| c1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary・契約テストの 1 行目・PR 本文が「hook を起動するテスト全部」を指すが、10 秒・30 秒・literal 60 秒の起動が残る。PR 本文の範囲の書き方を直す（commit: なし（PR 本文）） |
| c1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | test_merge_gate_hook_quoted_operator.py の docstring・docs/learned-patterns.md:17・ADR が「ほかの起動は既定の 10 秒」と書いたままで、明示の timeout=60 は既定と同じ値になった |
| c1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | 列挙: 契約テストは 2 つの helper の既定だけを固定し、直接の起動・FIFO の 3 本の打ち切りを戻しても落ちない |
| c1-9 | 独立-1 | low | no | self-inflicted | test-power | accepted | followup の境界のテスト 2 本は時刻の書き込みから hook の読みまでを 10 秒未満と見込む。60 秒まで待つので、負荷では TimeoutExpired の代わりに assert で落ちうる |
| c1-10 | 独立-1 | low | no | inherited | test-power | out-of-diff | ほかの gate（pre-push・pre-PR・root branch guard）のテストも hooks.json の timeout を壁時計の打ち切りにしたまま（origin: pre-existing。全量 1 回目で該当の失敗は 0 件） |
| c1-11 | 独立-1 | low | no | self-inflicted | style | accepted | 契約テストの setUp の mkdtemp を消さない |
| c1-12 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | PR 本文の限界の行の先頭が Honest Limitations の種類になっていない。PR 本文を直す（commit: なし（PR 本文）） |
| c1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 全量 2 回の結果と実測の測り方が材料に無い。PR 本文の確認したことに書く（commit: なし（PR 本文）） |
| c1-14 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 止まる退行が入ると、helper を通る起動は 1 回ごとに 60 秒待ち、全量の所要時間が延びる |
| c1-15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「長い入力の 3 本」に followup の 旧#3 が入っていない。PR 本文を直す（commit: なし（PR 本文）） |
| c1-16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | _merge_gate_support.py:29 の「超えると PreToolUse は通る」は、通知だけの今の merge gate では「通知が出ない」 |
| c1-17 | 独立-1 | advisory | no | inherited | bookkeeping | out-of-diff | request.md の 1 行目が依頼の由来の注記 |
| c2-1 | 独立-2 | low | no | self-inflicted | request-scope | accepted | PR 本文の問い 1 の戻す範囲に、ユーザーが明示して頼んだ 2 か所が入っている。PR 本文を直す（commit: なし（PR 本文）） |
| c2-2 | 独立-2 | low | no | self-inflicted | test-power | accepted | 列挙: 契約テストは直接起動の 2 か所を固定せず、timeout=10 に戻しても負荷の無い環境では落ちない |
| c2-3 | 独立-2 | low | no | self-inflicted | changelog | accepted | 断片は「利用者から見える変更なし」と書きながら、Changed 節にテストの内部の変更を並べている |
| c2-4 | 独立-2 | low | no | inherited | test-power | out-of-diff | test_shell_lexer_gates.py:236-242 の pre-push gate の assertLess(elapsed, 10) も壁時計を literal 10 秒と比べる（origin: pre-existing） |
| c2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の「2 つの helper」が、python_batch の helper も含むと読める |
| c2-6 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 最後の tip での全量の結果が材料に無い。PR 本文の確認したことに書く（commit: なし（PR 本文）） |
| c2-7 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | この巡を差分（無効化後）として記録する |
| c2-8 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり。PR 本文の抜粋ファイル内の「推奨は…Opus・Fable とも同じ」。次の巡の前に抜粋から除く |
