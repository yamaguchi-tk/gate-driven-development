# R9-2 Wave 1 蒸留監査シート: `skills/root-cause-investigation/SKILL.md`

> 本シートは `design.md` § D-7 / ADR-12 の構造に従う。**対象成果物の実測値は §1 の表にのみ書く**。他節は指標名で §1 を参照し、測定値リテラルを持たない。例外は逐語領域（コマンド出力の逐語引用）と、出典を併記した外部由来値。

- 実施タスク: T-6（S-2 / 対象5）
- 実施日: 2026-07-31
- cwd（本シートの全コマンドの実行位置）: `plugins/gate-driven-development`
- `<candidate_path>` = `skills/root-cause-investigation/SKILL.md`
- `<archive_path>` = `docs/references-archive/root-cause-investigation-SKILL-pre-r9-2-wave1-original.md`
- `<anchors_path>` = `docs/audits/r9-2-root-cause-investigation-anchors.txt`
- `<archive_commit>` = `8c6c969`（archive と anchors を含む単独コミット。SKILL.md 本体は未変更）

## 1. 実測サマリ

再実測コマンドで使うヘルパー。以降の表はこれと上記パス定義が読み込み済みであることを前提にする。

```bash
archive_path=docs/references-archive/root-cause-investigation-SKILL-pre-r9-2-wave1-original.md
candidate_path=skills/root-cause-investigation/SKILL.md
anchors_path=docs/audits/r9-2-root-cause-investigation-anchors.txt
archive_commit=8c6c969

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
refs_lines() { find references -name '*.md' | xargs wc -l | tail -1; }
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
floor_lines() {  # 削除不能行の下限 = (一意固定行 ∪ フェンス行 ∪ テーブル行) + ブロック境界に必要な空行
  python3 -c "import json,pathlib,sys;A={a for s in json.load(open(sys.argv[2]))['sets'].values() for a in s};L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];keep={h[0] for a in A for h in [[i for i,l in enumerate(b) if a in l]] if len(h)==1};inf=[False]
for i,l in enumerate(b):
    if l.strip().startswith('\`\`\`'): keep.add(i); inf[0]=not inf[0]; continue
    if inf[0]: keep.add(i); continue
    if l.strip().startswith('|'): keep.add(i)
ks=sorted(keep);blocks=1+sum(1 for x,y in zip(ks,ks[1:]) if y!=x+1);print(f'kept={len(ks)} blocks={blocks} required_blank={blocks-1} floor={len(ks)+blocks-1}')" "$1" "$2"
}
ac11() {  # AC-11 判定（tasklist.md T-6 Step 5 のコード片と同一。終点は常に HEAD）
  git -C ../.. diff --numstat "$archive_commit" HEAD -- \
    plugins/gate-driven-development/skills/root-cause-investigation/SKILL.md \
    plugins/gate-driven-development/references/ \
  | python3 -c "import sys;sd=0;rn=0;rows=[l.split(chr(9)) for l in sys.stdin.read().splitlines()];[None for i,d,p in rows];sd=sum(int(d)-int(i) for i,d,p in rows if 'skills/root-cause-investigation/SKILL.md' in p);rn=max(sum(int(i)-int(d) for i,d,p in rows if p.startswith('plugins/gate-driven-development/references/')),0);print(f'skill_decrease={sd} refs_net_increase={rn} AC11_OK={sd>=2*rn}')"
}
numstat() { git -C ../.. diff --numstat "$archive_commit" HEAD -- plugins/gate-driven-development/skills/root-cause-investigation/SKILL.md; }
verbatim_check() {  # 削除行の全件照合（§5）。非空削除行の本文が蒸留版に逐語 contiguous に残っているか
  git -C ../.. diff -U0 "$archive_commit" HEAD -- plugins/gate-driven-development/skills/root-cause-investigation/SKILL.md \
  | python3 -c "import sys,re,pathlib;new=pathlib.Path('$candidate_path').read_text(encoding='utf-8');d=[l[1:] for l in sys.stdin.read().splitlines() if l.startswith('-') and not l.startswith('---')];ne=[l for l in d if l.strip()];miss=[l for l in ne if re.sub(r'^\d+\.\s*','',re.sub(r'^[-*]\s*','',l.strip())) not in new];print(f'deleted={len(d)} non_blank={len(ne)} blank={len(d)-len(ne)} not_contiguous={len(miss)}')"
}
```

