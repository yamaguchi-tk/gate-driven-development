---
type: patch
---

#### Summary

- 回帰テストの既定実行を並列にし、並列時の下限を作っていた最長テストを分割した（X-36）。`pytest.ini` を新設し、`-n` を付けないコマンドでも xdist が既定で起動するようにした（直近 72 時間の実測で、全体回帰の起動の約 83% が `-n` なしで走っていた。コマンドの書き方に依存せず既定を変えることで解消する）。あわせて `test_hook_block_reason_recovery_contract.py` の 1 メソッドを、`reason_codes_by_hook()`（`hooks/scripts/*.sh` の glob 発見）を駆動集合とした hook ごとの生成メソッドへ分けた。検査対象へ hook を追加する操作は provider 登録 1 つのまま変わらない

#### Added

- `pytest.ini`: `[pytest]` セクションに `addopts = -n auto --dist worksteal`

#### Changed

- `tests/test_hook_block_reason_recovery_contract.py`: モノリシックな 1 メソッドを、factory 関数 + `setattr` による per-hook 生成メソッド（`test_block_reason_recovery__<slug>`）へ置換した。新設した `test_generation_is_driven_by_glob_discovery_only` が、生成が glob 発見だけで駆動されていること（hook 名 literal を持たないこと・集合一致）を検証する。生成メソッド本体は `_gdd_hook` 属性と実クロージャの同一性を実行時に自己検証し、late-binding 退行を検出する
- 既定の実行で `pytest-xdist` を使うようになった。1 ファイルだけを直列に実行したいときは `-n 0` を付ける（`-p no:xdist` は `unrecognized arguments: -n --dist` で失敗するため、上書きには使えない）
- `CONTRIBUTING.md` § 1 に、`pytest.ini` で既定が並列になること・直列にするときの `-n 0`・`pytest-xdist` の版の下限（3.2）を書いた

#### Affected Files

- `pytest.ini`（新規）
- `tests/test_hook_block_reason_recovery_contract.py`
- `CONTRIBUTING.md`

#### User Action Required

- `pytest-xdist` 3.2 以上を入れる（`pip install 'pytest-xdist>=3.2'` など）。`CONTRIBUTING.md` の必須チェックはもともと `-n auto` を使うので xdist 自体は前提だったが、`--dist worksteal` が 3.2 で入ったモードのため、版の下限が 3.2 に上がる
- maintainer: publish の前に、配布先の共有 repo の `.github/workflows/plugin-lint.yml` が `pytest-xdist>=3.2` を入れていることを確かめる。入っていないと、同期された `pytest.ini` の `-n auto --dist worksteal` が `unrecognized arguments` になり、`Run GDD plugin contract tests` が落ちる
- 1 ファイルだけを直列に実行したいときは `-n 0` を付ける（`-p no:xdist` は使えない）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` の全体回帰
- `python3 -m pytest plugins/gate-driven-development/tests/`（`-n` なし）が `pytest.ini` により並列で起動することを確認した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（BLOCK の追加なし）
- 追加 test: `test_generation_is_driven_by_glob_discovery_only`
