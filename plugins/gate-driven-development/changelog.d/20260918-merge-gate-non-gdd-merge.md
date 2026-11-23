---
type: patch
---

#### Summary

merge gate hook が、GDD と関係のない `gh pr merge` を止めていた。2026-09-15 と 2026-09-18 に、別の repo の依存更新 PR を自動マージするセッション（`gh pr merge -R <owner>/<repo> <番号>`）が `repo-root-unresolvable` で止まった。セッションの起動フォルダは git repo ではなく、対象の repo には GDD の marker も steering も無かった。

原因は root 候補ループにある。信頼できない候補（payload cwd / cd 先）は marker がある場合だけ採用される。信頼できる候補（プロセス cwd）が git repo でないと、root が決まらない。root が決まらない merge は一律に止めていた。一方、cwd が「marker の無い git repo」の場合、同じコマンドは step 5 の marker 不在 exit 0 で従来から通っていた。GDD の PR かどうかを見ずに通していたので、root checkout から GDD の PR を merge する形も無検査で通っていた。

「GDD の対象か」を、実行先の marker と、PR 単位の台帳の 2 つで判定するようにした。GDD の対象と判定できた merge だけを止め、対象外と判定できた merge は通す。

#### Fixed

- `hooks/scripts/run-merge-gate-hook.sh`: root が決まらない merge で、次の条件をすべて満たすときは GDD の対象外として exit 0 にした（`_mg_outside_gdd_merge`）
  - 解析が縮退なく完走している（`parsed=true` かつ `degraded` でない）
  - 曖昧な chdir が無い（`cd_intent` があるのに `cd_target` が確定しない形。例: `pushd` / `(cd …)` / 2 つ目の `cd` / `bash -c 'cd …'`）
  - payload cwd・cd 先が、実在する絶対パスのディレクトリである
  - プロセス cwd・payload cwd・cd 先の、論理パスと物理パスそれぞれの祖先（自身を含む）に marker（`.claude/gdd-dev.local.md`）が無い（`_mg_marker_in_ancestors`）。この探索は git に頼らない。git が無いときや `git rev-parse` が失敗するとき（dubious ownership など）は、候補ループが marker repo を見落とす。条件を「候補ループで marker が見つからない」にすると、GDD 管理下の merge が無検査で通るためである（方針メモ-1 の Opus の設計レビューで指摘）
  - 対象 PR が GDD の PR 台帳に載っていない（下記）
