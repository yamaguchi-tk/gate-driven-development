# GDD Scenario Evals

GDD のシナリオ評価は、GDD state machine / HITL / worktree / PR / verification の流れを守るための **GDD 専用の回帰評価基盤** である。目的は「直したつもり」の文面契約ではなく、過去に壊れた会話流れが再発していないことを scenario fixture と artifact 採点で確認すること。

`empirical-prompt-tuning` は、skill や prompt を別 agent に実行させて反復改善する重い品質改善手法である。GDD Scenario Evals はそれを置き換えるものでも、単なる別名でもない。GDD の日常 gate は deterministic replay を正本にし、subagent / LLM Judge は「人間が判断できるか」「会話ルートが自然か」を補助確認するために使う。

## Scope

### P0: Deterministic Replay

- **Scenario Corpus**: 過去に実際に壊れた HITL / route / worktree / PR flow / verification blocker を `evals/gdd-scenario-fixtures.json` に固定する
- **UX Regression Matrix**: 考慮漏れ、使用体験が悪い、読めるが判断できない、短すぎる HITL、次の行動が分からない、同じチャットで続けるべきか分からない、といった体験劣化を scenario として固定する
- **期待チェックリスト**: 各 scenario は 3-7 件の checklist を持ち、最低 1 件は `[critical]` 相当の `critical: true` にする
- **Artifact Collector**: `assistant.md` / `state.md` / `tasklist.md` / `requirements.md` / `pr_body.md` など、GDD の成果物を scenario ID ごとの directory から読む
- **Deterministic Scorer**: `contains_all` / `contains_any` / `regex` / `not_contains` で、route accuracy、HITL decisionability、state consistency、verification sufficiency を機械採点する

### P1: GDD Scenario Review Support

- **Subagent Prompt Generation**: `scripts/run-gdd-scenario-evals.py --emit-subagent-prompts` で、新しい subagent に渡す白紙評価プロンプトを scenario ごとに生成する
- **Iteration Report**: `--iteration-report` で Iteration N 形式の markdown report を出し、`変更点（前回差分）`、`実行結果（シナリオ別）`、`不明瞭点（今回新出）`、`裁量補完（今回新出）`、`次の修正案`、`収束判定` をこの順番で残す
- **Empirical-style Presentation**: report 冒頭は empirical-prompt-tuning の提示フォーマットに合わせる。GDD 固有の Final Evaluation / Improvement Result / Hold-out Regression Gate / category coverage は `詳細` 以降に置き、最初に読む面を盛りすぎない
- **Minimal Next Fix**: 冒頭の `次の修正案` は empirical と同じく 1 行だけにする。複数の未達がある場合も残件数をここに出さず、残りは `Actionable Failures` 詳細に逃がす
- **Final Evaluation**: iteration の最後に status / reason / scenario count / pass-warning-fail / review ambiguity / degrade / improvement / next action を必ず出す
- **Improvement Result**: 前回 summary と比較できる場合は、改善した check、退行した check、残る critical failure、残る actionable failure、残る review ambiguity を出す
- **Actionable Failures**: critical / non-critical failure ごとに、scenario、check、target、missing pattern、次の修正対象を出す
- **GDD Scenario Review Signals**: `--review-dir` で subagent review report を読み、不明瞭点、裁量補完、再試行を scenario ごとに出す
- **Baseline Compare**: `--baseline-summary` で前回 summary JSON を読み、check 単位の degrade / improvement を出す
- **Hold-out Regression Gate**: `--holdout` で GDD scenario corpus の過去 fixture が壊れていないことを fixed schema で report 末尾に出す
- **LLM Judge Boundary**: LLM Judge は deterministic scorer の代替ではない。HITL が人間に判断可能か、非エンジニアに読めるか、ユーザー入力と整理要件がズレていないかに限定する

### P2: Release Gate

