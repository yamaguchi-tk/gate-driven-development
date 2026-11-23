---
lane: L1+
pr: 旧#145
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user | - | 1 | 3 | 0 | 2026-09-18T22:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 71315f046ee6efee81cfb271a33bd5daa7a4a3d8 | 1 | 1 | 1 | 2026-09-18T23:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 全差分, model: opus | 89b3dcd731a5e93769539ec4e72d0d534d3139d1 | 4 | 1 | 4 | 2026-09-19T00:30+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user | - | 0 | 0 | 0 | 2026-09-19T01:20+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | 204399c9a4da0fd2a37923a5efc5c62a63f8ced1 | 4 | 0 | 4 | 2026-09-19T02:40+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user | - | 0 | 0 | 0 | 2026-09-19T03:40+09:00 |
| 独立-4 | light-lane-independent-reviewer, 全差分, model: opus | 25d5c58c2cbb227a566a00f11edbc877cc0e2e35 | 0 | 0 | 0 | 2026-09-19T05:10+09:00 |
| 方針メモ-3 | Fable アドバイザリ (general-purpose, model: fable) + user | - | 0 | 0 | 0 | 2026-09-19T07:30+09:00 |
| PR後-1 | Cursor (Grok 4.6), 全差分 | d6bed292 | 0 | 0 | 0 | 2026-09-19T08:30+09:00 |
| 独立-5 | light-lane-independent-reviewer, 全差分, model: opus | f319be08be7431378134ecae1fc73df2d1a04d83 | 1 | 0 | 1 | 2026-09-19T22:16+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user | - | 0 | 0 | 0 | 2026-09-19T22:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | high | no | inherited | route-key-side-fail-open | fixed | Check 3 は Route In Progress の行が読めなければ通す作りで、キーの側を壊す 6 形（ZWSP・NBSP・`-` 直後の ZWSP・全角コロン・字下げ・先頭 BOM）は今も allow。開いた入力なので塞がず、限界として PR 本文と断片に開示（ユーザー承認） |
| P2 | 方針メモ | medium | no | self-inflicted | hook-literal-contract | fixed | Check 3 を lib へ移すと tests/checks/hooks.sh が gdd_stop_hook.py に要求する `Route In Progress` の文字列が消える。呼び出し箇所のコメントで残した |
| P3 | 方針メモ | medium | no | self-inflicted | limits-disclosure | fixed | 閉じない残りに、Check 3 の前提（agent 自身が書く・行が無い＝通す）と state.md 不在時の no-op を足す |
| P4 | 方針メモ | medium | no | self-inflicted | recovery-hint-wording | fixed | 共通の回復ヒント「削除後の tasklist で改めて検査されます」は state.md では誤案内。両ファイルを指す文にした |
| A1 | 独立-1 | high | yes | inherited | route-value-unreadable | fixed | Check 3 はキー行があっても値が読めないと route なしとして通す。行中の単独 CR（read_text が LF に変える）、区切り文字の LF への置き換え、値が次の行にある形、注記だけの行で、non-none の route を抱えたまま done が通る |
| A2 | 独立-1 | medium | no | inherited | handoff-summary-resub-escape | fixed | handoff_summary.apply_summary の re.sub が置換文字列の `\f` / `\v` などを制御文字に変え、hook 自身が state.md に U+000C / U+000B を書いて新しい検査が done を止めうる（テストは truncate_summary だけを見ている） |
| A3 | 独立-1 | low | no | self-inflicted | hook-literal-contract | accepted | tests/checks/hooks.sh の `Route In Progress` の pin が hook 内のコメントでしか満たされず、配線の有無を判別しない |
| A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | done_guard.py の module docstring「挙動は変えていない」が、挙動を変えた Check 3 を含む今の内容と合わない |
| A5 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | `assertIn("state.md", hints)` は固定文言だけで満たされ、判別しない |
| B1 | 独立-2 | high | yes | self-inflicted | route-value-unreadable | fixed | 前にある読める行（`none`）が後ろの読めない行（値が次の行・注記だけ・単独 CR・LF 置き換え）を隠し、done が通る。A1 の判定は「ファイル全体で読める値が 1 つでもあるか」を見ており、現在値を決める最後のキー行を見ていない |
| B2 | 独立-2 | high | yes | self-inflicted | route-key-acceptance-asymmetry | fixed | 新しいキー判定が write guard の正本（state_fields.state_field_pattern）より狭い。`- Route In Progress : x`、`` - `Route In Progress`: x ``、二重バッククォートは write guard では field ありだが done guard では素通り |
| B3 | 独立-2 | high | yes | inherited | route-key-side-fail-open | fixed | キーの側が崩れた形（全角コロン・字下げ・太字・`*` 箇条書き・ZWSP/NBSP・先頭 BOM）は今も allow。開示済みでも降格しない（P1 と同じ） |
| B4 | 独立-2 | high | yes | inherited | handoff-summary-resub-escape | fixed | apply_summary の re.sub が要約中の 2 文字の `\n` を本物の改行にし、同じ Stop 呼び出しの中で Check 3 の直前に `Route In Progress: none` 行を state.md に足せる（A2 の fail-open 側） |
| B5 | 独立-2 | medium | no | self-inflicted | route-unreadable-hint | fixed | 「値を読めない」block に tasklist.md と Verification を直せという既定の推奨アクションが付く |
| B6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | done_guard.py / done_block_message.py の docstring が変更に追従していない |
| B7 | 独立-2 | low | no | self-inflicted | hook-literal-contract | accepted | hooks.sh の `Route In Progress` の pin がコメントだけで満たされる（A3 と同じ） |
| B8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required に「値を読めない」block が無く、件数の母数（264 / 548）が揃っていない |
| B9 | 独立-2 | advisory | no | inherited | doc-claim | deferred | skills の等号形とテンプレートのコロン形が食い違い、複数の route 行が通常の運用で生じる |
| C1 | 方針メモ-1 | advisory | no | inherited | safety-4-hitl | fixed | 安全策 4 の発火（route-value-unreadable が 2 巡）で HITL。Opus は B1・B2 だけ直す案、ユーザーは Fable の意見を求めた。Fable は全部直す案（キー行の正本を write guard と 1 つにし最後のキー行を見る、正準キー行が無ければ block に既定を反転、apply_summary を lambda 置換、専用の回復ヒント）。反転の影響は fixture 除外の state.md 422 件中キー行なし 165 件・非 terminal 78 件（古い worktree の steering）（後日訂正: 方針メモ-3 の実走で allow → block は 0 件）。ユーザーが Fable 案で全部直すことを選択 |
| D1 | 独立-3 | high | yes | inherited | route-mixed-separator | fixed | コロン形の `none` の後に等号形の route を書くと、最後のキー行は読めるが select がコロン形を優先して `none` を採り done が通る（B9 の実害側。混在は実測 2 件） |
| D2 | 独立-3 | high | yes | inherited | route-key-side-fail-open | deferred | 正準キー行の後ろにある崩れたキー行（太字・`*`・全角コロン・字下げ・ZWSP）は無視され、前の `none` で done が通る。「崩れた形はすべて畳まれる」の記述は正準キー行が無いときに限られる |
| D3 | 独立-3 | high | yes | inherited | handoff-summary-resub-escape | fixed | apply_summary の置換パターン `Last Handoff Summary=.*` が行区切り文字と同じ物理行の後続（route 行）まで上書きし、Check 3 より前に走るため U+2028 と route 行が消えて done が通る |
| D4 | 独立-3 | high | yes | inherited | state-fence-unclosed | fixed | state.md の閉じていない fence 内の記入例 `none` が最後のキー行・select の値に採られ done が通る（tasklist.md 側は未閉 fence を block） |
| D5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | テスト docstring「キーの側を壊す形はここでは閉じない」が同じファイルの block テストと矛盾 |
| D6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | done_guard.py docstring・tasklist_parse の「1 箇所に集約」・state-schema.json・state-field-tiers.md が Check 3 のキー行判定に追従していない |
| D7 | 独立-3 | low | no | self-inflicted | test-power | accepted | キー集合の包含テストは has_state_field_line が常に False でも通る |
| D8 | 独立-3 | advisory | no | self-inflicted | review-template | accepted | PR 本文の欄にテンプレート外の節（実データ・User Action Required）と経緯（HITL の選択）が入っていた |
| D9 | 独立-3 | advisory | no | self-inflicted | review-template | accepted | 差分の欄で `\u2028` などのエスケープが実文字に化けていた（Read の表示経由の転記） |
| D10 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実測件数に測定コマンドと対象範囲が無い |
| C2 | 方針メモ-2 | advisory | no | inherited | safety-4-hitl | fixed | 安全策 4 の発火（high か blocking を含む巡が 独立-1・2・3 の 3 回）で HITL。D1〜D4 の形は実データ（fixture 除外の state.md 422 件）で 0 件。Opus と Fable はともに B'（D1・D3・D4 を Check 3 の中だけで直し、共有 reader は変えない。D2 は開いた入力なので限界として開示）を推奨した。Fable の追加点は、D4 は未閉 fence を一律 block にすること、persist 側で要約から 8 文字を除くこと（既存の truncate_summary が splitlines で LF に畳むため満たし済み）、「受理集合は write guard と同じ」の文言を直すこと。ユーザーは Fable 版 B' を選択した。独立-4 の打ち切り条件も事前に合意した: high・blocking が route-key-side-fail-open クラスタの inherited だけなら限界に追記して止める（このクラスタに限って「止める」を適用する）。それ以外の high が出たら 1 回だけ直して独立-5 を回し、そこでも出たら HITL に戻す |
| E1 | 独立-4 | low | no | inherited | test-power | accepted | tests/_stop_hook_test_base.py の persist の複製が旧 re.sub のままで、本番の apply_summary が戻っても test_stop_hook_unit の handoff テストは落ちない（本番関数は新テストが固定） |
| E2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | references/state-field-tiers.md の Tier 1 の検査箇所に done guard Check 3 と tasklist_parse のキー行判定が無い |
| E3 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | done_guard.py / handoff_summary.py の「挙動は変えていない」、done_block_message.py の変更の列挙、テスト docstring の「キーの側を壊す形は閉じない」が今の挙動と合わない |
| E4 | 独立-4 | advisory | no | self-inflicted | test-power | accepted | test_verification_block_message_contract の assertIn("state.md", hints) と hooks.sh の Route In Progress の pin が判別しない（A3・A5・B7 と同じ） |
| E5 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 行区切りの案内文言の変更と、行が無い・読めない block に「なぜ」が付くことが PR 本文に無い |
| E6 | 独立-4 | advisory | no | self-inflicted | bookkeeping | fixed | 既定の block 条件の変更を type: patch にしているが、VERSIONING.md の :68・:92 は Breaking 扱いを示す（:178 のフローは User Action Required の記載で足りるとする） |
| E7 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | 実測件数（422 / 165 / 78 / 0）に対象ディレクトリと集計コマンドが無い（D10 と同じ） |
| E8 | 独立-4 | advisory | no | self-inflicted | product | accepted | Route In Progress の残存・読めない block が、対象の行番号を示さない |
| E9 | 独立-4 | advisory | no | self-inflicted | review-independence | accepted | reviewer がコンテキスト圧縮後に PR 本文の文言確認のため親セッションの transcript を Grep した。判定には prompt と実コードだけを使ったと申告 |
| C3 | 方針メモ-3 | advisory | no | self-inflicted | safety-4-hitl | fixed | マージ前の判断（E6 の type と、キー行なし block の影響）について、ユーザーが影響の詳しい説明と Fable の意見を求めた。main と本ブランチで Stop hook を実走した結果、キー行なし・非 terminal は 120 ファイル（重複除き 32 steering、2026-04〜07 の旧形式）で、すべて main でも既に block されており、allow → block は 0 件だった（以前の「78 件」は粗い集計）。Fable の推奨は type: breaking（VERSIONING.md :66・:92 と過去 3 例に合わせる。版数は 0.45.0 で変わらない）と、反転を受け入れること（detect-steering.sh と state-machine.md は既に fail-closed）。ユーザーは両方を選択した。断片の変更で独立-4 は無効になり、独立-5 を回す |
| F1 | PR後-1 | advisory | no | self-inflicted | bookkeeping | fixed | マージ前確認: 全量テストと validate を今の tip で再確認する、GitHub checks が無い（CI 無し運用の前提を明記する）、キー行の無い旧 steering（本文の「78 件」）の扱い。最終 tip で全量と validate を再実行し、CI 無しを PR 本文に書き、78 件は実走で allow → block 0 件と訂正した（C3） |
| G1 | 独立-5 | high | yes | inherited | precompact-sed-line-model | accepted | PreCompact hook（run-pre-compact-hook.sh:48・55・62）の sed の `.*` が、行の途中の単独 CR と 8 文字を越えて物理行末まで消す。`- Status: running<CR or U+2028>- Route In Progress: <route>` の route 行が消え、前の `none` だけが残って Check 3 が allow（実 sed で再現。実データ 260 ファイルで該当 0）。D3（apply_summary）と同じ型。方針メモ-4 で止め、限界として PR 本文に開示し後続候補に列挙（Issue は作らない） |
| G2 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | route_in_progress_key_lines の docstring「block 側に倒れる」は、小文字の後置 `none` で allow 側にも働く（reader と同じで退行ではない） |
| G3 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | テスト docstring と done_guard のコメントが反転前の前提（キー崩れは閉じない、LF 置換で素通り）のまま（D5・E3 と同じ） |
| G4 | 独立-5 | low | no | self-inflicted | test-power | accepted | 包含テストに陽性対照が無い（D7 と同じ） |
| G5 | 独立-5 | low | no | self-inflicted | test-power | accepted | hooks.sh の Route In Progress の pin がコメントだけで満たされる（A3・B7・E4 と同じ） |
| G6 | 独立-5 | advisory | no | self-inflicted | test-power | accepted | _stop_hook_test_base.py の persist の複製が旧 re.sub のまま（E1 と同じ） |
| G7 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | 実測（0 件・120 ファイル）に再現手順と比べた sha が無い（D10・E7 と同じ） |
| C4 | 方針メモ-4 | advisory | no | self-inflicted | safety-4-hitl | fixed | 独立-5 の G1（high・pre-existing）で安全策 4 が発火。実測は再現あり・実データ 260 件中 0。Opus・Fable ともに (B) 止める（暫定運用の ②：Check 3 の呼び出し経路の外にある別 hook の書き手）。ユーザーは (B) を選び、限界は PR 本文だけに書き（断片を変えて独立-5 を無効にしない）、行き先は Issue ではなく後続候補にした。以後この PR では安全策 4 を発火させない |
