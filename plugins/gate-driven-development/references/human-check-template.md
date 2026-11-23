# human-check テンプレート（正本）

`human-check-waiting` 停止時に出力するテンプレートの **唯一の正本**。構造・適用ルール・content 品質ルールを全てここに集約する。skill / reference 側から参照する際は「このファイルを Read して従う」と pointer で書き、構造を inline で再掲しない（DRY / SSOT 維持のため）。

## GDD Complexity Budget

HITL を出す前に GDD Complexity Budget を確認する。内部用語数、HITL行数、承認ポイント数、正本重複、似たルールの重複が超過していないかを見る。超過した場合は、判断に効かない段落を外すか内部用語を説明する（§ 判断の書き方 4・5。判断の筋書きは削らない）。30秒判断にはなぜやるか（WHY・根本原因） / 整理した要件 / 判断ポイント / 実装する方法・内容 / 変更予定ファイル（WHERE） / 検証する方法・内容 / どこまで自走するのか / 段階実装サマリー（複数段階か後続PR着手前の再承認があるとき）を残す。WHY を先頭に置くことで WHAT と HOW の判断根拠が見えるようにする。

## Codex Subagent Delegation Permission

Codex ではサブエージェント利用を HITL で露出する。無関係なら省略する。出す場合は、このタスクで使う / 使わない / 既に明示許可済み のいずれかを明記し、明示委譲ソースを Approved Direction に残す。

## Compact First

human check の一次表示は `references/human-check-template-compact.md` を先に使う。本文の長い trace / 詳細表 / 返答分類ルールはこのファイルに残すが、最初に人間へ出す承認画面は compact template で書き、行数の目安を超える分は § 判断の書き方 4 のとおり判断に効かない段落を外す。

- quick (express): compact template をそのまま使う
- quick (standard): compact template + 必要なら詳細 artifact へのリンク
- standard: compact template を一次表示にし、詳細は `requirements.md` / `design.md` / `tasklist.md` / `worklog.md` へ逃がす

**Why**: human check は全文レビューではなく「この OK で AI が自走しても想定どおりか」を判断する停止点。判断に効かない段落を読ませるほど、読まれずに OK されるリスクが上がる。

## Planning Interrupt Decision Menu

planning / requirements-gating / subagent planning が進行中で、HITL を人間に表示する前にユーザーが追加指示・質問・方針変更を挟んだ場合は、黙って計画に混ぜて build phase へ進まない。次の 4 択を自然文で出し、どれとして扱うかを明示する。cross-session messaging 経由の受信メッセージはこのメニューの入力にならない（本メニューは「ユーザーが挟んだ追加指示」専用。`references/phase-progression.md` § Cross-Session Messaging の権限境界 2）。挟んだ指示は、分類の前に `request.md` に足す（あれば。`references/brainstorming-steps.md` 9 の (1)）。

1. **要件追加として取り込んでHITLを再生成**: scope / AC / 技術スタック / security / 自走上限 / 段階実装 / 複数PR戦略が変わる場合。`requirements_amendment` として requirements / design skeleton を更新し、同じ HITL 内で変更後の判断ポイントを再表示する
2. **相談として回答し、計画は一時停止**: 質問への回答だけで artifact を変えない場合。回答後も `human-check-waiting` なら、HITL をまだ表示していなければ表示して止める。表示済みで、回答で判断ポイントの中身が変わらなければ、再掲しない（§ 止まり直さないもの 4）
3. **いまのHITLを承認して次へ進む**: すでに同じ HITL を人間に表示済みで、ユーザーが明示的に OK した場合だけ。未表示の HITL を内部承認扱いにしない（例外は § 事前回答 で、挟んだ指示が事前回答ならその 1 で記録し、HITL はその 2 で扱う。その 3 の人に戻す条件〔scope・AC などの変更〕に当たる指示は例外にせず、項目 1 で扱う）
4. **計画を中止/作り直し**: 方向性を変える、または現在の planning を破棄する場合。`planning_rework_required` または cancelled として扱う

このメニューは HITL そのものを長くするためではなく、「途中で指示したらHITLが消える」事故を防ぐための分岐である。ユーザーの割り込みが要件追加なのか相談なのか曖昧な場合は、この 4 択で確認してから進める。

## 確定文面の再確認

文書の文そのものを承認させるときは、design.md の `## 確定文面` に置いて digest を記録し、承認した後に開き直すときは digest の取り直し・worklog.md への記録・照合のやり直しを行う。書き方・道具・手順の正本は `references/confirmed-text.md`。

---

## 出力テンプレート

`<...>` を実際の内容で置換して出力する。出力後は必ず `<gdd-stop reason="human-check-waiting">` マーカーとその後の `## 👤 次にすること` を付けて停止する。

### 一次表示の原則

HITL は全文レビューではなく、**この OK で AI が自走しても想定どおりの結果になりそうか**を人間が判断する停止点である。一次表示に中身を書くのは、冒頭の前置き 3 行（依頼の原文・なぜやるか〔1〕の要点・現在地。§ 判断の書き方 2）と、判断ポイント（7）と OK の範囲（6）と、複数段階のときの段階実装サマリー（8）だけである。2〜5（整理した要件・実装する方法・変更予定ファイル・検証する方法）と 1 の詳しい根拠は `requirements.md` などに書き、一次表示ではその場所を指す 1 行（`human-check-template-compact.md` の `詳細:`）にする。人が詳細を開くのは判断ポイントの材料を確かめたいときで、そのとき `requirements.md` の中で WHY が WHAT と HOW の判断根拠として先に読めるようにする（2026-11-12、依頼「判断ポイントと OK の範囲だけにし、詳細は requirements.md へ回す」。見出しを全部残すと、必須の見出しだけで行数の目安を超えていた）。

1. **なぜやるか（WHY・根本原因）**: 解決する問題・根本原因・この変更が必要な理由。WHY が先にあることで WHAT と HOW の判断根拠が見える
2. **整理した要件**: ユーザー入力を AI がどう解釈したか。変換・延期・非スコープ化した完了条件があればここで見えるようにする。整理した要件の各行に、対応する依頼の原文を `原文: …` として並べる（`request-crosscheck.md` の要件の表の原文。`#` は付けない〔表に対応する行が無ければ `request.md` の発言。hook の節があれば、その中のユーザーの発言と、節の下に時刻つきで足したユーザーの発言。`見直し` で始まる assistant の引用は除く〕。`request.md` の先頭が `<!-- gdd-request-capture:not-copied -->` のときは、初めの依頼の原文が無いので、§ ズレ確認 に `依頼の原文: なし（<見出しの理由>）` の行を出し、依頼をユーザーに確かめる。返事は `request.md` に時刻つきで足す。main が言い換えと思っていない読み替えも、人が見つけられるようにするため）
3. **実装する方法・内容**: 採用するアーキテクチャ、技術スタック、既存実装の再利用方針（変更対象ファイルは項目 4 の WHERE に記載する）
4. **変更予定ファイル（WHERE）**: 判断に効く変更予定の実ファイルパスと変更内容の対応（全列挙は artifact の場所を指す。§ 判断の書き方 4）。`git grep` / 類似実装調査に基づく実名を記載し、placeholder（例: `src/...`）は禁止。該当なしの場合は「N/A」と根拠を1行添える
5. **検証する方法・内容**: どこで確認するか、どう確認するか、OK条件、失敗時の扱い
6. **どこまで自走するのか**: 実装完了 / PR 作成 / post-merge read-only 検証などの最大到達点と、merge / deploy / apply 等の除外
7. **判断ポイント**: 人間が今決める必要があるもの（方向性を除き 2 件以内。置くもの・書き方は § 判断の書き方）。`Option B` / `P1` のような略称は同じ HITL 内で定義する。判断ポイントごとに `相談役の推奨: Opus-1 <案> / Opus-2 <案> / 食い違い: <なし | 内容>`（2 本の割れと、main の案との食い違い）を足す（相談役の推奨。human check や Handoff を作る subagent は相談せず、この行も書かない。**相談役の返りを待って表示を止めない**: main は人に表示する同じターンで、表示の前に `gate-driven-development:gdd-opus-advisor` を、`model` を渡さず `run_in_background: true` で並行に 2 本起動し、返りを待たずに確認を表示する。表示の時点のこの行は `相談役の推奨: 確認中（届いたら全文を出し直す）` と書く。起動した相談役が全部返ったら（完了通知で起きたターン。まだ動いている相談役があるターンでは何も出し直さず、`human-check-waiting` の marker を付けた発言を出さずに終える）、§ 止まり直さないもの 2 に当たるときは出し直さない。それ以外は、前置き 3 行（§ 判断の書き方 2）と、判断ポイントごとに何を決める点かを中身の言葉で書き、この行に判断ポイントの番号ごとの推奨を書いた確認の全文（判断ポイントごとの `依頼との差:` と、マーカー直前の `request-diff` つきのタグを含む）を出し直し、同じ `<gdd-stop reason="human-check-waiting">` と `## 👤 次にすること` で止まり直す。推奨の行だけを追記として出さない（承認の書き込みを検査する hook は、最後の `human-check-waiting` の発言を直前の提示として読み、マーカー直前のタグが無いと止める）。推奨を受けて main が推奨案を変える・案に足すときは、§ 判断の書き方 8 のとおり推奨案の文に書き込んでから出し直す。出し直したら `human-check-draft.md` も書き直すが、相談役は起動し直さない。人が先に返事をしたら、まだ動いている相談役を `TaskStop` で止めて返事を扱い（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running` 以外の結果〔拒否など〕で返っても繰り返さず、そのまま返事を扱う。その相談役は待ちに残るので、返事を扱った後に loop state を消す停止で止まるときは、`references/subagent-dispatch.md` の「セッションが終わって background の dispatch が返らなかったとき」のとおり `clarification-needed` で人に渡す）、全文を出し直さない。セッションが終わって返らなかった相談役は起動し直さない（人が意見を求めたら、そのとき 1 回相談する）。相談役には期限 timer を置かない（`references/subagent-dispatch.md` § Reviewer Input and Time Budget の時間上限の対象外）。2 本に渡す材料は同じにし、要約せずに場所で渡す。渡すのは、人に表示する確認の文面をそのまま `.steering/<task>/human-check-draft.md` に書いたファイルのパスと、steering のパスと、依頼の原文（`request.md`。無いときと、先頭が `<!-- gdd-request-capture:not-copied -->` のときは、その旨の 1 行）のパスだけである。main が判断ポイントや案を書き直した文は渡さない。確認の中の選択肢と推奨は参考で、相談役は依頼の原文から、そもそもどうあるべきかを先に問う〔2026-11-12 にユーザーが「A/Bだと狭すぎないか？」「サブエージェントにサマリーせずにそれなりにまるごと渡して判断させた方がいいのでは？」と言った。それまでは、main が書き出した判断ポイントと案を渡していた〕。相談ごとの観点や、前回の相談の推奨は足さない〔観点は定義の本文のもの〕。2 本が割れた点は、main が repo の事実を確かめてから推す側を決め、決めきれなければ両方を載せて人に委ねる。順序は § 事前回答 2・3 → 人に表示するときだけこの相談、とする。定義が読み込まれていないときの代わりの経路は `references/autonomy.md` 判断の手順 1 と同じ。同じ材料で `gdd-opus-advisor` の相談を 1 本済ませていれば〔§ 事前回答の委任先 `opus` など〕その推奨を表示の時点で載せて、もう 1 本だけを起動する。委任先 `並行` で同じ材料の 2 本を済ませていれば、その 2 本を載せて起動しない〔委任先 `fable` の相談は、この 2 本に数えない〕。起動できなかった本は `Opus-2 unavailable（理由）` のように書く。根拠と費用は `references/fixed-models.md` の相談役の段落にある。推奨は材料で、承認の境界・選択肢は変えない。2026-10-03〜10-10 に人が確認への返事で「Opus／Fable の意見を聞きたい」と求めた例は 18 件〔GDD を使う 2 repo の合計。正式 GDD の repo が 9 件〕で、確認からその発話までの中央値は 204 分だった。2026-11-12 に、GDD を使う repo のタスクで、計画が終わり確認の文面もできていたのに、表示の前の相談役 2 本の返りを待つ間にセッションのプロセスが終わり、相談役も確認の表示も失われた。人が推奨を読むのは表示から時間が経ってからなので、表示を先に出し、推奨は届いたら全文を出し直して載せる）
8. **段階実装サマリー**: 複数段階か後続PR前の再承認があるときだけ、この PR でやる範囲と、後続 Stage が何を consume するか。段階が 1 つだけなら書かず、`<gdd-hitl-fields>` の `stage` を `none` にする

一次表示の行数の目安は `scripts/lib/hitl_budget.py` の `PRIMARY_SURFACE_MAX_LINES` が正本（sizing 別。ここに数値を再掲しない）。目安を超える場合は、情報を削るのではなく、詳細を `requirements.md` / `design.md` / `tasklist.md` / `worklog.md` に逃がし、HITL には「判断に必要な差分」だけを残す。

禁止:
- 何を判断すべきか曖昧な旧式見出しを使わない。特に「保護が増える/増えない」という言い方で、実装範囲・検証範囲・未確認事項を説明しない
- `P0` / `P1` / `Option B` / `S-2` を未定義のまま出さない
- 検証計画、自走上限、未確認事項、人間に戻す条件を参考欄や長い trace の末尾に埋めない
- 詳細を短くするために、要件変換・検証境界・危険操作の除外を落とさない

### 承認後の到達点

- 標準: PR 作成まで
- 外部レビュー収束: 「PR 作成 + 外部レビュー収束まで」。設定キー `PR Auto Review Convergence`（`references/operation-levels.md`）がある場合はこれを既定値として提示する。設定キーが不在の場合は「設定キー不在のため収束までは選択不可」を自走上限の提示時に併記する。多 Stage 計画では、この上限は承認済み全 Stage の PR 作成と各収束に適用される
- インフラ変更: deploy 手前まで（`terraform apply` / AWS write は別途明示承認が必要）
- 本番相当操作: `terraform apply`、AWS write、DB write、Docker push はこの human check の包括承認に含めない。承認後にアーキテクチャ選択（採用フレームワーク・access method・credential backend 等）を覆す必要が出た場合も同様に、silent に変更せず `gdd-requirements-amendment` 経由で再承認を取る
- ユーザーが「マージして再学習まで」「merge 後に検証まで」「post-merge verification / relearning まで」などを完了条件として明示した場合、その完了条件を **Post-PR Completion Scope** として残し、標準既定の `PR 作成まで` に丸めない。危険操作だけを「別途明示承認が必要な操作」に分離する

```markdown
## 🔍 確認

**依頼**: <`request.md` の初めのユーザーの発言をそのまま引用>
**なぜやるか**: <解決する問題と根本原因>
**現在地**: <済んだ工程と、返事で次に始まること>

### 30秒判断（まず見るところ）

**整理した要件**: <ユーザー入力を AI がどう整理したか。各行に `原文: …`>
**判断ポイント**: <人間が今決めること>
**実装する方法・内容**: <採用する実装方法と変更内容>
**変更予定ファイル（WHERE）**: <実ファイルパス | 変更内容 | 対応ACの行、または該当なしの理由>
**検証する方法・内容**: <どこでどう確認するか>
**どこまで自走するのか**: <実装 / PR 作成 / merge 前まで等。迷ったら確認する欄〔承認ポイント N / まだ確認できないこと など〕を括弧で添える>
**段階実装サマリー**: <複数段階 / 次PRの扱い。段階が 1 つだけなら行ごと書かない>

### 判断ポイント

非エンジニアでも `OK` の意味が分かるよう、詳細表の前に意思決定カードを必ず置く。ここには仕様のズレ・漏れを防ぐための重要判断だけを書く。

**OKで実装・検証すること**
- <今回の承認で AI が実装すること / 新しく確認すること>

**OKしても今回は対象外のこと**
- <今回 scope 外のため実装しないこと / 今回は検査だけで本番では止めないこと>
- これは**権限の話ではなく scope の話**。「merge / deploy は別承認」のような権限境界は `OKでも許可されないこと` に書き、ここには「今回の承認で発生しないこと」を書く

