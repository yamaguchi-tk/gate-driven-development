# GDD vs superpowers Worked Examples

> **所有**: 同じタスクを GDD primitive / superpowers primitive 両方で実行した場合の体験差を示す demo 集
> **参照元**: `README.md` / `references/superpowers-overlap.md` の補強として、利用判断の判断材料を実例で提示

## 構成

各シナリオで以下を並記する:

- **タスク**: 1 段落の状況設定
- **superpowers での実行**: 期待される素の挙動と artifact 出力
- **GDD での実行**: state.md / tasklist.md / adr.md / learned-patterns.md への波及
- **差別化ポイント**: どこで「GDD でやってよかった」/「superpowers の方が軽かった」が出るか

これは **conceptual walkthrough**（実 benchmark ではなく挙動の比較例）。実 benchmark は `benchmark-scenarios.md` の subagent eval で取得する。

## Example 1: 単一 commit regression（軽量 debug）

### タスク

`pytest tests/test_pagination.py::test_cursor` が `AttributeError` で失敗。直近 commit でメソッド名がリネームされた疑い。

### superpowers での実行

```
1. superpowers:systematic-debugging 起動
2. Phase 1 (Root Cause): error message / git log で commit 特定
3. Phase 2-3: skip（root cause 明確）
4. Phase 4: fix 実装、test pass で完了
```

artifact: なし（standalone debug）。次回同じ症状が来たら最初から探索しなおす。

### GDD での実行

```
1. /gdd-dev pagination cursor test が失敗する → quick (express) と判定
2. brainstorming → requirements-gating → human-check
3. gdd-test-failure-debug-pack → root-cause-investigation 呼び出し
4. Phase 4 で SMI block 出力:
   - ADR 起票: 不要（既存設計前提に変更なし）
   - Reviewer Lineage 追加提案: なし
   - Routing 提案: gdd-subagent-driven-implementation
5. gdd-systematic-debugging が SMI を受けて Routing 確定
6. gdd-subagent-driven-implementation で fix 実装
7. impl-gate 通過 → completion-check → done
8. learned-patterns.md に「commit-rename type の regression は git log -S で 1 件特定可能」を記録
```

artifact: `state.md` / `tasklist.md` / `worklog.md`（Error Log）。

### 差別化ポイント

- **superpowers が速い**: 0 ゲート / 0 artifact で即実行
- **GDD が効く**: 次回同じ commit-rename パターンが来たら learned-patterns で探索短縮、reviewer Lineage で同種の reviewer 種別を事前提案
- **使い分け**: 単発で完結する debug → superpowers。1 週間に 3 回同じ regression が出る環境 → GDD で蓄積する価値あり

## Example 2: 機能追加 with security boundary

### タスク

API レスポンスにキャッシュ層（Redis）を追加したい。auth middleware の前段に置く想定。

### superpowers での実行

```
1. superpowers:brainstorming で要件 1 案を出す
2. superpowers:test-driven-development で RED → GREEN
3. superpowers:requesting-code-review で security 観点をレビュー依頼（手動）
4. 完了
```

artifact: なし。auth middleware と Redis cache の境界判断は reviewer の手動チェック頼み。

### GDD での実行

```
1. /gdd-dev API レスポンスにキャッシュ層追加 → standard 判定
   - security keyword 検出（auth）→ 自動的に gdd-security-reviewer 起動
2. brainstorming で Value-Based Scope Narrowing を提示:
   - Option A: Redis のみ追加（auth は変更なし）
   - Option B: Redis + auth middleware への TTL 統合
   - Option C: やらない（メモリキャッシュで十分か再検討）
3. human-check で Option A 採用
4. design-gating で security boundary を明示（Redis 経由で auth 情報を漏らさない設計）
5. task-breakdown で Implementation Reviewer Selection の初期枠に gdd-security-reviewer を入れる
6. implementation 中に Spec Change Detection 発火（cache key に session_id を含めた）
   - Impact Block 出力: Reviewer Lineage 追加提案=gdd-security-reviewer + added_by=impact_block
7. impl-gate で security-reviewer が cache key の session_id 含有を検出 → changes_requested
8. fix（cache key の hash 化）→ impl-gate 通過
9. completion-check:
   - Step 4b: SMI / Impact Block 蓄積記録の確認 → ADR 起票要件 / Reviewer Lineage 反映を全件 OK
   - AC Drift Check 通過 → done
10. Post-Completion Learning:
    - Reviewer Lineage Patterns に「cache + auth boundary」signature で gdd-security-reviewer 必須を記録
    - adr.md に「cache key に session_id を含めない」決定を記録
```

