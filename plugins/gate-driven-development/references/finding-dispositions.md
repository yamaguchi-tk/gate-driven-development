# Finding Dispositions

> **所有**: reviewer の指摘ごとの ID・行き先・検証役の判定の記録（steering の `review-findings.md`）と、その検査
> **参照元**: `skills/gdd-implementation-gating/SKILL.md` Step 8、`references/independent-review.md`（出力フォーマット・§ 証跡）、`references/reviewer-common.md` § Output Format、`agents/gdd-finding-verifier.md`
> **述語**: `hooks/scripts/lib/finding_dispositions.py`。入口は `scripts/check-finding-dispositions.py` と `scripts/check-gate-ledger.sh` の `findings` 行。値域を変えるときは、本書と述語を同時に変える
> **Why**: 2026-10-22 に手元の steering を調べると、指摘の採否（`[Review Calibration]`）を書いていたものはわずかで、誤検知（`was_valid=false`）を記録したものは無かった。指摘ごとの行き先を書く欄が無く、main が 1 人で指摘を捨てられた

## 書く場所と時点

`.steering/<slug>/review-findings.md` に、巡ごとに 1 節を足す（追記専用。検査が前の節の形・番号の誤りを示したときだけ、その節を直す）。impl-gating は Round の判定を決める前（Step 8）に節を書いて `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-finding-dispositions.py --steering <Steering Dir> --task <Current Task> --base <default-branch>` が ok になるまで直し（`--task` のどの task も、Current Task にあり、その task を含む最後の IG 節の sha が HEAD で round がその task の `Gate Rounds` でなければ invalid）、独立レビューは `Independent Review` 行を書く前に節を書く（push・PR の前の `check-gate-ledger.sh` の `findings` 行が、行の sha と件数に突き合わせる）。検査（自由文を読まない）はファイル全体の形（見出し・7 欄の表・通しの連番）、id の連番（`1〜N`・`m1` から）、値域（severity・category・行き先・検証）、下の付けられない行き先・検証役の条件・duplicate と re-reported の参照先と、根拠が `absent@<sha>` の行の path（CLI がどの IG 節の行もその節の sha で git で分類し、sha が解けなければ invalid。ledger は形だけを見る）を見る。ok 以外が 1 件でもあれば exit 1。

```markdown
## IG1 | task: T-1, T-2 | sha: 1a2b3c4 | round: 0 | findings: 2

| id | severity | category | file:line | 行き先 | 検証 | 根拠 |
|---|---|---|---|---|---|---|
| IG1-1 | high | fail-open | src/a.py:10 | blocking | - | - |
| IG1-2 | medium | product | src/b.py:3 | rejected:refuted | refuted | src/b.py:5 |
```

- **節の見出し**: `## IG<k> | task: <task id。Gate Batch は , 区切り> | sha: <レビューした HEAD の sha> | round: <その task の Gate Rounds。無ければ 0> | findings: <N>`、`## IR<k> | sha: <Independent Review 行に書く sha> | findings: <N>`（sha は 7 桁以上。短い方が長い方の先頭と一致すれば同じとみなす）。`k` は IG・IR それぞれの steering 通しの連番（ファイルの順に 1 から。task ごとの `Gate Rounds` は使わない）。`N` は reviewer の出力の末尾の `findings: <N>`（`references/reviewer-common.md` § Output Format。reviewer が複数なら受け取った順に番号を続け、inline review で gate が見つけた指摘はその後ろ）
- **id**: `<節の名前>-<n>`（1〜N の連番）。前の巡で出てまだ解消していない high・blocking を reviewer が再報告しなかったので main が足す行（`references/independent-review.md` (3-c)）は `<節の名前>-m<n>` にし、行き先は `re-reported:<前の id>`（IR 節の re-reported の行は、参照先より severity を下げず、実害クラスを外さない）
- **severity・category**: reviewer の値をそのまま写す（category は `references/reviewer-common.md` § finding category の 9 値）。降格は行き先の理由で表す
- **検証・根拠**: 検証は下の検証役の判定（`confirmed` / `refuted` / `unverifiable`。通していなければ `-`）。根拠は、検証が `refuted` の行（行き先によらない）で検証役が返した `path:line`（下の `file:line` と同じ形）。`advisory:unverified_file` で、`file:line` の path がその sha の時点で merge-base にも sha にも branch の途中の commit にも無く、同じ basename の file も無い（未 commit・staged の file を含み、NFC・NFD と大文字小文字の違いは同じ名前とみなす）行は `absent@<節の sha>`（`file:line` は 1 つの `path:行` か `path:行-行`〔前後のバッククォートは可〕で、path は文字〔Unicode の文字・数字・`_`〕と `./@+~-` だけ。外れた形は分類できないので invalid）。ほかは `-`

## 行き先（閉じた集合）