| # | 指標 | 蒸留前 | 蒸留後 | 目標 | 判定 | 再実測コマンド |
|---|---|---|---|---|---|---|
| 1 | body 行数 | 644 | 541 | ≤350（AC-8） | **未達（§7）** | `body_metrics "$archive_path"` / `body_metrics "$candidate_path"` |
| 2 | body chars | 25,176 | 24,992 | — | 参考 | 同上 |
| 3 | 推定トークン | 6,294 | 6,248 | 目標なし（`design.md` D-5 Amendment 2） | 参考 | 同上 |
| 4 | body 行数削減率 | — | −16.0% | — | 導出（旧#1） | 導出値 |
| 5 | 推定トークン削減率 | — | −0.7% | — | 導出（旧#3） | 導出値 |
| 6 | SKILL body 合計行数（全 skills） | 7,177 | 7,074 | 引き下げに寄与（AC-6 旧#2） | 達成 | `pre_budget_totals` / `budget_totals .` |
| 7 | 全 skills の最大 body 行 | 644 | 590 | ≤636（AC-6 旧#7） | 達成 | `max_skill_body <一時ツリー>` / `max_skill_body .` |
| 8 | express profile 合計トークン | 32,804 | 32,804 | — | 不変（本対象は profile 非収載） | `pre_budget_totals` / `budget_totals .` |
| 9 | standard profile 合計トークン | 56,004 | 56,004 | — | 不変（本対象は profile 非収載） | 同上 |
| 10 | `references/` 合計行数 | 12,183 | 12,183 | — | 不変（移送なし） | `refs_lines` |
| 11 | locked 行数（set1+set4+set5） | 177 | 177 | — | 参考 | `locked_chars "$archive_path" "$anchors_path"` / `locked_chars "$candidate_path" "$anchors_path"` |
| 12 | locked chars | 8,600 | 9,302 | — | 参考（§4） | 同上 |
| 13 | locked 比率（対 旧#2 蒸留前） | 34.2% | — | — | 導出（旧#12 ÷ 旧#2） | 導出値 |
| 14 | アンカーが一意に対応する body 行数 | 209 | 208 | — | 参考（§7） | `unique_locked "$archive_path" "$anchors_path"` / `unique_locked "$candidate_path" "$anchors_path"` |
| 15 | アンカー総数 | 399 | 399 | 欠落 0（AC-1） | 達成 | `anchor_counts "$anchors_path"` |
| 16 | アンカー set 別内訳 | set1=53 set2=6 set3=202 set4=84 set5=54 | 同左 | — | 参考 | 同上 |
| 17 | アンカー欠落数 / allow list 宣言数 | — | 0 / 0 | 0 / 0（AC-1） | 達成 | §3 の `verify` |
| 18 | `selftest` ケース数 | — | 22 | 全 pass | 達成 | §3 の `selftest` |
| 19 | `verify` fail 回数（途中経過） | — | 0 | — | 参考（§3） | N/A（実行過程の記録。再現不能） |
| 20 | numstat insertions / deletions | — | 41 / 144 | — | 参考 | `numstat` |
| 21 | 削除行の分類内訳（非空 / 空行） | — | 123 / 21 | 合計 = 旧#20 deletions | 整合 | `verbatim_check` |
| 22 | 非空削除行のうち本文が蒸留版に逐語 contiguous 残存した行数 | — | 123 | = 旧#21 非空（AC-3 の前提） | 達成 | 同上 |
| 23 | `skill_decrease` / `refs_net_increase` | — | 103 / 0 | `skill_decrease ≥ 2 × refs_net_increase`（AC-11） | 達成 | `ac11` |
| 24 | `validate-plugin.sh` / `pytest` exit | — | 0 / 0 | 0 / 0（AC-2） | 達成 | §7 |
| 25 | `pytest` 結果（passed / subtests passed） | — | 790 / 607 | T-9 完了時点の baseline と同値（AC-2。出典: `tasklist.md` T-6 RED Evidence（AC-2）） | 達成 | `python3 -m pytest plugins/gate-driven-development/tests/ -q`（リポジトリルートで実行） |
| 26 | AC-11 RED 判定（移送のみ・削除 0 のダミー差分） | — | `skill_decrease=0` / `refs_net_increase=2` / `AC11_OK=False` | 判定式が不成立になること | 達成 | N/A（一時ダミー差分。復元済みで再現不能。§7 に逐語出力） |
| 27 | コードフェンス行数（フェンス記号行を含む） | 123 | 123 | — | 不変 | `structure_lines "$archive_path"` / `structure_lines "$candidate_path"` |
| 28 | テーブル行数 | 33 | 33 | — | 不変 | 同上 |
| 29 | 空行数 | 177 | 156 | — | 参考 | 同上 |
| 30 | 削除不能行の下限（保守的前提: アンカー行を互いに併合しない / ブロック境界ごとに空行 1 行。一意固定行 ∪ フェンス行 ∪ テーブル行 + その空行） | 406 | 397 | — | 参考（§7） | `floor_lines "$archive_path" "$anchors_path"` / `floor_lines "$candidate_path" "$anchors_path"` |

