---
lane: L1
pr: 633
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 598f8094 | 0 | 2 | 0 | 2026-11-03 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 7ccfd08d | 0 | 1 | 0 | 2026-11-03 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2e30c992 | 0 | 1 | 0 | 2026-11-03 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 8d005837 | 0 | 1 | 0 | 2026-11-03 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | eeb971e0 | 0 | 3 | 0 | 2026-11-03 |
| 独立-6 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 8f215763 | 0 | 2 | 0 | 2026-11-12 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 3992b39e | 0 | 0 | 0 | 2026-11-12 |
| 独立-8 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 1298996c | 0 | 2 | 0 | 2026-11-12 |
| 独立-9 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | d7124d79 | 0 | 1 | 0 | 2026-11-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 触ったファイルに件数・比率の実測値が残り、PR 本文と断片の「書き直した」と合わない。残りを意味の文に書き直した。commit: 7ccfd08d |
| I1-2 | 独立-1 | medium | no | self-inflicted | intent | fixed | 依頼の ①④ から外れ: 計画書の番号の無いファイルに残る運用の実測値（前の PR で書き直した値と同じものを含む）を扱っていない。群の全ファイルを探し直して書き直した。commit: 7ccfd08d |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 別の形の計画書の ID（`PR-W3`・`#W29-H1`・`AC-W1-*` など）と、由来を確かめていない `G-NN` が残る。PR 本文に残した形を書く |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 同じ測定を CONTRIBUTING.md は「数倍」、テストは「倍ほど」と書く。どちらも「2〜3 倍ほど」にした。commit: 7ccfd08d |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 見出しの取りこぼしと同型の欠陥を「bind の不具合と同型」と書き直していた。commit: 7ccfd08d |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 件数を外した後の「これより多い」が指す数が無い。commit: 7ccfd08d |
| I1-7 | 独立-1 | low | no | self-inflicted | style | fixed | 番号を外した後に閉じ括弧だけが残っていた。commit: 7ccfd08d |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文と断片が、assert の失敗時の msg と `--help` の説明文が変わることを書いていない。断片と PR 本文を直した。commit: 7ccfd08d |
| I1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「テスト時間の ADR」からどの ADR かを辿れない。docs の群の PR でファイル名を決めるときに合わせる |
| I1-10 | 独立-1 | advisory | no | inherited | doc-claim | accepted | review-log のファイル名と branch 名に計画書の番号が小文字で残る。実在するファイルへの参照なので、PR 本文に残した形として書く |
| I1-11 | 独立-1 | advisory | no | inherited | doc-claim | accepted | PR 旧#83 のレビューの巡の数（7 巡）が残る。運用の件数ではなく、自由文の判定が収束しなかった経緯の説明として残す |
| I2-1 | 独立-2 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: 群に「N 件」「N 本」の形の運用の件数が残る（gdd-pr-roots.sh の merge の本数など 6 か所）。commit: 2e30c992 |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 同じ計測を script は「差が出た」、テストは「1 件差」と書く。テストをそろえた。commit: 2e30c992 |
| I2-3 | 独立-2 | low | no | self-inflicted | intent | fixed | 依頼の ① から外れ: 比率を外さずに「2〜3 倍ほど」の幅を足していた。意味の文にした。commit: 2e30c992 |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 書き直した文に指摘の番号（High-1）が残り、`PR-W7` を外したことが断片に無い。番号を外し、断片に書き足した。commit: 2e30c992 |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | transcript.py の書き直しが、isMeta を外す理由ではなく false positive の内訳の話になっていた。commit: 2e30c992 |
| I2-6 | 独立-2 | advisory | no | inherited | product | next-pr | 旧#627 の後に足された agents/gdd-requirements-precheck.md に運用の実測値が残り、群の分け方ではどの PR も扱わない |
| I3-1 | 独立-3 | medium | no | self-inflicted | intent | fixed | 依頼の ② から外れ: ハイフンの無い計画書の ID（`#W29-H1`・`PR-W1`・`PR-W1a`・`PR-W3`・`AC-W1-*`・`AC-W2-*`）が tests に残る。意味の文にした。commit: 13cd7ebc |
| I3-2 | 独立-3 | low | no | self-inflicted | intent | fixed | 依頼の ① から外れ: コードの性能・時間の計測値（正規表現の所要時間・レイテンシの増加率・timeout の根拠の ms・テストの件数）を残していた。相談役と Fable の推奨（依頼の字面どおり）で、閾値・設定値・入力の大きさは残して意味の文にした。commit: 8d005837 |
| I3-3 | 独立-3 | low | no | self-inflicted | intent | fixed | 依頼の ① から外れ: 「十数回」「千行を超え」「未完了 27 件」「32 タスク中 2 完了」「半数を超え」の形の運用の値が残る。意味の文にした。commit: 13cd7ebc |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の「残した」が、`G-NN`・fixture の中身・ファイル名と branch 名の番号を書いていない。commit: 13cd7ebc |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | gdd-pr-roots.sh で標本の大きさを外した後、「どれも承認の下だった」が全称の主張に読める。測った範囲に限った。commit: 13cd7ebc |
| I3-6 | 独立-3 | advisory | no | self-inflicted | style | accepted | 「より大きく膨らんだ」が、時間とともに大きくなったように読める（CONTRIBUTING.md と test_agent_tool_allowlist_contract.py） |
| I3-7 | 独立-3 | advisory | no | self-inflicted | style | accepted | transcript.py の書き直しで、何を付けたか（isMeta:true）が抜け、表記もそろっていない |
| I3-8 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | pr-review-anticipation-tokens.sh の「実測で見つかった型」は、測ったものではなく作業中に起きた出来事 |
| I3-9 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | unittest の `-v` で出るテストの説明文（docstring の 1 行目）も変わるが、PR 本文は書いていない |
| I3-10 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | 断片が、利用者から見えないコメントの変更の細目（ファイル数・`PR-W7`）まで書いている |
| I3-11 | 独立-3 | advisory | no | inherited | doc-claim | out-of-diff | 書き直していない文に、前のレビューの指摘番号（`Medium-4`・`H-2(b)`）が残る |
| I4-1 | 独立-4 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: 群に運用の比率と件数（「merge の deny の半数近く」「871 passed」「+45 test」）が残る。意味の文にした。commit: eeb971e0 |
| I4-2 | 独立-4 | low | no | self-inflicted | intent | fixed | 依頼の ① から外れ: `pytest.ini` に、書き直したテストと同じ値（16 コア・負荷平均 40 前後）が残り、ほかの断片・docs の実測の値は行き先を書かずに後回しにしていた。`pytest.ini` を書き直し、残りは次の群の PR で扱うと PR 本文に書いた。commit: eeb971e0 |
| I4-3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 断片の「同じ文にあった AC 番号・指摘の番号も外した」に対し、書き直した文に `IG-6`・`BL-1`・`AC-20`・`AC-8`・`AC-6` などが残る |
| I4-4 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | `lint-requirements-duplication.py --help` の説明文も変わるのに、PR 本文が `lint-hitl-required-fields.py` だけと書いていた。PR 本文だけ直した。commit: なし（PR 本文） |
| I4-5 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 値を語にしたとき強さが変わった（merge-gate-binding.sh の「持ち時間の多く」、test_pre_push_gate_contract.py の「1 秒に近い」） |
| I4-6 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | steering_size.py の書き直しが「実サイズより大きな書き込み」という成り立たない文になった |
| I4-7 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | hook の起動時間について、test_merge_gate_followup_findings.py:825 と _merge_gate_support.py・_timing_budget.py の書き方が逆に読める |
| I4-8 | 独立-4 | low | no | inherited | doc-claim | accepted | CONTRIBUTING.md の addopts の引用に `--maxprocesses=8` が抜けている |
| I4-9 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | test_root_branch_guard_contract.py:464 の「この長さ」が指す長さが前の文に無い |
| I4-10 | 独立-4 | advisory | no | self-inflicted | style | accepted | _git_fixture.py の余分な空白と、test_hitl_lint_marker_sync_contract.py:3 の半角の読点 |
| I5-1 | 独立-5 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: test_hitl_lint_marker_sync_contract.py に同じ形のテストの件数（872 test）が残る。commit: c76d20a5 |
| I5-2 | 独立-5 | medium | no | inherited | intent | fixed | 依頼の ① から外れ: 群の tests にテストの本数・実行結果（既存 41 test・全 1002 test・1341 tests・190 test・全 15 本）と、同じ文の指摘の番号が残る。挙がった箇所を意味の文にした。テストの表の件数（`既存 10 行` など）は残し、test 以外の単位で書いた件数は限界として PR 本文に書く。commit: c76d20a5 |
| I5-3 | 独立-5 | medium | no | inherited | intent | fixed | 依頼の ① から外れ: test_hooks_kill_switch.py の「16 並列」と手元の環境の名前が残る。commit: c76d20a5 |
| I5-4 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | pytest.ini の書き直しが、測った 1 組（16 と 8 worker）より広い主張になった。テストの言い方にそろえた。commit: c76d20a5 |
| I5-5 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 「deny の半数近く」を「多くを占めた」にして主張が強くなった。commit: c76d20a5 |
| I5-6 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Summary に pytest.ini が無い。commit: c76d20a5 |
| I5-7 | 独立-5 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の tests の本数が古い（92 本に直した）。commit: c76d20a5 |
| I6-1 | 独立-6 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: test_stop_hook_e2e_block_content.py に、stop hook の docstring と対になるセッション ID と再掲の回数が残る。群の `session <hex8>` を全部外した。commit: f3de3347 |
| I6-2 | 独立-6 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: test_stop_hook_validate.py にセッション ID と運用の回数が残る。commit: f3de3347 |
| I6-3 | 独立-6 | low | no | self-inflicted | intent | fixed | 依頼の ① から外れ: test_timing_budget_contract.py に時間の計測値（~0.001s）が残る。commit: f3de3347 |
| I6-4 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | test_pre_push_gate_contract.py の書き直し「1 秒に近い」が元の計測の大きさとずれる |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | steering_size.py の書き直し「実サイズより大きな書き込み」が自己矛盾する |
| I6-6 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 断片の Affected Files に、`--help` に出る lint-requirements-duplication.py が無い。commit: 8adadadf |
| I6-7 | 独立-6 | low | no | self-inflicted | intent | fixed | 依頼の ② から外れ: G-NN を確かめずに残した。CHANGELOG-archive で計画書の札と確かめ、群の G-NN・R9-N・計画書のファイル名と、同じ文の指摘の番号を書き直した。commit: 6d7847bc |
| I6-8 | 独立-6 | advisory | no | self-inflicted | style | accepted | _git_fixture.py の「より ずっと」に余計な空白 |
| I6-9 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | test_hooks_wiring_new_events_contract.py に hook の本数のずれの数が残り、test_hooks_kill_switch.py と扱いがそろわない |
| I6-10 | 独立-6 | advisory | no | inherited | doc-claim | fixed | 件数の無いセッション ID（constants.py・test_stop_hook_stop_reason_unit.py）が残る。I6-1 と同じ形として外した。commit: f3de3347 |
| I7-1 | 独立-7 | low | no | self-inflicted | intent | fixed | 依頼の ① から外れ: 書き直した行に回数（「百回を超えて」「4 ラウンド」）が残る。commit: 380613ae |
| I7-2 | 独立-7 | low | no | inherited | doc-claim | accepted | run-stop-failure-hook.sh の「`$(cat` を持つ 5 hook 共通」が今の本数と合わない |
| I7-3 | 独立-7 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が、外した `G-NN` を全部計画書の札と書く（一部はレビューの指摘番号）。I7-4 の直しで断片を書き直した。commit: 380613ae |
| I7-4 | 独立-7 | low | no | self-inflicted | intent | fixed | 依頼の語より広げて外した番号（G-NN・R9-N・計画書のファイル名・セッション ID）を、広げた分として書いていない。断片を直し、PR 本文にも書く。commit: 380613ae |
| I7-5 | 独立-7 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files の本数を差分巡の範囲では確かめられない（main が全差分で数えて照合済み） |
| I7-6 | 独立-7 | advisory | no | inherited | doc-claim | accepted | test_gdd_scenario_eval_contract.py と fixture にセッション ID の形の値が残る。fixture を扱う群で決める |
| I7-7 | 独立-7 | advisory | no | self-inflicted | style | accepted | run-notification-hook.sh と test_notification_hook_contract.py の、札を外した後の括弧書きが同じことを繰り返す |
| I8-1 | 独立-8 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: gdd_stop_hook.py の docstring に、テスト側で外した回数と同じ事実（百回を超えて）が残る。commit: aff18bea |
| I8-2 | 独立-8 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: run-notification-hook.sh と osascript-arg-lint.sh に「4 ラウンド」が残る。commit: aff18bea |
| I8-3 | 独立-8 | low | no | self-inflicted | intent | fixed | 依頼より広げた分（W-NN と、同じ文にあった AC 番号・指摘番号・task の ID）が PR 本文の「依頼より広い」に出ていない。PR 本文に足す。commit: なし（PR 本文） |
| I8-4 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 断片の「残した」の限定が 3 つに掛からない。commit: aff18bea |
| I8-5 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 断片に、読み手が辿れない「依頼」の語を足した。commit: aff18bea |
| I8-6 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「依頼より広い」の行で句点が抜け、2 文がつながる。commit: なし（PR 本文） |
| I8-7 | 独立-8 | advisory | no | self-inflicted | style | accepted | test_stop_hook_e2e_block_content.py の括弧の中が直前の文を繰り返す |
| I9-1 | 独立-9 | medium | no | self-inflicted | intent | accepted | 決着（11-12、ユーザーが別の PR で外すと決めた）: レビューの巡・再発の回数（「3巡連続」「4 回連続」など）が群に 13 行残る。実測の値に数えるかは依頼から 2 通りに読め、形も開いている。指摘・task の番号と一緒に別の PR で扱う案で進め、PR 本文で問う |
| I9-2 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | run-notification-hook.sh の「AC-16 で繰り返した」に目的語が無い |
| I9-3 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | gdd_stop_hook.py の括弧書きが主文の繰り返しで、「長い session では」と狭く書く |
| I9-4 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | 断片の本数が差分の後も合っているか未確認（main が数え直して一致を確かめた） |
| I9-5 | 独立-9 | advisory | no | inherited | doc-claim | accepted | gdd_stop_hook.py の「約 60 行」を実測の値に数えるか |
| I9-6 | 独立-9 | advisory | no | inherited | intent | accepted | 11-02 に確認済みの 4 種類と、この群で新しく広げた種類が PR 本文で分かれていない |
