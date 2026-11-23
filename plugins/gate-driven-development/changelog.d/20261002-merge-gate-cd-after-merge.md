---
type: patch
---

#### Summary

merge gate は、コマンドのどこかに `cd`・`pushd`・`popd` があると、マージの実行先を 1 つに決められないとして止めていた（`pr-target-unresolvable`）。そのため、`gh pr merge <URL> --merge && cd <dir> && git pull` のように、マージの後で別のディレクトリへ移る形まで止めていた。今後は、切ってよいと言える形のコマンドに限って、マージを含む区切り（`;`・`&&`・`||`・`|` で区切った単位）より後ろを実行先の判定に使わない。マージより後ろの `cd` は、走り終わったマージの実行先を変えないためである。ただし、利用者のシェルの設定に予約語（`repeat` など）の別名（alias）を置いていると、その別名でマージを囲んだ形も切ってしまい、後ろの `cd` の後で別の repo のマージが走りうる（今までは止めていた）。

#### Fixed

- `hooks/scripts/lib/gh_command_parse.py` は、マージより後ろの `cd`・`pushd`・`popd`・`env -C` などの実行先を変える指定を、マージの実行先の判定に使わない。マージより前に `cd` があれば、今までどおりその `cd` で判定する
- 切ってよいと言える形は、コマンド文字列が次をすべて満たすものに限る。外れた形は今までどおりコマンド全体で判定する（後ろに `cd` があれば止める）
  - 文字が、語の文字（英数字・かな漢字など）・空白・`./:=@%+,'"&|;~<>-` だけでできている（括弧・波括弧・`$`・バッククォート・`\`・`!`・`[`・`#`・`*` などを含まない）
  - heredoc（`<<`）、単独の `&`（`&&`・`>&`・`&>` は除く）、bash の予約語、zsh の `repeat`・`foreach`・`end`、`trap`・`sched` の語を含まない
  - `merge` の語がちょうど 1 つ（2 つ以上のマージ、引用符の中の `merge` を含む形は外れる）
  - 縮退した token 列（引用符が閉じない形）でなく、入れ子 shell（`bash -c`・`eval`）を含まない
  - マージより前の区切りが `&&`・`;` だけ（パイプ・`||` があれば切らない）
- マージの後に演算子を置かずに改行して `cd` を続ける形は、改行を区切りとして読まないので、今までどおり止める

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/tests/test_merge_gate_cd_after_merge.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_cd_after_merge.py` を足した。マージの後ろに `cd`・`pushd`・`popd` を `&&`・`;`・`||`・`|` で続けた形が、マージ単独と同じ判定になり、前と後ろに `cd` がある形は前の `cd` だけの形と同じ判定になる。マージを囲む構文（zsh の `repeat`・括弧なしの `foreach` を含む）・バッククォート・語の途中の行継続・`trap`・`$(…)`・heredoc を含む縮退した形・入れ子 shell・`&`・演算子の無い改行の形と、マージより前と後ろで別の repo に `cd` する形は、今までどおり block する。`2>&1 | tail` を挟む形、`&& cd <dir>` の後に改行で続く形、`cd ~/…` は切る。マージより前にパイプ・`||` がある形は切らず、`cd /Q >/dev/null && gh pr merge …`・`cd /Q || exit 1; gh pr merge …` は今までどおり `/Q` を実行先にする。マージの前に区切りが 5 万個あっても、切り出しが線形時間で終わる
