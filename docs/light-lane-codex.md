# 軽いレーンの Codex の使い方

root `CLAUDE.md` の手順 5 の、起動の仕方と結果の扱いである。使う条件は手順 5 に書いてある。

- 入口は codex plugin（`codex@openai-codex`）の `adversarial-review`。観点の文字列を渡せるのはこちらだけで、`/codex:review` は受け付けない
- このコマンドはモデルからは起動できない（`disable-model-invocation`）。セッションからは、同じ実体を Bash で呼ぶ：`node ~/.claude/plugins/cache/openai-codex/codex/<版>/scripts/codex-companion.mjs adversarial-review "--wait --base origin/main --scope branch <観点>"`。先に同じスクリプトの `setup --json` で使えるかを確かめる
- 観点は配線：新しく作る部品の書く側・読む側・到達経路を実コードで追えるか、同じ入力を読む別の実装と受理する集合が一致するか
- 結果は `codex-N` の巡として、手順 6 と同じ形式で review-log に追記する。Codex の指摘の severity は、`plugins/gate-driven-development/skills/pr-review-followup/SKILL.md` の手順 2 Classify のとおりに分ける（`reviewer-common.md` § 常時 High の 4 型と適用範囲、範囲外の上限、4 型に当たるかを判定できないときと、確かめた後に戻すときの扱い。ここには書き写さない。PR を作る前なら、確かめた根拠は PR コメントの代わりに review-log の `## 指摘` の要約に書く）。Codex の指摘には `差分との関係` の欄が無いので、直すのは high と blocking だけにし、medium 以下は手順 6 の ② と同じく次の PR に回す（`next-pr`）。直して commit を積んだら、最後の独立レビューの後なら手順 6 の「最後の独立レビューの後に commit を積んだとき」に従う。それより前なら、次の巡（1 巡目より前なら全差分巡）へ進む通常の流れに戻る（再設計で呼んだときは、直す分を再設計の commit に含める）
