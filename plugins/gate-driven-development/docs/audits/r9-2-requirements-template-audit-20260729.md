# R9-2 Wave 1 監査シート: requirements-template.md（2026-07-31 実施）

対象: `plugins/gate-driven-development/references/requirements-template.md`（原本 721 行 / 48,166 chars / 推定 12,042 tokens）
着地: **693 行 / 44,779 chars / 推定 11,195 tokens（−28 行 / −3.9%、−3,387 chars、−847 tokens / −7.0%）**
推定トークンは `scripts/lint-runtime-budget.py` の `estimated_tokens()`（`ceil(len(text)/4)`、`len` は Python の文字数）と同一式。
ルーブリック: keep（low freedom 契約）/ rewrite-to-intent（意図へ圧縮）/ delete（重複・歴史的経緯・例示）/ relocate（原本退避で代替）
原本退避先: `docs/references-archive/requirements-template-pre-r9-2-wave1-original.md`（蒸留コミットより前の archive コミット `48677db` で git 管理下）
アンカー分母: `docs/audits/r9-2-requirements-template-anchors.txt`（archive と同一コミットに固定。**925 件**）

## 数値目標の達成状況（本 Wave で唯一 per-target 数値目標を持つ対象）

ADR-8 は AC-6 の充足のため、本ファイルに **`≤702 行` かつ standard profile で追加 `−1,190 トークン`** を割り付けている。

| 目標 | 基準 | 実測（蒸留後） | 判定 |
|---|---|---|---|
| 行数（AC-6 旧#4 の下限要件） | ≤ 702 行 | **693 行**（−28） | **達成**（余裕 9 行） |
| standard 推定トークン（AC-6 旧#6） | 12,042 − estimated_tokens ≥ 1,190 | **11,195**（削減 **847**） | **未達（−343 トークン不足、目標の 71.2%）** |

`lint-runtime-budget.py`（`--quiet` なし）の standard runtime profile 内訳実測:

```
- standard runtime profile: lines=3376, estimated runtime tokens=56721
  - references/requirements-template.md: lines=693, estimated_tokens=11195
- Runtime template budget: express=182/200, standard=799/850
```

**判定: 未達**。RED Evidence Entry 5 の judgment procedure 手順 3（1 回目の差し戻し）に相当する追加削減パスとして、蒸留後の全 soft 行（非フェンス かつ アンカー完全一致でない行、残 13,570 chars）に対し `difflib.SequenceMatcher` で総当たり近似重複検出（閾値 0.55）を再実行したが、**新たな非契約テキストは検出されなかった**。90 文字を超える残 soft 行はすべて規範文（`必ず` / `〜しない` / 写像規則 / 数値・ラベル定義）であり、これ以上の削減は契約文の削除になる。

したがって design.md Global Constraints「挙動維持が最優先。数値目標を先に置かず、規定度監査の結果に従う。目標駆動で規範文を削らない」および D-5 の fail-closed 規定に従い、**(a) バジェット据え置き / (b) 余裕率の縮小 / (c) scope 外ファイルの追加蒸留 のいずれも行わず、AC-6 旧#6 未達を記録して `human_recheck_required` へ回す**。

補足: standard profile 合計は 57,568 → **56,721 トークン**（−847）。ADR-8 が AC-6 充足に必要とした standard 全体 −2,712 トークンに対し、本対象の寄与は 847 にとどまる。S-3 でのバジェット引き下げ可否は、この実測を前提に再計算すること。

## 抽出コマンド列（再実行で同じ分母が再現することを確認済み）

実行 cwd: `plugins/gate-driven-development`（パスが相対のため）。誤った cwd から実行した場合は fail-closed する。

```bash
rm -rf /tmp/r9-2-base-tree && mkdir -p /tmp/r9-2-base-tree
git archive 33cb8aa5f448724ed4510b86d03dcd40af4a9ea8 | tar -x -C /tmp/r9-2-base-tree

python3 docs/audits/r9-2-anchor-tools.py selftest

python3 docs/audits/r9-2-anchor-tools.py extract \
  --base-tree /tmp/r9-2-base-tree/plugins/gate-driven-development \
  --target references/requirements-template.md \
  --archive docs/references-archive/requirements-template-pre-r9-2-wave1-original.md \
  --out docs/audits/r9-2-requirements-template-anchors.txt

python3 docs/audits/r9-2-anchor-tools.py verify \
  --anchors docs/audits/r9-2-requirements-template-anchors.txt \
  --candidate references/requirements-template.md
```

