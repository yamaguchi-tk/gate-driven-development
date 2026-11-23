#!/usr/bin/env python3
"""reviewer を過去に実際に出た欠陥に当て、見逃しを測る（正本: docs/reviewer-recall-eval.md）。

使い方:
  python3 scripts/run-reviewer-recall-eval.py --out <dir> [--runs 2] [--jobs 3] [--max-cost-usd 150]
  python3 scripts/run-reviewer-recall-eval.py --check          # ケースを git で確かめるだけ（claude を呼ばない）
  python3 scripts/run-reviewer-recall-eval.py --out <dir> --dry-run   # 材料を書くだけ

ケース（evals/reviewer-recall-cases.json）ごとに、tip の木を review-log/ を除いて <out>/<case>/wt に展開し、
base..tip の差分と review-input の 1 枚を書く。reviewer（既定 gdd-implementation-reviewer）を headless の
claude で Read・Grep・Glob だけで回し、出力を写し役（sonnet）が 1 指摘 1 行に写す。その行から
review-findings.md と同じ形（references/finding-dispositions.md の IG 節の表）を書き、
hooks/scripts/lib/finding_dispositions.py で読み戻して採点する。

採点は expected の 1 件ごとに、まだ使っていない指摘で path が paths のどれか（末尾の path 要素で一致）に当たるものを探す。
high か実害クラスの指摘なら hit、それ以外の指摘なら weak、無ければ miss（1 つの指摘は 1 件にだけ当てる）。
費用は、実行の前に「使った額 + 走っている数と次の 1 本の上限（--max-run-usd）」が --max-cost-usd を超えるなら
その実行を始めずに budget として記録し、exit 3 で終わる。終わった実行は <case>/run-<n>.result.json に残し、
次の起動はそれを使い直す（budget の実行だけが回り直す）。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.finding_dispositions import BLOCKING_CATEGORIES, location_path, parse  # noqa: E402

DEFAULT_CASES = PLUGIN_ROOT / "evals" / "reviewer-recall-cases.json"
DEFAULT_AGENT = "gate-driven-development:gdd-implementation-reviewer"
EXCLUDE = ":(exclude)review-log"
# headless の --agent では omitClaudeMd が効かないので env で外す。advisor も切る（memory の実測。手順は正本の文書）
REVIEW_ENV = {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1"}
TRANSCRIBE_PROMPT = """次の文章は、コードレビューの出力である。指摘（finding）ごとに 1 行、次の形の行だけを出力する。
見出し行・区切り行・説明・コードブロックは書かない。指摘が 1 件も無ければ何も出力しない。

| <通し番号> | <severity: high・medium・low のどれか。出力の値を写す> | <category: 出力の値を写す。無ければ -> | <file:line: 出力が欠陥の場所として挙げたファイルを 1 つ、path:行 の形で。行が無ければ path:1> |