- **Release Gate Enforcement**: `scripts/run-gdd-scenario-evals.py --require-release-pass` は `release_decision.status=pass` 以外を exit 1 にする。critical failure だけでなく warning / review ambiguity / baseline degrade も release 推奨にしない
- **Representative Artifact Gate**: `validate-plugin.sh` は代表 artifact を使った deterministic scenario gate を実行し、Stop hook / post-merge cleanup / PR follow-up / ADR persistence の直近事故が再発していないことを確認する
- **Incident-to-Fixture Rule**: GDD で実害が出た事故は、修正PRと同じか次のPRで `evals/gdd-scenario-fixtures.json` に scenario を追加し、少なくとも 1 つの critical checklist を持たせる
- **No Green Without Evidence**: `--require-critical-pass` は開発中の軽量確認、`--require-release-pass` は配布・PR前の厳格確認として使い分ける。warning が残る場合は「機能的には通るが配布判断は保留」と扱う

## Why

contract test は「文書に必須語があるか」を見るのに強い。一方で、GDD の事故は会話の流れで起きる。

- brainstorming から formal GDD に入った後に PR まで進まない
- merge 後の「次の計画は？」が superpowers に流れる
- Option B や P1 が未定義のまま HITL に出る
- 検証計画がなく、完了条件に対して何をどこで確認するか分からない
- worktree / branch / steering / state の identity が混ざる
- verification blocker を completion と誤報告する

これらは単体の grep contract だけでは検出しづらい。Scenario Corpus と Artifact Collector で会話単位の outcome を採点し、Iteration Report と Hold-out Regression Gate で再発を見える化する。

## Scenario Schema

各 scenario は、最低限以下を持つ。

- `scenario_id`: 安定した ID
- `source_session`: 事故や観測の元になった Codex / Claude Code / Cursor session ID。未観測の仮想シナリオなら `synthetic:<name>`
- `category`: `hitl` / `route` / `next-plan` / `worktree` / `pr` / `verification` / `debugging` / `model-routing` / `staged-implementation` など
- `origin`: `incident_regression` / `gdd_flow_goal` / `synthetic_edge`。未指定の古い scenario は incident regression とみなす
- `goal`: GDD として実現したい体験や保証。`gdd_flow_goal` では必須
- `flow_stage`: GDD のどの段階を評価するか。例: `gdd-pre-workflow-brainstorming` / `human-check-waiting` / `build phase`
- `prompt`: その scenario でユーザーが何をしたか
- `artifacts`: 採点対象の成果物
- `current_contract_refs`: 現行GDD契約の参照先。GDDが変わったらここを読み直して checklist を更新する
- `must_preserve`: フローが変わっても守るべき本質
- `must_not_happen`: フローが変わっても起きてはいけないこと
- `human_ux_rubric`: 人間にとって判断可能かを見る観点。例: `decisionability`, `non_engineer_readability`, `next_human_action`, `too_short_or_too_long`
- `safety_rubric`: 自走境界、危険操作、worktree、scope、PR / merge / deploy 境界を見る観点
- `failure_modes`: この scenario で再発させたくない悪い挙動
- `checklist`: deterministic scorer で見る具体条件

### Scenario Layers

GDD は現在進行形で変わるため、scenario を全部「固定文言」にしない。

- **Incident Regression**: 過去に壊れた事故事例。`failure_modes` と `source_session` を残し、再発を防ぐ
- **GDD Flow Goal**: GDD が実現したい体験から作る scenario。`goal` / `flow_stage` / `must_preserve` / `must_not_happen` を正本にし、checklist は現行契約に合わせて更新可能な派生物として扱う
- **Synthetic Edge**: まだ実事故はないが、設計上壊れると影響が大きい境界ケース

フロー変更で古い checklist が合わなくなった場合、scenario を削除するのではなく、`goal` / `must_preserve` / `must_not_happen` と `current_contract_refs` を読み直し、現行フローに合う checklist へ更新する。

## Scenario Selection

