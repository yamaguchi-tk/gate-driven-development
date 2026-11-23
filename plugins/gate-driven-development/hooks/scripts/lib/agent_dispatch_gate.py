"""Judgment 1: Agent 起動時の工程別 model 強制。

過去の `Agent` 起動を調べると、`model` の未指定が多く、requirements と review では
特に多かった。未指定は host 既定（main セッションの
model）に落ちるため、main を Sonnet にしていると formal gate も Sonnet で走る。

phase → tier のマッピングは `scripts/resolve-gdd-model.py` の `PHASE_TO_TIER` /
`TIER_TO_MODEL["claude_code"]` を正本として再利用する（新しく重複したマッピングを
作らない）。この module は `classify_tier()` のテキストヒント解析（開いた入力）を
経由せず、辞書引きだけを使う——判定材料を「閉じた入力」に限定するため
（PR #83 の失敗: 自由文を機械判定しようとして 7 巡しても収束しなかった）。
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

_PLUGIN_ROOT = Path(__file__).resolve().parents[3]


def _load_resolver() -> ModuleType:
    path = _PLUGIN_ROOT / "scripts" / "resolve-gdd-model.py"
    spec = importlib.util.spec_from_file_location("gdd_agent_dispatch_gate_resolver", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load resolver from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_resolver = _load_resolver()

#: phase → tier（正本: `scripts/resolve-gdd-model.py` PHASE_TO_TIER）
PHASE_TO_TIER: dict[str, str] = _resolver.PHASE_TO_TIER
#: tier → Claude Code での必須 model（正本: 同ファイル TIER_TO_MODEL["claude_code"]）
REQUIRED_MODEL_BY_TIER: dict[str, str] = _resolver.TIER_TO_MODEL["claude_code"]

#: `state.md` の `Resume From` が正本になる planning phase
#: （`references/state-machine.md:199` — build フェーズの戻り先には使わない）。
PLANNING_PHASES: frozenset[str] = frozenset(
    {"gdd-brainstorming", "gdd-requirements-gating", "gdd-design-gating"}
)

#: `tasklist.md` の `Next Action` が正本になる build phase
#: （`references/state-machine.md:203` — 3 gate 承認後の formal な次工程）。
BUILD_PHASES: frozenset[str] = frozenset(
    {
        "gdd-task-breakdown",
        "gdd-test-driven-development",
        "gdd-subagent-driven-implementation",
        "gdd-implementation-gating",
        "gdd-systematic-debugging",
        "gdd-refactor-planning",
        "gdd-completion-check",
        "gdd-requesting-code-review",
        "gdd-pr-review",
        "gdd-requirements-amendment",
    }
)

#: `Agent(model=...)` を省略する dispatch のための表（model を明示した起動も、opus に固定した
#: agent は `judge_fixed_override` がこの表で照合する）。`agents/*.md` の frontmatter で
#: model が既に固定されている `subagent_type` と、その model（値は frontmatter と同じ。
#: tests/test_implementation_worker_agents.py が突き合わせる）。`Agent(model=...)` を省略すると
#: agent 定義側の model が適用されるので、判定 1 はこの model で工程を判定する（opus は
#: どの工程でも許されるので判定を省く）。phase Template が `model` を明示する runner
#: （gdd-formal-gate-runner・gdd-light-task-runner）は入れない（工程の tier で判定する）。
#: 実装の worker は task の `Complexity:` と `Gate Rounds` で controller が選び分けるので、
#: 工程の tier ではなく agent 定義の model で動かす。簡素化パス（gdd-code-simplifier）も sonnet に固定し、
#: worker と同じく agent 定義の model で工程を判定する。
FIXED_MODEL_BY_SUBAGENT_TYPE: dict[str, str] = {
    "gate-driven-development:gdd-code-simplifier": "sonnet",
    "gate-driven-development:gdd-completion-reviewer": "opus",
    "gate-driven-development:gdd-implementation-worker": "sonnet",
    "gate-driven-development:gdd-implementation-worker-heavy": "opus",
    "gate-driven-development:gdd-implementation-reviewer": "opus",
    "gate-driven-development:gdd-planning-reviewer": "opus",
    "gate-driven-development:gdd-qa-runner": "opus",
    "gate-driven-development:gdd-remediation-worker": "opus",
    "gate-driven-development:gdd-security-reviewer": "opus",
    # 判断の相談役（references/autonomy.md 判断の手順）
    "gate-driven-development:gdd-opus-advisor": "opus",
    "gate-driven-development:gdd-opus-advisor-max": "opus",
    # 着手前の、依頼の原文と既存コードの突き合わせ（references/brainstorming-steps.md の 9）
    "gate-driven-development:gdd-request-code-crosscheck": "opus",
    # 指摘の検証役（references/finding-dispositions.md § 検証役）
    "gate-driven-development:gdd-finding-verifier": "opus",
    # 独立レビュー（references/independent-review.md 契約 4）
    "gate-driven-development:gdd-independent-reviewer": "opus",
}
MODEL_FIXED_SUBAGENT_TYPES: frozenset[str] = frozenset(FIXED_MODEL_BY_SUBAGENT_TYPE)


def fixed_model(subagent_type: str) -> str:
    """agent 定義の frontmatter で固定した model を返す。表に無ければ空文字。

    `Agent(subagent_type=...)` には `gate-driven-development:gdd-xxx`（plugin prefix 付き）と
    `gdd-xxx`（bare）のどちらの表記も実測で渡ってくるため、両方を同一の subagent として扱う。
    """
    subagent_type = (subagent_type or "").strip()
    for name, model in FIXED_MODEL_BY_SUBAGENT_TYPE.items():
        if subagent_type in (name, name.split(":", 1)[-1]):
            return model
    return ""


#: phase-tier 表は各フェーズの GDD worker 向けであり、その下請けとして
#: dispatch される読み取り専用の汎用 agent（コードベース調査・plan 立案）には
#: tier の model 要件は及ばない。ここまで機械強制すると、調査目的の軽量
#: dispatch が誤検知される（独立レビュー Medium-7 指摘）。
#: Fable の相談役（`agents/gdd-fable-advisor.md`。references/autonomy.md 判断の手順）も、
#: 読み取り専用で工程の worker ではなく、工程の tier に無い model で動くので、同じく
#: model の値によらず対象外にする（Opus の相談役は FIXED_MODEL_BY_SUBAGENT_TYPE に置き、
#: model を明示した起動は判定する）。完全一致で比べるので、prefix 付きと bare の両方を並べる。
#: 提出前の照合（`agents/gdd-requirements-precheck.md`。references/requirements-gating-steps.md
#: Step 4a）も read-only で工程の worker ではなく、Sonnet に固定して opus 必須の
#: requirements-gating から起動するので、同じく対象外にする。
EXEMPT_INVESTIGATION_SUBAGENT_TYPES: frozenset[str] = frozenset(
    {
        "Explore",
        "Plan",
        "gdd-fable-advisor",
        "gate-driven-development:gdd-fable-advisor",
        "gdd-requirements-precheck",
        "gate-driven-development:gdd-requirements-precheck",
    }
)


def is_exempt_from_phase_model_check(subagent_type: str, model: str) -> bool:
    """`subagent_type`（と `model`）が判定 1 の対象外か判定する。

    対象外になるのは 2 種類で、扱いが異なる:
      1. `EXEMPT_INVESTIGATION_SUBAGENT_TYPES`（phase の tier 要件と無関係な
         読み取り専用の汎用調査 agent と、Fable の相談役）。`model` の値によらず常に対象外。
      2. `MODEL_FIXED_SUBAGENT_TYPES`（agent 定義の frontmatter で model 固定済み）のうち
         固定の model が opus のもの。`model` が **未指定のときだけ** 対象外にする（opus は
         どの工程でも許されるので、判定を省いても結果は同じ。opus 以外に固定したものは、
         呼び出し側が `fixed_model()` の値で工程を判定する）。Claude Code の model 解決順は
         起動時 `model` → agent frontmatter → 環境変数 → main セッションの順であり、
         frontmatter の `model: opus` は起動時に `model` が省略されたときだけ効く。
         起動時に `model` を明示指定すればそちらが優先されるため、`model=sonnet` 等
         で明示的にダウングレードされた場合は frontmatter が効かず、判定 1 が
         見逃してはならない（PR #91 人間レビュー指摘、High。実測: `model=sonnet` で
         固定 reviewer を起動すると rc=0・出力なしで見逃していた）。
         prefix 付き・bare の扱いは `fixed_model()` と同じ。
    """
    subagent_type = (subagent_type or "").strip()
    if not subagent_type:
        return False
    if subagent_type in EXEMPT_INVESTIGATION_SUBAGENT_TYPES:
        return True
    if (model or "").strip():
        return False
    return fixed_model(subagent_type) == "opus"


def resolve_phase(resume_from: str, next_action: str) -> str:
    """5 材料のうち Resume From / Next Action から現在工程を特定する。

    `Resume From` は planning phase 専用の正本なので、値が planning 語彙に
    一致する間はそちらを優先する（3 gate 承認前は `Next Action` が draft 記載値
    でしかないため）。一致しなければ `Next Action`（build phase の正本）を見る。
    どちらからも特定できなければ空文字を返す——ここで fail-open に倒さず、
    「工程不明」は判定 1 では何もしない（判定 4 の管轄に委ねる）。
    """
    resume_from = (resume_from or "").strip()
    next_action = _strip_decoration((next_action or "").strip())
    if resume_from in PLANNING_PHASES:
        return resume_from
    if next_action in BUILD_PHASES:
        return next_action
    return ""


def _strip_decoration(value: str) -> str:
    """`Next Action` に付く `| reason: ...` 等の装飾を取り除く。

    既存 hook（`gdd_check_3field_gate` の Review Status 読み取り等）が同じ値を
    読む際に使っている `sed 's/[[:space:]|].*//'`（最初の空白または `|` の
    手前までを採用）と同じ正規化をここでも揃える。
    """
    indices = [i for i in (value.find(" "), value.find("|")) if i != -1]
    if not indices:
        return value
    return value[: min(indices)]


#: `_normalize_model_family` が認識する family 名。`judge()` が要求しうる値
#: （`REQUIRED_MODEL_BY_TIER` の値域）と同じ集合で、実際に許可判定へ使う family
#: だけを列挙する。不許可な軽量モデルの family 名はここに含めない——リテラル
#: 名指しをしない契約（hooks 配下から特定モデル名の語を排除した
#: 経緯）を守るため、認識できない値は正規化せずそのまま返し、結果として常に
#: 不適切（許容集合に含まれない）として扱われる。
_KNOWN_MODEL_FAMILIES: frozenset[str] = frozenset({"opus", "sonnet"})


def _normalize_model_family(model: str) -> str:
    """`model` の値を family（`opus` / `sonnet`）に正規化する。

    Claude Code は起動時の `model` に alias（`opus`/`sonnet`）だけでなく
    `claude-opus-5` のような full ID も受理する。alias とだけ比較すると、
    full ID 指定を「不適切な model」と誤警告する（PR #91 人間レビュー指摘、
    Medium。実測: `model=claude-opus-5` で opus 必須 phase でも警告していた）。
    `inherit`（host 既定に落ちる）等、family を認識できない値はそのまま返す
    ——`_allowed_models()` の集合に一致しないため、未指定相当として扱われる
    （警告は出る。この扱いは変えない）。
    """
    normalized = (model or "").strip().lower()
    if not normalized:
        return normalized
    tokens = re.split(r"[^a-z0-9]+", normalized)
    for family in _KNOWN_MODEL_FAMILIES:
        if family in tokens:
            return family
    return normalized


def _allowed_models(required: str) -> frozenset[str]:
    """required model に対して許容される実際の model の集合。

    opus 必須 tier は opus のみ許容。sonnet 相当 tier は sonnet 推奨だが opus
    使用はコスト超過であって不適切ではないため許容する（false positive 回避。
    判定 1 の目的は伐ち漏らし防止であって倹約強制ではない）。集合に無い model
    ——ここには、費用が高く検出力が低いと実測で分かった軽量モデルも含まれる
    （`CHANGELOG.md:94-95`。ユーザー明示指示時のみ許容するが、それを機械判定
    する材料は無いので、tier の必須集合に無い限り常に warn する）——はすべて
    不適切として扱う。
    """
    if required == "opus":
        return frozenset({"opus"})
    return frozenset({required, "opus"})


def judge_fixed_override(phase: str, subagent_type: str, model: str) -> dict[str, str] | None:
    """opus に固定した agent を、明示した opus 以外の model で起動するなら violation dict を返す。

    明示した `model` は agent 定義の model より優先される（`is_exempt_from_phase_model_check`
    の docstring）。工程の tier が sonnet でも、opus に固定した agent（reviewer・相談役など）を
    下げるのは定義の上書きなので、工程の tier ではなく固定の model と比べる。直し方は
    `model` の省略である。opus 以外に固定した agent は扱わない（`judge` が工程の tier で見る）。
    """
    normalized = (model or "").strip().lower()
    if not normalized or fixed_model(subagent_type) != "opus":
        return None
    if _normalize_model_family(normalized) == "opus":
        return None
    return {
        "phase": phase,
        "tier": PHASE_TO_TIER.get(phase, ""),
        "required": "opus",
        "actual": normalized,
        "reason": "overrides_fixed",
    }


def judge(phase: str, model: str) -> dict[str, str] | None:
    """phase に対して model が未指定/不適切なら violation dict を返す。適切なら None。"""
    tier = PHASE_TO_TIER.get(phase)
    if tier is None:
        return None
    required = REQUIRED_MODEL_BY_TIER.get(tier)
    if required is None:
        return None

    normalized = (model or "").strip().lower()
    if not normalized:
        return {
            "phase": phase,
            "tier": tier,
            "required": required,
            "actual": "(unspecified)",
            "reason": "unspecified",
        }
    family = _normalize_model_family(normalized)
    if family not in _allowed_models(required):
        return {
            "phase": phase,
            "tier": tier,
            "required": required,
            "actual": normalized,
            "reason": "not_allowed",
        }
    return None
