---
lane: L1+
pr: 620
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | caf9ccad | 3 | 3 | 1 | 2026-10-30T23:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 1f0a85aa | 1 | 3 | 0 | 2026-10-31T00:05+09:00 |
| 方針メモ-1 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 1f0a85aa | 0 | 0 | 0 | 2026-10-31T00:20+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 55b01d26 | 0 | 0 | 0 | 2026-10-31T01:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（行ごとに想定した例外〔ValueError〕だけを捕まえる設計を、行ごとと全体の catch-all にした）。transcript の深い入れ子の行で RecursionError が抜け、gate 全体が落ちて Sonnet でも通っていた。再現テストを足した。commit: fb191e85 |
| r1-2 | 独立-1 | high | no | self-inflicted | wiring | fixed | 設計: 変えない（名簿のテストが新しい hook を拾う設計どおり）。test_hooks_kill_switch.py の ALL_HOOKS に新しい hook が無く CI が落ちる。commit: ec389324 |
| r1-3 | 独立-1 | high | no | self-inflicted | wiring | fixed | 設計: 変えない（件数の語の表を伸ばすだけ）。test_pre_push_gate_contract.py の _NUMBER_WORDS が fourteen までで、15 本で IndexError。commit: ec389324 |
| r1-4 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼の SessionStart の通知を UserPromptSubmit に置き換えていた。SessionStart にも登録し、payload の model か再開時の transcript で判定する。commit: fb191e85 |
| r1-5 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 依頼の「agent が書けるファイルは外し方にしません」に対し、全 hook 共通の kill switch（~/.claude/gdd-hooks-disabled）でもこの gate が外れる。依頼が専用の外し方だけを指すのか、kill switch も含むのか 2 通りに読める。推奨の「kill switch は全 hook の非常停止として残す」で進め、PR 本文の限界の節に問いを書いた |
| r1-6 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | fixed-models.md・subagent-dispatch.md・gdd-model-routing が、Sonnet の main（implementation tier・model-ack:sonnet・相談の sonnet 固定）を前提にしたまま |
| r1-7 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 確認待ち: 依頼の「resume」を /gdd-dev resume と /gdd-resume の起動に絞った。claude --resume の後に自然文で GDD を続ける経路は止めない。2 通りに読めるので、推奨の「コマンドの起動だけ」で進め、PR 本文の限界の節に問いを書いた |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の通知の時機が実装（信号ができた後の最初の発言）と合っていなかった。commit: なし（PR 本文） |
| r1-9 | 独立-1 | low | no | self-inflicted | product | accepted | 別のモデルで再開した直後の古い信号と、family を含まない /model の名前（Default など）を判定に使う |
| r1-10 | 独立-1 | low | no | self-inflicted | product | accepted | deny された main が setup-gdd-loop.sh を Bash で直接起動すると GDD の loop に入れる |
| r1-11 | 独立-1 | low | no | self-inflicted | product | accepted | Skill の名前の鍵が既存の 2 hook（name・skill_name・skill）と揃っていない |
| r1-12 | 独立-1 | low | no | self-inflicted | product | accepted | UserPromptExpansion の判定が command_name だけで、prompt を読まない |
| r1-13 | 独立-1 | low | no | self-inflicted | product | accepted | model の attachment の信号だけ、isSidechain を除いていない |
| r1-14 | 独立-1 | low | no | self-inflicted | product | accepted | Set model to の検索が local-command-stdout に限られていない |
| r1-15 | 独立-1 | low | no | self-inflicted | perf | accepted | 発言ごとに transcript を全部読む。印があっても読み終えてから見る |
| r1-16 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の hook の表と state dir の一覧に、transcript の読み取りと main-model-notice の印が無い |
| r1-17 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | README の「7 matcher」が PreToolUse の entry 8 個と合わない |
| r1-18 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の type が minor のまま（Opus の main が新しい前提条件になる） |
| r1-19 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の「kill switch でも止まる」が 2 通りに読めた。commit: fb191e85 |
| r1-20 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Haiku のときも通知が「Sonnet のとき」と書く |
| r1-21 | 独立-1 | advisory | no | self-inflicted | product | accepted | 印の置き場所が GDD_HOOK_STATE_DIR を読まない |
| r1-22 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | advisory: テンプレート外の記述あり（PR 本文の抜粋に実装の経緯）。次の巡の前に抜粋から除いた。commit: なし（PR 本文） |
| r2-1 | 独立-2 | high | no | self-inflicted | acceptance-set | fixed | 列挙: 設計: 変える（user の文字列のどこにあっても Set model to を拾う設計を、local-command-stdout のタグの直後に固定した許可リストにした。isSidechain を種類より先に見る）。要約・貼ったログ・subagent の報告の Set model to や sidechain の attachment で、Sonnet の main でも通っていた。方針メモ-1 で (a)。入力者は transcript に 4 件（subagent の報告 2・ユーザーの発言 1・compaction の要約 1）、許可リストの誤 block は本物 552 件中 0。commit: 21977eac |
| r2-2 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 新しいセッションの SessionStart では知らせていなかった（依頼は SessionStart で通知）。ANTHROPIC_MODEL と settings の model の既定で判定して知らせる。既定は止める判定には使わない。commit: 6ed76d96 |
| r2-3 | 独立-2 | medium | no | self-inflicted | acceptance-set | accepted | 通知の経路は payload・env・settings の model を使い、止める経路は transcript だけを読むので、同じセッションで食い違う文が出うる |
| r2-4 | 独立-2 | medium | no | self-inflicted | request-drift | re-reported | kill switch の扱い（r1-5 と同じ） |
| r2-5 | 独立-2 | medium | no | self-inflicted | test-power | fixed | 深い入れ子のテストが Python 3.12 以降では例外にならず、修正を戻しても通りえた。100 万段にした（3.9・3.14 とも RecursionError を確認）。commit: 8b5bf833 |
| r2-6 | 独立-2 | low | no | self-inflicted | product | accepted | SessionStart の分岐が source=compact を除いていない（subagent の compaction で誤って知らせる恐れ） |
| r2-7 | 独立-2 | low | no | self-inflicted | test-power | accepted | ensure_ascii を外した修正を固定するテストが無い |
| r2-8 | 独立-2 | low | no | self-inflicted | test-power | accepted | SessionStart のテストが payload と transcript の優先順位と文の種類を固定していない |
| r2-9 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文が「hook の入力にモデルの欄が無い」のままだった。commit: なし（PR 本文） |
| r2-10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | module docstring が SessionStart と payload の model に追随していない |
| r2-11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の hook の表と state dir の一覧に main-model-gate が無い |
| r2-12 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 断片の Validation が変えたテストを挙げていない |
| r2-13 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | test_hooks_kill_switch.py の docstring の一覧に main-model-gate が無い |
| r2-14 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | payload の model の経路が実在する証拠が無い（測った headless の版では来なかった） |
| m1-1 | 方針メモ-1 | advisory | no | self-inflicted | acceptance-set | fixed | 列挙: r2-1 の閉じ方。2 本とも (a) 許可リスト、タグの直後に固定する形を推した。割れた点なし。main の案（タグで始まる＋search）より狭く閉じた。commit: 21977eac |
| r3-1 | 独立-3 | low | no | self-inflicted | product | accepted | Codex も hooks.json を読むので、SessionStart の settings への fallback が Codex で Claude Code の既定から知らせうる（CLAUDE_CODE_ENTRYPOINT で絞っていない。Codex の SessionStart に session id が来なければ出ない） |
| r3-2 | 独立-3 | low | no | self-inflicted | test-power | accepted | 新しいセッションの env と settings の優先順をテストが固定していない |
| r3-3 | 独立-3 | low | no | self-inflicted | test-power | accepted | settings の local・project・user の優先順と、上位が Opus で下位が Sonnet のときに黙ることをテストが固定していない |
| r3-4 | 独立-3 | low | no | self-inflicted | test-power | accepted | /model の出力の .match を .search に戻しても通る（tag ごと引用した要約の形のテストが無い） |
| r3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | hooks.json の description の SessionStart が env と settings の既定に追随していない |
| r3-6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | run-main-model-gate-hook.sh の冒頭コメントの SessionStart が env と settings の既定に追随していない |
| r3-7 | 独立-3 | low | no | self-inflicted | product | accepted | settings の opusplan などの別名では、新しいセッションの開始で知らせない（止める判定は assistant の model で読むので影響なし） |
| r3-8 | 独立-3 | low | no | self-inflicted | product | accepted | 既定から決めたときも「今の main は X です」と断定する文で知らせる |
| r3-9 | 独立-3 | advisory | no | self-inflicted | product | accepted | 再開時に transcript を env より先に見る順が、実際の起動時の設定の優先と合うか未確認 |
| r3-10 | 独立-3 | advisory | no | self-inflicted | product | accepted | managed settings と CLAUDE_PROJECT_DIR を見ていない |
| r3-11 | 独立-3 | advisory | no | self-inflicted | product | accepted | payload に cwd が無く cwd が消えていると os.getcwd() で通知の分岐が落ちる（止める判定には届かない） |
| r3-12 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | docstring の sidechain の除外が assistant の行にだけ書かれている |
