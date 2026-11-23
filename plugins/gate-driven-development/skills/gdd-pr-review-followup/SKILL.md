---
name: gdd-pr-review-followup
version: 0.2.0
description: "Use after a GDD PR exists and review comments, requested changes, failed PR checks, or post-PR fix instructions need follow-up."
---

# GDD PR Review Follow-up

## Fixed Model

- `Claude Code`: `sonnet` + `effort=medium`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light_task tier）
- review findings の取りこぼしを防ぐため mini は使わない

## Goal

PR 作成後に、GitHub PR 上の review comments / requested changes / failed checks / LLM review findings を **review findings -> fix -> push -> re-request review** の順で処理し、レビュー指摘がなくなるまでループさせる。これは review findings -> fix -> push -> re-request review loop である。

この skill は PR 作成後の follow-up lane を担当する。PR 作成前の最終 diff review は `gdd-pr-review`、個別 finding の検証規律は `gdd-receiving-code-review`、修正後の formal gate は `gdd-implementation-gating` が担当する。collect → classify → verify → fix → 独立レビュー → push → re-request の骨格と修正時規律（規律A/B/C と § 直し方）・証跡の書き方は GDD 非依存の `pr-review-followup` skill を正本とし、本 skill はそこに `state.md` / `tasklist.md` / steering / Auto-Arm / ADR distillation 等の GDD 固有の記録・自走契約を上乗せする。

## When To Use

使う:

- PR 作成後に reviewer から `changes_requested` / review comments が来た
- ユーザーが「レビュー指摘がなくなるまで」「push して再レビュー依頼して」と言った
- PR 作成後にユーザーが「PR後に修正指示」「この指摘を直して」「review comment に対応して」「CI 失敗を直して」と言った
- PR 作成後に Copilot / LLM reviewer / CI から actionable finding が出た（Claude Code desktop の Auto-fix が届けた `<ci-monitor-event>` の CI の失敗を含む。人間キックなしで直す。正本は `references/post-completion-pr-flow.md` Option 1 手順 6 の CI 失敗の自動修正）
- 同じ PR / branch 上で修正して再度レビュー指示したい

PR 後 follow-up では `superpowers:receiving-code-review` / `superpowers:test-driven-development` を workflow owner にしない。個別 finding の読み方や TDD 規律を参考にする場合も、collector / loop owner は本 skill のままにし、修正は `gdd-receiving-code-review` → `gdd-systematic-debugging` → `gdd-test-driven-development` / `gdd-subagent-driven-implementation` → `gdd-implementation-gating` に戻す。

使わない:

- PR 作成前の diff review → `gdd-pr-review`
- 実装直後の formal gate → `gdd-implementation-gating`
- companion review の単発受領 → `gdd-receiving-code-review`
- PR が merge 済みの追加実装 → `gdd-using-git-worktrees` の Post-Merge Follow-up Worktree Policy

## Design Review Checkpoint

指摘 1 件ずつのパッチを積んでも収束しないときに、パッチを止めて設計レベルで見直す。毎巡、Step 3 の対応プロトコル (c) の後・Step 4 Route の前に判定する。閾値は `hooks/scripts/lib/constants.py` の定数が唯一正本で、本節には定数名だけを書く。

| trigger | 発火条件 | 0 件 → 非発火 | 判定不能 → 強制発火 |
|---|---|---|---|
| (a) 巡数 | `PR Review Rounds` ≥ `PR_CHECKPOINT_ROUNDS_THRESHOLD` | `PR Review Rounds` が 0 | `PR URL` があるのに `PR Review Rounds` が読めない（上限到達と同じ 2 択） |
| (b) 自傷率 | 直近 2 巡の妥当 finding（`file:line` あり）のうち `fix_origin: self-inflicted` の割合 > `PR_CHECKPOINT_SELF_INFLICTED_RATIO` | 分母 0 | `last_head` が解決できない / `git diff` 失敗 / 初巡より後で `last_head` と当巡の head が同じ / `Valid actionable findings` と `Findings:` 行の件数不一致 / 独立レビュー由来の finding に `file:line` なし |
| (c) クラスタ再発 | `PR Review Cause Cluster Log` の `bounce_count`（そのカテゴリが出た巡の数）の最大値 ≥ `PR_CHECKPOINT_CLUSTER_REPEAT_ROUNDS` | log 行が無く `Findings:` 行にも `cause:` が無い | `Findings:` に `cause:` があるのに log 行が無い / `cause:` が空 / parse 不能 |
| (d) commit 比率 | `git rev-list --count --first-parent --no-merges <first_head>..HEAD` ÷ 同 `origin/<base>..HEAD` > `PR_CHECKPOINT_REVIEW_COMMIT_RATIO` | 分母 0 | `first_head` または `origin/<base>` が解決できない |

- 発火したら、下の (1)〜(3) を選ぶ前に、`references/requirements-gating-steps.md` § レビューループの契約 1 の前提の点検をして `worklog.md` に `前提の点検:` 行を書く。記録の欠落を「分母 0」に読み替えない。判定不能は発火しない側ではなく**強制発火**に倒す。
- ほかの強制発火: 上限到達（`PR Review Rounds` ≥ `PR_REVIEW_ROUNDS_MAX`。`blocked` にせず、選べるのは (1)(2) の 2 択で、(3) パッチ継続は選べない）/ 範囲外 blocker（比較 diff の外で見つかった high・実害クラス）/ 前回 (3) の期限切れ / (3-f) 取り直し後の残り（`state.md` § Gate Status に `Decision Retake` の行があり、その後の独立レビューにも high または blocking が残った。下の自律選択のとおり (1)〜(3) を選ばず人に戻し、`<選択>` は `人に戻す` と書く）。
- **差分スコープ**: 初巡より後の対応範囲は、比較 diff（`last_head..<当巡でレビューした head>`）の変更行と、reviewer が `origin: this-diff` を付けた finding。比較 diff の外で新たに見つかった `pre-existing` の finding は、medium 以下かつ実害クラスでないなら Step 3 (a) で「範囲外」（PR コメントに根拠を残しコードは変えない）、high・実害クラスならその巡では直さず `Independent Review` の high / blocking に数えたまま `範囲外 blocker` で強制発火する。例外として前巡未解消 blocker は diff 外でも blocking 維持（独立レビューが再報告しなければ main session が件数に足す）。`last_head` が解決できないときは差分を信頼せず全量を対象にする。

