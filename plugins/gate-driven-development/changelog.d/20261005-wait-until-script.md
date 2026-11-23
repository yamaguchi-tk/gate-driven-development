---
type: minor
---

#### Summary

処理待ち（CI・レビュー bot のレビュー・デプロイなど）を上限つきで待つ `scripts/wait-until.py` を足した。Bash の run_in_background で起動する。

- 条件は `--pr-checks <PR 番号>`（PR の CI。条件を書かなくてよい）か、`-- <条件コマンド>` で渡す
- 条件コマンドの終了コードが 0 なら成立（exit 0）、1 ならまだ（待つ）、それ以外（シグナル・起動できない・1 回の実行が `--check-timeout` を超えた、を含む）なら条件が壊れているとして、待たずに exit 2 で終わる
- `--timeout` は必須で、7,200 秒が上限。過ぎたら exit 124 で終わる。引数を読めないときは、条件を実行せずに exit 2 で終わる
- 1 回の確認ごとの観測行と、決まった形の最終行（`wait-until: result=met|timeout|broken ...`）を stdout に出す
- `--pr-checks` は、pending の check が無くなれば success でも failure でも成立とし、PR の状態と CI の結果を最終行で返す。PR が OPEN でなくなったら CI を問わず成立とする。gh が失敗した・出力を読めない・checks が登録されないまま 600 秒たった、は壊れている扱い
- 条件は状態を読むだけのコマンドにする（書き込みを入れると「まだ」のたびに繰り返される）。docstring に、エラーが 1 になる条件の書き方の注意とあわせて書いた

Stop hook のマージ待ちの押し返しが示す待ち方の例を、`gh pr checks --watch` から、このスクリプトの絶対パスの呼び出しに替えた。CI の分類は `hooks/scripts/lib/ci_state.py` に移し、押し返しとスクリプトで同じ実装を使う（押し返しが使う分類の結果は変えていない）。`references/post-merge-qa.md`（マージ待ち・デプロイの run の出現と完了の待ち。条件の終了コードの返し方と、出現と完了を別に待つこと）と `skills/gdd-pr-review-followup/SKILL.md`（Claude Code の待ち方）の案内も、このスクリプトで待つ形にした。README のスクリプトの表に足した。

#### Affected Files

- `plugins/gate-driven-development/scripts/wait-until.py`
- `plugins/gate-driven-development/hooks/scripts/lib/ci_state.py`
- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_pushback.py`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/tests/test_wait_until.py`
- `plugins/gate-driven-development/tests/test_stop_hook_autonomy_pushback.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_wait_until.py`: 成立・まだの後の成立・期限切れ（124）・壊れた条件（終了コード 3・シグナル・起動できない・1 回の実行のハングと孫のプロセスの停止・別のグループに移った子が残るハング）・stdin を受け継がないこと・観測行がすぐに出ること・SIGTERM で確認のプロセスも止まること・引数の拒否（条件を実行しない）・`--pr-checks` の success / failure / pending / failure と pending の混在 / MERGED・CLOSED / gh の失敗 / 読めない出力 / checks が登録されないままの猶予、CI の分類を押し返しと共有すること
- `tests/test_stop_hook_autonomy_pushback.py`: pending の押し返しの理由文が、実在する絶対パスの wait-until.py を示し、`--watch` を示さないこと
- `bash tests/validate-plugin.sh`
