# R9-2 Wave 1 実装計画: hot references 蒸留とスキル本文予算例外の解消

- 作成日: 2026-07-18
- 状態: 未着手
- 前提: PR 旧#169（R9-2 Wave 0 + pilot、2026-07-17 マージ済み）
- 目的: 実行時にロードされる references・スキル本文の注入トークンを、挙動を変えずに削減する。セッション定常費（起動時注入）ではなく、GDD ワークフロー実行時のコンテキスト消費が対象
- 実装体制: Sonnet セッションで通常の GDD フローに乗せて実装する。**現在実行中のタスクが completion-check を完了してから着手する**（同一ファイル群の並行編集を禁止）

## 背景

Wave 0 で以下が完了している。本計画はその継続で、蒸留の型・ガードは Wave 0 のものをそのまま使う。

- 実行時に一度もロードされていない references 6 本を `docs/references-archive/` へ移動
- `brainstorming-steps.md` を規定度監査に基づき 517→139 行に蒸留（原本アーカイブ済み）
- `tests/checks/skill-body-budget.sh` 新設: 本文 350 行上限 + 例外 4 スキルのラチェット（baseline 超過で fail）
- references 合計行数バジェット（13,128 行）、`lint-runtime-budget.py` の実行時推定トークン上限（express ≤33,300 / standard ≤57,300）を凍結

残作業は (1) 実行時ロードが残っている hot references 上位 4 本、(2) skill-body-budget の例外リスト 4 スキル。

## Global Constraints

1. **挙動維持が最優先**: 各蒸留は replay 評価（Wave 0 と同一の型）に合格して初めて完了。数値目標（-N%）を先に置かず、規定度監査の結果に従う。目標駆動で規範文を削らない
2. **原本保全**: 蒸留前の原本は `docs/references-archive/<name>-pre-r9-2-wave1-original.md` として保存する（ロールバック手段）
3. **保存必須（蒸留で削ってはならないもの）**:
   - 契約文字列・アンカー（他ファイル・テスト・スクリプトから grep される見出し ID・キーワード）
   - 成果物フォーマット定義（テンプレート必須フィールド、台帳スキーマ、出力契約）
   - 停止規律・ゲート条件・数値閾値・「〜してはならない」系の規範文
4. **削減対象（優先順）**: 他文書と重複する説明 → 過剰な例示（worked example 相当はアーカイブへ）→ 背景・理由の冗長な散文（1 文へ圧縮）→ 歴史的経緯
5. **判断に迷った節は削らない**: Wave 0 の flag 運用を踏襲し、監査シートに flag を立てて人間確認に回す
6. **ラチェットは減少方向のみ**: タスク完了ごとに baseline・バジェット値を新実測値へ引き下げる。引き上げは本計画のスコープ外
7. 各タスクのコミット条件: `validate-plugin` exit 0、契約テスト green、`skill-body-budget.sh` green
8. 1 コミット = 1 reference（または 1 スキル）。まとめて蒸留しない

## Task 1: 実行時ロード実測の更新と対象確定

Wave 0 と同じ実測方法で、現時点のロード頻度を再取得する。

- 対象候補（ソース行数の現在値）: `state-machine.md` 841 行 / `human-check-template.md` 773 行 / `requirements-template.md` 721 行 / `phase-progression.md` 696 行
- 実測の結果、ロード実績が無いと判明したものは蒸留せず Wave 0 と同様にアーカイブへ移動（そちらが優先・低コスト）
- 実測でこの 4 本以外に高頻度ロードの reference があれば、監査対象に追加してよい（Global Constraints 適用）

**成果物**: 実測結果の記録（ロード頻度順の一覧）を本計画書の末尾に追記

## Task 2: hot references の規定度監査と蒸留

Task 1 で確定した対象を、1 本ずつ以下の手順で処理する。

1. 監査シート作成: `docs/audits/r9-2-<name>-audit-<date>.md`（Wave 0 の `r9-2-brainstorming-steps-audit-20260716.md` と同形式: 節別判定・保存必須契約の一覧・判定集計・矛盾 flag）
2. 監査結果に基づき蒸留（Global Constraints 3・4 に従う）
3. 原本を `docs/references-archive/` へ保存
4. アンカー整合テスト・契約テスト・replay 評価に合格させる
5. コミット（1 reference = 1 コミット）

