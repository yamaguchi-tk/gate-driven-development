# ADR 逐語アーカイブ: W-36 タスク儀式コスト削減（20260904-w36-task-ceremony-cost）

> 2026-10-16 追記: steering の size 上限は、今は書き込みを止めずに通知する（`plugins/gate-driven-development/changelog.d/20261016-steering-size-notice.md`）。kill switch `GDD_STEERING_SIZE_DENY` と、size の deny counter・降格の連動は無くなった。本文の「deny」は当時の挙動である。

## ADR-1: 未作成ファイルへの `Write` は size 判定を継続する（2026-09-05, T-3 実装時）

- Context: design § 実装契約 2 (c)「対象ファイルが存在しない → 算出不能」を字句どおり適用すると、未作成 `state.md` への超過 `Write`（case1/9/11/14/25）が deny されず、AC-5 の主経路が fail-open になる
- Decision: `Write` は全文置換で post-write サイズが `len(content.encode())` で確定するため、ファイル未存在でも `existing=0` として判定を継続する。差分系 `Edit` / `MultiEdit` は従来どおり算出不能（非 deny、case16）
- Why: 契約テスト（design § テスト方針）を正とした。算出不能の趣旨は「post-write サイズが決められない」であり、`Write` はこれに該当しない
- Consequences: 新規 steering ファイルの初回 `Write` でも上限を超えれば deny される（意図どおり）。design.md § 実装契約 2 を更新済み

## ADR-2: deny 本文の数値は桁区切りなし（2026-09-05, T-3 実装時）

- Context: `_size_deny_description` の `{post_size:,}` は case9 の `assertIn("20000", body)` と不一致
- Decision: `{post_size}`（桁区切りなし）に統一
- Why: design § 実装契約 4 は「固定文 + 数値のみ」で桁区切りを規定していない。テストの grep 可能性を優先
- Consequences: なし（表示のみ）

## ADR-3: 「未作成」と「算出不能」を分離する（2026-09-06, T-3 impl-gate Round 1 M-2）

- Context: design § 実装契約 2 (d)「`stat()` が `OSError`」を実装は Write でだけ不履行にしていた。(c) 未作成と (d) 例外が同じ `None` に潰れ、Write は権限エラー時も `baseline=0` に落ちて判定を継続していた
- Decision: `path.stat()` を直接呼び、`FileNotFoundError` のみ「未作成」、その他の `OSError` は `tool_name` によらず算出不能（非 deny）。ADR-1 の Write 継続は**ファイル未作成時のみ**。regular file でない対象は未作成扱い（`stat.S_ISREG`）
- Why: (d) を Write で不履行にすると、上限超過ファイルへの縮小 Write が `post > 0` で deny され、AC-5 の唯一の出口が塞がる。算出できないなら判定しない、が本 design の一貫した扱い
- Consequences: `stat()` が失敗する対象への超過 write は size deny されない（既存 deny は動く）。case 36 が固定（root 環境では skip）

## ADR-4: size 算出の入力面を `extract_content_chunks` と揃える（2026-09-06, T-3 impl-gate Round 1 M-4）

- Context: size 算出は `old_string` / `new_string` のみ読み、`newText` / `replacement` は算出不能→無言 allow に落ちていた（gate 実測: `new_string` rc=2 / `newText` rc=0）。design が列挙した算出不能 4 つに無い 5 件目
- Decision: `NEW_STRING_KEYS=("new_string","newText","replacement")` / `OLD_STRING_KEYS=("old_string","oldText","oldString")` を定数化し、`_first_str` / `_edit_delta` で Edit / MultiEdit に適用。「別名は対象外」と観測範囲に書いて逃げる案は採らない
- Why: どの deny が効くかが payload キー名で変わるのは機械強制として成立しない。算出不能の集合は design の 4 つに閉じる
- Consequences: 別名 payload でも size deny が効く（case 37）。`oldText` / `oldString` は未観測の別名で対称性のために置いた
- Follow-up（impl-gate Round 2 M-R2-1、2026-09-06）: 初回適用は `new_string` 系だけで、`extract_content_chunks` が受理する `Write` の `contents` と edits 内 `content` が漏れていた（実測: `contents` の超過 Write が rc=0 の無言 allow）。`NEW_STRING_KEYS` に `content` を追加し `Write` 分岐を `_first_str(tool_input, ("content", "contents"))` にして対称化し、`case37b` で固定した。これで「算出不能の集合は design の 4 つに閉じる」が実際に成立する

