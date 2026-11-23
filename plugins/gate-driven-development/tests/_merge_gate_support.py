"""merge gate hook 契約テスト群が **横断で** 共有するリポジトリ/state.md fixture。

`tests/test_merge_gate_hook.py`（旧・単一ファイル、2355 行）が large_file /
python_function_count の両方で medium 判定されたため、関心事ごとに
`test_merge_gate_hook_*.py` へ分割した。分割後の各ファイルがそれぞれ独自に
git repo 初期化・state.md 書き込み・hook subprocess 起動を持つと、同じ fixture が
複数ファイルへコピーされて片方だけ直すドリフトが再発する。ここへ 1 本化することで
「証跡 fixture の正本はここだけ」という構造を保つ。

`_init_repo_with_commit_date` は当初 1 箇所（独立レビュー severity の回帰テスト）
専用ヘルパーとして書かれたが、分割で block reason 品質系 fixture
（`_merge_gate_block_reason_samples`）からも参照されることが判明したため、
2 ファイル間の重複を避けてここへ移した（分割時の依存関係調査で判明）。

repo の中身（init + user 設定 + 1 commit）は、merge gate 以外のテストと共有する
`_git_fixture.init_repo` に委ねる。ここに残すのは repo の置き場所と名前だけである。
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

from _git_fixture import init_repo
from _paths import PLUGIN_ROOT
from _timing_budget import hang_guard_seconds, hook_timeout_seconds
HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "run-merge-gate-hook.sh"
# merge gate の hooks.json の timeout（秒）。これを超えると PreToolUse は通る。
HOOK_TIMEOUT = hook_timeout_seconds("run-merge-gate-hook.sh")
# hook を起動するテストの壁時計の打ち切り。止まったときの保険だけにする。hook 1 回の CPU 時間は
# HOOK_TIMEOUT より十分短いが、壁時計はほぼプロセス起動の待ちで、並列の全量テストと外部の負荷の下では
# HOOK_TIMEOUT に届く（2026-10-26、load average が高い中で HOOK_TIMEOUT の近くまで延びた）。
HANG_GUARD = hang_guard_seconds("run-merge-gate-hook.sh")
LIB_DIR = PLUGIN_ROOT / "hooks" / "scripts" / "lib"


def _init_bare_repo(parent, name):
    """`git init` だけを済ませた repo（commit なし）を `parent/name` に作る。

    root 候補ループ系のテストは「git repo として解決できるが HEAD が無い」形を
    多用する（`git rev-parse --show-toplevel` は成立し、証跡検査へは進まない）。
    """
    repo = parent / name
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def _init_named_repo(parent, name):
    """`_init_repo` と同じ内容（init + user config + 1 commit）を任意の名前で作る。

    root 候補ループ / AC-18 系のテストは 1 test 内で複数 repo を作り分けるため、
    名前を固定できない。`_init_repo` はこの関数の `name="repo"` 版。
    """
    repo = parent / name
    repo.mkdir()
    init_repo(repo)
    return repo


def _init_repo(tmp_path):
    return _init_named_repo(tmp_path, "repo")


def _head_sha(repo):
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _init_repo_with_commit_date(tmp_path, commit_date_iso):
    """`_init_repo` と同じだが commit の author/committer date を指定できる。

    A-1 pin（`Last Review Push At` の `at` は HEAD committer date 以降でなければ
    ならない）を満たしたまま「40 分前に push した」を模擬するための fixture 専用
    helper。
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo, commit_date=commit_date_iso)
    return repo


# 本 module 唯一の hook 実行 helper。分割後の全ファイルがこれを共有する
# （同名の定義を複数置くと後勝ちで片方が死にコード化するため 1 本に保つ）。
def _run_hook(payload: dict, cwd, home_dir, session_id="test-session", extra_env=None,
              drop_env=(), timeout=HANG_GUARD):
    # `GH_HOST` / `GH_REPO` は repo 決定要因そのもの、`GDD_HOOK_STATE_DIR` は GDD の PR
    # 台帳の場所。実行環境から継承すると、それらを設定している開発者の手元でだけ
    # verdict が変わる（環境依存の失敗）。
    env = {k: v for k, v in os.environ.items()
           if k not in ("GH_HOST", "GH_REPO", "GDD_HOOK_STATE_DIR")}
    env["HOME"] = str(home_dir)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["CLAUDE_CODE_SESSION_ID"] = session_id
    if extra_env:
        env.update(extra_env)
    # `drop_env` は「その変数が **無い** ときの hook 挙動」を固定するための穴。
    # 既定の env 構築は `HOME` を必ず設定するため、`set -u` 由来の即死経路
    # （`${GDD_HOOK_STATE_DIR:-${HOME}/...}` の展開失敗）は fixture から原理的に
    # 踏めない。ここを塞がないと、その経路を守っている subshell ガードを外す
    # mutation が生き残る（実測）。
    for _name in drop_env:
        env.pop(_name, None)
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True, text=True, env=env, cwd=str(cwd), timeout=timeout,
    )


def _write_local_state(repo, pr_url="https://github.com/acme/widgets/pull/7",
                        session_id="test-session", extra_lines=()):
    local_state = repo / ".claude" / "gdd-dev.local.md"
    local_state.parent.mkdir(parents=True, exist_ok=True)
    local_state.write_text(f"active: true\nsession_id: {session_id}\n")
    steering = repo / ".steering" / "20260101-demo"
    steering.mkdir(parents=True, exist_ok=True)
    (steering / "state.md").write_text(
        "## Gate Status\n"
        "- Resume From: done\n- Next Action: done\n"
        f"- PR URL: {pr_url}\n" + "".join(f"{ln}\n" for ln in extra_lines)
    )
    return steering / "state.md"


