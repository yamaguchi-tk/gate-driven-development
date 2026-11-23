# R9-2 Wave 1 監査シート: human-check-template.md（2026-07-30 実施）

対象: `plugins/gate-driven-development/references/human-check-template.md`（原本 773 行 / 42,562 chars / 推定 10,641 tokens）
着地: **773 行 / 42,562 chars / 推定 10,641 tokens（±0 行 / 0.0%、±0 tokens / 0.0%）— 蒸留可能な非契約テキストが存在しないため、本文は 1 バイトも変更しない**
推定トークンは `scripts/lint-runtime-budget.py` の `estimated_tokens()`（`ceil(len(text)/4)`、`len` は Python の文字数）と同一式。
ルーブリック: keep（low freedom 契約）/ rewrite-to-intent（意図へ圧縮）/ delete（重複・歴史的経緯・例示）/ relocate（原本退避で代替）
原本退避先: `docs/references-archive/human-check-template-pre-r9-2-wave1-original.md`（蒸留コミットより前の archive コミット `16eb559` で git 管理下。現行本文と `diff` バイト同一）
アンカー分母: `docs/audits/r9-2-human-check-template-anchors.txt`（archive と同一コミットに固定。957 件）

**重要な前提（ADR-1）**: 本ファイルは design-gating で Option D（`docs/` へのアーカイブ移動）が却下され、標準経路の必読正本（`skills/gdd-requirements-gating/SKILL.md:281`）として **蒸留対象** に確定している。path 変更・退避は行っていない。

先行 2 対象（`state-machine.md` -5.8% / `phase-progression.md` -2.9%）と同一の判定基準を適用した（矛盾なし）。本対象は先行 2 対象より契約密度が高く、削減率 0% で着地した。**数値目標を先に置かず、規定度監査の結果に従った結果である**（design.md § D-2 は本対象に数値目標を課していない。数値目標があるのは T-5 `requirements-template.md` のみ）。

## 抽出コマンド列（再実行で同じ分母が再現することを確認済み）

実行 cwd: `plugins/gate-driven-development`（パスが相対のため）。誤った cwd から実行した場合は fail-closed する。

```bash
rm -rf /tmp/r9-2-base-tree && mkdir -p /tmp/r9-2-base-tree
git archive 33cb8aa5f448724ed4510b86d03dcd40af4a9ea8 | tar -x -C /tmp/r9-2-base-tree

python3 docs/audits/r9-2-anchor-tools.py selftest

python3 docs/audits/r9-2-anchor-tools.py extract \
  --base-tree /tmp/r9-2-base-tree/plugins/gate-driven-development \
  --target references/human-check-template.md \
  --archive docs/references-archive/human-check-template-pre-r9-2-wave1-original.md \
  --out docs/audits/r9-2-human-check-template-anchors.txt \
  --expect-empty 2

python3 docs/audits/r9-2-anchor-tools.py verify \
  --anchors docs/audits/r9-2-human-check-template-anchors.txt \
  --candidate references/human-check-template.md
```

`--expect-empty 2` を使用（SET 2 `[Ss]tep <数字>` が実測 0 件。ADR-9 に従い事前宣言し、宣言なき空集合が `ANCHOR_EXTRACT_FAILED` になる fail-closed 設計を維持している。selftest R13/R14 が担保）。
`--allow-missing` は 2026-07-30 の本監査時点では **使用していない**（承認済み削除が 0 件のため。allow list ファイル自体を作っていない）。**2026-08-17 の PR-W1 以降はこの前提が変わっており、`--allow-missing docs/audits/r9-2-human-check-template-allowed-missing.txt` を付けないと `verify` は exit 1 になる**（下記「PR-W1 追記（2026-08-17）」を参照。上のコマンド列は 2026-07-30 に実行した実体のスナップショットとして書き換えない）。
本対象は T-3b の Python 実装（`docs/audits/r9-2-anchor-tools.py`）で最初から抽出しており、bash 版（削除済み）の分母や `-v2` への移行は発生していない。

## 保存必須の契約（蒸留後も維持したもの）

アンカー全数照合の分母と結果:

| 集合 | 内容 | 件数 | 蒸留後の欠落 |
|---|---|---|---|
| SET 1 | 見出し行（`^[ \t]*#{1,6} ` 全行。コードフェンス内の擬似見出しを含む） | 53 | 0 |
| SET 2 | `[Ss]tep <数字>` 番号体系 | 0（`--expect-empty 2` で宣言） | — |
| SET 3 | 外部被参照文字列（base tree `33cb8aa5` の `tests` / `hooks` / `scripts` / `skills` / `references` / `commands` / `agents` から逆引き） | 533 | 0 |
| SET 4 | コードフェンス内の全行 | 285 | 0 |
| SET 5 | 規範表現・数値閾値を含む行 | 86 | 0 |
| 合計 | | **957** | **0（allowed 0）** |

個別に維持を確認した契約群（すべて verbatim / 本文無改変）:

- **停止マーカーと停止規律**: `<gdd-stop reason="human-check-waiting">` の末尾必須（無いと autonomous continuation が止まらない）、「requirements.md を確認してください」だけで止めないこと、blocking `Open Questions` が残る場合は `human-check-waiting` に進めないこと
- **成果物フォーマット定義（最大の契約塊）**: `## 🔍 確認` 出力テンプレート全文（L73-418、フェンス内 344 行）— `30秒判断` 8 項目、`承認サマリ`、`判断ポイント`、`選択肢の説明`、`Multiple PR Strategy Options`、`検証計画`、`モデル実行計画`、`まず見るところ`、`Stage Continuity Brief`、`段階実装案`、`LLM 方針レビュー`、`Adversarial Requirements Review`、`人間に戻す主な条件`、`まだ確認できないこと`、`この OK で許可すること / 許可しないこと`、`現在地`、`前提`、`ズレ確認`（完了条件の変換 / テスト化確認 / 既存実装の調査状況 / Engineering Baseline / コードベース健全性確認 / アーキテクチャ提案 / 依存・実行環境 / Project Reproducibility Gate / Baseline Compliance Check / Architecture Drift / 正本と事実の扱い / Workflow Fit Check / Baseline Verification Status / 技術スタック確認 / Architecture Option Matrix / 実装技術スタック / 作り方の重要判断）、`承認ポイント`、`用語の短縮定義`、`参考（任意）` の全見出し・全表ヘッダ・全プレースホルダ
- **必須ルール 20 項（contract 違反条件）**: L426-454 の全行。`Post-PR Completion Scope` の非降格、`Architecture Option Matrix` 必須条件、`既存実装の調査状況` 欠落は contract 違反、未定義 Option ラベル禁止、`検証計画` 必須トリガ語（`no-post` / `score` / `compare` / `runner` / `E2E` / `external evidence`）
- **承認ポイントの 4 要素（欠落禁止）**: `AI の仮決定` / `根拠` / `却下した代替案` / `判断に影響する前提`（1 つでも欠けたら contract 違反）
- **数値閾値**: 一次表示 quick (express) 10 行 / quick (standard) 20 行 / standard 30 行、判断ポイント 1-3 件、承認サマリ 5 行以内、承認ポイント 3〜5 件、`判断ポイント` 3-5 行程度、`Stage Continuity Brief` 3-5 行、gate 数 1 / 3 / 4
- **置換値テーブル 2 種**: 通過予定 gate 数（sizing 3 行）と自走上限（5 行 + 5 bullet の operational safety 規約 = 「1 操作ごとの明示承認」）
- **返答分類の判定基準**: hedge 語彙リスト 10 行、AND 2 条件、ケース別判定表 7 行、再質問テンプレ（フェンス内）、修正指示の 4 分類表 4 行 + 判定順 + 安全側に倒す規則、即再承認の短絡形 3 行、共通の承認後処理 4 step（`Route In Progress=none` クリア忘れの警告を含む）
- **Planning Interrupt Decision Menu 4 択**: `requirements_amendment` / `human-check-waiting` 継続 / 既表示 HITL のみ承認可 / `planning_rework_required` or cancelled
- **含めるべき情報の写像 20 行**: requirements.md / design.md の各情報 → テンプレート位置の対応表

