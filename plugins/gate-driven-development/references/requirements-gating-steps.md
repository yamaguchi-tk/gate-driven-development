# Requirements Gating: Steps & Human Check Handoff

> **所有**: `gdd-requirements-gating` の詳細手順
> **参照元**: `skills/gdd-requirements-gating/SKILL.md`

## 精度の第一原則

出荷物の品質はテストと implementation-gating が担保する。requirements-gating が高精度で守るのは **人間の承認判断に使う箇所**と **AC の意味**だけ。それ以外の記述の詳細化・網羅化を gate で追わない。

- **blocking にできる指摘は「AC の意味・スコープ・承認ポイント・安全境界（破壊的操作・秘匿・不可逆）」に影響するものだけ**（接地条件）。検証手順の精度・trace の網羅性・語彙・文言への指摘は advisory として記録し、changes_requested の理由にしない
- **requirements / design 段階の blocking の決め方はこの節が正本**（`gdd-requirements-gating` と `gdd-design-gating` の両方。reviewer の観点〔requirements・design・security〕を問わない）
  - blocking にするのは、接地条件のどれかに当たり、failure scenario（具体的な入力・状態 → 誤った結果）を付けられる指摘だけにする。severity（High / Medium / Low）と category は blocking を決めない。`reviewer-common.md` の `is_blocking`（実害クラス）と category 未付与の既定は requirements / design 段階を除く数え方で、この段階には当てない
  - failure scenario を付けられなくても blocking のまま扱うのは、`reviewer-common.md` § 常時 High の適用範囲の 4 型に当たる指摘だけにする。ほかの安全境界の指摘は、破壊的操作・秘匿・不可逆のどれに当たり、何が壊れる・漏れるかを failure scenario に書く。reviewer が当たるかで迷ったときは、AC の意味・スコープ・承認ポイントなら `blocking: no` にして迷った点を書き、安全境界なら `blocking: yes（安全境界）` にしてどれに当たりうるかを failure scenario に書く。`gdd-security-reviewer` の指摘も、ほかの reviewer と同じくこの規則で分ける（security の観点だからという理由では blocking にしない）
  - reviewer は指摘ごとに `blocking: yes（<当たる接地条件>）` か `blocking: no` を書く（出力形式の正本: `reviewer-common.md` § Output Format）。gate を実行する側は、reviewer が `blocking: no` にした指摘を blocking に上げない。`blocking: yes` を advisory に下げてよいのは次の 2 つのときだけで、ほかは欄のとおりに扱う。どちらも、指摘ごとに理由（(b) では当たる規則の場所）を `reviews.md` に書き、`reviewer-common.md` § 常時 High の 4 型に当たるものは下げない。(a) artifact と実コードを追って再現できないとき。(b) 欄の値が、advisory にすると決めた規則に反するとき。当てられる規則の置き場所は、この節、§ レビューループの契約、`subagent-dispatch.md` § Reviewer Input and Time Budget の blocking の条件、`agents/gdd-planning-reviewer.md`・`agents/gdd-security-reviewer.md` の定義に限る
  - 下げることとは別に、`gdd-requirements-gating`（human check の前）では、policy-level の判断が要る指摘（安全境界に当たるものを含む）を `Human Check Questions` に移して blocking を解除してよい。人の回答で閉じる処置で、移した項目には元の指摘 ID と当たる接地条件を書く。安全境界に当たる項目を移した human check は、事前回答（委任）があっても人に表示する（正本: `references/human-check-template.md` § 事前回答 3）。`gdd-design-gating` ではこれを使わず、policy-level の指摘は blocking のまま残し、同 skill の `human_recheck_required` の手順で人に戻す。欄が無い指摘は、gate を実行する側がこの規則で分け、そうしたことを `reviews.md` に書く
  - `gdd-design-gating`（human check の後）では、`agents/gdd-planning-reviewer.md` の `Open Predicate in AC`（承認済みの AC に閉じ方も開示も無い開いた述語）は `blocking: no` にする（閉じ直すには amendment が要る）。安全境界に当たるものは除く。承認済みの AC へのほかの指摘（`計測:` が改善を測れないなど）は上の規則で分け、blocking なら `human_recheck_required` で人に戻す。ただし § AI が閉じる blocking に当たるものは、人に戻さずその節のとおり閉じる
- **枠（節見出し）は機械強制・中身は prose**。節の存在と決まった欄（AC の `根拠:`・`計測:`、承認ポイントの `根拠:`、処置の `根拠:`・`伝播:`）の有無は確認するが、中身の網羅性を gate で採点しない。欄の書き方の浅さは blocking にしない（欄が指す事実がコード・データと違えば、AC の意味として blocking にできる）。進行中のタスクが欄を書き足すのは、再入の「変えた節」に数えない

**Why**（2026-08-31〜09-01 の経験による）: 中身の精度を gate で追った結果、レビューが何ラウンドも長時間発散し、AC が 1 文字も変わらないままラウンドが続いた。文書が肥大するほど指摘が再生産され、収束しない。

## レビューループの契約