### ADR-4 Follow-up 訂正（2026-09-06 completion review M-2）

- impl-gate Round 2 で `content` を追加し「閉包が成立」と記したが、`extract_content_chunks` の top-level 受理集合にある `contents` が `NEW_STRING_KEYS` に無く、`Edit` + `contents` が無言 allow だった（completion reviewer 実測 rc=0）。Remediation 旧#2 で `contents` を追加し、閉包を実態と一致させる。根本原因は Architecture Debt Finding（キー集合の二重定義）で、後続 PR で `extract_content_chunks` に定数を参照させて構造的に閉じる

### ADR-4 Follow-up 訂正 2（2026-09-06 独立セルフレビュー H-1）

- `extract_content_chunks` の edits 内リテラル tuple に `contents` が無く、`MultiEdit` + `contents` は size が deny を算出するのに chunk が空で `main()` が allow に落ちていた。top-level / edits 内とも `NEW_STRING_KEYS` を参照させて二重定義を廃止し、chunk 空でも `size.deny` 成立時は emit 経路へ回す。case 37b に `MultiEdit/contents` を追加。相対パスは size 非対象（L-2、case 42b）

## ADR-5: size deny を既存カテゴリの escape hatch から独立させる（2026-09-06, PR 旧#37 Copilot Finding 1）

- Context: 「`reasons` 非空時は size を record も emit もしない」設計のため、上限超過 write に既存違反（email 等）を同梱すると、既存カテゴリの escape hatch が 3 回目を allow する一方で size counter は 0 のままとなり、size deny を無期限に迂回できた（Copilot 実測、修正前 `[2,2,0,2,2,0]`）
- Decision: size decision を既存違反の有無と独立に評価・記録する。既存カテゴリの降格時も size deny が成立していれば deny を維持し、size は自身の 3 回周期でのみ降格する。size counter は size が実効ゲートになった回だけ進める
- Why: size deny は本 PR 唯一の機械強制であり、他カテゴリの ping-pong 対策がその強制を落とす面になってはならない。size 自身の無限ループ回避のため独立した 3 回周期の出口は残す（縮小 write は常に allow という一次の出口も維持）
- Consequences: 超過 + 既存違反が続く場合の周期は `[2,2,2,2,0,2]`（5 回目に降格）。deny 本文は両理由と両 suffix を含む。`_emit_with_violations` の複雑度は `_record_existing_denies` / `_clear_existing_denies` / `_size_reason` / `_size_holds_after_hatch` の抽出で吸収。case 39〜41 が固定

## ADR-6: `..` 正規化後の `.steering` 配下再確認（2026-09-06, PR 旧#37 Copilot Finding 5）

- Context: `is_steering_path` は resolve 前の文字列で判定するため `/x/.steering/../state.md` が steering target 扱いとなり `/x/state.md` への大きな Write が size deny されていた
- Decision: `_steering_size_target` で resolve 後の parts に `.steering` が無ければ size 非対象（算出不能）。既存 deny category の判定（`is_steering_path`）は変えない
- Why: size deny の対象は実在する `.steering/` 配下 3 ファイルに限る設計。既存判定を変えると既存 deny の対象集合が動くため触らない
- Consequences: case 42 が固定。`..` 経由で `.steering/` 配下に着地するパスは従来どおり対象
