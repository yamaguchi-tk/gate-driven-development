#!/usr/bin/env python3
"""`git push` コマンド解析: token化・cwd解決・refspec解決・opt-out prefix判定。

design.md § コマンド解析ロジックの再利用方針 により、
`run-pre-pr-gate-hook.sh` の inline python heredoc（bash lib からは source 不可）
とは別に、この module へ集約する。nested shell 展開ロジックは同 heredoc の
`expand_nested_shell_tokens` と同型の重複であり、統合は S-6 で行う。

**設計方針（検出面の網羅）と、その保証範囲**:

保証しているのは「`tests/test_push_command_parse.py::RealShellDifferentialTests.CORPUS`
に**実測で固定した書式集合**については、実 bash / 実 git が push として実行するなら
`is_git_push` も True を返す」という限定命題であり、**任意の shell 入力に対する
無条件の包含関係ではない**。CORPUS は固定ケースの片方向 assert であって property 検証
ではないため、列挙外の書式は保証の外にある（未検出が実測済みの書式は design.md
§ Honest Limitations に列挙する。`<<<` herestring / パイプ経由の shell / ANSI-C
quoting / 変数展開・パラメータ展開・コマンド置換による間接実行など）。

この gate の守備範囲は「うっかりスキップの防止」であり、シェル書式を意図的に選んだ
迂回は escape hatch と同じ「意図的」側に分類して防護対象外とする。

保証している範囲を支える構造は 3 つ:

- 字句層は bash の読みに合わせる（`shell_lexer`）。落とすのは語頭の `#` からのコメントだけで
  （行末まで。バッククォートの区間の中では閉じの手前まで）、語の途中・引用符の中・`${…}` の中の
  `#` は残す。行継続は
  **バックスラッシュのエスケープを数えて**、引用符の外と二重引用符の中でだけ除去する。
  引用符の外の改行は区切り token として残し、引用符の中の改行は語の一部にする
- git global option は「一覧の完全性」に依存しない。未知 flag は arity 不明として
  **引数を取る / 取らない の両方**を subcommand 候補にする（fail-closed）
- 一覧 `GIT_GLOBAL_FLAGS_WITH_ARGUMENT` は過検出を減らすためだけに使い、その正しさは
  `tests/test_push_command_parse.py` が**実 git に問い合わせて**検証する
"""
from __future__ import annotations

import json
import re
import sys

from git_command_parse import (
    NEWLINE_TOKEN,
    COMMAND_SEPARATOR_TOKENS,
    GIT_GLOBAL_FLAGS_WITH_ARGUMENT,
    find_git_subcommand,
    tokenize,
    tokenize_with_boundary,
    subcommand_candidates,
    is_git_token,
    is_redirection_operator,
    is_unquoted_separator,
    token_ends_with_separator,
)


def is_git_push(tokens: list[str]) -> tuple[bool, int]:
    """`git` token を basename 一致で探し、subcommand が `push` か判定する。

    `/usr/bin/git` は shlex で 1 token になるため basename 一致で照合する
    （既存 `run-pre-pr-gate-hook.sh` の `gh` 照合と同型。design.md §判定順 step 3）。
    subcommand 照合の前に git global option を読み飛ばす。読み飛ばさないと step 3 の
    早期 exit により step 4（候補 root 列挙・AC-17）と step 5（`--git-dir` 到達時の
    block）に到達できない。戻り値の index は読み飛ばし前の `git` token 位置を指す。

    コマンド先頭に限定せず token 列全体を走査するため、`echo git push origin main`
    のように git を起動しないコマンドも `True` になる（過検出。design.md
    § Honest Limitations に記載の受容済み挙動で、fail-closed 側に倒している）。
    """
    index = find_git_subcommand(tokens, "push")
    return index >= 0, index


_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
_COMMAND_START_SEPARATORS = frozenset({"&&", "||", ";", "|", "&", "(", NEWLINE_TOKEN})
_OPTOUT_VAR = "GDD_SKIP_PRE_PUSH_GATE"

