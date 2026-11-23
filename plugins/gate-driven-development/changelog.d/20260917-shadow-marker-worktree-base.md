---
type: patch
---

#### Summary

SessionStart hook の `[gdd:shadow-marker]` は、worktree の置き場として `~/.gdd/worktrees/<repo>` と `<current>/.worktrees` だけを探していた。一方、worktree を作る側（`skills/gdd-using-git-worktrees`）は、プロジェクトルートの `.gdd-config.md` の `Worktree Base:` を優先する。そのため、設定済みの Worktree Base に置いた worktree（別 clone で作ったもので、現 repo の `git worktree list` に出ないもの）の非終端 steering が警告に出なかった（PR 旧#101 の Codex adversarial-review F2）。探す置き場を、作る側と同じ `<Worktree Base>/<repo>` に揃えた。

#### Fixed

- `detect_shadow_gdd_markers` の置き場に、次の Worktree Base を足した。既定の `~/.gdd/worktrees` も引き続き探す（設定を変える前に作った worktree を隠さない）
  - `GDD_WORKTREES_ROOT`（`scripts/find-stale-steerings.sh` と同じ環境変数）
  - 現 worktree と root checkout（`git worktree list` の先頭）の `.gdd-config.md` にある `Worktree Base:`。値は既存の `gdd_extract_doc_field` で読む（fence 内の記入例は値にしない）。先頭の `~` は `$HOME` に展開し、相対パスは設定ファイルのあるディレクトリを基準にする
- 受理する形は `<Worktree Base>/<repo>/<task>/.steering/<id>/state.md` だけで、探索の深さ・現 worktree の除外・重複除去・5 件の上限は従来どおり
- SessionStart の active steering（`[gdd:reboot]`）・複数 steering（`[gdd:warning]`）・shadow-marker の 3 分岐は、dir 名・パス・state.md の値を `"` と `\` だけエスケープして出力していた。TAB や ESC を含むと JSON が壊れ、additionalContext 全体が落ちていた（変更前からある穴。`Worktree Base:` で任意のディレクトリを指せるようになり、到達面が広がった。PR 旧#105 レビュー）。3 分岐とも出力の直前で、compact 経路と同じ `gdd_truncate_chars`（不正な UTF-8 を捨てる。上限は自分の長さで切り詰めない）と制御文字の除去を通すようにした。制御文字の除去は `LC_ALL=C` で行う。UTF-8 ロケールの BSD `tr` は不正なバイト列で失敗し、`set -euo pipefail` の下で hook 全体が出力無しで止まるため。python3 が失敗して結果が空になったとき（壊れた shim、UTF-8 以外のロケール）は、案内を空にせず制御文字の除去だけに戻す

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/tests/test_session_start_shadow_marker_scope.py`
- `plugins/gate-driven-development/tests/test_session_start_context_json_control_chars.py`（新規）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_session_start_shadow_marker_scope.py` に `ConfiguredWorktreeBaseTests` を追加した（入口は SessionStart hook の実行。`git worktree add` を使わずに置き場へ直接作る）。設定済み base の steering が警告に出る／`~` と末尾スラッシュを受ける／root checkout の未追跡の設定を linked worktree から読む／`GDD_WORKTREES_ROOT` を探す／設定済み base があっても既定の置き場も探す／設定済み base でも fixture の深さは拾わない／fence 内の記入例は設定にしない／存在しない base は飛ばして他の候補を出す
- 新規 contract test: `tests/test_session_start_context_json_control_chars.py`（入口は SessionStart hook の実行。TAB・ESC 入りの dir 名で reboot / 複数 steering / 設定済み base の shadow-marker の出力が JSON として読め、制御文字を含まない／不正な UTF-8 を含む requirements.md の値でも、UTF-8 ロケールで hook が止まらず、出力が置換なしの UTF-8 として読める／PATH の先頭に失敗する python3 を置いても 3 分岐の案内が空にならない）
- 限界: `~/.gdd/config.local.md` の `Worktree Base:` は読まない。worktree を作る側が読まない値で（`references/operation-levels.md` の解決順の注記）、読んでもそこに worktree は作られないため。このリポジトリ自身に `.gdd-config.md` は無く、新しい経路の実運用での確認は 0 件。python3 が無い・失敗する環境では不正な UTF-8 は残る。`gdd_truncate_chars` は python3 が失敗しても成功を返し、空文字を出す（既存の compact 経路・post-merge 経路・直前ターン失敗の前置きも同じ。この PR では触っていない）。compact 経路のサイクル上限の警告は `GDD_MAX_AUTO_CYCLES` を検証せずに埋め込むため、改行を含む値で JSON が壊れる（変更前から。この PR では触っていない）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
