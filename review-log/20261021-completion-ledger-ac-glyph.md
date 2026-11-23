---
lane: L1+
pr: 559
follow_up_of: 556
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 5d52d105 | 0 | 1 | 0 | 2026-10-21 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ac70d14a | 2 | 0 | 2 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 4d85e852 | 2 | 0 | 2 | 2026-10-21 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 4d85e852 | 0 | 1 | 0 | 2026-10-21 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8f96a953 | 2 | 1 | 2 | 2026-10-21 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 8f96a953 | 0 | 1 | 0 | 2026-10-21 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | e6c64d36 | 0 | 1 | 0 | 2026-10-21 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | f9db0529 | 1 | 0 | 1 | 2026-10-21 |
| 方針メモ-4 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | f9db0529 | 0 | 1 | 0 | 2026-10-21 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 99890af8 | 0 | 0 | 0 | 2026-10-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | medium | no | self-inflicted | fail-open | fixed | 字形の判定を AC_ID_RE（Unicode の \b・大文字固定）ではなく NFKC＋IGNORECASE＋ASCII の前方だけの正規表現にし、ループの頭で 1 回だけ計算して、読み飛ばす分岐（`>`・`#`、AC ID の見出し、区切りの直前、別の表の行）をすべて字形が無いときだけ通す（Opus・Fable が一致。`AC-1は`・`AC-2a`・`ac-1` が草案の定義では当たらない）。commit: 8ad9473b |
| K1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 字形を含む見出しの形の行の後も前の Ledger の見出しが残り、別の表の行を Ledger の行として読む（completion_trace.py:256）。退行。commit: 8bc5c6b6 |
| K2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | NFKC の後に前の境界を見るので `①AC-1`・`™AC-1` を字形と見ない（completion_trace.py:205）。commit: 8bc5c6b6 |
| K3 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 確認待ち: Ledger の節の中の fence の行は、字形を含んでも読み飛ばす（strip_fenced_blocks）。依頼の線に入るかをユーザーに確かめる |
| K4 | 独立-1 | low | no | self-inflicted | test-power | accepted | 見出しの形の行のテストが exit 1 だけを見る。前の境界の変異を固定するテストが無い（後者は K2 のテストで足した） |
| K5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | SKILL.md:54 の ac-source の括弧に、字形を含む注記・見出し・別の表の行が無い |
| K6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | テストのコメント（:593・:618）が字形の条件と合わない |
| K7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の行き先・列挙・範囲の書き方が実装と合わない |
| K8 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | PR 本文の実データの件数にコマンドと、字形の条件に当たった行の件数が無い |
| K9 | 独立-1 | advisory | no | self-inflicted | product | accepted | Ledger の行のほかの欄にある別の AC の字形は見ない |
| K10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 全差分巡の base が 旧#556 の branch の tip（merge-base ではない）。旧#556 のマージ後に main の上で変更行を突き合わせる |
| M1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 前の境界のせいで `①AC-１`・`①ＡＣ-1`・`TaskAC-1` を字形と見ない（completion_trace.py:202）。方針メモ-1 で (a) 相当: 境界を外して依頼の定義（NFKC で正規化した形）に戻した。入力者の transcript は未測。commit: dac85ec9 |
| M2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 1 行に AC_ID_RE で拾える AC と字形でしか拾えない AC（`AC-2は`）が並ぶと後者が gate に返らない（completion_trace.py:264-269）。requirements.md の AC を消した残りに字形があれば gate に返す。commit: dac85ec9 |
| M3 | 独立-2 | low | no | self-inflicted | test-power | accepted | `_has_ac_glyph` の `ac_id_re.search(line)` を固定するテストが無い |
| M4 | 独立-2 | low | no | self-inflicted | test-power | accepted | Ledger の行を読む条件の `not header_like` を固定するテストが無い |
| M5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | ledger_errors の docstring が判定とずれる |
| M6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片が挙動に追随していない |
| M7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 実データの件数にコマンドと起点が無い |
| M8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 限界の `リスクが低い` に件数も「未測」も無い |
| M9 | 独立-2 | advisory | no | self-inflicted | style | accepted | テスト名 test_ledger_row_before_separator_is_read が挙動と合わない |
| M10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | SKILL.md の ac-source の例が gate に返る行より狭い |
| pm-2 | 方針メモ-1 | medium | no | self-inflicted | fail-open | accepted | 安全策 4 の 1 回目の発火（fail-open の high を含む巡が独立-1・2）。Opus・Fable とも続行を推奨し、推奨で進めた。M1 は 2 本とも境界を外す案、M2 は Opus 案（AC を消した残りに字形が残るか。Fable は抽出 1 本の案）を採った（`AC-12`・`AC-3-d` を抜き出しで崩さない）。返事が「止める」なら 4d85e852 まで戻す。PR 本文に問いを書く |
| N1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 列挙: Ledger の行として読めた行は、ほかの欄の別の AC の字形（`-> AC-2 1 failed`）を見ない（completion_trace.py:259-263）。この PR の前からある。安全策 4 で止めた後、ユーザーの「559で続行」で、Ledger の節を許可リストで読む形に反転して閉じた。commit: f9db0529 |
| N2 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 列挙: `_AC_GLYPH_RE` が `re.ASCII` で、ASCII でない数字（`AC-١は`・`TaskAC-١`）を字形と見ない（completion_trace.py:202）。安全策 4 で止めた後、ユーザーの「559で続行」で、Ledger の節を許可リストで読む形に反転して閉じた。commit: f9db0529 |
| N3 | 独立-3 | medium | no | self-inflicted | test-power | accepted | `(not named and header is not None)` の項を固定するテストが無い。安全策 4 で止めた。直さず限界の節に書く |
| N4 | 独立-3 | low | no | self-inflicted | test-power | accepted | 1 行に並ぶ AC のテストが、どの行が gate に返ったかを見ない。安全策 4 で止めた。直さず限界の節に書く |
| N5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | docstring の「その AC を読めない」と「読めない行」が排他に読める。安全策 4 で止めた。直さず限界の節に書く |
| N6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「1 回だけ判定」が残りへの再判定と合わない。安全策 4 で止めた。直さず限界の節に書く |
| N7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片が境界なしの字形と 1 行に並ぶ AC を書いていない。安全策 4 で止めた。直さず限界の節に書く |
| N8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | SKILL.md:54 の ac-source の列挙が実装より狭い。安全策 4 で止めた。直さず限界の節に書く |
| N9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 実データの件数を測った時点とコマンドが読めない。安全策 4 で止めた。直さず限界の節に書く |
| N10 | 独立-3 | low | no | self-inflicted | product | accepted | NFKC の後の大文字化で ASCII になる字（`ı`）を字形と見ない。安全策 4 で止めた。直さず限界の節に書く |
| N11 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 限界の「字形に当たらない書き方は読み飛ばす」が範囲を言い過ぎている（Ledger の表の中は gate に返る）。安全策 4 で止めた。直さず限界の節に書く |
| pm-3 | 方針メモ-2 | medium | no | self-inflicted | fail-open | accepted | 安全策 4 の 2 回目の発火（fail-open の high を含む巡が独立-1・2・3）と巡の上限。規則どおり止めて PR を作り返事を待つ。Opus・Fable とも次の一手は、読む側の既定を反転して Ledger の節を許可リストで閉じ、字形の判定を撤去する案（Opus は書く側の書式の変更を、反転で正当な行が gate に返る件数を測ってからにする） |
| pm-4 | 方針メモ-3 | medium | no | self-inflicted | fail-open | fixed | ユーザーが「559で続行」と指示（.request.md）。Ledger の節を許可リストで読む形に反転し、字形の判定と AC ごとの読めない印を撤去する。Opus・Fable とも同じ推奨で、見出しを「区切りが続き AC ID が無い行」に絞る、ほかの欄の別の AC は境界なしの AC ID の式で探す、欄が欠けた見出しの下の行は見出しの不備で止める、期待が変わるテストを列挙する、を足した。実データ 5 件で前後とも ok 2・ac-source 2。commit: f9db0529 |
| H-1 | 独立-4 | high | yes | self-inflicted | fail-open | accepted | 列挙でなく構造: Ledger の節の中の閉じた fence は strip_fenced_blocks で落ち、許可リストの判定に届かない。fence の中の failed を読まずに ok を返す（completion_trace.py:223）。安全策 4 の 3 回目の発火で止めた。直さず限界の節に書く |
| L-1 | 独立-4 | low | no | self-inflicted | product | accepted | ほかの欄の別の AC の判定は lint-ac の文法（ASCII・大文字）だけで、全角・小文字・別のハイフンは通る。安全策 4 で止めた。直さず限界の節に書く |
| L-2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | SKILL.md:54 の ac-source の列挙に欄の数が合わない行などが無い。安全策 4 で止めた |
| L-3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 旧#556 の断片 :9 が撤去した ac-ledger invalid の挙動を書いたまま。安全策 4 で止めた |
| L-4 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 欄の中の縦棒を逃がしに直す append-only の例外が PR 本文と断片に無く、「ok には戻らない」と食い違う。安全策 4 で止めた |
| L-5 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 注記の置き場所の「worklog.md の退避の節」が定義されていない。安全策 4 で止めた |
| L-6 | 独立-4 | low | no | inherited | product | accepted | 欄が欠けた AC ID の表は ac-ledger invalid で、append-only の下で解消の手順が無い。安全策 4 で止めた |
| L-7 | 独立-4 | low | no | inherited | doc-claim | accepted | check-completion-mechanical.py 先頭の行の意味に、Ledger の読めない行による ac-source が無い。安全策 4 で止めた |
| L-8 | 独立-4 | low | no | self-inflicted | style | accepted | lint-ac.py の private 名 _AC_ID_CORE を外から使う。安全策 4 で止めた |
| L-9 | 独立-4 | low | no | self-inflicted | style | accepted | テスト名 `_is_read`・変数名 `bad`・N1/N2 のラベルが挙動と合わない。安全策 4 で止めた |
| L-10 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | PR 本文の実データの件数に測ったコマンドと止まった不備の件数が無い。安全策 4 で止めた |
| A-1 | 独立-4 | advisory | no | self-inflicted | product | accepted | 確認待ち: 旧#556 で承認した許可リストから注記・見出しを外した根拠は「559で続行」の計画への承認だけ。PR 本文の限界の節に問いとして書く |
| pm-5 | 方針メモ-4 | medium | no | self-inflicted | fail-open | accepted | 2026-10-22 にユーザーが続行を選んだ（Opus の形で 1 commit、差分巡の 2 回目で確かめる。.request.md）。安全策 4 の 3 回目の発火（独立-4 の H-1）。規則どおり止めて PR 本文を更新し返事を待つ。Opus・Fable とも推奨は続行（fence を読めない行にする 1 commit と差分（無効化後）の 2 回目）。割れた点は実装の形で、Opus は閉じた fence の行を印つきの行に置き換えてから今の正規表現で節を切る、Fable は fence の走査の行番号で節を切る |
| O-1 | 独立-5 | low | no | self-inflicted | request-drift | accepted | 確認待ち: 依頼は「1 commit」だが、テスト（f1e08233）と実装（99890af8）の 2 commit になっている。TDD の手順（テストを先に commit）によるもの。PR 本文の限界の節に問いを書く |
| O-2 | 独立-5 | low | no | self-inflicted | test-power | accepted | fence の中の `#` で節を閉じないテストが、CLI の出力からは節が閉じた場合と区別できない |
| O-3 | 独立-5 | low | no | self-inflicted | test-power | accepted | _mark_fenced_blocks が _scan_fences を直接呼び、strip_fenced_blocks との一致を固定するテストが無い |
| O-4 | 独立-5 | low | no | self-inflicted | product | accepted | 節の中の fence は 1 行ごとに ac-source の行になり、長い fence で出力が膨らむ |
| O-5 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文の実データの件数にコマンド・測った tip・fence の件数が無い。commit: なし（PR 本文） |
| O-6 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化に fence が無い。commit: なし（PR 本文） |
| O-7 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 断片の「これまで読み飛ばしていた…」に fence が無い |
| O-8 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「欄が欠けた見出しの下の行は読めない行に数えない」が実装より広い。commit: なし（PR 本文） |
| O-9 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | テストのコメントが撤去した NFKC・字形の判定を根拠に書いている |
| O-A | 独立-5 | advisory | no | self-inflicted | product | accepted | 閉じていない fence の扱い（節より前で開いた fence の後の行は読む）が限界の節に無い |
| O-B | 独立-5 | advisory | no | inherited | product | accepted | 節より前で閉じていない fence の後に記入例の Ledger を置くと ok になりうる（strip_fenced_blocks と同じ救済） |
| O-C | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | SKILL.md:54 の括弧の列挙が gate に返す行を全部は挙げていない |
