---
type: patch
---

#### Summary

- compact 自動復帰は、SessionStart が compaction の直後（stdin の `source` が `compact`）で、PreCompact が書いた `CompactSessionId` が現在の session と一致し、worktree が既定ブランチ（main / master / trunk / develop / development）でないときだけ発火する。これまでは state.md に印が残っているだけで発火していた。compaction が完了せずに印が残ると、次の新しいセッション（main を含む）が照合なしに `/gdd-dev resume` を注入し、Safe Resume の検査を迂回していた（実データで 4 件。旧#142）
- PreCompact / SessionStart の state.md 書き込み（`Status` / `CompactSource` / `CompactSessionId` / `AutoCycleCount`）は、書いた後に読む側 `gdd_extract_doc_field` で読み直し、書いた値が読めたときだけ自動復帰を続ける。`=` 形・区切りの後の空白なし・CRLF・非数値の `AutoCycleCount` も書き換えられるようになり、`AutoCycleCount` の上限（`GDD_MAX_AUTO_CYCLES`）が確実に効く。書き換えられない形（値の違うバッククォート形の行が先にある）では自動復帰しない（旧#141）
- **利用者から見える変化**：
  - compact 以外（新しいセッション・`--resume`・`/clear`）で始まったセッションには、compact 自動復帰を注入しない。通常の再開案内（Safe Resume を含む）になる
  - 既定ブランチの worktree では、compact 後も自動復帰しない
  - `develop` / `development` の worktree でも、非終端の steering があれば（compaction と無関係の通常起動でも）Safe Resume Candidate Mode になる（これまでは `main` / `master` / `trunk` だけ）
  - 印を書けなかったときは、PreCompact が systemMessage で「compact 後は `/gdd-dev resume` を手動で実行する」よう知らせる
  - この版に上げた直後の最初の compact で、古い hook が書いた印（`CompactSessionId` が無い）は発火しない。次の compact からは発火する

#### Changed

- `hooks/scripts/lib/compact-resume.sh`（新規）：state.md の hook 所有 field の setter（`gdd_set_state_field`。行頭・bullet 1 個までの `Field:` / `Field=` を置換して reader で読み直す。値が読めないときだけ、末尾の改行を補って追記する。別の値が読めるとき（置換できない行が先にある）は、追記せずに非 0 を返す）、SessionStart の stdin payload の上限付き読み取り（`read -t 1`・JSON 解析）、発火条件（`gdd_compact_resume_allowed`）、既定ブランチの述語（`gdd_is_default_branch`。Safe Resume と共有）
- `hooks/scripts/run-pre-compact-hook.sh`：`Status` → `CompactSessionId` → `CompactSource` の順に setter で書き、途中で失敗したら残りを書かない。sed の失敗が `&&` の途中で握りつぶされていた経路と、最終行に改行が無いときに追記が直前の行につながる経路を閉じた。失敗の知らせは既存のリマインダーと 1 個の JSON にまとめる
- `hooks/scripts/run-session-start-hook.sh`：`CompactSource` の消費を、行を削除する regex から setter（`consumed` への書き換え＋読み直し）に変える。reader が `pre-compact` と読む形を regex で写すと写し漏れの形で印が残って再発火するため。書き換えられない形では発火しない側に倒れる。`_compact_resume_check` がロックを取る前に `gdd_compact_resume_allowed` を呼ぶ。`AutoCycleCount` の加算を setter に置き換え、書き戻せなければ発火しない。加算は消費の後に置く（消費できずに発火しないのに加算だけが残ると、compaction のたびに増えて上限で原因と無関係な表示になる）。stdin を読むのは compact の判定だけで、`$(cat` は使わない

#### Affected Files

