---
lane: L1
pr: 224
follow_up_of: 220
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1d82ac8fb785b589dd2eb4b8bce88bdfef839759 | 0 | 0 | 0 | 2026-09-28T22:02+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 9f7c17a4ec6145affcfc6b58bdee5ea5f5a2827b | 0 | 0 | 0 | 2026-09-28T22:24+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 38c7b58043c9a5e6cb15cdc93c128ba26cb52949 | 0 | 1 | 0 | 2026-09-28T23:29+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| H1 | 独立-1 | low | no | self-inflicted | test-power | fixed | 否定形の S-2b・S-3 を残し、対になる肯定形 (b-2) だけを消していた。S-1〜S-6 も文書の語の不在だけを見るので外し、.sh を見る S-7・S-8 だけを残した。節コメントと docstring を合わせた（0ea95b2e） |
| H2 | 独立-1 | low | no | self-inflicted | test-power | fixed | runner の frontmatter の effort を正本とつなぐ唯一の検査が消えていた。frontmatter の effort を resolver の resolve_effort と照合する assert を足し、resolver の effort を書き換えると落ちることを確かめた（ac5fe17c） |
| H3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring・コメントが消したテストの検査を主張していた。残るテストだけの記述に直した（ac5fe17c、b5d2162f） |
| H4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 文書の語だけを見るテストが残っていた（test_p1、ADR の見出し・語、RELATIONS の比較、scenario eval の文書の assert）。消し、実在確認とコードを読む assert だけを残した（ac5fe17c、b5d2162f） |
| H5 | 独立-1 | low | no | self-inflicted | style | fixed | 呼び出し元の無い read_repo_root と、メソッド間の空行 2 行が残っていた（b5d2162f、ac5fe17c） |
| H6 | 独立-1 | low | no | self-inflicted | style | fixed | _root_branch_guard_support.read の呼び出し元が 0 になっていた。消した（fd489659、断片 658772b1） |
| H7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの変更断片 5 本が、消したテストを名指ししている。断片は後続の PR で書き換えられないので、PR 本文の限界に書き、リリースの dry-run で直す |
| I1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界の断片一覧が、テスト名を名指しする 5 本に限られ、消したテストの検査内容を述べる断片（20260919-light-lane-review-routing.md ほか 4 本）が抜けていた。断片は書き換えず、PR 本文の限界の一覧に足してリリースの dry-run で直す |
| I2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | test_typed_dispatch_templates_contract.py:33 のコメントが、model も TIER_TO_MODEL と照合すると読めるが、そのテストが resolver と照合するのは effort だけ。model の照合は test_subagent_type_and_model_follow_the_phase_tier にある。follow_up_of がある PR の差分巡の low なので accepted にし、PR 本文の限界に書く |
| I3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | test_verification_closed_grammar_release_notes_contract.py の module docstring が、消した ADR の見出しの検査を挙げたまま。accepted にし、PR 本文の限界に書く |
| I4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | test_verification_grammar_single_source_contract.py の module docstring が、署名の範囲を S-1〜S-8 と書いたまま。accepted にし、PR 本文の限界に書く |
| I5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | test_light_lane_review_routing_contract.py の module docstring の結びの句が、消した 差分との関係 の検査の理由のまま。accepted にし、PR 本文の限界に書く |
| I6 | 独立-2 | low | no | self-inflicted | style | accepted | test_gdd_scenario_eval_contract.py の test_fable_remaining_contract_docs_cover_runtime_ux_guards が、文書の assert を外した後もその名前のまま。accepted にし、PR 本文の限界に書く |
| I7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 文書とコードの assert が混ざる test の扱い（文書の assert だけを外す・丸ごと残す）が同じファイルの中で揃っていない。PR 本文の advisory に書く |
| I8 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 変更断片の Summary にヘルパーの削除を巡で書き足した。戻すのも巡ごとの編集になるので直さない。PR 本文の advisory に書く |
| K1 | 独立-3 | medium | no | self-inflicted | test-power | accepted | fixed-models.md の formal_gate・light_task・remediation_loop の行と、cursor.md・codex.md の independent_review の行を resolver と照合するテスト（クラス A/D）を消していた。足した resolve_effort の assert はコード同士の比較で、その代わりにならない。main の取り込みで巡が無効になった後の差分巡の blocking でない medium で、follow_up_of があるので accepted にし、PR 本文の限界に書く。次の PR で resolver を読む形で戻す |
| K2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | docstring・クラス名・メソッド名・コメントが、消したテストの契約を書いたまま（release_notes・typed_dispatch・host_route・last_handoff・merge_gate_followup・remediation_loop・scenario_eval）。独立-2 の I2〜I6 と重なる。accepted にし、PR 本文の限界に書く |
| K3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文と断片の「文書の語・文だけを assert する」という対象の定義が、コードのテキストも連結して見ていた 4 メソッドの削除・メソッドの中の文書 assert だけの削除と合わない。PR 本文の定義を直し、残る混在メソッドを限界に書く。断片は accepted |