| 選択 | 選べる条件 | 実行内容 |
|---|---|---|
| (1) 設計し直し | 常に可 | `design_detail_only` で `gdd-systematic-debugging` → design.md / adr.md → `gdd-design-gating`（差分スコープ）→ 責務単位でテスト再構成 → `gdd-implementation-gating`。同一 finding カウントは 0 に戻す。同一 PR で 2 回目の (1) は実行せず、方式転換（task 撤回 / 再設計 / 依頼の範囲を変えるかを人に問う）を人間へ提示する（数える元は state.md の `checkpoint:` 行の `→ 設計し直し`。方式転換で止める遷移を書く main が、同じ手順で `references/human-check-template.md` § 事前回答 3 の `上限到達:` 行を語 `followup-redesign-2nd` で書く。形と、表示し直しでは書かないことは同節が正本） |
| (2) スコープ縮小 | 現 head の `Independent Review`（`references/independent-review.md` § 証跡 のとおり引き継いだものを含む）が high 0 かつ blocking 0（範囲外 blocker・前巡未解消 blocker を含めた値）、かつ Step 11 の clean 条件のうち medium を follow-up に回す以外をすべて満たし（未解決の High・実害クラスなし、required checks が pass / neutral / skipped、CONFLICTING なし、`Ripple check` 充足、未解消の `changes_requested` なし）、かつ AC の未達なし | 残り medium を worklog の follow-up 行に残して merge gate へ（merge は人間の明示承認。自走のマージの条件を満たすときの例外は `references/post-merge-qa.md` 手順 2。`Medium Disposition` は `Independent Review` の medium 件数専用の merge gate 証跡 field のため、PR レビュー由来の medium はここに書かない）。AC を削る縮小は `human_recheck_required` |
| (3) パッチ継続 | 上限到達でも (a) の判定不能でもない発火で、原因が局所と判定できたとき | 次の 1 巡だけ有効（期限が切れたら再発火）。同一 finding カウントは継続 |

- **再評価**: 発火したらパッチを止め、AC / design の WHERE / PR 本文の主張と累積修正後の実装を、`references/independent-review.md` § 観点レーン (a)〜(h) + 意図適合（順方向一致）で design レベルに再評価してから選ぶ。主体は main session。計画中の `gdd-review` が着地したらこの観点 pointer を差し替える。
- **自律選択**: 選択は AI が行い、人間へは事後報告する。人間へ戻すのは AC / scope / policy / security boundary が変わるとき（`human_recheck_required`）と、2 回目の (1) と、`references/independent-review.md` の (3-f) の取り直しでも high・blocking が残ったときだけ（`Approved Direction` の `判断の委任` の欄が委任の値か、`worklog.md` に対象を含む `事前回答:` 行があれば、戻す前に `references/human-check-template.md` § 事前回答 2・3 で扱う）。impl-gate 側の方式転換は人間へ提示するが、PR 後側はユーザー方針に従い自律選択を既定にする（意図的な非対称）。
- **記録**: `state.md`（worklog 代替不可）に `- checkpoint: <trigger> → <選択> | round: <N> | at: <ISO 8601>`（`<trigger>` ∈ `(a)` / `(b)` / `(c)` / `(d)` / `上限到達` / `判定不能(<入力名>)` / `範囲外 blocker` / `(3) 期限切れ` / `(3-f) 取り直し後の残り`、複数は `+`）。`worklog.md` に `### Design Review Checkpoint（巡 <N>）` としてトリガーの値・乖離の結論・選択と根拠・`human_recheck_required` の要否を残す。(c) の log は `state.md` の `## PR Review Cause Cluster Log` に `- <PR 番号> + <root cause カテゴリ> | bounced_at: <ISO 8601> | bounce_count: <N>`（PR 単位で生存し reset しない。identifier-key の正本は `references/bounce-log-schema.md`）。

## PR Review Follow-up Loop

Iron law: **no actionable review findings before merge**。

Evidence before claims: **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE**。actionable finding 0件 と言う前に、fresh verification evidence として PR reviews / review threads / comments / required checks を再取得する。`no actionable review findings` は post-fix の fresh 証跡がある場合だけ使う。

1. **Collect**: `gh pr view <PR> --comments --json reviews,reviewThreads,comments,latestReviews,headRefName,headRefOid,baseRefName,mergeStateStatus,mergeable`、`gh pr status`、`gh pr checks <PR>` を使い、PR 作成後の review findings と check failure を収集する。thread-level 状態が必要な場合は GraphQL で `reviewThreads(first: 100) { nodes { isResolved isOutdated comments(first: 100) { nodes { path line outdated } } } }` を取得し、flat comments only では完了判定しない。`gh` が使えない場合は、ユーザーが貼った review comments / CI log を入力として扱う。
   - **Suppressed comments の展開（必須）**: `gh pr view <PR> --comments` の出力に `<summary>Suppressed comments (N)</summary>` が含まれる場合、"no new comments" という表示だけで新規指摘 0 件と判定しない。suppressed セクション内の各項目を個別 finding として展開し、通常の Classify 以降のステップに載せる（PR 旧#900: "no new comments" の裏に多くの suppressed comments が埋もれ、その中に実バグが含まれていた）。
   - **mergeStateStatus / mergeable の確認（必須・最優先チェック）**: `mergeable == "CONFLICTING"`（`mergeStateStatus` が `DIRTY` 等の非マージ可能値）を検知したら、他の review finding より先に対応する最優先 actionable finding として扱う。放置したまま review finding の修正だけを繰り返さない（PR 旧#900 / 旧#922: base への merge conflict が長時間検知されず、レビュー対応だけが空転していた）。対応は最新 `origin/<baseRefName>` を取り込んで conflict を解消し、解消できない場合は Escape Hatches の該当項目に従う。
   - **required checks は個別に確認する（集約表示だけで clean 判定しない）**: `gh pr checks <PR>` の要約行や `gh pr view --json mergeStateStatus` の集約値だけで「CI green」と判定しない。各 check を個別に走査し、1 件でも `FAILURE` / `ERROR` があれば actionable finding として扱う（PR 旧#823 実測: 「CI green」と自己申告した直後に `lambroll diff` の個別 check が失敗していたと指摘され気づいていなかった）。
   - **巡数**: 新しい head sha のレビュー結果を収集したら `PR Review Rounds` を +1 する（同一 sha の再レビュー・CI 再実行・polling wake では加算しない。先行の high / blocking を打ち消さない）。上限と閾値は § Design Review Checkpoint
