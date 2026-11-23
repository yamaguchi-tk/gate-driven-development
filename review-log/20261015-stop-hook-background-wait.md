---
lane: L1+
pr: 520
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-10-15 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c4c18940 | 0 | 2 | 0 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 10c0e91d | 0 | 0 | 0 | 2026-10-15 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | fc173f93 | 0 | 2 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | product | fixed | 案 1（in-flight guard の条件に any_background_running を同じ窓で足す）を推す。continuation の誤った押し返し 49 件のうち 26 件は、今のコードの再生で既に止まる（原因の commit は未確認）。案 1 は残りのうち background の Bash を待っていた 7 件を閉じる。失う正しい押し返しは 1 件以下。押し返さない期間に上限は無い（終わらない background の処理では止まったままになる）と限界に書く。ScheduleWakeup・Monitor は足さない。main の案と食い違いは無い。commit: なし（方針） |
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | 依頼の「宣言された待ちの状態で抑える」を、宣言を読まずに、まだ終わっていない background の処理（Bash を含む）の有無で推定している。PR 本文で問い、ユーザーは「許可リスト」と答えた。待ちの形の許可リストに絞った commit: 10c0e91d |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | accepted | ScheduleWakeup・Monitor の待ちと、marker の無いユーザーへの確認の停止を、確認なしに範囲の外にした。PR 本文で問い、ユーザーは「そのまま」と答えた |
| I1-3 | 独立-1 | low | no | self-inflicted | product | accepted | dispatch が返った後に止め忘れた期限 timer があると、満了まで継続を押し返さない（gate-runner は最大 61 分） |
| I1-4 | 独立-1 | low | no | self-inflicted | test-power | accepted | 窓の下限（BACKGROUND_WINDOW_SECONDS - 60 で押し返さない）と未来の時刻を固定するテストが無い |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 同じ規定を書く別の箇所（state-machine.md:49-55・652、setup-gdd-loop.sh:598・622、gdd_stop_hook.py:1268 の押し返しの文）が dispatch の待ちだけのまま |
| I1-6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | PR 本文に、数を出したコマンドと、未測の理由が無い。PR 本文に書いた commit: なし（PR 本文） |
| I1-7 | 独立-1 | advisory | no | self-inflicted | product | accepted | hook-errors の記録名 subagent_in_flight_guard が、実際には background の判定の例外を記録する |
| I1-8 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの fixture の gh pr checks --watch の background 起動は、wait loop gate が拒否する形 |
| I1-9 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの helper（_ago・_bg_bash）が test_stop_hook_autonomy_pushback.py と重複 |
| I1-10 | 独立-1 | advisory | no | inherited | product | accepted | loop state を消す停止の押し返し（wait_watchdog.state_clear_reason）は Agent/Task だけを数え、この変更の後は継続の判定と集合がずれる（差分の前から） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の Validation の「入口から」が例外のテストも含めて読める。押し返しの文の字面が実際と違う |
| I2-1 | 独立-2 | low | no | self-inflicted | product | fixed | wait-until.py の項が、起動の形ではなく語の有無を見ている（cat・grep で触れただけのコマンドも待ちに数える）。依頼の「待ちの形の許可リスト」に合わせ、行頭か ; & パイプの直後で起動する形に絞った commit: 921d9d99 |
| I2-2 | 独立-2 | low | no | self-inflicted | product | accepted | sleep の項の受理範囲が wait_watchdog._TIMER_RE（ASCII・先頭が 0 でない 6 桁まで）と食い違う |
| I2-3 | 独立-2 | low | no | self-inflicted | product | accepted | 止め忘れた期限 timer（sleep 3660）が走る間、marker の無い早すぎる停止を押し返さない（最大約 61 分） |
| I2-4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 負例が wait-until.py の lookbehind を検出していない |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | reference・断片の書き方が実装より狭く、終わらないコマンドで止まったままになる注意書きを消した |
| I2-6 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 計測の measure3.py が repo に無く再現できない |
| I2-7 | 独立-2 | low | no | inherited | doc-claim | accepted | state-machine.md:55 の判定順序に、継続を押し返さない条件が無い（subagent の分は前から無い） |
| I3-1 | 独立-3 | medium | no | self-inflicted | product | accepted | 改行区切り・( ) の中・代入や wrapper・flag 付きの python・絶対パスの python で起動した wait-until.py を待ちに数えず、押し返す（押し返す側に倒れ、PR 前の挙動に戻る） |
| I3-2 | 独立-3 | medium | no | self-inflicted | product | accepted | 空白を含む plugin のパスを shlex.quote でクォートした案内どおりの wait-until.py の起動を待ちに数えず、押し返す |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界に、I3-1・I3-2 の形で起動した wait-until.py も押し返すことが無い |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の件数がどの sha の再生か書かれていない（921d9d99 で再生し直した） |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | コメントと PR 本文の「python3 か path つき」「触れただけのものは数えない」が言い過ぎ（どちらも省略でき、引用符の中の パイプ の直後でも当たる） |
| I3-6 | 独立-3 | low | no | self-inflicted | product | accepted | 空白の無い token に ; & パイプ が密だと正規表現が O(n²) になり、全 launch に先に当てている |
| I3-7 | 独立-3 | low | no | self-inflicted | test-power | accepted | & の区切り・単引用符・python・行末の分岐を当てるテストが無い |
| I3-8 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | reference と断片が起動の位置と形の条件を書いていない |
| I3-9 | 独立-3 | advisory | no | self-inflicted | product | accepted | wait-until.py の直後に空白なしで ; が続く形を待ちに数えない |
| I3-10 | 独立-3 | advisory | no | inherited | product | accepted | sleep の項と wait_watchdog._TIMER_RE の受理集合が違う（I2-2 と同じ） |
