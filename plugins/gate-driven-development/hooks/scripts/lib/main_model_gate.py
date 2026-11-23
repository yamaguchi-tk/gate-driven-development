"""main が Sonnet・Haiku のときに、GDD の起動を止め、セッションの開始か相談の段で 1 回知らせる。

2026-10-19〜10-30 の判断ポイントつき HITL で、人が作り直しを求めた率は main が
Sonnet 5.5 で 6/13、Opus 5.5 で 2/56 だった。狭い案は GDD に入る前の main の相談で
作られていた（review-log/20261030-main-model-gate.notes.md）。main は自分のモデルを
替えられないので、警告ではなく止めて、ユーザーに `/model opus` を案内する。

止めるのは GDD の入口で、毎回判定する。状態は持たない:
  - Skill の gdd-dev・gdd-resume（PreToolUse の hook）
  - commands/gdd-dev.md の手動の手順で run を始める書き込み（PreToolUse の hook の Write・Edit・MultiEdit）。
    `.claude/gdd-dev.local.md` がディスクで active でない（無い・読めないを含む）ときの書き込みで、書く内容は見ない。
    run の途中の更新（ディスクの frontmatter が active: true）は止めない。宣言された欄（file_path）とディスクの
    中身だけを読み、Bash の書き込みは判定しない
  - setup-gdd-loop.sh の実行（/gdd-dev・/gdd-resume が最初に走らせる）。script の中から `--setup` で呼ぶ。
    Bash の command の文字列から実行かを推測しないので、どう包んで実行しても判定し、読むだけなら判定しない。
    0 以外で終わると、commands/gdd-dev.md の「走って 0 以外で終われば止まって知らせる」に当たる
直接打った /gdd-dev（UserPromptExpansion）では判定しない。返事の前の transcript の最後の信号は前のターンの
モデルで、画面での切り替えが記録に残らないと前のモデルで誤るため。

モデルは、今の返事の行から取る（PreToolUse の入力にモデルの欄は無い）。transcript は非同期に書かれ、hook の時点で
今の返事がまだ無いことがある（Claude Code の hooks の文書）ので、次の順に探し、無ければ期限まで短く読み直す:
  1. 入力の tool_use_id を持つ main の assistant の行の `message.model`（hook だけ）
  2. 最後の人の発言（ほかに `/model` の出力・model の attachment）より後の、main の assistant の行
  3. どちらも無ければ、transcript の最後の信号（model の attachment、`/model` の出力 `Set model to <名前>`、
     main の assistant の `message.model`。`<synthetic>` は除く）。このときだけ、止める文に切り替えた直後の案内を足す
transcript は末尾の _TAIL_BYTES だけを読み、そこに信号が無いときだけ全体を読む。どの段で決めたかは state dir の
main-model-gate.log に 1 行書く（前提が成り立つ割合を数えるため）。
止めるのは、その名前に sonnet か haiku を含むときだけ。信号が無いとき（Codex・Cursor）は止めない。外し方は
settings.json の env の `GDD_ALLOW_NON_OPUS_MAIN=1` だけ。hook には settings の env が環境変数で届く。setup の中では
agent がコマンドの前に付けた環境変数で外れないよう、プロセスの環境ではなく settings のファイル（user と、cwd から
上の各ディレクトリの .claude/settings.json・settings.local.json）の env を読む。
"""
from __future__ import annotations

import json
import os
import re
import hashlib
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

GATED_SKILLS = ("gdd-dev", "gdd-resume")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit")
STOP_FAMILIES = ("sonnet", "haiku")
OPT_OUT_ENV = "GDD_ALLOW_NON_OPUS_MAIN"
# `/model` の出力だけを受け付ける許可リスト。タグの直後に固定し、要約・貼ったログ・ほかの
# local command の出力の途中にある `Set model to` は読まない（実測: 本物はすべて一致）。
_SET_MODEL = re.compile(r"<local-command-stdout>(?:\x1b\[[0-9;]*m)*Set model to (?:\x1b\[[0-9;]*m|`)*([^\x1b`<\n]+)")

