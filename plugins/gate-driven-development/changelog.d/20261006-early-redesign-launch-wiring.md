---
type: patch
---

#### Summary

実装の差し戻しの早期の方式判断で、判断役を起動できないときの扱いと、事前回答・記録の書き方の食い違いを直した。

- 判断役を「起動できない」ときを閉じて書いた。Claude Code で代わりの経路を試した後も Agent tool がエラーを返した、Codex・Cursor で別コンテキストの起動がエラーを返した、Codex で委譲の許可が無く起動しない、の 3 つだけである。結果が返ったら、空でも欄で読んで route に写す
- 早期の方式判断の判断役を起動できないときは、自律モードでも `references/autonomy.md` の止まる場面に当たらず、通常どおり判定する。autonomy.md の参照元と止まる場面にも書いた
- Downstream Human Recheck Handoff で、`worklog.md` に対象を含む `事前回答:` 行があれば、出力の前に § 事前回答 2・3 で扱い、無く `GDD Autonomy: internal` があれば autonomy.md で判定する。この判定は main が行い、Handoff を出力する subagent は判定も記録の行も書かずに止まる
- § 事前回答 2 の「確かめられないとき」の行に、Handoff で着いたときの形（`human-recheck`・`Current Task` の id）を足した
- `早期方式判断:` の行の `写した route:` と、`gdd-systematic-debugging` が採った route（検査の後で違いうる）の違いを書いた

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
