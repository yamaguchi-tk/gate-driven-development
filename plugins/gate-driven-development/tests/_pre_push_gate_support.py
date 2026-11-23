"""pre-push gate の契約テストが共有する fixture（一時 repo・state.md・証跡行・hook 起動）。

`test_pre_push_gate_contract.py` が 2,000 行を超えたので、テストを関心ごとのファイルに
分けた。各ファイルは `PrePushGateFixtureMixin` を `unittest.TestCase` と一緒に継承する。
mixin は TestCase ではないので、どのファイルから import しても test は二重に収集されない。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from _paths import PLUGIN_ROOT
from _git_fixture import init_repo

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-push-gate-hook.sh"
# fixture が作る steering slug の既定値。否定側検査（slug が reason へ漏れない）で
# 実値と突き合わせるため、`_write_steering` の default と同じ 1 本を使う。
DEFAULT_STEERING_SLUG = "20260817-t9"



# AC-18 の block reason の許可トークン集合（design.md § block reason の許可トークン集合 1〜6）。
# 後から緩めない（下の test の docstring）。tip で解いた経路の reason も同じ集合で検査する。
AC18_ALLOWED_TOKENS = frozenset(
    {
        # 1. 固定メッセージカタログの語
        "pre-push", "gate", "Pre-Push", "Self", "Review", "push", "ref",
        "tip", "sha", "reason", "code", "key", "escape", "hatch",
        "Independent", "high", "blocking", "Carry",
        "opt-out", "bash", "c", "eval", "git", "git-dir", "work-tree",
        # 2. reason code
        "missing-evidence", "sha-mismatch", "dry-not-reached",
        "refspec-ambiguous", "unresolvable-root", "optout-log-write-failed",
        "independent-review-missing", "independent-review-stale",
        "independent-review-high", "steering-multiple", "steering-unreadable",
        # 3. 欠落 key 名（self-review 証跡 / Independent Review 証跡）
        "rounds", "consecutive_clean", "dry", "lanes",
        "reviewer", "context", "medium", "at",
        # `context` の固定値ドメイン（独立レビュー契約の diff-only）
        "diff-only",
        # 5. Task Size の 4 リテラル + 表示語
        "Task", "Size", "trivial", "quick", "express", "standard", "yes",
        # 6. 固定ファイル名リテラル + escape hatch 1 行
        "<steering-dir>/state.md", "references/self-review-lanes.md", "references/independent-review.md",
        "GDD_SKIP_PRE_PUSH_GATE=1",
    }
)
AC18_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
# ASCII の語だけを抜き出す（日本語の固定文言は allow-list 1 に含まれるため対象外）
AC18_TOKEN_RE = re.compile(r"[A-Za-z0-9_<][A-Za-z0-9_./<>=-]*")


class PrePushGateFixtureMixin:
    def _init_repo(self, path: Path, *, default_branch: str = "main") -> None:
        init_repo(path, branch=default_branch)

    def _write_local_state(
        self, path: Path, *, active: bool = True, session_id: str = "test-session"
    ) -> None:
        state_dir = path / ".claude"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "gdd-dev.local.md").write_text(
            f"---\nactive: {str(active).lower()}\nsession_id: {session_id}\n---\n",
            encoding="utf-8",
        )

    def _run_hook(
        self,
        cwd: Path,
        command: str,
        *,
        extra_env: dict[str, str] | None = None,
        tool_cwd: Path | None = None,
        tool_cwd_key: str = "cwd",
        drop_env: tuple[str, ...] = (),
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        tool_input: dict[str, str] = {"command": command}
        if tool_cwd is not None:
            tool_input[tool_cwd_key] = str(tool_cwd)
        payload = {"tool_name": "Bash", "tool_input": tool_input}
        env = os.environ.copy()
        env.update(
            {
                "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                "CLAUDE_CODE_SESSION_ID": "test-session",
            }
        )
        if extra_env:
            env.update(extra_env)
        # `drop_env` は「その変数が **無い** ときの hook 挙動」を固定するための穴。
        # 既定の env 構築は os.environ.copy() で HOME を必ず持つため、set -u 由来の
        # 即死経路（gdd_sr_log_event の ${HOME} 展開失敗）は fixture から原理的に
        # 踏めない（tests/_merge_gate_support.py の _run_hook と同じ意味・同じ
        # コメント方針）。
        for _name in drop_env:
            env.pop(_name, None)
        return subprocess.run(
            ["bash", str(HOOK)],
            cwd=cwd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=timeout,
        )

    # ---- T-9 helpers: .steering/<slug>/state.md + Pre-Push Self Review 証跡 ---

    def _head_sha(self, repo: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _evidence_line(
        self,
        *,
        sha: str,
        rounds: str = "2",
        consecutive_clean: str = "2",
        dry: str = "yes",
        lanes: str = "internal=2,grounding=not_applicable(no-external-dep),adversarial=1",
        at: str = "2026-08-17T12:00:00Z",
    ) -> str:
        return (
            f"{sha} | rounds: {rounds} | consecutive_clean: {consecutive_clean} "
            f"| dry: {dry} | lanes: {lanes} | at: {at}"
        )

    def _independent_review_line(
        self,
        *,
        sha: str,
        reviewer: str = "gdd-independent-reviewer",
        high: str = "0",
        medium: str = "0",
        blocking: str = "0",
        at: str = "2026-08-17T12:00:00Z",
    ) -> str:
        """`Independent Review` 行（正本: self-review-lanes.md § merge gate 証跡）。"""
        return (
            f"{sha} | reviewer: {reviewer} | context: diff-only | high: {high} "
            f"| medium: {medium} | blocking: {blocking} | at: {at}"
        )

    def _write_steering(
        self,
        repo: Path,
        *,
        slug: str = DEFAULT_STEERING_SLUG,
        resume_from: str = "gdd-implementation-gating",
        next_action: str = "gdd-implementation-gating",
        task_size: str = "standard",
        evidence: str | None = None,
        independent_review: str | None = None,
        auto_independent_review: bool = True,
        task_id: str | None = None,
        worktree: Path | None = None,
        branch: str | None = None,
    ) -> Path:
        steering = repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        lines = [
            f"Resume From: {resume_from}\n",
            "Human Check Status: approved\n",
            "Route In Progress: none\n",
            f"Next Action: {next_action}\n",
            f"Task Size: {task_size}\n",
            "Started At: 2026-08-17T00:00:00Z\n",
        ]
        if task_id is not None:
            lines.insert(0, f"Task ID: {task_id}\n")
        if worktree is not None:
            lines.append(f"Worktree: {worktree}\n")
        if branch is not None:
            lines.append(f"Branch: {branch}\n")
        if evidence is not None:
            lines.append(f"Pre-Push Self Review: {evidence}\n")
        # standard は step 13b で `Independent Review` 行を要求する（2026-09-06）。
        # 既存 fixture が step 13b の手前で観測している分岐を保つため、明示指定が
        # 無ければ証跡と同じ sha の有効な行を自動で足す（否定側は明示的に作る）。
        if independent_review is None and auto_independent_review and evidence is not None:
            independent_review = self._independent_review_line(
                sha=evidence.split("|", 1)[0].strip()
            )
        if independent_review is not None:
            lines.append(f"Independent Review: {independent_review}\n")
        (steering / "state.md").write_text("".join(lines), encoding="utf-8")
        return steering

    def _register_binding(self, repo: Path, state_path: Path) -> None:
        subprocess.run(
            [
                "python3",
                str(PLUGIN_ROOT / "scripts" / "gdd_task_binding.py"),
                "upsert-from-state",
                "--repo-root",
                str(repo),
                "--state",
                str(state_path),
            ],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )

    # ---- T-12: opt-out 肯定/否定側（Step 0 で未充足と確定した surface のみ）----

    def _decision(self, result: subprocess.CompletedProcess[str]) -> str | None:
        """実行後の通知（PreToolUse の additionalContext）を出したら "notice" を返す。素通り（空 stdout）なら None。

        T-13 / T-14 が消費する共有 helper（T-11 廃止に伴い T-12 が所有 — ADR-8
        Addendum / planning reviewer H-2）。`json.loads` を直に書くと素通りケースが
        `JSONDecodeError` になり「通知しなかった」と「出力が壊れた」を区別できない。
        """
        if not result.stdout.strip():
            return None
        payload = json.loads(result.stdout)
        self.assertNotIn("decision", payload)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return "notice"
