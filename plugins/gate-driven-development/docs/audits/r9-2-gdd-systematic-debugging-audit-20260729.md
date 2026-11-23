# R9-2 Wave 1 蒸留監査シート: `skills/gdd-systematic-debugging/SKILL.md`

> 本シートは `design.md` § D-7 / ADR-12 の構造に従う。**対象成果物の実測値は §1 の表にのみ書く**。他節は指標名で §1 を参照し、測定値リテラルを持たない。例外は逐語領域（コマンド出力の逐語引用）と、出典を併記した外部由来値。

- 実施タスク: T-8（S-2 / 対象7）
- 実施日: 2026-07-31
- cwd（本シートの全コマンドの実行位置）: `plugins/gate-driven-development`
- `<candidate_path>` = `skills/gdd-systematic-debugging/SKILL.md`
- `<archive_path>` = `docs/references-archive/gdd-systematic-debugging-SKILL-pre-r9-2-wave1-original.md`
- `<anchors_path>` = `docs/audits/r9-2-gdd-systematic-debugging-anchors.txt`
- `<archive_commit>` = `0c1ad99`（archive と anchors のみの単独コミット。SKILL.md 本体は未変更）

## 1. 実測サマリ

再実測コマンドで使うヘルパー。以降の表はこれと上記パス定義が読み込み済みであることを前提にする。定義は T-7 の監査シート（`r9-2-gdd-writing-skills-audit-20260729.md` §1）と同一で、パスのみ本対象に置換している。**T-7 §1 の `floor_lines()` / `anchor_floor()` は複写していない**（理由は §7）。

```bash
archive_path=docs/references-archive/gdd-systematic-debugging-SKILL-pre-r9-2-wave1-original.md
candidate_path=skills/gdd-systematic-debugging/SKILL.md
anchors_path=docs/audits/r9-2-gdd-systematic-debugging-anchors.txt
archive_commit=0c1ad99

body_metrics() {  # 出力: lines=<int> chars=<int> tokens=<int>（lint-runtime-budget.py と同一定義）
  python3 -c "import sys,math,pathlib;L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b='\n'.join(L[L.index('---',1)+1:]) if L and L[0].strip()=='---' else '\n'.join(L);print(f'lines={len(b.splitlines())} chars={len(b)} tokens={max(1,math.ceil(len(b)/4))}')" "$1"
}
budget_totals() {  # $1 = plugin root。SKILL body 合計 / profile 合計
  python3 "$1"/scripts/lint-runtime-budget.py "$1" --max-skill-body-lines 999999 --max-total-skill-body-lines 999999 \
    --max-express-template-lines 999999 --max-standard-template-lines 999999 \
    --max-express-estimated-tokens 999999 --max-standard-estimated-tokens 999999 \
    | grep -E 'SKILL body line budget|runtime profile'
}
pre_budget_totals() {  # 蒸留前の合計。worktree を変更せず一時ツリーで再現する
  t=$(mktemp -d) && cp -R . "$t"/ && cp "$archive_path" "$t"/"$candidate_path" && budget_totals "$t"; rm -rf "$t"
}
max_skill_body() {  # $1 = plugin root。全 skills の最大 body 行と該当 skill
  python3 -c "import pathlib,sys;m=sorted(((len(l[l[1:].index('---')+2:]),str(p)) for p in sorted(pathlib.Path(sys.argv[1],'skills').glob('*/SKILL.md')) for l in [p.read_text(encoding='utf-8').splitlines()]),reverse=True);print('skills=%d max=%d %s'%(len(m),m[0][0],m[0][1]))" "$1"
}
pre_max_skill_body() { t=$(mktemp -d) && cp -R . "$t"/ && cp "$archive_path" "$t"/"$candidate_path" && max_skill_body "$t"; rm -rf "$t"; }
refs_lines() { find references -name '*.md' | xargs wc -l | tail -1; }
goal_bullets() { awk '/^## Goal/{f=1;next} /^## /{f=0} f' "$1" | grep -c '^- '; }
locked_chars() {  # set1 + set4 + set5 に該当する行（set2 / set3 は短い汎用トークンのため行の locked 判定に使わない）
  python3 -c "import json,pathlib,sys;S=json.load(open(sys.argv[2]))['sets'];A=[a for k in ('1','4','5') for a in S[k]];L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];lk=[l for l in b if any(a in l for a in A)];print(f'locked_lines={len(lk)} locked_chars={sum(len(l)+1 for l in lk)}')" "$1" "$2"
}
unique_locked() {  # アンカーが本文中ちょうど 1 行にしか一致しない = その行が逐語で固定される行数
  python3 -c "import json,pathlib,sys;A={a for s in json.load(open(sys.argv[2]))['sets'].values() for a in s};L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];print('unique_locked=%d'%len({h[0] for a in A for h in [[i for i,l in enumerate(b) if a in l]] if len(h)==1}))" "$1" "$2"
}
anchor_counts() { python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('total',d['total'],'counts',d['counts'])" "$1"; }
structure_lines() {  # body の コードフェンス行 / テーブル行 / 空行
  python3 -c "import pathlib,sys;L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];f=0;inf=False;tb=0;bl=0
for l in b:
    if l.strip().startswith('\`\`\`'): f+=1; inf=not inf; continue
    if inf: f+=1; continue
    if not l.strip(): bl+=1
    elif l.strip().startswith('|'): tb+=1
print(f'fence={f} table={tb} blank={bl}')" "$1"
}
anchor_cover() {  # 貪欲 set cover。全アンカーを担持できる行集合の greedy 解のサイズ（併合・書き換えなし、行の削除のみ）
  python3 -c "import json,pathlib,sys;A={a for s in json.load(open(sys.argv[2]))['sets'].values() for a in s};L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];hit={a:{i for i,l in enumerate(b) if a in l} for a in A};un={a for a,h in hit.items() if h};cov=set()
while un:
    i=max(range(len(b)),key=lambda j:sum(1 for a in un if j in hit[a]))
    g=[a for a in un if i in hit[a]]
    if not g: break
    cov.add(i); un-=set(g)
print('unique_anchors=%d uncovered=%d greedy_lines=%d'%(len(A),len(un),len(cov)))" "$1" "$2"
}
ac11() {  # AC-11 判定（tasklist.md T-8 Step 5 のコード片と同一。終点は常に HEAD）
  git -C ../.. diff --numstat "$archive_commit" HEAD -- \
    plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md \
    plugins/gate-driven-development/references/ \
  | python3 -c "import sys;rows=[l.split(chr(9)) for l in sys.stdin.read().splitlines()];sd=sum(int(d)-int(i) for i,d,p in rows if 'skills/gdd-systematic-debugging/SKILL.md' in p);rn=max(sum(int(i)-int(d) for i,d,p in rows if p.startswith('plugins/gate-driven-development/references/')),0);print(f'skill_decrease={sd} refs_net_increase={rn} AC11_OK={sd>=2*rn}')"
}
numstat() { git -C ../.. diff --numstat "$archive_commit" HEAD -- plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md; }
verbatim_check() {  # 削除行の全件照合（§5）。非空削除行の本文が蒸留版に逐語 contiguous に残っているか
  git -C ../.. diff -U0 "$archive_commit" HEAD -- plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md \
  | python3 -c "import sys,re,pathlib;new=pathlib.Path('$candidate_path').read_text(encoding='utf-8');d=[l[1:] for l in sys.stdin.read().splitlines() if l.startswith('-') and not l.startswith('---')];ne=[l for l in d if l.strip()];miss=[l for l in ne if re.sub(r'^\d+\.\s*','',re.sub(r'^[-*]\s*','',l.strip())) not in new];print(f'deleted={len(d)} non_blank={len(ne)} blank={len(d)-len(ne)} not_contiguous={len(miss)}')"
}
```

