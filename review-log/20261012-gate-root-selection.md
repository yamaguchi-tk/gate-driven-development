---
lane: L1
pr: 442
follow_up_of: 431
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 7ebde4e7f5153246bdaadfdf65d978ab12774536 | 0 | 1 | 0 | 2026-10-12T16:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 740f2586af2991c2e9e806e846232be6d92e0553 | 0 | 1 | 0 | 2026-10-12T17:00+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 56d03b42eae55ffb13fd50e383c7f5b3c6b21b8f | 0 | 0 | 0 | 2026-10-12T17:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | PR 作成時・push 時の素通りの両方を「旧#431 で実測して受け入れた」と書いたが、実測と理由は PR 作成側だけ。作成側の実測と、push 側を測らずに受け入れたことを分けて書いた。commit: 740f2586 |
| F2 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼で選んだ案は「文書だけの PR（近道で独立レビュー 1 巡）」だが、`hooks/scripts/lib/gdd-pr-roots.sh` のコメントも 旧#431 を指していて直すので、近道は使えず通常の巡になる。依頼から外れているので、Opus（gdd-opus-advisor）に相談し、推奨どおり依頼に合わせて lib のコメントの変更を戻し、SECURITY.md・断片だけの PR にした。commit: 56d03b42 |
| F3 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 選んだ案の「completion-check を通さない運用が増えたら開き直す」が差分に無い。SECURITY.md と lib のコメントに書いた。commit: 740f2586 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 受け入れた形は block guard の脅威モデルの ADR では守る範囲の内に当たるが、例外の記録が無い。SECURITY.md § 制限事項に、ユーザーの決定で直さないことと、許可リストの規定を当てない理由を書いた。commit: 740f2586 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | push の素通りの件数が lib のコメント（44 件）と PR 本文（49 件）で違う。PR 本文に、49 件は作り直した抽出で範囲が違うことを書いた。commit: なし（PR 本文） |
| F6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「旧#431 で閉じた」は、マージの時点で 旧#431 が閉じていることを前提にしている（PR を出すときに閉じる） |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「marker を使うどの案でも止まらない」の理由（marker は作ったセッションのものとしてしか扱わない）が書かれていない |
| F8 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Summary の後半が採らなかった案の理由で、挙動を変えていないことが書かれていない |
| F9 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | SECURITY.md § 制限事項に「ADR の守る範囲の内だが許可リストで閉じる規定は当てない」と書いたが、同じ規定を定める ADR（docs/adr/2026-10-03-block-guard-threat-model.md）と root CLAUDE.md の (a) の既定には例外が無い。follow_up_of のある PR の 2 巡目の medium なので直さず、PR 本文の限界に書く |
| F10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文が、差分で消した「旧#431 で実測して閉じた」を引用している。PR 本文を直した。commit: なし（PR 本文） |
| F11 | 独立-2 | low | no | inherited | doc-claim | accepted | lib のコメントの push の素通り 44 件が、抽出し直すと 49 件になることがファイルに書かれていない。PR 本文の限界に書く |
| F12 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 依頼で選んだ手段（近道で 1 巡）が、hooks/ のコメントの変更で使えなくなった（独立-1 の F2 と同じ）。lib のコメントの変更を戻した。commit: 56d03b42 |
| F13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片が § 制限事項への追記に触れていない |
| F14 | 独立-2 | advisory | no | self-inflicted | product | accepted | ユーザーは push 側の件数を見ずに決めている。報告に push 側は測っていないことを添える |
| F15 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「旧#431 で閉じた」はマージ前に 旧#431 が閉じていることを確かめる |
| F16 | 独立-2 | advisory | no | self-inflicted | product | accepted | 開き直す条件に、基準の値（25 本中 4 本）と測り方が SECURITY.md に無い |
| F17 | 独立-2 | advisory | no | self-inflicted | style | accepted | lib のコメントの 1 行だけが長い（lib の変更を戻したので解消） |
| F18 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary に、SECURITY.md § 制限事項（:273）への追記が無い。follow_up_of のある PR の 2 巡目以降の low なので直さず、PR 本文の限界に書く |
| F19 | 独立-3 | low | no | inherited | doc-claim | fixed | PR 本文の目的 3 点目に、fix・revert の名指しの探し方と、機密の検査に使ったものが書かれていない。PR 本文に書いた。commit: なし（PR 本文） |
| F20 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | lib のコメントは 旧#431 を指すだけで、SECURITY.md の「直さずに受け入れた限界（旧#431 で閉じた）」とそろっていない。誤りではなく、そろえると hooks/ が差分に入る |
| F21 | 独立-3 | advisory | no | inherited | doc-claim | accepted | 「旧#431 で閉じた」の裏付けが材料に無い。PR 作成の後、マージの前に 旧#431 を閉じて state を確かめる |
