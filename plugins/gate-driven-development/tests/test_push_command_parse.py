"""Unit tests for hooks/scripts/lib/push_command_parse.py.

新 python module は `run-*.sh` 命名でないため hooks-wiring-lint の対象外。
未参照化を検出するため、この単体テストから直接 import する（design.md §テスト方針）。

このファイルには、git global option と `git push` option の一覧を実 git・実 bash と突き合わせるテストと、
一覧に無い global flag でも push を検出できること（`UnknownGlobalFlagPropertyTests`）を確かめるテストを置く。
ほかの主題は `test_push_command_parse_lexing.py`（字句・分割）・`test_push_command_parse_push_detection.py`（push の検出）・
`test_push_command_parse_push_target.py`（push 対象の解決）・`test_push_command_parse_optout.py`（opt-out と副作用の無い push）にある。
"""
from __future__ import annotations

import functools
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

import push_command_parse as pcp  # noqa: E402
import git_command_parse as gcp  # noqa: E402


GIT_BINARY = shutil.which("git")


BASH_BINARY = shutil.which("bash")


# 実 git への arity 問い合わせで使う引数（flag ごとに妥当な形が違うもののみ指定）。
_PROBE_ARGUMENTS = {
    "-C": ".",  # 実在するディレクトリでないと `git -C` 自体が fatal になる
    "-c": "user.name=probe",
    "--config-env": "user.name=HOME",  # 実在する環境変数名でないと fatal になる
    "--shallow-file": os.devnull,
}