artifact: `requirements.md` / `design.md` / `tasklist.md` / `adr.md` / `learned-patterns.md`。

### 差別化ポイント

- **GDD が決定的に効く**: cache key session_id 漏洩を impl-gate 段階で検出（reviewer Selection 初期枠 + Spec Change Detection の二重防御）
- **superpowers で再現する場合**: 手動で security reviewer を選んで依頼する必要があり、忘れると本番事故
- **使い分け**: security boundary に触れる変更 → GDD が低リスク。auth に触れない pure cache 追加 → superpowers でも十分

## Example 3: flaky test 調査

### タスク

`tests/test_async.py::test_event_order` が CI で 30% の頻度で失敗。local では再現しない。

### superpowers での実行

```
1. superpowers:systematic-debugging → Phase 1 で再現性 deterministic 不可
2. root-cause-tracing.md / condition-based-waiting.md（superpowers 側 reference）を参照
3. flaky の根本原因を特定（例: setTimeout 100ms 待ち → 200ms に変更）
4. 完了
```

artifact: なし。次回別 test が flaky になっても再度同じ調査が必要。

### GDD での実行

```
1. /gdd-dev test_event_order が flaky → quick (express) 判定
2. brainstorming → requirements-gating → human-check
3. root-cause-investigation 呼び出し
   - Phase 1 で deterministic 再現失敗を検出 → Phase 2/3 で flaky 仮説
   - GDD の condition-based-waiting.md を参照（setTimeout anti-pattern 検出）
4. Phase 4 で SMI block 出力（root cause 未確定パス）:
   - 一次原因（仮説、未確定）: setTimeout 固定時間待ち
   - 最優先アクション: 追加データ収集（waitFor に置換 + 100 回連続実行）
   - 意思決定 question: 「データ収集に着手しますか? それとも flaky として retry / monitor に倒しますか?」
5. ユーザーが「データ収集」選択 → 観測強化 task に分解
6. 実装で setTimeout → waitFor に置換
7. 100 回連続実行で再現率 0% を確認
8. completion-check で done
9. Post-Completion Learning:
   - learned-patterns.md に「async test の flaky は setTimeout 固定待ちが第 1 容疑」記録
   - common-failure-patterns.md（GDD 側 reference）の timing パターンとリンク
```

artifact: `requirements.md` / `worklog.md` / `learned-patterns.md`。

### 差別化ポイント

- **GDD が効く**:
  - Phase 4 が「未確定でも fix を当てない」Iron Law を強制（superpowers にもあるが GDD では SMI block で routing にも反映）
  - 100 回連続実行のような verification を tasklist の Verification field に正式記録
  - 次回別 test が flaky になったとき learned-patterns で第 1 容疑が即出る
- **superpowers が速い**: 単発の flaky なら GDD ceremony は冗長
- **使い分け**: flaky が「初めて見る test」→ superpowers。「うちの async test、また flaky になった」が定常的 → GDD で pattern 蓄積

## まとめ表

| シナリオ | superpowers 推奨 | GDD 推奨 | 決め手 |
|---|---|---|---|
| 単一 commit regression | ○ 速い | △ ceremony 過剰 | 再発頻度。1 回限りなら superpowers |
| security boundary 変更 | △ 手動依頼必須 | ◎ 自動 reviewer + 二重防御 | reviewer 漏れ事故のコスト |
| flaky 初遭遇 | ○ 速い | △ ceremony 過剰 | チーム内で flaky 頻発するなら GDD |
| 機能 amendment（既存修正） | △ artifact 無し | ◎ Entry Intent + ADR 連鎖 | 過去判断の再現性 |
| 1 行 typo 修正 | ○ 即実行 | trivial で同等 | どちらも 0 ゲート |

## 関連

- `superpowers-overlap.md`: GDD / superpowers の primitive 別 overlap map と推奨使い分け
- `benchmark-scenarios.md`: 実 subagent eval で精度 / steps / duration を測るシナリオ集
- `README.md` § 「Superpowers と併用するときの使い分け」: ユーザー向け使い分けガイド

