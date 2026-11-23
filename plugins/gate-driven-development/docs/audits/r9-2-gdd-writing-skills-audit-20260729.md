# R9-2 Wave 1 蒸留監査シート: `skills/gdd-writing-skills/SKILL.md`

> 本シートは `design.md` § D-7 / ADR-12 の構造に従う。**対象成果物の実測値は §1 の表にのみ書く**。他節は指標名で §1 を参照し、測定値リテラルを持たない。例外は逐語領域（コマンド出力の逐語引用）と、出典を併記した外部由来値。

- 実施タスク: T-7（S-2 / 対象6）
- 実施日: 2026-07-31
- cwd（本シートの全コマンドの実行位置）: `plugins/gate-driven-development`
- `<candidate_path>` = `skills/gdd-writing-skills/SKILL.md`
- `<archive_path>` = `docs/references-archive/gdd-writing-skills-SKILL-pre-r9-2-wave1-original.md`
- `<anchors_path>` = `docs/audits/r9-2-gdd-writing-skills-anchors.txt`
- `<archive_commit>` = `931df6d`（archive と anchors を含む単独コミット。SKILL.md 本体は未変更）

## 1. 実測サマリ

再実測コマンドで使うヘルパー。以降の表はこれと上記パス定義が読み込み済みであることを前提にする。定義は T-6 の監査シート（`r9-2-root-cause-investigation-audit-20260729.md` §1）と同一で、パスのみ本対象に置換している。

```bash
archive_path=docs/references-archive/gdd-writing-skills-SKILL-pre-r9-2-wave1-original.md
candidate_path=skills/gdd-writing-skills/SKILL.md
anchors_path=docs/audits/r9-2-gdd-writing-skills-anchors.txt
archive_commit=931df6d

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
anchor_cover() {  # 貪欲 set cover。全アンカーを担持できる行集合の greedy 解のサイズ（併合・書き換えなし、行の削除のみ）
  python3 -c "import json,pathlib,sys;A={a for s in json.load(open(sys.argv[2]))['sets'].values() for a in s};L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];hit={a:{i for i,l in enumerate(b) if a in l} for a in A};un={a for a,h in hit.items() if h};cov=set()
while un:
    i=max(range(len(b)),key=lambda j:sum(1 for a in un if j in hit[a]))
    g=[a for a in un if i in hit[a]]
    if not g: break
    cov.add(i); un-=set(g)
print('unique_anchors=%d uncovered=%d greedy_lines=%d'%(len(A),len(un),len(cov)))" "$1" "$2"
}
anchor_floor() {  # アンカー担持行を 1 行も落とさない構成のサイズ（非アンカー行を全削除した仮想ファイル）
  python3 -c "import json,pathlib,sys;A={a for s in json.load(open(sys.argv[2]))['sets'].values() for a in s};L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];ks=[i for i,l in enumerate(b) if any(a in l for a in A)];blocks=1+sum(1 for x,y in zip(ks,ks[1:]) if y!=x+1);print(f'anchor_lines={len(ks)} blocks={blocks} floor={len(ks)+blocks-1}')" "$1" "$2"
}
ac11() {  # AC-11 判定（tasklist.md T-7 Step 5 のコード片と同一。終点は常に HEAD）
  git -C ../.. diff --numstat "$archive_commit" HEAD -- \
    plugins/gate-driven-development/skills/gdd-writing-skills/SKILL.md \
    plugins/gate-driven-development/references/ \
  | python3 -c "import sys;rows=[l.split(chr(9)) for l in sys.stdin.read().splitlines()];sd=sum(int(d)-int(i) for i,d,p in rows if 'skills/gdd-writing-skills/SKILL.md' in p);rn=max(sum(int(i)-int(d) for i,d,p in rows if p.startswith('plugins/gate-driven-development/references/')),0);print(f'skill_decrease={sd} refs_net_increase={rn} AC11_OK={sd>=2*rn}')"
}
numstat() { git -C ../.. diff --numstat "$archive_commit" HEAD -- plugins/gate-driven-development/skills/gdd-writing-skills/SKILL.md; }
verbatim_check() {  # 削除行の全件照合（§5）。非空削除行の本文が蒸留版に逐語 contiguous に残っているか
  git -C ../.. diff -U0 "$archive_commit" HEAD -- plugins/gate-driven-development/skills/gdd-writing-skills/SKILL.md \
  | python3 -c "import sys,re,pathlib;new=pathlib.Path('$candidate_path').read_text(encoding='utf-8');d=[l[1:] for l in sys.stdin.read().splitlines() if l.startswith('-') and not l.startswith('---')];ne=[l for l in d if l.strip()];miss=[l for l in ne if re.sub(r'^\d+\.\s*','',re.sub(r'^[-*]\s*','',l.strip())) not in new];print(f'deleted={len(d)} non_blank={len(ne)} blank={len(d)-len(ne)} not_contiguous={len(miss)}')"
}
```

