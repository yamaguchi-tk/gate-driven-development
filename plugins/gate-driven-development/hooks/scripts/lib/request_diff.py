"""human check の提示が依頼から外れていないかを読み手に照らさせ、差があれば種類ごとに 1 行で人に見せる。

その前に、判断ポイントの `依頼との差:` の欄とマーカー直前のタグを、承認の書き込みの検査と同じ判定
（`lib/request_diff_field.py` の `field_problem`）で見る。人の発言の後で最後のマーカー付きの発言（承認の書き込みの検査が
読むのと同じ選び方）の欄が読めないか、タグが無い・読めないか、なし以外の点があるなら、読み手を起動せず block して、main に
確認の全文を出し直させる（ユーザーが OK した後に承認の書き込みで止まり、同じ判断を答え直させるのを防ぐ）。なし以外のときは、
推奨を依頼より狭くせず、狭める案を採用しない案として並べさせる（ユーザーが名指しで選べば、その返事で決まる）。数えは、この hook 自身の記録
（`request-diff.log` の、同じ session・人の発言のターンの block の行）で決め、block は数えの行を書けたときだけ出す
（main の書き方や transcript の自由文に左右されず、書けないのに block して止まらない輪にもならない）。記録を読めない・
書けないときは止めずに知らせる。`MAX_FIELD_BLOCKS` 回までは出し直させ、その後は、最後の発言の
形によらず止めずに知らせだけを出す（止まらない輪にしない）。知らせは、そのまま答えてよいこと・狭める点は名指しで答えることと、
hook が見た行を人に見せる（人の返事の後は、main が補正を書いて承認を記録する。`lib/request_diff_approval.py`）。`GDD_SKIP_REQUEST_DIFF` は読み手だけを切り、この検査は
切らない。例外・読めない transcript では止めない（承認の書き込みの検査が後ろに残る）。

差の表示は提示を止めず、main に書き直させない（systemMessage だけ）。読み手は `claude -p` で
1 回だけ起動し、ツールも hook も使えない。受け取るのはユーザーの発言と提示の本文だけで、main の
途中の分析や相談役の報告は渡さない。読み手の文は測ったときの文のまま変えない。

- ユーザーの発言は `request_capture` の許可リストで transcript から選ぶ。範囲はこの session の全部
- 同じ session の同じ提示は 1 回だけ見る（記録の sha で見分ける）
- 人に見せるのは種類（変わる・満たせない）ごとの先頭の 1 行だけで、最大 2 行。残りは件数を添え、全件は記録に残す
- 動かなかったときは見せず、理由を記録に残す
- 結果は worktree が消えても読めるよう、hook の state dir の `request-diff.log` に残す。判断ポイントの
  `依頼との差:` の値と欄の問題（`lib/request_diff_field.py`）も残し、読み手の判定と突き合わせて数える
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.hitl_lint_gate import HITL_MARKER  # noqa: E402
from lib.request_capture import _assistant_text, _human_entry, _redact  # noqa: E402
from lib.request_diff_field import field_problem, field_values, unreadable_lines  # noqa: E402

CHECKER_TIMEOUT_SECONDS = 45
SKIP_ENV_VAR = "GDD_SKIP_REQUEST_DIFF"
MAX_USER_CHARS = 40000
MAX_QUOTE_CHARS = 120

MAX_FIELD_BLOCKS = 3
DIFFERS = "なし以外の点がある"
FIELD_BLOCKED = "依頼との差の欄の問題で出し直させた"
FIELD_BLOCK_MESSAGE = (
    "人に出した human check の確認で、判断ポイントの `依頼との差:` の欄かタグに問題があります（{problem}）。"
    "このままユーザーが OK すると、承認を記録できず、OK を言い直させることになります。"
    "人に確認を出すなら、前置きの説明を書かずに確認の全文だけを出し直し、同じ `{marker}` と "
    "`## 👤 次にすること` で止まり直してください。欄は判断ポイントごとに 1 行の `- 依頼との差: なし` です。"
    "マーカーの直前の行には `<gdd-hitl-fields ... request-diff=\"none,none\">` のように、判断ポイントの順に "
    "`none` か `differs` を並べたタグを置きます。"
    "欄に `なし` と項目を並べて書きません。確認のほかの文には、この欄の名前を書きません。"
    "確認の追記や質問への回答だけなら、マーカーを付けずに書きます。"
)
FIELD_DIFFERS_MESSAGE = (
    "人に出した human check の確認で、推奨が依頼より狭い判断ポイントがあります（{problem}）。"
    "このままユーザーが OK すると、承認を記録できず、同じ判断を答え直させることになります。"
    "推奨と無回答時のデフォルトを依頼より狭くせず、依頼を狭める案は `採用しない案:` に、変わる AC を書いて並べてください"
    "（ユーザーが名指しで選べば、その返事で決まります）。依頼のままでは届かないなら、前提を変える案か、前提の問いを推奨にします。"
    "ユーザーが自分で狭めると決めた点は、その発言を `根拠` の行に引き、欄は `なし`、タグは `none` にします。"
    "直したら、前置きの説明を書かずに確認の全文だけを出し直し、同じ `{marker}` と `## 👤 次にすること` で止まり直してください。"
)
FIELD_NOTICE = (
    "上の確認は、依頼との差の欄かタグに問題があります（{problem}）。そのまま答えてかまいません。"
    "依頼より狭い点を受け入れるなら、その点を名指しで答えてください。返事の後に、欄とタグだけを直して承認を記録します。"
)

KINDS = ("変わる", "満たせない")  # 見せる順
ALTS = ("あり", "なし")

CHECKER_PROMPT = """あなたは確認役です。添付の 1 件だけを読んでください。ファイル以外は読まないでください。