1. **ラウンド上限**: 初回レビュー + **再入は 1 回まで**。それでも blocking が残る場合は、ラウンドを重ねず、§ AI が閉じる blocking を閉じた後の**残る blocking を一覧で人間へ一括提示**する。選択肢は accept as known risk / 修正 / 差し戻しに、残った指摘と依頼の未達を生んだ設計の決定・前提を名指しして変える案を加える。すべての選択肢を、依頼を満たすか・原因が消えるかで比べ、推奨は依頼を満たし原因を消す案を優先する。変える案が無いときは、無い理由を書く。ほかの上限（修正の回数など）で止まるときも同じにする。一括提示を書く前に、遷移を書く側は、依頼の原文（`.steering/<task>/request.md`）に照らして、残った指摘を生んだ前提を自分で点検する（点検のために巡を重ねず、人にも問わない）。結果は `worklog.md` に `前提の点検: <合う | ずれる> | <依頼の原文の語と、ずれた前提を 1 文> | 案: <その前提を変える案の名前 | なし>` の 1 行で書く（1 つ目の `|` より前はこの 2 つに閉じる。後で数えるための固定の形で、機械の検査はしない）。`ずれる` なら、その前提を名指しして変える案を、上の変える案に入れる。点検で AC か依頼の読み方が変わると分かったら、それを判断ポイントにする。一括提示の遷移を書く側は、`worklog.md` に `上限到達: <requirements-round-limit | design-round-limit>` の行も書く（同じ steering で 2 回目なら、委任していても人に戻す。正本: `references/human-check-template.md` § 事前回答 3）
2. **fail-closed カウンタ**: Review Round は `reviews.md` の `## Round N` 見出しで数える。**記録がなければ上限超過扱い**とし、人間への一括提示に倒す（測る前提の義務は、測らなければ発火しない — 過去のレビューで実際に起きたこと）。Round の判定を決めた後に `worklog.md` へ `gate結果:` 行も 1 行足す（正本: `references/subagent-dispatch.md` § Subagent Return Output Contract）
   - **カウントの起点**: 上限は「直近の human check 到達（承認または一括提示）から数えたエピソード内」に適用する。human check を跨いだ再入場（承認後の amendment 等）では `## Round 1（re-entry: <直前の human check evidence ID または日付>）` として新しい連番を開始してよい。**数え直しの根拠（直前の human check）を見出しに書けない数え直しは上限回避と見なし、上限超過扱いにする**
3. **差分スコープ**: 再入レビューは **amendment の差分（処置箇所と変えた節）だけをレビューする**。**通過済みの未変更節への新規指摘は advisory**（新情報の根拠が示せる場合のみ、reviewer が `blocking: yes` で返せる。gate を実行する側はその根拠を reviews.md に写す）
   - **再入で読む範囲**: 再入レビュー（requirements・design とも、同じ gate・同じエピソード〔直近の human check より後〕で、前回 Round が `changes_requested` で、その blocking を処置してから起動する Round。回数は問わない。human check をまたいだ Round〔見出しの番号を数え直したかを問わない〕と、前回 Round が `changes_requested` でない Round〔build から `design_detail_only` で戻ったときなど〕は含めない）で reviewer が読むのは、前回 Round の blocking ごとの処置箇所、変えた節、それらが名指しする実コード（変える関数・その呼び出し元・同じ入力を読む別の実装・それを固定するテストと文書）だけにする。`agents/gdd-planning-reviewer.md` の観点レーンの「レーンごとに最低 1 回は実測」は再入レビューには当てない（Round 1 で当て済み）。advisory もこの範囲の中で見つけたものだけを報告する。1 枚に前回 Round の blocking の一覧が無いときは、Round 1 と同じ範囲で見る。処置の `伝播:` に挙げた節は「変えた節」に含み、`根拠:` が指す場所は「名指しする実コード」に含む。変えた節が引く AC を参照するほかの節への波及は、再入では見ない（限界。`伝播:` で処置した側が直す。範囲を広げる変更は、同じ入力で呼び出しの回数・時間・判定・advisory を比べる A/B を付けてから入れる）
   - **再入の前の処置は blocking だけ**: 前回 Round の advisory を再入の前に反映すると、書き換えた節が再入の範囲に入る。advisory の反映は、最後の Round の後にまとめる。Why: 2026-10-06 に調べると、design の再入レビューは、呼び出しの回数も時間も Round 1 とほぼ変わらなかった。reviewer の時間はモデルの出力量で決まり、出力量は呼び出しの回数とともに増える（1 回あたりの量は effort で決まる）。同じ日の design-gating では、Round 1 の処置で少数の blocking と一緒に多数の advisory を反映して詳細設計を書き直し、再入の範囲が詳細設計の全体になった
4. **記録分離**: **requirements.md にレビュー記録・処置結果を積まない**。指摘・判定・処置はすべて `.steering/<task>/reviews.md`（追記専用）へ書く。gate が読むのは**最新ラウンド分だけを読む**（過去ラウンドは処置済みの履歴であり、再読して新指摘の種にしない）
5. **行数の目安**: requirements.md（standard）は **300 行**以内。`wc -l` で実測し、超えていたら承認判断に効かない記述から削る（削り先が無いほど承認事項が多い場合はスコープ分割を人間へ提案する）

### reviews.md の形式

