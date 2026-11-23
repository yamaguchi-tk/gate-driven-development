# Fixed Model（GDD 共通モデル正本）

> **所有**: gate-driven-development 全 skill が固定使用するモデルと effort 値の唯一の正本
> **参照元**: 全 skill の `## Fixed Model` セクションがこの正本を pointer 参照する

formal gate skill は重いモデルで固定する。理由は以下:

- requirements / design は human check の承認対象であり、解釈差が後段の手戻りに直結する
- impl-gate は autonomous continuation を止める formal gate であり、軽量モデルに落とすと差し戻し検出漏れが発生する
- completion-check は `done` 判定の最終 gate であり、AC Drift / external dependency / skill quality の総合判定を担う

軽量モデルへの自動ダウングレードは設計上禁止する。**この禁止は Claude Code では起動時に機械強制される**。`Agent` の起動を調べると、`model` を指定しない起動が多く（requirements・design・review のどの工程にもあった）、未指定は host 既定（main セッションの model）に落ちていた——つまり本節の散文だけでは守られていなかった。`hooks/hooks.json` の `PreToolUse`（`matcher: "Agent"`）が `hooks/scripts/run-agent-dispatch-model-gate-hook.sh` を発火し、工程に対して `model` が未指定、または工程が許容する model 集合に含まれない場合（軽量モデルへの自動ダウングレードを含む）に `additionalContext` で warn する（block はしない）。工程判定は `state.md` の `Resume From`（planning phase）と、3 gate 承認済み（canonical）な `tasklist.md` の `Next Action`（build phase。`references/state-machine.md:199-208`。draft の tasklist.md の `Next Action` は仮置きの記載値でしかないため routing source にしない）のみを材料にし、`description` の自由文は使わない。phase → tier のマッピングは `scripts/resolve-gdd-model.py` の `PHASE_TO_TIER` / `TIER_TO_MODEL["claude_code"]` を正本として共有する（`hooks/scripts/lib/agent_dispatch_gate.py` が読む）。`agents/*.md` の frontmatter で `model: opus` に固定されている reviewer subagent（`gdd-planning-reviewer` 等）と実装の worker（`gdd-implementation-worker-heavy`・`gdd-remediation-worker`）、マージ後の QA の `gdd-qa-runner`、Opus の相談役（`gdd-opus-advisor`・`gdd-opus-advisor-max`）を model 省略で起動したとき（bare 名・plugin prefix 付きのどちらでも。sonnet に固定した `gdd-implementation-worker`・`gdd-code-simplifier` は、frontmatter の model で工程を判定する）と、`Explore` / `Plan` 等の読み取り専用の汎用調査 agent（phase の tier 要件と無関係）と Fable の相談役 `gdd-fable-advisor`（tier に無い model で動く。model の値によらない）と、Sonnet に固定した提出前の照合 `gdd-requirements-precheck`（read-only で、opus 必須の requirements-gating から起動する）は対象外。`model: opus` に固定した agent に opus 以外の `model` を明示した起動は、工程の tier が sonnet でも、`model` を省略するよう警告する（明示した model は定義より優先されるため）。**既知の限界**: `Resume From` / `Next Action` から工程を特定できない起動では判定しない——具体的には、brainstorming / requirements / design の初回 dispatch は steering 作成前（`Resume From` がまだ書かれていない）か `human-check-waiting` 経由の遷移であることが多く、この経路では判定できない。3 gate 未承認の間の build-phase 相当 dispatch も、canonical でない tasklist.md の `Next Action` を使わない設計上、同様に判定できない。Cursor / Codex にこの機械強制は無い（`hooks.json` は Claude Code 専用機構のため）。

## モデル名の書き方

- Claude の名前には版数を書かない。Claude Code で起動に使う名前は alias（`opus` / `sonnet` / `haiku`）で、表の Claude Code 列・agent frontmatter の `model`・`Agent(model=…)` は小文字の alias で書く。散文では版数なしの family 名（Opus・Sonnet・Haiku）で書いてよい。既定の設定では Claude Code が alias をその版の CLI が知る最新のモデルに解決する（2026-09-23 実測: CLI を 2.1.261 から 2.1.280 に上げると、`opus` の解決先が 1 つ新しい版の Opus に変わった）。同じ family の新しい版が出たら、CLI を更新すれば、その後に開いたセッションから subagent も上がる。契約 md は直さない。環境変数や設定で解決先を固定している環境では、CLI を更新しても上がらないことがある
- Cursor はモデルを名前で選ぶ。Cursor で Opus を使うところ（Dialectic Counter）は、Cursor のモデル一覧にある最新の Opus を選ぶ。文書には版を書かない
- 過去の実測は「当時の Opus」のように版を書かず、日付を添えて書く。版は日付と CHANGELOG から辿る。実適用 model を記録するとき（`worklog.md` など）は、alias だけでは版が分からないので、transcript の model ID（`claude-<family>-<版>` の形）を確かめられたら併記する。版が上がったことを知らせる仕組みは無い