- `hooks/scripts/lib/compact-resume.sh`（新規。既定ブランチの集合は main / master / trunk / develop / development で、lint 2 本の `DEFAULT_BRANCHES` と揃える。Safe Resume にも同じ集合が効く）
- `hooks/scripts/run-pre-compact-hook.sh`
- `hooks/scripts/run-session-start-hook.sh`
- `tests/test_compact_resume_writer_and_source.py`（新規）
- `tests/test_session_start_hook_compact_resume.py`・`tests/test_session_start_last_turn_failure_contract.py`・`tests/test_hook_multibyte_truncation_contract.py`（compact の経路に SessionStart(compact) の payload と `CompactSessionId` を渡す）
- `tests/test_pre_compact_hook.py`（python 不在を再現する PATH に `awk`・`tail` を足す）
- `tests/test_compact_state_form_invariants.py`（新規。state.md の形の組み合わせに対する不変条件 I1〜I3）
- `tests/test_p0_p1_operational_hardening_contract.py`（compact の経路を通す 4 本目。payload と `CompactSessionId` を渡し、切り詰めを見る前に発火を assert する。旧#154。`GDD_HOOK_STATE_DIR` を隔離する。同じファイルの SessionStart を起動するテストはすべて隔離する。`gdd_is_default_branch` の集合のうち main / develop / development の 3 値を Safe Resume 側の入口から固定するテスト〔develop / development が既定ブランチ扱い、task branch は扱わない〕を足す。master / trunk は `tests/test_compact_resume_writer_and_source.py` の compact 側の入口からのみ固定する）
- `references/state-field-tiers.md`・`references/state-schema.json`（hook 所有の field に、同じ往復の印 `CompactSessionId` / `CompactSource` / `AutoCycleCount` / `PausedAt` を足し、書き手・読み手・許容値（`CompactSource` は `pre-compact` / `consumed`）を書く。`PausedAt` に読み手は無い）
- `tests/test_always_high_scope_contract.py`（宣言の継続行に足した field を、常時 High の範囲か理由つきの範囲外かに分類させる。SessionStart の行は reader の呼び出し（`gdd_extract_doc_field "$_state_file" "{}"`）に固定する。旧#123 の `RESUME_PATHS` は PreCompact hook 内の sed の正規表現（`?Status:`）を前提にしていた。書き手を `gdd_set_state_field` に移したので、検査する形を setter の呼び出し（`gdd_set_state_field "$STATE_FILE" "Status"` / 同 `"CompactSource"`）に合わせる。読むだけに差し替わっても通らない形にする）

#### User Action Required

- 利用者の操作は不要。動いているセッションは、hook を読み直すために開き直すと確実（hooks.json は変えていない）
- 長いタスクで `AutoCycleCount` の上限（既定 30）に届いたら、`GDD_MAX_AUTO_CYCLES` を上げるか、state.md の `AutoCycleCount` を手で戻す（戻す書き手は無い）

#### Known Limitations

- state.md に、値の違うバッククォート形の `Status` / `CompactSessionId` / `CompactSource` / `AutoCycleCount` の行（`` - `Status`: x ``）が先にあると、書き換えずに自動復帰を止める
- SessionStart の stdin が途中まで届いて閉じない異常時は、1 秒で読み取りを打ち切り、自動復帰しない
- Codex など、SessionStart に `source` と session id が来ない runtime では compact 自動復帰は発火しない
- python3 が無い環境では、stdin の payload を解析できないので compact 自動復帰は発火しない（payload の解析は python3 固定）。印を書けなかった知らせ（PreCompact の systemMessage）は、python3 も `python` も無い環境でだけ出ない
- PreCompact が session id を読むのは env の `CLAUDE_CODE_SESSION_ID` だけで、SessionStart は payload を優先する。PreCompact に env が届かない runtime では `CompactSessionId` が `unknown` になり、警告なしで自動復帰しない（実測した runtime では、両 hook の env と payload の session id は同じ値）
- state.md にバッククォート形の `CompactSource` の行があると、値が `pre-compact` でも自動復帰しない（書き換えず、PreCompact は警告を出さずに成功と扱い、SessionStart は消費できずに発火しない。`AutoCycleCount` は据え置く）。通常形の行を足すと直る。この形では compaction を繰り返しても、PreCompact も SessionStart も何も表示せず、上限（`GDD_MAX_AUTO_CYCLES`）の案内も出ないまま自動復帰が止まり続ける。書き手側の検知（同じ値のバッククォート形を非 0 にする）は、setter の成功条件を変えて検査を増やすので、この PR では採らない
- setter の grep / sed は fence（```）の中の行も置換する。読む側は fence の中を読まないので、fence 内の記入例は compaction のたびに書き換わる（行は増えない）
- 作業ディレクトリが git で解決できない（git 不在・commit が無い）ときは、既定ブランチの判定を行わずに発火する（source と session の条件は効く）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_compact_state_form_invariants.py`：`Status` / `AutoCycleCount` / `CompactSource` の形（`=` 形・bullet 形・バッククォート形・fence 内だけ・末尾空白・非数値・CRLF）を 1 軸ずつ動かした 20 通りで、形ごとに次の 3 つ（計 60 件）を検査する。形ごとの期待値を持たず、reader の受理集合を写さない。(I1) 発火したなら `AutoCycleCount` の +1 を reader が読める (I2) 上限を超えて発火しない (I3) 発火したなら reader が読む `CompactSource` が `pre-compact` のまま残らない。書き換えられない形は、発火しない側に倒れてよい
- `tests/test_compact_resume_writer_and_source.py`：PreCompact → SessionStart の往復を実プロセスで通し、各形の書き込み・`AutoCycleCount` の上限・compact 以外の source・session 不一致・判定不能・既定ブランチ・stdin が閉じない場合を検査する。書き換えられない行が先にあっても、compaction を繰り返して state.md の行数が増えないこと（旧#155）も検査する。payload の source と session_id が入れ替わらないこと（`{"session_id": "compact"}` で発火しないこと）も検査する
