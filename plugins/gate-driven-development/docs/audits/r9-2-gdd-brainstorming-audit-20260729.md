# R9-2 Wave 1 蒸留監査シート: `skills/gdd-brainstorming/SKILL.md`

> 本シートは `design.md` § D-7 / ADR-12 の構造に従う。**対象成果物の実測値は §1 の表にのみ書く**。他節は指標名で §1 を参照し、測定値リテラルを持たない。例外は逐語領域（コマンド出力の逐語引用）と、出典を併記した外部由来値。

- 実施タスク: T-9（S-2 / AC-6 の最終可動対象）
- 実施日: 2026-07-31
- cwd（本シートの全コマンドの実行位置）: `plugins/gate-driven-development`
- `<candidate_path>` = `skills/gdd-brainstorming/SKILL.md`
- `<archive_path>` = `docs/references-archive/gdd-brainstorming-SKILL-pre-r9-2-wave1-original.md`
- `<anchors_path>` = `docs/audits/r9-2-gdd-brainstorming-anchors.txt`
- `<archive_commit>` = `086e758`（archive と anchors を含む単独コミット）
- 蒸留後 blob: `1b66e2b4b7f170c6eec19be3269efbd11d2330a2`（completion-check `completion-20260801-1` の指摘で 2 箇所を逐語復元した後の値。復元前は `0a0b416e49e7d123720a22cfaca4f43df6a47bd3`）

## 1. 実測サマリ

再実測コマンドで使うヘルパー。以降の表はこれと上記パス定義が読み込み済みであることを前提にする。

```bash
archive_path=docs/references-archive/gdd-brainstorming-SKILL-pre-r9-2-wave1-original.md
candidate_path=skills/gdd-brainstorming/SKILL.md
anchors_path=docs/audits/r9-2-gdd-brainstorming-anchors.txt
archive_commit=086e758

body_metrics() {  # 出力: lines=<int> chars=<int> tokens=<int>（lint-runtime-budget.py と同一定義）
  python3 -c "import sys,math,pathlib;L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b='\n'.join(L[L.index('---',1)+1:]) if L and L[0].strip()=='---' else '\n'.join(L);print(f'lines={len(b.splitlines())} chars={len(b)} tokens={max(1,math.ceil(len(b)/4))}')" "$1"
}
profile_totals() {  # $1 = plugin root
  python3 "$1"/scripts/lint-runtime-budget.py "$1" --max-skill-body-lines 999999 --max-total-skill-body-lines 999999 \
    --max-express-template-lines 999999 --max-standard-template-lines 999999 \
    --max-express-estimated-tokens 999999 --max-standard-estimated-tokens 999999 | grep -E '^- (express|standard) runtime profile'
}
pre_profile_totals() {  # 蒸留前の profile 合計。worktree を変更せず一時ツリーで再現する
  t=$(mktemp -d) && cp -R . "$t"/ && cp "$archive_path" "$t"/"$candidate_path" && profile_totals "$t"; rm -rf "$t"
}
goal_bullets() { awk '/^## Goal/{f=1;next} /^## /{f=0} f' "$1" | grep -c '^- '; }
locked_chars() {  # set1 + set4 + set5 に該当する行（set2 / set3 は短い汎用トークンのため行の locked 判定に使わない）
  python3 -c "import json,pathlib,sys;S=json.load(open(sys.argv[2]))['sets'];A=[a for k in ('1','4','5') for a in S[k]];L=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines();b=L[L.index('---',1)+1:];lk=[l for l in b if any(a in l for a in A)];print(f'locked_lines={len(lk)} locked_chars={sum(len(l)+1 for l in lk)}')" "$1" "$2"
}
anchor_counts() { python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('total',d['total'],'counts',d['counts'])" "$1"; }
```

