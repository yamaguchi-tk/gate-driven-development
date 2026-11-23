# R9-2 Wave 1 監査シート: state-machine.md（2026-07-29 起票 / 2026-07-30 実施）

対象: `plugins/gate-driven-development/references/state-machine.md`（原本 841 行 / 推定 18,760 tokens）
着地: **792 行 / 推定 17,799 tokens（-49 行 / -5.8%、-961 tokens / -5.1%）**（**訂正 / 2026-08-01**: 初版の 17,796 は誤り。`ceil(len(text)/4)` で再計算すると全文基準 17,799 / body 基準 17,798。`state-machine.md` は frontmatter を持たないため両者の差は末尾改行 1 文字だけで、CHANGELOG / plan doc / PR の実績表が採る全文基準の 17,799 を正とする）
ルーブリック: keep（low freedom 契約）/ rewrite-to-intent（意図へ圧縮）/ delete（重複・歴史的経緯）/ relocate（原本退避で代替）
原本退避先: `docs/references-archive/state-machine-pre-r9-2-wave1-original.md`（蒸留コミットより前の archive コミットで git 管理下）
アンカー分母: `docs/audits/r9-2-state-machine-anchors.txt`（archive と同一コミットに固定）

## 抽出コマンド列（再実行で同じ分母が再現することを確認済み）

```bash
rm -rf /tmp/r9-2-base-tree && mkdir -p /tmp/r9-2-base-tree
git archive 33cb8aa5f448724ed4510b86d03dcd40af4a9ea8 | tar -x -C /tmp/r9-2-base-tree

docs/audits/r9-2-anchor-tools.sh extract \
  --base-tree /tmp/r9-2-base-tree/plugins/gate-driven-development \
  --target references/state-machine.md \
  --out docs/audits/r9-2-state-machine-anchors.txt \
  --expect-empty 4

docs/audits/r9-2-anchor-tools.sh verify \
  --anchors docs/audits/r9-2-state-machine-anchors.txt \
  --candidate references/state-machine.md
```

実行 cwd: 上記は `plugins/gate-driven-development` を cwd として実行する（パスが相対のため）。誤った cwd から実行した場合、`verify` は `ANCHOR_VERIFY_FAILED: anchors not found: ...` / exit 1 で fail-closed する。

再現性: 同一コマンドを 2 回実行し、出力 `anchors.txt` が `diff` で完全一致することを確認（`REPRODUCIBLE_OK`）。

## 保存必須の契約（蒸留後も維持したもの）

アンカー全数照合の分母と結果:

| 集合 | 内容 | 件数 | 蒸留後の欠落 |
|---|---|---|---|
| SET 1 | 見出し行（`^[ \t]*#{1,6} ` 全行。字下げ見出しを含む） | 39 | 0 |
| SET 2 | `[Ss]tep <数字>` 番号体系（小文字始まりを含む） | 2 | 0 |
| SET 3 | 外部被参照文字列（base tree `33cb8aa5` の `tests` / `hooks` / `scripts` / `skills` / `references` / `commands` / `agents` から逆引き） | 535 | 0 |
| SET 4 | コードフェンス内の全行（フェンス判定は `^[ \t]*` + バッククォート 3 個。字下げフェンスを含む） | **0（expected-empty）** | 0 |
| SET 5 | 規範表現・数値閾値を含む行 | 110 | 0 |
| 合計 | | **686** | **0** |