## Task 3: skill-body-budget 例外 4 スキルの削減計画実行

`tests/checks/skill-body-budget.sh` の例外リストに記載済みの削減計画を実行し、各スキル本文を 350 行以下にする。

| スキル | baseline | 削減手段（budget スクリプト記載の計画） |
|---|---|---|
| `root-cause-investigation` | 650 行 | superpowers fork 由来の重複説明を references へ分離し、本文はルーティングと証跡手順に絞る |
| `gdd-writing-skills` | 590 行 | 開発時のみ必要なガイダンスを docs / references へ分離し、実行時本文を最小化する |
| `gdd-systematic-debugging` | 484 行 | 詳細なデバッグトリアージ資料を references へ分離し、本文は経路判断に絞る |
| `gdd-brainstorming` | 352 行 | 残りの詳細ステップ本文を `references/brainstorming-steps.md` へ統合する |

- references へ分離する場合、分離先が Task 2 の実行時ロード対象を再肥大させないこと（実行時に必要な節のみロードされる構造にする。references 合計行数バジェット 13,128 行は超えない）
- 350 行以下を達成したスキルは例外リストと baseline 定義から削除する。**例外リストが空になるのが最終状態**

## Task 4: バジェット値の引き下げ（ラチェット確定）

Task 2・3 完了後の実測値に基づき、再肥大を構造的に防ぐ。

- references 合計行数バジェット（現 13,128 行）を新実測値まで引き下げ
- `lint-runtime-budget.py` の上限（express 33,300 / standard 57,300 推定トークン）を新実測値 + 5% 程度まで引き下げ（`skill-body-budget.sh` と `lint-scripts-functional.sh` の両方の呼び出し箇所を同期）
- 例外リスト削除済みスキルの baseline 定義を除去

## 受入確認

1. replay 評価: Wave 0 と同一シナリオセットで蒸留前後の挙動が一致する
2. 全テスト green: `validate-plugin` / 契約テスト / `skill-body-budget.sh` / `lint-runtime-budget.py`（引き下げ後の閾値で）
3. 削減実測の記録: 各対象の蒸留前後の行数・推定トークンを CHANGELOG と本計画書末尾に記載
4. 例外リストが空である（未達の場合は、残存スキルごとに更新済み baseline と未達理由が明記されている）
5. `docs/references-archive/` の原本から任意の 1 本を復元してテストが通ること（ロールバック手順の実証）

## 実施記録

### Task 1 実測結果（base commit 33cb8aa5f448724ed4510b86d03dcd40af4a9ea8 / 2026-07-29実測）

行数前提はほぼ設計書どおりだが、バジェット上限は設計書記載値（express 33,300 / standard 57,300）から実際には 33,600 / 57,600 へ引き上げ済みで、設計書のほうが古い。

**hot references:**

| reference | 行数 | 参照元skill数 | 全参照数 | runtime profile | 守る契約テスト数 |
|---|---|---|---|---|---|
| state-machine.md | 841 | 9 | 36 | 非収載（条件付きロード） | 9 |
| human-check-template.md | 773 | 2 | 28 | 非収載 | 15 |
| requirements-template.md | 721 | 1 | 21 | standard | 8 |
| phase-progression.md | 697 | 6 | 23 | 非収載 | 5 |

**skill body（frontmatter除外）:**

| skill | 現body行 | budget baseline |
|---|---|---|
| root-cause-investigation | 644 | 650 |
| gdd-writing-skills | 590 | 590 |
| gdd-systematic-debugging | 484 | 484 |
| gdd-brainstorming | 352 | 352 |

**バジェット実測（`--quiet`なしの`lint-runtime-budget.py`実行結果）:**

express 33,521/33,600・standard 57,568/57,600・skill body合計 7,217/7,500・express template 182/200・standard template 827/850・references合計 12,280/13,128。

**対象範囲の確定:** 承認ポイント1でOption B（8対象: hot references 4本 + skill 4本）を採用。設計書のOption D分岐（human-check-template.mdのアーカイブ移動）はdesign-gatingで却下し、他3referencesと同じ5ステップで蒸留する（ADR-1）。

### S-3 実施記録（post-distillation / 2026-07-31）

