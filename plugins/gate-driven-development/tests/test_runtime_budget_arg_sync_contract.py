"""`lint-runtime-budget.py` のバジェット引数が 2 箇所で同期していることの契約テスト。

背景:
`lint-runtime-budget.py` は 2 つの check から呼ばれる。

- `tests/checks/skill-body-budget.sh`: バジェット本体の検査
- `tests/checks/lint-scripts-functional.sh`: lint script の smoke test

両者は同じ上限値を渡す前提だが、片方だけ引き下げても CI は通ってしまう。
実際、skill の本文を削った作業では人手で `diff <(grep -A7 ...) <(grep -A7 ...)` を実行して
同期を確認しており、自動テストが無かった。

生の `grep -A7` の diff は空にならない。`skill-body-budget.sh` 側は
`required_files` 配列にも同名のパスを持ち、`--quiet` 行の末尾処理も
2 ファイルで異なるためである。よってここでは **引数の値だけを抽出して比較**する。

値そのものは意図的に固定しない。バジェットの引き下げ自体は正当な変更であり、
このテストが守る契約は「2 箇所が同時に動くこと」だけである。
"""
from __future__ import annotations

import ast
import re
import unittest

from _paths import PLUGIN_ROOT as ROOT
BUDGET_SCRIPT = "scripts/lint-runtime-budget.py"

CALLERS = (
    "tests/checks/skill-body-budget.sh",
    "tests/checks/lint-scripts-functional.sh",
)

REQUIRED_FLAGS = frozenset({
    "--max-skill-body-lines",
    "--max-total-skill-body-lines",
    "--max-express-template-lines",
    "--max-standard-template-lines",
    "--max-express-estimated-tokens",
    "--max-standard-estimated-tokens",
})

_FLAG_VALUE = re.compile(r"(--max-[a-z0-9-]+)\s+(\d+)")


def _extract_budget_args(rel_path: str) -> dict[str, str]:
    """`lint-runtime-budget.py` の呼び出し行から `--max-*` の値を抽出する。

    `required_files` 配列などの単なる言及ではなく、実際の実行行
    (`"$PYTHON_BIN" ... lint-runtime-budget.py`) だけを対象にし、
    行末 `\\` で継続する行を連結してから値を拾う。
    """
    lines = (ROOT / rel_path).read_text(encoding="utf-8").splitlines()
    starts = [
        i for i, line in enumerate(lines)
        if BUDGET_SCRIPT in line and "$PYTHON_BIN" in line
    ]
    if len(starts) != 1:
        raise AssertionError(
            f"{rel_path}: {BUDGET_SCRIPT} の実行行が {len(starts)} 件見つかった（1 件であるべき）"
        )

    parts: list[str] = []
    for line in lines[starts[0]:]:
        stripped = line.rstrip()
        parts.append(stripped.removesuffix("\\"))
        if not stripped.endswith("\\"):
            break
    return dict(_FLAG_VALUE.findall(" ".join(parts)))


# smoke 側（`tests/test_p0_meta_feedback_contract.py`）は、実 gate と同じ 6 引数を
# `lint-runtime-budget.py` へ渡して「linter が動くこと」だけを確かめる。値は実 gate より
# 必ず大きく保つ約束だが、`CALLERS` は shell script 前提のため smoke は同期対象外だった。
# 実際 A-1 の引き上げ（33468→33801）で smoke が 33600 のまま取り残され、
# 「smoke > 実 gate」が破れても全 check が緑のまま通る状態になっていた。
SMOKE_FILE = "tests/test_p0_meta_feedback_contract.py"
SMOKE_FUNC = "test_runtime_budget_linter_measures_skill_and_template_runtime_surface"


def _extract_smoke_budget_args() -> dict[str, str]:
    """smoke test が渡す `--max-*` の値を抽出する。

    同じファイルには「意図的に超過させて rc=1 を確かめる」呼び出しもあるため、
    関数名で位置を拘束してから、その関数内の引数リストだけを読む。
    """
    tree = ast.parse((ROOT / SMOKE_FILE).read_text(encoding="utf-8"))
    funcs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == SMOKE_FUNC
    ]
    if len(funcs) != 1:
        raise AssertionError(
            f"{SMOKE_FILE}: {SMOKE_FUNC} が {len(funcs)} 件見つかった（1 件であるべき）"
        )

    args: dict[str, str] = {}
    for node in ast.walk(funcs[0]):
        if not isinstance(node, ast.List):
            continue
        items = [
            e.value for e in node.elts
            if isinstance(e, ast.Constant) and isinstance(e.value, str)
        ]
        for flag, value in zip(items, items[1:]):
            if flag.startswith("--max-") and value.isdigit():
                args[flag] = value
    return args


class RuntimeBudgetArgSyncTests(unittest.TestCase):
    def test_all_required_flags_are_passed(self) -> None:
        """6 つのバジェット引数がどちらの呼び出しにも渡っている"""
        for rel_path in CALLERS:
            with self.subTest(caller=rel_path):
                flags = set(_extract_budget_args(rel_path))
                self.assertEqual(
                    REQUIRED_FLAGS - flags, set(),
                    f"{rel_path}: バジェット引数が欠けている",
                )

    def test_budget_args_are_identical_across_callers(self) -> None:
        """2 箇所のバジェット引数が完全に一致する（片方だけ変更させない）"""
        first, second = CALLERS
        first_args = _extract_budget_args(first)
        second_args = _extract_budget_args(second)

        diff = {
            flag: (first_args.get(flag), second_args.get(flag))
            for flag in set(first_args) | set(second_args)
            if first_args.get(flag) != second_args.get(flag)
        }
        self.assertEqual(
            diff, {},
            f"{first} と {second} のバジェット引数がずれている。"
            "片方だけ変更せず、両方を同時に更新すること "
            f"(flag: ({first} の値, {second} の値)) -> {diff}",
        )

    def test_smoke_budget_args_stay_above_real_gate(self) -> None:
        """smoke 側の 6 値が実 gate の 6 値より大きい（`>` であって `>=` ではない）。

        smoke が実 gate 以下に沈むと、linter が実 gate では落ちる状態でも smoke は
        rc=0 のまま通り、「smoke が先に気づく」という前提が静かに失われる。
        """
        gate_args = _extract_budget_args(CALLERS[0])
        smoke_args = _extract_smoke_budget_args()

        missing = REQUIRED_FLAGS - set(smoke_args)
        self.assertEqual(
            missing, set(),
            f"{SMOKE_FILE}::{SMOKE_FUNC}: バジェット引数が欠けている -> {sorted(missing)}",
        )

        violations = {
            flag: (smoke_args[flag], gate_args[flag])
            for flag in sorted(REQUIRED_FLAGS)
            if int(smoke_args[flag]) <= int(gate_args[flag])
        }
        self.assertEqual(
            violations, {},
            "smoke 側の上限は実 gate より必ず大きく保つこと。"
            "実 gate を引き下げたときは smoke 側も見直す "
            f"(flag: (smoke, 実 gate)) -> {violations}",
        )


if __name__ == "__main__":
    unittest.main()