#: `is_git_push_at_command_start` 専用の区切り集合。`_COMMAND_START_SEPARATORS`
#: に `)` `;;` `{` を加え、`if ...; then git push ...; fi` / `case x in a) git
#: push ...;; esac` / `{ git push ...; }` のような、実 bash が実際に実行する
#: compound command 内の push を見逃さないようにする（PR #88 独立レビュー
#: round 4 指摘 Medium）。`find_optout` / `_find_cd_root` の**既定値**
#: （`_COMMAND_START_SEPARATORS` / `COMMAND_SEPARATOR_TOKENS`）とは意図的に
#: 別にする — 両関数は run-pre-push-gate-hook.sh とも共有されており、
#: 既定値そのものを広げるとそちらの opt-out 受理面・cd 解決まで影響範囲が
#: 本 hook の外に及ぶため。
#:
#: 一方で、round 4 が検出面（この定数）だけを広げた結果、nudge hook 自身の
#: 中で「push とは判定するが opt-out は受理しない」「push とは判定するが
#: cd 解決が外れる」非対称が生まれた（PR #88 人間レビュー round 5 指摘
#: Medium）。`find_optout` と `_find_cd_root`（→ `resolve_candidate_roots`）
#: に `separators`/`cd_separators` 引数を足し、nudge hook 側の呼び出しだけ
#: この widened 集合を明示的に渡すことで、既定値（＝ pre-push gate の受理面）
#: を変えずに 3 判定を同じ「コマンド先頭」定義に揃える。
PUSH_DETECTION_COMMAND_START_SEPARATORS = _COMMAND_START_SEPARATORS | {")", ";;", "{"}

#: `_find_cd_root` / `resolve_candidate_roots` 用の widened 区切り集合。
#: 既定の `COMMAND_SEPARATOR_TOKENS` は `)` `;;` を含む（`is_redirection_operator`
#: 等と共有する汎用集合のため）が `{` は含まない。nudge hook 専用に `{` を
#: 足したものが本集合（上記 `PUSH_DETECTION_COMMAND_START_SEPARATORS` と同じ
#: 動機・同じ scoping 方針）。
PUSH_DETECTION_CD_SEPARATORS = COMMAND_SEPARATOR_TOKENS | {"{"}


def _at_true_command_start(
    tokens: list[str],
    index: int,
    separators: frozenset[str] = _COMMAND_START_SEPARATORS,
) -> bool:
    """`index` の手前にある `env` / `NAME=VALUE` 代入列を読み飛ばした上で、
    真のコマンド先頭（index 0、または区切り token 直後）かどうかを判定する。
    `find_optout` の代入列スキップと同じ規律（`NAME=VALUE git push ...` は
    実 bash が実際に実行する標準的な形で、過検出ではない）。`separators` を
    差し替えることで、呼び出し元ごとに異なる「コマンド先頭」の定義を使える
    （`find_optout` は既定の `_COMMAND_START_SEPARATORS` を直接参照するため、
    この関数の既定値もそれに合わせる）。

    呼び出し元は `is_git_push_at_command_start` に限定する（pre-push gate
    ではなく nudge hook 専用の判定。PR #88 人間レビュー round 6 指摘 High
    参照）。`token_ends_with_separator` の glued punctuation 再解釈を使うのは
    ここだけであり、それが安全なのはこの判定の過検出・過小検出のどちらも
    advisory な nudge の発火にしか影響しないため（block はしない）。
    `find_optout` / `_find_cd_root`（pre-push gate と共有）は同じ再解釈を使わず
    `token in separators` の完全一致に留める。
    """
    cursor = index
    while cursor > 0:
        token = tokens[cursor - 1]
        if token != "env" and not _ASSIGNMENT_RE.match(token):
            break
        cursor -= 1
    return cursor == 0 or token_ends_with_separator(tokens[cursor - 1], separators)