考慮漏れや UX 劣化を洗い出すときは、まず次の category coverage を満たす。単に似た HITL だけを増やさない。

- `hitl`: 要件、実装方法、検証方法、自走範囲、判断ポイント、段階計画が読めるか
- `route`: brainstorming / root cause / amendment / implementation の入口が混線しないか
- `next-plan`: merge 後や stage 完了後に、同じチャットで続けるか新チャットへ渡すかが分かるか
- `worktree`: root checkout、host-managed checkout、既存 task branch、patch migration recovery を誤らないか。加えて、作業場所宣言（`workspace-policy.md`）が最初の応答で正しく出力されるか
- `pr`: review 指摘が残る限り fix / push / 再レビュー依頼を続けるか
- `verification`: 検証 blocker を完了扱いせず、どこでどう検証するかを示すか
- `debugging`: root cause が未確定なら最大 3 cycle まで仮説検証を回すか
- `model-routing`: 計画 / 実装 / review / 軽量作業で model / effort を使い分けるか
- `staged-implementation`: PR を挟む段階実装で、次 phase の受け渡しと cleanup を案内するか
- `pre-workflow`: 相談段階で artifact-free を維持し、formal workflow への移行判断を明確にするか
- `design`: 承認済み方向性を、既存コード調査・アーキテクチャ・依存環境・検証可能な設計へ変換するか
- `build`: TDD / refactor / implementation review / completion evidence の順序を守るか
- `state`: Approved Direction、Resume From、Next Action などの状態が、承認後の自走と安全停止を支えるか

## Subagent Prompt Contract

`--emit-subagent-prompts` が生成する prompt は、必ず以下を含む。

- `あなたは GDD scenario fixture を白紙で読む実行者です`
- `評価モード`: 親セッションの会話履歴や暗黙知を使わず、prompt 単体で判断すること
- `pass / warning / fail` の判定基準
- 対象 scenario の状況設定
- GDDとして守りたいこと
- 起きてはいけないこと
- 現行契約の参照先
- 契約スナップショット（scenario 固有の短い定義や境界条件）
- 期待される結果（白紙評価者が裁量なしに成果物を説明できる最低条件）
- 期待される成果物の型
- GDD共通の形式要件（identity tuple、PR follow-up、verification blocker、root cause cycle、post-merge cleanup など）
- 要件チェックリスト
- 成果物の期待形
- レポート構造
  - 成果物
  - 要件達成
  - 不明瞭点
  - 裁量補完
  - 再試行

新しい subagent を使う。前回の評価結果を読んだ subagent を再利用しない。自己再読で代替しない。dispatch できない環境では `gdd scenario review skipped: dispatch unavailable` と記録し、deterministic replay だけを実施する。

白紙評価では `current_contract_refs` の実ファイルを読めるとは限らない。prompt 内に十分な contract snapshot / expected artifact shape / state field expectation が無ければ、subagent は裁量補完として warning を返してよい。これは評価の失敗ではなく、scenario prompt 側の改善シグナルである。

古い incident regression scenario が `current_contract_refs` を持たない場合、prompt generator は `category` から既定の contract refs を補完する。白紙評価 prompt に `現行契約の参照先: なし` を出してはならない。

## Scoring Rules

scenario の status は以下で決める。

- `pass`: critical checklist が全て pass
- `fail`: critical checklist が 1 件以上 fail
- `warning`: critical は pass だが non-critical が fail、または GDD Scenario Review Signals に `不明瞭点` が残る

summary JSON は `overall_status`、`status_counts`、`category_coverage`、`comparison`、scenario ごとの `next_actions` を持つ。精度は `passed checklist / total checklist` で計算する。LLM Judge が必要な観点は `judge_required: true` として deterministic score と分ける。

`--review-dir` を指定した場合、各 scenario の `review.md` / `<scenario_id>.review.md` から以下を抽出し、`GDD Scenario Review Signals` として report に出す。

- `不明瞭点`
- `裁量補完`
- `再試行`

