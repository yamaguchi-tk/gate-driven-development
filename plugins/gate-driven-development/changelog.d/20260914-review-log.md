---
type: minor
---

#### Summary

軽いレーン（root `CLAUDE.md`）で進める GDD 改善には要件・設計 gate が無く、Codex・独立レビュー・PR 後の指摘が記録として一切残らないため、施策の効果を測定できなかった（X-51）。repo root 直下に `review-log/<changelog.d/ の断片と同じ slug>.md` を新設し、`plugins/gate-driven-development/tests/checks/review-log-present.sh` で強制する（正本: X-52）。副産物として、独立レビュー2巡目の差分絞り込み（`references/independent-review.md` 契約3）を将来 finding 単位で検証できる土台になる。あわせて X-53 対策 A/C/D/E に基づき、root `CLAUDE.md` の L1+ 安全策1（方針メモ）の既定を「開いた入力は狭い側」から「広い側」へ反転し、延期条件の開示と QA 合否基準の2点を追加した。

#### Added

- `plugins/gate-driven-development/tests/checks/review-log-present.sh`（新規）: `changelog.d/` に断片があるのに対の `review-log/` が無い、または書式が不正なら FAIL。検査対象は「merge-base 時点の断片名集合との差分で見つかる、working tree 上に現在ある断片」（コミット状況を問わない。git diff HEAD ベースではない。理由は後述）。断片・対応する review-log の両方とも working tree から直接読む（`git show HEAD:` ではなく `Path.read_text()`）。ROOT が repo root へ解決できない場合は FAIL。統合先 ref だけが解決できない場合は FAIL にする（このチェックには ref なしに「このブランチが新規に足した断片」を特定する層が無いため。理由はスクリプト冒頭のコメントと本 PR の review-log 参照）。書式検査は body 全体を「空行・`## 巡` の表・`## 指摘` の表」だけのホワイトリストで走査する方式に固定し（2026-09-14、Codex レビュー〈H1'〉でテーブルの検査範囲を見出し単位で区切る方式が「未知の見出しの下は無検査になる」fail-open を5回目再発させたため、フェンス判定・見出し終端判定を丸ごと廃止しこの方式に置き換えた）、それ以外の内容（コードフェンスや別見出しを含む）は種類を問わず即 FAIL にするほか、frontmatter（`lane`/`pr` キー）・`## 巡`/`## 指摘` の2表のヘッダーと最低1行・巡と指摘の対応関係（0件は `要約: なし` 行必須）・巡ラベルの値域（X-52 正本: `方針メモ`/`codex-N`/`独立-N`/`PR後-N`）・`## 巡` の high/medium 件数と `## 指摘` の実際の severity 別件数の照合・同じ巡での実指摘行と「なし」行の排他性（混在禁止・「なし」行は0件の巡につき1本のみ）・主要列の非空必須（`## 巡` の reviewer/sha/at、`## 指摘` のクラスタ/要約。sha は方針メモ巡だけ `-` を許可）・`severity`/`実害`/`自己起因`/`対応` の値域（「なし」行以外は固定語彙必須、`-` は不可）・id の一意性まで見る。SKIP-B（repo root が本リポジトリの開発 checkout として解決できない場合）の判定は最終的に git にもディレクトリレイアウトにも一切触れない identity marker 方式にした（2026-09-15、Codex レビュー〈H2→H2'→H3→H4→H5〉で5回連続再発したため root CLAUDE.md 安全策4に基づき Opus へセカンドオピニオンを依頼し、Opus 案を採用）: `git rev-parse --is-inside-work-tree` の成否・`.git` マーカーの `exists()` 判定・ROOT が `<repo_root>/plugins/<ROOT の名前>` と `samefile` かどうかは、いずれも派生信号からの逆算であり、狭めるたびに別の変異（壊れた symlink、環境変数汚染、別名 symlink 経由の basename 不一致）で再発した。加えて layout ベースの判定は、真の消費者環境（marketplace clone）を「開発 checkout」と誤判定する逆方向の false negative も実機に抱えていた（Opus が実機で6パターンの ROOT パスを検証し発見）。代わりに `.claude-plugin/marketplace.json` の `name` フィールド（リポジトリが既に持つ固定の自己申告 identity marker）を読むだけの判定に転換したが、この方式自体も `name` キー欠落・null・非文字列・空文字列（`{}` 等）を等価比較だけで弾こうとして False（別リポジトリ・SKIP-B）に落としてしまう H5 を再発させた。`name` は marketplace の主キーであり、これを欠く manifest はインストール不能な壊れた manifest であるため、`name` が文字列として存在し不一致の場合だけ False、それ以外（欠落・null・非文字列・空文字列、manifest がディレクトリ・壊れた symlink・symlink loop）はすべて None（判定不能）に倒す1ルールへ書き換えた。一致すれば本リポジトリの開発 checkout と確信でき、以後の git 呼び出しの失敗は理由を問わずすべて FAIL（fail-closed）にする。manifest が無ければ SKIP-B、manifest が壊れていて `name` が読めない場合は判定不能として FAIL にする（推測しない）
- `plugins/gate-driven-development/tests/checks/manifest.tsv`: `review-log-present` を BLOCK として登録
- `plugins/gate-driven-development/tests/test_review_log_present.py`（新規、59 tests, 12 subtests）: 上記の contract test
- `review-log/README.md`（新規）: 置き場所の理由と、導入前から存在した7断片の遡及しない旨（cutoff）を記録
- `review-log/20260914-review-log.md`（新規、この PR 自身の記録。実体1つ目）

