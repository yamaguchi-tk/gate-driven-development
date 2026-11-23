---
lane: L1
pr: 244
follow_up_of: 232
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 62121d7c50b06beeab94d81efc6e50893fff37ac | 0 | 0 | 0 | 2026-09-29T17:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | test-power | fixed | EUC-JP の判定の呼び出し側（`euc_jp_locale_env`）を元の比較に戻してもテストが通った。subprocess を差し替えて、別名で skip せず、近い codec で skip するテストを足した。別名のテストは skip を失敗にして、戻すと落ちることを確かめた。commit: 781a0a3a |
| F2 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 「別名を取りこぼす」は python が別名を返す前提だった。変更断片を「別名を返しても EUC-JP と読む（防御）」に直した。commit: 781a0a3a |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 前の文脈に改行とタブが無く、正規表現の前後読みを狭める変更が通った。`\n`・`\t`・`x\n` を足した。commit: 781a0a3a |
| F4 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 「全組み合わせ」が選んだ 16×12 の直積である点を、断片とコメントに書いた。commit: 781a0a3a |
| F5 | 独立-1 | advisory | no | inherited | test-power | accepted | `_scripts_of` が `re.search` なので、`.sh` に別の command が続く複合の command は最初の `.sh` だけ拾う。変更前も同じで、`test_hooks_wiring_new_events_contract.py` の fullmatch が落とす。次の改善で扱う |
| F6 | 独立-1 | low | no | inherited | test-power | accepted | 廃止した印の正規表現が、選択の中（`Status` の後ろが選択の区切り）・エスケープした改行の直後・空白の直後の形を拾わない。差分の外の列挙型の判定。現在の hook にこの形の廃止した印の読み手はない。PR 本文の限界に書く |
| F7 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 未リリースの断片 `20260918-issue123-always-high-resume-scope.md` の記述が今のテストと逆になっている。リリース時に直す |
| F8 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | `_hook_scripts` が `_scripts_of` を通ることは固定していない。今の hooks.json で `.sh` でない command が入れば、別のテスト（`_COMMAND_RE` の fullmatch）が落とす |
