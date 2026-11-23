# R9-2 Wave 1 監査シート: phase-progression.md（2026-07-30 実施）

対象: `plugins/gate-driven-development/references/phase-progression.md`（原本 697 行 / 51,802 chars / 推定 12,951 tokens）
着地: **677 行 / 51,195 chars / 推定 12,799 tokens（-20 行 / -2.9%、-152 tokens / -1.2%）**
推定トークンは `scripts/lint-runtime-budget.py` の `estimated_tokens()`（`ceil(len(text)/4)`、`len` は Python の文字数）と同一式。
ルーブリック: keep（low freedom 契約）/ rewrite-to-intent（意図へ圧縮）/ delete（重複・歴史的経緯・例示）/ relocate（原本退避で代替）
原本退避先: `docs/references-archive/phase-progression-pre-r9-2-wave1-original.md`（蒸留コミットより前の archive コミット `69d8030` で git 管理下。base commit `33cb8aa5` の原本と `diff` バイト同一）
アンカー分母: `docs/audits/r9-2-phase-progression-anchors.txt`（archive と同一コミットに固定）

先行対象 `state-machine.md`（`r9-2-state-machine-audit-20260729.md`）と同系統のため、判定基準は先行対象と同一のものを適用した（矛盾なし）。

## 抽出コマンド列（再実行で同じ分母が再現することを確認済み）

```bash
rm -rf /tmp/r9-2-base-tree && mkdir -p /tmp/r9-2-base-tree
git archive 33cb8aa5f448724ed4510b86d03dcd40af4a9ea8 | tar -x -C /tmp/r9-2-base-tree

docs/audits/r9-2-anchor-tools.sh extract \
  --base-tree /tmp/r9-2-base-tree/plugins/gate-driven-development \
  --target references/phase-progression.md \
  --out docs/audits/r9-2-phase-progression-anchors.txt

docs/audits/r9-2-anchor-tools.sh verify \
  --anchors docs/audits/r9-2-phase-progression-anchors.txt \
  --candidate references/phase-progression.md \
  --allow-missing docs/audits/r9-2-phase-progression-allowed-missing.txt
```

実行 cwd: 上記は `plugins/gate-driven-development` を cwd として実行する（パスが相対のため）。誤った cwd から実行した場合、`verify` は `ANCHOR_VERIFY_FAILED: anchors not found: ...` / exit 1 で fail-closed する。

`--expect-empty` は **使用していない**（5 集合すべてが非空。0 件集合は 1 つも発生していないため、「空であることが正当な集合」の事前宣言は不要）。
再現性: 同一コマンドを 2 回実行し、出力 `anchors.txt` が `diff` で完全一致することを確認（`REPRODUCIBLE_OK`）。

**抽出器の被覆修正（T-3 逐語照合レビュー F-1 / 本シートの初版からの訂正）**: 初版の集計（合計 536 件）は、抽出器が見出し・コードフェンスを **行頭アンカー限定**（`^#{1,6} ` / 行頭 + バッククォート 3 個）で判定していたため、リスト項目配下の **字下げ見出し・字下げコードフェンスを分母から取りこぼしていた**。`Step <数字>` も大文字始まりのみを拾っていた。抽出器を字下げ許容（`^[ \t]*`）・`[Ss]tep` に修正して再抽出した結果、分母は **536 → 597 件**（SET 1 が 34→44、SET 2 が 2→3、SET 4 が 33→83）に拡大した。本シートの以降の記述は **修正後の分母**を正とする。SET 3 は 380 件で不変。

## 保存必須の契約（蒸留後も維持したもの）

アンカー全数照合の分母と結果:

| 集合 | 内容 | 件数 | 蒸留後の欠落 |
|---|---|---|---|
| SET 1 | 見出し行（`^[ \t]*#{1,6} ` 全行。**字下げ見出しを含む**。コードフェンス内の擬似見出しも含む） | 44 | 0 |
| SET 2 | `[Ss]tep <数字>` 番号体系（**小文字始まりを含む**） | 3 | 0 |
| SET 3 | 外部被参照文字列（base tree `33cb8aa5` の `tests` / `hooks` / `scripts` / `skills` / `references` / `commands` / `agents` から逆引き。参照元側の**字下げ見出しも含む**） | 380 | 0 |
| SET 4 | コードフェンス内の全行（フェンス判定は `^[ \t]*` + バッククォート 3 個。**リスト項目配下の字下げフェンスを含む**） | 83 | 2（承認済み削除。下記） |
| SET 5 | 規範表現・数値閾値を含む行 | 87 | 0 |
| 合計 | | **597** | **0 unexpected（2 allowed）** |

