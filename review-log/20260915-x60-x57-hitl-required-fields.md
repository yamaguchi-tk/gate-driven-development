---
lane: L1+
pr: 92
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose subagent (read-only, diff-only, 経緯非共有; L1+ 追加観点 (g)(h)+security 込み) | 043648c | 2 | 1 | 2 | 2026-09-16T00:00+09:00 |
| PR後-1 | GitHub PR 旧#92 review (yamaguchi-tk、review状態:COMMENTED 1件 + issue comment 1件、計2件) | 839925e | 1 | 5 | 1 | 2026-09-16T12:00+09:00 |
| 独立-2 | general-purpose subagent (read-only, diff-only, 経緯非共有; 対象は独立-1 の sha 043648c 以降の差分のみ、review-log/ 除外; L1+ 追加観点 (g)(h)+security 込み) | 9f75601 | 1 | 1 | 1 | 2026-09-16T14:00+09:00 |
| PR後-2 | GitHub PR 旧#92 review (yamaguchi-tk) | 61fda7d | 1 | 1 | 0 | 2026-09-16T16:00+09:00 |
| 方針メモ | opus (second opinion, via Agent tool) | - | 1 | 0 | 0 | 2026-09-16T16:30+09:00 |
| PR後-3 | GitHub PR 旧#92 review (yamaguchi-tk) | 5218fbc | 0 | 1 | 0 | 2026-09-16T18:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | yes | self-inflicted | raw-text-match-vs-placeholder | fixed | 未編集 placeholder 自身の例示文言（「選択肢なし（単一案。理由:」等）が該当なし明記/Option ラベルとして誤検出され、4節中3節+Option軸が黙って合格していた |
| F2 | 独立-1 | high | yes | self-inflicted | warn-path-budget-not-shared | fixed | warn パスが独立した新しい時間予算を確保しており、Stop hook 全体の timeout に近づき既存の block ゲート自体が到達不能になりうる構造だった |
| F3 | 独立-1 | medium | no | self-inflicted | raw-text-match-vs-placeholder | fixed | テスト fixture が実テンプレートの placeholder 文言を再現しておらず F1 を検出できていなかった |
| F4 | 独立-1 | low | no | self-inflicted | option-axis-section-scope-asymmetry | accepted | Option 軸チェックの受理集合（節ごとの条件チェックと非対称）は意図的な設計と判断し、エラーメッセージの明確化のみ行った |
| G1 | PR後-1 | high | yes | self-inflicted | raw-text-match-vs-placeholder | fixed | 節の存在判定が `text.find(marker)` による部分一致で見出しに束縛されておらず、独立-1 の High（placeholder 例示句の誤認）と同一クラスタとして4パターン（前置きの散文言及・見出し削除+末尾参照行・bold見出し・別節の散文言及）が実機で再現された（L1+ 安全策#4 該当、方針メモでユーザーに線引きを確認）。見出し行（`#`〜`######`+節名、行末まで一致）のみをアンカーとする方式へ修正した |
| G2 | PR後-1 | medium | no | self-inflicted | option-axis-section-scope-asymmetry | fixed | Option ラベルを文書全体からカウントしており、判断ポイント中の短い言及だけで Option 軸が満たされたと誤認していた。「選択肢の説明」節内のみでカウントするよう修正した（方針メモでユーザー確認） |
| G3 | PR後-1 | medium | no | self-inflicted | template-lint-vocabulary-mismatch | fixed | テンプレートが指示する「0件なら延期・削除: なし」という正しい最小回答が、lint の受理句「該当なし（理由:」と食い違い exit 1 になっていた。テンプレートの定型句を受理句に追加した |
| G4 | PR後-1 | medium | no | self-inflicted | missing-regression-test | fixed | `enforce_hitl_lint_gate` が block パスと warn パスに同一 deadline を渡すことを固定するテストが無く、独立予算に戻す退行を検出できなかった。呼び出し元の deadline 一致を検証する regression test を追加した |
| G5 | PR後-1 | medium | no | inherited | template-scope-decision | deferred | full template（human-check-template.md）・gdd-requirements-gating skill が compact の常時表示化に追随していない。一次表示の正本を compact に揃えるか測定対象を限定するかは別途方針決定が必要なため後続課題とし、PR本文に開示した |
| G6 | PR後-1 | medium | no | self-inflicted | log-window-occupancy | deferred | warn失敗を finding 単位で hook-errors.log に書くため、将来 warn 対象 script が増えた場合に gdd-status の末尾5件窓を占有しうる。現状は配線対象が1本のみで実害が無いため後続課題とし、PR本文に開示した |
| H1 | 独立-2 | high | yes | self-inflicted | raw-text-match-vs-placeholder | fixed | `_visible_text()` の未編集 placeholder 除外が単一物理行前提のヒューリスティックで、placeholder 文言が複数の物理行に折り返されるとどの行も条件を満たさず除外対象から外れ、未編集のまま合格していた（F1・G1 と同一クラスタの3巡目の再発、L1+ 安全策#4 該当、方針メモで今回も修正する方針をユーザーに確認）。節全体を正規化した上で単一の `<...>` ブロックとして成立しているかを見る判定を追加して修正した |
| H2 | 独立-2 | medium | no | self-inflicted | heading-boundary-overbroad | fixed | 見出し境界検出を `#`〜`######`（H1〜H6）まで無差別に広げたことで、節本文中のフェンス付きコードブロック内の `# コメント` 行まで「次の見出し」と誤認し、正当な回答が途中で打ち切られて reject される false-reject 回帰が生じていた（この PR が新規に広げた範囲でのみ発生）。見出し判定を実テンプレートの実際の見出しレベル（`##`/`###`）に限定して修正した |
| H3 | 独立-2 | low | no | self-inflicted | heading-whitespace-charset | fixed | 見出し直後の空白判定が半角スペース/タブ限定で、全角スペース（U+3000）を含む見出しを認識できなかった。空白クラスを拡張して修正した |
| H4 | 独立-2 | low | no | self-inflicted | boilerplate-boundary-not-anchored | deferred | 末尾定型行「条件付き詳細: ...」の境界検出だけが見出しアンカー化されておらず、行頭アンカーなしの部分文字列一致のまま残っている。理論上の非対称性の指摘で実機未再現のため後続課題とした |
| H5 | 独立-2 | advisory | no | self-inflicted | duplicate-heading-first-match-only | deferred | 同じ見出しが文書内に複数回出現した場合、常に最初の出現だけを節本体として扱う（false-reject 方向で fail-open ではない）。実機未再現・発生頻度が低いと判断し後続課題とした |
| I1 | PR後-2 | high | yes | self-inflicted | raw-text-match-vs-placeholder | fixed | F1・G1・H1 と同一クラスタの4巡目の再発。`_visible_text` の行頭剥がしが `>`（blockquote マーカー）を含んでいなかったため、placeholder 行が `> <...>` のように引用として貼られると除外できず、未編集のまま例示文言が可視テキストに漏れて合格していた（単一行・複数行折返しの両方で実機再現）。L1+ 安全策#4 該当（同一クラスタの high が4巡連続）のため、個別パッチを続けずユーザーへ線引きを確認し、lint の設計自体を見直す方針とした（方針メモ参照）。最終的な修正内容は `_strip_line_prefix` による `>` の先頭専用剥がしと、na_phrase/Option ラベルの行頭アンカー化（方針メモ J1 の根本対策）の両方に分割して実装した |
| I2 | PR後-2 | medium | no | self-inflicted | heading-boundary-fence-unaware | deferred | 見出し・境界検出（`_heading_pattern` / `_HEADING_LINE_RE`）がフェンス（```）を認識しないため、フェンス付きコードブロック内に `##`/`###` 相当の行があると誤って見出し・境界として扱う可能性が理論上残る。方針メモで確認のとおり、フェンスマスキングの追加は Opus 設計レビューで「複雑さに見合わない」と判断され、本 PR のスコープでは対応せず Known limitations に開示し後続課題とした |
| J1 | 方針メモ | high | yes | self-inflicted | acceptance-check-not-anchored | fixed | I1（4巡目の再発）を受け、修正を続ける前に Opus（claude-opus-5）へセカンドオピニオンを依頼した。まず自分が提案していた「placeholder の完全一致比較 + フェンスマスキング」による全面改修は、新たな fail-open（placeholder への1文字編集で現状 reject の入力が誤って pass に反転する／角括弧だけ除去する既知バイパスが温存されたまま／テンプレートからの実行時抽出自体が失敗した場合の fail-open リスク）を持ち込むと指摘され、実装を見送った。根本原因は「na_phrase・Option ラベルの受理判定が可視テキスト中のどこでも一致する substring-anywhere のままで、除外ヒューリスティックの精度に受理判定の正しさが従属している」ことにあるとの指摘を受け、判定を「いずれかの可視行が na_phrase・Option ラベルで始まるか」という行頭アンカー方式に変更した（除外ヒューリスティックの精度に依存しない防御）。ユーザー確認（2026-09-16）のうえ、Opus 推奨の3段階案のうち (A) 本 PR での最小修正（`>` 剥がし + 行頭アンカー化 + 最終 HITL marker 位置での入力切り詰め）のみを実装し、(B) 宣言フィールド化（`<gdd-hitl-fields ...>`）による本命の再設計は別 PR の後続タスクへ切り離し、(C) 角括弧除去バイパス（Opus H-3、本 PR でも未解決）・フェンス埋め込み見出し（I2）等の残存する限界は changelog の Known limitations に明記する方針とした |
| K1 | PR後-3 | medium | yes | self-inflicted | first-marker-trigger-vs-scored-segment-mismatch | fixed | J1 で新設した `_final_hitl_segment()`（最後の marker 出現を採点対象にする設計）が、実際の Stop hook の発火点と逆向きだった。`hooks/scripts/gdd_stop_hook.py::_check_stop_markers` は `STOP_PATTERN.search(last_output)`（最初の一致）の reason だけで human-check-waiting への遷移を判定し、`enforce_hitl_lint_gate` にはその判定結果とともに `last_output` 全文をそのまま渡すため、実際に人間へ提示され pause の引き金になった HITL は常に最初の marker 出現に対応する（実コードで確認済み）。「本番（1つ目）が非 compliant でも、後ろに compliant な例を続けると合格する」という新たな fail-open を持ち込んでいた（実機で再現確認済み）。独立レビューなら High/fail-open 相当だが warn-only のため medium とした（レビュー自身の判定）。`_final_hitl_segment()` を `_scored_hitl_segment()` に改名し、最初の marker 出現までだけを採点対象にするよう修正した |
| K2 | PR後-3 | low | yes | self-inflicted | option-label-prefix-not-word-bounded | fixed | Option ラベルの prefix 一致（`_any_line_starts_with`）が `Option Alpha` のように `Option A` から始まる別の単語にも一致していた（実機再現済み）。H-2 の行頭アンカー化自体の精度を上げるため、ラベル直後が英数字でないことを要求する境界条件（`_any_line_starts_with_option_label`）を追加して修正した |
| K3 | PR後-3 | advisory | no | self-inflicted | closed-form-reason-content-not-validated | accepted | 固定句（例: `該当なし（理由:`）の判定は「行頭が固定句の文字列で始まるか」だけを見ており、理由部分が空のまま閉じ括弧だけ書いても合格する。closed-form（自由文の内容は一切解釈しない）という設計方針どおりの意図的な限界として受け入れ、changelog の Known limitations に開示した |
| K4 | PR後-3 | low | no | self-inflicted | known-limitations-wording-accuracy | fixed | I2（フェンス境界検出）の Known limitations 開示文言が「実機未再現」のままだったが、実際は GitHub レビューで「4節をフェンス内だけに置いた文書は rc=0」と実機再現されていた。文言を実測結果に合わせて訂正した |