## 2. 蒸留方針

`skill-body-budget.sh` に登録された reduction plan は「重複した superpowers fork の説明を `references/` へ移送し、entry skill を routing と evidence steps に集中させる」。本 task はこの plan のうち **移送を採らず、同一ファイル内の構造圧縮のみで削減した**。理由は §6 F-1 / §7 に記す。

適用した操作は行併合だけである。

- **並列列挙の行併合**: 親項目に従属する短い並列 bullet を、親行または同一 bullet 内へ併合する。連結子は ` / `（並列列挙）、` — `（親項目と従属節の接続）、`。`（段落の連結）、`(1)(2)(3)`（番号付き手順のインライン化）を使い分ける。空行のみで区切られていた隣接段落・ラベル行を 1 段落へ併合する。

**併合の際に本文を書き換えていない**。削除された非空行はすべて、その本文が蒸留版に **contiguous な部分文字列として逐語で存在する**（§1「非空削除行のうち本文が蒸留版に逐語 contiguous 残存した行数」参照）。したがって T-9 で問題になった「長い bullet の中間にある従属節が書き換えで消える」型の欠落は、本 task では構造的に発生しえない。

アンカー contract で固定された行は、その行頭（字下げ + `- ` / `N. ` 接頭辞を含む）を保ったまま単独行として残すか、併合後の行の**先頭**に置いた。`present()` が部分一致であるため、行頭に置いた場合もアンカー文字列は逐語で保存される。

削らなかったもの: 契約文字列・アンカー、成果物フォーマット定義（`## 出力形式（任意）` / `## No Root Cause Decision` / `Root Cause Confidence` / `.gdd/rci-findings.md` の各テンプレート）、停止規律・ゲート条件・数値閾値・禁止規範（Iron Law、Early Exit Criteria、Architecture Check 発火条件、`**禁則**` / `**チェック**` 各項、Routing 提案の各経路）。

## 3. アンカー機械照合（AC-1）

`docs/audits/r9-2-anchor-tools.py` を使用。本番照合の前に `selftest` を実走した。