## 節別判定

| 節（行範囲） | 旧行数 | 新行数 | 判定 | 処置と理由 |
|---|---|---|---|---|
| Header（L1-4） | 4 | 4 | keep | 正本分界宣言と「pointer で書き inline 再掲しない」DRY 規約 |
| `## GDD Complexity Budget`（L5-8） | 4 | 4 | keep | 本文 L7 が SET 5 アンカー。`skills/gdd-requirements-gating/SKILL.md:13` と一部重複するが、当該行は 8 項目（skill 側は 7 項目）を持ち上位集合であり、削ると skill 側から参照できる正本が消える（**flag 1**） |
| `## Codex Subagent Delegation Permission`（L9-12） | 4 | 4 | keep | 3 値の明記義務と `Approved Direction` への保存義務 |
| `## Compact First`（L13-27） | 15 | 15 | keep | compact template への一次表示委譲、sizing 別 3 行、Why 1 行、参照 skill 3 件 |
| `## Planning Interrupt Decision Menu`（L28-40） | 13 | 13 | keep | 4 択の route 語彙（`requirements_amendment` / `planning_rework_required` / cancelled）と「未表示の HITL を内部承認扱いにしない」規範 |
| `## 出力テンプレート`（L41-44） | 4 | 4 | keep | 停止マーカー義務 |
| `### 一次表示の原則`（L45-65） | 21 | 21 | keep | 8 項目定義・行数目安・禁止 4 件。すべて low freedom |
| `### 承認後の到達点` + 出力テンプレート本体（L66-421） | 356 | 356 | keep | うち 344 行がフェンス内（SET 4）で成果物フォーマット定義そのもの。冒頭 4 bullet は到達点契約 |
| `## 必須ルール`（L422-423） | 2 | 2 | keep | 見出し（`human-check-waiting` を含む） |
| `### 構造・マーカー`（L424-455） | 32 | 32 | keep | 必須ルール 20 項。番号に重複がある（**flag 2**）が本文は全行契約 |
| `### 承認ポイントの 4 要素（欠落禁止）`（L456-466） | 11 | 11 | keep | 出力テンプレート L399-402 と対応するが、テンプレート側は placeholder、本節は定義。片方だけでは契約が痩せる（**flag 3**） |
| `### 用語の短縮定義`（L467-476） | 10 | 10 | keep | 例示 3 行（L473-475）は削除候補として検討したが、当該例は規則本文が指す「Webhook event 名・プロトコル名」クラスの唯一の具体化であり、L471 の例（`warn` / `offline` / `unknown surface`）は別クラス。**判断に迷ったため削らない**（**flag 4**） |
| `### 通過予定 gate 数の置換値`（L477-488） | 12 | 12 | keep | sizing → gate 数・gate 名の置換テーブルと Why |
| `### 自走上限の置換値`（L489-510） | 22 | 22 | keep | 5 上限 × 進めてよいこと / 止めること + operational safety の 1 操作ごと承認 + Why |
| `### HITL の役割`（L511-542） | 30 | 30 | keep | content 品質ルール 27 bullet。必須ルールと主題が重なる bullet があるが、いずれも「何を出さないか」の追加規範を持ち完全な重複ではない（**flag 5**） |
| `### 承認ポイントの粒度`（L543-550） | 8 | 8 | keep | 変更前 → 変更後の併記義務、1 項 1 判断、3〜5 件 |
| `### 判定ルールの書き方`（L551-557） | 7 | 7 | keep | 4 点（条件 / 見る入力 / 出力 / 不足時）と悪い例・良い例。例は規則の唯一の運用可能な具体化 |
| `### scope 必須項目`（L558-567） | 10 | 10 | keep | 4 カテゴリと blocking Open Questions の進行禁止 |
| `### 承認ポイントの位置関係`（L568-576） | 9 | 9 | keep | `Summary Brief` / `Design Policy Discussion` / 参考の配置契約 |
| `## 含めるべき情報の写像`（L577-606） | 30 | 30 | keep | requirements.md / design.md → テンプレート位置の写像表 20 行。成果物フォーマット定義 |
| `## 具体例`（L607-697） | 91 | 91 | keep | 「過剰な例示」に該当しうる最大候補（91 行）だが、L611-694 の 84 行はすべてフェンス内（SET 4 アンカー）。削除には 80 件超の承認済み欠落宣言が必要で、先行 2 対象（フェンス 83 行中 81 行 verbatim 維持）の基準と整合しない。**削除しない**（**flag 6**） |
| `## 返答分類の判定基準`（L698-701） | 4 | 4 | keep | メインセッション向け分類フローの入口 |
| `### 曖昧返答の検出`（L702-745） | 44 | 44 | keep | AND 2 条件・hedge 語彙 10 行・ケース別判定 7 行・再質問テンプレ。他ファイルに写しが無い唯一の所有 |
| `### 修正指示の 4 分類`（L746-758） | 13 | 13 | keep | 判定順 4 行と安全側に倒す規則 |
| `### 即再承認の短絡形`（L759-773） | 15 | 15 | keep | 短絡形 3 行と共通の承認後処理 4 step |

上表は 25 見出し（フェンス外の `##` / `###` 全件）を覆う。SET 1 の 53 件は本表の 25 見出しに加え、フェンス内の擬似見出し 28 件を含む（後者は出力テンプレートと具体例の内部見出しであり、上表の該当節に含まれる）。

## 判定集計

- **keep: 25 節（全節）**
- **rewrite-to-intent: 0 節**
- **delete: 0 箇所**
- **relocate: 0**（ADR-1 で Option D 却下済み。移送先を持たない）
- 削減内訳: なし（±0 行 / ±0 chars / ±0 tokens）

