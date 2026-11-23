---
lane: L1+
pr: 93
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み) | 4f722fa | 1 | 2 | 0 | 2026-09-16T12:47+09:00 |
| 独立-2 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み) | 0e02b66 | 1 | 3 | 0 | 2026-09-16T13:00+09:00 |
| 方針メモ | ユーザー確認（安全策4: 独立-1/独立-2で同種のhigh「解除経路が機能しない」が2回続いたため線引きを確認） | - | 0 | 0 | 0 | 2026-09-16T13:10+09:00 |
| 独立-3 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み) | b8d5cb6 | 2 | 1 | 0 | 2026-09-16T13:45+09:00 |
| 独立-4 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み) | c86c4d0 | 1 | 3 | 0 | 2026-09-16T14:12+09:00 |
| 方針メモ-2 | ユーザー確認＋Opus(claude-opus-5)へのセカンドオピニオン（安全策4: 独立-1〜独立-4で4回連続、クラスタ再発検知機能自身の受理集合・状態遷移に high が出続けたため、機能自体の撤回を決定） | - | 0 | 0 | 0 | 2026-09-16T15:47+09:00 |
| PR後-1 | GitHub review（PR 旧#93、インラインコメント3件） | 0a85da0 | 0 | 3 | 0 | 2026-09-16T16:30+09:00 |
| 独立-5 | general-purpose subagent (read-only, diff-only, 経緯非共有; independent-review.md (a)〜(h) 込み、PR後-1対応差分のセルフレビュー) | 321d835 | 1 | 1 | 0 | 2026-09-16T17:10+09:00 |
| 独立-6 | general-purpose subagent (read-only, diff-only, 経緯非共有; independent-review.md (a)〜(h) 込み、独立-5指摘反映後の差分のセルフレビュー) | a4b2e3c | 1 | 0 | 0 | 2026-09-16T17:35+09:00 |
| 方針メモ-3 | ユーザー確認＋Opus(claude-opus-5)へのセカンドオピニオン（安全策4: 独立-5/独立-6で同種のhigh「共有モジュールロードのexcept ExceptionがSystemExitを捕捉できないfail-open」が2回続いたため線引きを確認。Opus判断: 受理集合が原理的に閉じない開いた入力ではなく、exec_module()という有限で列挙可能な単一パターンのコピペ網羅漏れであり、ロードの唯一の入口をload_dynamic_module()に集約して閉じる方向で対応継続を承認） | - | 0 | 0 | 0 | 2026-09-16T17:45+09:00 |
| 独立-7 | general-purpose subagent (read-only, diff-only, 経緯非共有; independent-review.md (a)〜(h) 込み、load_dynamic_module()一本化差分のセルフレビュー) | c87ba61 | 0 | 2 | 0 | 2026-09-16T18:05+09:00 |
| PR後-2 | GitHub review（PR 旧#93、commit 14a1ec1 に対する再レビュー） | 14a1ec1 | 1 | 1 | 0 | 2026-09-16T19:10+09:00 |
| 方針メモ-4 | ユーザー確認＋Opus(claude-opus-5)へのセカンドオピニオン（安全策4: 独立-5/独立-6に続き、PR後-2で同種のhigh「動的ロードしたモジュールへの呼び出し中のSystemExit fail-open」が3巡目。Opusの二層構造提案（内側: run()化+宣言フラグ、外側: validate-plugin.shの全46 BLOCKチェックへの判定行必須化の番兵）を、外側も含めて実施することを承認） | - | 0 | 0 | 0 | 2026-09-16T19:20+09:00 |
| 独立-8 | general-purpose subagent (read-only, diff-only, 経緯非共有; independent-review.md (a)〜(h) 込み、run()化+VERDICT番兵差分のセルフレビュー) | 773191d | 1 | 2 | 0 | 2026-09-16T20:10+09:00 |
| PR後-3 | GitHub review（PR 旧#93、commit 773191d/80fe85c に対する再レビュー） | 80fe85c | 1 | 2 | 0 | 2026-09-16T14:15+09:00 |
| 方針メモ-5 | ユーザー確認＋Opus(claude-opus-5)へのセカンドオピニオン（安全策4: 独立-5/独立-6/PR後-2に続き、PR後-3で同種のhigh「fail-open」が4巡目。ただし機序は別（前3回は guard 外への到達性、今回は guard 内での値変換=SystemExitのcodeがPOSIXの終了コードマスクでシェルrc=0に落ちる）。Opus判断: 受理集合は開いていない（run()の正常return有無という単一の真偽値に絞れば残余の列挙は0件）ため、安全策4の形式要件には該当するが趣旨には当たらず、線引きを戻すのではなく今回で閉じ切ることを承認。error.codeを一切読まずexcept SystemExit: sys.exit(1)にする対応で決着） | - | 0 | 0 | 0 | 2026-09-17T09:30+09:00 |
| 独立-9 | general-purpose subagent (read-only, diff-only, 経緯非共有; independent-review.md (a)〜(h) 込み、PR後-3対応差分〔773191d..c5c5cc0〕のセルフレビュー) | c5c5cc0 | 0 | 0 | 0 | 2026-09-17T10:15+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | yes | self-inflicted | cluster-recurrence-guard-no-reset-path | fixed | クラスタ連続再発検知に方針メモ後のリセット機構が無く、一度 high/実害=yes が出るとブランチが恒久的に push 不能になる |
| F2 | 独立-1 | medium | yes | self-inflicted | cluster-recurrence-guard-adjacency-scope | fixed | 検知が隣接する2巡のみを見ており、間に無関係な巡を挟むと検知を回避できる |
| F3 | 独立-1 | medium | yes | self-inflicted | cluster-recurrence-guard-exact-match | fixed | クラスタ名の完全一致判定のため、大文字小文字・空白の差異だけで検知を回避できる |
| F4 | 独立-1 | low | no | self-inflicted | cluster-recurrence-guard-blocking-not-covered | accepted | 検知が severity=high または実害=yes の指摘のみを見ており、blocking 件数は対象外（既存の設計限界として開示） |
| F5 | 独立-1 | low | no | self-inflicted | cluster-recurrence-guard-empty-cluster | fixed | クラスタが空文字の指摘行が連続すると、それ自体が誤って再発検知される二次ノイズになりうる |
| F6 | 独立-1 | low | no | self-inflicted | doc-consistency-h-clause | fixed | independent-review.md (h) の文言拡張が inline-review-checklists.md と CONTRIBUTING.md に未反映だった |
| F7 | 独立-1 | advisory | no | self-inflicted | dead-code-unused-import | fixed | 未使用の import json が残存していた |
| F8 | 独立-2 | high | yes | self-inflicted | escape-hatch-unreachable-in-append-order | fixed | 方針メモ-N によるリセットは巡の記載順で再発ペアより前に無いと効かないが、root CLAUDE.md の運用（指摘が出たら方針メモ巡を追記する＝末尾追記）では方針メモは常に検出済みペアの後に来るため、F1 で修正したはずの「恒久的に push 不能」状態が実運用フローでは解消されていない。走査完了後にまとめて発火する保留方式に変更 |
| F9 | 独立-2 | medium | yes | self-inflicted | escape-hatch-unreachable-in-append-order | accepted | `last_seen_by_cluster.clear()` は全クラスタの追跡を一律に消すため、ユーザーが確認したのは特定クラスタ1件でも無関係なクラスタの再発記録まで解除される。方針メモにクラスタ指定欄が無く自由文から機械判定もしないため、既存の設計限界として changelog の Known limitations に開示 |
| F10 | 独立-2 | medium | yes | self-inflicted | cluster-recurrence-guard-exact-match | accepted | クラスタ名の正規化が casefold と空白畳み込みのみで、ハイフン/アンダースコア表記・全角文字・訳語違いでは依然回避可能（individual-review.md (h) が指摘する「個別変異を塞ぐパッチ」型のまま）。これ以上の正規化（列挙値化等）は本PRのスコープ外として changelog の Known limitations に開示 |
| F11 | 独立-2 | medium | yes | self-inflicted | escape-hatch-unreachable-in-append-order | accepted | `at` 列と巡の記載順の整合を検証していないため、方針メモ行を時系列と無関係な位置に置くだけで再発検知を解除できる。保留方式への変更後も既存の Known limitations（記載順操作で回避可能）の範囲内であり、新たな限界の拡大ではないと判断 |
| F12 | 独立-2 | low | no | self-inflicted | doc-impl-label-asymmetry | fixed | リセット条件の `POLICY_MEMO_JUN_RE` はサフィックス無し `方針メモ` でもリセットするが、changelog・FAIL 文言は `方針メモ-N` のみを記述しており受理集合の説明が実装と不一致。`方針メモ`/`方針メモ-N` の表記に統一 |
| F13 | 独立-2 | low | no | self-inflicted | placeholder-cluster-conflation | fixed | 実指摘行のクラスタは `-` でも許容され、`-` も正規化後の有効なクラスタ名として追跡されるため、無関係な指摘が `-` を使うと誤 FAIL になりうる。正規化後 `-` になる行を検知対象から除外 |
| F14 | 独立-2 | advisory | no | self-inflicted | message-wording | fixed | FAIL 文言 `... finding in 両 巡 ...` が日英混在で読みにくい。`both 巡` に修正 |
| pm-1 | 方針メモ | - | - | - | - | - | なし |
| F15 | 独立-3 | high | yes | self-inflicted | dash-cluster-bypass | fixed | クラスタ列は空チェックのみで `-` を有効な値として通す一方、severity/実害/自己起因/対応の4列は「なし」行以外で `-` を明示的に拒否している。受理集合が非対称で、全指摘のクラスタを `-` にすれば再発検知全体を無効化できる。実指摘行のクラスタ `-` を他4列と同じく fail() で拒否 |
| F16 | 独立-3 | high | yes | self-inflicted | policy-memo-parking | fixed | 方針メモ巡自身が severity=high/実害=yes の指摘を持つ場合、その巡は `continue` で丸ごとスキップされ `last_seen_by_cluster` に登録されないため、方針メモ巡自身の high 指摘のクラスタが以降の再発検知から見えなくなる。方針メモ巡でも保留破棄と同時に自身のクラスタを新しい基準点として記録するよう修正 |
| F17 | 独立-3 | medium | yes | self-inflicted | escape-hatch-unreachable-in-append-order | accepted | 「ユーザー確認1回で無関係なNクラスタの再発が一括解除される」非対称は F9 と同種。既存の Known limitations 開示で対応済みと判断し追加対応なし |
| F18 | 独立-3 | low | no | self-inflicted | vacuous-assertion | fixed | `test_consecutive_rounds_with_same_cluster_but_invalid_severity_does_not_crash` の `assertNotIn("consecutive", result.stdout)` は FAIL 文言に "consecutive" という語が無いため常に真で、退行を検出できない。実際の FAIL 文言のリテラルで確認するよう修正 |
| F19 | 独立-3 | low | no | self-inflicted | pending-coverage-gaps | accepted | 複数クラスタの一括解除・3巡以上の連続再発・方針メモの連続等の組み合わせテストが無い。F17と同根の既知の限界であり、本PRのスコープでは追加しない |
| F20 | 独立-4 | high | yes | self-inflicted | policy-memo-tracking-lost | fixed | 方針メモ巡が2回連続する実運用で、1つ目の方針メモ巡が記録した自身のクラスタが2つ目の方針メモ巡の `clear()` で無条件に消え、独立-3で塞いだはずの「方針メモ巡自身の指摘が追跡から消える」fail-open が実質再発していた。クラスタ再発検知機能自体の撤去（方針メモ-2）により解消 |
| F21 | 独立-4 | medium | yes | self-inflicted | misleading-fail-message | fixed | `prev_label` が方針メモ巡になり得るのに FAIL 文言が固定で「方針メモ/方針メモ-N round を追加せよ」と指示し、既に方針メモ巡が存在する状況で自己矛盾した文言になっていた。機能撤去により解消 |
| F22 | 独立-4 | medium | no | self-inflicted | dash-enumeration-blacklist | fixed | `-` だけを拒否する修正（F15）自体が「既知の異常パターンを列挙して弾く」型で、`--`・Unicode ハイフン変種・単に別ラベルを書くだけで同様に回避できる。個別ケースを塞ぐパッチが別の変異で再発する構造的な問題であり、機能自体の撤去（方針メモ-2、Opus セカンドオピニオンに基づく）で対応 |
| F23 | 独立-4 | medium | no | self-inflicted | acceptance-asymmetry-nashi | fixed | 「なし」行の全列 `-` 検査タプルがクラスタ列を含んでおらず、実指摘行では `-` 禁止・なし行では任意文字列可という非対称が残っていた。機能撤去により解消 |
| F24 | 独立-4 | low | no | self-inflicted | weak-test-assertion | fixed | `test_cluster_dash_placeholder_is_rejected_on_a_real_finding_row` のアサーションが既存の空クラスタ文言とも一致し新検査を特定できていなかった。機能撤去に伴いテスト自体を削除 |
| F25 | 独立-4 | advisory | no | self-inflicted | redundant-dash-skip | fixed | `severe_clusters_by_jun` 構築時の `cluster == "-"` チェックが、fail() 済み行だけが通る到達性の低い分岐になっていた。機能撤去により解消 |
| pm-2 | 方針メモ-2 | - | - | - | - | - | なし |
| F26 | PR後-1 | medium | no | self-inflicted | shared-module-load-untested | fixed | 共有モジュール（`scripts/lib/repository_identity.py`）のロードが SKIP-B より前にあり、欠落・破損時は fail-closed（FAIL）になる設計自体は正しいが、その経路を固定するテストが無かった。`review-log-present.sh` にモジュール欠落・破損の2パターンの regression test を追加し、SKIP-B の前提が「モジュール同梱」になったことをヘッダコメントと changelog Known limitations に明記 |
| F27 | PR後-1 | medium | no | self-inflicted | shared-module-load-untested | fixed | 上と同じロード経路が `version-not-consumed.sh` にも対で存在し、テストが無かった。同じ2パターンの regression test を `test_changelog_fragments.py` の `VersionCheckTests` に追加 |
| F28 | PR後-1 | medium | no | self-inflicted | dash-cluster-orphaned-guard | fixed | 撤回したクラスタ再発検知機能の残骸として、実指摘行のクラスタ `-` 拒否分岐にテスト・changelog記載が無く、コメントも存在しない機械化（クラスタ再発検知の無効化）を前提にしていた。列対称性（severity/実害/自己起因/対応の4列と同じ扱い）を独立の根拠として残存を正当化し、コメントを書き直し、regression test を追加、changelog Changed に記載 |
| F29 | 独立-5 | high | yes | self-inflicted | except-exception-misses-systemexit | fixed | 共有モジュールロードの `except Exception` は `SystemExit`（`BaseException` 派生）を捕捉できず、モジュールの exec 中に `SystemExit` が送出されるとスクリプト全体が rc=0 で静かに成功してしまう（`SKIP-B:` 行すら出ない）。F26/F27 の regression test はこの変異を検出できていなかった。`except BaseException` に広げ、`SystemExit` を送出するモジュールのケースを両ファイルに regression test で追加 |
| F30 | 独立-5 | medium | no | self-inflicted | dash-cluster-blacklist-asymmetry | fixed | F28 で書いたコメント「他4列と同じ扱いに揃える」は不正確だった。他4列は固定語彙のホワイトリスト検査だが、クラスタ `-` 拒否はプレースホルダー1点のみを拒否するブラックリスト判定で、受理集合は揃っていない（`n/a`・`--`・空白等は依然通る）。クラスタ名は自由記述の分類ラベルであり列挙値ではないため、ホワイトリスト化はスコープ外としつつ、コメントと changelog Known limitations をブラックリスト判定である実態通りに書き直した |
| pm-3 | 方針メモ-3 | - | - | - | - | - | なし |
| F31 | 独立-6 | high | yes | self-inflicted | except-exception-misses-systemexit | fixed | F29 と同一クラスタ。`repository_identity.py` ロードとは別に、`release.py` をロードする箇所（両ファイルに1箇所ずつ）にも同一パターンの `except Exception` が残っており、同じ SystemExit fail-open が存在した（release 変数が未初期化のモジュールオブジェクトのまま後続で参照される別の実害もある）。安全策4に従いユーザー確認・Opus セカンドオピニオン（方針メモ-3）を経て、動的モジュールロードを専用のブートストラップ関数 `load_dynamic_module()` に一本化し、`exec_module()` 呼び出し1箇所だけを `except BaseException` にすることで両ロード経路を同時に閉じた。release.py が SystemExit を送出するケースの regression test を両ファイルに追加 |
| F32 | 独立-7 | medium | no | self-inflicted | dynamic-module-loader-copy-untested | fixed | `load_dynamic_module()` は scripts/lib/ へ切り出さず両チェックスクリプトにコピペしたまま（Opus のセカンドオピニオン: 切り出すとブートストラップ自体のロードに同じ保護が要る循環になるため妥当と判断済み）だが、コピペである以上、両ファイルの実装が同期していることを固定する契約テストが無かった。`test_repository_identity.py` の `SharedModuleWiringTests` に、型注釈の差異を正規化して両実装を比較する contract test を追加 |
| F33 | 独立-7 | medium | no | self-inflicted | except-exception-misses-systemexit | accepted | `version-not-consumed.sh` の `release.load_fragments(root)` 呼び出し（load_dynamic_module() の外側、モジュールロード成功後）は `except Exception` のままで `SystemExit` を捕捉しない。F29/F31 と同一クラスタの潜在系だが、現時点では release.py 内に到達可能な SystemExit 経路が無い（`if __name__ == "__main__":` ガード内のみ）ため実害は無い。将来 release.py の変更で到達可能になった場合の残存リスクとして changelog Known limitations に開示し、本PRのスコープでは対応しない（F34 の構造的解決により後日この受容自体も解消） |
| F34 | PR後-2 | high | yes | self-inflicted | except-exception-misses-systemexit | fixed | load_dynamic_module() は exec_module() 呼び出しの SystemExit だけを守り、動的ロードしたモジュールへの「呼び出し」4箇所（identity_lib.repository_identity()、release.NAME_RE.fullmatch() 複数箇所、release.load_fragments()）は guard 外のままで同型の fail-open が再発する経路だった（独立-5・独立-6に続き3回目、同一クラスタ）。個別呼び出し箇所を except BaseException で塞ぐ対処（独立-5/6と同じ列挙型パッチ）ではなく、Opus のセカンドオピニオンに基づき、両チェックスクリプトの本体を run() 関数に集約し、run() が正常return しなかった経路（die() の明示的 SystemExit(1)・呼び出し中の想定外の SystemExit・その他の例外を区別しない）を呼び出し元の except で一律 FAIL に合流させる構造に変更した。validate-plugin.sh 側にも、rc=0 なのに VERDICT 宣言行（OK または SKIP）が無い check を一律で FAIL にする番兵を全46 BLOCK チェック共通で追加し、宣言なき成功を機械的に拒否する二層構造にした |
| F35 | PR後-2 | medium | no | self-inflicted | changelog-known-limitations-inaccurate | fixed | changelog の Known limitations が「release.load_fragments() 呼び出しだけが残渣で実害なし」と書いていたが、identity_lib.repository_identity() 呼び出しと release.NAME_RE.fullmatch() 呼び出しも同じ穴だった。F34 の構造的解決で全呼び出し箇所を閉じたため、この限界の記述自体を changelog から削除し、実態（呼び出し箇所は個別にではなく run() 構造で一括して閉じた）に合わせて書き直した |
| pm-4 | 方針メモ-4 | - | - | - | - | - | なし |
| F36 | 独立-8 | high | yes | self-inflicted | test-coverage-guard-removal-undetected | fixed | VERDICT 番兵の唯一の契約テスト test_validate_plugin_verdict_sentinel.py が git 未追跡(untracked)のままだった。commit すると番兵ロジックだけが入りテストは入らず、番兵を削除しても検知できない状態だった。git add してコミットに含めた |
| F37 | 独立-8 | medium | no | self-inflicted | record-audit | fixed | changelog.d/ の変更断片が、今回の主要変更（VERDICT 番兵、run() 化、46本への VERDICT 行追加）を Summary/Added/Changed/Affected Files に記載しておらず、既に閉じた fail-open を「未対応の限界」と書いたまま逆の内容になっていた。断片を実装と一致するよう更新した |
| F38 | 独立-8 | medium | yes | self-inflicted | fail-open-check-silently-skipped | fixed | validate-plugin.sh の check 呼び出しが manifest.tsv の read ループの stdin リダイレクトを継承していたため、stdin を読む check が manifest の残り行を食い、後続の check が一度も実行されずに rc=0 で完走する経路があった（実機再現済み）。`</dev/null` で切った |
| F39 | 独立-8 | low | no | self-inflicted | unescaped-regex-metacharacter | fixed | check_name を未エスケープで VERDICT 検査の grep -E に埋め込んでおり、正規表現メタ文字を含む名前だと誤マッチの余地があった（現行46名は無害だが将来のmanifest追加で問題になりうる）。manifest 読み込み時に `[A-Za-z0-9_-]+` へ限定する検査を追加 |
| F40 | 独立-8 | low | no | self-inflicted | unvalidated-return-value | fixed | run() の戻り値が "OK"/"SKIP" 以外を返さないことを検証していなかった（現状の全 return はこの2値のみで実害は無いが、将来の変更で宣言と無関係な文字列がそのまま VERDICT 行に出力される余地があった）。except 節と同じ try 内で検証し fail-closed に合流させた |
| F41 | 独立-8 | low | no | self-inflicted | asymmetric-guard-placement | fixed | review-log-present.sh の SKIP-B 返却前に、sibling の version-not-consumed.sh と同じ `if failures: die()` ガードが無かった（現状は到達前の fail() が全て直後に die() するため到達不能だが、対称性のため揃えた） |
| F42 | 独立-8 | low | no | self-inflicted | verdict-vocabulary-asymmetry | accepted | opt-in が既定で無効な2本（superpowers-benchmark-gate.sh・skill-red-green-gate.sh）は、何も検査していない実行でも VERDICT: OK を宣言し、同様に検査対象が無い external-verifier-smoke.sh・docs-links-valid.sh の SKIP 宣言と語彙が非対称。本PRのスコープでは対応せず changelog Known limitations に開示 |
| F43 | 独立-8 | low | no | self-inflicted | stdout-stderr-ordering-regression | accepted | check_output のキャプチャが stdout のみのため、check が stderr に書いた診断行と stdout の出力順が入れ替わる（判定には影響しない）。長時間 check の進捗もリアルタイムに見えなくなる。本PRのスコープでは対応せず changelog Known limitations に開示 |
| F44 | 独立-8 | advisory | no | self-inflicted | new-contract-undocumented | accepted | VERDICT 行必須という新しい契約が CONTRIBUTING.md 等に文書化されておらず、47本目の check を追加する人が VERDICT_MISSING のエラーメッセージで初めて気づく。後続課題とする |
| F45 | 独立-8 | advisory | no | self-inflicted | unused-import | fixed | test_validate_plugin_verdict_sentinel.py の import shutil・import sys が未使用だった。削除した |
| F46 | 独立-8 | advisory | no | self-inflicted | no-cross-check-with-fail-line | accepted | VERDICT 番兵は宣言の有無しか見ず、同じ出力中の自己申告 FAIL: 行との整合を検査していない。46本の check 本体は fail() した時点で die()/非0 exit するため現行実装では両方が同時に出る経路は無いが、将来の実装ミスに対する二重化が無い。後続課題とする |
| pm-5 | 方針メモ-5 | - | - | - | - | - | なし |
| F47 | PR後-3 | high | yes | self-inflicted | systemexit-code-posix-mask-fail-open | fixed | F34 で追加した except SystemExit ハンドラが error.code を読み `code if code != 0 else 1` に倒していたが、SystemExit(256)（256の倍数）は POSIX のシェル終了コードマスク（exit_code & 0xFF）でシェル側の実終了コードが0になるため、この判定を通過して静かに成功してしまう fail-open だった（validate-plugin.sh 経由の公式入口は VERDICT_MISSING で検出できるが、check スクリプトの直接実行では偽の成功になる）。独立-5・独立-6・PR後-2に続き4回目の同種high（安全策4再発火）。Opus へのセカンドオピニオン（方針メモ-5）で「機序は別だが受理集合は開いていない」との判断を受け、error.code を一切読まず常に sys.exit(1) にする実装に修正し、両ファイルの except SystemExit ハンドラの対称性・error.code 未参照を固定する contract test を追加した |
| F48 | PR後-3 | medium | no | self-inflicted | changelog-test-count-mismatch | fixed | changelog.d/ の Validation/Eval Impact が test_validate_plugin_verdict_sentinel.py を「10 tests」と記載していたが実数は8（Added節の記載と不一致）。あわせて test_repository_identity.py の Added節の記載が「9 tests」だったが実数は10（Validation/Eval Impact節の記載とも不一致）だったため、この機会に合わせて修正した |
| F49 | PR後-3 | medium | no | self-inflicted | test-power-dead-defensive-branch | fixed | F40（run() 戻り値検証）・F41（review-log-present.sh の SKIP-B 前 if failures: die() ガード）は、いずれも現状のコードパスでは到達不能な防御的コードで、削除しても既存テストスイートは green のまま通る（test-power指摘、mutation testing相当）。root CLAUDE.md でmutation testing自体は既にスコープ外と判断済みのため、強制的に踏ませる専用テストは追加せず、changelog Known limitations に「実測で検証済みではなく、対称性・将来の変更に備えた防御的追加である」ことを明示する開示で対応した |
| F50 | 独立-9 | low | no | self-inflicted | changelog-test-count-mismatch | fixed | changelog.d/ が test_repository_identity.py のテスト数を「10 tests」と記載していたが、この差分自体が同ファイルに test_systemexit_handler_does_not_read_error_code を1本追加したため実数は11。Added節・Validation/Eval Impact節の2箇所を「11 tests」に修正した |
