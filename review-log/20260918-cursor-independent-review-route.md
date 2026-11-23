---
lane: L1
pr: 130
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f364672601ee2e381faa5536162ab806879b2d21 | 0 | 4 | 0 | 2026-09-18T23:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 全差分, model: opus | 9012504a1a09546d4925f8733d8c2f9af667b2db | 0 | 3 | 0 | 2026-09-19T01:30+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#130 review, Cursor / Grok 4.6 high) | eeba8ad66534d597b544ae96215bb6a63f944108 | 0 | 2 | 0 | 2026-09-19T16:03+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | adac5182b1326cb7da31e400cdce0236ce8e2ae4 | 0 | 4 | 2 | 2026-09-19T17:10+09:00 |
| 独立-4 | light-lane-independent-reviewer, 全差分, model: opus | a892d6544edcff1ba0e532c5772c10994a584eb1 | 0 | 1 | 0 | 2026-09-19T18:10+09:00 |
| PR後-2 | yamaguchi-tk (GitHub PR 旧#130 review, Cursor / Grok 4.6 high) | 97d2aa39a9172db48852ab8edc50a7a07cf39f48 | 0 | 3 | 0 | 2026-09-19T20:38+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | non-claude-review-model-condition | fixed | inherit の経路では main のモデル・effort（Grok 4.6 medium や Composer 2.5）のまま走り、reviewer 列もモデル名だけなので、tier に届かない起動でも model 条件を満たしたと読める（旧#131。ユーザー指示で同じ PR で修正） |
| F2 | 独立-1 | medium | no | self-inflicted | gdd-reviewer-fallback-conflict | fixed | GDD の agents/*.md の reviewer にも本文を貼る経路を広げた文が、faq.md・cursor-guide.md の inline フォールバックと subagent-dispatch.md の Codex inline 実行と食い違い、PR 本文にも無い（旧#132。ユーザー指示で同じ PR で修正） |
| F3 | 独立-1 | medium | no | self-inflicted | codex-delegation-permission | deferred | codex.md の新しい経路が、同じファイルの Codex Subagent Delegation Permission（許可なしに subagent を起動しない）と突き合わされていない（旧#133） |
| F4 | 独立-1 | medium | no | inherited | model-routing-skill-table | deferred | gdd-model-routing SKILL の写像表と test_model_routing_contract の tier リストに independent_review が無く、対の片方だけが直っている（旧#134） |
| F5 | 独立-1 | low | no | self-inflicted | codex-claim-unverified | accepted | 「Codex は agent 定義を読まない」を未実測のまま断定している |
| F6 | 独立-1 | low | no | self-inflicted | fragment-claim-scope | accepted | 断片の「表と実装の食い違いを解消した」が、independent_review の行だけの変更より広く読める（cheap_readonly・dialectic_counter は resolver に無いまま） |
| F7 | 独立-1 | low | no | self-inflicted | lane-term-in-plugin | accepted | plugin の reference に root CLAUDE.md の merge-ready の語（model: opus）を持ち込み、effort の要件が抜けたように読める |
| A1 | 独立-1 | advisory | no | self-inflicted | restated-model-values | accepted | CLAUDE.md・cursor.md・codex.md の散文でモデル値を再掲しているが、テストは fixed-models.md と突き合わせない |
| G1 | 独立-2 | medium | no | self-inflicted | plugin-self-contained-review-def | deferred | 配布先の GDD では cursor.md・codex.md が貼れと言う「定義の本文」が plugin 内に無く、agents/*.md の reviewer は steering を読むので独立レビューの契約 1 を満たさない（旧#137） |
| G2 | 独立-2 | medium | no | self-inflicted | codex-delegation-permission | deferred | codex.md の独立レビューの文が委譲許可に触れず、同じ箇条の GDD reviewer の文と非対称（F3 と同じ。旧#133） |
| G3 | 独立-2 | medium | no | inherited | model-routing-skill-table | deferred | gdd-model-routing SKILL.md の写しに independent_review が無い（F4 と同じ。旧#134） |
| G4 | 独立-2 | low | no | self-inflicted | review-record-destination | accepted | モデルと effort を記録する規定が CLAUDE.md では inherit の副箇条にしかなく、GDD 側では書き先が無い（reviewer: に空白を含めると pre-push gate が malformed で止まる） |
| G5 | 独立-2 | low | no | self-inflicted | restated-model-values | accepted | 括弧内のモデル値がテストで fixed-models.md と突き合わされず、起動経路の文が 3 箇所に重複する（A1 と同型） |
| G6 | 独立-2 | low | no | self-inflicted | test-power | accepted | faq の順序検査が節全体の rindex("inline") で常に成り立ち、旧#132 の順序を固定できていない |
| G7 | 独立-2 | low | no | self-inflicted | observation-generalized | accepted | cursor-guide.md の起動失敗の記述に「2026-09-18 実測」の限定が無い |
| G8 | 独立-2 | advisory | no | self-inflicted | pr-body-claim | accepted | PR 本文の「契約上は Grok 4.6 でモデル条件を満たしていた」に effort の証拠が無い |
| P1 | PR後-1 | medium | no | self-inflicted | review-tools-restriction | fixed | 定義の本文を frontmatter を除いて貼ると tools: Read, Grep, Glob の制限が落ち、独立レビュー契約 2 の read-only が散文だけになる（ユーザー指示で同じ PR で修正） |
| P2 | PR後-1 | medium | no | self-inflicted | codex-delegation-permission | deferred | codex.md の独立レビューの文が委譲許可に触れていない（F3・G2 と同じ。旧#133） |
| H1 | 独立-3 | medium | no | self-inflicted | codex-delegation-permission | fixed | codex.md の独立レビューだけが § Codex Subagent Delegation Permission の条件を持たず、同じ箇条の GDD reviewer の条件付きとの対比で許可の対象外と読める（approval-path・blocking。F3・G2・P2 と同じクラスタ、旧#133） |
| H2 | 独立-3 | medium | no | self-inflicted | review-tools-restriction | fixed | GDD の reviewer を「本文を貼る同じ経路」で起動すると read-only のツール制限まで引き継ぐと読め、退行注入・実起動検証が取れなくなる（data-loss・blocking。P1 の修正が生んだ） |
| H3 | 独立-3 | medium | no | self-inflicted | review-tools-restriction | deferred | Claude Code 側の fallback（general-purpose に本文を貼る、CLAUDE.md 手順 6）だけ、read-only が散文だけになった旨の記録が無い（対の片方。旧#139） |
| H4 | 独立-3 | medium | no | inherited | model-routing-skill-table | deferred | gdd-model-routing SKILL の表に independent_review が無い（F4・G3 と同じ。旧#134） |
| H5 | 独立-3 | low | no | self-inflicted | test-power | accepted | 新テストが単一行の構造を固定し、CLAUDE.md は節全体を 1 要素にするため len==1 が常に真 |
| H6 | 独立-3 | low | no | self-inflicted | restated-model-values | accepted | 散文のモデル名・effort がテストで fixed-models.md と突き合わされない（A1・G5 と同型） |
| H7 | 独立-3 | low | no | self-inflicted | review-record-destination | accepted | 明示起動のときに effort を記録する規定が inherit の副箇条にしか無い（G4 と同型） |
| H8 | 独立-3 | advisory | no | self-inflicted | observation-generalized | accepted | cursor-guide.md の起動失敗の記述に実測日の限定が無い（G7 と同じ） |
| J1 | 独立-4 | medium | no | self-inflicted | review-tools-restriction | deferred | Claude Code の fallback（CLAUDE.md 手順 6 の general-purpose に本文を貼る経路）に read-only が落ちた旨の記録規定が無い（H3 と同じ。旧#139） |
| J2 | 独立-4 | low | no | inherited | model-routing-skill-table | accepted | gdd-model-routing SKILL の 2 表とテストの tier リストに independent_review が無い（F4・G3・H4 と同じ。旧#134 で扱う） |
| J3 | 独立-4 | low | no | self-inflicted | test-power | accepted | GDD reviewer の検査が箇条全体に当たり後半の削除を検出できない、faq の順序検査が rindex で常に成り立つ、コメントが subagent-dispatch.md を読むと書くが読んでいない |
| J4 | 独立-4 | low | no | self-inflicted | cursor-inline-substitution | accepted | cursor.md の独立レビューの部分に「inline で代替しない」が無く、faq・cursor-guide の inline フォールバックが独立レビューにも当たると読める |
| J5 | 独立-4 | advisory | no | self-inflicted | codex-claim-unverified | accepted | 「Codex は read-only の sandbox」を未確認と書かずに断定している |
| J6 | 独立-4 | advisory | no | self-inflicted | observation-generalized | accepted | cursor-guide.md の実測日の限定が無く、「inherit なら起動できた」で何を起動したかも不明（定義を model だけ上書きして起動できるなら tools を保てる） |
| J7 | 独立-4 | advisory | no | self-inflicted | codex-delegation-permission | accepted | 軽いレーンでの Codex の委譲許可の成り立つ条件（AGENTS.md:5 を明示委譲ソースとみなすか）と記録先が無い（安全側の unavailable に倒れる） |
| J8 | 独立-4 | advisory | no | self-inflicted | review-record-destination | accepted | GDD での「記録」の書き先が無く、reviewer 欄に空白を含めると pre-push gate が malformed で止まる（G4 と同型） |
| J9 | 独立-4 | advisory | no | self-inflicted | section-ref-mismatch | accepted | 「§ 初稿とレビュー」「§ 方針」が実際の見出し（括弧つき）と完全一致しない |
| K1 | PR後-2 | medium | no | inherited | host-route-canonical-pointer | deferred | gdd-pr-review が起動方法の正本とする independent-review.md の契約 4 に、host 別経路（直接起動しない・本文を貼る・Codex の委譲許可）への pointer が無い（旧#150） |
| K2 | PR後-2 | medium | no | self-inflicted | cursor-review-inline-fallback | deferred | Cursor の独立レビューの失敗処理と GDD reviewer の inline フォールバックが 1 文に繋がり、FAQ 経由で inline を独立レビューとして記録しうる（J4 と同型。旧#151） |
| K3 | PR後-2 | medium | no | self-inflicted | pr-body-accuracy | fixed | PR 本文の「行数は増やしていない」が実測（references は base 比 +7 / -4、合計 11958 行で上限ちょうど）と食い違う（PR 本文だけを修正） |
| K4 | PR後-2 | low | no | inherited | model-routing-skill-table | accepted | gdd-model-routing の写像表と test_model_routing_contract に independent_review が無い（J2・旧#134 と同じ） |
| K5 | PR後-2 | low | no | self-inflicted | cursor-task-readonly | accepted | Cursor の Task スキーマに readonly 引数は無い（限界の「未確認」は現行スキーマでは「無い」と言える） |
| K6 | PR後-2 | advisory | no | self-inflicted | prose-only-enforcement | accepted | inherit 時の自己申告、起動経路の散文強制なし、は PR 本文の限界どおり |
