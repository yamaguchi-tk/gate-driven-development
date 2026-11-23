---
type: patch
---

#### Summary

Stop hook が停止の判定に使う state.md・post-merge の marker・`.claude/gdd-dev.local.md` が FIFO・ディレクトリ・symlink のループ・指す先の無い symlink のときに、判定を飛ばすか、hook が timeout まで止まっていたのを直した。

- done guard の Route In Progress の検査は、state.md を「無い」と読んで飛ばし、done を通していた。今後は done を止め、理由に state.md のパスと、通常のファイルに置き換える回復手順を出す
- tasklist.md・requirements.md・post-merge の marker が指す先の無い symlink のときも、「無い」と読んでいた。今後は FIFO などと同じく止める側に倒す
- post-merge の marker が symlink のループだと、存在の確認で「無い」と読み、merge cue の後の早い停止を止めていなかった。今後は止める
- `.claude/gdd-dev.local.md` が FIFO だと、hook が timeout まで止まっていた。今後は、ディレクトリ・symlink のループと同じく `.gdd/hook-errors.log` に記録して停止を通す
- bind が無いとき、最新の steering の state.md が通常のファイルでない、最新の steering のディレクトリが steering の外を指す symlink・ループ、または権限で stat できない（task dir や `.steering` に x が無い）と、古い steering の state.md を読んでいた（古いタスクの `human-check-waiting` で停止を許す、古いタスクの回数でポーリング上限を判定する）。今後は古い steering へ飛ばさない
- ポーリング上限の判定は、bind を見ずに最新の steering の state.md を読んでいた。今後は resume-from と同じ steering の state.md を読み、使えない・`.steering` を一覧できないときは `blocked` に倒して `.gdd/hook-errors.log` に記録する。steering を選ぶのは external-review-waiting の停止のときだけで、ほかの停止理由は `.steering` を一覧できなくても今までどおり pause・終了する
- `os.O_NONBLOCK` の無い環境（Windows）では、状態ファイルの読み込みが AttributeError で落ち、stop hook の判定が丸ごと通っていた。今後はこのフラグなしで開く

#### Fixed

- `hooks/scripts/lib/regular_file.py`
  - `read_regular_text(path, errors="strict")` を足した。`read_regular_bytes` を UTF-8 で decode し、改行を `Path.read_text()` と同じく `\n` にそろえる
  - `lstat_or_none(path)` を足した。ENOENT・ENOTDIR だけを「無い」とし、権限エラーなどは送出する
  - `read_regular_bytes` は、指す先の無い symlink で `OSError` を送出する（None はパスに何も無いときだけ）。`os.O_NONBLOCK` が無ければ付けずに開く
- `hooks/scripts/lib/done_guard.py`: Route In Progress の検査は state.md を `read_regular_text` で読む。無ければ検査しない、通常のファイルでなければ、パスを示して done を止める
- `hooks/scripts/lib/done_block_message.py`: tasklist.md・state.md を通常のファイルとして読めないときの回復手順を足した
- `hooks/scripts/lib/state_io.py`: `parse_state` は `read_regular_text` で読み、無ければ `FileNotFoundError` を送出する
- `hooks/scripts/gdd_stop_hook.py`
  - post-merge の marker と `.claude/gdd-dev.local.md` の存在の確認を `os.path.lexists` にした
  - `_steering_candidate` を足した（選び方の本体は `hooks/scripts/lib/steering_candidate.py`）。bind 済み steering、bind が無ければ最新の steering の対象ファイルと、それが使えるかを返す。最新の steering のディレクトリが使えない・stat できないか、在るのに使えないファイルがあれば、古い steering へ飛ばさない（「無い」とするのは ENOENT・ENOTDIR だけ）
  - `_bound_steering_file` は `_steering_candidate` で使えるファイルだけを返す
- `hooks/scripts/lib/pr_review_followup_polling.py`: ポーリング上限の判定（`escalate_polling_reason`）を stop hook から移し、external-review-waiting のときだけ `_steering_candidate` で state.md を選んで読む。使えない・一覧できない・読めなければ `blocked` にして記録する。`find_active_steering_state` を消した
- `references/state-field-tiers.md`: `PR Review Follow-up Attempts` の行に、state.md を読めないときも `blocked` にすることを書いた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/regular_file.py`
- `plugins/gate-driven-development/hooks/scripts/lib/done_guard.py`
- `plugins/gate-driven-development/hooks/scripts/lib/done_block_message.py`
- `plugins/gate-driven-development/hooks/scripts/lib/state_io.py`
- `plugins/gate-driven-development/hooks/scripts/lib/pr_review_followup_polling.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/lib/steering_candidate.py`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/tests/_stop_hook_test_base.py`
- `plugins/gate-driven-development/tests/test_regular_file.py`
- `plugins/gate-driven-development/tests/test_next_plan_check_fence.py`
- `plugins/gate-driven-development/tests/test_steering_state_selection.py`
- `plugins/gate-driven-development/tests/test_stop_hook_non_regular_files.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_regular_file.py` に `read_regular_text` のテスト（改行のそろえ方・無いパス・ディレクトリ・不正な UTF-8）と、指す先の無い symlink・`os.O_NONBLOCK` の無い環境のテストを足した
- `tests/test_next_plan_check_fence.py` に、指す先の無い symlink の requirements.md を未完と読むテストを足した
- `tests/test_stop_hook_non_regular_files.py` に、state.md・`gdd-dev.local.md` が FIFO・ディレクトリ・symlink のループ・指す先の無い symlink のときと、marker が symlink のループ・指す先の無い symlink のときに、hook を起動して判定を見るテストを足した。tasklist.md にも指す先の無い symlink を足した
- `tests/test_steering_state_selection.py` を足した。bind が無いときに、最新の state.md が通常のファイルでない・最新の steering のディレクトリが使えないと古い steering へ飛ばないこと、ポーリング上限の判定と記録を見る（FIFO を含むので別プロセスで timeout 付き）
- `tests/test_steering_state_selection.py` に、最新の task dir・`.steering`・bind 済みの task dir に x が無いときに古い steering へ飛ばず、ポーリング上限が `blocked` になるテストを足した（root では skip）
- `tests/test_stop_hook_non_regular_files.py` に、`.steering` を一覧できないときに human-check-waiting は pause し、external-review-waiting は `blocked` にして記録するテストを足した
- `tests/_stop_hook_test_base.py` の `_run_hook` に `timeout` 引数を足した