```markdown
## Round 1（YYYY-MM-DD / reviewer: gdd-planning-reviewer / 所要: <分> 分・呼び出し <回数か 不明> 回）
<!-- human check 跨ぎの再入場では: ## Round 1（YYYY-MM-DD / re-entry: human-check-YYYYMMDD-NN / reviewer: ...） -->
- 判定: approved | changes_requested | timeout（timeout は `subagent-dispatch.md` § Reviewer Input and Time Budget）
- blocking: <指摘と、AC の意味・スコープ・承認ポイント・安全境界のどれに影響するか。無ければ「なし」>
- advisory: <blocking 要件を満たさない指摘。gate を実行する側が `blocking: yes` から下げたものには `（gate が下げた: <理由か規則の場所>）` を添える。無ければ「なし」>
- 処置:
  - <blocking ID>: <どう解消したか> / 根拠: <file:line か コマンドと値 か 未測（理由）> / 伝播: <grep した語> → <直した節 か なし>
```

- `処置:` は requirements の amendment 側が、`- 処置:`（`（注記）` を挟んでよい）の見出しの下に 1 件 1 行の項目（`- `・`* `・`1. `。続きの行は書かない）で追記し、1 件ごとに `根拠:` と `伝播:` の欄を書く（書き方: `skills/gdd-requirements-amendment/SKILL.md` § レビュー指摘の処置）。Round の中でほかに `処置` で始まる行（`### 処置`・`- 処置の確認:`・`- 処置案:` など）を書かない。処置は Round の最後の塊にし、見出しの後ろ（ファイルの終わりまで。fence の中も）には処置の見出しと項目だけを書く（備考・再入判定・人の回答・別の `##` は処置の前か worklog.md に書く）。requirements の再入の reviewer を起動する前の `scripts/lint-plan-consistency.py --entry requirements-reentry` が、最新 Round に処置が無い・見出しや項目の形が違う・欄が無い（値は解析しない）なら ERROR にする。design の再入の処置はこの検査の外。前の形の Round が最新のまま進行中のタスクは、処置の項目に欄を足し、処置より後ろの行を処置の前か worklog.md に移してから起動する（この追記と移動は Round 節の書き換えに数えない）
- 同一 gate 実行で複数 reviewer（例: planning + security）を起動した場合は **1 つの Round にまとめ**、`reviewer:` に併記する（reviewer ごとに Round を分けると 2 reviewer で即上限到達になるため分けない）。requirements-gating で design の観点の組も起動したときは、`reviewer: gdd-planning-reviewer（requirements）・gdd-planning-reviewer（design）・gdd-security-reviewer` のように観点を括弧で書き、`所要:` も `requirements <分> 分・呼び出し <回数> 回、design <分> 分・呼び出し <回数> 回、security <分> 分・呼び出し <回数> 回` と reviewer ごとに書く。blocking と advisory の各項目の先頭には、出した reviewer の観点（`[requirements]`・`[design]`・`[security]`）を書く。requirements-gating の再入で起動するのは、前回 Round で blocking を出した reviewer だけにする。ただし、処置で `design.md` を変えたら design の観点の planning reviewer も、`requirements.md` を変えたら requirements の観点の planning reviewer も起動する（どちらも、起動していなかったものを除く）
- 「追記専用」は **Round 節の削除・書き換えをしない**という意味。処置行を該当 Round 節の末尾に足すのは追記に含まれる

## Steps

1. `requirements.md` と `design.md` を読む。`adr.md` があれば、既に確定した重要判断や却下済み代替案も補助コンテキストとして確認する。`reviews.md` があれば最新ラウンド分だけを読み、Round 数を数える（上記ループ契約 1-2）。
2. 節見出しが揃っていることを確認する。必須節は `references/requirements-template.md` の「requirements.md セクション一覧」（常設 11 節 + 該当する条件付き節）が正本。`Task Size` 別の最小構成も同ファイルに従う。欠けている節は見出しを足してから進める（中身の網羅性はここで採点しない）。
3. `references/reviewer-selection.md` に従って applicable reviewer を選び、`Planning Reviewer Selection` を `state.md` に記録する。
   - `gdd-planning-reviewer` は必ず `selected`。design の観点の組（`gdd-planning-reviewer（design の観点）` と `gdd-security-reviewer`）も、`reviewer-selection.md` § Gate Rules § `gdd-requirements-gating` の条件で選んで記録する
   - reason は requirements/design の節、AC、対象論点など selection 根拠が追える粒度にする
4. reviewer 起動前に `Requirements Review Status=in_review | evidence: <review-start-id> | updated_by: gdd-requirements-gating | updated_at: <timestamp>`、`Design Review Status=pending | evidence: none | updated_by: gdd-requirements-gating | updated_at: <timestamp>`、`Human Check Status=pending | evidence: none | updated_by: gdd-requirements-gating | updated_at: <timestamp>`、`Resume From=gdd-requirements-gating` を永続化する。
4a. reviewer を起動する前に、提出前の照合を 1 回行う。`gate-driven-development:gdd-requirements-precheck`（`agents/gdd-requirements-precheck.md`。Sonnet・high・read-only。起動時に `model` を渡さない）に、`requirements.md`・`design.md` のパス（quick (express) では `requirements.md` だけ）と worktree のパスを渡す。再入では、加えて `reviews.md` のパスを渡し、最新 Round の blocking の処置の検証（定義の項目 0）をさせる
   - 返ってきた表を `.steering/<task>/review-input/precheck-round-<N>.md` にそのまま書く（`<N>` はこれから記録する Round の番号）
   - `ng` の行を 1 件ずつ、根拠の `path:line` を自分で読んで確かめる。合っていた `ng` は、reviewer を起動する前に `requirements.md`・`design.md` に反映する。誤りだった `ng` は反映しない。再入では、反映した 1 件ごとに、最新 Round の `- 処置:` の下に `根拠:`・`伝播:` の欄つきの項目を追記する（blocking ID の代わりに `照合-<行の #>` と書く）。こうすると、反映した節が再入の 1 枚の「変えた節」に入り、reviewer が見る
   - 照合の表と結果は reviewer に渡さない（reviewer の入力は Step 5 の 1 枚だけ）
   - `worklog.md` に `照合: Round <N> ng <n>・反映 <n>・不採用 <n>` の 1 行を書く。照合の agent が起動できない・返らないときは、`照合: unavailable（理由）` と書いて Step 5 に進む（照合は reviewer の代わりではないので、無くても Round は止めない）
   - 照合で直しても、Round の数え方と Round 上限は変わらない
