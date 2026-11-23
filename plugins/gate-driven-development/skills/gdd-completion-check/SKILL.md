---
name: gdd-completion-check
description: "Internal: auto-routed only when Next Action=gdd-completion-check. Verifies completion evidence before done or PR handoff."
version: 0.1.1
---

# Completion Check

完了宣言の前に、AC ごとの確認と最後の包括レビューを閉じる。Claude Code の main セッションで、この gate を回すためにこの手順を読んでいるとき（Skill ツール・slash コマンド・Read のどれで開いても）は、ここで実行しない。`references/subagent-dispatch.md` § Completion-Check Template を Read・置換して `gate-driven-development:gdd-formal-gate-runner` に dispatch する（`gdd-formal-gate-runner` の中で読んでいるなら、このまま続ける。Codex・Cursor には、この段落は当てはまらない）。
- どの runtime でも、gate を実行した側（gate runner。inline 実行なら main。main が gate runner を時間上限・エラーで止めて出口を決めたときも main。worker 経由なら結果を統合する main で、worker 自身は書かない）は、Round の判定を決めた後に `worklog.md` へ `gate結果:` 行を 1 行足す（正本: `references/subagent-dispatch.md` § Subagent Return Output Contract）。

## Goal

- `tasklist.md` の `Verification` を正本として埋める
- `gdd-completion-reviewer` で最終の横断レビューを行う
- reviewer selection record の欠落や不整合を残さない
- 未解決の review / debug / verification failure を残さない
- 条件を満たす場合は最終的な `Next Action` を `done` または `cancelled` にし、差し戻し時は `gdd-systematic-debugging` に戻す
- `Next Action` は **`tasklist.md` / `state.md` の行頭に**（bullet marker は `- ` 1 個まで）書く。インデントした行は field として読まれない。過去の `Next Action` に言及する履歴・経緯メモは**入れ子 bullet（先頭 2 スペース以上）**にする — 行頭に置くと本文の履歴が現在値として読まれ、`gh pr create` が古い値で block される（`references/state-schema.json` § `canonical_line_form` が正本）
- 外部前提不足だけが blocker のときは `Next Action=gdd-completion-check` のまま再試行可能にする
- advisory companion review（`gdd-requesting-code-review`）は補助証跡として扱い、formal gate と混同しない
- prompt / skill / review policy / 人間向け出力を変更した standard タスクでは、必要に応じて dialectic review lane の evidence を確認し、最終成果物の読みやすさ・severity calibration・採否判断の揺れを completion 前に収束させる
- required external security evidence を `Verification` に残さず `done` に進めない
- mandatory refactor checkpoint の証跡を `Verification` に残さず `done` に進めない
- 全タスク完了後の `Refactor Gate Status` を横断リファクタ点検の証跡として確認し、実施結果または省略理由を completion output に明示する
- `Verification` の固定 schema を崩さない
- `Approved Direction` / 承認済み AC / 実際の diff / tasklist evidence の対応が取れないまま `done` に進めない
- human check 承認後の自走フローにおける最後の formal gate として、後続の人手 spot-check を前提にしない

## Fixed Model

`references/fixed-models.md` を参照（Claude Code: `opus` + `effort=high` / Cursor: `Grok 4.6` + `medium` / Codex: `gpt-5.6-sol` + `medium` 固定。理由: `done` 判定の最終 gate）。Cursor 環境の詳細は `references/cursor.md`。

## Verification Delegation

`Verification` field の schema、許容 status、Fresh Verification Rule、Speculative Language 拒絶、Schema Validation は **`gdd-ac-verification`** が正本。本 skill は Part B（Steps 5〜11）で `gdd-ac-verification` を呼び、judgment と schema validation の結果を受け取って state 更新（`Next Action` / `Route In Progress`）と AC Drift Check / Stub Detection / External Dependency Check / Skill Quality Check を実行する。

呼び出し元として最低限知る境界だけをここに残す: AC 行は `pending` / `pass` / `fail` のみ、`status=pass` は evidence 必須、external security evidence は `N/A` / `unsupported` を取り得る。詳細な table / 禁句リスト / fail-closed 動作は `gdd-ac-verification` § Verification Schema / Schema Validation を参照し、本 skill 側で重複定義しない（drift 防止）。

AC 本文が要求する検証水準（E2E 必須・外部証跡必須と書かれた AC）を完了判定時の verification 期待値として扱う。E2E / 外部証跡を要求する AC を unit test だけで pass にしない。Yes/No で観測できない曖昧な AC が accepted のまま残っている場合は requirements schema issue として `human_recheck_required` または `planning_rework_required` に戻す。

## Completion Loop Safety

completion-check にも Round 上限・差分スコープ・記録 stale の非 blocker 化を適用する（数値と発動条件の正本は `references/state-machine.md` § Remediation Loop Safety）。カウンタは `Completion Rounds` / `Completion Baseline` の 2 field、差分の起点は `Completion Reviewed Through` で、保存先は 3 つとも **`tasklist.md`**（field 定義は `references/state-field-tiers.md` Tier 3）。**初回 Round 開始時に `Completion Baseline` へ `HEAD` を 1 度だけ記録し（既に行があれば上書きしない）、blocker を出して差し戻すたびに `Completion Rounds` を +1 したうえで `Completion Baseline` もその Round が使った `HEAD` へ更新し、Step 13 の `gdd-completion-reviewer` の出力が返った Round を差し戻すとき（Round 上限超過を含む）は、差し戻しの書き込みを終えた後に Step 13 で reviewer を起動する直前の `HEAD` を `Completion Reviewed Through` に上書きし（時間超過・エラーで返らないとき、書き込みを終える前に止まったときは書かない）、`Next Action=done` 到達時に 3 行とも削除する**（route reset と tasklist の作り直しでは削除しない）。手順の正本は `references/gate-checklists.md` § Checklist E の「Completion Rounds / Completion Baseline の操作手順」。

stale は 3 分類する（曖昧なら (iii) に倒す）: (i) evidence 鮮度不足 → `gdd-ac-verification` § Fresh Verification Rule で再実行（fail / 不能も blocker）。(ii) 記録が実態より古いだけ（`git log` / 本セッションで実行した検証コマンドの出力 / `Completed Tasks` の `Reviewed by:` 行の実在 の 3 観測のいずれかで反証できる場合のみ。human approval を完了条件に持つ route は常に (iii)）→ 自動更新して advisory。(iii) それ以外（記録欠落・実体未完了）→ 既定で blocker。Step ごとの割り当ては `references/gate-checklists.md` § Checklist E: Completion Stale Classification が正本。

2 回目以降の Round は `Completion Reviewed Through` 以降の差分と影響範囲だけを再検証し、通過済み箇所への新規指摘は advisory（新情報の根拠があるときだけ blocking へ昇格）。`Completion Reviewed Through` の欠落（Step 13 がまだ判定を返していない。差し戻しが Step 13 より前だった Round の後を含む）・解決不能 sha・`HEAD` の祖先でない（reset・rebase で commit が落ちた）、または再検証時に diff が空の場合は全量再検証（fail-closed）。差分スコープ再検証は前ラウンド未解消 blocker を対象外にしない。`## AC Trace Ledger Gate` / Implementation Gate Evidence Check / Part B の required external security evidence 判定（Step 8 / Step 10）は毎ラウンド全量実行する。Part C Step 19（外部前提不足だけが blocker の経路）と、Step 13 の reviewer が 2 回とも返らない経路は `Completion Rounds` の対象外。

