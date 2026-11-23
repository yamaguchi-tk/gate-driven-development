---
lane: L1+
pr: 218
follow_up_of: 125
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。Opus の推奨はメインの案と食い違わず、Fable は呼んでいない） | - | 1 | 1 | 1 | 2026-09-28T21:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3be4bfd9a239b0efd9217e00d2ff777e6ef1842f | 4 | 0 | 4 | 2026-09-28T22:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | fb5657f16a5ed9c291faacca23139f01355362df | 2 | 1 | 2 | 2026-09-28T19:45+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の発火。独立-1 F3・独立-2 G1 で同じクラスタ unreadable-steering-scan の high を含む巡が 2 回。ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。Opus は A を狭めて続行を推奨し、メインの案の線引き〔merge gate の中を列挙で閉じる〕は閉じないと指摘した。メインは Opus の線に合わせたので食い違いは残らず、Fable は呼んでいない） | fb5657f16a5ed9c291faacca23139f01355362df | 1 | 0 | 1 | 2026-09-28T20:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 87618ba5d05d23be1912a4e57a14f4577e483a67 | 2 | 1 | 2 | 2026-09-28T20:15+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の 2 回目の発火。high を含む巡が 3 回、クラスタ unreadable-steering-scan が 3 回、独立レビューは上限の 3 巡。ユーザーの 2026-09-28 の決定で、確認は内部の相談で代えた。メインの案〔止める〕と Opus の推奨は一致し、Fable は呼んでいない。H1・H2 は base 41b78164 でも同じ入力が同じ素通りになることを Opus がコードで確かめ、決定 5〔直す次の PR を続けて出すならマージしてよい〕を当てた） | 87618ba5d05d23be1912a4e57a14f4577e483a67 | 0 | 0 | 0 | 2026-09-28T20:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | high | yes | inherited | leading-zero-pr-number | fixed | 先頭 0 の番号は、台帳の照合だけでなく本体（marker のある worktree の done の steering）でも一致せずに証跡の検査なしで通る（`gh pr merge 007` で実測）。台帳の関数の中ではなく入口で 1 回正規化し、両方を閉じた（5443d8b5） |
| P2 | 方針メモ | medium | no | self-inflicted | ledger-read-fail-open | fixed | 「1 回の cat で読む」でも、行を here-string やプロセス置換で回すと、そのリダイレクトの失敗で loop を飛ばして miss に進む（旧#128 と同じ型）。行はパラメータ展開で回した（5443d8b5） |
| P3 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | 新しい local は値つきで初期化する（set -u）、task dir の glob が 0 件のときの `-d` ガード、正規化に算術展開を使わない。実装とテスト（全部 0・空の `.steering`）に入れた（5443d8b5） |
| P4 | 方針メモ | advisory | no | self-inflicted | memo-wording | fixed | 壊れた symlink の扱いを台帳・root・`.steering`・task dir・state.md で揃え、台帳の親が辿れないときも unreadable にした。root がファイル・state.md がディレクトリを unreadable にするのは、hit はありえない誤 block だが、repo 内へ移れば（git cwd の経路）通るので受け入れる、と理由を書き直した（5443d8b5） |
| P5 | 方針メモ | advisory | no | inherited | ledger-scan-limits | accepted | ドットで始まる task dir は台帳の glob では拾わず、本体の `find` は拾う。台帳は追記だけで刈り込みが無く、全走査で state.md ごとの awk が増える。`gdd_extract_doc_field` の読み取り失敗は miss に落ちる。root の祖先が辿れないときは「無い」になる。PR 本文の限界の節に書く |
| P6 | 方針メモ | advisory | no | inherited | pr-number-forms | accepted | `#7`・`+7` を gh がどう扱うかは未確認。parser は番号にしないので、台帳では unknown になる。旧#126 とは別のクラスなので、この PR では扱わない |
| F1 | 独立-1 | high | yes | self-inflicted | leading-zero-pr-number | fixed | 経路: 入口の番号の正規化 → 本体の `*"/pull/$PR_NUMBER"` の比較 3 か所。state.md の URL 側を正規化していないので、`/pull/007` の steering に `gh pr merge 007` が以前の block から素通りに反転し、台帳の経路とも割れる。URL の番号の比較を `_mg_url_matches_number` にまとめて本体と台帳で使った（cb98bbf5） |
| F2 | 独立-1 | high | yes | self-inflicted | leading-zero-pr-number | fixed | bash の `${x#"${x%%[!0]*}"}` は 0 の個数に二乗で効く（実測: 10 万個で 9 秒）。hook の timeout は素通り。正規化を python の `lstrip` に移し、長すぎる URL は比べずに止める側に倒した（cb98bbf5） |
| F3 | 独立-1 | high | yes | inherited | unreadable-steering-scan | fixed | 経路: 台帳の走査 → 同じ入力を読む本体の探し直し `_mg_match_steering_by_target`。読めない state.md・辿れない task dir を飛ばし、none で素通りする。共通の `_mg_steering_unreadable` で読めないものを伝え、none なら state-unreadable で止めた（cb98bbf5） |
| F4 | 独立-1 | high | yes | inherited | ledger-kind | fixed | 経路: 台帳の種類の判定 → 同じ台帳を開く書く側 `gdd_pr_roots_register`（pre-PR gate）。FIFO の grep で待ち続けて timeout し、pre-PR gate の検査ごと素通りする。通常ファイルでない台帳は開かないようにした（cb98bbf5） |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `_mg_ledger_verdict` の見出しのコメントが、unreadable の条件・全走査・経路ごとの倒し方に追いついていない。更新した（cb98bbf5） |
| F6 | 独立-1 | low | no | self-inflicted | test-power | fixed | 新しいテストが GDD_HOOK_STATE_DIR を実行環境から引き継ぎ、手元の台帳を読みうる。`drop_env` で落とす `_hook` を通した（e03a0bf5） |
| A1 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 未リリースの断片 `changelog.d/20260918-merge-gate-non-gdd-merge.md:85-86` の「未修正」の限界が、この PR の後は古くなる。他の PR の断片は通常の PR で書き換えないので、リリース時に直す候補にした |
| A2 | 独立-1 | advisory | no | inherited | product | accepted | 台帳が読めないことで止めるとき、案内文が台帳に触れない（repo 内へ移れば通る出口はある）。PR 本文に列挙する |
| G1 | 独立-2 | high | yes | inherited | unreadable-steering-scan | fixed | 経路: `_mg_steering_unreadable` と state-unreadable の block → 同じ `.steering/*/state.md` を読む resolver → `!= found` の分岐。単一 steering の task dir が辿れない・`.steering` に x が無いと、resolver が none を返し承認も証跡も見ずに通る。読める steering がもう 1 件あると止まり、件数で反転する。`!= found` の分岐でも `_mg_steering_unreadable` が真なら state-unreadable で止めた（ecf7daeb） |
| G2 | 独立-2 | medium | no | self-inflicted | test-power | fixed | found の経路に足した block（`_MG_MATCH_UNREADABLE` の none）を通るテストが 0 本。3 本のうち 1 本は差分前でも通る。G1 の対のテスト（読める別 PR の steering と読めない steering が 1 件ずつ）で閉じる。対のテスト（読める別 PR の steering と辿れない steering が 1 件ずつ）で found の経路の block を通るようにした（4af485cc） |
| G3 | 独立-2 | high | yes | inherited | fifo-hang | fixed | `_mg_log_suppressed` が抑止ログを種類を確かめずに `>>` で開く。FIFO だと open が戻らず、降格経路と旧書式の経路で hook が timeout して素通りする（差分の外。§ 常時 High・実害クラスなのでこの PR で直す）。在るのに通常ファイルでないログは開かないようにした（ecf7daeb） |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「本体の `find` と同じ範囲」のコメントが symlink の扱いで実態と合わない（find は symlink の task dir・state.md を列挙しない）。follow_up_of の PR なので、2 巡目の ① の low は PR 本文の限界の節に書く |
| G5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 長い PR URL の限界に、台帳の照合では repo も比べない（marker の無い場所からの merge は repo によらず止まる）ことが無い。PR 本文の限界の節に書く |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | found の経路の説明コメントと `_mg_match_steering_by_target` の説明が、state-unreadable の block を書いていない。PR 本文の限界の節に書く |
| G7 | 独立-2 | low | no | self-inflicted | test-power | accepted | 長い URL の台帳で repo の比較を飛ばす分岐を判別するテストが無い（repo が違う長い URL の形）。PR 本文の限界の節に書く |
| G8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | state.md の URL の番号の後ろに余り（`/pull/7/files`）があっても本体の経路で一致するようになった（止める側への変更）。PR 本文に書く |
| Q1 | 方針メモ-2 | high | yes | self-inflicted | unreadable-steering-scan | fixed | `_mg_steering_unreadable` は task dir を x だけで「読める」とするが、本体と resolver の `find` は task dir の一覧（r）も要る。x だけの task dir は find に拾われず、読めないとも判定されずに素通りする。task dir の判定を一覧できるディレクトリにする。task dir を一覧できるディレクトリで判定するようにした（ecf7daeb） |
| Q2 | 方針メモ-2 | advisory | no | inherited | fifo-hang | next-pr | 「開いたまま待つ」型は、source している lib（detect-steering.sh・self-review-evidence.sh・merge-gate-evidence.sh）、python の resolver（`scripts/gdd_task_binding.py` の `read_text`）、pre-push gate にも広がり、列挙では閉じない。hook の中に timeout より短い締め切りを置き、切れたら block する仕組みで閉じる。次の PR にする |
| H1 | 独立-3 | high | yes | inherited | unreadable-steering-scan | accepted | 経路: 差分の none 分岐の `_mg_steering_unreadable` → 同じ resolver の none を読む pre-push gate（`run-pre-push-gate-hook.sh:161-167`）。列挙できない steering で Pre-Push Self Review・Independent Review を検査せずに通す。pre-push gate と resolver は差分の外で base と同じ（悪化なし。merge gate との非対称だけが新しい）。安全策 4 の「止める」で直さず、限界の節の先頭に書き、次の PR（helper を lib に移して pre-push gate でも block）で直す |
| H2 | 独立-3 | high | yes | inherited | unreadable-steering-scan | accepted | `_mg_steering_unreadable` は symlink を辿るが、resolver と本体の `find -type f`（-P）は symlink の task dir・state.md・`.steering` の中身を列挙しない。symlink で置いた steering の PR は承認と証跡を見ずに通る。base の本体 find（:674）と none の分岐（:709-716）でも同じ入力が同じ素通りになる（Opus がコードで確認。reviewer の欄は変更箇所だが origin は pre-existing）。実データ 0 件。安全策 4 の「止める」で直さず、次の PR（列挙の結果から unreadable を導く）で H1 と一緒に直す |
| H3 | 独立-3 | medium | no | self-inflicted | test-power | accepted | none 分岐で `.steering` が在るのに通す側（cancelled だけ・空の `.steering`）のテストが無く、条件を `-d .steering` に置き換える変異が生き残る。follow_up_of の PR の 3 巡目の ① の medium なので、PR 本文の限界の節に書く |
| H4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の「state-unreadable で止める」は所有 marker があるときの reason code まで断定している。コメントの「辿れない」が「一覧できない」に追随していない。listdir 化が台帳の照合にも効くことが断片に無い。PR 本文の限界の節に書く |
| H5 | 独立-3 | advisory | no | inherited | bookkeeping | accepted | reviewer の repo 全体の Grep に review-log の行が混じった（判断には使っていない）。agent 定義に「repo 全体の Grep では review-log/ を除く」を足す案は、この PR では扱わない |
| R1 | 方針メモ-3 | - | - | - | - | - | なし |
