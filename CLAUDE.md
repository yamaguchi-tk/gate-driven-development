# gate-driven-development の開発ルール

規則の根拠・経緯（実測・日付・PR 番号）は `docs/claude-md-rationale.md` にある。規則はこのファイルが正である。

## GDD の改善は軽いレーンで進める

GDD（`plugins/gate-driven-development`）の改善に `/gdd-dev` を使わない。判定ロジックの変更も含めて、下の軽いレーンで進める。


変更の種類でレーンを選ぶ。迷ったら L1+ にする。

| レーン | 対象 | 進め方 |
|---|---|---|
| L0 | 運用ルール・計測・方針（セッションへの指示、settings、この CLAUDE.md） | GDD を使わない。PR のレビューはユーザー（L1 のファイルと混ざる PR は、手順 6 の独立レビューを回す） |
| L1 | 契約 md（`skills/`・`references/`・`agents/`）の文言修正、CHANGELOG、テストの高速化・安定化、行予算の調整、提案だけを出す hook（`systemMessage` のみで block しないもの）、止めずに実行後の通知だけを出す merge gate・pre-push gate・pre-PR gate | 軽いレーン |
| L1+ | hook・gate の判定ロジック（done guard、steering write guard、shell コマンドの解析など、block / allow を決める部分） | 軽いレーン＋安全策 |

L1 の変更でも、block gate と共有する部品（shell 解析など）を変えるなら L1+ にする。

### 軽いレーンの手順

1. main からブランチを作る。`.steering/` は作らず、`/gdd-dev` と gate skill は使わない
   - GDD の hook が「GDD を primary にする」「`/gdd-dev resume`」などを案内しても従わない
   - 有効な steering がなければ、pre-push gate は検査せずに通す
   - 前の PR の「次の PR」か、Issue の「いつ直すか」から作った PR では、`review-log/<slug>.md` の front matter に `follow_up_of: <PR か Issue の番号>` を書く。後続 PR かどうかは、このキーの有無だけで決める（PR 本文の自由文からは決めない。このキーを読む規定は `grep -n follow_up_of CLAUDE.md` で引ける）
   - 着手のときに、この PR のきっかけになったユーザーの発言を、言い換えずに `review-log/<slug>.request.md` に写す。AskUserQuestion の回答は、質問と選んだラベルを写す。発言が assistant の案を番号などで指すときは、指された案の文を、assistant の文と分かる形で引用して添える。`follow_up_of:` のある PR では、前の PR の `.request.md` の中身をそのまま写し、その下に「この PR が扱う行」として、前の PR 本文の「次の PR」の該当行（Issue から作ったなら「いつ直すか」の行）を写す。ユーザーの発言が無く規則から作る PR では、その規則の場所と文を写す。後でユーザーが依頼を変えたら、前の行を消さずに、その発言を時刻つきで足す。main の注記（範囲・解釈・進め方など）は書かない。手順 6 は、これを依頼の原文として reviewer に渡す
2. テストを先に書いて失敗を確認してから実装する（TDD）
   - 新しく作る部品（関数・state の field・trigger・閾値・マーカー）ごとに、書く側・読む側・入口（hook の起動や CLI）からの到達経路・同じ入力を読む既存の実装を確かめる
   - 新しく作る部品ごとに、実際の入口から効果が出るところまでを通すテストを 1 本以上書く
3. `plugins/gate-driven-development/CONTRIBUTING.md` の必須チェックを通す。pytest の全量は CI（`.github/workflows/plugin-lint.yml`）が回す。ローカルで回すのは、関係するテストと `validate-plugin.sh` だけ
   - 関係するテスト: 変更したファイルの名前（拡張子を除いた部分）を参照するテスト（`grep -rl <拡張子を除いた名前> plugins/gate-driven-development/tests/`）と、この PR で足した・変えたテスト。拡張子を除くのは、`from lib.errors import` のように名前だけを書くテストも拾うため。GDD の helper（`tests/_*.py`）がその名前を含むなら、helper の名前を参照するテストも入れる。GDD 以外の plugin を変えたら、その plugin の `tests/` 直下の `test_*.py` も入れる（`.claude-plugin/marketplace.json` なら GDD 以外の全 plugin。pytest でない検査〔aws-investigate の `tests/validate-plugin.sh`〕は CI も回さないので、変えたときは手で回す。スクリプトが stderr に出す）。この規則の列挙と実行は `python3 scripts/light-lane-related-tests.py --run . origin/main` で行い、grep を手で組み直さない（commit していない変更と untracked のファイルも数える。1 件も無ければ pytest を回さずに 65 で終わる。`$(…)` で受けて pytest に渡すと、zsh は改行で分けない）。block gate と共有する部品（shell 解析など）を変えたときは、その部品を参照するテストを全部入れる。スクリプトが拾わないテストは `-- <テストのパス…>`（top-level から見たパス）で足す。迷ったら範囲を広げる
   - `bash plugins/gate-driven-development/tests/validate-plugin.sh` は軽いので、ローカルでも回す
   - ローカルで全量（`python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`）を回してよいのは、CI が使えないとき（Actions の障害など）、release 前（`plugins/gate-driven-development/CONTRIBUTING.md` 項 0）、hooks を local に入れる前（`plugins/gate-driven-development/references/gdd-self-development.md` § 開発場所の使い分け）だけ
   - skill 本文・prompt・reviewer policy・HITL 出力契約を変えたら、1c の `Skill RED-GREEN Evidence` を `review-log/<slug>.notes.md` に残す（superpowers 同等品がある primitive なら 1b も）
4. 変更断片（`plugins/gate-driven-development/changelog.d/`）を確定する。版数と `CHANGELOG.md` の版の節には触れない（リリースでまとめて上げる）
   - 断片の内容・書式（利用者から見える変更だけを書く・確定の時機・必須の節）の正本は `CHANGELOG.md` § Policy
   - 断片と `review-log/` の 1 対 1 対応（`review-log-present.sh` の検査）は変えない
   - 確定したら、手順 3 のローカルの確認（関係するテストと `validate-plugin.sh`）をもう一度回す
5. Codex は定常の手順では使わない。セカンドオピニオンとして、次のどちらかのときだけ使う
   - 手順 6 の行き詰まりで再設計するとき（再設計の材料として、Opus の案と並べる）
   - ユーザーが指示したとき
   - 1 PR あたり最大 1 回
   - 起動の仕方と結果の扱いは、起動の前に `docs/light-lane-codex.md` を読む
