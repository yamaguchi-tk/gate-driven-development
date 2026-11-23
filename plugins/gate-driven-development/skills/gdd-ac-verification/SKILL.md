---
name: gdd-ac-verification
version: 0.2.0
description: "Use when verifying GDD acceptance criteria against fresh evidence, especially from completion or implementation gates."
---

# AC Verification

`tasklist.md` の `Verification` field を埋めて各 AC に合否判定を付ける discipline skill。**「証跡がない pass は禁止」** を Iron Law として、speculative claim をはじき、fresh evidence のみを受け入れる。

責務境界:

- 本 skill が触ってよいもの: `tasklist.md` の `Verification` 行、または呼び出し元に返す Verification judgment
- 本 skill が触らないもの: `state.md`、`Next Action`、`Resume From`、PR / branch / worktree の状態
- state 更新は呼び出し元（`gdd-completion-check` / `gdd-implementation-gating` / active workflow owner）が行う

`gdd-completion-check` の AC 検証部分から抽出された skill。完了 gate 以外（impl-gating Express path safety net や、ad-hoc な「AC-3 だけ verify したい」場面）からも単独で呼べる。

## Fixed Model

- `Claude Code`: `sonnet` + `effort=medium`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light_task tier）
- AC 適合の判定は取りこぼしが損失に直結するため mini は使わない

## Iron Law

> **NO COMPLETION WITHOUT FRESH EVIDENCE.**

「動いたはず」「前のセッションで通った」「CI が green だから」は全て evidence ではない。本セッションで再実行して得た exit code / output / log のいずれかが evidence。違反した瞬間にこの skill を使う意味がない。

## When to Use

- `gdd-completion-check` から全 AC verify を委譲されたとき
- `gdd-implementation-gating` Express path の safety net で AC 検証を回すとき
- 「AC-N だけ再 verify して」というユーザーの局所指示
- E2E hotfix / 追加修正後の AC 再判定
- 外部 security evidence の schema 検証

使わない場面:

- **AC Drift Check** — 実装 → artifact の逆方向整合（記載のない挙動の検出）は `gdd-completion-check` の Step 5a で扱う。本 skill は AC → 実装 の正方向検証に専念する
- AC の文面そのものの妥当性判定 — `gdd-requirements-gating` の責務
- reviewer による主観判断 — `gdd-implementation-gating` の inline checklist 系

## Verification Schema

`tasklist.md` の `Verification` 配下の各行は以下 4 field を必須にする:

- **`method`** — 何で検証するか（コマンド / 確認手順 / evidence kind）
- **`status`** — 判定結果
- **`evidence`** — 検証の証跡（コマンド出力 / log / artifact 参照）
- **`notes`** — 補足、未確認事項、後続作業の記録

### Verification 節の受理文法

正本は下記 BNF ブロック（`references/self-contained-contract.md` と同一テキスト）。行の種類・method 形式・status 許容値はすべてこのブロックが定める。

<!-- verification-grammar:begin -->
```
verification_section := heading NEWLINE section_line*
heading              := "## Verification"      ; exact match。rstrip 後の全行一致で
                                               ; 判定し、接頭一致は取らない。したがって
                                               ; `## Verification Notes` /
                                               ; `## Verification History` /
                                               ; `## Verification の例:` はいずれも
                                               ; 別の節であり、この節に飲み込まない
section_line         := blank | empty_marker | header | separator | data_row
blank                := ""                     ; rstrip 後に空
empty_marker         := "- なし"
header               := "|" h_method "|" h_status "|" h_evidence "|" h_notes "|"
separator            := "|" sep_cell "|" sep_cell "|" sep_cell "|" sep_cell "|"
data_row             := ac_row | evidence_row | refactor_row

ac_row       := "|" ws* "method=ac:" AC_ID ws*            "|" ac_status "|" cell "|" cell "|"
evidence_row := "|" ws* "method=security_evidence:" KIND ws* "|" ev_status "|" cell "|" cell "|"
refactor_row := "|" ws* "method=refactor-checkpoint" ws*  "|" ac_status "|" cell "|" cell "|"

