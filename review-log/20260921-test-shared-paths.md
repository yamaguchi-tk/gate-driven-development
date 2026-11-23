---
lane: L1
pr: 旧#168
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 500b23ef3058eba4b997833394632dc9f4f5e2a9 | 0 | 1 | 0 | 2026-09-21T23:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | unittest-module-launch | fixed | `_paths` の import は `tests/` が sys.path に無いと解決しない。docstring と `docs/DISTRIBUTION_READINESS.md` に書かれた `python3 -m unittest tests.<module>` 起動（`test_hitl_lint_gate_unit.py`・`test_hitl_lint_gate_warn_wiring.py`・`test_lint_hitl_required_fields.py`・`test_e2e_replay_fixtures.py`）が `ModuleNotFoundError` になる（再現済み）。pytest・`unittest discover -s tests` は影響なし。実測では main で `tests.<module>` として import できた 121 本のうち 115 本が退行していた。近道の巡の ① の blocking でない medium だが、テストだけで直せて巡を無効にしないため、ユーザーの指示でこの PR で直した。`tests/__init__.py` で `tests/` を sys.path に入れ（ed45809e）、全モジュールの import を固定するテストを足した（616b752b） |
| F2 | 独立-1 | low | no | self-inflicted | unused-import-left | fixed | 置き換え後に使われない `pathlib` の import が 3 ファイルに残る（文字列リテラル中の `Path` を使用とみなしたため）。ユーザーの指示でこの PR で直した（59495d2f） |
| A1 | 独立-1 | advisory | no | inherited | root-built-inline | accepted | sys.path への挿入式など、式の中でルートを組み立てる箇所は集約の対象外。PR 本文の限界に書く |
| A2 | 独立-1 | advisory | no | self-inflicted | changelog-fragment-policy | fixed | 断片の `#### Changed` がテスト内部の詳細で、Affected Files の `tests/_*.py` のグロブが対象外の 2 本も含む。`#### Changed` を消し、helper を名前で列挙した（断片だけの修正） |
| A3 | 独立-1 | advisory | no | self-inflicted | evidence-granularity | accepted | 収集件数の一致とローカル実行結果に `at <sha>` が無い。PR 本文に `at <sha>` つきで書く |
