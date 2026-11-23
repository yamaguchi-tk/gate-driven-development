---
lane: L1+
pr: 旧#174
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user | - | 0 | 0 | 0 | 2026-09-22T10:40+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 7fae0f6b6da4394e5e74b5a5b99ffdfdaa6dcbbe | 0 | 0 | 0 | 2026-09-22T11:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 6b4b642cd4934d9cfb872d8997600832e02f810d | 0 | 0 | 0 | 2026-09-22T12:10+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | 6bffc013c81f00cda809d521cbae81be892d1e64 | 0 | 0 | 0 | 2026-09-22T12:55+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#174 review) | 4b13de76c847a6ca3d2af647e0226b5b756555f4 | 0 | 0 | 0 | 2026-09-23T17:52+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | post-merge-seed-path-mismatch | fixed | 発端は 旧#166 独立-2 の B3（`out-of-diff`）。**実測**: marker の書き手は `gdd_stop_hook.py::write_post_merge_continuation` → `lib/post_merge_continuation.py::state_path` で `<project root>/.claude/gdd-post-merge-continuation.json` に書くが、SessionStart の `_post_merge_seed_check` は `${HOME}/.claude/` を見ており実データでの注入は 0 件。他の読み手は 2 つ（UserPromptSubmit は相対パスで読み削除しない、stop hook の `resolve_block` は marker が無ければ即 None を返し post-merge 確認が済んだときだけ unlink する）。**何を変え何を変えないか**: SessionStart の読み手だけを消し、compact 自動復帰・Safe Resume・`[gdd:reboot]`・`[gdd:paused]`・複数 steering の `[gdd:warning]`・既定の案内・上の 2 読み手は変えない。**広い側／狭い側**: 候補は A（パスを project root に合わせる）と B（撤去）。Opus は B を推奨し、メインの案も B で食い違い無し。理由は (1) A では SessionStart が marker を `rm -f` するので、marker の存在を入口にしている stop hook の block lane と UserPromptSubmit の cue 注入が次のセッション開始で入口ごと消える、(2) marker は PR 作成時に `status: "pending_manual_merge"` で書かれ「マージ済みか」を持たないので PR が open の間ずっと `/gdd-dev resume` を注入する。**各 AC の閉じ方**: marker の置き場 2 通り（HOME 側・project root 側）＋ env 上書きの 3 入力を列挙して閉じる。**閉じない残り**: 無し（撤去なので入力空間を増やさない）。**延期・削除する完了条件**: SessionStart 由来の post-merge 自動継続は無くなり、マージ後の継続は UserPromptSubmit の cue と stop hook の block lane が担う。**QA の合否基準**: 新規 contract test 3 本が RED → GREEN、関係するテストと `validate-plugin.sh` が通る。**配線**: 新規部品は無く、直す読み手は出力点の構造 pin（`test_every_shipped_output_point_is_wired` の 6 → 5）と `GDD_POST_MERGE_SEED_FILE` を渡していたテスト群。**過去の教訓**: 「撤去は代替を残す」——`_run_post_merge_seed` が担っていた hook state dir の隔離は `_run()` 側の `test_run_helper_does_not_touch_real_hook_state_dir` が引き続き担い、撤去後に marker が生き残ることを project root 側のテストで固定した（残存と中身の一致まで assert する）。**ユーザーの決定**: 「撤去する（推奨）」 |
| A1 | 独立-1 | advisory | no | self-inflicted | changelog-fragment-stale-enumeration | accepted | 旧#167 の未リリース断片（`20260921-shadow-marker-followup.md:13`）が、3 段 sanitize を通る出力点の列挙に `post-merge` を含んだまま。両断片は同じ版の節に連結されるので、リリース後の CHANGELOG に出荷コメントに無い列挙が残る。reviewer も「既存エントリは書き換えない」（`CHANGELOG.md:180`）と逆向きなので対応不要とした。PR 本文に列挙 |
| A2 | 独立-1 | low | no | self-inflicted | doc-claim-overbroad | fixed | 断片とテスト docstring の「書き手が `<project root>/.claude/` に書くため注入は 0 件」という因果が、project root が `${HOME}` と一致する起動では成り立たない。因果を「project root が `${HOME}` と一致する起動を除いてパスが一致しない」に限定した |
| A3 | 独立-1 | low | no | self-inflicted | test-power-negative-only | fixed | `_assert_untouched` が `assertNotIn` 3 本と marker の存在だけで、どの出力枝を通ったかを固定していない。将来 SessionStart が別の理由で早期 exit する枝を持つと空振りで通る。`assertIn("gate-driven-development is available.")` を足した |
| A4 | 独立-1 | low | no | self-inflicted | red-evidence-overstated | fixed | 「3 入力で先に RED を確認した」のうち、project root 側の 1 本は撤去前も GREEN になる（旧経路は env 上書きか `${HOME}` 側しか読まない）。断片とテストのコメントを「RED は HOME 側と env 上書きの 2 入力。project root 側は再導入を止める pin」に書き分けた |
| A5 | 独立-1 | low | no | inherited | home-unset-unbound-variable | out-of-diff | `HOME` 未設定で hook を起動すると、superpowers 検出の未ガードな `"${HOME}/.claude/settings.json"` が `set -u` で落ち、additionalContext を出さずに終わる（`run-session-start-hook.sh:527`・`:539`）。reviewer は fail-open に当たらないと判断し `product`/low とした。同じクラスは `CHANGELOG.md:836` に「別 PR で対応する」として既に記録があり、本差分はそのうち 1 件（seed の既定値）を消して件数を減らしている。この PR では直さない |
| B1 | 独立-2 | low | no | self-inflicted | fragment-policy-violation | fixed | 独立-1 A4 の対応で断片の Validation 欄に「RED を確認したのは 2 入力」という巡の経緯と件数を書き足していた。`CHANGELOG.md` § Policy は、断片にレビューの経緯・巡の記録・テストの件数を書かないと定める。欄を検証の種類（追加・削除したテストの名前）だけに戻し、RED の範囲と pin の意図は PR 本文と本ファイルに移した |
| B2 | 独立-2 | low | no | inherited | stale-reader-name-in-comment | fixed | `gdd_stop_hook.py:816-821` と `test_stop_hook_bind_resolution_contract.py:589-593` が、消費不能な seed が溜まる根拠として撤去済みの読み手（`run-session-start-hook.sh`）を名指ししていた。根拠を実際の消費経路（`lib/post_merge_continuation.py` の `resolve_block` が merge cue と post-merge 完了の両方が揃ったときしか消さない）に書き換えた。block gate のガード自体は変えていない |
| B3 | 独立-2 | advisory | no | self-inflicted | limitation-rationale-mismatch | accepted | A1 を直さない根拠として書こうとした「既存エントリは書き換えない」は、対象がリリース済みの版の節なので未リリース断片には当たらない。根拠を「旧#167 の断片であり 1 PR 1 課題の規律で別 PR に回す」に差し替えて PR 本文に書く。直さない結論は変えない |
| B4 | 独立-2 | advisory | no | self-inflicted | test-anchor-branch-precision | accepted | 足した肯定アンカー `gate-driven-development is available.` は 5 出力点のうち 3 点に現れるので、枝までは固定しない（compact 復帰 2 点・paused 枝・superpowers 枝は弾く）。コメントが述べる空振り防止としては機能する。判別力の不足ではなく上限の話。PR 本文に列挙 |
| C1 | 独立-3 | advisory | no | self-inflicted | changelog-fragment-stale-enumeration | accepted | A1 と同じ件（旧#167 の未リリース断片が 3 段 sanitize の出力点の列挙に `post-merge` を残している）を、`origin: this-diff` として再報告。reviewer は「`CHANGELOG.md:22` の『既存エントリは書き換えない』は released エントリの規約で未リリース断片には当たらない」とし、1 PR 1 課題の規律で別 PR を勧めている。advisory なので直さず PR 本文に列挙 |
| C2 | 独立-3 | advisory | no | inherited | stale-example-in-limitations | out-of-diff | 旧#140 の未リリース断片（`changelog.d/20260918-issue123-always-high-resume-scope.md:42`）が、常時 High 適用範囲の限界の例として「post-merge の自動継続」「shadow marker の判定」を挙げている。前者が SessionStart 側を指すならこの PR で存在しなくなる。ただし UserPromptSubmit の cue レーンを指す読みもでき、断片からは決まらない。正本（`references/reviewer-common.md`）は挙動名を列挙していないので修正不要。PR 本文に列挙 |
| D1 | PR後-1 | low | no | self-inflicted | commit-type-fragment-mismatch | accepted | 断片は `type: minor`、先頭 commit は `feat(gdd)!` で揃っていない。版数を決める `release.py` は断片の `type` だけを読み、commit message は読まない。撤去した経路は実データで注入 0 件なので minor が正。揃えるには merge commit だけが許可された repo で履歴を書き換えて force push する必要があり、ユーザーの判断で直さない。旧#166（`8813fa49`）も同じ組み合わせで main に入っている |
| D2 | PR後-1 | low | no | self-inflicted | stale-reader-name-in-comment | fixed | `test_session_start_context_json_control_chars.py` の docstring 7 行目が「compact 経路・post-merge 経路は入力の段階で `tr -d` 済み」のまま。SessionStart の post-merge 経路はこの PR で撤去したので「compact 経路」だけにした（61594e8a。docstring のみで巡は無効にならない） |
