"""`gh pr merge` コマンド解析: 判定・PR 引数解決・repo 決定要因の検出。

design.md § コマンド検出の設計 が正本。pre-PR gate（`run-pre-pr-gate-hook.sh`）も、字句解析と
sub-command の探し方（gh〔cobra〕の規則の写し）を import する。名前を変えると、pre-PR gate は
解析の失敗として active GDD の中の create・new・pulls を含むコマンドを不足として通知する。

レビュー指摘の remediation: sub-command 前後どちらの
`-R`/`--repo`/`--repo=` も同じ token walker で repo_flag を確定し、
`GH_REPO=`/`GH_HOST=` は command-prefix と process env の両方を見て
env_repo_conflict を確定し、値を取る flag はその値を消費してから
次の token へ進む（位置引数として誤読しない）。
"""
from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    from . import shell_lexer
except ImportError:  # hook と多くのテストは lib を sys.path に入れて top-level の module として読む
    _DIR = str(Path(__file__).resolve().parent)
    sys.path.insert(0, _DIR)
    try:
        import shell_lexer
    finally:
        sys.path.remove(_DIR)

# heredoc の introducer と所有 pipeline の境界は字句解析の芯（shell_lexer）と共有する。
HEREDOC_RE = shell_lexer.HEREDOC_RE
PIPELINE_BOUNDARY_RE = shell_lexer.PIPELINE_BOUNDARY_RE
# gh の `pr/shared/finder.go` は URL を `url.Parse` した path に `^/([^/]+)/([^/]+)/pull/(\d+)` を
# 前方一致で当てる（scheme は http・https。path の `%xx` は戻して読む。`/pull/7x` も `/pull/7/files`
# も番号 7 の URL）。host は gh が正規化する〔大小文字・Unicode の変換・`www.` などの下位の host は
# github.com と読まれ、host が空の `https:/o/r/pull/7` は既定の host と読まれる〕ので、ここでは
# 列挙で近似せず host を問わず path を読む。名指しできるのは host が `github.com` の形だけ。
URL_SCHEME_RE = re.compile(r"(?i)https?:")
PR_URL_PATH_RE = re.compile(r"/([^/]+)/([^/]+)/pull/([0-9]+)")
ENV_ASSIGNMENT_RE = re.compile(r"^(GH_REPO|GH_HOST)=(.*)$")
# `GH_HOST` の既定値。`GH_HOST=github.com` は「既定ホストの明示」であって repo
# 決定要因ではない。ここを見ないと、明示しただけで `pr-target-unresolvable` の
# 恒久的な不足の通知になる。`GH_REPO` は値に関係なく対象 repo を上書きするので常に conflict。
DEFAULT_GH_HOST = "github.com"
# `2>&1` / `2>` のように空白なしでリダイレクトへ密着した fd 番号。bash は int に収まる
# 並び（`12>x`）も fd 番号に、zsh は 1 桁だけを fd 番号に読む。11 桁以上はどちらも語なので
# 残す（pre-PR gate の本文の 12 桁数字）。2 桁以上は `_mask_for_fd` の判定で merge の対象を決められない側に倒す（merge gate が不足として通知する）。
FD_DIGITS = 10
MULTI_DIGIT_FD_RE = re.compile(r"(^|\s)(\d{2,10})(?=[<>])")
# `gh pr merge` の flag の表（gh 2.93.0 の `gh pr merge --help`。継承の `-R/--repo` と
# `-h/--help` を含む）。gh（cobra＋pflag）は sub-command を見つけた後、コマンド名を除いた
# 全 token をこの表で読む。sub-command を見つける段（`_find_sub_command`）は別の規則。
# 表に無い flag は gh が `unknown flag` で止める（対象を決められない、に倒す）。
MERGE_VALUE_SHORT_FLAGS = frozenset("AbFtR")
MERGE_BOOL_SHORT_FLAGS = frozenset("dhmrs")
MERGE_VALUE_LONG_FLAGS = frozenset({
    "author-email", "body", "body-file", "match-head-commit", "repo", "subject",
})
MERGE_BOOL_LONG_FLAGS = frozenset({
    "admin", "auto", "delete-branch", "disable-auto", "help", "merge", "rebase", "squash",
})
# pflag の bool の値のうち偽（strconv.ParseBool）。
FALSE_BOOL_VALUES = frozenset({"0", "f", "F", "false", "FALSE", "False"})
# gh は先頭の `#` を落として PR 番号を `strconv.Atoi` で読むので、ASCII の数字（`+` の符号と
# 先頭の 0 を許す）だけが番号になる（`str.isdigit` は全角・上付きの数字も受け付ける）。
PR_NUMBER_RE = re.compile(r"#?\+?([0-9]+)")
# cobra の探索（`stripFlags`）が値を取らない長い flag として読む名前（root は `--help` と
# `--version`、`pr` は `--help`）。鍵は探す名前（pre-PR gate は create・new・api を探す）。gh 2.93.0 で確かめた。
FIND_BOOL_LONG_FLAGS = {
    **dict.fromkeys(("pr", "api"), frozenset({"help", "version"})),
    **dict.fromkeys(("merge", "create", "new"), frozenset({"help"})),
}
# 演算子文字・退避先の候補は字句解析の芯（shell_lexer）の定義を使う。演算子は「全文字が
# 演算子文字」という形で判定し、集合の取りこぼしを構造的に無くす（`gh pr merge 7 2>&1` の
# `>&` を位置引数と読まない）。
COMMAND_OPERATOR_CHARS = shell_lexer.COMMAND_OPERATOR_CHARS
_SHLEX_SPECIAL_CHARS = shell_lexer.SHLEX_SPECIAL_CHARS
OPERATOR_MASK_START = shell_lexer.OPERATOR_MASK_START
# 演算子の内訳。「最初の演算子で走査を打ち切る」実装は、shell が
# リダイレクトを simple command の**任意位置**に置けることを取りこぼしていた
# （`gh pr merge </dev/null other-branch` の位置引数が見えず「引数省略形」と
# 誤認され、別 PR 向けの承認で allow された）。制御演算子は simple command の
# 区切り、リダイレクト演算子はオペランドごと読み飛ばす対象、と分けて扱う。
CONTROL_OPERATOR_CHARS = frozenset(";|&")
REDIRECT_OPERATOR_CHARS = frozenset("<>")
# `bash -c '<command>'` / `eval '<command>'` の入れ子を 1 段ずつ解いて再走査する
# 深さ上限。agent が日常的に使う idiom なので、posix shlex が
# クォートを剥がして 1 token になった時点で検出できなくなる面を閉じる。
SHELL_INTERPRETERS = shell_lexer.SHELL_INTERPRETERS
MAX_NESTED_SHELL_DEPTH = 3
# 1 層（`_nested_shell_commands` の 1 回の呼び出し）で展開する env split-string の
# 個数の上限。1 つの simple command に split-string を区切りなしで多数並べると、
# 各 argv が後続の split-string を抱えて次の深さで再展開され、解析時間が個数に
# 対して指数的に伸びる（agent が手順を忘れて書く形は通常 1〜2 個で、8 を超える
# 正当な書き方は想定しない）。超えたら展開をやめ、module 内の例外で
# `parse_gh_pr_merge` / `_extract_cd_target` まで戻し、既存の「対象を決められ
# ない」表現（`unresolvable=True`）へ倒す。
MAX_ENV_SPLIT_STRINGS_PER_LAYER = 8


class _EnvSplitStringBudgetExceeded(Exception):
    """env split-string の本体を確かめられず、解析を続けられない。

    2 つの契機がある: (1) 1 層の展開個数が `MAX_ENV_SPLIT_STRINGS_PER_LAYER`
    を超えた、(2) 本体に `\\c`（本ホスト `man env` で「文字列の残りを無視す
    る」記号）が含まれる。`\\c` は tokenize 側では普通の文字 `c` に戻ってしまい
    実 env の打ち切りを再現できないため、`\\c` を見た時点で「対応を確かめられな
    い形」として (1) と同じ扱いに倒す（人間承認 2026-09-11T17:40:53+09:00）。"""


# shell interpreter の短フラグ束（`-c` / `-lc` / `-euo`）。旧判定
# `startswith("-") and endswith("c")` は `--norc` を `-c` と誤認し、値を取る
# フラグ（`-euo pipefail`）の値で走査を打ち切って `-c` に到達できなかった。
SHORT_FLAG_RE = re.compile(r"^[-+][A-Za-z]+$")
# 束の末尾に来ると次の token を値として食う短フラグ（`bash -euo pipefail`）。
VALUE_TAKING_SHELL_FLAG_CHARS = frozenset("oO")
VALUE_TAKING_SHELL_LONG_FLAGS = {"--rcfile", "--init-file"}

