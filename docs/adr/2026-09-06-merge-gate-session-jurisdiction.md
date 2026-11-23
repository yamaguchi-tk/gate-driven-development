# ADR: merge gate の session 管轄判定を他 gate と揃える（`session-mismatch` block の削除）

- **日付**: 2026-09-06
- **状態**: 採用
- **対象タスク**: `20260906-merge-gate-session-jurisdiction`
- **リリース**: `plugins/gate-driven-development/CHANGELOG.md` `[0.41.0]`
- **関連**: `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh` / `hooks/scripts/lib/detect-steering.sh` の `gdd_session_continuity_ok`

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

## Context

merge gate（`run-merge-gate-hook.sh`）だけが、`.claude/gdd-dev.local.md` の `active: true` マーカーと
現セッションの `session_id` が一致しない場合に `session-mismatch` で **block** していた。

この block には 2 つの問題があった。

1. **復旧手順が原理的に実行不能**。block メッセージは「セッションを開き直して再実行してください」と案内するが、
   不一致の原因が「別セッションが残した marker」の場合、再実行しても同じ marker を読むため何度でも block する。
   marker の所有者を特定して消す導線も、marker を自動失効させる TTL も存在しなかった。
2. **発火条件が「他セッション」に限られない**。`session_id` が空・欠落しているケースでも同じ block に落ちる。
   これは自セッションが marker を書き込む途中で失敗した場合にも起きる。`commands/gdd-dev.md` の setup
   フォールバック手順自体が `session_id:` を空のまま state を作る形を案内しており、恒常的な発生源になっていた。

同じ `gdd_session_continuity_ok` を使う他 gate は 9 箇所 / 8 hook あるが、**いずれも不一致を
`|| exit 0`（管轄外）として扱っている**。merge gate だけが block に倒す非対称に、正当な理由は見つからなかった。
関数側の契約（`gdd_session_continuity_ok "..." || exit 0`）から見ても、block は契約からの逸脱だった。

一方で「単純に `exit 0` へ倒す」ことはできない。残置 marker 1 個で merge gate 全体
（承認証跡・再 fetch 証跡・bot review・independent review の検査）が無効化される既知の fail-open を再導入するためである。

## Decision

**`IS_ACTIVE_MARKER` を「自セッションが所有すると確認できた active marker」の意味へ揃え（`IS_OWNED_ACTIVE_MARKER` へ改名）、
所有を確認できない marker は block ではなく「起動根拠からの降格」に倒す。** 降格後も steering 解決と証跡検査は継続する。

- **経路 A**（marker 単独で gate 対象と判定していた分岐）: block をやめ、marker 由来の起動根拠だけを外す。
  抑止したことを `merge-gate-suppressed.log` に `unowned-active-marker-demoted` として 1 行残す
- **経路 B**（PR URL 一致経路）: session 検査を撤去し、そのまま証跡検査へ進める。
  検査項目は減らない（承認 sha 一致・鮮度・bot review・independent review は引き続き要求する）
- `session-mismatch` の reason code と `_mg_action` のカタログ行、テスト側の literal を削除する。
  他 gate（pre-push 等）の `session-mismatch` ログは変更しない

却下した代替案:

| 案 | 却下理由 |
|---|---|
| 不一致時に無条件 `exit 0` | 残置 marker 1 個で証跡検査ごと無効化される既知の fail-open の再導入になる |
| reason code を残して復旧手順だけ改善 | marker の所有者特定も TTL も無いため、実行可能な手順を書けない |
| marker に TTL を持たせて自動失効 | 残置マーカーの寿命管理は承認済み scope の外（human check で境界として確認済み） |

補助的な判断（実装細部）:

- **降格ログの呼び出しを subshell + `|| true` で二重に封じる**。`_mg_log_suppressed` は `HOME` 未設定（`set -u`）と
  `shasum` / `sha1sum` の両方が無い場合（`pipefail`）にシェルごと即死する。既存の呼び出しは直後が `exit 0` なので
  無害だったが、降格は**処理を継続する初めての呼び出し**であり、即死すると証跡検査に到達せず無出力で終わる
  （= 新しい silent fail-open）。`|| true` だけでは `set -u` の死を捕まえられない
- **同値検査は「相対的な一致」ではなく「絶対期待値の pin」で組む**。両側が同時に壊れると検知できないため、
  判定表（6 入力 × marker 3 状態）で block の有無と reason code を絶対値で固定する

## Consequences

**縮小する保護面は 3 面**（正確な列挙と実測値は CHANGELOG `[0.41.0]` § Breaking Contract Changes (b) が正本）。
(1)(2) は marker 由来、(3) は走査コスト由来で性質が異なる。

- (1) 他人の `active: true` marker がある repo で、その steering が対象 PR を記録していない merge → 素通り
- (2) done steering が複数あり対象 PR をどれも記録していない場合 → `steering-ambiguous` block から素通りへ
- (3) 降格ケースは `.steering/` の全走査へ必ず進むため、done 候補が約 295〜300 件を超える repo では
  hook が 10 秒 timeout に達して無出力のまま素通りしうる。走査コスト自体は所有済み marker でも同じで
  本変更が作ったものではないが、降格ケースが新たにこの経路へ入る

(1)(2) はいずれも「対応する証跡が無く、実行可能な復旧手順も持たない、他人／所有不明の marker だけを根拠にした強制」
という同一クラスであり、今回の incident そのものである。

承認証跡の provenance が session に紐づかなくなる点も許容した。窓は「承認・再 fetch 直後で HEAD が動いていない間」
（承認 120 分鮮度 / 再 fetch 10 分鮮度 / head sha 一致 / PR 番号一致）に限られ、`active: false` marker では
従来から同じ前提だったためである。

**再導入条件**: 将来「session 越境の merge」を再度 block したくなった場合、同名の reason code をそのまま復活させない。
復活させる block は、削除前の `session-mismatch` が欠いていた「実行可能な復旧手順」を持つことを条件にする
（marker の所有者を特定して削除を案内する、marker に TTL を持たせて自動失効させる等）。

**後続で参照すべき制約**:

- `hooks/scripts/lib/detect-steering.sh` と他 9 consumer は無変更（他 gate の session continuity は変えない）
- `commands/gdd-dev.md` の空 `session_id` フォールバック手順は降格の恒常的な発生源として残っている（本 PR では非スコープ）
- Distill to Spec は `not_applicable`。plugin 側の `plugins/gate-driven-development/docs/specs/` は capability spec としての運用実績が無く
  （2026-06 の design doc 2 本のみ）、merge gate の契約は CHANGELOG § Breaking Contract Changes が正本として機能している