## モデル定義表

### 共通 tier 正本

| tier | Claude Code | Cursor | Codex |
|---|---|---|---|
| `formal_gate` | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=medium` | `gpt-5.6-sol` + `reasoning.effort=medium` |
| `general_heavy` | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=low` | `gpt-5.6-sol` + `reasoning.effort=low` |
| `general_heavy_risk` | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=high` | `gpt-5.6-sol` + `reasoning.effort=high` |
| `light_task` | `sonnet` + `effort=medium` | `Grok 4.5` + `reasoning.effort=medium` | `gpt-5.6-terra` + `reasoning.effort=medium` |
| `leaf_task` | `sonnet` + `effort=low` | `Grok 4.5` + `reasoning.effort=low` | `gpt-5.6-terra` + `reasoning.effort=low` |
| `cheap_readonly` | `haiku` 相当が使える場合のみ | `Grok 4.5` + `reasoning.effort=low`（`Grok Code Fast 1` が使えればそちら） | `gpt-5.6-luna` + `reasoning.effort=high` |
| `implementation` | `sonnet` + `effort=medium`、`Complexity: standard` でない task は `opus` + `effort=high` | `Composer 2.5`（`composer-2-fast` 不使用） | `gpt-5.6-terra` + `reasoning.effort=low` |
| `dialectic_counter` | `opus` + `effort=high` | `Opus`（一覧の最新）+ `reasoning.effort=high` | `gpt-5.6-terra` + `reasoning.effort=high` + reviewer prompt role |
| `remediation_loop` | `opus` + `effort=xhigh` | `Grok 4.6` + `reasoning.effort=high` | `gpt-5.6-sol` + `reasoning.effort=high` |
| `independent_review` | `opus` + `effort=xhigh` | `Grok 4.6` + `reasoning.effort=high` | `gpt-5.6-sol` + `reasoning.effort=high` |

`gdd-subagent-driven-implementation` は `implementation` tier。Claude Code で worker subagent を起動するときは、task の `Complexity:`（`gdd-task-breakdown` が宣言する）と `Gate Rounds` で agent 定義を選び、`Agent(model=...)` は省略する（model と effort は agent 定義の frontmatter が決める。`## Worktree` と `## Plugin Root` を渡す。model を検査する hook は、model を省略した起動を agent 定義の model で工程に照らして判定する。opus の heavy・remediation は免除と同じ結果になり、sonnet の worker は opus 必須の工程で警告される）: `Gate Rounds` ≥ 2 → `gate-driven-development:gdd-remediation-worker`（`remediation_loop`、`opus` + `effort=xhigh`）、`Complexity: standard`（値が `standard` と一致するときだけ）→ `gate-driven-development:gdd-implementation-worker`（`sonnet` + `effort=medium`）、それ以外（`complex`・未宣言・ほかの値）→ `gate-driven-development:gdd-implementation-worker-heavy`（`general_heavy_risk`、`opus` + `effort=high`）。worker が推論力の不足で `BLOCKED` を返したときは 1 段上の worker（standard → heavy → remediation）で再 dispatch し、`Gate Rounds` ≥ 2 の間は remediation worker より下げない。`complex` にするのは security-sensitive（`gdd-implementation-gating` Step 3 か `references/reviewer-selection.md` § Gate Rules の security reviewer の適用条件）/ large working-set / AC・scope・ownership 変更可能性 / 既存コード読解が難しい、のどれかに当たる task。agent 定義が見つからないときは `references/subagent-dispatch.md` § Typed Agent Resolution と同じく、1 回だけ `general-purpose` を agent 定義と同じ model を明示して起動し直す。main session で inline に実装するときは main の model のまま。往復（差し戻し回数）による昇格は `remediation_loop` に一本化し、本 tier の条件には含めない。

`root-cause-investigation` / `gdd-systematic-debugging` / `gdd-refactor-planning` は `general_heavy` tier。