BLOCK_TEXT = (
    "⛔ GDD は main のセッションが Opus のときに使います。今の main は {model} です。"
    "`/model opus` で切り替えてから、もう一度起動してください。"
    "Opus を使えないときは、settings.json の env に GDD_ALLOW_NON_OPUS_MAIN=1 を設定すると外せます。"
)
# 今の返事の行が読めず、前の信号で判定したときだけ足す
HINT_TEXT = "画面でモデルを切り替えた直後なら、一言送ってからやり直してください（今の返事のモデルをまだ読めず、前の返事のモデルで判定しました）。"
# 読み直しの間隔と、走査を含めた全体の期限（hook の timeout 5 秒の内）。末尾から読む量
_RETRY_SECONDS = 0.3
_DEADLINE_SECONDS = 3.0
_TAIL_BYTES = 4 * 1024 * 1024
UNKNOWN_TEXT = "GDD は main のセッションが Opus のときに使います。今の main のモデルを判定できませんでした（このまま進めます）。"
NOTICE_TEXT = (
    "今の main は {model} です。GDD（/gdd-dev）に進む相談は、Opus に切り替えてから（`/model opus`）行ってください。"
    "main が Sonnet のとき、GDD の確認で作り直しになる率が高くなっています（このセッションで 1 回だけ表示します）。"
)


def _signal(record: dict) -> str | None:
    name = _raw_signal(record)
    # 孤立サロゲートなど UTF-8 にできない文字を、ここで一度だけ置き換える（ログ・出力の例外で判定を落とさない）
    return name.encode("utf-8", "replace").decode("utf-8") if name else None


def _raw_signal(record: dict) -> str | None:
    if record.get("isSidechain"):
        return None
    kind = record.get("type")
    if kind == "attachment":
        att = record.get("attachment")
        if isinstance(att, dict) and att.get("type") == "model":
            ident = att.get("identity")
            if isinstance(ident, dict) and isinstance(ident.get("modelId"), str):
                return ident["modelId"]
        return None
    msg = record.get("message")
    if not isinstance(msg, dict):
        return None
    if kind == "assistant":
        model = msg.get("model")
        return model if isinstance(model, str) and model and model != "<synthetic>" else None
    if kind == "user" and isinstance(msg.get("content"), str):
        found = _SET_MODEL.match(msg["content"])
        if found:
            return found.group(1).strip()
    return None


def main_model(transcript_path: object) -> str | None:
    """transcript の最後の信号のモデル名。読めない行は飛ばす。読めなければ None。"""
    if not isinstance(transcript_path, str) or not transcript_path:
        return None
    latest = None
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                # 深い入れ子（RecursionError）などの例外も行ごとに飛ばし、guard 全体を落とさない
                try:
                    record = json.loads(line)
                    signal = _signal(record) if isinstance(record, dict) else None
                except Exception:
                    continue
                latest = signal or latest
    except Exception:
        return None
    return latest


def _is_boundary(record: dict) -> bool:
    """今の turn の始まり: 人の発言・`/model` の出力（user の行で tool_result でないもの）か model の attachment。"""
    if record.get("isSidechain") or record.get("isMeta"):
        return False
    if record.get("type") == "attachment":
        att = record.get("attachment")
        return isinstance(att, dict) and att.get("type") == "model"
    if record.get("type") != "user":
        return False
    msg = record.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str):
        return True
    return isinstance(content, list) and not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def _has_tool_use(record: dict, tool_use_id: str) -> bool:
    content = record.get("message", {}).get("content")
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") == tool_use_id for b in content)


def _scan(transcript_path: str, tool_use_id: object, deadline: float) -> tuple[str | None, str | None] | None:
    """(今の返事のモデル, 段) か、今の返事の行が無ければ (最後の信号, None)。読めなければ None。
    末尾の _TAIL_BYTES だけを読み、そこに信号が 1 つも無いときだけ全体を読む。期限を過ぎたら読んだところまでで返す。"""
    try:
        size = os.path.getsize(transcript_path)
    except OSError:
        return None
    starts = [max(0, size - _TAIL_BYTES)]
    if starts[0]:
        starts.append(0)
    for start in starts:
        by_id = turn = latest = None
        try:
            with open(transcript_path, "rb") as fh:
                fh.seek(start)
                if start:
                    fh.readline()  # 途中から読んだ最初の行は欠けている
                for raw in fh:
                    if time.monotonic() > deadline:
                        break
                    try:
                        record = json.loads(raw.decode("utf-8", "replace"))
                        if not isinstance(record, dict):
                            continue
                        signal = _signal(record)
                        if _is_boundary(record):
                            turn = None
                        elif signal and record.get("type") == "assistant":
                            turn = signal
                            if isinstance(tool_use_id, str) and tool_use_id and _has_tool_use(record, tool_use_id):
                                by_id = signal
                    except Exception:
                        continue
                    latest = signal or latest
        except Exception:
            return None
        if by_id:
            return by_id, "tool_use_id"
        if turn:
            return turn, "current_turn"
        if latest or time.monotonic() > deadline:
            return latest, None
    return None, None


