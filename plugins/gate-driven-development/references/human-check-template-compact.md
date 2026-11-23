# Compact Human Check Template

> **所有**: human check の一次表示
> **上位正本**: `references/human-check-template.md`
> **目的**: 詳細表を読まなくても、OK で AI が自走してよいかを判断できる最小表示を作る

一次表示に置くのは、前置き 3 行（§ 判断の書き方 2）と、判断ポイントと OK の範囲だけである。整理した要件・実装する方法・内容・変更予定ファイル・検証する方法・内容・ズレ確認・trace・レビュー履歴は、`requirements.md`（目的・スコープ・受入条件・実装方針・影響範囲）・`request-crosscheck.md`・`state.md` に書き、一次表示ではその場所を指す 1 行にする。事実（欄名・数値）は AC の値に `AC-n` を添え、言い換えない。判断ポイントは方向性を除き 2 件以内。行数の目安は `scripts/lib/hitl_budget.py` の `PRIMARY_SURFACE_MAX_LINES` が正本（sizing 別）。

## Template

```markdown
## 確認

**依頼**: <`request.md` の初めのユーザーの発言をそのまま引用>
**なぜやるか**: <解決する問題と根本原因>
**現在地**: <済んだ工程と、返事で次に始まること>

<次の 1〜2 文: 決めてほしいことの数と、それぞれの中身。最後に OK の中身を閉じる 1 文（§ 判断の書き方 8）>

### 判断ポイント
承認ポイント数: <N>
1. <何をする案か> — 変更前: <現状> / 変更後: <採用案> / 採用しない案: <却下案>
   - 材料: <いまの状態→分かったこと→起こりうること→各案で残るもの。指摘などは件数と場所の 1 行>
   - 選択肢2つ以上: 推奨案: <案> / 判断軸: <決め手の軸と一言。推奨案が要件の充足度か信頼境界・fail-closed で ○ でなければ、その軸も書く。軸: 要件の充足度、信頼境界・fail-closed、確かめやすさ、堅牢性、保守性、費用> / 相談役の推奨: <2 本の Opus の案と食い違い。main 記入>
   - 判断に影響する前提: <崩れたら結論が変わる条件。無ければ「なし」>
   - この案を選ぶと次に何が起きるか: <実装・成果物・後続 phase への影響を 1 行>
   - 依頼との差: なし
   - 無回答時のデフォルト: <既定で選ばれる案とその結果を 1 行。定型文禁止。依頼より狭い案を既定にしない>
2. <無ければ削る>／根拠の母集団: <件数・実測時のみ。N の出典集合と代表性>

### どこまで自走するか（どこまで自走するのか）
- OKで進む範囲: <実装 / テスト / review / PR 作成 / 設定キーがあれば外部レビュー収束まで（不在なら「収束までは選択不可」を併記）。`マージまで` 以上は既定にせず、動く CD と環境（本番なら本番、不明は `不明`）、QA までは書き込み先も>
- OKでも許可されないこと: merge / deploy / apply / production write / external posting など（自走上限の値で許す操作は除く）
- 判断の委任: Fable に任せる（既定）/ 人に止める / 相談役に任せる（Opus に 2 本並行で相談、割れたら人に止める）/ Opus に任せる（`human-check-template.md` § 自走上限の置換値）
- 人間に戻す条件: <満たせない見込み / AC・scope を削る・弱める / 信頼境界を緩める / dangerous operation>（依頼の中で足す・技術を変えるなら戻さない）
- 延期・削除: なし | 取りに行かない: <当初目的>（依頼より狭めた変換の行）
- 具体化: なし | <扱い> <語 | なし> → <変換後>（AC-n）
- 今やること: <判断ポイントへの返事> / OK後: <次の phase と残タスク>

<次の 4 節と Multiple PR は当たらなければ書かず、タグは none>
### 選択肢の説明
<Option A / B / C を使うとき（詳細は § Option Completeness）>

### アーキテクチャ選択
<複数の妥当な選択肢があるとき。勝手に単一案へ丸めない（詳細は § アーキテクチャ選択（条件付き詳細））>

### 段階実装（段階実装サマリー）
<Stage list summary / 後続PR着手前に再承認>

### ズレ確認
<人に残った行（`質問` にした行の質問の文、`既存とぶつかる`〔未決のものと、ユーザーの決めた規則・方針に触れる仮決定〔`記録の場所: なし` も落とさない〕〕、`突き合わせ: unavailable`・`判定できない`・`依頼の原文: なし` の行）だけ。無ければ節ごと書かず `zure="none"`>

### Multiple PR Strategy Options
<複数PR・後続PR・post-merge verification があるとき（詳細は § Multiple PR Strategy Options）>

詳細: 整理した要件・実装する方法・内容・変更予定ファイル（WHERE）・検証する方法・内容は `<steering path>/requirements.md`、依頼の原文との突き合わせは `request-crosscheck.md`
<gdd-hitl-fields options="none|filled" arch="none|filled" zure="none|filled" multi-pr="none|filled" stage="none|filled" request-diff="none|differs,…">
<gdd-stop reason="human-check-waiting">
## 👤 次にすること
OK で承認（差 なし の点） / 直す点を返信
```

## Required Words

以下の意味を必ず含める。**見出し名は本ファイルの表記のまま使う**。末尾のタグの値は `none`/`filled` の一方（そのまま書かない）。

- 詳細の場所を指す 1 行（`詳細:`）に、整理した要件・実装する方法・内容・変更予定ファイル（WHERE）・検証する方法・内容の語と、その場所。中身は一次表示に書かない
- どこまで自走するのか
- 判断ポイント
- 複数段階なら段階実装
- この案を選ぶと次に何が起きるか / 依頼との差（`なし`。狭める案は採用しない案に AC つきで並べる）/ 無回答時のデフォルト
- 判断に影響する前提 / 完了条件の変換（`延期・削除:` の行は決定論で機械検査。`具体化:` の行は検査せず、行に「完了条件の変換」と書かない。詳細は上位正本）
- OKでも許可されないこと
- 人間に戻す条件
- Option A / B / C を使う場合は選択肢の説明
- 複数の妥当な選択肢がある architecture / CI / IaC policy / runtime / framework / test tooling / access method / credential backend は アーキテクチャ選択 の要約または条件付き詳細
- 複数PRになる場合は Multiple PR Strategy Options
- 実測・件数を根拠に出す場合は根拠の母集団（`lint-hitl-decision-quality.py` が決定論で要求する）

## Option Completeness

- `Option B` だけを判断ポイントに出さない。`Option A / B / C`（何をする案か・良い点・弱い点・AIの仮決定）を `選択肢の説明` で定義する

## アーキテクチャ選択（条件付き詳細）

- 一次表示には判断に効く行だけを置く。既存 repo 標準、業界標準 / vendor official、最小の自前実装の詳細表は requirements.md / design.md に置く
- DRY / KISS / YAGNI、採用しない理由、人間に確認する点のうち、後戻りが大きい判断だけ HITL に出す
- 用語の定義（`業界標準 / vendor official` の解釈）と技術別の第一候補は上位正本の § アーキテクチャ選択 に従う

## Multiple PR Strategy Options

複数PR、後続PR、post-merge verification、または段階実装でPRをまたぐ場合は、最低限、単一PR / 複数PR / 後続PR着手前に再承認 の 3 つを比較し、AI の仮決定、後続の追跡先、同じチャットで続けるか / 別チャットへ渡すか、次に進む条件 / 人間に戻す条件を出す。