| # | 指標 | 蒸留前 | 蒸留後 | 目標 | 判定 | 再実測コマンド |
|---|---|---|---|---|---|---|
| 1 | body 行数 | 590 | 558 | ≤350（AC-8） | **未達（§7）** | `body_metrics "$archive_path"` / `body_metrics "$candidate_path"` |
| 2 | body chars | 20,841 | 20,215 | — | 参考 | 同上 |
| 3 | 推定トークン | 5,211 | 5,054 | 目標なし（`design.md` D-5 Amendment 2） | 参考 | 同上 |
| 4 | body 行数削減率 | — | −5.4% | — | 導出（旧#1） | 導出値 |
| 5 | 推定トークン削減率 | — | −3.0% | — | 導出（旧#3） | 導出値 |
| 6 | SKILL body 合計行数（全 skills） | 7,074 | 7,042 | 引き下げに寄与（AC-6 旧#2） | 達成 | `pre_budget_totals` / `budget_totals .` |
| 7 | 全 skills の最大 body 行 | 590 | 558 | ≤636（AC-6 旧#7） | 達成 | `pre_max_skill_body` / `max_skill_body .` |
| 8 | express profile 合計トークン | 32,804 | 32,804 | — | 不変（本対象は profile 非収載） | `pre_budget_totals` / `budget_totals .` |
| 9 | standard profile 合計トークン | 56,004 | 56,004 | — | 不変（本対象は profile 非収載） | 同上 |
| 10 | `references/` 合計行数 | 12,183 | 12,183 | — | 不変（移送 0 件。§6 F-1） | `refs_lines` |
| 11 | locked 行数（set1+set4+set5） | 181 | 180 | — | 参考 | `locked_chars "$archive_path" "$anchors_path"` / `locked_chars "$candidate_path" "$anchors_path"` |
| 12 | locked chars | 6,891 | 6,796 | — | 参考（§4） | 同上 |
| 13 | locked 比率（対 旧#2 蒸留前） | 33.1% | — | — | 導出（旧#12 ÷ 旧#2） | 導出値 |
| 14 | アンカーが一意に対応する body 行数 | 154 | 154 | — | 参考（§7） | `unique_locked "$archive_path" "$anchors_path"` / `unique_locked "$candidate_path" "$anchors_path"` |
| 15 | アンカー総数 | 391 | 391 | 欠落 0（AC-1） | 達成 | `anchor_counts "$anchors_path"` |
| 16 | アンカー set 別内訳 | set1=57 set2=2 set3=225 set4=78 set5=29 | 同左 | — | 参考 | 同上 |
| 17 | アンカー欠落数 / allow list 宣言数 | — | 0 / 0 | 0 / 0（AC-1） | 達成 | §3 の `verify` |
| 18 | `selftest` ケース数 | — | 22 | 全 pass | 達成 | §3 の `selftest` |
| 19 | numstat insertions / deletions | — | 7 / 39 | — | 参考 | `numstat` |
| 20 | 削除行の分類内訳（非空 / 空行） | — | 32 / 7 | 合計 = 旧#19 deletions | 整合 | `verbatim_check` |
| 21 | 非空削除行のうち本文が蒸留版に逐語 contiguous 残存した行数 | — | 14 | — | 参考 | 同上 |
| 22 | 非空削除行のうち逐語残存しない行数（§5 で 1 件ずつ残存先を特定） | — | 18 | 全件について残存先または削除根拠が特定されていること（AC-3） | 達成（§5） | 同上（`not_contiguous`） |
| 23 | 削除行の分類内訳（intra-file duplicate / 背景散文 / ラベル行 / 圧縮吸収） | — | 21 / 1 / 2 / 8 | 合計 = 旧#20 非空 | 整合 | N/A（読解による分類。根拠は §5 全件照合） |
| 24 | `skill_decrease` / `refs_net_increase` | — | 32 / 0 | `skill_decrease ≥ 2 × refs_net_increase`（AC-11） | 達成 | `ac11` |
| 25 | `validate-plugin.sh` / `pytest` exit | — | 0 / 0 | 0 / 0（AC-2） | 達成 | §7 |
| 26 | `pytest` 結果（passed / subtests passed） | — | 790 / 607 | T-6 完了時点の baseline と同値（AC-2。出典: `tasklist.md` T-7 RED Evidence（AC-2）） | 達成 | `python3 -m pytest plugins/gate-driven-development/tests/ -q`（リポジトリルートで実行） |
| 27 | コードフェンス行数（フェンス記号行を含む） | 166 | 166 | — | 不変 | `structure_lines "$archive_path"` / `structure_lines "$candidate_path"` |
| 28 | テーブル行数 | 52 | 52 | — | 不変 | 同上 |
| 29 | 空行数 | 128 | 121 | — | 参考 | 同上 |
| 30 | 保守的構成のサイズ（一意固定行 ∪ フェンス行 ∪ テーブル行 + ブロック境界の空行）。**下限ではない**（フェンス行・テーブル行のうち非アンカー行を無条件に残す編集判断を含む。§7） | 393 | 393 | — | 参考（§7） | `floor_lines "$archive_path" "$anchors_path"` / `floor_lines "$candidate_path" "$anchors_path"` |
| 31 | アンカー担持行を 1 行も落とさない構成のサイズ（非アンカー行を全削除した仮想ファイル）。**下限ではない**（アンカーは複数行に冗長出現するため担持行の一部は削除可能。§7） | 507 | 490 | — | 参考（§7） | `anchor_floor "$archive_path" "$anchors_path"` / `anchor_floor "$candidate_path" "$anchors_path"` |
| 32 | 貪欲 set cover による全アンカー担持行数（併合・書き換えなし。行の削除のみで到達しうる構成のサイズ。未担持アンカー 0） | 181 | 180 | — | 参考（§7 の AC-8 到達可能性判定に使う。目標列 350 を下回る） | `anchor_cover "$archive_path" "$anchors_path"` / `anchor_cover "$candidate_path" "$anchors_path"` |
| 33 | 一意アンカー数（`<anchors_path>` の set 間重複を除いた数。旧#15 は set 別の延べ数） | 361 | 361 | — | 参考 | 同上 |

