---
type: patch
---

#### Summary

merge gate と pre-push gate が、steering の列挙から落ちる steering を「無い」として検査せずに通していた経路を閉じた。

- pre-push gate: 一覧できない task dir・`.steering` など、読めない steering があると、その steering が候補に入らず、検査せずに push を通していた（作業中の steering が 1 件も無いときと、別の trivial の steering が 1 件あるときの両方）。steering の解決の結果によらず、新しい reason code `steering-unreadable` で止める
- 両 gate: `.steering` 自体、その下の task dir、task dir の中の state.md が symlink のとき、steering の列挙（symlink を辿らない）からは落ちていた。merge gate では「読めない」の判定（symlink を辿る）でも読めるとされ、pre-push gate にはこの判定自体が無く、どちらも検査せずに通っていた。symlink は読めない側に数える。merge gate は `state-unreadable` で止める
- 両 gate: state.md が FIFO（symlink の先が FIFO の形を含む）のとき、binding の resolver が開いて待ち続け、hook の timeout で検査せずに通っていた。resolver は通常ファイルでない state.md を開かない。pre-push gate は判定を resolver より前に行う
- 「読めない」の判定を merge gate の中から lib に移し、両 gate で同じものを使う

task dir でないファイル（README など）、state.md の無い task dir は、今までどおり飛ばす。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/self-review-evidence.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/scripts/gdd_task_binding.py`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`
- `plugins/gate-driven-development/tests/test_steering_enumeration_unreadable.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`
- `plugins/gate-driven-development/tests/test_pre_push_tip_sha_resolution_contract.py`
- `plugins/gate-driven-development/tests/_pre_push_gate_support.py`

#### User Action Required

- `.steering` 自体、またはその下に symlink を置いている場合は、実体のディレクトリ・ファイルに置き換える（GDD 自体は symlink を作らない）

#### Validation / Eval Impact

- `tests/test_steering_enumeration_unreadable.py` を足した（symlink の `.steering`・task dir・state.md、一覧できない `.steering`・task dir、FIFO の state.md を両 gate で、通す側の形、名前の文字）
- `tests/test_pre_push_tip_sha_resolution_contract.py` の、読めない state.md が複数の steering に混ざる形の期待する reason code を `steering-multiple` から `steering-unreadable` に変えた（block であることの検査は同じ）
- `tests/test_pre_push_gate_contract.py` の reason code の照合に `steering-unreadable` を足した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
