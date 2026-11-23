---
type: minor
---

#### Summary

`review-log-present.sh` と `version-not-consumed.sh` に逐語コピーされていた `repository_identity()`（H2〜H6 の fail-open がそれぞれ独立に再発する経路になっていた。`independent-review.md` (h) 受理集合の対称性が指摘する型そのもの）を共有モジュールへ一本化した。あわせて `independent-review.md` の観点レーンに「列挙型判定の検出」を追記し、差し戻し後に方針メモを複数回記録できるよう巡ラベル値域に `方針メモ-N` を追加した。

root `CLAUDE.md` L1+ 安全策4「同じ種類（クラスタ）の high・blocking が2回続いたら、修正を続けずにユーザーへ線引きを戻す」の機械化も同時に試みたが、独立レビュー4巡（独立-1〜独立-4）で計5件の high 指摘が連続し、そのたびに検知ロジック自身の受理集合・状態遷移に新しい穴が見つかった。クラスタ名は検査対象である当人が自由文で書く自己申告値であり、個別の異常値を塞ぐ都度、別の変異（表記を変える・別ラベルを使う等）で回避できてしまう構造だった。Opus（claude-opus-5）へのセカンドオピニオンで「この受理集合は原理的に閉じない」との判断を受け、ユーザー承認のもと本PRのスコープからこの機械化を撤回した（経緯は `review-log/20260916-review-log-cluster-recurrence-guard.md` 参照）。安全策4自体は root CLAUDE.md の散文の規定のまま残る。

PR 旧#93 の PR 後レビュー3巡目（独立-5・独立-6に続く同クラスタの High、PR後-2）: `load_dynamic_module()` は `exec_module()` 呼び出しの `SystemExit` だけを守り、動的ロードしたモジュールへの「呼び出し」4箇所（`identity_lib.repository_identity()`、`release.NAME_RE.fullmatch()` 複数箇所、`release.load_fragments()`）は guard 外のままで同型の fail-open が再発する経路だった。安全策4に従いユーザー確認・Opus へのセカンドオピニオン（方針メモ-4）を経て、個々の呼び出し箇所を塞ぐ対処ではなく、両チェックスクリプトの本体を `run()` 関数に集約し「判定を宣言したか」を機械的に検査する二層構造に倒した:
- 内側: `review-log-present.sh`・`version-not-consumed.sh` の本体を `run() -> str` 関数に集約し、正常return（`"OK"` または `"SKIP"`）した場合だけ呼び出し元が `VERDICT: <check_name>: OK|SKIP` を出力する。`die()` の明示的 `SystemExit(1)`、動的ロードしたモジュールへの呼び出し中に送出される想定外の例外（`SystemExit(0)` を含む）、その他の `BaseException` は、いずれも「`run()` が正常return しなかった」の一点に合流し、呼び出し元の `except` で一律 FAIL にする（fail-closed）。呼び出し箇所を個別に列挙して塞ぐ対処ではないため、将来この動的ロードしたモジュールへの呼び出しが増えても構造的に閉じたままになる
- 外側: `validate-plugin.sh` に、rc=0 なのに `VERDICT: <check_name>: OK` または `VERDICT: <check_name>: SKIP` 行が無い check を一律で FAIL にする番兵を追加し、全46 BLOCK チェックへ共通適用した。判定行を出していなかった check には `VERDICT: <name>: OK`（分岐がある check は SKIP 分岐にも）を追加した

