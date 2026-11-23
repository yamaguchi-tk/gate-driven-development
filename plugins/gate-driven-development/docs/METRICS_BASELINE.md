# METRICS BASELINE（運用 KPI のベースライン）

> **対象**: GDD 導入チームのテックリード・運用担当
> **目的**: `gdd-metrics` で収集した数値を「健全」「要注意」「危険」のしきい値で評価するためのベースライン
> **上位正本**: `skills/gdd-metrics/SKILL.md`（収集方法・算出式の定義）
> **この文書の位置付け**: 数値は取れているが「どの値なら良いか」の判断基準を与える

---

## 前提

- `gdd-metrics` skill で数値は自動収集される
- 本文書は **健全に運用できているかの目安** を提供する
- 完全な正解値ではなく、**チームごとに調整してよい**（初期 baseline として参照）
- 測定期間は **直近 30 日** を原則とする（タスク数が少ないチームは 90 日）
- `Resume From` / `Human Check Status` / `Route In Progress` / `Next Action` の coverage が低い期間は、distribution や完了率を参考値として扱う。まず state 記録の欠落を埋める

---

## Core KPI（コアメトリクス）

### 1. 完了率

```
完了率 = (Next Action=done) / (全タスク - cancelled - blocked)
```

| 水準   | 値       | 評価                  | 対応                                               |
| ------ | -------- | --------------------- | -------------------------------------------------- |
| 健全   | 80% 以上 | GDD が期待通り機能    | 継続観察                                           |
| 要注意 | 60-79%   | 中断タスクが多い      | 中断理由を分析（タスクサイズ見直し・要件不明瞭？） |
| 危険   | 60% 未満 | workflow の定着に課題 | オンボーディング再実施・運用レベル見直し           |

---

### 2. 実装 gate の通過率

```
通過率 = approved / (approved + changes_requested)
```

| 水準   | 値       | 評価                            | 対応                                                        |
| ------ | -------- | ------------------------------- | ----------------------------------------------------------- |
| 健全   | 70% 以上 | 実装品質が gate を通る          | 継続                                                        |
| 要注意 | 50-69%   | 初回レビューで落ちがち          | TDD の実効性・実装前のコンテキスト整備を確認                |
| 危険   | 50% 未満 | reviewer が過剰 or 実装品質不足 | `learned-patterns.md` の適用状況・reviewer calibration 確認 |

---

### 3. 平均差し戻し回数（Attempts）

```
平均 = Σ(各タスクの Attempts 数) / タスク数
```

| 水準   | 値       | 評価                               | 対応                                                   |
| ------ | -------- | ---------------------------------- | ------------------------------------------------------ |
| 健全   | 1.5 以下 | 1 回の修正で大抵通る               | 継続                                                   |
| 要注意 | 1.5-3.0  | 修正ループが長い                   | reviewer calibration 確認、task breakdown の粒度見直し |
| 危険   | 3.0 超   | reviewer loop が発生している可能性 | Reviewer Loop Escape Hatch の発動状況確認              |

---

### 4. Task Size 分布

| サイズ   | 健全な割合 | 危険シグナル                           |
| -------- | ---------- | -------------------------------------- |
| trivial  | 20-40%     | 0% = GDD を使いすぎ（ceremony 過剰）   |
| express  | 30-50%     | 0% = 小タスクが standard に流れている  |
| quick    | 20-40%     | 80% 超 = sizing の精度が低い           |
| standard | 10-20%     | 50% 超 = overhead 過多、タスク分割不足 |

**目安**: `standard` が全体の 10-20% 程度に収まっていれば健全。`standard` が過半数ならタスク分割が粗い。

---

### 5. Human Check 差し戻し率

```
差し戻し率 = Scope Drift Guard 発動回数 / human-check-waiting 到達回数
```