## 削減不可の定量根拠（推測ではなく実測）

| 指標 | 実測値 | 意味 |
|---|---|---|
| 非空行 | 585 / 773 | — |
| **hard-locked 行**（SET 1 / 4 / 5 に行全体が一致し、1 文字でも変えれば `verify` が落ちる行） | **415 / 585 = 70.9%** | 文言の自由度が構造的に存在しない |
| hard-locked 文字数 | 29,603 / 42,562 = **69.6%** | トークン削減の上限が 30.4% 側にしか存在しない |
| コードフェンス内の行（フェンス記号含む） | 435 / 773 = **56.3%** | 過半が成果物フォーマット定義 |
| soft 行（SET 3 部分一致のみ、原理的には書き換え可能） | 170 / 585 = 29.1% | 下記のとおり実質すべて契約文 |
| soft 行のうち規範マーカー（`必ず` / `禁止` / `〜しない` / `contract 違反` / `進めない` / 数値 / バッククォート付きフィールド名）を **1 つも含まない** 行 | 71 / 170 | — |
| その 71 行の内訳 | 表ヘッダ・表区切り 39、契約語彙の表本文（gate 数表 / 自走上限表 / 写像表 / hedge 語彙 / ケース別判定表 / 4 分類表）24、ラベル行（`例:` / `参照する skill:` 等）4、純粋な背景説明 4（L21 / L37 前半 / L465 / L487） | **非契約テキストは実質 4 行分の散文のみ**。全圧縮しても約 -150 chars = -38 tokens = -0.35% |

結論: 削減率を 1% でも稼ぐには、契約文（必須ルール本文・content 品質ルール bullet・出力テンプレートの表）を削るしかない。先行 2 対象（-5.8% / -2.9%）でも削ったのは重複 bullet と旧形式の例示だけであり、本対象にはその両方が存在しない（フェンス外の重複は `承認ポイントの 4 要素` の 1 箇所のみで、これは placeholder と定義の関係で完全重複ではない）。**S-3 のバジェット引き下げでは本ファイルの寄与を 0 として扱うこと。**

### `grep -F` masking の総当たり（advisory / 本対象では追加の警告あり）

各非空行を 1 行ずつ削除し、957 アンカーの全包含を再判定した:

| 対象 | 検出されずに削除できる行 |
|---|---|
| SET 5 の規範行（87 行） | **2 行**（`### この OK で許可すること / 許可しないこと` が L242 と L643 に重複しており、片方を消してももう片方が残る） |
| 全非空行（585 行） | **210 行**（内訳: SET 3 部分一致のみの行 134 / 表区切り 39 / 他所と重複する見出し 20 / 他所と重複するフェンス行 15 / 上記 SET 5 重複 2） |

先行対象 `phase-progression.md` では SET 5 行の masking 総当たりが 0 件だった。本対象で 2 件出るのは、**出力テンプレートと `## 具体例` が同一見出し・同一表ヘッダを意図的に 2 回持つ**ためである（設計上の重複であり、原本の欠陥ではない）。
含意として、本ファイルでは **アンカー照合だけでは契約保存を保証できない**。今回は本文を 1 バイトも変更していないため実害は無いが、将来この 210 行のいずれかに手を入れる場合、`verify` の exit 0 を根拠にしてはならず、逐語照合が唯一の gate になる（**flag 7**）。

## 検証結果

| 項目 | 結果 |
|---|---|
| `selftest`（抽出・照合前に実行） | `SELFTEST_OK: 22 cases passed` / exit 0（R1〜R21 + round-trip） |
| アンカー全数照合（957 件） | `ANCHOR_VERIFY_OK: 957 anchors checked, 0 unexpected missing (0 allowed) in references/human-check-template.md` / exit 0 |
| 照合器の RED 確認（実アンカー 1 件除去） | fixture（`/tmp/r9-2-t4-fixture/` に plugin_root 構造を再現し、candidate から `### 承認ポイントの 4 要素（欠落禁止）` を除去）に対して `MISSING (set 1)` + `MISSING (set 5)` / `ANCHOR_VERIFY_FAILED: 2 missing anchors` / exit 1 |
| 同 fixture の control（忠実コピー） | `ANCHOR_VERIFY_OK: 957 anchors checked` / exit 0（false-fail でないことを確認） |
| fail-closed 性（archive 不在） | fixture に archive を置かずに `verify` すると `ANCHOR_VERIFY_FAILED: archive original not found (registry-derived)` / exit 1（TARGETS registry からの逆算が効いていることを実測） |
| archive の同一性 | `diff -q references/human-check-template.md docs/references-archive/human-check-template-pre-r9-2-wave1-original.md` → 差分なし |
| `bash tests/validate-plugin.sh` | exit 0（全 BLOCK チェック OK） |
| `python3 -m pytest tests/ -q` | 790 passed, 607 subtests passed / exit 0（baseline と同値） |

契約テスト被参照の実測（本文無変更のため落ちる余地は無いが、分母として記録）: pytest 13 ファイル / 39 箇所（`test_hitl_trace_contract.py` が 17 箇所で最多）+ `tests/checks/` の 3 スクリプト（`existing-code-reading-lint.sh` / `lint-scripts-functional.sh` / `skill-body-budget.sh`）。

## flag（衝突・注意）

1. **`## GDD Complexity Budget` は `skills/gdd-requirements-gating/SKILL.md:13` と主題が重複する**。ただし本ファイル側は 30秒判断を **8 項目**（`変更予定ファイル（WHERE）` を含む）、skill 側は **7 項目**（WHERE なし）と規定しており、内容が一致していない。本ファイル側が上位集合のため keep したが、**2 つの正本が 8 項目 / 7 項目でずれているのは原本時点で既に存在する不整合**である。R9-2 の承認 scope（蒸留）を超えるため本タスクでは修正せず flag として記録する。
2. **必須ルール（L424-455）の番号が原本時点で重複している**: `8` が 2 回（L433 / L434）、`11` が 2 回（L437 / L445）、`12` が 3 回（L438 / L439 / L446）、`13` が 2 回（L440 / L447）。連番として読むと 20 項ではなく実質 24 項ある。**これらの行はすべて SET 5 / SET 3 アンカーであり、番号を振り直すとアンカーが落ちる**。また番号の振り直しは内容変更に当たり承認 scope 外。原本の欠陥として記録し、修正しない。
   追記（2026-08-16, PR-W1）: 本 audit の flag 2（「番号を振り直すとアンカーが落ちる・R9-2 の承認 scope 外」）は、PR-W1 の AC-W2-6 として人間が明示承認し、1〜26 の連番へ振り直した。過去のスナップショット自体は書き換えない。