**根拠の母集団**（件数・実測を根拠に出す場合のみ・必須）
- <その N をどの集合から取ったか / その集合が判断対象の母集団を代表しているか>
- 代表していない場合は、結論の適用範囲をその集合に限定して書く
- 悪い例: 件数だけ書いて出所を書かない（「実測 6 件がすべて doc 整合性だった」とだけ書き、その 6 件が docs のみの PR 3 本から取られたことを書かない）
- `lint-hitl-decision-quality.py` が `件の実測` / `実測` / `件中` を検出したときに決定論で要求する。発火語のマッチなので fail-open（該当語を使わずに件数を根拠にした場合は素通りする）

**人間に決めてほしいこと**
1. <業務・安全上の判断を自然文で。例: 未知の経路は warn（警告）から始め、今すぐ止めないことでよいか>
2. <実装方針の判断を自然文で。例: 新しい検査は advisory（警告のみ）に限定し、今回は止めないことでよいか>
3. <自走上限または戻し条件>

### やること
<この変更で何を実現するか — 1-2 文>

**タスクサイズ**: <quick (express) | quick (standard) | standard> — <判定理由 1 行>
**リスクの段**: <高 | 低> — <`request-crosscheck.md` の `### リスクの段` の 1 行目と根拠の要点を写す。正本はそのファイルで、ここは写し。読めないときは `高（判定できない: <理由>）`>
**フロー**: <このサイズで通るセレモニーを 1 行>
**通過予定 gate 数**: <N gate>（<gate 名を列挙>）
**自走上限**: <今回の承認で AI が進めてよい最大到達点。値は § 自走上限の置換値>
**Post-PR Completion Scope**: <なし / マージして再学習まで / post-merge verification / relearning まで。ユーザーが明示した場合は PR 作成までに丸めない>

### 承認サマリ

非エンジニア向けに、詳細表を読まなくても `OK` の意味が分かる要約を必ず置く（行数では決めない）。

- **人間が今だけ判断すること**: <scope / AC / 技術スタック / 自走上限のうち、ズレると後戻りが大きい判断を、自走上限と、ほかに 2 件以内>
- **What と How の分離**: <何を実現するか（What）と、どう作るか（How）が分かれているか。混ざっている場合は human-check に進めない>
- **OK で許可される最大到達点**: <実装完了まで / PR 作成まで / デプロイ準備まで等。merge / deploy は含めないなら明記。`マージまで` 以上なら、マージで起動する workflow と環境（本番なら本番）も、`マージ・デプロイ・QA まで` なら QA の書き込み先も並べる>
- **PR 後も完了条件に含むこと**: <Post-PR Completion Scope がある場合だけ 1 行。例: PR が merge された後に read-only で再学習結果を確認する>
- **OKでも許可されないこと**: <merge / deploy / terraform apply / AWS write / DB write / Docker push / actual external posting など。自走上限が `マージまで`・`マージ・デプロイ・QA まで` なら、その値で許す操作は除く>
- **OK 後に AI がまず行うこと**: <design-gating / task-breakdown / RED 作成など、次アクションを 1 行>
- **迷った時の返答**: <例: `2 は変更` / `自走上限は実装完了まで` / `全面見直し`>

### 選択肢の説明

**原則**: 選択肢を増やして判断負荷を上げない（出典: `references/post-completion-pr-flow.md:11`。ただし同行の "exactly these 4 options" は completion 分岐メニュー固有の規定であり、選択肢数の根拠にはしない）。数の根拠は本節の Option A/B/C 表（3 列）に置く。

`Option B` / `P1` / `S-2` のような短いラベルだけでは承認者が判断できない。選択肢を出す場合は、同じ HITL 内で Option A / B / C の意味、採用案、採用理由、却下理由を必ず自然文で説明する。Option B だけを承認ポイントに出す、未定義の Option ラベルを出す、`Option B とは？` と聞かれる状態のまま human-check に進める、の 3 つは禁止。単一案なら Option ラベルを使わず、節ごと書かない（理由は `requirements.md` に残す）。

| 選択肢 | 何をする案か | 良い点 | 弱い点 / やらないこと | AI の仮決定 |
|---|---|---|---|---|
| Option A | <小さく直す / 個別修正だけ等、承認者が分かる言葉で説明> | <早い / 影響が小さい等> | <再発防止や測定が弱い等> | <採用 / 不採用> |
| Option B | <今回の推奨案なら、その中身を 1 行で説明。例: 既存 runner を拡張し、品質を測れる仕組みまで入れる> | <なぜ良いか> | <重くなる点 / 今回やらない点> | <採用 / 不採用> |
| Option C | <大きく作る / release gate 化する等> | <強い保証等> | <重すぎる / 運用変更が必要等> | <採用 / 不採用> |

### Multiple PR Strategy Options

複数PR、後続PR、post-merge verification、または段階実装でPRをまたぐ場合は必須。HITL には段階表だけでなく、PRをどう分けるかの選択肢を出す。単に「複数PRで進める」「このPRではここまで」と書くだけでは、人間が同じチャットで続けるべきか、マージ後に次へ進むべきか、別チャットに渡すべきか判断できない。

| 選択肢 | 何をする案か | 良い点 | 弱い点 / やらないこと | AI の仮決定 |
|---|---|---|---|---|
| 単一PR | <全部を1つのPRで進める案> | <レビューとマージが一度で済む> | <巨大PRになりやすく、戻しづらい> | <採用 / 不採用> |
| 複数PR | <安定した単位でPRを分ける案> | <レビュー・検証・rollback がしやすい> | <段階間の追跡が必要> | <採用 / 不採用> |
| 後続PR着手前に再承認 | <前のPRがmergeされた後、ローカル整理と次段階確認をしてから着手する案> | <混線しにくい。マージ後の状態から始められる> | <都度の確認が必要> | <採用 / 不採用> |

複数PR案を採用する場合は、`段階実装案` に `後続の追跡先`、`同じチャットで続けるか / 別チャットへ渡すか`、`次に進む条件 / 人間に戻す条件`、`後続PR着手前に再承認` か `事前回答で後続PRも実施許可` かを出す。後続 Stage の実装までこの OK で許可できるのは、`事前回答で後続PRも実施許可`（§ 事前回答 の対象に Stage が入っているときだけ）と、Stage Continuation（`Continuation Mode=auto-after-clean`・`auto-stacked`）だけで、どちらも独立した承認ポイントに昇格する。

### 検証計画

実装することと同じ重さで、検証することを承認者に見せる。`どこで確認するか` / `どう確認するか` / `OK条件` / `失敗時の扱い` が無い検証計画のまま human-check に進めない。

| 検証対象 | どこで確認するか | どう確認するか | OK条件 | 失敗時の扱い |
|---|---|---|---|---|
| <例: artifact ledger> | <repo / worktree / runner / 出力 artifact / 既存 test file> | <unit / contract / integration / E2E / no-post smoke / compare / score> | <何が観測できたら pass か。例: phase ごとの入力・出力・失敗理由が artifact に残る> | <自動修復 / coverage gap 記録 / human_recheck_required / blocked> |
| <例: classified unavailable artifact> | <status artifact / score artifact> | <fixture または no-post smoke で確認> | <未検証を green 扱いせず、不可理由が分類される> | <未分類なら修正して再検証。外部前提不足なら PR ready / 完了とは言わない> |

Web 画面・UI・ブラウザ操作を含む場合は、QA観点と Playwright 確認をここに含める。Playwright が実行できない場合も、`not_run` ではなく、理由・代替確認・人間に戻す条件を明示する。

Playwright fallback minimum:
- Playwright が実行不可なら、最低でも manual reproduction steps、screenshot or DOM evidence、console / network error check、対象 viewport / browser、未確認として残るリスク、人間に戻す条件を `検証計画` に出す
- screenshot or DOM evidence は「画面を見た」だけではなく、対象画面・操作・期待表示・取得時刻またはコマンドを残す
- DOM evidence の例は locator text、accessible name、URL、timestamp を含める
- console / network error check ができない場合は、その理由と代替確認を明記し、UI の完了 claim を弱める
- 主要導線が確認できない場合は PR ready / done と言わず、blocked または human_recheck_required にする

### モデル実行計画

GDD が phase ごとに worker model / effort を使い分ける場合は必須。`requested` と `applied` を混同しない。実行 metadata で確認できない場合は `適用未確認` と表示し、`要求どおり適用済み` と断定しない。

| 工程 | 推奨する品質レベル | 要求する model / effort | 実際の適用状態 | 判断への影響 | 次に選べること |
|---|---|---|---|---|---|
| <例: design-gating> | <設計レビューなので高精度モデル> | <gpt-5.6-sol / medium> | <適用確認済み / 適用未確認 / 利用不可> | <判断品質に影響あり / 影響軽微> | <このまま進める / 高精度 model で再実行 / 人間が確認して採用> |

表示ルール:
- `要求する model / effort`: GDD が worker 起動時に指定する値
- `実際の適用状態`: `verified` / `unverified` / `unavailable` / `failed` の人間向け表示
- formal gate で `unverified` / `unavailable` / `failed` の場合は、軽量 model へ黙って落とさず、再実行または human acceptance を承認ポイントに出す
- main session の model が裏で切り替わったとは書かない。worker 起動時の要求として説明する

### Stage Continuity Brief

段階連続性:
- <S-1: 何を生成するか> → <S-2: 何がそれを consume するか> → <S-3: 何を完成させるか>
- 後続が依存する生成物: <schema / API / policy / fixture / integration contract 等>
- 前回からの段階計画の変更: <初回なら `なし`。再承認なら `Implementation Sequence Plan` の変更要約>
- 人間に戻す条件: <Stage の生成物・依存・後続消費物が変わる場合>

### 段階実装案

`Implementation Sequence Plan` が複数 Stage を持つ場合は必須。`Stage Continuity Brief` は「段階間の受け渡し」、この表は「どの順番で何を実装・検証するか」を示す。片方で代替しない。

| Stage | この段階でやること | このPR/後続 | このOKで承認する範囲 | 完了確認 | 次に進む条件 / 人間に戻す条件 | 後続の追跡先 | 見積もり diff 行数 |
|---|---|---|---|---|---|---|---|
| <S-1> | <目的と生成物を 1 行。例: 既存コード調査と contract test を固定する> | <current-pr / follow-up-pr / post-merge-verification> | <このPRで実施許可 / 後続PRの方針のみ承認 / 後続PR着手前に再承認 / 事前回答で後続PRも実施許可> | <Covers AC / 検証方法 / RED test> | <次 stage へ進む条件。scope・AC を削る・意味を変える、承認した信頼境界を緩めるなら人間に戻す> | <current-pr なら `なし`。follow-up-pr なら Planned Follow-up Stage Lane の seed / backlog / steering 予定> | <production 差分の見積もり行数。範囲でよい> |
| <S-2> | <実装する主な変更> | <current-pr / follow-up-pr / post-merge-verification> | <このPRで実施許可 / 後続PRの方針のみ承認 / 後続PR着手前に再承認 / 事前回答で後続PRも実施許可> | <unit / contract / integration / E2E / external evidence> | <継続条件または停止条件> | <後続PRの作成タイミング・追跡先> | <production 差分の見積もり行数。範囲でよい> |

### 人間に戻す主な条件

Top 3 Stop Conditions:
- <AC・scope を削る・弱める・意味を変える必要が出た、または依頼のとおりに満たせない見込みになった場合>
- <承認した信頼境界（認証・認可・入力検証・credential backend・tenant 境界）を外す・緩める必要が出た場合>
- <自走上限超過、危険操作・本番相当 write、E2E / 外部証跡不足により検証境界が変わる場合>

### まだ確認できないこと

Not Verified Yet:
| 未確認事項 | 今回の扱い | 確認タイミング / 人間に戻す条件 |
|---|---|---|
| <種類>: <post-merge 反映 / relearning / prod 相当評価 / actual posting / 外部サービス状態など> | Deferred / external evidence required / blocked if unavailable | <いつ確認するか。不足時に止めるか、次 phase に送るか> |

### この OK で許可すること / 許可しないこと

| 区分 | この OK で許可すること | この OK に含まれないこと | 人間に戻す条件 |
|---|---|---|---|
| scope / AC | <承認対象の要件・完了条件> | <非スコープ / Deferred / Open Question / 未解決条件> | <AC・scope を削る・弱める・意味を変える必要が出た、または依頼のとおりに満たせない見込みになった場合> |
| 実装 | <採用する作り方・技術スタック・access method> | <未承認の方式変更 / credential backend 変更 / tenant 境界変更 / 公式統合からの逸脱> | <承認した信頼境界（credential backend・tenant 境界・認証・認可）を外す・緩める場合> |
| 自走 | <実装完了まで / PR 作成まで / デプロイ準備まで等、自走上限の範囲内> | <merge / deploy / terraform apply / AWS write / DB write / Docker push / その他の危険操作・本番相当 write。自走上限の値で許す操作は除く> | <自走上限を超える操作、または operational safety 対象の 1 操作ごとの承認が必要な場合> |
| PR 後の完了条件 | <Post-PR Completion Scope がある場合、PR 作成後も done にせず、明示承認済みの post-PR scope の read-only verification / relearning まで追跡する> | <merge / deploy / apply / AWS write の自動実行。これらは 1 操作ごとの明示承認が必要> | <PR 作成後に merge / deploy / apply / AWS write が未承認で必要になった場合は `<gdd-stop reason="blocked">` で停止し、scope は消さない> |
| 検証 | <unit / contract / integration / E2E / external evidence のうち今回実施する証跡> | <今回確認できないこと / 外部証跡なしでは断言できないこと / 非テスト化 Deferred> | <E2E 不可、外部証跡不足、再現不能、検証境界の変更が発生した場合> |

- 今やること: <判断ポイントへの返事> / OK後: <次の phase と残タスク>

### 前提
| 項目 | 内容 |
|------|------|
| 確定 | <箇条書き> |
| 非スコープ | <今回やらないこと> |
| 外部依存 | <なければ「なし」> |
| 設計方針 | <採用方針を 1 行> |
| ベースライン検証 | <pass / fail / not_run。fail なら作業前から壊れていた可能性、not_run なら未計測理由を 1 行> |

### ズレ確認

この節の中身（下の件数の行と「完了条件の変換」表）は `requirements.md` の `### ズレ確認` に書く。一次表示の `### ズレ確認` に出すのは、人に残った行（`質問` にした行の質問の文、回答も仮決定も添えていない `既存とぶつかる`、ユーザーの決めた規則・方針の側に仮決定した `既存とぶつかる`（記録の場所を添える。OK はこの行も承認する）、既存側がユーザーの決めた規則・方針で、依頼の側に仮決定した `既存とぶつかる`（記録の場所か、無ければ `記録の場所: なし` を添える。行数の目安を超えても落とさない。`記録の場所: なし` の行を一次表示に出した human check に本人が返事をしたら、その返事を受けた main が、`requirements.md` の同じ行の末尾に ` / 表示: 済み` を足す〔一次表示の文面を作る subagent と、表示せずに事前回答を当てたときは足さない〕。main が自分の出した一次表示にその行があると確かめられないとき〔compaction の後など〕は足さない。行を書き直したら外し、表示し直した human check に本人が返事をしたら足し直す。完了の報告に書くかはこの印で決める〔`references/post-completion-pr-flow.md` Step 4〕。返事を受けたターンの Stop で印の無い行が残っていれば、hook〔`hooks/scripts/lib/display_marker.py`〕が止めずに知らせる）、`突き合わせ: unavailable`・`判定できない`・`依頼の原文: なし` の行）だけで、無ければ節ごと書かず `zure="none"` にする。要件を固める確認で 3 回聞いても残った行は、human check に回さず、確認の中で一つ前の突き合わせに戻って見直す（`references/brainstorming-steps.md` 9）。延期・削除の有無は、一次表示の `延期・削除:` の行に書く。「完了条件の変換」表のそれ以外の行（`具体化`・`追加` など）は、一次表示の `具体化:` の行に `<扱い> <初期条件の語 | なし> → <変換後>（AC-n）` の形で 1 行ずつ出し、無ければ `具体化: なし` と書く（OK はこの行も承認する。`human-check-template-compact.md`）。行数の目安を超えても、この行は落とさない。HITL は全文レビューの場ではない。この出力ではズレると手戻りが大きい差分だけを露出する（trace 表は作らない — 正本: `references/requirements-template.md` § 精度の第一原則）。そのまま維持した完了条件は表示しない。quick (express)・quick (standard)・standard では、この節の末尾に **既存とぶつかる** として、`.steering/<task>/request-crosscheck.md` の `既存とぶつかる（上位 3）` の質問を、`#` を外してそのまま載せる（0 件なら固定行 `既存とぶつかる: なし`）。要件を固める確認（`references/brainstorming-steps.md` 9）で聞いた行は、質問の後に `→ 回答: <答え>` か `→ 仮決定: <仮決定>` を添える。続けて **原文だけでは決まらない** として、同じファイルの `原文だけでは決まらない` の節の行の件数と行き先を、`#` を使わずに言葉で書く（例: `原文だけでは決まらない 5 件。質問 1 件は下、AI が具体化した 4 件は上の表の 4 行`）。`#` ごとの行き先は `worklog.md` に固定行 `原文だけでは決まらない: <n> 行 / 質問: #a, … / 回答: #d, … / 具体化: #b→AC-n, …（変換表の具体化 <m> 行） / 延期・削除・追加: #c, …` で書く。`<n>` は `request-crosscheck.md` の要件の表で判定が `原文だけでは決まらない` の行の数で、どの `#` も 1 回だけ書く。`<m>` は下の「完了条件の変換」表で、扱いが `具体化` で初期条件がその行の原文の語の行の数（1 行に 2 つ載せたら 2 と数える）で、`具体化:` に並べた `#` の数より少なければ、表に載っていない行がある。行き先の無い `#` を残さない。`質問` にした行は、その質問の文を一次表示の `### ズレ確認` に載せ、`Human Check Questions` の 2 個の上限に数える（上限を超える分は `具体化` か延期にする）。0 件なら、`requirements.md` と `worklog.md` の両方に固定行 `原文だけでは決まらない: なし` を書く。

