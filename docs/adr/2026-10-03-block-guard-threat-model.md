# ADR: block guard は agent が事故で打つ形から守る

- **日付**: 2026-10-03（決定は 2026-10-02、ユーザー）
- **状態**: Accepted
- **Superseded（部分）by**: `docs/adr/2026-10-15-merge-gate-notice-only.md`（merge gate は止めなくなった）
- **Supersedes（部分）**: `docs/adr/2026-08-21-pr-w3-self-review.md` の ADR-6 のうち、守る範囲の線引きの測り方（下の Decision の 1 点目）
- **関連**: root `CLAUDE.md` 手順 6 の「`閉じ方: 列挙` の指摘」/ `plugins/gate-driven-development/references/reviewer-common.md` § Fix の影響範囲（`閉じ方` の定義）/ `plugins/gate-driven-development/references/self-review-lanes.md` の規律 C / `docs/adr/2026-09-11-env-s-merge-gate.md` / `plugins/gate-driven-development/docs/SECURITY.md` § 制限事項 / `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh` / `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py` / PR 旧#279・旧#293・旧#308・旧#321

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

## Context

GDD の block guard（merge gate・pre-push gate・pre-PR gate など）は、agent が Bash tool に渡す shell 文字列を解析して、block するかを決める。shell の文法は開いていて、同じ操作を書く形はいくらでも作れる（`. /dev/stdin <<< 'cd …'`、`trap 'cd /x' DEBUG`、`autoload` した関数、利用者のシェル設定の alias など）。

pre-push gate については、ADR-6（2026-08-21、逐語アーカイブ `plugins/gate-driven-development/docs/design/2026-08-21-pr-w3-self-review-adr.md`）が守る範囲を決めていた。守るのは「うっかりスキップの防止」で、シェル書式を意図的に選んだ迂回は守る範囲の外とし、意図せず通り抜ける形（行継続の数え漏れのような字句層のバグ）は直す。pre-PR gate も、統合のときにこの定義を引き継ぐことになっていた。一方、merge gate を含む guard 全体の守る範囲と、「意図せず」かどうかの測り方を決めた文書は無かった。独立レビューの § 常時 High（`reviewer-common.md`）にも、この線引きは届いていなかった。

そのため独立レビューは、作れる形をすべて guard の穴として high にした。PR は、その形を語・形の列挙で塞ぎ、次の巡で残りの形が high として出た。

- 独立レビューの 2 巡目以降の high 182 件のうち 65 件が、その PR の変更が生んだもので、shell 解析・パス解析の block guard に集まっていた（2026-10-02 の作業の時点の review-log の `## 指摘` を集計。root `CLAUDE.md` 手順 6 の「`閉じ方: 列挙` の指摘」に同じ数値がある）
- 旧#293 は、cwd を変える読み込みの語（`source`・`.`・`alias`）を列挙で数えた。high は 4 → 2 → 2 件と続き、検査を撤回して終わった。塞ごうとした形は、過去のマージ 934 件で 0 件だった（`review-log/20261003-merge-gate-hidden-chdir.md` の方針メモ-1 の行）
- その前の 旧#279 では、方針メモ-2 の Opus が、拒否リストへの継ぎ足しをやめて許可リストへ作り直すことを推していた（`review-log/20261002-merge-gate-cd-after-merge.md` の方針メモ-2 の行）。それでも、守る範囲が決まっていなかったので、次の PR（旧#293）で同じ形を塞ぎにいった

`docs/adr/2026-09-08-verification-closed-grammar.md` は、Markdown 表の検査で同じ型（9 巡・high 34 件）を、受理する形を閉じることで止めた。

## Decision

block guard は、agent が事故で打つ形から守る。敵対的に作らないと出ない形は、守る範囲の外とする。ADR-6 の線引き（意図の有無）をすべての block guard に広げ、意図を実測で決める。

