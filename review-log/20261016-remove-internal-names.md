---
lane: L1
pr: 565
amends: 20260911-x36-parallel-regression-tests.md, 20260914-review-log.md, 20260915-agent-dispatch-model-gate.md, 20260918-merge-gate-non-gdd-merge.md, 20260919-testing-standard-class-e-pin.md, 20260919-testing-standard.md, 20261012-request-to-pr-review.md, 20260929-agent-tool-allowlist.md, 20260913-planning-design-wiring-checks.md, 20260920-typed-dispatch-templates.md, 20261005-wait-until-script.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0a9070d3 | 1 | 3 | 0 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8a02721c | 0 | 0 | 0 | 2026-10-16 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 72683423 | 0 | 0 | 0 | 2026-10-16 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 831cb0fc | 0 | 0 | 0 | 2026-10-16 |
| 独立-5 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 246c4af2 | 0 | 0 | 0 | 2026-10-31 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 4fcf0ef0 | 0 | 2 | 0 | 2026-10-31 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | no | self-inflicted | intent | fixed | 列挙: 依頼が名指しした社内 wiki のサービス名が GDD に残る（gdd-dev.md の社内 wiki・チケット管理の例、記事番号、出力先の例）。GDD の中のその名前を全部書き直した。commit: 8a02721c |
| I1-2 | 独立-1 | medium | no | self-inflicted | intent | fixed | 依頼が指定した語の拾い方の結果が PR 本文に無い。PR 本文に拾った語の出どころと件数を書く。commit: なし（PR 本文） |
| I1-3 | 独立-1 | medium | no | self-inflicted | intent | fixed | 公開の単位（GDD だけ）が依頼に無い。GDD だけを切り出すと決めたユーザーの発言を request.md に足した。commit: 8a02721c |
| I1-4 | 独立-1 | medium | no | self-inflicted | intent | fixed | チームメイトの名前を commit 作者でしか確かめていない。ユーザーからもらった名前 6 つを漢字とローマ字で探し、切り出す範囲で 0 件だった。commit: なし（PR 本文） |
| I1-5 | 独立-1 | low | no | self-inflicted | intent | fixed | author.email の変更が依頼に無い。noreply を指示したユーザーの発言を request.md に足した。commit: 8a02721c |
| I1-6 | 独立-1 | low | no | self-inflicted | docs | accepted | root の marketplace.json の owner.email が gmail のまま（切り出す範囲の外。PR 本文の限界に書く） |
| I1-7 | 独立-1 | low | no | self-inflicted | docs | accepted | backlog を外部チケットの例として残す箇所と、消した箇所が割れる（PR 本文の限界に書く） |
| I1-8 | 独立-1 | low | no | self-inflicted | docs | accepted | 別の repo の PR 番号 旧#1328 がテストのコメントに残る（PR 本文の限界に書く） |
| I1-9 | 独立-1 | low | no | self-inflicted | docs | accepted | CHANGELOG § Policy の「既存エントリは書き換えない」とリリース済みの節の書き直しが食い違う（PR 本文の限界に書く） |
| I1-10 | 独立-1 | low | no | self-inflicted | docs | fixed | PR 本文の「コメントだけ」と fixture のバケット名の記述が差分と合わない。commit: なし（PR 本文） |
| I1-11 | 独立-1 | low | no | self-inflicted | docs | accepted | 変更断片の Summary が差分と合わない（PR 本文の限界に書く） |
| I1-12 | 独立-1 | advisory | no | self-inflicted | intent | accepted | 社内の plugin・skill の名前 3 つが社内のものか決められない（PR 本文に列挙） |
| I1-13 | 独立-1 | advisory | no | self-inflicted | docs | accepted | gdd-pr-review の 3b の手順リンクの例が分類名になった（PR 本文に列挙） |
| I1-14 | 独立-1 | advisory | no | self-inflicted | docs | accepted | noreply の数値 ID を確かめた記録が無い（PR 本文に列挙） |
| I1-15 | 独立-1 | advisory | no | self-inflicted | docs | accepted | 残した旧 repo の URL は private の repo を指す（PR 本文に列挙） |
| I1-16 | 独立-1 | advisory | no | self-inflicted | intent | accepted | 以後の取り込みで社内語が戻るのを止める仕組みが無い（PR 本文に列挙） |
| I2-1 | 独立-2 | low | no | self-inflicted | docs | accepted | archive を書き換えたのに、r9-2 の anchors manifest 3 本の source_sha256 が古い archive の値のまま（CI の外の verify が落ちる。PR 本文の限界に書く） |
| I2-2 | 独立-2 | low | no | self-inflicted | docs | accepted | 変更断片の「lint-requirements-duplication.py（コメントだけ）」は、--help に出る docstring も変えている（PR 本文の限界に書く） |
| I2-3 | 独立-2 | advisory | no | inherited | intent | accepted | 社内の skill の名前が社内のものか決められない（PR 本文に列挙） |
| I2-4 | 独立-2 | advisory | no | inherited | intent | accepted | root の README.md に社内 wiki のサービス名が残る。切り出す範囲に入れるかで決まる（PR 本文に列挙） |
| I2-5 | 独立-2 | advisory | no | self-inflicted | docs | accepted | 変更断片の「テスト 14 本」を確かめていない（PR 本文に列挙） |
| I2-6 | 独立-2 | advisory | no | self-inflicted | docs | fixed | PR 本文の限界の節の項目に種類が無い。commit: なし（PR 本文） |
| I3-1 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の抜粋に、テンプレート外の advisory の節がある（次の巡の抜粋から除く）。commit: なし（PR 本文） |
| I3-2 | 独立-3 | low | no | self-inflicted | docs | fixed | 書き換えたリリース済みの CHANGELOG の行数が PR 本文の限界と合わない。commit: なし（PR 本文） |
| I3-3 | 独立-3 | low | no | self-inflicted | docs | fixed | smoke の行の形の assert を緩めたことが PR 本文に無い。commit: なし（PR 本文） |
| I3-4 | 独立-3 | low | no | self-inflicted | product | accepted | smoke を引数なしで起動すると、場所が空のまま MISSING で終わる（PR 本文の限界に書く） |
| I3-5 | 独立-3 | low | no | self-inflicted | test-power | accepted | SNYK_PLUGIN_ROOT を設定してもパスが誤っていると SKIP になる（PR 本文の限界に書く） |
| I3-6 | 独立-3 | low | no | self-inflicted | test-power | accepted | tests/checks の場所の受け取り方を固定するテストが無い（PR 本文の限界に書く） |
| I3-7 | 独立-3 | low | no | self-inflicted | intent | accepted | 社内 plugin の中の hook の file 名が smoke に残る。ユーザーが推奨の「残す」を選んだ（2026-10-31） |
| I3-8 | 独立-3 | low | no | inherited | intent | fixed | 同じ社内 skill を「CVE 検索機能」と書く箇所が 5 つ残る。「CVE 一覧の投稿」に揃えた。commit: fd39ba16 |
| I3-9 | 独立-3 | low | no | self-inflicted | intent | accepted | root の README.md と過去の review-log を持っていかないことに、ユーザーの発言が無かった。ユーザーが推奨を選んだ（2026-10-31）。推奨（Opus・Fable とも）の「root README と .request.md は持っていかず、review-log の本体は社内語を書き直して持っていく」で進め、ユーザーに確かめる |
| I3-10 | 独立-3 | low | no | self-inflicted | style | accepted | faq.md・self-contained-contract.md で英字と日本語の間の空白が抜け、verifier が重複する（PR 本文の限界に書く） |
| I3-11 | 独立-3 | low | no | inherited | docs | accepted | 同じエントリと同じファイルで「snyk plugin」「Snyk plugin」の呼び方が残る（PR 本文の限界に書く） |
| I3-12 | 独立-3 | advisory | no | self-inflicted | product | accepted | block メッセージの <plugin 名> から設定するファイルを一意に決められない（PR 本文に列挙） |
| I3-13 | 独立-3 | advisory | no | self-inflicted | docs | accepted | CONTRIBUTING の check 一覧に、smoke を回すには SNYK_PLUGIN_ROOT が要ると書いていない（PR 本文に列挙） |
| I3-14 | 独立-3 | advisory | no | self-inflicted | docs | accepted | PR 本文の「69 語で 0 件」を材料から再現できない（PR 本文に列挙） |
| I3-15 | 独立-3 | advisory | no | self-inflicted | docs | accepted | 断片の「テスト 16 本」が確かめられず、User Action Required が「なし」のまま（PR 本文に列挙） |
| I3-16 | 独立-3 | advisory | no | self-inflicted | docs | accepted | archive-2 の書き直しで「sibling の」が消え、同じ版の別の行と合わない（PR 本文に列挙） |
| I4-1 | 独立-4 | low | no | self-inflicted | intent | re-reported | 社内 plugin の中の hook の file 名が smoke に残る（I3-7 の再掲。確認待ち） |
| I4-2 | 独立-4 | low | no | self-inflicted | intent | fixed | Backlog を確認なしに公開の SaaS 名として残した。外部チケットの例を、特定のサービス名を使わない形にした。commit: 5f04884d |
| I4-3 | 独立-4 | low | no | self-inflicted | docs | fixed | PR 本文の目的と限界で、過去の review-log を持っていくかが食い違う。commit: なし（PR 本文） |
| I4-4 | 独立-4 | low | no | self-inflicted | docs | accepted | SNYK_PLUGIN_ROOT を export した環境では validate-plugin.sh が smoke を走らせ、今の writer では落ちる（PR 本文の限界に書く） |
| I4-5 | 独立-4 | low | no | self-inflicted | test-power | re-reported | smoke を環境変数で走らせる経路のテストが無い（I3-6 の再掲） |
| I4-6 | 独立-4 | low | no | self-inflicted | style | re-reported | smoke を引数なしで起動すると場所が空のまま終わる（I3-4 の再掲） |
| I4-7 | 独立-4 | low | no | inherited | product | accepted | smoke の usage の heredoc のバッククォートがコマンド置換になる（PR 本文の限界に書く） |
| I4-8 | 独立-4 | low | no | inherited | test-power | accepted | DEPLOY.replace の置き換え元が無いときテストが黙って通る（PR 本文の限界に書く） |
| I4-9 | 独立-4 | low | no | self-inflicted | docs | accepted | 変更断片の Affected Files が差分と 3 点合わない（PR 本文の限界に書く） |
| I4-10 | 独立-4 | advisory | no | self-inflicted | docs | accepted | CHANGELOG § Policy の「既存エントリは書き換えない」とリリース済みの節の書き直し（PR 本文に列挙） |
| I4-11 | 独立-4 | advisory | no | self-inflicted | product | accepted | 社内 wiki の名前の多くは語を 1 対 1 で替えた形（PR 本文に列挙） |
| I4-12 | 独立-4 | advisory | no | self-inflicted | docs | accepted | S-1a の説明を消したので同じファイルの「S-1a」が何を指すか読めない（PR 本文に列挙） |
| I4-13 | 独立-4 | advisory | no | self-inflicted | docs | fixed | archive の書き直しで source_sha256 が合わなくなる本数の記述（PR 本文）。commit: なし（PR 本文） |
| I4-14 | 独立-4 | advisory | no | self-inflicted | docs | accepted | テストの入力と docstring にも PR 番号 1328 が残る（PR 本文に列挙） |
| I4-15 | 独立-4 | advisory | no | inherited | docs | accepted | block メッセージの「本 PR 対象外」は利用者にどの PR か分からない（PR 本文に列挙） |
| I4-16 | 独立-4 | advisory | no | self-inflicted | docs | accepted | 語のリストと noreply の数値 ID を材料から確かめられない（PR 本文に列挙） |
| I4-17 | 独立-4 | advisory | no | self-inflicted | style | accepted | 「verifier pluginを」の空白の抜け（PR 本文に列挙） |
| I4-18 | 独立-4 | advisory | no | self-inflicted | product | accepted | 新しい repo の commit の作者を noreply にするかは切り出しの手順で扱う（PR 本文に列挙） |
| I5-1 | 独立-5 | low | no | self-inflicted | intent | fixed | 依頼の「リポジトリ名」に当たる社内の repo・bot の略称 ai-bot が GDD に 17 か所残る。「GDD を使う別の repo」「レビュー bot」に書き直した。commit: 4fcf0ef0 |
| I5-2 | 独立-5 | low | no | self-inflicted | intent | fixed | 社内の repo の略称 infra と、チケット管理サービス名を含むタスクの slug を確認なしに残した。書き直した。commit: 4fcf0ef0 |
| I5-3 | 独立-5 | low | no | self-inflicted | product | re-reported | root の marketplace.json の owner.email が gmail のまま（I1-6 の再掲） |
| I5-4 | 独立-5 | low | no | self-inflicted | doc-claim | re-reported | 変更断片の Affected Files・本数が差分と合わない（I4-9 の再掲） |
| I5-5 | 独立-5 | low | no | self-inflicted | product | re-reported | smoke を引数なしで起動すると場所が空のまま MISSING で終わる（I3-4 の再掲） |
| I5-6 | 独立-5 | low | no | self-inflicted | doc-claim | re-reported | 同じファイルで書き直した ID と残した ID（S-1a・1328・ADR 番号）が混ざる（I4-12・I4-14 の再掲） |
| I5-7 | 独立-5 | low | no | self-inflicted | style | re-reported | 「verifier pluginを」の空白の抜け（I3-10 の再掲） |
| I5-8 | 独立-5 | advisory | no | inherited | product | re-reported | smoke 検査が社内 verifier の hook のファイル名を持つ（I3-7 の再掲。確認待ち） |
| I5-9 | 独立-5 | advisory | no | self-inflicted | product | re-reported | block メッセージの <plugin 名> から設定ファイルを決められない（I3-12 の再掲） |
| I5-10 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文がチームメイトの名前を確かめた結果に触れていない。PR 本文に 1 行書く。commit: なし（PR 本文） |
| I5-11 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋の「main を取り込んだ。」。次の巡の抜粋から除く） |
| I6-1 | 独立-6 | medium | no | self-inflicted | intent | fixed | completion-check の書き直した行に、社内の repo の略称 infra が残る。文を書き直した。判断資料のファイル名の infra は、改名すると参照 3 か所と履歴に波及するので残す（PR 本文の限界に書く）。commit: 760b2271 |
| I6-2 | 独立-6 | medium | no | self-inflicted | product | fixed | 1 つの repo にだけ当てていた CI gate の禁止が、GDD を使う repo 全般に広がって読める。判断資料の Context の repo に限る文にした。commit: 760b2271 |
| I6-3 | 独立-6 | low | no | self-inflicted | intent | fixed | 判断資料の見出しに repo の略称 Infra が残る。見出しを書き直した。commit: 760b2271 |
| I6-4 | 独立-6 | low | no | self-inflicted | doc-claim | re-reported | 変更断片の Affected Files・本数が差分と合わない（I4-9 の再掲） |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「--help に出る docstring は 1 文だけ」が wait-until.py の分を数えていない。agents も書き直し先に無い。commit: なし（PR 本文） |
| I6-6 | 独立-6 | low | no | self-inflicted | style | accepted | 判断資料で「その repo」に置き換えた跡の空白と「同じ その repo の」の崩れ（PR 本文の限界に書く） |
| I6-7 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | 書き直した文に別の repo の番号（旧#1327・ADR-0194・PR 旧#615）が残る（公開前の数値・番号の作業で扱う） |
| I6-8 | 独立-6 | advisory | no | inherited | doc-claim | accepted | テストの架空の repo 名 example-org/infra-repo・acme/infra-gdd に infra が残る（一般語として読める） |
