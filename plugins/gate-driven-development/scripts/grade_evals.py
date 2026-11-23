#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FLAGS = re.IGNORECASE | re.DOTALL
MAX_SEARCH_TEXT_CHARS = 20_000
DEFAULT_CATEGORY = "uncategorized"
DEFAULT_PRIORITY = "normal"


@dataclass(frozen=True)
class Rule:
    mode: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class CompiledRule:
    mode: str
    patterns: tuple[re.Pattern[str], ...]


def any_rule(*patterns: str) -> Rule:
    return Rule("any", patterns)


def all_rule(*patterns: str) -> Rule:
    return Rule("all", patterns)


RULES: dict[str, Rule] = {
    ".steering または `.cursor/plans` を作らないことに言及がある": any_rule(
        r"\.steering.*(?:作らない|作成しない|作りません|作らず)",
        r"\.cursor/plans.*(?:作らない|作成しない|作りません|作らず)",
        r"artifact.*(?:作らない|未作成)",
        r"artifact を作らず",
    ),
    "/gdd-dev にまだ handoff しないことに言及がある": any_rule(
        r"/gdd-dev.*(?:handoff\s*しない|入らない|開始せず)",
        r"まだ `/gdd-dev`.*(?:始めない|hand.?off しない)",
        r"`?/gdd-dev`?.*(?:はまだ.*始めません|には.*入りません|には.*入らない|まだ.*始めません)",
        r"formal workflow.*(?:入らない|始めない)",
        r"相談.*(?:留める|留まり).*?/gdd-dev",
        r"勝手に開始しません",
    ),
    "Current Task / Pending Tasks / Completed Tasks に言及がある": all_rule(
        r"Current Task",
        r"Pending Tasks",
        r"Completed Tasks",
    ),
    "非終端 state では status summary だけで止まらないと説明している": all_rule(
        r"non-terminal|非終端",
        r"status summary|状態説明|要約",
        r"止まらない|止めない|継続|閉じない",
    ),
    "`gdd-task-breakdown` を実行して `tasklist.md` を更新すると説明している": all_rule(
        r"gdd-task-breakdown",
        r"tasklist\.md",
        r"実行|更新|作成|初期化",
    ),
    "`gdd-stop` marker に言及がある": any_rule(
        r"gdd-stop"
    ),
    "`reason=\"blocked\"` に言及がある": all_rule(
        r"gdd-stop",
        r'reason="?blocked"?',
    ),
    "`gdd-test-failure-debug-pack` に言及がある": any_rule(
        r"gdd-test-failure-debug-pack"
    ),
    "`Current Task` と `Failure Command` を含めることに言及がある": all_rule(
        r"Current Task",
        r"Failure Command",
    ),
    "`Expected` と `Actual` を分けることに言及がある": all_rule(
        r"Expected",
        r"Actual",
    ),
    "`Next Action` 更新は `gdd-systematic-debugging` に委譲すると説明している": all_rule(
        r"Next Action",
        r"gdd-systematic-debugging",
        r"委譲|任せる|更新しない|routing",
    ),
    "再現条件と `Failure Surface` を含めることに言及がある": all_rule(
        r"Reproduction|再現",
        r"Failure Surface",
    ),
    "`Evidence` と `Root Cause Hypothesis` と `Confidence` に言及がある": all_rule(
        r"Evidence",
        r"Root Cause Hypothesis",
        r"Confidence",
    ),
    "`Workaround` と `Fix Plan` を分けることに言及がある": all_rule(
        r"Workaround",
        r"Fix Plan",
    ),
    "`gdd-systematic-debugging` に handoff すると説明している": all_rule(
        r"gdd-systematic-debugging",
        r"Handoff|handoff|引き継ぐ|渡す",
    ),
    "`Worklog Decision` と理由を含めることに言及がある": all_rule(
        r"Worklog Decision",
        r"理由|reason",
    ),
    "再発時に `worklog.md` 更新可否を判断すると説明している": all_rule(
        r"worklog\.md",
        r"再発|同じ Current Task|失敗が続",
        r"判断|可否|yes|no",
    ),
    "候補一覧または選び方に言及がある": any_rule(
        r"候補一覧",
        r"選び方",
        r"どれを再開",
        r"どの steering.*選",
    ),
    "Human Check Status に waived を使わないと説明している": all_rule(
        r"waived",
        r"(?:使えない|使えません|使わない|してはいけない)",
    ),
    "human check 承認後は追加の人間承認なしで自走すると説明している": all_rule(
        r"human check 承認後|Human Check Status.?=.?approved",
        r"追加.*人間承認.*(?:なし|求めない|待たない|挟まない|不要)",
    ),
    "Latest Tech Context に言及がある": any_rule(r"Latest Tech Context"),
    "Latest Tech Context または External References に言及がある": any_rule(
        r"Latest Tech Context",
        r"External References",
    ),
    "Next Action=gdd-test-driven-development に言及がある": any_rule(
        r"Next Action.?=.?gdd-test-driven-development"
    ),
    "`Next Action=gdd-completion-check` のままにすることに言及がある": any_rule(
        r"Next Action.?=.?gdd-completion-check",
        r"gdd-completion-check.*(?:のまま|維持)",
    ),
    "Open Questions に落とすことに言及がある": any_rule(r"Open Questions"),
    "Behavior Change Summary に言及がある": any_rule(r"Behavior Change Summary"),
    "Route / Ownership Matrix に言及がある": any_rule(
        r"Route / Ownership Matrix",
        r"Route / Ownership",
        r"ownership matrix",
    ),
    "Sensitive Data / Masking Policy に言及がある": any_rule(
        r"Sensitive Data / Masking Policy",
        r"masking policy",
    ),
    "Human Check Questions に言及がある": any_rule(r"Human Check Questions"),
    "`承認ポイント` に言及がある": any_rule(
        r"承認ポイント",
        r"承認事項",
    ),
    "blocking Open Questions なら human-check-waiting に進めないと説明している": all_rule(
        r"Open Questions",
        r"human-check-waiting",
        r"進めない|入れない|止める|残っている間は",
    ),
    "Requirements Review Status に言及がある": any_rule(r"Requirements Review Status"),
    "required external security evidence の代替ではないことに言及がある": all_rule(
        r"external security evidence|security evidence|verifier hook",
        r"代替ではない|代替ではありません|代替ではなく追加|置き換えない|置き換えません|代わりではない|やめる話ではありません",
    ),
    "Implementation Gate Evidence の不足を build loop 内で扱うことに言及がある": all_rule(
        r"Implementation Gate Evidence|Reviewed by|impl-gat",
        r"gdd-implementation-gating|gdd-systematic-debugging|build loop|build レーン",
        r"human_recheck_required.*(?:ではない|にしない)|human recheck.*(?:不要|戻さない)|人間再承認.*(?:不要|戻さない)",
    ),
    "procedural / evidence 反復では human recheck に戻さないことに言及がある": all_rule(
        r"procedural|evidence|Reviewed by|verification wording|metadata|記録手順",
        r"human_recheck_required.*(?:ではない|ではなく|にしない)|human recheck.*(?:不要|戻さない)|人間再承認.*(?:不要|戻さない)",
        r"gdd-implementation-gating|gdd-completion-check|blocked|route recalibration|再実行",
    ),
    "Verification に `method` / `status` / `evidence` / `notes` が必要だと説明している": all_rule(
        r"method",
        r"status",
        r"evidence",
        r"notes",
    ),
    "`Human Check Status=approved` が `gdd-design-gating` の前提だと説明している": all_rule(
        r"gdd-design-gating",
        r"Human Check Status.?=.?approved|Human Check Status.*approved",
        r"Requirements Review Status.?=.?approved|Requirements Review Status.*approved",
    ),
    "`Human Check Status` の許容値 `pending` / `changes_requested` / `approved` に言及がある": all_rule(
        r"pending",
        r"changes_requested",
        r"approved",
    ),
    "`新規開始` か `再開` かの確認を要求している": any_rule(
        r"新規(?:開始)?\s*か.*再開",
        r"再開\s*か.*新規(?:開始)?",
        r"新規開始.*再開",
        r"再開.*新規開始",
        r"新規か再開か",
        r"new.*/.*resume",
    ),
    "`次の1アクション` に相当する案内がある": any_rule(
        r"次の1アクション",
        r"次に.*(?:する|選ぶ|確認する)",
        r"不足前提のチェックリスト",
        r"復旧手順",
    ),
    "active worktree 側 `state.md` を正本として扱うことに言及がある": all_rule(
        r"active worktree",
        r"state\.md",
        r"正本|canonical",
    ),
    "active steering を一意に決められないことに言及がある": any_rule(
        r"active steering.*(?:一意|1 つ).*(?:決められない|解決できない)",
        r"候補のどれを active steering にするか.*(?:推測せず|決めず)",
        r"active steering.*(?:複数|candidate)",
    ),
    "active worktree 側 `tasklist.md` を正本として扱うことに言及がある": all_rule(
        r"active worktree",
        r"tasklist\.md",
        r"正本|canonical",
    ),
    "canonical artifact を worktree 側へ切り替えることに言及がある": all_rule(
        r"canonical artifact|正本",
        r"worktree 側",
    ),
    "gdd-completion-check に言及がある": any_rule(r"gdd-completion-check"),
    "gdd-design-gating に戻すことに言及がある": any_rule(r"gdd-design-gating"),
    "gdd-design-gating に言及がある": any_rule(r"gdd-design-gating"),
    "design.md に lightweight design skeleton、state.md に Gate Status が含まれる": all_rule(
        r"design\.md",
        r"state\.md",
        r"Gate Status|Requirements Review Status|Design Review Status|Human Check Status|Resume From",
    ),
    "design_detail_only に言及がある": any_rule(r"design_detail_only"),
    "entry intent が `ambiguous` だと説明している": any_rule(r"ambiguous"),
    "entry intent を `new` と判断することに言及がある": any_rule(
        r"entry intent.*`?new`?",
        r"`new` と判断",
        r"new cue",
        r"新規.?\(new\)",
    ),
    "entry intent を `resume` と判断することに言及がある": any_rule(
        r"entry intent.*`?resume`?",
        r"`resume` と判断",
        r"`resume` として扱",
    ),
    "fail-closed に言及がある": any_rule(
        r"fail-closed",
        r"自動では進めません",
        r"そのまま formal workflow.*進められません",
        r"そのまま.*続行できません",
    ),
    "fail-closed または done に進めないことに言及がある": any_rule(
        r"fail-closed",
        r"done に進めない",
        r"done には進めない",
        r"done に進めません",
        r"done には進めません",
        r"`done` に進めない",
        r"`done` には進めない",
        r"`done` に進めません",
        r"`done` には進めません",
        r"`done` にせず",
        r"完了できない",
    ),
    "formal な `Next Action` / `Review Status` は変えないことに言及がある": all_rule(
        r"Next Action",
        r"Review Status",
        r"変更しません|変えない|変えません|更新しません",
    ),
    "git または worktree capability 不足に言及がある": all_rule(
        r"git|worktree",
        r"使えない|不足|capability|検知",
    ),
    "human check が必須 gate であることに言及がある": all_rule(
        r"human check",
        r"必須 gate|必須ゲート",
    ),
    "human check の再実施に言及がある": all_rule(
        r"human check",
        r"再実施|取り直し|再度|再承認",
    ),
    "human check の前段であることに言及がある": all_rule(
        r"human check",
        r"前段|前に|その通過後",
    ),
    "human check を取り直さないことに言及がある": any_rule(
        r"human check.*(?:取り直さない|取り直しません|再実施しない|再実施しません|やり直さない|再実施せず)",
        r"human check を再実施せず",
        r"human check には戻しません",
        r"Human Check Status.*approved.*(?:のまま|維持)",
    ),
    "human-check-waiting に言及がある": any_rule(r"human-check-waiting"),
    "human-check-waiting への差し戻しが説明されている": any_rule(r"human-check-waiting"),
    "human_recheck_required に言及がある": any_rule(r"human_recheck_required"),
    "human_recheck_required または planning_rework_required に言及がある": any_rule(
        r"human_recheck_required",
        r"planning_rework_required",
    ),
    "gdd-implementation-gating に言及がある": any_rule(r"gdd-implementation-gating"),
    "gdd-requirements-gating の applicable reviewer selection に言及がある": all_rule(
        r"gdd-requirements-gating",
        r"gdd-planning-reviewer",
        r"必要時|必要な reviewer|applicable|選択|選ぶ|reviewer-selection",
    ),
    "gdd-design-gating の applicable reviewer selection に言及がある": all_rule(
        r"gdd-design-gating",
        r"gdd-planning-reviewer",
        r"必要時|必要な reviewer|applicable|選択|選ぶ|reviewer-selection",
    ),
    "gdd-implementation-gating の applicable reviewer selection に言及がある": all_rule(
        r"gdd-implementation-gating",
        r"gdd-implementation-reviewer",
        r"gdd-security-reviewer",
        r"必要時|必要な reviewer|applicable|選択|選ぶ|reviewer-selection",
    ),
    "Reviewer Selection 記録に言及がある": any_rule(
        r"Reviewer Selection",
        r"Planning Reviewer Selection",
        r"Implementation Reviewer Selection",
        r"reviewer selection record",
    ),
    "Implementation Reviewer Selection 記録に言及がある": any_rule(
        r"Implementation Reviewer Selection"
    ),
    "gdd-implementation-reviewer が契約変更で必須だと説明している": all_rule(
        r"gdd-implementation-reviewer",
        r"必須|常時|always",
        r"state-machine|self-contained-contract|reviewer-selection|gate|resume|verification semantics|user-visible|AC|contract|品質|spec",
    ),
    "gdd-implementation-gating で medium 指摘を waived で流さないと説明している": all_rule(
        r"gdd-implementation-gating",
        r"medium",
        r"waived",
        r"(?:流さない|使わない|許可しない|解消する|受容しない)",
    ),
    "`changes_requested` 後も自律 remediation すると説明している": all_rule(
        r"changes_requested",
        r"自律 remediation|自律修正|ユーザー確認待ち.*(?:しない|せず|止めない)|報告だけで終わらせない",
    ),
    "`High` を `Medium` より優先すると説明している": all_rule(
        r"High",
        r"Medium|ops-blocking medium",
        r"優先|最優先|先に",
    ),
    "`ops-blocking medium` または実運用影響 medium に言及がある": any_rule(
        r"ops-blocking medium",
        r"実運用.*medium",
        r"運用影響.*medium",
    ),
    "`worklog.md` に根本原因と route 判断を書くことに言及がある": all_rule(
        r"worklog\.md",
        r"根本原因|root cause",
        r"route 判断|前回との差分|比較",
    ),
    "`implementation_fix_only` の盲目的反復を止めることに言及がある": all_rule(
        r"implementation_fix_only",
        r"blind|盲目的|繰り返さない|3 回目",
        r"design_detail_only|human_recheck_required|planning_rework_required|fail-closed",
    ),
    "legacy root candidate または migration に言及がある": any_rule(
        r"legacy root candidate",
        r"migration",
        r"移行対象",
        r"legacy root",
        r"root .*copy",
    ),
    "lightweight design skeleton または detailed design gate に言及がある": any_rule(
        r"lightweight design skeleton",
        r"detailed design gate",
        r"詳細設計ゲート",
    ),
    "gdd-brainstorming に言及がある": any_rule(r"gdd-brainstorming"),
    "gdd-brainstorming の新規作成から入り直さない": any_rule(
        r"gdd-brainstorming.*(?:入り直さない|やり直さない)",
        r"要件.?設計.*壁打ち.*やり直す必要はなく",
        r"壁打ちからやり直す必要はなく",
        r"設計の壁打ち.*入り直しません",
        r"新規の requirements/design ドラフト作成に進まない",
        r"最初から進め直さない",
        r"入り直しません",
    ),
    "planning_rework_required に言及がある": any_rule(r"planning_rework_required"),
    "gdd-pre-workflow-brainstorming に言及がある": any_rule(r"gdd-pre-workflow-brainstorming"),
    "gdd-requirements-gating に言及がある": any_rule(r"gdd-requirements-gating"),
    "gdd-requirements-gating への言及がある": any_rule(r"gdd-requirements-gating"),
    "requirements.md に実装方針が含まれる": all_rule(
        r"requirements\.md",
        r"実装方針",
    ),
    "reviewer status を pending で初期化することに言及がある": all_rule(
        r"reviewer status|review status|Review Status",
        r"pending",
    ),
    "same-name ambient asset または衝突に言及がある": any_rule(
        r"same-name ambient asset",
        r"衝突",
    ),
    "adr.md が optional だと説明している": all_rule(
        r"adr\.md",
        r"optional|任意",
    ),
    "adr.md が canonical artifact や routing source ではないことに言及がある": all_rule(
        r"adr\.md",
        r"canonical|正本|routing source|gate",
        r"ではない|にしない|含めない",
    ),
    "adr.md が無くても止めないことに言及がある": all_rule(
        r"adr\.md",
        r"無くても|なくても|欠如|無い",
        r"止めない|止まらない|blocked にしない|fail-closed にしない",
    ),
    "adr.md に Context / Decision / Why / Consequences を残すことに言及がある": all_rule(
        r"adr\.md",
        r"Context",
        r"Decision",
        r"Why",
        r"Consequences",
    ),
    "plugin-managed Cursor symlink は衝突に含めないことに言及がある": all_rule(
        r"plugin-managed|cursor symlink|symlink alias",
        r"衝突に含めない|同一 asset|同じ asset|alias",
    ),
    "cursor-links.tsv または install-cursor-links.sh に言及がある": any_rule(
        r"cursor-links\.tsv",
        r"install-cursor-links\.sh",
    ),
    "別実体の同名 asset だけを衝突扱いすることに言及がある": all_rule(
        r"別実体|別配布物|third-party|第三者",
        r"衝突|unsupported configuration|fail-closed",
    ),
    "external verifier hook または security_evidence に言及がある": any_rule(
        r"external verifier hook",
        r"security_evidence:",
    ),
    "security_evidence:code と security_evidence:sca に言及がある": all_rule(
        r"security_evidence:code",
        r"security_evidence:sca",
    ),
    "security_evidence:code に言及がある": any_rule(r"security_evidence:code"),
    "security_evidence:sca に言及がある": any_rule(r"security_evidence:sca"),
    "gdd-subagent-driven-implementation に言及がある": any_rule(
        r"gdd-subagent-driven-implementation"
    ),
    "`gdd-systematic-debugging` に誤送しないことに言及がある": all_rule(
        r"gdd-systematic-debugging",
        r"誤送しない|送らない|戻さない|振り分けない",
    ),
    "gdd-task-breakdown に言及がある": any_rule(r"gdd-task-breakdown"),
    "task 単位 review の取りこぼしを done 前に確認することに言及がある": all_rule(
        r"取りこぼし",
        r"done 前|gdd-completion-check|task.?単位",
    ),
    "gdd-test-driven-development に言及がある": any_rule(
        r"gdd-test-driven-development"
    ),
    "unsupported configuration または deterministic に解決できないことに言及がある": any_rule(
        r"unsupported configuration",
        r"deterministic に解決できない",
        r"決定的に解決できない",
    ),
    "gdd-using-git-worktrees helper に言及がある": any_rule(
        r"gdd-using-git-worktrees"
    ),
    "gdd-using-git-worktrees に言及がある": any_rule(
        r"gdd-using-git-worktrees"
    ),
    "gdd-completion-reviewer に言及がある": any_rule(
        r"gdd-completion-reviewer"
    ),
    "gdd-planning-reviewer に言及がある": any_rule(
        r"gdd-planning-reviewer"
    ),
    "gdd-requesting-code-review に言及がある": any_rule(
        r"gdd-requesting-code-review"
    ),
    "gdd-requesting-code-review を generic request では使わないことに言及がある": any_rule(
        r"gdd-requesting-code-review.*(?:入れません|使わない|自動起動しない|generic)",
        r"companion レーン.*(?:入れません|使わない)",
        r"generic.*gdd-implementation-gating",
    ),
    "gdd-security-reviewer に言及がある": any_rule(
        r"gdd-security-reviewer"
    ),
    "Route / Ownership Matrix と diff の一致確認に言及がある": all_rule(
        r"Route / Ownership Matrix",
        r"diff",
        r"一致",
    ),
    "Sensitive Data / Masking Policy と diff の一致確認に言及がある": all_rule(
        r"Sensitive Data / Masking Policy",
        r"diff",
        r"一致",
    ),
    "rollout / rollback の実装漏れ確認に言及がある": all_rule(
        r"rollout|flag",
        r"rollback",
        r"実装漏れ|漏れ",
    ),
    "gdd-completion-check で証跡不足やテストギャップを blocking と説明している": all_rule(
        r"gdd-completion-check",
        r"証跡|evidence",
        r"テストギャップ|testing gap|検証不足",
        r"blocking|done に進めない|差し戻し|gdd-systematic-debugging",
    ),
    "復旧手順または `次の1アクション` に言及がある": any_rule(
        r"復旧手順",
        r"次の1アクション",
        r"チェックリスト",
    ),
    "worktree を準備することに言及がある": any_rule(
        r"worktree",
        r"gdd-using-git-worktrees",
        r"専用.?worktree",
        r"dedicated branch.?/worktree",
    ),
    "どの steering を再開するか明示指定を要求している": any_rule(
        r"どの steering.*再開",
        r"どれを再開",
        r"明示指定",
        r"明示.*必要",
        r"指定してください",
        r"選んでもらう",
    ),
    "公式ドキュメント または release notes または migration guide の再確認に言及がある": all_rule(
        r"公式|release notes|migration guide|アップグレードガイド|リリースノート|prisma\.io/docs|nextjs\.org/docs",
        r"再確認|再チェック|最新情報",
    ),
    "公式ドキュメント または release notes または migration guide の確認に言及がある": any_rule(
        r"公式ドキュメント",
        r"release notes",
        r"migration guide",
        r"アップグレードガイド",
        r"リリースノート",
        r"公式.*guide",
        r"prisma\.io/docs",
        r"nextjs\.org/docs",
    ),
    "gdd-systematic-debugging に言及がある": any_rule(
        r"gdd-systematic-debugging"
    ),
    "勝手に 1 つ選ばない": any_rule(
        r"勝手に.*選ばない",
        r"推測で.*選ばない",
        r"決め打ち.*避ける",
    ),
    "新しい steering を作らないことに言及がある": any_rule(
        r"新規 steering.*(?:作らない|作りません)",
        r"新しい steering.*(?:作らない|作りません)",
        r"新規の `?\.steering/.+?`? は作らない",
        r"新規の \.steering/.+? は作らない",
        r"新規 steering を勝手に作らない",
        r"新規タスク扱いに逃げない",
        r"新しい `?\.steering/.+?`?.*(?:作って.*吸収しません|作って.*吸収しない|作らない)",
        r"新しい steering.*(?:吸収しません|吸収しない)",
        r"新しい steering / `?\.steering/.+?`?.*(?:吸収しません|吸収しない)",
    ),
    "新しい steering を作り直さない": any_rule(
        r"新しい steering.*(?:作らない|作り直さない)",
        r"新規.*steering.*(?:作らない|作り直さない)",
        r"作り直さない",
    ),
    "新しい worktree または `.steering/...` を作ることに言及がある": any_rule(
        r"新しい.*worktree",
        r"新規.*worktree",
        r"専用.*worktree",
        r"dedicated branch.?/worktree",
        r"\.steering",
    ),
    "既存 steering を resume しないことに言及がある": any_rule(
        r"既存.*steering.*resume\s*しない",
        r"既存.*steering.*resume 対象にしない",
        r"勝手に.*再開.*吸い込まない",
        r"勝手に resume 対象にしない",
        r"既存.*再開しない",
        r"自動的に.*再開.?\(resume\).*しません",
        r"resume に吸い込まない",
        r"resume 対象にしない",
        r"合流させません",
    ),
    "衝突解消前は `/gdd-dev` を続行しないことに言及がある": any_rule(
        r"衝突解消前.*?/gdd-dev.*?(?:続行しない|続けない)",
        r"/gdd-dev.*(?:続行しない|続けない)",
        r"衝突を解消してから.*再実行",
    ),
    "目的 / スコープ / 受入条件 の言葉に置き換えることに言及がある": all_rule(
        r"目的",
        r"スコープ",
        r"受入条件",
        r"置き換|言い換|整理",
    ),
    "独立した必須 `Examples` セクションを要求しないことに言及がある": any_rule(
        r"Examples.*(?:独立.*必須.*(?:にしない|不要)|独立必須セクション.*(?:にしない|不要)|増やさない)",
        r"独立(?:した)?必須 `?Examples`? セクション.*(?:にしない|不要)",
        r"`?Examples`?.*(?:独立必須セクションにせず|独立必須にせず|独立させない)",
        r"独立セクション.*(?:増やさない|増やさず|増やしません).*(?:受入条件|検証ヒント)",
    ),
    "`受入条件` または `検証ヒント` に入力 / 出力 / 期待挙動 の代表例を書くことに言及がある": all_rule(
        r"受入条件|検証ヒント",
        r"入力|入出力",
        r"出力|入出力",
        r"期待挙動|代表例|例として",
    ),
    "承認ポイントに背景を含めることに言及がある": any_rule(
        r"承認ポイント.*背景",
        r"背景.*(?:なぜ|理由|必要)",
    ),
    "承認ポイントに変更前→変更後を含めることに言及がある": any_rule(
        r"変更前.*変更後",
        r"before.*after",
        r"何が.*変わるか",
    ),
    "承認ポイントに方向性承認を含めることに言及がある": any_rule(
        r"方向性承認|方向性.*承認",
        r"自走範囲.*合意|合意.*自走範囲",
        r"Approved\s*Direction.*承認",
    ),
    "Approved Direction に言及がある": any_rule(
        r"Approved\s*Direction",
        r"方向性承認",
    ),
    "Approved Direction を state.md に記録することに言及がある": any_rule(
        r"state\.md.*Approved\s*Direction",
        r"Approved\s*Direction.*state\.md",
        r"state\.md.*方向性",
    ),
    "Approved Direction に自走範囲を含めることに言及がある": any_rule(
        r"自走範囲",
        r"自走.*(?:条件|範囲|判断)",
        r"AI.*自律.*判断",
    ),
    "Approved Direction は routing source にしないことに言及がある": any_rule(
        r"routing\s*source.*(?:にはしない|ではない|にしない)",
        r"補助.*コンテキスト",
        r"routing.*(?:使わない|にしない)",
    ),
    "E2E Discovery Loop に言及がある": any_rule(
        r"E2E\s*Discovery\s*Loop",
        r"E2E.*発見.*ループ",
        r"E2E.*自走",
    ),
    "Approved Direction の自走範囲に言及がある": any_rule(
        r"Approved\s*Direction.*自走",
        r"自走範囲.*(?:内|矛盾|超)",
        r"方向性.*(?:範囲内|矛盾しない)",
    ),
    "E2E Discovery Loop の自走条件に言及がある": all_rule(
        r"AC.*壊さない|AC.*変わらない|AC.*追加.*削除",
        r"セキュリティ.*新規|security.*新規",
    ),
    "design_detail_only で human check に戻さないことに言及がある": any_rule(
        r"design_detail_only.*human\s*check.*(?:戻さ|戻ら|スキップ|不要)",
        r"human\s*check.*(?:戻さ|戻ら|不要).*design_detail_only",
        r"reviewer.*通す.*human\s*check.*戻さ",
    ),
    "Scope Drift Guard に言及がある": any_rule(
        r"Scope\s*Drift\s*Guard",
        r"スコープ.*ドリフト",
    ),
    "Scope Drift Guard の 3 回閾値に言及がある": any_rule(
        r"design_detail_only.*3\s*回",
        r"3\s*回.*(?:超え|を超|超過)",
    ),
    "Scope Drift Guard は即座に human check ではないことに言及がある": any_rule(
        r"即座.*human\s*check.*(?:ではない|ではなく)",
        r"方向性.*矛盾.*(?:なければ|ない場合).*継続",
        r"自走.*継続.*(?:してよい|できる)",
    ),
    "Scope Drift Guard で worklog が必要だと言及がある": any_rule(
        r"worklog.*(?:累積|要約|書き)",
        r"累積.*変更.*(?:要約|worklog)",
    ),
    "セキュリティ新規発生で E2E 自走が中断されることに言及がある": any_rule(
        r"セキュリティ.*(?:新規|発生).*(?:自走.*(?:でき|条件.*満た)|human)",
        r"security.*(?:break|中断|stop|戻す)",
    ),
    "セキュリティ新規発生で human_recheck_required になることに言及がある": any_rule(
        r"セキュリティ.*human_recheck",
        r"human_recheck.*セキュリティ",
        r"セキュリティ.*人間.*(?:判断|戻す|確認)",
    ),
    "Problem Discovery に言及がある": any_rule(
        r"Problem\s*Discovery",
        r"問題発見",
        r"既存.*(?:コード|環境).*(?:具体的|事実|確認)",
    ),
    "Options Exploration に言及がある": any_rule(
        r"Options\s*Exploration",
        r"候補案.*(?:比較|探索)",
        r"選択肢.*(?:比較|探索|検討)",
    ),
    "Problem Discovery で既存コードを確認することに言及がある": any_rule(
        r"既存.*(?:コード|ファイル|構造|テスト).*確認",
        r"(?:コード|環境).*(?:具体的|事実)",
        r"ファイル構造|依存関係|CI.*設定",
    ),
    "Options Exploration で候補案を比較することに言及がある": any_rule(
        r"候補案.*比較",
        r"(?:比較|検討).*(?:案|候補|選択肢)",
        r"採用案.*代替案",
    ),
    # --- gdd-model-routing ---
    "重い処理に重いモデルを使うことに言及がある": any_rule(
        r"(?:Opus|重い(?:モデル|側)).*(?:要件|計画|レビュー|判断)",
        r"(?:要件|計画|レビュー|最終判断).*(?:Opus|重い(?:モデル|側))",
        r"曖昧.*(?:重い|Opus)",
    ),
    "軽い処理に軽いモデルを使うことに言及がある": any_rule(
        r"(?:Sonnet|軽い(?:モデル|側)).*(?:情報収集|ログ|テスト失敗|debug.?pack)",
        r"(?:情報収集|ログ取得|テスト失敗).*(?:Sonnet|軽い)",
        r"判断.*軽.*(?:Sonnet|軽い(?:モデル|側))",
    ),
    "起動時の固定表に言及がある": any_rule(
        r"固定表",
        r"(?:起動時|デフォルト).*(?:モデル|tier)",
        r"(?:Opus|Sonnet).*(?:effort|固定)",
    ),
    "Cursor 環境でデバッグ計画の high escalation に言及がある": any_rule(
        r"GPT-5\.5.*(?:low|標準).*(?:high|escalation|上げる)",
        r"(?:undocumented|large working-set|security-sensitive|final review).*(?:high|上げる)",
        r"xhigh.*(?:使わない|不使用)",
    ),
    "Cursor 環境の cursor.md を参照することに言及がある": any_rule(
        r"cursor\.md",
        r"Cursor.*(?:環境|モデル).*参照",
    ),
    # --- gdd-pr-review ---
    "Terraform をコードレビューとして扱うことに言及がある": any_rule(
        r"Terraform.*コード(?:レビュー|として)",
        r"Terraform.*(?:重い|Opus|コード扱い)",
    ),
    "コード PR に重いモデルを使うことに言及がある": any_rule(
        r"(?:コード|Terraform|混在).*(?:重い(?:モデル)?|Opus)",
        r"docs.?only.*(?:でない|ではない).*(?:重い|Opus)",
    ),
    "findings-first でレビューすることに言及がある": any_rule(
        r"findings.?first",
        r"重要度順.*指摘",
        r"指摘.*(?:重要度|severity).*順",
    ),
    # --- gdd-receiving-code-review ---
    "findings を検証してから修正することに言及がある": any_rule(
        r"(?:findings|指摘).*(?:検証|verify|確認).*(?:修正|fix)",
        r"(?:検証|verify).*(?:findings|指摘)",
        r"validate.*findings",
    ),
    "レビューコメントを盲目的に受け入れないことに言及がある": any_rule(
        r"(?:盲目的|blindly).*(?:受け入れ|accept).*(?:ない|not)",
        r"(?:受け入れ|accept).*(?:ない|not).*(?:盲目|blind)",
        r"鵜呑み.*(?:し|せ)ない",
    ),
    "valid な issue を適切に routing することに言及がある": any_rule(
        r"(?:valid|有効).*(?:issue|指摘).*(?:routing|route|振り分け)",
        r"debugging.*design.?gating",
        r"(?:routing|route).*(?:debugging|design)",
    ),
    # --- gdd-refactor-planning ---
    "挙動を変えないリファクタであることに言及がある": any_rule(
        r"挙動.*変え(?:ない|ず)",
        r"behavior.?preserving",
        r"(?:リファクタ|refactor).*(?:挙動|behavior).*(?:変え|preserv)",
    ),
    "挙動変更にはこの skill を使わないことに言及がある": any_rule(
        r"(?:user.?visible|挙動.*変わる).*(?:使わない|ではない|でない|gated.?dev|brainstorming)",
        r"(?:AC|requirements|acceptance).*(?:動かす|変える).*(?:使わない|ではない|gated.?dev)",
        r"(?:機能追加|要件変更).*(?:担当しない|ではない|gated.?dev)",
    ),
    "リファクタ後に実装レーンに戻ることに言及がある": any_rule(
        r"実装.*(?:レーン|lane).*戻",
        r"(?:実装|implementation).*(?:戻す|戻る|返す)",
        r"通常.*(?:実装|implementation).*(?:レーン|lane)",
    ),
    # --- gdd-status ---
    "state.md を読むことに言及がある": any_rule(
        r"state\.md.*読",
        r"読.*state\.md",
        r"Gate\s*Status.*(?:読|確認|表示)",
    ),
    "Gate Status を表示することに言及がある": any_rule(
        r"Gate\s*Status",
        r"Resume\s*From.*(?:表示|確認|見せ)",
        r"review\s*status.*(?:表示|一覧)",
    ),
    "次のアクションを表示することに言及がある": any_rule(
        r"Next\s*Action.*(?:表示|確認|見せ)",
        r"次.*(?:すべき|アクション|action).*(?:表示|明確)",
        r"(?:表示|見せ).*(?:次|next).*(?:action|アクション|すべき)",
    ),
    "task sizing の判定基準に言及がある": any_rule(
        r"(?:trivial|quick|standard).*(?:判定|判断|分類|基準|条件)",
        r"(?:task|タスク).*(?:size|sizing|サイズ).*(?:判定|判断|分類|基準|条件)",
        r"(?:判定|判断|分類|基準|条件).*(?:trivial|quick|standard)",
    ),
    "trivial はゲートをスキップすることに言及がある": any_rule(
        r"trivial.*(?:skip|スキップ|省略|不要|gate|ゲート)",
        r"(?:typo|タイポ|コメント|1.?行).*(?:skip|スキップ|省略|不要|gate|ゲート)",
    ),
    "quick と standard の違いに言及がある": any_rule(
        r"quick.*(?:standard|違い|差|reviewer|security)",
        r"standard.*(?:quick|違い|差|reviewer|security)",
        r"(?:quick|standard).*(?:ファイル|file|数|scope)",
    ),
    "task sizing で reviewer 数が変わることに言及がある": any_rule(
        r"(?:task|タスク).*(?:size|sizing|サイズ).*(?:reviewer|レビュー)",
        r"(?:quick|standard).*(?:reviewer|レビュー|security)",
        r"(?:reviewer|レビュー).*(?:quick|standard|省略|減)",
    ),
    "task sizing は upgrade のみで downgrade しないことに言及がある": any_rule(
        r"(?:upgrade|昇格|引き上げ).*(?:downgrade|降格|引き下げ|しない|不可)",
        r"(?:trivial|quick).*(?:standard|昇格|upgrade)",
        r"(?:downgrade|降格).*(?:しない|不可|禁止)",
    ),
    "human check で現在地と残作業を表示することに言及がある": all_rule(
        r"現在地",
        r"ここまで出来ていること",
        r"人間が今やること",
        r"OK 後に残る作業|OK後に残る作業",
        r"残タスク",
    ),
    "HITL で完了条件の変換とテスト化確認を露出することに言及がある": all_rule(
        r"Completion Condition Trace|完了条件の変換|完了条件",
        r"テスト化確認|Testable claim|Completion Testability Matrix",
        r"承認ポイント|HITL|human check",
    ),
    "HITL で技術スタック確認を露出することに言及がある": all_rule(
        r"Technology Stack Fit Matrix",
        r"Adopted Technology Stack Trace",
        r"技術スタック確認",
        r"access method|credential backend|tenant|公式統合",
    ),
    "Codex compact 503 を resume cue として扱うことに言及がある": all_rule(
        r"Codex compact 503|responses/compact|Error running remote compact task",
        r"host-level interruption|host 側|workflow failure ではない",
        r"参照した正本|現在 phase|次の1アクション",
    ),
}

