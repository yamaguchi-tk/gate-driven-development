---
type: breaking
---

#### Summary

- done guard（Stop hook）の Check 3（state.md の `Route In Progress` が non-none なら done を止める）が、`Route In Progress` を読めない state.md を「route なし」として通していた穴を閉じた（Issue 旧#119 / D-28）
- 入口は、state.md に LF / CR 以外の行区切り文字（U+000B / 000C / 001C / 001D / 001E / 0085 / 2028 / 2029）があると `select_route_in_progress()` の `str.splitlines()` が行を誤分割し、`- Route In Progress: <U+2028>implementation_fix_only` の値が空になって done が通る形だった。tasklist.md 側は同じ 8 文字をすでに block しており、対の片方だけが直っていた。独立レビューで、同じ「読めなければ通す」既定から通る形（値が次の行にある、注記だけ、前の `none` 行が後ろの読めない行を隠す、write guard とキーの形が違う、キーの側が崩れている、コロン形と等号形の混在、state.md の未閉 fence、hook 自身の要約の書き込み）が続けて見つかったため、既定そのものを反転した

#### Fixed

- Check 3 の入口で state.md の全文（code fence の中も含む）に行区切り文字の検査をかける。見つかったら行区切りの理由だけを返し、`Route In Progress` の判定には進まない（fail-closed）。block 理由には、Check 3 を迂回できる置き換え方を書かない
- state.md に閉じていない code fence があれば block する（tasklist.md と同じ扱い）。閉じ忘れの後ろにある記入例の `none` が現在値に採られていた
- `Route In Progress` のキー行（write guard の `state_field_pattern` と同じく backtick を全除去してから照合する。大文字小文字を無視するので、受理集合は write guard より少し広い）のうち、最後の 1 本を現在の行として読む。その値を読めなければ block する（値が次の行、注記だけ、行の途中の単独 CR、` : x` のような形）
- 最後のキー行の値と `select_route_in_progress()` の値の両方が `none` のときだけ通す。reader はコロン形を優先するので、`: none` の後に `=<route>` を書くと reader だけが `none` を返して通っていた（reader は変えていない）
- 正準のキー行が 1 本も無い state.md は block する（`Route In Progress` は Tier 1 必須 field）。正準のキー行が無ければ、キーの側が崩れた形（全角コロン、字下げ、太字、`*` 箇条書き、キー内の ZWSP / NBSP、先頭の BOM）は崩れ方を見分けずにここへ畳まれる。state.md そのものが無いときは従来どおり通す
- `lib/handoff_summary.apply_summary()` の `re.sub` を関数置換にした。文字列置換だと、要約中の 2 文字の `\n` が state.md の本物の行になり（同じ Stop の中で Check 3 の直前に `Route In Progress: none` 行を足せた）、`\f` / `\v` は行区切り文字になっていた
- `apply_summary()` の置換範囲を行区切り文字の手前までにした。`Last Handoff Summary=.*` の `.` が U+2028 などにも一致し、同じ物理行の後ろの route 行ごと上書きしていた。persist は Check 3 より前に走るので、行区切り文字の検査が効かずに done が通っていた

#### Changed

- `lib/done_guard._line_break_char_error()` を、対象ファイル名（`tasklist.md` / `state.md`）を引数に取る形にした。tasklist.md 向けの block 理由の文言はバイト等価
- Check 3（`_route_in_progress_errors`）を `gdd_stop_hook.py` から `lib/done_guard.py` へ移した（hook 本体は 1525 行 → 1506 行）
- `state_field_pattern()` の正本を `lib/state_fields.py` から `lib/tasklist_parse.py` へ移した（`state_fields` は再 export。done guard から `state_fields` を import すると stop hook の `sys.path` では解決できないため）
- 行区切り文字 8 種の集合を `lib/tasklist_parse.NON_NEWLINE_LINE_BREAKS` に置き、done guard の検査と `apply_summary()` の置換範囲が同じ集合を使うようにした
- 回復ヒント（`lib/done_block_message.py`）: 「行区切り文字 →」を両ファイルの見出しで出す。「唯一の回復手順」の抑止は tasklist.md の見出しのときだけ。「行が無い」「最後の行を読めない」「state.md の fence が閉じていない」block には、tasklist.md ではなく state.md の直し方を案内するヒントを出す

#### Added

