---
lane: L1+
pr: 旧#191
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user | - | 1 | 2 | 1 | 2026-09-25T00:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f42fa95ec4f2b6a82f49d53d4c2de2df63ea080c | 4 | 1 | 4 | 2026-09-25T02:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 36b24214aac13be6729858d152640e8e0e0e91c7 | 1 | 0 | 1 | 2026-09-28T10:30+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) + Fable (general-purpose, model: fable) + user | - | 0 | 0 | 0 | 2026-09-28T12:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | 68ac2350ad701d6480fce69d2eaf4ad96419e91c | 0 | 0 | 0 | 2026-09-28T14:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 方針メモ | high | yes | inherited | merge-target | fixed | 修正後は primary が active の steering を返し、merge gate の PR URL 照合（multiple のときだけ走る）を通らなくなる。対象 PR の steering が検査されずに通る。user 判断でこの PR で閉じる（primary の steering の PR URL が明示された対象と一致しないとき、全 state.md で照合し直す） |
| A2 | 方針メモ | medium | no | inherited | helper | fixed | ヘルパーは新設せず session-start の _gdd_strip_pipe_tail を値を受ける形で detect-steering.sh に移す |
| A3 | 方針メモ | medium | yes | inherited | empty-head | fixed | ヘルパーは比較だけに使い、代入と空判定は切り出す前の値のままにする（pre-PR で tasklist の空 head から state.md へ読み直して通る経路を作らない） |
| A4 | 方針メモ | low | no | inherited | rationale | fixed | 狭い側（ASCII のパイプだけ）の根拠を、文法と同じ入力を読む既存の 5 実装との対称性に差し替える |
| A5 | 方針メモ | low | no | inherited | union-blocked | out-of-diff | union が Next Action の blocked を拾わない既存のずれ（コメントと食い違う） |
| B1 | 独立-1 | high | yes | self-inflicted | merge-target | fixed | merge gate の照合し直しが many と PR URL 未記録の none を捨て、found の active のまま進んで素通りする（base の multiple 経路では block だった） |
| B2 | 独立-1 | high | yes | self-inflicted | union-multiple | fixed | pre-push で素の done と注記つき done が並ぶと union が 2 件で multiple になり exit 0（base では注記つきが active 扱いで検査されていた） |
| B3 | 独立-1 | high | yes | self-inflicted | union-blocked | fixed | Next Action が blocked の注記つき steering が primary で除外され union も拾わず、pre-push と merge が検査されない |
| B4 | 独立-1 | high | yes | inherited | stale-brainstorming | fixed | gdd_is_stale_brainstorming_candidate が Resume From を生値で比べ、注記つきの古い brainstorming が候補に残って multiple になる |
| B5 | 独立-1 | medium | no | inherited | stop-hook-human-check | fixed | gdd_stop_hook.py の markerless human-check fallback が Resume From を生値で比べ、注記つき human-check-waiting で発火しない |
| B6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | lint と同じ受理集合という記述の言い過ぎと、限界の節の別実装の列挙漏れ |
| C1 | 独立-2 | high | yes | inherited | pre-push-multiple | fixed | primary の multiple（非終端 2 件以上）で pre-push が検査せずに exit 0 する。文法外の値（Done・**done**・done (merged)・全角の注記）は active と数えられてこの経路に落ちる。安全策 4 の発火で HITL に回す |
| C2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | Next Action blocked の追加と steering-multiple の block を、self-review-lanes.md の blocked の節とテストの docstring が反映していない |
| C3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | block の文言（完了済み・片付けて）と断片の User Action Required が、対象集合・止まる条件・merge gate の新しい block と合わない |
| C4 | 独立-2 | low | no | self-inflicted | merge-target | fixed | merge gate の単一 found 経路の pr-url-unrecorded が、cancelled など検査対象外の steering の URL 欠落でも発火する |
| C5 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | bind された注記つきの古い brainstorming が素の値と同じく検査対象から外れる（通す向きの変化）ことが PR 本文に無い |
| D1 | 方針メモ-1 | advisory | no | self-inflicted | process | fixed | 独立-1 の B2（終端 2 件の multiple）と独立-2 の C1（非終端 2 件の multiple）が同じ種類の high として 2 巡続き、安全策 4 が発火した。実測は Opus が gdd_detect_active_steering を registry 解決込みで走らせ multiple 18 checkout、うち active 6（全て GDD を使う別の repo の git 追跡された古い steering）。Opus の推奨は B（primary の multiple でも pre-push を block し pre-PR とそろえる。tip の sha で 1 件に決める案 C は次の PR）でメインの案と一致。ユーザーの指示で Fable にも相談し、推奨は B で一致。Fable の訂正は 3 点（session_id が一致しないと step 5 で通るので 6 件の実効はほぼ 0、merge gate の対象 PR で解決する設計が C の前例、block 文言は reason で分けず 1 本にする）。ユーザーは B を選んだ。C1 はこの PR で直す |
| E1 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界と実データが tip と合わない（全角の注記は multiple で止まる。marker を書いた本人のセッションからの push も止まる）。PR 本文を書くときに直した |
| E2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | session-start の multiple 警告の復旧案内（worktree ごと削除、tasklist の Next Action を cancelled）が pre-push の block と食い違い、案内どおりでは解けない |
| E3 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 全角の注記のテストが steering 1 件だけで、全角で切る実装と切らない実装を判別できない |
| E4 | 独立-3 | low | no | self-inflicted | test-power | next-pr | merge gate の照合し直しのテストが、対象の steering で判定したこと（approval-missing）を固定していない |
| E5 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 断片の Summary の merge gate の記述に、所有 marker が無いときだけという条件が無い |
| E6 | 独立-3 | low | no | self-inflicted | bookkeeping | next-pr | 断片に利用者から見えない置き換えと経緯の記述があり、追加したテストのファイル名が Validation に無い |
| E7 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の type patch の理由を PR 本文に書く |
| E8 | 独立-3 | advisory | no | self-inflicted | style | accepted | multiple-terminal を読む production のコードが無い |
| E9 | 独立-3 | advisory | no | self-inflicted | style | accepted | steering-multiple の block 文に関係の無い復旧手順が付く |
| E10 | 独立-3 | advisory | no | self-inflicted | style | accepted | 照合し直しの many で出る steering-ambiguous の案内が経路に半分しか合わない |
| E11 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 他の gdd_detect_active_steering の呼び出し元への影響が PR 本文に無い。PR 本文に書いた |
| E12 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 新しいコメントが pipe で切らない理由を PR URL の読み手と書いているが、依存するのは証跡行の parser |
