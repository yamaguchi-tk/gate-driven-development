---
type: patch
---

#### Summary

- `commands/gdd-dev.md` の human check の STEP 2 から、旧#585 で足した括弧（委任先の判断で承認するときは、人間に戻す条件を足すだけにする）を消した。この括弧で standard の実行時プロファイルの推定 token が 45489 から 45513 になって上限の 45497 を超え、`validate-plugin.sh` が main で失敗していた。足すだけの規定は `references/human-check-template.md` § 事前回答 2 にあり、委任先が承認する経路はそこから STEP 2 を呼ぶので、挙動は変わらない

#### Fixed

- `commands/gdd-dev.md`（STEP 2 の `Approved Direction` の記録の行）

#### Affected Files

- `commands/gdd-dev.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