## 2. 蒸留方針

`skill-body-budget.sh` に登録された reduction plan は「開発時のみ必要なガイダンスを `docs/` または `references/` へ移送し、runtime skill body を最小に保つ」。本 task はこの plan の**移送を採らず、削除のみで蒸留した**。理由は §6 F-1 に記す（移送候補が AC-1 のアンカーで固定されているため、移送すると `verify` が欠落を検出する）。

適用した操作は次のとおりで、いずれも**行併合による見かけ上の行数稼ぎではない**（内訳の件数は §1「削除行の分類内訳（intra-file duplicate / 背景散文 / ラベル行 / 圧縮吸収）」参照）。

1. **intra-file duplicate の削除**: 同一ファイル内の別節が正本として同じ内容を持つ行を削除する。削除した行の内容が残っている節を §5 で 1 件ずつ特定した。
2. **背景・理由の散文の削除**: 規範でも契約でもない動機説明を削除する。
3. **ラベル行の削除**: 直後の箇条書きを導入するだけで内容を持たないラベル行（`**原則**:` 等）を削除する。箇条書きは直前の段落に続けて読める。
4. **圧縮吸収**: ラベル行と、その直後・直前にあった 1 文を同一行へ吸収する。吸収された文は逐語のまま保持する。

**条件の論理構造を併合で曖昧にしていない**。本 task で新設した行はいずれも節間参照（ポインタ）と例示ラベルであり、AND / OR 条件・チェックリスト・発行要件を ` / ` で併合した箇所は無い（T-6 で実欠陥になった操作型を本 task では使っていない）。

**原本に無い文言の追加**は §5 に全件を列挙した。追加はすべて「どの節が正本か」を指す節間参照で、参照先の節見出しが本文中に実在することを `grep -F` で確認済み（§3）。

## 3. アンカー機械照合（AC-1）