# cwd 変更 token（AC-4 の受理条件が対象にする語彙）。`env -C` は 2 token 形だが、
# condition (h)（`env` の basename 一致で走査範囲全体を不採用にする）が先に効くため
# 個別の 2-token 判定は持たない。
CWD_CHANGE_WORDS = {"cd", "pushd", "popd", "chdir"}
# `env` の chdir を表す短オプション。綴りは BSD / GNU とも `-C` / `--chdir` の
# 2 つだけなので、短オプション束（`-iC`）・値密着（`-iC/B`）・両方（`-iC/B`）まで
# 1 本で閉包できる。`--chdir` は長オプションなので `[^-]*` に掛からず、
# 呼び出し側の接頭一致が受け持つ（`--chdir=/B` / `--chdir /B` の両方）。
CHDIR_SHORT_OPTION_RE = re.compile(r"^-[^-]*C")
# `env` の split-string オプション（`-S` / `--split-string`）走査で使う綴りの正本
# （走査規則そのものの正本は `_env_split_string_body` の docstring）。
# 値を取る短オプション文字: BSD env の `-C` / `-P` / `-u` と GNU coreutils env の
# `-a`（`--argv0`）の和集合。`-S` も値を取るが本体として別に扱う。
ENV_VALUE_TAKING_SHORT_OPTION_CHARS = frozenset("CPua")
# 値を別 token でも取る長オプション（GNU）。`--block-signal` 等の optional-argument
# （`[=SIG]`）は `=` 形でしか値を取らないので含めない。含めないことがそのまま
# 「option token だけ読み飛ばす」挙動になる。
ENV_REQUIRED_ARG_LONG_OPTIONS = ("--chdir", "--unset", "--argv0")
# `NAME=value` 形の環境変数代入（一般形）。上の `ENV_ASSIGNMENT_RE` は
# `GH_REPO` / `GH_HOST` 専用で repo 決定要因の判定に使う別物。
ENV_NAME_VALUE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _collect_nested_shell_layers(
    tokens: list[str],
) -> tuple[list[str], list[str], bool]:
    """`_scan_tokens` と同じ深さ（`MAX_NESTED_SHELL_DEPTH`）まで入れ子 shell 本体を
    展開し、(生文字列のリスト, token 列を平坦化したリスト, 縮退したか) を返す。

    `_scan_tokens` は入れ子 `bash -c` / `eval` を depth 引数で
    `MAX_NESTED_SHELL_DEPTH` まで再帰的に解くが、旧実装の
    `_extract_cd_target` は 1 段しか展開していなかった（IG-1）。走査範囲が
    食い違うと、深い階層にある追加の `cd` を見落として top-level の `cd` を
    誤って単独採用してしまう。

    展開は **層ごと（BFS）に本体ごとの token 列を分けたまま** 進め、同一本体
    文字列は最初（= 最浅の層）に見た 1 回だけ展開する。
    - 層ごとに全本体の token を 1 本の frontier へ連結すると、`eval` の本体
      （= 残り token 全部）が他の本体の token まで巻き込んで層をまたいで乗算的に
      膨張し、`eval` 13 個で hook の timeout 10 秒を超えて通知を返せなくなる
      （IG-4、fail-open）。
    - 本体ごとの DFS で全層を保持すると、`eval×n` では各層の本体が互いの suffix
      になるため `_scan_tokens` と同型の O(n^4) 走査を独立にもう 1 回行い、本体を
      n^3 オーダーで保持する（IG-6。main より所要時間が大きく延び、メモリ使用量も桁違いに増えた）。
    呼び出し側の条件 (f)(g)(h) は本体集合に対する存在検査で、`nested_hits` も
    「0 か否か」しか判定に効かないため、重複本体の再展開を省いても結果は不変。
    BFS は浅い層を先に処理するので、同一本体を最初に見る位置は常に最浅であり、
    深い層で再展開しても得られる本体はその部分集合にしかならない（走査する
    本体の集合は DFS の superset。深さ予算が効く形では BFS の方が広く、
    狭くなることはない）。
    """
    bodies: list[str] = []
    body_tokens: list[str] = []
    seen: set[str] = set()
    degraded = False
    layer: list[list[str]] = [tokens]
    for _ in range(MAX_NESTED_SHELL_DEPTH):
        next_layer: list[list[str]] = []
        for layer_tokens in layer:
            for body in _nested_shell_commands(layer_tokens):
                if body in seen:
                    continue
                seen.add(body)
                nested_tokens, nested_degraded = _tokenize_checked(body)
                degraded = degraded or nested_degraded
                bodies.append(body)
                body_tokens.extend(nested_tokens)
                next_layer.append(nested_tokens)
        if not next_layer:
            break
        layer = next_layer
    return bodies, body_tokens, degraded


def _is_env_long_option(name: str, full_name: str) -> bool:
    """`name`（`=` の手前まで切り出した長オプション名）が `full_name` の一意な
    省略形として受理されるか。

    GNU coreutils env は getopt_long なので長オプションを一意に定まるところまで
    縮めて書ける。受理下限は `--` + 1 文字（`len(name) >= 3`）。判定対象の
    `--split-string` / `--chdir` / `--unset` / `--argv0` はいずれも先頭 1 文字で
    一意に定まる（env の長オプション全般がそうではない: `--d` は `--debug` と
    `--default-signal` の両方に一致する）。`_is_chdir_long_option` と
    `_env_split_string_body` で共有する。
    """
    return len(name) >= 3 and full_name.startswith(name)


def _is_chdir_long_option(token: str) -> bool:
    """`env` の `--chdir` 長オプション（GNU の一意な省略形と `=value` 形を含む）か。

    GNU coreutils env は getopt_long なので `--chdir` を一意に定まるところまで
    縮めて書ける（`--ch` / `--chd` / `--c`。`env` の長オプションで `c` 始まりは
    `--chdir` だけ）。接頭一致だけで判定すると省略形を chdir と認識できず、
    束ね短オプションと同じ形で intent が落ちる。macOS の BSD env は長オプション
    自体を持たないので本機では実行不能形だが、判定は実行環境に依存させない
    （`env` があれば AC-4 (h) で cd_target は必ず None なので通知する方向にのみ倒れる）。
    """
    name = token.split("=", 1)[0]
    return _is_env_long_option(name, "--chdir")