これは empirical-prompt-tuning の自己申告メトリクスを GDD 用に薄く取り込むものであり、deterministic scorer の代替ではない。`不明瞭点` が `なし` 以外なら、scenario の critical checklist が pass でも `overall_status=warning` とし、release 推奨ではなく `iter 継続` にする。

## Hold-out Regression Gate

release / PR 前に過去 fixture を hold-out として実行する。report 末尾には以下の fixed schema を出す。

```text
### Hold-out Regression Gate
- mode: standard | quick-gate | deterministic-only | baseline-compare | skipped
- N: <scenario count>
- threshold: <absolute pt>
- degrade: <count>（内訳: <scenario / item>; ...）
- improvement: <count>（内訳: <scenario / item>; ...）
- 判定: pass | warning | fail | terminate-no-benefit
- 次アクション: release 推奨 | iter 継続 | 構造書き直し | 現行維持 | dispatch unavailable
```

P1 では `--baseline-summary` がある場合だけ check 単位の degrade / improvement を測る。baseline がない場合は deterministic-only として、過去に壊れた scenario の critical checklist が全て pass することを gate にする。

## Empirical-Style Operating Loop

GDD Scenario Evals は、固定 fixture を一度回して終わりではない。GDD の方向性やフローが変わるたびに、次の empirical-style loop で scenario と prompt を更新する。

1. **方向性を決める**
   - GDD が今回守りたい価値を `goal` / `flow_stage` / `must_preserve` / `must_not_happen` にする
   - 事故再発防止なら `incident_regression`、GDD の体験保証なら `gdd_flow_goal` として scenario を追加または更新する
2. **scenario prompt を生成する**
   - `--emit-subagent-prompts` で、白紙 subagent に渡す prompt を生成する
   - prompt は親セッションの会話履歴に依存しない。必要な契約は `contract_snapshot` / `expected_outcome` / `GDD共通の形式要件` に入れる
3. **新規 subagent で評価する**
   - 同一 agent を再利用しない
   - subagent の `不明瞭点` / `裁量補完` / `再試行` を `reviews/<scenario_id>/review.md` に保存する
4. **deterministic replay と review signal をまとめて採点する**
   - `--input-dir` と `--review-dir` を渡して scenario eval を実行する
   - critical failure があれば `fail`
   - critical が通っても review ambiguity があれば `warning`
   - report 冒頭は empirical-prompt-tuning と同じ順番にする。`結論` や `改善結果` を先に盛らず、シナリオ別結果と不明瞭点を主役にする。GDD 固有の technical details は `詳細` 以降に置く
5. **足りなければ自動改善する**
   - 不足が scenario prompt の情報不足なら、`contract_snapshot` / `expected_outcome` / checklist / expected artifact shape を更新する
   - GDD 本体の契約不足なら、対象 skill / reference / hook / lint を更新する
   - 修正後は新規 subagent で再評価する。同じ subagent の再利用は禁止
6. **収束条件**
   - release 推奨は `Final Evaluation status=pass` のときだけ
   - `warning` は「機能的には通るが、人間または白紙 agent が迷う」状態なので `iter 継続`
   - `fail` は critical failure / degrade が残っている状態なので `iter 継続`
   - 連続 2 回 `pass` かつ新規不明瞭点 0 のとき、scenario prompt の改善は一旦収束とみなす

## Operating Loop

1. scenario fixture を追加する
2. 現在の GDD 出力 artifact を `artifacts/<scenario_id>/` に置く
3. `scripts/run-gdd-scenario-evals.py --fixture evals/gdd-scenario-fixtures.json --input-dir artifacts --review-dir reviews --baseline-summary previous-summary.json --iteration-report report.md --holdout` を実行する
4. critical failure を最小修正する
5. 新しい subagent 用 prompt を生成して白紙評価する
6. 連続 2 回、critical failure と新規不明瞭点が 0 になったら収束とする
