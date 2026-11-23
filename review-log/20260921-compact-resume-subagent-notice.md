---
lane: L1+
pr: 169
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user | - | 0 | 4 | 0 | 2026-09-22T00:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 04a460295638a0cf7cf826c33197e46bb85dee9d | 1 | 2 | 1 | 2026-09-22T01:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 216c42eb1a6fa51a648066f0896a8dad40093403 | 1 | 1 | 1 | 2026-09-22T02:35+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + user（安全策 4 の発火。独立-1 F2・独立-2 F1 で同じクラスタの high を含む巡が 2 回。ユーザーは選択肢 A〔PreCompact の固定文を revert し、テストの low を直して止める〕を選んだ） | 216c42eb1a6fa51a648066f0896a8dad40093403 | 0 | 1 | 0 | 2026-09-22T02:50+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 0bd795846e0bb0fe04e13b56af4ff9f366c574d1 | 1 | 0 | 1 | 2026-09-22T03:30+09:00 |
| PR後-1 | user（GitHub の PR レビュー） | 850c4a849f8ffd2dbe0c9ffb6872eefb2f37e2f6 | 0 | 2 | 0 | 2026-09-22T22:00+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | f8d6631f82faef80ea4d66b0ab703780d5ce0a9f | 0 | 1 | 0 | 2026-09-22T22:28+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 587e0a64ae0ecdb89d56cc4be728a33483e7692c | 1 | 1 | 1 | 2026-09-23T18:00+09:00 |
| 独立-6 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 80663a426c7706cf634c351e0a3de5472e700fb1 | 1 | 1 | 1 | 2026-09-23T19:30+09:00 |
| 独立-7 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 6e50144ebfebd4ddcaa1ebfcaa354f2a6b3d3809 | 0 | 0 | 0 | 2026-09-23T20:20+09:00 |
| 独立-8 | light-lane-independent-reviewer, 差分（無効化後）, model: opus（main 取り込み d9bbb071 の後。セッションに読み込まれた定義は 旧#173 前の版で、材料はファイルのパスで渡し、tip の定義に従って全行を読んだ） | d9bbb071a8513d2bf3be3fc0c1bd5d6ac1a25f11 | 0 | 1 | 0 | 2026-09-24T16:54+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | medium | no | self-inflicted | discriminator-survey | fixed | 「手がかりがどこにも無い」は言い過ぎ。PreToolUse と Stop の入力には agent_id がある（`Sa(o.session,Q(),d,o)`）。方針メモの限界の記述を「PreCompact と SessionStart には無い」に限定した |
| pm-2 | 方針メモ | medium | no | self-inflicted | wider-option | fixed | 広い側は (e) の mtime ヒューリスティックではなく (g)（消費を PreToolUse / Stop に移す）。(e) は main の compaction の 22% で取りこぼすため数値で却下。(g) を狭める理由（hooks.json の変更・検証できない前提・実害 11 件がすべて read-only のレビュアー）を HITL に載せ、ユーザーは A（(d)+(c)）を選んだ |
| pm-3 | 方針メモ | medium | no | self-inflicted | always-high-scope | accepted | 残る穴は `reviewer-common.md` § 常時 High の適用範囲 (b) に当たる。ユーザーの承認のもと accepted とし、PR 本文の限界の節の先頭に書く |
| pm-4 | 方針メモ | medium | no | self-inflicted | residual-holes | fixed | `delegatedObservation` の subagent（PreCompact だけ走り SessionStart が走らない）と、破棄された先読みの compaction でも印が残りうる。限界に追記した |
| pm-5 | 方針メモ | low | no | self-inflicted | fact-uncertainty | fixed | A-4（hook の時点で境界が未書き込み）はコードからの推定で、transcript の timestamp とは見かけ上ずれる。推定と明記した（headless の compaction は OAuth 期限切れで検証できない） |
| 独立1-F1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 順序の assert が恒真（固定文自身が `/gdd-dev resume` を含む）。比較先を `## GDD 自動復帰` と `サイクル上限` にした |
| 独立1-F2 | 独立-1 | high | yes | inherited | subagent-indistinguishable | accepted | subagent の compaction でも判定が発火し、印の消費と `AutoCycleCount` の加算が起きる。方針メモでユーザーが承認した限界（常時 High 適用範囲 (b)）。PR 本文の限界の節の先頭に書く |
| 独立1-F3 | 独立-1 | medium | no | inherited | paired-fix | fixed | PreCompact の systemMessage だけ固定文が無かった。固定文を lib/compact-resume.sh の `GDD_COMPACT_SUBAGENT_NOTICE` に移し、3 つの注入文で共有した |
| 独立1-F4 | 独立-1 | low | no | self-inflicted | test-power | fixed | host の `GDD_MAX_AUTO_CYCLES` が入ると resume の経路を踏まずに緑になる。`_env` で落とし、resume の見出しを pin した |
| 独立1-F5 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 変更断片にテストの件数を書いていた（CHANGELOG § Entry Template は件数を禁じる）。テスト名の列挙に直した |
| 独立2-F1 | 独立-2 | high | yes | inherited | subagent-indistinguishable | accepted | 独立1-F2 と同じ。常時 High（適用範囲 (b)）なので再掲にできず、巡の high に数える。安全策 4 の発火要因 |
| 独立2-F2 | 独立-2 | medium | no | self-inflicted | wrong-channel | fixed | PreCompact に足した固定文は受け手が違う。exit 0 の PreCompact の stdout は、復帰する側ではなく compaction の要約器へ `Additional Instructions` として渡る（Claude Code 2.1.261）。独立-1 F3 の修正を revert した |
| 独立2-F3 | 独立-2 | low | no | inherited | post-merge-seed | accepted | post-merge 継続の seed（`${HOME}/.claude/gdd-post-merge-continuation.json`）も subagent の SessionStart が消費して `rm -f` しうる。Opus は data-loss の medium 相当と見る。「止める」の選択により限界の節に書く |
| 独立2-F4 | 独立-2 | low | no | inherited | test-isolation | fixed | 同型の env 組み立て 2 ファイルでも host の `GDD_MAX_AUTO_CYCLES` を落とした |
| 独立2-F5 | 独立-2 | low | no | self-inflicted | test-diagnostics | fixed | assert の順序を入れ替え、経路違いの診断メッセージが出るようにした |
| pm2-1 | 方針メモ-2 | medium | no | self-inflicted | wrong-channel | fixed | 「systemMessage は model に届かない」は PreCompact には当てはまらない（stdout 全体が要約器の Additional Instructions になる）。要約器呼び出しは transcript に残らないので、transcript の 0 件は非到達の根拠にならない。限界の節に書く |
| 独立3-F1 | 独立-3 | high | yes | inherited | subagent-indistinguishable | accepted | 独立1-F2・独立2-F1 と同じ。ユーザーが安全策 4 の HITL で「止める」を選んだため直さない。限界の節の先頭に書く |
| 独立3-F2 | 独立-3 | low | no | inherited | test-isolation | accepted | `test_p0_p1_operational_hardening_contract.py:912` も host の `GDD_MAX_AUTO_CYCLES` を落としていない（4 本目）。「止める」により次の PR |
| 独立3-F3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | `lib/compact-resume.sh:14-16` が PreCompact の stdout の経路を検証済みの事実のように書いている。実際は本体コードからの推定。限界の節に書く |
| 独立3-F4 | 独立-3 | low | no | inherited | uncovered-channel | accepted | PreCompact のリマインダー本文には固定文が付かない。subagent の compaction の要約に継続指示が入りうる。限界の節に書く |
| 独立3-A1 | 独立-3 | advisory | no | self-inflicted | placement | accepted | 固定文の利用者が 1 ファイル 2 箇所になったので、共有 lib に置く理由が弱い。PR 本文に列挙 |
| 独立3-A2 | 独立-3 | advisory | no | self-inflicted | prompt-template | accepted | PR 本文の限界の見出しに経緯（accepted・止める）を書いたのをテンプレート外と報告された。PR 本文に列挙 |
| pr1-M1 | PR後-1 | medium | no | self-inflicted | notice-wording | fixed | 固定文が禁止だけで、肯定の「メインなら従え」が無い。compaction 後に自分がどちら側か決めかねた main が、先頭の禁止を採って自動復帰を落としうる。固定文を排他の 2 節にし、メインの節を先に肯定で書き、subagent の節から `/gdd-dev resume` を外した（ユーザーの指示で対応） |
| pr1-M2 | PR後-1 | medium | no | self-inflicted | test-power | fixed | 新規テストが固定文の部分文字列しか見ておらず、禁止の逆転・条件の削除・末尾の resume の削除を素通しする。全文を写し、`/gdd-dev resume` が固定文の外に 1 回だけ、見出し・上限の文の後にあることを pin した（ユーザーの指示で対応） |
| 独立4-F1 | 独立-4 | medium | no | self-inflicted | cap-notice-conflict | fixed | サイクル上限の警告は趣旨が逆で、「メインは以下に従うこと」の「以下」が「手動で /gdd-dev resume を実行してください」で終わる。上限の分岐は印を消費せず加算もしないため、従うと上限が bound として効かない。pr1-M1 の修正が入口。`reviewer-common.md:25` により warn の文言は § 常時 High の適用範囲外。ユーザーの指示でこの PR で直した（上限の警告から固定文を外し、誰にも再開させない禁止文にした） |
| 独立4-F2 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 変更断片の `#### Summary` が旧文言（「subagent なら従わない」）のまま。PR 本文の `目的` も同じ。`限界 3` の指す行番号も、コメント 4 行の差し込みでずれた（PR 本文の側は push 時の記載でそろえた）。独立4-F1 の修正で断片を書き直したときに Summary もそろえた |
| 独立4-A1 | 独立-4 | advisory | no | self-inflicted | injection-surface | accepted | 復帰の注入文の「以下」には state.md 由来の自由文 field が入る。明示の「従うこと」を前置きしたぶん、指示として扱われる度合いが上がる。同一信頼ドメインで実害は見ていない。PR 本文に列挙 |
| 独立5-F1 | 独立-5 | high | yes | inherited | cap-input-validation | fixed | `GDD_MAX_AUTO_CYCLES` を検証せずに `[[ -ge ]]` で比べる（`run-session-start-hook.sh:201,203`）。`1.5`・`40x` などでは比較が偽になり、上限を飛ばして発火・加算が続く。`abc` では set -u で hook が落ちる見込み。`AutoCycleCount: 08` は 8 進扱い。§ 常時 High 適用範囲 (b)。差分以前から。ユーザーの指示でこの PR で直した（数字だけの 10 進整数でない上限を倒し、先頭 0 を 10 進に正規化。RED のテストから） |
| 独立5-F2 | 独立-5 | medium | no | self-inflicted | test-power | fixed | 上限の警告のテストが否定の assert だけで、resume を促す文の追記や「メインは以下に従うこと」の前置きを素通しする。警告の全文を pin した（独立4-F1 の修正のテストとして、ユーザーの指示の範囲で直した。テストだけの変更で巡は無効にならない） |
| 独立5-F3 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 変更断片の User Action が、上限の警告には固定文が付かないこと・`AutoCycleCount` を戻す手段を書いていない。書き足した（同上。断片だけの変更） |
| 独立5-A1 | 独立-5 | advisory | no | self-inflicted | placement | accepted | 固定文の利用者が 1 箇所になり、共有 lib に置く理由が消えた。PR 本文に列挙 |
| 独立5-A2 | 独立-5 | advisory | no | inherited | stop-hook-conflict | accepted | 自律継続中は、Stop hook の継続の block（`gdd_stop_hook.py:1456,1491-1493`）が上限の禁止文と食い違い、上限が歯止めになるかは model 次第。PR 本文に列挙 |
| 独立5-A3 | 独立-5 | advisory | no | self-inflicted | subagent-cap | accepted | 固定文が付かなくなったので、委譲された作業の途中の subagent が上限の禁止文を受けて作業をやめうる（上限到達と subagent の compaction が重なったときだけ）。PR 本文に列挙 |
| 独立5-A4 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「安全策 1〜4 を通した」に根拠が無い。PR 本文を書き直した |
| 独立6-F1 | 独立-6 | high | yes | self-inflicted | cap-input-validation | fixed | 読めない上限を既定の 30 に倒したため、これまで上限として効いていた ` 5`・`+5`・`-1` が 30 まで緩む（bash の `[[ -ge ]]` はこれらを数として読む。実行で確認）。倒し先を 0（自動復帰しない）にした。count を設定値と 30 の間に置く RED のテストから |
| 独立6-F2 | 独立-6 | medium | no | self-inflicted | test-power | fixed | 上限側の先頭 0 の正規化を、どのテストも固定していない。`("8", "08")` を足し、正規化の行を消すと落ちることを確かめた |
| 独立6-F3 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 「整数でない値を 30 に倒す」の記述が、実装が受ける値（数字だけ）と合わない。倒し先の変更とあわせて、断片・コメント・テスト名を「数字だけの 10 進整数でない値」にそろえた |
| 独立6-A1 | 独立-6 | advisory | no | self-inflicted | style | fixed | 既定値 30 のリテラルが 2 箇所。倒し先を 0 にしたので解消 |
| 独立7-F1 | 独立-7 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の「数字だけでなければ 0」は、空（`GDD_MAX_AUTO_CYCLES=`）が 30 になることを書いていない。`+30`・` 30` などを設定している利用者は更新後に自動復帰しなくなるのに、User Action Required と Summary に対処が無い |
| 独立7-F2 | 独立-7 | low | no | self-inflicted | test-power | next-pr | 読めない上限のテストは count=10 で止まることしか見ず、倒し先が 1〜10 でも通る。警告の `GDD_MAX_AUTO_CYCLES=0)` を assert し、コメントの「count は設定値と 30 の間」を直す |
| 独立7-F3 | 独立-7 | low | no | self-inflicted | test-isolation | next-pr | `test_p0_p1_operational_hardening_contract.py:912` は host の `GDD_MAX_AUTO_CYCLES` を落とさない。読めない値が 0 に倒れるようになり、切り詰めの検査が空振りする host の値が増えた（限界 7 と同じ箇所） |
| 独立7-A1 | 独立-7 | advisory | no | self-inflicted | product | accepted | 読めない値でも警告は `GDD_MAX_AUTO_CYCLES=0` になり、意図した 0 と誤設定を区別しない。PR 本文に列挙 |
| 独立8-F1 | 独立-8 | medium | no | inherited | doc-claim | fixed | PR 本文の限界 2（subagent の SessionStart が post-merge seed を消費・削除しうる）は、取り込んだ 旧#174 で SessionStart の読み手が撤去されて解消した。PR 本文から削る（PR 本文の更新だけで、巡を無効にしない） |
| 独立8-F2 | 独立-8 | low | no | inherited | doc-claim | fixed | PR 本文の限界 7 の `test_p0_p1_operational_hardening_contract.py:912` が取り込みで 18 行ずれた。テスト名 `test_compact_resume_sanitizes_long_task_field` で指す（PR 本文の更新だけ） |
