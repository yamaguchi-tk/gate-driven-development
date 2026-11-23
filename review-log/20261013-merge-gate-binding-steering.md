---
lane: L1+
pr: 454
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-13T10:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b6421fd8a33cbaa49917e9c026bc89630035a2e9 | 3 | 2 | 3 | 2026-10-13T11:20+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-10-13T11:52+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | a649c805f9a3b398840193770314dcda26d5a6b9 | 1 | 3 | 1 | 2026-10-13T12:35+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-13T14:00+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c261813988f24c9d012bffed149a423627b1a29a | 0 | 1 | 0 | 2026-10-13T14:40+09:00 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | a8e36da038c33cfb6dccbfa2abc4e98bae35030f | 2 | 1 | 3 | 2026-10-13T16:20+09:00 |
| 方針メモ-4 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-13T16:30+09:00 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | b3755bb886fb6769de35bf8eb5195f695c582c74 | 2 | 0 | 2 | 2026-10-13T17:10+09:00 |
| 方針メモ-5 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-10-13T17:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ-1 | low | no | self-inflicted | design | fixed | binding は gh の実行先の repo の root checkout（git の共通ディレクトリから求める）から読む。root の steering が読めない・PR URL を記録していないときは binding で追い越さない。trusted root も新しく検査の対象になる。marker 不在の経路にも同じ照合を入れるか・headRefName を PR URL に代えるかはユーザーに確認し、どちらも推奨どおりに決まった（依頼の原文の 2026-10-13 の回答）。commit: 64b67c8f |
| H1 | 独立-1 | high | yes | self-inflicted | binding-reach | accepted | 列挙: gh の実行先の git repo を決められない merge（cwd が git の外、`cd "$X"`）は binding を引かず台帳だけで決まるのに、「どこから打っても同じ判定」と宣言していた。方針メモ-2 で (b)。宣言は範囲つきに直した。commit: f8a18c32 |
| H2 | 独立-1 | high | yes | self-inflicted | gh-repo-choice | fixed | 番号だけの merge で gh の既定 repo を origin と決めていた。upstream remote がある clone では origin#N の証跡で通りうる。remote が origin だけか origin が set-default のときだけ引く。commit: f8a18c32 |
| H3 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 前段の python が binding.json・state.md を通常ファイルか確かめずに読み、FIFO で hook が timeout する。regular_file.read_regular_text で読む。commit: f8a18c32 |
| M1 | 独立-1 | medium | no | self-inflicted | binding-reach | fixed | registry は root checkout と各 worktree に分かれるのに root だけを読んでいた。worktree list の全 registry を読み、state.md の実パスで重複を除く。commit: f8a18c32 |
| M2 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼が求めた変異注入の記録が無い。PR 本文に書く。commit: なし（PR 本文） |
| L1 | 独立-1 | low | no | self-inflicted | test-power | fixed | 読めない steering・remote の条件・GH_REPO・URL での allow・別 PR を記録した root などの条件をテストが通らない。テストを足した。commit: f8a18c32 |
| L2 | 独立-1 | low | no | self-inflicted | binding-reach | fixed | 別の repo のセッションから binding のある repo へ cd した番号だけの merge が、切り替え後に AC-18 で止まる。切り替えた後は AC-18 のループを飛ばす。commit: f8a18c32 |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 自セッションの marker の root で別 PR を記録しているときに緩む変化が、断片と PR 本文に無い。書いた。commit: f8a18c32 |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「cd しても同じ照合で止まる」と書く 5 か所が binding の切り替えと食い違う。binding が指さないときの条件を足した。commit: f8a18c32 |
| L5 | 独立-1 | low | no | self-inflicted | binding-reach | fixed | 同じ steering を指す binding が 2 つあると steering-ambiguous で止まり、案内どおりにしても抜けられない。state.md の実パスで重複を除き、2 件以上の文に binding を案内した。commit: f8a18c32 |
| L6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 新しい発火条件の件数とコマンドが目的の節に無い。PR 本文に書く。commit: なし（PR 本文） |
| A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | advisory: テンプレート外の記述あり（PR 本文の抜粋の、手段を置き換えた経緯の文）。次の巡の前に抜粋から除いた。commit: なし（PR 本文） |
| A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | binding で切り替えた後の block 文が、読んだ steering の場所を出さない。PR 本文に列挙する |
| A3 | 独立-1 | advisory | no | inherited | gh-repo-choice | accepted | main の (c) は origin の gh-resolved しか読まない（既知の 旧#136）。PR 本文に列挙する |
| A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | lib の冒頭の依存の列挙と $1 の説明が実体と合わない。lib を書き直したときに直した。commit: f8a18c32 |
| pm2-1 | 方針メモ-2 | low | no | self-inflicted | binding-reach | accepted | H1 は (b)。形は transcript の gh pr merge 1,743 本中 293 本（cwd が git の外）・21 本（cd 先が決められない）で現れるが、許可リストで閉じると正当な merge を 293 本止め、binding では起点の repo が無く閉じられない。binding が記録した PR を対象にしたものは 0 本（母数は約 15 PR）。reviewer の配線案 (i)(ii) は主な形（cd なしの -R）を閉じず合流の道を増やすので入れない |
| r2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: binding で GDD worktree へ切り替えた後、steering の解決（scripts/gdd_task_binding.py の load_bindings）が切り替え先の registry の binding.json を種類を確かめずに開き、FIFO で hook が timeout して merge が通る。方針メモ-3 で A'。load_bindings を read_regular_text で読み、切り替え後の marker の読み（run-merge-gate-hook.sh）も通常のファイルに限った。commit: 66ccdc3a |
| r2-2 | 独立-2 | medium | no | self-inflicted | test-power | fixed | FIFO のテストが切り替えた後の経路を通らない。marker の無い実行先からの再現テストを足した。commit: 494836d6 |
| r2-3 | 独立-2 | medium | no | self-inflicted | request-scope | accepted | 番号だけの merge で origin 以外の remote がある repo は binding を引かない絞りを、ユーザーの確認なしに限界にした。方針メモ-3 でユーザーが限界として受け入れた（GDD を使う 6 repo はすべて origin だけ）。request.md に回答を足した |
| r2-4 | 独立-2 | medium | no | self-inflicted | test-power | fixed | 別の PR を記録した root のテストが切り替えの有無を見分けない。証跡が揃えば通ることを足した。commit: 494836d6 |
| r2-5 | 独立-2 | medium | no | self-inflicted | product | next-pr | binding が 2 件以上のときの block 文がアクションから始まらず、ユーザーへの確認の語も無い。本体の _mg_action と文面が 2 つに分かれた |
| r2-6 | 独立-2 | medium | no | self-inflicted | binding-reach | next-pr | 対象を repo つきで明示した merge で、binding を引く repo が呼び出し側（実行先と PROJECT_ROOT）で違う |
| r2-7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 断片の「実行先の git repo を決められるときは同じ判定」と lib のコメントの「実行先と同じ repo」が実装より広い |
| r2-8 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | テストの docstring が「root checkout の binding」のまま |
| r2-9 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | repo-root-unresolvable の新しい案内が、binding を引かなかった場面でも出る |
| r2-10 | 独立-2 | low | no | self-inflicted | binding-reach | next-pr | 重複除きが bash 側の検査より先にあり、古い worktree_path の binding が正しい binding を隠しうる |
| r2-11 | 独立-2 | low | no | self-inflicted | test-power | fixed | GH_REPO の subTest が lookup の戻りを固定していない。untrusted-root-unverified で止まることを assert した。commit: 494836d6 |
| r2-12 | 独立-2 | low | no | self-inflicted | product | next-pr | 切り替えた後の出口で、台帳の照合が hit だけで止める形に戻った（main の marker 不在の経路と同じ判定） |
| r2-13 | 独立-2 | low | no | self-inflicted | style | fixed | テストの節の見出しが工程の名前になっている。挙動の名前にした。commit: 494836d6 |
| r2-14 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | commit の件名に巡の ID がある（履歴を書き換えないと直せない）。以後の件名は内容だけにする。PR 本文に列挙する |
| r2-15 | 独立-2 | advisory | no | self-inflicted | request-scope | fixed | 依頼の変異注入の結果が見えない。PR 本文の検証の節に書く。commit: なし（PR 本文） |
| pm3-1 | 方針メモ-3 | low | no | self-inflicted | fail-open | fixed | 安全策 4 の発火（fail-open の high が独立-1・独立-2 の 2 巡）。Opus は A'（load_bindings と :934 の 2 か所。読み手を数え切った）、Fable は A' で 旧#4・旧#11・旧#13 は next-pr、ユーザーは A'（旧#4・旧#11・旧#13 も入れる）と 旧#3 は限界を選んだ。commit: 66ccdc3a |
| r3-1 | 独立-3 | medium | no | self-inflicted | test-power | fixed | UTF-8 でない binding のテストが、except を差分前に戻しても通る（依頼の変異注入）。load_bindings が正しい binding を返すことを assert し、コメントを効く経路に直した。except を戻す変異で落ちることを確かめた。commit: 08c79c36 |
| r3-2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 別の PR を記録した root のテストに足した 3 行が、root に steering を作らないテストにも重複して入り、コメントが事実と違う |
| r3-3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 断片に、UTF-8 でない binding.json をその 1 件だけ飛ばす変化（今までは解決全体が失敗し done guard が warn に下がった）が無い |
| r3-4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文が load_bindings の使い手を pre-push・pre-PR・merge gate と書き切り、done guard を落としている。「消えたファイル」は今までも飛ばしていた。commit: なし（PR 本文） |
| r3-5 | 独立-3 | advisory | no | self-inflicted | product | accepted | load_bindings は (OSError, ValueError) だけを受け、lookup は Exception を受ける。入れ子の深い binding.json の RecursionError は敵対的な形。PR 本文に列挙する |
| r3-6 | 独立-3 | advisory | no | self-inflicted | style | accepted | テストの節の見出しに当たらないテストが 2 件ある。PR 本文に列挙する |
| r4-1 | 独立-4 | high | yes | self-inflicted | approval-path | fixed | `cd /R & gh pr merge 7` と、cd とパイプでつないだ `gh pr merge 7` で cd 先 R の binding の証跡で通し、gh は元の cwd の repo の 旧#7 を merge しうる。方針メモ-4 で B′。cd 先は元の cwd と同じ repo か明示の merge のときだけ binding の起点にする。commit: b8fcf2d0 |
| r4-2 | 独立-4 | high | yes | self-inflicted | approval-path | fixed | root の steering に対象 PR が無いときの切り替えが、gh の実行先ではなく root の repo の binding を引く。gh の実行先から引く（決められないときは root）。commit: b8fcf2d0 |
| r4-3 | 独立-4 | medium | yes | self-inflicted | request-scope | accepted | 対象 PR を省いた merge・対象を決められない merge・GH_REPO/GH_HOST の merge を binding から外したことを、ユーザーに確認していなかった。方針メモ-4 でユーザーが限界として受け入れた（番号も URL も無い merge 11/1,390、GH_REPO 0）。差分の前と同じ判定 |
| r4-4 | 独立-4 | medium | no | self-inflicted | doc-claim | next-pr | cwd が git の外のとき binding を引かないのに、repo-root-unresolvable の案内が binding で判定すると言い、限界の書き方も実際と合わない |
| r4-5 | 独立-4 | low | no | self-inflicted | request-scope | fixed | 変異注入の結果が断片と PR 本文の抜粋に無い。PR 本文の検証の節に書いた。commit: なし（PR 本文） |
| r4-6 | 独立-4 | low | no | self-inflicted | test-power | next-pr | URL の長さ・UNRESOLVABLE・相対の worktree_path・改行を含む state_path・payload の cwd の分岐の変異が生き残る |
| r4-7 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | root で起動したセッションのテストのコメントが誤っていて、assert が重複している |
| r4-8 | 独立-4 | low | no | self-inflicted | product | next-pr | chmod(0) のテストに、root で走らせるときの skip が無い |
| r4-9 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 断片に UTF-8 の扱い・binding の重複で止まるときの出口が無く、「同じ判定になる」が広い |
| r4-10 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | SECURITY.md の限界の段落に binding を引かない形の一部が無く、括弧書きが古い |
| r4-11 | 独立-4 | low | no | self-inflicted | product | next-pr | 切り替えた後も古い root で求めた値で判定が進み、止める理由の文が実際と合わないことがある（止める側） |
| r4-12 | 独立-4 | low | no | self-inflicted | product | next-pr | lookup の python の print が try の外にあり、孤立したサロゲートで列挙が途中で切れる（手で書き換えた binding だけ） |
| r4-13 | 独立-4 | low | no | self-inflicted | bookkeeping | next-pr | 新しい発火条件の実測にコマンドが無く、binding の重複の件数を測っていない |
| r4-14 | 独立-4 | advisory | no | self-inflicted | product | accepted | merge 1 回あたりの所要時間を測っていない。PR 本文に列挙する |
| r4-15 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | `-R HOST/OWNER/REPO` の形が限界に無く、URL の照合で host を比べていない。PR 本文に列挙する |
| pm4-1 | 方針メモ-4 | low | no | self-inflicted | approval-path | fixed | 安全策 4 の 2 回目の発火（high・blocking を含む巡が合計 3 回）。main は parser の signal 案、Opus は B′（hook の既存の前提と同じく、cd 先を同じ repo か明示の merge のときだけ信じる）を推し、main も B′ に合わせた。ユーザーは B′ と、F3 を限界として受け入れることを選んだ。commit: b8fcf2d0 |
| r5-1 | 独立-5 | high | yes | self-inflicted | binding-reach | accepted | 列挙: marker のある root から別の clone へ cd して -R で明示した merge は、cd 先の repo の binding だけを引き、台帳 miss なら通る（main と同じ判定）。方針メモ-5 で (b)。入力者: 明示の cd merge 83 本中、該当は実質 0 本。限界の節の先頭に書いた |
| r5-2 | 独立-5 | high | yes | inherited | fail-open | accepted | `cd B & gh pr merge 7`（番号だけ、B は別 repo）は台帳を cd 先の組で照合し、元の cwd の repo の GDD の PR に当たらず通る（差分の前から）。入力者 0/1,390。限界の節の先頭に書いた |
| r5-3 | 独立-5 | medium | no | self-inflicted | test-power | next-pr | payload cwd（Codex の workdir）の分岐を通るテストが無く、`_i` を常に 0 にする変異が生き残る |
| r5-4 | 独立-5 | low | no | self-inflicted | doc-claim | next-pr | marker のある root で明示の merge は実行先を決められなくても root の binding で判定するのに、限界・断片・SECURITY.md は引かないと書く（止める側） |
| r5-5 | 独立-5 | low | no | self-inflicted | doc-claim | next-pr | gdd_mg_binding_switch の $1 のコメントが、呼び出し元ごとの渡し方と合わない |
| r5-6 | 独立-5 | low | no | self-inflicted | doc-claim | next-pr | SECURITY.md に、番号だけの merge で cd 先が別 repo なら binding を引かない条件が無い |
| pm5-1 | 方針メモ-5 | low | no | self-inflicted | binding-reach | accepted | 安全策 4 の 3 回目の発火と、無効化後の差分巡の上限。Opus は止める（入力者 0、main と同じ判定、直すたびに鏡像が出る）を推し、main も実測を見て合わせた。Fable は 1 PR 1 回の枠を使い切っていて呼んでいない。ユーザーは「止めてマージする」を選んだ |
