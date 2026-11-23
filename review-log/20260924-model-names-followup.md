---
lane: L1
pr: 旧#178
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承（セッションが読み込んだ agent 定義が 旧#173 より前の版のため fallback 経路。read-only は散文だけの規定）。近道の 1 巡 | a54aee062302e3d5275cdd5bfc1f3b8a76aaf14d | 0 | 0 | 0 | 2026-09-24T11:05+09:00 |
| PR後-1 | user（PR 上の再レビュー） | b69bfbc2ca39c62f5197aeac22d935d42e64148c | 0 | 0 | 0 | 2026-09-24T18:26+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 独立-1 | medium | no | inherited | test-power | next-pr | `test_cursor_counter_is_not_given_as_claude_code_alias` の `alias` の正規表現が `\w` のままで、「Counterはopusで」のように和文に続けた小文字の alias を見逃す。この PR が `VERSIONED`・`COUNTER_OPUS` を ASCII に限ったのと対になる片方。近道のため `next-pr` |
| K2 | 独立-1 | medium | no | self-inflicted | test-power | next-pr | `test_claude_code_table_cells_use_lowercase_alias` に拾ったセルの件数の下限が無く、`_claude_code_cells` が何も返さなくなっても通る。下限の assert か、合成した表での単体テストを足す。近道のため `next-pr` |
| K3 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | `gdd-model-routing/SKILL.md:111` の「当時の Opus の途中の世代」に日付が無く、同じ PR で足した「日付を添える」に反する。製品仕様の記述なので、版に触れない元の書き方に戻すか日付を添える |
| K4 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 「§ モデル名の書き方 の 2 行だけを直す」（`gdd-model-routing/SKILL.md:143` の見直しの規定、変更断片）が、§ の本文の 2 行とも読める。`fixed-models.md` と `cursor.md` の `dialectic_counter` 行を名指しする |
| K5 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | `fixed-models.md:19` の「上の規定は … が固定する」が言い過ぎ。frontmatter・`Agent(model=…)` の alias、過去の実測の日付、model ID の併記はテストが検査しない。「上の規定のうち次のものは」に変える |
| K6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「古い正規表現はこの 6 通りを見逃す」が、版付きの名前の 6 例のことと読める（実際は版付きの名前 5 例と Counter の `Opus` 1 例の計 6 通り）。「README の見出し」も実際は箇条書きの項目。PR 作成前に PR 本文を直した（PR 本文だけの修正） |
| K7 | 独立-1 | low | no | inherited | doc-claim | next-pr | `references/subagent-dispatch.md:46-48` のフェーズ表の「モデル」列（Claude Code での起動に使う名前）が、大文字の `Sonnet`・`Opus` のまま。見出しが `Claude Code` でないため、§ の規定にも新しいテストにも掛からない。次の PR で揃え、規定の範囲も決める |
| K8 | 独立-1 | low | no | self-inflicted | style | next-pr | `gdd-model-routing/SKILL.md:43` の「6 件を 当時の Opus+high」に余分な空白がある |
| L1 | PR後-1 | medium | no | self-inflicted | test-power | re-reported | K2 の再掲。`_claude_code_cells()` が空を返しても通る。件数の下限と合成した表での単体テストを足す案。次の PR（方針 C: 例外の 2 行を無くし、テストを「版付きの名前が 1 つも無い」の 1 本に縮める）で、表の読み取りと検査ごと消す |
| L2 | PR後-1 | low | no | self-inflicted | test-power | re-reported | K1 の再掲。`test_cursor_counter_is_not_given_as_claude_code_alias` の `alias` の正規表現が `\w` のまま。方針 C でこの検査ごと消す |
| L3 | PR後-1 | low | no | self-inflicted | doc-claim | re-reported | K4 の再掲。「§ モデル名の書き方 の 2 行だけを直す」が曖昧。方針 C で直す行が無くなり、文ごと消す |
