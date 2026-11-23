---
lane: L1
pr: 415
follow_up_of: 414
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 022725c5 | 0 | 1 | 0 | 2026-10-08 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 9215465e | 0 | 1 | 0 | 2026-10-08 |
| 独立-3 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 099dd0c0 | 0 | 0 | 0 | 2026-10-08 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 自動昇格で human check が approved のままだと、突き合わせの上位 3 件がユーザーに届かない。commit: 9215465e |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | faq が同じ穴を持つ `${CLAUDE_PLUGIN_ROOT}` を置き換え先に勧めたまま。commit: 9215465e |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | SECURITY.md の検査の一覧が email の例外に `<redacted>` を残している。commit: 9215465e |
| F4 | 独立-1 | low | no | self-inflicted | wiring | fixed | § 9 の起動できないときの手順から Codex・Cursor の経路を指していない。commit: 9215465e |
| F5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 足したテストが `<redacted>` の不在しか見ず、別の placeholder を勧める退行を検出しない。commit: 07472317 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 共通の deny 文の末尾が、秘密値の deny でもパス向けの置き換えを勧める。commit: 9215465e |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Summary に、この差分が変えていない挙動が変更として入っている。commit: 9215465e |
| A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | general-purpose の fallback で起動したときの effort を記録する規定が無い |
| F8 | 独立-2 | medium | no | self-inflicted | wiring | fixed | task-sizing.md の昇格手順だけが、突き合わせの結果で human check を pending に戻す例外を持たない（独立-1 の F1 の直し漏れ）。commit: 099dd0c0 |
| F9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | faq.md には pending に戻すことが無いのに、変更断片と PR 本文は faq も対象のように読める |
| F10 | 独立-2 | low | no | self-inflicted | style | accepted | state-machine.md の同じ段落で「ただし」が 2 回続き、後ろの但し書きの掛かり先が紛れる |
| A2 | 独立-3 | advisory | no | self-inflicted | maintainability | accepted | task-sizing.md の節の参照が見出しの全名ではなく略記（state-machine § Express 昇格） |
