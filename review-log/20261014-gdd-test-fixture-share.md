---
lane: L1
pr: 旧#506
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d4e17455ceb956dc46504795e0a13fffc6a82183 | 0 | 2 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 依頼の「無駄コードの削除・スリム化」の行き先が PR 本文に無かった。PR 本文の目的に 3 項目の行き先を書いた。スリム化を別の PR に分けることは、2026-10-15 にユーザーが Fable の案（分ける。旧#502 の「次の PR」に名指しで書く）を選んだ。commit: なし（PR 本文） |
| r1-2 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 効果を fixture の git の延べで示し、全量の壁時計を比べていなかった。2 組の全量で比べ、中央値で壁時計 516s→484s、user+sys 2,999s→2,868s で、揺れより小さかったことを PR 本文に書いた。このまま出すことは、2026-10-15 にユーザーが Fable の案（このまま出す）を選んだ。commit: なし（PR 本文） |
| r1-3 | 独立-1 | low | no | self-inflicted | fixture-template | accepted | _build が落ちると連番の複製元ディレクトリが残り、以後の新しいキーが FileExistsError になる（近道の low） |
| r1-4 | 独立-1 | low | no | self-inflicted | fixture-template | accepted | commit_date を毎回変える呼び出し元（merge gate の setUp など）は速くならず、複製元がたまる（近道の low） |
| r1-5 | 独立-1 | low | no | self-inflicted | fixture-template | accepted | 複製元のキーが GIT_CONFIG_PARAMETERS・GIT_AUTHOR_* などを拾わない。amend で author の環境変数が効かない（近道の low） |
| r1-6 | 独立-1 | low | no | self-inflicted | fixture-template | accepted | copytree が path の mode・mtime を複製元の値にする、path が無くても作る、複製元の commit が reflog に残る、強制終了で複製元が残る（近道の low） |
| r1-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | 既存の repo・README.md があるときの従来の手順への分岐を通るテストが無い（近道の low） |
| r1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | git の起動回数の検査が assertLessEqual で 0 回も通す（近道の low） |
| r1-9 | 独立-1 | low | no | self-inflicted | test-power | accepted | 複製元を古い日時にする loop が、合うキーが無いと黙って何もしない（近道の low） |
| r1-10 | 独立-1 | low | no | self-inflicted | test-power | accepted | キーの各変数を 1 つずつ固定するテストが無い（近道の low） |
| r1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docstring の「全量のテストは git を約 1.9 万回」は hook の分を含むように読める。PR 本文は fixture の git（近道の low） |
| r1-12 | 独立-1 | advisory | no | self-inflicted | test-speed | fixed | test_pytest_ini_durations_contract が速いテストの見本にこのファイルを使うので、足した試験が 1 秒を超えると落ちうる。全量の計測で 1.47s になり実際に落ちたので、複製の試験を test_git_fixture_template.py に移した。commit: 80baf0bc |