def _env_split_string_body(tokens: list[str], index: int) -> tuple[str, int] | None:
    """`env` の split-string オプション（`-S` / `--split-string`）の本体と、
    本体を持つ token の位置を返す。

    `index` は `env` token の位置。走査は `index + 1` から前進し、`env` 1 出現に
    つき 1 回だけ回す。実 env の option 解析と同じ意味論で判定する（走査規則の
    正本。requirements.md § 実装方針「env option 走査規則」を写したもの）。

    1. `NAME=value` 形は環境変数代入として読み飛ばす
    2. `--` に到達したら次が operand なので打ち切る（本体なし）
    3. `--` 始まりの長オプション: `--split-string`（一意な省略形・`=value` 形を
       含む）なら本体とその位置を返す。`--chdir` / `--unset` / `--argv0`
       （required-argument）は `=` が無ければ次の token を値として読み飛ばす。
       `--block-signal` / `--default-signal` / `--ignore-signal`
       （optional-argument。`[=SIG]` の `=` 形でしか値を取らない）と
       その他の長オプションは option token だけ読み飛ばす
    3b. 単独の `-` は引数なし option として読み飛ばす。根拠は本ホストの BSD env
        （`man env` COMPATIBILITY: `-` を `-i` の synonym option として受理し、
        option 解析を続ける）。GNU では `-` 以降が option として解釈されず
        `env - -S …` は実行不能形なので、GNU に対しては過検出側（安全側）に倒れる
    4. `-` 始まりの短オプション束は左から 1 文字ずつ見る（実 env の getopt と
       同じ順序）。`S` に当たれば密着した残りか次の token を本体とし、その位置と
       あわせて返す。値取り文字（`ENV_VALUE_TAKING_SHORT_OPTION_CHARS`）に
       当たれば束の残りまたは次の token をその option の値として読み飛ばし、
       `S` を探さない
    5. 上記いずれにも当たらない token（operand = `env` が起動するコマンド名）で
       打ち切る

    本体の位置（`body_pos`）は、本体が同じ token 内（値密着・`=` 形）なら
    その option token 自身の位置、別 token 形なら次の token の位置になる。
    後続引数の始点は常に `body_pos + 1` であり、差し込み後の argv を組み立てる
    側（`_env_split_string_command`）がそこから読む。

    `_has_chdir_intent` も同じ `env` 以降を読むが、あちらは返り値が boolean の
    intent で、過検出が通知する方向にしか倒れないため打ち切らない。こちらは
    返り値が **差し込み後に再走査される argv（shell コマンド文字列）を組み立てる
    材料**で、打ち切らずに `env` より後ろの別プログラムの option 値
    （`grep -S "…"` の値など）まで拾うと過剰な通知になるため、operand で
    打ち切る。この非対称は意図したもの。

    手順 5 で早期に打ち切る代償として、未知の値取り option や識別子でない
    `NAME=` 形を operand と誤認した場合は検出漏れ（fail-open）方向に倒れる
    （CHANGELOG の Known limitations で開示）。
    """
    cursor = index + 1
    while cursor < len(tokens):
        tok = tokens[cursor]
        next_tok = tokens[cursor + 1] if cursor + 1 < len(tokens) else None
        if ENV_NAME_VALUE_RE.match(tok):  # 手順 1
            body, advance, offset = None, 1, 0
        elif tok == "--":  # 手順 2
            return None
        elif tok.startswith("--"):  # 手順 3
            body, advance, offset = _env_long_option_step(tok, next_tok)
        elif tok == "-":  # 手順 3b
            body, advance, offset = None, 1, 0
        elif tok.startswith("-"):  # 手順 4
            body, advance, offset = _env_short_option_step(tok, next_tok)
        else:  # 手順 5: operand
            return None
        if advance == 0:
            if body is None:
                return None
            return body, cursor + offset
        cursor += advance
    return None


def _env_long_option_step(
    tok: str, next_tok: str | None
) -> tuple[str | None, int, int]:
    """`_env_split_string_body` の手順 3（`--` 始まりの長オプション）を 1 token 分進める。

    返り値は (本体, 前進量, 本体位置の cursor からのオフセット)。前進量 0 は
    走査の終了を表し、呼び出し側はそのとき本体とその位置（本体が無ければ
    None）を返す。オフセットは `=value` 形なら 0（本体は同じ token）、
    別 token 形なら 1。
    """
    name, sep, inline = tok.partition("=")
    if _is_env_long_option(name, "--split-string"):
        # `--split-string=`（空値）も inline 扱いで本体 "" とする。空本体は
        # tokenize すると [] になり何も検出しない（例外も出さない）。
        if sep:
            return inline, 0, 0
        return next_tok, 0, 1
    if not sep and any(
        _is_env_long_option(name, opt) for opt in ENV_REQUIRED_ARG_LONG_OPTIONS
    ):
        return None, 2, 0
    return None, 1, 0


def _env_short_option_step(
    tok: str, next_tok: str | None
) -> tuple[str | None, int, int]:
    """`_env_split_string_body` の手順 4（`-` 始まりの短オプション束）を 1 token 分進める。

    束は左から 1 文字ずつ見る（実 env の getopt と同じ順序）。返り値の意味は
    `_env_long_option_step` と同じ。
    """
    size = len(tok)
    for pos in range(1, size):
        ch = tok[pos]
        if ch == "S":
            if pos + 1 < size:
                return tok[pos + 1:], 0, 0
            return next_tok, 0, 1
        if ch in ENV_VALUE_TAKING_SHORT_OPTION_CHARS:
            # 束の残りはこの option の値。残りが無ければ次の token が値。
            # token を切り出すのは値が要るときの 1 回だけ（1 文字ごとに切り出すと、
            # 長い束で解析時間が 2 乗になる）。
            return None, (1 if pos + 1 < size else 2), 0
    return None, 1, 0


def _has_chdir_intent(tokens: list[str]) -> bool:
    """走査範囲に cwd 変更 token（`cd` / `pushd` / `popd` / `chdir` / `env -C` / `env --chdir`）が
    1 つでもあるか（AC-18 の「chdir intent」。impl-gate 指摘を人間承認の案 (a)(1) で処置）。

    `cd_target` が None になる理由には「chdir の語彙が無い」と「語彙はあるが AC-4
    の受理条件で不採用にした」の 2 つがあり、hook 側で区別できないと後者が
    「実行先の signal が無い」扱いでプロセス cwd 由来 root により allow に抜ける
    （実シェルは chdir している）。後者を独立 signal として返し、hook が
    「解決できない実行先」として block() の通知へ倒せるようにする。

    `git -C` それ自体は chdir 語彙ではない（`gh` の実行先を動かさないので AC-4 の
    定義どおり対象外）。ただし走査範囲に `env` が現れて以降は、option 形の token を
    区別せず intent 扱いにするため、`env FOO=1 gh pr merge 7 && git -C <DIR> pull`
    のような並びは intent=True になる。`env` があれば AC-4 (h) で `cd_target` は
    必ず None なので、この過検出は通知する方向にしか倒れない。

    `env` の split-string 本体（`-S` / `--split-string`）を差し込み後の argv
    として組み立てる走査は `_env_split_string_body` / `_env_split_string_command`
    が別に持つ。あちらは返り値が再走査される argv（shell コマンド文字列）
    なので operand で打ち切り、こちらの「打ち切らない」方針とは異なる。
    """
    if any(token in CWD_CHANGE_WORDS for token in tokens):
        return True
    # `env` より後ろの token に `-C`（短オプション束・値密着を含む）/ `--chdir`
    # （GNU の一意な省略形を含む。`_is_chdir_long_option`）が
    # あれば intent。短オプションは束ねられる（macOS 実測で `env -iC <DIR>` /
    # `env -iC<DIR>` / `env -vC <DIR>` はいずれも chdir する）ので、接頭一致では
    # なく「`-` で始まる短オプション束に `C` を含む」で判定する。「`env` が起動する
    # コマンド名に到達したら打ち切る」判定は持たない: `-u NAME` / `-P path` /
    # `-S string` のように引数を別 token で取る option の引数をコマンド名と誤認して
    # 打ち切り、その後ろの `-C` を見落としていた（impl-gate Round 2 指摘。
    # `env -u X -C /B` が `env -C /B` と違って allow に抜けた）。走査範囲に `env` が
    # あれば AC-4 (h) で cd_target は必ず None なので、過検出は通知する方向にしか
    # 倒れない。最初の `env` 以降を 1 回走査すれば十分（`env` ごとのスライス走査に
    # よる O(n²) も同時に解消）。
    seen_env = False
    for token in tokens:
        if seen_env and (
            CHDIR_SHORT_OPTION_RE.match(token) or _is_chdir_long_option(token)
        ):
            return True
        if os.path.basename(token) == "env":
            seen_env = True
    return False


def _last_gh_basename_index(tokens: list[str]) -> int | None:
    """`tokens` のうち basename が `gh` である最後の token の位置を返す。

    `_env_split_string_command` の二重計上判定で、本体を持つ token 自身が
    既存経路の gh 探索に一致する場合に、本体 token 列から実行される gh より
    手前だけを argv に残すために使う。
    """
    for pos in range(len(tokens) - 1, -1, -1):
        if os.path.basename(tokens[pos]) == "gh":
            return pos
    return None


def _find_gh_pr_merge(
    tokens: list[str], start: int = 0, end: int | None = None
) -> int | None:
    """`tokens[start:end]` の中で `gh pr merge`（sub-command は cobra の規則で探す。
    `_locate_merge`）と読める `gh` token の位置を返す。見つからなければ `None`。

    `_scan_simple_command` と `_env_split_string_command` の二重計上判定が
    同じ判定を共有する（DRY）。探索位置だけでなく、sub-command 前の global
    flag の読み飛ばしと `pr merge` の照合も `tokens[:end]` の中に閉じる。
    `end` を同じ simple command の終端に置く呼び出し側が、制御演算子の向こうの
    `pr merge` をこの gh の sub-command と読み違えないため。
    """
    window = tokens[:end]
    memo: dict = {}
    for pos in range(start, len(window)):
        if os.path.basename(window[pos]) != "gh":
            continue
        if _locate_merge(window, pos, {}, memo) is not None:
            return pos
    return None


