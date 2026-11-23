---
lane: L1
pr: 356
follow_up_of: 330
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | acad725d1c9eda630929332b762c61e839d80d81 | 1 | 0 | 1 | 2026-10-03T21:36+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) | acad725d1c9eda630929332b762c61e839d80d81 | 0 | 0 | 0 | 2026-10-03T21:36+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 16b0b26d98f6f6616b3b23021ca38b96d3fe33f5 | 1 | 0 | 1 | 2026-10-03T21:54+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) | 16b0b26d98f6f6616b3b23021ca38b96d3fe33f5 | 0 | 0 | 0 | 2026-10-04T19:32+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 2ddf426fe77d76da17898534b26a0c93d60c82c1 | 0 | 0 | 0 | 2026-10-04T19:32+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | gdd-dev.md:80 の手順 4 から別の active な session_id の確認を外したため、brainstorming 中に同じ checkout で lock を取ったセッションの state を上書きし、その側の done guard が走らなくなる。閉じ方: 列挙。方針メモ-1 で Opus も (i) 手順 4 の確認を戻し手順 2 と両方に置く を推奨（食い違いなし）。実測: フォールバックの手動 Write 133 回・62 セッション、lock の文言 237 回・128 セッション。commit: bfa0afc569ef54c942d3a705796b19601c024ebb |
| P2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | README.md:271 と断片が lock の条件を runtime 名で書いているが、実際は両方のセッションが session_id を持つかで決まる。follow_up_of のため限界に書いた |
| P3 | 独立-1 | low | no | self-inflicted | product | accepted | gdd-dev.md:73 の手順 2 が、自分の session_id が空のときの扱いを書いておらず、setup-gdd-loop.sh:137 と受理集合が違う。follow_up_of のため限界に書いた |
| P4 | 独立-1 | low | no | self-inflicted | product | accepted | gdd-dev.md:70 の「0 以外で終われば止まる」が、起動できなかったときの 126・127 を区別しない。follow_up_of のため限界に書いた |
| P5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 手順 2 で止まったときは script の文言が出ないので、TROUBLESHOOTING の新しい節を停止メッセージで検索できない。follow_up_of のため限界に書いた |
| P6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片が手順 4 の確認を外したことに触れていない。手順 4 の確認を戻したので、断片の記述が差分と合う。commit: bfa0afc569ef54c942d3a705796b19601c024ebb |
| P7 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 未リリースの断片 3 本が同じ推奨を順に書き換えている。次のリリースで版の節を 1 つにまとめる。PR 本文に列挙 |
| P8 | 独立-1 | advisory | no | inherited | doc-claim | accepted | docs/SECURITY.md:222 の「atomic lock（mkdir 方式）」が、session_id の lock の条件とフォールバックが mkdir の lock を取らないことを書いていない。PR 本文に列挙 |
| P9 | 独立-1 | advisory | no | inherited | test-power | accepted | test_setup_gdd_loop_session_lock.py が、session_id が空のときに止まらず上書きする挙動を固定していない。PR 本文に列挙 |
| P10 | 方針メモ-1 | advisory | no | inherited | fail-open | accepted | Opus の推奨は (i)。(ii) は散文で lock の解放・stale 判定を守らせられず、早く active: true を書くと途中停止で誤 block を作る。残る限界（手順 4 の読み取りと書き込みの間の race、session_id が空のセッション）は以前からあるもので受け入れる |
| Q1 | 独立-2 | high | yes | inherited | fail-open | fixed | 列挙: gdd-dev.md:74-80 のフォールバックの雛形が `---` の無い形で、stop hook の parse_state が例外にして done guard を通らずに停止を通す。影響先・pre-existing・閉じ方: 列挙。方針メモ-2 で (a)：雛形を setup-gdd-loop.sh と同じ `---` で囲んだ形にし、手順 4 で全体を書き直す。commit: 2ddf426fe77d76da17898534b26a0c93d60c82c1 |
| Q2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片に手順 4 の読み直しの挙動が無い |
| Q3 | 独立-2 | low | no | self-inflicted | product | accepted | 手順 4 の「止まる」に、知らせる内容と human check を出さないことが無い |
| Q4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 手順 2・4 の比べる相手と、session_id が空のときの扱いが無い |
| Q5 | 独立-2 | low | no | inherited | product | accepted | フォールバックは brainstorming の間 lock を持たない |
| Q6 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | RED-GREEN が手順 4 の分岐を覆うか未確認 |
| Q7 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 断片の 2 文目が 旧#330 の断片と同じ挙動を書いている |
| Q8 | 方針メモ-2 | advisory | no | inherited | fail-open | accepted | 実測: Write で gdd-dev.local.md を書いた呼び出しは frontmatter あり 31、無し 5（5 セッション、うち active: true 2）。事故の形があるので (a)。Opus も (a) を推奨し、雛形に workflow_runtime は入れない（固定値だと Cursor のフォールバックが cross-runtime guard で止まる）。stop hook 側で `---` 無しを受理する案は L1+ で範囲外 |
| R1 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文が、新しい雛形で done・cancelled のときに state が消えるようになることを書いていない。follow_up_of のため限界・advisory に書いた |
| R2 | 独立-3 | low | no | self-inflicted | product | accepted | 雛形に本文が無く、stop hook の継続指示が指す「本文」が空になる。follow_up_of のため限界・advisory に書いた |
| R3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 直ったのは session_id のある Claude Code だけで、断片はすべての runtime で直ったように読める。follow_up_of のため限界・advisory に書いた |
| R4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | test_setup_gdd_loop_session_lock.py:71 の docstring が、今は作らない `---` 無しの形を「フォールバックが作る」と書いている。follow_up_of のため限界・advisory に書いた |
| R5 | 独立-3 | low | no | inherited | doc-claim | accepted | references/stop-hook-structured-markers.md:61-67 は frontmatter 破損を block と書くが、実装とテスト（AC-E8-3）は停止を通す。follow_up_of のため限界・advisory に書いた |
| R6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | フォールバックは brainstorming の間 lock を取らず、README:271 の「終わるまで止まる」がその間は成り立たない。follow_up_of のため限界・advisory に書いた |
| R7 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | 雛形が parse_state で読めることを固定するテストが無い。follow_up_of のため限界・advisory に書いた |
| R8 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | TROUBLESHOOTING の原因に、`---` の無い state と片付かずに残った旧 state が無い。follow_up_of のため限界・advisory に書いた |