2. **Classify**: 各 finding を `source`（human / GitHub PR comment / Copilot / LLM reviewer / CI / security / unknown）と severity（High / Medium / Low / advisory / no_action）に分ける。`mergeStateStatus: CONFLICTING` は `source=CI` 相当・`severity=High` として扱う。`references/reviewer-common.md` § 常時 High の 4 型に当たり、同節の適用範囲に当たる指摘は、source と reviewer が付けた severity によらず High に分ける。適用範囲外の部品の 4 型は、同節のとおり Medium を上限にする（上限を掛けない finding と、付けてよい category も同節に従う）。適用範囲内の部品（どの部品かの決め方と、判定できないときに適用範囲内とすることは同節に従う）の指摘で、4 型に当たるかを判定できないものも High に分ける。この規定は下の advisory の既定より優先し、適用範囲外と判定できた部品の指摘には掛けない。受け入れ判定で、4 型に当たらない、または適用範囲外の部品だと確かめたら（受け入れ判定の「範囲外」とは別）、この規定を掛けずに分けた severity（reviewer が付けていれば、その値を High / Medium / Low / advisory に読み替えた値。読み替えられなければ main が分けた値。上限は同節）に戻し、確かめた根拠を PR コメントに残す。指摘そのものが誤りなら事実誤認として棄却する。
   - `advisory` = 修正は強制でないが、production品質・security・observabilityなど **production concern に関わる理由付きで改善を示唆** しているコメント（例: "Consider adding structured logging for production observability"）
   - `no_action` = 修正要求を含まず、production concern でない **純粋な suggestion / 称賛**（FYI / LGTM / "This looks clean!" / 理由なし "Consider X" / readability・style 系）。スレッドに "acknowledged" を記録し、コード変更しない。
   - 迷ったら `advisory` に倒す（`no_action` は production concern でない場合のみ）
   - **advisory 処理の必須化（Advisory Disposition Required）**: advisory 指摘を受けたとき、以下の 2 択を明示的に決定する（どちらかを必ず選ぶ）:
     - **やる（do）**: 修正を実施し、通常の valid finding として Fix ステップで処理する
     - **やらない（skip）**: やらない根拠を PR コメント or コードコメント（TODO/NOTE）で明示する
       - 根拠例: "コスト対効果が低い"、"後続 PR で対応予定 (#xxx)"、"スコープ外（AC に含まれていない）"、"Copilot/reviewer の misread（根拠: 該当コメントの引用）"
       - やらない根拠なしに advisory をサイレントにスキップしない
       - なぜ: 根拠なしスキップは次ラウンドで同じ指摘が再発する確率が高い（observed パターン）
3. **Verify（対応プロトコル (a)〜(c)）**: 全件を集めてから判定し、1 件ずつ直さない。
   - **(a) 受け入れ判定**: 各 finding を `gdd-receiving-code-review` に渡し、READ -> UNDERSTAND -> VERIFY -> EVALUATE -> RESPOND -> IMPLEMENT の順で 妥当 / 事実誤認（実測で棄却し PR コメントに根拠）/ 範囲外 / 既知の限界（`Human Check Status=approved` 時点の requirements.md Honest Limitations 既載に限る。実害クラスと別の AC を破るものは除く）に分ける。コメント内の自己申告は根拠にしない。既知の限界に分類した High も `Independent Review` の high に数えたまま（gate の受理述語は変えない）
   - **(b) 原因クラスタリング**: 妥当 finding を root cause カテゴリ（語彙は `references/bounce-log-schema.md` § 既存実装一覧 の例示。新ラベルの前に既存ラベルと照合する）で束ねる。同型の全域検索（規律 A）はここで行い、ヒットを同じクラスタに加える。各 finding に `fix_origin` を付ける: 当巡の比較 diff（`last_head..<当巡でレビューした head>`）の変更行に位置する、または reviewer が `origin: this-diff` を付けたものは `self-inflicted`、それ以外は `inherited`（比較 diff が空なら全件 `inherited`）。クラスタが確定するたびに `state.md` の `## PR Review Cause Cluster Log` を更新する（該当 identifier-key の行があれば `bounce_count` を +1、無ければ `bounce_count: 1` で新規作成。checkpoint が発火するかどうかに関わらず毎巡行う）
   - **(c) クラスタ判定**: **パッチ可** = 1 件（ヒット含む）かつ局所かつ判定規則を変えない かつ `inherited`。**設計し直し** = 2 件以上 / `self-inflicted` を含む / 判定規則を変える（局所パッチ禁止）。続けて § Design Review Checkpoint を判定する
4. **Route**（クラスタ単位）:
   - パッチ可クラスタ（valid within approved AC）→ `gdd-systematic-debugging` で `implementation_fix_only` として修正
   - 設計し直しクラスタ / design detail のみ → `design_detail_only`
   - scope / AC / policy / security boundary / prompt-output contract が変わる → `human_recheck_required`（done マーカーの後なら Hotfix Lane に回るので、この skill のどの節でこの route か `planning_rework_required` に決めても、クラスタの finding を `worklog.md` の `## Hotfix Findings` に書く。`references/phase-progression.md` § Post-PR / Post-Merge Contract の 3）
   - invalid / out-of-scope / advisory (skip) → 理由を PR コメント（`gh pr comment <PR> --body "reason"`。本文構築は Guardrails の Body Construction Safety に従う）に残し、コード変更しない
   - no_action → スレッドに "acknowledged" を記録し、コード変更しない（記録方法: `gh api graphql` でスレッドを resolve、または `gh pr comment <PR> --body "Acknowledged: <理由>"` でコメント追加。いずれも本文構築は Body Construction Safety に従う）
