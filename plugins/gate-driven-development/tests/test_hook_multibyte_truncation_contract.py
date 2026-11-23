"""hook が注入する additionalContext を multibyte 安全に切り詰める契約テスト。

背景（PR #191 Copilot レビュー指摘）:
`run-user-prompt-submit-hook.sh` / `run-session-start-hook.sh`（当時の compaction 復帰プロンプト）は
`Approved Direction` / `Last Handoff Summary` を `${var:0:512}` で切り詰めていた。
bash の substring 展開はロケール依存で、`LC_ALL=C` やロケール未設定では
**バイト単位**になり、日本語の UTF-8 シーケンスを途中で切って
additionalContext の JSON を壊す（invalid continuation byte）。

どちらも日本語自由記述 field で、512 バイト = 日本語約 170 文字なので超過は現実的。
引用符・バックスラッシュのエスケープは既に正しく行われているので、
残る穴は文字境界の切断のみ。

同じ落とし穴を `scripts/find-stale-steerings.sh` は「multibyte を含みうる値は
バイト単位で切らない」方針で回避している。hook 側も文字単位の切り詰めに揃える。

hook の入口は最初に `lib/kill-switch.sh` を source し、C.UTF-8 がある環境ではそこでロケールが
`C.UTF-8` になる（無い環境では bash は受け継いだロケールのまま。kill-switch.sh のコメントのとおり）。
入口経由の 3 ロケールのテストは、その上書きの後でも JSON が壊れないことの確認になる。上書きが
効くことは `test_hook_locale_utf8_contract.py` が見る。C ロケールでの切り詰めそのものは、lib を
直接 source する `TruncateCharsInCLocaleTests` で見る。入口の hook が `${var:0:N}` に戻っていない
ことは、C.UTF-8 がある環境の入口テストでは捕まらないので、`NoByteSubstringInHooksTests` で固定する。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
PROMPT_HOOK = ROOT / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"
SESSION_START_HOOK = ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"
PRE_COMPACT_HOOK = ROOT / "hooks" / "scripts" / "run-pre-compact-hook.sh"

# 512 バイト境界をまたぐ長さ。'あ' は UTF-8 3 バイトなので 300 文字 = 900 バイト。
LONG_JA = "あ" * 300

# 入口に渡すロケールの 3 条件。C とロケール未設定で JSON が壊れていた。3 条件とも、kill-switch.sh の
# 上書きの後でも JSON が壊れないことの確認になる。上書きが効くことは test_hook_locale_utf8_contract.py が見る。
LOCALES = (
    ("LC_ALL=C", {"LC_ALL": "C", "LANG": "C"}),
    ("locale unset", {}),
    ("ja_JP.UTF-8", {"LC_ALL": "ja_JP.UTF-8", "LANG": "ja_JP.UTF-8"}),
)

_TASKLIST = (
    "## Current Task\n"
    "### Task: T-1 実装する\n"
    "- AC: AC-1\n\n"
    "## Review Status\nNext Action=gdd-subagent-driven-implementation\n"
)


def _base_env(locale_env: dict) -> dict:
    env = os.environ.copy()
    for var in ("CLAUDE_CODE_SESSION_ID", "GDD_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT",
                "LC_ALL", "LANG", "LC_CTYPE"):
        env.pop(var, None)
    env.update(locale_env)
    return env


def _assert_valid_utf8_json(testcase: unittest.TestCase, stdout: str, label: str) -> dict:
    """hook 出力が壊れていない UTF-8 の JSON であることを検査する"""
    raw = stdout.strip().encode("utf-8", errors="surrogateescape")
    testcase.assertTrue(raw, f"[{label}] hook produced no output")
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - 失敗時の診断用
        testcase.fail(f"[{label}] hook output is not valid UTF-8: {exc}")
    try:
        return json.loads(decoded)
    except json.JSONDecodeError as exc:  # pragma: no cover - 失敗時の診断用
        testcase.fail(f"[{label}] hook output is not valid JSON: {exc}")


class UserPromptSubmitTruncationTests(unittest.TestCase):
    """UserPromptSubmit hook: 別セッション再開時の context 注入"""

    def _setup(self, repo: Path, value: str = LONG_JA) -> None:
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        # 毎ターンの注入は GDD の印（active な marker）があるときだけ
        (repo / ".claude").mkdir(exist_ok=True)
        (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
        steering = repo / ".steering" / "20260730-multibyte"
        steering.mkdir(parents=True, exist_ok=True)
        steering.joinpath("state.md").write_text(
            "Started At: 2026-07-30T00:00:00+09:00\n"
            "Resume From: gdd-subagent-driven-implementation\n"
            "Requirements Review Status=approved | evidence: r\n"
            "Design Review Status=approved | evidence: d\n"
            "Human Check Status=approved | evidence: h\n"
            "Route In Progress=none\n"
            "Next Action: gdd-subagent-driven-implementation\n"
            f"Approved Direction: {value}\n"
            f"Last Handoff Summary: {value}\n",
            encoding="utf-8",
        )
        steering.joinpath("requirements.md").write_text(
            "### 一言\nmultibyte fixture\n\n## 受入条件\n- AC-1: x\n", encoding="utf-8")
        steering.joinpath("tasklist.md").write_text(_TASKLIST, encoding="utf-8")

    def test_long_japanese_fields_keep_json_valid(self) -> None:
        for label, locale_env in LOCALES:
            with self.subTest(locale=label):
                with tempfile.TemporaryDirectory(prefix="gdd-mb-ups-") as tmp:
                    repo = Path(tmp)
                    self._setup(repo)
                    r = subprocess.run(
                        ["bash", str(PROMPT_HOOK)], cwd=repo,
                        input=json.dumps({"prompt": "続きをお願い"}).encode("utf-8"),
                        capture_output=True, env=_base_env(locale_env),
                    )
                    stdout = r.stdout.decode("utf-8", errors="surrogateescape")
                    payload = _assert_valid_utf8_json(self, stdout, label)
                    context = payload["hookSpecificOutput"]["additionalContext"]
                    self.assertNotIn("�", context,
                                     f"[{label}] truncation produced a replacement char")
                    self.assertIn("あ", context, f"[{label}] handoff context was dropped")

    def test_truncation_is_bounded(self) -> None:
        """切り詰め自体は効いていること（無制限注入に退行していない）

        上限の単位はバイトから文字に変わる。同じ 512 でも日本語の許容量が増えるため、
        文字数で境界を超える fixture で検査する。
        """
        with tempfile.TemporaryDirectory(prefix="gdd-mb-bound-") as tmp:
            repo = Path(tmp)
            self._setup(repo, value="い" * 700)
            r = subprocess.run(
                ["bash", str(PROMPT_HOOK)], cwd=repo,
                input=json.dumps({"prompt": "続きをお願い"}).encode("utf-8"),
                capture_output=True, env=_base_env({}),
            )
            context = json.loads(r.stdout.decode("utf-8"))[
                "hookSpecificOutput"]["additionalContext"]
            # 2 field で元は 1400 文字。512 文字上限で切られていれば全量は残らない。
            self.assertEqual(context.count("い"), 512 * 2,
                             "free-text fields must be truncated at 512 characters each")


class TruncateCharsInCLocaleTests(unittest.TestCase):
    """lib を直接 source し、C ロケールで `gdd_truncate_chars` を呼ぶ。

    C.UTF-8 がある環境では、入口経由だと kill-switch.sh がロケールを上書きするので、バイト単位のロケールでの
    切り詰めはここで見る（`${var:0:N}` に戻すと、C ロケールでは UTF-8 の途中で切れる）。
    """

    def _truncate(self, value: str, limit: int) -> bytes:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "LC_", "LANG"))}
        env["LC_ALL"] = "C"
        lib = ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
        proc = subprocess.run(
            ["bash", "-c", f'source "{lib}"; gdd_truncate_chars "$1" "$2"', "_", value, str(limit)],
            capture_output=True, env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def test_cuts_at_a_character_boundary(self) -> None:
        self.assertEqual(self._truncate(LONG_JA, 100).decode("utf-8"), "あ" * 100)

    def test_keeps_a_value_shorter_than_the_limit(self) -> None:
        self.assertEqual(self._truncate(LONG_JA, 512).decode("utf-8"), LONG_JA)


class NoByteSubstringInHooksTests(unittest.TestCase):
    """state.md の値を注入する hook（UserPromptSubmit・SessionStart・PreCompact）が、`${var:0:N}` で切り詰めていないこと。

    C.UTF-8 がある環境では入口の bash が文字単位で動くので、`${var:0:N}` に戻しても入口テストは
    通る。C.UTF-8 が無く、受け継いだロケールが C の環境でだけ JSON が壊れるので、コードで固定する。
    """

    def test_no_substring_expansion_outside_comments(self) -> None:
        pattern = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*:0:")
        for hook in (PROMPT_HOOK, SESSION_START_HOOK, PRE_COMPACT_HOOK):
            with self.subTest(hook=hook.name):
                code = [
                    line for line in hook.read_text(encoding="utf-8").splitlines()
                    if not line.lstrip().startswith("#")
                ]
                self.assertEqual([line for line in code if pattern.search(line)], [])


class PreCompactTruncationTests(unittest.TestCase):
    """PreCompact hook: 要約器へ渡す Resume From / Next Action（128 文字で切り詰める）"""

    def test_long_japanese_fields_keep_json_valid(self) -> None:
        for label, locale_env in LOCALES:
            with self.subTest(locale=label):
                with tempfile.TemporaryDirectory(prefix="gdd-mb-pc-") as tmp:
                    steering = Path(tmp) / "steering"
                    steering.mkdir()
                    steering.joinpath("state.md").write_text(
                        f"Resume From: {LONG_JA}\nNext Action: {LONG_JA}\n", encoding="utf-8"
                    )
                    env = _base_env(locale_env)
                    env["GDD_STEERING_DIR"] = str(steering)
                    r = subprocess.run(["bash", str(PRE_COMPACT_HOOK)], capture_output=True, env=env, input=b"")
                    stdout = r.stdout.decode("utf-8", errors="surrogateescape")
                    message = _assert_valid_utf8_json(self, stdout, label)["systemMessage"]
                    self.assertNotIn("\ufffd", message, f"[{label}] truncation produced a replacement char")
                    self.assertIn("あ" * 128, message, f"[{label}] value was dropped")
                    self.assertNotIn("あ" * 129, message, f"[{label}] value was not truncated")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
