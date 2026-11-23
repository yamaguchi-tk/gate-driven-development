# GDD 自身を開発するときのルール

GDD で GDD を開発するときは、**動いている道具と作っている成果物が同一**になる。壊すと自分の workflow が止まるため、層ごとに開発場所を変える。

## 層ごとの影響範囲

| 層 | 読み込みのタイミング | 壊れたときに起きること |
|---|---|---|
| `hooks/scripts/*.sh` / `*.py` | **毎回パス実行** | **即座に影響**。`PreToolUse` は Bash 実行のたびに走る |
| `skills/*/SKILL.md` | その skill を使うときに読む | 次にその skill を呼ぶまで無害 |
| `references/*.md` | 参照時に読む | 同上 |
| `.claude-plugin/plugin.json` / `hooks/hooks.json` | セッション開始時 | 次のセッションから |

危険は hook に集中する。skills / references は**壊しても次回参照時まで影響が出ない**。

## 開発場所の使い分け

- **skills / references は local を直接編集してよい**。次に呼んだ瞬間に反映されるので、その場でドッグフーディングできる
- **hooks は worktree で開発しテストが green になるまで local に入れない**。`tests/validate-plugin.sh` と `python3 -m pytest tests/ -q -n auto`（並列。直列より大幅に速い。`pytest-xdist` 必須） の両方を通してから反映する
- **テストの階層（2026-09-06）**: impl-gate の各 round と remediation は**変更ファイルに対応する契約テストのみ**（`python3 -m pytest tests/test_<対象>_contract.py -q`。対応が不明なら `-k <変更した関数名・ファイル名>`）。**フルスイートは CI（`plugin-lint` の `gdd-plugin`）が PR ごとに回す**。手元では completion-check と pre-PR でも対応する契約テストだけを回す（2026-09-20 まではフルを completion-check と pre-PR の 2 回だけ手元で回していた）。CI は PR を作った後の push（と main への push）で走るので、フルの結果は PR 作成後に `gdd-plugin` の success で確かめる。round ごとにフルを回さない（round ごとにフルを回すと待ち時間が積み上がり、対象テストだけに絞っても問題は出なかった）
- `plugin.json` / `hooks.json` はセッション開始時にしか読まれないので急がない。worktree で変更し、反映は次セッションでよい

## 壊れたときの復旧

1. **hook を全停止する**（最優先）

   ```bash
   touch ~/.claude/gdd-hooks-disabled
   ```

   全 hook runner の先頭に `gdd_kill_switch_active && exit 0` があり、このファイルがあれば即 no-op で抜ける（`hooks/scripts/lib/kill-switch.sh`）。純 bash で python / git に依存しないため、それらが壊れていても効く。解除は `rm ~/.claude/gdd-hooks-disabled`

2. **local を戻す**。local は正本なので git 履歴が無い。直前の publish 済み状態へ戻すなら `rsync -a --delete <repo>/plugins/<name>/ ~/.claude/plugins/local/<name>/` を使う（**未 publish の local 変更は失われる**ため、先に `python3 scripts/check-plugin-drift.py` で差分を確認する）

3. hook 本体は fail-open 設計で、python / git が見つからない場合も `exit 0` で抜ける。GDD active のときだけ警告付きで block する

## 適用範囲の注意

- kill switch が止めるのは **hook だけ**。skills / references の破損には効かない（復旧は git）
- 「skills / references は安全」は**次回参照時まで影響が出ない**という意味であり、壊れた契約を読んだ LLM が誤動作しないことまでは保証しない