def reply_model(transcript_path: object, tool_use_id: object = None) -> tuple[str | None, str]:
    """今の返事のモデルと、決めた段（tool_use_id / current_turn / fallback / unreadable）。"""
    if not isinstance(transcript_path, str) or not transcript_path:
        return None, "unreadable"
    deadline = time.monotonic() + _DEADLINE_SECONDS
    while True:
        found = _scan(transcript_path, tool_use_id, deadline)
        if found is None:
            return None, "unreadable"
        model, stage = found
        if stage:
            return model, stage
        if time.monotonic() + _RETRY_SECONDS > deadline:
            return model, "fallback"
        time.sleep(_RETRY_SECONDS)


def _state_dir(env: dict) -> Path:
    base = env.get("GDD_HOOK_STATE_DIR")
    return Path(base) if base else Path(env.get("HOME") or Path.home()) / ".claude" / ".gdd-hook-state"


def _log(env: dict, session: object, entry: str, stage: str, model: str | None, decision: str) -> None:
    """判定を 1 行書く。どの例外も判定に届かせない。session はハッシュの先頭 8 桁で書く。"""
    try:
        digest = hashlib.sha1(str(session or "").encode("utf-8", "replace")).hexdigest()[:8]
        line = "\t".join((datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), digest, entry, stage,
                          model or "-", decision))
        path = _state_dir(env) / "main-model-gate.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8", errors="backslashreplace") as fh:
            fh.write(line + "\n")
        os.chmod(path, 0o600)
    except Exception:
        pass


def _session_start_model(payload: dict) -> str | None:
    """SessionStart は payload の model だけで決める。
    env と settings の既定は使わない。Desktop はセッションごとにモデルを選ぶので、既定は実際のモデルと
    食い違う（30 日の通知 555 件のうち、直後の main が Opus だったのが 250 件）。再開の transcript も使わない。
    最後の信号は再開の前のモデルで、画面で別のモデルを選ぶと食い違う。どちらも最初の返事の後の Stop で知らせる。"""
    model = payload.get("model")
    return model if isinstance(model, str) and model else None


def _is_stopped(model: str | None) -> bool:
    return model is not None and any(f in model.lower() for f in STOP_FAMILIES)


def _gated_name(payload: dict) -> str | None:
    tool_input = payload.get("tool_input")
    name = tool_input.get("skill") or tool_input.get("name") if isinstance(tool_input, dict) else None
    if not isinstance(name, str):
        return None
    name = name.strip().lstrip("/").split(":")[-1]
    return name if name in GATED_SKILLS else None


def _entry(payload: dict) -> str | None:
    """判定する入口なら、その名前（ログの入口の列）を返す。"""
    if payload.get("tool_name") in WRITE_TOOLS:
        return "Write" if _starts_run(payload) else None
    return "Skill" if _gated_name(payload) else None


def _starts_run(payload: dict) -> bool:
    """手動の手順で run を始める書き込みか。ディスクのファイルが active でなければ、書く内容を見ずに判定する。
    active かは Stop hook と同じ読み方（state_io.marker_state。frontmatter の active が 1 行で、大文字小文字を
    問わず true）で決め、無い・読めない・判定できないときも判定する。"""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("file_path"), str):
        return False
    path = Path(tool_input["file_path"])
    cwd = payload.get("cwd")
    if not path.is_absolute() and isinstance(cwd, str):
        path = Path(cwd) / path
    try:
        # 字面と、解決した先のどちらかが .claude/gdd-dev.local.md なら判定する（大文字小文字は問わない）
        if not (_is_state_path(path) or _is_state_path(Path(os.path.realpath(path)))):
            return False
    except Exception:  # noqa: BLE001 - 解決できないときは、run を始める書き込みとして判定する
        return True
    scripts = str(Path(__file__).resolve().parents[1])  # hooks/scripts（ほかの hook と同じく lib. から import する）
    sys.path.insert(0, scripts)
    try:
        from lib.state_io import marker_state

        return marker_state(path, "") != 0
    except Exception:  # noqa: BLE001 - 判定できないときは、run を始める書き込みとして判定する
        return True
    finally:
        sys.path.remove(scripts)


def _is_state_path(path: Path) -> bool:
    return path.name.casefold() == "gdd-dev.local.md" and path.parent.name.casefold() == ".claude"


