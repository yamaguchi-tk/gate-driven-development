---
lane: L1+
pr: 236
follow_up_of: 232
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) | a424a7c1065a9adc36ddbca8b8e6d1b8e28eb4df | 0 | 0 | 0 | 2026-09-29T08:59+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 874ee99536b61e7edbf2440dce1821558018546e | 5 | 0 | 5 | 2026-09-29T10:20+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) | 874ee99536b61e7edbf2440dce1821558018546e | 0 | 0 | 0 | 2026-09-29T10:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 715a97d97bfd2cf0b9a05a0f40252268d3909e76 | 7 | 0 | 7 | 2026-09-29T11:29+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) | 715a97d97bfd2cf0b9a05a0f40252268d3909e76 | 0 | 0 | 0 | 2026-09-29T11:29+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 060fae26ea77d729b44d859aefa1bac21cbad8f1 | 4 | 0 | 4 | 2026-09-29T12:31+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | merge-target-grammar | accepted | 方針: gh の flag の表（`pr merge` の値を取る flag・値を取らない flag・継承の `-R`・`--help`/`-h`）と pflag の規則（束ね・密着値・`=`・`--` 以降は位置引数）で、`gh` の後の全 token を読む。表に無い flag・位置引数 2 つ以上は unresolvable を立てるが、読めた URL と番号は消さない。番号は ASCII の数字に限る。台帳の経路は URL と番号の両方で照合し、hit を unknown より優先する。本体の経路の URL の形は、記録の番号と URL の番号で照合し（番号の形と同じ）、repo の違いは 3 組解決の (d) に任せる。Opus の推奨（unresolvable を増やす方向は台帳の git-cwd の経路で新しく通る形になる、repo の比較は番号の形と非対称）をメインの草案に代えて採用した。メインと Opus の食い違いは残らず、Fable は使わない。gh の cobra の探索規則・`MaximumNArgs(1)` は実行では未確認 |
| H1 | 独立-1 | high | yes | inherited | sub-command-find | fixed | sub-command の探し方が gh（cobra の `stripFlags`）と違い、gh が merge を実行する `gh pr -st merge fix 7`・`gh pr -s -- merge 7`・`gh pr --admin -- merge 7`・`gh -s -t pr merge 7` を merge と読まず、承認の証跡を見ずに通していた。sub-command を cobra の規則（2 文字の短い flag と `=` の無い長い flag は次を値として飛ばす、束ねと `=` は飛ばさない、`--` で止まる）で探し、`pr` と `merge` を除いた全 token を merge の表で読む形にした。飛ばした token が探している名前なら、見つけたものとして unresolvable を立てる。gh の探索規則は `--help` を付けた実行で確かめた。commit: 4dcce27c |
| H2 | 独立-1 | high | yes | inherited | unresolvable-number | fixed | 対象を決められない merge（位置引数 2 つ以上・知らない flag など）が、読めた番号が steering の PR と違うと「別 PR の merge」として本体の経路で通っていた（`gh pr merge 42 --squash` の後に改行で続く別のコマンドの引数を位置引数に読む形など）。本体の経路で、unresolvable のときは番号・URL を空にして、対象を省いた merge と同じ経路に載せ `pr-target-unresolvable` で止める形にした。flag の値の位置のリダイレクトも argv から除いて読む。commit: 4dcce27c |
| H3 | 独立-1 | high | yes | inherited | number-url-accept | fixed | 番号・URL の受理が gh より狭く（`+7`・`'#7'`・`…/pull/7/`・`…/pull/7/files`・`http://`・先頭の 0 を branch と読み）、台帳の経路で台帳の PR の merge が unknown として通っていた。gh が読む形（`#` を落とした Atoi、`^/o/r/pull/(\d+)` の前方一致、http・https、host は大小文字を区別しない github.com）を読み、正準形にして照合する。commit: 4dcce27c |
| H4 | 独立-1 | high | yes | inherited | pre-pr-sub-command | accepted | pre-PR gate が `gh pr -R acme/widgets create`・`gh pr --repo=acme/widgets create`・`gh pr -Racme/widgets create` を PR の作成と読まず（入口の語の並びの絞りも通らず）、Pre-PR Self Review の証跡なしに通す。入口の絞りと `-R` の綴りの読みを直したが、open の 旧#234 が `run-pre-pr-gate-hook.sh` の同じ範囲（入口の絞り）を書き換えていて衝突するので、この PR から pre-PR gate の変更を外した（独立-2 の H-5・H-6 と合わせて、旧#234 のマージ後に merge gate の探索を共有する次の PR で直す）。main から残る常時 High。PR 本文の限界の節の先頭に書く |
| H5 | 独立-1 | high | yes | self-inflicted | parse-cost | fixed | `_read_merge_flag` が短い flag の束ねを 1 文字ごとに token を切り出して読み、長い束ねで解析時間が 2 乗になった（hook の timeout を超えると block を返せない）。切り出しを値が要るときの 1 回だけにして線形にした。速度は 40 万文字で 3.2 秒から 0.1 秒未満へ。commit: 4dcce27c |
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片・抜粋の「止める」が、本体の経路の出口（番号が違えば通す）と合っていなかった。H2 で実装を記述に合わせた。commit: 4dcce27c |
| L2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「ASCII の数字だけが番号」が gh の実装（先頭の `#`・`+` も受ける）と合わなかった。受理と記述を直した。commit: 4dcce27c |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | パーサの module docstring の「pre-PR gate と同型」が成り立たなくなった。実態（別の実装）に直した。commit: 4dcce27c |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 台帳の判定の順序のコメントが `hit > unreadable > miss` のままだった。unknown を足した。commit: 4dcce27c |
| L5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 件名の 7 を対象と読む誤りに戻っても落ちない hook の入口のテスト。記録が 旧#9 のときに `-st 7 <branch>` が止まるテストを足した。commit: 4dcce27c |
| L6 | 独立-1 | low | no | self-inflicted | test-power | fixed | 既存テストの入力が新しい文法で URL と番号の両方を位置引数に持つ形でなくなっていた。入力を `<URL#8> 7` に直した。commit: 4dcce27c |
| L7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 別の repo の同じ番号を URL で merge する形が新しく止まることが User Action Required に無かった。断片に出口を書いた。commit: 4dcce27c |
| A1 | 独立-1 | advisory | no | self-inflicted | product | accepted | URL の番号の取り出しが bash の `##` 展開のまま（パーサが番号を正準形にするので桁は短い）。PR 本文に書く |
| A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | 複数の merge があるとき `--admin=false` が前の merge の `--admin` を消す（判定は merges > 1 で止まるので変わらず、block 文から注意書きが落ちるだけ）。PR 本文に書く |
| A3 | 独立-1 | advisory | no | inherited | product | accepted | `gh api` の merge と gh の alias は、どの hook も検出しない（gate の宣言の範囲外）。PR 本文に書く |
| A4 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの一時ディレクトリを消していない（既存のテストと同じ書き方）。PR 本文に書く |
| P2 | 方針メモ-1 | advisory | no | inherited | sub-command-find | accepted | 独立-1 の high 5 件への対応方針（Opus の推奨を採用）。sub-command の探索と merge の表での読みは 1 系統にし、2 つの読みの突き合わせはしない。本体の経路の unresolvable は 1 箇所で番号・URL を空にする。改行を制御演算子の区切りにする変更（H2 の一部）は、同じ token 列を読む `_chdir_signals` などに効くので別の課題とし、限界に書く（台帳の経路で unknown を通す設計は変えない）。pre-PR gate は Opus が分けることを推奨したがメインは入口の絞りと `-R` の綴りだけを直した。その後 旧#234 と衝突すると分かり、独立-2 の後に外した（H4 を accepted にした）。pre-PR gate の cobra の探索の共有（`gh pr -s -- create` など）と、入力長の上限で timeout を parse-error に倒す変更は、限界として PR 本文に書く。Fable は使わない |
| H-1 | 独立-2 | high | yes | self-inflicted | sub-command-find | fixed | sub-command の探索が cobra と違い、`-`・空の token で見つからないとして止まり、`-=` を値を取る flag と読んだ。`gh pr -st - merge 7`・`gh -st '' pr merge 7`・`gh -st -= -R acme/widgets pr merge 7` は gh が merge するのに通していた（独立-1 の直しの前は検出していた形）。`-`・空の token は読み飛ばし、`=` を含む 2 文字の token は値を取らないと読む。commit: 986c91fb |
| H-2 | 独立-2 | high | yes | inherited | shell-expansion | accepted | sub-command の探索位置の token が `$VAR`・`$(…)` を含むと見つからないとして止まる（`gh $GH_OPTS pr merge 7`）。開いた入力（シェル展開はいくつの語にも展開される）で、main も同じ。PR 本文の限界の節の先頭に書く。次の PR の予定は無い |
| H-3 | 独立-2 | high | yes | self-inflicted | parse-cost | fixed | `_find_gh_pr_merge` が gh の token ごとに sub-command の探索を末尾まで歩かせ、`gh -s gh -s … ; gh pr merge 7` で 2 乗（3000 組で 6.0 秒、main は 0.04 秒。hook の timeout は 10 秒）。探索の結果を位置ごとにメモ化して線形にした（メモは `_find_gh_pr_merge` の 1 回の呼び出しごとに作り、結果を書く呼び出しには渡さない）。commit: 986c91fb |
| H-4 | 独立-2 | high | yes | inherited | parse-cost | fixed | `_env_short_option_step` に、`_read_merge_flag` で直したのと同じ 1 文字ごとの切り出しが残り、`env -vvv…(30 万文字) gh pr merge 7` で 5.7 秒（main も同じ）。値が要るときの 1 回だけ切り出す形にした。commit: 986c91fb |
| H-5 | 独立-2 | high | yes | inherited | pre-pr-sub-command | accepted | pre-PR gate の入口の絞り `*"pr "*"create"*` が、引用した `gh "pr" create` に当たらず python が動かず通る。open の 旧#234 が入口の絞りを 1 語の照合に書き換えて閉じる。この PR は pre-PR gate を変えない。PR 本文の限界の節の先頭に書く |
| H-6 | 独立-2 | high | yes | inherited | pre-pr-sub-command | accepted | pre-PR gate の sub-command の探索が `-R` 系以外の flag を読まない（`gh pr --title t create`・`gh -t t pr create`）。旧#234 のマージ後に、merge gate の探索を共有する次の PR で直す。PR 本文の限界の節の先頭に書く |
| H-7 | 独立-2 | high | yes | inherited | number-url-accept | accepted | URL の `%xx` を gh は復号し `www.github.com` も github.com とみなすが、パーサは復号せず `www.` は branch と読む。台帳の経路の root 未解決で `https://github.com/acme/infra-gd%64/pull/7` が miss で通る（本体の経路は (d) で止まる）。gh の URL の読み方を実行で確かめたうえで、次の PR で直す。PR 本文の限界の節の先頭に書く |
| L-1 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片・抜粋・コメントが「3 経路とも `pr-target-unresolvable`」と書くが、multiple と候補 0 件の経路は `steering-ambiguous`。断片とコメントを実際の出口に直した。commit: 986c91fb |
| L-2 | 独立-2 | low | no | self-inflicted | product | fixed | 新しく止まる形（知らない flag・余分な位置引数・改行で続く別のコマンド）の回避が断片に無い。User Action Required に、1 回の呼び出しに merge を 1 つずつ実行する回避を書いた。block 文面の変更は限界として PR 本文に書く。commit: 986c91fb |
| L-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `merge-gate-evidence.sh` のコメントが記録の PR URL の値ドメインを「`PR_URL_RE` と同一形」と書くが、前方一致の形に変わって同一ではない。follow_up_of の PR の 2 巡目の low なので限界として PR 本文に書く |
| L-4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 既存テストの名前が入力の変更と合わず、assert が block だけで hook の変更を固定しない。follow_up_of の PR の 2 巡目の low なので限界として PR 本文に書く（hook の変更は MainPathUrlFormTests の `pr-target-unresolvable` の assert が固定している） |
| L-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の Validation が、パーサの単体テストも「hook の入口から」と書いていた。単体テストと hook の入口のテストを分けて書いた。commit: 986c91fb |
| A-1 | 独立-2 | advisory | no | self-inflicted | test-power | fixed | 解析時間のテストが比で判定し、並列実行の負荷で揺れうる。数秒〜十数秒かかる大きさの入力を 1 秒未満で終えることを確かめる形（大きな余裕の絶対値）に直した。commit: 986c91fb |
| A-2 | 独立-2 | advisory | no | self-inflicted | style | accepted | `FIND_BOOL_LONG_FLAGS` の key が探す名前で、コメントの階層名と読み違えやすい。PR 本文に書く |
| A-3 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | pre-PR gate の読み飛ばしが `-R` の綴り以外も飛ばす。pre-PR gate の変更を外したので該当しなくなった |
| A-4 | 独立-2 | advisory | no | inherited | product | accepted | `PR_NUMBER_RE` に桁数の上限が無い（gh は int64 を超えると branch と読む）。GDD の PR に届く入力は示せない。PR 本文に書く |
| P3 | 方針メモ-2 | advisory | no | inherited | sub-command-find | accepted | 安全策 4 の発火（独立-1・独立-2 とも high を含み、同じクラスタが 2 回）。Opus の推奨を採用した。この PR で直すのは、この差分が入れた退行 H-1・H-3 と、同じ型の別実装 H-4 だけ。前からある H-2（開いた入力）・H-5（旧#234 が閉じる）・H-6・H-7 は accepted にして次の PR に回す。H-3 は探索のメモ化（Opus が試作で 3000 組 6.84 秒から 0.05 秒、604 本で出力の差 0 件）。独立-3 で打ち切る（続行は H-1・H-3・H-4 と独立-3 まで。独立-3 の high のうち、その修正 commit 自身が入れた退行だけ直し、残りは限界に書いて止める）。旧#234 が同じ pre-PR gate の範囲を変えているので、この PR から pre-PR gate の変更を外した。Fable は使わない |
| F1 | 独立-3 | high | yes | inherited | pre-pr-sub-command | accepted | pre-PR gate が `pr` と `create` の間に flag がある PR の作成（`gh pr -R acme/widgets create`・`gh -Racme/widgets pr create` など）を読まず、Pre-PR Self Review の証跡なしに通す（入口の語の並びの絞りも通らない）。open の 旧#234 と同じ範囲なので、この PR から pre-PR gate の変更を外した（H4・H-5・H-6 と同じ。方針メモ-2 で決めた）。main から残る常時 High。PR 本文の限界の節の先頭に書き、旧#234 のマージ後に、merge gate の探索を共有する次の PR で直す |
| F2 | 独立-3 | high | yes | inherited | parse-cost | accepted | 解析時間が 2 乗に延びる型が、`env -u env -u env … gh pr merge 7` の連なり（`_env_split_string_body` を値の位置の `env` ごとに呼ぶ）と、interpreter 名の連なり（`_shell_c_operand`）に残る。攻撃的に組んだ入力に限られ、main も同じ。`eval` の連なりは CHANGELOG.md に開示済み。走査予算の上限化（超過を unresolvable に倒す）を次の PR で直す。PR 本文の限界の節の先頭に書く |
| F3 | 独立-3 | high | yes | inherited | parse-cost | accepted | pre-PR gate の `skip_gh_global_flags` が gh の token ごとに歩き、`echo -R a/gh … ; gh pr create` で 2 乗になりうる。攻撃的に組んだ入力に限られる。pre-PR gate の変更を外したので、旧#234 のマージ後の次の PR で直す。PR 本文の限界の節の先頭に書く |
| F4 | 独立-3 | high | yes | inherited | pre-pr-fail-open | accepted | pre-PR gate の inline python が 0 以外で終わると、PR の作成を検査せずに通す（`COMMAND_INFO=$(…)` の代入に失敗時の続行が無く、`set -e` で hook が落ちる。merge gate は番兵で見分けて GDD の管轄内では止める）。差分とは無関係。別の PR で直す。PR 本文の限界の節の先頭に書く |
| F5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋の reason code の記述が、断片・コメント・実装と食い違う。PR 本文を経路ごとの出口に直す。commit: なし（PR 本文） |
| F6 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の「候補 0 件の経路は `steering-ambiguous`」「止まる」が一般化しすぎ（候補 0 件で PR URL の記録が無いときは通す）。条件を書いた。commit: 95868a13 |
| F7 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の「解析が 2 乗にならないようにした」が hook の入口では当たらない（tokenize が 1 つの長い token に対して 2 乗）。パーサの中の読み取りに絞って書いた。commit: 95868a13 |
| F8 | 独立-3 | low | no | self-inflicted | test-power | fixed | 断片が書いた reason code を固定するテストが無い。multiple の経路に `steering-ambiguous` の assert、候補 0 件（PR URL を記録した終端の steering）の経路に対象を決められない merge のテストを足した。commit: 95868a13 |
| F9 | 独立-3 | low | no | inherited | bookkeeping | fixed | 断片の Affected Files が変更したテストを載せていない。載せた。commit: 95868a13 |
| F10 | 独立-3 | advisory | no | self-inflicted | style | fixed | テストが同じコマンドを 2 回解析している。1 回にした。commit: 95868a13 |
| P4 | 独立-3 | advisory | no | inherited | sub-command-find | accepted | 安全策 4 の再発火（high を含む巡が 3 回）。方針メモ-2 で決めたとおり、独立-3 の high のうち、修正 commit 自身が入れた退行は 0 件（F1〜F4 は main 由来で、pre-PR gate の 3 件は 旧#234 と同じ範囲）。Opus への再相談はせず、残りを accepted にして止める。差分の本体（sub-command の探索の `-`・空 token・`-=`、探索のメモ化、env の束の線形化）に high は出ていない |
