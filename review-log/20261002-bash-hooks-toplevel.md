---
lane: L1+
pr: 276
follow_up_of: 274
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#274 の限界に書いた次の PR。Opus は「進めてよい。PR-A〔共有の取得関数・block hook 5 本・gdd-active-check.sh・session-start〕と PR-B〔pre-push・pre-PR・detect-steering.sh・steering の列挙を NUL 区切りに〕の 2 本に分ける」を推した。main の案〔1 本・pre-push は unsafe_root で止める〕と食い違ったのは分割と pre-push の扱いで、分割は Opus の案を採った。pre-push の扱いは PR-B の論点なので、Fable への相談〔信号 ①〕は PR-B で行う。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-02T11:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0634f55e0e4b41d1fdf3b92e133ade973dd8db01 | 1 | 1 | 1 | 2026-10-02T12:10+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（独立-1 の high〔marker の書き手 setup-gdd-loop.sh は改行を落としたパスに書くので、読む側だけ直すと marker を見失う〕を受けて範囲を相談した。main は「書き手と読み手を全部そろえる」を推し、Opus は「この PR は止めるだけ〔改行で終わる toplevel なら止める側に倒す〕。全部そろえる案は落としたパスで読む箇所の取りこぼしが fail-open になり、+800〜1,200 行」を推した。食い違ったので信号 ① で Fable を呼び、Fable は Opus 案に賛成し、SessionStart だけは正しいパスで読む今の差分を残すよう修正した〔StopFailure の記録の書き手が正しいパスで書くため〕。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて、Fable の修正付きの Opus 案を採った） | - | 0 | 0 | 0 | 2026-10-02T12:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 716f999afbe7e99ea0bd4e8165997a74d4a7dd71 | 2 | 0 | 2 | 2026-10-02T13:20+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火〔クラスタ path-normalization の high が独立-1・独立-2 の 2 巡。独立-2 の 2 件は origin: pre-existing〕。Opus は「止める」を推した〔root branch の guard だけを直しても marker を toplevel から読む実装は約 20 本あり、根治は書き手と読み手をそろえる次の PR。done guard は止める側に倒すと GDD を使っていない repo の stop が全部止まる〕。Fable はこの PR で信号 ① に 1 回使ったので呼んでいない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて「止める」を採った。以後の指摘は直さず限界に書く） | - | 0 | 0 | 0 | 2026-10-02T13:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| L1 | 独立-1 | high | yes | self-inflicted | path-normalization | fixed | 読む側だけを正しいパスにしたので、改行を落としたパスに書く setup-gdd-loop.sh の marker を見失い、名前が改行で終わる repo で block hook が通す。改行で終わる toplevel では marker を見ずに active として扱う commit: af926d2e |
| L2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | warn だけの Agent 起動の gate を block する hook として書いていた。断片を 4 つの block hook に直した commit: 716f999a |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary の主語が「bash の hook」全体で、直した範囲より広い。主語を直した hook に絞った commit: 716f999a |
| L4 | 独立-1 | low | no | self-inflicted | test-power | fixed | fixture が全部 git repo で、pwd の番兵の経路を通らない。git の外のディレクトリのテストを足した commit: 6fb26707 |
| L5 | 独立-1 | low | no | self-inflicted | test-power | fixed | block hook のテストが HOME を隔離せず、手元の kill switch で判定を見ずに通る。HOME を空のディレクトリにした commit: 6fb26707 |
| L6 | 独立-1 | low | no | self-inflicted | product | fixed | テストが通知コマンドを含む PATH で StopFailure の hook を起動し、実機の通知が出る。通知コマンドを含まない PATH にした commit: 6fb26707 |
| L7 | 独立-1 | advisory | no | self-inflicted | product | fixed | SessionStart だけ kill switch の判定より前に新しい lib を読む。detect-steering.sh の source の後に移した commit: af926d2e |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| M1 | 独立-2 | high | yes | inherited | path-normalization | accepted | root branch の guard（validate-worktree-command.py active_gdd_state_exists）が marker を改行を残したパスで読み、名前が改行で終わる repo で書き手の marker を見つけずに root checkout のブランチ作成を通す。「止める」により限界に書く。書き手と読み手をそろえる次の PR で直す |
| M2 | 独立-2 | high | yes | inherited | path-normalization | accepted | done guard（gdd_stop_hook.py main）が payload の cwd を resolve したパスで marker を読み、同じ repo で動かない。「止める」により限界に書く。次の PR で直す |
| M3 | 独立-2 | low | no | self-inflicted | product | accepted | Agent 起動の gate が、改行で終わる toplevel で marker の検査を飛ばし、改行を落とした同名の repo の steering で warn を出しうる。「止める」により限界に書いた |
| M4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が、止まるようになる範囲（Stop hook の bash 入口、git の外のディレクトリ）を書いていない。PR 本文の限界を直した commit: なし（PR 本文） |
| M5 | 独立-2 | low | no | self-inflicted | product | accepted | 改行で終わる toplevel で止めたときの理由の文が、原因と抜け道（ディレクトリ名の変更・kill switch）を示さない。「止める」により限界に書いた |
| M6 | 独立-2 | low | no | self-inflicted | test-power | accepted | 述語を「どこかに改行を含む」に広げる変異をテストが捕まえない（途中に改行を含む repo の対照が無い）。「止める」により限界に書いた |
| M7 | 独立-2 | low | no | self-inflicted | product | accepted | テストの _quiet_path が python3 を shutil.which の先に向け、見つからないコマンドを黙って飛ばす（既存の形と違う）。「止める」により限界に書いた |
| M8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | exact-path.sh の冒頭の説明が「marker を見落とす」のままで、設計（別のパスの marker で判定する）と食い違う。PR 本文に列挙 |
| M9 | 独立-2 | advisory | no | self-inflicted | product | accepted | git の外を見るテストが、一時ディレクトリが git の作業ツリーの外にあることを前提にしている。PR 本文に列挙 |
| K3 | 方針メモ-3 | - | - | - | - | - | なし |
