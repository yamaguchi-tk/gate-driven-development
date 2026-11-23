## Root Cause Investigation

### 症状

複数のアカウントすべてで `sts:AssumeRole` が失敗し、以前は成功していたという報告です。まだ fix ではなく、真因候補を証跡で絞ります。root-cause-investigation の Phase 1〜3 を、仮説検証として最大 3 cycle まで回します。

### Phase 1: 集めた事実

- AssumeRole の正規ターゲットは `example-read-role`、実行側は `example-runtime-role`
- コード上は `ExternalId` を Secrets Manager から読み、`sts.assume_role(... ExternalId=...)` している実装が既にある（単純な付け忘れではなさそう）
- 中央 account の runtime role には inline policy が 1 本だけ付いている

### Phase 2: 比較した working code と差分

同じ runtime role から、同時刻帯の別ジョブ（`example-inventory-job`）は一部の `example-read-role` へ AssumeRole できている非対称性がある。「仕組み自体が壊れている」のではなく、対象の一部だけで失敗している可能性が高い。

### Phase 3: 仮説と検証（3 cycle 上限までの仮説検証ループ）

**Cycle 1/3**

- Working Hypothesis: 中央 account 側の trust condition か ExternalId 不一致が原因ではないか
- Probe: 中央 account の runtime role の inline policy と trust policy を読む
- 結果: trust は runtime role + ExternalId 条件で構成されているが、これだけでは対象アカウント側の実体までは分からない

Root Cause Confidence:
- status: no_root_cause_yet
- cycle: 1/3
- disproving evidence checked: 中央 account 側の trust 定義自体は ExternalId 条件を含んでおり、単純な条件欠落ではなさそう
- next evidence to collect: 実際に ExternalId あり/なしで AssumeRole を再現させ、失敗が trust condition 由来かを直接確認する
- fix allowed: no

まだ **未確定** です。仮説検証を続けます。

**Cycle 2/3**

- Working Hypothesis: ExternalId 条件そのものは機能しており、失敗は対象アカウント個別の trust / 展開状態にある
- Probe: 「ExternalId なしなら失敗、ExternalId ありなら成功」を read-only 認証で再現。CloudTrail で実際の AccessDenied イベントを確認
- 結果: CloudTrail 上で 定期ジョブ由来の AccessDenied を複数件確認。対象は ジョブの入力のユニーク account とほぼ一致し、中央 account も同じ失敗に含まれる。一方、中央 role への成功イベントも別に存在し、ExternalId 付き assume の仕組み自体は runtime で動くことが確認できた

Root Cause Confidence:
- status: likely
- cycle: 2/3
- disproving evidence checked: ExternalId 付き assume の仕組み自体は動作している（成功イベントあり）ため、「ExternalId 伝播が全面的に壊れている」仮説は棄却できる
- next evidence to collect: 対象アカウント側で role / trust / 一括配布が実際にどうなっているか
- fix allowed: no

依然 confirmed には届かず、**未確定** のまま Cycle 3 へ進みます。

**Cycle 3/3**

- Working Hypothesis: 対象 AWS アカウント側の `example-read-role` role を、実行側の runtime role が AssumeRole できていない（trust / 一括配布起因）
- Probe: 中央アカウント側の一括配布の管理面から対象アカウントのスタック配布状況を確認。手元 SSO からの直接クロスアカウント確認は権限上できなかったため、間接証跡（CloudTrail の非対称性、一括配布の `UPDATE_COMPLETE` 状態、成功/失敗イベントの分布）で絞り込む
- 結果: 中央アカウント内の一括配布由来のスタックは `UPDATE_COMPLETE` でパラメータも現行 runtime role ARN を指している一方、失敗は対象アカウント側に集中している非対称性が残り、対象アカウント側の role 実体がここで確定できる状態になった

### Phase 4: 確定した root cause

一次原因は「対象 AWS アカウント側の `example-read-role` role を、実行側の runtime role が AssumeRole できていない」ことです。

Root Cause Confidence:
- status: confirmed
- cycle: 3/3
- disproving evidence checked: ExternalId 伝播の仕組み自体は動作している（Cycle 2 で確認済み）ため原因ではない。中央アカウント側の一括配布は正常に済んでいる（Cycle 3 で確認済み）のため中央側の設定不備でもない
- next evidence to collect: 対象アカウント側 role の trust policy 実値（手元 SSO の権限では直接読めず、**残る不確実性** として修正 PR の受け入れ確認に持ち越す）
- fix allowed: yes

### 意思決定

3 cycle の仮説検証を経て root cause が confirmed になったため、次は GDD の**修正フロー**に乗せます。`gdd-systematic-debugging` へ SMI block を渡し、`implementation_fix_only` として `gdd-subagent-driven-implementation` に route します。対象アカウント側 role の trust policy 実値という**残る不確実性**は、修正 PR の受け入れ確認（read-only diagnostic 追加）で埋める前提です。

## 👤 次にすること

- 根本原因: 対象アカウント側 `example-read-role` role の AssumeRole 経路に問題があり、調査ツールの自由文一括調査経路で ExternalId 付き AssumeRole の正規手順が保証されていない
- GDD フローで進める場合: `/gdd-dev` で修正フェーズを開始できます
