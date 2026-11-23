---
lane: L1+
follow_up_of: 454
amends: 20261013-merge-gate-binding-steering.md
pr: 旧#483
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-14T09:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f1dd2df2221b2a23000fd50ef92980a1d59a25b5 | 1 | 2 | 1 | 2026-10-14T10:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-10-14T11:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e1a23afb6ffebb71a6a8ddec47fb775a67f68f86 | 1 | 4 | 1 | 2026-10-14T12:10+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-14T13:20+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2339bd23b7ef3b2d502078735bc61b75fde53352 | 0 | 1 | 0 | 2026-10-14T14:10+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 2e5834e36aa338cb4a726c9e46111ed2b43de37d | 0 | 0 | 0 | 2026-10-14T14:40+09:00 |
| 独立-5 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 7dbc5daa04b9ce72e010738f07847141579878c7 | 1 | 0 | 1 | 2026-10-14T15:20+09:00 |
| 方針メモ-4 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-10-14T15:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ-1 | low | no | self-inflicted | design | fixed | 14 は新しい root で steering だけを求め直す（marker を求め直すと通常の worktree では所有なしになり、台帳の miss で通る）。2 は PROJECT_ROOT からの引き直しを足さず、コメントと限界で閉じる（該当 0 本、別 clone の限界を開き直す）。7 はコメントで閉じる。6 は realpath の制御文字も落とし、同じ state で絶対の worktree が 2 つ残る形は実測 0 件。15 は worktree_path に `\ud800` を書いてテストする。ユーザーは B を選んだ。commit: なし（方針） |
| r1-1 | 独立-1 | high | yes | self-inflicted | binding-reach | fixed | 列挙: lookup の `.steering/` の条件が marker の無い経路にも効き、worktree の registry の binding が `.steering/` の外の state を指す GDD の PR が、証跡の検査から台帳の miss で通る形に変わる。依頼の 14（B: steering を求め直す）を lookup を狭める手段に置き換えた marker 不在の経路は条件を当てず base に戻し、root の steering に対象 PR が無いときの切り替えだけ、1 件に決まった binding の state が .steering/<slug>/state.md のときに限る。B のとおり切り替え後に steering を求め直す（方針メモ-2）。commit: e1a23afb |
| r1-2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | repo-root-unresolvable の案内の「cwd が git の外なら cd <worktree> && で」は、cd 先に marker が無いと root が決まらず binding を引かないので、同じ block に戻る。断片・SECURITY.md の条件も root を決められることを書いていない 案内・断片・SECURITY.md の条件を、hook が root を決められることを含めて書き、git の外のセッションのテストを足した。commit: e1a23afb |
| r1-3 | 独立-1 | medium | no | self-inflicted | test-power | fixed | UNRESOLVABLE・相対の worktree_path・改行の state_path のテストが、分岐を消しても落ちない UNRESOLVABLE は marker の無い経路、相対の worktree_path は hook の cwd から解決できる値で確かめ、変異で落ちることを確かめた。改行の state_path は単独で落ちる形を作れない（PR 本文に書く）。commit: 66572967 |
| r1-4 | 独立-1 | low | no | self-inflicted | product | fixed | 依頼の 16 の実測のコマンドが再実行できる形で無い。`.steering/` の外の state を指す binding の件数も無い PR 本文に、transcript の集計と binding の集計のコマンド、`.steering/` の外の state を指す binding の件数を書く。commit: なし（PR 本文） |
| r1-5 | 独立-1 | low | no | self-inflicted | test-power | fixed | `.steering/` の外の state のテストは base でも通り、コメントも今のコードで成り立たない root の作業中の steering 2 件と stale marker の形にし、reason まで assert した。commit: 66572967 |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | lookup の `*` が深さ 2 以上の state も通し、照合（深さ 1）とずれる。出口のコメントが経路ごとの違いを書いていない 深さ 1 の判定を python 側で行い、出口のコメントを経路ごとに書いた。commit: e1a23afb |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | SECURITY.md の「だけである」が直後の例外と食い違い、番号だけの merge の条件の書き方が一部だけ SECURITY.md の条件を例外つきに書き直し、番号だけの merge の条件を肯定の形で書いた。commit: e1a23afb |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストの docstring に「同じ判定」が残る docstring を「同じ binding を引く」にし、例外は lib のコメントを指す。commit: 66572967 |
| r1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files にテストと amends の断片が無い Affected Files にテストと amends の断片を足した。commit: e1a23afb |
| r1-10 | 独立-1 | low | no | self-inflicted | test-power | fixed | binding が 2 件以上のときの文を固定するテストが無い reason の文の先頭を assert した。commit: 66572967 |
| r1-11 | 独立-1 | low | no | inherited | product | fixed | hook の `.steering/` の外の binding の steering-ambiguous の文が `_mg_action` の外で、観測から始まる `_mg_action` のキー steering-outside-binding に移し、ユーザーへの確認から始めた。commit: e1a23afb |
| r1-12 | 独立-1 | advisory | no | self-inflicted | product | accepted | 依頼の中の「18 項目」と、この PR の 17 項目が合わない。PR 本文に書く |
| pm2-1 | 方針メモ-2 | low | no | self-inflicted | binding-reach | fixed | 列挙: r1-1 は (a)。依頼の 14 の手段の置き換えなので件数（外の state を指す binding 70 件中 2、worktree 自身の registry 0）では (b) にしない。条件はループで数から外さず、1 件に決まったときだけ見る（many は base のまま止める）。marker 不在の経路は base のまま。切り替え後の求め直しは条件がある限り観測できる違いを出さない。commit: e1a23afb |
| r2-1 | 独立-2 | high | yes | self-inflicted | binding-reach | fixed | 切り替えの条件（held）が state.md の名前を見ず、`.steering/<slug>/other.md` を指す binding で切り替え、求め直しで none になり台帳の miss で通る（base は glob で外していた）。入力: binding の state_path の名前が state.md でないもの 1,039 件中 0 切り替えの条件（held）に state.md の名前を足し、`.steering/<slug>/other.md` を指す binding のテストを足した（方針メモ-3 の A）。commit: 38124598 |
| r2-2 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | SECURITY.md に「`.steering/` の下に持たない binding は当たりにしない」が残り、実装（数えて、切り替えだけ限る）と食い違う |
| r2-3 | 独立-2 | medium | no | self-inflicted | test-power | fixed | `\ud800` は realpath で例外になり binding ごとの try で落ちるので、書き出しの try を外す変異が落ちない見込み。PR 本文の変異注入の記述が裏付けられない PR 本文の変異注入の記述から「出力を try の外に戻す」を外し、落ちるテストが無いことを限界に書いた（方針メモ-3 の A）。commit: なし（PR 本文） |
| r2-4 | 独立-2 | medium | no | self-inflicted | product | fixed | 依頼の 11 の改行入りの state_path のテストは、名前が `state.md\n` の実ファイルで分岐を固定できるのに、限界に回した 名前に改行を含む実ファイルを置き、改行の除外を外すと落ちることを確かめた（方針メモ-3 の A）。commit: 38124598 |
| r2-5 | 独立-2 | medium | no | self-inflicted | product | fixed | 依頼の 10: repo-root-unresolvable の案内の先頭が「cd <worktree> && gh pr merge の形で」のままで、git の外のセッションでは効かない 案内を、repo の中を cwd にしたセッションからの明示の merge から始め、cd の形は marker のある worktree に限った（方針メモ-3 の A）。commit: 38124598 |
| r2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | in-steering のコメントの理由が、求め直しを足した後の実装と合わない |
| r2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | root を決められる条件の書き方が、hook・断片 2 本と SECURITY.md で違う（payload の cwd の marker） |
| r2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `.steering/` の外の binding のテストのコメントと名前が古い意味のまま |
| r2-9 | 独立-2 | low | no | self-inflicted | test-power | accepted | 外の state のテスト（stale marker）は切り替えの条件を外しても通る |
| r2-10 | 独立-2 | low | no | self-inflicted | test-power | accepted | 2 件以上の文の assert が、`.steering/` の外の文と区別できない |
| r2-11 | 独立-2 | low | no | self-inflicted | test-power | accepted | 対象を決められない merge のテストが無出力の落ちを区別せず、root の steering のテストが reason を見ない |
| r2-12 | 独立-2 | low | no | self-inflicted | product | accepted | marker の無い経路で root の registry の外の binding へ切り替え、worktree の URL 未記録の steering で pr-url-unrecorded に止まる変化（止める側）が断片に無い |
| pm3-1 | 方針メモ-3 | low | no | self-inflicted | binding-reach | fixed | 安全策 4（同じクラスタ binding-reach の high が 2 巡）。Opus・Fable とも A。ユーザーは A を選んだ: r2-1 は切り替えの条件に state.md の名前を足して閉じ、依頼から外れた r2-4・r2-5 と PR 本文の誤り（r2-3）を直し、ほかの medium・low は accepted にして限界に書き、3 巡目を回す。3 巡目で high が出たら直さずに限界に書いて渡す。commit: 38124598 |
| r3-1 | 独立-3 | medium | no | self-inflicted | test-power | fixed | 案内の先頭の書き換えで「repo 内のディレクトリ」の語が消え、test_merge_gate_hook_gate_activation.py の文言テストが落ちる。案内の先頭をその語で書き直した。commit: ab15966c |
| r3-2 | 独立-3 | low | no | self-inflicted | test-power | accepted | state.md でない名前を指す binding のテストの assert が block かどうかだけで、切り替えないことまでは固定しない |
| r3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 台帳 hit で repo-root-unresolvable を出す経路では、案内の先頭の動作が今打ったコマンドと同じで、本当の出口（人が merge）は括弧の末尾にしか無い |
| r3-4 | 独立-3 | low | no | inherited | doc-claim | accepted | 案内の括弧の中の binding の説明が、例外（番号だけの merge・GH_REPO・名前の条件など）を持つのに全称で書かれている |
| r3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の切り替えの条件が名前の条件を含まず、「当たりにしない」も実装（数えて、marker のある root の切り替えだけ限る）と違う |
| r3-6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の「案内どおり GDD worktree へ cd しても」が、新しい案内の先頭に合わない |
| r3-7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界に、marker の無い経路で state.md でない名前を指す binding の形（台帳で決まる。main と同じ）が無い |
| r3-8 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の項目数の経緯と、変異注入の結果の断定。次の巡の前に抜粋から除く |
| r4-1 | 独立-4 | low | no | inherited | product | accepted | 案内の先頭の「repo 内のディレクトリ」が対象 PR の repo を指さず、別の repo から -R で打った台帳 hit の merge では解決にならない |
| r4-2 | 独立-4 | low | no | inherited | doc-claim | accepted | 括弧内の「番号か URL で明示した merge は binding で判定する」が、番号だけの merge の remote の条件・GH_REPO・対象を決められない merge の除外を書かずに言い切る |
| r4-3 | 独立-4 | low | no | inherited | doc-claim | accepted | 括弧内の root の条件から payload の cwd の marker が抜け、SECURITY.md と食い違う（旧#454 の断片も同じ） |
| r4-4 | 独立-4 | low | no | inherited | doc-claim | accepted | 台帳 hit で止める呼び出し元のコメントが、案内を「GDD の worktree へ誘導」と書いたまま |
| r4-5 | 独立-4 | advisory | no | self-inflicted | style | accepted | 断片・PR 本文・案内の括弧内に「repo の中」の語が残り、先頭の「repo 内のディレクトリ」とそろっていない |
| r5-1 | 独立-5 | high | yes | inherited | fail-open | accepted | marker の無い経路で binding で切り替えた後、新しい root で対象 PR の steering を解決できない（root の registry の binding が `.steering/` の外の state を指す、worktree 自身の binding が終端・branch 違いの外の state を指す）と、素通りの出口で台帳の miss だけを見て証跡を見ずに通る（main・旧#454 と同じ判定） |
| r5-2 | 独立-5 | low | no | self-inflicted | product | accepted | 依頼の項目 11 の「payload の cwd（Codex の workdir）」のテストを tool_input.cwd で書き、tool_input.workdir を送るテストが無い |
| r5-3 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の「`.steering/` の外の binding は当たりにしない」と、PR 本文・テストのコメントの「解決が binding 先を見つける」が実装と合わない |
| r5-4 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | binding を引く条件の書き方が SECURITY.md・断片・案内で違い（payload の cwd が抜ける）、案内は条件を言い切りすぎる |
| r5-5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界の、求め直しと出力の try の理由が実装と合わない（反例がある） |
| r5-6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | `gdd_mg_binding_switch` の `$2` の理由のコメントが、求め直しを足した後の実装と合わない |
| r5-7 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 実測の件数の単位・範囲が、PR 本文とコメントで違う |
| r5-8 | 独立-5 | low | no | self-inflicted | test-power | accepted | 切り替えた後の求め直しを外しても落ちるテストが無い |
| r5-9 | 独立-5 | low | no | self-inflicted | test-power | accepted | 出力の try と、実パスの制御文字の検査を元に戻しても落ちるテストが無い |
| r5-10 | 独立-5 | low | no | self-inflicted | test-power | accepted | 足したテストのうち 3 本は、assert が判定を固定していない |
| r5-11 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋に実測の節がある。次の巡の前に目的か限界の節へ移す |
| r5-12 | 独立-5 | advisory | no | self-inflicted | product | accepted | 依頼の項目 1 の外の文（`.steering/` の外の binding の文）も書き換えた |
| r5-13 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 断片に利用者から見えない変更があり、amends の説明に切り替えの条件が無い |
| r5-14 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | `_mg_action` の見出しのコメントと、reason code でない新しいキーが合わない |
| r5-15 | 独立-5 | advisory | no | self-inflicted | style | accepted | コメントの折り返しと、テストのメソッドの間の空行 |
| pm4-1 | 方針メモ-4 | low | no | self-inflicted | fail-open | accepted | 安全策 4（high か blocking を含む巡が合計 3 回）。Opus の推奨は止める: r5-1 はこの PR で直さず、限界の節の先頭に「直していない常時 High・実害クラス」として書き、merge-ready とは書かずに渡す。依頼の項目 7 は方針メモ-1 で B（コメントで閉じる）、13:20 の A は「3 巡目で high が出たら直さずに限界」。main と同じ判定で後退ではない。次の PR は既定にせず、ユーザーが指示したときに、先に該当する merge の件数を測る。main の案（次の PR を既定にする）は Opus に合わせた。memory の決定（安全策 4 の続行・止めるは Opus に相談して決めてよい）により内部で決めた。commit: なし（方針） |
