---
lane: L1
pr: 632
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | bce3772b744767f29f62b1946c8c01c04654a6ea | 0 | 2 | 0 | 2026-11-02 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8081f900e240b39e1fc2a55db1037f26862141c4 | 0 | 3 | 0 | 2026-11-02 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の案は Task Size で絞っていないのに、quick (express) を確認なしに照合の対象から外していた。express でも requirements.md だけを渡して照合する。commit: 561bb063ca5c7b5c4b7aef22ec334c34e61b43a8 |
| I1-2 | 独立-1 | medium | no | self-inflicted | wiring | accepted | 定義を読み込む前のセッションと Codex・Cursor で、Step 4a から照合を起動する経路が無く unavailable に落ちる |
| I1-3 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 再入で処置した節の外に当たる ng を後回しにして、reviewer の前に写していなかった。全部を reviewer の前に反映し、処置に 照合-<n> の項目として追記する。commit: 561bb063ca5c7b5c4b7aef22ec334c34e61b43a8 |
| I1-4 | 独立-1 | low | no | self-inflicted | request-scope | fixed | PR 本文の目標と測り方が、案の「初稿の事実の誤り」と 4 つの計測から替わっていた。PR 本文と notes を案に合わせた。commit: なし（PR 本文） |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | Step 17 は照合を Step 4a が行うと言い切るが、express は照合しなかった。旧#1 で express も照合するので解消。commit: 561bb063ca5c7b5c4b7aef22ec334c34e61b43a8 |
| I1-6 | 独立-1 | low | no | self-inflicted | symmetry | accepted | 照合は名前で免除しているので、model=haiku を明示しても hook が警告しない |
| I1-7 | 独立-1 | low | no | self-inflicted | path | accepted | 相対パスの決めが根拠の列だけで、ほかの列に絶対パスを書くと steering の書き込みの検査が止める（止まる側） |
| I1-8 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 照合: の行に所要時間の欄が無い |
| I1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 再入で反映しても処置の記録が古いまま。旧#3 の直しで、反映ごとに処置へ追記する。commit: 561bb063ca5c7b5c4b7aef22ec334c34e61b43a8 |
| I1-10 | 独立-1 | low | no | self-inflicted | timeout | accepted | 照合に時間の上限が無い |
| I1-11 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | human check をまたいで Round を数え直すと precheck-round-1.md を上書きする |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 再生の結果を 3 か所で違う言い方で書いている |
| I1-13 | 独立-1 | low | no | self-inflicted | test-power | accepted | frontmatter の model: sonnet を固定するテストが無い |
| I1-14 | 独立-1 | low | no | self-inflicted | same-rule-elsewhere | accepted | is_exempt_from_phase_model_check の docstring に照合が無い |
| I1-15 | 独立-1 | low | no | self-inflicted | same-rule-elsewhere | accepted | README の agents/ の列挙に照合の agent が無い |
| I1-16 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片に Codex・Cursor の経路と再入の反映の範囲が無い |
| I1-17 | 独立-1 | advisory | no | self-inflicted | ordering | accepted | lint と Step 4a の反映の順が書かれていない |
| I1-18 | 独立-1 | advisory | no | self-inflicted | closed-values | accepted | 判定の値が ng・ok だけで、該当なし・要実行の扱いが閉じていない |
| I1-19 | 独立-1 | advisory | no | self-inflicted | isolation | accepted | reviewer が Glob で review-input/ の照合の表を読める |
| I2-1 | 独立-2 | medium | no | self-inflicted | same-rule-elsewhere | accepted | 再入で照合の ng を全部反映する規定が、同じファイルの契約 3（再入の前の処置は blocking だけ）と処置の書き手の規定と食い違う。PR 本文の限界に書いた |
| I2-2 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化が express では起動しないのまま。commit: なし（PR 本文） |
| I2-3 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | PR 本文の再入の反映の範囲が直す前のまま。commit: なし（PR 本文） |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | agent の description と example が design.md を渡す前提のまま |
| I2-5 | 独立-2 | low | no | self-inflicted | ordering | accepted | 照合が design.md を変えても、Step 3 で選んだ reviewer を選び直さない |
| I2-6 | 独立-2 | low | no | self-inflicted | ordering | accepted | 照合の処置の追記の後に lint を回し直す規定が無い |
| I2-7 | 独立-2 | low | no | self-inflicted | same-rule-elsewhere | accepted | 再入の 1 枚と planning reviewer の定義に 照合-<n> の処置の扱いが無い |
| I2-8 | 独立-2 | low | no | self-inflicted | timeout | re-reported | 照合に時間の上限が無い（I1-10 の再掲） |
| I2-9 | 独立-2 | advisory | no | self-inflicted | measurement | accepted | 照合の反映が作った blocking が処置の作ったものに混ざる |
| I2-10 | 独立-2 | low | no | self-inflicted | same-rule-elsewhere | re-reported | README の agents/ に照合の agent が無い（I1-15 の再掲） |
| I2-11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Affected Files にテスト 3 本が無い |
| I2-12 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | fixed-models の誤った ng 0 件が初回だけの数か読めない |