**完了条件の変換**（無条件必須。表には変換・延期・削除した条件だけを載せる）
| 初期条件 | 扱い | 変換後 | 承認してほしい点 |
|---|---|---|---|
| <ユーザーが最初に言った完了条件（`スコープ` の原文一覧から転記）> | 具体化 / 延期 / 削除 / 追加 / 未解決 | <AC / 非スコープ / Honest Limitations / Open Questions への行き先> | <ここがズレると何が困るか> |

延期・削除の行は、承認してほしい点の欄に固定フィールド `取りに行かない: <当初目的のどこを取りに行かないか（と理由）>` を書く。スコープ縮小の事実だけを書いて、目的に対する取りこぼしを書かないのは不可。延期・削除の行が 1 件も無い場合は、固定行 `延期・削除: なし` を書く（未記録と 0 件を区別する。この固定行が無かったころは、このルールが一度も発火していなかった）。`lint-hitl-decision-quality.py` はこの固定フィールドの有無だけを行ごとに見る（自由文の理由の妥当性は判定しない）。

**テスト化確認**（判断が必要な条件だけ）
| 完了条件 | テスト可能な形 | 確認方法 | HITL で確認したい点 |
|---|---|---|---|
| <テスト化できない完了条件 / E2E必須 / 外部証跡必須 / 解釈差が大きい条件> | <観測可能な claim または未解決> | unit / contract / integration / E2E / external evidence / Open Question | <何がズレると困るか> |

**既存実装の調査状況**
| 調査対象 | 状況 | 見つけた既存経路 / 再利用判断 | HITL で確認したい点 |
|---|---|---|---|
| <repo 構造 / 関連ファイル / 類似実装 / read-write surface / tests / docs / policy boundary / QA観点 / Playwright 対象> | complete / partial / not_run | <既存 wrapper / adapter / policy / client / command / tests を再利用・拡張するか、新規が必要な理由> | <未調査・部分調査のまま OK すると何がズレ得るか。complete なら `N/A`> |

**Engineering Baseline**
| 観点 | 現状 / 採用案 | 根拠 | HITL で確認したい点 |
|---|---|---|---|
| どこに何を置くか | <architecture / code structure / module boundary> | <既存構造・類似実装・新規なら採用理由> | <この構造で「思った作り方」とズレないか> |
| どうやって同じ環境を再現するか | <dependency manifest / lock file / runtime / install command> | <既存 file / docs / CI / 未整備なら今回整える範囲> | <未整備のまま進めてよいか、今回整えるか> |
| どうやって検証するか | <test command / CI command / baseline command> | <既存 test / runner / CI / 代替確認> | <どの検証を OK 条件にするか> |

**コードベース健全性確認**
| 見つかったこと | 設計・タスク順序への影響 | この OK で扱うこと | HITL で確認したい点 |
|---|---|---|---|
| <巨大ファイル / lockfile なし / test baseline なし / CI baseline なし等。影響する finding だけ> | <設計変更、先に足場タスク、今回は Non-Goal 等> | <実装する / 先に整える / 明示的に対象外にする> | <後戻りが大きい判断だけ> |

**アーキテクチャ提案**
| 採用案 | 何を意味するか | 却下した案 | HITL で確認したい点 |
|---|---|---|---|
| <Follow / Fit + Small Refactor / Reshape / Simple Modular / Layered / Clean-ish / Service / Worker Split> | <承認者が分かる言葉で。例: 既存の置き場所に合わせる / 小さく責務整理する / service を分ける> | <なぜ採用しないか> | <この構造で進めてよいか。後から変えると何が大きく変わるか> |

**依存・実行環境**
| 項目 | 採用 / 現状 | 不足・制約 | HITL で確認したい点 |
|---|---|---|---|
| package manager / dependency manifest / lock file | <例: pnpm + package.json + lock file / pyproject + lock / missing> | <不足があれば明記> | <今回整えるか、後続に回すか> |
| runtime / install command / test command / CI command | <実行環境とコマンド> | <未確認・重い・CIのみ等> | <どこまでを完了条件にするか> |

**Project Reproducibility Gate**
| 再現性チェック | 状態 | 扱い |
|---|---|---|
| dependency manifest | confirmed / missing / needs-human / N/A | <今回作る / 既存利用 / 後続 / 非スコープ> |
| lock file | confirmed / missing / not-used + reason / needs-human / N/A | <同上> |
| install command | confirmed / missing / needs-human / N/A | <同上> |
| test command | confirmed / missing / needs-human / N/A | <同上> |
| CI command | confirmed / missing / needs-human / N/A | <同上> |

**Baseline Compliance Check**
| 完了時に確認すること | 確認方法 | 失敗時の扱い |
|---|---|---|
| approved architecture / file placement に従ったか | <diff / reviewer / path check> | <設計に戻す / 実装修正 / human recheck> |
| dependency manifest / lock file が実装と一致するか | <manifest / lock / import / provider / image check> | <修正して再検証 / 未整備なら blocked> |
| fresh install / fresh test / CI command の証跡があるか | <command / CI / not_run reason> | <pass 扱いしない / blocker / debug route> |

**Architecture Drift / Re-Architecture**
| 兆候 | 今回の扱い | 人間に戻す条件 |
|---|---|---|
| <mixed responsibilities / duplicated validation / dependency direction inversion / runtime-deploy mismatch 等> | <なし / Local Refactor / Boundary Reshape / Runtime / Service Split / 後続> | <承認済み architecture option や runtime boundary が変わる場合> |

**正本と事実の扱い**
| 種別 | 扱い | HITL で確認してほしい点 |
|---|---|---|
| 会話履歴 | 会話履歴は参考情報。compaction / 新チャットで欠落し得るため、単独で正本にしない | 初期意図の読み替えがズレていないか |
| GDD artifact | GDD artifact は正本。requirements.md / design.md / tasklist.md / state.md / worklog.md / continuation.json を承認済み scope と state の基準にする | artifact に残した What / How / 検証境界が妥当か |
| Git / PR / CI / test | Git / PR / CI / test は事実。merge commit、PR state、CI、test result、diff を観測事実として扱う | 事実確認できないものを pass 扱いしていないか |
| Continuation ID | Continuation ID は復旧用の受け渡しキー。通常は同じチャットで「次に進んで」、チャットが壊れた場合だけ `/gdd-resume <id>` で registry を読む | 長文プロンプト貼り付けではなく ID 復元でよいか |

**ワークフロー適合判定**
<!-- 人間の判断が必要な場合だけ出す。必要なのは (a) 判定が standalone route / superpowers sufficient のとき、(b) ユーザーが formal workflow 継続を明示したとき の 2 つだけで、それ以外（GDD formal workflow で判断不要 / not_applicable）はこのブロックごと出力しない -->
| 判定 | 理由 | HITL で確認したい点 |
|---|---|---|
| GDD formal workflow / standalone route / superpowers sufficient | <state machine・AC ID・Reviewer Lineage が必要か、単発相談や単発 debug で十分か> | <GDD に乗せる重さが妥当か。standalone route に落としてよいか> |

**Baseline Verification Status**
| baseline_command | status | evidence / blocker |
|---|---|---|
| <例: npm test / pytest / bash tests/validate-plugin.sh / not_run> | pass / fail / not_run | <開始時点で壊れているか、未実行ならなぜ未実行か> |

**技術スタック確認**
| 採用する技術スタック | 代替案 | 採用理由 | HITL で確認したい点 |
|---|---|---|---|
| <MCP / CLI / SDK / API / framework / runtime / IaC / DB 等> | <比較した案> | <Existing repo standard / Official integration / Operational constraints / Multi-tenant / credential boundary / Testability への適合> | <access method / credential backend / tenant 境界 / 公式統合とのズレで何が困るか> |

**アーキテクチャ選択**
複数の妥当な選択肢がある architecture / CI / IaC policy / runtime / framework / test tooling / access method / credential backend では必須。AI が勝手に単一案へ丸めない。既存 repo 標準、業界標準 / vendor official、最小の自前実装、現行方式を比べ、DRY / KISS / YAGNI に照らして採用しない理由と人間に確認する点を出す。

`業界標準 / vendor official` は、vendor official があれば vendor official、無い/非該当なら ecosystem standard 寄り候補を意味する。HITL では混同しないよう、例: `OPA/Rego + Conftest（Terraform公式そのものではなく、policy as code の標準寄り候補）` のように一言補足する。

| 選択肢 | 何をする案か | 標準との合い方 | DRY / KISS / YAGNI | 良い点 | 弱い点 / 採用しない理由 | AIの仮決定 |
|---|---|---|---|---|---|---|
| 既存 repo 標準 | <既存CI・既存tooling・既存配置に合わせる> | <既存 repo 標準との一致> | <重複・複雑化を増やさないか> | <良い点> | <不採用なら理由> | <採用 / 不採用 / 人間に確認> |
| 業界標準 / vendor official | <公式・標準ツールに寄せる> | <公式統合・標準方式との一致> | <自前実装を減らせるか> | <良い点> | <不採用なら理由> | <採用 / 不採用 / 人間に確認> |
| 最小の自前実装 | <Python / shell / small script 等で狭く作る> | <標準から外れるか> | <KISSか、長期的に重複が増えるか> | <良い点> | <不採用なら理由> | <採用 / 不採用 / 人間に確認> |

Terraform plan JSON の CI policy では、既存 repo 標準が無い限り `OPA/Rego + Conftest` を第一候補として説明する。既存 repo 標準が Python 等で存在する場合は、既存標準拡張と `OPA/Rego + Conftest` 移行を `needs-human` として並べ、policy が増える見込み、保守できる人、導入コスト、CI 依存追加を判断材料にする。`Python 独自チェック` を採る場合は「なぜ Conftest / OPA ではないか」を判断ポイントに出す。`terraform validate / tflint / Checkov` は補助候補として、何を検出し何を検出しないかを `検証計画` に分ける。

**実装技術スタック**
| 分類 | 採用するもの | 採用理由 | 変更時の影響 |
|---|---|---|---|
| language / runtime | <例: Python 3.11 / Node.js 20 / Go 1.22> | <既存 repo 標準・host 制約・運用制約> | <変えると build / deploy / test に何が波及するか> |
| framework / library | <例: FastAPI / React / Terraform provider / internal helper> | <既存実装再利用・公式統合・保守性> | <変えると API shape / UI / IaC state に何が波及するか> |
| test tooling | <例: pytest / vitest / contract test / E2E smoke> | <AC の検証方法と対応> | <検証境界が変わる場合の影響> |
| access method | <MCP / CLI / SDK / direct API / managed integration> | <公式統合・既存標準・認可境界> | <後から変えると credential / tenant / mock / E2E が変わるか> |
| credential backend | <Secrets Manager / SSM / env / OAuth / none> | <secret handling と tenant 境界> | <変更時の移行・権限・監査影響> |

**作り方の重要判断**
| 論点 | AI の仮決定 | 代替案 | ズレた時の影響 |
|---|---|---|---|
| <repo 分割 / import-recreate / 既存再利用 / public-private / CI/CD 方針など> | <採用案> | <却下案または design-gating 送り> | <後戻りが高い理由> |

### 承認ポイント
承認ポイント数: 1
返答ガイド:
- **「OK」** → 差 `なし` の点を承認し、上記の自走上限まで進めます。`なし` 以外の点は承認にせず、要件の変更の経路（`gdd-requirements-amendment`。計画の途中なら `planning_rework_required`）に送ります
- **「N は〇〇にしてほしい」** → 該当ポイントを修正し、全部の点を再提示します（表示した案を名前で選ぶ返答（「1 は B で」「推奨で」）は変更要求ではない（`commands/gdd-dev.md` #10 STEP 1 の「明確な承認」）。全部の点に答えていれば、再提示せずに進みます）
- **「実装方針を〇〇に変えて」** → AC は維持し、設計フェーズから再開します
- **「自走上限は PR 作成まで」** → 実装・検証・PR 作成までは進め、merge / deploy は止めます
- **「全面見直し」** → 要件ごとやり直します

**1. <判断テーマ>**
- **AI の仮決定**: <選んだ案を 1 行>
- **根拠**: <なぜこれを選んだか・根拠となる制約や前提を 1-2 行>
- **却下した代替案**: <検討したが採用しなかった案 + 却下理由を 1 行。単一候補なら「他案なし（理由）」>
- **判断に影響する前提**: <この前提が崩れたら結論が変わる条件を 1 行。なければ「なし」>
- **この案を選ぶと次に何が起きるか**: <実装・成果物・後続 phase への影響を 1-2 行>
- **依頼との差**: なし
- **無回答時のデフォルト**: <無回答・部分回答時に AI が採る挙動を 1 行。「仮決定を採用する」だけの定型文は禁止。何が既定で選ばれ、その結果どうなるかを具体的に書く>

**N. 方向性**
- 自走範囲: ...
- 自走上限: ...
- 人間に戻す条件: ...

### 用語の短縮定義（該当時のみ必須）
- `<用語1>`: <1 行定義>
- `<用語2>`: <1 行定義>
- `warn`: 問題の可能性を記録・表示するが、今すぐ止めない扱い
- `offline`: 本番の実行経路ではなく、評価・検査用にだけ使う扱い
- `unknown surface`: Browser / Playwright / HTTP など外部送信になり得る未知の経路

