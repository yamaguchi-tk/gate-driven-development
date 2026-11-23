---
type: patch
---

#### Summary

PR 旧#93 のマージ直前（2026-09-17T02:51:24Z, 02:51:25Z、マージの1分16秒前）に届いた2件のレビュー指摘への後続対応。いずれも実害のある fail-open ではなく、既存の fail-closed 実装の検出力・診断性を補強するもの。

- 指摘1（test-power）: `except SystemExit:` ハンドラの検査を、字句照合から `run()` を実際に例外・返り値で動かし `subprocess` で観測される終了コードを直接測る振る舞いテスト（`make_variant()` + `SystemExitHandlerBehaviorTests`）へ全面転換した
- 指摘2（product、origin: pre-existing）: `review-log-present.sh`・`version-not-consumed.sh` の `except SystemExit: sys.exit(1)` パス（fail-closed だが診断メッセージが無かった）に、原因を断定しない固定診断文言 `FAIL: <label>: run() ended via SystemExit without returning a verdict` を追加した

残る限界: heredoc 境界抽出（`extract_heredoc()`）はシェル構文を解釈しない正規表現のまま（F13）、`.code`・`.args` の属性アクセス検出はディスクリプタ直接呼び出し経路が対象外、`die()` 経路では `FAIL:` 行が3本になる誤読の余地が残る（詳細は下記 Known limitations 参照）。対応過程の詳細な経緯（Codex レビュー7巡・独立レビュー2巡の各指摘とセカンドオピニオンの判断根拠）は `review-log/20260917-pr93-late-review-followup.md` を参照

#### Added

- `plugins/gate-driven-development/tests/test_review_log_present.py`・`plugins/gate-driven-development/tests/test_changelog_fragments.py` に `SystemExit(512)` を送出させる regression test を1本ずつ追加（rc≠0・VERDICT無し・`FAIL:` 固定文言を1本のテストで検証）
- 同2ファイルに、`die()` 経由の通常のバリデーション失敗で `FAIL:` 出力に "dynamic module load" という文言が含まれないこと、かつ新しい固定文言全体が含まれることを固定する regression test を1本ずつ追加
- `plugins/gate-driven-development/tests/test_repository_identity.py` に `make_variant()` を新設し、埋め込み Python の `run()` 関数本体（および任意で `except SystemExit:` ハンドラ本体）を AST で差し替えた新しいソースを返せるようにした。`MakeVariantHelperTests`（5 tests）でこの書き換え能力自体を固定した
- `ExtractHeredocTests`（3 tests）を新設し、`extract_heredoc()` が実行対象コマンド行より前のダミー heredoc を無視すること、実行対象の heredoc が無ければ `AssertionError` になること、候補が2個以上あれば `AssertionError` になることを固定した
- `SystemExitHandlerBehaviorTests`（9 tests）を新設し、`make_variant()` で差し替えた `run()` を実際に `subprocess` で実行し、観測される終了コード・出力を直接検証する振る舞いテストに切り替えた: 正常系（`run()` が `"OK"` を返すと rc=0 で `VERDICT:` 行）・未宣言の返り値（`AssertionError` 経由で rc≠0）・想定外の例外（`RuntimeError` 経由で rc≠0）・`SystemExit` の code 値（`{0, 1, 256, 512, None, "err"}` の全てで rc≠0 かつ `.code` を読まない固定文言）を固定した。sanity テストとして、PR 旧#93 の PR 後レビュー（PR後-3）で修正済みの旧バグ（`code = error.code; sys.exit(code if code != 0 else 1)`）を `make_variant()` で意図的に注入し、`SystemExit(256)` が実際に POSIX の終了コードマスク（`exit_code & 0xFF`）で rc=0 に落ちることも先に固定し、テストヘルパー自体の信頼性を担保した
- Codex レビュー5巡目・F17（medium、実測で再現済み）: 上記の `SystemExit` code 値のテストがプリミティブ値のみで、`.code` を暗黙に `__format__` する F12 型の変異を実際には検出できていなかった。`__format__` が呼ばれた時点で副作用として `SystemExit(256)` を送出する専用オブジェクトを code に使い、sanity テスト（変異ハンドラで rc=0 に落ちることを固定）と本題テスト（実ファイルのハンドラでは rc≠0 のまま保たれることを固定）を追加した
- Codex レビュー6巡目・F18（medium、実測で再現済み）: F17 の `_FormatBomb` が `__format__` メソッドのみをフックしていたため、`print(error.code)`（`__str__` 経由）や `error.args[0]`（`.code` と同じ値を返す別経路）のような回避を見逃していた。個別の dunder メソッドを列挙する代わりに、`.code`・`.args` への属性アクセスそのものを `__getattribute__` でフックする `_CodeAccessBomb` に切り替えた（Opus へのセカンドオピニオン: `code` だけでなく `args` もフックしないと同型の回避が残ることを実測で確認）。あわせて、bomb が `except SystemExit:` ハンドラで捕捉されず未捕捉のままトップレベルまで逃げた場合に CPython 自体が `.code` を参照し結果的に rc≠0 になる誤検知を避けるため、本題テストは `rc==1`（固定値）かつ固定文言の診断メッセージが出力に含まれることの両方を検査するよう強化した

