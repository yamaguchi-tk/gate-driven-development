---
type: patch
---

#### Summary

Stop hook と post-merge continuation が `## Planned Follow-up Stage Lane` の未完を読む判定と、stop hook が読む状態ファイルの扱いに残っていた穴を閉じた。どれも、止めるべき停止を通すか、hook を timeout まで止めていた。

- `|` を含む項目（例: `- [ ] S-2 | x`）の次の行が `|---|` のような区切りの形だと、その項目を表のヘッダーと読んで完了としていた。今後は、Lane の中で完了と読む行を `- [x]` の項目と空行だけにする。表の行は、ヘッダーと区切りの行も含めて未完と読む。Stage が全部終わったら表ごと消す
- requirements.md・tasklist.md・post-merge の marker（`.claude/gdd-post-merge-continuation.json`）が FIFO・ディレクトリ・デバイスなど通常のファイルでないと、「無い」と取り違えて通すか（done guard の素通りを含む）、FIFO では書き手が来るまで読み込みが戻らず hook が timeout まで止まっていた。今後は、パスが無いとき（ENOENT・ENOTDIR）だけ「無い」とし、それ以外の通常のファイルでないもの・開けないもの（symlink のループを含む）は止める側に倒す。ただし post-merge の marker が symlink のループのときは、その前の存在の確認（`exists()`）が「無い」と読むので止めない
  - requirements.md: Lane を未完として扱う
  - tasklist.md: done を止める
  - post-merge の marker: merge cue のある停止を止め、marker を消すよう案内する

#### Fixed

- `hooks/scripts/lib/regular_file.py` を足した。`read_regular_bytes(path)` は、非ブロッキングで開いて通常のファイルかを確かめてから読む。無ければ None、通常のファイルでない・読めないなら `OSError` を送出する
- `hooks/scripts/lib/next_plan_check.py`
  - `_lane_has_pending` は、Lane の中の空行と `- [x]` の項目以外の行を全部未完と読む。表のヘッダーと区切りの行を完了と読む扱いをやめた
  - `requirements_lane_pending(path)` を足した。requirements.md を `read_regular_bytes` で読んで Lane を判定する。無ければ False、通常のファイルでない・読めないなら True
- `hooks/scripts/gdd_stop_hook.py`
  - done guard は tasklist.md を `read_regular_bytes` で読む。`is_file()` で先に除外する分岐（FIFO・ディレクトリ・symlink のループ〔Python 3.13 以降〕を「無い」として done を通していた）を消した
  - `### 次の計画` の検査は `requirements_lane_pending` で判定する
- `hooks/scripts/lib/post_merge_continuation.py` は、marker を `read_regular_bytes` で 1 回だけ読む。読めないときは、merge cue のある停止を止める（別の PR と明示したときは止めない）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/regular_file.py`
- `plugins/gate-driven-development/hooks/scripts/lib/next_plan_check.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/lib/post_merge_continuation.py`
- `plugins/gate-driven-development/references/requirements-template.md`
- `plugins/gate-driven-development/tests/_stop_hook_test_base.py`
- `plugins/gate-driven-development/tests/test_regular_file.py`
- `plugins/gate-driven-development/tests/test_next_plan_check_fence.py`
- `plugins/gate-driven-development/tests/test_stop_hook_e2e_block_content.py`
- `plugins/gate-driven-development/tests/test_stop_hook_non_regular_files.py`
- `plugins/gate-driven-development/tests/test_stop_hook_bind_resolution_contract.py`

#### User Action Required

- 表で書いた Lane は、Stage が全部終わったら表ごと消すか、`- [x] S-2` の形に書き換える。ヘッダーだけ残すと、done と post-merge の停止のたびに `### 次の計画` が要る（`references/requirements-template.md` にも書いた）

#### Validation / Eval Impact

- `tests/test_regular_file.py` を足した。通常のファイル・無いパス・ディレクトリ・`/dev/null`・symlink のループ・FIFO（別プロセスで timeout 付き）を見る
- `tests/test_next_plan_check_fence.py` に、ヘッダーだけの表・区切りの形の上の項目を未完と読むテストと、`requirements_lane_pending` のテスト（無いパス・ディレクトリ・権限エラー・I/O エラー・symlink のループ〔`Path.resolve` が RuntimeError を投げる版を含む〕・`/dev/null`・FIFO・読めるファイル）を足した
- `tests/test_stop_hook_non_regular_files.py` を足した。tasklist.md・requirements.md・marker が FIFO などのときに、hook を実際に起動して止める側に倒れることを見る
- `tests/test_stop_hook_e2e_block_content.py` に、requirements.md が読めない（自分を指す symlink）ときに done と post-merge の停止を止め、marker を残すテストを足した
- `tests/_stop_hook_test_base.py` の `_run_hook` に 60 秒の timeout を付けた（hook が止まったとき、テストが戻らずに CI が止まるのを防ぐ）
