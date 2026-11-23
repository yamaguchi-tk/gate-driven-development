---
type: patch
---

#### Summary

- 指摘の行き先の検査の誤りを直した。根拠の path が履歴にも無く、同じ basename の file も無い high・実害クラスの指摘を、検証役なしで `advisory:unverified_file` に下げられるようにした（`20261022-review-finding-dispositions` の変更で high・実害クラスの降格に検証役の `refuted` を求めたが、根拠の file が無いと検証役は判定できず、差し戻しになっていた）。同じ tip を 2 回レビューすると `findings` 行が直せない invalid になっていた。dialectic review の Final synthesizer の model の記述も、host ごとの表とずれていた

#### Fixed

- `skills/gdd-implementation-gating/SKILL.md` Step 1c・`scripts/check-finding-dispositions.py`: 根拠の path が merge-base にも tip にも無い high・実害クラスは、根拠に `absent@<HEAD の sha>` と書いて、検証役なしで `advisory:unverified_file` に下げられる。CLI（新しい `--base <default-branch>`）がその sha の時点の git で path を分類し、tip・未 commit の file にある、diff か branch の途中の commit が消した・改名した、同じ basename の file がある（NFC・NFD と大文字小文字の違いは同じ名前とみなす）、分類できない（`path:行:桁` や、path に文字〔Unicode の文字・数字・`_`〕と `./@+~-` 以外の文字がある形を含む）、のどれかなら invalid にする。それ以外の high・実害クラスは、検証役が `refuted` と判定したときだけ下げる
- `scripts/check-gate-ledger.sh` の `findings` 行: 同じ sha の `IR` 節が 2 つあれば、ファイルの順で最後の節と突き合わせる。前の節の high・実害クラスに、最後の節の `re-reported:<id>` が無ければ invalid
- `references/dialectic-review.md`: Final synthesizer は Claude Code では `opus` + `effort=high`、Cursor・Codex では Primary 系に戻した（`skills/gdd-model-routing/SKILL.md` の表を正本にした）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/finding_dispositions.py`
- `plugins/gate-driven-development/references/finding-dispositions.md`
- `plugins/gate-driven-development/scripts/check-finding-dispositions.py`
- `plugins/gate-driven-development/references/dialectic-review.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`

#### User Action Required

- impl-gating Step 8 の検査は `check-finding-dispositions.py --steering <Steering Dir> --base <default-branch>` で回す。`--base` が無くても今までの行は検査できるが、根拠が `absent@<sha>` の行は invalid になる

#### Validation / Eval Impact

- `tests/test_finding_dispositions.py`（同じ sha の `IR` 節が 2 つあるときの `findings` 行を、`check-gate-ledger.sh` の入口から通す。`absent@<sha>` の行を、一時 repo で CLI の入口から分類ごと〔path の形、非 ASCII・NFD・大文字小文字・staged の basename を含む〕に通す）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
