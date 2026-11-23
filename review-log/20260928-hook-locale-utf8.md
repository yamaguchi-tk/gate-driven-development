---
lane: L1+
pr: 旧#217
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) | f6e44eede5f486557c65e89a13b1f07ff8aab9a1 | 0 | 0 | 0 | 2026-09-28T23:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 52b6728b03f2ac4e01b7d0afdfd5c46d42854ed5 | 0 | 0 | 0 | 2026-09-29T00:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 5b9da7b2b940da23bdc9791d65659765c49de732 | 0 | 0 | 0 | 2026-09-29T01:10+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | f8d81ebd292d36947d4db2fb2adf24c890981f46 | 0 | 0 | 0 | 2026-09-29T01:50+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | hook-locale | next-pr | hook の外で使う `scripts/` の CLI（`find-stale-steerings.sh` など）は kill-switch.sh を source しないので、UTF-8 以外のロケールでは構文エラーで止まる。block gate ではなく黙って通すことはないので、この PR には入れない |
| P2 | 方針メモ | advisory | no | inherited | pre-push-exception | next-pr | pre-push gate の payload 読み取りの `except Exception: pass` は、ロケール以外の原因でも push を通す。ロケールの修正とは別の fail-open なので次の PR にする |
| I1-1 | 独立-1 | low | no | self-inflicted | hook-locale-doc | fixed | 入口経由の切り詰めのテスト（`test_hook_multibyte_truncation_contract.py`）の 3 ロケール軸が、kill-switch.sh の上書きで全部 C.UTF-8 になり、docstring と実態が合わない。C ロケールでの切り詰めの検査が入口では効かない |
| I1-2 | 独立-1 | low | no | self-inflicted | hook-locale-doc | fixed | kill-switch.sh のコメント・断片・PR 本文が、C.UTF-8 が無いときの bash 自身の挙動と、`-I`・`-E` の python の起動の有無について言い過ぎている |
| I1-3 | 独立-1 | low | no | self-inflicted | hook-locale-doc | fixed | `run-session-start-hook.sh:576` と `test_route_in_progress_reader_contract.py:409-412` のコメントが、hook の中で UTF-8 以外のロケールが効く前提のまま |
| I1-4 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | source の順序のテストが監視するのは python・awk・sed・grep だけで、tr・cut などは見ない。今の入口では source より前に無い |
| I1-5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | UTF-8 の利用者でも照合順序が C.UTF-8 に変わり、C ロケールの利用者は文字単位の扱いに変わる。判定への影響は無い |
| I1-6 | 独立-1 | advisory | no | inherited | release-fragment-overlap | accepted | 未リリースの断片 `20260917-shadow-marker-worktree-base.md` の「python3 が失敗する原因＝UTF-8 以外のロケール」が古くなる。リリースの版の節で直す |
| I2-1 | 独立-2 | low | no | self-inflicted | hook-locale-doc | fixed | 入口テストのコメントが「上書きが効くことの確認になる」と書くが、テストはそれを見ていない。docstring の書き方と食い違う |
| I2-2 | 独立-2 | low | no | self-inflicted | hook-locale-doc | fixed | テストのコメントが C.UTF-8 への固定を無条件に書き、C.UTF-8 が無い環境の扱い（kill-switch.sh のコメント）と食い違う |
| I2-3 | 独立-2 | low | no | inherited | test-power | fixed | C.UTF-8 がある環境では、入口の hook を `${var:0:N}` に戻しても入口テストが通る。2 つの hook に `${var:0:` が無いことをコードで固定した |
| I2-4 | 独立-2 | advisory | no | inherited | test-power | accepted | `test_route_in_progress_reader_contract.py` の `LOCALES_UNDER_TEST` の ja_JP.UTF-8 が、CI の runner に無ければ C で走り、2 ロケールの設計が 1 つに縮む（未確認） |
| I3-1 | 独立-3 | low | no | self-inflicted | test-power | next-pr | `_locale_support.py` の EUC-JP の判定が文字列比較で、libc が `eucJP` を返すと入口テストが skip になる（推定）。この macOS では `euc_jp` が返り skip されないことを実測した。`codecs.lookup` での比較への堅牢化を次の PR で扱う |
| I3-2 | 独立-3 | low | no | self-inflicted | test-power | next-pr | `_hook_scripts()` が `hooks/scripts/<名前>.sh` に当たらない hooks.json の command を黙って落とす。`.sh` 以外の入口を足すと、kill-switch.sh を通らなくても検査が通る |
| I3-3 | 独立-3 | low | no | inherited | hook-locale | next-pr | `run-pre-compact-hook.sh:78` の Resume From の切り詰めが `${RESUME_FROM:0:128}` のままで、SessionStart の `gdd_truncate_chars` と別実装。C.UTF-8 が無く C ロケールの環境で残る。PR 旧#208 が PreCompact を書き換えるので、その取り込みの後で確かめる |
| I3-4 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | C.UTF-8 が無いホストでは setlocale の警告が stderr に出て、stderr を検査する既存のテスト（`test_hooks_kill_switch.py:130` など）が落ちる（推定）。CI の Ubuntu と macOS には C.UTF-8 がある |
