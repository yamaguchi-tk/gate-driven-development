# reviewer の見逃しの評価

reviewer を、過去に実際に出た欠陥に当て直して、見逃しを数える。reviewer の定義（`agents/gdd-*-reviewer.md` と、4 つの定義が共通の規則として名指しする `references/reviewer-common.md`）を変える PR で、変える前と後に回して、見逃しが増えていないかを確かめるために使う。gate には組み込んでいない。定期実行もしない。

- runner: `scripts/run-reviewer-recall-eval.py`
- ケース: `evals/reviewer-recall-cases.json`（この repo には置いていない。過去のケースは切り出す前の private repo の commit を base・tip にしていて、この repo の履歴では再現できないため。使うときは、この repo の commit でケースを作り直し、`--cases` で渡す）
- テスト: `tests/test_run_reviewer_recall_eval.py`（偽の claude で runner を通す。LLM は呼ばない）

## 回し方

```bash
python3 scripts/run-reviewer-recall-eval.py --out ~/.gdd/eval-out/<日付>-<名前> --runs 2 --jobs 3 --max-cost-usd 150
```

- runner は、自分のいる checkout の plugin を `--plugin-dir` で読む。変える前の版は main の checkout で、変えた後の版はブランチの checkout で回し、2 つの `summary.md` を並べる
- 既定の reviewer は `gate-driven-development:gdd-implementation-reviewer`。security・completion reviewer を変えたときは、`--agent` でその reviewer を選ぶ。ケースはどれも実装の欠陥なので、planning reviewer に当てるケースは無い
- 終わった実行は `<out>/<case>/run-<n>.result.json` に残る。同じ `--out` で起動し直すと、終わった実行は使い直し、残りだけを回す
- `--check` はケースを git で確かめるだけで、claude を呼ばない。`--dry-run` は材料を書くだけ

## 1 本の実行でしていること

1. tip の木を、`review-log/` を除いて `<out>/<case>/wt` に展開する（その PR の指摘の記録を reviewer に読ませない）
2. base..tip の差分（`review-log/` を除く）と、review-input の 1 枚（`references/subagent-dispatch.md` § Reviewer Input and Time Budget の形を、steering の無い過去の PR に合わせて縮めたもの）を書く
3. reviewer を headless の `claude -p --agent` で、Read・Grep・Glob だけで回す。`CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` と `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` を付ける（headless の `--agent` では、agent 定義の `omitClaudeMd` が効かない）
4. reviewer の出力を、写し役（sonnet）が 1 指摘 1 行（severity・category・`file:line`）に写す。runner がその行から `references/finding-dispositions.md` の IG 節の表を書き、`hooks/scripts/lib/finding_dispositions.py` で読み戻す。本番では main が reviewer の出力をこの表に写すので、評価も同じ形で数える
5. 採点する（下の節）

費用は、実行を始める前に「使った額＋走っている本数と次の 1 本の上限（`--max-run-usd`、既定 $5）」が `--max-cost-usd`（既定 $150）を超えるなら、その実行を始めずに `budget` と記録し、exit 3 で終わる。

## ケース

- `found`: 独立レビューの巡で reviewer が見つけ、後で直した指摘。review-log の `## 指摘` で、severity が high か `実害` が yes で、`commit:` の付いた行から選んだ。tip はその巡が見た sha、base はその巡の差分の起点（全差分巡は merge-base、差分巡は前の巡の sha）
- `missed`: PR を作った後の外部レビュー（`PR後-N`）で見つかった指摘。tip は `PR後-N` の巡の sha。M01〜M04 は、その sha の前の独立レビューが high を出した後の sha で、独立レビュー自身は tip を見ていない。M05〜M07 は、直前の独立レビューが high 0 で通した sha である。M08〜M35 は、この 2 つに分けていない
- `expected` の `paths` は、直した commit（`fix_commit`）が触ったファイルのうち、指摘の場所に当たるもの
- 選び方: found の 11 件は、2026-10-19 に light-lane reviewer の advisor の効果を測ったときの 12 巡（同じ PR の 2 巡目を 1 つ外した）を写した（1 PR から 2 ケースまで）。missed の 35 件は、review-log の `PR後-N` の巡のうち、high か `実害` が yes の行で、直した commit を辿れるものを全部入れた（PR の上限は置いていない。PR ごとの件数は 旧#84 が 10、旧#88 が 6、旧#92・旧#94 が 3 ずつ、旧#93・旧#96 が 2 ずつ、ほかは 1）。巡の中で入れていない行は、直した変更が main の取り込みや review-log の追記で、木に残らないもの（旧#88 の F46・F50）と、外部レビューではなく push 前のセルフレビューで見つかったもの（旧#105 の F7）である。その PR では直さず Issue にした行も、後の PR で直したものは入れた。旧#140 の PR後-1 の U1・U2（Issue 旧#141）は 旧#156 で、旧#124 の PR後-2 の X2・X3（Issue 旧#125・旧#126）は 旧#218 で直した。旧#156 の直した commit は 旧#140 のマージより前の並行したブランチにあり、tip の子孫にならないので、M34 の `fix_commit` は 旧#156 の merge commit にした。入れていないのは、対応不要で閉じた 旧#124 の X1（Issue 旧#127）と、直した指摘の再掲の `20260919-compact-resume-writer-and-source.md` の PR後-2 の Y1 である
- `20260915-x58-x59-review-followup-nudge.md`（#88）の `## 巡` は、PR後-1〜5 の sha の欄に、その巡の指摘を直した commit を書いている（commit の件名の件数が巡の high・medium と一致する）。このため M06・M14・M28〜M30 の tip は、その commit の親にした
- 依頼は steering も出典に挙げたが、使えなかった。2026-10-24 に手元の steering 46 slug を数えると、high の指摘に触れる行があるのは 1 件、直した commit と結べる行は 0 件だった

