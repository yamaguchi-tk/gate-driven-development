# CONTRIBUTING（plugin 内部開発者向け）

> **対象**: GDD plugin 自体の skill / agent / reference / hook / script を変更する開発者
> **対象外**: GDD plugin を**使う**側の開発者（その場合は `docs/ONBOARDING.md` を読む）
> **上位正本**: `references/self-contained-contract.md` / `references/common-guardrails.md`
> **この文書の位置付け**: plugin に PR を送る前に満たすべき条件・テスト手順・レビュー観点を 1 枚にまとめる

---

## plugin の構成

```
gate-driven-development/
├── README.md                 # 使う側向け機能紹介
├── CHANGELOG.md              # 変更履歴（版の節はリリースで changelog.d/ から集める）
├── CHANGELOG-archive.md      # 古い release 節（行数上限のため分割。追記はしない）
├── CHANGELOG-archive-2.md    # さらに古い release 節
├── CHANGELOG-archive-3.md    # 0.40.3 〜 0.38.0 の release 節
├── CHANGELOG-archive-4.md    # 0.40.15 〜 0.40.4 の release 節
├── changelog.d/              # PR ごとの変更断片（リリースで CHANGELOG.md に集めて消す）
├── CONTRIBUTING.md           # 本文書
├── plugin.json               # manifest（Claude Code / Cursor が読む）
├── commands/                 # ユーザー向け slash command
├── skills/                   # workflow 本体（29 skill / Skill count budget の上限）
├── agents/                   # reviewer・phase runner・実装 worker などの subagent
├── hooks/                    # hook 定義（UserPromptSubmit / UserPromptExpansion / SessionStart /
│                             #   PreCompact / Stop / StopFailure / Notification / PreToolUse）
│   ├── hooks.json
│   └── scripts/              # shell / python 実装
├── references/               # plugin 内部正本（契約レベルの Q&A・steps 等）
├── docs/                     # 他チーム向け読み物（導入・障害・CLAUDE.md 雛形・セキュリティ）
├── scripts/                  # インストール・リンク・utility
├── tests/                    # validate-plugin.sh, test_*.py
├── evals/                    # skill トリガー精度評価（evals.json）
└── dev/                      # 開発者向け一時作業（audit log 等）
```

---

## 変更の種類と出発点

| 変更 | 出発点 | 追加で触る場所 |
|------|--------|--------------|
| 既存 skill のロジック修正 | `skills/<name>/SKILL.md` | 関連する `references/*-steps.md` / `changelog.d/` の断片 |
| 新しい skill の追加 | `skills/<name>/SKILL.md` 新規 | `plugin.json`, `evals/evals.json`, `references/`, `changelog.d/` の断片 |
| reviewer agent の責務変更 | `agents/gdd-*-reviewer.md` | `references/reviewer-common.md` / `reviewer-selection.md` |
| hook の挙動追加 | `hooks/scripts/*.py` / `*.sh` | `hooks/hooks.json`, `tests/test_*.py`, `changelog.d/` の断片 |
| 契約 Q&A の更新 | `references/faq.md` | 他 reference との整合性確認、`docs/TROUBLESHOOTING.md` の整合 |
| 他チーム向けドキュメント | `docs/*.md` | `README.md § 他チーム導入向けドキュメント`, `changelog.d/` の断片 |
| validate rule の追加 | `tests/validate-plugin.sh` | 該当対象ファイル、CI |
| チーム外への配布 | `docs/DISTRIBUTION_READINESS.md` | PR 分割、untracked 除外、release candidate 検証 |

---

## 等価交換ルール（加算式改修の禁止）

GDD は軽量オーケストレーターなので、新しい文書・skill・長い section を足すだけの改修は原則 reject する。

