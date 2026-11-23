# Autonomous Model Workers

GDD が Codex / Cursor / Claude Code を「工程ごとに適切な worker へ渡す」ための契約。

## 原則

- **main session is the only state owner**: `state.md` / `tasklist.md` / `worklog.md` / human-check 出力を更新してよいのは main session だけ。
- **worker is an isolated artifact producer**: worker は `worker_runs/<run_id>/result.json` に成果物案を返す。正本 artifact へ統合するのは main session。
- **requested is not applied**: `requested_model` / `requested_effort` は起動時に要求した値。実行ログや metadata で確認できない限り `applied_model` / `applied_effort` は `unknown`、`application_status` は `unverified` にする。
- **do not claim main-session model switching**: Codex Desktop の同一メイン会話のモデルが裏で切り替わったとは表示しない。GDD が制御するのは worker 起動時の model / effort request。
- **initial rollout is serial**: 初期実装では worker を直列に実行する。並列化は state 統合・再開・conflict handling の契約が通ってから。
- **Recommended model is not execution**: `setup-gdd-loop.sh only reports a recommendation`。`Recommended model` は bootstrap の案内であり、実際にその model / effort が適用された証拠ではない。`GDD phase dispatch` が `scripts/run-gdd-worker.py` を呼び、`worker_runs/<run_id>/result.json` を残して初めて requested execution と扱う。
- **phase dispatch must call the worker runner**: Codex / Cursor で phase ごとの model / effort を使い分ける場合、phase dispatch は `scripts/resolve-gdd-model.py` を直接表示用途で呼ぶだけでは不十分。`scripts/run-gdd-worker.py` を通して requested / applied / application_status を記録し、main session が検証して統合する。

## Phase Routing

| Phase / lane | Worker model | effort | 扱い |
|---|---|---|---|
| formal gate: brainstorming / requirements / design / impl / completion | `gpt-5.5` | `medium` | 通常の品質判断。未確認なら HITL または retry |
| general heavy: implementation / debug / refactor / advisory review | `gpt-5.5` | `low` | コスト最適化。risk signal があれば `high` |
| risk escalation: undocumented / security-sensitive / large working-set / final review | `gpt-5.5` | `high` | formal gate も含めて重要判断は high |
| light task: task-breakdown / TDD / pr-review / receiving-code-review | `gpt-5.4` | `medium` | mini には落とさない |
| leaf: status / metrics / worktree | `gpt-5.4` | `low` | state / routing source を読むため mini 不使用 |
| cheap read-only lane | `gpt-5.4-mini` | `high` | 短い要約・リンク確認・一覧整形。state 更新と routing 判断は禁止 |

## Dispatch Contract

Codex / Cursor の通常 GDD フローでは、phase ごとの実行単位を以下に分ける。

- bootstrap: `setup-gdd-loop.sh` が候補と `Recommended model` を表示する。これは実行ではない。
- GDD phase dispatch: `scripts/run-gdd-worker.py --runtime <codex|cursor> --phase <phase> --text <intent> --cwd <worktree>` を呼び、model / effort requested execution を作る。
- integration: main session が `worker_runs/<run_id>/result.json` を読み、scope / artifact / safety を確認してから `state.md` / `tasklist.md` / `worklog.md` へ統合する。

代表例:

- `gdd-design-gating -> gpt-5.5 / medium`
- `gdd-design-gating + security-sensitive -> gpt-5.5 / high`
- `gdd-task-breakdown -> gpt-5.4 / medium`
- `gdd-status -> gpt-5.4 / low`

formal gate で `application_status=unverified` の場合は、軽量 model に黙って落とさず、HITL に「要求した model / 実際の確認状態 / 判断への影響 / 次に選べること」を出す。

## Worker Result Schema

`worker_runs/<run_id>/result.json` は最低限以下を含む。

```json
{
  "run_id": "20260611-123456-gdd-design-gating",
  "phase": "gdd-design-gating",
  "runtime": "codex",
  "requested_model": "gpt-5.5",
  "requested_effort": "medium",
  "applied_model": "unknown",
  "applied_effort": "unknown",
  "application_status": "unverified",
  "worker_exit_status": "not_run",
  "integration_status": "pending_main_review",
  "artifacts": [],
  "warnings": []
}
```

`application_status`:

- `planned`: dry-run で起動引数だけ作った
- `verified`: 実行 metadata から model / effort を確認できた
- `unverified`: worker は成功したが実適用 metadata は取れていない
- `unavailable`: model / effort / runner が使えなかった
- `failed`: worker が失敗した

`integration_status`:

- `pending_main_review`: main session がまだ正本へ統合していない
- `integrated`: main session が検証後に正本へ統合した
- `rejected`: 不正成果物・scope 不一致・機密混入などで採用しない

## Fallback / Stop Rules

- formal gate で `application_status` が `unavailable` / `failed` / `unverified` の場合、軽量モデルへ黙って落とさない。`needs_human_acceptance` または heavy retry を要求する。
- non-formal phase では `unverified` を警告付きで許容できるが、status / PR body で「適用確認済み」と書かない。
- worker output が schema 不正、artifact 欠落、timeout、AC ID 欠落の場合、次 phase に進めない。
- retry する場合は新しい `run_id` / `attempt` を付ける。再開時は `integrated` 済みだけを正本扱いする。

## HITL / Status 表示

人間向けには model 名より「品質レベル」「適用状態」「判断への影響」を前面に出す。

```text
モデル実行計画:
- 推奨: 設計レビューなので高精度モデルを使います
- 要求: gpt-5.5 / medium
- 実際: 適用未確認
- 影響: 判断品質に影響する可能性があります
- 次に選べること: このまま進める / 高精度モデルで再実行 / 人間が確認して採用
```

## Test Contract

- phase ごとの model / effort から worker 起動引数が決定的に生成される
- `requested_*` と `applied_*` を混同しない
- 実適用を確認できない場合は `unknown` / `unverified` として残す
- model unavailable 時に formal gate が silent fallback しない
- worker 成果物が不正なら main state は次 phase に進まない
- replay fixture は実モデルに依存せず fake runner で同じ state / status を再現する