def _cutoff_matches_visible_gh(
    tokens: list[str],
    body_tokens: list[str],
    body_pos: int,
    after: int,
    end: int,
    visible: int,
) -> bool:
    """打ち切る前の差し込み後の argv で見つかる gh が、既存経路が見つけた
    `visible`（`tokens[body_pos:end]` の中で `gh … pr merge` と読める
    token の位置）と同じ token に対応するかを判定する。

    対応しなければ `_env_split_string_command` は打ち切らない（同じ merge
    を二重に数え、呼び出し側で `unresolvable` になる。fail-closed）。既存
    経路の gh 読みを検証せずに信用すると、`visible` が実は別の値（`-R` の
    値など、basename がたまたま `gh` になる token）を gh 本体と誤読して
    いた場合に、その誤読をそのまま採用してしまう。

    対応の定義:
    - argv の gh が本体由来（`body_tokens` の中）なら、次の 3 条件すべて:
      (1) `visible == body_pos`
      (2) 見つかった gh が本体 token 列のうち basename が `gh` の最後の
          token（`_last_gh_basename_index`）と同じ位置であること
      (3) その最後の gh が本体 token 列の**末尾**にあること（本体を
          tokenize した結果、最後の gh の後ろに token が残っていない）。
          本体の生文字列の末尾に語頭 `#` の語（`#/gh` 等）があると、
          bash 準拠のコメント除去で `#` 以降が丸ごと本体 token 列から
          落ち、見かけ上「最後の gh」が手前の gh に繰り上がる。実 env も
          `#` で始まる語から後ろを捨てるので、実行されるのは繰り上がった
          gh とその後ろの token（`-R` 等）だが、トップ層は生文字列全体の
          basename（末尾の `#/gh` 由来）を gh と読む。この食い違いを
          対応ありと誤認して打ち切ると、繰り上がった gh の後ろの flag が
          env の argv 差し込みから消えてしまう
    - argv の gh が後続引数由来（`tokens[after:end]` の中）なら、元の
      token 位置が `visible` と同じであること

    本体に `\\c`（実 env の「文字列の残りを無視する」記号）が含まれる形は
    ここに到達しない。`_env_split_string_command` が本体を tokenize する
    前に `\\c` の有無を見て `_EnvSplitStringBudgetExceeded` を送出する
    （tokenize 側は `\\c` を普通の文字 `c` に戻してしまい、対応の有無を
    確かめる材料にならないため）。
    """
    candidate = ["env", *body_tokens, *tokens[after:end]]
    found = _find_gh_pr_merge(candidate)
    if found is None:
        return False
    # candidate の中で後続引数 `tokens[after:end]` が始まる位置
    trailing_start = 1 + len(body_tokens)
    if found < trailing_start:
        last_gh = _last_gh_basename_index(body_tokens)
        return (
            visible == body_pos
            and last_gh is not None
            and found == 1 + last_gh
            # 最後の gh が本体 token 列の末尾にあるときだけ対応あり
            # （docstring 条件 (3)）。
            and last_gh == len(body_tokens) - 1
        )
    return after + (found - trailing_start) == visible


def _env_split_string_command(tokens: list[str], index: int) -> str | None:
    """本体を env の argv に差し込んだ後の argv を 1 本の文字列で返す。

    実 env の `-S` は、分割した本体を env の引数列のその位置に差し込み、
    option 解析を続ける（本ホスト `man env` § Details of -S (split-string)
    processing）。本体中の `-S` / `-C` は env option として読み直され、
    後続の元引数も同じ argv に続く。

    1. `_env_split_string_body` で `(body, body_pos)` を得る。無ければ
       `None`。後続引数の始点は `after = body_pos + 1`
    2. 本体に `\\c`（本ホスト `man env` の「文字列の残りを無視する」記号）が
       含まれていれば、tokenize せずに `_EnvSplitStringBudgetExceeded` を
       送出する。`\\c` の後ろが `gh` になるとは限らない一般形（`env -S 'gh
       \\cx' pr merge 7` 等）は、tokenize 側が `\\c` を普通の文字 `c` として
       残すため gh 探索そのものが崩れ、merge を検出できないまま素通りする。
       対応の有無を確かめられない形として、展開個数の上限超過と同じ扱いに
       倒す（人間承認 2026-09-11T17:40:53+09:00）
    3. 本体を tokenize する。縮退したら本体の生文字列をそのまま返す
       （後続引数は付けない。`_collect_nested_shell_layers` がこの本体で
       縮退を検知する境界を保つ）
    4. 後続引数の終端 `end` を、`after` 以降で最初の制御演算子の位置
       （無ければ末尾）に決める。同じ simple command の中だけを読む
    5. `tokens[body_pos:end]` の中に、既存経路の gh 探索と同じ判定で
       `gh … pr merge` と読める token（位置 `V`）があり、**かつ**
       `_cutoff_matches_visible_gh` で「打ち切る前の差し込み後の argv を
       同じ gh 探索でもう一度読んで見つかる gh が `V` と同じ token に
       対応する」と確認できたときだけ、`end = max(after, V)` に打ち切り、
       同じ merge を 2 回数えない。対応しなければ打ち切らない（既存経路の
       gh 読みが誤りだった可能性があるため、二重に数えて fail-closed に
       倒す）。`V == body_pos`（本体を持つ token 自身がその `gh`）で打ち
       切る場合は、本体 token 列のうち basename が `gh` の最後の token の
       手前までを argv に残す（その `gh` 自身と後続引数は入れない。本体中
       の env option・代入を保つため）
    6. `env` + 本体 token + `tokens[after:end]` を 1 token ずつ quote して
       返す。argv には `-S` より前の env option・代入を含めない
       （トップレベルの token 列で既に見えているため、再度含めると
       同じ `-S` を次の深さで無駄に再検出する）
    """
    found = _env_split_string_body(tokens, index)
    if found is None:
        return None
    body, body_pos = found
    if "\\c" in body:
        raise _EnvSplitStringBudgetExceeded()
    after = body_pos + 1
    # env は split-string の本体の改行を空白として読む（shell のコマンドの区切りではない）。
    body_tokens, body_degraded = shell_lexer.lex(body, None, FD_DIGITS)
    if body_degraded:
        return body
    end = after
    while end < len(tokens) and not _is_control_operator(tokens[end]):
        end += 1
    visible = _find_gh_pr_merge(tokens, body_pos, end)
    if visible is not None and _cutoff_matches_visible_gh(
        tokens, body_tokens, body_pos, after, end, visible
    ):
        end = max(after, visible)
        if visible == body_pos:
            last_gh = _last_gh_basename_index(body_tokens)
            body_tokens = body_tokens[:last_gh] if last_gh is not None else []
    return shlex.join(["env", *body_tokens, *tokens[after:end]])


def _chdir_signals(
    top_tokens: list[str], top_degraded: bool
) -> tuple[str | None, bool]:
    """(cd_target, cd_intent) を、入れ子 shell の展開 1 回で同時に求める。

    入れ子展開（`_collect_nested_shell_layers`）は `eval×n` で重い走査なので
    （IG-6）、cd_target と cd_intent で別々に走らせない。
    """
    nested_bodies, nested_tokens, nested_degraded = _collect_nested_shell_layers(
        top_tokens
    )
    cd_target = _select_cd_target(top_tokens, nested_bodies, nested_tokens)
    if nested_degraded:
        # 入れ子本体だけが縮退した形では、その本体の中の `cd` が語彙として数えられ
        # ない。数え落としたまま先頭の `cd` を「唯一の cwd 変更」として採用すると、
        # 実シェルが別の場所へ chdir しているのに AC-18 の照合が「一致」で通る
        # （`cd /A && bash -c ";cd /B; gh pr merge 7 --x 'q"` で /A の証跡が /B の
        # merge に使われる）。target は捨て、intent だけ立てて通知する方向へ倒す。
        return None, True
    if top_degraded:
        # 縮退した token 列は chdir 語彙も `gh` 本体も数え落とすので、この signal
        # からは何も主張しない。縮退そのものは `degraded` として別に返し、hook が
        # 解析未完走と同じ family（`parse-error`）へ倒す。ここで `cd_intent=True`
        # に倒すと、chdir 語彙が 1 つも無い入力まで「実行先が解決できない」という
        # 実態と違う reason で通知してしまう。
        return None, False
    return cd_target, _has_chdir_intent(top_tokens + nested_tokens)


