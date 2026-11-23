---
lane: L1+
follow_up_of: 535
amends: 20261013-merge-intent-vs-merge-gate.md, 20260928-steering-multiple-followups.md
pr: 540
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | - | 0 | 0 | 0 | 2026-10-16 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 30f8e879 | 0 | 2 | 0 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e76d887e | 0 | 1 | 0 | 2026-10-16 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c7dc7f5e | 0 | 0 | 0 | 2026-10-16 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | f9507e9f | 0 | 1 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | product | fixed | Opus と Fable はどちらも、分岐を消す・止める前提の文書をこの PR で直す・merge gate の lib 移行は次の PR、を推す。足したのは、待つ場面のテストを削除せず止まる側に移す、AC の grep を消す 3 つの定数名に絞る、post-completion-pr-flow.md の差し戻しは通知の時点で PR がある前提に書き直す、未リリース断片 20261013 を amends: で直す、の 4 点。ユーザーへの確認は返事を待たずに本文に書き、推奨の案で進めた。commit: なし（方針） |
| F1 | 独立-1 | medium | no | self-inflicted | product | fixed | merge gate の block() の lib 移行を、確認なしにこの PR の後へ回した（依頼の原文では、旧#535 の「次の PR」とこの PR の「進めて」の 3 番目に入る）。この PR で移した。commit: 3b7bf023 |
| F2 | 独立-1 | medium | no | inherited | doc-claim | fixed | self-review-lanes.md:121、post-completion-pr-flow.md:87、independent-review.md:19、SECURITY.md:109 に、merge gate が止めると書いた行が残る。通知の形に直した。commit: 3b7bf023 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | TROUBLESHOOTING.md の 2 つ目の見出しは断片が参照していないのに変えず、本文と食い違う |
| F4 | 独立-1 | low | no | inherited | doc-claim | accepted | run-session-start-hook.sh:380 の案内文が「pre-push gate も steering-multiple で止まります」のまま |
| F5 | 独立-1 | low | no | inherited | doc-claim | accepted | hooks.json の (11) が「than it blocks」のまま |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | hooks.json の新しい (7)(9) の文が、実装より広く言っている（途中で終わる検査、opt-out でも出る通知） |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | post-completion-learning.md の新しい文が、通知の条件から not_applicable を落とした |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | post-completion-pr-flow.md の 202 行（解除は kill-switch のみ）と 203 行の扱いが食い違い、PR 本文の「同じ形」も合わない |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 通知を受けた時点で push・PR はもう済んだと断定している（失敗することもある） |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | test_merge_gate_ir_carry.py:146 のコメントと pushback テストの docstring が、消した判定を理由にしている |
| F11 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 新しい断片の Affected Files に amends した断片が無く、CONTRIBUTING.md の位置と Summary の対象に漏れがある |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 次の版の notes で、出てこない例外を「消した」と告げることになる |
| F13 | 独立-1 | low | no | inherited | doc-claim | accepted | 未リリースの 20261001 の断片 2 本が、review-wait-not-elapsed は待つ、のまま |
| F14 | 独立-1 | low | no | inherited | doc-claim | accepted | validate-steering-write.py・run-pre-pr-gate-hook.sh・run-pre-push-gate-hook.sh・push_command_parse.py などのコメントに、pre-push / pre-PR gate が止める前提が残る |
| F15 | 独立-1 | low | no | inherited | doc-claim | accepted | merge が通知つきで失敗した後の押し返しで、押し返しの文・手順 2・merge gate の通知が 3 通りの指示を出す |
| F16 | 独立-1 | low | no | self-inflicted | product | accepted | 確認待ち: 依頼の 4（文書に残る「止める」の記述の扱いの確認）のうち、言い回しの違う記述と docs/design・ADR の過去の記録を、確認なしに限界に回した。残す案で進め、ユーザーに確かめる |
| F17 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の「（review-log の amends:）」。次の巡の前に抜粋から外す |
| F18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の実測に、単位と再現のコマンドが無い |
| F19 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | self-review-lanes.md の 99・139・141・147・155 行に、gate が block する・止めると書いた文が残り、断片と PR 本文の「直した」と合わない。依頼の 4 の範囲に入るので通知の形に直した。commit: cb492a5f |
| F20 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | independent-review.md:14 の「前回の push 自体が block されて」。依頼の 4 の範囲に入るので直した。commit: cb492a5f |
| F21 | 独立-2 | low | no | inherited | doc-claim | fixed | README.md:489 が 3 つの gate を block するゲートとし、git push を止めると書く。依頼の 4 の範囲に入るので直した。commit: cb492a5f |
| F22 | 独立-2 | low | no | inherited | doc-claim | accepted | SECURITY.md:110 の state dir に書くものの一覧に、pre-push-gate-suppressed.log・pre-pr-gate-suppressed.log が無い |
| F23 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | run-merge-gate-hook.sh の 930〜936・1416〜1421 行のコメントと 2 つのテストの docstring が、無くなった HOME 未設定での set -u の落ち方を説明している |
| F24 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | lib/gate-notice.sh の見出しコメントが merge gate を別の実装として扱い、code を本文から切り出さないと書く |
| F25 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files に self-review-lanes.md が無い。F19 の修正に合わせて足した。commit: cb492a5f |
| F26 | 独立-2 | low | no | self-inflicted | product | re-reported | 依頼の 4 の扱いに対するユーザーの答えが依頼の原文に無い（F16 の確認待ちと同じ） |
| F27 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | ADR 2026-10-16-push-pr-gate-notice-only.md:32 が、merge gate の lib 移行は次の PR のまま |
| F28 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「行の形は変わらない」は、今の reason code に数字が無いから成り立つ |
| F29 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | HOME が無い環境で、直接呼ぶ 3 か所の exit code が 1 から 0 に変わったことが断片に無い |
| F30 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Validation に、merge gate の lib 移行の等価を保つ既存テストが書かれていない |
| F31 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | README.md:489 の「大半は block するゲート」が、14 本中 7 本で数と合わない |
| F32 | 独立-3 | low | no | inherited | doc-claim | accepted | skills/gdd-completion-check/SKILL.md:135 の「hook は最初に欠けた 1 行でしか止まらない」が残る（pre-PR gate は止めず、不足をまとめて通知する） |
| F33 | 独立-3 | low | no | inherited | doc-claim | accepted | docs/TROUBLESHOOTING.md:246 の「止める原因にならない」が残る |
| F34 | 独立-3 | low | no | inherited | doc-claim | accepted | run-session-start-hook.sh:380 の「pre-push gate も steering-multiple で止まります」が残る（F4 と同じ箇所） |
| F35 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | self-review-lanes.md:147 が Medium Disposition の invalid を全部 medium-disposition-missing とするが、実装は evidence-unparsable・evidence-malformed にも分ける |
| F36 | 独立-3 | low | no | inherited | doc-claim | accepted | lib/gate-notice.sh:2・10 が merge gate を使い手に数えず、自分自身と比べる文になっている（F24 と同じ箇所） |
| F37 | 独立-3 | low | no | inherited | doc-claim | accepted | run-pre-pr-gate-hook.sh:501、run-review-followup-nudge-hook.sh:101 と merge gate のテスト 3 本のコメントに「止める」が残る |
| F38 | 独立-3 | advisory | no | inherited | doc-claim | accepted | self-review-lanes.md:122 の見出しが「gh pr merge の解除条件」のまま（テストの定数が固定） |
| F39 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | self-review-lanes.md:99 から、gh pr create の前に検算する理由が消えた |
| F40 | 独立-3 | advisory | no | self-inflicted | style | accepted | independent-review.md:14 の新しい理由の文は、通知が出たことからレビュー不成立を導いており、前提が弱い |
| F41 | 独立-4 | medium | no | self-inflicted | product | accepted | 確認待ち: ADR 8 本と設計文書 2 本を、本文を直さず冒頭の 1 行の追記にした（依頼は「直す」）。Opus と Fable の推奨（今も止めると読める現在形の文を直し、Context の実測は残す）で進め、ユーザーに確かめる。推奨の案の commit: 774b044c |
| F42 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | テストのコメントで、当時の main・旧仕様の挙動を書いた過去形の文まで「通知していた」に置き換えた（当時は止めていた） |
| F43 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | self-review-lanes.md:147 で、空の recorded・note を evidence-malformed としたが、実装は evidence-unparsable になる |
| F44 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | test_merge_gate_ir_carry.py:146 が、消した autonomy_pushback の判定を読み手として挙げている |
| F45 | 独立-4 | low | no | inherited | doc-claim | accepted | テストの docstring 3 か所が、HOME 未設定で set -u により即死する古い説明のまま |
| F46 | 独立-4 | low | no | self-inflicted | product | fixed | テストのコメント 9 か所に、3 つの gate が止める前提の記述が残る（ユーザーはテストのコメントも直すと答えた）。直した。commit: c961a133 |
| F47 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | post-completion-pr-flow.md:203 の主節「PR 作成に進まず差し戻す」が、書き換えた括弧と食い違う |
| F48 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | test_pre_push_gate_activation_contract.py:125 が、観測できる出力を 3 つと数え、suppressed.log を落としている |
| F49 | 独立-4 | low | no | self-inflicted | style | accepted | test_merge_gate_followup_findings.py:540 が機械的な置き換えで意味が通らない |
| F50 | 独立-4 | low | no | self-inflicted | style | accepted | test_merge_gate_followup_findings.py:656 で助詞「が」が重なる |
| F51 | 独立-4 | low | no | self-inflicted | style | accepted | test_merge_gate_ir_carry.py:142 に余分な空白がある |
| F52 | 独立-4 | low | no | self-inflicted | style | accepted | test_merge_gate_hook_evidence_gate.py:63 の「→」の後の空白が落ちている |
| F53 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files で repo 直下の docs/ と plugin の docs/ が区別できず、gate-notice.sh が無い |
| F54 | 独立-4 | low | no | inherited | doc-claim | accepted | run-pre-pr-gate-hook.sh の通知の本文が「PR を作成してください」のままで、前置きの「更新してください」と並ぶ |
| F55 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | test_pre_pr_gate_contract.py:1175 のコメントが exit 2 でコマンドを止める経路を認めるが、SECURITY.md:275 と hooks.json (7) は例外なく止めないと書く |
| F56 | 独立-4 | advisory | no | inherited | test-power | accepted | HOME のテストは、subshell を外す mutation をもう捕まえない |
| F57 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に、Medium Disposition の reason code の表・adr-na-with-decision-handoff の条件・hooks.json (11) が無い |
