#!/usr/bin/env python3
"""GDD Telemetry Collector — `.steering/` 配下の artifact から定量指標を抽出する。

`gdd-metrics` skill が AI dispatch で行っている集計を、AI 呼び出しなしの
deterministic な script として提供する。CI / cron / 朝会レポート等の自動化に使える。

## 抽出する指標

- タスク数（done / in-progress / cancelled）
- タスクサイズ分布（trivial / quick (express) / quick (standard) / standard）
- gate 通過率（requirements / design / human-check）
- Fix Attempts 統計（impl_fix_only の差し戻し回数）
- Route In Progress 履歴の集計（route 別の発生回数）
- debug bounce 件数と未パース Route Decision 節数（受理面の正本は
  `references/phase-progression.md` § Bounce 計測の受理面）
- Reviewer Lineage Patterns 蓄積件数
- learned-patterns.md のエントリ数
- Workflow Incident Review 件数
- Guardrail / lint / fixture 検出件数（prompt 品質改善の proxy）

## 入力

`--root` で指定したディレクトリ配下の `.steering/<task>/` を全て対象にする。
default は repo root を auto-detect する（`git rev-parse --show-toplevel`）。
複数 worktree がある場合は `--include-worktrees` で `git worktree list` の全 worktree
を対象にする。
ディレクトリが無い worktree（`git worktree prune` の前の行）は、stderr に警告を出して飛ばす。
`--root` で明示した場所が無いときは終了 1 にする。

## 出力

- `--format=text`（既定）: 人間向けの table 形式
- `--format=json`: machine-readable な構造化出力（dashboard 連携用）
- `--format=csv`: 1 task = 1 row の表形式（spreadsheet 集計用）

## Exit code

- 0: 正常完了
- 1: 入力 path 不正
- 2: usage error

## 推定コストフィールド（model usage proxy）

各 task の Phase 到達数 × Fixed Model を掛け合わせて、概算 token / cost を出す
（実際の token 消費は LLM 呼び出し側でないと取れないため proxy 値）。
正確な計測には外部 logging（OpenAI usage API / Anthropic invocation log）が必要。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

# `hooks/scripts/lib` を **top-level module として** 読む。`hooks/scripts` を
# sys.path に載せて `from lib.X import` すると `sys.modules["lib"]` が hooks 側に
# 固定され、同一プロセスの `scripts/lib`（`lint_base` 等）が解決できなくなる
# （実測: 双方向に ModuleNotFoundError）。読んだ直後に path を戻すのは、この
# ディレクトリを常設して他 module の解決順を変えないため。
_LIB_DIR = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from tasklist_parse import (  # noqa: E402
        classify_task_line,
        select_route_in_progress,
        strip_fenced_blocks,
    )
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)


@dataclass
class TaskMetrics:
    steering_id: str
    worktree: str
    task_size: str = "unknown"
    entry_intent: str = "unknown"
    requirements_status: str = "unknown"
    design_status: str = "unknown"
    human_check_status: str = "unknown"
    resume_from: str = "unknown"
    next_action: str = "unknown"
    route_in_progress: str = "unknown"
    fix_attempts: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    error_log_entries: int = 0
    learned_patterns_entries: int = 0
    reviewer_lineage_smi_added: int = 0
    reviewer_lineage_impact_added: int = 0
    workflow_incident_entries: int = 0
    guardrail_detection_entries: int = 0
    bounce_count: int = 0
    unparsed_route_sections: int = 0
    incident_types: str = ""
    state_is_terminal: bool = False
    state_kind: str = "unknown"  # done / cancelled / in-progress / blocked


def find_steering_dirs(roots: list[Path]) -> list[tuple[Path, str]]:
    """Scan roots for `.steering/<task>/` directories. Returns [(steering_dir, worktree_label)]"""
    results: list[tuple[Path, str]] = []
    for root in roots:
        steering_root = root / ".steering"
        if not steering_root.is_dir():
            continue
        for entry in sorted(steering_root.iterdir()):
            if not entry.is_dir():
                continue
            # Skip non-task dirs (learned-patterns.md is a file, not a dir)
            if entry.name.startswith("."):
                continue
            # Legacy/root-bleed copies without state.md are not canonical tasks.
            if not (entry / "state.md").is_file():
                continue
            results.append((entry, str(root)))
    return results


def read_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def normalize_field_value(value: str | None) -> str | None:
    """Normalize markdown field values before aggregation.

    Gate status fields often carry schema metadata such as
    `approved | evidence: ...`; telemetry should count the status value, not
    the audit suffix. 値がバッククォート囲みで書かれることもあるため、
    集計リテラル（`approved` / `done` 等）と比較する前に落とす。
    """
    if value is None:
        return None
    normalized = value.split("|", 1)[0].strip().rstrip(".").strip("`").strip()
    return normalized or None


def extract_field(text: str, key: str) -> str | None:
    """Extract `Key: value` lines from markdown（値の無い canonical 行はスキップ
    し、次の値付き行を見る。正本: tests/test_state_field_value_less_line_contract.py）。
    """
    text = strip_fenced_blocks(text)
    # canonical field 行は行頭 + bullet marker 1 個まで。インデント行（入れ子
    # bullet の履歴メモ / コードブロック内の記入例）は field として数えない
    # (tests/test_canonical_field_line_anchoring_contract.py が正本)。
    pattern = re.compile(
        rf"^(?:-[ \t]+)?{re.escape(key)}[ \t]*[:：][ \t]*(.+?)[ \t]*$", re.MULTILINE
    )
    for m in pattern.finditer(text):
        if m.group(1).strip().strip("`").strip():
            return normalize_field_value(m.group(1))
    return None


def count_task_headings(section_body: str) -> int:
    """Count task headings in one `## Pending / Completed Tasks` section body.

    受理面は `lib/tasklist_parse.classify_task_line` に集約する。過去の
    silent failure は「正規表現が間違っていた」ではなく「読み手ごとに見出しの
    定義が食い違っていた」ことなので、ここで正規表現を書き直すと欠陥が再び開く
    （旧実装の `^###\\s+Task:` は `### Task N:` を取りこぼす一方、名前が空の
    `### Task:` を 1 と数えていた ＝ 両方向にずれていた）。

    共有関数に**追加で 2 つ**の限定を掛ける:

    - **行頭ぴったり**であること（`design.md` § 論点 2c-2）。インデント行は散文の
      例示か indented code block で tasklist の構造ではない。`gdd_stop_hook.py` の
      done guard / 進捗表示と同じ規約。見るのは **先頭の空白だけ** ―― `strip()` で
      比較すると末尾に空白があるだけの task 行まで捨てる（hook 側で実測した退行）
    - **`###` 見出し形**であること。`- T-N |` 等の list-item を telemetry が数えない
      現行仕様を維持する。`gdd_stop_hook.py` の進捗表示は数えるので受理面は完全
      同値ではない（同値化するかは planning 判断で、この変更では広げない）
    """
    count = 0
    for line in section_body.splitlines():
        if line.lstrip() != line:
            continue
        stripped = line.strip()
        if stripped.startswith("###") and classify_task_line(stripped) == "task":
            count += 1
    return count


#: 見出し行そのもの（section の切れ目）。`#####` 以降は `\s` が `#` に当たらず不一致。
_HEADING_RE = re.compile(r"^#{2,4}\s")

#: route section の anchor。正本は `references/phase-progression.md`
#: § Bounce 計測の受理面。正本は 4 形を列挙するが、`= route `
#: は `route ` の**真部分集合**（`=` + 空白 + `route` + 空白 を含む行は必ず
#: `route` + 空白 を含む）なので、受理面を変えずに 3 形へ畳んである。
#: 畳んだ形と 4 形の同値は corpus 実測でも 0 差（本 task の worklog に記録）。
#: 見出し level の範囲は `_HEADING_RE` だけが持つ。ここは heading と判定済みの行にしか
#: 当てないので、`^#{2,4}\s.*` を重ねると同じ述語が 2 箇所に分かれるだけで判別力が増えない
#: （実測: 片側から落とす変異は 2 つとも SURVIVED、両側から落として初めて KILLED）。
_ROUTE_SECTION_ANCHOR_RE = re.compile(r"(Route Decision|route\s|route`)")

#: F1 = 正本書式。section 内のトップレベル `- ` 行で `route: ` を含むもの。
_F1_TOKEN = "route: "

#: F2 = legacy alias（読むだけ）。太字マーカー `*` と空白を落として `route 判定` 始まり。
_F2_PREFIX = "route 判定"


def parse_route_decisions(worklog_text: str) -> tuple[int, int]:
    """Return `(bounce_count, unparsed_route_sections)` for one `worklog.md`.

    受理面の正本は `references/phase-progression.md` § Bounce 計測の受理面。
    ここは**その正本の実装**であって定義ではない（件数の期待値も持たない —
    fixture 別の期待値はテスト側 1 箇所が正本）。

    **anchor は広く、計上は狭く**:

    - anchor: 見出し行が `Route Decision` / `route ` / `` route` `` を含む section
    - 計上: section 内の**トップレベル `- ` 行**のみ。F1（`route: ` を含む）と
      F2（`*` と空白を落として `route 判定` 始まり）の 2 形だけ。インデントされた
      `  - ` sub-bullet は計上しない
    - anchor に一致したのに F1/F2 が 0 件だった section は `unparsed_route_sections`
      に計上する（silent 0 を作らない = AC-10）。`## Batch Route Decisions` /
      見出しだけが route 値を持つ形 / `- **選んだ route**:` 形がここに落ちる

    **所在（AC-10）**: 本関数は 1 worklog の集計だけを返す。所在は呼び出し側の
    `TaskMetrics` 行（`steering_id` / `worktree`）が持ち、json / csv の per-task 行と
    text の task 別出力で辿れる。行番号は telemetry の出力粒度に無いので持たせない。
    """
    bounce_count = 0
    unparsed = 0
    in_section = False
    section_had_hit = False
    for line in worklog_text.splitlines():
        if _HEADING_RE.match(line):
            if in_section and not section_had_hit:
                unparsed += 1
            in_section = bool(_ROUTE_SECTION_ANCHOR_RE.search(line))
            section_had_hit = False
            continue
        if not in_section or not line.startswith("- "):
            continue
        de_bolded = line[2:].lstrip("* \t")
        if _F1_TOKEN in line or de_bolded.startswith(_F2_PREFIX):
            bounce_count += 1
            section_had_hit = True
    if in_section and not section_had_hit:
        unparsed += 1
    return bounce_count, unparsed


def _section_body(text: str, heading: str) -> str:
    """`## <heading>` 節の本文を返す（無ければ空文字）。次の `## ` 見出しか EOF まで。"""
    match = re.search(rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    return match.group(1) if match else ""


def _count_section_tasks(tasklist_text: str, heading: str) -> int:
    """`## Completed Tasks` / `## Pending Tasks` 節の task 見出し数。

    `なし` を含む節は 0。受理面は `count_task_headings`（= `classify_task_line`）が正本。
    """
    body = _section_body(tasklist_text, heading)
    if not body or "なし" in body:
        return 0
    return count_task_headings(body)


def _count_error_log_entries(worklog_text: str) -> int:
    """`## Error Log` 節の markdown table 行数（header 1 行を差し引く）。"""
    body = _section_body(worklog_text, "Error Log")
    if not body:
        return 0
    rows = [r for r in body.splitlines() if r.strip().startswith("|") and not r.strip().startswith("|---")]
    return max(0, len(rows) - 1)


#: terminal 判定。`Next Action` を優先し、無ければ `Resume From` を見る既存順序を保つ。
_TERMINAL_KINDS = ("done", "cancelled", "blocked")


def _terminal_state(next_action: str, resume_from: str) -> tuple[bool, str]:
    """`(state_is_terminal, state_kind)` を返す。"""
    if next_action in _TERMINAL_KINDS:
        return True, next_action
    if resume_from in _TERMINAL_KINDS:
        return True, resume_from
    return False, "in-progress"


def _first_group(pattern: str, text: str, flags: int = 0) -> str | None:
    """最初の一致の group(1) を trim して返す。**一致が無ければ `None`**。

    「一致なし」と「一致したが正規化後に空」を呼び出し側が区別できるよう、
    空文字ではなく `None` を返す。`or` で既定値へ落とすと `Task Size: .` の
    ように正規化後が空になる入力で既定値が残り、telemetry の集計バケットが
    変わる（旧実装は空文字を代入していた）。
    """
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def parse_task_metrics(steering_dir: Path, worktree_label: str) -> TaskMetrics:
    state_text = read_text_safe(steering_dir / "state.md")
    tasklist_text = read_text_safe(steering_dir / "tasklist.md")
    requirements_text = read_text_safe(steering_dir / "requirements.md")
    worklog_text = read_text_safe(steering_dir / "worklog.md")
    ac_ledger_text = read_text_safe(steering_dir / "ac-ledger.md")
    # 置き場は worktree 直下の docs/（正本: references/cross-task-learning.md）
    learned_patterns_text = read_text_safe(steering_dir.parent.parent / "docs" / "learned-patterns.md")

    m = TaskMetrics(steering_id=steering_dir.name, worktree=worktree_label)

    # state.md fields
    m.requirements_status = extract_field(state_text, "Requirements Review Status") or "unknown"
    m.design_status = extract_field(state_text, "Design Review Status") or "unknown"
    m.human_check_status = extract_field(state_text, "Human Check Status") or "unknown"
    m.resume_from = extract_field(state_text, "Resume From") or "unknown"
    # **hook と同じ受理面で読む**（completion-check 6 回目の M6-1）。従来は
    # `extract_field` の返り値をそのまま集計キーにしていたため、`none（注記）` /
    # `**none**` / `None` が **1 件ごとに別バケット**になり route 別集計が成立しなかった
    # （実データで hook 判定との不一致があった）。受理面の共有は本 PR の主題そのもの。
    _rip = select_route_in_progress(state_text)
    m.route_in_progress = "none" if (not _rip or _rip.lower() == "none") else _rip

    # Entry Intent — could be in state.md (new format) or undetectable
    # 一致した場合だけ代入する（`or` で畳むと「一致したが正規化後に空」を
    # 既定値で上書きしてしまい、集計バケットが変わる）。
    _intent = _first_group(r"##\s+Entry Intent.*?\n\s*-?\s*判定\s*[:：]\s*(\w+)", state_text, re.DOTALL)
    if _intent is not None:
        m.entry_intent = _intent

    # requirements.md — Task Size
    _size = _first_group(r"Task Size\s*[:：]\s*([^\n]+)", requirements_text)
    if _size is not None:
        m.task_size = _size.rstrip(".")

    # tasklist.md — Next Action, Fix Attempts, completed / pending counts
    m.next_action = extract_field(tasklist_text, "Next Action") or m.resume_from

    # Fix Attempts: format is "Fix Attempts: 2/3"
    _fix_attempts = _first_group(r"Fix Attempts\s*[:：]\s*(\d+)\s*/\s*\d+", tasklist_text)
    if _fix_attempts is not None:
        m.fix_attempts = int(_fix_attempts)

    # Count completed and pending tasks
    m.completed_tasks = _count_section_tasks(tasklist_text, "Completed Tasks")
    m.pending_tasks = _count_section_tasks(tasklist_text, "Pending Tasks")

    # worklog.md — Error Log entries
    m.error_log_entries = _count_error_log_entries(worklog_text)

    # worklog.md — Route Decision bounce 計上（AC-8 / AC-9）と未パース節（AC-10）
    m.bounce_count, m.unparsed_route_sections = parse_route_decisions(worklog_text)

    # learned-patterns.md — total bullets count
    if learned_patterns_text:
        m.learned_patterns_entries = len(re.findall(r"^\s*-\s+\S", learned_patterns_text, re.MULTILINE))

    # Reviewer Lineage added_by markers in tasklist.md
    m.reviewer_lineage_smi_added = len(re.findall(r"added_by\s*[:：]\s*smi_block", tasklist_text))
    m.reviewer_lineage_impact_added = len(re.findall(r"added_by\s*[:：]\s*impact_block", tasklist_text))

    combined_workflow_text = "\n".join([state_text, tasklist_text, requirements_text, worklog_text, ac_ledger_text])
    m.workflow_incident_entries = len(re.findall(r"Workflow Incident Review", combined_workflow_text))
    incident_type_values = re.findall(r"incident_type\s*\|\s*([^|\n]+)", combined_workflow_text)
    incident_type_values += re.findall(r"incident_type\s*[:：]\s*([A-Za-z0-9_-]+)", combined_workflow_text)
    incident_types = sorted({value.strip() for value in incident_type_values if value.strip()})
    m.incident_types = ",".join(incident_types)
    m.guardrail_detection_entries = len(
        re.findall(
            r"lint-[A-Za-z0-9_-]+|tests/fixtures/e2e-replay|HITL Outcome Audit|Worktree Provenance|AC Trace Ledger",
            combined_workflow_text,
        )
    )

    # Terminal state detection
    m.state_is_terminal, m.state_kind = _terminal_state(m.next_action, m.resume_from)

    return m


def aggregate(tasks: list[TaskMetrics]) -> dict:
    total = len(tasks)
    by_kind = Counter(t.state_kind for t in tasks)
    by_size = Counter(t.task_size for t in tasks)
    by_route = Counter(t.route_in_progress for t in tasks if t.route_in_progress not in ("none", "unknown"))
    by_intent = Counter(t.entry_intent for t in tasks if t.entry_intent != "unknown")

    gate_pass = {
        "requirements_approved": sum(1 for t in tasks if t.requirements_status == "approved"),
        "design_approved": sum(1 for t in tasks if t.design_status == "approved"),
        "human_check_approved": sum(1 for t in tasks if t.human_check_status == "approved"),
    }

    total_fix_attempts = sum(t.fix_attempts for t in tasks)
    total_error_log = sum(t.error_log_entries for t in tasks)
    total_smi = sum(t.reviewer_lineage_smi_added for t in tasks)
    total_impact = sum(t.reviewer_lineage_impact_added for t in tasks)
    by_incident_type: Counter[str] = Counter()
    for task in tasks:
        for incident_type in task.incident_types.split(","):
            if incident_type:
                by_incident_type[incident_type] += 1

    return {
        "total_tasks": total,
        "by_kind": dict(by_kind),
        "by_size": dict(by_size),
        "by_route_in_progress": dict(by_route),
        "by_entry_intent": dict(by_intent),
        "gate_pass_counts": gate_pass,
        "gate_pass_rates": {
            k: round(v / total * 100, 1) if total else 0.0 for k, v in gate_pass.items()
        },
        "total_fix_attempts": total_fix_attempts,
        "avg_fix_attempts": round(total_fix_attempts / total, 2) if total else 0.0,
        "total_error_log_entries": total_error_log,
        "reviewer_lineage": {
            "smi_block_added": total_smi,
            "impact_block_added": total_impact,
            "total_dynamic_additions": total_smi + total_impact,
        },
        "workflow_guardrails": {
            "workflow_incident_entries": sum(t.workflow_incident_entries for t in tasks),
            "guardrail_detection_entries": sum(t.guardrail_detection_entries for t in tasks),
            "by_incident_type": dict(by_incident_type),
        },
        "bounce": {
            "total_bounce_count": sum(t.bounce_count for t in tasks),
            "total_unparsed_route_sections": sum(t.unparsed_route_sections for t in tasks),
        },
    }


def render_text(tasks: list[TaskMetrics], summary: dict) -> str:
    lines = []
    lines.append("## GDD Telemetry")
    lines.append("")
    lines.append("### Overview")
    lines.append(f"- total_tasks: {summary['total_tasks']}")
    for kind, count in summary["by_kind"].items():
        lines.append(f"  - {kind}: {count}")
    lines.append("")
    if summary["by_size"]:
        lines.append("### Task Size Distribution")
        for size, count in sorted(summary["by_size"].items(), key=lambda x: -x[1]):
            lines.append(f"- {size}: {count}")
        lines.append("")
    if summary["by_route_in_progress"]:
        lines.append("### Route In Progress Distribution")
        for route, count in sorted(summary["by_route_in_progress"].items(), key=lambda x: -x[1]):
            lines.append(f"- {route}: {count}")
        lines.append("")
    if summary["by_entry_intent"]:
        lines.append("### Entry Intent Distribution")
        for intent, count in sorted(summary["by_entry_intent"].items(), key=lambda x: -x[1]):
            lines.append(f"- {intent}: {count}")
        lines.append("")
    lines.append("### Gate Pass Rate")
    rates = summary["gate_pass_rates"]
    counts = summary["gate_pass_counts"]
    for key in ("requirements_approved", "design_approved", "human_check_approved"):
        lines.append(f"- {key}: {counts[key]} ({rates[key]}%)")
    lines.append("")
    lines.append("### Fix Attempts")
    lines.append(f"- total: {summary['total_fix_attempts']}")
    lines.append(f"- avg per task: {summary['avg_fix_attempts']}")
    lines.append(f"- error_log_entries: {summary['total_error_log_entries']}")
    lines.append("")
    lines.append("### Reviewer Lineage (dynamic additions)")
    lineage = summary["reviewer_lineage"]
    lines.append(f"- smi_block_added: {lineage['smi_block_added']}")
    lines.append(f"- impact_block_added: {lineage['impact_block_added']}")
    lines.append(f"- total: {lineage['total_dynamic_additions']}")
    lines.append("")
    lines.append("### Workflow Guardrails")
    guardrails = summary["workflow_guardrails"]
    lines.append(f"- workflow_incident_entries: {guardrails['workflow_incident_entries']}")
    lines.append(f"- guardrail_detection_entries: {guardrails['guardrail_detection_entries']}")
    if guardrails["by_incident_type"]:
        lines.append("- by_incident_type:")
        for incident_type, count in sorted(guardrails["by_incident_type"].items(), key=lambda x: -x[1]):
            lines.append(f"  - {incident_type}: {count}")
    lines.append("")
    lines.append("### Bounce (Route Decision)")
    bounce = summary["bounce"]
    lines.append(f"- total_bounce_count: {bounce['total_bounce_count']}")
    lines.append(f"- total_unparsed_route_sections: {bounce['total_unparsed_route_sections']}")
    # AC-10 の「所在」。json / csv は per-task 行が持つが text は集計しか出さないので、
    # 未パース節を持つ task だけをここに並べる。値は `tasks` から機械導出し、
    # summary 側へは複写しない（数値の正本を 1 箇所に保つ）。
    unparsed_tasks = [t for t in tasks if t.unparsed_route_sections]
    if unparsed_tasks:
        lines.append("- unparsed_by_task:")
        for t in sorted(unparsed_tasks, key=lambda x: (-x.unparsed_route_sections, x.steering_id)):
            lines.append(f"  - {t.steering_id}: {t.unparsed_route_sections}")
    return "\n".join(lines)


def render_csv(tasks: list[TaskMetrics]) -> str:
    if not tasks:
        return ""
    from io import StringIO

    buf = StringIO()
    fieldnames = list(asdict(tasks[0]).keys())
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for t in tasks:
        writer.writerow(asdict(t))
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--root",
        action="append",
        default=None,
        help="Root directory to scan for .steering/. Can be repeated. Defaults to git root.",
    )
    parser.add_argument(
        "--include-worktrees",
        action="store_true",
        help="Also scan all worktrees from `git worktree list` (missing ones are skipped with a warning)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "csv"),
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    roots: list[Path] = []
    if args.root:
        roots = [Path(r).resolve() for r in args.root]
    else:
        # Auto-detect git root
        try:
            git_root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            roots = [Path(git_root)]
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: Not a git repo and --root not provided", file=sys.stderr)
            return 1

    for root in roots:
        if not root.is_dir():
            print(f"ERROR: root not found: {root}", file=sys.stderr)
            return 1

    if args.include_worktrees:
        try:
            wt_out = subprocess.check_output(
                ["git", "worktree", "list", "--porcelain"], text=True, stderr=subprocess.DEVNULL
            )
            for line in wt_out.splitlines():
                if line.startswith("worktree "):
                    wt_path = Path(line[len("worktree "):]).resolve()
                    if wt_path in roots:
                        continue
                    # ディレクトリを消した worktree も `git worktree prune` までは一覧に残る
                    if not wt_path.is_dir():
                        print(f"WARNING: skipped missing worktree: {wt_path}", file=sys.stderr)
                        continue
                    roots.append(wt_path)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # Non-fatal

    steering_pairs = find_steering_dirs(roots)
    tasks = [parse_task_metrics(d, w) for d, w in steering_pairs]
    summary = aggregate(tasks)

    if args.format == "json":
        print(json.dumps(
            {"tasks": [asdict(t) for t in tasks], "summary": summary},
            ensure_ascii=False,
            indent=2,
        ))
    elif args.format == "csv":
        print(render_csv(tasks))
    else:
        print(render_text(tasks, summary))

    return 0


if __name__ == "__main__":
    sys.exit(main())