# マージより後ろを切ってよいと言える形（許可リスト）。外れたら全体を見る（main と同じ判定）。
# 文字はマージを囲む構文・置換・行継続を作れないものだけを許し、heredoc・単独の `&`・
# bash（`compgen -k`）と zsh の `repeat`・`foreach`・`end`・後で走らせる `trap`・`sched` の語・
# 2 つ以上の `merge` の語を除く。
_CUTTABLE_CHARS = re.compile(r"[\w\s./:=@%+,'\"&|;~<>-]*")
_CUT_BLOCKERS = re.compile(
    r"<<|(?<![&>])&(?![&>])|(?<![\w./-])(?:if|then|else|elif|fi|case|esac|for|select|while"
    r"|until|do|done|in|function|time|coproc|repeat|foreach|end|trap|sched)(?![\w./-])"
)
_MERGE_WORD = re.compile(r"(?<![\w./-])merge(?![\w./-])")


def _through_merge_segment(command: str, tokens: list[str], degraded: bool) -> list[str]:
    """マージを含む segment の終わりまでの token 列（後ろの `cd` は実行先を変えない）。

    `command` が許可リストの形でないとき、入れ子 shell があるとき、マージが 2 つあるときは
    切らずに全体を返す。
    """
    if (
        degraded
        or not _CUTTABLE_CHARS.fullmatch(command)
        or _CUT_BLOCKERS.search(command)
        or len(_MERGE_WORD.findall(command)) != 1
        or _nested_shell_commands(tokens)
    ):
        return tokens
    # マージより前の区切りが `&&`・`;` だけのときに限る（パイプ・`||` の前の cd は main と同じく数える）。
    cut, start, chained = None, 0, True
    for i in range(len(tokens) + 1):
        if i < len(tokens) and not _is_control_operator(tokens[i]):
            continue
        if _find_gh_pr_merge(tokens[start:i]) is not None:
            if cut is not None or not chained:
                return tokens
            cut = i
        if cut is None and i < len(tokens) and tokens[i] not in ("&&", ";"):
            chained = False
        start = i + 1
    return tokens if cut is None else tokens[:cut]


def _extract_cd_target(top_tokens: list[str]) -> str | None:
    """マージを含む segment までを見て、採用可能な単一 `cd <絶対パス>` があれば返す（AC-4 (a)〜(i)）。

    1 つでも外れたら None。切り出せない形では `gh pr merge` 探索と同一の走査範囲
    （トップレベル token 列 + 入れ子 `bash -c` / `eval` 本体を
    `MAX_NESTED_SHELL_DEPTH` まで再帰的に展開したもの）を見る。`top_tokens`
    は呼び出し側（`parse_gh_pr_merge`）が既に計算済みのものを渡す
    （command 文字列を渡す形だと `_strip_heredoc_bodies` / `_tokenize` を
    `_scan_tokens` 側と二重に走らせてしまうため）。

    入れ子展開が env split-string の展開個数の上限を超えた場合は、
    「対象を決められない」ことを表す `None` を返す（`_nested_shell_commands`
    が送出する `_EnvSplitStringBudgetExceeded` をここで捕捉する）。
    """
    # 縮退の有無は本番経路（`parse_gh_pr_merge`）が別に扱う。ここは token 列を
    # 受け取る形なので縮退したかを知りようがなく、`False` を渡すのは「この関数は
    # 縮退を判定材料にしない」の明示（既定引数にすると本番から呼ばれたときに
    # 無言で落ちる）。
    try:
        # 元の文字列を受け取らないので、token を空白でつないだ文字列で許可リストを見る。
        return _chdir_signals(
            _through_merge_segment(" ".join(top_tokens), top_tokens, False), False
        )[0]
    except _EnvSplitStringBudgetExceeded:
        return None


def _select_cd_target(
    top_tokens: list[str], nested_bodies: list[str], nested_tokens: list[str],
) -> str | None:
    """`_extract_cd_target` の判定本体（展開済みの入れ子層を受け取る）。"""
    # (g) 走査範囲全体（トップレベル token 列 + 入れ子本体の生文字列）に `$` / `` ` ``。
    blob = " ".join(top_tokens) + " " + " ".join(nested_bodies)
    if "$" in blob or "`" in blob:
        return None

    # (h) 走査範囲に `env` が basename 一致で 1 つでも現れたら不採用（`/usr/bin/env` を含む）。
    if any(os.path.basename(t) == "env" for t in top_tokens + nested_tokens):
        return None

    top_hits = [(i, t) for i, t in enumerate(top_tokens) if t in CWD_CHANGE_WORDS]
    nested_hits = [t for t in nested_tokens if t in CWD_CHANGE_WORDS]

    # (a)(f) 走査範囲全体で cwd 変更 token がちょうど 1 つ。入れ子側にしか
    # 無ければトップレベル先頭にはなり得ないので不採用。
    if len(top_hits) + len(nested_hits) != 1 or not top_hits:
        return None

    index, word = top_hits[0]
    # (i) その 1 つが `cd`（`pushd` / `popd` 単独形は None）。
    if word != "cd":
        return None
    # (b) トップレベル先頭 segment の先頭 token。
    if index != 0 or index + 1 >= len(top_tokens):
        return None

    arg = top_tokens[index + 1]
    # (c)(d)(e) 絶対パスで `..` パス成分・`*` / `?` を含まない。
    if not arg.startswith("/"):
        return None
    if ".." in arg.split("/"):
        return None
    if "*" in arg or "?" in arg:
        return None
    # 制御文字（改行・タブなど）を含む引数は採らない。hook への出力は改行・タブを
    # 空白に置き換えるので、照合するパスと実際に移る先が別になる（語の途中の
    # 行継続 `a\<改行>b` は、シェルでは `ab` になる）。intent は残るので通知する側。
    if any(ord(c) < 0x20 or c == "\x7f" for c in arg):
        return None
    return arg


# `run-merge-gate-hook.sh` が **判定に消費する** signal の正本。
# 実測した fail-open の root cause は「parser が repo 決定要因を返しているのに、
# hook が変数へ代入するだけで一度も読まない」ことだった。同じ形の再発を構造で
# 止めるため、
# 消費する signal と「意図的に消費しない signal（+ その理由）」をここで宣言し、
# tests/test_merge_gate_hook_contracts.py の HookSignalConsumptionContractTests が
# 「parse 結果の全 key がどちらかに登録されているか」「消費 signal が hook で
# emit され、shell 変数として実際に読まれているか」を機械検査する。
# 新しい signal を parse 結果へ足したら、この 2 集合のどちらかへ登録しない限り
# テストが落ちる（= 消費漏れが CI 緑をすり抜けない）。
HOOK_CONSUMED_SIGNALS = (
    "is_merge",
    "pr_number",
    "pr_url",
    "repo_flag",
    "unresolvable",
    "env_repo_conflict",
    "admin",
    "cd_target",
    "cd_intent",
    "degraded",
    "ledger_targets",
)
LEDGER_TARGET_KEYS = ("repo_flag", "pr_number", "pr_url")
HOOK_UNCONSUMED_SIGNALS = {
    # ブランチ名は design.md § Sensitive Data / Masking Policy の禁止 token
    # （block reason にも hook 所有ログにも出せない）。値そのものは使わず、
    # 同じ位置引数から立つ `unresolvable` を hook 側の判定材料にする。
    "branch_arg": "masking policy によりブランチ名は判定材料に使わない（unresolvable で代替）",
}


# heredoc の所有 pipeline の判定（`bash <<EOF` / `cat <<EOF | bash` の本文は実行される）は芯と共有する。
_feeds_shell_interpreter = shell_lexer.feeds_shell_interpreter


def _strip_heredoc_bodies(text: str) -> str:
    """heredoc 本文を落とす。ただし interpreter へ食わせる本文は評価対象に残す。

    本文除去は pre-PR gate から引き継いだ過検出緩和（`git commit -F - <<MSG …
    gh pr create … MSG` の散文を誤って通知しない）。だが heredoc は **コマンドを
    実行する経路でもある**ので、緩和したままだと `bash <<EOF … gh pr merge … EOF`
    が gate を丸ごと素通りする。データとして渡す形（`git commit
    -F -` 等）と interpreter への入力を **heredoc ごとに** 所有 pipeline 単位で
    切り分け、後者の本文だけを制御演算子で区切った別 segment として
    末尾へ戻す（`_split_command_segments` が introducer 行の token 列と混ぜずに
    走査できる形）。
    """
    lines = text.split("\n")
    kept: list[str] = []
    executed: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        for match in HEREDOC_RE.finditer(line):
            word = match.group(2)
            runs_body = _feeds_shell_interpreter(line, match.start())
            body: list[str] = []
            while index < len(lines) and lines[index].strip() != word:
                body.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            if runs_body and body:
                executed.append(";")
                executed.extend(body)
    return "\n".join(kept + executed)


