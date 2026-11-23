# Verification Before Completion

> **所有**: 完了宣言前の検証（evidence before claims）ルールの集約
> **参照元**: `skills/gdd-completion-check/SKILL.md`（AC verification / done 判定）、`skills/gdd-implementation-gating/SKILL.md`（reviewer approval 前の evidence 確認）、`skills/gdd-subagent-driven-implementation/SKILL.md`（subagent 完了報告の独立検証）

## Core Principle

**Evidence before claims.**

**証拠のない完了宣言は、効率化ではなく嘘である。**

主張する前に検証する。検証しないまま主張するのは、推量を evidence として扱うこと。
fresh verification evidence が無い場合、成功・完了・clean・pass を主張しない。

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

**成功を主張する直前に fresh verification evidence の出力と exit code を読めていない場合、pass とは主張できない。**

- 以前のセッションの実行結果は evidence ではない
- 同じ起動の外（ユーザーの発言か compaction をはさんだ前のターン）で走らせたコマンドも fresh ではない（コードが変わった可能性がある）。同じ起動の中のテストの結果も、§ Fresh の粒度の「同じ起動の中の結果」の条件を満たすときだけ使える
- 「should work」「多分通る」「前は通った」は evidence ではない

### Fresh の粒度

`成功を主張する直前` は completion / status / PR follow-up の最終応答を作る時点で、出力と exit code を自分で読んでいることを指す。`本セッション内` は同じ GDD run の中で、最新の関連変更より後に実行された証跡を指す。

- 同じセッション内でも、検証後に code / test / docs / requirements / tasklist / review response が変わった場合、その検証は fresh ではない（テストの結果は、次の次の箇条のとおり、requirements.md・design.md を除く `.steering/` の記録だけの変更では古くならない）
- 直前の tool 実行で出力と exit code を読めている場合は fresh として扱える
- 同じ起動の中の結果: 同じ起動（subagent の 1 回の起動、または main の 1 ターン。ユーザーの発言と compaction をはさまない）の中で、テストを回した worktree の root（以下 `<wt>`。subagent では prompt の `## Worktree`、main ではテストと同じ Bash 呼び出しで出した `git rev-parse --show-toplevel`）を cwd にして回したテスト（コマンドと引数が完全に同じもの）の出力と exit code は、`<wt>` についての主張にだけ、次の条件を満たすときに fresh として使ってよく、回し直さなくてよい。次のコマンドを、テストを始める直前（テストと同じ Bash 呼び出しの中で、テストより前。例: `git -C "<wt>" rev-parse HEAD && git -C "<wt>" status … && shasum … && <テスト>`）と使う前の 2 回打ち、どれも exit code 0 で終わり、(1) `git -C "<wt>" rev-parse HEAD` の出力が同じ (2) `git -C "<wt>" status --porcelain=v1 --untracked-files=all -- ':/' ':(exclude).steering/'` の出力が空（clean） (3) `shasum` で取った `.steering/<task>/` の requirements.md・design.md の値が同じ（2 回ともどちらのファイルも無いときは (3) を省く）。どれかを満たさない・確かめられない（コマンドが失敗した、テストの cwd が `<wt>` でない、直前の分を出していない）ときは回し直す。使ってよいのはテストの結果だけで、状態確認（`aws` の get 系など）・E2E・lint、`.steering/` を読むテスト（テストのコードを `.steering` で grep して当たるもの、grep で確かめていないもの）、同じ入力で繰り返し実行して結果を比べる手順（E2E の一貫性確認、flaky の再現率、再現性の確認）と、別の起動の結果（subagent の報告、前のセッション）はこの扱いに入らない（§ Subagent 報告の独立検証）
- 会話履歴・subagent の自己申告・古い CI summary だけで、出力と exit code を読めていない場合は fresh として扱わない

## The Gate Function

完了・成功・満足のいずれかを表現する前に、以下 5 ステップを順に踏む。

```
1. IDENTIFY: この主張を裏付けるコマンドは何か？
2. RUN: そのコマンドを fresh に、完全に実行する（テストの結果は、§ Fresh の粒度の同じ起動の中の結果があれば、それを使う）
3. READ: 全出力を読み、exit code を確認し、failure を数える
4. VERIFY: 出力は主張を支持しているか？
   - NO → actual status を evidence 付きで述べる
   - YES → 主張を evidence 付きで述べる
5. THEN: 主張する

いずれかの step を省略した時点で、検証ではなく嘘になる
```

## Common Failures（主張と必要な evidence の対応表）

