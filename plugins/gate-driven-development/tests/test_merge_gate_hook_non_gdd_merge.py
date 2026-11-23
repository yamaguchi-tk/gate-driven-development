"""merge gate: GDD の対象と判定できない merge を不足として通知しない（非 git cwd 起点）。

事象（2026-09-15 / 2026-09-18）: 非 git ディレクトリで起動したセッションが、
GDD と無関係な repo（marker なし）の PR を `gh pr merge -R owner/repo N` /
`cd <clone> && gh pr merge N` で merge すると、root 候補が全滅して
`repo-root-unresolvable` で止まっていた。cwd が「marker の無い git repo」なら
同じコマンドは従来から exit 0 で通っており、非 git cwd だけが止まる非対称だった。

新しい契約:
- 実行先（cwd / payload cwd / cd 先）が確定でき、そのどれの祖先にも marker が
  無い merge は、GDD の対象外として通す（exit 0）。marker の探索は git に頼らない
  （git 不在・`git rev-parse` 失敗で marker を見落とすと、GDD 管理下の merge が
  無検査で通るため）。
- 解析未完走・縮退・曖昧な chdir・実在しない（または相対の）実行先は、従来どおり
  `repo-root-unresolvable` として通知する。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    PLUGIN_ROOT,
    _init_bare_repo,
    _new_repo_with_marker_and_pr,
    _run_hook,
    _write_state,
)

PRE_PR_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-pr-gate-hook.sh"


def _ledger(home: Path) -> Path:
    return home / ".claude" / ".gdd-hook-state" / "gdd-pr-roots"


def _register(home: Path, *roots: Path) -> None:
    ledger = _ledger(home)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as fh:
        for root in roots:
            fh.write(f"{root}\n")


def _clone_like(parent: Path, name: str, origin: str) -> Path:
    """marker を持たない git repo（origin だけ設定）。root checkout や Renovate 用 clone 相当。"""
    repo = _init_bare_repo(parent, name)
    subprocess.run(["git", "remote", "add", "origin", origin], cwd=repo, check=True)
    return repo


def _run_pre_pr(cwd: Path, home: Path, command: str = "gh pr create --title t --body ok", extra_env=None, timeout=20):
    env = {k: v for k, v in os.environ.items() if k not in ("GH_HOST", "GH_REPO", "GDD_HOOK_STATE_DIR")}
    env.update({
        "HOME": str(home),
        "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
        "CLAUDE_CODE_SESSION_ID": "test-session",
    })
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(PRE_PR_HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        capture_output=True, text=True, env=env, cwd=str(cwd), timeout=timeout,
    )


def _git_failing_path(tmp: Path) -> str:
    """`git` だけが常に失敗する PATH（dubious ownership 等の rev-parse 失敗を再現）。"""
    stub = tmp / "git-fail-stub"
    stub.mkdir()
    fake = stub / "git"
    fake.write_text("#!/bin/sh\nexit 128\n", encoding="utf-8")
    fake.chmod(0o755)
    return f"{stub}:{os.environ.get('PATH', '')}"


def _git_absent_path(tmp: Path) -> str:
    """`git` だけが存在しない PATH（他のコマンドは元の PATH の先頭一致を symlink で残す）。"""
    farm = tmp / "no-git-farm"
    farm.mkdir()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory or not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if name == "git" or (farm / name).exists() or (farm / name).is_symlink():
                continue
            source = Path(directory) / name
            if source.is_file() and os.access(source, os.X_OK):
                (farm / name).symlink_to(source)
    return str(farm)


class NonGddMergePassesTests(unittest.TestCase):
    """AC-1/AC-2: 非 git cwd から marker の無い repo への merge は通る。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.non_repo = self.tmp / "work-claude"
        self.non_repo.mkdir()
        self.plain = _init_bare_repo(self.tmp, "plain-clone")

    def _assert_passes(self, result):
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_repo_flag_merge_from_non_git_cwd_passes(self):
        # AC-1: Renovate の PR を自動マージする運用が実際に使う形。
        for command in (
            "gh pr merge -R example-org/infra-repo 12",
            "gh pr merge -R example-org/infra-repo 12 --squash --delete-branch",
            "gh pr merge https://github.com/example-org/infra-repo/pull/12 --squash",
        ):
            with self.subTest(command=command):
                self._assert_passes(
                    _run_hook({"tool_input": {"command": command}}, self.non_repo, self.home)
                )

    def test_cd_into_repo_without_marker_passes(self):
        # AC-2: `cd <marker を持たない repo> && gh pr merge N`。
        for sep in ("&&", ";"):
            with self.subTest(sep=sep):
                command = f"cd {self.plain} {sep} gh pr merge 12"
                self._assert_passes(
                    _run_hook({"tool_input": {"command": command}}, self.non_repo, self.home)
                )

    def test_cd_into_clone_without_marker_passes_with_ledger_present(self):
        # AC-2 の定常状態（PR後-1 の medium）: 一度 `gh pr create` を通ると台帳ができる。
        # 台帳に GDD の PR があっても、origin を持つ無関係な clone への merge は通る。
        gdd = _new_repo_with_marker_and_pr(self.tmp, "infra-gdd", pr=12, commit=False)
        _register(self.home, gdd)
        clone = _clone_like(self.tmp, "renovate-clone", "https://github.com/example-org/infra-repo.git")
        for sep in ("&&", ";"):
            with self.subTest(sep=sep):
                command = f"cd {clone} {sep} gh pr merge 12 --squash"
                self._assert_passes(
                    _run_hook({"tool_input": {"command": command}}, self.non_repo, self.home)
                )

    def test_payload_cwd_repo_without_marker_passes(self):
        # AC-2 の payload cwd 形（旧 test_payload_cwd_without_marker_blocks_... の反転）。
        self._assert_passes(
            _run_hook(
                {"tool_input": {"command": "gh pr merge 12", "cwd": str(self.plain)}},
                self.non_repo, self.home,
            )
        )

    def test_cd_into_non_git_directory_passes(self):
        other = self.tmp / "plain-dir"
        other.mkdir()
        self._assert_passes(
            _run_hook(
                {"tool_input": {"command": f"cd {other} && gh pr merge -R acme/widgets 12"}},
                self.non_repo, self.home,
            )
        )