### 参考（任意）
変更範囲 / リスク / 戻し方 / 詳細: <.steering/パス>
```

---

## 必須ルール（contract 違反で `human-check-waiting` に進めない）

以下で「含める」「表示する」と定める節のうち、冒頭の前置き 3 行（依頼・なぜやるか・現在地）・判断ポイント・OK の範囲（自走上限・この OK で許可しないこと・人間に戻す条件・延期・削除）・段階実装サマリー・条件付きの節（選択肢の説明・アーキテクチャ選択・Multiple PR Strategy Options・人に残ったズレ確認）以外は、`requirements.md`（または `state.md`・`request-crosscheck.md`）に書き、一次表示ではその場所を指す 1 行にする（§ 一次表示の原則）。

### 構造・マーカー

1. 出力に `<gdd-stop reason="human-check-waiting">` マーカーを含める（無いと autonomous continuation が止まらず人間確認がスキップされる）。直前の行（空行のみ挟んでよい）に `<gdd-hitl-fields options="none|filled" arch="none|filled" zure="none|filled" multi-pr="none|filled" stage="none|filled" request-diff="none|differs,…">` タグを置く（`references/human-check-template-compact.md` の Template どおり）。`none|filled` は二択の記法であり、各属性の値は `none` か `filled` のどちらか一方だけを書く（`none|filled` という文字列をそのまま書くと reject される）。`request-diff` は判断ポイントの順に、`依頼との差` が `なし` の点を `none`、それ以外を `differs` としてカンマで並べる（例: `request-diff="none,none"`。簡易な確認も同じ）。`lint-hitl-required-fields.py`（条件付き節の「該当なし」の明記と Option 軸の必須化の検査、warn-only）はマーカー直前に隣接するタグだけを見るため、間に他の行を挟むと正しく宣言していても検出されない。マーカーの後には `## 👤 次にすること`（`references/output-format.md` § 停止時の「👤 次にすること」マップ）を置く（無いと Stop hook が停止を差し戻す）
2. 「requirements.md を確認してください」「次は human check です」だけで止めない（テンプレート省略は contract 違反）
3. Express Path も同じテンプレートを使う（承認ポイントは方向性承認と、ほかに 2 件以内）
4. downstream phase からの再承認では「前回からの変更点」を承認ポイントの前に追加する
5. 初回 human check では **自走上限** を必ず明示する。上限が曖昧なまま `OK` 承認させない
6. 初回 human check では、完了条件の変換を必ず `requirements.md` の `ズレ確認` に書き、一次表示には `延期・削除:` と `具体化:` の行を出す。作り方の重要判断はズレると後戻りが大きい箇所だけを追加で出す。requirements.md の全文や全 AC を貼らない
7. `現在地` は前置きの `**現在地**:` の 1 行で示し（§ 判断の書き方 2）、`人間が今やること` と `OK 後に残る作業` は OK の範囲の `今やること:`・`OK後:` の行に書く。`ここまで出来ていること` と `残タスク` は `state.md` に書く。state.md / tasklist.md / requirements.md / design.md を根拠にし、根拠が無い残タスクは推測せず「承認後に task-breakdown で作成」または「未作成」と書く
8. 外部サービス、runtime、framework、test tooling、access method、credential backend のいずれかを採用または変更する場合、`技術スタック確認` とは別に `実装技術スタック` を必ず含める。HITL で「何を作るか」だけでなく「何で実装するか」を承認できる状態にする
9. architecture / CI / IaC policy / runtime / framework / test tooling / access method / credential backend の選定で複数の妥当な選択肢がある場合、`アーキテクチャ選択` を必ず含める。既存 repo 標準 / 業界標準 / vendor official / 最小の自前実装を比較し、AI が勝手に単一案へ丸めない。非標準な自前実装を採る場合は、採用理由と採用しない理由を `人間に確認` する承認ポイントへ昇格する
10. 初回 human check では `この OK で許可すること / 許可しないこと` を必ず含める。`OK` が許可する scope / AC、実装、自走、検証と、`この OK に含まれないこと` を同じ表で明示する。危険操作・本番相当 write はここで明示的に **承認しない** と書く
11. 初回 human check では `まず見るところ` / `人間に戻す主な条件` / `まだ確認できないこと` を `この OK で許可すること / 許可しないこと` より前に置く。制限事項・未検証事項・停止条件を詳細 trace や参考欄に埋めない
12. 初回 human check では `判断ポイント` を必ず含め、`OKで実装・検証すること` / `OKしても今回は対象外のこと` / `人間に決めてほしいこと` を § 判断の書き方 で書く（長さでは決めない）。制限事項を詳細表に埋めず、先頭で読む人に見えるようにする
13. 初回 human check では `承認サマリ` を `判断ポイント` の後に置く。非エンジニア向けに `人間が今だけ判断すること` / `OK で許可される最大到達点` / `OKでも許可されないこと` を出し（行数では決めない）、詳細表を読まない承認者にも誤承認させない
14. `Baseline Verification Status` を取得済み、または未実行理由が判明している場合は、`前提` の `ベースライン検証` に必ず出す。作業前 failure を隠すと、承認者が「今回壊した / 今回直るはず」を誤認する
15. `ベースライン検証` を承認ポイントに昇格する条件:
   - baseline `fail` / `not_run` が今回の完了条件、検証範囲、または「既存 failure を直すか」に影響する場合は、独立した承認ポイントにする
   - baseline `not_run` だが代表コマンドが存在するかを人間に確認したい場合は、`人間に決めてほしいこと` に出す
   - baseline が `pass`、または未計測でも scope / 完了条件に影響しない軽微な作業なら、`前提` に書けば足りる。承認ポイントを増やしすぎない
16. 複数段階では `Stage Continuity Brief` を必ず含める。`Implementation Sequence Plan` 全文を貼らず、Stage 間の生成物・consume 関係・前回からの段階計画の変更・人間に戻す条件だけを書く（§ 判断の書き方 4）
17. `Implementation Sequence Plan` が複数 Stage を持つ場合、`Stage Continuity Brief` とは別に `段階実装案` を必ず含める。`段階実装案` には `Stage ID`、この段階でやること、この PR / 後続の区分、この OK で承認する範囲、完了確認、次に進む条件 / 人間に戻す条件、後続の追跡先、**見積もり diff 行数**を出す。`Stage Continuity Brief` だけで済ませない
18. 「段階実装」「複数段階」「この PR ではここまで」「後続で実施」と書く場合、`段階実装案` が無い human check は contract 違反。段階の詳細が多い場合でも、HITL には stage list summary を出し、詳細は requirements.md の `Implementation Sequence Plan` に残す。`follow-up-pr` の Stage は `後続PRの方針のみ承認` または `後続PR着手前に再承認` を明記し、この OK だけで後続実装へ自走しない。例外は、§ 事前回答 の対象に入っている Stage で `事前回答で後続PRも実施許可` を独立した承認ポイントとして出したときと、`Continuation Mode=auto-after-clean`・`auto-stacked` を独立した承認ポイントで選んだ Stage（`references/requirements-gating-steps.md`）だけである（3 つの値の違いは § 事前回答 の 4）。`このOKで承認する範囲` は承認者の誤解を防ぐために必須で、`current-pr` は `このPRで実施許可` と書く
19. 段階が 1 つだけの回（sizing を問わない）は、段階実装の節（`段階実装サマリー`・`Stage Continuity Brief`・`段階実装案`）を書かず、`<gdd-hitl-fields>` の `stage` を `none` にする。複数段階、または後続PR着手前に再承認を出すときは節を書いて `filled` にする。display-integrity・human-check-language・decision-quality の lint は、各 stop marker 直前のタグがすべて `stage="none"` のときだけ段階実装の語を要求しない
20. 初回 human check では、読み書き・保存・投稿・検索・更新・外部連携を含むタスクなら `既存実装の調査状況` を必ず含める。調査結果（`findings.md`）から、再利用判断や未調査だとズレる点だけを表示する
21. ユーザー入力の完了条件に `merge` / `マージ` / `再学習` / `relearning` / `post-merge verification` / `release verification` / `apply 後確認` が含まれる場合、`Post-PR Completion Scope` を必ず表示する。標準既定を理由に自走上限を PR 作成までへ自動降格しない。write 操作が未承認なら `別途明示承認が必要な操作` に分離し、完了条件そのものは残す
22. `Option A` / `Option B` / `Option C`、`P0` / `P1` / `P2`、`S-1` / `S-2` のような短いラベルを使う場合は、`選択肢の説明` または `段階実装案` でラベルの意味を同じ HITL 内に定義する。`Option B とは？` と聞かれる状態、未定義の Option ラベル、略称だけの承認ポイントは contract 違反であり、human-check に進めない
23. `OKで実装・検証すること`、`検証`、`no-post`、`score`、`compare`、`runner`、`E2E`、`external evidence` のいずれかを出す場合は、`検証計画` を必ず含める。`検証計画` には検証対象、どこで確認するか、どう確認するか、OK条件、失敗時の扱いを出す。`classified unavailable artifact` や外部前提不足は成功扱いではなく、分類済み未検証として扱い、PR ready / 完了とは言わない
24. コードベース健全性の調査で設計・タスク順序・検証方法へ影響する finding がある場合は、`コードベース健全性確認` を必ず含める。全 finding を貼らず、巨大ファイル、依存管理、テスト/CI baseline のうち「今回どう扱うか」を人間が判断すべきものだけに絞る。影響なしなら欄は省略可

### 承認ポイントの 8 要素（欠落禁止）

各承認ポイントは必ず以下の 8 要素を揃える。1 つでも欠けたら contract 違反:

- **AI の仮決定**: 選んだ案
- **根拠**: なぜそれを選んだか・根拠となる制約
- **却下した代替案**: 検討したが採用しなかった案 + 理由（案が実質 1 つの判断は判断ポイントにしない。§ 止まり直さないもの 1。OK の範囲だけを判断ポイントにしたときは「他案なし（理由）」）。compact 正本は `採用しない案`
- **判断に影響する前提**: この前提が崩れたら結論が変わる条件（なければ「なし」）
- **この案を選ぶと次に何が起きるか**: 実装・成果物・後続 phase への影響
- **依頼との差**: `なし`。推奨は依頼より狭くせず、狭める案は `採用しない案:` に変わる AC を書いて並べる。`あり: <その項目>`（`なし` と並べない）の点がある確認は、表示の時点で出し直しになる
- **無回答時のデフォルト**: 無回答・部分回答時に AI が採る挙動。定型文禁止（悪い例: 全ポイントに同一の「仮決定を採用する」とだけ書く状態）。依頼の原文やユーザーが決めた範囲より狭い案を既定にしない（扱いの正本は `common-guardrails.md` § scope の勝手な拡大・縮小）。自走上限の `マージまで` 以上も既定にしない

**Why**: 人間が根拠を追えないと承認判断できず、停止点の価値（artifact を開かず判断できる）が崩れる。HITL の多くは「OK」だけで確定し、既定がそのまま結論になる。以前あった `既定範囲` / `狭める根拠` の欄は、数値を書けば狭い側を既定にしてよいと読めたので撤去した（2026-11-08）

### 承認ポイントの固定フィールド受理文法

承認ポイントの欄が書かれているかは、自由文からは判定しない（原理的に閉じない。PR 旧#83 は自由文判定で何巡回しても収束しなかった）。lint は行の形・隣接性・固定キーだけを見る。

<!-- decision-scope-grammar:begin -->
承認ポイントの欠落検査（判断に影響する前提 / 却下した代替案・採用しない案）は見出しや番号書式に依存しない。起点は `### 判断ポイント` / `### 承認ポイント` の見出しのうち、節の中に `承認ポイント数: <N>` の宣言を持つ最初のもの（見出しは完全一致。見出しが見つからなければ reject。full は後ろの `### 承認ポイント`、compact は `### 判断ポイント` になる）で、見出し直後に固定で書くその宣言値と `- 無回答時のデフォルト:` の出現数を突き合わせ、一致しなければ reject する（宣言が無い場合も reject）。`- 無回答時のデフォルト:` の出現を終端マーカーとし、直前の終端（1件目は区間内最初のテーマ行）からの区間を 1 ポイント分として検査する。`完了条件の変換` の見出しそのものが無いケースも、この終端マーカーを持つ文書に限って検査する（変換表がほとんど出ていなかった原因。簡易 HITL はこの検査の対象外のまま据え置く）。

限界: 件数の突き合わせは著者が宣言した `承認ポイント数:` を信頼する（他の固定フィールドと同じ自己申告の信頼境界。宣言と実態が食い違えば reject で気づける。旧実装はテーマ行の番号書式から件数を推定しており、番号を持たない書式で同型の fail-open を繰り返した経緯がある）。1件目の開始位置だけは番号付き行（`1. <テーマ>` 等）に一致する必要があり、1件目が番号を持たない書式だと reject する（受け入れる限界）。
<!-- decision-scope-grammar:end -->

`依頼との差:` は判断ポイントごとに 1 行書く（選択肢が複数あるときは推奨の案について）。値は `なし` か、推奨が満たさない依頼の原文の項目を宣言する `あり: <その項目>` の 2 形だけで（`なし | <項目>` のように並べない。`ありません` などの言い換えもしない）、理由を書く場所は無い。推奨を依頼より狭くしないので、ふつうは `なし` になる（`あり:` の点がある確認は、表示の時点で出し直しになる）。ユーザーが自分で狭めると決めた点は、その発言を `根拠` の行に引き、欄は `なし` にする。簡易な確認も、判断ポイントごとに 1 行置く。この語は欄の行だけに使い、提示のほかの文（返答ガイド、出し直しの理由の説明など）には書かない。再提示では全部の点を載せる（変えていない点と、ユーザーが取り下げた点は、1 行と欄の行だけでよい）。

承認の記録（`Human Check Status` を approved にする書き込み）は、hook（`hooks/scripts/lib/request_diff_approval.py`）が直前の提示と照らし、次のときに止める: マーカーの直前にタグが無いか、タグの `request-diff` が読めない（属性が無い・2 つ以上・`none`/`differs` のカンマ区切りでない）、`differs` の点がある、この語を含む行が `- 依頼との差: <値>` の形でない、値が `なし` と `あり: <項目>` のどちらでもない、`あり:` の点がある。通すかどうかと件数はタグだけで決め、本文の欄の数と `承認ポイント数:` は読まない（引用・例示にある欄の形の行を、欠けた本物の欄と区別できないため。本文の欄が欠けていても止めない）。その前に、確認を出した Stop で、hook（`hooks/scripts/lib/request_diff.py`）が同じ判定（欄とタグの形と、`あり:`・`differs` の点）を当て、止まる確認なら block し、ユーザーが答える前に確認の全文を出し直させる（同じ人の発言のターンで 3 回まで。数えは、この hook 自身の記録〔`request-diff.log` の、同じ session・人の発言のターンの block の行〕で決め、block は数えの行を書けたときだけ出す〔書けないときは止めずに知らせる〕。その後は、最後の発言の形によらず止めずに、人に知らせだけを出す。知らせは、上の確認にそのまま答えてよいこと、依頼より狭い点を受け入れるならその点を名指しで答えることと、hook が見た行〔読めない行と `なし` 以外の値〕を並べる）。前の提示とは比べないので、変えた点だけの再提示で外れた点が消えると通る。Bash で承認を書くコマンドは、提示を読まずに Edit・Write へ付け替える。依頼から外れる点は、承認ではなく要件の変更の経路に送る。値の正しさは書き手の自己申告で、hook は見ない。欄かタグに問題のある確認にユーザーが返事をした後は（Stop の hook が動かなかった・記録を書けなかったときなど）、確認を出し直さない。マーカーを付けない発言の最後の行に `<gdd-hitl-fields correction request-diff="none,none" decided="<返事の文>">`（判断ポイントの順に、値はすべて `none`。提示のタグが読めれば点の数をそろえる。`decided` には、提示の後のユーザーの返事の文を 1 行で、`"` とこの語を含まない部分をそのまま引く）を置いた補正を書き、承認を書き直す。承認の書き込みの検査は、提示の後の人の返事の後に書かれた最後の補正を、提示と同じ判定（補正の文全体の欄とタグ）で見て、`decided` がその返事に含まれれば通す（記録は `allow-corrected` と引用の字数。人の発言は残さない）。hook は狭める点かを分類せず、どの補正にも引用を求める。依頼を狭める点（`あり:`・`differs`・読めない欄）は、返事がその点を名指しで選んだときだけ `none` にし、名指しが無ければ、確認全体ではなく、その点を受け入れるかだけを問う

### 用語の短縮定義

仮決定や AC に **ユーザーが即座に意味を取れない技術用語**（Webhook event 名・プロトコル名・サービス固有の概念等）が含まれる場合、**同じ human check 出力内で 1 行定義**を付ける。別ドキュメントに誘導しない。

特に `warn` / `offline` / `unknown surface` のように制限事項の誤解につながる語は、非エンジニア向けに「何を止めるか / 止めないか」を自然文で説明する。例: `offline Judge`: 評価用の検査であり、本番では止めない。`unknown surface`: 未知の経路で、warn の場合は今すぐ止めない。

例:
- `synchronize イベント`: PR に新しい commit が push されたときに発火する GitHub Webhook event
- `ready_for_review`: Draft PR が通常の PR に変更されたときに発火するイベント

### 通過予定 gate 数の置換値

sizing ごとの gate 数。`<N gate>（<gate 名を列挙>）` を以下で置換する。