**SET 4 の承認済み欠落 2 件**: 原本 L556-560 の例「feat-A → hotfix-1 → hotfix-2」に含まれる `Origin Steering: .steering/20260301-feat-A/` と `Parent Hotfix: .steering/hotfix-1-2026-04-15/` の 2 行。この例の `Origin Steering` 値は prefix なしの素の path であり、**同じ節の 4 行下で定義される value grammar**（`local:` / `snapshot:` / `git-ref:` / `unresolved:` の 4 形式 + `Origin Resolution Status` 併記）を満たしていない。規範側と矛盾する例のため削除した。併記規約の規範 bullet（`Parent Hotfix: <直前 hotfix steering path>` を併記する）は蒸留版 L543 に現存し、蒸留版 L561-566 の hotfix-3 の例が `local:` prefix + `Origin Resolution Status` + `Parent Hotfix` + `Abandoned Hotfix Attempts` の完全形で上位互換。契約損失なし。この 2 行は `docs/audits/r9-2-phase-progression-allowed-missing.txt` に宣言し、`verify --allow-missing` で機械照合する（宣言と実測が 1 行でもずれれば fail-closed。宣言外の欠落が 1 件でも出れば通常どおり `ANCHOR_VERIFY_FAILED`）。

個別に維持を確認した契約群:

- **route 分類の全語彙**: `implementation_fix_only` / `design_detail_only` / `requirements_amendment` / `human_recheck_required` / `planning_rework_required` / `express_promotion_required` / `batch_mixed` / `cancelled` と、Active Session Follow-up Classification 表 7 行・Post-Done Correction Default 表 4 行の全行
- **停止規律・停止マーカー**: `<gdd-stop reason="done">` / `blocked` / `human-check-waiting` / `staging-verification-blocked` の各発火条件、`参照した正本` を含む記録義務、`Fix Attempts >= 2` で route 判断記録が無ければ fail-closed
- **数値閾値**: Fix Attempts 3、Scope Drift Counter 3 超過（4 回目以降）、Cumulative Changed Files 3 倍、hotfix chain depth 5、`Abandoned Hotfix Attempts` 3 件、PR CI Wait Timeout 既定 1800 秒 / network retry 3 回・最大 60 秒
- **成果物フォーマット定義（コードフェンス 83 行中 81 行を verbatim。残る 2 行は上記の承認済み削除）**: Follow-up Classification / Express フロー / External Guardrails Inventory 表 / 並列 batch フロー図 / Batch Route Decisions / Worklog フォーマット / per-task annotation / Hotfix Diverted / Batch WIP Discard / Route Decision / CI Partial Pass / Origin Steering + Abandoned Hotfix Attempts の例 / Verification History / root stub
- **fail-closed 条件**: CI 3 状態の排他分類（到達不能 / 設定不明 / 明示未設定）と Manual skip 禁止、override validation、partial write 検知時の Rollback 3 択、`Origin Steering:` value grammar 4 形式、Scrub 許可範囲マトリクス 8 行の禁止指定
- **Escalation Decision Table 7 行と判定の優先順位**（安全側に倒す規則・override 不可の宣言を含む）

## 節別判定

