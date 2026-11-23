# ADR: W-36 — steering artifact のサイズ上限 deny と security reviewer の条件起動

> 2026-10-16 追記: steering の size 上限は、今は書き込みを止めずに通知する（`plugins/gate-driven-development/changelog.d/20261016-steering-size-notice.md`）。kill switch `GDD_STEERING_SIZE_DENY` と、size の deny counter・降格の連動は無くなった。本文の「deny」は当時の挙動である。

- Status: Accepted（2026-09-06）
- 対象タスク: `20260904-w36-task-ceremony-cost`
- リリース: `plugins/gate-driven-development/CHANGELOG.md` § `[0.39.0]`
- **逐語アーカイブ（正本）**: `plugins/gate-driven-development/docs/design/2026-09-06-w36-task-ceremony-cost-adr.md`

本ファイルは repo 直下の ADR インデックスである。**個々の判断の本文・数値・実測はすべて上記の逐語アーカイブが正本**で、
ここには**転記しない**（同じ値を 2 箇所に置くと片方が黙って陳腐化する。この規律は PR-W3 の ADR-12 で確立した）。

## Context

GDD 改善計画 §2 W-36「task あたりの儀式コストを下げる」のうち、human check で **AC-3 / AC-5 / AC-6 / AC-7** に
スコープを確定した分の実装である（AC-1 / AC-2 / AC-4 / AC-8 と `metrics.jsonl` は後続タスクへ繰り越し）。

コストの実測上の主因は 2 つあった。ひとつは **reviewer を subagent として実起動した gate round が
inline checklist の 4〜8 倍の所要**になること。もうひとつは **steering artifact が際限なく肥大する**こと
（本タスク自身の `tasklist.md` が 146KB、`state.md` が 25KB に達した）。
前者には security reviewer の条件起動の明文化（AC-3）を、後者には write 時の deny（AC-5）を当てた。

## Decisions

逐語アーカイブに **ADR-1〜ADR-6** として記録した（ADR-5 / ADR-6 は PR 旧#37 の Copilot レビュー対応で追加）。いずれも AC-5 の deny 判定の受理面に関する判断である。

| ADR | 決定の要旨 |
|---|---|
| ADR-1 | 未作成ファイルへの `Write` は size 判定を継続する（全文置換なので post-write サイズが確定する）。差分系 `Edit` / `MultiEdit` は従来どおり算出不能 |
| ADR-2 | deny 本文の数値は桁区切りなしに統一する（grep 可能性を優先） |
| ADR-3 | 「未作成」と「算出不能」を分離する。`FileNotFoundError` のみ未作成、その他の `OSError` は算出不能＝非 deny |
| **ADR-4** | **size 算出の入力面を `extract_content_chunks` と揃える**。どの deny が効くかが payload のキー名で変わる状態は機械強制として成立しない |
| **ADR-5** | **size deny を既存カテゴリの escape hatch から独立させる**。既存カテゴリが 3 回 deny で降格する write でも size deny が成立していれば deny を維持し、size は自身の 3 回周期でのみ降格する（Copilot 指摘: 超過 + email 同梱で size を無期限に迂回できた） |
| ADR-6 | `_steering_size_target` は resolve 後の parts に `.steering` が無ければ size 非対象（`/x/.steering/../state.md` の誤 deny を防ぐ）。既存 deny の判定 `is_steering_path` は変えない |

## Consequences

- `.steering/` の `state.md` / `tasklist.md` / `design.md` は、post-write サイズが上限を超えて**増える** write が deny される。
  上限値は既存定数を流用し、新しい数値は増やしていない
- **サイズが減る write は上限超過中でも常に allow** される。これが唯一の出口であり、ADR-3 はこの出口が
  権限エラー等で塞がることを防ぐための分離である
- kill switch `GDD_STEERING_SIZE_DENY=0` は strip 後の完全一致のみを受理し（fail-closed）、無効化中も毎回 notice を出す
- ADR-4 の閉包は当初キー集合の二重定義（`NEW_STRING_KEYS` と `extract_content_chunks` のリテラル tuple）の上に成り立っていたが、
  PR 旧#37 の独立レビュー H-1 是正で top-level / edits 内とも `NEW_STRING_KEYS` を参照させ**構造的に閉じた**（Architecture Debt Finding は close）

## 後続 task が守るべき制約

- **上限値は実測に対して較正されていない**。移行期に deny が頻発する場合、緩和は kill switch・縮小 allow・
  3 回連続 deny の降格・退避導線で行い、閾値を安易に動かさない
- **AC-3 / AC-6 の契約テストが固定できるのは「文言が置かれたこと」まで**。reviewer selection も finding 生成も
  実行時の LLM 判断であり、実効性は後続の実測（DV-1 / DV-2）で見る。契約テストの pass を実効性の証跡に読み替えない
- **AC-5 は Bash 経由の write を迂回できる**。抑止であって強制ではない、という射程を広げて書かない