def is_git_push_at_command_start(
    tokens: list[str], original_token_count: int, start: int = 0
) -> tuple[bool, int]:
    """外部副作用（認証付き `gh` 呼び出し等）を伴う hook 専用の狭い判定。

    `is_git_push` は pre-push gate 向けに token 列全体を fail-closed で走査する
    （`echo git push` 等の過検出を意図的に許容: design.md § Honest
    Limitations）。この広い判定をネットワーク I/O を伴う hook にそのまま使うと、
    実行されないコマンド文面（`echo git push` / `# git push` 等）でも認証付き
    `gh` が呼ばれる（PR #88 人間レビュー指摘 High-2）。

    この関数は「git token がコマンド先頭（`env`/代入列を読み飛ばした上で
    index 0、または区切り token 直後）に現れ、かつ push subcommand へ実際に
    到達する」場合だけを対象にする。`is_git_push` の最初の一致だけを見ると、
    その一致が command-start でないときに後続の本物の push（`echo git push
    foo && git push origin bar` の 2 つ目）を見逃すため、command-start 条件を
    満たす一致が見つかるまで全 token を走査する。`bash -c` 由来の展開 token
    （`original_token_count` 以上の index）は対象外にする（`find_optout` と
    同じ規律）。

    `start`（既定 0）以降だけを走査する。呼び出し側が「見つかった一致は
    `push_has_side_effect_excluded_flag` で除外対象だったので、続きを探す」
    形で反復できるようにするため（`git push --dry-run origin main && git
    push origin main` のように、除外対象の push の後に本物の push が続く形を
    取りこぼさない。PR #88 独立レビュー round 4 指摘 Medium）。

    Honest Limitations（未対応、既知）: `then` / `do` / `else` / `elif` /
    `!` のような shell 予約語の直後、および `timeout` / `time` / `nohup` /
    `sudo` のようなコマンド前置ラッパーの直後は command-start として扱わない
    （予約語・ラッパーの一覧は shell によって異なり網羅すると際限が無いため、
    意図的に対応を見送った）。これらの形の push は本 hook では取りこぼす
    （fail-safe = nudge が出ないだけで、gh は呼ばれない）。

    引用符の中の改行は語の一部として読む（`echo "手順\ngit push origin x\nです"`
    の `git push` は引数の文字列の中で、command-start にならない）。引用符が末尾まで
    閉じない入力（縮退）では、行ごとの読みとの和で push を探すので、引用符の中の
    行頭 `git push` も検出しうる（過検出。fail-safe 側）。heredoc の本文は別の
    コマンドとして読むので、本文の行頭 `git push` も command-start になりうる。
    """
    for index, token in enumerate(tokens):
        if index < start:
            continue
        if index >= original_token_count:
            break
        if not is_git_token(token):
            continue
        if not any(
            tokens[candidate] == "push"
            for candidate in subcommand_candidates(tokens, index + 1)
        ):
            continue
        if _at_true_command_start(
            tokens, index, PUSH_DETECTION_COMMAND_START_SEPARATORS
        ):
            return True, index
    return False, -1


#: `git push -h`（実 git、2026-09-15 計測）で確認した、remote へ実際には push
#: しない（or push 完了と無関係な）flag。文字列部分一致ではなく token 完全
#: 一致で見る — `--no-dry-run`（dry-run の明示無効化 = 実 push）を誤って
#: 除外側に倒さないため。
_SIDE_EFFECT_EXCLUDED_FLAGS = frozenset(
    {"-n", "--dry-run", "-d", "--delete", "-h", "--help"}
)


def push_has_side_effect_excluded_flag(tokens: list[str], git_index: int) -> bool:
    """push が `-n/--dry-run` `-d/--delete` `-h/--help` のいずれかを伴うか判定する。

    これらは実際に remote の ref を更新しない（dry-run / help）か、通常の
    followup フロー対象ではない（delete）。外部副作用を伴う hook がこれらの
    ケースにまで認証付き `gh` を呼ばないための判定（PR #88 独立レビュー指摘
    High-2 の付随修正）。`is_git_push` が True を返した呼び出しでのみ使う想定。
    """
    push_index = push_subcommand_index(tokens, git_index)
    if push_index < 0:
        return False
    cursor = push_index + 1
    while cursor < len(tokens):
        token = tokens[cursor]
        if is_unquoted_separator(token, COMMAND_SEPARATOR_TOKENS):
            break
        if token in _SIDE_EFFECT_EXCLUDED_FLAGS:
            return True
        cursor += 1
    return False


