---
type: patch
---

#### Summary

相談役を Opus 2 本にした変更、簡素化パスの Sonnet 化、agent が advisor ツールを呼ばない変更、README の費用の節で残っていた記述のずれを直した。簡素化パスを opus 必須の工程で起動したときの警告を、実装の worker 向けの案内から簡素化パス向けの案内に替えた。

#### Changed

- dispatch model gate の警告（`hooks/scripts/run-agent-dispatch-model-gate-hook.sh`）：簡素化パスを model を省略して opus 必須の工程で起動したとき、worker を起動し直す案内ではなく、Next Action を確かめる案内を出す。止める・通すの判定は変えていない
- `README.md` § 費用の目安：Opus の固定が Claude Code の話であること、表を測った構成と本数、割合の数え方、Pro・Team の既定のモデルの版の扱い、枠が尽きたときの続け方、Opus を使えないときの GDD の扱い、Fable を起動する条件、advisor の資料のリンクを書き直した。§ モデル選択の「一覧を写さない」を、費用の節の要約と合わせた
- 実装の worker 3 つ・`gdd-code-simplifier`・`gdd-qa-runner` の advisor の行：根拠の資料のリンクを足し、「費用だけを足す」を根拠に合わせて弱めた
- `references/fixed-models.md`：Opus と Fable を並べていた頃の文を過去形にし、簡素化パスの段落の版数と保証の言い方を直した
- `references/human-check-template.md` 項目 7：済ませた相談を 2 本のどちらに数えるかを書いた
- `docs/VERSIONING.md` のよくある判断の迷い：既存の agent の model・effort だけを変えたときは PATCH にする、という問いを足した

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-agent-dispatch-model-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`（コメントだけ）
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/agents/gdd-implementation-worker.md`
- `plugins/gate-driven-development/agents/gdd-implementation-worker-heavy.md`
- `plugins/gate-driven-development/agents/gdd-remediation-worker.md`
- `plugins/gate-driven-development/agents/gdd-code-simplifier.md`
- `plugins/gate-driven-development/agents/gdd-qa-runner.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/docs/VERSIONING.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_implementation_worker_agents.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
