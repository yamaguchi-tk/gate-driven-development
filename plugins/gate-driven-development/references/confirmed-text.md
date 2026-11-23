# 確定文面（human check で承認した文を固定して照合する）

> **所有**: 確定文面の書き方・digest・照合・再確認の手順の正本。道具は `scripts/confirmed-text.py`
> **参照元**: `human-check-template.md` § 確定文面の再確認

human check で文書の文そのもの（ADR の決定、規則の文など）を承認するときに使う。承認した文が、マージする文書にそのまま入ったことを機械で確かめる。

## 書き方（design.md）

- 節は `## 確定文面` で始まる見出し 1 つ（後ろに空白か括弧で補足を足してよい）。節は、コードフェンスの外の次の `#`・`##` 見出しの前で終わる（無ければ末尾まで）。節の中の小見出しは `###` 以下にする。節の中に `##` を置くときは、終わりの見出し（その行の先頭の文字列）を `digest`・`extract` の `--until` と manifest の `section_end` で宣言する。宣言すると、フェンスの外でその文字列で始まる最初の行の前で終わる（無い・空なら止める）。宣言なしで終えた節の後ろに `### D-<n>` があれば止める（確定文面でない `### D-<n>` が後ろにあるときも、次の節の見出しを宣言する）
- 承認する文ごとに `### D-<n> <題>` を置き、文をコードフェンスに入れる。block の id は `D-<n>#<i>`（i はその見出しの中のフェンスの順で 1 から）。フェンスの外の文（適用先の説明など）は block に入らない。`### D-<n>` の見出しの下にない照合するフェンスは、digest の時点で止める。中身に ``` を含むときは、外側のフェンスを ```` にする。フェンスの規則（字下げ・info の扱い）は design.md を読むほかの検査と同じ `hooks/scripts/lib/tasklist_parse.py` に従い、字下げしたフェンスは中身から開きの行の字下げを外す
- まだ決まっていない値（新しい ADR の番号、日付など）は `NNNN` のような置換の鍵で書く。置換は block の中身にだけ当て、digest は置換の前の design.md で取る
- 参考に見せるだけで照合しない block は、フェンスの info に `noverify` の語を書く（例: ```` ```text noverify ````）。それ以外の block は、manifest の `new`・`content`・`text` のどれからも参照されていなければ不一致になる。`noverify` の block は参照できない

## digest

`## 確定文面` の見出し行から節の終わりの前の行までを `\n` でつなぎ、末尾に `\n` を 1 つ足した UTF-8 の byte 列の sha256。`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/confirmed-text.py digest --design <design.md> [--until <見出し>]` が `sha256=`・`lines=`・節を終わらせた見出し（`end:`）・照合する block と照合しない block の一覧を出す。human check では `end:` と 2 つの一覧を見せ、承認の範囲と照合しない block が意図どおりかを確かめてもらう。承認を受けたら、worklog.md に次の形の行を 1 行書く（再確認でも同じ形）。

`確定文面: <ISO 8601 の時刻> / sha256=<hex> / lines=<n> / end: <end: の値> / 理由: <承認 | 再確認: 理由> / 前: <前の sha256 | なし>`

block の中身を文書に貼るときは `extract --design <design.md> [--until <見出し>] --block D-n#i [--sub NNNN=0192]` で取り出す（置換の後の中身を、末尾の改行なしで出す）。

## 置き方の宣言（manifest）

置き方は design.md の散文から読まず、`.steering/<task>/confirmed-text.json` に宣言する（散文を解析すると判定が開いた入力になる）。

```json
{"digest": "<承認時の sha256>", "section_end": "## advisory の扱い", "substitutions": {"NNNN": "0192"},
 "files": [
  {"path": "AGENTS.md", "edits": [{"old": "次の 2 つで", "new": "次の 3 つで"},
                                  {"old": "  - 例外 2: …\n", "new": "  - 例外 2: …\n{{D-3#1}}\n"}]},
  {"path": "docs/adr/0192-x.md", "sections": [{"start": "## Decision\n", "end": "\n## Rejected Alternatives", "text": "{{D-1#1}}\n"}]},
  {"path": "docs/new.md", "content": "# 題\n\n{{D-2#1}}\n"}]}
```