| 節 | 旧行数 | 新行数 | 判定 | 処置 |
|---|---|---|---|---|
| Header（所有 / 上位正本 / 参照元 + 導入） | 9 | 9 | keep | 正本分界と参照ポインタ。verbatim |
| ## Autonomous Continuation | 5 | 5 | keep | 既に `state-machine.md` への正本委譲 2 行のみ |
| ## Post-Merge Same-Chat Boundary | 4 | 4 | keep | worktree 分離方針（アンカー） |
| ### Merge Report Cleanup Trigger | 4 | 4 | keep | cleanup cue の判定契約 |
| ## Active Session Follow-up Classification | 18 | 18 | keep | route 分類表 7 行と `requirements_amendment + human_recheck_required` の合成規則 |
| ### Same-Session Correction Rule | 22 | 20 | delete | 直上の分類表 行 1・行 2 と同内容の bullet 2 件（`既存 AC の範囲内の実装修正` / `reviewer 指摘`）を削除。優先順位 1〜5、merge 済み例外、`gdd-refactor-planning` / 当初目的の未達 / `new` intent の 3 bullet は verbatim 維持（**flag 1**） |
| #### Post-Merge Follow-up Worktree Policy | 20 | 20 | keep | 標準フロー 5 step と HITL 出力 5 項目は成果物フォーマット |
| #### Post-Done Correction Default | 24 | 24 | keep | 表 4 行・適用範囲・記録フォーマット |
| ## Express Path（quick express） | 4 | 4 | keep | — |
| ### Express フロー | 7 | 7 | keep | フロー図はコードフェンス（SET 4） |
| ### Express の遷移ルール | 15 | 15 | keep | skip 対象・tasklist 最小構成・impl-gate advisory 化はすべて low freedom 契約 |
| ### Express → standard 昇格 | 14 | 4 | rewrite-to-intent | フィールド更新 9 bullet を 1 段落へ集約。原本末尾の「詳細は `state-machine.md` § Express 昇格時の state ロールバック規則を参照」を「正本とする」に格上げし、field 名（`Task Size` / `Requirements Review Status` / `Design Review Status` / `Human Check Status` / `Planning Reviewer Selection` / `Implementation Reviewer Selection` / `Resume From`）と値はすべて逐語で残した。原本に無い field は追加していない（**flag 2**） |
| ## Planning Phase 〜 ### gdd-design-gating（5 節） | 29 | 29 | keep | phase ごとの reviewer 必須・selection 保存先・`waived` 不使用・high 指摘解消は per-phase の所有宣言。`gdd-requirements-gating` と `gdd-design-gating` で reviewer 2 行が反復するが、先行対象 `state-machine.md` § 更新責任（flag 2）と同じ理由で共通化しない |
| ## Build Phase | 12 | 12 | keep | phase 順序 1〜6 + 5.5 Refactor Gate。本ファイルの所有そのもの |
| ### External Guardrails Inventory（W-5）+ 表本体 | 21 | 21 | keep | 生成義務・目的（対象外の明示を含む）・表テンプレート・reviewer の差し戻し条件 |
| ### Staging Verification（W-6） | 8 | 8 | keep | mandatory 化と Express 例外 |
| ### Parallel Execution（並列実行） | 73 | 73 | keep | 並列ルール 5 件 / in-flight overlap 6 step / human_recheck 5 step / 複数 route 6 rule / severity 順序 / 2 task 同時昇格の直列化。すべて数値・順序・fail-closed 条件を含む |
| ## Batch Route Decisions（フェンス内） | 11 | 11 | keep | worklog フォーマット |
| ### batch_mixed Serialization Contract | 23 | 23 | keep | 単独 writer 契約・先着採用・辞書順・partial write の Rollback 3 択 |
| ### Batch-Hotfix Bridge Contract | 56 | 56 | keep | Case 1 / Case 2 の全 step と state.md 書換規約 |
| ## Implementation Review | 5 | 5 | keep | reviewer 必須と selection 保存先 |
| ## Remediation | 7 | 7 | keep | 既に `state-machine.md` への正本委譲を含む 4 bullet |
| ### Escalation Decision Table | 21 | 21 | keep | 判定表 7 行・優先順位・記録義務・複数境界の記録粒度 |
| ## Route Decision（フェンス内） | 10 | 10 | keep | worklog フォーマット |
| ### E2E Discovery Loop | 37 | 37 | keep（Why のみ圧縮） | 自走 4 条件 / Scope Drift Guard の OR 2 条件と閾値 / `Drift Review Required` のクリア条件 6 件は verbatim。`Why` の 1 文目（一般論）のみ削除 |
| ## Completion | 20 | 20 | keep | Verification schema（field / status 許容値 / 禁止値 / 非空必須）と Post-Completion PR Flow |
| ### Post-PR / Post-Merge Contract | 208 | 203 | keep + delete 1 箇所 | 多段 hotfix の旧例（`例: feat-A → hotfix-1 → hotfix-2`、5 行）を削除。同節後半の `例: feat-A → hotfix-1（cancelled）→ hotfix-2（merged）→ hotfix-3` の例が `Origin Steering:` value grammar 確定後の完全形（`local:` prefix + `Origin Resolution Status` + `Parent Hotfix` + `Abandoned Hotfix Attempts`）を示しており上位互換（**flag 3**）。CI Wait semantics a〜g、Origin VH Rehydration、Scrub 規約 X-1〜X-4、VH schema、chain depth guard はすべて verbatim |
| ## Diff Routing（差し戻し先） | 7 | 4 | rewrite-to-intent | 4 bullet を 1 行へ集約。4 つの route → 復帰先の対応は Escalation Decision Table の「復帰先」列と同内容のため、その旨を明示したうえで 4 対応をすべて逐語で残した（**flag 4**） |
| ## External Verifier との共存 | 4 | 4 | keep | 非固定宣言 |

