---
lane: L1
pr: 105
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| codex-1 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線） | 223ba3ae | 0 | 1 | 0 | 2026-09-17T20:30+09:00 |
| 独立-1 | general-purpose subagent (model: opus, read-only, diff-only, 経緯非共有; independent-review.md (a)〜(h) 込み) | 3a48a25c | 0 | 0 | 0 | 2026-09-17T20:50+09:00 |
| PR後-1 | GitHub PR 旧#105 review (yamaguchi-tk、採用 1 件・不採用 7 件) と、その修正への push 前セルフレビュー（F7） | 57a06164 | 1 | 1 | 0 | 2026-09-17T21:30+09:00 |
| codex-2 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線 + additionalContext の sanitize の受理集合） | 5b4c0ef6 | 0 | 2 | 0 | 2026-09-17T22:10+09:00 |
| 独立-2 | general-purpose subagent (model: opus, read-only, 3a48a25c..45edf5dc の差分と影響先, 経緯非共有; independent-review.md (a)〜(h) 込み) | 45edf5dc | 0 | 1 | 0 | 2026-09-17T22:40+09:00 |
| 独立-3 | general-purpose subagent (model: opus, read-only, 45edf5dc..87e362b1 の差分と影響先, 経緯非共有; independent-review.md (a)〜(h) 込み) | 87e362b1 | 0 | 0 | 0 | 2026-09-17T23:05+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | codex-1 | medium | no | inherited | shadow-base-depth | deferred | 置き場の task 列挙が <base>/<repo> 直下 1 階層固定で .git を見ず、find-stale-steerings.sh --registry（.git 基準・深さ無制限）と受理集合が非対称（実測 ~/.gdd/worktrees の .git 112 件すべて 1 階層、書く側の契約も <base>/<repo>/<task-slug>。PR 旧#101 F3 と同クラスタで既定の置き場から継承） |
| F2 | 独立-1 | low | no | self-inflicted | shadow-candidate-cap-order | deferred | 探索順が既定→env→設定の Worktree Base のため、既定の置き場に非終端 steering が 5 件以上あると設定済み base の候補が上限で表示されない（marker 自体は出る） |
| F3 | 独立-1 | advisory | no | self-inflicted | worktree-base-resolution | deferred | 未追跡の .gdd-config.md を持つ別 clone の Worktree Base は GDD_WORKTREES_ROOT を設定しない限り探さない限界が変更断片に未記載 |
| F4 | 独立-1 | advisory | no | self-inflicted | test-power | deferred | 相対パスの Worktree Base を設定ファイル基準で解決する分岐にテストが無い |
| F5 | 独立-1 | advisory | no | self-inflicted | doc-claim | deferred | docs/SUPERPOWERS_COEXISTENCE.md:134 の shadow-marker 探索先列挙に設定済み Worktree Base と GDD_WORKTREES_ROOT が無い |
| F6 | PR後-1 | medium | yes | inherited | context-json-sanitize | fixed | SessionStart の reboot / 複数 steering / shadow-marker の 3 分岐が dir 名・パス・state.md の値を `"` と `\` だけエスケープして出力し、TAB 等の制御文字で JSON が壊れ additionalContext 全体が落ちる（Worktree Base で到達面が拡大）。3 分岐とも出力直前に LC_ALL=C tr -d '[:cntrl:]' |
| F7 | PR後-1 | high | yes | self-inflicted | context-json-sanitize | fixed | F6 の修正で足した tr -d '[:cntrl:]' が UTF-8 ロケールの BSD tr で不正なバイト列に Illegal byte sequence を返し、set -euo pipefail で hook 全体が出力無しで止まる（セルフレビューで実測、再現テスト追加後に LC_ALL=C で修正） |
| F8 | codex-2 | medium | yes | self-inflicted | context-json-sanitize | fixed | F6 の制御文字除去が不正な UTF-8 を通し、出力が strict UTF-8 では読めない JSON のまま残る。再現テストも decode("replace") で隠していた。テストを置換なし decode にして RED を確認し、compact 経路と同じ gdd_truncate_chars（上限は自分の長さ）を通すよう修正 |
| F9 | codex-2 | medium | no | inherited | context-json-sanitize | deferred | compact 経路のサイクル上限警告が GDD_MAX_AUTO_CYCLES を検証せず埋め込み、改行を含む値で JSON が壊れる（利用者自身が設定する環境変数で、今回の入力＝dir 名・state.md の値とは別の入力。この PR は compact 経路に触れていない。全出力点の共通 serializer 化とあわせて後続課題） |
| F10 | 独立-2 | medium | yes | self-inflicted | context-json-sanitize | fixed | F8 で通した gdd_truncate_chars の python3 が失敗すると（壊れた shim・UTF-8 以外のロケール）空文字を成功扱いで返し、reboot / 複数 steering / shadow-marker の案内全体が無言で空になる（変更前は python3 を通らず起きなかった）。再現テスト追加後、空なら制御文字の除去だけに戻す分岐を追加。gdd_truncate_chars 自体の修正は既存経路にも効くため後続課題 |
| F11 | 独立-3 | low | no | self-inflicted | context-json-sanitize | deferred | python3 の失敗を「結果が空」で推定するため、エラーを stdout に書いて非ゼロ終了する壊れた python3 では退避が効かず、案内が shim の出力に置き換わる（pyenv/asdf の shim は stderr に書くため現実的な確率は低い。gdd_truncate_chars が終了コードを返す修正とあわせて後続課題） |
| F12 | 独立-3 | advisory | no | inherited | context-json-sanitize | deferred | compact 経路・post-merge 経路には python3 失敗時の退避が無く、値が空のまま案内が出る（変更前から。変更断片の限界に開示済み） |