`--expect-empty` は **不要**（5 集合すべて非空: set1=57 / set2=1 / set3=520 / set4=285 / set5=62）。
`--allow-missing` は **使用していない**（承認済み削除が 0 件のため。allow list ファイル自体を作っていない）。

## 保存必須の契約（蒸留後も維持したもの）

アンカー全数照合の分母と結果:

| 集合 | 内容 | 件数 | 蒸留後の欠落 |
|---|---|---|---|
| SET 1 | 見出し行（`^[ \t]*#{1,6} ` 全行。コードフェンス内の擬似見出しを含む） | 57 | 0 |
| SET 2 | `[Ss]tep <数字>` 番号体系 | 1 | 0 |
| SET 3 | 外部被参照文字列（base tree `33cb8aa5` の `tests` / `hooks` / `scripts` / `skills` / `references` / `commands` / `agents` から逆引き） | 520 | 0 |
| SET 4 | コードフェンス内の全行 | 285 | 0 |
| SET 5 | 規範表現・数値閾値を含む行 | 62 | 0 |
| 合計 | | **925** | **0（allowed 0）** |

個別に維持を確認した契約群（すべて verbatim / 本文無改変）:

- **成果物フォーマット定義（最大の契約塊、フェンス 404 行 = 全体の 58.3%）**: `Summary Brief` 4 層テンプレート（一言 / 判断材料 / ズレ確認 / 承認ポイント / Honest Limitations）、`方向性承認` ブロック（自走範囲 / 自走上限 / `Post-PR Completion Scope` / `Post-PR 操作承認` / 人間に戻す条件）、`Trace セクション` の全 12 表（`User-Stated Completion Conditions` / `Completion Condition Trace` / `Post-PR Completion Scope` / `Verification Sanity Check` / `Completion Testability Matrix` / `Implementation Approach Trace` / `Existing Implementation Survey` / `Engineering Baseline Survey` / `Architecture Option Matrix` / `Architecture Drivers` / `Dependency / Runtime Baseline` / `Baseline Compliance Check Plan` / `Architecture Drift Detection` / `Technology Stack Fit Matrix` / `Adopted Technology Stack Trace` / `Implementation Sequence Plan` / `Planned Follow-up Stage Lane` / `Adversarial Requirements Review` / `Plan Direction LLM Review` / `Plan Revision Ledger`）の全表ヘッダ・全プレースホルダ・全 enum 値、`Express requirements.md テンプレート` 全文、`Critical Trace` 形式、`実装方式の選定` 比較表、`Entry Intent` / `Approved Direction` / `Stage Continuity` の 3 テンプレート全文
- **停止規律・fail-closed 規範**: `not_run` は human-check へ進めない停止理由（`partial` との使い分けを含む）、`ambiguous` の場合は fail-closed 停止して state.md を作成しない、Architecture Option Matrix の比較が無いまま CI policy を決めた場合は human-check に進めない、blocking な未確認事実を `unresolved` / `Open Question` へ分離する規則
- **危険操作の承認境界**: `merge / deploy / apply / AWS write` は `Requires explicit operation approval`、**1 操作ごとの明示承認を維持**、`マージして再学習まで` を `PR 作成まで` に丸めない（`Post-PR Completion Scope` の非降格）
- **数値閾値**: 承認ポイント原則 3〜5 件（express は 1-3 件）、方向性承認 1 件必須、Summary Brief 4 層 / quick 3 層、broad change surface の 1〜2 / 3〜7 / 8 ファイル閾値、severity 3 段階（low / medium / high）
- **Status / enum 語彙の定義**: Completion Condition Trace 7 値（`kept` / `refined` / `split` / `deferred` / `dropped` / `added` / `unresolved`）、Completion Testability Matrix 5 値（`testable` / `needs-clarification` / `e2e-required` / `external-evidence-required` / `non-testable-deferred`）、Handling 4 値（`apply-now` / `defer-follow-up` / `human-recheck-required` / `planning-rework-required`）、Re-Architecture 3 段階、`Reuse decision` 5 値、`Completeness` 3 値
- **HITL 圧縮規則 5 本**: 全テスト計画 / 全 dependency 一覧 / 全 Stage 詳細を貼らず、`テスト化確認` / `技術スタック確認` / `Stage Continuity Brief` / `段階連続性` / `ズレ確認` へ圧縮する各規則と、`kept` 行を原則出さない規則
- **段階実装の contract**: `段階実装にする` と書いて `段階実装案` が無い場合は requirements gate で差し戻す、`Stage Continuity Brief` を `段階実装案` の代替にしない、HITL 側で新 Stage を作らず requirements.md を正本にする
- **`Critical Trace` の証明方法 3 値**（`new-red-green` / `code-diff` / `existing-evidence`）と Why（`Existing coverage inspection` へのすり替え防止）
- **自走範囲の glob 判定基準**と `Cumulative Diff Base` の更新規則