class GddMergeStillBlocksTests(unittest.TestCase):
    """AC-3/AC-4 と fail-open 3 ケース: 通してはいけない入力は不足として通知されたまま。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.non_repo = self.tmp / "work-claude"
        self.non_repo.mkdir()
        self.gdd = _new_repo_with_marker_and_pr(self.tmp, "gdd-repo", pr=7)

    def _assert_blocks(self, result, code=None):
        self.assertEqual(result.returncode, 0)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        if code:
            self.assertIn(code, result.stdout)

    def test_cd_into_marker_repo_still_checks_evidence(self):
        # AC-3: marker を持つ repo の merge は、従来どおり承認証跡を検査する。
        self._assert_blocks(
            _run_hook(
                {"tool_input": {"command": f"cd {self.gdd} && gh pr merge 7"}},
                self.non_repo, self.home,
            ),
            "approval-missing",
        )

    def test_marker_repo_blocks_when_git_rev_parse_fails(self):
        # fail-open ケース「不足を通知すべき入力が通過扱いになる」: rev-parse が失敗すると
        # root 候補ループは marker repo を見落とす。marker は git に頼らず探すので不足として通知される。
        env = {"PATH": _git_failing_path(self.tmp)}
        sub = self.gdd / "sub"
        sub.mkdir()
        for command, payload_cwd in (
            (f"cd {self.gdd} && gh pr merge 7", None),
            (f"cd {sub} && gh pr merge 7", None),
            ("gh pr merge 7", str(sub)),
        ):
            with self.subTest(command=command, payload_cwd=payload_cwd):
                tool_input = {"command": command}
                if payload_cwd:
                    tool_input["cwd"] = payload_cwd
                self._assert_blocks(
                    _run_hook({"tool_input": tool_input}, self.non_repo, self.home, extra_env=env),
                    "repo-root-unresolvable",
                )

    def test_marker_repo_blocks_when_git_is_absent(self):
        # fail-open ケース「判定できないときに通ってしまう」: git 不在では候補ループが
        # 丸ごと飛ぶ。marker の探索は git に依存しないので不足として通知される。
        env = {"PATH": _git_absent_path(self.tmp)}
        self.assertNotEqual(
            subprocess.run(["bash", "-c", "command -v git"], env=env, capture_output=True).returncode,
            0,
        )
        self._assert_blocks(
            _run_hook(
                {"tool_input": {"command": f"cd {self.gdd} && gh pr merge 7"}},
                self.non_repo, self.home, extra_env=env,
            ),
            "repo-root-unresolvable",
        )

    def test_symlink_into_marker_repo_blocks_when_git_rev_parse_fails(self):
        # 論理パスの祖先に marker が無くても、物理パスの祖先にあれば不足として通知する。
        link = self.tmp / "link-into-gdd"
        link.symlink_to(self.gdd / ".claude")
        env = {"PATH": _git_failing_path(self.tmp)}
        self._assert_blocks(
            _run_hook(
                {"tool_input": {"command": f"cd {link} && gh pr merge 7"}},
                self.non_repo, self.home, extra_env=env,
            ),
            "repo-root-unresolvable",
        )

    def test_ambiguous_chdir_still_blocks(self):
        # 実行先を 1 つに確定できない形は、marker の有無を問わず不足として通知する。
        plain = _init_bare_repo(self.tmp, "plain-clone")
        for command in (
            f"pushd {plain} && gh pr merge 7",
            f"(cd {plain} && gh pr merge 7)",
            f"cd {plain} && cd {self.gdd} && gh pr merge 7",
            f"bash -c 'cd {self.gdd} && gh pr merge 7'",
        ):
            with self.subTest(command=command):
                self._assert_blocks(
                    _run_hook({"tool_input": {"command": command}}, self.non_repo, self.home),
                    "repo-root-unresolvable",
                )

    def test_unresolvable_execution_target_still_blocks(self):
        # 実在しない cd 先・payload cwd、相対の payload cwd は、実行先を確定できない。
        (self.non_repo / "rel").mkdir()
        for tool_input in (
            {"command": f"cd {self.tmp}/no-such-dir && gh pr merge 7"},
            {"command": "gh pr merge 7", "cwd": str(self.tmp / "no-such-dir")},
            {"command": "gh pr merge 7", "cwd": "rel"},
        ):
            with self.subTest(tool_input=tool_input):
                self._assert_blocks(
                    _run_hook({"tool_input": tool_input}, self.non_repo, self.home),
                    "repo-root-unresolvable",
                )

    def test_parse_failure_still_blocks(self):
        # AC-4 / fail-open ケース「例外で guard 全体が落ちる」: python3 が動かない。
        stub = self.tmp / "py-stub"
        stub.mkdir()
        fake = stub / "python3"
        fake.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        fake.chmod(0o755)
        self._assert_blocks(
            _run_hook(
                {"tool_input": {"command": "gh pr merge -R owner/repo 7"}},
                self.non_repo, self.home,
                extra_env={"PATH": f"{stub}:{os.environ.get('PATH', '')}"},
            ),
            "repo-root-unresolvable",
        )

    def test_degraded_merge_still_blocks(self):
        # AC-4: shlex がクォート解析に失敗して縮退した merge は不足として通知する。
        self._assert_blocks(
            _run_hook(
                {"tool_input": {"command": "gh pr merge -R owner/repo 7 'unterminated"}},
                self.non_repo, self.home,
            ),
            "repo-root-unresolvable",
        )



class GddPrLedgerTests(unittest.TestCase):
    """方針メモ-2: GDD の PR は PR 単位（owner/repo + 番号）の台帳で判定する。

    台帳 `~/.claude/.gdd-hook-state/gdd-pr-roots` は pre-PR gate が GDD worktree の root を
    書き、merge gate が「marker が無いので通す」経路（root 未解決 / git cwd の marker
    不在 / 共通ディレクトリで通した実行先 / 対象を repo つきで明示した merge）で、各 root の `.steering/*/state.md` の `PR URL`
    と照合する。共通ディレクトリの経路は test_merge_gate_same_repo_worktree.py で見る。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.non_repo = self.tmp / "work-claude"
        self.non_repo.mkdir()
        # GDD worktree（PR URL: https://github.com/acme/infra-gdd/pull/7）。
        self.gdd = _new_repo_with_marker_and_pr(self.tmp, "infra-gdd", pr=7, commit=False)

    def _run(self, command, cwd=None, **kw):
        return _run_hook({"tool_input": {"command": command}}, cwd or self.non_repo, self.home, **kw)

    def _assert_blocks(self, result):
        self.assertEqual(result.returncode, 0)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("repo-root-unresolvable", result.stdout)

    def _assert_passes(self, result):
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_registered_gdd_pr_blocks_from_non_git_cwd(self):
        # codex-1 の再現: 非 git cwd から -R / URL で GDD の PR を merge する。
        _register(self.home, self.gdd)
        for command in (
            "gh pr merge -R acme/infra-gdd 7",
            "gh pr merge -R ACME/Infra-GDD 7 --squash",
            "gh pr merge --repo=acme/infra-gdd 7",
            "gh pr merge https://github.com/acme/infra-gdd/pull/7",
        ):
            with self.subTest(command=command):
                self._assert_blocks(self._run(command))

    def test_other_pr_or_repo_passes_even_when_ledger_has_entries(self):
        # 番号だけで照合しない（別 repo の Renovate #7 を通知しない）。
        _register(self.home, self.gdd)
        for command in (
            "gh pr merge -R acme/infra-gdd 8",
            "gh pr merge -R example-org/infra-repo 7",
            "gh pr merge https://github.com/acme/other/pull/7",
        ):
            with self.subTest(command=command):
                self._assert_passes(self._run(command))

    def test_cd_into_clone_without_marker_matches_by_origin(self):
        _register(self.home, self.gdd)
        clone = _clone_like(self.tmp, "clone", "https://github.com/acme/infra-gdd.git")
        self._assert_blocks(self._run(f"cd {clone} && gh pr merge 7"))
        self._assert_passes(self._run(f"cd {clone} && gh pr merge 8"))

    def test_git_cwd_without_marker_is_checked_too(self):
        # 広い側（step 5 の marker 不在 exit 0 経路）: root checkout から GDD の PR を merge。
        _register(self.home, self.gdd)
        clone = _clone_like(self.tmp, "root-checkout", "git@github.com:acme/infra-gdd.git")
        self._assert_blocks(self._run("gh pr merge 7", cwd=clone))
        self._assert_blocks(self._run("gh pr merge -R acme/infra-gdd 7", cwd=clone))
        self._assert_passes(self._run("gh pr merge 8", cwd=clone))
        unrelated = _clone_like(self.tmp, "unrelated", "https://github.com/acme/unrelated.git")
        self._assert_passes(self._run("gh pr merge 7", cwd=unrelated))
        self._assert_blocks(self._run("gh pr merge -R acme/infra-gdd 7", cwd=unrelated))

    def test_set_default_to_origin_slug_is_checked(self):
        # PR後-1 の high: origin の gh-resolved が `base` でも、origin と同じ repo を指す
        # slug・URL（手で設定した場合など）でも、origin で照合する（3 組解決 (c) と同じ受理集合）。
        _register(self.home, self.gdd)
        clone = _clone_like(self.tmp, "root-checkout-sd", "git@github.com:acme/infra-gdd.git")
        for resolved in ("base", "acme/infra-gdd", "ACME/Infra-GDD", "https://github.com/acme/infra-gdd"):
            subprocess.run(["git", "config", "remote.origin.gh-resolved", resolved],
                           cwd=clone, check=True)
            with self.subTest(resolved=resolved, path="git-cwd"):
                self._assert_blocks(self._run("gh pr merge 7", cwd=clone))
                self._assert_passes(self._run("gh pr merge 8", cwd=clone))
            with self.subTest(resolved=resolved, path="root-unresolved"):
                self._assert_blocks(self._run(f"cd {clone} && gh pr merge 7"))
                self._assert_passes(self._run(f"cd {clone} && gh pr merge 8"))

    def test_set_default_elsewhere_or_garbage_stays_unknown(self):
        # fail-open 側: origin と別の repo・解釈できない値は unknown（照合しない）。
        # git cwd の経路は main と同じく通り、root 未解決の経路は不足として通知される。hook は落ちない。
        _register(self.home, self.gdd)
        clone = _clone_like(self.tmp, "root-checkout-sd2", "https://github.com/acme/infra-gdd.git")
        for resolved in ("acme/other", "not a slug", "/"):
            subprocess.run(["git", "config", "remote.origin.gh-resolved", resolved],
                           cwd=clone, check=True)
            with self.subTest(resolved=resolved):
                result = self._run("gh pr merge 7", cwd=clone)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn('"hookEventName"', result.stdout)
                self._assert_blocks(self._run(f"cd {clone} && gh pr merge 7"))

    def test_other_remote_with_gh_resolved_stays_unknown(self):
        # 独立-2 の H1 / #127: origin 以外の remote（fork の upstream など）に gh-resolved が
        # あると、gh はそちらを対象にしうる。origin の値によらず unknown にする。
        # root 未解決の経路は不足として通知され、git cwd の経路は main と同じく通る。
        _register(self.home, self.gdd)
        for origin_resolved in (None, "base", "me/infra-gdd"):
            fork = _clone_like(self.tmp, f"fork-{origin_resolved or 'unset'}".replace("/", "-"),
                               "https://github.com/me/infra-gdd.git")
            subprocess.run(["git", "remote", "add", "upstream", "https://github.com/acme/infra-gdd.git"],
                           cwd=fork, check=True)
            subprocess.run(["git", "config", "remote.upstream.gh-resolved", "base"], cwd=fork, check=True)
            if origin_resolved:
                subprocess.run(["git", "config", "remote.origin.gh-resolved", origin_resolved],
                               cwd=fork, check=True)
            with self.subTest(origin_resolved=origin_resolved):
                self._assert_blocks(self._run(f"cd {fork} && gh pr merge 7"))
                result = self._run("gh pr merge 7", cwd=fork)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn('"hookEventName"', result.stdout)

    def test_unknown_target_falls_back_to_main_verdict(self):
        # 方針メモ-3（(a′)）: 対象 PR を特定できない形は台帳で照合せず、その経路の main の
        # 判定に戻す。root 未解決の経路は不足として通知、git cwd の marker 不在の経路は exit 0。
        _register(self.home, self.gdd)
        clone = _clone_like(self.tmp, "root-checkout-2", "https://github.com/acme/infra-gdd.git")
        unrelated = _clone_like(self.tmp, "unrelated-2", "https://github.com/acme/unrelated.git")
        for command, cwd in (
            ("gh pr merge", clone),
            ("gh pr merge --squash some-branch", clone),
            ("GH_REPO=acme/infra-gdd gh pr merge 7", unrelated),
        ):
            with self.subTest(path="git-cwd", command=command):
                self._assert_passes(self._run(command, cwd=cwd))
        # 連結した merge は merge ごとの組で照合する（Issue #438）。台帳の PR を含めば不足として通知する。
        self._assert_blocks(self._run("gh pr merge -R acme/infra-gdd 7 && gh pr merge -R acme/other 8", cwd=unrelated))
        for command in (
            "GH_REPO=acme/whatever gh pr merge 9",
            "GH_REPO=acme/whatever gh pr merge -R example-org/infra-repo 7",
            "gh pr merge -R example-org/infra-repo some-branch",
        ):
            with self.subTest(path="root-unresolved", command=command):
                self._assert_blocks(self._run(command))
        # repo を特定できない実行先（origin 無し・gh repo set-default が origin 以外）と、
        # URL が残ったまま unresolvable になる形も、root 未解決の経路では main と同じく不足として通知。
        no_origin = _init_bare_repo(self.tmp, "no-origin")
        set_default = _clone_like(self.tmp, "set-default", "https://github.com/acme/unrelated.git")
        subprocess.run(["git", "config", "remote.origin.gh-resolved", "acme/infra-gdd"],
                       cwd=set_default, check=True)
        for command in (
            f"cd {no_origin} && gh pr merge 7",
            f"cd {set_default} && gh pr merge 7",
            "gh pr merge https://github.com/acme/other/pull/7 extra",
        ):
            with self.subTest(path="root-unresolved", command=command):
                self._assert_blocks(self._run(command))

    def test_chained_merges_do_not_hide_a_gdd_pr(self):
        # codex-2 C2: 複数 merge の連結で parser は番号を消し repo_flag に最後の値を残す。
        # 先頭の GDD PR が最後の repo での照合に隠れて通らないこと（両順序）。
        _register(self.home, self.gdd)
        for command in (
            "gh pr merge -R acme/infra-gdd 7 && gh pr merge -R acme/other 8",
            "gh pr merge -R acme/other 8 && gh pr merge -R acme/infra-gdd 7",
            "gh pr merge -R example-org/x 1 && gh pr merge https://github.com/acme/infra-gdd/pull/7",
        ):
            with self.subTest(command=command):
                self._assert_blocks(self._run(command))

    def test_env_repo_does_not_turn_a_renovate_merge_into_a_number_only_match(self):
        # codex-2 C3: GH_REPO 付きでも「番号だけで台帳と一致」させない。git cwd の marker
        # 不在の経路は main と同じく通す（別 repo の GDD PR #7 が台帳にあっても）。
        _register(self.home, self.gdd)
        renovate = _clone_like(self.tmp, "renovate-clone", "https://github.com/example-org/renovate-repo.git")
        self._assert_passes(
            self._run("GH_REPO=acme/default gh pr merge -R example-org/renovate-repo 7", cwd=renovate)
        )

    def test_missing_or_stale_ledger_passes(self):
        self._assert_passes(self._run("gh pr merge -R acme/infra-gdd 7"))
        _register(self.home, self.tmp / "deleted-worktree")
        self._assert_passes(self._run("gh pr merge -R acme/infra-gdd 7"))

    def test_unreadable_ledger_or_state_fails_closed(self):
        # fail-open ケース「判定できないときに通ってしまう」。
        if os.geteuid() == 0:
            self.skipTest("root は chmod 000 を読めてしまう")
        _register(self.home, self.gdd)
        state = self.gdd / ".steering" / "20260101-demo" / "state.md"
        state.chmod(0)
        try:
            self._assert_blocks(self._run("gh pr merge -R acme/other 3"))
        finally:
            state.chmod(0o644)
        ledger = _ledger(self.home)
        ledger.chmod(0)
        try:
            self._assert_blocks(self._run("gh pr merge -R acme/other 3"))
        finally:
            ledger.chmod(0o644)

    def test_ledger_read_does_not_crash_without_home(self):
        # fail-open ケース「例外で guard 全体が落ちる」: HOME 未設定（set -u）でも無出力で
        # 落ちない。台帳の場所が決まらない = unreadable で、経路ごとに main と同じ判定になる
        # （root 未解決は不足として通知、git cwd の marker 不在は exit 0）。
        clone = _clone_like(self.tmp, "no-home", "https://github.com/acme/unrelated.git")
        self._assert_passes(_run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, clone, self.home, drop_env=("HOME",),
        ))
        self._assert_blocks(_run_hook(
            {"tool_input": {"command": "gh pr merge -R acme/infra-gdd 7"}}, self.non_repo, self.home,
            drop_env=("HOME",),
        ))

    def test_verdict_by_path_table(self):
        # 方針メモ-3/4 の不変条件: 台帳に hit した場合だけ不足として通知する側へ変え、それ以外（miss /
        # unknown / unreadable）は経路ごとに main と同じ判定（root 未解決 = 不足として通知、git cwd の
        # marker 不在 = exit 0）。ただし root 未解決の miss は AC-1/AC-2 の意図した緩和で通す。
        if os.geteuid() == 0:
            self.skipTest("root は chmod 000 を読めてしまう")
        _register(self.home, self.gdd)
        unrelated = _clone_like(self.tmp, "unrelated-table", "https://github.com/acme/unrelated.git")
        ledger = _ledger(self.home)
        state = self.gdd / ".steering" / "20260101-demo" / "state.md"
        verdicts = {
            "hit": ("gh pr merge -R acme/infra-gdd 7", None),
            "miss": ("gh pr merge -R acme/infra-gdd 8", None),
            "unknown": ("GH_REPO=acme/x gh pr merge 7", None),
            "unreadable-ledger": ("gh pr merge -R acme/infra-gdd 8", ledger),
            "unreadable-state": ("gh pr merge -R acme/infra-gdd 8", state),
        }
        expected = {
            ("root-unresolved", "hit"): True, ("root-unresolved", "miss"): False,
            ("root-unresolved", "unknown"): True, ("root-unresolved", "unreadable-ledger"): True,
            ("root-unresolved", "unreadable-state"): True,
            ("git-cwd", "hit"): True, ("git-cwd", "miss"): False,
            ("git-cwd", "unknown"): False, ("git-cwd", "unreadable-ledger"): False,
            ("git-cwd", "unreadable-state"): False,
        }
        for (path, verdict), blocks in expected.items():
            command, locked = verdicts[verdict]
            cwd = self.non_repo if path == "root-unresolved" else unrelated
            with self.subTest(path=path, verdict=verdict):
                if locked:
                    locked.chmod(0)
                try:
                    result = self._run(command, cwd=cwd)
                finally:
                    if locked:
                        locked.chmod(0o644)
                (self._assert_blocks if blocks else self._assert_passes)(result)

    def test_pre_pr_gate_registers_root_and_merge_gate_blocks(self):
        # 入口から効果まで: pre-PR gate（gh pr create）が台帳へ書き、merge gate が読む。
        worktree = _init_bare_repo(self.tmp, "gdd-wt")
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/acme/gdd-wt.git"],
                       cwd=worktree, check=True)
        _write_state(worktree, active=True, pr_url="https://github.com/acme/gdd-wt/pull/11")
        _run_pre_pr(worktree, self.home)
        _run_pre_pr(worktree, self.home)
        self.assertEqual(_ledger(self.home).read_text().splitlines(), [str(worktree.resolve())])
        self._assert_blocks(self._run("gh pr merge -R acme/gdd-wt 11"))
        self._assert_passes(self._run("gh pr merge -R acme/gdd-wt 12"))

    def test_pre_pr_gate_does_not_register_outside_active_gdd(self):
        worktree = _init_bare_repo(self.tmp, "not-active")
        _write_state(worktree, active=False, pr_url="https://github.com/acme/not-active/pull/1")
        _run_pre_pr(worktree, self.home)
        self.assertFalse(_ledger(self.home).exists())

    def test_pre_pr_gate_verdict_is_unchanged_when_ledger_write_fails(self):
        # 書き込み失敗で pre-PR gate の判定を変えない（state dir がファイルで mkdir できない）。
        worktree = _init_bare_repo(self.tmp, "write-fail")
        _write_state(worktree, active=True)
        baseline = _run_pre_pr(worktree, self.home, extra_env={"GDD_HOOK_STATE_DIR": str(self.tmp / "sd")})
        blocker = self.tmp / "as-file"
        blocker.write_text("x")
        broken = _run_pre_pr(worktree, self.home, extra_env={"GDD_HOOK_STATE_DIR": str(blocker / "sub")})
        self.assertEqual(broken.returncode, baseline.returncode)
        self.assertEqual(broken.stdout, baseline.stdout)
        self.assertTrue((self.tmp / "sd" / "gdd-pr-roots").exists())


if __name__ == "__main__":
    unittest.main()
