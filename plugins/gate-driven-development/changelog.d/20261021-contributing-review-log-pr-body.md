---
type: patch
---

#### Summary

- 利用者から見える変更なし。この repo の開発の手順の文言だけを直した
- `CONTRIBUTING.md` 1d と `CHANGELOG.md` § Policy が、受け入れた限界を「`review-log/` と PR 本文に残す」と書いていた。root `CLAUDE.md` 手順 7（受け入れた medium・low と advisory は `review-log/` だけに残し、PR 本文の限界にはマージの後も残る限界とまだ決まっていないことだけを書く）に合わせた。`CONTRIBUTING.md` 1d は置き場所だけを書き、PR 本文に書く限界は正本の `CHANGELOG.md` § Policy から手順 7 を指す

#### Changed

- `CONTRIBUTING.md` 1d（受け入れた指摘の置き場所の文）
- `CHANGELOG.md` § Policy（断片に書かないものの行の括弧）

#### Affected Files

- `CONTRIBUTING.md`
- `CHANGELOG.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `python3 scripts/light-lane-related-tests.py --run . origin/main`
