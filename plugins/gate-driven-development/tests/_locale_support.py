"""UTF-8 以外のロケール（EUC-JP）で hook を起動するテストが共有する環境変数の用意。

hook が受け継ぐロケールが UTF-8 以外だと、python の stdin・stdout・argv・環境変数や
awk・sed がそのロケールで文字を扱い、Claude Code が渡す UTF-8 の payload や state.md の
日本語を読めなくなる。ロケールが実際に効かないと、Python は UTF-8 に落ちて修正の前の
コードでも通ってしまうので、stdin の encoding が EUC-JP になったことを確かめてから返す。
"""
from __future__ import annotations

import codecs
import os
import subprocess
import unittest
from pathlib import Path

_NAMES = ("ja_JP.eucJP", "ja_JP.eucjp", "ja_JP.EUC-JP")


def is_euc_jp(encoding: str) -> bool:
    """python が返した encoding 名が EUC-JP か。別名（`eucJP`・`ujis`・`EUC-JP`）は codecs が正規名に寄せる。"""
    try:
        return codecs.lookup(encoding).name == "euc_jp"
    except LookupError:
        return False


def euc_jp_locale_env(test: unittest.TestCase, workdir: Path) -> dict[str, str]:
    """EUC-JP のロケールの環境変数（`LC_ALL`、作ったときは `LOCPATH` も）を返す。

    入っていなければ localedef で `workdir` の下に作る（root は要らない）。用意できないときは
    skip するが、CI（`GITHUB_ACTIONS`）では黙って skip せずに落とす。
    """
    try:
        installed = subprocess.run(["locale", "-a"], capture_output=True, text=True).stdout.split()
    except FileNotFoundError:
        installed = []
    name = next((n for n in _NAMES if n in installed), None)
    env = {"LC_ALL": name} if name else {}
    localedef_error = ""
    if name is None:
        # localedef は出力先の親ディレクトリを作らない
        locpath = workdir / "locales"
        locpath.mkdir(parents=True, exist_ok=True)
        try:
            made = subprocess.run(
                ["localedef", "-i", "ja_JP", "-f", "EUC-JP", str(locpath / "ja_JP.eucJP")],
                capture_output=True, text=True, timeout=120,
            )
            localedef_error = made.stderr.strip()[-300:]
        except (FileNotFoundError, subprocess.TimeoutExpired) as error:
            localedef_error = repr(error)
        # localedef は警告でも非 0 を返すので、出力先ができたかで判定する
        if (locpath / "ja_JP.eucJP").is_dir():
            env = {"LC_ALL": "ja_JP.eucJP", "LOCPATH": str(locpath)}
    encoding = ""
    if env:
        probe_env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        probe_env.update(env)
        encoding = subprocess.run(
            ["python3", "-c", "import sys; print(sys.stdin.encoding)"],
            capture_output=True, text=True, env=probe_env,
        ).stdout.strip()
    if not is_euc_jp(encoding):
        message = (
            f"stdin が EUC-JP になるロケールを用意できない（{env or 'ロケールなし'}、stdin: {encoding or '不明'}、"
            f"localedef: {localedef_error or '-'}）"
        )
        if os.environ.get("GITHUB_ACTIONS"):
            test.fail(message)
        test.skipTest(message)
    return env