## 節別判定

| 節（新行範囲） | 旧行数 | 新行数 | 判定 | 処置と理由 |
|---|---|---|---|---|
| Header（L1-8） | 8 | 8 | keep | 正本分界宣言（所有 / 上位正本 / 参照元） |
| `## HITL Outcome Audit`（L9-12） | 4 | 4 | keep | `match / mismatch / unverified` の記録義務と completion 阻止条件 |
| `## Size-Specific Template Dispatch`（L13-22） | 10 | 10 | rewrite-to-intent | 導入文が直後の 3 項リスト（L17-19）を散文で再掲していたため、再掲部分だけを削除（**−110 chars**）。ディスパッチ表・Why は無改変 |
| `## Summary Brief（4 層構造）`（L23-110） | 88 | 88 | keep | うち 65 行がフェンス内（SET 4）で成果物フォーマット定義。フェンス外は承認ポイントの記入規則（背景 / 変更前 → 変更後 / 3〜5 件）と Honest Limitations の規範。すべて low freedom |
| `## Trace セクション`（L111-427） | 318 | 317 | rewrite-to-intent | **−1 行 / −343 chars**。うち 252 行がフェンス内（全 trace 表の正本）。フェンス外で 2 箇所のみ処置: ① `needs-clarification` / `non-testable-deferred` の再掲 1 行を delete（同節 L383 / L386 に個別定義が verbatim 存在）② `Existing Implementation Survey` bullet から調査範囲列挙と `partial` / `not_run` 定義を削除し、フェンス内 L166 の定義へ pointer 化（当該定義はフェンス内に verbatim 保存されている） |
| `## Express requirements.md テンプレート`（L428-478） | 51 | 51 | keep | うち 35 行がフェンス内。原則 5 bullet と Gate Status 4 設定はすべて契約 |
| `## requirements.md セクション一覧`（L479-577） | 125 | 99 | delete + rewrite-to-intent | **本タスク最大の削減源（−26 行 / −2,502 chars = 削減量の 73.9%）**。項目 6-8 / 9 の一部 / 10-12 / 14-17 の sub-bullet 19 本は、直前の `Trace セクション` 表ヘッダおよび `Trace の運用` bullet の再掲だった（下記「削除行の逐語照合」で全件の残存先を確認済み）。番号付き項目名（＝セクション一覧としての機能）は全件維持し、冒頭に正本 pointer 1 行を追加。項目 31 `Human Check Questions` の sub-bullet 5 本は `Summary Brief` の承認ポイント規則の逐語再掲のため 1 行へ統合。項目 5 の機械可読 schema、項目 9 の必須トリガ語、項目 13 `Critical Trace` 全文（本ファイル内で唯一の定義）、項目 24-30 は無改変 |
| `### 写像の目安`（L578-586） | 9 | 9 | keep | 目的 / スコープ / 品質 / 制約 → Why / What / How well / Constraints の写像。`Constraints` は SET 3 の唯一保有（**flag 3**） |
| `### Examples の扱い`（L587-590） | 4 | 4 | keep | `Examples` を独立セクションにしない規範 |
| `## lightweight design.md skeleton セクション一覧`（L591-617） | 27 | 27 | keep | 16 項目 + 設計抜けパターン 3 チェック。design.md 側の唯一の正本 |
| `## state.md セクション一覧`（L618-636） | 19 | 19 | keep | Gate Status 11 field と「Core field を省略しない」規範 |
| `### Entry Intent テンプレート（正本）`（L637-655） | 19 | 19 | rewrite-to-intent | **±0 行 / −223 chars**。テンプレート（フェンス 7 行）と規則 6 bullet は無改変。末尾 Why の後半（superpowers との比較・「永続化されていなかった」という歴史的経緯）を 1 文へ圧縮。運用上の理由と `/gdd-dev` 参照は保持 |
| `### Approved Direction テンプレート（正本）`（L656-680） | 25 | 25 | keep | テンプレート 17 行（フェンス）+ glob 判定基準 + `Cumulative Diff Base` 更新規則 |
| `### Stage Continuity State テンプレート（正本）`（L681-693） | 14 | 13 | delete + rewrite-to-intent | **−1 行 / −209 chars**。`Plan Revision` の一致義務 1 行を delete（L633 の state.md field 定義に同義文が verbatim 存在）。`Stage Continuity Source` bullet 末尾の quick (express) 記法は L426 の規範文と完全重複のため pointer 化 |

