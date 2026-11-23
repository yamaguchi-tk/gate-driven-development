---
lane: L1+
pr: 156
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable。ユーザーの指示) + user | - | 1 | 4 | 0 | 2026-09-19T21:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus（transcript で claude-opus-5・effort max を確認） | 7ca1b7395b49151e6a7426abe3473f09a088d439 | 0 | 2 | 0 | 2026-09-20T00:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 25ff2669b1102a6668a49f163973dcc1b7b160c9 | 0 | 0 | 0 | 2026-09-20T10:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | e0c23e1a18fde72ca750a6d47b44ea2b237cf5cf | 0 | 2 | 0 | 2026-09-20T11:30+09:00 |
| PR後-1 | Cursor / Grok 4.6 (effort=high) + user, 全差分（origin/main...HEAD、review-log 除外） | b4289b288e7aa38d61ba17095d9a7f0f994bbd6d | 1 | 1 | 1 | 2026-09-20T09:48+09:00 |
| 独立-4 | light-lane-independent-reviewer, 全差分, model: opus | c6bb7e00c22537cbd4f66e2538192591fb2d53c2 | 0 | 1 | 0 | 2026-09-20T13:10+09:00 |
| 独立-5 | light-lane-independent-reviewer, 全差分, model: opus | 59c8909ff6b2200da0a67d3a7f57b43669638b86 | 0 | 0 | 0 | 2026-09-20T14:03+09:00 |
| 独立-6 | general-purpose, 差分, model: opus, effort 継承, 定義本文を貼付（8fa70573 の main 取り込みで agent 定義が変わり、セッションは古い定義を保持）。base は前回の独立レビュー（c6bb7e00）ではなく main の merge commit 8fa70573（c6bb7e00 を base にすると、CI 対応で取り込んだ main の差分がこの PR の差分として reviewer に渡る） | 4e2088db4735409a33578b8843c0c7394fe95354 | 0 | 0 | 0 | 2026-09-20T16:05+09:00 |
| 独立-7 | general-purpose, 全差分, model: opus, effort 継承, 定義本文を貼付 | 66c5b7262e54e43146254ed03965372ee5458a61 | 0 | 0 | 0 | 2026-09-20T16:45+09:00 |
| 独立-8 | general-purpose, 差分, model: opus（agent 定義未反映のセッションでの fallback 起動） | 2a1b8e6ec9aecc37f5768dabb5f7cb780ad3a77b | 1 | 1 | 1 | 2026-09-20T15:23+09:00 |
| 独立-9 | light-lane-independent-reviewer, 差分, model: opus | 99dc0c5dcda8d82dbb65227a28f839bd81140ceb | 0 | 3 | 0 | 2026-09-20T15:50+09:00 |
| 独立-10 | light-lane-independent-reviewer, 最終の全差分巡, model: opus | 99dc0c5dcda8d82dbb65227a28f839bd81140ceb | 1 | 0 | 1 | 2026-09-20T16:03+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + user（安全策 4 の発火。PR後-1・独立-8・独立-10 の 3 巡で high を含む巡が合計 3 回に達した。Opus は選択肢 B（限定修正・残りは次の PR）を推奨したが、ユーザーは選択肢 A（① を全件このPRで修正）を選択） | 99dc0c5dcda8d82dbb65227a28f839bd81140ceb | 1 | 0 | 1 | 2026-09-20T16:41+09:00 |
| 独立-11 | light-lane-independent-reviewer, 差分, model: opus | a5532573621908cc647abce8ea604ed234100ef7 | 0 | 3 | 0 | 2026-09-20T17:03+09:00 |
| 独立-12 | light-lane-independent-reviewer, 最終の全差分巡（1 回目）, model: opus | a71fb569dd90d586811a0d3f36b12bfd93988c71 | 0 | 1 | 0 | 2026-09-20T17:32+09:00 |
| 独立-13 | light-lane-independent-reviewer, 差分, model: opus | 6bd6886ba6040d09d2511288d6b81e19957c4899 | 0 | 0 | 0 | 2026-09-20T17:47+09:00 |
| 独立-14 | light-lane-independent-reviewer, 差分, model: opus | 4673960a4011c1c14ea6b627e7618589f6d9d727 | 0 | 1 | 0 | 2026-09-21T18:30+09:00 |
| 独立-15 | light-lane-independent-reviewer, 最終の全差分巡（2 回目）, model: opus | 3c7d1b8e5807fb6550d9168fc08f73bbaa6839e1 | 0 | 2 | 0 | 2026-09-21T19:00+09:00 |
| PR後-2 | Cursor / Grok 4.6 (effort=high)、全差分（origin/main...HEAD、review-log 除外。review id 5264816726 と 5264964107、同一 tip `ef80614d` への重複レビュー） | ef80614d55470de389653e0aa2567b8a63091ba4 | 0 | 0 | 0 | 2026-09-21T18:25+09:00 |
| PR後-3 | Cursor / Grok 4.6 (effort=high)、全差分（origin/main...HEAD、review-log 除外。review id 5265713784） | dcfcf2a286695660e540adb5322c6f56d1342d9e | 0 | 0 | 0 | 2026-09-21T19:46+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | high | yes | self-inflicted | errexit-in-if | fixed | `if _compact_resume_check` の中は errexit が効かない。新しい setter の失敗が握りつぶされて発火に進む。各ステップで失敗時に return 1 し、setter は読み直しで非 0 を返す |
| pm-2 | 方針メモ | medium | no | self-inflicted | shared-reader-change | fixed | 草案の reader awk への set/del mode 追加は block gate の共有部品を変える。reader は触らず、sed 置換（区切り `[:=]`）＋読み直しで fail-closed にした（Opus・Fable が一致、ユーザー承認） |
| pm-3 | 方針メモ | medium | no | self-inflicted | lock-order | fixed | 発火条件の判定をロック取得より前に置かないと、発火しないセッションがロックだけ取って残す |
| pm-4 | 方針メモ | medium | no | self-inflicted | default-branch | fixed | source==compact だけでは、main の worktree で同じセッションが compact したときに Safe Resume の既定ブランチ検査を迂回する（Fable）。述語 `gdd_is_default_branch` を Safe Resume と共有した |
| pm-5 | 方針メモ | medium | no | self-inflicted | hook-output | fixed | 印を書けなかった systemMessage と既存のリマインダーが 2 個の JSON になる。1 個に合成した |
| pm-6 | 方針メモ | low | no | inherited | auto-cycle-cap | accepted | `AutoCycleCount` を戻す書き手が無く、重いタスクは上限 30 に届く（実データで 30・22）。変更断片の User Action Required に書いた |
| pm-7 | 方針メモ | advisory | no | self-inflicted | payload-evidence | accepted | compaction 成功後の SessionStart(compact) の実 payload は、headless の compaction が OAuth 切れで 2 回失敗して採れなかった。Claude Code 2.1.261 のコード（compaction 後に `source:"compact"` で SessionStart を呼ぶ）で代えた |
| M1 | 独立-1 | medium | no | self-inflicted | compact-test-wiring | deferred | test_compact_resume_sanitizes_long_task_field が payload と CompactSessionId を渡さず、発火しないまま通る。Task の 512 文字切り詰めが無検査になった（旧#154） |
| M2 | 独立-1 | medium | no | self-inflicted | setter-append-growth | fixed | 値の違うバッククォート形の行が先にあると、setter が compaction のたびに state.md へ 1 行ずつ追記する（修正前は 1 行まで）。変更断片の「書き換えずに」と食い違う（旧#155。ユーザーの指示でこの PR で直した） |
| L1 | 独立-1 | low | no | self-inflicted | payload-parse | accepted | payload の source が空だと、IFS のタブ畳み込みで session_id が source の変数に入る。実 payload では起きない |
| L2 | 独立-1 | low | no | self-inflicted | default-branch | accepted | HEAD が無い（unborn）・git が無いときは既定ブランチの条件を見ずに発火する。Safe Resume と同じ HEAD_EXISTS 条件で対称。source と session の条件は効く |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | compact 前後で session id が変わる約 2%（7/409）と、python3 が無い環境で自動復帰が発火せず知らせも出ない件が、Known Limitations に無い |
| L4 | 独立-1 | low | no | inherited | hook-owned-fields | accepted | CompactSessionId が state-schema.json の hook_owned_fields に未登録（CompactSource・AutoCycleCount も元から未登録） |
| L5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | lib 冒頭の「どの関数も非 0」が payload 読み取りに当たらない。MARK_WARNING が CompactSessionId と書き込み権限に触れない |
| A1 | 独立-1 | advisory | no | self-inflicted | session-source-asymmetry | accepted | session id の出所が、書く側は env、読む側は payload 優先で非対称。食い違えば発火しない側に倒れる |
| A2 | 独立-1 | advisory | no | inherited | fence-rewrite | accepted | setter の grep/sed は fence 内の記入例も書き換える（`:` 形は元から。`=` 形と新しい field に広がった） |
| A3 | 独立-1 | advisory | no | self-inflicted | entry-test | accepted | GDD_STEERING_DIR 無しの本番の入口（gdd_detect_active_steering 経由）で compact payload を通すテストが無い |
| A4 | 独立-1 | advisory | no | self-inflicted | test-hermeticity | accepted | 新しいテストは tmp_path が git 管理外であることを暗黙の前提にしている |
| A5 | 独立-1 | advisory | no | inherited | default-branch-set | accepted | 既定ブランチの集合が validate-worktree-command.py（main/master/develop）と割れている |
| A6 | 独立-1 | advisory | no | self-inflicted | review-template | accepted | 依頼の PR 本文の欄に「実測した事実」「方針メモ」の節が入っていた（判断には使われていない） |
| L6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の setter の説明と Validation が、旧#155 で足した「別の値が読めるときは追記せずに非 0」を反映していない。差分が届くのでこの PR で直した |
| L7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 印を書けなかった知らせと Known Limitations の列挙に CompactSessionId が無く、書き込み不可のときも行の形だけを案内する（L5 の後半と同じ）。差分が届くのでこの PR で直した |
| M3 | 独立-3 | medium | no | self-inflicted | session-source-asymmetry | accepted | 再掲（独立-1 A1）。書く側は env、読む側は payload 優先で session id を読む。実測で両 hook とも env と stdin の session_id は同じ値だった。食い違えば発火しない側に倒れる |
| M4 | 独立-3 | medium | no | self-inflicted | compact-test-wiring | deferred | 再掲（旧#154 / 独立-1 M1）。test_p0_p1_operational_hardening_contract の Task 切り詰めのテストが payload を渡さず、常に通る |
| L8 | 独立-3 | low | no | self-inflicted | payload-parse | accepted | 再掲（独立-1 L1）。source が空だと IFS のタブ畳み込みで欄が左にずれる。`{"session_id":"compact"}` のように source が無い payload では source の検査を通りうる。実 payload では起きない |
| L9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | lib 冒頭の「どの関数も非 0」が payload 読み取りに当たらない（再掲、独立-1 L5）。PausedAt を 3 つの印がそろったときだけ書くことが PR 本文に無い（PR 本文に追記）。Status 上書きの正本（gate-status-schema.md・state-schema.json）に上書きされない形の例外が無い（後続候補） |
| L10 | 独立-3 | low | no | self-inflicted | auto-cycle-cap | accepted | AutoCycleCount を書き戻せないとき、知らせを出さずに発火しない（PreCompact の知らせは Status / CompactSessionId / CompactSource だけ）。PR 本文の限界に書いた |
| L11 | 独立-3 | low | no | inherited | fence-rewrite | accepted | 再掲（独立-1 A2）。setter の置換が fence 内の記入例も書き換える |
| A7 | 独立-3 | advisory | no | inherited | default-branch-set | accepted | 再掲（独立-1 A5）。既定ブランチの集合が 3 通りある |
| A8 | 独立-3 | advisory | no | inherited | safe-resume-parity | accepted | compact の発火条件が Safe Resume と共有するのは既定ブランチだけ（ブランチ名と task 名の一致、gdd-dev.local.md の session_id は見ない）。条件を狭める向きで退行ではない。PR 本文の限界に書いた |
| H1 | PR後-1 | high | yes | self-inflicted | payload-parse | fixed | 独立-1 L1 / 独立-3 L8 の格上げ。source と session をタブ 1 本で戻すため、source が空だと先頭タブが IFS の空白として落ち、session が GDD_HOOK_SOURCE に入る。`{"session_id": "compact"}` で SessionStart(compact) でないのに発火する fail-open。「実 payload では起きない」で accepted にしていたが、ガードの fail-open として直した。2 行で渡す形に変え（5c342430）、再現テストを先に足した（31c02e89）。`{"source": "startup", "session_id": "compact"}` で source が優先されることも検査する |
| M5 | PR後-1 | medium | no | inherited | compact-test-wiring | deferred | 再掲（旧#154 / 独立-1 M1 / 独立-3 M4）。test_p0_p1_operational_hardening_contract の Task 切り詰めのテストが compact 経路に入らず、注入しなくても通る。本 PR の差分外 |
| F1 | 独立-4 | medium | no | inherited | compact-test-wiring | deferred | 再掲（旧#154 / PR後-1 M5 / 独立-1 M1 / 独立-3 M4）。test_p0_p1_operational_hardening_contract の Task 切り詰めのテストが compact 経路に入らない。「先に assertIn で発火を確かめてから切り詰めを見る」形にする案も 旧#154 に寄せる。本 PR の差分外 |
| L12 | 独立-4 | low | no | self-inflicted | session-source-asymmetry | accepted | 再掲（独立-1 A1 / 独立-3 M3）。書く側は env、読む側は payload 優先。reviewer 自身が gdd_stop_hook.py の _session_guard（env 由来の session_id と payload を等値比較して止める設計が実運用されている）を根拠に low とした。PR 本文の限界に追記した |
| L13 | 独立-4 | low | no | self-inflicted | default-branch-unknown | accepted | 3 条件のうち既定ブランチだけ、git が無い・unborn のとき通る側に倒れる。露出は「同じ session の compact が main で起きたとき」に限られる。PR 本文の限界に既出 |
| L14 | 独立-4 | low | no | inherited | fence-rewrite | accepted | 再掲（独立-1 A2 / 独立-3 L11）。setter が fence 内の記入例も書き換える。この差分で `=` 形・bullet 形・AutoCycleCount まで範囲が広がった点を追記として受け入れる |
| L15 | 独立-4 | low | no | inherited | schema-registration | accepted | 再掲（独立-1 L4）。CompactSessionId が state-schema.json の hook_owned_fields に無く、gate-status-schema.md / state-schema.json の書き手の名前が lib/compact-resume.sh に追随していない。後続候補 |
| L16 | 独立-4 | low | no | self-inflicted | test-power | accepted | stdin を閉じない検査の上限が 4.5 秒で、実装の `read -t 1` より緩い。`-t 4` に変えても通る。後続候補 |
| A9 | 独立-4 | advisory | no | self-inflicted | auto-cycle-cap | accepted | AutoCycleCount を書き戻せないとき `.gdd_is_running` が残り、次の compaction が無ければ残り続ける。PR 本文の限界に追記した |
| A10 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 再掲（独立-1 L5 / 独立-3 L9）。lib 冒頭の「どの関数も非 0 を返す」が、値を返す関数（空文字で判定不能を表す）と真偽を返す関数に当たらない |
| L17 | 独立-5 | low | no | inherited | compact-test-wiring | accepted | 再掲（旧#154 / 独立-1 M1 / 独立-3 M4 / 独立-4 F1）。test_p0_p1_operational_hardening_contract の Task 切り詰めのテストが payload と CompactSessionId を渡さず、発火しないまま通る。旧#154 で追跡 |
| L18 | 独立-5 | low | no | self-inflicted | test-power | accepted | 追加した test_compact_state_form_invariants.py は、compact 自動復帰を丸ごと無効化する変異でも 60 件が通る（I1・I3 は発火しないと抜け、I2 は fired<=3 なので 0 でも成立）。判別力は test_compact_resume_writer_and_source.py が担保。基準ケースが発火することを固定する 1 本を足すのは後続候補 |
| L19 | 独立-5 | low | no | inherited | fence-rewrite | accepted | 再掲（独立-1 A2 / 独立-3 L11 / 独立-4 L14）。setter の grep/sed が fence を見ず、fence 内の記入例も書き換える。AutoCycleCount と CompactSessionId で範囲が広がった。直すなら sed を fence 外に限る awk へ置き換える（呼び出しは pre-compact 4 箇所・session-start 1 箇所） |
| L20 | 独立-5 | low | no | self-inflicted | test-power | accepted | 新規 2 テストの _env が GDD_MAX_AUTO_CYCLES を host env から遮断せず、発火マーカーも 2 ファイルで割れている（gdd:compact-auto-resume は上限到達の警告にも含まれる）。開発者の env に GDD_MAX_AUTO_CYCLES=0 があると偽陽性で通りうる |
| L21 | 独立-5 | low | no | self-inflicted | payload-parse | accepted | read -t 1 の timeout 時に部分入力を変数へ保存するのは bash 4.2+ の挙動で、bash 3.2 では fd 0 を閉じない host のとき発火可否が変わる。向きは fail-closed（発火しない）。fd 0 を閉じない host を限界に足すのが候補 |
| A11 | 独立-5 | advisory | no | inherited | source-lib-unguarded | accepted | 両 hook の lib/compact-resume.sh の source が set -e 下で無防備。stop-failure hook が ADR-16 で受容済みの NEW-1 クラスを 2 行広げただけ。横断規約で扱う |
| A12 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 再掲（独立-1 L5 / 独立-3 L9 / 独立-4 A10）。lib 冒頭の「どの関数も非 0 を返す」が gdd_read_session_start_payload に当たらない |
| A13 | 独立-5 | advisory | no | self-inflicted | safe-resume-parity | accepted | 「Safe Resume と同じ述語」は述語だけで、ブランチの取得元は Safe Resume が worktree root、compact 側が steering ディレクトリ。GDD_STEERING_DIR が worktree 外を指すと別のブランチを見うる |
| A14 | 独立-5 | advisory | no | inherited | test-table-coverage | accepted | test_canonical_field_line_anchoring_contract.py の実装の表に、共有 setter（gdd_set_state_field）が入っていない。docstring の「7 実装」と path 定数の 6 本も食い違う（元から）。PreCompactRewriteAnchoringTests は挙動テストで退行なし |
| A15 | 独立-5 | advisory | no | self-inflicted | review-template | accepted | 依頼の PR 本文の目的・限界の節に、巡の ID を含む経緯（旧#155・PR後-1 H1・独立-3 L10 など）が入っていた。reviewer は未検証の主張として扱い、差分と実コードだけで判断した（判断には使われていない） |
| N1 | 独立-6 | low | no | self-inflicted | contract-test-form | fixed | `RESUME_PATHS` の PreCompact が `"Status"` だけを見る形だと、書き手 `gdd_set_state_field` が読み手 `gdd_extract_doc_field` に差し替わっても通る。呼び出しごと固定し、書き手を読み手へ差し替える変異で落ちることを確認した |
| N2 | 独立-6 | advisory | no | self-inflicted | doc-claim | fixed | 変更断片が検査対象を `"Status"` だけと書いていた（実際は `CompactSource` も）。N1 の修正に合わせて呼び出しの形に直した |
| P1 | 独立-7 | medium | no | self-inflicted | compact-test-wiring | re-reported | 独立-1 M1（旧#154）の再報告。`test_compact_resume_sanitizes_long_task_field` が payload と `CompactSessionId` を渡さず、発火しないまま通る。旧#153 後の手順 6 ① は `origin: this-diff` をこの PR で直す対象にするので、遡及の可否をユーザーに確認中 |
| P2 | 独立-7 | medium | no | self-inflicted | entry-test | re-reported | 独立-1 A3 の再報告（severity は advisory → medium で上がっており、再掲の条件を厳密には満たさない）。`GDD_STEERING_DIR` 無しの本番の入口（`gdd_detect_active_steering` 経由）で payload を通すテストが無い |
| P3 | 独立-7 | low | no | inherited | hook-owned-fields | re-reported | 独立-1 L4 の再報告。`references/state-field-tiers.md` の hook 所有の列挙が `Status` だけで、`CompactSessionId` が無い |
| P4 | 独立-7 | low | no | inherited | default-branch-set | re-reported | 独立-1 A5 の再報告。既定ブランチの集合が lint 2 本（`lint-resume-integrity.py` / `lint-worktree-provenance.py` は develop・development も含む）と割れている |
| P5 | 独立-7 | low | no | inherited | mark-consume-asymmetry | next-pr | SessionStart の `CompactSource` 削除 regex がバッククォート形に一致せず、印が消えずに残りうる。差分の外の消費側で、再発火には同じ session の次の compaction が要る |
| P6 | 独立-7 | low | no | inherited | fence-rewrite | re-reported | 独立-1 A2 の再報告（advisory → low）。setter の grep/sed が fence 内の記入例を 1 度書き換える（追記後は安定し、行は増え続けない） |
| P7 | 独立-7 | advisory | no | self-inflicted | field-name-validation | accepted | setter の `_field` が無検証で grep/sed のパターンに入る。現在の呼び出しは固定リテラル 5 種だけで到達しない |
| P8 | 独立-7 | advisory | no | self-inflicted | review-template | accepted | 依頼の PR 本文の欄に巡の名前と過去の指摘ラベルが入っていた（独立-1 A6 と同型。判断には使われていない） |
| Q1 | 独立-8 | high | yes | self-inflicted | mark-consume-asymmetry | fixed | P5 で手で広げた削除 regex でも、値が同じバッククォート全体形（`` `CompactSource: pre-compact` ``）は読む側が受理する形として残り、印が消えず次の compaction で再発火した（fail-open）。削除を setter（consumed へ書き換え＋読み直し）に寄せ、消し損じが「発火しない」側に倒れるよう修正した（`d8661d33`） |
| Q2 | 独立-8 | medium | no | self-inflicted | test-power | fixed | 既定ブランチへの develop/development 追加と削除 regex のバッククォート対応が、どちらもテストで固定されていなかった（3 値のまま・バッククォート値は manual のみ）。parametrize と `SOURCE_FORMS` を広げた |
| Q3 | 独立-8 | low | no | inherited | test-power | fixed | Task 512 文字切り詰めテストが `GDD_HOOK_STATE_DIR` を渡さず、実行のたびに開発者の実 `last-turn-failure.json` を読み書き・削除していた |
| Q4 | 独立-8 | advisory | no | self-inflicted | doc-claim | accepted | 既定ブランチ集合のコメント「lint と揃える」が、lint 側の正規化（lowercase・スラッシュ以降切り出し）を行わない旨を書いていない。綴り違いの実害例は示せず advisory |
| Q5 | 独立-8 | advisory | no | self-inflicted | fence-rewrite | fixed | 削除 regex に足した `[[:space:]]*` が読み手と逆方向にずれ、`CompactSource : pre-compact`（コロン前空白）という無害な行を余分に消していた。Q1 の setter 化で解消 |
| R1 | 独立-9 | medium | no | self-inflicted | test-power | fixed | 新設した `MARK_FORMS` テストの 2 回目の `SessionStart` 呼び出しは `.gdd_is_running` ロックで必ず失敗するため、印が `consumed` に書き換わっていなくても assert が通っていた（判別力 0） |
| R2 | 独立-9 | medium | no | self-inflicted | test-power | fixed | hook 所有 field の宣言を継続行（`state-field-tiers.md`）に書いたため、`test_always_high_scope_contract.py` の 1 行だけを見る機械検査が新 4 field を素通りしていた |
| R3 | 独立-9 | medium | no | self-inflicted | product | accepted | 値が同じバッククォート形の印では、PreCompact は成功・SessionStart は消費失敗で、どちらも利用者に知らせない。`AutoCycleCount` だけが上限まで増え続ける（独立-11 F1 として引き継がれ、書き手側検知は採らず限界開示に倒れた） |
| R4 | 独立-9 | low | no | self-inflicted | doc-claim | fixed | `state-field-tiers.md` の書き手・読み手の記述が、`CompactSource` を SessionStart も書く（消費）ことと `PausedAt` に読み手が無いことを反映していなかった |
| R5 | 独立-9 | low | no | self-inflicted | bookkeeping | fixed | `state-schema.json` の `hook_owned_fields` が新 4 field・新許容値 `consumed` と同期していなかった |
| R6 | 独立-9 | low | no | self-inflicted | doc-claim | fixed | changelog の Known Limitations が PR 本文と食い違い、fence 内書き換えの挙動記述（消費が削除でなく書き換えになった後の実装）とも合っていなかった |
| R7 | 独立-9 | low | no | inherited | test-power | fixed | 同ファイルの他の SessionStart 起動テスト（3〜4 本）が `GDD_HOOK_STATE_DIR` を隔離しないまま残っていた |
| R8 | 独立-9 | advisory | no | inherited | default-branch-set | accepted | 既定ブランチ集合が worktree guard・pre-PR gate と割れている（独立-1 A5 系の再掲） |
| R9 | 独立-9 | advisory | no | self-inflicted | review-template | accepted | テンプレート外の記述（呼び出し元候補の節）。判断には使っていない |
| S1 | 独立-10 | high | yes | self-inflicted | fail-open | fixed | `AutoCycleCount` の加算が消費より先に確定するため、値が同じバッククォート形の印では消費できず未発火のまま加算だけが進み、上限（既定 30）で原因と無関係な cap 警告だけが出て `AutoCycleCount` を戻す書き手も無い。加算を消費の後ろへ移した（`a5532573`） |
| S2 | 独立-10 | low | no | self-inflicted | bookkeeping | fixed | R5 の再掲（schema 同期） |
| S3 | 独立-10 | low | no | self-inflicted | test-power | fixed | `test_always_high_scope_contract.py` の SessionStart 側の pin が reader 呼び出しの形に固定されておらず、発火の門（`gdd_extract_doc_field`）を丸ごと消しても通っていた |
| S4 | 独立-10 | low | no | self-inflicted | test-power | fixed | `test_compact_state_form_invariants.py` の I1〜I3 は未発火で早期 return するため、1 件も発火しなくなっても 60 件全部 green になっていた。基準形の発火を固定する positive assert を足した |
| S5 | 独立-10 | low | no | self-inflicted | doc-claim | fixed | changelog の「60 通り」が形の数ではなくテスト件数（20 形 × 不変条件 3 本）だった |
| S6 | 独立-10 | low | no | self-inflicted | product | accepted | steering dir が git で解決できない（git 不在・commit 無し）ときは既定ブランチ判定を行わずに発火しうる。限界に開示済み |
| S7 | 独立-10 | low | no | inherited | default-branch-set | accepted | R8 の再掲 |
| S8 | 独立-10 | advisory | no | self-inflicted | review-template | accepted | テンプレート外の追送（差分貼り付けの訂正）。判断には使っていない |
| S9 | 独立-10 | advisory | no | self-inflicted | test-power | accepted | stdin の `read -t 1` のタイムアウト時の部分入力保持は bash 4.0+ の挙動で、bash 3.2 での実機確認はしていない（未確認）。向きは fail-closed |
| pm-12 | 方針メモ-2 | high | yes | self-inflicted | safety-net-4-count | fixed | 安全策 4 の発火。`PR後-1`・`独立-8`・`独立-10` で high を含む巡が合計 3 回に達した。Opus は選択肢 B（S1 の順序修正＋限界開示のみ、残りの ① は次の PR）を推奨したが、ユーザーは選択肢 A（① を全件このPRで 1 commit にまとめて修正）を選んだ。回数は戻らない（次に high・blocking を含む巡が出たら再発火する） |
| T1 | 独立-11 | medium | no | self-inflicted | product | accepted | R3/S1 修正の副作用として、印を消費できない形では compaction を何度繰り返しても PreCompact・SessionStart のどちらも表示を出さなくなった（上限警告も出ない）。書き手側で検知する案もあったが L1+ 安全策 2 のテストが要る規模のため採らず、沈黙を受け入れて限界に開示した |
| T2 | 独立-11 | medium | no | self-inflicted | doc-claim | fixed | 文書の「発火の後に consumed へ書き換える」は実装（発火判定の後・注入の前）と順序が逆で、書き換え後に `AutoCycleCount` の書き戻しに失敗すると `consumed` のまま発火しない窓があることも書いていなかった |
| T3 | 独立-11 | medium | no | self-inflicted | doc-claim | fixed | `HOOK_OWNED_OUT_OF_SCOPE` の命名・見出しコメントが、同ファイルが固定する常時 High 適用範囲 (b)（発火判定）と矛盾していた。`HOOK_OWNED_OUTSIDE_RESUME_FIELDS` に改名し、(b) には入る旨を明記した |
| T4 | 独立-11 | low | no | self-inflicted | test-power | fixed | 新設した `hook_owned_fields` の 4 entry を固定するテストが無く、丸ごと消しても全テスト green だった |
| T5 | 独立-11 | advisory | no | self-inflicted | test-power | accepted | `test_baseline_form_fires` は基準形 1 通りしか固定しない。他 19 形の空振りは同ディレクトリの別テストが実質的に担保している |
| T6 | 独立-11 | advisory | no | self-inflicted | doc-claim | fixed | changelog の「他のテスト 4 本も隔離する」が実際の本数と合っていなかった |
| U1 | 独立-12 | advisory | no | self-inflicted | review-template | accepted | テンプレート外の追送（差分貼り付けの訂正）。判断には使っていない |
| U2 | 独立-12 | medium | no | self-inflicted | test-power | fixed | Safe Resume 側の既定ブランチ集合が develop/development まで広がったが、Safe Resume 経路を通すテストは main だけで、3 値に戻す変異が生存した |
| U3 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | 「利用者から見える変化」が compact 自動復帰側しか書いておらず、Safe Resume の develop/development 拡張（compaction と無関係な通常起動でも挙動が変わる）が抜けていた |
| U4 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | PreCompact の session id 判定が env（`CLAUDE_CODE_SESSION_ID`）限定である旨が限界に無く、env が届かない runtime では警告なしに恒久的に発火しなくなる |
| U5 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | `test_canonical_field_line_anchoring_contract.py` の docstring が、書き手の実装が `lib/compact-resume.sh` の `gdd_set_state_field` に移った実体と食い違っていた |
| U6 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | python3 も python も無い環境では、印を書けなかった知らせ（systemMessage）自体も出ないことが限界に書かれていなかった |
| U7 | 独立-12 | low | no | self-inflicted | bookkeeping | fixed | changelog の隔離本数の記述と Affected Files の二重掲載が実態と合っていなかった |
| U8 | 独立-12 | advisory | no | self-inflicted | style | accepted | setter の `_field` が無検証で sed パターンに展開されるが、現在の呼び出し元は固定リテラル 5 種のみで到達しない（YAGNI） |
| V1 | 独立-13 | medium | no | inherited | default-branch-set | out-of-diff | 既定ブランチ名の列挙が plugin 内で 4 種（compact 側 5 値・lint 2 本 5 値・root branch guard 3 値・pre-PR gate 候補 7 種）に割れている。差分の外（`validate-worktree-command.py`）で、実データに該当（既定ブランチが trunk/development の repo）が無いため、この PR には入れない |
| V2 | 独立-13 | low | no | self-inflicted | test-power | fixed | develop/development の Safe Resume 陽性テストが実 `HOME` を隔離しておらず、開発者の `~/.claude/gdd-post-merge-continuation.json` を読み書き・削除しうる形だった |
| V3 | 独立-13 | low | no | inherited | test-power | fixed | 既定ブランチ側の陰性ケース（HEAD があり既定ブランチでない task branch）が無く、集合を全ブランチへ広げる変異が Safe Resume 側のどのテストでも生存していた |
| V4 | 独立-13 | low | no | self-inflicted | doc-claim | fixed | changelog の Affected Files と「他のテスト 5 本」の本数記述が、新設した develop/development テストに追随していなかった |
| V5 | 独立-13 | low | no | self-inflicted | doc-claim | fixed | 限界の「python3 が無い環境では知らせも出ない」は実装より広い断定だった（PreCompact の知らせは python フォールバックがある。発火判定側は python3 固定のまま） |
| V6 | 独立-13 | low | no | inherited | doc-claim | fixed | `test_canonical_field_line_anchoring_contract.py` の「7 実装すべてを表で検査」が、実体（表で 5 実装、書き手 2 つは PreCompact の実起動 2 件で代表）と食い違っていた |
| V7 | 独立-13 | advisory | no | self-inflicted | review-template | accepted | テンプレート外の追送（差分貼り付けの訂正）。判断には使っていない |
| W1 | 独立-14 | medium | no | self-inflicted | test-power | fixed | develop/development の Safe Resume 陽性テストのうち、独立-13 の env 隔離ヘルパーが無い 4 本（同ファイルの他の SessionStart 起動テスト）が実 HOME・post-merge seed 系 env を隔離しておらず、開発者の実ファイルに触れうる形だった。3 本は同じ隔離を追加し、1 本（main 既定ブランチのケース）は隔離済みの共通ヘルパーへ差し替えた |
| W2 | 独立-14 | medium | no | inherited | test-power | next-pr | test_session_start_invalid_seed_json_noop が GDD_POST_MERGE_SEED_FILE を渡さないため、不正 JSON のフィクスチャが実際には読まれず、seed 解析コードの正しさを検査できていない（差分の外・同じ test-power クラスタの話題）。この PR の直後に次の PR で直す |
| W3 | 独立-14 | low | no | self-inflicted | doc-claim | fixed | 変更断片が「Safe Resume 側の入口から gdd_is_default_branch の 5 値を固定する」と過大に書いていたが、実際にその入口から固定されるのは main/develop/development の 3 値で、master/trunk は compact 側の入口（test_compact_resume_writer_and_source.py）からのみ固定されている。文言を実体に合わせた |
| W4 | 独立-14 | medium | no | inherited | product | out-of-diff | lib/post_merge_continuation.py（書き手）と run-user-prompt-submit-hook.sh:38（読み手）はプロジェクトルート相対のパスを使うが、run-session-start-hook.sh:278 の既定値は ${HOME}/.claude/gdd-post-merge-continuation.json にフォールバックしており、GDD_POST_MERGE_SEED_FILE を明示しない実運用では SessionStart 側の post-merge-continuation 経路が発火しない可能性がある。差分の外（旧#141/#142 の対象である state.md の compact 系フィールドとは別のファイル・別の書き手読み手の組）で、実データでの該当件数は未確認のため、この PR では対応しない（要追加調査） |
| X1 | 独立-15 | advisory | no | self-inflicted | review-template | accepted | 呼び出しテンプレートの3欄をファイル参照（4回のRead呼び出し手順を欄外に付記）で渡した。reviewer は指示どおり全文を読み切ったことを確認した上でレビューを実施したが、次回は git diff の出力そのものを直接貼るべきと指摘した。判断には影響していない |
| X2 | 独立-15 | medium | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容が「test_p0_p1_operational_hardening_contract.py は本PRの差分外なので#154に回した」と書いているが、実際は同ファイルが差分に入っており（CompactSessionId 追加・compact 経路4本目の発火 assert を含む）、変更断片の記述と矛盾していた。差分に入っているのに変更内容に現れないファイルが他に4つあった。PR 本文を直接修正した（repo へのコミットを伴わないため、この巡を無効にしない） |
| X3 | 独立-15 | medium | no | self-inflicted | doc-claim | accepted | CompactSource の消費方式を「行削除」から「setter でconsumedへ書き換え」に変えた、利用者から最も見える変更が PR 本文の変更内容・限界のどちらにも書かれていなかった（変更断片には記載済み）。fence 内の記入例が書き換わる限界も PR 本文の限界節に無かった。PR 本文を直接修正した |
| X4 | 独立-15 | medium | no | self-inflicted | product | next-pr | gdd_is_default_branch は完全一致判定だが、「揃える」と名指す lint 2 本（lint-resume-integrity.py・lint-worktree-provenance.py）は判定前に大文字小文字正規化と `/` 区切りの正規化を行っており、照合規則が非対称。`Develop`/`Main` 等の大文字小文字違いのブランチ名では lint が既定ブランチと警告するのに hook 側は既定ブランチと見なさない。実害は限定的（#142本体の害はsource+session一致の2条件で閉じたまま）で blocking ではないため、修正（大文字小文字正規化の追加とテスト）はコード変更と再レビューを要する。最終全差分巡の繰り返し1回の枠を使い切ったため、次のPRで直す |
| X5 | 独立-15 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「run-session-start-hook.sh（行数は−1）」が実際の−2と食い違い、「1軸ずつ動かした60通り」が実際は20通り(計60件のtest item)と食い違っていた。変更断片は正しく書けていた。PR 本文を直接修正した |
| X6 | 独立-15 | low | no | self-inflicted | bookkeeping | next-pr | gate-status-schema.md § Status は「機械可読な定義はstate-schema.json § hook_owned_fieldsと同期する」と宣言しているが、この差分で state-schema.json / state-field-tiers.md に足した CompactSessionId 等4 fieldに追随していない。修正はドキュメントファイルの変更を伴い再レビューを要するため、次のPRで直す |
| X7 | 独立-15 | low | no | self-inflicted | doc-claim | next-pr | test_canonical_field_line_anchoring_contract.py の docstring が「SessionStart側のsetterの呼び出しはtest_compact_state_form_invariants.pyが持つ」と書いているが、そのテストが持つのはI1〜I3の発火不変条件で、このファイルの主題（入れ子bullet・インデント行を書き換えない）は検査していない。修正はテストファイルの変更を伴い再レビューを要するため、次のPRで直す |
| X8 | 独立-15 | advisory | no | inherited | product | accepted | 2 hookのlib/compact-resume.shのsourceがset -e下で無防備。直上のlib/detect-steering.shのsourceが既に持つ既存の露出と同型で、差分はそれを1行広げただけ。横断規約として別PRで扱うのが筋 |
| Y1 | PR後-2 | high | no | self-inflicted | mark-consume-asymmetry | re-reported | 独立-8 Q1（fail-open、fixed）の再掲。reviewerがレビューしたtip `ef80614d` は d8661d33（Q1の修正）未反映で、バッククォート形のCompactSourceが消費できず再発火する問題が実際に残っていた。現在の tip（4efc0ebb）で同じ再現手順（PreCompact→SessionStart(compact)を2回）を実プロセスで確認したところ、2回ともgdd:compact-auto-resumeは発火せず、AutoCycleCountも0のまま変わらなかった（fail-closed）。GitHubのinline commentに再現結果とd8661d33を明示して返信した |
| Y2 | PR後-2 | medium | no | self-inflicted | compact-test-wiring | re-reported | 旧#154 / 独立-7 P1（fixed, commit 2a1b8e6e）の再掲。reviewerがレビューしたtip `ef80614d` は2a1b8e6e（P1の修正）未反映だった。現在のtipのtest_compact_resume_sanitizes_long_task_fieldはCompactSessionIdとcompact payloadを渡し、切り詰めを見る前にgdd:compact-auto-resumeの発火をassertしている。PR本文のClosesリストに#154を追加し、GitHubのinline commentに解決済みである旨を返信した |
| Y3 | PR後-2 | low | no | self-inflicted | mark-consume-asymmetry | next-pr | reviewerの指摘を精査する過程で新規に見つけた非対称性。gdd_set_state_fieldは、書き込み対象のfieldがバッククォート形かつ値が既に書き込み先と一致する場合、置換せずに読み直しだけ一致して0を返す（false success）。PreCompact側（Status/CompactSessionId/CompactSourceの書き込み）でこれが起きると、行は正規化されないまま警告も出ずに成功扱いになる。consume側（SessionStartのconsumed書き込み）は同じ理由で非0を返すため実際の発火には至らず（fail-closedを維持）実害は「知らせが出ない」ことに限られるが、テストカバレッジの穴でもある。修正はtest_compact_state_form_invariants.pyへのケース追加とgdd_set_state_field自体の検討を要し、独立-15が最終全差分巡の繰り返し枠を使い切った後の発見のため、次のPRで直す |
| Z1 | PR後-3 | - | - | - | - | - | なし |