# 引用符・エスケープ由来の演算子文字だけから成る token の印（`_is_operator` は演算子と見なさない）。
_QuotedWord = shell_lexer.QuotedWord
_is_operator = shell_lexer.is_operator


def _is_redirect_operator(token: str) -> bool:
    """`<` `>` `>>` `>&` `<&` のようなリダイレクト演算子か（オペランドを 1 つ取る）。"""
    return _is_operator(token) and any(ch in REDIRECT_OPERATOR_CHARS for ch in token)


def _is_control_operator(token: str) -> bool:
    """`;` `&&` `||` `|` `&` のような simple command の区切りか。

    `(` `)` は含めない（`$(echo gh) pr merge 7` の再走査を切らないため）。
    引用符・エスケープで守られていた演算子文字（`_QuotedWord`）は区切りと
    見なさない。
    """
    if isinstance(token, _QuotedWord):
        return False
    return bool(token) and all(ch in CONTROL_OPERATOR_CHARS for ch in token)


_pick_operator_masks = shell_lexer.pick_operator_masks
_mask_quoted_operators = shell_lexer.mask_quoted_operators


def _split_command_segments(tokens: list[str]) -> list[list[str]]:
    """制御演算子で token 列を simple command 単位へ分割する。

    `gh pr merge 7 && gh pr merge 999` のように 1 行に複数の merge が並ぶ形で、
    2 本目以降を評価対象から落とさないための前処理。
    """
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if _is_control_operator(token):
            if current:
                segments.append(current)
            current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def _mask_for_fd(text: str) -> tuple[str, dict[str, str]]:
    """行継続とコメントを処理し引用符の中の演算子を退避する（2〜10 桁の密着 fd 番号の判定と zsh の読みで共有）。

    行継続は芯と同じく bash の規則で消す（`gh pr merge 1\\` + 改行 + `2>x` の `12>` を見る）。
    """
    text = shell_lexer.normalize(text)
    masks = _pick_operator_masks(text)
    return _mask_quoted_operators(text, masks), masks


def _split_multi_digit_fd(text: str) -> str:
    """引用符の外の 2〜10 桁の密着 fd 番号を、リダイレクトから離した語にする（zsh の読み）。"""
    masked, masks = _mask_for_fd(text)
    split = MULTI_DIGIT_FD_RE.sub(r"\1\2 ", masked)
    return split.translate({ord(m): original for original, m in masks.items()})


def _value_position(tokens: list[str], cursor: int) -> int | None:
    """flag の値の位置を返す（`tokens[cursor]` の次。リダイレクトは argv から除かれるので飛ばす）。

    値が無ければ `None`。
    """
    cursor += 1
    while cursor < len(tokens) and _is_redirect_operator(tokens[cursor]):
        cursor += 2
    return cursor if cursor < len(tokens) else None


def _read_merge_flag(tokens: list[str], cursor: int, result: dict) -> int:
    """`tokens[cursor]`（`-` で始まり `-`・`--` ではない token）を `gh pr merge` の flag の
    表と pflag の規則で読み、次の cursor を返す。

    - 長い形は `--name` と `--name=value`。値を取る flag に `=` が無ければ次の token が値
    - 短い形は 1 文字ずつ読む（束ね）。値を取る文字に当たったら、残りが `=x` なら `x`、
      残りがあれば残り、無ければ次の token が値。値を取らない文字の後の `=x` も値として
      token の残りを読む（`-s=false`）。token を切り出すのは値が要るときの 1 回だけ
      （1 文字ごとに切り出すと、長い束ねで解析時間が 2 乗になる）
    - `-R` / `--repo` の値は repo_flag に入れる（後勝ち）。`--admin` は偽の値でなければ admin
    - 表に無い flag・値の無い値を取る flag は unresolvable を立て、その 1 token だけ進む
      （次の token は位置引数の候補として残す）
    """
    token = tokens[cursor]
    if token.startswith("--"):
        name, eq, value = token[2:].partition("=")
        if name in MERGE_VALUE_LONG_FLAGS:
            if not eq:
                position = _value_position(tokens, cursor)
                if position is None:
                    result["unresolvable"] = True
                    return cursor + 1
                cursor = position
                value = tokens[cursor]
            if name == "repo":
                result["repo_flag"] = value
            return cursor + 1
        if name in MERGE_BOOL_LONG_FLAGS:
            if name == "admin":
                result["admin"] = not eq or value not in FALSE_BOOL_VALUES
            return cursor + 1
        result["unresolvable"] = True
        return cursor + 1
    size = len(token)
    for pos in range(1, size):
        char = token[pos]
        if char not in MERGE_BOOL_SHORT_FLAGS and char not in MERGE_VALUE_SHORT_FLAGS:
            result["unresolvable"] = True
            return cursor + 1
        after = pos + 1
        if after + 1 < size and token[after] == "=":
            value = token[after + 1:]
        elif char in MERGE_BOOL_SHORT_FLAGS:
            continue
        elif after < size:
            value = token[after:]
        else:
            position = _value_position(tokens, cursor)
            if position is None:
                result["unresolvable"] = True
                return cursor + 1
            cursor = position
            value = tokens[cursor]
        if char == "R":
            result["repo_flag"] = value
        return cursor + 1
    return cursor + 1


def _find_sub_command(
    tokens: list[str], start: int, name: str, result: dict, memo: dict | None = None
) -> int | None:
    """cobra の探索（`Command.Find` の `stripFlags`）で `name`（`pr`・`merge`）の位置を返す。

    gh が sub-command を見つける規則を写す。この段は merge の flag の表ではなく、その階層の
    flag 集合で読む（gh 2.93.0 の実行で確かめた）。

    - `--`（token として現れたもの）で止まる。flag の値として飛ばされた `--` では止まらない
    - `-` と空の token は読み飛ばす（sub-command の候補にならない）
    - `=` を含む flag と 3 文字以上の短い束ね（`-st`）は、値を取らない 1 token として飛ばす
    - 2 文字の短い flag（`-s`・`-R`）と、`=` の無い長い flag（`--admin`）は、`--help`
      （と root の `--version`）を除いて次の token を値として飛ばす
    - flag でも `name` でもない token が先に来たら、別の sub-command（見つからない）

    gh が別の版で値を取らない flag と読むときに merge を見失わないよう、値として飛ばした
    token が `name` そのものなら、そこを `name` として読み unresolvable を立てる（通知する側）。
    リダイレクトとそのオペランドは argv に入らないので読み飛ばす。演算子 token
    （`$(echo gh) pr merge 7` の `)` など）も飛ばして、sub-command 照合に届かせる。

    `memo` は `_find_gh_pr_merge` が、gh の token ごとの探索が同じ位置を何度も歩かないために渡す
    （結果は窓・位置・`name` だけで決まる。gh の token が並ぶ入力で探索が 2 乗になり、hook の
    timeout を超えるのを防ぐ）。結果を書く呼び出し（`result` が実際の解析結果のとき）には渡さない
    （メモに当たった経路では、unresolvable を立てる処理が走らない）。
    """
    bool_long = FIND_BOOL_LONG_FLAGS[name] if name in FIND_BOOL_LONG_FLAGS else frozenset()
    visited: list[tuple[int, str]] = []
    found: int | None = None
    cursor = start
    while cursor < len(tokens):
        if memo is not None and (cursor, name) in memo:
            found = memo[(cursor, name)]
            break
        visited.append((cursor, name))
        token = tokens[cursor]
        if _is_redirect_operator(token):
            cursor += 2
            continue
        if _is_operator(token) or token in ("", "-"):
            cursor += 1
            continue
        if token == name:
            found = cursor
            break
        if token == "--":
            break
        if token.startswith("--"):
            takes_value = "=" not in token and token[2:] not in bool_long
        elif token.startswith("-"):
            takes_value = len(token) == 2 and "=" not in token
        else:
            break
        if not takes_value:
            cursor += 1
            continue
        position = _value_position(tokens, cursor)
        if position is None:
            break
        if tokens[position] == name:
            result["unresolvable"] = True
            found = position
            break
        cursor = position + 1
    if memo is not None:
        for key in visited:
            memo[key] = found
    return found