上表は 13 見出し（フェンス外の `##` / `###` 全件）を覆う。SET 1 の 57 件は本表の 13 見出しに加え、フェンス内の擬似見出し 44 件を含む（後者は各テンプレート内部の見出しであり、上表の該当節に含まれる）。

## 判定集計

- **keep: 8 節**
- **rewrite-to-intent: 4 節**（Size-Specific Template Dispatch / Trace セクション / Entry Intent / Stage Continuity State）
- **delete: 2 節に集中**（requirements.md セクション一覧 / Stage Continuity State）
- **relocate: 0**（他 references への移送は行っていない。AC-11 は本タスクの対象外）
- 削減内訳: **−28 行 / −3,387 chars / −847 tokens**（節別実測）
  - `## requirements.md セクション一覧`: −26 行 / **−2,502 chars**（73.9%）
  - `## Trace セクション`: −1 行 / −343 chars（10.1%）
  - `### Entry Intent テンプレート`: ±0 行 / −223 chars（6.6%）
  - `### Stage Continuity State テンプレート`: −1 行 / −209 chars（6.2%）
  - `## Size-Specific Template Dispatch`: ±0 行 / −110 chars（3.2%）
  - 他 9 節は ±0 行 / ±0 chars（本文 1 バイトも変更していない）

## 削除行の逐語照合（T-4 carry-forward の masking 盲点対策）

T-4 impl-gate の carry-forward「`verify` の exit 0 を単独の保存証跡にしない」に従い、`diff <archive> <蒸留版>` の削除行を **全件** 原本と照合した。

削除された行インスタンス: **34**（追加 6）。34 件すべてについて、削除された規範内容の残存先を蒸留版内で機械照合（部分文字列一致）し、**34/34 で残存を確認、欠落 0**。代表例:

