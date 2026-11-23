---
lane: L1+
pr: 271
follow_up_of: 270
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#270 の限界に書いた次の PR。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた。Opus は pre-PR gate・pre-push gate・worktree guard を 3 本の PR に分け、worktree guard は「値を正しく取る」〔最後の改行だけ落とす〕で閉じる案を推した。main の案と食い違わず、Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-02T06:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | de51a37d89b603ceb472b8a0d1d079a498d799bd | 3 | 0 | 3 | 2026-10-02T06:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 4ba8e0a2e580baafc70d774b33a10d867f2522ca | 3 | 0 | 3 | 2026-10-02T07:20+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（安全策 4 の発火〔クラスタ path-normalization の high が独立-1・独立-2 の 2 巡。数えた high はすべて origin: pre-existing〕。Opus は「止める」〔3 件を accepted で限界に書き、次の PR を Stop hook → toplevel を `$()` で読む hook 群 → guard の `git -C`・`cd` の順で 3 本〕を推し、信号 ② で呼んだ Fable も賛成した〔差分は fail-closed 側で、マージで新しい fail-open は生まれない〕。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて「止める」を採った。以後の指摘は直さず限界に書く） | - | 0 | 0 | 0 | 2026-10-02T07:35+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| L1 | 独立-1 | high | yes | inherited | path-normalization | fixed | text モードの subprocess が CR を改行に置き換え、名前が CR で終わる・途中に CR を含む toplevel が別のパスになる。bytes で読み、最後の改行だけ落とす commit: cf624436 |
| L2 | 独立-1 | high | yes | inherited | path-normalization | accepted | Stop hook の done guard（gdd_stop_hook.py:117-124 `_worktree_toplevel`）が toplevel を `.strip()` で読み、名前が空白・改行で終わる worktree で done の検査対象を見失う。差分の外の既存の穴。直す次の PR を続けて出す |
| L3 | 独立-1 | high | yes | inherited | path-normalization | accepted | EnterWorktree・Plan mode・skill gate・skill expansion gate の 4 hook と pre-PR gate・pre-push gate・detect-steering.sh が `$(git rev-parse --show-toplevel)` で末尾の改行を落とす。差分の外の既存の穴。直す次の PR を続けて出す |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片・コメント・PR 本文の「最後の改行だけ落とす」が CR では成り立たない。L1 の修正で成り立つようにし、断片に CR を書いた commit: 4ba8e0a2 |
| L5 | 独立-1 | low | no | self-inflicted | style | fixed | テストが起動 fixture の正本（run_root_branch_guard）を使わず、timeout と環境の隔離を落としている。正本に寄せた commit: 929c4115 |
| L6 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の「どれも 1 行の出力」、断片の core.ignorecase の書き方、逆向きの変化（同名の repo が active・対象が inactive で allow）の記載漏れ。断片と PR 本文を直した commit: 4ba8e0a2 |
| L7 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | inactive の対照が末尾の空白の 1 形だけで、逆向きの形のテストが無い。PR 本文に列挙 |
| L8 | 独立-1 | advisory | no | inherited | product | accepted | block しない stop-failure-record.py・collect-gdd-telemetry.py にも toplevel の `.strip()` が残る。PR 本文に列挙 |
| M1 | 独立-2 | high | yes | inherited | path-normalization | accepted | `$(git rev-parse --show-toplevel)` で末尾の改行を落とす block hook 群（L3 の再報告。常時 High なので re-reported にできない）。「止める」により限界に書く。次の PR で直す |
| M2 | 独立-2 | high | yes | inherited | path-normalization | accepted | Stop hook の done guard の `.strip()`（L2 の再報告）。「止める」により限界に書く。次の PR で直す |
| M3 | 独立-2 | high | yes | inherited | approval-path | accepted | guard が payload の cwd しか見ず、`git -C`・`cd` の実行先を見ない（差分とは無関係）。「止める」により限界に書く。次の PR で直す |
| M4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 逆向きの変化（同名の repo が active、対象が inactive で allow）を固定するテストが無い。「止める」により限界に書く |
| M5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 非 UTF-8 のパスで deny 固定だったものが marker での判定に変わったことが、断片と PR 本文に無い。PR 本文の限界に書いた |
| M6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「allow していた」「allow になる」は、タスク名でない branch を linked でない checkout で作るときだけ成り立つ。PR 本文の限界に書いた |
| M7 | 独立-2 | low | no | inherited | product | accepted | 停止失敗の記録の書く側（.strip()）と読む側（$()）で toplevel の読み方が違う。block しない部品。PR 本文に列挙 |
| M8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | test_root_branch_guard_fail_closed.py の docstring が text モードの git_output を説明したまま。PR 本文に列挙 |
| M9 | 独立-2 | advisory | no | self-inflicted | product | accepted | CRLF を出す git では `\r` が残る（Windows は未実測）。PR 本文の限界に書いた |
| M10 | 独立-2 | advisory | no | self-inflicted | product | accepted | 改行で終わらない git の出力をそのまま採る（merge gate は止める）。本物の git では届かない。PR 本文に列挙 |
| M11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 文字の列挙（空白・改行・タブ・CR）が断片・docstring・コメントでそろっていない。PR 本文に列挙 |
| M12 | 独立-2 | advisory | no | inherited | product | accepted | extract_cwd が main() の try の外にある。PR 本文に列挙 |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
