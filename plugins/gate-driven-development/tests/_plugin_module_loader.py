"""明示パスで plugin の module を読む共有ローダ。

`hooks/scripts/lib` と `scripts/lib` は **同じパッケージ名 `lib`** を持つため、
`sys.path.insert` + `from lib.X import` は import 順序に依存して落ちる
（実測: `scripts/lib` を先に import したあとでは `No module named 'lib.tasklist_parse'`）。
明示パス loader を各テストが個別に書き写すと、`sys.modules` 登録のような
「必要だと記録されている手順」が写し落とされる。1 箇所に置いて共有する。
"""
from __future__ import annotations

import importlib.util
import sys
from types import ModuleType

from _paths import PLUGIN_ROOT


def load_plugin_module(relative_path: str) -> ModuleType:
    """Load a module by explicit file path, bypassing package-name collisions."""
    path = PLUGIN_ROOT / relative_path
    module_name = f"gdd_contract_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {relative_path} from {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclass の解決は sys.modules 経由で行われるため exec_module の前に登録する
    # （Python 3.14 では未登録だと `_is_type` が None を引いて AttributeError になる）
    # 先例: tests/test_gdd_scorecard_contract.py の load_module()
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
