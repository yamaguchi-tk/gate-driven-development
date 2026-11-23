---
lane: L1
pr: 432
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5d1aee48c2c1e67826b37a150f75e9d3358c6de2 | 1 | 1 | 1 | 2026-10-12T10:01+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 5c721e5fcd73c338c316b9441ec02ef00e374f23 | 1 | 0 | 1 | 2026-10-12T10:16+09:00 |
| 方針メモ-1 | user | - | 0 | 0 | 0 | 2026-10-12T10:16+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | yes | inherited | root-selection | accepted | `cd <GDD worktree> && gh pr create`・`git push` で移動先に marker が無いと、pre-PR gate と pre-push gate が検査せずに通す。root の選び方が merge gate（marker を持つ候補を先に採る）とそろっていない。pre-PR 側は 25 本、pre-push 側は 09-28 以降の 872 件中 44 件。ユーザーの決定（依頼の原文の 2026-10-12 の確認）で直さず、旧#431 に追記した |
| F2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | SECURITY.md § 制限事項の「pre-PR gate は事故で打つ形から守る」が、足した限界（agent が打つ cd の形を検査しない）と食い違う。§ 制限事項に例外と参照を足した。commit: d9d79f02 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「検査せずに通す（completion-check もしない）」が、走る raw task steering の検査を書かず、飛ばす PR body の機密の検査などを書き漏らしていた。走る検査と飛ばす検査を分けて書いた。commit: d9d79f02 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「移動先の worktree に marker が無いので」が常にそうだと読める。marker は /gdd-dev を始めた root にだけ作られると書き、「無いと」の条件にした。commit: d9d79f02 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「出口の無い block」は言い過ぎ（kill switch を案内する。marker のあるセッションからは別の経路）。「marker を持つ場所の無いセッションからは…出口は kill switch か人の手の merge」とした。commit: d9d79f02 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「未登録の 36 本のうち 22 本」の数の関係が読めず、11 本の原因が無かった。36 本の内訳（25・11・仮に載っても当たらない 22）に書き直した。commit: d9d79f02 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 導入先向けの SECURITY.md に、開発元の実測の件数と「観測されていない」を範囲なしで載せていた。SECURITY.md からは件数を外し「マージの承認は人が持つ」という帰結にした（件数はコードのコメントに残す）。commit: d9d79f02 |
| F8 | 独立-1 | low | no | inherited | ledger-hit-deadend | fixed | いまも台帳で hit した PR は、marker の無いセッションからは案内どおり cd しても止まり続ける。限界の文（2 か所）に足した。merge gate の扱いは変えない。commit: d9d79f02 |
| F9 | 独立-1 | low | no | self-inflicted | request-scope | fixed | PR 本文が 旧#431 を completion-check の素通りとしか書かず、別案の実測 3 点といつ直すかに触れていなかった（旧#431 本文には 3 点と「いつ直すか」がある）。PR 本文に書いた。commit: なし（PR 本文） |
| F10 | 独立-1 | advisory | no | self-inflicted | request-scope | accepted | 依頼が求めた当時の root checkout の版の確認結果が PR 本文に無い。PR 本文に書く（a751817a・a424a7c1） |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 限界の文に 旧#431 の参照が無かった。2 か所に添えた。commit: d9d79f02 |
| F12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Summary が「SECURITY.md の冒頭」と読め、pre-PR gate が検査しないことに触れていなかった。直した。commit: d9d79f02 |
| F13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 限界に、旧#429 の root の決め方の後も限界の文が成り立つかを衝突の解消時に確かめる、と書いていない。PR 本文に書く |
| F14 | 独立-2 | high | yes | inherited | root-selection | accepted | 列挙: 独立-1 の F1 と同じ欠陥（pre-PR gate・pre-push gate の root の選び方が merge gate とそろわず、`cd <marker の無い GDD worktree>` の形を検査せずに通す）。常時 High なので再掲にできない。閉じ方: 列挙。方針メモ-1：この形は transcript に 25 件・44 件あるので規定の既定は (a) だが、ユーザーが 2026-10-12 に同じ欠陥を直さず 旧#431 に足すと決めた（依頼の原文）のでそれに従い accepted。Opus 設計レビュー: 呼んでいない（同じ欠陥の扱いをユーザーが決定済みのため） |
| F15 | 独立-2 | medium | no | self-inflicted | doc-claim | next-pr | SECURITY.md § 制限事項の例外が pre-PR gate だけで、同じ形を通す pre-push gate を書いていない。:109 と gdd-pr-roots.sh の 旧#431 の範囲も PR 作成時だけ |
| F16 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 飛ばす検査の列挙に Codebase Health・`--head` の照合・steering の一意性が無い。raw steering の検査は base ref が決まるときだけ走る。§ 制限事項の「検査しない」と :109 の「raw だけ走る」が食い違う |
| F17 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「マージの承認は人が持つ」が、GDD が承認を保証すると読める。導入先の運用で担保すると書く |
| F18 | 独立-2 | low | no | inherited | ledger-hit-deadend | next-pr | merge gate の案内（:180）とコメント（:771-772）が「GDD worktree で証跡を検査する」と書き、marker の無い worktree では止まり続ける限界と逆を言う |
| F19 | 独立-2 | low | no | self-inflicted | request-scope | fixed | PR 本文が、旧#431 に pre-push 側の 44 件と root の選び方の修正案を追記したことを書いていない（追記は済み: 旧#431 のコメント）。PR 本文に書いた。commit: なし（PR 本文） |
| F20 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の 旧#1158・旧#1165 は別 repo の PR なのに、この repo の番号としてリンクされる。repo 名つきにした。commit: なし（PR 本文） |
| F21 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 件数の数え方（transcript の範囲・条件）が PR 本文に無い。PR 本文に 1 行書く |
| F22 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | SECURITY.md の Issue 参照は導入先から辿れないことがある |
| F23 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「通常の GDD worktree には無い」は、worktree で /gdd-dev を実行すれば作られる点が読み取りにくい |
| F24 | 方針メモ-1 | - | - | - | - | - | なし |
