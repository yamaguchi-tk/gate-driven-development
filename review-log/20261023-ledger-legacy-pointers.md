---
lane: L1
pr: 573
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f3b1a0e8 | 0 | 0 | 0 | 2026-10-23 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c1ed7381 | 0 | 0 | 0 | 2026-10-23 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L-1 | 独立-1 | low | no | self-inflicted | scope | accepted | 依頼の「テスト名の名残」を test_check_completion_mechanical.py だけで直し、assert を変えた test_verification_block_message_contract.py の test_move_prohibition_names_both_audit_sections_with_carveout（節の前提の名前）を残した（依頼より狭い）。Opus・Fable とも改名を推し、推奨で進めた commit: c1ed7381。ユーザーが改名のままとした（2026-10-23 22:59） |
| L-2 | 独立-1 | low | no | self-inflicted | scope | accepted | test_check_completion_mechanical.py のコメントから「旧#564 の独立-1・独立-2 の high の形」を消した（依頼より広い。旧#564 の accepted の advisory の取り込み）。Opus は残す、Fable は戻すを推した。CLAUDE.md の「advisory は指示があるときだけ取り込む」に合わせて戻した commit: c1ed7381。ユーザーの指示（2026-10-23 22:59）で巡の ID を消した |
| L-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の草案が規定を「移してよい例外」と言い換え、Ledger や Verification History へ移してよいと読める。PR 本文は言い換えを直した |
| L-4 | 独立-1 | low | no | self-inflicted | test-power | accepted | 新しい assert（`ac-ledger.md` を含み `## AC Trace Ledger` を含まない）は、表記を変えた旧来の節の案内（`AC Trace Ledger` の節など）でも通る |
| L-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 改名したテストのコメントが、テストで確かめていない性質（ac-ledger.md の中の行であること）を言う |
| L-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | learned-patterns の注記「Ledger の行は消さず、移さない」が、完了時に要約してよいとする正本と合わない。(4) の「同様に」が何を指すかも曖昧になった |
| L-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 規定が ac-ledger.md を名指すが、定義の場所を示さず、成果物の一覧にも ac-ledger.md が無い |
| A-1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | learned-patterns の注記に日付が無く、参照のパスが plugin の root からでない |
| A-2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の節は Changed より Fixed が合う |
| A-3 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 「ただし … の正規の記録は対象外」の言い方が、そこへ移すのは許されると読める（main の文の言い方） |
| L-8 | 独立-2 | low | no | self-inflicted | test-power | accepted | 改名したテストの assert は ac-ledger.md と「対象外」を別々に探すだけで、ac-ledger.md が例外の括弧の中にあるかを見ない |