EXPECTATION_RULE_LABELS: dict[str, str] = {
    "active_steering_not_unique": "active steering を一意に決められないことに言及がある",
    "active_worktree_design_md_canonical": "active worktree 側 `state.md` を正本として扱うことに言及がある",
    "active_worktree_tasklist_md_canonical": "active worktree 側 `tasklist.md` を正本として扱うことに言及がある",
    "adr_md_absence_not_blocking": "adr.md が無くても止めないことに言及がある",
    "adr_md_not_canonical_or_routing": "adr.md が canonical artifact や routing source ではないことに言及がある",
    "adr_md_optional": "adr.md が optional だと説明している",
    "adr_md_record_template_fields": "adr.md に Context / Decision / Why / Consequences を残すことに言及がある",
    "canonical_artifacts_switch_to_worktree": "canonical artifact を worktree 側へ切り替えることに言及がある",
    "changes_requested_self_remediation": "`changes_requested` 後も自律 remediation すると説明している",
    "completion_check_evidence_or_test_gap_blocking": "gdd-completion-check で証跡不足やテストギャップを blocking と説明している",
    "confirm_new_vs_resume": "`新規開始` か `再開` かの確認を要求している",
    "cursor_links_install_script_or_tsv": "cursor-links.tsv または install-cursor-links.sh に言及がある",
    "debug_pack_evidence_hypothesis_confidence": "`Evidence` と `Root Cause Hypothesis` と `Confidence` に言及がある",
    "debug_pack_includes_current_task_and_failure_command": "`Current Task` と `Failure Command` を含めることに言及がある",
    "debug_pack_reproduction_and_failure_surface": "再現条件と `Failure Surface` を含めることに言及がある",
    "debug_pack_separates_expected_and_actual": "`Expected` と `Actual` を分けることに言及がある",
    "debug_pack_workaround_vs_fix_plan": "`Workaround` と `Fix Plan` を分けることに言及がある",
    "debug_pack_worklog_decision_with_reason": "`Worklog Decision` と理由を含めることに言及がある",
    "design_gating_applicable_reviewer_selection": "gdd-design-gating の applicable reviewer selection に言及がある",
    "design_md_lightweight_skeleton_or_gate_status": "design.md に lightweight design skeleton、state.md に Gate Status が含まれる",
    "distinct_duplicate_asset_only_as_conflict": "別実体の同名 asset だけを衝突扱いすることに言及がある",
    "entry_intent_ambiguous": "entry intent が `ambiguous` だと説明している",
    "entry_intent_new": "entry intent を `new` と判断することに言及がある",
    "entry_intent_resume": "entry intent を `resume` と判断することに言及がある",
    "explicit_steering_resume_choice_required": "どの steering を再開するか明示指定を要求している",
    "fail_closed_or_blocked_from_done": "fail-closed または done に進めないことに言及がある",
    "formal_next_action_review_status_unchanged": "formal な `Next Action` / `Review Status` は変えないことに言及がある",
    "git_or_worktree_capability_missing": "git または worktree capability 不足に言及がある",
    "handoff_to_systematic_debugging_lite": "`gdd-systematic-debugging` に handoff すると説明している",
    "human_check_approved_prerequisite_for_design_gating": "`Human Check Status=approved` が `gdd-design-gating` の前提だと説明している",
    "human_check_is_prerequisite_stage": "human check の前段であることに言及がある",
    "human_check_not_redone": "human check を取り直さないことに言及がある",
    "human_check_redo_mentioned": "human check の再実施に言及がある",
    "human_check_required_gate": "human check が必須 gate であることに言及がある",
    "human_check_status_allowed_values": "`Human Check Status` の許容値 `pending` / `changes_requested` / `approved` に言及がある",
    "human_check_status_no_waived": "Human Check Status に waived を使わないと説明している",
    "human_check_current_location": "human check で現在地と残作業を表示することに言及がある",
    "hitl_completion_trace_visible": "HITL で完了条件の変換とテスト化確認を露出することに言及がある",
    "hitl_technology_stack_visible": "HITL で技術スタック確認を露出することに言及がある",
    "codex_compact_503_resume_cue": "Codex compact 503 を resume cue として扱うことに言及がある",
    "implementation_gating_applicable_reviewer_selection": "gdd-implementation-gating の applicable reviewer selection に言及がある",
    "implementation_gate_evidence_stays_in_build_loop": "Implementation Gate Evidence の不足を build loop 内で扱うことに言及がある",
    "implementation_gating_medium_not_waived": "gdd-implementation-gating で medium 指摘を waived で流さないと説明している",
    "implementation_reviewer_selection_recorded": "Implementation Reviewer Selection 記録に言及がある",
    "legacy_root_or_migration": "legacy root candidate または migration に言及がある",
    "lightweight_skeleton_or_detailed_design_gate": "lightweight design skeleton または detailed design gate に言及がある",
    "mentions_completion_check": "gdd-completion-check に言及がある",
    "mentions_behavior_change_summary": "Behavior Change Summary に言及がある",
    "mentions_design_detail_only": "design_detail_only に言及がある",
    "mentions_design_gating": "gdd-design-gating に言及がある",
    "mentions_fail_closed": "fail-closed に言及がある",
    "mentions_human_approval_items": "`承認ポイント` に言及がある",
    "mentions_human_check_questions": "Human Check Questions に言及がある",
    "mentions_human_check_waiting": "human-check-waiting に言及がある",
    "mentions_human_recheck_or_planning_rework": "human_recheck_required または planning_rework_required に言及がある",
    "mentions_human_recheck_required": "human_recheck_required に言及がある",
    "mentions_implementation_gating": "gdd-implementation-gating に言及がある",
    "mentions_latest_tech_context": "Latest Tech Context に言及がある",
    "mentions_latest_tech_context_or_external_refs": "Latest Tech Context または External References に言及がある",
    "mentions_open_questions": "Open Questions に落とすことに言及がある",
    "mentions_route_ownership_matrix": "Route / Ownership Matrix に言及がある",
    "mentions_plan_brainstorming": "gdd-brainstorming に言及がある",
    "mentions_planning_rework_required": "planning_rework_required に言及がある",
    "mentions_pre_workflow_brainstorming": "gdd-pre-workflow-brainstorming に言及がある",
    "mentions_requirements_gating": "gdd-requirements-gating に言及がある",
    "mentions_requirements_review_status": "Requirements Review Status に言及がある",
    "mentions_sensitive_data_masking_policy": "Sensitive Data / Masking Policy に言及がある",
    "mentions_subagent_driven_implementation_lite": "gdd-subagent-driven-implementation に言及がある",
    "mentions_security_evidence_code": "security_evidence:code に言及がある",
    "mentions_security_evidence_sca": "security_evidence:sca に言及がある",
    "mentions_systematic_debugging_lite": "gdd-systematic-debugging に言及がある",
    "mentions_task_breakdown": "gdd-task-breakdown に言及がある",
    "mentions_test_driven_development_lite": "gdd-test-driven-development に言及がある",
    "mentions_test_failure_debug_pack": "`gdd-test-failure-debug-pack` に言及がある",
    "mentions_using_git_worktrees_lite": "gdd-using-git-worktrees に言及がある",
    "mentions_workflow_comprehensive_reviewer": "gdd-completion-reviewer に言及がある",
    "mentions_workflow_design_feasibility_reviewer": "gdd-planning-reviewer に言及がある",
    "mentions_workflow_design_security_reviewer": "gdd-security-reviewer に言及がある",
    "mentions_workflow_design_reviewer": "gdd-planning-reviewer に言及がある",
    "mentions_gdd_stop_marker": "`gdd-stop` marker に言及がある",
    "mentions_workflow_requesting_code_review": "gdd-requesting-code-review に言及がある",
    "mentions_workflow_requirements_reviewer": "gdd-planning-reviewer に言及がある",
    "mentions_workflow_requirements_feasibility_reviewer": "gdd-planning-reviewer に言及がある",
    "mentions_workflow_requirements_security_reviewer": "gdd-security-reviewer に言及がある",
    "mentions_workflow_security_reviewer": "gdd-security-reviewer に言及がある",
    "mentions_worktree_preparation": "worktree を準備することに言及がある",
    "mentions_both_security_evidence_code_and_sca": "security_evidence:code と security_evidence:sca に言及がある",
    "new_worktree_or_steering_created": "新しい worktree または `.steering/...` を作ることに言及がある",
    "next_action_stays_completion_check": "`Next Action=gdd-completion-check` のままにすることに言及がある",
    "next_action_test_driven_development_lite": "Next Action=gdd-test-driven-development に言及がある",
    "next_action_update_delegated_to_systematic_debugging": "`Next Action` 更新は `gdd-systematic-debugging` に委譲すると説明している",
    "next_single_action_guidance": "`次の1アクション` に相当する案内がある",
    "no_create_new_steering": "新しい steering を作らないことに言及がある",
    "no_generic_route_to_requesting_code_review": "gdd-requesting-code-review を generic request では使わないことに言及がある",
    "no_misroute_to_systematic_debugging_lite": "`gdd-systematic-debugging` に誤送しないことに言及がある",
    "no_rebuild_new_steering": "新しい steering を作り直さない",
    "no_restart_from_plan_brainstorming": "gdd-brainstorming の新規作成から入り直さない",
    "no_resume_existing_steering": "既存 steering を resume しないことに言及がある",
    "no_steering_or_cursor_plans_artifacts": ".steering または `.cursor/plans` を作らないことに言及がある",
    "no_gdd_handoff_yet": "/gdd-dev にまだ handoff しないことに言及がある",
    "no_gdd_until_conflict_resolved": "衝突解消前は `/gdd-dev` を続行しないことに言及がある",
    "non_terminal_no_summary_only_stop": "非終端 state では status summary だけで止まらないと説明している",
    "official_docs_or_release_notes_check": "公式ドキュメント または release notes または migration guide の確認に言及がある",
    "official_docs_or_release_notes_recheck": "公式ドキュメント または release notes または migration guide の再確認に言及がある",
    "ops_blocking_or_ops_impact_medium": "`ops-blocking medium` または実運用影響 medium に言及がある",
    "plugin_managed_cursor_symlink_not_conflict": "plugin-managed Cursor symlink は衝突に含めないことに言及がある",
    "post_human_check_autonomous_phases": "human check 承認後は追加の人間承認なしで自走すると説明している",
    "priority_high_over_medium": "`High` を `Medium` より優先すると説明している",
    "procedural_repetition_not_human_recheck": "procedural / evidence 反復では human recheck に戻さないことに言及がある",
    "recovery_steps_or_next_single_action": "復旧手順または `次の1アクション` に言及がある",
    "reframes_vague_request_into_goal_scope_acceptance": "目的 / スコープ / 受入条件 の言葉に置き換えることに言及がある",
    "requirements_gating_applicable_reviewer_selection": "gdd-requirements-gating の applicable reviewer selection に言及がある",
    "requirements_md_includes_implementation_policy": "requirements.md に実装方針が含まれる",
    "return_routing_to_design_gating": "gdd-design-gating に戻すことに言及がある",
    "resume_candidates_or_selection_guidance": "候補一覧または選び方に言及がある",
    "reviewer_selection_record_mentioned": "Reviewer Selection 記録に言及がある",
    "reviewer_status_initialized_pending": "reviewer status を pending で初期化することに言及がある",
    "rollback_to_human_check_waiting": "human-check-waiting への差し戻しが説明されている",
    "no_mandatory_examples_section": "独立した必須 `Examples` セクションを要求しないことに言及がある",
    "acceptance_or_verification_hints_with_io_examples": "`受入条件` または `検証ヒント` に入力 / 出力 / 期待挙動 の代表例を書くことに言及がある",
    "same_name_ambient_asset_or_conflict": "same-name ambient asset または衝突に言及がある",
    "security_evidence_not_replaced_by_companion_review": "required external security evidence の代替ではないことに言及がある",
    "external_security_evidence_contract": "external verifier hook または security_evidence に言及がある",
    "stop_blind_implementation_fix_only_loops": "`implementation_fix_only` の盲目的反復を止めることに言及がある",
    "task_breakdown_executes_tasklist_update": "`gdd-task-breakdown` を実行して `tasklist.md` を更新すると説明している",
    "task_level_review_gaps_before_done": "task 単位 review の取りこぼしを done 前に確認することに言及がある",
    "tasklist_task_sections_mentioned": "Current Task / Pending Tasks / Completed Tasks に言及がある",
    "blocks_human_check_on_open_questions": "blocking Open Questions なら human-check-waiting に進めないと説明している",
    "comprehensive_checks_route_matrix_vs_diff": "Route / Ownership Matrix と diff の一致確認に言及がある",
    "comprehensive_checks_masking_policy_vs_diff": "Sensitive Data / Masking Policy と diff の一致確認に言及がある",
    "comprehensive_checks_rollout_rollback_gaps": "rollout / rollback の実装漏れ確認に言及がある",
    "unsupported_or_nondeterministic_resolution": "unsupported configuration または deterministic に解決できないことに言及がある",
    "verification_schema_fields_required": "Verification に `method` / `status` / `evidence` / `notes` が必要だと説明している",
    "gdd_stop_reason_blocked": "`reason=\"blocked\"` に言及がある",
    "workflow_spec_reviewer_required_trigger": "gdd-implementation-reviewer が契約変更で必須だと説明している",
    "worklog_root_cause_and_route_decision": "`worklog.md` に根本原因と route 判断を書くことに言及がある",
    "worklog_update_decision_on_recurrence": "再発時に `worklog.md` 更新可否を判断すると説明している",
    "approval_point_has_background": "承認ポイントに背景を含めることに言及がある",
    "approval_point_has_before_after": "承認ポイントに変更前→変更後を含めることに言及がある",
    "approval_point_has_direction_approval": "承認ポイントに方向性承認を含めることに言及がある",
    "mentions_approved_direction": "Approved Direction に言及がある",
    "approved_direction_in_state_md": "Approved Direction を state.md に記録することに言及がある",
    "approved_direction_has_scope": "Approved Direction に自走範囲を含めることに言及がある",
    "approved_direction_not_routing_source": "Approved Direction は routing source にしないことに言及がある",
    "mentions_e2e_discovery_loop": "E2E Discovery Loop に言及がある",
    "mentions_approved_direction_scope": "Approved Direction の自走範囲に言及がある",
    "e2e_self_run_conditions": "E2E Discovery Loop の自走条件に言及がある",
    "design_detail_only_without_human_check": "design_detail_only で human check に戻さないことに言及がある",
    "mentions_scope_drift_guard": "Scope Drift Guard に言及がある",
    "scope_drift_guard_threshold_3": "Scope Drift Guard の 3 回閾値に言及がある",
    "scope_drift_guard_not_immediate_human_check": "Scope Drift Guard は即座に human check ではないことに言及がある",
    "scope_drift_guard_worklog_required": "Scope Drift Guard で worklog が必要だと言及がある",
    "e2e_security_breaks_self_run": "セキュリティ新規発生で E2E 自走が中断されることに言及がある",
    "human_recheck_required_for_security": "セキュリティ新規発生で human_recheck_required になることに言及がある",
    "mentions_problem_discovery": "Problem Discovery に言及がある",
    "mentions_options_exploration": "Options Exploration に言及がある",
    "problem_discovery_checks_existing_code": "Problem Discovery で既存コードを確認することに言及がある",
    "options_exploration_compares_candidates": "Options Exploration で候補案を比較することに言及がある",
    "model_routing_heavy_for_planning": "重い処理に重いモデルを使うことに言及がある",
    "model_routing_light_for_info_gathering": "軽い処理に軽いモデルを使うことに言及がある",
    "model_routing_mentions_fixed_table": "起動時の固定表に言及がある",
    "model_routing_cursor_high_escalation_for_debugging": "Cursor 環境でデバッグ計画の high escalation に言及がある",
    "model_routing_mentions_cursor_md": "Cursor 環境の cursor.md を参照することに言及がある",
    "pr_review_terraform_as_code": "Terraform をコードレビューとして扱うことに言及がある",
    "pr_review_heavy_model_for_code": "コード PR に重いモデルを使うことに言及がある",
    "pr_review_findings_first": "findings-first でレビューすることに言及がある",
    "receiving_review_validates_findings": "findings を検証してから修正することに言及がある",
    "receiving_review_does_not_blindly_accept": "レビューコメントを盲目的に受け入れないことに言及がある",
    "receiving_review_routes_valid_issues": "valid な issue を適切に routing することに言及がある",
    "refactor_planning_behavior_preserving": "挙動を変えないリファクタであることに言及がある",
    "refactor_planning_not_for_behavior_change": "挙動変更にはこの skill を使わないことに言及がある",
    "refactor_planning_returns_to_impl_lane": "リファクタ後に実装レーンに戻ることに言及がある",
    "status_reads_state_md": "state.md を読むことに言及がある",
    "status_shows_gate_status": "Gate Status を表示することに言及がある",
    "status_shows_next_action": "次のアクションを表示することに言及がある",
    "task_sizing_criteria": "task sizing の判定基準に言及がある",
    "trivial_skips_gates": "trivial はゲートをスキップすることに言及がある",
    "quick_vs_standard_difference": "quick と standard の違いに言及がある",
    "task_sizing_affects_reviewer_count": "task sizing で reviewer 数が変わることに言及がある",
    "task_sizing_upgrade_only": "task sizing は upgrade のみで downgrade しないことに言及がある",
}

