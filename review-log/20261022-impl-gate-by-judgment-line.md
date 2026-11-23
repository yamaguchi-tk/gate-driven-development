---
lane: L1+
pr: 567
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 6721efe9 | 0 | 8 | 0 | 2026-10-22 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f7a88f0f | 2 | 11 | 3 | 2026-10-22 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | f7a88f0f | 0 | 0 | 0 | 2026-10-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | eae699e0 | 1 | 3 | 1 | 2026-10-22 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | eae699e0 | 0 | 0 | 0 | 2026-10-22 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 059375be | 0 | 0 | 0 | 2026-10-22 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e35e5450 | 2 | 2 | 2 | 2026-10-22 |
| 方針メモ-4 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | e35e5450 | 0 | 0 | 0 | 2026-10-22 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 25479555 | 1 | 7 | 2 | 2026-10-23 |
| 方針メモ-5 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | 25479555 | 0 | 0 | 0 | 2026-10-23 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 89566063 | 1 | 2 | 1 | 2026-10-23 |
| 方針メモ-6 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 89566063 | 0 | 0 | 0 | 2026-10-23 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 339f587e | 1 | 0 | 1 | 2026-10-23 |
| 方針メモ-7 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | 339f587e | 0 | 0 | 0 | 2026-10-23 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 385edf7e | 0 | 1 | 0 | 2026-10-23 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | medium | no | self-inflicted | declaration-accuracy | accepted | §7a.4 の「外の実害 0」は実際の diff で分けた数で、計画の時点の宣言の精度は未測。外す経路でも gate が Step 1 の変更ファイルと diff を線に照らし、触れる・判定できないときは欄を `yes` に上げて通常の review に進む。`no` に下げてよいのは task-breakdown だけ（Opus・Fable） |
| pm-2 | 方針メモ | medium | no | self-inflicted | fail-open | accepted | Express は completion-check の後ろ盾が無い。外す・外さないの固定行を出す script が Task Size も読み、`quick (express)`・読めないときは run を出す（Fable）。Current Task の task の見出しが崩れて宣言の無い task が前の `no` の block に混ざる形は、Current Task の `### ` 見出しが task として読めなければ run にする（Opus） |
| pm-3 | 方針メモ | medium | no | self-inflicted | rerun-loop | accepted | completion で線に触れると分かった task を再 gate するとき、欄が `no` のままだとまた外れる。Current Task に戻す書き込みで欄を `yes` にする（Opus） |
| pm-4 | 方針メモ | medium | no | self-inflicted | predicate-split | accepted | 草案の述語が 2 通り（`no` の行が 1 本ある／`Judgment Change` の行がすべて `no`）。後者の 1 関数を、gate の固定行・completion の受理・write guard で共有する（Opus） |
| pm-5 | 方針メモ | medium | no | self-inflicted | wiring | accepted | 外す経路で State Machine Impact block を読まないと、Routing 提案（human check）と Reviewer Lineage 追加提案を素通りする。`なし` 以外なら review を回す（Opus） |
| pm-6 | 方針メモ | medium | no | self-inflicted | wiring | accepted | 同じ記録を読む別の箇所が未対応：completion Step 2a の judgment・conditional reviewer の確認、Checklist E (ii) の `Reviewed by:` の観測、Step 11・Guardrails の「implementation-reviewer は必ず selected」、Template の State Update Contract、state-machine.md の差し戻し理由の表（Opus・Fable） |
| pm-7 | 方針メモ | medium | no | self-inflicted | rule-conflict | accepted | `references/reviewer-selection.md` の非 waivable 上書き条項 2（`hooks/`・`scripts/` などのパス）は、review を外すと空文になる。条項は「review を回すときの reviewer の選び方」に限ると書き、回すかどうかは線で決める（Fable の推奨 (ii)）。ユーザーに確認する |
| pm-8 | 方針メモ | medium | no | self-inflicted | request-drift | accepted | 確認待ち: (1) 遷移表は変えず gate の中で review を外す案 A、(2) 依頼が範囲外とした completion-check の SKILL と reviewer を触る（旧#564 とは別の hunk）、(3) Express は外さない（依頼より狭い）、(4) 非 waivable 条項の扱い、(5) skill 本文の合計・references の行予算と standard の token 予算を、増やした分だけ上げる。推奨で進め、PR 本文に問いを書く |
| F1 | 独立-1 | high | yes | self-inflicted | review-skip-history | fixed | 列挙: 設計: 変える（外す判定が今の宣言だけを見て、gate 単位の差し戻しの履歴を見ない）。並列の batch で差し戻された `no` の task と Express からの昇格の再 gate が review なしで approved になる。方針メモ-1 で (a)。Current Task に `Gate Rounds` の行が 1 本でもあれば run、`quick (express → standard)` を外してよい集合から抜いた。テストを先に書いて失敗を確かめた commit: fdf8090a |
| F2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（読めた task だけを block にし、読めない形を 1 つずつ run に倒す拒否リスト）。最初の task より前の行・別の書き方の宣言・崩れた task の混入が捨てられて skip になる。方針メモ-1 で (a)：最初の task より前は空行だけ、`Reviewed by` 以外で判定の語を含む行はちょうど 1 本の `- Judgment Change: no`、1 本だけの欄の重なりで run、Step 1e で task 名を突き合わせる。事故の形は実データ 21 行、誤 run は欄の重なり 2/175 block commit: fdf8090a |
| F3 | 独立-1 | medium | yes | self-inflicted | review-skip-history | fixed | 設計: 変える（F1 と同じ決定）。外すと Step 8a（remediation ADR ≥2）を評価しない。差し戻し 2 回は Gate Rounds ≥1 なので run になる。Step 1e に 8a を飛ばさないと書いた commit: fdf8090a |
| F4 | 独立-1 | medium | no | self-inflicted | completion-reopen | accepted | 観点 11 の High の扱いが Part A の Step 2a にあり、Part C の Step 14・16 に欄を yes に上げる手順が無い。再オープンした task が `no` のまま戻るか、remediation task で Reviewed by が残る |
| F5 | 独立-1 | medium | no | self-inflicted | gate-unit-diff | accepted | Step 1e と観点 11 が見る差分（branch 全体か gate 単位か）を決めていない。前の task が線に触れると後の task も全部 review に回る |
| F6 | 独立-1 | medium | no | self-inflicted | wiring | accepted | impl-gate-context.py の `_handoff` は block を持つ最新 1 ファイルだけを出すので、Gate Batch で前の task の SMI block（ADR 起票: 要 など）が落ちる |
| F7 | 独立-1 | medium | no | self-inflicted | stage-a-skip | accepted | review を外すと Stage A（Human Recheck Boundary・Approved Direction・Tech Stack への接触）も飛ぶ |
| F8 | 独立-1 | medium | no | self-inflicted | deny-message | accepted | skipped の記録を落とす書き込みの deny 文が「implementation-reviewer が消えた」と言い、従うと走っていない review の記録ができる |
| F9 | 独立-1 | medium | no | self-inflicted | trust-boundary | accepted | `no` を書けるのは task-breakdown だけという規定は散文だけで、write guard は yes→no の書き換えを止めない |
| F10 | 独立-1 | medium | no | self-inflicted | doc-drift | accepted | 観点 11 の線の言い直しが正本より狭い。SKILL 24・39 行、reviewer-selection.md:97、task-sizing.md:96、state-machine.md:213・532、completion-check 46 行、state-field-tiers.md:18 が外す経路・新しい値を書いていない |
| F11 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 依頼が範囲外とした completion-check の SKILL・reviewer・機械検査を変えた（pm-8 (2) と同じ問い） |
| F12 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: Express（と、F1 の修正で Express からの昇格も）を線によらず review に回す。依頼より狭い。Opus は昇格を集合に残し task-breakdown の規則で閉じる案 |
| F13 | 独立-1 | medium | no | self-inflicted | test-power | accepted | `_JUDGMENT_KEY_RE` が読む形を固定するテストが無い（F2 の修正で述語を替え、別の書き方の行と 2 本目の行のテストを足した） |
| F14 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 確認待ち: 非 waivable 上書き条項 2（hooks・scripts のパス）が impl-gating で効かなくなる（pm-7・pm-8 (4) と同じ問い） |
| F15 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 確認待ち: `no` を書けるのを task-breakdown だけにしたので、refactor-planning などが足した task は線の外でも review に回る。Opus は refactor-planning にも書かせる案、Fable はこのまま |
| F16 | 独立-1 | low | no | self-inflicted | test-power | accepted | write guard と check-completion-mechanical.py の入口から skipped を通すテストが無い |
| F17 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 文書の「quick (express) でなく」とコードの許可集合（値ちょうど）が食い違う（F1 の修正で文書に値を書いた） |
| F18 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「Round が約 46% 減る」が何を数えた値か・gate runner の 1 回は残ることを書いていない |
| F19 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の挙動の変化に size の deny 文の案内と (ii) の除外が無く、「write guard に新しい block は足していない」が 13 行目と食い違って読める |
| F20 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Changed・Affected Files に lint-scripts-functional.sh の上限の引き上げが無い |
| F21 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | review を外したときの reviewer status の値を決めていない。最後の task を外すと Review Status が前の値のまま completion-check に進む |
| M1 | 方針メモ-1 | advisory | no | self-inflicted | policy | accepted | F1・F2 の `閉じ方: 列挙` の相談。入力者は LLM、見出しでない task の書き方が実データ 21 行あり (a)。割れた点：Gate Rounds は Fable の「行があれば run」（template に 0 は無い）。Express 昇格は Fable の「集合から抜く」を採り、Opus の「集合に残し、差し戻した commit を残す作り直しでは `no` を書かない」の文も § Judgment Change に足し、F12 の問いに両案を載せる。(c) 欄の重なりは Opus の求めで先に数え 2/175 block（同じ archive の 1 本）で入れた。F15 は main・Fable の案で進め、Opus の案を問いに載せる |
| G1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（方針メモ-3。外すかを Current Task の文で組み立てた task の集合ではなく、gate 単位の git の差分が no の task の Files の宣言に収まるかで決める。起点は Step 11 が書く Impl Gate Base か merge-base）。当初は 設計: 変えない（見出しも行頭の欄も持たない task は、文法の上で前の task の本文と区別できない）。読めた task の後ろに続くと script は skip を出す。方針メモ-2 で (b)：block の行の許可リストは全節で 785/6104 行が外れ、実例の形（番号付き＋インデントした欄）も通すので閉じない。id の突き合わせも id の無い形を閉じない。この形の実例は Current Task のある 24 本で 0 件（id の無い形は未測）。安全策 4 の発火で「止める」を推奨（Opus・Fable）。限界の節の先頭に書く commit: d98a20e7 |
| G2 | 独立-2 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 差し戻しを受けた gate 単位（Gate Rounds がある）の再 gate は、線の外でも review を回す（依頼より狭い） |
| G3a | 独立-2 | low | no | self-inflicted | request-drift | accepted | 確認待ち: Express から昇格した steering（`quick (express → standard)`）は外さない（F12 と同じ問い） |
| G3b | 独立-2 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: `quick (express)` は線の外でも外さない（F12 と同じ問い） |
| G4 | 独立-2 | medium | no | self-inflicted | gate-unit-diff | accepted | Step 1e の「差分が線に触れない」が default branch からの累積の差分なので、前の task が線に触れると後の `no` の batch は全部 yes に上がる（F5 と同じ型） |
| G5 | 独立-2 | low | no | self-inflicted | test-power | accepted | `test_review_line_runs_for_express` の fixture が Gate Rounds を残しているので、入口が Task Size を渡す配線を壊しても落ちない |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「Round が約 46% 減る」は線の外を全部外したときの上限で、再 gate・Express・昇格を除き、gate runner の起動も残る |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「Gate Rounds の行が無い（差し戻し後の再 gate ではない）」と書くが、completion の再オープン後と planning の作り直し後は行が無い再 gate |
| G8 | 独立-2 | low | no | self-inflicted | deny-message | accepted | 宣言を崩す書き込み（2 本目の宣言など）も write guard が止めるが、理由の文が「implementation-reviewer が消えた」で原因と合わない（F8 と同じ型） |
| G9 | 独立-2 | low | no | self-inflicted | trust-boundary | accepted | `no` を書くのは task-breakdown だけという規定は散文だけで機械では止めない（F9 と同じ型） |
| G10 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | `test_lines_before_the_first_task_run` の、表の形で書いた T-4 の行は task と読まれ、新しい分岐を通らない |
| G11 | 独立-2 | advisory | no | inherited | doc-claim | accepted | references/task-breakdown-steps.md のテンプレートは `- AC:` を使い `Judgment Change:` を持たず、`_SINGLE_FIELD_RE` の欄名とそろっていない |
| M2 | 方針メモ-2 | advisory | no | self-inflicted | policy | accepted | 安全策 4 の発火（fail-open の high が独立-1・独立-2 の 2 巡）。部品は止めない固定行で、入力者は LLM。Opus・Fable とも「止める」を推奨。1 回目の発火なので推奨で進め、G1 を限界の節の先頭に書き、merge-ready とは書かずにユーザーへ渡す。HITL の問いは PR 本文。発火した巡の sha は eae699e0 |
| M3 | 方針メモ-3 | advisory | no | self-inflicted | policy | accepted | ユーザーが HITL に「設計に戻る選択肢も考慮して修正して」と返事（続行）。穴の種類を生んだ決定は、gate 単位で何が変わったかを Current Task の文から推していたこと。Opus・Fable とも案 3（差分で決める）を推奨し、案 2（Gate Unit の宣言）・4 は採らない。割れた点は起点の書き手：Opus は TDD Step 1 が task ごとに書く、Fable は Step 11 が 1 本だけ書き無ければ merge-base。task を Current Task に上げる経路は 7 系統あり書き忘れが残るので、書き手 1 か所の Fable 案を採った。Files の宣言は block ごとにちょうど 1 つ、注記の中は読まない。実データで宣言のある task 127 件中 92 件が読める（Files の無い task 48 件） commit: d98a20e7 |
| H1 | 独立-3 | high | yes | self-inflicted | fail-open | accepted | 列挙: 確認待ち: 並列の batch では Step 11 が batch の途中で Impl Gate Base を HEAD に進め、残りの `no` の task は空の差分で skip になる（Files の突き合わせも Step 1e の線の確認も空になる）。安全策 4 の 2 回目の発火で「止める」の扱いにし、直さず限界の節の先頭に書く。修正案は、起点を進めるのを gate 単位が終わったときだけにする・`no` の task ごとに Files と差分の重なりを求める |
| H2 | 独立-3 | high | yes | self-inflicted | fail-open | accepted | 列挙: 確認待ち: Files の欄を持たない `no` の task の block に、崩れた task が自分の Files を持ち込むと、それを `no` の task の宣言として読み skip になる。安全策 4 の 2 回目の発火で「止める」の扱いにし、直さず限界の節の先頭に書く。修正案は、宣言に数えるのを見出し直後の欄の並びの Files だけにする |
| H3 | 独立-3 | medium | no | self-inflicted | test-power | accepted | git の入口テストが、起点の後に commit した変更・祖先でない起点・merge-base への切り替えを見ていない |
| H4 | 独立-3 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: Files の宣言が読めることを外す条件に足した（依頼より狭い。宣言のある task 127 件中 35 件が読めない形、宣言の無い task 48 件） |
| H5 | 独立-3 | medium | no | inherited | request-drift | re-reported | 依頼が範囲外とした completion-check を変えている（F11 の再掲） |
| H6 | 独立-3 | medium | no | inherited | request-drift | re-reported | Express・その昇格・差し戻し後の再 gate は外さない（F12・G2・G3b の再掲） |
| H7 | 独立-3 | low | no | self-inflicted | product | accepted | git の出力が UTF-8 でないと script 全体が traceback で落ちる（exit 1 で外さない側に倒れるが、script の契約と合わない） |
| H8 | 独立-3 | low | no | self-inflicted | product | accepted | default branch を origin/HEAD だけで決めている（gate-ledger.sh・TDD Step は origin/main・master などに倒す） |
| H9 | 独立-3 | low | no | self-inflicted | product | accepted | untracked の一覧が `git -C` の cwd の下だけになる |
| H10 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 新しい state の欄 `Impl Gate Base` が state-field-tiers.md と subagent-dispatch.md の approved の更新に無い |
| H11 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | impl-gate-context.py の docstring・断片・テストの docstring の出力の形と外す条件の説明が古い |
| H12 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | docstring の「その変更は宣言の外に出る」と Why の「約 46% 減る」が保証より広い |
| H13 | 独立-3 | low | no | self-inflicted | product | accepted | 承認した未 commit の変更は起点に入らず、次の gate が run に倒れる |
| H14 | 独立-3 | low | no | self-inflicted | product | accepted | 外したときの起点が残らず、completion-reviewer の観点 11 が範囲を再現できない |
| H15 | 独立-3 | low | no | self-inflicted | product | accepted | 受け付けるパスの形（top からの相対・使える文字）が規定に書かれていない |
| H16 | 独立-3 | low | no | self-inflicted | style | accepted | `impl_gate_review` で `declared` を別の型で使い回している |
| H17 | 独立-3 | advisory | no | self-inflicted | style | accepted | テスト用の git repo を共有の `_git_fixture.init_repo` で作っていない |
| M4 | 方針メモ-4 | advisory | no | self-inflicted | policy | accepted | 安全策 4 の 2 回目の発火（high を含む巡が独立-1・2・3 の 3 回、どれも fail-open）。規則により推奨によらず「止める」の扱いで PR を更新し、返事を待つ。発火した巡の sha は e35e5450。HITL の推奨は Opus・Fable とも続行して H1 を構造で閉じる（Impl Gate Base を書くのは Current Task が空になったときだけ。Fable は skip のとき全 task を一度に移すことも足す）。割れた点は H2：Opus は限界（実例 0 件、Step 1e は実際の差分を見る）、Fable は位置の許可リストを読める割合を測ってから入れる。両者とも、設計を変えるたびに script が信じる LLM の欄が増え、次の巡がその境目を突いたと読む |
| I1 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（gate 単位と、起点・State Machine Impact block の単位が食い違っていた。起点を書くのは Current Task が空になったときだけにし、宣言が空でない task は宣言したファイルが差分に出ていることを求める）。ユーザーの返事「続行。並列の batch と Gate Batch の穴を構造で閉じて」で直した。H1 と同じ。空の差分も宣言に収まると読み、Step 11 が task ごとに Impl Gate Base を進めるので、並列の batch の残りの no の task が差分を誰も見ずに外れる。安全策 4 で「止める」を選んだ扱いの後なので直さない。限界の節の先頭に書いたまま。commit: 4ed39c89 |
| I2 | 独立-4 | medium | yes | self-inflicted | approval-path | fixed | 設計: 変える（外すのは Current Task が 1 task のときだけにし、Gate Batch・並列の batch は外さない）。ユーザーの返事で直した。Gate Batch で、前の task の仕様変更（AC・ADR・human check への Routing）は handoff の block に残らず、gate 単位の差分も steering を除くので、Step 1e が見ずに外す。安全策 4 で「止める」を選んだ扱いの後なので直さない。限界の節の先頭に足す。commit: 4ed39c89 |
| I3 | 独立-4 | medium | no | self-inflicted | product | accepted | 完了の受理（skipped）が、gate が外せる条件（Task Size・Gate Rounds・Files）より広い |
| I4 | 独立-4 | medium | no | self-inflicted | product | accepted | state-field-tiers.md の縮める規定と write guard の deny の文が、Judgment Change の行を残すよう案内しない |
| I5 | 独立-4 | medium | no | self-inflicted | doc-claim | accepted | task-sizing.md の reviewer 省略の表と impl-gating SKILL の冒頭・eval が Step 1e の例外を書かない |
| I6 | 独立-4 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: gate runner は起動したままで遷移表を変えていない（依頼は impl-gating を外す）。残した 1 回の費用は未測。PR 本文の問いに足す |
| I7 | 独立-4 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 範囲外の completion-check を、問いに挙げた範囲より広く変えた（機械検査・Checklist E (ii)・state-machine の表）。旧#564 はすでに main に入った。PR 本文の問いを直す |
| I8 | 独立-4 | medium | no | self-inflicted | product | accepted | 観点 11 は外した task の差分の範囲を再現できず、判定できないときは High なので外した task を全部再 gate しうる |
| I9 | 独立-4 | low | no | self-inflicted | request-drift | accepted | 確認待ち: 再 gate では宣言によらず review を回す（依頼より狭い）。問いに足す |
| I10 | 独立-4 | low | no | self-inflicted | product | accepted | H7 と同じ。git の出力の decode の例外で context の script 全体が exit 1 |
| I11 | 独立-4 | low | no | self-inflicted | test-power | accepted | 入口のテストが run の理由を判別していない。祖先でない起点のテストが無い |
| I12 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | Impl Gate Base が state-field-tiers.md・State Update Contract に無い。state-machine.md・completion-check の (ii) が例外を持たない |
| I13 | 独立-4 | low | no | self-inflicted | product | accepted | shell・LLM 呼び出し・エージェント実装は security reviewer を選ぶ語だが線に入っていない |
| I14 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | 変更断片が lint-scripts-functional.sh の上限の変更を書いていない |
| I15 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | Gate Rounds を approved で消すという注記、skip の行の起点の注記、approved の単位の注記が実装と合わない |
| I16 | 独立-4 | low | no | self-inflicted | style | accepted | H16 と同じ。declared の使い回し |
| I17 | 独立-4 | low | no | self-inflicted | product | accepted | write guard が ok と skipped の間の書き換えを止めない |
| I18 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に、サイズ上限の deny の文・(ii) の例外・外したときの reset・guard の通す書き換えが無い |
| I19 | 独立-4 | advisory | no | self-inflicted | product | accepted | 線の読み方を広げた（refactor・手順文・受理する値）。根拠の実測と読み方が同じかは示していない |
| M5 | 方針メモ-5 | advisory | no | self-inflicted | policy | accepted | ユーザーが安全策 4 の 2 回目の発火に「続行。並列の batch と Gate Batch の穴を構造で閉じて」と返事。Opus は main の案 1〜3（1 task だけ外す・起点は gate 単位を終えたときだけ・宣言と差分の重なり）を推奨。Fable は 2・3 を採り、1 の代わりに差分から除くのを帳簿だけにする案。割れた点は main が実測で決めた：この repo の .gitignore は `.steering/*/` を無視するので、requirements.md・adr.md の変更は git の差分に出ず、Fable の案は効かない。依頼より狭くなる分は Gate Batch の行がある tasklist 2/68 本・`Mode: parallel` 6/68 本。安全策 4 は続行に戻し、以後の巡を数える |
| J0 | 独立-5 | advisory | no | self-inflicted | policy | accepted | 1 回目の起動は、読み込みの行数が 4 つとも wc -l より 1 多かったので無効にして起動し直した（末尾の改行は 4 ファイルとも有り）。指摘は 2 回目の出力から記録する |
| J1 | 独立-5 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（並列の batch を Current Task の task 数だけで見分けていた。subagent-driven-implementation が並列かを決める Execution Plan の Mode の行を許可リストで読み、節が無いか決まった逐次の形のときだけ外す）。ユーザーの返事「続行。Execution Plan を許可リストで読んで並列の batch の残りを閉じて」で直した。並列の batch で 1 つ目の task を移すと Current Task に最後の 1 task だけが残り、兄弟が steering の外を何も変えていなければ、1 task の gate として skip になる。判定は Execution Plan を読まない。安全策 4 の 3 回目の発火なので、方針メモ-6 の後に止める扱いで限界の節の先頭に書く。commit: b14f341f |
| J2 | 独立-5 | medium | no | self-inflicted | test-power | accepted | 2 task のテストは len の判定を消しても、後ろの Files の判定で run になって通る |
| J3 | 独立-5 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 並列の batch を線の外でも外さないように狭めたことを、問いとして確かめていない |
| J4 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Summary 1 行目が gate 単位の全 task と書いたまま |
| J5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | § Judgment Change の Why が約 46% 減ると条件なしに書く |
| J6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | PR 本文の上限の理由の列挙と Files の文が 1 task の判定と合わない |
| J7 | 独立-5 | low | no | inherited | product | accepted | State Update Contract に Impl Gate Base の書き込みが無い（H10・I12 と同じ） |
| J8 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | テストの docstring と入口テストのコメントが古い |
| J9 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 宣言したファイルが差分に出ているの意味（1 つ以上）が文書で曖昧 |
| M6 | 方針メモ-6 | advisory | no | self-inflicted | policy | accepted | 安全策 4 の 3 回目の発火（独立-5 の J1）。2 回目以降なので推奨によらず「止める」の扱いで PR を更新し返事を待つ。Opus・Fable とも HITL の推奨は続行で、Execution Plan を許可リストで読む（節が無いか、Mode の行がちょうど 1 本で sequential と読めて Gate Batch の行が無いときだけ今の判定に進む。見出しの段や Mode 行の重複は run）。main の案（parallel の語か Gate Batch の行で run）は拒否語のリストなので採らない。割れた点は sequential として受け付ける形で、Opus は `- Mode: sequential` と `- sequential`、Fable は実データを測ってから。実データは Execution Plan のある 17 本のうち `- Mode: sequential` 10 本、括弧の注記つきの `Mode: sequential` 2 本、parallel 系 5 本（`parallel-then-sequential` を含む） |
| K1 | 独立-6 | high | yes | self-inflicted | fail-open | accepted | 列挙: 確認待ち: Execution Plan があるかを見出し（`#+ ... execution plan`）だけで見るので、見出しでない形（`**Execution Plan**`・冒頭の `- Execution Plan: Mode parallel`・行頭の空白・`## Execution-Plan`・`## 実行計画`）で並列を書くと逐次と読む。実データの事故の形は 0 件（68 本中、該当の語を持つ 2 本は pytest の並列実行の記述）。方針メモ-7 で (b)、安全策 4 の 4 回目の発火で止める扱い。限界の節の先頭に書く |
| K2 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | `## Execution Plan` の後ろに語がある見出しも外してよい節として通る（PR 本文は前後の語が違えば run と書く） |
| K3 | 独立-6 | low | no | self-inflicted | test-power | accepted | 見出しのテストの本文が `- Mode: parallel` なので、見出しの判定を消しても通る |
| K4 | 独立-6 | low | no | self-inflicted | request-drift | accepted | 確認待ち: 番号つきの Gate Batch の行があると、Gate Batch の外の単独の task も外さない（依頼より狭い） |
| K5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 変更断片が Gate Batch の行と見出しの数の条件を書いていない |
| K6 | 独立-6 | low | no | self-inflicted | style | accepted | `_SKIPPABLE_TASK_SIZES` の `#:` コメントが Execution Plan の定数の上に離れた |
| K7 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の 17 本の内訳と parallel 6 本の数の重なりが読めない |
| M7 | 方針メモ-7 | advisory | no | self-inflicted | policy | accepted | 安全策 4 の 4 回目の発火（独立-6 の K1、閉じ方: 列挙）。Opus・Fable とも (b) と「止める」でよいと推す（入力者の実測で事故の形は 68 本中 0 件）。続行するなら、全行から数える案は語の列挙が続くので両者とも採らない。構造の案は割れた: Fable は並列の batch を Gate Batch と同じく全 task が通るまで Current Task から移さない形、Opus は Step 11 が Impl Gate Base と同じ時点で Completed Tasks の数を state に書き、数が違うか欄が無ければ run にする形（書き忘れが run の向きになる）。main は Opus の形を続行の案に載せる（既存の数え方と既存の書く時点に足すだけで、書き忘れが fail-closed になるため）。2 回目以降の発火なので推奨によらず止める扱いで PR を更新し、返事を待つ |
| L1 | 独立-7 | medium | no | self-inflicted | count-source | accepted | 列挙: `Impl Gate Completed` は runner（LLM）が数え、script は `completed_tasks_reviewed_by` で数える。Step 1 の出力（`_calibration_and_tasks`）は fence の中やインデントした task 行も並べるので、runner が一覧から数えると 1 多くなりうる。逐次では毎回 run（費用の側）、見出しでない並列の batch では数の層が効かない（Files の層と Step 1e が残る）。修正案は script が数を固定行で出し runner が写す |
| L2 | 独立-7 | low | no | self-inflicted | request-drift | accepted | ユーザーの返事「最初の gate 単位を 0 とみなす今の形でよい」で今の形に決めた。選んだ案は「欄が無ければ run」だが、実装は起点も欄も無い最初の gate 単位を 0 とみなす（外す側への広げ方）。戻す範囲は `_completed_at_start` の 0 の分岐と § Judgment Change の括弧 |
| L3 | 独立-7 | low | no | self-inflicted | test-power | accepted | 欄が無い・読めないときの入口のテストは Completed が 4 件なので、None を 0 に変える変異でも通る。理由を assert していない |
| L4 | 独立-7 | low | no | self-inflicted | fail-closed | accepted | 4,300 桁を超える数字で `int()` が ValueError を出し script が traceback で exit 1 になる（review を回す側） |
| L5 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | `references/state-field-tiers.md` の Tier 3 の表に `Impl Gate Completed`・`Impl Gate Base` の書き込み・クリア条件が無い |
| L6 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | 数が違えば run にする分岐の、当たる件数（または未測）が PR 本文に無い |
| L7 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | Step 11 が並列の batch の途中で Current Task が空だと読み違えて 2 欄を同時に書くと、数は合い見分けない。限界に無い |