- 新規 reference を追加する場合、親文書から同じ内容の本文を削除し、親はリンク + 要約にする
- overview は 30 行以内を目安にし、field meaning / 許容値 / 手順 table を持たせない
- references/ の総行数は `validate-plugin.sh` の line budget を超えない
- **Skill count budget**: 現在の上限は 29（2026-09-15、`pr-review-followup` 新設で 28→29）。新しい skill を追加する場合は、既存 skill の統合・削除・責務移管で上限以内に収めるか、上限変更の理由と削減計画を同じ PR に書く
- 上限自体を変える PR は `SKILL_COUNT_BUDGET_CHANGE=true` と `SKILL_COUNT_REDUCTION_PLAN=<理由と削減計画>` を validation / PR evidence に残す。Codex manifest の `manifest skill count` も実 skill 数と一致させる
- 追加だけで目的が達成されたように見える PR は、削減した本文・統合した正本・参照元更新を PR 本文に書く

このルールは `references/source-of-truth-map.md` の owner ルールと同じ考え方。配線（参照元更新）と削減（親からの削除）が揃って初めて完了。

---

## 必須チェック（PR / merge 前に必ず通す）

### 0. 正本 repo / local cache drift guard

GDD plugin の正本はこの git 管理下の `plugins/gate-driven-development/`。`~/.claude/plugins/local/gate-driven-development` や `~/.codex/plugins/cache/.../gate-driven-development/<version>` は配布・検証用の local cache であり、直接編集しただけでは完了にしない。

- local cache で試した変更は、必ず正本 repo に還流してから PR 化する
- release 前は正本 repo 側で `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` と `bash plugins/gate-driven-development/tests/validate-plugin.sh` を通す
- local cache へ同期した場合は、正本 repo と cache の差分が意図した配布差分だけであることを確認する
- CI の `Run GDD plugin contract tests` / `Smoke test workflow plugin` が正本 repo で落ちる状態では release しない

### 1. pytest の全量が通る（CI が回す。手元では関係するテスト）

全 contract test（`python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`）は、CI（`.github/workflows/plugin-lint.yml` の `Run GDD plugin contract tests`）が PR と main への push ごとに回す（Linux 標準 runner で回す）。手元では、変更に関係するテスト（変更したファイルの名前〈拡張子を除く〉を参照するテストと、その名前を含む helper〈`tests/_*.py`〉の名前を参照するテストと、足した・変えたテスト。round ごとの粒度は `references/gdd-self-development.md` § 開発場所の使い分け）と、項 2 の `validate-plugin.sh` を回す。PR をマージする前に、PR の check で `gdd-plugin` が success であることを確かめる（branch protection の required check はまだ設定していないので、CI が赤でも GitHub はマージを止めない）。手元で全量を回すのは、release 前（項 0）、hooks を local に入れる前（`references/gdd-self-development.md` § 開発場所の使い分け）、CI が使えないときだけ。

GDD の hook・script の契約と、コードが読む値・集合・シンボル（command・agent の frontmatter を含む）と文書の一致は `tests/test_*.py` で固定する。文書（command の本文を含む）の語・文だけを見るテスト（`tests/test_*.py`）は書かず、残さない（既存のものは消す）。`tests/checks/*.sh` の文言の検査の扱いは別に決める。pytest full suite が落ちる場合（CI が赤のときを含む）は、機能追加ではなく契約破れの修正を先に行う。

以下は全量を手元で回すときの手順。

`-n auto` は pytest-xdist による並列実行（コア数の多いマシンでは、直列よりずっと速い）。plugin 直下の `pytest.ini`（`addopts = -n auto --dist worksteal --durations=30 --durations-min=1.0`）により、`-n` を付けなくても既定で並列になる。1 秒以上かかったものを遅い順に最大 30 行出す（1 行は 1 テストの setup・call・teardown のどれか。最後の集計行の手前に入る）。CI の全量のログにも残るので、テストの実行時間を削るときの前後比較に使う。手元で速いテストだけを回したときは、行を出さない。1 秒未満も見るときは `--durations-min=0` を付ける（`-vv` では出ない）。直列で走らせたいときは `-n 0` を付ける（`-p no:xdist` は `unrecognized arguments` で失敗する）。`--dist worksteal` のため pytest-xdist 3.2 以上が要る。未導入なら `python3 -m pip install --break-system-packages 'pytest-xdist>=3.2'`（homebrew Python は pytest 自体も同経路）。

### 2. `bash tests/validate-plugin.sh` を実行して全 BLOCK OK

現在の BLOCK:

