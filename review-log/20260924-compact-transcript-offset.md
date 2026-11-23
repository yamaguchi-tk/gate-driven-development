---
lane: L1+
pr: 旧#182
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable。ユーザーの指示) + user | - | 0 | 0 | 0 | 2026-09-24T18:16+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ff845a02f18b7f1ffcfad7a41ce09ab71b5040c3 | 0 | 2 | 0 | 2026-09-24T18:44+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus（reviewer が Grep で review-log を読んだと申告。判断には使っていないとのこと） | b9140d2f7cfe667b90071cfc27cca483bfb985ea | 0 | 0 | 0 | 2026-09-24T19:06+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | 6c88eaac5b2ac26138c539408b8fda9935bacaea | 0 | 0 | 0 | 2026-09-24T19:29+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#182 review。2 回) | 4c715e72cbe04e6d0545f56d4bcc8578dce649c5 | 0 | 1 | 0 | 2026-09-25T08:56+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 8abd08696fa034280e797804b42b701e8ee1d0d4 | 0 | 0 | 0 | 2026-09-28T11:39+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | subagent-compaction-discrimination | fixed | 発端は 旧#169 の限界 1（subagent の compaction でも compact 自動復帰の判定が走る。accepted の常時 High）。**実測（Claude Code 2.1.280）**: PreCompact・SessionStart(compact)・PostCompact の入力は agent_id を持たず、hook の env にも agent を示すものは無い。通常の subagent（delegatedObservation でない）でも 3 つとも走る。headless の `/compact` で、hook の時点の main transcript の compact_boundary は 0 行、終了後に 1 行（hook の中では判定できない）。subagent の境界は `<session>/subagents/` の下にだけ書かれる（実データ 305 件すべて）。PreToolUse は subagent の tool 呼び出しに agent_id を付け、additionalContext を返せる。compaction の約 15% が subagent 側で、subagent に届いた注入は 11 回。その場で見分けるヒューリスティクスは 5〜19% を取りこぼす。**何を変え何を変えないか**: この PR（PR-1）は PreCompact が `CompactTranscriptOffset`（main transcript のバイト長）を書き、読む側の純関数 `gdd_compact_boundary_after_offset` を lib に足すだけ。発火の判定・SessionStart・hooks.json は変えない（PR-2 で配線）。**各 AC の閉じ方**: payload の形（無い・壊れている・非 object・path 欠落・空・非文字列・相対・subagents/・別 session・無いファイル・ディレクトリ・session id 無し）と offset の形（空・unknown・符号・空白・接尾辞・16 進・小数・先頭 0）、境界の形（type/subtype の一致・別 subtype・文字列中の出現・壊れた行）を列挙して閉じる。**閉じない残り**: 2.1.280 の内部の事実（subagent の PreCompact でも transcript_path が main のもの・subagent の境界は subagents/ にだけ書かれる・PreToolUse の agent_id）に依存する。読めない・壊れている・形式が変わったときは自動復帰しない側に倒す（ユーザーが限界として事前に承認）。**広い側／狭い側**: 同じ入力空間（subagent の compaction すべて）を閉じるのは A′（後から確かめる）と D（撤去）。D は main の自動復帰 90 回・39 session を失うので A′。**延期・削除する完了条件**: 読む側の配線（PreToolUse `*`・UserPromptSubmit）、SessionStart(compact) の縮小、上限の分岐での消費、再開をまたぐ古い印の無効化は PR-2。**QA の合否基準**: 新規 contract test が RED → GREEN、関係するテストと validate-plugin.sh が通る。**配線**: 書く側 = run-pre-compact-hook.sh（gdd_pre_compact_transcript_offset）、読む側 = gdd_compact_boundary_after_offset（PR-1 では入口からの配線なし。入口から効果までのテストは実際の PreCompact が書いた値で判定する）、同じ入力を読む既存の実装 = 無し（transcript を読む hook は他に無い）。**Opus と Fable の食い違い**: Opus は境界の数 N・バイト長 S・transcript_path の 3 つを書く案、Fable は S だけでよい（transcript のファイル名は CompactSessionId から導け、パスは setter の文字種で弾かれる）とした。S だけを採った。上書き race は両者とも指摘（同じ session の未消費の印があれば前の値を保つ）。**過去の教訓**: 「機械検査に自由文を解析させない」→ 境界は JSON の type/subtype で判定。「読めない設定値は止める側に倒す」→ offset の読めない値は判定不能。「完全性ではなく限界開示で止める」→ 版への依存は限界として書く。**ユーザーの決定**: 別の L1+ PR で直す（旧#169 は限界開示のまま）、hooks.json を変えてよい（PR-2）、読めないときに自動復帰しないことを限界として承認、2 本に分ける、PR-1 を Fable の絞った範囲で始める、D′ の測定をする（結果: PreCompact の出力は JSON の systemMessage でも plain でも compaction の要約に入った。opus・手動 /compact で各 1 回。PR-2 の設計の材料） |
| 独立1-F1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | PreCompact が新しく stdin を読むのに、本番の入口（GDD_STEERING_DIR 無し）と、stdin が閉じない場合のテストが無い。印の書き込みより前の読み取りなので、退行すると本番でだけ offset が unknown になるか、hook が timeout まで止まる |
| 独立1-F2 | 独立-1 | medium | no | self-inflicted | product | fixed | 前の値を保つ規則に期限が無い。既定ブランチ・上限で SessionStart が印を消費しないと、古い offset が保たれ、読む側をつなぐと古い main の境界で発火しうる。この PR では PR 本文の限界と「次の PR」に書き、発火を恒常的に断る判定で印を消費する修正は PR-2 で行う（読む側は PR-1 ではどこからも呼ばれない） |
| 独立1-F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | missing-file・directory・相対パスのテストが、ファイル名の検査で先に落ちており、isfile / isabs を消しても通る。ファイル名を <session>.jsonl にそろえ、FIFO も足す |
| 独立1-F4 | 独立-1 | low | no | self-inflicted | product | fixed | 読む側が境界ありを python3 の exit 0 だけで決めている。実行せずに 0 で終わる python3 で境界ありになる |
| 独立1-F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Summary（振る舞いは変わらない）と Changed が矛盾し、「自動復帰は起きず」が前の印が残る場合を含まない。unknown の条件に session id が取れない場合が無い |
| 独立1-F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界 2「形式が変わったときは境界が無い側に倒す」は、subagent の境界が main transcript に書かれるようになる変化では誤発火の側に倒れる。2 つに分けて書く |
| 独立1-F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | state-field-tiers.md の CompactTranscriptOffset の定義に、前の値を保つ規則が無い（schema と食い違う） |
| 独立1-A1 | 独立-1 | advisory | no | self-inflicted | product | accepted | 読む側が offset より後ろの全行を json.loads する。PR-2 で main の tool 呼び出しのたびに走るので、部分文字列での読み飛ばしと実データでの計測を PR-2 で行う。PR 本文に列挙 |
| 独立1-A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | `/subagents/` をパス全体の部分文字列で除外しており、上位に subagents という名前のディレクトリがあると main transcript まで unknown になる。PR 本文に列挙 |
| 独立1-A3 | 独立-1 | advisory | no | self-inflicted | product | accepted | payload をロケールの文字コードで読む（既存の SessionStart の解析と同じ形）。PR 本文に列挙 |
| 独立2-F1 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 前の値を保つ規則の「前の値が数字なら」を tiers にだけ足し、変更断片と state-schema.json の note は無条件のまま |
| 独立2-A1 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 相対パスのケースを parametrize から外した新しいテストは offset の 1 本だけを assert する（Status・CompactSource の assert が無い）。同じ経路は残りのケースで検査している。この PR で足したテスト同士の入れ替えで、main に対する緩和ではない。PR 本文に列挙 |
| 独立2-A2 | 独立-2 | advisory | no | self-inflicted | product | accepted | Windows のネイティブの python3 は出力の改行が \r\n になり、found・バイト長の照合が外れる（自動復帰しない側）。書く側・読む側・SessionStart の payload 解析を、Windows に対応するときにまとめて直す。PR 本文に列挙 |
| 独立3-F1 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | compact-resume.sh 冒頭の「どの関数も判定できないときは非 0」に対し、gdd_pre_compact_transcript_offset は常に 0 で unknown を出力する（既存の gdd_read_session_start_payload も同じ）。冒頭に例外を書く |
| 独立3-F2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | テストの docstring とコメントの「この PR は発火を変えない」が、offset の行を書けないと pre-compact を書かない変化を含まない。「state.md が既定の形なら」と限定する |
| 独立3-F3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | state-schema.json の read_by: CompactTranscriptOffset を state.md から読むのは run-pre-compact-hook.sh（前の値を保つ規則）で、gdd_compact_boundary_after_offset は値を渡されるだけ。CompactSource・CompactSessionId の read_by にも run-pre-compact-hook.sh が無い |
| 独立3-F4 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | state-field-tiers.md の「前の値が数字なら」が、schema・変更断片の「10 進の数字」と実装の ^[0-9]+$ にそろっていない |
| 独立3-A1 | 独立-3 | advisory | no | self-inflicted | product | accepted | 前の値を保つ規則は印を読んでから書き戻すまでロックが無く、消費と background の subagent の PreCompact が重なると、消費済みの印を pre-compact に戻しうる。読む側の配線（PR-2）で、書き込み直前の読み直しかロックと、その順序のテストを入れる。PR 本文に列挙 |
| 独立3-A2 | 独立-3 | advisory | no | self-inflicted | product | accepted | python3 -c が cwd のモジュール（json.py など）を先に読む。自動復帰しない側に倒れる。既存の SessionStart の payload 解析と同じ型。python3 -I にそろえる。PR 本文に列挙 |
| 独立3-A3 | 独立-3 | advisory | no | self-inflicted | product | accepted | 読む側が行ごとの json.loads で ValueError だけを捕まえ、RecursionError では走査全体が終わる（境界なしの側）。PR 本文に列挙 |
| pr1-M1 | PR後-1 | medium | no | self-inflicted | test-power | fixed | 変更断片の「python3 が無ければ unknown」を固定しているのは読む側だけで、書く側を入口から通すテストが無い。前の値を保つ規則が後から上書きするので、印が無いとき（unknown かつ pre-compact）と、同じ session の未消費の印＋10 進のとき（前の値を保つ）の 2 本が要る。テストだけを足した（巡を無効にしない） |
| pr1-M2 | PR後-1 | medium | no | self-inflicted | product | next-pr | 既存の発火テスト（test_compact_resume_writer_and_source.py の _pre_compact、test_compact_state_form_invariants.py）は stdin=DEVNULL のままで、この PR の後は毎回 CompactTranscriptOffset: unknown を書く。PR-2 で境界を発火の条件にすると I1/I3 が空振りし、test_baseline_form_fires と発火の assert が赤になる。PR-2 の必須作業として PR 本文の「次の PR」に書いた |
| pr1-A1 | PR後-1 | advisory | no | self-inflicted | product | accepted | CompactTranscriptOffset は書いたときの path を持たない。この PR では関数の引数の契約で足りる。PR-2 の配線時に、読む側の path を書く側と同じ述語で落とす以上の紐付けが要るかを確かめる |
| 独立4-A1 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | 独立レビューに渡した PR 本文の限界 2 に「（ユーザーが限界として事前に承認）」という経緯の記述がある。判断には使っていない。PR 本文から括弧書きを削り、限界を変更の性質として書く |
