---
lane: L1+
pr: 333
follow_up_of: 320
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（実装前の安全策 1。実測: Claude Code は tool_input.cwd を載せない、Codex の session 488 本の workdir 146,629 件はすべて絶対パス。Opus は変更を要るとし、壊れた payload は allow〔コマンドを取り出せないので deny にすると git に関係ない Bash まで止まる〕、except の中で cwd が未束縛にならないよう先に束ねること、parser が無いときの分岐より前で cwd を解くことを足した。main の案と食い違いは無い。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T02:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1fec8e0cb02c45259274e47234c8c9beedb117a2 | 2 | 0 | 2 | 2026-10-03T02:40+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（独立-1 の high 2 件に `閉じ方: 列挙` が付いたため、修正の commit を積まずに相談した。Opus の推奨: X1〔壊れた payload の allow〕は、差分前も exit 1 で止めておらず、harness が作らず transcript 0 件なので accepted。reviewer の案は拒否する語を足す修正で閉じる修正に数えない。X2〔変数の行き先〕は 旧#320 の F6 で決めた案 B のまま accepted。low の止める範囲は `_GIT_WORD_RE` にそろえ、専用の文面にする。main の案と食い違いは無い。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T02:50+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 5ac45c9dcf1764a2361761b6077b694dabbe96a5 | 1 | 0 | 1 | 2026-10-03T03:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable (general-purpose, model: fable)（安全策 4 の発火: fail-open の high が独立-1・独立-2 の 2 巡。Y1 は敵対的な形〔引用符で割った git と囮の部分文字列〕で、囮の無い形は差分前から通る。Opus・Fable とも案 B〔作業ディレクトリを解けないとき、parser で root branch の作成か GDD 名の worktree add があるものだけを止める。parser の例外は止める。parser が無いときは `_GIT_WORD_RE`〕を推した。根拠は Y1 を閉じることではなく、except 分岐だけが本線より弱い判定を使う非対称と、worktree を消す事故で `git worktree prune` などの後始末まで止まる Y3。食い違いは無い。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T03:45+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 0967b936de3a220776416c5bae960f909508f7e5 | 5 | 1 | 5 | 2026-10-03T04:20+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 2b6acd887e06def34a369d6a5d437511dc697fa3 | 0 | 1 | 0 | 2026-10-03T05:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus の補足〔cwd を先に束ねる、parser 不在の分岐より前で解く、lone surrogate は `\ud800`〕をそのまま採用） |
| M2 | 方針メモ-1 | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨をそのまま採用） |
| X1 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | payload が JSON の object でない・UTF-8 として読めないときを明示的に allow し、テストで固定した。差分前も exit 1（PreToolUse の非 block）で止めていない。harness は作らず transcript 0 件（block guard は事故から守る）。PR 本文の限界の先頭に書く |
| X2 | 独立-1 | high | yes | inherited | fail-open | accepted | 行き先を決められない `cd`・`git -C`（変数・置換）は候補にせず、root checkout へのブランチ作成を通す。旧#320 の F6 で案 B（変数の 66 件のうち mktemp 43・worktree 7）に決めたまま。PR 本文の限界の先頭に書く |
| X3 | 独立-1 | low | no | self-inflicted | product | fixed | cwd を解けないときの deny が `git` の部分文字列に当たるコマンド全部で、文面もブランチ作成用だった。`_GIT_WORD_RE` にそろえ、専用の文面（例外と戻し方）にした。hook 自身の cwd が消えたときも止まることを断片に書いた commit: e67b9767 |
| X4 | 独立-1 | low | no | self-inflicted | test-power | fixed | `b"\xff\xfe"` の subtest が UTF-8 mode で UnicodeDecodeError の分岐を通らない。`PYTHONUTF8=0`・strict で読ませる別のテストにした commit: 499a8c2f |
| X5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文の「UTF-8 でないときは通す」「止めると git に関係ないコマンドまで止まる」が実態と合わない。断片を実際の条件に合わせ、PR 本文の限界を書き直した commit: 6d5f7c48 |
| X6 | 独立-1 | low | no | inherited | product | next-pr | 例外で guard が落ちる型を 1 つずつ try に入れて閉じている。wrapper で 0・2 以外の終了コードを deny にする多重防御（steering write guard と同じ形） |
| X7 | 独立-1 | low | no | self-inflicted | test-power | fixed | 止めたときのメッセージをテストが見ていない。専用の文面を assert する commit: 499a8c2f |
| X8 | 独立-1 | low | no | self-inflicted | style | fixed | hook を起動する fixture が support の外に 2 つ目としてあった。support に bytes の stdin を受ける関数を足して使う commit: 499a8c2f |
| X9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 決められない `-C` の後の相対 `-C` を前の基点から解くので、git が使わないパスで止めうることを docstring に書いていない（PR 本文に書く） |
| X10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Validation に、exec_target に足したテストの名前が無い（PR 本文に書く） |
| M3 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし（Opus と Fable の推奨は案 B で一致。そのまま採用） |
| Y1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 作業ディレクトリを解けないときの範囲を `\bgit\b` にしたので、`echo .gitignore; g''it checkout -b x` が通る。parser で作成サイトと GDD 名の worktree add を判定するようにした（テストを先に書いて失敗を確かめた）。囮の無い `g''it …` は差分前から `"git" not in command` で通る（限界） commit: b42277ec |
| Y2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 「Claude Code は payload に cwd を載せない」は誤りで、この guard が `tool_input` しか読まない。断片と文面を直した commit: b42277ec |
| Y3 | 独立-2 | low | no | self-inflicted | product | fixed | hook 自身の cwd が消えると `\bgit\b` のコマンドが全部止まり、文面の復旧手順も通らない。作るコマンドだけを止め、文面をセッションを開き直す案内にした commit: b42277ec |
| Y4 | 独立-2 | low | no | self-inflicted | test-power | fixed | hook 自身の cwd が消えた経路のテストが無い。rmdir した cwd で hook を起動するテストを足した commit: 0c9d841c |
| Y5 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files に support ファイルが無い commit: 18f98c0d |
| Y6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「UTF-8 として読めない payload は通す」は入口（PYTHONUTF8=1）の挙動と違う。断片の文は直した。テストが env の差し替えに頼る前提の固定はしていない（PR 本文に書く） |
| Z1 | 独立-3 | high | yes | inherited | fail-open | accepted | `g''it checkout -b x` は部分文字列 `git` が無いので、parser に届く前の `"git" not in command` で通る（変更前から。引用符で割る敵対的な形で、block guard は事故から守る〔2026-10-02〕の範囲外）。PR 本文の限界の先頭に書く |
| Z2 | 独立-3 | high | yes | inherited | fail-open | accepted | pre-push gate が hook 自身の cwd が消えたとき `$(pwd)` の失敗で exit 1 になり、push を通す（run-pre-push-gate-hook.sh:33）。Claude Code が消えた cwd で hook を起動するかは未確認。PR 本文の限界の先頭と「次の PR」に書く |
| Z3 | 独立-3 | high | yes | inherited | fail-open | accepted | pre-PR gate が同じく `$(pwd)` の失敗で exit 1（run-pre-pr-gate-hook.sh:473）。Z2 と同じ扱い |
| Z4 | 独立-3 | high | yes | inherited | fail-open | accepted | merge gate が同じく `$(pwd)` の失敗で exit 1（run-merge-gate-hook.sh:56）。Z2 と同じ扱い |
| Z5 | 独立-3 | high | yes | inherited | fail-open | accepted | pre-push・pre-PR・merge gate の前段の部分文字列フィルタが、引用符で割った `pu''sh`・`cre''ate`・`mer''ge` を通す（変更前から。敵対的な形で範囲外）。PR 本文の限界の先頭に書く |
| Z6 | 独立-3 | medium | no | self-inflicted | test-power | accepted | `_creates_without_cwd` の parser 不在と parser の例外の分岐、入口の wrapper 経由の経路をテストが通っていない（follow_up_of のため accepted。PR 本文の限界に書く） |
| Z7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | parser の import に失敗し、かつ作業ディレクトリを解けないとき、文面が「`git worktree prune` などは通る」と案内するが実際は止まり、本当の原因も出ない（PR 本文の限界に書く） |
| Z8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | テストの module docstring と 36 行のコメントが、変更前の「git コマンドは止める」の規定のまま（PR 本文の限界に書く） |
| Z9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片と main() のコメントが「作るコマンドだけを止める」と書くが、parser 不在と解析できないときは止める範囲が広い（PR 本文の限界に書く） |
| Z10 | 独立-3 | advisory | no | self-inflicted | product | accepted | 止めうるコマンドの集合を通常の経路と `_creates_without_cwd` の 2 か所で列挙している（今は一致。PR 本文に書く） |
| Z11 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | Claude Code が消えた cwd で hook を起動するか未確認で、起動しないならこの修正は効かない（PR 本文に書く） |
| W1 | 独立-4 | medium | no | self-inflicted | test-power | fixed | Linux の CI で、作るコマンドだけを止める振り分けのテストが毎回 skip になる。原因は PATH を渡さずに bare の python3 を起動するテストの形と見て、絶対パス（sys.executable）で起動するようにした（skip は残す） commit: aab8f591 |
| W2 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | skip の理由と PR 本文の限界が、起動できない条件を「Linux」に一般化している。テストのコメントを直し、PR 本文は CI の結果に合わせて書く commit: aab8f591 |
| W3 | 独立-4 | low | no | inherited | test-power | accepted | root branch guard のテストの hook は、CI が選んだ 3.14 ではなく system の python3 で走る（support の env に PATH が無い。9 本の起動形が変わるので別の PR） |
| W4 | 独立-4 | low | no | inherited | doc-claim | accepted | テストのモジュール docstring が、作業ディレクトリを解けない git コマンドを全部止めると書いている（PR 本文の限界に書く） |