- **SET 4 が 0 件であることの事前宣言**: `state-machine.md` は原本にコードフェンスを 1 つも持たない（design.md § D-B の base 33cb8aa 実測と一致）。`--expect-empty 4` で宣言し、`anchors.txt` ヘッダに `# set4_count=0 (expected-empty)` として archive と同一コミットに固定した。ヘッダに宣言の無い集合が 0 件になった場合は `ANCHOR_EXTRACT_FAILED` で fail-closed する（骨抜き防止）。
- **`--expect-empty 4` 宣言の再検証（T-3 逐語照合レビュー F-1 対応 / 2026-07-30）**: 初版の抽出器はコードフェンスを **行頭アンカー限定**（行頭 + バッククォート 3 個）で判定していたため、「フェンス 0 件」の宣言が字下げフェンスの見落としを隠している可能性があった。抽出器を字下げ許容（`^[ \t]*`）に修正したうえで base tree `33cb8aa5` の原本を再検査した結果、**行頭・字下げ・チルダのいずれの形式でもフェンスは 0 件**（**訂正 M-1 / 2026-07-30**: 初版はここを「原本の backtick 出現数自体が 0」と記載していたが誤り。正しくは **三連 backtick のフェンスが 0 件**であり、単独 backtick を含む行は実測 494 行ある。`grep -c '\`' docs/references-archive/state-machine-pre-r9-2-wave1-original.md` = 494）であり、**`--expect-empty 4` の宣言は正しかった**ことを確認した。修正版抽出器で再抽出した `anchors.txt` は初版と **バイト同一**（SET 1〜5 の件数もすべて不変）で、`verify` も `ANCHOR_VERIFY_OK: 686 anchors checked, 0 unexpected missing (0 allowed)` / exit 0。**T-2 の AC-1 証跡は本修正の影響を受けない**。
- 個別に維持を確認した契約群:
  - state field 名と許容値の全列挙（`Requirements Review Status` / `Design Review Status` / `Human Check Status` / `Resume From` / `Next Action` / `Route In Progress` / `Refactor Gate Status` / `Post-Merge Follow-up Mode` / `Fix Attempts` / `Scope Drift Counter` / `Cumulative Diff Base` / `Root Cause Tag` / `Origin Steering` 系ほか）
  - 停止規律: 7 種の stop reason、`<gdd-stop reason="...">` マーカー、`参照した正本` / `停止理由` / `次の1アクション` の 3 点セット、fail-closed 条件の全文
  - 3-field gate check（`Requirements Review Status=approved` + `Design Review Status=approved` + `Human Check Status=approved`）とフォーマット検証ルール
  - 数値閾値: `Fix Attempts` 3 回、planning blocker `>=2`、Scope Drift 累積 4 回目、hotfix chain depth 5、`root-cause-investigation` の probe 最大 3 回、`Blocked Since` 24 時間超警告
  - 状態遷移表（express / standard 両方）の全遷移と `gdd-completion-check` の `Next Action` 許容値 6 行

## 節別判定