4b. **時間の目安**: HITL までの時間を、`state.md` の `Started At`（着手の時刻）、`worklog.md` の最後の `要件確認: 回答 <時刻>`、`request.md` に時刻つきで足した最後のユーザーの返事（human check・要件確認・一括提示への返答。作業中の質問は数えない）、事前回答の委任で一括提示の答えを適用したときに（行き先によらず）`worklog.md` に書く `要件ゲート再開: <ISO 8601>` のうち、いちばん遅い時刻から測る（人の返事を待った時間を入れない。human check への返事や差し戻しの後に戻った Round も、その返事から測り直す）。Round 1 の初回の起動の後は、reviewer を起動する前、Step 7 の 1 点目で blocking を処置する前、`references/subagent-dispatch.md` § Reviewer Input and Time Budget の「超過・無応答のとき」の再実行の前ごとに経過を確かめ、20 分を超えていたら処置（§ AI が閉じる blocking を除く）も新しい起動もせず、Round 上限到達と同じ扱い（Step 7 の 2 点目）で、残る blocking と途中の結果を人に見せる。Round 1 が返らないまま打ち切ったときは、一括提示に `Round 1: 未完（timeout）` と書く。2026-11-12 にユーザーが「HITLまで1hは長い」と言った（計画が 1 本で約 58 分かかり、表示の前にセッションが終わった件）
4c. **範囲の狭めの検査**: requirements の観点の reviewer の 1 枚に、`request-crosscheck.md` の `原文だけでは決まらない` の行と、`worklog.md` のその固定行（行き先）を写す。要件を固める確認で仮決定を添えた `既存とぶつかる` の行（`requirements.md` の § ズレ確認 の `→ 仮決定:` の行）があれば、それも写す。reviewer は、原文の語が指す範囲の一部に絞った `具体化`（`references/brainstorming-steps.md` 9 の (5)）と、依頼を既存に合わせて狭めた `既存とぶつかる` の仮決定（既存側がユーザーの決めた規則・方針で、決定の記録の場所〔種類と条件は `references/brainstorming-steps.md` の要件を固める確認。`記録の場所: なし` は添えたものに数えない〕を添えた仮決定〔`references/common-guardrails.md` § 選ぶときの基準 0〕を除く）を blocking にする。human check の前に、要件の深掘りの不足（AI が質問せずに範囲を狭めた仮決定）を止めるためである
5. selected reviewer だけを、`references/subagent-dispatch.md` § Reviewer Input and Time Budget の入力（1 枚。上記「精度の第一原則」の blocking の決め方と、再入時は「レビューループの契約」の差分スコープを含む）・時間上限でバックグラウンドで起動する。design の観点の組を選んだときは、requirements の観点の reviewer と同時に起動し（reviewer ごとに 1 枚。期限 timer は同節で置ける経路でだけ reviewer ごとに置く）、全部が返ってから 1 つの Round に記録する。design の観点の組の reviewer が同節の「超過・無応答のとき」の再実行でも返らなければ、`所要:` のその reviewer を `timeout` と書き、Round の判定は残りの reviewer の結果で決める（design の観点は design-gating がもう一度見る）。完了をアイドルで待たない: 待ち時間に HITL draft の組み立てと requirements.md の行数実測・削減を先に進める（2026-08-31 に調べると、reviewer を待つだけのアイドルと反映の直列化が、HITL に着くまでの時間の大きな部分を占めていた）。
   - 重要な意思決定や却下した代替案が固まった場合は、任意で active worktree 側 `.steering/.../adr.md` を作成または更新してよい
6. reviewer 結果を blocking / advisory に分類し、`reviews.md` に Round として記録する。
   - 分け方は § 精度の第一原則 のとおり（reviewer の `blocking:` 欄に従う）。advisory は、内容が有用でも changes_requested の理由にしない
   - advisory は HITL 提示後の承認待ち時間中に反映してよい。条件は反映が承認ポイントを変えないこと。変える場合は Planning Interrupt Decision Menu の 1（HITL 再生成）で扱う
