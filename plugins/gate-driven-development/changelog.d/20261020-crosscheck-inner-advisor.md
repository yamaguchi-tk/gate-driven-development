---
type: patch
---

#### Summary

- `gdd-request-code-crosscheck` に、advisor ツールを呼ばない規定を足した。着手前の突き合わせの中で、advisor（利用者の設定のモデル）を呼ばない指示になる。散文の指示なので、効いたかはマージ後に数えて確かめる
- 2026-10-12〜20 の実行では、crosscheck は 16 本中 16 本で、結論の直前に advisor を 1 回呼んでいた（推定 1 回 約 $1.6）。同じ使い方の reviewer は 2026-10-20 に止めている
- 判定の 4 つの値・出力の節・model・effort は変えていない
- 実装 worker 3 本・`gdd-code-simplifier`・`gdd-qa-runner` は変えていない

#### Changed

- `agents/gdd-request-code-crosscheck.md`（「守ること」の read-only の行の直後に 1 行）

#### Affected Files

- `agents/gdd-request-code-crosscheck.md`

#### User Action Required

- 動いているセッションは、開き直すまで古い定義で動く

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