6. 独立レビューを行う。`plugins/gate-driven-development/references/independent-review.md` の契約 3（対象は push 対象 tip の diff）と契約 4（independent_review tier のモデル・effort と、push 1 回あたり 1 回）は、軽いレーンではこの手順で置き換える。契約 1（渡すのは diff とリポジトリの read-only アクセスだけ）は、下の PR 本文の抜粋と依頼の原文の分だけ緩める。契約 1 を破った巡（reviewer が `テンプレート外の記述あり` を報告した巡）も、軽いレーンでは有効な独立レビューに数える（扱いは下の報告の行のとおり）
   - 起動は固定テンプレートで行う。`subagent_type` に、全差分巡（下の「全差分（無効化後）」を含む）では `light-lane-independent-reviewer`（`.claude/agents/light-lane-independent-reviewer.md`。model と effort は定義側で `opus`・`xhigh` に固定）、差分巡（「差分（無効化後）」を含む）では `light-lane-independent-reviewer-xhigh`（本文が同じ。model・effort は `fable`・`high`）を指定し、prompt には定義の末尾の呼び出しテンプレートの欄を埋めたものだけを渡す。観点（`plugins/gate-driven-development/references/independent-review.md` のレーン (a)〜(h)、L1+ では (g)(h)＋security、gdd-pr-review の 2a/3a/3d/3f、PR 後の外部レビューで繰り返し出た型）と read-only の指示は定義の本文にある。欄の外に文を足さない（実装の経緯、前回の指摘、「対応済み」「通るはず」などの誘導、指摘を控えるよう求める文）
     - 差分巡を Fable 5.2 high にするのは、1 巡の時間を縮めるため。差分巡を Fable で回した PR が 10 本たまったら、`docs/claude-md-rationale.md` の読むものと撤去の条件で読む
   - commit の件名と本文には、変更の内容だけを書く。巡の ID（`独立-N` など）と、どの指摘への対応かは書かない
   - 差分は一時ファイルに書き出し、テンプレートにはその絶対パスを書く（`git diff <base>..<tip> -- . ':(exclude)review-log/' > <差分ファイル>`）。prompt に本文を貼らない。`$(cat …)` も使わない（展開されずにリテラルで届く）。`review-log/` を除外しないと、reviewer が前の巡の指摘を読んでしまう
   - 呼び出し元の候補は同じ差分から `scripts/light-lane-review-candidates.py` で作り、ファイルのパスを渡す（`python3 scripts/light-lane-review-candidates.py . < <差分ファイル> > <候補ファイル>`）。main が選んだり足したりしない。reviewer の往復を減らすための起点で、網羅は保証しない
   - 依頼の原文（手順 1 の `review-log/<slug>.request.md`）も、一時ファイルに写してパスを渡す。中身を言い換えたり、抜粋したりしない。reviewer が依頼の原文から外れたと指摘したもの（範囲を狭めた・広げた、語を読み替えた、合格基準を替えた、確認なしに範囲外・後回しにした、頼まれた手段を別の手段で代えた）は、限界の節に書くだけで閉じない。severity によらず、実装を依頼に合わせて直す（`fixed`）。直さずにユーザーに確かめ、その発言を `.request.md` に足すのは、(a) 直すと `.request.md` に後から足したユーザーの決定と食い違う、(b) 依頼が 2 通りに読め、どちらに合わせるかが推測になる、(c) 依頼に合わせると +1,000 行を超えるか、別の機能・別のファイル群に広がる、のどれかに当たるときだけである。ユーザーに確かめるとき（reviewer の指摘によるものも、main が自分で気づいたずれも）は、返事を待つ tool（AskUserQuestion など）を使わない。本文に問い・推奨の案で進めていること・違う案を選んだときに戻す範囲を書き、推奨の案で作業を続ける。返事を待つ間、その指摘は `accepted` にして要約の先頭に `確認待ち:` と書き、PR 本文の限界の節に問いを書く。返事が来たら、その発言を `.request.md` に時刻つきで足し、PR 本文から問いと戻す範囲を消し、推奨と違う案なら直す（直す commit の扱いは、ほかの修正と同じ）。返事が無いうちは merge-ready と報告しない。ただし、下の再設計の上限でユーザーに戻したときは、限界の節に書き、依頼から外れたままであることを明記する。契約 1 は、この欄の分も緩める（渡すのは手順 1 が写すものだけで、ほかの会話は渡さない）
   - PR 本文の抜粋（GitHub の PR 本文から目的・変更内容・限界の節だけを抜いたもの。レビュー結果の行は除き、限界の節からも、巡の指摘を受け入れた記録（手順 6 が書かせる、直していない指摘）は除く。PR 作成前は草案）も同じようにファイルに書き、パスを渡す。`plugins/gate-driven-development/references/independent-review.md` の契約 1（渡すのは diff とリポジトリの read-only アクセスだけ）は、軽いレーンではこの欄と依頼の原文の欄の分だけ緩める。欄には巡の ID・前の巡の指摘とその対応・実装の経緯・review-log の中身・「対応済み」「通るはず」などの誘導・指摘を控えるよう求める文を書かない
   - reviewer が `advisory: テンプレート外の記述あり` を報告しても、その巡は有効のままにし、起動し直さない。見つかった指摘は、ほかの巡と同じく振り分ける。報告は `## 指摘` に advisory の行として記録し、報告された記述は、次の巡の前に prompt と抜粋から除く
   - 読み込みの照合をする。reviewer は出力の冒頭に `読み込み: 差分 <読んだ行数>/<ファイルの行数> 行、候補 <候補の行数> 行、PR 本文 <PR 本文の行数> 行、依頼 <依頼の原文の行数> 行` を出す。main は 4 つのファイルの `wc -l` と突き合わせ、1 つでも合わなければその巡を無効にして起動し直す
   - パスの区分。巡の無効化（下の「最後の独立レビューの後に commit を積んだとき」）は「判定のコード」だけで決める
     - 判定のコード：plugin の `hooks/`・`scripts/`・`tests/checks/`・`tests/validate-plugin.sh`・`evals/`・`.claude-plugin/plugin.json`・`.cursor-plugin/plugin.json`・`.codex-plugin/plugin.json`、repo root の `scripts/`・`.github/workflows/`・`.claude-plugin/marketplace.json`、plugin の `docs/VERSIONING.md`（3 manifest・`marketplace.json`・`VERSIONING.md` は、版数・配布識別子の宣言だけを目的とするファイルで、`grade-evals.sh`・`version-not-consumed.sh`・`review-log-present.sh` がその宣言値を読んで一致を検査する。`evals/` は `tests/checks/hooks.sh` が中身を読んで必須 eval の有無を検査する。同じ理由で `CHANGELOG.md`〔版の見出し行の書式は `version-not-consumed.sh` が読むが、文書の主目的は変更履歴であり対象に含めない〕とは区別する）
     - 規則の文書：plugin の `references/`・`skills/`・`agents/`・`commands/`、repo root の `.claude/agents/`・`CLAUDE.md`・`AGENTS.md`・`.github/`（`workflows/` を除く。`copilot-instructions.md`・`instructions/` など、外部 bot・reviewer 向けの散文）、plugin の `CONTRIBUTING.md`
     - どちらにも入らないもの（`tests/test_*.py` などのテスト、`changelog.d/`、`review-log/`、`docs/`（`VERSIONING.md` を除く）・README などの文書）は、巡を無効にしない。ただし、テストを削除する、または assert を緩める変更（比較条件の緩和・許容範囲の拡大・`skip`/`xfail` 化など）を含む commit は、判定のコードと同じ扱いで巡を無効にする
   - 巡は 2 種類ある。1 巡目で指摘を全部出し、2 巡目以降はその修正の差分だけを見る
     - 全差分巡：base は `git merge-base origin/main HEAD`。1 巡目と、下の差分巡の代わりにだけ使う。1 巡目の reviewer の出力（high〜advisory の全 severity）を記録した `## 指摘` の行が、この PR の台帳になる
     - 差分巡：base は前回の独立レビューの sha。2 巡目以降はすべてこれにする。前回の sha が解決できない、または履歴が書き換わったなら全差分巡にする。差分が空なら巡を回さず、前の巡を最後の独立レビューとする。ただし前回の独立レビューの後に `fixed` にした行があるのに差分が空なら、直した分がまだ commit に入っていないので、commit してから差分巡を回す
     - 最後の巡を全差分に戻さない。1 巡目の全件と差分巡で 2〜3 巡に収めることを優先し、この取りこぼしは限界として受け入れる
     - 台帳は reviewer に渡さない。前の巡の指摘との突き合わせは、下の「先に再掲を分ける」のとおり main が行う
   - 巡の終わり方：巡の後に直す commit を積まなかったら、その巡を最後の独立レビューとする。直したら、次の差分巡でその修正を見る（上限の巡の後は、下の巡の上限と行き詰まりに従う）。直す commit が無いのは、下の振り分けでこの PR で直すものが 1 件も出なかったときである。限界に回したもの（再設計の上限でユーザーに戻したもの）は、直すものに数えない。PR 本文だけを直す指摘（抜粋の書き漏れなど）も、直す commit に数えない（手順 7）
     - `fixed` にした `## 指摘` の行の要約の末尾には、直した commit を `commit: <sha>` の形で書く（PR 本文だけを直したなら `commit: なし（PR 本文）`）。差分巡を回すかどうかを決める前に、main は前回の独立レビューの後に `fixed` にした行ごとに、その sha が `git log <差分巡の base>..HEAD` に入っていて、`git show --name-only --format= <sha>` に指摘の `file:line` のファイルが入っていることを確かめる。どちらかが欠けていたら、直してから回す（記録だけ直して実ファイルに入っていない型を、差分巡では reviewer が拾えないため）
   - 先に再掲を分ける。前の巡で記録した指摘（Issue にしたもの〔`deferred`〕、`accepted`・`next-pr`・`out-of-diff` にしたもの）の再報告は、巡の high・medium・blocking に数えず、この PR では直さない
     - 再掲にできるのは、記録した行と比べて severity が同じか低く、`reviewer-common.md` の § 常時 High にも実害クラスにも当たらず、`origin: pre-existing` のものだけである。ただし前の巡で `next-pr` にした指摘（手順 5 の Codex の分と、ユーザーの指示で次の PR にした ① の分）と、下の ① の規定で `accepted` にした ① の、blocking でない medium・low の分は、`origin` を問わない。どれかに当たらなければ、新しい指摘として下の振り分けに通す
     - 照合は reviewer に経緯を渡してさせない。main が、同じ `review-log/<slug>.md` の既存の行と Issue に突き合わせる
     - `## 指摘` には行を残し、`対応` を `re-reported` にする
   - 残りの指摘は、独立レビューの出力の `origin` と `差分との関係`（`変更箇所` / `影響先` / `無関係`）で行き先を決める。main が自由文から推定し直さない
     - ① `origin: this-diff`、`変更箇所`、`影響先` のどれか（変えた関数の中、その呼び出し元、同じ入力を読む別の実装、同じ規定を定める別の箇所）：どの巡でも、この PR で直すのは high と blocking（blocking の medium・low を含む）と、前の巡でこの PR で直すことにしてまだ直っていないものだけである。blocking でない medium・low は直さず `accepted` にする。依頼の原文から外れたという指摘は、上の依頼の原文の行に従う。① の指摘を次の PR にするのは、ユーザーが指示したときだけである。blocking に数えるのは `reviewer-common.md` の `is_blocking`（実害クラス）に当たるものだけで、① の medium・low も、実害クラスでなければ blocking には数えない（実害クラスの medium・low は blocking で、直す）。advisory は直さない。§ 常時 High の適用範囲の部品の high・blocking で `閉じ方: 列挙` のものは、下の「`閉じ方: 列挙` の指摘」に従う。§ 常時 High の適用範囲外の部品の指摘と medium・low でも、入力が開いていて列挙で閉じないものは直し続けず、`accepted` にする
     - 差分巡で `無関係` とされても、指摘の `file:line` がこの PR の全差分（merge-base..tip）の変更行に入るなら ① にする
     - ② `無関係` のうち、話題としてだけ関連するもの（同じ機能の、差分が触っていない側。差分は文書で欠陥はコード、など）：この PR には入れない。この PR の直後に次の PR として直し、PR 本文の「次の PR」に列挙する。`対応` は `next-pr`
     - ③ `無関係` のうち ② に当たらないもの（reviewer が差分の外を監査した）：実データに該当があれば ② と同じにする。無ければ対応しない。`対応` は `out-of-diff`
     - `next-pr`・`out-of-diff` と `re-reported` は `## 巡` の high・medium に数えない（`review-log-present.sh` も除いて照合する）。`deferred`・`accepted` は今までどおり数える
   - ②③ でも、次のものはこの PR で直す（blocking のまま）
     - `plugins/gate-driven-development/references/reviewer-common.md` の § 常時 High（対象の部品は同節の適用範囲に従う）と実害クラス
     - 前回までに ① か上の 1 点目でこの PR で直すことにして、まだ直っていないもの
   - `閉じ方: 列挙` の指摘（reviewer の固定フィールド。定義は `plugins/gate-driven-development/references/reviewer-common.md` § Fix の影響範囲）：巡を問わず、§ 常時 High の適用範囲の部品の high・blocking に `閉じ方: 列挙` が付いたら、reviewer の修正案の commit を積まず、下の方針メモ-N で (a)〜(c) を決める。① と上の「②③ でも、次のものはこの PR で直す」より優先する。main は値を上書きしない。§ 常時 High の適用範囲の部品の high・blocking で `閉じ方` の欄が無いもの（定義を読み込む前から動いているセッション、Codex、PR 後のレビュー）は、`列挙` として扱う
     - 方針メモ-N として `spec-autopilot:opus-advisor` に、巡ごとに並行に 2 本相談する。その巡の `列挙` の指摘をまとめて扱う。起動の仕方と、呼べないときの扱いは安全策 1 と同じ。全レーン共通の確認の前の相談と同じく、相談ごとの観点や前回の推奨は足さない。2 本が割れた点は、main が下の入力者の実測で決める。決めきれなければ、行き詰まりとして下の再設計に進む
     - 入力者を `plugins/gate-driven-development/references/self-review-lanes.md` の規律 C のとおり実測し、既定を次のように決める
       - agent が事故で打つ形として transcript に現れる（1 件以上）なら、(a) 受理する形を許可リストで閉じる。引用符・改行・`$`・バッククォートは受理せず、拒否する語のリストを併用しない。拒否する語・形を足す修正は (a) に数えない。許可リストに実データを当てて誤 block の件数を測り、方針メモに書く。正当な入力を 1 件以上止めるなら、規律 C のとおり別の直し方と比べ、その結果も書く。(a) を選んだら、許可リストの修正を commit し、指摘を `fixed` にする（直す commit に数える）
       - 0 件か、敵対的に作らないと出ない形か、入力者を測れないときは、(b) 行き詰まりとして下の再設計に進む（(a) の許可リストも再設計の候補に入る）
       - (c) 要件・スコープを縮めるのは、ユーザーが指示したときだけ
     - 方針メモ-N の行は、安全策 4 で数えない
     - `## 指摘` の要約の先頭に `列挙:` と書く（効果を後から数えるため。検査はしない）
   - 独立レビューの finding で、`差分との関係` が欠けている、または値が 3 つのどれでもないものは ① として扱う（欄の無い Codex の指摘は手順 5 に従う）
   - 巡の上限：push までの独立レビューは、1 PR あたり 3 巡（全差分 → 差分 → 差分）まで。数えるのは `review-log/<slug>.md` の `独立-N` の行だけで、手順 5 の `codex-N` と、下の「最後の独立レビューの後に commit を積んだとき」の差分巡は数えない
     - 3 巡目の後は、4 巡目を回さない。3 巡目の指摘も ① の振り分けで直し、直したら、直したファイルの種類を問わず、下の「最後の独立レビューの後に commit を積んだとき」の差分巡（base は 3 巡目の sha。2 回まで）で確かめる
     - 下の再設計の後は、最後の `再設計` の行より後の `独立-N` だけを数え、上限は 2 巡（差分 → 差分。1 本目の base は再設計の前の最後の独立レビューの sha）にする。2 巡目の後は確かめの差分巡を回さない
   - 行き詰まり：次のどれかに当たったら、残った high・blocking を `accepted` にせず、直す commit も積まずに再設計に進む。HITL はせず、返事も待たない
     - 上限の巡の後に high・blocking が残った（3 巡目の後に直したときは、確かめの差分巡 2 回の後も残った）
     - 「最後の独立レビューの後に commit を積んだとき」の差分巡の 2 回目の後も残った
     - L1+ で安全策 4 の条件に当たった
   - 再設計：「指摘を直すとき」の 1 点目を、残った high・blocking と、それまでの巡の high・blocking の全部に、クラスタを問わずまとめて当てる。L1 でも `spec-autopilot:opus-advisor` に並行に 2 本相談する（起動の仕方と呼べないときの扱いは安全策 1 と同じ。材料は差分・実コード・`review-log/<slug>.md`・`.request.md` の場所）。同じ形の修正（列挙を足す・述語を狭める）は再設計に数えない。2 本が割れたら、作り直す側を採る
     - 相談の前に、main が `.request.md` に照らして、行き詰まりを生んだ前提を自分で点検する。ずれた前提があれば、その前提を変える側から作り直す。依頼の読み方か合格基準が変わるときだけ、上の依頼の原文の行の (b) としてユーザーに確かめる
     - 推奨の設計で作り直して commit する。部品を置き換え・撤去してよい（「指摘を直すとき」の、簡素化・スコープの縮小を混ぜない規定の例外）。依頼の範囲を縮めるのはユーザーだけで、+1,000 行の相談（全レーン共通）はそのままにする
     - 作り直しで依頼に無い部品（field・閾値・マーカー・分岐など）を足すときは、先に、その部品で止まる損失を既存の記録で数え、`方針メモ-N` の要約に件数を書く（数え方は全レーン共通の新しい発火条件の行と同じ）。0 件なら足さず、その部品の無い設計で直すか、残った指摘を `next-pr` にする
     - `方針メモ-N` の巡として記録し、reviewer 列の先頭に `再設計` と書く。`## 指摘` の要約の先頭に `再設計:` と、点検の結果を `前提: 合う` か `前提: ずれる（<前提>）` で書く（効果を後から数えるため。検査はしない）。安全策 4 も、この行より後の巡だけを数える（安全策 4 が reviewer 列を読まない規定の例外）
     - 再設計は 1 PR あたり 2 回まで。2 回目の後にまた行き詰まったとき、または 2 本がともに種類ごと消す設計の変更は無いと答えたときは、ユーザーに戻して返事を待つ（全レーン共通の「依頼の機能が実装できる見込みが無いとき」に当たる）。PR を作り（作成済みなら本文を更新し）、残った high・blocking を `accepted` にして要約の先頭に `確認待ち:` と書き、PR 本文の限界の節に問いを書く。材料は、再設計の内容、残った指摘、巡数と経過時間、選択肢（ユーザーが方向を与えて再設計を続ける／依頼の範囲を縮める／PR を分ける／限界として出す）。限界として出すのはユーザーが選んだときだけで、§ 常時 High・実害クラス（`is_blocking`）は限界の節の先頭に「直していない常時 High・実害クラス」として書く
   - 各巡の後は、関係するテストと `validate-plugin.sh` を回す
   - 各巡の直後に `review-log/<changelog.d/ の断片と同じ slug>.md` の `## 巡` に 1 行、`## 指摘` に指摘の行（0 件でも `要約: なし` の行を 1 本）追記する（書式の正本は `review-log/README.md`、強制は `plugins/gate-driven-development/tests/checks/review-log-present.sh`。`review-log/` は repo root 直下で、plugin 配下には置かない）。reviewer 列には agent 名・範囲・model を書く（例：`light-lane-independent-reviewer, 全差分, model: opus`、`light-lane-independent-reviewer-xhigh, 差分, model: fable`。上の「最後の独立レビューの後に commit を積んだとき」の差分巡は `light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable`、main の取り込みの後の全差分は `light-lane-independent-reviewer, 全差分（無効化後）, model: opus` と書き、通常の巡と区別する。差分（無効化後）では、呼び出しテンプレートの `範囲` 欄自体は `差分` のまま渡す）。`## 指摘` の `自己起因` は、指摘の `file:line` がこの PR の全差分（merge-base..tip）の変更行に入るか、reviewer が `origin: this-diff` を付けたら `self-inflicted`、それ以外は `inherited` にする。巡の差分では決めない
   - 終了条件（merge-ready）は次の 3 つがそろったときである。PR 本文には、巡については手順 7 のレビュー結果の 1 行だけを書き（3 つ目の CI は待たない）、「merge-ready」とは書かない。merge-ready と宣言するのは、3 つ目を確かめた後の、ユーザーへの報告だけである。マージはユーザーが行う
     - 最後の独立レビューが上の起動の agent で走り、上の「巡の終わり方」で最後になった巡か、下の「最後の独立レビューの後に commit を積んだとき」の差分巡のどちらかである
     - その巡が high=0・blocking=0
     - PR の head（push 対象の tip）で、CI（`plugin-lint` の `gdd-plugin`。pytest の全量と `validate-plugin.sh`、plain-writing と japanese-reply-guard の pytest）が success になっている（job が始まらないときは手順 7）。PR の check で確かめる。CI は PR を作るまで走らず、結果は PR 本文を書いた後に出るので、run の URL・件数は PR 本文に書かず、ユーザーへの merge-ready の報告に書く。`review-log/` だけを変える commit の run は、その前の tip の結果を引き継いでよい。テストだけを変える commit の run は引き継がず、その tip の run を見る
   - 最後の独立レビューの後に commit を積んだとき（PR 上のレビュー〔ユーザー・外部 bot〕への対応、ユーザーの指示での修正、main の取り込みを含む）：巡の sha から今の tip までで変わったファイル（`git diff --name-only <巡の sha>..HEAD`）に、「判定のコード」が 1 つでも入っていたら、その巡は無効になる。規則の文書・テスト・`changelog.d/`・`review-log/`・その他の文書だけを変える commit は、巡を無効にしない。ただし、テストを削除する、または assert を緩める変更は例外で、上のパスの区分のとおり巡を無効にする
     - 無効になったら、全差分をもう 1 回回さない。差分巡（base は巡の sha。reviewer 列には範囲を「差分（無効化後）」と書き、通常の差分巡と区別する）を 1 回回して high=0・blocking=0 を確かめる。high・blocking が無ければ、その巡を最後の独立レビューとする（終了条件の 1・2 つ目を満たしたものとし、3 つ目の CI は手順 7 のとおり確かめる）。差分巡で high・blocking が出たら、直して差分巡をもう 1 回回す（巡が無効になるたびに、差分巡は 2 回まで）。その 2 回目の後も high・blocking が残ったら、上の行き詰まりとして再設計に進む
     - main の取り込みで無効になったときは、差分巡の base を巡の sha にしない。その範囲には、main で審査済みの他の PR の変更が入る。その行への指摘が ① に入り、他の PR の変更をこの PR で直すことになる。代わりに、新しい merge-base からの全差分（`git diff $(git merge-base origin/main HEAD)..HEAD -- . ':(exclude)review-log/'`）を材料にし、reviewer 列の範囲は「全差分（無効化後）」と書く。回数の上限と、出た指摘の扱いは、上の差分巡と同じにする
     - 取り込みの後の全差分の変更行（`+`・`-` の行）が、無効になった巡の時点の全差分（その時点の merge-base から巡の sha まで）の変更行と同じなら、巡を回し直さない（取り込みで変わったのは、この PR が触らない行だけである）。突き合わせのコマンドと結果を `review-log/<slug>.notes.md` に書く