#### Changed

- `plugins/gate-driven-development/tests/checks/review-log-present.sh`・`plugins/gate-driven-development/tests/checks/version-not-consumed.sh`: `except SystemExit:` ハンドラに固定文言の `FAIL: <label>: run() ended via SystemExit without returning a verdict` 行を追加（`SystemExit.code` は引き続き読まない）
- `plugins/gate-driven-development/tests/test_repository_identity.py`: `test_systemexit_handler_does_not_read_error_code`（旧 `SystemExitHandlerPatternTests`→ `SystemExitHandlerASTTests`）を撤去し、`SystemExitHandlerBehaviorTests` に置き換えた。AST 構造検査（ハンドラ本体が `.code` を読んでいないことを文・式レベルで否定形に検証する代理指標）は、Codex による敵対的レビューで正規表現→文レベル AST→式レベル AST→実行到達性（3巡目・F11）→型の変数/import エイリアス（4巡目・F16）と回避経路の指摘が5巡連続した。Opus（claude-opus-5）・Fable（claude-fable-5-1）双方へのセカンドオピニオンで、型名の意味解析をどれだけ足しても新しい回避経路が見つかり続ける構造だと判断し、`run()` から実際に例外・返り値を発生させ観測される終了コードを直接測る肯定形の振る舞いテストへ全面転換することで合意した（詳細は review-log 参照）。`find_systemexit_handlers()`・`_is_broader_than_systemexit()`・`_handler_type_names()`・`handler_is_unconditional_sys_exit_1_without_reading_code()` は全て撤去し、`make_variant()` に一本化した
- `extract_heredoc()`: マッチ開始行を `"$PYTHON_BIN" - "$ROOT" <<'PY'` という実行コマンド行そのものに固定し（`re.M`）、`findall` で候補が正確に1個であることを検査するよう変更した（旧実装はファイル内で最初に現れる任意の `<<'PY'` にマッチしていたため、実行対象より前に無関係な heredoc があると誤った本体を検査していた）。この関数自体は振る舞いテストへの転換後も引き続き使用する（F13 の限界は残存、下記 Known limitations 参照）

#### Affected Files

- `plugins/gate-driven-development/tests/checks/review-log-present.sh`
- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/tests/test_review_log_present.py`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`
- `plugins/gate-driven-development/tests/test_repository_identity.py`

#### User Action Required

- なし

#### Known limitations