#### 蒸留8対象の実績

| 対象 | 前 | 後 | 行削減率 | 推定トークン（前 → 後） | トークン削減率 |
| --- | --- | --- | --- | --- | --- |
| `references/state-machine.md` | 841 行 | 792 行 | −5.8% | 18,760 → 17,799 | −5.1% |
| `references/phase-progression.md` | 697 行 | 677 行 | −2.9% | 12,951 → 12,799 | −1.2% |
| `references/human-check-template.md` | 773 行 | 773 行 | 0% | 10,641 → 10,641 | 0% |
| `references/requirements-template.md` | 721 行 | 693 行 | −3.9% | 12,042 → 11,195 | −7.0% |
| `skills/root-cause-investigation/SKILL.md` | 644 行 | 541 行 | −16.0% | 6,340 → 6,294 | −0.7% |
| `skills/gdd-writing-skills/SKILL.md` | 590 行 | 558 行 | −5.4% | 5,247 → 5,091 | −3.0% |
| `skills/gdd-systematic-debugging/SKILL.md` | 484 行 | 463 行 | −4.3% | 6,980 → 6,665 | −4.5% |
| `skills/gdd-brainstorming/SKILL.md` | 352 行 | 312 行 | −11.4% | 8,731 → 8,021 | −8.1% |
| **合計** | **5,102 行** | **4,809 行** | **−5.74%** | **81,692 → 78,505** | **−3.90%** |

> 表の基準: **行数列は body 行**（frontmatter を除く）、**推定トークン列は全文基準**（frontmatter 込みの `ceil(len(text)/4)`）で、2 列の基準は一致していない。監査シートは body 基準で記録しているため、skill 4 本のトークン値は監査シートと 36〜46 トークンずれる。body 基準で揃えた場合の合計は **81,523 → 78,335 = −3.91%** で、結論（削減率は約 −4%）は変わらない。

各対象の節別判定・AC-11判定・未達理由の正本は `docs/audits/r9-2-<対象名>-audit-20260729.md` を参照する。

#### バジェット7値（すべて現行値より小さい。`ceil(蒸留後実測 × 1.02)`。承認された余裕率+2%、design.md D-5 Amendment 2）

| 上限 | 現行 | 実測 | 新値 | 引き下げ後 headroom |
| --- | --- | --- | --- | --- |
| `--max-skill-body-lines` | 650 | 558 | **570** | 12 行 |
| `--max-total-skill-body-lines` | 7500 | 7021 | **7162** | 141 行 |
| `--max-express-template-lines` | 200 | 182 | **186** | 4 行 |
| `--max-standard-template-lines` | 850 | 799 | **815** | 16 行 |
| `--max-express-estimated-tokens` | 33600 | 32811 | **33468** | 657 トークン |
| `--max-standard-estimated-tokens` | 57600 | 56011 | **57132** | 1,121 トークン |
| `references/` 合計行数 | 13128 | 12183 | **12427** | 244 行 |

`--max-skill-body-lines` の制約元は `skills/gdd-writing-skills/SKILL.md`（558行）。design.md Amendment 2 が予測値として挙げた 354 はハードコードせず、T-10 の一括実測から算出した。

#### AC-8（バジェット例外リスト）の着地

- `gdd-brainstorming` のみ 312 行で ≤350 を達成し、`skill_body_reduction_plan()` / `skill_body_baseline_lines()` の両関数から削除した。
- 残り3件（`root-cause-investigation` 541 / `gdd-writing-skills` 558 / `gdd-systematic-debugging` 463）は baseline を実測値へ引き下げ、未達理由を script コメントに明記した。**未達理由は「意味保存を優先した判断」**であり、到達不能ではない（T-8 で貪欲 set cover により 177 行への圧縮が構成的に確認されている）。
- **承認時の最終状態は「例外リストが空」だったが、本 Wave はそこに到達していない**（3 件残存）。この着地で締めることは人間の再承認を得ている（`hc-20260801-8`）。

#### AC-6 上限の実効性の実証

**7 値すべて**で「上限ちょうどは exit 0 / +1 単位で exit 1」を実測した（判定は厳密な `>`）。狙った上限だけが単独で反応することも各回で確認している（例: standard template を試験する間 `express` は 182/186 のまま無反応）。実測後は全ファイルを復元し `git status` clean を確認済み。