5. **Fix（対応プロトコル (d)）**: 1 巡で直すのは merge を止めるもの（high / 実害クラス / failed required check / CONFLICTING）と、それと同じ原因クラスタの medium だけ。それ以外の medium は直さず worklog の follow-up 行に残す（`Medium Disposition` は `Independent Review` の medium 件数専用の merge gate 証跡 field のため書かない）。有効な finding のうち (d) の範囲だけを、以下の 3 段に固定して修正する（正本: `references/self-review-lanes.md` § 修正時規律。GDD 非依存の `pr-review-followup` skill も同じ 3 段を Fix ステップに持つが、②の一括修正/検出のみの違いは followup 例外として self-review-lanes.md に別記されている）。各段の証跡記録は required。
   1. **①直す**: 指摘箇所を修正する。直す順序は `references/self-review-lanes.md` § 直し方 に従う。修正には fresh test / lint / build / relevant verifier を伴わせる。TDD に戻すときは、上の Route のとおり `gdd-systematic-debugging` を通し（finding を task の `Fix Findings:` に書くため）、`gdd-test-driven-development` で RED evidence を追加する。guard に deny の分岐（拒否する条件・上限・受理する集合の縮小）を足す修正は、先に `references/self-review-lanes.md` § 修正時規律 の規律 C で、新しく deny になる入力を本番で誰が何件出すかを測る。証跡: 修正ファイル + 実行した検証コマンドと結果（規律 C の実測をしたら、その記録の項目も `Verification:` 行に）
   2. **②同型を全域 grep して検出・記録**（規律 A の followup 例外）: 同じロジック・パターン・バグの全域検索（`grep` / `git grep`）は Step 3 (b) で済ませてあり、ここではその結果を記録するだけで一括修正はしない（クラスタが設計し直しと判定されたら再設計側で直す）。証跡: 検索コマンドと走査母集合（ファイル数・抽出条件）、ヒット件数、ヒットを入れたクラスタ（全件リストは転記しない）
   3. **③再 review**: 修正後に関連テストが全て pass するかを確認し、未消化スレッドが残っていないか確認する（規律 B）。証跡: 実行したテストコマンドと結果、未消化件数 0 の確認
   指摘 1 件をインスタンス修正だけで closed にしてはならない。**②の証跡（`Ripple check`）が無い closed / fixed 宣言は closed として扱わない**。その finding は元の severity のまま未対応の valid finding として「loop を続ける対象」に残し、次周回に持ち越す（`advisory` / `no_action` に読み替えて loop を止めてよい対象に移すことは禁止）。波及チェックの証跡は `state.md` または `worklog.md` に `Ripple check` 行として残す（書式の正本は `## State / Worklog Contract`。どちらのファイルも無い場合は PR コメントに同じ書式で残す）。
6. **Post-PR Decision Persistence**: PR後の修正で Approved Direction、設計方針、採用技術、却下した代替案、運用制約、security / policy boundary、後続 task が守るべき制約が変わった、または新たに明確になった場合は **Distill to ADR** を行う。scope / AC / policy / security boundary / prompt-output contract が変わる場合は `human_recheck_required` へ戻し、承認後に ADR を更新する。承認済み範囲内の設計詳細変更でも後続が参照すべき重要判断なら、PR に載せる共有資産として `docs/adr/` または repo 既定の ADR 置き場へ蒸留する。ADR には `Approved Direction` / `Decision` / `Rejected Alternatives` / `Consequences` / follow-up constraints だけを残し、tasklist 進捗や個別 verification log は残さない。raw task steering は AI 作業用の一時正本であり、ローカル / 作業 branch 内で管理してよい。ただし PR diff / main には入れない。PRに入れる永続成果物はADR。必要なら PR body に「ADR distilled after PR follow-up: <path | not_applicable + reason>」を追記する。
7. **Formal gate**: code / test / docs が変わったら `gdd-implementation-gating` を再実行する。advisory review 対応だけで formal gate を置き換えない。
8. **Secret and diff check**: push 前に `git diff` / `git status --porcelain` を確認し、secrets detected（AWS アカウント ID、秘密鍵、`.env`、API key、access token、Secrets Manager / SSM 実値）があれば push しない。
9. **Push**: valid fixes と evidence を commit し、`git push` する。push したら、PR 本文の影響範囲の節を `references/post-completion-pr-flow.md` の PR Body Merge-Triggered Workflows Check のとおり作り直す。PR 更新に必要な通常 push は許可するが、force push 禁止。履歴改変が必要なら人間に戻す。push 後、`gh pr view <PR番号> --json headRefOid` で PR HEAD が期待する commit SHA と一致するか確認する。不一致なら `git branch -vv` で upstream tracking を確認し、`git push origin <正しいブランチ名>` で明示再 push する。再 push 後は step 11 の fresh evidence 取得義務に従い、headRefOid の一致を必ず再確認する。
10. **Re-request**: 再依頼の直前に `last_head` を当巡でレビューした head に更新する（`first_head` は上書きしない。同一 PR 内でリセットしない）。再度レビュー指示を出す。可能なら `gh pr comment <PR> --body "<対応内容と再レビュー依頼>"`、または reviewer 再依頼 API / `gh` workflow を使う。環境上 re-request ができない場合は、再レビュー依頼文を提示し、manual action として残す。
11. **Repeat**: `gh pr view` / `gh pr checks` を再取得する。no actionable review findings かつ required checks が pass / neutral / skipped（理由付き）かつ **本周回までの `Fixed findings` すべてに対応する `Ripple check` 行が記録済み**なら loop を終了する。新しい actionable finding があれば 1 に戻る。pending / queued / in_progress の check が残る場合は clean としない。
    - **Ripple check 充足の確認（loop 終了条件）**: `Fixed findings` の各 id に対応する `Ripple check` 行が `state.md` または `worklog.md`（書式は `## State / Worklog Contract`）に存在するかを照合する。1 件でも欠けていれば `no actionable review findings` と宣言せず、その finding を未対応のまま 1 に戻す。
    - **確認間隔**: レビューの所要時間に合わせ、状態確認は 5〜10 分に 1 回に留める（短間隔の連続 fetch をしない）。
    - **待機中の取得量**: 変化検知は最小フィールド（`gh pr checks` の状態列、`--json latestReviews,mergeStateStatus` 等）に絞る。ただし**完了判定・対応要否の判断時は既存の fresh verification evidence 契約に従い全量を取得**する。

### ADR update required

以下のいずれかが true なら ADR update required:

