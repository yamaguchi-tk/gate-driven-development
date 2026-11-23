---
type: minor
---

#### Summary

X-53 対策 A〜D（HITL の AI 推奨が要件を矮小化するのを止める）の作り直し。前回の PR 旧#83（closed、未マージ）は「広い側を採用したか」「数値根拠が示されたか」を日本語の自由文から判定しようとして 7 巡収束しなかった（`gh api repos/<owner>/<repo>/pulls/83/comments` に実測が残る）。今回は自由文判定を全廃し、`- 既定範囲: 広い側 | 狭い側` / `- 狭める根拠: <key>=<数値>` という固定フィールドの行の形・隣接性だけを見る受理文法に置き換えた（PR 旧#65 の `## Verification` 受理文法と同じ構え）。

#### Added

- `references/human-check-template.md` / `human-check-template-compact.md` の承認ポイント / 判断ポイントに固定フィールド `既定範囲`（広い側 | 狭い側）と `狭める根拠`（実装コスト= / 誤検知実測= / 他AC波及= のいずれかにキー直後の数値）を追加。承認ポイントの 6 要素を 8 要素に拡張
- `references/human-check-template.md` § 承認ポイントの固定フィールド受理文法（`<!-- decision-scope-grammar:begin/end -->`）を新設。lint はこの文法だけを受理する
- `scripts/lint-hitl-decision-quality.py` に 4 系統の新規決定論的チェックを追加
  - `既定範囲:` の値域（広い側/狭い側 の完全一致）と `狭める根拠:` のペアリング（直後行固定、狭い側は数値必須、広い側は「該当なし」完全一致）
  - `既定範囲` の行そのものが承認ポイント内に無い（丸ごと欠落）ケースの検出。`- 無回答時のデフォルト:` の直後から次の承認ポイントの終端マーカーの手前までを見る（欄順が「無回答時のデフォルト → 既定範囲 → 狭める根拠」であるため、判断に影響する前提・却下した代替案とは逆向きの区間になる）
  - `判断に影響する前提` / `却下した代替案`・`採用しない案` の欠落検査。`- 無回答時のデフォルト:` の出現を承認ポイントの終端マーカーとして使い、見出し・番号書式に一切依存しない（件数 0/1/複数を同じ経路で扱う）
  - `完了条件の変換` 見出しそのものの欠落検査（承認ポイント構造を持つ文書に限る）と、テーブルの「扱い」列（具体化/延期/削除/追加/未解決の閉じた 5 値）を見て、延期・削除の行に `取りに行かない:` を、0 件なら固定行 `延期・削除: なし` を要求。「延期・削除: なし」の存在検査は出現（occurrence）ごとに次の出現までの区間へスコープする（文書全体への substring 検査だと複数出現時に取り違える）
- `tests/test_hitl_decision_scope_contract.py`（新規、50 テスト）。PR 旧#83 の 7 巡・24 件のレビューコメントのうち再現可能なものと、本 PR の独立レビュー（1 巡目）で見つかった 2 件の fail-open、PR 旧#86 への PR レビュー（3〜5 巡目、下記）で見つかった 11 件の fail-open、push 前セルフレビュー（6 巡目、下記）で見つかった 6 件の fail-open を退行テストとして固定した
- `references/human-check-template.md` / `human-check-template-compact.md` の承認ポイント / 判断ポイント節に `承認ポイント数: <N>` の宣言フィールドを新設（`DECLARED_POINT_COUNT_RE`）。件数の突き合わせをテーマ行の番号書式からの推定ではなく著者の明示宣言で行う（下記 6 巡目 F5 の対応）

#### Changed