| 節 | 旧行数 | 新行数 | 判定 | 処置 |
|---|---|---|---|---|
| Header（所有 / 上位正本 / 参照元） | 13 | 13 | keep（軽圧縮） | 本文冒頭 1 行から、直後の § 契約境界 と重複する所有範囲の再掲を削除 |
| ## 契約境界 | 16 | 16 | keep | 正本分界そのもの。verbatim |
| ## Single Source of Truth（workflow phase） | 6 | 6 | keep | phase 正本と task identity 正本の定義。verbatim |
| ### 理由 | 4 | 4 | rewrite-to-intent | `workflow_phase` 二重保持の経緯を 1 文へ圧縮（結論の規範は保持） |
| ### 各ファイルの責務 | 10 | 10 | keep | 表は責務の正本 |
| ### Stop hook の判定順序 | 11 | 9 | delete | 末尾の `detected_phase` 注記が § 各ファイルの責務 の同内容と重複。判定順序 1〜3 と allowed stop reasons は verbatim 維持 |
| ### pre-brainstorming 期間の扱い | 6 | 6 | keep | `clarification-needed` の停止契約 |
| ### subagent の state 更新契約 | 4 | 4 | keep | read-back 契約。verbatim |
| ## state machine の外側 | 7 | 7 | keep | pre-workflow lane の非所有宣言 |
| ## 保存場所 | 47 | 41 | rewrite-to-intent | `worklog.md` の内容例 4 行を 1 行へ、`gdd-dev.local.md` / `binding.json` / `Verification` の単一子 bullet を親行へ畳む。保存先とルーティング非使用の宣言は全保持 |
| ## state field の意味 | 125 | 103 | rewrite-to-intent + delete | (a) `Human Check Status` と `Route In Progress` が同一節内で二重定義されていたのを 1 エントリへ統合。固有情報（`planning と build の境界判定（3-field gate check）に使う` / 両 field の `**active steering では必須**` fail-closed 行）は統合先へ逐語で移送した。統合で落ちたのは値の再掲 2 行のみで、`Human Check Status` の 3 値は § 許容値 に、`Route In Progress` の値列挙は同 field の既存 bullet と § 許容値 に、`remediation 完了時または terminal 遷移時に none に戻す` は同 field の `route の修正が完了し次の phase に進んだ時点で none にクリアする` と遷移表の ※ 注記に、それぞれ同義の記述が残っている(b) 各 field の先頭説明 bullet を field 行へ畳む（16 field）(c) `Why: iteration N findings #...` の歴史的経緯 2 件を delete (d) `Refactor Gate Status` の Express 非適用が § 許容値 と重複するため delete |
| ## 許容値 | 104 | 102 | keep | 値の全列挙は契約テストの grep 対象。歴史的経緯 2 行のみ delete、値・必須項目・遷移規則は verbatim |
| ### state field のフォーマット検証 | 14 | 14 | keep | パイプ区切り検証と 3-field gate check。verbatim |
| ## 状態遷移一覧（quick express） | 20 | 20 | keep | 遷移表は契約 |
| ### Express 昇格時の state ロールバック規則 | 71 | 71 | keep | 昇格 2 契機・フィールド更新表・段階 1/段階 2 の順序・code artifact 扱いはすべて low freedom 契約。Why 4 件はいずれも規範文（SET 5）に該当するため verbatim 維持 |
| ### Task Size 再評価マトリクス | 36 | 34 | keep（例示のみ delete） | 再入契機表・責務主体・降格禁止の原則は verbatim。降格禁止を言い換えただけの例示 1 件を delete |
| ## 状態遷移一覧（quick standard / standard） | 52 | 40 | rewrite-to-intent | 5 phase（design-gating / task-breakdown / TDD / subagent-impl / systematic-debugging）× 3 route の 15 行が、遷移先 5 列すべて同値の反復だったため 3 行へ集約。集約行に 5 phase 名を逐語列挙し、どの phase からの検知かは表から読み取れる状態を維持（**flag 1 参照**） |
| ### gdd-completion-check の `Next Action` 許容値 | 15 | 15 | keep | fail-closed 制約。verbatim |
| ## Remediation Loop Safety | 8 | 8 | keep | blind loop 禁止と route recalibration |
| ## Planning Loop Safety | 8 | 8 | keep | 閾値 `>=2` と停止条件 |
| ## entry intent の決定規則 | 13 | 13 | keep | 全行がアンカー |
| ## active steering の決定規則 | 31 | 31 | keep | resolver の 4 段（hard exclude → hard match → soft score → conflict）と candidate 3 分類 |
| ## Resume 正本の切り替え | 9 | 9 | keep | 正本切替の分岐 |
| ## Resume 時の再開ルーティング | 11 | 9 | rewrite-to-intent | 直前節と重複する build / planning candidate の正本再掲 2 行を親行へ畳む。merge 済み PR の分岐（fail-closed）は verbatim |
| ## Resume 時の state 整合性検証 / ### 検証項目 / ### 不整合検出時の対応 | 26 | 26 | keep | 整合性ルール全 7 件と自動修復禁止 |
| ## 停止時の返答契約 | 12 | 12 | keep | 停止時 3 点セット |
| ## Autonomous Continuation | 9 | 9 | keep | 7 stop reason とマーカー契約 |
| ### Goal-Driven Loop Ownership | 22 | 22 | keep | outer / inner loop の所有境界 |
| ## ユーザー起点の中止（Cancel） | 8 | 8 | keep | terminal 遷移 |
| ## planning 差し戻し後の tasklist.md リセット | 19 | 18 | rewrite-to-intent | 末尾 2 行の目的説明を 1 行へ。`design_detail_only` / `human_recheck_required` のリセット範囲は verbatim |
| ## planning 差し戻し時の code artifact 扱い（+ 4 サブ節） | 31 | 31 | keep | revert / discard / stash drop 禁止の表と適用除外 |
| ## tasklist.md の canonical state | 17 | 17 | keep | セクション構成と `Fix Attempts` 契約 |
| ## 更新責任 | 57 | 57 | keep | 各 skill の所有 state。**flag 2 参照** |