Round 上限を超えたとき（Pre-PR loop の `Pre-PR Fix Attempts` の上限と、`references/independent-review.md` の (3-f) の取り直しの上限も同じ）は本 skill 自身が方式転換 4 択（task 撤回 / 再設計 / 依頼の範囲を変えるかを人に問う / 限界として開示して人に渡す）を提示してから停止する。各案に、選んだ後に PR を作れる見込み（completion-check を差し戻し無しで通れるか、その後の pre-PR gate の条件を満たせるか）を書き、4 つ目を置ける条件と選ばれた後の扱いは `references/rollback-patterns.md` § gdd-completion-check の Round 上限超過 に従う（出力手順と `Next Action` の逸脱理由は `references/rollback-patterns.md` § Downstream Human Recheck Handoff / § gdd-completion-check の Round 上限超過）。`## Self-Healing Verification Blocker`（検証詰まりを完了に変換しない逆方向の規律）とは別物 — 混同しない。

## AC Trace Ledger Gate

`references/ac-trace-ledger.md` を completion gate の補助正本として読む。accepted AC に対して AC Trace Ledger の行が無い場合は `unverified AC` として扱い、missing ledger row / status=unverified / status=failed / AC drift が残る限り completion を通さない。Ledger の行の有無・最後の行の status・検証コマンドの空欄は、Part B の後（Step 11 の後、Part C の前）に `check-completion-mechanical.py` を Step 0 と同じ引数に `--ledger` を足して回し、`ac-ledger` 行（gate 列 `completion-check:ledger`）で判定する（Step 0 の (a)〜(c) と error の規則を同じく当てる。missing・invalid ならこの節の不備。後続 Stage にだけ置いた AC は除く）。`ac-ledger` が missing（`ac-ledger.md` が無い）か、行が無い AC があるときは、Part B の `gdd-ac-verification` で得た fresh verification の結果から AC ごとに Ledger の行を `ac-ledger.md` の末尾に追記し（無ければ作る。`references/ac-trace-ledger.md` の形式）、`--ledger` を回し直す。この追記は Checklist E の (iii) の例外で、本セッションの Part B で pass した AC だけを、`last verified at/phase` を `gdd-completion-check @ <時刻>` にして書く。`ac-source` 行が invalid（AC か PR Boundary を閉じた形で読めない、`ac-ledger.md` に Ledger の表のほかの行がある、または tasklist.md・worklog.md の見出しに `AC Trace Ledger` が残っている。`ac-ledger.md` に置ける行は `references/ac-trace-ledger.md` § Append-Only Rule が正本で、それ以外の行〔注記・ほかの見出し・別の表・欄の数が合わない行・fence の行など〕はすべて当たる）なら、Step 0 の (c) によらず、gate が requirements.md と Ledger を読んでこの節を判定する。fresh evidence か・AC drift は gate が判定する。外部前提待ちや再検証待ちで閉じる場合は `Next Action=gdd-completion-check` のまま止め、done / clean / PR-ready と主張しない。

## HITL Outcome Audit

`requirements.md` の Approved Direction と最終成果物を照合し、HITL Outcome Audit を行う。以下の観点を `match / mismatch / unverified` で記録し、mismatch または unverified が残る場合は completion を通さない。

- 何を作るか
- どう作るか
- 何を完了とみなすか
- 確認すること
- 確認しないこと
- AIに任せる範囲
- AIが止まって人間に戻す条件

この確認は「この承認をきっかけに AI が自走した結果、期待どおりの結果になったか」を見るためのもの。Approved Direction から外れる場合は `human_recheck_required` または planning route に戻す。

## Evidence Before Claims

Evidence before claims. Completion uses fresh verification evidence before pass / clean / done claims.

superpowers `verification-before-completion` の規律を GDD completion gate に吸収する。**NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE** をこの skill の Iron Law とする。

Gate Function:

1. **IDENTIFY**: 「完了」「通った」「問題なし」「review clean」「PR 作成可」と言う前に、その claim を支える必要 evidence を列挙する。
2. **RUN**: 必要な test / lint / build / verifier / AC check を、このセッションで fresh に実行する（テストの結果は、`references/verification-before-completion.md` § Fresh の粒度の同じ起動の中の結果を使ってよい）。過去セッション・subagent 報告・CI summary だけを根拠にしない。
3. **READ**: exit code と出力を読み、失敗・skip・対象外を区別する。
4. **VERIFY**: `Verification` の `method/status/evidence/notes` と claim が対応しているか確認する。
5. **ONLY THEN**: evidence が揃った claim だけをユーザーに出す。証拠なしに成功表現を使わない。

以下は completion evidence ではない:

- subagent の `DONE` / `completed` 報告
- 以前のテスト pass（§ Fresh の粒度の条件を満たす同じ起動の中のテストの結果を除く。`references/verification-before-completion.md` § Fresh の粒度）
- CI green summary だけ（実行コマンド・対象・ログ未確認）
- 「たぶん動く」「問題なさそう」「実装は終わったと思う」

## Completion Branch Decision Menu
completion 後の 4 option（PR 作成 / このまま保持 / ローカル整理 / 破棄）、Worktree Provenance Gate、branch-only steering / Distill to ADR / Distill to Spec（機能仕様を `docs/specs/` に蒸留。main に置く例外は蒸留物（ADR / spec）のみ）、Raw Steering Exclusion Check の詳細は `references/post-completion-pr-flow.md` を正本として読む。
本 skill 側の責務は、fresh verification evidence が揃った後に option を選べる状態かを判定し、PR 作成を選ぶ場合は `gdd-pr-review` / `gdd-pr-review-followup` へ接続すること。merge / deploy / apply / release はこの menu に含めず、必要な場合は 1 操作ごとの明示承認を維持する。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける
- `done` に進めるかを説明するときは、`method` / `status` / `evidence` / `notes` の 4 field をまず列挙する。
- そのうえで `status` の 5 値（`pending` / `pass` / `fail` / `N/A` / `unsupported`）を明示し、AC 検証では `pending` / `pass` / `fail` だけを使うことまで答える。
- AC 検証の `status=pass` は `evidence` 必須だと明示する。
- 外部前提不足で止まる場合は、以下のフォーマットで明示する:

  ```
  ⚠ 外部前提が不足しています
  不足している evidence:
  - security_evidence:<kind> — <具体的に何が必要か>
  解消手順:
  1. <具体的なコマンドや操作>（例: `gh run list --branch <branch>` で CI status 確認）
  2. evidence が生成されたら `/gdd-dev 再開` で completion を再実行
  Next Action: gdd-completion-check（変更なし。外部前提の解消待ち）
  ※ code/debug failure ではないため gdd-systematic-debugging には戻しません
  ```

