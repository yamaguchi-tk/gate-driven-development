## 確認

### なぜやるか（WHY・根本原因）
障害対応で repo 単位の索引しか無く、該当 path に辿り着けないため。

### 何を作るか（整理した要件）
AWS inventory の事前学習を path 単位へ拡張します。

### どう作るか（実装する方法・内容）
既存の source evidence chain を再利用し、path index を追加します。

**変更予定ファイル（WHERE）**: scripts/build-path-index.py / references/inventory.md

### どう確かめるか（検証する方法・内容）
unit と contract で path index の生成と参照解決を確認します。

### 現在地
完了フェーズ: 要件整理 / 今やること: OK 判断 / OK後: 設計 / 残タスク: 実装・レビュー

### どこまで自走するか（どこまで自走するのか）
- OKで進む範囲: 実装 / テスト / review / PR 作成
- OKでも許可されないこと: merge / deploy / apply / production write
- 人間に戻す条件: scope / AC / security / architecture の変更

### 判断ポイント
1. 索引の粒度 — 変更前: repo 単位 / 変更後: path 単位 / 採用しない案: 全文検索
   - この案を選ぶと次に何が起きるか: path index の生成コストが増え、後続の対応でcacheが要る
   - 無回答時のデフォルト: path 単位を採用し、cacheは後の対応に送る

### 段階実装（段階実装サマリー）
single-stage: 今回の PR で完結

### ズレ確認（後戻りが大きいものだけ）
完了条件の変換: source evidence が保存されることを完了条件に読み替えています。

## 👤 次にすること
OKで承認してください

<gdd-stop reason="human-check-waiting">
