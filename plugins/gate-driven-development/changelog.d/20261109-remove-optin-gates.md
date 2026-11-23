---
type: patch
---

#### Summary

- `validate-plugin.sh` の検査から `superpowers-benchmark-gate` と `skill-red-green-gate` を外した。どちらも環境変数を立てたときだけ動く検査で、環境変数を立てる箇所が無く、CI でも動いていなかった
- `SUPERPOWERS_BENCHMARK_REQUIRED`・`SUPERPOWERS_BENCHMARK_EVIDENCE`・`SKILL_RED_GREEN_REQUIRED`・`SKILL_RED_GREEN_EVIDENCE` は読まれなくなる。`Superpowers Benchmark Summary` と `Skill RED-GREEN Evidence` を残す規則は変えない

#### Affected Files

- `tests/checks/superpowers-benchmark-gate.sh`・`tests/checks/skill-red-green-gate.sh`（削除）
- `tests/checks/manifest.tsv`
- `CONTRIBUTING.md`・`docs/VERSIONING.md`
- `references/post-completion-pr-flow.md`
- `skills/gdd-pr-review/SKILL.md`・`skills/gdd-writing-skills/SKILL.md`

#### User Action Required

- これらの環境変数を手元で立てていても、`validate-plugin.sh` は読まない。比較資料は、PR や release note に書く

#### Validation / Eval Impact

- `validate-plugin.sh` の検査が 2 本減る。`tests/test_validate_plugin_check_inventory.py` の一覧を合わせた
