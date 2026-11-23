# DISTRIBUTION READINESS（チーム外への配布前チェック）

> **対象**: GDD plugin をチーム外へ配布する maintainer / 導入担当者
> **目的**: 大きな差分をそのまま配布せず、PR 分割・除外・検証 evidence を確認してから公開する
> **上位正本**: `CONTRIBUTING.md` / `docs/VERSIONING.md` / `docs/SECURITY.md`

---

## まず見るコマンド

配布 PR を作る前に、必ず以下を確認する。

```bash
git status --short
git diff --stat
git ls-files --others --exclude-standard
```

見る観点:

- modified と untracked を分ける
- plugin 本体の差分と、IDE / 個人設定 / 検証用一時ファイルを分ける
- 1 PR で説明できる変更だけを同じ PR に入れる
- 変更断片（`changelog.d/`）の affected files と実際の diff が合っているか確認する

---

## PR Bundle 推奨分割

大きな GDD 改修は、以下の束で分ける。1 つの bundle の中で `README / docs / references / skills / tests / CHANGELOG` が閉じているなら同じ PR に含めてよい。

### PR Bundle 1: distribution-readiness

チーム外への配布・非エンジニア配布・安全境界・リリース手順の整備。

代表ファイル:

- `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`
- `docs/NON_ENGINEER_APPROVER_HANDOUT.md`
- `docs/NON_ENGINEER_HITL_GUIDE.md`
- `docs/DISTRIBUTION_READINESS.md`
- `docs/SECURITY.md`
- `docs/VERSIONING.md`
- `docs/ONBOARDING.md`
- `README.md`
- `docs/references-archive/team-onboarding.md`
- `hooks/scripts/validate-steering-write.py`
- `tests/test_distribution_readiness_contract.py`

### PR Bundle 2: HITL / 既存コード読解

HITL の読みやすさ、要件・完了条件の trace、既存コード読み込み証跡の強化。

代表ファイル:

- `references/human-check-template.md`
- `references/output-format.md`
- `references/requirements-template.md`
- `references/requirements-gating-steps.md`
- `references/brainstorming-steps.md`
- `references/task-breakdown-steps.md`
- `skills/gdd-requirements-gating/SKILL.md`
- `skills/gdd-subagent-driven-implementation/SKILL.md`
- `tests/test_hitl_trace_contract.py`

### PR Bundle 3: superpowers differentiation

GDD と superpowers の使い分け、active GDD workflow lock、superpowers から取り込む discipline の整理。

代表ファイル:

- `docs/SUPERPOWERS_COEXISTENCE.md`
- `references/superpowers-overlap.md`
- `references/skill-responsibility-matrix.md`
- `skills/gdd-using-skills/SKILL.md`
- `hooks/scripts/run-session-start-hook.sh`
- `tests/test_superpowers_differentiation_contract.py`

### PR Bundle 4: model routing

Claude Code / Cursor / Codex の model tier、mini 禁止境界、Composer 2.5、Opus 5 の扱い。

代表ファイル:

- `references/cursor.md`
- `references/codex.md`
- `references/fixed-models.md`
- `references/cursor-guide.md`
- `scripts/resolve-gdd-model.py`
- `scripts/benchmark-model-routing.py`
- `skills/gdd-model-routing/SKILL.md`
- `skills/gdd-model-routing/references/cursor.md`
- `tests/test_model_routing_contract.py`

### PR Bundle 5: AC trace / PR follow-up

AC Trace Ledger、completion gate、PR 作成後 review follow-up loop、compact/resume 復元正本。

代表ファイル:

