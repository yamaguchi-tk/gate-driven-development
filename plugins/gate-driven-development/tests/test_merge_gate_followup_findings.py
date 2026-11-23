"""merge gate のマージ後独立レビュー findings に 1:1 対応する回帰テスト。

PR #23（merge gate）を main へ取り込んだあとに到着した独立レビューを、マージ済み
main で実測した結果、以下が実在の欠陥として確定した。各 finding に 1 クラスを対応
させ、「実装を戻したら必ず落ちる」形で固定する。

- A-1: 承認語彙の述語が全文アンカーで、人間の明示承認を記録できない（運用ロック）
- A-3: python 解析の失敗で gate が無出力素通りする（fail-open）
- A-4: fenced code block 内の記入例が本物の証跡として読まれる（fail-open）
- A-5: `*merge*` の事前判定が payload 全体に掛かり、無関係な Bash 呼び出しでも
       python3 が起動する（性能・副作用）
- A-6: hook 実起動テストが `GH_HOST` / `GH_REPO` を継承して環境依存で落ちる
       ＋ 鮮度 10 分 / 待機 40 分の境界を実起動で踏むテストが無い
- A-7: `-A`（`--author-email` の短縮形）未登録による PR 番号の化けと誤 block、
       owner/repo 照合の大小文字区別、`GH_HOST=github.com` の誤 block
- A-8: 出荷物に steering-local な識別子（`ADR-n` / `gate #n` / finding ID）が残る

本 module は `tests/test_merge_gate_hook_*.py`（関心事別に分割済み）を肥大化させないために分離している
（分割後も各 file の行数・関数数の目安を超えない方向を維持する）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _paths import PLUGIN_ROOT
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

from lib.constants import (  # noqa: E402
    MERGE_GATE_RECHECK_FRESHNESS_MINUTES,
    MERGE_GATE_REVIEW_WAIT_MINUTES,
    is_merge_approval,
)
from lib.gh_command_parse import parse_gh_pr_merge  # noqa: E402
from _git_fixture import init_repo  # noqa: E402
from _merge_gate_support import HANG_GUARD  # noqa: E402
from _timing_budget import hook_timeout_seconds, timing_budget  # noqa: E402

HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "run-merge-gate-hook.sh"
GH_PARSE_SOURCE = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "gh_command_parse.py"
DETECT_STEERING_LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
PR_FOLLOWUP_SKILL = PLUGIN_ROOT / "skills" / "gdd-pr-review-followup" / "SKILL.md"
PR_URL = "https://github.com/acme/widgets/pull/7"
BACKTICK = chr(96)

#: hook 自身の timeout（`hooks/hooks.json` の正本から読む。literal を二重に持たない）。
HOOK_TIMEOUT_SEC = hook_timeout_seconds("run-merge-gate-hook.sh")
#: #3 用の CPU 閾値（厳）と壁時計 backstop（緩）。同じ `HOOK_TIMEOUT_SEC` から
#: 別の除数で 2 つ導出するため、読み間違い防止に別名を置く（security review A-5）。
CPU_BUDGET_SEC = HOOK_TIMEOUT_SEC / 4
WALL_BACKSTOP_SEC = HOOK_TIMEOUT_SEC / 2


# --- 共通 fixture ---------------------------------------------------------


def _iso(delta_seconds: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=delta_seconds)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _init_repo(tmp: Path, commit_date_iso: str | None = None) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    init_repo(repo, commit_date=commit_date_iso)
    subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "origin",
         "https://github.com/acme/widgets.git"], check=True,
    )
    return repo


def _head_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _run_hook(payload: dict, cwd, home_dir, extra_env=None):
    """hook を実起動する。

    A-6: `GH_HOST` / `GH_REPO` は hook の判定入力そのものなので、実行環境から
    継承すると repo 決定要因の検査が環境依存になる。常に除去した env で起動する。
    """
    env = {k: v for k, v in os.environ.items() if k not in ("GH_HOST", "GH_REPO")}
    env["HOME"] = str(home_dir)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["CLAUDE_CODE_SESSION_ID"] = "test-session"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True, text=True, env=env, cwd=str(cwd), timeout=HANG_GUARD,
    )


def _write_state(repo: Path, evidence_lines, *, pr_url: str = PR_URL,
                 active: bool = True) -> Path:
    local_state = repo / ".claude" / "gdd-dev.local.md"
    local_state.parent.mkdir(parents=True, exist_ok=True)
    local_state.write_text(
        f"active: {'true' if active else 'false'}\nsession_id: test-session\n"
    )
    steering = repo / ".steering" / "20260101-demo"
    steering.mkdir(parents=True, exist_ok=True)
    lines = ["## Gate Status", "- Resume From: done", "- Next Action: done",
             f"- PR URL: {pr_url}"] + list(evidence_lines)
    (steering / "state.md").write_text("\n".join(lines) + "\n")
    return steering / "state.md"


def _approval_line(sha: str, pr: int = 7) -> str:
    return (f"- Merge Approval: PR #{pr} / head {sha} | evidence: 明示承認 "
            f"| approved_at: {_iso()}")


def _all_evidence_lines(sha: str, pr: int = 7) -> list[str]:
    now = _iso()
    return [
        _approval_line(sha, pr),
        f"- Pre-Merge Review Recheck: {sha} | new_blocking: 0 | at: {now}",
        f"- Last Review Push At: {sha} | at: {now}",
        f"- Bot Review Received: {sha} | received: yes | at: {now}",
    ]


def _hook_diag(result) -> str:
    """hook サブプロセス失敗時の診断メッセージ（returncode / stderr を含む）。

    docs/learned-patterns.md（2026-09-06, `20260906-merge-gate-session-jurisdiction`）:
    外部プロセスの stdout を無防備に扱うと、1 本の失敗が診断不能になる。
    stdout だけを assert すると、非 JSON 出力 / 予期しない block
    reason のどれで落ちたのかが assert メッセージから分からないため、
    returncode と stderr を必ず添える。
    """
    return (
        f"returncode={result.returncode!r} stderr={result.stderr!r} "
        f"stdout={result.stdout!r}"
    )


class _RepoCase(unittest.TestCase):
    """有効な証跡一式を持つ repo（統制群は allow）を用意する基底クラス。"""

    commit_minutes_ago = 0

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        commit_iso = (
            _iso(-self.commit_minutes_ago * 60) if self.commit_minutes_ago else None
        )
        self.repo = _init_repo(self.tmp, commit_iso)
        self.head = _head_sha(self.repo)


# --- A-1: 承認語彙の述語が人間の明示承認を記録できない ----------------------


class MergeApprovalUtteranceTests(unittest.TestCase):
    """A-1: 承認述語の入力域は「閉じた確認への短い返答」。

    元の実装は全文アンカーで、`はい、マージしてください` のような**肯定の応答**まで
    落としていた（`Merge Approval` を記録できず `approval-missing` の恒久 block）。
    前置きを自由にして直すと極性の判定が必要になり、それは regex で閉じない
    （独立レビュー 3 巡で漏れ続けた）。肯定間投詞の前置だけを許して閉じる。
    """

    #: 閉じた確認（`PR #<n> / head <sha> をマージしてよいですか`）への肯定返答。
    APPROVING_REPLIES = [
        "マージして",
        "マージしてください",
        "マージしていい",
        "マージ実行",
        "はい、マージしてください",
        "はい。マージしてください",
        "はい マージして",
        "OK、マージして",
        "了解、マージして",
        "承認、マージして",
        "LGTM, merge it",
        "yes, merge it",
        "merge it",
    ]

    #: 承認語彙を含むが承認ではない発話。列挙で潰していたときに漏れた形を含む。
    NON_APPROVING_UTTERANCES = [
        # 否定。`cannot` は `\bnot\b` の境界が成立せず、列挙方式では漏れていた。
        "cannot merge it",
        "Unable to merge it",
        "It is impossible to merge it",
        "don't merge it",
        "won't merge it",
        "I can't merge it",
        "we shouldn't merge this",
        "do not merge it",
        "I would not merge it",
        "まだマージしないで",
        "テストが通るまでマージしないでください",
        "マージしてはいけません",
        # 拒否・保留の間投詞。
        "no, merge it",
        "Nope, merge it",
        "Nah, merge it",
        "Wait, merge it",
        "I disagree, merge it",
        "Hold off for now, merge it",
        "It's too early to merge it",
        # 条件・時期付き。日本語の条件節は列挙方式では対応が無かった。
        "CI が通ったらマージして",
        "テストが緑になったらマージして",
        "明日マージして",
        "リリース後にマージして",
        "確認が取れ次第マージして",
        # 完了報告・疑問・散文。
        "マージしてしまった",
        "マージして？",
        "マージして再学習まで回す",
    ]

    #: 作業指示であって、この HEAD への承認ではない発話。hook は承認 sha と HEAD の
    #: 一致を要求するので、sha が確定する前のこれらは承認になりえない。作業後に
    #: 閉じた確認を出し、その返答で承認を取る。
    INSTRUCTION_NOT_APPROVAL = [
        "独立セルフレビューしてマージして",
        "レビュー通ったのでマージお願いします",
        "この PR はマージして良い",
        "No problem, マージしてください",
        "PR No. 25 をマージしてください",
    ]

    def test_affirmative_replies_are_recognized(self):
        for text in self.APPROVING_REPLIES:
            with self.subTest(text=text):
                self.assertTrue(is_merge_approval(text))

    def test_non_approval_utterances_stay_rejected(self):
        for text in self.NON_APPROVING_UTTERANCES:
            with self.subTest(text=text):
                self.assertFalse(is_merge_approval(text))

    def test_instructions_are_not_treated_as_approval(self):
        for text in self.INSTRUCTION_NOT_APPROVAL:
            with self.subTest(text=text):
                self.assertFalse(is_merge_approval(text))


# --- 承認述語の 2 つの句読点クラスがずれないこと ------------------------------


class ApprovalPunctuationHasASingleSourceTests(unittest.TestCase):
    """承認返答に許す句読点の定義が 1 箇所であること。

    実測した退行: 肯定間投詞の後ろと承認語彙の後ろで句読点クラスを別々に書いており、
    片方にだけ `。` が無かった（`はい、マージしてください` は True、
    `はい。マージしてください` は False）。列挙を 2 つ持てば必ずずれるので、
    複製の照合ではなく**複製が無いこと**を固定する。
    """

    def test_both_positions_are_built_from_the_same_constant(self):
        """2 つの位置のパターンが、正本の文字クラスを**そのまま**含むこと。

        literal を書き直すと、この包含が崩れて落ちる。
        （`_APPROVAL_REPLY_RE` は human-check 承認の別述語なので対象外。）
        """
        from lib import constants

        canonical = constants._MERGE_APPROVAL_PUNCTUATION
        self.assertIn(canonical, constants._MERGE_APPROVAL_TRAILING_RE)
        self.assertIn(canonical, constants._MERGE_APPROVAL_REPLY_RE.pattern)

    def test_every_punctuation_char_works_in_both_positions(self):
        """正本に載っている文字が、両方の位置で実際に通ること。"""
        from lib import constants

        chars = [
            c for c in constants._MERGE_APPROVAL_PUNCTUATION.strip("[]")
            if c not in "\\s"
        ]
        self.assertGreaterEqual(len(chars), 5, "抽出が空回りしている")
        for char in chars:
            with self.subTest(char=char, position="肯定間投詞の後ろ"):
                self.assertTrue(is_merge_approval(f"はい{char}マージしてください"))
            with self.subTest(char=char, position="承認語彙の後ろ"):
                self.assertTrue(is_merge_approval(f"マージしてください{char}"))


# --- A-1（呼び出し側）: 承認は閉じた確認への返答として取る --------------------


class ClosedConfirmationProtocolTests(unittest.TestCase):
    """A-1: skill の `Merge Approval` 記録手順が指す返答形の正本を、述語が受理すること。

    `is_merge_approval()` は「`PR #<n>` と `head <sha>` を提示した閉じた確認への
    短い返答」だけを受ける。skill の段落は語彙を持たず `MERGE_APPROVAL_PHRASES` を指すので、
    その正本の各語が述語で承認と判定されることを固定する（確認を出す手順の文面は
    本ファイルに機械検査なし）。
    """

    def _approval_paragraph(self) -> str:
        text = PR_FOLLOWUP_SKILL.read_text(encoding="utf-8")
        paragraphs = [p for p in text.split("\n\n") if "`Merge Approval` は" in p]
        self.assertEqual(
            len(paragraphs), 1,
            "SKILL.md の `Merge Approval` 記録手順の段落が 1 つに特定できない",
        )
        return paragraphs[0]

    def test_the_predicate_accepts_the_reply_form_the_skill_points_at(self):
        """skill が指す「受理される返答形」の正本が、実際に承認と判定されること。

        skill は語彙 literal を持たず `MERGE_APPROVAL_PHRASES` を指すだけなので、
        正本側が空・不一致になると手順が指す先が失われる（恒久の不足通知へ戻る）。
        """
        from lib.constants import MERGE_APPROVAL_PHRASES

        self.assertTrue(MERGE_APPROVAL_PHRASES)
        for phrase in MERGE_APPROVAL_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertTrue(is_merge_approval(phrase))
        self.assertIn("MERGE_APPROVAL_PHRASES", self._approval_paragraph())


# --- 大小文字非依存の一致判定が hook を無言終了させないこと --------------------


class EqualsCaseInsensitiveIsSetESafeTests(_RepoCase):
    """`_mg_equals_ci` が `set -euo pipefail` 下で hook を無言終了させないこと。

    `shopt -p <name>` は **option が未設定のとき exit 1 を返す**（既定は未設定）。
    退避の代入 `_saved="$(shopt -p nocasematch)"` はそのため毎回失敗する代入で、
    `if` 条件や `||` の中に無い呼び出し（素の statement / `&&` リストの末尾）に
    置いた瞬間、hook は無出力 exit 1 になる。これは通知を返せない = 素通りで、
    `tr` を排した理由として関数のコメントが「排除した」と書いている失敗モードと
    同じもの。呼び出し位置に依存しない形で閉じる。
    """

    def _run_snippet(self, call: str):
        script = (
            "set -euo pipefail\n"
            + _extract_shell_function(HOOK_SCRIPT, "_mg_equals_ci")
            + "\n" + call + "\necho SURVIVED\n"
        )
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True)

    def test_bare_statement_does_not_kill_the_shell(self):
        result = self._run_snippet('_mg_equals_ci "a" "A"')
        self.assertIn("SURVIVED", result.stdout, f"rc={result.returncode} err={result.stderr}")

    def test_it_still_compares_case_insensitively(self):
        same = self._run_snippet('_mg_equals_ci "https://x/Acme/W" "https://x/acme/w" && echo MATCH')
        self.assertIn("MATCH", same.stdout, same.stderr)
        diff = self._run_snippet('_mg_equals_ci "a" "b" || echo NOMATCH')
        self.assertIn("NOMATCH", diff.stdout, diff.stderr)

    def test_nocasematch_is_restored_after_the_call(self):
        # 復元を落とすと `[[ ]]` 全体が大小文字非依存になり、他の判定が緩む。
        result = self._run_snippet('_mg_equals_ci "a" "A"; shopt nocasematch || echo RESTORED-OFF')
        self.assertIn("RESTORED-OFF", result.stdout, result.stderr)


# --- 閉じ忘れ救済の規約は Route In Progress の reader にも掛かること ------------


class RouteInProgressSharesTheFenceRuleTests(unittest.TestCase):
    """`select_route_in_progress()` が閉じ忘れ救済で旧規約に取り残されないこと。

    閉じ忘れ時に本文を丸ごと読むと、**それ以前の正しく閉じた記入例**まで現在値に
    化ける。`Route In Progress` は done guard の Check 3（`none` 以外なら block）と
    telemetry が読むので、記入例の `none` を拾うと未完了の route を抱えたまま
    done が成立する（fail-open）。

    ここで固定するのは **fence 追跡の側だけ**にする。値の選択規則（最終行採択 /
    正準形優先 / 空値スキップ / 注記除去 / 行頭アンカー）は
    `tests/test_route_in_progress_reader_contract.py` が両 reader を同時に拘束する。

    本 class が awk 側を `gdd_extract_doc_field` で直接叩いているのは、fence 追跡が
    **汎用 reader に**残っていることを見るため（出荷経路は共有 reader
    `gdd_extract_route_in_progress` を通る）。
    """

    #: 「正しく閉じた記入例」＋「後続の閉じ忘れ」。現在値は先頭行。
    STATE = "\n".join([
        "## Gate Status",
        "- Route In Progress: systematic_debugging | reason: T-3 | updated_by: gdd-dev",
        "",
        "解除の書き方:",
        BACKTICK * 3,
        "- Route In Progress: none | reason: 解除 | updated_by: human",
        BACKTICK * 3,
        "",
        "貼り付けたログ:",
        BACKTICK * 3,
        "some log",
    ])

    def test_closed_example_does_not_become_the_current_value(self):
        from lib.tasklist_parse import select_route_in_progress

        self.assertEqual(select_route_in_progress(self.STATE), "systematic_debugging")

    def test_awk_reader_also_skips_the_closed_example(self):
        """awk 側も閉じた記入例を拾わないこと。

        現在値を**記入例より後ろ**に置く。awk は「最初の一致」で返すので、
        fence 追跡が効いていなければ記入例（`none`）が返る。先頭に現在値を置くと
        fence を一切見ない awk でも正解になり、判別力を失う（実測で確認した空洞形）。
        """
        tmp = Path(tempfile.mkdtemp())
        doc = tmp / "state.md"
        doc.write_text("\n".join([
            "## Gate Status",
            "解除の書き方:",
            BACKTICK * 3,
            "- Route In Progress: none | reason: 記入例 | updated_by: human",
            BACKTICK * 3,
            "- Route In Progress: systematic_debugging | reason: T-3 | updated_by: gdd-dev",
        ]) + "\n", encoding="utf-8")
        lib = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
        result = subprocess.run(
            ["bash", "-c", f'. "{lib}"; gdd_extract_doc_field "{doc}" "Route In Progress"'],
            capture_output=True, text=True,
        )
        self.assertTrue(
            result.stdout.strip().startswith("systematic_debugging"),
            f"閉じた記入例を拾っている: {result.stdout.strip()!r}",
        )

    def test_unclosed_fence_content_is_still_readable(self):
        """閉じ忘れ救済そのものは残っていること（落とす側へ倒し過ぎない）。"""
        from lib.tasklist_parse import select_route_in_progress

        state = BACKTICK * 3 + "\n- Route In Progress: systematic_debugging | reason: r | updated_by: u"
        self.assertEqual(select_route_in_progress(state), "systematic_debugging")


# --- A-3: python 解析の失敗で gate が無出力素通りする ------------------------


def _extract_shell_function(path: Path, name: str) -> str:
    """shell script から関数定義 1 つだけを取り出す（hook 全体を実行せずに検査する）。"""
    text = path.read_text(encoding="utf-8")
    start = text.index(f"{name}() {{")
    end = text.index("\n}\n", start) + len("\n}\n")
    return text[start:end]


def _python3_shim(bin_dir: Path, body: str) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / "python3"
    shim.write_text("#!/bin/sh\n" + body)
    shim.chmod(0o755)
    return bin_dir


class ParseFailureFailsClosedTests(_RepoCase):
    """A-3: `gh pr merge` と分かった後の解析失敗は fail-closed（AC-10）。

    python3 不在 / 不正 JSON / import 失敗のいずれでも、承認も証跡も検査せずに
    素通りしてはならない。
    """

    def setUp(self):
        super().setUp()
        _write_state(self.repo, _all_evidence_lines(self.head))

    def test_broken_python3_blocks_with_parse_error(self):
        fake_bin = _python3_shim(self.tmp / "fakebin", "exit 127\n")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            extra_env={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("parse-error", result.stdout)

    def test_block_output_is_valid_json_without_python3(self):
        # block() 自体が python3 に依存していると、この経路で JSON を出せない。
        fake_bin = _python3_shim(self.tmp / "fakebin", "exit 127\n")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            extra_env={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
        )
        parsed = json.loads(result.stdout)
        self.assertNotIn("decision", parsed)
        self.assertTrue(parsed["hookSpecificOutput"]["additionalContext"].strip())

    def test_malformed_payload_json_blocks(self):
        env = {k: v for k, v in os.environ.items() if k not in ("GH_HOST", "GH_REPO")}
        env["HOME"] = str(self.home)
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        env["CLAUDE_CODE_SESSION_ID"] = "test-session"
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            input='{"tool_input": {"command": "gh pr merge 7"',
            capture_output=True, text=True, env=env, cwd=str(self.repo), timeout=HANG_GUARD,
        )
        self.assertIn("parse-error", result.stdout)

    def test_parser_exception_mid_parse_blocks(self):
        """解析が **途中で** 例外になる入力（`json.load` は成功する）。

        完走標識を `json.load` 直後へ前倒しすると、この経路が無検査素通りへ戻る。
        `json.load` より前で落ちるケースだけを踏んでいると、その退行を検出できない。
        """
        # 事前判定（payload に `gh` と `merge`）は通り、parser が例外を投げる形。
        # `tool_input.command` は文字列という前提を崩した payload。
        payload = {"tool_input": {"command": ["merge please", "gh pr merge 7"]}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("parse-error", result.stdout)

    def test_non_gdd_repo_is_not_blocked_by_a_parse_failure(self):
        """gate が管轄しない repo（GDD セッションマーカー不在）は巻き込まない。

        解析失敗を GDD セッション判定より前で不足として通知すると、python3 が壊れた環境の
        `gh` を含む無関係なコマンドまで全 repo で通知が出て、逃げ道が kill-switch だけになる。
        """
        outsider = Path(tempfile.mkdtemp())
        repo = _init_repo(outsider)
        fake_bin = _python3_shim(self.tmp / "fakebin2", "exit 127\n")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, repo, self.home,
            extra_env={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_kill_switch_still_bypasses_parse_failure(self):
        # gate 側の故障で故障が出たときの出口（kill-switch）は効き続けること。
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        fake_bin = _python3_shim(self.tmp / "fakebin", "exit 127\n")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            extra_env={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)


# --- A-4: fenced code block 内の記入例が証跡として読まれる -------------------


def _extract_doc_field(path: Path, field: str) -> str:
    script = (
        f'source "{DETECT_STEERING_LIB}"\n'
        f'gdd_extract_doc_field "{path}" "{field}"\n'
    )
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=HANG_GUARD,
    ).stdout.strip()


class FencedExampleIsNotAFieldTests(_RepoCase):
    """A-4: ``` / ~~~ で囲まれた記入例は canonical field として読まない。

    state.md に書式の記入例を置いただけで `Merge Approval` が成立していた。
    """

    def test_fenced_example_line_is_not_extracted(self):
        doc = self.tmp / "state.md"
        doc.write_text(
            "## Gate Status\n"
            "記入例:\n"
            "```\n"
            "- Merge Approval: PR #7 / head 0123456 | evidence: 例 | approved_at: x\n"
            "```\n"
        )
        self.assertEqual(_extract_doc_field(doc, "Merge Approval"), "")

    def test_tilde_fenced_example_line_is_not_extracted(self):
        doc = self.tmp / "state.md"
        doc.write_text("~~~\n- Next Action: done\n~~~\n")
        self.assertEqual(_extract_doc_field(doc, "Next Action"), "")

    def test_canonical_line_after_a_closed_fence_is_still_read(self):
        doc = self.tmp / "state.md"
        doc.write_text(
            "```\n- Next Action: gdd-task-breakdown\n```\n- Next Action: done\n"
        )
        self.assertEqual(_extract_doc_field(doc, "Next Action"), "done")

    def test_tab_indented_fenced_evidence_does_not_pass_the_gate(self):
        """TAB でインデントした fence に包んだ証跡一式で gate が素通りしないこと。

        fence 判定のインデントを半角スペースだけに狭めると、この形が fence として
        認識されず証跡 4 種が同時に成立し、hook が **無出力で素通り**する
        （実測: 集約時に `^ *` へ狭めて再発した）。抽出層の契約テストとは別に、
        hook を実起動して「不足の通知が出ること」で押さえる。
        """
        fence = "\t" + BACKTICK * 3
        body = "\n".join([fence] + _all_evidence_lines(self.head) + [fence])
        _write_state(self.repo, [])
        state = self.repo / ".steering" / "20260101-demo" / "state.md"
        state.write_text(state.read_text() + body + "\n")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_quadruple_backtick_wrapped_example_is_not_accepted(self):
        """4 連バッククォートで包んだ ``` 入りの記入例で証跡が成立しないこと。

        素朴なトグルは内側の ``` で反転し、記入例が現在値として読まれる。
        """
        fence3 = "`" * 3
        fence4 = "`" * 4
        lines = _all_evidence_lines(self.head)
        _write_state(self.repo, [fence4, fence3] + lines + [fence3, fence4])
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_unclosed_fence_does_not_hide_canonical_fields(self):
        """閉じ忘れた fence でそれ以降の canonical field が消えないこと。

        そこから先を全部落とすと、読み手は routing 材料を失い、書き手バリデータは
        「触った field が無い」と判断して検査自体を飛ばす（fail-open）。
        """
        fence = "`" * 3
        doc = self.tmp / "state.md"
        doc.write_text(
            "例:\n" + fence + "\nsome code\n\n## Gate Status\n- Next Action: done\n"
        )
        self.assertEqual(_extract_doc_field(doc, "Next Action"), "done")

    def test_hook_does_not_accept_a_fenced_approval(self):
        # 承認以外の証跡は本物、承認だけを fence の中に置く（承認だけが落ちる形）。
        lines = _all_evidence_lines(self.head)
        approval, rest = lines[0], lines[1:]
        _write_state(self.repo, ["```", approval, "```"] + rest)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)


