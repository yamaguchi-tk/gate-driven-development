---
type: patch
---

#### Summary

- Cursor の Dialectic Counter も、版付きの名前（`Opus 5.5`）をやめて「Cursor のモデル一覧にある最新の Opus」を選ぶことにした。これで契約 md から版付きの Claude の名前がなくなり、新しい Claude のモデルが出ても直す文書は無い

#### Changed

- `references/fixed-models.md`・`references/cursor.md` の `dialectic_counter` 行を `Opus 5.5` から `Opus`（一覧の最新）にした。版付きの 2 行を指していた参照（`references/cursor.md`・`references/cursor-guide.md`・`references/dialectic-review.md`・`skills/gdd-model-routing/SKILL.md`）を外した
- `references/fixed-models.md` § モデル名の書き方を 3 点に縮めた。テストの走査範囲や落ちる条件の説明は、契約テストの docstring だけに書く
- 契約テスト `test_model_names_without_version_contract.py` を「契約 md に版付きの Claude の名前が 1 つも無い」の 1 本と、正規表現の自己テストに縮めた。例外の行の一覧・表の列の検査・参照の検査・repo root の走査はなくした
- `references/` の行予算（11998 行）を、main が 4 行超えていた分も含めて上限内に戻した

#### Affected Files

- `references/fixed-models.md`・`references/cursor.md`・`references/cursor-guide.md`・`references/dialectic-review.md`
- `skills/gdd-model-routing/SKILL.md`
- `tests/test_model_names_without_version_contract.py`・`tests/checks/hooks.sh`

#### User Action Required

- Cursor で Dialectic Counter を使う場合は、Cursor のモデル一覧にある最新の Opus を選ぶ

#### Validation / Eval Impact

- 関係するテスト: `test_model_names_without_version_contract.py`・`test_x64_fable_remnant_cleanup_contract.py` ほか、変更したファイル名を参照するテスト
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
