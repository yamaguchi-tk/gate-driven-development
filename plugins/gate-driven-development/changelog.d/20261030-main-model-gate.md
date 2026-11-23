---
type: minor
---

#### Summary

Claude Code で、main のセッションが Sonnet・Haiku のときに GDD の起動（`/gdd-dev`・`/gdd-resume` の Skill の呼び出し、`setup-gdd-loop.sh` の実行、手動の手順で、active でない `.claude/gdd-dev.local.md` に書く書き込み）を止めるようにした。セッションの開始か相談の段の返事の後に、セッションにつき 1 回、Opus への切り替えを知らせる。2026-10-19〜10-30 の判断ポイントつきの確認で、人が作り直しを求めた率は main が Sonnet で 6/13、Opus で 2/56 だった。狭い案は GDD に入る前の main の相談で作られていて、main は自分のモデルを替えられないので、警告ではなく止める。

#### Changed

- 新しい hook `hooks/scripts/run-main-model-gate-hook.sh`（判定は `hooks/scripts/lib/main_model_gate.py`）を、PreToolUse（`Skill|Write|Edit|MultiEdit`）・Stop・SessionStart に登録した。gdd-dev・gdd-resume の Skill の呼び出しと、手動の手順で run を始める `.claude/gdd-dev.local.md` への書き込み（ディスクのファイルが active でないときの書き込み。書く内容は見ない）で毎回判定する。`setup-gdd-loop.sh` も同じ判定を script の中で行い、止めるときは 1 で終わる（どう包んで実行しても判定し、読むだけでは判定しない）。直接打った `/gdd-dev`（UserPromptExpansion）は判定しない（返事の前の transcript の最後の信号は前のターンのモデルのため）。相談の段の通知は、返事の後の Stop で出す。SessionStart は payload の model だけで判定する
- 止める判定のモデルは、Skill を呼んだ・script を実行した返事の行（hook では入力の `tool_use_id` を持つ行、無ければ今の turn の main の assistant の行）から取る。transcript は遅れて書かれることがあるので短く読み直し、それでも無ければ main の transcript の最後の信号（model の attachment、`/model` の出力、main の assistant の `message.model`）で決める。このときだけ、止める文に、画面で切り替えた直後なら一言送ってからやり直す案内を足す。どの段で決めたかを `~/.claude/.gdd-hook-state/main-model-gate.log` に書く。信号が無いときは止めず、Claude Code なら判定できなかったことを知らせる
- `GDD_ALLOW_NON_OPUS_MAIN=1`（`settings.json` の `env`）で外せる。`setup-gdd-loop.sh` は settings のファイルの env だけを読み、コマンドの前に付けた値では外れない。kill switch（`~/.claude/gdd-hooks-disabled`）があるときも、ほかの hook と同じく働かない

#### Affected Files

- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/hooks/scripts/run-main-model-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/main_model_gate.py`
- `plugins/gate-driven-development/scripts/setup-gdd-loop.sh`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/tests/test_main_model_gate.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`

#### User Action Required

- Claude Code で GDD を使うときは、main のセッションを Opus にする（`/model opus`）。Opus を使えないときは `settings.json` の `env` に `GDD_ALLOW_NON_OPUS_MAIN=1` を設定する
- デスクトップアプリの画面でモデルを切り替えた直後に止まり、止める文が一言送るよう案内したときは、一言送ってから起動し直す

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_main_model_gate.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
