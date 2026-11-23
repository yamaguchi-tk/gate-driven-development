# R9-2 pilot 監査シート: brainstorming-steps.md（2026-07-16）

対象: `plugins/gate-driven-development/references/brainstorming-steps.md`（repo 移植時点 517 行。pilot 実施時のローカル原本は 513 行）
ルーブリック: keep（low freedom 契約）/ rewrite-to-intent（意図+例へ圧縮）/ delete（旧モデル補正・重複）/ relocate（原本退避で代替）
原本退避先: `docs/references-archive/brainstorming-steps-pre-r9-2-original.md`

## 保存必須の契約（書き直しで維持したもの）

- 契約テスト固定文字列: `Technology Stack Fit Matrix` / `公式統合`（test_hitl_trace_contract）、`artifact-less trivial`（test_worktree_pollution_contract）、`Current State Verification Check` / `gh pr list` / `全実行経路`（test_engineering_baseline_architecture_contract）、`scripts/assert-worktree-ready.py` / `pre-artifact` / `root に \`.steering/\` を作る前に失敗させる`（test_worktree_pollution_contract 連結判定）、Step 4 の root branch guard 文言一式（test_root_branch_guard_contract 連結判定）
- 外部参照アンカー: Step 1〜20 の番号体系、2a / 7s / 7t / 7a / 7b / 8a〜8h / 9 / 9a / 11a / 12a、§ 現状の把握、§ 外部依存コンポーネントの実動作調査、§ Direct Intent 判定（task-sizing が正本指定）、§ Visual Companion、§ 要件変更時の再評価 trigger、Step 15（findings.md）
- 成果物フォーマット: `Intake Brief` の節構成、`<!-- Direct Intent: score=N, signals=[...] -->`、Broad Requirement 判定の記録、Pre-option Scope Narrowing の記録フォーマット、Gate Status 初期値（blocked 一覧）、mockup の置き場所（`/tmp/` の mockup.html・`.steering/<task>/` の mockup.md）、findings.md の記録項目

## 節別判定

| 節 | 旧行数 | 判定 | 処置 |
|---|---|---|---|
| Header | 7 | keep | 原本退避へのポインタ 1 行を追加 |
| Step 1（self-contained） | 2 | keep | そのまま |
| Step 2（entry-intent） | 3 | keep | そのまま |
| Step 2a（Clarification Loop） | 37 | rewrite-to-intent | 発火条件・ready criteria・Intake Brief 契約を保持し、出力ルールの重複説明と長い理由文を圧縮 |
| Step 3（resume） | 4 | keep | そのまま |
| Step 4（worktree 解決） | 17 | keep | 契約文言が集中するため verbatim 維持 |
| Step 5〜6 | 6 | keep | そのまま |
| Step 7/7s/7t（task size） | 24 | rewrite-to-intent + delete | task-sizing・12a と重複する説明をポインタ化。7t アンカー維持 |
| Step 7b（Direct Intent 判定） | 46 | keep（Why のみ delete） | スコア表・記録形式・省略ステップ表は契約。理由文を圧縮 |
| Step 8 + 8a〜8h（技術スタック確認） | 74 | rewrite-to-intent | 各サブチェックを「トリガー→確認→記録先」に圧縮。過去セッション事例の逐語記録は (task id) の括弧書きに縮約（一次記録は原本退避側） |
| Step 9（Problem Discovery） | 99 | rewrite-to-intent + delete | 名前付き check は全て保持。Existing Code Reading Evidence の 11 列列挙は requirements-template（正本）へのポインタに置換（重複 delete）。async_mode 事例等は 1 行化 |
| Step 9a + Pre-option Scope Narrowing | 35 | rewrite-to-intent | 判定条件・必須処理・記録フォーマットを保持、説明文を圧縮 |
| Step 10（Options Exploration + Visual Companion） | 69 | rewrite-to-intent | A/B/C 構成・推奨理由の型・mockup 契約を保持。superpowers 由来の長い説得文を 1 行の意図に置換 |
| Step 11/11a（要件本文・Stack Fit） | 17 | keep（軽圧縮） | 契約文字列保持 |
| Step 12/12a（design skeleton・Complexity 表） | 20 | keep | 表は判定基準の正本 |
| § 要件変更時の再評価 trigger | 13 | keep（軽圧縮） | トリガー条件と (a)〜(d) を保持 |
| Step 13（Gate Status 初期値） | 7 | keep | 成果物形式 |
| Step 14（planning 差し戻し時の追従更新） | 7 | keep | そのまま |
| Step 15（findings.md） | 20 | rewrite-to-intent | 記録項目リストと worklog 使い分けを保持 |
| Step 16/16b/16c（Iterative Refinement） | 26 | rewrite-to-intent | 縮退・打ち切りの数値条件を保持、反復の説得文を削除 |
| Step 17〜20 | 15 | keep | そのまま |

## 判定集計

- keep: 12 節（契約・成果物形式・停止条件）
- rewrite-to-intent: 9 節（手順羅列・説得文・事例逐語）
- delete: 2 箇所（他 references との重複列挙、Why の多重反復）※節ごと削除はなし
- relocate: 過去セッション事例の詳細・長文 Why → 原本退避ファイルで代替

## flag（衝突・注意）

- 実測着地は **139 行（517 → 139、-73%）**（ローカル pilot 時点は 513 → 135。repo 移植で main 側の契約 3 ブロックを原文統合し +4 行）。契約文字列・アンカー・成果物フォーマットは維持（validate-plugin exit 0・契約テスト green）
- **replay eval で検出された回帰と修復（2026-07-16 同日）**: 初回の書き直し（110 行）は、headroom 圧縮で原本を部分的にしか読めていない状態で意味を推測して書いた結果、次の回帰を起こした — ①8a〜8h の意味の取り違え（原本: 8a=外部API統合 / 8b=Runtime環境変数 / 8c=Migration・フォーマット変換 / 8d=IDE互換 / 8e=Command I/F 事前確定 / 8f=Execution・Evaluation Reality / 8g=Tech Stack Fit / 8h=Verification Sanity。初回版は library依存・hook反映経路・既存テスト・Baseline計測を捏造）②Step 12（design.md skeleton → adr.md と誤記）・12a（5次元 低/中/高 評価 → 数値スコア表を捏造）③Step 13（state.md の Gate Status 4 キー → requirements.md の blocked 列挙を捏造）④Step 14（差し戻し追従更新 → ポリシー pre-check を捏造）⑤Step 15（findings/adr/worklog 三分棲み分け + 2 回ルール → 一部欠落）⑥Step 16（16a Gap Scan 6 観点 / 16b Self-Resolve / 16c Update / 16d Re-scan → 16b/16c を別意味で捏造）⑦Step 17〜20・§ 再評価 trigger の条件 (a)〜(d) も原本と相違。全て原本（archive）から逐語確認して復元した
- **教訓（R9-2 wave 1 の手順に反映すべき）**: 蒸留の書き直しは「原本の全文を逐語で確認してから」が絶対条件。部分読み + 記憶での再構成は同型の捏造を再発させる。原本退避（archive コピー）を先に行い、archive を読み直せる状態を作ってから書き直す手順は有効だった
- 「Step 7t」「§ 7a」は外部参照があるためアンカーのみ維持（中身は task-sizing 正本へ委譲）
- replay eval（蒸留前後の gate 判定比較）は本監査シートの範囲外（親セッションで実施）
