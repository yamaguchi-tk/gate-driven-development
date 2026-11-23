---
lane: L1
pr: 634
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 632da211be908f6b6970981731264a03c72af4b7 | 0 | 2 | 0 | 2026-11-04 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 96fd7dfd938d6705254379182859f13927e21e84 | 0 | 4 | 1 | 2026-11-04 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 7ea20faaccea299988022414a2244cde3f4dd9e7 | 0 | 2 | 0 | 2026-11-04 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | design-gating から severity の条件を外したのに、planning reviewer の表が design phase の開いた述語を Low にして design gate を止めない作りのまま残り、一本化から外れていた。design 段階では承認済みの AC の文言への指摘を blocking にしない、を正本に書き、表と Why は正本を指す。commit: 96fd7dfd938d6705254379182859f13927e21e84 |
| I1-2 | 独立-1 | medium | no | self-inflicted | rule-copy | fixed | phase-progression.md の design-gating の行が「high・medium のうち」の条件を写したまま残っていた。正本を指すだけにした。commit: 96fd7dfd938d6705254379182859f13927e21e84 |
| I1-3 | 独立-1 | low | no | self-inflicted | rule-copy | fixed | 正本は gate が欄を動かす場合を 2 つに閉じたのに、Step 6 と design-gating 手順 9 は gate が自分で絞る書き方で、HCQ に移して解除する経路とも食い違っていた。上げない・下げるときは理由を書く、の向きで書き、写しは正本を指す。commit: 96fd7dfd938d6705254379182859f13927e21e84 |
| I1-4 | 独立-1 | low | no | self-inflicted | safety-exemption | accepted | failure scenario と再現の免除を安全境界の全体に与えたので、reviewer が `blocking: yes（安全境界）` と書けば defense-in-depth の指摘も落とせない。免除を 4 型に限る案 |
| I1-5 | 独立-1 | low | no | inherited | rule-copy | fixed | reviewer-common の Uncertainty Rule「迷ったら blocking」が段階を限っておらず、境目の指摘を yes に寄せる。requirements / design 段階の `blocking:` 欄には当てない、と足した。commit: 96fd7dfd938d6705254379182859f13927e21e84 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | `is_blocking` を「implementation 段階の数え方」と書いたが、completion・独立レビューでも使われている。除く側で書く案。各文書は `is_blocking` を直接指すので判定は変わらない |
| I1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | reviewer に渡す 1 枚の (3) に § 精度の第一原則 の写しが加わることが、PR 本文と断片に書かれていない |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の「再現できない `blocking: yes` を落とす」に、安全境界を落とさない例外が抜けている |
| I2-1 | 独立-2 | medium | yes | self-inflicted | approval-path | fixed | 設計: 変える（両 gate 共通の正本に、requirements-gating だけの HCQ で解除する手順を入れた）。design-gating でも人の承認なしに policy-level の blocking を外せる文になっていた。下げてよい場合を 2 つに閉じ、HCQ に移す解除は requirements-gating だけにした。design-gating では blocking のまま human_recheck_required で人に戻す。commit: 7ea20faaccea299988022414a2244cde3f4dd9e7 |
| I2-2 | 独立-2 | medium | no | self-inflicted | design-exemption | accepted | design 段階の例外「承認済みの AC の文言への指摘（開いた述語など）」が「など」で開いており、承認済み AC の `計測:` が改善を測れない High なども design gate を止めなくなる。例外を Open Predicate in AC だけに限る案 |
| I2-3 | 独立-2 | medium | no | self-inflicted | safety-exemption | accepted | Uncertainty Rule の除外が安全境界にも効き、安全境界に当たるかで迷う指摘が `blocking: no` で通る側に倒れる。除外を安全境界以外の 3 つに限る案 |
| I2-4 | 独立-2 | medium | no | self-inflicted | rule-copy | fixed | requirements-gating SKILL の「HCQ に集約して blocking を解除する」が条件なしで、正本の「安全境界は下げない」と食い違っていた。I2-1 の対になる箇所として、正本の条件を指すようにした。commit: 7ea20faaccea299988022414a2244cde3f4dd9e7 |
| I2-5 | 独立-2 | low | no | self-inflicted | rule-copy | fixed | 「例外は 2 つだけ」を消したので、ほかの理由で `blocking: yes` を下げてよいかが決まらなかった。I2-1 と同じ文で「下げてよいのは次の 2 つのときだけ」に戻した。commit: 7ea20faaccea299988022414a2244cde3f4dd9e7 |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化が、gate が欄を下げる経路の説明で差分と食い違っていた。commit: なし（PR 本文） |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の design 段階の例外の説明が、「など」で広く効く規則より狭く書かれている |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文が「表の blocking はこの PR の規則と食い違わない」と根拠なしに断定していた。断定を外した。commit: なし（PR 本文） |
| I2-9 | 独立-2 | low | no | self-inflicted | rule-copy | accepted | planning reviewer の表の design phase の `blocking: no` が、requirements-gating から design の観点で起動した reviewer にも当たり、正本の「human check の後」と食い違う |
| I2-10 | 独立-2 | low | no | inherited | rule-copy | accepted | レビューループの契約 3 の「blocking に昇格でき」が、昇格するのが reviewer か gate かを書いていない |
| I2-11 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | reviews.md の形式に、gate が下げた指摘とその理由を書く欄が無い |
| I2-12 | 独立-2 | advisory | no | self-inflicted | style | accepted | design-gating 手順 9 の「ほかは advisory」の「ほか」が指すものが読めなくなった |
| I3-1 | 独立-3 | medium | no | self-inflicted | rule-copy | accepted | 列挙: 下げてよい場合を 2 つに閉じたので、レビューループの契約 3（差分スコープ）・design 段階の承認済み AC・security の Honest Limitations で advisory にする規則を gate が当てられないと読める。当たる規則の場所を書いて advisory にしてよい、を足す案 |
| I3-2 | 独立-3 | medium | no | self-inflicted | safety-exemption | accepted | requirements-gating で、人にしか決められない安全境界の policy-level の指摘を HCQ に移して解除できず、再入を 1 Round 回ってから同じ HCQ に着く。HCQ に移すことを「下げる」から外す案 |
| I3-3 | 独立-3 | advisory | no | self-inflicted | budget | accepted | SKILL 手順 5 の字数が増え、token 予算を超えないかを reviewer は実測していない（validate-plugin.sh で確かめる） |
| I3-4 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 断片が、design-gating で代わりに human_recheck_required で人に戻すことを書いていない |
| I3-5 | 独立-3 | advisory | no | inherited | doc-claim | accepted | design-gating 手順 13 の自走中に policy-level の指摘が出たとき、正本どおり人に戻すのかが読めない |
