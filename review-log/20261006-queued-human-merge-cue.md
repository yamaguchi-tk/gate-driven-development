---
lane: L1+
pr: 386
follow_up_of: 376
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（実測: 30 日の transcript 3,215 本で、attachment.origin.kind が human の queued_command は 422 件、うち 407 件は type:user の行に出ない。main の草案は queued の human を last_user_text に入れ、継続判定とマージの合図の両方に効かせる案で、end_turn 24,197 回のうち継続判定が 61 回〔すべて継続する→しない〕、合図の判定が 89 回〔新しく一致 22、一致しなくなる 67〕変わる。Opus は、継続判定は turn の途中の割り込みでは変えるべきでなく、広い側の既定は別の機能に及ばないとして、last_user_text を変えずに別の field に溜め、マージの合図だけが OR で読む案と、害の実測を関門にすることを推奨した。関門の実測: queued の human の合図 10 件のうち、その後に確認せずに end_turn したものが最大 8 件〔marker の有無は不明〕。main は Opus の案に改め、食い違いは残らないので max・Fable には相談していない。ユーザーは「マージの合図だけで作る」を選んだ） | - | 0 | 0 | 0 | 2026-10-06T13:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b4432e56 | 2 | 0 | 2 | 2026-10-06T14:00+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（独立-1 の F2 が high・blocking で閉じ方: 列挙。入力者の実測: 30 日の type:user の候補行は origin.kind human 5,373・origin なし 7,616〔skill の前置き 1,976、compaction の要約 657 など〕。queued の合図の後に来て合図を消した行 9 件のうち 4 件が host の注入〔skill の前置き・ci-monitor-event など〕で、agent が事故で打つ形。main は (a)〔合図を消す契機を origin.kind human の許可リスト〕を案にした。Opus は (a) を type:user の合図まで広げ、合図を持ち続けることで起きる誤 block を先に測るよう推奨した。実測: 人間の合図 → origin なしの行 → 人間の発話なし → PR 作成・GDD 完了の並びが 21 件、marker を書く GDD の done は 3 件〔上限〕。1 件以上なので規律 C で別の直し方〔marker の created_at_epoch で合図の寿命を区切る〕と比べ、ユーザーに戻した。ユーザーは「許可リスト＋時刻で区切る」を選んだ） | - | 0 | 0 | 0 | 2026-10-06T14:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 72ef93f3 | 4 | 0 | 4 | 2026-10-06T15:20+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（安全策 4 の発火: fail-open クラスタの high が独立-1・独立-2 で 2 回。対象は Stop hook のマージ後確認の block gate。実測: 合図の語に一致する人間でない type:user 行 891 件〔skill の前置き 504、compaction の要約 368〕、人間の合図 296 件のうち未マージの発話 17 件、価値の最大 8 件のうち marker があったのは最大 1 件。main と比べて退行するのは G2 の広がりだけ。main の初案は時刻の区切りを外す縮小で、Opus は方針メモ-2 で閉じた古い合図の誤 block が戻るとして「止める」を推奨し、main はこれに改めた。ユーザーは「続行する」を選んだ。回数は戻さない。G1・G2 は (a) の許可リスト〔合図は origin.kind human の発話だけから取り、origin を書かない transcript だけ last_user_text を読む。合図の語の後に続く形を過去の報告に限る。人間の合図 296 件に当てて、合図から外れる過去の報告は「が」を許可に足して 0 件〕、G3 は境界を PR の URL が初めて出た時刻に、G4 は marker の時刻を範囲つきの int に限る） | - | 0 | 0 | 0 | 2026-10-06T16:30+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 32e0743c | 3 | 3 | 3 | 2026-10-06T17:30+09:00 |
| 方針メモ-4 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（安全策 4 の再発火: fail-open クラスタの high が独立-3 で 3 回目。対象は Stop hook のマージ後確認の block gate。実測〔30 日 3,221 本〕: H3 は古い正規表現に当たり新しい正規表現に当たらない人間の発話 22 件のうちこの PR のマージの報告 0 件、H2 は origin の無い typed の行 2,635 件がすべて headless の prompt で人間の合図が消える実例 0 件、H1 は合図より後にだけ PR の URL が出た合図が上限 6 件。main の案は H1 を min〔URL の初出, created_at〕で直し H2・H3 を (b) accepted。Opus も同じ案を推奨し、(a) URL の時刻が読めなければ区切らない、(b) 確かめの差分巡で high・blocking が出たら直さず止める、(c) テストの時刻を過去に移す、を足した。信号 ② で Fable〔gdd-fable-advisor〕にも相談し、同じ案を「退行を直してから止める」と位置づけた。ユーザーは「H1 を直してから止める」を選んだ。確かめの差分巡は 1 回だけ回す） | - | 0 | 0 | 0 | 2026-10-06T18:10+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | bf678238 | 1 | 1 | 1 | 2026-10-06T19:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 合図を新しい順の最初の 1 件で決めるので、後から届いた別の PR の合図が前の合図を打ち消す。commit: 7160ca27 |
| F2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 合図を消す条件が host の注入の type:user 行（skill の前置きなど）でも成り立ち、合図の後に skill を起動すると停止が通る。方針メモ-2 で許可リスト＋marker の時刻で区切る形にした。commit: d0e5a7bf |
| F3 | 独立-1 | low | no | self-inflicted | テストの検出力 | fixed | テストが合図の候補が 2 件一致する並びと「新しい順」を固定していない。commit: 67f3c18f |
| F4 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 断片の「peer のメッセージの後は確認を始めない」が queued で届いた peer に当たらない。commit: 7160ca27 |
| F5 | 独立-1 | advisory | no | inherited | 合図の語 | accepted | UserPromptSubmit hook の合図の語の判定が Stop hook と違い、queued の発話で発火するかが未確認 |
| M2 | 方針メモ-2 | - | - | - | - | - | なし |
| M3 | 方針メモ-3 | - | - | - | - | - | なし |
| G1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 合図の候補に残した last_user_text が host の注入の行（本文に「マージした」を含む skill の前置き）で上書きされて合図になり、block の後の返答で marker が消える。commit: 6f1090a8 |
| G2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: MANUAL_MERGE_RE が「マージしたら次に進んで」などのまだマージしていない発話に一致し、block の後に marker が消える。合図を持ち続ける形がこの範囲を広げた。commit: 6f1090a8 |
| G3 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 時刻の境界が marker を書いた時刻なので、PR を作った後・done の Stop の前に届いた本物の合図を数えない。commit: 6f1090a8 |
| G4 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | marker の created_at_epoch の NaN・Infinity・未来の値を読めたものとして扱い、合図を全部落とす。commit: 6f1090a8 |
| G5 | 独立-2 | low | no | self-inflicted | 文言 | fixed | 断片と phase-progression.md が、last_user_text を時刻で区切らないことを書かず、実装より広い規定を書いている。commit: 6f1090a8 |
| G6 | 独立-2 | low | no | self-inflicted | テストの検出力 | fixed | テストの skill の前置きの fixture が、合図の語を含む実物の本文を表していない。commit: 1218eb0f |
| G7 | 独立-2 | low | no | inherited | 受理集合の対称性 | accepted | UserPromptSubmit hook の合図の受理集合が Stop hook と違う |
| G8 | 独立-2 | advisory | no | self-inflicted | style | accepted | marker の JSON を何回も parse している |
| G9 | 独立-2 | advisory | no | self-inflicted | 配線 | accepted | 置き直しの条件が isMeta を見ず、人間の行に origin.kind human が付くという未確認の形に頼っている |
| H1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 境界に PR の URL の初出を created_at より優先するので、PR を作った record の無い別の session で、合図の後に assistant が URL を書くと合図が外れて block しない。commit: b682175f |
| H2 | 独立-3 | high | yes | self-inflicted | fail-open | accepted | 列挙: human_origin_seen が queued の attachment.origin でも立つので、top-level に origin の無い typed の「マージした」が候補から消える |
| H3 | 独立-3 | high | yes | self-inflicted | fail-open | accepted | 列挙: MANUAL_MERGE_RE の後ろ読みの許可リストで、「マージしたんで」「マージした後」などの本物の報告が合図にならない |
| H4 | 独立-3 | medium | no | self-inflicted | 受理集合の対称性 | accepted | UserPromptSubmit hook の合図の判定が部分一致のままで、Stop hook の受理集合と食い違う |
| H5 | 独立-3 | medium | no | self-inflicted | テストの検出力 | fixed | テストの created_at がどれも未来の値で、有効な created_at を境界にする分岐を固定していない。commit: 5a3f937d |
| H6 | 独立-3 | medium | no | inherited | fail-open | accepted | 許可リストの中にも未マージの発話（「マージした 方がいい？」「not merged yet」「マージしたよね？」）に一致する形が残る |
| H7 | 独立-3 | low | no | self-inflicted | 文言 | fixed | 断片が、origin を書かない transcript の直近のユーザー入力を時刻で区切らないことと、origin の無い行の範囲を書いていない。commit: b682175f |
| H8 | 独立-3 | advisory | no | self-inflicted | 文言 | fixed | 断片の Affected Files に merge-gate-evidence.sh のコメントの変更が無い。commit: b682175f |
| H9 | 独立-3 | advisory | no | inherited | 独立性 | accepted | テンプレート外の記述あり: 起動時の git status の commit の件名に巡の ID と経緯が入っていた |
| M4 | 方針メモ-4 | - | - | - | - | - | なし |
| J1 | 独立-4 | high | yes | self-inflicted | fail-open | accepted | 列挙: 境界を下げる先が assistant の本文の URL の初出だけなので、gh pr create の tool_result に URL が出てから本文に書くまでの間に queued で届いた合図を数えない。方針メモ-4 の決定（確かめの巡で high が出たら止める）で直さない |
| J2 | 独立-4 | medium | no | self-inflicted | テストの検出力 | accepted | 合図の時刻が読めないテストの created_at が未来の値で、境界が効いた状態で読めない合図を数える分岐を固定していない |
| J3 | 独立-4 | low | no | self-inflicted | 文言 | accepted | docstring と断片の「PR を作った後・marker を書く前の合図も数える」が、本文に URL を書く前の区間を含むように読める |
| J4 | 独立-4 | low | no | self-inflicted | 文言 | accepted | 文書の「今より後でない」とコードの 60 秒の許容が合わない |
| J5 | 独立-4 | low | no | self-inflicted | 文言 | accepted | phase-progression.md から「発話の時刻が読めないときは数える」が落ちた |
| J6 | 独立-4 | low | no | self-inflicted | 文言 | accepted | テストの class docstring が古い境界の規定のまま |
| J7 | 独立-4 | low | no | self-inflicted | 文言 | accepted | resolve_block のコメントが別の session の場合を外している |
| J8 | 独立-4 | low | no | self-inflicted | 文言 | accepted | テストの module docstring が、合図を last_user_text から取る古い設計のまま |
| J9 | 独立-4 | low | no | inherited | 受理集合の対称性 | accepted | UserPromptSubmit hook の合図の受理集合が Stop hook と違う |
