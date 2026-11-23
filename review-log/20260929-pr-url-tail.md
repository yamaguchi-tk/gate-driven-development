---
lane: L1+
pr: 242
follow_up_of: 236
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 19ef68938a2d913c504ea02e754ce77aaed074f4 | 2 | 1 | 2 | 2026-09-29T14:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 63b1aeca6b7e16034cdfd66c1a10165c73b82431 | 1 | 0 | 1 | 2026-09-29T14:50+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) | ef9e6d95f96895d3aefdf49a7208d39299cb2c44 | 3 | 0 | 3 | 2026-09-29T15:20+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 33039ad5ffffc982961c4695e7f2b25112ef85d7 | 0 | 1 | 0 | 2026-09-29T15:55+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | yes | self-inflicted | url-tail | fixed | URL の全体一致（番号の後を `[/?#]` で始まる形か終端に限る）に外れた `…/pull/7x`・`…/pull/7.`・引用した末尾空白つきの形が branch と読まれ、台帳の git-cwd の経路（hit のときだけ止める）で台帳の PR の merge が unknown として通っていた。URL は gh と同じく番号の前方一致で正準形にして記録し、名指しできない形は unresolvable を立てる形にした。hook の入口の再現テストを先に書いて失敗を確かめた。commit: c64ea977 |
| F2 | 独立-1 | high | yes | inherited | url-tail | fixed | `www.github.com`・port・userinfo・path の `%xx` を含む URL も gh は PR の URL と読むが、branch と読まれて F1 と同じ経路で通っていた。`urlsplit` で host（github.com・www.github.com）を読み、path の `%xx` を戻して前方一致し、名指しできない形は F1 と同じ扱いにした。commit: c64ea977 |
| F3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 変更断片と抜粋の「止める」が、台帳の git-cwd の経路（当たるときだけ止める）と合わなかった。経路ごとの挙動（本体の経路は pr-target-unresolvable、台帳の経路は台帳の PR に当たれば止める）に書き直した。commit: c64ea977 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `gh_command_parse.py` の URL の読み方のコメントが、gh の前方一致と実在しない置き換えの印の説明で不正確だった。実態（前方一致・host・`%xx`）に書き直した。commit: c64ea977 |
| F5 | 独立-1 | low | no | self-inflicted | test-naming | fixed | `/pull/7x` を branch と読むと名付けたテストが実態と食い違っていた。URL を読んだうえで unresolvable になるテストに分けた。commit: c64ea977 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片に開発の経緯（直前の変更でテストが落ちていた）の文があった。利用者から見える変更だけにした。commit: c64ea977 |
| F7 | 独立-1 | low | no | inherited | doc-claim | fixed | `merge-gate-evidence.sh` のコメントが存在しなくなった `PR_URL_RE` を同一形と説明していた。現状の 2 つの定数との違いに直した。commit: c64ea977 |
| F8 | 独立-1 | low | no | inherited | test-power | fixed | 行継続の契約のテストが `pr_url` を assert せず、URL の正準形の退行が通っていた。URL のケースで `pr_url` を assert した。commit: c64ea977 |
| A1 | 独立-1 | advisory | no | inherited | file-size | accepted | `gh_command_parse.py` が行数の目安（1,500 行）に近い。この変更の増分は小さく、分割は別の課題。PR 本文の限界の節に書く |
| G1 | 独立-2 | high | yes | inherited | url-host | fixed | marker の無い checkout の台帳の経路で、`gh pr merge https://api.github.com/acme/infra-gdd/pull/7` のように `github.com` の下位の host（`api.`・`foo.bar.` など）の URL が host の列挙の外として branch と読まれ、台帳の PR が通っていた。gh は下位の host を github.com と読む（gh 2.93.0 の `gh pr view https://api.github.com/cli/cli/pull/1` が github.com の PR を返すことを read-only で確認。`notgithub.com` は別 host に送られる）。host を `github.com` かその下位に広げ、名指しできる形は netloc が `github.com` に完全一致するときだけにした。先に台帳経路の hook 入口の再現を書いて失敗を確かめた。commit: d69c342f |
| G2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | `…/pull/1` + 語の途中の行継続の形は gh の対象が 旧#123 になりうるのに、docstring・変更断片・テストが「gh が merge する PR と同じ」「別の PR と読み違えない」と断定し、`pr_url` の 旧#1 を固定していた。docstring と断片を実態に直し、テストは `unresolvable` だけを固定する形に戻した。commit: d69c342f |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | `unresolvable` の原因を列挙するコメント 3 か所とテストの docstring に、名指しできない URL が無かった。足した。commit: d69c342f |
| G4 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 「`%xx` を含む」の記述が広く、検査しているのは path だけだった。「path の `%xx`」に直した。commit: d69c342f |
| G5 | 独立-2 | advisory | no | inherited | hitl-message | accepted | `pr-target-unresolvable` の次の 1 アクションの文言が、URL の形を直せばよいことを伝えない。表示文の変更で、この PR の判定を変えないので、PR 本文の限界の節に書く |
| G6 | 独立-2 | advisory | no | inherited | independence | accepted | review-log の commit の件名が、前の巡の話題（URL の読み方）を起動時の git status 経由で reviewer に伝えた。判断には使われていない。以後の review-log の commit の件名は話題を書かない形にする |
| M1 | 方針メモ-1 | high | yes | inherited | url-host | fixed | 安全策 4 の発火（同じ型の high が 独立-1・独立-2 で 2 巡）で Opus に相談した。推奨は、host の列挙で gh の受理集合に近づける設計を止め、host を問わず path を読む設計にすること。Opus が gh 2.93.0 の `gh pr view` で確かめた、gh は github.com の PR と読むのに hit しない入力: host が空の `https:/o/r/pull/7`・`https:///o/r/pull/7`。commit: 74071dba |
| M2 | 方針メモ-1 | high | yes | inherited | url-host | fixed | 同上: Unicode の大小変換で github.com になる host（`gİthub.com`）は、Python の lower が一致せず branch になり台帳経路で通っていた。host を問わず path を読む形で閉じた。commit: 74071dba |
| M3 | 方針メモ-1 | high | yes | inherited | url-host | fixed | 同上: NFKC で区切り文字になる全角文字を含む下位 host（`a／.github.com`・`a＃.github.com`）で `urlsplit` が ValueError を投げ、握りつぶして None を返していた。`urlsplit` をやめ、手で `//authority` を切り出す形にした。3 件とも台帳経路の hook 入口の再現テストを先に書いて失敗を確かめた。方針メモ: ユーザーへの確認は 2026-09-28 の決定（HITL は当初の機能が実装できる見込みが無いときだけ。設計変更は内部相談）に従い行っていない。続行の判断は agent が行った。commit: 74071dba |
| J1 | 独立-3 | medium | no | inherited | line-continuation | accepted | 語の途中に行継続を挟んだ URL・番号（`…/pull/1\⏎23`）は、marker の無い checkout の台帳の経路で読んだ 旧#1 で照合され、bash が繋ぐ 旧#123 が台帳の PR でも unknown として通る。台帳の経路の契約（hit のときだけ止める）どおりで、main も同じく通していた。パーサ側の修正（token の改行を除いて読む）は判定のコードで、最後の巡の後に足すと巡が無効になる。follow_up_of の PR なので accepted にし、PR 本文の限界の節に書く |
| J2 | 独立-3 | low | no | self-inflicted | scheme-case | accepted | `URL_SCHEME_RE` の `(?i)` が `ſ`（U+017F）を `s` と受け、`httpſ://…/pull/7` が名指しになる。gh は失敗し何も merge しない（実害なし）。判定のコードの修正になるので accepted、PR 本文の限界の節に書く |
| J3 | 独立-3 | low | no | inherited | shell-expansion | accepted | `$` などの shell の展開を owner/repo に含む URL が名指しになる。意図した偽装でしか起きず、強度モデルの外。判定のコードの修正になるので accepted、限界の節に書く |
| J4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 変更断片の「host が github.com の完全一致」が、大小文字を無視する実装と食い違っていた。「大小文字を除いて一致」に直した。commit: 52ac658f |
| J5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 台帳のテストの docstring が、受け入れた止めすぎ（別の host の同じ owner/repo/番号）を gh が台帳の PR と読む入力と呼んでいた。実態を書いた。commit: 52ac658f |
| J6 | 独立-3 | low | no | self-inflicted | test-power | fixed | `test_hostile_url_tokens_never_raise` が `is_merge` だけを見ていた。各入力で unresolvable を assert した。commit: 52ac658f |
| J7 | 独立-3 | advisory | no | inherited | independence | accepted | review-log の commit の件名が前の巡の話題を伝えた（独立-2 の G6 と同じ）。以後の件名は話題を書かない形にしている |
| J8 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | host が空の形・Unicode の綴り・下位の host が gh でどう読まれるかの根拠の記述。下位の host は gh 2.93.0 の `gh pr view` で確認済み。host が空・Unicode・全角文字を含む形は、別の gh の read-only 実行で確かめた（挙動は止める側に倒れる）。PR 本文の限界の節に、確認の範囲を書く |
| J9 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | 変更断片の Validation が、行継続のテストの見る範囲より広く書かれていた。unresolvable になる契約に狭めた。commit: 52ac658f |
| J10 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | User Action Required が「なし」のまま、別の host（GHES）の同じ owner/repo/番号の URL が止まる場合の出口を書いていない。まれな形なので限界の節に書くだけにする |
| J11 | 独立-3 | advisory | no | inherited | doc-claim | accepted | run-merge-gate-hook.sh:390 の unresolvable の原因の列挙が 654 行と揃っていない（値の欠落）。コメントの修正は判定のコードの変更になるので accepted |