- 再実行時に前回と同じ blocker リストなら `blocked` で停止し、human に解消手順を再提示する。
- `blocked` で停止する際、`state.md` に `Blocked Since=<ISO 8601 timestamp>` を記録する（既に記録されていれば更新しない）。blocker が解消されて `blocked` 以外の状態に進んだ時点で `Blocked Since` を削除する。SessionStart hook はこの値を参照し、24 時間超の blocked に対して「長時間 blocked です。外部前提の解消状況を確認してください」と警告する。
- active な `/gdd-dev` run で terminal または blocked まで到達した場合は、最後の assistant text block に `<gdd-stop reason="done|cancelled|blocked">...</gdd-stop>` を 1 つだけ含めて Stop hook loop を外す。
- `done` に到達した場合は、`<gdd-stop>` を出す **前に** Post-Completion PR Flow（下記）を実行する。test 再実行 → 4 択提示（PR 作成 / 保持 / ローカル整理 / 破棄）→ 選択に応じた処理 →（PR 作成時は CI の待機と自動修正の後、Auto-Arm 有効時はさらにレビュー収束 clean 後、さらに Stage Continuation 発火時は継続後）→ `<gdd-stop reason="done">` の順で進める。auto mode で明示選択がない場合は PR 作成を既定とする。
- **Plan mode 遷移禁止**: completion-check 完了後に harness の Plan mode へ遷移しない。`Next Action` の許容値は `done` / `cancelled` / `gdd-completion-check`（外部前提待ち）/ `gdd-systematic-debugging`（差し戻し）/ `gdd-refactor-planning`（refactor pending）/ `gdd-implementation-gating`（impl-gate evidence 不足での再 gate）に固定する。これら以外（特に `plan` / `planning` / 空 / Plan mode 遷移指示）は state 不整合として fail-closed 停止する。**Why:** Cursor 等の harness 側で「複雑タスクは plan-mode へ」のデフォルトが効き、completion 直後に自走停止して人間に Plan-mode 入りを要求してしまう挙動が観測された。完了 gate は Post-Completion PR Flow（PR 作成 / 保持 / ローカル整理 / 破棄 4 択）で次アクションを必ず取り、Plan-mode に逃さない。

## Active GDD PR Creation Re-entry

active GDD で `Next Action=gdd-completion-check` の状態にあり、ユーザーが「PR作って」「PR作成して」「pushしてPR」「レビュー指摘がなくなるまでループして」と言った場合、この skill が workflow owner になる。これは PR 作成の明示承認であり、completion-check を省略する指示ではない。

この re-entry では以下を禁止する:

- status-only で「次は completion-check です」と説明して止まる
- `gdd-pr-review` だけを単独実行し、AC / drift / fresh verification / completion reviewer を飛ばす
- generic pr-lifecycle を primary workflow owner にして GDD state を更新しないまま PR 作成へ進む

必須動作:

1. `requirements.md` / `state.md` / `tasklist.md` を re-read し、`Next Action=gdd-completion-check` と current task identity を確認する。
2. Part A〜C（必要なら Part D）を実行し、fresh verification、AC Drift Check、completion reviewer、Post-Completion Learning を閉じる。
3. `Next Action=done` になったら `Post-Completion PR Flow` の Option 1 を既定として実行する。ユーザーが「PR作って」と言っている場合、4 択の再確認で止めず PR 作成へ進む。
4. `gh pr create` 前に Pre-PR `gdd-pr-review` loop を必ず通す。その後 `bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-gate-ledger.sh` で帳簿を検算し、gate 列に `pre-PR`・`completion-check`・`independent-review` のどれかを含む missing / invalid の行を解消してから `gh pr create` する（判定の述語は pre-PR gate と共有。pre-PR gate は止めずに不足をまとめて 1 本の通知にし、その通知は `gh pr create` の実行後に届くので、PR の前に検算で全部を直しておく）。証跡の行は、レビューを回し直してから書く（sha だけを書き換えない。default branch を取り込むだけの merge commit で Independent Review を引き継ぐときは、`references/independent-review.md` § 証跡 が指す引き継ぎの節のとおり、`Independent Review` の行は旧 sha のまま残して `Independent Review Carry` 行を足し、`Pre-Push Self Review`・`Pre-PR Self Review`・`Medium Disposition` の行は sha だけを merge sha に書き換えてよい）。`Reviewed by:` の欠落は Step 2a のとおり再 gate する。worklog.md へ移しただけの行は、そのまま戻す。
5. PR URL を取得したら `gdd-pr-review-followup` を起動し、レビュー指摘がある場合は fix -> push -> re-request review を繰り返す。レビュー指摘が無い、または初回取得時点で review が無い場合も state / worklog に evidence を残す。
6. `references/post-merge-qa.md` § 入口 の条件を満たすなら、PR 作成の後に `done` で戻る。マージ以降はメインセッションがその文書で続ける。それ以外で `Approved Direction` または `requirements.md` に `Post-PR Completion Scope` がある場合は Post-PR Scope Continuation に入る。`マージして再学習まで` のような明示承認済みの post-PR scope を `PR 作成まで` に丸めず、PR 作成後も done にしない。`merge / deploy / apply / AWS write` が必要で未承認なら、`1 操作ごとの明示承認` が必要な blocker として `<gdd-stop reason="blocked">` を出し、scope は消さない。
7. Post-PR Completion Scope が無く、CI の待機と自動修正（`references/post-completion-pr-flow.md` Option 1 手順 6）が終わり、Auto-Arm（`references/post-completion-pr-flow.md` 参照）が無効または収束完了（clean）済みで、かつ Stage Continuation が発火しない場合だけ、最終出力には PR URL と `references/post-completion-pr-flow.md` Step 4 の `記録の場所: なし` の行を含め、`<gdd-stop reason="done">` を 1 つだけ出し、その後に `## 👤 次にすること` を置く。PR 作成できない場合は blocker、未完了 task、次の1アクションを具体化し、`<gdd-stop reason="blocked">` で止める。

**Why:** brainstorm から GDD build に入った後、実装と gate は完了していても「PR作って」が status-only や generic pr-lifecycle に吸われると、PR 作成まで自動の期待が壊れる。`Next Action=gdd-completion-check` での PR 作成指示は、GDD の最終 gate と Post-Completion PR Flow への再入場として扱う。

## Self-Healing Verification Blocker

`verification blocker is not completion`。completion-check は、承認済み Stage の検証が詰まった状態を「完了」「自走済み」「PR 作成可」に変換してはならない。`runtime_timeout_or_repair_loop` / `execution_timeout_or_repair_loop` のように、評価 runner、fixture、repair loop、status artifact の問題で証跡が取れない場合も、その Stage は未達のまま扱う。**`## Completion Loop Safety` との関係**: 同節の (ii)（記録が実態より古いだけ）は記録の陳腐化を自動更新して advisory に落とす規律で、本節の「検証が詰まった状態は未達のまま」とは方向が逆 — 検証 blocker を stale 扱いにして advisory へ落とさない。

必須分類:

1. `fixable_within_scope`: approved AC / Stage の範囲内で直せる検証 blocker。例: timeout 上限、status artifact の早期出力、deterministic repair の retry 境界、fixture schema、local runner の不備。この場合は `route to gdd-systematic-debugging` とし、必要なら RED を `gdd-test-driven-development` へ戻してから同じ verification を再実行する。PR 作成には進まない。
2. external prerequisite: auth、tenant policy、CI 到達不能、production write 未承認、外部サービス障害など、AI が scope 内で直せない blocker。この場合は不足前提と人間の次アクションを出し、`<gdd-stop reason="blocked">` で止める。
3. scope/policy change: AC、security boundary、ownership、technology stack、prompt-output contract の変更が必要な blocker。この場合は `human_recheck_required` に戻す。

PR 作成前の hard gate:

- `approved Stage unmet blocks PR creation`。承認済み Stage、例: S-4a / S-4b / S-4c、のうち 1 つでも未実行・未検証なら Post-Completion PR Flow に入らない。
- `partial PR requires explicit partial-pr approval`。部分 PR にする場合は、含む Stage、含まない Stage、未達理由、後続入口を人間に提示し、明示的な partial-pr 承認を得てから PR 作成する。
- final output では `do not say S-4cまで自走しました when S-4c was not executed`。実行していない Stage は「未実行」「未達」「blocker により保留」と書く。

この section は Active GDD PR Creation Re-entry と Post-Completion PR Flow より優先する。`PR 作成まで` が自走上限に入っていても、承認済み Stage の未達は PR 作成権限ではなく blocker である。

## Phase Gate Pre-check

