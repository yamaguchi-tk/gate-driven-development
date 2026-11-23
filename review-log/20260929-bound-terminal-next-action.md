---
lane: L1+
pr: 233
follow_up_of: 219
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user | 4b49901bbc9185127988968d349e1933b742bd9f | 0 | 0 | 0 | 2026-09-29T10:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 86221ee8ab084389161aadd618c4f99410816f60 | 2 | 2 | 2 | 2026-09-29T12:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c6944d623a7c2d9ae9f8e39f6c93b87e1cbc1e81 | 1 | 2 | 1 | 2026-09-29T13:30+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) | c6944d623a7c2d9ae9f8e39f6c93b87e1cbc1e81 | 1 | 0 | 1 | 2026-09-29T14:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 0bcbfaa689785c0d9644424131c67a9bd1df17cf | 1 | 1 | 1 | 2026-09-29T15:10+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) | 0bcbfaa689785c0d9644424131c67a9bd1df17cf | 2 | 0 | 2 | 2026-09-29T15:40+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | c0e9c4ade56992c86e2c30beeaa282159482d897 | 2 | 0 | 2 | 2026-09-29T16:20+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus) | c0e9c4ade56992c86e2c30beeaa282159482d897 | 0 | 0 | 0 | 2026-09-29T16:30+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 0418912ec0d72c696cbf1147f0b7874bef9f108b | 2 | 0 | 2 | 2026-09-29T17:10+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus) | 0418912ec0d72c696cbf1147f0b7874bef9f108b | 0 | 0 | 0 | 2026-09-29T17:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（ユーザーが次の PR の実施とマージを許可。Opus の推奨は、H1 は数え直すときだけ binding 先の state.md か tasklist.md の Next Action の done・cancelled も終端とみなす、G2 は広い側〔pre-PR も --recount-terminal-binding〕。実測は ~/.gdd/worktrees の 95 worktree で解決の結果が変わるのは 0 件。全角の注記・blocked の binding・pre-PR に tip の材料が無いことは限界に書く） |
| J1 | 独立-1 | high | yes | inherited | bound-terminal-fail-open | fixed | binding 先の終端判定が done・cancelled の完全一致だけで、`done（…）`・`done (merged)`・`Done`・`canceled` の binding 先（trivial）が作業中の steering を隠して push を通す。数え直すときは先頭の英単語を小文字にして比べる（831c77ae、1b898de8） |
| J2 | 独立-1 | high | yes | self-inflicted | bound-terminal-fail-open | fixed | binding 先の state.md が .steering/ の外にあると、Next Action: done の binding 先が数え直しでも union でも拾われず、検査されなくなった。作業中が無ければ done とみなした binding 先を返す（831c77ae、1b898de8） |
| J3 | 独立-1 | medium | no | self-inflicted | product | fixed | 作業中が無く別の done・blocked の steering があると multiple-terminal になり、「今どおり」が成り立たない。J2 と同じ fallback で binding 先を返す（831c77ae、1b898de8） |
| J4 | 独立-1 | medium | no | self-inflicted | product | fixed | pre-PR が数え直しで読めない state.md を found にすると、set -e で無出力のまま終わる。読む前に確かめて理由つきで止める（831c77ae、1b898de8） |
| J5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | abandon-and-pause.md の「state.md を読む」が、binding 先の tasklist.md も読む gate に合わない（1b898de8） |
| J6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | コメントの「same as _is_terminal_state」が不正確（1b898de8） |
| J7 | 独立-1 | low | no | self-inflicted | test-power | fixed | 読めない state.md のテストと merge のテストが差分の効果を判別しない。tasklist.md が読めない形と、対象 PR を省いた merge のテストを足した（831c77ae） |
| J8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 正式なキャンセル（Next Action=cancelled だけ）の binding 先で、ほかに steering が無いときは検査しなくなる（state-machine.md の終端の定義どおり）。PR 本文に書く |
| J9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | followup 中の形を数え直しでは終端とみなすことが、gdd-pr-review-followup と post-completion-pr-flow.md に反映されていない。PR 本文の限界に書く |
| K1 | 独立-2 | high | yes | inherited | bound-terminal-fail-open | fixed | binding 先の tasklist.md が読めないと値が空になり binding 先を作業中とみなす。binding 先が trivial なら、binding の無い作業中の steering を検査しないまま pre-push を通す（読めれば steering-multiple で止まる）（f0791e65、90dd95da） |
| K2 | 独立-2 | medium | no | self-inflicted | product | fixed | 数え直しの loop が binding 先自身の state.md を完全一致で読み直し、`done (merged)`・`canceled` などの binding 先を作業中に数える。作業中が無くても leftover の done があると multiple で誤って止まり、コメント・changelog の主張と食い違う。binding 先は loop から外し、done・blocked なら scan の後で終端の候補に足す（f0791e65、90dd95da） |
| K3 | 独立-2 | medium | no | inherited | doc-claim | accepted | 終端の綴りを先頭の英単語 done・cancelled・canceled で判定するので、`**done**`・`"done"`・`abandoned`・日本語の binding 先は作業中として扱う（開く側）。限界の節に書かれていない。PR 本文の限界に書く |
| K4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | gdd_detect_active_steering のヘッダが、先頭語の判定と作業中が無いときの fallback を書いていない（90dd95da） |
| N1 | 方針メモ-1 | high | yes | self-inflicted | bound-terminal-fail-open | fixed | 安全策 4 の発火（bound-terminal-fail-open の high が 2 巡）で Opus に相談。推奨どおり K1・K2 と同じ修正で直す。Opus が実行で確かめた穴: .steering/ の外の binding 先が Next Action: done（または Resume From: done）で、作業中の steering が trivial なら、binding 先が終端の候補に入らず push を無出力で通す（f0791e65、90dd95da） |
| P1 | 独立-3 | high | yes | self-inflicted | bound-terminal-fail-open | fixed | 数え直しで cancel とみなした binding 先を候補から外すので、peer turn の write guard が止めない綴り（`Canceled`・`canceled`・`cancelled（…）`、tasklist.md だけ）の cancel を 1 行書くと、binding 先が push・merge gate の検査から外れる（base は作業中に数えて検査していた）。Opus の推奨（A）どおり、数え直しで終端とみなした binding 先は cancel でも候補に残し、作業中が無ければ返す（4d34b056、75eb6ef1） |
| P2 | 独立-3 | medium | no | self-inflicted | doc-claim | fixed | cancel とみなした binding 先を、作業中が無いときに検査しなくなった変化が changelog・PR 本文に書かれていない（4d34b056、75eb6ef1、8c9fb3b7） |
| P3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | ヘッダと changelog が tasklist.md の Resume From も読むように読める（75eb6ef1、8c9fb3b7） |
| P4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 「union would pick」のコメントが、.steering/ の外の binding 先を残す実装と合わない（75eb6ef1） |
| P5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | self-review-lanes.md が、読めない tasklist.md を done とみなす規則と出口を書いていない（8c9fb3b7） |
| P6 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | .steering/ の外の binding 先のテストの subTest が、前の周の fixture を引き継ぐ。PR 本文に書く |
| Q1 | 方針メモ-2 | high | yes | inherited | peer-turn-cancel-guard | accepted | 安全策 4 の再発火（high・blocking の巡が 3 回）で Opus に相談し、A（reader 側で閉じる）を採用。残る穴: peer turn の write guard は Resume From を検査しないので、Resume From: cancelled（完全一致）を書くと binding 先が gate の検査から外れる（main からある）。直す場所は write guard で、次の PR（follow_up_of）で受理集合を数え直しの規則に揃える。PR 本文の限界の先頭に書く |
| Q2 | 方針メモ-2 | high | yes | self-inflicted | merge-gate-outside-binding | accepted | .steering/ の外の binding 先を数え直しで終端とみなし作業中もあるとき、merge gate の対象 PR の照合は .steering/ しか見ないので none になり、承認の証跡を見ずに素通りする（main では found で検査していた。実データで外を指す binding は 0 件）。直すには候補の一覧を merge gate へ渡す配線とパスの正規化が要り、巡の上限の後なので次の PR に回す。PR 本文の限界の先頭に書く |
| R1 | 独立-4 | high | yes | inherited | peer-turn-cancel-guard | accepted | peer turn の write guard は Resume From を検査しないので、Resume From: cancelled（完全一致）を書くと binding 先が 3 つの gate から外れる（Q1 と同じ。main からある）。直す場所は write guard で、次の PR に回す。PR 本文の限界の先頭に書く |
| R2 | 独立-4 | high | yes | self-inflicted | merge-gate-outside-binding | fixed | merge gate の multiple の対象 PR の照合は .steering/ しか見ず、.steering/ の外の binding 先が対象 PR を記録していても none で素通りする（Q2 と同じ）。none の枝で .steering/ の外の候補があれば steering-ambiguous で止める（c72b5cda、376c3333、6087539b） |
| R3 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 「guard が止めない綴りの cancel では binding 先は外れない」の断定が Resume From: cancelled では成り立たない（4e580b0b） |
| R4 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | changelog が Resume From の完全一致の done・cancelled の例外を書いていない（4e580b0b） |
| R5 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | abandon-and-pause.md が、Next Action=cancelled だけでは binding 先が gate から外れないことを書いていない（4e580b0b） |
| S1 | 方針メモ-3 | advisory | no | inherited | none | accepted | 要約: なし（安全策 4 の再発火で Opus に相談。R2 は none の枝で .steering/ の外の候補を止める狭い修正で閉じ、対になる通過のテストを足す。R1 は代案〔Resume From と Next Action がどちらも cancelled のときだけ外す〕を入れず accepted のまま止め、次の PR で write guard の受理集合を揃える。文書の low は同じ修正に入れる） |
| T1 | 独立-5 | high | yes | self-inflicted | merge-gate-outside-binding | accepted | merge gate の新しい block 文が binding 先の絶対パスを reason に入れ、block() は `\` `"` タブ・改行・CR しかエスケープしないので、ESC などの制御文字を含むディレクトリ名だと JSON が壊れ merge が通る（main は外の binding 先を found にしパスを出さずに止めていた）。無効化後の巡の上限を使い切ったので、直後の PR で文面からパスを外して直す。PR 本文の限界の先頭に書く |
| T2 | 独立-5 | low | no | self-inflicted | product | accepted | 同じ block 文が絶対パスを出し、merge gate の masking の規約に反する。T1 と同じ修正で直す |
| T3 | 独立-5 | high | yes | inherited | peer-turn-cancel-guard | accepted | peer turn の write guard が Resume From: cancelled を止めない（R1・Q1 と同じ。main からある）。直後の PR で直す。PR 本文の限界の先頭に書く |
| T4 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 「Resume From の完全一致の done・cancelled だけが binding 先を gate から外す」の記述が、done は候補に残るコードとテストに反し、stale な brainstorming も抜かしている。PR 本文の限界に書き、直後の PR で直す |
| T5 | 独立-5 | low | no | inherited | doc-claim | accepted | 正式キャンセルの skill（gdd-completion-check の手順 21・Cancelled Cleanup の keep）が Resume From: cancelled を書かない（止める側）。PR 本文の限界に書く |
| T6 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | changelog の User Action Required に、merge gate の .steering/ の外の候補での新しい止まり方が無い。PR 本文に書く |
| U1 | 方針メモ-4 | advisory | no | inherited | none | accepted | 要約: なし（安全策 4 の再発火で Opus に相談。無効化後の巡の上限を使い切ったので「止める」を選び、T1・T3 を限界の節の先頭に書き分けて PR を作る。T1 は this-diff の退行、T3 は main からある。T1〔文面からパスを外す〕と T3〔guard の受理集合〕は直後の follow-up PR でまとめて直す） |
