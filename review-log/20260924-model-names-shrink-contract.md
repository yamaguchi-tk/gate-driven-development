---
lane: L1
pr: 旧#184
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承（セッションが読み込んだ agent 定義が 旧#173 より前の版のため fallback 経路。read-only は散文だけの規定） | aff0b6df47fafc59041b5453675a6ba8ddc93a79 | 0 | 0 | 0 | 2026-09-24T20:30+09:00 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承（fallback 経路。理由は独立-1 と同じ） | 6002a56e424a7880f93ddeab31c7cf84327c33c5 | 0 | 0 | 0 | 2026-09-24T20:45+09:00 |
| 独立-3 | general-purpose, 全差分, model: opus, effort 継承（fallback 経路。理由は独立-1 と同じ） | 6002a56e424a7880f93ddeab31c7cf84327c33c5 | 0 | 0 | 0 | 2026-09-24T21:00+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#184 review, インラインコメント 3 件) | 85b5801043c5874552102ba3036f58b1e0265181 | 0 | 0 | 0 | 2026-09-28T10:00+09:00 |
| PR後-2 | yamaguchi-tk (GitHub PR 旧#184 再レビュー, 85b58010..d6329e31) | d6329e316d57efc4a44ead629516f4ddddfd3c07 | 0 | 0 | 0 | 2026-09-28T09:28+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `test_x64_fable_remnant_cleanup_contract.py:84` のコメントが、この差分で消した「版は `dialectic_counter` の 2 行だけに書く」を引用したまま残り、直後の版の正規化も何も変えなくなっていた。コメントと正規化を外し、元の比較に戻した（6002a56e） |
| M2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 検査をやめた範囲のうち、repo root（`.claude/agents`・`CLAUDE.md`・`AGENTS.md`）の走査と、Cursor の Counter を小文字の `opus` で書かないことの検査が、PR 本文の限界の節に無かった。限界の節に足した |
| M3 | 独立-2 | advisory | no | self-inflicted | none | accepted | 要約: なし |
| N1 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 未リリースの断片 `changelog.d/20260923-model-names-without-version.md`（Summary・Changed・User Action Required の `Opus 5.5` と「2 行」）と `changelog.d/20260924-model-names-followup.md`（「2 行だけを直す」）が、この PR で消した規定を書いたまま。リリースで統合すると、同じ版の User Action Required に `Opus 5.5` と「一覧の最新の Opus」が並ぶ。3 巡目のため `next-pr`。次の PR で 2 断片から廃止した規定を外す |
| N2 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文が K7 を直さない理由を「表の列の書き方の規定をやめたので」としていたが、§ には規定が残り、限界の節とも食い違っていた。「テストをやめた（規定は残す）」に直し、K7 を次の PR に回した（PR 本文だけの修正） |
| N3 | 独立-3 | low | no | self-inflicted | bookkeeping | next-pr | この PR の断片の Affected Files に `tests/test_x64_fable_remnant_cleanup_contract.py` が無い。Changed の行予算の箇条は利用者から見える変更ではない（`CHANGELOG.md` § Policy）。3 巡目のため `next-pr` |
| P1 | PR後-1 | low | no | self-inflicted | bookkeeping | re-reported | N3 の再掲。この PR の断片の Changed に行予算の箇条（利用者から見えない）があり、Affected Files に `tests/test_x64_fable_remnant_cleanup_contract.py` が無い |
| P2 | PR後-1 | medium | no | self-inflicted | doc-claim | next-pr | N1 と同じ内容を medium で指摘。未リリースの `changelog.d/20260923-model-names-without-version.md`（User Action Required の「`Opus 5.5` を選ぶ」ほか）と `changelog.d/20260924-model-names-followup.md`（「2 行だけを直す」）が、この PR の新しい案内と矛盾する。リリースで 1 つの版にまとめると同じ節に並ぶ。N1 より severity が高いので再掲にせず、PR 後の medium の既定どおり次の PR で 2 断片から廃止した規定を外す |
| P3 | PR後-1 | low | no | inherited | doc-claim | next-pr | `skills/gdd-model-routing/SKILL.md:146` が Cursor の Primary を「GPT 系」と書いたまま（2 行下は Grok 4.6 / Grok 4.5）。旧#176 より前からの記述。次の PR で「Primary（Grok 系）」に直す |
| P4 | PR後-2 | low | no | self-inflicted | bookkeeping | fixed | PR 本文の「次の PR」に P3（`SKILL.md:146` の「Primary（GPT 系）」）が無く、PR 本文だけから次の PR を起こすと落ちる。PR 本文の「次の PR」に 4 番目として足した（PR 本文だけの修正） |