7. blocking が残る場合:
   - Round 上限内（再入前）なら、先に Step 4b の経過を確かめ（超えていたら下の 2 点目に進む）、`Requirements Review Status=changes_requested | evidence: <requirements-review-id> | ...` と `Resume From=gdd-requirements-gating` / `Next Action=gdd-requirements-gating` を記録し、`gdd-requirements-amendment` で blocking だけを処置してから再入する（**自律修正**: ユーザーに質問して止まらず AI が修正する。AI だけでは解決できない policy-level の指摘は `Human Check Questions` に集約する）。要件の目的・前提・スコープを再壁打ちする必要がある場合だけ `Resume From=gdd-brainstorming` へ戻す
   - Round 上限到達（または `reviews.md` に Round 記録が無い）なら、先に § AI が閉じる blocking に当たるものを閉じる。残る blocking がそれだけなら Step 8 に進む。人に出すものが残れば、それを一覧で人間へ一括提示する。修正の案には、直した後の文面（AC の文・節の文）を書く（§ 一括提示への返答 の 1 行目で、そのまま反映できるようにする）。`Requirements Review Status=changes_requested` のまま `Resume From=human-check-waiting` / `Next Action=human-check-waiting` / `Route In Progress=none` を記録し、`Human Check Questions` に「blocking 残指摘の扱い」として accept as known risk / 修正 / 差し戻しに、原因の決定・前提を変える案を加えた選択肢を出し（比べ方は § レビューループの契約 の 1）、`human-check-waiting` で止める（遷移の正本: `references/state-machine.md` § 状態遷移一覧）。返答例は案の名前で書く（返答の扱いは § 一括提示への返答）
8. blocking が無い場合、human-check 前の最終確認として **Spec Self-Review Checklist**（後述）を通してから:
   - 一括提示で表示した文面の採用か accept as known risk が選ばれたら、ここへ合流する（文面の採用は § 一括提示への返答 の 1 行目の反映の後。accept と同じく再度の HITL は出さない）: accept された指摘を `reviews.md` に `accepted-as-known-risk` として記録して以下の approved 遷移へ進む（同じ HITL で承認ポイントも回答済みのため再度の HITL は出さない）
   - `Requirements Review Status=approved | evidence: <requirements-review-id> | updated_by: gdd-requirements-gating | updated_at: <timestamp>`
   - `Design Review Status=pending | evidence: none | updated_by: gdd-requirements-gating | updated_at: <timestamp>`
   - `Human Check Status=pending | evidence: none | updated_by: gdd-requirements-gating | updated_at: <timestamp>`
   - `Resume From=human-check-waiting`
   - `tasklist.md` が既にある場合は `Next Action=human-check-waiting` に更新して human check に進める状態を作る。
   - **必須出力テンプレート**: 一次表示は `references/human-check-template-compact.md`（個別ルールの正本は `references/human-check-template.md` § 必須ルール）をターミナルに出力し、`<gdd-hitl-fields ...>` タグと `<gdd-stop reason="human-check-waiting">` マーカー、その後の `## 👤 次にすること` を必ず含めて停止する。マーカーがないと autonomous continuation が停止しない。

## Express

`quick (express)` も、brainstorming の後にこの gate を同じターンで通ってから human check で止まる。上の Steps との違いは次だけで、Round 上限・時間上限・再入・`reviews.md` の記録はそのまま当てる。

- Step 1・2: 読むのは `requirements.md` だけ（`design.md` は作らない）。節と Summary Brief の欄名は `references/requirements-template-express.md` を正とし、standard の常設 11 節を足さない。起動前の `lint-plan-consistency.py --entry requirements` は express でも回す
- Step 3・5: 起動するのは `gdd-planning-reviewer`（requirements の観点）と、`references/reviewer-selection.md` § Gate Rules § `gdd-requirements-gating` の express の条件に当たる `gdd-security-reviewer` だけ（渡す 1 枚と記録は同節）。design の観点の組は、同 § Gate Rules § `gdd-requirements-gating` の (1) で外れる（express の経路に design-gating が無い）。reviewer は、express の条件（`references/task-sizing.md` § 判定基準 の quick (express) の 4 条件と、テンプレートの § Promotion Rules）を外れていれば blocking を出す
- Step 4: `Design Review Status=pending | evidence: none`。Step 4a の提出前の照合には `requirements.md` だけを渡す
- Step 8: `Requirements Review Status=approved` と、同じ evidence で `Design Review Status=approved` を書く（design.md が無いので design の審査は無い）。承認の後は今どおり `gdd-test-driven-development` に進む
- Express の条件を外れた blocking の処置は、`references/task-sizing.md` § Express 昇格条件 の昇格である。昇格の後のこの gate は Round を数え直さず再入として数える（上限を避ける手段にしない）。再入で起動するのは前回 blocking を出した reviewer だけなので design の観点の組は起動しない
- human check で「一部変更」の返答が範囲（Scope・Non-goals）・Files・`## Implementation Policy` のどれかを変えたら、再提示の前にこの gate をもう 1 Round 回す（express の条件の確認を含む）。この Round は、§ レビューループの契約 3 の再入（前回 Round が `changes_requested`）には当たらないので、初回と同じ扱いにする（lint は `--entry requirements`、reviewer は全範囲を読む）。ただし human check の提示は承認でも一括提示でもないので Round の起点を戻さず、同じエピソードの Round として契約 1 の上限に数える。上限に当たっていたら、回さずに残る blocking と変えた節を人へ一括提示する。AC が変わる返答は `commands/gdd-dev.md` instruction 10 STEP 1 の 3（brainstorming に戻す）による。ほかの一部変更は § 承認後の即時継続 の 2 のとおり