h_method   := ws* "method" ws*      ; ASCII 小文字化して比較
h_status   := ws* "status" ws*
h_evidence := ws* "evidence" ws*
h_notes    := ws* "notes" ws*
sep_cell   := ws* ":"? "-"+ ":"? ws*
ac_status  := ws* ("pending" | "pass" | "fail") ws*                            ; ASCII 小文字化後に完全一致
ev_status  := ws* ("pending" | "pass" | "fail" | "n/a" | "unsupported") ws*    ; 同上
cell       := 任意（区切りの `|` は `\|` でエスケープする）

AC_ID  := "AC-" [A-Za-z]? DIGIT+ ("-" (DIGIT+ | [a-z]))? [a-z]?
KIND   := [a-z] [a-z0-9-]*

ws     := " " | TAB                 ; ASCII 半角空白 (U+0020) と水平タブ (U+0009) の 2 種だけ。
                                    ; 全角空白 (U+3000) / NBSP (U+00A0) / U+2028 等の
                                    ; Unicode 空白は ws ではなく、除去もしない。セルの
                                    ; padding に使った行は schema 違反になる
DIGIT  := [0-9]                     ; ASCII 数字だけ。全角数字 (`AC-１`) は DIGIT ではない
```

`## Verification` 節に置けるのは上記が定める行だけ。列挙外の行はすべて schema 違反として block される（`## Verification Notes` へ移す。検証行〔`method=` で始まる行 / AC ID・`security_evidence`・`refactor-checkpoint` を名指す行 / status トークンを含む行〕は `## Verification` 以外のどの節へも移してはならない。ただし `ac-ledger.md` / `## Verification History` が各々の規定に従って持つ正規の記録は対象外）。節に一部でも重なる fenced code block も schema 違反。

**節見出しは exact match**。行を rstrip した結果が `## Verification` と**完全一致**する行だけがこの節の開始であり、接頭一致では判定しない。`## Verification Notes` / `## Verification History` / `## Verification の例:` はいずれも別の節として扱い、この文法の適用対象外とする。fenced code block の中にある `## Verification` 見出し行も同じ exact match で判定する（接頭一致で拾うと、記入例 fence が `## Verification Notes` を 1 行含むだけで回復手順の無い恒久 block になる）。
<!-- verification-grammar:end -->

**AC 検証行（`method=ac:`）は 1 件以上必要**。上記文法は data 行 0 件の節も行の形としては受理するが、done guard は `method=ac:` 行が 1 件も無い節を「検証行がありません」で block する。`security_evidence` 行・`refactor-checkpoint` 行は AC の検証行の代わりにならない。AC 検証行 1 件以上は形の下限であり、AC カバレッジを保証しない。tasklist の改行は LF / CR / CRLF だけとし、`str.splitlines()` が行を分ける他の文字（`\x0b` `\x0c` `\x1c`〜`\x1e` `\x85` U+2028 U+2029）を含む tasklist は、行・節の境界が崩れて検証行を正しく数えられないため done guard が block する（該当文字を削除する）。

### 行の種類と method 値

| 行種別 | method の形式 | 例 |
|---|---|---|
| AC 検証行 | `method=ac:<AC_ID>` | `method=ac:AC-1` / `method=ac:AC-3a` |
| 外部 security evidence | `method=security_evidence:<KIND>` | `method=security_evidence:csp` / `method=security_evidence:dependency-scan` |
| Mandatory refactor checkpoint | `method=refactor-checkpoint` | `method=refactor-checkpoint` |

正本は上記文法ブロック。`method` が空 / `TBD` / `unknown` は schema 違反として扱う（後述の fail-closed table 参照）。

### status の許容値

| status | 意味 | 使える行 |
|---|---|---|
| `pending` | まだ verify していない | AC 検証行 / security evidence / refactor-checkpoint |
| `pass` | 検証して通った（evidence 必須） | AC 検証行 / security evidence / refactor-checkpoint |
| `fail` | 検証して落ちた | AC 検証行 / security evidence / refactor-checkpoint |
| `N/A` | この evidence kind は今回の変更に非該当 | **security evidence のみ**（AC 行で使うと schema 違反） |
| `unsupported` | この evidence kind は必要だが current verifier contract では対象外 | **security evidence のみ**（AC 行で使うと schema 違反） |

