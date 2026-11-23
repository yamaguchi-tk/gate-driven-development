---
lane: L1+
pr: 607
follow_up_of: 601
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 76defb8e | 0 | 0 | 0 | 2026-10-28 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 76e638ab | 2 | 6 | 2 | 2026-10-29 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 76e638ab | 0 | 0 | 0 | 2026-10-29 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 15418a80 | 0 | 2 | 0 | 2026-10-29 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c897d4af | 0 | 3 | 0 | 2026-10-29 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | 飛ばす条件 | accepted | 方針: 飛ばす条件は許可リスト（Opus）、文書の変化は hash（Fable）、stale tasklist は design-gating へ（Opus）、Inventory は skeleton（Opus）。確認は返事を待たずに推奨で進める |
| I1-1 | 独立-1 | high | yes | self-inflicted | 許可の寿命 | fixed | 列挙: 設計: 変える（許可を寿命の無い別の行に置き、初回かを Route In Progress で推し量った）差し戻しの後の再承認で design-gating を飛ばす。許可を Design Review Status の evidence の token に移し、遷移で消えるようにした。commit: b0454af8 |
| I1-2 | 独立-1 | high | yes | self-inflicted | hash の時点 | fixed | 列挙: 設計: 変える（hash を承認の直前に取った）reviewer が見ていない編集にも skip を与える。reviewer の起動の直前に snapshot で控え、承認の直前に confirm で照合する。commit: b0454af8 |
| I1-3 | 独立-1 | medium | no | self-inflicted | 飛ばす条件 | fixed | accept as known risk でも飛ばす。confirm を呼ぶ条件に blocking 無し・Round 上限からの合流でないを足した。commit: b0454af8 |
| I1-4 | 独立-1 | medium | no | self-inflicted | state.md の読み方 | fixed | = 形の state.md で書けない。script は書かなくなり、読みは state_field_pattern で両形を受ける。commit: b0454af8 |
| I1-5 | 独立-1 | medium | no | self-inflicted | skip の経路で抜ける手順 | accepted | dialectic の起動の手順が requirements-gating に無い |
| I1-6 | 独立-1 | medium | no | self-inflicted | skip の経路で抜ける手順 | accepted | 最新技術の再確認（design-gating Step 2）が抜ける |
| I1-7 | 独立-1 | medium | no | self-inflicted | 契約の文書 | accepted | self-contained-contract.md が必ず design-gating を通すと書いたまま |
| I1-8 | 独立-1 | medium | no | self-inflicted | route の呼び方 | fixed | STEP 2 の呼び方に引数が無く、出力が無いときの既定が無い。引数を書き、1 行目が gdd-task-breakdown のときだけ進むとした。import も try の中へ。commit: b0454af8 |
| I1-9 | 独立-1 | low | no | self-inflicted | 契約の文書 | accepted | 承認の後の順序を書いた別の reference が古い |
| I1-10 | 独立-1 | low | no | self-inflicted | 断片 | accepted | 断片の type が minor |
| I1-11 | 独立-1 | low | no | self-inflicted | 断片 | accepted | 断片が evals.json を挙げていない |
| I1-12 | 独立-1 | low | no | self-inflicted | PR 本文 | accepted | scorecard の母数の記述が実態と逆。PR 本文で直す |
| I1-13 | 独立-1 | low | no | self-inflicted | テスト | fixed | Task Size 無し・field の重複・= 形のテストが無い。足した。commit: 8c896b18 |
| I1-14 | 独立-1 | low | no | self-inflicted | state.md の読み方 | accepted | 飛ばすときの Design Review Status の行に updated_at が無い |
| I1-15 | 独立-1 | low | no | self-inflicted | state.md の読み方 | fixed | encoding の指定が無く、書き込みが atomic でない。script は書かなくなり、encoding を指定した。commit: b0454af8 |
| I1-16 | 独立-1 | low | no | self-inflicted | state.md の読み方 | accepted | Route In Progress を正本の reader と違う読み方で読む |
| I1-17 | 独立-1 | low | no | self-inflicted | 飛ばす条件 | accepted | Broad Requirement を明示の行だけで判定する |
| I1-18 | 独立-1 | low | no | self-inflicted | 依頼の範囲 | accepted | 確認待ち: Quick Standard Design Gate Optional と運用レベル light を対象外にした |
| I1-19 | 独立-1 | low | no | self-inflicted | 依頼の範囲 | accepted | 確認待ち: 分割で hook を含むとした PR-6 を hook なしで作った |
| I1-20 | 独立-1 | advisory | no | self-inflicted | 依頼の範囲 | accepted | 確認待ち: 数えずに出すことと、マージ後の 5 本で測る条件をユーザーが確かめていない |
| I1-21 | 独立-1 | advisory | no | self-inflicted | テスト | accepted | sys.path の挿入を戻さず、contract test も拾わない |
| M2-1 | 方針メモ-2 | advisory | no | self-inflicted | 許可の寿命 | accepted | 方針: (a)。Opus の案（許可を Design Review Status の evidence に入れる）を採り、Fable の案（Step 8 の形の全体を読む述語）はこれに含まれる。STEP 2 の呼び方は Fable の勧めで直した |
| I2-1 | 独立-2 | medium | no | self-inflicted | 依頼の範囲 | fixed | 設計: 変えない（hash を起動の前に取る決定は I1-2 の閉じ方で、変えると I1-2 が戻る）待ち時間の削減と承認待ちの advisory の反映で文書が変わり、通常の経路でも design-gating が残る。依頼から外れるので、削減を Step 4 の前、反映を承認の後に回した。commit: d60eb84e |
| I2-2 | 独立-2 | medium | no | inherited | 飛ばす条件 | accepted | timeout・Round 上限からの合流で token を出さない判定が Step 8 の散文だけ。confirm は hash しか見ない |
| I2-3 | 独立-2 | low | no | self-inflicted | 測り方 | accepted | confirm が none を返した理由が残らず、マージ後の分布で削減のせいかを区別できない |
| I2-4 | 独立-2 | low | no | self-inflicted | 契約の文書 | accepted | gate-status-schema.md の evidence の規定に token の形が無い |
| I2-5 | 独立-2 | low | no | self-inflicted | 契約の文書 | accepted | reviewer-selection.md の「通過の後に変えたら」が実際より狭い |
| I2-6 | 独立-2 | low | no | self-inflicted | 断片 | accepted | 断片の条件の文と Changed に Step 4 が無い |
| I2-7 | 独立-2 | low | no | inherited | route の呼び方 | accepted | Route In Progress の判定は呼び順で常に none を見る。差し戻しは evidence の書き換えで見分けている |
| I2-8 | 独立-2 | low | no | self-inflicted | route の呼び方 | accepted | STEP 2 の呼び方から scripts/ の前置きが落ちた（失敗すれば design-gating） |
| I3-1 | 独立-3 | medium | no | self-inflicted | advisory の反映 | accepted | 承認の後に回した advisory を反映する手順と担当が、承認の処理にも Task-Breakdown にも無い。飛ばす経路では落ちうる |
| I3-2 | 独立-3 | medium | no | self-inflicted | 依頼の範囲 | accepted | HITL draft の組み立て・Human Check Questions の集約・Spec Self-Review の修正も起動の後に文書を書き、token を消す |
| I3-3 | 独立-3 | medium | no | inherited | 依頼の範囲 | accepted | 確認待ち: 部分修正・timeout・再入の Round・手順上の書き込みでは、差し戻しでなくても design-gating に進む（依頼より狭い） |
| I3-4 | 独立-3 | low | no | self-inflicted | 手順の順序 | accepted | 削減を Step 4 の前にする指示が Step 5 の中にあり、読む時点が snapshot の後 |
| I3-5 | 独立-3 | low | no | self-inflicted | 手順の順序 | accepted | 組を起動しない Round でも削減が直列になる |
| I3-6 | 独立-3 | low | no | self-inflicted | PR 本文 | accepted | PR 本文の挙動の節の例が差分と食い違う。PR 本文で直す |
| I3-7 | 独立-3 | low | no | self-inflicted | 断片 | accepted | 断片に Step 6 と削減・反映の時機が無い |
| I3-8 | 独立-3 | low | no | self-inflicted | 契約の文書 | accepted | 契約 3 と amendment の advisory の時機に token の例外が無い |
| I3-9 | 独立-3 | low | no | inherited | 依頼の範囲 | accepted | 確認待ち: hook を含む PR-6 を hook なしで作った |
| I3-10 | 独立-3 | advisory | no | self-inflicted | 契約の文書 | accepted | Step 5 と Step 8 の基準の時点、token の語、挿入位置の文言のずれ |
