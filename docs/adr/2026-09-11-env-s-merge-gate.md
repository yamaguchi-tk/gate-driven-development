# ADR: `env -S` で包んだ `gh pr merge` を、env の argv に本体を差し込んだ形で再走査して merge gate に検出させる

- **日付**: 2026-09-11
- **状態**: 採用
- **Superseded（部分）by**: `docs/adr/2026-10-15-merge-gate-notice-only.md`（merge gate は止めなくなったので、後続の制約は適用しない）
- **対象タスク**: `20260909-env-s-merge-gate`
- **リリース**: `plugins/gate-driven-development/CHANGELOG.md` `[0.42.1]`（origin/main が分岐後に別内容で `[0.41.12]` を消費したため、取り込み時に付け替えた）
- **関連**: `docs/adr/2026-10-03-block-guard-threat-model.md`（block guard の守る範囲。本 ADR の後続の制約は置き換えない）/ `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py` の `_nested_shell_commands`（env 分岐）/ `_env_split_string_body` / `_env_split_string_command` / `_cutoff_matches_visible_gh` / `MAX_ENV_SPLIT_STRINGS_PER_LAYER`

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

## Context

origin/main（64e33e0）の merge gate は、`env -S 'gh pr merge 7'` を `is_merge=False` と読んでいた。
この場合 hook は「解析が完走し、merge ではない」経路で `exit 0` になり、証跡と承認と待機のすべてを迂回した merge が通る。
`env -S '-C <別 repo> gh pr merge 7'` のように chdir を伴う形も同じで、`[0.41.11]` の Known limitations で別 steering の第一候補として開示していた。

pre-push gate（`push_command_parse.py`）と pre-PR gate（`run-pre-pr-gate-hook.sh` の inline python）にも同型の穴があることを実測した。
3 つの gate は tokenize の方針も返り値も違う別々の parser を持つ。

最初の実装の完了前の点検（completion-check）で、同じクラスタに次の欠陥が見つかった。

- 本体の末尾に語頭 `#` の語や `\c` を置くと、同じ merge を 2 回数えないための打ち切り（Decision 4）が誤って働き、本体の `-R` が argv から消えて現 repo の PR と読み違える（origin/main と同じ読み違い）。
- split-string を区切りなしで多数並べると、解析時間が個数に対して指数的に伸び、hook の `timeout: 10` を超えて無出力 allow になる（origin/main には無い退行）。

## Decision

1. **対象は merge gate だけにする**。姉妹 gate の同型の穴は CHANGELOG の Known limitations に実測付きで開示し、別 steering で扱う。
2. **`env` の split-string オプション（`-S` / `--split-string`）の本体を、実 env と同じく env の argv のその位置に差し込んだ argv として再走査する**。argv は `env` と本体の token と、同じ simple command の後続引数（次の制御演算子の手前まで）からなる。これを `bash -c` / `eval` と同じ入れ子経路（tokenize、深さ予算 `MAX_NESTED_SHELL_DEPTH`=3、重複除去）に流す。新しい深さ定数と新しい tokenizer は作らない。
3. **env の option 走査は operand（env が起動するコマンド名）か `--` で打ち切る**。代入（`NAME=value`）と値取り option とその値は読み飛ばし、短オプション束は左から 1 文字ずつ読む。走査規則の正本は `_env_split_string_body` の docstring、綴りの正本は同じファイルの定数に置く。
4. **同じ merge を 2 回数えないよう、トップ層が既に数えている `gh … pr merge` の手前で argv を打ち切る**。ただし打ち切るのは、打ち切る前の argv を同じ gh 探索で読んで見つかる gh が、トップ層の gh と同じ token に対応するときだけにする。gh が本体由来のときの対応の定義には、本体 token 列の最後の gh が本体 token 列の末尾にあることを含む。対応しなければ打ち切らず、2 回数えて `pr-target-unresolvable` の block に倒す（当時）。
5. **1 層（`_nested_shell_commands` の 1 回の呼び出し）で展開する env split-string の個数に上限 8（`MAX_ENV_SPLIT_STRINGS_PER_LAYER`）を設ける。加えて、本体に `\c` を含む場合は位置を問わず同じ「対応・解析を確かめられない」扱いに倒す**。制御演算子では数え直さない。超えたら（または `\c` を見た時点で）展開・解析をやめ、`is_merge=True` / `unresolvable=True` / `cd_intent=True`（`pr_number` / `pr_url` / `cd_target` は None）として既存の block 経路に乗せる（当時）。reason code と hook の出力 field は増やさない。`cd_intent=True` にするのは、この例外が `_scan_tokens` より前に送出され、走査範囲に chdir intent（`cd` / `env -C` 等）があっても実行先（`cd_target`）を確定できないためで、hook 側の「chdir intent はあるが実行先を 1 つに決められない形を block する」既存の遮断へ委ねる（当時）。

