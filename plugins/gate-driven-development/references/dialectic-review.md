# Dialectic Review Lane

> **所有**: 異なる強みを持つ reviewer の相互評価、統合判断、記録フォーマット
> **参照元**: `gdd-requirements-gating`、`gdd-design-gating`、`gdd-completion-check`、`gdd-pr-review`、`gdd-model-routing`、`subagent-dispatch`

## Purpose

単なる複数 reviewer ではなく、**独立評価 → 相互レビュー → 改訂 → 最終統合**を 1 つの optional lane として扱う。

目的は次の 3 つ:

- 片方の model / reviewer の blind spot をもう片方で補う
- 表現品質、severity calibration、false positive / false negative の揺れを減らす
- 最終成果物には長い議論ではなく、採用判断だけを短く残す
- HITL 前に「この要件・完了条件・作り方だと人間が誤承認しそうか」を敵対的に確認する

## Trigger

以下のいずれかに該当する場合は `dialectic review` を **selected** にする。

- prompt / skill / agent / review policy / reviewer checklist の変更
- Slack / GitHub / wiki / PR review など、人間が読む出力フォーマットの変更
- severity policy、false positive / false negative 改善、reviewer calibration
- security / privacy / operational boundary、masking / redaction / prompt-output contract の変更
- human check または reviewer が「見やすさ」「判断しやすさ」「表現」「採否の揺れ」を論点にした
- 同一論点で reviewer 判断が 2 回以上ぶれた、または前回レビューで valid finding の採否が揺れた
- HITL 前の要件で、completion condition / technology stack / access method / credential boundary / implementation sequence / self-run limit のどれかが `needs-human`、`unresolved`、`external-evidence-required`、または後戻り高リスクとして扱われている
- ユーザーが「独立レビュー」「敵対的レビュー」「反対意見」「思ったんと違うを防ぐ」などを明示した
- planning-reviewer が `Scope Narrowing without Evidence`、`Scope Narrowing via Unverified Risk`、または `DRY Violation: Dual Source of Truth` を **Medium 以上**で報告した（Conservative Design Challenge）
  - gdd-requirements-gating（design の観点を含む）か gdd-design-gating で planning-reviewer の出力を受け取った直後に dialectic review を起動する
  - チャレンジ観点: ① 縮小スコープは全 AC を満たすか ② リスク主張をコードで確認したか ③ 全量対応コストを定量比較したか ④ 将来の全量化コストを試算したか

以下は Trigger 非該当として `not_applicable` にする。

- typo / 文言 1 行修正
- 既に AC と実装方針が明確な小さい bug fix
- テスト追加だけで外部出力・review policy・security / ops boundary に触れない変更
- quick (express) の明白な修正

## Selection Values

記録値は次で統一する。

| 値                            | 意味                                                                                                                                                              |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `selected`                    | Trigger に該当し、GDD 内で dialectic review を実行する                                                                                                            |
| `selected(existing_evidence)` | Trigger に該当するが、同じ論点の独立評価・cross-review・final synthesis が既に会話 / worklog / design に trace 可能に残っており、それを evidence として再利用する |
| `not_applicable`              | Trigger に該当しない。typo、明白な quick express、外部出力や review policy に触れない変更など                                                                     |

`skipped` は selection value として使わない。実行しない理由を残したい場合も `not_applicable` と reason を書く。

既存 evidence を再利用できる条件:

- 自分の初回評価、相手の独立評価、cross-review または統合判断が trace できる
- 採用 / 不採用の理由が残っている
- 現在の requirements / design / diff と論点が同じ

上記のどれかが欠ける場合は `selected` として GDD 内で実行し直す。

## Role Protocol

model 名ではなく役割を固定する。host ごとの model 割当は `gdd-model-routing` が行う。

| 役割                   | 責務                                                                          |
| ---------------------- | ----------------------------------------------------------------------------- |
| Primary evaluator      | 初回案を作る。実装可能性、具体案、既存制約への適合を重視                      |
| Counter evaluator      | 独立に別案 / 批評を作る。曖昧さ、過剰/不足、表現、severity calibration を重視 |
| Final synthesizer      | consensus / adopted / rejected / final decision に圧縮して最終案を決める      |

## Execution Pattern

1. Primary evaluator が初回案 A を作る
2. Counter evaluator が独立案 B を作る
3. Primary evaluator が B を cross-review する
4. Counter evaluator が A を cross-review する
5. Primary evaluator が cross-review を受けて改訂案 A' を作る
6. Final synthesizer が A / B / cross-review / A' を統合し、最終案を作る

Step 3〜5 の cross-review と改訂（Revising evaluator）は Primary・Counter が兼ね、相手の案の採用できる点・反論・blind spot を整理する。並列実行できる場合、Step 1 と Step 2 は並列にしてよい。Step 3 / 4 は A と B が揃ってから行う。