- PR review / CI fix により、当初の Approved Direction と異なる実装方針を採用した
- reviewer の指摘で、採用技術・access method・境界条件・fallback 方針・verification 方針が変わった
- rejected だった代替案を採用した、または新たな Rejected Alternatives が生まれた
- 後続PR / post-merge verification / 運用担当が守るべき Consequences が増えた
- raw task steering の中にしか残っていない重要判断があり、PR merge 後に参照不能になる

ADR update が不要な場合も、state / worklog には `ADR distilled after PR follow-up: not_applicable | reason: <trivial wording / no decision change / test-only fix>` を 1 行で残す。重要判断があるのに ADR path も not_applicable 理由も無い状態で `clean` と言わない。PR diff に `.steering/<task>/` が含まれる場合は clean にせず、必要な判断を ADR へ蒸留してから raw task steering を PR diff から除外する。ローカルの steering を削除する必要はない。

## Auto-Arm Entry（PR 作成後の自動起動）

Post-Completion PR Flow（Option 1 × CI 正常パスのみ）から、人間キックなしで § Review Pending Loop に入る正規経路。

1. **発火条件**: 設定キー `PR Auto Review Convergence: reviewers=<list>`（解決順: ① `~/.gdd/config.local.md` ② 作業ツリー直下 `.gdd-config.md`。仕様は `references/operation-levels.md`）が存在し、かつタスク自走上限が「PR 作成 + 外部レビュー収束まで」であること。タスク自走上限が「PR 作成まで」なら設定キーがあっても発火しない。設定キーが無い環境では依頼も遷移も行わず従来どおり done 停止する
2. **初回レビュー依頼（CI pass 後・1 PR につき 1 回）**: `gh pr view <PR> --json reviewRequests` で既依頼を確認し、未依頼の reviewer にだけ依頼を実行して（Copilot は `gh pr edit --add-reviewer` で login 解決に失敗するため `gh api repos/<owner>/<repo>/pulls/<PR>/requested_reviewers -X POST -f "reviewers[]=copilot-pull-request-reviewer[bot]"` を使う。人間 reviewer は `gh pr edit <PR> --add-reviewer <login>`。2026-08-07 dogfood 実測） `Last PR Review Request At` を記録する。コマンド失敗（gh CLI < 2.62.0 / reviewer 解決不可 / 403 等）や reviewRequests 取得失敗の場合は auto-arm に入らず `Next Action=gdd-completion-check` を設定して `<gdd-stop reason="blocked">` で停止し、手動依頼文（実行すべきコマンド）を提示する（Post-Return Routing が completion-check 再試行として拾う）
3. **合流**: 依頼後は `PR Review Follow-up Status=waiting_for_review` として § Review Pending Loop に合流する。state 契約: `Next Action=done` を維持し `Resume From=external-review-waiting` を設定する。この間の `done` は暫定値であり、`Resume From=external-review-waiting` が併記されている限り終端ではない。収束 clean に到達した時点で `Next Action=done` の確定とあわせて `Resume From` から `external-review-waiting` を外し、terminal を確定させる（GDD の terminal 判定は `Next Action` と `Resume From` の両方を見る）
4. **停止境界は手動起動時と同一**: clean（latest head に unresolved actionable thread なし + required checks pass/neutral/skipped）で `<gdd-stop reason="done">`（直前に `references/post-completion-pr-flow.md` Step 4 の `記録の場所: なし` の行を書く）。ただし Stage Continuation（`references/post-completion-pr-flow.md` Option 1 手順 6）が発火する場合は done を出さず継続する。merge は実行しない。AC / scope / policy / security boundary に触れる指摘は `human_recheck_required`、poll 上限（既定 12 回）・同一 finding 3 回は `blocked`

## Review Pending Loop

レビューがまだ返っていない、または再レビュー依頼後に返答待ちの場合、Goal は未完了として扱う。PR 作成直後の「review findings 0件」は `clean` ではなく `waiting_for_review`。fix を push して再レビュー依頼を送った後は `pushed_waiting_re_review` とする。

待機時も毎回 fresh evidence を取る:

- `gh pr view <PR> --json headRefOid,latestReviews,comments,reviewDecision`
- GraphQL `reviewThreads` with `isResolved` / `isOutdated` / latest head comment anchors
- `gh pr checks <PR>`

`latest head` 判定では、現在の `headRefOid` と evidence の head SHA を照合する。古い head の outdated/resolved thread は blocker から外してよいが、latest head に残る unresolved actionable thread は blocker として loop を継続する。
merge gate hook は merge を止めず、不足を merge の後の「実行後の通知」で返す。そのため bot レビューの待ちは、merge の前に本 skill が確かめる。待ちの時間が過ぎていなければ、既存 Review Pending Loop の `ScheduleWakeup` を残り分後に 1 回で再武装し、`external-review-waiting` で停止する。独立レビュー（HEAD sha か、`references/independent-review.md` § 証跡 のとおり引き継いだもの。high 0・blocking 0）を記録済みなら待機は免除されるため、再武装せずそのまま merge へ進んでよい。merge の後に `review-wait-not-elapsed` などの通知が出たら、承認や証跡を後から書き足さず、ユーザーに報告する。

### Cross-Platform Waiting

レビュー収束待ちは自走させる。待機停止は `<gdd-stop reason="external-review-waiting">` で行う。Stop hook はこの reason を認識して継続 nudge を出さず、state.md を保持する。

- **Claude Code**: `ScheduleWakeup` で再開を予約して自走待機する。`sleep` でのブロック待機はしない（CI の完了など、判断の要らない処理だけを Bash の background で待つときは、plugin の `scripts/wait-until.py` で上限つきで待つ）。各 wake で `gh pr view <PR> --json reviews,reviewThreads,latestReviews,statusCheckRollup,headRefOid`（checks は `gh pr view --json` 非対応のため `gh pr checks <PR>` で別途取得）を fresh 取得し、(a) actionable findings あり → 修正ループ（手順 1〜）へ、(b) clean（latest head に unresolved actionable thread なし + required checks pass/neutral/skipped）→ merge gate へ、(c) まだ pending → 次の `ScheduleWakeup` を再 arm し `external-review-waiting` で停止する。
- **ポーリング上限**: 連続 wake を `state.md` の `PR Review Follow-up Attempts` で数え、上限（既定 12 回）に達したら `blocked` に落として無限ループを避ける。同一 finding が 3 回以上なら既存 Escape Hatch で `blocked`。
- **Codex**: `ScheduleWakeup` 相当が無いので、短時間なら heartbeat、長時間なら Codex automation で「PR review / checks を再取得して `waiting_for_review` / `changes_requested` / `clean` を報告する」follow-up を作る。automation は merge / deploy / write を実行しない。
- **Cursor**: Composer / Agent で同じ visible state（`waiting_for_review` / `pushed_waiting_re_review` と次回確認条件）を残し、同じチャットで再開できるようにする。