```
$ python3 docs/audits/r9-2-anchor-tools.py selftest
SELFTEST_OK: 22 cases passed

$ python3 docs/audits/r9-2-anchor-tools.py verify \
    --anchors docs/audits/r9-2-gdd-writing-skills-anchors.txt \
    --candidate skills/gdd-writing-skills/SKILL.md
ANCHOR_VERIFY_OK: 391 anchors checked, 0 unexpected missing (0 allowed) in skills/gdd-writing-skills/SKILL.md
```

`--allow-missing` は使っていない（アンカー削除の宣言は承認済み禁止事項）。

新設したポインタ行が指す節見出しの実在確認（T-9 で「実在しない委譲先へ委譲した」と書いた失敗の再発防止）:

```
$ for s in '## Skill 種別フレームワーク' '## Rationalization Check ルール' \
           '## Supporting References / Scripts の配置ルール' '## 新規 Phase Gate skill テンプレート' \
           '## 新規 Methodology skill テンプレート' '## 命名規約'; do
    printf '%s -> ' "$s"; grep -c -F "$s" skills/gdd-writing-skills/SKILL.md; done
## Skill 種別フレームワーク -> 1
## Rationalization Check ルール -> 1
## Supporting References / Scripts の配置ルール -> 1
## 新規 Phase Gate skill テンプレート -> 1
## 新規 Methodology skill テンプレート -> 1
## 命名規約 -> 1
```

## 4. 節別判定（定性）

| 節 | 判定 | 何を保持したか / 何をしたか |
|---|---|---|
| 冒頭導入 | 挙動維持 | superpowers との補完関係の記述を削除。同内容は `他 skill との関係` § の `superpowers:writing-skills` 行が正本 |
| `Process Documentation TDD` | 無変更 | — |
| `Skill Type Testing Matrix` | 無変更 | — |
| `なぜこの skill が要るか` | 挙動維持 | `state.md` / `tasklist.md` / `worklog.md` の正本性の記述を保持。残る暗黙規約（description の書き出し / `Rationalization Check` の列数 / supporting reference の置き場所）は正本節へのポインタに置換。動機を述べる散文を削除 |
| `Iron Law` | 無変更 | — |
| `Skill RED-GREEN Evidence` | 無変更 | — |
| `When to Use` | 無変更 | — |
| `Skill 種別フレームワーク` | 挙動維持 | 4 種別の見出し・`例`・`特徴`・`description 書き出し` を全て保持。種別 1 / 種別 2 の `標準セクション順` 列挙のみ、対応するテンプレート節の見出し順へのポインタに置換（テンプレート節が同じ順序を見出しとして持つ）。種別 2 の `命名` は `命名規約` § へのポインタに統合。種別 3 / 種別 4 はテンプレートが無いため `標準セクション順` を原文のまま保持 |
| `命名規約` | 無変更 | — |
| `SKILL.md frontmatter ルール` | 挙動維持 | frontmatter テンプレート・`description` の要件・CSO の原則群を保持。`name` の一致要件は frontmatter テンプレートのコメントとチェックリストが保持（§6 F-3）。`悪い例` と `良い例` はいずれも保持し、各例の説明文を見出し行へ吸収 |
| `Skill Slimming Discipline` | 挙動維持 | slimming 規則・SemVer 判定表・依存波及手順・同時更新表を保持。SemVer 節の導入文にあった保守側へ倒す方針は `判断に迷うときの保守ルール` § が正本。`patch / minor` 行は規則本体を保持し理由の括弧書きのみ削除 |
| `Rationalization Check ルール` | 挙動維持 | 種別別フォーマット表・3 列 / 2 列テンプレート・運用規則を全て保持。使い分けの理由の各項目も保持し、そのラベル行のみ削除 |
| `Supporting References / Scripts の配置ルール` | 無変更 | — |
| `State Machine への接続ルール` | 無変更 | — |
| `新規 Phase Gate skill テンプレート` | 無変更 | — |
| `新規 Methodology skill テンプレート` | 無変更 | — |
| `新規 skill 追加チェックリスト` | 無変更 | 本文規則と重複するチェック項目も削除しなかった（チェックリストは実行時に単独で走査される成果物であり、項目を落とすと実行者の行動が変わるため） |
| `Rationalization Check（この skill 固有）` | 無変更 | — |
| `Guardrails` | 無変更 | — |
| `他 skill との関係` | 無変更 | — |
| `Quick Reference` | 無変更 | — |