### AC 行の追加ルール

- AC 検証行で使える status は `pending` / `pass` / `fail` の 3 種類のみ
- `pass` のときは `evidence` が空であってはいけない（空 = fail-closed）
- `N/A` や `unsupported` を AC 行で使うのは「AC が測定不能」を意味するため、AC 定義の見直しが必要 → `human_recheck_required` に昇格

### 外部 security evidence の追加ルール

- `pending` / `pass` / `fail` / `N/A` / `unsupported` の 5 種類を使える
- `status=pass` のときは scan / verifier run を追跡できる evidence を残す
- `status=fail` のときは未解決 issue、実行失敗、または verification 不足を `evidence` / `notes` に残す
- `N/A` はその evidence kind 自体が今回の変更に非該当のときだけ
- `unsupported` はその evidence kind が必要だが current verifier では対象外と具体的に示せるときだけ

### Mandatory refactor checkpoint の追加ルール

- `status=pass` と `evidence` が必須
- `evidence` には「どのファイルをどう簡略化したか」「なぜ安全な改善がなかったか」を残す
- `status=fail` の場合は `gdd-subagent-driven-implementation` に戻す

## Schema Validation（fail-closed 条件）

以下の schema 違反は **fail-closed** とし、呼び出し元（completion-check 等）に schema 違反として返す。自走継続させない。

| 違反 | 例 | Fail-closed 動作 |
|---|---|---|
| AC 行で `status=unsupported` / `N/A` | `method=ac:AC-3, status=unsupported` | schema 違反として reject。reviewer に「AC は測定可能でなければならない」旨の指摘を返し、AC 定義見直し（`human_recheck_required`）に倒す |
| `method` が空 / `TBD` / `unknown` | `method=ac:AC-4, method=TBD` | method 未確定は方向性判断のため **`human_recheck_required` に短絡**。method 決定は systematic-debugging の対象ではない |
| `status=pass` で `evidence` 空 | `method=ac:AC-1, status=pass, evidence=""` | evidence 不足として reject。primary owner task を再オープンし `gdd-systematic-debugging` 送り |
| `evidence` に推量表現（"should work" / "probably" / "seems to" / "looks like"） | `evidence="should work after fix"` | speculative claim として reject。実コマンド出力 / exit code / log の参照に置き換えるよう要求 |
| security evidence の `status=pass` で prod 未検証 | `method=security_evidence:csp, status=pass, notes="stg のみ"` | prod 未検証なら `status=unsupported` が正しい。`notes` に prod pending 必須明記を求めて再試行 |
| `method=ac:<id>` だが `id` が `requirements.md` に存在しない | `method=ac:AC-99` で AC-99 が無い | AC ID 不整合として reject。tasklist と requirements の同期を要求 |

**Why**: schema 違反（`unsupported` in AC rows / `TBD` method / 空 evidence / speculative wording）を事前に reject しないと、completion-check が broadly に loop して blind pass / false blocker の両方が起きる。schema 穴は fail-closed 信頼性に直結するため、通常の外部前提不足ループに合流させない。

### 自動 AC ID lint

`method=ac:<id>` の AC ID 整合性は **`scripts/lint-ac.py`** が機械的に検査する。verify 開始前または Schema Validation 実施時に実行する:

```sh
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-ac.py --steering-dir .steering/<task>/
```

- **exit=1**（ERROR）: tasklist が存在しない AC ID を参照、または requirements.md で AC ID が重複定義 → schema 違反として reject。`requirements.md` / `tasklist.md` を同期してから verify を再実行
- **exit=0 + WARN**: requirements にあるが tasklist で verify されない AC ID あり → tasklist.md に `method=ac:<id>` 行を追加するか、AC を削除する。strict 運用なら `--strict` で ERROR 扱い
- **exit=0 + OK**: AC 定義と参照が完全一致

