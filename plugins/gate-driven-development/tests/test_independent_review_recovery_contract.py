"""`GDD_IR_RECOVERY_CORE` の必要 key 列挙が parser の実際の必須集合と一致することの契約。

`independent-review-*` の block reason は復旧要素 2（必要 key の全列挙）を持つが、
self-review 系の `GDD_SR_RECOVERY_CORE`（sha,rounds,consecutive_clean,dry,lanes）を
流用していたため、operator は `Independent Review` 行の書式を hook ソースからしか
復元できなかった（独立レビュー R3 #7）。

ここでは reason に載る key 一覧を **手書き literal の突き合わせにしない**。
`gdd_parse_merge_gate_field "Independent Review"` に valid な行を渡し、key を
1 つずつ落として invalid になるかを実測し、そこから導いた必須集合と定数の列挙を
比較する。定数だけを直したり parser だけを直したりするとこの test が落ちる。
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "merge-gate-evidence.sh"

# 全 key を備えた valid 行。sha は位置指定なので key 名を持たない。
_LINE_PARTS = {
    "sha": None,  # 先頭 segment
    "reviewer": "reviewer: opus-5",
    "context": "context: diff-only",
    "high": "high: 0",
    "medium": "medium: 0",
    "blocking": "blocking: 0",
    "at": "at: 2026-09-06T00:00:00Z",
}
_SHA = "0123456789abcdef0123456789abcdef01234567"


def _build_line(drop: str | None) -> str:
    segments = [] if drop == "sha" else [_SHA]
    for key, seg in _LINE_PARTS.items():
        if key == "sha" or key == drop:
            continue
        segments.append(seg)
    return " | ".join(segments)


def _parse(line: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state.md"
        state.write_text(f"## Gate Status\n- Independent Review: {line}\n", encoding="utf-8")
        script = (
            f'source "{LIB}"\n'
            f'gdd_parse_merge_gate_field "{state}" "Independent Review"\n'
            'printf "%s\\n%s" "$GDD_MG_VALID" "$GDD_MG_REASON"\n'
        )
        out = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, check=False
        )
        valid, _, reason = out.stdout.strip().partition("\n")
        return valid == "true", reason


def _declared_keys() -> list[str]:
    text = LIB.read_text(encoding="utf-8")
    matched = re.search(r"^GDD_IR_RECOVERY_CORE='(.*?)'", text, re.MULTILINE)
    assert matched, "GDD_IR_RECOVERY_CORE が見つからない"
    keys = re.search(r"必要な key は ([^（(]+)", matched.group(1))
    assert keys, "必要な key の列挙が見つからない"
    return [k.strip() for k in keys.group(1).split(",") if k.strip()]


class IndependentReviewRecoveryContractTests(unittest.TestCase):
    def test_full_line_is_valid(self) -> None:
        valid, reason = _parse(_build_line(None))
        self.assertTrue(valid, reason)

    def test_declared_keys_match_parser_required_keys(self) -> None:
        # 欠落が invalid になる key に加え、**欠落が固有 reason に落ちる key**
        # （`blocking` = 旧書式互換の `legacy-no-blocking-field`）も必要 key に数える。
        # 互換扱いは `GDD_MG_REQUIRE_BLOCKING_FIELD` の反転までの過渡措置であり、
        # 書式としては必須（reason に載せないと operator が復元できない）。
        required = set()
        for key in _LINE_PARTS:
            valid, reason = _parse(_build_line(key))
            if not valid or reason.startswith("legacy-"):
                required.add(key)
        self.assertEqual(
            sorted(_declared_keys()),
            sorted(required),
            "GDD_IR_RECOVERY_CORE の key 列挙が parser の必須集合と一致しない",
        )


if __name__ == "__main__":
    unittest.main()