- GDD の PR 台帳を新設した（`hooks/scripts/lib/gdd-pr-roots.sh`、`~/.claude/.gdd-hook-state/gdd-pr-roots`。`GDD_HOOK_STATE_DIR` で変えられる）。Codex adversarial-review（codex-1）が high で指摘した「非 git の cwd から `-R` や PR URL で GDD 管理下の PR を merge すると無検査で通る」を閉じるためである。repo 単位ではなく PR 単位で判定するので、Renovate の PR は巻き込まない
  - 書く側: pre-PR gate（`run-pre-pr-gate-hook.sh`）が、active GDD で session continuity を確認した直後に、その worktree の root（と steering を持つ worktree）の絶対パスを重複なく追記する。best-effort で、書き込みに失敗しても pre-PR gate の判定は変えない。`chmod 600`
  - 読む側: merge gate が「marker が無いので通す」2 経路で照合する（`_mg_ledger_verdict`）。root 未解決の経路と、step 5 の git cwd に marker が無い経路（root checkout など）である。台帳に載った各 root の `.steering/*/state.md` の `PR URL` と、コマンドの対象 PR（owner/repo と番号の組）を照合する
  - 対象 PR の owner/repo は、URL・`-R`・実行先 repo の origin の順に取る。番号だけ・repo だけでは照合しない（別 repo の同じ番号や、連結した merge の片方で判定を割らない）
  - 照合の結果は 4 値で、経路ごとに次のように扱う
    - `hit`（台帳の PR と一致）: 2 経路とも `repo-root-unresolvable` で止め、GDD の worktree での実行へ誘導する（そこで証跡を検査する）
    - `miss`（一致しない・台帳が無い・root が消えている）: 通す
    - `unknown`（対象 PR を特定できない）: その経路の main の判定に戻す。root 未解決の経路は止め、git cwd の marker 不在の経路は通す。該当するのは、parser の `unresolvable`（複数 merge の連結・ブランチ名での指定など）、`GH_REPO` / `GH_HOST`（`env_repo_conflict`）、番号なし、実行先の origin が取れない、`gh repo set-default` の値（`remote.origin.gh-resolved`）が origin と別の repo を指す・解釈できない場合、origin 以外の remote（fork の upstream など）に `gh-resolved` がある場合である。origin の値は、`base` でも、origin と同じ repo を指す slug・URL（手で設定した場合など）でも origin で照合する。origin の値の受理集合は 3 組解決 (c) と同じにした（当初は `base` 以外を一律に unknown にしていたため、root checkout からの番号指定が台帳に載った PR でも通っていた。PR 後のレビュー（PR後-1）の high）。origin 以外の remote は (c) が読まないが、gh はそちらを対象にしうるので unknown にした（独立-2 の H1）。これで 旧#127 のうち、upstream に `gh-resolved` がある fork の clone へ非 git cwd から `cd` する形は、台帳があれば止まる（`gh repo clone <fork>` がこの値を書くことは未実測の前提）。どの remote にも `gh-resolved` が無い複数 remote の clone は閉じていない（下の限界）。`unresolvable` / `env_repo_conflict` の倒し方は、対象 PR の 3 組解決 (a)(b) と揃えた
    - `unreadable`（台帳の場所が決まらない＝`HOME` 未設定、台帳や state.md が読めない）: `unknown` と同じく、その経路の main の判定に戻す（root 未解決の経路は止め、git cwd の marker 不在の経路は通す）。当初は 2 経路とも止めていたが、main が無条件に通していた merge を台帳の故障で新たに止めるため、Codex（codex-3）の指摘で直した（方針メモ-4）
  - 当初は特定できない要素を「何にでも一致」として照合していた。Codex（codex-2）が 2 件を指摘した。複数 merge の連結で先頭の GDD PR が最後の repo での照合に隠れて通る（high）。`GH_REPO` 付きの `-R` merge が番号だけで台帳と一致して誤って止まる（medium）。安全策 4 の HITL でユーザーの指示により Fable に再設計を相談し、4 値にした（方針メモ-3）
- `repo-root-unresolvable` の案内文を「GDD 管理下の repo・PR なら GDD の worktree へ `cd <worktree> && gh pr merge` の形で実行」に変えた（root checkout から台帳に載った PR を merge した場合にも当てはまるように）
- 解析未完走（python3 不在・不正な JSON）・縮退・曖昧な chdir・実在しない（または相対の）実行先は、従来どおり `repo-root-unresolvable` で止める。marker のある repo での判定（`approval-missing` / `pr-target-unresolvable` / `untrusted-root-unverified` など）には手を入れていない
- `_mg_equals_ci` と `_mg_owner_repo` の定義を、root の解決より前（`_mg_marker_path` の直後）へ移した。中身は変えていない

#### Changed（テストの期待値）

旧仕様（「GDD の対象か判定できない merge は止める」）を固定していた次のテストは、期待値を exit 0 に反転した。判定できない入力の一部は、実は判定できる（全候補と祖先に marker が無く、台帳にも無い）ためである。marker の無い git cwd では、同じ入力は従来から exit 0 だった。

- `tests/test_merge_gate_hook_gate_activation.py`
  - `test_cd_target_without_marker_blocks_instead_of_passing_through` → `test_cd_target_without_marker_passes_as_outside_gdd`
  - `test_payload_cwd_without_marker_blocks_when_process_cwd_is_not_git` → `test_payload_cwd_without_marker_passes_when_process_cwd_is_not_git`
  - `test_repo_root_unresolvable_still_blocks_with_repo_and_pr_url_flags` → `test_repo_flag_merge_outside_gdd_passes_from_non_git_cwd`
