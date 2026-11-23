---
type: patch
---

#### Summary

- steering への書き込みの検査（`validate-steering-write.py`）が state dir に書く deny の counter に、書き込み先のパスと category を書かないようにした。回数と時刻だけを書く。counter は umask のまま（通常 0644）作られるので、これまでは書き込み先の steering ファイルの絶対パスが平文で残っていた。回数・閾値・TTL・消す契機は変えていない
- `docs/SECURITY.md` の counter と `last-turn-failure.json` の記述、`references/bounce-log-schema.md` の counter の置き場所と TTL の記述を、実装に合わせた。`last-turn-failure.json` は、project root が一致する SessionStart（compaction の直後を除く）か壊れた記録のときに消え、別の project のセッションでは残る

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/references/bounce-log-schema.md`

#### User Action Required

- 任意：以前の版が作った counter は、書き込み先のパスを持ったまま残る。1 時間を過ぎた counter は回数を 0 と読まれるだけなので、消しても挙動は変わらない。消すときは次を実行する（`GDD_HOOK_STATE_DIR` を変えているなら、そのディレクトリを指定する）
  - `find ~/.claude/.gdd-hook-state -maxdepth 1 -type f -name '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f].json' -mmin +60 -delete`

#### Validation / Eval Impact

- `tests/test_steering_deny_counter_contents.py`
- `tests/validate-plugin.sh`