**Why**: AC ID typo（`AC-3` と `AC-3a` の混同）や、AC 削除後の tasklist 残存参照は manual review では見落としやすい。lint で planning / build / completion の各 phase で機械的に潰す。

## Fresh Verification Rule

**毎セッションで evidence を再生成する**。以下は evidence として認めない:

- 前セッションで pass した記録
- CI の green status
- 「test を回した」の推量表現
- evidence field に書かれた「動作確認済み」だけ

毎セッションで以下のどれかを実行し、結果を `evidence` に記録する:

- `npm test` / `pytest` / `go test` 等のテストコマンド実行 → exit code 0 と pass 数
- E2E スクリプト実行 → 出力 / 副作用の観測
- `aws s3 ls <bucket>` / `aws iam get-role` 等の状態確認 → 期待値との一致
- script の手動実行 → stdout / stderr / 戻り値

**Why**: コードは前セッション後にも変わり得る（小さな lint fix、別の concurrent task の merge、依存の Renovate 等）。前回 pass は現在 pass を保証しない。

## Speculative Language の拒絶

`evidence` に以下のフレーズが含まれる場合は schema 違反として reject:

- "should work"
- "probably"
- "seems to"
- "looks like"
- "おそらく"
- "たぶん"
- "動くはず"
- "通っているはず"
- "動作確認済み"（具体的なコマンド・出力なし）

代わりに以下のいずれかの形式を要求:

- `exit code 0 で pass した` + コマンド名
- `<command>` 出力 / log 抜粋
- artifact path（screenshot / log file）
- 観測した副作用（DB row / S3 object / API response 等）

**Why**: 推量表現は「verification をやったつもり」を許す。Iron Law（NO COMPLETION WITHOUT FRESH EVIDENCE）は具体的観測でしか満たせない。

## Steps（呼び出し元から渡される入力に応じた処理）

1. **呼び出し元コンテキストを確認**: 全 AC verify（completion-check 経由）か、特定 AC のみ verify（impl-gating Express / manual）か
2. **必要な行を読む**:
   - 全 AC verify: `requirements.md` の全 AC を列挙し、`tasklist.md` の `Verification` 行と照合
   - 特定 AC verify: 該当 AC ID を `tasklist.md` の `Verification` から探す
   - 不足行があれば `pending` として行を追加（status の初期値）
3. **各行を 4 field で確認 / 埋める**:
   - `method` が空 / TBD なら fail-closed
   - `status=pass` を付ける前に Fresh Verification Rule に従ってコマンド再実行（テストの結果だけは、同じ起動の中の結果を条件付きで使ってよい。`references/verification-before-completion.md` § Fresh の粒度）
   - `evidence` の speculative 表現を拒絶
4. **Schema Validation を実行**: 上記の table に 1 件でも該当すれば schema 違反としてマークする（行は判定結果 table にも残す。表記規約を参照）
5. **行ごとの完了条件を判定**:
   - **AC 行**: `pass` で完了（`pending` / `fail` / schema 違反 pending は未完了）
   - **security_evidence 行**: `pass` / `N/A` / `unsupported` のいずれかで完了（`fail` / `pending` は未完了）
   - **refactor-checkpoint 行**: `pass` で完了（`fail` は未完了）

   5b. **全体判定を導く**: 全行が完了条件を満たし、かつ schema 違反 0 件なら **completion 可能**。1 件でも未完了 / 違反があれば **completion 不可**

   5c. **Output Template を埋める**: Schema Validation section / 判定結果 table / サマリ（全体判定行を含む）/ handoff section の順で構成
6. **呼び出し元に結果を返す**:
   - completion 可能 → 呼び出し元が `done` に進められる
   - `fail` 残存（schema 違反なし）→ 呼び出し元が differ ルートを判定（implementation_fix_only 等）
   - schema 違反残存 → 呼び出し元が fail-closed で停止

この skill は **judgment（合否）と schema validation を返す**だけで、`Next Action` / `Resume From` / `Route In Progress` などの state 更新は呼び出し元の責務。

