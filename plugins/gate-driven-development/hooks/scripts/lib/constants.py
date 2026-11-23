from __future__ import annotations

import re

STOP_PATTERN = re.compile(r'<gdd-stop reason="([^"]+)">', re.DOTALL)
ALLOWED_STOP_REASONS = {
    "done",
    "cancelled",
    "human-check-waiting",
    "blocked",
    "clarification-needed",
    "external-review-waiting",
    "auth-waiting",
    "staging-verification-blocked",
}
# state.md と .claude/gdd-dev.local.md を残して止まる停止理由（pause）。ほかの停止は loop state を消す。
STATE_KEEPING_STOP_REASONS = frozenset({
    "human-check-waiting", "clarification-needed", "external-review-waiting", "auth-waiting",
})
GOAL_COMPLETE_REASONS = {"done"}
GOAL_INCOMPLETE_REASONS = {
    "blocked",
    "human-check-waiting",
    "clarification-needed",
    "cancelled",
    "external-review-waiting",
    "auth-waiting",
    "staging-verification-blocked",
}

# Bounded wake budget for auth-waiting pause (mirrors external-review poll-cap).
# Named/overridable so the auth-waiting ScheduleWakeup loop transitions to
# `blocked` at the cap instead of re-arming forever when no human re-login occurs.
AUTH_WAITING_MAX_WAKES = 12

# Bounded poll budget for the PR review follow-up loop (gdd-pr-review-followup).
# Mirrors AUTH_WAITING_MAX_WAKES: skill prose alone ("既定 12 回で blocked") was not
# enforced anywhere in the hook chain, so a stuck review-convergence loop could
# re-arm ScheduleWakeup indefinitely. This constant is the single source of truth
# for the cap; the stop hook reads `PR Review Follow-up Attempts` from state.md and
# forces reason=blocked once it reaches this value.
PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS = 12

# Design Review Checkpoint thresholds. Single source of truth for the
# gdd-pr-review-followup checkpoint; SKILL.md and references only point here.
# PR_REVIEW_ROUNDS_MAX counts review rounds (a new head sha reviewed), not polling
# wakes; the wake cap stays PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS above.
PR_REVIEW_ROUNDS_MAX = 5
PR_CHECKPOINT_ROUNDS_THRESHOLD = 3
PR_CHECKPOINT_SELF_INFLICTED_RATIO = 0.5
PR_CHECKPOINT_CLUSTER_REPEAT_ROUNDS = 2
PR_CHECKPOINT_REVIEW_COMMIT_RATIO = 2 / 3
HANDOFF_PATTERN = re.compile(
    r'<!-- Context Handoff:[^>]*-->\s*\n(\*\*Handoff:\*\*.*?)(?=\n\n|\n##|\n<!-- |\n<gdd-|\Z)',
    re.DOTALL,
)

# ---- merge gate（AC-2）: マージ承認語彙の唯一の正本 -------------------------
# design.md § 承認判定の設計 条件2: 正本は述語 is_merge_approval(text) ただ 1 つ。
# 素の MERGE_APPROVAL_RE を直接使う経路は作らない（呼び出し側は述語を通す）。
# ADR-14（transcript 解析の廃止）以降、**hook はこの述語を呼ばない**。実際の
# 消費者は skills/gdd-pr-review-followup/SKILL.md の手順に従う GDD main session
# （Merge Approval 行を書く際の語彙判定）と、リークテストを含む契約テストのみ。
#
# **入力域の契約**: この述語が判定するのは「マージ可否を尋ねた**閉じた確認への短い
# 返答**」であって、人間の任意の自由文ではない。承認は `PR #<n> / head <sha>` に
# 紐づく必要があり（hook が approval-sha-mismatch を検査する）、その 2 つを提示して
# いない時点の発話は、そもそもこの HEAD への承認になりえない。
#
# 自由文に対する極性判定は regex で閉じない。否定語の列挙で除外する方式は独立レビュー
# 3 巡で漏れ続け（`cannot merge it` は `\bnot\b` の境界が成立せず、日本語の条件節
# `〜たら` / `〜次第` / `明日` には対応が無い）、同時に正当な承認まで落とした
# （`Not bad, merge it` / `I checked before, merge it`）。列挙は増やしても収束しない。
# そのため本述語は全文アンカー（+ 肯定間投詞の任意前置）に固定し、否定語の列挙は
# 持たない。判定できない返答は False を返す。
#
# **呼び出し側の義務**: 確認の文面に「受理される返答形」を 1 つ示すこと
# （正本は下の `MERGE_APPROVAL_PHRASES`）。肯定間投詞は**前置としてのみ**成立する
# ため、`はい` / `yes` / `OK` 単独は承認にならない（実測）。返答形を示さずに
# 「判定できないので確認を取り直す」だけを繰り返すと、閉じた確認への最も自然な
# 返答が毎回 False になり、恒久 block が別の形で残る。
MERGE_APPROVAL_PHRASES = (
    "マージして",
    "マージしていい",
    "マージして良い",
    "マージお願い",
    "マージ実行",
    "merge して",
    "merge して良い",
    "merge it",
    "merge this",
)