- 「事故で打つ形」は、agent が実際に打った形として transcript に現れるもの（1 件以上）を指す。測り方は規律 C（`self-review-lanes.md`）に従う。ADR-6 の「意図せず通り抜ける形は直す」は、この実測で読み替える
- 独立レビューの high・blocking のうち `閉じ方: 列挙`（列挙でしか閉じない）のものは、root `CLAUDE.md` 手順 6 の (a)〜(c) で扱う
  - 守る範囲の外の形を通す穴は、直さずに `accepted` にし、PR 本文の限界の節の先頭に書いて、merge-ready とは書かずにユーザーへ渡す（(b)）
  - 事故で打つ形は、受理する形の許可リストで閉じる。拒否する語・形を足す修正は、閉じる修正に数えない（(a)）
- `閉じ方: 構造`・`有限集合`（既定の反転などで、同じ種類の入力を全部止める）の指摘は、守る範囲の外の形でも、今までどおり手順 6 の ① のとおり直す
- すでにある止める側の判定は、この決定を理由に外さない。たとえば `run-merge-gate-hook.sh` の (a‴) の拡張は、`builtin cd /B`・`cd -- /B`・語の途中の `#` で `cd` を隠す形も止めた（当時。今は実行後に通知する）。これらは守る範囲の外の形も含むが、止める側に倒れていて、正当な入力を止めた実測が無いので、そのまま残す。外すのは、正当な入力を止めると実測できたときだけにする
- (a) で許可リストを作るときも、上の既存の判定は外さない。root `CLAUDE.md` の (a) の「拒否する語のリストを併用しない」は、新しく作る許可リストの受理条件に拒否する語を混ぜないことを指し、既存の止める側の判定を外すことは求めない

`docs/adr/2026-09-11-env-s-merge-gate.md` の後続の制約（env 分岐のクラスタの新しい fail-open は、開示で受容せず直すか人間に判断を戻す）は置き換えない。(b) は merge-ready とは書かずにユーザーへ渡すので、「人間に判断を戻す」に当たる。

### 却下した代替案

- **敵対的な agent からも守る**：却下する。shell 文字列の検査は、この相手に対しては原理的に閉じない。利用者のシェル設定の alias は、コマンド文字列に現れない（旧#279 E1）。閉じない検査を続けると、PR ごとに巡が収束しない
- **守る範囲を PR ごとに方針メモで決める**：却下する。旧#279・旧#293 では、PR ごとの相談は最初に列挙で塞ぐ案を推し（旧#293 の方針メモ、旧#279 の方針メモ-3）、high の巡を重ねてから、列挙では閉じないと分かった（旧#279 の方針メモ-2、旧#293 の方針メモ-1）。PR ごとに決めると、同じ巡を毎回繰り返す

## Consequences