| # | 指標 | 蒸留前 | 蒸留後 | 目標 | 判定 | 再実測コマンド |
|---|---|---|---|---|---|---|
| 1 | body 行数 | 484 | 463 | ≤350（AC-8） | **未達（§7）** | `body_metrics "$archive_path"` / `body_metrics "$candidate_path"` |
| 2 | body chars | 27,749 | 26,491 | — | 参考 | 同上 |
| 3 | 推定トークン | 6,938 | 6,623 | 目標なし（`design.md` D-5 Amendment 2） | 参考 | 同上 |
| 4 | body 行数削減率 | — | −4.3% | — | 導出（旧#1） | 導出値 |
| 5 | 推定トークン削減率 | — | −4.5% | — | 導出（旧#3） | 導出値 |
| 6 | SKILL body 合計行数（全 skills） | 7,042 | 7,021 | 引き下げに寄与（AC-6 旧#2） | 達成 | `pre_budget_totals` / `budget_totals .` |
| 7 | 全 skills の最大 body 行 | 558 | 558 | ≤636（AC-6 旧#7） | 達成 | `pre_max_skill_body` / `max_skill_body .` |
| 8 | express profile 合計トークン | 32,804 | 32,804 | — | 不変（本対象は profile 非収載） | `pre_budget_totals` / `budget_totals .` |
| 9 | standard profile 合計トークン | 56,004 | 56,004 | — | 不変（本対象は profile 非収載） | 同上 |
| 10 | `references/` 合計行数 | 12,183 | 12,183 | — | 不変（移送を行わず。§6 F-1） | `refs_lines` |
| 11 | locked 行数（set1+set4+set5） | 133 | 133 | — | 参考 | `locked_chars "$archive_path" "$anchors_path"` / `locked_chars "$candidate_path" "$anchors_path"` |
| 12 | locked chars | 8,959 | 8,959 | — | 参考（§4） | 同上 |
| 13 | locked 比率（対 旧#2 蒸留前） | 32.3% | — | — | 導出（旧#12 ÷ 旧#2） | 導出値 |
| 14 | アンカーが一意に対応する body 行数 | 164 | 165 | — | 参考（§7） | `unique_locked "$archive_path" "$anchors_path"` / `unique_locked "$candidate_path" "$anchors_path"` |
| 15 | アンカー総数 | 422 | 422 | 欠落 0（AC-1） | 達成 | `anchor_counts "$anchors_path"` |
| 16 | アンカー set 別内訳 | set1=39 set2=3 set3=281 set4=57 set5=42 | 同左 | — | 参考 | 同上 |
| 17 | アンカー欠落数 / allow list 宣言数 | — | 0 / 0 | 0 / 0（AC-1） | 達成 | §3 の `verify` |
| 18 | `selftest` ケース数 | — | 22 | 全 pass | 達成 | §3 の `selftest` |
| 19 | numstat insertions / deletions | — | 2 / 23 | — | 参考 | `numstat` |
| 20 | 削除行の分類内訳（非空 / 空行） | — | 18 / 5 | 合計 = 旧#19 deletions | 整合 | `verbatim_check` |
| 21 | 非空削除行のうち本文が蒸留版に逐語 contiguous 残存した行数 | — | 1 | — | 参考 | 同上 |
| 22 | 非空削除行のうち逐語残存しない行数（§5 で 1 件ずつ残存先を特定） | — | 17 | 全件について残存先または削除根拠が特定されていること（AC-3） | 達成（§5） | 同上（`not_contiguous`） |
| 23 | 削除行の分類内訳（intra-file duplicate / 他文書重複 / 背景・理由散文 / 圧縮統合） | — | 8 / 1 / 5 / 4 | 合計 = 旧#20 非空 | 整合 | N/A（読解による分類。根拠は §5 全件照合） |
| 24 | `skill_decrease` / `refs_net_increase` | — | 21 / 0 | `skill_decrease ≥ 2 × refs_net_increase`（AC-11） | 達成 | `ac11` |
| 25 | `validate-plugin.sh` / `pytest` exit | — | 0 / 0 | 0 / 0（AC-2） | 達成 | §7 |
| 26 | `pytest` 結果（passed / subtests passed） | — | 790 / 607 | T-7 完了時点の baseline と同値（AC-2。出典: `tasklist.md` T-8 RED Evidence（AC-2）） | 達成 | `python3 -m pytest plugins/gate-driven-development/tests/ -q`（リポジトリルートで実行） |
| 27 | コードフェンス行数（フェンス記号行を含む） | 87 | 87 | — | 不変 | `structure_lines "$archive_path"` / `structure_lines "$candidate_path"` |
| 28 | テーブル行数 | 15 | 15 | — | 不変 | 同上 |
| 29 | 空行数 | 116 | 112 | — | 参考 | 同上 |
| 30 | 貪欲 set cover による全アンカー担持行数（併合・書き換えなし。行の削除のみで到達しうる構成のサイズ。未担持アンカー 0） | 177 | 177 | — | 参考（§7 の AC-8 到達可能性判定に使う。旧#1 の目標列を下回る） | `anchor_cover "$archive_path" "$anchors_path"` / `anchor_cover "$candidate_path" "$anchors_path"` |
| 31 | 一意アンカー数（`<anchors_path>` の set 間重複を除いた数。旧#15 は set 別の延べ数） | 409 | 409 | — | 参考 | 同上 |
| 32 | `## Goal` bullet 数 | 9 | 4 | — | 参考（§4 / §5） | `goal_bullets "$archive_path"` / `goal_bullets "$candidate_path"` |

