#!/usr/bin/env python3
"""GDD Scorecard — skill / prompt 改訂の採否を行動メトリクスで判定する。

`collect-gdd-telemetry.py --format=json` の snapshot を 2 つ取り、改訂前（baseline）と
改訂後（candidate）を突き合わせて「採用してよいか」を出す。改訂の評価を実行者の
自己申告や主観レビューに任せると「良くなった気がする」で終わるため、実際に走った
task の行動ログだけで判定する。

## 使い方

```sh
# 改訂前にベースラインを取る
python3 scripts/collect-gdd-telemetry.py --include-worktrees --format=json > /tmp/baseline.json

# 改訂を入れて運用したあとに再取得
python3 scripts/collect-gdd-telemetry.py --include-worktrees --format=json > /tmp/candidate.json

# 判定
python3 scripts/gdd-scorecard.py --baseline /tmp/baseline.json --candidate /tmp/candidate.json

# 指標定義の一覧（この registry が指標の唯一の正本）
python3 scripts/gdd-scorecard.py --list-metrics
```

## キャリーオーバー除外

同一 repo で時系列比較すると、candidate snapshot は baseline の task を内包する。
そのまま比べると改訂前の実績で薄まるため、baseline に存在する `steering_id` は
candidate 集合から除外する。除外件数は `carried_over_excluded` として出力する。
baseline 時点で進行中だった task も「改訂前に始まった」ものとして除外される
（改訂の効果を測る対象は、改訂後に着手した task に限る）。
snapshot が元々 disjoint なら除外は 0 件で、そのまま全件が対象になる。

## 判定ルール（統計的有意性は使わない）

個人〜小チーム運用では A/B テストに必要な母数が集まらない。p 値の代わりに
「母数が足りなければ足りないと言う」ことで過剰主張を防ぐ。

- 母数が `--min-samples` 未満の指標は `insufficient_data`（improved とは言わない）
- 相対変化が `--noise-floor` 未満なら `flat`
- 差が「task 1 件分の振れ幅」(`unit / 母数`) 以下なら `flat`。n=4 の割合指標は
  task 1 件で 25 ポイント動くため、相対変化だけでは 1 件の偶然を改善と誤認する
- それ以外を direction に従って `improved` / `regressed`
- 全体判定: improved のみ = `adopt` / regressed のみ = `reject` / 両方 = `mixed` /
  決め手なし = `inconclusive`
- baseline か candidate の task 総数が `--min-samples` 未満なら、個別指標に関わらず
  全体判定を `inconclusive`（理由: データ不足）に固定する

## Exit code

- 0: 正常完了
- 1: 入力 path 不正 / JSON 不正
- 2: usage error
- 3: `--fail-on-regress` 指定時に regressed を含む判定（reject / mixed）だった
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

DEFAULT_MIN_SAMPLES = 3
DEFAULT_NOISE_FLOOR = 0.10

LOWER_IS_BETTER = "lower_is_better"
HIGHER_IS_BETTER = "higher_is_better"


@dataclass(frozen=True)
class MetricValue:
    """指標値と、その値を支える母数。母数は判定と表示の両方で必ず持ち回る。"""

    value: float
    sample: int


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    direction: str
    proxy: str
    unit: float
    """task 1 件が動かせる最大幅。割合指標は 100（0%↔100% に振れる）、件数指標は 1。

    `unit / 母数` が「1 件の task で説明できる変化量」になり、これを超えない差は
    改善とも悪化とも呼ばない。小サンプルでは相対変化の noise-floor が機能しない
    （n=4 の割合指標は 1 件で 25 ポイント動く）ための下駄。
    """

    compute: Callable[[list[dict]], "MetricValue | None"]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator * 100 if denominator else 0.0


def _avg_of(field: str) -> Callable[[list[dict]], MetricValue | None]:
    def compute(tasks: list[dict]) -> MetricValue | None:
        if not tasks:
            return None
        values = [float(t.get(field, 0) or 0) for t in tasks]
        return MetricValue(round(_mean(values), 3), len(tasks))

    return compute


def _gate_first_pass(field: str) -> Callable[[list[dict]], MetricValue | None]:
    """gate 一発通過率。母数はその gate に到達した task だけに限る。

    未到達 task を分母に含めると、進行中 task が多い時期の通過率が不当に下がり、
    改訂と無関係な差が出てしまう。
    """

    def compute(tasks: list[dict]) -> MetricValue | None:
        reached = [t for t in tasks if (t.get(field) or "unknown") != "unknown"]
        if not reached:
            return None
        approved = sum(1 for t in reached if t.get(field) == "approved")
        return MetricValue(round(_rate(approved, len(reached)), 1), len(reached))

    return compute


def _completion_rate(tasks: list[dict]) -> MetricValue | None:
    if not tasks:
        return None
    done = sum(1 for t in tasks if t.get("state_kind") == "done")
    return MetricValue(round(_rate(done, len(tasks)), 1), len(tasks))


def _reroute_rate(tasks: list[dict]) -> MetricValue | None:
    if not tasks:
        return None
    rerouted = sum(1 for t in tasks if (t.get("route_in_progress") or "none") not in ("none", "unknown"))
    return MetricValue(round(_rate(rerouted, len(tasks)), 1), len(tasks))


# 指標定義の単一の正本。追加・変更はここだけで行い、SKILL.md や README に表を複製しない
# （複製すると片方だけ直って乖離する）。一覧は `--list-metrics` で機械的に取り出す。
METRICS: list[Metric] = [
    Metric(
        key="avg_fix_attempts",
        label="平均 Fix Attempts",
        direction=LOWER_IS_BETTER,
        proxy="実装が gate を一発で通ったか（差し戻し後の作り直し回数）",
        unit=1.0,
        compute=_avg_of("fix_attempts"),
    ),
    Metric(
        key="error_log_per_task",
        label="task あたり Error Log 件数",
        direction=LOWER_IS_BETTER,
        proxy="実行時に踏んだエラーの量（指示の曖昧さで手戻りが増えていないか）",
        unit=1.0,
        compute=_avg_of("error_log_entries"),
    ),
    Metric(
        key="incident_per_task",
        label="task あたり Workflow Incident 件数",
        direction=LOWER_IS_BETTER,
        proxy="ワークフロー自体の事故（誤ルーティング・状態不整合）の発生量",
        unit=1.0,
        compute=_avg_of("workflow_incident_entries"),
    ),
    Metric(
        key="completion_rate",
        label="完走率 (%)",
        direction=HIGHER_IS_BETTER,
        proxy="着手した task が done まで到達した割合",
        unit=100.0,
        compute=_completion_rate,
    ),
    Metric(
        key="reroute_rate",
        label="リルート発生率 (%)",
        direction=LOWER_IS_BETTER,
        proxy="途中で別 route に飛ばされた task の割合（手戻りの proxy）",
        unit=100.0,
        compute=_reroute_rate,
    ),
    Metric(
        key="requirements_first_pass_rate",
        label="Requirements gate 一発通過率 (%)",
        direction=HIGHER_IS_BETTER,
        proxy="要件整理の指示が一度で承認水準に届いたか",
        unit=100.0,
        compute=_gate_first_pass("requirements_status"),
    ),
    Metric(
        key="design_first_pass_rate",
        label="Design gate 一発通過率 (%)",
        direction=HIGHER_IS_BETTER,
        proxy="設計の指示が一度で承認水準に届いたか",
        unit=100.0,
        compute=_gate_first_pass("design_status"),
    ),
    Metric(
        key="human_check_first_pass_rate",
        label="Human Check 一発通過率 (%)",
        direction=HIGHER_IS_BETTER,
        proxy="HITL 提示が人間の差し戻しなしで通ったか",
        unit=100.0,
        compute=_gate_first_pass("human_check_status"),
    ),
]


def load_snapshot(path: Path) -> list[dict]:
    """telemetry JSON から tasks[] を取り出す。"""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "tasks" not in raw:
        raise ValueError(f"telemetry JSON に tasks[] がない: {path}")
    tasks = raw["tasks"]
    if not isinstance(tasks, list):
        raise ValueError(f"tasks[] が list ではない: {path}")
    return tasks


def exclude_carry_over(baseline: list[dict], candidate: list[dict]) -> tuple[list[dict], int]:
    """baseline に既にある steering_id を candidate から除く。"""
    seen = {t.get("steering_id") for t in baseline}
    fresh = [t for t in candidate if t.get("steering_id") not in seen]
    return fresh, len(candidate) - len(fresh)


def relative_delta(baseline: float, candidate: float) -> float:
    delta = candidate - baseline
    if baseline == 0:
        if delta == 0:
            return 0.0
        return math.inf if delta > 0 else -math.inf
    return delta / abs(baseline)


def judge_metric(
    metric: Metric,
    baseline: MetricValue | None,
    candidate: MetricValue | None,
    min_samples: int,
    noise_floor: float,
) -> dict:
    row: dict = {
        "key": metric.key,
        "label": metric.label,
        "direction": metric.direction,
        "proxy": metric.proxy,
        "baseline": baseline.value if baseline else None,
        "candidate": candidate.value if candidate else None,
        "baseline_sample": baseline.sample if baseline else 0,
        "candidate_sample": candidate.sample if candidate else 0,
        "delta": None,
        "relative_delta": None,
        "single_task_effect": None,
        "verdict": "insufficient_data",
    }

    if baseline is None or candidate is None:
        row["reason"] = "母数となる task がない"
        return row
    if baseline.sample < min_samples or candidate.sample < min_samples:
        row["reason"] = f"母数が min-samples({min_samples}) 未満"
        return row

    delta = round(candidate.value - baseline.value, 3)
    rel = relative_delta(baseline.value, candidate.value)
    # 母数が小さい側に合わせる。少ない方ほど task 1 件の影響が大きいため
    single_task_effect = round(metric.unit / min(baseline.sample, candidate.sample), 3)
    row["delta"] = delta
    row["relative_delta"] = None if math.isinf(rel) else round(rel, 3)
    row["single_task_effect"] = single_task_effect

    if abs(rel) < noise_floor:
        row["verdict"] = "flat"
        row["reason"] = f"相対変化が noise-floor({noise_floor:.0%}) 未満"
        return row
    if abs(delta) <= single_task_effect:
        row["verdict"] = "flat"
        row["reason"] = f"task 1 件分（{single_task_effect}）で説明できる差"
        return row

    improved = delta < 0 if metric.direction == LOWER_IS_BETTER else delta > 0
    row["verdict"] = "improved" if improved else "regressed"
    return row


def judge_overall(rows: list[dict], baseline_count: int, candidate_count: int, min_samples: int) -> dict:
    improved = [r["key"] for r in rows if r["verdict"] == "improved"]
    regressed = [r["key"] for r in rows if r["verdict"] == "regressed"]

    if baseline_count < min_samples or candidate_count < min_samples:
        return {
            "verdict": "inconclusive",
            "reason": (
                f"データ不足: baseline {baseline_count} 件 / candidate {candidate_count} 件"
                f"（min-samples={min_samples}）。改善とも悪化とも言えない"
            ),
            "improved": improved,
            "regressed": regressed,
        }

    if improved and not regressed:
        verdict, reason = "adopt", f"改善 {len(improved)} 指標・悪化なし"
    elif regressed and not improved:
        verdict, reason = "reject", f"悪化 {len(regressed)} 指標・改善なし"
    elif improved and regressed:
        verdict, reason = "mixed", f"改善 {len(improved)} 指標・悪化 {len(regressed)} 指標。トレードオフを人間が判断する"
    else:
        verdict, reason = (
            "inconclusive",
            "改善とも悪化とも呼べる変化がない（noise-floor 未満、または task 1 件分の振れ幅の範囲内）",
        )

    return {"verdict": verdict, "reason": reason, "improved": improved, "regressed": regressed}


def render_metrics_registry(fmt: str) -> str:
    if fmt == "json":
        return json.dumps(
            {
                "metrics": [
                    {"key": m.key, "label": m.label, "direction": m.direction, "proxy": m.proxy}
                    for m in METRICS
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
    lines = ["## GDD Scorecard Metrics", ""]
    lines.append("| key | 指標 | 方向 | 何の proxy か |")
    lines.append("|---|---|---|---|")
    for m in METRICS:
        arrow = "低いほど良い" if m.direction == LOWER_IS_BETTER else "高いほど良い"
        lines.append(f"| `{m.key}` | {m.label} | {arrow} | {m.proxy} |")
    return "\n".join(lines)


def _format_value(value: float | None) -> str:
    return "-" if value is None else f"{value:g}"


def render_text(payload: dict) -> str:
    sample = payload["sample"]
    overall = payload["overall"]
    lines = ["## GDD Scorecard", ""]
    lines.append("### Sample")
    lines.append(f"- baseline: n={sample['baseline_tasks']}")
    lines.append(f"- candidate: n={sample['candidate_tasks']}（carry-over 除外 {sample['carried_over_excluded']} 件）")
    lines.append(f"- min-samples: {sample['min_samples']} / noise-floor: {sample['noise_floor']:.0%}")
    lines.append("")
    lines.append("### Metrics")
    lines.append("| 指標 | baseline | candidate | 差分 | 判定 | 母数 |")
    lines.append("|---|---|---|---|---|---|")
    for row in payload["metrics"]:
        n = f"n={row['baseline_sample']}→{row['candidate_sample']}"
        lines.append(
            f"| {row['label']} (`{row['key']}`) | {_format_value(row['baseline'])} | "
            f"{_format_value(row['candidate'])} | {_format_value(row['delta'])} | {row['verdict']} | {n} |"
        )
    lines.append("")
    lines.append("### Overall")
    lines.append(f"- verdict: **{overall['verdict']}**")
    lines.append(f"- reason: {overall['reason']}")
    if overall["improved"]:
        lines.append(f"- improved: {', '.join(overall['improved'])}")
    if overall["regressed"]:
        lines.append(f"- regressed: {', '.join(overall['regressed'])}")
    return "\n".join(lines)


def build_payload(
    baseline_tasks: list[dict],
    candidate_tasks: list[dict],
    min_samples: int,
    noise_floor: float,
) -> dict:
    fresh, excluded = exclude_carry_over(baseline_tasks, candidate_tasks)
    rows = [
        judge_metric(m, m.compute(baseline_tasks), m.compute(fresh), min_samples, noise_floor)
        for m in METRICS
    ]
    overall = judge_overall(rows, len(baseline_tasks), len(fresh), min_samples)
    return {
        "sample": {
            "baseline_tasks": len(baseline_tasks),
            "candidate_tasks": len(fresh),
            "carried_over_excluded": excluded,
            "min_samples": min_samples,
            "noise_floor": noise_floor,
        },
        "metrics": rows,
        "overall": overall,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--baseline", help="改訂前の telemetry JSON")
    parser.add_argument("--candidate", help="改訂後の telemetry JSON")
    parser.add_argument("--list-metrics", action="store_true", help="指標定義の一覧を出して終了する")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--min-samples", type=int, default=DEFAULT_MIN_SAMPLES)
    parser.add_argument(
        "--noise-floor",
        type=float,
        default=DEFAULT_NOISE_FLOOR,
        help="相対変化がこの割合未満なら flat 扱い（既定 0.10 = 10%%）",
    )
    parser.add_argument(
        "--fail-on-regress",
        action="store_true",
        help="regressed を含む判定（reject / mixed）のとき exit 3 を返す",
    )
    args = parser.parse_args()

    if args.list_metrics:
        print(render_metrics_registry(args.format))
        return 0

    if not args.baseline or not args.candidate:
        parser.error("--baseline と --candidate は必須（--list-metrics 指定時を除く）")

    if args.min_samples < 1:
        parser.error("--min-samples は 1 以上")
    if args.noise_floor < 0:
        parser.error("--noise-floor は 0 以上")

    try:
        baseline_tasks = load_snapshot(Path(args.baseline))
        candidate_tasks = load_snapshot(Path(args.candidate))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = build_payload(baseline_tasks, candidate_tasks, args.min_samples, args.noise_floor)

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))

    if args.fail_on_regress and payload["overall"]["verdict"] in ("reject", "mixed"):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
