---
lane: L1+
pr: 592
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 624abb56 | 0 | 0 | 0 | 2026-10-27 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 30b030be | 2 | 3 | 2 | 2026-10-27 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 30b030be | 0 | 0 | 0 | 2026-10-27 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c7eeac17 | 1 | 2 | 1 | 2026-10-27 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | c7eeac17 | 0 | 0 | 0 | 2026-10-27 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | ec1b34ad | 0 | 1 | 0 | 2026-10-27 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | low | no | self-inflicted | 閉じ方 | fixed | 2 本とも案 A（処置の欄）を推した。割れたのは欄の有無を誰が見るかで、Opus は lint-plan-consistency.py の ERROR、Fable は gate runner の散文。散文の規定は守られにくい（memory）ので Opus の側を採った。commit: f0a5cbe0 |
| M-2 | 方針メモ | advisory | no | inherited | 読む系 | accepted | Opus: 似た既存部品 scripts/lint-existing-code-reading.py が gate の手順から呼ばれていない。Round 1 の根拠の誤り（G 30 件）に当てる前に、配線するか撤去するかを別に決める |
| F1-1 | 独立-1 | high | yes | self-inflicted | 処置の読み取り | fixed | 列挙: 設計: 変える（再入かどうかを判定の行から推す決定をやめ、gate が --entry で宣言する。宣言が無ければ exit 2）。(a) 許可リスト: 先頭が 処置 の行は `- 処置:` の形だけ。実データ 69 本で別の見出しが 21/309（事故で出る形）。決まった形でない処置の見出し（`- **処置**:`・`### 処置`・字下げなど）と、処置の無い再入・判定の読めない Round を WARN か OK で通す。commit: 280848fb |
| F1-2 | 独立-1 | high | yes | self-inflicted | 処置の読み取り | fixed | 列挙: 設計: 変える（続きの行の概念をなくし、1 件 1 行に閉じる。Fable の案）。(a) 許可リスト: 処置の塊の行はすべて同じ字下げの項目の形。実データで項目の位置の別の形 3/777、深い行 1/181 塊。項目の形でない行（`・B2:`・`+ B2:`・記号なし）を前の項目の続きに足し、前の項目の欄で通す。commit: 280848fb |
| F1-3 | 独立-1 | medium | no | self-inflicted | 依頼のずれ | accepted | 依頼の見出しは Round 1 の差し戻しだが、Round 2 の主因に当てた。依頼が 2 通りに読める（見出しと「損失の主因に当たる直し方」）ので、ユーザーに確かめる。推奨は今の案 |
| F1-4 | 独立-1 | medium | no | self-inflicted | 依頼のずれ | fixed | 依頼の範囲（requirements gate）を design gate の再入まで広げた。design の再入を対象から外した。commit: 280848fb |
| F1-5 | 独立-1 | medium | no | self-inflicted | 依頼のずれ | fixed | design の再入で処置を書く手順から、根拠・伝播の書き方に辿り着けない。design を外したので届ける先が無くなった。commit: 280848fb |
| F1-6 | 独立-1 | low | no | self-inflicted | 処置の読み取り | fixed | 再入でない起動でも前の gate の最後の Round を検査し、誤って止めるか誤った WARN を出す。--entry other では処置を見ない。commit: 280848fb |
| F1-7 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | 前の形の処置に欄を足す手順が、追記専用の規定と食い違う |
| F1-8 | 独立-1 | low | no | self-inflicted | 処置の読み取り | accepted | blocking ごとに処置があるかは見ない |
| F1-9 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | 限界の「再入の reviewer が根拠を確かめる」は、上限到達の損失を減らさない |
| F1-10 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | 未測を Honest Limitations に出す規定と、位置引数でも reviews.md を読むことが PR 本文・docstring に無い |
| F1-11 | 独立-1 | advisory | no | self-inflicted | テスト | accepted | smoke test の requirements.md が共有の一時ディレクトリにあり、そこの reviews.md を読む |
| F1-12 | 独立-1 | advisory | no | self-inflicted | 秘匿 | accepted | 根拠の書き方に、相対パスと秘匿値を書かないことが無い |
| F1-13 | 独立-1 | advisory | no | self-inflicted | 再入の範囲 | accepted | 再入の reviewer に根拠の照合を足したのに、同じ段落が求める A/B が無い |
| F1-14 | 独立-1 | advisory | no | self-inflicted | 断片 | accepted | 断片の type が minor だが、進行中のタスクを止める |
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | 処置の読み取り | accepted | Opus: 宣言を必須にする（付け忘れは exit 2）。Fable: 1 件 1 行に閉じる（深い行も ERROR）。どちらも閉じる側なので両方採った。2 巡目でこの parser に 閉じ方: 列挙 の high がまた出たら、修正を打ち切って限界にする（Opus） |
| F2-1 | 独立-2 | high | yes | self-inflicted | 処置の読み取り | fixed | 列挙: 設計: 変える（処置の塊の終わりを字下げで推す決定をやめ、処置を Round の最後の塊にする）。(a) 許可リスト: 最初の `- 処置:` からファイルの終わりまで（fence の中も）、空でない行は見出しか同じ字下げの項目だけ。再入直前の Round で後ろに行があったのは 10/87（備考・再入判定・人の回答など。処置の前か worklog.md に移す）。処置の塊の後ろに字下げなしで書いた処置の行（`- B2: 直した`）を検査せず、欄が無くても OK。commit: ec1b34ad |
| F2-2 | 独立-2 | medium | no | self-inflicted | 依頼のずれ | re-reported | F1-3 と同じ（Round 1 を Round 2 に読み替えた） |
| F2-3 | 独立-2 | medium | no | self-inflicted | 宣言 | accepted | `--entry other` を誤って宣言した再入は、偽の 機械検査: OK が 1 枚に載る。entry を出力に出す案 |
| F2-4 | 独立-2 | medium | no | self-inflicted | テスト | accepted | test_header_variants_are_error は有効な見出しの無い入力だけで、別の見出しを止める分岐を固定していない |
| F2-5 | 独立-2 | low | no | self-inflicted | テスト | accepted | 項目の形のテストが欄の無い行だけで、形の検査を固定していない |
| F2-6 | 独立-2 | low | no | self-inflicted | 文書の主張 | accepted | 追記専用の例外が欄を足すことだけで、見出し・項目の形を直す書き換えと食い違う |
| F2-7 | 独立-2 | low | no | self-inflicted | 文書の主張 | accepted | reviews.md を読めず --entry も無いときの exit 2 が docstring に無い |
| F2-8 | 独立-2 | advisory | no | self-inflicted | 文書の主張 | accepted | `1) ` を項目として受けるが、文書は `- `・`* `・`1. ` だけ |
| F2-9 | 独立-2 | advisory | no | self-inflicted | 処置の読み取り | accepted | has_round は fence の中の Round も数える（止める側） |
| F2-10 | 独立-2 | low | no | self-inflicted | テスト | accepted | smoke test の requirements.md が共有の一時ディレクトリにあり、そこに Round のある reviews.md があると exit 2 |
| F2-11 | 独立-2 | low | no | inherited | 文書の主張 | out-of-diff | subagent-dispatch.md の lint の起動が相対パス（前から） |
| F2-12 | 独立-2 | advisory | no | self-inflicted | 文書の主張 | accepted | 契約 3 は伝播を requirements・design とも変えた節に含め、agent 定義は requirements に絞った |
| F2-13 | 独立-2 | advisory | no | self-inflicted | 文書の主張 | accepted | 処置が生んだ 21 件のうち残る 3 件の内訳と、依頼の数字との対応が PR 本文に無い |
| F2-14 | 独立-2 | advisory | no | self-inflicted | 文書の主張 | accepted | マージ後に効果を測る指標・費用の見込みが PR 本文に無い |
| M2-1 | 方針メモ-2 | advisory | no | self-inflicted | 処置の読み取り | accepted | 安全策 4 が発火（処置の読み取りの high が独立-1・独立-2 の 2 巡）。Opus と Fable はそろって続行と案 3（処置を Round の最後の塊にする）を推した。Opus は、後ろの `##` と fence も止めることを足した。1 回目の発火なので推奨で進めた。2026-10-27 22:48 にユーザーが「Round2の修正はその方向で良い」と答え、続行に決まった |
| F3-1 | 独立-3 | medium | no | self-inflicted | 依頼のずれ | re-reported | F1-3 と同じ（Round 1 を Round 2 の主因に読み替えた）。依頼が挙げた数（差し戻し率・上限到達・reviewer の時間・費用）ごとの見込みを PR 本文の限界に書いた。commit: なし（PR 本文） |
| F3-2 | 独立-3 | medium | no | self-inflicted | テスト | accepted | test_empty_treatment_is_error の入力の `## メモ` が新しい ERROR に当たり、「処置が空」の分岐を固定しなくなった |
| F3-3 | 独立-3 | low | no | inherited | 文書の主張 | accepted | 見出しより前の閉じた fence の中の `処置` の行は止めないが、文書は fence を除くと書いていない |
| F3-4 | 独立-3 | low | no | self-inflicted | 文書の主張 | accepted | docstring・subagent-dispatch:61・steps:38 の ERROR の列挙に「処置の後ろの行」が無い。断片と PR 本文の「項目でない行」は 2 つ目の見出しを含まない言い方にすべき |
| F3-5 | 独立-3 | low | no | self-inflicted | 文書の主張 | accepted | 処置の後ろの行を移すのを書き換えに数えない例外が、前の形のタスクにしか掛かっていない |
| F3-6 | 独立-3 | low | no | inherited | 処置の読み取り | re-reported | F1-8 と同じ（blocking ごとに処置の項目があるかは見ない） |
| F3-7 | 独立-3 | advisory | no | inherited | 文書の主張 | accepted | `1) ` も項目として通るが、文書は `- `・`* `・`1. ` だけを挙げる |