`references/phase-gate-prechecks.md` § Template B（Task-Size Aware Skip）を実行する。`quick (express)` ではこの skill 全体を skip して Post-Completion PR Flow のみ実行し `<gdd-stop reason="done">`。`standard` / `quick (standard)` / `quick (express → standard)` では Template A の 3-gate approval check を通して通常 Steps へ進む。

## Steps

### Part A: 事前確認（Steps 1〜4）

> 番号付けルール: `2a` / `3b` は親 Step の直後に実行される sub-step。`Step 2` → `Step 2a` → `Step 3` → `Step 3b` → `Step 4` の順で線形実行する（並列・スキップ不可）。

0. **機械検査**: 毎 Round、Step 1 の前に `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-completion-mechanical.py --steering <Steering Dir> --base <Template の対象の差分の base> --root <Worktree>` を 1 回 fresh に実行し、出力の全行を `worklog.md` に写す。判定は Step 0 では下さない。各 Step が自分の位置で、gate 列にその Step を持つ行（`completion-check:2a`・`:3`・`:4`・`:4c`・`:4c-3`・`:4d`・`:5`）を読み、missing・invalid があればその Step の不備として扱う（差し戻し先・出力は各 Step のとおり）。Step 0 の行が判定する項目は、gate が tasklist・state を読み直して判定し直さない。Step が不備なしと読めるのは、(a) exit が 0 か 1、(b) 最後の行が終わりの行（`ok<TAB>end<TAB>completion-check:0<TAB>rows=<n>`）、(c) gate 列にその Step を持つ行が 1 行以上あり、どれも `ok`、の 3 つがそろうときだけである。それ以外（行が無い・状態が `ok` 以外の値を含む）は exit の値によらず、その Step を不備として扱い（missing・invalid の行はその要求の不備、それ以外は invalid）、tasklist・state を読み直して代えない（行が無いことを不備が無いことと読まない）。ただし、どれかの行が `error`（検査の道具が判定できない）か、exit が 0・1 以外か、最後の行が終わりの行でないときは、各 Step の差し戻し先へ送らず、外部前提不足として `Next Action=gdd-completion-check` のまま `<gdd-stop reason="blocked">` で止める（`Completion Rounds` に数えない）。exit 2（引数の誤り、またはスクリプトを開けない）なら引数を直して 1 回だけ実行し直し、その結果にも同じ規則を当てる。行が無いまま Step 1 の判定に進まない

1. `requirements.md` の AC と `tasklist.md` の `Verification` を対応付ける。active worktree 側 `.steering/.../adr.md` があれば、重要な意思決定の背景を補助コンテキストとして確認する。
2. **Reviewer Selection Audit（読み取り専用監査）**: `Planning Reviewer Selection` が `state.md` に残っているか確認する。requirements gate で `gdd-planning-reviewer` が、design gate で `gdd-security-reviewer` の判断が記録されていることを確認する。
   - **audit = 既存 record の確認のみ**。completion-check から新規 record を追記しない（reviewer 判断は requirements-gating / design-gating の責務）。欠落を検知した場合も completion 側で補完記入しない
   - record が無い、reason が曖昧、scope と selection が明らかに食い違う場合は blocking issue とする
   - `Implementation Reviewer Selection` は per-task 一時状態であり、task 完了時にリセットされるため、completion 時の監査対象にしない。代わりに各 completed task の `Reviewed by` 行と全 task が `Completed Tasks` に到達していること（= 各 task が `gdd-implementation-gating` を通過した事実）を監査根拠とする。`Reviewed by` に conditional reviewer（`gdd-security-reviewer`）が含まれている場合は、scope に対して適切な reviewer が選択されたことを確認する
     2a. **Implementation Gate Evidence Check（必須・fail-closed・escape hatch あり）**: 各 completed task エントリに以下が含まれていることを確認する。1 件でも欠けていれば **fail-closed で停止** し、`Next Action=gdd-implementation-gating` に戻して対象 task を再 gate にかける。`Reviewed by: none (Judgment Change: no)` の task（impl-gating Step 1e で review を外した。Step 0 の行は ok）には下の 2・3 つ目を当てず、completion-reviewer が差分の線への接触を見る（観点 11）。触れていれば、その task を `Current Task` に戻して欄を `- Judgment Change: yes` にし、同じく再 gate にかける。
   - `Reviewed by:` 行が存在し、少なくとも `gdd-implementation-reviewer` が列挙されている: Step 0 の `reviewed-by` 行（gate 列 `completion-check:2a`）で判定する
   - reviewer の judgment（`approved` / `changes_requested` の決着）が読み取れる: `tasklist.md` の `## Completed Tasks` をディスクから re-read して読む（スクリプトは見ない）
   - conditional reviewer（security / terraform checklist）が scope 上必要な場合は、その reviewer も列挙されている: 同じく re-read して読む
   - **不備があった場合の出力**:

     ```
     ⛔ Implementation Gate Evidence 不足により completion-check を停止します

     対象 task（Reviewed by 行が欠落または不整合）:
     - <task-id>: <不足している項目>

     Next Action: gdd-implementation-gating（対象 task を再 gate にかける）
     ```

- **無限ループ防止（escape hatch）**: `references/bounce-log-schema.md` の共通仕様に従う。bounce log 名 `Implementation Gate Bounce Log` / identifier-key `task-id + 欠落項目` / 閾値 `>= 2` / escalate 先 `gdd-systematic-debugging`（schema の既存実装一覧参照）。2 回目の bounce 検知時は schema の「発動時の出力テンプレート」を使い、`Next Action` はまず `gdd-systematic-debugging` にして route recalibration を行う。recalibration では **policy / scope / ownership / security boundary / prompt-output contract の変更が無い限り `human_recheck_required` に上げない**。`Reviewed by:` 行や reviewer judgment の欠落、verification wording の不整合、evidence 整形ミスのような procedural / metadata blocker は build loop 内で扱い、`gdd-implementation-gating` 再実行または `blocked` で具体的な修正手順を返す
- **Why:** この確認を implicit assumption のまま放置すると、`Completed Tasks` に移動する処理さえ走れば impl-gate を経由せず completion-check に到達できてしまう。実際、ある migration タスクで impl-gating を経ずに completion-check → PR 作成まで進み、PR 作成後の ad-hoc review で初めて High 相当の content-loss が発見された事例がある。evidence check を hard gate に昇格させ、gate skip の経路を塞ぐ。一方で、`Reviewed by:` 行の欠落のような procedural blocker まで人間再承認に倒すと human check が常態化するため、escape hatch は **build loop 内の route recalibration** に使う（escape hatch の仕様詳細は `references/bounce-log-schema.md`）

