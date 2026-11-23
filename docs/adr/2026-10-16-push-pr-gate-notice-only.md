# ADR: pre-push gate と pre-PR gate は push・PR 作成を止めず、実行後の通知と would-block の記録だけを残す

- **日付**: 2026-10-16（ユーザーの指示「1から順に対応して」「次に取りかかって」。第 1 手の後半）
- **状態**: Accepted
- **Supersedes（部分）**: `docs/adr/2026-10-03-block-guard-threat-model.md` の「外すのは、正当な入力を止めると実測できたときだけ」を、2 つの gate について置き換える
- **関連**: `docs/adr/2026-10-15-merge-gate-notice-only.md`（merge gate の同じ決定）/ `plugins/gate-driven-development/hooks/scripts/lib/gate-notice.sh` / `plugins/gate-driven-development/docs/SECURITY.md` § 制限事項

## Context

2026-09-15〜10-15 の transcript で、hook が実際に止めた回数（is_error の tool_result で、本文が hook の ⛔ の文で始まるもの）は、pre-PR gate が 11 回、pre-push gate が 4 回だった。

- pre-PR gate の 11 回のうち 9 回は「state.md / tasklist.md を一意に解決できません」で、agent は hook のコードを読み、別の cwd から作り直すなどで回避した。欠陥を捕まえた例は 0 件。PR 本文の機密候補で止めたのは 0 件
- pre-push gate の 4 回のうち 1 回は、止められた後に回した独立レビューが high 1・blocking 1 を見つけた。1 回は、止められた後にレビューを回さず、証跡の行だけを書いて push した
- 止めない hook の通知は、コマンドの実行後に届く。push・PR 作成の後でも、merge の前に通知でレビューを回せる

## Decision

- 2 つの gate は止めない。不足を見つけたら、不足を「実行後の通知」（`hookSpecificOutput.additionalContext` と `systemMessage`）で返し、state dir の `pre-push-gate-suppressed.log`・`pre-pr-gate-suppressed.log` に `would-block:<code>` を 1 行書く（形は merge gate の `merge-gate-suppressed.log` と同じ。repo は絶対パスの sha1 の先頭 8 桁）
- code は呼び出し側が引数で宣言して渡す（`block <code> <本文>`）。本文から切り出さない。pre-PR gate の多くの文は reason code を持たないので、切り出すと記録が測れなくなる
- 通知の組み立てと記録は `lib/gate-notice.sh` の `gdd_gate_notice` 1 本にする。python3 に依存しない
- pre-PR gate は PR 1 本につき 1 回しか走らないので、最初の不足で終えず、見つけた不足をまとめて 1 本の通知と 1 行の記録（code はカンマでつなぐ。merge gate と同じ形）にする。出すのは終了時の trap なので、後段のコマンドが落ちても集めた不足は消えない。PR 本文の検査（機密候補など）は steering に依らないので、steering を解決する前に行う。steering を解決できない・読めないとき、base branch を解決できないときは、その後の検査をせずに、それまでの不足を出す
- pre-push gate は push のたびに走るので、今までどおり最初の不足 1 つを通知する
- PR 本文の機密候補も通知にする。本文はもう GitHub に出ているので、通知はただちにユーザーに報告するよう求める（30 日で 0 件。12 桁の数字の規則は、AWS アカウント ID を GitHub に書いてよいとする運用と食い違う）
- 判定のコードと reason code は残す。撤去（hooks.json から外す）はしない。この PR のマージから 30 日以降に、would-block の全行を、時刻と repo の hash で transcript の Bash の実行と突き合わせ、止めていたら防げたもの（未レビューの merge、機密の本文など）があったかを数える。あれば止め方を戻すかを検討し、無ければ撤去を検討する

## Consequences

- 2 つの gate は `references/reviewer-common.md` § 常時 High の適用範囲の外（block しない hook）になる。gate が使う shell 解析の部品（`lib/push_command_parse.py`・`lib/gh_command_parse.py` など）は、Stop hook の押し返しなど block する部品と共有しているので、L1+ のまま残る
- merge gate も止めないので、push から merge までに plugin が止める地点は無い。証跡とレビューは、agent が通知に従うかで決まる。承認は導入先の運用で担保する
- `GDD_SKIP_PRE_PUSH_GATE=1` は、止めるのを外すものから、通知と記録を省くものに意味が変わる
- raw task steering の検査は active GDD かどうかを見る前に走るので、active でない repo でも、止めずに通知する形に変わる
- merge gate の `block()` はまだ `lib/gate-notice.sh` を使っていない（通知の実装が 2 本ある）。移すのは次の PR（2026-10-16 追記: 後続の PR 旧#540 で merge gate も lib/gate-notice.sh に移した）
- Cursor・Codex で、止めない PreToolUse の通知がどう届くかは測っていない