## Why

- 実 env の `-S` は、分割した本体を元の env コマンドの引数として扱い、後続の元引数がそのまま続く（`man env` § Details of -S (split-string) processing）。本体だけを独立した shell 本体として読む初版は、`env -S 'gh pr' merge 7` や本体の中の `-S` を素通りさせ、後続引数の `-R` や PR 番号も読み落とした。実装ゲートがこれを fail-open として検出した。欠陥の出どころは実装ではなく、設計が env の意味論をモデル化しきれていなかったことにある。
- 差し込み後の argv を既存経路に渡せば、PR 番号、repo 指定、`--admin` の解決を既存経路にそのまま任せられる。`env VAR=x gh pr merge 7 -R other/repo` を正しく解決している経路そのものである。
- 打ち切りに対応条件を付けたのは、トップ層が `-S` の意味論を持たないためである。`-R` の値や本体の token 全体の basename が `gh` になる形（例 `env -S 'gh -R' o/gh pr merge 7`）では、トップ層はその値を gh 本体と読み違える。無条件に打ち切ると、その読み違いを信用して、別 repo の PR を現 repo の証跡で merge させてしまう。実 argv とトップ層の読みの両方を見られるのは env 分岐だけなので、対応を確かめ、確かめられなければ block 側に倒す（当時）。
- option 走査を operand で打ち切るのは、返り値が再走査される argv だからである。打ち切らないと `env FOO=1 grep -S "… gh pr merge …" file` の `grep` の値まで shell 本体として読み、過剰 block になる（当時）。同じ `env` 以降を読む `_has_chdir_intent` は返り値が真偽値の intent で block 方向にしか倒れない（当時）ので打ち切らない。この非対称は意図したもので、両方の docstring に書いた。
- 打ち切りの対応条件に「最後の gh が本体 token 列の末尾にある」を足したのは、本体の生文字列の末尾に語頭 `#` の語を置く形（`env -S '/usr/bin/gh -R o/x #/gh' pr merge 7`）のためである。実 env は `#` で始まる語から後ろを捨てるので、実行されるのは `/usr/bin/gh -R o/x pr merge 7`（o/x の 旧#7）になる。parser も本体 token 列からは `#` 以降を落とすが、トップ層は本体の生文字列全体の basename（末尾の `#/gh` 由来の `gh`）を gh 本体と読み、`pr merge 7` を現 repo の 旧#7 と解決する。本体 token 列の最後の gh（`/usr/bin/gh`）の後ろに `-R o/x` が残るのに対応ありと判定して打ち切ると、その `-R o/x` が argv から消え、読み違いがそのまま採用される。
- 本体の `\c` を打ち切り条件の 1 つとして足す初版は、`\c` が本体全体の basename を `gh` にする形（`… o/x \c/gh` の最後の token は `c/gh` になり、末尾条件を満たしてしまう形）しか判断材料にしておらず、`\c` の後ろが `gh` にならない一般形（`env -S 'gh \cx' pr merge 7` 等）は打ち切り判定の経路そのものに入らず素通りが残っていた（実装ゲートの独立レビューで発見）。`\c` を打ち切り条件の一部として扱うのをやめ、本体に `\c` が含まれていれば `gh` との位置関係を問わず「対応・解析を確かめられない形」として展開個数の上限超過と同じ扱いに倒すよう改めた。`\c` は実 env にとって「文字列の残りを無視する」記号であり、parser の tokenize は `\c` を普通の文字 `c` として残すため、`#` のように末尾条件で捕捉する形をモデル化できない。上限超過も `\c` も、実 env の解釈を再現するものではなく、対応・解析を確かめられない形を block 側に倒すだけである（当時）。
- split-string の展開個数に上限を設けたのは、1 つの simple command に split-string を区切りなしで並べると、各 argv が後続の split-string を抱えて次の深さで再展開され、解析時間が個数に対して指数的に伸びるからである（`env -Sx ` × 100、813 byte で 21〜42 秒。origin/main は同じ入力を 1 秒未満で merge と判定する）。層ごとに数えるのは、simple command ごとに数え直すと、上限内の simple command を `&&` でつないだ形で時間が段数に比例して伸び続けるためである。
- 値 8 は、手順の忘れで書く形（split-string 1〜2 個）を十分に上回る。そのうえで、上限内で 10 秒の timeout に届く入力長が長くなるほうを選んだ（測定時点で上限 20 は約 8 KB、上限 8 は約 90 KB）。代償として、既存の性能テストのうち 4 本が上限を超える入力になり、解析せず block する経路（当時）で予算内に収まるようになるが、assert の期待値は変わらない。
- 展開個数の上限超過を「対象を決められない」表現へ倒す except 節は、当初 `cd_target` だけを None にし、`cd_intent` は既定の `False` のまま残していた。この例外は `_scan_tokens` より前（`_chdir_signals` の中）で送出されるため、走査範囲に chdir intent（`cd` / `env -C` 等）があっても `cd_intent=False` のままでは hook 側の「chdir intent はあるが実行先を 1 つに決められない形を block する」既存の遮断を通り抜け、GDD セッションの repo に steering が無い状態で無出力 allow になっていた（実装ゲートの独立レビューで発見）。`cd_intent=True` を立てるよう改めた。