| 主張 | 必要な evidence | 不十分なもの |
|------|---------------|-------------|
| テストが通る | テストコマンドの出力: 0 failures | 前の起動の実行・§ Fresh の粒度の条件（HEAD が同じ・clean などを 2 回）を満たさない実行 / 「通るはず」 |
| Linter clean | Linter 出力: 0 errors | 部分チェック / 類推 |
| Build 成功 | Build コマンド: exit 0 | Linter pass / ログが良さそう |
| Bug 修正 | 元の症状のテストが pass | コードを変えたから多分直った |
| Regression test が機能 | Red-Green サイクル検証済み | テストが 1 回 pass した |
| Agent 完了 | VCS diff が変更を示している | Agent が「成功」と言った |
| Requirements 充足 | AC 1 行ずつの checklist | テストが通る |

## Red Flags — STOP

- "should" / "probably" / "seems to" を使う
- 検証前に満足を表現する（「素晴らしい」「完璧」「完了」等）
- 検証なしで commit / push / PR を試みる
- agent の成功報告を鵜呑みにする
- 部分的な検証に頼る
- 「今回だけ」と考える
- 疲労していて早く終わらせたい
- **検証せずに成功を含意する、いかなる言い回し**

## Rationalization Prevention（合理化と現実）

| 言い訳 | 現実 |
|--------|------|
| 「動くはず」 | 検証コマンドを実行する |
| 「確信がある」 | 確信 ≠ evidence |
| 「今回だけ」 | 例外なし |
| 「Linter が通った」 | Linter ≠ compiler / test |
| 「Agent が成功と言った」 | 独立に検証する |
| 「疲れている」 | 疲労は例外理由にならない |
| 「部分チェックで十分」 | partial は何も証明しない |
| 「言い回しが違うからルール適用外」 | 文字より spirit |

## Key Patterns（何をどう検証するか）

### テスト

```
✅ [test command を run] [34/34 pass を確認] → 「全テスト pass」
❌ 「should pass now」 / 「looks correct」
```

### Regression test（TDD Red-Green）

```
✅ テスト作成 → Run (pass) → fix を revert → Run (MUST FAIL) → fix 復元 → Run (pass)
❌ 「regression test を書いた」だけ（red-green 未検証）
```

### Build

```
✅ [build コマンド実行] [exit 0] → 「Build passes」
❌ 「Linter passed」（Linter は compile をチェックしない）
```

### Requirements

```
✅ plan を再読 → checklist 作成 → 1 行ずつ検証 → gap または完了を報告
❌ 「tests pass, phase complete」
```

### Agent 委譲

```
✅ Agent が success 報告 → VCS diff を確認 → 変更を独立検証 → actual state を報告
❌ Agent report を trust
```

## GDD の文脈での適用

### Fresh Verification の強制

- **各 AC の検証コマンドは最新の関連変更より後に実行する**。以前のセッションの実行結果や CI ログだけを根拠に `Verification.status=pass` にしない
- CI green / PR check green だけでは不十分。CI ログ内の actual コマンド出力を確認するか、ローカルで再実行する
- テストが「前のセッションで通った」は fresh ではない。コードが変わった可能性がある前提で再実行する

### 完了宣言の言語制限

- evidence は **「テスト X を実行し exit code 0 で pass した」** 形式で記述する
- 「should work」「probably」「seems to」「I think」「I'm confident」などの推量表現は evidence として認めない
- Partial pass（一部だけ動く / happy path だけ通った）は full pass ではない。AC に記載された全条件が満たされていることを確認してから `pass` にする

### Subagent 報告の独立検証

- implementer subagent が「完了」と報告しても、controller 側で `git diff` / `git log` / test 再実行で独立検証してから次の phase に進める
- subagent の自己申告だけで `Current Task` を `Completed Tasks` に移さない
- 4 値 status（`DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED`）のうち `DONE` でも review は省略しない

### Before/After 確認

- 変更前の動作と変更後の動作を比較し、意図通りに変化している（または変化していない）ことを確認する
- 変更箇所だけでなく、周辺の既存動作が壊れていないことも確認する

## When To Apply

**以下の前には常に適用する:**

- いかなる形の成功 / 完了宣言
- いかなる形の満足表現
- work state について肯定的な発言
- commit / PR 作成 / task 完了
- 次 task への移行
- agent 委譲の結果受領
- `Next Action=done` / `Next Action=gdd-completion-check → approved` への遷移

**適用対象の表現:**

- 厳密な phrase
- paraphrase / 同義語
- 成功を含意する間接表現
- 完了 / 正しさを示唆する **あらゆる**コミュニケーション

## Why This Matters

false completion は以下を引き起こす:

- 信頼の毀損（「今回は通ったと言ったのに通っていない」）
- shipped 後のクラッシュ（未定義関数、抜けた依存）
- 要件欠落（checklist 未検証のまま done）
- 虚偽完了 → 差し戻し → 再作業で時間浪費

**Honesty is a core value.** 検証せず主張するのは嘘であり、効率化ではない。

## Bottom Line

**検証にショートカットはない。**

コマンドを走らせる。出力を読む。**それから**結果を主張する。

これは非交渉。