def _locate_merge(
    tokens: list[str], gh_pos: int, result: dict, memo: dict | None = None
) -> list[str] | None:
    """`tokens[gh_pos]` の gh が `pr merge` を起動するなら、merge の表で読む引数列を返す。

    sub-command は `_find_sub_command`（cobra の探索）で見つける。引数列は、gh の後の全 token
    から見つけた `pr` と `merge` の 2 token を除いた残り（cobra の `argsMinusFirstX` と同じ。
    `gh -R other/x pr merge 7` の `-R` も、`gh pr -st merge fix 7` の `-st` も、merge の flag
    として読む）。sub-command の探索で unresolvable を立てることがある（result に書く）。
    """
    pr_pos = _find_sub_command(tokens, gh_pos + 1, "pr", result, memo)
    if pr_pos is None:
        return None
    merge_pos = _find_sub_command(tokens, pr_pos + 1, "merge", result, memo)
    if merge_pos is None:
        return None
    return tokens[gh_pos + 1:pr_pos] + tokens[pr_pos + 1:merge_pos] + tokens[merge_pos + 1:]


def _read_pr_url(token: str) -> tuple[str, bool] | None:
    """gh が PR の URL と読む token を `(正準形の URL, 対象を名指しできるか)` にする。読まなければ `None`。

    host を問わず、`?`・`#` を落とした `//authority` の後の path を読む。正準形は番号を前方一致で読んだ
    結果で、名指しできる形では gh が実際に merge する PR と同じ。名指しできるのは、token が空白を含まず、
    host が `github.com`（下位の host・port・userinfo が無く、path に `%xx` も無い）で、番号の後が終端か
    `/` のときだけ。それ以外は URL を返したうえで、呼び出し側が対象を決められない扱いにする
    （語の途中の行継続や shell の展開を含む形では、gh の対象と違うことがある）。
    """
    words = token.split(None, 1)
    if not words or not URL_SCHEME_RE.match(words[0]):
        return None
    rest = re.split(r"[?#]", words[0].partition(":")[2], maxsplit=1)[0]
    authority = ""
    if rest.startswith("//"):
        authority, slash, tail = rest[2:].partition("/")
        rest = slash + tail
    path = unquote(rest)
    matched = PR_URL_PATH_RE.match(path)
    if not matched:
        return None
    owner, repo, number = matched.groups()
    named = (
        token == words[0] and authority.lower() == "github.com" and "%" not in rest
        and path[matched.end():matched.end() + 1] in ("", "/")
    )
    return f"https://github.com/{owner}/{repo}/pull/{number.lstrip('0') or '0'}", named


def _read_pr_target(token: str) -> tuple[str, str, bool] | None:
    """位置引数を gh と同じ規則で読み、`("url", 正準形の URL, 名指しできるか)` か `("number", 番号, True)` を返す。

    URL は `_read_pr_url`、番号は `#` を落とした `Atoi`。どちらでもなければ `None`（branch 名）。
    番号は先頭の 0 を落とした ASCII の数字。
    """
    url = _read_pr_url(token)
    if url:
        return "url", url[0], url[1]
    matched = PR_NUMBER_RE.fullmatch(token)
    if matched:
        return "number", matched.group(1).lstrip("0") or "0", True
    return None


def _is_repo_overriding_env(name: str, value: str) -> bool:
    """`GH_REPO` / `GH_HOST` の値が対象 repo の解決先を実際に動かすか。

    `GH_HOST=github.com` は既定ホストの明示にすぎず、解決先は変わらない。空値も
    未設定と同じ。ここを「設定されていれば conflict」で判定すると、明示しただけで
    `pr-target-unresolvable` の恒久的な不足の通知になる。`GH_REPO` は値によらず対象 repo を
    上書きするので常に conflict とする。
    """
    if name == "GH_HOST":
        return bool(value) and value != DEFAULT_GH_HOST
    return bool(value)


def _has_env_repo_prefix(tokens: list[str]) -> bool:
    """gh 起動前の command-prefix 代入（`GH_REPO=x gh ...`）を検出する。

    `env GH_REPO=x gh ...` のように gh の手前に何 token 挟まっても、gh に到達
    するまでに現れた `GH_REPO=`/`GH_HOST=` 代入をすべて見る。
    """
    for token in tokens:
        matched = ENV_ASSIGNMENT_RE.match(token)
        if matched and _is_repo_overriding_env(matched.group(1), matched.group(2)):
            return True
        if os.path.basename(token) == "gh":
            break
    return False


def _consume_merge_args(tokens: list[str], start: int, result: dict) -> None:
    """`gh pr merge` の引数列（`_locate_merge` の戻り値）を走査して result を埋める。

    - flag は `_read_merge_flag`（gh の表と pflag の規則）で読む。`--` の後は全部位置引数
    - 位置引数は URL / PR番号 / ブランチ名のいずれかへ振り分ける。gh は位置引数を 1 つまでしか受け付けないので、
      2 つ以上なら unresolvable を立て、読めた URL・番号を全部 `("url" | "number", 値)` の list で返す（台帳の照合用。
      それ以外は `None`）
    - リダイレクト（`<` `>` `>&` …）は **オペランドごと読み飛ばして走査を継続**する。shell はリダイレクトを
      simple command の任意位置に置けるので、ここで打ち切ると後ろの位置引数が見えなくなり「引数省略形」と誤認する
    """
    cursor = start
    positionals = 0
    read: list[tuple[str, str]] = []
    flags_ended = False
    while cursor < len(tokens):
        t = tokens[cursor]
        if _is_redirect_operator(t):
            cursor += 2
            continue
        if _is_operator(t):
            cursor += 1
            continue
        if not flags_ended and t == "--":
            flags_ended = True
            cursor += 1
            continue
        if not flags_ended and t.startswith("-") and t != "-":
            cursor = _read_merge_flag(tokens, cursor, result)
            continue
        # 位置引数: URL / PR番号 / ブランチ名のいずれか
        positionals += 1
        target = _read_pr_target(t)
        read += [target[:2]] if target else []
        if target and target[0] == "url":
            result["pr_url"] = target[1]
            if not target[2]:
                result["unresolvable"] = True
        elif target:
            result["pr_number"] = target[1]
        else:
            result["branch_arg"] = t
            result["unresolvable"] = True
        cursor += 1
    if positionals > 1:
        result["unresolvable"] = True
        return read
    return None


def _tokenize(text: str) -> list[str]:
    """text を字句解析の芯（shell_lexer.lex）で token 化する。"""
    tokens, _degraded = _tokenize_checked(text)
    return tokens


def _tokenize_checked(text: str) -> tuple[list[str], bool]:
    """`_tokenize` の結果と「shlex が縮退したか」を返す。

    行継続（bash の規則）と語頭コメントを落とし、引用符の外の改行を `;`（コマンドの区切り）にし、
    引用符の中の演算子文字を `_QuotedWord` にし、密着した 1〜10 桁の fd 番号を落として割る
    （`shell_lexer.lex`）。閉じない引用符で shlex が割れない片は、引用符を見ずに割って縮退を返す。
    縮退した token 列では演算子と密着した `cd`（`;cd /B`）を数え落としうるので、縮退そのものを
    「実行先を解決できない」signal として上へ伝える（AC-18 の guard をアポストロフィ 1 つで
    無効化させない）。退避先を使い切ったときの `ValueError` は縮退に変えずに伝える。
    """
    return shell_lexer.lex(text, ";", FD_DIGITS)