上表は 34 見出し（SET 1 全件）を覆う。`## Planning Phase 〜 ### gdd-design-gating` の行が 5 見出しをまとめている。

### Why 節の圧縮（行数不変・トークンのみ削減）

`**Why**` 段落 7 箇所を 1〜2 文へ圧縮した。規範を含む節は当該文を逐語で残している。

| 箇所 | 保持した規範文 |
|---|---|
| § Same-Session Correction Rule | 「merge 前は same-session correction、merge 後は hygiene 済みの follow-up worktree に分ける」 |
| § 並列 batch human_recheck | 「この例外は並列文脈に閉じる（逐次実行時の `human_recheck_required` は通常通り Tasklist Reset Policy に従い全 revert 対象）」を逐語保持 |
| § 並列 batch 複数 route | 「severe でない route（fix_only / design_detail_only 単独）は当該タスクだけで閉じて」を保持 |
| § batch_mixed Serialization | 「main session 単独 writer + 先着採用ポリシーで deterministic な収束を保証する」を保持 |
| § Batch-Hotfix Bridge | 「手動 Hotfix は既定 queue とし、緊急時のみ batch pause を許容する」を保持 |
| § E2E Discovery Loop | 「方向性が同じなら AI が自律的に吸収し、方向性が変わるときだけ人間に戻す」を逐語保持 |
| § Manual merge continuation | 「manual merge を gate release として扱うことで、安全な read-only 後続作業だけを継続できる」を逐語保持 |

`**Why**: CI 不在 / auth 失敗 ...`（CI Wait semantics）と `**Why**: PR 作成後・merge 後の問題発覚 ...`（Post-PR/Post-Merge）の 2 箇所は SET 5 アンカーのため verbatim 維持。

## 判定集計

- **keep: 26 節**（契約表・許容値・停止規律・数値閾値・成果物フォーマット）
- **rewrite-to-intent: 2 節**（`### Express → standard 昇格` / `## Diff Routing`）
- **delete が主判定: 1 節**（`### Same-Session Correction Rule` の重複 bullet 2 件）
- **delete した箇所は計 3**: 他節と重複する bullet 2（分類表 行 1・行 2 の再掲）/ 旧形式の例示 1（多段 hotfix の 5 行）
- **relocate: 0**（移送先を持たない。削った内容はすべて archive 原本で参照可能）
- 削減内訳: -20 行 = 重複 bullet -2 / Express 昇格の集約 -10 / 旧例の削除 -5 / Diff Routing の集約 -3

## 検証結果

| 項目 | 結果 |
|---|---|
| アンカー全数照合（597 件 / 被覆修正後） | `ALLOWED-MISSING (set 4)` 2 行 + `ANCHOR_VERIFY_OK: 597 anchors checked, 0 unexpected missing (2 allowed) in references/phase-progression.md` / exit 0 |
| 抽出の再現性 | `extract` 2 回実行で `anchors.txt` が `diff` 完全一致 |
| archive の同一性 | base commit `33cb8aa5` の原本と `diff -q` バイト同一 |
| 照合器の RED 確認（蒸留前 / 実アンカー 1 件除去） | `MISSING (set 1): # Phase Progression` / `1 missing anchors (checked 536)` / exit 1（被覆修正前の分母で実施） |
| 被覆修正の再現テスト（字下げフェンス fixture） | 修正前は字下げフェンス内の契約行削除を検出できず `ANCHOR_VERIFY_OK` / exit 0。修正後は `MISSING (set 1/3/4)` 3 件 / exit 1。忠実な candidate は修正後も exit 0 |
| 承認済み例外の fail-closed 性 | 3 件目の実削除は `--allow-missing` があっても `MISSING (set 5)` / exit 1。宣言だけあって実際は欠落していない stale 例外は `allow-missing mismatch` / exit 1。`--allow-missing` 未指定なら 2 件とも通常の `MISSING` / exit 1 |
| 照合器の RED 確認（蒸留後 / 実アンカー 1 件除去） | `MISSING (set 1): ## Diff Routing（差し戻し先）` / exit 1 |
| `grep -F` masking の総当たり（advisory） | 規範語彙を含む 87 行を 1 行ずつ削除して全アンカー包含を再判定 → **検出されずに削除できる行は 0 件** |
| `bash tests/validate-plugin.sh` | exit 0 |
| `python3 -m pytest tests/ -q` | 790 passed, 607 subtests passed（baseline と同値）/ exit 0 |

