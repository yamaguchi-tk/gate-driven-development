---
type: minor
---

#### Summary

- PR ごとの版数上げと `CHANGELOG.md` への版の節の追記をやめ、PR は `changelog.d/` に変更断片を 1 つ足す運用に切り替えた。版数上げと CHANGELOG への集約は、リリースのときに `scripts/release.py` がまとめて行う。PR ごとに版数を上げると、1 本マージされるたびに残りの PR が 3 manifest・`CHANGELOG.md`・`docs/VERSIONING.md` で衝突し、衝突の解消のたびに回帰テストと独立レビューのやり直しが起きていたため

#### Added

- `scripts/release.py`: 断片の `type` の最大値（breaking > minor > patch。v0.x の breaking は minor を上げる）から次の版数を決め、3 manifest の `version`・`docs/VERSIONING.md` § 現状・`CHANGELOG.md` の新しい版の節をまとめて更新し、断片を削除する。既定は dry-run で、書き込むのは `--apply` のときだけ。断片が 0 件なら何もしない。不正な断片や 3 manifest の不一致があれば何も書かずに失敗する
- `changelog.d/`: PR ごとの変更断片の置き場（書式は `CHANGELOG.md` § Entry Template）

#### Changed

- `tests/checks/version-not-consumed.sh`: 「manifest の版数 > 記録した消費済み版数」の要求をやめた。ブランチが統合先との分岐点（merge-base）から版数を変えていなければ、通常の PR として、分岐後に断片（`scripts/release.py` が集める `changelog.d/` 直下のもの）を 1 つ以上足していることを要求する。統合先が先にリリースしていても、統合先の取り込みは求めない。版数を変えていれば、統合先より大きいときだけリリースのコミットとして、断片が残っていないことを要求する。統合先の版数以下なら FAIL にする。断片の書式も検査する
- `docs/VERSIONING.md`: main を取り込むたびに書き換わっていた「統合先の消費済み版数」の記録行を削除した。§ リリース手順を `scripts/release.py` を使う手順に置き換え、リリース手順の正本をここに一本化した
- `CHANGELOG.md` § Policy / § Entry Template / § Archive、`CONTRIBUTING.md`、`skills/gdd-writing-skills/SKILL.md`、`references/rationalization-root-causes.md`、`docs/DISTRIBUTION_READINESS.md`、`README.md`: PR ごとの版数上げと CHANGELOG 追記の指示を、断片を書く指示に置き換えた

#### Affected Files

- `scripts/release.py`（新規）, `changelog.d/`（新規）, `tests/checks/version-not-consumed.sh`, `tests/test_changelog_fragments.py`（新規）, `tests/checks/hooks.sh`, `tests/test_merge_approval_vocabulary_leak.py`
- `docs/VERSIONING.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `README.md`, `docs/DISTRIBUTION_READINESS.md`, `skills/gdd-writing-skills/SKILL.md`, `references/rationalization-root-causes.md`
- （リポジトリ直下）`CLAUDE.md` の L1 手順と push 前の順序、`docs/learned-patterns.md` の旧手順 3 項目への廃止の注記

#### User Action Required

- GDD plugin に PR を送る人: 3 manifest の `version`・`CHANGELOG.md` の版の節・`docs/VERSIONING.md` § 現状 には触れず、`changelog.d/<YYYYMMDD>-<slug>.md` に断片を 1 つ足す（`type` は patch / minor / breaking）。断片が無いと `tests/validate-plugin.sh` の `version-not-consumed` が FAIL する
- maintainer: リリースは `python3 scripts/release.py`（dry-run）で内容を確かめてから、`--apply` を付けて実行する（`docs/VERSIONING.md` § リリース手順）
- GDD plugin を使うだけの人: 対応は不要

#### Validation / Eval Impact

- `tests/test_changelog_fragments.py`（新規）: 版数の決め方、`scripts/release.py` の dry-run / `--apply` / 断片 0 件 / 不正な断片 / manifest の不一致、`version-not-consumed.sh` の各判定と manifest の型違い、2 本の PR の無衝突マージ
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
