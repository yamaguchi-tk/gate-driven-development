---
lane: L1
pr: 286
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e85a3ce99d762b709a63723f6a5d01adfc37aeeb | 1 | 6 | 1 | 2026-10-02T10:15+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 41a4ce65639935126e36b18508b0b4787822ec01 | 1 | 0 | 1 | 2026-10-02T10:50+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | c7a2222620beca3bc2a99d4f6b75a456591c4caa | 2 | 0 | 2 | 2026-10-02T11:20+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | bd7c4e846e2b33b604ff2d6f341c72dcfae185ef | 0 | 0 | 0 | 2026-10-02T11:30+09:00 |
| 独立-5 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | f777438e57faf6a7e906ec100d2488218dec0115 | 0 | 0 | 0 | 2026-10-02T12:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| R1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | blocking の条件に § 常時 High・実害クラス・security の除外が無く、再現できない High が advisory に落ちて gate を通る。除外を正本と両 agent 定義に足した commit: 48121d75 |
| R2 | 独立-1 | medium | no | self-inflicted | product | fixed | reviewer に worktree の root が届かず、1 枚・参照・変更ファイルを解決できない。1 枚の絶対パスと `## Worktree` を渡し、先頭に `- Worktree:` 行を置く commit: 48121d75 |
| R3 | 独立-1 | medium | no | self-inflicted | product | fixed | requirements の初回の 1 枚に承認ポイント・スコープ・非スコープ・段階計画が入らない。初回の (1) を差し替えた commit: 48121d75 |
| R4 | 独立-1 | medium | no | self-inflicted | product | fixed | implementation の 1 枚に承認時点の Honest Limitations と Approved Direction が無い。(4) を足した commit: 48121d75 |
| R5 | 独立-1 | medium | no | self-inflicted | product | fixed | planning reviewer の読む範囲が正本より狭く、実コード・reviews.md を読むレーンと矛盾する。否定形に揃えた commit: 48121d75 |
| R6 | 独立-1 | medium | no | self-inflicted | product | fixed | implementation reviewer の読む範囲が Review Focus 1・2 の呼び出し側と矛盾する。呼び出し側と対の実装を足した commit: 48121d75 |
| R7 | 独立-1 | medium | no | self-inflicted | product | fixed | 時間切れの一括提示で、レビュー不成立を HITL で知らせる規定が無い。Human Check Questions への記載と SKILL の例外を足した commit: 48121d75 |
| R8 | 独立-1 | low | no | self-inflicted | product | fixed | gdd-requesting-code-review からの起動でも新しい読む範囲がかかる。1 枚を渡されない起動は従来どおりにした commit: 48121d75 |
| R9 | 独立-1 | low | no | self-inflicted | product | fixed | 時間切れで Gate Rounds を進める規定が既存の +1 の定義と食い違う。進めないことにした commit: 48121d75 |
| R10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | design gate に Round のカウンタが無いのに Round を進めると書いていた。design の (1) を決め、Round を進めない commit: 48121d75 |
| R11 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | `判定: timeout` が reviews.md の書式の列挙に無い。列挙に足した commit: 48121d75 |
| R12 | 独立-1 | low | no | self-inflicted | test-power | fixed | 受入条件の節の欠落のテストが別の ERROR で通る。AC を引用しない入力にした commit: 8e522ede |
| R13 | 独立-1 | low | no | self-inflicted | test-power | fixed | AC を 1 つだけ含む行だけを比べる規則が未テスト。AC を 2 つ含む行のテストを足した commit: 8e522ede |
| R14 | 独立-1 | low | no | self-inflicted | product | fixed | 節の分割がコード fence を考慮せず lint-ac.py と受理集合がずれる。fence の中を外した commit: 1d8e2214 |
| R15 | 独立-1 | low | no | self-inflicted | product | fixed | 数値の WARN が段階計画の見積もり行数や分割を拾う。表の行と分割を外した commit: 1d8e2214 |
| R16 | 独立-1 | low | no | self-inflicted | product | fixed | 機械検査の行が WARN のときしか無く、未実行と pass を区別できない。必ず 1 行書き、無ければ reviewer が突合する commit: 48121d75 |
| R17 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | requirements-gating SKILL の手順の概要が新しい節を参照していない。参照を足した commit: 48121d75 |
| R18 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | implementation-gating Step 4 の起動の文が Step 7 の escalation と食い違う。Step 7 に移した commit: 48121d75 |
| R19 | 独立-1 | low | no | self-inflicted | product | fixed | 参照に plugin の reference を絶対パスで書くと steering write guard に止められる。`${CLAUDE_PLUGIN_ROOT}` で書くと決めた commit: 48121d75 |
| R20 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | reviewer-common.md の出力書式に failure scenario が無い。impact の行に足した commit: 48121d75 |
| R21 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が Plan mode の行の削除と design-gating 冒頭の書き換えを書き漏らしている。Changed に足した commit: 48121d75 |
| R22 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 新しく止まる条件ができたのに User Action Required が「なし」。止まる条件と再開の仕方を書いた commit: 48121d75 |
| R23 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 「複製しない」の文が agent 定義の言い換えと合わない。「要点だけ書き、範囲は一致させる」に改めた commit: 48121d75 |
| R24 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に受入条件の節の欠落の ERROR が無い。commit: なし（PR 本文） |
| R25 | 独立-1 | advisory | no | self-inflicted | product | accepted | 30 分・20 分の上限に実測の根拠が無い。PR 本文の限界に書く |
| R26 | 独立-1 | advisory | no | self-inflicted | product | fixed | 返ったときの所要時間を記録しない。reviews.md の Round（implementation は Attempts）に書くことにした commit: 48121d75 |
| R27 | 独立-1 | advisory | no | self-inflicted | product | fixed | 1 枚が 200 行を超えたときの扱いが無く、受入条件を 2 回写す。初回の (1) から受入条件を外し、超えたら参照に回す commit: 48121d75 |
| R28 | 独立-1 | advisory | no | self-inflicted | product | fixed | lint の exit 2 と ERROR 行の無い exit 1 の扱いが無い。起動を止めて worklog に書く commit: 48121d75 |
| R29 | 独立-1 | advisory | no | self-inflicted | product | accepted | design.md の対応表を `- AC-1: <テスト名>` の形で書くと再定義の ERROR になる。実データの件数は未確認。PR 本文の限界に書く |
| S1 | 独立-2 | high | yes | self-inflicted | fence-parsing | fixed | 閉じ忘れの fence から後ろを読み飛ばし、再定義と未定義の引用の ERROR が消える。fence 走査を tasklist_parse._scan_fences に揃えた commit: 8876dd7b |
| S2 | 独立-2 | medium | no | self-inflicted | product | next-pr | reviewer が `${CLAUDE_PLUGIN_ROOT}` を解決できない。prompt に `## Plugin Root` を足す |
| S3 | 独立-2 | medium | no | self-inflicted | product | next-pr | requirements の初回の 1 枚からリスク・実装方針・影響範囲が落ちた |
| S4 | 独立-2 | medium | no | self-inflicted | product | next-pr | 時間超過の一括提示の選択肢が Steps 7 と食い違い、回答の扱いと status が決まっていない |
| S5 | 独立-2 | medium | no | self-inflicted | product | next-pr | lint のコマンドが相対パスで、worktree からは exit 2 になり reviewer を起動できない |
| S6 | 独立-2 | medium | no | self-inflicted | product | next-pr | failure scenario の必須化が Evidence Discipline・Uncertainty Rule と矛盾する |
| S7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「消費済み」と「Round を進めず」が食い違う |
| S8 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | 所要時間の書く欄・design の書き先・集める先が無い |
| S9 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 足したテストが外す向きしか固定していない（表以外の行・Summary の表の行） |
| S10 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | script の docstring が fence・表・分割の除外を書いていない |
| S11 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | implementation-gating Step 7 の参照が security reviewer にも上限を当てうる |
| S12 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | design-gating Step 9 の参照も security reviewer を含みうる |
| S13 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の「だけを読む」が reviewer-common と implementation の差分を書き漏らす |
| S14 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 機械検査の行があれば突合をやり直さない範囲が script の範囲より広い |
| S15 | 独立-2 | low | no | self-inflicted | product | next-pr | fence の中の AC 定義を lint-ac.py は数え、lint-plan-consistency は数えないので受理集合が割れる |
| S16 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | Worktree Binding Precheck の対象に reviewer が入るかが曖昧。PR 本文に列挙 |
| S17 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「他の絶対パスを書くと guard が止める」が実装より広い。PR 本文に列挙 |
| S18 | 独立-2 | advisory | no | self-inflicted | product | accepted | worktree のパスに空白があると 1 枚を書けない（止める側）。PR 本文に列挙 |
| S19 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 分割などを分として数えない変更が PR 本文と断片に無い。断片に足した commit: 8876dd7b |
| S20 | 独立-2 | advisory | no | self-inflicted | product | accepted | 「計れないとき」の経路を起動前に判定できない。PR 本文に列挙 |
| S21 | 独立-2 | advisory | no | self-inflicted | excerpt-contains-history | accepted | advisory: テンプレート外の記述あり（起動時の git status の commit 件名に巡の番号）。以後の commit の件名に巡の番号を書かない |
| T1 | 独立-3 | high | yes | self-inflicted | fence-parsing | fixed | 閉じ忘れの fence の後ろを検査に残すと、受入条件の節で記入例の `- AC-N:` を定義に数え、未定義の引用の ERROR が消える。閉じ忘れを ERROR にした commit: 6093393d |
| T2 | 独立-3 | high | yes | inherited | fence-parsing | accepted | steering write guard の `_advance_section_state`（validate-steering-write.py:616）が ``` の行ごとに反転するだけなので、4 連 fence の中の ```・`~~~` の中の ```・info に ` を含む行の後ろで、fence の外の `password:` などの値・AWS アカウント ID・placeholder を見逃して `.steering/` への書き込みを通す。差分は guard を変えていない。直すと L1+ になるので、限界の先頭に書き、直す次の PR（L1+）を出す（Fable 信号 ③ で相談し B を推奨） |
| T3 | 独立-3 | low | no | self-inflicted | test-power | next-pr | sys.path の巻き戻しの probe（test_sys_path_rollback_on_import_failure_contract.py の TARGETS）に lint-plan-consistency.py が無い |
| T4 | 独立-3 | low | no | self-inflicted | test-power | next-pr | fence の可視性を 1 か所で決める契約テストが `_scan_fences` から可視性を決める lint を拾わない |
| T5 | 独立-3 | low | no | self-inflicted | test-power | next-pr | ERROR・WARN の `line <n>` を assert するテストが無かった（閉じ忘れの ERROR では行番号を固定した） |
| T6 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片の Validation の列挙に、足した fence のテストが無い。列挙に足した commit: 6093393d |
| T7 | 独立-3 | low | no | inherited | doc-claim | next-pr | 手順の lint のコマンドが plugin root 無しの相対パスで、worktree からは exit 2 になる（独立-2 の S5 と同じ） |
| T8 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | unfenced_lines の docstring と断片が、閉じ忘れの扱いと閉じる条件を書いていない。docstring と断片を直した commit: 6093393d |
| U1 | 独立-4 | low | no | self-inflicted | product | next-pr | リスト記号と同じ行で開いた fence（`- ```bash`）は開きと数えず、閉じの行を閉じ忘れと誤 ERROR にする（repo 内の該当 0 件） |
| U2 | 独立-4 | low | no | inherited | test-power | next-pr | `~~~`・4 連 fence の中で閉じないテスト 2 本が、閉じ忘れの ERROR が出ないことを assert していない |
| U3 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 新しいテストの名前（例を定義に数えない）が挙動と逆で、固定しているのは閉じ忘れの ERROR だけ |
| U4 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | subagent-dispatch.md の検査一覧に、受入条件の節の欠落と閉じ忘れの fence の ERROR が無い |
| U5 | 独立-4 | low | no | inherited | product | re-reported | lint-ac.py と AC の定義集合が割れている（S15 の再掲） |
| U6 | 独立-4 | low | no | inherited | test-power | re-reported | fence の可視性の単一正本の契約が lint を拾わない（T4 の再掲） |
| U7 | 独立-4 | advisory | no | inherited | test-power | re-reported | sys.path の巻き戻しの probe の対象に lint が無い（T3 の再掲） |
| U8 | 独立-4 | advisory | no | self-inflicted | style | accepted | docstring の「main」が main session とも読める。PR 本文に列挙 |
| U9 | 独立-4 | advisory | no | self-inflicted | excerpt-contains-history | accepted | reviewer の Grep が review-log/ の行に当たり、前の巡の要約が見えた（reviewer は以降 review-log/ を除き、指摘は実コードから導いたと報告） |
| V1 | 独立-5 | medium | no | self-inflicted | product | re-reported | reviewer に plugin root が届かない（S2 の再掲） |
| V2 | 独立-5 | medium | no | self-inflicted | product | re-reported | 時間超過の一括提示の選択肢と回答の受け口・遷移表が噛み合わない（S4 の再掲） |
| V3 | 独立-5 | medium | no | self-inflicted | product | next-pr | 機械検査の行があると reviewer は突合をやめるが、script が見るのは Summary Brief・ISP・design.md だけ（HCQ などを見ない） |
| V4 | 独立-5 | medium | no | self-inflicted | product | re-reported | requirements の 1 枚に安全境界の節（リスクなど）が入らない（S3 の再掲） |
| V5 | 独立-5 | medium | no | self-inflicted | product | next-pr | 再現の確認と advisory への降格が、gate の分類 Step から参照されていない |
| V6 | 独立-5 | medium | no | self-inflicted | product | re-reported | 新しい降格が Evidence Discipline・既存の 1 段階降格と衝突する（S6 の再掲） |
| V7 | 独立-5 | low | no | self-inflicted | product | next-pr | 機械検査の後に requirements.md を削るので、OK が古くなる |
| V8 | 独立-5 | low | no | self-inflicted | doc-claim | re-reported | 「消費済み」と「Round を進めず」が食い違う（S7 の再掲） |
| V9 | 独立-5 | low | no | self-inflicted | bookkeeping | re-reported | 所要時間と再現できない理由の記録先に書式が無い（S8 の再掲） |
| V10 | 独立-5 | low | no | self-inflicted | product | re-reported | lint の起動コマンドが相対パスで exit 2 になる（S5 の再掲） |
| V11 | 独立-5 | low | no | self-inflicted | product | next-pr | design gate で承認済みの requirements.md 側に ERROR が出たときの扱いが無い |
| V12 | 独立-5 | low | no | self-inflicted | test-power | next-pr | 見出しの表記ゆれ（番号・強調・先頭空白）で Summary Brief・ISP が検査から外れる |
| V13 | 独立-5 | low | no | self-inflicted | doc-claim | re-reported | テスト名と挙動が逆（U3 の再掲） |
| V14 | 独立-5 | low | no | self-inflicted | bookkeeping | next-pr | 変更断片に、利用者から見えない整理（行のまとめ）を書いている |
| V15 | 独立-5 | advisory | no | self-inflicted | excerpt-contains-history | accepted | advisory: テンプレート外の記述あり（起動時の git status の commit 件名） |
| V16 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | レーンを L1 としたが、差分に判定のコード（scripts/）を含む。PR 本文に理由を書く |
| V17 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋に、exit 2 の扱い・選択肢・Human Recheck Boundary などが無い。PR 本文に列挙 |
| V18 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | guard が止める絶対パスの範囲の記述が実装より広い。PR 本文に列挙 |
| V19 | 独立-5 | advisory | no | self-inflicted | product | accepted | 1 枚の `- Worktree:` 行のローカルパスが対象 repo の履歴に残る。PR 本文に列挙 |
| V20 | 独立-5 | advisory | no | self-inflicted | test-power | accepted | 数値の WARN は同じ単位の値が 1 つ一致すると残りを見ない。PR 本文に列挙 |
| V21 | 独立-5 | advisory | no | self-inflicted | test-power | accepted | design.md の表の行で数値を比べることを固定するテストが無い。PR 本文に列挙 |
| V22 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | reviewer-common の出力書式が 2 つの reviewer だけの節を正本として指す。PR 本文に列挙 |
| V23 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | subagent-dispatch.md 冒頭の参照元が古い。PR 本文に列挙 |
| V24 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 空の受入条件の節が「節が無い」と出る。PR 本文に列挙 |
| V25 | 独立-5 | advisory | no | self-inflicted | product | accepted | subagent の中で background の reviewer を待つ方法が書かれていない。PR 本文に列挙 |