| # | 指標 | 蒸留前 | 蒸留後 | 目標 | 判定 | 再実測コマンド |
|---|---|---|---|---|---|---|
| 1 | body 行数 | 352 | 312 | ≤350（AC-8） | 達成 | `body_metrics "$archive_path"` / `body_metrics "$candidate_path"` |
| 2 | body chars | 34,738 | 31,899 | — | 参考 | 同上 |
| 3 | 推定トークン | 8,685 | 7,975 | ≤6,820（ADR-8。**Amendment 1 で失効**） | 未達（§7） | 同上 |
| 4 | body 行数削減率 | — | −11.4% | — | 導出（旧#1） | 導出値 |
| 5 | 推定トークン削減率 | — | −8.2% | — | 導出（旧#3） | 導出値 |
| 6 | `## Goal` bullet 数 | 21 | 14 | — | 参考 | `goal_bullets "$archive_path"` / `goal_bullets "$candidate_path"` |
| 7 | express profile 合計トークン | 33,521 | 32,811 | ≤31,999（AC-6 旧#5） | **未達（+812）** | `pre_profile_totals` / `profile_totals .` |
| 8 | standard profile 合計トークン | 56,721 | 56,011 | ≤54,856（AC-6 旧#6） | **未達（+1,155）** | 同上 |
| 9 | references 合計行数 | 12,183 | 12,183 | ≤13,128 | 達成（移送なし） | `find references -name '*.md' \| xargs wc -l \| tail -1` |
| 10 | locked 行数（set1+set4+set5） | 104 | — | — | 参考 | `locked_chars "$archive_path" "$anchors_path"` |
| 11 | locked chars | 14,626 | — | — | 参考 | 同上 |
| 12 | locked 比率（対 旧#2 蒸留前） | 42.1% | — | — | 導出（旧#11 ÷ 旧#2） | 導出値 |
| 13 | アンカー総数 | 572 | 572 | 欠落 0（AC-1） | 達成 | `anchor_counts "$anchors_path"` |
| 14 | アンカー set 別内訳 | set1=22 set2=17 set3=447 set4=12 set5=74 | 同左 | — | 参考 | 同上 |
| 15 | アンカー欠落数 / allow list 宣言数 | — | 0 / 0 | 0 / 0（AC-1） | 達成 | §3 の `verify` |
| 16 | `selftest` ケース数 | — | 22 | 全 pass | 達成 | §3 の `selftest` |
| 17 | `verify` fail 回数（途中経過） | — | 3 | — | 参考（§3・§5） | N/A（実行過程の記録。再現不能） |
| 18 | `verify` fail により逐語復元したアンカー数 | — | 9 | — | 参考 | N/A（§5 の列挙件数） |
| 19 | 照合中に検出した規範文の意図せぬ欠落（復元済み） | — | 2 | — | 参考 | N/A（§5 の列挙件数） |
| 20 | `git diff --numstat` insertions | — | 73 | — | 参考 | `git diff --numstat $archive_commit HEAD -- plugins/gate-driven-development/$candidate_path`（リポジトリルートで実行） |
| 21 | `git diff --numstat` deletions | — | 113 | — | 参考 | 同上 |
| 22 | 削除行内訳: 圧縮・統合により同内容が新版に存在 | — | 103 | — | 参考 | N/A（読解による分類。根拠は §5 全件照合） |
| 23 | 削除行内訳: intra-file duplicate | — | 8 | — | 参考 | N/A（読解による分類。根拠は §5 全件照合） |
| 24 | 削除行内訳: 例示・根拠のみの削除 | — | 2 | — | 参考 | N/A（読解による分類。根拠は §5 全件照合） |
| 25 | AC-11 判定値 `skill_decrease` / `refs_net_increase` | — | 40 / 0 | 移送 0 | 達成 | §2 の逐語出力 |
| 26 | pytest 結果（passed / subtests passed） | 790 / 607 | 790 / 607 | baseline と同値（AC-2） | 達成 | `python3 -m pytest tests/ -q` |

**内訳の自己整合**: 旧#22 + 旧#23 + 旧#24 = 旧#21。

**再実測の実施記録（D-7 適用時）**: 再実測コマンド列が `N/A` でない全行を実行し、上表と一致することを確認した。旧#7 / 旧#8 の蒸留前は一時ツリーで再現、旧#20 / 旧#21 は終点を `HEAD` にして再実行した。`N/A` 行は §5 の列挙との整合を人間確認した。