| sizing | gate 数 | gate 名 |
|--------|---------|---------|
| quick (express) | 2 gate | req-gate → impl-gate |
| quick (standard) | 3 gate | req-gate → design-gate → impl-gate |
| standard | 4 gate | req-gate → design-gate → impl-gate → completion |

**Why**: ユーザーが「承認後にどれだけ AI が自走するか」を事前に把握できる。「standard: 4 gate を通過予定」と見れば覚悟ができるし、過剰に感じれば sizing 変更を依頼できる。

### 自走上限の置換値

`<自走上限>` は、今回の human check で承認された後に AI がどこまで進めてよいかを示す。scope / AC の承認とは別に、以下のいずれかを明示する。

| 上限 | AI が進めてよいこと | 止めること |
|------|--------------------|------------|
| 実装完了まで | 実装、テスト、実装 gate、完了確認用の証跡整理 | commit / push / PR 作成 / merge / deploy |
| PR 作成まで | 実装、テスト、commit、push、PR 作成、PR 本文作成、PR の CI の失敗の修正と push（`references/post-completion-pr-flow.md` Option 1 手順 6） | merge / deploy |
| PR 作成 + 外部レビュー収束まで | 上に加え、`gdd-pr-review-followup` § Auto-Arm Entry での外部レビューの収束（設定キー `PR Auto Review Convergence` があるときだけ選べる） | merge / deploy |
| デプロイ準備まで | PR 作成、release note、deploy plan、dry-run / plan、必要な手順整理 | deploy 実行、本番 write 操作 |
| デプロイ実行まで | 明示された環境への deploy 実行まで。ただし危険操作は 1 操作ごとの承認を維持 | 未提示の追加 deploy、merge、追加 write 操作 |
| PR マージ後検証 / 再学習まで | PR 作成、レビュー収束、明示承認済みの post-PR scope、post-merge verification / relearning の read-only 確認 | 未承認の merge / deploy / apply / AWS write。これらは 1 操作ごとの明示承認で停止 |
| マージまで | PR 作成、`gdd-pr-review-followup` の経路でのマージ（`references/post-merge-qa.md` 手順 2） | マージ後の write と QA。マージで起動する CD は止まらないので、この値を提示するときに並べる |
| マージ・デプロイ・QA まで | 上に加え、QA 計画とそのレビュー、承認した QA の範囲の環境へのデプロイの完了確認、`gdd-qa-runner` による QA、失敗時の revert PR の作成 | revert のマージ、承認した QA の範囲（環境・書き込み先）の外への操作、本番へ出す後続の PR のマージ |

- デフォルト推奨は **PR 作成まで**。リポジトリ規約やユーザー指示で commit / push / PR 作成が禁止される場合は **実装完了まで** に落とす
- ユーザーが「マージして再学習まで」などを完了条件に入れた場合、デフォルト推奨を理由に `PR 作成まで` へ自動降格しない。HITL では `Post-PR Completion Scope` として表示し、PR 作成後も done にしない範囲と、merge / deploy / apply / AWS write のように 1 操作ごとの明示承認が必要な範囲を分ける
- 本番 deploy、Terraform apply、AWS write、DB write、docker push、merge 等の operational safety 対象は、自走上限が「デプロイ実行まで」でも **1 操作ごとの明示承認** を別途必要とする
- `<自走上限>` に書くのは表の「上限」の列の値だけにする。範囲を狭める条件（PR の限定・前提の PR など）があるなら、その値にせず `PR 作成まで` にする（別の行に書いても入口の判定は読まない）。日付・発話の引用・委任先は注記に付けず `worklog.md` に書く（`references/post-merge-qa.md` 手順 2 は値の完全一致で本人の承認を判定する。2026-10-02 時点の `state.md` 7 本はどれも注記つきで、一致しなかった）
- `マージまで` と `マージ・デプロイ・QA まで` は、どの repo でも選択肢に出す（セルフマージを許さない repo は GitHub がマージを断る。`references/post-merge-qa.md`）。`マージ・デプロイ・QA まで` を出すときは、同じ確認に QA の範囲（環境・デプロイの workflow・書き込み先。本番なら本番と書く）を並べる（`references/post-merge-qa.md` § QA の範囲）。どちらも既定値・推奨値にせず、値に置くのはユーザーがこのタスクで選んだ・求めたときだけにする。マージで起動する workflow と環境を判定できなければ `不明` と書く。`Merge Approval` を問わずにマージしてよい条件と、QA の書き込みを runner に任せてよい条件は同じ文書の手順 1・2 に従う（上の 1 操作ごとの承認が緩むのは、マージは同じ文書 手順 2 の自走のマージの条件、QA の書き込みは手順 1 の条件を満たすときだけ）
- 自走上限を変更したい場合は、ユーザーが「自走上限は PR 作成まで」「デプロイは止めて」等と返せるように、承認ポイントにも 1 件として出す
- **判断の委任**：自走上限と並べて、承認の後の human check を誰が判断するかを 1 行で出す。値は `Fable に任せる`（`fable`。既定）／`人に止める`／`相談役に任せる`（`並行`）／`Opus に任せる`（`opus`）。この行を出すのは、その steering の `state.md` に `Approved Direction` がまだ無い間の human check（修正指示での再提示を含む。前の返事で値を選んでいればその値を出す）だけで、後の human check には出さない。行には、既定が `Fable に任せる` であること、`OK` だけなら承認の後の判断は Fable が決めること、人に戻るのは § 事前回答 3 の条件に当たるときであること、人に止めたいときはそう返せばよいこと（承認の後も会話で戻せる。§ 事前回答 5）を書く。承認の時点で、選んだ値（返事が `OK` だけなら `fable`）を `Approved Direction` の `- 判断の委任: <fable | opus | 並行 | 人に止める>` の欄に書く。`自走上限` と同じく 1 つの値を上書きで持ち、承認の後の上げ下げは § 事前回答 5 で行う。この欄のために `事前回答:` 行は書かない。欄の値が `人に止める` 以外なら、以後の human check を § 事前回答 2 で扱う。欄の無い steering（この既定の前に承認したもの）は、今までどおり `事前回答:` 行だけで決める（2026-11-14 にユーザーが「GDDで途中の意思決定はFableに任せたい」「要件が満たせないときだけHITLでいい」と言った。それまでの既定は `人に止める` で、委任は `事前回答:` 行にだけ記録した）
- `この OK で許可すること / 許可しないこと` の表では、`自走上限` の置換値をそのまま人間向けに再掲し、`この OK に含まれないこと` と `人間に戻す条件` を隣に置く。上限名だけで済ませない

**Why**: 「OK」が要件承認なのか、PR 作成までの許可なのか、デプロイまでの許可なのかが曖昧だと、AI が進みすぎるか、逆に途中で止まりすぎる。初回 HITL で最大到達点を分けて確認することで、自走と安全確認の境界が揃う。

---

## content 品質ルール

### HITL の役割

- human check は全文レビューの場ではない。判断に効かない段落は読ませず、ズレると後戻りが大きい判断だけを材料と一緒に露出する（§ 判断の書き方）
- HITL 停止時は「承認してください」だけで止めない。冒頭の `まず見るところ` で、何を判断してほしいか、OK が何を許可し何を許可しないか、迷ったらどこを見るかを 30 秒で読めるようにする
- `人間に戻す主な条件` は Top 3 Stop Conditions として表の前に出す。AC・scope / 信頼境界 / 自走・検証境界の 3 系統を自然文で示し、詳細な `人間に戻す条件` は `この OK で許可すること / 許可しないこと` の表で補足する
- `まだ確認できないこと` は Not Verified Yet として表の前に出す。post-merge 反映、relearning、prod 相当評価、actual posting、外部サービス状態など、今回の HITL では断言できないものを `Deferred` / `external evidence required` / `blocked if unavailable` で扱い分ける。未確認事項の先頭には、限界の種類（`references/common-guardrails.md` § Honest Limitations）を書く
- `Stage Continuity Brief` は段階計画レビューではない。人間に確認してほしいのは、Stage の生成物が後続でどう使われるか、どの境界が変わると再承認が必要かだけに絞る。全 task / 全 Depends on / 全ファイル一覧は tasklist に残し、HITL では表示しない
- 段階が 1 つだけの回は、sizing を問わず `Stage Continuity Brief` を書かない（必須ルール 19。多段階でないことはタグの `stage="none"` で示す）
- `段階実装案` は表示されていても、空欄、`TBD`、`TODO`、`適切に`、`必要なら`、`実装する`、`テストする` だけのような曖昧なセルがある場合は contract 違反。`scripts/lint-hitl-stage-plan.py` で human-check draft / fixture を検査できる形にし、複数 Stage では Stage ID と requirements.md の `Implementation Sequence Plan` を対応させる
- `後続の追跡先` は、`follow-up-pr` / `post-merge-verification` の Stage で必須。未作成なら `Planned Follow-up Stage Lane seed を completion/post-merge で作成` と書き、後続 Stage が会話終了で消えないようにする
- `選択肢の説明` は内部メモではなく、承認者の「Option B とは？」を防ぐための欄である。Option A / B / C を使わない場合は節ごと書かない。Option B だけを承認ポイントに出してはいけない
- `検証計画` は full test list ではない。人間に確認してほしいのは、どの完了条件をどの場所・どの方法で確認し、何を OK条件 とし、失敗した時に自動修復するのか人間に戻すのかである。実装詳細の全テスト名は tasklist / design に残す
- downstream phase からの再承認では、`前回からの段階計画の変更` に `Implementation Sequence Plan` の差分を必ず要約する。新 task が元のどの Stage を変えたのか、後続 invalidation があるかを隠さない
- HITL では「できること」だけでなく、`この OK に含まれないこと` を上部に出す。制限事項は説明文に埋めず、scope / AC、実装、自走、検証の 4 区分で `人間に戻す条件` と一緒に表で示す
- `現在地` は state.md / tasklist.md / requirements.md / design.md を根拠に書く。tasklist.md がまだ無い planning 初回停止では、残タスクを捏造せず「承認後に task-breakdown で作成」と明示する
- ユーザーが言った完了条件は requirements.md の AC にそのまま写されている（trace 表は作らない。正本: `references/requirements-template.md` § 精度の第一原則）
- Human Check Questions は requirements 側の記録名。human-check では `承認ポイント` として表示する。requirements の質問を別セクションとして二重表示せず、ユーザーが yes/no / 修正依頼で答えられる自然文で書く（§ 判断の書き方）
- ユーザーの完了条件を変換・延期・削除した場合（丸め・deferred・非スコープ送り）は、該当する承認ポイントか `やらないこと` で人間に見えるように出す。維持したもの（kept 相当）は表示しない
- unit test / contract test の全件一覧は HITL に出さない。人間に承認してほしいのは「どの完了条件をどの観測可能な claim として扱うか」「E2E / 外部証跡に残す境界が妥当か」だけに絞る
- `技術スタック確認` は dependency 一覧や実装詳細レビューではない。vendor official integration とのズレ、既存 repo 標準からの逸脱、MCP / CLI / SDK / API 等の access method、credential backend、multi-tenant 境界、後戻りが高い採用技術だけを表示する
- `実装技術スタック` は、人間が「どういう技術スタックで実装するか」を承認するための表である。language / runtime、framework / library、test tooling、access method、credential backend を中心に、既存 repo 標準・公式統合・credential / tenant 境界に関わるものだけを出す
- 後戻りが高い技術判断とは、access method / credential backend / tenant boundary / official integration / existing repo standard のいずれかを変える判断、または一度実装すると wide refactor・認証情報移行・運用手順変更・テスト証跡再作成が必要になる判断を指す
- 公式統合があるのに direct API / CLI wrapper / 独自実装を採る場合、または credential backend（Secrets Manager / SSM / env / OAuth 等）や tenant 切替方式が未確定の場合は、必ず `技術スタック確認` または承認ポイントに出す
- `作り方の重要判断` は repo 分割、既存仕組み再利用 vs 新設、import vs recreate、public vs private、CI/CD の載せ方など、後戻りが高い作り方の判断だけ表示する。ファイル単位計画や細かな設計は design-gating に送る

### 判断の書き方

human check の判断ポイントと、人に判断を求めるほかの出力（停止本文・完了報告の問い。`references/output-format.md` § Human-Facing Conversation Contract の「人間にお願いしたいこと」）に当てる。長さの上限では決めない。決めるのは、全段落が判断の材料になっているかである。GDD のほかの文書（skill・reference・テンプレート）の行数や「短く」の指示は、3 の筋書きと選択肢ごとに残るものを削る理由にしない。
1. **判断ポイントに置くもの**: 人が自分の持つ情報で決められ、選び方で後戻りが変わるものだけ。内部の処置（ライブラリの設定値、レビュー指摘の閉じ方、lint の値）は AI が決め、`現在地` か artifact に 1 行で書く。規則が人の判断を求める内部の処置（上限で残った指摘を既知のリスクとして受け入れるなど）は、細部ではなく、受け入れると何が起こりうるかで書く
2. **冒頭**: 最初に前置き 3 行を置く。`**依頼**:`（`request.md` の初めのユーザーの発言を言い換えずに引用。長いときと、`依頼との差` の語を含むときは、その部分を「…」で切る。複数の行にわたる発言も、`**依頼**:` の 1 行に収め、引用の行を分けない）、`**なぜやるか**:`（解決する問題・根本原因を 1〜2 文）、`**現在地**:`（どの工程まで済み、この返事で次に何が始まるか）。続く 1〜2 文で、決めてほしいことの数と、それぞれ何を決めるかを書く。一次表示では `### 判断ポイント` を冒頭の直後に置く。人は複数のセッションを行き来し、確認を読むのは表示から時間が経ってからなので、前の発言を読んだ前提で書かない。確認の出し直し・経過報告の末尾の問い・相談役の推奨の追記でも前置きを毎回書き、「内容は前回と同じ」「止める点 1・2・4」のように前の発言を指して中身を省かない。前置きは行数の目安を超えても削らない
3. **判断ごとの流れ**: いまの状態（ルール・挙動）→ 分かったこと（事実と出所）→ 何が起こりうるか（どの入力・操作で何が起き、誰にどの影響が出るか。よくある場合と最悪の場合を分ける）→ 選択肢（それぞれ何をして、何が残るか）→ おすすめと理由。承認ポイントの 8 要素は、この流れで書いた文を指して短く書き、言い換えて繰り返さない
4. **一次表示から外すもの**: 判断に効かない段落（変更予定ファイルの全列挙、レビューの経緯、内部の処置の細部、相談役との往復）。レビューの指摘・未確認の点などは、件数と場所の 1 行にする。案の選び方を分ける点は、一覧にせず、各案で何が残るかの文の中に書く（悪い例: 指摘 10 件を記号つきで全部並べ、決めることは「直すかどうか」1 つだった）。判断ポイントと OK の範囲のほかは、`詳細:` の 1 行で場所を指す。判断に効くもの（新しい権限・公開面・削除など）は、判断ポイントの材料か OK の範囲に書く。条件付きの節（`選択肢の説明`・`アーキテクチャ選択`・`Multiple PR Strategy Options`・人に残ったズレ確認・段階が 1 つだけのときの段階実装）は、当たらなければ節ごと書かず、`<gdd-hitl-fields>` の値を `none` にする。同じ話を節ごとに書かない。判断ポイントに書いたこと（段階・PR の分け方・自走の範囲）は、ほかの節では判断ポイントの番号を指す 1 行にする。行数の目安を超えるときは、この段落から外し、3 の筋書きと選択肢ごとに残るものは削らない
5. **内部 ID・略語**: 記号のまま残してよいのは次だけで、それ以外の内部の記号・番号・識別子（指摘・質問・task・ADR の番号、`request-crosscheck.md` の行の `#`、run の名前、内部フィールド名など）は、判断に使うときも中身の言葉にする（例: `要件レビューで決めきれなかった、再試行の回数の指摘`。場所が要るなら `reviews.md` Round 2 のように artifact を指す）。(a) 人が返事で使う呼び名: `AC-n`（初出で意味を書く。例: `AC-3（再試行の回数の上限）`）、Stage ID（初出で意味を書く。`段階実装案` の表の外で使うときも同じ。表は `lint-hitl-stage-plan.py` が読む）、選択肢・案の名前。(b) 機械が読む行: `<gdd-hitl-fields>` タグと `<gdd-stop>` marker。(c) 人が文そのものを承認する `references/confirmed-text.md` の block の中（置き換えずにそのまま出し、記号の説明は block の外に書く）。判断に使わない呼び名は出さない。main は subagent の下書きを表示する前に、この置き換えをする。置き換えるのは記号の表記だけで、判断ポイント・選択肢・承認の境界は変えない
6. **ラベルだけの項目を置かない**: 項目ごとに、何が・なぜ・影響を書く。悪い例: `レビュー bot が出した 2 件の確認`・`承認の水準を下げた`（何の承認が何から何へ変わり、その結果何が通るようになったかが無く、聞き返された）。良い例: 前と今の規定を並べ、検索キーを足す具体的な場面で、何が軽くなり、何がまだ防げないかを書く
7. **上限で止まる提示**: Round 上限の一括提示では、残った指摘と依頼の未達を生んだ設計の決定・前提を名指しして変える案を選択肢に加える。すべての選択肢を、依頼を満たすか・原因が消えるかで比べ、推奨は依頼を満たし原因を消す案を優先する。変える案が無いときは、無い理由を書く。ほかの上限（修正の回数など）で止まるときも同じにする。方式転換の選択肢では案の数を増やさず、再設計の案でこの決定・前提を名指しする（正本: `references/requirements-gating-steps.md` § レビューループの契約 の 1、方式転換は `references/rollback-patterns.md`）
8. **OK の中身を 1 つにする**: 冒頭の最後に、OK が何を決めるかを案の名前だけで閉じた 1 文を書く（例: `OK は、1 を (b)、2 を (3) で進めるという意味です`）。相談役が案に足すことを勧めたら（表示の後に届いた推奨を含む）、main が取捨を決め、取るものを推奨案の文に書き込む。`案 + 追加 N 点` の形で見せず、取らなかった追加は `相談役の推奨:` の食い違いに書く。追加が承認の境界か選択肢を変えるなら、推奨案に混ぜず、別の選択肢か判断ポイントとして出す。表示した後に推奨案を変える・足すときは、差分を積まず、全文を出し直す（相談役の推奨が届いたときに出し直すかは、一次表示の原則 7 と § 止まり直さないもの 2）