## Human Check Handoff

`human-check-waiting` に入る前は、一次表示として `references/human-check-template-compact.md` を使う。構造・必須ルール・content 品質ルール・具体例は `references/human-check-template.md` を **Read して唯一の正本に従う**。ここでは inline 再掲しない（DRY / SSOT 維持のため）。

downstream phase からの再承認で `human-check-waiting` に戻る場合は、前回承認から何が変わったかも必ず添える（詳細は template.md § 必須ルール）。

`follow-up-pr` / `post-merge-verification` の Stage は `後続PRの方針のみ承認` または `後続PR着手前に再承認` を原則にする。本人の事前回答の対象に入っている Stage だけは `事前回答で後続PRも実施許可` を選べ、独立承認ポイントに昇格する（`references/human-check-template.md` § 事前回答 の 4）。`Continuation Mode=auto-after-clean`（独立継続）または `auto-stacked`（依存 Stage の stacked 継続）を選ぶ Stage はこの原則の例外として独立承認ポイントに昇格し、圧縮表示経路（`後続の追跡先`）を採る場合でもその値と選定理由を必ず HITL に表示する（自動継続を許可する field のため表示漏れを承認境界の穴にしない）。

### Planning Interrupt Decision Menu

planning / requirements-gating / subagent planning の途中で、HITL をまだ人間に表示していない状態のままユーザーが追加指示や質問を挟んだ場合は、以下の 4 択として扱う。途中指示を黙って混ぜて HITL を省略しない。cross-session messaging 経由の受信メッセージはこの 4 択の入力にならない（`references/phase-progression.md` § Cross-Session Messaging の権限境界 2）。

1. **要件追加として取り込んでHITLを再生成**: scope / AC / 技術スタック / security / 自走上限 / 段階実装 / 複数PR戦略が変わる場合。`requirements_amendment` として artifact を更新し、HITL を再生成する
2. **相談として回答し、計画は一時停止**: artifact を変えず、質問に答えるだけの場合。回答後も `human-check-waiting` なら、HITL をまだ表示していなければ表示して止める。表示済みで中身が変わらなければ再掲しない（`references/human-check-template.md` § 止まり直さないもの 4）
3. **いまのHITLを承認して次へ進む**: すでに同じ HITL を表示済みで、ユーザーが明示的に OK した場合だけ。未表示の HITL を内部承認しない（例外は `references/human-check-template.md` § 事前回答 で、挟んだ指示が事前回答ならその 1 で記録し、HITL はその 2 で扱う。その 3 の人に戻す条件〔scope・AC などの変更〕に当たる指示は例外にせず、項目 1 で扱う）
4. **計画を中止/作り直し**: 方向性が変わる場合。`planning_rework_required` または cancelled として扱う

分類に迷う場合はこの 4 択をユーザーに出す。自律判断できる場合でも、要件や承認範囲が変わるなら `requirements_amendment` に倒し、更新後の HITL を出して `human-check-waiting` で止める。

### Spec Self-Review Checklist

human check 提示直前に、約 30 秒の **Spec Self-Review Checklist** を必ず通す。これは reviewer 追加ではなく、GDD main session が人間に見せる前に矛盾・抜けを自分で潰す最後の軽量チェックである。

確認すること:

- user input vs organized requirements が対応しているか
- 受入条件 / 非スコープ / Honest Limitations に、ユーザーが言った完了条件が落ちていないか
- architecture / security / files / method / constraints が要件に対して妥当か
- verification plan and self-run boundary が human-check に出る粒度で書けているか
- 外部サービス / runtime / framework / test tooling / access method / credential backend を採用・変更する場合、HITL に `実装技術スタック` が出ているか
- 外部形式に依存する AC（API 応答・通知 payload・Webhook・ログ書式などの欄の位置や値の形を前提にするもの）が、`references/brainstorming-steps.md` § 8a の外部形式の実測で作った fixture を根拠にしているか。実測できていないものは、AC に「未測」と理由が書かれ、取得手段が `Human Check Questions` に出ているか
- Option A / B / C、P0 / P1 / P2 のようなラベルだけが出ておらず、意味が説明されているか（`Option B とは？` と聞かれる状態で出さない）
- 複数PR、後続PR、post-merge verification、または段階実装でPRをまたぐ場合、PR の分け方（単一PR / 複数PR / 後続PR着手前に再承認）が承認ポイントとして同じ HITL 内で比較されているか
- `Post-PR Completion Scope` がある場合、`マージして再学習まで` 等のユーザー完了条件を `PR 作成までに丸めない` 表示になっているか

未達があれば `human-check-waiting` に進めない。requirements / design skeleton / human-check draft を修正してから、再度 requirements gating に戻る。

### AI が閉じる blocking