## 2. 蒸留方針

`skill-body-budget.sh` に登録された reduction plan は「詳細な debug triage 材料を `references/` へ移送し、skill body は route 決定に集中させる」。本 task はこの plan の**移送を採らず、削除のみで蒸留した**。理由は §6 F-1 に記す（移送候補の節見出しはすべて set1 アンカーであり、節ごと出すと `verify` が欠落を検出する。加えて移送は AC-11 の分母を押し上げるだけで削減に寄与しない）。

適用した操作は次のとおりで、いずれも**行併合による見かけ上の行数稼ぎではない**（内訳の件数は §1「削除行の分類内訳（intra-file duplicate / 他文書重複 / 背景・理由散文 / 圧縮統合）」参照）。

1. **intra-file duplicate の削除**: 同一ファイル内の別節が正本として同じ内容を持つ行を削除する。削除した行の内容が残っている節を §5 で 1 件ずつ特定した。
2. **他文書重複の削除**: `references/` 側に正本が宣言されている内容の再掲を削除する。委譲先の実在を §3 の `grep` で確認した。
3. **背景・理由の散文の削除**: 規範でも契約でもない動機説明（`**Why:**` 段落等）を削除する。
4. **圧縮統合**: 同一の文を route ごとに繰り返していた行を、対象 route 名を明示した単一の段落へ統合する（件数は §1「削除行の分類内訳（intra-file duplicate / 他文書重複 / 背景・理由散文 / 圧縮統合）」の圧縮統合欄）。