COMPILED_RULES_BY_LABEL: dict[str, CompiledRule] = {
    name: CompiledRule(
        mode=rule.mode,
        patterns=tuple(re.compile(pattern, FLAGS) for pattern in rule.patterns),
    )
    for name, rule in RULES.items()
}


def default_evals_path() -> Path:
    return Path(__file__).resolve().parent.parent / "evals" / "evals.json"


def default_workspace_root() -> Path:
    override = os.environ.get("GDD_EVALS_TRUSTED_ROOT")
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parent.parent.parent / "gate-driven-development-workspace"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def snippet(text: str, start: int, end: int) -> str:
    left = max(0, start - 120)
    right = min(len(text), end + 120)
    return compact(text[left:right])[:260]


def truncate_for_search(text: str) -> str:
    if len(text) <= MAX_SEARCH_TEXT_CHARS:
        return text
    return text[:MAX_SEARCH_TEXT_CHARS]


def search_pattern(text: str, pattern: re.Pattern[str]) -> str | None:
    limited_text = truncate_for_search(text)
    match = pattern.search(limited_text)
    if not match:
        return None
    return snippet(limited_text, match.start(), match.end())


def judge(text: str, rule: CompiledRule) -> tuple[bool, str]:
    if rule.mode == "any":
        for pattern in rule.patterns:
            evidence = search_pattern(text, pattern)
            if evidence is not None:
                return True, evidence
        return False, "No matching evidence found in final_response.md or transcript.md."

    evidences: list[str] = []
    for pattern in rule.patterns:
        evidence = search_pattern(text, pattern)
        if evidence is None:
            return False, "No matching evidence found in final_response.md or transcript.md."
        evidences.append(evidence)

    unique: list[str] = []
    for evidence in evidences:
        if evidence not in unique:
            unique.append(evidence)
    return True, " / ".join(unique)[:500]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def summarize_user_notes(notes_text: str) -> dict[str, list[str]]:
    if not notes_text.strip():
        return {"uncertainties": [], "needs_review": [], "workarounds": []}
    return {
        "uncertainties": [compact(notes_text)],
        "needs_review": [],
        "workarounds": [],
    }