## flag（衝突・注意）

1. **§ Same-Session Correction Rule の重複 bullet 2 件の削除**は、本蒸留で唯一「route 対応の記述行を消した」処置。削除した 2 行の内容（`既存 AC 内の不具合修正 / テスト失敗修正 → implementation_fix_only / gdd-systematic-debugging`、`reviewer 指摘対応（既承認 AC 内）→ gdd-pr-review-followup`）は同一章の Active Session Follow-up Classification 表 行 1・行 2 に逐語で残っている。ただし削除した bullet には「E2E で見つかった bug」「PR レビューコメント対応」という言い換えの語が含まれており、これらの語自体は本ファイルから消えている（`E2E` 起点の扱いは § E2E Discovery Loop、PR レビューコメントは § Post-PR / Post-Merge Contract 3 が別途所有）。AC-3 の重点確認箇所。
2. **§ Express → standard 昇格の集約**（14 行 → 4 行）は、`state-machine.md` § Express 昇格時の state ロールバック規則（T-2 で 71 行すべて keep 済み）と重複する説明の削減。集約時に **原本に無いフィールド（`Fix Attempts` / `Root Cause Tag` / `Scope Drift Counter` 等）を書き足さないこと**を明示的に確認した（下書き段階で一度書き足しかけたが、原本に無い記述の追加＝ Wave 0 型の捏造にあたるため撤回した）。集約後も原本の 7 フィールドの名前・値・「現在値を維持」「存在する場合は削除」の条件はすべて逐語で残っている。AC-3 の重点確認箇所。
3. **多段 hotfix の旧例の削除**: 削除した例は `Origin Steering: .steering/20260301-feat-A/` という **value grammar 確定前の形式**（`local:` prefix なし・`Origin Resolution Status` なし）であり、同節の 20 行後で定義される 4 形式の grammar と表記が食い違っていた。残した例（hotfix-3 の例）は grammar 準拠の完全形。したがってこの削除は重複例示の除去であると同時に、原本にあった表記の不整合を 1 件解消している。**原本の記述を「修正」した唯一の箇所ではない**（残した側の記述は一切変更していない）が、原本にあった 2 例のうち片方だけを残す判断であることを明示しておく。
4. **§ Diff Routing の 4 bullet → 1 行集約**: 4 つの `route → 復帰先` 対応はすべて逐語で残したが、リスト形式が失われている。この節は Escalation Decision Table の「復帰先」列の要約であり、独自情報を持たない。逐語照合で「構造が変わった」と判定されうる箇所として明示する。
5. **原本に既存の stale 参照を発見（本蒸留では未修正）**: § Batch-Hotfix Bridge Contract Case 1 rule 3 の「`state-machine.md` L208 の clear 条件に…」という **行番号による他ファイル参照**は、base commit `33cb8aa5` の時点で既に指す先がずれている（base tree の `state-machine.md` L208 は `Operation Level` の記述）。T-2 の蒸留（841 → 792 行）でさらにずれるが、**原因は本 Wave ではなく原本の時点で既に stale**。行番号参照は本来 § 見出し参照にすべきだが、承認 scope 外の内容変更になるため本タスクでは修正せず flag として記録する。
6. **削減幅が小さい（-2.9% 行 / -1.2% tokens）**。本ファイルは 535 非空行のうち 152 行がアンカーで完全固定され、残りも route 語彙・数値閾値・worklog / state.md の記録スキーマ・fail-closed 分岐という low freedom 契約が大半を占める。長文（100 字超）の非アンカー行 78 行を全数点検したが、そのほとんどが field 名・stop reason・優先順位・retry 回数を含む運用契約であり、圧縮すると契約が痩せる。先行対象 `state-machine.md`（-5.8%）と同じ構造的理由であり、削減率を稼ぐには契約本文を削るしかないためこの着地を正とする。S-3 のバジェット引き下げでは本ファイルの寄与を過大評価しないこと。