7. push は 1 回にまとめて PR を作る。マージはユーザーが行う
   - push 前の順序は「変更断片の確定 → ローカルの確認（関係するテストと `validate-plugin.sh`）→ 最後の独立レビュー（手順 6 の「巡の終わり方」）→ push → CI が success（merge-ready）」。`review-log/` への追記は各巡の直後にその都度行い、最終 push の 1 commit にまとめて含めてよい
   - PR 本文は push のときに 1 回だけ書き、巡ごと・commit ごとに更新しない。`plain-writing:writing-for-readers` で書き、型は同 skill の PR description（テンプレートが無いとき）に従う。この規則でいう目的・変更内容・限界は、その型の「なぜ変えるか」「挙動の変化」「やっていないこと・残した問題」を指す。この repo で足すのは次だけである
     - 目的：前の PR の語は、初めて出るところで中身を添える
     - 限界：マージの後も残る不利益と、まだ決まっていないこと（返事待ちの問い、直していない常時 High・実害クラス）だけを、どの巡で出たかではなく変更の性質として書く。行の先頭に種類（`common-guardrails.md` § Honest Limitations）を書く。決着した確認は、決めたことを 1 文で書く
     - レビュー結果：「確認したこと」の最後に `独立レビュー: <巡>（<sha>）high <n>・blocking <n>。指摘の全件は review-log/<slug>.md` の 1 行（L0 は `独立レビュー: なし（L0）`）を書く。`unavailable` の行（`AGENTS.md` の「Claude Code 以外で読むとき」・安全策 1）はこの行の下に書く
     - `next-pr` があれば、最後に「次の PR:」のラベルで列挙する
     - 工程の記録は書かない。受け入れた medium・low と advisory は `review-log/<slug>.md` の `## 指摘` に残す。表にならない記録（`Skill RED-GREEN Evidence` など）は、あるときだけ `review-log/<slug>.notes.md` を作り、記録ごとに `## <名前>` の見出しの下に書く
   - PR 作成後に commit を積むとき（PR 上のレビューへの対応など）は、届いている指摘をまとめて直し、手順 6 の「最後の独立レビューの後に commit を積んだとき」に従う。順序は「修正 → 差分巡 → push 1 回 → PR 本文を 1 回だけ更新（レビュー結果の行の書き換え）」。push 先は PR の head（`git push origin HEAD:<head>`）。`review-log/` だけを変える commit（`pr:` の記入を含む）と PR 本文の更新は、巡を無効にしない
   - push の後は `gh pr checks <PR>` で `gdd-plugin` が success になるまで確かめる（CI が赤でも GitHub はマージを止めない）
   - `gdd-plugin` の job が始まらなかったとき（`gh run view <run> --json jobs` で steps が 0。課金の上限など）は、差分のせいにせず commit も積まない。tip で `plugin-lint.yml` のテストの step をすべてローカルで回し、コマンド・件数・tip の sha と「CI 未起動」をユーザーに報告する。これを終了条件の 3 つ目の代わりにする
   - CI が赤のとき、原因が差分の中なら修正 commit を積む（判定のコードを変えるなら、手順 6 のとおり巡が無効になる）。原因が差分の外（main 由来）なら、差分に入れない。main を直す別 PR に回し、main が直った後に、ユーザーの指示で main を取り込む
   - PR 作成後、`review-log/<slug>.md` の front matter `pr:` を埋める。埋め忘れたら PR 本文で開示する

