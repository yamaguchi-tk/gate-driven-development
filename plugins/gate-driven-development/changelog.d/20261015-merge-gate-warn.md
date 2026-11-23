---
type: breaking
---

#### Summary

- merge gate（`gh pr merge` の PreToolUse hook）が、merge を止めなくなった。不足を見つけたときは merge を通し、reason code と不足を「実行後の通知」として返す。通知が agent に届くのは merge の後である

#### Breaking Contract Changes

- merge gate は `{"decision": "block"}` を返さない。代わりに `systemMessage` と `hookSpecificOutput.additionalContext` に同じ通知を入れて返す。通知は「実行後の通知: merge gate は止めずに通した。」で始まる
- 承認の無い merge、証跡の足りない merge、bot レビューを待たない merge（`review-wait-not-elapsed`）を、plugin は止めない。承認は導入先の運用（人がマージを決める、branch protection、auto mode classifier など）で担保する

#### Changed

- 通知を出した実行（merge と断定できなかったコマンドを含む）は、1 回ごとに state dir の `merge-gate-suppressed.log` に `event: would-block:<code>[,<code>…]` の行を残す（不足条件の全 code。repo は絶対パスの sha1 の先頭 8 桁）
- `references/post-merge-qa.md` と `skills/gdd-pr-review-followup/SKILL.md`: bot レビューの待ちと証跡は merge の前に確かめ、merge の後に通知が出たら、承認や証跡を後から書き足さずにユーザーに報告する
- `references/reviewer-common.md` § 常時 High の適用範囲: merge gate は block しない hook として (1) に入る

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- merge gate で承認の無い merge を止めていたなら、branch protection などの仕組みで代える
- 止めていたはずの merge を数えるときは、`merge-gate-suppressed.log` の `would-block:` の行を、transcript の実行と突き合わせて数える（merge でないコマンドの行もある）

#### Validation / Eval Impact

- 追加: `tests/test_merge_gate_warn_only.py`（全 reason code で `decision` を出さず通知を出す、would-block の記録、集約の経路で全 code を 1 行に記録する、state dir に書けないときも通知を出す）
- merge gate のテストの block の assert を、通知の assert に置き換えた
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
