# ADR: 性能回帰テストの判定を「CPU 時間（厳）＋ 壁時計 backstop（緩）」の二本立てにする（X-37）

- **日付**: 2026-09-12
- **状態**: 採用（開示して受容した既知の穴あり）
- **対象タスク**: `20260911-x37-test-timing-flakiness`（X-37）
- **リリース**: 変更断片 `plugins/gate-driven-development/changelog.d/20260912-x37-test-timing-flakiness.md`（次のリリースで `CHANGELOG.md` の版の節に集める）
- **関連**: `plugins/gate-driven-development/tests/_timing_budget.py`（新規）/ `tests/test_timing_budget_contract.py`（新規）/ `tests/_root_branch_guard_support.py` / `tests/test_root_branch_guard_contract.py` / `tests/test_merge_gate_followup_findings.py` / `tests/test_merge_gate_hook_command_parse.py`
- **前史**: `docs/adr/2026-09-11-x35-ac-closure-check.md` § Consequences が「壁時計の閾値を持つテストが `-n auto` の並列負荷下で落ちる」を後続課題として挙げていた。本 ADR はその課題への回答

## Context

`plugins/gate-driven-development/tests` の性能回帰テスト 5 本（以下 `T`）が、`-n auto` の並列実行と外部由来の高 CPU 負荷の下で落ちる。5 本はいずれも `time.monotonic()` の差分を絶対閾値と比較する形で、**壁時計 1 本が 2 つの性質を同時に担っていた**。

1. 入力長に対して計算量が二次で効かないこと（本来の検出目的）
2. hook の運用 timeout（10 秒）より十分速いこと（ユーザーが明示した完了条件）

実測で次が確定した。

- `T` の計測対象はいずれも CPU 律速（退行再現時、壁時計 2.18 秒に対し子プロセス CPU 2.16 秒）
- 負荷下では壁時計が 2.5 倍に膨らむ一方、CPU 時間の増加は 1.6 倍に留まる
- CPU 時間は CPU を使わない遅延を一切拾わない（`bash -c 'sleep 1'` で壁時計 1.016 秒・CPU 0.005 秒）

守る性質が 2 つあるのに時計が 1 本しかないことが、flaky の構造的な原因である。

## Decision

1. **二本立て判定**: 区間の CPU 秒と壁時計秒を同時に返す共有ヘルパー `tests/_timing_budget.py` を 1 本置き、`T` の 5 本すべてが次の 2 本を assert する
   - CPU 時間 < 現状の閾値（3.0 / 3.0 / `HOOK_TIMEOUT_SEC/4` = 2.5 / 1.0 / 0.5。**1 つも緩めない**）
   - 壁時計 < 該当 hook の timeout ÷ 2（= 5.0 秒）
2. **CPU 秒の定義**: `time.process_time()` の差分（自プロセス）＋ `resource.getrusage(RUSAGE_CHILDREN)` の user+sys 差分（子孫プロセス）。subprocess 計測と in-process 計測が同じ API を使う
3. **閾値の導出元を 1 本化**: 壁時計 backstop も `run_root_branch_guard` に追加した subprocess timeout も `hooks/hooks.json` から `hook_timeout_seconds(script_basename)` 経由で導出し、テスト側に `10` / `5` の literal を持たない。一致が 0 件・非数値・0 以下なら `LookupError` で fail-loud にし、既定値へのフォールバックは置かない
4. **旧#5 の検出力は今回広げない**: `test_cd_target_extraction_does_not_repeat_the_nested_scan` が守る退行は二次計算量ではなく約 2 倍の定数倍増で、入力長を増やしても正常時との比が変わらない。AC-4 の mutation 実測で事実関係だけを確定し、閾値の引き締めは行わない
5. **mutation 実測時だけ fixture timeout を override**: `run_root_branch_guard(..., timeout=None)` の既定は `hooks.json` 由来の 10 秒（2026-10-27 に、その 6 倍の `hang_guard_seconds` に変えた。Consequences の「2026-10-27 の変更」を参照）。mutation 実測時のみ呼び出し側が `timeout=120` を明示的に渡す。`TimeoutExpired` を捕捉して合成レスポンスを返す形は採らない
6. **mutation の封じ込め**: production の deny 境界（`hooks/scripts/**`）を変異させる検証は、repo 外 scratch への `cp -R` コピー上で行い、index を経由する復元を使わない。PR 作成直前に `git diff --name-only origin/main...HEAD` で `hooks/` 配下 0 件を確認する

## Why

- **性質ごとに時計を分けると、検出力を落とさずに環境依存だけを切り離せる**。二次計算量の検出は CPU 律速の計測に載せて閾値を据え置ける一方、外部負荷由来の壁時計の膨らみは判定から外れる
- **導出元の一本化と fail-loud** は、hook 側 timeout の変更がテストへ自動で伝播し、hook 名の typo や `hooks.json` の構造変更で backstop が黙って無意味化する経路を塞ぐ
- **fixture timeout の override 方式**は既定引数なので、`_root_branch_guard_support` を参照する既存 6 ファイルの呼び出しが無変更で済み、「全テスト pass」でそのまま担保できる。一方、`TimeoutExpired` を握り潰すとハング退行が Error として現れる検出経路を潰すため、握り潰しは採らない
- **mutation の封じ込めを手順で固定した**のは、`git checkout -- <path>` が index から復元するため、mutation 中に `git add -A` 相当が 1 回でも走ると変異版を復元して `git status` が clean に見えるという具体的な失敗モードがあるため。加えて `tests/checks/` 44 本に `hooks/scripts/**` の**内容**差分を見る check は存在せず、旧#5 の mutation は挙動保存かつ 0.0143 秒なので全体回帰でも赤くならない。全体回帰を backstop にする案は成立しない