## 2. AC-11（移送の実質性）判定

```
skill_decrease=40 refs_net_increase=0 AC11_OK=True
```

- **移送は行っていない**（§1 旧#25 の `refs_net_increase`）。削減はすべて SKILL.md 内での削除・統合（intra-file dedup と冗長散文の圧縮）による。
- `references/brainstorming-steps.md` は無変更（§1 旧#9 が増減なし）。Wave 0 で同ファイルを蒸留した判断と矛盾しない（戻し込みなし）。
- したがって S-3（T-10）のバジェット引き下げ根拠から除外すべき「見かけの削減」分は無い。

## 3. AC-1 アンカー照合

- コマンド:

  ```bash
  python3 docs/audits/r9-2-anchor-tools.py selftest
  python3 docs/audits/r9-2-anchor-tools.py verify \
    --candidate skills/gdd-brainstorming/SKILL.md \
    --anchors docs/audits/r9-2-gdd-brainstorming-anchors.txt
  ```

- `selftest`: `SELFTEST_OK: 22 cases passed` / exit 0
- `verify`: `ANCHOR_VERIFY_OK: 572 anchors checked, 0 unexpected missing (0 allowed)` / exit 0
- **allow list は宣言していない**（承認済み削除なし。§1 旧#15）。
- 途中経過として `verify` が fail し（§1 旧#17）、そのつど原本から逐語復元した（§5）。`verify` 単独を保存証跡にせず、`diff` の削除行全件照合と併用した。

## 4. 節別判定

> 本表は測定値を持たない（D-7 決定 3）。定量が要る指標は §1 に行を立てる。判定の誤り（対象名の取り違え・残存先の誤記・挙動変更の見落とし）は blocking（D-7 決定 4）。

| 節 | 変更 | 判定 |
|---|---|---|
| （冒頭導入） | 接続を圧縮 | 挙動維持 |
| `## Goal` | `Workflow Fit Check` / `Engineering Baseline Survey` 系 / `Baseline Verification Status` の各 bullet を削除（いずれも § Steps / § Baseline Verification Before Work に同内容の規範文が存在する intra-file duplicate）。Playwright 系 bullet を統合（内容は全保持）。bullet 数は §1 旧#6 | 挙動維持 |
| `## Subsystem Decomposition Gate` | 独立 subsystem 条件の bullet 群をインライン統合（**条件はすべて保持**）。code fence は無変更 | 挙動維持 |
| `## Baseline Verification Before Work` | 導入段落を統合。command selection priority・code fence・`status=fail` / `not_run` 規範は無変更 | 挙動維持 |
| `## Fixed Model` / `## Model Routing` | 重複していた model 既定の記述を統合（Opus 5 / GPT-5.5 + medium / risk 時 high / formal gate / host default 注記 / `ultrathink` 不使用 をすべて保持） | 挙動維持 |
| `## Trigger Matrix` / `## Artifact Rule` | 入れ子 bullet をインライン化（**項目は全保持**） | 挙動維持 |
| `## Critical: ...` | 散文の圧縮のみ。停止規律・contract 違反条項・Express Path 例外・Value-Based Scope Narrowing は全保持 | 挙動維持 |
| `## Steps` | 最大の削減源。`brainstorming-steps.md` が正本である詳細（8a / 8b の Why 例、`Gate Status` の bullet、`現状の把握` の重複説明等）を圧縮。SKILL 固有の契約（Entry Intent 永続化、Workflow Fit Check、Pre-HITL Codebase Survey Pack、Architecture Recommendation Gate、Dependency / Runtime Baseline、Summary Brief 4 層、design.md skeleton 必須見出し、Exit Decision 3 経路）はすべて残置 | 挙動維持（例示の削除は §6 F-1 / F-2） |
| `## Output Guidance` | 根拠文（WHY 先頭の理由、session 事例の詳細）を圧縮。停止マーカー・表示順序・回答パターン 3 分類・Sizing 再評価 trigger (a)〜(d) は全保持 | 挙動維持 |
| `## Transition Rules` | 3 択・手順・auto-downgrade 禁止は全保持。文言のみ圧縮 | 挙動維持 |
| `## Rationalization Check` | **表本体は全行無変更**（規範性が高いため目標駆動での削除をしない判断）。導入 1 文のみ圧縮 | 挙動維持 |
| `## Guardrails` | ほぼ全行が locked。無変更 | 挙動維持 |