def collect_output_chars(outputs_dir: Path) -> int:
    total = 0
    for path in sorted(outputs_dir.rglob("*")):
        if path.is_file():
            total += len(safe_text(path))
    return total


def load_execution_metrics(outputs_dir: Path, transcript_text: str) -> dict:
    metrics_path = outputs_dir / "metrics.json"
    default_metrics = {
        "tool_calls": {},
        "total_tool_calls": 0,
        "total_steps": 0,
        "errors_encountered": 0,
        "output_chars": collect_output_chars(outputs_dir),
        "transcript_chars": len(transcript_text),
    }
    if not metrics_path.exists():
        return default_metrics

    metrics = read_json(metrics_path)
    metrics.setdefault("tool_calls", {})
    metrics.setdefault("total_tool_calls", 0)
    metrics.setdefault("total_steps", 0)
    metrics.setdefault("errors_encountered", 0)
    metrics["output_chars"] = metrics.get("output_chars", collect_output_chars(outputs_dir))
    metrics["transcript_chars"] = metrics.get("transcript_chars", len(transcript_text))
    return metrics


def load_timing(run_dir: Path) -> dict:
    timing_path = run_dir / "timing.json"
    default_timing = {
        "executor_duration_seconds": 0.0,
        "grader_duration_seconds": 0.0,
        "total_duration_seconds": 0.0,
    }
    if not timing_path.exists():
        return default_timing

    timing = read_json(timing_path)
    return {
        "executor_duration_seconds": float(timing.get("executor_duration_seconds", 0.0)),
        "grader_duration_seconds": float(timing.get("grader_duration_seconds", 0.0)),
        "total_duration_seconds": float(timing.get("total_duration_seconds", 0.0)),
    }