| 削除行（要約） | 残存先（蒸留版で verbatim 確認） |
|---|---|
| 項目 6 の USC 保存規則 | `Trace の運用` L398 + フェンス L118-119 |
| 項目 7 の Status 写像規則 | L399（SET 5 hard-locked）+ フェンス `Completion Condition Trace` 表 |
| 項目 8 の Testability 5 フィールド | L400（SET 5 hard-locked、`HITL 前には ... を埋める` の上位集合） |
| 項目 9 の `PR 作成まで` 非降格 / 1 操作ごと承認 | L393 + フェンス `Post-PR Completion Scope` 表 L131 |
| 項目 10 の作り方論点列挙 | フェンス L50（`repo 分割 / import-recreate / 既存再利用 / public-private / CI/CD 方針`） |
| 項目 11 の 5 フィールド | フェンス `Technology Stack Fit Matrix` 表ヘッダ（全 9 列） |
| 項目 12 の記録項目 | フェンス `Adopted Technology Stack Trace` 表ヘッダ（全 6 列） |
| 項目 14 の Stage 記録項目 | フェンス `Implementation Sequence Plan` 表ヘッダ（全 11 列） |
| 項目 15 の Pending Stage 8 項目 | フェンス `Planned Follow-up Stage Lane` 表ヘッダ（全 8 列） |
| 項目 16 の敵対的レビュー 5 観点 | フェンス `Adversarial Requirements Review` 表 5 行 + L423 |
| 項目 17 の `Affected Stage` 明示義務 | L427（SET 5 hard-locked）+ フェンス `Plan Revision Ledger` 表ヘッダ |
| 項目 31 の承認ポイント 5 規則 | L78-L83（`背景` / `変更前 → 変更後` は SET 5 hard-locked） |
| `Route / Ownership Matrix` の例示行 | 直前行 `before / after / owner / flag / rollback を 1 表で見せる` にフィールド列挙が残存 |
| Entry Intent の Why 後半 | 運用理由を 1 文に圧縮して保持（`/gdd-dev` 参照は維持） |
| `Plan Revision` 一致義務 | L633 `` `Plan Revision`（段階計画の最新 revision。`requirements.md` の `Plan Revision Ledger` と一致させる） `` |
| `Stage Continuity Source` の express 記法 | L426（SET 5 hard-locked、同一記法を verbatim 規定） |

照合は個別文字列 40 本の存在検査として実行し、全件 OK（1 件は検査文字列側の引用ミスで初回 FAIL となったが、原本該当行 L78 の存在を `grep` で直接確認して解消）。

### `grep -F` masking の総当たり（advisory）

蒸留後の各非空行を 1 行ずつ削除し、925 アンカーの全包含を再判定した:

| 対象 | 検出されずに削除できる行 |
|---|---|
| SET 5 の規範行 | **1 行** |
| 全非空行（559 行） | **201 行**（36.0%） |

先行対象 `human-check-template.md` の 210/585（35.9%）とほぼ同率。原因も同じで、**フェンス内テンプレートと本文規範が同一文字列（表ヘッダ・enum 値・見出し）を意図的に重複保有する**ためである。含意として、本ファイルでも `verify` の exit 0 は保存証跡として単独では不十分であり、上記「削除行の逐語照合」が唯一の網である（**flag 1**）。本タスクの削除 34 行はすべてこの逐語照合を通している。

## 削減余地の定量根拠（推測ではなく実測）

| 指標 | 蒸留後の実測値 | 意味 |
|---|---|---|
| 非空行 | 559 / 693 | — |
| **hard-locked 行**（SET 1 / 2 / 4 / 5 に行全体が一致し、1 文字でも変えれば `verify` が落ちる行） | **353 / 559 = 63.1%** | 文言の自由度が構造的に存在しない |
| コードフェンス内の行（フェンス記号含む） | 404 / 693 = **58.3%** | 過半が成果物フォーマット定義（原本と同数。1 行も削っていない） |
| soft 行の総文字数（非フェンス かつ アンカー完全一致でない） | 13,570 chars（原本 16,957 → −3,387） | 残る削減余地の理論上限 |
| 残 soft 行のうち 90 文字超 | 55 行 | 全件が規範文（規則 / 写像 / 圧縮ルール / 定義）。近似重複検出（difflib ≥0.55 総当たり）で新規の重複は 0 件 |

結論: 目標の −1,190 トークン（−4,760 chars）は soft 質量 16,957 chars の 28.1% に相当した。実際に非契約と判定できたのは 3,387 chars（20.0%）であり、残り 8.1 ポイント分は契約文（規範 bullet・enum 定義・写像規則）を削らない限り到達できない。**目標駆動で規範文を削らないという Global Constraints を優先し、未達で確定させた。**

## 検証結果