ケースを足すときは、同じ形で書き、`--check` が通ることを確かめる。

## 採点

`expected` の 1 件ごとに、まだ当てていない指摘のうち、`file:line` の path が `paths` のどれかと path 要素の境目で一致するもの（basename だけ・plugin からの相対・絶対パスでも当てる）を探す。

- `hit`: high か実害クラスの指摘が当たった。impl-gating なら差し戻しになる
- `weak`: 当たったが、medium 以下で実害クラスでもない。impl-gating では advisory に落ちて、欠陥は通る
- `miss`: 当たる指摘が無い

1 つの指摘は 1 件にだけ当てる。同じファイルに既知の指摘が 3 件あれば、3 件とも `hit` にするには、そのファイルに high・実害クラスの指摘が 3 つ要る。

## 読み方

- `summary.md` の 2 つ目の表（kind ごとに「全 run で hit」「一部の run で hit」「hit なし」）を、変える前と後で比べる
- 同じ条件で 2 回回しても結果は揺れる（下の基準の実行の run 1 と run 2 の差）。差がこの揺れの幅に収まるなら、増えた・減ったとは言わない。決めきれないときは `--runs` を増やす

## 基準の実行（2026-10-26）

main（`3c60fd15`）の `gdd-implementation-reviewer` を、46 ケース × 2 回で回した（claude CLI 2.1.280、reviewer のモデルは `claude-opus-5-5`）。92 本とも ok、費用 $90.79。44 ケースを 87 分（`--jobs 3`）で回した後、M34・M35 の 4 本を同じ出力先に足した（6 分）。1 本の時間は写し役を含めて 0.8〜7.5 分。

| case | kind | expected | run 1（hit/weak/miss） | run 2（hit/weak/miss） |
|---|---|---|---|---|
| F01 | found | 5 | 1/1/3 | 1/0/4 |
| F02 | found | 4 | 1/0/3 | 1/0/3 |
| F03 | found | 2 | 0/0/2 | 0/2/0 |
| F04 | found | 2 | 1/0/1 | 2/0/0 |
| F05 | found | 2 | 0/0/2 | 1/0/1 |
| F06 | found | 2 | 0/0/2 | 0/1/1 |
| F07 | found | 2 | 0/0/2 | 0/0/2 |
| F08 | found | 1 | 0/0/1 | 0/0/1 |
| F09 | found | 3 | 0/0/3 | 1/0/2 |
| F10 | found | 3 | 0/2/1 | 0/1/2 |
| F11 | found | 2 | 1/0/1 | 0/1/1 |
| M01 | missed | 3 | 0/2/1 | 0/2/1 |
| M02 | missed | 1 | 0/1/0 | 1/0/0 |
| M03 | missed | 1 | 0/0/1 | 0/0/1 |
| M04 | missed | 1 | 0/1/0 | 0/1/0 |
| M05 | missed | 1 | 0/1/0 | 0/0/1 |
| M06 | missed | 5 | 0/1/4 | 0/2/3 |
| M07 | missed | 1 | 0/0/1 | 0/0/1 |
| M08 | missed | 1 | 0/0/1 | 0/0/1 |
| M09 | missed | 1 | 0/0/1 | 0/0/1 |
| M10 | missed | 1 | 0/1/0 | 0/0/1 |
| M11 | missed | 2 | 0/1/1 | 0/1/1 |
| M12 | missed | 1 | 0/1/0 | 0/1/0 |
| M13 | missed | 1 | 0/0/1 | 0/0/1 |
| M14 | missed | 2 | 0/1/1 | 0/1/1 |
| M15 | missed | 1 | 0/1/0 | 0/1/0 |
| M16 | missed | 2 | 0/0/2 | 0/0/2 |
| M17 | missed | 1 | 0/1/0 | 1/0/0 |
| M18 | missed | 2 | 0/0/2 | 0/1/1 |
| M19 | missed | 1 | 0/0/1 | 0/0/1 |
| M20 | missed | 1 | 0/0/1 | 1/0/0 |
| M21 | missed | 1 | 0/0/1 | 0/0/1 |
| M22 | missed | 2 | 0/0/2 | 1/0/1 |
| M23 | missed | 2 | 0/1/1 | 0/1/1 |
| M24 | missed | 2 | 1/0/1 | 0/1/1 |
| M25 | missed | 1 | 0/1/0 | 0/1/0 |
| M26 | missed | 1 | 0/1/0 | 0/0/1 |
| M27 | missed | 1 | 0/1/0 | 0/1/0 |
| M28 | missed | 2 | 0/1/1 | 0/2/0 |
| M29 | missed | 1 | 0/1/0 | 0/1/0 |
| M30 | missed | 1 | 0/0/1 | 0/0/1 |
| M31 | missed | 2 | 1/0/1 | 1/1/0 |
| M32 | missed | 2 | 0/1/1 | 0/1/1 |
| M33 | missed | 4 | 0/1/3 | 0/1/3 |
| M34 | missed | 2 | 0/0/2 | 0/0/2 |
| M35 | missed | 2 | 0/2/0 | 0/2/0 |

