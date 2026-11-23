---
lane: L1
pr: 旧#176
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus（材料はファイル渡し。旧#173 の定義をセッション開始時に読み込んだ） | 8d705eebf4422682b1491b3247017ce52680d114 | 0 | 1 | 0 | 2026-09-23T10:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus（材料はファイル渡し） | bd3bd9f7c1a5a514ae6789906a8111994c7fd670 | 0 | 0 | 0 | 2026-09-23T11:20+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus（材料はファイル渡し） | 06a165ab3e8b2a4bb5e819087160746bf5dbca57 | 0 | 0 | 0 | 2026-09-23T12:05+09:00 |
| PR後-1 | user（Cursor / gdd-pr-review のレビューを PR に投稿） | 0ba10ce6184c51660ffe51f22f1aa48f3b5f9b73 | 0 | 1 | 0 | 2026-09-23T21:54+09:00 |
| 独立-4 | general-purpose, 差分（無効化後）, model: opus, effort 継承（セッションが読み込んだ agent 定義が 旧#173 より前の版で、ファイルで渡した材料を読まずに diff 未到達を返したため fallback 経路。read-only は散文だけの規定） | 7c3c7a80fc81033e5c34c835d973d243d887abb3 | 0 | 0 | 0 | 2026-09-23T22:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | cursor-alias-leak | fixed | `references/cursor.md:113` が Cursor の Dialectic Counter を Claude Code の alias `opus` で指示していた（直前の行は Cursor が alias を解決できないと書いている）。一括置換の取りこぼし。Opus と tier 表の行への参照に直し、cursor.md に `opus` の alias が無いことを契約テストに足した |
| F2 | 独立-1 | low | no | self-inflicted | version-update-rule-drift | fixed | 版・世代が上がったときに直す場所の規定が、新設の § モデル名の書き方・`fixed-models.md:93`・`gdd-model-routing/SKILL.md:79` の 3 か所で食い違っていた。「同じ family の新しい版」と「alias で表せない新しい family」に分けて揃えた |
| F3 | 独立-1 | low | no | self-inflicted | alias-rule-overclaim | fixed | 「Claude Code の列と散文は alias で書く」の断定が、表の `Sonnet`・`Haiku` の表記と、大文字小文字を区別しないテストと合っていなかった。規定を「Claude の名前には版数を書かない」に直し、「Claude の」を足した |
| F4 | 独立-1 | low | no | self-inflicted | eval-expected-stale | fixed | `evals/evals.json` の eval 57 の期待回答が「Opus 5」のままで、PR 本文は経緯の記録と分類していた。期待回答は今のスキルに対するものなので「Opus」に直した |
| F5 | 独立-1 | low | no | self-inflicted | style | fixed | 新しいテストが共有モジュール `_paths` を使わずにパスを組み立てていた。`from _paths import PLUGIN_ROOT, REPO_ROOT` に直した |
| F6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | alias の解決先の断定が 1 回の実測からの一般化で、既定の設定に限る旨が無い。advisory のため PR 本文に列挙する（F3 の修正で「既定の設定では」と、解決先を固定した環境の注記は入れた） |
| F7 | 独立-1 | advisory | no | inherited | doc-claim | accepted | `docs/VERSIONING.md`・`docs/DISTRIBUTION_READINESS.md` の例示に「Opus 5」が残り、PR 本文の限界に載っていない。PR 本文の限界に足す |
| G1 | 独立-2 | low | no | self-inflicted | version-update-rule-drift | fixed | F2 の修正で書き直した `fixed-models.md:93` の「本 reference だけを更新する」が、:17 の「2 行（うち 1 行は cursor.md）だけを直す」と食い違っていた。範囲を「本 reference を正本とし、Claude の版は 2 行だけを直す」に書いた |
| G2 | 独立-2 | low | no | self-inflicted | alias-rule-overclaim | fixed | F6 を受けて :16 に足した「既定の設定では」の限定が、断片の User Action Required・SKILL.md:78・テストの docstring に入っていなかった。3 か所に足し、:16 に「その後に開いたセッションから」をそろえた |
| G3 | 独立-2 | low | no | self-inflicted | test-power | fixed | F1 のテストが cursor.md 全文の `` `opus` `` の有無だけを見ており、バッククォートなしの `opus` と補助の `skills/gdd-model-routing/references/cursor.md` を通していた。2 つの cursor.md の Counter の行に絞り、語で探す形にした（Counter の行を alias に戻すと落ちることを変異で確認） |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文と断片に、4 つ目の検査・SKILL.md:79 の発火条件の変更・eval の期待回答の更新が無かった。SKILL.md:79 は、同じ family の新しい版でも frontmatter の effort の見直しが発火するよう「新しい版や model family が出たとき」に戻し、PR 本文と断片の Affected Files に足した |
| G5 | 独立-2 | advisory | no | inherited | bookkeeping | accepted | 呼び出しがこの branch のディスク上の定義（本文を貼る方式）ではなく、旧#173 のファイル渡しのテンプレートだった。セッション開始時に 旧#173 の定義を読み込んだため。旧#173 のマージで揃う。PR 本文に書く |
| H1 | 独立-3 | low | no | self-inflicted | alias-rule-overclaim | next-pr | § モデル名の書き方は起動名を alias と定めるが、表の Claude Code 列と README は `Sonnet`・`Haiku`、散文は `Opus + effort=high` が混ざる。`ALIAS` が大文字小文字を無視するので、表示名の `Opus` でもテストが通る。表記を小文字の alias に揃えて IGNORECASE を外すか、§ と断片を「版数なしの family 名」に言い換える |
| H2 | 独立-3 | low | no | self-inflicted | history-lost-version | next-pr | 過去の実測の記述（`fixed-models.md:47`、`gdd-model-routing/SKILL.md:111`）を alias に置き換えたため、当時どのモデルで測ったかが読めない。「当時の Opus」に揃え、版が要る過去の記述の書き方を § に足す |
| H3 | 独立-3 | low | no | self-inflicted | applied-model-record | next-pr | 判断の書き方・実適用 model の記録が alias になり、Opus 5 と 5.5 のどちらで走ったかを区別できない。版が上がったことを知らせる仕組みも無い。テンプレートに「transcript の model ID を確かめたら併記する」を足し、限界に書く |
| H4 | 独立-3 | low | no | self-inflicted | cursor-counter-pointer | next-pr | Cursor の Counter の行の一部（`cursor.md:74,87,97`・`cursor-guide.md:62`・`gdd-model-routing/SKILL.md:61,99,125,139`）に、版の書かれた `dialectic_counter` 行への参照が無い。SKILL.md:79 の見直しの規定が 2 行の更新に触れていない |
| H5 | 独立-3 | low | no | self-inflicted | test-power | next-pr | `VERSIONED` の `\b` が和文に続けた「当時のOpus 5」を見逃す。`Opus5`・`Opus-5`・`claude-3-opus` も通る。今の走査対象には 0 件。境界を `(?<![A-Za-z])` にし、形を広げ、和文に続けた場合のケースを足す |
| H6 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 数の記述が差分と合わない（置き換えは約 94 か所で「約 110」は多い。固定文字列を合わせた既存テストは 3 本で、x64 は版を落として比べる正規化も入れた）。PR 本文は後者に合わせて書いた。docstring の数は次の PR で直す |
| H7 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | § の走査範囲の記述が、テストの実際の範囲（root の `.claude/agents`・`CLAUDE.md`・`AGENTS.md` も走査）より狭い。root CLAUDE.md に実測の model ID を書くと GDD のテストが落ちる。§ に書き足すか、root の CLAUDE.md・AGENTS.md を走査から外す |
| H8 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレートの 3 欄がファイルのパスで渡され、欄の外に材料の説明がある。reviewer は、読み込まれていた定義は本文を貼る方式だったと申告した（3 ファイルとも末尾まで読めたのでレビューした）。PR 本文の限界の記述を申告に合わせて直した |
| I1 | PR後-1 | medium | no | self-inflicted | cursor-counter-pointer | fixed | Cursor の Counter を版のない `Opus` で指示する表・箇条書き（`cursor.md` 19・74・79・87・97・142 行、`cursor-guide.md` 16・56・62 行、`gdd-model-routing/SKILL.md` 21・99・125・139 行）が、版を書いた `dialectic_counter` 行を指しておらず、表だけを読む利用者に `Opus 5.5` が届かない。`fixed-models.md` の「inline 値は tier 定義と一致させる」も 2 行の例外と食い違う。13 行に参照を足し、同じ規定に例外を書き、参照の有無を検査するテストを足した（RED 7f7d1e5b → GREEN 7c3c7a80）。H4 のうち参照の欠けはこれで直り、SKILL.md:79 の見直しの規定は H4 のまま次の PR に残る |
| J1 | 独立-4 | medium | no | self-inflicted | test-power | next-pr | 新しいテストは「`Counter` か `reasoning.effort` を含む行」だけを見るので、`dialectic-review.md:126`（Host Adapter 表の Cursor 行。Counter の欄に版のない Opus があり `dialectic_counter` 行を指さない）を拾わない。`fixed-models.md:17` の「指さない行があっても落ちる」は、この範囲では言い過ぎになる。差分巡（無効化後）で blocking でないため `next-pr`。次の PR で、同行に参照を足し、表の行は列名から Counter の列を特定して判定する（または記述を検出範囲に合わせる） |
| J2 | 独立-4 | low | no | self-inflicted | test-power | next-pr | 新しいテストの `(?<![\w-])Opus` は、Python の `\w` が和字を含むため「はOpusで」のように和文に続けた書き方を拾わない（今の 5 ファイルに該当は 0 件）。H5 と同じ型。次の PR で前後の判定を ASCII に限る |
| J3 | 独立-4 | low | no | inherited | doc-claim | next-pr | `dialectic-review.md:127`（Host Adapter 表の Codex 行）の Counter が「Opus または別 GPT high」で、Codex は Anthropic を使えないとする `codex.md`・`gdd-model-routing/SKILL.md` と食い違う（origin: pre-existing、差分の外の同じ表）。J1 と同じ表なので次の PR でまとめて直す |
