# ADR: `## Verification` 節の受理文法を閉じた行種の列挙へ統一する

- **日付**: 2026-09-08（決定・PR 作成時に蒸留）
- **状態**: Accepted
- **Supersedes**: `docs/adr/2026-09-06-done-guard-verification-header.md`
- **関連**: `plugins/gate-driven-development/CHANGELOG.md` の `[0.42.0]` entry / `plugins/gate-driven-development/hooks/scripts/lib/done_guard.py` / `plugins/gate-driven-development/references/self-contained-contract.md` / `.steering/20260908-verification-closed-grammar/design.md`

## Context

`docs/adr/2026-09-06-done-guard-verification-header.md`（以下「旧 ADR」）は done guard Check 2 の判定を 2 つの不変条件へ還元した。

1. **未完了の検出は無条件・列位置非依存**。`pending` / `fail` と完全一致するセルを持つ行は、形（表 / list / 散文）・インデント・引用・凡例・補助表を問わず必ず未完了として報告する
2. **完了の受理は canonical schema に一致する行だけ**。status 列を 1 つに確定できた行の値が許容値のときだけ検証済みと認め、確定できない検証行は「status 判別不能」で block する

旧 ADR 自身のマージ後、この 2 不変条件を土台にした独立レビューが 9 ラウンド（R9〜R19相当）走り、**high 34 件**を検出・修正した。しかし修正のたびに別の fail-open が開く状態が収束しなかった（列位置の候補探索順、header 境界の貼り替えタイミング、インデント除外の対象範囲、凡例除外と検出の前後関係など、絞り込みを 1 つ足すたびに別経路が開いた）。

根本原因は個々の判定規則の誤りではなく、**仕様側の欠落**だった。`skills/gdd-ac-verification/SKILL.md` は Verification 行が持つべき**フィールド**（method / status / evidence / notes）だけを規定し、行の**シリアライズ形式**（表か list か、区切り文字、header の有無、装飾やラベルの許容範囲）を規定していなかった。一方で `references/self-contained-contract.md` は「閉じた文法」を暗黙に宣言していたが、実装（`done_guard.py`）は歴史的な実データ（過去のセッションが実際に書いた表記ゆれ）に合わせて**8 通りの行形**を受理するよう継ぎ足されていた。**未定義の形式に対して正しいパーサは原理的に書けない**。規則を締めるたびに「まだ受理すべき既存形」を落とすか「まだ塞ぐべき迂回路」が残るかのどちらかになり、これが 9 ラウンドの高頻度 high 検出という症状として現れていた。

## Decision

`## Verification` 節が受理する行の文法を、以下の**閉じた行種の列挙**に統一する（正本は `references/self-contained-contract.md` / `skills/gdd-ac-verification/SKILL.md` の文法ブロック。本 ADR には複製しない）。

    section_line := blank | empty_marker | header | separator | data_row
    data_row     := ac_row | evidence_row | refactor_row

受理するのは「空行 / `- なし` / canonical header / canonical separator / 4 列 canonical data 行（3 形）」のみで、それ以外の行種（list 行・引用行・インデント行・装飾 status・注記付き status・ラベル形・日本語 header 語・全角パイプ・外側パイプ省略など）はすべて schema 違反として block する。

この決定に伴い、次を実施した。

