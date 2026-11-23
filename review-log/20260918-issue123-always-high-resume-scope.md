---
lane: L1+
pr: 140
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1209561608aeea72805cf9e4bfce11b82bf1580f | 2 | 2 | 2 | 2026-09-18T23:30+09:00 |
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable、ユーザー指示) + user | - | 0 | 0 | 0 | 2026-09-19T01:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 全差分, model: opus | 6bad33598f461f52bfa284dfcc4fbaa6d14dbe93 | 3 | 0 | 3 | 2026-09-19T02:10+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#140 review) | 1b9173e8b665f5fc683cc48cc818e5af41bece31 | 2 | 4 | 2 | 2026-09-19T09:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | 08e70b1db158c4d34759ac09d0daa10db54397b7 | 5 | 1 | 5 | 2026-09-19T10:10+09:00 |
| PR後-2 | yamaguchi-tk (GitHub PR 旧#140 review) | 5dc562f9373ac27b1404c04be63205142f930e73 | 0 | 0 | 0 | 2026-09-19T21:32+09:00 |
| 独立-4 | light-lane-independent-reviewer, 全差分, model: opus | 16f93aafd69769734f11f75ab22036bfdd70b1c2 | 5 | 2 | 5 | 2026-09-19T21:53+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分, model: opus | db0a7ea6bbdc5c855902a1aca66ba7e9daae5d0d | 5 | 0 | 5 | 2026-09-19T23:10+09:00 |
| 独立-6 | light-lane-independent-reviewer, 全差分, model: opus | 6444950d4881dd6e81ae3dabeaf6e5e16e5ac260 | 6 | 2 | 6 | 2026-09-20T00:00+09:00 |
| 独立-7 | light-lane-independent-reviewer, 差分, model: opus | 6e9e86c4bc8e001566cf95a7b74b963d98d89de0 | 6 | 1 | 6 | 2026-09-20T00:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| R1 | 独立-1 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）SessionStart の `AutoCycleCount` 加算が行頭の `AutoCycleCount: N` 完全一致しか見ず、bullet 形・`=` 形などでは読む側（gdd_extract_doc_field）と食い違って加算が止まり、上限が効かず compact 自動復帰が発火し続ける（pre-existing。本 PR の (b) で適用範囲内になった） |
| R2 | 独立-1 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）PreCompact の `Status` / `CompactSource` 書き込みが `=` 形・バッククォート形・fence を読む側と同じに扱わず、先頭の値が残って compact 自動復帰が発火しない（pre-existing。本 PR の (a) で適用範囲内になった） |
| R3 | 独立-1 | medium | no | self-inflicted | always-high-scope-restatement | fixed | 「降格の防止」が範囲を言い直しており、後半の「block しない lint・hook には実害クラスを付けない」が (a)(b) と字面で食い違う |
| R4 | 独立-1 | medium | no | self-inflicted | resume-firing-enumeration | deferred | （Issue 旧#138）(b) が post-merge 自動継続・canonical field 欠落時の `[gdd:blocked]`・shadow marker の抑止判定を含まず、限界にも書いていない |
| R5 | 独立-1 | low | no | self-inflicted | wiring-claim | fixed | 「done guard が `Next Action` を読む」は誤り（done guard は `Resume From` / `Route In Progress` だけ） |
| R6 | 独立-1 | low | no | self-inflicted | resume-scope-test-power | fixed | field の実在検査は 4 ファイル連結で PreCompact・Stop hook には当たっておらず、断片の「PreCompact / done guard で読まれていることを検査」は実際より強い。独立-4 X12 の修正で、ファイル単位の検査にした |
| R7 | 独立-1 | low | no | self-inflicted | test-docstring-stale | fixed | テストの docstring が無条件の「実害クラスを付けない」のまま、コメントの「3 箇所」は実際は 2 箇所。独立-4 X10 の修正で、docstring とコメントを直した |
| R8 | 独立-1 | advisory | no | inherited | agent-high-example | fixed | agents/gdd-implementation-reviewer.md の High の例「resume/gate failure」が無条件のまま |
| P1 | 方針メモ | advisory | no | inherited | resume-field-writer-reader-asymmetry | accepted | ユーザーが R1・R2 を本 PR で直す（L1+）と決めた後、Opus は別ファイルの setter/deleter（fence 非追跡＋読み直し）、Fable は B に fence 開始行の除外・改行ガードを足す案か共有 reader に行番号 mode を足す案 C を推奨。ユーザーは「止める」を選択し、R1・R2 は限界として PR 本文に書く（以後の巡で安全策 4 を発火させない） |
| S1 | 独立-2 | high | yes | inherited | compact-resume-marker-bypass | accepted | （Issue 旧#142）compact の印（`CompactSource: pre-compact` / `Status: paused`）が SessionStart(compact) に消費されずに残ると、同じ worktree の次の SessionStart（/clear・新セッション・main）で session・branch を照合せずに自動復帰が発火し、Safe Resume を迂回する（pre-existing。止める選択後のため限界として PR 本文に追記） |
| S2 | 独立-2 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | R2 の再掲 |
| S3 | 独立-2 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | R1 の再掲。AutoCycleCount の加算は bullet 形・空白なし・末尾空白・CRLF も扱わず、断片の開示文（行頭形と bullet 形を扱う）は不正確 |
| S4 | 独立-2 | low | no | self-inflicted | resume-scope-test-power | fixed | R6 の再掲（field 実在検査は PreCompact・done guard に効いていない）。独立-4 X12 の修正で、ファイル単位の検査にした |
| S5 | 独立-2 | low | no | self-inflicted | test-docstring-stale | fixed | R7 の再掲。独立-4 X10 の修正で、docstring とコメントを直した |
| S6 | 独立-2 | low | no | self-inflicted | harm-class-enumeration | fixed | 範囲外でも付ける実害クラスの列挙に `approval-path` が無い。V6 と同じ修正で解消 |
| S7 | 独立-2 | advisory | no | self-inflicted | resume-scope-type-mapping | fixed | (a)(b) の欠陥を 4 型の fail-open として扱うと明記していない。独立-4 X7 の修正で、(a)(b) に届く欠陥を fail-open として扱うと明記 |
| U1 | PR後-1 | high | yes | inherited | precompact-write-failure-silent | accepted | （Issue 旧#141）PreCompact の `sed` の失敗が `&&` の途中の要素で `set -e` に掛からず、state.md が書き換わらないまま exit 0（止める選択後のため限界として PR 本文と断片に追記） |
| U2 | PR後-1 | high | yes | inherited | precompact-append-newline | accepted | （Issue 旧#141）PreCompact の `CompactSource` / `PausedAt` の追記が先頭改行なしで、最終行に改行が無い state.md では直前行に連結して読めない（同上） |
| U3 | PR後-1 | medium | no | inherited | resume-gate-example-unscoped | fixed | gdd-implementation-gating・gdd-systematic-debugging の ops-blocking medium の「resume / gate correctness」が無条件。横展開で agent の High 例（R8）も同じ直し方にした |
| U4 | PR後-1 | medium | no | self-inflicted | fragment-limit-accuracy | fixed | 断片の Known Limitations が「2 件」「行頭形と bullet 形を扱う」で実態と違う |
| U5 | PR後-1 | medium | no | self-inflicted | resume-scope-test-power | fixed | `Status` が契約テストで固定されておらず、doc と RESUME_FIELDS から同時に消しても green |
| U6 | PR後-1 | medium | no | self-inflicted | review-log-lane | fixed | front matter が `lane: L1` のまま（L1+ に格上げ済み） |
| V1 | 独立-3 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R1 の再掲 |
| V2 | 独立-3 | high | yes | inherited | compact-resume-marker-bypass | accepted | （Issue 旧#142）S1 の再掲 |
| V3 | 独立-3 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R2 の再掲 |
| V4 | 独立-3 | high | yes | inherited | precompact-write-failure-silent | accepted | （Issue 旧#141）U1 の再掲 |
| V5 | 独立-3 | high | yes | inherited | precompact-append-newline | accepted | （Issue 旧#141）U2 の再掲 |
| V6 | 独立-3 | medium | no | self-inflicted | harm-class-enumeration | fixed | （Issue 旧#149）「4 型の判定と実害クラスの判定は独立」が広すぎ、範囲外の欠陥に `approval-path` を付けるかが割れる（S6 と同じクラスタ）。V6 修正（61e34f00）で付けてよい実害クラスを data-loss と security-boundary に限った |
| V7 | 独立-3 | low | no | self-inflicted | resume-scope-test-power | fixed | 断片の Added とテストのコメントが field 実在検査の範囲を言い過ぎ、User Action Required の「high・blocking として報告される」も 4 型の判定を前提にしている。S4・S7 が断片の Known Limitations に無い。独立-4 X8 の修正で、断片の Added・User Action Required を直した |
| V8 | 独立-3 | low | no | self-inflicted | ops-impact-derivation | accepted | skill に足した「範囲は § 常時 High の適用範囲に従う」は、`ops impact` を実害クラス ∪ `product` から導く規則のため ops-blocking の分類を変えない |
| V9 | 独立-3 | low | no | self-inflicted | resume-firing-enumeration | accepted | UserPromptSubmit と plan-reread hook の cross-session guard も (b) の字面では範囲外で、PR 本文の限界に無い |
| V10 | 独立-3 | low | no | self-inflicted | always-high-scope-structure | accepted | 適用範囲の段落に継ぎ足した結果、「判定できないときは適用範囲内」が (a)(b) の境目に及ぶかが字面で決まらない |
| V11 | 独立-3 | low | no | self-inflicted | test-docstring-stale | fixed | R7 の再掲。独立-4 X10 の修正で、docstring とコメントを直した |
| V12 | 独立-3 | advisory | no | self-inflicted | resume-scope-test-power | fixed | 列挙が 1 箇所だけかの検査が `CompactSource` しか数えていない。独立-4 X6 の修正で、全 field の出現を数えるようにした |
| V13 | 独立-3 | advisory | no | inherited | session-id-trim-asymmetry | accepted | Safe Resume と gdd_session_continuity_ok で session_id の末尾空白・CRLF の扱いが違う（止める側に倒れる） |
| W1 | PR後-2 | - | - | - | - | - | なし |
| X1 | 独立-4 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R1 の再掲 |
| X2 | 独立-4 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R2 の再掲 |
| X3 | 独立-4 | high | yes | inherited | precompact-write-failure-silent | accepted | （Issue 旧#141）U1 の再掲 |
| X4 | 独立-4 | high | yes | inherited | precompact-append-newline | accepted | （Issue 旧#141）U2 の再掲。直前の canonical field の値も壊れること、SessionStart の AutoCycleCount 追記も同じ形であることは新しい情報で、PR 本文の限界と断片を正確にした（hook は直さない。差分は文書で欠陥はコードの②） |
| X5 | 独立-4 | high | yes | inherited | compact-resume-marker-bypass | accepted | （Issue 旧#142）S1 の再掲 |
| X6 | 独立-4 | medium | no | self-inflicted | resume-scope-test-power | fixed | (a)(b) を適用範囲内とする文が固定されておらず、「範囲外」や「・削除」の欠落でも green。文を全文で固定し、列挙 1 箇所の検査を全 field に広げた |
| X7 | 独立-4 | medium | no | self-inflicted | resume-scope-type-mapping | fixed | (a)(b) の欠陥が 4 型のどれかを書いておらず、「発火しないのは fail-closed で medium」と読めて割れが残る。fail-open として扱う文を足した |
| X8 | 独立-4 | low | no | self-inflicted | fragment-limit-accuracy | fixed | 断片の Added・User Action Required・Known Limitations が PR 本文の限界より強い。そろえた |
| X9 | 独立-4 | low | no | self-inflicted | ops-impact-derivation | fixed | impl-gating の ops-blocking medium が狭まる帰結（express で advisory になりうる）が書かれていない。断片の Known Limitations に書いた |
| X10 | 独立-4 | low | no | self-inflicted | test-docstring-stale | fixed | テストの docstring とコメント（3 箇所、PreCompact を読む側と書く）が改訂後と合わない。直した |
| X11 | 独立-4 | advisory | no | self-inflicted | fragment-limit-accuracy | fixed | X-66 の断片が (a)(b) と例外で古くなる。他 PR の断片は書き換えられない（version-not-consumed）ので、本断片の Summary に書いた |
| X12 | 独立-4 | advisory | no | self-inflicted | resume-scope-test-power | fixed | field の実在検査に PreCompact・done guard が寄与していない（R6・S4 の再掲）。ファイル単位の検査にした |
| X13 | 独立-4 | advisory | no | self-inflicted | disclosure-scope | fixed | 5 件が残る間、hook 周りを触る他 PR の独立レビューもこれを数えうることが限界に無い。PR 本文に書いた |
| Y1 | 独立-5 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R1 の再掲 |
| Y2 | 独立-5 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R2 の再掲 |
| Y3 | 独立-5 | high | yes | inherited | precompact-write-failure-silent | accepted | （Issue 旧#141）U1 の再掲 |
| Y4 | 独立-5 | high | yes | inherited | precompact-append-newline | accepted | （Issue 旧#141）U2 / X4 の再掲 |
| Y5 | 独立-5 | high | yes | inherited | compact-resume-marker-bypass | accepted | （Issue 旧#142）S1 の再掲 |
| Y6 | 独立-5 | low | no | self-inflicted | fragment-limit-accuracy | fixed | 断片の Summary が他の断片のファイル名と「同じ版」を書き、リリース後に存在しないファイルを指す。X-66 の「medium として deferred にできる」も上書きの列挙に無い。ファイル名を使わない書き方にし、作業上の注記は PR 本文に移した |
| Y7 | 独立-5 | low | no | self-inflicted | resume-scope-type-mapping | fixed | 「(a)(b) に届く欠陥（書き損じ・消し損じ・発火しない・誤発火）」が網羅の列挙と読め、誤削除が抜ける。「種類（…誤削除…など）を問わず」にした |
| Y8 | 独立-5 | advisory | no | inherited | fragment-limit-accuracy | fixed | PR 本文の限界にある UserPromptSubmit・plan-reread hook の cross-session guard の呼び出し側（V9）が、断片の Known Limitations に無い。足した |
| Z1 | 独立-6 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R1 の再掲。数値でない値・fence 内だけの行でも加算が止まる |
| Z2 | 独立-6 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R2 の再掲 |
| Z3 | 独立-6 | high | yes | inherited | precompact-write-failure-silent | accepted | （Issue 旧#141）U1 の再掲。追記は成功しうるので「書き換わらないまま」は不正確、ロック削除の失敗でも発火しない |
| Z4 | 独立-6 | high | yes | inherited | precompact-append-newline | accepted | （Issue 旧#141）U2 / X4 の再掲 |
| Z5 | 独立-6 | high | yes | inherited | compact-resume-marker-bypass | accepted | （Issue 旧#142）S1 の再掲 |
| Z6 | 独立-6 | high | yes | inherited | session-id-trim-asymmetry | accepted | V13 の再掲（severity を high と判定）。Safe Resume の session_id 読み取りだけが末尾空白・CR を落とさず、同じセッションで Candidate Mode が誤発火する。欠陥はコードで差分は文書（②）。限界の 6 件目と後続候補に書いた |
| Z7 | 独立-6 | medium | no | self-inflicted | resume-scope-test-power | fixed | 「降格の防止」の範囲の参照を消してもテストが通る（後半の「適用範囲外」に一致する）。句を丸ごと固定した |
| Z8 | 独立-6 | medium | no | self-inflicted | harm-class-enumeration | fixed | 括弧書き（test-power / product）と「付けてよいのは data-loss と security-boundary だけ」が食い違い、category が割れる。1 文にまとめ、「（data-loss など）」を外した |
| Z9 | 独立-6 | low | no | self-inflicted | harm-class-enumeration | fixed | 「medium の上限が data-loss に掛かるかは明文が無い」は不正確で、上限と independent-review.md (3-d) が食い違う。data-loss / security-boundary を付けた finding には上限を掛けないと明記した |
| Z10 | 独立-6 | low | no | inherited | resume-gate-example-unscoped | accepted | reviewer-common.md の ops impact の説明の「resume/gate 正確性」だけが範囲への参照を持たない（U3 の対の片方）。参照を足した。足した参照は導出（実害クラス ∪ product）と矛盾したので取り消した（独立-7 Q8）。ops impact は category からの導出のまま |
| Z11 | 独立-6 | advisory | no | self-inflicted | resume-scope-type-mapping | fixed | 「(a)(b) に届く欠陥は fail-open」が hook に限定されておらず、skill の文言の欠陥まで High と読める。hook に限った |
| Z12 | 独立-6 | advisory | no | inherited | hook-owned-field-declaration | accepted | state-field-tiers の hook 所有 Status の「無いのが正常」が実動作と合わず、CompactSource 等が宣言されていない（②。後続候補） |
| Z13 | 独立-6 | advisory | no | self-inflicted | resume-scope-test-power | fixed | hook 所有 field のテストが宣言の最初の 1 つしか読まない。findall にした |
| Z14 | 独立-6 | advisory | no | self-inflicted | red-green-evidence | fixed | gdd-systematic-debugging を触ったのに 1b の記載が not_applicable の理由と合わない。PR 本文を直した |
| Q1 | 独立-7 | high | yes | inherited | session-id-trim-asymmetry | accepted | Z6 / V13 の再掲（Safe Resume の session_id の末尾空白）。PR 本文の後続候補 |
| Q2 | 独立-7 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R1 の再掲 |
| Q3 | 独立-7 | high | yes | inherited | resume-field-writer-reader-asymmetry | accepted | （Issue 旧#141）R2 の再掲 |
| Q4 | 独立-7 | high | yes | inherited | precompact-write-failure-silent | accepted | （Issue 旧#141）U1 の再掲 |
| Q5 | 独立-7 | high | yes | inherited | precompact-append-newline | accepted | （Issue 旧#141）U2 の再掲 |
| Q6 | 独立-7 | high | yes | inherited | compact-resume-marker-bypass | accepted | （Issue 旧#142）S1 の再掲 |
| Q7 | 独立-7 | medium | no | self-inflicted | harm-class-enumeration | fixed | Z9 で足した「(3-d) と同じく severity は下げない」が、同じ段落の「Stage 2 の対象に戻る」と食い違い、同じ段落が二通りに読める。Stage 2 に戻らない例外を明記し、(3-d) は「独立レビューでは同趣旨で降格を禁じる」に限定した |
| Q8 | 独立-7 | low | no | self-inflicted | ops-impact-derivation | fixed | Z10 で足した ops impact の範囲限定が、導出定義（実害クラス ∪ product）と矛盾する。足した参照を取り消し、範囲を足さないことをテストで固定した |
| Q9 | 独立-7 | advisory | no | self-inflicted | test-docstring-stale | fixed | テストの module docstring に、data-loss / security-boundary には medium の上限も掛けない旨が無い。足した |
| Q10 | 独立-7 | advisory | no | self-inflicted | fragment-limit-accuracy | fixed | PR 本文の変更内容に、足したテストクラスの記載が無い。書いた（クラス名は Q8 で OpsImpactIsDerivedFromCategoryTest に変えた） |
| Q11 | 独立-7 | advisory | no | self-inflicted | fragment-limit-accuracy | fixed | 断片の「既存の欠陥 6 件」の下に補足の bullet が並び 7 個に見える。補足を親の外に出した |
