---
name: gdd-design-gating
description: "Internal: auto-routed only when Next Action=gdd-design-gating. Reviews design before task breakdown."
version: 0.1.0
---

# Design Gating

approved な `requirements.md` と human check 前の `design.md` skeleton をもとに detailed design を具体化し、reviewer を通して implementation planning に進めるかを判定する。状態遷移の概要は `references/state-machine-overview.md`、詳細な遷移表は `references/state-machine.md` を参照。

## Goal

- approved な `requirements.md` と design skeleton をもとに `design.md` を具体化する
- version-sensitive / fast-moving な利用技術の最新情報を確認し、design に反映する
- `gdd-planning-reviewer` と applicable `gdd-security-reviewer` で文書品質、非機能、実現可能性、セキュリティを確認する
- prompt / skill / review policy / 人間向け出力を変更する場合は、必要に応じて dialectic review lane を走らせ、表現・severity・採否判断の揺れを設計段階で収束させる
- `Gate Status` を更新する
- `gdd-task-breakdown` へ進める状態を作る
- active な `/gdd-dev` run では、`Resume From=gdd-task-breakdown` を報告して止まらず、そのまま `gdd-task-breakdown` に handoff する
- 実装後の差し戻しが発生しても、人間再チェックは `human_recheck_required` のときだけに絞る
- route / owner / prompt/output contract / masking / rollout の変更が、人間承認済み policy の範囲内かどうかを明確に判定する

## Fixed Model

`references/fixed-models.md` を参照（Claude Code: `opus` + `effort=high` / Cursor: `Grok 4.6` + `medium` / Codex: `gpt-5.6-sol` + `medium` 固定。理由: design は formal review、軽量モデル禁止）。

## Inputs

- `.steering/.../requirements.md`
- `.steering/.../design.md`
- `.steering/.../adr.md`（存在すれば補助コンテキストとして読む）
- `.steering/.../worklog.md`（存在すれば planning 中の調査過程を補助コンテキストとして確認する。detailed design 具体化の過程で新たに調査した内容も追記してよい）

## Review Set

- always:
  - `gdd-planning-reviewer`
- conditional:
  - `gdd-security-reviewer`（認証・認可・secrets・PII・untrusted input が設計論点の場合）
- すべて plugin 内 `agents/` に同梱された reviewer を使う。root 側 `~/.claude/agents` は前提にしない。
- selection rule の正本:
  - `references/reviewer-selection.md`
- dialectic review lane:
  - `references/dialectic-review.md`
  - formal reviewer ではなく補助 lane。trigger に該当する場合だけ selected とし、結果は `design.md` または `worklog.md` の `Dialectic Review Summary` に圧縮して残す
- task sizing:
  - `Task Size: quick` の場合は `gdd-planning-reviewer` のみで security reviewer を省略してよい（`references/task-sizing.md` 参照）
- lazy loading:
  - `references/reviewer-selection.md` の概要表で selection を先に決定し、`selected` になった reviewer の agent 定義（`agents/*.md`）だけを読む
  - `waived` の reviewer の agent 定義は読まない

## Status Update Format

Schema の正本は `references/gate-status-schema.md`。許容値・`<status> | evidence | updated_by | updated_at` フォーマット・`waived` 禁止（phase-level のため）はすべて schema に従う。

この skill 固有の補足:

- この skill に入る時点で `Requirements Review Status=approved` と `Human Check Status=approved` を前提にし、requirements / AC / 実装方針が本当に変わる場合だけ人間再チェックへ戻す
- E2E Discovery Loop 経由（`design_detail_only` で自走中）の場合は、`Approved Direction` の自走範囲内であれば human check に戻さず gate を完了してよい（詳細は `references/phase-progression.md` の「E2E Discovery Loop」を参照）

## Steps

