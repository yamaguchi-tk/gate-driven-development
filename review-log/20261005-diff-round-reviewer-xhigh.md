---
lane: L1
pr: 370
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ace8b0bef86cea0598631ffc069d17221fa7b221 | 0 | 1 | 0 | 2026-10-05T01:10+09:00 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承 | caef72211c795dda00bc4f8bda669a38ce34e29c | 0 | 1 | 0 | 2026-10-05T01:30+09:00 |
| 独立-3 | general-purpose, 差分, model: opus, effort 継承 | 6cf1e28fe841f6e12da6a968acbeae15eb3350ed | 0 | 0 | 0 | 2026-10-05T01:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 差分巡を xhigh にする根拠が fixed-models.md の「推論型は max でしか拾えなかった」と食い違い、10-03 の実験の差（max 19/20・xhigh 11/20）と観点つきの xhigh のデータが無いことも書いていない。実験記録の該当行と要約の違い、逆向きのデータを書いた commit: caef7221 |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 全差分（無効化後）の reviewer 列の例が xhigh 版の名前で読める。例を 2 つに分けた commit: caef7221 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストのパスが repo root から見て実在しない commit: caef7221 |
| F4 | 独立-1 | low | no | self-inflicted | test-power | fixed | frontmatter の比較が model と tools の値しか見ない。name・description・effort を除いた辞書を比べた commit: caef7221 |
| F5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 全差分巡の定義を改名・削除するとテストが skip になる。目印を root CLAUDE.md の見出しにし、定義が無ければ落とす commit: caef7221 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Affected Files・Summary・Validation がテストの変更と合わない commit: caef7221 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 契約 4 の置き換えの括弧書きが回数だけで、差分巡が tier の effort から外れることを覆っていない commit: caef7221 |
| F8 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | テストモジュールの docstring が足したテストの目的を含まない commit: caef7221 |
| F9 | 独立-1 | advisory | no | self-inflicted | product | fixed | 速くなるかの測り方と max に戻す条件が無い commit: caef7221 |
| F10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | agent 定義の effort: xhigh が効くことを transcript で確かめた記録が無い。このセッションでは定義が読み込まれないので、PR 本文の限界に書く |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 時間の根拠が CLAUDE.md と PR 本文で強さが違う commit: caef7221 |
| F12 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 全差分巡を max で回すことは散文の規定だけで、記録の検査は区別しない。守られているかを reviewer 列で数えてから決める |
| F13 | 独立-2 | medium | no | self-inflicted | design-consistency | fixed | max に戻す条件の「後の全差分巡で出た high」は、最後の巡を全差分に戻さない規定の下では観測できず、比べる件数と閾値も無い。差分巡 10 本の時間の中央値と PR 後の巡の high の割合で書いた commit: 6cf1e28f |
| F14 | 独立-2 | low | no | self-inflicted | test-coverage | fixed | canonical repo の目印が 2 つあり、既存のテストクラスは agent 定義の改名・削除で skip になる。目印を 1 つにまとめ、定義が無ければ落とす commit: 6cf1e28f |
| F15 | 独立-2 | low | no | self-inflicted | test-coverage | fixed | 新しい目印が root CLAUDE.md の見出しの文言に依存し、文言を直すと skip になる。review-log の README を目印にした commit: 6cf1e28f |
| F16 | 独立-2 | advisory | no | self-inflicted | docs | fixed | 変更断片の Summary が利用者から見えないテストの追加を書き、根拠が外部ファイルの行番号を指す commit: 6cf1e28f |
| F17 | 独立-3 | low | no | self-inflicted | clarity | fixed | max に戻す条件 (2) の割合の分母と、比べる max の差分巡の本数が決まっていない。直近 10 本と、巡 1 本あたりの割合にした commit: acbeed44 |
| F18 | 独立-3 | advisory | no | self-inflicted | consistency | accepted | 変更断片の Summary からテストの記述を外したので、Affected Files の唯一のファイルの役目が Summary から読めない。CHANGELOG の方針（利用者から見える変更だけ）に従い、役目は Validation に書いてある |