- `references/ac-trace-ledger.md`
- `references/context-budget.md`
- `references/state-machine.md`
- `references/verification-before-completion.md`
- `scripts/lint-resume-integrity.py`
- `skills/gdd-completion-check/SKILL.md`
- `skills/gdd-pr-review/SKILL.md`
- `skills/gdd-pr-review-followup/SKILL.md`
- `skills/gdd-status/SKILL.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `tests/test_e2e_replay_fixtures.py`
- `tests/fixtures/e2e-replay/`
- `tests/test_p0_meta_feedback_contract.py`
- `tests/test_p0_p1_operational_hardening_contract.py`

---

## GDD 本体配布 PR に混ぜない

以下は GDD 本体の配布 PR に混ぜない。必要なら別 PR または個人設定として扱う。

| 対象 | 扱い | 理由 |
|---|---|---|
| `.vscode/` | 原則除外。プロジェクト標準設定として配るなら別 PR | IDE / 個人・組織設定が混ざりやすい |
| Snyk organization 設定 | GDD plugin PR には含めない | security scan plugin / IDE 設定の文脈で扱う |
| temporary output / eval scratch | 除外 | 再現性がなく、配布物ではない |
| unrelated repository settings | 除外 | GDD plugin の契約説明と関係しない |

---

## Release Candidate チェック

PR を出す直前に以下を満たす。

1. `git status --short` の untracked が、PR に入れる新規ファイルか除外対象か分類済み
2. `git diff --stat` が 1 つの PR 説明で収まる
3. 変更断片（`changelog.d/`）の Affected Files と実 diff が一致している
4. `python3 -m unittest discover -s plugins/gate-driven-development/tests -p 'test_*.py'` が通る
5. `bash plugins/gate-driven-development/tests/validate-plugin.sh` が通る
6. `python3 scripts/sync-plugin-tooling.py --check` が通る
7. `git diff --check` が通る
8. changed GDD primitive がある場合、Superpowers Benchmark Summary を PR 本文または release evidence に書く
9. HITL / prompt / skill 文面を変えた場合、**GDD Complexity Budget** を確認する。内部用語数、HITL行数、承認ポイント数、正本重複、似たルールの重複が超過していないかを見て、読めない場合は easy summary か詳細表削減で直す
10. human-check sample がある場合、`scripts/lint-human-check-language.py <sample.md>` を実行し、説明なしの内部用語が出ていないこと、および最終HITL（`<gdd-stop reason="human-check-waiting">` を含むもの）に必須フレーズ 6 語（`整理した要件` / `実装する方法・内容` / `検証する方法・内容` / `どこまで自走するのか` / `判断ポイント` / `段階実装サマリー`。`段階実装サマリー` は各 stop marker 直前のタグがすべて `stage="none"` のときは求めない）が揃っていることを確認する。**OK 境界（OKで進む範囲 / OKでも許可されないこと）を見るのは `lint-hitl-decision-quality` であって本 lint ではない**
11. requirements.md に `HITL Outcome Audit` がある場合、`scripts/lint-hitl-outcome-audit.py <requirements.md>` を実行し、`mismatch` / `unverified` が残っていないことを確認する
12. generated HITL sample がある場合、`scripts/lint-hitl-complexity.py <sample.md>` を実行し、HITL行数 / 承認ポイント数 / 詳細表数 / 内部用語数が GDD Complexity Budget を超過していないことを確認する
13. generated HITL sample がある場合、`scripts/lint-hitl-display-integrity.py <sample.md>` と `scripts/lint-hitl-decision-quality.py <sample.md>` を実行し、壁打ち差分（`採用しない案` / `却下した代替案` のいずれか）、ズレ確認、完了条件の変換 / テスト化確認 / 技術スタック確認 / 作り方の重要判断 のいずれか、OKで承認する/しない境界が最終表示HITLに残っていることを確認する
14. requirements.md がある場合、`scripts/lint-plan-consistency.py --entry requirements <requirements.md>` を実行し、AC と承認ポイントの項目に `根拠:`・`計測:` の欄が書かれていることを確認する
15. resume / compact recovery / SessionStart hook 変更がある場合、`scripts/lint-resume-integrity.py --steering-dir <.steering/task> --branch <branch> --worktree-path <worktree>` と `scripts/lint-worktree-provenance.py --steering-dir <.steering/task> --branch <branch> --worktree-path <worktree> --pr-head-branch <branch>` の pass / fail sample を確認する
16. requirements / design / tasklist / state の連続性を変える場合、`scripts/lint-state-tasklist-continuity.py --steering-dir <.steering/task>` を実行する。canonical template 準拠の artifact に対してこの runner が強制するのは「build-like な再開なのに `tasklist.md` に `## Current Task` が無い」ことだけで、requirements / design 改訂後に古い tasklist から再開していないことの担保は `Route In Progress` の運用（`references/task-breakdown-steps.md` Step 2）側にある。exit 0 を「stale tasklist でない」の証跡として記録しない
17. 開発元の release gate として、`tests/fixtures/e2e-replay/` の bad artifact が期待どおり fail することを `test_e2e_replay_fixtures.py` で確認する。配布先に replay fixture 実行は求めず、配布先は導入 smoke と事故ログ共有だけでよい
18. resume混線、worktree汚染、skill arbitration、context loss、code reading gap、PR review follow-up 早期終了などの workflow 事故があった場合、`references/workflow-incident-review.md` と `references/prompt-contract-map.md` に従って再発防止を記録し、可能なら `tests/fixtures/e2e-replay/` に fixture を追加する