## T-3b 構造修正後の再抽出・再照合（2026-07-30）

照合器を bash から Python 単一実装（`docs/audits/r9-2-anchor-tools.py`。design.md D-B2 / adr.md ADR-10）へ書き直したため、本対象の AC-1 証跡を新ツールで再現した。

**旧ツールの blob sha（本シートの上記コマンド列を実行した実体）**: `docs/audits/r9-2-anchor-tools.sh` = `893d39a2d949dfb8b47fc7e73225fa9a8fea009d`（commit `f449a84` 時点。T-3b で削除）。
上記 § 抽出コマンド列の `.sh` invocation は **旧ツールで実行したものとして保持**する。以降の再実行は下記 `.py` invocation を正とする。

```bash
rm -rf /tmp/r9-2-base-tree && mkdir -p /tmp/r9-2-base-tree
git archive 33cb8aa5f448724ed4510b86d03dcd40af4a9ea8 | tar -x -C /tmp/r9-2-base-tree

python3 docs/audits/r9-2-anchor-tools.py selftest

python3 docs/audits/r9-2-anchor-tools.py extract \
  --base-tree /tmp/r9-2-base-tree/plugins/gate-driven-development \
  --target references/phase-progression.md \
  --archive docs/references-archive/phase-progression-pre-r9-2-wave1-original.md \
  --out docs/audits/r9-2-phase-progression-anchors-v2.txt

python3 docs/audits/r9-2-anchor-tools.py compare \
  --old docs/audits/r9-2-phase-progression-anchors.txt \
  --new docs/audits/r9-2-phase-progression-anchors-v2.txt

python3 docs/audits/r9-2-anchor-tools.py verify \
  --anchors docs/audits/r9-2-phase-progression-anchors-v2.txt \
  --candidate references/phase-progression.md \
  --allow-missing docs/audits/r9-2-phase-progression-allowed-missing-v2.txt
```

**凍結と v2 の役割分担**: `docs/audits/r9-2-phase-progression-anchors.txt`（blob `de460be19d2ae3d60abca906e0cbaba18a51a726` / 597 件）と `docs/audits/r9-2-phase-progression-allowed-missing.txt`（blob `6224415074dd124af46979c6881d8e4a7b1121a7` / 2 件）は AC-1 の証跡として**凍結し上書きしない**。`-v2.txt`（JSON）が以後の verify の正本で、凍結 `.txt` は `compare --old` の入力専用。allow list の JSON 化では旧ファイルのコメント記法で書いていた削除理由を各エントリの `reason` フィールドへ逐語で移した（情報は失っていない。コメント記法自体を持たないため、F-2 の「`#` 始まりアンカーの非対称」は表現できない）。

### `selftest` 出力（R1〜R21。抽出前に実行し fail-closed を確認）

```
R1: PASS (missing anchors manifest -> VerifyFailed)
R2: PASS (empty and truncated manifests -> VerifyFailed)
R3: PASS (tampered counts/total -> VerifyFailed)
R4: PASS ('## SET 2' is an anchor, not a delimiter)
R5: PASS (indented heading in set 1)
R6: PASS (lowercase 'step 4' and 'Step 12b' in set 2)
R7: PASS (indented fence content in set 4)
R8: PASS (referencing-md indented heading and .py literal in set 3)
R9: PASS ('#'-prefixed allow entry counted in declared and used (1 allowed))
R10: PASS (stale allow declaration -> VerifyFailed)
R11: PASS (unapproved deletion + stale declaration -> VerifyFailed)
R12: PASS (faithful candidate -> VerifyOk (15 checked))
R13: PASS (undeclared empty set -> ToolError from extract)
R14: PASS (declared empty set extracts and verifies)
R15: PASS (cross-set duplicate (1 anchors) keeps total intact)
R16: PASS (CLI exit codes 2/2/0/1 as expected; dispatch table complete)
R17: PASS (legacy reader keeps '#'-prefixed anchors and enforces header counts)
R18: PASS (wrong base tree (extract) and sha mismatch (verify) both fail closed)
R19: PASS (all-empty manifest (total=0) -> VerifyFailed (condition 2 is the sole guard))
R20: PASS (case-only difference -> VerifyFailed (present() is case-sensitive))
R21: PASS (nested quote token extracted into set 3 (quote types scanned independently))
round-trip: PASS (extract -> write -> read gives identical sets)
SELFTEST_OK: 22 cases passed
```