**Why**: 2026-10-15 にユーザーが評価した例（GDD を使う repo のセッション）。読みにくいとされた長文は節を全部埋め、内部 ID が多く、`### 判断ポイント` は本文の後半にあり、2 つ目は人が決められない再試行の設定の処置だった（返事は「OK」だけ）。分かると評価された長文は判断ごとに 3 の流れで書き、内部 ID は少なかった（返事は「おすすめでよい」）。短すぎて分からないとされた文はラベルだけで、「影響を教えて」と聞き返された。2026-11-09 に読みにくいとされた human check は、案が 1 つの節にも `選択肢なし` の行があり、指摘の id と run の名前が残り、OK の中身が `案 + 相談役の追加 7 点` の 2 層で、本文を読み比べないと分からなかった。2026-11-13 にユーザーが「聞きたいことだけ聞く感じになっている」「コンテキストが無いと人間は何のために何を判断するかがわからない」「長すぎてよくわからない場合もある」と言った。11-12 に一次表示から目的と要件を外した後の確認（出し直しで「内容は前回と同じです」と書き、判断ポイントは記号の案名だけだった）への返事は「そもそも何を実装する？要件は？」で、その前にも「何のための実装？」「判断 2 がわからない」「案 C がわからない」と聞き返されていた。同じ時期の確認は 3,800〜9,700 字で、指摘を記号つきで全部並べていた。前置き 3 行と 4 の列挙の扱いは、この 2 つ（文脈の欠けと長さ）に当てる

### 承認ポイントの粒度

- `Summary Brief` の「承認ポイント」は summary の言い換えではなく、人間に yes/no で決めてほしい policy question だけを書く
- 各承認ポイントには **変更前 → 変更後**（何がどう変わるか）を含め、人間がコンテキストを遡らずに判断できるようにする
- 原則 **1 項 1 判断** で、誰が / 何が変わるか / 何を承認してほしいかが読み取れるようにする
- 承認ポイントは方向性承認を除いて **2 件以内** を目安にし、AI が決められるものは AC に落とす。requirements.md の承認ポイントは事実を書き直さず `AC-n` を引き、HITL の一次表示では AC の値に `AC-n` を添えて言い換えない（正本: `references/requirements-template.md` § 事実は AC に 1 回だけ書く）

### 止まり直さないもの

`<gdd-stop reason="human-check-waiting">` は、人が選べる案が残っている確認と、本人の承認が要る停止点（要件の承認の OK の範囲。下の 1 の 0 件のとき）を出すときだけ付ける。次のときは、判断ポイントにせず、確認を出し直さない。state.md の `Resume From` が `human-check-waiting` のまま、マーカーを付けない出力で終わると、Stop hook はそのまま止める（`hooks/scripts/gdd_stop_hook.py` の markerless の扱い。「次に進みます」のような続ける意図の文を書くと押し返される）。承認の書き込みを検査する hook は、最後に表示した確認を直前の提示として読む。表示の前に `human-check-draft.md` へ `scripts/lint-hitl-decision-fields.py` を当て、落ちたら直してから表示する（`依頼との差:` の欄の不良となし以外の点は、確認を出した Stop で request-diff の hook〔`hooks/scripts/lib/request_diff.py`〕が block し、出し直しになる。lint 自体は Stop hook で記録だけで止めない）。なし以外のときは、推奨を依頼より狭くせず、狭める案を `採用しない案:` に変わる AC を書いて並べる（人が名指しで選べば、その返事で決まる。`commands/gdd-dev.md` #10 STEP 1 の「明確な承認」）。確認を出した後の追記（相談役の推奨・質問への回答など）にはマーカーを付けない。付けると、その追記が確認として読まれる。

1. **案が実質 1 つの判断**: ほかの案が、依頼を満たさない、すでに決まったこと（本人の返事・事前回答・承認済みの AC）に反する、結果が推奨と同じ、のどれかに当たるとき。ただし、推奨の案が依頼より狭い（`依頼との差:` が `なし` でない）ときと、§ 事前回答 3 の人に戻す条件に当たるときは、この 1 に当てず、判断ポイントにする。推奨の案で AI が決め、決めたことと、ほかの案を退けた理由を `現在地` か artifact に 1 行で書く。退けた案を `採用しない案:` に並べて判断ポイントを作らない。判断ポイントが 0 件になった human check は、OK の範囲（どこまで自走するか）を 1 つの判断ポイントにして出す（`承認ポイント数: 1`。承認の hook は判断ポイントが 0 件の確認を、`依頼との差:` の欄が無いとして拒否する）。Round 上限の一括提示でも、同じ基準で判断ポイントにするかを決める（§ 判断の書き方 7 の、原因を変える案は、依頼を満たすなら現実の案に数える）。一括提示で判断ポイントが 0 件になっても（現実の案が「修正」だけのときも）、上限を越えて自分で修正を続けない。止まって、推奨の案で再入してよいかを 1 つの判断ポイントにして出す
2. **相談役の推奨が、表示した推奨と同じとき**: 2 本がそろって返り、どちらも判断ポイントごとに表示した推奨案と同じ案を推し、止めるべきと答えず、main が推奨案に書き込む追加も無いとき。全文を出し直さず、マーカーを付けずに「相談役 2 本の推奨も、表示した案と同じです」と 1 行だけ書く。推奨案を変える・足す、2 本が割れる、表示した推奨と違う案を推す、止めるべきと答える、のどれかなら、一次表示の原則 7 のとおり全文を出し直す
3. **本人が答えた判断**: 本人が選んだ案を AC に書き写した結果や、言い直した文を、もう一度判断ポイントにしない。承認するか・修正指示として扱うかは `commands/gdd-dev.md` #10 STEP 1 の「明確な承認」の行で決める。承認に入る名指しは、点の番号と表示した案の名前の組（「1 は B、2 は推奨で」）で全点に答えた返答と、点が 1 つの確認での案の名前だけの返答に限る。点が 2 つ以上の確認で点の番号の無い名指し（「B で」「2 で」）は、承認にも修正指示にもせず、「どの点を何にしますか（例: 1 は B）」の 1 行だけで聞き返す（§ 曖昧返答の検出の再質問テンプレートは使わない。選んだ案が消えるため）。承認の語や名指しのほかに文がある返答は、承認に入れない。変更・条件なら修正指示とし（「1 は B、2 は推奨で。あと 2 の対象に X も」、1 点の確認で「B で。ただしタイムアウトは 30 秒に」）、名指しした点は決定済みの 1 行と `依頼との差:` で残す。変更でない文（質問など）なら、答えてから承認するかを聞き返す。一部の点だけを組で答えた返答では、答えた点を決定済みの 1 行と `依頼との差:` だけにし、`承認ポイント数:` は元の数のままで、答えていない点だけを判断ポイントにして出し直す。表示に AC の変更を書いた案（`採用しない案:` に並べた、依頼を狭める案を含む）の名指しは承認に入れ、発言を `request.md` に足して requirements.md に書き写し、requirements-gating を 1 Round 回す。blocking の指摘で表示した案の中身が変わったときだけ再提示する。
4. **質問への回答・状況報告**: 表示済みの確認について、質問や「残りは？」に答えるとき、答えで判断ポイントの中身（案・推奨・OK の範囲）が変わらなければ、確認を再掲せず、マーカーも付けない。変わったら全文を出し直す。問いの無い報告にマーカーを付けない

**Why**: 2026-11-09〜13 の main の `human-check-waiting` の停止 111 件（fork の重複を除く）のうち 48 件は、人が選べる案が実質無かった。案が実質 1 つの判断 14 件、相談役の推奨が表示と同じなのに全文を出し直した 11 件、承認の hook が欄の形で拒否した出し直し 12 件（本節の外。表示の時点の検査で直す）、答えた判断の聞き直し 5 件、質問への回答に再掲した 5 件、AI が決められる処置 1 件（2026-11-13、依頼「ほぼ選択肢がない状態でもHITLで止まることがルール上ある」）

### 判定ルールの書き方

- `unknown -> needs_input` のような内部遷移だけでは書かない。必ず「どの条件なら」「何の入力を見て」「どの出力・応答にするか」を自然文で書く
- 判定ルールは少なくとも `条件` / `見る入力` / `出力または次アクション` / `不足時の扱い` の 4 点が読めるようにする
- 悪い例: `unknown は needs_input に倒す`
- 良い例: `service metadata の信頼度が unknown、または PRD / non-PRD 判定に必要な証跡が不足している場合は、自動受理せず needs_input を返して人手確認に止める`

### scope 必須項目

以下が scope にある場合は、それぞれの承認事項を「承認ポイント」に**必ず**含める:
- route / ownership
- secret handling / masking
- rollout / rollback
- 自走上限（実装完了 / PR 作成 / デプロイ準備 / デプロイ実行）

上記カテゴリに関する blocking `Open Questions` が残っている場合は `human-check-waiting` に進めない。

### 承認ポイントの位置関係

- `Summary Brief` は `Design Policy Discussion` の前に置き、人間が要約を先に読めるようにする
- `Summary Brief` の「一言」で対象と目的、「判断材料」で確定/未確定/非スコープ/外部依存/設計方針が読めること
- `Design Policy Discussion` は「承認ポイント」の判断根拠として、人間が設計方針を先に見てから承認判断できる位置に置く
- 「参考」は折りたたみ的な位置づけ。承認ポイントの判断に必要な情報はすべて承認ポイント内に書く

---

## 含めるべき情報の写像

`requirements.md` / `design.md` の各情報をテンプレートのどこに配置するか:

| 情報 | テンプレートの位置 |
|------|-------------------|
| なぜやるか（WHY・根本原因） | **冒頭の前置きの `**なぜやるか**:`**。WHY が WHAT と HOW の判断根拠になるよう最初に配置する |
| 対象 steering / artifact | 参考 > 詳細 |
| 実装内容・変更内容の要約 | やること |
| state.md / tasklist.md / requirements.md / design.md から分かる workflow 状況 | 前置きの `**現在地**:` と、OK の範囲の `今やること:`・`OK後:` の行（ここまで出来ていること・残タスクは `state.md`） |
| Summary Brief（一言 / 判断材料 / 承認ポイント + Honest Limitations） | やること + まず見るところ + 前提 + 承認ポイント（Honest Limitations は `まだ確認できないこと` と参考欄にも写す） |
| Honest Limitations / Open Questions / 外部証跡不足 | まだ確認できないこと（Not Verified Yet） + 必要なら前提 > 非スコープ |
| Approved Direction / safety boundary / recheck trigger | 人間に戻す主な条件（Top 3 Stop Conditions） + この OK で許可すること / 許可しないこと |
| Design Policy Discussion / Options Exploration | 選択肢の説明（Option A / B / C の意味、採用案、採用理由、却下理由。未定義の Option ラベルは禁止） |
| 受入条件（ユーザーの完了条件を写した AC） | 承認ポイント（変換・延期・削除した完了条件だけ。維持したものは表示しない） + 検証計画（どこで確認するか / どう確認するか / OK条件 / 失敗時の扱い） |
| AC の開いた入力の扱い（構造で閉じる / なし / 列挙に縮める / 限界として開示する） | `構造で閉じる` は採った設計を、`列挙に縮める` は対象パターンと列挙外の既定挙動を承認ポイントに含める。`限界として開示する` は まだ確認できないこと（Not Verified Yet） |
| 採用技術スタックの結論（実装方針） | ズレ確認 > 技術スタック確認（採用する技術スタック / 公式統合 / 既存標準 / access method / credential backend / tenant 境界だけ） + 実装技術スタック（language / runtime、framework / library、test tooling、access method、credential backend） |
| コードベース健全性の finding | ズレ確認 > コードベース健全性確認（巨大ファイル / 依存管理 / test baseline / CI baseline のうち、設計・タスク順序・検証へ影響するものだけ） |
| 実装方針の後戻りが高い論点 | ズレ確認 > 作り方の重要判断（後戻りが高い論点だけ） |
| Design Policy Discussion | 前提 > 設計方針（採用案を 1 行で） + 承認ポイントの AI の仮決定 / 根拠 / 却下した代替案 |
| 変更範囲と利用者影響 | 参考 > 変更範囲 |
| リスク / 注意点 | 参考 |
| ロールバック方針 | 参考 |
| 検証方針 | 参考 |
| 未解決の質問 / 仮定 | 前提 > 非スコープ or 承認ポイント |
| 何の承認を求めているか | 承認ポイント（全文） |

---

## 具体例

CI Gated PR Open タスク（standard）での出力例:

```markdown
## 🔍 確認

**依頼**: 「CI が通ってからレビューに回して」
**なぜやるか**: PR を作った直後に reviewer が割り当てられ、CI が落ちたままの PR をレビューさせている
**現在地**: 要件の整理と承認ポイントの抽出は済み。OK で設計に進む

### 30秒判断（まず見るところ）

**整理した要件**: CI が通るまで Draft で待ち、通ったら open して reviewer を割り当てる。原文: 「CI が通ってからレビューに回して」
**判断ポイント**: 決めてほしいことは 2 つ。CI 成功の判定基準と、自動修復の上限（下の `### 判断ポイント`）
**実装する方法・内容**: 全 PR 作成ルートが共通の契約（`pr-ci-gate.md`）を参照し、既存の `AGENTCORE_WAIT_FOR_CI` で切り替える
**変更予定ファイル（WHERE）**: 新しい権限・公開面は無い。全列挙は `design.md` § 変更ファイル
**検証する方法・内容**: unit / contract テストと、実 PR での E2E smoke
**どこまで自走するのか**: PR 作成まで。merge / deploy / GitHub branch protection 変更 / 本番 write は含めない（迷ったら承認ポイント 1-3 とまだ確認できないこと）