**`remediation_loop` tier（往復発生時の昇格）**: 開始点は**同一 `Current Task` で `changes_requested` が累計 2 回目**になった時点（連続でなくてよい）。判定は `tasklist.md` の `Current Task` セクションの **`Gate Rounds: N`**（`gdd-implementation-gating` が `changes_requested` を出すたびに +1。route 非依存で、`Fix Attempts` の値では判定しない。`human_recheck_required` の reset 対象に含めず、task が `approved` になった時点で削除する）が **2 以上**であること。reset を跨いでも維持し、task が `approved` になるまで続く。この時点から (1) route 判断（`gdd-systematic-debugging` subagent）、(2) 再レビュー（`gdd-implementation-gating` の gate subagent 自体を `Agent(model="opus")` で起動する。inline review も escalation した reviewer subagent もこの tier になる）、(3) remediation 実装（worker subagent〔`gdd-remediation-worker`。model は agent 定義が決める〕の dispatch を必須にし、main session inline では修正しない）の 3 工程をこの tier で起動する。1 回目の `changes_requested` 後の再レビューは通常 tier のまま。`BLOCKED` の昇格で `gdd-remediation-worker` を使っても、この tier は始まらない（gate subagent などは上げない）。`gdd-completion-check` は task 単位でないため対象外。判定主体は controller で、実適用 model と effort を `worklog.md` に記録する（Agent tool は effort を引数で受けないため、agent 定義を持たない subagent は host の既定 effort で動く。`xhigh` を持たない host では `high` に縮退する）。`general_heavy_risk`（`high`）より上げるのは、下の planning reviewer の段落と同じ実験で、推論型の欠陥は `high` では拾えず、`xhigh` と `max` だけが拾ったため（観点なしの検出は xhigh と max で同じだった）。2026-10-28 に `max` から `xhigh` に下げた。理由は時間と費用で、remediation worker は 1 本ごとの時間と費用が大きかった。軽いレーンの差分巡を `max` から `xhigh` にしたときは、時間が大きく縮んだ（2026-10-10）。2026-10-29 に、max で走った過去の worker の一部を同じ依頼で xhigh で当て直し、差分を伏せて採点した。点は max が xhigh をやや上回った。差は、後の gate の指摘を先に避けたかに出た（max が同じ類の穴まで閉じた件があった）。ただし、採点役は max の差分を見分けられ、max だけが controller の答えを受けていた件もあった。同じ類の穴まで閉じた件でも、次の gate は同じ類の別の穴で `changes_requested` になり、往復は減らなかった。xhigh は 1 本の費用・時間が max より小さいので、xhigh のままにする。remediation worker の後の gate が `approved` になる率が、max で走っていた期間（2026-10-01〜28）より下がったら、max に戻すかを見直す。根拠: 当時の Opus で往復を重ねても収束しなかったタスクがあった（ユーザー判断 2026-09-02）。**`Agent(model="opus")` / `model="opus"` は Claude Code の Agent tool 呼び出しを指す。Cursor / Codex はこの記法を実行せず、`scripts/run-gdd-worker.py --complexity remediation_loop`（正本: `references/subagent-dispatch.md` § Codex / Cursor Worker Dispatch）経由で上の tier 表の host 列（Cursor: `Grok 4.6` / Codex: `gpt-5.6-sol`）を解決する。モデル面の昇格は Claude Code だけで起き、Cursor / Codex は `general_heavy_risk` と同じモデルのまま（`independent_review` tier と同型の限界）。worker dispatch 必須化など model 以外の効果は Cursor / Codex にも及ぶ。**

**`independent_review` tier（push 前の独立レビュー）**: `references/independent-review.md` の契約（実装文脈を渡さない / read-only / diff-only）で 1 回起動する専用 tier。**実装文脈を渡さない独立実行であり、手順の正本は `references/independent-review.md`**。`gdd-completion-reviewer` の dispatch は independent review ではない（当該 agent は steering artifacts＝実装文脈を読むのが job なので、否定命令を付けても条件 1「実装文脈を渡さない」を満たせない）。Claude Code の `effort=xhigh` は `general_heavy_risk` より上げる意図を表す（`remediation_loop` と同じ値）（`effort` の値域は host が提供する範囲。`xhigh` を持たない host では `high` に縮退し、縮退した旨を `worklog.md` に記録する）。2026-10-29 に `max` から `xhigh` に下げた。理由は時間と費用で、軽いレーンの全差分巡（同じく実装文脈を渡さない独立レビュー）を過去の PR に当て直すと、当時の high を high として当てた数は xhigh と max でほぼ同じで、時間と費用は xhigh のほうが小さかった（各 1 回の味見で、ばらつきを超える差は測れていない）。Claude Code では `agents/gdd-independent-reviewer.md` が model と effort を固定する（2026-10-29 に作った。それまでは定義が無く、下げる前の `max` も強制されていなかった）。headless で起動したときと、定義を読み込む前から動いているセッションで `general-purpose` に代えたときは固定されない。Cursor / Codex 列は `general_heavy_risk` と同じ写像（`reasoning.effort=high`）で、両 host には `high` より上の effort が無い。コストが高いため発火は **push 1 回あたり 1 回**に絞る（PR 全体で 1 回ではない。正本: `references/self-review-lanes.md` § followup 周回時のレーン要求）。