3. **`承認ポイントの 4 要素` の二重定義**（テンプレート L399-402 と規則節 L460-463）。テンプレート側は出力用の placeholder（`<選んだ案を 1 行>` 等）、規則節側は要素の意味定義。文面が異なるため「重複説明」として削除する条件を満たさない。逐語照合で「重複が残っている」と指摘されうる箇所として明示する。
4. **`### 用語の短縮定義` の例示 3 行（L473-475）は唯一の削除候補だったが削らなかった**。理由は本文に記載のとおり（規則が指す「技術用語」クラスの唯一の具体化であり、L471 の例は別クラス）。仮に削っても -3 行 / -0.4% にしかならず、「判断に迷った節は削らない」原則を優先した。
5. **`### HITL の役割` の 27 bullet は必須ルールと主題が重なる**（例: 原本 L529 と必須ルール 11、原本 L530 と必須ルール 7、原本 L521-523 と必須ルール 17-18。**この番号は PR-W1 の採番振り直し後（1〜26）の値に更新済み**。振り直し前は順に 10 / 7 / 12-13 だった）。いずれも「何を出さないか」「どこに逃がすか」の追加規範を持ち、片方を消すと規範が痩せるため keep した。将来 references 全体の再編を行う場合、この節と必須ルールの統合が最大の削減余地（推定 -15〜20 行）だが、**必須ルール本文の書き換えを伴うため R9-2 の承認 scope 外**である。
6. **`## 具体例`（91 行）を残した判断**。「過剰な例示」の定義には最も近いが、84 行がフェンス内 SET 4 アンカーであり、削除には 80 件超の `--allow-missing` 宣言が必要になる。先行 2 対象ではフェンス内削除は 2 行（承認済み・上位互換の例が別に存在する場合のみ）に留めており、本対象で 84 行を一括削除するのは基準の不整合になる。また `docs/NON_ENGINEER_HITL_GUIDE.md` 等の非エンジニア向け導線が具体例を前提にしている可能性があるため、削除の影響評価には別途調査が必要。
7. **アンカー照合の被覆が本対象では弱い**（上記 masking 総当たりの節）。585 非空行のうち 210 行は 1 行削除しても `ANCHOR_VERIFY_OK` に倒れる。原因は出力テンプレートと `## 具体例` が同一見出し・同一表ヘッダを意図的に 2 回持つ設計。本タスクでは本文無変更のため実害なしだが、**本ファイルの将来の変更では `verify` exit 0 を保存証跡として単独で使ってはならない**。
8. **tasklist.md の「契約テスト被参照 15 本」と実測が一致しない**。実測は pytest 13 ファイル（39 箇所）+ `tests/checks/` 3 スクリプト = 16 ファイル。design.md の「15 本」がどの数え方（ファイル数 / テストメソッド数 / 特定時点の値）かは特定できなかった。本タスクの判定には影響しない（本文無変更）が、S-3 で参照数を根拠にする場合は数え方を明示すること。
9. **削減率 0%**。先行 2 対象（-5.8% / -2.9%）が示した「契約密度が高いほど削減率が下がる」傾向の極値。本 Wave の 4 references（合計 3,032 行）で本ファイルが 773 行（25.5%）を占めるため、**Wave 全体の削減率見込みは本ファイルの寄与を 0 として再計算する必要がある**。

## PR-W1 追記（2026-08-17）: 無条件必須の撤去に伴う承認済み文言変更 2 件

PR-W1 の `AC-W2-2`（人間が明示承認）で、必須ルール 20（`LLM 方針レビュー`）と 21（`Adversarial Requirements Review`）の末尾から旧規範「`not_applicable` の場合も…欄自体は省略しない」を撤去し、T-8 が 2 正本へ入れたのと同じ語「`not_applicable` の場合は HITL から欄ごと省略してよい（判定結果と理由は requirements.md に必ず記録する）」へ書き換えた。

当該 2 行は T-6 の採番変更（旧 15 → 新 20 / 旧 16 → 新 21）で既に `kind: moved` として allow list に宣言済みだったが、本変更で**本文そのものが変わる**ため `kind: replaced` へ移し、`replacement` に現行の全文を逐語で記録した。類似度は 0.865 / 0.808（閾値 0.8）。

判定結果と理由を `requirements.md` に残す義務は維持しており（受け皿は T-9 Step 2c で `references/requirements-template.md` に新設）、保護の純減ではない。

> **本ファイル内の `T-nn`（作業単位）/ `AC-Wn-n`（受入条件）は PR-W1 の識別子で、その定義は作業ブランチの steering artifact にのみ存在する**（GDD の運用上 `.steering/` は main に含めない）。以下の各節は、識別子を解決できなくても内容が読めるよう要点を自己完結で書いている。

## PR-W1 追記（2026-08-17）: 承認ポイント 6 要素化に伴う承認済み文言変更 3 件

PR-W1 の `AC-W2-1`（人間が明示承認）で、承認ポイントの必須要素を 4 → 6 に増やした（`この案を選ぶと次に何が起きるか` / `無回答時のデフォルト` を追加）。これに伴い次の 2 アンカー（SET 1 / SET 5 に重複計上され verify 上は 3 件）が MISSING になる。

| アンカー | 置換後 |
|---|---|
| `### 承認ポイントの 4 要素（欠落禁止）` | `### 承認ポイントの 6 要素（欠落禁止）` |
| `各承認ポイントは必ず以下の 4 要素を揃える。1 つでも欠けたら contract 違反:` | `各承認ポイントは必ず以下の 6 要素を揃える。1 つでも欠けたら contract 違反:` |

**上記「採番変更に伴う承認済みアンカー移動 16 件」との性質の違い**: 16 件は「本文は逐語で現存し、行頭 prefix だけが変わった移動」だった。本 3 件は **`4 要素` → `6 要素` という規範内容そのものの更新**であり、旧文言は意図的に存在しなくなる。ただし要素は 4 件から 6 件へ**増えて**おり、規範が痩せたわけではない（削除ではなく追加）。

このため allow list の `reason` でも両者を明示的に区別している。allow list の総数は 16 → 18 件（verify 上の allowed は 19）。**これは T-7 時点のスナップショット**であり、現在の総数と内訳は下記 §「allow list の内訳（機械集計。手で数えない）」を正本とする（T-9 で `moved` 2 件が `replaced` へ移り、`pointerized` 1 件が加わっている）。

### allow list の `kind` 拡張（T-7 remediation）

`reason` の日本語だけで両者を区別すると機械検査できない。当時新設した `tests/test_r9_2_anchor_verify_contract.py`（**このファイルは PR-W1a で PR-W5 へ退避したため現在は存在しない**。下記 `## PR-W1a 追記（2026-08-17）: R9-2 照合の配線を PR-W5 へ退避した` を参照）は「行頭 prefix を除いた本文が逐語現存すること」を全エントリに要求していたため、本 3 件（`4 要素` → `6 要素` の文言変更）では成立せず fail する。**この test を緩めると T-6 で塞いだ fail-open が戻る**ため、緩めずに種別を持たせた。

