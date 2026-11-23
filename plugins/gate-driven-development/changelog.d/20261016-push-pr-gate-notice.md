---
type: breaking
---

#### Summary

- pre-push gate（`git push`）と pre-PR gate（`gh pr create`）が、push・PR 作成を止めなくなった。不足を見つけたときは通し、不足を「実行後の通知」として返す。通知が agent に届くのは push・PR 作成の後である

#### Breaking Contract Changes

- 2 つの gate は `{"decision": "block"}` を返さない。代わりに `systemMessage` と `hookSpecificOutput.additionalContext` に同じ通知を入れて返す。通知は「実行後の通知: pre-push gate は止めずに通した。」（pre-PR gate は「実行後の通知: pre-PR gate は止めずに通した。」）で始まる
- 証跡の足りない push・PR 作成、completion-check を通していない PR 作成、機密候補を含む PR 本文、raw task steering を含む diff を、plugin は止めない。機密候補の通知は、ただちにユーザーに報告するよう求める
- `GDD_SKIP_PRE_PUSH_GATE=1` は、通知と記録を省くものになった

#### Changed

- pre-PR gate は、見つけた不足をまとめて 1 本の通知にする。PR 本文の機密候補は、steering を解決できないときや completion-check の前でも通知に載る（pre-push gate は今までどおり最初の不足 1 つ）
- 通知を出した実行は、1 回ごとに state dir の `pre-push-gate-suppressed.log`・`pre-pr-gate-suppressed.log` に `event: would-block:<code>` の行を残す（pre-PR gate で不足が複数あれば、code をカンマでつないだ 1 行。repo は絶対パスの sha1 の先頭 8 桁）
- `references/reviewer-common.md` § 常時 High の適用範囲: 2 つの gate は block しない hook として (1) に入る

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gate-notice.sh`（新規）
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/references/independent-review.md`・`post-completion-pr-flow.md`・`self-review-lanes.md`・`post-merge-qa.md`、`skills/gdd-pr-review/SKILL.md`、`scripts/check-gate-ledger.sh`（gate が止めると書いていた記述）

#### User Action Required

- 2 つの gate で証跡の無い push・PR 作成を止めていたなら、branch protection や CI の検査で代える
- 止めていたはずの実行を数えるときは、2 つのログの `would-block:` の行を、transcript の実行と突き合わせて数える

#### Validation / Eval Impact

- 追加: `tests/test_push_pr_gate_notice.py`（`decision` を出さず通知を出す、code を引数で渡す、would-block の記録、記録先に書けないときも通知を出す、判定できない push も通知する、機密候補の通知が報告を求める、機密候補を steering の解決より前に検査する、不足を 1 本の通知にまとめる、後段が落ちても前段の不足を出す）
- 2 つの gate のテストの block の assert を、通知の assert に置き換えた
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
