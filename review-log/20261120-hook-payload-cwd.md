---
lane: L1+
pr: 721
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) + user | 26ffb542 | 0 | 0 | 0 | 2026-11-20 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 24007ea4 | 2 | 3 | 2 | 2026-11-20 |
| 方針メモ-1 | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | 8d1034e6 | 0 | 0 | 0 | 2026-11-20 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | ef0bf854 | 1 | 2 | 1 | 2026-11-20 |
| 方針メモ-2 | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | 985b90e4 | 0 | 0 | 0 | 2026-11-20 |
| 方針メモ-3 | 再設計, Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | f60c8329 | 0 | 0 | 0 | 2026-11-20 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 881ec399 | 1 | 1 | 1 | 2026-11-20 |
| 方針メモ-4 | 再設計, Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | a28c2e52 | 0 | 0 | 0 | 2026-11-20 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分, model: fable | db8bb70c | 1 | 1 | 1 | 2026-11-20 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分, model: fable | d5fe7ee5 | 2 | 1 | 2 | 2026-11-21 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | e990ea98 | 1 | 0 | 1 | 2026-11-21 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 5bdb30c3 | 2 | 1 | 2 | 2026-11-21 |
| 方針メモ-5 | 再設計, Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) + user | f826363f | 0 | 0 | 0 | 2026-11-21 |
| 独立-8 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 69e1ed3c | 1 | 0 | 1 | 2026-11-21 |
| 方針メモ-6 | Opus 設計レビュー ×2 (spec-autopilot:opus-advisor, model: opus) | bb62d23b | 0 | 0 | 0 | 2026-11-21 |
| 独立-9 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 390babff | 0 | 1 | 0 | 2026-11-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | low | no | inherited | design | fixed | なし。入口で payload の cwd へ移す、契約テストで wrapper を縛る、毎ターンの注入を印で絞る（ユーザーが「止める（推奨）」を選んだ）を決めた。commit: 24007ea4 |
| 独立-1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（root を 1 つ選んでから gate の述語で判定する）。git が無い・marker の表記揺れ・session id 無しの 3 つの形で、移す前の repo の marker を見落として通していた。選ぶのをやめ、gate の述語を 2 つの repo に OR で当てる。再現テストを先に書いた（8d1034e6）。commit: 0e9f8a91 |
| 独立-1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（入口の失敗が set -e で hook 全体を落とす）。消えた cwd で pwd が失敗すると Stop hook などが exit 1 になっていた。本体を または true の文脈で呼び、失敗したら移さないだけにする。方針メモ-1 で決めた。再現テストを先に書いた（8d1034e6）。commit: 0e9f8a91 |
| 独立-1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 入口の python を -X utf8 無しで起動し、既存の契約テストが落ちていた。全量のテストを通すために直した。commit: 0e9f8a91 |
| 独立-1-4 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の原文から外れた: session id の無いランタイムを印の判定の対象外にしていた。方針メモ-1 で割れ、Fable の推奨で id が無くても active な marker を求める側にした。commit: 0e9f8a91 |
| 独立-1-5 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の原文から外れた: 印の無いセッションに複数 steering の警告が毎ターン入っていた。印の判定を steering の検出の前に移し、plan-reread の注入にも同じ判定を当てる。commit: 0e9f8a91 |
| 独立-1-6 | 独立-1 | low | no | self-inflicted | product | fixed | SessionStart の前回の失敗の記録を、読む側だけ移す前の root と照合しうる。root の解決を toplevel だけに戻して直った。commit: 0e9f8a91 |
| 独立-1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 同じ規定を書いた別の箇所（session-start のコメント、hook_cwd.py の一覧、state-machine.md など）が差分の前の挙動のまま |
| 独立-1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | 足したテストの一部が、入口の移動や受理条件を消しても通る |
| 独立-1-9 | 独立-1 | low | no | self-inflicted | product | accepted | 入口の stdin を 1 バイトずつ読み、今まで stdin を読まなかった hook も EOF まで待つ。所要時間は未測 |
| 独立-1-10 | 独立-1 | advisory | no | inherited | doc-claim | fixed | plan-reread の注入が印の無いセッションに残る。独立-1-5 と同じ判定を当てた。commit: 0e9f8a91 |
| pm1-1 | 方針メモ-1 | low | no | self-inflicted | design | fixed | なし。2 本は 旧#1・旧#2・旧#5 で一致し、旧#4 で割れた（読み 1 と読み 2）。commit: 0e9f8a91 |
| 独立-2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（cwd を取れないことを pwd の失敗として hook 全体に伝える）。cwd が消え payload の cwd も使えないと、block gate 6 本が判定の前に exit 1 で通していた。root を取れないときは空にし、block gate は判定できない root として止める側にする。再現テストを先に書いた（986b5362）。commit: 985b90e4 |
| 独立-2-2 | 独立-2 | medium | no | self-inflicted | test-power | accepted | plan-reread の印の判定を固定するテストが無い |
| 独立-2-3 | 独立-2 | medium | no | self-inflicted | test-power | accepted | Stop の bash 側が 2 つの root を見ることを固定するテストが無い |
| 独立-2-4 | 独立-2 | low | no | self-inflicted | product | accepted | agent-dispatch の警告は、marker が移す前の repo にだけあるとき出なくなる（warn だけ） |
| 独立-2-5 | 独立-2 | low | no | inherited | product | accepted | marker の active の読み方が block gate と注入・Stop の bash 側で違う |
| 独立-2-6 | 独立-2 | low | no | self-inflicted | product | accepted | exact-path.sh が source していない detect-steering.sh の関数に依存する（今の呼び出し元はすべて先に source する） |
| 独立-2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 設計を変えた後に古い説明と使われない部品が残っている |
| 独立-2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | UserPromptSubmit の fail-closed を定める文書が印の条件を知らない |
| 独立-2-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 限界の節に、印が消えた後の同じセッションと PreCompact が書かれていない |
| 独立-2-10 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 確認待ち: 依頼の原文から外れた。session id の無いランタイムでは、別のセッションの active な marker も印として通る。Stop hook と同じく payload の session_id と比べる形にして狭めた（2d490eec）が、session_id の無い marker は通る。直すには setup が Codex の id を書く変更が要り、別のファイル群に広がる |
| 独立-2-11 | 独立-2 | low | no | self-inflicted | test-power | accepted | 消えた cwd のテストは終了コードしか見ず、skip の条件も広い |
| 独立-2-12 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required に /gdd-dev の打ち直しが無い |
| 独立-2-13 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | wrapper が入口を呼ぶことのテストは部分一致である |
| pm2-1 | 方針メモ-2 | low | no | self-inflicted | request-scope | fixed | なし。独立-2-10 の確認の前の相談。2 本とも、返事を待たずに完了報告でユーザーに確かめると答えた。1 本は Stop hook と同じく payload の session_id で比べる形を推し、1 本は開示だけを推した。Stop の実装（gdd_stop_hook.py の _session_guard）を確かめ、前者を採った。commit: 2d490eec |
| pm3-1 | 方針メモ-3 | low | no | self-inflicted | fail-open | fixed | 再設計: 前提: 合う。安全策 4（fail-open の high が独立-1・独立-2 の 2 巡）で、独立-1-1・1-2・2-1 にまとめて当てた。設計: 変える（block gate の述語が「止める理由が在る」の形で、判定できない形を通す側に落としていた）。2 本とも、どの root でもこのセッションの active な marker が無いと言い切れたときだけ通す形を推した。marker が読めない・照合の関数が無いときも止める。active の読み方をそろえ、使われない関数を消した。1 本が推した block gate の EXIT trap は、判定の前で落ちる文を今の tip で見つけられず、止まる損失を数えられないので足さない（PR 本文の限界に書く）。Stop の bash 側の向きは変えない。commit: f60c8329 |
| 独立-3-1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（block gate が、確かめの失敗から「無い」を導いていた）。marker が無く親を検索できたとき・active が false のときだけ「無い」と読み、ほかは止める側にした。stat の失敗・宙に浮いた symlink、移す前の cwd を取れない、行頭でない・読めない active 行を閉じた。再現テストを先に書いた（184d5421）。git が失敗したとき祖先をたどる分岐は、件数 0 の部品なので足さず next-pr にした。commit: a28c2e52 |
| 独立-3-2 | 独立-3 | medium | no | self-inflicted | test-power | accepted | block gate の active の読み方の変更を、root 1 つで固定するテストが無い |
| 独立-3-3 | 独立-3 | low | no | self-inflicted | test-power | accepted | 移す前の repo が判定できないときに止める分岐を固定するテストが無い |
| 独立-3-4 | 独立-3 | low | no | self-inflicted | test-power | accepted | 新しいテストの skip の条件が、skill gate と background gate では成り立たない |
| 独立-3-5 | 独立-3 | low | no | self-inflicted | request-scope | re-reported | 観点 0。session id の無いランタイムで、別のセッションの marker による注入が残る（独立-2-10 と同じ） |
| 独立-3-6 | 独立-3 | low | no | self-inflicted | request-scope | accepted | 確認待ち: 観点 0。依頼に無い deny（判定できないとき block gate が止める）を足した。誤 block の実測が PR 本文に無く、止めたときの理由の文が実際（判定できない）と違う。手元の marker 78 個で判定できない側に落ちるものは 0 件。理由の文は直していない |
| 独立-3-7 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 同じ規定を書いた hook の冒頭のコメントと workspace-policy.md が、fail-open で通すと書いたまま。commit: a28c2e52 |
| 独立-3-8 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の「block gate 6 本」が警告だけの hook を含む。書き分けた。commit: a28c2e52 |
| 独立-3-9 | 独立-3 | advisory | no | inherited | product | accepted | Stop の bash 側は、判定できないとき通す向きのまま |
| 独立-3-10 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | marker の session_id が空のときの扱いが、Stop hook と注入の判定で違う |
| 独立-3-11 | 独立-3 | advisory | no | inherited | product | accepted | skill gate と background gate は、marker の判定の後で python が失敗すると通す（差分の外） |
| pm4-1 | 方針メモ-4 | low | no | self-inflicted | fail-open | fixed | 再設計: 前提: 合う。独立-3-1（閉じ方: 列挙）の相談。入力者の実測は、手元の marker 78 個で行頭でない active 行・空・symlink が 0 件、30 日の transcript で .git の中への cd が 0 件（(b) に進む）。1 本は規定を書き直して next-pr にする案、1 本は「無い」の既定を正の証拠の許可リストに反転する案で割れ、作り直す側（反転）を採った。祖先をたどる分岐は件数 0 なので next-pr。反転の後、78 個で判定できない側に落ちるものは 0 件。commit: a28c2e52 |
| 独立-4-1 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（block gate が同じ marker を 2 つの読み手で読んでいた。active は awk、session_id は grep）。字下げ・コロンの前の空白の session_id を読めず、このセッションの active な marker を別のセッションとして通していた。frontmatter を 1 回読み、active と session_id を Stop hook と同じ規則（strip・後の行）で取り出す。空か許す文字だけで違う id のときだけ通し、許す文字の外は止める。再現テストを先に書いた（照合の関数が無いときのテストは、関数に頼らない形のテストに替えた）。commit: 53d2b036 |
| 独立-4-2 | 独立-4 | medium | no | self-inflicted | request-scope | accepted | 確認待ち: 観点 0。判定できないとき止める範囲を広げる変更は依頼に無く、main より止める範囲が広がる（壊れた marker など、cwd の移動と関係ない形も止める）。理由の文は直していない。PR 本文の限界に問いを書く |
| 独立-4-3 | 独立-4 | low | no | self-inflicted | product | accepted | active の読み手が block gate（awk）と注入・Stop の bash 側（grep）で割れた |
| 独立-4-4 | 独立-4 | low | no | self-inflicted | product | accepted | 列挙: `.claude` が宙に浮いた symlink・ディレクトリでないとき、親を検索できれば「無い」と読む |
| 独立-4-5 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 「無いと読むのは 2 つのときだけ」が、別のセッションの marker を通す場合を書いていない。断片とコメントに足した。commit: 53d2b036 |
| 独立-4-6 | 独立-4 | low | no | self-inflicted | test-power | accepted | frontmatter の無い・閉じていない `active: false` を止めることと、値の小文字化を、テストが固定していない |
| 独立-4-7 | 独立-4 | low | no | self-inflicted | test-power | accepted | 移す前の cwd が空のテストは、入口の python3 が起動できない環境では別の分岐で通る |
| 独立-4-8 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md・TROUBLESHOOTING.md・SUPERPOWERS_COEXISTENCE.md とテストの docstring が「GDD session 中だけ止める」のまま |
| 独立-4-9 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 断片の Affected Files に workspace-policy.md が無く、User Action Required に判定できないとき止まることと抜け方が無い |
| 独立-4-10 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 手元の marker 78 個で 0 件は材料から確かめられない |
| 独立-4-11 | 独立-4 | advisory | no | self-inflicted | product | accepted | `[[:space:]]` を解さない awk では、どの marker も止める側になる（未確認） |
| 独立-5-1 | 独立-5 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（同じ key が 2 行ある marker を、後の行で「別のセッション」と言い切っていた）。session_id が frontmatter に 2 行以上ある marker は、どの行を採るかで読み手の結論が割れるので、判定できないとして止める。ユーザーが「この PR で直す」を選んだ。再現テストを先に書いた。commit: 126bdf27 |
| 独立-5-2 | 独立-5 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（5-1 と同じ）。active が frontmatter に 2 行以上ある marker も、判定できないとして止める。ユーザーが「この PR で直す」を選んだ。再現テストを先に書いた。commit: 126bdf27 |
| 独立-5-3 | 独立-5 | medium | no | self-inflicted | request-scope | accepted | 確認待ち: 観点 0。依頼に無い block gate の判定の変更が、session_id の読み方でさらに広がった（独立-4-2 と同じ問い） |
| 独立-5-4 | 独立-5 | low | no | self-inflicted | product | accepted | session_id の許す文字が root-branch guard（英数字・`_`・`-`）より広い（`.`・`:`） |
| 独立-5-5 | 独立-5 | low | no | self-inflicted | test-power | accepted | 足したテストが、許す文字の集合と、自分の id の後に別の id がある向きを固定していない |
| 独立-5-6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の「無いと読む」条件に、今の session id があるときという前提が無い |
| 独立-5-7 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 手元の marker 78 個で 0 件が、session_id の条件を足した後の測り直しか材料から分からない |
| 独立-5-8 | 独立-5 | low | no | self-inflicted | product | accepted | 注入の側（gdd_session_continuity_ok）は古い読み方のままで、このセッションの印の読み方が 2 通りになった |
| 独立-5-9 | 独立-5 | advisory | no | inherited | product | accepted | session_id が空の marker を、block gate は通し、root-branch guard は止める（決定済みの挙動） |
| 独立-5-10 | 独立-5 | advisory | no | self-inflicted | product | accepted | block gate の wrapper が、使わなくなった detect-steering.sh を判定の前に source したまま |
| 独立-5-11 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 2 つに、gdd_session_continuity_ok を block gate と共有すると書いたまま |
| 独立-6-1 | 独立-6 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（bash 側が Stop hook の parse_state の読み方を真似て、違いを 1 つずつ追っていた）。単独の `\r`（Stop hook は行の区切りにする）や、key の前後の Unicode の空白（Stop hook は落とす）で、Stop hook だけが重複と読む形を通していた。frontmatter の行の文法を許可リストにし、`\r` を含む行と `:` の前が ASCII の key でない行があれば止める。再現テストを先に書いた。手元の marker 78 個で止まる側に落ちるものは 0 件。commit: 5d9c76f4 |
| 独立-6-2 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | テストのコメントが、消した規定「後の行を採る」のまま |
| 独立-6-3 | 独立-6 | low | no | inherited | product | accepted | frontmatter の外の active・session_id の行は数えず、ファイル全体を grep する読み手と結論が割れる |
| 独立-6-4 | 独立-6 | low | no | self-inflicted | test-power | accepted | 列挙: 新しいテストは止める側だけを固定し、数えすぎる変異を落とさない |
| 独立-6-5 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | 手元の marker 78 個で 0 件は差分から確かめられない |
| 独立-7-1 | 独立-7 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（block gate と Stop hook が marker を別々の読み手で読む）。列挙: marker に NUL があると macOS の awk が行を NUL で打ち切り、`\r` の後ろの active・session_id の行を読まない。Stop hook はこのセッションの active な marker と読むのに、block gate は通す（手元で再現した）。ユーザーが「読み手を 1 つにする」を選び、marker の中身を Stop hook と同じ state_io.py のコードで読むようにした。commit: f826363f |
| 独立-7-2 | 独立-7 | high | yes | inherited | fail-open | fixed | 設計: 変える（7-1 と同じ）。列挙: `---` の直後の NUL で、awk は閉じの行と読み、Stop hook は閉じと読まない。block gate は通す（手元で再現した）。7-1 と同じ根。commit: f826363f |
| 独立-7-3 | 独立-7 | medium | no | self-inflicted | test-power | accepted | setup が実際に書いた marker を、別のセッションとして block gate が通すことを固定するテストが無い |
| 独立-7-4 | 独立-7 | low | no | self-inflicted | request-scope | fixed | 観点 0。依頼で直すとしたのは重複の 2 件で、`\r` や key でない行が 1 つあるだけの marker も止める側に広げた（独立-4-2 と同じ問い）。読み手を 1 つにして、`\r` と key の規則・awk ごと消した（7-6 は python3 が無いときのテストを足した）。commit: f826363f |
| 独立-7-5 | 独立-7 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文の「ASCII の key でない行」が、実装（英数字・`_`・`.`・`-` だけの key）より狭い。読み手を 1 つにして、`\r` と key の規則・awk ごと消した（7-6 は python3 が無いときのテストを足した）。commit: f826363f |
| 独立-7-6 | 独立-7 | low | no | self-inflicted | test-power | fixed | awk が無い・落ちるときに block gate が止めることのテストが無い。読み手を 1 つにして、`\r` と key の規則・awk ごと消した（7-6 は python3 が無いときのテストを足した）。commit: f826363f |
| 独立-7-7 | 独立-7 | advisory | no | inherited | doc-claim | accepted | テストのコメントが「後の行を採る」のまま |
| 独立-7-8 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | 手元の marker 78 個で 0 件が tip での測り直しか材料から分からない |
| pm5-1 | 方針メモ-5 | low | no | self-inflicted | fail-open | fixed | 再設計: 前提: ずれる（block gate が awk で Stop hook の読み方を写せる）。独立-7-1・7-2 の相談。2 本とも、marker が在るときは Stop hook と同じ Python のコードで読む案（読み手を 1 つにする）を推した。ユーザーが選んだ。commit: f826363f |
| 独立-8-1 | 独立-8 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（3 本は payload を読む python3 の失敗を「通す」と読んでいた）。列挙: python3 が無いと、skill・skill の展開・background dispatch の 3 本の gate は、自セッションの active な marker があっても通す（payload を python3 で読んでから止めるため）。依頼の「python3 が無い・例外のときは止める」が 3 本に届いていない。方針メモ-6 で、python3 の終了コードが 0 以外なら静的に止めるように既定を反転した。commit: bb62d23b |
| 独立-8-2 | 独立-8 | low | no | self-inflicted | product | accepted | marker_state が frontmatter の枠の検出（先頭の `---` と閉じの行）を parse_state と共有せず写している |
| 独立-8-3 | 独立-8 | low | no | self-inflicted | test-power | accepted | NUL のテストは、NUL で行を打ち切る awk のときだけ、元に戻すと落ちる。CRLF の inactive な marker と非 UTF-8 の marker のケースが無い |
| 独立-8-4 | 独立-8 | low | no | self-inflicted | doc-claim | accepted | `\r`・key の行のテストの名前とコメントが、消した awk の規則を説明したまま |
| 独立-8-5 | 独立-8 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Affected Files に state_io.py が無い |
| 独立-8-6 | 独立-8 | low | no | self-inflicted | product | accepted | timeout 3 秒の block gate に python3 の起動が 1〜2 回増えたが、所要時間を測っていない |
| 独立-8-7 | 独立-8 | low | no | self-inflicted | product | accepted | `_GDD_EXACT_PATH_SCRIPTS` が空だと cwd の lib/state_io.py を import する（届く入力は見つかっていない） |
| 独立-8-8 | 独立-8 | low | no | inherited | product | accepted | 同じ marker を読む別の実装（root-branch guard・注入の印・Stop の bash 側）が 3 つ残り、手で書き換えた marker で読みが割れる |
| 独立-8-9 | 独立-8 | advisory | no | self-inflicted | doc-claim | accepted | 限界の節の「止める範囲が広がる」列挙に、python3 が無いホストで marker が残る repo が無い。PR 本文で直す |
| pm6-1 | 方針メモ-6 | low | no | self-inflicted | fail-open | fixed | 列挙: 独立-8-1 の相談。入力者は python3 の無い・壊れたホスト（agent が打つ形ではなく、transcript の件数は未測）。2 本とも、許可リストではなく 3 本の既定の反転（python3 が 0 以外で終われば止める）を推した。割れたのは JSON として読めない payload で、1 本は止める、1 本は今の設計どおり通す。python3 が自分で 0 で抜ける分岐で今回の穴と別なので、通す側を採った。2026-11-21 22:00 にユーザーが選んだ設計の未実装分を閉じるもので、再設計には数えない。commit: bb62d23b |
| 独立-9-1 | 独立-9 | medium | no | inherited | doc-claim | accepted | docs/SECURITY.md の「失敗時に通す例外」（125-127 行）が、python3 が落ちたら 3 本が止める挙動と食い違う |
| 独立-9-2 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | python3 が落ちたときの理由の文が「active GDD workflow の marker がある repo」と断定するが、inactive・別セッションの marker や判定できない root でも届く |
| 独立-9-3 | 独立-9 | low | no | self-inflicted | product | accepted | JSON だが dict でない payload を、skill・展開の gate は AttributeError で止め、background gate は通す（Claude Code の payload は常に dict） |
| 独立-9-4 | 独立-9 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「理由の文は /gdd-dev session が active ですのまま」が 3 本に当たらない。commit: なし（PR 本文） |
| 独立-9-5 | 独立-9 | low | no | self-inflicted | bookkeeping | fixed | 足した deny の分岐に当たる件数か「未測」が PR 本文に無い。commit: なし（PR 本文） |
| 独立-9-6 | 独立-9 | advisory | no | self-inflicted | style | accepted | 同じ理由文のリテラルが 3 ファイルに重複 |
| 独立-9-7 | 独立-9 | advisory | no | inherited | product | out-of-diff | worktree-command-guard は python が無いと通す（docs/SECURITY.md:128 の既知の例外） |
| 独立-9-8 | 独立-9 | advisory | no | inherited | product | accepted | python3 の起動回数と hook の timeout（3 秒）の関係は未測 |