| 行き先 | 意味 |
|---|---|
| `blocking` | 差し戻す（impl-gating Step 9）。独立レビューでは push の前に直す（件数は下の数え方） |
| `advisory` | 差し戻さずに記録する（impl-gating Step 13 の Advisory Findings → PR 本文） |
| `advisory:out_of_scope` | 範囲外（impl-gating Step 6 の再入時の差分スコープ、`references/independent-review.md` (3-b)）。IG の high・実害クラスは、節の task がどれも前の IG 節にあるときだけ |
| `advisory:insufficient_evidence` | 根拠が足りず、直す対象と決められない |
| `advisory:calibration` | impl-gating Step 5 の calibration で 1 段下げた |
| `advisory:unverified_file` | impl-gating Step 1c で、diff の外の根拠ファイルの実在を確かめられなかった（high・実害クラスは、検証役の `refuted` か根拠の `absent@<sha>`） |
| `rejected:refuted` | 欠陥でない（検証役が `refuted` と判定した行だけ） |
| `rejected:duplicate:<id>` | 同じ巡の別の id と同じ欠陥（参照先は duplicate・`rejected:refuted`・検証 `refuted`・根拠 `absent@` のどれでもなく、参照元より軽くない行） |
| `re-reported:<id>` | 前の巡の id と同じ指摘 |

high か実害クラス（`is_blocking`）の行に付けられない行き先: 独立レビューでは `advisory` の全部（(3-d)）。impl-gating では `advisory` と `advisory:insufficient_evidence`（§ Uncertainty Rule）、実害クラスには `advisory:calibration` も。`advisory:calibration`・`advisory:unverified_file` に下げるのは、検証役が `refuted` と判定した行だけ（`advisory:unverified_file` は、根拠が `absent@<sha>` で CLI が path を `never` と分類した行も。その行は検証役を起動しない）。

## 検証役

`agents/gdd-finding-verifier.md`（read-only、Opus・high。起動時に `model` を渡さない）を、行き先を `rejected:refuted` にしたい行か、high・実害クラスを `advisory:calibration`・`advisory:unverified_file` に下げたい行があるときだけ（根拠が `absent@<sha>` の `advisory:unverified_file` の行は除く）、その巡に 1 回、対象の id をまとめて起動する。渡すのは Worktree・tip の sha・対象の指摘の reviewer の出力の原文だけで、main が捨てたい理由は渡さない。`refuted` 以外が返った行は、通常の行き先（Step 9 に当たれば `blocking`、当たらなければ `advisory`）に戻す。起動できないときは `-` のままにし、同じく通常の行き先に戻す。並行の finder は置かない（GDD を使う別の repo のレビュー bot の eval で、費用が増えたうえ結論が反転したので見送った）。

## 独立レビューの件数

`findings` 行は、`Independent Review` 行と同じ sha の `IR` 節（2 つ以上あればファイルの順で最後の節。前の節すべての high・実害クラスには、最後の節の `re-reported:<id>` が要る。re-reported を元の id まで辿って比べる）で、次の件数が行と一致するかを見る（`rejected:duplicate` の行は数えない）。`rejected:refuted` の行も数える。次の独立レビュー（(3-a) により全差分）が、`rejected:refuted` にした行と同じ指摘を出したら、`re-reported:<id>` にし、`state.md` の `Route In Progress` を `human_recheck_required` にして人に戻す。

- `high` = severity が high の行、`blocking` = category が実害クラスの行（high でも数える）、`medium` = severity が medium・low で、行き先が `advisory:out_of_scope` でない行

## 限界

- `その他`: 書き手と ID を写す者がどちらも main なので、reviewer の出力の末尾を落とし `findings: N` も書き違える形と、検証役を起動せずに `検証` を `refuted` と書く形は、検査が見つけない
- `依頼より狭い`: 検証役は、main が捨てる・下げる行だけを判定する。採った行（`blocking`・`advisory`）は判定しない（判定しても行き先は変わらない）。`advisory:out_of_scope` も判定しない（独立レビューの (3-c) が後で拾う）
- `その他`: 独立レビューでは、検証役が `refuted` とした行も件数に残す。検証役の判定だけで push の前の件数を減らさない
- `その他`: `absent@<sha>` の行は、basename まで書き違えた path の本物の欠陥も advisory に下げる（確実に残るのは PR 本文の Advisory Findings だけ。件数は未測）。同じ basename の file がある架空の path は差し戻しのまま。impl-gating の節は件数の突き合わせをせず、Current Task にある別の task を `--task` に渡す形、`Gate Rounds` の加算と今回の節の両方を落とす形、今回の Round の節の中の行を落とす形は見つけない。表は raw steering にあり、マージ後の cleanup で消える
- Step 10 の `[Review Calibration]` と Step 5 の降格は、この表とつながない。表がたまったら、Step 5 の入力をこの表に替えるか、Step 10 を外すかを問う
