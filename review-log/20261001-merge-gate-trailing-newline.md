---
lane: L1+
pr: 270
follow_up_of: 268
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（旧#268 の限界に書いた次の PR。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた。main の案〔改行を位置を問わず拒む〕と Opus の推奨〔番兵で厳密に取り、改行で終わる toplevel だけを解決できないものにする〕が食い違ったので、信号 ① で Fable を 1 回呼んだ。Fable は Opus の案を推し、2 値の形で番兵の有無を先に見る 1 行を足す案を出した。どちらも採った） | - | 0 | 0 | 0 | 2026-10-02T03:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 319cf64c64f312c7cb075a297374be2dc9c3224c | 6 | 0 | 6 | 2026-10-02T03:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c720509caed199b406d48e036b101fd1b1d79cff | 1 | 0 | 1 | 2026-10-02T04:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火〔クラスタ path-normalization の high が独立-1・独立-2 の 2 巡〕。Fable はこの PR で方針メモに 1 回使ったので呼んでいない。Opus は「改行の block から merge の条件を外して常に止め、差分巡をもう 1 回」〔C〕を推し、main の案と一致した。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて C を採った） | - | 0 | 0 | 0 | 2026-10-02T04:45+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 4928e8425a5d8de3c8a27a385e94e7569d042ae2 | 0 | 0 | 0 | 2026-10-02T05:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| L1 | 独立-1 | high | yes | self-inflicted | path-normalization | fixed | 改行で終わる toplevel の候補を捨てるだけだと、marker の無い root では台帳の照合に回って通る（main は同名の改行なしの worktree があれば止めていた）。merge ならフラグで root の marker を問わず止める commit: 53b36374 |
| L2 | 独立-1 | high | yes | inherited | path-normalization | fixed | parser の emit が cd 先の改行・タブを空白に置き換え、照合するパスと実際の移動先が別になる。制御文字を含む cd 先を採らない（intent が残って止まる） commit: 53b36374 |
| L3 | 独立-1 | high | yes | inherited | path-normalization | accepted | pre-PR gate（run-pre-pr-gate-hook.sh:609-632）も `$()` で workdir・toplevel の末尾の改行を落とす。差分の外の既存の穴。直す次の PR を続けて出す |
| L4 | 独立-1 | high | yes | inherited | path-normalization | accepted | pre-push gate（run-pre-push-gate-hook.sh:68・:152）も同じ型。差分の外の既存の穴。直す次の PR を続けて出す |
| L5 | 独立-1 | high | yes | inherited | path-normalization | accepted | validate-worktree-command.py:511 が toplevel を `.strip()` で読み、末尾の空白・改行を落とす。差分の外の既存の穴。直す次の PR を続けて出す |
| L6 | 独立-1 | high | yes | inherited | approval-path | accepted | marker の無い root checkout から `cd .; gh pr merge 7` と打つと実行先が決まらず、台帳の照合が unknown になって通る（main と同じ）。差分の外の既存の穴。直す次の PR を続けて出す |
| L7 | 独立-1 | low | no | inherited | path-normalization | fixed | プロセス cwd の `$(pwd)` だけが番兵なし。番兵で取る commit: 53b36374 |
| L8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 候補を捨てる `continue` を消しても足したテストが通る。marker の無い root checkout から指すテストを足した commit: dab7d85e |
| L9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「pr-target-unresolvable で止める」が marker のあるセッションでしか成り立たない。L1 の修正で経路を問わず成り立つようにし、断片を書き直した commit: c720509c |
| L10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が cd でも通ること・判定が変わることを書いていない。L1 の修正で該当の形は止まるので、PR 本文から外した commit: なし（PR 本文） |
| L11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「NUL が入ると値が消える」が不正確（NUL は落ちて残りがつながる）。lone surrogate と NUL を分けて書いた commit: なし（PR 本文） |
| M1 | 独立-2 | high | yes | self-inflicted | path-normalization | fixed | 改行の block が IS_MERGE=true に限られ、解析が縮退するコマンド（merge かを判定できない）で、marker の無い root から改行で終わる GDD worktree を指すと通る。merge の条件を外して常に止める commit: dd74bdef |
| M2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の「制御文字を含む cd 先も止める」が marker の無い root では成り立たない。範囲を足した（断片は後の PR で書き換えられないので push 前に直した） commit: 4928e842 |
| M3 | 独立-2 | low | no | self-inflicted | test-power | accepted | 制御文字のテストに `\r` が無く、filter を `\n`・`\t` に狭める変異が生き残る。PR 本文の限界に列挙 |
| M4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「同じ型が残る hook」に `$(pwd)` で root を取る他の hook が無い。PR 本文を直した commit: なし（PR 本文） |
| M5 | 独立-2 | advisory | no | self-inflicted | product | accepted | プロセス cwd が改行で終わるセッションでは、解決できる cd 先への merge も止まる（過剰 block、実データ未計測）。PR 本文に列挙 |
| M6 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の「番兵が無ければ値が無いとする」はプロセス cwd に当たらない。範囲を直した commit: なし（PR 本文） |
| M7 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の「実データ 0 件」に測り方が無い。未計測と書き直した commit: なし（PR 本文） |
| M8 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Summary がプロセス cwd も照合すると書いている（プロセス cwd は root を決める側）。分けて書いた（断片は後の PR で書き換えられないので push 前に直した） commit: 4928e842 |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| N1 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary が、parser が採らない cd 先（marker の無い root では台帳の照合に回る）まで止めると読める。止める実行先を toplevel が改行で終わると分かったものに限った（断片は後の PR で書き換えられないので push 前に直した） commit: 0e6e36b2 |
| N2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 候補ループのコメント「merge なら下で止める」が、merge かを判定できない入力も止める実装と合わない。hook のコメントで、変えると巡が無効になるので限界に書く |
| N3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | step 2b・parser・test_merge_gate_hook_non_gdd_merge の docstring が、判定できない入力の扱いに改行の例外を書いていない（縮退した非 merge のコマンドも pr-target-unresolvable で止まる）。限界に書く |
| N4 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の括弧書きが判定できない入力の reason を別に見せ、限界に縮退・未解析の非 merge のコマンドが止まることが無い。PR 本文を直した commit: なし（PR 本文） |
| N5 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | 縮退のテストが reason を固定していない（block の経路の差し替えを検出できない）。PR 本文に列挙 |