| BLOCK | 目的 |
|-------|------|
| `grade-evals` | `evals/evals.json` のスキーマ・スコア基準 |
| `hooks` | `hooks/hooks.json` と実装スクリプトの整合 |
| `skill-reference-drift` | skill の step 番号が reference と一致 / 存在しない ref を参照しない |
| `docs-links-valid` | `docs/*.md` が実在する `references/` / `docs/` を参照 |
| `express-promotion-transition` | Express → standard 昇格ルールの整合 |
| `workflow-loop` | done-guard A〜J（terminal 遷移の検査） |
| `external-verifier-smoke` | 外部 verifier の evidence 書き込み smoke test |

1 つでも FAIL したら merge しない。

### 1a. Distribution Readiness（チーム外配布時）

チーム外へ広めに配布する PR では、`docs/DISTRIBUTION_READINESS.md` を読み、以下を確認する。

- `git status --short` / `git diff --stat` / untracked ファイルを棚卸しした
- 変更を distribution-readiness / HITL / superpowers differentiation / model routing / AC trace のどの PR bundle に入れるか決めた
- `.vscode/` や IDE / 個人・組織設定を GDD 本体配布 PR に混ぜていない
- 変更断片（`changelog.d/`）の Affected Files と実 diff が一致している

### 1b. Superpowers Benchmark Summary（changed GDD primitive のみ）

changed GDD primitive（`gdd-brainstorming` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `root-cause-investigation` など superpowers 同等品がある primitive）を変更した PR では、`Superpowers Benchmark Summary` を PR / release note に入れる。

- benchmark を実行した場合: 比較資料のパスか要約を残し、対象 primitive / scenario / GDD と superpowers の checklist 達成率 / steps / duration / retries / GDD 固有軸を要約する
- benchmark を実行しない場合: `Superpowers Benchmark Summary: missing` とし、省略理由を書く
- primitive 変更が無い場合: `Superpowers Benchmark Summary: not_applicable (no changed GDD primitive)`

### 1c. Skill RED-GREEN Evidence（skill / prompt / reviewer policy 変更時）

skill 本文、prompt、reviewer policy、HITL 出力契約を変える場合は `Skill RED-GREEN Evidence` を残す。これは superpowers `writing-skills` の pressure scenario TDD を GDD plugin 開発に適用するもの。

- `baseline_without_skill`: 変更前またはスキル無しで、どの pressure scenario がどう失敗したか
- `with_skill`: 変更後に同じ pressure scenario がどう改善したか
- `pressure scenario`: agent が合理化しやすい短い入力、期待される違反、期待される合格条件

### 1d. 変更断片（`changelog.d/`）

plugin の配下を変える PR は、`changelog.d/<YYYYMMDD>-<slug>.md` に断片を 1 つ足す（書式は `CHANGELOG.md` § Entry Template）。3 manifest の version・`CHANGELOG.md` の版の節・`docs/VERSIONING.md` § 現状 には触れない。版数上げと集約はリリースのときだけ行う（`docs/VERSIONING.md` § 版数はリリースでだけ上げる）。検査は `tests/checks/version-not-consumed.sh`（BLOCK）。

断片の内容・書式（利用者から見える変更だけを書く・確定の時機・必須の節）の正本は `CHANGELOG.md` § Policy。レビューの経緯・巡の記録・指摘の一覧・受け入れた指摘（medium・low と advisory）は、本リポジトリでは `review-log/` に残す。

### 3. 根幹ルール違反チェック

`validate-plugin.sh` が自動検出する:

- **Root CLAUDE.md 独立性**: `README.md` / `commands/*.md` / `skills/*/SKILL.md` / `agents/*.md` / `scripts/*.sh` は文字列 `CLAUDE.md` を含まない（plugin が根幹 CLAUDE.md に依存しないため）
  - CHANGELOG.md / docs/ / references/ での参照は許容
- **Skill の description フォーマット**: WHEN to use を述べる（CSO）
- **Skill 名競合**: 同名 skill/agent/command がないこと

### 3a. 独立レビュー 1 回（push 前・standard のみ）

