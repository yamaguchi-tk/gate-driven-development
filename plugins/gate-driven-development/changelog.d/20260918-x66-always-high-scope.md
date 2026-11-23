---
type: minor
---

#### Summary

- `references/reviewer-common.md` § 常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）に適用範囲を設け、**block しない lint・hook と、開発者が実行する検査スクリプト自身の欠陥**を外した（X-66）。agent の操作を止める部品（PreToolUse の deny、pre-push / pre-PR / merge gate、done guard、steering write guard など）と、利用者の製品コードの判定部品（認証・認可・入力検証など）は、従来どおり常時 High のまま
- 改訂前は部品を問わず High に固定され、運用では category も fail-open が付いて blocking に数えられていた。旧#92 の high 6 件のうち 5 件は warn-only の HITL lint 自身の欠陥（F2 は Stop hook の block に届くため改訂後も High）、旧#93 の high の多くは開発者が手元で走らせる検査スクリプトの fail-open・例外で、agent の操作を止めない部品が往復を長引かせていた
- **利用者の `/gdd-dev` の gate の severity にも効く**。implementation gate・独立レビュー・merge gate の reviewer はすべて `reviewer-common.md` に従うため、block しない lint・hook と開発者向けの検査スクリプトの fail-open・例外は、medium 以下・blocking なしで報告されるようになる

#### Changed

- `references/reviewer-common.md` § 常時 High に「適用範囲」を追加した（除外リスト形）。適用範囲外（warn-only / advisory の lint と hook、`tests/checks/*`・`validate-plugin.sh` などの開発者が実行する検査）で 4 型に当たる欠陥は、severity を medium 上限にし、category に実害クラスを付けない（判別力の欠陥は test-power、それ以外は product）。4 型に当たらない欠陥（data-loss など）は従来どおり。適用範囲外の finding は Stage 2 の severity 調整の対象に戻る
- ただし、適用範囲外の部品への変更が block gate と共有する部品（shell 解析のヘルパーなど）を壊して block gate の判定が変わった場合は、block gate 側の欠陥として High のままにする（旧#88 F52/F53/F61/F62 の型）。判定できないときは適用範囲内として扱う
- 同節の主文と「予約 alias との関係」を適用範囲に当たるものに限る書き方に直した。§ finding category の「降格の防止」に、適用範囲外の部品の欠陥には実害クラスを付けないことを追記した。実害クラスの 4 値の表と `is_blocking` の定義は変えていない
- 参照側（`references/inline-review-checklists.md`、`references/self-contained-contract.md`、`references/independent-review.md` の出力フォーマット、`skills/gdd-implementation-gating/SKILL.md` Step 5）と、plugin の外の root `CLAUDE.md` 手順 6・`.claude/agents/light-lane-independent-reviewer.md` を、§ 常時 High の適用範囲を参照する形に揃えた。範囲の文言は複製しない

#### Added

- `tests/test_always_high_scope_contract.py`: 正本の適用範囲の記述と、参照側が 4 型の列挙や無条件の「常に High」を複製しないことを固定する契約テスト

#### Affected Files

- `references/reviewer-common.md`
- `references/inline-review-checklists.md`
- `references/self-contained-contract.md`
- `references/independent-review.md`
- `skills/gdd-implementation-gating/SKILL.md`
- `tests/test_always_high_scope_contract.py`
- `tests/test_diff_scope_out_of_range_blocking_contract.py`（independent-review.md の固定文言を追従。後に PR 旧#463 で削除）
- plugin の外: root `CLAUDE.md`、`.claude/agents/light-lane-independent-reviewer.md`

#### User Action Required

- 利用者の操作は不要。block しない lint・hook と開発者向けの検査スクリプトの fail-open・例外で、gate が high / blocking を理由に止まらなくなる。これらは medium として deferred（後続課題）にできる

#### Known Limitations

- 適用範囲の判定は reviewer の判断に依存する。部品が block するかどうかの機械的な宣言（hook ごとの属性など）は持たない
- 適用範囲外の部品でも、実害の程度によっては medium 上限が低すぎる場合がありうる。そのときは Issue に切り出して扱う
- category の test-power / product の振り分けと、guard bypass をどの実害クラスに当てるかは reviewer によって割れうる。severity と blocking の結論は変わらない（Skill RED-GREEN Evidence で確認）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）: 旧#92 F1/H1 と 旧#93 F29/F47 は改訂前 high・blocking、改訂後 medium・非 blocking。旧#88 F52/F62 と、利用者の製品コードの認可ミドルウェアの例外による素通りは、改訂後も high・blocking