## 判定集計

上表は 33 行で 39 見出しすべてを覆う（`Resume 時の state 整合性検証` 行が 3 見出し、`planning 差し戻し時の code artifact 扱い` 行が 5 見出しを含む）。

- **keep: 26 行**（契約・許容値・遷移表・停止規律・fail-closed 条件）
- **rewrite-to-intent: 6 行**（`### 理由` / `## 保存場所` / `## state field の意味` / standard 遷移表 / `## Resume 時の再開ルーティング` / tasklist リセット）
- **delete が主判定: 1 行**（`### Stop hook の判定順序` 末尾の重複注記）
- **delete した箇所は計 7**（節ごとの削除は 0）: 同一節内の二重定義 2（`Human Check Status` / `Route In Progress`）/ 歴史的経緯 2（`Why: iteration ...`）/ 他節と重複する注記 2（`detected_phase` / `Refactor Gate Status` の Express 非適用）/ 言い換えだけの例示 1（降格禁止）
- **relocate: 0**（本ファイルは移送先を持たない。削った内容はすべて archive 原本で参照可能）

## 検証結果

| 項目 | 結果 |
|---|---|
| アンカー全数照合（686 件） | `ANCHOR_VERIFY_OK: 686 anchors checked, 0 unexpected missing (0 allowed)` / 欠落 0 件（impl-gate remediation 後・被覆修正後にそれぞれ再実行し同値） |
| 被覆修正後の再抽出（F-1 対応） | 修正版抽出器で再抽出した `anchors.txt` が初版と `diff` バイト同一。原本のフェンスは行頭・字下げ・チルダのいずれも 0 件で `--expect-empty 4` は正当 |
| 照合器の RED 確認（合成 fixture） | `MISSING (set 1): THIS_STRING_DOES_NOT_EXIST_IN_CANDIDATE` / exit=1 |
| 照合器の GREEN 確認（実在文字列 fixture） | `ANCHOR_VERIFY_OK: 1 anchors checked, 0 missing` / exit=0 |
| fail-open 回帰 RED（anchors 不在 / ヘッダ残骸 / 本体 0 件 / 宣言件数不一致 / `## SET UP ...` 内容行） | 5 件とも `ANCHOR_VERIFY_FAILED` / exit=1 |
| extract 失敗時の既存 anchors.txt 保全 | `--expect-empty 4` 省略で exit=1、既存ファイルの sha1 不変・一時ファイル残骸 0 |
| 蒸留版から 1 アンカーを削った fixture | `MISSING (set 1): # State Machine（正本）` / exit=1 |
| `bash tests/validate-plugin.sh` | exit 0 |
| `python3 -m pytest tests/ -q` | 790 passed, 607 subtests passed（baseline と同値） |

## flag（衝突・注意）

