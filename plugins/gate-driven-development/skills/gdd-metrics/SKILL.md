---
name: gdd-metrics
description: "Use when the user asks for GDD metrics, statistics, gate pass rates, tuning evidence, or whether a skill / prompt revision actually improved anything (before/after scorecard)."
version: 0.2.0
---

# GDD Metrics

完了済み・進行中の GDD タスクから定量データを収集し、ワークフローの健全性を可視化する。

## Goal

- gate 通過率・差し戻し率を数値で把握できるようにする
- Reviewer Learning Loop の効果（false positive 削減）を計測する
- タスクサイズ分布・完了傾向を可視化する
- 運用レベルやレビュー設定の調整根拠を提供する

## Fixed Model

- `Claude Code`: `sonnet` + `effort=low`
- `Cursor`: `Grok 4.5` + `reasoning.effort=low` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=low`
- 集計と表示だけでも state / tasklist を読むため、mini には落とさない

## Steps

**推奨: deterministic script を使う**

AI dispatch で集計するより、`scripts/collect-gdd-telemetry.py` を呼び出した方が
速くて安く、結果も同じ。AI を経由するメリットがあるのは「数値を見て解釈や次アクションを
ユーザーに提案する」場合のみ。

```sh
# 現 repo の .steering/ を集計（既定 = text format）
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect-gdd-telemetry.py

# 全 worktree 横断
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect-gdd-telemetry.py --include-worktrees

# JSON / CSV 出力（dashboard 連携用）
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect-gdd-telemetry.py --format=json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect-gdd-telemetry.py --format=csv
```

script は以下を抽出する:

- タスク数（done / in-progress / cancelled / blocked）
- Task Size 分布
- Gate 通過率（requirements / design / human-check）
- Fix Attempts 集計
- Route In Progress 分布
- Entry Intent 分布
- Reviewer Lineage 動的追加件数（SMI / Impact Block 由来）
- Error Log エントリ数

**AI dispatch で集計する場合の手順（script 不可な環境用）**

1. git worktree を列挙し、`.steering/` を含む全 worktree を探す。main branch の `.steering/` も対象にする。
2. 各 steering ディレクトリから以下を読む:
   - `state.md` — gate status、差し戻し回数（Route In Progress 履歴）
   - `tasklist.md` — タスク数、完了数、Verification 結果、Attempts 記録
   - `requirements.md` 冒頭 — Task Size
   - worktree ごとに 1 つ、worktree 直下の `docs/learned-patterns.md`（存在する場合。置き場の正本は `references/cross-task-learning.md`）— Adopted Patterns / Rejected Alternatives / Calibration 記録
3. 以下のメトリクスを算出する:

### Workflow Metrics

| メトリクス           | 算出方法                                                   |
| -------------------- | ---------------------------------------------------------- |
| **タスク数**         | steering ディレクトリの数（完了 / 進行中 / 中断）          |
| **タスクサイズ分布** | Task Size 別の件数（trivial / express / quick / standard） |
| **gate 通過率**      | `Requirements Review Status=approved` / 全タスク           |
| **差し戻し率**       | `changes_requested` の発生回数 / gate 実行回数             |
| **平均差し戻し回数** | Attempts セクションの attempt 数の平均                     |
| **完了率**           | `Next Action=done` / 全タスク                              |

### Reviewer Learning Loop Metrics

| メトリクス                   | 算出方法                                                 |
| ---------------------------- | -------------------------------------------------------- |
| **Adopted Patterns 数**      | `learned-patterns.md` の Adopted Patterns エントリ数     |
| **Rejected Alternatives 数** | Rejected Alternatives エントリ数                         |
| **Code Conventions 数**      | Code Conventions Discovered エントリ数                   |
| **Calibration 適用回数**     | tasklist.md の Attempts 内で `calibration:` を含む記録数 |
| **severity 調整回数**        | `calibration:` 記録のうち severity が下がったケースの数  |

4. 以下のフォーマットで出力する:

```
## GDD Metrics

### Overview
| メトリクス | 値 |
|-----------|-----|
| 総タスク数 | N |
| 完了 | N |
| 進行中 | N |
| 中断 | N |
| 完了率 | N% |

### Task Size Distribution
| サイズ | 件数 | 割合 |
|--------|------|------|
| trivial | N | N% |
| express | N | N% |
| quick | N | N% |
| standard | N | N% |

### Gate Performance
| Gate | 通過 | 差し戻し | 通過率 |
|------|------|---------|--------|
| Requirements Review | N | N | N% |
| Design Review | N | N | N% |
| Implementation Review | N | N | N% |
| Completion Review | N | N | N% |

### Reviewer Learning Loop
| メトリクス | 値 |
|-----------|-----|
| Adopted Patterns | N |
| Rejected Alternatives | N |
| Code Conventions | N |
| Calibration 適用回数 | N |
| severity 調整回数 | N |
| 推定 false positive 削減率 | N% |