# --- AC-2: `env -S` 経由 merge の hook レベル A/B ---------------------------


class EnvSplitStringHookBehaviorTests(_RepoCase):
    """AC-2: `env -S` で包んだ `gh pr merge` が merge gate が実際に不足を通知すること。

    origin/main（HEAD=64e33e0）では is_merge=False のため hook 自体が
    step 2b で exit 0 になり無出力で素通りしていた。
    この 3 形が不足の通知へ倒れることと、正当形が変更前後で不変であることを
    hook サブプロセスの実起動で固定する。
    """

    def test_split_string_with_chdir_flag_blocks_on_target_mismatch(self):
        _write_state(self.repo, [])
        payload = {"tool_input": {"command": "env -S '-C /private/tmp gh pr merge 7'"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout, _hook_diag(result))
        self.assertIn("reason code: pr-target-unresolvable", result.stdout, _hook_diag(result))

    def test_bare_split_string_merge_blocks_on_missing_evidence(self):
        _write_state(self.repo, [])
        payload = {"tool_input": {"command": "env -S 'gh pr merge 7'"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout, _hook_diag(result))
        self.assertIn("reason code: approval-missing", result.stdout, _hook_diag(result))

    def test_previously_undetected_form_blocks_on_missing_evidence(self):
        # `-S` の本体だけでは merge にならない形（`merge 7` が後続引数にある）:
        # 素通りしていた形のうち `env -S 'gh pr' merge 7` を hook サブプロセス
        # でも固定する。origin/main（HEAD=64e33e0）は is_merge=False のため
        # 無出力 exit 0 で素通りしていた。
        _write_state(self.repo, [])
        payload = {"tool_input": {"command": "env -S 'gh pr' merge 7"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout, _hook_diag(result))
        self.assertIn("reason code: approval-missing", result.stdout, _hook_diag(result))

    def test_legitimate_env_assignment_form_is_unaffected(self):
        # 誤爆側の A/B: `env VAR=x gh pr merge 7` は証跡ありなら allow のまま
        # （env -S 分岐が新設する誤爆ではないことの固定）。hook がクラッシュして
        # stdout が空になった場合も `assertNotIn` は素通りしてしまうため、
        # returncode=0 かつ decision field 自体が無い（= 無検査 allow）ことまで
        # 確かめる（他の allow 固定テストと同じ形。独立レビュー L-2）。
        _write_state(self.repo, _all_evidence_lines(self.head))
        payload = {"tool_input": {"command": "env VAR=x gh pr merge 7"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertEqual(result.returncode, 0, _hook_diag(result))
        self.assertNotIn('"hookEventName"', result.stdout, _hook_diag(result))


# --- A-5: `*merge*` の事前判定が payload 全体に掛かる ------------------------


class MergePrefilterScopeTests(_RepoCase):
    """A-5: 事前判定の範囲と、そこで閉じられなかった面。

    A-5 の要求は「`tool_input.command` だけを見る」だったが、bash でその絞り込みは
    成立しない（値の終端探索が値長に対して二乗で効き、hook の timeout を超える。
    `gh` の共起で絞る案はクォート除去後の token を見る解析側と食い違い、
    `g\\h pr merge 7` が gate ごと素通りする）。よって粗いフィルタは `merge` 1 語に
    留めてある。ここでは「何が閉じていて、何が閉じていないか」を実測で固定する。
    """

    def _run_with_python_probe(self, payload):
        probe = self.tmp / "python3-invoked"
        fake_bin = self.tmp / "probebin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        real = subprocess.run(
            ["bash", "-c", "command -v python3"], capture_output=True, text=True,
        ).stdout.strip()
        shim = fake_bin / "python3"
        shim.write_text(f'#!/bin/sh\n: >> "{probe}"\nexec "{real}" "$@"\n')
        shim.chmod(0o755)
        result = _run_hook(
            payload, self.repo, self.home,
            extra_env={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
        )
        return result, probe.exists()

    def test_payload_without_merge_does_not_start_python(self):
        payload = {
            "cwd": "/Users/x/plain/worktree",
            "tool_input": {"command": "ls -la", "description": "list files"},
        }
        result, python_started = self._run_with_python_probe(payload)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)
        self.assertFalse(python_started)

    def test_merge_outside_the_command_still_starts_python(self):
        """閉じられていない面を **意図された挙動として** 固定する。

        cwd / transcript_path / description に merge が入るだけで python3 が 1 回
        起動する（その起動の分だけ遅くなる）。これを閉じるには bash 側で JSON の値を切り出す
        必要があり、それが hook の timeout を超えるため採用していない。
        ここが False になる実装（＝絞り込みを再導入した実装）は、payload 長に対する
        所要時間の回帰テストと合わせて評価すること。
        """
        payload = {
            "cwd": "/Users/x/.gdd/worktrees/repo/20260901-pr-w17-merge-gate",
            "tool_input": {"command": "ls -la"},
        }
        result, python_started = self._run_with_python_probe(payload)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)
        self.assertTrue(python_started)

    def test_quote_obfuscated_gh_still_reaches_the_gate(self):
        """`gh` の共起を事前判定に足すと素通りする形。

        解析側は shlex の**クォート除去後**の token を見るため、payload に literal
        `gh` が現れなくても `is_merge=true` になる。事前判定に `gh` を要求すると
        この 3 形が gate ごと素通りする。
        """
        _write_state(self.repo, [])
        for command in ("g\\h pr merge 7", "'g''h' pr merge 7", 'g""h pr merge 7'):
            with self.subTest(command=command):
                result = _run_hook(
                    {"tool_input": {"command": command}}, self.repo, self.home,
                )
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_large_payload_stays_far_below_the_hook_timeout(self):
        """事前判定が payload 長に対して二乗で効かないことを固定する。

        この hook は全 Bash 呼び出しに掛かり、`hooks/hooks.json` の timeout は 10 秒。
        timeout で kill されると通知を返せないので、遅さはそのまま素通りになる。
        大きな heredoc を含む Bash 呼び出しは日常的なので、payload 長への耐性を測る。
        """
        body = "x" * 200_000
        payload = {
            "cwd": "/Users/x/plain/worktree",
            "tool_input": {"command": f"cat > f <<EOF\n{body}\nEOF\ngh pr merge 7",
                           "description": "write"},
        }
        _write_state(self.repo, [])
        # なぜ CPU 時間（厳）と壁時計（緩）の二本立てにするか: `_run_hook` は
        # bash -> python3 の子孫プロセスを起動する subprocess 計測なので、
        # CPU 律速の退行（payload 長への二乗）は CPU 時間で正確に検出でき、
        # 環境由来の壁時計膨張は backstop 側に切り離せる（ADR-1）。
        with timing_budget() as timing:
            result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertLess(
            timing.cpu_seconds,
            CPU_BUDGET_SEC,
            f"200KB payload で CPU {timing.cpu_seconds:.2f}s"
            f"（wall {timing.wall_seconds:.2f}s, 閾値 {CPU_BUDGET_SEC}s）",
        )
        self.assertLess(
            timing.wall_seconds,
            WALL_BACKSTOP_SEC,
            f"200KB payload で wall {timing.wall_seconds:.2f}s"
            f"（CPU {timing.cpu_seconds:.2f}s, backstop {WALL_BACKSTOP_SEC}s）",
        )

    def test_cmd_key_form_still_reaches_the_gate(self):
        _write_state(self.repo, [])
        result = _run_hook({"tool_input": {"cmd": "gh pr merge 7"}}, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_escaped_quotes_in_the_command_still_reach_the_gate(self):
        _write_state(self.repo, [])
        payload = {"tool_input": {"command": 'echo "a" && gh pr merge 7',
                                  "description": "x"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)


# --- A-6: 鮮度 10 分 / 待機 40 分の境界を実起動で踏む ------------------------


#: 境界の「内側」を作るときに引くマージン（秒）。hook の実起動はこのマージンより十分短いが、
#: `now - limit` ちょうどで書くと hook が動く間に経過が limit を超えて反転する。
#: 外側は経過が増える方向にしか動かないため +1 秒で十分。
_BOUNDARY_SLACK_SEC = 10


class RecheckFreshnessBoundaryTests(_RepoCase):
    """A-6: `Pre-Merge Review Recheck` の鮮度上限（10 分）の境界。"""

    LIMIT_SEC = MERGE_GATE_RECHECK_FRESHNESS_MINUTES * 60

    def _run_with_recheck_age(self, age_sec):
        _write_state(self.repo, [
            _approval_line(self.head),
            f"- Pre-Merge Review Recheck: {self.head} | new_blocking: 0 "
            f"| at: {_iso(-age_sec)}",
        ])
        return _run_hook({"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home)

    def test_just_inside_the_limit_is_not_stale(self):
        result = self._run_with_recheck_age(self.LIMIT_SEC - _BOUNDARY_SLACK_SEC)
        self.assertNotIn("recheck-stale", result.stdout)

    def test_just_past_the_limit_is_stale(self):
        result = self._run_with_recheck_age(self.LIMIT_SEC + 1)
        self.assertIn("recheck-stale", result.stdout)


class ReviewWaitBoundaryTests(_RepoCase):
    """A-6: bot レビュー待機（40 分）の境界。

    待機が経過していなければ `review-wait-not-elapsed`、経過していれば独立レビュー
    の検査へ進む（= `independent-review-missing`）。fixture は Independent Review を
    置かないため、待機免除（HEAD・high 0 の独立レビュー）は成立しない。
    """

    LIMIT_SEC = MERGE_GATE_REVIEW_WAIT_MINUTES * 60
    commit_minutes_ago = MERGE_GATE_REVIEW_WAIT_MINUTES + 5

    def _run_with_push_age(self, age_sec):
        push_at = _iso(-age_sec)
        _write_state(self.repo, [
            _approval_line(self.head),
            f"- Pre-Merge Review Recheck: {self.head} | new_blocking: 0 | at: {_iso()}",
            f"- Last Review Push At: {self.head} | at: {push_at}",
            f"- Bot Review Received: {self.head} | received: no | at: {push_at}",
        ])
        return _run_hook({"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home)

    def test_just_inside_the_limit_still_waits(self):
        result = self._run_with_push_age(self.LIMIT_SEC - _BOUNDARY_SLACK_SEC)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def test_just_past_the_limit_requires_the_independent_review(self):
        result = self._run_with_push_age(self.LIMIT_SEC + 1)
        self.assertNotIn("review-wait-not-elapsed", result.stdout)
        self.assertIn("independent-review-missing", result.stdout)


class HookEnvIsolationTests(_RepoCase):
    """A-6: hook 実起動 helper が `GH_HOST` / `GH_REPO` を継承しないこと。"""

    def test_ambient_gh_repo_does_not_change_the_verdict(self):
        _write_state(self.repo, _all_evidence_lines(self.head))
        with_ambient = dict(os.environ)
        try:
            os.environ["GH_REPO"] = "org/otherrepo"
            os.environ["GH_HOST"] = "ghe.example.com"
            result = _run_hook(
                {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            )
        finally:
            os.environ.clear()
            os.environ.update(with_ambient)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)


# --- A-7: パーサの誤読・誤通知 ---------------------------------------------


class AuthorEmailShortFlagTests(_RepoCase):
    """A-7: `-A`（`--author-email` の短縮形）の値を位置引数として読まない。"""

    def test_short_flag_value_is_not_read_as_a_pr_number(self):
        result = parse_gh_pr_merge("gh pr merge 23 -A 99", "", "/repo")
        self.assertEqual(result["pr_number"], "23")

    def test_short_flag_value_is_not_read_as_a_branch(self):
        result = parse_gh_pr_merge("gh pr merge 23 -A alice@example.com", "", "/repo")
        self.assertEqual(result["pr_number"], "23")
        self.assertFalse(result["unresolvable"])

    def test_hook_allows_a_merge_with_the_short_flag(self):
        _write_state(self.repo, _all_evidence_lines(self.head))
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7 -A alice@example.com"}},
            self.repo, self.home,
        )
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)


class DefaultGhHostIsNotAConflictTests(_RepoCase):
    """A-7: `GH_HOST=github.com` は既定ホストの明示であって repo 決定要因ではない。"""

    def test_default_host_prefix_is_not_a_conflict(self):
        result = parse_gh_pr_merge("GH_HOST=github.com gh pr merge 7", "", "/repo")
        self.assertFalse(result["env_repo_conflict"])

    def test_non_default_host_prefix_is_still_a_conflict(self):
        result = parse_gh_pr_merge("GH_HOST=ghe.example.com gh pr merge 7", "", "/repo")
        self.assertTrue(result["env_repo_conflict"])

    def test_gh_repo_prefix_is_still_a_conflict(self):
        result = parse_gh_pr_merge("GH_REPO=org/other gh pr merge 7", "", "/repo")
        self.assertTrue(result["env_repo_conflict"])

    def test_hook_allows_with_default_host_in_process_env(self):
        _write_state(self.repo, _all_evidence_lines(self.head))
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            extra_env={"GH_HOST": "github.com"},
        )
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_hook_still_blocks_on_a_non_default_host(self):
        _write_state(self.repo, _all_evidence_lines(self.head))
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            extra_env={"GH_HOST": "ghe.example.com"},
        )
        self.assertIn("pr-target-unresolvable", result.stdout)


class OwnerRepoCaseFoldingTests(_RepoCase):
    """A-7: owner/repo の照合は大小文字を区別しない（GitHub の実仕様に合わせる）。"""

    def test_case_differing_repo_flag_still_allows(self):
        _write_state(self.repo, _all_evidence_lines(self.head),
                     pr_url="https://github.com/Acme/Widgets/pull/7")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge -R acme/widgets 7"}},
            self.repo, self.home,
        )
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_case_differing_repo_flag_on_the_command_side_still_allows(self):
        """コマンド側が mixed case（`-R Acme/Widgets`）でも別 repo 扱いにしない。

        state 側だけを正規化しても閉じない。`_mg_owner_repo`（コマンド側・origin 側の
        正規化）を外す変異は、state 側を大文字にした fixture では検出できない。
        """
        _write_state(self.repo, _all_evidence_lines(self.head))
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge -R Acme/Widgets 7"}},
            self.repo, self.home,
        )
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_case_differing_origin_remote_still_allows(self):
        """origin remote の owner/repo が mixed case でも別 repo 扱いにしない。"""
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "set-url", "origin",
             "https://github.com/Acme/Widgets.git"], check=True,
        )
        _write_state(self.repo, _all_evidence_lines(self.head))
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
        )
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_case_differing_url_argument_still_reaches_the_gate(self):
        """コマンド側が mixed case の URL でも gate 対象から外れないこと。

        `active: false`（merge 時の既定状態）では、gate 対象判定を外れると承認も
        証跡も検査せずに素通りする。state 側だけを正規化しても閉じない。
        """
        _write_state(self.repo, [], pr_url="https://github.com/acme/widgets/pull/7",
                     active=False)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge https://github.com/Acme/Widgets/pull/7"}},
            self.repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_case_differing_url_matches_across_multiple_steerings(self):
        """steering が複数ある経路（`_mg_match_steering_by_target`）でも大小文字を吸収。

        **「不足として通知されないこと」で確かめてはいけない。** 一致に失敗した場合の
        行き先は `_MG_MATCH_STATUS=none` → `unresolved-steering-on-merge` の
        **無言の素通り**（AC-6(a)）であり、一致成功時の allow と出力上は
        区別が付かない。実測で、一致分岐を `false` に潰す変異が素通りした。

        そこで証跡を 1 つ欠いた state.md を置き、**一致したときだけ現れる不足の通知**
        （`approval-missing`）で確かめる。一致に失敗すると通知が消えて落ちる。
        """
        _write_state(self.repo, _all_evidence_lines(self.head)[1:],
                     pr_url="https://github.com/Acme/Widgets/pull/7", active=False)
        other = self.repo / ".steering" / "20260102-followup"
        other.mkdir(parents=True, exist_ok=True)
        (other / "state.md").write_text(
            "## Gate Status\n- Resume From: done\n- Next Action: done\n"
            "- PR URL: https://github.com/acme/other/pull/99\n"
        )
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge https://github.com/acme/widgets/pull/7"}},
            self.repo, self.home,
        )
        self.assertIn("approval-missing", result.stdout)

    def test_case_differing_url_still_allows_when_evidence_is_complete(self):
        # 上の通知が「大小文字を吸収できている」ことの裏返しであることを固定する
        # （証跡が揃っていれば同じ入力で通知しない）。
        _write_state(self.repo, _all_evidence_lines(self.head),
                     pr_url="https://github.com/Acme/Widgets/pull/7", active=False)
        other = self.repo / ".steering" / "20260102-followup"
        other.mkdir(parents=True, exist_ok=True)
        (other / "state.md").write_text(
            "## Gate Status\n- Resume From: done\n- Next Action: done\n"
            "- PR URL: https://github.com/acme/other/pull/99\n"
        )
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge https://github.com/acme/widgets/pull/7"}},
            self.repo, self.home,
        )
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_a_different_repo_still_blocks(self):
        _write_state(self.repo, _all_evidence_lines(self.head))
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge -R org/otherrepo 7"}},
            self.repo, self.home,
        )
        self.assertIn("pr-target-unresolvable", result.stdout)


