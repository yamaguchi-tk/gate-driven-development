---
lane: L1+
pr: 541
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | - | 0 | 1 | 0 | 2026-10-16 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a41773364932641c72c7059ef9ad116dbc2c5521 | 0 | 1 | 0 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | ddaedc5ee89adbfbd5b32203dcdb925456e74088 | 0 | 1 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| m-1 | 方針メモ | medium | no | self-inflicted | design | accepted | 2026-10-16 にユーザーが「OK」と答えた（推奨のとおり）。再開した agent の待ちを数える読み手を、押し返しを抑える 2 つ（Stop hook の継続の押し返しの免除、マージ待ちの押し返しの any_background_running）に限る。wait_watchdog（overdue_reason・state_clear_reason）と git_pre_push_review は変えない。入れると block が増え、その件数を測っていない（Opus は外す、Fable は wait_watchdog も入れる、で割れた。推奨は外す案で進めている）。再開と終わりの通知・TaskStop は行の順に記録し、toolUseResult を読む例外で行ごと失わないようにする（2 本とも）。後でマージ待ちの押し返し 26 件を再生し、当たる 0 件だったので、マージ待ちの側も外した（r1-3）。commit: なし（方針） |
| r1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の「2 の残り」の一部（ScheduleWakeup・Monitor、marker の無いユーザー・CI 待ち、自動 background の Bash）を確認なしに外し、残る 4 件の種類を書いていない。実の parser で測り直すと、ScheduleWakeup の 2 件はこの変更で押し返さなくなり、まだ押し返す 4 件は、完了通知が届いた後の待ち 1、reason の名前を書き違えた marker 1、marker の無いユーザー確認 1、自動で background に回った pytest 1 で、どれも hook がすでに求めている記録で抑えられる形ではない（pytest は 旧#520 でユーザーが選んだ許可リストの外）。PR 本文に種類ごとに書いた。commit: なし（PR 本文） |
| r1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 期限 watchdog・pre-push の判定を数えないことに付けた限界の種類が `依頼より狭い` で逆。`その他` にした。commit: なし（PR 本文） |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | マージ待ちの押し返しの規定（post-merge-qa.md:28・state-machine.md:51・autonomy_pushback.py の docstring）が、再開した agent を書いていない。マージ待ちの押し返し 26 件の再生で当たるのが 0 件だったので、root CLAUDE.md の「当たる件数が 0 なら足さない」に従い、マージ待ちの側の配線を外して規定と一致させた。commit: ddaedc5e |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の 11 件と 13 件の差の説明が無い。差の 2 件は ScheduleWakeup の待ちに分けたもので、同じ時に再開した agent も走っていたと書いた。commit: なし（PR 本文） |
| r1-5 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 件数を測ったコマンドが PR 本文に無い。抽出と再生のコマンドを書いた。マージ待ちの側は 26 件中 0 件と測り、配線を外した。commit: なし（PR 本文） |
| r1-6 | 独立-1 | low | no | inherited | reader-symmetry | accepted | wait_watchdog の state_clear_reason は再開した agent を数えず、走っている間の done・blocked・cancelled を通す（この PR の前から同じ） |
| r1-7 | 独立-1 | low | no | inherited | reader-symmetry | accepted | 時差の無い timestamp を、_timestamp_epoch は数えず、wait_watchdog._epoch・git_pre_push_review._epoch はローカル時刻として読む（今の host は Z 付き） |
| r1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | 自由文だけでは数えないことのテストの本文が agent の id を含まず、本文から id を拾う実装でも通る |
| r1-9 | 独立-1 | low | no | self-inflicted | test-power | accepted | TaskStop の結果で消す行、別の id への TaskStop、queued の完了通知で終わる経路を、テストで固定していない |
| r1-10 | 独立-1 | advisory | no | self-inflicted | product | accepted | 再開を SendMessage の tool_use と結び付けず、どの user 行の toolUseResult も読む |
| r1-11 | 独立-1 | advisory | no | self-inflicted | product | accepted | 再開の後の通知の task-id が agentId かを、repo の fixture で確かめていない（実 transcript では task-id が agentId で、tool-use-id は SendMessage の id だった） |
| r1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の「入口から」の下に、関数を直接呼ぶテストが混ざる。分けて書いた。commit: ddaedc5e |
| r2-1 | 独立-2 | medium | no | self-inflicted | test-power | accepted | マージ待ちの押し返しが再開した agent を数えないことを固定するテストが無く、any_background_running に判定を戻しても全テストが通る |
| r2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation に、名前を変えた直接呼び出しのテスト（test_resume_is_running_until_its_end）が載っていない |
| r2-3 | 独立-2 | advisory | no | inherited | doc-claim | accepted | マージ待ち 26 件の再生（0 件）を、手元で再現する手順が PR 本文に無い |
| r2-4 | 独立-2 | advisory | no | inherited | doc-claim | accepted | PR 本文の誤り 49 件の内訳のうち、今のコードですでに押し返さない 32 件が書かれていない |
