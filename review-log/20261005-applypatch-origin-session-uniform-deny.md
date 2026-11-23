---
lane: L1+
pr: 373
follow_up_of: 355
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user（ブランチ 20261004-patch-fence-and-fuzzy-removal〔旧#355 の限界を、Codex の apply_patch の写しで全文に当てて閉じる案〕は、安全策 4 が 3 回発火したところで、ユーザーが設計の見直しを指示した。実測: 実在の state.md 478 本で `Origin Session` の行 0 本・`Origin Notification: sent` 0 件、transcript で値の書き込み 0 件、Codex の sessions で `Origin Session` 0 件、Bash による state.md の書き込み 69 件〔検査の対象外〕、前例の `completed_reviewed_by` は ApplyPatch を見ない。Opus は、ApplyPatch の値の推定をやめ、既存の綴りの target 判定 × 既存値 × peer turn で一律に止める案 B を、main から新しい PR で行うよう推した。main の案との違いは、通す分岐を消して止める側に固定する、target の判定は既存のものを使う、旧#355 の peer turn の移動元の検査は残す、の 3 点で、main は 3 点とも採った。Origin Session そのものの撤去〔D〕はユーザーに出し、ユーザーは B を選んだ。前のブランチは PR にしない） | - | 0 | 0 | 0 | 2026-10-05T01:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 39e69bf208d7feb18708839be49f253d1444e44b | 3 | 0 | 2 | 2026-10-05T02:10+09:00 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user（独立-1 の `閉じ方: 列挙` の F2・F3。入力者の実測: Origin Session の行・書き込みは実データで 0 件、`..` を含む ApplyPatch は 0/1,001 件。Opus は F3 を (b) にし、F2 は main の置き換え案〔語の照合で全ターン止める〕が要件を縮める (c) に当たるとして、ユーザーに聞くよう推した。あわせて、照合の範囲に今の state.md の本文を入れ、バッククォートを除いて照合すれば、当てた後の行の出どころ〔patch・移動元・今の state.md〕を全部覆うと示した。main の案は (a) に数えない語の拒否で、照合の範囲が狭かった点で食い違い、main は Opus の形を採った。ユーザーは (c) を承認した。F1〔閉じ方: 構造〕も同じ判定で閉じる） | - | 0 | 0 | 0 | 2026-10-05T02:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3577449f2f6393f9e207ed5757179d7ca8aff106 | 3 | 1 | 3 | 2026-10-05T03:00+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable アドバイザリ (gate-driven-development:gdd-fable-advisor) + user（安全策 4 の発火: path-alias のクラスタの high が独立-1〔F3〕と独立-2〔H3、self-inflicted〕の 2 回。あわせて H1・H3 の `閉じ方: 列挙`。実測: 実在の steering の md 3,639 本で `Origin Session` の語 0 本、Codex の apply_patch で state.md 宛てに語を含むもの 0、state.md を移動先にする patch 1 件〔steering ディレクトリの移し替え〕、綴りの違う move の連鎖 0。Opus は H1・H3 を (b) として「止める」を推し、閉じるなら state.md を移動先にする patch を移動元を読まずに止める案 A'〔(c)〕とした。H2 は実害クラスなので再掲にできず (b) で accepted とした。main の案〔A: H1 を短絡、H3 を構造で直す〕と食い違ったので信号 ① で Fable を呼び、Fable はこの PR でのユーザーの選び方と H1 がこの PR の退行であることから A' を推した。ユーザーは A' を選んだ） | - | 0 | 0 | 0 | 2026-10-05T03:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 8792003b3533819a699bd1c46e401eef1af77037 | 1 | 1 | 1 | 2026-10-05T04:10+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus)（独立-3 の J1 の `閉じ方: 列挙`。入力者: 実在の state.md 478 本で FIFO 0、agent が steering に FIFO を作る操作は未観測〔件数は未測〕。Opus は (b) を推し、main の案と同じだった。J1 は H2 と同じ根〔今の state.md の読み込みが通常でないファイルで戻らない〕で、指摘の行〔:1405〕はこの PR の全差分の変更行に入らないので inherited・path-alias とし、安全策 4 の数えから外れる。巡の上限の 3 巡目なので直す commit は積まない） | - | 0 | 0 | 0 | 2026-10-05T04:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| F1 | 独立-1 | high | yes | self-inflicted | origin-patch-word | fixed | peer turn の初回値の判定が生の部分文字列だけを見るので、field 名の途中のバッククォート（`` O`rigin Session ``）と、既存の記入例の fence の開きを消す patch が通る。reader と同じくバッククォートを除き、今の state.md の本文も照合に入れて、ターンによらず止める。commit: 154efe42 |
| F2 | 独立-1 | high | no | self-inflicted | origin-patch-word | fixed | 列挙: 通常のターンの 2 値の判定が、全ファイルの追加行を 1 本で読み、move で運ぶ値を見ないので、値が 2 行ある state.md を作れる。方針メモ-1 でユーザーが (c) を承認し、ApplyPatch では初回の値も書かせない形（patch・移動元・今の state.md のどこかに語があれば止める）にした。commit: 154efe42 |
| F3 | 独立-1 | high | yes | inherited | path-alias | accepted | 列挙: 途中のディレクトリが無い `d/../state.md` では既存の本文を読めず空として扱うので、ApplyPatch の判定と Write・Edit の書き換えの禁止を外れうる（Codex がこの綴りをどう当てるかは未測）。入力者: `..` を含む ApplyPatch は 0/1,001 件。方針メモ-1 で (b) にした。PR 本文の限界の先頭に書く |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `collect_origin_session_rewrite_violations` の docstring が、ApplyPatch の判定と、もう無い「削除の 4 形」の正本を書いたまま。ApplyPatch の規則を書き、`_origin_session_patch_reason()` を指した。commit: 247aa9f3 |
| F5 | 独立-1 | low | no | self-inflicted | product | fixed | 新しい deny の Why の文が `Origin Notification: unavailable` の記録を案内するが、それも ApplyPatch では止まる。降格しない根拠のコメントも「書き換えをやめれば解消」のまま。Why に Write・Edit で書く・shell で書かずにユーザーに頼むことを足し、コメントに降格しない理由を書いた。commit: 247aa9f3 |
| F6 | 独立-1 | low | no | self-inflicted | test-power | fixed | 一律 deny の後に切り分けを見分けなくなったテストの名前・docstring、期待値を被検査関数で作るテスト、既存値が無いと書く class docstring。名前と docstring を今の挙動に合わせ、category と理由の文を assert するようにした。commit: 55ddd6f8 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の止める範囲が「流れ込む」だけで狭く、User Action Required が「なし」。止める範囲を書き直し、Edit・Write の無い runtime での手順を書いた（hook の終了コードの契約は変えないので type は patch のまま）。commit: 247aa9f3 |
| K2 | 方針メモ-1 | - | - | - | - | - | なし |
| H1 | 独立-2 | high | yes | self-inflicted | timeout | fixed | 列挙: 値のある state.md へ move する patch で、移動元を全部読んでから判定するので、巨大な移動元で hook の timeout（止めない側）に届きうる（差分前は読まずに止めていた）。方針メモ-2 でユーザーが A' を選び、state.md を移動先にする patch は移動元を読まずに止め、Origin Session の検査からも移動元の読み込みを外した。commit: 6022ad16 |
| H2 | 独立-2 | high | yes | inherited | path-alias | accepted | 列挙: 今の state.md を読めない（`d/../state.md`・権限なし・FIFO は timeout）と本文を空として扱う。F3 と同じ穴で、実害クラスなので再掲にできない。入力者 0/1,001 件。方針メモ-2 で (b) にした。PR 本文の限界の先頭に書く |
| H3 | 独立-2 | high | yes | self-inflicted | path-alias | fixed | 列挙: 移動元の連鎖を綴り（`normalize_path`）で比べるので、`a.md→b.md` と `./b.md→state.md` の連鎖で a.md の値を見落とす。方針メモ-2 の A' で、state.md を移動先にする patch を連鎖をたどらずに止めた。commit: 6022ad16 |
| H4 | 独立-2 | medium | no | self-inflicted | product | accepted | 語で止めるので、値の無い行や記入例・別ファイルの行でも止まる。実在の steering の md 3,639 本で語を含むもの 0 本（方針メモ-2 の実測）。follow_up_of のある PR なので直さず、PR 本文の限界に書く |
| H5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 理由の文が「field を書く」と読め、値の行に触れない patch で読み違いを招く。A' の修正で、変更そのものを Write・Edit で行う案内に変えた。commit: 6022ad16 |
| H6 | 独立-2 | low | no | self-inflicted | product | accepted | deny の本文が ApplyPatch の runtime で agent に届くかは未確認。follow_up_of のある PR なので直さず、PR 本文の限界に書く |
| H7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の「語の無い patch は通す」が、語のある移動元を move する形を除いていない。A' で state.md を移動先にする patch は止まるので、断片をその形に書き直した。commit: f6e10f39 |
| H8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary が、綴りの違いを推定をやめたことで解消したように読める（今の state.md の読み込みは綴りに依存したまま）。follow_up_of のある PR なので直さず、PR 本文の限界に書く |
| H9 | 独立-2 | low | no | inherited | doc-claim | accepted | SECURITY.md の hook の読み取り範囲に、ApplyPatch の move の移動元が無い。A' で Origin Session の検査は移動元を読まなくなったが、peer turn の記録の検査は state.md 以外への move で読む。follow_up_of のある PR なので直さず、PR 本文の限界に書く |
| H10 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり。PR 本文の抜粋の限界の節に、受け入れた指摘の記録を書いていた。次の巡の前に抜粋から除く |
| K3 | 方針メモ-2 | - | - | - | - | - | なし |
| J1 | 独立-3 | high | yes | inherited | path-alias | accepted | 列挙: state.md が FIFO だと今の state.md の読み込み（validate-steering-write.py:1405）が戻らず、hook の timeout（止めない側）で通りうる。move の判定より先に読むので、FIFO の state.md から state.md への move も止まらない。H2 と同じ根。入力者: state.md 478 本で FIFO 0。方針メモ-3 で (b) にした。PR 本文の限界の先頭に書く |
| J2 | 独立-3 | medium | no | self-inflicted | test-power | accepted | main() の peer turn の検査の skip が「move の規則が必ず止める」という別の関数の不変条件に頼っていて、それを固定するテストと `patch_move_destinations` の単体テストが無い。follow_up_of のある PR なので直さず、PR 本文の限界に書く |
| J3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「移動元を読まずに止める」は、移動元が steering の state.md なら今の state.md として開くので成り立たない。PR 本文の限界に書く |
| J4 | 独立-3 | low | no | self-inflicted | test-power | accepted | move のテストが peer turn の理由の有無と、移動元を読まないことを確かめていない。PR 本文の限界に書く |
| J5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | peer turn の検査は移動元を読まないだけでなく丸ごと飛ぶので、peer turn の理由の案内が出ない（deny のまま）。PR 本文の限界に書く |
| J6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | テストの module docstring と write_once_contract の docstring が、移動元を読む前の規則のまま。PR 本文の限界に書く |
| J7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | collect の docstring に、語によらず止める move の規則が無い。PR 本文の限界に書く |
| J8 | 独立-3 | low | no | self-inflicted | style | accepted | validate-steering-write.py は main（1,684 行）より減ったが、差分の hunk は +4 と数えられた。未使用の import の削除などで減らせる。PR 本文の限界に書く |
| J9 | 独立-3 | low | no | inherited | doc-claim | accepted | SECURITY.md の読み取り範囲に、peer turn の ApplyPatch で state.md 以外の steering へ move される移動元が無い。H9 と同じ。PR 本文の限界に書く |
| J10 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | advisory: `_Hunk` の docstring が stray を target のためだけと書く |
| J11 | 独立-3 | advisory | no | self-inflicted | product | accepted | advisory: move の deny に Origin Session の Why が付き、field の無い move でも宛先の書き換えの説明が出る |
| J12 | 独立-3 | advisory | no | self-inflicted | style | accepted | advisory: `[hunk.path] * (hunk.kind == "stray")` の bool の掛け算が読みにくい |
| J13 | 独立-3 | advisory | no | inherited | doc-claim | accepted | advisory: `_read_patch_source` の docstring の「Update の先」が古い |
| J14 | 独立-3 | advisory | no | inherited | test-power | accepted | advisory: test_patch_section_scan.py の state.md への move のテストが、どの規則で止まったかを理由の文で区別していない |
| K4 | 方針メモ-3 | - | - | - | - | - | なし |