ファイルの前半は、停止の時点までにユーザーが書いた発言の全部です（依頼の原文と、途中でユーザーが決めたこと）。後半は、アシスタントが人に出した確認（推奨つき）です。アシスタントの分析の正しさは判断しません。見るのは、推奨どおりに進めたときに、ユーザーの言葉がどうなるかだけです。

ユーザーが求めた目的・対象・範囲・合格の条件を挙げ、推奨どおりに進めたときに次に当たるものを探してください。
- 変わる: 推奨が、ユーザーが求めたものの一部を外す・後回しにする・弱める、またはユーザーが前に決めたことを覆す
- 満たせない: 推奨どおりに進めても、ユーザーが求めた目的や条件に届かない（推奨が別の問題を解いている、目的の一部にしか効かない場合を含む）
- アシスタントが開示していても、ユーザーがその形に同意した発言が無ければ当たる
- ユーザーが後からその形に決めた発言があるものは当たらない。細部の選び方だけを問う確認や、依頼どおりの推奨は当たらない。迷うときは当たらないとする

「alt」は、提示の中に、それを満たす別の案があるかです。

出力は次の JSON 1 行だけにしてください。
{"flag":true|false,"items":[{"kind":"変わる|満たせない","user":"<ユーザーの発言を原文のまま 80 字以内>","rec":"<該当する推奨の文を原文のまま 80 字以内>","alt":"あり|なし"}]}
"""


@dataclass
class Verdict:
    flag: bool = False
    items: list[dict] = field(default_factory=list)
    not_run: str = ""
    cost_usd: float | None = None


def _records(transcript_path: str) -> list[dict]:
    records = []
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and not record.get("isSidechain"):
                records.append(record)
    return records


def _presentation_and_words(records: list[dict]) -> tuple[str, list[str]]:
    presentation = ""
    words: list[str] = []
    for record in records:
        if record.get("type") == "assistant":
            text = _assistant_text(record)
            if text:
                presentation = text
            continue
        entry = _human_entry(record)
        if entry and entry[1].strip():
            words.append(entry[1].strip())
    return presentation, words


def _turn_presentation(records: list[dict]) -> tuple[str | None, int]:
    """(最後の人の発言の後で、最後のマーカー付きの assistant の発言, その人の発言までの人の発言の数)。"""
    found: str | None = None
    turn = 0
    for record in records:
        if record.get("type") == "assistant":
            text = _assistant_text(record)
            if HITL_MARKER in text:
                found = text
            continue
        if _human_entry(record):
            turn += 1
            found = None
    return found, turn


def _packet(words: list[str], presentation: str) -> str:
    said = "\n\n".join(words)
    if len(said) > MAX_USER_CHARS:
        head = MAX_USER_CHARS // 3
        said = said[:head] + "\n\n（途中を省略）\n\n" + said[-(MAX_USER_CHARS - head):]
    return (
        f"{CHECKER_PROMPT}\n--- 添付 ---\n"
        f"# 依頼の原文とユーザーの決定（停止までのユーザー発言）\n\n{said}\n\n"
        f"# 停止の提示（main が出した推奨）\n\n{presentation}\n"
    )


def _parse(stdout: str) -> Verdict:
    outer = json.loads(stdout)
    if not isinstance(outer, dict) or outer.get("is_error"):
        return Verdict(not_run="読み手がエラーを返した")
    cost = outer.get("total_cost_usd")
    found = re.search(r"\{.*\}", str(outer.get("result", "")), re.S)
    if not found:
        return Verdict(not_run="読み手の判定を読めない")
    inner = json.loads(found.group(0))
    items = inner.get("items") if isinstance(inner, dict) else None
    if not isinstance(inner, dict) or not isinstance(inner.get("flag"), bool) or not isinstance(items, list):
        return Verdict(not_run="読み手の判定を読めない")
    if not inner["flag"]:
        return Verdict(cost_usd=cost)
    usable = [
        i for i in items
        if isinstance(i, dict) and isinstance(i.get("user"), str) and isinstance(i.get("rec"), str)
        and i.get("kind") in KINDS and i.get("alt") in ALTS
    ]
    if not usable:
        return Verdict(not_run="読み手の判定を読めない")
    return Verdict(flag=True, items=usable, cost_usd=cost)


def ask_checker(packet: str) -> Verdict:
    claude = shutil.which("claude")
    if not claude:
        return Verdict(not_run="claude コマンドが無い")
    env = {
        **os.environ,
        SKIP_ENV_VAR: "1",
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
        "CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1",
    }
    command = [
        claude, "-p", "--model", "opus", "--effort", "medium", "--tools", "",
        "--system-prompt", "記録を読んで指定の JSON を返す確認役です。",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--disable-slash-commands",
        "--settings", '{"disableAllHooks":true}', "--permission-mode", "dontAsk",
        "--no-session-persistence", "--output-format", "json",
    ]
    try:
        with tempfile.TemporaryDirectory(prefix="gdd-request-diff-") as cwd:
            result = subprocess.run(
                command, input=packet, capture_output=True, text=True, cwd=cwd, env=env,
                timeout=CHECKER_TIMEOUT_SECONDS, check=False,
            )
    except subprocess.TimeoutExpired:
        return Verdict(not_run="時間切れ")
    except OSError:
        return Verdict(not_run="読み手を起動できない")
    if result.returncode != 0:
        return Verdict(not_run="読み手が失敗した")
    try:
        return _parse(result.stdout)
    except ValueError:
        return Verdict(not_run="読み手の判定を読めない")


def _one_line(text: str) -> str:
    return " ".join(text.split())[:MAX_QUOTE_CHARS]


def render(item: dict, others: int) -> str:
    tail = f"（ほか {others} 件）" if others else ""
    user = _one_line(item["user"])
    if item["kind"] == "変わる":
        return f"依頼との差（変わる）: {user} → {_one_line(item['rec'])}{tail}"
    return f"依頼との差（満たせない）: {user}（別の案: {item['alt']}）{tail}"


def _log_path() -> Path:
    base = os.environ.get("GDD_HOOK_STATE_DIR") or str(Path.home() / ".claude" / ".gdd-hook-state")
    return Path(base) / "request-diff.log"


def _already_seen(path: Path, session_id: str, sha: str) -> bool:
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if (isinstance(record, dict) and record.get("session_id") == session_id and record.get("sha") == sha
                and not record.get("blocked")):
            return True
    return False


def _blocks_in_turn(path: Path, session: str, turn: int) -> int:
    """このターンでこの hook が欄の問題で block した回数（記録の行の数）。読めなければ OSError。"""
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if (isinstance(record, dict) and record.get("session_id") == session and record.get("turn") == turn
                and record.get("blocked")):
            count += 1
    return count


def _field_extras(checked: str, problem: str) -> dict:
    """記録の付け足しの欄。組み立てか書き出しで例外が出たら、付け足さない（数えの行は残す）。"""
    try:
        extras = {
            "sha": hashlib.sha256(checked.encode("utf-8", "surrogatepass")).hexdigest(),
            "fields": [_redact(value) for value in field_values(checked)],
            "field_problem": problem,
        }
        json.dumps(extras, ensure_ascii=False).encode("utf-8")
        return extras
    except Exception:  # noqa: BLE001
        return {}


def _seen_lines(checked: str) -> str:
    """知らせに添える、hook が見た行（読めない行と、`なし` 以外の値）。"""
    lines = unreadable_lines(checked) + [value for value in field_values(checked) if value != "なし"]
    return ("\nhook が見た行:\n" + "\n".join(f"- {_one_line(line)}" for line in lines)) if lines else ""


def _field_check(records: list[dict], payload: dict) -> dict | None:
    """承認の書き込みで止まる確認なら、出す payload（block か知らせ）。問題が無ければ None。

    数えはこの hook 自身の記録で決め、block は数えの行を書けたときだけ出す（書けないのに block すると、数えが進まず
    止まらない輪になる）。書けないとき・上限を使い切った後は、止めずに人へ知らせる。"""
    checked, turn = _turn_presentation(records)
    problem = field_problem(checked) if checked is not None else None
    if not problem:
        return None
    notice = {"systemMessage": FIELD_NOTICE.format(problem=problem) + _seen_lines(checked)}
    session = str(payload.get("session_id") or payload.get("transcript_path") or "")
    try:
        path = _log_path()
        blocks = _blocks_in_turn(path, session, turn)
    except Exception:  # noqa: BLE001
        return notice
    if blocks >= MAX_FIELD_BLOCKS:
        return notice
    if problem == DIFFERS:
        output = {"decision": "block", "reason": FIELD_DIFFERS_MESSAGE.format(problem=problem, marker=HITL_MARKER)}
    else:
        lines = unreadable_lines(checked)
        tail = ("\n読めなかった行:\n" + "\n".join(f"- {_one_line(line)}" for line in lines)) if lines else ""
        output = {"decision": "block", "reason": FIELD_BLOCK_MESSAGE.format(problem=problem, marker=HITL_MARKER) + tail}
    try:
        _append(path, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session,
            "cwd": str(payload.get("cwd", "")),
            "turn": turn,
            "blocked": True,
            "flag": False,
            "not_run": FIELD_BLOCKED,
            "cost_usd": None,
            "items": [],
            **_field_extras(checked, problem),
        })
    except Exception:  # noqa: BLE001
        return notice
    return output


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NONBLOCK", 0), 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def run(payload: dict) -> dict | None:
    """hook の出力（block か systemMessage）を返す。出すものが無ければ None。"""
    transcript = payload.get("transcript_path")
    if not transcript:
        return None
    try:
        records = _records(str(transcript))
    except OSError:
        return None
    field_output = _field_check(records, payload)
    if field_output:
        return field_output
    path = _log_path()
    presentation, words = _presentation_and_words(records)
    if os.environ.get(SKIP_ENV_VAR) or HITL_MARKER not in presentation:
        return None
    session_id = str(payload.get("session_id", ""))
    sha = hashlib.sha256(presentation.encode("utf-8")).hexdigest()
    if _already_seen(path, session_id, sha):
        return None
    verdict = ask_checker(_packet(words, presentation)) if words else Verdict(not_run="ユーザーの発言が記録に無い")
    _append(path, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "cwd": str(payload.get("cwd", "")),
        "sha": sha,
        "flag": verdict.flag,
        "not_run": verdict.not_run,
        "cost_usd": verdict.cost_usd,
        "fields": [_redact(value) for value in field_values(presentation)],
        "field_problem": field_problem(presentation),
        "items": [{"kind": i["kind"], "user": _redact(i["user"]), "rec": _redact(i["rec"]), "alt": i["alt"]} for i in verdict.items],
    })
    if not verdict.flag:
        return None
    lines = []
    for kind in KINDS:
        same = [i for i in verdict.items if i["kind"] == kind]
        if same:
            lines.append(render(same[0], len(same) - 1))
    return {"systemMessage": "\n".join(lines)}


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        output = run(payload)
    except Exception as exc:  # noqa: BLE001 - 人の停止を妨げない（承認の書き込みの検査が後ろに残る）
        print(f"request-diff: {type(exc).__name__}", file=sys.stderr)
        return 0
    if output:
        print(json.dumps(output))  # ASCII で出す（引いた行に対にならない surrogate があっても書き出しで落ちない）
    return 0


if __name__ == "__main__":
    sys.exit(main())
