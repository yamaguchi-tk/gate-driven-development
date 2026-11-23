# ADR: merge gate parser で、引用符・バックスラッシュで守られた演算子文字を「語」として区別する

- **日付**: 2026-09-11
- **状態**: 採用
- **対象タスク**: `20260911-merge-gate-quoted-operator`
- **リリース**: `plugins/gate-driven-development/CHANGELOG.md` `[0.42.2]`
- **関連**: `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py` の `_tokenize_checked` / `_is_operator` / `_is_control_operator`

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

## Context

merge gate は「承認された PR だけを merge させる」安全境界である。
parser は posix `shlex` で tokenize するため、クォートを剥がした時点で `';'` と裸の `;` が同じ token `;` になっていた。
その結果、`gh pr merge -t ';' 8` のような形で simple command を誤って区切り、PR 番号と `-R` を見失っていた。
PR 番号が見えない形は「引数省略形」として扱われ、hook は state.md の PR（承認済み）を対象とみなして allow する。
つまり、承認済み PR 旧#7 の証跡で、別 PR 旧#8 の merge が通っていた（hook サブプロセスで再現済み）。

## Decision

**案 A: tokenizer の段階で、引用符・エスケープ由来の演算子文字を「語」として区別する**を採用する（人間承認済み、2026-09-11）。