## Rejected Alternatives

- **入口で `env -S 'X'` を `X` に書き換える前処理**: `degraded` の判定が元のコマンドを基準にしている設計と干渉する。
- **`env` を見たら無条件に block する**: `env VAR=x gh pr merge 7` のような日常の正当形を巻き込む。既存テストが allow を固定している。
- **3 つの parser の入れ子展開を共有 lib にしてから直す**: 独立した refactor であり、1 綴りの修正に載せるとスコープが膨らむ。
- **`-S` の本体だけを独立した shell 本体として再走査する（初版）**: 上の Why のとおり素通りが残る。
- **option 走査の中で本体を差し込み、そのまま走査を続ける**: 入れ子の `-S` を深さ予算なしで解くことになり、終了性と計算量の論証が新たに要る。密着形 `-S-S-S…` は 1 段 2 文字で入れ子にできるので、入力長 L に対して O(L²) になりうる。
- **merge を対象（PR 番号や URL）の組で重複除去する**: `gh pr merge 7 && gh pr merge 7` の既存の判定を変える。
- **打ち切り条件を付けず、見えている gh があれば必ず打ち切る**: トップ層の読み違いを信用する fail-open が残る。
- **トップ層の読み違いを別タスクに寄せて開示だけする**: 同じクラスタで新しく見つかった fail-open を受容しないという歯止めに反する。
- **split-string の展開個数の上限を 20 にする**: 既存の性能テストのうち 3 本を解析の経路のまま保てるが、上限内で 10 秒の hook timeout に届く入力長が約 8 KB まで短くなる（上限 8 では約 90 KB）。
- **展開した argv の語数の合計にも上限を設ける（長さの予算）**: 上限内で語数に比例して伸びる形も閉じるが、承認された「個数の上限」とは別の仕組みで、定数と判定面が増える。
- **env の split-string オプションを見た時点で解析せず block する（方式転換）**: 打ち切りの誤判定と展開個数の問題をまとめて閉じるが、正当な split-string 経由の merge も block するようになり、検出の受入条件の意味が変わる。人間に再提示したうえで採らなかった。実装ゲートの独立レビューで新たに 2 件（`\c` の一般形、展開個数超過時の `cd_intent`）が見つかった際に再度提示したが、どちらも fail-closed 側で閉じる修正であり歯止めの例外を広げないため、今回も採らなかった。以後 impl-gate Round 2 以降で同じクラスタの fail-open が再発した場合は、修正を止めてこの方式転換に切り替える閾値を人間が承認した。

## Consequences

- 人間の承認を得て開示し受容した過剰 block（fail-closed）が残った（当時。今は不足として実行後に通知する）。
  - `eval` / `bash -c` / 別の `env -S` が `env -S` の前、本体の中、後続引数のどこかにある形は、既存経路と差し込み経路が同じ merge を 2 層で数え、`pr-target-unresolvable` になる。`env -S '' eval 'gh pr merge 7'` などは origin/main が PR 番号を解決していた形からの退行である。
  - 本体と後続引数の両方に `-R` を書く `env -S 'gh -R o/gh' -R o/r pr merge 7` も、origin/main が `repo_flag="o/r"` に解決していた形からの退行である。避けるには実 gh の flag 解釈を再現する新しい解析面が要る。
  - 展開個数の上限の裏返しとして、1 つの層に split-string を持つ `env` を 9 個以上並べたコマンド（1 つの `env` につき最初の `-S` だけを数える）、または本体に `\c` を 1 つでも含むコマンドは、`gh pr merge` を含まなくても `is_merge=True` / `unresolvable=True` になる。