| 水準   | 値       | 評価                   | 対応                                                          |
| ------ | -------- | ---------------------- | ------------------------------------------------------------- |
| 健全   | 10% 以下 | 要件整理が適切         | 継続                                                          |
| 要注意 | 10-30%   | 承認後の方針変更が多い | brainstorming の Problem Discovery / Options Exploration 強化 |
| 危険   | 30% 超   | 要件把握が弱い         | Direct Intent Shortcut の誤適用、承認ポイントの Why 不足      |

---

## Secondary KPI（補助メトリクス）

### 6. Reviewer Learning Loop の効果

| メトリクス                 | 健全な傾向        | 危険シグナル                                             |
| -------------------------- | ----------------- | -------------------------------------------------------- |
| Adopted Patterns 数        | 月 5+ 件増加      | 横ばい = 学習が進まない                                  |
| Rejected Alternatives 数   | Adopted の 30-50% | Rejected が Adopted を上回る = 設計判断が不安定          |
| Code Conventions 数        | 月 3+ 件増加      | 横ばい = プロジェクト規約の蓄積が進まない                |
| Calibration 適用回数       | 月 2+ 件増加      | 0 件継続 = reviewer の false positive 検出が働いていない |
| 推定 false positive 削減率 | 月 5-15% 改善     | 30% 超の改善 = 元の reviewer が過剰だった可能性          |

**読み方**: Learning Loop は「右肩上がりに増えていく」のが健全。横ばい・減少は calibration / cross-task learning の活用不足。

---

### 7. Blocked 率

```
Blocked 率 = blocked タスク数 / 全タスク数
```

| 水準   | 値      | 評価                     | 対応                                             |
| ------ | ------- | ------------------------ | ------------------------------------------------ |
| 健全   | 5% 以下 | 外部前提が揃っている     | 継続                                             |
| 要注意 | 5-15%   | 外部依存による停止が発生 | 依存を減らす工夫、security evidence 等の事前準備 |
| 危険   | 15% 超  | 運用環境が不安定         | blocker カテゴリ別に原因を深掘り、運用改善       |

---

### 8. 自走率（auto-continue の効果）

```
自走率 = (phase 遷移 - human-check-waiting 停止) / phase 遷移
```

| 水準   | 値       | 評価           | 対応                                                                                               |
| ------ | -------- | -------------- | -------------------------------------------------------------------------------------------------- |
| 健全   | 80% 以上 | 自走が機能     | 継続                                                                                               |
| 要注意 | 60-79%   | 停止が頻発     | stop 理由ログ確認、hook 動作確認                                                                   |
| 危険   | 60% 未満 | 手動介入が多い | SessionStart / Stop hook の manifest 経由有効化、Cursor の場合は `references/cursor-guide.md` 確認 |

---

## 時系列での期待傾向

導入後の時間経過で期待される変化:

### Month 1（導入期）

- 完了率: 50-70%（学習中）
- gate 通過率: 40-60%（運用定着途上）
- Task Size 分布: `standard` が過剰（sizing 判断が未熟）
- Learning Loop: Adopted Patterns が急増

### Month 2-3（定着期）

- 完了率: 70-80%
- gate 通過率: 60-75%
- Task Size 分布: `standard` / `quick` / `express` がバランス
- 差し戻し回数: 平均 2 以下に収束

### Month 4+（成熟期）

- 完了率: 80+
- gate 通過率: 70+
- Learning Loop: 月次で新規パターン 5+ 件追加
- false positive 削減率: 定常的に 10-20%

---

## 赤信号（即対応）

以下のいずれかが発生したら即座に原因調査:

1. **Reviewer Loop Escape Hatch の発動**（同一タスクで 5 回連続 `changes_requested`。procedural / evidence only なら build loop 内で route recalibration、policy-level 変更なら human recheck）
2. **Scope Drift Guard の発動**（同一 steering で design_detail_only が 3 回超）
3. **Blocked Since > 24h のタスク**（SessionStart hook が警告）
4. **同一規約違反の繰り返し**（learned-patterns に既にあるのに reviewer が見逃している）
5. **評価スコアの急落**（`evals/evals.json` のトリガー精度が基準値を下回る）

これらは `gdd-metrics` 出力だけでは見えないので、個別に `.steering/*/tasklist.md` の Attempts / worklog.md を確認する。