## Rejected Alternatives

- **CPU 時間のみにする**: 差分は最小だが、ユーザーが明示した完了条件「hook の timeout より十分速いこと」の面が丸ごと消え、`sleep 1` 相当の非 CPU 律速な退行を一切検出しなくなる
- **比率判定（N と 2N の所要比）**: O(N²) なら比 4 という直接的な判定になるが、実行時間が倍になり、正常実装では比がプロセス起動コスト（約 0.2 秒）に支配されて ≈1 に潰れる
- **直列マーカー（pytest marker で並列から外す）**: 実際の失敗要因である**外部**由来の CPU 負荷には効かない。加えて marker 登録先が並行タスク（X-36）の変更ファイルと衝突する
- **閾値を単に緩める**: 性質の検出力が下がる。ユーザーが明示的に却下した案
- **テスト側に timeout 定数を literal で書く / `hook_timeout_seconds()` に既定値を持たせる**: 実装は最短だが、`hooks.json` との乖離が検出されず、閾値が静かに無意味化する経路が開く
- **旧#5 の入力長を拡大する / 旧#5 を `T` から外す / 旧#5 の閾値を実測ベースに引き締める**: 順に、比が変わらないため無効 / 旧#5 は `T` で最も落ちやすく外すと目的が達成されない / CPU 側閾値の変更にあたり承認済み AC に反する
- **`tests/checks/` に `hooks/scripts/**` の内容差分 check を新設する**: 恒久的な再発防止にはなるが、本タスクのスコープ（テストの計測方法の差し替え）を越えて production の check 群を触ることになる

## Consequences

- **良い影響**: 二次計算量の退行検出は CPU 律速の計測で据え置かれ、並列 + 外部負荷下の flaky が止まる。計測式が 1 箇所に集約され、コピーのドリフトが起きない。hook 側 timeout の変更が自動でテストへ伝播する
- **悪い影響**: 壁時計の単独上限が 0.5〜3.0 秒から一律 5.0 秒へ**緩む**。5 秒を超えない非 CPU 律速の遅延（I/O 待ち・ロック待ち）の混入は検出されなくなる。`hooks.json` の構造変更でテスト群が collection 段階から落ちる（意図した fail-loud）
- **既知の穴（開示して受容）**
  - **`T` の外に壁時計判定が残る**: 対象外の 2 本と、兄弟ファイル `test_merge_gate_hook_env_split_string.py`（`monotonic` 10 箇所）は今回の変更に含まない。残したままでは「並列負荷下の flaky を止める」目的は完全には満たされない
  - **旧#5 の二重走査形は依然として検出できない**: 閾値 0.5 秒に対し当該退行の実測は 0.0143 秒（1/35）。AC-4 は `seen` dedup を外す形で red を取っており、docstring が名指しする退行形そのものは赤くならない
  - **旧#4 は退行時に fail ではなく hang する**: in-process 計測で subprocess timeout を持たないため（pre-existing）
  - **`run_root_branch_guard` の `timeout=` は mutation で固定されていない**: 削除しても guard 系 122 本が緑のまま。AC-9 は構造確認で充足しており、assert の恒真化ではなく hang 保護の消失（2026-10-27 に閉じた: `test_timing_budget_contract.py` の `HangGuardSecondsTests` が、既定の打ち切りが `hang_guard_seconds` であることを固定する）
  - **負荷下の CPU 余裕の最小は 2.9 倍**（旧#3、ncpu=16 に対し burner 32 の下での実測）。極端な負荷では原理的になお落ちうる。今回の対応は確率的な改善であり、非 flaky の証明ではない
- **2026-10-27 の変更**: Decision 5 の `run_root_branch_guard` の既定 timeout を、`hooks.json` の timeout の 6 倍（`tests/_timing_budget.py` の `hang_guard_seconds`）にした。並列の全量テストの負荷で、壁時計が運用 timeout の 10 秒に届くため。壁時計 backstop（`GUARD_HOOK_TIMEOUT_SEC / 2`）は変えていない
- **後続タスク・再検討条件**
  - `T` の外に残る壁時計判定 2 本と兄弟ファイルを同じ形へ寄せる
  - `tests/checks/` に production スクリプトの内容差分 check を常設する
  - 旧#5 の閾値を実測ベースに引き締めるかは、CPU 側閾値の変更にあたるため human check で判断する

## Source

- Derived from `.steering/20260911-x37-test-timing-flakiness/`（branch-only。ADR-1〜ADR-5 と Honest Limitations を蒸留）
- 検証の実測値と各 AC の evidence は PR 本文に残す（変更の要約は上記の変更断片）
