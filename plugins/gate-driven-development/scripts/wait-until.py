#!/usr/bin/env python3
"""処理待ち（CI・レビュー bot のレビュー・デプロイなど）を、上限つきで待つ。

Bash の run_in_background: true で起動し、完了の通知を待つ（main は待ちの間 idle になり、hook は発火しない。
止めどころはこのスクリプトの上限だけである）。条件は次のどちらか 1 つで渡す。

  python3 <plugin>/scripts/wait-until.py --timeout 3600 --pr-checks <PR 番号> [-R <owner/repo>]
  python3 <plugin>/scripts/wait-until.py --timeout 1800 [--interval 60] -- bash -c '<条件コマンド>'

<plugin> は plugin の絶対パス（skill の base directory の 2 つ上）。Bash では ${CLAUDE_PLUGIN_ROOT} が未定義なので使わない。

条件コマンドを interval 秒ごとに実行し、終了コードで分ける。
  0          成立。終わる（exit 0）
  1          まだ。観測行を出して待つ
  それ以外   条件が壊れている（シグナル・起動できない・1 回の実行が --check-timeout を超えた、を含む）。
             待たずに終わる（exit 2）
全体の期限（--timeout 秒）を過ぎたら exit 124。引数を読めないときは、条件を実行せずに exit 2。

--pr-checks は条件を書かせずに PR の CI を待つ（`gh pr view --json state,headRefOid,statusCheckRollup`）。
読めるかの判定と check ごとの分類は、Stop hook のマージ待ちの押し返しと同じ hooks/scripts/lib/ci_state.py を
使う。ただし check が混在するときは pending を優先する（押し返しは failure を優先する）。pending の check が
1 つも無くなれば（success でも failure でも）成立とし、結果を最終行の last_stdout（state=<PR の状態>
ci=<状態> any_failure=<yes|no> head=<sha の先頭 12 桁>）で返す。any_failure は、pending が残っていても
failure の check が出ていれば yes。PR が OPEN でなくなったら（MERGED・CLOSED）、CI を問わず成立とする。
gh が失敗した・JSON を読めない・checks が登録されないまま 600 秒たった、は壊れている扱い。
CI を待つときは `gh pr checks` を条件にしない（pending の終了コード 8 は「壊れている」に当たる）。

出力（stdout。background では task の output file に残る）:
  wait-until: check=<n> elapsed=<秒> exit=<終了コード|none> stdout=<最後の行>    1 回の確認ごと
  wait-until: stderr=<最後の行>                                                 壊れているときだけ
  wait-until: result=<met|timeout|broken> elapsed=<秒> checks=<n> last_exit=<終了コード|none> last_stdout=<最後の行>
条件を確かめ始めた後は、最終行がいつもこの形なので、成立と打ち切りを出力の自由文から読み分けなくてよい
（1 回の確認の中の予期しない例外も、例外の名前を stderr= に出して broken で終わる）。最終行が出ないのは、
引数の誤り（usage を stderr に出して exit 2）、--help（exit 0）、シグナルで止められたとき（exit 128 +
シグナルの番号）、stdout に書けないときである。

注意:
- 条件は状態を読むだけのコマンドにする。`gh pr merge`・`git push`・コメントなどの書き込みを入れない
  （1 を返すたびに「まだ」として繰り返され、PreToolUse の gate は起動時の 1 回しか見ない）
- 1 は「まだ」なので、`until gh ... | grep -q X` の形では gh・grep のエラー（終了コード 1）も「まだ」になり、
  期限まで待つ。CI は --pr-checks で待ち、汎用の形では、エラーで 2 以上を返すように条件を書く
- `set -o pipefail` と `grep -q` を併せると、成立しても前段が SIGPIPE で 141 になり「壊れている」に当たる
- 1 回の実行の後も stdout を開いたまま残る子（`cmd &`）がいると、--check-timeout まで待って壊れている扱いになる。
  そのとき止めるのは条件のプロセスグループだけで、別のグループに移った子（set -m の job など）は残る
- --timeout の上限は 7200 秒。それより長く待つときは、124 の後に原因を確かめてから起動し直す
- 全体の所要は最大で --timeout + --check-timeout + 10 秒（止めた確認の出力を読み切る待ちと、終わりを待つ待ち。
  止められないプロセスはそのまま残す）。124 で終わったら、同じ待ちをそのまま起動し直さず、
  最終行の観測値から、待つ対象が来ない理由（条件のずれ・相手の遅れ）を先に確かめる
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# CI の分類は Stop hook と共有する。top-level module として読む（`from lib.X` にすると scripts/lib と衝突する。
# scripts/lint-approved-direction.py と同じ）。
_LIB_DIR = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from ci_state import ci_state, ci_states  # noqa: E402
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)

MAX_TIMEOUT_SECONDS = 7200
MIN_INTERVAL_SECONDS = 10  # gh API を叩きすぎない
DEFAULT_INTERVAL_SECONDS = 30
DEFAULT_CHECK_TIMEOUT_SECONDS = 60
MAX_CHECK_TIMEOUT_SECONDS = 600
NO_CHECKS_GRACE_SECONDS = 600  # PR の checks の登録を待つ猶予。references/post-merge-qa.md 手順 3 の 10 分にそろえた
EXIT_MET, EXIT_BROKEN, EXIT_TIMEOUT = 0, 2, 124
_LINE_LIMIT = 200
_DRAIN_SECONDS = 5  # 1 回の確認を止めた後、出力を読み切るのを待つ秒数と、その後に終わりを待つ秒数

_running: subprocess.Popen | None = None


def _bounded_int(low: int, high: int):
    def parse(value: str) -> int:
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"整数ではない: {value!r}") from None
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"{low} 以上 {high} 以下にする: {number}")
        return number
    return parse


def _parse(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(prog="wait-until.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--timeout", required=True, type=_bounded_int(1, MAX_TIMEOUT_SECONDS), help="全体の期限（秒）")
    parser.add_argument("--interval", type=_bounded_int(MIN_INTERVAL_SECONDS, MAX_TIMEOUT_SECONDS),
                        default=DEFAULT_INTERVAL_SECONDS, help="確認の間隔（秒）")
    parser.add_argument("--check-timeout", type=_bounded_int(1, MAX_CHECK_TIMEOUT_SECONDS),
                        default=DEFAULT_CHECK_TIMEOUT_SECONDS, help="1 回の確認の上限（秒）")
    parser.add_argument("--pr-checks", type=_bounded_int(1, 10**9), metavar="PR", help="この PR の CI を待つ")
    parser.add_argument("-R", "--repo", help="--pr-checks の repo（owner/name）")
    command: list[str] = []
    if "--" in argv:
        index = argv.index("--")
        argv, command = argv[:index], argv[index + 1:]
    args = parser.parse_args(argv)
    if (args.pr_checks is None) == (not command):
        parser.error("条件は --pr-checks か `-- <条件コマンド>` のどちらか 1 つで渡す")
    if args.repo is not None and args.pr_checks is None:
        parser.error("-R は --pr-checks と一緒に使う")
    return args, command


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _last_line(text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return ""
    return "".join(ch if ch.isprintable() else "?" for ch in lines[-1])[:_LINE_LIMIT]


def _run(argv: list[str], check_timeout: int) -> tuple[int | None, str, str]:
    """(終了コード, stdout, stderr)。起動できない・時間を超えたときの終了コードは None。"""
    global _running
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, errors="replace", start_new_session=True)
    except OSError as exc:
        return None, "", f"起動できない: {exc}"
    _running = proc
    try:
        out, err = proc.communicate(timeout=check_timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        try:
            out, err = proc.communicate(timeout=_DRAIN_SECONDS)
        except subprocess.TimeoutExpired:
            # 別のプロセスグループに移った子（set -m の job、GNU timeout など）が pipe を持ったまま残っている。
            # その子は止めずに pipe を手放す
            for pipe in (proc.stdout, proc.stderr):
                pipe.close()
            try:
                proc.wait(timeout=_DRAIN_SECONDS)
            except subprocess.TimeoutExpired:
                pass  # 止められない（EPERM・D state など）。残して上限を守る
            out, err = "", ""
        return None, out, f"1 回の確認が {check_timeout} 秒を超えた"
    finally:
        _running = None
    return proc.returncode, out, err


def _check_command(command: list[str], check_timeout: int) -> tuple[str, int | None, str, str]:
    """(met | wait | broken, 終了コード, stdout の最後の行, stderr の最後の行)。"""
    code, out, err = _run(command, check_timeout)
    verdict = {0: "met", 1: "wait"}.get(code, "broken") if code is not None else "broken"
    return verdict, code, _last_line(out), _last_line(err)


def _check_pr(pr: int, repo: str | None, check_timeout: int, elapsed: float) -> tuple[str, int | None, str, str]:
    argv = ["gh", "pr", "view", str(pr), "--json", "state,headRefOid,statusCheckRollup"]
    code, out, err = _run(argv + (["-R", repo] if repo else []), check_timeout)
    if code != 0:
        return "broken", code, _last_line(out), _last_line(err) or "gh pr view が失敗した"
    try:
        view = json.loads(out)
    except ValueError:
        return "broken", code, _last_line(out), "gh pr view の出力を JSON として読めない"
    if not isinstance(view, dict):
        return "broken", code, _last_line(out), "gh pr view の出力が object ではない"
    pr_state, rollup = view.get("state"), view.get("statusCheckRollup")
    states = ci_states(rollup)
    if not isinstance(pr_state, str) or not pr_state or states is None:
        return "broken", code, _last_line(out), "state か statusCheckRollup を読めない"
    # failure が 1 つあっても、pending が残る間は CI が終わっていないので待つ
    state = "pending" if "pending" in states else ci_state(rollup)
    any_failure = "yes" if "failure" in states else "no"
    observed = (f"state={_last_line(pr_state)} ci={state} any_failure={any_failure} "
                f"head={_last_line(str(view.get('headRefOid') or ''))[:12]}")
    if pr_state != "OPEN" or state in {"success", "failure"}:
        return "met", code, observed, ""
    if state == "no-checks" and elapsed >= NO_CHECKS_GRACE_SECONDS:
        return "broken", code, observed, f"checks が登録されないまま {NO_CHECKS_GRACE_SECONDS} 秒たった"
    return "wait", code, observed, ""


def main(argv: list[str]) -> int:
    args, command = _parse(argv)
    start = time.monotonic()
    checks = 0
    while True:
        checks += 1
        try:
            if args.pr_checks is not None:
                verdict, code, line, err = _check_pr(args.pr_checks, args.repo, args.check_timeout,
                                                     time.monotonic() - start)
            else:
                verdict, code, line, err = _check_command(command, args.check_timeout)
        except Exception as exc:  # 予期しない例外も最終行で終える
            verdict, code, line, err = "broken", None, "", f"{type(exc).__name__}: {_last_line(str(exc))}"[:_LINE_LIMIT]
        elapsed = int(time.monotonic() - start)
        exit_text = "none" if code is None else str(code)
        print(f"wait-until: check={checks} elapsed={elapsed} exit={exit_text} stdout={line}", flush=True)
        remaining = args.timeout - (time.monotonic() - start)
        if verdict == "met":
            result, status = "met", EXIT_MET
        elif verdict == "broken":
            print(f"wait-until: stderr={err}", flush=True)
            result, status = "broken", EXIT_BROKEN
        elif remaining <= 0:
            result, status = "timeout", EXIT_TIMEOUT
        else:
            time.sleep(min(args.interval, remaining))
            continue
        print(f"wait-until: result={result} elapsed={elapsed} checks={checks} last_exit={exit_text} last_stdout={line}",
              flush=True)
        return status


def _stop(signum: int, _frame: object) -> None:
    # TaskStop などで止められたら、動いている確認のプロセスグループも止める
    if _running is not None:
        _kill_group(_running)
    sys.exit(128 + signum)


if __name__ == "__main__":
    for _signal in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(_signal, _stop)
    sys.exit(main(sys.argv[1:]))
