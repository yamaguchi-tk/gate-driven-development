"""`scripts/lib/repository_identity.py`（review-log-present.sh・version-not-consumed.sh
が共有する identity marker 判定）の契約テスト。

両 check スクリプトの `repository_identity()` は逐語コピーだった（過去の
fail-open がそれぞれ独立に再発する経路を作っていた。independent-review.md
(h) 受理集合の対称性が指摘する型そのもの）。共有モジュールに一本化し、
ここで (1) モジュール自体の判定ロジックを直接固定し、(2) 両スクリプトが
実際にこの共有モジュールを参照していること（ローカルコピーを再度持ち込ん
でいないこと）を固定する。

脅威モデル（`extract_heredoc`・`SystemExitHandlerBehaviorTests` 共通）: この
検査が対象とするのは、同一リポジトリの開発者による「善意の編集が意図せず
fail-open を再導入する」偶発的なリグレッション（例: ハンドラに `.code` を
読む行を足す、例外処理をまとめようとして広いハンドラを先に置く）である。
検査対象のシェルスクリプト自体を書き換えられる権限を持つ第三者が、この
検査ロジック自体の回避だけを目的に構成した敵対的な合成コード（シェルの
heredoc 構文を悪用した decoy を仕込む等）までは対象としない。同じ権限が
あれば、このテストファイル自体を書き換えて検査を無効化できるため、検査
だけを厳格化しても天井は変わらない。

`except SystemExit:` ハンドラの検査は、当初 AST 構造検査（ハンドラ本体が
`.code` を一切読んでいないことを文・式レベルで否定形に検証する）だった。
Codex による敵対的レビューで、正規表現→文レベル AST→式レベル AST→ハンドラ
の実行到達性（3巡目・F11）→例外型の変数エイリアス・import エイリアス
（4巡目・F16）と、回避経路の指摘が5巡連続した。「`.code` を読んでいないか」
という否定形の代理指標は、型名の意味解析をどれだけ足しても新しい回避経路が
見つかり続ける構造だったため、Opus（claude-opus-5）・Fable（claude-fable-5-1）
双方へのセカンドオピニオンで、`run()` から実際に例外・返り値を発生させ、
観測される終了コードを直接測る肯定形の振る舞いテスト（`SystemExitHandlerBehaviorTests`）
へ全面的に置き換えることで合意した（詳細は review-log 参照）。型名の意味解析
を一切行わないため、F11・F16 はハンドラの型がどう書かれていても構造的に
成立しなくなった。旧 AST 検査（`SystemExitHandlerASTTests` ほか）はこの
振る舞いテストに置き換えられて撤去済み。

F12（`print` 引数の暗黙 dunder メソッド呼び出しによる `.code` 漏洩）は、
`SystemExit.code` に副作用オブジェクトを渡すことで実行結果として検出する
（6巡目・F18、Opus へのセカンドオピニオンで確定）。ただしこれは「ハンドラが
`.code`・`.args` という属性名に Python レベルでアクセスする（代入・`print`・
f-string・`getattr` を含む）」ことだけを検出する。`object.__getattribute__`
や `SystemExit.code.__get__` のようにディスクリプタを直接呼び出す経路は
対象外とする（自然な編集ではまず書かれない形であり、この検査が対象とする
偶発的なリグレッションの範囲外）。「どのような式でも検出できる」という
全称的な保証ではない点に注意。

残る限界は `extract_heredoc` の F13（heredoc 境界抽出自体がシェル構文を
解釈しない正規表現であること）と、上記のディスクリプタ直接呼び出し経路の
2点で、これは同関数の docstring に明記した通り対応を見送っている（独立
レビュー2巡目・low: 「のみ」という表現が上記のディスクリプタ経路の限界と
矛盾していた点を修正）。F16→F17→F18 と「振る舞いテストの検出力をケースの
列挙で埋める」指摘が3巡連続したため、本巡（F18）の `__getattribute__` 化を
もって、この種の指摘に対するレビュー巡は打ち切る（Opus・Fable 双方へのセカンド
オピニオンで、この判断に至った理由を含めて合意。詳細は review-log 参照）。
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from _plugin_module_loader import PLUGIN_ROOT, load_plugin_module

identity_module = load_plugin_module("scripts/lib/repository_identity.py")
MARKETPLACE_NAME = "gate-driven-development"


def extract_heredoc(text: str, rel: str) -> str:
    """`"$PYTHON_BIN" - "$ROOT" <<'PY' ... PY` の本体（実行される Python
    ソース）を取り出す。この境界抽出自体は依然として字句判定だが、
    見つからなければ AssertionError で落ちる（fail-closed）。開始行を実行
    コマンド行そのものに固定し（Codex レビュー指摘・2巡目・medium、実測で
    再現済み: 旧実装は最初に現れる任意の `<<'PY'` にマッチしており、実行
    対象より前に無関係な heredoc（例: `: <<'PY'`）があるとそちらを誤って
    検査対象にしていた）、候補が正確に1個であることも検査する。

    既知の限界（Codex レビュー3巡目・F13・medium、モジュール docstring の
    脅威モデル参照）: この抽出はシェルの引用・heredoc 構文自体を解釈しない
    正規表現である。検査対象を書き換えられる開発者が、この抽出パターンに
    合致する commandと `PY` 境界を持つ decoy heredoc を外側に意図的に仕込み、
    実際に実行する heredoc の delimiter を変えるような敵対的な細工をすれば、
    decoy だけが候補1個として抽出され本物を見逃しうる。この検査は偶発的な
    リグレッションの検出を目的としており、この種の意図的な回避は対象外
    とする。"""
    pattern = re.compile(r"^\"\$PYTHON_BIN\" - \"\$ROOT\" <<'PY'\n(.*?)\nPY\n", re.M | re.S)
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise AssertionError(
            f'{rel}: expected exactly one "$PYTHON_BIN" - "$ROOT" <<\'PY\' heredoc body, found {len(matches)}'
        )
    return matches[0]


def make_variant(source: str, *, run_body: str, handler_body: str | None = None) -> str:
    """`source`（`extract_heredoc` で取得した埋め込み Python 全体）の
    `run()` 関数本体を `run_body` に差し替えた新しいソースを返す。
    `handler_body` を指定した場合は `except SystemExit:` ハンドラの本体も
    それに差し替える（旧バグを意図的に再現する sanity テスト専用。通常の
    振る舞いテストでは指定しない）。呼び出し元の try/except 構造自体は実
    ファイルのまま保つため、`run()` から特定の例外・返り値を発生させた
    ときに、呼び出し元が実際にどういう終了コード・出力になるかを
    subprocess で直接実測できる（Codex レビュー4巡目・F16、Opus・Fable
    へのセカンドオピニオンに基づく振る舞いテストへの転換。詳細は
    review-log 参照）。"""
    tree = ast.parse(source)
    run_statements = ast.parse(textwrap.dedent(run_body)).body
    handler_statements = ast.parse(textwrap.dedent(handler_body)).body if handler_body is not None else None
    found_run = False
    found_handler = handler_statements is None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            node.body = run_statements
            found_run = True
        if handler_statements is not None and isinstance(node, ast.Try):
            for handler in node.handlers:
                if isinstance(handler.type, ast.Name) and handler.type.id == "SystemExit":
                    handler.name = "error"
                    handler.body = handler_statements
                    found_handler = True
    if not found_run:
        raise AssertionError("run() function not found in source")
    if not found_handler:
        raise AssertionError("except SystemExit handler not found in source")
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class RepositoryIdentityModuleTests(unittest.TestCase):
    def test_matching_name_is_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write(base / ".claude-plugin" / "marketplace.json", json.dumps({"name": MARKETPLACE_NAME}))
            self.assertIs(identity_module.repository_identity(base, MARKETPLACE_NAME), True)

    def test_missing_manifest_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self.assertIs(identity_module.repository_identity(base, MARKETPLACE_NAME), False)

    def test_mismatched_name_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write(base / ".claude-plugin" / "marketplace.json", json.dumps({"name": "some-other-repo"}))
            self.assertIs(identity_module.repository_identity(base, MARKETPLACE_NAME), False)

    def test_name_key_missing_is_none(self) -> None:
        # H5: name キー欠落は判定不能(None)、"別リポジトリ"(False)ではない。
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write(base / ".claude-plugin" / "marketplace.json", "{}")
            self.assertIsNone(identity_module.repository_identity(base, MARKETPLACE_NAME))

    def test_broken_holder_symlink_is_none(self) -> None:
        # H6: 親（.claude-plugin）自体が壊れた symlink の場合も判定不能(None)。
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            holder = base / ".claude-plugin"
            holder.symlink_to(base / "nonexistent-target")
            self.assertIsNone(identity_module.repository_identity(base, MARKETPLACE_NAME))

    def test_holder_without_manifest_is_false(self) -> None:
        # D2型: .claude-plugin は実在するが marketplace.json を持たない単体
        # plugin リポジトリのレイアウト。SKIP-B のまま維持する。
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / ".claude-plugin").mkdir(parents=True)
            self.assertIs(identity_module.repository_identity(base, MARKETPLACE_NAME), False)


class SharedModuleWiringTests(unittest.TestCase):
    """両 check スクリプトが共有モジュールを参照しており、ローカルコピーを
    再度持ち込んでいないことを固定する（independent-review.md (h) 受理集合の
    対称性）。"""

    def test_neither_check_script_defines_its_own_copy(self) -> None:
        for rel in ("tests/checks/review-log-present.sh", "tests/checks/version-not-consumed.sh"):
            text = (PLUGIN_ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn(
                "def repository_identity(",
                text,
                f"{rel} must load scripts/lib/repository_identity.py instead of defining its own copy",
            )

    def test_both_check_scripts_load_the_shared_module(self) -> None:
        for rel in ("tests/checks/review-log-present.sh", "tests/checks/version-not-consumed.sh"):
            text = (PLUGIN_ROOT / rel).read_text(encoding="utf-8")
            self.assertIn(
                'scripts" / "lib" / "repository_identity.py',
                text,
                f"{rel} must load scripts/lib/repository_identity.py",
            )

    def test_load_dynamic_module_bootstrap_is_identical_across_check_scripts(self) -> None:
        # 独立レビュー指摘（独立-7・medium）: repository_identity.py・release.py
        # の動的ロード（importlib.util.spec_from_file_location → exec_module）を
        # 専用のブートストラップ関数 load_dynamic_module() に一本化したが、
        # scripts/lib/ への切り出しはしていない（Opus へのセカンドオピニオン:
        # ブートストラップ自体のロードにも同じ保護が要る循環になるため、両
        # check スクリプトへのコピペのままにするのが妥当と判断）。コピペである
        # 以上、両ファイルの実装が同期していることを機械で固定する（型注釈の
        # 差異 `Path` / `pathlib.Path` は正規化して吸収する）。
        pattern = re.compile(
            r"def load_dynamic_module\(module_name: str, path: (?:pathlib\.)?Path\):.*?return module, None\n",
            re.S,
        )
        normalized_by_file: dict[str, str] = {}
        for rel in ("tests/checks/review-log-present.sh", "tests/checks/version-not-consumed.sh"):
            text = (PLUGIN_ROOT / rel).read_text(encoding="utf-8")
            match = pattern.search(text)
            self.assertIsNotNone(match, f"{rel} must define load_dynamic_module()")
            normalized_by_file[rel] = match.group(0).replace("pathlib.Path", "Path")
        review_log_impl, version_impl = normalized_by_file.values()
        self.assertEqual(review_log_impl, version_impl, "load_dynamic_module() implementations have diverged")


class ExtractHeredocTests(unittest.TestCase):
    """`extract_heredoc` 自体の対象同定を固定する。Codex レビュー指摘
    （2巡目・medium、実測で再現済み）: 旧実装は開始行を実行コマンドに固定
    せず、ファイル内で最初に現れる任意の `<<'PY'` にマッチしていたため、
    実行対象より前にダミーの heredoc（例: `: <<'PY'`）を置くと、そちらを
    誤って検査対象にしてしまい、実際に実行される heredoc を見ない（境界が
    見つからないわけではないので fail-closed にならない）。"""

    def test_ignores_a_decoy_heredoc_before_the_real_command(self) -> None:
        text = (
            ": <<'PY'\n"
            "this is not the real payload and must not be selected\n"
            "PY\n"
            '"$PYTHON_BIN" - "$ROOT" <<\'PY\'\n'
            "print('real')\n"
            "PY\n"
        )
        self.assertEqual(extract_heredoc(text, "decoy.sh"), "print('real')")

    def test_raises_when_the_real_command_heredoc_is_missing(self) -> None:
        text = ": <<'PY'\nonly a decoy here\nPY\n"
        with self.assertRaises(AssertionError):
            extract_heredoc(text, "missing.sh")

    def test_raises_when_two_real_command_heredocs_exist(self) -> None:
        text = (
            '"$PYTHON_BIN" - "$ROOT" <<\'PY\'\nprint(1)\nPY\n'
            '"$PYTHON_BIN" - "$ROOT" <<\'PY\'\nprint(2)\nPY\n'
        )
        with self.assertRaises(AssertionError):
            extract_heredoc(text, "duplicate.sh")


class MakeVariantHelperTests(unittest.TestCase):
    """`make_variant` 自体の書き換え能力を固定する。振る舞いテスト本体
    （`SystemExitHandlerBehaviorTests`）が依存する前提を先に固定しておく。"""

    SKELETON = (
        "import sys\n"
        "\n"
        "def run():\n"
        "    return 'OK'\n"
        "\n"
        "try:\n"
        "    verdict_kind = run()\n"
        "except SystemExit:\n"
        "    print('FAIL: original handler')\n"
        "    sys.exit(1)\n"
        "else:\n"
        "    print(f'VERDICT: {verdict_kind}')\n"
        "    sys.exit(0)\n"
    )

    def test_replaces_the_run_function_body(self) -> None:
        variant = make_variant(self.SKELETON, run_body="raise SystemExit(9)")
        self.assertIn("raise SystemExit(9)", variant)
        self.assertNotIn("return 'OK'", variant)

    def test_replaces_the_systemexit_handler_body_when_given(self) -> None:
        variant = make_variant(
            self.SKELETON,
            run_body="raise SystemExit(9)",
            handler_body="print('patched handler')\nsys.exit(2)",
        )
        self.assertIn("patched handler", variant)
        self.assertNotIn("print('FAIL: original handler')", variant)

    def test_leaves_the_systemexit_handler_body_untouched_by_default(self) -> None:
        variant = make_variant(self.SKELETON, run_body="raise SystemExit(9)")
        self.assertIn("print('FAIL: original handler')", variant)

    def test_raises_when_run_function_is_missing(self) -> None:
        with self.assertRaises(AssertionError):
            make_variant("x = 1\n", run_body="pass")

    def test_raises_when_handler_body_given_but_no_systemexit_handler_exists(self) -> None:
        source = "def run():\n    return 'OK'\n\ntry:\n    run()\nexcept ValueError:\n    pass\n"
        with self.assertRaises(AssertionError):
            make_variant(source, run_body="pass", handler_body="pass")


class SystemExitHandlerBehaviorTests(unittest.TestCase):
    """`review-log-present.sh`・`version-not-consumed.sh` に埋め込まれた
    Python の try/except 構造を、実際にサブプロセスで実行して観測される
    終了コードで直接検証する。

    Codex レビュー4巡目・F16（medium、実測で再現済み）: AST 構造検査
    （`find_systemexit_handlers`・`_is_broader_than_systemexit`）は例外型を
    文字列名の一致で判定していたため、`Broad = BaseException` のような
    変数エイリアスや `import ... as Fatal` のような import エイリアスを
    使われると、実行時には先行ハンドラが SystemExit を奪っているにも
    かかわらず検査は正規と誤認していた。これは「`.code` を読んでいないか」
    という否定形（回避経路の列挙）の代理指標である限り、型名の意味解析を
    どれだけ足しても新しい回避経路が見つかり続ける構造だった（正規表現→
    文レベル AST→式レベル AST→到達性→型エイリアス、と5巡連続で類似指摘
    が続いた）。

    Opus（claude-opus-5）・Fable（claude-fable-5-1）双方へのセカンド
    オピニオンで、否定形の構造検査から肯定形の振る舞い検査（`run()` から
    実際に特定の返り値・例外を発生させ、観測される終了コードが期待通りか
    を直接測る）へ転換することで合意した。型名の意味解析（変数エイリアス・
    import エイリアス・条件分岐による束縛）を一切行わないため、F11・F16
    はハンドラの型がどう書かれていても構造的に成立しなくなる。詳細は
    review-log 参照。

    旧 AST 検査（`find_systemexit_handlers`・`_is_broader_than_systemexit`・
    `_handler_type_names`・`handler_is_unconditional_sys_exit_1_without_reading_code`・
    `SystemExitHandlerASTTests`）はこのクラスに置き換えられて撤去した。"""

    TARGET_SCRIPTS = ("tests/checks/review-log-present.sh", "tests/checks/version-not-consumed.sh")

    def _extracted_source(self, rel: str) -> str:
        text = (PLUGIN_ROOT / rel).read_text(encoding="utf-8")
        return extract_heredoc(text, rel)

    def _run(self, rel: str, run_body: str) -> subprocess.CompletedProcess[str]:
        variant = make_variant(self._extracted_source(rel), run_body=run_body)
        with tempfile.TemporaryDirectory() as tmp:
            return subprocess.run(
                [sys.executable, "-", str(Path(tmp))],
                input=variant,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_sanity_old_buggy_handler_lets_256_fall_through_to_rc_zero(self) -> None:
        # sanity check（Opus/Fable 双方の推奨）: 振る舞いテストのヘルパー
        # （make_variant + subprocess 実行）自体が、PR #93 の PR 後レビュー
        # （PR後-3）で修正済みの旧バグ（`code = error.code; sys.exit(code if
        # code != 0 else 1)`）を実際に再現できることを、本題のテストより先に
        # 固定する。SystemExit(256) は POSIX の終了コードマスク
        # （`exit_code & 0xFF`）で rc=0 に落ちる。
        for rel in self.TARGET_SCRIPTS:
            with self.subTest(rel=rel):
                variant = make_variant(
                    self._extracted_source(rel),
                    run_body="raise SystemExit(256)",
                    handler_body=(
                        "code = error.code\n"
                        "print(f'FAIL: {label}')\n"
                        "sys.exit(code if code != 0 else 1)"
                    ),
                )
                with tempfile.TemporaryDirectory() as tmp:
                    result = subprocess.run(
                        [sys.executable, "-", str(Path(tmp))],
                        input=variant,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                self.assertEqual(
                    result.returncode,
                    0,
                    "sanity check failed: the old buggy handler should let SystemExit(256) fall "
                    "through to rc=0, otherwise this test helper cannot be trusted to catch a "
                    "real regression",
                )

    def test_normal_return_value_exits_zero_with_verdict_line(self) -> None:
        # 独立レビュー2巡目・medium: 旧アサーション `assertIn("VERDICT: ", ...)`
        # は部分一致のため、`validate-plugin.sh:64` の行頭アンカー付き ERE
        # `^VERDICT: {check_name}: (OK|SKIP)$` より受理集合が広く、ラベル違い・
        # 行頭でない・末尾に余分な文字がある出力でもテストは通ってしまう
        # （gate とテストの受理集合が非対称だった）。gate と同じ行を固定し、
        # `SKIP` 側（従来未検証だった）も対象に含める。
        for rel in self.TARGET_SCRIPTS:
            label = Path(rel).stem
            for verdict in ("OK", "SKIP"):
                with self.subTest(rel=rel, verdict=verdict):
                    result = self._run(rel, f'return "{verdict}"')
                    self.assertEqual(result.returncode, 0)
                    self.assertIn(f"VERDICT: {label}: {verdict}", result.stdout.splitlines())

    def test_undeclared_return_value_exits_nonzero(self) -> None:
        # run() が宣言済みの 'OK'/'SKIP' 以外を返した場合、呼び出し元が
        # AssertionError を raise し except BaseException 経由で fail-closed
        # になることを固定する。
        for rel in self.TARGET_SCRIPTS:
            label = Path(rel).stem
            with self.subTest(rel=rel):
                result = self._run(rel, 'return "NOPE"')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"FAIL: {label}: unexpected exception during check: ", result.stdout)

    def test_unexpected_exception_exits_nonzero(self) -> None:
        for rel in self.TARGET_SCRIPTS:
            label = Path(rel).stem
            with self.subTest(rel=rel):
                result = self._run(rel, 'raise RuntimeError("boom")')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"FAIL: {label}: unexpected exception during check: ", result.stdout)

    def test_systemexit_with_various_codes_all_exit_nonzero_without_leaking_the_code(self) -> None:
        # 本題: SystemExit の code 値（256・512 という 256 の倍数を含む）を
        # 一切読まず、常に固定文言で rc!=0 にすることを実測で固定する。旧
        # バグ（sanity テスト参照）ならここで 256・512 が rc=0 に落ちる。
        for rel in self.TARGET_SCRIPTS:
            for code in (0, 1, 256, 512, None, "err"):
                with self.subTest(rel=rel, code=code):
                    result = self._run(rel, f"raise SystemExit({code!r})")
                    self.assertNotEqual(result.returncode, 0, f"{rel}: SystemExit({code!r}) must not exit 0")
                    self.assertIn(
                        "run() ended via SystemExit without returning a verdict",
                        result.stdout,
                        f"{rel}: SystemExit({code!r}) must produce the fixed diagnostic line",
                    )

    # Codex レビュー5巡目（medium、実測で再現済み）: 上のテストで SystemExit
    # の code として注入していた値がプリミティブ値（0, 1, 256, 512, None,
    # 文字列）だけだったため、`.code` を暗黙にフォーマットする変異
    # （`print(f'FAIL: {label}: {error.code}')` のような F12 型の回避）を
    # 実際には検出できていなかった。`__format__` が呼ばれた時点で副作用と
    # して `SystemExit(256)` を送出するオブジェクトを code に使い、まず
    # sanity テストでこの変異ハンドラが実際に rc=0 に落ちることを固定して
    # から、実ファイルのハンドラ（`.code` を一切読まない固定文言）では
    # この回避が成立しないことを固定する。
    _FORMAT_BOMB_RUN_BODY = (
        "class _FormatBomb:\n"
        "    def __format__(self, spec):\n"
        "        raise SystemExit(256)\n"
        "raise SystemExit(_FormatBomb())"
    )

    def test_sanity_a_handler_that_formats_the_code_leaks_via_dunder_format(self) -> None:
        for rel in self.TARGET_SCRIPTS:
            with self.subTest(rel=rel):
                variant = make_variant(
                    self._extracted_source(rel),
                    run_body=self._FORMAT_BOMB_RUN_BODY,
                    handler_body="print(f'FAIL: {label}: {error.code}')\nsys.exit(1)",
                )
                with tempfile.TemporaryDirectory() as tmp:
                    result = subprocess.run(
                        [sys.executable, "-", str(Path(tmp))],
                        input=variant,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                self.assertEqual(
                    result.returncode,
                    0,
                    "sanity check failed: a handler that formats .code should leak via the "
                    "__format__ dunder method and fall through to rc=0",
                )

    def test_systemexit_code_with_dunder_format_side_effect_does_not_leak(self) -> None:
        for rel in self.TARGET_SCRIPTS:
            with self.subTest(rel=rel):
                result = self._run(rel, self._FORMAT_BOMB_RUN_BODY)
                self.assertNotEqual(result.returncode, 0, f"{rel}: the format-bomb code must not exit 0")
                self.assertIn(
                    "run() ended via SystemExit without returning a verdict",
                    result.stdout,
                    f"{rel}: the format-bomb code must produce the fixed diagnostic line",
                )

    # Codex レビュー6巡目（medium、実測で再現済み）: `_FormatBomb` は
    # `__format__` メソッドのみをフックしていたため、`print(error.code)`
    # （`__str__` 経由）のような別の暗黙変換経路を見逃していた。個別の
    # dunder メソッドをこれ以上列挙するのではなく、`.code`・`.args` という
    # 属性名への**アクセスそのもの**を `__getattribute__` でフックする
    # sentinel に切り替える（Opus へのセカンドオピニオン: `code` だけでなく
    # `args`（`error.args[0]` は `.code` と同じ値を返す別経路）もフック
    # しないと同型の回避が残ることを実測で確認済み）。
    _CODE_ACCESS_BOMB_RUN_BODY = (
        "class _CodeAccessBomb(SystemExit):\n"
        "    def __getattribute__(self, name):\n"
        "        if name in ('code', 'args'):\n"
        "            raise SystemExit(256)\n"
        "        return object.__getattribute__(self, name)\n"
        "raise _CodeAccessBomb()"
    )

    def test_sanity_a_handler_that_reads_code_leaks_via_getattribute(self) -> None:
        for rel in self.TARGET_SCRIPTS:
            for handler_body in (
                "print(f'FAIL: {label}: {error.code}')\nsys.exit(1)",
                "print('FAIL:', error.args[0])\nsys.exit(1)",
            ):
                with self.subTest(rel=rel, handler_body=handler_body):
                    variant = make_variant(
                        self._extracted_source(rel),
                        run_body=self._CODE_ACCESS_BOMB_RUN_BODY,
                        handler_body=handler_body,
                    )
                    with tempfile.TemporaryDirectory() as tmp:
                        result = subprocess.run(
                            [sys.executable, "-", str(Path(tmp))],
                            input=variant,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                    self.assertEqual(
                        result.returncode,
                        0,
                        "sanity check failed: a handler that accesses .code or .args should leak "
                        "via __getattribute__ and fall through to rc=0",
                    )

    def test_systemexit_code_access_side_effect_does_not_leak(self) -> None:
        # Opus へのセカンドオピニオン: rc!=0 だけでは、ハンドラが実際に
        # `.code`/`.args` を読まずに固定文言で `sys.exit(1)` したことを
        # 区別できない（bomb が except SystemExit: ハンドラで捕捉されずに
        # 未捕捉のままトップレベルまで逃げた場合も、CPython 自体が `.code`
        # を参照するため結果的に rc!=0 になることを実測で確認した）。
        # 固定文言の診断メッセージが出力に含まれることを合わせて確認し、
        # 実ハンドラが正しく実行されたことを担保する。
        for rel in self.TARGET_SCRIPTS:
            with self.subTest(rel=rel):
                result = self._run(rel, self._CODE_ACCESS_BOMB_RUN_BODY)
                self.assertEqual(
                    result.returncode, 1, f"{rel}: the code-access-bomb must exit exactly 1"
                )
                self.assertIn(
                    "run() ended via SystemExit without returning a verdict",
                    result.stdout,
                    f"{rel}: the code-access-bomb must produce the fixed diagnostic line",
                )


if __name__ == "__main__":
    unittest.main()