1. `requirements.md` と `design.md`（と `findings.md` があれば）を読み、対象技術・version 前提・`Open Questions`・承認済みの採用技術と実装方針を抽出する。
2. 利用技術が version-sensitive または fast-moving な場合は、最新の公式ドキュメント / release notes / migration guide を確認する。利用可能なら `tech-docs-searcher` を優先し、無ければ host の web/doc search で補う。
3. 最新情報を踏まえても、`requirements.md` の要件・受入条件・実装方針を変更せずに detailed design へ落とせるか確認する。
   - detailed design で access method（MCP / CLI / SDK / API / wrapper 等）、採用技術、credential backend（Secrets Manager / SSM / env / OAuth 等）、multi-tenant 切替・境界、official integration の採否が承認済みの `実装方針` から変わる場合は、単なる設計詳細ではなく `human_recheck_required` を検討する。
   - detailed design で approved architecture option / code structure / package manager / runtime / install command / test command / CI command が承認済みの `実装方針` から変わる場合は、単なる設計詳細ではなく `human_recheck_required` を検討する。
   - vendor official integration が新たに確認できた、または GA / preview / deprecated 等の maturity が requirements 時点と異なる場合は、承認前提が変わっていないか確認する。変わるなら `design_detail_only` で閉じない。
4. lightweight `design.md` skeleton の必須項目が揃っていない場合は、reviewer 起動前に埋める。
5. `design.md` を更新し（書いてある分は確かめ、足りない分を足す）、approved な `requirements.md` をもとに少なくとも次を具体化する。
   - 変更点の要約
   - 影響範囲。規定を変えるなら、変える前の語と正本名で `git grep` した語と、外の記述ごとに直すか直さない理由
   - 主要フロー
   - 承認済みの採用技術・access method・architecture option を detailed design へ落とした結果（承認前提から動く場合は Step 3 の判定へ）
   - テスト方針（`references/testing-anti-patterns.md` § テスト判定基準 に沿う）
   - ロールバック / 失敗時の戻し方
   - 該当時のみ: `Route / Ownership Matrix`（enforcement point の具体化）／`Sensitive Data / Masking Policy`（同）
   - 新設要素があれば配線表（5c 参照）
   - 採用しない代替案は `adr.md` へ（`references/adr-vs-design.md`）
     5a. **LLM 出力責任分界チェック（LLM Output Boundary Check）**: SKILL.md が外部出力（Slack / GitHub / wiki）を扱う場合、以下の観点で設計を確認する:
     - スクリプトが `--json` で返したデータを LLM がフォーマットして投稿する設計の場合、データ件数が可変かつ 20 件超の可能性があるなら **High risk** として flagging する
     - 推奨: スクリプト側で最終テキストを生成する `--slack-mrkdwn` パターンに変更し、LLM はそのまま投稿するだけにする
     - LLM の判断が必要な出力（要約・ナラティブ・調査報告等）は決定性不要のため許容する
     - **判定基準**: 「出力先が外部サービス」かつ「データ件数が可変で 20 件超の可能性」かつ「全件の忠実な再現が求められる」→ スクリプト生成方式を推奨
     - **Why:** 一覧の投稿機能で LLM フォーマット方式を採用した結果、同一入力で大半の行が落ちる非決定的な挙動が発生した。SKILL.md に「省略禁止」と書いても LLM は従わない
       5b. **出力先レンダリング制約チェック（Delivery Channel Rendering Check）**: `references/e2e-verification-catalog.md` § Pattern 2 を適用する。出力先が Slack / GitHub / wiki 等の外部サービスの場合、マークアップ仕様 / AgentCore 経由のエスケープ影響 / フォーマットサンプルを `design.md` に記録する。記録なしは Medium finding。
       5c. **配線表（Wiring Table）**: 新設する要素（関数・state field・trigger・閾値・マーカー）がある場合、要素ごとに1行、次の列を持つ表を `design.md` に記載する: 要素 / 書く側（file:関数）/ 読む側 / 入口からの到達経路（hook 起動・CLI 等）/ 同じ入力を読む既存実装 / 検証テスト名。新設要素が無い場合は表自体を省略してよい。`gdd-planning-reviewer` の配線表整合チェックが、この表の各行を実コードと突き合わせる。
       5d. **規則の実値検算**: 外部の形式から値を取る規則（正規表現・上限値など）は、`references/brainstorming-steps.md` § 8a の fixture（値の形が足りなければ § 8a と同じ扱いの実データ）に当て、`落ちた件数 / 総件数` と落ちた値の形を `design.md` に記録して確定する。0 件でなければ、規則を直すか落としてよい理由を書く。どちらのデータも無ければ未測と理由を書き `Open Questions` に出す。記録なしは Medium finding