3. Step 0 の `remaining-tasks` 行（gate 列 `completion-check:3`。Stop hook の done guard の Check 1 と同じ判定）が missing・invalid なら（`Current Task` または `Pending Tasks` に task が残っている、fence の閉じ忘れなどで数えられない）、completion を行わず停止する。停止時は残タスクの一覧を明示し、`Next Action=gdd-test-driven-development` に戻す。
   3b. **Refactor Gate 確認**: `tasklist.md` に `Refactor Gate Status` 行が存在しない場合（standard/planning パスで未到達の可能性）は、`gdd-refactor-planning` が未実行であることを記録し `Next Action=gdd-refactor-planning` に戻す。`pass-empty` / `pass-applied` の場合はそのまま続行する。`Task Size` が `quick (express)` に完全一致する場合（Template B により通常この Step には到達しない）は `Refactor Gate Status` 行がなくてもそのまま続行する。
   - completion output には **横断リファクタ点検** の結果を 1 行で含める。`pass-applied` なら適用した改善、`pass-empty` なら「改善候補なし」の根拠、Express パスで省略した場合は **省略理由** を書く。単に `Refactor Gate Status=pass` とだけ書かない
   - **`Refactor Gate Status=pending` 検知時**: refactor task 実装中に Behavior Preservation Invariants 違反で abort され通常 task として再計画された状態。`Next Action=gdd-refactor-planning` に戻し、再計画された通常 task の完了を前提に改善機会を再評価する（`skills/gdd-refactor-planning/SKILL.md` § Behavior Preservation Invariants Re-check 参照）。completion-check は pending を検知したら自走継続し、`human-check-waiting` には戻さない
   - `in-progress` が残ったまま completion-check に到達した場合は state 不整合として fail-closed 停止（本来 impl-gate が全タスク完了時に pass-applied に更新する）
   - build フェーズの canonical state である既存 `Next Action` は上書きしない。
4. Step 0 の `route-in-progress` 行（gate 列 `completion-check:4`。done guard の Check 3 と同じ判定）が missing・invalid なら（`state.md` の `Route In Progress` が `none` 以外、または読めない）、completion を行わず停止する。差し戻し route が未完了のまま完了宣言されることを防ぐ safety gate。
   - `Route In Progress` が残っている場合は `Next Action=gdd-systematic-debugging` に戻し、route の完了を優先する。

   4b. **SMI / Impact Block 蓄積記録の確認（AC Drift Check の入力強化）**: build loop 中に発生した `root-cause-investigation` の Phase 4 SMI block（`gdd-systematic-debugging` 経由）と `gdd-subagent-driven-implementation` の State Machine Impact Block（`gdd-implementation-gating` 経由）を以下のソースから収集する:
   - `.steering/.../worklog.md` の Error Log: SMI block 由来の routing 差異記録 / ADR 起票要件 / Reviewer Lineage 追加履歴
   - `.steering/.../adr.md`: SMI / Impact Block により起票された ADR エントリ
   - `tasklist.md` の `Implementation Reviewer Selection` の `selection_change_reason`: Reviewer Lineage 追加の trace

   収集した記録を以下の 3 項目チェックリストで AC Drift Check（Step 5a）の入力にする:

   - [ ] **ADR 起票要件の充足**: SMI block / Impact Block で `ADR 起票: 要` が記録されているなら、対応する ADR エントリが `.steering/.../adr.md` に実在するか。**未起票なら blocker** として `Next Action=gdd-completion-check` のまま停止し、起票を要求する
   - [ ] **Reviewer Lineage 追加の反映**: SMI block / Impact Block で `Reviewer Lineage 追加提案: <reviewer 種別>` が記録されているなら、対応する `Reviewed by:` 行が該当 task の `Completed Tasks` エントリにあるか。**未反映なら blocker** として `Next Action=gdd-implementation-gating` に戻し、対象 task を該当 reviewer で再 gate にかける
   - [ ] **Routing 提案との整合**: SMI block で `Routing 提案: human-check-waiting` が来ていた task について、実際に human check を通過したか（`state.md` の `Human Check Status=approved` の updated_at が該当 routing 後か）。整合しない場合は spec drift の疑いとして Step 5a の AC Drift Check で重点的に検査する

   全項目 [✓] なら Step 5 へ進む。1 つでも blocker があれば該当する `Next Action` で停止する。

   複数 blocker 同時発生時の合成 `Next Action` ルール（優先順位）と背景は `references/gate-checklists.md` § Checklist E: Completion Stale Classification § Step 4b を参照。

   4c. **Approved Direction vs Diff Check**: human check で承認された方向性が実装完了時に消えていないかを確認する。以下をディスクから re-read する:
   - `state.md` の `Approved Direction`
   - `requirements.md` の AC（人間が承認した重要判断は AC として書かれている）
   - `tasklist.md` の `Completed Tasks` / `Verification`
   - `git diff --name-only <Cumulative Diff Base or origin/base>...HEAD` の変更ファイル一覧

   判定ルール:

   - 承認済み AC が tasklist の task の `AC:` 行（legacy の `Covers AC:` を含む）に存在しない場合は blocker とし、`Next Action=gdd-task-breakdown` 相当の再分割が必要であることを報告する。Step 0 の `ac-coverage` 行（gate 列 `completion-check:4c`）で判定する。行は、Implementation Sequence Plan で `PR Boundary` が `follow-up-pr`・`post-merge-verification` の Stage にだけ置いた AC を除く。`current-pr`・`this-pr` の Stage にもある AC と、それ以外の値（空・記入例・語彙に無い語）の Stage の AC は除かない。代わりに `ac-source` 行が invalid（受入条件の節が無い、`- AC-n:` の定義が無い、節の AC ID を定義として読めない、Plan の PR Boundary が語彙に無い値か、行の欄の数が見出しと合わない）なら、Step 0 の (c) によらず、gate が requirements.md と tasklist.md を読んでこの項目を判定する。このときも、除いてよいのは上の 2 値の Stage にだけ置いた AC だけである
   - `Approved Direction` または承認済み AC に hook / sanitizer / registry / policy / guard / external egress / masking / audit boundary などの実装対象が含まれるのに、diff が docs / Judge / steering のみで実装対象ファイルを含まない場合は blocker とする
   - 上記を `Existing coverage inspection` で閉じる場合は、Verification に対象の実装ファイル、対象のテストファイル、テスト名または検証コマンド、新規実装なしの理由、制限事項がある場合だけ pass とする
   - 証拠が弱い場合は、仕様変更ではなく evidence 不足として `Next Action=gdd-implementation-gating` に戻す
   - 「新規実装はない / 既存実装の証明である」という意味が HITL に露出していなかった場合は、期待値変更の疑いとして `human_recheck_required` に昇格する

   **Why:** human check で「抜け道 hardening を追加する」と承認されても、tasklist が existing coverage inspection だけで完了し、実 diff が Judge / docs のみなら、人間が期待した「できあがり」と実装がズレる。Approved Direction vs Diff Check は、テストが通ったかだけでなく「承認された作り方・制限事項が実際に実装または証明されたか」を completion の最後で検査する。

   4c-2. **Baseline Compliance Check（構造・依存・実行環境の整合）**: `requirements.md` と `design.md` から承認済みの `実装方針`（architecture option / code structure / dependency / runtime / install / test / CI command）を re-read し、実装差分と照合する。これは AC verification の代替ではなく、AC が通っていても「作り方が承認と違う」状態を止める final gate。

   必須確認:

   - approved architecture option と file placement に従っているか。新規ファイルや変更ファイルが approved code structure から外れる場合は `human_recheck_required` または `planning_rework_required`
   - 新しい import / provider / image / tool / runtime 追加がある場合、dependency manifest と lock file に反映されているか。repo 方針で lock file を使わない場合は `not-used + reason` が requirements にあるか
   - install command がある場合は fresh install evidence を確認する。実行できない場合は `not_run` 理由を Verification に残し、do not mark done
   - test command がある場合は fresh test evidence を確認する。target test だけで十分な場合も理由を残す。必要 evidence が無い場合は do not mark done
   - CI command と local verification が矛盾していないか。CI のみで確認する項目があるなら external evidence として残す
   4c-3. **Codebase Health Gate（構造健全性）**: コード変更がある場合、Step 0 の `codebase-health` 行（gate 列 `completion-check:4c-3`。`gdd-codebase-health.py --mode changed --fail-on high` の結果）を読み、repo-local `scripts/check_code_health.py` / lint / architecture / package health check があれば併用する。行が invalid（High finding がある、または base を解決できない・実行できない）なら High として扱う。High finding は `gdd-systematic-debugging` に戻し（dispatch の前の main の差し戻しと同じ先。`references/subagent-dispatch.md` § Completion-Check の前の機械検査）、Medium finding は Verification に扱い（修正 / Non-Goal / no-action + 理由）を残す。判断資料 `docs/references-archive/infra-accretion-prevention-decision.md` の Context に書いた repo へ同等の CI gate を足すかは、その資料を参照し、却下された案（PR 旧#615）と同じ gate をユーザーの選択なしに再び足さない。Medium の件数は同じ行の詳細にあり、Medium finding の中身は `gdd-codebase-health.py` を `--format markdown` で回して読む。あわせて Step 0 の `unused-symbols` 行（`lint-unused-new-symbols.py` の結果。未参照シンボル検出、report-only で block しない）を読む。diff で追加された Python の新設関数・定数のうちテスト以外から参照 0 件のものを列挙するだけで、出力があれば completion output または reviewer の判断材料として提示する。
   不備がある場合:

   - 実装修正で直せる dependency manifest / lock file / command documentation の抜けは `Next Action=gdd-implementation-gating` または `gdd-systematic-debugging`
   - architecture option / runtime / service boundary / package manager の変更が必要なら `human_recheck_required`
   - external CI / auth など AI が直せない前提不足なら `<gdd-stop reason="blocked">`
   4d. **Planned Follow-up Stage Check（計画済み後続 Stage の消失防止）**: `requirements.md` に `Planned Follow-up Stage Lane` がある場合、`PR Boundary=follow-up-pr` / `post-merge-verification` の Stage が PR 完了時に消えないことを確認する。
   - `Pending Stage ID` / `Origin Steering` / `Base Branch` / `Next Planned Stage` / `Tracking Destination` / `Human Recheck` が埋まっているか、`Tracking Destination=none` に理由があるかは、Step 0 の `follow-up-stage` 行（gate 列 `completion-check:4d`）で判定する。表でない Lane、`- [ ]` の項目がある Lane も invalid になる。行が ok でも、欄の中身が追跡先として使えるか（`-`・`なし`・テンプレートの文言のままでないか）は gate が Lane を読んで判定する
   - `Tracking Destination` が `new steering seed` の場合は、completion output または worklog に `Next Planned Stage` と follow-up seed を残す。PR 作成後または手動 merge 後に新 steering を作るまで、後続 Stage を `done` の説明から落とさない
   - `Tracking Destination` が `none` の場合は理由が必要。理由が無い場合は `Next Action=gdd-completion-check` のまま停止し、後続 Stage の追跡先を補完する
   - `Human Recheck=required before implementation` の Stage は、この PR の `OK` だけで後続実装へ自走しない。後続着手時は `/gdd-dev` の新規または amendment として human-check に戻す
   - **Post-Merge Follow-up Prompt**: 段階実装で PR Boundary をまたぐ場合、PR作成時点では確定プロンプトを出さない。PR作成時は follow-up seed だけを残し、`post_merge_followup_prompt_required=true`、`next_chat_prompt_status=draft_until_merge` として worklog または post-merge continuation state に記録する。レビュー指摘・CI・最終差分が確定し、post-merge verification が終わったら `next_chat_prompt_status=ready_after_merge_verification` に更新し、マージ後に同じチャットで次 Stage に進む導線を生成する。
   - follow-up prompt には、前PRで完了したこと、次にやること、触ってよい範囲、触らない範囲、参照すべきPR/commit/steering、残っているAC / Stage、開始コマンドを含める。原則として同じチャット継続 + stageごとに新 worktree で開始し、旧 worktree / 旧 branch で後続実装へ流れ込まない。

   **Why:** HITL で「後続PR」と書いても、PR 作成・merge 後に追跡先が無いと Stage が会話履歴の中で消える。`Planned Follow-up Stage Lane` は hotfix ではなく、当初から計画済みだった後続実装の seed を残すための安全網。

