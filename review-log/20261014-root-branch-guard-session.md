---
lane: L1+
pr: 505
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 282254bf | 0 | 0 | 0 | 2026-10-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fffb5adf | 4 | 1 | 4 | 2026-10-14 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | abadf7d9 | 0 | 0 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 189cf61a | 2 | 0 | 2 | 2026-10-14 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 189cf61a | 0 | 0 | 0 | 2026-10-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6827ff2a | 0 | 0 | 0 | 2026-10-14 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 37db0335 | 0 | 0 | 0 | 2026-10-15 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 24cf57ae | 0 | 1 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | advisory | no | inherited | design | accepted | 採用: Opus の推奨（案 A'）。今の session id は payload の session_id だけから取り、env の予備は持たない。state の session_id が空・無いときは deny。照合は main() の try の中。OSError で allow になる既存の穴は混ぜない。main の草案は payload の次に env を見る形だった。信号 ① で Fable に相談し、Fable も案 A'。ユーザーが「この方針で進める」を選んだ |
| I1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: marker の持ち主の id は setup が env の CLAUDE_CODE_SESSION_ID から書き、今の id は payload から読む。env を継いだ runtime（Cursor など）が持ち主のとき、持ち主自身も通る。ユーザーの「常時Highの修正をしたい」を受け、方針メモ-3 の案 X′ で直した。commit: c6647c8a |
| I1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | id の形でない値（U+FFFD・引用符つき・`# note` つき）を別の session として通す。commit: b15de135 |
| I1-3 | 独立-1 | high | yes | self-inflicted | parse-symmetry | fixed | splitlines が U+2028 などでも行を分け、行頭の `session_id:` だけを数えるので、parse_state（strip・後勝ち）と受理集合がずれる。commit: b15de135 |
| I1-4 | 独立-1 | high | yes | inherited | fail-open | fixed | marker が通常のファイルでない・OSError のとき全員を通す（差分が変えた関数の中）。commit: abadf7d9 |
| I1-5 | 独立-1 | medium | no | self-inflicted | evidence | fixed | PreToolUse の payload に session_id が入るかが未測。Claude Code 2.1.280 のバイナリで、payload の session_id が session.id（リモート呼び出しだけ `served:<id>`）であることを確かめ、PR 本文に書く。commit: なし（PR 本文） |
| I1-6 | 独立-1 | low | no | self-inflicted | docs | accepted | test_root_branch_guard_contract.py のコメントが古い |
| I1-7 | 独立-1 | low | no | self-inflicted | docs | accepted | docs/SECURITY.md の Bash の行に payload の session_id が無い |
| I1-8 | 独立-1 | low | no | self-inflicted | test-coverage | accepted | setup-gdd-loop.sh を通したテストが無い |
| I1-9 | 独立-1 | low | no | self-inflicted | pr-body | accepted | 目的の節に件数を数えたコマンドが無い |
| I1-10 | 独立-1 | advisory | no | self-inflicted | naming | accepted | 関数名 active_gdd_state_exists が意味と合わない |
| I1-11 | 独立-1 | advisory | no | self-inflicted | changelog | accepted | 断片の User Action Required が「なし。」の後にすることを書いている |
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | design | accepted | 列挙: I1-1 は (b)。入力者の実測は、active の marker 12 個のうち cursor 3・codex 1 がどれも session_id 空（今も止まる）で、env を継いだ runtime が親の id を書いた形は 0 件。main の案（workflow_runtime: claude_code のときだけ緩める）は、Opus が許可リストに当たらず効く件数も 0 件として推さず、採らない。I1-2 と served: は id の形の許可リストで閉じる（誤 block の実測: claude_code の marker 8 個はどれも transcript があり形に収まる。transcript の sessionId 559,584 件で形の外は 0、served: は 30 日で 0 件）。I1-4 は、M-1 の「OSError の穴は混ぜない」を改めて直す。① の変更箇所の high（§ 常時 High）で、依頼の「例外のときは止める」にも当たるため |
| I2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | root の `.claude/` に x が無いと os.path.lexists が marker を「無い」と読んで通す。Python 3.12 以前では、差分前の is_file が EACCES を送出して deny だったので退行。安全策 4 の発火で HITL へ（ユーザーは A を選んだ）。commit: f7d9ce10 |
| I2-2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: marker の書き手は env の id、読み手は payload の id。env を継ぐ runtime で持ち主自身を通す（I1-1 と同じ内容。§ 常時 High なので re-reported にしない）。安全策 4 の発火で HITL へ。ユーザーの「常時Highの修正をしたい」を受け、方針メモ-3 の案 X′ で直した。commit: c6647c8a |
| I2-3 | 独立-2 | low | no | self-inflicted | product | accepted | 読めない marker で止める条件を、依頼の原文で確かめた方針（今までどおり止める）より広げている。依頼の原文から外れた指摘なので HITL でユーザーに確かめ、「止める側に広げてよい」を request.md に足した |
| I2-4 | 独立-2 | low | no | self-inflicted | product | accepted | 新しく足した止め方で、deny の文が理由と抜け方を示さない |
| I2-5 | 独立-2 | low | no | self-inflicted | docs | accepted | contract テストのコメントと docs/SECURITY.md:99 の記述が古い |
| I2-6 | 独立-2 | low | no | self-inflicted | changelog | accepted | 変更断片の User Action とテストの冒頭のコメントが新しい止め方を含まない |
| I2-7 | 独立-2 | advisory | no | inherited | parse-symmetry | accepted | 同じ marker の session_id を読む detect-steering.sh・setup-gdd-loop.sh と受け入れる形が違う（guard の側が厳しい） |
| I2-8 | 独立-2 | advisory | no | self-inflicted | pr-body | accepted | この変更で 21 件のうち何件が通るようになるかが書かれていない |
| M2-1 | 方針メモ-2 | advisory | no | self-inflicted | design | accepted | 安全策 4 の発火（fail-open の high を含む巡が 2 回）。Opus の推奨は A（I2-1 を lib/regular_file.py の read_regular_text で直し、独立-3 を最後の巡にする）。main も A。選択肢は A・B（止める）・C（M-1 の範囲に戻す）・D（取り下げ）。ユーザーは A を選び、読めない marker で止める広げ方も認めた |
| I3-1 | 独立-3 | low | no | self-inflicted | product | accepted | regular_file の import に失敗すると、deny のメッセージと回復手順が git_command_parse.py だけを名指しする（止める側） |
| I3-2 | 独立-3 | low | no | self-inflicted | test-coverage | accepted | regular_file.py が欠けても止まることを、入口から固定するテストが無い |
| I3-3 | 独立-3 | low | no | self-inflicted | product | accepted | 検索権の無い `.claude/` の下では、state が無くても止める。依頼で承認された文（marker があるのに）より広い。巡の上限の 3 巡目の後なので、限界の節に書き、依頼から外れたままであることをユーザーに明記する |
| I3-4 | 独立-3 | low | no | self-inflicted | docs | accepted | 断片の「今までは通していた」は、検索権の無い `.claude/` については Path.is_file() が権限エラーを False に読む Python の版でだけ成り立つ |
| I3-5 | 独立-3 | advisory | no | self-inflicted | docs | accepted | 足したテストのコメントが os.lstat を名指しする（今は os.open が EACCES を受ける） |
| I3-6 | 独立-3 | advisory | no | inherited | parse-symmetry | accepted | 同じ marker を `[[ -f ]]` で読む bash 側の hook は、通常のファイルでない・検索権の無い marker を inactive と読む（向きが逆） |
| I3-7 | 独立-3 | advisory | no | inherited | changelog | accepted | 断片の Summary が、閉じの区切りが無いときを止める条件に挙げていない |
| M3-1 | 方針メモ-3 | advisory | no | self-inflicted | design | accepted | ユーザーが「常時Highの修正をしたい」と依頼（マージ前）。Opus の推奨は案 X′（payload の id が環境変数 CLAUDE_CODE_SESSION_ID と一致するときだけ緩める）を 旧#505 に積むこと。main の案 X（環境変数が持ち主と同じなら止める）・Y（setup が claude_code 以外では session_id を空で書く）・Z は、Y が Codex の経路（runtime が claude_code と判定される）を閉じないので外した。前に書いた「この形は 0 件」は、継いだ形を見分けられない測り方だった。ユーザーは X′ を選び、依頼の原文の「環境変数は予備としても使いません」から外れることを認めた |
| I4-1 | 独立-4 | medium | no | self-inflicted | test-power | fixed | 止める側のテストの多くは env なしの `_run` で起動し、「照合できない」分岐で止まって通る。frontmatter の読み方・形の検査・持ち主との一致の変異（先勝ち・本文の値・`or gdd_named` を外すなど）が生き残る。修正案は helper の既定を env と payload の一致に反転すること。ユーザーの「テストも直してからマージして」で直した。commit: b07c55f0 |
| I4-2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | Claude Code の PreToolUse の hook で環境変数と payload の id が一致することに、PR の中の証拠が無い（一致しなければ止める側で、21 件の改善が 0 になる） |
| I4-3 | 独立-4 | advisory | no | self-inflicted | style | fixed | テスト名 test_env_session_id_is_not_used が、変更後の規定と読み違えられる。ユーザーの「テストも直してからマージして」で直した。commit: b07c55f0 |
| I4-4 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の目的の文が、Claude Code 以外の runtime まで含めて言い切っている |
| I4-5 | 独立-4 | advisory | no | inherited | changelog | accepted | 断片が「閉じの区切りが無い」を名指ししていない |