`git push` の前に、実装文脈を渡さない独立レビューを 1 回起動して `high: 0` かつ `blocking: 0` を確認する。契約（read-only / diff-only / 観点レーン (a)〜(h) / 出力フォーマット / 証跡書式）の正本は `references/independent-review.md`。証跡は `state.md` の `Independent Review` 行に残し、standard の pre-push gate（push 対象 tip と比べる）と pre-PR gate（HEAD と比べる）が sha 一致と `high: 0` かつ `blocking: 0` を機械検査する（通知の reason code: 欠落 `independent-review-missing` / sha 不一致 `independent-review-stale` / `high > 0` または `blocking > 0` `independent-review-high`）。default branch を取り込むだけの merge commit では、取り直さずに `references/self-review-lanes.md` § Independent Review の引き継ぎに従ってよい。

観点レーンには 2026-09-06 に **(g) 例外で guard 全体が落ちる経路** と **(h) 受理集合の対称性** を追加した（reviewer recall 実測で、(a)〜(f) だけの構成が例外による fail-open を見逃したため）。2026-09-16 に (h) へ「列挙型判定の検出」を統合した（review-log-present.sh の同種 fail-open が何度も再発した実測に基づく）。

### 4. `.steering/` 書き込み検査

plugin が artifact を書く処理は自動で hook 経由になるが、直接編集が必要な場合は:

- email アドレス（`example.com` / `example.org` / `<redacted>` 除く）を書かない
- ローカル絶対パス（`/Users/...` 等）を書かない
- プレースホルダー（`TBD` / `TODO` / 「適切に対応」）を書かない（hook は検出しない。task-breakdown の Self-Review が tasklist の Steps を、brainstorming の Self-Review が requirements.md・design.md を見る。references/common-guardrails.md § プレースホルダー禁止）

---

## 変更ごとの詳細手順

### skill を追加する

1. `skills/<new-skill>/SKILL.md` を作成
   - frontmatter: `name`, `description` (WHEN to use), `allowed-tools`
   - 本文: `## Steps` セクション、`## Phase Gate Pre-check`（必要時）
2. `plugin.json` の `skills` 配列に追加
3. `evals/evals.json` にトリガーケースを追加（最低 5 ケース）
4. 参照する `references/*.md` が既存でない場合は作成
5. `changelog.d/` の断片に `#### Added` として書く（`type: minor`）
6. 関係するテストを回す（`python3 -m pytest <ファイル…> -q`。新規の skill は名前を参照するテストがまだ無いので、skill 数を固定する `tests/test_superpowers_differentiation_contract.py` も入れる。全量は CI が回す。項 1）
7. `bash tests/validate-plugin.sh`

### reviewer agent を追加・改修する

- 現在 4 種類（planning / implementation / security / completion）で原則これ以上増やさない
- 責務重複を避けるため新規追加前に `references/reviewer-common.md` と `reviewer-selection.md` を確認
- 既存 agent の改修は `agents/gdd-*-reviewer.md` を直接編集し、`changelog.d/` の断片に変更を記録
- `agents/gdd-*-reviewer.md` か `references/reviewer-common.md`（4 つの reviewer の定義が共通の規則として名指しする）を変えたら、変える前と後で `scripts/run-reviewer-recall-eval.py` を回し、過去の欠陥の見逃しが増えていないかを比べる（手順と読み方: `docs/reviewer-recall-eval.md`）
- `agents/` の定義は `tools:` の許可リストを持つ（無いと MCP を含む親の全ツールを受け取る。2026-09-29 の実測で、起動時の文脈は全ツールの agent が Read・Grep・Glob だけの agent より大きく膨らんだ）。agent を足したら `tests/test_agent_tool_allowlist_contract.py` の `EXPECTED` に許可リストを足す

### hook を追加する

1. `hooks/scripts/<name>.sh` または `.py` を作成
2. 実行可能に: `chmod +x hooks/scripts/<name>.sh`
3. `hooks/hooks.json` に登録
4. `tests/test_*_hook_logic.py` を追加（Python 実装の場合）
5. 関係するテストを回す（`python3 -m pytest <ファイル…> -q`。local に入れる前は全量も通す。項 1）
6. `bash tests/validate-plugin.sh`

### references/ を編集する

