---
lane: L1
pr: 281
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c15ace4318725a13738a3b88ff91bcba51fbffdd | 0 | 1 | 1 | 2026-10-02T16:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | e86ca2b7e8db4b741c60add126795dedf9411e04 | 0 | 0 | 0 | 2026-10-02T17:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | yes | self-inflicted | security-boundary | fixed | § 8a ① の読み取り専用の操作が secret の読み出し（get-secret-value・--with-decryption）を除いておらず、生の secret が会話と session の記録に入る。secret・認証情報・token を返す操作を除き、鍵の配置は値を返さない操作かマスク済みの sample で得る commit: 260389b6 |
| A2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | quick (express) は requirements-gating・design-gating を通らないのに、断片が新しい確認を一般化している。断片の Summary と PR 本文の限界に express の扱いを書いた commit: 260389b6 |
| A3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「未実測」が既存の「未測」+ 理由と別の語で、planning reviewer の除外に当たらない。「未測」と理由にそろえた commit: 260389b6 |
| A4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | Step 6 をまとめて multi-tenant boundary が消え、official integration が入った。Step 3 に境界を足し、断片の文を直した commit: 260389b6 |
| A5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | skill の 8a の記録先が雛形に無い External Dependencies だけになった。外部依存の確認結果と Open Questions にした（references の 8a も同じ）commit: 260389b6 |
| A6 | 独立-1 | low | no | self-inflicted | product | fixed | 発火条件が skill と references で違い（design・Webhook が無い）、5d にデータが無いときの出口が無い。条件をそろえ、5d に未測の出口を足した commit: 260389b6 |
| A7 | 独立-1 | low | no | self-inflicted | product | fixed | 5d の記録を読む側が無く、参照先の § 8a が曖昧。記録なしは Medium finding とし、references のパスを書いた commit: 260389b6 |
| A8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 取る件数の下限が無く、少ない sample で 5d が 0 件のまま通る。取る範囲と値の形ごとの件数を findings.md に書く commit: 260389b6 |
| A9 | 独立-1 | low | no | inherited | doc-claim | fixed | TDD skill の fixture の規定が § 8a の fixture につながっていない。あればそれを使うと書いた commit: 260389b6 |
| A10 | 独立-1 | low | no | self-inflicted | product | fixed | fixture の置き場が無く、session ごとの scratchpad に置くと後の phase から読めない。worktree の中に作ると書いた commit: 260389b6 |
| A11 | 独立-1 | advisory | no | self-inflicted | product | accepted | 生データをディレクトリで置いて消すと rm -r になり確認が要る。PR 本文に列挙 |
| A12 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 新しい check が手順の中の語まで pin している。PR 本文に列挙 |
| A13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence と 1b が抜粋に無い。PR 本文に書く commit: なし（PR 本文） |
| A14 | 独立-1 | advisory | no | self-inflicted | style | accepted | 8a の直後の箇条書きで、描画時に 8b〜8h が同じ段落に入る。PR 本文に列挙 |
| B1 | 独立-2 | medium | no | self-inflicted | product | next-pr | § 8a ③ が fixture の置き場に `.steering/<task>/` を許し、TDD はそれを使うよう指示するが、raw steering は PR に入らないので CI と main でテストが fixture を見つけられない。テストで使う fixture はテストの fixture 置き場に置く |
| B2 | 独立-2 | medium | no | self-inflicted | product | next-pr | 5d の「どちらも無ければ未測」が、規則を直すことも理由を書くこともできないときの抜け道に読める。「どちらのデータも無ければ」にする（断片も） |
| B3 | 独立-2 | low | no | self-inflicted | product | next-pr | AWS 由来の fixture を `.steering/` に置くと steering write guard が 12 桁の合成値を deny し、値の形が崩れる。B1 と同じくテストの fixture 置き場に置く |
| B4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 5d の「同じ扱いの実データ」が何と同じかを失い、実データを worktree の中に置くと読める。「§ 8a と同じ扱い」に戻す |
| B5 | 独立-2 | low | no | self-inflicted | product | next-pr | 「記録なしは Medium finding」を出す項目が planning reviewer の Design phase に無い |
| B6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | describe-secret は secret の値のキー構造を返さない。キー構造が要るときはマスク済みの sample を求めると書き分ける |
| B7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | express の雛形の欄名は `外部依存` で、8a の記録先 `外部依存の確認結果` が無い |
| B8 | 独立-2 | low | no | self-inflicted | product | next-pr | TDD で § 8a の fixture を使う指示が、外部へ出力するスキルの節にしかない。Contract Surface Coverage の external API response variants にも置く |
| B9 | 独立-2 | low | no | self-inflicted | product | next-pr | Spec Self-Review Checklist の外部形式の範囲に Webhook と「など」が無く、8a より狭い |
| B10 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | runtime 予算が tip で通るかが未確認。実測値（standard 45404/45405、express 29934/30083）を PR 本文に書く commit: なし（PR 本文） |
| B11 | 独立-2 | advisory | no | self-inflicted | style | accepted | 8a の語が SKILL（レート制限・ページング）と references（レートリミット・ページネーション仕様）で違う。PR 本文に列挙 |
| B12 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に SKILL の 8a の記録先の変更が明示されていない。PR 本文に書く commit: なし（PR 本文） |
| B13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary が quick (standard) に触れていない。PR 本文に列挙 |