---
"""


def git(repo: Path, *args: str, binary: bool = False):
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True, text=not binary)
    return proc.stdout


def load_cases(path: Path, only: set[str] | None) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    return [c for c in cases if not only or c["id"] in only]


def check_cases(repo: Path, cases: list[dict]) -> list[str]:
    """ケースの sha・path・fix_commit を git で確かめ、誤りの一覧を返す。"""
    errors = []
    seen = set()
    for case in cases:
        cid = case["id"]
        if cid in seen or case.get("kind") not in ("found", "missed") or not case.get("expected"):
            errors.append(f"{cid}: id の重複か、kind が found・missed でないか、expected が空")
        seen.add(cid)
        for sha in (case["base"], case["tip"]):
            if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True).returncode:
                errors.append(f"{cid}: commit が無い: {sha}")
        for exp in case["expected"]:
            for p in exp["paths"]:
                if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{case['tip']}:{p}"], capture_output=True).returncode:
                    errors.append(f"{cid} {exp['id']}: tip に path が無い: {p}")
            if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", case["tip"], exp["fix_commit"]],
                              capture_output=True).returncode:
                errors.append(f"{cid} {exp['id']}: fix_commit が tip の後に無い: {exp['fix_commit']}")
    return errors


def prepare(repo: Path, case: dict, case_dir: Path) -> None:
    """tip の木（review-log/ を除く）・差分・review-input の 1 枚・prompt を書く。あれば作り直さない。"""
    wt = case_dir / "wt"
    if not wt.exists():
        data = git(repo, "archive", "--format=tar", case["tip"], "--", ".", EXCLUDE, binary=True)
        tmp = case_dir / "wt.partial"
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(tmp, filter="data")
        tmp.rename(wt)
    diff = case_dir / "diff.txt"
    diff.write_text(git(repo, "diff", f"{case['base']}..{case['tip']}", "--", ".", EXCLUDE), encoding="utf-8")
    sheet = case_dir / "sheet.md"
    sheet.write_text(
        f"- Worktree: {wt}\n\n## 変更点\n\n"
        f"対象の差分: {case['base']}...{case['tip']}（この評価では git を使えない。差分の本文は {diff} を Read する。"
        "review-log/ を除いた差分）\n\n## AC 表\n\nなし（過去の PR を再現した評価で、steering が無い）\n\n"
        "## blocking の条件\n\nblocking の finding には failure scenario（具体的な入力・状態 → 誤った結果）を付ける。"
        f"接地条件は {PLUGIN_ROOT}/references/reviewer-common.md § 常時 High と § finding category（実害クラス）。\n\n"
        "機械検査: 対象外\n", encoding="utf-8")
    (case_dir / "prompt.txt").write_text(f"レビュー入力: {sheet}\n\n## Worktree\n{wt}\n", encoding="utf-8")


def call_claude(argv: list[str], stdin: str, cwd: Path, env: dict, timeout: int) -> dict:
    """claude -p を 1 回呼び、出力の JSON を返す（失敗は is_error にする）。"""
    try:
        proc = subprocess.run(argv, input=stdin, capture_output=True, text=True, cwd=cwd,
                              env={**os.environ, **env}, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"is_error": True, "result": "timeout", "total_cost_usd": 0.0}
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": (proc.stdout + proc.stderr)[-2000:], "total_cost_usd": 0.0}
    if proc.returncode:
        out["is_error"] = True
    return out


def findings_table(case: dict, run: int, transcribed: str) -> str:
    """写し役の 4 欄の行から、review-findings.md の IG 節を書く（行き先は impl-gating Step 9 の向き）。"""
    rows = []
    for line in transcribed.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cells) != 4:
            continue
        severity, category, location = cells[1].lower(), cells[2], cells[3].replace("|", "/")
        dest = "blocking" if severity == "high" or category in BLOCKING_CATEGORIES else "advisory"
        rows.append(f"| IG1-{len(rows) + 1} | {severity} | {category} | {location} | {dest} | - | - |")
    head = f"## IG1 | task: {case['id']} | sha: {case['tip']} | round: {run} | findings: {len(rows)}"
    return "\n".join([head, "", "| id | severity | category | file:line | 行き先 | 検証 | 根拠 |",
                      "|---|---|---|---|---|---|---|", *rows]) + "\n"


def path_matches(found: str | None, expected: list[str]) -> bool:
    if not found:
        return False
    # plugin 配下からの相対・basename・wt の絶対パスのどれで書かれても、path 要素の境目で一致すれば当てる
    found = found.removeprefix("./")
    return any(p == found or p.endswith("/" + found) or found.endswith("/" + p) for p in expected)


def score(case: dict, table: str) -> dict:
    sections, _ = parse(table)
    rows = sections[0].rows if sections else []
    used: set[int] = set()
    matches = {}
    for exp in case["expected"]:
        matches[exp["id"]] = "miss"
        for want, serious in (("hit", True), ("weak", False)):
            for i, row in enumerate(rows):
                is_serious = row.severity == "high" or row.category in BLOCKING_CATEGORIES
                if i not in used and is_serious == serious and path_matches(location_path(row.location), exp["paths"]):
                    used.add(i)
                    matches[exp["id"]] = want
                    break
            if matches[exp["id"]] != "miss":
                break
    return matches


class Budget:
    def __init__(self, cap: float, per_run: float, spent: float) -> None:
        self.cap, self.per_run, self.spent, self.running = cap, per_run, spent, 0
        self.lock = threading.Lock()

    def start(self) -> bool:
        with self.lock:
            if self.spent + (self.running + 1) * self.per_run > self.cap:
                return False
            self.running += 1
            return True

    def finish(self, cost: float) -> None:
        with self.lock:
            self.running -= 1
            self.spent += cost


def run_one(args, case: dict, run: int, budget: Budget) -> dict:
    """1 本を回し、budget でなければ結果を run-<n>.result.json に残す（途中で落ちても終わった分は使い直せる）。"""
    res = _run_one(args, case, run, budget)
    if res["status"] != "budget":
        (args.out / case["id"] / f"run-{run}.result.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return res


def _run_one(args, case: dict, run: int, budget: Budget) -> dict:
    case_dir = args.out / case["id"]
    base = {"case": case["id"], "kind": case["kind"], "run": run}
    if not budget.start():
        return {**base, "status": "budget", "cost_usd": 0.0, "duration_s": 0, "findings": 0, "matches": {}}
    cost = 0.0
    started = time.time()
    try:
        wt = case_dir / "wt"
        review = call_claude(
            [args.claude_bin, "-p", "--plugin-dir", str(PLUGIN_ROOT), "--agent", args.agent, "--tools", "Read,Grep,Glob",
             "--add-dir", str(case_dir), "--add-dir", str(PLUGIN_ROOT), "--settings", '{"disableAllHooks":true}',
             "--permission-mode", "dontAsk", "--max-budget-usd", str(args.max_run_usd), "--output-format", "json"],
            (case_dir / "prompt.txt").read_text(encoding="utf-8"), wt, REVIEW_ENV, args.timeout_min * 60)
        cost += float(review.get("total_cost_usd") or 0)
        (case_dir / f"run-{run}.json").write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
        if review.get("is_error"):
            return {**base, "status": "error", "cost_usd": round(cost, 4), "duration_s": round(time.time() - started),
                    "findings": 0, "matches": {}}
        trans = call_claude(
            [args.claude_bin, "-p", "--model", "sonnet", "--tools", "", "--settings", '{"disableAllHooks":true}',
             "--max-budget-usd", "1", "--output-format", "json"],
            TRANSCRIBE_PROMPT + review.get("result", ""), case_dir, REVIEW_ENV, 600)
        cost += float(trans.get("total_cost_usd") or 0)
        if trans.get("is_error"):
            return {**base, "status": "error", "cost_usd": round(cost, 4), "duration_s": round(time.time() - started),
                    "findings": 0, "matches": {}}
        table = findings_table(case, run, trans.get("result", ""))
        (case_dir / f"run-{run}.findings.md").write_text(table, encoding="utf-8")
        sections, _ = parse(table)
        return {**base, "status": "ok", "cost_usd": round(cost, 4), "duration_s": round(time.time() - started),
                "findings": sections[0].count if sections else 0, "matches": score(case, table)}
    finally:
        budget.finish(cost)


def summary(cases: list[dict], results: list[dict]) -> str:
    by = {(r["case"], r["run"]): r for r in results}
    runs = sorted({r["run"] for r in results})
    lines = ["| case | kind | expected | " + " | ".join(f"run {n}（hit/weak/miss）" for n in runs) + " | 費用 $ | 時間 分 |",
             "|---|---|---|" + "---|" * len(runs) + "---|---|"]
    for case in cases:
        cells, cost, dur = [], 0.0, 0
        for n in runs:
            r = by.get((case["id"], n))
            cost += r["cost_usd"] if r else 0
            dur += r["duration_s"] if r else 0
            if not r or r["status"] != "ok":
                cells.append(r["status"] if r else "-")
                continue
            vals = list(r["matches"].values())
            cells.append(f"{vals.count('hit')}/{vals.count('weak')}/{vals.count('miss')}")
        lines.append(f"| {case['id']} | {case['kind']} | {len(case['expected'])} | " + " | ".join(cells)
                     + f" | {cost:.2f} | {dur / 60:.1f} |")
    lines += ["", "| kind | expected の件数 | 全 run で hit | 一部の run で hit | hit なし |", "|---|---|---|---|---|"]
    for kind in ("found", "missed"):
        tally = [0, 0, 0, 0]
        for case in (c for c in cases if c["kind"] == kind):
            for exp in case["expected"]:
                got = [by[(case["id"], n)]["matches"].get(exp["id"]) for n in runs
                       if by.get((case["id"], n), {}).get("status") == "ok"]
                tally[0] += 1
                tally[1 if got and all(g == "hit" for g in got) else 2 if "hit" in got else 3] += 1
        lines.append(f"| {kind} | " + " | ".join(map(str, tally)) + " |")
    total = sum(r["cost_usd"] for r in results)
    lines += ["", f"費用の合計: ${total:.2f}。実行: " + ", ".join(
        f"{s} {sum(r['status'] == s for r in results)}" for s in ("ok", "error", "budget"))]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--repo", type=Path, default=PLUGIN_ROOT.parents[1])
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--max-cost-usd", type=float, default=150.0)
    ap.add_argument("--max-run-usd", type=float, default=5.0)
    ap.add_argument("--timeout-min", type=int, default=30)
    ap.add_argument("--only", help="回すケースの id（, 区切り）")
    ap.add_argument("--agent", default=DEFAULT_AGENT)
    ap.add_argument("--claude-bin", default="claude")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cases = load_cases(args.cases, set(args.only.split(",")) if args.only else None)
    errors = check_cases(args.repo, cases)
    if errors or args.check:
        print("\n".join(errors), file=sys.stderr)
        return 2 if errors else 0
    if not args.out:
        ap.error("--out が要る")
    args.out = args.out.resolve()
    for case in cases:
        (args.out / case["id"]).mkdir(parents=True, exist_ok=True)
        prepare(args.repo, case, args.out / case["id"])
    if args.dry_run:
        return 0
    done, todo = {}, []
    for case in cases:
        for run in range(1, args.runs + 1):
            path = args.out / case["id"] / f"run-{run}.result.json"
            if path.exists():
                done[(case["id"], run)] = json.loads(path.read_text(encoding="utf-8"))
            else:
                todo.append((case, run))
    budget = Budget(args.max_cost_usd, args.max_run_usd, sum(r["cost_usd"] for r in done.values()))
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for res in pool.map(lambda cr: run_one(args, cr[0], cr[1], budget), todo):
            done[(res["case"], res["run"])] = res
    results = [done[(c["id"], n)] for c in cases for n in range(1, args.runs + 1)]
    (args.out / "results.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results),
                                            encoding="utf-8")
    (args.out / "summary.md").write_text(summary(cases, results), encoding="utf-8")
    return 3 if any(r["status"] == "budget" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
