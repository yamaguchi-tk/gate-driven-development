---
lane: L1+
pr: 615
follow_up_of: 576
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 900a69d7 | 0 | 0 | 0 | 2026-10-29 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5202f425 | 2 | 6 | 2 | 2026-10-30 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 87140d10 | 1 | 5 | 3 | 2026-10-30 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 87140d10 | 0 | 0 | 0 | 2026-10-30 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 78d4c2bf | 1 | 1 | 2 | 2026-10-30 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | 78d4c2bf | 0 | 0 | 0 | 2026-10-30 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | fbabf571 | 0 | 1 | 0 | 2026-10-30 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 89f425eb | 0 | 0 | 0 | 2026-10-30 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | 経路 | accepted | 方針: 案 A（express も requirements-gating で planning reviewer と request-crosscheck を回す。2 本一致）。lint はテンプレートを合わせる（Fable。Opus は script 側）、human check の一部変更で AC・範囲・Files が変われば再入（Opus。Fable の機械の確認は次の PR）、auto-confirm も reviewer の後で blocking・衝突なら辞退（2 本一致）、条件外れは reviewer の blocking から既存の昇格（2 本一致）、3 タスクの再生で効き目を測る（Opus）。確認は返事を待たずに推奨で進める |
| F1-1 | 独立-1 | high | yes | self-inflicted | state テンプレート | fixed | 設計: 変えない（実装の写し間違い。テンプレートに行を足す設計は正しい）。Standard の state.md テンプレートに Requirements・Design Review Status が 2 行ずつ入り、design-gate-route.py が 1 行と読めず confirm が常に none になる。重複を消し、テンプレートに confirm を当てるテストを足した。commit: ffd5ab1b |
| F1-2 | 独立-1 | high | yes | self-inflicted | auto-confirm | fixed | 設計: 変える（条件 8 を「衝突 0 件」の数えから、通す形の許可リストに変えた）。突き合わせが unavailable でも条件 8 が通り、human check なしで build に進む。読めて unavailable が無く、節が `既存とぶつかる: なし` の 1 行だけのときだけ通す。commit: 1383c865 |
| F1-3 | 独立-1 | medium | no | self-inflicted | 既存規定との食い違い | accepted | human-check-template.md:248・compact:61 がズレ確認を quick (standard)・standard に限ったまま。express の human check に着手のときのぶつかりが出ない |
| F1-4 | 独立-1 | medium | no | self-inflicted | express の条件 | accepted | express の 4 条件は実装コード 1-2 ファイル、Promotion Rules と § 昇格条件は変更ファイル 3 件以上で、実装 2・テスト 1 の express が blocking になる |
| F1-5 | 独立-1 | medium | no | self-inflicted | 再入 | accepted | gdd-dev.md 10 の返答の分類 STEP 1 に、express の一部変更の再入が無い |
| F1-6 | 独立-1 | medium | no | self-inflicted | auto-confirm | accepted | auto-confirm では「原文だけでは決まらない」の行き先が人に届かない。条件 8 はぶつかりだけを見る |
| F1-7 | 独立-1 | medium | no | self-inflicted | 既存規定との食い違い | accepted | state-machine-overview.md:14-18 の express の流れが requirements-gating を飛ばしたまま |
| F1-8 | 独立-1 | medium | no | self-inflicted | 依頼との突き合わせ | fixed | 依頼の「計画のレビュー」を requirements の観点だけに狭め、design phase のチェックを express に当てていない。reviewer の express の段落に、実装可能性の机上追跡を Implementation Policy・Sequence Plan・既存実装の確認に当てる文を足した。commit: 003754cb |
| F1-9 | 独立-1 | low | no | self-inflicted | 再入 | accepted | 一部変更からの再入で、読む範囲・lint の --entry・Round の数え方がレビューループの契約と合わない |
| F1-10 | 独立-1 | low | no | self-inflicted | auto-confirm | accepted | auto-confirm のときに requirements-gating Step 8 の HITL・stop marker を何で置き換えるかが書かれていない |
| F1-11 | 独立-1 | low | no | self-inflicted | reviewer の選定 | accepted | express の requirements-gating での security reviewer の選定条件が reviewer-selection に無い |
| F1-12 | 独立-1 | low | no | self-inflicted | 依頼との突き合わせ | accepted | 確認待ち: Promotion Rules の AC の線を 2 件以上から 4 件以上に、確認なしに変えた。task-sizing の昇格条件にそろえる推奨で進め、PR 本文の限界に問いを書く |
| F1-13 | 独立-1 | low | no | self-inflicted | 既存規定との食い違い | accepted | gdd-completion-reviewer.md:67・gdd-pr-review SKILL.md:93 に「request.md は quick (standard)・standard だけ」が残る |
| F1-14 | 独立-1 | low | no | self-inflicted | 説明 | accepted | README.md:118・onboarding.md:40 の express の所要時間の目安が古い |
| F1-15 | 独立-1 | low | no | self-inflicted | changelog | accepted | 断片の User Action Required に進行中の express の扱いが無く、Affected Files と Validation が差分と合わない |
| F1-16 | 独立-1 | low | no | self-inflicted | reviewer の選定 | accepted | 昇格の後の再入で design の観点の組が selected になるのに § Express は起動しない |
| F1-17 | 独立-1 | low | no | self-inflicted | テスト | accepted | express の precheck のテストが Design Review Status の条件を固定していない |
| F1-18 | 独立-1 | low | no | self-inflicted | 計測 | accepted | 一部変更の再入・条件 8・reviewer の express の blocking の 3 つで、当たる件数を PR 本文に書いていない |
| F1-19 | 独立-1 | advisory | no | self-inflicted | 説明 | accepted | Standard テンプレートに行を足した変更が PR 本文にも断片にも無い（重複を消したので不要） |
| F1-20 | 独立-1 | advisory | no | self-inflicted | 説明 | accepted | task-sizing.md:426・faq.md:195-196 に express に AI reviewer が無い前提の記述が残る |
| F2-1 | 独立-2 | high | yes | self-inflicted | auto-confirm | fixed | 設計: 変える（条件を「blocking 0 件」の数えから、reviews.md の全 Round 節と突き合わせの固定の 1 行を通す形に変えた）。文を縮めて「Round を問わず」が落ち、最新 Round だけを読むと Round 1 の blocking を AI が直した後に人を通らず build に入る。commit: 67f8959a |
| F2-2 | 独立-2 | medium | yes | self-inflicted | auto-confirm | fixed | 設計: 変える（F2-1 と同じ）。条件が `原文だけでは決まらない` を見ず、曖昧な語の質問がユーザーに届かずに build に入る。`原文だけでは決まらない: なし` の 1 行も条件にした。commit: 67f8959a |
| F2-3 | 独立-2 | medium | yes | inherited | auto-confirm | fixed | 設計: 変える（条件 7 を発動文に取り込み、「または」を「かつ」にした）。task-sizing.md:189 の「または」で `--auto-confirm` だけで条件を飛ばせる読み方が残る。commit: 67f8959a |
| F2-4 | 独立-2 | medium | no | self-inflicted | 依頼との突き合わせ | accepted | express に当てた机上追跡の対象の節が、reviewer の入力の 1 枚（subagent-dispatch.md:60）に入らず届かない |
| F2-5 | 独立-2 | medium | no | self-inflicted | 依頼との突き合わせ | accepted | 確認待ち: 依頼の「計画のレビュー」は design の観点を足したものを指すが、express には机上追跡だけを当て、配線表・テスト方針・影響範囲の記録を当てていない。design の観点の組を起動しない推奨で進め、PR 本文の限界に問いを書く |
| F2-6 | 独立-2 | medium | no | self-inflicted | express の条件 | re-reported | F1-4 の再掲（ファイル数の数え方が判定基準と Promotion Rules・昇格条件で違う） |
| F2-7 | 独立-2 | medium | no | self-inflicted | 計測 | accepted | 発火条件の件数で、reviewer の express の条件による blocking は 14 タスクの requirements.md で測れるのに未測。残り 2 つは未測のまま足すユーザーの確認が依頼の原文に無い |
| F2-8 | 独立-2 | low | no | self-inflicted | 依頼との突き合わせ | accepted | 机上追跡の節の見出しと本文が「design phase 専用」「requirements phase ではスキップ」のまま |
| F2-9 | 独立-2 | low | no | self-inflicted | 依頼との突き合わせ | accepted | 机上追跡の対象に `## Scope` の Files が入っていない |
| F2-10 | 独立-2 | low | no | self-inflicted | changelog | fixed | 断片の auto-confirm の辞退の条件が、unavailable・読めない・ほかの形を書いていない。断片を条件に合わせた。commit: 67f8959a |
| F2-11 | 独立-2 | low | no | self-inflicted | changelog | accepted | 断片の Summary に机上追跡、Validation に StateTemplateGateFieldsTest が無い |
| F2-12 | 独立-2 | advisory | no | self-inflicted | 依頼との突き合わせ | accepted | express の机上追跡の High がいつ blocking になるかが書かれていない |
| M2-1 | 方針メモ-2 | advisory | no | self-inflicted | auto-confirm | accepted | 安全策 4 の 1 回目の発火（auto-confirm のクラスタで high の巡が 2 回）。Opus・Fable とも案 1（続行し、条件を通す形の許可リストで閉じ、発動文を「かつ」にする）。割れた点は reviewer の条件の書き方（Opus: Round 1 で approved、Fable: reviews.md の全 Round 節に blocking なし）で、追記専用の artifact を根拠にできる Fable の側を採った。予算は条件 7 を発動文に取り込んで上限内に収めた。auto-confirm の撤去（使用 0/14）は PR 本文で問う。返事を待たずに推奨で進めた |
| F3-1 | 独立-3 | high | yes | self-inflicted | auto-confirm | accepted | 止める: 安全策 4 の 2 回目の発火で直していない。auto-confirm の条件 7 は「どの Round にも blocking が無い」しか見ず、reviewer が 2 回とも timeout した Round や Round 0 件でも通り、timeout の一括提示が人に届かない。build の前の条件が Requirements=approved を求めるので、レビューなしで build には入らない |
| F3-2 | 独立-3 | medium | yes | inherited | auto-confirm | accepted | 止める: auto-confirm で approved になったタスクが昇格すると、昇格の手順（task-sizing.md:273、state-machine.md:373・394）が Human Check Status を維持し、人の承認なしで standard を進む読み方が残る。safety net（task-sizing.md:243）とぶつかる |
| F3-3 | 独立-3 | low | no | self-inflicted | auto-confirm | accepted | 条件 7 の `<見出しの語>: なし` を見出しの字どおりに読むと突き合わせの出力と合わず、常に辞退する（安全側） |
| F3-4 | 独立-3 | low | no | self-inflicted | 説明 | accepted | PR 本文の抜粋が、番号の変わった「条件 8」を指したまま |
| F3-5 | 独立-3 | low | no | inherited | 説明 | accepted | commands/gdd-dev.md:30 の表の Auto-Confirm の行が条件の一部しか書いていない |
| F3-6 | 独立-3 | advisory | no | self-inflicted | 予算 | accepted | standard の実行時プロファイルの token の上限に tip で収まるかが確かめられていない（validate-plugin.sh は tip で通過） |
| F3-7 | 独立-3 | advisory | no | self-inflicted | 予算 | accepted | references の行数の上限 12177 と、この差分の −1 行が合っているか確かめられていない |
| M3-1 | 方針メモ-3 | advisory | no | self-inflicted | auto-confirm | accepted | 安全策 4 の 2 回目の発火（独立-3 の F3-1。auto-confirm のクラスタで high を含む巡が 3 回）。規則どおり推奨によらず「止める」の扱いで、F3-1・F3-2 を直さずに PR 本文の限界に書き、返事を待つ。続行のときの推奨は割れた: Opus は auto-confirm の判定を「requirements-gating の Round 1 で Step 8 の通常の承認に入ったとき」だけに結び付け、昇格のときは auto-confirm の承認を pending に戻す（1 commit）。Fable は express の Auto-Confirm モードをこの PR で撤去する（使用 0/14、約 10 ファイル・約 −100 行）。2026-10-30 にユーザーは「撤去する（案 2）」と答え、続行した（安全策 4 の数えは戻さない） |
| F4-1 | 独立-4 | medium | no | self-inflicted | 予算 | accepted | 撤去で references が 12101 行になり、上限を 12155 から 12177 に上げる必要が無くなったのに、上限・注記・断片・PR 本文の問いが上げたまま |
| F4-2 | 独立-4 | medium | no | self-inflicted | 依頼との突き合わせ | re-reported | F2-5 の再掲（express に design の観点の組を当てていない。PR 本文で確認待ち） |
| F4-3 | 独立-4 | low | no | self-inflicted | 依頼との突き合わせ | re-reported | F1-12 の再掲（Promotion Rules の AC の線を 4 件以上に変えた。PR 本文で確認待ち） |
| F4-4 | 独立-4 | low | no | self-inflicted | 説明 | accepted | README.md:150 の express の目安が 5-15 分のまま |
| F4-5 | 独立-4 | low | no | self-inflicted | 説明 | accepted | README の express の 15〜45 分に測った根拠が無く、quick (standard) の上限 40 分を超える |
| F4-6 | 独立-4 | low | no | self-inflicted | 説明 | accepted | README.md:113 の「Direct Intent の最速値」が表のどの値も指さなくなった |
| F4-7 | 独立-4 | low | no | self-inflicted | 説明 | accepted | README.md:312・328・331 の express の工程に requirements-gating が無い |
| F4-8 | 独立-4 | low | no | self-inflicted | 説明 | accepted | docs/references-archive/worked-examples.md:38・187-195 に --auto-confirm と Auto-Confirm Decline 記入例が残る |
| F4-9 | 独立-4 | low | no | self-inflicted | テスト | accepted | state-schema.json に auto_confirm が無いことを見る assert は、読むコードの無いキーの不在だけを見る |
| F4-10 | 独立-4 | low | no | self-inflicted | 説明 | accepted | 利用者が --auto-confirm を渡したときに撤去を伝える手順が entry-intent.md に無い |
| F4-11 | 独立-4 | low | no | self-inflicted | changelog | accepted | 断片の Affected Files と Validation が差分の変更ファイルと合わない |
| F4-12 | 独立-4 | advisory | no | self-inflicted | 説明 | accepted | gate-status-schema.md:24 の太字の主語「人の承認」が risk-low: を含む範囲より狭い |
| F4-13 | 独立-4 | advisory | no | self-inflicted | 説明 | accepted | phase-gate-prechecks.md:54-55 に空行が 2 つ続く |
| F4-14 | 独立-4 | advisory | no | inherited | changelog | accepted | 前の断片 20260920-typed-dispatch-templates.md:41 が旧テスト名を指す（既存の断片は書き換えない） |
| F4-15 | 独立-4 | advisory | no | self-inflicted | changelog | accepted | evidence: auto-confirm: を書いた進行中の steering の扱いが User Action Required に無い |
| F5-1 | 独立-5 | low | no | self-inflicted | 予算 | accepted | 上限を 12155 に戻した後も skill-body-budget.sh:374 の「余裕は 0」と 359-360 の「最後のラチェットの実測値」が残り、実態（12101 行）と合わない |
| F5-2 | 独立-5 | medium | no | self-inflicted | 説明 | next-pr | README.md:150・312・328・331 の express の所要時間（5-15 分）と流れ（要件レビューの段が無い）が、この PR で変えた 118 行・gate の順序と合わない |
| F5-3 | 独立-5 | low | no | self-inflicted | changelog | re-reported | F4-11 の再掲（断片の Affected Files が変更したファイルを全部挙げていない） |
