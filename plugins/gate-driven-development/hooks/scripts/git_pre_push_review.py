"""git の pre-push hook の判定（git-pre-push-review-hook.sh から呼ぶ。log-only）。

引数は git が渡す remote の名前と URL、stdin は `<local ref> <local sha> <remote ref> <remote sha>` の行。
GitHub の remote の branch で、PR が open のものへの push ごとに、次のどれかをログ
（`<state dir>/push-review.log`、0600）に 1 行書く。

- `reviewed`: push する tip の commit 時刻の次の秒以降に、reviewer の Agent が起動して成功で終わっている
- `exempt-only`: 最後に成功した reviewer の起動の前の commit から tip までの変更が、その commit の
  `.gdd-config.md` で宣言したレビュー不要のパスだけ
- `would-deny`: どちらでもない。reason は `no-reviewer`・`reviewer-incomplete`（tip の後の reviewer が
  まだ終わっていない。起動応答が読めず、通知もまだ無い background の起動を含む）・`reviewer-failed`（tip の後の reviewer がエラー・停止で終わった）・
  `changed-after-review`（成功した reviewer の後に、宣言の外の変更がある）・`other-agent-only`
  （tip の後に起動したのが reviewer 以外の Agent だけ）
- `not-github`・`no-pr`・`gh-unknown`・`no-transcript`・`error`: 判定の前に止まったもの
- `skipped`: 1 回の push で ref が `MAX_REFS` を超えた分（まとめて 1 行）

reviewer は、subagent_type の `:` より後ろが `REVIEWERS` のどれかと一致する Agent（Task）だけを数える。
description などの自由文は読まない。Skill は数えない（Skill の起動は手順の最初で、レビューが終わった
ことを示さない）。`GDD_PUSH_REVIEW_GH_BIN` はテスト用の gh の差し替えで、絶対パスのときだけ使う。
"""
from __future__ import annotations

import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