def find_optout(
    tokens: list[str],
    original_token_count: int,
    separators: frozenset[str] = _COMMAND_START_SEPARATORS,
) -> dict:
    """AC-4 の opt-out 受理面を機械判定する（design.md §opt-out受理面の機械定義）。

    受理条件: コマンド先頭（index 0、または区切り token 直後）から始まる
    `NAME=VALUE` 代入列があり、その列の直後の token が push を担う git token
    であること。`env` token はスキップしてよい。`bash -c` 由来（展開 token、
    つまり original_token_count 以上の index）は受理しない。プロセス env 経由の
    受理はこの関数の対象外（hook 側が `os.environ` を直接見る。T-9 で実装）。

    `separators`（既定 `_COMMAND_START_SEPARATORS`）は「コマンド先頭」の定義。
    既定値は run-pre-push-gate-hook.sh（pre-push gate）とも共有される受理面で
    あり、そのまま保つ。nudge hook のように push 検出側を
    `PUSH_DETECTION_COMMAND_START_SEPARATORS` まで広げた呼び出し元でも、
    ここでの一致判定はあえて `token in separators` の**完全一致のまま**に
    している（`token_ends_with_separator` のような glued punctuation の
    再解釈は使わない）。opt-out は受理すると pre-push gate の検査自体を素通りさせる
    ため、過検出（誤って受理してしまう）が fail-open に直結する — 過小検出
    （nudge が出ない・cd root 解決が外れる）と非対称なリスク方向であり、
    push 検出側と同じ緩め方はできない（PR #88 人間レビュー round 6 指摘
    High: `>|GDD_SKIP_PRE_PUSH_GATE=1 git push` は実 bash では `>|` が
    redirect 演算子として `GDD_SKIP_PRE_PUSH_GATE=1` という名前のファイルを
    指すだけで環境変数は立たないが、`token_ends_with_separator` で `>|` を
    `>` + `|` に再分割すると末尾の `|` が区切りに一致し、実際には立って
    いない opt-out を受理してしまっていた）。nudge hook 側の「検出はするが
    opt-out は受理しない」非対称（PR #88 人間レビュー round 5 指摘 Medium）
    は、pre-push gate の安全側を優先し、既知の限界として開示するに留める。
    """
    is_push, git_index = is_git_push(tokens)
    if not is_push or git_index >= original_token_count:
        return {"accepted": False, "via": None}

    # git token の手前から代入列（と `env`）を遡り、その先頭がコマンド先頭かを見る。
    cursor = git_index
    has_optout = False
    while cursor > 0:
        token = tokens[cursor - 1]
        if token != "env" and not _ASSIGNMENT_RE.match(token):
            break
        has_optout = has_optout or token == f"{_OPTOUT_VAR}=1"
        cursor -= 1

    at_command_start = cursor == 0 or is_unquoted_separator(tokens[cursor - 1], separators)
    if has_optout and at_command_start:
        return {"accepted": True, "via": "command-prefix"}
    return {"accepted": False, "via": None}


def push_subcommand_index(tokens: list[str], git_index: int) -> int:
    """`git_index` の git が担う `push` subcommand の index を返す。無ければ -1。

    `is_git_push` の戻り index は global option 読み飛ばし**前**の `git` 位置なので、
    refspec 走査（T-4）の起点は `git_index + 1` ではなくこの関数から取る。
    候補が複数ある場合（未知 flag の arity 不明）は最も手前の `push` を採る。
    """
    if git_index < 0 or git_index >= len(tokens):
        return -1
    candidates = [
        candidate
        for candidate in subcommand_candidates(tokens, git_index + 1)
        if tokens[candidate] == "push"
    ]
    return min(candidates) if candidates else -1


