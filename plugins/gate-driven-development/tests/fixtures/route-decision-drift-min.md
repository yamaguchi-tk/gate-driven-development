<!--
route-decision fixture (frozen copy / minimized + anonymized)
source: 20260407-example-allowlist steering worklog.md
minimization/anonymization policy: design.md (PR-W0) § Sensitive Data / Masking Policy § enforcement point 5
acceptance surface: references/phase-progression.md § Bounce 計測の受理面
NOTE: 件数の正本はこの fixture（データ）そのもの。期待値の literal は計上テスト 1 箇所だけに置き、
      fixture から導出しない（AC-9）。内容を書き換えるときは同じ commit で計上テストの期待値も更新すること。
-->

## 2026-04-07 Systematic Debugging Route Decision

- 症状: production runtime を `<resource>` へ更新後も、`<repo>#<n>` の reopen E2E は worker で `ACCEPTED` するだけで、5 分以上待っても bot comment が返らない。
- 根拠:
  - worker log `<log-id>` -> `status=ACCEPTED`
  - issue `#<n>` の `updatedAt` は `2026-04-07T23:25:34Z` のままで、新規 bot comment が増えない
  - `Apply Failed` 判定位置の command 修正だけでは即時 no-action が実現していない
- route 判定:
  - `implementation_fix_only` ではなく `design_detail_only`
  - 理由: 要件は変えずに、`Apply Failed` の no-action 判定を Claude command 依存から runtime/intake 側の deterministic fast path へ移す責務変更が必要なため
- 次の戻り先: `gdd-design-gating`