## Short Form

completion-check や PR review で `Dialectic Review Summary` 欠落を補完する場合だけ、short form を使ってよい。

short form は手順を省略することではなく、**中間出力を短くする**ことを意味する。最低限、次を満たす。

1. Primary evaluator の独立評価 A を作る
2. Counter evaluator の独立評価 B を作る（A を見せない）
3. A と B を同じ context に置き、差分・採用・棄却を cross-review note として整理する
4. Final synthesizer が `Dialectic Review Summary` だけを出す

Revising evaluator の明示的な A' は、cross-review note と final synthesis で採用 / 棄却が trace できる場合だけ省略してよい。

HITL 前に敵対的レビューを使う場合は Short Form を既定にする。目的は全文レビューではなく、次だけを短く固定すること:

- `反対仮説`: この要件 / 作り方が間違っているとしたら何が原因か
- `ズレリスク`: 人間が「思ったんと違う」と言いそうな completion condition / tech stack / sequence / self-run boundary
- `採用した修正`: HITL 前に requirements / design skeleton / human-check に反映した修正
- `棄却した指摘`: 採用しない指摘と理由
- `残すリスク`: human check で明示確認する残リスク

## Context Discipline

良い dialectic は「最初から相手の意見を混ぜる」ことではなく、**独立した自分の評価を一度固定してから、相手の評価を読み込んで見直す**ことで生まれる。

- Step 1 / 2（独立評価）では、相手 model の評価結果を渡さない
- Step 3 / 4（cross-review）では、必ず次の 2 つを同じ context に入れる:
  - 自分が先に出した初回評価
  - 相手 model / reviewer が出した評価
- cross-review の役割は「相手に同意すること」ではなく、自分の初回評価のどこが補強・修正・棄却されるかを明示すること
- Step 5（revision）では、初回評価を捨てずに、何を採用し何を退けたかを trace できる形で改訂する
- Step 6（final synthesis）では、初回評価・相手評価・相互レビュー・改訂案をすべて入力にする

この順序を崩すと、最初から平均化された案になり blind spot が見えにくくなる（2 つの案を並べただけで統合しない、cross-review を読まずに最初の案を採用しない、Trigger に当たらないときに full dialectic を走らせない）。一方で cross-review 時に自分の初回評価が context に残っていないと、「何が変わったか」を検証できず、単なる別レビューの要約になる。

## Host Adapter

Primary evaluator は host の現在の実行 model（Claude Code は `sonnet` でもよい）、Counter evaluator は `references/fixed-models.md` の `dialectic_counter` tier（Codex は Anthropic を使えないので GPT 系の別 role。`references/codex.md`）、Final synthesizer は Claude Code では `opus` + `effort=high`、Cursor・Codex では Primary 系にする（host ごとの表は `skills/gdd-model-routing/SKILL.md` § Dialectic Review のモデル割当）。

model が 1 系統しか使えない環境では、同一 model で role prompt を分けて実行してよい。ただし `independent` と `cross-review` を同じ出力に混ぜない。

## Output Contract

dialectic の詳細ログを最終 artifact に貼り付けない。`design.md` / `worklog.md` / PR review には次の summary だけを残す。

記録先の優先順位:

- requirements-gating で HITL 前に確定したもの: `requirements.md`
- design-gating で設計判断として確定したもの: `design.md`
- completion-check / PR review で summary 欠落を補完したもの: `worklog.md`
- PR review の一時判断: review 本文の `Review metadata`

見出しは `## Dialectic Review Summary` の下に `### Consensus`・`### Adopted From Primary`・`### Adopted From Counter`・`### Rejected`・`### Final Decision`・`### Open Risks` の 6 つで、各見出しの下は箇条書きにする。

`Rejected` には「なぜ採用しないか」を 1 行で書き、Final synthesizer は採用・不採用の理由を残さずにまとめない。長い議論、相手 model の採点、モデル優劣の感想は残さない。

## Gate Semantics

- dialectic review は **補助 lane**。単独で `Human Check Status` や `Next Action` を更新しない
- dialectic の結果、AC 追加/削除・scope・policy・ownership・security boundary・prompt-output contract が変わる場合は、既存の `human_recheck_required` / `planning_rework_required` ルールに従う
- 既承認範囲内の表現改善、severity 調整、出力フォーマットの具体化で閉じる場合は `design_detail_only` または同 gate 内の修正でよい
- completion-check / pr-review で発見した dialectic 結果は、blocking finding ではなく最終判断の evidence として扱う。ただし valid High / Medium finding を発見した場合は通常の gate ルールに従う
