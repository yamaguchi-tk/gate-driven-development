---
lane: L1
pr: 447
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e17a1bc3 | 0 | 4 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | f5af4073 | 0 | 2 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b0f7a127 | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | test-power | accepted | manifest は承認の外にあり、置換の値・後の edits で block の中身を書き換えても SAME になる。閉じ方: 列挙（常時 High の適用範囲外で開いた入力のため、reference の限界に書いて受け入れた） |
| I1-2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | manifest が参照しない block は照合されず一覧も出ない commit: 5f5a32be |
| I1-3 | 独立-1 | medium | no | self-inflicted | test-power | fixed | sections を新しいファイルに限る規定がコードで強制されていない commit: 5f5a32be |
| I1-4 | 独立-1 | medium | no | self-inflicted | product | fixed | フェンスの解析の規則が tasklist_parse と違う（字下げ・info の `） commit: 5f5a32be |
| I1-5 | 独立-1 | low | no | self-inflicted | product | fixed | 想定外の例外が exit 1（不一致）で返る commit: 5f5a32be |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | reference のコマンドが利用先の repo から届かない commit: 5f5a32be |
| I1-7 | 独立-1 | low | no | self-inflicted | product | fixed | 1 回だけあたるの数え方が重なる出現を数えない commit: 5f5a32be |
| I1-8 | 独立-1 | low | no | self-inflicted | product | fixed | 文字どおりの {{…}} を書けない commit: 5f5a32be |
| I1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | worklog.md の記録の行の形が決まっていない commit: 5f5a32be |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | digest の突き合わせが本文を担うと言い過ぎで限界に書き漏れ commit: 5f5a32be |
| I1-11 | 独立-1 | low | no | self-inflicted | test-power | fixed | 実物が無いときのテストが exit 2 や例外でも通る commit: 5f5a32be |
| I1-12 | 独立-1 | low | no | self-inflicted | test-power | fixed | --base のテストが既定の base と同じ値を渡している commit: 5f5a32be |
| I1-13 | 独立-1 | low | no | self-inflicted | test-power | fixed | 知らない key と型の違いが単独で確かめられていない commit: 5f5a32be |
| I1-14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の行予算の説明が数と合わない commit: 5f5a32be |
| I1-15 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片と docstring のファイル全体を比べるが sections では成り立たない commit: 5f5a32be |
| I1-16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | reference の例の確定文面外の edit に reason が無く、コードも reason を任意にしている |
| I1-17 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | extract の使い方と --actual の意味が reference に無い commit: 5f5a32be |
| I1-18 | 独立-1 | advisory | no | self-inflicted | product | accepted | block の見出しが直後の括弧を受け付けない |
| I1-19 | 独立-1 | advisory | no | self-inflicted | product | accepted | manifest の digest の形（64 桁の hex）を確かめていない |
| I1-20 | 独立-1 | advisory | no | self-inflicted | product | fixed | 承認の範囲（end:）を承認する人に見せる手順が無い commit: 5f5a32be |
| I1-21 | 独立-1 | advisory | no | self-inflicted | style | fixed | テストが verify を 2 回走らせている commit: 5f5a32be |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | fixed | 依頼の背景の digest（「## advisory の扱い」の前まで）が節の中の `##` のため再現できない。節の終わりを --until・section_end で宣言できるようにした commit: 1e731a5c |
| I2-2 | 独立-2 | medium | no | self-inflicted | test-power | fixed | 参照されない block の検出が `### D-n` の見出しの揺れで外れる（I1-2 の残り） commit: 1e731a5c |
| I2-3 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | info に ` を含む行のテストが、規則を消しても通る |
| I2-4 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 字下げのテストの digest の assert がどの規則でも通る |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 想定外の例外を exit 2 にする catch-all を固定するテストが無い |
| I2-6 | 独立-2 | low | no | self-inflicted | product | next-pr | tasklist_parse を import できないとき exit 1 になる |
| I2-7 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 新しいファイルの判定が path の書き方（大文字小文字・..）で外れる |
| I2-8 | 独立-2 | low | no | self-inflicted | product | next-pr | noverify の block を参照すると両方の一覧に出る |
| I2-9 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | フェンスの開閉の判定が tasklist_parse の写しで、一致を固定するテストが無い |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | reference の参照の数え方と old の括弧書きが実装と合わない |
| I2-11 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文に外から見える挙動の一部が無い commit: なし（PR 本文） |
| I2-12 | 独立-2 | low | no | self-inflicted | product | next-pr | 承認のときにどの block が noverify かを人が見る手順が無い |
| I2-13 | 独立-2 | advisory | no | self-inflicted | style | accepted | テストのファイルを戻す処理が finally に無い |
| I2-14 | 独立-2 | advisory | no | self-inflicted | style | accepted | 照合した block の並びが文字列順 |
| I3-1 | 独立-3 | medium | no | inherited | product | next-pr | 宣言なしで節の中に `##` があると、後ろの `### D-n` が黙って範囲外になる |
| I3-2 | 独立-3 | low | no | self-inflicted | product | next-pr | 空文字の --until・section_end が宣言なしとして扱われる |
| I3-3 | 独立-3 | low | no | self-inflicted | test-power | next-pr | until のテストの最後の assert が終了コードを見ていない |
| I3-4 | 独立-3 | low | no | self-inflicted | test-power | next-pr | D-n の下にない noverify のフェンスを止めないことを確かめるテストが無い |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | usage・reference の手順・manifest の key 一覧が --until・section_end に追いついていない |
| I3-6 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の scripts の行が --until・section_end・digest の止まり方を書いていない |
| I3-7 | 独立-3 | advisory | no | self-inflicted | style | accepted | 新しいエラーの行番号が design.md の行でなく節の中の行 |
| I3-8 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | --until は見出しでない行の先頭にも当たる |
