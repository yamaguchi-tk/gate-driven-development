# ADR: state.md canonical field reader の「空値行スキップ」を規則で統一する

- **日付**: 2026-09-04（決定）/ 2026-09-05（PR 作成時に蒸留）
- **状態**: 採用
- **関連**: `plugins/gate-driven-development/CHANGELOG.md` `[0.40.4]` / `plugins/gate-driven-development/references/state-schema.json` の `canonical_line_form.value_less_line_skip`

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

## Context

`state.md` の canonical field（`- Resume From: <値>` の形）を読む reader は、区切り文字の後ろが空の「書きかけ行」を現在値として返し、最初の一致で走査を打ち切っていた。

このため `- Resume From:` という空値行がファイルの先頭側に 1 本あるだけで、後続に正しく書かれた `- Resume From: gdd-test-driven-development` があっても reader は空文字を返す。`gdd_validate_active_state_fields` の存在判定はこの空文字を「field 欠落」と解釈し、SessionStart / UserPromptSubmit hook が `[gdd:blocked]` を出して**正しく書かれた task の resume を塞いでいた**（2026-09-04 に実機で再現。`rc=1` / `missing=Resume From`）。

同型の reader は複数あり、どこまで揃えるかが最初の論点になった。

## Decision

**「区切り文字の後ろが（各実装が既に行っている trim + backtick 除去まで適用して）trim 後に空の canonical 行は現在値ではない。走査を継続して次の canonical 行を見る」という 1 次元（以下 R-1）を、規則に該当する reader へ入れる。**

適用範囲は**数え上げではなく規則**で定義する。

> hook / skill / command が runtime で呼ぶ経路にあり、`state.md` の canonical field を共通受理形 `- <Field>: <値>` / `<Field>: <値>` で読む reader

現時点でこの規則に該当し、実際に揃えたのは 6 実装（`detect-steering.sh:gdd_extract_doc_field` / `gdd_task_binding.py:_field` / `setup-gdd-loop.sh:parse_field` / `validate-steering-write.py:state_field_value` / `collect-gdd-telemetry.py:extract_field` / `gdd_stop_hook.py:resume_from_value`）。既知リストは**完全性を主張しない**。揃えなかった reader は理由と残る非対称の向きとともに `references/state-schema.json` の `excluded_known` に記録する。

行の選択規則は変えない。「最初の**値付き**一致」であり、最終行採択にはしない。

## 却下した代替案

- **最終行採択に変える**: `Route In Progress` 専用 reader（`tasklist_parse.py:select_route_in_progress`）が最終行採択なので揃える案があった。却下する。他 5 実装の消費者はすべて「最初の一致」を前提にしており、選択規則を変えると R-1 と無関係な挙動変化が広範囲に混ざる。R-1 は 1 次元だけ足す変更に留める。
- **母集団を「N 実装」という数で書く**: 当初は requirements に「同型 reader は 5 実装」と書いていた。却下する。新しい同型 reader が 1 本見つかるたびに受入条件が不成立になり、design gate が同じ欠陥クラスで 2 回連続 bounce した。母集団は規則で定義し、除外記録は「見つかったものの記録」として完全性を主張しない形にした。
- **3 lint（`lint-resume-integrity.py` / `lint-worktree-provenance.py` / `lint-state-tasklist-continuity.py`）も揃える**: 却下する。これらは hooks / skills / commands のどこからも runtime で呼ばれておらず（呼び出し元は pytest・`validate-plugin.sh`・replay fixture のみ）、ユーザーの resume を止めたり merge を通したりする経路ではない。加えて `FIELD_PATTERNS` がインデント行と `*` bullet を受理する = 行頭アンカーの次元で既に本体と別規約であり、空値行の 1 次元だけ揃えても規約は揃わない。同じ 1 行を 3 本へ複製するのは repo の DRY 方針にも逆行する。
- **merge gate の `PR URL` 経路に characterization test を置く**: 却下する。`- PR URL: <他 PR>` 1 行だけのファイルは本変更の前から素通りしており、R-1 が解除するのは「書きかけ行があると偶然 block されていた」ケースだけである。gate 境界そのものは変わらない。ここにテストを置くと穴を契約として固定してしまい、将来この境界を見直す際の足枷になる。
- **Codebase Health Gate の baseline を書き換えて通す（ratchet）**: 却下する。`gh pr create` を止めていた high 11 件は、baseline の数値を緩めるのではなく実際に解消する方針を人間が選んだ。

## 受容した挙動変化

R-1 が取り除く「遮蔽」は、設計意図ではなく欠陥の副作用が偶然 fail-closed 側に倒れていたものである。したがって遮蔽が消えて到達可能になる既存の挙動は、ガードを追加せず受容し、隠さず開示する。内訳は `CHANGELOG.md` `[0.40.4]` の `#### Changed` を正本とする（件数での網羅は主張しない）。

方向が質的に違う 1 件だけここに再掲する。`gdd_detect_active_steering` の terminal 除外は、他が「missing → present」なのに対し「active → none」へ動く。空値行の後に `Next Action: done` がある state をこれまでは active として拾っていたが、R-1 適用後は terminal と判定して除外し、当該 steering への `[gdd:blocked]` の context 注入も止まる。enforcement が消える方向の変化であるため、独立して記録する。

## 判別力の担保

規約を足すだけの変更は、テストが「実装をなぞっただけ」になりやすい。判別力は変異注入で実測して固定した。

- awk の空値スキップ分岐を削除 → 14 failed
- 6 実装のうち `gdd_task_binding.py:_field` だけを旧規約へ戻す → 13 failed
- 採用行を「最初の値付き一致」から「最後の値付き一致」へ変える → 3 failed

いずれも隔離コピー上で実行し、復元後に green へ戻ることも確認している。

## Consequences

- `state.md` に書きかけの空値行を残しても、後続の値付き行が現在値として読まれる。逆に「空値行を置いて一時的に gate を止める」運用は成立しなくなる。もともと意図された運用ではなく遮蔽バグの副作用だった。
- 揃えなかった reader との非対称は残る。向きと理由は `references/state-schema.json` の `excluded_known` が正本。
- 当初は人間承認済みの Scope Amendment として `gdd_stop_hook.py` の lib 3 module 分割と `CHANGELOG.md` の 3 分割を含んでいたが、`origin/main` から 100 commit 以上離れて構造衝突したため、**競合解消時にどちらも本 PR から外した**（分割は別 PR が現在の main に対して実施する）。本 PR に残るリファクタは `gdd_task_binding.py` / `collect-gdd-telemetry.py` の複雑度 helper 抽出のみ。ロールバック単位は **PR の merge commit 1 個の revert**。
- **測った入力集合**: GDD managed worktree 群と repo-local worktree 群の steering markdown 1698 ファイル。このうち空値 canonical 行は 26 本 / 11 ファイル実在したが、いずれも後続に値付き行が無いため、本修正で出力が変わるファイルは 0 件だった。この観測範囲の外については主張しない。本修正は「再現手順が確立した fail-closed 誤爆の芽を潰す」ものであり、実データ上の効果は発生時にしか観測できない。