if sys.flags.isolated or getattr(sys.flags, "safe_path", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.transcript import ParsedTranscript, inflight_dispatch_ids, parse_transcript  # noqa: E402

# 独立レビューでない reviewer（gdd-completion-reviewer など）も数える。log-only の間はログの `by:` で
# 分け、止める側に切り替えるときに受理する集合を決める
REVIEWERS = frozenset({
    "light-lane-independent-reviewer",
    "light-lane-independent-reviewer-xhigh",
    "gdd-implementation-reviewer",
    "gdd-completion-reviewer",
    "gdd-security-reviewer",
    "code-reviewer",
})
ZERO_SHA = re.compile(r"\A0+\Z")
GITHUB_REMOTE = re.compile(
    r"\A(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"(?P<owner>[A-Za-z0-9._-]+)/(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?/?\Z"
)
EXEMPT_FIELD = "GDD Push Review Exempt Paths:"
# 宣言の値（git の pathspec に渡す）。`:`（pathspec の magic）・`..`・絶対パスは受け付けない。
# 英数字を含まない値（`.`・`*` など、全体を除きうるもの）も受け付けない
EXEMPT_VALUE = re.compile(r"\A[A-Za-z0-9._*-][A-Za-z0-9._/*-]*\Z")
UNSAFE_LOG_CHARS = re.compile(r"[^A-Za-z0-9._:+@-]")
GH_TIMEOUT_SECS = 5
MAX_REFS = 10
MAX_LOGGED_AGENTS = 3


def _git(*args: str) -> subprocess.CompletedProcess:
    # UTF-8 でない出力（Shift_JIS の設定ファイルなど）は、読めない値として扱う側に倒す
    return subprocess.run(["git", *args], capture_output=True, text=True, errors="replace", timeout=30)


def _hash8(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


def _clean(value: object) -> str:
    return UNSAFE_LOG_CHARS.sub("_", value)[:80] if isinstance(value, str) and value else "-"


def _epoch(ts: object) -> float | None:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _github_repo(remote: str, url: str) -> str | None:
    """push 先の owner/repo。remote の名前なら書き換え（insteadOf）の前の pushurl も見る。

    候補（pushurl、無ければ url、git が渡した書き換え後の URL）の順に、最初に github.com に当たった
    ものを使う。pushurl が複数あると git は URL ごとに hook を呼ぶので、1 回の push で行が複数になる。
    """
    candidates: list[str] = []
    if remote:
        # git は pushurl があると url には push しない
        for key in ("pushurl", "url"):
            r = _git("config", "--get-all", f"remote.{remote}.{key}")
            if r.returncode == 0 and r.stdout.split():
                candidates.extend(r.stdout.split())
                break
    candidates.append(url)
    for raw in candidates:
        m = GITHUB_REMOTE.match(raw)
        if m:
            return f"{m.group('owner')}/{m.group('repo')}"
    return None


def _open_pr_count(repo: str, branch: str) -> int | None:
    gh = os.environ.get("GDD_PUSH_REVIEW_GH_BIN") or shutil.which("gh") or ""
    if not os.path.isabs(gh):
        return None
    try:
        r = subprocess.run(
            [gh, "pr", "list", "--repo", repo, "--head", branch, "--state", "open",
             "--json", "number", "--jq", "length"],
            capture_output=True, text=True, errors="replace", timeout=GH_TIMEOUT_SECS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and re.fullmatch(r"[0-9]+", out) else None


def _exempt_paths(commit: str) -> list[str]:
    """commit の `.gdd-config.md` の宣言を読む。読めない・書式が違うときは空（止める側）。

    コードフェンス（バッククォート・チルダ 3 つ）と HTML コメントの開始を 1 つでも含むファイルは
    読まない（その中に書いた宣言を有効にしないため。`<details>` などほかの HTML ブロックは区別しない）。そのうえで、行頭から
    `GDD Push Review Exempt Paths:` で始まる行が 1 つだけのときに使う。
    """
    r = _git("show", f"{commit}:.gdd-config.md")
    if r.returncode != 0 or any(mark in r.stdout for mark in ("```", "~~~", "<!--")):
        return []
    found = [line[len(EXEMPT_FIELD):] for line in r.stdout.split("\n") if line.startswith(EXEMPT_FIELD)]
    if len(found) != 1:
        return []
    values = found[0].split()
    valid = all(EXEMPT_VALUE.match(v) and ".." not in v and re.search(r"[A-Za-z0-9]", v) for v in values)
    return values if values and valid else []


def _reviewer_outcomes(tv: ParsedTranscript) -> list[tuple[str, float, str, object]]:
    """reviewer の起動ごとに (結果, 起動時刻, subagent_type, timestamp)。結果は ok・running・failed。"""
    inflight = inflight_dispatch_ids(tv)
    completed = {i for pair in tv.completed_notifications for i in pair if i}
    notified = {tid for _, tid in tv.task_notifications if tid}
    outcomes = []
    for launch in tv.launches:
        t = _epoch(launch.timestamp)
        if launch.name not in {"Agent", "Task"} or t is None:
            continue
        if launch.subagent_type.rsplit(":", 1)[-1] not in REVIEWERS:
            continue
        agent_id = tv.dispatch_agent_ids.get(launch.tool_use_id)
        errored = launch.tool_use_id in tv.error_tool_result_ids
        if launch.tool_use_id in inflight:
            result = "running"
        elif agent_id is not None:
            result = "ok" if {launch.tool_use_id, agent_id} & completed else "failed"
        elif launch.run_in_background:
            # 起動応答が読めない background の起動は、通知の <tool-use-id> で終わりを見る
            if launch.tool_use_id in completed:
                result = "ok"
            elif errored or launch.tool_use_id in notified:
                result = "failed"
            else:
                result = "running"
        else:
            result = "failed" if errored else "ok"
        outcomes.append((result, t, launch.subagent_type, launch.timestamp))
    return outcomes


def _only_exempt_changes_since(reviewed_at: int, sha: str) -> bool:
    """reviewer の起動の前の commit から sha までの変更が、その commit の宣言のパスだけか。"""
    # 起動と同じ秒の commit は、レビューが見たかどうか分からないので含めない
    reviewed_point = _git(
        "rev-list", "-1", "--first-parent", f"--before=@{reviewed_at - 1}", sha,
    ).stdout.strip()
    exempt = _exempt_paths(reviewed_point) if reviewed_point else []
    if not exempt:
        return False
    # wildcard を含む値は、末尾の `/` だけではディレクトリの中身に当たらない（`plugins/*/changelog.d/`）
    excludes = [f":(exclude,glob){p}**" if p.endswith("/") else f":(exclude,glob){p}" for p in exempt]
    return _git("diff", "--quiet", reviewed_point, sha, "--", ".", *excludes).returncode == 0


def _judge(sha: str, tv: ParsedTranscript) -> tuple[str, str, str]:
    """(verdict, reason, 追加の欄)。"""
    first_counted = int(_git("show", "-s", "--format=%ct", sha).stdout.strip()) + 1
    outcomes = _reviewer_outcomes(tv)
    after = [o for o in outcomes if o[1] >= first_counted]
    ok_after = [o for o in after if o[0] == "ok"]
    if ok_after:
        last = max(ok_after, key=lambda o: o[1])
        return "reviewed", "-", f" | by: {_clean(last[2])}@{_clean(last[3])}"
    done = [o[1] for o in outcomes if o[0] == "ok"]
    if done and _only_exempt_changes_since(int(max(done)), sha):
        return "exempt-only", "-", ""
    if any(o[0] == "running" for o in after):
        return "would-deny", "reviewer-incomplete", ""
    if after:
        return "would-deny", "reviewer-failed", ""
    if done:
        return "would-deny", "changed-after-review", ""
    others = [
        launch.subagent_type for launch in tv.launches
        if launch.name in {"Agent", "Task"} and (_epoch(launch.timestamp) or 0) >= first_counted
    ]
    if others:
        names = ",".join(_clean(n) for n in others[:MAX_LOGGED_AGENTS])
        return "would-deny", "other-agent-only", f" | agents: {names}"
    return "would-deny", "no-reviewer", ""


def _state_dir() -> Path | None:
    configured = os.environ.get("GDD_HOOK_STATE_DIR")
    if configured:
        return Path(configured)
    home = os.environ.get("HOME")
    return Path(home) / ".claude" / ".gdd-hook-state" if home else None


def _log(line: str) -> None:
    state = _state_dir()
    if state is None:
        return
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(state / "push-review.log", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _session_hash() -> str:
    raw = os.environ.get("GDD_PUSH_REVIEW_TRANSCRIPT", "")
    return _hash8(Path(raw).stem) if raw else "-"


def _write_line(
    verdict: str, reason: str, extra: str = "", session: str = "-",
    repo: str = "", branch: str = "", sha: str = "", ms: int = 0,
) -> None:
    at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _log(
        f"{at} | verdict: {verdict} | reason: {reason} | session: {session} | "
        f"repo: {_hash8(repo) if repo else '-'} | branch: {_hash8(branch) if branch else '-'} | "
        f"sha: {_clean(sha[:8])} | ms: {ms}{extra}"
    )


class _Push:
    """1 回の push の文脈（transcript は最初に要るときに 1 回だけ読む）。"""

    def __init__(self, remote: str, url: str) -> None:
        self.repo_root = _git("rev-parse", "--show-toplevel").stdout.strip()
        self.github = _github_repo(remote, url)
        raw = os.environ.get("GDD_PUSH_REVIEW_TRANSCRIPT", "")
        self.transcript = Path(raw) if raw else None
        self.session = _session_hash()
        self._parsed: ParsedTranscript | None = None

    def parsed(self) -> ParsedTranscript:
        if self._parsed is None:
            self._parsed = parse_transcript(self.transcript)
        return self._parsed

    def write(self, verdict: str, reason: str, extra: str = "", branch: str = "", sha: str = "", ms: int = 0) -> None:
        _write_line(verdict, reason, extra, self.session, self.repo_root, branch, sha, ms)

    def check(self, local_sha: str, branch: str) -> None:
        started = time.monotonic()
        verdict, reason, extra = self._verdict(local_sha, branch)
        self.write(verdict, reason, extra, branch, local_sha, int((time.monotonic() - started) * 1000))

    def _verdict(self, local_sha: str, branch: str) -> tuple[str, str, str]:
        if self.github is None:
            return "not-github", "-", ""
        count = _open_pr_count(self.github, branch)
        if count is None:
            return "gh-unknown", "-", ""
        if count == 0:
            return "no-pr", "-", ""
        if self.transcript is None or not self.transcript.is_file():
            return "no-transcript", "-", ""
        try:
            return _judge(local_sha, self.parsed())
        except Exception as exc:  # noqa: BLE001 — log-only: 判定の失敗は記録して push を通す
            return "error", type(exc).__name__, ""


def _refs(data: bytes) -> list[tuple[str, str]]:
    refs = []
    for line in data.decode("utf-8").split("\n"):
        parts = line.split()
        if len(parts) == 4 and not ZERO_SHA.match(parts[1]) and parts[2].startswith("refs/heads/"):
            refs.append((parts[1], parts[2][len("refs/heads/"):]))
    return refs


def _run(argv: list[str]) -> None:
    refs = _refs(sys.stdin.buffer.read())
    if not refs:
        return
    push = _Push(argv[1] if len(argv) > 1 else "", argv[2] if len(argv) > 2 else "")
    for local_sha, branch in refs[:MAX_REFS]:
        try:
            push.check(local_sha, branch)
        except Exception as exc:  # noqa: BLE001 — log-only: 記録して次の ref へ進む
            _write_line(
                "error", type(exc).__name__, session=push.session, repo=push.repo_root, branch=branch, sha=local_sha,
            )
    if len(refs) > MAX_REFS:
        push.write("skipped", "ref-limit", f" | refs: {len(refs) - MAX_REFS}")


def main(argv: list[str]) -> int:
    try:
        _run(argv)
    except Exception as exc:  # noqa: BLE001 — log-only: 判定の外の失敗も 1 行残して push を通す
        try:
            _write_line("error", type(exc).__name__, session=_session_hash())
        except Exception:  # noqa: BLE001 — ログが書けなくても push を通す
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