allow list の各エントリに必須フィールド `kind` を追加した（`schema_version` は 1 のまま。`r9-2-anchor-tools.py` は `anchor` / `reason` しか読まず未知キーを無視するので、照合器側の互換は保たれる）。

| kind | 意味 | contract test が要求する逐語証跡 |
|---|---|---|
| `moved` | 行頭 prefix だけが変わった移動（T-6 の 16 件） | 行頭 prefix を除いた**旧本文が現存**すること |
| `replaced` | 本文そのものの承認済み書き換え（本 3 件） | `replacement` を宣言し、**旧本文が非現存** + **置換後テキストが現存** + 両者の類似度 >= 0.8 |

2 種別は**排他**である（`moved` は旧本文の現存を、`replaced` は非現存を要求する）ため、種別を選び直して assertion を回避することはできない。`kind` の欠落・未知値も fail させる。「消しただけ」は `replacement` が現存しないため落ち、「無関係な既存行を `replacement` に据える」は類似度で落ちる。したがって **allow list にエントリを書き足すだけで契約行を消せる経路は依然として存在しない**（= **正本ファイルを無改竄のまま allow list だけを書き換える弱い脅威モデルでの話**。正本ファイルと allow list を同時に書き換える強い脅威モデルについては下記 §「変異検証 2」を参照。PR-W1 の意思決定のとおり、契約内容の保存は最終的に `reason` に対する人手レビューが担う）。

閾値 0.8 の根拠（実測）: 本 2 エントリの旧本文と置換後テキストの `difflib.SequenceMatcher` 比は 0.954 / 0.978。一方、同ファイル内で最も紛らわしい無関係行との比は 0.629 / 0.358。契約行の半分を落とす部分削除は比 ~0.66 になるため、0.8 は「同一契約行の改稿」と「別物・部分削除」を分離する。

変異検証（9 変異すべてで当該 test が FAILED、復元後 passed を実測）:

| # | 変異 | 結果 |
|---|---|---|
| M1 | `moved` の旧本文を正本から削除 | FAILED |
| M2 | `replaced` の置換後テキストを正本から削除（消しただけ） | FAILED |
| M3 | `replacement` を無関係な既存行にすり替え | FAILED |
| M4 | `kind` フィールドを削除 | FAILED |
| M4b | `kind` に未知値を宣言 | FAILED |
| M5 | `moved` を `replaced` と誤宣言（旧本文が現存） | FAILED |
| M6 | `replaced` を `moved` と誤宣言（旧本文が非現存） | FAILED |
| M7 | 契約行を部分削除し truncate 版を `replacement` 宣言 | FAILED |
| M8 | `replaced` なのに `replacement` 未宣言 | FAILED |

test 関数名は `test_allowed_missing_bodies_are_still_present` → `test_allowed_missing_entries_are_verbatim_backed` に改名した（本文現存を全件に課す前提が種別依存に変わったため）。既存 16 件は `kind: moved` を付与しただけで、要求する assertion は T-6 時点と同一である（意味は変えていない）。

## PR-W1 追記（2026-08-17）: 一次表示バジェットの正本ポインタ化 1 件

PR-W1 の `AC-W2-5`（数値の正本 1 箇所。人間が明示承認）で、`§ 承認ポイント` 直後の一次表示バジェット行から裸数値 `10` / `20` / `30` を撤去し、`scripts/lib/hitl_budget.py` の `PRIMARY_SURFACE_MAX_LINES` を指す表現へ移した（T-9 Step 3b。T-7 Step 2b が compact 側に入れたのと同じ言い回し）。旧文の `standard 30 行` は正本の値と食い違っており、ポインタ化でこのズレも解消している。

当該行は SET 5 の 1 アンカー（重複計上なし）で、置換により MISSING 1 件になる。

### なぜ `kind: replaced` にできなかったか

`replaced` は旧本文と `replacement` の `difflib.SequenceMatcher` 比 >= 0.8 を要求する。しかし本変更は **旧本文 201 chars のうち裸数値を含む 82 chars のスパンを取り除く** ことそのものであり、比は構造的に 0.8 に届かない（**実測 0.614**）。文言側で寄せる調整を 4 案実測しても **0.643 / 0.644 / 0.652 / 0.709** が上限で、原文を多く残す方向の調整は `AC-W2-5`（裸数値の撤去）と正面から矛盾する。閾値の再設定は PR-W1 の意思決定で禁止されているため、**閾値ではなく保証の側を差し替えた**。

### `kind: pointerized` が要求する逐語証跡

| # | 条件 | 何を防ぐか |
|---|---|---|
| 1 | 旧本文が非現存 / `replacement` が現行ファイルに逐語現存 | 消しただけ。`moved` との取り違え |
| 2 | `removed` が旧本文にちょうど 1 回現れる連続スパン | スパン宣言の曖昧化 |
| 3 | `pointer_clause` が `replacement` にちょうど 1 回現れる連続スパン | 同上 |
| 4 | `旧本文.replace(removed, pointer_clause) == replacement`（完全再構成） | **宣言スパン以外の 1 文字の変更もすべて**。スパン外の末尾切り詰めも、スパン外の意味反転もここで落ちる。**スパンの内側は防げない**（下記 § `replaced` の既知の穴に対する強度 / 穴 4） |
| 5 | スパンを除いた残余に照合器 SET 5 の規範表現が残る | 行全体を `removed` に宣言して条件 4 を自明化する経路（= 契約行の丸ごと差し替え） |
| 6 | `removed` に数値リテラルが 1 つ以上あり、その各々が `pointer_clause` に再掲されていない | 値の移送ではない書き換えの流用。正本 1 箇所の破壊 |
| 7 | `pointer_path` / `pointer_symbol` が `pointer_clause` に逐語で現れ、当該ファイルが実在し、当該シンボルがそのファイルに逐語で存在する | dangling pointer（正本を指していないポインタ化） |

条件 5 の規範表現は照合器 `docs/audits/r9-2-anchor-tools.py` の `NORMATIVE_RE` を import して使う（正本を 2 箇所に書かない）。本エントリの残余は `一次表示の` + `を超える場合は、情報を削るのではなく、詳細を…だけを残す。` で、規範本体（`超`）がそのまま残る。

3 種別は排他である。`pointerized` は旧本文の非現存を要求するので `moved` とは両立せず、`replaced` の類似度条件で落ちたエントリを `pointerized` へ付け替えても条件 4〜7 で落ちる（逆も同様）。

### `replaced` の既知の穴に対する強度（2026-08-17 design-gating D9 の独立変異検証で訂正）

