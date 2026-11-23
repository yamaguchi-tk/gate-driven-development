# Root Cause Investigation Findings

## AssumeRole 失敗調査（アラート調査）

- **Cycle 1/3**: 確認済み = 中央 account trust は ExternalId 条件を含む構成。除外 = 「ExternalId を丸ごと付け忘れている」仮説（コード実装済みのため）。現在の仮説 = trust condition か対象アカウント個別設定に絞り込み中。status=no_root_cause_yet
- **Cycle 2/3**: 確認済み = CloudTrail で AccessDenied 22 件を確認しジョブの入力対象とほぼ一致。除外 = 「ExternalId 付き assume の仕組み自体が壊れている」仮説（同じ role への成功イベントを確認したため棄却）。現在の仮説 = 対象アカウント側の role / trust / 一括配布に起因。status=likely
- **Cycle 3/3**: 確認済み = 中央アカウント側の一括配布は `UPDATE_COMPLETE` で現行 runtime role ARN を指しており、失敗は対象アカウント側に集中。除外 = 中央側の設定不備。現在の仮説（確定） = 対象アカウント側 `example-read-role` role の AssumeRole 経路の問題。status=confirmed

## Error Log

| #   | Phase | Error | Root Cause | Resolution | Attempt |
| --- | ----- | ----- | ---------- | ---------- | ------- |
| 1   | root-cause-investigation | 22 account で `sts:AssumeRole` 失敗 | 対象アカウント側 `example-read-role` role の AssumeRole 経路に問題があり、調査ツールの自由文一括調査経路で ExternalId 付き AssumeRole の正規手順が保証されていない | `implementation_fix_only` として `gdd-subagent-driven-implementation` へ route。対象アカウント側 role の trust policy 実値は残る不確実性として修正 PR の受け入れ確認で埋める | 1/3 |
