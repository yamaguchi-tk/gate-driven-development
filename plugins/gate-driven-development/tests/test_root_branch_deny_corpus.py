"""AC-5 / ADR-4: root-branch 経路の既存 deny の非回帰 corpus。

分割の経緯と共有 fixture は `tests/_root_branch_guard_support.py` を参照。
"""

import json
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import RootBranchGuardFixtureMixin


ROOT_BRANCH_DENY_CORPUS: tuple[str, ...] = (
    "git switch -c codex/20260611-root-branch",
    "git checkout -b codex/20260611-root-branch",
    "git branch codex/20260611-root-branch",
    "git switch -c codex/20260610-example-detection-task",
    "git -c core.hooksPath=/dev/null switch -c codex/20260903-a",
    "git --git-dir=/tmp/gddprobe/.git switch -c codex/20260903-b",
    "git -c a=b -C /tmp/gddprobe checkout -b codex/20260903-c",
    "git --no-pager branch codex/20260903-d",
    "git -C /tmp/gddprobe switch -c codex/20260903-e",
    "git --work-tree=/tmp/w switch -c codex/20260903-f",
    "git --namespace=ns switch -c codex/20260903-g",
    "git --bare switch -c codex/20260903-h",
    "git switch --create codex/20260903-i",
    "git switch --force-create codex/20260903-j",
    "git switch --create=codex/20260903-k",
    "git --git-dir /tmp/gddprobe/.git switch -c codex/20260903-a",
    "git --config-env=core.hooksPath=/dev/null switch -c codex/20260903-b",
    "git --attr-source=refs/heads/main switch -c codex/20260903-c",
    "git --shallow-file=/tmp/gddprobe.shallow switch -c codex/20260903-d",
    "git -p switch -c codex/20260903-e",
    "git --paginate switch -c codex/20260903-f",
    "git -P switch -c codex/20260903-g",
    "git --no-optional-locks switch -c codex/20260903-h",
    "git --no-replace-objects switch -c codex/20260903-i",
    "git --literal-pathspecs switch -c codex/20260903-j",
    "git switch -C codex/20260903-a",
    "git checkout -B codex/20260903-b",
    "git worktree add /tmp/w -b codex/20260903-a origin/main ; "
    "git switch -c codex/20260903-b",
    "git worktree add /tmp/w -b codex/20260903-c origin/main || "
    "git switch -c codex/20260903-d",
    "git worktree add /tmp/w -b codex/20260903-e origin/main | "
    "git switch -c codex/20260903-f",
    "git worktree add /tmp/w -b codex/20260903-g origin/main\n"
    "git switch -c codex/20260903-h",
    "bash -c 'git switch -c codex/20260903-i'",
    "git branch -c old codex/20260903-b",
    "git branch -f codex/20260903-c",
    "sudo git switch -c codex/20260903-d",
    "env FOO=1 git switch -c codex/20260903-e",
    "git branch -cf old codex/20260904-c",
    "git branch -fc old codex/20260904-d",
    "git branch -Cf old codex/20260904-e",
    "git branch -fC old codex/20260904-f",
    "git -C $(pwd) checkout -b codex/20260903-c",
    'git commit -m "example: $(git switch -c codex/20260904-a)"',
    'git commit -m "example: `git switch -c codex/20260904-b`"',
    "echo it\\'s $(git switch -c codex/20260904-c)",
    "bash -c 'git -C $(pwd) checkout -b codex/20260904-f'",
    "bash <<'EOF'\ngit switch -c codex/20260903-a\nEOF",
    "sh <<EOF\ngit switch -c codex/20260903-b\nEOF",
    "cat <<'EOF' | bash\ngit switch -c codex/20260903-c\nEOF",
    "bash -s <<'EOF'\ngit switch -c codex/20260903-d\nEOF",
    "cat <<'EOF' |& bash\ngit switch -c codex/20260903-e\nEOF",
    "bash <<'EOF' &> /tmp/gdd-probe.log\ngit switch -c codex/20260903-f\nEOF",
    "cat <<'EOF' 3<&0 | bash\ngit switch -c codex/20260904-g\nEOF",
    'git commit -m "see <<EOF docs"\ngit switch -c codex/20260903-a',
    "git --future-flag switch -c codex/20260903-x",
    "git --future-flag=v switch -c codex/20260903-y",
    "git worktree add /tmp/w -b codex/20260903-a origin/main && "
    "git switch -c codex/20260903-b",
    # PR #88 独立レビュー round 7 指摘 High/blocking: `&>`（stdout+stderr を
    # まとめてリダイレクトする複合演算子）が simple command の途中に glue
    # されている形。実 bash はこのコマンドで実際に branch を作る
    # （`git switch -c <name>` の実行を止めない）。tokenizer が `&>` を
    # `&`（区切り）+ `>` に誤分割すると segment 分割が git を含む segment
    # からこの branch 名を切り落とし、guard が非回帰的に deny→allow に
    # 退行する。
    "git switch &>/dev/null -c codex/20260903-z",
    # PR #88 人間レビュー round 6 指摘 High: `>|`（noclobber 上書き付き
    # redirect 演算子。`_TWO_CHAR_OPERATORS` 未列挙）が simple command の
    # 途中に glue されている形。実 bash はこのコマンドで実際に branch を
    # 作る（`>|` はファイル名 `/dev/null` への出力上書きを指定するだけで、
    # `git switch -c <name>` の実行を止めない）。round 7 是正は `&>` の
    # 単一リテラルしか regression test で固定しておらず、`>|` のような
    # 別の未列挙演算子では同型の deny→allow 退行が残っていた（人間レビュー
    # round 6 で検出）。
    "git switch >|/dev/null -c codex/20260903-w",
)


class RootBranchDenyCorpusTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    """AC-5 / ADR-4: root-branch 経路の既存 deny を active state 無しで再実行する。

    母集団: `tests/test_root_branch_guard_contract.py`（corpus 抽出時点では
    contract / segmentation / name candidates が 1 ファイルにあった。現在は
    `test_root_branch_guard_*.py` / `test_root_branch_name_candidates.py` へ分割済み）
    で `returncode == 2` を
    assert している全テストメソッドのコマンド文字列リテラルのうち、deny メッセージが
    `Blocked GDD root branch creation` で始まるもの。除外理由はメソッド名ではなく
    実測した deny メッセージで判定した（`worktree add` 経路のメッセージは
    `Blocked GDD worktree creation from HEAD` / `... from a local default branch`
    であり、`test_hook_blocks_unquoted_command_substitution_segmentation` /
    `test_hook_blocks_nested_shell_command_substitution_segmentation` 等、メソッド名に
    `worktree` を含まないテストの中にも worktree add コマンドが混在するため）。
    """

    def test_corpus_is_not_empty(self):
        # 下の subTest のループが空で通らないようにする。件数は固定しない
        self.assertTrue(ROOT_BRANCH_DENY_CORPUS)

    def test_all_corpus_commands_deny_without_active_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            for command in ROOT_BRANCH_DENY_CORPUS:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertTrue(
                        payload["systemMessage"].startswith(
                            "Blocked GDD root branch creation"
                        )
                    )