- **脅威モデル（Codex レビュー3巡目・F13、Opus・Fable へのセカンドオピニオンで確定）**: この検査が対象とするのは、同一リポジトリの開発者による善意の編集が意図せず fail-open を再導入する偶発的なリグレッションである。検査対象のシェルスクリプト自体を書き換えられる権限を持つ第三者が、検査ロジック自体の回避だけを目的に構成した敵対的な合成コードまでは対象としない。同じ権限があればテストファイル自体を書き換えて検査を無効化できるため、これ以上の厳格化はコストに見合わないと判断した
- `extract_heredoc()` は依然としてシェルの引用・heredoc 構文自体を解釈しない正規表現であり、検査対象を書き換えられる開発者が意図的に decoy heredoc を仕込めば本物の heredoc を見逃しうる（F13、未対応）。開始行の固定・候補数検査は Codex レビュー2巡目の指摘を受けて強化済み（対象より前の decoy heredoc への誤マッチは防止済み）で、境界が見つからない、または候補が2個以上ある場合は `AssertionError` で落ちる（fail-closed）ため、対象同定の失敗が「無言の成功」にはならない
- F12（`print(...)` の位置引数に暗黙の dunder メソッド呼び出しを埋め込み `.code` を読んで再送出する経路）は、Codex レビュー4巡目・F16（例外型の変数/import エイリアスによる実行到達性検査の回避）を機に AST 構造検査を振る舞いテストへ全面転換したことで、`SystemExit.code`・`.args` という属性名への Python レベルのアクセス（代入・`print`・f-string・`getattr` を含む）を検出できるようになった（Codex レビュー6巡目・F18 まで、`__format__` 単体のフック→`__getattribute__` による `code`/`args` 一括フックの順で強化）。ただし「どのような式でも検出できる」という全称的な保証ではない。`object.__getattribute__` や `SystemExit.code.__get__` のようにディスクリプタを直接呼び出す経路は対象外とする（自然な編集ではまず書かれない形であり、この検査が対象とする偶発的なリグレッションの範囲外と判断。Opus・Fable 双方へのセカンドオピニオンで確定）。F16→F17→F18 と「振る舞いテストの検出力をケースの列挙で埋める」指摘が3巡連続したため、F18 の `__getattribute__` 化をもってこの種の指摘に対するレビュー巡は打ち切る方針とした
- die() 経路（通常の入力検証失敗）では `FAIL:` 行が3本（fail() の理由行・die() の裸行・新規の総称行）になり、最後の総称行が唯一の失敗原因であるかのように誤読されうる（独立レビュー・F7、advisory・low、対応見送り）。総称行を条件付きで省略する対応も検討したが、1回の実行で fail() が複数回呼ばれる場合に唯一の失敗理由を隠す副作用があるため見送った
- heredoc 本体の埋め込み Python を独立した `.py` ファイルへ分離すれば `extract_heredoc()` 自体（および F13 の限界）が不要になる（Fable へのセカンドオピニオンでの指摘）。本 PR のスコープ外の設計変更のため後続課題とする
- 検証中に `bash plugins/gate-driven-development/tests/validate-plugin.sh` で `hitl-required-fields-lint` の `VERDICT_MISSING` を観測したが、`origin/main` の別 worktree でも同一症状を確認済みの既存の別問題であり、本PRのスコープ外

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（`review-log-present` check を含む。既知の `hitl-required-fields-lint` VERDICT_MISSING は既存の別問題。上記 Known limitations 参照）
- Snyk Code Scan（変更対象ファイル）
- 新規 regression test はいずれも実装前に RED（旧実装では検出できない／誤診断が再現する）を確認してから実装を修正し、GREEN になることを確認した
- Codex adversarial-review・独立レビュー（`Agent(model="opus")` general-purpose subagent、read-only・diff-only・実装経緯非共有）を実施し、字句照合→AST 構造検査→振る舞いテストの順にアプローチを転換しながら high・blocking を解消した。各巡の severity・指摘内容・セカンドオピニオンの判断根拠は `review-log/20260917-pr93-late-review-followup.md` を正本として参照