- `human-check-template-compact.md` § ズレ確認: `完了条件の変換` を「後戻りが大きいものだけ」の対象から外し無条件必須にした（他 3 項目は従来どおり任意）。前回計測で変換表が 2/10 しか出ていなかったのはこれが原因
- `human-check-template.md` § 必須ルール ルール6: `完了条件の変換` を「作り方の重要判断」と同じ条件（後戻りが大きいものだけ）から外し無条件必須にした。compact.md・lint の実挙動とは元から無条件だったため、full 正本の文言だけが条件付きのまま取り残されていた（PR 旧#86 レビュー指摘 Medium: doc-claim）
- `tests/checks/skill-body-budget.sh` の行予算 ratchet を更新（ユーザー承認済み。方針: 既存の pre-existing 超過分とこの PR の追加分をまとめて 1 回で引き上げる）
  - `references/*.md` 合計行数 cap: 11927 → 11958 行。うち 8 行は本 PR 以前から main に存在していた pre-existing 超過（この PR の変更とは無関係）、残りがこの PR の固定フィールド追加分
  - `lint-runtime-budget.py` の `--max-standard-estimated-tokens`: 45381 → 45405。`human-check-template-compact.md` への固定フィールド追加による増分（等価削減を 2 巡試し 888→945 token まで圧縮した残りをユーザー承認で吸収）
  - 同じ値を `tests/checks/lint-scripts-functional.sh` の smoke test 呼び出しにも同期

#### Affected Files

- `references/human-check-template.md`
- `references/human-check-template-compact.md`
- `scripts/lint-hitl-decision-quality.py`
- `tests/test_hitl_decision_scope_contract.py`（新規）
- `tests/checks/skill-body-budget.sh`
- `tests/checks/lint-scripts-functional.sh`

#### User Action Required

- なし。新しい固定フィールドは今後 AI が human check を生成する際のテンプレート規約であり、既存の完了済み HITL 記録を書き換える必要はない

#### Validation / Eval Impact

