---
lane: L1
pr: 153
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | user | - | 0 | 0 | 0 | 2026-09-19T21:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus（reviewer が main の transcript を参照したと自己申告。判断は差分とリポジトリだけと明記） | b350f0e0 | 0 | 7 | 2 | 2026-09-19T22:20+09:00 |
| 方針メモ-1 | user | - | 0 | 0 | 0 | 2026-09-19T22:30+09:00 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承（セッションの agent 定義が古いため fallback） | 6dfb3d5c | 0 | 2 | 0 | 2026-09-19T23:10+09:00 |
| 独立-3 | general-purpose, 全差分, model: opus, effort 継承（セッションの agent 定義が古いため fallback） | 09a2efeb | 0 | 3 | 0 | 2026-09-19T23:30+09:00 |
| 独立-4 | general-purpose, 差分, model: opus, effort 継承（セッションの agent 定義が古いため fallback） | 94e07c20 | 0 | 1 | 0 | 2026-09-19T23:36+09:00 |
| 独立-5 | general-purpose, 全差分, model: opus, effort 継承（セッションの agent 定義が古いため fallback） | fd44d21f | 0 | 0 | 0 | 2026-09-19T23:45+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#153 review, Grok 4.6, 全差分, インラインコメント 1 件) | d3d25fa1 | 0 | 1 | 0 | 2026-09-20T00:06+09:00 |
| 独立-6 | light-lane-independent-reviewer, 差分, model: opus | f031968a | 0 | 0 | 0 | 2026-09-20T00:21+09:00 |
| 独立-7 | light-lane-independent-reviewer, 全差分, model: opus | 954826a4 | 0 | 0 | 0 | 2026-09-20T00:39+09:00 |
| 独立-8 | light-lane-independent-reviewer, 差分, model: opus | 3f731e72 | 0 | 0 | 0 | 2026-09-20T00:48+09:00 |
| 独立-9 | light-lane-independent-reviewer, 全差分, model: opus | f999036d | 0 | 0 | 0 | 2026-09-20T01:07+09:00 |
| PR後-2 | yamaguchi-tk (GitHub PR 旧#153 review, Grok 4.6, 差分 d3d25fa1..ee5a8a3d, インラインコメント 1 件) | ee5a8a3d | 0 | 1 | 0 | 2026-09-20T09:46+09:00 |
| 独立-10 | light-lane-independent-reviewer, 差分, model: opus | ae12b091 | 0 | 0 | 0 | 2026-09-20T10:07+09:00 |
| 独立-11 | light-lane-independent-reviewer, 全差分, model: opus | d84d9e3a | 0 | 1 | 0 | 2026-09-20T10:31+09:00 |
| 独立-12 | light-lane-independent-reviewer, 差分, model: opus | 14d3fbd2 | 0 | 0 | 0 | 2026-09-20T10:48+09:00 |
| 独立-13 | light-lane-independent-reviewer, 全差分, model: opus | d4243ffd | 0 | 0 | 0 | 2026-09-20T11:07+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | routing-policy | fixed | 範囲外の常時 High・実害クラスはこの PR で直す例外を残す、① は severity を問わずこの PR で直す（ユーザー決定） |
| A1 | 独立-1 | medium | yes | self-inflicted | re-reported-scope | fixed | 再掲の除外が severity 上昇・実害クラス・this-diff の再報告まで外していた。severity 同等以下・常時 High/実害でない・pre-existing に限定（approval-path、blocking） |
| A2 | 独立-1 | medium | yes | self-inflicted | approval-boundary | fixed | Issue の not planned close を依頼なしに行わせていた（AGENTS.md の承認境界と矛盾）。候補を出して承認後に閉じる形に変更（approval-path、blocking） |
| A3 | 独立-1 | medium | no | self-inflicted | routing-policy | fixed | ② の high が巡の high に数えられ merge-ready を塞ぐ。`next-pr`・`out-of-diff` を足して件数から外す |
| A4 | 独立-1 | medium | no | self-inflicted | routing-policy | fixed | ① を severity を問わず blocking に数えると最終巡が収束せず is_blocking と二重定義になる。blocking は is_blocking のまま、最終巡の繰り返しを 1 回までに |
| A5 | 独立-1 | medium | no | self-inflicted | routing-policy | fixed | 「2 巡目以降を全差分にしない」が最終巡・既存の手順 5/7 と矛盾。中間の巡に限定し、手順 5・7 と Codex の振り分けをそろえた |
| A6 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 実測の「差分巡 0 回」が誤り（旧#124 に 3 巡）。数え直して、再掲の分離と組み合わせる理由を書いた |
| A7 | 独立-1 | medium | no | self-inflicted | routing-policy | fixed | origin: this-diff を振り分けに使わず、差分巡で this PR の欠陥が ③ に落ちる。origin と全差分の変更行で ① にする |
| A8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 契約テストが実装の字面を固定、既存ログの検査が断片を読んだか確かめていない |
| A9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の後方互換の記載に除外 3 本と 旧#140・旧#145 の確認方法が無い |
| A10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `## 巡` の件数の意味が前後で変わることを限界に書いていない |
| A11 | 独立-1 | low | no | self-inflicted | routing-policy | fixed | 古い agent 定義のセッションでは欄が無く全件 ① になる。欄が無ければ fallback で起動し直す |
| A12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 棚卸しと ② の次の PR の順序が未定。棚卸しを先にする |
| A13 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Affected Files に plugin 外の変更が無い |
| A14 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | レビュー後に commit（候補スクリプト）がある。次の巡で見る |
| A15 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 1c の RED-GREEN 証跡が見当たらない（PR 本文に書く） |
| A16 | 独立-1 | advisory | no | self-inflicted | lane | accepted | L1+ にするか。ユーザー指定の L0/L1 のまま |
| M2 | 方針メモ-1 | advisory | no | self-inflicted | routing-policy | fixed | Issue close は候補を出して承認後、① の medium・low は直すが blocking に数えない、規定の矛盾（A3・A5・A6・A7）はこの PR で直す（ユーザー決定） |
| B1 | 独立-2 | medium | no | self-inflicted | routing-policy | fixed | 安全策 4 の「止める」が消えた「0 まで直す」を参照し、① の medium・low を上書きの対象に入れていない（影響先） |
| B2 | 独立-2 | medium | no | self-inflicted | approval-boundary | fixed | Issue にした行の `対応` の値が無く、AGENTS.md の「deferred の Issue の作成」と語がずれる。close の根拠の書き方（影響先） |
| B3 | 独立-2 | low | no | self-inflicted | routing-policy | fixed | 「欄が欠けた finding は ①」の主語が無く、Codex の medium を ① と読める |
| B4 | 独立-2 | low | no | self-inflicted | candidates-script | fixed | 引用符つきのパスで前のファイルの状態を引き継ぐ、コロンを含むパスで ValueError |
| B5 | 独立-2 | low | no | self-inflicted | candidates-script | fixed | main・run・references など一致が千件単位の名前で先頭 30 件が docs に埋まる。100 件超は件数だけ |
| B6 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 旧#140・旧#145 の確認にコマンドと出力が無い（PR 本文に添える） |
| B7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 候補のスクリプトの限界が changelog 断片に無い（配布物の外。PR 本文にある） |
| C1 | 独立-3 | medium | no | self-inflicted | candidates-script | fixed | 本文に U+2028 などがあると splitlines で NUL の無い断片ができ IndexError（今の repo で再現） |
| C2 | 独立-3 | medium | no | self-inflicted | re-reported-scope | fixed | 検査が 実害=yes の行も 3 つの値で件数から外せる。CLAUDE.md の規定（実害クラスは再掲・②③ にしない）と合わせて fail にする |
| C3 | 独立-3 | medium | no | self-inflicted | routing-policy | fixed | this-diff を next-pr にした指摘（Codex 分・最終巡の打ち切り分）が再度出ると再掲にできず ① に戻り、打ち切りが効かない |
| C4 | 独立-3 | low | no | self-inflicted | test-power | fixed | 既存ログの後方互換テストが名前の除外リストで、L0 の review-log が足されると無関係に落ちる。lane で絞る |
| D1 | 独立-4 | medium | no | self-inflicted | candidates-script | fixed | text=True の universal newlines で単独の \r がレコードを割り ValueError。bytes で受けて \n だけで分ける |
| D2 | 独立-4 | low | no | self-inflicted | test-power | fixed | 改行文字のテストが \x0c だけで U+2028・\r を入力にしていない。subTest に広げた |
| D3 | 独立-4 | advisory | no | self-inflicted | test-power | accepted | 後方互換テストの LANE_RE が front matter の外まで探し、CRLF の L1 を黙って外す（今の 20 本は LF で実害なし） |
| E1 | 独立-5 | low | no | self-inflicted | candidates-script | next-pr | 改行を含むファイル名で git grep のレコードが割れ IndexError（fail-loud）。最終巡の繰り返し 1 回までの規定で次の PR |
| E2 | 独立-5 | advisory | no | self-inflicted | test-power | accepted | 後方互換テストの LANE_RE が front matter の外まで読みうる（D3 と同じ。今の checkout では起きない） |
| F1 | PR後-1 | medium | no | self-inflicted | test-power | fixed | 契約テストの正規表現が UNCOUNTED_TAIOU_VALUES の末尾に当たり、3 値の包含だけを見て集合の一致を見ていない（値を足しても緑）。名前ごとピンして一致を assert、受理集合への union も別 assert（ユーザー指示でこの PR で直した。3ab7b461）|
| G1 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 契約テストの module docstring が片方向（受理）のまま。一致の契約に直した（8d372acf） |
| G2 | 独立-6 | low | no | self-inflicted | test-power | fixed | UNCOUNTED_TAIOU_VALUES への追加代入や再代入で後から値を足すと一致の assert をすり抜ける。代入が 1 か所であることを assert（8d372acf） |
| G3 | 独立-6 | low | no | self-inflicted | test-power | fixed | review-log/README.md の 6 値を照合するテストが無い。差分巡では review-log/ が除外され、README:12 は全差分の変更行なので ① にした（8d372acf） |
| G4 | 独立-6 | advisory | no | self-inflicted | test-power | accepted | 受理集合の assert が `UNCOUNTED_TAIOU_VALUES` という書き方を固定する（列挙へのリファクタでも落ちる）。振る舞いは test_review_log_present.py が固定するので現状維持 |
| H1 | 独立-7 | low | no | self-inflicted | doc-claim | fixed | scripts/.gitignore が変更断片の Affected Files と PR 本文に無い。断片に足し、PR 本文にも書く（98ac203b） |
| H2 | 独立-7 | low | no | self-inflicted | doc-claim | fixed | 安全策 4 が「手順 6 のとおり blocking の列に入らない」と書くが、手順 6 は next-pr・out-of-diff の blocking を述べていない。high に入らない、実害クラスにできないので blocking にも入らない、と書き直した（98ac203b） |
| H3 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | Codex の medium 以下は全部 next-pr、独立レビューの advisory は PR 本文に列挙するだけ、で扱いが違う。Codex の指摘に差分との関係の欄が無いための割り切りで、全レーン共通の既定とは矛盾しない |
| H4 | 独立-7 | advisory | no | self-inflicted | candidates-script | accepted | git の diff.noprefix や mnemonicPrefix の環境で FILE_RE が一致せず、Markdown の差分からも名前を抜き出す。倒れる向きは余計に列挙する側で実害なし |
| H5 | 独立-7 | advisory | no | self-inflicted | candidates-script | accepted | 候補の一覧がテストの足場の名前（setUp・_read・SCRIPT など）で埋まり、変えた部品が埋もれる。上限は効いている。PR 本文の限界に書く |
| I1 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 最終巡の打ち切り（① の medium・low だけなら next-pr）が実害クラスを除いておらず、実害=yes の next-pr を落とす検査と衝突する。実害クラスは next-pr にできずこの PR で直す、と書き足した（60687fae） |
| J1 | 独立-9 | low | no | self-inflicted | test-power | next-pr | 差分との関係が review-log の列に無く、変更箇所と宣言された指摘を next-pr にしても検査は通る（実害=no）。列を足すと 8 列が 9 列になり既存 review-log 全本に波及するので、最終巡の繰り返し 1 回までの規定で次の PR |
| J2 | 独立-9 | low | no | self-inflicted | test-power | next-pr | 後方互換テストが review-log の実ファイルを 1 本ずつ直列に回し、PRE_EXISTING_INVALID がファイル名だけの除外になる。subTest では分散されず、検査を締めるたびに除外が増える。最終巡の繰り返し 1 回までの規定で次の PR |
| J3 | 独立-9 | advisory | no | self-inflicted | product | accepted | 実害=yes の番兵は、実害の列が自己申告なので実害=no と書けば素通りする。PR 本文の限界と変更断片の Known Limitations が開示済み |
| J4 | 独立-9 | advisory | no | self-inflicted | doc-claim | accepted | 手順 5 の medium 以下は次の PR に回す、が実害クラスを除いていないと読める。手順 6 は実害クラスを直すと定め、検査も実害=yes の next-pr を落とすので実害は出ない。PR 本文に列挙する |
| J5 | 独立-9 | advisory | no | self-inflicted | candidates-script | accepted | 候補の一覧の信号密度が低く、この PR の一覧で起点になるのは 10 件ほど。H5 と同じ。PR 本文の限界が開示済み |
| K1 | PR後-2 | medium | no | self-inflicted | test-power | fixed | 契約テストの正規表現が UNCOUNTED_TAIOU_VALUES の集合リテラルの直後までしか見ず、同じ行で集合の外に値を足す形（集合の和の演算子・.union()・frozenset との和）は緑のまま（F1 の修正の穴。修正前に 3 形と TAIOU_VALUES の受理側への追加が緑なのを確認）。右辺を行末まで集合リテラル 1 個に固定し、対になる TAIOU_VALUES の右辺も全体一致にした（この PR で直した。0143e522） |
| L1 | 独立-10 | low | no | self-inflicted | test-power | fixed | 契約テストで TAIOU_VALUES だけ代入は 1 か所の assert が無く、後の行で集合の和の代入演算子を使って足す形が緑のまま（K1 の修正の対の片方。修正前に緑なのを変異で確認）。UNCOUNTED_TAIOU_VALUES と同じ assert を足し、changelog の変異注入の記述も合わせた（この PR で直した。7d2228d3）|
| L2 | 独立-10 | advisory | no | self-inflicted | test-power | accepted | ソース文字列をピンする方式は、変異の形ごとに穴が再発する（`;` で続ける形・整形の違いで落ちる形）。埋め込みの Python を ast で読むか、検査側に語彙を出す口を持つ案は次の PR 以降。実害は無く、`review-log-present.sh` の値域検査と件数の照合は別のテストが振る舞いで固定している |
| N1 | 独立-11 | medium | no | self-inflicted | product | accepted | ① の medium・low だけが出続ける中間の差分巡に回数の上限が無く、安全策 4 も発火しない（上限があるのは最終の全差分巡の繰り返しだけ）。ユーザーの方針メモで確定した手順は変えず、PR 本文の限界の節に開示した。回数の上限は次の PR で検討する |
| N2 | 独立-11 | low | no | self-inflicted | test-power | accepted | 再掲の 3 つの前提のうち、検査が機械化したのは 実害=yes の拒否だけ。severity が同じか低いことと origin は、再掲元の行を指す欄が無く検査できない。J3 と同じ自己申告の限界で、PR 本文の限界の節に前提の未検査分を明記した |
| N3 | 独立-11 | low | no | self-inflicted | doc-claim | fixed | ① の「severity を問わず」が、直後の「advisory は直さない」と食い違う。「advisory を除いて」を足した（3d1e3e3a） |
| N4 | 独立-11 | low | no | self-inflicted | doc-claim | fixed | 全レーン共通の「全差分巡をやり直す」が、手順 6 の 2 段階の終了条件と揃っていない。「終了条件に戻る」に直した（3d1e3e3a） |
| N5 | 独立-11 | low | no | self-inflicted | test-power | fixed | 契約テストの集合一致が、単引用符の値や `*名前` の展開を数え損ねて緑のまま（K1・L1 と同じ、形ごとに穴が残る型）。抜き出した集合を ast.literal_eval で評価して比較した（3d1e3e3a。修正前に緑なのを変異で確認） |
| N6 | 独立-11 | low | no | self-inflicted | doc-claim | fixed | PR 本文が 100 件の閾値だけを書き、一覧が 30 件までで切られることを書いていない。PR 本文の変更内容 6 を直した（PR 本文の更新） |
| N7 | 独立-11 | low | no | self-inflicted | product | fixed | 候補スクリプトが、改行を含む追跡パスで IndexError を出し、一覧全体が出なくなる（E1 の再報告。E1 は next-pr）。直す費用が小さいので、この PR で git grep -z の出力をレコード構造で読むようにした（3d1e3e3a。再現テストを先に追加）。E1 は次の PR から外す |
| N8 | 独立-11 | low | no | self-inflicted | test-power | re-reported | 後方互換テストの直列実行とファイル名だけの除外（J2 の再報告。J2 は next-pr） |
| N9 | 独立-11 | advisory | no | self-inflicted | bookkeeping | accepted | 1c の証跡は PR 本文の別の節にある（A15 で対応済み）。reviewer に渡した 3 節の外にあるため未確認と報告された。PR 本文を確認済み |
| N10 | 独立-11 | advisory | no | self-inflicted | style | accepted | `__pycache__/` の無視が scripts/.gitignore で 2 か所目になる。root の .gitignore に足す案は、配布物の外を触らない方針との兼ね合いで次の PR 以降 |
| O1 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | 全レーン共通の ① の記述が、手順 6 ① の「advisory を除く」を欠いていて、同じ finding で読む場所により逆の結論になる（N3 の修正の対の片方）。全レーン共通と PR 本文の変更内容 1 に足した（afc37663） |
| O2 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | 手順 5 だけが「最終の全差分巡をやり直す」の旧文言で、手順 6・7 の 2 段階の終了条件と揃っていない（N4 の修正の対の片方）。手順 6 の終了条件に戻る、に揃えた（afc37663） |
| O3 | 独立-12 | low | no | self-inflicted | test-power | fixed | 改行を含むパスのテストが `ird.py:1` の部分一致で、パスを切り詰める実装でも緑のまま。パス全体を assert した（afc37663） |
| O4 | 独立-12 | low | no | self-inflicted | product | fixed | git grep に --no-color が無く、color.grep=always の構成で行番号に色の制御文字が混ざり int() が ValueError で一覧ごと落ちる。再現テストを先に追加し、--no-color を渡した（afc37663）。1 レコードずつ捨てる案は入れない（git の出力の構造は保証されるので、崩れたら止まる方がよい） |
| O5 | 独立-12 | advisory | no | self-inflicted | product | accepted | 改行を含むパスは、候補の一覧の 1 項目が 2 行に割れる。表示の見づらさだけで、パスは作者の管理下。PR 本文の変更内容 6 に開示済み |
| P1 | 独立-13 | medium | no | self-inflicted | doc-claim | next-pr | 手順 6 の「出力のどの finding にも `差分との関係` が無いとき」は、finding が 0 件の巡でも真になり、merge-ready の巡を毎回 general-purpose で起動し直す読み方ができる。「finding が 1 件以上あり、そのどれにも無いとき」に限る直しが要る。最終の全差分巡の 2 回目なので、手順 6 の打ち切りで next-pr（実害クラスではない。0 件の巡で起動し直すのは、定義が変わる前のセッションの話を読み違えた場合だけ） |
| P2 | 独立-13 | low | no | self-inflicted | doc-claim | next-pr | 変更断片と実ファイルは review-log/README.md を変えているのに PR 本文の変更内容に無く、差分が review-log/ を全部除外するので README の変更はレビューの差分に一度も載らない。PR 本文には README の 1 項目を追記した。除外を記録ファイル（review-log/2*.md）に絞る案は次の PR |
| P3 | 独立-13 | low | no | self-inflicted | doc-claim | next-pr | 全レーン共通の「① に当たるもの（advisory を除く）は例外としてこの PR で直す」が、手順 6 の最終の全差分巡の打ち切り（2 回目は next-pr）を除いておらず、同じ規定が 2 か所で食い違う。全レーン共通の末尾に手順 6 が正本であることを足す |
| P4 | 独立-13 | low | no | self-inflicted | doc-claim | next-pr | J4（accepted）と同じ内容だが origin が this-diff なので再掲にせず、新しい指摘として通した。手順 5 の「medium 以下は next-pr」が実害クラスの medium を除いておらず、手順 6 と検査（実害=yes に next-pr を付けると落ちる）に対して抜けている。「実害クラスを除く」を足す |
| P5 | 独立-13 | low | no | self-inflicted | test-power | re-reported | J2 の再報告（前の巡で next-pr にした指摘は origin を問わず再掲にできる）。後方互換テストの除外 PRE_EXISTING_INVALID が名前だけの集合で、除外理由を検査しない。17 本を 1 つの for で直列に回すので並列化もされない。名前から期待する失敗理由への辞書にする案は J2 のまま次の PR |
| P6 | 独立-13 | low | no | self-inflicted | product | next-pr | 候補のスクリプトに repo 配下のサブディレクトリを渡すと、rev-parse は通るが git grep の範囲がそのディレクトリだけになり、警告なしで一部の一覧が渡る。rev-parse --show-toplevel を使い、pathspec を `:/` にする案は次の PR |
| P7 | 独立-13 | advisory | no | self-inflicted | test-power | accepted | 契約テストの代入 1 か所の検査は行頭の出現を数えるので、同じ行に別の文を置く形（セミコロン区切り）の追加代入は数えない。偶発的なドリフト（行頭の代入）は捕まる。ast で検査する案は PR 本文に列挙 |
| P8 | 独立-13 | advisory | no | self-inflicted | style | accepted | __pycache__/ の無視が plugin 配下の .gitignore に続いて scripts/.gitignore で 2 か所目になる。root の .gitignore に 1 行足す案は PR 本文に列挙 |