この対応の独立レビュー（独立-8）でさらに以下を検出・修正した: (H) 番兵の唯一のテストが untracked でブランチに入っていなかった（git add で修正）。(M) check の stdin が manifest.tsv の read ループのリダイレクトを継承したままだと、stdin を読む check が manifest の残り行を食い、後続の check が一度も実行されずに rc=0 で完走する経路があった（`</dev/null` で切った）。(L) check_name を未エスケープで後段の `grep -E` に埋め込んでいたため正規表現メタ文字が誤マッチする余地があった（manifest 読み込み時に `[A-Za-z0-9_-]+` へ限定）。(L) `run()` の戻り値が未検証だった（`"OK"`/`"SKIP"` 以外を検出したら fail-closed にする検査を追加）。(L) `review-log-present.sh` の SKIP-B 返却前に `version-not-consumed.sh` と同じ `if failures: die()` ガードが無かった（対称性のため追加）。詳細は `review-log/20260916-review-log-cluster-recurrence-guard.md` の PR後-2・方針メモ-4・独立-8 を参照

このpush(commit 773191d)後の新しいレビュー巡（PR後-3）で、上記の内側修正で書いた `except SystemExit as error:` ハンドラ自体に新しい High が指摘された: `error.code` を読み `code if code != 0 else 1` に倒していたが、`SystemExit(256)`（256 の倍数）は POSIX のシェル終了コードマスク（`exit_code & 0xFF`）でシェル側の実終了コードが 0 になるため、この判定を通過して静かに成功してしまう fail-open だった（`validate-plugin.sh` 経由の公式入口は VERDICT_MISSING で検出できるが、check スクリプトの直接実行では偽の成功になる）。安全策4に従いユーザー確認・Opus へのセカンドオピニオン（方針メモ-5）を経て対応: `error.code` を一切読まず、`SystemExit` が発生した事実だけを根拠に常に `sys.exit(1)` にする（`except SystemExit: sys.exit(1)`、`as error` 束縛自体を削除）。Opus の見立て: 危険クラスは同じ（rc=0 かつ VERDICT 無しの fail-open）だが機序は別（前3回は「guard 外への到達性」、今回は「guard 内での値変換」）であり、判定入力を「run() が正常return したか」という単一の真偽値に絞ることで残余の列挙は0件になる（受理集合は原理的に開いていない）。安全策4の形式要件（同種high 2回連続）には該当するが、条項の趣旨（開いた入力）には当たらないため、この修正で閉じ切る

#### Added

- `plugins/gate-driven-development/scripts/lib/repository_identity.py`（新規）: `review-log-present.sh`・`version-not-consumed.sh` が共有する identity marker 判定（`repository_identity(base, marketplace_name)`）。両スクリプトのローカルコピーを削除し、`importlib.util.spec_from_file_location` でこのファイルをロードして使う（`scripts/release.py` の既存のロード方式と同じパターン）
- `plugins/gate-driven-development/tests/test_repository_identity.py`（新規、11 tests）: 共有モジュール自体の判定ロジック（H4/H5/H6 の代表ケース）と、両 check スクリプトがローカルコピーを持たず共有モジュールを参照していることを固定する契約テスト
- 差し戻し後の再方針メモを記録できるよう、巡ラベル値域に `方針メモ-N` を追加で許可（`方針メモ` 単独の重複禁止とは独立に複数回使える）。sha='-' の例外（「まだコミットが無い」ことを表す）も `方針メモ-N` に及ぶ
- `plugins/gate-driven-development/tests/test_review_log_present.py` に regression test を7本追加（`方針メモ-N` の受理・sha='-' 例外・クラスタ `-` 拒否・共有モジュールロード失敗4本〔identity: 欠落・構文エラー・SystemExit／release: SystemExit〕）
- `plugins/gate-driven-development/tests/test_validate_plugin_verdict_sentinel.py`（新規、8 tests）: `validate-plugin.sh` の VERDICT 番兵ロジック自体の契約テスト。合成 check スクリプトで fail-open 3ケース＋逆方向対照（正規の OK/SKIP 宣言は通る）を固定し、独立-8 で追加検出された stdin 消費・check_name のメタ文字混入も regression test で固定する
- `plugins/gate-driven-development/tests/test_review_log_present.py`・`plugins/gate-driven-development/tests/test_changelog_fragments.py` に、動的ロードしたモジュールへの「呼び出し」中に SystemExit が送出されるケースの regression test を追加（`identity_lib.repository_identity()` 呼び出し・`release.NAME_RE.fullmatch()` 呼び出し・`release.load_fragments()` 呼び出しの3パターン）。旧実装（コミット 14a1ec1）に対してこれらのテストが RED になることを確認済み
- `plugins/gate-driven-development/tests/test_review_log_present.py`・`plugins/gate-driven-development/tests/test_changelog_fragments.py` に、`identity_lib.repository_identity()` 呼び出しが `SystemExit(256)` を送出するケースの regression test を1本ずつ追加（PR後-3対応）。旧実装（コミット 773191d）に対してこれらのテストが RED になることを確認済み
- `plugins/gate-driven-development/tests/test_repository_identity.py` に、両チェックスクリプトの `except SystemExit` ハンドラが同一かつ `error.code`（`SystemExit` インスタンスの束縛自体）を参照しないことを固定する contract test を1本追加