`light_task` tier: `gdd-task-breakdown` / `gdd-test-driven-development` / `gdd-pr-review-followup` / `gdd-pre-workflow-brainstorming` / `gdd-ac-verification` / `gdd-writing-skills`。

`general_heavy_risk` tier（固定）: `gdd-pr-review`（最終 diff review）。2026-08-25 に light_task から昇格。根拠は 2026-08-22 の調べで、gate 通過後に残った実害級の欠陥を検出したのは当時の Opus（`effort=high`）の最終レビューだけだった。

`leaf_task` tier: `gdd-status` / `gdd-metrics` / `gdd-using-git-worktrees` / `gdd-next-plan`。

### Formal gate 固定表

| Gate Skill | Claude Code | Cursor | Codex | 補足 |
|---|---|---|---|---|
| `gdd-requirements-gating` | `opus` + `effort=high` | `Grok 4.6` + `effort=medium` | `gpt-5.6-sol` + `effort=medium` | brainstorming と同一ターン実行、要件整理・初稿の人間承認対象 |
| `gdd-design-gating` | `opus` + `effort=high` | `Grok 4.6` + `effort=medium` | `gpt-5.6-sol` + `effort=medium` | detailed design + security boundary |
| `gdd-implementation-gating` | `opus` + `effort=high` | `Grok 4.6` + `effort=medium` | `gpt-5.6-sol` + `effort=medium` | formal impl gate + reviewer dispatch |
| `gdd-completion-check` | `opus` + `effort=high` | `Grok 4.6` + `effort=medium` | `gpt-5.6-sol` + `effort=medium` | AC verification + 最終 comprehensive review |

**`agents/gdd-planning-reviewer.md`（requirements / design gate が dispatch する reviewer）**: gate 本体は `formal_gate`（Claude Code: `opus` + `effort=high`）のまま、reviewer subagent だけ agent 定義の `model: opus` + `effort: xhigh` で動く。根拠は 2026-09-05 の比較実験（正解の欠陥が分かっている設計成果物に、各構成を 1 回ずつ当てた）で、Opus max ＋観点レーンは、観点レーンなしの Opus high より多くの欠陥を拾った。照合型の欠陥（接地・記録監査・実効性）は観点レーンで拾え、推論型（内部整合・実装接続）は high 以下では拾えなかった。2026-10-29 に同じ材料と観点レーンで当て直すと、xhigh は max と同程度に拾い、1 回の費用と時間は xhigh のほうがずっと小さかった。このため `effort: max` から `xhigh` に下げた。Cursor / Codex は比べた記録が無く `high` より上の effort も無いため、`formal_gate` の写像のまま。

**Claude Code の phase Template（`references/subagent-dispatch.md` § Typed Agent Resolution）**: formal gate（planning・design-gating・implementation-gating・completion-check）は `agents/gdd-formal-gate-runner.md`（`model: opus` + `effort: high`）、light task（task-breakdown・TDD）は `agents/gdd-light-task-runner.md`（`model: sonnet` + `effort: medium`）で起動する。`Agent` ツールは effort を引数で受けないため、effort を固定できるのは agent 定義の frontmatter だけである。`remediation_loop` 中の implementation-gating は runner が `high` 固定のため、上の `effort=xhigh` は強制されない（従来は host 既定を継承していた。強制は未対応の限界）。

