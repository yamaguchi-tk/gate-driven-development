"""branch 名候補抽出（AC-1〜AC-4）と AC-7 fail-closed fallback の契約。

`switch` / `checkout` / `branch` の各 subcommand から「実際に作成される branch 名」を
抽出する経路と、候補を確定できない形（未展開 token / 未知 flag / 候補 0 件）で
コマンド全文判定へ退避する経路を扱う。分割の経緯と共有 fixture は
`tests/_root_branch_guard_support.py` を参照。
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import RootBranchGuardFixtureMixin


class RootBranchNameCandidateTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    # AC-1 の形式カバレッジ。active state を **書かない** ことが要点で、
    # `main()` の `not root_state_blocks(...) and not _creates_gdd_named_branch(...)`
    # の短絡を通り抜けて名前抽出経路まで到達させる。active state 付きのテストは
    # 抽出結果によらず deny になるため、抽出側の退行を検出できない。
    _AC1_CREATE_FORMS = [
        # 分離形 long flag
        "git switch --create {name}",
        "git switch --force-create {name}",
        # inline value long flag
        "git switch --create={name}",
        "git switch --force-create={name}",
        # 分離形 short flag / 大文字 force 形
        "git switch -C {name}",
        "git checkout -B {name}",
        # 分離形 short cluster
        "git switch -fc {name}",
        "git checkout -fb {name}",
        # global flag 前置
        "git -C . switch -c {name}",
        "git --git-dir=.git switch -c {name}",
        "git --no-pager checkout -b {name}",
    ]

    def test_hook_blocks_branch_creating_short_option_cluster(self):
        # completion_check.md H-1 remediation: `_segment_creates_branch` は
        # `_BRANCH_CREATING_FLAGS = {"-c", "-C", "--copy", "-f", "--force"}` を
        # 厳密一致でしか見ておらず、`_segment_creates_switch` /
        # `_segment_creates_checkout` がすでに使っている `_short_cluster_has`
        # 型の短 option cluster 対応をしていなかった（分離形は deny、cluster
        # 形 `-cf`/`-fc`/`-Cf`/`-fC` は誤って allow されていた）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -cf old codex/20260904-c",
                "git branch -fc old codex/20260904-d",
                "git branch -Cf old codex/20260904-e",
                "git branch -fC old codex/20260904-f",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_branch_non_creating_short_option_cluster_precedence(self):
        # H-1 横断監査: creating flag（`-f`）と non-creating flag（`-d`/`-D`/
        # `-m`/`-M`）が同一 cluster に混在する場合、実 git の挙動（force delete /
        # force move はブランチを作成しない）に合わせて non-creating を優先する。
        # 実測: `git branch -fd <name>` / `-df <name>` は削除操作として rc=0 で
        # 完了し、ブランチを作成しない（force move の `-fm` も同様）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)
            subprocess.run(["git", "branch", "old-branch"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "old-branch-2"], cwd=repo, check=True)

            for command in [
                "git branch -fd old-branch",
                "git branch -df old-branch",
                "git branch -fm old-branch-2 renamed-branch",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_allows_branch_read_only_operations(self):
        # AC-6(e) / AC-8 FP-1: 読み取り専用は allow（active state ありでも）
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -a",
                "git branch -v",
                "git branch -vv",
                "git branch -d old-branch",
                "git branch -D old-branch",
                "git branch -m old new",
                "git branch -M old new",
                "git branch -r",
                "git branch --list",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_allows_branch_value_taking_flags(self):
        # AC-6(f) 相当: 値を取る branch flag の引数を positional と誤認しない。
        #
        # `git branch --color always` は元々ここに含まれていたが、`--color` は
        # 実 git では optional argument（`=` 必須、空白区切りの次 token は値として
        # 消費しない）であり、この形は実際には branch "always" を作成する
        # （実測確認済み、git 2.50.1）。「値を取る flag の引数だから positional
        # ではない」という当時の前提が実 git 未検証のまま誤っていたため、正しい
        # 期待値（deny）へ `test_hook_blocks_branch_value_taking_flags_with_leftover_positional`
        # として移した。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                # `%(refname)` は unquoted だと bash 自体が `(` を構文エラーにする
                # ため、実コマンドとして成立する quote 済みの形で検証する。
                "git branch --format '%(refname)'",
                "git branch --abbrev 10 -a",
                "git branch --sort committerdate",
                "git branch --set-upstream-to=origin/main feature-x",
                "git --no-pager diff branch main",
                "git --git-dir=/tmp/x diff branch main",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_blocks_branch_value_taking_flags_with_leftover_positional(self):
        # 独立実装レビュー指摘: `_segment_creates_branch` は `-` 始まりの token が
        # 1 つでもあれば既知の creating flag（-c/-C/-f/--copy/--force）の有無だけで
        # 作成操作かどうかを判定しており、`--color`/`--column`/`--abbrev` のような
        # optional argument 型 flag（`=` 無しの空白区切りの次 token を値として
        # 消費しない）や `--sort`/`--format` のような必須値 flag の「値の後ろに
        # 残る positional」を一切考慮していなかった。実 git（2.50.1）はいずれの
        # 形でも branch を作成するため、site 自体が gate 1 の収集から漏れる
        # guard bypass だった。
        #
        # `git branch --color always` は名前分の追加 token が無い 2 token 形だが、
        # 実 git はこの唯一の positional "always" を branch 名として作成するため
        # （start-point 省略 = HEAD から作成）、これも同じ bypass の一種として
        # deny する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch --color always",
                "git branch --color always feature-x",
                "git branch --color=always feature-x",
                "git branch --column always",
                "git branch --column always feature-x",
                "git branch --column=always feature-x",
                "git branch --abbrev 10",
                "git branch --abbrev=10 feature-x",
                "git branch --sort committerdate feature-x",
                # `%(refname)` は unquoted だと bash 自体が `(` を構文エラーにする
                # （`bash -n -c 'git branch --format %(refname) feature-x'` で実測
                # 確認済み）ため、実コマンドとして成立する quote 済みの形で検証する。
                "git branch --format '%(refname)' feature-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_mandatory_value_flag_when_value_looks_like_non_creating_flag(
        self,
    ):
        # 独立セルフレビュー（2 名の finder agent が独立に同一事例を実測確認）
        # 指摘: `_segment_creates_branch` の非作成 flag 判定（`_token_is_branch_
        # non_creating_flag`）は `rest` 全体を位置を無視して一括スキャンして
        # いたため、`--sort`/`--format`（必須値 flag）の**値**の token が
        # たまたま `-d`/`-D`/`-m`/`-M` の見た目をしていると、実際には branch
        # を作成する操作（実 git は `-d` 等を sort key / format として消費し
        # 残りの token から branch を作成する。実測確認済み: git 2.50.1）を
        # delete/move 操作と誤認して非作成と判定し、site 自体が gate 1 の
        # 収集から漏れる guard bypass だった（`git branch --sort -d
        # codex/... ` が active state 有りでも allow されていた）。
        # `_segment_creates_branch` を 1 パスの cursor walk へ書き換え、
        # `--sort`/`--format` の値として消費した token を独立の flag として
        # 再評価しないことで解消した。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch --sort -d codex/20260906-x",
                "git branch --sort -D codex/20260906-x",
                "git branch --format -m codex/20260906-x",
                "git branch --format -M codex/20260906-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_creating_flag_with_mandatory_value_flag_and_no_name(self):
        # 独立セルフレビュー指摘: `has_creating_flag`（`-f` 等）と `has_positional`
        # （`-` 始まりでない token の有無）を独立に 2 回スキャンする旧実装は、
        # `--sort`/`--format` の値 token を「独立した positional」と誤認して
        # いたため、`git branch -f --sort committerdate`（実際には branch 名
        # 引数が無く、実 git は何も作成しない。実測確認済み: git 2.50.1）を
        # 誤って作成操作と判定し deny していた（fail-closed 方向の false
        # positive）。1 パスの cursor walk では `committerdate` が `--sort`
        # の値として正しく消費されるため、leftover positional が無く allow
        # になる。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -f --sort committerdate",
                "git branch --force --format committerdate",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_blocks_value_taking_flag_followed_by_double_dash_and_name(self):
        # 独立セルフレビュー指摘: 新設した value-taking flag モデリングが `--`
        # （end-of-options）を一切考慮しておらず、`--sort`/`--format` が値を
        # 消費した後や `--color`/`--column`/`--abbrev` の直後に `--` が続く
        # 形で、実 git が branch を作成する（実測確認済み: git 2.50.1）にも
        # 関わらず未知の `-` 始まり token として保守側 `return False` に落ちて
        # いた。既に値取り flag を 1 つ以上消費済みの場合に限り `--` を
        # 読み飛ばすよう修正した（`git branch -- <name>` という creating flag
        # 無しの bare 形は既知 limitation のまま allow を維持する）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch --sort committerdate -- feature-x",
                "git branch --sort -- feature-x",
                "git branch --color -- feature-x",
                "git branch --color always -- feature-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_when_redirection_target_looks_like_non_creating_flag(self):
        # PR #34 Copilot review 指摘 Round 6: `_segment_creates_branch` は
        # redirection を読み飛ばさず raw token をそのまま走査するため、
        # `git branch codex/... >-d` の `-d`（redirection の出力先 `-d` という
        # 名前のファイル）を delete flag と誤認し、segment 自体が「作成操作
        # ではない」と判定される。gate 1（`command_creates_root_branch`）の
        # site 収集から丸ごと漏れるため、active state が有っても検出されない
        # guard bypass だった（実 git は `codex/...` を作成する。実測確認済み）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch codex/20260905-x >-d",
                "git branch codex/20260905-x >-D",
                "git branch codex/20260905-x >-m",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_numeric_branch_name_before_redirection(self):
        # 独立実装レビュー指摘（PR #34 Round 6 直後）: 上記 guard bypass 修正が
        # `_strip_redirections` に gate 2 用の fd 数字ヒューリスティック
        # （`_is_potential_fd_token`）まで持ち込んでいたため、`git branch 2
        # >/dev/null` のように branch 名そのものが数字だと、その唯一の
        # positional を fd 宣言と誤認して除去し、`_segment_creates_branch` が
        # 「作成操作ではない」と判定して gate 1 の site 収集ごと漏れる新規
        # regression になっていた（active state が有っても検出されない）。
        # gate 1 では operator + 対象のみを除去し、fd 数字ヒューリスティックは
        # 使わない（実測確認済み: 修正前は active state 有りでも allow）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch 2 >/dev/null",
                "git branch 42 > build.log",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_creation_via_uncategorized_flags(self):
        # 独立実装レビュー指摘（PR #34 merge 後）: 当時の gate 1（`_segment_creates_branch`）
        # は `_token_is_branch_non_creating_flag` / `_token_is_branch_creating_flag`
        # （本タスクで `_classify_branch_short_cluster` / `_branch_long_flag_dispatch`
        # へ置換・削除済み）のどちらにも該当しない未知 flag（`-q`/`-t`/`--track`/`--no-track`/
        # `--create-reflog` 等）を一切考慮しておらず、gate 2 の
        # `_has_unknown_branch_flag` のような fail-closed fallback が gate 1 に
        # 存在しなかった。`git branch -q <name>` のような日常的な形も含め、実 git
        # はいずれも branch を作成するが（実測確認済み: git 2.50.1）、gate 1 が
        # site 自体を収集しないため active state が有っても検出されず bypass
        # していた。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -q codex/20260906-a",
                "git branch -t codex/20260906-b main",
                "git branch --track codex/20260906-c",
                "git branch --no-track codex/20260906-d",
                "git branch --create-reflog codex/20260906-e",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_bare_double_dash_branch_creation_known_limitation(self):
        # 既知の gate 1 false negative（PR #34 Copilot review 指摘）:
        # `git branch -- <name>`（creating flag
        # 無し）は `_segment_creates_branch` が作成操作として検出しないため、
        # active state 有り・GDD 名でも allow される。本 PR 前後で不変
        # （AC-8 は gate 1 の判定基準を変えない方針のため非スコープ）。
        # creating flag 付きの `-f --` 形（AC-2）は別テストで deny を固定済み。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -- codex/20260905-x",
                "git branch -- feature-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_allows_checkout_start_point_and_pathspec(self):
        # AC-2(checkout) / AC-3: start-point / `--` 以降の pathspec は候補から除外される。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git checkout -b feature-x codex/20260903-x",
                "git checkout -b feature-x -- codex/20260903-x",
                "git switch -c feature-x codex/20260903-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_blocks_value_joined_short_forms(self):
        # AC-1 (値結合形): `\b` 不成立で現行 allow だった形を安全側の deny に是正する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git switch -ccodex/20260903-x",
                "git switch -fccodex/20260903-x",
                "git checkout -bcodex/20260903-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_redirection_at_value_position(self):
        # AC-1 (redirection 単発/連続): while ループでの前送りが無いと候補が
        # `2` や `>` になり silent allow になる。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git checkout -b 2>/dev/null codex/20260903-x",
                "git switch -c 2>&1 codex/20260903-x",
                "git switch -c >/dev/null 2>&1 codex/20260903-x",
                "git switch -c 2>/dev/null >/tmp/gdd-t1-probe codex/20260903-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_ac1_create_forms_without_active_state(self):
        # AC-1: 各形式で GDD 命名の新 branch を作る形は active state 無しでも deny。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for template in self._AC1_CREATE_FORMS:
                command = template.format(name="codex/20260903-x")
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_ac1_create_forms_with_gdd_start_point(self):
        # AC-1 / AC-3: 同じ形式で新 branch 名が非 GDD、GDD 命名は start-point の
        # 位置にある場合は allow。
        #
        # 退行検出の要: いずれかの形式で名前抽出が壊れると候補 0 件 → AC-7(i)
        # fallback でコマンド全文判定に落ち、`codex/...` を含むため deny になる。
        # つまりこの allow assertion が形式ごとの抽出経路の生存確認になる
        # （deny 側だけでは fallback に救われて退行を素通しする）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for template in self._AC1_CREATE_FORMS:
                command = template.format(name="feature-x") + " codex/20260903-x"
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_falls_back_when_switch_checkout_candidate_unavailable(self):
        # AC-7(i): checkout の `-b` が `--` の後ろにしか無く候補 0 件 → fallback で deny。
        # AC-7(i-sanitize): sanitize 後に空になる switch の各形。
        # AC-7(ii-var) / AC-7(ii-subst): 未展開 token を含む switch の各形。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git checkout codex/20260903-x -- -b file",
                "git switch --create= codex/20260903-x",
                "git switch -c -- codex/20260903-x",
                "git switch --create --force codex/20260903-z",
                "BRANCH=codex/20260903-x git switch -c $BRANCH",
                'git switch -c "$(echo codex/20260903-x)"',
                "git switch -c `echo codex/20260903-x`",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_branch_non_copy_and_copy_forms(self):
        # AC-1 (branch 非 copy / copy): 非 copy は最初の positional、
        # copy は最後の positional のみが新 branch 名。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git branch feature-x codex/20260903-x",
                "git branch -c codex/20260903-old new-name",
                "git branch --copy codex/20260903-old new-name",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_blocks_branch_double_dash_end_of_options(self):
        # AC-2(branch): `--` は end-of-options であり後続 positional は候補に含む。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_guard(repo, "git branch -f -- codex/20260903-x")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_falls_back_on_unknown_branch_flag(self):
        # AC-7(iii): branch site に既知 no-arg flag 以外の `-` 始まり token が
        # あれば command 全体を fallback する（値取り long option の分離引数誤認対策）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git branch -f --sort committerdate codex/20260903-x",
                # `%(refname)` は unquoted だと bash 自体が `(` を構文エラーにする
                # （`bash -n -c '...'` で実測確認済み）ため、実コマンドとして
                # 成立する quote 済みの形で検証する。
                "git branch -f --format '%(refname)' codex/20260903-x",
                "git branch --force --sort refname codex/20260903-x",
                "git branch -f -q feature-x codex/20260903-seed",
                # 独立セルフレビュー指摘（cross-file tracer 角度）: 上記はいずれも
                # `-f`/`--force`/`-q` という「既存の creating flag」が同時に
                # 存在するため、gate 1 の site 検出自体は旧 `has_creating_flag`
                # 経路でも成立していた。`--color`/`--column`/`--abbrev` 単独
                # （companion creating flag 無し）でも同じ fallback 経路が
                # 機能することを、active state 無しの構成で直接検証する
                # （`_branch_names` は --color を「値抽出不要な bare flag」
                # として扱えず候補 0 件になるため、`_has_unknown_branch_flag`
                # 経由でコマンド全文の GDD 命名 regex 判定へ fallback する）。
                "git branch --color codex/20260903-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_positional_after_redirection(self):
        # T2-1（impl-gate Round 1 / High）: `split_segments` は redirection を
        # 独立 token に分解する（`git branch 2>/dev/null codex/...` ->
        # ['git','branch','2','>','/dev/null','codex/...']）。positional を
        # 「`-` 始まりでない token」だけで拾うと非 copy の候補が `2` や `>` に
        # なり、sanitize にも `_is_unexpanded_token` にも `_has_unknown_branch_flag`
        # にも掛からず AC-7 の fallback へ到達しないまま silent allow になる
        # （実 git 2.50.1 は refs/heads/codex/20260903-x を作成する）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git branch 2>/dev/null codex/20260903-x",
                "git branch >/dev/null codex/20260903-x",
                "git branch -f 2>/dev/null codex/20260903-x",
                "git branch -f >/dev/null 2>&1 codex/20260903-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_branch_copy_with_redirection_between_positionals(self):
        # T2-1 の allow 側: redirection を読み飛ばした結果、copy の「最後の
        # positional」が `/dev/null` や `1` ではなく実際の新 branch 名
        # （`new-name`）になること。読み飛ばしを deny 側だけで実装すると
        # copy の候補位置がずれてこの形が deny に倒れる。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_guard(
                repo, "git branch -c codex/20260903-old 2>/dev/null new-name"
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])

    def test_hook_blocks_switch_when_digit_positional_precedes_unrelated_redirection_known_limitation(self):
        # 既知の limitation（PR #34 Copilot review 指摘 Round 2）:
        # `2>/dev/null`（fd 番号としての `2`。
        # 空白なし）と `2 > /dev/null`（`2` は独立した positional 引数、`>` は
        # 既定 fd への redirection。空白あり）は shlex ベースの tokenizer を
        # 通すと同一の token 列になり、空白の有無という区別情報が失われる。
        # そのため `git switch -c 2 > /dev/null codex/20260903-x` は実 git では
        # `2`（非GDD名）を作成するにもかかわらず、本 hook は `2` を fd 番号と
        # 誤認して読み飛ばし、start-point の `codex/20260903-x` を `-c` の値と
        # 誤認して deny する（過剰 deny・fail-closed 方向で silent allow では
        # ない）。修正には `git_command_parse.py`（他 guard と共有）の
        # tokenizer 自体の変更が必要で本 task の非スコープ。実 git の挙動
        # （`Switched to a new branch '2'`）を実測確認済み。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_guard(
                repo, "git switch -c 2 > /dev/null codex/20260903-x"
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_allows_branch_when_redirection_target_looks_like_flag(self):
        # PR #34 Copilot review 指摘（Round 2）: `_has_unknown_branch_flag` は
        # `_branch_names` と異なり `_skip_redirection` を使わず生の token 列を
        # そのまま走査するため、redirection の対象 token（`>-q` の `-q` 等）を
        # 未知 flag と誤認していた。実際に作成される branch 名は `feature-x`
        # のみ（`codex/...-seed` は start-point として既に存在する前提）で
        # あり、redirection 対象がたまたま `-` 始まりであることは branch 名
        # 判定に無関係。誤認すると AC-7(iii) の fallback が発火し、command
        # 全文中の `codex/...-seed` に一致して deny になる。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git branch -f feature-x codex/20260903-seed >-q",
                "git branch -f feature-x codex/20260903-seed 2>-q",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_blocks_named_fd_redirect_guard_bypass(self):
        # PR #34 Copilot review 指摘（Round 3、guard bypass）: bash 4.1+ の
        # 可変（named）FD redirect 構文 `{name}>word` は、`{name}` が redirection
        # operator に直接隣接するとき bash がそれ自体を fd 宣言として消費し、
        # `{name}` はコマンドの引数には残らない。実行される git コマンドは
        # 事実上 `git switch -c codex/...` / `git branch codex/...` になり、
        # 実 git は GDD 命名の ref を新規作成する。
        #
        # ところが `_next_value_index` / `_skip_redirection` は数字 fd
        # （`isdigit()`）しか redirection の一部として読み飛ばさないため、
        # `{fd}` を素の候補・positional として取り込んでしまい、後続の
        # `codex/...` が候補から漏れて active state 無しで allow される
        # （silent allow / guard bypass）。`{name}` 形の token を fd 候補として
        # 読み飛ばすよう修正し、名前を確定できない形として fail-closed
        # fallback（コマンド全文判定）へ倒す。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git switch -c {fd}>/dev/null codex/20260903-x",
                "git branch {fd}>/dev/null codex/20260903-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_switch_and_checkout_when_redirection_target_looks_like_flag(self):
        # PR #34 Copilot review 指摘（Round 4）: `_checkout_branch_names` は
        # `_branch_names` / `_has_unknown_branch_flag`（Round 2 で修正済み）と
        # 異なり `_skip_redirection` を使わず生の token 列をそのまま走査する
        # ため、redirection の対象 token（`>-b` の `-b` 等）を 2 個目の
        # `-b`/`-c` flag と誤認していた。実際には最初の `-b`/`-c` の値
        # （`feature-x`）だけが新規 branch 名で、redirect 対象の後ろの token
        # （`codex/...-seed`）は既存 branch を指す start-point にすぎない。
        # 誤認すると start-point まで候補に含めてしまい、GDD 名を含む
        # start-point 指定で誤って deny になる。`_switch_branch_names` にも
        # 同型の欠陥があることを ripple check で確認済み。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git checkout -b feature-x >-b codex/20260903-seed",
                "git switch -c feature-x >-c codex/20260903-seed",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    # --- R2: gate 1 `_segment_creates_branch` 未知 flag fail-closed 化 ---
    # T-1 (AC-1 / AC-2 / AC-4 / AC-5 / AC-8)。design.md § R2再設計 D-1〜D-10 /
    # requirements.md § Correction Log (A) が正本。

    def test_hook_blocks_branch_residual_fail_open_flags(self):
        # AC-1（R2）: 新 base `3b21a2c`（PR #41 適用後）で残存する fail-open
        # 11 形。実測（git 2.50.1）: いずれも実 git が branch を作成するが、
        # 旧 gate 1 は未知 `-` token に当たった時点で `return False` する
        # ため site が収集されず allow だった（requirements.md § Correction
        # Log (A) 表が正本）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -v codex/20260906-a",
                "git branch -vv codex/20260906-b",
                "git branch --verbose codex/20260906-c",
                "git branch -i codex/20260906-d",
                "git branch --ignore-case codex/20260906-e",
                "git branch -vi codex/20260906-f",
                "git branch -iv codex/20260906-g",
                "git branch --omit-empty codex/20260906-h",
                "git branch --quiet codex/20260906-i",
                "git branch --no-column codex/20260906-j",
                "git branch --no-abbrev codex/20260906-k",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_track_attached_value_short_form(self):
        # AC-1（12形目）: `-tdirect` = `--track=direct` の letter 結合形。
        # 実測: `git branch -tdirect newb` は rc=0 で作成する。
        # design.md D-4 / ADR-7 が正本。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(repo, "git branch -tdirect codex/20260906-l")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_blocks_branch_track_attached_value_non_regression(self):
        # D-5b: `-tinherit` は実 git が ref を作るが、旧実装でも既に rc=2
        # （`t` の部分文字列一致）。非回帰 assertion として固定する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(repo, "git branch -tinherit codex/20260906-m")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_blocks_branch_short_cluster_attached_value_all_gdd_prefixes_r2(self):
        # AC-8（R2、design.md L269 が「維持: RED-3」と明示）: `-fcodex/...`
        # 等の値結合形で branch 名中の文字を letter と誤読しない。
        # 実測確認済み: git 2.50.1（いずれも `error: unknown switch/option`
        # で rc=129、ref は作らない。real-git oracle 由来の deny ではなく、
        # 値結合形を letter 単位走査しない方針そのものを固定する意図的な
        # over-block）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -fcodex/20260906-v",
                "git branch -fgdd/20260906-w",
                "git branch -fclaude/20260906-x",
                "git branch -fcursor/20260906-y",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_branch_neutral_and_value_taking_short_letters_non_regression(
        self,
    ):
        # RED-6（design.md L154/L269 が「維持」と宣言）+ neutral letter /
        # `u` の allow 維持を固定する。実測確認済み: git 2.50.1。
        # `-av`/`-va <名前>` は `-a`/`-r` と同じく「branch 名を取らない」
        # (rc=128, ref 0 件)。`-u main <名前>` は `-u`/`--set-upstream-to`
        # 同様に対象 branch 名を要求し取らない（rc=128, ref 0 件）。
        # `-lv`/`-vl`/`-li`/`-qv`（positional 無し）は rc=0, ref 0 件。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -av codex/20260906-z",
                "git branch -va codex/20260906-aa",
                "git branch -u main codex/20260906-ab",
                "git branch -lv",
                "git branch -vl",
                "git branch -li",
                "git branch -qv",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_allows_branch_list_scope_u_then_creating_letter_widening(self):
        # completion-check Round 2 H-1（AC-12）: `u`が残余ありのvalue-taking
        # letterとして即時returnし、後続のcreating letter（c/C/f/q/t）を
        # 走査しないため`saw_creating`が立たずlist-scope letterのconditional
        # vetoが効いてしまうwidening（deny→allow）を固定する。ここで
        # 固定する2形はcluster長3の代表形10形（全量ではなくcluster長は
        # 開放集合のため列挙しない。widening は3条件（(i) d/D/m/M非含有
        # (ii) 最初の残余ありuより前がa/r/v/i/残余なしuのみでa/rを1つ以上
        # 含む (iii) そのuの残余にcreating letterを1つ以上含む）の必要
        # 十分述語を正本とする）のうちの2形。base（旧`_short_cluster_has`
        # の部分文字列一致）はdenyだった。
        # 実測確認済み: git 2.50.1（`-auc`/`-ruc`とも rc=128・新規ref 0件で
        # fail-openではない。CHANGELOG.md の本タスクエントリ Breaking
        # Contract Changes / docs/adr/2026-09-06-branch-guard-unknown-flag.md
        # § 受容した挙動変化 に3条件の必要十分述語として記載済み）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -auc codex/20260906-widen-a",
                "git branch -ruc codex/20260906-widen-b",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_blocks_branch_list_scope_letter_with_unknown_letter_narrowing(self):
        # completion-check Round 3 M-3（AC-1/AC-4）: narrowing クラス(2)の
        # attached 形（list-scope letter `a`/`r` が未知 letter と同一 cluster
        # に同居する形）を固定する。CHANGELOG の本タスクエントリ Breaking
        # Contract Changes narrowing クラス(2)が代表例として挙げる
        # `-a -l <pattern>`/`-al <pattern>`/`--all --omit-empty <pattern>` は
        # base（PR #41 の1パス cursor walk）では allow だったが、head では
        # `l` が未知 letter として `saw_unknown_flag` を立てるため deny に
        # narrowing する。他の narrowing クラス(1)(3)(4) は既存テストで
        # 固定済みだが、この分岐は未固定だった（他クラスと異なる走査打ち
        # 切り経路で allow へ silent に戻りうる）。
        # 実測確認済み: base/HEAD 突合で3形とも base=allow(rc=0)→
        # head=deny(rc=2)。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -al codex/20260906-narrow-attached",
                "git branch -a -l codex/20260906-narrow-separate",
                "git branch --all --omit-empty codex/20260906-narrow-long",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_negated_long_flags_representative(self):
        # D-5b（design gate Round 4 追補）。実装追加なしで変更1/2が自動的
        # に閉じる想定。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch --no-color codex/20260906-n",
                "git branch --no-quiet codex/20260906-o",
                "git branch --no-ignore-case codex/20260906-p",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_copy_list_scope_long_and_separate_forms(self):
        # D-5b: copy × list-scope の long/分離形。短 cluster 形は現に rc=2。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch --copy --all codex/20260906-q",
                "git branch --all --copy codex/20260906-r",
                "git branch -c -a codex/20260906-s",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_synthetic_unknown_flags(self):
        # AC-2: 未知 flag は作成候補側に倒れる。合成の未知 flag
        # `--gdd-probe-future-flag`/`-Z` で固定（意図的 over-block）。
        # 実測（git 2.50.1）: どちらも `error: unknown option/switch` で
        # rc=129、ref は作らない。real-git oracle 由来の deny ではなく、
        # 未知 flag を fail-closed 側へ倒す方針そのものを固定するテスト
        # である。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch --gdd-probe-future-flag codex/20260906-t",
                "git branch -Z codex/20260906-u",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_unknown_flag_overrides_conditional_veto(self):
        # design.md ADR-6 Round4/D-3: `--cop` は git の unambiguous
        # abbreviation として `--copy` に解決され実 git は ref を作る。
        # veto 条件に saw_unknown_flag を加えて AC-2 の反例を防ぐ。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(repo, "git branch --cop -a codex/20260906-v")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_blocks_branch_conditional_veto_deny_non_regression(self):
        # AC-4: mode letter a/r/u を無条件 veto にすると次の7形が無宣言で
        # allow へ反転する（新 base で現に rc=2、gate2 fallback 経由）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -fa codex/20260906-w",
                "git branch -fr codex/20260906-x",
                "git branch -qa codex/20260906-y",
                "git branch -qr codex/20260906-z",
                "git branch -ta codex/20260906-aa",
                "git branch -fu codex/20260906-ab",
                "git branch -cu main codex/20260906-ac",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_branch_conditional_veto_scan_continuation(self):
        # design.md D-3 Round4/ADR-6: conditional veto letter(a/r/u)は走査
        # を打ち切らず次letterへ進む。-fad/-famは後続のd/mが勝ってallow。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)
            subprocess.run(
                ["git", "branch", "codex/20260906-ad"], cwd=repo, check=True
            )

            for command in [
                "git branch -fad codex/20260906-ad",
                "git branch -fam codex/20260906-ad",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_blocks_branch_double_dash_carveout_after_recognized_short_flag(self):
        # Round4/security MEDIUM-1: 短cluster分類器がseen_recognized_flag
        # を立てないとこれらが deny→allowへ反転する（旧実装は現に rc=2）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -c -- codex/20260906-ae",
                "git branch -C -- codex/20260906-af",
                "git branch -t -- codex/20260906-ag",
                "git branch -q -- codex/20260906-ah",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_branch_verbose_then_double_dash(self):
        # design.md D-5: 変更1の帰結として -v -- <名前> もdenyが正しい
        # （実測: rc=0で作成）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(repo, "git branch -v -- codex/20260906-ai")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_blocks_branch_value_taking_letter_attached_value_narrowing(self):
        # design.md D-4/ADR-7: uの残余はattached valueと断定しvetoしない。
        # 現行baseは -umain が `m` の偶然一致でallow（実測rc=128、narrowing
        # としてCHANGELOG明記対象）。-tv/-vtも同規則で固定する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -umain codex/20260906-aj",
                "git branch -tv codex/20260906-ak",
                "git branch -vt codex/20260906-al",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_branch_new_mode_flags_standalone(self):
        # design.md 変更2: R2追加のnon-creating long/short（実測でref非作成
        # 確認済み）。名前引数付きでもallowのままであることを固定する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch --show-current codex/20260906-am",
                "git branch --edit-description codex/20260906-an",
                "git branch --unset-upstream codex/20260906-ao",
                "git branch --contains main codex/20260906-ap",
                "git branch --no-contains main codex/20260906-aq",
                "git branch --merged main codex/20260906-ar",
                "git branch --no-merged main codex/20260906-as",
                "git branch --points-at main codex/20260906-at",
                "git branch --all codex/20260906-au",
                "git branch --remotes codex/20260906-av",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_allows_branch_unconditional_veto_safe_with_creating_flag(self):
        # design.md D-3 ADR-6: unconditional vetoは作成系flagと併用でも
        # 常にveto（実測でいずれもref非作成）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git branch -f --list codex/20260906-aw",
                "git branch --list -f codex/20260906-ax",
                "git branch -f --show-current codex/20260906-ay",
                "git branch -f --merged main codex/20260906-az",
                "git branch --contains main -f codex/20260906-ba",
                "git branch -f --edit-description codex/20260906-bb",
                "git branch -f --set-upstream-to=main codex/20260906-bc",
                "git branch -f --unset-upstream codex/20260906-bd",
                "git branch -f --points-at main codex/20260906-be",
                "git branch --no-contains main -f codex/20260906-bf",
                "git branch --no-merged main -f codex/20260906-bg",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
