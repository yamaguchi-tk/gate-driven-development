---
lane: L1
pr: 558
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 61129ff7 | 0 | 2 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認済み（ユーザーが推奨どおり全件を本文に残すと回答）: 依頼は Advisory Findings の全件列挙を工程の記録に数えたが、差分は全件を本文に残し、写した型の行数の目安から `指摘止まり（` の行を外した。ユーザーの確認の記録が無い |
| F2 | 独立-1 | medium | no | self-inflicted | sync-copy | accepted | 上流の pr-review plugin が入った環境では gdd-pr-review が上流を呼び、WHY Check と Boundary Check の古い文面（独立した見出し）が読まれる。同梱の写しだけを直した |
| F3 | 独立-1 | low | no | self-inflicted | line-format | accepted | 「行の先頭に種類」と「`指摘止まり（` で始める」が同じ欄で食い違い、箇条書きの記号を付けると数え方で 0 行になる |
| F4 | 独立-1 | low | no | self-inflicted | silent-drop | accepted | silent drop の照合が件数の和で、Pre-PR loop で受け入れた件数はどこにも記録されず、落ちた行と重ねた行が相殺される |
| F5 | 独立-1 | low | no | self-inflicted | placement | accepted | 影響範囲・自律で判断したこと・残した問題の置き場が、テンプレートの有無と欄の有無の組み合わせで規定どうし食い違う |
| F6 | 独立-1 | low | no | self-inflicted | placement | accepted | 残した問題の欄に置ける行を 3 種類「だけ」に限ったため、Boundary / Follow-up Check が求める今回含む Stage とマージ順が当たらない |
| F7 | 独立-1 | low | no | self-inflicted | pr-body | fixed | PR 本文の草案が「見出しを足さない」と言い切り、3 行を超えるときの短い見出しの例外と、影響範囲・Boundary の置き場の変更を書いていなかった。commit: なし（PR 本文） |
| F8 | 独立-1 | low | no | self-inflicted | pr-body | fixed | PR 本文の草案が、依頼の挙げた 5 つの規定のうち 3 つしか食い違いとして名指していなかった。commit: なし（PR 本文） |
| F9 | 独立-1 | low | no | self-inflicted | sync-copy | accepted | 3g の Codex の advisory、ADR を蒸留しない理由、「PR 本文の限界」を指すほかの規定が、新しい型（指摘止まりの行、残した問題の欄）に揃っていない |
| F10 | 独立-1 | advisory | no | self-inflicted | pr-body | fixed | 測ったコマンドと節ごとの量、工程の記録の割合が PR 本文の草案に無かった。commit: なし（PR 本文） |
| F11 | 独立-1 | advisory | no | self-inflicted | pr-body | fixed | マージ後に見る指標に合否の値が無く、`指摘止まり（` の行を除いた字数も測らない。commit: なし（PR 本文） |
| F12 | 独立-1 | advisory | no | self-inflicted | line-format | accepted | WHY の文の数が、型（1〜2 文）と規定（通常 PR は 1-3 文）で食い違ったまま |
| F13 | 独立-1 | advisory | no | self-inflicted | placement | accepted | gdd-pr-review-followup の「影響範囲の節を作り直す」が、見出しの無い段落を指せない |
| F14 | 独立-1 | advisory | no | self-inflicted | pr-body | fixed | 依頼の「block / allow の判定に触るなら L1+」に対して、L1 とした理由が PR 本文に無かった。commit: なし（PR 本文） |
