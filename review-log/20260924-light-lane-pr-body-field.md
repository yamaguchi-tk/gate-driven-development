---
lane: L1
pr: 旧#180
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 6db44ab49832e011b3f397ac82807577b9f3d064 | 0 | 0 | 0 | 2026-09-24T17:02+09:00 |
| PR後-1 | yamaguchi-tk (GitHub PR 旧#180 review) | 096c2d70ae170f36b57d72faf752258fa4350737 | 0 | 0 | 0 | 2026-09-24T19:39+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | pr-body-field-scope-drift | next-pr | `CLAUDE.md:53` は欄を「目的・変更内容・限界の節」と定めながら、同じ行の後半「欄には差分が変える挙動と限界を書き」から目的が落ちている。agent 定義も :18 は欄の用途を「挙動と限界の照合」に限り、:28 は「目的・変更内容・限界」を照合先にしていて食い違う。PR 本文の限界にある「理由は変更内容として書いてよい」は差分のどこにも無い |
| F2 | 独立-1 | low | no | self-inflicted | pr-body-field-set-narrower | next-pr | 欄の中で報告させる集合（agent 定義 :18・`CLAUDE.md:53`・テストの `PR_BODY_EXCLUDES`）に、欄の外の集合（:17・`CLAUDE.md:49`）にある誘導（「対応済み」「通るはず」）と抑制（指摘を控えるよう求める文）が入っていない。限界の節に「指摘不要」と書いても報告されない |
| F3 | 独立-1 | low | no | self-inflicted | advisory-without-follow-up | next-pr | :18 の advisory を受けた後の扱いが無い。main は `CLAUDE.md:69` のとおり PR 本文に列挙するだけで、経緯を読んだ巡が有効のまま最終の全差分巡になりうる。欄の外の文（:17）も同じ扱いで、そちらは差分の前から |
| F4 | 独立-1 | low | no | self-inflicted | contract-override-header-stale | next-pr | 手順 6 の冒頭（`CLAUDE.md:48`）は、軽いレーンが置き換える契約を 3 と 4 しか挙げていない。契約 1 を緩める規定は、5 行下の箇条の途中にしか無い |
| F5 | 独立-1 | low | no | self-inflicted | test-power | next-pr | `PrBodyFieldTests` は行に「契約 1」があることしか見ず、「この欄の分だけ緩める」を「緩めない」に変えても通る。reviewer の規定の「判断に使わない」も固定していない。テスト名の `only` と断片の説明が assert の範囲より広い |
| A1 | 独立-1 | advisory | no | inherited | stale-loaded-agent-definition | accepted | reviewer が起動時に読み込んだ定義は、材料をファイルで渡す方式より前の版だった。reviewer は現行の定義ファイル（:14-16）に従い、3 ファイルを全行読んでからレビューしたと申告した。出力には `差分との関係` があるので、手順 6 の起動し直しの条件には当たらない。この巡は、:18 を含む定義で走った証拠にはならない |
| A2 | 独立-1 | advisory | no | self-inflicted | template-tip-unfilled | accepted | 呼び出し側（main）が `tip:` 欄を埋め忘れた（プレースホルダのまま渡した）。差分ファイルは `6db44ab4` で作ったもので、reviewer も差分の + 行が worktree の該当行と一致することを確かめている。巡の sha には `6db44ab4` を書いた |
| A3 | 独立-1 | advisory | no | self-inflicted | skill-red-green-evidence | fixed | reviewer policy と prompt の欄を変えるので、手順 3 の 1c `Skill RED-GREEN Evidence` が要る。現行の定義の本文で pressure scenario を 1 本走らせ（手順 6 の `general-purpose`・`model: opus` の経路）、3 欄を PR 本文に書いた |
| G1 | PR後-1 | medium | no | self-inflicted | test-power | next-pr | `PrBodyFieldTests` が禁止の向きを固定していない。`書かない` を `書いてよい` に変えても、`PR_BODY_EXCLUDES`・「契約 1」・advisory のトークンが残るので 3 本とも通る。独立-1 の F5 と同型。書く側 2 か所に `書かない`、読む側に `判断に使わない` を assert すれば閉じる。レビュアーの判断で次の PR |
| G2 | PR後-1 | low | no | self-inflicted | pr-body-name-overloaded | next-pr | 手順 6 の reviewer に渡す「PR 本文」は巡の ID を書かないが、手順 7（`CLAUDE.md:96`）は GitHub の PR 本文に巡の sha を書かせる。同じ名前なので、GitHub 側の全文を渡すと新しい規定の advisory が発火し、逆に「書かない」を GitHub 側へ当てると終了条件の巡の sha が落ちる。reviewer に渡すものを別の名前にし、「目的・変更内容・限界だけを抜き、手順 7 の巡の記録は除く」と書く。レビュアーの判断で次の PR |
| G3 | PR後-1 | advisory | no | self-inflicted | report-token-location | next-pr | 欄の中の経緯にも、欄の外の文と同じトークン `テンプレート外の記述あり` を使うので、main が prompt の欄の外を疑い、渡した PR 本文のファイルを見ないことがある。トークンは変えず、報告文に「PR 本文ファイル内」と場所を足す |
