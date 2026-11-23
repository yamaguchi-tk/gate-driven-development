---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。文書の語・文だけを見るテストを消した変更の続き。`CONTRIBUTING.md` のテストの方針を、hook・script・command の契約と、コードが読む値・集合・シンボルと文書の一致を `tests/test_*.py` で固定し、文書の語・文だけを見るテスト（`tests/test_*.py`）は書かない（`tests/checks/*.sh` の文言の検査の扱いは別に決める）、に改めた。`references/prompt-contract-map.md` の state の正本の行の guard 欄に、overview 2 文書の 30 行の上限を見る `tests/checks/codebase-health-smoke.sh` を書いた。`tests/test_always_high_scope_contract.py` は、`reviewer-common.md` § 常時 High の (a) の列挙を再開用の field の集合と両方向で比べるようにした。

#### Affected Files

- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/references/prompt-contract-map.md`
- `plugins/gate-driven-development/tests/test_always_high_scope_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_always_high_scope_contract.py` の変異の確認
- `python3 -m pytest plugins/gate-driven-development/tests/test_always_high_scope_contract.py -q`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