### 判断ポイント
**OKで実装・検証すること**: 全 PR 作成ルートの共通契約、CI が通るまで Draft で待つこと、修復は 2 回まで
**OKしても今回は対象外のこと**: branch protection の変更、CI の高速化、レビュー基準の変更
**人間に決めてほしいこと**
1. **CI 成功の判定基準**: いまは CI の結果を見ずに open している。required checks（branch protection で merge の条件として必須にした CI check）はすでに定義があり、全 checks にすると optional な lint の失敗でも ready 化（Draft を通常の PR に切り替える GitHub API 操作 `ready_for_review`）が止まる。おすすめは required checks（判定基準を二重に持たない）。選ぶと、必須でない check が落ちていても PR は open する。相談役の推奨: Opus-1 required checks / Opus-2 required checks / 食い違い: なし
2. **自動修復の上限**: いまは CI が落ちると人が直している。この repo の CI の一時的な失敗は 5% 未満（直近の CI 実行履歴）で、1 回の修復では flaky test などに弱く、3 回以上では Claude API の費用と CI の時間が増える割に回復が増えない。上限なしでは修復が止まらない。おすすめは 2 回で、超えたら Draft のまま人に返す。選ぶと、3 回目で直るはずの失敗も人に戻る。相談役の推奨: Opus-1 2 回 / Opus-2 2 回 / 食い違い: なし

### やること
PR 作成後に CI が通るまで Draft で待機し、成功後にだけ open して reviewer をアサインする仕組みを全 PR 作成ルートに共通で入れます。CI 失敗時は自動修復を最大 2 回試み、上限超過なら Draft のまま返します。

**タスクサイズ**: standard — 5 ルート共通の契約変更・外部 API 呼び出し方式変更を含むため
**フロー**: 要件整理 → 要件レビュー → 人間確認 → 設計 → 設計レビュー → タスク分割 → TDD → 実装レビュー → 完了チェック
**通過予定 gate 数**: 4 gate（req-gate → design-gate → impl-gate → completion）
**自走上限**: PR 作成まで。merge / deploy は別承認

### 承認サマリ
- **人間が今だけ判断すること**: 判断ポイント 1・2 と、自走上限を PR 作成までにすること
- **OK で許可される最大到達点**: PR 作成まで
- **OKでも許可されないこと**: merge / deploy / GitHub branch protection 変更 / 本番 write

### 人間に戻す主な条件

Top 3 Stop Conditions:
- CI 成功判定を required checks 以外に広げる必要が出た場合
- GitHub API の access method、credential backend、PR route ownership を変える必要が出た場合
- merge / deploy / branch protection 変更など、自走上限を超える操作が必要になった場合

### まだ確認できないこと

Not Verified Yet:
| 未確認事項 | 今回の扱い | 確認タイミング / 人間に戻す条件 |
|---|---|---|
| 実 PR での CI 待機から ready_for_review までの end-to-end 挙動 | external evidence required | 実装後の E2E smoke で確認。GitHub 側制約で再現不能なら人間に戻す |

### この OK で許可すること / 許可しないこと

| 区分 | この OK で許可すること | この OK に含まれないこと | 人間に戻す条件 |
|---|---|---|---|
| scope / AC | CI green まで Draft 維持し、成功後 ready_for_review する契約追加 | branch protection 変更、レビュー基準変更、CI 高速化 | AC の意味や対象 route を変える場合 |
| 実装 | 既存 GitHub API client と `AGENTCORE_WAIT_FOR_CI` を使う | credential backend 変更、独自 GitHub client 新設 | access method / credential backend / route ownership を変える場合 |
| 自走 | テスト・実装・PR 作成まで | merge / deploy / GitHub 設定変更 / 本番 write | 自走上限を超える操作が必要な場合 |
| 検証 | unit / contract / E2E smoke を実施 | 実運用 PR 全ルートでの長期観測 | E2E smoke 不可、外部証跡不足の場合 |

- 今やること: 承認ポイント 1-3 への返事（OK / N は変更 / 全面見直し） / OK後: design-gating → task-breakdown → TDD → 実装 → implementation-gate → completion-check → PR 作成

### 前提
| 項目 | 内容 |
|------|------|
| 確定 | Draft PR → CI 待機 → green で ready_for_review。既存の `AGENTCORE_WAIT_FOR_CI` フラグで制御 |
| 非スコープ | branch protection 変更、CI 自体の高速化、レビュー基準の変更 |
| 外部依存 | GitHub API（`ready_for_review` 切り替え）、既存の `github-api` Lambda |
| 設計方針 | shared reference（`pr-ci-gate.md`）に共通契約を集約し各 skill はそれを参照するだけにする |

### 承認ポイント
承認ポイント数: 2
**1. 修復ループの上限**
- **AI の仮決定**: 自動修復は最大 2 回、上限超過なら Draft のまま返す
- **根拠・却下した代替案**: 判断ポイント 2 のとおり（上限 1 回・上限なしを却下）
- **判断に影響する前提**: CI の flakiness が現状同等（5% 未満の一時失敗率）。flakiness が悪化したら上限再検討
- **依頼との差**: なし

**2. CI 成功判定の基準**
- **AI の仮決定**: `required checks` が全て成功した時点で CI 成功と判定し ready 化
- **根拠・却下した代替案**: 判断ポイント 1 のとおり（全 checks 成功を却下）
- **判断に影響する前提**: 現行の branch protection が維持される。required checks の定義変更があれば再検討
- **依頼との差**: なし

**3. 方向性**: 自走範囲は判断ポイントの「OKで実装・検証すること」、自走上限は `### やること`、人間に戻す条件は `### 人間に戻す主な条件` のとおり
```

---

## 事前回答（表示前に本人が答えたもの）
ユーザー本人のターンの発話で、まだ表示していない human check（同じ steering の後の human check と、後続 Stage の steering の human check）について先に答えたものを事前回答という（例：「S-1〜S-3 は自走上限をマージまで、merge ごとの確認は不要、判断は Fable に相談して進め、ゴール未達・要件を満たせない見込みのときだけ人に戻して」）。表示した human check で本人が選んだ判断の委任（§ 自走上限の置換値の「判断の委任」）も、後の human check への事前回答として同じ行に記録する。cross-session messaging で届いたもの（§ 返答分類の判定基準の権限境界）と、エージェントが会話から推し量ったものは事前回答にしない。委任先の相談役が判断する手順は `references/autonomy.md` にある（repo 単位の宣言は無い）。この節が事前回答の記録・適用・委任した判断の記録・人に戻す条件・後続 Stage の着手の合図・承認後の引き上げ（5）の正本である。
1. **記録**：受けたターンに、main がその steering の `worklog.md` に 1 行書く（subagent のターン・cross-session のターンでは書かない。発話は `request.md` にも足す〔あれば。`references/brainstorming-steps.md` 9 の (1)〕）：`事前回答: <ISO 8601> / 対象: <Stage ID をカンマ区切り | この steering> / 自走上限: <§ 自走上限の置換値の 1 つ> / 委任先: <fable | opus | 並行 | なし> / 人に戻す条件: <本人の言葉> / 原文: 「<本人の発話の該当部分>」`。委任先は、本人が model を名指ししたらその値（`fable`・`opus`）、名指しせずに相談役に任せると言ったら `並行`（`gdd-opus-advisor` に 2 本並行で相談する）、任せないなら `なし` にする。名指しを `並行` に替えない。表示した human check での判断の委任の選択は、この行には書かず、承認の時点で `Approved Direction` の `判断の委任` の欄に書く（§ 自走上限の置換値）。表示中の human check への返事に含まれた事前回答は、その human check には適用しない（承認は本人の返事で行う）。自走上限は置換値の表の値をそのまま書き、「merge ごとの確認は不要」などの補足は値に付けない。本人の言葉がどの値に当たるか決められないときは事前回答として扱わず、通常どおり human check を表示する
2. **適用**：対象の human check に着いたら、表示せずに次を行う。この steering の `Approved Direction` に `判断の委任` の欄があれば、委任先はその欄の値で決める（`人に止める` なら適用せず表示する。欄は本人の承認と 5 の発話で書いた現在値なので、原文の照合をしない）。欄の値が委任なら、`事前回答:` 行が無くてもこの節の手順で扱い、記録の行の 1 欄目と `対象:` は下と同じに決める。欄があるときも、`事前回答:` 行の `人に戻す条件` は 3 のとおり効く。欄が無ければ、下の `事前回答:` 行で決める。適用できる行は、main が `原文` を会話の本人のターンの発話と突き合わせ、行の各欄（対象・自走上限・委任先・人に戻す条件）がその原文から読めると確かめられた行だけである。4 で写した行も同じで、写し元との照合だけでは適用しない。原文が表示した判断の委任の行と本人の返事の組（1）なら、前半は main が表示した行と、後半は本人のターンの返事と突き合わせ、`対象` は `この steering`、`委任先` は返事が 4 値（§ 自走上限の置換値の「判断の委任」）のどれに当たるか、`人に戻す条件` は 3 の一覧と読む。原文が触れていない欄は、委任先は `なし`、人に戻す条件は 3 の一覧だけと読む。原文が自走上限に触れていない行（1 の組の原文の行と、5 の判断の委任で書いた行）は、`自走上限` の欄を照合に使わず、適用の時点の `state.md` の `Approved Direction` の `自走上限` をこの行の自走上限として読む（承認の後に 5 で引き上げ・引き下げたときは、変えた後の値に従う。3 の「事前回答の自走上限より先へ進む」もこの値で判定する）。確かめられないとき（compaction の後や別のセッションで発話が見えない、`原文` が無い、該当する発話が無い、欄が原文から読めない）は、`事前回答の適用: <human-check | human-recheck> / 対象: <承認ポイントの番号 | Current Task の id> / 採った案: 適用しない（原文を確かめられない） / 委任先の推奨: なし / model: なし`（1 欄目と `対象:` は下の記録の行と同じ決め方）を書き、行が無いときと同じに扱う（表示する）。表示するときは冒頭で、事前回答を適用できなかったことと、言い直せば記録し直すことを伝える。判断が要る承認ポイント（PR の分け方・許可する欄名・ガードの置き場など）は委任先に聞く（`references/autonomy.md` 判断の手順。下の行の `model:` の欄は、代わりの経路なら `<実際の model ID>（effort: main から継承）`、`並行` なら 2 本を `, ` で並べ、`委任先の推奨:` も `Opus-1 <案>; Opus-2 <案>` と並べる。委任先が `なし` なら承認ポイントの AI の仮決定を採る）。判断ごとに `worklog.md` に `事前回答の適用: <human-check | next-stage | human-recheck | requirements-round-limit | design-round-limit | completion-round-limit | pre-pr-fix-limit | remediation-loop-limit | followup-redesign-2nd> / 対象: <承認ポイントの番号 | Stage ID | Current Task の id> / 採った案: <案> / 委任先の推奨: <案 | なし> / model: <実際の model ID | なし>` を書き（`human-recheck` は Downstream Human Recheck Handoff〔`references/rollback-patterns.md`〕で着いたときで、`対象:` は `Current Task` の id。requirements・design の Round 上限で残る blocking の一括提示〔`references/requirements-gating-steps.md` § レビューループの契約 1。Round の記録が無いときを含む〕は、その順に `requirements-round-limit`・`design-round-limit` と書き、`対象:` は一括提示した `Human Check Questions` の番号にする。上限での方式転換の提示〔`gdd-completion-check` の Round 上限超過、`Pre-PR Fix Attempts` の上限〔`references/independent-review.md` の (3-f) の取り直しの上限を含む〕、Remediation Loop Safety の上限、`gdd-pr-review-followup` の同じ PR での 2 回目の設計し直し〕は、`human-recheck` ではなくその順に `completion-round-limit`・`pre-pr-fix-limit`・`remediation-loop-limit`・`followup-redesign-2nd` と書く）、承認したら、行の末尾に ` / 承認した変換: <「完了条件の変換」表の行（初期条件 → 変換後、扱い）。複数なら ; で区切る | なし>` を足す（`references/autonomy.md` 判断の手順 4 と同じ。completion-reviewer が承認の記録として読む）。理由を長く残すときは `reviews.md` の `## Human Check 代行判断` 節に書く（相談役の `範囲を広げる提案:` があれば同じ節に写す）。requirements・design の一括提示で採った案は `references/requirements-gating-steps.md` § 一括提示への返答 のとおりに進める。ほかの承認は `commands/gdd-dev.md` Instructions #10 STEP 2 を行い（`Route In Progress=none` のクリアと `Resume From` の更新を含む）、`Human Check Status: approved | evidence: human:<自走上限の値>` にし、`Approved Direction` の `自走上限` も同じ値にする。STEP 2 で記録し直す `Approved Direction` の人間に戻す条件は、前の項目を消さず・書き換えず、足すことだけをする（消す・緩める必要があるときは、承認せずに人に戻す）。どちらにも補足を付けない（`references/post-merge-qa.md` 手順 2 は両者の完全一致で本人の承認を判定する。Write・Edit・MultiEdit で書くと、steering の書き込み hook が書き込み後の state.md を見て、自走上限か `human:` の evidence の値が自走のマージを指しうるとき（注記付きの `PR マージ後検証 / 再学習まで` を含む）、`post-merge-qa.md` § 入口と手順 2 の形〔1 行・`- 自走上限: <値>`・表の値・完全一致・承認前〔`pending`・`changes_requested`〕でない status の evidence が `human:` で始まる〕を満たさない理由を additionalContext で返す。書き込みは止めないので、受けたらこの記録の続きの書き込みで直す。返すのは自走上限と `Human Check Status` の行が変わった書き込みだけである。範囲を狭める条件なら値を `PR 作成まで` にする。hook が main に知らせない書き込み〔ApplyPatch（警告は利用者の端末にだけ出る）・Bash〕では、書く前に自分で値を確かめる）。事前回答による承認であることは `worklog.md` の行で区別する
3. **人に戻す条件**：委任したときに人に戻すのは、承認した要件（依頼の原文・AC・信頼境界・承認した契約）を満たせない、または満たさない方向に変えるときと、止まる側に倒す仕組みと、許可の境界だけである。それ以外の判断（依頼の範囲の中で AC・scope を足す・具体化する・強める、技術スタック・設計・policy・ownership を変える、確認に並んでいない案を採る、など）は委任先が決める。依頼の語より広げる AC・scope は、委任の下では採らずに止まらず進み、`範囲を広げる提案` として 2 の記録の節に書いて完了の報告と PR 本文で本人に示す（広げないと承認した要件を満たせないときは、下の「満たせない見込み」で人に戻す）。§ ズレ確認 の `記録の場所: なし` の行の扱いは、`references/post-completion-pr-flow.md` の Step 4 と Autonomy Decisions Check に従う。下の一覧の各項目はこの 3 つのどれかに当たる：承認した要件を満たせない見込みになった（同じ種類の上限に 2 回目、方式転換の「限界として開示」、上限で残った blocking の accept、Human Check Questions に移した安全境界の項目を含む）、要件が決まらない・判定できない（`clarification-needed`・AC の曖昧さ、原文を確かめられない、本人の新しい入力、委任先を起動できない）、許可の境界（自走上限、Codex の委譲、時間超過の「レビュー無しで承認」）。次のどれかに当たったら、委任先が何と答えても `事前回答の適用: ... / 採った案: 人間に止める` を書いて human check を表示する。承認した要件を満たせない見込みになった。scope・AC を削る・意味を変える。承認した信頼境界（認証・認可・入力検証・credential backend・tenant 境界）か承認した prompt-output contract を外す・緩める（足す・強めるのは委任先が決める）。一次表示の § ズレ確認 に、ユーザーの決めた規則・方針の側に仮決定した `既存とぶつかる` の行があり、その行を引用した本人の承認が `request.md` に無い（委任では承認の記録にならないため）。事前回答の自走上限より先へ進む、または `Post-PR Completion Scope` に自走上限の外の操作が入る。AC を削る・弱める、task を撤回する、steering を中止する、`planning_rework_required` に進む（上限で止まる提示で、依頼の読み方も AC も変えない前提を変える案を採って進むときを除く）、上限で止まる提示の、依頼の読み方か AC を変える案を採る、時間超過の一括提示で「レビュー無しで承認」を採る、方式転換の「限界として開示して人に渡す」を採る、上限（Round 上限・`Pre-PR Fix Attempts` の上限・`references/independent-review.md` の (3-f) の取り直しの上限）で残った blocking を accept as known risk にする、または `Request Drift` を理由にした `human_recheck_required` で、依頼に合わせて実装を直す以外の案を採る。requirements-gating で blocking から `Human Check Questions` に移した、安全境界に当たる項目（元の指摘 ID と接地条件を書いた項目。`references/requirements-gating-steps.md` § 精度の第一原則）がある。同じ steering で同じ種類の上限に 2 回目に当たった（`worklog.md` の `上限到達:` 行で数える。6 種の上限のどれかを理由に、方式転換の選択肢か Round 上限の一括提示で止まる遷移〔`Resume From=human-check-waiting` などを書く書き込み〕を書くたびに、その遷移を書く側〔subagent か main。gate runner の `gate結果:` 行と同じく、遷移を書いた側が書く〕が、同じ手順で `worklog.md` に `上限到達: <requirements-round-limit | design-round-limit | completion-round-limit | pre-pr-fix-limit | remediation-loop-limit | followup-redesign-2nd> / at: <ISO 8601>` を 1 行書く（語の決め方は 2 の `事前回答の適用:` 行の 1 欄目と同じ）。この行を書く前に、`references/requirements-gating-steps.md` § レビューループの契約 1 の前提の点検をし、`前提の点検:` 行も書く。誰が答えるか・事前回答の行があるかは問わない。`Resume From` がすでに `human-check-waiting` の state を表示し直すとき〔resume・compaction の後など〕は、遷移を書かないので行も書かない。委任先に聞く前に main が数え、同じ語の行が 0 本なら〔書き落とし〕、main がこの到達の行を書いてから止まり、今回の分を含めて 2 本以上なら 2 回目とする。`worklog.md` が読めなければ止まる）。`clarification-needed` と AC の曖昧さを理由にした停止（TDD の `needs_clarification` など）。Codex の subagent 委譲の判断点（委譲は `references/codex.md` § Codex Subagent Delegation Permission の明示委譲ソースか、表示した human check での本人の承認でだけ開き、`委任先: なし` の AI の仮決定でも委任先の判断でも承認しない）。適用中に本人から新しい入力を受けた（その入力を § 返答分類の判定基準で扱う）。事前回答の `人に戻す条件` か、承認した human check で `state.md` の `Approved Direction` に記録した人間に戻す条件に当たる、その人間に戻す条件の項目を消す・緩める必要がある、または対象に入っていない Stage・human check である。委任先を起動できない（`fable` を起動できないときも `opus` に替えない）、委任先が人に止めるべきと答えた、または `並行` の 2 本の推奨する案が違う（`references/autonomy.md` 判断の手順）。どれに当たるか判定できない（`state.md`・`worklog.md` が読めない、対象に入るか・上のどれかに当たるか決められない）。この一覧は閉じている。merge・deploy などの操作の承認の境界は § 自走上限の置換値と `references/post-merge-qa.md` のとおりで、事前回答は自走上限の値を決めるだけである
4. **後続 Stage の着手**：`段階実装案` の `このOKで承認する範囲` は、`後続PRの方針のみ承認`（方針だけ。着手には本人の明示入力か、Stage Continuation の発火〔`Continuation Mode=auto-after-clean`・`auto-stacked` を独立承認ポイントで選んだ Stage。`references/requirements-gating-steps.md`〕が要る）、`後続PR着手前に再承認`（マージ後に本人が「次に進んで」と言ってから着手）、`事前回答で後続PRも実施許可`（事前回答が着手の合図を代える。事前回答の `対象` にその Stage が入っているときだけ使い、独立した承認ポイントとして出す。`scripts/lint-hitl-stage-plan.py` が `follow-up-pr`・`post-merge-verification` の Stage で受ける）を使い分ける。この値の Stage は、先行 PR の post-merge verification が済み、元の `事前回答:` 行を 2 のとおり確かめられたら、「次に進んで」を待たずに着手してよい（確かめられなければ `事前回答の適用: next-stage / 対象: <Stage ID> / 採った案: 適用しない（原文を確かめられない） / 委任先の推奨: なし / model: なし` を書いて着手せず、停止の出力に `### 次の計画` を入れて「次に進んで」を待つ）。着手の時点で `worklog.md` に `事前回答の適用: next-stage / 対象: <Stage ID> / 採った案: 着手 / 委任先の推奨: なし / model: なし` を書く。着手の手順（latest default branch からの新しい worktree、新しい steering）は今までどおりで、新しい steering の `worklog.md` に元の `事前回答:` 行をそのまま写して末尾に ` / 写し元: <元の steering のパス>` を足し、`Approved Direction` の `自走上限` を同じ値で書く。元の steering の `Approved Direction` に `判断の委任` の欄があれば、新しい steering にも同じ値で書く（承認の後に 5 で下げた値も届く）。`Approved Direction` の人間に戻す条件には、写す時点の元の steering の `Approved Direction` の人間に戻す条件と、`Implementation Sequence Plan` のその Stage の行の人間に戻す条件を写す（`自走上限` の値は次の括弧のとおり。原文が自走上限に触れていない行〔5 の判断の委任で書いた行〕は、行の値と、写す時点の元の steering の `Approved Direction` の `自走上限` の狭い方で書く。`worklog.md` の履歴は読まない。狭い方は、同じ値ならその値、次の包含に当たる組なら含まれる側である：`実装完了まで` はほかのすべての値に、`PR 作成まで` は `PR 作成 + 外部レビュー収束まで` と `マージまで` に、`マージまで` は `マージ・デプロイ・QA まで` に含まれる〔包含は推移的に読む〕。この包含に当たらない組〔`デプロイ準備まで` と `マージまで` など〕と、元の値が読めないときは `PR 作成まで` で書く〔行の値か元の値が `実装完了まで` なら `実装完了まで`〕。元の steering の中の引き上げは行の値を超えて後続 Stage に届かず、引き下げは届く）。`Planned Follow-up Stage Lane`（`references/requirements-template.md`）では、この Stage の `Human Recheck` を `not required + 事前回答` と書く。新しい steering の human check は 2 で扱う（表示は省くが、判断と記録は省かない）。post-merge verification の後で止まるときは、今までどおり停止の出力に `### 次の計画` を入れる（`hooks/scripts/gdd_stop_hook.py` の done の検査が求める。手動のマージの後は `hooks/scripts/lib/post_merge_continuation.py` も求める）
5. **承認後の引き上げ**：human check の承認の後に、本人が自分のターンで次のどれかを言ったら、human check を表示し直さずに適用する（2026-10-03 ユーザー決定。承認の後に会話で許可しても、表示し直すまで止まっていた）。適用するのは発話が明示したものだけで、触れていないものは変えない。どの記録も、`原文` を会話の本人のターンの発話と突き合わせて確かめてから書く（確かめられなければ適用しない。下の引き下げ・取り消しは除く）。3 の人に戻す条件は今までどおり効く
   - **自走上限の引き上げ**：エージェント自身にマージ（やデプロイ）をさせる指示・許可（例：「マージも自律的にして良い」「CI が通ったらマージして」）。表の値に当てはめ、`Human Check Status` を `approved | evidence: human:<新しい値>` に、`Approved Direction` の `自走上限` を同じ値に、1 回の書き込みで書き換え、`worklog.md` に `自走上限の引き上げ: <ISO 8601> / <変更前の値> → <新しい値> / 原文: 「<発話の該当部分>」` を書く。表の外の言い方は値にそのまま書かない（例：「マージして検証まで」は、検証がマージ後の read-only の確認なら `マージまで`。デプロイ・QA の書き込みを含むなら `マージ・デプロイ・QA まで`。`マージ` を含み表の値でない値〔`PR マージ後検証 / 再学習まで` に注記を付けた値を含む〕と、自走上限がマージの値のときの、承認前〔`pending`・`changes_requested`〕でない status の `human:` で始まらない evidence は、steering の書き込み hook が 2 の注記と同じく知らせる）。誰がマージするかが読めない発話（「マージしたら次に進んで」は本人がマージするとも読める）、表の値に当てはめられない発話は引き上げず、マージの時点で今までどおり Merge Approval を 1 問で問う。`マージ・デプロイ・QA まで` に引き上げるときは、`references/post-merge-qa.md` § QA の範囲を本人に 1 問で問い、答えを同じ節の行で記録する（範囲が無いうちは自走でマージしない）。条件を付けた許可は、その条件をマージの経路が確かめるとき（CI・required checks が通る、レビュー指摘の対応が済む、指摘が無い）だけ引き上げる。時刻・他人の承認・外部の出来事など、経路が確かめない条件を含む発話は引き上げず、マージの時点で Merge Approval を 1 問で問う
   - **引き下げ・取り消し**：承認の後に本人が自分のターンで、エージェントにマージ（やデプロイ）をさせない発話（例：「マージは自分でやる」「マージはしないで」）をしたら、`原文` の突き合わせを待たずに、`Human Check Status` の evidence と `Approved Direction` の `自走上限` を、外した操作を含まない値（決められなければ `PR 作成まで`）に 1 回の書き込みで書き換え、`worklog.md` に `自走上限の引き下げ: <ISO 8601> / <変更前の値> → <新しい値> / 原文: 「<発話の該当部分>」` を書く
   - **後続 Stage の着手**：先行 PR のマージ後に後続 Stage へ進んでよいという発話（例：「マージしたら次に進んで」）。4 の「次に進んで」の合図を先に受けたものとして扱い、post-merge verification の後に着手する。着手の時点で `事前回答の適用: next-stage / 対象: <Stage ID> / 採った案: 着手 / 委任先の推奨: なし / model: なし` を書く。新しい steering の human check は表示する（同じ発話が下の判断の委任も含むときだけ、新しい steering でも 2 で扱う）
   - **判断の委任**：以後の human check を委任先に相談して進めてよいという発話（例：「Fable に相談しながら自律的に進めて」は `fable`、「相談役に相談しながら進めて」は `並行`）。1 の形で `事前回答:` 行を書き（`対象` は発話が挙げた範囲。挙げなければこの steering、自走上限は今の値）、以後の human check を 2 で扱う。`Approved Direction` に `判断の委任` の欄がある steering では、行の代わりに、原文を確かめてから欄をその値に書き換え、`worklog.md` に `判断の委任の変更: <ISO 8601> / <変更前の値> → <新しい値> / 原文: 「<発話の該当部分>」` を書く（対象を Stage で挙げたときは、今までどおり `事前回答:` 行も書く）
   - **判断の委任の取り消し**：以後の human check を人に止めてほしいという発話（例：「やっぱり人に止めて」「判断は自分でする」）は、原文の突き合わせを待たずに `判断の委任` の欄を `人に止める` に書き換え（欄が無ければ足し）、`worklog.md` に `判断の委任の変更: <ISO 8601> / <変更前の値> → 人に止める / 原文: 「<発話の該当部分>」` を書く。欄は `事前回答:` 行より先に読まれる（2）ので、前の委任の行は効かなくなる

