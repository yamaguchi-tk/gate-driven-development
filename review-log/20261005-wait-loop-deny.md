---
lane: L1+
pr: 378
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus)（待機処理の監視の PR D2。実測 2026-10-05、直近 30 日の main transcript の run_in_background の Bash 1,341 件: ループ + sleep 367 件〔目視で待ちでないのは heredoc の python の retry 1 件〕、--watch 31・gh run watch 28 件、`sleep N` だけ 55 件、ループでない sleep 46 件、sleep を含まない 814 件。main の案は、全セッション・例外なしで ループ + sleep と watch を deny する。Opus は方向に同意し、語の左境界を `(?<![\w./-])` にして wait-until.py の名前の until を外す、線形の判定にする、理由文に run の完了の条件の例を足す、全セッションで動くので project root・marker・`.gdd/` への記録を外して state dir に記録する、触るテストの一覧を実物に合わせる〔`_NUMBER_WORDS` に fourteen、trailing-newline の HOOKS には足さない〕を推した。読めない payload は通して記録、subagent の中も対象、他 repo も例外なし、上限つきのループも deny、`do` を必須にしない〔実測で `do` の無い deny は heredoc の python 2 件だけ〕も推奨どおり。食い違いは無く、採った。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-05T14:05+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 23e1d4374290362f5cd2548d90c5527e2a9e3c65 | 2 | 1 | 2 | 2026-10-05T14:38+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9fc37316f3d3ef0cfdbaaa2564b2b64a72fd6dde | 1 | 0 | 1 | 2026-10-05T14:52+09:00 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（独立-1 の F1・F2 と独立-2 の G1 で、同じクラスタ fail-open の high を含む巡が 2 回になり、安全策 4 が発火した。HITL の選択肢は 止める〔Opus の推奨〕・この PR で全部直す・スコープを撤回する で、ユーザーは 再設計して と答えた。再設計は、すべての hook が最初に source する lib/kill-switch.sh で PYTHONSAFEPATH=1 を export して 1 か所で閉じる案。Opus は同意して 止める の推奨を取り下げ、ファイルで起動して自分のディレクトリの lib を読むスクリプト〔Stop hook と HITL lint〕も直す、Stop hook のテストを PYTHONSAFEPATH の下で通す、3.11 未満は限界として G1 を accepted にする、を推した。実測で PYTHONSAFEPATH の下で lib を読めなくなるスクリプトは 12 本〔gdd_stop_hook.py と scripts/lint-*.py 11 本〕で、全部直した。食い違いは無く、採った） | - | 0 | 0 | 0 | 2026-10-05T15:18+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 078a2df670c2869cdc904971c9a3313fd4fa65c9 | 2 | 0 | 2 | 2026-10-05T15:39+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（独立-3 の H1〔self-inflicted、fail-open〕で high を含む巡が 3 回になり、安全策 4 が再発火した。実測: PYTHONPATH の `:`・`.`・`:/x` は 3.14.7 で PYTHONSAFEPATH=1 でも cwd の json.py を読む。利用者の環境の PYTHONPATH は 0 件。Opus は 止める を推し、H1・H2 を accepted にし -I の直し方を次の PR の候補にする案だった。ユーザーが直せるかを尋ね、main が kill-switch.sh に python3 を -I -X utf8 で起動する関数を置けば、リテラル・変数・標準入力の起動を 1 か所で -I にでき、3.9 でも閉じることを実測して示した。残るのは exec の起動と python から起動する子の python。ユーザーは H1・H2 を両方直すを選んだ） | - | 0 | 0 | 0 | 2026-10-05T15:49+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 727bc54ecbfb645e1085aa203d81289ddbf75c31 | 0 | 0 | 0 | 2026-10-05T16:17+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨〔語の境界、線形の判定、run の完了の例、state dir への記録、テストの一覧〕を採用） |
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 入口の python3 -c が cwd を sys.path の先頭に置き、repo の lib/__init__.py・lib.py が判定の module を置き換えて、import の失敗が入口の true への倒しで素通りになる。python3 -I -X utf8 で起動し、plugin の lib を先頭に入れた（閉じ方: 構造） commit: a4d8db4a |
| F2 | 独立-1 | high | yes | inherited | fail-open | fixed | background-dispatch-gate の入口にも同じ形があり、repo の lib が判定を置き換えて同期の gate-runner の起動が通る。同じ形に直した（閉じ方: 構造） commit: a4d8db4a |
| F3 | 独立-1 | medium | no | self-inflicted | product | fixed | subagent の中も deny するが、subagent が background の完了通知を受け取れる裏付けが無い。subagent には Monitor か foreground の待ち方を案内し、docstring を未確認に直した commit: a4d8db4a |
| F4 | 独立-1 | low | no | self-inflicted | product | fixed | dev watcher の --watch も deny され、理由文が無関係な案内になる。常駐の処理は利用者に確認する、を足した commit: a4d8db4a |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | SECURITY.md の hook 表の Bash の行に、新しい deny の hook と run_in_background が無い commit: 6d36e6af |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の「wait-until.py の呼び出しは通す」が言い過ぎ（条件にループの語と sleep を含めば deny される） commit: 6d36e6af |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の列挙（関数に包む・perl・文中の語）が実際の判定と合わない commit: なし（PR 本文） |
| F8 | 独立-1 | low | no | self-inflicted | test-power | fixed | sleep がループの語の後ろにあるという順序と、理由文の呼び出しの正しさをテストが固定していない commit: b6d57beb |
| A1 | 独立-1 | advisory | no | self-inflicted | product | accepted | run_in_background が文字列で届く経路を確かめていない（PR 本文に列挙） |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | docstring の実測に、集計方法と誤 deny の件数が無い（PR 本文に列挙） |
| A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 限界の列挙に watch -n が無い（PR 本文に列挙） |
| A4 | 独立-1 | advisory | no | inherited | product | accepted | ほかの python3 -c の hook でも、cwd の json.py などが標準モジュールより先に探される（PR 本文に列挙） |
| G1 | 独立-2 | high | yes | inherited | fail-open | fixed | pre-push gate・pre-PR gate・active-gdd-skill gate・その expansion gate の python3 -c も、hook の cwd の json.py などで import が落ちて素通りになる（block() の出力も同じ）。kill-switch.sh の python3 関数で -I にし、3.11 未満〔/usr/bin/python3 の 3.9〕も含めて閉じた（閉じ方: 構造） commit: 373b07c8 |
| G2 | 独立-2 | low | no | inherited | fail-open | fixed | merge gate・block しない hook・lib/*.sh の python3 -c も cwd の stdlib 名のファイルで落ちる（merge gate は理由の合わない parse-error で止める、nudge は黙って消える）。どれも kill-switch.sh を通るので、3.11 以上は同じ修正で閉じた commit: ad637b70 |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | subagent への案内が Monitor を先に出すが、Monitor のイベントが subagent に届くかも確かめていない |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | wait_loop_gate.py の docstring の「ループを含まない sleep N; <コマンド> は通す」が、断片・PR 本文の新しい表現と食い違う |
| G5 | 独立-2 | low | no | inherited | doc-claim | next-pr | SECURITY.md の Agent の行に、background-dispatch-gate の deny と marker の読み取りが無い |
| G6 | 独立-2 | low | no | inherited | doc-claim | next-pr | SECURITY.md の「hook は失敗時 fail-closed」が、読めない payload を通す 2 つの hook と食い違う |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の Validation に、subagent の理由文のテストが無い |
| A5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋の変更内容に、SECURITY.md の hook 表の Bash の行の変更が無い（PR 本文に列挙） |
| A6 | 独立-2 | advisory | no | self-inflicted | style | accepted | テストの関数の中の import と __import__（PR 本文に列挙） |
| M2 | 方針メモ-1 | advisory | no | inherited | none | accepted | 要約: なし（再設計〔kill-switch.sh の PYTHONSAFEPATH と、lib を読むスクリプト 12 本の修正〕を採った） |
| H1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | PYTHONSAFEPATH は sys.path[0] の 1 件だけを止め、PYTHONPATH の空・相対の要素〔`:`・`.`・`:/x`〕は 3.11 以上でも cwd を標準ライブラリより前に入れる。repo の json.py で block gate の python3 -c が落ちて素通りする〔実測で再現。利用者の環境の PYTHONPATH は未設定〕。断片とテストの docstring の「3.11 以上で閉じた」が無条件（閉じ方: 列挙） kill-switch.sh の python3 関数で -I -X utf8 にした commit: 373b07c8 |
| H2 | 独立-3 | high | yes | inherited | fail-open | fixed | Python 3.10 以下では block gate・merge gate・detect-steering の python3 -c・python3 - が今も cwd の json.py を読み、block の出力も python に頼るので出ない（閉じ方: 列挙） 呼び出し元の -c の行は変えず、kill-switch.sh の python3 関数で -I にした（3.9 の -I も確かめた） commit: 373b07c8 |
| H3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | kill-switch.sh の「-I で起動するのは今は SessionStart・PreCompact」が古い（wait-loop-gate・background-dispatch-gate も -I） H1 の修正と同じコメントを直した commit: 373b07c8 |
| H4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が SessionStart の python をすべて -I として扱うが、run-session-start-hook.sh:94 の python3 - は -I なし :94 の python3 - も関数を通って -I になり、限界の文を書き直した commit: なし（PR 本文） |
| H5 | 独立-3 | low | no | self-inflicted | test-power | next-pr | NEEDS_SAFE_PATH は runner の版で skip を決めるが、hook は PATH の python3 で動く |
| A7 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | glob に hooks/scripts/lib/stop-failure-record.py が入っていない（PR 本文に列挙） |
| M3 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし（ユーザーの選択で H1・H2 を直す。kill-switch.sh の python3 関数で -I -X utf8 にする） |
| I1 | 独立-4 | low | no | self-inflicted | test-power | next-pr | sys.flags.isolated の分岐は 3.11 未満の python があるときだけ確かめられ、CI では何の表示も無く外れる |
| I2 | 独立-4 | low | no | self-inflicted | test-power | next-pr | hook がファイルで起動する lib/stop-failure-record.py が -I の import テストの対象に入っていない |
| I3 | 独立-4 | low | no | self-inflicted | test-power | next-pr | Stop hook を run-gdd-stop-hook.sh から -I の本番の経路で通し、cwd の json.py と PYTHONPATH=: でも block するテストが無い |
| I4 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | python3 が無いときの python への fallback は 3 系でも関数を通らないが、記述は 2 系とだけ書く |
| I5 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | PYTHONSAFEPATH を export する理由（子の python で cwd を入れない）は、ファイルで起動する HITL lint には当たらない |
| I6 | 独立-4 | low | no | inherited | doc-claim | next-pr | 変更断片の「merge gate も block せずに通していた」は、parse の失敗で block する merge gate の主経路と合わない |
| I7 | 独立-4 | low | no | self-inflicted | test-power | next-pr | exec・timeout・env・絶対パスなど関数を通らない python の起動が後から足されても止めるテストが無い |
| A8 | 独立-4 | advisory | no | self-inflicted | test-power | accepted | default のケースを runner の python の版で決めている（PR 本文に列挙） |
| A9 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | hook ではない check-gate-ledger.sh も python3 関数を受け継ぐ（PR 本文に列挙） |
| A10 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | worktree guard の ADR が exec python3 のまま（PR 本文に列挙） |
| A11 | 独立-4 | advisory | no | self-inflicted | product | accepted | exec を外したので bash が python の親として残る（PR 本文に列挙） |
