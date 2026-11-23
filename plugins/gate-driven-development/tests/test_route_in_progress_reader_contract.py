"""`Route In Progress` を読む全経路が同じ値を返すことを固定する契約テスト。

背景（2026-09-03 実測 / main = 5ca4fee）:
同じ `state.md` に対して 2 つの reader が別の値を返していた。

    - Route In Progress: systematic_debugging | reason: r | updated_by: gdd-dev
    - Route In Progress: none | reason: 解除 | updated_by: human

    `select_route_in_progress()`  → `none`（最終行を採る）
    `gdd_extract_doc_field`       → `systematic_debugging | ...`（最初の一致で `exit`）

実害は gate 判定ではなく**誘導のズレ**だった。人間が解除行を追記して route を
解除しても、`run-session-start-hook.sh` / `run-user-prompt-submit-hook.sh` は
最初の一致（古い route）を context に注入し続ける。

**分岐は「行の選択」1 次元ではなかった**（shipped 実装への実測。本テストの表が
そのまま実測ログに対応する）:

1. 行の選択     —— python は最終行、awk は最初の一致
2. 書式の優先   —— python は正準形（`:`）を旧等号形（`=`）より優先、awk は行順のみ
3. 空値の扱い   —— python は値が空の行を飛ばす、awk は空値のまま `exit`
4. 注記の除去   —— python は enum トークンだけを返す、awk は raw 行末まで返す
5〜7. 行頭アンカー —— python が `    Route In Progress: x`（インデント bare 行）/
   `-Route In Progress: x`（bullet 直後に空白なし）/ `* Route In Progress: x` を
   受理し、awk は拒否していた

4 の実害は単独で fail-open だった。`- Route In Progress: none（2026-08-21 / 人間に
よる解除）` は awk 経路で `none（2026-08-21` として返り、消費者の
`[[ "$v" == "none" ]]` に一致しないため、**解除済みの route が「進行中」として
注入され続ける**。`route_value()` の docstring が記録する bind の不具合と同型。

5〜7 の実害も fail-open だった。`select_route_in_progress()` は done guard の
Check 3 が読む経路なので、インデントされた記入例・散文の `Route In Progress: none`
を現在値として拾うと、未完了 route を抱えたまま done が成立する。
`tests/test_canonical_field_line_anchoring_contract.py` が 5 実装へ課している
「行頭 + bullet marker 1 個 + 空白まで」を、この field の reader にも課す。

規約（本テストが正本）:

- **値の選択は `lib/tasklist_parse.select_route_in_progress()` が単一正本**。
  shell 側は awk に規則を書き写さず、この関数へ委譲する
  （`gdd_extract_route_in_progress`）。7 次元の規則を 2 実装で持つと、片方だけ
  直す形の退行が必ず戻る —— PR #25 で 6 巡した failure mode がまさにこれ
- shell の generic reader `gdd_extract_doc_field` にこの field を渡さない。
  渡した瞬間に「最初の一致」規則が復活するため、call site を機械検査で禁じる
- python3 不在時のフォールバックだけは旧 awk 経路を使う。この状態では
  `select_route_in_progress()` を持つ python reader 自体が起動できないので、
  値が割れる相手が存在しない
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

from lib.tasklist_parse import select_route_in_progress  # noqa: E402

DETECT_STEERING_LIB = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"
SESSION_START_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"
USER_PROMPT_SUBMIT_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"

BACKTICK = chr(96)
FENCE = BACKTICK * 3

#: shell 側で `Route In Progress` を読む全 call site。ここに載っていないファイルが
#: この field を読み始めたら `test_no_shell_call_site_uses_the_generic_reader` が落ちる。
SHELL_READER_FILES = (DETECT_STEERING_LIB, SESSION_START_HOOK, USER_PROMPT_SUBMIT_HOOK)

#: `(id, state.md 本文, 期待値)`。**両 reader がこの表の全行で一致すること**が契約。
#: 期待値は `select_route_in_progress()` の規則（= 採用した規則）で決まる。
ROUTE_READER_CASES: tuple[tuple[str, str, str], ...] = (
    # --- 基本形（現行の両実装が既に一致している。narrowing の巻き添えを検出する） ---
    ("single_canonical", "- Route In Progress: systematic_debugging | reason: r\n", "systematic_debugging"),
    ("bare_line_at_column_one", "Route In Progress: implementation_fix_only\n", "implementation_fix_only"),
    ("legacy_equals_form", "- Route In Progress=design_detail_only\n", "design_detail_only"),
    ("backtick_wrapped_field", f"- {BACKTICK}Route In Progress=batch_mixed{BACKTICK}\n", "batch_mixed"),
    ("absent", "## Gate Status\n- Next Action: done\n", ""),
    # --- 1. 行の選択: 解除の追記が効くこと（報告された再現例そのもの） ---
    (
        "release_appended_later_wins",
        "- Route In Progress: systematic_debugging | reason: r | updated_by: gdd-dev\n"
        "- Route In Progress: none | reason: 解除 | updated_by: human\n",
        "none",
    ),
    # --- 2. 書式の優先: 正準形（`:`）が旧等号形（`=`）に勝つ（行順に依らない） ---
    (
        "canonical_colon_beats_legacy_equals_written_first",
        "- Route In Progress=systematic_debugging\n- Route In Progress: none\n",
        "none",
    ),
    (
        "canonical_colon_beats_legacy_equals_written_last",
        "- Route In Progress: none\n- Route In Progress=systematic_debugging\n",
        "none",
    ),
    # --- 3. 空値の扱い: 値の無い行は現在値にならない ---
    #
    # 値がまるごと無い行（`- Route In Progress:`）は正規表現に**一致しない**ので、
    # ここだけでは空値スキップの分岐に届かない（変異注入で実測: 分岐を削っても
    # 落ちない空洞だった）。`enum を書き忘れて注記だけ残した行`が実際に分岐へ届く形。
    (
        "value_less_line_is_not_a_field",
        "- Route In Progress:\n- Route In Progress: systematic_debugging\n",
        "systematic_debugging",
    ),
    #
    # 空値スキップが観測できるのは、空値の行が有効な行より**後ろ**に来る形だけ
    # （前に置くと最終行採択が上書きして同じ値になる ＝ 空洞。変異注入で実測）。
    # 実害もこの向きにある: 書きかけの行を追記しただけで route が消え、done guard
    # Check 3 が素通りする（fail-open）。
    (
        "note_only_line_appended_later_does_not_clear_the_route",
        "- Route In Progress: systematic_debugging\n"
        "- Route In Progress: | reason: enum 書き忘れ | updated_by: human\n",
        "systematic_debugging",
    ),
    (
        "note_only_line_alone_yields_no_value",
        "- Route In Progress: | reason: enum 書き忘れ | updated_by: human\n",
        "",
    ),
    # --- 4. 注記の除去: enum トークンだけが値（解除済みが「進行中」に化けない） ---
    (
        "fullwidth_note_is_not_part_of_the_value",
        "- Route In Progress: none（2026-08-21 / 人間による解除で route を閉じた）\n",
        "none",
    ),
    (
        "pipe_metadata_is_not_part_of_the_value",
        "- Route In Progress: human_recheck_required | reason: AC 変更 | updated_by: human\n",
        "human_recheck_required",
    ),
    # --- 5〜7. 行頭アンカー: 記入例・散文を現在値にしない ---
    (
        "indented_bare_line_is_not_a_field",
        "    Route In Progress: systematic_debugging\n",
        "",
    ),
    (
        "bullet_without_space_is_not_a_field",
        "-Route In Progress: systematic_debugging\n",
        "",
    ),
    (
        "asterisk_bullet_is_not_a_field",
        "* Route In Progress: systematic_debugging\n",
        "",
    ),
    (
        "nested_bullet_history_note_is_not_a_field",
        "  - Route In Progress: none\n- Route In Progress: systematic_debugging\n",
        "systematic_debugging",
    ),
    ("prose_mention_is_not_a_field", "なお Route In Progress: none と書く\n", ""),
    # --- fence 追跡（`tests/test_fence_policy_single_source_contract.py` と同じ規約） ---
    (
        "closed_fence_example_is_not_the_current_value",
        "解除の書き方:\n"
        f"{FENCE}\n- Route In Progress: none | reason: 記入例 | updated_by: human\n{FENCE}\n"
        "- Route In Progress: systematic_debugging | reason: T-3\n",
        "systematic_debugging",
    ),
    (
        "unclosed_fence_content_is_still_readable",
        f"{FENCE}\n- Route In Progress: systematic_debugging | reason: r\n",
        "systematic_debugging",
    ),
)


def _shell_route_in_progress(text: str, tmp: Path) -> str:
    """shipped の `gdd_extract_route_in_progress` をそのまま実行して値を取る。"""
    target = tmp / "state.md"
    target.write_text(text, encoding="utf-8")
    script = (
        f'source "{DETECT_STEERING_LIB}"; '
        f'gdd_extract_route_in_progress "{target}"'
    )
    proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    # `assert` は `python -O` で無効化され失敗を素通りさせるため、明示的に送出する
    if proc.returncode != 0:
        raise AssertionError(
            "gdd_extract_route_in_progress の実行に失敗した "
            f"(returncode={proc.returncode}): {proc.stderr}"
        )
    return proc.stdout.strip()


class RouteInProgressReaderContractTests(unittest.TestCase):
    """python reader と shell reader が同じ表で同じ値を返すこと。"""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_python_reader_matches_the_table(self) -> None:
        """`select_route_in_progress()`（done guard Check 3 / telemetry の経路）"""
        for case_id, text, expected in ROUTE_READER_CASES:
            with self.subTest(case=case_id):
                self.assertEqual(select_route_in_progress(text), expected)

    def test_shell_reader_matches_the_table(self) -> None:
        """`gdd_extract_route_in_progress`（session-start / user-prompt-submit の経路）"""
        for case_id, text, expected in ROUTE_READER_CASES:
            with self.subTest(case=case_id):
                self.assertEqual(_shell_route_in_progress(text, self.tmp), expected)

    def test_both_readers_agree_on_every_form(self) -> None:
        """表の期待値を経由せず、2 reader を**直接**突き合わせる。

        表側だけを直して実装を放置する形（両 test が同じ期待値を見ているだけ）を
        塞ぐ。片方が規則を変えたらここで落ちる。
        """
        for case_id, text, _expected in ROUTE_READER_CASES:
            with self.subTest(case=case_id):
                self.assertEqual(
                    select_route_in_progress(text),
                    _shell_route_in_progress(text, self.tmp),
                    f"reader 間で値が割れている: {case_id}",
                )


class RouteInProgressPresenceCheckTests(unittest.TestCase):
    """`gdd_validate_active_state_fields` の存在判定も同じ規約で読むこと。

    存在判定は「field 行があるか」しか見ないが、汎用 reader は最初の一致で `exit`
    するので、`- Route In Progress:`（値の無い書きかけ行）が先頭にあると後続の
    正しい行を見ずに「canonical field 欠落」と判定していた。hook はこれを
    `[gdd:blocked]` として出し、**正しく書かれている state.md の resume を塞ぐ**
    （fail-closed の誤爆）。値 reader と存在判定で規約が割れている状態そのもの。
    """

    STATE = (
        "## Gate Status\n"
        "- Resume From: gdd-test-driven-development\n"
        "- Human Check Status: approved\n"
        "- Route In Progress:\n"
        "- Route In Progress: systematic_debugging | reason: T-3\n"
    )

    def _validate(self, state_text: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as d:
            steering = Path(d) / ".steering" / "20260903-example"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(state_text, encoding="utf-8")
            script = (
                f'source "{DETECT_STEERING_LIB}"; '
                f'GDD_STEERING_DIR="{steering}"; GDD_TASKLIST_CANONICAL="false"; '
                'gdd_validate_active_state_fields; '
                'printf "%s\\n" "$?" "$GDD_ACTIVE_STATE_MISSING"'
            )
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
            lines = proc.stdout.splitlines() + ["", ""]
            return int(lines[0] or 1), lines[1]

    def test_value_less_line_does_not_hide_the_canonical_line(self) -> None:
        rc, missing = self._validate(self.STATE)
        self.assertEqual((rc, missing), (0, ""), "書きかけ行が canonical 行を隠している")

    def test_a_genuinely_absent_field_is_still_reported(self) -> None:
        """緩めすぎていないこと（fail-closed が消えていない）。"""
        without = "## Gate Status\n- Resume From: gdd-test-driven-development\n- Human Check Status: approved\n"
        rc, missing = self._validate(without)
        self.assertEqual(rc, 1)
        self.assertIn("Route In Progress", missing)

    def test_a_fenced_example_does_not_satisfy_the_field(self) -> None:
        """記入例だけの state.md を「field あり」にしない。"""
        fenced = (
            "## Gate Status\n"
            "- Resume From: gdd-test-driven-development\n"
            "- Human Check Status: approved\n"
            f"{FENCE}\n- Route In Progress: none\n{FENCE}\n"
        )
        rc, missing = self._validate(fenced)
        self.assertEqual(rc, 1)
        self.assertIn("Route In Progress", missing)


class RouteInProgressValidationCachesTheValueTests(unittest.TestCase):
    """`gdd_validate_active_state_fields` が読んだ `Route In Progress` を再利用できること。

    独立レビューで実測確認された欠陥: `run-user-prompt-submit-hook.sh` は
    `gdd_validate_active_state_fields`（内部で `Route In Progress` を読む）を呼んだ
    直後に、表示用の値を得るためもう一度 `gdd_extract_route_in_progress` を呼んで
    いた —— 同じ `state.md` に対して python3 を 2 回起動する（1 回で足りる）。
    `gdd_validate_active_state_fields` が読んだ値を `GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS`
    として公開し、呼び出し側がそれを再利用できることを固定する。
    """

    def _run(self, state_text: str) -> tuple[int, str, str, int]:
        """`gdd_validate_active_state_fields` を実行し、公開された値と python3 起動回数を返す。

        起動回数は `python3` を薄いカウンタ wrapper で覆って測る —— スタブで
        置き換えると「呼ばれたかどうか」しか見えず、`gdd_extract_route_in_progress`
        の実装が正しく動いていることまでは検証できない。
        """
        with tempfile.TemporaryDirectory() as d:
            steering = Path(d) / ".steering" / "20260903-example"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(state_text, encoding="utf-8")
            counter_dir = Path(d) / "bin"
            counter_dir.mkdir()
            counter_file = Path(d) / "python3.count"
            real_python3 = sys.executable
            wrapper = counter_dir / "python3"
            wrapper.write_text(
                "#!/usr/bin/env bash\n"
                f'printf "x" >> "{counter_file}"\n'
                f'exec "{real_python3}" "$@"\n',
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            script = (
                f'source "{DETECT_STEERING_LIB}"; '
                f'GDD_STEERING_DIR="{steering}"; GDD_TASKLIST_CANONICAL="false"; '
                'gdd_validate_active_state_fields; '
                'printf "%s\\n%s\\n" "$?" "$GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS"'
            )
            env = dict(os.environ)
            env["PATH"] = f"{counter_dir}{os.pathsep}{env.get('PATH', '')}"
            proc = subprocess.run(
                ["bash", "-c", script], capture_output=True, text=True, env=env
            )
            lines = proc.stdout.splitlines() + ["", ""]
            spawn_count = len(counter_file.read_text(encoding="utf-8")) if counter_file.exists() else 0
            return int(lines[0] or 1), lines[1], proc.stderr, spawn_count

    def test_the_value_it_read_is_exposed_for_reuse(self) -> None:
        rc, value, stderr, _ = self._run(
            "## Gate Status\n"
            "- Resume From: gdd-test-driven-development\n"
            "- Human Check Status: approved\n"
            "- Route In Progress: systematic_debugging | reason: T-3\n"
        )
        self.assertEqual(rc, 0, stderr)
        self.assertEqual(value, "systematic_debugging")

    def test_none_is_exposed_as_the_literal_string(self) -> None:
        """`route_in_progress == "none"` 判定は呼び出し側が行う。ここでは剥がさない。"""
        rc, value, stderr, _ = self._run(
            "## Gate Status\n"
            "- Resume From: gdd-test-driven-development\n"
            "- Human Check Status: approved\n"
            "- Route In Progress: none\n"
        )
        self.assertEqual(rc, 0, stderr)
        self.assertEqual(value, "none")

    def test_reading_route_in_progress_spawns_python3_exactly_once(self) -> None:
        """存在判定 1 回につき python3 起動は 1 回だけ（2 回目の再読み込みを要求しない）。"""
        _, _, stderr, spawn_count = self._run(
            "## Gate Status\n"
            "- Resume From: gdd-test-driven-development\n"
            "- Human Check Status: approved\n"
            "- Route In Progress: systematic_debugging | reason: T-3\n"
        )
        self.assertEqual(spawn_count, 1, f"python3 起動回数が想定と異なる: {stderr}")

    def test_run_user_prompt_submit_hook_reuses_the_cache_not_a_second_direct_call(self) -> None:
        """`run-user-prompt-submit-hook.sh` が再利用側（キャッシュ）を選んでいること。

        `test_both_context_injection_hooks_use_the_shared_reader` は「直接呼び出し
        **または**再利用」のどちらでも通す OR 条件なので、単独では
        `run-user-prompt-submit-hook.sh` が再利用から直接呼び出しへ後退しても
        検出できない（変異注入で実測: N5 生存）。ここでは同 hook に限定して
        再利用側であることを固定する。
        """
        text = USER_PROMPT_SUBMIT_HOOK.read_text(encoding="utf-8")
        self.assertIn(
            "$GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS",
            text,
            "run-user-prompt-submit-hook.sh がキャッシュされた値を再利用していない"
            "（python3 の二重起動に後退している）",
        )
        self.assertNotRegex(
            text,
            r"\$\(gdd_extract_route_in_progress\s",
            "run-user-prompt-submit-hook.sh が共有 reader を直接もう一度呼んでいる"
            "（同じ state.md に対する python3 の二重起動）",
        )


class RouteInProgressFallbackTests(unittest.TestCase):
    """python3 が使えないときの退避経路。

    この状態では `select_route_in_progress()` を持つ python reader（done guard /
    telemetry）自体が起動できないので、**値が割れる相手が存在しない**。だから
    行の選択（最終行採択）は再現しない。

    ただし**値の正規化は再現しなければならない**。`none（人間による解除）` を
    そのまま返すと消費者の `[[ "$v" == "none" ]]` に一致せず、解除済みの route が
    「進行中」として注入される —— この欠陥は分岐相手の有無と無関係に出る
    （`route_value()` docstring の bind の不具合と同型）。
    """

    #: `[[:alnum:]]` は libc の wctype 経由で locale 依存になる。macOS の
    #: `ja_JP.UTF-8` / `en_US.UTF-8` はいずれも CJK を alnum とみなし（実測）、
    #: lib を直接 source したときの呼び出し側の locale によって結果が変わる（hook の
    #: 入口では、C.UTF-8 がある環境なら kill-switch.sh がロケールを C.UTF-8 に上書きする）。**同じ入力で 2 locale を回し、両方で python と同じ値**
    #: になることを要求する。1 locale だけだと、C locale では偶然正しい値になる
    #: 入力（"実装修正中" 単体等）で退行を取り逃がす（変異注入で実測: M13）。
    LOCALES_UNDER_TEST = ("C", "ja_JP.UTF-8")

    def _fallback(self, text: str, locale: str) -> str:
        """`python3` を必ず失敗させて退避経路だけを走らせる。

        PATH を削るのではなく shell function で覆う。`command -v` は関数も見つける
        ので、「python3 はあるが起動に失敗する」（import 失敗）側も同時に踏む。

        locale は呼び出し元の環境から継承させず、スクリプト内で `export` して
        固定する。`subprocess.run(..., env=...)` は環境を丸ごと置換してしまい
        `HOME` 等の欠落で bash 起動自体が不安定になるため、既存 env に上書きする
        形にする。
        """
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_text(text, encoding="utf-8")
            script = (
                f'source "{DETECT_STEERING_LIB}"; '
                "python3() { return 127; }; "
                f'gdd_extract_route_in_progress "{target}"'
            )
            env = dict(os.environ)
            env["LC_ALL"] = locale
            proc = subprocess.run(
                ["bash", "-c", script], capture_output=True, text=True, env=env
            )
            if proc.returncode != 0:
                raise AssertionError(
                    f"退避経路が異常終了した (locale={locale}): {proc.stderr}"
                )
            return proc.stdout.strip()

    def test_it_still_returns_a_value(self) -> None:
        """空を返すと存在判定が「field 欠落」に倒れ、全 resume を塞ぐ。"""
        for locale in self.LOCALES_UNDER_TEST:
            with self.subTest(locale=locale):
                self.assertEqual(
                    self._fallback(
                        "- Route In Progress: systematic_debugging | reason: r\n", locale
                    ),
                    "systematic_debugging",
                )

    def test_note_is_stripped_so_a_released_route_is_not_reinjected(self) -> None:
        for locale in self.LOCALES_UNDER_TEST:
            with self.subTest(locale=locale):
                self.assertEqual(
                    self._fallback(
                        "- Route In Progress: none（2026-08-21 / 人間による解除）\n", locale
                    ),
                    "none",
                )

    def test_identifier_glued_to_non_ascii_is_still_truncated_at_the_boundary(self) -> None:
        """識別子と全角が区切り無しで結合した値。

        UTF-8 locale で `[[:alnum:]]` を使うと CJK 文字も alnum に含まれ、
        識別子の終端を見失って**値全体**（`systematic_debugging実装` のような
        壊れた route 名）を返す。python の `route_value()`
        （`[A-Za-z_][A-Za-z0-9_-]*`）は locale に関係なく境界で切るため、
        2 reader が locale 依存でだけ割れる形になっていた。
        """
        for locale in self.LOCALES_UNDER_TEST:
            with self.subTest(locale=locale):
                self.assertEqual(
                    self._fallback("- Route In Progress: systematic_debugging実装\n", locale),
                    "systematic_debugging",
                )

    def test_non_identifier_value_is_kept_for_the_block_side(self) -> None:
        """識別子で始まらない値は落とさず残す（`route_value()` と同じ）。

        空にすると「route なし」に化けて done guard を素通りさせる。
        """
        for locale in self.LOCALES_UNDER_TEST:
            with self.subTest(locale=locale):
                self.assertEqual(
                    self._fallback("- Route In Progress: 実装修正中\n", locale), "実装修正中"
                )

    def test_decorated_value_is_normalized_like_route_value(self) -> None:
        """バッククォート/アスタリスク/引用符の装飾は `route_value()` と同じく剥がす。

        独立レビューで実測確認された欠陥: 剥がさないと `**none**` が `none` と
        一致せず、解除済みの route が「進行中」として注入され続ける
        （`route_value()` docstring の bind の不具合と同型。2026-09-04 実測）。
        """
        cases = (
            ("- Route In Progress: **none**\n", "none"),
            (f"- Route In Progress: {BACKTICK}none{BACKTICK}\n", "none"),
            ('- Route In Progress: "none"\n', "none"),
            ("- Route In Progress: 'none'\n", "none"),
        )
        for locale in self.LOCALES_UNDER_TEST:
            for text, expected in cases:
                with self.subTest(locale=locale, text=text):
                    self.assertEqual(self._fallback(text, locale), expected)

    def test_digit_leading_value_is_kept_whole_not_truncated(self) -> None:
        """`route_value()` は識別子が英字/アンダースコアで始まらなければ**値全体**を返す。

        独立レビューで実測確認された欠陥: 先頭が数字の壊れた値を境界で切り捨てると、
        block 判定に渡す情報が失われる（2026-09-04 実測）。
        """
        for locale in self.LOCALES_UNDER_TEST:
            with self.subTest(locale=locale):
                self.assertEqual(
                    self._fallback("- Route In Progress: 123abc実装\n", locale),
                    "123abc実装",
                )

    def test_multiple_matching_lines_return_the_first_not_the_last(self) -> None:
        """既知の制限（意図的・固定）: この退避経路は最終行採択を再現しない。

        独立レビューが指摘したとおり、ここは本 PR が閉じた欠陥そのものと同型の
        振る舞いが残る（python3 が真に使えない場合に限る）。それでも last-line-wins
        まで再現しないのは、fence 追跡込みの選択規則をこのローカル関数へ複製すると、
        規約が再び 2 実装に散る——本 PR が解消した欠陥のクラスをこの 1 関数の中で
        再生産することになるため。python3 真の不在は環境要因であり、同じ環境では
        `Resume From` 等の他 field も同じ「最初の一致」規則のまま
        （汎用 reader を最終行採択へ拡張する変更は影響範囲が広く、本 PR の対象外。
        `references/state-schema.json` の `route_in_progress_reader` 参照）。
        したがって Route In Progress だけが他 field より劣化するわけではない。
        """
        for locale in self.LOCALES_UNDER_TEST:
            with self.subTest(locale=locale):
                self.assertEqual(
                    self._fallback(
                        "- Route In Progress: systematic_debugging | reason: r | updated_by: gdd-dev\n"
                        "- Route In Progress: none | reason: 解除 | updated_by: human\n",
                        locale,
                    ),
                    "systematic_debugging",
                )


class RouteInProgressResilientToMalformedInputTests(unittest.TestCase):
    """python3 が使える環境でも、データ起因の失敗で無言退避しないこと。

    独立レビューで実測確認された欠陥: 旧実装は `python3 -c '...'` の**非ゼロ終了**を
    「python3 不在」と同一視しており、state.md に不正 UTF-8 バイトが 1 つあるだけで
    python3 が使える状態のまま無言でフォールバック（最初の一致）に退避していた。
    フォールバックの限界（`RouteInProgressFallbackTests`）は「python3 が真に不在」の
    場合だけを想定しており、この経路はその想定を破る（2026-09-04 実測）。
    """

    def test_invalid_utf8_byte_does_not_trigger_stale_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "state.md"
            target.write_bytes(
                "- Route In Progress: systematic_debugging | reason: r | updated_by: gdd-dev\n"
                "- Route In Progress: none | reason: ".encode("utf-8")
                + b"\xff"
                + " bad byte | updated_by: human\n".encode("utf-8")
            )
            script = f'source "{DETECT_STEERING_LIB}"; gdd_extract_route_in_progress "{target}"'
            proc = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(
                proc.stdout.strip(),
                "none",
                "不正 UTF-8 バイトが原因で最初の一致（stale route）に退避している",
            )


class RouteInProgressCallSiteContractTests(unittest.TestCase):
    """shell 側が generic reader へ戻っていないこと（規約の再分散を禁じる）。"""

    def test_no_shell_call_site_uses_the_generic_reader(self) -> None:
        """`gdd_extract_doc_field ... "Route In Progress"` を出荷物から禁じる。

        generic reader は「最初の一致」で `exit` する。この field を渡した瞬間に
        報告された分岐が復活するので、フォールバック実装の内部を除いて禁止する。
        """
        pattern = re.compile(r'gdd_extract_doc_field[^\n]*"Route In Progress"')
        offenders: list[str] = []
        for path in sorted(PLUGIN_ROOT.rglob("*.sh")):
            if "/tests/" in str(path) or "/fixtures/" in str(path):
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not pattern.search(line):
                    continue
                # フォールバック実装の中だけは許す（python3 不在時の退避経路）。
                if "GDD_ROUTE_FALLBACK" in line:
                    continue
                offenders.append(f"{path.relative_to(PLUGIN_ROOT)}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "generic reader（最初の一致）で `Route In Progress` を読んでいる: "
            + "; ".join(offenders),
        )

    def test_both_context_injection_hooks_use_the_shared_reader(self) -> None:
        """2 つの context 注入 hook が共有 reader の値を実際に**使って**いること。

        禁止側（上のテスト）だけだと、call site を丸ごと消しても通ってしまう。
        単なる名前の出現ではなくコマンド置換の形、または
        `gdd_validate_active_state_fields`（内部で共有 reader を呼び、値を
        `GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS` に公開する）が既に読んだ値の再利用の
        どちらかを要求する —— 名前だけを見ると「呼び出しを汎用 reader へ戻したが
        comment に名前が残っている」形を取り逃がす（変異注入で実測）。

        `run-user-prompt-submit-hook.sh` は後者（再利用）を選んでいる: 同じ
        `state.md` に対して python3 を 2 回起動する重複を解消するため（独立
        レビュー実測、2026-09-04）。再利用も正しく共有 reader を経由することは
        `RouteInProgressValidationCachesTheValueTests` が別途固定する。
        """
        direct_call = re.compile(r"\$\(gdd_extract_route_in_progress\s")
        reuse = re.compile(r"\$GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS\b")
        for path in (SESSION_START_HOOK, USER_PROMPT_SUBMIT_HOOK):
            with self.subTest(hook=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(
                    direct_call.search(text) or reuse.search(text),
                    f"{path.name} が共有 reader の値を使っていない（直接呼び出しも再利用もない）",
                )


if __name__ == "__main__":
    unittest.main()