6. 最新情報から confirmed facts と未確認事項を分けて `design.md` に残す。確認できない点は `Open Questions` に落とし、requirements / implementation policy の変更が必要だと分かった場合は silent change せず `human_recheck_required` または `planning_rework_required` に戻す。
   - 最新技術情報の再確認を説明するときも、戻し先は単に「requirements に戻る」ではなく `human_recheck_required` / `planning_rework_required` のどちらかを名前付きで明示する。
   - detailed design を固める過程で重要な意思決定や却下した代替案が確定した場合は、任意で `.steering/.../adr.md` を作成または更新し、`Context` / `Decision` / `Why` / `Consequences` を追記してよい（`references/adr-vs-design.md` の書き分けルールに従う）。
   - final output の owner、delivery path、prompt contract、output contract、prompt への sensitive value 投入、mask / reject / sanitize の enforcement point、rollout / rollback の順序が approved な requirements / human approval から動くなら、`design_detail_only` ではなく `human_recheck_required` または `planning_rework_required` を優先して検討する。
   - Step 3 の列挙が承認済みの `実装方針` から動くときも同じに扱う。
   - 上記が requirements で既に承認済みで、design が enforcement point や component boundary を具体化するだけなら `design_detail_only` で閉じてよい。
7. `references/reviewer-selection.md` に従って applicable reviewer を選び、`Planning Reviewer Selection` を `state.md` に記録する。
   - `gdd-planning-reviewer` は必ず `selected`
   - `gdd-security-reviewer` は条件に該当しなければ `waived` にし、reason に non-applicable と分かる根拠を残す
   - `references/dialectic-review.md` の Trigger に該当する場合は Selection Values に従って `Dialectic Review Lane=selected` または `selected(existing_evidence)` を `state.md` または `worklog.md` に記録し、該当しない場合は記録省略または `not_applicable` でよい
   - selected の場合、Primary / Counter / Cross-review / Revision / Final synthesis を実行し、詳細ログではなく `Dialectic Review Summary` だけを `design.md` または `worklog.md` に残す
   - dialectic の結果、AC 追加/削除・scope・policy・ownership・security boundary・prompt-output contract が変わるなら `design_detail_only` で閉じず、`human_recheck_required` / `planning_rework_required` を検討する
   - **Cumulative Diff Base 書込責務**: design が `approved` に遷移した瞬間に `state.md` の `Cumulative Diff Base` field を記録する（Scope Drift Guard の impl-gate「前回の 2 倍以上」判定の分母となる基準値。欠落すると判定が fail-open 化するため必須）
     - **schema（list of entry、必須 field）**:
       ```
       Cumulative Diff Base:
         - files: <int>              # 計測手順は下記「計測規則」参照
           hash_prefix: <string>     # feature 作業ブランチの HEAD commit sha 先頭 8 hex（この entry 記録時点）
           recorded_at: <ISO8601>    # UTC タイムスタンプ
           reason: <enum>            # 許容値: initial_design_approved / recalibrated_after_changes_requested / recalibrated_after_human_recheck
       ```
     - **計測規則**:
       - `<glob>` の正本は **`design.md` の「影響範囲」節** に記載された glob リスト（skeleton 段階で approved された glob を design-gating で具体化した最終値）。他の場所の glob 定義と食い違う場合は design.md を優先
       - `files` = `git ls-files <glob>` の件数。未存在 path は 0 としてカウント（glob に該当する tracked file が現時点で 0 件でも entry は必須）
       - `hash_prefix` は **feature 作業ブランチ HEAD** の sha を採用（base branch HEAD ではない。base マージによる数値揺れを避け、design approved 時点のスナップショットを固定する）
       - drift 経由の再 approved で glob が拡大する場合、拡大は Approved Direction 拡張の帰結として受け入れ、新 glob で再計測した値を累積追記する
     - **semantics**: list の**最新 entry（末尾行）** が impl-gate Scope Drift Guard の分母。過去 entry は append-only の audit trail として保持し、分母には使わない
     - **初回書込**: design が初めて approved になるとき、list を新規作成して 1 entry 追加（`reason: initial_design_approved`）
     - **累積追記（上書き禁止）**: 2 回目以降の design-gating（`changes_requested` 後の再承認 / `human_recheck_required` route 復帰後の再承認）では既存 entry を残したまま末尾に 1 entry 追加する
       - `changes_requested` 経由 → `reason: recalibrated_after_changes_requested`
       - `human_recheck_required` 経由 → `reason: recalibrated_after_human_recheck`（新 Approved Direction に対して再計測した値を記録。旧基準は stale のため分母に使わず audit 履歴として残る。詳細は `references/rollback-patterns.md` の `human_recheck_required` 参照）