**条件の論理構造を併合で曖昧にしていない**。本 task で新設した行は §5 の追加行 A1 のみで（件数は §1「numstat insertions / deletions」）、これは対象 route を列挙する OR 型の指定であり、AND 条件・チェックリスト・発行要件を ` / ` で併合した箇所は無い（T-6 で実欠陥になった操作型を本 task では使っていない）。

**原本に無い文言の追加**は §5 に全件を列挙した。

## 3. アンカー機械照合（AC-1）

```
$ python3 docs/audits/r9-2-anchor-tools.py selftest
SELFTEST_OK: 22 cases passed

$ python3 docs/audits/r9-2-anchor-tools.py verify \
    --anchors docs/audits/r9-2-gdd-systematic-debugging-anchors.txt \
    --candidate skills/gdd-systematic-debugging/SKILL.md
ANCHOR_VERIFY_OK: 422 anchors checked, 0 unexpected missing (0 allowed) in skills/gdd-systematic-debugging/SKILL.md
```

`--allow-missing` は使っていない（アンカー削除の宣言は承認済み禁止事項）。

削除行の委譲先として §5 が主張する `references/` 側の正本の実在確認（T-9 で「実在しない委譲先へ委譲した」と書いた失敗の再発防止）:

```
$ grep -n '^## ' references/rollback-patterns.md | grep -E 'implementation_fix_only|design_detail_only|human_recheck_required|planning_rework_required|Escape Hatch'
15:## planning_rework_required
30:## human_recheck_required
78:## design_detail_only
125:## implementation_fix_only
160:## Reviewer Loop Escape Hatch

$ grep -n 'human check が過剰' references/rollback-patterns.md
169:**Why:** `implementation_fix_only` の 3 回制限は `design_detail_only` への昇格で回避される。`design_detail_only` 後にさらに `changes_requested` が繰り返される場合、AI だけでは構造的問題を解決できない兆候ではあるが、それが直ちに人間再承認を意味するわけではない。方向性の変更が無い procedural / evidence blocker まで `human_recheck_required` に倒すと、human check が過剰に増える。
```

## 4. 節別判定（定性）

| 節 | 判定 | 何を保持したか / 何をしたか |
|---|---|---|
| 冒頭導入 | 無変更 | — |
| `Goal` | 挙動維持 | routing 契約を述べる bullet（root cause 確定後の router であること / `implementation_fix_only` を既定にすること / `High` -> `ops-blocking medium` の優先順位）を保持。他は本文の対応節が正本のため削除（§5 旧#1〜旧#5） |
| `Human Partner Signals You're Doing It Wrong` | 無変更 | 違和感の例示・分類・route selection guide をすべて保持（例示は route recalibration の入力そのものであり削らない） |
| `Methodology Delegation` | 挙動維持 | root cause 未確定時の委譲手順・`No Root Cause Routing` の status 別 route・`final route label rule`・`status selection guide`・`Goal-Driven Root Cause Handoff` をすべて保持。observation-only の例外は `final route=design_detail_only` の行が正本のため重複行を削除、handoff の動機を述べる散文を削除 |
| `SMI Block Handoff` | 挙動維持 | Routing 提案の arbiter 規則・Reviewer Lineage 反映手順・記録形式例・ADR 起票判定・standalone 時の扱い・反映チェックリスト・`Why` をすべて保持。Error Log への差異記録の重複行のみ削除（正本は優先順位 1 の差異記録行と反映チェックリスト） |
| `Fixed Model` | 挙動維持 | `Claude Code` / `Cursor` のモデル指定を保持。固定する理由の散文を削除 |
| `Test-Failure Intake` | 無変更 | — |
| `Routing Decision Tree` | 挙動維持 | Express Guard・decision tree のコードフェンス・並列修正パス・並列調査パス・`判定の具体的な目安` 表をすべて保持。並列修正パスの `Why` 散文のみ削除 |
| `Failure Routing` | 挙動維持 | 全 route の戻り先と復帰シーケンスを保持。route ごとに繰り返していた `rollback-patterns.md` 永続化の文を、対象 route 名を明示した単一の段落へ統合。復帰シーケンスを明示する理由の `Why` 散文を削除 |
| `Review-Finding Priority` | 無変更 | — |
| `Error Log（worklog.md への構造化記録）` | 挙動維持 | テーブル定義・列定義・記録条件を保持。Loop Safety の判定材料としても使う旨の散文を削除（`Attempt` 列の定義に「分母 3 は Loop Safety の blind fix 上限」が残っている） |
| `Loop Safety` | 挙動維持 | `Fix Attempts` 分数表記規則・3 回制限・escalation 条件・fail-closed・Reviewer Loop Escape Hatch の policy 系 / procedural・evidence only の両分岐をすべて保持。`changes_requested` 2 回連続時の worklog 記録は `Steps` の同一文が正本のため重複行を削除、Escape Hatch の `Why` は `references/rollback-patterns.md` § Reviewer Loop Escape Hatch が正本のため削除 |
| `なぜ 3 回か / Architecture Problem の兆候` | 無変更 | 兆候の箇条書きをすべて原文のまま保持（escalation の発火条件そのものであり、Decision Tree 側と重複していても落とさないと判断した。§6 F-3） |
| `Steps` | 無変更 | 番号つき項目をすべて原文のまま保持（`Step 4` / `Step 12` の相互参照が既に存在するため番号を動かさない。§6 F-4） |
| `Output Guidance` | 無変更 | — |
| `Worked Example` | 無変更 | — |
| `Rationalization Check（この skill 固有）` | 無変更 | — |
| `Guardrails` | 無変更 | — |

