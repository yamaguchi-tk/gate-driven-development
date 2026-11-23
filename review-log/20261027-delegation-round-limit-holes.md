---
lane: L1
pr: 585
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b12fc2beaacfe664095fedefd359ed3a07996d06 | 0 | 3 | 0 | 2026-10-27T09:59+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 817ae397440b96d8e6fe197763aed5f66c2f8c04 | 0 | 2 | 0 | 2026-10-27T10:35+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d636a5a047ff8969e55eae856ce7ebc3f5bf6102 | 0 | 1 | 0 | 2026-10-27T11:02+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | design には Round 上限の一括提示の規定が無く、規定どおりの Bounce Log → human_recheck_required の止まり方では design-round-limit が書かれない（GDD を使う別の repo の runner は契約 1 を design に当てて止まっていた）。契約 3 が requirements・design の両方に当たるので、契約 1 の変更は design に届く。推奨（Opus）の Bounce Log の閾値も数える案は一度入れたが、Bounce Log だけで止まった停止が 0 件で、全レーン共通の規則（当たる件数 0 なら足さない）により戻した（commit: d636a5a0） |
| r1-2 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認済み（2026-10-27、今の案でよい）: 人に戻す条件を Approved Direction から読むと、委任先の承認でも STEP 2 が書き換え、後続 Stage にも写らない。推奨（Opus・Fable 一致）の、委任の承認では足すだけにし後続 Stage に写す案で進めた（commit: 817ae397） |
| r1-3 | 独立-1 | medium | no | inherited | round-limit | accepted | 時間超過の一括提示で「レビュー無しで承認」を選ぶことが、人に戻す条件に入っていない |
| r1-4 | 独立-1 | low | no | self-inflicted | round-limit | accepted | 時間超過の一括提示に、requirements-round-limit と design-round-limit のどちらを書くかが決まっていない |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 契約 1 の行の形に `/ at:` と、表示し直しでは書かない旨が無い |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 記録の形の `対象:` の列挙と、「適用しない」の行の形が新しい語に合わせて更新されていない |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の文が、requirements の Round 上限で委任が効く場面を実際より狭く言い切っている（commit: なし（PR 本文）） |
| r1-8 | 独立-1 | low | no | self-inflicted | changelog | accepted | 断片の「相談役が決め続けた」が、起きた事実の報告に読める（実際に委任した例は 0 件） |
| r1-9 | 独立-1 | low | no | self-inflicted | changelog | accepted | 断片の検証の欄に、関係するテストを書いていない |
| r1-10 | 独立-1 | low | no | self-inflicted | request-drift | fixed | PR 本文が「返事の無い停止」を human check の返事待ちに狭めた（human-check-waiting・external-review-waiting・blocked の 3 種で測り直し、本文を直した。commit: なし（PR 本文）） |
| r1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | design が収束しない原因を見ることが、残した問題に載っていない |
| r1-12 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | (i)(ii) の当たる件数を PR 本文に書いていない（commit: なし（PR 本文）） |
| r2-1 | 独立-2 | medium | no | self-inflicted | round-limit | fixed | Round 上限と Bounce Log の閾値に同時に当たると、1 回目の停止で上限到達の行が 2 本になりうる（Bounce Log の分を戻した。commit: d636a5a0） |
| r2-2 | 独立-2 | medium | no | self-inflicted | bookkeeping | fixed | 新しく足した Bounce Log の発火条件の当たる件数が PR 本文に無い（測って 0 件、戻した。commit: d636a5a0） |
| r2-3 | 独立-2 | low | no | self-inflicted | round-limit | fixed | runner の契約が Bounce Log の種類を絞らず、light runner が Task Breakdown Bounce Log で行を書く（commit: d636a5a0） |
| r2-4 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | Bounce Log だけで止まったときの `対象:` が決まらない（commit: d636a5a0） |
| r2-5 | 独立-2 | low | no | self-inflicted | request-drift | fixed | 依頼 (i) の「Round 上限」を Bounce Log まで広げた（commit: d636a5a0） |
| r2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | gdd-dev.md STEP 2 の括弧が「委任先の判断で承認するとき」に絞っており、委任先 なし の AI の仮決定による承認を含まない |
| r2-7 | 独立-2 | low | no | self-inflicted | changelog | accepted | 断片の Changed の human-check-template.md の行に、足すだけ・消す必要があるとき・後続 Stage への写しが無い |
| r2-8 | 独立-2 | low | no | self-inflicted | style | accepted | 「どちらにも補足を付けない」の指す先が、間に入った文で離れた |
| r2-9 | 独立-2 | low | no | self-inflicted | style | accepted | § 事前回答 4 の括弧の中の「次の括弧のとおり」が指す括弧が無い |
| r2-10 | 独立-2 | low | no | self-inflicted | round-limit | fixed | state-machine.md の Planning Loop Safety に、Bounce Log の停止で上限到達を書く参照が無い（Bounce Log の分を戻した。commit: d636a5a0） |
| r2-11 | 独立-2 | low | no | inherited | round-limit | accepted | requirements reviewer の時間超過による一括提示でも、契約 1 の字面では上限到達を書くことになり、PR 本文の限界の行と合わない |
| r3-1 | 独立-3 | medium | no | self-inflicted | request-drift | accepted | 確認済み（2026-10-27、数えないままでよい）: Requirements・Design Gating Bounce Log は human check で 0 に戻らないので、次のエピソードの Round 1 で Round 上限より先に止める経路では 2 回目の上限停止が数えられない（依頼より狭い）。Bounce Log だけの停止は実データ 0 件で、全レーン共通の規則により足していない |
| r3-2 | 独立-3 | low | no | inherited | round-limit | accepted | design-gating の SKILL と state-machine.md に、Round 上限の一括提示の手順・遷移の行が無い（契約 1・3 からだけ届く） |
| r3-3 | 独立-3 | low | no | inherited | round-limit | accepted | requirements reviewer の時間超過による一括提示を数えるかが、§ 事前回答 3 の字面から読めない（r2-11 と同じ） |
| r3-4 | 独立-3 | low | no | inherited | round-limit | accepted | Bounce Log だけで止まった human check で残った blocking を受け入れることが、人に戻す条件に入らない |
| r3-5 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | Bounce Log だけの停止が 0 件という数の数え方が、PR 本文から確かめられない |