- 守る範囲の外の形は、guard を通る。たとえば `. /dev/stdin <<< 'cd /other'; gh pr merge 7` は merge gate を通りうる。これは事故では起きない形として受け入れ、plugin の `docs/SECURITY.md` § 制限事項にも書く
- 独立レビューは、今までどおり守る範囲の外の形も high として出す（§ 常時 High は変えない）。振り分けは root `CLAUDE.md` 手順 6 が行う。そのため、`accepted` の high が残った PR は merge-ready とは書かずに渡す
- 守る範囲の内か外かは、transcript の実測で決める。測れないときも `accepted` にし、限界の節に「入力者: 未測」と書く
- ADR-6 の線引きのうち、字句層のバグでも transcript に現れない形（G-9 の偶数個の `\` など）は、`列挙` の指摘なら直さずに `accepted` になる。`構造` の修正で閉じるなら、今までどおり直す
- 撤回条件：守る範囲の外とした形を agent が事故で打ったことが transcript で観測されたら、その形は守る範囲の内に入り、許可リストで閉じる

## 追記（2026-10-08）

`閉じ方` の定義を `plugins/gate-driven-development/references/reviewer-common.md` § Fix の影響範囲 に移し、全 reviewer の `concrete fix` に付けるようにした（旧#403。軽いレーンの独立レビューでは advisory を除く全 finding）。`列挙` は、開いた入力のほかに、規定に条件・例外・範囲の定義を足して新しい境界ができるものも含む。root `CLAUDE.md` 手順 6 が方針メモ-N に回すのは、今までどおり § 常時 High の適用範囲の部品の high・blocking である。上の Decision の (a)・(b) は入力の形を前提にしている。`修正後に残る形` が入力の形でない `列挙`（状態・時刻・記録の読み方など）に何を測るかは、方針メモ-N で決める（2026-10-03〜07 の `列挙:` の行 37 件では、待ちの期限・transcript の記録の読み方なども方針メモ-N を通り、18 件が `fixed`、19 件が `accepted` だった）。

## 追記（2026-10-19）: guard ごとに block を残すか

依頼（2026-10-19、ユーザー）: 「guard ごとの判断に着手して。棚卸しの表に沿って 1 PR 1 guard で進めて」。

### 決め方

guard ごとに守る事故を 1 行で決め、止めた件数のうち止める必要が無かったもの（誤）の割合と、その guard を直した PR の数（保守の費用）で、block を残すかを決める。「事故を防いだ例が transcript に 1 件以上ある形だけ block にする」は採らない。block が効いていれば事故は記録に残らないので、測れないためである。

Stop hook の押し返しには、通知の段が無い。agent に届くのは `decision: block` の reason だけで、`systemMessage` は利用者にしか出ない（`gdd_stop_hook.py` の `_emit_block`）。そのため Stop hook の型の選択肢は、残す・判定を直す・消すの 3 つで、「通知に下げる」は agent から見ると「消す」と同じになる。

### 件数と判断

件数は、2026-09-15〜10-15 の棚卸し（作者の手元の分析ノート（非公開））と、10-15〜10-19 を同じスクリプトで数え直したもの。案内どおりは、止められた後に agent が案内のとおりに直して進んだもので、事故を防いだかどうかは分からない。事故を防いだ例（正）は、どの guard でも 0 件だった。下の「残す」の根拠は、誤が 0 か少ないことで、事故を防いだことではない。

| guard / 型 | 守る事故 | 30 日（案内・誤・不明） | 10-15〜19（案内・誤・不明） | 判断 |
|---|---|---|---|---|
| wait loop gate | 上限の無い待ちのループで、セッションが止まらなくなる | 66・0・9 | 24・0・4 | 残す |
| steering write guard の秘密系（aws-account-id・secret-marker・sensitive-value・email） | 秘密の値・個人情報を steering に書く | 25・0・4 | 2・0・0 | 残す。止めた値が本物かは測っていないので、止める側に倒したままにする |
| steering write guard の書式系（placeholder・abs-path・state-fields・line-separator ほか） | 使えない steering を残す（未記入の欄・手元の絶対パスなど） | 149・2・14 | 9・0・0 | 残す |
| steering write guard の size | steering が大きくなりすぎる | 247・9・35 | 41・0・4 | 通知に下げる（旧#542） |
| steering write guard の cross-session-approval | 別のセッションの発言を承認として扱う | 0・11・0 | 0・4・0 | 判定を直した（旧#526）。誤はすべて 旧#526 の前 |
| root branch guard | root checkout で task branch を作る | 3・11・1 | 0・1・0 | 残す。誤は 旧#423・旧#505・旧#517 の前で、その後の実の deny は 0 件（10-15〜19 の 1 件は検証用のもの） |
| Stop hook の wait-watchdog（no-timer・overdue） | 期限の無い待ち・上限を超えた待ちを放置する | 61・0・0 | 18・0・0 | 残す |
| Stop hook の next-action-block-missing | 人に渡す停止で、次にすることを書かない | 24・0・0 | 2・0・0 | 残す |
| Stop hook の merge-intent-pr-open | マージ待ちの宣言があるのに、待たずに止まる | 19・0・7 | 0・0・3 | 残す |
| Stop hook の merge-promise-without-intent | 「CI が通ったらマージする」と書いて、待つ仕組みを置かずに止まる | 23・8・4 | 4・4・4 | 残す（下の再判定の条件で見直す） |
| Stop hook の continuation | active な `/gdd-dev` を途中で止める | 9・49・0 | 1・4・1 | 判定を直した（旧#520・旧#541）。誤はすべて 旧#541 の前 |
| merge gate・pre-push gate・pre-PR gate | 承認の無い merge・push・PR | — | — | 通知に下げた（旧#514・旧#535） |
| HITL lint | 品質の低い human check を出す | — | — | 警告だけにした（旧#485） |

2026-10-16 の検討（作者の手元の分析ノート（非公開） 3.1）は、merge-promise-without-intent と root branch guard を通知に下げる側に挙げていた。数え直すと、merge-promise-without-intent は案内どおりが多く（47 件中 27 件。宣言を書いて待つ仕組みを起動した）、root branch guard は直した後の誤が 0 件だったので、どちらも残す。同じ検討が残す側に挙げていた HITL lint は、旧#485 で警告だけになっている。

### merge-promise-without-intent の再判定の条件

判定は、最後の発言の末尾 600 字を正規表現（`autonomy_pushback.py` の `_PROMISE`）で読む。47 件のうち、誤の 12 件のうち 10 件は、「マージしません」「merge-ready とは言えません」などの文の後に続く「マージする…」に当たったもの（残る 2 件は、マージしない方針の説明の中の「CI が通ったらマージする」）で、不明の 8 件のうち 4 件は「PR がまだ無いので宣言を書けない」停止だった。1 回の誤の費用は agent の 1 ターンで、押し返しは 600 秒に 1 回までである。

- 否定の語を除く直し方は採らない。自由文への列挙の継ぎ足しで、上の Decision が閉じる修正に数えない形である
- 文の区切りを越えて一致させない直し方も採らない。誤 12 件のうち 10 件は押し返さなくなるが、案内どおりの 27 件のうち 10 件も押し返さなくなる（「CI の完了を待っています。終わったらマージします」のように、約束が 2 文にまたがるため）
- 宣言した欄と状態で閉じる直し方も、今は採らない。候補は、人に戻す停止の marker（`<gdd-stop reason="…">`）があるときは押し返さない、PR が無いときは押し返さない、の 2 つだった。数えると、誤 12 件のどれにも marker は無かった（marker があったのは、案内どおりの 1 件だけ）。不明 8 件は、どれも停止の前に transcript に PR の URL が出ていたので、transcript から PR の有無を見ても区別できない（今の branch の PR を `gh` で引いたときの件数は測っていない）。当たる件数が 0 なので足さない
- 型ごと消すのは、週次の数え直しで、続く 2 つの窓（各 10 件以上）とも案内どおりが誤と不明の合計より少なくなったときにする
- 2026-10-09 にユーザーは、約束の文の側の判定を変えない案を選んでいる（`review-log/20261009-merge-wait-skip-when-waiting.request.md`）。直すときは、この決定を変えることをユーザーに示す

### 再判定の時機

merge gate の撤去の検討（`docs/adr/2026-10-15-merge-gate-notice-only.md`）と同じ 2026-11-15 以降に、同じスクリプトで全 guard を数え直す。誤の割合が案内どおりを上回った guard は、その guard だけを扱う PR で、判定を直すか消すかを決める。

## 追記（2026-10-30）: (b) を再設計に向けた

root `CLAUDE.md` 手順 6 の `閉じ方: 列挙` で、入力者が 0 件か、敵対的に作らないと出ない形か、測れないときは、`accepted` にして限界に書かず、行き詰まりとして再設計に進むようにした（ユーザー決定。PR 旧#624）。上の Decision の (b) は、軽いレーンではこの再設計に置き換わる。再設計は 1 PR 2 回までで、その後はユーザーに戻す。許可リスト（(a)）も再設計の候補に入る。
