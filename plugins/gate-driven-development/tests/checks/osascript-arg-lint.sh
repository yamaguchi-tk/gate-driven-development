#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: osascript-arg-lint"

# design § enforcement point 2 / ADR-4 の 2 規約を静的に固定する。
#
#   1. `osascript` へ `-e` で文字列を渡さない（AppleScript injection 面の再生産）
#   2. `osascript -` の heredoc 区切りは**クォートする**（`<<'DELIM'`）
#
# 2 が静的検査の owner なのは、実装のレビューの advisory による ——
# 変異 C7（quoted -> unquoted）は**現時点では真の等価変異**なので stub 方式の
# テストでは SURVIVED にしかならないが、AppleScript 本文に `$` を 1 文字足した
# 瞬間に規約が黙って壊れる。本文の中身に依存せず「クォートされていること」だけを
# 見る静的検査でしか捕まえられない。
#
# コメント行（先頭が `#`）は対象外にする。規約そのものを各 hook のヘッダで
# 説明できなくなるため。実際の呼び出しは行頭 `#` の後ろには置けない。

target_dir="$ROOT/hooks/scripts"
if [[ ! -d "$target_dir" ]]; then
  echo "MISSING DIR: hooks/scripts"
  echo "FAIL: osascript-arg-lint"
  exit 1
fi

fail=0
seen_invocations=0

