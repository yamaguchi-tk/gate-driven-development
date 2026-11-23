---
type: minor
---

#### Summary

- human check で承認した文（確定文面）を、design.md の `## 確定文面` 節に固定し、マージする文書にそのまま入ったことを照合する標準の道具を足した。これまではタスクごとに取り出し・digest・照合の script を書いていて、最初の照合は「含まれるか」で比べる弱い形になりやすかった（確定文面の隣に文を足しても通る）。標準の照合は、base の版に宣言した置き換えを当てた期待値と、実物をバイト単位で比べる（既存のファイルと全体を承認した新しいファイルはファイル全体、一部だけを承認した新しいファイルは目印の間）

#### Added

- `references/confirmed-text.md`: 確定文面の書き方（節名・block の id `D-n#i`・置換の鍵・照合しない block の `noverify`・節の中に `##` があるときの終わりの見出しの宣言）、digest の定義、置き方の宣言（`.steering/<task>/confirmed-text.json`）、照合、承認の後に開き直すときの手順（digest の取り直し・worklog.md への記録・照合のやり直し）の正本
- `scripts/confirmed-text.py`: `digest`（節の sha256・行数・節を終わらせた見出し）、`extract`（block の中身を置換つきで出す）、`verify`（digest の突き合わせ、期待値とのバイト単位の比較、manifest が参照していない block の検出。終了コード 0 = 一致・1 = 不一致・2 = 入力の誤り）

#### Changed

- `references/human-check-template.md`: § 確定文面の再確認 を足し、正本の `references/confirmed-text.md` を指した
- `references/source-of-truth-map.md`: 確定文面の行を足した
- `tests/checks/skill-body-budget.sh`: 必須ファイルに `references/confirmed-text.md` を足し、references の行予算を、足した行（新しい reference と、human-check-template.md・source-of-truth-map.md に足した行）の分だけ上げた

#### Affected Files

- `references/confirmed-text.md`（新規）, `scripts/confirmed-text.py`（新規）, `tests/test_confirmed_text.py`（新規）
- `references/human-check-template.md`, `references/source-of-truth-map.md`, `tests/checks/skill-body-budget.sh`

#### User Action Required

- なし。文書の文そのものを human check で承認させるタスクで使う

#### Validation / Eval Impact

- 追加 test: `tests/test_confirmed_text.py`（digest の範囲、block の取り出し、照合の一致、変異注入〔隣に文を足す・1 文字変える・block を消す・CRLF・design.md の承認後の変更・manifest と実物の両方から block を落とす〕、フェンスの規則、入力の誤りで止まること）
- `bash tests/validate-plugin.sh`