- fail-open として開示した限界が残る。1 つの env の argv に 4 個目以降の `-S` がある形（深さ予算を使い切る）、`-S` の本体を変数展開やクォート分割で難読化した形、未知の値取り option を operand と誤認した形は検出できない。
- 完了前の点検で見つかった fail-open のうち次の 4 系統は、人間が「同じクラスタの新しい fail-open は受容しない」という歯止めの例外として、開示したうえで受容した。最後の 1 系統を除き、origin/main と同じ判定である。
  - 本体が shlex で割れない（縮退する）形で、後続引数で merge が完成する形（例 `env -S 'gh pr "' merge 7`）は検出しない。縮退した本体には後続引数を付けないためである。本体に `\c` を含む形（例 `env -S 'gh pr \c"' merge 7`）は、縮退の判定より前に `\c` の有無を見るようになったため対象外で、`is_merge=True` / `unresolvable=True` になる（Decision 5）。
  - env の option 区間にリダイレクトがある形（`env 2>/dev/null -S 'gh pr merge 7'` / `env -S >/dev/null 'gh pr merge 7'`）は、option 走査がリダイレクトを operand と読んで打ち切り、`-S` を見落とす。
  - 本体で env 固有の区切り `\_` を使う形は、parser が `\_` を区切りとして再現しないため、hook が発火しない（`env -S 'gh\_pr\_merge\_7'`）か、本体を 1 つの token に見せて repo を読み違える。後者の例 `env -S '/usr/bin/gh\_-R\_o/x\_#/gh' pr merge 7` は `repo_flag=None` で現 repo の 旧#7 と読むが、実 env は o/x の 旧#7 を merge する。この形は Decision 4 の末尾条件の対象外である（同じ形で `#` の代わりに `\c` を使うと、本体に `\c` を含む形として位置を問わず block 側に倒れる。当時の挙動）。
  - 上限 8 以内でも、同じ simple command に語を多数並べると、解析時間が語数に比例して伸びる（例 `env -Sx ` × 8 + 語 40000 個 + `gh pr merge 7`）。10 秒を超えると hook は無出力で allow になる。10 秒に届く長さは負荷に依存し、通常は 100 KB 前後、高負荷下では 20 KB 前後まで下がる。origin/main は同じ入力を 1 秒未満で merge と判定するので、この入力に限れば origin/main より悪い。ただし同じ長さの `eval` の並びは origin/main でも既に素通りし（`eval` 単独なら 513 byte で 10 秒に届く）、hook の時間制限を使う素通りの手段が新しく増えるわけではない。閉じるには長さの予算という別の仕組みが要る。
- origin/main から存在する別の fail-open 3 件は本変更に含めず、別タスクで扱う。トップ層の引用符付きの演算子による PR 番号と repo 指定の読み落とし（例 `gh pr merge -t ';' 8`）、`env -u gh GH_REPO=o/r gh pr merge 7` の `GH_REPO=` の見落とし、ANSI-C クォート `$'…'` を shlex が解さず `gh` を見失う形（例 `$'gh' pr merge 7`。`env -S` の有無に関わらずトップ層で再現する tokenizer 全体の限界。impl-gate Task 5 Round 2 の security review で発見）である。
- CHANGELOG に Breaking Contract Changes 節は足さない。reason code と hook の出力の形は変えておらず、block 条件の変化は `docs/VERSIONING.md` § Breaking Change の分類の「利用者体験レベル」に当たる。回避手順は `[0.42.1]` の User Action Required に書いた。
- 後続の変更が守る制約: この env 分岐のクラスタで新しい fail-open が見つかった場合は、開示で受容せず直すか人間に判断を戻す。上の 4 系統は人間が個別に認めた例外であり、例外を広げる根拠にはしない。`git_command_parse.py` の同名関数に env 分岐が無いのは意図した非対称であり、揃えるときは pre-push gate の修正として別に扱う。