## 5. `diff` 削除行の全件照合

`diff <archive_path> <candidate_path>` の削除行（件数は §1 旧#21）を 1 件ずつ原本と突き合わせた。分類の件数は §1 旧#22〜旧#24。内訳:

- **圧縮・統合により同内容が新版に存在する**（§1 旧#22）。
- **intra-file duplicate として削除**（§1 旧#23。規範文は同一ファイル内の別節に残存）:
  - Goal の `Workflow Fit Check` → § Steps 7 サブ bullet に残存
  - Goal の `Engineering Baseline Survey / Architecture Recommendation Gate / Dependency / Runtime Baseline / Project Reproducibility Gate`（「完全未調査のまま human check に進めない」を含む）→ § Steps 9 の各 bullet に残存
  - Goal の `Baseline Verification Status` → § Baseline Verification Before Work + § Steps 4 に残存
  - 自律解決の判断基準 の `Subsystem Decomposition Gate` サブ bullet → § Subsystem Decomposition Gate 本節に残存（`separate steering` / `phased single steering` / `first subsystem only` を含む）
  - `Fixed Model` / `Model Routing` の重複行 → 統合先に全項目残存
- **例示・根拠のみの削除**（§1 旧#24）→ §6 の flag 対象。内訳は **正本委譲（F-1: `brainstorming-steps.md` § 8a に残存）/ 単純削除（F-2: 委譲先を持たない。詳細は §6）**。いずれも規範文は残置のため挙動影響なし。

照合中に検出した**規範文の意図せぬ欠落を復元済み**（件数は §1 旧#19）:

1. `Formal Handoff Progress Note` の「worktree 探索や baseline 検証で時間がかかる場合も、この案内を先に出す」（行動規則を根拠文と誤認して削除 → 復元）
2. `Pre-HITL Codebase Survey Pack` の「ユーザーが『既存コードがあるはず』と示した場合」トリガーと `partial` の定義（→ 復元）

`verify` 失敗により逐語復元したアンカー（件数は §1 旧#18）: set2 `Step 3` / set3 `tech-docs-searcher` / set3 `未確認` / set3 `1-2 文` / set3 `requirements review` / set5 `Clarification Loop 停止時` 行 / set5 `一度に聞く量` 行 / set5 `初回 human check` 行 / set5 `gdd-using-git-worktrees` で worktree を解決した後… 行（`重い full suite しかない場合は…` を復元）。

逐語復元により推定トークンは増加した（§1 旧#3 の蒸留後は**復元後**の値）。復元後も `verify` は `ANCHOR_VERIFY_OK: 572 anchors checked, 0 unexpected missing (0 allowed)`。

### 「圧縮・統合により同内容が存在」バケットから個別開示へ移した 2 件（completion-check `completion-20260801-1` の指摘）

上記バケット（§1 旧#22）は件数のみの集計だったが、その中に **規範の強さが変わっていた 2 件**が埋もれていた。いずれもアンカー文字列自体は新版に残っており、`present()` の部分一致では検出できない型（= §3 の照合が構造的に持つ盲点そのもの）。**原本から逐語復元済み**で、復元後の body 行数は 312 行のまま（AC-8 の ≤350 は維持）。

| # | 箇所 | 蒸留で起きた変化 | 対応 |
| --- | --- | --- | --- |
| 1 | § Steps 15 Exit Decision 判定軸 2（原本 L247） | 「AC が測定可能で、**reviewer / 人間が** pass/fail を判定できる粒度か」から判定主体が脱落し、「AC が測定可能で pass/fail を判定できる粒度か」に。**AI 自身が判定できれば可**と読める余地が生まれていた | 原本の文へ逐語復元 |
| 2 | § Steps 11（原本 L232） | 独立文だった「`Design Policy Discussion` で設計方針の候補を整理」が、requirements skeleton に含める**見出し名の一員**へ格下げされ、行為義務が「見出しを置けば充足」と読める形になっていた。同ファイル L34 / L140 / L143 / L144 / L308 が個別の記録義務を残すため実害は限定的だが、総則は失われていた | 原本の独立文へ逐語復元し、skeleton 列挙からは当該見出し名を外した |

