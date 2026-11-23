#!/usr/bin/env python3
"""HITL の判断ポイントの固定フィールドだけを見る（Stop hook の記録だけの lint。止めない）。

判定は新しく書かない。`lint-hitl-decision-quality.py` の固定フィールドの検査（承認ポイントごとの前提・
採用しない案・無回答時のデフォルトと件数、完了条件の変換）と、`hooks/scripts/lib/request_diff_field.py`
の `依頼との差:` の検査（`field_problem`。表示した Stop で request-diff の hook が出し直させる判定と同じで、`あり:` で宣言した差も落とす）を呼ぶ。decision-quality の自由文の検査（語の有無など）は呼ばない。

Exit code: 0 pass / 1 欄の不良 / 2 usage error・file not found
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # decision-quality が読む scripts/lib（-I の下では入らない）


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lint_text(text: str) -> list[str]:
    quality = _load("gdd_lint_hitl_decision_quality", HERE / "lint-hitl-decision-quality.py")
    field = _load("gdd_request_diff_field", HERE.parent / "hooks" / "scripts" / "lib" / "request_diff_field.py")
    lines = text.splitlines()
    errors = quality._decision_item_field_errors(lines) + quality._completion_table_errors(lines)
    problem = field.field_problem(text)
    if problem:
        errors.append(f"判断ポイントの `依頼との差:` の欄: {problem}")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: lint-hitl-decision-fields.py <HITL markdown>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    errors = lint_text(text)
    if errors:
        print("ERROR: HITL Decision Fields failed.\n" + "\n".join(f"- {e}" for e in errors))
        return 1
    print("OK: HITL Decision Fields passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