## 5. `diff` 削除行の全件照合

`verbatim_check` の分類は §1「削除行の分類内訳（非空 / 空行）」参照。逐語 contiguous に残存しなかった行（§1「非空削除行のうち逐語残存しない行数」）を全件、残存先または削除根拠とともに列挙する。

| # | 削除行（原本） | 分類 | 残存先 / 根拠 |
|---|---|---|---|
| 1 | `両者は補完関係。skill 全般の書き方は superpowers 側、GDD 固有の規約はここを参照する。` | intra-file duplicate | `他 skill との関係` § の `superpowers:writing-skills` 行「skill 作成全般の TDD 規律…GDD 固有の規約ではなく skill 作成の方法論を扱う。両方併用が望ましい」 |
| 2 | `- description の書き出しが種別ごとに違う（…）` | intra-file duplicate | `Skill 種別フレームワーク` § の 4 種別それぞれの `**description 書き出し**` ブロック（原文のまま残存） |
| 3 | `- Rationalization Check 表は 3 列で、Why ラベルは references/rationalization-root-causes.md を参照` | intra-file duplicate | `Rationalization Check ルール` § の種別別フォーマット表と `**Why 列のラベル**は references/rationalization-root-causes.md から選ぶ` |
| 4 | `- supporting reference は skill 内 references/、plugin 共通 reference は /references 直下` | intra-file duplicate | `Supporting References / Scripts の配置ルール` § の 3 階層表 |
| 5 | `これらは「前の skill を真似する」ことで伝承されているが…` | 背景散文 | 残存先なし。動機説明であり規範・契約・数値閾値を含まないため削除（§2 操作 2） |
| 6 | `3. Phase Gate Pre-check（前提条件）` | intra-file duplicate | `新規 Phase Gate skill テンプレート` § の `## Phase Gate Pre-check` と直後の「開始前に確認する gate 状態:」（括弧の語釈に対応） |
| 7 | `5. Output Guidance（次 phase への handoff 形式）` | intra-file duplicate | 同テンプレート § の `## Output Guidance` と直後の「phase 完了時の handoff 形式:」 |
| 8 | `3. 適用範囲（When to Use / 使わない場面）` | intra-file duplicate | `新規 Methodology skill テンプレート` § の `## 適用範囲` と直下の「使うべき場面:」「使わない場面:」 |
| 9 | `4. Phases or Steps` | intra-file duplicate | 同テンプレート § の `## <N> Phases / Steps` |
| 10 | `6. 合理化との対決（superpowers 風の Rationalization 表）` | intra-file duplicate | 同テンプレート § の `## 合理化との対決` と直後の引用ブロック（`superpowers 風` の語を含む） |
| 11 | `**命名**: gdd- prefix を **付けない**（汎用なので）` | intra-file duplicate | `命名規約` § の `- **GDD 非依存の汎用 methodology**: gdd- 外す（例: root-cause-investigation）`。加えて種別 2 のポインタ行に「命名は `命名規約` § のとおり `gdd-` prefix を付けない」を明記 |
| 12 | `- name は必須・ディレクトリ名と完全一致` | intra-file duplicate | frontmatter テンプレートの `name: <kebab-case-name>     # ディレクトリ名と一致` とチェックリストの `- [ ] ディレクトリ名と name frontmatter が一致`（§6 F-3 に flag） |
| 13 | `**原則**:` | ラベル行 | 内容を持たないラベル。直後の箇条書きは全行保持 |
| 14 | `**Why この使い分け**:` | ラベル行 | 内容を持たないラベル。直後の各項目は全行保持 |
| 15 | `**悪い例**:` | 圧縮吸収 | `**悪い例** — これは実行順を要約しており…` へ吸収（説明文は逐語保持） |
| 16 | `**良い例**:` | 圧縮吸収 | `**良い例** — こちらは発火条件を示し…` へ吸収（説明文は逐語保持） |
| 17 | `skill / plugin の version bump は SemVer に従う。判定に迷うときは保守的に倒す（破壊的判定を選ぶ）。` | 圧縮吸収 | 前半は逐語で残存。後半（保守側へ倒す方針）は `判断に迷うときの保守ルール` § の各項目が正本 |
| 18 | `- patch / minor で迷ったら **minor**（小修正の連打で…）` | 圧縮吸収 | 規則本体は逐語で残存。括弧内の理由のみ削除（規範・閾値を含まない） |