Round 上限・Step 4b の時間の目安に当たった時点で残った blocking（requirements・design とも）と、`gdd-design-gating` で承認済みの AC に出た blocking のうち、処置が次のどちらかだけで済むものは、人に出さず AI が閉じる。ただし、接地条件がスコープ・承認ポイント・安全境界のもの、`計測:` を緩める直し（確かめる対象を減らす、合格の閾値を下げる、計測を消す）、AC の本文を変える直し、当たるかで迷うものは当たらず、今どおり人に出す。
1. 計測の締め直し: 同じ AC の `計測:` 欄だけを、確かめ方を厳しくする向きに書き換える（壊れた実装を落とす計測に替える）。確かめる対象を足すのは、AC の本文がすでに述べている挙動だけで、本文のどの語を確かめるかを処置の `根拠:` に引用する。引用できない対象を足す直しは当たらない。AC の本文（挙動の文）・`根拠:`・範囲・承認ポイントは変えない
2. 任された具体化（requirements-gating だけ。design-gating の承認済みの AC には当てない）: `worklog.md` の「原文だけでは決まらない」の固定行で、行き先が `具体化（任された）` の行（`references/brainstorming-steps.md` 9 の要件を固める確認で、人が残りを推奨に任せた行）の具体化を、同じ範囲の中でさらに細かく書く。範囲を狭めない。印の無い `具体化` の行は当たらない

閉じ方は次のとおり。
- `gdd-requirements-amendment` で、その blocking だけを処置する（Round 上限の後でも、design-gating からでも、state の欄を変えずに処置する）。`reviews.md` の最新 Round の `- 処置:` に `根拠:`・`伝播:` の欄つきで書き、項目の先頭に `AI が閉じた:` と書く。Round を足さず、reviewer を回し直さない。処置の後、Step 4a の提出前の照合を、再入と同じ入力（`reviews.md` のパスを含む）で 1 回だけ起動し、項目 0 の `ng` を反映する（Round に数えない）。閉じたことにするのは、照合が閉じた blocking ごとに項目 0 の `ok` を返したときだけである。照合が起動できない・返らない、`ng` が直らない、のどれかなら、その blocking は人に出す側に戻す
- `worklog.md` に `AI が閉じた: <blocking ID の列> | 次の gate で確かめる: <AC ID の列>` の 1 行を書く。次の gate は閉じた gate で決める。requirements-gating で閉じたら `gdd-design-gating`（quick (express) は `gdd-implementation-gating`）、design-gating で閉じたら `gdd-implementation-gating`。design-gating では reviewer の 1 枚に名指しで写す（`references/subagent-dispatch.md` § Reviewer Input and Time Budget の (6)）。implementation-gating では、必ず回る `references/inline-review-checklists.md` の AC の項で確かめる（reviewer subagent を起動するときは 1 枚にも写す）。人に出す blocking が残らなければ、requirements は Steps 8 へ、design は `gdd-design-gating` の通過の手順へ進む。残れば、それだけを一括提示する。Why: 2026-11-13 のタスクで、計測の穴を人に出すたびに人は表示どおり「直す」を選び、全範囲の再レビューで約 40 分と人の待ち 2 回を使った。過去 52 件でも、human check をまたいだ全範囲の Round が 255 中 119 あった。

### 一括提示への返答

一括提示は、残った blocking をどうするかを問うもので、承認の確認ではない。`Requirements Review Status` か `Design Review Status` が `changes_requested` で `Resume From=human-check-waiting` のとき（Round 上限、Round 記録なし、時間超過）は、本人の返答と委任で採った案を、残った blocking ごとに次の表で分ける（1 つの blocking への返答は、上の行から当てて最初に当たった行で分ける）。blocking ごとの行き先が分かれたら、最も止める側に進む。止める側から順に、待つ行（下の 2 行）、差し戻し、再レビュー、文面の採用と accept である。この state から `commands/gdd-dev.md` #10 STEP 2 に入るのは、残った blocking が全部、表示した文面の採用か accept の行に当たったときだけである。採用した文面は、ほかの行に進むときも反映してから進む。委任で採った案を適用したら、行き先によらず先に `worklog.md` に `要件ゲート再開: <ISO 8601>` を書く（Step 4b の起点）。

| 返答 | 行き先 |
|---|---|
| 一括提示に直した後の文面を書いた修正の案を、文面を変えずに採る名指し（推奨の案を名前で復唱して得た肯定を含む。blocking ごとの推奨が文面つきの 1 案に決まっている提示への「推奨で」「推奨案で進めて」も、復唱せずにこの名指しとして扱う。方向だけで文面の無い案、文面に条件や変更を足した返答は当たらない） | 表示した文面をそのまま `requirements.md`・`design.md` に反映し、`reviews.md` の最新 Round の `- 処置:` に、表示した文面と反映した場所を `根拠:`・`伝播:` の欄つきで書く（返答を `request.md` に足すとき、採った案の直した後の文面を assistant の文と分かる形で引用して添え〔`references/brainstorming-steps.md` 9 の (1)〕、処置にはその引用から写す）。`worklog.md` に `表示した文面を採用: <blocking ID の列> | 次の gate で確かめる: <AC ID の列>` の 1 行を書く（名指しの渡し方は § AI が閉じる blocking と同じ）。Step 4a の提出前の照合を再入と同じ入力（`reviews.md` のパスを含む）に `request.md` のパスを足して 1 回だけ起動し（Round に数えない）、項目 0 の `ng`（(d) の字句の食い違いを含む）は表示した文面に合わせる向きで直す（文面そのものを変える直しが要るなら、この行に当たらないものとして下の行で分け直す）。承認に進むのは、照合が採用した blocking ごとに (d) の `ok` を返したときだけである。照合が起動できない・返らない（Step 4a の `照合: unavailable` を含む）、(d) の行が無い、`ng` が直らない、のどれかなら、待つ行として扱い、表示した文面と反映先を人に見せて待つ。AC が変わっても `planning_rework_required` にせず、要件の再レビューも再度の HITL も出さない。requirements は Steps 8 の approved を書き、同じターンで #10 STEP 2 へ。design は `gdd-design-gating` の通過の手順へ |
| accept as known risk の名指し（時間超過では「レビュー無しで承認」） | `reviews.md` に `accepted-as-known-risk` を記録する。requirements は Steps 8 の approved を書き、再度の HITL を出さず同じターンで #10 STEP 2 へ。design は `gdd-design-gating` の通過の手順へ |
| 差し戻しの名指し。修正や原因の決定を変える案のうち、AC・依頼の読み方・前提・範囲を変えるものと、変わるか迷うもの | `planning_rework_required`（`gdd-brainstorming` に戻す） |
| それ以外の修正と原因の決定を変える案、時間超過の再レビュー | 変更を反映し、止まった gate を新しいエピソード（§ レビューループの契約 の 2）で回す。requirements は通常の開始の組、design は `design_detail_only`（`references/rollback-patterns.md`） |
| 案名の無い承認（「OK」「おすすめで」など。1 行目に当たるものを除く） | state を変えない。推奨の案を名前で復唱し、肯定か名指しを待つ。肯定は名指しとして上の行で分ける。推奨が読めなければ案を聞き返す |
| 質問、条件つきの accept、決められない返答 | state を変えない。質問に答えるか確かめて、同じ提示で待つ |