## Output Template

呼び出し元に返す形式:

```markdown
## AC Verification Result

### Schema Validation
- 違反: 0 件 / 総検証行数 N 件   ← 分子=違反件数、分母=判定結果 table の総行数
- 違反内訳（あれば、1 件ごとに 1 行）:
  - <違反種別>: <該当行 method>: <fail-closed 動作>

### 判定結果

| Method | Status | Evidence | Notes |
| --- | --- | --- | --- |
| method=ac:AC-1 | pass | `npm test` exit 0, 42 passed | — |
| method=ac:AC-2 | fail | `npm test` exit 1, AC-2.spec.ts:23 failed | implementation 修正必要 |
| method=ac:AC-3 | pending | — | 未検証 |
| method=ac:AC-4 | pending | (rejected: "should work after fix") | Speculative Language として reject。具体的観測（exit code / 出力 / log / artifact path）に置き換えて再 verify 要 |
| method=ac:AC-5 | pending | (rejected: evidence empty) | `status=pass` 主張に対し evidence 空。primary owner task 再オープン |
| method=security_evidence:dependency-scan | pass | `npm audit` 0 vulnerabilities | — |
| method=security_evidence:csp | unsupported | stg で nuclei scan 0 findings | prod 未検証。`unsupported` に修正、`notes` に prod pending 必須 |
| method=refactor-checkpoint | pass | `src/foo.ts` を 80 行 → 50 行に簡略化 | — |

### サマリ
- pass: N 件
- fail: N 件
- pending: N 件（うち schema 違反で巻き戻し: M 件）   ← M 件は完了条件を満たさない pending
- schema violation: 0 件 / 総検証行数 N 件
- **全体判定**: completion 可能 / completion 不可（理由: <stop / fail 残存 / pending 残存>）

### 呼び出し元への handoff
- **優先順位**: ① stop 指示（schema 違反 1 件でも残存なら fail-closed で停止）→ ② 各違反の対処（再オープン先 / human_recheck_required）→ ③ fail 残存への next action 候補（implementation_fix_only 等）→ ④ pending 残存の再 verify 指示 → ⑤ state 更新は呼び出し元責務であることの再確認
- 必要な情報を簡潔に。違反 / fail / pending ごとに 1 行 OK。長さ制限なし
- 単一 AC が pass でも、関連する security_evidence や refactor-checkpoint に違反 / fail があれば **全体判定は completion 不可**。両者を併記する
```

### 表記規約（異常行の扱い）

- **pending 行で evidence 未取得**: Evidence セルは `—`（em dash）に統一
- **schema 違反行**（evidence 空 / Speculative Language / 許容外 status / method=TBD 等）:
  - Status は **`pending` に巻き戻す**（呼び出し元が再 verify 対象として扱えるように）。第 6 status 値は作らない（5 値の許容を維持）
  - Evidence セルに `(rejected: <違反理由 1 行>)` を入れる。元の不正 evidence 文字列を残したい場合は `(rejected: "<元値>")` で wrap
  - Notes セルに違反種別と次に呼び出し元が取るべき action（再オープン先 / human_recheck_required 等）を 1-2 行
  - **同じ行を Schema Validation section と判定結果 table の両方に出す**（前者は集計・後者は呼び出し元の re-verify 一覧）
- **security_evidence で prod 未検証**: Status を `unsupported` に修正し、Notes に prod pending 必須明記を要求
- **多重違反**（例: `method=TBD` + `status` も許容値外）: より上流の違反（method）を主違反として 1 件カウントし、副次違反は Notes で言及。Schema Validation の集計は **行単位**（method ごと）で 1 件として数える

## Rationalization Check（この skill 固有）