**`agents/gdd-qa-runner.md`（マージ後の QA。`references/post-merge-qa.md` 手順 4）**: `general_heavy_risk` tier（Claude Code: `model: opus` + `effort: high` を agent 定義で固定）。実装の main が Sonnet でも、検証の工程は Opus で行う。 **`agents/gdd-code-simplifier.md`（簡素化パス。`skills/gdd-subagent-driven-implementation/SKILL.md` 14a）**: Claude Code では `model: sonnet` + `effort: medium` を agent 定義で固定する（`implementation` tier と同じ model）。テストが赤なら変更を捨てる（テストが捉えない誤りは残りうる）。2026-10-30 に調べると、この agent の費用は GDD の agent 全体のごく一部で、当時の最新の Sonnet なら 1 本の費用は Opus より小さかった（alias `sonnet` が最新の Sonnet に解決されるとき。Sonnet の公称単価で usage から数えた。headless の `total_cost_usd` は Sonnet を Opus の単価で数える）。過去の簡素化を当て直して伏せて採点すると、Opus と Sonnet の点は近く、振る舞いを変えた差分はどちらにも無く、Sonnet の失点は主な重複を残す型だった（件数が少なく、各 1 回の採点）。opus 必須の工程から起動すると、dispatch model gate が警告する。

**相談役（`agents/gdd-opus-advisor.md`・`gdd-opus-advisor-max.md`・`gdd-fable-advisor.md`）**: 判断の相談に使う read-only の agent（Read・Grep・Glob）。model と effort を agent 定義で固定し、起動時に `model` を渡さない。`gdd-opus-advisor` は Opus・`effort: high`（`references/human-check-template.md` § 事前回答の委任先が `opus` のときは 1 本、`並行` のときは同じ材料で 2 本。手順は `references/autonomy.md` 判断の手順）、`gdd-fable-advisor` は Fable・`effort: medium`（同じ委任先が `fable` のとき）。`並行` を Opus high の 2 本にしたのは、2026-10-29 に過去の相談を当て直して論点ごとに採点すると、2 本並べたときに良い推奨が出た論点の数が Opus high と Fable medium の組に劣らず、1 相談の費用は組の半分以下だったからである（Opus xhigh 1 本は、良い推奨が出た論点がこれより少なかった）。差は小さく、同じ構成の回し直しでも入れ替わる程度なので、上回るとは言えない。組の値は 10-14 時点の定義で回したものである。どちらも、ユーザーが自分のターンで名指しで意見を求めたときにも起動する（起動の条件の正本は各定義の `description`）。`gdd-opus-advisor-max` は Opus・`effort: max`（high の推奨と呼び出し側の案が食い違ったときの相談し直しで、利用する repo の規則が定めた場面だけ。plugin の reference からは起動しない）。`general-purpose`・`Plan` に `model` を付ける起動では effort が main から継承される（2026-10-03 に確かめると、定義なしの相談はすべて継承していた）ので、effort を固定するにはこの定義を使う。根拠（2026-10-03。過去の食い違いを当時のコミットで再投入し、後の経過で採点）: 後で問題になった箇所を先に挙げた度合いは Opus max が最も高く、high と xhigh は同じで、Fable medium・high は Opus high を超えなかった（採点役も Opus max で、別系統の採点役では確かめていない）。推奨が割れた件では、ユーザーの選択は Fable の推奨と合うことが多かった。xhigh は high と同点で費用がずっと大きいので、定義を置かない。2026-10-14 の再投入（過去の相談・各構成 1 回。後の経過を要素に分けて採点。採点役も Opus）でも、良い値を取った要素の数は high・xhigh・Fable medium で並び、xhigh の費用は high よりずっと大きかった。2 本を並べると、どちらかが当てた要素が増え、当てる構成は要素ごとにばらついた。このため、2026-10-14〜29 は、人に表示する前の相談で Opus high と Fable medium を並べていた（今は上のとおり Opus high の 2 本。`references/human-check-template.md` 項目 7）。当時の組は、xhigh 単独より時間が短く、入力 token も少なかった。2026-10-29 の当て直しは「後で正しかった側」で採点しており、Fable の役（ユーザーの選択との一致）は採点の対象に入っていない。本文の「選ぶときの基準」は、過去の確認をユーザーの実際の選択と照らして入れた（Opus high で、ユーザーが推奨と違う案を選んだ件では選択との一致が増え、推奨どおりに選んだ件〔基準を作るときに見ていない件〕では一致が変わらなかった。採点役は Opus）。Codex・Cursor ではこの定義を使わない（`references/autonomy.md` の `general_heavy_risk` tier の経路）。 依頼と既存コードの突き合わせ（`agents/gdd-request-code-crosscheck.md`。brainstorming の 9）も、同じく read-only で Opus・`effort: high` を定義で固定し、起動時に `model` を渡さない。Codex・Cursor では、`general_heavy_risk` tier のモデルで会話を引き継がない read-only の別コンテキストを起動し、この定義の本文を渡す。 提出前の照合（`agents/gdd-requirements-precheck.md`。`references/requirements-gating-steps.md` Step 4a）は、read-only で Sonnet・`effort: high` を定義で固定し、起動時に `model` を渡さない。決まったチェック表を既存のコードに当てるだけで、判断の深さは reviewer が担うので、Sonnet にした（2026-11-02 の再生で、Sonnet の照合は Opus の当て直しと当てた件数がほぼ同じで、誤った `ng` は 0 件だった）。Codex・Cursor では、`implementation` tier のモデルで会話を引き継がない read-only の別コンテキストを起動し、この定義の本文を渡す。

