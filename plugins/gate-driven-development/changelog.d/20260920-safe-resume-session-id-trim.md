---
type: patch
---

#### Summary

SessionStart hook の Safe Resume Candidate Mode が、`.claude/gdd-dev.local.md` の `session_id` の末尾の空白・CR を落とさずに現在の session id と比べていた。手で編集した・改行コードを変換した local state では、同じ session でも `[gdd:paused] … Safe Resume Candidate Mode` に落ち、同一 worktree の自然な再開が止まっていた。同じ行を読む `gdd_session_continuity_ok`（`lib/detect-steering.sh`）と `lib/state_io.py::parse_state` は末尾を落とすので、3 つの読み手のうち Safe Resume だけが違っていた（PR 旧#140 の review-log の V13・Z6・Q1。旧#140 の断片が「直していない既存の欠陥 6 件」のうち 1 件目に挙げたもの）。

Safe Resume の読み取りに、末尾の空白・CR を落とす `sed` を 1 段足した。効くのは最後の `==` 比較だけである。1 段目の `sed 's/^session_id:[[:space:]]*//'` の `[[:space:]]*` は貪欲なので、その出力は「空」か「先頭が非空白」のどちらかにしかならず、末尾の除去が値を空にすることはない。したがって、値が空かどうかで選ぶ 2 つの分岐は動かない。

#### Fixed

- `hooks/scripts/run-session-start-hook.sh` の Safe Resume の `STORED_SESSION_ID` の読み取りで、末尾の空白・タブ・CR を落とすようにした。落とすのは末尾だけで、値の途中の空白は保持する。現在の session id（env）側は変えない
- main の全量テストが赤だったのを直した。旧#145 が Check 3 の読み手 `select_route_in_progress` を `gdd_stop_hook.py` から `lib/done_guard.py` へ移した後の main で、旧#140 の `tests/test_always_high_scope_contract.py::ResumeScopeTest::test_resume_fields_are_used_by_resume_paths` が `gdd_stop_hook.py` に固定したまま落ちていた。呼び出し元を探すファイルを `lib/done_guard.py` に直した（テストだけの変更。本件とは別 commit）

#### Added

- `tests/test_safe_resume_session_id_trim.py` を追加した。実プロセスの SessionStart hook に、同じ入力表を `gdd_session_continuity_ok` と並べて流し、結論が一致することを固定する。表は、現在の session id が非空の入力に限る（下の限界）
  - 同じ session とみなす入力：`session_id` の行だけ末尾が CR、ファイル全体が CRLF、末尾の空白・タブ・混在、コロンの後に空白なし、値の途中に空白がある id
  - Candidate Mode のままにする入力：別の id（末尾の空白・CR の有無を問わない）、値の途中の空白を保持しない一致（`abcd` と `ab cd`）、値が空・CR だけ・空白だけ、`session_id` の行が無い、UTF-8 として不正なバイト列、現在の id が空白だけで stored が空
- 検出力は変異で確認した。末尾除去の `sed` を消すと 7 ケースが落ち、全空白を消す過剰な除去に変えると 2 ケースが落ちる

#### Affected Files

- `hooks/scripts/run-session-start-hook.sh`
- `tests/test_safe_resume_session_id_trim.py`
- `tests/test_always_high_scope_contract.py`

#### User Action Required

- 利用者の操作は不要。改行コードを変換した・手で編集した `.claude/gdd-dev.local.md` でも、同じ session の再開が Candidate Mode に落ちなくなる

#### Validation / Eval Impact

- 追加したテストは実プロセスで hook を走らせる。全量の回帰テストと `validate-plugin.sh` は、この変更の tip で通っている（main の赤 1 件は同梱の修正で解消）
- skill 本文・prompt・reviewer policy・HITL 出力契約は変えていない（Skill RED-GREEN Evidence は対象外）

#### Known Limitations

- 現在の session id が空のときは、Safe Resume の連鎖と `gdd_session_continuity_ok` の結論は元から一致しない（Safe Resume の連鎖には、現在の id が無いとき soft note で再開を許す分岐がある）。追加したテストの突き合わせは、現在の id が非空の入力に限る
- 現在の session id（env）側の末尾の空白は落とさない。両側を落とすと、空白だけの現在 id が空扱いになり、Candidate Mode（block）から soft note の再開（allow）へ反転する。`gdd_session_continuity_ok` と `scripts/setup-gdd-loop.sh` のロック検査も同じ片側の trim で、そろえているだけである
- BOM・大文字小文字・値の途中の空白の違いは吸収しない（別の id として扱う）
- `.claude/gdd-dev.local.md` の `session_id` を読む実装は 4 つに散在したままである（この行の読み取り、`gdd_session_continuity_ok`、`state_io.py::parse_state`、`scripts/setup-gdd-loop.sh` のロック検査。最後のものは `#` 以降も剥がす）。共有 helper 化は `gdd_session_continuity_ok`（11 箇所から呼ばれ、block gate と共有）に波及するので、この変更では見送った
- 実データでは、`session_id` の値が非空で末尾に空白・CR が付く local state は 0 件だった（手元の 57 件。末尾空白のある 5 件は値が空で、trim の有無で結果は変わらない）。誤発火は同じ session を止める側（過抑制）に倒れ、Safe Resume を通す側（fail-open）には倒れない
- 旧#140 の断片が挙げた既存の欠陥 6 件のうち、この変更で直したのは 1 件目だけである。残りは 旧#141・旧#142 ほか（compact の印の照合は open の PR 旧#156）