## Direct Intent スコアの計算例（`references/task-sizing.md` より移送）

算出ルールは `references/brainstorming-steps.md` § 7b（Direct Intent 判定）の 5 条件（ファイル・関数名指し +2 / 実装方式・ライブラリ指定 +1 / 期待入出力具体提示 +1 / 過去同型実績 +1 / 目的だけで手段未指定 -3）を正本とする。

**例 1**: `gdd-model-routing/SKILL.md の cheap_readonly 行にある「Haiku」を「Haiku 4.5」に変えて。表の他の行・他の列は変えない`
- ファイル・関数名指し（ファイル内の対象行を名指し＝位置まで特定）(+2) + 実装方式・ライブラリ指定(0) + 期待入出力具体提示（変更前後の文言を明示）(+1) + 過去同型実績(0) + 目的だけで手段未指定（該当なし。手段=文言置換を明示）(0) = **3点** → Direct Intent
- Express と組み合わせ → Options Exploration skip + Refinement 1回制限

**例 2**: `ログイン画面にパスワードリセット機能を追加したい`
- ファイル・関数名指し(0) + 実装方式・ライブラリ指定(0) + 期待入出力具体提示(0) + 過去同型実績(0) + 目的だけで手段未指定（該当。目的のみで実装方式の指定なし）(-3) = **-3点** → 通常フロー

**例 3**: `認証基盤を OAuth2 に移行したい`（standard タスク）
- ファイル・関数名指し(0) + 実装方式・ライブラリ指定「OAuth2」(+1) + 期待入出力具体提示(0) + 過去同型実績(0) + 目的だけで手段未指定（該当なし。手段=OAuth2 移行を明示）(0) = **1点**
- standard タスクでは、上記スコアとは別に Direct Intent を適用しない（`self-contained-contract.md` § direct intent 契約）→ 通常フロー

## quick サイズのサンプル（旧 `references/` 配下の `team-onboarding.md` より移送。現在は `docs/references-archive/team-onboarding.md`）

### サンプル: requirements.md（quick サイズ）

```markdown
Task Size: quick

## Summary Brief

### 一言
ユーザー一覧画面にカーソルベースのページネーションを追加する

### 判断材料
- 確定事項: REST API は既存の GET /users を拡張
- 未確定事項: 1ページあたりのデフォルト件数
- やらないこと: 検索機能の追加
- 外部依存の確認結果: なし
- 設計方針: カーソルベース（オフセットベースより大量データに強い）

### 承認ポイント
1. **方針**: カーソルベースのページネーションを採用する
   - 採用案: カーソルベース（ID ベースの次ページ取得）
   - 代替案: オフセットベース（シンプルだがデータ量に弱い）
   - → OK / 別案希望

2. **スコープ**: API のみ変更、フロントエンドは別タスク
   - → OK / 修正依頼

## 目的
大量のユーザーデータを効率的に表示するため、ページネーションを導入する。

## スコープ
- GET /users API にカーソルパラメータを追加
- レスポンスに next_cursor を含める
- 既存のテストを拡張

## 受入条件
- AC-1: GET /users?cursor=xxx&limit=20 でカーソルベースのページ取得ができる
- AC-2: レスポンスに next_cursor が含まれ、次ページの取得に使える
- AC-3: cursor が無効な場合は 400 エラーを返す
- AC-4: 既存の GET /users（パラメータなし）は従来通り全件返す

## 実装方針
- users テーブルの id をカーソルキーとして使用
- limit のデフォルトは 20、最大は 100
```

### サンプル: design.md（quick サイズ）

```markdown
## Summary Brief

### 一言
GET /users API にカーソルベースのページネーション機能を追加する

### 判断材料
- requirements.md の承認済み方針に従う
- カーソルキーは users.id（PK、auto increment）

## 変更点の要約
- `src/api/users.ts` に cursor / limit パラメータを追加
- `src/repository/user-repository.ts` にカーソルクエリを追加
- レスポンス型に `next_cursor: string | null` を追加

## テスト方針
- 正常系: cursor あり / なし、limit 指定あり / なし
- 異常系: 無効な cursor、limit が範囲外
- 境界値: 最終ページ（next_cursor が null）
```