def _find_cd_root(
    tokens: list[str],
    limit: int,
    separators: frozenset[str] = COMMAND_SEPARATOR_TOKENS,
) -> str:
    """`limit` より手前で**実際に実行される** `cd` の引数を返す。無ければ空文字。

    `find_optout` と同じ「コマンド先頭 = index 0 または区切り token 直後」の規律を
    `cd` 走査にも適用する。規律なしだと `echo cd /tmp && git push` の `cd` を実行扱い
    にし、引数検証なしだと `cd && git push` / `cd -P /repo/a` で区切り token や option
    token（`-` / `-L` / `-P` / `--`）をそのまま候補 root にする。誤 root は hook 側の
    ディレクトリ実在チェックで候補が全滅し、**無記録の exit 0（fail-open）** になる。

    引数が取れない `cd`（`cd` 単独 / `cd -`）は root を決められないので空文字を返し、
    AC-17 の優先順どおり payload cwd → process cwd へフォールバックさせる。
    複数ある場合は最後にコマンド先頭で現れた `cd` を採る（後の `cd` が勝つ）。

    `separators`（既定 `COMMAND_SEPARATOR_TOKENS`）は「コマンド先頭」の定義。
    既定値は run-pre-push-gate-hook.sh（pre-push gate）とも共有される。ここでの
    一致判定は `token in separators` の**完全一致のまま**にしている
    （`token_ends_with_separator` の glued punctuation 再解釈は使わない）。
    誤った root を候補にすると、hook 側のディレクトリ実在チェックで候補が
    全滅し無記録の exit 0（fail-open）になりうるため、`find_optout` と同じ
    理由で過検出を避ける安全側に倒す（PR #88 人間レビュー round 6 指摘
    High、`find_optout` の docstring 参照）。nudge hook 側の「検出はするが
    cd 解決だけ外れる」非対称（PR #88 人間レビュー round 5 指摘 Medium）は、
    pre-push gate の安全側を優先し、既知の限界として開示するに留める。
    """
    cd_root = ""
    for index in range(limit):
        if tokens[index] != "cd":
            continue
        if index and not is_unquoted_separator(tokens[index - 1], separators):
            continue
        argument = index + 1
        while argument < limit and tokens[argument].startswith("-"):
            argument += 1
        usable = argument < limit and not is_unquoted_separator(tokens[argument], COMMAND_SEPARATOR_TOKENS)
        cd_root = tokens[argument] if usable else ""
    return cd_root


def resolve_candidate_roots(
    tokens: list[str],
    git_index: int,
    payload_cwd: str,
    process_cwd: str,
    cd_separators: frozenset[str] = COMMAND_SEPARATOR_TOKENS,
) -> dict:
    """AC-17: `-C`/`-C=` > `cd` > payload cwd > process cwd の優先順で候補 root を決める。

    design.md §判定順 step 4: `--git-dir`/`--work-tree` を伴う場合は「解釈不能」とし、
    その引数が指す先も候補 root 集合に加える（この順序にしないと
    `git --git-dir=<GDD repo>/.git push` が非 active early-exit をすり抜ける）。

    `cd_separators` は `_find_cd_root` へそのまま渡す「コマンド先頭」の定義
    （既定は run-pre-push-gate-hook.sh と共有する `COMMAND_SEPARATOR_TOKENS`）。
    """
    unresolvable = False
    extra_roots: list[str] = []
    dash_c_root = ""
    cursor = git_index + 1
    while cursor < len(tokens):
        token = tokens[cursor]
        if token == "push":
            break
        if token == "-C" and cursor + 1 < len(tokens):
            dash_c_root = tokens[cursor + 1]
            cursor += 2
            continue
        if token.startswith("-C="):
            dash_c_root = token.split("=", 1)[1]
            cursor += 1
            continue
        if token.startswith(("--git-dir", "--work-tree")):
            unresolvable = True
            if "=" in token:
                value = token.split("=", 1)[1]
                cursor += 1
            else:
                value = tokens[cursor + 1] if cursor + 1 < len(tokens) else ""
                cursor += 2
            if token.startswith("--git-dir"):
                value = value.removesuffix("/.git") or value
            extra_roots.append(value)
            continue
        cursor += 1

    cd_root = _find_cd_root(tokens, git_index, cd_separators)
    primary_root = dash_c_root or cd_root or payload_cwd or process_cwd
    return {"roots": [primary_root] + extra_roots, "unresolvable": unresolvable}


#: push 対象 ref の tip を一意に決められなくする flag。
#: 実 git が `alias of --all` と宣言する別綴り（`--branches`）も同じ集合に入れる。
_AMBIGUOUS_FLAGS = frozenset({"--all", "--branches", "--mirror"})

#: `git push` option のうち、**分離引数を消費する**もの。
#: 引数を refspec と誤認しないためだけに使う。値を取らない option を誤って
#: 登録すると逆に次 token（remote 名）を読み飛ばし、実際の refspec が捨てられて
#: `explicit_ref=None`（ref 省略扱い）になる fail-open を生むため、
#: **登録の向きは両方とも危険**。
#:
#: この 2 つの集合の arity と alias 関係は
#: `tests/test_push_command_parse.py::PushFlagArityTests` が
#: `git push -h`（実 git）に問い合わせて検証する（synopsis のような二次情報や
#: 記憶を正本にしない。`GIT_GLOBAL_FLAGS_WITH_ARGUMENT` と同じ規律）。
_KNOWN_VALUE_FLAGS = frozenset(
    {
        "--repo",
        "-o",
        "--push-option",
        "--receive-pack",
        "--exec",
    }
)


