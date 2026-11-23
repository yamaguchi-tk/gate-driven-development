---
type: minor
---

#### Summary

requirements.md と design.md のテンプレートを、受入条件の AC を事実の単一の正本にする形に変えた。欄名の一覧・数値・PR の分け方・継続方式などは AC に 1 回だけ書き、Summary Brief・`Human Check Questions`・`Implementation Sequence Plan`・`Route / Ownership Matrix`・design.md などは事実を書き直さずに `AC-n 参照` と書く。照合元（`スコープ` の原文の完了条件、express の `Express Minimal Trace`）と、`Planned Follow-up Stage Lane` の欄の値（hook が読む）はそのまま書く。AC は 1 PR あたり 8 個以内、`Human Check Questions`（承認ポイント）は人が決めるものだけを方向性承認を除いて 2 個以内とする目安を足した。

steering write hook は、requirements.md・design.md の write のたびに、AC の欄名の列挙（backtick で囲んだ語が 2 つ以上）を AC 以外の節と design.md に書き直した行を `[duplication lint]` として advisory に出す。write は止めない。

#### Added

- `scripts/lint-requirements-duplication.py`: AC（`- AC-N:` の行と、同じ節でその下に続く行）の backtick 語のうち 2 つ以上を含む、AC 以外の行（requirements.md の AC を含まない節、design.md）を WARN として出す。`スコープ`・`Scope`・`Express Minimal Trace`・`Planned Follow-up Stage Lane` の節は見ない。WARN は先頭の 5 件と残りの件数だけを出す。AC の行の文法は `lint-ac.py` と同じ。終了コードは WARN の有無によらず 0（例外は 1、usage error は 2）
- `references/requirements-template.md` § 事実は AC に 1 回だけ書く

#### Changed

- `hooks/scripts/validate-steering-write.py` の advisory lint に、requirements.md・design.md の write で上の lint を足した。lint の実行部は `hooks/scripts/lib/advisory_lint.py` に移した（挙動は同じ）
- `references/requirements-template.md`: Summary Brief の確定事項・承認ポイント、`Implementation Sequence Plan` の完了確認、design.md skeleton の Summary Brief・`Human Check Questions`・`Implementation Sequence Plan` の参照を、AC を引用する形に変えた。承認ポイントの目安を「原則 3〜5 件」から「方向性承認を除いて 2 件以内」に変えた
- `references/requirements-template.md` § Express requirements.md テンプレート: 中にあった express テンプレートの複製（express 専用ファイルと見出しが違っていた）を消し、`references/requirements-template-express.md` を指すようにした。express の承認ポイントは「1〜3 件」から「方向性承認と、ほかに 1〜2 件」に変え、方向性承認の行を express 専用ファイルに移した。`references/task-sizing.md` の件数の表記も揃えた
- `references/requirements-template-express.md`: ほかの欄は `AC-n` を引く
- `references/human-check-template.md`・`references/human-check-template-compact.md`: requirements.md の承認ポイントは `AC-n` を引き、HITL の一次表示では AC の値に `AC-n` を添えて言い換えない。承認ポイント（判断ポイント）は方向性を除いて 2 件以内を目安にする（express は方向性と、ほかに 1〜2 件）
- `references/brainstorming-steps.md` の Gap Scan ⑤: 「`Human Check Questions` が 3 件未満」を未解決とせず、「方向性承認を除いて 2 個を超え、理由の 1 行が無い」を未解決とする
- `skills/gdd-requirements-gating/SKILL.md` § AC Quality Check: AC 以外の節・design.md の事実が AC と食い違えば blocking。食い違わない書き直し・`[duplication lint]` の行・方向性を除いて 2 個を超える HCQ は advisory

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-requirements-duplication.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/hooks/scripts/lib/advisory_lint.py`
- `plugins/gate-driven-development/references/requirements-template.md`
- `plugins/gate-driven-development/references/requirements-template-express.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/task-sizing.md`
- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/skills/gdd-requirements-gating/SKILL.md`
- `plugins/gate-driven-development/tests/test_lint_requirements_duplication.py`

#### User Action Required

- なし。既存の steering はそのまま使える。節見出しと、hook・lint が読む欄名（`受入条件` の `- AC-N:`、`Planned Follow-up Stage Lane` の欄など）は変えていない
- 新しく書く requirements.md では、AC 以外の節に欄名や数値を書き直さず `AC-n 参照` と書く。`[duplication lint]` が出たら、その行を引用に置き換える（照合元と Lane の値は除く。行番号は write 前の内容のもの）

#### Validation / Eval Impact

- `tests/test_lint_requirements_duplication.py` を足した。lint 単体（Summary Brief に同じ列挙・古い列挙が Route / Ownership Matrix に残る・design.md に同じ列挙・AC の下の行の語との重なりで WARN、`AC-n 参照` だけ・AC と重なる語が 1 つ・照合元と Lane の節・requirements.md が無いときは何も出さない、WARN の上限）と、steering write hook の入口から `[duplication lint]` が systemMessage に出るまでを見る
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