#### Changed

- root `CLAUDE.md`: 軽いレーンの手順5（Codex）・6（独立レビュー）・7（PR作成）に `review-log/` への記録タイミングを追記。手順6でreviewerに渡す差分から `review-log/` を除外する一文を追記（独立レビューの契約1「実装文脈を渡さない」を壊さないため）。L1+安全策1の方針メモを5点から7点へ拡張し、「開いた入力の既定」を狭い側→広い側へ反転（X-53対策A/B）、「延期・削除する完了条件の開示」「QAの合否基準」の2点を追加（X-53対策C/D/E）
- `plugins/gate-driven-development/tests/test_validate_plugin_check_inventory.py`: canonical チェック一覧に `review-log-present` を追加（`main` 取り込み時の `hitl-lint-gate-wiring` 追加とあわせて 26 + 3 + 17 = 46）
- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`: sibling の `review-log-present.sh` と同じ SKIP-B 設計転換を同時適用した（root CLAUDE.md「対になる片方だけを直さない」規定に基づく）。PR後-8（H3）時点ではレイアウトベース判定・fail-closed 化と `GIT_*` 環境変数除去、PR後-9（H4）時点では identity marker（`marketplace.json` の `name` 一致）方式への転換、PR後-10（H5）時点では `name` フィールドの JSON 型空間（欠落・null・非文字列・空文字列）とディレクトリ・壊れた symlink を None（判定不能）に倒す1ルールへの精緻化、PR後-11（H6）時点では leaf（`marketplace.json` 自体）だけでなく親（`.claude-plugin`）自体が壊れた symlink・symlink loop・通常ファイル・権限拒否ディレクトリの場合も None に倒す既定反転（詳細は Known limitations 参照）。`tests/test_changelog_fragments.py` に regression test を計11本追加（`GIT_DIR` 汚染で誤 SKIP-B にならないこと、壊れた `.git` symlink で SKIP せず FAIL すること、marketplace.json が無い/壊れている場合の SKIP-B/FAIL、別名 symlink 経由でも false SKIP-B にならないこと、identity 不一致ならレイアウトが一致していても SKIP-B になること、`name` の JSON 型空間・manifest がディレクトリ・壊れた symlink でも SKIP-B にならないこと、`.claude-plugin` 自体が壊れた symlink・symlink loop・通常ファイル・権限拒否ディレクトリでも SKIP-B にならないこと、`.claude-plugin` が実在するが `marketplace.json` を持たない単体 plugin リポジトリのレイアウトは引き続き SKIP-B のままであること）

#### Affected Files

- `plugins/gate-driven-development/tests/checks/review-log-present.sh`（新規）
- `plugins/gate-driven-development/tests/checks/manifest.tsv`
- `plugins/gate-driven-development/tests/test_review_log_present.py`（新規）
- `plugins/gate-driven-development/tests/test_validate_plugin_check_inventory.py`
- `review-log/README.md`（新規）
- `review-log/20260914-review-log.md`（新規）
- `CLAUDE.md`（repo root）

#### User Action Required

- なし。軽いレーンで作業する次回以降のブランチから、`changelog.d/` に断片を足す際は対の `review-log/` も作る必要がある（root `CLAUDE.md` の手順に従えば自然に満たされる）

#### Known limitations

- 総件数の before/after 比較はできない。軽いレーンには要件・設計 gate が無く、X-45 の before（558件中286件=51%）は要件・設計段階の指摘であるため、比較できるのは「Codex・独立レビュー・PR後」の3段だけ
- 記録は自己申告であり、`severity`/`実害`/`自己起因`の判定は書き手の主観。X-45の事後分類（Sonnet subagentによる）とは完全には一致しない
- `review-log-present.sh` の強制は `validate-plugin.sh` の手動実行（`CONTRIBUTING.md` に明記された運用規約）に依存する。CI workflow（`.github/workflows/`）や pre-push hook からの自動実行は無い（既存の全 BLOCK チェックと同水準であり、本 PR が新たに弱くしたものではない）。この強制経路の弱さは、body のパース系がここまで何度も再発した根本原因の一つでもある（記録の書式が壊れていても push 自体は止まらないため、パーサー側で閉じるしかなかった）
- `review-log-present.sh` の body 検査（フェンス判定・見出し終端判定・隠し領域）は、独立レビュー・PR 後レビューを通じて計5回同種の fail-open が再発した（独立-1/独立-2/PR後-1/PR後-6/PR後-7）。root CLAUDE.md 安全策4に従い、5回目（PR後-7, H1'）で Opus（claude-opus-5）にセカンドオピニオンを依頼し、対策を「終端判定の精度向上」から「body が受理する文法自体を `## 巡`/`## 指摘` の2表だけに狭めるホワイトリスト化」に転換した。この転換により、コードフェンス・別見出しなど body に置ける内容の種類が構造的に閉じたため、**以降このブランチ・この PR では body のパース方式そのものに対する追加修正は行わない**（新しい指摘が出た場合も、パーサーの調整ではなくユーザーへ方針を差し戻す）
- SKIP-B（消費者環境かどうか）の判定述語は、PR後-6（H2）で導入した「`git rev-parse --is-inside-work-tree` の成否から逆算する」設計を起点に、狭めるたびに別の変異で6回連続再発した（PR後-7〈H2'〉: `GIT_*` 環境変数の汚染、PR後-8〈H3〉: `.git` マーカーの `exists()` が symlink を辿る、PR後-9〈H4〉: ディレクトリレイアウト一致判定〈H3で採用〉が別名 symlink 経由の basename 不一致で真の開発 checkout でも SKIP-B になる、PR後-10〈H5〉: identity marker〈H4で採用〉の `name` 等価比較が `name` キー欠落・null・非文字列・空文字列を素通りして False に落とす、PR後-11〈H6〉: leaf（`marketplace.json` 自体）の異常だけを見ており親〈`.claude-plugin`〉自体が壊れた symlink・symlink loop・通常ファイル・権限拒否ディレクトリの場合を見ていない）。root CLAUDE.md 安全策4（同一クラスタの high が2回続いたらユーザーへ線引きを戻す）が本セッションで4回（H3・H4・H5・H6）トリガーされ、都度 Opus（claude-opus-5）にセカンドオピニオンを依頼した。H4 では実機で6パターンの ROOT パスを検証し、H3 で採用したレイアウトベース判定が H4 だけでなく逆方向（真の消費者環境である marketplace clone を「開発 checkout」と誤判定する false negative）にも壊れていることを実証し、対策を「git・ディレクトリレイアウトいずれかの派生信号からの逆算」から「リポジトリが既に持つ固定の自己申告 identity marker（`.claude-plugin/marketplace.json` の `name`）を読むだけの判定」に転換した。H5 では実機でマシン上の全32件の marketplace.json を検証し、`name` が marketplace の主キーであること・修正後も実在する消費者環境（120 plugin ディレクトリ）の判定に一切差分が出ないこと（逆方向の実害ゼロ）を実証し、`name` が文字列として存在し不一致の場合だけ False、それ以外はすべて None（判定不能）に倒す1ルールへ書き換えた。H6 では、H5 で導入した「None にすべきケースを列挙し、それ以外を False」という形自体が、親ディレクトリの異常という別軸で列挙漏れを起こしていたと判明した（権限拒否のケースは、正しい name の manifest が実在する本物の開発 checkout でも検査全体が黙ってスキップされる、最も重大な形）。個々のケースの列挙で塞ぐと H2〜H4 と同じ「狭めては別の変異で再発する」反復になるため、Opus の提案に基づき既定を反転した: **False（「宣言が無い」）を返してよいのは、対象が本当に存在しないと `FileNotFoundError` で積極的に確認できた場合だけ。それ以外のあらゆる `OSError`（権限拒否・symlink loop・想定外の errno 等）はすべて None（判定不能）に倒す**。これにより未知の errno やファイル種別を新たに列挙する必要が構造的に無くなった。H5・H6 はどちらも H2〜H4（消費者環境かどうかを派生信号から逆算する開いた入力）とは軸が異なり、「宣言を読めなかった場合の既定値」という閉じた分岐だったため、identity marker 設計への転換自体を覆す根拠にはならないと判断した。修正が実在する消費者環境の判定を変えないことを実機153件（`~/.claude/plugins/{marketplaces,cache,local}` 配下・`~/repository` 配下）で確認し、判定が変わったものは0件だった。**この既定反転をもって、以降このブランチ・この PR では SKIP-B 判定述語そのものに対する追加修正は行わない**（新しい指摘が出た場合も、判定ロジックの調整ではなくユーザーへ方針を差し戻す）。sibling の `version-not-consumed.sh` にも同じ修正を同時適用した。唯一原理的に閉じない残差は「本リポジトリ自体を marketplace として clone した消費者環境」（`marketplace.json` の `name` が偶然 `gate-driven-development` と一致する外部リポジトリ）であり、限界として受け入れる。`name` の前後空白・大小文字違いも意図的に締めていない（`strip()` した非空文字列であることだけを要求し、比較は厳密一致）。`.claude-plugin` ディレクトリ自体が不在、または実在するが `marketplace.json` を持たない場合（実機に複数実在する単体 plugin リポジトリのレイアウト、例: `~/.claude/plugins/local/` 配下の単体 plugin 6 件が `.claude-plugin/plugin.json` のみのケースを実機で確認）は、引き続き意図的に SKIP-B のまま締めていない（締めると正当な消費者環境を誤 FAIL させる新しい逆方向の穴になるため）
- 導入 PR のマージ時点で `changelog.d/` に既に存在した7断片は、遡及的に review-log を作らない（`review-log/README.md` に一覧を記録済み）
- `pr:` frontmatter キーは存在のみ必須とし、値は空でも通す（手順7でPR作成後に埋める運用のため）。埋める仕組みを強制していないため、値が空のまま残るリスクがある
- `severity`/`実害`/`自己起因`/`対応` の値域チェックはセル単位の固定語彙一致のみで、判定内容そのものの正しさ（自己申告の精度）は検証しない
- `## 巡` の `blocking` 列は非負整数であることのみ検証する。`severity` の値域（high/medium/low/advisory）に blocking に対応する値が無く `## 指摘` から件数を導出できないため（X-52 正本にも blocking 専用の列は定義されていない）、high/medium のような対応関係の照合はできない
- `independent-review.md` 契約3の絞り込み条件そのものの変更は本PRの対象外（別タスク。記録が溜まってから）
- H4/identity marker 対応後の独立レビュー（独立-4、sha 1a24a01）で low 2件が見つかった。(1) `repository_identity()` の `manifest.is_file()` が try/except の外にあり、権限エラー（EACCES）で捕捉されない traceback 終了になる、という指摘（review-log F31）。H5 対応時に実機で再検証したところ、この環境の Python（3.14.7）では `is_file()` が権限エラーを内部で握って `False` を返すため再現せず、対応不要と判断した。(2) manifest が同名のディレクトリの場合に `is_file()` が `False` を返し「判定不能を無いと誤認しない」という設計原則とやや非対称、という指摘（review-log F32）。H5（F33）対応で `repository_identity()` を書き換えた際に副次的に解消した（ディレクトリ・壊れた symlink・symlink loop を明示的に None に倒す分岐を追加）
- plugin cache 配置等（`ONBOARDING.md` 手順3が想定する消費者環境）で repo root が git work tree にならない場合、`review-log-present` は SKIP-B になり検査が働かない。この場合、消費者は本チェックの効果を受けない（review-log の運用自体が本リポジトリ固有のものであり、消費者リポジトリでは元々対象外）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 新規 contract test: `test_review_log_present.py`（59 tests, 12 subtests）
- `test_changelog_fragments.py` に SKIP-B 設計転換の regression test を計11本追加（42 tests, 46 subtests）
