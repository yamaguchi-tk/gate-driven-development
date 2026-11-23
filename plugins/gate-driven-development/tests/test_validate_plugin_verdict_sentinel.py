"""`tests/validate-plugin.sh` の外側番兵（VERDICT 行必須化）の契約テスト。

背景（PR #93 の PR 後レビュー3巡目、独立-5・独立-6に続く同クラスタの High）:
`review-log-present.sh`・`version-not-consumed.sh` の `load_dynamic_module()` は
`exec_module()` の SystemExit だけを守り、動的ロードしたモジュールへの**呼び出し**
（`identity_lib.repository_identity()`、`release.NAME_RE.fullmatch()`、
`release.load_fragments()` 等）で SystemExit が送出されると、check スクリプトは
rc=0 で静かに成功してしまう（fail-open）。個別の呼び出し箇所を塞ぐ対処は
`independent-review.md` (h) が指摘する「列挙型判定」の再発（独立-5/6 と同型）に
なるため、Opus（claude-opus-5）へのセカンドオピニオンで構造的解決を採用した:

    check スクリプトは成功時に `VERDICT: <check_name>: OK` または
    `VERDICT: <check_name>: SKIP` を必ず1行出力する（宣言フィールド化。
    `machine-checks-never-parse-free-text` と同じ設計原則）。
    validate-plugin.sh は各 check の実行後、rc=0 なのにこの行が無ければ
    FAIL にする（判定を宣言したかどうかを機械的に検査する。個別の呼び出し
    箇所を塞ぐのではなく、「宣言が無い成功」を一律で拒否する）。

このテストは、L1+ 安全策2 の fail-open 3 ケース + 逆方向対照を、合成 check
スクリプトで固定する。実際の46本の check 内容には依存しない
（validate-plugin.sh 自体の番兵ロジックだけを検証する）。
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _plugin_module_loader import PLUGIN_ROOT


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_sandbox(tmp: Path, check_script_body: str, check_name: str = "synthetic-check") -> Path:
    """validate-plugin.sh 本体を実体からコピーし、合成 manifest + 合成 check を1本だけ持つ
    サンドボックス plugin root を作る。"""
    root = tmp / "plugin"
    write(root / "tests" / "validate-plugin.sh", (PLUGIN_ROOT / "tests" / "validate-plugin.sh").read_text(encoding="utf-8"))
    (root / "tests" / "validate-plugin.sh").chmod(0o755)
    write(root / "tests" / "checks" / "manifest.tsv", f"{check_name}\ttrue\ttests/checks/{check_name}.sh\n")
    write(root / "tests" / "checks" / f"{check_name}.sh", "#!/usr/bin/env bash\nset -euo pipefail\n" + check_script_body)
    (root / "tests" / "checks" / f"{check_name}.sh").chmod(0o755)
    return root


def run_validate(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(root / "tests" / "validate-plugin.sh")],
        capture_output=True,
        text=True,
        check=False,
    )


class VerdictSentinelFailOpenTests(unittest.TestCase):
    """安全策2: block すべき入力が allow になる／判定不能なのに通ってしまう経路を固定する。"""

    def test_silent_success_without_verdict_line_fails(self) -> None:
        # ケース1: check が何の判定行も出さずに rc=0 で終わる (今回のクラスタの
        # 実害そのもの: 呼び出し中の SystemExit(0) で fail() に到達せず、
        # 判定行なしで静かに成功する経路)。VERDICT 行が無ければ FAIL にする。
        with tempfile.TemporaryDirectory() as tmp:
            root = make_sandbox(Path(tmp), 'echo "some unrelated diagnostic output"\n')
            result = run_validate(root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("VERDICT", result.stdout)

    def test_exception_in_check_still_fails_closed(self) -> None:
        # ケース2: check スクリプトが例外(非0 exit)で落ちる。既存の
        # fail-fast 動作(set -euo pipefail 下の直接呼び出し)が、出力の
        # キャプチャ方式に変えても保たれることを固定する回帰テスト。
        with tempfile.TemporaryDirectory() as tmp:
            root = make_sandbox(Path(tmp), 'echo "BLOCK: synthetic-check"\necho "boom" >&2\nexit 1\n')
            result = run_validate(root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("boom", result.stdout + result.stderr)

    def test_verdict_line_for_different_check_name_fails(self) -> None:
        # ケース3a: 判定できない(=別の check 向けの宣言を騙って出す)のに
        # 通ってしまわないことを固定する。アンカー一致は check_name まで見る。
        with tempfile.TemporaryDirectory() as tmp:
            root = make_sandbox(Path(tmp), 'echo "VERDICT: some-other-check: OK"\n')
            result = run_validate(root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("VERDICT", result.stdout)

    def test_verdict_line_as_unanchored_substring_fails(self) -> None:
        # ケース3b: VERDICT 行が行頭・行末に固定されていない(他の文言に埋め込まれた
        # 部分文字列)場合は、宣言行として認めない。^...$ アンカーで拒否する。
        with tempfile.TemporaryDirectory() as tmp:
            root = make_sandbox(Path(tmp), 'echo "noise-before VERDICT: synthetic-check: OK noise-after"\n')
            result = run_validate(root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


class VerdictSentinelIndependentReview8Tests(unittest.TestCase):
    """独立-8（review-log/20260916-review-log-cluster-recurrence-guard.md 参照）
    で指摘された穴を固定する回帰テスト。"""

    def test_check_consuming_stdin_does_not_skip_later_checks(self) -> None:
        # M-2: check の stdin が manifest.tsv の read ループのリダイレクトを
        # 継承したままだと、stdin を読む check が manifest の残り行を食い、
        # while が EOF で抜けて後続の check が一度も実行されずに rc=0 で
        # 完走する（「走らなかった check」を番兵は検出できない）。
        # </dev/null で切ったことを、2本の check を manifest に並べて固定する。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "plugin"
            write(root / "tests" / "validate-plugin.sh", (PLUGIN_ROOT / "tests" / "validate-plugin.sh").read_text(encoding="utf-8"))
            (root / "tests" / "validate-plugin.sh").chmod(0o755)
            write(
                root / "tests" / "checks" / "manifest.tsv",
                "stdin-eating-check\ttrue\ttests/checks/stdin-eating-check.sh\n"
                "later-check\ttrue\ttests/checks/later-check.sh\n",
            )
            write(
                root / "tests" / "checks" / "stdin-eating-check.sh",
                "#!/usr/bin/env bash\nset -euo pipefail\ncat >/dev/null\necho \"VERDICT: stdin-eating-check: OK\"\n",
            )
            write(
                root / "tests" / "checks" / "later-check.sh",
                "#!/usr/bin/env bash\nset -euo pipefail\nexit 1\n",
            )
            for name in ("stdin-eating-check.sh", "later-check.sh"):
                (root / "tests" / "checks" / name).chmod(0o755)
            result = run_validate(root)
            self.assertIn("VERDICT: stdin-eating-check: OK", result.stdout)
            # later-check.sh が実際に走り、exit 1 で全体が FAIL になることを
            # 固定する（stdin を吸われて未実行のまま rc=0 になっていないか）。
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_name_with_regex_metacharacter_is_rejected(self) -> None:
        # L-1: check_name を未エスケープで後段の grep -E に埋め込むため、
        # 正規表現メタ文字を含む名前だと誤受理の余地がある
        # （例: "aXcheck" が "a.check" というパターンに誤マッチする）。
        # manifest の時点で安全な文字種だけを許可することを固定する。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "plugin"
            write(root / "tests" / "validate-plugin.sh", (PLUGIN_ROOT / "tests" / "validate-plugin.sh").read_text(encoding="utf-8"))
            (root / "tests" / "validate-plugin.sh").chmod(0o755)
            write(root / "tests" / "checks" / "manifest.tsv", "a.check\ttrue\ttests/checks/a.check.sh\n")
            write(root / "tests" / "checks" / "a.check.sh", "#!/usr/bin/env bash\nset -euo pipefail\necho \"VERDICT: aXcheck: OK\"\n")
            (root / "tests" / "checks" / "a.check.sh").chmod(0o755)
            result = run_validate(root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("MANIFEST_ERROR", result.stdout)


class VerdictSentinelPositiveControlTests(unittest.TestCase):
    """逆方向の誤 block 対照: 正規の宣言は通ることを確認する。"""

    def test_ok_verdict_line_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_sandbox(Path(tmp), 'echo "some detail"\necho "VERDICT: synthetic-check: OK"\n')
            result = run_validate(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_skip_verdict_line_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_sandbox(Path(tmp), 'echo "VERDICT: synthetic-check: SKIP"\n')
            result = run_validate(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class RealChecksEmitVerdictTests(unittest.TestCase):
    """実物の check が番兵の契約（成功時に VERDICT 行を出す）を満たすことを固定する。

    PR #93 で番兵が入った時点で `hitl-required-fields-lint.sh` だけが VERDICT 行を
    出しておらず、main の validate-plugin.sh が rc=1 になっていた。
    """

    def test_hitl_required_fields_lint_emits_ok_verdict(self) -> None:
        # 入口: validate-plugin.sh と同じ環境変数（ROOT / PYTHON_BIN）で check を実行する。
        env = {"ROOT": str(PLUGIN_ROOT), "PYTHON_BIN": "python3", "PATH": os.environ["PATH"]}
        result = subprocess.run(
            ["bash", str(PLUGIN_ROOT / "tests" / "checks" / "hitl-required-fields-lint.sh")],
            capture_output=True,
            text=True,
            check=False,
            env=env,
            stdin=subprocess.DEVNULL,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VERDICT: hitl-required-fields-lint: OK", result.stdout.splitlines())


if __name__ == "__main__":
    unittest.main()