---

## チーム外展開 readiness

チーム外へ GDD を広げる前後 1 週間は、通常 KPI に加えて導入事故を直接示す指標を見る。ここで危険水準になった場合は展開継続せず、展開一時停止として原因を直す。

| 指標 | 健全 | 要注意 | 危険時の扱い |
|---|---|---|---|
| resume 成功率 | 80% 以上 | 60-79% | 60% 未満なら展開一時停止。候補選択・Worktree Identity Tuple・compact recovery を確認 |
| worktree 汚染警告 | 0 件 | 1 件 | 2 件以上または未解消なら展開一時停止。混線リスクが残るため新規 task を増やさない |
| HITL 差し戻し率 | 30% 以下 | 30-50% | 50% 超なら HITL の承認サマリと技術スタック確認を見直す |
| superpowers 混入率 | active GDD 中 0 件 | 1 件 | active GDD 中に workflow handoff したら展開一時停止。`GDD Workflow Lock` を再周知 |
| GDD owner 曖昧化 | 0 件 | 1 件 | `superpowers の指示に従い` / `gdd-dev 相当` / Project Skill を workflow owner にする表現が出たら展開一時停止。Codex goal continuation と Task Binding 解決を確認 |
| post-merge follow-up 再利用違反 | 0 件 | 0 件以外 | 元 worktree 再利用が出たら展開一時停止。latest default branch から切り直す |

展開継続の最低条件:

- 代表タスク 3 件で human check 到達と resume が成功する
- worktree 汚染警告が未解消のまま実装に進まない
- HITL で「OK で許可される最大到達点」と「OK でも許可されないこと」を承認者が説明できる
- active GDD 中は state.md / tasklist.md / worklog.md が workflow owner として更新される
- Codex goal continuation と SessionStart reboot task が食い違う場合、reboot task を自動採用せず Task Binding / PR / branch / worktree で解決する

---

## チーム内での運用リズム

### 毎週（テックリード）

- `gdd-metrics` 実行
- 完了率・gate 通過率・Blocked 率を確認
- 赤信号が出ていたら個別に worklog を確認

### 毎月（チーム全体）

- Learning Loop 指標の推移確認
- Adopted Patterns の内容共有（チーム内勉強会に組み込み）
- task size 分布が偏っていたら sizing 判断の見直し

### 四半期（運用担当）

- baseline 値をチームの実績で更新
- 運用レベル（strict / standard / light）の見直し判断
- v1.0 昇格基準（`docs/VERSIONING.md`）との照らし合わせ

---

## ベースライン調整の方法

本文書の baseline 値は **一般的な目安**。チームの状況に合わせて調整する:

### 厳しくする方向（品質重視チーム）

- 完了率: 健全 ≥ 85%、gate 通過率: 健全 ≥ 80%
- 差し戻し回数: 健全 ≤ 1.2
- Blocked 率: 健全 ≤ 3%

### 緩める方向（experimental / 研究開発）

- 完了率: 健全 ≥ 70% で可
- gate 通過率: 健全 ≥ 60% で可
- Task Size 分布: `standard` が多くても許容

**調整時の注意**: baseline を変える場合は `.gdd-config.md` または team-specific な CLAUDE.md で宣言し、チーム内で合意を取る。

---

## KPI 収集の自動化

現状 `gdd-metrics` は手動実行。将来の自動化候補:

- cron で日次実行して CSV 出力 → Grafana / Datadog で可視化
- 月次で Slack channel に post
- PR description に `gdd-metrics` 出力を自動添付

（これらは plugin scope 外の運用実装。実装時は導入チーム側で整備する）

---

## 参考

- メトリクス収集手順: `skills/gdd-metrics/SKILL.md`
- Reviewer Learning Loop: `references/cross-task-learning.md` / `references/inline-review-checklists.md` § Reviewer Calibration
- Reviewer Loop Escape Hatch: `references/rollback-patterns.md`
- 運用レベルの定義: `references/operation-levels.md`