### review-log の巡の名前

- `独立-N`：手順 6 の独立レビュー。PR の作成の前か後かを問わない
- `codex-N`：手順 5 の Codex
- `PR後-N`：PR 上で受けた外部のレビュー（ユーザー、GitHub 上のレビュー bot など）。PR 作成後に回した独立レビュー・Codex は、それぞれ `独立-N`・`codex-N` にする
- `方針メモ` / `方針メモ-N`：L1+ 安全策 1 の、Opus 2 本への相談とユーザーへの確認。reviewer 列は `Opus 設計レビュー ×<呼べた本数> (<agent>, model: opus) + user`。手順 6 の `閉じ方: 列挙` と再設計の相談も `方針メモ-N` にする。ユーザーへの確認を含まないので、reviewer 列は `+ user` を除いて書く（再設計は先頭に `再設計, ` を足す）。2 本とも呼べなかったら、main が (a)〜(c) の既定どおりに決め、`Opus 設計レビュー: unavailable（理由）` と書く

### 指摘を直すとき

- high・blocking を直す commit の前に、設計に戻る。その種類の穴を生んだ設計の決定を 1 つ挙げ、その種類ごと消す設計の変更があるかを確かめる。あれば、指摘の形だけを塞ぐ修正より先にそれを採る（L1+ では、方針メモ-N で Opus 2 本に並べて聞く）。`## 指摘` の要約の先頭に `設計: 変える（<決定>）` か `設計: 変えない（<理由>）` と書く
- 実害の指摘（`reviewer-common.md` の常時 High か実害クラスに当たるもの）は、指摘を再現するテストを先に書き、失敗を確認してから直す。そのテストは残す（後の変更で修正が消えたら、テストが落ちるようにする）
- 直す前に、変える部品を使う側と、同じ入力を読む別の実装を列挙する。対になる片方だけを直さない
- 修正の commit に、簡素化・スコープの縮小・別の変更を混ぜない
- block / allow の判定を変える修正（分岐の追加、述語の拡張、入力の正規化の変更を含む）では、下の「L1+ で足す安全策」2 の fail-open の 3 ケースのテストを書く