> **⚠️ 訂正前の記述は撤回済み**。本節は当初「`pointerized` は `replaced` の既知の穴 2 件を**構造的に塞ぐ**」「穴 1 は条件 4 で **FAILED**」「穴 2 の逃げ道は条件 4 / 5 で **FAILED**（逃げ道は 2 つ）」と書いていたが、D9 が **正本ファイルと allow list を同時に書き換える強い脅威モデル**で独立に変異させた結果、**いずれも成立しない**ことを実測した。訂正後の正本は本ファイルの「変異検証 2（正本と allow list の同時改竄）」と「穴 4」の記述である（初出時の「構造的に塞ぐ」という主張は撤回済み）。

`pointerized` は `replaced` より「強い」のではなく、**保証の向きが違う（incomparable）**。塞がるのは **宣言スパンの外側の改変だけ**であり、穴 1（末尾切り詰め）も穴 2（意味の反転）も **スパンの内側に移せば通る**。正確には「**規範表現がすべて `removed` スパンの内側にある行に限り塞がる**」— 規範表現が 1 つでもスパンの外側に残っていれば条件 5（非退化）が満たされてしまうため、義務本体を丸ごと含む大スパンの除去が通る。**「`pointerized` なら塞がっている」と一般化しないこと**（同型の n=1 一般化を PR-W1 内で 3 度繰り返している）。

| 穴 | `replaced` での挙動 | `pointerized` での挙動（D9 実測） |
|---|---|---|
| 穴 1: 末尾切り詰め | 残 75% で比 **0.855** >= 0.8 のため通る | **スパン外**の切り詰めは条件 4（完全再構成）で **FAILED**。**スパン内なら通る** — 規範表現が行頭側にある行では除去率 **69.7%** / 旧本文比 **0.3497** の末尾除去が **ACCEPTED**（`replaced` の許容幅「残 67% まで」**より広い**） |
| 穴 2: 意味の反転 | `情報を削るのではなく` → `情報を削ってよく` は比 **0.981** で通る | **スパン外**の反転は条件 4 で **FAILED**、スパンを伸ばして規範表現を飲み込む経路は条件 5 で **FAILED**。ただし**逃げ道は 3 つ目がある** — `removed` を 1 文字も伸ばさず `pointer_clause` の内側に規範反転文を同梱する経路が条件 1〜7 をすべて満たして **ACCEPTED**（旧本文比 **0.610**。同じ改稿を `replaced` で宣言すれば 0.8 未満で弾かれる） |

穴 3（宣言した anchor が照合器の照合対象から外れる）は `pointerized` でも変わらない。照合器 `AllowList.load` は `anchor` と `reason` しか読まないため、**`kind` を解釈するのは契約テストだけ**という責任分界も変わらない。

**穴 4（PR-W1 の design review で新規に判明。`pointerized` が保証しない事項の 4 件目）**: 条件 4 の等式が保証するのは「**変更が 1 スパンに閉じている**」ことだけで、**そのスパンの大きさにも中身にも上限が無い**。条件 5（非退化）は残余に規範表現が 1 つ残ることしか要求せず、条件 7 の「ポインタの実在」は substring 検査であって symbol 解決ではなく、条件 6 の数値非再掲は綴り一致検査である。したがって **`pointerized` に載せれば契約内容が保存される、わけではない**。内容の保存は穴 1〜3 と同じく **allow list の `reason` に対する人手レビューが担う**（PR-W1 の意思決定）。**機構側の追加ガードは入れない**（PR-W1 の意思決定 — 自然な案「`pointer_clause` に規範表現を含めない」「`pointer_clause` の規範表現は `removed` の部分集合」は、**現行の唯一の正当エントリを自分自身で弾く**ことを D9 が実測した）。

### 変異検証 1: 弱い脅威モデル（allow list だけを改竄）— 16 変異すべて FAILED、復元後 3 passed を実測

隔離コピー上で 1 変異ずつ適用し、pytest の failing assertion まで確認した。**本表は「正本ファイルは無改竄のまま allow list だけを書き換える」脅威モデルの結果**であり、下の「変異検証 2」（正本ファイルと allow list を同時に書き換える強い脅威モデル）とは前提が違う。**2 表を混ぜて「全変異が FAILED」と読まないこと**。

| # | 変異 | 落ちた assertion |
|---|---|---|
| M1 | 契約行を正本から削除（宣言は残す） | `置換後テキストが現行ファイルに存在しない` |
| M2 | `removed` に行全体を宣言して条件 4 を自明化 | 条件 5 `残余に規範表現が 1 つも残っていない` |
| M3 | `replacement` を無関係な既存行にすり替え | 条件 3 `pointer_clause が 1 回現れない` |
| M4 | スパン外（規範本体）の意味を反転し `replacement` も揃える | 条件 4 `宣言スパン以外が変わっている` |
| M5 | `removed` を伸ばして残余から規範表現を消す | 条件 5 |
| M6 | `pointer_clause` に除去済みの数値を再掲 | 条件 6 `除去した数値がポインタ節に再掲されている` |
| M7 | 存在しない正本ファイルを指す | 条件 7 `pointer_path のファイルが実在しない` |
| M8 | 実在ファイルだが存在しないシンボルを指す | 条件 7 `dangling pointer` |
| M9 | 末尾 25% を切り詰め `replacement` も揃える（`replaced` なら比 0.855 で通る） | 条件 4 |
| M10 | `pointerized` → `moved` へ付け替え | `moved` の本文現存 |
| M11 | `pointerized` → `replaced` へ付け替え | 類似度 `ratio=0.614 < 0.8` |
| M12 | 既存 `replaced` エントリを `pointerized` へ付け替え | 条件 7 `pointer_path が pointer_clause に現れない` |
| M13 | `removed` フィールドを削除 | 必須フィールド宣言 |
| M14 | `pointer_path` / `pointer_symbol` を削除 | 必須フィールド宣言 |
| M15 | 値の移送ではない書き換えを `pointerized` として宣言 | 条件 6 `removed に数値リテラルが 1 つも無い` |
| M16 | `kind` に未知値（`condensed`）を宣言 | `kind` 値域 |

### 変異検証 2: 強い脅威モデル（正本ファイルと allow list を同時に書き換える）— 11 変異中 4 件が **ACCEPTED**

allow list 機構が本来想定している脅威は「正本ファイルと allow list の両方を書き換える」側である。design-gating D9 は同じ `_assert_pointerized` を直接駆動する独立ハーネスでこの脅威モデルの 11 変異を実測し、**4 件が ACCEPTED（= 機構をすり抜ける）**ことを確認した。**上の変異検証 1 の FAILED 一覧とは分けて読むこと**。