- **AC-8**: `done_guard.py` から列位置推定・補助表判定・凡例除外・注記位置規則・header 境界規則に関わる **16 シンボル**（`_status_column` / `_method_columns` / `_BARE_ID_CELL` / `_ROW_ID_CELL` / `_ROW_ID_PREFIX` / `_BARE_NUMBER_CELL` / `_is_verification_row` / `_VERIFICATION_ID` / `_is_verification_skip_line` / `_LEGEND_PREFIX` / `_verification_line_shape` / `_ANNOTATED_STATUS` / `_BRACKET_UNFINISHED` / `_can_be_header` / `_verification_schema` / `_has_unfinished_status`）を削除した。名前を変えて等価な推論を残していないことは、削除対象クラスを入力として与えると必ず violation になることを 1 形ずつ assert する契約テストで担保する
- **旧 ADR 不変条件 (1)（未完了検出は無条件・列位置非依存）を後継の 1 本（status 列は常に固定 2 列目）へ置き換える**。これが安全なのは、**節に重なる fence を schema 違反にしたこと（AC-7）を条件**にしているためである。旧不変条件 (1) は「`pending` をどんな形で書いても検出する」ことで fence による隠蔽（findings F-12）を含む迂回路を塞いでいたが、AC-7 が fence 自体を違反にしたことで、その迂回路は別の層で塞がれた。条件を欠いたまま (1) を外すと、閉じた fence で `pending` 行を包む迂回路が残る
- **legacy parser への一時 fallback は作らない（D8）**。fallback は「開いた文法」を第 2 正準形として温存し、受理を 1 形に閉じるという本決定の目的をそのまま無効化する。解除導線は block メッセージの canonical 3 行と `## Verification Notes` への逃がし先、最終手段は `touch ~/.claude/gdd-hooks-disabled`（done guard 全停止）

### 却下した代替案（Rejected Alternatives）

- **案 B（list 行にも同じ status 列確定を全面適用し表 / list を完全対称にする）**: 却下する。新規 block 件数が案 A と同数（127 件、diff 0 / measured_at 2026-09-08T16:42:59+09:00）で、移行コストが決め手にならない一方、対称化それ自体が新しい安全性を追加しない
- **案 C（fail-open を温存し文書だけ整備する）**: 却下する。AC-4〜AC-11 / AC-13 / AC-19 のほぼ全体が消え、9 ラウンドで観測された fail-open の再発サイクルを止める効果が無い
- **legacy parser への一時 fallback（環境変数での新旧切替）**: 却下する（D8）。切替の存在自体が「どちらの文法が正か」を再び曖昧にし、閉じた文法という決定の意味を失わせる

## Why

独立レビュー 9 ラウンドで high 34 件を検出・修正しても収束しなかった。個々の指摘は毎回正しかったが、**直したそばから別の迂回路が開く**という構造が変わらなかった。原因はパーサの実装品質ではなく仕様側にあった。`SKILL.md` はフィールドの意味（method / status / evidence / notes）だけを定義し、行のシリアライズ形式を定義していなかった。`self-contained-contract.md` は文法が閉じていることを前提にした記述を持ちながら、実装は過去の実データに合わせて 8 形（表 header 有無・list・引用・インデント・全角パイプ・装飾・ラベル・注記）を受理するよう継ぎ足されていた。**受理形が仕様として確定していない限り、それを正しく判定するパーサは書けない**。本決定は、仕様（contract / SKILL）を先に閉じた文法として確定し、実装をその文法の 1 対 1 の写像にすることで、この症状を構造的に止める。

## Consequences

**唯一の block→done 方向の挙動変化**: `notes_only_status_word_is_detected` — 旧実装の `_has_unfinished_status` は全セルを列位置非依存で走査していたため、notes 欄に書かれたリテラル `pending`（例: `| method=ac:AC-1 | pass | fail | - |` の evidence / notes セル）も未完了として block していた。新文法は status 列を固定 2 列目としてのみ判定するため、この行は通る。旧 ADR の不変条件 (1)「未完了の検出は無条件・列位置非依存」に直接触れる変更であり、本 ADR で明示的に上書きする。impl-gate R6 はこれを「fail-open ではなく受容可能」と判定した。理由は、status 列に `pass` を書く以上の迂回力をこの挙動が持たないため（迂回したい行為者は最初から status 列に `pass` と書けるので、notes 欄の `pending` を無視してもコストが増えない）。旧実装も注記付き形（`pending（未実施）`）は元々 ALLOW にしていたことと整合する。実コーパス実測（`measured_at: 2026-09-09T05:59:52+09:00` / 母集団 459）でこのクラスの件数は **block→done: 0 件**であり、影響ゼロを確認済み。

