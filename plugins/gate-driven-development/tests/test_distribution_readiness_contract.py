"""Contract tests for broad internal GDD distribution readiness."""
from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT


def read(path: str) -> str:
    return (PLUGIN_ROOT / path).read_text(encoding="utf-8")


def load_steering_hook_module():
    script = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
    spec = importlib.util.spec_from_file_location("validate_steering_write", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DistributionReadinessContractTests(unittest.TestCase):
    def test_steering_write_hook_detects_distribution_sensitive_values(self) -> None:
        hook = load_steering_hook_module()

        account_id = "123456" + "789012"
        private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
        sensitive_key = "access_" + "token"
        reasons = hook.collect_violations(
            [
                f"AWS account: {account_id}\n"
                f"private_key: {private_key_marker}\n"
                f"{sensitive_key}: abcdefghijklmnop\n"
            ]
        )
        categories = {category for category, _ in reasons}

        self.assertIn("aws_account_id", categories)
        self.assertIn("secret_marker", categories)
        self.assertIn("sensitive_value", categories)

    def test_steering_write_hook_detects_known_token_prefixes(self) -> None:
        """既知の接頭辞を持つ token 実値は secret_marker として deny する。

        2026-09-01 実測: `- token: ghp_...` 形式の行が find_secret_marker /
        find_sensitive_value のどちらにも拾われず allow されていた
        （SENSITIVE_VALUE_RE のキーワードに裸の `token` が無く、
        SECRET_MARKER_RE は private key マーカーと AKIA しか見ていなかった）。
        token 値はスキャナ誤検知を避けるため連結で組み立てる。

        `japanese_*` の 3 ケースは前方境界の回帰を固定する。Python の `\\b` は
        日本語文字を単語構成文字として扱うため、`\\b` のままだと分かち書きしない
        日本語（この plugin の steering の既定言語）の直後に置かれた実値を
        取りこぼす。`_` 直後・英数字直後の扱いも同じ lookbehind が決めるので
        `after_underscore` を併せて固定する。
        """
        hook = load_steering_hook_module()

        # 実 token と同じ形（fine-grained PAT は 22 文字 + `_` + 59 文字）で組む。
        # 区切り `_` を跨いだ形を 1 本置くのは Copilot レビュー指摘への対応。
        fine_grained = "github_pat_" + "11ABCDEFG0abcdefghijkl" + "_" + "a" * 59
        slack_bot = "xoxb-" + "1234567890123-abcdefghijklmnop"

        lines = {
            "github_pat_classic": "- token: ghp_" + "abcdefghijklmnopqrstuvwxyz0123456789",
            "github_oauth": "- token: gho_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
            "github_server": "- token: ghs_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
            "github_fine_grained": f"- token: {fine_grained}",
            "slack_bot": f"- token: {slack_bot}",
            "slack_user": "- token: xoxp-" + "1234567890-1234567890-abcdefghijkl",
            "slack_client": "- token: xoxc-" + "1234567890123-1234567890123-" + "a" * 20,
            "slack_cookie": "- token: xoxd-" + "a" * 40,
            # Socket Mode 用。`connections:write` を持つため実害があり、
            # CHANGELOG が宣言する「Slack token」の範囲に含まれる。
            "slack_app_level": "SLACK_APP_TOKEN=xapp-" + "1-A01ABCDEFGH-1234567890123-" + "a" * 64,
            "aws_permanent_key": "aws_access_key_id = AKIA" + "IOSFODNN7EXAMPLE",
            "aws_temporary_key": "aws_access_key_id = ASIA" + "IOSFODNN7EXAMPLE",
            "japanese_before_github": "実測で使ったトークンはghp_" + "a" * 36,
            "japanese_before_slack": f"トークンは{slack_bot} です",
            "japanese_before_fine_grained": f"fine-grained は{fine_grained}",
            "after_underscore": "- token: my_ghp_" + "a" * 36,
        }
        for name, line in lines.items():
            with self.subTest(token_kind=name):
                reasons = hook.collect_violations([line + "\n"])
                categories = {category for category, _ in reasons}
                self.assertIn("secret_marker", categories)

    def test_steering_write_hook_detects_tokens_inside_code_blocks_and_attempts(self) -> None:
        """`secret_marker` はコードブロック内・`#### Attempts` 節でも発火する。

        `find_secret_marker` は他の finder（`find_ellipsis` /
        `find_sensitive_value` 等）と違い `in_code_block` / `in_exclude_section` を
        受け取らない。設定例をフェンスに貼る・試行記録に失敗時の値を残す、という
        `.steering/` で実 token が最も落ちやすい 2 箇所を無検査にしないための設計
        だが、どのテストも固定していなかった（`DETECTORS` の secret_marker を
        `None if code else ...` に変異させても全緑になる状態だった）。
        """
        hook = load_steering_hook_module()

        token = "ghp_" + "a" * 36
        chunks = {
            "code_block": f"```sh\nexport GITHUB_TOKEN={token}\n```\n",
            "attempts_section": f"#### Attempts\n- 試行1: token {token} で失敗\n",
        }
        for name, chunk in chunks.items():
            with self.subTest(location=name):
                reasons = hook.collect_violations([chunk])
                categories = {category for category, _ in reasons}
                self.assertIn("secret_marker", categories)

    def test_steering_write_hook_allows_token_prefix_mentions_without_value(self) -> None:
        """接頭辞への言及・redact 済み表記・説明用プレースホルダーは誤検知しない。

        誤検知は fail-closed 側でも実害がある。`secret_marker` は
        NON_DEMOTABLE_CATEGORIES に入っており escape hatch で降格しないため、
        誤検知した表現は書き直すまで恒久的に block される
        （token の書式を説明する steering 記述がまさにこれに当たる）。

        3 枝それぞれにプレースホルダーを置く。区切り文字を含む連続長で下限を
        掛けると `github_pat_YOUR_TOKEN_HERE` / `xoxb-your-token-here` を拾う
        ため、枝ごとに独立して固定しないと片枝だけの回帰を見逃す。
        """
        hook = load_steering_hook_module()

        safe_lines = [
            "GitHub token は ghp_ / gho_ / ghs_ のいずれかの接頭辞で始まる\n",
            "- token: <redacted>\n",
            "xoxb- 形式の Slack bot token は Secrets Manager に保管する\n",
            "ドキュメント例: ghp_your_token_here を置き換える\n",
            "ドキュメント例: github_pat_YOUR_TOKEN_HERE_REPLACE_ME\n",
            "ドキュメント例: xoxb-your-token-here を置き換える\n",
            "設定例 `xoxp-YOUR-SLACK-USER-TOKEN` を .env に置く\n",
            "設定例 xapp-your-app-token-here を使う\n",
            # `xoxo-` は Slack の token 種別に無い（英語の定型句を拾わせない）
            "ありがとう xoxo-everyone-thanks-a-lot\n",
            # `ASIA` は英単語でもあるため、大文字の散文が続く形を固定する
            "REGION ASIAPACIFICNORTHEAST1TOKYO deployment\n",
            # IAM unique ID（AROA/AIDA 等）は credential ではないので対象外
            "principalId: AROA" + "ABCDEFGHIJKLMNOP" + "\n",
        ]
        for line in safe_lines:
            with self.subTest(line=line.strip()):
                reasons = hook.collect_violations([line])
                categories = {category for category, _ in reasons}
                self.assertNotIn("secret_marker", categories)

    def test_steering_write_hook_never_demotes_secret_marker_to_warning(self) -> None:
        """`secret_marker` は 3 回連続 deny の escape hatch で allow に降格しない。

        escape hatch は「AI が別表記で再試行し続ける ping-pong」を止めるための
        降格だが、実 token を握っているのは AI 自身なので、表記だけ変えた再試行
        では値が残ったまま 3 回目に allow へ到達する（2026-09-01 実測）。
        平文の credential が git 履歴へ着地すると取り消せないため、この category
        は降格対象から外す。

        観測点は **4 回すべての returncode**。escape hatch は 3 回目に降格した
        直後に counter を clear するので、終状態だけを見ると降格の有無と独立な
        観測になり test が vacuous になる
        （先例: tests/test_validate_steering_write.py の
        test_self_review_mixed_category_four_consecutive_denies_stays_denied）。
        """
        token = "ghp_" + "a" * 36
        # AI が表記を変えて再試行する現実的なループ（token 値は同一のまま残る）
        variants = [
            f"- token: {token}",
            f"実測で使った token: {token}",
            f"| GitHub | {token} |",
            f"GitHub token = {token}",
        ]
        with tempfile.TemporaryDirectory() as state_dir, tempfile.TemporaryDirectory() as work:
            steering_path = Path(work) / ".steering" / "20260901-secret" / "design.md"
            steering_path.parent.mkdir(parents=True)
            env = dict(os.environ, GDD_HOOK_STATE_DIR=state_dir)
            script = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"

            codes = []
            for variant in variants:
                payload = {
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(steering_path), "content": variant + "\n"},
                }
                codes.append(
                    subprocess.run(
                        [sys.executable, str(script)],
                        input=json.dumps(payload),
                        env=env,
                        capture_output=True,
                        text=True,
                    ).returncode
                )

            # baseline は [2, 2, 2, 2]。NON_DEMOTABLE_CATEGORIES から secret_marker を
            # 外す変異では 3 回目だけが 0 に転じ [2, 2, 0, 2] になる。差は 3 回目に
            # しか現れないので全回を assert する。
            self.assertEqual(codes, [2, 2, 2, 2])

    def test_versioning_uses_manifest_version_and_mentions_codex_release_sync(self) -> None:
        versioning = read("docs/VERSIONING.md")
        manifest_version = json.loads(read(".claude-plugin/plugin.json"))["version"]

        self.assertIn(f"現行バージョン**: v{manifest_version}", versioning)
        self.assertIn(".codex-plugin/plugin.json", versioning)
        self.assertIn("scripts/sync-plugin-tooling.py --check", versioning)


if __name__ == "__main__":
    unittest.main()