## 6. 矛盾 flag

| # | 内容 | 種別 | 扱い |
|---|---|---|---|
| F-1 | § Steps 8a の `**Why:** ある外部 API は組織の表示名を…` 例を削除 | 例示の正本委譲 | `references/brainstorming-steps.md` § 8a に同じ事例が残存。挙動影響なし |
| F-2 | § Steps 8b の `**Why:** ある一覧の投稿機能では環境変数 4 つ + IaC 変更…` 例を削除 | 例示の削除（**委譲ではない**） | `brainstorming-steps.md` § 8b は一般化された根拠のみ保持し この具体例は持たない。`一覧の投稿機能` の事例自体は `gdd-test-driven-development/SKILL.md`（Slack エスケープの例）と `gdd-task-breakdown/SKILL.md`（コンテナデプロイ回数の例）に存在するが、いずれも別論点の `**Why:**` 例であり、削除した内容（環境変数 4 つ + IaC 変更）を持つ箇所は plugin 全体に存在しない。したがって委譲先は無く、単純削除にあたる。原本 archive に保全。挙動影響なし（規範文「以下を `requirements.md` に明記する」は locked のまま残置） |
| F-3 | **per-target トークン目標が未達**（§1 旧#3）。ADR-8 Amendment 1 により per-target トークン目標は失効しており、逐語復元による増加も AC 違反ではない | 目標未達 | design.md Global Constraints「挙動維持が最優先。目標駆動で規範文を削らない」に従い、据え置き・余裕率縮小・scope 外追加蒸留・移送による辻褄合わせのいずれも行わず、未達のまま human check に上げる（design.md D-5 fail-closed） |

## 7. 未達の根拠（F-3 の内訳）

対象成果物の測定値はすべて §1 を参照する。目標由来の値と他タスクの実績は出典を併記する（D-7 決定 1）。

- 蒸留前 body のうち、AC-1 のアンカーで**逐語ロックされる質量が大きい**: `§1 #11 ÷ §1 #2（蒸留前）` = §1 旧#12。`estimated_tokens = ceil(chars/4)` のため、locked だけで `ceil(§1 #11 ÷ 4)` = 3,657 トークンが動かせない。
- 目標を満たすには、`§1「推定トークン」目標列 6,820 → 必要 chars = 6,820 × 4 = 27,280`。free 質量を `27,280 − §1 #11` = 12,654 chars まで落とす必要がある。free 総量は `§1 #2（蒸留前）− §1 #11` = 20,112 chars なので、**必要削減量は 7,458 chars = free 質量の 37.1%**。
- 実際に削除・統合できた free 質量は `§1 #2（蒸留前）− §1 #2（蒸留後）` = 2,866 chars = **free の 14.2%**（locked 行は無変更のため、body chars の減少はすべて free 由来）。残る free 行は大半が「規範文ではないが行動を規定する指示文」であり、削ると挙動が変わる。
- 他対象と同傾向: T-5 実績（`r9-2-requirements-template-audit-20260729.md`）は free 質量のうち非契約と判定できたのが 20.0%、削減率 −7.0%。本対象の削減率（§1 旧#5）も同じ水準に着地した。
- **移送による達成は選ばなかった**。SKILL.md は実行時に `references/brainstorming-steps.md` を参照するため移送しても実コンテキストは減らず、AC-11 が禁じる「見かけの削減」に該当する。加えて `brainstorming-steps.md` は Wave 0 で蒸留済みであり、戻し込みはその判断と矛盾する。

## 8. AC-2 回帰

- `bash tests/validate-plugin.sh` → exit 0
- `python3 -m pytest tests/ -q` → exit 0 / `790 passed, 607 subtests passed`（baseline と同値）
