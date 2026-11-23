---
lane: L1
pr: 旧#158
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | de3fef31e2ddaa7490ce6ad92481f3f84dc565d9 | 0 | 2 | 0 | 2026-09-20T01:19+09:00 |
| 独立-2 | light-lane-independent-reviewer, 全差分, model: opus | 2cc77734691de7617c966d9e82aa8ac74b751325 | 0 | 1 | 0 | 2026-09-20T10:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | invalid-utf8-without-python | fixed | python3 が使えない（不在・壊れた shim）と `gdd_truncate_chars` が値を素通しし、Linux でも不正な UTF-8 が additionalContext に載って JSON が壊れる。ユーザーの指示（レビュー指摘に対応して）で直した。Goal の抽出に `iconv -c` を足し、再現テストを先に書いて macOS で RED→GREEN を確認（a884a012）|
| A2 | 独立-1 | medium | no | self-inflicted | fix-not-guarded-on-macos | accepted | 当該テストは macOS（BSD grep）では `-a` の有無にかかわらず通り、`-a` を外しても全量が緑のまま。grep の挙動を模したスタブのテストは、mock しか検証しないテストになるため足さない。守るのは Linux の CI（別 PR）で、限界として断片と PR 本文に開示した |
| A3 | 独立-1 | low | no | self-inflicted | sanitize-claim-overstated | fixed | 「不正バイトは CONTEXT の sanitize で落とす」の断定を、抽出の時点で `iconv -c` で落とす説明に直した（コメント・断片）|
| A4 | 独立-1 | low | no | inherited | goal-reader-asymmetry | accepted | 同じ `### 一言` を読む 3 実装のうち、SessionStart だけが実 Goal を出すようになった（他 2 つは sanitize が無く `-a` を足せない）。断片と PR 本文に開示済み。後続 PR で 2 つに sanitize を入れてから `-a` を足す |
| A5 | 独立-1 | advisory | no | inherited | fragment-heading-case | fixed | 断片の見出しを既存の多数派（9 件）の `Known limitations` に揃えた |
| A6 | 独立-1 | advisory | no | self-inflicted | task-size-cause-unresolved | fixed | Task Size の原因を切り分けた。`/usr/bin/grep` は行を出し、BSD sed が `illegal byte sequence` で失敗する。断片に書いた |
| B1 | 独立-2 | medium | no | self-inflicted | fix-not-guarded-on-macos | deferred | 主目的の `-a` の退行を検出するテストが無い（macOS は `-a` 無しでも通り、Linux CI は未着）。source-text assertion（`HOOK.read_text()` に `grep -aA1 '### 一言'` を含むこと。既存の contract テストと同じ idiom）を後続で足す。独立-1 の A2 と同じクラスタ。Issue 旧#159 にした |
| B2 | 独立-2 | low | no | self-inflicted | test-power | accepted | 追加テストの assert が `ゴール` だけで、`iconv -c` が「除去」でなく「打ち切り」でも通る。`ゴールです` にすれば固定できる。PR 本文に列挙 |
| B3 | 独立-2 | low | no | inherited | goal-reader-asymmetry | accepted | 同じ `### 一言` を読む 3 実装のうち SessionStart だけが直った（独立-1 の A4 と同じ）。姉妹 2 本は sanitize を入れてから `-a` を足す。共有ヘルパーに寄せる案あり。断片と PR 本文に開示済み |
| B4 | 独立-2 | advisory | no | self-inflicted | iconv-dependency | accepted | `iconv` の不在時は Goal が案内から外れる（壊れた JSON は出ない）。`command -v` で生値に戻す案は fail-open を開き直すので採らない |
| B5 | 独立-2 | advisory | no | inherited | test-name-mismatch | accepted | `test_invalid_utf8_in_state_value_...` は requirements.md の Goal を書いており名前と食い違う。後続で改名 |