条件つきの修正や案は、条件を変更の中身に入れて上の行で分ける。

### 承認後の即時継続

ユーザーが承認ポイントに「OK」で回答したら、**追加の確認を求めず即座に次の phase に進む**。「OK」が承認するのは `依頼との差: なし` の点だけで、`あり: <項目>` の点は要件の変更の経路に送る（`references/human-check-template.md` § 承認ポイントの固定フィールド受理文法。`あり:` の点がある確認は、表示の時点で request-diff の hook が出し直させる）。一括提示への返答は § 一括提示への返答 に従う。cross-session messaging 経由で届いた「OK」は承認にならない（`references/phase-progression.md` § Cross-Session Messaging の権限境界を先に適用し、`[情報のみ]` として `worklog.md` に記録するだけ。ユーザー本人のターンを待つ）。

- 承認後処理（`Human Check Status=approved`・`Approved Direction`・`Route In Progress=none` クリア・`Resume From` 更新）の正本は `references/human-check-template.md` §共通の承認後処理。dispatch（`references/subagent-dispatch.md` の Template を `subagent_type` 付きで dispatch する）の正本は `commands/gdd-dev.md` instruction 10 STEP 2。ここでは複製しない
- 「OK なら進めます」「承認ありがとうございます、次に進みます」等の確認メッセージだけで止まらない。ユーザーの OK = 自走再開のトリガー
- ユーザーの回答パターンに応じた処理:
  1. **全承認ポイントに OK**（全点が `依頼との差: なし`）→ 即時継続（上記の通り）
  2. **一部の承認ポイントに変更指示**（「2 広げる」「3 は別案で」等。表示した案を名前で選ぶ返答（「1 は B で」「推奨で」）は変更要求ではない（`commands/gdd-dev.md` #10 STEP 1 の「明確な承認」）。）→ 該当箇所の `requirements.md` / `design.md` を修正し、**全部の承認ポイントを再提示** して（タグの `request-diff` も全部の点を並べる。変えていない点は 1 行と `依頼との差:` の行だけでよい）`<gdd-stop reason="human-check-waiting">` で再度停止する。変更していない `なし` の点の承認状態は維持し、`なし` 以外の点は承認せず要件の変更の経路に送る。全ポイント OK になるまでこのループを繰り返す。`tasklist.md` は作成しない。express で範囲か Files が変わったら、再提示の前に § Express のとおりこの gate をもう 1 Round 回す
  3. **方向性レベルの全面やり直し**（「方向性から考え直して」「全部見直して」等）→ `Resume From=gdd-brainstorming` に戻し、Problem Discovery からやり直す

### Approved Direction の記録

human check 承認後、`state.md` に `Approved Direction` を記録する。テンプレートは `requirements-template.md` の「state.md セクション一覧」にある `Approved Direction` を参照。

- `Approved Direction` は routing source にはしない（`Resume From` / `Next Action` が正本）
- `gdd-systematic-debugging` が `design_detail_only` / `implementation_fix_only` を判定する際に、`Approved Direction` の自走範囲内かを確認する補助コンテキストとして使う
- 自走範囲内の変更であれば `human_recheck_required` に escalate せず、`design_detail_only` で閉じてよい
- 人間が自走範囲または自走上限を制限した場合は、その制限を `Approved Direction` に明記し、制限を超える変更は `human_recheck_required` に escalate する
- `Approved Direction` に `Post-PR Completion Scope` がある場合、自走上限を PR 作成までへ自動降格しない。PR 作成は中間地点であり、明示承認済みの post-PR scope は `gdd-completion-check` の Post-PR Scope Continuation が追跡する。未承認の merge / deploy / apply / AWS write が必要になった場合は scope を消さず、対象操作・影響範囲・ロールバックを示して `<gdd-stop reason="blocked">` で停止する