| kind | expected の件数 | 全 run で hit | 一部の run で hit | hit なし |
|---|---|---|---|---|
| found | 28 | 3 | 4 | 21 |
| missed | 56 | 1 | 5 | 50 |

- found の hit は run 1 で 4 件、run 2 で 6 件。両方の run で hit したのは 3 件（F01・F02・F04 の 1 件ずつ）だけで、run の間の揺れが大きい。1 回の比較で 2〜3 件の差は揺れの範囲と読む
- found の 28 件は、light-lane reviewer が見つけたもの（全差分巡は max、F05〜F08 の差分巡は xhigh）である。この設定の implementation reviewer は、その 2 割ほどしか差し戻しの重さで挙げなかった。場所は当てたが medium 以下にした `weak` は run 1 で 3 件、run 2 で 5 件
- missed の 56 件で hit したのは、run 1 で 2 件、run 2 で 5 件。両方の run で hit したのは M31 の F61 の 1 件だけだった。`weak` は両方の run で 22 件ずつある。外部レビューが後で見つけた欠陥は、この設定の implementation reviewer も、場所には触れても差し戻しの重さではほぼ挙げない
- 2026-10-24〜26 に、前の版のケース（30 ケースまで）で回した結果（`~/.gdd/eval-out/20261024-reviewer-recall-baseline/`）は、この表に混ぜていない。その後に 旧#88 のケース（M06・M14）の tip を直したので、ケースの定義が同じではない

## 限界

- 当たりは path だけで決める。同じファイルの別の欠陥を挙げても `hit` になり、機序が同じかは見ない。生の出力（`run-<n>.json`）と表（`run-<n>.findings.md`）が残るので、疑わしい `hit` は人が読んで確かめる
- reviewer は Read・Grep・Glob だけで回す。本番の implementation reviewer は Bash でテストを回し、退行を入れて確かめられるが、評価ではできない（`review-log/` を見せないため、git も使わせない）
- review-input に AC 表・Honest Limitations・依頼の原文が無い。過去の軽いレーンの PR には steering が無いため。依頼から外れた形の欠陥は見つけにくい
- reviewer は `--add-dir` で plugin 全体と `<out>/<case>` を読めるので、直した後のコード・変更断片・ケースの JSON・前の run の出力も読める。基準の 92 本の transcript（写し役を含めて 184）では、plugin 側で開いたのは `references/reviewer-common.md` と `references/testing-anti-patterns.md` だけで、ケースの JSON・docs・前の run の出力を開いたものは無かった。回すたびに同じとは限らない
- 同じ名前の plugin が入っている環境（root checkout へのリンクなど）で、`--plugin-dir` の定義と入っている定義のどちらで回るかを確かめていない。基準の実行はブランチと main の定義が同じなので影響しないが、定義を変えた後の比較では先に確かめる
- 写し役は LLM なので、写し違い（指摘を落とす、場所を取り違える）がありうる。本番で main が写すときと同じ種類の誤りである
- ケースの多くは、軽いレーンの独立レビュー（light-lane reviewer）が見つけたものである。正式 GDD の reviewer が同じものを見つけるべきかは、ケースごとに確かめていない
- `missed` のケースは 35 件（既知 56 件）で、run の間の揺れより大きい差を読めるかは確かめていない。旧#84 の 10 ケースは同じ検査スクリプトを順に直した巡なので、互いに似ていて、kind ごとの合計での重みが大きい
