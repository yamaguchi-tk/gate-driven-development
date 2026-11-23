---
lane: L1
pr: 435
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 9cfce8a7 | 0 | 2 | 0 | 2026-10-12 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 666354db | 0 | 2 | 0 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | 相談役は、ほかの repo では呼び出し元が場所を渡さないので references/autonomy.md § 比較の軸 を読めない。ユーザーが「読み手に直接書く」を選び、6 軸の名前と定義を相談役 3 つの欄に直接書いた commit: b8084b8d |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | human check の書き手（formal gate runner）は autonomy.md を読む規定が無く、指し先だけが残りうる。読む場合は runtime の予算が数えない。判断軸の欄に軸の名前を直接書き、増分の分だけ予算を上げた commit: b8084b8d |
| I1-3 | 独立-1 | low | no | self-inflicted | product | fixed | human check でも案ごと・軸ごとの表を求めると、一次表示の行数・表の上限に当たりうる。判断軸には決め手の軸と一言だけを書き、表は相談役の出力か requirements.md に置くと書いた commit: b8084b8d |
| I1-4 | 独立-1 | low | no | self-inflicted | doc | fixed | 「割合で選び、少ないものは近い軸に含めた」と書いたが、32% の波及を 19% の堅牢性に含めていた。実際の合わせ方どおりに書いた commit: b8084b8d |
| I1-5 | 独立-1 | low | no | self-inflicted | product | fixed | 「(1)(2) は省かない」と「当てはまらない軸は対象外」の関係が決まっていない。(1)(2) は対象外にせず、触れない案は ○ にして理由を書くと決めた commit: b8084b8d |
| I1-6 | 独立-1 | low | no | self-inflicted | doc | fixed | 変更断片に予算の引き上げと検査スクリプト 2 つが無い。Affected Files に上げ幅つきで足した commit: b8084b8d |
| I1-7 | 独立-1 | low | no | self-inflicted | doc | fixed | 予算のコメントの「残りの 4」が上げ幅 5 と合わない。上げ直した値と増分を書いた commit: b8084b8d |
| I1-8 | 独立-1 | low | no | self-inflicted | doc | fixed | autonomy.md の所有の宣言に、比較の軸の扱いと根拠が無い。足した commit: b8084b8d |
| I1-9 | 独立-1 | advisory | no | self-inflicted | doc | accepted | references の行予算に収めるため、autonomy.md の見出しの直後の空行を詰めた（ほかの references と書式が違う） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | product | accepted | gdd-pre-workflow-brainstorming の「違いと判断軸を整理する」は既定の軸を指していない（依頼の範囲外） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc | accepted | RED-GREEN の結果と 52 件の割合に、記録の場所が書かれていない。PR 本文に RED-GREEN Evidence と数え方を書く |
| I1-12 | 独立-1 | advisory | no | self-inflicted | product | accepted | 2 週間後に測る指標のうち、AskUserQuestion で委ねた率は差分が変えない面を測る。残す・戻すの目安も無い |
| I1-13 | 独立-1 | advisory | no | self-inflicted | doc | accepted | 判断の手順 2 の「security boundary に触れる変更では信頼境界の観点を足す」が、(2) を常に見ることと並び、条件つきの軸と読まれうる |
| I1-14 | 独立-1 | advisory | no | self-inflicted | doc | accepted | 案が 1 つのときも 6 軸で評価することが PR 本文に無い |
| I1-15 | 独立-1 | advisory | no | inherited | product | accepted | Codex・Cursor の判断役には agent の本文が届かないので、比較の軸の欄も届かない（前からある穴） |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | fixed | express の runtime token 予算の引き上げ（30083→30088）に、ユーザーの承認の記録が無い。ユーザーに確かめ「承認する」を依頼の原文に足した commit: なし（PR 本文） |
| I2-2 | 独立-2 | medium | no | self-inflicted | product | fixed | 案 2 が 2 週間後に測るとした 3 項目のうち、AskUserQuestion で Opus・Fable に委ねた率を確認なしに外していた。PR 本文の限界に戻した commit: なし（PR 本文） |
| I2-3 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | 出荷する形（軸を欄に直接書く相談役の本文と、テンプレートの判断軸）の RED-GREEN が無い。相談役の分は取り直して PR 本文に書いた。HITL テンプレートの pressure scenario は次の PR |
| I2-4 | 独立-2 | low | no | self-inflicted | doc | next-pr | skill-body-budget.sh のコメントの増分（standard 13・express 9）は、両方の profile に同じファイルが入るので同じ値になるはずで、少なくとも 1 つは誤り |
| I2-5 | 独立-2 | low | no | self-inflicted | doc | next-pr | autonomy.md の参照元に、もう autonomy を指さない human-check-template-compact.md の判断軸が残っている |
| I2-6 | 独立-2 | low | no | self-inflicted | doc | next-pr | テンプレートには軸の名前しか無いのに「名前と定義を直接書く」と書いている。そろえる先は autonomy.md 自身を含めて 5 か所。テンプレートは「信頼境界」で、ほかは「信頼境界・fail-closed」 |
| I2-7 | 独立-2 | low | no | self-inflicted | product | next-pr | 相談役の欄の定義から「範囲の広さを含む」「未測のまま決めていないか」が落ち、autonomy.md の「範囲の広さは要件の充足度に含めた」と合わない |
| I2-8 | 独立-2 | low | no | self-inflicted | product | next-pr | テンプレートの「この 2 つは必ず」が、必ず書くとも必ず確かめるとも読め、autonomy.md の「決め手の軸と一言だけを書く」とぶつかる |
| I2-9 | 独立-2 | low | no | self-inflicted | doc | fixed | PR 本文の「見出しの直後の空行を詰めた」は、比較の軸の節では「## 限界 の直前の空行」も詰めている。PR 本文を直した commit: なし（PR 本文） |
| I2-10 | 独立-2 | advisory | no | self-inflicted | product | accepted | 軽いレーンの AskUserQuestion の本文には、軸を載せる規定が無い（相談役の推奨を経て間接に届くだけ） |
| I2-11 | 独立-2 | advisory | no | inherited | doc | accepted | 相談役の止めるべきかの欄は、ほかの repo では読めない references/autonomy.md の判断の手順 4 を指したまま（前からある） |
