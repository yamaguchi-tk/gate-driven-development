---
lane: L1+
pr: 535
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | - | 0 | 0 | 0 | 2026-10-16 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d68f7d63 | 0 | 4 | 1 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e2dc75fe | 0 | 2 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | product | fixed | Opus と Fable はどちらも案 A（2 つの gate の 34 か所をすべて通知にし、機密候補の検査も通知にする）を推す。通知は共有の lib にし、code は本文から切り出さず引数で渡す。割れたのは merge gate も lib に移すかで、別のファイル群への拡大なので次の PR に回した。ユーザーへの確認は返事を待たずに本文に書き、推奨の案で進めた。ユーザーは 2 点とも推奨の案（機密候補も通知にする・merge gate の移行は次の PR）を選んだ。commit: なし（方針） |
| F1 | 独立-1 | medium | yes | self-inflicted | security-boundary | fixed | pre-PR gate は最初の不足で exit するので、completion-check 前や steering を解決できないときに機密候補の検査（と「ただちにユーザーに報告」の通知）に届かない。PR 本文の検査を steering の解決より前に移し、不足を集めて終了時に出す形にした。commit: b7c679a8 |
| F2 | 独立-1 | medium | no | self-inflicted | product | fixed | pre-PR gate は PR 1 本で 1 回しか走らないのに、通知と記録が最初の不足 1 つだけ。不足を集めて 1 本の通知と 1 行の記録（code はカンマでつなぐ。merge gate と同じ）にし、出すのは EXIT の trap にした。commit: b7c679a8 |
| F3 | 独立-1 | medium | no | self-inflicted | product | accepted | 確認待ち: hooks.json の description と root CLAUDE.md のレーンの表の文言を、ユーザーの確認なしに次の PR へ回した（依頼より狭い）。references・skills は F4 で直した。hooks.json・CLAUDE.md は open の 旧#532 があるので同時に 1 本の規則で触れない。この PR では直さず、旧#532 のマージ後の次の PR で直す案で進め、ユーザーに確かめる |
| F4 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | independent-review.md:19・51、post-completion-pr-flow.md:201、self-review-lanes.md:119、post-merge-qa.md:32、gdd-pr-review/SKILL.md:68・84・86、check-gate-ledger.sh:127・134 が gate は止めると書いたまま。実行後の通知の形に直した。commit: b7c679a8 |
| F5 | 独立-1 | low | no | self-inflicted | product | accepted | 止めない出口が PR 台帳の登録より前にあり、作られた PR の root が台帳に載らない。raw steering の出口は F1 の直しで exit しなくなった。command-parse-error の出口は残る |
| F6 | 独立-1 | low | no | self-inflicted | product | accepted | pre-push の unresolvable-root の記録が、PROJECT_ROOT を決める前に呼ばれ、repo の hash が空文字の値になる |
| F7 | 独立-1 | low | no | self-inflicted | product | accepted | gate-notice.sh のエスケープが、タブ・LF・CR 以外の制御文字を扱わない |
| F8 | 独立-1 | low | no | self-inflicted | product | accepted | pre-push の通知が GDD_SKIP_PRE_PUSH_GATE を案内し続け、使うと would-block の記録が減る |
| F9 | 独立-1 | low | no | self-inflicted | product | accepted | pre-PR の本文の末尾が「PR を作成してください」のままで、前置きの「更新してください」と食い違う |
| F10 | 独立-1 | low | no | self-inflicted | product | accepted | pre-push のテストの _run_hook が state dir を渡さず、実の pre-push-gate-suppressed.log に行を足す |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片・ADR の「GDD_SKIP_PRE_PUSH_GATE=1 は通知と記録を省く」が、unresolvable-root と opt-out の記録失敗を除いていない |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の state dir に書くものの一覧に、2 つの新しいログが無い |
| F13 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 置き換えた 2026-10-03 の ADR の側に、逆向きの Superseded の参照が無い |
| F14 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | pre-push の opt-out の記録失敗の分岐のコメントと 2026-09-07 の ADR が、止める前提のまま |
| F15 | 独立-1 | low | no | self-inflicted | test-power | accepted | 宣言した code と本文の reason code が一致するかを、どのテストも見ていない |
| F16 | 独立-1 | advisory | no | self-inflicted | style | accepted | SECURITY.md の「もともと止めない」と、通知の本文の先頭の ⛔ が、止めたと読める |
| F17 | 独立-2 | medium | no | self-inflicted | product | accepted | 不足を集めた後で後段が set -e で落ちると、trap が集めた分だけを出して exit 0 し、落ちたことと走らなかった検査が通知にも記録にも出ない |
| F18 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | post-completion-pr-flow.md:203・205・206 の差し戻しの手順が、pre-PR gate の block を前提にしたまま |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | check-gate-ledger.sh:18・124、independent-review.md:23、post-completion-pr-flow.md:80、state-field-tiers.md:69、post-completion-learning.md:52、TROUBLESHOOTING.md:232-242、CONTRIBUTING.md:149、rollback-patterns.md:59 に、gate が止めるという記述が残る |
| F20 | 独立-2 | low | no | self-inflicted | test-power | accepted | 複数 code の記録が 1 行であることを、テストが固定していない |
| F21 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | raw-steering-in-diff の文だけ Next Action=done が固定で、1 本の通知の中で Next Action が食い違いうる |
| F22 | 独立-2 | low | no | self-inflicted | product | accepted | --head の不一致を通知した後も、今の branch の HEAD で ADR・Health・独立レビューの検査を続ける |
| F23 | 独立-2 | low | no | self-inflicted | product | accepted | 制御文字が 1 つ混ざると、まとめた通知が全部 JSON として読めなくなる |
| F24 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | post-merge-qa.md:32 の復旧手順が、通知を受けた時点で revert の PR がもう作られていることと合わない |
| F25 | 独立-2 | low | no | self-inflicted | product | accepted | 確認待ち: hooks.json の説明と root CLAUDE.md のレーンの表の後回しに、ユーザーの確認が記録されていない（F3 と同じ問い） |
| F26 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「後段が落ちても消えない」は、timeout で殺されたときには当たらない |
| F27 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「空の配列は使わない」というコメントと、新しい配列が食い違う |
