"""テストが共有する plugin・repo のルートパス。

各テストが `Path(__file__)` から個別に組み立てると、`.resolve()` の有無や
`parents[1]` / `parent.parent` の綴りがばらつく。1 箇所に置いて共有する。
"""
from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
