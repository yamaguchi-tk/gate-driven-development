---
type: patch
---

#### Summary

- 確定文面の道具（`scripts/confirmed-text.py`）の続き。承認や照合の範囲から黙って外れる形と、判定できないのに不一致（exit 1）として返る形を止めた

#### Changed

- `scripts/confirmed-text.py`:
  - `digest`・`extract` の `--until` と manifest の `section_end` で、節の終わりの見出しを宣言できる。空の宣言は止める（exit 2）
  - 宣言なしで終えた節の後ろに `### D-n` があれば止める（節の中に `##` を置いて、後ろの D-n が範囲から外れる形）
  - `digest` が、照合する block と照合しない block（`noverify`）の一覧を出す。`noverify` の block を manifest から参照すると止める
  - manifest の `path` は repo からの相対の正規形だけを受ける。base のファイルと大文字小文字だけが違う綴りと、大文字小文字だけが違う重複を止める
  - `tasklist_parse` を読めない・壊れているときは exit 2 にする
  - block の一覧を番号の順に並べる
- `references/confirmed-text.md`: 上の挙動と、human check で `end:` と block の一覧を見せること、再確認では承認のときと同じ `--until` で digest を取ることを書いた

#### Affected Files

- `scripts/confirmed-text.py`, `references/confirmed-text.md`, `tests/test_confirmed_text.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_confirmed_text.py` に、節の後ろの D-n・空の宣言・path の書き方・大文字小文字・noverify の参照・フェンスの判定の一致・import の失敗・catch-all のテストを足した。フェンスの内外の判定は `tasklist_parse` の `_scan_fences` との一致を、`### D-n` の見出しの下にない照合するフェンスを止めることは変わらないことを、テストで確かめる
- `bash tests/validate-plugin.sh`
