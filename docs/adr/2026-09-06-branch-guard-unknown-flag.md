# ADR: root-branch guard gate 1 の未知 flag 判定を fail-open から fail-closed へ反転する

- **日付**: 2026-09-06（決定）
- **状態**: 採用
- **関連**: `plugins/gate-driven-development/CHANGELOG.md`（本タスク `20260906-branch-guard-unknown-flag` の Breaking Contract Changes エントリ。版数は origin/main の進行に伴い再導出されうるため見出し番号は固定しない） / `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`（`_segment_creates_branch`）/ `plugins/gate-driven-development/docs/design/2026-09-03-validate-worktree-git-global-flag-adr.md`（ADR-6 Superseded）

## Context

root-branch-creation guard の gate 1 `_segment_creates_branch`（`git branch` 経路）は、未知 flag（creating/non-creating どちらの curated set にも無い `-` 始まり token）を黙って非作成側に倒す fail-open を持っていた。実測（git 2.50.1）で `-v`/`-i`/`--quiet` 等 11 形以上が実際に branch を作成するにもかかわらず guard は allow していた。並行して origin/main の PR 旧#41（`[0.40.3]`）が同じ関数を 1 パス cursor walk へ書き換え済みだったため、その骨格を維持したまま残る fail-open だけを閉じる最小 diff として設計し直した。

## Decision

`_segment_creates_branch` を次の3点だけ変更する。

1. 未知の `-` 始まり token の早期 `return False`（fail-open本体）を撤去し、読み飛ばして継続する（`saw_unknown_flag` を立てる）。
2. 非作成（mode）判定を **unconditional veto**（`d`/`D`/`m`/`M`、`--delete`/`--move`、実測で作成系flag併用でもrefを作らないと確認できた10 long flag）と **conditional veto**（`a`/`r`/`u`（残余なし）、`--all`/`--remotes`。同一segmentに作成系flagも未知flagも無いときだけveto）の2区分に分け、ループ末尾でまとめて評価する（pre-scanは作らない）。
3. 短option cluster判定を新設の `_classify_branch_short_cluster` へ置き換える。bodyに英字以外を含むclusterは「flag+結合値」と断定し、全英字のclusterだけを1letterずつ分類する。値を取り得るletter（`t`/`u`）は残余があればattached valueと断定して走査を打ち切る。`v`/`i`はveto/creating/unknownいずれにも属さない**neutral letter**として新設する（`-v <名前>`/`-i <名前>`単独をAC-1の残存fail-openとしてdenyにするため。`-lv`等read-only形のover-block非回帰と両立させる唯一の区分）。

`_token_is_branch_non_creating_flag`/`_token_is_branch_creating_flag` の2関数は削除する。long flag判定は新設の `_branch_long_flag_dispatch` へ、short cluster判定は `_classify_branch_short_cluster` へそれぞれ切り出す（呼び出し側への単純インライン化ではなく、複雑度是正を兼ねた専用ヘルパへの再配置。実装は top-level関数数を純増させない）。

## Why

- unconditional/conditionalの2区分にしないと、mode拡張時に`--copy`/`-c`/`-C`併用で新規fail-open（`-ca`/`--copy --all`等）か、無宣言のdeny→allow緩和（`-fa`/`-qa`/`-ta`等7形）のどちらかが必ず発生する。veto条件に`saw_unknown_flag`を加えたのは、`--cop -a <name>`（`--cop`はgitのunambiguous abbreviationとして`--copy`に解決され実際にrefを作る）のような未知flag経由の反例が、`saw_creating`だけの条件ではconditional vetoに上書きされてallowに落ちるため。
- `t`/`u`のattached-value規則は、`-tdirect`（全英字）が「英字以外があれば値結合形」の1段目判定をすり抜け`d`をdelete letterと誤読してallowに落ちる穴を塞ぐ。実gitのparse規則（値を取る短optionは残余を値として消費する）に忠実な唯一の一貫した規則。
- pre-scan案は、PR #41が既に修正した「value-taking flagの値tokenをflagとして誤読する」欠陥を再導入し`--sort -committerdate -a <name>`に新規over-blockを生むため撤回した。ループ末尾のdeferred評価で順序非依存も同時に満たせる。

## 却下した代替案

- **mode letter a/r/uを無条件vetoにする**: `-ca`/`--copy --all`等の新規fail-openが生じる。却下。
- **`--copy`/`-c`/`-C`だけを例外にする**: `-fa`/`-qa`/`-ta`/`-fu`の既存deny契約がallowへ反転する。却下。
- **veto条件をsaw_creatingだけにする**: `--cop -a <name>`のような未知flag経由のfail-openが残り、AC-2に反する。却下。
- **値letterの表を廃し未知letterを含むclusterはletter veto非適用へ一般化**: `-tdirect`等は閉じられるが`-dZ <name>`のようにveto letter後ろの未知letterでも追加narrowingが発生する。follow-up候補として記録するに留めた。

## 受容した挙動変化

方向の大半はallow→deny（narrowing）だが、次の3条件をすべて満たす短clusterでwidening（deny→allow）が残る: (i) clusterに`d`/`D`/`m`/`M`を含まない、(ii) 残余のある（cluster末尾ではない）`u`がcluster中で最初に現れる位置より前の部分文字列が、すべて`a`/`r`/`v`/`i`または残余のない`u`のいずれかで構成され、かつ`a`/`r`を1つ以上含む、(iii) その`u`の残余に creating letter（`c`/`C`/`f`/`q`/`t`）を1つ以上含む（代表形: `-auc`/`-ruc`等。cluster長は開放集合のため全量列挙はしない。既知14文字`arucCfqtvidDmM`について長さ≤5の全数列挙で必要十分性を実測確認済み: miss 0/false positive 0。実gitはrc=128・新規ref0件でfail-openではない）。`switch`/`checkout`/gate2/`worktree add`には及ばない。個別クラスと代表形は`plugins/gate-driven-development/CHANGELOG.md`の本タスクエントリ（Breaking Contract Changes節）を正本とする。

neutral letter（`v`/`i`）の新設により、`-v <名前>`単独はdeny（bool(positionals)経由）だが`-a -v <名前>`はallow（`a`のconditional vetoがneutralで上書きされない）という非対称が生じる。同様に長形式`--all --verbose <名前>`は`--verbose`が未知long flagとしてsaw_unknown_flagを立てるためdenyになる。narrowingクラス(2)は「list-scope letterが未知letter（short/long問わずattached/分離いずれも）または分離形のcreating letterと組み合わされた形」を指す。attached形のcreating letter組み合わせ（`-ac <名前>`等）はbase側が部分文字列一致で既にdenyだったため変化なし（base側は各tokenを個別に未知判定するため、分離形`-a -c <名前>`の`-a`単独は既にfail-openだった）。list-scope letter同士・neutral letter・unconditional veto letter（`d`/`D`/`m`/`M`）・残余なしの`u`との組み合わせのみallowのまま残る（widening該当形を除く）。

残る既知gap（本ADR対象外、follow-up）:

- `git branch -- <name>`（creating flag無しのbare形）は任意のGDD名でguardを迂回できる状態が続く。
- `git branch -m <単一positional>`/`-M`/`--move`は現在のbranchをrenameでき、本PR後もallowのまま（実測で任意の先行flagとの組み合わせ94形に及ぶ）。
