# ADR: merge gate は merge を止めず、実行後の通知と would-block の記録だけを残す

- **日付**: 2026-10-15（ユーザーの指示「1から順に対応して」。第 1 手として提示した案）
- **状態**: Accepted
- **Supersedes（部分）**: `docs/adr/2026-10-03-block-guard-threat-model.md` の「外すのは、正当な入力を止めると実測できたときだけ」を、merge gate について置き換える / `docs/adr/2026-09-11-env-s-merge-gate.md` の「後続の変更が守る制約」は、merge gate が止めなくなったので fail-open を数えない
- **関連**: `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh` の `block()` / `plugins/gate-driven-development/docs/SECURITY.md` § 制限事項 / `plugins/gate-driven-development/references/reviewer-common.md` § 常時 High の適用範囲

## Context

2026-09-15〜10-15 の transcript では、merge gate は merge を 59 回止めた（60 秒以内の重複をまとめて 54 回）。事故を防いだ例は 0 件で、45 件は止める必要のないものだった。主な原因は、承認の有無ではなく、コマンドの書き方や実行場所から対象 PR を決められないこと（`pr-target-unresolvable` 33 件）である。証跡の検査まで届いた止め方は 12 件だった。同じ期間に、steering を解決できずに検査を通らなかった merge は 415 件あった。承認の無い merge は 357 件中 1 件で、merge gate はそれを止めていない。

止める側に倒す shell 解析は、独立レビューが 4 巡以上かかる PR の主な発生源だった（30 日で関係 PR 29 本）。

## Decision

- merge gate は止めない。不足を見つけたら、reason code と不足を「実行後の通知」（`hookSpecificOutput.additionalContext` と `systemMessage`）で返し、state dir の `merge-gate-suppressed.log` に `would-block:<code>[,<code>…]` を 1 行書く（集約の経路では不足条件の全 code を書く）
- 判定のコードと reason code は残す。止めていた場面が今どれだけあるかを、would-block の記録で測る
- 止めない hook の additionalContext は、コマンドの実行後に届く。通知の文は、merge が成功した場合（不足をユーザーに報告するだけにし、承認や証跡を後から書き足さない）と、失敗した場合（後ろに続く手順で直してから再実行する）を分ける前置きで始める
- 承認の無い merge、bot レビューを待たない merge は plugin では止めない。承認は導入先の運用（人がマージを決める、branch protection、auto mode classifier など）で担保する
- 撤去（hooks.json から外す）はしない。2026-11-15 以降に、would-block の全行（code を問わない）を、時刻と repo の hash で transcript の Bash の実行と突き合わせる。そのうえで、merge だったか（merge でないコマンドの `parse-error` の行もある）と、merge の前にユーザーの承認があったかを transcript で分類する。承認の無い merge が 1 件以上あれば止め方を戻すかを検討し、0 件なら撤去を検討する。code の種類では分類しない（承認の判定より前の code で終わる経路があり、承認の無い merge の多くは approval 系でない行に入るため）

## Consequences

- merge gate は § 常時 High の適用範囲の外（block しない hook）になる。merge gate だけを変える PR を L1 にするには、root `CLAUDE.md` のレーンの表（L1+ の対象に merge gate を挙げている）を直す必要があり、この ADR の時点では直していない。merge gate が使う shell 解析の部品（`lib/gh_command_parse.py` など）は、Stop hook の押し返しなど block する部品と共有しているので、L1+ のまま残る
- auto mode classifier の無い runtime（Cursor・Codex など）では、plugin の側に merge を止める仕組みが無くなる。その runtime での merge は測っていない