def _write_marker_only(repo, *, active, session_id="test-session"):
    """`.claude/gdd-dev.local.md` だけを書く（`.steering/` は作らない）。

    `session_id=None` は `session_id:` 行そのものを欠落させる（design.md
    § 降格の入力クラス C-2「所有を確認できない」の欠落形。空文字列 `""` を
    渡すと C-2 の別形——値が空——になる）。`_write_state` /
    `_write_two_done_steerings` 共通の marker 書き込みロジックをここへ集約する。
    """
    local_state = repo / ".claude" / "gdd-dev.local.md"
    local_state.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"active: {'true' if active else 'false'}"]
    if session_id is not None:
        lines.append(f"session_id: {session_id}")
    local_state.write_text("\n".join(lines) + "\n")


def _write_state(repo, *, active, extra_lines=(),
                 pr_url="https://github.com/acme/widgets/pull/7",
                 session_id="test-session"):
    """`active:` マーカーを **明示的に選べる** state fixture。

    既存の `_write_local_state` / `_write_evidence_state` は `active: true` 固定で、
    そのため design 5c の代替条件（PR URL 一致）は 1 度も実行されていなかった
    （gate #11 F-2）。
    """
    _write_marker_only(repo, active=active, session_id=session_id)
    steering = repo / ".steering" / "20260101-demo"
    steering.mkdir(parents=True, exist_ok=True)
    # pr_url=None は `PR URL` 行そのものが state.md に無い形（RF-1 の再現条件）。
    lines = ([f"- PR URL: {pr_url}"] if pr_url else []) + list(extra_lines)
    (steering / "state.md").write_text(
        "## Gate Status\n- Resume From: done\n- Next Action: done\n"
        + "\n".join(lines) + "\n"
    )
    return steering / "state.md"


def _new_marker_only_repo(parent, name):
    """marker（`active: false` / `session_id` 行なし）だけを持つ commit なし repo。

    「GDD セッションではあるが起動根拠（所有 marker / 対象 PR steering）が無い」
    形の最小 fixture。`.steering/` は作らない。
    """
    repo = _init_bare_repo(parent, name)
    _write_marker_only(repo, active=False, session_id=None)
    return repo


def _new_repo_with_marker_and_pr(parent, name, pr=7, *, commit=True):
    """marker + 対象 PR を記録した steering を持つ repo。

    `commit=False` は commit を作らない形（AC-18 の入れ子 repo 再現など、
    証跡検査まで進む必要がない fixture 用）。
    """
    builder = _init_named_repo if commit else _init_bare_repo
    repo = builder(parent, name)
    _write_state(repo, active=False, pr_url=f"https://github.com/acme/{name}/pull/{pr}")
    return repo


def _new_full_evidence_repo(parent, name):
    """全解除条件を満たす証跡一式を持つ repo（統制群 = 単独なら allow）。"""
    repo = _init_named_repo(parent, name)
    _write_state(repo, active=False, extra_lines=_valid_evidence_lines(_head_sha(repo)))
    return repo


def _write_evidence_state(repo, extra_lines, pr_url="https://github.com/acme/widgets/pull/7"):
    local_state = repo / ".claude" / "gdd-dev.local.md"
    local_state.parent.mkdir(parents=True, exist_ok=True)
    local_state.write_text("active: true\nsession_id: test-session\n")
    steering = repo / ".steering" / "20260101-demo"
    steering.mkdir(parents=True, exist_ok=True)
    lines = [f"- PR URL: {pr_url}"] + extra_lines
    (steering / "state.md").write_text(
        "Resume From: done\nNext Action: done\n" + "\n".join(lines) + "\n"
    )


def _write_two_done_steerings(repo, *, active=False, session_id="test-session",
                              slugs=("20260101-demo", "20260102-followup"),
                              unrecorded=()):
    """done 済み steering を 2 件置く（gate #14 M-4 の再現条件）。

    `gdd_pre_push_resolve_steering` は候補 2 件以上で `multiple` を返す。
    `post-completion-pr-flow` が follow-up steering を起こす運用を勧めているため、
    この状態は製品内の導線から普通に生じる。

    `unrecorded` に slug を渡すと、その steering から `PR URL` 行そのものを落とす
    （gate の指摘の再現条件）。旧 fixture は **常に両方へ URL を書いていた**ため、
    `multiple` × `PR URL` 未記録の組み合わせが既存のテストのどこにも無く、
    「判定材料の欠落」が素通りへ潰れる回帰を CI が検出できなかった。
    """
    _write_marker_only(repo, active=active, session_id=session_id)
    for index, slug in enumerate(slugs, start=1):
        steering = repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        body = "## Gate Status\n- Resume From: done\n- Next Action: done\n"
        if slug not in unrecorded:
            body += f"- PR URL: https://github.com/acme/widgets/pull/{index}\n"
        (steering / "state.md").write_text(body)
    return slugs


def _approval_line(pr, sha, minutes_ago=0, evidence="ユーザーが「マージして」と指示"):
    at = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    return f"- Merge Approval: PR #{pr} / head {sha} | evidence: {evidence} | approved_at: {at}"


def _valid_evidence_lines(head, pr=7):
    """全解除条件を満たす証跡一式（allow になる統制群）。"""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        _approval_line(pr, head),
        f"- Pre-Merge Review Recheck: {head} | new_blocking: 0 | at: {now_iso}",
        f"- Last Review Push At: {head} | at: {now_iso}",
        f"- Bot Review Received: {head} | received: yes | at: {now_iso}",
    ]
