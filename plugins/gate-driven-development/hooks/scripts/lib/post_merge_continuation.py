"""Manual merge continuation lane の永続化と早期停止ブロック。

`gdd_stop_hook.py` から切り出した。切り出しの理由は挙動ではなく健全性で、
hook 本体が 1595 行（上限 1500）に達し、**このファイルに 1 行触るだけで
pre-PR の Codebase Health Gate が `gh pr create` を止める**状態だったため。

lane 名（`Manual merge continuation`）と marker ファイル名は
`tests/checks/hooks.sh` が `gdd_stop_hook.py` の**ソース上に**存在することを
要求する契約リテラルなので、ここでは定義せず呼び出し元から受け取る。
定数をこちらへ移すと契約チェックが落ちる（実測）。
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from lib.constants import PR_URL_RE
from lib.next_plan_check import has_next_plan_block, requirements_lane_pending
from lib.regular_file import read_regular_bytes
from lib.transcript import ParsedTranscript

# マージを済ませた報告だけを合図にする（語の後が文末・空白・句読点・接続の語のときだけ。「マージしたい」
# 「マージしたら」「マージした？」「マージしたPR」は合図にしない）
MANUAL_MERGE_RE = re.compile(
    r'(mergeした|マージした|\bmerged\b)(?=$|[\s。、．，.,!！）)」』]|ので|から|が|よ|けど|です)', re.IGNORECASE
)
POST_MERGE_DONE_RE = re.compile(
    r'(post[- ]merge|post[- ]apply|merge 後|マージ後|apply 後|実環境|実リソース)'
    r'.*(state|tasklist|steering|残タスク|Verification|確認)',
    re.IGNORECASE | re.DOTALL,
)
OTHER_PR_RE = re.compile(r"別の.{0,20}(?:PR|pull.?request|ブランチ|branch)", re.IGNORECASE)


def state_path(project_root: Path, marker_file: str) -> Path:
    return project_root / ".claude" / marker_file


def _next_task_hint(steering_dir: Path | None) -> str | None:
    if not steering_dir:
        return None
    state_file = steering_dir / "state.md"
    if not state_file.exists():
        return None
    task_match = re.search(
        r"^Task:\s*(.+)", state_file.read_text(encoding="utf-8"), re.MULTILINE
    )
    return task_match.group(1).strip() if task_match else None


def write_continuation(
    project_root: Path,
    *,
    marker_file: str,
    session_id: str,
    tasklist_path: str,
    last_output: str,
) -> None:
    """PR 作成後の continuation state を永続化する。

    後から利用者が「mergeした」と言ったときに、正式な GDD state が done に
    達していても hook が post-merge lane を復元できるようにする。
    """
    pr_match = PR_URL_RE.search(last_output or "")
    if not pr_match:
        return
    target = state_path(project_root, marker_file)
    target.parent.mkdir(parents=True, exist_ok=True)

    steering_dir = Path(tasklist_path).parent if tasklist_path else None
    payload = {
        "session_id": session_id,
        "created_at_epoch": int(time.time()),
        "tasklist_path": tasklist_path,
        "pr_url": pr_match.group(0),
        "status": "pending_manual_merge",
        "next_task_hint": _next_task_hint(steering_dir),
        "steering_dir": str(steering_dir) if steering_dir else None,
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _mentions_other_pr(user_msg: str, marker_text: str) -> bool:
    """並行作業ガード: merge 発言が **別の PR** についてのものかを判定する。

    利用者は GDD 対象とは別の PR について「別のPRをマージしたからこれをやって」と
    言うことがある。判定は次の順で行う。marker が読めない / parse できない場合、
    規則 2-3 は丸ごと飛ばして呼び出し元の pending-merge 検査へ落ちる（その検査は
    なお block しうる）。

      1. 「別の…PR/ブランチ」の明示があれば常に別 PR 扱い。**marker のデータに
         依存せず最初に判定する**ので、marker が壊れていてもこの明示信号を
         握り潰せない
      2. GitHub の PR URL があれば、marker の PR と**完全一致**するときだけ
         GDD の PR 扱い（marker に URL が無い場合はこの規則を飛ばす）。番号だけの
         比較にしないのは、別 repo の同番 PR を一致させないため
      3. `#<番号>` があれば marker の PR 番号と一致するときだけ GDD の PR 扱い
      4. PR 参照が無ければ GDD の PR とみなす
    """
    if OTHER_PR_RE.search(user_msg):
        return True
    try:
        data = json.loads(marker_text)
        marker_url = data.get("pr_url", "")
        num_match = re.search(r"/pull/(\d+)", marker_url)
        marker_num = num_match.group(1) if num_match else ""
        found_urls = PR_URL_RE.findall(user_msg)
        if found_urls:
            return bool(marker_url) and marker_url not in found_urls
        found_nums = re.findall(r"#(\d+)\b", user_msg)
        return bool(found_nums and marker_num and marker_num not in found_nums)
    except Exception:
        return False


def _next_plan_block_payload(marker_text: str, last_output: str) -> dict | None:
    """OT-F9 E3: post-merge verification 完了時に未完 stage が残るなら block payload。

    requirements.md が読めなければ未完として扱う（`requirements_lane_pending`）。
    marker の JSON が壊れていて `tasklist_path` を取れないときは検査せず None を返す（fail-open）。
    """
    try:
        data = json.loads(marker_text)
        req_path = Path(data["tasklist_path"]).parent / "requirements.md"
        if requirements_lane_pending(req_path) and not has_next_plan_block(last_output):
            return {
                "decision": "block",
                "reason": (
                    "post-merge verification が完了しましたが、"
                    "`Planned Follow-up Stage Lane` に未完 stage があります。\n\n"
                    "停止出力に `### 次の計画`（次 stage / Registry 状態 / "
                    "「次に進んで」案内）ブロックを追加してください。"
                ),
            }
    except Exception:
        return None
    return None


def pending_block_payload(lane: str) -> dict:
    """merge 後の必須作業が未了のまま停止しようとしたときの block payload。"""
    return {
        "decision": "block",
        "reason": (
            f"{lane} が pending です。"
            " `mergeした` を受けた後は、merge 後 workflow 監視、"
            "post-merge / post-apply verification、state/tasklist re-read、"
            "残タスク確認まで実施してから停止してください。"
        ),
        "systemMessage": (
            f"{lane}: inspect the merged PR and main workflows, "
            "wait for deploy/apply/CI, run read-only post-merge/post-apply verification, "
            "re-read state.md/tasklist.md, respect Approved Direction/autonomy ceiling, "
            "then report remaining work. The merge cue authorizes read-only monitoring "
            "and verification only; do not perform new write operations without explicit approval."
        ),
    }


def _epoch(timestamp: object) -> float | None:
    """transcript の record の timestamp（ISO 8601、時差つき）を epoch 秒にする。読めなければ None。"""
    if not isinstance(timestamp, str):
        return None
    try:
        at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return at.timestamp() if at.tzinfo is not None else None


def _cue_boundary(tv: ParsedTranscript, marker_text: str) -> float | None:
    """これより前の発話を合図に数えない境界（epoch 秒）。決められなければ None（区切らない）。

    marker を作った時刻（hook が書く int の epoch で、0 以上・今より後でないものだけ）を使い、marker の
    PR の URL が assistant の本文にそれより前に出ていれば、その時刻まで下げる（PR を作った後・marker を
    書く前の合図も数える。URL を後から書いた別の session では下げない）。marker の時刻が使えないとき、
    URL の record の時刻が読めないときは区切らない。
    """
    try:
        data = json.loads(marker_text)
    except (ValueError, RecursionError):
        return None
    if not isinstance(data, dict):
        return None
    created = data.get("created_at_epoch")
    if not (type(created) is int and 0 <= created <= time.time() + 60):
        return None
    url = data.get("pr_url")
    if not isinstance(url, str) or url not in tv.pr_url_first_seen:
        return float(created)
    first = _epoch(tv.pr_url_first_seen[url])
    return None if first is None else min(first, float(created))


def resolve_block(
    project_root: Path,
    tv: ParsedTranscript,
    *,
    marker_file: str,
    lane: str,
) -> dict | None:
    """manual merge cue の後、post-merge の確認が済むまでの早期停止を止める。

    block すべきなら payload を返す。止めない場合は None。marker の後始末
    （verification 完了時の unlink）もここで行う。
    """
    marker = state_path(project_root, marker_file)
    try:
        raw = read_regular_bytes(marker)
    except OSError:  # FIFO・ディレクトリなど。中身を読めないので、merge cue なら止める側に倒す
        raw, unreadable = b"", True
    else:
        unreadable = False
    if raw is None:
        return None
    last_output = tv.last_assistant_text or ""
    marker_text = raw.decode("utf-8", errors="replace")
    # 合図は人間の発話（turn の途中に queued で届いたものを含む）から取り、PR を作る前の発話は数えない
    # （時刻が読めなければ数える）。origin を書かない版（origin.kind が human の行が無い transcript）だけ、
    # 今までどおり直近のユーザー入力も読む。どれか 1 つがこの PR の合図なら合図とする
    boundary = _cue_boundary(tv, marker_text)
    candidates = [t for t, at in tv.human_utterances
                  if boundary is None or (said := _epoch(at)) is None or said >= boundary]
    if not tv.human_origin_seen:
        candidates.append(tv.last_user_text or "")
    if not any(MANUAL_MERGE_RE.search(t) and not _mentions_other_pr(t, marker_text) for t in candidates):
        return None
    if unreadable:
        return {
            "decision": "block",
            "reason": (
                f".claude/{marker.name} を通常のファイルとして読めないため、merge 後の確認が済んだかを判定できません。"
                "このファイルを削除してから停止してください。"
            ),
        }
    if POST_MERGE_DONE_RE.search(last_output):
        payload = _next_plan_block_payload(marker_text, last_output)
        if payload is not None:
            return payload
        marker.unlink(missing_ok=True)
        return None
    return pending_block_payload(lane)
