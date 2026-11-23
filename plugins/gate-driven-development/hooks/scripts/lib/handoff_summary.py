"""assistant 出力の Handoff Summary を active steering の state.md へ永続化する。

`gdd_stop_hook.py` から切り出した。理由は挙動ではなく健全性で、hook 本体が
行数上限と複雑度上限の両方を超え、**1 行触るだけで pre-PR の Codebase Health
Gate が `gh pr create` を止める**状態だったため。挙動は変えていない。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from lib.tasklist_parse import NON_NEWLINE_LINE_BREAKS

MAX_SUMMARY_LINES = 10
STATE_MARKER = "Last Handoff Summary="
# 置換は行区切り文字の手前で止める。`.` は U+2028 など 8 文字にも一致し、同じ物理行の後ろ
# （route 行など）まで上書きして、Check 3 の行区切り文字の検査を無効にしていた（独立-3 D3）
_STATE_MARKER_LINE = re.compile(
    r'Last Handoff Summary=[^\n' + re.escape("".join(sorted(NON_NEWLINE_LINE_BREAKS))) + r']*'
)
INSERT_ANCHORS = ("Route In Progress=", "Approved Direction=")


def truncate_summary(summary: str) -> str:
    """契約（Handoff Summary は 10 行以内）に合わせて切り詰める。

    切り詰めた事実は本文にも stderr にも残す（黙って落とすと、利用者は
    次のセッションで欠けていることに気付けない）。
    """
    all_lines = summary.splitlines()
    original_count = len(all_lines)
    lines = all_lines[:MAX_SUMMARY_LINES]
    if original_count > MAX_SUMMARY_LINES:
        lines.append(f"[truncated: original {original_count} lines]")
        print(
            f"⚠ Handoff Summary truncated: {original_count} lines → "
            f"{MAX_SUMMARY_LINES} lines. Consider shortening the summary.",
            file=sys.stderr,
        )
    return "\n".join(lines)


def _is_terminal_tasklist(tasklist: Path) -> bool:
    """tasklist.md の最初の `Next Action=` 行が terminal 値かどうか。

    最初の 1 行だけを見て break するのは元実装のまま。ここは挙動不変の
    切り出しなので、読み取り規約は変更していない。
    """
    if not tasklist.is_file():
        return False
    for line in tasklist.read_text(encoding="utf-8").splitlines():
        if "Next Action=" in line:
            return line.split("Next Action=", 1)[1].strip() in ("done", "cancelled")
    return False


def find_active_state_files(cwd: Path) -> list[Path]:
    """git worktree を横断して、terminal でない steering の state.md を集める。"""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=True, cwd=str(cwd),
        )
    except Exception:
        return []

    state_files: list[Path] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line.startswith("worktree "):
            continue
        steering = Path(raw_line[9:]) / ".steering"
        if not steering.is_dir():
            continue
        for d in sorted(steering.iterdir(), reverse=True):
            state_file = d / "state.md"
            if not state_file.is_file():
                continue
            if _is_terminal_tasklist(d / "tasklist.md"):
                continue  # 古い steering を続けて見る
            state_files.append(state_file)
            break
    return state_files


def apply_summary(content: str, encoded: str) -> str:
    """state.md 本文へ `Last Handoff Summary=` を書き込んだ結果を返す。"""
    if STATE_MARKER in content:
        # 置換は関数で渡す。文字列だと要約中の `\n` `\f` `\1` を置換テンプレートとして展開し、
        # state.md に本物の行や行区切り文字を書いていた（独立-2 B4）
        return _STATE_MARKER_LINE.sub(lambda _m: f'{STATE_MARKER}{encoded}', content, count=1)
    for anchor in INSERT_ANCHORS:
        if anchor in content:
            eol = content.index("\n", content.index(anchor))
            return content[:eol + 1] + f"{STATE_MARKER}{encoded}\n" + content[eol + 1:]
    # anchor が無い場合の退避先: Gate Status 節の最初の空行の直前
    if "## Gate Status" in content:
        gs_idx = content.index("## Gate Status")
        blank = content[gs_idx:].find("\n\n")
        if blank >= 0:
            insert_pos = gs_idx + blank
            return content[:insert_pos] + f"\n{STATE_MARKER}{encoded}" + content[insert_pos:]
    return content


def persist(text: str, cwd: Path, pattern: re.Pattern[str]) -> None:
    """assistant 出力から最新の Handoff Summary を取り出して state.md に残す。"""
    match = pattern.search(text)
    if not match:
        return
    summary = match.group(1).strip()
    if not summary:
        return
    summary = truncate_summary(summary)

    state_files = find_active_state_files(cwd)
    if len(state_files) != 1:
        if state_files:
            print(
                f"⚠ persist_handoff_summary: 複数の active steering を検出 "
                f"({len(state_files)} 件) — 更新をスキップします: "
                + ", ".join(str(p) for p in state_files[:3]),
                file=sys.stderr,
            )
        # 0 件は active steering なし = 正常な早期終了（ログ不要）
        return

    state_path = state_files[0]
    content = state_path.read_text(encoding="utf-8")
    # 1 行エンコード: frontmatter 安全な形にするため改行を " | " で連結する
    state_path.write_text(apply_summary(content, summary.replace("\n", " | ")), encoding="utf-8")
