"""`_locale_support.is_euc_jp` が、python の返す encoding 名の別名も EUC-JP と読み、近い別の codec を EUC-JP と読まない。"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _locale_support import euc_jp_locale_env, is_euc_jp


class IsEucJpTests(unittest.TestCase):
    def test_aliases_of_euc_jp_are_accepted(self) -> None:
        for name in ("EUC-JP", "euc_jp", "eucJP", "eucjp", "ujis", "U-JIS", "EUC_JP"):
            with self.subTest(name=name):
                self.assertTrue(is_euc_jp(name))

    def test_other_or_unknown_encodings_are_rejected(self) -> None:
        for name in ("UTF-8", "ascii", "ANSI_X3.4-1968", "shift_jis", "iso2022_jp", "euc_jis_2004", "euc_jisx0213", "euc_kr", "", "no-such-codec"):
            with self.subTest(name=name):
                self.assertFalse(is_euc_jp(name))


class LocaleEnvUsesTheCodecNameTests(unittest.TestCase):
    """`euc_jp_locale_env` が、probe の返す別名でも skip せず、近い別の codec では skip する（判定の呼び出し側を固定する）。"""

    def _run(self, probe_stdout: str):
        def fake_run(args, **kwargs):
            stdout = "ja_JP.eucJP\n" if args[0] == "locale" else probe_stdout + "\n"
            return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

        with tempfile.TemporaryDirectory() as workdir, mock.patch("_locale_support.subprocess.run", side_effect=fake_run):
            return euc_jp_locale_env(self, Path(workdir))

    def test_an_alias_is_accepted(self) -> None:
        try:
            env = self._run("eucJP")
        except unittest.SkipTest as skipped:
            self.fail(f"別名を EUC-JP と読まず skip した: {skipped}")
        self.assertEqual(env, {"LC_ALL": "ja_JP.eucJP"})

    def test_a_near_codec_skips(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=False) as env:
            env.pop("GITHUB_ACTIONS", None)
            with self.assertRaises(unittest.SkipTest):
                self._run("euc_jis_2004")


if __name__ == "__main__":
    unittest.main()