**追加行の全件**（原本に無い文言。捏造検査の対象）:

| # | 追加行 | 種類 |
|---|---|---|
| A1 | `- description の書き出し・Rationalization Check の列数・supporting reference の置き場所は、それぞれ後続の Skill 種別フレームワーク / Rationalization Check ルール / Supporting References / Scripts の配置ルール § が正本` | 節間参照（削除 旧#2 / 旧#3 / 旧#4 の置換） |
| A2 | `**標準セクション順**: 新規 Phase Gate skill テンプレート § の見出し順に従う。` | 節間参照（削除 旧#6 / 旧#7 を含む列挙の置換） |
| A3 | `**標準セクション順**: 新規 Methodology skill テンプレート § の見出し順に従う。命名は 命名規約 § のとおり gdd- prefix を付けない。` | 節間参照（削除 旧#8〜旧#11 を含む列挙の置換） |
| A4 | `**悪い例** — これは実行順を要約しており…` | 既存 2 行の吸収（新規の主張なし） |
| A5 | `**良い例** — こちらは発火条件を示し…` | 既存 2 行の吸収（新規の主張なし） |
| A6 | `skill / plugin の version bump は SemVer に従う。` | 既存行の前半のみ（新規の主張なし） |
| A7 | `- patch / minor で迷ったら **minor**` | 既存行から括弧内理由を除いたもの（新規の主張なし） |

A1〜A3 の参照先はすべて §3 の `grep -F` で実在を確認済み。A4〜A7 は原本の文字列の部分集合であり、新しい主張を持たない。

## 6. flag

| # | 内容 | 判断 |
|---|---|---|
| F-1 | reduction plan が指示する `docs/` / `references/` への移送は、本対象では **AC-1 と両立しない**。移送候補として最大の質量を持つテンプレート節（`新規 Phase Gate skill テンプレート` / `新規 Methodology skill テンプレート`）は、ほぼ全行が set1（見出し）と set4（コードフェンス内の全行）のアンカーで固定されている。SKILL.md から出すと `verify` がその全行を欠落として検出し、回避するには `--allow-missing` によるアンカー削除宣言が要る（承認済み禁止事項）。よって移送を行わず、削除のみで蒸留した | blocking ではない。AC-11 は移送がないため自明に成立（§1「`skill_decrease` / `refs_net_increase`」参照） |
| F-2 | **AC-8 未達**。ただし**到達不能ではない**。§1「貪欲 set cover による全アンカー担持行数」は §1「body 行数」の目標列を下回り、AC-1 と両立したまま目標行数へ到達する経路（非アンカーの説明散文の削除）が構成的に存在する。未達は**意味保存を優先した判断**の結果である（§7） | S-3（T-10）でこの対象の baseline を新実測値へ引き下げ、未達理由を script コメントに残す運用へ回す（`design.md` D-5 手順 2）。**script コメントに書く理由は「AC-1 が構造的に塞いでいる」ではなく「意味保存を優先した判断」であること**（§7 / §8 M-1） |
| F-3 | 削除 旧#12（`- name は必須・ディレクトリ名と完全一致`）は「必須」という規範語を含む行だった。一致要件そのものは frontmatter テンプレートのコメントとチェックリスト項目が保持しているが、「必須」という語自体は本文から消えた | 一致要件は frontmatter テンプレートとチェックリストの双方で維持され、チェックリストは commit 前の全項目確認を課しているため実効性は変わらないと判断した。読解で異議があれば原本から逐語復元する |
| F-4 | 本 task の削減量は §1「body 行数削減率」「推定トークン削減率」のとおり小さい。T-6 の留保（行数だけ動いてトークンが動かない）は回避したが、削減の絶対量は小さい | **削減余地はアンカー contract に塞がれてはいない**（§7 / F-2）。残る削減余地は非アンカーの説明散文であり、それを削ると skill として読めなくなるため今回は採らなかった。行併合で行数だけを稼ぐ選択も取らなかった |

## 7. 検証結果

### AC-1 / AC-2 / AC-3 / AC-4 / AC-5 / AC-11

- AC-1: §3 のとおり `selftest` と `verify` がともに exit 0。欠落・allow 宣言は §1「アンカー欠落数 / allow list 宣言数」参照
- AC-2: 下記の逐語出力

