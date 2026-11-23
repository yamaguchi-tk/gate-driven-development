---
name: pr-review-followup
version: 0.1.0
description: "PR 作成後、レビュー指摘・CI 失敗・Copilot / LLM reviewer の finding に対応して push・再レビュー依頼するまでの follow-up ループ。GDD (gate-driven-development) の有無に依存しない汎用手順。"
---

# PR Review Follow-up (Generic)

GDD (`/gdd-dev`) 配下のタスクではこの skill を直接の workflow owner にしない。
`gdd-pr-review-followup` が本 skill の手順を内包し、`state.md` / `tasklist.md` /
steering / Auto-Arm / ADR distillation などの GDD 固有の記録・自走契約を追加する。
本 skill は GDD の有無に関わらず成立する部分（collect → classify → verify →
fix → 独立レビュー → push → re-request のループ骨格と、修正時規律・証跡の書き方）
だけを正本として持つ。

## Goal

Iron law: **no actionable review findings before merge**。PR 作成後に出た review
comments / requested changes / failed checks / Copilot・LLM reviewer の finding
を、review findings -> fix -> push -> re-request review の順で処理し、指摘が
なくなるまでループする。

Evidence before claims: 「actionable finding 0 件」と言う前に、PR reviews /
review threads / comments / required checks を fresh に再取得する。

## When To Use

使う:
- PR 作成後に `changes_requested` / review comments / CI failure が来た
- 「レビュー指摘に対応して」「push して再レビュー依頼して」と言われた
- Copilot / LLM reviewer / CI から actionable finding が出た

使わない:
- PR 作成前の diff review（別の完了前レビュー手順に従う）
- GDD 配下のタスク（`gdd-pr-review-followup` を使う。本 skill はその内部手順）
- PR が merge 済みの追加実装

## Loop

1. **Collect**: `gh pr view <PR> --comments --json reviews,reviewThreads,comments,latestReviews,headRefOid,mergeStateStatus,mergeable`、`gh pr checks <PR>` を取得する。thread-level の未解決状態は GraphQL `reviewThreads(first: 100) { nodes { isResolved isOutdated comments(first: 100) { nodes { path line outdated } } } }` で取る（flat comments だけで完了判定しない）。`mergeable == "CONFLICTING"` は他の finding より先に対応する最優先 finding。`gh` が使えない場合はユーザーが貼った review comments / CI log を入力として扱う。
2. **Classify**: 各 finding を source（human / GitHub PR comment / Copilot / LLM reviewer / CI / security / unknown）と severity（High / Medium / Low / advisory / no_action）に分ける。`references/reviewer-common.md` § 常時 High の 4 型に当たり、同節の適用範囲に当たる指摘は、source と reviewer が付けた severity によらず High に分ける。適用範囲外の部品の 4 型は、同節のとおり Medium を上限にする（上限を掛けない finding と、付けてよい category も同節に従う）。適用範囲内の部品（どの部品かの決め方と、判定できないときに適用範囲内とすることは同節に従う）の指摘で、4 型に当たるかを判定できないものも High に分ける。この規定は advisory に分けるより優先し、適用範囲外と判定できた部品の指摘には掛けない。手順 3 の Verify で、4 型に当たらない、または適用範囲外の部品だと確かめたら（手順 3 の out-of-scope とは別）、この規定を掛けずに分けた severity（reviewer が付けていれば、その値を High / Medium / Low / advisory に読み替えた値。読み替えられなければ main が分けた値。上限は同節）に戻し、確かめた根拠を PR コメントに残す。指摘そのものが誤りなら invalid にする。advisory は「やる」か「やらない根拠を残す」かを明示的に決める（根拠なしのサイレントスキップはしない）。
3. **Verify**: 各 finding を READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT の順で評価し、valid / invalid / out-of-scope を決める。妥当性を検証せず即実装しない。unclear な finding は実装前にすべて明確化する。
4. **Fix**: 有効な finding だけを以下の 3 段に固定して修正する（正本: `references/self-review-lanes.md` § 修正時規律）。各段の証跡記録は必須。
   1. **①直す**: 指摘箇所を修正し、fresh test / lint / build 等の検証を伴わせる。直す順序は `references/self-review-lanes.md` § 直し方 に従う。guard に deny の分岐（拒否する条件・上限・受理する集合の縮小）を足す修正は、先に `references/self-review-lanes.md` § 修正時規律 の規律 C で、新しく deny になる入力を本番で誰が何件出すかを測り、その記録はその周回の証跡に `Fixed findings` の id とは分けて書く。
   2. **②横展開検索（規律A）**: 同じロジック・パターンの欠陥が他にないか `grep` / `git grep`（コードは AST 走査も併用）で全域検索し、ヒットを一括修正する。走査対象の母集合（ファイル数・抽出条件）と件数を記録する。母集合を書かない「他に同型なし」宣言は受け付けない。
   3. **③再 review（規律B）**: 修正後に関連テストが pass するか、未消化の指摘・未解決スレッドが 0 件かを確認する。
   指摘 1 件を①だけで closed 扱いにしない。②の証跡（Ripple check）が無い closed 宣言は closed として扱わず、未対応の valid finding のまま次周回へ持ち越す。
