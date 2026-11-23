---
lane: L1+
pr: 342
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (Plan, model: opus) + Fable (信号 ①, model: fable) + user | - | 0 | 0 | 0 | 2026-10-03T01:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 08c1e0865740cfd1d43fcf1f6e64fe092fb38106 | 4 | 3 | 4 | 2026-10-03T05:10+09:00 |
| 方針メモ-1 | Opus 設計レビュー (Plan, model: opus) | - | 0 | 0 | 0 | 2026-10-03T05:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c6c582ed782a5e5a61fb4f81cfd91a732c17ddcd | 1 | 1 | 1 | 2026-10-03T06:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (Plan, model: opus) + Fable (信号 ②, model: fable) | - | 0 | 0 | 0 | 2026-10-03T06:50+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | fa5c5617740771236eb77d02fc7be5a90bed4a99 | 0 | 0 | 0 | 2026-10-03T07:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | advisory | no | inherited | merge-wait-pushback | fixed | 「CI が通ったらマージします」で止まった 96 件のうち 33 件は待つ仕組みが無かった。user が「宣言ファイル＋『マージします』の検知」を選んだ（自由文の検知は 1 回の押し返しの発火だけに使う）。commit: (本 PR) |
| pm-2 | 方針メモ | advisory | no | inherited | human-check-pushback | fixed | 事前回答があるのに human-check-waiting で止まる停止を、`事前回答:` 行を読んで 1 回押し返す。GDD は継続の block を連鎖させるので、1 回目の判定は stop_hook_active ではなく sidecar の key で行う。commit: (本 PR) |
| H1 | 独立-1 | high | yes | self-inflicted | pushback-deadline | fixed | gh の timeout 20 秒が Stop hook の 10 秒を超え、done guard より前で kill されて停止が通る。判定全体を 3 秒の締め切りで打ち切り、gh は 2 秒にした。commit: 3f7ac488 |
| H2 | 独立-1 | high | yes | self-inflicted | pushback-deadline | fixed | 宣言・記録を exists/read_text で読み、FIFO で done guard より前に止まる。read_regular_bytes で読み、os.replace で書く（締め切りでも閉じる）。commit: 3f7ac488 |
| H3 | 独立-1 | high | yes | self-inflicted | pushback-output | fixed | 理由文の then を無害化せず、lone surrogate で出力時に例外になり hook 全体が抜ける。then に unsafe な文字があれば宣言を受けず、head は 16 進 40 桁だけ載せる。commit: 3f7ac488 |
| P1 | 独立-1 | high | yes | inherited | compact-record-fifo | accepted | 既存: .claude/gdd-compact-suggestions.json が FIFO だと溜めた block が書き出されない（閉じ方: 列挙）。方針メモ-1 で transcript の事故の形 0 件を確かめ、(b) として PR 本文の限界に書いた |
| M1 | 独立-1 | medium | no | self-inflicted | merge-intent-session | fixed | 宣言が session を持たず、同じ worktree の別セッションに届き key を消費する。宣言のパスを tool_use に持つセッションだけに押し返す。commit: 3f7ac488 |
| M2 | 独立-1 | medium | no | self-inflicted | merge-intent-ci | fixed | rollup が空（CI none）の指示が無い。pending として扱い、未登録を含むと書いた。commit: 3f7ac488 |
| M3 | 独立-1 | medium | no | self-inflicted | pushback-deadline | fixed | 押し返しが遅い・止まる・落ちるときに done guard が判定を出すかのテストが無い。遅い gh・FIFO 宣言・FIFO 記録のテストを足した。commit: 3f7ac488 |
| L1 | 独立-1 | low | no | self-inflicted | merge-promise | fixed | 約束の正規表現が過去形・依頼にも当たる。未来・意志の形に絞った。commit: 3f7ac488 |
| L2 | 独立-1 | low | no | self-inflicted | transcript-read | fixed | transcript を splitlines で分け、dict 以外の行で落ちる。split("\\n") にして dict 以外を読み飛ばす。commit: 3f7ac488 |
| L3 | 独立-1 | low | no | self-inflicted | fence | fixed | fence の判定を独自に持つ。strip_fenced_blocks を使う。commit: 3f7ac488 |
| L4 | 独立-1 | low | no | self-inflicted | bind | fixed | bind できないとき別タスクの worklog で押し返す。bind が resolved のときだけ読む。commit: 3f7ac488 |
| L5 | 独立-1 | low | no | self-inflicted | peer | fixed | 直前のターンが peer でも再開させる。peer なら押し返さない。commit: 3f7ac488 |
| L6 | 独立-1 | low | no | self-inflicted | pushback-errors | fixed | 失敗を黙って捨て、書きかけの記録が残りうる。append_hook_error に残し、一時ファイルと os.replace で書く。壊れた記録は今までどおり押し返さない側。commit: 3f7ac488 |
| L7 | 独立-1 | low | no | self-inflicted | doc | fixed | autonomy.md の「だけ」がマージ待ちの押し返しと食い違う。human check についての範囲に直した。commit: 3f7ac488 |
| L8 | 独立-1 | low | no | self-inflicted | doc | fixed | hooks.json の description に GDD の外での押し返しが無い。1 文足した。commit: 3f7ac488 |
| L9 | 独立-1 | low | no | self-inflicted | doc | fixed | 導入テンプレートの ignore のチェックリストに 2 ファイルが無い。足した。commit: 3f7ac488 |
| L10 | 独立-1 | low | no | self-inflicted | test-power | fixed | 読めない worklog のテストが分岐を通っていない。不正な UTF-8 にした。commit: 3f7ac488 |
| A1 | 独立-1 | advisory | no | self-inflicted | doc | fixed | changelog の User Action Required と「2 つ」の数。直した。commit: 3f7ac488 |
| A2 | 独立-1 | advisory | no | self-inflicted | merge-intent | accepted | 宣言の original を受理の条件にしていない。PR 本文に列挙 |
| A3 | 独立-1 | advisory | no | self-inflicted | merge-intent | accepted | 宣言は toplevel の .claude/ を見るが既存は cwd。PR 本文に列挙 |
| A4 | 独立-1 | advisory | no | self-inflicted | doc | accepted | followup の待ち方の規定に宣言が無い。PR 本文に列挙 |
| A5 | 独立-1 | advisory | no | self-inflicted | doc | fixed | PR 本文の「今までどおり止まる」が H1〜H3 で成り立たない。締め切りと gh を呼ぶ条件を PR 本文に書いた。commit: なし（PR 本文） |
| pm1-1 | 方針メモ-1 | advisory | no | inherited | compact-record-fifo | accepted | P1 の相談: transcript で gdd-compact-suggestions.json を tool_use で置き換えた形は 0 件、mkfifo 57 件はテストと MCP のパイプだけ。(b) を推奨、この PR では compact_suggestion.py を触らない |
| K1 | 独立-2 | high | yes | self-inflicted | pushback-deadline | fixed | run_within_deadline が Thread.start の RuntimeError を捕まえず、done guard より前で hook が exit 1 になる。境界を例外を出さない形にし、締め切りをプロセス全体で共有した。commit: f7579550 |
| K2 | 独立-2 | medium | no | self-inflicted | pushback-cost | fixed | peer の判定が候補の有無より前に transcript 全体を読む。候補が決まった後にだけ呼ぶ。commit: f7579550 |
| K3 | 独立-2 | low | no | self-inflicted | pushback-deadline | fixed | _EXPIRED が同じ実行の別の押し返しを止める。締め切りをプロセス全体の予算にしたので、過ぎた後は押し返さない（設計どおり）。commit: f7579550 |
| K4 | 独立-2 | low | no | self-inflicted | pushback-deadline | next-pr | 締め切りぎりぎりで押し返しを出さずに key だけが書かれうる |
| K5 | 独立-2 | low | no | self-inflicted | merge-intent-session | next-pr | 宣言を書いたセッションの判定が、行の文字列の近似（読んだだけ・文書の編集でも数える） |
| K6 | 独立-2 | low | no | self-inflicted | peer | next-pr | human check の押し返しには peer の判定が無い。PR 本文はマージ待ちと約束の経路に絞って書く |
| K7 | 独立-2 | low | no | self-inflicted | pushback-errors | next-pr | lambda の中で try の外の例外はエラー記録に残らない |
| K8 | 独立-2 | low | no | self-inflicted | merge-intent-ci | next-pr | checks の無い repo で常に pending になる |
| K9 | 独立-2 | low | no | inherited | merge-intent-ci | next-pr | CI の判定が全 check を見て required に揃っていない |
| K10 | 独立-2 | low | no | inherited | merge-intent | next-pr | repo・then が null だと宣言全体が無効になる |
| K11 | 独立-2 | low | no | inherited | merge-intent | next-pr | 宣言の基準ディレクトリが文書に無い |
| K12 | 独立-2 | advisory | no | self-inflicted | merge-intent | accepted | 正規表現の $ が末尾の改行を通す。PR 本文に列挙 |
| K13 | 独立-2 | advisory | no | self-inflicted | pushback-errors | accepted | 一時ファイルが残りうる。PR 本文に列挙 |
| K14 | 独立-2 | low | no | self-inflicted | test-power | next-pr | FIFO の sidecar のテストがどの block かを見ていない |
| K15 | 独立-2 | low | no | self-inflicted | test-power | fixed | 締め切りを過ぎる分岐を通るテストが無い。RunWithinDeadlineTest を足した。commit: f7579550 |
| K16 | 独立-2 | low | no | inherited | doc | next-pr | state-machine.md の Stop hook の判定順が押し返しに追随していない |
| K17 | 独立-2 | advisory | no | self-inflicted | doc | fixed | PR 本文の箇条の位置。commit: なし（PR 本文） |
| K18 | 独立-2 | advisory | no | self-inflicted | doc | accepted | changelog の「2 つのファイルを足した」が description の実物と合わない。PR 本文に列挙 |
| K19 | 独立-2 | advisory | no | self-inflicted | doc | fixed | post-merge-qa.md の助詞。commit: f7579550 |
| pm2-1 | 方針メモ-2 | advisory | no | self-inflicted | pushback-deadline | accepted | 安全策 4 の発火。Opus は続行（境界の不変条件化）、Fable も続行。3 巡目に同じクラスタの high が出たら、押し返しを guard が許可した後へ並べ替える（Fable）か merge-wait だけ撤回する（Opus） |
| M3-1 | 独立-3 | medium | no | self-inflicted | pushback-deadline | next-pr | 締め切りの起点が import 時で、human check の押し返しは手前の処理に予算を食われ、記録も残さずに出ないことがある |
| M3-2 | 独立-3 | medium | no | self-inflicted | test-power | next-pr | 約束の経路の peer の判定にテストが無い |
| M3-3 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 締め切りの共有のテストが 2 つの変異を見逃す |
| M3-4 | 独立-3 | low | no | self-inflicted | test-power | next-pr | fn の例外のテストが差分の前でも緑になる |
| M3-5 | 独立-3 | low | no | self-inflicted | merge-promise | next-pr | 約束の判定が 2 か所にある |
| M3-6 | 独立-3 | low | no | inherited | pushback-deadline | re-reported | 締め切りぎりぎりで key だけが書かれうる（K4 の再掲） |
| M3-7 | 独立-3 | low | no | inherited | doc | next-pr | post-merge-qa.md の押し返しの記述に条件が無い |
| M3-8 | 独立-3 | advisory | no | inherited | peer | accepted | human check の押し返しは peer を見ない（設計の選択）。PR 本文に列挙 |
| M3-9 | 独立-3 | advisory | no | inherited | doc | accepted | hooks.json の description に human check の押し返しが無い。PR 本文に列挙 |
| M3-10 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | テストが Thread.start をプロセス全体で差し替え、mkdtemp を消さない。PR 本文に列挙 |