# 承認返答に許す句読点。**1 箇所で定義する** —— 肯定間投詞の後ろと承認語彙の後ろで
# 別々に書いていたため、`。` が片方にだけ無く `はい、マージしてください` は通るのに
# `はい。マージしてください` が落ちていた（実測）。列挙を 2 つ持てば必ずずれる。
_MERGE_APPROVAL_PUNCTUATION = r"[\s!！.．,、。]"

# 承認語彙の直後に許すのは丁寧語・句読点だけ。任意の続きを許すと
# 「マージしてしまった」等の否定/完了/禁止接尾まで拾ってしまう。
_MERGE_APPROVAL_TRAILING_RE = r"(?:ください|お願いします|します)?" + _MERGE_APPROVAL_PUNCTUATION + r"*"

MERGE_APPROVAL_RE = re.compile(
    r"(?:" + "|".join(re.escape(p) for p in MERGE_APPROVAL_PHRASES) + r")"
    + _MERGE_APPROVAL_TRAILING_RE,
    re.IGNORECASE,
)

# 承認語彙の前に置いてよい肯定の間投詞・応答。ここだけを前置として許す。
# 「はい、マージしてください」「OK、マージして」「LGTM, merge it」を通し、
# 条件句・否定句を前置として通さないための、閉じた集合。
_MERGE_APPROVAL_AFFIRMATION_RE = (
    r"(?:はい|うん|ええ|了解|承認|ok|okay|yes|yep|lgtm|approve[d]?|sure)"
)

# 否定/完了/禁止の接尾（design.md 条件2の除外規律）。全文アンカーでも
# 「マージして」+ 接尾 の形は末尾許容文字に載らないため原理的に落ちるが、
# 語彙が増えたときの取りこぼしを防ぐ二重化として残す。
_MERGE_APPROVAL_NEGATION_SUFFIX_RE = re.compile(
    r"マージして(?:しまった|おいた|ある|はいけません|は駄目|ないよね)"
)

# merge gate の 3 既定値。人間向け正本は references/config-defaults.md § Merge Gate。
# 同期は契約テスト（tests/test_merge_gate_hook_contracts.py の md↔code 同期テスト）で担保する。
# env override は設けない（ADR-7）。
MERGE_GATE_REVIEW_WAIT_MINUTES = 40
MERGE_GATE_RECHECK_FRESHNESS_MINUTES = 10

# design.md § 既定値の正本: Approval Freshness は Review Wait より大きくなければ
# ならない（正規手順の待機がそのまま承認を失効させないため）。同期テストで
# 大小関係を assert する（config-defaults.md 同期テスト）。
MERGE_GATE_APPROVAL_FRESHNESS_MINUTES = 120

# 承認返答の全文アンカー。`<肯定間投詞>?<承認語彙><丁寧語・句読点>?` だけを受ける。
_MERGE_APPROVAL_REPLY_RE = re.compile(
    r"^(?:" + _MERGE_APPROVAL_AFFIRMATION_RE + _MERGE_APPROVAL_PUNCTUATION + r"*)?"
    + r"(?:" + "|".join(re.escape(p) for p in MERGE_APPROVAL_PHRASES) + r")"
    + _MERGE_APPROVAL_TRAILING_RE + r"$",
    re.IGNORECASE,
)


def is_merge_approval(text: str) -> bool:
    """AC-2 の承認述語。正本はこの関数のみ。

    判定対象は「マージ可否を尋ねた閉じた確認への短い返答」（入力域の契約は上記）。
    全文アンカー + 肯定間投詞の任意前置。否定語の列挙は持たない — 前置きを自由に
    すると極性の判定が必要になり、それは regex で閉じないため（実測は上記）。
    全角空白・半角カナ・全角英字の正規化は行わない（誤許可面を広げないため）。
    """
    if not text:
        return False
    stripped = text.strip()
    if not stripped:
        return False
    if _MERGE_APPROVAL_NEGATION_SUFFIX_RE.search(stripped):
        return False
    return _MERGE_APPROVAL_REPLY_RE.match(stripped) is not None


