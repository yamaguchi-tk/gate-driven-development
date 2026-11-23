---
type: patch
---

#### Summary

pre-push gate が、`cd` や `git -C` で書いた push 先の repo を取り違え、検査せずに push を通していた経路のうち、次の形を閉じた。

- 相対パス（`cd repo && git push`・`git -C repo push`）: hook が repo へ移った後も同じ相対パスで steering を探していたので、done・blocked の steering を見つけずに通していた。作業中の steering は、trivial でも証跡があっても止めていた（push 対象の tip が決まらないため）。今は絶対パスで書いたときと同じ判定になる
- `~`・`$HOME`（`cd ~/repo && git push`・`git -C $HOME/repo push`）: 展開していなかったので、GDD の repo と判定されずに通していた。pre-PR gate と同じく、hook の環境変数で展開する。`git --git-dir=~/repo/.git push` のような形も、今は解決できない push として止める
- repo の中のサブディレクトリ（`cd repo/sub && git push`・`git -C repo/sub push`、サブディレクトリで動くセッション）: GDD の repo と判定されずに通していた。pre-PR gate・merge gate と同じく、repo の toplevel で判定する
- 移動先を解決できない `cd`（`cd "$(git rev-parse --show-toplevel)" && git push`・存在しないパス・未定義の変数）: その移動先だけを見て通していた。hook にはコマンドがどこで走るかを決められないので、セッションの作業ディレクトリ（Codex では workdir も）も判定する。別の repo を指すコマンド置換の `cd` は、作業ディレクトリ側の steering で止まることがある
- `CDPATH` が設定されていると、hook の中の `cd` が移った先のパスを出力し、block が効かなくなっていた（`CDPATH` の先の別の repo へ移ることもあった）。merge gate と同じく、hook の中では `CDPATH` を外す
- `git -C -P push` のように `-` で始まる名前の repo も、`cd` の option と取り違えない

コマンドの解釈は変えていないので、`cd a && cd b`（最後の `cd` だけを見る）・`cd /abs && git -C rel` の組み合わせ、引用符の中の `~`・`$HOME`（hook だけが展開する）、セッションの中で export した変数は、今までどおり取り違えうる。gitdir の中を指す root（`git -C repo/.git push`・`.git/hooks` の中での push）も、pre-PR gate・merge gate と同じく今までどおり検査しない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/tests/test_pre_push_root_resolution.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_pre_push_root_resolution.py` を足した（相対パス・symlink・`~`・`$HOME`・`${HOME}`・`--git-dir=~/…`・`CDPATH`・`-P`・サブディレクトリ・解決できない `cd` の root、payload の cwd への fallback、lone surrogate を含む root、読めない steering、展開できない root、空の `--git-dir=`、相対パスで起動した hook の `CDPATH`）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
