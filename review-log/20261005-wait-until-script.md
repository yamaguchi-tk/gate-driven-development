---
lane: L1+
pr: 371
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus)（待機処理の監視の PR D。実測 2026-10-05、直近 30 日の main transcript 3,212 本: 待ちの background Bash 413 件、`--watch` を上限ありとして数えても上限の無いループ 154 件、うち 2 件が 5,014 分・2,076 分回った。自前の上限で打ち切られた 11 件は終了コードがすべて 0。条件の処理が壊れたまま上限まで待った例が少なくとも 7 件〔各 10〜51 分〕。plugin のスクリプトは skill の base directory から組んだ絶対パスで呼ばれ、`${CLAUDE_PLUGIN_ROOT}` の直書き 30 件は Bash では未定義。main の案はスクリプト＋文書と強制の方法の選択。Opus は、スクリプトを作り D1〔スクリプト・CI の分類の共有・文書と押し返しの案内文〕と D2〔PreToolUse(Bash) の deny、全セッション〕に分ける、`--pr-checks` で CI を条件を書かせずに待つ、汎用の形の「1 = まだ」はエラーも吸い込むので上限で止まるだけと書く、`--watch` を勧める案内を D1 で置き換える、ScheduleWakeup の待ちは併存させる、を推した。食い違いは無く、採った。この PR は D1。queued 形式の完了通知を Stop hook が読まない別の不具合は別タスクに切り出した。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-05T10:50+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 220c7e5c4ded998aa662035938cf1256fb8e9f67 | 0 | 1 | 0 | 2026-10-05T11:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 1ae25b2419f046c712f7b5173ea81e58412ee2fa | 0 | 0 | 0 | 2026-10-05T11:58+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨〔D1/D2 の分割、--pr-checks、契約の書き直し、案内の置き換え、ScheduleWakeup の併存〕を採用） |
| F1 | 独立-1 | medium | no | self-inflicted | ci-classification | fixed | --pr-checks が failure を最優先に返し、ほかの check が pending でも成立で終わる。文書は「CI が終われば」と書く。pending が残る間は待つ形にした commit: 8bc51607 |
| F2 | 独立-1 | low | no | self-inflicted | ci-classification | fixed | --pr-checks が PR の state を取得して読まず、MERGED・CLOSED を最終行に出さず待ち続けうる。観測に state を出し、OPEN でなければ成立とした commit: 8bc51607 |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | PR 番号の拒否のテストが偽の gh を置かず exit 2 だけを見ていて、範囲の検査を外しても本物の gh の失敗で通る commit: b45b9236 |
| F4 | 独立-1 | low | no | self-inflicted | timeout-bound | fixed | 1 回の確認を止めた後の communicate に上限が無く、別のプロセスグループに移った子が pipe を持つと返らない commit: 8bc51607 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「最終行はいつもこの形」と README の終了コードが、引数の誤り・--help・シグナルの経路を含まない commit: 8bc51607 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | post-merge-qa の手順 3 で、run の出現・失敗を条件の終了コードにどう写すかが無く、手順 2 の例に -R が無い commit: 8bc51607 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring が、条件を状態を読むだけのコマンドに限ると書いていない（書き込みが「まだ」のたびに繰り返される） commit: 8bc51607 |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | NO_CHECKS_GRACE_SECONDS のコメントの根拠が別の場面の規定を指す（F1〜F7 の修正で書き直した） commit: 8bc51607 |
| A2 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 押し返しのテストの正規表現が、パスがクォートされない前提（PR 本文に列挙） |
| A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に既定値・範囲・-R の制約・シグナルの終了コードが無い commit: なし（PR 本文） |
| A4 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストが関数の中で sys.path.insert し、戻していない（PR 本文に列挙） |
| A5 | 独立-1 | advisory | no | self-inflicted | signal | accepted | TaskStop が SIGKILL でグループを止める場合と、Popen 直後の SIGTERM で条件のプロセスが残りうる（未確認を含む。PR 本文に列挙） |
| A6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | skill をリンクで入れたとき、base directory の 2 つ上が plugin を指さない可能性（未確認。PR 本文に列挙） |
| G1 | 独立-2 | medium | no | self-inflicted | doc-claim | next-pr | post-merge-qa 手順 3 の run の出現待ちに、完了まで 0 を返さない条件の形しか書いておらず、10 分を超えるデプロイで「現れない」として止まる |
| G2 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 完了待ちを QA 計画の時間の上限で起動する書き方が、--timeout の上限 7,200 秒に触れていない |
| G3 | 独立-2 | low | no | self-inflicted | ci-classification | next-pr | docstring の「分類は押し返しと同じ」と、混在のとき pending を優先する分類が食い違う |
| G4 | 独立-2 | low | no | self-inflicted | ci-classification | next-pr | pending を優先した結果、出ている failure が観測行と最終行から消える |
| G5 | 独立-2 | low | no | self-inflicted | timeout-bound | next-pr | drain を打ち切った後の proc.wait() に timeout が無く、シグナルを受け付けない先頭プロセスで上限が崩れる |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「最終行が出ないのは…だけ」と言い切るが、RecursionError・stdout の OSError で traceback と exit 1 になる |
| G7 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 別グループの子のテストが、子が別グループにいる前提を assert していない |
| B1 | 独立-2 | advisory | no | self-inflicted | product | accepted | drain を打ち切ったとき、それまでの出力を捨てる（PR 本文に列挙） |
| B2 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「OPEN でなくなったら CI を問わず成立」だが、rollup を読めないと broken が先（PR 本文に列挙） |
| B3 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | テストの後に別グループの sleep 30 が残る（PR 本文に列挙） |
| B4 | 独立-2 | advisory | no | inherited | product | accepted | headRefOid の検査が押し返しと wait-until でそろっていない（PR 本文に列挙） |