```
$ python3 docs/audits/r9-2-anchor-tools.py selftest
SELFTEST_OK: 22 cases passed
```

```
$ python3 docs/audits/r9-2-anchor-tools.py extract \
    --base-tree /tmp/r9-2-base-tree/plugins/gate-driven-development \
    --target skills/root-cause-investigation/SKILL.md \
    --archive docs/references-archive/root-cause-investigation-SKILL-pre-r9-2-wave1-original.md \
    --out docs/audits/r9-2-root-cause-investigation-anchors.txt
ANCHOR_EXTRACT_OK: 399 anchors (set1=53 set2=6 set3=202 set4=84 set5=54) -> docs/audits/r9-2-root-cause-investigation-anchors.txt
```

```
$ python3 docs/audits/r9-2-anchor-tools.py verify \
    --candidate skills/root-cause-investigation/SKILL.md \
    --anchors docs/audits/r9-2-root-cause-investigation-anchors.txt
ANCHOR_VERIFY_OK: 399 anchors checked, 0 unexpected missing (0 allowed) in skills/root-cause-investigation/SKILL.md
```

`--allow-missing` は使用していない。すなわち原本のアンカーは 1 件も削除を宣言せずに全数が蒸留版へ残っている（§1「アンカー欠落数 / allow list 宣言数」参照）。

**この `verify` の pass を単独の保存証跡にしない**。`present()` は部分一致であり、書き換えられた長い行の断片が別位置に一致して pass しうる（T-9 実績）。本 task では §5 の全件照合と §4 の節別読解を独立の根拠として併置する。

## 4. 節別判定（定性）

| 節 | 判定 | 保持したもの / 施した操作 |
|---|---|---|
| 冒頭 / `## Fixed Model` / `## GDD Debug Entry` / `### Goal-Driven Root Cause Loop` | 挙動維持 | 無変更 |
| `## なぜこの skill が要るか` / `## Iron Law` / `## 4 Phases` | 挙動維持 | 無変更 |
| `## 適用範囲` | 挙動維持 | 「使うべき場面」「特に **使わなければいけない**」の各列挙を行併合。項目そのものは全数逐語保持 |
| `### Phase 1: Root Cause Investigation（事実を集める）` | 挙動維持 | Early Exit Criteria の全条件・「省略可」条項・step 1〜5 の規範は全て逐語保持。step 1〜5 の従属 bullet と、step 4 の「各 component 境界で」列挙 / 順序規律 / probe 参照、step 5 の遡り手順を行併合。`**Early Exit 時の Phase 2 / Phase 3 の扱い**:` ラベルを直前段落末へ併合 |
| `### Phase 2: Pattern Analysis（似ているものと比べる）` | 挙動維持 | 各項目の見出しと従属 bullet を 1 行へ併合。`common-failure-patterns.md` への参照段落は無変更 |
| `### Phase 3: Hypothesis & Testing（仮説を 1 個ずつ検証する）` | 挙動維持 | 各項目を行併合。`「分からない」も valid な結論` / `parallel-failure-investigation.md` 参照 / 「並列にしない」条件は単独行のまま保持 |
| `### Phase 4: Implementation Handoff（root cause が確定したら）` | 挙動維持 | 各項目を行併合。Architecture Check への遷移条件は単独行のまま保持 |
| `#### 出力構造のルール` | 挙動維持 | 各項目の本体は無変更。`root cause 確定時` の最優先アクション定義を item 1 本文へ併合、「一次原因欄の書き方」の各項目を 1 行へ併合。`root cause 未確定時` / `Architecture Check 発火時` / question の各条項は逐語保持 |
| `#### State Machine Integration（GDD workflow 内で呼ばれた場合）` | 挙動維持 | ADR 起票トリガー・Reviewer Lineage 判定・Routing 提案の全条件を逐語保持。トリガー列挙を親項目へ併合。Routing 提案の第 1 経路を item 3 本文へ併合し、`human-check-waiting` / `gdd-design-gating` / `gdd-brainstorming` の各経路は単独行のまま保持 |
| `## Investigation Hygiene（認知バイアス対策・6 原則）` および `### 原則 1`〜`### 原則 6` | 挙動維持 | 全 `**禁則**` / `**チェック**` / `**チェックテンプレ**` / `**テンプレ**` と適用域テーブルを無変更で保持。導入段落の併合と `### 原則 4` の「適用例」列挙の行併合のみ |
| `### 失敗実例（Why this matters）` | 挙動維持 | 原則 1〜6 の各違反記述と結論を逐語保持。違反 bullet を行併合 |
| `## Architecture Check（3 回失敗、または過去パターン一致のとき）` | 挙動維持 | 両方の発火条件・責務外宣言を無変更。「兆候」列挙と「人間と相談する」観点列挙を行併合 |
| `## Red Flags（出てきたら一旦止まる）` | 挙動維持 | red flag を全数逐語保持し、行併合 |
| `## 合理化との対決` / `## Quick Reference` | 挙動維持 | 無変更（表形式のため併合対象外） |
| `## 「root cause が無い」と結論するとき` | 挙動維持 | 記録手順を番号付き 1 段落へ併合。「結論されるケースの大半は調査不足」を述べる規範文は無変更 |
| `### When Process Reveals No Root Cause` | 挙動維持 | `No Root Cause Decision` の発行条件・status selection guide・出力テンプレート・許可範囲を逐語保持。導入段落のみ併合。発行条件は逐語照合の指摘を受けて原本どおり独立 bullet に復元（§8 参照） |
| `## Supporting References` / `## 他 skill との関係` | 挙動維持 | 無変更 |
| `## 出力形式（任意）` | 挙動維持 | 無変更（成果物フォーマット定義のため対象外） |
| `## 中間報告・調査サイクル・状態永続化` および配下の各節 | 挙動維持 | 中間報告フォーマット・サイクル手順・`<gdd-stop reason="done">` の出力順序・`.gdd/rci-findings.md` テンプレートを無変更。`### 調査完了後の遷移案内` の内容列挙のみ行併合 |