8. reviewer 起動前に `state.md` の `Gate Status` を更新し、`Requirements Review Status=approved | evidence: <requirements-review-id> | updated_by: gdd-design-gating | updated_at: <timestamp>`、`Design Review Status=in_review | evidence: <review-start-id> | updated_by: gdd-design-gating | updated_at: <timestamp>`、`Human Check Status=approved | evidence: <元の evidence> | updated_by: gdd-design-gating | updated_at: <timestamp>`、`Resume From=gdd-design-gating` を永続化する。phase を抜けるとき `references/phase-gate-prechecks.md` step 3 に従い `Last Handoff Summary` を更新する。
9. selected reviewer だけを `references/subagent-dispatch.md` § Reviewer Input and Time Budget に従って呼び、blocking と advisory を `references/requirements-gating-steps.md` § 精度の第一原則 のとおりに分ける（reviewer の `blocking:` 欄に従う）。advisory は `design.md` または `worklog.md` に記録する。
10. reviewer 指摘が `planning_rework_required` を要求する場合: `references/rollback-patterns.md` の `planning_rework_required` パターンに従い Gate Status を永続化する。

11. reviewer 指摘が `human_recheck_required` を要求する場合: 先に、承認済みの AC への計測の締め直しだけで済む blocking を、人に戻さず `references/requirements-gating-steps.md` § AI が閉じる blocking のとおり閉じる。残りが `human_recheck_required` を要するときだけ、`references/rollback-patterns.md` の `human_recheck_required` パターンに従い Gate Status を永続化する。

12. reviewer 指摘が `design_detail_only` で解決できる場合: `references/rollback-patterns.md` の `design_detail_only` パターンに従い Gate Status を永続化する。同 route の**記録要件**（`design.md` 本文更新 + `adr.md` の Context/Decision/Why/Consequences 追記。`design_detail_only` は remediation 扱いのため `adr.md` entry には `- **Origin**: remediation / <Current Task>` 行も必須。正本: `references/state-machine.md` § Remediation Loop Safety の ADR ≥2 独立トリガー）が欠けている場合は `approved` にしない。AC の根本追加/削除・`Approved Direction` の方向性変更・final output owner / delivery path / prompt-output contract / masking enforcement / rollout order の変更が含まれる場合は `human_recheck_required` に昇格する。再入の前の反映は blocking の処置だけにする（advisory は手順 14）。

