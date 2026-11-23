---
type: patch
---

#### Summary

README に、前提（bash・git・Python 3・GitHub CLI と、確かめている OS、Python・git・GitHub CLI の版と版で変わること）、インストールすると GDD を使っていないセッションで何が変わるかの節を足した。古くなっていた Reviewer Agents の数と、モデル選択の一覧の写しを、正本への案内に置き換えた。plugin の挙動は変わらない。

#### Changed

- `README.md` § 導入に「前提」を足した
- `README.md` に「インストールすると変わること」を足した
- `README.md` § モデル選択を `references/fixed-models.md` への案内にした
- `README.md` § Reviewer Agents の見出しから数を外し、ほかの agent の場所を書いた

#### Affected Files

- `plugins/gate-driven-development/README.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
