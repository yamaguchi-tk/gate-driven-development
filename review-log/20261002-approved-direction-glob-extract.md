---
lane: L1
pr: 298
follow_up_of: 295
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | cb2dd1fc6aefc48a565dd30b7613624e4aee93ff | 0 | 3 | 1 | 2026-10-02T16:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 6da43ff7be58a575b36b84fa5b3ef5b9e81490cb | 0 | 1 | 0 | 2026-10-02T18:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | Step 3c の INFO: global glob の分岐が、正本の「security-sensitive path の変更は human_recheck_required に昇格する」を「検討する」に弱めていた。昇格すると書き、正本の節を指した commit: e7d84335 |
| F2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 見出しの形の reader が `repo 全体` のような glob でない値を pattern にし、何も出さずに合格にする（colon の形とは受理集合が違う）。path らしい語だけを読み、無ければ INFO に落とす commit: 3578a473 |
| F3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 正本テンプレートの glob の欄の記入例 `src/http/cookie.ts` が、lint が ERROR にする単一ファイル固定の値。`src/http/**` にした commit: e7d84335 |
| F4 | 独立-1 | low | no | self-inflicted | product | fixed | 節の終わりを `#` で始まる行で判定し、`#123` の行や深い見出しでも閉じる。ATX の見出しで、同じ階層以上のときだけ閉じる commit: 3578a473 |
| F5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 複数行に分けた値は 1 行目しか読まず、残りを検査しないまま合格になる。欄より深く字下げした続きの箇条も読む commit: 3578a473 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 見出しの節があっても colon の形の reader が走り、自由文から path らしい語を拾う。断片の「カンマ区切り」「次の見出しで終わる」も実装と違う。見出しの節があれば colon の reader を走らせず、記述を実装に合わせた commit: 3578a473 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 未リリースの前の断片の「lint は見出しの形を読めない」を置き換える注記が無い commit: e7d84335 |
| F8 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 断片の Validation に時点に依存する実測の件数を書いていた。断片から外し、PR 本文に書く commit: e7d84335 |
| F9 | 独立-1 | low | no | self-inflicted | test-power | fixed | test_directory_globs_pass_silently は修正を戻しても通る。抽出の戻り値を完全一致で比べ、--quiet を外した commit: 4fd0069c |
| F10 | 独立-1 | low | no | self-inflicted | test-power | fixed | assertNotIn("deploy") は落ちようがない。抽出の戻り値を完全一致で比べた commit: 4fd0069c |
| F11 | 独立-1 | low | no | self-inflicted | test-power | fixed | 自由文のテストは、置換がずれると空振りする。置換の結果を assert した commit: 4fd0069c |
| F12 | 独立-1 | low | no | self-inflicted | test-power | fixed | hook の入口から ERROR が systemMessage に届くテストが無い。足した commit: 4fd0069c |
| F13 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | script の冒頭の docstring が見出しの形の読み方に追随していない commit: 3578a473 |
| F14 | 独立-1 | low | no | inherited | product | fixed | 承認時に Approved Direction を記録させる gdd-dev.md #10 が glob の欄を案内していない。自走範囲の glob 欄を書くと指した（runtime の token 予算に収めた） commit: e7d84335 |
| F15 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に、hook の advisory の変化が書かれていない。PR 本文に書いた commit: なし（PR 本文） |
| F16 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文の抜粋に実行結果の断定（実データの件数）がある（テンプレート外の記述あり）。抜粋から除き、レビューの節に移す |
| F17 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | hook 入口のテストの環境変数の修正は、lint の読み方とは別の問題（PR 本文に書いてある） |
| F18 | 独立-1 | advisory | no | self-inflicted | style | accepted | `.replace("INFO", "")` は何もしていなかった（テストの書き直しで消えた） |
| F19 | 独立-2 | medium | no | self-inflicted | test-power | accepted | `/` だけの語や `S-1/S-2` のような語も path らしい語に数えられ、glob の欄に自由文を書くと INFO が出ずに合格になる |
| F20 | 独立-2 | low | no | self-inflicted | product | accepted | `package.json` のような拡張子の語を取りこぼし、`・` 区切りや `+`・`1.` の箇条を分割・続きの行として読まない |
| F21 | 独立-2 | low | no | self-inflicted | test-power | accepted | 続きの箇条が、欄と同じ字下げの次の箇条で終わることを固定するテストが無い |
| F22 | 独立-2 | low | no | self-inflicted | product | accepted | 値が `<` で始まるものを読まない規則が、続きの行には効かない |
| F23 | 独立-2 | low | no | inherited | doc-claim | accepted | Step 3c の WARN の分岐と rollback-patterns の 120 行目が、正本の昇格を「検討」のまま書いている |
| F24 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | gdd-dev.md #10 の記録の項目が「自走範囲の glob 欄」に狭まり、AC の範囲を書く案内が消えた |
| F25 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界の「2 行以上に分けた値は読まない」は、印の無い折り返しの行だけに当てはまる。PR 本文で言い方を直す commit: なし（PR 本文） |
| F26 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 実データの照合は、時点（sha）を添えて PR 本文に書く |
| F27 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 行の予算（skill 本文・runtime の token）の余裕がほぼ無い |
| F28 | 独立-2 | advisory | no | self-inflicted | style | accepted | hook 入口のテストが import を関数の中で行っている |
| F29 | 独立-2 | advisory | no | self-inflicted | product | accepted | 見出しの階層の端（`#` 7 個以上・setext の見出し）は節の終わりとして扱わない |