どの環境でも same visible state contract を守る。人間に見える状態は `waiting_for_review` / `changes_requested` / `fixing` / `pushed_waiting_re_review` / `clean` / `blocked` のいずれかで、何を待っているか、次にいつ何を確認するか、残タスクがあるかを明示する。

### auth pause 再開規約（machine-parseable / lint 対象）

自走中に SSO/auth セッションが失効した場合は終端停止せず、`external-review-waiting` と同じ非終端 pause に載せて再ログイン後に自走再開する。この規約は散文ではなく、`scripts/lint-pr-review-followup-state.py` が構造検証する以下の固定ブロックで宣言する（reason 行の値は `lib.constants.ALLOWED_STOP_REASONS` と一致しなければならない）。

```gdd-auth-pause
reason: auth-waiting
resume-on: 再ログイン検知後の ScheduleWakeup 再 arm で自走再開
no-cred: 認証情報（SSO token 等）は保持・出力しない
```

`auth-waiting` の wake は `lib.auth_waiting.next_reason_after_auth_wake` の bounded budget（`AUTH_WAITING_MAX_WAKES`、既定 12）で数え、上限到達で silently 再 arm せず `blocked` に落とす。停止出力には reason に対応した `## 👤 次にすること` ブロックを必ず付ける（`auth-waiting` は next-action guard の免除対象ではない）。

## External Review Skepticism

review feedback = suggestions to evaluate, not orders to follow。External Review Skepticism として、unclear finding は clarify all unclear items before implementing を原則に扱う。一部だけ実装してから質問しない。technical pushback が妥当な場合は、テスト・既存コード・承認済み artifact を根拠に invalid / out-of-scope として返答できる。

subagent や reviewer が `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` を返した場合は、懸念・不足情報・blocker を先に分類する。同じ finding が 3 回以上繰り返される場合は blocked とし、同じ修正を無限に push しない。

## Actionable Finding Definition

loop を続ける対象:

- `changes_requested`
- High・実害クラス category の valid finding と、それと同じ原因クラスタの Medium（対応プロトコル (d)）
- failed required check（個別 check 単位で判定する。集約表示の green だけを見て見落とさない）
- `mergeStateStatus: CONFLICTING`（他の finding より優先して対応する）
- Suppressed comments として展開された個別指摘（"no new comments" の裏に埋もれている場合も対象）
- security finding
- `Fixed findings` に載っているのに対応する `Ripple check` 行が無い finding（②未実施として未対応の valid finding のまま持ち越す）
- reviewer が明示的に修正を要求している comment

loop を止めてよい対象:

- invalid と検証済みで、PR コメントに根拠を残した comment
- out-of-scope と判断され、requirements amendment が必要なため `human_recheck_required` に戻した finding
- advisory / Low だけで、merge 前 blocker ではないと明示した finding
- merge を止める finding と同じ原因クラスタでない Medium で、worklog の follow-up 行に記録済みのもの
- no_action に分類したコメント（修正要求を含まない FYI / suggestion / positive comment）
- reviewer から新規コメントがなく、required checks が pass / neutral / skipped（理由付き）

merge gate（`gh pr merge`）はこの既定ポリシーを `Independent Review` の `high` / `blocking` カウンタとして読む（射影定義は「category の projection」= 本節の分類のうち実害クラス category（正本: `references/reviewer-common.md` § finding category）の件数を `blocking` へ、High severity の件数を `high` へ写像するだけで、本節の行動指示自体は変えない。算出主体は証跡を書く GDD main session で、`review-findings.md` の `IR` 節の行を `references/finding-dispositions.md` § 独立レビューの件数 のとおり数えて（`rejected:duplicate` は数えない）`blocking` を確定する。`medium` は記録用として残す）。

## State / Worklog Contract

各 iteration で `state.md` または `worklog.md` に以下を残す。

```markdown
PR Review Follow-up:
- PR URL: <url>
- Iteration: <N>（loop の周回。CI だけの周回を含む。巡数の正本は `PR Review Rounds`）
- Collected findings: <count>
- Valid actionable findings: <count>
- Findings: <id> | <file:line or -> | <severity> | <category> | origin: <this-diff|pre-existing|-> | fix_origin: <self-inflicted|inherited|-> | cause: <root cause カテゴリ>
- checkpoint: <trigger> → <選択> | round: <N> | at: <ISO 8601>（発火時のみ。state.md に書く。語彙は § Design Review Checkpoint）
- Fixed findings: <ids>
- Ripple check（規律 A / 手順5 ②）: <finding id ごとに 検索コマンド + 走査母集合（ファイル数・抽出条件） + ヒット件数 + ヒットを入れたクラスタ | not_applicable + 理由（Fixed findings が空の場合のみ）>
- Invalid / out-of-scope: <ids + reason>
- Verification: <commands + result>
- Push: <commit sha or not_pushed reason>
- Re-review request: sent / manual_required / not_needed
- ADR distilled after PR follow-up: <docs/adr/... | repo ADR path | not_applicable + reason>
- Next: repeat / no actionable review findings / human_recheck_required / blocked
- Idempotency key: <source:thread:file:line:finding>
- Post-fix Fresh PR Review Evidence: <gh pr view / reviewThreads / comments result>
- Post-fix Fresh PR Checks Evidence: <gh pr checks result>
```

Each finding should also carry a lowercase idempotency key so repeated CI failure or review thread processing can be detected without double-fixing the same item.
merge gate（`gh pr merge`）が読むため、`PR URL` は state.md の `## Gate Status` 節への記録が**必須**（`worklog.md` 代替は認めない。書式は `references/self-review-lanes.md` § merge gate 証跡）。証跡 6 種（`Merge Approval` を除く。`PR URL` / `Last Review Push At` / `Pre-Merge Review Recheck` / `Bot Review Received` / `Independent Review` / `Medium Disposition`）の記録タイミングは Route / Ownership（書き手は本 skill）: PR 作成直後 / push のたび / マージ直前の再 fetch直後 / fresh 取得ごと / 独立レビュー完了時 / 独立レビューの medium が 1 件以上のとき独立レビューと同時。書式は同ファイルへの参照 1 行にとどめる。`Independent Review` の起動方法・観点レーン・出力フォーマット・受理述語（high 0 かつ blocking 0）の正本は `references/independent-review.md`。`Merge Approval` の記録タイミングは他 6 種と異なるため別項で扱う（下記）。