- 追加 test: `tests/test_hitl_decision_scope_contract.py`（新規 50 件）
  - A/B: `既定範囲: 広い側|狭い側` の値域完全一致、`狭める根拠` のペアリング（直後行固定・広い側は「該当なし」完全一致・狭い側は `実装コスト=` / `誤検知実測=` / `他AC波及=` のいずれかにキー直後の数値必須）。値の表記ゆれ・順序入れ替え・行を離した配置・部分一致語がいずれも fail することを確認
  - `既定範囲` / `狭める根拠` の行そのものを丸ごと書かない場合に reject されること（独立レビュー 1 巡目 finding 1 の退行テスト。`_decision_scope_errors` は出現 0 件なら素通りする設計のため、別途の存在チェックが要る）
  - C/D: `判断に影響する前提` / `採用しない案`・`却下した代替案` の欠落検査が `- 無回答時のデフォルト:` を終端マーカーとして件数 0/1/複数のいずれでも同じ経路で動くこと。承認ポイントが 1 件だけ・複数件・見出しの言い回しが違う場合でも同じ結果になること（PR 旧#83 の「2 見出し曖昧性」「単一項目スキップ」「文書全体スコープへのフォールバック」を退行させる fixture を含む）
  - `完了条件の変換` 見出しそのものを書かない場合に reject されること（独立レビュー 1 巡目 finding 2 の退行テスト。X-53実測2「変換表が2/10 しか出ていなかった」と同じ失敗の再現。承認ポイント構造を持たない簡易 HITL は対象外のまま）
  - `完了条件の変換` テーブルの「扱い」列（具体化/延期/削除/追加/未解決）を見て、延期・削除の行がある場合は `取りに行かない:`、0 件なら固定行 `延期・削除: なし` を要求。テーブルの行順・列の空白ゆれでも同じ判定になること
  - fail-open 側の 3 ケース（block すべき入力が allow になる／例外で guard 全体が落ちる／判定できないときに通ってしまう）を固定フィールドごとに用意し、いずれも block 側に倒れることを確認
  - 自由文免疫: 既定範囲・狭める根拠・判断に影響する前提の値そのものに何を書いても（空文字・長文・PR 旧#83 で実際に指摘された言い回しを含む）、値域・隣接性・件数以外を一切見ないこと
  - 既存 fixture `tests/checks/hitl-decision-quality-lint.sh` の OK fixture（30 秒判断の簡易書式、承認ポイントの番号項目を持たない）は `無回答時のデフォルト` を含まないため新規チェックの対象外であることを確認し、zero false-FAIL を実測で確認した
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`: `2824 passed, 4 skipped, 16665 subtests passed`、失敗 0（push 前セルフレビュー対応（6 巡目）を含む最終差分）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: EXIT 0。新規 BLOCK 追加なし、`hitl-decision-quality-lint` / `hitl-population-tokens` / `skill-body-budget` を含め全 OK
- `references/*.md` の line budget: 実測 11958 / cap 11958（変更前は pre-existing 超過込みで 11935。独立レビュー 2 巡目・PR レビュー 3・4 巡目・6 巡目セルフレビューの doc-claim 対応分はいずれも同節内の文言差し替え・等価圧縮で吸収し、cap は追加で動かしていない）
- `lint-runtime-budget.py` の standard token 見積り: 実測 45400 / cap 45405（cap は変更前 45405 のまま。6 巡目で追加した `承認ポイント数:` 宣言フィールドの説明文は、同じ compact 正本内の別行を等価圧縮して吸収した）
- 独立レビュー（実装文脈を渡さない read-only diff レビュー）
  - 1 巡目（main からの全差分対象）: High 2 件（いずれも fail-open）、Medium 1 件、Low 0 件。High 2 件は本 fragment の上記追加チェックで修正済み（fail-open 側の再現テストを先に書いて RED を確認してから直した）
  - 2 巡目（1 巡目の sha からの差分対象。実装文脈を渡さない別の読み手が、1 巡目の修正差分を再度 read-only で検証）: 1 巡目の High 2 件が実コード・CLI・境界値の両方で閉じたことを確認済み。新規 High 0 件・Medium 1 件（正本の受理文法節が新設 2 チェックを記述していない doc drift）・Low 1 件（既定範囲の丸ごと欠落チェックに複数ポイント回帰テストが無い）。Medium・Low とも同じ push で吸収した（`human-check-template.md` § 承認ポイントの固定フィールド受理文法 に追記、`test_second_point_cannot_drop_scope_field_entirely` を追加）
  - 3 巡目（PR 旧#86 への PR オーナー自身の PR レビュー、`gh api repos/<owner>/<repo>/issues/comments/5665007763` に実測。実装文脈を渡さず PR tip の diff だけを見た読み手）: High 3 件・Medium 2 件・Low 1 件（不採用と明記）
    - High 1（`_decision_item_field_errors`）: 2 件目の承認ポイントが `- 無回答時のデフォルト:` を丸ごと欠くと、1 件目の区間に無音で吸収され 8 要素検査が走らなかった。レビュー指摘どおり番号見出しの意味解析には戻さず、承認ポイントの開始行数（`THEME_LINE_RE`、番号の値は見ない）と終端マーカーの出現数を比べる件数バランスチェックで境界を検査し、不一致なら個別項目のチェックへ進まず reject するよう修正。`無回答時のデフォルト` を一度も使わない簡易 HITL（Yes/No 形式の番号リストのみ等）はこのチェックの対象外のまま据え置いた（既存 2 テストがこの簡易書式に依存していたため、実装中に regression として検出・修正した）
    - High 2（`_decision_area_start_index`）: 30秒判断の地の文 `**判断ポイント**: 完了条件と検証範囲が意図通りか。` が `判断ポイント` という語を含むため、`label in line` の部分一致で承認ポイント本体より前から検査区間が始まっていた。見出し記法（`^#{1,4} `）を要求する正規表現に変更し、地の文を除外
    - High 3（`_completion_table_rows` / `_completion_table_errors`）: 3 つの独立した fail-open を含んでいた。(a) ヘッダー行の直後に区切り行が無い壊れた table が「data 0 件」に化けて `延期・削除: なし` で素通りしていた → 区切り行（`|---|---|...|`）の妥当性を検証し、無効なら `None` を返して reject する。(b) `扱い` 列は「閉じた5値」と changelog は主張していたが実装は `延期`/`削除` 以外を検査していなかった（未知の値、例: 見送り、が素通り） → `HANDLING_CLOSED_VALUES`（具体化/延期/削除/追加/未解決）との完全一致を検査。(c) `取りに行かない:` はどのセルに書いても満たしたことになっていた → 「承認してほしい点」列（`TAKE_NOT_COLUMN_INDEX`、行の4番目のセル）だけを見るよう限定
    - Medium 1（doc-claim）: 上記 Changed の `human-check-template.md` ルール6の無条件化で対応
    - Medium 2（test-power、marker-sync 命名規約 drift）: 1 巡目から継続する既知の限界として据え置き（下記「受け入れた限界」を参照）。今回のレビューでも「マージ前確認」の必須項目には含まれておらず、新しい実害の指摘も無かったため、本 push では見送った
    - Low（changelog の「30 テスト」表記が tip では 31 だった、というレビュー時点の指摘）: 情報のみで「マージは止めない」と明記されていた。本 push で最終テスト数を実測し直し、上の Added 節・本節の件数を 37 に更新して解消した
    - High 3 件・Medium 1 件（doc-claim）はいずれも fail-open 側の再現テストを先に書いて RED を確認してから直した（`test_second_point_with_zero_fields_is_rejected` / `test_prose_before_real_heading_cannot_satisfy_required_fields` / `test_malformed_completion_table_without_separator_row_is_rejected` / `test_completion_table_with_unknown_handling_value_is_rejected` / `test_take_not_field_in_wrong_column_is_still_rejected`、および回帰ガード `test_well_formed_completion_table_is_still_accepted`）
  - 4 巡目（3 巡目の commit `a0b0042` からの差分対象。同じ PR オーナーによる read-only diff レビュー）: 3 巡目で閉じた3クラス（件数バランス・見出し起点・完了条件テーブル）と**同じ種類の High が 3 件**、隣接形として再発した。`references/independent-review.md` 等に定める、この PR が採る L1+ 安全策（CLAUDE.md: 同種 high が 2 巡続いたら修正を続けずユーザーへ線引きを戻す）に該当したため、いったん実装を止めてユーザーに確認した
    - ユーザーの判断で、Opus（別モデル）に技術的な advisory を依頼した。Opus の結論: 「3クラスとも『認識できない行を黙って無視する（skip）』という同じ設計が fail-open の共通の源であり、隣接形を1つずつ塞ぐパッチではなく、skip を reject に統一する原理レベルの書き換えで fail-closed を広げるべき」。番号見出しの意味解析には戻さない（維持）という前提のもとで、ユーザーはこの方針で進めることを承認した
    - High 1（`THEME_LINE_RE` が行頭専用）: 承認ポイントのテーマ行をインデントすると `THEME_LINE_RE`（`^\*{0,2}\d+\.`）にマッチせず件数バランスチェックをすり抜け、丸ごと欠落した2件目が無音で吸収されていた（3 巡目 High 1 の同型）。テーマ行の判定から行頭固定を外し、インデントの有無に依存しないよう修正（番号の値は引き続き見ない）
    - High 2（`DECISION_AREA_HEADING_RE` が前方一致）: `### 判断ポイント補足` のような見出しが承認区間の起点になり、直下の地の文が必須欄を充足できてしまっていた（3 巡目 High 2 の同型）。見出しを行末まで完全一致に変更（見出しレベルの上限 `{1,4}` も撤廃し、`#####` 等の取りこぼしも解消）
    - High 3（`_completion_table_rows` の列数チェック無し）: 列が足りない延期行（3セル）が `len(cells) >= 4` のガードで無音 skip され「行が無かったこと」にされる、延期行をそのまま4セルの header として使い区切り行だけ `|---|`（1セル）に短縮すると区切り行のセル数チェックが無く通る、の2つの隣接形があった（3 巡目 High 3 の同型）。ヘッダー・区切り行・data 行のいずれも `COMPLETION_TABLE_COLUMN_COUNT`（4）に一致しない行は skip ではなく table 全体を不正として reject するよう統一
    - Medium（`human-check-template.md` の完了条件テーブルの見出しキャプションが旧文のまま）: 「変換・延期・削除した条件だけ」という文言がルール6の無条件必須化後も残っており、セクション自体が条件付きに読めた。「無条件必須。表には変換・延期・削除した条件だけを載せる」に修正し、セクションの必須性と表の内容選別を文言上も分離した
    - High 3 件はいずれも fail-open 側の再現テストを先に書いて RED を確認してから直した（`test_indented_second_theme_line_still_counts_toward_balance_check` / `test_heading_with_trailing_text_is_not_a_valid_decision_area_start` / `test_short_data_row_is_rejected_instead_of_silently_skipped` / `test_disguised_deferred_row_as_header_with_short_separator_is_rejected`）
  - 5 巡目（4 巡目の commit `cfbafcb` からの差分対象）: 4 巡目のコメントが挙げた 3 High + Medium は記載どおり閉じていることを確認した上で、skip→reject の統一方針の「残り2箇所」を新たに指摘。新しい隣接形の列挙はせず、宣言どおり reject へ統一するだけを求められた
    - High 1（`_decision_item_field_errors` が見出し 0 件で文書先頭へフォールバック）: `無回答時のデフォルト` があるのに見出しが見つからない（`area_start is None`、例: ATX の閉じ `#` を持つ `### 承認ポイント ###` で完全一致から外れる）場合、旧実装は `block_start` を文書先頭（0）へフォールバックしていたため、30 秒判断の地の文が必須欄を充足できてしまっていた。見出しが見つからない場合は個別項目のチェックへ進まず reject するよう修正（フォールバックそのものを廃止）
    - High 2（`_completion_table_rows` が非 table 行以外で正常終了扱いになる）: 閉じる `|` を欠く行は `_TABLE_ROW_RE` に一致しないため、table がそこで legitimate に終わったことにされ、延期行が消えて `延期・削除: なし` で素通りしていた。`|` で始まる行はすべて「table 行のつもり」（`_TABLE_ROW_START_RE`）として扱い、正しい形（`_TABLE_ROW_RE`）でなければ reject するよう統一（table の外への legitimate な終了と、壊れた table 行を区別する）
    - Medium（承認ポイント以降のコードフェンス内 `1. foo` が theme として数えられ得る、false FAIL リスク）: 4 巡目の `THEME_LINE_RE` インデント許容化により生じうる誤検知で、fail-open ではなく fail-closed 方向（安全側）のリスクであることを確認した。真の是正には markdown code fence（```` ``` ````）の内外を全マーカー正規表現の照合で共通して除外する仕組みが要り、この lint ファイル全体の解析モデル（現状すべて行単位・fence 非対応）に関わる横断的な変更になるため、本 push のスコープ外として見送った（下記「受け入れた限界」を参照）
    - High 2 件はいずれも fail-open 側の再現テストを先に書いて RED を確認してから直した（`test_atx_closing_hashes_leave_heading_unmatched_and_must_reject` / `test_table_row_missing_closing_pipe_ends_table_silently_and_must_reject`）
  - 6 巡目（push 前セルフレビュー、`references/independent-review.md` の契約に従い実装文脈を渡さない fresh agent へ委託。5 巡目までは PR オーナー自身の GitHub レビューコメントへの対応のみで、PR オーナー自身による独立レビューは未実施だったため、push 前に追加で実施した）: High 6 件。いずれも直接の再現で検証済み
    - F1（`DEFAULT_SCOPE_LINE_RE` / `NARROWING_LINE_RE` / `DEFAULT_ANSWER_LINE_RE` の行頭記号が `-` 固定）: 承認ポイント全体を `* ` 箇条書きで書く（有効な markdown）だけで `marker_indices` が空になり、X-53 の新設チェックが丸ごと素通りしていた。`BULLET_PREFIX_RE` と同じ受理集合（`-`/`*`/`+`）に統一
    - F2（`_completion_table_rows` の data 行ループが空行で無音終了）: 空行を挟んだ延期行が `rows` に入らず、直前の `延期・削除: なし` で素通りしていた。区間内に残る `|` 始まりの行を残さず走査するよう修正
    - F3（`theme_count` が承認ポイント節より後ろの無関係な番号リストまで走査、かつ修正の第一案が別の regression を誘発）: 文書末尾まで無条件に走査していたため、`### 残タスク` の `1. / 2.` のような無関係な番号リストまで数え、正当な文書が false FAIL していた。節の終端を「次の見出し」に区切るよう修正（第一案の `marker_indices[-1]+1` 区切りは、終端マーカーを丸ごと欠く2件目の検出を壊す regression だったため、実装中に pytest 全量で検出し `_ANY_HEADING_RE` ベースへ修正し直した）
    - F4（1件目のブロックが見出し行そのものから始まる）: 見出し直後・最初のテーマ行より前に置いた地の文が1件目の必須欄を充足できてしまっていた。block の開始を最初のテーマ行にするよう修正
    - F5（テーマ行の件数推定がテーマ行の番号書式に依存）: round3「丸ごと空の2件目」→round4「インデントされた2件目」→ここ「番号の無い2件目」と3回同型の fail-open が再発した。CLAUDE.md の L1+ 安全策（同種 high が2回続いたら修正を続けずユーザーへ線引きを戻す）に該当したため、いったん実装を止めてユーザーに確認した。ユーザーの判断で、件数の突き合わせをテーマ行の形推定から著者の明示宣言（`承認ポイント数: <N>` / `DECLARED_POINT_COUNT_RE`）へ置き換える方針で進めることを承認した。宣言が無い場合・宣言値とマーカー数が不一致の場合はいずれも reject する。1件目の開始位置検出（`THEME_LINE_RE`）は残したが、1件目が番号付き行で始まらない場合もフォールバックせず reject するよう合わせて閉じた
    - F6（`references/human-check-template.md` § 承認ポイントの固定フィールド受理文法 の記述が実装と食い違い）: 起点説明の字句が古く、「限界」の記述も F5 修正前の実装（テーマ行の番号書式依存）を前提にしたままだった。実装の現状に合わせて修正
    - High 6 件はいずれも fail-open 側の再現テストを先に書いて RED を確認してから直した（`test_asterisk_bullets_still_trigger_the_same_checks_as_hyphen` / `test_deferred_row_separated_by_blank_line_is_not_silently_dropped` / `test_theme_count_scan_is_bounded_and_does_not_count_unrelated_numbered_lists` / `test_prose_between_heading_and_first_theme_line_cannot_satisfy_required_fields` / `test_unnumbered_second_theme_line_is_still_caught_by_declared_point_count` / `test_missing_declared_point_count_is_rejected`、および回帰ガード `test_declared_point_count_matching_marker_count_with_unnumbered_theme_is_accepted`）

#### 受け入れた限界

- 独立レビュー（1 巡目）の Medium finding: 本 PR で `lint-hitl-decision-quality.py` に追加した定数（`DECISION_PREMISE_LABEL` / `REJECTED_ALTERNATIVE_LABELS` / `SCOPE_VALUES` / `NONE_NARROWING_VALUE` / `COMPLETION_TABLE_LABEL` / `NONE_DEFERRED_DELETED_FIELD` / `TAKE_NOT_LABEL` 等）は、既存の `tests/test_hitl_lint_marker_sync_contract.py::test_bidirectional_marker_sync` が自動収集する命名規約（`^(REQUIRED|FINAL_HITL_REQUIRED)_.*(MARKERS|PHRASES)$`）に一致せず、正本テンプレートとの語彙 drift を機械検査する既存の防御パターンの対象外になっている。現時点では両テンプレートと lint の語彙は一致することを確認済みだが、将来どちらか片方だけ改名・削除された場合に無音で drift しうる。是正（命名規約への合わせ込み、または専用 pin チェックの追加）は本 PR のスコープ外の別タスクとする
- PR レビュー（5 巡目）の Medium finding: `THEME_LINE_RE` は markdown code fence（```` ``` ````）の内外を区別しないため、承認ポイントの見出し以降にあるコードフェンス内の例示（`1. foo` のような番号リスト）を theme として数え得る。fail-open ではなく fail-closed 方向（正当な文書を誤って reject する false FAIL）のリスクであり、実害の方向はこれまでの High とは逆である。真の是正には code fence の内外を全マーカー正規表現（`THEME_LINE_RE` に限らず `DEFAULT_ANSWER_LINE_RE` 等も同様に fence 非対応）で共通して除外する仕組みが要り、この lint ファイル全体の解析モデル（現状すべて行単位）に関わる横断的な変更になる。承認ポイント本文にコードフェンスで囲んだ例示を書く運用は正本テンプレートに存在せず、発生確率は低いと判断し、本 push のスコープ外とする（6 巡目 F5 の対応で `THEME_LINE_RE` は件数の突き合わせには使わなくなり、1件目の開始位置検出だけに残っているため、この限界の影響範囲は縮小した）。是正は別タスクとする
- 6 巡目 F5 の対応で導入した `承認ポイント数: <N>` は、既定範囲・狭める根拠など他の固定フィールドと同じ自己申告の信頼境界を持つ。宣言値そのものが実態と食い違っていても、行の形・出現数だけを見る本 lint の設計上は検出できない（宣言と `無回答時のデフォルト` の出現数が一致すれば reject されない）。宣言の真偽を機械検査する仕組みは無く、承認者が承認ポイント数の宣言と実際の項目数を目視で突き合わせる前提に依存する
