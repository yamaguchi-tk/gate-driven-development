---
lane: L1
pr: 414
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 893fa542 | 0 | 3 | 0 | 2026-10-08 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | c2146cbf | 1 | 0 | 1 | 2026-10-08 |
| 独立-3 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 64f883d2 | 0 | 0 | 0 | 2026-10-08 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | wiring | fixed | brainstorming の入口の SKILL.md の Step 9 に新しい手順が無く、発火しない。commit: d6431650 |
| F2 | 独立-1 | medium | no | self-inflicted | wiring | fixed | agent の出力や依頼の原文に絶対パス・email があると steering の書き込みの検査が止める。commit: d6431650 |
| F3 | 独立-1 | medium | no | self-inflicted | wiring | fixed | express から昇格したタスクに突き合わせの手順が無く、gating の条件の対象も決まらない。commit: d6431650 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Affected Files が差分と食い違う。commit: d6431650 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | compact の ズレ確認 で既存とぶつかるが必須か任意か読み分けられない。commit: d6431650 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 完了条件の変換表の列の意味と、仮決定の書き方がずれる。commit: d6431650 |
| F7 | 独立-1 | low | no | self-inflicted | test-power | fixed | 下げた model の警告のテストが工程の検査で通り、固定表を確かめていない。commit: d6431650 |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | README の agents/ の注記に新しい agent が無い。commit: d6431650 |
| F9 | 独立-1 | low | no | self-inflicted | product | fixed | Codex・Cursor での代わりの起動が書かれていない。commit: d6431650 |
| F10 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | `<redacted>` への置き換えの指示が、placeholder を含む行全体でパス検出を止める既存の穴に入力を流す。指示を語への置き換えに変えた（検査側の穴は次の PR）。commit: 64f883d2 |
| F11 | 独立-2 | medium | no | self-inflicted | wiring | next-pr | agent を起動できないとき（委譲許可なし・定義の無いセッション・起動失敗）の出口が無い |
| F12 | 独立-2 | low | no | inherited | doc-claim | next-pr | state-machine.md・phase-progression・faq の昇格の手順に突き合わせが無い |
| F13 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の Summary に、相対パス・Codex/Cursor の経路が無い |
| F14 | 独立-2 | low | no | self-inflicted | request-drift | fixed | 依頼の 3 番目（差分の外のずれ）を次の PR で扱うことがどこにも書かれていない。PR 本文に書いた。commit: なし（PR 本文） |
| F15 | 独立-3 | low | no | inherited | product | next-pr | faq.md と steering の書き込みの検査の deny 文が、パス・email の置き換え先に今も `<redacted>` を勧めている |
| F16 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | § 9 の 1 文で「止める」が block と検査の無効化の両方の意味に使われ、外れるのはパスの検査だけなのに広く読める |
