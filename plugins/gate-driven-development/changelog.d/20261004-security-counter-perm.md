---
type: patch
---

#### Summary

- `docs/SECURITY.md` § 4 の state dir の権限の記述を実装に合わせた。deny の counter と state dir 自体は chmod せず umask のまま作ること、counter が書き込み先の steering ファイルのパスを平文で持つことを書いた

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
