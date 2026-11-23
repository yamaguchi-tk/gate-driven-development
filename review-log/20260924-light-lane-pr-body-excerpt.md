---
lane: L1
pr: 旧#185
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4b13435af962003d92a20455f8ab64b543564647 | 0 | 0 | 0 | 2026-09-24T20:06+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 102844e58c852da488b181641965b14ed6ea45dd | 0 | 0 | 0 | 2026-09-25T09:02+09:00 |
| 方針メモ | user | - | 0 | 0 | 0 | 2026-09-25T09:02+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#185 review) | bb89eef77053064216800477843c952199f90738 | 0 | 0 | 0 | 2026-09-28T11:28+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| H1 | 独立-1 | medium | no | self-inflicted | relaunch-rule-underspecified | next-pr | 足した「`テンプレート外の記述あり` を返したら記述を材料から除いて起動し直す」（`CLAUDE.md:54`）が、(1) 除く先を「材料」と書き、prompt の欄の外の文を名指ししない一方で差分・候補のファイルの行を消す余地を残す、(2) PR 作成後の抜粋を GitHub から抜き直すと除いた記述が戻る・除けない記述（テンプレートの欄そのもの、harness が差し込む文脈）で出口と回数の上限が無い、(3) 無効にした巡を `## 巡` にどう書くか（`独立-N` だと 3 巡の上限と安全策 4 に数えられる）が無い。近道の規定で次の PR |
| H2 | 独立-1 | low | no | self-inflicted | excerpt-vs-github-body-sections | next-pr | 抜粋の定義（GitHub の PR 本文から目的・変更内容・限界を抜く）が、手順 7（`:96`）の PR 本文の中身（概要・巡の sha と結果・`next-pr`・advisory・限界）と節の名前で合わない。手順 6・安全策 4 が限界の節に書かせる「直していない指摘」の行と見出しを抜くと、前の巡の指摘が抜粋に入る |
| H3 | 独立-1 | low | no | self-inflicted | test-power | next-pr | 契約テストが「手順 7」「契約 1」の語と、報告の規定の一部の語しか見ず、「巡の sha と結果は除く」を「含める」に、「契約 1 は…緩める」を「緩めない」に、「として報告し」を「報告しなくてよく」に変えても通る。向きまで含む句で固定する |
| H4 | 独立-1 | low | no | inherited | agents-md-material-list-stale | next-pr | `AGENTS.md:5` が依頼なしに reviewer へ送ってよい材料を「PR 本文の草案」と挙げ、PR 作成後の抜粋と呼び出し元の候補を挙げていない。経路: 差分の `CLAUDE.md:53`（抜粋の改名と定義）→ `AGENTS.md:5` |
| H5 | 独立-1 | low | no | inherited | history-leak-other-routes | next-pr | 経緯が reviewer に届く経路は抜粋のほかにもある。差分そのもの（コードのコメントに巡の ID と指摘を書く慣行。`review-log-present.sh:156`・`:213` など）と、harness が差し込む直近の commit の件名。手順 6 に「修正のコメント・commit の件名に巡の ID と指摘を書かない」を足すか、限界に書く |
| H6 | 独立-1 | advisory | no | self-inflicted | excerpt-contains-history | fixed | `advisory: テンプレート外の記述あり`（PR 本文の抜粋ファイル内）。抜粋の変更内容に「（実装前に 5 本とも RED を確認）」があり、実装の経緯に当たる。reviewer は判断に使っていないと明記した。GitHub の PR 本文では、抜粋に入らない節（TDD の証跡）に移した |
| H7 | 独立-1 | advisory | no | self-inflicted | skill-red-green-evidence | fixed | reviewer の prompt と policy を変えるので、1c の `Skill RED-GREEN Evidence` が要る。変更前（main）と変更後（tip）の定義の本文で同じ pressure scenario を走らせ、PR 本文に書いた |
| P1 | 方針メモ | advisory | no | self-inflicted | relaunch-rule-scope | fixed | 独立-1 の後、pressure scenario（変更前の定義）が、足した起動し直しの規定では無効にした巡で見つかった本物の high・blocking まで捨てられることを示した（起動し直した巡が見つけ直す保証は無い）。H1 と合わせて、未確定の規定を main に入れるかをユーザーに確認し、「この PR から外す」に決まった。規定の 1 文・その契約テスト・断片の該当記述を外し（102844e5）、起動し直しの扱いは次の PR で、拾った high の引き継ぎも含めて設計し直す |
| I1 | 独立-2 | low | no | inherited | test-power | next-pr | `test_reviewer_reports_read_lines_and_main_checks_them` は読み込みの照合の行に `wc -l` があることしか見ず、「1 つでも合わなければその巡を無効にして起動し直す」が消えても通る。経路: 差分の `CLAUDE.md:54`（行末の文の削除）→ 同じ行を読むこのテスト。PR後-1 で前提の誤りを確認した（102844e5 が行末から消したのは、足した起動し直しの規定の 1 文で、照合の「1 つでも合わなければ…起動し直す」は残っている。最終差分は 54 行目を変えていない）。テストが照合の文を固定していない弱さは差分の前からあり、H3 と一緒に次の PR で扱う |
| J1 | PR後-1 | medium | no | self-inflicted | excerpt-vs-github-body-sections | next-pr | H2 と同じ。抜粋の定義（`CLAUDE.md:53`）は目的・変更内容・限界の節を抜くが、手順 7（`:96`）が書かせる本文は概要・巡の sha と結果・`next-pr`・advisory・限界で、重なるのは限界だけ。同じ行の「目的と、差分が変える挙動・限界」と照合先の「目的・変更内容・限界」でも真ん中の呼び方が揃っていない。直すと規則の文書が変わり独立-2 が無効になるので、レビュアーの判断で次の PR |
| J2 | PR後-1 | low | no | self-inflicted | test-docstring-tense | next-pr | `PrBodyFieldTests` の docstring（`test_light_lane_review_routing_contract.py:145`）が「欄に書いてよいものの制約が無く、reviewer が報告できなかった」と現在形のまま。旧#118 の失敗理由としては正しいが、この差分の後の状態としては過去形にする。low は既定で次の PR |