AC verification を雑に終わらせたくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「CI が green だから本セッションでの再実行は不要」 | CI green ≠ 現在の AC pass。Fresh Verification Rule で毎セッション再実行が必須 | [Tooling Faith] CI の coverage を 100% と錯覚し、AC との対応関係を独自に検証しない |
| 「前セッションで pass したから skip」 | コードは前セッション後にも変わる（lint fix / concurrent merge / Renovate 等）。前回 pass は現在 pass を保証しない | [Recency Bias] 直近の pass を「現在も pass」と一般化する |
| 「evidence に "動作確認済み" と書けば十分」 | 具体的観測（exit code / 出力 / 副作用）がない記述は evidence ではない。Speculative Language として reject | [Confirmation Bias] 確認した感覚だけで evidence を満たそうとする |
| 「AC は概ね pass、細部は notes で済ます」 | partial pass は pass ではない。全条件が満たされるまで `status=pass` を付けない | [Premature Closure] 早く done にしたい欲求が、AC 完備性を読み替える |
| 「`method=TBD` でひとまず行を作る」 | `method` 未確定は方向性判断のため `human_recheck_required` に短絡する schema 違反 | [Bias for Action] 進捗の見えなさを嫌い、判断未確定のまま行を埋める |
| 「AC-3 だけ measurable じゃないから `unsupported`」 | AC 行で `unsupported` は schema 違反。AC が測定不能なら AC 定義の見直し（`human_recheck_required`） | [Locus of Control Drift] AC 定義の責任を verification 側に滑り込ませる |
| 「security evidence は `N/A` で逃せる」 | `N/A` はその evidence kind が今回の変更に非該当のときだけ。意図的な逃避は schema 違反 | [Authority Substitution] schema を「方便」に使い、実証責任を回避する |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（fail-closed 応答）。以下はこの skill 固有のルール。

- **state を変更しない**: `Next Action` / `Resume From` / `Route In Progress` / `Gate Status` の更新は呼び出し元の責務。本 skill は judgment と schema validation を返すだけ
- **AC Drift Check に立ち入らない**: 実装 → artifact の逆方向整合は `gdd-completion-check` Step 5a の責務。本 skill は AC → 実装 の正方向のみ
- **reviewer 判断に立ち入らない**: scope guard / dead code / 設計整合は `gdd-implementation-gating` の reviewer の責務
- **Fresh Verification Rule を skip しない**: 「忙しい」「明らかに前と同じ」は理由として認めない（例外は、`references/verification-before-completion.md` § Fresh の粒度の条件を満たす同じ起動の中のテストの結果だけ）
- **Speculative Language を許容しない**: "should work" / "probably" / "動作確認済み" 等は evidence として記録しない
- **Schema Validation を絶対に bypass しない**: schema 違反は 1 件でも呼び出し元に通知する
- **Context Compaction Resilience**: 全 AC verify 時は `requirements.md` の AC 一覧をディスクから re-read してから verify する。tasklist の `Verification` だけを信用しない

## 他 skill との関係

- **`gdd-completion-check`** — 全 AC verify の主な呼び出し元。本 skill から judgment を受け取り、state 更新と AC Drift Check / 他の品質チェックを実行する
- **`gdd-implementation-gating`** — Express path safety net で本 skill を呼んで AC 検証を行う
- **`gdd-pr-review`** — Spec Drift Check で AC ↔ 実装の整合を見るときに参照
- **`gdd-systematic-debugging`** — `status=fail` を返した場合、呼び出し元が routing decision tree で differ ルートを判定する
- **`references/rationalization-root-causes.md`** — Why 列の認知バイアスラベルの正本
- **`references/skill-responsibility-matrix.md`** § Pair 4 — `gdd-completion-check` との境界

## Quick Reference

| 状況 | アクション |
|---|---|
| 全 AC verify（completion-check 経由） | `requirements.md` の全 AC を `Verification` 行と照合 → 各行 4 field 埋め → Schema Validation → 結果 return |
| 特定 AC verify（impl-gating / manual） | 該当 AC ID の行だけ 4 field 埋め → Schema Validation → 結果 return |
| schema 違反検出 | fail-closed として呼び出し元に通知（自走しない） |
| `status=fail` が残る | 呼び出し元が differ ルート判定（本 skill は judgment のみ） |
| Speculative Language 検出 | reject して具体的観測の入力を要求 |