def classify_refspec(tokens: list[str], git_index: int) -> dict:
    """AC-16: push 対象 ref の tip を一意解決できるかを判定する。

    `--all`/`--mirror`/複数 refspec（remote 名の後に 2 個以上の非オプション token）
    は ambiguous とし block 対象にする。通常運用の
    `git push -u origin <branch>`（HEAD == tip）は ambiguous=False で通す。

    shell のリダイレクト（`2>&1` / `> file` / `&> file`）は push 対象 ref を変え
    ないので数えない（`is_redirection_operator`）。
    """
    # `git_index` は global option 読み飛ばし**前**の `git` 位置なので
    # `git_index + 2` では `git -C <dir> push` の `<dir>` / `push` を refspec と
    # 誤認して誤って不足として通知する（over-block。AC-16 / AC-17 違反）。push の位置は T-1 の
    # `push_subcommand_index` から取る（契約の正本を 1 箇所にする）。
    push_index = push_subcommand_index(tokens, git_index)
    if push_index < 0:
        # is_git_push が True の場合のみ呼ばれる想定。到達したら判定不能として
        # fail-closed に倒す
        return {"ambiguous": True, "explicit_ref": None}
    cursor = push_index + 1
    positional: list[str] = []
    while cursor < len(tokens):
        token = tokens[cursor]
        if is_unquoted_separator(token, COMMAND_SEPARATOR_TOKENS):
            break
        if token in _AMBIGUOUS_FLAGS:
            return {"ambiguous": True, "explicit_ref": None}
        if token in _KNOWN_VALUE_FLAGS and cursor + 1 < len(tokens):
            cursor += 2
            continue
        if token.startswith("-"):
            cursor += 1
            continue
        if is_redirection_operator(token):
            # 演算子と転送先の 2 token を読み飛ばす。`git push origin main 2>&1`
            # の `1` を refspec と数えると refspec-ambiguous として誤って通知する（over-block）
            cursor += 2
            continue
        if (
            token.isdigit()
            and cursor + 1 < len(tokens)
            and is_redirection_operator(tokens[cursor + 1])
        ):
            # `2>&1` の fd 番号。演算子側で転送先ごと読み飛ばすのでここは 1 つ進める
            cursor += 1
            continue
        positional.append(token)
        cursor += 1

    # positional[0] は remote 名。それ以降が refspec 候補
    refspecs = positional[1:]
    if len(refspecs) > 1:
        return {"ambiguous": True, "explicit_ref": None}
    if not refspecs:
        return {"ambiguous": False, "explicit_ref": None}

    local_ref = refspecs[0].split(":", 1)[0]
    return {"ambiguous": False, "explicit_ref": local_ref}


def _main() -> int:
    payload = json.load(sys.stdin)
    command = payload.get("command", "")
    payload_cwd = payload.get("payload_cwd", "")
    process_cwd = payload.get("process_cwd", "")

    # 境界値は tokenize_with_boundary から取る（A-11: len(tokens) は nested
    # shell 展開後の長さになり、展開由来 token の境界チェックが機能しない）。
    # 取り違えを判別するのは MainEntrypointOptoutBoundaryTests の
    # test_expanded_optout_after_inner_separator_rejected_via_cli
    # （nested command string の内側に区切り token がある形。区切りが無い形は
    # 境界に到達する前にコマンド先頭判定で落ちるため判別力を持たない）。
    # `shlex.split` 等での再計算も禁止（tokenize_with_boundary の docstring 参照）
    tokens, raw_count = tokenize_with_boundary(command)
    is_push, git_index = is_git_push(tokens)
    result: dict = {"is_push": is_push}
    if is_push:
        result["optout"] = find_optout(tokens, original_token_count=raw_count)
        result["roots"] = resolve_candidate_roots(
            tokens, git_index, payload_cwd, process_cwd
        )
        result["refspec"] = classify_refspec(tokens, git_index)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