@functools.lru_cache(maxsize=None)
def git_consumes_separate_argument(flag: str) -> bool | None:
    """実 git に問い合わせて `flag` が**分離引数**を消費するか判定する。

    `git <flag> <arg> version` が `git version ...` を出力すれば、`<arg>` は flag に
    消費され `version` が subcommand として解釈されている。消費しない flag では
    `<arg>` 自体が subcommand 扱いになり `version` は出力されない。
    インストール済み git が知らない option（バージョン差）では `None` を返す。

    テストの期待値をハードコードの一覧ではなく **実 git の挙動から導出**するための
    oracle。`push_command_parse` 側の一覧が git の仕様とずれたら検出できる。
    """
    if GIT_BINARY is None:
        return None
    argument = _PROBE_ARGUMENTS.get(flag, "probe-value")
    completed = subprocess.run(
        [GIT_BINARY, flag, argument, "version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    combined = f"{completed.stdout}{completed.stderr}"
    if "unknown option" in combined or "unknown argument" in combined:
        return None
    return completed.returncode == 0 and combined.startswith("git version")


#: `git push -h` の option 行末に現れる値プレースホルダ（`<repository>` /
#: `(check|on-demand|no)`）。**空白区切りで後続する**ものだけが分離引数であり、
#: `--force-with-lease[=<refname>:<expect>]` のような `[=...]` 形は
#: 付加形（分離引数を消費しない）なのでここには一致しない。
_PUSH_OPTION_ARGUMENT_RE = re.compile(r"\s(<[^>]+>|\([^)]+\))$")


#: `--[no-]branches  alias of --all` の alias 宣言。
_PUSH_OPTION_ALIAS_RE = re.compile(r"^alias of (--[\w-]+)")


#: `--[no-]signed[=(yes|no|if-asked)]` のような付加値の綴りを名前から落とす。
_PUSH_OPTION_ATTACHED_VALUE_RE = re.compile(r"\[=.*\]$")


def _parse_push_option_spec(spec: str) -> list[tuple[str, bool]]:
    """`-o, --[no-]push-option <server-specific>` 形の spec を `(名前, arity)` へ分解する。

    `--[no-]foo` は肯定形 `--foo` と否定形 `--no-foo` の両方を生む。否定形は値を
    取らないため arity は常に False にする。
    """
    match = _PUSH_OPTION_ARGUMENT_RE.search(spec)
    takes_argument = match is not None
    head = spec[: match.start()] if match else spec
    names: list[tuple[str, bool]] = []
    for piece in head.split(","):
        piece = _PUSH_OPTION_ATTACHED_VALUE_RE.sub("", piece.strip())
        if not piece.startswith("-"):
            continue
        if "[no-]" in piece:
            names.append((piece.replace("[no-]", ""), takes_argument))
            names.append((piece.replace("[no-]", "no-"), False))
        else:
            names.append((piece, takes_argument))
    return names


@functools.lru_cache(maxsize=None)
def real_git_push_options() -> tuple[tuple[str, bool, str], ...]:
    """`git push -h` を解析し `(option 名, 分離引数を取るか, 説明)` の一覧を返す。

    `git_consumes_separate_argument` が git global flag に対して行うのと同じことを
    `git push` の subcommand option に対して行う oracle。期待値をハードコードの
    一覧や man の二次情報ではなく **インストール済み実 git の宣言**から導出するため、
    `_KNOWN_VALUE_FLAGS` / `_AMBIGUOUS_FLAGS` が git の仕様とずれたら検出できる。

    `git push -h` は usage を stdout / stderr のどちらかに出し終了コードも
    バージョン差があるため、両方を連結して解析し returncode は見ない。
    解析できなければ空 tuple を返し、呼び出し側が skip する。
    """
    if GIT_BINARY is None:
        return ()
    completed = subprocess.run(
        [GIT_BINARY, "push", "-h"], capture_output=True, text=True, timeout=30
    )
    entries: list[tuple[str, bool, str]] = []
    pending: list[tuple[str, bool]] | None = None
    for line in f"{completed.stdout}{completed.stderr}".splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip())
        if indent and stripped.startswith("-"):
            # 新しい option 行。説明が同じ行にあれば 2 個以上の空白で区切られる
            parts = re.split(r"\s{2,}", stripped, maxsplit=1)
            description = parts[1] if len(parts) > 1 else ""
            names = _parse_push_option_spec(parts[0])
            if description:
                entries.extend((name, arity, description) for name, arity in names)
                pending = None
            else:
                pending = names
        elif pending is not None and indent:
            # 直前の option 行が長く、説明だけが次行へ折り返された形
            entries.extend((name, arity, stripped) for name, arity in pending)
            pending = None
    if pending is not None:
        entries.extend((name, arity, "") for name, arity in pending)
    return tuple(entries)


class GitGlobalFlagArityTests(unittest.TestCase):
    """global flag 一覧の正しさを**実 git の挙動から**検証する（flag の引数の数を取り違える欠陥のクラス）。

    一覧は「検出漏れを防ぐため」ではなく「push を引数として消費する形を過検出
    しないため」にだけ使う。したがって検証すべき述語は 2 つ:

    1. 一覧メンバは実 git でも分離引数を消費する（消費しないなら一覧から外す）
    2. 分離引数形 `git <flag> <arg> push` は必ず検出される（一覧に無くても）

    期待値 `EXPECTED_ARG_TAKING_FLAGS` は module の定数を参照せずテスト側に literal で
    置く。module の集合を読んで回すと、集合からメンバを削る mutation が「反復対象から
    も消える」ため検出できない（同語反復テストになる）。
    """

    EXPECTED_ARG_TAKING_FLAGS = frozenset(
        {
            "-C",
            "-c",
            "--git-dir",
            "--work-tree",
            "--namespace",
            "--config-env",
            "--attr-source",
            "--shallow-file",
        }
    )

    def test_module_set_matches_expected_flags(self) -> None:
        self.assertEqual(
            set(pcp.GIT_GLOBAL_FLAGS_WITH_ARGUMENT),
            set(self.EXPECTED_ARG_TAKING_FLAGS),
        )

    def test_every_expected_flag_consumes_separate_argument_in_real_git(self) -> None:
        if GIT_BINARY is None:
            self.skipTest("git binary not available")
        for flag in sorted(self.EXPECTED_ARG_TAKING_FLAGS):
            with self.subTest(flag=flag):
                consumes = git_consumes_separate_argument(flag)
                if consumes is None:
                    self.skipTest(f"installed git does not know {flag}")
                self.assertTrue(
                    consumes,
                    f"{flag} は実 git で分離引数を消費しない。一覧から外すこと",
                )

    def test_expected_flag_consuming_push_is_not_a_push(self) -> None:
        """`git <flag> push` は push が flag の引数なので非検出（集合メンバシップの固定）。

        集合から 1 メンバを削除する mutation は、このテストで必ず落ちる。
        """
        if GIT_BINARY is None:
            self.skipTest("git binary not available")
        for flag in sorted(self.EXPECTED_ARG_TAKING_FLAGS):
            with self.subTest(flag=flag):
                if git_consumes_separate_argument(flag) is not True:
                    self.skipTest(f"installed git does not know {flag}")
                tokens = pcp.tokenize(f"git {flag} push")
                self.assertFalse(pcp.is_git_push(tokens)[0])

    def test_separate_argument_form_is_detected_for_expected_flags(self) -> None:
        for flag in sorted(self.EXPECTED_ARG_TAKING_FLAGS):
            with self.subTest(flag=flag):
                argument = _PROBE_ARGUMENTS.get(flag, "probe-value")
                tokens = pcp.tokenize(f"git {flag} {argument} push origin main")
                self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_real_git_flags_outside_the_declared_set_are_detected(self) -> None:
        """一覧に載せていない実在 global flag でも検出できる（fail-closed 設計）。

        ADR-3（T-2）で `GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT` に登録した no-arg flag
        （`--no-pager` / `--paginate` / `--bare` / `--literal-pathspecs` /
        `--no-replace-objects` / `--no-optional-locks` 等）はこの corpus から除外する。
        これらは「declared set の外」ではなくなり、`git <flag> value push origin main`
        は実 git 同様「value」を（誤った）subcommand とみなして push に到達しないのが
        正しい挙動になる（design.md ADR-3 § Consequences で明示的に想定済み）。
        ここでは依然として未宣言（fail-closed で両 arity 候補にすべき）な flag のみを残す。
        """
        outside = [
            "--exec-path",
            "--super-prefix",
            "--icase-pathspec",  # note: 末尾 "s" 無し = GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT の "--icase-pathspecs" とは別の未宣言 flag
        ]
        for flag in outside:
            with self.subTest(flag=flag):
                self.assertTrue(
                    pcp.is_git_push(pcp.tokenize(f"git {flag} push origin main"))[0]
                )
                self.assertTrue(
                    pcp.is_git_push(pcp.tokenize(f"git {flag} value push origin main"))[0]
                )


class GitGlobalFlagsWithoutArgumentTests(unittest.TestCase):
    """ADR-3: 既知 no-arg global flag は実 git で分離引数を消費しないことを固定する。"""

    @unittest.skipIf(GIT_BINARY is None, "git binary not found")
    def test_known_no_arg_flags_do_not_consume_separate_argument(self):
        for flag in sorted(gcp.GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT):
            with self.subTest(flag=flag):
                consumes = git_consumes_separate_argument(flag)
                if consumes is None:
                    self.skipTest(f"{flag} not recognized by installed git")
                self.assertFalse(consumes)

    def test_with_and_without_argument_sets_are_disjoint(self):
        self.assertEqual(
            gcp.GIT_GLOBAL_FLAGS_WITH_ARGUMENT & gcp.GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT,
            frozenset(),
        )

    def test_known_no_arg_flag_narrows_subcommand_candidates(self):
        """既知 no-arg flag は「引数を取る」候補を生成しない（過検出の減少）。

        `git <no-arg flag> push origin main` は push が唯一の候補として検出される。
        `git <no-arg flag> value push origin main` は "value" が（誤った）subcommand
        候補になり、"push" は候補に入らないため非検出になる。これは実 git の挙動と一致
        する（未宣言 flag 向けの fail-closed 両候補とは意図的に異なる。ADR-3）。
        """
        for flag in sorted(gcp.GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT):
            with self.subTest(flag=flag):
                self.assertTrue(
                    pcp.is_git_push(pcp.tokenize(f"git {flag} push origin main"))[0]
                )
                self.assertFalse(
                    pcp.is_git_push(pcp.tokenize(f"git {flag} value push origin main"))[0]
                )


class UnknownGlobalFlagPropertyTests(unittest.TestCase):
    """未知 flag は arity 不明として**両方の解釈**を候補にする（一覧の完全性に依存しない）。"""

    UNKNOWN_FLAGS = ("--totally-unknown", "--future-option", "-Z", "-Xy")

    def test_unknown_flag_with_any_arity_is_detected(self) -> None:
        for flag in self.UNKNOWN_FLAGS:
            for command in (
                f"git {flag} push origin main",
                f"git {flag} value push origin main",
                f"git {flag}=value push origin main",
            ):
                with self.subTest(command=command):
                    self.assertTrue(pcp.is_git_push(pcp.tokenize(command))[0])

    def test_unknown_flag_mixed_with_known_flags(self) -> None:
        command = "git --totally-unknown value -C /repo/a --future-option push origin main"
        self.assertTrue(pcp.is_git_push(pcp.tokenize(command))[0])

    def test_unknown_flag_does_not_cross_command_separator(self) -> None:
        tokens = pcp.tokenize("git --totally-unknown; push")
        self.assertFalse(pcp.is_git_push(tokens)[0])


@unittest.skipUnless(
    BASH_BINARY is not None and GIT_BINARY is not None,
    "requires bash and git",
)
class RealShellDifferentialTests(unittest.TestCase):
    """差分テスト: **CORPUS に列挙した書式**について、実 bash が push を実行するなら
    `is_git_push` も True になることを実測で固定する。

    **保証範囲**: 下の `CORPUS` は固定ケースであり property / fuzz ではない。したがって
    このテストが固定するのは「列挙した書式集合に対する保証」であって、任意の shell 入力に
    対する無条件の包含関係ではない。列挙外で未検出が実測されている書式（herestring /
    パイプ経由の shell / ANSI-C quoting / 変数展開・コマンド置換）は design.md
    § Honest Limitations に列挙する。**検出面を変える変更では CORPUS を先に増やすこと**。

    oracle は 2 層とも実物から取る:

    - shell 層: 実 bash に文字列を食わせ、PATH 先頭に置いた stub `git` が受け取った
      argv を記録する（tokenize / コメント / 行継続 / nested shell の正しさを実測）
    - git 層: `git_consumes_separate_argument` で実 git から global flag の arity を
      取得し、記録した argv の subcommand を決める

    判定は**片方向**（実 bash が push する → `is_git_push` が True）。過検出は
    design.md § Honest Limitations で受容済みのため逆方向は課さない。
    """

    CORPUS = (
        "git push origin main",
        "git -C {dir} push origin main",
        "git --git-dir {dir}/.git push origin main",
        "git --shallow-file /dev/null push origin main",
        "git commit -m fix#12 && git push origin main",
        "true a#b; git push --force origin main",
        "bash --norc -c 'git push origin main'",
        "bash -c -- 'git push origin main'",
        "bash -xc 'git push origin main'",
        'bash -c \'bash -c "git push origin main"\'',
        "eval 'git push origin main'",
        "env git push origin main",
        "git \\\npush origin main",
        "echo hi\ngit push origin main",
        "GDD_SKIP_PRE_PUSH_GATE=1 git push origin main",
        # 偶数個の行末バックスラッシュ = 行継続ではない
        "echo a\\\\\ngit push origin main",
        "GDD_SKIP_PRE_PUSH_GATE=1 env \\\\\ngit push origin main",
        "echo a\\\\\\\\\ngit push origin main",
        # 二重引用符の中の置換・展開の中の `"` は外の引用を閉じず、中の `#` はコメントではない
        'git commit -m "$(printf "fix #12")" && git push origin main',
        "echo `echo a #b`; git push origin main",
        'echo "${{x:-"a #b"}}" && git push origin main',
        # バッククォートの中の `$(…)`・サブシェルの中の `#` もコメントではない（bash は閉じる ` を先に探す）
        "echo `echo $(echo a #b)`; git push origin main",
        "`(echo a #b)`; git push origin main",
        'echo `echo "$(echo a #b)"`; git push origin main',
        'echo "`echo "a #b"`" && git push origin main',
        # 引用した区切り文字は `-C` の値（git は `&` という dir で push する）
        "git -C '&' push origin main",
        # 複数行の commit メッセージ（閉じ側の行に `"` が 2 つ）の後の push
        'git commit -m "s\n\nCo-Authored-By: X <x@example.com>" && git push origin main',
        # 引用した heredoc の本文の行末の `\` は終端の行をつながない
        "cat > /dev/null <<'EOF'\na \\\nEOF\ngit push origin main",
        "true # c\ngit push origin main",
        "git push origin main 2>&1",
    )

    STUB_GIT = (
        "#!/bin/sh\n"
        "{\n"
        '  for arg in "$@"; do printf \'%s\\n\' "$arg"; done\n'
        "  printf '%s\\n' '<<<INVOCATION-END>>>'\n"
        '} >> "$GDD_GIT_STUB_LOG"\n'
        "exit 0\n"
    )

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        bindir = root / "bin"
        bindir.mkdir()
        stub = bindir / "git"
        stub.write_text(self.STUB_GIT, encoding="utf-8")
        stub.chmod(0o755)
        self.root = root
        self.bindir = bindir
        self.log = root / "git-invocations.log"
        self.addCleanup(self._tmp.cleanup)

    def _invocations(self, command: str) -> list[list[str]]:
        if self.log.exists():
            self.log.unlink()
        env = dict(os.environ)
        env["PATH"] = f"{self.bindir}{os.pathsep}{env.get('PATH', '')}"
        env["GDD_GIT_STUB_LOG"] = str(self.log)
        subprocess.run(
            [BASH_BINARY, "-c", command],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if not self.log.exists():
            return []
        invocations: list[list[str]] = []
        current: list[str] = []
        for line in self.log.read_text(encoding="utf-8").splitlines():
            if line == "<<<INVOCATION-END>>>":
                invocations.append(current)
                current = []
                continue
            current.append(line)
        return invocations

    @staticmethod
    def _real_subcommand(argv: list[str]) -> str | None:
        cursor = 0
        while cursor < len(argv):
            token = argv[cursor]
            if not token.startswith("-"):
                return token
            if "=" in token:
                cursor += 1
                continue
            if git_consumes_separate_argument(token) is True:
                cursor += 2
                continue
            cursor += 1
        return None

    def test_every_real_push_form_is_detected(self) -> None:
        for template in self.CORPUS:
            command = template.format(dir=self.root)
            with self.subTest(command=command):
                invocations = self._invocations(command)
                real_push = any(
                    self._real_subcommand(argv) == "push" for argv in invocations
                )
                self.assertTrue(
                    real_push,
                    f"corpus 前提が壊れている（実 bash が push を実行していない）: {command!r}",
                )
                self.assertTrue(
                    pcp.is_git_push(pcp.tokenize(command))[0],
                    f"実 bash は push したが is_git_push が False: {command!r}",
                )


class PushFlagArityTests(unittest.TestCase):
    """`git push` option 一覧の正しさを**実 git の宣言から**検証する（H-1 / M-2 クラス）。

    `GitGlobalFlagArityTests` が git global flag に対して行っている検証を、
    push subcommand の option 一覧（`_KNOWN_VALUE_FLAGS` / `_AMBIGUOUS_FLAGS`）へ
    そのまま適用する。個別 flag の足し引きを assert しても「次の 1 件」は防げないので、
    検証すべき述語をクラスとして 4 つ置く:

    1. 一覧メンバは実 git でも分離引数を消費する（消費しないなら一覧から外す）
    2. 実 git が値を取らないと宣言する option は値 flag 一覧に**登録されていない**
       （H-1: `-u` / `--set-upstream` の誤登録はこの述語違反）
    3. 実 git が alias と宣言する綴りは、alias 先と同じ集合に属する
       （M-2: `--branches` は `--all` の alias なので `_AMBIGUOUS_FLAGS` に属する）
    4. 上記が refspec 解決の**挙動**に反映されている（値を取らない option を前置しても
       refspec が読み飛ばされない / 値を取る option の引数が refspec と誤認されない）

    期待値 `EXPECTED_*` は module の定数を参照せずテスト側に literal で置く
    （`GitGlobalFlagArityTests` と同じ理由: 集合を読んで回すと集合からメンバを削る
    mutation が反復対象からも消えて同語反復になる）。
    """

    EXPECTED_VALUE_FLAGS = frozenset(
        {
            "--repo",
            "-o",
            "--push-option",
            "--receive-pack",
            "--exec",
        }
    )
    EXPECTED_AMBIGUOUS_FLAGS = frozenset({"--all", "--branches", "--mirror"})

    def _real_options(self) -> tuple[tuple[str, bool, str], ...]:
        options = real_git_push_options()
        if not options:
            self.skipTest("git binary not available or `git push -h` unparseable")
        return options

    def _arity(self) -> dict[str, bool]:
        return {name: takes for name, takes, _ in self._real_options()}

    def test_module_flag_sets_match_expected(self) -> None:
        self.assertEqual(set(pcp._KNOWN_VALUE_FLAGS), set(self.EXPECTED_VALUE_FLAGS))
        self.assertEqual(set(pcp._AMBIGUOUS_FLAGS), set(self.EXPECTED_AMBIGUOUS_FLAGS))

    def test_parser_reads_real_git_push_options(self) -> None:
        """oracle 自体の健全性（解析に失敗した空 dict で他テストが空回りしない）。"""
        arity = self._arity()
        for flag in ("--all", "--mirror", "--branches", "-u", "--repo", "-o"):
            with self.subTest(flag=flag):
                self.assertIn(flag, arity, f"`git push -h` から {flag} を読めていない")

    def test_every_expected_value_flag_consumes_separate_argument(self) -> None:
        arity = self._arity()
        for flag in sorted(self.EXPECTED_VALUE_FLAGS):
            with self.subTest(flag=flag):
                if flag not in arity:
                    self.skipTest(f"installed git does not list {flag}")
                self.assertTrue(
                    arity[flag], f"{flag} は実 git で値を取らない。一覧から外すこと"
                )

    def test_no_valueless_real_git_option_is_registered_as_value_flag(self) -> None:
        """H-1: 実 git が値を取らないと言う option を値 flag に登録しない。

        誤登録すると次 token（通常は remote 名）が値として読み飛ばされ、実際の
        refspec が `positional[0]` に繰り上がって捨てられる = `explicit_ref=None`
        （ref 省略扱い → 呼び出し側が HEAD 解決）という fail-open になる。
        """
        for name, takes_argument, _ in self._real_options():
            if takes_argument:
                continue
            with self.subTest(flag=name):
                self.assertNotIn(
                    name,
                    pcp._KNOWN_VALUE_FLAGS,
                    f"{name} は実 git で値を取らないのに値 flag として登録されている",
                )

    def test_real_git_aliases_share_the_registration_of_their_target(self) -> None:
        """M-2: `alias of --X` と宣言された綴りは alias 先と同じ集合に属する。"""
        checked = 0
        for name, _, description in self._real_options():
            match = _PUSH_OPTION_ALIAS_RE.match(description)
            if match is None or name.startswith("--no-"):
                continue
            target = match.group(1)
            for registry, label in (
                (pcp._AMBIGUOUS_FLAGS, "_AMBIGUOUS_FLAGS"),
                (pcp._KNOWN_VALUE_FLAGS, "_KNOWN_VALUE_FLAGS"),
            ):
                if target not in registry:
                    continue
                checked += 1
                with self.subTest(flag=name, target=target):
                    self.assertIn(
                        name,
                        registry,
                        f"{name} は実 git で {target} の alias。{label} にも登録すること",
                    )
        if not checked:
            self.skipTest("installed git declares no alias of a registered flag")

    def test_valueless_real_git_option_does_not_hide_the_refspec(self) -> None:
        """挙動側の担保: 値を取らない option を前置しても refspec が落ちない。"""
        for name, takes_argument, _ in self._real_options():
            if takes_argument or name in pcp._AMBIGUOUS_FLAGS:
                continue
            with self.subTest(flag=name):
                tokens = pcp.tokenize(f"git push {name} origin feature-x")
                _, git_index = pcp.is_git_push(tokens)
                result = pcp.classify_refspec(tokens, git_index)
                self.assertFalse(result["ambiguous"])
                self.assertEqual(result["explicit_ref"], "feature-x")

    def test_valueless_real_git_option_keeps_multiple_refspecs_ambiguous(self) -> None:
        for name, takes_argument, _ in self._real_options():
            if takes_argument or name in pcp._AMBIGUOUS_FLAGS:
                continue
            with self.subTest(flag=name):
                tokens = pcp.tokenize(f"git push {name} origin main feature-x")
                _, git_index = pcp.is_git_push(tokens)
                self.assertTrue(pcp.classify_refspec(tokens, git_index)["ambiguous"])

    def test_registered_value_flag_argument_is_not_a_refspec(self) -> None:
        arity = self._arity()
        for flag in sorted(pcp._KNOWN_VALUE_FLAGS):
            with self.subTest(flag=flag):
                if arity.get(flag) is not True:
                    self.skipTest(f"installed git does not list {flag} with a value")
                tokens = pcp.tokenize(f"git push {flag} probe-value origin feature-x")
                _, git_index = pcp.is_git_push(tokens)
                result = pcp.classify_refspec(tokens, git_index)
                self.assertFalse(result["ambiguous"])
                self.assertEqual(result["explicit_ref"], "feature-x")

    def test_unregistered_value_taking_option_fails_closed(self) -> None:
        """A-15（非 blocking / T-9 carry forward）の方向を固定する。

        値を取る option を一覧に載せていないと分離引数が positional に混じって
        refspec 数がずれる。ずれる向きが **over-block（fail-closed）** であることを
        固定し、将来 fail-open 側へ倒れたら落ちるようにする。一覧への追加自体は
        T-9 の block reason 設計と併せて判断する（T-4 の scope 外）。
        """
        unregistered = [
            name
            for name, takes_argument, _ in self._real_options()
            if takes_argument and name not in pcp._KNOWN_VALUE_FLAGS
        ]
        if not unregistered:
            self.skipTest("all value-taking push options are registered")
        for name in unregistered:
            with self.subTest(flag=name):
                tokens = pcp.tokenize(f"git push {name} probe-value origin feature-x")
                _, git_index = pcp.is_git_push(tokens)
                self.assertTrue(
                    pcp.classify_refspec(tokens, git_index)["ambiguous"],
                    f"{name} の未登録は over-block ではなく fail-open になっている",
                )


if __name__ == "__main__":
    unittest.main()