`locked chars` が蒸留前より増えている（§1「locked chars」参照）。これはアンカー行の**先頭**へ自由行を併合した結果であり、アンカー行が減った・書き換えられたことを意味しない（`locked 行数` は不変、§1「locked 行数（set1+set4+set5）」参照）。

## 5. `diff` 削除行の全件照合

削除行を機械で全件照合した。判定基準は「削除行の本文（行頭の bullet / 番号接頭辞のみ除去）が、蒸留版に **contiguous な部分文字列**として存在するか」。断片単位ではなく行本文まるごとの一致を要求するため、T-9 が検出した「行の中間の従属節だけが落ちる」型は原理的に検出できる。

```
$ verbatim_check
deleted=144 non_blank=123 blank=21 not_contiguous=0
```

内訳（§1「削除行の分類内訳（非空 / 空行）」参照）:

- **非空行**: すべて行併合によるもの。本文は蒸留版へ逐語 contiguous に残存（`not_contiguous` が空集合であること）。情報損失なし。
- **空行**: 併合により不要になった段落・箇条書き区切り。内容を持たない。

本シートは**委譲の主張を含まない**。本 task は他ファイルへの移送を行っていないため、「§ X へ委譲した」型の記述はシート内に存在せず、委譲先実在確認（T-9 指摘 1 の型）の対象も存在しない。移送を行っていないことは §1「`references/` 合計行数」と「`skill_decrease` / `refs_net_increase`」の両方で裏取りされている。

## 6. flag

