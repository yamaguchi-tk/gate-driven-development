---
lane: L1
pr: 539
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d83d712a | 0 | 2 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 依頼 C の「1 本で確かめる」を実行ファイルの読み取りに代え、足さない条件を「効かない見込み」にし、実行での確認を後回しにした。headless は週の上限、定義はセッション開始時にしか読まれず、1 本を起動できなかった。10-16 16:55 にユーザーが、A と B を先にマージし C を後続 PR（follow_up_of: 539。マージ後 20 本で内側 advisor が 0 件なら作らない）にすると決めた |
| F2 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が「CLAUDE.md の場所を渡す」を勧めるが、human-check-template.md 項目 7 と autonomy.md は材料を steering のパスなどに限り、CLAUDE.md を渡さない。基準 0 と Fable の役が、repo の規則とユーザーの方針の無いまま推奨を出す |
| F3 | 独立-1 | low | no | self-inflicted | measurement | accepted | 測り直しの指標に、omitClaudeMd が効いた起動を見分けるもの（最初の turn の input token）が無い。古い定義の起動や general-purpose の代わりの経路が混ざりうる |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary が「費用を下げた」「読み込まなくなる」と効果を済んだものとして書く。plugin agent での omitClaudeMd を実行で確かめていない |
| F5 | 独立-1 | low | no | self-inflicted | test-power | accepted | test_frontmatter_omits_claude_md は agent 定義の文字列を見るだけで、repo のコードが読む値ではなく、root CLAUDE.md § テスト の書かないテストに当たる |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 呼ばない理由の「呼び出し側が Opus と Fable を並べて読む」が、1 本だけで起動する場面（委任先が 1 本、Fable の 1 回、名指し、max）で成り立たない |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 本文の「1 回 約 $1.3、1 本の約半分」が max の description の「1 回 約 $4.5」と合わず、費用の正本（fixed-models.md）の外に数字を置く |
| F8 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files に tests/test_advisor_agents.py が無く、Validation のパスの書き方が混ざる |
| F9 | 独立-1 | advisory | no | inherited | cost | next-pr | 相談役以外の agent（軽いレーンの reviewer、GDD の reviewer・worker）も tools によらず advisor を使える。相談役の測り直しの後、同じ集計で回数と額を測って止めるかを決める |
