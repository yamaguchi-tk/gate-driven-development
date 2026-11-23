---
lane: L1
pr: 550
follow_up_of: 547
amends: 20261020-fix-procedure.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ea22e501 | 0 | 3 | 0 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2f58e32f | 0 | 0 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | wiring | accepted | TDD route でテストを書く subagent の Template が self-review-lanes.md を読ませないので、systematic-debugging の「テストを書く段を含む」が届かない |
| F2 | 独立-1 | medium | no | self-inflicted | scope | accepted | § 常時 High の適用範囲は除外で定義されているので、§ 直し方 2 の和集合がほぼすべてのコードに fail-open の 3 ケースを求め、テスト判定基準とぶつかる |
| F3 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | rollback-patterns.md が § 直し方 を「1〜3」と番号で切り、文言・帳簿の除外と逆になり、4・5 が落ちる |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | systematic-debugging の「それ以外は § 直し方 の再現テスト」が、文言・帳簿の指摘にも再現テストの段を見せる |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 参照元の行の gdd-systematic-debugging の注記が「implementation_fix_only の復帰」のままで、どの route でもに広げた使い方より狭い |
| F6 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 依頼の「別の箇条に分ける」を、総行数の上限のため手順 1 の行の末尾に替えた。Opus と Fable の推奨（手順の後の独立した段落にし、前の 2 段落をつないで行数を保つ）で直した。commit: 2f58e32f |
| F7 | 独立-1 | low | no | self-inflicted | wiring | accepted | worker が § 直し方 5 を判定する材料（前の巡で直した部品）が prompt の契約に無い |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 旧#547 の断片の Changed が、規定を移す前の場所（停止条件の上書き、implementation_fix_only の復帰）を指したまま |
| F9 | 独立-1 | advisory | no | self-inflicted | request-drift | accepted | gdd-pr-review の括弧（Pre-PR loop と手順 2）が skill 全体より狭く、PR Body の 7 チェックが入らない |
| F10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | worker に返させる記録が「部品が要るかの答え」で、§ 直し方 5 の「共有の実装に寄せられるか」が落ちた |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 3 つの worker 定義の報告の項目に 4・5 の記録が無い（prompt の契約が優先するので今は衝突しない） |
| F12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの 2 本の断片が同じ版に入るので、新しい断片の「戻した」に先行する文が無く、同じ変更が 2 回出る |
| F13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 旧#547 の断片の Summary が、RED-GREEN Evidence の対象を skill・reference・prompt に広げて書いている |
| F14 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 書き換えた 旧#547 の断片が、この PR の断片の Affected Files に無い |
| F15 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | tip に amends: の宣言が無い。review-log の front matter に書いた。commit: なし（review-log） |
| F16 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋ファイル内の「review-log の amends: で宣言」。次の巡の前に抜粋から除く |
| F17 | 独立-1 | advisory | no | self-inflicted | request-drift | accepted | worker への指し先が「差し戻しの修正」に限られ、Self-Correct Pass で自分で見つけた問題を直すときに指さない |
| F18 | 独立-1 | advisory | no | inherited | bookkeeping | accepted | gdd-pr-review・receiving の IMPLEMENT で deny の分岐を足すときの、規律 C の記録そのものの置き先が無い |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | F8 の再掲。旧#547 の断片の Changed が gdd-pr-review を「手順 1 の停止条件の上書きと 3g」と書き、移した後の位置と合わない |
| F20 | 独立-2 | low | no | inherited | doc-claim | re-reported | F5 の再掲。self-review-lanes.md の参照元の gdd-systematic-debugging の注記が implementation_fix_only の復帰に限り、SKILL.md の「どの route でも」より狭い |
| F21 | 独立-2 | advisory | no | inherited | request-drift | accepted | この PR が扱う行の advisory 2 件（4・5 の件数の未測、self-review-lane-tokens.sh のコメントの「3 skill」）を確かめた記録なしに限界に置いた |
| F22 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | この PR の断片の Changed に 3g の指す文の変更が無い（挙動は変わらない） |