### Part A-2: Output Consistency Evidence（データ出力 skill の場合）

`references/e2e-verification-catalog.md` § Pattern 3 を適用する。AC に決定性・網羅性が含まれる場合、2 回以上の E2E 実行比較・件数/内容/分割の一致・比較方法の記録を verification evidence に要求する。不足は `status=fail` とし追加 E2E を要求する。

### Part B: Verification 充足判定（Steps 5〜11）

5. `Verification` から required evidence を読み取る。
   - `method=ac:<id>` の行は AC 検証行として扱う
   - `method=security_evidence:<kind>` の行は required external security evidence として扱う
   - `method=refactor-checkpoint` の行は mandatory refactor checkpoint として扱う
   - workflow artifact や tasklist の説明で external security evidence が必要とされているのに `security_evidence:<kind>` 行が存在しない場合は、schema 未充足の blocker として `Next Action=gdd-completion-check` のまま止める
   - AC 本文が要求する検証水準（E2E 必須・外部証跡必須）に対応する evidence が `Verification` に無い場合は、verification evidence insufficiency として `status=fail` または schema blocker にする
   - Yes/No で観測できない曖昧な AC が accepted のまま残っている場合は、実装の失敗ではなく requirements schema issue として `planning_rework_required` / `human_recheck_required` へ戻す
   - **AC ID 整合性 lint**: Step 0 の `ac-ids` 行（gate 列 `completion-check:5`。`lint-ac.py --steering-dir` の結果）を読む。invalid なら requirements.md と tasklist.md の AC ID 不整合（orphan 参照 or 重複定義）として、`Next Action=gdd-completion-check` のまま blocker 報告して止める（fix されるまで Part B 以降は実行しない）
     5a. **AC Drift Check（reverse direction 検査：実装 → artifact 整合）**: `references/gate-checklists.md` § Checklist A を実行する。`Verification.status=pass` を付ける前に reverse direction（実装 → artifact）の整合を確認し、`gdd-ac-verification` の forward direction と双方向で drift 無しを保証する。該当時の routing（AC 追記 / ADR 追記 / `human_recheck_required` 昇格 / scope guard 差し戻し）も同 reference に従う。artifact 更新を伴う場合は updated_by / updated_at を記録して Part B を再実行する。
6. 各 AC について次を埋める。
   - `method`
   - `status`
   - `evidence`
   - `notes`
   - 行のシリアライズ形式（`method=ac:<AC_ID>` / `method=security_evidence:<KIND>` / `method=refactor-checkpoint` の 3 形）の正本は `gdd-ac-verification/SKILL.md` § Verification Schema の文法ブロック。canonical 例: `| method=ac:AC-1 | pass | npm test 通過 | - |`
7. `Verification.status` の許容値は `pending` / `pass` / `fail` / `N/A` / `unsupported` に固定する。
   - AC 検証の行では `Verification` の status は `pending` / `pass` / `fail` に固定する。
   - `pass` は evidence 必須にする。
8. external security evidence の行では次を固定する。
   - `pending` / `pass` / `fail` / `N/A` / `unsupported` を使う
   - `status=pass` のときは scan or verifier run を追跡できる evidence を残す
   - `status=fail` のときは未解決 issue、実行失敗、または verification 不足を `evidence` / `notes` に残す
   - `N/A` は、その evidence kind 自体が今回の変更に非該当のときだけ許可する
   - `unsupported` は、その evidence kind は必要だが current verifier contract では対象外であることを具体的に示せるときだけ許可する