## 5. `diff` 削除行の全件照合

`verbatim_check` の分類は §1「削除行の分類内訳（非空 / 空行）」参照。逐語 contiguous に残存しなかった行（§1「非空削除行のうち逐語残存しない行数」）を全件、残存先または削除根拠とともに列挙する。

| # | 削除行（原本） | 分類 | 残存先 / 根拠 |
|---|---|---|---|
| 1 | `- 人間再チェックは例外扱いにし、実装後の差し戻しはまず AI ループ内で閉じる` | intra-file duplicate | `Goal` § の `- 実装後は implementation_fix_only を既定にし、human_recheck_required を乱発しない`（原文のまま残存）と `Guardrails` § の `- 実装後の差し戻しは、まず implementation_fix_only か design_detail_only で閉じられないかを確認する` |
| 2 | `- formal gate の changes_requested は、報告だけで止まらず High と ops-blocking medium を優先して自律 remediation する` | intra-file duplicate | `Goal` § の `- formal gate 差し戻しでは High を最優先し、次に ops-blocking medium を優先する`（原文のまま残存）と `Steps` § の 6 番、`Review-Finding Priority` § の優先順位行 |
| 3 | `- build フェーズでは Next Action を正本として再開先を固定する` | intra-file duplicate | `Test-Failure Intake` § の `- この skill は pack の有無にかかわらず Next Action / Resume From の最終更新を所有する`、`Steps` § の 14 番と保存場所定義（`Next Action`: active worktree 側 `tasklist.md`） |
| 4 | `- same route が 3 回続けて失敗した場合は Architecture Gate としてアーキテクチャを疑う` | intra-file duplicate | `Routing Decision Tree` § のコードフェンス内 `2b. Architecture Gate（same route 3 回）` ブロック（原文のまま残存。正本宣言 `※ 正本は references/bounce-log-schema.md § Architecture Gate（same route 3回）` を含む） |
| 5 | `- 必要なら worklog.md に原因を残す` | intra-file duplicate | `Error Log（worklog.md への構造化記録）` § 全体（記録条件を含む）と `Steps` § の 12 番 |
| 6 | `例外は、root cause ではなく **安全な観測強化**（ログ追加、diagnostic message、retry の可観測化）だけを行う場合。その場合でも「fix ではなく observation」として route を記録する。` | intra-file duplicate | `No Root Cause Routing` § の `- final route=design_detail_only: 承認済み scope / AC は変えず、ログ追加・diagnostic message・観測条件固定など observation-only の設計変更で進められる場合。`（同一の例外を route 名つきで規定）。route の記録義務は `Steps` § の 17 番（`Route In Progress` の更新）と `Human Partner Signals` § の worklog 1 行記録 |
| 7 | `この handoff は root cause 専用 skill を増やすためではなく、GDD の汎用 Goal-Driven Execution に debug を接続するための契約である。` | 背景・理由散文 | 残存先なし。動機説明であり規範・契約・数値閾値を含まない（§2 操作 3）。handoff の契約本体は同 § の confidence 別 bullet 群と `Loop owner の正本は references/state-machine.md § Goal-Driven Loop Ownership` の行が保持 |
| 8 | `   - Routing 差異がある場合は上記 1 の差異記録と合わせて Error Log に残す` | intra-file duplicate | 同 § 優先順位 1 の `- 一致しない → 本 skill の判定を優先し、worklog.md に差異と理由を 1 行記録する（例: …）`（原文のまま残存）と `SMI block 反映チェックリスト` § の `- [ ] Routing 差異がある場合は worklog.md に記録した` |
| 9 | `- root cause 判定と戻り先決定の誤りコストが高いため、重いモデルで固定する` | 背景・理由散文 | 残存先なし。モデル固定の動機説明であり、固定値そのもの（`Claude Code` / `Cursor` の 2 行）は原文のまま残存 |
| 10 | `**Why:** 独立した N 件の failure を sequential に直すと、1 件目の修正が 2 件目のテストを壊すことがある。並列化することで相互干渉なく修正でき、全体の修正時間も短縮できる。` | 背景・理由散文 | 残存先なし。並列化の動機説明。発火条件・独立性確認・Conflict Detection の各手順は原文のまま残存 |
| 11 | `  - references/rollback-patterns.md の implementation_fix_only パターンに従い永続化` | 圧縮統合 | 追加行 A1（対象 route 名を明示して同一内容を規定） |
| 12 | `  - references/rollback-patterns.md の design_detail_only パターンに従い永続化` | 圧縮統合 | 同上（A1） |
| 13 | `  - references/rollback-patterns.md の human_recheck_required パターンに従い永続化` | 圧縮統合 | 同上（A1） |
| 14 | `  - references/rollback-patterns.md の planning_rework_required パターンに従い永続化` | 圧縮統合 | 同上（A1） |
| 15 | `**Why:** 「戻り先」だけでは「修正後どうする？」で AI が止まるリスクがある。復帰シーケンスを明示することで、route 変更後もゴールまで自動的に進む。` | 背景・理由散文 | 残存先なし。復帰シーケンスを書く動機説明。復帰シーケンス本体（Standard / Express 両方）は原文のまま残存し、`Failure Routing` § 冒頭の `各 route には「戻り先」と「修正後にゴールまで自動的に進む復帰シーケンス」がある。…途中で止まらない。` が同じ規範を保持 |
| 16 | `このテーブルは Loop Safety の判定材料としても使う。同一 Current Task で Attempt が増えている場合に、blind fix の繰り返しを検知しやすくなる。` | 背景・理由散文 | 残存先なし。ただし `Attempt` 列の定義行に `分母 3 は Loop Safety の blind fix 上限。3/3 に到達したら escalate 必須` が原文のまま残存し、Loop Safety との接続は保持されている |
| 17 | `  - **Why:** 5 回の累積失敗が常に policy-level 変更を意味するとは限らない。人間再承認が必要なのは方向性自体が変わるときだけで、記録手順や evidence の欠落まで human_recheck_required に倒すと human check が常態化する` | 他文書重複 | `references/rollback-patterns.md` § Reviewer Loop Escape Hatch の `**Why:**` 段落（§3 の `grep` で実在を確認済み）。Escape Hatch の両分岐（policy 系 → `human_recheck_required` / procedural・evidence only → `implementation_fix_only`）は原文のまま残存 |

