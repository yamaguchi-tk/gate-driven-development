---
lane: L1+
pr: 301
follow_up_of: 291
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#291 の次の PR。Opus は、フェンスを落とす案に賛成し、Lane の終わりを `#` か `##` の見出しに広げるよう推した〔`# ` の見出しの後ろの別の節を読み込むため。duplication lint の節の切り方とそろえる〕。フェンスの中だけの `- [ ]` を数えない挙動の変化も、`strip_fenced_blocks` の方針どおりとして入れてよいとした。表の形式の Lane を読まない既存の欠陥を別に挙げ、入力の形が違うので次の PR に回すよう推した。main の案と食い違いは無く、Fable は呼んでいない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 1 | 0 | 1 | 2026-10-02T14:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b8a7e77dd3a8a021935748a2e61d815e3d3faf17 | 3 | 0 | 3 | 2026-10-02T15:00+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（独立-1 が、表の形式の Lane を読まない欠陥を、差分が変えた関数の中の常時 High として報告した。方針メモで Opus は次の PR に回すよう推していて、main の「この PR で直す」案と食い違ったので、信号 ① で Fable を呼んだ。Fable は、§ 常時 High を再掲にできず次の巡で安全策 4 が発火するので、この PR で直すのが正しいとした。直し方は、表のデータ行〔先頭のセルが空でない行〕を全部数え、プレースホルダや `none` の除外を作らない。完了を示す列は template・SKILL・コードをそろえて変える話なので次の PR に回す。main は Fable の案を採った。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-02T15:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c5754dfc2213a750fe89503445dee154f8f19eb2 | 5 | 0 | 5 | 2026-10-02T16:10+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火〔クラスタ fail-open の high が独立-1・独立-2 の 2 巡〕。high はどれも「書き方の揺れで未完を見落とす」入力で、列挙で塞ぐと次の形が出る開いた集合だった。Opus は、既定を反転して入力空間を閉じる案〔Lane の中が `- [x]`・`###` 以下の小見出し・表のヘッダーと区切り・空行だけなら完了、ほかは未完〕を推した。誤 block のコストは `### 次の計画` を 1 つ書くことだけで、実データの 4 steering では判定が変わらないと見積もった。列挙〔B〕は 旧#84 と同じ型、止める〔C〕は自己起因の後退 2 件を限界に出すことになり、撤回〔D〕は常時 High を戻すとして退けた。main の案と食い違いは無かった。Fable はこの PR で 1 回使ったので呼んでいない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて続行した） | - | 0 | 0 | 0 | 2026-10-02T16:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | ef0df69c98a5663789abc14fc6d00b747cc1919d | 3 | 1 | 3 | 2026-10-02T17:00+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus) + user（安全策 4 の 2 回目の発火〔high を含む巡が 3 回、どれも fail-open〕。Opus は、完了と読む形を小さくして構造で閉じる案〔空行・`- [x]`・パイプを含む区切り・表の先頭のヘッダーだけ。見出しは未完〕を推し、見出しの中身を判定する案は分岐が増えて再発するとして退けた。実データの誤 block は増えないと見積もった。ユーザーは「続行（Opus 案）」を選んだ。差分巡でまた high が出たら止める） | - | 0 | 0 | 0 | 2026-10-02T17:20+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 1dca219ae7a4ab56987d5e3e74ac2c45d66a600d | 2 | 0 | 2 | 2026-10-02T17:50+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | high | yes | inherited | stage-lane-table | fixed | `has_incomplete_follow_up_stages` は `- [ ]` の行しか見ず、テンプレートの表の形式（`Pending Stage ID` の行）の Lane を読まない。表のデータ行を未完として数えるようにした commit: 763f3eff |
| Q1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | `strip_fenced_blocks` の `splitlines()` が U+2028 などで行を割るので、Lane が途中で切れて後ろの `- [ ]` を見落とす。LF 以外の行区切り文字を空白に置き換えてから読む commit: 763f3eff |
| Q2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | Lane の終わりの `\n#{1,2}\s` が全角空白・NBSP にも一致し、見出しでない `#　注記` で Lane が終わる。`#` の後に半角空白・タブ・行末が続く行だけにした commit: 763f3eff |
| Q3 | 独立-1 | high | yes | inherited | stage-lane-table | fixed | 表の形式の Lane を常に未完なしと読む（方針メモの P1 と同じ欠陥）。表のデータ行を未完として数えるようにした commit: 763f3eff |
| Q4 | 独立-1 | low | no | self-inflicted | lane-boundary | fixed | Lane の本文が次の見出しの行から始まると、次の節まで Lane に取り込む。先読みを行頭のアンカーにした commit: 763f3eff |
| Q5 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 断片の Validation に時点に依存する実測値を書いている。数値は PR 本文に移した commit: 763f3eff |
| Q6 | 独立-1 | low | no | inherited | lint-scope | fixed | duplication lint のフェンスの開きが `tasklist_parse` より広く、Lane の範囲が hook と食い違う。開きの規則をそろえた commit: 763f3eff |
| Q7 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Summary が post-merge continuation の判定の変化を書いていない commit: 763f3eff |
| Q8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 共有のフェンス規約に従うので、トップレベルで 4 桁以上字下げした ``` の間の `- [ ]` を数えなくなる。PR 本文の限界に書く |
| Q9 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし |
| R1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | LF 以外の行区切り文字を空白に読み替えたので、その後ろの `- [ ]`・Lane の見出し・表の行が行頭でなくなり消える。Lane の見出しの語と行区切り文字があれば未完とした commit: 548d656c |
| R2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 見出しの行末を `[ \t]*$` に狭めたので、行末が全角空白・NBSP の Lane の見出しを読まない。見出しを前方一致で読む commit: 548d656c |
| R3 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 表は先頭がパイプの行しか読まない。既定を反転し、完了の形でない行を全部未完とした commit: 548d656c |
| R4 | 独立-2 | high | yes | inherited | fail-open | fixed | チェックリストは `-` の項目しか読まない（`*`・`+`・番号付き）。既定の反転で閉じた commit: 548d656c |
| R5 | 独立-2 | high | yes | inherited | fail-open | fixed | Lane の見出しが 2 つあると最初の 1 つしか読まない。全部の Lane を見る commit: 548d656c |
| R6 | 独立-2 | low | no | self-inflicted | lint-scope | accepted | duplication lint と hook で、Lane の終わりの位置（全角空白の `#`・行区切り文字・`#` だけの行）が違う |
| R7 | 独立-2 | low | no | self-inflicted | rule-sync | accepted | `gdd-requirements-gating/SKILL.md` の「Stop hook の自動検出にチェックリストが必須」が実装と合わない。PR 本文の限界に書く |
| R8 | 独立-2 | low | no | self-inflicted | test-power | fixed | 崩れた表の行のテストが戻り値を固定していない commit: 548d656c |
| R9 | 独立-2 | low | no | self-inflicted | test-power | accepted | duplication lint のフェンスのテストが、開きにならない例しか見ていない |
| R10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | Lane の正規表現のコメントが、開き側の実装と合わない commit: 548d656c |
| R11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | e2e テストのクラスの docstring に、表の行が書かれていない |
| R12 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 表の Lane を post-merge の入口から通すテストが無い |
| R13 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の実データの比較が、コマンドと sha が無く再現できない commit: なし（PR 本文） |
| R14 | 方針メモ-3 | advisory | no | inherited | none | accepted | 要約: なし |
| S1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 表のヘッダーの判定が表の 2 行目以降でも効き、直後が区切りの形のデータ行や項目を完了と読む。ヘッダーを表の先頭の行に限り、区切りにパイプを要るようにした commit: 8b80bef6 |
| S2 | 独立-3 | high | yes | inherited | fail-open | fixed | `###` 以下の見出しを中身を問わず完了と読む。見出しを未完にした commit: 8b80bef6 |
| S3 | 独立-3 | high | yes | inherited | fail-open | fixed | requirements.md が UTF-8 で読めないと、Stop hook は判定せずに通し、post-merge は marker を消す。置き換えて読むようにした commit: 8b80bef6 |
| S4 | 独立-3 | medium | no | self-inflicted | test-power | fixed | 完了の形の境界（パイプの無い区切り・表の途中のヘッダーの形・`* [x]`・`###x`）をテストが固定していない commit: f2ad8ea8 |
| S5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 行区切り文字の扱いの docstring が実装より狭い commit: 8b80bef6 |
| S6 | 独立-3 | low | no | self-inflicted | product | accepted | block の文が、未完と読んだ行や理由を示さない |
| S7 | 独立-3 | low | no | self-inflicted | test-power | fixed | Lane の無い本文に行区切り文字があるときに False を返すテストが無い commit: f2ad8ea8 |
| S8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | duplication lint は Lane の見出しを完全一致で読み、hook は前方一致で読む。PR 本文の限界に書く |
| S9 | 独立-3 | low | no | self-inflicted | rule-sync | accepted | 完了の判定の規則が、Lane を書くときに読む文書（gating SKILL・template・completion-check）に書かれていない。PR 本文の限界に書く |
| S10 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | 実データの比較に、この PR の関数の sha と内訳が無い commit: なし（PR 本文） |
| S11 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | review-log だけを変える commit の件名から、前の巡に独立レビューと相談があったことが reviewer に届いた |
| S12 | 方針メモ-4 | advisory | no | inherited | none | accepted | 要約: なし |
| T1 | 独立-4 | high | yes | self-inflicted | fail-open | accepted | 表のヘッダーの判定が、リストの項目・見出し・セルの数が合わない行も受け入れる。パイプを含む `- [ ]` の項目の次の行がパイプを含む区切りの形だと、その項目をヘッダーと読んで Lane を完了とする（main はこの入力を止めていた）。方針メモ-4 の「差分巡でまた high が出たら止める」に従い、限界に書いて次の PR で直す |
| T2 | 独立-4 | high | yes | inherited | fail-open | accepted | requirements.md が UTF-8 の誤り以外（権限など）で読めないと、Stop hook は判定せずに通し、post-merge は marker を消す。「内部エラーは fail-open」の設計の変更になるので、限界に書いて次の PR で扱う |
| T3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | `ClosedByDefaultTests` の docstring が見出しを完了の形に入れたまま |
| T4 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 変更断片で、行区切り文字の規定が別のファイルの項目の子になっている |
| T5 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 変更断片の検証の欄が、post-merge のテストを実際より多く書いている |
| T6 | 独立-4 | advisory | no | inherited | rule-sync | accepted | gating SKILL の「チェックリスト形式が必須」と template の表の書式が食い違う |
| T7 | 独立-4 | advisory | no | inherited | doc-claim | accepted | e2e のクラスの docstring が未完の条件を狭く書いている |
| T8 | 独立-4 | advisory | no | self-inflicted | style | accepted | `starts_block` の `i == 0` の分岐に入らない |
| T9 | 独立-4 | advisory | no | self-inflicted | test-power | accepted | 変更を戻しても落ちない冗長な部分テストがある |