5. **内部整合レーン 1 周**: diff 内部の数値・列挙・命名・型の自己整合性を確認し、新規 high / blocking がゼロであることを確認する（レーン定義の正本: `references/self-review-lanes.md`）。
6. **独立レビュー**: 実装文脈を渡さない独立レビューを 1 回実行する（起動の方法は契約 4。Claude Code では agent 定義 `gdd-independent-reviewer` で起動し、effort を固定する。契約の正本: `references/independent-review.md` — 実装文脈を渡さない / read-only / diff-only / push 1 回につき 1 回）。`high: 0` かつ `blocking: 0` を確認する。high が出たら是正して内部整合レーンを回し直し、独立レビューを再実行する（後で実装する guard・contract test の Decision への high は、取り直しを 1 回までとし、それでも high または blocking が残れば人に戻す。取り直しを使ったことは証跡に書き、読めなければ使用済みとする。基準は `references/independent-review.md` の (3-f)）。
7. **Push**: push 前に `git diff` / `git status --porcelain` で secrets（AWS アカウント ID、秘密鍵、`.env`、API key、access token、Secrets Manager / SSM 実値）が無いか確認する。force push 禁止（履歴改変が必要なら人間に戻す）。証跡（下記）を残してから push する。push 先は PR の head にする（`git push origin HEAD:<headRefName>`。headRefName は `gh pr view <PR> --json headRefName` で取る）。`git push origin HEAD` は手元の branch 名で push するので、worktree の branch 名と PR の head が違うと、PR を更新せずに別のリモートブランチを作る。
8. **Re-request**: `gh pr comment <PR> --body "<対応内容と再レビュー依頼>"` 等で再レビューを依頼する。本文にシェルのコマンド置換や動的な生ログを直接埋め込まない（先にファイル/変数で確定し、内容を確認してから投稿する）。
9. **Repeat**: `gh pr view` / `gh pr checks` を再取得し、no actionable finding かつ required checks が pass/neutral/skipped（理由付き）かつ本周回までの Fixed findings すべてに Ripple check が記録済みなら loop を終了する。未消化があれば 1 に戻る。

## Actionable Finding Definition

loop を続ける対象: `changes_requested` / High・Medium の valid finding / failed
required check（個別 check 単位。集約表示の green だけで見落とさない）/
`mergeStateStatus: CONFLICTING` / security finding / Fixed findings に載って
いるのに Ripple check が無い finding / reviewer が明示的に修正を要求している
comment。

loop を止めてよい対象: invalid・out-of-scope と検証済みで根拠を残した comment /
advisory・Low だけで merge 前 blocker でないと明示した finding / no_action /
reviewer から新規コメントがなく required checks が pass/neutral/skipped。

## 証跡の書き方

worklog（またはリポジトリの慣例に従い PR コメント）に、1 iteration ごとに以下を残す。

```markdown
PR Review Follow-up:
- PR URL: <url>
- Iteration: <N>
- Collected findings: <count>
- Valid actionable findings: <count>
- Fixed findings: <ids>
- Ripple check（規律A）: <finding id ごとに 検索コマンド + 走査母集合（ファイル数・抽出条件） + ヒット件数 + 修正した型 | not_applicable + 理由（Fixed findings が空の場合のみ）>
- Independent Review: <sha> | high: <uint> | blocking: <uint> | at: <ISO 8601>（書式の正本: references/independent-review.md）
- Decision Retake: used | not_used（(3-f) の取り直し。GDD の `state.md` § Gate Status に `Decision Retake` の行があるか、前の iteration の値が used なら used。初回の iteration で行も前の値も無ければ not_used。GDD の steering があるのに `state.md` を読めないときと、前の iteration の値を読めないときは used）
- Push: <commit sha or not_pushed reason>
- Re-review request: sent / manual_required / not_needed
- Next: repeat / no actionable review findings / blocked
```

## Escape Hatches

- 同じ finding が 3 回以上再発する: `blocked` とし、root cause が修正方針・
  テスト・reviewer expectation のどこにあるかを調べる。無限に push しない。
- **structural mismatch early-exit**: 検証ループ中に前提崩壊（想定と根本的に
  異なるハーネス構造・存在しない前提条件）を検知した場合、回数閾値を待たず
  attempt 1 時点で中断し、再計画に戻す。
- scope / AC / policy / security boundary が変わる: 実装を進めず承認を得てから
  再開する。PR comment だけで承認済み範囲を silent に変更しない。
- required check が外部障害で失敗し続ける: `blocked` として解消手順と待ち条件
  を示す。
- secrets detected: commit / push を止め、ユーザーに即報告する。
- merge / deploy はこの skill の範囲外。実行しない。

## Guardrails

- valid finding を検証せず即修正しない。
- force push 禁止。履歴改変が必要な場合は人間に戻す。
- merge / deploy は実行しない。
- no actionable review findings と言う前に fresh に PR reviews / comments /
  checks を再取得する。
- review pending を clean と呼ばない。
- flat comments only で unresolved thread の有無を判断しない。
- 同一 finding の 3 回以上の繰り返しは `blocked`。無限に再 push しない。
- push する前に `git diff` / `git status --porcelain` で今回の finding と無関係
  な変更が混入していないかを確認する。混入していたら push せず確認する。