class AsciiCaseFoldingTests(unittest.TestCase):
    """A-7 追補: 大小文字の正規化を ASCII に固定する。

    `tr '[:upper:]' '[:lower:]'` の写像は POSIX 上ロケール依存で、実装によっては
    `I` が `i` 以外へ落ちる（トルコ語ロケールの dotless i）。owner/repo は ASCII
    なので `LC_ALL=C` に固定すれば環境差で照合が揺れない。
    """

    CASE_FOLD_RE = re.compile(r"(?:(LC_ALL=C)\s+)?tr\s+'\[:upper:\]'\s+'\[:lower:\]'")
    #: 走査母集合は出荷 script 全域（merge gate だけ直すと同型が他 hook に残る）。
    SCAN_DIRS = ("hooks", "scripts", "bin")

    def _scan(self):
        found = []
        for name in self.SCAN_DIRS:
            root = PLUGIN_ROOT / name
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.suffix not in (".sh", ".py", ""):
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                for match in self.CASE_FOLD_RE.finditer(text):
                    found.append((path.relative_to(PLUGIN_ROOT), match.group(1)))
        return found

    def test_every_case_fold_is_pinned_to_the_c_locale(self):
        found = self._scan()
        self.assertTrue(found, "大小文字の正規化が 1 箇所も見つからない（走査の空洞化）")
        unpinned = [str(path) for path, pinned in found if pinned is None]
        self.assertEqual(unpinned, [], f"LC_ALL=C で固定されていない: {unpinned}")


