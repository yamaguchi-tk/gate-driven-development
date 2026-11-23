# CI GUARDS

> **対象**: GDD を導入するプロジェクトの repository maintainer
> **目的**: raw task `.steering/<task>/` が PR / main に混入する前に機械的に止める
> **上位正本**: `docs/SECURITY.md` / `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`

---

## なぜ必要か

standard 運用では、raw task `.steering/<task>/` は branch-only working state であり、main に残す正本ではない。次回以降に読む判断は `docs/adr/`、PR body、CI / test evidence、採用済み repo-level learned-patterns に蒸留する。

GDD の completion-check も `.steering/<task>/` を PR に含めないよう確認するが、LLM の自己申告だけにすると読み落としや別経路 merge で漏れる。導入先 repository の CI に raw steering guard を入れることで、PR / main への混入を機械的に止める。

---

## GitHub Actions snippet

導入先 repository に GDD plugin の `scripts/check-no-raw-task-steering.py` をコピーするか、plugin path から実行できるようにして、pull request CI に以下を追加する。snippet は repo 内 `scripts/check-no-raw-task-steering.py` にコピーした場合の例。plugin path から直接実行する場合は、`python3 /path/to/gate-driven-development/scripts/check-no-raw-task-steering.py --root . --against "origin/${{ github.base_ref }}"` のように `--root .` を付けて導入先 repo を検査対象にする。local staged check も同じく `python3 /path/to/gate-driven-development/scripts/check-no-raw-task-steering.py --root . --staged` とする。

```yaml
name: gdd-guards

on:
  pull_request:

jobs:
  gdd-guards:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Reject raw task steering
        run: |
          python3 scripts/check-no-raw-task-steering.py --against "origin/${{ github.base_ref }}"
```

monorepo でも `services/foo/.steering/<task>/state.md` のようなサブディレクトリ配下の raw task steering を検出する。repo-level learned-patterns（`<repo-root>/docs/learned-patterns.md`。このプラグイン自身の `docs/` とは別物）は `.steering/` の外に置く規約のため、この検査の対象にそもそも含まれない。採用済み判定の正本は `skills/gdd-completion-check/SKILL.md` の repo-level learned-patterns 節で、default branch で tracked 済み、または `.gdd-config.md` / repo docs に保存先が明記されている場合に限る。

---

## Local pre-PR check

CI で落ちる前に、PR 作成前のローカル確認として同じスクリプトを実行する。

```bash
python3 scripts/check-no-raw-task-steering.py --staged
python3 scripts/check-no-raw-task-steering.py --against origin/main
```

`--staged` は commit 前の `git add` 済みファイルだけを見る。raw task `.steering/<task>/` を誤って stage した時点で気づけるため、push / PR / CI まで待たずに修正できる。`--against origin/main` は PR の最終 diff に raw steering が残っていないことを確認する。

このチェックが fail した場合は、raw task `.steering/<task>/` をそのまま PR に入れない。重要判断を `docs/adr/`、PR body、CI / test evidence、採用済み repo-level learned-patterns に蒸留してから、tracked raw task steering を除去する。

誤って `git add` しただけなら、まず staged から外す。

```bash
git restore --staged .steering/<task>/
git restore --staged services/foo/.steering/<task>/  # monorepo 例
```

すでに tracked / committed 済みの場合は、ADR 等へ蒸留してから `git rm -r .steering/<task>/` などで PR diff から除去する。機密が混入した可能性がある場合は、自分で push / PR 作成を続けず、repository maintainer に報告する。

### Optional pre-commit hook

導入先 repository で早めに止めたい場合は、`.git/hooks/pre-commit` に以下を置く。

```bash
#!/usr/bin/env bash
set -euo pipefail
python3 scripts/check-no-raw-task-steering.py --staged
```

この hook は raw task `.steering/<task>/` の stage を止めるだけで、`.steering/` の外に置く repo-level `<repo-root>/docs/learned-patterns.md` には影響しない。

---

## Branch-only handoff の注意

別マシン・別ホスト・別人へ引き継ぐために raw task `.steering/<task>/` を task branch へ一時 commit / push する運用は、原則ではなく例外扱いにする。必要な場合だけ、以下を満たす。

1. push 前に機密情報チェックを通す
2. PR 作成前に ADR / PR body 等へ判断を蒸留する
3. PR の最終 diff から raw task `.steering/<task>/` を除去する
4. squash merge を前提にし、merge 後は handoff branch を削除する

`git rm` による net-zero 化は main の最終 tree を守るが、remote branch の中間履歴から raw steering を完全に消すものではない。機密が混入した可能性がある場合は、自分で push や PR 作成を続けず、ユーザーまたは repository maintainer に報告する。
