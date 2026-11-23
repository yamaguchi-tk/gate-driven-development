---
lane: L1+
pr: 124
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) + user | a639deb1 | 1 | 0 | 0 | 2026-09-18T15:40+09:00 |
| codex-1 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線） | b883f47b | 1 | 0 | 0 | 2026-09-18T16:08+09:00 |
| 方針メモ-2 | Opus 相談 ×2 (general-purpose, model: opus) + user（安全策 4 の HITL:「設計を見直して」→ PR 単位の台帳案を承認） | b883f47b | 0 | 0 | 0 | 2026-09-18T16:35+09:00 |
| codex-2 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線 + 台帳照合の受理集合） | 1fbaaeae | 1 | 1 | 0 | 2026-09-18T17:05+09:00 |
| 方針メモ-3 | Opus 相談 (model: opus) + Fable 再設計相談 (model: fable, ユーザー指示) + user（安全策 4 の 2 回目の HITL。C2/C3 の直し方を Fable に再検討させ、wildcard 照合を捨てて hit/miss/unknown/unreadable の 4 値、unknown は経路ごとに main の判定へ戻す案 (a′) を承認） | 1fbaaeae | 0 | 0 | 0 | 2026-09-18T17:35+09:00 |
| codex-3 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線 + 4 値の受理集合の対称性） | 6d7d6fe0 | 1 | 0 | 0 | 2026-09-18T17:53+09:00 |
| 方針メモ-4 | Opus 相談 (model: opus) + user（安全策 4 の 3 回目の HITL。Codex 案で続行を承認: step 5 は hit のみ block、root 未解決は miss のみ通す。4 値 × 2 経路を表テストで固定） | 6d7d6fe0 | 0 | 0 | 0 | 2026-09-18T18:05+09:00 |
| codex-4 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線 + 4 値の受理集合の対称性） | 2c725874 | 1 | 0 | 0 | 2026-09-18T18:09+09:00 |
| 方針メモ-5 | Opus 相談 (model: opus) + user（安全策 4 の 4 回目の HITL。ユーザーが「止める」を選択。以後この PR では安全策 4 を発火させず、新しい high・blocking は直さずに PR 本文の限界へ追記） | 2c725874 | 0 | 0 | 0 | 2026-09-18T18:15+09:00 |
| 独立-1 | general-purpose subagent (model: opus, read-only, origin/main からの全差分, 経緯非共有; independent-review.md (a)〜(h) + security) | e2e644ae | 3 | 0 | 3 | 2026-09-18T21:15+09:00 |
| PR後-1 | PR レビュー（ユーザー、Cursor / Grok 4.6）。ユーザーの「レビュー指摘に対応して」の指示で修正 | 729dbafa | 1 | 1 | 0 | 2026-09-18T21:38+09:00 |
| PR後-2 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線 + gh-resolved の受理集合と (c) の対称性） | f6499b53 | 3 | 0 | 0 | 2026-09-18T21:55+09:00 |
| 独立-2 | light-lane-independent-reviewer (model: opus, effort: max, read-only, e2e644ae からの差分, 経緯非共有; independent-review.md (a)〜(h) + security。差分より前からの high 4 件（C5・I1〜I3 と同じ）は再計上しない) | f6499b53 | 1 | 1 | 1 | 2026-09-18T22:10+09:00 |
| 独立-3 | light-lane-independent-reviewer (model: opus, effort: max, read-only, f6499b53 からの差分, 経緯非共有; independent-review.md (a)〜(h) + security) | 7cb6acdf | 2 | 0 | 2 | 2026-09-18T22:45+09:00 |
| 独立-4 | light-lane-independent-reviewer (model: opus, effort: max, read-only, 7cb6acdf からの差分（変更断片の文言のみ）, 経緯非共有; independent-review.md (a)〜(h) + security) | 28710efb | 2 | 1 | 2 | 2026-09-18T23:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ-1 | high | yes | self-inflicted | non-gdd-merge-judgement | fixed | 当初案の通す条件（候補ループで marker が見つからない）では、git 不在や git rev-parse 失敗のときに marker repo への merge が無検査で通る。git に頼らない祖先方向の marker 探索に変更し、git 失敗・git 不在の再現テストを先に追加 |
| C1 | codex-1 | high | no | self-inflicted | repo-flag-target-unchecked | fixed | _mg_outside_gdd_merge が -R / PR URL の対象 repo を見ず、非 git cwd から -R <GDD 管理 repo> N が無検査 exit 0（方針メモ-1 で案 A として承認済みの限界と同じ面。安全策 4 の HITL でユーザーが設計見直しを指示し、方針メモ-2 で pre-PR gate が書く PR 台帳と merge gate の 2 経路での owner/repo+番号照合に変更） |
| pm-2 | 方針メモ-2 | - | - | - | - | - | なし |
| C2 | codex-2 | high | yes | self-inflicted | ledger-target-resolution | fixed | 複数 merge の連結でパーサが unresolvable=true にして番号を消す一方 repo_flag は最後の merge の値を残し、台帳照合が最後の repo で絞られて先頭の GDD PR が無検査で通る（gh pr merge -R acme/infra-gdd 7 && gh pr merge -R acme/other 8） |
| C3 | codex-2 | medium | yes | self-inflicted | ledger-target-resolution | fixed | ENV_REPO_CONFLICT（GH_REPO）で明示の -R も捨てて repo を何にでも一致させるため、GH_REPO 付きの Renovate -R merge が別 repo の同番号の GDD PR で誤 block される |
| pm-3 | 方針メモ-3 | - | - | - | - | - | なし |
| C4 | codex-3 | high | no | self-inflicted | ledger-unreadable-step5 | fixed | step 5（git cwd の marker 不在）経路で台帳の unreadable を hit と同じく block しており、main が無条件に通していた merge を、台帳・無関係な state.md が読めない・HOME 未設定のときに新たに止める（誤 block 側。不変条件「hit 以外は main と同じ」に反する） |
| pm-4 | 方針メモ-4 | - | - | - | - | - | なし |
| C5 | codex-4 | high | yes | self-inflicted | ledger-unreadable-step5 | deferred | 台帳走査が読めない state.md を見つけた時点で unreadable を返し、後続の state.md の hit を隠す。step 5 は unreadable を通すので、台帳に hit する GDD PR が root checkout から無検査で通る。.steering 自体が読めないと glob が空で miss に落ちる |
| pm-5 | 方針メモ-5 | - | - | - | - | - | なし |
| I1 | 独立-1 | high | yes | self-inflicted | ledger-target-resolution | deferred | 先頭 0 の PR 番号（gh pr merge -R acme/infra-gdd 007）が parser では番号として通り、台帳照合は文字列比較で 7 と一致せず miss。gh は 007 を 旧#7 として扱うので、非 git cwd から台帳に載った GDD PR が通る（止める選択後のため未修正） |
| I2 | 独立-1 | high | yes | self-inflicted | ledger-target-resolution | deferred | remote.origin.gh-resolved しか見ないため、fork 構成（remote.upstream.gh-resolved=base）で gh が upstream を対象にしても origin（fork）で照合して miss。cd <fork> && gh pr merge 7 が非 git cwd から通る。変更断片の set-default の記述とも不一致（止める選択後のため未修正） |
| I3 | 独立-1 | high | yes | self-inflicted | ledger-unreadable-step5 | deferred | 台帳パスがディレクトリだと -r が真でリダイレクト失敗が「or true」に吸われて miss、FIFO だと read が待ち続けて timeout。変更断片の「台帳が読めないときは root 未解決の経路で止まる」と不一致（止める選択後のため未修正） |
| I4 | 独立-1 | low | no | self-inflicted | ledger-growth | accepted | 台帳の行が剪定されず増え続け、state.md ごとの awk 起動で hook の 10 秒 timeout に近づく余地がある |
| I5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | _mg_ledger_verdict の見出しコメントが unreadable を「止める」と書いたまま（step 5 は通す） |
| R1 | PR後-1 | high | yes | self-inflicted | ledger-target-resolution | fixed | remote.origin.gh-resolved が base 以外（gh repo set-default 後の owner/repo 形。origin と同じ repo でも）だと _repo が空で unknown になり、step 5 は hit だけ止めるため root checkout からの gh pr merge 7 が台帳に載った GDD PR でも通る。origin と一致するなら origin で照合するよう 3 組解決 (c) と揃えた |
| R2 | PR後-1 | medium | no | self-inflicted | test-power | fixed | test_cd_into_repo_without_marker_passes は台帳ファイルが無いときにしか成立せず、AC-2 の定常状態（台帳あり）を測っていない。台帳ありで origin を持つ clone が通るテストを追加し、origin の無い clone が止まる点を限界に追記 |
| X1 | PR後-2 | high | yes | self-inflicted | ledger-target-resolution | deferred | fork 構成で origin 以外の remote を見ない（I2 / 旧#127 と同じ。独立-2 の H1 の修正で root 未解決の経路は閉じた） |
| X2 | PR後-2 | high | yes | self-inflicted | ledger-unreadable-step5 | deferred | 読めない state.md が後続の hit を隠す（C5 / 旧#125 と同じ） |
| X3 | PR後-2 | high | yes | self-inflicted | ledger-target-resolution | deferred | 先頭 0 の PR 番号が台帳と一致しない（I1 / 旧#126 と同じ） |
| J1 | 独立-2 | high | yes | self-inflicted | ledger-target-resolution | fixed | R1 の修正で origin の gh-resolved が origin 自身の slug のとき origin で照合するようにした結果、upstream にも gh-resolved がある clone で非 git cwd からの cd && gh pr merge 7 が block から素通しに変わった。origin 以外の remote に gh-resolved があれば origin の値によらず unknown にした（旧#127 の root 未解決の経路も閉じる） |
| J2 | 独立-2 | medium | no | self-inflicted | test-power | fixed | != base の条件を落とす変異が台帳経路のどのテストでも落ちない。set-default のテストに base を追加し、ミューテーション 3 種が落ちることを確認 |
| J3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | set-default 後は owner/repo の形がよくあるという頻度の主張に根拠が無い。変更断片とテストのコメントから外した |
| J4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | AC-2 の満たすが広すぎる（set-default が別 repo・解釈できない clone も台帳があると止まる）。変更断片と PR 本文の限界を揃えた |
| J5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 389 行のコメントの特定できないは不正確（解決値が有効な slug ならそれを対象にできる）。判定を変える広い側の案は後続 |
| J6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文 Summary の hit だけを新たに止め、それ以外は main と同じが、root 未解決の経路の miss を通す緩和を書いていない。PR 本文を直した |
| K1 | 独立-3 | high | yes | self-inflicted | ledger-target-resolution | deferred | どの remote にも gh-resolved が無く upstream 等を持つ fork の clone へ非 git cwd から cd && gh pr merge 7 すると、台帳照合は origin で miss になり通る。非対話の gh は upstream を選ぶ見込み（未実測）。止める選択後のため未修正、限界に追記 |
| K2 | 独立-3 | high | yes | inherited | ledger-target-resolution | deferred | 3 組解決 (c) は origin の gh-resolved しか読まず、fork の GDD worktree（upstream=base）で steering が origin 側の PR のとき gh pr merge 5 が承認検査を通るが gh は upstream の 旧#5 を merge しうる。main から同じ。止める選択後のため未修正 |
| K3 | 独立-3 | advisory | no | self-inflicted | product | accepted | 他の remote の gh-resolved を unknown にせず解決すれば fork の限界が閉じる。gh の解決規則を真似るかは後続 |
| K4 | 独立-3 | advisory | no | inherited | doc-claim | accepted | _mg_ledger_verdict の見出しコメントが unreadable を止めると書いたまま（I5 と同じ） |
| L1 | 独立-4 | high | yes | inherited | ledger-target-resolution | deferred | K1 / 旧#135 と同じ（payload cwd の形も同じく通る） |
| L2 | 独立-4 | high | yes | inherited | ledger-target-resolution | deferred | K2 / 旧#136 と同じ。どの remote にも gh-resolved が無い fork の GDD worktree でも起き、(c) だけ直しても閉じない変種がある |
| L3 | 独立-4 | medium | no | self-inflicted | doc-claim | fixed | 限界の残りが 2 つという数え不足、旧#136 の範囲と payload cwd の形の欠落。変更断片と Issue 旧#136 の本文を広げた |
| L4 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | gh repo clone <fork> が upstream に gh-resolved を書く前提を未実測と断っていない。変更断片に明記 |
| L5 | 独立-4 | advisory | no | inherited | doc-claim | fixed | 旧#126・旧#128 が変更断片の限界に無く、C5 に 旧#125 の番号が無い。追記 |