9. mandatory refactor checkpoint が required evidence の場合は、`method=refactor-checkpoint` の行を追加し、`status=pass` と `evidence` を必須にする。
   - `evidence` には、どのファイルをどう簡略化したか、またはなぜ安全な改善がなかったかを残す
   - `status=fail` の場合は、再度 `gdd-subagent-driven-implementation` に戻す
     9b. **Stub Detection（Existence ≠ Implementation）**: `references/gate-checklists.md` § Checklist B を実行する。変更された実装ファイル（テスト/mock/fixture を除く）に対して stub パターン（`return null` / `raise NotImplementedError` / `TODO` / 空関数本体）を grep し、検出されれば `status=fail`。
     9c. **External Dependency Completeness Check（外部依存の実装充足確認）**: `references/gate-checklists.md` § Checklist C を実行する。新規スキル / コマンド追加タスクでは、requirements / SKILL.md に宣言された env var / IAM 権限 / cross-account ロールが env 定義・IaC に反映されているかを 2 段階（diff + 既存確認）で照合し、欠落があれば `status=fail`。
     9d. **Skill / Document Quality Check（スキル・ドキュメント品質確認）**: `references/gate-checklists.md` § Checklist D を実行する。SKILL.md / `*.md` の変更が含まれる場合、記述の一貫性 / 具体性 / Why の記載 / 重複・矛盾を確認し、いずれかが不合格なら `status=fail` で implementation に差し戻す。
10. required external security evidence が未到着、未記録、または schema 不正な場合は `done` に進めず、外部前提不足か verification 不足かを切り分ける。
    - 外部 hook / verifier がまだ書いていないだけなら `Next Action=gdd-completion-check` のまま止める
    - evidence 自体が fail している、または task 側 remediation が必要なら差し戻し候補にする
11. `Verification` の field や status schema が揃っていない場合も `done` に進めず、必要項目を埋めてから最終判定する。この判定とは別に、`Verification` の状態を問わず毎 Round、`git fetch origin --quiet` の後に `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/list-merge-triggered-workflows.py --base origin/<default-branch> --default-branch <default-branch> --merge-with origin/<default-branch>` を実行し（マージで起動する workflow の一覧。commit 済みの差分を、マージの結果の workflow と突き合わせる。commit していない変更は入らないので、変更を commit してから実行する）、出力の全行を `worklog.md` の `マージで起動する workflow:` の下にそのまま写す。0 以外で終わったら原因を直して実行し直し、一覧が無いまま `done` に進めない。一覧の使い方（PR 本文の影響範囲、デプロイ系のマージ後の完了確認）は `references/post-completion-pr-flow.md` の PR Body Merge-Triggered Workflows Check が正本。

### Part C: Comprehensive review と最終判定（Steps 12〜21）

12. comprehensive reviewer 起動前に `gdd-completion-reviewer.status=in_review | evidence: review-start:gdd-completion-check | updated_by: gdd-completion-check | updated_at: <timestamp>` を記録する。
    12a. **Dialectic Review Evidence Check（条件付き）**: `references/dialectic-review.md` の Trigger に該当する変更（prompt / skill / reviewer policy / 人間向け出力 / severity calibration / false positive 改善等）の場合、`design.md` または `worklog.md` に `Dialectic Review Summary` が残っているか確認する。- summary がある場合: `Consensus` / `Adopted From Primary` / `Adopted From Counter` / `Rejected` / `Final Decision` / `Open Risks` が最終実装・docs・skill 文面と矛盾していないか確認する - summary が無いが trigger に該当する場合: completion-check 内で `references/dialectic-review.md` の Short Form を実行し、`worklog.md` に `Dialectic Review Summary` を追記してから続行する - dialectic の結果、AC 追加/削除・scope・policy・ownership・security boundary・prompt-output contract が変わる場合は `human_recheck_required` に昇格し、silent に `done` にしない - 表現圧縮、章立て、severity calibration、採否理由の改善だけで閉じる場合は completion 内の evidence として扱い、formal gate status は単独で変更しない
13. `gdd-completion-reviewer` を **Task tool 経由でサブエージェントとして起動** し（`subagent_type=gate-driven-development:gdd-completion-reviewer` を指定、プラグイン名前空間は環境に応じて調整。steering に `request.md` があれば、それと `request-crosscheck.md`・`worklog.md` の絶対パスも渡す。時間上限と、時間超過・エラーで返らないときの出口は `references/subagent-dispatch.md` § Reviewer Input and Time Budget の「時間上限」「超過・無応答のとき」に従う）、high と unresolved medium issue を整理する。reviewer finding で差し戻すのは `gdd-implementation-gating` Step 9 と同じ述語（High と実害クラス。`references/reviewer-common.md` § finding category の `is_blocking`）に当たるものだけで、このうち実害クラスの medium を unresolved medium と呼ぶ。有意な testing gap は、AC の Verification の evidence がその AC を示せていないもの（AC に対応する検証が無い、または検証が AC の条件を確かめていない）を指し、category によらず evidence の不足として blocking にする。これに当たらないテストの指摘は、category のとおりに扱う。verification evidence が弱い、抽象的すぎる、reviewer selection record が欠けている、dialectic の final decision と実装・docs が矛盾している、または有意な testing gap が残っている場合は blocking issue として扱う。Low と、上の述語に当たらない medium は、`state.md` の `## Advisory Findings (Impl-Gate)` に impl-gate の記録と同じ形で追記し（PR 本文への搬送は `references/post-completion-pr-flow.md` の Advisory Findings Check）、単独では `done` をブロックしない（手順 14・20 と Guardrails の testing gap・unresolved issue も、この定義で読む）。`references/independent-review.md` の (3-f) の finding は同項の申し送りに回す（`state.md` の `Decision Handoff` を書く）。
14. `fail` がある場合、verification evidence が不足している場合、reviewer selection record が弱い場合、または comprehensive review に unresolved issue / 有意な testing gap がある場合は、失敗した AC の **primary owner task**（`(primary: T-n)` で指定された Task ID の task）を deterministic に再オープンする。Task ID で一意に特定するため、task の並び順に依存しない。`Request Drift` のうち AC を変えないと閉じないもの（依頼に合わせると AC が変わる）は、再オープンや remediation task にせず `human_recheck_required` に戻す。
15. 再オープン対象が複数ある場合は、最初の 1 件だけ `Current Task` に戻し、残りは `Pending Tasks` に戻す。
16. 対応 task が無い failed AC や comprehensive review 指摘には remediation task を作り（書く欄は `references/state-machine.md` § tasklist.md の canonical state の remediation task の規定）、`Current Task` が空なら最初の 1 件を `Current Task`、残りを `Pending Tasks` に置く。
17. gdd-completion-check 差し戻しとして `Next Action=gdd-systematic-debugging` に戻す場合は、formal reviewer status を `pending | evidence: none | updated_by: gdd-completion-check | updated_at: <timestamp>` に戻し、古い `waiver_reason` を残さない。あわせて、手順 14〜16 で再オープン・作成した task のすべて（`Pending Tasks` に置いたものも含む）の `Fix Findings:` を、その task に当たる blocker で書き直す（書き方は `references/state-field-tiers.md` の `Fix Findings` の行）。
18. actual な AC failure / review blocker / verification evidence insufficiency の場合だけ `Next Action=gdd-systematic-debugging` に戻す。
19. 外部前提不足だけが blocker の場合は `Next Action=gdd-completion-check` のままにし、external verifier hook が evidence を書いた後に再実行する。再実行時に前回と同じ blocker リスト（同じ `security_evidence:<kind>` が同じ `status` で残っている）なら、外部前提に変化がないと判断し、不足 evidence の具体的な解消手順を human に明示通知して `blocked` で停止する。変化がある場合（1 つでも status が変わった、新たな evidence 行が追加された等）は通常通り再判定を続行する。
20. 全 AC が `pass` になり、required external security evidence も揃い、mandatory refactor checkpoint も pass になり、reviewer selection record と verification evidence が `done` を支えるだけ具体的で、未完了 task が無く、unresolved な blocking review（手順 13 の high / unresolved medium / evidence insufficiency / testing gap）も無い場合だけ `gdd-completion-reviewer.status=approved` を記録し、`state.md` の `Route In Progress` が `none` 以外なら `none` にクリアし（`references/rollback-patterns.md` §ターミナル状態でのクリア 参照）、`Next Action=done` にする。
21. 中止する場合だけ `gdd-completion-reviewer.status=waived` を理由付きで記録し、`state.md` の `Route In Progress` が `none` 以外なら `none` にクリアし、`Next Action=cancelled` にする。cancelled 後のワークツリー・ブランチ・`.steering/` の cleanup は `gdd-using-git-worktrees` の Cancelled Cleanup セクションに従い、ユーザーに選択肢（keep / archive / discard）を提示する。

