---
lane: L1
pr: 690
follow_up_of: 688
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a05dc2602e62e630c8a7bcd79fb42d6531c59add | 0 | 4 | 0 | 2026-11-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | a4b015790d5e00c94f8b00f9baeee9a6c1e4b904 | 0 | 1 | 0 | 2026-11-17 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の「一次表示の行と requirements.md の同じ行を突き合わせる」を、§ ズレ確認 の印の無い行を全部数える形に替えていた。一次表示の行ごとに、表の区切り・記号・空白・印を外して突き合わせ、一致して印の無い行と、同じ行が見つからない行を数える形にした。commit: c81f1df4 |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | accepted | Stop hook の systemMessage は利用者の画面にだけ出て main に届かないのに、知らせの文が main に向けて書かれている |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | accepted | 返事の後に background の通知で始まるターンの Stop でも、同じ返事を見直して知らせと記録を繰り返す |
| I1-4 | 独立-1 | medium | no | self-inflicted | product | accepted | 記録の粒度（Stop 1 回ごと、規定どおり印の無い行を含む数）では、撤去の条件を判定できない |
| I1-5 | 独立-1 | low | no | self-inflicted | product | accepted | compaction を見るのは一次表示と返事の間だけで、返事の後の compaction と、compaction の後に出し直した一次表示を扱わない |
| I1-6 | 独立-1 | low | no | self-inflicted | product | accepted | § ズレ確認 の見出しの読み方が緩く、`#` で始まる行・小見出し・語を足した見出しで行を落とす |
| I1-7 | 独立-1 | low | no | self-inflicted | product | accepted | display-marker.log を umask のまま開き、FIFO なら止まる。同じ state dir の request_diff の開き方と SECURITY.md の規定（600）に合わない |
| I1-8 | 独立-1 | low | no | self-inflicted | product | accepted | 記録の書き込みの OSError 以外の例外（surrogate・HOME 無し）で、知らせごと消える |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | hooks.json の description に 3 本目の Stop hook が無い |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | README の hook の表と SECURITY.md の読む入力・書く記録の表に、新しい hook が無い |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の記述が、通知のターンでの繰り返しと、知らせが利用者の画面にだけ出ることを書いていない |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「未測のまま足すことはユーザーが確かめた」の根拠が依頼の原文に無く、件数が目的の節に無い。PR 本文を直した |
| I1-13 | 独立-1 | low | no | self-inflicted | test-power | accepted | bind が解決したときの分岐、isCompactSummary の側を通るテストが無い。雛形の語だけを見る assert がある |
| I1-14 | 独立-1 | advisory | no | self-inflicted | style | accepted | transcript の読み込み・toplevel・steering の選び方を、既存の実装から写している |
| I1-15 | 独立-1 | advisory | no | self-inflicted | product | accepted | Stop のたびに transcript の全体を JSON として読む |
| I1-16 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストが存在しない環境変数 GDD_DISABLE_HOOKS を外している |
| I1-17 | 独立-1 | advisory | no | self-inflicted | product | accepted | 打ったコマンドや AskUserQuestion の答えも人の発言に数え、一次表示を探す範囲がずれる |
| I1-18 | 独立-1 | advisory | no | self-inflicted | product | accepted | bind が解決しないと最新の steering を読み、別のタスクの行を見うる |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | fixed | 撤去の条件が unmarked だけを読み、突き合わせに失敗した回（missing）を付け忘れなしに数える。PR 本文の条件を、missing が 0 の行で読む形に直した。commit: なし（PR 本文） |
| I2-2 | 独立-2 | low | no | self-inflicted | product | accepted | 一次表示の側は節を絞らず、説明文の行も数えて missing の知らせを出しうる |
| I2-3 | 独立-2 | low | no | self-inflicted | product | accepted | missing だけの知らせに、受け取った側が次にすることが書かれていない |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | human-check-template.md と入口のスクリプトの説明が、行ごとの突き合わせと見つからない行の知らせに追随していない |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | ログの missing が 0 以外になる場合を固定するテストが無い |
| I2-6 | 独立-2 | low | no | self-inflicted | test-power | accepted | 正規化で外す #・*・・ と、同じ key の行が複数あるときの扱いを通るテストが無い |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 正規化は行の中の記号と空白を全部外し、説明の「箇条の記号」より広い |
| I2-8 | 独立-2 | advisory | no | inherited | product | re-reported | systemMessage は利用者の画面にだけ出るが、文面は main に印を足すよう求めている（I1-2 と同じ） |