- `repo-root-unresolvable` の文言を見るテスト（`test_repo_root_unresolvable_wording_matches_the_corrected_recovery_fragments`、`tests/test_merge_gate_hook_block_reason_quality.py` の sample）は、入力を「まだ止まる形」（実在しない cd 先）に差し替えた
- `tests/test_pre_pr_gate_contract.py` の hook 実行 helper は、`GDD_HOOK_STATE_DIR` を一時ディレクトリにする（テストが実 HOME の台帳へ書かないように）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`（新規）
- `plugins/gate-driven-development/tests/test_merge_gate_hook_non_gdd_merge.py`（新規）
- `plugins/gate-driven-development/tests/test_merge_gate_hook_gate_activation.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_block_reason_quality.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`

#### User Action Required

- GDD で作った PR を、marker の無い場所（root checkout・非 git のフォルダ）から `gh pr merge` すると、台帳に載っていれば止まるようになった。GDD の worktree で実行する

#### Validation / Eval Impact

- 新規 `tests/test_merge_gate_hook_non_gdd_merge.py`（入口は hook の実行）
  - 通す側: 非 git cwd から `-R` / PR URL / `cd <marker の無い repo>` / payload cwd / `cd <非 git ディレクトリ>` の merge が exit 0。台帳に別 repo の同じ番号・同じ repo の別の番号があっても exit 0
  - 止める側（marker）: marker repo への `cd` は `approval-missing`。次の場合は `repo-root-unresolvable` のまま止まる
    - git が失敗する PATH で marker repo（とその sub dir・payload cwd・symlink 経由）を実行先にした場合
    - git が無い PATH の場合
    - 曖昧な chdir 4 形
    - 実在しない cd 先・payload cwd、相対の payload cwd
    - python3 が失敗する場合、縮退した場合
  - 止める側（台帳）: 非 git cwd から `-R`（大小文字違い・`--repo=`）/ URL、`cd <origin が同じ clone>`、root checkout からの番号指定・`-R` で、台帳の PR に一致すると止まる。複数 merge の連結（両順序・URL 混在）は、非 git cwd から実行すると止まる。台帳・state.md が読めない、`HOME` 未設定のときは、root 未解決の経路で止まり、git cwd の marker 不在の経路で通る（4 値 × 2 経路の表テスト）
  - unknown の扱い: root checkout からの番号なし・ブランチ名・`GH_REPO`・連結 merge は通る（main と同じ）。非 git cwd からの `GH_REPO`・ブランチ名・`<URL> extra`、origin の無い clone や set-default が別 repo の clone への `cd` は止まる（main と同じ）。`GH_REPO` 付きの Renovate の `-R` merge は、root checkout から実行すると、別 repo の同じ番号の GDD PR が台帳にあっても通る
  - set-default: origin の `gh-resolved` が `base`・origin と同じ repo を指す値（`owner/repo`・大小文字違い・URL の形）の clone では、root checkout からの番号指定・非 git cwd からの `cd` とも、台帳の PR に一致すると止まり、別の番号は通る。origin と別の repo・解釈できない値、origin 以外の remote（upstream）に `gh-resolved` がある fork の clone（origin の値が未設定・`base`・fork 自身の場合）は unknown（git cwd では通り、root 未解決では止まる）
  - AC-2 の定常状態: 台帳に GDD の PR がある状態でも、非 git cwd から origin を持つ無関係な clone への `cd && gh pr merge <同じ番号>` は通る
  - 入口から効果まで: pre-PR gate（`gh pr create`）を 2 回実行すると台帳に root が 1 行だけ載り、merge gate がその PR を止め、別の番号は通す。active でない GDD では登録しない。state dir に書けなくても pre-PR gate の判定・出力は変わらない
- `_mg_outside_gdd_merge` の条件を 1 つずつ外すミューテーション 4 種と、`_mg_ledger_verdict` とその 2 呼び出し点の条件を 1 つずつ変えるミューテーション 13 種（step 5 の unreadable を block から exit 0 へ変えた後も再確認）が、いずれも新規テストで落ちることを確認した。PR 後に足した set-default の条件（`base` の除外、origin 以外の remote の検査 2 種）のミューテーション 3 種も落ちることを確認した
- 限界（PR 本文にも書く）: 次の PR は台帳に載らず、marker の無い場所からの merge は無検査で通る
  - 台帳の導入前に作られた open な GDD PR
  - pre-PR gate が発火しない経路で作った PR（`gh api`、GitHub の UI、kill-switch 中、`active: true` でない、session continuity が合わない）
  - `PR URL` を state.md に記録していない steering、worktree を削除した後の PR
  - marker の無い git cwd（root checkout など）から、対象 PR を特定できない形（番号なし・ブランチ名・`GH_REPO`・連結 merge）で merge する場合、実行先の origin が取れない・set-default が origin と別の repo を指す・origin 以外の remote に `gh-resolved` がある（fork の clone）場合と、台帳や state.md が読めない場合。main と同じ判定に戻しているためで、台帳に載った PR でも通る
- 限界（AC-2 の定常状態）: 非 git cwd から、対象 PR を特定できない clone（marker なし）へ `cd && gh pr merge <番号>` すると、台帳が無ければ通り、台帳があれば unknown で止まる（main と同じ）。該当するのは、origin の無い clone、set-default が origin と別の repo を指す・解釈できない clone、origin 以外の remote に `gh-resolved` がある clone（`gh repo clone <fork>` で作った fork など）である。一度 `gh pr create` を pre-PR gate で通すと台帳ができるので、定常状態では止まる。Renovate が merge する repo の clone は origin だけを持つ見込みで当たらない（未確認）
- 限界（独立-3・独立-4、未修正。安全策 4 で「止める」を選択した後のため）: 番号だけ・引数なしの merge で、gh が対象にする repo を origin と決めつけている残りがある。gh の解決規則（set-default が無く非対話なら upstream > github > origin の順に remote を選ぶ）は未実測の前提
  - 旧#135: どの remote にも `gh-resolved` が無く、`upstream` など origin 以外の remote を持つ fork の clone（`git clone` の後に `git remote add upstream` したもの）へ、非 git cwd から `cd && gh pr merge <番号>`（payload の cwd がその clone を指す形も同じ）すると、台帳照合は origin で miss になり通る。gh は upstream の PR を merge しうる（main はこの入力を止めていた）
  - 旧#136: marker のある経路では、番号だけの merge の owner/repo を origin から取り、3 組解決 (c) は origin の `gh-resolved` しか読まない。fork の GDD worktree で steering の PR URL が origin 側の PR のとき、`gh pr merge <番号>` は承認の検査を通るが、gh は upstream の同じ番号の PR を merge しうる。upstream に `gh-resolved=base` がある場合と、どの remote にも `gh-resolved` が無い場合の両方で起きる。main から同じ挙動
- 限界（独立-1、未修正）: 旧#126 先頭 0 の PR 番号（`gh pr merge -R acme/infra-gdd 007`）は台帳の `/pull/7` と文字列比較で一致せず miss になる。旧#128 台帳のパスがディレクトリだと miss、FIFO だと読み取りで待ち続けて timeout する
- 限界（C5・旧#125、未修正。安全策 4 の HITL でユーザーが「止める」を選択）: 台帳の走査は、読めない state.md に当たった時点で `unreadable` を返し、後続の state.md の hit を見ない。marker の無い git cwd の経路は `unreadable` を main と同じく通すので、台帳に載った PR でも root checkout から通る（main から緩くはなっていない）。root 未解決の経路では、`.steering` や root dir を列挙できないと `miss` になり、main なら止めていた merge が通る。どちらも台帳に載った worktree のパーミッションを壊したとき（chmod 等）に限る。`gdd_extract_doc_field` が読み取りに失敗して空を返す場合も `miss` 側に落ちる。後続 Issue で、読めないものを記録したまま全件を走査し（優先順位は hit > unreadable > miss）、`.steering/*/` の列挙可否を検査する
- 台帳は照合に実パスを要るため、絶対パスを持つ（`merge-gate-suppressed.log` などのログは hash 化している。台帳はログではなく、`chmod 600` でホーム配下に置く）
- pre-push gate（`run-pre-push-gate-hook.sh`）は、active 判定の後でしか `unresolvable-root` を出さない。同じ「判定できない場合は止める」パターンは無い
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