#### Changed

- `plugins/gate-driven-development/references/independent-review.md`: 観点(h)「受理集合の対称性」に「列挙型判定の検出」（同じ入力を読む判定が既知の異常パターンを列挙して弾く型になっていないか。列挙型なら受理文法のホワイトリスト化・既定の反転への置き換えを見る）を統合。`references/` の line budget（validate-plugin.sh 固定値）を超えないよう、新規bulletではなく既存(h)行への統合という形にした
- `plugins/gate-driven-development/tests/checks/review-log-present.sh`・`plugins/gate-driven-development/tests/checks/version-not-consumed.sh`: `repository_identity()` のローカル定義を削除し、共有モジュールのロードに置き換え。あわせて `## 指摘` の実指摘行でクラスタ列に `-` を許容しない（プレースホルダーの `-` では分類にならないため。ただし他4列のホワイトリスト検査とは異なり、既知のプレースホルダーのみを拒否するブラックリスト判定であることは Known limitations に開示）
- `plugins/gate-driven-development/tests/checks/review-log-present.sh`・`plugins/gate-driven-development/tests/checks/version-not-consumed.sh`: `repository_identity.py`・`release.py` の動的ロード（`importlib.util.spec_from_file_location` → `exec_module`）を専用のブートストラップ関数 `load_dynamic_module()` に一本化した。個別に書かれていた `except Exception` は `SystemExit`（BaseException 派生）を捕捉できず、モジュールの exec 中に SystemExit が送出されるとスクリプト全体が rc=0 で静かに成功してしまう fail-open だった（独立レビューで2箇所とも検出）。`BaseException` の対象を `exec_module()` 呼び出し1箇所に集約し、静的ファイル読み込みには広げていない
- `plugins/gate-driven-development/tests/test_review_log_present.py`・`plugins/gate-driven-development/tests/test_changelog_fragments.py`: `make_plugin()` ヘルパーが `scripts/lib/repository_identity.py` も合成 plugin ディレクトリへコピーするよう変更（共有モジュール参照に追随するため）。共有モジュールのロード失敗（欠落・破損）が SKIP ではなく FAIL になることを固定する regression test を両ファイルに追加
- `plugins/gate-driven-development/tests/checks/review-log-present.sh`・`plugins/gate-driven-development/tests/checks/version-not-consumed.sh`: 本体を `run() -> str` 関数に集約し、呼び出し元を `try/except SystemExit/BaseException/else` で包む構造に変更（PR 旧#93 の PR 後レビュー3巡目対応、上記 Summary 参照）。`load_dynamic_module()` の定義位置は両ファイルとも `run()` 内のネスト関数に移動したが、実装本体（コピペ同期）は変更していない
- `plugins/gate-driven-development/tests/checks/review-log-present.sh`・`plugins/gate-driven-development/tests/checks/version-not-consumed.sh`: `except SystemExit as error:` ハンドラを `except SystemExit:` に変更し、`error.code` を一切読まず常に `sys.exit(1)` にした（PR後-3対応、上記 Summary 参照。`SystemExit(256)` 等の POSIX 終了コードマスクによる fail-open を閉じる）
- `plugins/gate-driven-development/tests/validate-plugin.sh`: 各 check 実行後、rc=0 なのに `VERDICT: <check_name>: OK` または `VERDICT: <check_name>: SKIP` 行（アンカー一致）が無ければ `VERDICT_MISSING` で FAIL にする番兵を追加。check の呼び出しを `check_output="$(bash "$ROOT/$check_script" </dev/null)"` に変更し（出力キャプチャ＋stdin 切断）、check_name を `[A-Za-z0-9_-]+` に限定する manifest 検査も追加
- `plugins/gate-driven-development/tests/checks/*.sh`（44本、review-log-present.sh・version-not-consumed.sh を除く全 BLOCK チェック）: 成功時（分岐がある check は該当する全分岐）に `VERDICT: <check_name>: OK` または `VERDICT: <check_name>: SKIP` を1行追加。既存の判定文言（`OK`/`PASS: ...`/`SKIP: ...`/`BLOCK: <name>` 等）は変更せず、宣言行を追加するだけにした

