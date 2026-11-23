"""`review-log-present.sh` と `version-not-consumed.sh` が共有する identity marker 判定。

この判定は元々両スクリプトにそれぞれ逐語コピーされていた。消費者環境かどうかの
判定ロジックが独立に何度も fail-open を再発させた経緯を
踏まえ、2026-09-16 に共有モジュールへ一本化した（independent-review.md
(h) 受理集合の対称性: 同じ入力を読む判定が複数箇所にあると、片方だけを
直して非対称になるリスクが構造的に残る）。両スクリプトは
`importlib.util.spec_from_file_location` でこのファイルをロードして使う
（`scripts/release.py` の既存のロード方式と同じパターン）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def repository_identity(base: Path, marketplace_name: str) -> bool | None:
    """base（repo_root）が marketplace_name の checkout かどうかを
    `.claude-plugin/marketplace.json` の `name` フィールドだけで判定する。
    True=妥当な manifest で name が marketplace_name と一致、False=manifest が
    存在しない、または妥当な manifest で name が別の値、None=manifest が
    「ある」のに妥当な marketplace manifest として読めない（呼び出し側で
    FAIL。判定不能を「無い」にしない）。

    H4: 直前の設計（root が `<repo_root>/plugins/<name>` というディレクトリ
    レイアウトと一致するかどうか）は、root が別名の symlink（plugin cache の
    バージョン番号ディレクトリ等）経由だと basename が一致せず、真の開発
    checkout でも SKIP-B になる fail-open だった。さらに逆方向にも壊れて
    いた: 本物の消費者環境（別リポジトリの marketplace clone）が同じレイアウト
    を偶然満たし「開発 checkout」と誤判定される事例が実機に複数実在した。
    git 呼び出しにも、ディレクトリ名の偶然の一致にも触れない、リポジトリが
    既に持っている固定の自己申告フィールドを読むだけの設計に転換した。

    H5: 上記の実装は `.get("name") == marketplace_name` の等価比較だけに
    頼っており、`name` キー欠落・null・非文字列・空文字列（例: `{}`）が
    例外を投げずに False（別リポジトリ・SKIP-B）に落ちていた。`name` は
    marketplace の主キーであり、これを欠く manifest は「別の marketplace」
    ではなくインストール不能な壊れた manifest であるため、None（判定不能）
    に倒すべきだった。manifest が「ディレクトリ・壊れた symlink・symlink
    loop」の場合（`is_file()` は False を返すが「宣言が無い」わけではない）
    も同様に None にする。「宣言が無い（True でも None でもない）」と言え
    るのは、その位置に何も無い場合だけに限定する。

    H6: 上記は leaf（`marketplace.json` 自体）の異常だけを `is_symlink()/
    exists()` で見ており、親（`.claude-plugin`）自体が壊れた symlink・
    symlink loop・通常ファイル・権限拒否ディレクトリの場合を見ていなかった。
    この場合 `manifest.is_file()/is_symlink()/exists()` はいずれも例外を
    投げず全て False を返すため（CPython の stat 系メソッドが `OSError` を
    内部で握りつぶす）、「manifest が無い」＝ False（SKIP-B）に落ちる。
    権限拒否のケースは特に重大で、`.claude-plugin` に正しい name の
    manifest が実在する本物の開発 checkout であっても、読み取り権限が無い
    だけで検査全体が黙ってスキップされる。個々のケースを列挙するのではなく
    既定を反転する: **False（＝「宣言が無い」）を返してよいのは、その位置に
    本当に何も無いことを `FileNotFoundError` で積極的に確認できた場合だけ。
    それ以外の `OSError`（権限拒否・symlink loop・想定外の errno 等）は
    すべて None（判定不能）に倒す**。

    一方で `.claude-plugin` が実在する通常のディレクトリだが `marketplace.json`
    を持たない場合（単体 plugin リポジトリの実際のレイアウト）は、従来通り
    False（SKIP-B）のまま維持する。「親が存在するかどうか」ではなく「親が
    読めるディレクトリとして実在し、その中に宣言が無いことを確認できたか」
    を判定軸にすることで、この正当な消費者環境レイアウトを誤って FAIL させる
    新しい逆方向の穴を作らない。
    """
    holder = base / ".claude-plugin"
    manifest = holder / "marketplace.json"

    def nothing_there(path: Path) -> bool:
        # path に「本当に何も無い」ことを ENOENT で積極的に確認する。権限拒否・
        # symlink loop・途中の component がファイル等（他の OSError）は
        # 「無いとは言い切れない」として False を返す（判定不能 → 呼び出し側で
        # None に倒れる）。
        try:
            os.lstat(path)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return False

    try:
        manifest_is_file = manifest.is_file()
    except OSError:
        return None
    if not manifest_is_file:
        if not nothing_there(manifest):
            return None
        if nothing_there(holder):
            return False
        try:
            if not holder.is_dir():
                return None
        except OSError:
            return None
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    return name == marketplace_name