```
$ bash tests/validate-plugin.sh ; echo "exit=$?"
exit=0

$ python3 -m pytest plugins/gate-driven-development/tests/ -q
790 passed, 607 subtests passed in 168.69s (0:02:48)
```

- AC-3: 削除行の全件照合は §5。新規 subagent による逐語照合は実装フェーズ Step 7 で実施する
- AC-4 / AC-5: archive コミット `931df6d`（archive + anchors のみ）が蒸留コミットに先行する 2 コミット構造
- AC-11: 移送がないため判定式は自明に成立（§1「`skill_decrease` / `refs_net_increase`」参照）。`references/` 配下に差分は無く、`docs/` へのポインタも本文に無い（`grep -n 'docs/' <candidate_path>` が `NO_DOCS_POINTER`）。したがって `design.md` D-4 の `docs/` 分岐は「削除」計上側で確定する

### AC-8（body ≤350 行）の到達可能性

**未達。ただし到達不能によるものではなく、意味保存を優先した判断の結果である。**

§1「保守的構成のサイズ」と §1「アンカー担持行を 1 行も落とさない構成のサイズ」は、いずれも**保守的前提の下で作った特定の構成のサイズであって、下限ではない**。前提は 2 つある。

1. 一意固定行に加えて**フェンス行・テーブル行を無条件に残す**。これらのうちアンカーを担持しない行は AC-1 が課す制約ではなく、内容を残したいという編集判断である。
2. **アンカー担持行を 1 行も落とさない**。実際にはアンカーの多くが複数行に冗長に出現するため、担持行の一部を落としても `verify` は成立する。

両前提を外すと、実際に必要な行数は §1「貪欲 set cover による全アンカー担持行数」であり、これは §1「body 行数」の目標列を**下回る**。この行だけを残した候補ファイル（**行の削除のみ。併合なし・書き換えなし・`--allow-missing` なし**）を作って `verify` を実行し、構成的に確認した（確認後に候補を破棄して原ファイルを復元し、`git status` が clean であることを確認済み）:

```
$ python3 docs/audits/r9-2-anchor-tools.py verify \
    --anchors docs/audits/r9-2-gdd-writing-skills-anchors.txt \
    --candidate skills/gdd-writing-skills/SKILL.md   # 中身を set cover 候補に差し替えた状態
ANCHOR_VERIFY_OK: 391 anchors checked, 0 unexpected missing (0 allowed) in skills/gdd-writing-skills/SKILL.md
exit=0
```

すなわち §1「body 行数」目標列への到達経路は、(a) アンカー担持行を削除して `--allow-missing` で欠落を宣言する、(b) アンカー行同士を併合して行数だけを減らす、の 2 択ではない。**(c) 非アンカーの説明散文を削除する**という経路が AC-1 と両立して存在する。

**それを採らなかったのは品質判断である。** AC-1 の 5 集合は意味保存の機械的な proxy であり、そこに含まれない説明文・規範散文・箇条書きの保存は守らない（`requirements.md` L91 の Honest Limitations が既に明示）。set cover が残す行だけの文書は `verify` を通るが、skill として読めず実行者の行動を再現できない。行数指標を満たすために読めない文書を作る選択は採らなかった。

(a) と (b) も行っていない。(a) は承認済み禁止事項であり、(b) は T-6 で AND 条件の OR 誤読という実欠陥を生んだ操作で、かつ実コンテキストを減らさない（T-6 は行数 −16.0% に対し推定トークン −0.7%。出典: `handoff/t-6-impl-gate.md` の留保）。

したがって **AC-8 は「到達不能」ではなく、「意味保存を優先した結果として未達」である**（T-6 監査シート §7 の AC-8 と同じ結論構造）。

本 task の削減は §1「body 行数削減率」と §1「推定トークン削減率」の両方が負であり、**行数だけが動いてトークンが動かない** T-6 の型は回避している。ただし絶対量は小さい（§6 F-4）。

### AC-6

- 旧#7（全 skills の最大 body 行 ≤636）: §1「全 skills の最大 body 行」参照。蒸留後も本対象が制約元のまま、目標列を下回る
- 旧#2（SKILL body 合計の引き下げ）: §1「SKILL body 合計行数（全 skills）」参照
- 旧#5 / 旧#6（express / standard profile のトークン）: 本対象は両 profile に非収載のため不変（§1「express profile 合計トークン」「standard profile 合計トークン」）
- 7 値の最終判定は T-10 の一括実測で行う

