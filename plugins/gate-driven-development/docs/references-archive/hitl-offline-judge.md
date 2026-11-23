# HITL Offline Readability Judge

> **所有**: `references/human-check-template.md`
> **目的**: human-check を出す前に「読めるが判断できない」状態を検出し、表示前に直す。

## 契約

HITL は、人間に出す前に deterministic lint と offline LLM Judge 相当の読みやすさ確認を通す。Judge は production allow / deny の主判定ではなく、表示文を直すための二次評価である。

## 判定観点

Judge は次を 30 秒以内に判断できるかを見る。

1. この OK で AI が何を作るか
2. この OK で何を承認しないか
3. 人間が今返すべきこと
4. AI がどこまで自走するか
5. AI が止まって人間に戻る条件

## 判定値

- `pass`: そのまま表示してよい
- `needs_rewrite`: 読めるが、承認判断に必要な情報が欠けている
- `blocked`: 要件・完了条件・自走範囲が曖昧で、文章修正だけでは安全に HITL できない
- `not_run`: judge 実行環境がない。deterministic lint は通す

## 表示前修正ループ

1. HITL draft を作る
2. `lint-hitl-decision-quality.py` / `lint-human-check-language.py` / `lint-hitl-complexity.py` を通す
3. offline LLM Judge が使える場合は判定する
4. `needs_rewrite` の場合は、人間に出す前に HITL を書き直す
5. 書き直した HITL を lint / judge に再投入する
6. `pass` か `repaired_then_pass` になったものだけを `human-check-waiting` として表示する
7. `blocked` の場合は `<gdd-stop reason="clarification-needed">` で止め、HITL ではなく 1-3 個の確認質問にする

## 最終 HITL に出す短い表示

最終 HITL には、judge の長い採点理由を出さない。人間には次だけを短く出す。

```markdown
### HITL読みやすさ確認（LLM Judge / offline）

| 項目 | 内容 |
|---|---|
| 判定 | <pass / repaired_then_pass / not_run: reason> |
| 直した点 | <judge で読みにくいと判定され、表示前に直した点。なければ `なし`> |
| まだ残る注意 | <人間が見るべき注意。なければ `なし`> |
```

この欄は新しい承認ポイントではない。人間が「この表示は判断しやすい形に直されたか」を確認するためのメタ情報である。
