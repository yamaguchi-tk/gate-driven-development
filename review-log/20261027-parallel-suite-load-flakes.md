---
lane: L1
pr: 587
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0fe1f2ff5b22c4588c13bd7860235dfa6a4e585f | 0 | 1 | 0 | 2026-10-27T14:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 7d7c055fa6f780e790974383fbe183b54d4419a3 | 0 | 1 | 0 | 2026-10-27T14:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| c1-1 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-27、推奨の案 A で直した。commit: 7d7c055f）: Stop hook の押し返しのテストを直さない理由の「本番の秒数を変えずにテストで保証する手は無い」は入口からの e2e にだけ当てはまる。判定の表は merge_wait_reason を in-process で呼び gh の subprocess.run を差し替えれば負荷に依らない。PR 本文の限界の文を直した（commit: なし（PR 本文）） |
| c1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docs/learned-patterns.md:17 が「hook のテストは本番と同じ timeout で起動する」のまま |
| c1-3 | 独立-1 | low | no | self-inflicted | test-power | accepted | 打ち切りを 6 倍にしたテストは、10〜60 秒かかって正しく返す遅さを検出しない。PR 本文の限界に書いた（commit: なし（PR 本文）） |
| c1-4 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-27、推奨の案 A で直した。commit: 7d7c055f）: test_review_followup_nudge_hook_gh.py:131-167 は hooks.json の timeout（8 秒）を壁時計の上限にしたままで、限界にも無い。nudge は gate かが読み方で割れる |
| c1-5 | 独立-1 | low | no | self-inflicted | test-power | accepted | 深いバッククォートのテストは CPU を使わない 10 秒超えの退行を通す。_run に打ち切りが無い |
| c1-6 | 独立-1 | low | no | self-inflicted | test-power | accepted | durations のテストは -c で ini を渡すので、CI と同じ探し方で plugin の pytest.ini が選ばれることを確かめなくなった |
| c1-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | 契約テストは run_root_branch_guard_raw の打ち切りを固定しない |
| c1-8 | 独立-1 | low | no | self-inflicted | test-power | fixed | _reset が hook-errors.log を消さないので、subTest の message に前の subTest の記録が混ざる。in-process の判定（_decide）が呼ぶたびに記録を消す（commit: 7d7c055f） |
| c1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | test_timing_budget_contract.py の冒頭の契約の一覧に hang_guard_seconds が無い |
| c1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR X-37 の Decision 5 と既知の穴の行が、10 秒の既定・timeout の未固定を現在形で書いたまま |
| c1-11 | 独立-1 | low | no | self-inflicted | changelog | accepted | 断片の Summary が残りを全部直したと読め、Affected Files に ADR が無い |
| c1-12 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 並列の全量 2 回の証拠が材料に無い。PR 本文の確認したことに書く（commit: なし（PR 本文）） |
| c1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「テストだけを変えた」に ADR の 1 行が入っていない。PR 本文を直した（commit: なし（PR 本文）） |
| c1-14 | 独立-1 | advisory | no | inherited | style | accepted | _run_pre_pr の既定が literal 20 秒で、同じテストの 2 回の起動の打ち切りの導出元が分かれる |
| c1-15 | 独立-1 | advisory | no | inherited | test-power | out-of-diff | 依頼の 3 の型の外に、壁時計の上限を置くテストが残る（Stop hook の done guard の 8 秒など。全量の失敗には出ていない） |
| c1-16 | 独立-1 | advisory | no | self-inflicted | style | accepted | pre-push gate の打ち切りの定数が 2 つのファイルに別名で置かれ、共有 helper の既定は None のまま |
| c1-17 | 独立-1 | advisory | no | self-inflicted | style | accepted | 2 か所が起動のたびに hang_guard_seconds で hooks.json を読む |
| c2-1 | 独立-2 | medium | no | self-inflicted | request-scope | accepted | test_stop_hook_autonomy_pushback.py:624-627・:654-656 の GuardSurvivesPushbackFailureTest は Stop hook を入口から起動し、壁時計 8.0 秒（hooks.json の timeout 10 秒より短い）を上限にしたまま、限界にも書いていない。依頼の終わりの形のとおり、直さない理由を PR 本文の限界に書いた（commit: なし（PR 本文）） |
| c2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 入口に残した止まる側の 2 本も、締め切りに届くと deadline: の記録で落ちうることが限界に無い。PR 本文に書いた（commit: なし（PR 本文）） |
| c2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の「入口から起動するのは 3 本」は、陽性対照の 1 本を数えておらず 4 本。PR 本文は直した（commit: なし（PR 本文）） |
| c2-4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 列挙: nudge の頭打ちのテストは、前処理を含む hook 全体が 8 秒に収まることを見なくなった |
| c2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | nudge の helper に足した既定の打ち切りを固定するテストが無い |
| c2-6 | 独立-2 | low | no | inherited | test-power | accepted | nudge の hook を helper を通さずに起動する 2 か所（test_review_followup_nudge_hook.py:195-203・test_review_followup_nudge_hook_gh.py:208-216）に打ち切りが無い |
| c2-7 | 独立-2 | low | no | self-inflicted | changelog | accepted | 断片の Summary の nudge の部分が「hooks.json の timeout から 6 倍に替えた」と読め、Changed と合わない |
| c2-8 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 7d7c055f 以降の tip での並列の全量 2 回の結果が材料に無い。PR 本文の確認したことに書く（commit: なし（PR 本文）） |