| # | 変異 | 旧本文との比 | 結果 | すり抜ける理由 |
|---|---|---|---|---|
| B1 | `pointer_clause` に規範反転文を同梱（`行数の上限は撤廃してよい。…`）。`removed` は無改変 | **0.610** | **ACCEPTED** | 条件 4 の等式は「変更が 1 スパンに閉じている」ことしか見ず、**スパンの中身を見ない**。同じ改稿を `replaced` で宣言すれば 0.610 < 0.8 で弾かれる（**この 1 件が「incomparable」の決定的根拠**） |
| B2 | `pointer_clause` を散文ゼロの `` `path` `symbol` `` へ縮約（文が壊れる） | 0.638 | **ACCEPTED** | 同上 |
| B3 | 無関係な実在ファイル・実在文字列を指す（`references/human-check-template.md` の `禁止` を `pointer_path` / `pointer_symbol` に宣言） | 0.654 | **ACCEPTED** | 条件 7 の「ポインタの実在」は **substring 検査であって symbol 解決ではない**ため原理的に弾けない |
| C2 | `30` → `三十` の綴り替えで数値を再掲 | 0.650 | **ACCEPTED** | 条件 6 の数値非再掲は**綴り一致検査**である |

同じ脅威モデルで REJECTED だった 7 件（対照）: A1 `removed`=行全体（0.136 / 非退化）/ A2 先頭 5 文字以外すべて（0.160 / 非退化）/ A3 先頭〜規範開始（0.574 / 非退化）/ A4 規範本体のみ（0.595 / 数値リテラル 0）/ A5 `30 行を超える`〜末尾（0.507 / 非退化）/ C1 数値 `10 / 20 / 30` の逐語再掲（0.677 / 条件 6）/ C3 `10` を含む `100` を clause に置く（0.663 / 条件 6 の過検知側）。したがって **fail-open は無条件には存在しない**（等式・非退化・数値・ポインタの各条件はいずれも実際に発火する）が、**スパンの内側は無制約**である。

### allow list の内訳（機械集計。手で数えない）

allow list の総数は 18 → 19 件。**内訳は `moved` 14 / `replaced` 4 / `pointerized` 1**。T-9 Step 2b が必須ルール 20 / 21 の本文を書き換えたことで、`kind: moved` として宣言済みだった 2 件が `kind: replaced` へ移ったため（`moved` 16 − 2 = 14 / `replaced` 2 + 2 = 4）。

**訂正前の「`moved` 16 / `replaced` 2 / `pointerized` 1」は誤り**（Step 2b の kind 移動を反映していなかった。PR-W1 の意思決定記録（`pointerized` の保証範囲を撤回・訂正した記録）の (c) と一致）。同じ数え違いを繰り返さないため、**この内訳は目視で数えず次のコマンドで機械集計する**（cwd は `plugins/gate-driven-development`）:

```bash
python3 -c "import json,collections; d=json.load(open('docs/audits/r9-2-human-check-template-allowed-missing.txt',encoding='utf-8')); e=d['allowed_missing']; print(len(e), collections.Counter(x['kind'] for x in e))"
```

実測（2026-08-17）: `19 Counter({'moved': 14, 'replaced': 4, 'pointerized': 1})`。同一コマンドを `git show 49ae1ca:` 経由の同ファイルにも適用して同値であることを確認済み（= 導入時点から 14 / 4 / 1 であり、記録側だけが誤っていた）。

verify は `ANCHOR_VERIFY_OK: 957 anchors checked, 0 unexpected missing (20 allowed)` / exit 0（allowed が 20 になるのは見出しアンカー 1 件が SET 1 と SET 5 に重複計上されるため。理由は design.md §10-2 § エントリ数と allowed 数がずれる理由）。

## PR-W1 追記（2026-08-17）: 採番変更に伴う承認済みアンカー移動 16 件

本節は 2026-07-30 の監査結果を書き換えるものではなく、その後の承認済み変更が分母（957 アンカー）に与えた影響の追記である。

### 何が起きたか

PR-W1 の `AC-W2-6`（flag 2 の是正。人間が明示承認）で `### 構造・マーカー` の必須ルール採番を 1〜26 の連番一意へ振り直した結果、**SET 5（規範表現・数値閾値を含む行）の 16 アンカーが行頭 prefix だけ変わって照合に失敗する**状態になった。`present()` は部分一致だが正規化を行わないため、`8. ` → `9. ` のような prefix 変更でも行全体のアンカーは MISSING になる。

- 内訳: 旧 8→9 / 9→10 / 10→11 / 11→12 / 11→16 / 12→13 / 12→14 / 12→17 / 13→18 / 14→19 / 15→20 / 16→21 / 17→22 / 18→23 / 20→25 の 15 件 + `ベースライン検証` 節配下のネスト bullet → 独立項目 26 への昇格 1 件 = 計 16 件
- SET 1 / 3 / 4 への影響は 0 件（見出し・外部被参照文字列・フェンス内行は不変）
- **行頭 prefix を除いた本文は 16 件すべて逐語で現存する**（実測。契約の削除ではない）

flag 2 の「番号を振り直すとアンカーが落ちる」という 2026-07-30 時点の予測は正しかった。R9-2 の承認 scope 外だった振り直しを PR-W1 で人間が承認したため、承認済み変更として allow list に宣言する。

### 対処

`docs/audits/r9-2-human-check-template-allowed-missing.txt`（`schema_version: 1`）を新設し、16 件を `allowed_missing` として宣言した。各エントリの `reason` に旧番号 → 新番号を記録している。

```bash
python3 docs/audits/r9-2-anchor-tools.py verify \
  --anchors docs/audits/r9-2-human-check-template-anchors.txt \
  --candidate references/human-check-template.md \
  --allow-missing docs/audits/r9-2-human-check-template-allowed-missing.txt
```

実測: `ANCHOR_VERIFY_OK: 957 anchors checked, 0 unexpected missing (16 allowed)` / exit 0。

**分母（`r9-2-human-check-template-anchors.txt`）は書き換えていない。** 分母は base commit `33cb8aa5` の原本から `extract` で再現される値であり、原本は変わっていないため手で新採番へ書き換えると `extract` の再現性（本シート冒頭の再実行性）が壊れる。承認済みの変更は allow list 側で宣言する、というのが本ツールの設計（ADR-10 の allow list = パース済みリスト 1 本 / `declared == used` の集合等価）である。

### allow list が開ける穴と、その塞ぎ方

allow list に載せた 16 行は、以降 `verify` の照合対象から外れる。**本文（番号 prefix を除いた部分）が後から削除されても `verify` は exit 0 のまま通る**。これは flag 7（本ファイルではアンカー照合の被覆が弱い）と同型の fail-open である。

そこで `tests/test_r9_2_anchor_verify_contract.py` を新設し、次の 3 点を pytest で固定した（**このファイルは PR-W1a で PR-W5 へ退避したため現在は存在しない**。下記 `## PR-W1a 追記（2026-08-17）: R9-2 照合の配線を PR-W5 へ退避した` を参照）。

1. `r9-2-anchor-tools.py selftest` が exit 0
2. `human-check-template.md` の `verify`（allow list 付き）が exit 0
3. **allow list の全エントリについて、`kind` に応じた逐語証跡が現行ファイルに存在する**（allow list が開ける穴を塞ぐ。`kind` は T-7 remediation で追加。上記「allow list の `kind` 拡張（T-7 remediation）」を参照）