| 項目 | 結果 |
|---|---|
| `selftest`（抽出・照合前に実行） | `SELFTEST_OK: 22 cases passed` / exit 0（R1〜R21 + round-trip） |
| アンカー全数照合（925 件） | `ANCHOR_VERIFY_OK: 925 anchors checked, 0 unexpected missing (0 allowed) in references/requirements-template.md` / exit 0 |
| `diff` 削除行の全件逐語照合 | 削除 34 行インスタンス / 追加 6 行。**34/34 で残存先を確認、欠落 0** |
| `wc -l` | **693**（目標 ≤702: 達成） |
| `lint-runtime-budget.py` standard 内訳 | `references/requirements-template.md: lines=693, estimated_tokens=11195`（削減 847 / 目標 1,190: **未達**） |
| `bash tests/validate-plugin.sh` | exit 0（全 BLOCK チェック OK） |
| `python3 -m pytest tests/ -q` | 790 passed, 607 subtests passed / exit 0（baseline と同値） |

## flag（衝突・注意）

1. **アンカー照合の被覆が弱い**（masking 総当たり 201/559 = 36.0%）。フェンス内テンプレートと本文規範が同一文字列を重複保有する設計に起因する。**本ファイルの将来の変更でも `verify` exit 0 を保存証跡として単独で使ってはならない**。今回の削除 34 行はすべて逐語照合済み。
2. **`## requirements.md セクション一覧` の項目番号が原本時点で重複している**: 14-17（`Implementation Sequence Plan` / `Planned Follow-up Stage Lane` / `Adversarial Requirements Review` / `Plan Revision Ledger`）の直後に再び 15-18（`制約・前提・依存関係` / `影響範囲` / `リスク` / `実装方針`）が始まり、通し番号として破綻している（実質 34 項目が 31 番までの番号で表記されている）。**番号の振り直しは内容変更に当たり R9-2 の承認 scope 外**のため修正せず、原本の欠陥として記録する。
3. **`### 写像の目安` は削除候補として検討したが削らなかった**。「新しい固定スキーマを増やす意図ではなく、既存項目への写像の目安」という背景説明の色が濃く 4 行の対応表しか持たないが、`Constraints` が SET 3（外部被参照）の唯一保有であり、削除には allow list 宣言が必要になる。削っても −145 chars（−36 tokens）で目標到達に寄与しない。「**判断に迷った節は削らない**」原則を優先した。
4. **`Trace の運用` L411 の historical note**（`（session b5af6133: Serena MCP 未接続時に周辺コード探索が行われなかった再発防止）`）は「歴史的経緯」に該当する唯一の残存箇所だが、`再発防止` が SET 3 の唯一保有のため削除に allow list 宣言が必要。−48 chars（−12 tokens）に対し承認済み欠落を 1 件増やす取引が見合わないと判断し、keep とした。
5. **`## HITL Outcome Audit`（L9-11）と `Trace の運用` の重複可能性は未評価**。本節は他 references（`human-check-template.md` / `self-contained-contract.md`）と主題が重なりうるが、**他ファイル側は T-4 で本文無変更が確定しており、本タスクの承認 scope はファイル内蒸留に限られる**ため、cross-file の重複解消は行っていない。references 全体の再編を行う場合の削減余地として記録する。
6. **AC-6 旧#6 未達（−343 トークン）**。本 Wave の references 4 対象の実績は −5.8% / −2.9% / 0% / **−7.0%（本対象）** であり、本対象が最大の削減率を出したうえでなお ADR-8 の割り付け（−9.9% 相当）に届いていない。ADR-8 の割り付けは design.md の「free 行 273 行 / free 質量 4,413 トークン、その 27% を削れば届く」という見積りに基づいていたが、**実測の free 質量は 16,957 chars（4,239 トークン）で見積りとほぼ一致した一方、そのうち非契約と判定できたのは 20.0% にとどまった**（見積りは 27%）。乖離の原因は「free 行＝削減可能」という前提であり、free 行の大半が SET 3 に部分一致するだけの規範文だったことによる。S-3 で AC-6 を再検討する際は、この 20.0% を実績値として使うこと。