- tokenize の前に、クォート内・バックスラッシュ直後（単引用符の外）の演算子文字 `&` `(` `)` `;` `<` `>` `|` を内部表現の文字へ退避する
- 内部表現は、呼び出しごとに次の 2 段の候補から先頭順で「入力に現れない文字」を 7 個選ぶ。置き換え表は呼び出しごとの局所 dict だけで、module に状態を持たない
  - 1 段目: U+0001〜U+00FF のうち、shlex が特別扱いする 14 文字（空白・タブ・CR・LF、`'` `"` `\`、`&` `(` `)` `;` `<` `>` `|`）を除いた 241 文字（1 byte 幅）
  - 2 段目: 従来どおり U+E000 から U+10FFFF まで（途中で打ち切らない）
- tokenize の後に元の文字へ戻し、演算子文字だけから成る token を `str` 派生の `_QuotedWord` にする
- `_is_operator` / `_is_control_operator` は `_QuotedWord` を演算子と見なさない。区切り・リダイレクトの読み飛ばしの判定がこの 2 関数でまとめて揃う
- 候補を使い切った場合（1 段目と 2 段目を合わせて distinct で 1,057,003 個以上の入力）は、`ValueError` を parser の外まで出す。masks の選択は `_tokenize_checked` の try 節の**外**で行う。hook は parse-error で block する（当時）

## Why

- bash と同じ意味で読める。**tokenize 後の token 列を消費する側**（`_is_operator` / `_is_control_operator`、すなわち simple command の区切り・リダイレクトの読み飛ばしの判定）が 1 箇所の修正でまとめて直る。heredoc introducer 行の pipeline 境界検出（`_feeds_shell_interpreter` / `PIPELINE_BOUNDARY_RE`）は token 列を経由しない別経路で、本修正の対象外（独立レビュー実測、2026-09-11。バックスラッシュエスケープされた演算子文字を pipeline 境界と誤認する既存の穴が残っている。origin/main と同一挙動で本 diff による悪化はない）
- 「入力に現れない文字」を実行時に選ぶので、入力中の私用領域の文字と衝突しない。鳩の巣原理により、先頭から「入力の distinct 文字数 + 7」個の中に必ず 7 個の空きがある
- `str` 派生型なので token 列の型（`list[str]`）が変わらず、consumer の変更は演算子判定の 2 関数だけで済む。token 列は module の外に出ない（hook が読むのは `parse_gh_pr_merge` の返す dict だけ）
- 使い切り時の例外を try 節の外に出すのは、縮退経路（`except ValueError: return text.split()`）に落とすと、heredoc を含む形で縮退の標識が立たず `is_merge=False` の fail-open になるため（design review の実測）
- 1 段目を先に使う理由: shlex は引用中の文字を `self.token += nextchar` で 1 文字ずつ token へ連結するため、token の組み立て時間は token の内部幅（CPython の `str` が採る 1 / 2 / 4 byte 幅。token が含む最大コードポイントで決まる）に比例する。内部表現が U+00FF 以下（1 byte 幅）に収まれば、引用内で演算子が長く連なる入力でも組み立て時間が origin/main と同等になる。U+E000 台（2 byte 幅）から候補を始めていた当初案では、この種の入力で約 1.8 倍遅くなっていた（実測）

## Rejected Alternatives

- **案 B: 値を取る flag が値を失ったら `unresolvable` に倒す**: 差分は数行だが、`gh pr merge 7 -t ';'` のような正当な merge まで block し、原因の tokenizer が残る
- **内部表現を固定の対応（`U+E000 + ord(演算子)`）にする**: 入力に同じ文字があると衝突し、新しい fail-open を生む（spike で実測）
- **候補を私用領域 6400 文字（U+E000–U+F8FF）に限る**: それを全部含む入力で候補を使い切り、fail-open になる
- **候補の衝突・使い切りを縮退経路で扱う**: heredoc を含む形で縮退の標識が立たず fail-open になる
- **token と並行に「引用由来か」の list を持つ**: `_split_command_segments` 以降の全関数のシグネチャが変わり、差分と退行の面が広がる
- **位置引数に引用符付き演算子を置く形だけ従来の判定を残す例外分岐**: 複雑度が増え、shell の意味ともずれる
- **1 byte 幅の空きが無ければ parse-error で止める**: 性能の残余 (i) を塞げるが、新しい block 面ができる（241 文字をすべて含むコマンドは、GDD セッションでは `active: false` でも止まる）。候補が有限になり明示の分岐も 1 つ増える
- **入力長の上限をこの変更に入れる**: hook の timeout 超過による素通りを形によらず塞げるが、巨大な heredoc で書き込むコマンドなど merge でないコマンドも止まる。既存の別タスクで扱う範囲を超える
- **開始点を「入力の最大コードポイント以下」にする**: CJK を含む入力で U+0100 以降の 2 byte 幅の文字を選んでしまい、演算子の token が結局 2 byte 幅に戻る（実測）

## Consequences

判定が変わる形（origin/main との比較）:

- 位置引数に引用符付き演算子を置く形（`gh pr merge 8 ';'` など）は `pr-target-unresolvable` で block される（当時）。gh 自身が「引数過多」で拒否する形で、正当な merge を含まない。例外は `find . -exec gh pr merge 7 \;` で、`\;` は find が消費するが、tokenizer 単体では区別できず block される（当時。回避策: 直接 `gh pr merge 7` と実行する）
- `active: false`（管轄外）のとき、`gh pr merge 7 '&&' gh pr merge 8` は block から allow に変わる（`'&&'` を語として読み 1 本の merge とみなす）。実シェルでは gh が引数過多で拒否するので merge は起きず、`active: true` では block のまま（当時）
- sub-command より前の位置では判定が両方向に変わる。`(` か `)` を含む演算子文字だけの引用付き token を sub-command の位置に置く形（`gh '(' pr merge 8` など）は `is_merge` が False になるが、gh が未知の sub-command として拒否するので merge は起きない（1 文字の演算子に限って 6 形、2 文字で 48 形、3 文字で 294 形。いずれも gh が拒否する）。`gh -R ';' pr merge 8` / `gh --hostname ';' pr merge 8` のように、`-R` / `--hostname` の値に制御演算子 7 種を引用した形は各 21 形（7 文字 × 3 引用形）あるが、`is_merge` が False→True に変わるのはそのうち値が `;` `|` `&` の 9 形（3 文字 × 3 引用形）だけで block の方向に倒れる（当時）。残る 12 形（`(` `)` `<` `>` の 4 文字 × 3 引用形）は origin/main でも既に `is_merge=True` で変化しない（独立レビュー実測、2026-09-11）
- `active: true` で、`eval` の引数に `(` か `)` だけの引用付き token を置く形（`eval gh '(' pr merge 8` / `eval gh ')' pr merge 8` / `\(` `\)` `"("` `")"` を使う変形も含め計 6 形。後続に別の引用付き演算子を足した形（`eval gh ')' pr merge '|' 8` 等）も同様）が block 相当（`unresolvable=True`）から allow に変わる。`eval` は本体の token を空白で連結して読み直すので `_QuotedWord` の印が失われ、PR 番号の見えない引数省略形になるため。実 bash では `eval` が構文エラーになり、何も実行されない
- 候補を使い切る入力（UTF-8 で約 4.2MB 以上）は、GDD の marker があるセッションでは `active` の値によらず parse-error で block になる（当時。`active: false` の別 PR 宛て merge も、この入力に限り allow から block に変わる）。marker が無いセッションでは既存の parse 失敗と同じく通す

性能（実測値は `.steering/20260911-merge-gate-quoted-operator/evidence/perf_result.md` が正本）:

- 通常の入力（N=550,000 の `gh pr merge 8 -t '<;×N>'`）では、内部表現が 1 byte 幅になるため origin/main と同程度の所要になる
- 残余 (i): 1 段目の 241 文字のうち 235 文字以上を含む細工した入力では、一部の演算子の内部表現が 2 byte 幅に戻り、引用内の演算子が長く連なる形の所要が約 1.8 倍になる
- 残余 (i) の最悪値: さらに U+E000〜U+FFFF の 8,192 文字も含めると、7 種すべての内部表現が U+10000 以降（4 byte 幅）になり、約 3.5 倍遅くなる
- 残余 (ii): 置き換えの走査による線形の追加分。実運用の典型的な長さのコマンド（`gh pr merge 7` 程度〜4KB 程度の引用値）では走査の固定費が相対的に重く、独立レビュー実測で約 14〜22%、`eval` の入れ子と組む形では約 30〜42% 増になった。長大な入力（N=550,000 の繰り返し）では相対的に約 1% と小さくなる（絶対値はいずれも μs〜ms オーダーで運用上の支障はない。独立レビュー実測、2026-09-11）
- 残余は攻撃者に新しい能力を与えない。origin/main でも、引用内の連なりの先頭に絵文字を 1 つ置くだけで token 全体が 4 byte 幅になり、残余 (i) の最悪値と同じ遅さになる（実測で確認済み）
- hook の timeout（10 秒）超過で素通りになる既存の穴は、この 2 つの残余の分だけ起きうる入力が小さくなる。穴そのものは別タスクで塞ぐ
- 候補を使い切る入力（約 4.2MB）のテストだけは、並列回帰での `subprocess.TimeoutExpired`（実測）を避けるため hook を 60 秒の timeout で起動する。他のテストは本番と同じ 10 秒のまま（当時。2026-10-26 から、merge gate の hook を起動するテストの打ち切りは `HANG_GUARD`〔hooks.json の timeout の 6 倍〕）。テストの目的は「候補を使い切ると `ValueError` が parser の外へ伝播し、hook が parse-error で block する」経路（当時）の確認であり、この入力サイズが本番の 10 秒 timeout に達する経路はほぼ理論上のもの

今回直していない既存の制限・穴（origin/main と同じ挙動）:

- `eval` は token を空白で連結して読み直すため、引用の情報が失われる
- コマンド置換（`echo "$(gh pr merge 8)"`）は `is_merge=False` で gate を素通りする
- 引用内の `<<EOF` を heredoc と誤認し、後続行を捨てて素通りする
- push gate・pre-PR gate・`git_command_parse.py` の tokenizer は独立実装で、同型の穴が残る（hook サブプロセスで fail-open まで実測済み）。共有 helper が無いため、別の変更で扱う。追跡先: push gate（`task_f423ebd0`）/ pre-PR gate（`task_d6f46f36`）