# Text-prefix fallback identifying a cross-session peer message when a host
# does not send a structured origin field (design.md § 受信側の機械的
# 境界 v2, defense-in-depth 2nd layer). `isMeta` alone is NOT used as a peer
# signal (PR #31 review): Claude Code sets `isMeta: true` on many host
# injections unrelated to peer messages (skill-invocation preambles, Stop
# hook feedback, `<local-command-caveat>`, `<system-reminder>`), so relying
# on it produced frequent false positives against real transcripts. A
# genuine peer message always carries `origin.kind=="peer"` together with
# this prefix (see the `PEER_RECORD` fixture in
# tests/test_peer_turn_write_boundary_contract.py), so dropping `isMeta`
# does not weaken detection. Included in _HOOK_INJECTION_PREFIXES
# below so parse_transcript() also excludes it from last_user_text (a peer
# message must never become "the user's" last text). But last_user_turn_is_peer()
# in lib/transcript.py checks this prefix BEFORE consulting
# _HOOK_INJECTION_PREFIXES and returns True (peer turn) on a match — it never
# falls through to the generic "skip and continue scanning" branch that the
# other entries in that tuple trigger. Dual-consumer, dual-meaning: same
# literal, "exclude from last_user_text" for one consumer and "this IS a peer
# turn" for the other.
_PEER_MESSAGE_TEXT_PREFIX = "Another Claude session sent a message:"

# GitHub の PR の URL（マージ後の確認の marker の pr_url と、transcript に PR の URL が初めて出た時刻の記録が読む）
PR_URL_RE = re.compile(r'https://github\.com/[^/\s]+/[^/\s]+/pull/\d+')

# turn の途中に届いて queue から出た入力（attachment の type: queued_command）は、host が
# attachment.origin.kind に出どころを書く。steering write guard（last_user_turn_is_peer の
# include_queued=True）は、この kind の行と origin の無い行（task-notification の古い版・
# ci-monitor-event）だけを peer でないとして読み飛ばし、ほかの kind（peer・未知の値・
# 読めない形）は peer として扱う。
_QUEUED_NON_PEER_ORIGIN_KINDS = frozenset({"human", "task-notification", "auto-continuation"})

# Background-agent completion notices are injected by the host as `type:"user"`
# text records (see tests/test_stop_hook_validate.py `_task_notification_user_turn`
# for the observed shape), or, when they arrive mid-turn, only as queued records
# (lib/transcript.py `_queued_body`; those never reach last_user_text, and
# last_user_turn_is_peer() reads them only for the steering write guard, by
# attachment.origin.kind). They are not human input, so they must neither become
# last_user_text nor clear the peer-turn state in last_user_turn_is_peer(): a
# background agent finishing right after a peer message would otherwise re-open
# the approval / cancellation write boundary without the human saying anything
# (PR #31 review Finding B). Matched as a prefix, like the other entries here,
# because the host emits the tag at the start of the record.
_TASK_NOTIFICATION_TEXT_PREFIX = "<task-notification>"

# Hook-injected continuation messages re-appear as user-role transcript entries.
# They are NOT real user input and must be skipped when judging whether the user
# wants to continue the GDD workflow. See _PEER_MESSAGE_TEXT_PREFIX above for the
# one entry whose skip-and-continue meaning does not apply to last_user_turn_is_peer().
_HOOK_INJECTION_PREFIXES = (
    "Continue the active `/gdd-dev` run.",
    "Stop hook feedback:",
    # GDD CLAUDE.md is injected as a user text block at session start. Its
    # "Merge Report Cleanup Trigger" section documents the keywords マージした /
    # mergeした / merged, which would otherwise match MANUAL_MERGE_RE and cause
    # a false-positive post-merge block (this was the root cause of one such block).
    "# Gate-Driven Development",
    _PEER_MESSAGE_TEXT_PREFIX,
    _TASK_NOTIFICATION_TEXT_PREFIX,
)

_GDD_SLASH_RE = re.compile(r'(?im)^\s*/gdd[\-_]')
_GDD_SKILL_REF_RE = re.compile(
    r'(?i)\bgdd[- ]?(?:dev|brainstorming|requirements[- ]?gating|'
    r'design[- ]?gating|task[- ]?breakdown|test[- ]?driven[- ]?development|'
    r'subagent[- ]?driven[- ]?implementation|implementation[- ]?gating|'
    r'completion[- ]?check|systematic[- ]?debugging|pr[- ]?review|status|metrics)\b'
)
_GDD_PHASE_MARKER_RE = re.compile(r'<gdd-phase>[^<]+</gdd-phase>')
_HUMAN_CHECK_PAUSE_RE = re.compile(
    r'<gdd-stop\s+reason="human-check-waiting"|🔍\s*確認をお願いします|承認ポイント'
)
_APPROVAL_REPLY_RE = re.compile(
    r'^(ok|approved?|承認|yes|はい|y|continue|go|進めて|続けて|done|👍|✅)'
    r'[\s!.。、]*$',
    re.IGNORECASE,
)