def _nested_shell_commands(tokens: list[str]) -> list[str]:
    """`bash -c '<command>'` / `eval '<command>'` / `env -S '<command>'` を
    差し込み後の argv として展開し、その script 本体（または argv）を返す。

    posix shlex はクォートを剥がすため、`bash -c 'gh pr merge 7'` の script は 1 token に潰れて素通りしていた。
    **shell interpreter の引数に限定して**再解釈する（`git commit -m "gh pr merge を修正"` のような散文引数まで
    再走査すると、commit・CHANGELOG の更新が誤って不足として通知される。heredoc の過検出の緩和と同じ理由）。

    env の split-string オプションで展開した個数が 1 回の呼び出しで
    `MAX_ENV_SPLIT_STRINGS_PER_LAYER` を超えたら、展開をやめて `_EnvSplitStringBudgetExceeded` を送出する（呼び出し元の
    `_collect_nested_shell_layers` / `_scan_tokens` は捕捉せず、
    `parse_gh_pr_merge` / `_extract_cd_target` まで伝播させる）。
    """
    nested: list[str] = []
    split_string_count = 0
    for index, token in enumerate(tokens):
        name = os.path.basename(token)
        if name in SHELL_INTERPRETERS:
            script = _shell_c_operand(tokens, index)
            if script is not None:
                nested.append(script)
        elif name == "eval" and index + 1 < len(tokens):
            nested.append(" ".join(tokens[index + 1:]))
        elif name == "env":
            command = _env_split_string_command(tokens, index)
            if command is not None:
                split_string_count += 1
                if split_string_count > MAX_ENV_SPLIT_STRINGS_PER_LAYER:
                    raise _EnvSplitStringBudgetExceeded()
                nested.append(command)
    return nested


def _shell_c_operand(tokens: list[str], index: int) -> str | None:
    """shell interpreter の引数列を走査し、`-c` の script 本体を返す。

    短フラグ束（`-lc`・`+e`）に `c` が含まれるときだけ `-c` とする。値を取る束（`-euo pipefail`）は
    値ごと、長い option（`--norc`）は 1 語、リダイレクト（`2>/dev/null`）はオペランドごと飛ばす。
    """
    cursor = index + 1
    while cursor < len(tokens):
        token = tokens[cursor]
        if _is_redirect_operator(token):
            cursor += 2
            continue
        if SHORT_FLAG_RE.match(token):
            if "c" in token:
                return tokens[cursor + 1] if cursor + 1 < len(tokens) else None
            cursor += 2 if token[-1] in VALUE_TAKING_SHELL_FLAG_CHARS else 1
            continue
        if token in VALUE_TAKING_SHELL_LONG_FLAGS:
            cursor += 2
            continue
        if token.startswith("--") and token != "--":
            cursor += 1
            continue
        # `--` / 非フラグ token（script ファイル名など）に当たったら `-c` は無い。
        return None
    return None


def _scan_simple_command(tokens: list[str], result: dict) -> bool:
    """1 つの simple command から `gh pr merge` を検出して result を埋める。"""
    index = _find_gh_pr_merge(tokens)
    if index is None:
        return False
    result["is_merge"] = True
    # merge ごとの組（-R・番号・URL）を台帳の照合に残す。読む前に空にし、組を足した後で空のものだけ前の値に戻す。
    # sub-command の前後の flag も、merge の表で一緒に読む（repo_flag は後勝ち）。
    before = {key: result[key] for key in LEDGER_TARGET_KEYS}
    result.update(dict.fromkeys(LEDGER_TARGET_KEYS))
    read = _consume_merge_args(_locate_merge(tokens, index, result), 0, result)
    if read is None:
        result["ledger_targets"].append(tuple(result[key] for key in LEDGER_TARGET_KEYS))
    else:
        # 位置引数が 2 つ以上（改行で区切った merge など）は番号と -R の対応を決められない。番号は repo を決めない印で残す。
        result["ledger_targets"] += [(None, None, value) if kind == "url" else ("*", value, None) for kind, value in read]
    for key in LEDGER_TARGET_KEYS:
        result[key] = result[key] or before[key]
    return True


def _scan_tokens(tokens: list[str], result: dict, depth: int = 0, text: str = "") -> bool:
    if _has_env_repo_prefix(tokens):
        # token 列の command-prefix（`GH_REPO=x gh ...` / `env GH_REPO=x gh ...`）。
        result["env_repo_conflict"] = True

    # 制御演算子で区切った simple command を **全部** 走査する。
    # 1 本目で return すると `gh pr merge 7 && gh pr merge 999` の 2 本目が
    # 評価されず、記録済みの別 PR 向け承認で allow される。
    merges = 0
    for segment in _split_command_segments(tokens):
        if _scan_simple_command(segment, result):
            merges += 1
    # 入れ子 shell も同じ理由で「見つかったら打ち切り」にしない
    # （`gh pr merge 7 && bash -c 'gh pr merge 999'` の 2 本目）。
    if depth < MAX_NESTED_SHELL_DEPTH:
        for nested in _nested_shell_commands(tokens):
            if _scan_tokens(_tokenize(nested), result, depth + 1, nested):
                merges += 1
    # 2〜10 桁の fd 番号は shell で読みが割れる。読めた番号・URL は台帳の照合に残す（`_consume_merge_args` と同じ）。
    if merges and MULTI_DIGIT_FD_RE.search(_mask_for_fd(text)[0]):
        result["unresolvable"] = True
    if merges > 1:
        # 1 つの result で複数の対象は表現できない。「対象を決められない」（番号・URL を空にして
        # unresolvable）へ揃え、hook の `pr-target-unresolvable` に倒す（AC-10）。台帳は ledger_targets で照合する。
        result["unresolvable"] = True
        result["pr_number"] = None
        result["pr_url"] = None
    return merges > 0


def parse_gh_pr_merge(command: str, payload_cwd: str, process_cwd: str) -> dict:
    result = {
        "is_merge": False,
        "pr_number": None,
        "pr_url": None,
        "repo_flag": None,
        "branch_arg": None,
        "admin": False,
        "unresolvable": False,
        "cd_target": None,
        "cd_intent": False,
        "degraded": False,
        "ledger_targets": [],
        "env_repo_conflict": any(
            _is_repo_overriding_env(name, os.environ.get(name) or "")
            for name in ("GH_REPO", "GH_HOST")
        ),
    }
    if not command:
        return result
    # 縮退の判定は **元のコマンド** に対して行う。heredoc の切り落としは切断面でクォートを開いたままにする
    # （`bash -lc 'git commit -F - <<MSG`）が、これは解析の副作用で、元のコマンドは valid にクォートされている。
    # 切り落とし側で判定すると、commit message に `gh pr merge` を含むだけの正当なコマンドが不足として通知される。
    stripped = _strip_heredoc_bodies(command)
    tokens, _stripped_degraded = _tokenize_checked(stripped)
    # 縮退を signal にできるのは **heredoc を含まないコマンド** に限る。切り落とし後を基準にすると、引用符の内側の
    # introducer で閉じ引用符を落とす形（`bash -lc 'git commit -F - <<MSG …MSG'`）が、元コマンドを基準にすると本文の
    # アポストロフィ（`git commit -F - <<'MSG'\nDon't merge yet\nMSG`）が縮退扱いになる。
    # どちらも通知する方向の誤検知なので、heredoc を含む形では signal を立てない
    # （その形の扱いは origin/main と同じままで、下の Known limitations に開示する）。
    # 判定はトップレベルの tokenize だけを見る。入れ子本体まで含めると `bash -c "echo don't"` のような
    # valid な形まで縮退扱いになる。入れ子本体が shlex で割れない形は origin/main でも merge 検出に届かない。
    result["degraded"] = not HEREDOC_RE.search(command) and _tokenize_checked(command)[1]
    try:
        result["cd_target"], result["cd_intent"] = _chdir_signals(
            _through_merge_segment(command, tokens, result["degraded"]), result["degraded"]
        )
        _scan_tokens(tokens, result, text=stripped)
        if result["unresolvable"] and not (result["pr_number"] or result["pr_url"]) and MULTI_DIGIT_FD_RE.search(_mask_for_fd(stripped)[0]):
            # zsh の読み（2〜10 桁の密着形は語）で読めた番号・URL も、台帳の照合に残す。
            zsh = dict(result, ledger_targets=[])
            _scan_tokens(_tokenize(_split_multi_digit_fd(stripped)), zsh)
            result["pr_number"], result["pr_url"] = zsh["pr_number"], zsh["pr_url"]
            result["ledger_targets"] += zsh["ledger_targets"]
    except _EnvSplitStringBudgetExceeded:
        # env split-string の本体を確かめられず（展開個数の上限超過、本体の `\c`）解析を完走できない。
        # 「対象を決められない」（`merges > 1` と同じ）へ倒す。先に読んだ ledger_targets は残す（通知する側にだけ効く）。cd_target は
        # 確定できず、cd_intent を False のまま残すと「実行先を確定できない」遮断を通り抜けるので True 側に倒す（人間承認 2026-09-11T17:40:53+09:00）。
        result["is_merge"] = True
        result["unresolvable"] = True
        result["pr_number"] = None
        result["pr_url"] = None
        result["cd_target"] = None
        result["cd_intent"] = True
    return result