1. **状態遷移表の 15 行 → 3 行集約は、本蒸留で唯一「表の行を消した」処置**。5 列すべてが同値の反復であり意味の欠落はないが、`gdd-task-breakdown で \`design_detail_only\` を検知` のような「phase 名 + route」の逐語行は表から消えている（集約行に 5 phase 名を列挙して補償）。アンカー照合・契約テストはいずれも通過したが、逐語照合で「手順の順序・依存関係が変わった」と判定されうる唯一の箇所なので、AC-3 の重点確認対象として明示しておく。
2. **`## 更新責任`（57 行）は圧縮していない**。`planning_rework_required` なら `gdd-brainstorming`、`human_recheck_required` なら `human-check-waiting`、`design_detail_only` なら `gdd-design-gating` に戻す、という同一行が 4 skill 分（`gdd-design-gating` / `gdd-task-breakdown` / TDD+impl / `gdd-systematic-debugging`）反復しており、共通注記へ factor すれば -3 行できる。ただし per-skill の所有宣言を共通注記へ移すと「その skill がこの route を持つ」という個別契約が薄まるため、**判断に迷った節は削らない**方針に従い現状維持とした。
3. **アンカー分母の非対称**: SET 5 は「規範表現を含む行」を全行ロックするため、`Why:` で始まる歴史的経緯であっても `しない` 等を含めば保存必須になる（例: `Scope Drift Counter` の `Why: iteration 2 findings #12`）。一方、同種の `Why: iteration 12 finding N12-a` / `iteration 2 findings #1` は語彙が外れるため delete できた。**同じ性質の記述で保存/削除が割れている**のはアンカー機構の副作用であり、意図的な意味判断ではない。
4. **抽出ツールの欠陥を実装中に 2 件修正した**（いずれも `extract` / `verify` を本番適用する前に検出・修正済み）:
   - (a) `extract` の走査ループ内で、マッチ 0 件の `grep` が `set -euo pipefail` により途中終了を起こし、集合 (3) の走査が silent に打ち切られていた。`|| true` で修正。
   - (b) `verify` が「`#` で始まる行はコメント」として読み飛ばしていたため、**SET 1（見出し 39 件）と SET 5 の見出し行が 1 件も照合されない fail-open** になっていた。ヘッダ領域（最初の `## SET` より前）のみコメント扱いするよう修正し、見出しを 1 件書き換えた fixture で `MISSING (set 1)` が出ることを確認した。修正版は archive コミットに含めている（T-3 以降も同じ修正版を使う）。
5. **impl-gate（impl-gate-20260730-2）で fail-open をさらに 3 件塞いだ**（`handoff/t-2-impl-gate.md` Finding 1〜3）。いずれも「検査が走っていないのに pass を返す」型:
   - (a) `verify` が anchors ファイル不在でも `ANCHOR_VERIFY_OK` / exit 0 を返していた（`done < "$ANCHORS"` のリダイレクト失敗は `set -e` で止まらない）。存在検査を追加。
   - (b) `extract` が `$OUT` に直接リダイレクトしていたため、`ANCHOR_EXTRACT_FAILED` の exit で既存 anchors.txt がヘッダ数行に truncate され、その残骸を `verify` が 0 件照合で pass させていた。同一ディレクトリの一時ファイルへ書き切ってから `mv` する atomic write に変更し、`verify` 側にも「照合件数 0 件は fail」「ヘッダの `# setN_count=` 5 行の合計と実照合件数の一致」を追加。
   - (c) `## SET ` の前方一致がラベル 1〜5 に限定されておらず、`## SET UP ...` のような内容行がマーカーに誤認されて無言で照合対象から外れていた。「次に来るべきマーカーとの完全一致」に変更。
   - **`verify` の成功出力は `ANCHOR_VERIFY_OK: <N> anchors checked, 0 missing` 形式になり、0 件照合と成功が出力上区別できる**。T-3 以降は照合件数が期待値と一致することを毎回目視する。
6. **削減幅が小さい（-5.8%）**。本ファイルは 713 非空行のうち 277 行がアンカーで固定され、残りの大半も遷移表・許容値列挙・fail-closed 条件という low freedom 契約である。他 references と重複する説明・過剰な例示・冗長な背景散文が構造的に少なく、Wave 0 の `brainstorming-steps.md`（-73%）のような圧縮余地は存在しない。**削減率を稼ぐには契約本文を削るしかなく、それは AC-1 と本 Wave の目的に反する**ため、この着地を正とする。S-3 のバジェット引き下げでは本ファイルの寄与を過大評価しないこと。

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
  --target references/state-machine.md \
  --archive docs/references-archive/state-machine-pre-r9-2-wave1-original.md \
  --expect-empty 4 \
  --out docs/audits/r9-2-state-machine-anchors-v2.txt

