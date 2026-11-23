---
type: minor
---

#### Summary

`references/subagent-dispatch.md` の dispatch template（design-gating / task-breakdown / TDD / implementation-gating / completion-check、および `gdd-subagent-driven-implementation` の GREEN 並列 worker・remediation worker・`gdd-code-simplifier` REFACTOR dispatch）は `## Steering Dir` を渡すが、subagent の cwd は呼び出し元セッションのままなので、ファイルを書く phase（RED / GREEN / refactor）が呼び出し元 worktree へ書いてしまう事故が 2026-09-08 に実際に発生していた（X-33）。RED は「失敗すること」が期待値のため、書き先が違っても RED としては成立してしまい、GREEN が正しい worktree に現れないと気づけない設計だった。全 dispatch 経路に `## Worktree`（絶対パス）を必須項目として追加し、RED Evidence の worktree 記録と `gdd-implementation-gating` での独立検出を追加した。

#### Added

- `references/subagent-dispatch.md`: 共有の `## Worktree Binding Precheck` 節を追加し、5 template すべてに `## Worktree`（`## Steering Dir` の 2 階層上にある worktree 絶対パス）を追加した。subagent は着手前に `git -C "<## Worktree の値>" rev-parse --show-toplevel` を実行し、その出力を realpath 相当で正規化した値が `## Worktree` 自身と一致するかを確認する（subagent 自身の ambient cwd とは比較しない。cwd は呼び出し元セッションのままなので、正常系でも ambient cwd とは一致しないため）。不一致・パス不在・コマンド失敗はすべて同じ扱いで fail-closed とし、いかなるファイルも書き込まず `worktree_mismatch` を返して停止する。`gdd-implementation-gating` 用の Post-Return Routing には、他の template と揃える形で `worktree_mismatch` の catch-all（無限再 dispatch 防止）を追加した
- `skills/gdd-test-driven-development/SKILL.md`: 「Worktree Binding（必須）」節を追加した（既存の「AC ID Binding（必須）」と同型）。RED Evidence に `Worktree: <path>` 行を必須化した。値は precheck 実行後に観測した `git rev-parse --show-toplevel` の出力（宣言値ではなく観測値）とし、未記載なら fail-closed で reject する。この記録自体は自己申告であり単独では検証できないことを節内に明記し、実効性の主体が `gdd-implementation-gating` の独立検出（次項）にあることを disclose した
- `skills/gdd-implementation-gating/SKILL.md`: Step 1 差分 scope guard に 1d「RED Evidence Worktree Provenance Check」を追加した。RED Evidence の `Worktree:` 値が `## Worktree` と一致するかに加え、ファイルパスを持つ形式（形式1/3）は `git diff <default-branch>...HEAD --name-only`（1c で確定）または `git status --porcelain` の未 commit 分にそのパスが含まれるかを確認する（コミット済みの差分だけでなく、コミット前の正常系も拾う）。ファイルパスを持たない形式（形式2、`verification:` のみ）は値一致チェックのみを適用し `provenance: file-path-absent` として記録する。`Worktree:` 未記載・値不一致・diff/未 commit いずれにも未掲載・`git diff`/`git status` 自体の実行失敗のいずれかなら High finding とし、reviewer を起動せず `changes_requested` で `gdd-systematic-debugging` に戻す（TDD subagent 自身の自己検査に依存しない独立検出であり、本 X-33 の実効性の主体）
- `skills/gdd-subagent-driven-implementation/SKILL.md`: GREEN の並列 worker dispatch（Step 2a）・remediation worker dispatch（Step 3）・REFACTOR の `gdd-code-simplifier` dispatch（Step 14a）にも `## Worktree` と § Worktree Binding Precheck の必須実行を追加した（これらは production code を書く phase であり、RED と同じ書き込み事故が起こり得るため）
- `hooks/scripts/lib/secret_scanning.py`: `.steering/**` 書込み guard の `find_local_path()` に、新設した `- Worktree: <path>` フィールド用の例外を追加した（追加しないと、この新しい必須フィールド自体が既存の「ローカル絶対パス denied」guard に弾かれ、RED Evidence を書けなくなる）。既存の `Active Worktree Path` 例外（部分文字列一致）とは違い、フィールド行全体（ラベル + 値のみ）への fullmatch に限定した。行頭一致や部分文字列一致だと、正規の値の後ろへ別の漏洩パスを付け足す形で素通りできてしまう（実測で確認・テストで固定）ため
- `references/subagent-dispatch.md`: 2 巡目独立レビューで見つかった、Task-Breakdown Post-Return Routing に fail-closed catch-all が無かった欠落（他 4 template には既にある）を追加し、`worktree_mismatch` を Subagent Report Contract に明示登録した
- `skills/gdd-implementation-gating/SKILL.md`: 1d に、`## Worktree` が未提供（dispatch template を経由しない inline 実行等）の場合の `state.md` `Active Worktree Path` への fallback、バッククォート等の装飾を除いた realpath 相当の正規化比較、`git status --porcelain` の `git -C` 固定を追加した（cwd の持続に依存しない検証にする）
- `skills/gdd-test-driven-development/SKILL.md`: RED Evidence 例の `Worktree:` 値からバッククォートを除去し、`## Worktree` 自身と同じ「装飾なしの絶対パス」表記に揺れを無くした
- `skills/gdd-subagent-driven-implementation/SKILL.md`: Step 3 の一般的な subagent dispatch（`remediation_loop` 以外の逐次実装でも subagent を使う場合）にも `## Worktree` 必須化を拡大した（従来は `remediation_loop` 分岐だけが対象だった）
- `tests/test_x33_worktree_dispatch_binding_contract.py`（新規）: 上記の contract test。precheck が `git -C` で対象パス自体を検証すること（ambient cwd 比較ではないこと）、`worktree_mismatch` の catch-all（Task-Breakdown 含む全 template）、GREEN/REFACTOR 3 経路の `## Worktree` 必須化、1d のコマンド失敗時 fail-closed・`## Worktree` 未提供時 fallback・比較の正規化を含む
- `tests/test_stop_hook_validate.py`: `- Worktree:` フィールドの許可、フィールド外での「Worktree」という語の言及は引き続き deny、フィールド行に別パスを付け足した場合も deny、の 3 パターンを固定