| 上限 | 新値 | 上限ちょうど | +1 単位 |
| --- | --- | --- | --- |
| `--max-skill-body-lines` | 570 | 570 → exit 0 | `SKILL body line budget exceeded: skills/gdd-writing-skills/SKILL.md 571 > 570` / exit 1 |
| `--max-total-skill-body-lines` | 7162 | 7162 → exit 0 | `Total SKILL body line budget exceeded: 7163 > 7162` / exit 1 |
| `--max-express-template-lines` | 186 | 186 → exit 0 | `Runtime template budget exceeded: express 187 > 186` / exit 1 |
| `--max-standard-template-lines` | 815 | 815 → exit 0 | `Runtime template budget exceeded: standard 816 > 815` / exit 1 |
| `--max-express-estimated-tokens` | 33468 | 33468 → exit 0 | `express runtime profile estimated runtime tokens exceeded: 33469 > 33468` / exit 1 |
| `--max-standard-estimated-tokens` | 57132 | 57132 → exit 0 | `standard runtime profile estimated runtime tokens exceeded: 57133 > 57132` / exit 1 |
| `references/` 合計行数 | 12427 | 12427 → exit 0 | `REFERENCES_LINE_BUDGET_EXCEEDED: 12428 > 12427` / exit 1 |

トークン 2 値は、completion-check `completion-20260801-1` blocker F-3 の逐語復元 2 行（`skills/gdd-brainstorming/SKILL.md`。詳細は `docs/audits/r9-2-gdd-brainstorming-audit-20260729.md` §5）で実測が 32,804 → 32,811 / 56,004 → 56,011 へ動いたため、`ceil(実測 × 1.02)` を再計算して 33,461 → **33,468** / 57,125 → **57,132** に更新し、境界も再実測した。いずれも現行値（33,600 / 57,600）より小さくラチェットは成立している。

#### AC-10 ロールバックの実証

- **その1（引き下げ前）**: `docs/references-archive/state-machine-pre-r9-2-wave1-original.md`（841行）を `references/state-machine.md` へ復元 → `validate-plugin.sh` exit 0 / `pytest` 790 passed, 607 subtests → `git checkout --` で蒸留版へ復元。
- **その2（引き下げ後）**: バジェット引き下げコミットを `git revert` した状態で同じ復元を行い、両テスト exit 0 を確認 → revert と復元の両方を戻した。
- **巻き戻しに revert が要るかは復元範囲で変わる**（実測）。
  - **原本 1 本だけの復元**: revert 不要。引き下げ済み HEAD のまま `references/state-machine.md` を原本 841 行へ復元しても references 合計 **12,232 ≤ 12,427** で、`lint-runtime-budget.py`（新 6 引数）/ `validate-plugin.sh` とも exit 0。AC-10 が実証したのはこの単一ファイル復元であり、その2 の revert は必須条件ではなかった。
  - **8 本すべての復元**: revert が必要。skill body 合計が **7,217 > 7,162** で落ちる（併せて `gdd-writing-skills` 590 > 570 / `root-cause-investigation` 644 > 570 / express 推定トークン 33,521 > 33,468）。この場合のみ「原本復元 + バジェットコミットの revert」の2手順セットになる。

#### 測定できないこと・分かったこと（Honest Limitations）