`state.md` に残す field（`PR URL` のみ必須、他は推奨）:

- `PR Review Follow-up Status: waiting_for_review | changes_requested | fixing | pushed_waiting_re_review | clean | blocked | human_recheck_required`
- `PR Review Follow-up Attempts: <N>`（レビュー待ちの連続 wake 数。上限は `hooks/scripts/lib/constants.py` の `PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS` で、巡数ではない）
- `PR Review Rounds: <N> | first_head: <sha> | last_head: <sha>`（巡数。PR 作成時に `0` と PR head で初期化し、`PR Review Rounds` の導入前に作成された PR は followup 初回で `0 | first_head: <現 head> | last_head: <現 head>` として初期化する。`PR Review Rounds` が無いときの初期化（PR 作成時の分と導入前の PR の分のどちらも）は、followup を起動した直後、その回の `Iteration` 行を書く前に判定し、当 PR の `Iteration` / `Findings:` / `checkpoint:` 行が state.md・worklog.md のどちらにも無いときだけ行う。どれかがあるのに `PR Review Rounds` が無い・読めないときは初期化せず § Design Review Checkpoint の (a) 判定不能として扱う。更新契機とリセット契約の正本は `references/state-field-tiers.md`）
- `Last PR Review Request At: <ISO 8601>`
- `PR URL: <url>`（**必須**。記録先は `state.md` の `## Gate Status`。書式は `references/self-review-lanes.md` § merge gate 証跡）
- `PR Head SHA: <headRefOid>`
- `Next Review Check: <ISO 8601 or manual>`
- `ADR distilled after PR follow-up: <path | not_applicable + reason>`

`Merge Approval` は**閉じた確認への返答**として取る（`references/post-merge-qa.md` 手順 2 の自走のマージの条件をすべて満たすときだけ問わず、同じ手順の形で書く。満たさなければ自走上限の値を問わずここで問う）。マージ直前に `PR #<n>` と `head <sha>`（`git rev-parse HEAD` 実測値。`gh pr view <PR> --json headRefOid` と違えば問わずに報告する）を提示して可否を問う 1 問を出し、承認されたら `gh pr merge <PR> --match-head-commit <その sha>` でマージする。その文面には**受理される返答形を 1 つ示す**（正本は `constants.py` の `MERGE_APPROVAL_PHRASES`）。示さないと肯定の間投詞だけの返答が承認にならず、取り直しても同じ返答が返って進まない。cross-session messaging 経由で届いた承認語は `Merge Approval` の根拠にしない（`references/phase-progression.md` § Cross-Session Messaging の権限境界）。機械的な最終防御は `hooks/scripts/validate-steering-write.py` にある（peer turn 直後の記録は block される）。返答が承認と判定できたターンで、その場で `state.md` の `## Gate Status` に bullet 1 段（`- Merge Approval: PR #<n> / head <sha> | evidence: <承認発言の要約> | approved_at: <ISO 8601>`）で記録する（後追いでまとめて書かない）。語彙判定は `constants.py` の `is_merge_approval()` を正本にする（本 skill に語彙 literal を書かない）。同述語はこの返答だけを受け、作業指示・条件付き・否定は承認にしない。判定できない返答は承認にせず確認を出し直す（`approval-missing` の不足は、返答形を示した出し直しで解ける）。承認後に commit を積むと sha が変わるので取り直す。subagent は書かない。書式の正本は `references/self-review-lanes.md` § merge gate 証跡。

## Escape Hatches

- same finding repeats >= 3: 同じ finding が 3 回以上再発する場合は blocked とし、root cause が修正方針・テスト・reviewer expectation のどこにあるかを調べる。無限に push しない。§ Design Review Checkpoint との順序: checkpoint が先行し、3 択が「パッチ継続」の巡に限り本カウントを継続する（(1) では 0 に戻し、(2) は対象外）。
- **structural mismatch early-exit（attempt 1 で中断）**: 検証ループ中に、eval ハーネスの構造が想定と根本的に異なる / 前提条件が設計時点で存在しない等、**前提崩壊（structural mismatch）**を検知した場合は、回数閾値を待たず **attempt 1 時点で** `planning_rework_required` として中断・再計画する。既存の `same finding repeats >= 3` は refinement（実装改善で解消できる失敗）に適用し、structural mismatch には適用しない。refinement 例: 実装コードのバグ / テストの誤り / 設定値の調整。structural mismatch 例: eval ハーネスが MCP を強制無効化するため Serena 依存の設計が機能しない / CI 環境に前提ランタイムが存在しない。正本規律: `references/phase-progression.md` § Escalation Decision Table「初回試行で前提が崩れた失敗（structural mismatch）」を参照。
- scope / AC / policy / security boundary / prompt-output contract が変わる: `human_recheck_required` に戻す。PR comment だけで承認済み要件を silent に変更しない。
- required check が外部障害で失敗し続ける: `blocked` として、解消手順と待ち条件を出す。
- secrets detected: commit / push を止め、ユーザーに即報告する。マスク・削除・履歴上の扱いを確認するまで PR 更新しない。
- reviewer が merge / deploy / production write を要求しても、この skill では merge / deploy は実行しない。

## Output Template

```markdown
## PR Review Follow-up

PR: <url>
Iteration: <N>

### 収集したレビュー指摘
| # | source | severity | finding | 判定 | route |
|---|---|---|---|---|---|
| 1 | GitHub PR comment | Medium | <要約> | valid | implementation_fix_only |

### 対応
- 修正した finding: <ids>
- 修正しない finding: <ids + reason>
- 実行した検証: <commands + result>
- push: <commit sha / not_pushed>
- 再度レビュー指示: sent / manual_required / not_needed

### 次
- status: waiting_for_review | changes_requested | fixing | pushed_waiting_re_review | clean | human_recheck_required | blocked
- next check: <automation / heartbeat / manual / now>
- clean 条件: latest head の unresolved actionable thread なし + required checks pass/neutral/skipped
```