---

## E2E Replay Fixture Authoring

E2E replay fixture は **開発元だけで実行する** release gate。配布先に replay fixture 実行は求めない。配布先は導入 smoke と事故ログ共有だけでよい。

追加するタイミング:

- workflow 事故が再発しやすく、artifact と linter で再現できる
- HITL / state / requirements / worklog の bad artifact が「落ちるべき理由」を説明できる
- 既存 runner で表現できる。できない場合は、fixture 追加の前に linter と runner を追加する

基本構成:

```text
tests/fixtures/e2e-replay/<scenario>/
  expected.json
  <bad artifact>
```

`expected.json` の必須項目:

```json
{
  "scenario": "<scenario>",
  "runner": "<runner>",
  "expected_status": "fail",
  "path": "<bad artifact path>",
  "expected_reason_contains": ["<failure token>"]
}
```

`expected_status` は通常 `fail` にする。目的は、過去の workflow 事故を再現する bad artifact が release gate で落ちることを確認するため。pass fixture を足す場合は、同じ runner の正常系が必要なときだけにする。

対応 runner:

| runner | artifact | 使う場面 |
|---|---|---|
| `lint-resume-integrity` | `.steering/<task>/state.md` など | resume混線、worktree汚染、branch/task 不一致 |
| `lint-hitl-display-integrity` | `final-hitl.md` | 壁打ち差分（採用しない案 / 却下した代替案）、ズレ確認、完了条件 / テスト化 / 技術スタック / 作り方の重要判断 が HITL から抜ける |
| `lint-hitl-decision-quality` | `final-hitl.md` | HITL は出ているが、OKで何を承認するか、何を承認しないか、人間が今何をするかが判断できない |
| `lint-human-check-language` | `final-hitl.md` | 非エンジニアに分からない内部用語が説明なしで出る、または最終HITLに必須フレーズ 6 語（`整理した要件` / `実装する方法・内容` / `検証する方法・内容` / `どこまで自走するのか` / `判断ポイント` / `段階実装サマリー`。各 stop marker 直前のタグがすべて `stage="none"` のときは `段階実装サマリー` を除く）が揃っていない |
| `lint-hitl-complexity` | `final-hitl.md` | HITL が長すぎる、承認ポイントや詳細表が多すぎる |
| `lint-pr-review-followup-state` | `state.md` / `worklog.md` | PR 作成後レビュー指摘ループが、push / 再レビュー依頼 / fresh evidence なしに clean 扱いになる |
| `lint-worktree-provenance` | `.steering/<task>/state.md` + branch / PR / diff metadata | task、branch、PR head、worktree、steering、diff scope が混線している |
| `lint-state-tasklist-continuity` | `.steering/<task>/state.md` / `tasklist.md` / `requirements.md` / `design.md` | build-like な再開なのに `tasklist.md` に `## Current Task` が無い。`Requirements Revision` / `Design Revision` / tasklist の `Task ID` / design の `Stage Continuity Source` は canonical template が持たない任意 field で、steering 側が記録した場合だけ突き合わせる。requirements / design 改訂後の tasklist 再生成そのものは `Route In Progress` の運用（`references/task-breakdown-steps.md`）が正本で、本 runner では機械強制していない |