- **設計書の前提「約 5,000 → 約 2,000 行（−60%）」は誤りだった。** 実績は8対象合計（body 行 5,102 → 4,809）で約 **−5.7%**（想定 −60% の約 1/10）。生ファイル行数でも 5,122 → 4,829 = −5.7% で同値。これらは契約文書であって解説文書ではなく、削れる散文がほとんど存在しなかった。この前提の崩壊が、承認された余裕率を +5% から +2% へ改定する直接の原因になった（+5% では7値中4値が現行上限を上回りラチェットが成立しない）。
- **行数削減とトークン削減は別物。** `root-cause-investigation` は行数 −16.0% に対し推定トークン −0.7% で、実質的な context 削減はほぼゼロだった。`gdd-writing-skills`（−5.4% / −3.0%）と `gdd-systematic-debugging`（−4.3% / −4.5%）は同率で減っており同型ではない。行数だけを成果指標にすると実態を誤認する。**本 Wave の目的は実行時に注入されるトークンの削減なので、成果指標は上表の「トークン削減率」の合計行を見ること**（行数の合計行ではない）。
- **蒸留前後の文面に対する LLM の解釈差は決定論的に測定できない。** 逐語照合 subagent による外部証跡（AC-3）で補っている。原本は `docs/references-archive/` にコミット保全済み。
- **検証ツール（AC-1 のアンカー照合器）自体の fail-open を計 7 件検出・修正した。** いずれも「読み手が1つの厳密な形しか認めず、書き手は複数の形で書く」型で、検査は走っているのに実質何も見ていない状態だった。7 件はすべて bash 版に由来し、うち 1 件（旧#7）は 旧#6 の修正自身が持ち込んだもので Python への構造書き直しで解消した。

  | # | 内容 | 出所 |
  | --- | --- | --- |
  | 1 | マッチ 0 件の `grep` が `set -euo pipefail` で集合 (3) の走査を silent に打ち切る | `handoff/t-2-distillation.md`（本番適用前に検出） |
  | 2 | `[[ "$line" == \#* ]] && continue` が集合 (1) の見出し 39 件を丸ごと未照合にする | 同上 |
  | 3 | `verify` が anchors ファイル不在でも 0 回ループのまま `ANCHOR_VERIFY_OK` に到達する | `handoff/t-2-impl-gate.md` Finding 1 |
  | 4 | `extract` の非アトミック書き込みで anchors.txt が truncate され、その残骸を 0 件照合が pass させる | 同 Finding 2 |
  | 5 | `## SET ` の前方一致がラベル 1〜5 に限定されず内容行と衝突する | 同 Finding 3 |
  | 6 | 字下げフェンス・字下げ見出し・小文字 `step` の被覆漏れ | `handoff/t-3-collation.md` F-1 |
  | 7 | `--allow-missing` の非対称読み（照合は `#` 行にマッチするがカウントからは除外）。**旧#6 の remediation 自身が持ち込んだ**同型欠陥 | `handoff/t-3-impl-gate.md` F-2 |

  Python 化後にも 3 件（SET 3 の nested quote 取りこぼし / 条件 2 の回帰ケース欠落 / `present()` 大小文字区別の回帰ケース欠落）を検出・修正しているが、これらは `worklog.md` L42 と `handoff/t-10-impl-gate-remediation.md` L130 が明示するとおり **under-extraction と回帰ケース欠落であって fail-open ではない**ため、上表には数えていない。旧記載の「計 9 件（bash 6 + Python 3）」はこの書き分けを取り違えたもので、7 件が確定できる件数である。
- **アンカー照合の pass は「契約が保全されている」ことの証明ではない。** 照合器の存在判定はファイル全体に対する**部分一致**で、行境界も文脈も見ない。そのため「アンカー文字列は残っているが、それを含む文の規範性が変わっている」型の変化を原理的に検出できない。盲点の実測値は `requirements-template` で 201/559 = **36.0%**、`human-check-template` で 210/585 = **35.9%**（対象により 29〜36%）。実際に本 Wave でも `gdd-brainstorming` の 2 箇所（判定主体 `reviewer / 人間が` の脱落、`Design Policy Discussion` の総則の格下げ）がこの盲点を通過し、機械照合は pass したまま規範が弱まっていた（completion-check で検出し、原本から逐語復元済み）。**AC-3 の逐語照合はこの盲点を埋めるための補完であり、機械照合の重複ではない。**「`verify` が通ったから意味は変わっていない」とは読めない。
- **AC-1 の「アンカーが 100% 存在する」には承認済みの例外が 2 件ある。** `references/phase-progression.md` で原本 L556-560 の例に含まれる `Origin Steering:` / `Parent Hotfix:` の 2 行を意図的に削除し、`--allow-missing` の allow list で宣言している（`verify` 出力は `597 anchors checked, 0 unexpected missing (2 allowed)`）。削除理由は「この例が同じ節で定義される value grammar を満たさず規範と矛盾していた」ためで、規範 bullet と上位互換の例は蒸留版に現存する。正本は `docs/audits/r9-2-phase-progression-allowed-missing-v2.txt`。他 7 対象の allow list は空。
