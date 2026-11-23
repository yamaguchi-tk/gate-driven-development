---
lane: L1+
pr: 439
follow_up_of: 433
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 102919af | 0 | 1 | 0 | 2026-10-12 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 914ee06b | 7 | 1 | 7 | 2026-10-12 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 914ee06b | 0 | 0 | 0 | 2026-10-12 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6963ae81 | 3 | 1 | 3 | 2026-10-12 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 6963ae81 | 0 | 0 | 0 | 2026-10-12 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 3f3dd85f | 3 | 0 | 3 | 2026-10-12 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable (gdd-fable-advisor) + user | 3f3dd85f | 0 | 0 | 0 | 2026-10-12 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 1fb1620c | 1 | 0 | 1 | 2026-10-12 |
| 方針メモ-4 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 1fb1620c | 0 | 0 | 0 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | medium | no | inherited | design | fixed | 4 件とも直す。7 は simple command ごとに `_find_sub_command` で探す。6 は fd 番号の正規表現を 1 つ（1〜10 桁）に戻し、2〜10 桁の密着形があれば merge の対象を決められないとする（入れ子の本体も）。1 は先に fail-open のテストを書き、lib を使わずに payload の cwd を取る。8 は `+` の option とリダイレクトを読み飛ばす。lib の正味の行は増やさない。commit: なし（方針） |
| F1 | 独立-1 | high | yes | self-inflicted | fd-ambiguity | fixed | 列挙: 2〜10 桁の fd 番号の枝が読めた番号・URL まで消し、marker の無い checkout から台帳の PR 旧#7 への `gh pr merge 7 12>/tmp/x` などを unknown で通す（差分の前は止めていた退行）。transcript 0 件だが差分が生んだ退行を戻すだけで受理集合を変えないので、方針メモ-1 で直すとした（規則の (b) から外れる）。unresolvable だけを立て番号・URL を残し、`merges > 1` は今どおり消す。commit: 602cb074 |
| F2 | 独立-1 | high | yes | self-inflicted | perf-scan | accepted | 列挙: pre-PR gate の新しい探索ループが gh の語の数の 2 乗。PR 作成の候補で gh の語は最大 63（50 以上は 1 件）、害の見積もりは約 3,000 語。方針メモ-1 で (b)。限界の節の先頭に書く |
| F3 | 独立-1 | high | yes | self-inflicted | shell-c | accepted | 列挙: `_shell_c_operand` は `-c` の直後の語を script にするので、`bash -c 2>/dev/null '…'`・`-c -e`・`-c --`・`-co pipefail`・`-oe pipefail -c` の中の merge を読まない。transcript 0 件。方針メモ-1 で (b)。限界の節の先頭に書く |
| F4 | 独立-1 | high | yes | inherited | nested-expand | accepted | 列挙: pre-PR gate の入れ子の展開（hook の中の写し）は `bash --norc -c`・`ksh`/`dash -c`・`env -S` を読まず、merge gate と受理集合が違う。transcript 0 件。方針メモ-1 で (b)。lib の `_nested_shell_commands` に寄せるのは Issue 旧#246 の後の PR。限界の節の先頭に書く |
| F5 | 独立-1 | high | yes | self-inflicted | fd-ambiguity | accepted | 列挙: zsh は 1 桁の数字の直後の `&>` も fd 番号に読む（未確認）ので、`gh pr merge 9&>/dev/null` を 旧#9 と読む。transcript 0 件。方針メモ-1 で (b)。限界の節の先頭に書く |
| F6 | 独立-1 | high | yes | self-inflicted | ledger-multi | accepted | 列挙: merge が 2 つ以上の枝も番号・URL を消すので、marker の無い checkout から台帳の PR を含む連結 merge を unknown で通す。形は transcript 24 件（台帳の PR との重なりは未測）。依頼の外で、直すには 旧#436 と同じ merge gate の hook と新しい signal が要るので、方針メモ-1 で (b) とし Issue 旧#438 にした。限界の節の先頭に書く |
| F7 | 独立-1 | high | yes | self-inflicted | gh-subcommand | accepted | 列挙: `pr` を見つけると api を探さないので、`gh -q pr api …/pulls` を PR 作成と読まない。transcript 0 件。方針メモ-1 で (b)。限界の節の先頭に書く |
| F8 | 独立-1 | medium | no | self-inflicted | test-power | fixed | merge gate の 2 変更に hook の入口からのテストが無い。台帳の経路・GDD の中の unresolvable・shell の `-c` の前の形を test_merge_gate_target_grammar.py に足した。commit: 768043fd |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「止める」が marker の無い checkout まで含む書き方。GDD の中は止め、marker の無い checkout は台帳と照合する、と書いた。commit: 602cb074 |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 前の PR の未リリースの断片が古い fd 番号の規定を書く。この PR の断片に、その記述を置き換えると書いた。commit: 602cb074 |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 解析の失敗の block の文が「create・new・pulls を含むコマンド」で、判定は payload 全体。文を Bash の呼び出し（コマンド・cwd・説明などのどれか）にし、Next Action を足した。commit: 602cb074 |
| F12 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | PR 本文の件数に測ったコマンドが無い。PR 本文にコマンドを書く。commit: なし（PR 本文） |
| F13 | 独立-1 | low | no | self-inflicted | test-power | fixed | merge の形の assert が is_merge が真のときだけ働く。条件なしで見る形にした。commit: 768043fd |
| F14 | 独立-1 | low | no | self-inflicted | test-power | fixed | 解析の失敗の経路で最上位の cwd と workdir を通すテストが無い。2 本足した。commit: 768043fd |
| F15 | 独立-1 | low | no | self-inflicted | product | fixed | sub-command の探索の bool flag の表に create・new・api が無く `--help` を値を取る flag と読む。表に足した。commit: 602cb074 |
| F16 | 独立-1 | low | no | self-inflicted | style | fixed | kill switch の案内を手で写した literal にしている。merge gate の定数（lib/merge-gate-evidence.sh）を使う形にした。commit: 602cb074 |
| F17 | 独立-1 | advisory | no | self-inflicted | product | accepted | PARSED を読むために python3 を 1 回多く起動する。PR 本文に書く |
| F18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | FD_PREFIX_RE のコメントが、10 桁で int を超える並び（止める側）に触れていない。PR 本文に書く |
| R1 | 方針メモ-1 | - | - | - | - | - | なし |
| G1 | 独立-2 | high | yes | inherited | fd-ambiguity | fixed | zsh の `gh pr merge 12>/tmp/x`（zsh は 旧#12）は bash の読みで番号が無いので、marker の無い checkout で台帳と照合されず通る。閉じ方: 構造。bash の読みで番号・URL が無いときは、2〜10 桁の密着形を語として切り離した zsh の読みでもう 1 回走査し、その番号・URL を残す（hook は変えない）。commit: b91d3e91 |
| G2 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 依頼の 6（閉じる）を、断片で「GDD の中では止め、marker の無い checkout は台帳と照合」と狭めた。G1 を直して、台帳の経路でも zsh の読みの番号を照合する形にした。commit: b91d3e91 |
| G3 | 独立-2 | high | yes | inherited | nested-expand | accepted | 列挙: pre-PR gate の入れ子の展開が `--norc` を `-c` と読み、dash・ksh・`env -S` を読まない。独立-1 の F4 と同じ指摘。transcript 0 件。方針メモ-2 で (b)。限界の節の先頭（F4 の段落）に書く |
| G4 | 独立-2 | high | yes | self-inflicted | parse-exception | accepted | 列挙: PARSED=false のとき raw task steering の検査を飛ばす分岐をこの PR が足した（差分の前は hook が exit 1 で同じく走らなかった）。解析の例外は transcript の前段 29,960 件で 0 件。直すと、lib が壊れている・marker が無い・base との差分に raw steering がある、が重なると create・new・pulls を含む Bash がすべて止まる。方針メモ-2 で (b)。限界の節の先頭に書く |
| G5 | 独立-2 | low | no | self-inflicted | product | accepted | merge-gate-evidence.sh も読めないと kill switch の案内が空になる。follow_up_of のある PR の 2 巡目の low なので限界の節に書く |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `_find_sub_command` の docstring が探す名前を pr・merge だけ書く。限界の節に書く |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の検証の欄が「台帳の経路で 2〜10 桁の fd 番号の merge を止める」と全称で書く。限界の節に書く |
| G8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 前の PR の未リリースの断片が古い fd 番号の規定を書いたまま残る（この PR の断片で置き換えを宣言しただけ）。限界の節に書く |
| G9 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の lib の行数が古い。PR 本文で tip の行数にする。commit: なし（PR 本文） |
| G10 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 旧と新の全件一致をどの commit で比べたかが無い。tip で比べ直し（merge gate 30,463 件・pre-PR gate 30,104 件で違い 0）、PR 本文に書く。commit: なし（PR 本文） |
| R2 | 方針メモ-2 | - | - | - | - | - | なし |
| H1 | 独立-3 | high | yes | self-inflicted | fd-ambiguity | fixed | `_split_multi_digit_fd` は `_has_multi_digit_fd` と違い語頭コメントと行継続の前処理をしないので、`# don't wait` の後の `gh pr merge 07>/tmp/x` で zsh の読みの番号を取れず、台帳の照合を通る。閉じ方: 構造。transcript の merge 1,309 件で 2〜10 桁の密着形は 0 件。安全策 4 の発火で HITL へ 方針メモ-3 で A' を選び、前処理と引用符の退避を `_mask_for_fd` に寄せて有無の判定と zsh の読みで共有した。commit: 4989f418 |
| H2 | 独立-3 | high | yes | inherited | fd-ambiguity | accepted | zsh の読み直しは最上位だけなので、`eval 'gh pr merge 07>/tmp/x'`・`zsh -c '…'` の本体の番号を台帳と照合しない。閉じ方: 構造。transcript で入れ子の本体の 2〜10 桁の密着形は 0 件。安全策 4 の発火で HITL へ 方針メモ-3 で (b)。限界の節の先頭に書く |
| H3 | 独立-3 | high | yes | inherited | fd-ambiguity | accepted | 列挙: `gh pr merge 12\` + 改行 + `>/tmp/x` は行継続の置き換えで `12 >` になり、PR 12 と読む（bash は fd 12）。transcript で数字＋行継続＋リダイレクトの merge は 0 件。安全策 4 の発火で HITL へ 方針メモ-3 で (b)。限界の節の先頭に書く |
| H4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片に zsh の読みの番号で台帳と照合することが書かれていない follow_up_of のある PR の low なので限界の節に書く |
| H5 | 独立-3 | low | no | self-inflicted | test-power | fixed | 引用符の中の `12>` のテストが `_split_multi_digit_fd` の退避と戻しを固定していない 退避と戻しを `_split_multi_digit_fd` の出力で固定した。commit: 82e95364 |
| H6 | 独立-3 | advisory | no | inherited | doc-claim | accepted | merge gate の hook の `_mg_ledger_verdict` と step 5b の説明に 2〜10 桁の fd 番号と zsh の読みが無い advisory。PR 本文に書く |
| H7 | 独立-3 | advisory | no | self-inflicted | product | accepted | zsh の読みで `_scan_tokens` をもう 1 回走らせるので、この経路の最悪の解析時間が約 2 倍 advisory。PR 本文に書く |
| R3 | 方針メモ-3 | - | - | - | - | - | なし |
| I1 | 独立-4 | high | yes | self-inflicted | fd-ambiguity | accepted | 列挙: `gh pr merge 12\` + 改行 + `>/tmp/x`（1 桁の `2\` + 改行 + `>` も）は、行継続の置き換えで `12 >` になり PR 12 と読む（bash は fd 番号で引数の無い merge）。done 状態の経路でも同じ。H3 と同じ仕組み（`_join_line_continuations`）。transcript の merge 1,309 件で数字＋行継続＋リダイレクトは 0 件。方針メモ-4 で (b)。A' の止める条件のとおり直さず、限界の節の先頭に書く |
| I2 | 独立-4 | low | no | inherited | fd-ambiguity | accepted | zsh の読みは最上位だけで、`zsh -c '…'` の本体を読まない（H2 と同じ）。follow_up_of のある PR の low なので限界の節に書く |
| I3 | 独立-4 | low | no | self-inflicted | fd-ambiguity | accepted | `_mask_for_fd` の `_mask_quoted_operators` は `$'…'` の `\'` を知らず、`--body $'it\'s' 12>/tmp/x` で判定が働かない。限界の節に書く |
| I4 | 独立-4 | low | no | self-inflicted | test-power | accepted | 足したテストが行継続の処理を固定しない。限界の節に書く |
| I5 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | PR 本文の旧と新の比較の sha が古い。PR 本文で直した。commit: なし（PR 本文） |
| I6 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 断片に zsh の読みの番号で台帳と照合することが無い（H4 と同じ）。断片を直した。commit: 38871a92 |
| I7 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | lib の注記が `_mask_for_fd` を判定と書くが、判定は呼び出し側。限界の節に書く |
| I8 | 独立-4 | low | no | self-inflicted | style | accepted | 判定式が 2 か所に書き写され、1 行が約 170 字。限界の節に書く |
| R4 | 方針メモ-4 | - | - | - | - | - | なし |