| # | 内容 | 扱い |
|---|---|---|
| F-1 | reduction plan（`skill-body-budget.sh` 記載）が指示する `references/` への移送を実施していない | **未実施のまま上げる**。理由: (a) アンカー contract 上、移送対象になりうる節（`## なぜこの skill が要るか` / `## 適用範囲` / `## Red Flags` / `## 合理化との対決` / `## Investigation Hygiene（認知バイアス対策・6 原則）`）はいずれも set1 の見出しアンカーを含み（`## 合理化との対決` を除く 4 節は set5 の規範文アンカーも含む）、移送には `--allow-missing` による削除宣言が必要になる。AC-1 の証跡強度（宣言なし）を落としてまで得られる削減量は AC-8 の目標行数に届かない。**この 5 節を全移送しても残り 392 行で目標未達**（出典: `handoff/t-6-collation.md` §5 の独立実測）であり、AC-6 旧#7 の判定分岐も変えない (b) design.md D-5 の「辻褄合わせをしない」および T-6 依頼文の「移送よりも削除を優先する / 数字を作るための移送で辻褄を合わせない」に従い、判定式を通すためだけの移送は行わない。plan 自体は skill-body-budget.sh に残るため、将来の再蒸留で再評価できる |
| F-2 | AC-8（body ≤350 行）未達 | **未達のまま上げる**。`tasklist.md` T-6「3 分岐の判定手順」由来の分岐 2（AC-8 未達 / AC-6 旧#7 成立）に該当。据え置き・余裕率縮小・scope 外追加蒸留のいずれも行っていない。**未達は到達不能によるものではなく、条件スコープの曖昧化を避ける品質判断の結果**である（§7）|
| F-3 | 本 task の削減は行数に対してのみ有効で、内容量（chars / 推定トークン）はほぼ変わっていない | **記録のみ**。§1「body 行数削減率」と「推定トークン削減率」の乖離がそれを示す。行併合は改行と bullet 接頭辞しか除去しないため当然の帰結であり、AC-8 / AC-6 旧#7 / AC-6 旧#2 はいずれも body **行数**を判定軸にしているので AC への影響はない。ただし「context 削減」という R9-2 全体の目的に対しては、本対象の寄与が行数指標に限定されることを T-10 / completion-check が誤読しないよう明記する |
| F-4 | 行併合により、一部の節で 1 行が長くなり可読性が下がった（`## Red Flags` / `### 失敗実例（Why this matters）` / Phase 2 の各項目） | **記録のみ**。プラグイン内の既存記法（` / ` 区切りの並列列挙）に揃えており、逐語内容は全数保持。挙動を規定する条件・禁止・出力先は、§8 指摘 1 で復元した `No Root Cause Decision` 発行条件を除き、いずれも併合前後で同一（当該箇所は復元済みのため現状も原本と同一） |

## 7. 検証結果

- **AC-1（アンカー機械抽出・照合）**: 達成。§3 のとおり `selftest` は全 pass、`verify` はアンカー欠落なし・allow 宣言なし（§1「アンカー欠落数 / allow list 宣言数」「`selftest` ケース数」参照）。
- **AC-2（regression baseline）**: 達成。`bash plugins/gate-driven-development/tests/validate-plugin.sh` と `python3 -m pytest plugins/gate-driven-development/tests/ -q` をリポジトリルートで実行。

  ```
  Plugin layout validation passed.
  ```

  ```
  790 passed, 607 subtests passed
  ```

