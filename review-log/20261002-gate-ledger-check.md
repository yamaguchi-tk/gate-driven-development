---
lane: L1+
pr: 285
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（main の案は、hook の inline 判定を結果コードを返すラッパー関数に切り出すものだった。Opus は、ラッパーを作らず純粋な述語を中身を変えずに lib へ移すこと、`Reviewed by` を hook に入れないこと、deny 文言だけでは事故は閉じないので書き込み時の検査は次の PR にすることを推した。main の案と食い違ったので、信号 ① で Fable を呼んだ。Fable は、sha と high・blocking の比較もスクリプト側で書き直さず lib の述語にすること、解決が multiple のときは `--steering` があっても解決の行を invalid のまま残すことを足した。main は Opus 案に Fable の 2 点を足して採った。実測: Next Action=done・standard で完了タスクを持つ steering 55 本のうち 38 本に `Reviewed by` の欠落があり、hook で止めると誤 block になる。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-02T15:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 69b8f04ce3f27698a28f6603f47d4b509ae1a04c | 0 | 2 | 0 | 2026-10-02T17:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 7d6f8b719973dc7132b82e7868c71dc701ce2c3f | 0 | 0 | 0 | 2026-10-02T18:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| A1 | 独立-1 | medium | no | self-inflicted | product | fixed | deny 文言の「移さない行」の列挙が、Human Check Status・merge gate の field・Stacked Base などの現在値を落とし、一般則「現在値は残す」を失った commit: 7d6f8b71 |
| A2 | 独立-1 | medium | no | self-inflicted | product | fixed | deny 文言の「移した後に missing / invalid を全部直す」は作業の途中では満たせず、証跡を先に書く方向へ誘導する commit: 7d6f8b71 |
| A3 | 独立-1 | low | no | self-inflicted | product | fixed | --base を gdd_resolve_base_ref に通さず、hook と diff の範囲が変わり、値が git の option として読まれうる commit: 7d6f8b71 |
| A4 | 独立-1 | low | no | self-inflicted | product | fixed | completed_tasks_missing_reviewed_by の見出しが完全一致・インデント行をタスク行に読み、done guard と受理集合が違う。0 件を ok と出す commit: 7d6f8b71 |
| A5 | 独立-1 | low | no | self-inflicted | product | fixed | --steering を論理パスで正規化し、相対パスを repo root から解く commit: 7d6f8b71 |
| A6 | 独立-1 | low | no | self-inflicted | product | fixed | --tip ≠ HEAD のとき、Independent Review の行の gate 列が失敗した gate を示さない commit: 7d6f8b71 |
| A7 | 独立-1 | low | no | self-inflicted | product | fixed | Independent Review の書式不正の詳細が正本の key 一覧（GDD_IR_RECOVERY_CORE）とずれ、理由を出さない commit: 7d6f8b71 |
| A8 | 独立-1 | low | no | self-inflicted | product | fixed | 検算の行と SKILL の「直してから」に復旧の道筋が無く、sha だけの書き換えや Reviewed by の書き足しへ誘導しうる commit: 7d6f8b71 |
| A9 | 独立-1 | low | no | self-inflicted | product | fixed | 「hook と同じ判定」の説明が実際より広く、実行するコマンドの gate に関係ない行まで直させる commit: 7d6f8b71 |
| A10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | self-review-lanes.md の段落が followup の節の、別の話題の段落の先頭にある |
| A11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | post-completion-pr-flow.md・gdd-pr-review §2b に検算の手順が無い |
| A12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | テストの検出力（deny 文言の部分一致、4 列でない行を捨てる、--base・--root・読めない steering などの変異が無い） |
| A13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | --help が exit 2・stderr、値のタブ、deny 文言のパスを引用しない |
| A14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | gdd_adr_not_applicable_allowed に Task Size の正規化の写しが残る |
| A15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | steering_size.py のコメントが、hook が Reviewed by を検査すると書く |
| A16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の成功の断定、n/a の定義、述語の列挙の漏れ |
| A17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | active 行がセッションの一致を考慮しない |
| A18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | python3 - が cwd を stdlib より先に探す |
| A19 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 読めない steering があると --steering を無視する |
| B1 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | 完了タスクが 0 件のとき reviewed-by が n/a で失敗せず、完了タスクを丸ごと移した・要約で見出しが崩れたときに「ok から崩れた行を戻す」が発火しない |
| B2 | 独立-2 | medium | no | self-inflicted | product | next-pr | reviewed-by の ok を 1 行にまとめるので、既に 1 タスク欠けている steering で別のタスクの Reviewed by を落としても「ok だった行」が無く発火しない |
| B3 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | --base のテストが、解決の変更を元に戻しても落ちない |
| B4 | 独立-2 | low | no | inherited | doc-claim | next-pr | _oversize_warning と WHY 行が「圧縮」を案内し、deny 文言の「要約しない」と食い違う |
| B5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | state-field-tiers.md の 13 行目（履歴の field を移す）と 18 行目（現在の行は全部残す）が逆に読める |
| B6 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 書式不正のテストが detail の理由を assert しない |
| B7 | 独立-2 | low | no | self-inflicted | test-power | next-pr | pwd -P の変更を固定するのが macOS だけ |
| B8 | 独立-2 | low | no | self-inflicted | product | next-pr | python3 -I に -X utf8 が無く、script がロケールをそろえない |
| B9 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | gh pr create の前に解消する行の範囲が self-review-lanes.md と completion-check で違う |
| B10 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | deny 文言の括弧書きが、拒否された正当な証跡の書き込みのやり直しまで禁じて読める |
| B11 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | steering 行の gate 列が常に pre-PR,pre-push で、push の前にも steering の整理を求めて読める |
| B12 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋に、--steering・--base の解き方、0 件の n/a、gate 列の分け方などが書かれていない |
| B13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 使い方のコメントが --steering と --base の解き方を書いていない |
| B14 | 独立-2 | advisory | no | self-inflicted | product | accepted | 作業中の steering が複数あると移す前後の検算が空振りし、deny 文言が --steering を案内しない |
| B15 | 独立-2 | advisory | no | inherited | product | out-of-diff | hook と lib の python -c が cwd のモジュールを読む |
| B16 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「述語をここに書き足さない」のコメントと、dry・Next Action の比較が script に inline にあること |
