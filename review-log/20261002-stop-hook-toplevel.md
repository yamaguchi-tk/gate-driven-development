---
lane: L1+
pr: 274
follow_up_of: 271
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#271 の限界に書いた次の PR の 1 本目。旧#271 の方針メモ-2 で、Opus がこの穴を「python 1 か所で、旧#271 と同じ直し方〔bytes で読み、最後の改行だけ落とす〕」として次の PR の 1 本目に推した。その推奨をそのまま採り、memory の 2026-09-28 の決定に従ってユーザーへの確認は内部の相談で代えた。main の案との食い違いは無く、Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-02T08:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 938e01cacbc10b92629c45574c9b0f5f8a835f91 | 1 | 2 | 1 | 2026-10-02T09:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 2c3419b3dac24c60d20125f1ef726d82a9219f6c | 1 | 1 | 1 | 2026-10-02T09:45+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（安全策 4 の発火〔クラスタ path-normalization の high が独立-1・独立-2 の 2 巡。どちらも origin: pre-existing〕。Opus は O1 をこの PR で直すことを推した〔`resolve_guard_tasklist` の fallback で、steering が 1 つ以上かつ worktree のパスに注入面のある文字があれば containment で止める。判定はパス文字列だけで閉じる〕。信号 ② で呼んだ Fable も賛成した〔新しい fail-open・例外での落ちは無く、増える block は steering が 2 つ以上の形だけ〕。main の案と食い違わず、memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて「直す」を採った。O2 は Opus も accepted を推した） | - | 0 | 0 | 0 | 2026-10-02T10:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | ec7136509f5c315d71dd33adebe3ca942a09f1ee | 0 | 1 | 0 | 2026-10-02T10:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| N1 | 独立-1 | high | yes | inherited | path-normalization | accepted | 名前（パス）に LF を含む worktree で、pre-push gate が `$(pwd)`・1 行 1 レコードの root の受け渡し・detect-steering.sh の `$(git rev-parse --show-toplevel)` で別のパスを見て、検査せずに push を通す。差分の外の既存の穴（旧#271 の L3・M1 と同じ）。直す次の PR を続けて出す |
| N2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | テストが block の理由を固定せず、タブ・改行・CR では containment の拒否で block していた。理由を assert し、完了済みの tasklist の対照を足した commit: 9161e5df |
| N3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | タブ・改行・CR を名前に含む worktree では containment で done が止まり続けることが、断片と PR 本文に無い。断片の Summary・User Action Required と PR 本文の限界に書いた commit: 2c3419b3 |
| N4 | 独立-1 | low | no | self-inflicted | style | fixed | 1500 行を超える gdd_stop_hook.py が 5 行増えた。コメントを縮め、余分な空行を削って base より減らした commit: bf14f186 |
| N5 | 独立-1 | low | no | inherited | product | fixed | stop-failure-record.py が同じ toplevel を text モードの `.strip()` で読み、SessionStart の照合と一致しない。同じ読み方にした commit: bf14f186 |
| N6 | 独立-1 | low | no | inherited | product | out-of-diff | handoff_summary.py が全 worktree を走査する（差分とは無関係） |
| N7 | 独立-1 | low | no | inherited | doc-claim | out-of-diff | pr_review_followup_polling.py の docstring が steering の決め方の現状と合わない（差分とは無関係） |
| N8 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Fixed が同じ toplevel を使う経路の一部しか挙げていない。経路を列挙した commit: 2c3419b3 |
| N9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の限界の列挙にタブが無い。commit: なし（PR 本文） |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| O1 | 独立-2 | high | yes | inherited | path-normalization | fixed | worktree のパスに制御文字があると binding が捨てられ、steering が 2 つ以上なら resolve_guard_tasklist が None を返し、未完了の tasklist のまま done を通す。steering が 1 つ以上なら containment で止める commit: ff2d604f |
| O2 | 独立-2 | medium | no | self-inflicted | product | accepted | 名前が LF で終わる repo で、StopFailure の記録の書き手が LF を残し、SessionStart の bash `$()` の読み手と一致しなくなった（通知が出ない。block はしない）。PR 本文の限界に退行として書き、bash の読み手を直す次の PR でそろえる |
| O3 | 独立-2 | low | no | inherited | product | accepted | 制御文字の名前で止めたときの理由（CONTAINMENT_ERROR）が symlink・binding を案内し、名前を変える手段を示さない。PR 本文の限界に書いた |
| O4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 完了済みの tasklist のテストが bind-unresolved を見ておらず、修正を戻しても落ちない。PR 本文の限界に書いた |
| O5 | 独立-2 | low | no | self-inflicted | test-power | accepted | StopFailure の記録の修正に、書き手→読み手のテストが無い。PR 本文の限界に書いた |
| O6 | 独立-2 | low | no | self-inflicted | product | accepted | stop-failure-record の os.fsdecode の値が _scrub を通らず、非 UTF-8 のパスで記録が書かれないことがある。PR 本文の限界に書いた |
| O7 | 独立-2 | low | no | inherited | product | accepted | handoff_summary.py が git worktree list を text モードで読み、CR・LF を含む名前の state.md を見つけない。PR 本文の限界に書いた |
| O8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Validation がテストより広い（完了済みは binding がある形だけ）。文をテストの範囲に合わせた commit: ec713650 |
| O9 | 独立-2 | advisory | no | inherited | product | accepted | collect-gdd-telemetry.py が toplevel を .strip() で読む（手で回すスクリプト）。PR 本文に列挙 |
| P1 | 独立-3 | medium | no | self-inflicted | product | accepted | パスの拒否文字で止めたときの block の理由と回復手順が、symlink・binding・tasklist を案内し、名前を変える手段を示さない（steering が 2 つ以上の形にも広がった）。PR 本文の限界に書いた |
| P2 | 独立-3 | low | no | self-inflicted | test-power | accepted | steering なしの対照テストが終了コードと allow の経路を見ておらず、hook が落ちても通る。PR 本文の限界に書いた |
| P3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 新しいコメントの「1 つのときは下の検査が止める」が制御フローと合わず、docstring が新しい例外を書いていない。PR 本文の限界に書いた |
| P4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文が拒否する文字を狭く書いている（U+2028・U+2029、Linux で UTF-8 として読めないバイトも止まる）。PR 本文の限界に書いた |
| P5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Validation がテストの網羅を広く書いている（2 つ × 完了済み、steering なし × 改行・CR は未テスト）。PR 本文の限界に書いた |
| P6 | 独立-3 | advisory | no | inherited | product | accepted | 新しい判定は resolve 前の文字列だけを見て、binding を捨てる条件より狭い（`.steering` 自体が symlink の形など。設計上の warn 降格の範囲内）。PR 本文に列挙 |
