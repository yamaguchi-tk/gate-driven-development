---
lane: L1+
pr: 旧#208
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable。ユーザーの指示) + user | - | 0 | 0 | 0 | 2026-09-28T15:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 31460a0b5cb0576b8cbe6a00ea24956a18b61c85 | 0 | 1 | 0 | 2026-09-28T16:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 88ab777836d4e8c7465cee1b5be3343245c8c2dd | 0 | 1 | 0 | 2026-09-28T17:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | 755add1a2d7efb809bdade64eaeaedef8f6abdb5 | 1 | 0 | 1 | 2026-09-28T18:10+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | dc7696b1383bbec88eb81d55998c7effed5132b2 | 1 | 1 | 1 | 2026-09-28T19:00+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) | - | 0 | 0 | 0 | 2026-09-28T19:20+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | f06948cd69aa83a41fa0a3d1260bf7084f2383ff | 1 | 0 | 1 | 2026-09-28T21:40+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) | - | 0 | 0 | 0 | 2026-09-28T21:50+09:00 |
| 独立-6 | light-lane-independent-reviewer, 全差分（無効化後・main 取り込み。base は取り込んだ main 0f62d081）, model: opus | 0f66874709cc700a54f657d984f76d89d8894f2e | 0 | 0 | 0 | 2026-09-29T04:30+09:00 |
| 独立-7 | light-lane-independent-reviewer, 全差分（無効化後・main の 2 回目の取り込み。base は取り込んだ main 7b7c7655）, model: opus | e0b7c949412b2e19cc0c98d5129834f0a80753dd | 0 | 0 | 0 | 2026-09-29T06:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | subagent-compaction-discrimination | fixed | 発端は 旧#169 の限界 1（subagent の compaction でも compact 自動復帰が走る。accepted の常時 High）の PR-2。**実測**: 自動復帰の注入は main 約 90 回・41 session、subagent 約 6 回・3 session。注入の直後に main が Skill gdd-dev を呼んだのは 2/90 で、注入の無い場面の基準（2.9%）と変わらない（Fable）。注入の有無で比べると、自律的な継続 72% 対 76%、停止 26% 対 22%。PreCompact のリマインダーは `grep "^Resume From:"` の 1 形だけを読み、実データの state.md 127 件の約 69% で出ていなかった。**選択肢**: A′（読む側を PreToolUse `*`＋UserPromptSubmit に移す。+1,000 行超、CC 2.1.280 の内部の 3 事実に依存し、前提が崩れると常時 High (b) が再発）、D′（自動復帰の注入をやめる）、止める。**何を変え何を変えないか**: D′。SessionStart(compact) は何も出さない（`[gdd:reboot]`・`[gdd:paused]` とも、自律実行中の main を止めるため）。直前の turn の失敗の記録は消費しない。PreCompact は state.md に書かず、`Resume From`・`Next Action` を 4 形で読んで事実だけを要約器に渡す（subagent の要約にも入るので、役割を問わない文）。印 6 つと `.gdd_is_running`・`GDD_MAX_AUTO_CYCLES` を廃止。Safe Resume・UserPromptSubmit・plan-reread は変えない。**AC の閉じ方**: 入口（SessionStart の payload・PreCompact）から、出力と state.md のバイト不変を確かめるテスト。source の形（compact・startup・空・壊れた JSON・source 無し・python3 無し）を列挙。**閉じない残り**: source が読めないときは通常の流れに落ちる（compact の直後でも `[gdd:reboot]` が出うる）。compaction の後に再開の案内が出ないので、要約に状態が無ければ利用者が `/gdd-dev resume` を打つ。**広い側／狭い側**: 同じ入力空間（compaction の後の注入すべて）を閉じるのは A′ と D′。D′ は判定自体を消すので広い側に当たる。**延期**: なし。PR-1 の next-pr（独立3-F1〜F4、pr1-M2）は対象のコードが消えるので不要。**QA**: 新規の入口テストが通る、関係するテストと validate-plugin.sh が通る。**配線**: 書く側 = なし（PreCompact は書かない）、読む側 = SessionStart の `_gdd_session_start_source`（payload の source）、PreCompact の `gdd_extract_doc_field`（Resume From・Next Action）。同じ入力を読む既存の実装 = UserPromptSubmit・plan-reread（state.md の routing field）、Safe Resume（`gdd_is_default_branch` を detect-steering へ移した）。**Opus と Fable の食い違い**: Opus は D′ を推奨し、compact の直後に `[gdd:paused]` だけを出す案、Fable も D′ を推奨し、何も出さない案。`[gdd:paused]` は「再開しない」を含み自律的な継続と矛盾するので、何も出さない案を採った。**過去の教訓**: 「機械検査に自由文を解析させない」→ source は JSON の固定フィールドで判定。「読めない設定値は止める側に倒す」→ 読めない source は注入を止める側ではなく通常の流れに倒す（止める側＝何も出さない、にすると SessionStart の payload が壊れた startup で案内が消える）ので、限界として書く。「完全性ではなく限界開示で止める」。**ユーザーの決定**: A′ を考えていたが Fable の意見を聞いた上で「D′ で進める」 |
| I1-1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 沈黙の判定（SessionStart の source）を守っていた payload の形の検査（resume・clear・source が配列・payload が配列・compact を含む壊れた JSON・cwd に compact・session_id が compact）と stdin が開いたままの起動の検査が、削除したテストから移っていなかった。新しいテストに足した（文字列一致に崩す変異 2 つが落ちることを確かめた） |
| I1-2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 移した `gdd_is_default_branch` の master・trunk を固定するテストが無くなっていた。既存の develop・development のテストに足した |
| I1-3 | 独立-1 | low | no | self-inflicted | product | fixed | PreCompact の Next Action が state.md だけから読まれ、build 中の正本（tasklist.md）と 縦棒以降の正規化が SessionStart・UserPromptSubmit と割れていた。同じ読み方にした |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `phase-gate-prechecks.md` の書き換えた文が、compaction の直後の沈黙と食い違っていた。context field は次のユーザー入力で UserPromptSubmit が入れると直し、PR 本文の限界に足した |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 削除した compact 復帰の経路を前提にしたコメント（UserPromptSubmit・plan-reread）、plan-reread の注入文、テストの docstring を直した |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `SymmetryWithCompactPathTests` の名前・docstring・メッセージが無い経路を指していた。Quick Reboot と UserPromptSubmit の対称性として直した |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `state-schema.json` の canonical_line_form.note が、2 つの hook を規約を共有する実装に数えていた（正本テストの列挙と不一致）。gdd_extract_doc_field 経由と書いた |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「skill 名を含めない」が値については成り立たず、テストの不在の assert が fixture で必ず通っていた。PR 本文を「固定の文に指示を入れない。値はそのまま渡す」に直し、テストを固定の文と値の通過に分けた |
| I1-9 | 独立-1 | low | no | self-inflicted | test-power | fixed | 廃止した印の読み手が無いことの検査が、bullet 形・正規表現形と plugin の scripts/ を見ていなかった。どちらも見るようにした（`grep -m1 '^- Status:'` の変異が落ちることを確かめた） |
| I1-10 | 独立-1 | low | no | self-inflicted | test-power | fixed | python3 が無いときの PreCompact のテストが、steering の検出で終わり文の組み立てまで届いていなかった。GDD_STEERING_DIR を渡し、不正な UTF-8 を値に混ぜた |
| I1-11 | 独立-1 | low | no | self-inflicted | product | fixed | PreCompact の state.md の場所が sanitize されず、不正な UTF-8 で出力が消えうる。python3 が無いと BSD tr が不正なバイト列で失敗しうる。sanitize を python の中にまとめた |
| I1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 既存の `.gdd_is_running` が残ることが限界の節に無かった。PR 本文の限界に足した |
| I1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 3 本（20260919・20260921・20260924）が廃止した機能の案内を載せたまま残る。通常の PR では断片を書き換えないので、次のリリースの dry-run で版の節から外す |
| I2-1 | 独立-2 | medium | no | self-inflicted | test-power | fixed | 廃止した印の検出パターンの否定後読みに量指定子を足したことで、`^\s*Status:` のような量指定子の直後の field 名を検出しなくなっていた（assert の緩和）。除外を「英字＋`\s`＋量指定子」の並びに限り、パターンそのものの自己テストを足した |
| I2-2 | 独立-2 | low | no | self-inflicted | product | fixed | PreCompact の JSON を ensure_ascii の既定で出したため、要約器が読む文の非 ASCII が `\uXXXX` になっていた。ensure_ascii=False・UTF-8 で出し、C ロケールでも生のバイトに日本語が入ることを確かめるテストを足した |
| I2-3 | 独立-2 | low | no | self-inflicted | test-power | fixed | 不正な UTF-8 の場所の subtest が、捨てずに孤立サロゲートのまま残す変異を落とせなかった。サロゲートが無いことと、除いた後の場所が入ることを確かめた |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | `phase-gate-prechecks.md` の「新しいセッションでは SessionStart が context field を注入する」が実装（別 session は Safe Resume、Approved Direction は field として注入しない）と合わなかった。UserPromptSubmit が session 一致後に注入、Quick Reboot は同じ session のときだけ Last Handoff Summary、と直した |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | fixed | `SymmetryWithQuickRebootTests` が Quick Reboot も Approved Direction を扱うと主張していた。Quick Reboot は Last Handoff Summary だけと直した |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | `state-schema.json` の note の括弧書き（hook は gdd_extract_doc_field 経由）が、同じファイルの hook 側の別の reader と食い違っていた。PreCompact・SessionStart の routing field に狭めた |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PreCompact のコメント・断片・PR 本文の「SessionStart・UserPromptSubmit と同じ」は、tasklist.md が空のとき（あちらは Resume From、こちらは state.md）に成り立たなかった。判定関数が同じこと、順は gdd_validate_active_state_fields と同じことに直した |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | README の PreCompact の行が、build 中の Next Action の出どころ（tasklist.md）を書いていなかった |
| I2-9 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | テストのコメント「python3 が無いときの文字単位の切り詰めを通す」が、bash 側の切り詰めを消した後で古くなっていた |
| I2-10 | 独立-2 | advisory | no | self-inflicted | product | fixed | PreCompact の値は 128 字までの自由文のまま要約器に入る（steering write guard は値の形を制限しない）。PR 本文の限界を「128 字までの自由文」に直した |
| I2-11 | 独立-2 | advisory | no | self-inflicted | product | fixed | `os.environb` は POSIX 専用で、Windows では PreCompact が何も出さなくなる。分岐を足さずに `os.environ` を surrogateescape で bytes に戻す形にした |
| I3-1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | UTF-8 以外のロケール（EUC-JP など）で、非 ASCII の cwd を含む compaction の payload を `json.load(sys.stdin)` が decode できず、沈黙の判定（常時 High (b)）が外れて `[gdd:reboot]`・`[gdd:paused]` が出ていた。ja_JP.eucJP で再現するテストを先に足し（ロケールが無い環境では skip）、`sys.stdin.buffer` で読むようにした |
| I3-2 | 独立-3 | low | no | self-inflicted | product | fixed | PreCompact の `clean()` が環境変数を UTF-8 と仮定して bytes に戻しており、ファイルシステムの encoding が UTF-8 以外だと値が化ける（I3-1 と根が同じ）。`os.fsencode` にした。再現できる環境が無く、テストは無い |
| I3-3 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 廃止した印の検出パターンが列挙型で、`Status[:=]`・`Status *:`・`\bStatus\b`・alternation・引用符の無い引数などで読み手が戻っても通る。既定を反転し、既知の複合名を許可リストで除く形に直す |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文の「tasklist.md に値があれば SessionStart・UserPromptSubmit と同じ値」が、UserPromptSubmit が最初の空白でも切る点で言い過ぎだった。断片と PR 本文を直した |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | `phase-gate-prechecks.md` と `test_cross_session_handoff_contract.py` の docstring の「SessionStart は同じ session と判定したときだけ Last Handoff Summary を入れる」が、session id を取れない runtime の経路と合わない。「PreCompact が渡すのは Resume From・Next Action だけ」も state.md の場所が抜けている |
| I4-1 | 独立-4 | high | yes | inherited | fail-open | accepted | block gate の run-pre-push-gate-hook.sh（`json.load(sys.stdin)` を `except Exception: pass` で握り push を通す）と validate-worktree-command.py（UnicodeDecodeError が except JSONDecodeError に捕まらず exit 1 で guard が落ちる）が、UTF-8 以外のロケール（EUC-JP など）で非 ASCII を含む payload を読めず fail-open する。I3-1 と同じ仕組みの既存の欠陥で、stdin をロケールで読む hook は計 15 ファイル。安全策 4 の発火と方針メモ-1 により、この PR では直さず、直後の次の PR（hook の stdin・stdout をロケールに依らず UTF-8 にする）で直す。実害クラスなので next-pr にできず accepted にし、PR 本文の限界の節の先頭に書く |
| I4-2 | 独立-4 | medium | no | self-inflicted | test-power | fixed | 足したロケールのテストが、EUC-JP のロケールが無い CI（ubuntu）では skip され、`sys.stdin.buffer` の回帰を CI が守らなかった。ロケールが無ければ localedef でテストの中に作り（root は不要、ubuntu:24.04 で実測）、stdin が EUC-JP になったことを確かめてから走らせる。CI では作れなければ skip せずに落とす |
| I4-3 | 独立-4 | low | no | inherited | product | next-pr | `gdd_truncate_chars`・UserPromptSubmit の prompt の読み方など、block しない hook の入出力もロケールに依存している（I4-1 と根が同じ）。次の PR で一緒に直す |
| P2 | 方針メモ-1 | advisory | no | self-inflicted | locale-dependent-stdin | fixed | 安全策 4 が発火（ロケール依存の decode の high が独立-3・独立-4 の 2 巡）。**材料**: 対象は block gate（pre-push・worktree guard・pre-pr・merge など）。入力は Claude Code が作る UTF-8 の JSON で、欠陥は利用者のロケールが UTF-8 以外のマルチバイトのときだけ起きる（このセッションは LANG 未設定＝C で Python は UTF-8 mode。実データでの観測手段は無い）。独立 4 巡・約 4 時間。**選択肢**: (A) この PR で 15 ファイルを直す、(B) この PR から外して直後の次の PR で直し、限界の節に書く、(C) 止める。**Opus の推奨**: (B)。(A) は 15 ファイルの判定のコードで巡が無効になり、1 PR 1 課題と「実装中の別発見は差分に入れない」に反し、同じクラスタで安全策 4 が再発火する。(C) は block gate の fail-open が記録されずに残る。実害クラスは next-pr にできないので accepted とし、2 回目の差分巡は回さない（同じ pre-existing の high が再び出て数えられるため）。medium は localedef でテストの中にロケールを作って閉じる。**メインの案との食い違い**: なし。**決定**: 2026-09-28 のユーザー方針（設計変更は内部相談で決める）に従い (B)。merge-ready とは書かず、マージの判断はユーザーに渡す |
| I5-0 | 独立-5 | low | no | self-inflicted | test-power | fixed | （独立-4 の後の CI の赤）CI で EUC-JP のロケールを作れていなかった。localedef は出力先の親ディレクトリを作らない（ubuntu:24.04 の container で再現）。親を作り、失敗したら localedef の stderr を出す。さらに Linux では python の argv・環境変数もロケールで decode され、`-c` のプログラムの日本語が壊れて SessionStart の沈黙の判定が外れ、PreCompact は何も出さなかった（macOS では出ない）。2 つの hook の python を `-X utf8` で起動した |
| I5-1 | 独立-5 | high | yes | inherited | fail-open | accepted | pre-push gate・pre-PR gate の `python3 -c` の本文の日本語が、Linux の UTF-8 以外のロケールで起動時に decode できず、gate が allow に倒れる。I4-1 と同じ既存の欠陥（ロケール依存）。方針メモ-2 のとおり、ロケールを直す PR（kill-switch.sh で LC_ALL=C.UTF-8 と PYTHONUTF8=1 を export）を先にマージし、main を取り込んでから差分巡で確かめる |
| I5-2 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界「日本語を含む state.md から値を読めず、PreCompact は何も出さない」が、片方だけ読めないとき（`(なし)` として渡る）と、steering を検出する python が `-X utf8` でないことと合わなかった。PR 本文を直した |
| I5-3 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | CI がロケールの用意（localedef と i18n の定義）に依存するようになったことが PR 本文に無かった。PR 本文に書いた |
| P3 | 方針メモ-2 | advisory | no | self-inflicted | locale-dependent-stdin | fixed | 独立-5 でも同じクラスタ（ロケール依存）の既存の high が出た。accepted のまま 旧#208 をマージせず、順序を入れ替える（Opus の B′）。ロケールを直す PR を main から先に出してマージし、main を取り込んで差分巡（無効化後）を回す。ロケールの設計は Opus の推奨（kill-switch.sh の末尾で LC_ALL=C.UTF-8 と PYTHONUTF8=1 を export。PYTHONUTF8 だけでは BSD awk・sed で gate のテスト 284 件が落ちたまま、と実測）。ユーザーの指示（2026-09-28: 自律的にマージしてよい、当初の予定を実装しきるまで進める）により内部で決定 |
| I6-1 | 独立-6 | medium | no | self-inflicted | session-scope | next-pr | PreCompact が local state の session を照合せずに、別 session の steering の Resume From・Next Action・場所を要約器へ渡す。UserPromptSubmit・plan-reread は `gdd_session_continuity_ok` で止め、SessionStart は Safe Resume で `[gdd:paused]` にする（受理集合の非対称）。block しない hook |
| I6-2 | 独立-6 | low | no | self-inflicted | test-power | next-pr | EUC-JP で hook を起動する 2 本は、kill-switch.sh の `LC_ALL=C.UTF-8` の上書きで、`-X utf8` を外しても通る。docstring・コメントの古い記述と、`_euc_jp_locale_env` の `_locale_support.py` との重複もあわせて直す |
| I6-3 | 独立-6 | low | no | self-inflicted | test-power | next-pr | PreCompact の「指示を入れない」を 5 語の不在だけで確かめている。文は入力だけで決まるので全文で assert できる |
| I6-4 | 独立-6 | low | no | inherited | product | next-pr | PreCompact は Next Action だけ縦棒以降を落とし、Resume From は落とさない。SessionStart・UserPromptSubmit は両方切る |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | next-pr | `phase-gate-prechecks.md`・README の PreCompact の説明に state.md の場所が抜け、session の照合の説明が、session id が取れない runtime の fail-open と合わない（I3-5 と同じ箇所） |
| I6-6 | 独立-6 | low | no | inherited | doc-claim | next-pr | `gdd-brainstorming` の discard 手順が、廃止した印の `Status` に `Discarded` を書かせている |
| I6-7 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | 限界の節に、PreCompact のリマインダー（`<gdd-phase>`・委譲の注意）が出なくなることと、state.md の場所も自由文として要約器に入ることが無い。PR 本文の限界に足した |
| I7-1 | 独立-7 | low | no | self-inflicted | test-power | re-reported | EUC-JP で hook を起動する 2 本が、kill-switch.sh の上書きで `-X utf8` の有無を見分けられない（I6-2 の再掲） |
| I7-2 | 独立-7 | low | no | self-inflicted | test-power | next-pr | compact の payload を書いたまま stdin が閉じない起動を、どのテストも通していない。timeout のときに途中の入力が残るかは bash の版に依存する（未確認） |
| I7-3 | 独立-7 | low | no | self-inflicted | test-power | re-reported | `_retired_mark_pattern` が `Status[=:]`・語境界・awk の書き方の読み手を拾えない（I3-3 の再掲） |
| I7-4 | 独立-7 | low | no | self-inflicted | doc-claim | next-pr | `lib/kill-switch.sh` のコメント「今の hook に `-I` の起動は無い」が、SessionStart・PreCompact の `python3 -I -X utf8` と合わない |
| I7-5 | 独立-7 | low | no | self-inflicted | doc-claim | re-reported | `phase-gate-prechecks.md` の「同じ session と判定したときだけ Last Handoff Summary を入れる」が、session id が渡らない runtime の扱いより狭い（I6-5 の再掲） |
| I7-6 | 独立-7 | low | no | self-inflicted | style | next-pr | テストのコメントが、定義の無い `RETIRED_MARKS` を参照している |
| I7-7 | 独立-7 | low | no | self-inflicted | style | next-pr | `test_canonical_field_line_anchoring_contract.py` の `import os` が使われなくなった |
| I7-8 | 独立-7 | low | no | inherited | doc-claim | re-reported | `gdd-brainstorming` の discard 手順が `Status: Discarded` を書かせている（I6-6 の再掲） |
| I7-9 | 独立-7 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり：PR 本文の抜粋の目的の節に、前の PR の限界と PR 番号による経緯（旧#169・旧#182）が入っていた。判断には使われていない |