#### Affected Files

- `references/subagent-dispatch.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `skills/gdd-implementation-gating/SKILL.md`
- `skills/gdd-subagent-driven-implementation/SKILL.md`
- `hooks/scripts/lib/secret_scanning.py`
- `tests/test_x33_worktree_dispatch_binding_contract.py`（新規）
- `tests/test_stop_hook_validate.py`

#### User Action Required

- なし。`/gdd-dev` を使う側は次回 dispatch から自動的に `## Worktree` を受け取る

#### Known limitations

- 対策2（書き込み先が指定 worktree の外なら hook で block する強制）は本 PR の対象外。今回追加したのは自己検査（対策1）と独立検出（対策3）のみで、subagent が自己検査の指示に従わなかった場合の「強制」は無い（自己申告 + `gdd-implementation-gating` での事後検出のみ）。将来同種の実害が再発したら対策2の追加を検討する
- RED Evidence の `Worktree:` 行は、既存の `AC:` と違い `scripts/lint-ac.py` に相当する機械検証を持たない。ドキュメント上「必須」と書いてあるだけで、subagent が省略しても書式検証では検出できない（`gdd-implementation-gating` の 1d が事後に独立検出するのが実質の防止線であり、記録側は前段の自己停止に過ぎない）
- 1d のファイルパス突合（形式1/3）は `git diff` と `git status --porcelain` の両方を見るが、形式2（`verification:` のみ、ファイルパスを持たない）は値一致チェックのみで、diff/uncommitted との突合はできない（そもそも突合対象のパスが無いため）。この限界は SKILL.md 内に明記した
- 1d の `git diff <default-branch>...HEAD --name-only`（1c で確定する既存コマンド）自体は本 PR の対象外のため cwd を pin していない（pre-existing）。1d が新設した `git status --porcelain` 側は `git -C` で pin したが、1c 側の pin は別課題として残る

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`（2753 passed, 4 skipped, 16566 subtests passed）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（全 BLOCK チェック OK、line budget 含む）
- 追加 contract test: `test_x33_worktree_dispatch_binding_contract.py`（14 tests）
- 独立レビュー 1 巡目（read-only, diff-only, 経緯非共有）: High 3 件（H-1: precheck が ambient cwd と比較していて正常系でも不一致になる設計バグ／H-2: 新設 `Worktree:` フィールドが既存 steering-write guard に弾かれる／H-3: GREEN・REFACTOR dispatch が対象外だった）・Medium 5 件をすべて確認・修正した。独立レビュー後の自己点検で、H-2 の修正自体に新しい fail-open（フィールド値の後ろへ別の漏洩パスを付け足すと素通りする）を発見し、fullmatch への変更で追加修正した
- 独立レビュー 2 巡目（push 対象 tip の全差分。前回レビューの sha を state.md に記録していないため軽いレーンの絞り込み条件を満たさず全差分で実施）: High 2 件（Task-Breakdown Post-Return Routing の catch-all 欠落／1d が `## Worktree` 未提供時に未定義動作になる）・Medium 5 件を確認し、判断のうえで対応した。修正: catch-all 追加、fallback 追加、比較の realpath 正規化、`git status` の `git -C` pin、Step 3 の一般 dispatch への拡大、Worktree Binding Precheck 見出しの "5 template" → 実際の 8 経路への訂正、`worktree_mismatch` の Subagent Report Contract への明示登録。対応不要と判断: `find_local_path()` の `Worktree:` 例外が値を制約しないという指摘（フィールドの目的が任意の実 worktree 絶対パスを記録することである以上、値の制約は本末転倒であり、既存の `Active Worktree Path` 例外よりは既に narrow である点は fullmatch で確保済み）