- **AC-3（逐語照合）**: 本シートの §4 / §5 が蒸留 subagent 側の根拠。独立 subagent による逐語照合は `handoff/t-6-collation.md` に記録する（external-evidence-required）。
- **AC-4 / AC-5（コミット順序・単独性）**: 達成。archive + anchors を `<archive_commit>` で先行コミットし、蒸留 + 本シートを後続コミットに分離。`git log --stat` で確認可能。
- **AC-6 旧#2（SKILL body 合計の引き下げ）**: 寄与あり（§1「SKILL body 合計行数（全 skills）」参照）。
- **AC-6 旧#7（`--max-skill-body-lines` の制約元移動）**: 達成。本対象は最大 body 行の制約元ではなくなり、制約元は `skills/gdd-writing-skills/SKILL.md`（T-7 の対象）へ移った（§1「全 skills の最大 body 行」参照）。充足条件（`design.md` D-5 Amendment 2 由来の ≤636）を満たす。最終判定は T-10 の一括実測による。
- **AC-8（body ≤350 行）**: **未達**（§1「body 行数」参照）。`tasklist.md` T-6「3 分岐の判定手順」由来の分岐 2（351〜636）に該当するため、`skill_body_baseline_lines` を蒸留後の実測値へ引き下げて続行する（T-10 Step 3 の既定動作）。例外リストからの削除は行わない。

  **未達理由**: 本対象には削除不能行の下限があり、それが AC-8 の目標行数（`design.md` D-5 / AC-8 由来の ≤350）を上回る。下限は次の 3 集合の和集合と、それらを markdown として成立させるのに必要な空行から成る。

  1. **アンカーが一意に対応する行**（§1「アンカーが一意に対応する body 行数」参照）。行頭接頭辞を含めた逐語一致が要求されるため互いに併合できず、それぞれ独立した行として残さざるをえない
  2. **コードフェンス行**（§1「コードフェンス行数」参照）。成果物フォーマット定義そのもので、内部の改行を減らせない
  3. **テーブル行**（§1「テーブル行数」参照）。行単位が構文であり併合できない
  4. 上記を連続ブロックに畳んだうえで、ブロック境界ごとに必要な空行

  この下限は §1「削除不能行の下限」に実測値として記録した。**ただしこれは保守的前提の下の値であり、到達不能の証明ではない**。前提は 2 つある。(i) アンカー行を互いに併合しない (ii) ブロック境界ごとに空行 1 行を置く。行頭接頭辞を持たないアンカーは行頭に置く必要がなく隣接行へ併合しても `present()` は成立するため (i) は緩められ、CommonMark では箇条書きが段落を中断できるため (ii) も緩められる。両方を厳密化すると下限は目標行数を下回る（出典: `handoff/t-6-collation.md` §10.3 の独立実測）。すなわち **さらなる併合を進めれば、削除も `--allow-missing` も使わずに形式上は目標行数へ到達しうる**。

  それを採らなかったのは品質判断である。追加の併合は、逐語照合が実害を検出した型（§8 指摘 1: AND 条件を ` / ` で併合したことで OR に読めるようになり、停止規律の発行要件が緩む方向へ変化した）と同じ操作になる。逐語は保存されても**条件スコープと係り受けが曖昧化する**リスクが行数と引き換えになる。停止規律・ゲート条件・成果物フォーマット定義の意味保存を優先し、行数を稼ぐための併合は行わなかった。

  したがって **AC-8 は「到達不能」ではなく、「意味保存を優先した結果として未達」である**。成果物フォーマット定義・停止規律・禁止規範の削除や `--allow-missing` によるアンカー削除宣言（T-6 依頼文が禁じた操作）も、当然行っていない。

- **AC-11（移送の実質性）**: 達成（§1「`skill_decrease` / `refs_net_increase`」参照）。RED 確認として「移送のみ・削除 0」のダミー差分（`references/debug-triage.md` へ追記し、SKILL.md の変更を `git stash` で退避）で判定式が不成立になることを先に確認した。

  ```
  skill_decrease=0 refs_net_increase=2 AC11_OK=False
  ```

  ダミーは `git checkout --` と `git stash pop` で復元し、worktree に残していない。本番判定:

  ```
  skill_decrease=103 refs_net_increase=0 AC11_OK=True
  ```

  `refs_net_increase` は共有 `references/` と skill 同梱 `skills/root-cause-investigation/references/` の両方とも純増なし（どちらのファイルも変更していない）。したがって S-3（T-10）の引き下げ根拠から除外すべき移送分は存在しない。