**done→block 方向の挙動変化**（新たに block されるようになったクラス。詳細は `design.md` § 5 を根拠表とする）: 装飾 status（`` `pass` `` / `**pass**`）/ 注記付き status（`pass（2026-08-30 …）`）/ 全角空白・NBSP・zero-width 入り status / 制御文字入り status / `status=` ラベル形 / `method:` コロン形 / 日本語 header 語（`ステータス` / `状態` / `判定`）/ list 行 / 引用行 / インデント行 / 外側パイプ省略・全角パイプ / 凡例 list / H3 見出し・散文 / 5 列 ROW-ID 表・list / 節に重なる fence（`section_fence` / `fenced_heading`、AC-7）。実コーパス実測: **母集団 459 / done→block 131 件**（内訳: 文法由来 130 件 / fence 由来 0 件 / 両方 1 件 / n/a 0 件）。

**移行コスト**（時点依存のスナップショット。CHANGELOG `[0.42.0]` § Migration Cost が正本）:

- `measured_at: 2026-09-09T05:59:52+09:00`
- `integration_ref: origin/main`
- 母集団: **459**
- done→block: **131**（内訳: 文法由来 130 / fence 由来 0 / 両方 1 / n/a 0）
- block→done: **0**
- 導出: `scripts/measure-done-guard-drift.py`

**AC-20 の残余リスク**: `method=security_evidence:*` 行の手書き禁止は、block メッセージと contract の文言だけで伝える規範であり、guard は検査しない。

**AC 検証行の下限（2026-09-10 追記 / AC-9 第 5 形）**: 最終差分への独立レビューで、`method=ac:` 行が 1 件も無い節（`security_evidence` 行・`refactor-checkpoint` 行だけの表）でも done が通ることが判明した。external verifier が upsert する行だけの節は、悪意もミスも無く仕組み上ふつうに起きる。Check 2 は `method=ac:` 行が 1 件以上ある節だけを受理するよう改めた。行文法は変えず、節の基数制約として足した。第 5 形に未完了/失敗行があれば件数を併記する。実コーパス再実測（`measured_at: 2026-09-10T17:13:48+09:00` / 母集団 455）で done→block は 129 件のまま増えなかった。新実装単独で done を返すファイルが 0 件のためで、コーパスがまだ新文法へ移行していない時点のスナップショット性質であり、恒久的な性質ではない（上記の 459 / 131 は 2026-09-09 時点の値）。

**AC カバレッジの責務（2026-09-10 追記）**: Check 2 は `## Verification` 節の行の形だけを入力にすると決めている（スコープ判断）。そのため、AC 検証行を他の節へ移すことと消すことは guard から見て区別できず、走査対象を節外へ広げても移動しか塞げない。requirements.md の AC 集合と照合すれば原理的には検出できるが、本 PR の範囲外とした。2026-09-10 時点で、AC カバレッジ（requirements.md の各 AC が `## Verification` に検証行を持ち、その status が pass であること）を機械的に強制している層は無い。`scripts/lint-ac.py` は未検証の AC を `--strict` なしでは警告に留め、tasklist 全体から AC 参照を拾い、status を見ない。AC Trace Ledger Gate は skill 段の gate で機械強制ではない。Check 2 は agent が書くファイルを読むので意図的な偽装は防げず、担うのは書き忘れや事故の防止である。「AC 検証行 1 件以上」は形の下限であり、AC カバレッジを保証しない。

**撤回条件と後続対応**: 次のいずれかが起きたら、節外の検証行を検出する判断へ戻る。(1) 実コーパスで `## Verification` の外に canonical data 行を持つ tasklist が観測された（2026-09-10 時点 0 / 455）(2) lint-ac の未検証 AC がエラー化され、参照抽出が `## Verification` 節に限定され、status を見るようになった (3) done 通過後に AC が未検証だったインシデントが記録された。後続対応として、requirements.md の AC 集合 × `## Verification` の `method=ac:` 行 × status の 3 項照合を別 task で扱う（後続対応は PR 本文を参照。Issue は未起票）。

**参照**: `.steering/20260908-verification-closed-grammar/design.md`（§ 1 閉じた文法の正本定義、§ 2 D1-D8 の設計判断、§ 5 インターフェース全量カバレッジ、§ 12 Review Rounds）、`docs/adr/2026-09-06-done-guard-verification-header.md`（被 supersede）。