逐語 contiguous に残存した非空削除行（§1「非空削除行のうち本文が蒸留版に逐語 contiguous 残存した行数」）は次の 1 行:

| 削除行（原本） | 分類 | 残存先 |
|---|---|---|
| `- 同じ Current Task で changes_requested が 2 回連続した場合は、worklog.md に根本原因、前回との差分、今回の route 判断を書く` | intra-file duplicate | `Steps` § の 8 番（末尾の句点を除いて逐語一致）。`references/state-machine.md` § Remediation Loop Safety にも同一文がある |

**追加行の全件**（原本に無い文言。捏造検査の対象）:

| # | 追加行 | 種類 |
|---|---|---|
| A1 | `上記 4 route（implementation_fix_only / design_detail_only / human_recheck_required / planning_rework_required）の永続化は references/rollback-patterns.md の同名パターンに従う。` | 圧縮統合（削除 旧#11〜旧#14 の置換）。A1 が名指しする route はいずれも削除された永続化行と対応し、`references/rollback-patterns.md` の `##` 見出しとして実在する（§3 の `grep`） |

追加は本表の行のみで、他に原本に無い文言は無い（§1「numstat insertions / deletions」の insertions は本行と、統合段落の前に置いた空行）。

## 6. flag

| # | 内容 | 判断 |
|---|---|---|
| F-1 | reduction plan が指示する `references/` への移送は、本対象では **AC-1 と両立しない**。移送候補になりうる節（`SMI Block Handoff` / `Error Log` / `Worked Example` 等）はいずれも `##` / `###` 見出しを持ち、見出しは set1 アンカーとして全数が抽出されている。節ごと `references/` へ出すと `verify` がその見出し行を欠落として検出し、回避には `--allow-missing` によるアンカー削除宣言が要る（承認済み禁止事項）。見出しを残して本文だけ移す形も、AC-11 の判定式が `skill body 減少 ≧ 2 × references 純増` を課すため、移送は削除に対して常に不利になる。よって移送を行わず、削除のみで蒸留した | blocking ではない。AC-11 は移送がないため自明に成立（§1「`skill_decrease` / `refs_net_increase`」参照） |
| F-2 | **AC-8 未達**。ただし**到達不能ではない**。§1「貪欲 set cover による全アンカー担持行数」は §1「body 行数」の目標列を下回り、AC-1 と両立したまま目標行数へ到達する経路（非アンカーの説明散文の削除）が構成的に存在する。未達は**意味保存を優先した判断**の結果である（§7） | S-3（T-10）でこの対象の baseline を新実測値へ引き下げ、未達理由を script コメントに残す運用へ回す（`design.md` D-5 手順 2）。**script コメントに書く理由は「AC-1 が構造的に塞いでいる」ではなく「意味保存を優先した判断」であること** |
| F-3 | `なぜ 3 回か / Architecture Problem の兆候` § の兆候の箇条書きは、`Routing Decision Tree` § のコードフェンス内 `2. ⚠️ アーキテクチャ問題の兆候` および `references/bounce-log-schema.md` § Architecture Gate（same route 3回）と内容が重なる。削除して正本へのポインタに置換する案を検討したが**採らなかった** | これらの行は `implementation_fix_only` を選ばず escalation する発火条件そのもの（規範）であり、読み手が別文書へ跳ばずに判定できる状態を優先した。「判断に迷った節は削らない」に従い flag に留める |
| F-4 | `Steps` § の番号つき項目のうち複数（`Steps` の 4 / 8 / 9 番など）は `Review-Finding Priority` / `Loop Safety` の再掲であり、intra-file duplicate として削除余地がある。**削除しなかった** | 本文中に `Step 4` / `Step 12` を指す相互参照が既にあり（set2 アンカー）、項目を削ると番号が動いて参照先が変わる。番号を動かさずに項目だけ抜くと欠番になる。挙動が変わるリスクを取らず据え置いた |
| F-5 | 本 task の削減量は §1「body 行数削減率」「推定トークン削減率」のとおり小さい。行数とトークンがほぼ同率で減っており、T-6 の型（行数だけ動いてトークンが動かない）は回避している | **削減余地はアンカー contract に塞がれてはいない**（§7 / F-2）。残る削減余地は非アンカーの規範箇条書き・復帰シーケンス・例示であり、それらを削ると router としての判定が読み手側の再構成に依存するため今回は採らなかった。行併合で行数だけを稼ぐ選択も取らなかった |

