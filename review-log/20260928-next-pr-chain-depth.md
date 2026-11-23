---
lane: L1
pr: 210
follow_up_of: 202
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5165197e4f42254d22e47ffcd77569c3aec46dca | 0 | 1 | 0 | 2026-09-28T19:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 3b74aad375f512f5ec0142dd51eeb92a96cd5be3 | 0 | 0 | 0 | 2026-09-28T20:05+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| N1 | 独立-1 | medium | no | self-inflicted | follow-up-wiring | fixed | 経路: 差分の ① の例外 → 同じ規定を定める全レーン共通の 1 点目（`CLAUDE.md:183`）。例外が無く、後続 PR でも next-pr にする読みが残る。例外の参照を足しテストで固定した（699fda9a）。この PR 自身は follow_up_of: 202 で新しい規定では accepted になるが、規定の配線の欠けでこの PR の目的が半分しか効かないため、ユーザーの「Fable に相談しながら自律的に」の指示のもと、Fable の推奨で直した |
| N2 | 独立-1 | low | no | self-inflicted | follow-up-wiring | fixed | 無効化後の差分巡（`CLAUDE.md:97`）が「直さず next-pr にする」と言い切っていた。例外の参照を足した（699fda9a）。直した理由は N1 と同じ |
| N3 | 独立-1 | low | no | self-inflicted | follow-up-wiring | fixed | 再掲の条件（`CLAUDE.md:70`）の origin の例外に、後続 PR で accepted にした ① の medium・low が無く、再報告が 2 回数えられる。足した（699fda9a）。直した理由は N1 と同じ |
| N4 | 独立-1 | low | no | self-inflicted | measurement-wording | fixed | テンプレート外の実測値のコマンドに revision が無く、9 本のうち 3 本は報告ではない行に語が出るだけ。コマンドに `a00e872d` を入れ、3 本を分けて書いた（62cf2e4d） |
| N5 | 独立-1 | low | no | self-inflicted | measurement-wording | fixed | 連鎖の実測値「next-pr 26 行・fixed 6 行」の fixed が再現しない（8 行）。時点・数え方が無い。数字を消し、PR 番号の連鎖だけを残した（62cf2e4d） |
| N6 | 独立-1 | low | no | self-inflicted | follow-up-wiring | accepted | 手順 5 の Codex の medium・low は、後続 PR でも next-pr のまま。Codex は 1 PR 最大 1 回・発火条件つきで連鎖の入口として細いので、規定は足さず PR 本文の限界の節に書いた |
| N7 | 独立-1 | advisory | no | inherited | template-outside-harness | accepted | `advisory: テンプレート外の記述あり`。harness が差し込んだ gitStatus の直近 commit の件名（実装の順序）。判断には使っていない。手順 6 のとおり巡は有効のまま |
| N8 | 独立-1 | advisory | no | self-inflicted | follow-up-wiring | fixed | この PR 自身が Issue 旧#202 の「いつ直すか」から作った PR で、新しい手順 1 では follow_up_of の宣言が要る。この review-log に `follow_up_of: 202` を書いた |
| N9 | 独立-1 | advisory | no | self-inflicted | test-fixture | fixed | 配線テストの例が codex-1 の行を ① の例に使っていた。独立-1 の行にした（21191e0e） |
| N10 | 独立-1 | advisory | no | inherited | review-diff-scope | accepted | 差分の pathspec が `review-log/` を丸ごと除くので、`review-log/README.md` の変更が独立レビューに届かない。reviewer は現物を読んで矛盾が無いことを確かめた。PR 本文に書いた |
| N11 | 独立-2 | advisory | no | inherited | template-outside-harness | accepted | `advisory: テンプレート外の記述あり`。harness の gitStatus の直近 commit の件名に巡の ID と修正の順序が入っていた。判断には使っていない。手順 6 のとおり巡は有効のまま |
| N12 | 独立-2 | low | no | self-inflicted | test-power | accepted | 再掲のテストが句の有無だけを見て、向き（「は、`origin` を問わない」）を固定していない。follow_up_of: 202 の PR なので、① の規定のとおり next-pr にせず PR 本文の限界の節に書いた |
| N13 | 独立-2 | low | no | inherited | test-power | accepted | `test_follow_up_of_key_is_accepted_with_accepted_low` の `.replace` が効いたかを確かめていない（既定の `pr` が変わると常に成功する）。今は効いている。follow_up_of: 202 の PR なので、PR 本文の限界の節に書いた |
| N14 | 独立-2 | low | no | self-inflicted | changelog-policy | accepted | 断片に、利用者から見えない Summary の 1 文と Validation の内訳を巡の後に書き足した（CHANGELOG § Policy に反する）。内容は正しく、戻すと編集が 1 回増えるので戻さない。PR 本文の限界の節に書いた |