### L1+ で足す安全策

1. 実装の前に、方針メモをユーザーに 1 回だけ確認する。順序は次のとおり
   1. 事実を実測する（対象部品を使う側、その入力を誰が作るか、実データでの件数）
   2. Opus に 2 本並行で設計レビューを依頼する。Agent は `subagent_type: spec-autopilot:opus-advisor`（`plugins/spec-autopilot/agents/opus-advisor.md`。model と effort は定義で固定し、`model` は渡さない）で、同じ材料を渡して 2 本を並行に起動する。呼べない本があるとき（再試行は 1 回まで）は、ユーザーへの確認（再設計では方針メモ-N の記録）の本文と PR 本文に、呼べなかった本を `Opus-2 設計レビュー: unavailable（理由）` の形で（2 本とも呼べなければ番号を除いて）書いて次へ進む。材料は要約ではなく場所で渡す。実装前なので差分の代わりに、変更案（触るファイルと箇所）・実コード・関連する review-log の場所を渡す。方針メモの草案（下の 8 点）も一緒に渡す。問いは「そもそもどうあるべきか、どうするのがいいのか」から始める
      - `opus-advisor`（high）の推奨と main の案が食い違っても、max（`gdd-opus-advisor-max`）に相談し直さない。並行で聞いたもう 1 本の推奨と並べて確認に載せる
   3. ユーザーに確認する。2 本の推奨、2 本が割れた点、メインの案との食い違いを載せる（割れた点の扱いは、全レーン共通の確認の前の相談と同じ）。返事の待ち方も、全レーン共通の確認の前の相談の行に従う
   - 確認は短い質問か 1 通のメッセージで行う。要件レビューや human check のテンプレートは使わない
   - ユーザーから指摘や修正が出たら、`方針メモ` 巡として `review-log/<slug>.md` に追記する（書式の正本: `review-log/README.md`）
   - 方針メモには次の 8 点を書く
     - 何を変え、何を変えないか
     - 各 AC がどう閉じるか（列挙した入力集合か、計測コマンドと合否基準か）
     - 閉じない残りをどこまで受け入れるか。受け入れた限界は PR 本文に書く
     - 同じ入力空間を閉じる範囲で広い側と狭い側が候補にあるとき、**既定は広い側**にする。狭い側を既定にするのは、**ユーザーが狭めると決めたときだけ**にする（基準 1 の正本は `common-guardrails.md`）。実装コストや実測件数の数値は案の説明に書くだけにする。「別の設計判断が混ざる」「正本の置き場を決める必要がある」「判断が増える」は狭める理由にしない。**境界**: 広い側の既定は「同じ入力空間を閉じる」範囲に限る。別の AC・別のファイル群・別の機能への拡張を既定にはしない
     - 延期・削除する完了条件と、その結果どこが開いたまま残るか
     - QA の合否基準（何を測って、どの値なら OK か）。測れないものはその旨
     - 新しく作る部品の配線（書く側・読む側・入口からの到達経路・同じ入力を読む既存の実装）
     - 該当する過去の教訓（memory）と、それにどう従うか