### `compare` / `verify` 出力

```
ANCHOR_EXTRACT_OK: 597 anchors (set1=44 set2=3 set3=380 set4=83 set5=87) -> docs/audits/r9-2-phase-progression-anchors-v2.txt
compare: old declares 597 anchors (set1=44 set2=3 set3=380 set4=83 set5=87), read 597
compare: new has 597 anchors (set1=44 set2=3 set3=380 set4=83 set5=87)
ANCHOR_COMPARE_OK: old (597) is a subset of new (597); net gain 0
ANCHOR_VERIFY_OK: 597 anchors checked, 0 unexpected missing (2 allowed) in references/phase-progression.md
```

| 項目 | 値 |
|---|---|
| 旧 anchors.txt blob sha | `de460be19d2ae3d60abca906e0cbaba18a51a726` |
| 旧 allow list blob sha | `6224415074dd124af46979c6881d8e4a7b1121a7` |
| 旧件数 | 597（44 + 3 + 380 + 83 + 87） |
| 新件数（`-v2`） | 597（44 + 3 + 380 + 83 + 87） |
| `compare` 結果 | `ANCHOR_COMPARE_OK`（旧集合 ⊆ 新集合 / net gain 0 = 集合として完全一致） |
| `verify` 結果 | `ANCHOR_VERIFY_OK` 597 件照合 / 承認済み 2 件以外の欠落 0 / exit 0 |

**Amendment 1（2026-07-30）後の再実行**: SET 3 の引用符走査を独立走査へ変更した後（design.md D-B2 Amendment 1 / T-3b impl-gate F-3）も、本対象は **SET 3 = 380 件で完全に不変**（回収 0 / 喪失 0）。上表の値・`compare` の net gain 0・`verify` の結果はいずれも変化しない。`-v2` manifest もバイト同一。

### F-2（`handoff/t-3-impl-gate.md` High）の実測 2 ケースの再現

旧 bash 版では 2 ケースとも `ANCHOR_VERIFY_OK` / exit 0 に倒れていた（`handoff/t-3b-tdd.md` に実測を逐語記録）。新実装で同じ操作を再実行した結果:

| ケース | 操作 | 旧 `.sh` | 新 `.py` |
|---|---|---|---|
| (a) stale 宣言 | 候補に**実在する**見出し `## Diff Routing（差し戻し先）` を allow list に宣言 | `ANCHOR_VERIFY_OK ... (2 allowed)` / **exit 0** | `STALE-ALLOW: ## Diff Routing（差し戻し先）` → `ANCHOR_VERIFY_FAILED: allow-missing declaration mismatch: 1 stale declaration(s)` / **exit 1** |
| (b) 未承認欠落 + stale 宣言 | 同見出しを候補から実削除し、`#` 始まり宣言 1 行 + カウント合わせの stale 宣言 1 行を追加 | `ANCHOR_VERIFY_OK ... (3 allowed)` / **exit 0** | `STALE-ALLOW: STALE_LINE_TO_BALANCE_COUNT` → `ANCHOR_VERIFY_FAILED: allow-missing declaration mismatch: 1 stale declaration(s)` / **exit 1** |

構造的な理由: allow list は**パース済みリスト 1 本**で、`declared` と `used` は同一オブジェクトから派生する（`used ⊆ declared` が構造的に成立）。突合は件数比較ではなく**集合等価**なので、旧実装が持っていた「照合は `grep -qxF`、宣言カウントは `grep -cvE '^[[:space:]]*(#|$)'`」という**同一ファイルを別ルールで読む非対称**が表現自体できない。`#` 始まりのアンカーに特別扱いは存在しない。

**`compare` の被覆低下検出（本番判定前の RED 確認）**: `-v2` manifest から SET 1 のアンカー 1 件（`       # Root Stub for <root-name>`）を落としたダミーに対し `compare` を実行 → `COVERAGE-LOSS (set 1): ...` / `ANCHOR_COMPARE_FAILED: 1 old anchors are absent from the new manifest` / **exit 1**。被覆低下が fail-closed で検出されることを確認してから本番 superset 判定に使用した。
