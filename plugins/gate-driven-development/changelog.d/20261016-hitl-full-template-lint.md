---
type: patch
---

#### Summary

- full の human check テンプレート（`references/human-check-template.md`）から、承認サマリと中身が同じ独立した `### まず見るところ` 節を外した。その節にだけあった「迷ったら確認する欄」は、30秒判断の `どこまで自走するのか` の括弧に添える形にした（§ 具体例と同じ形）。テンプレートが両方を置くよう求めなくなったので、テンプレートどおりに書いた HITL は `lint-hitl-decision-quality.py` の重複した要約の検査に落ちない（両方を置いた HITL は今までどおり落ちる。この検査の判定は変えていない）
- full テンプレートの欄名「OK でも許可されないこと」を、lint（`lint-hitl-decision-quality.py`・`lint-hitl-display-integrity.py`）と compact が使う「OKでも許可されないこと」にそろえた
- `lint-hitl-decision-quality.py` の承認ポイントの検査の起点を、最初の `### 判断ポイント` / `### 承認ポイント` 見出しから、`承認ポイント数:` の宣言を節の中に持つ見出しに替えた。full の並び（宣言の無い判断ポイントが先で、宣言は後ろの承認ポイント）が「宣言がありません」で落ちなくなる

#### Affected Files

- `references/human-check-template.md`（出力テンプレートの 30秒判断・承認サマリ・まず見るところ、必須ルール 13、§ 承認ポイントの固定フィールド受理文法、§ 具体例の承認サマリ）
- `scripts/lint-hitl-decision-quality.py`

#### User Action Required

なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_hitl_decision_scope_contract.py plugins/gate-driven-development/tests/test_hitl_lint_marker_sync_contract.py -q`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