- `上位正本` / `参照元` フィールドを frontmatter 同等位置に明記
- 他 reference からのリンクが切れていないか `grep -rn '<filename>' skills/ agents/ references/ docs/`
- `docs/` 側との整合を確認（`docs/TROUBLESHOOTING.md` は `references/faq.md` を参照）

### docs/ を編集する

- `docs/` は他チーム向け読み物。契約レベルは references/ を SSOT として参照する
- 手順・FAQ の詳細は references/ をコピペせず、ポインターで済ませる（drift 防止）
- validate `docs-links-valid` BLOCK で docs/ → references/ / docs/ リンクの実在を検査する

---

## テスト方針

### 既存テスト

- pytest の全量（`python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`）: GDD 契約テスト（必須。CI が PR ごとに回す。手元では関係するテスト。項 1）
- `tests/validate-plugin.sh`: 構造検査・drift 検出（必須）
- `tests/test_stop_hook_unit.py`・`tests/test_stop_hook_state_unit.py`・`tests/test_stop_hook_continuation_unit.py`・`tests/test_stop_hook_stop_reason_unit.py`: Stop hook のロジック単体（unit tests）
- `tests/test_stop_hook_e2e.py`・`tests/test_stop_hook_e2e_block_content.py`: Stop hook の E2E テスト
- `tests/test_stop_hook_validate.py`: validate-plugin.sh と inflight 判定テスト

### 新機能のテスト

- hook 追加時は対応する `test_*_hook_logic.py` を用意
- `validate-plugin.sh` に新 BLOCK を追加する場合は、failing case を artificial に作って exit 1 になることを確認してから戻す
- skill の新規フロー追加時は `evals/evals.json` のケースで最低 5 件の trigger サンプルを入れる

---

## レビュー観点

plugin 変更の PR レビューで確認する項目:

| 観点 | 確認内容 |
|------|---------|
| **契約整合性** | references/ 間のリンク・責務分担に矛盾がないか |
| **後方互換** | 既存 `.steering/` を壊さないか。state field の rename がないか |
| **fail-closed** | 曖昧入力・hook 失敗時に安全側（停止）に倒れるか |
| **プレースホルダー混入** | TBD / TODO / 「適切に対応」が artifact に書かれないか |
| **description 品質** | skill description が CSO（WHEN to use）を満たすか |
| **validate 通過** | `bash tests/validate-plugin.sh` が OK |
| **変更断片** | `changelog.d/` に断片があり、版数系のファイル（3 manifest・`CHANGELOG.md` の版の節・`docs/VERSIONING.md` § 現状）を変えていないか。利用者から見える変更だけを書いているか |
| **独立レビュー** | push 前に独立レビュー 1 回（`high: 0` かつ `blocking: 0`）を通し、`Independent Review` 行を記録したか |

---

## 禁止事項

- **root `CLAUDE.md` への依存追加**: plugin core files（README.md 等）に `CLAUDE.md` の substring を書かない
- **ユーザー向けの plugin 直接編集指示**: 利用者が `.steering/` や plugin core を直接編集することを前提にしない
- **hook の fail-open**: エラー時に処理を続行させる実装は入れない（fail-closed 原則）
- **破壊的な migration を silent に実行**: state スキーマ変更は CHANGELOG の Breaking Changes に明記 + 既存 state を壊さない互換レイヤー or 明示的な migration ガイド
- **`validate-plugin.sh` の BLOCK 削除**: 既存 BLOCK を消す PR は reject。必要なら無効化フラグを設けて理由を CHANGELOG に残す

---

## リリース手順（maintainer 向け）

手順の正本は `docs/VERSIONING.md` § リリース手順（`scripts/release.py` を dry-run で確かめてから `--apply` で実行し、必須チェックを通して commit と tag を作る）。リリースは maintainer の明示の指示があるときだけ行う。

---

## 参考

- plugin 内部契約: `references/self-contained-contract.md`
- 共通 guardrail: `references/common-guardrails.md`
- セキュリティ境界: `docs/SECURITY.md`
- validate script: `tests/validate-plugin.sh`
- 他チーム展開: `docs/ONBOARDING.md`
