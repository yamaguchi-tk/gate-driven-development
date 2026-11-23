---
lane: L1+
pr: 320
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（実装前の安全策 1。実測: ブランチを作るコマンド 5,398 件のうち、worktree のセッションから cd・git -C で root checkout に作るもの 37 件。Opus は、判定を実行先に置き換えず payload cwd を候補に残して実行先を足し、どれか 1 つで止める案と、決められない実行先は今どおり payload cwd で判定する案 B を推した。main の草案は案を絞っておらず食い違いは無い。案 B の根拠: 変数の 66 件のうち mktemp・一時ディレクトリ 43、worktree 7 で、案 A は約 50 件を新しく止める。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-02T23:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0956257758c84ce641d379c2359a27db58823b53 | 6 | 1 | 5 | 2026-10-03T00:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | da66b131 | 4 | 0 | 4 | 2026-10-03T00:50+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) + Fable (general-purpose, model: fable)（安全策 4 の発火: fail-open のクラスタの high が独立-1・独立-2 の 2 巡。実測: ブランチを作るコマンド 867 件のうち、2 つ以上の `-C` で決められない要素を含むもの 0、区切りと括弧がくっつく形 0、cd の glob 0。Opus・Fable とも案 A〔G1 だけ直し、G2〜G4 は限界、G4 は直後の PR〕を推し、食い違いは無い。memory の 2026-09-28 の決定〔設計変更は内部の相談で決める〕に従い、ユーザーへの確認は内部の相談で代えた。3 巡目で high が出たら、G1 の修正起因は 1 回だけ直し、fail-open の 0 件は accepted、それ以外は止める） | - | 0 | 0 | 0 | 2026-10-03T01:05+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 6e175ccc0ffb99294dd356d9d658a8f9ce66ec08 | 0 | 0 | 0 | 2026-10-03T01:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨: 候補を足す・payload cwd を残す・どれか 1 つで止める・`resolve_candidate_roots` は `git branch -C` を取り違えるので使わない・決められない行き先は案 B。そのまま採用） |
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | `then cd`・`{ cd`・`builtin cd`・`);cd` のように先頭にない `cd` を実行先にせず、active な root へのブランチ作成を通す。transcript（ブランチを作るコマンド 867 件）で先頭にない `cd` の行き先が字句で決まるものは 0 件（block guard は事故から守る、2026-10-02 の決定）。PR 本文の限界の先頭に書く |
| F2 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | サブシェル・`&`・パイプ・失敗した `cd` の後の相対 `cd` を、効いていない行き先を基点に解き、本当の行き先が候補から落ちる。transcript で該当する形は 0 件（正規表現の当たり 9 件はすべて変数・mktemp か誤検出）。docstring を実挙動に合わせた commit: ce85709e。PR 本文の限界の先頭に書く |
| F3 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | `-C` の引数の basename が `git` だと git の語を取り違え、`-C` を見落とす。transcript で 0 件。PR 本文の限界の先頭に書く |
| F4 | 独立-1 | high | no | self-inflicted | product | accepted | GDD 名のブランチの fallback を実行先に当てず、payload cwd と非対称。payload cwd が linked worktree で root に GDD 名のブランチを作る形は transcript で 0 件。repo でない行き先に当てると誤 block が出るため狭い側のまま。PR 本文の限界に書く |
| F5 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | 候補を重複除去せず `git rev-parse` が組数の 2 乗で増え、hook の timeout で素通りしうる。実データの最悪（サイト 8・cd 12）で hook 全体 0.30 秒、合成した 12 cd × 12 サイトで 1.34 秒（timeout 10 秒）。PR 本文の限界の先頭に書く |
| F6 | 独立-1 | high | yes | inherited | fail-open | accepted | 変数・コマンド置換で決まる行き先は判定しない。base と同じ挙動で、方針メモで案 B（変数の 66 件のうち一時ディレクトリ 43・worktree 7）を選んだ。PR 本文の限界の先頭に書く |
| F7 | 独立-1 | medium | no | self-inflicted | test-power | fixed | テストが linked worktree の例外と `git branch -C` の区別を固定していない。行き先の worktree にも active を書き、`git branch -C ../root copy` を allow 側に置いた（2 つの変異で落ちることを確かめた） commit: ce85709e |
| F8 | 独立-1 | low | no | self-inflicted | test-power | fixed | メッセージの assert が `command:` 行の絶対パスで必ず真になる。`cwd: <root>` の行を assert する commit: ce85709e |
| F9 | 独立-1 | low | no | self-inflicted | test-power | fixed | サブシェルのテストが `);` で区切られず意図を確かめていない。空白を入れ、コメントを実際の理由に直した commit: ce85709e |
| F10 | 独立-1 | low | no | self-inflicted | product | fixed | 後の `cd` で置き換わった前の `cd` も候補に残り、worktree の中のブランチ作成を止める。docstring に書き、PR 本文の限界に書く commit: ce85709e |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring と PR 本文が、サブシェル・`&`・パイプの `cd` の扱いを実装と違えて書いている。docstring を直し、PR 本文の限界を書き直す commit: ce85709e |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「payload cwd だけで判定」「先行する cd」が実装より広い。断片を直した commit: ce85709e |
| F13 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `_literal_path` の置換の判定が `_is_unexpanded_token` と違う。`_is_unexpanded_token` を使う commit: ce85709e |
| F14 | 独立-1 | low | no | self-inflicted | product | fixed | `~-` など展開できない `~` で RuntimeError になり、GDD を使っていない repo でも止める。行き先にしない（テストを先に書いて失敗を確かめた） commit: ce85709e |
| F15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | テストの docstring の測定日（2026-10-04）が実際の測定日と合わない（PR 本文に書く） |
| M2 | 方針メモ-1 | advisory | no | inherited | none | accepted | 要約: なし（Opus と Fable の推奨は案 A で一致。そのまま採用） |
| G1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 決められない `-C`（`~+`・`~-`・途中に置換を含む token）で `-C` の連鎖全体を捨て、`git -C ~+ -C <root> switch -c` を通す。`cd` と同じく飛ばして前の基点を保つ（テストを先に書いて失敗を確かめた） commit: 9dc5bfa5 |
| G2 | 独立-2 | high | yes | inherited | fail-open | accepted | `cd <root> &&(git checkout -b x)` のように区切りと括弧がくっつくと 1 セグメントになり、cd を見ない。transcript 0 件。PR 本文の限界の先頭に書く |
| G3 | 独立-2 | high | yes | inherited | fail-open | accepted | glob・CDPATH を literal のパスとして解き、存在しないパスは素通りする。transcript 0 件。PR 本文の限界の先頭に書く |
| G4 | 独立-2 | high | yes | inherited | fail-open | accepted | `extract_cwd` が main() の try の外で、`tool_input.cwd`/`workdir` が `~-`・NUL、dict でない payload、UTF-8 でない入力で exit 1（非 block）。入力を作るのは runtime で、Claude Code は cwd を載せず、Codex の workdir でも 0 件。except の cwd の組み替えが要るので直後の PR で直す。PR 本文の限界の先頭に書く |
| G5 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 置換を途中に含む token を行き先にしない変更を固定するテストが無い |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「payload cwd だけで判定する」が、変数の cd の後の相対 cd や `-C` も候補にする実挙動と合わない commit: なし（PR 本文） |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | `_cd_targets_before` の docstring が、決められない cd は基点を動かさず後の相対 cd を前の行き先で解くことを書いていない |
| G8 | 独立-2 | advisory | no | inherited | product | accepted | 候補の重複を除かない（実データの最悪で hook 全体 0.30 秒。PR 本文に書く） |
| G9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の 37 件と、判定が変わる 10 件の関係が書かれていない（PR 本文に書く） |
| G10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「展開できない `~`」の理由は `~+` には当たらない（Python で展開できない `~` を候補にしない、が正確。PR 本文に書く） |
| H1 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 決められない `-C` を飛ばすテストが、後ろを絶対パスにしていて「前の基点から解く」を固定していない（`or base` の変異が生き残る） |
| H2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | `root_branch_exec_targets` の docstring の「payload cwd を除く」が、決められない `-C` だけの連鎖で基点を返す挙動と合わない |
| H3 | 独立-3 | advisory | no | self-inflicted | product | accepted | `git -C -` を `cd -` と同じく決められない値として飛ばすが、git では `-` という名前のディレクトリ（PR 本文に書く） |
| H4 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 断片と PR 本文に、決められない `-C` を飛ばした結果（関係ない場所で止めうる）が書かれていない（PR 本文に書く） |
| H5 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: 起動時の git status の commit 件名に巡の番号と方針メモの経緯が入っていた。判断には使われていない |
