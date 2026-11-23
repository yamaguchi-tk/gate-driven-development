# ADR: PR-W0 — Stop hook の誤バインド false block 修正と計測・通知導線の是正

- Status: Accepted（2026-08-30）
- 対象タスク: `20260822-pr-w0-defect-telemetry`
- リリース: `plugins/gate-driven-development/CHANGELOG.md` § `[0.34.0]`
- **逐語アーカイブ（正本）**: `plugins/gate-driven-development/docs/design/2026-08-30-pr-w0-defect-telemetry-adr.md`

本ファイルは repo 直下の ADR インデックスである。**個々の判断の本文・数値・実測はすべて上記の逐語アーカイブが正本**で、
ここには**転記しない**（同じ値を 2 箇所に置くと片方が黙って陳腐化する。この規律は PR-W3 の ADR-12 で確立した）。

## Context

Stop hook の done guard が、**セッションに紐付いていない別 worktree の tasklist** を検査対象にしていた。
その結果 `done` も `blocked` も両方 block され、**1 セッションで 9 回・約 3 日**作業が止まった実績がある。
あわせて (a) bounce log が導入後 0 件のまま実運用の debug 遷移を 1 件も捉えていない、
(b) ターンが異常終了しても誰も気付かず約 90 分放置される、という計測・通知側の欠落があった。

## Decisions

逐語アーカイブに **ADR-1〜ADR-20** として記録した。主なものは次のとおり（詳細・根拠・却下案は各 ADR を参照）。

| ADR | 決定の要旨 |
|---|---|
| ADR-1 / ADR-8 | 検査対象は **current worktree に bind された steering だけ**。他 worktree は列挙しない。bind 不能時の表示・resume-from フォールバックは 1 関数に集約する |
| ADR-2 / ADR-13 / ADR-19 | 異常終了の永続記録は append せず 1 件保持。キー集合を固定し、**「使えない記録」は fail-closed で削除**する（例外は state dir symlink） |
| ADR-3 | Route Decision の計上面は正本書式に限り、受理面の外は `unparsed_route_sections` として**件数で可視化**する（黙って 0 件にしない） |
| ADR-4 / ADR-14 | untrusted な `error_details` を通知本文と `additionalContext` に流さない。通知（AC-16）は記録（AC-17）に従属させない |
| ADR-10 / ADR-11 | `--help` の受理面を「行番号範囲」から**先頭コメントブロックの機械判定**へ。AC の述語を「不変」から**実挙動**へ改訂 |
| ADR-15 / ADR-17 | hook の fail-open は**全称をやめ、射程を列挙**する。射程の (E) は「データ I/O」に限る |
| ADR-18 | hook の実測基盤に**環境（bash 版数 / OS）の軸**を入れる |
| **ADR-20** | **承認済み design の字句は「後続タスクが写経しても壊れない」形に保つ** |

## 後続 task が守るべき制約

- **done guard の fail-open は 2 条件**（bind が解決できない **かつ** current worktree にも steering が無い）。
  bind 不能でも自 worktree の steering が**ちょうど 1 つ**なら検査する。
  **複数あるとき「どれか」を選ぶのは推測**であり、本 PR が塞いだ欠陥そのものなので行わない
- **走査器の合格表明には「走査した形 / 走査していない形」を併記する**。
  検出器を強くする方向は追わない（grep -> AST -> 観測子と替えても受理面の外側が毎回見つかることを 3 周で実証済み）
- **結論は「出荷時に実際にその入力を読む主体」に食わせて確かめる**。目視照合で代替しない
- **bind 不能時の fallback で選んだ steering は containment 検査を通してから block の根拠にする**。
  `Path.is_dir()` は **symlink を辿る**ので、検査なしだと他 worktree の tasklist で停止する
  （本 PR の是正がいったんこの退行を作り、completion-check が検出した）。
  bound 側 `lib/task_binding_resolve.py::_validate_binding()` と同じ
  `resolve(strict=False)` + `relative_to()` を使う。**前方一致に置き換えてはならない**
- **`state.md` の field は行頭アンカーで読む**。行内部分一致だと解説文中の言及を値として拾い、
  かつ正準形を素通りする（`Route In Progress` で実際に両方起きていた）

## 却下した代替案

- **bind 不能時に逆ソート先頭の steering を選ぶ** —— 推測で検査対象を決めるのは本 PR が塞いだ欠陥そのもの
- **受理面の表明を全走査器に義務づける lint の新設** —— 遡及改修の量が本 PR の scope を超える（YAGNI）
- **結論を観測子非依存の述語で二重化することの一般規律化** —— 適用できる対象が限られ、形骸化する

## 既知の未達

- `validate-plugin.sh` は exit 1。**ただし統合先の `origin/main` 単独でも同一の数値で同じ 2 件が落ちる**
  （runtime token budget の超過）。本 PR は budget を 1 トークンも増やしていない
- MCP 再試行の指示は**機械強制ではない**。配布先を参照しない skill には届かない