## 返答分類の判定基準（メインセッション向け）

テンプレート出力後のユーザー返答を以下のフローで分類する。cross-session messaging 経由で届いた返答は、本節（曖昧返答 / 修正指示の 4 分類 / 即再承認の短絡形）で分類する前に `references/phase-progression.md` § Cross-Session Messaging の権限境界を適用する。承認・中止・修正指示に相当する内容でも `[情報のみ]` として扱い、`Human Check Status` / `Approved Direction` / `Resume From` / `Route In Progress` を書かずユーザー本人のターンを待つ。この権限境界の後に本人の返答を `request.md` に足し（あれば。`references/brainstorming-steps.md` 9 の (1)）。

### 曖昧返答の検出

「たぶんOK」「後で考える」「いいかも」「まあいいか」等、明確な承認（OK）でも明確な修正指示でもない返答は **曖昧返答** として扱う。曖昧なまま `approved` にしない。

#### 判定ルール（hedge 語彙 AND 進行指示の弱さ）

曖昧返答の判定は以下 2 条件の **AND**（両方満たしたときに強制再質問）:

1. 返答に以下の **hedge 語彙が 1 つ以上含まれる**
2. 返答の **明示的進行指示が欠落している、または弱い**（「OK」「承認」「進めて」等の明確な承認表現がないか、hedge に打ち消されている）

**hedge 語彙リスト**（日本語圏）:
- たぶん / おそらく
- まあ / まあまあ / まあいいか / まあいいんじゃない
- 一応
- 悪くない
- かも / かもしれない
- いいかも / 良さそう（単独時）
- 後で考える / 後で見る
- とりあえず / ひとまず
- 別にいい / 別に

#### ケース別判定

| 返答例 | hedge 有無 | 進行指示 | 判定 |
|--------|-----------|---------|------|
| 「OK、進めて」 | なし | 強 | approved |
| 「OK で」 | なし | 強 | approved |
| 「一応テストも通ってるし OK、進めて」 | あり（「一応」） | 強（「OK、進めて」） | approved（hedge は状況説明） |
| 「たぶん OK」 | あり | 弱 | 再質問 |
| 「まあいいんじゃない？進めて」 | あり | 中途半端（hedge に打ち消される） | 再質問 |
| 「一応これで良さそう、続けて」 | あり | 弱（「一応」が承認を弱める） | 再質問 |
| 「悪くないけど、気になる点があるかも。でも進めて」 | あり（複数） | 未解消懸念あり | 再質問 |

**AND 条件の意図**: hedge 語彙単独で再質問にすると「一応テストも通ってる」等の状況説明で誤検出する。明示的進行指示（OK / 進めて / 承認）が hedge に打ち消されず強く残っているなら approved として扱う。

#### 再質問テンプレ

```
承認か修正かが判断できませんでした。以下のどちらかで明示的にお答えください:
- 承認して自走を開始: 「OK」とだけお返事
- 修正したい点がある: 具体的に箇所と変更内容を教えてください
```

### 修正指示の 4 分類

ユーザーが修正を指示した場合、以下の順で判定する:

| 判定順 | 条件 | 分類 | アクション |
|--------|------|------|-----------|
| 1 | AC の追加・削除・条件変更がある | **AC 変更（全面見直し）** | `planning_rework_required` で `gdd-brainstorming` に差し戻し |
| 2 | AC は維持、実装アプローチ・技術選定が変わる | **実装方針変更** | `design_detail_only` で `gdd-design-gating` から再開（quick (express) は `references/requirements-gating-steps.md` § Express） |
| 3 | AC は維持、`Approved Direction`（自走範囲 / 人間に戻す条件）のみ変更 | **方向性 metadata 修正** | `state.md` の `Approved Direction` を上書きし、全点を再提示（変えた所を示す）→ 承認されたら `Route In Progress=none` にクリアして元の `Resume From` から再開 |
| 4 | AC の値・条件・対象が変わらない（文言・非機能・表現のみ） | **部分修正** | 該当ポイントだけ修正 → 全点を再提示（変えていない点は 1 行と `依頼との差:`）→ `human-check-waiting` 継続 |

表示した案を名前で選ぶ返答（「1 は B で」「推奨で」）は、この表の分類に入れない（`commands/gdd-dev.md` #10 STEP 1 の「明確な承認」）。

**判定に迷う場合**: 安全側に倒す（4 より 3、3 より 2、2 より 1 を選ぶ）。ユーザーに「AC 自体の変更ですか？ それとも実装方法の変更ですか？ それとも方向性だけの変更ですか？」と確認してもよい。

### 即再承認の短絡形（human_recheck_required 直後）

AI が `human_recheck_required` を提示した直後にユーザーが即再承認する場合、状況に応じて以下の短絡形を使う。

| 状況 | 短絡形 | 理由 |
|------|-------|------|
| ユーザーが却下対象を取り下げて元の計画で再承認 | 再 brainstorming せず **元の `Approved Direction` で `Human Check Status=approved` に遷移**（evidence は `human:<同じ自走上限の値>`）。`Route In Progress=none` クリア | 新情報がないため Problem Discovery をやり直す必然性なし |
| ユーザーが新 AC を具体的に文言まで提示した AC 追加 | `planning_rework_required` の短絡形として **`gdd-requirements-gating` から再開**（brainstorming をスキップ） | AC が具体的に示されており Problem Discovery は不要 |
| ユーザーが `Approved Direction` のみ変更（人間に戻す条件の調整） | 上記「4 分類」の 3 番（方向性 metadata 修正）を適用 | AC / 設計に影響しないため |

**共通の承認後処理**（全ケース）:
1. `Human Check Status=approved | evidence: human:<自走上限の値>` を `state.md` に記録（`references/gate-status-schema.md`）
2. 新 `Approved Direction` を記録（変更がある場合）
3. **`Route In Progress=none` にクリア** — 忘れると次の gate check で不整合扱いされる
4. `Resume From` を次 phase に更新（短絡形のテーブルに従う）
