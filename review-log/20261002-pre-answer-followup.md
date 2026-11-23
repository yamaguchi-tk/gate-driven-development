---
lane: L1
pr: 295
follow_up_of: 288
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e75703212851b3892b8ff2432c16b7258c173188 | 0 | 1 | 0 | 2026-10-02T14:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 6f236791133282e3e5d4bf5207bc5722b205b677 | 0 | 0 | 0 | 2026-10-02T15:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | lint は `## Approved Direction` の見出しの形から glob を読めず、glob の無い state.md を exit 0 にしたことで、Step 3c の「exit=0 + INFO のみ → 自走可」に入る。Step 3c で INFO を合格に数えず、自走範囲の glob を手で確かめるようにした（抽出の取りこぼし自体は直していない） commit: 6f236791 |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 未リリースの前の断片の「WARN が無ければ今までどおり exit 2」が偽になる。前の断片は書き換えず、新しい断片に置き換える旨を書いた commit: 6f236791 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 予算のコメントの前置き・結びが 2 つの ratchet のままで、旧#9 の説明が実際と違う commit: 6f236791 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が phase-progression.md の変更（例外を足した）を、確かめの条件を書いたと逆の向きに書いていた。別の項に分けた commit: 6f236791 |
| F5 | 独立-1 | low | no | self-inflicted | test-power | fixed | hook 入口のテストが hook の見出し文字列の不在だけを見ている。正規の記録では systemMessage のキー自体が無いことを見るようにした commit: 6f236791 |
| F6 | 独立-1 | low | no | inherited | doc-claim | fixed | gdd-next-plan の次 Stage の HITL before implementation に、事前回答の Stage の例外が無い commit: 6f236791 |
| F7 | 独立-1 | low | no | inherited | doc-claim | fixed | subagent-dispatch の Post-Return Routing に事前回答の分岐だけが入り、autonomy の分岐が無い。旧#9 と同じ順序に揃えた commit: 6f236791 |
| F8 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 確かめられないときの記録で、承認ポイントが複数あるときの対象の欄の値が決まらない |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 原文が触れていない欄の書き方が § 1 に無く、§ 2 の読み方と対になっていない |
| F10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Planning Interrupt Decision Menu の「項目 1 で扱う」が、§ 事前回答 3 の一覧のうち中止・作り直し（項目 4）に当たるものを含めていない |
| G1 | 独立-2 | low | no | self-inflicted | lint-output-contract | accepted | Step 3c の判定木から、`INFO: global glob` だけが出る場合（colon 形の state.md で全域 glob・security marker なし）の分岐が抜けた |
| G2 | 独立-2 | low | no | self-inflicted | test-power | accepted | 強めた hook 入口のテストが、環境変数 `GDD_STEERING_SIZE_DENY=0` を export した環境では DISABLED_NOTICE の systemMessage で誤って落ちる |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | Step 3c が正本として指す rollback-patterns.md § Approved Direction glob 粒度 guard に、INFO を合格に数えないことと見出しの形から抽出しないことが無い |
| G4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片と Step 3c の「見出しの形を読めない」は言い過ぎで、読めないのは glob の抽出だけ（evidence の検査は見出しの形を読む） |
| G5 | 独立-2 | advisory | no | inherited | product | accepted | 同じ Approved Direction の節を、evidence の検査と glob の抽出が違う受理集合で読む |
| G6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 予算のコメントの「origin/main tip で測った」は、3 つ目の ratchet についてはマージまで正しくない |
| G7 | 独立-2 | advisory | no | self-inflicted | style | accepted | subagent-dispatch.md:128 が事前回答の行の場所（worklog.md）を書いていない |