### D-7 決定 6 の機械確認 5 手順

| 手順 | 結果 |
|---|---|
| 1 走査 | `design.md` 記載の awk をそのまま実行し、§1 の表行とコードフェンスを除いた数値含有行を全件取得 |
| 2 判定 | 逐語領域外に残る数値は、識別子（`T-7` / `AC-8` / `set1` 等）・日付・commit sha・目標由来値（出典併記）・節番号・§5 の連番のみ。**新規の測定値混入なし**（impl-gate advisory A-1 で指摘された §6 F-1 / §7 AC-11 の「移送 0 件」は §8 で指標名参照へ書き換え済み） |
| 3 §1 突合 | `再実測コマンド` 列が `N/A` でない全行を実行し全件一致 |
| 4 逐語領域突合 | §3 の `SELFTEST_OK` / `ANCHOR_VERIFY_OK`、§7 AC-2 の `790 passed, 607 subtests passed`、§7 AC-8 の `ANCHOR_VERIFY_OK` がいずれも再実行と一致 |
| 5 remediation 時の再実行 | §8 の remediation コミット直前に手順 1〜4 を再実走し、結果を本表に反映済み |

## 8. impl-gate（`impl-gate-20260731-15`）差し戻しの修正実施記録（2026-07-31）

`handoff/t-7-impl-gate.md` の changes_requested（Medium M-1 / ops-blocking）を受けて修正した。**`skills/gdd-writing-skills/SKILL.md` は変更していない**（`git diff` で無変更を機械確認済み）。

| # | 指摘 | 対応 |
|---|---|---|
| M-1（ops-blocking medium） | §7 が AC-8 を「AC-1 と両立する範囲では構造的に到達不能」と主張していたが、根拠にした 2 指標はいずれも下限ではない。フェンス行・テーブル行のうち非アンカー行を無条件に固定扱いしており、貪欲 set cover を取ると全アンカーが目標行数未満の行集合に収まる（gate 側が `verify` exit 0 で構成的に反証） | §7 AC-8 を全面書き換えし、到達不能の主張を撤回。**未達理由を「意味保存を優先した判断」**として述べ直した（T-6 監査シート §7 AC-8 と同じ結論構造に揃えた）。§1 に「貪欲 set cover による全アンカー担持行数」「一意アンカー数」を追加し、set cover 候補での `verify` exit 0 を §7 に逐語出力で記録。§1 旧#30 / 旧#31 の指標名から「下限」を外し、保守的前提を明記。§6 F-2 / F-4 を同じ結論へ整合させた |
| A-1（advisory・採用） | §6 F-1 / §7 AC-11 の「移送 0 件」「移送 0」は §1「`references/` 合計行数」が正本の測定値であり、D-7 の免除リストに当たらない。手順 2 の「測定値混入 0 件」は厳密には過大 | 両箇所を「移送を行わず」「移送がないため」へ書き換え、測定値リテラルを除去した。D-7 手順 2 の記述も実態に合わせた |
| A-2（advisory・不採用） | 追加行 A1 が 3 つの節ポインタを ` / ` で併合しており、3 つ目の節名自体が ` / ` を含むため素のテキストでは 4 項目に読める | **SKILL.md の変更が必要なため本 remediation では採らない**（本差し戻しの route は監査シートのみの `implementation_fix_only`）。gate 自身が「AND / OR 条件の併合ではないため T-6 の欠陥類型ではない」と判定しており、各節名は code span で分離される。T-8 の carry-forward として引き継ぐ |
| A-3（advisory・不採用） | 追加行 A2 の委譲先テンプレートに入れ子フェンス内の例示見出しが混在するため、ポインタ側に `##` 見出しのセクション数を明示すると照合が堅くなる | 同上（SKILL.md の変更が必要）。T-8 の carry-forward として引き継ぐ |

**再発防止（T-8 以降への carry-forward）**: 「削減の下限」を計算するときは、**アンカーを担持する行のみを固定扱い**し、貪欲 set cover で実際に到達可能な行数を測ること。非アンカーのフェンス行・テーブル行・説明散文を無条件に固定扱いすると、下限が過大に出て「構造的に到達不能」という誤った結論になる。同型の誤りは T-6（逐語照合が反証）と T-7（impl-gate が反証）で 2 回連続して発生している。