## 8. 逐語照合レビューの指摘と修正実施記録（2026-07-31）

独立 subagent による逐語照合（`handoff/t-6-collation.md`、判定 fail・指摘 3 件）を受けて修正した。

| # | 指摘 | 対応 |
|---|---|---|
| 指摘 1（中） | `### When Process Reveals No Root Cause` の `No Root Cause Decision` 発行条件は AND 条件だが、後半を ` / ` で併合した結果、同一行内の `True / False / inconclusive`（選択肢）と同じ記号になり OR 誤読が可能になっていた。停止規律の発行要件が緩む方向 | **原本から逐語復元**した。当該併合を戻し、発行条件を原本どおり独立 bullet に分けた。推測での書き直しはしていない。行数が増える方向の修正だが、停止規律の意味保存を優先した（§1「body 行数」は復元後の値） |
| 指摘 2（中） | §7 の AC-8 未達理由が、引用していた指標だけでは論証として閉じていなかった | §1 に「コードフェンス行数」「テーブル行数」「空行数」「削除不能行の下限」を追加し、§7 の論証を下限の実測値に基づく形へ書き換えた |
| 指摘 3（低） | §6 F-1 の「移送候補 5 節はいずれも set5 の規範文アンカーを含む」が事実誤り（`## 合理化との対決` は set5 に該当行を持たない） | F-1 の記述を訂正した。あわせて逐語照合が独立実測した「5 節を全移送しても目標未達」を出典併記で追記した |

逐語照合が独立に確認した事項（`handoff/t-6-collation.md` §2 / §5）:

- 削除された非空行は全件が蒸留版に contiguous かつ原本順序どおり残存
- 文字多重集合の比較で `only in old` が空集合（原本の文字が 1 つも失われていない）
- 見出し全行・テーブル全行・コードフェンス全内容が原本と完全一致
- 落ちやすい 3 類型（長い bullet 中間の従属節 / 出力先の指定 / session 参照付き規範文）の欠落なし、Step・ゲート・数値閾値・出力形式の捏造なし
- §6 F-1 について「移送すれば目標に届いたのに避けた」型の正当化には**該当しない**（独立実測で裏取り済み）

修正後の再実測は §1 に反映済み。`verify` は復元後も欠落 0 を維持している（§3 参照）。

### 修正後の再検証で追加された指摘（`handoff/t-6-collation.md` §10、判定 fail・指摘 3 件）

| # | 指摘 | 対応 |
|---|---|---|
| 再検証 A（中） | §7 の AC-8 未達理由が「到達手段は 2 つしかない」という**不可能性の主張**になっていたが、下限は保守的前提の下の値であり、さらなる併合という第 3 の経路が存在する（独立実測で構成的に反証された） | §7 を書き換え、**到達不能ではなく意味保存を優先した結果としての未達**であることを明示した。§1「削除不能行の下限」の指標名に前提を明記し、§6 F-2 にも同旨を追記した |
| 再検証 B（低） | §7 AC-11 の本番判定の逐語出力が復元前の値のままで、§1 の該当セルと矛盾していた | 逐語出力を再実測値へ更新した |
| 再検証 C（低） | §4 の `### When Process Reveals No Root Cause` セルが復元前の記述（発行条件を併合した旨）のままだった | 実態（導入段落のみ併合、発行条件は復元済み）へ更新した |

あわせて逐語照合の参考観察（開示補強）を反映し、§2 の操作種別に連結子の使い分けを、§4 の Phase 1 / State Machine Integration セルに未開示だった併合箇所を追記し、§6 F-4 の記述から復元済み箇所を除外した。

再検証で確認された事項: §1 の再実測可能セルは全一致、復元は原本とバイト単位で一致、副作用検査（文字多重集合・見出し / テーブル / フェンス一致・番号列・順序）はいずれも従前どおり、§8 に虚偽の作業主張なし。
