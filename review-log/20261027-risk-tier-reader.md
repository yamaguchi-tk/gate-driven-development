---
lane: L1+
pr: 584
follow_up_of: 576
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 89f67640 | 1 | 1 | 0 | 2026-10-27 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2606ee82 | 0 | 2 | 0 | 2026-10-27 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 4ea4d736 | 1 | 2 | 1 | 2026-10-27 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c3bb9db8 | 1 | 1 | 0 | 2026-10-27 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | 2b629dc8 | 0 | 0 | 0 | 2026-10-27 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 3a024f58 | 2 | 0 | 2 | 2026-10-27 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | 52c7ca33 | 0 | 0 | 0 | 2026-10-27 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 4b178e94 | 0 | 1 | 0 | 2026-10-27 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | high | no | self-inflicted | 発火の範囲 | fixed | 設計: 変える（発火に欄名を求めない）。草案は追加分の行に Human Check Status と risk-low が並ぶときだけ発火し、値だけを置換する Edit が素通りした（PR 旧#31 Finding C と同じ形）。Fable は射影の 2 層、Opus は欄名を問わず追加分のどこかに risk-low があれば発火を推した。手元の state.md 229 件で risk-low の揺れは 0 件で、狭める根拠が無いので広い側（Opus）を採った。commit: 6a443d4b |
| M-2 | 方針メモ | medium | no | self-inflicted | 読み手 | fixed | 読み手が高に倒す条件を広げた（通常のファイルとして読む・BOM・行は改行だけで割る・見出しと リスクの段: の行が 2 つ・判定できない）。commit: 6a443d4b |
| F1-1 | 独立-1 | medium | no | self-inflicted | 発火の範囲 | accepted | 依頼の原文から外れた（観点 0）: ApplyPatch では state.md 以外のファイルの追加行の risk-low でも止める。state.md 宛の追加行に絞ったが（59fb8288）、独立-2 の F2-1 でその絞り込みが fail-open を生んだので、patch 全体を見る形に戻した。ユーザーが選んだ Opus の広い形は全体を見る形で、別ファイルにだけ足す patch も止めることを PR 本文の限界に書く |
| F1-2 | 独立-1 | medium | no | self-inflicted | 文書の主張 | accepted | gate-status-schema.md の追記が、書く手順の無い risk-low: を「書ける」承認として書いている |
| F1-3 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | 変更断片と PR 本文の説明が実装と合わない（別ファイルの追加行・止めるのは書き間違いだけ・直後の行・判定できない の範囲） |
| F1-4 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | docs/SECURITY.md の降格しない category の列挙に risk_low_approval が無い |
| F1-5 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | docs/SECURITY.md の hook が読むものに request-crosscheck.md が無い |
| F1-6 | 独立-1 | low | no | self-inflicted | 書式の正本 | accepted | crosscheck の agent 定義（書式の正本）と読み手の定数をつなぐ記述・突き合わせのテストが無い |
| F1-7 | 独立-1 | low | no | self-inflicted | テストの検出力 | accepted | 低の枝・揺れ・止めないテストで rc を確かめていない |
| F1-8 | 独立-1 | low | no | self-inflicted | テストの検出力 | accepted | BOM 付きのケースが BOM の判定を消しても落ちない |
| F1-9 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | テストの docstring が実装に無い 2 層を書いている |
| F1-10 | 独立-1 | low | no | self-inflicted | 読み手 | accepted | 判定できない の語をファイル全体で見るので、形の整った低を高と読む |
| F1-11 | 独立-1 | low | no | self-inflicted | 件数の記録 | accepted | 止める条件の件数・未測の書き方が規則どおりでない |
| F1-12 | 独立-1 | advisory | no | self-inflicted | 読み手 | accepted | 後の段が上げた段を行頭の形だけで数える（PR-4 で書式を決める） |
| F1-13 | 独立-1 | advisory | no | self-inflicted | 受理集合 | accepted | PR-4 の承認の読み手との受理集合を確かめるものが無い |
| F1-14 | 独立-1 | advisory | no | self-inflicted | 信頼境界 | accepted | 判定の入力 request-crosscheck.md を守る相手と同じ main が書く |
| F1-15 | 独立-1 | advisory | no | self-inflicted | 文書の主張 | accepted | 降格しない category の注記に risk_low_approval の理由が無い |
| F1-16 | 独立-1 | advisory | no | self-inflicted | 変更断片 | accepted | 断片の Summary に利用者から見えない lib への移動がある |
| F2-1 | 独立-2 | high | yes | self-inflicted | 発火の範囲 | fixed | 設計: 変える（ApplyPatch の追加行をファイルに割り当てた結果で止めるかを決めない）。state.md 宛の行に絞った後、どのファイルにも入らない + 行（途中の End Patch の後など）の risk-low が通った。patch 全体の追加行を見る形に戻した。再現のテストを先に書いた。commit: 834a79ad |
| F2-2 | 独立-2 | medium | no | self-inflicted | 発火の範囲 | fixed | state.md 宛の行への絞り込みが、ユーザーの選んだ Opus の広い形からの縮小だった。F2-1 と同じ commit で広い形に戻した。commit: 834a79ad |
| F2-3 | 独立-2 | medium | no | self-inflicted | テストの検出力 | accepted | path ごとの判定の fail-open 側のテストが無い（どのファイルにも入らない行のテストは F2-1 で足した。path ごとの判定はやめた） |
| F2-4 | 独立-2 | low | no | self-inflicted | 文書の主張 | accepted | テストの docstring が実装に無い 2 層を書いている（F1-9 と同じ） |
| F2-5 | 独立-2 | advisory | no | self-inflicted | 性能 | accepted | state.md の target ごとに patch を走査し直す（F2-1 の修正で走査は無くなった） |
| F3-1 | 独立-3 | high | no | inherited | 発火の範囲 | fixed | 設計: 変える（追加分だけを見て書き込み後の state.md を見ない）。MultiEdit の複数の edit や 2 回の Edit で risk と -low を別の追加分に分けると、高の steering の state.md に risk-low: が着地する（追加分を 1 つずつしか見ず、書き込み後の値を見ない）。書き込み後の全文で、前に無かった risk-low の行が現れたら止める。commit: d59da932 |
| F3-2 | 独立-3 | medium | no | self-inflicted | テストの検出力 | accepted | 触れた state.md がすべて低のときだけ通す（all）を固めるテストが無い |
| F3-3 | 独立-3 | low | no | self-inflicted | 発火の範囲 | accepted | ApplyPatch の +++ で始まる追加行を extract_added_lines が飛ばす（field としては読まれない） |
| F3-4 | 独立-3 | low | no | self-inflicted | 文書の主張 | accepted | deny の本文が、別ファイルの追加行で止まったときも state.md に書いていると言う |
| F3-5 | 独立-3 | low | no | self-inflicted | 変更断片 | accepted | 変更断片の発火の範囲が、patch 全体・触れた steering のどれかの段に合っていない |
| F3-6 | 独立-3 | low | no | self-inflicted | テストの検出力 | accepted | 別ファイルの追加行のテストが、止めた理由を確かめていない |
| F3-7 | 独立-3 | low | no | inherited | 文書の主張 | accepted | テストの docstring が実装に無い 2 層を書いている（F1-9 と同じ） |
| F3-8 | 独立-3 | low | no | self-inflicted | 発火の範囲 | accepted | 確認待ち: 別ファイルの追加行・別の steering の state.md で止まる広げ方を、ユーザーに確かめた記録が無い |
| F3-9 | 独立-3 | advisory | no | self-inflicted | 文書の主張 | accepted | gate-status-schema.md の文が発火の範囲より狭く読め、F3-1 で「にだけ書ける」が成り立たない |
| F3-10 | 独立-3 | advisory | no | self-inflicted | 件数の記録 | accepted | PR 本文の「該当は 0 件のはず」を測っていない |
| M1-1 | 方針メモ-1 | advisory | no | inherited | 発火の範囲 | accepted | 安全策 4 が発火（発火の巡 c3bb9db8）。Opus・Fable とも A（書き込み後の全文で見る）。割れた点は、全文に risk-low があれば止める（Fable）か、前に無かった risk-low の行が現れたら止める（Opus）か。既存のテストが既に承認のある state.md への無関係な Edit を通すので Opus を採る。改行ごと消す Edit はツールと同じ動きで投影し、old_string が無い Edit だけを止め、ApplyPatch は生の + 行を全部見る（Opus）。old_string が無い Edit を止めると既存の契約テスト 5 件（無いファイルへの Edit など）が退行したので、2 本の推奨と違い止めずに追加分だけで判定し、引用符の正規化で当たる形を限界にした。2026-10-27 の返事（Opus 案で続行）で、既にある state.md への Edit に限って止める形にした |
| F4-1 | 独立-4 | high | yes | self-inflicted | 発火の範囲 | fixed | 設計: 変える（ツールの当て方を写す _project_like_tool をやめ、そのまま当てられない Edit を止める）。_project_like_tool の replace_all と空の new_string の当て方が reviewed_by_guard.edited_text（実測の写し）と違い、low を消す replace_all の Edit で分けた risk-low が止まらない commit: e00bfd77 |
| F4-2 | 独立-4 | high | yes | self-inflicted | 発火の範囲 | fixed | 設計: 変える（F4-1 と同じ）。old_string がそのまま無い Edit は 2 層目を見ないので、ツールが引用符・改行コードを正規化して当てる Edit で分けた risk-low が止まらない commit: e00bfd77 |
| F4-3 | 独立-4 | low | no | self-inflicted | テストの検出力 | accepted | replace_all の当て方・2 層目の読めない state.md・行の多重集合を固めるテストが無い |
| F4-4 | 独立-4 | low | no | self-inflicted | 変更断片 | accepted | 断片と gate-status-schema が、2 層目を見ない Edit の条件を書かずに止めると言う |
| F4-5 | 独立-4 | advisory | no | self-inflicted | 発火の範囲 | accepted | _edit_triples が Edit と MultiEdit のキーを合わせて返し、当たらない edit を混ぜると 2 層目が外れる（未知のキーをツールが拒むなら届かない） |
| F4-6 | 独立-4 | advisory | no | inherited | 発火の範囲 | accepted | move の移動元を読まず、Origin Session の検査の move 拒否に頼っている |
| F4-7 | 独立-4 | low | no | inherited | 文書の主張 | accepted | gdd-request-code-crosscheck.md:41 がどの gate もこの段を読まないと書いたまま |
| F4-8 | 独立-4 | advisory | no | inherited | 文書の主張 | accepted | deny の本文が常に state.md に書いていると言う（F3-4 と同じ） |
| F4-9 | 独立-4 | advisory | no | inherited | 信頼境界 | accepted | request-crosscheck.md を高から低に書き換えてから承認を書く形を止めない（PR 本文の限界にある） |
| F4-10 | 独立-4 | advisory | no | self-inflicted | 書式 | accepted | def read_risk_tier の前の空行が 1 行になった |
| M2-1 | 方針メモ-2 | advisory | no | inherited | 発火の範囲 | accepted | 安全策 4 の 2 回目の発火（発火の巡 3a024f58）。規則どおり止める扱いで PR を作り、F4-1・F4-2 を限界に書いて返事を待つ。Opus・Fable とも止める。続行のときの案は割れた。Fable は 2 層目を外す撤回（分けて書く形は事故の範囲の外）。Opus は old_string をそのまま当てられない Edit を止め（edit_misses_old_string。peer turn・Origin Session と同じ作り）、追加分の連結にも当て、_project_like_tool を消す（2 層目は、段を高に上げた後に値だけを置換する事故も守るため撤回しない）。ユーザーは Opus 案で続行を選んだ（既存の state.md への Edit に限る） |
| F5-1 | 独立-5 | medium | no | self-inflicted | テストの検出力 | accepted | 分けた形のテストの 2 件は追加分をつないだ層で先に止まり、書き込み後の行の多重集合の比較を数の比較に変えても通る。assert が層を区別しない |
| F5-2 | 独立-5 | low | no | self-inflicted | 改行の扱い | accepted | 書き込み前を read_regular_bytes の生の decode、書き込み後を read_text で読むので、CRLF の state.md で既にある risk-low の行が新しい行に数えられ、無関係な Edit が止まる（止める側） |
| F5-3 | 独立-5 | low | no | self-inflicted | 読めないファイル | accepted | 既にあるかを os.path.lexists で決めるので、親に権限が無い state.md は無いとみなす。ツールも書けないので通らない |
| F5-4 | 独立-5 | low | no | self-inflicted | deny の文面 | accepted | そのまま当てられない Edit にも risk_low_approval の Why（risk-low を読み違えて書く）が付き、原因を読み違えうる |
| F5-5 | 独立-5 | low | no | self-inflicted | テストの検出力 | accepted | 止めない側の assert が「リスクの段」の不在だけで、hook が例外で落ちる退行を検出しない |
| F5-6 | 独立-5 | advisory | no | self-inflicted | 受理集合 | accepted | _edit_triples の key の組が追加分の NEW_STRING_KEYS と違い、replacement などの別名の edit を後の 2 層が見ない（使う runtime は未確認） |
| F5-7 | 独立-5 | advisory | no | self-inflicted | 発火の範囲 | accepted | 無いファイルへの MultiEdit で最初の old_string が空のときと、英数字を挟んで後で置換する形は止まらない（事故の範囲の外） |
| F5-8 | 独立-5 | advisory | no | self-inflicted | 文書の主張 | accepted | state_write_projection.py の docstring とテストの docstring が、risk_tier の呼び出しと 4 層を書いていない |
| F5-9 | 独立-5 | advisory | no | self-inflicted | テストの検出力 | accepted | state.md への move は Origin Session の検査が止めているが、risk の側のコメント・テストにこの依存が無い |
| F5-10 | 独立-5 | advisory | no | self-inflicted | 文書の主張 | accepted | risk-low の行の他の部分を変える Edit が止まることと、通常のファイルでない state.md への Edit が止まることを、PR 本文に書いていない |