## Cursor / Codex 環境のモデル選択

Cursor / Codex の実際のモデル選択（Dialectic Counter 含む）は `references/cursor.md` / `references/codex.md` を参照する。

**コスト最適化方針（2026-08-25 最新化。Cursor は Grok + Composer 主体、Codex は GPT-5.6 系）**:

- **heavy tier の基本**は Cursor が `Grok 4.6`、Codex が `gpt-5.6-sol`
  - 一般 heavy（debug / refactor / advisory review）: `reasoning.effort=low`
  - 一般 heavy の risk escalation（undocumented step / large working-set / security-sensitive / final review）: `reasoning.effort=high`
  - **formal gate（brainstorming / requirements-gating / design-gating / impl-gating / completion-check）: `reasoning.effort=medium`**
- **leaf** は Cursor が `Grok 4.5` + `reasoning.effort=low`、Codex が `gpt-5.6-terra` + `reasoning.effort=low`（status / metrics / worktree などの admin task。state / routing source を読むため cheap lane 不使用）
- **cheap/read-only lane 専用**は Cursor が `Grok 4.5` + `low`（`Grok Code Fast 1` が使えればそちら）、Codex が `gpt-5.6-luna` + `high`（短い要約、リンク確認、一覧整形、state 更新なし、routing 判断なし）
- **light** は Cursor が `Grok 4.5` + `medium`、Codex が `gpt-5.6-terra` + `medium`（task-breakdown / TDD / pre-workflow-brainstorming 等の品質依存タスク。`pr-review` は light ではなく risk escalation の heavy 基本モデル + `high`）
- **Opus + `reasoning.effort=high`**（Cursor のモデル一覧にある最新の Opus）は **Cursor の Dialectic Review Counter evaluator** として cross-system 観点を確保（Codex は Anthropic 不可のため `gpt-5.6-terra` + `high` + reviewer prompt role で代替）
- **Cursor 実装は `Composer 2.5`** が標準。`composer-2-fast` は使わない
- **mini禁止境界**: cheap lane モデル（`gpt-5.6-luna` / `Grok Code Fast 1` 等）は HITL生成 / requirements判断 / design判断 / routing判断 / state更新 / worktree判断 / completion判定 / PR可否判断に使わない
- **`reasoning.effort=xhigh` は使わない**（high で十分、xhigh はコスト過剰）
- **GPT-5.4 系は使わない**（2026-08-31 廃止予定）。**GPT-5.5 も使わない**（Codex は `gpt-5.6-terra` へ、Cursor は Grok 系へ置換済み）

**判断根拠**: `references/cursor.md` § なぜ Grok 4.6 / 4.5 の 2 段構成か、および `references/codex.md` § 方針を正本とする。

## 各 skill の SKILL.md での参照方法

**Formal gate skill**（`gdd-requirements-gating` / `gdd-design-gating` / `gdd-implementation-gating` / `gdd-completion-check`）は `## Fixed Model` セクションを 1 行の pointer 参照のみにする:

```markdown
## Fixed Model

`references/fixed-models.md` を参照（Claude Code: `opus` + `effort=high` / Cursor: `Grok 4.6` + `effort=medium` / Codex: `gpt-5.6-sol` + `effort=medium` 固定）。
```

inline でモデル名を再掲しない。モデル名変更時は本 reference を正本として更新する。Claude の版が上がっても、直す行は無い（§ モデル名の書き方）。

**非 gate skill**（`gdd-subagent-driven-implementation` / `gdd-task-breakdown` / `gdd-pr-review` 等）は runtime ごとのモデル名を inline に明記したうえで、昇格条件や詳細は本 reference を pointer 参照する形にする。inline 値は本 reference の tier 定義と一致させること。ただし Claude の名前は版を書かずに一致させる（§ モデル名の書き方）。
