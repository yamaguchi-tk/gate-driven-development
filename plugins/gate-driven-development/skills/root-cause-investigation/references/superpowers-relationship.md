# `root-cause-investigation` vs `superpowers:systematic-debugging`

両方とも単体で機能する汎用 methodology（4 phases / Iron Law / architecture check の構造は同じ）。`root-cause-investigation` は call stack 深掘り（`./references/call-stack-tracing.md`）・多層 validation（`./references/defense-in-depth.md`）・テスト汚染源特定（`scripts/find-polluter.sh`）を自前で持つ依存ゼロの skill なので、GDD workflow の内外を問わず基本的にこちらを使う。

superpowers plugin をインストール済みで、`superpowers:systematic-debugging` 側にしかない補助 reference を明示的に参照したい場合のみ、そちらを使ってよい。

**両方を同じ debug セッションで呼ばない**（重複して時間が溶ける）。最初に 1 つ選んでそれで進める。
