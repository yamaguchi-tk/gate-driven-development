---
lane: L1+
pr: 486
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 8b527358 | 0 | 0 | 0 | 2026-10-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4f93cf53 | 2 | 0 | 2 | 2026-10-14 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 4f93cf53 | 0 | 0 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | f8b74fc5 | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | advisory | no | inherited | design | accepted | 採用: Opus の推奨（案 1 を硬くしたもの＋清掃）。setup-gdd-loop.sh だけを変え、project_root: を frontmatter に JSON 文字列で書き、確かに不一致と言えるときだけロックを外す。案 2（stop hook の fallback の active 判定も変える）と案 3（root で marker を書かない）は採らない。ユーザーが Fable の意見を求め、Fable も案 1 を推奨。Fable の条件（frontmatter が見つからないときも止める）を足し、active:・session_id: の読み方は変えない形にした。ユーザーが案 1 を選んだ |
| I1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: hardlink の写しの marker で写しと判定し、cat > が持ち主の marker を書き換える。方針メモ-1 で F2 の許可リストに st_nlink == 1 を含めて閉じた（単独では事故の形 0 件で (b) が既定。誤 block 0/93） commit: 8b3ee7c4 |
| I1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 記録値が今の toplevel と文字列で違うだけでロックを外す（git worktree move の後の旧パス、同じ checkout を別の文字列で指す値、相対パス）。方針メモ-1 で (a): 絶対パス・実在するディレクトリ・今の toplevel と別の st_dev/st_ino の全部を満たすときだけ写しとする許可リストにした。事故の形 git worktree move は transcript に 1 件、実データの写しの誤 block 見込み 0 commit: 8b3ee7c4 |
| I1-3 | 独立-1 | low | no | self-inflicted | product | accepted | toplevel が UTF-8 で読めないと text=True の decode で setup 全体が落ちる（止める側に倒れる） |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | commands/gdd-dev.md:73 の手動のフォールバックが写しの例外を知らず、project_root: も書かない |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | TROUBLESHOOTING.md の原因と抜け方に、写された state の場合が無い |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が、持ち主が root で動いている写しの扱いを書いていない |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ロックのメッセージと gdd-pr-review-followup の (v) が project_root の書き換えを禁じていない |
| I1-8 | 独立-1 | low | no | self-inflicted | test-power | accepted | stderr の Recorded project_root をテストが固定していない |
| I1-9 | 独立-1 | low | no | self-inflicted | product | fixed | 依頼の「複製の主体を確かめた後」を、ユーザーの確認なしに限界にした。案 1 を選ぶ直前に示した複製の主体の事実（Claude desktop と推定、GDD から止められない）を request.md に引用で足した commit: 7a0bf4a6 |
| I1-10 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | PR 本文の目的に、件数を数えたコマンドが無い commit: なし（PR 本文） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | product | accepted | active:・session_id: を frontmatter に限らない読み方は依頼からの外れではない。理由を PR 本文に 1 行添えるとよい |
| I1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「ほかの block hook は写された state では止めない」が、session を見ない 2 つの読み手（stop hook の fallback、root-branch guard）を含めて広く読める |
| I1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の条件が「改行で終わる」「JSON 文字列」でコードより狭い commit: 8b3ee7c4 |
| I1-14 | 独立-1 | advisory | no | self-inflicted | product | accepted | project_root の行の数え方が parse_state（strip して key を取る）と違う。ほぼロックに倒れる |
| I1-15 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | symlink の 2 条件と realpath の条件が互いの代わりになっていることを書いていない |
| I1-16 | 独立-1 | advisory | no | self-inflicted | style | accepted | stderr の記録値が ensure_ascii で日本語のパスが読みにくい |
| I1-17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | SECURITY.md に、marker が toplevel の絶対パスを持つことが無い |
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | design | accepted | 採用: Opus の推奨。I1-2 は (a) の許可リスト（絶対パス・実在するディレクトリ・別の st_dev/st_ino・stat の失敗はロック）。I1-1 は単独では事故の形 0 件で (b) が既定だが、同じ許可リストの写しの定義に st_nlink == 1 を含めて閉じる（main の既定は (b) だったが、1 行で誤 block 0/93、(b) だと merge-ready にできないので Opus の案を採った）。残る形: 旧パスに別のディレクトリを作り直したとき、inode を保たないネットワーク FS、.claude/ だけの bind mount（入力者: 未測） |
| I2-1 | 独立-2 | low | no | self-inflicted | test-power | accepted | 相対パスの値 "." と "sub" では isabs の判定を消しても落ちない（".." なら落ちる） |
| I2-2 | 独立-2 | low | no | self-inflicted | product | accepted | 案 1 の「一致しないときだけ外す」に、絶対パス・実在・別の実体・hardlink でないの条件を足した。依頼から外れた指摘なので、ユーザーに確かめ「残す」を request.md に足した |
| I2-3 | 独立-2 | low | no | inherited | product | accepted | 案 1 の「parser を frontmatter だけ」を project_root: だけに当てた。依頼から外れた可能性の指摘なので、ユーザーに確かめ「今のまま」を request.md に足した。限界の節に書く |
| I2-4 | 独立-2 | low | no | self-inflicted | product | fixed | 写しが hardlink で作られると st_nlink の条件でロックが外れない。写しの nlink を測っていない。marker 93 個で st_nlink>1 は 0、写しと root は別 inode の実測を PR 本文に書いた commit: なし（PR 本文） |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「改行を含む」「改行で終わる」が、コードの改行か CR を含むより狭い commit: なし（PR 本文） |
| I2-6 | 独立-2 | low | no | inherited | bookkeeping | accepted | 断片の Affected Files にテストのファイルが無い |
| I2-7 | 独立-2 | low | no | inherited | product | accepted | toplevel が UTF-8 で読めないと setup 全体が落ちる（I1-3 と同じ） |
| I2-8 | 独立-2 | low | no | inherited | doc-claim | accepted | TROUBLESHOOTING.md に写された state の場合が無い（I1-5 と同じ） |
| I2-9 | 独立-2 | advisory | no | inherited | product | accepted | 深く入れ子の値で json.loads が RecursionError を出し、setup が落ちる（止める側。作らないと出ない） |
| I2-10 | 独立-2 | advisory | no | inherited | product | accepted | ロックのメッセージが project_root の書き換えを禁じていない（I1-7 と同じ） |
| I2-11 | 独立-2 | advisory | no | inherited | doc-claim | accepted | テストの冒頭の説明に、足した条件が無い |
| I2-12 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | commit の件名に巡の ID があった。push 前に件名を変えた（review-log だけの commit で、tree はレビューした bd2677ae と同じ） commit: f8b74fc5 |
