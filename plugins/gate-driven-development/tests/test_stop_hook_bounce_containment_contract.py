"""T-5 / AC-12: `record_debug_bounce()` 系の削除と、それが持ち込んでいた
他 worktree 越境（read / write）の消滅を測る契約テスト。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_bounce_containment_contract.py -q
  python3 -m unittest tests.test_stop_hook_bounce_containment_contract

## なぜこの形か（観測子を強くする方向を採らない）

同じ主張（「他 worktree を触っていない」）の検証で **3 周失敗している**
（`.steering/.../tasklist.md` § T-4 § Attempts: literal grep → AST 走査 → `sys.addaudithook`。
毎回「観測子の外側」が見つかった）。表現形や API 名を数え上げる限り原理的に閉じないので、
本ファイルは **観測子非依存の 2 述語**だけで測る。

- **述語 Q（情報流）**: 他 worktree（wtA）の `.steering` の中身**だけ**を振り替えて
  出荷版 hook を実行し、本セッション（wtB）の **stdout の sha が arm 間で不変**であることを assert する。
  read 越境があると wtA の `bounce_count` が本セッションの stdout を変える
  （`[bounce-escalation]` の有無）ので落ちる。どの API で読んだかに依存しない。
- **述語 W（実体変化）**: hook 実行の前後で **wtA 配下の全ファイルの
  (相対パス, sha256) 集合**が不変であることを assert する。`open` / `os.rename` /
  `os.remove` / 子プロセス経由のいずれで書いても、この集合が変わるなら落ちる。

## この観測子が測る範囲 / 測らない範囲（測った述語と書く述語を一致させる）

測る:

- 本セッションの **stdout に出る情報流**（述語 Q）
- **wtA 配下のファイル実体の変化**（述語 W）。追加・削除・改名・内容変更をすべて含む

測らない（限定の外側。ここを書かずに「越境 0」と読ませない）:

1. **実行されなかった経路**。本 fixture が起こすのは
   `gdd-implementation-gating -> gdd-systematic-debugging` の phase 遷移 1 経路だけ
2. **内容が変わらない write**（mtime だけ動く上書き）と atime の更新。
   述語 W は内容 hash を見るので、同一バイト列の書き戻しは検出しない
3. **`persist_handoff_summary()` の write 越境**。本 fixture の transcript は
   Handoff Summary（`<!-- Context Handoff: ... -->` + `**Handoff:**`）を含まないため、
   この経路は起動しない。**T-5 の planned 削除でも消えない越境として実測済み**
   （wtB の steering が terminal・wtA が唯一の active のとき、wtA の `state.md` に
   `Last Handoff Summary=` が書かれる。証跡と再測スクリプトは
   `.steering/20260822-pr-w0-defect-telemetry/tasklist.md` § Current Task § RED Evidence）。
   AC-12 / AC-7 のいずれも当該関数を名指ししないため、本ファイルでは assert しない
4. **wtA の外**（wtB / repo / 絶対パス指定の第三者ディレクトリ）への書き込み
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）= 共通規約 13。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _stop_hook_test_base import _HOOK_PATH  # noqa: E402
from _git_fixture import init_repo  # noqa: E402

_HOOK_SOURCE = _HOOK_PATH.read_text(encoding="utf-8")


_TASKLIST = textwrap.dedent(
    """\
    # Tasklist
    ## Current Task
    ### Task: {task}

    ## Pending Tasks
    - P1 | AC-03 | next

    ## Completed Tasks
    - C1 | AC-01 | done

    ## Status
    Next Action={next_action}
    """
)

_BOUNCE_HEADING = "## Hook-Detected Debug Bounce Log"

#: wtA（他 worktree）の `.steering` に置く内容の型空間。
#: 「bounce_count が本セッションの出力を変える」経路は count>=1 でしか発火しないので、
#: **発火する形（count1）と発火しない形（count0 / worklog 無し / .steering 無し）を
#: 必ず同居させる**。片側だけだと sha が 1 種類になり判別力が消える。
_ARMS = ("count1", "count0", "no_worklog", "no_steering")


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True
    )


def _tree_digest(root: Path) -> dict[str, str]:
    """root 配下の (相対パス -> 内容 sha256) 。git 内部ファイルは除く。"""
    digest: dict[str, str] = {}
    if not root.is_dir():
        return digest
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0].startswith(".git"):
            continue
        if path.is_file():
            digest[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def _run_arm(arm: str) -> dict:
    """実 git の 3 worktree（repo / wtA=他タスク / wtB=本セッション）で hook を 1 回走らせる。

    実ファイル非破壊（すべて tempdir）。戻り値は観測子非依存の生値だけ。
    """
    with tempfile.TemporaryDirectory(prefix="gdd-t5-containment-") as tmp:
        root = Path(tmp).resolve()
        repo, wt_a, wt_b = root / "repo", root / "wtA", root / "wtB"
        repo.mkdir()
        init_repo(repo, branch="main")
        _git("worktree", "add", "-q", "-b", "brA", str(wt_a), cwd=repo)
        _git("worktree", "add", "-q", "-b", "brB", str(wt_b), cwd=repo)

        if arm != "no_steering":
            steering_a = wt_a / ".steering" / "20260101-foreign"
            steering_a.mkdir(parents=True)
            (steering_a / "tasklist.md").write_text(
                _TASKLIST.format(task="FOREIGN-A yoso", next_action="gdd-implementation-gating"),
                encoding="utf-8",
            )
            (steering_a / "state.md").write_text(
                "# state\n- Resume From: gdd-implementation-gating\n", encoding="utf-8"
            )
            if arm in ("count1", "count0"):
                count = 1 if arm == "count1" else 0
                (steering_a / "worklog.md").write_text(
                    "# worklog\n\n"
                    + _BOUNCE_HEADING
                    + "\n2026-08-24T00:00:00+00:00 | task: 20260101-foreign | "
                    + f"from_phase: x | bounce_count: {count}\n",
                    encoding="utf-8",
                )

        steering_b = wt_b / ".steering" / "20260501-task"
        steering_b.mkdir(parents=True)
        (steering_b / "tasklist.md").write_text(
            _TASKLIST.format(task="T-2 | AC-02 | doing now", next_action="gdd-implementation-gating"),
            encoding="utf-8",
        )
        (steering_b / "state.md").write_text(
            "# state\n- Resume From: gdd-implementation-gating\n", encoding="utf-8"
        )
        binding_dir = wt_b / ".gdd" / "tasks" / "20260501-task"
        binding_dir.mkdir(parents=True)
        (binding_dir / "binding.json").write_text(
            json.dumps(
                {
                    "task_id": "20260501-task",
                    "worktree_path": str(wt_b),
                    "steering_path": str(steering_b),
                    "branch": "brB",
                }
            ),
            encoding="utf-8",
        )
        (wt_b / ".claude").mkdir()
        (wt_b / ".claude" / "gdd-dev.local.md").write_text(
            "---\nactive: true\nsession_id: test-session\niteration: 1\n"
            "detected_phase: gdd-implementation-gating\n---\n\nbody\n",
            encoding="utf-8",
        )
        transcript = wt_b / "transcript.jsonl"
        transcript.write_text(
            "\n".join(
                [
                    json.dumps(
                        {"type": "user", "message": {"content": [{"type": "text", "text": "tsuzukete"}]}}
                    ),
                    json.dumps(
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "<gdd-phase>gdd-systematic-debugging</gdd-phase>\nroute check.",
                                    }
                                ]
                            },
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        # fixture 不変条件: wtA は wtB より先に列挙される（逆だと read 越境が起きず
        # 述語 Q が最初から緑になり、RED であることの意味が消える）。
        listing = _git("worktree", "list", "--porcelain", cwd=wt_b).stdout
        order = [ln[9:] for ln in listing.splitlines() if ln.startswith("worktree ")]
        # `assert` は `python -O` で消える。順序が逆だと述語 Q が最初から緑になり
        # RED の意味が失われるため、明示的に送出する。
        if order.index(str(wt_a)) >= order.index(str(wt_b)):
            raise AssertionError(f"fixture 不変条件違反: wtA が wtB より後に列挙された\n{listing}")

        before = _tree_digest(wt_a)
        env = os.environ.copy()
        env["GDD_HOOK_INPUT"] = json.dumps(
            {"cwd": str(wt_b), "session_id": "test-session", "transcript_path": str(transcript)}
        )
        env["CLAUDE_CODE_SESSION_ID"] = "test-session"
        for key in ("CLAUDE_PLUGIN_ROOT", "GDD_PLUGIN_ROOT", "GDD_STOP_HOOK_MAX_CONSECUTIVE_BLOCKS"):
            env.pop(key, None)
        result = subprocess.run(
            ["python3", str(_HOOK_PATH)],
            cwd=str(wt_b),
            env=env,
            capture_output=True,
            text=True,
        )
        after = _tree_digest(wt_a)
        return {
            "arm": arm,
            "exit": result.returncode,
            "stdout": result.stdout,
            "stdout_sha": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "foreign_before": before,
            "foreign_after": after,
        }


class ForeignWorktreeContainmentTests(unittest.TestCase):
    """出荷版 hook が他 worktree の中身に依存せず、他 worktree に書かないこと。"""

    results: dict[str, dict]

    @classmethod
    def setUpClass(cls) -> None:
        # 1 arm あたり実 git repo + worktree 2 本 + hook 1 実行。
        # 3 test で共有して 4 回に抑える（test ごとに作ると 12 回になる）。
        cls.results = {arm: _run_arm(arm) for arm in _ARMS}

    def test_stdout_is_invariant_under_foreign_worktree_content(self):
        """述語 Q: wtA の中身を振り替えても本セッションの stdout が変わらない。"""
        shas = {arm: self.results[arm]["stdout_sha"] for arm in _ARMS}
        self.assertEqual(
            len(set(shas.values())),
            1,
            "他 worktree の内容が本セッションの stdout を変えている（read 越境）: "
            + json.dumps({a: s[:12] for a, s in shas.items()}, ensure_ascii=False),
        )

    def test_no_foreign_worktree_file_is_modified(self):
        """述語 W: wtA 配下のファイル実体が 1 つも変わらない。"""
        for arm in _ARMS:
            with self.subTest(arm=arm):
                before = self.results[arm]["foreign_before"]
                after = self.results[arm]["foreign_after"]
                changed = sorted(set(before.items()) ^ set(after.items()))
                self.assertEqual(
                    changed,
                    [],
                    f"他 worktree に write 越境がある: {[c[0] for c in changed]}",
                )

    def test_each_arm_still_emits_the_bound_sessions_own_continuation(self):
        """positive control: 「hook が何も出さない」実装で述語 Q が緑になるのを防ぐ。

        述語 Q は sha の**一致**しか見ないので、出力が空でも全 arm 同一になり通る。
        bind 済み steering（wtB）由来の内容が毎 arm 出ていることを併せて固定する。
        """
        for arm in _ARMS:
            with self.subTest(arm=arm):
                stdout = self.results[arm]["stdout"]
                self.assertEqual(self.results[arm]["exit"], 0)
                self.assertIn('"decision": "block"', stdout)
                self.assertIn("T-2", stdout)


class BounceSymbolRemovalTests(unittest.TestCase):
    """T-5 の削除が完了していること（code-diff）。

    判定は **AST の `Name` / `Attribute` だけ**を見る。docstring・コメント・
    文字列リテラルは受理しない（`grep` hit を実体の証拠にしない、を検査側でも守る）。
    したがって「docstring に関数名が残っている」ことは本テストでは落ちない。
    """

    @staticmethod
    def _module_tree() -> ast.Module:
        return ast.parse(_HOOK_SOURCE)

    def test_no_unreachable_module_level_function_remains(self):
        """`record_debug_bounce()` だけ消して越境ヘルパを残す実装を機械的に弾く。

        T-5 § Stage Output Contract § 同時判断 の閉じ条件（「同時削除 or 残す理由」）は
        散文の約束で、これを検査する lint は repo に存在しない（= A-4'）。
        本テストは**名前の列挙ではなく到達解析**でその条件を機械化する
        （呼び出し元が消えた越境ヘルパが残ると到達不能関数として現れる）。

        roots  = module-level の実行文から参照される名前
        edge   = def の body 内の全 `Name` / `Attribute` 参照（呼び出しに限定しない）
        判定   = roots からの推移閉包に入らない module-level の def が 0 件
        """
        tree = self._module_tree()
        defs = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        def names_in(node: ast.AST) -> set[str]:
            found: set[str] = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name):
                    found.add(sub.id)
                elif isinstance(sub, ast.Attribute):
                    found.add(sub.attr)
            return found

        roots: set[str] = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            roots |= names_in(node)

        seen: set[str] = set()
        pending = [name for name in roots if name in defs]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(n for n in names_in(defs[current]) if n in defs and n not in seen)

        unreachable = sorted(set(defs) - seen)
        self.assertEqual(
            unreachable,
            [],
            "到達不能な module-level 関数が残っている（呼び出し元だけ消した形）: "
            + ", ".join(f"{n}(L{defs[n].lineno})" for n in unreachable),
        )


if __name__ == "__main__":
    unittest.main()
