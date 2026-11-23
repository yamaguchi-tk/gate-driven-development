---
lane: L1+
pr: 411
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus)（Opus は block を advisory に落とす main の案に対し、advisory は書いた agent に届かず違反 0 件のときしか走らないので、検出を消すよう推奨。乗り物のテスト 4 本と Attempts のテストの差し替えも指摘。main は推奨を採り、食い違いは残らない） | - | 0 | 0 | 0 | 2026-10-08T12:47+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 03dbbfca | 0 | 0 | 0 | 2026-10-08 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 3ec850d5 | 0 | 0 | 0 | 2026-10-08 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| F1 | 独立-1 | low | no | self-inflicted | test-power | fixed | test_non_steering_path_allowed の入力「TODO: implement」がどの検出器にも当たらず、is_steering_path の変異を見ない。email の入力に替えた。commit: 3ec850d5 |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | validate-steering-write.py のヘッダの「ルール正本」一覧が、検出しない § プレースホルダー禁止を載せ、§ 省略記法禁止を載せていない。commit: 3ec850d5 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | test_origin_session_write_once_contract.py:574・:776 の docstring が hook の検査に placeholder を挙げたまま。commit: 3ec850d5 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | CONTRIBUTING.md § 4 が hook がプレースホルダーも見る前提のまま。commit: 3ec850d5 |
| F5 | 独立-1 | low | no | self-inflicted | style | fixed | 定数名 PLACEHOLDER_EXCLUDE_SECTIONS がもう無い検出器を指す。ELLIPSIS_EXCLUDE_SECTIONS に改名。commit: 3ec850d5 |
| F6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 変更断片の Affected Files にテストが無く、Validation に足したテストの名前が無い。commit: 3ec850d5 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片が「規定はそのまま」と書くが、規定の対象外を変えている。commit: 3ec850d5 |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Self-Review の scan が見ない steering のファイル（state.md・worklog.md など）が限界と規定に書かれていない |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | common-guardrails.md:59 の「TBD を書けない」が、止められる事実として読める |
| A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの 20261002 の断片が placeholder の fence 免除を書いたまま |
| A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 撤去の根拠の実測に、数え方と外れた件の内訳が無い |
| F8 | 独立-2 | medium | no | self-inflicted | doc-claim | next-pr | 列挙: 正本 common-guardrails.md の対象外（語に触れるだけの記録・コード例）が、task-breakdown-steps.md:337・:378 と gdd-task-breakdown SKILL.md の scan の手順に無く、読み違えが両方向に起きる |
| F9 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片に書いた、足したテストのファイル名が違う。未リリースの断片は後の PR で直せないので、この PR で直した（changelog.d だけの commit で巡は無効にならない）。commit: 70efd3e6 |
| F10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に、規定の対象外を足したことと CONTRIBUTING.md § 4 の更新が無い。commit: なし（PR 本文） |
| F11 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | CONTRIBUTING.md:159 と common-guardrails.md:180 が、Self-Review が steering の全 artifact を見るように読める（scan は tasklist の Steps と requirements.md・design.md だけ） |
| F12 | 独立-2 | low | no | inherited | doc-claim | next-pr | common-guardrails.md:198 の ellipsis の除外に、reviews.md への書き込みの除外が無い |
| A5 | 独立-2 | advisory | no | inherited | doc-claim | accepted | validate-steering-write.py:88 の正本の参照先（§ .steering artifact の正本性）がローカル絶対パスの規定ではない |
| A6 | 独立-2 | advisory | no | inherited | test-power | accepted | test_stop_hook_validate.py:185 の assertNotIn("placeholder expression") は消した文言を固定しているだけ |
| A7 | 独立-2 | advisory | no | inherited | doc-claim | re-reported | common-guardrails.md:59 の「TBD を書けない」（独立-1 の A2 と同じ） |
