---
type: patch
---

#### Summary

- 人に判断を求める文面の書き方を `references/human-check-template.md` § 判断の書き方 にまとめた。判断ポイントに置くのは、人が自分の持つ情報で決められ、選び方で後戻りが変わるものだけにする（ライブラリの設定値やレビュー指摘の閉じ方などの内部の処置は、AI が決めて 1 行で知らせる）。判断ごとに「いまの状態 → 分かったこと → 何が起こりうるか → 選択肢ごとに残るもの → おすすめ」の順で書き、内部 ID は初出で意味を書き、ラベルだけの項目を置かない。長さの上限では決めず、判断に効かない段落（変更予定ファイルの全列挙、レビューの経緯など）を一次表示から外す
- 簡易版 human check テンプレートで、冒頭に決めてほしいことを書く行を足し、`### 判断ポイント` を WHY・整理した要件の直後に移した。`変更予定ファイル（WHERE）` は判断に効くファイルだけを挙げる
- 停止本文などの「人間にお願いしたいこと」（`references/output-format.md` § Human-Facing Conversation Contract）も、同じ書き方に従う

#### Affected Files

- `references/human-check-template.md`（§ 一次表示の原則 4・7、§ content 品質ルール）
- `references/human-check-template-compact.md`
- `references/output-format.md`（§ Human-Facing Conversation Contract）

#### User Action Required

なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