python3 docs/audits/r9-2-anchor-tools.py compare \
  --old docs/audits/r9-2-state-machine-anchors.txt \
  --new docs/audits/r9-2-state-machine-anchors-v2.txt

python3 docs/audits/r9-2-anchor-tools.py verify \
  --anchors docs/audits/r9-2-state-machine-anchors-v2.txt \
  --candidate references/state-machine.md
```

**凍結と v2 の役割分担**: `docs/audits/r9-2-state-machine-anchors.txt`（blob `7729997b531b197f266a200b293e3eef1f79a90e` / 686 件）は AC-1 の証跡として**凍結し上書きしない**。`-v2.txt`（JSON）は「被覆が下がっていないことの再検証記録」であり、**以後の verify は `-v2` を正**とする（凍結 `.txt` は `compare --old` の入力専用）。

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
ANCHOR_EXTRACT_OK: 687 anchors (set1=39 set2=2 set3=536 set4=0 set5=110) -> docs/audits/r9-2-state-machine-anchors-v2.txt
compare: old declares 686 anchors (set1=39 set2=2 set3=535 set4=0 set5=110), read 686
compare: new has 687 anchors (set1=39 set2=2 set3=536 set4=0 set5=110)
ANCHOR_COMPARE_OK: old (686) is a subset of new (687); net gain 1
ANCHOR_VERIFY_OK: 687 anchors checked, 0 unexpected missing (0 allowed) in references/state-machine.md
```

| 項目 | 値 |
|---|---|
| 旧 anchors.txt blob sha | `7729997b531b197f266a200b293e3eef1f79a90e` |
| 旧件数 | 686（39 + 2 + 535 + 0 + 110） |
| 新件数（`-v2`） | **687**（39 + 2 + **536** + 0 + 110） |
| `compare` 結果 | `ANCHOR_COMPARE_OK`（旧集合 ⊆ 新集合 / net gain 1 = 被覆が 1 件増えた） |
| `verify` 結果 | `ANCHOR_VERIFY_OK` 687 件照合 / 欠落 0 / exit 0 |

**net gain 1 の意味**: `compare` が旧 ⊆ 新を確認したうえで SET 3 が 1 件増えている。増えた 1 件は `SessionStart` で、交替走査のペアリング事故により旧実装が取りこぼしていたアンカーの**回収**である（design.md D-B2 Amendment 1 / T-3b impl-gate F-3）。**被覆低下ゼロかつ喪失ゼロ**で、分母は旧実装の真上位集合。回収した `SessionStart` は蒸留後の `state-machine.md` にも 8 箇所残存しているため、T-2 の照合結果（欠落 0）は無効化されない。

**移植で意図的に逐語再現した挙動 / 訂正した挙動**:

- **逐語再現（維持）**: SET 3 の候補抽出は旧 `grep -ohE` の**バイト単位**セマンティクス（C ロケールで `{3,}` がバイト数を数える）をバイト列上の正規表現で再現している。Python の文字数勘定へ素直に置き換えると引用符のペアリングが 1 つずれ、`新しい` のように旧集合に含まれていたアンカーが静かに落ちること（under-extraction の再導入）を実測で確認したため。
- **訂正（Amendment 1 / 2026-07-30）**: 初版はここに「引用符種別ごとに独立走査する読み方の改善も行わない（実測で `の場合、` のような文法断片が新規に混入したため）」と記載していたが、**この却下理由は再測で成立しない**。`{3,}` と改行除外を維持した**最小の独立走査**では、8 対象すべてで**喪失 0 件・回収 3 件**（`state-machine` の `SessionStart` / `requirements-template` の `### 一言` と `` - `Resume From=human-check-waiting` ``）であり、ノイズ混入は再現しない。ノイズが出るのは下限と改行除外を外した別の広い変種（`"[^"]*"` / `'[^']*'`）で、そちらは `戻す条件` を新規に入れる（この広い変種は引き続き不採用）。よって **SET 3 は引用符種別ごとの独立走査へ変更した**。
