---
lane: L1
pr: 旧#162
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 797db11e7ed5f4c2a34e1c169ad02cc2de83c008 | 0 | 4 | 0 | 2026-09-20T14:51+09:00 |
| PR後-1 | Cursor / Grok 4.6（PR 上のレビュー） | 0257ea41c955f751b086e5928c5c8da98d8acce5 | 0 | 3 | 0 | 2026-09-20T15:03+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 7d8b6e5597fdc18eecda6b0e37cf74fca71a9cb4 | 0 | 2 | 0 | 2026-09-20T15:21+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | 3985cb31f1178d06f243d6056b19cf20fcb63843 | 0 | 1 | 0 | 2026-09-20T16:28+09:00 |
| PR後-3 | Cursor / Grok 4.6（PR 上のレビュー） | 85309c12ad8a0c7bfe003ee1a1ad399fa3989e66 | 0 | 0 | 0 | 2026-09-20T16:55+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分, model: opus | a0ba2384578d294bac3167e95ca860afc8823457 | 0 | 0 | 0 | 2026-09-20T17:18+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | rule-exception-not-propagated | next-pr | 近道と 3 巡目の「① の medium・low は `next-pr`」に、同じ規定を定める全レーン共通（CLAUDE.md の「① に当たるもの…は、例外としてこの PR で直す」）と、`next-pr` の行き先（② と ③ だけを列挙）と、旧規定を名指す手順 6 再掲の「下の最終巡の打ち切りの分」が追随していない。main がどちらに従うか決められる。次の PR で 3 か所を揃える |
| A2 | 独立-1 | medium | no | self-inflicted | path-class-gap | fixed | 「規則の文書」に repo root・plugin の CONTRIBUTING が入らず、`docs/VERSIONING.md` § 統合先の定義（`review-log-present.sh` が読む）と `.claude-plugin/marketplace.json` の `name`（同 check の identity 判定）も区分に入らない。最終巡の後にこれらだけを変えても巡が有効のまま残る。次の PR で区分に足す。この PR で直した（a0ba2384）|
| A3 | 独立-1 | medium | no | self-inflicted | stale-canonical-pointer | fixed | CONTRIBUTING 項 1 が正本に指す `references/gdd-self-development.md` § 開発場所の使い分けは、フルスイートは completion-check と pre-PR の 2 回と書き、CI への委譲を書いていない。次の PR で同じ運用に更新するか、CONTRIBUTING 側から「全量は CI」の帰属を外す。旧#163 が先にマージされ、`gdd-self-development.md` § 開発場所の使い分けに「フルスイートは CI が回す」を書いた（この PR は 旧#163 の文面を採用）|
| A4 | 独立-1 | medium | no | self-inflicted | pr-body-vs-reviewer-instruction | fixed | `.github/copilot-instructions.md` は外部レビュー bot に、PR 本文に pytest・validate の実行結果や言及があるかの確認を求めている。「CI の結果は PR 本文に書かない」に変えたので、bot が記載なしを指摘し続けて PR後 の巡が増える。次の PR で「PR の check が success か」の確認に書き換える（`.github/` は判定のコードなので、巡を無効にする）。この PR で直した（a0ba2384）|
| A5 | 独立-1 | medium | no | self-inflicted | cap-has-no-post-pr-bound | fixed | 3 巡の上限は push までの `独立-N` だけで、最終巡の後の差分巡（PR 後）は数えず、その差分巡で high・blocking が出たときの繰り返しにも上限が無い。L0・L1 には安全策 4 が効かない。次の PR で打ち切りを足すか、PR 全体で数える。この PR で直した（a0ba2384）|
| A6 | 独立-1 | medium | no | self-inflicted | shortcut-eligibility-by-lane-name | next-pr | 近道の適用条件が「L0、または L1 の契約 md の文言修正」というレーン名で書かれ、CONTRIBUTING はどのレーンの対象にも無い。L0 の進め方は「独立レビューを要しない」と書いており、近道の 1 巡と食い違う。この PR は L0 と CONTRIBUTING の混在として近道を使った。次の PR でパス区分（判定のコードを含まない）に書き換える |
| A7 | 独立-1 | medium | no | self-inflicted | term-drift-blocking-class | next-pr | 3 巡目の後に残る指摘の分岐が「実害クラス（§ 常時 High と `is_blocking`）」と書き、`reviewer-common.md` が別概念とする 2 つを 1 語にしている。厳しい側なので取りこぼしは無いが、同じ CLAUDE.md の別の行と語彙が食い違う。次の PR で「§ 常時 High、または実害クラス」に直す |
| A8 | 独立-1 | low | no | self-inflicted | fragment-self-inconsistency | fixed | 断片の Summary が「利用者から見える変更なし」と断定しながら `#### Changed` に変更を列挙していた。Summary を「開発側の文書の規則を変えた（利用者の実行時の挙動は変わらない）」に直した。断片だけを変える commit で、手順 6 の区分では巡を無効にしない |
| A9 | 独立-1 | low | no | inherited | stale-skill-budget | next-pr | `.github/instructions/gate-driven-development.instructions.md` の skill 数の上限が 28（実際は 29）。差分は触っていない。次の PR で 29 に揃える |
| B1 | PR後-1 | medium | no | self-inflicted | merge-ready-timing-ambiguity | fixed | merge-ready を書いてよい時点が、終了条件（3 つがそろったら PR 本文に書く）と手順 7（本文は push 時に 1 回、確かめてから merge-ready と書く）で 3 通りに読める。本文には巡の sha と結果だけを書き、merge-ready と宣言するのは CI を確かめた後のユーザーへの報告だけにした（7d8b6e55） |
| B2 | PR後-1 | medium | no | self-inflicted | rule-exception-not-propagated | fixed | 独立-1 A1 の再指摘。全レーン共通・`next-pr` の行き先・再掲の条項を、近道と 3 巡目の例外に揃えた（7d8b6e55） |
| B3 | PR後-1 | medium | no | self-inflicted | shortcut-eligibility-by-lane-name | fixed | 独立-1 A6 の再指摘。近道の適用条件をレーン名でなく「判定のコードを含まない」に変え、L0 の表に混在時の扱いを足した（7d8b6e55） |
| B4 | PR後-1 | low | no | self-inflicted | pr-field-empty | fixed | `pr:` が空で本文に開示が無い。指摘時点の tip `0257ea41` の後の commit `3bcc5f63` で、すでに記入していた |
| B5 | PR後-1 | low | no | self-inflicted | term-drift-blocking-class | fixed | 独立-1 A7 の再指摘。「§ 常時 High に当たるもの、または実害クラス（`is_blocking`）」に直した（7d8b6e55） |
| B6 | PR後-1 | low | no | inherited | stale-skill-budget | re-reported | 独立-1 A9 の再指摘（`.github/instructions/…` の skill 数の上限が 28）。記録済みの `next-pr` と同じ |
| C1 | 独立-2 | medium | no | self-inflicted | l0-row-drops-shortcut-precondition | fixed | L0 の行の括弧「L1 のファイルと混ざる PR は近道の 1 巡」が、近道の前提（判定のコードを含まない）を落としている。L1 の「提案だけを出す hook」や `tests/checks/` を触る PR で、L0 の行は 1 巡、近道の条件は使えない、と正反対になる。次の PR で条件付きにする。ユーザーの指示（「2 件を今回の PR に入れて」）で、この PR で直した（23da8646）|
| C2 | 独立-2 | medium | no | self-inflicted | rule-exception-omits-harm-class | fixed | 全レーン共通と `next-pr` の行き先の新しい例外が、severity だけで書かれ、medium の実害クラス（`fail-open` など）を除いていない。`review-log-present.sh` は実害=yes の行に `next-pr` を付けると FAIL する。手順 6 側の同じ例外も同時に揃える。次の PR で優先して直す（独立-1 A1 と同じクラスタ）。ユーザーの指示（「2 件を今回の PR に入れて」）で、この PR で直した（23da8646）|
| C3 | 独立-2 | low | no | self-inflicted | shortcut-heading-stale | next-pr | 近道の見出しが「文言だけの変更」のまま、条件はパス区分になった。`plugin.json`・`evals/` などバケットに載らないファイルの扱いも未定。次の PR で見出しと区分を直す |
| C4 | 独立-2 | low | no | self-inflicted | merge-ready-wording-mixed | next-pr | 手順 6 の 78・91 行が CI を見ない時点で merge-ready と言い切る形のまま残り、86 行の宣言時点の一本化と食い違う。86 行の「だけ」も、手順 7 の PR 本文の列挙と字面で矛盾する。次の PR で揃える（B1 の残り） |
| C5 | 独立-2 | low | no | self-inflicted | term-drift-harm-class-heading | next-pr | 「直していない実害クラス」の見出しに、実害クラスでない常時 High も書かせる形になった。括弧の説明も実害=yes の行にしか掛からない。次の PR で見出しと括弧を直す |
| C6 | 独立-2 | low | no | self-inflicted | referent-covers-only-after-final | next-pr | 全レーン共通の「手順 6 の『最終の全差分巡の後に commit を積んだとき』に従う」は、最終巡より前（1 巡目・2 巡目の途中）に medium を取り込んだ場合を覆わない。次の PR で前提を満たさない場合も覆う書き方にする |
| D1 | 独立-3 | medium | no | self-inflicted | blocking-medium-sentence-contradiction | fixed | 手順 6 ① の同じ 1 文が、前半で「blocking の medium は例外にせず直す」、後半で「① の medium・low は blocking には数えない」と書き、実害クラスの medium で行き先が割れる。後半を「実害クラスでなければ blocking には数えない」にするか、`is_blocking` を単独正本にする。3 巡目の blocking でない medium なので `next-pr`。この PR で直した（a0ba2384）|
| D2 | 独立-3 | low | no | self-inflicted | test-only-commit-escapes-review | next-pr | 最終巡の後にテストだけを変える commit（テストの削除・assert の緩和）は、巡を無効にせず、どの巡にも載らない。CI は green のまま通る。次の PR で、テストをパス区分の非無効化から外すか、テストを削る・緩める commit は巡を無効にすると書く |
| D3 | 独立-3 | low | no | self-inflicted | cap-count-not-machine-distinguishable | next-pr | 3 巡の上限が数えない「最終巡の後の差分巡」も `独立-N` で記録され、reviewer 列の `範囲: 差分` は中間の差分巡と同じ値になる。行の値で判別できない。次の PR で reviewer 列に宣言トークンを足す |
| D4 | 独立-3 | low | no | self-inflicted | shortcut-first-round-vs-final-round-precondition | next-pr | 「最終の 1 回は差分巡で high=0・blocking=0 になった後に回す」（59 行）が、先行する差分巡の無い近道の 1 巡目を最終巡とする規定（82 行）と食い違う。次の PR で 59 行に近道の但し書きを足す |
| D5 | 独立-3 | low | no | self-inflicted | codex-step-stale-return-pointer | next-pr | 手順 5（Codex）だけが「手順 6 の終了条件に戻る」の旧い言い方のまま。手順 7 と全レーン共通は「最終の全差分巡の後に commit を積んだとき」に直した。次の PR で揃える |
| D6 | 独立-3 | low | no | self-inflicted | fragment-affected-files-mismatch | fixed | 断片の Affected Files が「手順 3」を挙げているが、差分に手順 3 の変更は無い（手順 3 は 旧#163 の文面を採用）。「手順 4・6・7」に直した。断片だけを変える commit で、手順 6 の区分では巡を無効にしない |
| D7 | 独立-3 | low | no | self-inflicted | rule-not-in-changelog-policy | next-pr | 断片の内容規則（利用者から見える変更だけ・巡ごとに書き足さない）が `CHANGELOG.md` § Policy に入っていない。次の PR で § Policy に 1 行足し、CONTRIBUTING と root CLAUDE.md はそこを指す |
| D8 | 独立-3 | advisory | no | self-inflicted | fragment-validation-narrower-than-related-tests | next-pr | 断片の Validation に挙げたテストが、手順 3 の grep で当たる「関係するテスト」より狭い。実害は無い（該当テストは差分が消した文字列に依存していない）。PR 本文に列挙する |
| D9 | 独立-3 | advisory | no | self-inflicted | post-final-round-diff-cycle-unbounded | re-reported | 独立-1 A5 と同じ（最終巡の後の差分巡の繰り返しに上限が無い）。記録済みの `next-pr` と同じ。A5 は a0ba2384 で直した（2 回目の起点の書き方は G4）|
| F1 | PR後-3 | medium | no | self-inflicted | blocking-medium-sentence-contradiction | re-reported | 独立-3 D1 の再確認（`CLAUDE.md:67` の 1 文が、前半で blocking の medium は直す、後半で medium・low は blocking に数えない、と割れる）。同じ指摘。D1 は a0ba2384 で直した |
| G1 | 独立-4 | medium | no | self-inflicted | path-class-gap-plugin-json | next-pr | パスの区分に `.claude-plugin/plugin.json` が入らない。`version-not-consumed.sh` が manifest version の入力として読み、PASS / FAIL を決める。括弧の根拠「`review-log-present.sh` が読む」も、`changelog.d/`・`review-log/` まで判定のコードにしてしまう基準になっている。次の PR で plugin.json を足し、根拠を「中身を読んで検査の結果を決める入力」に書き換える |
| G2 | 独立-4 | medium | no | inherited | merge-ready-wording-mixed | next-pr | 手順 6 の 91 行（と 78 行）が、CI の条件を落として「merge-ready とする」のまま。86〜89 行の 3 条件と、宣言はユーザーへの報告だけ、の規定と食い違う。独立-2 の C4 と同じ箇所で、この巡で severity が medium に上がった。次の PR で「終了条件の 1・2 つ目を満たしたものとする」に直す |
| G3 | 独立-4 | low | no | inherited | github-dir-bucket-too-coarse | next-pr | `.github/` をディレクトリごと判定のコードにしているため、外部 bot 向けの散文 `.github/copilot-instructions.md` だけを直す PR でも近道が使えない。次の PR で判定のコードを `.github/workflows/`・`.github/actions/` に絞り、散文を規則の文書に移す |
| G4 | 独立-4 | low | no | self-inflicted | second-diff-round-origin-unspecified | next-pr | 追記した「その 2 回目の後も残ったら」の数える単位が無い。巡が無効になるたびに 2 回か、PR で通算 2 回かで、3 回目の指摘の扱いが割れる。次の PR で「巡が無効になるたびに、差分巡は 2 回まで」と書き、実害クラスが残ったときの書き方（限界の節の先頭）も足す |
| G5 | 独立-4 | advisory | no | self-inflicted | fragment-changed-omits-github-file | next-pr | 断片の Changed に `.github/copilot-instructions.md` が無い（Affected Files にだけ挙げた）。姉妹断片 `20260920-contributing-full-suite-in-ci.md` は取り消した側の規則を書いている。配布物ではないので、断片に書くか、リリースノートの食い違いを受け入れるかはユーザーの判断。PR 本文に列挙する |