推定 false positive 削減率 = severity 調整回数 / (gate 差し戻し総数) * 100
（calibration データが無い場合は「データ不足」と表示）
```

5. steering が 1 つも見つからない場合は「完了済みの GDD タスクがありません。`/gdd-dev` でタスクを実行すると、ここに実績データが蓄積されます。」と返す。

## 改訂の採否をスコアカードで判定する

skill / prompt / reviewer 設定を変えたとき、「良くなった気がする」で採否を決めない。
改訂前後の telemetry snapshot を `scripts/gdd-scorecard.py` に食わせ、実際に走った
task の行動メトリクスだけで `adopt` / `reject` / `mixed` / `inconclusive` を出す。

```sh
# 1. 改訂を入れる前にベースラインを取る
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect-gdd-telemetry.py --include-worktrees --format=json > /tmp/gdd-baseline.json

# 2. 改訂を入れて通常どおり運用する（task が数件たまるまで待つ）

# 3. 改訂後の snapshot を取って判定する
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/collect-gdd-telemetry.py --include-worktrees --format=json > /tmp/gdd-candidate.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gdd-scorecard.py --baseline /tmp/gdd-baseline.json --candidate /tmp/gdd-candidate.json

# 指標の定義（方向・何の proxy か）を確認する
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gdd-scorecard.py --list-metrics
```

**指標定義の正本は script 内の `METRICS` registry**。ここには一覧を複製しない
（複製すると片方だけ直って乖離する）。追加・変更は registry と契約テストで行う。

### 判定の読み方

- `adopt` — 改善指標があり、悪化指標がない。改訂を残してよい
- `reject` — 悪化のみ。改訂を戻す
- `mixed` — 改善と悪化が同居。トレードオフを人間が判断する
- `inconclusive` — **判定できるだけの実績がない。これは失敗ではなく正常な結果**

### 過剰主張を避ける仕組み

- candidate snapshot は baseline の task を内包するため、`steering_id` が baseline に
  ある task は自動で除外される（除外数は `carried_over_excluded` に出る）
- 母数が `--min-samples`（既定 3）未満の指標は `insufficient_data` にする
- 差が「task 1 件分の振れ幅」以下なら `flat` にする。n=4 の割合指標は task 1 件で
  25 ポイント動くため、これがないと 1 件の偶然を改善と誤認する

**Why:** 個人〜小チーム運用では A/B テストに必要な母数が集まらない。統計的有意性の
代わりに「母数が足りなければ足りないと言う」ことで、改訂の効果を過大評価しない。

## 導入効果の測定（Before/After KPI）

チーム導入時に GDD の効果を定量的に示すための指標テンプレート。`gdd-metrics` の出力データと、外部ツール（GitHub / CI）のデータを組み合わせて測定する。

### 測定方法

導入前の 1〜2 週間のベースラインを記録し、導入後 1 ヶ月時点と比較する。

### KPI テンプレート

```
## GDD 導入効果レポート

### 品質指標
| 指標 | 導入前 | 導入後 | 変化 |
|------|--------|--------|------|
| PR レビューでの changes_requested 率 | N% | N% | ↓N% |
| 本番障害件数（月） | N | N | ↓N |
| レビュー差し戻し後の修正回数（平均） | N | N | ↓N |

### 速度指標
| 指標 | 導入前 | 導入後 | 変化 |
|------|--------|--------|------|
| タスク着手→PR 作成までの時間（中央値） | Nh | Nh | ↓Nh |
| 中断→再開までの復帰時間（中央値） | Nmin | Nmin | ↓Nmin |
| PR マージまでの時間（中央値） | Nh | Nh | ↓Nh |

### プロセス指標（gdd-metrics から取得）
| 指標 | 値 | 傾向 |
|------|-----|------|
| gate 通過率（implementation） | N% | ↑安定 |
| 差し戻し率 | N% | ↓改善 |
| Reviewer Calibration 適用回数 | N | ↑学習進行 |
| 推定 false positive 削減率 | N% | ↑改善 |

### 定性フィードバック
- 開発者の声: 「...」
- レビュワーの声: 「...」
```

### データソース

| 指標カテゴリ       | データソース                                            |
| ------------------ | ------------------------------------------------------- |
| 品質指標           | GitHub PR データ（`gh pr list`）、障害管理ツール        |
| 速度指標           | GitHub PR タイムスタンプ、GDD state.md のタイムスタンプ |
| プロセス指標       | `gdd-metrics` の出力                                    |
| 定性フィードバック | チームメンバーへのヒアリング                            |

**Why:** 「AI ツールを入れたら良くなった気がする」ではなく、数値で効果を示すことでチーム内外への説得力が上がる。特に品質指標の改善は、導入コスト（学習時間）との比較で判断材料になる。

## Guardrails

- 状態の表示だけを行い、state を変更しない
- `Resume From` / `Next Action` を更新しない
- reviewer を起動しない
- artifact を作成・更新しない
- `gdd-stop` タグは使わない（状態表示は terminal action ではない）