#### Affected Files

- `plugins/gate-driven-development/scripts/lib/repository_identity.py`（新規）
- `plugins/gate-driven-development/tests/test_repository_identity.py`（新規）
- `plugins/gate-driven-development/tests/test_validate_plugin_verdict_sentinel.py`（新規）
- `plugins/gate-driven-development/tests/checks/review-log-present.sh`
- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/tests/validate-plugin.sh`
- `plugins/gate-driven-development/tests/checks/*.sh`（44本、VERDICT 宣言行の追加。review-log-present.sh・version-not-consumed.sh は上記に個別記載）
- `plugins/gate-driven-development/tests/test_review_log_present.py`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`
- `plugins/gate-driven-development/references/independent-review.md`

#### User Action Required

- なし。`repository_identity()` の共有化・`方針メモ-N` の追加はいずれも既存の review-log 運用と後方互換

#### Known limitations

- 共有モジュール化（`repository_identity()` の一本化）により、SKIP-B の前提が「本リポジトリの checkout には `scripts/lib/repository_identity.py` が同梱されている」ことに変わった。通常の marketplace 配布は `scripts/` を含むため通常は崩れない前提だが、モジュールが欠落・破損した消費者環境ではロード失敗を SKIP に倒さず FAIL にする（判定不能を「無い」と誤認しない、既存の SKIP-B 設計判断と同じ方針）。この経路は両チェックスクリプトに regression test で固定した（identity: 欠落・構文エラー・`SystemExit` を送出するモジュールの3パターン／release: `SystemExit` を送出するモジュールの1パターン）
- `repository_identity.py`・`release.py` の動的ロードを `load_dynamic_module()` に一本化する前、両モジュールの `exec_module()` 呼び出しは個別に `except Exception` で囲まれており、`SystemExit`（BaseException 派生）を捕捉できず rc=0 で静かに成功する fail-open が2箇所（コピペ）に存在した。独立レビューで両方検出し、`exec_module()` 呼び出し1箇所への `except BaseException` 集約で閉じた（静的ファイル読み込みには広げていない。`read_text()`/`json.loads()` は SystemExit を投げないため対象外で、広げると `KeyboardInterrupt` を握り潰す逆方向の fail-open になる）
- `load_dynamic_module()` は scripts/lib/ へ切り出さず両チェックスクリプトへコピペしたままにしている（Opus のセカンドオピニオン: 切り出すとブートストラップ自体のロードに同じ保護が要る循環になるため）。同期は `test_repository_identity.py` の contract test で機械的に固定した
- 動的ロードしたモジュールへの「呼び出し」（`identity_lib.repository_identity()`・`release.NAME_RE.fullmatch()`・`release.load_fragments()`）が SystemExit を送出するケースは、PR 旧#93 の PR 後レビュー3巡目（PR後-2）で再指摘され、`run()` 関数化＋呼び出し元の一括 except による構造的解決で閉じた（上記 Summary 参照）。この Known limitations に以前あった「`release.load_fragments()` 呼び出しだけが残渣で実害なし」という記述は解消済みのため本版で削除した
- `run()` の戻り値検証（`"OK"`/`"SKIP"` 以外を検出したら fail-closed にする分岐）と、`review-log-present.sh` の SKIP-B 返却前の `if failures: die()` ガード（独立-8 L で追加。上記参照）は、いずれも現状のコードパスでは到達不能な防御的コードであり、この分岐を削除しても既存テストスイートは green のまま通る（PR後-3・medium・test-power 指摘）。mutation testing はスコープ外と既に判断済み（下記参照）のため、この2箇所を強制的に踏ませる専用テストは追加せず、「実測で検証済み」ではなく「対称性・将来の変更に備えた防御的追加」であることをここで明示する
- VERDICT 番兵は「宣言済みかどうか」だけを検査し、check の出力に自己申告の `FAIL:` 行が混在していても `VERDICT: <name>: OK` が出ていれば通す（独立-8 advisory）。46本の check 本体がそもそも `fail()` した時点で `die()`/非0 exit するため、現行実装ではこの2つが同時に成立するケースは無いが、将来 check の実装ミスで両方が出力される余地は構造上残る。クロスチェック（`FAIL:` 行があれば OK 宣言を拒否する）は本PRのスコープ外とし、限界として開示する
- opt-in が既定で無効な2本の check（`superpowers-benchmark-gate.sh`・`skill-red-green-gate.sh`）は、その opt-in が発火しない実行（何も検査していない）でも `VERDICT: <name>: OK` を宣言する。一方、同様に「今回は検査対象が無い」ケースを持つ `external-verifier-smoke.sh`・`docs-links-valid.sh` は `SKIP` を宣言しており、OK/SKIP の宣言語彙が実態に対して非対称（独立-8 low）。本PRのスコープでは対応せず、限界として開示する
- `check_output="$(bash "$ROOT/$check_script" </dev/null)"` は check の標準出力のみを捕捉するため、check が標準エラーへ書いた診断行（例: `docs-links-valid.sh` の `DRIFT:` 行）は先に端末へ流れ、捕捉した標準出力はその後にまとめて出る（順序が入れ替わる）。判定（VERDICT 行の有無）には影響しないが、失敗時の出力順序が変わる点と、長時間 check の進捗がリアルタイムに見えなくなる点（ストリーミングからバッファリングへの変更）を限界として開示する（独立-8 low）
- 実指摘行のクラスタ列は、既知のプレースホルダー `-` のみを拒否するブラックリスト判定であり、severity/実害/自己起因/対応の4列が使う固定語彙のホワイトリスト判定とは受理集合が揃っていない（`n/a`・`--` 等は依然通る。セルは strip() 済みのため空白のみは既存の空クラスタ検査で拒否される）。クラスタ名は自由記述の分類ラベルであり列挙値ではないため、ホワイトリスト化は本PRのスコープ外とし、既知のプレースホルダーのみを拒否する限界として開示する
- root CLAUDE.md L1+ 安全策4「同じ種類の high・blocking が2回続いたら線引きを戻す」の機械化は撤回した。現状は散文の規定のままで、review-log-present.sh による自動 FAIL 化は行わない。独立レビュー4巡で試みた設計（クラスタ名の自由文字列照合＋方針メモによる状態リセット）は、個別の異常値を塞ぐたびに別の変異で回避できる構造的な限界があった。後続の再設計案（Opus のセカンドオピニオンより）: クラスタ名を宣言済みの列挙値に限定し、block ではなく warn（L1 相当の `systemMessage` のみ）にすることで、回避のインセンティブ自体を無くす方向が有力。詳細は `review-log/20260916-review-log-cluster-recurrence-guard.md` の独立-1〜独立-4・方針メモ・方針メモ-2 を参照
- 独立レビューの差分絞り込みコスト実測改善・checkスクリプト群の `.py` 全面移行・mutation testing・分岐カバレッジ gate は、Opus のセカンドオピニオンで明確に非推奨とされたため対象外（詳細は review-log 参照）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 新規 contract test: `test_repository_identity.py`（11 tests、`load_dynamic_module()` の両ファイル同期を固定する contract test、および両ファイルの `except SystemExit` ハンドラの対称性・`error.code` 未参照を固定する contract test を各1本追加）
- `test_review_log_present.py` に regression test 7本追加（`方針メモ-N` の受理・sha='-' 例外・クラスタ `-` 拒否・共有モジュールロード失敗4本〔identity: 欠落・構文エラー・SystemExit／release: SystemExit〕）
- `test_changelog_fragments.py` に共有モジュールロード失敗の regression test 4本追加（identity: 欠落・構文エラー・SystemExit／release: SystemExit）
- 独立レビュー（独立-5・独立-6、PR後-1対応差分＋その修正のセルフレビュー）で計2回連続の high 指摘が続いた後、PR 旧#93 の PR 後レビュー3巡目（PR後-2）で同一クラスタの High が3回目、root CLAUDE.md 安全策4に従いユーザーへ確認。Opus へのセカンドオピニオン（方針メモ-4）で二層構造（内側 run() 化＋外側 VERDICT 番兵）を提案され、外側も含めて実施することを承認。対応後の独立レビュー（独立-8）でさらに5件の指摘（stdin 消費・check_name のメタ文字・run() 戻り値未検証・SKIP-B ガード非対称・untracked テストファイル）を検出し、同一 push で修正した
- 新規 contract test: `test_validate_plugin_verdict_sentinel.py`（8 tests、VERDICT 番兵の fail-open 3ケース＋逆方向対照＋独立-8 で追加検出された2ケース）
- `test_review_log_present.py`・`test_changelog_fragments.py` に、動的ロードしたモジュールへの呼び出し中の SystemExit を検出する regression test を計4本追加（review-log-present.sh: identity 呼び出し・NAME_RE.fullmatch 呼び出しの2本／version-not-consumed.sh: identity 呼び出し・load_fragments 呼び出しの2本）。旧実装（コミット 14a1ec1）でこれらのテストが RED になることを確認済み
- 独立レビュー（独立-5・独立-6、PR後-1対応差分＋その修正のセルフレビュー）で計2回連続の high 指摘（`except Exception` が `SystemExit` を捕捉しない fail-open、identity と release の2箇所）が続き、root CLAUDE.md 安全策4に従いユーザーへ確認。Opus へのセカンドオピニオンで「受理集合が原理的に閉じない開いた入力ではなく、`exec_module()` という有限で列挙可能な単一パターンのコピペ網羅漏れ」と判定され、`load_dynamic_module()` への一本化で対応を継続した（詳細は review-log 参照）
- push(commit 773191d)後の新しいレビュー巡（PR後-3）で、上記の内側修正自体に新しい High（`SystemExit(256)` 等の POSIX 終了コードマスクによる fail-open）が指摘され、独立-5・独立-6・PR後-2に続く4回目の同種high として root CLAUDE.md 安全策4に従いユーザーへ確認。Opus へのセカンドオピニオン（方針メモ-5）で「機序は別だが受理集合は開いていない（`run()` の正常return有無という単一の真偽値に絞れば残余の列挙は0件）ため、線引きを戻すのではなく今回で閉じ切るべき」と判定され、`error.code` を一切読まない実装に修正して対応を継続した。`test_review_log_present.py`・`test_changelog_fragments.py` に `SystemExit(256)` を送出させる regression test を1本ずつ、`test_repository_identity.py` に両ファイルの `except SystemExit` ハンドラの対称性・`error.code` 未参照を固定する contract test を1本追加。旧実装（コミット 773191d）でこれらのテストが RED になることを確認済み