`lint-state-tasklist-continuity` について「canonical artifact に対して強制するのは `## Current Task` の存在だけ」と限定した根拠。

**測った入力集合**: `references/*.md` 63 本と `skills/*/SKILL.md` 28 本の全走査（2026-09-03 実測）。`Requirements Revision` / `Design Revision` は該当 0 件、`references/task-breakdown-steps.md` の Agentic Worker Header は `Goal` / `Architecture` / `Tech Stack` / `Approved Direction` / `Stage Continuity Source` / `Human Recheck Boundary` の 6 field で `Task ID` を含まない、`Stage Continuity Source` は `requirements.md` / `state.md` / tasklist header の field で `design.md` 側の必須見出しではない。走査していない範囲、すなわち host 側テンプレート・利用者が独自に足した field・`.steering/` に手で書き足された label の外側については主張しない。

HITL が読みにくい事故は、原因で runner を分ける:

- 内部用語が説明なしで出る、または最終HITLに必須フレーズ 6 語（`判断ポイント` など）が揃っていない: `lint-human-check-language`
- 長すぎる、承認ポイントや詳細表が多すぎる: `lint-hitl-complexity`
- 壁打ち差分（採用しない案 / 却下した代替案）や完了条件など、承認に必要な欄が抜ける: `lint-hitl-display-integrity`
- HITL は出ているが、OKで何が進むか判断できない: `lint-hitl-decision-quality`
- 文章の硬さ、抽象度、言い回しだけが問題: deterministic に判定できる条件へ落とせる場合だけ linter 化する。それ以外は `references/prompt-contract-map.md` の residual risk に残す

PR review follow-up の artifact は、`PR Review Follow-up Status: clean` のような状態宣言が `state.md` にあるなら `state.md` を優先する。事故の証跡が `worklog.md` だけにある場合は `path` を `worklog.md` にする。修正 push 後に clean を名乗る fixture では、`Post-fix Fresh PR Review Evidence` と `Post-fix Fresh PR Checks Evidence` が無い状態、または checks が pending / failed の状態を再現すると、早期終了を検出しやすい。

未対応 runner の場合:

1. その事故を検出する最小 linter を `scripts/` に追加する
2. `tests/test_e2e_replay_fixtures.py` に runner 分岐を追加する
3. bad artifact と `expected.json` を追加する
4. `python3 -m unittest plugins/gate-driven-development/tests/test_e2e_replay_fixtures.py` で、bad artifact が期待どおり fail することを確認する

failure token は、linter の出力に含まれる事故理由を選ぶ。例: `説明なしの内部用語`、`clean claim requires fresh review evidence`、`branch slug mismatch`。単なるファイル名だけを token にしない。

---

## 判断

- チーム外への配布に向けた最初の PR は **PR Bundle 1: distribution-readiness** を推奨する。
- Bundle 2-5 は関連するが、すべてを 1 PR にまとめるとレビュー観点が散る。広めに配る前の説明可能性を優先し、bundle ごとに PR を分ける。
- どうしても 1 PR にまとめる場合は、PR 本文を bundle 見出しで分け、各 bundle の verification evidence を個別に書く。
