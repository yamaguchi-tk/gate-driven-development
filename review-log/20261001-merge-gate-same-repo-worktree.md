---
lane: L1+
pr: 268
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（ユーザーの指示「hook が原因なら修正して」の範囲で、memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた。Opus の推奨〔共通ディレクトリの一致は対象 PR を明示したときだけ、rev-parse の出力を 2 行の絶対パスに限る、marker のある同 repo の cd 先は root にしてそこの証跡で判定、root の切り替えは `cd "$PROJECT_ROOT"` の前、後ろの cd は次の PR〕をすべて採った。main の案との食い違いは残らず、Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-01T22:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 7bf3c17981a98d7d349dcdb9e8c07ad35c84d175 | 2 | 1 | 2 | 2026-10-01T23:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | ab27e1c3d090a7eca08425fde1c7249c346dd769 | 3 | 0 | 3 | 2026-10-02T00:10+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（安全策 4 の発火〔クラスタ path-normalization の high が独立-1・独立-2 の 2 巡〕。Fable は信号 ② で 1 回。Opus・Fable・main の案はどれも「F3 を直し、差分巡 1 回の後で止める」で一致し、Fable は F1・F2 を次の PR で fail-closed に倒す案を足した。memory の 2026-09-28 の決定〔差分の外の既存の常時 High は、直す次の PR を続けて出すなら限界に書いてマージしてよい〕に従い、ユーザーへの確認は内部の相談で代えて「止める」を採った） | - | 0 | 0 | 0 | 2026-10-02T00:40+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 612abfa03c361f79e3f797b4cf704e1442ea0ede | 0 | 1 | 0 | 2026-10-02T01:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| L1 | 独立-1 | high | yes | self-inflicted | exec-target-asymmetry | fixed | AC-18 の緩和は payload cwd にも効くが、root の切り替えは cd 先だけで、payload cwd で marker のある同 repo の worktree を指すと証跡を見ずに通る。marker のある実行先は緩和しないようにした commit: ab27e1c3 |
| L2 | 独立-1 | high | yes | self-inflicted | path-normalization | fixed | rev-parse の出力を最初の改行で切り、改行を含む toplevel が root と同じ文字列になる。2 行の絶対パスでなければ toplevel を単独の呼び出しで取り直す commit: ab27e1c3 |
| L3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | payload cwd に効くことが断片と PR 本文に無い。断片と PR 本文に書いた commit: ab27e1c3 |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「-R の扱いは変えていない」「共通ディレクトリが同じなら対象 repo は同じ」が実装より広い。条件付きに直した commit: ab27e1c3 |
| L5 | 独立-1 | low | no | self-inflicted | test-power | fixed | allow 側が block の不在だけを見る。failing の subtest は reason を固定せず toplevel ごと落ちる経路しか通らない。終了コードと無出力・reason を固定し、toplevel を取り直す経路を通した commit: ab27e1c3 |
| L6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | AC-18 のコメント「toplevel が一致するときだけ通す」と「toplevel の解決には影響させない」が実装と合わない。直した commit: ab27e1c3 |
| L7 | 独立-1 | low | no | self-inflicted | product | fixed | 対象 PR を記録していない marker 付き worktree への cd は reason が untrusted-root-unverified に変わり、案内どおり記録しても通らない。PR 本文の限界に書いた commit: なし（PR 本文） |
| L8 | 独立-1 | low | no | self-inflicted | product | fixed | 同 repo への cd で PR を省いた merge の block の案内が、効く手（番号か URL の明示）を先頭に示さない。PR 本文の限界に書いた commit: なし（PR 本文） |
| L9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片に内部の実装の詳細（rev-parse 1 回、PROJECT_ROOT_UNTRUSTED）がある。PR 本文に列挙 |
| L10 | 独立-1 | advisory | no | self-inflicted | product | accepted | Git for Windows は C:/ 形のパスを返し、共通ディレクトリが常に空になって修正が効かない（fail-closed）。PR 本文に列挙 |
| L11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | deny 9 件のうち PR を明示した形の件数が無い。PR 本文に件数を書いた |
| M1 | 独立-2 | high | yes | inherited | path-normalization | accepted | $() が末尾の改行を落とし、名前が改行で終わるディレクトリの toplevel が root と同じ文字列になって AC-18 を通る（main の候補ループにもある既存の穴。実データ 0 件）。次の PR で、改行で終わる値を解決不能として止める側に倒す |
| M2 | 独立-2 | high | yes | inherited | path-normalization | accepted | payload cwd の抽出も $() で末尾の改行を落とす（main と同じ）。M1 と同じ次の PR で直す |
| M3 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | 共通ディレクトリで通した marker の無い実行先への merge が、素通りの 3 つの exit で PR 台帳を照合しない。フラグを立て、3 つの exit の前で台帳を引いて miss 以外は止める commit: 612abfa0 |
| M4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の「パスが改行を含むなど…従来どおり止める」が末尾の改行では成り立たない。「パスの途中に改行を含む」に限った（断片は後の PR で書き換えられないので push 前に直した） commit: e68e18ba |
| M5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の「payload の cwd で marker を持つ worktree を指した merge は従来どおり止まる」は、セッションの worktree が marker を持つときだけ成り立つ。条件を足した commit: e68e18ba |
| M6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の「同じ repo への cd の後の -R は直接打ったときと同じ扱い」は、marker のある cd 先では成り立たない。その文を削った commit: e68e18ba |
| M7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | テストの docstring が「共通ディレクトリが同じなら gh の対象 repo も同じ」と断定したまま |
| M8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation に、payload cwd で marker の無い別 worktree を指す形が通ることが無い。PR 本文に列挙 |
| M9 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 改行のテストの fixture が同じ repo なので、害そのものではなく今の fail-closed の実装を固定している。PR 本文に列挙 |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| N1 | 独立-3 | medium | no | self-inflicted | doc-claim | fixed | 断片が台帳の照合という新しい止める出口を書いていない。Summary・Fixed・Validation に足した（断片は後の PR で書き換えられないので push 前に直した） commit: e68e18ba |
| N2 | 独立-3 | medium | no | self-inflicted | test-power | next-pr | 共通ディレクトリで通した経路の unknown・unreadable を止めることのテストが無い（miss 以外を hit に変える変異が生き残る） |
| N3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 台帳の読み手を列挙する注記（hook :375・:386-387、gdd-pr-roots.sh、2 つのテストの docstring）が 2 経路のまま |
| N4 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | hook の AC-18 の注記と PR 本文の「直接 merge と同じ扱い」が、台帳の照合の後は不正確 |
| N5 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 新しいテストが GDD_HOOK_STATE_DIR を落とさず、手元の環境変数で台帳の場所が変わる |
| N6 | 独立-3 | low | no | self-inflicted | style | next-pr | 台帳の fixture を写しで定義している（test_merge_gate_hook_non_gdd_merge の _register を使う） |
| N7 | 独立-3 | advisory | no | inherited | product | accepted | cd を外した同じ merge（marker のある root の素通りの exit）は台帳を見ずに通る。既存の境界として PR 本文に列挙 |
| N8 | 独立-3 | advisory | no | self-inflicted | product | accepted | root checkout の 3 件が台帳照合の後も通るかが未確認。今の台帳（旧#1191 だけ）では 3 件とも miss で通ることを PR 本文に書いた |