2. fail-open 側のテストを先に書く。書くケースは次の 3 つ
   - block すべき入力が allow になる
   - 例外で guard 全体が落ちる
   - 判定できないときに通ってしまう
3. 独立レビューでは、必ず次の 3 つの観点を見る
   - `independent-review.md` の (g)：例外で guard 全体が落ちる経路
   - `independent-review.md` の (h)：受理集合の対称性
   - security の観点：信頼境界と fail-closed
4. 次のどちらかに当たったら、手順 6 の行き詰まりとして再設計に進む。同じ `review-log/<slug>.md` の `## 巡` の行のうち、`独立-N`・`codex-N`・`PR後-N` を、PR の作成の前後を問わずに数える（巡の名前は上の「review-log の巡の名前」。開いた入力を扱っている兆候である）
   - 同じ種類（クラスタ）の high を含む巡が 2 回になった
   - クラスタを問わず、high を含む巡か `blocking` が 1 以上の巡が合計 3 回になった
   - `## 巡` の high・blocking の列で数える。`re-reported`・`next-pr`・`out-of-diff` の指摘は、手順 6 のとおり high に入らない。これらは実害クラスにできない（手順 6）ので、blocking にも入らない
   - `方針メモ` / `方針メモ-N` の行は数えない。これは相談の記録で、そこで相談役が挙げた high を数えると、再設計の直後にまた発火する
   - `## 指摘` で `対応` が `accepted` で、severity が high か `実害` が yes の行（受け入れた指摘）を `accepted` にした後に記録した巡では、受け入れた指摘のどれかと同じクラスタ（`## 指摘` のクラスタ列）にある指摘のうち、`自己起因` が `inherited` のものを数えない。`自己起因` が `self-inflicted` のもの（この PR の変更が生んだもの。付け方は手順 6 の review-log の項）は、同じクラスタでも数える。安全策 4 の数えは、巡を記録した時点の `## 指摘` で決める。後で `対応` を `accepted` に変えても、記録済みの巡の数えは戻さない。数えから外した後に、その巡に high も `実害` が yes の指摘も残らなければ、その巡は high を含む巡にも `blocking` が 1 以上の巡にも数えない（指摘ごとの blocking は `実害` 列で読む）。数えから外す根拠は、`## 指摘` の宣言した列（severity・実害・自己起因・クラスタ・対応）と巡の順序だけで、方針メモの reviewer 列と要約は読まない。`## 巡` の high・blocking の列は変えないので、merge-ready の条件は変わらない
   - 数え方（どの巡を数えるか、同じ指摘か）に迷ったら、発火したものとして再設計に進む
   - Opus は材料と推奨を出すだけで、安全策 4 を解除しない。再設計の上限でユーザーに戻した後は、返事が来るまで修正を続けない