while IFS= read -r file; do
  lineno=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    lineno=$((lineno + 1))
    # コメント行は対象外
    [[ "${line#"${line%%[![:space:]]*}"}" == \#* ]] && continue
    [[ "$line" == *osascript* ]] || continue

    # ------------------------------------------------------------------
    # 判定窓は「**その行の各 `osascript` の引数リスト**」。2 つの軸がある:
    #
    #   始点 — 行内の `osascript` を**全オカレンス**走査する。1 個目に固定すると
    #          `command -v osascript … && osascript -e "x"` の**2 個目**（＝本物の呼び出し）が
    #          丸ごと見えなくなる（Attempt 4 / SC4-H1。前 2 実装では検出できていた退行）
    #   終点 — 最初のコマンド区切り（`;` `&` `|` ` #`）で切る。切らないと
    #          `&&` / `||` / `|` の先の `-e` を引数と誤認する（Attempt 3 / CQ3-M1）
    #
    # **同じクラスの誤りを続けた**。原因は測り方で、
    # 正の対照（`&& [[ -e ]]` を誤 BLOCK しない）だけを足して
    # **対になる負変異（`&& osascript -e` を見逃さない）を母集団に入れていなかった**。
    # 以後は「正の対照を 1 形足したら同じ行形の負変異も 1 形足す」を規律とする。
    # ------------------------------------------------------------------
    scan="$line"
    while [[ "$scan" == *osascript* ]]; do
      before="${scan%%osascript*}"
      rest="${scan#*osascript}"
      scan="$rest"

      # `osascriptfoo` のような別語は対象外。トークン境界は空白だけではない ——
      # python の `["osascript", "-e", body]` では直後が `"` になる。
      case "$rest" in
        "" | [[:space:]]* | '"'* | "'"* | ,* | ")"* | "]"* ) : ;;
        *) continue ;;
      esac

      args="${rest#"${rest%%[![:space:]]*}"}"
      args="${args%%;*}"
      args="${args%%&*}"
      args="${args%%|*}"
      args="${args%% #*}"

      if [[ "$args" =~ (^|[[:space:]\"\'])-e([[:space:]\"\']|$) ]]; then
        echo "FAIL: osascript-arg-lint: '-e' argument found (must use stdin + system attribute): ${file#"$ROOT/"}:$lineno:$line"
        fail=1
        continue
      fi

      # 許すのは「stdin + クォートされた here-doc」だけ。該当しうる形は 3 つ:
      #   `osascript - <<DELIM` / `osascript <<DELIM`（`-` は省略可）/ `… | osascript`
      # 3 形目は**このスクリプト自身のコメントが根拠に挙げていた形**なのに、
      # Attempt 2 の入口条件を 1 つも満たしていなかった（Attempt 3 / CQ3-M2）。
      piped="${before%"${before##*[![:space:]]}"}"
      stdin_form=0
      [[ "$args" == -* ]] && stdin_form=1
      [[ "$args" == "<<"* ]] && stdin_form=1
      [[ "$piped" == *"|" ]] && stdin_form=1
      (( stdin_form )) || continue

      seen_invocations=$((seen_invocations + 1))
      if [[ "$args" != *"<<"* ]]; then
        # `--version` のように stdin を読まない形もここに来る。
        # 「stdin を読んでいる」と断定せず、**許可されていない呼び出し形**として述べる
        # （事実と逆の診断は Attempt 1 の M-2 と同じクラス ＝ Attempt 4 / SC4-M2）。
        echo "FAIL: osascript-arg-lint: osascript invocation is not the sanctioned form (stdin + quoted here-document): ${file#"$ROOT/"}:$lineno:$line"
        fail=1
        continue
      fi
      delim="${args#*<<}"
      if [[ "$delim" == "<"* ]]; then
        echo "FAIL: osascript-arg-lint: here-string (parameter expansion applies to the AppleScript body): ${file#"$ROOT/"}:$lineno:$line"
        fail=1
        continue
      fi
      delim="${delim#-}"
      delim="${delim#"${delim%%[![:space:]]*}"}"
      # 区切り語は `'` / `"` のほか **バックスラッシュ**でもクォートでき、
      # いずれも展開を無効化する（Attempt 4 / SC4-M3）。
      if [[ "$delim" != \'* && "$delim" != \"* && "$delim" != \\* ]]; then
        echo "FAIL: osascript-arg-lint: here-document delimiter is not quoted (parameter expansion would apply to the AppleScript body): ${file#"$ROOT/"}:$lineno:$line"
        fail=1
      fi
    done
  done < "$file"
done < <(find "$target_dir" -type f \( -name '*.sh' -o -name '*.bash' -o -name '*.zsh' -o -name '*.py' \) | sort)

# 主因を先に出す。空虚化ガードを先に評価すると、全呼び出しが `-e` 形へ退行したとき
# 「呼び出しが 1 件もない」という**事実と異なる行**が最後に出て読み手を誤誘導する
# （Attempt 4 / CQ4-M1）。
if (( fail != 0 )); then
  echo "FAIL: osascript-arg-lint"
  exit 1
fi

# 空虚化の正の対照 —— 呼び出しが 1 件も無ければ、この check は何も測っていない。
#
# **このガードは走査外の形への退行の受け皿でもある**。行継続 / 拡張子なし /
# 変数経由 / 複数行 argv はいずれも走査できないが、**全呼び出しがその形へ退行すると
# `seen_invocations` が 0 になり、ここで捕まる**（4 形すべてで実測）。
# つまりこの check がいちばん防ぎたい「既存の呼び出しを丸ごと非許可形へ書き換える」は
# 貫通しない。**削除するとその緩和が黙って失われる**ので、冗長に見えても消さないこと。
if (( seen_invocations == 0 )); then
  echo "FAIL: osascript-arg-lint: no stdin-form osascript invocation found under hooks/scripts (the check would be vacuous)"
  exit 1
fi

# 主張は**測った範囲**に限定する。無限定の「no '-e' calls」は、次の実装者に
# 「`-e` は機械的に禁止済み」と読ませ、走査外の形で書かせる導線になる
# （この plugin 自身が `bounded-claim-evidence` として BLOCK している型）。
echo "osascript-arg-lint: OK (scanned form = single-line direct invocation: no '-e' in that form; ${seen_invocations} stdin-form invocation(s), all with quoted here-doc delimiters. NOT scanned: line continuation / variable indirection / multi-line argv / quoted-literal context)"
echo "VERDICT: osascript-arg-lint: OK"