## 7. 検証結果

### AC-1 / AC-2 / AC-3 / AC-4 / AC-5 / AC-11

- AC-1: §3 のとおり `selftest` と `verify` がともに exit 0。欠落・allow 宣言は §1「アンカー欠落数 / allow list 宣言数」参照
- AC-2: 下記の逐語出力

```
$ bash tests/validate-plugin.sh ; echo "exit=$?"
exit=0

$ python3 -m pytest plugins/gate-driven-development/tests/ -q
790 passed, 607 subtests passed in 173.75s (0:02:53)
```

- AC-3: 削除行の全件照合は §5。新規 subagent による逐語照合は実装フェーズ Step 7 で実施する
- AC-4 / AC-5: archive コミット `0c1ad99`（archive + anchors のみ）が蒸留コミットに先行する 2 コミット構造
- AC-11: 移送がないため判定式は自明に成立（§1「`skill_decrease` / `refs_net_increase`」参照）。`references/` 配下に差分は無く、`docs/` へのポインタも本文に新設していない。したがって `design.md` D-4 の `docs/` 分岐は「削除」計上側で確定する

### AC-8（body ≤350 行）の到達可能性

**未達。ただし到達不能によるものではなく、意味保存を優先した判断の結果である。**

到達可能性の判定には**アンカーを担持する行だけ**を固定扱いした。非アンカーのコードフェンス行・テーブル行・説明散文を無条件に固定扱いすると下限が過大に出て「AC-1 と構造的に両立しない」という誤った結論になる（T-6 / T-7 で連続して発生し、いずれも事後に反証された。出典: `tasklist.md` T-8 Carry-forward 1 / `handoff/t-7-impl-gate.md` §3）。本シートは T-7 §1 の `floor_lines()` / `anchor_floor()` を複写していない。両者は保守的前提の下で作った特定の構成のサイズであって下限ではなく、指標名としても誤解を招くためである。

