---
type: minor
---

#### Summary

- `references/reviewer-common.md` § 常時 High の適用範囲に、**block しない hook でも再開経路に届く欠陥は適用範囲内**とする規定を足した（Issue 旧#123、X-66 の後続）。対象は効果で列挙した 2 つで、(a) 再開に使う `state.md` の canonical field（`Resume From` / `Status` / `CompactSource` / `Next Action` / `Route In Progress` / `Human Check Status`）の書き込み・削除と、(b) compact 自動復帰と Safe Resume Candidate Mode の発火判定（`AutoCycleCount` の上限と `session_id` の照合を含む）である。hook の (a)(b) に届く欠陥は、種類（書き損じ・消し損じ・誤削除・発火しない・誤発火など）を問わず、同節の fail-open として扱う
- 適用範囲外の部品で 4 型に当たる欠陥に付けてよい実害クラスを、`data-loss` と `security-boundary` だけと明記した（`fail-open` と `approval-path` は付けない。どちらにも当たらなければ `test-power` か `product`）。この 2 つを付けた finding には medium の上限を掛けず、Stage 2 の severity 調整にも戻さない（独立レビューでは `references/independent-review.md` の (3-d) が同趣旨で降格を禁じる）
- X-66（§ 常時 High の適用範囲の新設）の項目にある「medium 以下・blocking なしで報告される」「medium として deferred（後続課題）にできる」「実害クラスを付けない」は、block しない hook の (a)(b) に届く欠陥と、`data-loss` / `security-boundary` については、この変更で上書きされる
- 改訂前は、同じファイルの § finding category の表と「降格の防止」が「resume / gate の correctness に影響」を無条件に `fail-open` の例に挙げており、PreCompact hook が `Status: paused` を書き損ねる欠陥などで、reviewer によって blocking の判定が割れた

#### Changed

- `references/reviewer-common.md` § 常時 High の適用範囲に (a)(b) を追加した。発火後に注入する案内文の内容・JSON の sanitize・warn の文言は、適用範囲外のまま
- 同節と § finding category「降格の防止」の「実害クラスを付けない」を、「4 型に当たることを理由には実害クラスを付けない」にそろえた
- § finding category の表の `fail-open` の例と「降格の防止」の「resume / gate の correctness に影響」を、§ 常時 High の適用範囲を指す書き方にした。field の列挙は § 常時 High の 1 箇所だけに置く
- `skills/gdd-implementation-gating/SKILL.md`・`skills/gdd-systematic-debugging/SKILL.md` の ops-blocking medium の「resume / gate correctness」と、`agents/gdd-implementation-reviewer.md` の High の例「resume/gate failure」に、§ 常時 High の適用範囲への参照を足した
- 参照側（`references/independent-review.md`、`.claude/agents/light-lane-independent-reviewer.md`）は § 参照のままで、変更していない

#### Added

- `tests/test_always_high_scope_contract.py` に `ResumeScopeTest` を追加した。(a)(b) と範囲外に残す文、適用範囲外で付けてよい実害クラスの文を固定する。列挙した field が再開の経路（PreCompact hook が書き、SessionStart hook・active steering 判定・done guard が読む）で実際に使われていることをファイル単位で検査し、`references/state-field-tiers.md` の routing source と hook 所有の field（今は `Status`）が列挙に入っていることも検査する
- 同じファイルに `ResumeGateExamplesPointToScopeTest` を追加した。skill・agent の 3 箇所の「resume / gate」の severity 例が § 常時 High を指すことを固定する。`OpsImpactIsDerivedFromCategoryTest` で、`ops impact` の説明に範囲を足していないこと（導出は category に従う）を固定する

#### Affected Files

- `references/reviewer-common.md`
- `skills/gdd-implementation-gating/SKILL.md`
- `skills/gdd-systematic-debugging/SKILL.md`
- `agents/gdd-implementation-reviewer.md`
- `tests/test_always_high_scope_contract.py`

#### User Action Required

- 利用者の操作は不要。block しない hook の再開経路の欠陥（`Status: paused` の書き損じ、Safe Resume のすり抜けなど）は、改訂後は fail-open として high・blocking で報告される

#### Known Limitations

- field の列挙は、routing source の 4 field と `Status` が `references/state-field-tiers.md` と一致することだけを機械検査する。`CompactSource` のように同ファイルに無い field が再開経路に増えても、列挙への追加は検出しない
- 適用範囲に当たるかは reviewer の判断に依存する。(b) の発火判定と、発火後に注入する文面の境界は reviewer によって割れうる
- `skills/gdd-implementation-gating/SKILL.md` の ops-blocking medium は、適用範囲外の部品の resume 関連の medium に当たらなくなり、express では remediation 必須から advisory に変わりうる。`skills/gdd-systematic-debugging/SKILL.md` は `ops impact`（実害クラス ∪ `product`）を優先するので、同じ finding でも ops-blocking のままになりうる
- (b) が名指しするのは compact 自動復帰と Safe Resume Candidate Mode だけである。post-merge の自動継続、canonical field が欠けたときの `[gdd:blocked]`、shadow marker の「Do NOT auto-resume」の判定、UserPromptSubmit hook と plan-reread hook の cross-session guard の呼び出し側は、字面では適用範囲外になる（`gdd_session_continuity_ok` そのものは block gate と共有しているので適用範囲内）
- この改訂で適用範囲内になった既存の欠陥 6 件は直していない（high のまま。後続は 旧#141・旧#142 ほか。次の 6 件）
  - SessionStart hook の Safe Resume の `session_id` の読み取りだけが末尾の空白・CR を落とさない（`gdd_session_continuity_ok` は落とす）。手で編集した・改行コードを変換した `.claude/gdd-dev.local.md` では、同じセッションでも Safe Resume Candidate Mode が発火する
  - SessionStart hook の `AutoCycleCount` の加算は、行頭形の完全一致（`AutoCycleCount: N`）しか書き換えない。bullet 形・`=` 形・バッククォート形・空白なし・末尾空白・CRLF では読む側（`gdd_extract_doc_field`）と食い違い、加算が止まって上限が効かない。`CompactSource` の削除も行頭形と bullet 形しか扱わない（削除が漏れても `.gdd_is_running` のロックで再発火は抑えられる）
  - PreCompact hook の `Status` / `CompactSource` の書き込みは、行頭形と bullet 形しか扱わず、`=` 形・バッククォート形・fence 内の行を読む側と同じように扱わない。該当する形では compact 自動復帰が発火しない
  - PreCompact hook の `sed` の失敗は `&&` の途中の要素なので `set -e` に掛からず、その field が書き換わらないまま（後の追記は成功しうる）警告なしに exit 0 で終わる
  - PreCompact hook の `CompactSource` / `PausedAt` の追記と、SessionStart hook の `AutoCycleCount` の追記は、先頭に改行を付けない。最終行に改行が無い state.md では直前の行につながり、追記した field が読む側から見えなくなるうえ、直前の canonical field の値も壊れる（例: `Route In Progress: noneCompactSource: pre-compact`）
  - compact の印（`CompactSource: pre-compact` と `Status: paused`）が SessionStart(compact) に消費されずに残ると、同じ worktree の次の SessionStart で session・branch を照合せずに自動復帰が発火し、Safe Resume Candidate Mode を迂回する
- 補足：hook 自身は行頭形で書く。ローカルの state.md 203 件で、`=` 形・バッククォート形・fence 内だけ、の行は 0 件だった（空白・CRLF・末尾改行の有無は数えていない）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
