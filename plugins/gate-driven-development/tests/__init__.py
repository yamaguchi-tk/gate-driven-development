"""`tests/` を sys.path に入れる（共通規約 13）。

pytest は `tests/` を sys.path に入れるが、`python3 -m unittest tests.<module>` は
入れない。共有 helper（`_paths` など）を `from _paths import ...` の形で読めるように、
パッケージの import 時に 1 回だけ入れる。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