def _settings_opt_out(env: dict) -> bool:
    """setup の外し方。settings のファイルの env だけを読み、プロセスの環境は読まない。"""
    base = env.get("CLAUDE_CONFIG_DIR") or (str(Path(env["HOME"]) / ".claude") if env.get("HOME") else "")
    files = [Path(base) / "settings.json"] if base else []
    cwd = Path.cwd()
    for directory in (cwd, *cwd.parents):
        files += [directory / ".claude" / "settings.json", directory / ".claude" / "settings.local.json"]
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        values = data.get("env") if isinstance(data, dict) else None
        if isinstance(values, dict) and values.get(OPT_OUT_ENV) == "1":
            return True
    return False


def _notice_once(payload: dict, home: Path) -> bool:
    """このセッションで初めてなら印を置いて True。印を置けないときは出さない。"""
    session = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id") or ""))
    if not session:
        return False
    mark = home / ".claude" / ".gdd-hook-state" / "main-model-notice" / session
    try:
        mark.parent.mkdir(parents=True, exist_ok=True)
        mark.touch(exist_ok=False)
    except OSError:
        return False
    return True


def decide(payload: dict, env: dict) -> dict | None:
    if env.get(OPT_OUT_ENV) == "1":
        return None
    event = payload.get("hook_event_name")
    if event in ("SessionStart", "Stop"):
        # 相談の段の通知は返事の後（Stop）に出す。返事の前（UserPromptSubmit）の transcript の最後の信号は
        # 前のターンのモデルで、画面での切り替えが記録に残らないと前のモデルで知らせてしまう
        home = Path(env.get("HOME") or Path.home())
        if event == "SessionStart":
            model = _session_start_model(payload)
        else:
            model = main_model(payload.get("transcript_path"))
        if _is_stopped(model) and _notice_once(payload, home):
            return {"systemMessage": NOTICE_TEXT.format(model=model)}
        return None
    entry = _entry(payload) if event == "PreToolUse" else None
    if entry is None:
        return None
    model, stage = reply_model(payload.get("transcript_path"), payload.get("tool_use_id"))
    decision = "unknown" if model is None else "deny" if _is_stopped(model) else "allow"
    if decision == "deny":
        text = BLOCK_TEXT.format(model=model) + (HINT_TEXT if stage == "fallback" else "")
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": text + " main からは切り替えられないので、この文をユーザーにそのまま伝えて止まってください。",
            },
            "systemMessage": text,
        }
    elif decision == "unknown" and env.get("CLAUDE_CODE_ENTRYPOINT"):
        out = {"systemMessage": UNKNOWN_TEXT}
    else:
        out = None
    _log(env, payload.get("session_id"), entry, stage, model, decision)
    return out


def _session_transcript(env: dict) -> str | None:
    """setup の中で、CLAUDE_CODE_SESSION_ID の transcript（projects/*/<id>.jsonl のうち最後に更新したもの）を探す。"""
    session = env.get("CLAUDE_CODE_SESSION_ID") or ""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", session):
        return None
    base = env.get("CLAUDE_CONFIG_DIR") or (str(Path(env["HOME"]) / ".claude") if env.get("HOME") else "")
    if not base:
        return None
    found = sorted(Path(base).glob(f"projects/*/{session}.jsonl"), key=lambda p: p.stat().st_mtime)
    return str(found[-1]) if found else None


def setup_check(env: dict) -> int:
    """setup-gdd-loop.sh から呼ぶ。止めるなら止める文を stderr に出して 3、それ以外は 0。"""
    if (env.get("HOME") and Path(env["HOME"], ".claude", "gdd-hooks-disabled").is_file()) or _settings_opt_out(env):
        return 0
    model, stage = reply_model(_session_transcript(env))
    decision = "unknown" if model is None else "deny" if _is_stopped(model) else "allow"
    code = 3 if decision == "deny" else 0
    try:
        if decision == "deny":
            text = BLOCK_TEXT.format(model=model) + (HINT_TEXT if stage == "fallback" else "")
            print(text + " main からは切り替えられないので、この文をユーザーにそのまま伝えて止まってください。", file=sys.stderr)
        elif decision == "unknown":
            print(UNKNOWN_TEXT, file=sys.stderr)
    except Exception:
        pass
    _log(env, env.get("CLAUDE_CODE_SESSION_ID"), "setup", stage, model, decision)
    return code


def main() -> int:
    if sys.argv[1:2] == ["--setup"]:
        try:
            return setup_check(dict(os.environ))
        except Exception as exc:  # 判定できないときは止めない（hook と同じ）
            print(f"main-model-gate: 判定できませんでした（{type(exc).__name__}）", file=sys.stderr)
            return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    out = decide(payload, dict(os.environ))
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