### Part D: UAT チェックリスト提示（オプション）

`references/uat-checklist.md` を参照。`Next Action=done` 確定後、Post-Completion Learning の前にユーザー向け手動確認チェックリストを提示する。フォーマットと運用ルール（抽出件数 3-5 件 / テストで自動確認済みの AC は除外 / done をブロックしない / 問題報告時は新 steering 扱い）は同 reference を正本とする。

## Post-Completion PR Flow / Learning

`Next Action=done` 確定後、`<gdd-stop>` を出す前に `references/post-completion-pr-flow.md` を読む。そこに Post-Completion Learning、Planned Follow-up Stage Lane Output、Post-Completion PR Flow、Manual Merge Continuation、Post-Merge Final Output Next Plan の詳細を集約する。

本 skill 側では、Post-Completion Learning を PR Flow の前に実行すること、後続 Stage の開始は PR Flow 側の Stage Continuation 契約（`references/post-completion-pr-flow.md` Option 1 手順 6 § Stage Continuation）に従うこと、PR 作成後も post-PR scope が残る場合は `done` にしないことだけを保持する。ADR 蒸留や PR 本文など人間向けの文章を書くときは `references/japanese-writing-norm.md` に従う。

## Rationalization Check（この skill 固有）

done への近道を取りたくなる思考パターンは `references/common-guardrails.md` § 合理化防止テーブルと `references/rationalization-root-causes.md` を参照する。本 skill 固有の重点は、CI green を AC 充足と同一視しないこと、fresh evidence なしに `pass` と書かないこと、`Route In Progress` / AC Drift / ADR 追記漏れを残したまま `done` にしないこと。

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（fail-closed 応答）。完了宣言前の検証ルール（Iron Law / Gate Function / Fresh Verification / 言語制限 / Before-After 確認）の詳細は `references/verification-before-completion.md` に集約。以下はこの skill 固有のルール。

- 確認前に「完了」と言わない
- AC が未記録のまま completion しない
- `Verification` が completion の唯一の正本であることを崩さない
- `Verification` に `waived` を持ち込まない
- `Planning Reviewer Selection` / required external security evidence を silent skip しない
- **Fresh Verification 必須**: 各 AC の検証コマンドを本セッション内で新規実行し、その実行結果を evidence として記録する。同じ起動の外の結果（以前のセッション、前のターン、compaction の前）や、`references/verification-before-completion.md` § Fresh の粒度の条件を満たさない実行結果だけを根拠に `status=pass` にしない。詳細な Gate Function は `references/verification-before-completion.md` § The Gate Function
- **完了宣言の言語**: 「テスト X を実行し exit code 0 で pass した」形式で記述する。「should work」「probably」「seems to」「I think」「I'm confident」などの推量表現は evidence として認めない
- **CI のみに頼らない**: AC 検証は自分で実行したコマンドの出力を evidence にする。CI green / PR check green だけを根拠に `status=pass` にしない。CI ログで実際のコマンド出力を確認するか、ローカルで再実行する
- **Partial pass を full pass にしない**: 「一部のケースは動作する」「happy path だけ通った」は `pass` ではない。AC に記載された全条件が満たされていることを確認してから `pass` にする
- **Before/After 確認**: 変更前の動作と変更後の動作を比較し、意図通りに変化している（または変化していない）ことを確認する。変更箇所だけでなく、周辺の既存動作が壊れていないことも確認する
- `Implementation Reviewer Selection` は per-task 一時状態であり、全 task の `Completed Tasks` 到達を監査根拠にする
- relevant な evidence kind で `N/A` や `unsupported` を汎用 escape hatch として使わない
- 外部前提不足を code/debug failure と混同して `gdd-systematic-debugging` に誤送しない
- 証跡不足や有意な testing gap（手順 13 の定義）を advisory 扱いで `done` にしない
- 外部前提不足で止まる場合は Output Guidance の `⚠ 外部前提が不足しています` テンプレートを必ず使う。「evidence が足りません」だけで止めない
- `Route In Progress` が `none` 以外のまま `done` に進めない
- Post-Completion PR Flow の scope 確認・セルフレビューをスキップして PR を作成しない（ユーザー明示スキップを除く）
- **current task の `.steering/<slug>/` を silent skip しない**: `git status` で untracked / modified に見えても、現在 task の artifact なら PR 前に所在を確定する。standard では branch-only steering として扱い、同じ PR に raw task steering を含めない。重要判断は `docs/adr/` へ Distill to ADR し、main には raw task `.steering/<task>/` を含めない
- **root/worktree split steering を放置しない**: 同一 slug の `.steering/<slug>/` が root と active worktree の両方に存在する場合、どちらかを正本に確定するまで `gh pr create` / cleanup / done を進めない
- **PR-level Pre-PR Review 必須**: `gh pr create` を実行する前に `gdd-pr-review` Pre-PR loop を必ず起動し、PR 全体 diff に対して `reviewer-selection.md` に基づく reviewer 再選定と `inline-review-checklists.md` 全走査を行う。per-task 時点で `waived` だった reviewer も PR-level で条件に該当すれば再 `selected`。skip / waive 不可。High finding 残存時は `gdd-systematic-debugging` に差し戻す（silent に PR 作成しない）
- **AC Drift Check の bypass 禁止**: `Verification.status=pass` は artifact → 実装の一方向しか保証しない。実装 → artifact の逆方向整合（AC に書かれていない挙動が diff に含まれていないか）を Step 5a で必ず検査する。記載のない挙動がある場合は `requirements.md` / `design.md` / `adr.md` のいずれかに反映するか、`human_recheck_required` / `implementation_fix_only` で差し戻す。silent に `done` にしない
- **Branch Hygiene Pre-Flight の bypass 禁止**: Post-Completion PR Flow Option 1 の Pre-Flight（未コミット成果物の全量コミット + main 進行検知 + scope 外 file 検出）を skip して `gh pr create` を実行しない。各ステップのコマンド実行自体は省略しない（結果がゼロなら出力省略は可）。**Why:** 未コミット成果物・rebase 漏れ・scope 漏れを完了直前で発見できる最後のレイヤー
- **Plan mode 遷移禁止**: completion-check は terminal gate であり、`Next Action` は `done` / `cancelled` / `gdd-completion-check` / `gdd-systematic-debugging` / `gdd-refactor-planning` / `gdd-implementation-gating` のみを許容する。harness 側の Plan mode へ自動遷移しない。曖昧な状態で停止する場合は `<gdd-stop reason="blocked">` で止め、Plan mode へ逃さない