# --- completion-check の指摘: tr -d の非移植な range 指定 --------


class TrDeleteRangeSafetyTests(unittest.TestCase):
    """`tr -d '<set>'` の文字集合内で `-` が range 演算子として誤解釈されない
    ことを固定する。

    `tr -d '_-*[:space:]'` は `_`（0x5F）から `*`（0x2A）への range と解釈され、
    GNU coreutils は "reverse collating sequence order" で reject して非 0
    終了する（BSD tr は許容するため macOS 開発機では再現しない）。
    `set -euo pipefail` の hook 内でこれが起きると block() を出す前に落ち、
    merge gate 全体が無出力で素通りする（gate の指摘で実測）。

    `-` は文字集合の**先頭または末尾**に置けば literal として扱われ、
    range 解釈を回避できる（POSIX / GNU 共通の安全な書き方）。
    """

    # 引用符は単一/二重の両方、フラグは `-d` の前後どちらでも（`-cd` / `-s -d` 等の
    # 併用も含め）許容する。2-set の translate 形（`tr 'A' 'B'`）は `-d` を伴わないが
    # set1 に同じ range hazard があり得るため、`-d` の有無を問わず「`tr` に続く
    # クォート済み引数」をすべて拾う（Round 15 M-2: 旧 regex は `tr -d '...'` の
    # 単一引用符のみに一致し、二重引用符・`-cd`/`-s` 併用・2-set translate 形の
    # いずれも素通ししていた）。
    # 2 番目の quoted 引数（`-d` を伴わない 2-set translate 形の set2）は任意で
    # 追加マッチする。set1 だけの `tr -d '...'` 形では group(2) は None のまま。
    TR_ARG_RE = re.compile(
        r"""tr\s+(?:-[a-zA-Z]+\s+)*('[^']*'|"[^"]*")(?:\s+('[^']*'|"[^"]*"))?"""
    )
    SCAN_DIRS = ("hooks", "scripts", "bin")

    @classmethod
    def _extract_args(cls, text: str) -> list[str]:
        args = []
        for match in cls.TR_ARG_RE.finditer(text):
            for group in match.groups():
                if group is not None:
                    args.append(group[1:-1])  # クォートを剥がす
        return args

    def _scan(self):
        found = []
        for name in self.SCAN_DIRS:
            root = PLUGIN_ROOT / name
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.suffix not in (".sh", ".py", ""):
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                for char_set in self._extract_args(text):
                    found.append((path.relative_to(PLUGIN_ROOT), char_set))
        return found

    @staticmethod
    def _hyphen_is_unsafe(char_set: str) -> bool:
        # POSIX bracket 式（`[:space:]` 等）を 1 トークンとして扱ってから、
        # **すべての** `-` トークンについて先頭・末尾のどちらでもない位置に
        # あるかを判定する（Round 15 M-2: 旧実装は最初の `-` だけを見ており、
        # `-a_-*b` のように先頭が安全な `-` でも 2 個目以降に危険な `-` が
        # 埋め込まれているケースを見逃していた）。
        tokens = re.findall(r"\[:[a-z]+:\]|.", char_set)
        last_idx = len(tokens) - 1
        return any(
            token == "-" and idx != 0 and idx != last_idx
            for idx, token in enumerate(tokens)
        )

    def test_the_scan_is_not_hollow(self):
        found = self._scan()
        self.assertTrue(found, "`tr` 呼び出しが 1 箇所も見つからない（走査の空洞化）")

    def test_the_scan_covers_the_hooks_directory(self):
        # SCAN_DIRS からディレクトリを 1 つ落としても `found` が非空のままなら
        # 上記の非空洞性検査は green を維持してしまう（Round 15 M-2: `hooks` を
        # 落としても `scripts/` の hit で green だった）。`hooks/` 配下の実ファイルが
        # 走査結果に実在することを個別に固定する。`merge-gate-evidence.sh` は
        # 本 remediation（M-1）で `tr` 依存を完全に除去したため対象にしない
        # （それ自体が H-1 の恒久解消であり、対象に含めないのが正しい）。
        found = self._scan()
        scanned_paths = {str(path) for path, _ in found}
        self.assertIn(
            "hooks/scripts/run-session-start-hook.sh", scanned_paths,
            "`hooks/` 配下の `tr` 呼び出しが走査結果に含まれない"
            "（SCAN_DIRS の縮小等で `hooks/` が脱落している可能性）",
        )

    def test_no_tr_arg_has_an_unsafe_hyphen_position(self):
        found = self._scan()
        unsafe = [
            (str(path), char_set) for path, char_set in found
            if self._hyphen_is_unsafe(char_set)
        ]
        self.assertEqual(
            unsafe, [],
            f"`tr` の引数（delete-set / translate set）内で `-` が先頭/末尾以外に"
            f"ある（GNU coreutils で range 誤解釈により reject されうる）: {unsafe}",
        )

    def test_self_check_positive_and_negative_fixtures_are_detected(self):
        # 判別力の自己検証（空洞化防止）。
        self.assertFalse(self._hyphen_is_unsafe("_*[:space:]-"))  # 末尾 = 安全
        self.assertFalse(self._hyphen_is_unsafe("-_*[:space:]"))  # 先頭 = 安全
        self.assertFalse(self._hyphen_is_unsafe("_*[:space:]"))  # `-` 無し
        self.assertTrue(self._hyphen_is_unsafe("_-*[:space:]"))  # 中間 = 危険（実際の bug）
        self.assertTrue(self._hyphen_is_unsafe("-a_-*b"))  # 先頭は安全だが 2 個目が中間 = 危険

    def test_double_quoted_delete_set_is_scanned(self):
        # 旧 regex（単一引用符のみ）は二重引用符の delete-set を見逃していた。
        sample = 'printf x | tr -d "_-*"'
        self.assertEqual(self._extract_args(sample), ["_-*"])

    def test_two_set_translate_form_is_scanned(self):
        # `tr '[:upper:]' '[:lower:]'` のような 2-set 形（`-d` を伴わない）も
        # set1・set2 の両方を拾えることを固定する。
        sample = "tr '[:upper:]' '[:lower:]'"
        self.assertEqual(self._extract_args(sample), ["[:upper:]", "[:lower:]"])

    def test_flag_combinations_before_and_after_d_are_scanned(self):
        for sample in ("tr -cd '_-*'", "tr -s -d '_-*'", "tr -d -s '_-*'"):
            with self.subTest(sample=sample):
                self.assertIn("_-*", self._extract_args(sample))