13. E2E Discovery Loop 経由（`gdd-systematic-debugging` が `design_detail_only` で自走中）の場合:

- `state.md` の `Approved Direction` を確認し、自走範囲内かを判定する
- 自走条件（AC を壊さない・方向性と矛盾しない・セキュリティ要件の新規発生でない・AC の根本追加削除でない）をすべて満たせば、reviewer は通すが human check に戻さず gate を完了する
- 自走条件を満たさない場合は `human_recheck_required` に escalate する。reviewer が policy-level の判断が要る指摘を blocking で出したときも、自走条件の外として扱う（`references/requirements-gating-steps.md` § 精度の第一原則）
- **記録要件**: E2E で判明した制約は `design.md` の該当セクションに直接反映し、`adr.md` に「E2E で判明した事実 / 採用した設計変更 / 却下した代替案」と `- **Origin**: remediation / <Current Task>` 行を必ず追記する。自走は記録の省略を意味しない
- 詳細な自走条件は `references/phase-progression.md` の「E2E Discovery Loop」を参照

14. 手順 9 の blocking がすべて解消済みなら（advisory は最後の Round の後に反映する。`references/requirements-gating-steps.md` § レビューループの契約 3）:

- `Requirements Review Status=approved | evidence: <requirements-review-id> | updated_by: gdd-design-gating | updated_at: <timestamp>`
- `Design Review Status=approved | evidence: <review-id> | updated_by: gdd-design-gating | updated_at: <timestamp>`
- `Human Check Status=approved | evidence: <元の evidence> | updated_by: gdd-design-gating | updated_at: <timestamp>`
- `Resume From=gdd-task-breakdown`
- `tasklist.md` が既にあり、かつ上記 3 つの gate status がすべて `approved` の場合のみ `Next Action=gdd-task-breakdown`。gate status が stale な場合は `tasklist.md` の存在だけで routing しない
- `state.md` の `Route In Progress` が `design_detail_only` または `human_recheck_required` の場合は `none` にクリアする（`references/rollback-patterns.md` 参照）
  に更新する。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、承認見出しルール、最新情報確認、planning 差し戻し route、gate 開始前の記録ルール、fail-closed 応答）。以下はこの skill 固有のルール。

- Bounce Log: `references/bounce-log-schema.md` 準拠、閾値`>= 2`、escalate先`human_recheck_required`（ユーザー提示escalation。`gdd-systematic-debugging`不使用）

- `Requirements Review Status=approved` と `Human Check Status=approved` の前にこの skill を正式通過させない
- 手順 9 の blocking を黙って抱えたまま進まない
- approved な requirements / implementation policy を design 側で勝手に追加変更しない
- final output owner / delivery path / prompt-output contract / masking enforcement / rollout order の変更を、generic な設計修正として見逃さない
- 承認済みの `実装方針` に無い access method / credential backend / tenant 切替方式 / architecture option / file placement / package manager / runtime / install command / test command / CI command を design 側で新規採用しない。必要になったら `human_recheck_required` に戻す
- **Primary Source Verification（一次情報確認）**: AC に技術的な断定（特定サービス・API・仕様の挙動についての確定的な記述）を含める前に、公式ドキュメント等の一次情報で確認する。未確認のまま断定して human check に出し、後から覆すと、承認往復が繰り返される（断定を後から覆す動きで human-check-waiting が短期間に続けて発生した事例の再発防止）。確度が低い場合は断定せず「未確認・要検証」と明記して提示する。**適用対象は design phase で新たに導入する未確認の断定のみ**: planning 時点で既に一次情報の引用付きで確認済みの事実は再確認不要（既存の引用元をそのまま根拠として維持してよい）。断定の訂正が AC の実質的な意味（受入条件・実装方針そのもの）を変えない場合は `design_detail_only` で処理してよく、実質的な意味が変わる場合のみ `human_recheck_required` とする。