def selected_evals(evals: list[dict], eval_ids: set[int] | None) -> Iterable[dict]:
    if not eval_ids:
        return evals
    return [ev for ev in evals if ev["id"] in eval_ids]


def eval_metadata(ev: dict) -> dict:
    return {
        "eval_id": ev["id"],
        "category": ev.get("category", DEFAULT_CATEGORY),
        "priority": ev.get("priority", DEFAULT_PRIORITY),
        "required": bool(ev.get("required", False)),
    }


def new_rollup() -> dict:
    return {
        "runs": 0,
        "passed_runs": 0,
        "failed_runs": 0,
        "passed_expectations": 0,
        "total_expectations": 0,
    }


def update_rollup(rollup: dict, passed: int, total: int, run_passed: bool) -> None:
    rollup["runs"] += 1
    rollup["passed_runs"] += int(run_passed)
    rollup["failed_runs"] += int(not run_passed)
    rollup["passed_expectations"] += passed
    rollup["total_expectations"] += total


def finalize_rollup(rollup: dict) -> dict:
    runs = rollup["runs"]
    total_expectations = rollup["total_expectations"]
    return {
        **rollup,
        "run_pass_rate": round(rollup["passed_runs"] / runs, 4) if runs else 0.0,
        "expectation_pass_rate": round(
            rollup["passed_expectations"] / total_expectations, 4
        )
        if total_expectations
        else 0.0,
    }