到達可能性の唯一の根拠は §1「貪欲 set cover による全アンカー担持行数」で、これは §1「body 行数」の目標列を**下回る**。この行だけを残した候補ファイル（**行の削除のみ。併合なし・書き換えなし・`--allow-missing` なし**）を作って `verify` を実行し、構成的に確認した（確認後に候補を破棄して蒸留版を復元し、`git diff --numstat` が §1「numstat insertions / deletions」と一致することを確認済み）:

```
$ python3 docs/audits/r9-2-anchor-tools.py verify \
    --anchors docs/audits/r9-2-gdd-systematic-debugging-anchors.txt \
    --candidate skills/gdd-systematic-debugging/SKILL.md   # 中身を set cover 候補に差し替えた状態
ANCHOR_VERIFY_OK: 422 anchors checked, 0 unexpected missing (0 allowed) in skills/gdd-systematic-debugging/SKILL.md
exit=0
```

すなわち §1「body 行数」目標列への到達経路は、(a) アンカー担持行を削除して `--allow-missing` で欠落を宣言する、(b) アンカー行同士を併合して行数だけを減らす、の 2 択ではない。**(c) 非アンカーの説明散文・箇条書きを削除する**という経路が AC-1 と両立して存在する。

**それを採らなかったのは品質判断である。** AC-1 の 5 集合は意味保存の機械的な proxy であり、そこに含まれない説明文・規範散文・箇条書きの保存は守らない（`requirements.md` L91 の Honest Limitations が既に明示）。本対象で非アンカーとして残っている質量の大半は、`Failure Routing` の復帰シーケンス、`Review-Finding Priority` の `ops-blocking medium` 判定規則、`SMI Block Handoff` の反映手順とチェックリスト、`Error Log` の列定義と記録条件、`Worked Example` である。これらは router が route を選び切るための入力であり、削ると `verify` は通るが実行者が route を再構成できない。行数指標を満たすために判定不能な文書を作る選択は採らなかった。

(a) と (b) も行っていない。(a) は承認済み禁止事項であり、(b) は T-6 で AND 条件の OR 誤読という実欠陥を生んだ操作で、かつ実コンテキストを減らさない（T-6 は行数 −16.0% に対し推定トークン −0.7%。出典: `handoff/t-6-impl-gate.md` の留保）。

したがって **AC-8 は「到達不能」ではなく、「意味保存を優先した結果として未達」である**（T-6 / T-7 監査シート §7 の AC-8 と同じ結論構造）。

本 task の削減は §1「body 行数削減率」と §1「推定トークン削減率」の両方が負で、かつ両者がほぼ同率であり、**行数だけが動いてトークンが動かない** T-6 の型は回避している。ただし絶対量は小さい（§6 F-5）。

### AC-6

- 旧#7（全 skills の最大 body 行 ≤636）: §1「全 skills の最大 body 行」参照。本対象は制約元ではなく（制約元は `gdd-writing-skills`、T-7 確定値）、蒸留前後で最大値は変わらない。本 task の成否は AC-6 旧#7 の判定に影響しない（`design.md` D-5 Amendment 2）
- 旧#2（SKILL body 合計の引き下げ）: §1「SKILL body 合計行数（全 skills）」参照
- 旧#5 / 旧#6（express / standard profile のトークン）: 本対象は両 profile に非収載のため不変（§1「express profile 合計トークン」「standard profile 合計トークン」）
- 7 値の最終判定は T-10 の一括実測で行う

### D-7 決定 6 の機械確認 5 手順

| 手順 | 結果 |
|---|---|
| 1 走査 | `design.md` 記載の awk をそのまま実行し、§1 の表行とコードフェンスを除いた数値含有行を全件取得 |
| 2 判定 | 逐語領域外に残る数値は、識別子（`T-8` / `AC-8` / `set1` / `F-3` / `A1` 等）・日付・commit sha・節番号・§5 の連番・対象ファイル内の位置参照（`Steps` の項目番号、`2b`、`Step 4` 等）・出典併記のある外部由来値のみ。**新規の測定値混入なし** |
| 3 §1 突合 | `再実測コマンド` 列が `N/A` でない全行を実行し全件一致。`目標` 列は `design.md` D-5 / AC-6 の値と目視突合。`N/A` 行（旧#23）は §5 の全件照合と整合 |
| 4 逐語領域突合 | §3 の `SELFTEST_OK` / `ANCHOR_VERIFY_OK`、§7 AC-2 の `790 passed, 607 subtests passed`、§7 AC-8 の `ANCHOR_VERIFY_OK` がいずれも §1 の対応指標と一致 |
| 5 remediation 時の再実行 | 本シート作成時点で remediation コミットは無い。積む場合はコミット直前に手順 1〜4 を再実走し、値が動いていれば §1 の該当セルのみ更新して同一コミットに含める |