## 全レーン共通

- medium・advisory・low は既定でこの PR では直さない（行き先は手順 6 の ①〜③）。取り込むのは、ユーザーが指示した場合だけである（軽いレーンでは、取り込む commit が「判定のコード」を含むなら、その時点までの巡を無効にする。最後の独立レビューより前ならそのまま次の巡で扱い、後なら手順 6 の「最後の独立レビューの後に commit を積んだとき」に従う）。① で `accepted` にした、blocking でない medium・low と advisory を直す PR は、マージの報告・次の計画・セッションの候補で申し出ず、件数と review-log の場所だけを書く。作るのはユーザーが PR 番号を挙げて頼んだときだけで、残りを 1 本にまとめる
- PR 上の外部レビュー（`PR後-N`。ユーザー、GitHub 上のレビュー bot など）の指摘の severity は、`plugins/gate-driven-development/skills/pr-review-followup/SKILL.md` の手順 2 Classify のとおりに分ける（`reviewer-common.md` § 常時 High の 4 型と適用範囲、範囲外の上限、4 型に当たるかを判定できないときと、確かめた後に戻すときの扱い。ここには書き写さない）。そこで High になったものは、reviewer が付けた severity によらず、後続 PR に回さずこの PR で直し、`## 巡` の high にも数える
- ユーザーに案を選んでもらう確認（AskUserQuestion や、選択肢を挙げて返事を待つ発言）を出す前に、`spec-autopilot:opus-advisor` に、同じ材料を場所で渡して並行に 2 本相談し、2 本の推奨と、割れた点と、main の案との食い違いを確認の本文に載せる（確認の文面は `plugins/gate-driven-development/references/human-check-template.md` § 判断の書き方 に従う。1 つの確認に 1 組。相談ごとの観点や前回の推奨は足さない。割れた点は main が repo の事実を確かめてから推す側を決め、決めきれなければ両方を載せる。安全策 1 と再設計の設計レビューをすでに済ませた確認は、その 2 本の推奨を載せればよい）。推奨は材料で、決めるのはユーザーである。確認では、返事を待つ tool（AskUserQuestion など）を使わない。本文に問い・推奨の案・違う案を選んだときに戻す範囲を書き、推奨の案で作業を続ける。返事が無いうちは merge-ready と報告せず、マージもしない。返事が来たら、その発言を（あれば `review-log/<slug>.request.md` に時刻つきで）記録し、推奨と違う案なら戻す。推奨で進める確認では、相談役に依頼の原文（あれば `.request.md`）も渡す。次のときだけは、今までどおり返事を待つ
  - global の `CLAUDE.md`・`AGENTS.md` が 1 操作ごとに明示の確認を求める操作（マージ・release・Issue の close・デプロイ・`terraform apply`・クラウドへの書き込み・破壊的な削除・共有 DB の変更・docker push など。自走上限で認めた例外はそのまま）
  - ブランチを経ずにすぐ効くもの（settings・memory・root checkout の pull・local の hooks・他のセッションの state ファイル）
  - 答えをユーザーしか持たない事実を問うもの（推奨が推測にしかならないもの）
  - 依頼の機能が実装できる見込みが無いとき
  - 相談役が、人に止めて聞くべきと答えたとき
- main が案・既定・推奨を作るとき、依頼や承認した範囲の一部を対象外にする・狭い側を既定や推奨にする・合格条件や指標を替える・後回し（後続 PR・延期）にする、の 4 つは黙って決めない。扱いは plugin の `plugins/gate-driven-development/references/common-guardrails.md` § scope の勝手な拡大・縮小 に従う（軽いレーンと、PR を作る前の判断にも当てる）
- Fable には、次の信号のどれかが出たときだけ、ユーザーに聞かずにアドバイザリとして 1 回相談する（1 PR あたり 1 回まで）。信号は観測できるものに限り、main の確信度の自己申告では呼ばない（自己申告は甘くなりやすく、呼ぶ回数が読めない）
  - ① main の案と、Opus（並行の 2 本ならどちらか 1 本）の推奨が食い違った
  - ② 再設計の上限に当たり、ユーザーに戻す前（手順 6 の再設計）
  - ③ 取り消しにくい操作（マージ・デプロイ・ルールの変更）を決める根拠が、コマンドの出力などの実測ではなく推測だけである
  - Fable の役は、欠陥を先に見つけることではなく、ユーザーならどちらを選ぶかの代わりである
  - 呼んだら、どの信号で呼んだかと Fable の推奨、採ったかどうかを `review-log/<slug>.notes.md` の `## Fable への相談` に 1 行書く。Opus の推奨（並行の 2 本なら、Fable と食い違った側。2 本とも違えば両方）と食い違ったときは、その推奨と、ユーザーが選んだ案（ユーザーが選ばなかったときは `ユーザーの選択: なし`）も同じ行に書く（Fable とユーザーの一致を後から数えるため）。Fable の推奨は材料で、続行や採否を決めるのは今までどおり（安全策 4 の続行はユーザー）
  - 起動は `subagent_type: spec-autopilot:fable-advisor`（`plugins/spec-autopilot/agents/fable-advisor.md`。model と effort は定義で固定し、`model` は渡さない）で行う。ユーザーが「Fable に聞いて」と指示したときも同じにする