- `lib/tasklist_parse.route_in_progress_key_lines()`: fence を剥がした state.md の `Route In Progress` のキー行を書かれた順に返す
- `tests/test_done_guard_state_line_break_chars_contract.py`: 8 文字 × state.md の block（Stop hook の入口から）、fence の中、fail-open の 3 ケース、値を読めない形、前の `none` が後ろを隠す形、write guard の形、キーの崩れ 7 形、キー行なし、write guard とのキー集合の包含、区切りの混在、state.md の未閉 fence、回復ヒント、tasklist.md 文言のバイト等価、`truncate_summary` と `apply_summary` が行区切り文字・改行を作らず消しもしないこと（persist → Check 3 を Stop hook の入口から通すものを含む）
- `tests/test_verification_block_message_contract.py`: 回復ヒントの抑止を tasklist.md の見出しに限ることを固定する 4 ケース

#### Breaking Contract Changes

- **done guard Check 3 の既定を「読めなければ通す」から「読めなければ止める」へ反転した**（利用者体験レベル: 既定の block 条件の変更）。従来は `Route In Progress` を読めない state.md を「route なし」として done を通していた。次の形は、今後 done が block される
  - state.md に LF / CR 以外の行区切り文字（U+000B / 000C / 001C / 001D / 001E / 0085 / 2028 / 2029）がある
  - state.md に閉じていない code fence がある
  - `Route In Progress` のキー行が 1 本も無い（正準のキー行が無ければ、キーの側が崩れた形もここに入る）
  - 最後のキー行から値を読めない
  - 最後のキー行の値と `select_route_in_progress()` の値のどちらかが `none` でない（コロン形と等号形の混在）
- state.md そのものが無いときは、従来どおり通す
- SessionStart / UserPromptSubmit hook（`detect-steering.sh`）と `references/state-machine.md` は、すでに `Route In Progress` を抽出できない active steering を fail-closed にしている。この変更は、done guard だけが通す側だった不整合を揃えるもの
- 実測では、この変更で done が allow から block に変わる steering は 0 件（§ User Action Required）
- 暫定互換期間は設けない。旧挙動を残すことは、route を抱えたまま done が通る fail-open を残すことになるため
- 回復手順: state.md の行区切り文字を削除する、fence を閉じる、`- Route In Progress: <値>`（remediation route が完了していれば `none`）を 1 行で書く。block 理由の推奨アクションが同じ内容を案内する

#### Affected Files

- `hooks/scripts/gdd_stop_hook.py`
- `hooks/scripts/lib/done_guard.py`
- `hooks/scripts/lib/done_block_message.py`
- `hooks/scripts/lib/tasklist_parse.py`
- `hooks/scripts/lib/state_fields.py`
- `hooks/scripts/lib/handoff_summary.py`
- `tests/test_done_guard_state_line_break_chars_contract.py`
- `tests/test_verification_block_message_contract.py`
- `tests/checks/active-steering-candidate-resolution.sh`（fixture の state.md に必須の `Route In Progress=none` を追加）

#### User Action Required

- state.md に `- Route In Progress: <値>`（完了していれば `none`）の行が無い、最後のその行を読めない、code fence が閉じていない、または LF / CR 以外の行区切り文字がある steering は、done が block される。block 理由に従って state.md を直す
- 実測（2026-09-19）: 手元の作業ディレクトリと steering-archive の `.steering/*/state.md`（`/tests/fixtures/` を除く）に対して、Stop hook を main と本変更の両方で実走した。この変更で done が allow から block に変わる steering は 0 件だった
  - `Route In Progress` のキー行が無く、tasklist が非 terminal のものは 120 ファイル（worktree の複製を除くと 32 steering）。すべて 2026-04〜07 の Tier 1 導入前の形式で、main でも tasklist の検査で既に block されている。本変更では block 理由に「Route In Progress の行がありません」が 1 行加わるだけ
  - 行区切り文字、最後のキー行を読めない形、write guard の形でだけキー行になるもの、区切りの混在、未閉 fence は 0 件

#### Known Limitations

- 隠れ見出し（D-29）は直していない。BOM 付きの `## Pending Tasks` は数えられる（block 側）。task 行の先頭に半角空白 1 個を置くと remaining から消える既知の限界が残る。塞ぐには `IndentedLineTests` の不変条件を変える設計判断が要る
- 正準のキー行の後ろにある崩れたキー行（太字、`*` 箇条書き、全角コロン、字下げ、ZWSP / NBSP）は読まず、正準のキー行の値で判定する。崩れ方は列挙で閉じられない開いた入力なので塞いでいない（実データでの該当 0 件。後続 Issue）
- skills の等号形とテンプレートのコロン形の食い違いは直していない（混在しても done guard は両方の値を見て block 側に倒す。後続 Issue）
- state.md を書くのは agent 自身なので、Check 3 は消し忘れを止める部品で、意図的な迂回（値を `none` に書き換える、state.md を消す）は防げない
- telemetry（`scripts/collect-gdd-telemetry.py`）と `detect-steering.sh` の `gdd_extract_route_in_progress` は、読めない state.md の route を空として扱ったまま（block しない表示・集計の経路）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