番号を元に戻した場合は `verify` の条件 7（`declared == used`）が stale 宣言として exit 1 になるため、allow list が黙って腐ることもない。

### 照合器の配線について

`docs/audits/r9-2-anchor-tools.py` は CHANGELOG（`## R9-2 Wave 1` の残課題）に記載のとおり `tests/` / `scripts/` / `.github/` のいずれからも呼ばれておらず、本 F-1 が 37 check / pytest すべて緑のまま通過した直接の原因である。PR-W1 では **本 PR が編集した `references/human-check-template.md` 1 対象だけ** を上記 pytest で配線した。

残る 7 対象を同じ pytest に載せることは **本 PR では行わない（Non-Goal）**。理由は実測にもとづく:

| 対象 | main（PR-W1 適用前）での `verify` |
|---|---|
| `references/state-machine.md` | `FAILED: 1 missing` |
| `references/requirements-template.md` | `FAILED: 2 missing` |
| `references/phase-progression.md` | `FAILED: 1 missing`（allow list v2 適用後） |
| `skills/root-cause-investigation/SKILL.md` | `FAILED: 45 missing` |
| `skills/gdd-writing-skills/SKILL.md` | `OK` |
| `skills/gdd-systematic-debugging/SKILL.md` | `OK` |
| `skills/gdd-brainstorming/SKILL.md` | `OK` |
| `references/human-check-template.md` | `OK`（PR-W1 で 16 件が MISSING 化 → allow list 宣言で `OK` に復帰） |

`main` の時点で 4 対象・計 49 件が既に MISSING であり、これは PR-W1 が作った退行ではない（R9-2 Wave 1 以降の各 PR が原本を編集した結果の未宣言 drift）。49 件それぞれについて「承認済み変更として allow list へ宣言する / 契約損失として復元する」を判断するのは PR-W1 の AC の範囲外であり、要件追加になる。既知 fail を expected として test に焼き込むのは ADR-10 が排除した fail-open パターンそのものなので採らない。

- **Non-Goal owner**: GDD plugin owner（`yamaguchi-tk`）。後続 PR で 49 件を triage し、全 8 対象を 1 つの check へ配線する
- CHANGELOG の推奨は「`tests/checks/` から呼ぶこと」だが、本 PR では pytest 側に置いた。`tests/checks/` への追加は canonical check 数（37）と `tests/test_validate_plugin_check_inventory.py` の `CANONICAL_CHECK_NAMES` / ヘッダー合計の同時変更を伴い、AC-W2-6 の検証証跡が参照している「37 check」の分母を動かすため。全 8 対象を配線する後続 PR で `tests/checks/` へ移すのが妥当

## PR-W1a 追記（2026-08-17）: R9-2 照合の配線を PR-W5 へ退避した

PR-W1（対話UX）は W-2（HITL 表示）と W-1（1問1答）に分割され、本 PR は **PR-W1a = W-2 のみ**になった。あわせて、承認済み requirements の対象ファイル表に無かった R9-2 照合の**配線**（契約テスト `tests/test_r9_2_anchor_verify_contract.py` 292 行）を **PR-W5 へ退避**した。**allow list の宣言 19 件（verify 上の allowed anchor は 20）と本監査シートの記録は残す**（記録まで消すと、本 PR が落とした 20 アンカーが未宣言 drift になるため）。

### 現時点で機械が強制していないこと（重要）

1. **`kind`（`moved` / `replaced` / `pointerized`）は分類ラベルであり、照合器は読まない。** `docs/audits/r9-2-anchor-tools.py` の `AllowList.load` が読むのは `anchor` と `reason` の 2 つだけで、`kind` / `replacement` / `removed` / `pointer_*` はすべて無視される（実測: `grep -c "kind" docs/audits/r9-2-anchor-tools.py` = **0**）
2. **`replaced` の類似度 0.8 も `pointerized` の 6 条件も、PR-W5 で配線を戻すまで誰も検査しない。** 本 PR まではこれらを検査する pytest が 1 本だけ存在したが、本 Step で削除した
3. **本 PR が落とした 20 アンカーの担保は、この記録と人手レビューだけである。** 照合器 `verify` 自体はどの check / pytest からも呼ばれていない（main でも同じ状態で、これは本 PR が作った退行ではない）

### PR-W5 への引き継ぎ

**やること**: R9-2 アンカー照合の pytest 配線（`kind` の機械強制を含む）を戻す。
**owner**: 本 PR の起票者。次回 `/gdd-dev` で `PR-W5` として新しい作業を起こす。

**着手前に決める / 直す必要がある前提条件 3 件**（いずれも 2026-08-17 に実測）:

1. **`replaced` の閾値余裕が 4 件中 1 件で 0.0089 しかない。** 実測（行頭 prefix を落として `difflib.SequenceMatcher.ratio()`）:

   | エントリ（本文先頭） | ratio | 閾値 0.8 からの余裕 |
   |---|---|---|
   | `各承認ポイントは必ず以下の 4 要素を揃える…` | 0.9778 | 0.1778 |
   | `### 承認ポイントの 4 要素（欠落禁止）` | 0.9545 | 0.1545 |
   | `` `LLM 方針レビュー` を必ず含める…`` | 0.8710 | 0.0710 |
   | `` `Adversarial Requirements Review` を必ず含める…`` | **0.8089** | **0.0089** |

   `Adversarial Requirements Review` 行の文言をあと数文字削る改稿が入れば 0.8 を割り、**PR-W5 で配線を戻した瞬間に fail する**。

2. **`compare` が現行の manifest を読めない。** 実測: `r9-2-anchor-tools.py compare` に現行 JSON manifest を渡すと `ANCHOR_TOOL_FAILED: legacy anchors header incomplete (0/5 set counts)` で落ちる。現行 manifest は `schema_version: 1` の JSON（`base_commit` / `counts` / `sets`）だが `compare` は legacy テキストヘッダ形式を前提にしている。**アンカー消失の横断検知手段が実質不在**で、これが「manifest を手編集すれば allow list の条件を 1 つも満たさずに verify を通せる」経路を成立させている。配線を戻すときに `compare` の対応も同時に見ること。

3. **`kind` を機械が読む設計にするかを先に決める。** 現状は上記 1 のとおりラベルに過ぎない。`AllowList.load` を拡張して `kind` ごとの条件を強制するのか、`kind` を廃して `reason` の人手レビューに一本化するのかを、配線を戻す前に決める。

### allow list の内訳（機械集計。手で数え直さないこと）

```bash
python3 -c "
import json, collections, pathlib
d = json.loads(pathlib.Path('docs/audits/r9-2-human-check-template-allowed-missing.txt').read_text())
print(collections.Counter(e.get('kind','(none)') for e in d['allowed_missing']))
"
```

2026-08-17 実測: `moved 14 / replaced 4 / pointerized 1`（計 19 宣言。verify 上の allowed は 20）。