- PR レビュー対応では、指摘を 1 件ずつ push しない。届いている指摘をまとめて直してから、1 回だけ push する
- main の取り込みは、ユーザーの指示があったときに、マージ直前の 1 回だけ行う
- 実装中に見つけた別の問題は差分に入れず、再現手順を添えて後続課題にする
- PR をマージせずに閉じる前に（閉じることをユーザーに勧めるときも）、その PR の依頼（`review-log/<slug>.request.md`。無ければ PR のきっかけになったユーザーの発言）の項目ごとに、行き先を 1 つ挙げる。行き先は、main に入った commit、その項目を扱う別の PR、Issue のどれかである。別の PR を行き先にするときは、その PR の変更ファイル（`gh pr view <番号> --json files`）に、項目が求めるファイルが入っていることを確かめる。main に入っていない項目（行き先が別の PR・Issue のものを含む）が残るなら、閉じる前にユーザーに示す。行き先の無い項目があるときは、ユーザーの返事を待ってから閉じる。行き先は、閉じるときの PR のコメントに書く（PR を閉じる依頼は、このコメントの投稿を含むものとする）
- 後続 PR の連鎖（`follow_up_of:` でたどる PR）の 3 本目をマージしたら、4 本目を作る前に、連鎖の最初の依頼の原文に照らして、残りを 1 本にまとめるかをユーザーに問う。連鎖が終わるとき（`follow_up_of:` のある PR をマージし、その PR 本文に「次の PR」が無いとき）も、連鎖の最初の依頼（`.request.md` の最初の「この PR が扱う行」より上の部分）の項目ごとに、同じように行き先を 1 つ挙げ、マージの報告に書く（ユーザーがマージしたときは、マージの報告を受けた直後の応答に書く）。main に入っていない項目と、依頼に無い方向へ広がった PR があれば、ユーザーに示す
- 新しい発火条件（押し返し・判断役への相談・lint・route の分岐など、条件に当たったときだけ動く仕組み）を、PR の目的として、またはレビューの指摘を直すために足すときは、作る前に、既存の transcript・steering・review-log でその条件に当たる件数と、直したい損失のうちその条件で止まる分を測り、PR 本文に数を書く（目的として足すなら目的の節、指摘を直すために足すなら限界の節。コマンドは `review-log/<slug>.notes.md` に書き、実値は書かない。`plugins/gate-driven-development/references/self-review-lanes.md` の規律 C と同じ）。指摘を直すために deny（block）の分岐を足すときは、規律 C も当てる。当たる件数が 0、または直したい損失の主因に当たらないなら足さない。「測れない」のは、その条件が読む入力（agent の発言・tool の入力・steering の欄など）が既存の記録に残っていないときだけである。そのときは 0 件として扱わず、限界の節に「未測」と、どの入力が記録に残らないかを書く。未測のまま足すのは、ユーザーが確かめたときだけで、その発言を `review-log/<slug>.request.md` に足す。
- GDD の改善の案の採否は、少数件の再生実験の合格線で決めない。入れる前に、読む時期と撤去する条件を PR 本文に書き、その時期に本番の記録（問い直しの数、間違った枠で失った量、`request-diff.log` の行）を読んで決める。再生は、1 つの変更が受け入れていた形を壊さないかを安く確かめるときだけ使う。前提を挙げた問いは、返事が無いときに狭い側で確定しないなら、狭い提案に数えない
- root `CLAUDE.md` に規則を足す PR は、足した分と同じ量を `CLAUDE.md` から消す。字数の目標は置かず、検査も足さない
- 1 PR 1 課題にする。追加が +1,000 行を超えそうなら、先に分割をユーザーに相談する
- `hooks.json`・`validate-plugin.sh`・review-log の契約・root `CLAUDE.md` を触る PR は、open のものがある間は次を作らない
- 後回しにする指摘の行き先は、手順 6 の ①〜③ で決める。high・medium を一律に Issue にしない
  - ② と、実データに該当があった ③ と、ユーザーの指示で次の PR にした ① は、PR 本文の「次の PR」に列挙し、この PR の直後に次の PR として直す。Issue で寝かせない
  - Issue を作るのは、次の PR にすぐ取りかかれないとき（ユーザーが後回しを指示したときなど）だけである。`対応` は `deferred` にし、本文に PR 番号・review-log の id と、「いつ直すか」の条件を 1 行書く
- 開いている Issue が 20 件を超えたら、次の改善 PR より先に棚卸しをする。1 件ずつ、直す・閉じる・残すの案を作り、ユーザーに確認して決める。残すものには「いつ直すか」の条件を 1 行書く。件数は `gh issue list --state open --limit 500 --json number --jq length` で数える
- 2 週間誰も触っておらず（`updatedAt` が 14 日より前）、「いつ直すか」の条件も書かれていない Issue は、対応不要として閉じる候補にする。候補の一覧をユーザーに出し（週次の報告に載せてよい）、承認を得てから閉じる（`gh issue close <n> --reason "not planned"`。必要になったら開き直す）。Issue の close は、依頼なしに行わない
- 週に 1 回、その週に作った Issue の数・直して閉じた数（`stateReason` が `COMPLETED`）・対応不要で閉じた数（同 `NOT_PLANNED`）をユーザーに報告する
- 動いているセッションが使う GDD は、ルート checkout（main）へのシンボリックリンクで決まる。main を pull した時点で、全セッションのルールが切り替わる
- マージの報告を受けたセッションは、root checkout を pull する。`hooks.json` を変えた PR の後は、長く動いているセッションを開き直す

## テスト

`plugins/gate-driven-development/references/testing-anti-patterns.md` § テスト判定基準は、対象 repo の `CLAUDE.md` のテストの節を正とする。この repo では、次の点を本節で決める。

- 文書（skill・reference・agent 定義・`CLAUDE.md` など）に語・文があるか（無いか）だけを assert するテストは、書かない・残さない。クラス E の、規範文を行と動詞まで含めて見るテストも含む
- コードが読む値・集合・シンボルと文書を突き合わせるテスト（クラス A・D）は残す
- 文書だけを変える変更では、手順 2 と「指摘を直すとき」が求める、先に書くテストを求めない。skill 本文・prompt・reviewer policy・HITL 出力契約を変えたときは、手順 3 の `Skill RED-GREEN Evidence` で代える
- 1 点目・2 点目でいうテストは `tests/test_*.py` を指す。`tests/checks/*.sh` の文言の検査は対象外で、扱いは別に決める。3 点目は、`tests/checks/*.sh` も含めて先に書くテストを求めない
