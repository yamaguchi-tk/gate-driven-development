---
type: patch
---

#### Summary

`collect-gdd-telemetry.py --include-worktrees` が、ディレクトリを消した worktree（`git worktree prune` の前の行）で `root not found` を出して終了 1 になっていた。その worktree は警告を出して飛ばし、集計を続けるようにした。`--root` で明示した場所が無いときは、今までどおり終了 1 にする。

#### Changed

- `scripts/collect-gdd-telemetry.py`：`git worktree list` から足す worktree のうち、ディレクトリが無いものを `WARNING: skipped missing worktree: <path>` を stderr に出して飛ばす

#### Affected Files

- `plugins/gate-driven-development/scripts/collect-gdd-telemetry.py`
- `plugins/gate-driven-development/tests/test_telemetry_missing_worktree.py`

#### User Action Required

- なし。`gdd-metrics` の推奨経路（`--include-worktrees`）が、消えた worktree があっても使えるようになる

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_telemetry_missing_worktree.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