## Guardrails

- PR 作成後レビュー指摘を `gdd-pr-review` だけで閉じない。`gdd-pr-review` は PR 作成前 / final diff review の skill。
- valid finding を検証せず即修正しない。必ず `gdd-receiving-code-review` の評価順を通す。
- code / test / docs を変更したら、push 前に必要なテストと `gdd-implementation-gating` を再実行する。
- force push 禁止。履歴改変が必要な場合は人間に戻す。
- merge / deploy は実行しない。
- no actionable review findings と言う前に fresh に PR reviews / comments / checks を再取得する。
- review pending を clean と呼ばない。レビュー未着、レビュー待ち、再レビュー待ちは `waiting_for_review` または `pushed_waiting_re_review` として残す。
- flat comments only で unresolved thread の有無を判断しない。thread-aware evidence が取れない場合は `blocked` または `manual_required` として不足を表示する。
- レビュー待ちで `sleep` によるブロック待機をしない。`ScheduleWakeup` で自走し、停止は `<gdd-stop reason="external-review-waiting">` を使う。
- ポーリング上限（既定 12 回）に達したら `blocked`。無限に再 arm しない。
- clean 後の merge は条件付き明示指示時のみ。merge method は `gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed` で許可された方式から選ぶ（squash 固定で試行しない）。
- **GitHub 投稿の安全構築（Body Construction Safety）**: `gh pr comment` の `--body` にシェルのコマンド置換（`$(...)`）や動的生成された生ログ（pytest 出力・traceback 等）を直接埋め込まない。本文は先にファイル（scratchpad）か変数に確定し、投稿前に内容をプレビュー表示してから `--body-file` 等で渡す。**本規則は Route ステップ（手順4）の `--body "reason"` 等の簡略記法例に優先する**: 手順4の例は固定の短い文字列を示す簡易表記であり、動的ログを埋め込まない限りにおいて直接 `--body` を使ってよいが、内容に不確実性がある場合は本規則の手順（ファイル確定 → プレビュー → 投稿）を常に優先する。
- **フォーマルレビュー投稿の禁止（Formal Review Posting Ban）**: `gh pr review` / `gh api .../pulls/<PR>/reviews`（state=APPROVED/CHANGES_REQUESTED/COMMENTED の formal review）は、ユーザーから明示的に依頼された場合のみ実行する。本 skill の Route ステップが許可しているのは `gh pr comment`（PR タイムラインへの単純コメント）のみであり、ユーザー本人のアカウントでの formal review 投稿はこの権限に含まれない。
- **Push 前のコミットスコープ確認（Commit Scope Hygiene）**: `git push` する前に `git diff main...HEAD --stat` で、今回の followup fix と無関係なファイルが混入していないかを確認する。無関係な変更（別タスクの実装等）が混入している場合、push せずに人間に確認する。履歴改変（コミットの除外・squash 等）は自分で行わず人間に戻す（Serena MCP 追加ブランチに無関係な owasp-eval / Snyk 変更が混入し、Copilot レビューで指摘されるまで気づかなかった再発防止）。
- **Amendment 境界の明示（Amendment Boundary Labeling）**: 各 Route の対応が「当初 AC 範囲内の修正」か「当初範囲を超える追加」かを判定する。「3 ラウンド以上連続」とは、**既に Route/Fix が完了した過去のラウンドのうち、「当初範囲を超える追加」と判定されたラウンドが間に AC 範囲内ラウンドを挟まず連続で 3 回以上続くこと**を指す（AC 範囲内の修正ラウンドを 1 回でも挟んだ場合はカウントをリセットする）。**今回新たに来た未対応の指摘（現在判定中のラウンド）はこのカウントに含めない**。過去の連続数が 3 に達している場合、現在判定中の指摘の Route 判定を行う前に `gdd-requirements-amendment` の `Active Follow-up Classification` を一度実行して design.md への反映を検討する（複数 PR を横断する修正ループでAC範囲内/amendment相当の境界が曖昧になった再発防止）。
- **PR スコープ膨張の抑止（PR Scope Creep Guardrail）**: review 対応の修正が当初 AC/diff のスコープに含まれない新規ファイル・新規機能へ広がった場合、そのまま同一 PR に積み増さず、分割を検討する（目安: 当初 diff から additions が 2 倍を超える、または新規スコープが 3 iteration 以上連続で発生する）。分割が難しい・急がない場合も、少なくとも新規スコープを追加した理由を PR 本文または `worklog.md` に 1 行残す（PR 旧#900 では commit 数と追加行数が大きく膨らみ、レビュー対応自体が新しい指摘を呼ぶ正のフィードバックで収束が遅れた）。
- **セルフレビュー打ち切り宣言の禁止（No Self-Exemption From Self-Review）**: 「セルフレビューはここで打ち切り、以降は Copilot / CI に任せる」のような自己免除宣言をしない。push 前セルフレビューを開始した回では、以降のすべての push 前に同じセルフレビューを通す。既に開始したセルフレビューを自己判断で省略した場合、無指摘 push が続いていても `clean` と申告しない（PR 旧#900 実測: 自己免除を宣言した後、一度もセルフレビューを通さず push を繰り返し、Copilot 指摘の再発が継続した）。
- **opt-out 等価物の追加禁止**: 以下はユーザーの明示指示なしに AI が行わない — (v) `.claude/gdd-dev.local.md` の `session_id` 書き換え (vi) 別 checkout / 別 worktree からの push（`git -C <他 repo>`） (vii) `settings.json` / `settings.local.json` の `env` へ `GDD_SKIP_PRE_PUSH_GATE` / `GDD_HOOK_STATE_DIR` を書く (viii) `hooks/hooks.json` / hook 本体の編集 (ix) push を包むスクリプト / git alias の作成
- push 前の証跡記録: `git push` する前に `Pre-Push Self Review` を記録する（followup 周回では内部整合レーンのみ必須。`references/self-review-lanes.md` § followup 周回時のレーン要求 を参照）
- マージ後に着弾したレビューの扱い（検証 → follow-up 切り出し）は `references/post-completion-pr-flow.md` § マージ後着弾レビュー を参照する。