# --- A-8: 出荷物に steering-local な識別子が残る -----------------------------


class NoSteeringLocalIdentifierTests(unittest.TestCase):
    """A-8: 出荷物から解決できない識別子を merge gate の実装に残さない。

    `ADR-n` / `gate #n` / レビュー回の finding ID（`F-1` / `M-3` / `H-1` …）は
    `.steering/`（gitignore 済み・worktree 削除で消える）内の識別子で、
    plugin の利用者からは辿れない。markdown 側は除去済みなので実装側も揃える。
    """

    #: 検査対象は本 finding が名指しした 2 file。`AC-n` / `design.md §` は
    #: 出荷 hook 8 本以上で使われている repo 全体の記法なので対象外。
    TARGETS = (HOOK_SCRIPT, GH_PARSE_SOURCE)
    FORBIDDEN = (
        re.compile(r"ADR-\d+"),
        re.compile(r"gate #\d+"),
        re.compile(r"\b(?:F|M|H|A|T|RF|G)-\d+[A-Za-z0-9]*\b"),
    )

    def test_targets_carry_no_steering_local_identifier(self):
        for path in self.TARGETS:
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                for pattern in self.FORBIDDEN:
                    with self.subTest(path=path.name, lineno=lineno, pattern=pattern.pattern):
                        self.assertIsNone(
                            pattern.search(line),
                            f"{path.name}:{lineno}: 解決できない識別子 / {line.strip()}",
                        )

    def test_the_scan_is_not_hollow(self):
        # 検査自体が空回りしていないことを固定する（パターンの判別力の自己検証）。
        for pattern, sample in (
            (self.FORBIDDEN[0], "ADR-14 に従う"),
            (self.FORBIDDEN[1], "gate #15 H-1 の remediation"),
            (self.FORBIDDEN[2], "F-1 の root cause"),
        ):
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNotNone(pattern.search(sample))


if __name__ == "__main__":
    unittest.main()