- `edits`: base の版に、上から順に `old` → `new` を当てる。`old` は当てる時点の文でちょうど 1 回あたる文にする。確定文面の外で承認した直し（gate の指摘で直した空白など）も、`reason` を付けて同じ列に並べる。block の中身を書き換える直しはここに書かず、§ 確定文面の再確認 を通す
- `path` は repo からの相対の正規形（先頭の `/`、`.`・`..`・空の段、`\` を使わない）。base のファイルと大文字小文字だけが違う綴りは止める。`section_end` は `--until` と同じ（無ければ省く）
- `content`: base に無い新しいファイルの全体
- `sections`: 実物の `start` から `end` の前までを `text` と比べる（目印は実物でそれぞれ 1 回だけあたる）。base に無い新しいファイルのうち、承認した文が一部だけのときに使う（base にあるファイルは `edits` で書く）
- `{{D-n#i}}` は block の中身（置換の後）に展開する。この形でない `{{…}}` は文字どおりに扱う。知らない key・型の違い、当たらない、または重なりを含めて 2 回以上あたる `old` は、判定せずに止める
- manifest は digest の範囲に入れない。確定文面の外の直しを足すたびに human check をやり直さずに済むようにするためである。digest の突き合わせが守るのは、design.md の確定文面が manifest の `digest` のままであることだけである

## 照合

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/confirmed-text.py verify --design <design.md> --manifest <json> [--repo DIR] [--base REF] [--actual DIR]`（`--repo` は base を読む git repo、`--actual` は実物を読む場所。既定は `--repo` と同じ）

1. design.md の digest を取り直し、manifest の `digest` と違えば、ファイルを比べずに不一致にする
2. base（既定は `git merge-base origin/main HEAD`。マージ済みなどで合わないときは `--base` で渡す）の版に `edits` を当てた期待値と、実物のファイル全体を byte 単位で比べる。「含まれるか」では比べない。確定文面の隣に文を足す・1 文字変える・block を消す・改行を CRLF にする、のどれも不一致になる
3. `noverify` でない block が manifest の `new`・`content`・`text` のどれからも参照されていなければ不一致にする。照合した block と照合しない block の一覧を出す
4. 終了コードは 0 = 一致、1 = 不一致（差分の先頭 40 行を出す）、2 = 入力の誤り（判定できない）。2 を一致として扱わない

限界:
- `sections` は目印の外に足した文を見ない。新しいファイルの全体を承認したなら `content` で書く
- manifest に無いファイルの変更は見ない
- manifest は承認の外にある。置換の値、`{{…}}` の周りの地の文、後の `edits` で block の中身を書き換えると、design.md を変えずに承認と違う文を通せる。manifest の変更はレビューで見る
- manifest の `digest` は worklog.md の記録と照合しない。承認の後に design.md を直して `digest` を書き換えれば通るので、§ 確定文面の再確認 の手順 1 で記録と突き合わせる

## 確定文面の再確認（開き直し）

承認の後に確定文面の中を直す必要が出たら（レビューの指摘、事実の誤りなど）、次の順で行う。

1. 直す前に、承認のときと同じ `--until`（manifest の `section_end`）で `digest` を取り、worklog.md の最後の記録と一致することを確かめる（一致しなければ、承認の後に記録なしで直した文がある。先にそれを人に見せる）
2. design.md の block と、適用先の文書を直す。直す文と理由を human check（再確認）で見せ、承認を受ける
3. 承認の後に `digest` を取り直し、worklog.md に § digest の形の行（`理由: 再確認: …`、`前:` に前の sha256）を 1 行書く。前の digest は失効する
4. manifest の `digest` を新しい値にし、置き方が変わったなら `edits` を直す
5. `verify` を回し、exit 0 を確かめる。結果（`RESULT:` の行と base）を worklog.md に書く
