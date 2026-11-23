---
type: patch
---

#### Summary

`scripts/wait-until.py` と、その待ち方の案内を直した。

- `--pr-checks` の観測（観測行と最終行の `last_stdout`）に `any_failure=<yes|no>` を足した。check が混在するときは pending を優先して待つので、これまでは出ている failure が観測から消えていた
- 1 回の確認を止めた後、そのプロセスを止められない（EPERM・D state など）ときも、終わりを待つのは 5 秒までにした。全体の所要は最大 `--timeout + --check-timeout + 10` 秒になる
- 1 回の確認の中で予期しない例外が起きても、traceback で終わらず、例外の名前とメッセージの最後の行を `stderr=` に出して broken の最終行で終わる（exit 2）。`--pr-checks` の観測の `head=` は 1 行に整える
- docstring に、check ごとの分類は Stop hook の押し返しと共有するが、混在のときの優先は違う（スクリプトは pending、押し返しは failure）ことと、`--timeout` の上限 7,200 秒を超えて待つときの起動し直し方を書いた
- `references/post-merge-qa.md` 手順 3 で、デプロイの run を workflow ごとに出現・完了の順に待ち、出現の条件と完了の条件を分けて書いた。出現の条件が完了まで 0 を返さない形しか無く、10 分を超えるデプロイで「現れない」として止まっていた。完了の条件は、環境の承認待ち（status が `waiting`）の run があれば 3 を返し、上限まで待たずに止まる。QA 計画の時間の上限が 7,200 秒を超えるときの待ち方も書いた

#### Affected Files

- `plugins/gate-driven-development/scripts/wait-until.py`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/tests/test_wait_until.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_wait_until.py`: `any_failure` の値（success・failure・pending・failure と pending の混在・MERGED / CLOSED・checks なし）、止められない確認でも 15 秒以内に broken で終わること、確認の中の例外が両方の経路で broken の最終行になり、複数行のメッセージでも例外の名前が残ること、`head=` に改行が入っても最終行が 1 行のままであること、別グループの子のテストで子が本当に別のグループにいること（テストの後に子を止める）
- `bash tests/validate-plugin.sh`