def ensure_rule_coverage(evals: list[dict]) -> None:
    used_expectation_ids = {
        expectation_id
        for ev in evals
        for expectation_id in ev["expectations"]
    }
    missing_ids = sorted(
        expectation_id
        for expectation_id in used_expectation_ids
        if expectation_id not in EXPECTATION_RULE_LABELS
    )
    if missing_ids:
        raise SystemExit(
            "Missing grading rule ids for expectations:\n" + "\n".join(missing_ids)
        )

    missing_rule_labels = sorted(
        f"{expectation_id}: {EXPECTATION_RULE_LABELS[expectation_id]}"
        for expectation_id in used_expectation_ids
        if EXPECTATION_RULE_LABELS[expectation_id] not in RULES
    )
    if missing_rule_labels:
        raise SystemExit(
            "Missing grading rule labels for expectation ids:\n"
            + "\n".join(missing_rule_labels)
        )


def ensure_trusted_workspace(path: Path) -> Path:
    resolved = path.resolve()
    trusted_root = default_workspace_root().resolve()
    if resolved == trusted_root or trusted_root in resolved.parents:
        return resolved
    raise SystemExit(f"Workspace must be inside {trusted_root}")


def grade_run(run_dir: Path, ev: dict) -> dict:
    outputs_dir = run_dir / "outputs"
    final_path = outputs_dir / "final_response.md"
    transcript_path = run_dir / "transcript.md"
    notes_path = outputs_dir / "user_notes.md"
    expectations = ev["expectations"]
    metadata = eval_metadata(ev)

    if not final_path.exists() or not transcript_path.exists():
        raise SystemExit(f"Missing required run outputs: {run_dir}")

    final_text = safe_text(final_path)
    transcript_text = safe_text(transcript_path)
    notes_text = safe_text(notes_path) if notes_path.exists() else ""
    combined = final_text + "\n\n" + transcript_text

    grading_expectations: list[dict] = []
    passed = 0
    for expectation_id in expectations:
        expectation_label = EXPECTATION_RULE_LABELS[expectation_id]
        ok, evidence = judge(
            combined, COMPILED_RULES_BY_LABEL[expectation_label]
        )
        grading_expectations.append(
            {
                "id": expectation_id,
                "label": expectation_label,
                "text": expectation_label,
                "passed": ok,
                "evidence": evidence,
            }
        )
        passed += int(ok)

    total = len(grading_expectations)
    run_passed = passed == total
    grading = {
        "expectations": grading_expectations,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "run_passed": run_passed,
        },
        "eval_metadata": metadata,
        "execution_metrics": load_execution_metrics(outputs_dir, transcript_text),
        "timing": load_timing(run_dir),
        "claims": [],
        "user_notes_summary": summarize_user_notes(notes_text),
        "eval_feedback": {
            "suggestions": [],
            "overall": "Regex-based grading completed",
        },
    }

    grading_path = run_dir / "grading.json"
    grading_path.write_text(
        json.dumps(grading, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "passed": passed,
        "total": total,
        "run_passed": run_passed,
        **metadata,
    }


def parse_eval_ids(raw_values: list[str]) -> set[int]:
    selected: set[int] = set()
    for raw in raw_values:
        for part in raw.split(","):
            part = part.strip()
            if part:
                selected.add(int(part))
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Grade gate-driven-development eval runs for an iteration workspace."
    )
    parser.add_argument(
        "workspace",
        type=Path,
        help="Iteration directory such as iteration-15-full-rerun-post-tightening",
    )
    parser.add_argument(
        "--evals-file",
        type=Path,
        default=default_evals_path(),
        help="Path to evals/evals.json (defaults to repo-local evals.json).",
    )
    parser.add_argument(
        "--eval-id",
        action="append",
        default=[],
        help="Optional eval id filter. Repeat or pass comma-separated values.",
    )
    parser.add_argument(
        "--present-only",
        action="store_true",
        help="Grade only eval directories that exist in the workspace.",
    )
    args = parser.parse_args()

    workspace = ensure_trusted_workspace(args.workspace)
    evals_file = args.evals_file.resolve()
    eval_ids = parse_eval_ids(args.eval_id)

    evals_data = read_json(evals_file)
    evals = list(selected_evals(evals_data["evals"], eval_ids))
    ensure_rule_coverage(evals)

    graded_runs = 0
    passed_expectations = 0
    total_expectations = 0
    category_rollups: dict[str, dict] = defaultdict(new_rollup)
    priority_rollups: dict[str, dict] = defaultdict(new_rollup)
    required_rollup = new_rollup()

    for ev in evals:
        eval_dir = workspace / f"eval-{ev['id']}"
        if not eval_dir.exists():
            if args.present_only:
                continue
            raise SystemExit(f"Missing eval directory: {eval_dir}")

        for config_dir in sorted(path for path in eval_dir.iterdir() if path.is_dir()):
            for run_dir in sorted(path for path in config_dir.iterdir() if path.is_dir()):
                result = grade_run(run_dir, ev)
                graded_runs += 1
                passed_expectations += result["passed"]
                total_expectations += result["total"]
                update_rollup(
                    category_rollups[result["category"]],
                    result["passed"],
                    result["total"],
                    result["run_passed"],
                )
                update_rollup(
                    priority_rollups[result["priority"]],
                    result["passed"],
                    result["total"],
                    result["run_passed"],
                )
                if result["required"]:
                    update_rollup(
                        required_rollup,
                        result["passed"],
                        result["total"],
                        result["run_passed"],
                    )

    if graded_runs == 0:
        raise SystemExit("No runs were graded. Check the workspace path or eval filters.")

    overall_rollup = finalize_rollup(
        {
            "runs": graded_runs,
            "passed_runs": sum(
                bucket["passed_runs"] for bucket in category_rollups.values()
            ),
            "failed_runs": sum(
                bucket["failed_runs"] for bucket in category_rollups.values()
            ),
            "passed_expectations": passed_expectations,
            "total_expectations": total_expectations,
        }
    )
    category_summary = {
        key: finalize_rollup(value) for key, value in sorted(category_rollups.items())
    }
    priority_summary = {
        key: finalize_rollup(value) for key, value in sorted(priority_rollups.items())
    }
    required_summary = finalize_rollup(required_rollup)
    summary = {
        "workspace": str(workspace),
        "overall": overall_rollup,
        "by_category": category_summary,
        "by_priority": priority_summary,
        "required_evals": required_summary,
    }
    summary_path = workspace / "grading-summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"graded {graded_runs} runs "
        f"({passed_expectations}/{total_expectations} expectations, "
        f"pass_rate={overall_rollup['expectation_pass_rate']}, "
        f"summary={summary_path.name})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
