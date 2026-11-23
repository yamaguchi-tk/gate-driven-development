"""merge gate: hook の python の出力が UTF-8 に書けない値で落ちても、台帳の照合が空にならない。

hook の python は解析結果を key ごとに stdout へ出す。cd 先などに high surrogate（`\\ud800`）があると、
UTF-8 mode（`-X utf8`）の surrogateescape でも書けずに UnicodeEncodeError になり、後に出す `ledger_targets` が
空のまま終わっていた。marker の無い checkout の経路は台帳に当たったときだけ不足として通知するので、照合する組が
無いと unknown として通る（#449 の独立レビューの G2）。
"""
from __future__ import annotations

from _merge_gate_support import _run_hook
from test_merge_gate_hook_non_gdd_merge import _register
from test_merge_gate_ledger_fail_closed import _hook, _is_block, _is_pass, _LedgerCase

# surrogateescape でも書けない high surrogate（`\udc80`〜`\udcff` は byte として書ける）。
UNENCODABLE = "\ud800"


class UnencodableValueTests(_LedgerCase):
    """marker の無い root checkout（hit だけ不足として通知する）。台帳の PR は acme/infra-gdd#7。"""

    def setUp(self):
        super().setUp()
        _register(self.home, self.gdd)

    def test_lone_surrogate_cd_target_still_matches_ledger(self):
        for command in (
            f"cd /tmp/{UNENCODABLE}; gh pr merge 7",
            f"cd /tmp/{UNENCODABLE}; gh pr merge 6 && gh pr merge 7",
            f"gh pr merge -R 'acme/{UNENCODABLE}' 6 && gh pr merge 7",
        ):
            with self.subTest(command=ascii(command)):
                result = _hook(command, self.checkout, self.home)
                self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_lone_surrogate_without_ledger_pr_passes(self):
        result = _hook(f"cd /tmp/{UNENCODABLE}; gh pr merge 5", self.checkout, self.home)
        self.assertTrue(_is_pass(result), result.stdout + result.stderr)

    def test_unresolvable_payload_cwd_matches_number_only(self):
        # payload の cwd が解決できない（書けない文字を含む・存在しない）と実行先の repo を決められない。
        # `-R` の無い番号は番号だけで台帳と照合し、台帳の PR なら不足として通知し、外れたら今までどおり通す。
        for cwd in (f"/tmp/{UNENCODABLE}", str(self.tmp / "missing")):
            for command, blocked in (("gh pr merge 7", True), ("gh pr merge 5 && gh pr merge 7", True),
                                     ("gh pr merge 5", False)):
                with self.subTest(cwd=ascii(cwd), command=command):
                    payload = {"tool_input": {"command": command, "cwd": cwd}}
                    result = _run_hook(payload, self.checkout, self.home, drop_env=("GDD_HOOK_STATE_DIR",))
                    verdict = _is_block(result) if blocked else _is_pass(result)
                    self.assertTrue(verdict, result.stdout + result.stderr)
