🔍 確認をお願いします

GDD scenario evals の no-post scoreability（実際に外部へ投稿せず、reviewer / PR 相当の判定品質を測れるようにする改善）について、実装方針の承認をお願いします。

### 選択肢の説明

- **Option A**: 新しい no-post 専用の評価コンポーネントを追加する。既存の scenario runner とは独立させ、専用スキーマ・専用スコアラーを新規実装する
- **Option B: 何をする案か**: 既存の GDD scenario runner / status artifact / score / compare path を拡張し、実際の外部投稿（PR 作成・wiki への投稿など）を行わずに no-post scoreability を計測できるようにする。新しいコンポーネントは作らず、既存の `run-gdd-scenario-evals.py` の入出力契約に no-post モードを追加する形にする

Option B を推奨します。理由は、既存の deterministic scorer / artifact collector をそのまま流用でき、新規コンポーネントによる契約の二重化を避けられるためです（YAGNI）。

### 検証計画

- **どこで確認するか**: 生成された scenario report、status/score artifact、no-post smoke 出力
- **どう確認するか**: `run-gdd-scenario-evals.py` を no-post モードで実行し、summary JSON の `overall_status` / `status_counts` / checklist 結果を既存の green fixture と比較する
- **OK条件**: no-post モードでの critical checklist が既存の post モードと同じ pass 数になり、score / compare の差分が説明可能な範囲であること
- **失敗時の扱い**: no-post や score artifact が生成できない場合、その scenario は `unavailable` として分類済み未検証のまま扱い、PR ready / 完了とは言わない。green として誤報告しない

### 判断ポイント（OK / 別案希望 で回答してください）

1. Option B（既存 scenario runner の拡張）で進めてよいですか？
2. no-post scoreability の対象は今回 P0 の scenario corpus に限定し、P1/P2 は後回しでよいですか？

自走範囲は「実装完了と PR 作成まで」、merge / deploy は別承認です。

OK なら「OK」と返してください。変更したい点があれば、その承認ポイント番号で指示してください。

<gdd-stop reason="human-check-waiting">
