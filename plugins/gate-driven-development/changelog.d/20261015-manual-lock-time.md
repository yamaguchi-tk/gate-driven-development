---
type: patch
---

#### Summary

`commands/gdd-dev.md` の手動の手順（`setup-gdd-loop.sh` が走らなかったとき）で、別の session の state で止まるときに持ち主の時刻を添える手順を足した。手順 2 は時刻の取り方として `docs/TROUBLESHOOTING.md` のロックの節を指し、手順 4 で止まるときも時刻を添える。TROUBLESHOOTING には、transcript の末尾から top-level の `timestamp` の最新の値だけを手で取り出す手順を書いた。

#### Affected Files

- `plugins/gate-driven-development/commands/gdd-dev.md`（手動の手順 2・4）
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`（手で時刻を取る手順）
- `plugins/gate-driven-development/docs/SECURITY.md`（手動の手順で transcript の末尾を読むこと）
- `plugins/gate-driven-development/changelog.d/20261015-lock-last-active-followup.md`（手順 2 が指さないという記述を外す）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（起動時の文書の予算）
